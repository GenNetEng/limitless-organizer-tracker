from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import ApplicationStatus, ApplicationStatusCheck, ResubmissionEvent
from app.db.session import get_db
from app.main import app

BASE_TIME = datetime(2026, 6, 1, tzinfo=timezone.utc)


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
