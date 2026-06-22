from datetime import datetime, timezone

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.config import settings
from app.db.models import Organizer
from app.db.session import SessionLocal
from app.events import log_event


def run_organizer_scan(session: Session) -> int:
    """Scan public organizer profile pages for newly onboarded organizers (FR17).

    Watermark: MAX(organizer_id WHERE onboarded_at IS NOT NULL) — only rows the
    scanner itself has confirmed count, so ingestion-created stubs and activity
    data for high IDs never advance the position past unscanned ranges. Fetches
    each page via httpx (no auth), records a row for each 200 response
    (backfilling onboarded_at if a stub already exists), stops at the first 404
    or unexpected status code. Returns the number of rows created or updated.
    """
    start_id = (session.scalar(
        select(func.max(Organizer.organizer_id)).where(Organizer.onboarded_at.isnot(None))
    ) or 0) + 1

    found = 0
    now = datetime.now(timezone.utc)
    today = now.date()

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
def scan_new_organizers_task() -> int:
    """Scan for newly onboarded organizers on the Celery beat schedule (FR17, NFR3).

    Returns the number of organizers found.
    """
    session = SessionLocal()
    try:
        found = run_organizer_scan(session)
        log_event(
            session=session,
            event_type="scanner.scan_complete",
            source="organizer_tasks",
            message=f"Organizer scan found {found} new organizers",
            details={"found": found},
        )
        session.commit()
        return found
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
