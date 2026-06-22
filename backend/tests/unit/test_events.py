"""Unit tests for the event logging service (app/events.py)."""

import json
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import EventLog
from app.events import log_event


def _make_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def test_log_event_creates_row():
    factory = _make_session()
    with factory() as session:
        log_event(
            session=session,
            event_type="task.completed",
            source="celery",
            message="Task finished",
        )
        row = session.query(EventLog).one()
        assert row.event_type == "task.completed"
        assert row.severity == "INFO"
        assert row.source == "celery"
        assert row.message == "Task finished"
        assert row.timestamp is not None


def test_log_event_with_details():
    factory = _make_session()
    with factory() as session:
        log_event(
            session=session,
            event_type="ingestion.tournaments",
            source="tournament_tasks",
            message="Ingested tournaments",
            details={"count": 42, "pages": 2},
        )
        row = session.query(EventLog).one()
        parsed = json.loads(row.details)
        assert parsed == {"count": 42, "pages": 2}


def test_log_event_with_severity():
    factory = _make_session()
    with factory() as session:
        log_event(
            session=session,
            event_type="task.failed",
            source="celery",
            message="Task exploded",
            severity="ERROR",
        )
        row = session.query(EventLog).one()
        assert row.severity == "ERROR"


def test_log_event_with_correlation_id():
    factory = _make_session()
    with factory() as session:
        log_event(
            session=session,
            event_type="task.started",
            source="celery",
            message="Task started",
            correlation_id="celery-task-abc123",
        )
        row = session.query(EventLog).one()
        assert row.correlation_id == "celery-task-abc123"


def test_log_event_never_raises():
    """log_event should swallow exceptions so it never crashes the caller."""
    factory = _make_session()
    with factory() as session:
        session.close()
        log_event(
            session=session,
            event_type="task.completed",
            source="celery",
            message="This should not crash",
        )


def test_log_event_with_none_session_does_not_raise():
    """Passing None as session should not raise."""
    log_event(
        session=None,
        event_type="task.completed",
        source="celery",
        message="This should not crash",
    )


def test_log_event_timestamp_is_utc():
    factory = _make_session()
    with factory() as session:
        before = datetime.now(timezone.utc)
        log_event(
            session=session,
            event_type="test.event",
            source="test",
            message="Timestamp check",
        )
        after = datetime.now(timezone.utc)
        row = session.query(EventLog).one()
        assert before <= row.timestamp <= after
