from datetime import datetime, timedelta, timezone

import app.tasks.tournament_tasks as tournament_tasks
from app.config import settings
from app.db.models import ConfigEntry, Tournament
from app.limitless_client.schemas import TournamentDTO


def _dto(id_, date, organizer_id=1, game="PTCG"):
    return TournamentDTO(
        id=id_, name="Tournament", game=game, format="STANDARD", date=date, players=10, organizerId=organizer_id
    )


def test_stops_at_empty_page(db_session, monkeypatch):
    now = datetime.now(timezone.utc)
    pages = {
        1: [_dto("t1", now)],
        2: [],
    }

    def fake_fetch(limit, page=None):
        return pages[page]

    monkeypatch.setattr(tournament_tasks, "fetch_tournaments", fake_fetch)
    monkeypatch.setattr(settings, "tournament_backfill_months", 3)

    total = tournament_tasks.run_tournament_ingestion(db_session)

    assert total == 1
    assert db_session.get(Tournament, "t1") is not None


def test_stops_once_oldest_tournament_is_past_backfill_window(db_session, monkeypatch):
    now = datetime.now(timezone.utc)
    pages = {
        1: [_dto("t1", now)],
        2: [_dto("t2", now - timedelta(days=200))],
        3: [_dto("t3", now - timedelta(days=400))],
    }

    def fake_fetch(limit, page=None):
        return pages[page]

    monkeypatch.setattr(tournament_tasks, "fetch_tournaments", fake_fetch)
    monkeypatch.setattr(settings, "tournament_backfill_months", 3)

    total = tournament_tasks.run_tournament_ingestion(db_session)

    # page 2's tournament (200 days old) is past the 3-month (~90 day)
    # backfill window, so pagination stops after ingesting it
    assert total == 2
    assert db_session.get(Tournament, "t1") is not None
    assert db_session.get(Tournament, "t2") is not None
    assert db_session.get(Tournament, "t3") is None


def test_passes_configured_limit_to_fetch_tournaments(db_session, monkeypatch):
    now = datetime.now(timezone.utc)
    seen_limits = []

    def fake_fetch(limit, page=None):
        seen_limits.append(limit)
        return [] if page > 1 else [_dto("t1", now)]

    monkeypatch.setattr(tournament_tasks, "fetch_tournaments", fake_fetch)
    monkeypatch.setattr(settings, "tournament_backfill_months", 3)
    monkeypatch.setattr(settings, "tournament_ingest_limit", 500)

    tournament_tasks.run_tournament_ingestion(db_session)

    assert seen_limits == [500, 500]


def test_uses_db_override_for_ingest_limit(db_session, monkeypatch):
    """FR27: run_tournament_ingestion reads tournament_ingest_limit from DB when set."""
    now = datetime.now(timezone.utc)
    seen_limits = []

    def fake_fetch(limit, page=None):
        seen_limits.append(limit)
        return [] if page > 1 else [_dto("t1", now)]

    monkeypatch.setattr(tournament_tasks, "fetch_tournaments", fake_fetch)

    db_session.add(ConfigEntry(
        key="tournament_ingest_limit", value="25", updated_at=now,
    ))
    db_session.add(ConfigEntry(
        key="tournament_backfill_months", value="6", updated_at=now,
    ))
    db_session.commit()

    tournament_tasks.run_tournament_ingestion(db_session)

    assert seen_limits[0] == 25
