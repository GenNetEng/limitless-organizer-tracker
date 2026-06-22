from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.config import settings
from app.db.models import ResubmissionEvent
from app.db.session import SessionLocal
from app.events import log_event
from app.notifications.discord import post_resubmission_notice
from app.scraper.resubmit import resubmit_application
from app.scraper.session import authenticated_page


def record_resubmission(
    session: Session, success: bool, submitted_at: datetime, discord_notified: bool
) -> ResubmissionEvent:
    """Insert a resubmission datapoint (FR5)."""
    event = ResubmissionEvent(
        submitted_at=submitted_at, success=success, discord_notified=discord_notified
    )
    session.add(event)
    session.commit()
    return event


@celery_app.task(name="app.tasks.resubmit_tasks.resubmit_application_task")
def resubmit_application_task() -> int:
    """Resubmit the organization application and record the outcome (FR3, FR5).

    Posts a Discord notification with the outcome (FR4); the outcome is
    recorded (FR5) even if the notification fails. Returns the
    ResubmissionEvent row ID.
    """
    with authenticated_page() as page:
        success = resubmit_application(page)

    submitted_at = datetime.now(timezone.utc)

    discord_notified = False
    try:
        response = post_resubmission_notice(settings.discord_webhook_url, submitted_at, success)
        discord_notified = response.status_code < 300
    except httpx.HTTPError:
        discord_notified = False

    session = SessionLocal()
    try:
        event = record_resubmission(session, success, submitted_at, discord_notified)
        log_event(
            session=session,
            event_type="scraper.resubmit",
            source="resubmit_tasks",
            message=f"Application resubmission {'succeeded' if success else 'failed'}",
            severity="INFO" if success else "WARNING",
            details={
                "success": success,
                "discord_notified": discord_notified,
                "event_id": event.id,
            },
        )
        session.commit()
        return event.id
    finally:
        session.close()
