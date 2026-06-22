from datetime import date, datetime, timezone

from app.db.models import Organizer, OrganizerActivity


def _dt(*args):
    return datetime(*args, tzinfo=timezone.utc)


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
    # frontier_size == 1 when dates decrease as IDs increase: the highest-ID organizer
    # (300) dominates all lower-ID ones (200 and 100), which have later first_tournament_dates.
    # A point is on the frontier iff no higher-ID organizer has an earlier date.
    test_client, session_factory = client
    with session_factory() as session:
        session.add_all(
            [
                OrganizerActivity(**_activity(100, "PTCG", _dt(2026, 3, 1))),
                OrganizerActivity(**_activity(200, "PTCG", _dt(2026, 2, 1))),
                OrganizerActivity(**_activity(300, "PTCG", _dt(2026, 1, 1))),
            ]
        )
        session.commit()

    response = test_client.get("/api/organizers/wait-estimate")

    assert response.status_code == 200
    body = response.json()
    # frontier has 1 point (organizer 300 dominates all lower IDs); fallback uses all 3 for regression
    # frontier_size always reports the true frontier count, not the regression set size
    assert body["frontier_size"] == 1
    assert body["sample_size"] == 3


# ---------------------------------------------------------------------------
# GET /api/organizers/onboarding-history
# ---------------------------------------------------------------------------


def test_get_onboarding_history_by_day(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add_all([
            Organizer(organizer_id=1, onboarded_at=date(2026, 6, 1)),
            Organizer(organizer_id=2, onboarded_at=date(2026, 6, 1)),
            Organizer(organizer_id=3, onboarded_at=date(2026, 6, 2)),
        ])
        session.commit()

    response = test_client.get("/api/organizers/onboarding-history", params={"interval": "day"})

    assert response.status_code == 200
    assert response.json() == [
        {"period": "2026-06-01", "count": 2},
        {"period": "2026-06-02", "count": 1},
    ]


def test_get_onboarding_history_by_week(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add_all([
            Organizer(organizer_id=1, onboarded_at=date(2026, 6, 1)),   # Monday
            Organizer(organizer_id=2, onboarded_at=date(2026, 6, 3)),   # same week
            Organizer(organizer_id=3, onboarded_at=date(2026, 6, 8)),   # next Monday
        ])
        session.commit()

    response = test_client.get("/api/organizers/onboarding-history", params={"interval": "week"})

    assert response.status_code == 200
    assert response.json() == [
        {"period": "2026-06-01", "count": 2},
        {"period": "2026-06-08", "count": 1},
    ]


def test_get_onboarding_history_excludes_null_onboarded_at(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add_all([
            Organizer(organizer_id=1, onboarded_at=date(2026, 6, 1)),
            Organizer(organizer_id=2, onboarded_at=None),  # historical — no onboarded_at
        ])
        session.commit()

    response = test_client.get("/api/organizers/onboarding-history", params={"interval": "day"})

    assert response.status_code == 200
    assert response.json() == [{"period": "2026-06-01", "count": 1}]


def test_get_onboarding_history_defaults_to_day(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add(Organizer(organizer_id=1, onboarded_at=date(2026, 6, 1)))
        session.commit()

    response = test_client.get("/api/organizers/onboarding-history")

    assert response.status_code == 200
    assert response.json() == [{"period": "2026-06-01", "count": 1}]


def test_get_onboarding_history_rejects_invalid_interval(client):
    test_client, _ = client

    response = test_client.get("/api/organizers/onboarding-history", params={"interval": "month"})

    assert response.status_code == 422


def test_get_onboarding_history_empty_db(client):
    test_client, _ = client

    response = test_client.get("/api/organizers/onboarding-history")

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# POST /api/organizers/backfill-first-tournament-date
# ---------------------------------------------------------------------------


def test_backfill_sets_first_tournament_date_from_activity(client):
    test_client, session_factory = client
    with session_factory() as session:
        # Organizer exists (scanner found it) but no tournament yet → first_tournament_date=None
        session.add(Organizer(organizer_id=1, onboarded_at=date(2026, 6, 1)))
        # Activity exists for organizer 1 across two games
        session.add_all([
            OrganizerActivity(**_activity(1, "PTCG", _dt(2026, 5, 1))),
            OrganizerActivity(**_activity(1, "VGC", _dt(2026, 3, 1))),
        ])
        session.commit()

    response = test_client.post("/api/organizers/backfill-first-tournament-date")

    assert response.status_code == 200
    assert response.json() == {"updated": 1}
    with session_factory() as session:
        org = session.get(Organizer, 1)
        assert org.first_tournament_date == date(2026, 3, 1)  # MIN across games


def test_backfill_skips_organizers_already_having_first_tournament_date(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add(Organizer(organizer_id=1, first_tournament_date=date(2026, 1, 1)))
        session.add(OrganizerActivity(**_activity(1, "PTCG", _dt(2026, 1, 1))))
        session.commit()

    response = test_client.post("/api/organizers/backfill-first-tournament-date")

    assert response.status_code == 200
    assert response.json() == {"updated": 0}


def test_backfill_skips_organizers_with_no_activity(client):
    test_client, session_factory = client
    with session_factory() as session:
        # Organizer in table but no activity data to draw from
        session.add(Organizer(organizer_id=1, onboarded_at=date(2026, 6, 1)))
        session.commit()

    response = test_client.post("/api/organizers/backfill-first-tournament-date")

    assert response.status_code == 200
    assert response.json() == {"updated": 0}
    with session_factory() as session:
        assert session.get(Organizer, 1).first_tournament_date is None


def test_backfill_empty_organizer_table(client):
    test_client, _ = client

    response = test_client.post("/api/organizers/backfill-first-tournament-date")

    assert response.status_code == 200
    assert response.json() == {"updated": 0}


def test_backfill_updates_multiple_organizers(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add_all([
            Organizer(organizer_id=1),
            Organizer(organizer_id=2),
            Organizer(organizer_id=3, first_tournament_date=date(2026, 1, 1)),  # already set
        ])
        session.add_all([
            OrganizerActivity(**_activity(1, "PTCG", _dt(2026, 4, 1))),
            OrganizerActivity(**_activity(2, "PTCG", _dt(2026, 5, 1))),
            OrganizerActivity(**_activity(3, "PTCG", _dt(2026, 1, 1))),
        ])
        session.commit()

    response = test_client.post("/api/organizers/backfill-first-tournament-date")

    assert response.status_code == 200
    assert response.json() == {"updated": 2}
    with session_factory() as session:
        assert session.get(Organizer, 1).first_tournament_date == date(2026, 4, 1)
        assert session.get(Organizer, 2).first_tournament_date == date(2026, 5, 1)
        assert session.get(Organizer, 3).first_tournament_date == date(2026, 1, 1)  # unchanged
