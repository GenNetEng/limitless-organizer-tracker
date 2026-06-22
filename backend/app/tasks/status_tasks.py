from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.config import settings
from app.db.models import ApplicationStatusCheck
from app.db.session import SessionLocal
from app.notifications.discord import post_status_update_notice
from app.scraper.application_status import check_application_status
from app.scraper.parsing import ApplicationStatusResult
from app.scraper.session import authenticated_page


def record_status_check(
    session: Session, result: ApplicationStatusResult, checked_at: datetime
) -> tuple[ApplicationStatusCheck, bool]:
    """Insert a status-check datapoint and report whether the status changed.

    `changed` is False for the first-ever check, since there is no prior
    status to compare against.
    """
    previous = (
        session.query(ApplicationStatusCheck)
        .order_by(ApplicationStatusCheck.checked_at.desc(), ApplicationStatusCheck.id.desc())
        .first()
    )
    changed = previous is not None and previous.status != result.status

    check = ApplicationStatusCheck(
        checked_at=checked_at,
        status=result.status,
        raw_text=result.raw_text,
        review_note=result.review_note,
    )
    session.add(check)
    session.commit()

    return check, changed


def run_application_status_check(session: Session) -> tuple[ApplicationStatusCheck, bool]:
    """Check the organizer application status and record it (FR2, FR14).

    Posts a Discord notification only if the status changed since the last
    check; a failure to notify does not affect the recorded datapoint.
    Returns the inserted check row and whether the status changed.
    """
    with authenticated_page() as page:
        result = check_application_status(page)

    checked_at = datetime.now(timezone.utc)
    check, changed = record_status_check(session, result, checked_at)

    if changed:
        try:
            post_status_update_notice(settings.discord_webhook_url, result.status, checked_at)
        except httpx.HTTPError:
            pass

    return check, changed


@celery_app.task(name="app.tasks.status_tasks.check_application_status_task")
def check_application_status_task() -> int:
    """Run an application-status check and return the check row ID.

    Used by both the Celery beat schedule (FR2) and the on-demand
    API endpoint (FR14), which dispatches this task to the worker
    so Playwright runs in a container that has Chromium installed.
    """
    session = SessionLocal()
    try:
        check, _ = run_application_status_check(session)
        return check.id
    finally:
        session.close()
