from datetime import date, datetime, timezone

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


def test_get_wait_estimate_global_aggregates_across_games(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add_all(
            [
                # organizer 100 runs PTCG (earlier) and POCKET (later) — MIN picks PTCG date
                OrganizerActivity(**_activity(100, "PTCG", _dt(2026, 1, 1))),
                OrganizerActivity(**_activity(100, "POCKET", _dt(2026, 3, 1))),
                OrganizerActivity(**_activity(200, "PTCG", _dt(2026, 2, 1))),
            ]
        )
        session.commit()

    response = test_client.get("/api/organizers/wait-estimate")

    assert response.status_code == 200
    body = response.json()
    # each organizer appears exactly once (global dedup via MIN)
    assert body["sample_size"] == 2
    organizer_ids = [p["organizer_id"] for p in body["points"]]
    assert sorted(organizer_ids) == [100, 200]
    # organizer 100's date is its earliest (PTCG, 2026-01-01), not the POCKET date
    pt = next(p for p in body["points"] if p["organizer_id"] == 100)
    assert pt["first_tournament_date"] == "2026-01-01"


def test_get_wait_estimate_limits_to_top_n_by_organizer_id(client, monkeypatch):
    import app.api.routers.organizers as organizers_module

    monkeypatch.setattr(organizers_module, "TOP_N_ORGANIZERS", 2)

    test_client, session_factory = client
    with session_factory() as session:
        session.add_all(
            [
                OrganizerActivity(**_activity(100, "PTCG", _dt(2026, 1, 1))),
                OrganizerActivity(**_activity(200, "PTCG", _dt(2026, 2, 1))),
                OrganizerActivity(**_activity(300, "PTCG", _dt(2026, 3, 1))),
            ]
        )
        session.commit()

    response = test_client.get("/api/organizers/wait-estimate")

    assert response.status_code == 200
    body = response.json()
    # TOP_N_ORGANIZERS=2 and ordered DESC, so organizers 300 and 200 are kept
    assert body["sample_size"] == 2
    ids = {p["organizer_id"] for p in body["points"]}
    assert 300 in ids
    assert 200 in ids
    assert 100 not in ids


def test_get_wait_estimate_marks_frontier_points(client):
    test_client, session_factory = client
    with session_factory() as session:
        # (200, 2026-03-01) is dominated by (300, 2026-01-01): higher id, earlier date
        session.add_all(
            [
                OrganizerActivity(**_activity(100, "PTCG", _dt(2026, 1, 1))),
                OrganizerActivity(**_activity(200, "PTCG", _dt(2026, 3, 1))),
                OrganizerActivity(**_activity(300, "PTCG", _dt(2026, 1, 15))),
            ]
        )
        session.commit()

    response = test_client.get("/api/organizers/wait-estimate")

    assert response.status_code == 200
    body = response.json()
    pts = {p["organizer_id"]: p for p in body["points"]}
    assert pts[300]["is_frontier"] is True
    assert pts[200]["is_frontier"] is False
    assert pts[100]["is_frontier"] is True
    assert body["frontier_size"] == 2


def test_get_wait_estimate_without_organizer_id_returns_null_projection(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add_all(
            [
                OrganizerActivity(**_activity(100, "PTCG", _dt(2026, 1, 1))),
                OrganizerActivity(**_activity(200, "PTCG", _dt(2026, 2, 1))),
            ]
        )
        session.commit()

    response = test_client.get("/api/organizers/wait-estimate")

    assert response.status_code == 200
    body = response.json()
    assert body["organizer_id"] is None
    assert body["projected_active_date"] is None
    assert body["slope"] != 0
    assert 0.0 <= body["r_squared"] <= 1.0


def test_get_wait_estimate_with_organizer_id_returns_projection(client):
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

    response = test_client.get("/api/organizers/wait-estimate", params={"organizer_id": 400})

    assert response.status_code == 200
    body = response.json()
    assert body["organizer_id"] == 400
    assert body["projected_active_date"] is not None
    assert body["projected_active_date"] > "2026-03-03"
    assert body["sample_size"] == 3


def test_get_wait_estimate_clamps_out_of_range_projection(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add_all(
            [
                OrganizerActivity(**_activity(100, "PTCG", _dt(2026, 1, 1))),
                OrganizerActivity(**_activity(200, "PTCG", _dt(2026, 2, 1))),
            ]
        )
        session.commit()

    response = test_client.get(
        "/api/organizers/wait-estimate", params={"organizer_id": 10**12}
    )

    assert response.status_code == 200
    assert response.json()["projected_active_date"] == "9999-12-31"


def test_get_wait_estimate_returns_404_with_insufficient_data(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add(OrganizerActivity(**_activity(100, "PTCG", _dt(2026, 1, 1))))
        session.commit()

    response = test_client.get("/api/organizers/wait-estimate")

    assert response.status_code == 404


def test_get_wait_estimate_returns_404_with_empty_db(client):
    test_client, _ = client

    response = test_client.get("/api/organizers/wait-estimate")

    assert response.status_code == 404


def test_get_wait_estimate_falls_back_to_all_points_when_frontier_size_one(client):
    # When only one point is on the frontier, fall back to all points for regression
    # All dates increase as id increases — only the highest id (300) is on the frontier
    test_client, session_factory = client
    with session_factory() as session:
        session.add_all(
            [
                OrganizerActivity(**_activity(100, "PTCG", _dt(2026, 1, 1))),
                OrganizerActivity(**_activity(200, "PTCG", _dt(2026, 2, 1))),
                OrganizerActivity(**_activity(300, "PTCG", _dt(2026, 3, 1))),
            ]
        )
        session.commit()

    response = test_client.get("/api/organizers/wait-estimate")

    assert response.status_code == 200
    body = response.json()
    # frontier has 1 point, fell back to all 3 for regression
    assert body["frontier_size"] == 3
    assert body["sample_size"] == 3
