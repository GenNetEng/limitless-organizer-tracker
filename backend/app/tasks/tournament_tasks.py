from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.config import settings
from app.db.session import SessionLocal
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


@celery_app.task(name="app.tasks.tournament_tasks.ingest_tournaments_task")
def ingest_tournaments_task() -> None:
    """Ingest tournament data on the Celery beat schedule (FR6, FR7, NFR3)."""
    session = SessionLocal()
    try:
        run_tournament_ingestion(session)
    finally:
        session.close()
