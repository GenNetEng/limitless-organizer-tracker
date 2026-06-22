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


class TournamentEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tournament_id: str
    name: str
    date: str
    game: str
    players: int


class OrganizerProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    organizer_id: int
    name: str
    upcoming_tournaments: list[TournamentEntryOut]
    recent_tournaments: list[TournamentEntryOut]
    onboarded_at: date | None = None
    first_tournament_date: date | None = None
    estimated_onboard_date: date | None = None


class HighestOrganizerIdOut(BaseModel):
    organizer_id: int


class TaskResultOut(BaseModel):
    task_id: str
    status: str
    result: str


class EventLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    event_type: str
    severity: str
    source: str
    message: str
    details: dict | list | None = None
    correlation_id: str | None = None


class DiagnosticsOut(BaseModel):
    db_ok: bool
    redis_ok: bool
    celery_workers: list[str]
    beat_ok: bool
    last_success_per_task: dict[str, str | None]


class AdminConfigOut(BaseModel):
    application_status_check_interval_hours: int
    resubmit_times_utc: str
    tournament_ingest_interval_hours: int
    tournament_ingest_limit: int
    tournament_backfill_months: int
    organizer_scan_interval_hours: int
    organizer_scan_limit: int


class TaskTriggerInfo(BaseModel):
    name: str
    endpoint: str
    method: str
    description: str
