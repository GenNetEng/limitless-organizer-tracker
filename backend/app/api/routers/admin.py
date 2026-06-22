"""Admin API router (FR20-FR23): event log, diagnostics, config, task triggers."""

import json
import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.api.auth import require_api_key
from app.api.schemas import (
    AdminConfigOut,
    DiagnosticsOut,
    EventLogOut,
    Page,
    TaskTriggerInfo,
)
from app.config import settings
from app.db.models import EventLog
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_api_key)],
)

TASK_TRIGGERS = [
    TaskTriggerInfo(
        name="ingest_tournaments",
        endpoint="/api/tasks/ingest-tournaments",
        method="POST",
        description="Ingest tournament data from the Limitless API across all games",
    ),
    TaskTriggerInfo(
        name="scan_organizers",
        endpoint="/api/tasks/scan-organizers",
        method="POST",
        description="Scan for newly onboarded organizer profiles",
    ),
    TaskTriggerInfo(
        name="resubmit_application",
        endpoint="/api/tasks/resubmit-application",
        method="POST",
        description="Resubmit the organization application and post Discord notification",
    ),
    TaskTriggerInfo(
        name="check_application_status",
        endpoint="/api/status-check",
        method="POST",
        description="Check the current organizer application status",
    ),
]


def _parse_details(raw: str | None) -> dict | list | None:
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


@router.get("/event-log", response_model=Page[EventLogOut])
def get_event_log(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    event_type: str | None = Query(None),
    severity: str | None = Query(None),
    source: str | None = Query(None),
) -> dict:
    query = select(EventLog)
    count_query = select(func.count()).select_from(EventLog)

    if event_type is not None:
        query = query.where(EventLog.event_type == event_type)
        count_query = count_query.where(EventLog.event_type == event_type)
    if severity is not None:
        query = query.where(EventLog.severity == severity)
        count_query = count_query.where(EventLog.severity == severity)
    if source is not None:
        query = query.where(EventLog.source == source)
        count_query = count_query.where(EventLog.source == source)

    total = db.scalar(count_query)
    rows = db.scalars(
        query.order_by(EventLog.timestamp.desc()).offset(offset).limit(limit)
    ).all()

    items = [
        EventLogOut(
            id=row.id,
            timestamp=row.timestamp,
            event_type=row.event_type,
            severity=row.severity,
            source=row.source,
            message=row.message,
            details=_parse_details(row.details),
            correlation_id=row.correlation_id,
        )
        for row in rows
    ]

    return {"items": items, "total": total, "limit": limit, "offset": offset}


def check_db_health(db: Session) -> bool:
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def check_redis_health() -> bool:
    try:
        from app.celery_app import celery_app as _celery
        _celery.backend.client.ping()
        return True
    except Exception:
        return False


def check_celery_workers() -> list[str]:
    try:
        from app.celery_app import celery_app as _celery
        response = _celery.control.ping(timeout=2)
        return [list(r.keys())[0] for r in response]
    except Exception:
        return []


def check_beat_health(db: Session) -> bool:
    row = db.scalar(
        select(EventLog.id)
        .where(EventLog.event_type == "task.completed")
        .order_by(EventLog.timestamp.desc())
        .limit(1)
    )
    return row is not None


def get_last_success_per_task(db: Session) -> dict[str, str | None]:
    rows = db.execute(
        select(
            EventLog.message,
            func.max(EventLog.timestamp),
        )
        .where(EventLog.event_type == "task.completed")
        .where(EventLog.source == "celery")
        .group_by(EventLog.message)
    ).all()

    result = {}
    for row in rows:
        task_message = row[0]
        last_ts = row[1]
        if task_message and last_ts:
            task_name = task_message.removesuffix(" completed")
            result[task_name] = last_ts.isoformat() if hasattr(last_ts, "isoformat") else str(last_ts)
    return result


@router.get("/diagnostics", response_model=DiagnosticsOut)
def get_diagnostics(db: Session = Depends(get_db)) -> dict:
    return {
        "db_ok": check_db_health(db),
        "redis_ok": check_redis_health(),
        "celery_workers": check_celery_workers(),
        "beat_ok": check_beat_health(db),
        "last_success_per_task": get_last_success_per_task(db),
    }


@router.get("/config", response_model=AdminConfigOut)
def get_config() -> dict:
    return {
        "application_status_check_interval_hours": settings.application_status_check_interval_hours,
        "resubmit_times_utc": settings.resubmit_times_utc,
        "tournament_ingest_interval_hours": settings.tournament_ingest_interval_hours,
        "tournament_ingest_limit": settings.tournament_ingest_limit,
        "tournament_backfill_months": settings.tournament_backfill_months,
        "organizer_scan_interval_hours": settings.organizer_scan_interval_hours,
        "organizer_scan_limit": settings.organizer_scan_limit,
    }


@router.get("/tasks", response_model=list[TaskTriggerInfo])
def get_tasks() -> list[TaskTriggerInfo]:
    return TASK_TRIGGERS
