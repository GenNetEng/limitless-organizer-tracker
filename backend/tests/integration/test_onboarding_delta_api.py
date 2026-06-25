from datetime import date

from app.db.models import Organizer


def test_onboarding_delta_returns_avg_median_count(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add_all([
            Organizer(organizer_id=2723, onboarded_at=date(2026, 6, 1), first_tournament_date=date(2026, 6, 11)),
            Organizer(organizer_id=2724, onboarded_at=date(2026, 6, 2), first_tournament_date=date(2026, 6, 12)),
            Organizer(organizer_id=2725, onboarded_at=date(2026, 6, 3), first_tournament_date=date(2026, 6, 23)),
        ])
        session.commit()

    response = test_client.get("/api/organizers/onboarding-delta")

    assert response.status_code == 200
    body = response.json()
    # deltas: 10, 10, 20 days
    assert body["count"] == 3
    assert body["avg_days"] == 40 / 3  # ~13.333...
    assert body["median_days"] == 10.0


def test_onboarding_delta_excludes_rows_missing_onboarded_at(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add_all([
            Organizer(organizer_id=2723, onboarded_at=date(2026, 6, 1), first_tournament_date=date(2026, 6, 11)),
            Organizer(organizer_id=100, onboarded_at=None, first_tournament_date=date(2026, 1, 1)),
        ])
        session.commit()

    response = test_client.get("/api/organizers/onboarding-delta")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["avg_days"] == 10.0
    assert body["median_days"] == 10.0


def test_onboarding_delta_excludes_rows_missing_first_tournament_date(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add_all([
            Organizer(organizer_id=2723, onboarded_at=date(2026, 6, 1), first_tournament_date=date(2026, 6, 11)),
            Organizer(organizer_id=2724, onboarded_at=date(2026, 6, 2), first_tournament_date=None),
        ])
        session.commit()

    response = test_client.get("/api/organizers/onboarding-delta")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1


def test_onboarding_delta_returns_zero_values_when_no_qualifying_rows(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add(Organizer(organizer_id=2723, onboarded_at=date(2026, 6, 1), first_tournament_date=None))
        session.commit()

    response = test_client.get("/api/organizers/onboarding-delta")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 0
    assert body["avg_days"] == 0.0
    assert body["median_days"] == 0.0


def test_onboarding_delta_empty_db(client):
    test_client, _ = client

    response = test_client.get("/api/organizers/onboarding-delta")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 0
    assert body["avg_days"] == 0.0
    assert body["median_days"] == 0.0


def test_onboarding_delta_excludes_negative_deltas(client):
    """Organizers whose first_tournament_date precedes onboarded_at are excluded."""
    test_client, session_factory = client
    with session_factory() as session:
        session.add_all([
            Organizer(organizer_id=2723, onboarded_at=date(2026, 6, 1), first_tournament_date=date(2026, 6, 11)),
            Organizer(organizer_id=2724, onboarded_at=date(2026, 6, 20), first_tournament_date=date(2026, 6, 10)),
        ])
        session.commit()

    response = test_client.get("/api/organizers/onboarding-delta")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["avg_days"] == 10.0
    assert body["median_days"] == 10.0


def test_onboarding_delta_even_count_median(client):
    """Median for even count should be average of the two middle values."""
    test_client, session_factory = client
    with session_factory() as session:
        session.add_all([
            Organizer(organizer_id=2723, onboarded_at=date(2026, 6, 1), first_tournament_date=date(2026, 6, 11)),
            Organizer(organizer_id=2724, onboarded_at=date(2026, 6, 1), first_tournament_date=date(2026, 6, 21)),
            Organizer(organizer_id=2725, onboarded_at=date(2026, 6, 1), first_tournament_date=date(2026, 6, 5)),
            Organizer(organizer_id=2726, onboarded_at=date(2026, 6, 1), first_tournament_date=date(2026, 7, 1)),
        ])
        session.commit()

    response = test_client.get("/api/organizers/onboarding-delta")

    assert response.status_code == 200
    body = response.json()
    # deltas: 4, 10, 20, 30 → sorted: 4, 10, 20, 30 → median = (10+20)/2 = 15
    assert body["count"] == 4
    assert body["median_days"] == 15.0
