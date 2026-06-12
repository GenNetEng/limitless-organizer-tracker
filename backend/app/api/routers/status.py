from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.schemas import Page, ResubmissionEventOut, StatusCheckOut
from app.db.models import ApplicationStatusCheck, ResubmissionEvent
from app.db.session import get_db

DEFAULT_LIMIT = 50
MAX_LIMIT = 200

router = APIRouter(prefix="/api", tags=["status"])


@router.get("/status-history", response_model=Page[StatusCheckOut])
def get_status_history(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Page[StatusCheckOut]:
    total = db.scalar(select(func.count()).select_from(ApplicationStatusCheck)) or 0
    items = (
        db.query(ApplicationStatusCheck)
        .order_by(ApplicationStatusCheck.checked_at.desc(), ApplicationStatusCheck.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/resubmissions", response_model=Page[ResubmissionEventOut])
def get_resubmissions(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Page[ResubmissionEventOut]:
    total = db.scalar(select(func.count()).select_from(ResubmissionEvent)) or 0
    items = (
        db.query(ResubmissionEvent)
        .order_by(ResubmissionEvent.submitted_at.desc(), ResubmissionEvent.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return Page(items=items, total=total, limit=limit, offset=offset)
