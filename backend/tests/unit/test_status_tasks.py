from datetime import datetime, timezone

from app.db.models import ApplicationStatus, ApplicationStatusCheck
from app.scraper.parsing import ApplicationStatusResult
from app.tasks.status_tasks import preflight_check, record_status_check


def test_record_status_check_inserts_row(db_session):
    result = ApplicationStatusResult(status=ApplicationStatus.PENDING, raw_text="Pending review")
    timestamp = datetime(2026, 6, 12, 9, 0, tzinfo=timezone.utc)

    record_status_check(db_session, result, timestamp)

    fetched = db_session.query(ApplicationStatusCheck).one()
    assert fetched.status == ApplicationStatus.PENDING
    assert fetched.raw_text == "Pending review"
    assert fetched.checked_at == timestamp


def test_record_status_check_reports_no_change_on_first_check(db_session):
    result = ApplicationStatusResult(status=ApplicationStatus.PENDING, raw_text="Pending review")
    timestamp = datetime(2026, 6, 12, 9, 0, tzinfo=timezone.utc)

    _, changed = record_status_check(db_session, result, timestamp)

    assert changed is False


def test_record_status_check_detects_status_change(db_session):
    db_session.add(
        ApplicationStatusCheck(
            checked_at=datetime(2026, 6, 11, 9, 0, tzinfo=timezone.utc),
            status=ApplicationStatus.PENDING,
            raw_text="Pending review",
        )
    )
    db_session.commit()

    result = ApplicationStatusResult(status=ApplicationStatus.APPROVED, raw_text="Approved!")
    timestamp = datetime(2026, 6, 12, 9, 0, tzinfo=timezone.utc)

    _, changed = record_status_check(db_session, result, timestamp)

    assert changed is True


def test_record_status_check_reports_no_change_when_status_unchanged(db_session):
    db_session.add(
        ApplicationStatusCheck(
            checked_at=datetime(2026, 6, 11, 9, 0, tzinfo=timezone.utc),
            status=ApplicationStatus.PENDING,
            raw_text="Pending review",
        )
    )
    db_session.commit()

    result = ApplicationStatusResult(status=ApplicationStatus.PENDING, raw_text="Still pending")
    timestamp = datetime(2026, 6, 12, 9, 0, tzinfo=timezone.utc)

    _, changed = record_status_check(db_session, result, timestamp)

    assert changed is False


def test_record_status_check_persists_review_note(db_session):
    result = ApplicationStatusResult(
        status=ApplicationStatus.REJECTED,
        raw_text="Status: rejected",
        review_note="Your application was rejected. Please join the Discord.",
    )
    timestamp = datetime(2026, 6, 18, 9, 0, tzinfo=timezone.utc)

    record_status_check(db_session, result, timestamp)

    fetched = db_session.query(ApplicationStatusCheck).one()
    assert fetched.review_note == "Your application was rejected. Please join the Discord."


def test_record_status_check_review_note_is_none_when_absent(db_session):
    result = ApplicationStatusResult(status=ApplicationStatus.PENDING, raw_text="Pending review")
    timestamp = datetime(2026, 6, 18, 9, 0, tzinfo=timezone.utc)

    record_status_check(db_session, result, timestamp)

    fetched = db_session.query(ApplicationStatusCheck).one()
    assert fetched.review_note is None


# --- preflight_check ---


def test_preflight_returns_none_when_config_is_valid():
    result = preflight_check(
        username="user@example.com",
        password="secret",
        application_id="abc123",
    )
    assert result is None


def test_preflight_returns_error_when_application_id_missing():
    result = preflight_check(
        username="user@example.com",
        password="secret",
        application_id="",
    )
    assert result is not None
    assert result.status == ApplicationStatus.ERROR_MISSING_APPLICATION_ID


def test_preflight_returns_error_when_credentials_missing_no_username():
    result = preflight_check(
        username="",
        password="secret",
        application_id="abc123",
    )
    assert result is not None
    assert result.status == ApplicationStatus.ERROR_MISSING_CREDENTIALS


def test_preflight_returns_error_when_credentials_missing_no_password():
    result = preflight_check(
        username="user@example.com",
        password="",
        application_id="abc123",
    )
    assert result is not None
    assert result.status == ApplicationStatus.ERROR_MISSING_CREDENTIALS


def test_preflight_returns_error_when_all_missing():
    result = preflight_check(username="", password="", application_id="")
    assert result is not None
    assert result.status in (
        ApplicationStatus.ERROR_MISSING_CREDENTIALS,
        ApplicationStatus.ERROR_MISSING_APPLICATION_ID,
    )
