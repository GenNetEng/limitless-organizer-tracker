from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "limitless_organizer_tracker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.status_tasks", "app.tasks.resubmit_tasks"],
)


def parse_resubmit_times(value: str) -> list[tuple[int, int]]:
    """Parse a comma-separated "HH:MM,HH:MM" string into (hour, minute) tuples.

    Blank entries (including an empty `value`) are skipped, so an empty
    string yields no scheduled resubmit times rather than raising.
    """
    times = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        hour, minute = part.split(":")
        times.append((int(hour), int(minute)))
    return times


def _status_check_schedule(interval_hours: int) -> crontab:
    """Build the status-check crontab, treating a non-positive interval as hourly.

    `crontab(hour="*/0")` raises ValueError, so a misconfigured interval of 0
    (or less) falls back to checking every hour instead of crashing on import.
    """
    hours = interval_hours if interval_hours > 0 else 1
    return crontab(minute=0, hour=f"*/{hours}")


celery_app.conf.beat_schedule = {
    "check-application-status": {
        "task": "app.tasks.status_tasks.check_application_status_task",
        "schedule": _status_check_schedule(settings.application_status_check_interval_hours),
    },
    **{
        f"resubmit-application-{hour:02d}{minute:02d}": {
            "task": "app.tasks.resubmit_tasks.resubmit_application_task",
            "schedule": crontab(hour=hour, minute=minute),
        }
        for hour, minute in parse_resubmit_times(settings.resubmit_times_utc)
    },
}
