from datetime import date, datetime, timezone

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.config import settings
from app.db.models import Organizer, OrganizerActivity
from app.db.session import SessionLocal


def run_organizer_scan(session: Session) -> int:
    """Scan public organizer profile pages for newly onboarded organizers (FR17).

    Starts from MAX(organizer_id) + 1, where the Organizer watermark counts only
    rows with onboarded_at set (so ingestion-created stubs don't advance past
    unscanned IDs). Fetches each page via httpx (no auth), records a row for each
    200 response (backfilling onboarded_at if a stub exists), stops at the first
    404 or unexpected status code. Returns the number of rows created or updated.
    """
    max_organizer = session.scalar(
        select(func.max(Organizer.organizer_id)).where(Organizer.onboarded_at.isnot(None))
    ) or 0
    max_activity = session.scalar(select(func.max(OrganizerActivity.organizer_id))) or 0
    start_id = max(max_organizer, max_activity) + 1

    found = 0
    today = date.today()
    now = datetime.now(timezone.utc)

    for organizer_id in range(start_id, start_id + settings.organizer_scan_limit):
        url = f"{settings.limitless_base_url}/organizer/{organizer_id}"
        response = httpx.get(url, follow_redirects=True, timeout=30)

        if response.status_code == 404:
            break
        if response.status_code == 200:
            existing = session.get(Organizer, organizer_id)
            if existing is None:
                session.add(Organizer(
                    organizer_id=organizer_id,
                    onboarded_at=today,
                    detected_at=now,
                ))
            elif existing.onboarded_at is None:
                existing.onboarded_at = today
                existing.detected_at = now
            found += 1
        else:
            break  # stop on unexpected status; next run retries from same watermark

    session.commit()
    return found


@celery_app.task(name="app.tasks.organizer_tasks.scan_new_organizers_task")
def scan_new_organizers_task() -> None:
    """Scan for newly onboarded organizers on the Celery beat schedule (FR17, NFR3)."""
    session = SessionLocal()
    try:
        run_organizer_scan(session)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
