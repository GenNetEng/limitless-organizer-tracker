from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.pagination import DEFAULT_LIMIT, MAX_LIMIT, paginate
from app.api.schemas import Page, ResubmissionEventOut, StatusCheckOut
from app.db.models import ApplicationStatusCheck, ResubmissionEvent
from app.db.session import get_db

router = APIRouter(prefix="/api", tags=["status"])


@router.get("/status-history", response_model=Page[StatusCheckOut])
def get_status_history(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Page[StatusCheckOut]:
    items, total = paginate(
        db,
        ApplicationStatusCheck,
        (ApplicationStatusCheck.checked_at.desc(), ApplicationStatusCheck.id.desc()),
        limit,
        offset,
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/resubmissions", response_model=Page[ResubmissionEventOut])
def get_resubmissions(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Page[ResubmissionEventOut]:
    items, total = paginate(
        db,
        ResubmissionEvent,
        (ResubmissionEvent.submitted_at.desc(), ResubmissionEvent.id.desc()),
        limit,
        offset,
    )
    return Page(items=items, total=total, limit=limit, offset=offset)
