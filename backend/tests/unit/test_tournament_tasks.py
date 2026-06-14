from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.tasks.tournament_tasks as tournament_tasks
from app.db.base import Base
from app.db.models import Tournament
from app.limitless_client.schemas import TournamentDTO


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
        yield session


def _dto(id_, date, organizer_id=1, game="PTCG"):
    return TournamentDTO(
        id=id_, name="Tournament", game=game, format="STANDARD", date=date, players=10, organizerId=organizer_id
    )


def test_stops_at_empty_page(session, monkeypatch):
    now = datetime.now(timezone.utc)
    pages = {
        1: [_dto("t1", now)],
        2: [],
    }

    def fake_fetch(limit, page=None):
        return pages[page]

    monkeypatch.setattr(tournament_tasks, "fetch_tournaments", fake_fetch)
    monkeypatch.setattr(tournament_tasks.settings, "tournament_backfill_months", 3)

    total = tournament_tasks.run_tournament_ingestion(session)

    assert total == 1
    assert session.get(Tournament, "t1") is not None


def test_stops_once_oldest_tournament_is_past_backfill_window(session, monkeypatch):
    now = datetime.now(timezone.utc)
    pages = {
        1: [_dto("t1", now)],
        2: [_dto("t2", now - timedelta(days=200))],
        3: [_dto("t3", now - timedelta(days=400))],
    }

    def fake_fetch(limit, page=None):
        return pages[page]

    monkeypatch.setattr(tournament_tasks, "fetch_tournaments", fake_fetch)
    monkeypatch.setattr(tournament_tasks.settings, "tournament_backfill_months", 3)

    total = tournament_tasks.run_tournament_ingestion(session)

    # page 2's tournament (200 days old) is past the 3-month (~90 day)
    # backfill window, so pagination stops after ingesting it
    assert total == 2
    assert session.get(Tournament, "t1") is not None
    assert session.get(Tournament, "t2") is not None
    assert session.get(Tournament, "t3") is None


def test_passes_configured_limit_to_fetch_tournaments(session, monkeypatch):
    now = datetime.now(timezone.utc)
    seen_limits = []

    def fake_fetch(limit, page=None):
        seen_limits.append(limit)
        return [] if page > 1 else [_dto("t1", now)]

    monkeypatch.setattr(tournament_tasks, "fetch_tournaments", fake_fetch)
    monkeypatch.setattr(tournament_tasks.settings, "tournament_backfill_months", 3)
    monkeypatch.setattr(tournament_tasks.settings, "tournament_ingest_limit", 500)

    tournament_tasks.run_tournament_ingestion(session)

    assert seen_limits == [500, 500]
