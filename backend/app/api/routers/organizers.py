from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.buckets import bucket_activity
from app.analytics.regression import fit_linear_regression
from app.api.schemas import ActivityBucketOut, WaitEstimateOut
from app.db.models import OrganizerActivity
from app.db.session import get_db

router = APIRouter(prefix="/api", tags=["organizers"])


@router.get("/games", response_model=list[str])
def get_games(db: Session = Depends(get_db)) -> list[str]:
    return list(db.scalars(select(OrganizerActivity.game).distinct().order_by(OrganizerActivity.game)))


@router.get("/organizers/activity", response_model=list[ActivityBucketOut])
def get_organizer_activity(
    interval: Literal["week", "month"] = Query("week"),
    game: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[ActivityBucketOut]:
    stmt = select(OrganizerActivity.first_tournament_date)
    if game is not None:
        stmt = stmt.where(OrganizerActivity.game == game)

    dates = db.scalars(stmt).all()
    buckets = bucket_activity(dates, interval)
    return [ActivityBucketOut(period=period, count=count) for period, count in buckets]


@router.get("/organizers/wait-estimate", response_model=WaitEstimateOut)
def get_wait_estimate(
    organizer_id: int = Query(...),
    game: str = Query(...),
    db: Session = Depends(get_db),
) -> WaitEstimateOut:
    rows = db.scalars(select(OrganizerActivity).where(OrganizerActivity.game == game)).all()
    if len(rows) < 2:
        raise HTTPException(status_code=404, detail="not enough activity data to estimate")

    points = [(float(row.organizer_id), float(row.first_tournament_date.date().toordinal())) for row in rows]
    result = fit_linear_regression(points)
    projected_date = date.fromordinal(round(result.predict(float(organizer_id))))

    return WaitEstimateOut(
        organizer_id=organizer_id,
        game=game,
        slope=result.slope,
        r_squared=result.r_squared,
        projected_active_date=projected_date,
        sample_size=len(rows),
    )
