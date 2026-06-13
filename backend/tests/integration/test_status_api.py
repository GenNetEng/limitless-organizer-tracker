from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest
import respx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.tasks.status_tasks as status_tasks
from app.db.base import Base
from app.db.models import ApplicationStatus, ApplicationStatusCheck, ResubmissionEvent
from app.db.session import get_db
from app.main import app

BASE_TIME = datetime(2026, 6, 1, tzinfo=timezone.utc)
FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "html"
WEBHOOK_URL = "https://discord.com/api/webhooks/123/abc"


@contextmanager
def _fake_authenticated_page(page):
    yield page


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


def _seed_status_checks(session_factory, count):
    with session_factory() as session:
        for i in range(count):
            session.add(
                ApplicationStatusCheck(
                    checked_at=BASE_TIME + timedelta(hours=i),
                    status=ApplicationStatus.PENDING if i % 2 == 0 else ApplicationStatus.APPROVED,
                    raw_text=f"check {i}",
                )
            )
        session.commit()


def _seed_resubmissions(session_factory, count):
    with session_factory() as session:
        for i in range(count):
            session.add(
                ResubmissionEvent(
                    submitted_at=BASE_TIME + timedelta(hours=i),
                    success=i % 2 == 0,
                    discord_notified=True,
                )
            )
        session.commit()


def test_get_status_history_returns_envelope_ordered_by_checked_at_desc(client):
    test_client, session_factory = client
    _seed_status_checks(session_factory, 3)

    response = test_client.get("/api/status-history")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert [item["raw_text"] for item in body["items"]] == ["check 2", "check 1", "check 0"]
    assert body["items"][0]["status"] == "pending"


def test_get_status_history_supports_limit_and_offset(client):
    test_client, session_factory = client
    _seed_status_checks(session_factory, 5)

    response = test_client.get("/api/status-history", params={"limit": 2, "offset": 1})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 5
    assert body["limit"] == 2
    assert body["offset"] == 1
    assert [item["raw_text"] for item in body["items"]] == ["check 3", "check 2"]


def test_get_status_history_rejects_limit_above_max(client):
    test_client, _ = client

    response = test_client.get("/api/status-history", params={"limit": 201})

    assert response.status_code == 422


def test_get_status_history_empty_db(client):
    test_client, _ = client

    response = test_client.get("/api/status-history")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 50, "offset": 0}


def test_get_resubmissions_returns_envelope_ordered_by_submitted_at_desc(client):
    test_client, session_factory = client
    _seed_resubmissions(session_factory, 3)

    response = test_client.get("/api/resubmissions")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert [item["success"] for item in body["items"]] == [True, False, True]


def test_get_resubmissions_supports_limit_and_offset(client):
    test_client, session_factory = client
    _seed_resubmissions(session_factory, 5)

    response = test_client.get("/api/resubmissions", params={"limit": 2, "offset": 1})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 5
    assert body["limit"] == 2
    assert body["offset"] == 1
    assert len(body["items"]) == 2


@respx.mock
def test_post_status_check_records_and_returns_result(client, monkeypatch):
    test_client, session_factory = client

    monkeypatch.setattr(status_tasks.settings, "discord_webhook_url", WEBHOOK_URL)
    mock_page = MagicMock()
    mock_page.content.return_value = (FIXTURE_DIR / "application_pending.html").read_text()
    monkeypatch.setattr(
        status_tasks, "authenticated_page", lambda: _fake_authenticated_page(mock_page)
    )
    route = respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

    response = test_client.post("/api/status-check")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending"
    assert body["raw_text"]

    with session_factory() as session:
        checks = session.query(ApplicationStatusCheck).all()
        assert len(checks) == 1

    # First-ever check has nothing to compare against, so no Discord notice.
    assert not route.called


@respx.mock
def test_post_status_check_notifies_on_status_change(client, monkeypatch):
    test_client, session_factory = client
    with session_factory() as session:
        session.add(
            ApplicationStatusCheck(
                checked_at=BASE_TIME,
                status=ApplicationStatus.PENDING,
                raw_text="Pending review",
            )
        )
        session.commit()

    monkeypatch.setattr(status_tasks.settings, "discord_webhook_url", WEBHOOK_URL)
    mock_page = MagicMock()
    mock_page.content.return_value = (FIXTURE_DIR / "application_approved.html").read_text()
    monkeypatch.setattr(
        status_tasks, "authenticated_page", lambda: _fake_authenticated_page(mock_page)
    )
    route = respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

    response = test_client.post("/api/status-check")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"

    with session_factory() as session:
        checks = session.query(ApplicationStatusCheck).all()
        assert len(checks) == 2

    assert route.called
