"""Unit tests for the EventLog model."""

from app.db.models import EventLog


def test_event_log_table_name():
    assert EventLog.__tablename__ == "event_log"


def test_event_log_required_fields():
    columns = {c.name for c in EventLog.__table__.columns}
    assert columns == {
        "id",
        "timestamp",
        "event_type",
        "severity",
        "source",
        "message",
        "details",
        "correlation_id",
    }


def test_event_log_indexed_columns():
    indexed = {
        idx.columns.keys()[0]
        for idx in EventLog.__table__.indexes
        if len(idx.columns) == 1
    }
    assert "timestamp" in indexed
    assert "event_type" in indexed
