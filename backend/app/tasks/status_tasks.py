from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.config import settings
from app.db.models import ApplicationStatus, ApplicationStatusCheck
from app.db.session import task_session
from app.events import log_event
from app.notifications.discord import post_status_update_notice
from app.scraper.application_status import check_application_status
from app.scraper.browser import LoginFailed
from app.scraper.parsing import ApplicationStatusResult
from app.scraper.session import authenticated_page


def record_status_check(
    session: Session,
    result: ApplicationStatusResult,
    checked_at: datetime,
    debug_page_html: str | None = None,
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
    details = {
        "status": result.status.value,
        "changed": changed,
        "raw_text": result.raw_text[:200] if result.raw_text else None,
    }
    if debug_page_html is not None:
        details["debug_page_html"] = debug_page_html
    log_event(
        session=session,
        event_type="scraper.status_check",
        source="status_tasks",
        message=f"Application status: {result.status.value}",
        details=details,
    )
    session.commit()

    return check, changed


def preflight_check(
    username: str,
    password: str,
    application_id: str,
) -> ApplicationStatusResult | None:
    """Return an error result if required config is missing, else None."""
    if not username or not password:
        return ApplicationStatusResult(
            status=ApplicationStatus.ERROR_MISSING_CREDENTIALS,
            raw_text="",
        )
    if not application_id:
        return ApplicationStatusResult(
            status=ApplicationStatus.ERROR_MISSING_APPLICATION_ID,
            raw_text="",
        )
    return None


def run_application_status_check(session: Session) -> tuple[ApplicationStatusCheck, bool]:
    """Check the organizer application status and record it (FR2, FR14).

    Posts a Discord notification only if the status changed since the last
    check; a failure to notify does not affect the recorded datapoint.
    Returns the inserted check row and whether the status changed.
    """
    error = preflight_check(
        settings.limitless_username,
        settings.limitless_password,
        settings.limitless_application_id,
    )
    if error is not None:
        checked_at = datetime.now(timezone.utc)
        return record_status_check(session, error, checked_at)

    try:
        with authenticated_page() as ctx:
            result = check_application_status(ctx.page)
            try:
                debug_html = ctx.page.content()[:20000] if settings.scraper_debug else None
            except Exception:
                debug_html = None
    except LoginFailed:
        result = ApplicationStatusResult(
            status=ApplicationStatus.ERROR_INCORRECT_CREDENTIALS,
            raw_text="",
        )
        debug_html = None

    checked_at = datetime.now(timezone.utc)
    check, changed = record_status_check(session, result, checked_at, debug_page_html=debug_html)

    if changed:
        try:
            post_status_update_notice(settings.discord_webhook_url, result.status, checked_at)
            log_event(
                session=session,
                event_type="notification.discord_sent",
                source="status_tasks",
                message=f"Status change notification sent: {result.status.value}",
            )
            session.commit()
        except httpx.HTTPError:
            log_event(
                session=session,
                event_type="notification.discord_failed",
                source="status_tasks",
                message="Failed to send status change notification",
                severity="WARNING",
            )
            session.commit()

    return check, changed


@celery_app.task(name="app.tasks.status_tasks.check_application_status_task")
def check_application_status_task() -> int:
    """Run an application-status check and return the check row ID.

    Used by both the Celery beat schedule (FR2) and the on-demand
    API endpoint (FR14), which dispatches this task to the worker
    so Playwright runs in a container that has Chromium installed.
    """
    with task_session() as session:
        check, _ = run_application_status_check(session)
        return check.id
