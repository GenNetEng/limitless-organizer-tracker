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
    """Audit the Limitless API to discover total pages, then kick off sequential ingestion (#68).

    Counts pages by fetching until empty, logs the total, then dispatches
    backfill_page_task for page 1 which chains to subsequent pages.
    """
    total_pages = 0
    page = 1

    while True:
        dtos = fetch_tournaments(limit=settings.tournament_ingest_limit, page=page)
        if not dtos:
            break
        total_pages += 1
        page += 1

    with task_session() as session:
        log_event(
            session=session,
            event_type="ingestion.backfill_audit",
            source="tournament_tasks",
            message=f"Backfill audit complete: {total_pages} pages found, starting sequential ingestion",
            details={"total_pages": total_pages},
        )
        session.commit()

    if total_pages > 0:
        backfill_page_task.delay(page=1, total_pages=total_pages)

    return total_pages


@celery_app.task(name="app.tasks.tournament_tasks.backfill_page_task")
def backfill_page_task(page: int, total_pages: int = 0) -> int:
    """Ingest a single page of tournament history, then chain to the next (#68).

    Runs sequentially — each page completes before the next is dispatched.
    """
    dtos = fetch_tournaments(limit=settings.tournament_ingest_limit, page=page)

    if not dtos:
        with task_session() as session:
            log_event(
                session=session,
                event_type="ingestion.backfill_complete",
                source="tournament_tasks",
                message=f"Full backfill complete at page {page - 1}",
                details={"final_page": page - 1},
            )
            session.commit()
        return 0

    with task_session() as session:
        ingest_tournaments(session, dtos)
        log_event(
            session=session,
            event_type="ingestion.backfill_page",
            source="tournament_tasks",
            message=f"Backfill page {page}/{total_pages}: ingested {len(dtos)} tournaments",
            details={"page": page, "total_pages": total_pages, "count": len(dtos)},
        )
        session.commit()

    backfill_page_task.delay(page=page + 1, total_pages=total_pages)
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
