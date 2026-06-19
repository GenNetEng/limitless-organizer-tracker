from datetime import date
from typing import Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics.buckets import bucket_activity, bucket_onboarding
from app.analytics.frontier import compute_frontier
from app.analytics.regression import fit_linear_regression
from app.api.schemas import (
    ActivityBucketOut,
    BackfillResultOut,
    HighestOrganizerIdOut,
    OrganizerProfileOut,
    TournamentEntryOut,
    WaitEstimateOut,
    WaitEstimatePointOut,
)
from app.config import settings
from app.db.models import Organizer, OrganizerActivity
from app.db.session import get_db
from app.limitless_client.ingestion import sync_organizer_first_tournament_dates
from app.scraper.organizer_profile import parse_organizer_profile

TOP_N_ORGANIZERS = 1000

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
    organizer_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> WaitEstimateOut:
    rows = db.execute(
        select(
            OrganizerActivity.organizer_id,
            func.min(OrganizerActivity.first_tournament_date).label("first_tournament_date"),
        )
        .group_by(OrganizerActivity.organizer_id)
        .order_by(OrganizerActivity.organizer_id.desc())
        .limit(TOP_N_ORGANIZERS)
    ).all()
    if len(rows) < 2:
        raise HTTPException(status_code=404, detail="not enough activity data to estimate")

    # rows is DESC by organizer_id from the query; reverse to get ascending for frontier scan
    points = [(float(oid), float(first_date.date().toordinal())) for oid, first_date in reversed(rows)]
    frontier_points = compute_frontier(points)
    frontier_ids = {p[0] for p in frontier_points}
    regression_points = frontier_points if len(frontier_points) >= 2 else points
    result = fit_linear_regression(regression_points)

    projected_date = None
    if organizer_id is not None:
        projected_ordinal = round(result.predict(float(organizer_id)))
        projected_ordinal = max(date.min.toordinal(), min(date.max.toordinal(), projected_ordinal))
        projected_date = date.fromordinal(projected_ordinal)

    return WaitEstimateOut(
        organizer_id=organizer_id,
        slope=result.slope,
        intercept=result.intercept,
        r_squared=result.r_squared,
        projected_active_date=projected_date,
        sample_size=len(points),
        frontier_size=len(frontier_points),
        points=[
            WaitEstimatePointOut(
                organizer_id=int(oid),
                first_tournament_date=date.fromordinal(int(ordinal)),
                is_frontier=oid in frontier_ids,
            )
            for oid, ordinal in points
        ],
    )


@router.post("/organizers/backfill-first-tournament-date", response_model=BackfillResultOut)
def backfill_first_tournament_date(db: Session = Depends(get_db)) -> BackfillResultOut:
    """Back-populate Organizer.first_tournament_date from OrganizerActivity for any row where it is NULL."""
    null_ids = set(db.scalars(
        select(Organizer.organizer_id).where(Organizer.first_tournament_date.is_(None))
    ).all())

    if not null_ids:
        return BackfillResultOut(updated=0)

    sync_organizer_first_tournament_dates(db, null_ids)

    updated = db.scalar(
        select(func.count()).select_from(Organizer)
        .where(Organizer.organizer_id.in_(null_ids), Organizer.first_tournament_date.isnot(None))
    )
    db.commit()
    return BackfillResultOut(updated=updated or 0)


@router.get("/organizers/onboarding-history", response_model=list[ActivityBucketOut])
def get_onboarding_history(
    interval: Literal["day", "week"] = Query("day"),
    db: Session = Depends(get_db),
) -> list[ActivityBucketOut]:
    dates = db.scalars(
        select(Organizer.onboarded_at).where(Organizer.onboarded_at.isnot(None))
    ).all()
    buckets = bucket_onboarding(list(dates), interval)
    return [ActivityBucketOut(period=period, count=count) for period, count in buckets]


@router.get("/organizers/highest-id", response_model=HighestOrganizerIdOut)
def get_highest_organizer_id(db: Session = Depends(get_db)) -> HighestOrganizerIdOut:
    highest = db.scalar(select(func.max(Organizer.organizer_id)))
    if highest is None:
        highest = db.scalar(select(func.max(OrganizerActivity.organizer_id)))
    if highest is None:
        raise HTTPException(status_code=404, detail="no organizer data available")
    return HighestOrganizerIdOut(organizer_id=highest)


@router.get("/organizers/{organizer_id}/scrape", response_model=OrganizerProfileOut)
def scrape_organizer_profile(organizer_id: int) -> OrganizerProfileOut:
    url = f"{settings.limitless_base_url}/organizer/{organizer_id}"
    resp = httpx.get(url, follow_redirects=True)
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="organizer not found on Limitless")

    profile = parse_organizer_profile(resp.text, organizer_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="organizer profile could not be parsed")

    return OrganizerProfileOut(
        organizer_id=profile.organizer_id,
        name=profile.name,
        upcoming_tournaments=[
            TournamentEntryOut(
                tournament_id=t.tournament_id,
                name=t.name,
                date=t.date,
                game=t.game,
                players=t.players,
            )
            for t in profile.upcoming_tournaments
        ],
        recent_tournaments=[
            TournamentEntryOut(
                tournament_id=t.tournament_id,
                name=t.name,
                date=t.date,
                game=t.game,
                players=t.players,
            )
            for t in profile.recent_tournaments
        ],
    )
