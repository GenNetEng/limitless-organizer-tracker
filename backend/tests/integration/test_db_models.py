from datetime import datetime, timezone

from app.db.models import ApplicationStatus, ApplicationStatusCheck, Tournament


def test_create_and_query_tournament(db_session):
    tournament = Tournament(
        id="abc123",
        name="Test Cup",
        game="PTCG",
        format="STANDARD",
        date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        players=32,
        organizer_id=123,
        ingested_at=datetime.now(timezone.utc),
    )
    db_session.add(tournament)
    db_session.commit()

    fetched = db_session.get(Tournament, "abc123")
    assert fetched.name == "Test Cup"
    assert fetched.organizer_id == 123


def test_create_and_query_application_status_check(db_session):
    check = ApplicationStatusCheck(
        checked_at=datetime.now(timezone.utc),
        status=ApplicationStatus.PENDING,
        raw_text="Your application is pending review.",
    )
    db_session.add(check)
    db_session.commit()

    fetched = db_session.query(ApplicationStatusCheck).one()
    assert fetched.status == ApplicationStatus.PENDING
