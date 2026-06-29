"""One-time admin-triggered backfill tasks."""

import logging

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.config import settings
from app.db.models import Organizer, Tournament
from app.db.session import task_session
from app.events import log_event
from app.limitless_client.ingestion import (
    recompute_organizer_activity,
    sync_organizer_first_tournament_dates,
)
from app.tasks.organizer_tasks import scan_single_organizer_task

logger = logging.getLogger(__name__)


def run_backfill_organizers(session: Session) -> int:
    """Create Organizer rows for tournament organizer_ids that lack one.

    Returns the count of newly created Organizer rows.
    """
    existing_ids = set(session.scalars(
        select(Organizer.organizer_id)
    ).all())

    tournament_ids = set(session.scalars(
        select(Tournament.organizer_id).distinct()
    ).all())

    orphan_ids = tournament_ids - existing_ids
    if not orphan_ids:
        log_event(
            session=session,
            event_type="backfill.organizers_from_tournaments",
            source="backfill_tasks",
            message="No orphan organizer IDs found — nothing to backfill",
        )
        return 0

    orphan_pairs = set(session.execute(
        select(Tournament.organizer_id, Tournament.game)
        .where(Tournament.organizer_id.in_(orphan_ids))
        .distinct()
    ).all())

    recompute_organizer_activity(session, orphan_pairs)
    sync_organizer_first_tournament_dates(session, orphan_ids)

    created_ids = set(session.scalars(
        select(Organizer.organizer_id)
        .where(Organizer.organizer_id.in_(orphan_ids))
    ).all())
    count = len(created_ids)

    log_event(
        session=session,
        event_type="backfill.organizers_from_tournaments",
        source="backfill_tasks",
        message=f"Backfilled {count} Organizer rows from tournament data",
        details={"count": count, "orphan_ids_found": len(orphan_ids)},
    )
    return count


@celery_app.task(name="app.tasks.backfill_tasks.backfill_organizers_from_tournaments_task")
def backfill_organizers_from_tournaments_task() -> int:
    with task_session() as session:
        count = run_backfill_organizers(session)
        session.commit()
        return count


def _get_existing_ids_below_watermark(watermark: int) -> set[int]:
    with task_session() as session:
        return set(session.scalars(
            select(Organizer.organizer_id)
            .where(Organizer.organizer_id <= watermark)
        ).all())


def run_historical_scan(existing_ids: set[int], watermark: int) -> int:
    """Probe organizer IDs 1 through watermark, dispatching scan tasks for 200s.

    Unlike the frontier scanner, continues past 404/500 — historical IDs have gaps.
    Passes set_onboarded=False so historical organizers don't get onboarded_at set.
    Returns the number of scan tasks dispatched.
    """
    ids_to_probe = [oid for oid in range(1, watermark + 1) if oid not in existing_ids]
    if not ids_to_probe:
        with task_session() as session:
            log_event(
                session=session,
                event_type="backfill.historical_scan_complete",
                source="backfill_tasks",
                message="Historical scan: no missing IDs to probe",
                details={"watermark": watermark, "dispatched": 0, "probed": 0},
            )
            session.commit()
        return 0

    dispatched = 0
    errors = 0

    with httpx.Client(follow_redirects=True, timeout=30) as client:
        for probed, oid in enumerate(ids_to_probe, 1):
            try:
                url = f"{settings.limitless_base_url}/organizer/{oid}"
                response = client.get(url)
            except httpx.HTTPError:
                errors += 1
                logger.warning("Historical scan: HTTP error probing organizer %d", oid)
                continue

            if response.status_code == 200:
                scan_single_organizer_task.delay(organizer_id=oid, set_onboarded=False)
                dispatched += 1

            if probed % 100 == 0:
                logger.info("Historical scan progress: probed %d/%d IDs, dispatched %d", probed, len(ids_to_probe), dispatched)

    with task_session() as session:
        log_event(
            session=session,
            event_type="backfill.historical_scan_complete",
            source="backfill_tasks",
            message=f"Historical scan complete: dispatched {dispatched} scan tasks from {len(ids_to_probe)} probed IDs",
            details={"watermark": watermark, "dispatched": dispatched, "probed": len(ids_to_probe), "errors": errors},
        )
        session.commit()
    return dispatched


@celery_app.task(name="app.tasks.backfill_tasks.historical_organizer_scan_task")
def historical_organizer_scan_task() -> int:
    watermark = settings.organizer_scan_start_id
    existing_ids = _get_existing_ids_below_watermark(watermark)
    return run_historical_scan(existing_ids, watermark)
