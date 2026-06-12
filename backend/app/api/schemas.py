from datetime import datetime
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


class ResubmissionEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    submitted_at: datetime
    success: bool
    discord_notified: bool
