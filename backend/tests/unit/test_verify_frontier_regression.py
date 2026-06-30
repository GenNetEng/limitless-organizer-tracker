"""Unit tests for run_verify_frontier_regression() (Phase 49, #139).

Tests the verification task that counts Organizer rows, runs regression,
and logs slope/R²/frontier_size/sample_size as an event.
"""

from datetime import datetime, timezone

from app.db.models import EventLog, Organizer, OrganizerActivity
from app.tasks.backfill_tasks import run_verify_frontier_regression


def _add_organizer(session, organizer_id, detected_at=None):
    if detected_at is None:
        detected_at = datetime.now(timezone.utc)
    session.add(Organizer(organizer_id=organizer_id, detected_at=detected_at))
    session.flush()


def _add_activity(session, organizer_id, first_dt, game="PTCG"):
    session.add(OrganizerActivity(
        organizer_id=organizer_id, game=game,
        first_tournament_date=first_dt, first_tournament_id="t-dummy",
        last_seen_date=first_dt, updated_at=datetime.now(timezone.utc),
    ))
    session.flush()


def test_logs_event_with_regression_metrics(db_session):
    """Verification logs an event containing slope, r_squared, frontier_size, sample_size."""
    for oid in range(100, 105):
        _add_organizer(db_session, oid)
        _add_activity(db_session, oid, datetime(2025, 1, 1 + oid - 100, tzinfo=timezone.utc))
    db_session.commit()

    run_verify_frontier_regression(db_session)

    events = db_session.query(EventLog).filter(
        EventLog.event_type == "backfill.verify_frontier_regression"
    ).all()
    assert len(events) == 1

    import json
    details = json.loads(events[0].details)
    assert "slope" in details
    assert "r_squared" in details
    assert "frontier_size" in details
    assert "sample_size" in details
    assert "organizer_count" in details


def test_includes_organizer_count(db_session):
    """The logged event includes the total Organizer row count."""
    for oid in [100, 200, 300]:
        _add_organizer(db_session, oid)
        _add_activity(db_session, oid, datetime(2025, 1, oid // 100, tzinfo=timezone.utc))
    db_session.commit()

    run_verify_frontier_regression(db_session)

    import json
    event = db_session.query(EventLog).filter(
        EventLog.event_type == "backfill.verify_frontier_regression"
    ).one()
    details = json.loads(event.details)
    assert details["organizer_count"] == 3


def test_handles_insufficient_data(db_session):
    """With fewer than 2 activity rows, logs event indicating insufficient data."""
    _add_organizer(db_session, 100)
    db_session.commit()

    run_verify_frontier_regression(db_session)

    events = db_session.query(EventLog).filter(
        EventLog.event_type == "backfill.verify_frontier_regression"
    ).all()
    assert len(events) == 1
    assert "insufficient" in events[0].message.lower()


def test_returns_metrics_dict(db_session):
    """run_verify_frontier_regression returns a dict with the metrics."""
    for oid in [100, 200, 300]:
        _add_organizer(db_session, oid)
        _add_activity(db_session, oid, datetime(2025, 1, oid // 100, tzinfo=timezone.utc))
    db_session.commit()

    result = run_verify_frontier_regression(db_session)

    assert isinstance(result, dict)
    assert "slope" in result
    assert "r_squared" in result
    assert "frontier_size" in result
    assert "sample_size" in result
    assert "organizer_count" in result
