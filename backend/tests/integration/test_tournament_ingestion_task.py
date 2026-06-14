from datetime import datetime, timedelta, timezone

import httpx
import respx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.tasks.tournament_tasks as tournament_tasks
from app.celery_app import celery_app
from app.config import settings
from app.db.base import Base
from app.db.models import OrganizerActivity, Tournament


def _tournament(id_, date, organizer_id=1, game="PTCG"):
    return {
        "id": id_,
        "name": "Tournament",
        "game": game,
        "format": "STANDARD",
        "date": date.isoformat().replace("+00:00", "Z"),
        "players": 10,
        "organizerId": organizer_id,
    }


@respx.mock
def test_ingest_tournaments_task_paginates_through_backfill_window(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    test_session_factory = sessionmaker(bind=engine)

    monkeypatch.setattr(tournament_tasks, "SessionLocal", test_session_factory)
    monkeypatch.setattr(tournament_tasks.settings, "tournament_backfill_months", 3)
    monkeypatch.setattr(tournament_tasks.settings, "tournament_ingest_limit", 1000)

    now = datetime.now(timezone.utc)
    pages = {
        "1": [_tournament("t1", now, organizer_id=100)],
        "2": [_tournament("t2", now - timedelta(days=200), organizer_id=200)],
    }

    def handler(request):
        page = request.url.params.get("page", "1")
        return httpx.Response(200, json=pages.get(page, []))

    respx.get(f"{settings.limitless_base_url}/api/tournaments").mock(side_effect=handler)

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    tournament_tasks.ingest_tournaments_task.delay()

    with test_session_factory() as session:
        assert session.get(Tournament, "t1") is not None
        assert session.get(Tournament, "t2") is not None
        assert session.get(OrganizerActivity, (100, "PTCG")) is not None
        assert session.get(OrganizerActivity, (200, "PTCG")) is not None


@respx.mock
def test_ingest_tournaments_task_stops_after_first_page_when_within_backfill_window(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    test_session_factory = sessionmaker(bind=engine)

    monkeypatch.setattr(tournament_tasks, "SessionLocal", test_session_factory)
    monkeypatch.setattr(tournament_tasks.settings, "tournament_backfill_months", 3)
    monkeypatch.setattr(tournament_tasks.settings, "tournament_ingest_limit", 1000)

    now = datetime.now(timezone.utc)
    old_date = now - timedelta(days=100)
    route = respx.get(f"{settings.limitless_base_url}/api/tournaments").mock(
        return_value=httpx.Response(200, json=[_tournament("t1", old_date, organizer_id=100)])
    )

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    tournament_tasks.ingest_tournaments_task.delay()

    assert route.call_count == 1
    with test_session_factory() as session:
        assert session.get(Tournament, "t1") is not None
