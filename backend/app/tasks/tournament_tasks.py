from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.config import settings
from app.db.session import task_session
from app.events import log_event
from app.limitless_client.ingestion import ingest_tournaments
from app.limitless_client.tournaments_api import fetch_tournaments


def run_tournament_ingestion(session: Session) -> int:
    """Ingest tournaments across all games, paginating back through the backfill window (FR6, FR7).

    Pages through `GET /api/tournaments` (newest first) starting at page 1,
    ingesting each page, until either a page is empty or its oldest
    tournament is older than `tournament_backfill_months` ago. Re-walking the
    full window on every run is idempotent (ingest_tournaments upserts) and
    picks up any retroactive edits within the window. Returns the total
    number of tournaments ingested.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=30 * settings.tournament_backfill_months)
    total = 0
    page = 1

    while True:
        dtos = fetch_tournaments(limit=settings.tournament_ingest_limit, page=page)
        if not dtos:
            break

        ingest_tournaments(session, dtos)
        total += len(dtos)

        if dtos[-1].date < cutoff:
            break

        page += 1

    return total


@celery_app.task(name="app.tasks.tournament_tasks.audit_backfill_task")
def audit_backfill_task() -> int:
    """Audit the Limitless API to discover pages, then dispatch per-page tasks (#68).

    Pages through the API to find all non-empty pages, dispatches a
    backfill_page_task for each, and logs the total queued. Returns the
    number of page tasks dispatched.
    """
    pages_found = []
    page = 1

    while True:
        dtos = fetch_tournaments(limit=settings.tournament_ingest_limit, page=page)
        if not dtos:
            break
        pages_found.append(page)
        page += 1

    for p in pages_found:
        backfill_page_task.delay(page=p)

    with task_session() as session:
        log_event(
            session=session,
            event_type="ingestion.backfill_audit",
            source="tournament_tasks",
            message=f"Backfill audit complete: queued {len(pages_found)} page tasks",
            details={"pages_queued": len(pages_found)},
        )
        session.commit()

    return len(pages_found)


@celery_app.task(name="app.tasks.tournament_tasks.backfill_page_task")
def backfill_page_task(page: int) -> int:
    """Ingest a single page of tournament history (#68).

    Returns the number of tournaments ingested.
    """
    dtos = fetch_tournaments(limit=settings.tournament_ingest_limit, page=page)
    if not dtos:
        return 0

    with task_session() as session:
        ingest_tournaments(session, dtos)
        log_event(
            session=session,
            event_type="ingestion.backfill_page",
            source="tournament_tasks",
            message=f"Backfill page {page}: ingested {len(dtos)} tournaments",
            details={"page": page, "count": len(dtos)},
        )
        session.commit()

    return len(dtos)


@celery_app.task(name="app.tasks.tournament_tasks.ingest_tournaments_task")
def ingest_tournaments_task() -> int:
    """Ingest tournament data on the Celery beat schedule (FR6, FR7, NFR3).

    Returns the total number of tournaments ingested.
    """
    with task_session() as session:
        total = run_tournament_ingestion(session)
        log_event(
            session=session,
            event_type="ingestion.tournaments",
            source="tournament_tasks",
            message=f"Ingested {total} tournaments",
            details={"count": total},
        )
        session.commit()
        return total
