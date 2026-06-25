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
    assert data["first_tournament_date"] == "2026-06-10"


@respx.mock
def test_scrape_returns_null_onboarded_at_when_organizer_not_in_db(client):
    """Scraping a new organizer should return null onboarded_at (only the
    scanner sets that), but first_tournament_date should be populated
    from the scraped tournaments."""
    test_client, session_factory = client
    html = (FIXTURE_DIR / "organizer_profile_200.html").read_text()
    respx.get("https://play.limitlesstcg.com/organizer/2720").mock(
        return_value=httpx.Response(200, text=html)
    )

    resp = test_client.get("/api/organizers/2720/scrape")

    assert resp.status_code == 200
    data = resp.json()
    assert data["onboarded_at"] is None
    assert data["first_tournament_date"] == "2026-06-10"


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


@respx.mock
def test_scrape_upserts_organizer_with_first_tournament_date(client):
    """Scraping an organizer not in the DB should create an Organizer row
    with first_tournament_date derived from the scraped tournaments."""
    test_client, session_factory = client
    html = (FIXTURE_DIR / "organizer_profile_200.html").read_text()
    respx.get("https://play.limitlesstcg.com/organizer/2720").mock(
        return_value=httpx.Response(200, text=html)
    )

    resp = test_client.get("/api/organizers/2720/scrape")

    assert resp.status_code == 200
    data = resp.json()
    assert data["first_tournament_date"] == "2026-06-10"

    with session_factory() as session:
        org = session.get(Organizer, 2720)
        assert org is not None
        assert org.first_tournament_date == date(2026, 6, 10)
        assert org.onboarded_at is None
        assert org.detected_at is not None


@respx.mock
def test_scrape_updates_first_tournament_date_if_earlier(client):
    """If the scraped profile shows an earlier tournament than what's in
    the DB, first_tournament_date should be updated."""
    test_client, session_factory = client
    with session_factory() as session:
        session.add(Organizer(
            organizer_id=2720,
            first_tournament_date=date(2026, 6, 20),
        ))
        session.commit()

    html = (FIXTURE_DIR / "organizer_profile_200.html").read_text()
    respx.get("https://play.limitlesstcg.com/organizer/2720").mock(
        return_value=httpx.Response(200, text=html)
    )

    resp = test_client.get("/api/organizers/2720/scrape")

    assert resp.status_code == 200
    assert resp.json()["first_tournament_date"] == "2026-06-10"

    with session_factory() as session:
        org = session.get(Organizer, 2720)
        assert org.first_tournament_date == date(2026, 6, 10)


@respx.mock
def test_scrape_does_not_overwrite_onboarded_at(client):
    """Scraping should never set onboarded_at — only the scanner does that."""
    test_client, session_factory = client
    with session_factory() as session:
        session.add(Organizer(
            organizer_id=2720,
            onboarded_at=date(2026, 6, 1),
            first_tournament_date=date(2026, 6, 15),
        ))
        session.commit()

    html = (FIXTURE_DIR / "organizer_profile_200.html").read_text()
    respx.get("https://play.limitlesstcg.com/organizer/2720").mock(
        return_value=httpx.Response(200, text=html)
    )

    resp = test_client.get("/api/organizers/2720/scrape")

    assert resp.status_code == 200
    with session_factory() as session:
        org = session.get(Organizer, 2720)
        assert org.onboarded_at == date(2026, 6, 1)


@respx.mock
def test_scrape_returns_estimated_onboard_date_when_no_onboarded_at(client):
    """For organizers without an observed onboarded_at, the response should
    include an estimated_onboard_date derived from the regression."""
    test_client, session_factory = client

    with session_factory() as session:
        for oid, dt in [(2700, datetime(2026, 5, 1, tzinfo=timezone.utc)),
                        (2710, datetime(2026, 5, 15, tzinfo=timezone.utc)),
                        (2720, datetime(2026, 6, 1, tzinfo=timezone.utc))]:
            session.add(OrganizerActivity(
                organizer_id=oid, game="PTCG",
                first_tournament_date=dt, first_tournament_id=f"t{oid}",
                last_seen_date=dt, updated_at=dt,
            ))
        session.commit()

    html = (FIXTURE_DIR / "organizer_profile_200.html").read_text()
    respx.get("https://play.limitlesstcg.com/organizer/2720").mock(
        return_value=httpx.Response(200, text=html)
    )

    resp = test_client.get("/api/organizers/2720/scrape")

    assert resp.status_code == 200
    data = resp.json()
    assert data["onboarded_at"] is None
    assert data["estimated_onboard_date"] is not None


@respx.mock
def test_scrape_includes_detected_at_as_full_datetime(client):
    """FR30: detected_at should appear as a full ISO datetime in the scrape response."""
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
            detected_at=datetime(2026, 6, 10, 14, 30, 0, tzinfo=timezone.utc),
        ))
        session.commit()

    resp = test_client.get("/api/organizers/2720/scrape")

    assert resp.status_code == 200
    data = resp.json()
    assert data["detected_at"] == "2026-06-10T14:30:00Z"


@respx.mock
def test_scrape_returns_null_detected_at_when_not_set(client):
    """FR30: detected_at should be null when the organizer has no detected_at."""
    test_client, session_factory = client
    html = (FIXTURE_DIR / "organizer_profile_200.html").read_text()
    respx.get("https://play.limitlesstcg.com/organizer/2720").mock(
        return_value=httpx.Response(200, text=html)
    )
    with session_factory() as session:
        session.add(Organizer(
            organizer_id=2720,
            onboarded_at=date(2026, 6, 10),
        ))
        session.commit()

    resp = test_client.get("/api/organizers/2720/scrape")

    assert resp.status_code == 200
    data = resp.json()
    assert data["detected_at"] is None


@respx.mock
def test_scrape_omits_estimated_onboard_date_when_onboarded_at_exists(client):
    """If the organizer has a real onboarded_at, estimated_onboard_date should be null."""
    test_client, session_factory = client
    with session_factory() as session:
        session.add(Organizer(
            organizer_id=2720,
            onboarded_at=date(2026, 6, 1),
            first_tournament_date=date(2026, 6, 10),
        ))
        session.commit()

    html = (FIXTURE_DIR / "organizer_profile_200.html").read_text()
    respx.get("https://play.limitlesstcg.com/organizer/2720").mock(
        return_value=httpx.Response(200, text=html)
    )

    resp = test_client.get("/api/organizers/2720/scrape")

    assert resp.status_code == 200
    data = resp.json()
    assert data["onboarded_at"] == "2026-06-01"
    assert data["estimated_onboard_date"] is None
