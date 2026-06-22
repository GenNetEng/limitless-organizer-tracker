from datetime import date, datetime, timezone
from pathlib import Path

import httpx
import respx

from app.db.models import Organizer, OrganizerActivity

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "html"


@respx.mock
def test_scrape_returns_organizer_profile(client):
    test_client, session_factory = client
    html = (FIXTURE_DIR / "organizer_profile_200.html").read_text()
    respx.get("https://play.limitlesstcg.com/organizer/2720").mock(
        return_value=httpx.Response(200, text=html)
    )

    resp = test_client.get("/api/organizers/2720/scrape")

    assert resp.status_code == 200
    data = resp.json()
    assert data["organizer_id"] == 2720
    assert data["name"] == "Pudding Weekly"
    assert len(data["upcoming_tournaments"]) == 2
    assert len(data["recent_tournaments"]) == 2
    assert data["upcoming_tournaments"][0]["tournament_id"] == "6a30c6e62d97f3b0c2617d33"


@respx.mock
def test_scrape_includes_db_dates_when_organizer_exists(client):
    test_client, session_factory = client
    html = (FIXTURE_DIR / "organizer_profile_200.html").read_text()
    respx.get("https://play.limitlesstcg.com/organizer/2720").mock(
        return_value=httpx.Response(200, text=html)
    )
    with session_factory() as session:
        session.add(Organizer(
            organizer_id=2720,
            onboarded_at=date(2026, 6, 10),
            first_tournament_date=date(2026, 6, 15),
        ))
        session.commit()

    resp = test_client.get("/api/organizers/2720/scrape")

    assert resp.status_code == 200
    data = resp.json()
    assert data["onboarded_at"] == "2026-06-10"
    assert data["first_tournament_date"] == "2026-06-15"


@respx.mock
def test_scrape_returns_null_dates_when_organizer_not_in_db(client):
    test_client, session_factory = client
    html = (FIXTURE_DIR / "organizer_profile_200.html").read_text()
    respx.get("https://play.limitlesstcg.com/organizer/2720").mock(
        return_value=httpx.Response(200, text=html)
    )

    resp = test_client.get("/api/organizers/2720/scrape")

    assert resp.status_code == 200
    data = resp.json()
    assert data["onboarded_at"] is None
    assert data["first_tournament_date"] is None


@respx.mock
def test_scrape_returns_404_when_organizer_not_found(client):
    test_client, session_factory = client
    respx.get("https://play.limitlesstcg.com/organizer/99999").mock(
        return_value=httpx.Response(404)
    )

    resp = test_client.get("/api/organizers/99999/scrape")

    assert resp.status_code == 404


@respx.mock
def test_scrape_returns_404_when_page_has_no_profile(client):
    test_client, session_factory = client
    respx.get("https://play.limitlesstcg.com/organizer/88888").mock(
        return_value=httpx.Response(200, text="<html><body>Not a profile</body></html>")
    )

    resp = test_client.get("/api/organizers/88888/scrape")

    assert resp.status_code == 404


@respx.mock
def test_scrape_returns_502_on_upstream_server_error(client):
    test_client, session_factory = client
    respx.get("https://play.limitlesstcg.com/organizer/2720").mock(
        return_value=httpx.Response(500)
    )

    resp = test_client.get("/api/organizers/2720/scrape")

    assert resp.status_code == 502


@respx.mock
def test_scrape_returns_502_on_connection_error(client):
    test_client, session_factory = client
    respx.get("https://play.limitlesstcg.com/organizer/2720").mock(
        side_effect=httpx.ConnectError("DNS resolution failed")
    )

    resp = test_client.get("/api/organizers/2720/scrape")

    assert resp.status_code == 502


def test_scrape_rejects_non_positive_organizer_id(client):
    test_client, session_factory = client
    resp = test_client.get("/api/organizers/0/scrape")

    assert resp.status_code == 422


def test_highest_id_returns_highest_id_from_organizer_table(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add(Organizer(organizer_id=2700, onboarded_at=date(2026, 6, 10)))
        session.add(Organizer(organizer_id=2720, onboarded_at=date(2026, 6, 18)))
        session.commit()

    resp = test_client.get("/api/organizers/highest-id")

    assert resp.status_code == 200
    assert resp.json() == {"organizer_id": 2720}


def test_highest_id_falls_back_to_organizer_activity_when_organizer_table_empty(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add(OrganizerActivity(
            organizer_id=2500,
            game="Pokemon",
            first_tournament_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            first_tournament_id="t1",
            last_seen_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ))
        session.commit()

    resp = test_client.get("/api/organizers/highest-id")

    assert resp.status_code == 200
    assert resp.json() == {"organizer_id": 2500}


def test_highest_id_returns_404_when_both_tables_empty(client):
    test_client, session_factory = client
    resp = test_client.get("/api/organizers/highest-id")

    assert resp.status_code == 404
