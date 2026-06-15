from contextlib import contextmanager
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import OrganizerActivity
from app.db.session import get_db
from app.main import app


def _dt(*args):
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_session_factory = sessionmaker(bind=engine)

    def override_get_db():
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app), test_session_factory
    finally:
        app.dependency_overrides.clear()


@contextmanager
def _seed(session_factory, rows):
    with session_factory() as session:
        for row in rows:
            session.add(OrganizerActivity(**row))
        session.commit()
    yield


def _activity(organizer_id, game, first_date, last_date=None, first_id="t1"):
    return {
        "organizer_id": organizer_id,
        "game": game,
        "first_tournament_date": first_date,
        "first_tournament_id": first_id,
        "last_seen_date": last_date or first_date,
        "updated_at": first_date,
    }


def test_get_games_returns_distinct_sorted_games(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add_all(
            [
                OrganizerActivity(**_activity(1, "PTCG", _dt(2026, 1, 1))),
                OrganizerActivity(**_activity(2, "POCKET", _dt(2026, 1, 1))),
                OrganizerActivity(**_activity(3, "PTCG", _dt(2026, 2, 1))),
            ]
        )
        session.commit()

    response = test_client.get("/api/games")

    assert response.status_code == 200
    assert response.json() == ["POCKET", "PTCG"]


def test_get_games_empty_db(client):
    test_client, _ = client

    response = test_client.get("/api/games")

    assert response.status_code == 200
    assert response.json() == []


def test_get_organizer_activity_buckets_by_week(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add_all(
            [
                OrganizerActivity(**_activity(1, "PTCG", _dt(2026, 6, 1))),  # Monday
                OrganizerActivity(**_activity(2, "PTCG", _dt(2026, 6, 3))),  # same week
                OrganizerActivity(**_activity(3, "PTCG", _dt(2026, 6, 8))),  # next Monday
            ]
        )
        session.commit()

    response = test_client.get("/api/organizers/activity", params={"interval": "week"})

    assert response.status_code == 200
    assert response.json() == [
        {"period": "2026-06-01", "count": 2},
        {"period": "2026-06-08", "count": 1},
    ]


def test_get_organizer_activity_buckets_by_month(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add_all(
            [
                OrganizerActivity(**_activity(1, "PTCG", _dt(2026, 6, 1))),
                OrganizerActivity(**_activity(2, "PTCG", _dt(2026, 6, 30))),
                OrganizerActivity(**_activity(3, "PTCG", _dt(2026, 7, 4))),
            ]
        )
        session.commit()

    response = test_client.get("/api/organizers/activity", params={"interval": "month"})

    assert response.status_code == 200
    assert response.json() == [
        {"period": "2026-06-01", "count": 2},
        {"period": "2026-07-01", "count": 1},
    ]


def test_get_organizer_activity_filters_by_game(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add_all(
            [
                OrganizerActivity(**_activity(1, "PTCG", _dt(2026, 6, 1))),
                OrganizerActivity(**_activity(2, "POCKET", _dt(2026, 6, 1))),
            ]
        )
        session.commit()

    response = test_client.get(
        "/api/organizers/activity", params={"interval": "week", "game": "POCKET"}
    )

    assert response.status_code == 200
    assert response.json() == [{"period": "2026-06-01", "count": 1}]


def test_get_organizer_activity_defaults_to_week(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add(OrganizerActivity(**_activity(1, "PTCG", _dt(2026, 6, 1))))
        session.commit()

    response = test_client.get("/api/organizers/activity")

    assert response.status_code == 200
    assert response.json() == [{"period": "2026-06-01", "count": 1}]


def test_get_organizer_activity_rejects_invalid_interval(client):
    test_client, _ = client

    response = test_client.get("/api/organizers/activity", params={"interval": "year"})

    assert response.status_code == 422


def test_get_wait_estimate_returns_projection(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add_all(
            [
                OrganizerActivity(**_activity(100, "PTCG", _dt(2026, 1, 1))),
                OrganizerActivity(**_activity(200, "PTCG", _dt(2026, 2, 1))),
                OrganizerActivity(**_activity(300, "PTCG", _dt(2026, 3, 3))),
            ]
        )
        session.commit()

    response = test_client.get(
        "/api/organizers/wait-estimate", params={"organizer_id": 400, "game": "PTCG"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["organizer_id"] == 400
    assert body["game"] == "PTCG"
    assert body["sample_size"] == 3
    assert body["slope"] > 0
    assert 0.0 <= body["r_squared"] <= 1.0
    assert body["projected_active_date"] > "2026-03-03"


def test_get_wait_estimate_returns_404_with_insufficient_data(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add(OrganizerActivity(**_activity(100, "PTCG", _dt(2026, 1, 1))))
        session.commit()

    response = test_client.get(
        "/api/organizers/wait-estimate", params={"organizer_id": 400, "game": "PTCG"}
    )

    assert response.status_code == 404


def test_get_wait_estimate_returns_404_for_unknown_game(client):
    test_client, _ = client

    response = test_client.get(
        "/api/organizers/wait-estimate", params={"organizer_id": 400, "game": "NOPE"}
    )

    assert response.status_code == 404
