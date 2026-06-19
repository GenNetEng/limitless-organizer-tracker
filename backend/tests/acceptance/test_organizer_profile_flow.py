"""Acceptance tests for FR16 (highest-ID API) and FR18 (organizer profile scrape).

FR15 (frontend display) is covered in Phase 17.
"""

from datetime import date
from pathlib import Path

import httpx
import respx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import Organizer
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


class TestFR18_OrganizerProfileScrape:
    """FR18: GET /api/organizers/{id}/scrape returns organizer name and
    tournament list parsed from the public Limitless profile page."""

    def setup_method(self):
        self.client, self.session_factory = _make_client()

    def teardown_method(self):
        app.dependency_overrides.clear()

    @respx.mock
    def test_given_valid_organizer_id_returns_name_and_tournaments(self):
        html = (FIXTURE_DIR / "organizer_profile_200.html").read_text()
        respx.get("https://play.limitlesstcg.com/organizer/2720").mock(
            return_value=httpx.Response(200, text=html)
        )

        resp = self.client.get("/api/organizers/2720/scrape")

        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Pudding Weekly"
        assert isinstance(data["upcoming_tournaments"], list)
        assert isinstance(data["recent_tournaments"], list)
        assert all(
            {"tournament_id", "name", "date", "game", "players"} <= set(t.keys())
            for t in data["upcoming_tournaments"] + data["recent_tournaments"]
        )

    @respx.mock
    def test_given_nonexistent_organizer_id_returns_404(self):
        respx.get("https://play.limitlesstcg.com/organizer/99999").mock(
            return_value=httpx.Response(404)
        )

        resp = self.client.get("/api/organizers/99999/scrape")

        assert resp.status_code == 404


class TestFR16_HighestOrganizerId:
    """FR16: GET /api/organizers/highest-id returns the highest organizer ID
    currently in the Organizer table."""

    def setup_method(self):
        self.client, self.session_factory = _make_client()

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_given_organizers_exist_returns_highest_id(self):
        with self.session_factory() as session:
            session.add(Organizer(organizer_id=2700, onboarded_at=date(2026, 6, 10)))
            session.add(Organizer(organizer_id=2720, onboarded_at=date(2026, 6, 18)))
            session.commit()

        resp = self.client.get("/api/organizers/highest-id")

        assert resp.status_code == 200
        assert resp.json()["organizer_id"] == 2720
