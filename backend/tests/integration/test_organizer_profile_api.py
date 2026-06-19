from datetime import date, datetime, timezone
from pathlib import Path

import httpx
import respx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import Organizer, OrganizerActivity
from app.db.session import get_db
from app.main import app

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "html"


def _make_client():
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
    return TestClient(app), test_session_factory


class TestScrapeEndpoint:
    def setup_method(self):
        self.client, self.session_factory = _make_client()

    def teardown_method(self):
        app.dependency_overrides.clear()

    @respx.mock
    def test_scrape_returns_organizer_profile(self):
        html = (FIXTURE_DIR / "organizer_profile_200.html").read_text()
        respx.get("https://play.limitlesstcg.com/organizer/2720").mock(
            return_value=httpx.Response(200, text=html)
        )

        resp = self.client.get("/api/organizers/2720/scrape")

        assert resp.status_code == 200
        data = resp.json()
        assert data["organizer_id"] == 2720
        assert data["name"] == "Pudding Weekly"
        assert len(data["upcoming_tournaments"]) == 2
        assert len(data["recent_tournaments"]) == 2
        assert data["upcoming_tournaments"][0]["tournament_id"] == "6a30c6e62d97f3b0c2617d33"

    @respx.mock
    def test_scrape_returns_404_when_organizer_not_found(self):
        respx.get("https://play.limitlesstcg.com/organizer/99999").mock(
            return_value=httpx.Response(404)
        )

        resp = self.client.get("/api/organizers/99999/scrape")

        assert resp.status_code == 404

    @respx.mock
    def test_scrape_returns_404_when_page_has_no_profile(self):
        respx.get("https://play.limitlesstcg.com/organizer/88888").mock(
            return_value=httpx.Response(200, text="<html><body>Not a profile</body></html>")
        )

        resp = self.client.get("/api/organizers/88888/scrape")

        assert resp.status_code == 404


class TestHighestIdEndpoint:
    def setup_method(self):
        self.client, self.session_factory = _make_client()

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_returns_highest_id_from_organizer_table(self):
        with self.session_factory() as session:
            session.add(Organizer(organizer_id=2700, onboarded_at=date(2026, 6, 10)))
            session.add(Organizer(organizer_id=2720, onboarded_at=date(2026, 6, 18)))
            session.commit()

        resp = self.client.get("/api/organizers/highest-id")

        assert resp.status_code == 200
        assert resp.json() == {"organizer_id": 2720}

    def test_falls_back_to_organizer_activity_when_organizer_table_empty(self):
        with self.session_factory() as session:
            session.add(OrganizerActivity(
                organizer_id=2500,
                game="Pokemon",
                first_tournament_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
                first_tournament_id="t1",
                last_seen_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
                updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            ))
            session.commit()

        resp = self.client.get("/api/organizers/highest-id")

        assert resp.status_code == 200
        assert resp.json() == {"organizer_id": 2500}

    def test_returns_404_when_both_tables_empty(self):
        resp = self.client.get("/api/organizers/highest-id")

        assert resp.status_code == 404
