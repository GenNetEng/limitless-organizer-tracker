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


def run_historical_scan(session: Session) -> int:
    """Probe organizer IDs 1 through watermark, dispatching scan tasks for 200s.

    Unlike the frontier scanner, continues past 404/500 — historical IDs have gaps.
    Returns the number of scan tasks dispatched.
    """
    watermark = settings.organizer_scan_start_id

    existing_ids = set(session.scalars(
        select(Organizer.organizer_id)
        .where(Organizer.organizer_id <= watermark)
    ).all())

    ids_to_probe = [oid for oid in range(1, watermark + 1) if oid not in existing_ids]
    if not ids_to_probe:
        log_event(
            session=session,
            event_type="backfill.historical_scan_complete",
            source="backfill_tasks",
            message="Historical scan: no missing IDs to probe",
            details={"watermark": watermark, "dispatched": 0, "probed": 0},
        )
        return 0

    dispatched = 0
    probed = 0

    for oid in ids_to_probe:
        probed += 1
        try:
            url = f"{settings.limitless_base_url}/organizer/{oid}"
            response = httpx.get(url, follow_redirects=True, timeout=30)
        except httpx.HTTPError:
            continue

        if response.status_code == 200:
            scan_single_organizer_task.delay(organizer_id=oid)
            dispatched += 1

        if probed % 100 == 0:
            logger.info("Historical scan progress: probed %d/%d IDs, dispatched %d", probed, len(ids_to_probe), dispatched)

    log_event(
        session=session,
        event_type="backfill.historical_scan_complete",
        source="backfill_tasks",
        message=f"Historical scan complete: dispatched {dispatched} scan tasks from {probed} probed IDs",
        details={"watermark": watermark, "dispatched": dispatched, "probed": probed},
    )
    return dispatched


@celery_app.task(name="app.tasks.backfill_tasks.historical_organizer_scan_task")
def historical_organizer_scan_task() -> int:
    with task_session() as session:
        count = run_historical_scan(session)
        session.commit()
        return count
