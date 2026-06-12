from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import ApplicationStatus, ApplicationStatusCheck, Tournament


def test_create_and_query_tournament():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    with session_factory() as session:
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
        session.add(tournament)
        session.commit()

        fetched = session.get(Tournament, "abc123")
        assert fetched.name == "Test Cup"
        assert fetched.organizer_id == 123


def test_create_and_query_application_status_check():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    with session_factory() as session:
        check = ApplicationStatusCheck(
            checked_at=datetime.now(timezone.utc),
            status=ApplicationStatus.PENDING,
            raw_text="Your application is pending review.",
        )
        session.add(check)
        session.commit()

        fetched = session.query(ApplicationStatusCheck).one()
        assert fetched.status == ApplicationStatus.PENDING
