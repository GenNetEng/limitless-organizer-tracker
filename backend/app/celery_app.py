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
    """Parse a comma-separated "HH:MM,HH:MM" string into (hour, minute) tuples."""
    times = []
    for part in value.split(","):
        hour, minute = part.strip().split(":")
        times.append((int(hour), int(minute)))
    return times


celery_app.conf.beat_schedule = {
    "check-application-status": {
        "task": "app.tasks.status_tasks.check_application_status_task",
        "schedule": crontab(minute=0, hour=f"*/{settings.application_status_check_interval_hours}"),
    },
    **{
        f"resubmit-application-{hour:02d}{minute:02d}": {
            "task": "app.tasks.resubmit_tasks.resubmit_application_task",
            "schedule": crontab(hour=hour, minute=minute),
        }
        for hour, minute in parse_resubmit_times(settings.resubmit_times_utc)
    },
}
