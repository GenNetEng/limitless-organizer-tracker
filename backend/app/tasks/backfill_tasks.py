"""One-time admin-triggered backfill tasks (Phase 47, #136)."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.db.models import Organizer, Tournament
from app.db.session import task_session
from app.events import log_event
from app.limitless_client.ingestion import sync_organizer_first_tournament_dates

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

    sync_organizer_first_tournament_dates(session, orphan_ids)

    count = len(orphan_ids)
    log_event(
        session=session,
        event_type="backfill.organizers_from_tournaments",
        source="backfill_tasks",
        message=f"Backfilled {count} Organizer rows from tournament data",
        details={"count": count},
    )
    return count


@celery_app.task(name="app.tasks.backfill_tasks.backfill_organizers_from_tournaments_task")
def backfill_organizers_from_tournaments_task() -> int:
    with task_session() as session:
        count = run_backfill_organizers(session)
        session.commit()
        return count
