import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


class ApplicationStatusCheck(Base):
    __tablename__ = "application_status_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[ApplicationStatus] = mapped_column(SAEnum(ApplicationStatus, native_enum=False))
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)


class ResubmissionEvent(Base):
    __tablename__ = "resubmission_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    success: Mapped[bool] = mapped_column(default=False)
    discord_notified: Mapped[bool] = mapped_column(default=False)


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    game: Mapped[str] = mapped_column(String, index=True)
    format: Mapped[str | None] = mapped_column(String, nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    players: Mapped[int] = mapped_column(Integer)
    organizer_id: Mapped[int] = mapped_column(Integer, index=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class OrganizerActivity(Base):
    __tablename__ = "organizer_activity"

    organizer_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game: Mapped[str] = mapped_column(String, primary_key=True)
    first_tournament_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    first_tournament_id: Mapped[str] = mapped_column(String)
    last_seen_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
