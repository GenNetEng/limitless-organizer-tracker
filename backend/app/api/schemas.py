from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

from app.db.models import ApplicationStatus

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


class StatusCheckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    checked_at: datetime
    status: ApplicationStatus
    raw_text: str | None
    review_note: str | None


class ResubmissionEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    submitted_at: datetime
    success: bool
    discord_notified: bool


class ActivityBucketOut(BaseModel):
    period: date
    count: int


class WaitEstimatePointOut(BaseModel):
    organizer_id: int
    first_tournament_date: date
    is_frontier: bool


class WaitEstimateOut(BaseModel):
    organizer_id: int | None
    slope: float
    intercept: float
    r_squared: float
    projected_active_date: date | None
    sample_size: int
    frontier_size: int
    points: list[WaitEstimatePointOut]


class BackfillResultOut(BaseModel):
    updated: int
