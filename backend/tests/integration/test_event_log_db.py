"""Integration tests for EventLog model — round-trip insert/query."""

import json
from datetime import datetime, timezone

from app.db.models import EventLog


def test_insert_and_query_event_log(db_session):
    event = EventLog(
        timestamp=datetime(2026, 6, 22, 12, 0, 0, tzinfo=timezone.utc),
        event_type="task.completed",
        severity="INFO",
        source="celery",
        message="ingest_tournaments_task completed",
        details=json.dumps({"duration_ms": 1234.5, "result": "42 tournaments"}),
        correlation_id="abc-123",
    )
    db_session.add(event)
    db_session.commit()

    fetched = db_session.query(EventLog).one()
    assert fetched.event_type == "task.completed"
    assert fetched.severity == "INFO"
    assert fetched.source == "celery"
    assert fetched.correlation_id == "abc-123"
    parsed = json.loads(fetched.details)
    assert parsed["duration_ms"] == 1234.5


def test_event_log_nullable_fields(db_session):
    event = EventLog(
        timestamp=datetime(2026, 6, 22, 12, 0, 0, tzinfo=timezone.utc),
        event_type="system.startup",
        severity="INFO",
        source="api",
        message="Application started",
    )
    db_session.add(event)
    db_session.commit()

    fetched = db_session.query(EventLog).one()
    assert fetched.details is None
    assert fetched.correlation_id is None


def test_event_log_ordering_by_timestamp(db_session):
    db_session.add(EventLog(
        timestamp=datetime(2026, 6, 22, 10, 0, 0, tzinfo=timezone.utc),
        event_type="task.started",
        severity="INFO",
        source="celery",
        message="first",
    ))
    db_session.add(EventLog(
        timestamp=datetime(2026, 6, 22, 12, 0, 0, tzinfo=timezone.utc),
        event_type="task.completed",
        severity="INFO",
        source="celery",
        message="second",
    ))
    db_session.commit()

    events = db_session.query(EventLog).order_by(EventLog.timestamp.desc()).all()
    assert events[0].message == "second"
    assert events[1].message == "first"
