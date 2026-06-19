import enum
from datetime import date, datetime

from sqlalchemy import Date, Enum as SAEnum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UTCDateTime


class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


class ApplicationStatusCheck(Base):
    __tablename__ = "application_status_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    checked_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True)
    status: Mapped[ApplicationStatus] = mapped_column(SAEnum(ApplicationStatus, native_enum=False))
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)


class ResubmissionEvent(Base):
    __tablename__ = "resubmission_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    submitted_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True)
    success: Mapped[bool] = mapped_column(default=False)
    discord_notified: Mapped[bool] = mapped_column(default=False)


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    game: Mapped[str] = mapped_column(String, index=True)
    format: Mapped[str | None] = mapped_column(String, nullable=True)
    date: Mapped[datetime] = mapped_column(UTCDateTime, index=True)
    players: Mapped[int] = mapped_column(Integer)
    organizer_id: Mapped[int] = mapped_column(Integer, index=True)
    ingested_at: Mapped[datetime] = mapped_column(UTCDateTime)


class OrganizerActivity(Base):
    __tablename__ = "organizer_activity"

    organizer_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game: Mapped[str] = mapped_column(String, primary_key=True)
    first_tournament_date: Mapped[datetime] = mapped_column(UTCDateTime, index=True)
    first_tournament_id: Mapped[str] = mapped_column(String)
    last_seen_date: Mapped[datetime] = mapped_column(UTCDateTime)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime)


class Organizer(Base):
    __tablename__ = "organizers"

    organizer_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    onboarded_at: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    first_tournament_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    detected_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
