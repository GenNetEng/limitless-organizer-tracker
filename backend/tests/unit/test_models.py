from app.db.models import (
    ApplicationStatus,
    ApplicationStatusCheck,
    EventLog,
    OrganizerActivity,
    ResubmissionEvent,
    Tournament,
)


def test_application_status_enum_values():
    assert {s.value for s in ApplicationStatus} == {
        "pending",
        "approved",
        "rejected",
        "expired",
        "unknown",
    }


def test_table_names():
    assert ApplicationStatusCheck.__tablename__ == "application_status_checks"
    assert ResubmissionEvent.__tablename__ == "resubmission_events"
    assert Tournament.__tablename__ == "tournaments"
    assert OrganizerActivity.__tablename__ == "organizer_activity"
