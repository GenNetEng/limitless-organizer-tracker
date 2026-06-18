from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import ApplicationStatus, ApplicationStatusCheck
from app.scraper.parsing import ApplicationStatusResult
from app.tasks.status_tasks import record_status_check


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
        yield session


def test_record_status_check_inserts_row(session):
    result = ApplicationStatusResult(status=ApplicationStatus.PENDING, raw_text="Pending review")
    timestamp = datetime(2026, 6, 12, 9, 0, tzinfo=timezone.utc)

    record_status_check(session, result, timestamp)

    fetched = session.query(ApplicationStatusCheck).one()
    assert fetched.status == ApplicationStatus.PENDING
    assert fetched.raw_text == "Pending review"
    assert fetched.checked_at == timestamp


def test_record_status_check_reports_no_change_on_first_check(session):
    result = ApplicationStatusResult(status=ApplicationStatus.PENDING, raw_text="Pending review")
    timestamp = datetime(2026, 6, 12, 9, 0, tzinfo=timezone.utc)

    _, changed = record_status_check(session, result, timestamp)

    assert changed is False


def test_record_status_check_detects_status_change(session):
    session.add(
        ApplicationStatusCheck(
            checked_at=datetime(2026, 6, 11, 9, 0, tzinfo=timezone.utc),
            status=ApplicationStatus.PENDING,
            raw_text="Pending review",
        )
    )
    session.commit()

    result = ApplicationStatusResult(status=ApplicationStatus.APPROVED, raw_text="Approved!")
    timestamp = datetime(2026, 6, 12, 9, 0, tzinfo=timezone.utc)

    _, changed = record_status_check(session, result, timestamp)

    assert changed is True


def test_record_status_check_reports_no_change_when_status_unchanged(session):
    session.add(
        ApplicationStatusCheck(
            checked_at=datetime(2026, 6, 11, 9, 0, tzinfo=timezone.utc),
            status=ApplicationStatus.PENDING,
            raw_text="Pending review",
        )
    )
    session.commit()

    result = ApplicationStatusResult(status=ApplicationStatus.PENDING, raw_text="Still pending")
    timestamp = datetime(2026, 6, 12, 9, 0, tzinfo=timezone.utc)

    _, changed = record_status_check(session, result, timestamp)

    assert changed is False


def test_record_status_check_persists_review_note(session):
    result = ApplicationStatusResult(
        status=ApplicationStatus.REJECTED,
        raw_text="Status: rejected",
        review_note="Your application was rejected. Please join the Discord.",
    )
    timestamp = datetime(2026, 6, 18, 9, 0, tzinfo=timezone.utc)

    record_status_check(session, result, timestamp)

    fetched = session.query(ApplicationStatusCheck).one()
    assert fetched.review_note == "Your application was rejected. Please join the Discord."


def test_record_status_check_review_note_is_none_when_absent(session):
    result = ApplicationStatusResult(status=ApplicationStatus.PENDING, raw_text="Pending review")
    timestamp = datetime(2026, 6, 18, 9, 0, tzinfo=timezone.utc)

    record_status_check(session, result, timestamp)

    fetched = session.query(ApplicationStatusCheck).one()
    assert fetched.review_note is None
