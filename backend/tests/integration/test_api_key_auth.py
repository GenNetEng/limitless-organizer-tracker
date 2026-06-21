import os

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.config
from app.config import Settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app


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

    fastapi_app.dependency_overrides[get_db] = override_get_db
    return TestClient(fastapi_app)


class TestApiKeyAuth:
    def setup_method(self):
        os.environ["API_KEYS"] = "test-key-1,test-key-2"
        app.config.settings = Settings()
        self.client = _make_client()

    def teardown_method(self):
        fastapi_app.dependency_overrides.clear()
        os.environ.pop("API_KEYS", None)
        app.config.settings = Settings()

    def test_api_route_returns_401_without_key(self):
        resp = self.client.get("/api/games")
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Missing or invalid API key"

    def test_api_route_returns_200_with_valid_key(self):
        resp = self.client.get("/api/games", headers={"X-API-Key": "test-key-1"})
        assert resp.status_code == 200

    def test_api_route_accepts_second_key(self):
        resp = self.client.get("/api/games", headers={"X-API-Key": "test-key-2"})
        assert resp.status_code == 200

    def test_api_route_returns_401_with_invalid_key(self):
        resp = self.client.get("/api/games", headers={"X-API-Key": "wrong-key"})
        assert resp.status_code == 401

    def test_healthz_does_not_require_key(self):
        resp = self.client.get("/healthz")
        assert resp.status_code == 200

    def test_docs_does_not_require_key(self):
        resp = self.client.get("/docs")
        assert resp.status_code == 200

    def test_openapi_does_not_require_key(self):
        resp = self.client.get("/openapi.json")
        assert resp.status_code == 200


class TestApiKeyDisabled:
    def setup_method(self):
        os.environ.pop("API_KEYS", None)
        app.config.settings = Settings()
        self.client = _make_client()

    def teardown_method(self):
        fastapi_app.dependency_overrides.clear()
        app.config.settings = Settings()

    def test_api_route_accessible_when_no_keys_configured(self):
        resp = self.client.get("/api/games")
        assert resp.status_code == 200
