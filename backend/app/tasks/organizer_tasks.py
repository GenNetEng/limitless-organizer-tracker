from datetime import datetime, timezone

import httpx
from sqlalchemy import func, select

from app.celery_app import celery_app
from app.config import settings
from app.db.models import Organizer
from app.db.session import task_session
from app.events import log_event
from app.scraper.organizer_profile import earliest_tournament_date, parse_organizer_profile


@celery_app.task(name="app.tasks.organizer_tasks.audit_organizer_scan_task")
def audit_organizer_scan_task() -> int:
    """Probe organizer IDs sequentially, then dispatch per-organizer tasks (FR17).

    Watermark: MAX(organizer_id WHERE onboarded_at IS NOT NULL). Probes each
    ID via httpx until the first 404 or scan_limit, dispatching a
    scan_single_organizer_task for each 200. Returns the number of tasks
    dispatched.
    """
    with task_session() as session:
        db_watermark = session.scalar(
            select(func.max(Organizer.organizer_id)).where(Organizer.onboarded_at.isnot(None))
        ) or 0
        start_id = max(db_watermark, settings.organizer_scan_start_id) + 1

    found_ids = []
    for organizer_id in range(start_id, start_id + settings.organizer_scan_limit):
        url = f"{settings.limitless_base_url}/organizer/{organizer_id}"
        response = httpx.get(url, follow_redirects=True, timeout=30)

        if response.status_code == 404:
            break
        if response.status_code == 200:
            found_ids.append(organizer_id)
        else:
            break

    for oid in found_ids:
        scan_single_organizer_task.delay(organizer_id=oid)

    with task_session() as session:
        log_event(
            session=session,
            event_type="scanner.audit_complete",
            source="organizer_tasks",
            message=f"Organizer audit: queued {len(found_ids)} scan tasks (IDs {start_id}–{start_id + len(found_ids) - 1})" if found_ids else f"Organizer audit: no new organizers from ID {start_id}",
            details={"start_id": start_id, "queued": len(found_ids)},
        )
        session.commit()

    return len(found_ids)


@celery_app.task(name="app.tasks.organizer_tasks.scan_single_organizer_task")
def scan_single_organizer_task(organizer_id: int) -> bool:
    """Fetch, parse, and upsert a single organizer profile (FR17).

    Sets onboarded_at = today (scanner-observed). Parses the profile to
    extract first_tournament_date if available. Returns True if the
    organizer was created or updated.
    """
    url = f"{settings.limitless_base_url}/organizer/{organizer_id}"
    response = httpx.get(url, follow_redirects=True, timeout=30)

    if response.status_code != 200:
        with task_session() as session:
            log_event(
                session=session,
                event_type="scanner.organizer_skip",
                source="organizer_tasks",
                message=f"Organizer {organizer_id}: HTTP {response.status_code}",
                severity="WARNING",
                details={"organizer_id": organizer_id, "status_code": response.status_code},
            )
            session.commit()
        return False

    now = datetime.now(timezone.utc)
    today = now.date()

    with task_session() as session:
        existing = session.get(Organizer, organizer_id)
        if existing is None:
            existing = Organizer(
                organizer_id=organizer_id,
                onboarded_at=today,
                detected_at=now,
            )
            session.add(existing)
        elif existing.onboarded_at is None:
            existing.onboarded_at = today
            existing.detected_at = now

        profile = parse_organizer_profile(response.text, organizer_id)
        if profile is not None:
            scraped_date = earliest_tournament_date(profile)
            if scraped_date is not None:
                if existing.first_tournament_date is None or scraped_date < existing.first_tournament_date:
                    existing.first_tournament_date = scraped_date

        log_event(
            session=session,
            event_type="scanner.organizer_found",
            source="organizer_tasks",
            message=f"Organizer {organizer_id} onboarded",
            details={
                "organizer_id": organizer_id,
                "first_tournament_date": str(existing.first_tournament_date) if existing.first_tournament_date else None,
            },
        )
        session.commit()

    return True


@celery_app.task(name="app.tasks.organizer_tasks.scan_new_organizers_task")
def scan_new_organizers_task() -> int:
    """Scan for newly onboarded organizers on the Celery beat schedule (FR17, NFR3).

    Dispatches the audit task which probes IDs and queues individual scan tasks.
    Returns immediately.
    """
    audit_organizer_scan_task.delay()
    return 0
