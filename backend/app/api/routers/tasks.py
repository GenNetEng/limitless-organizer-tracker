from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import require_api_key
from app.api.schemas import ResubmissionEventOut, TaskResultOut
from app.db.models import ResubmissionEvent
from app.db.session import get_db
from app.tasks.organizer_tasks import scan_new_organizers_task
from app.tasks.resubmit_tasks import resubmit_application_task
from app.tasks.tournament_tasks import full_tournament_backfill_task, ingest_tournaments_task

router = APIRouter(
    prefix="/api/tasks",
    tags=["tasks"],
    dependencies=[Depends(require_api_key)],
)

TASK_TIMEOUT_SECONDS = 120


@router.post("/ingest-tournaments", response_model=TaskResultOut)
def trigger_ingest_tournaments() -> dict:
    """Trigger a tournament ingestion run on the Celery worker.

    Fetches tournament data from the Limitless API across all games,
    paginating back through the configured backfill window. Upserts
    tournaments and organizer-activity records. Returns the count of
    tournaments processed.
    """
    try:
        result = ingest_tournaments_task.delay()
        count = result.get(timeout=TASK_TIMEOUT_SECONDS)
    except Exception:
        raise HTTPException(status_code=500, detail="Tournament ingestion task failed or timed out")
    return TaskResultOut(
        task_id=result.id,
        status="completed",
        result=f"Ingested {count} tournaments",
    )


@router.post("/full-backfill", response_model=TaskResultOut)
def trigger_full_backfill() -> dict:
    """Trigger a full historical tournament backfill on the Celery worker.

    Pages through the entire Limitless tournament API history with no date
    cutoff, upserting all tournaments and recomputing organizer activity.
    This is a long-running operation.
    """
    try:
        result = full_tournament_backfill_task.delay()
        count = result.get(timeout=600)
    except Exception:
        raise HTTPException(status_code=500, detail="Full backfill task failed or timed out")
    return TaskResultOut(
        task_id=result.id,
        status="completed",
        result=f"Backfilled {count} tournaments",
    )


@router.post("/scan-organizers", response_model=TaskResultOut)
def trigger_scan_organizers() -> dict:
    """Trigger an organizer scan on the Celery worker.

    Scans public organizer profile pages starting from the current
    watermark (highest confirmed organizer ID), recording each new
    organizer found until the first 404. Returns the count of new
    organizers discovered.
    """
    try:
        result = scan_new_organizers_task.delay()
        count = result.get(timeout=TASK_TIMEOUT_SECONDS)
    except Exception:
        raise HTTPException(status_code=500, detail="Organizer scan task failed or timed out")
    return TaskResultOut(
        task_id=result.id,
        status="completed",
        result=f"Found {count} new organizers",
    )


@router.post("/resubmit-application", response_model=ResubmissionEventOut)
def trigger_resubmit_application(db: Session = Depends(get_db)) -> ResubmissionEvent:
    """Trigger an application resubmission on the Celery worker.

    Logs into play.limitlesstcg.com via Playwright, resubmits the
    organization application, posts a Discord notification, and records
    the outcome. Returns the full resubmission event record.
    """
    try:
        result = resubmit_application_task.delay()
        event_id = result.get(timeout=TASK_TIMEOUT_SECONDS)
    except Exception:
        raise HTTPException(
            status_code=500, detail="Resubmission task failed or timed out"
        )
    event = db.get(ResubmissionEvent, event_id)
    if event is None:
        raise HTTPException(status_code=500, detail="Resubmission result not found")
    return event
