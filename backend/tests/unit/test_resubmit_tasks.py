from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import ResubmissionEvent
from app.tasks.resubmit_tasks import record_resubmission


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
        yield session


def test_record_resubmission_inserts_row(session):
    timestamp = datetime(2026, 6, 12, 9, 0, tzinfo=timezone.utc)

    record_resubmission(session, success=True, submitted_at=timestamp, discord_notified=True)

    fetched = session.query(ResubmissionEvent).one()
    assert fetched.success is True
    assert fetched.discord_notified is True
    assert fetched.submitted_at == timestamp


def test_record_resubmission_records_failure_without_notification(session):
    timestamp = datetime(2026, 6, 12, 21, 0, tzinfo=timezone.utc)

    record_resubmission(session, success=False, submitted_at=timestamp, discord_notified=False)

    fetched = session.query(ResubmissionEvent).one()
    assert fetched.success is False
    assert fetched.discord_notified is False
