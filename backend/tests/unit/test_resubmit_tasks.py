from datetime import datetime, timezone

from app.db.models import ResubmissionEvent
from app.tasks.resubmit_tasks import record_resubmission


def test_record_resubmission_inserts_row(db_session):
    timestamp = datetime(2026, 6, 12, 9, 0, tzinfo=timezone.utc)

    record_resubmission(db_session, success=True, submitted_at=timestamp, discord_notified=True)

    fetched = db_session.query(ResubmissionEvent).one()
    assert fetched.success is True
    assert fetched.discord_notified is True
    assert fetched.submitted_at == timestamp


def test_record_resubmission_records_failure_without_notification(db_session):
    timestamp = datetime(2026, 6, 12, 21, 0, tzinfo=timezone.utc)

    record_resubmission(db_session, success=False, submitted_at=timestamp, discord_notified=False)

    fetched = db_session.query(ResubmissionEvent).one()
    assert fetched.success is False
    assert fetched.discord_notified is False
