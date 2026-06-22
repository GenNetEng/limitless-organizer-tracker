from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from app.db.models import ApplicationStatus, ApplicationStatusCheck, ResubmissionEvent

BASE_TIME = datetime(2026, 6, 1, tzinfo=timezone.utc)


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


def test_get_status_history_includes_review_note_when_present(client):
    test_client, session_factory = client
    with session_factory() as session:
        session.add(
            ApplicationStatusCheck(
                checked_at=BASE_TIME,
                status=ApplicationStatus.REJECTED,
                raw_text="Status: rejected",
                review_note="Your application was rejected. Please join the Discord.",
            )
        )
        session.commit()

    response = test_client.get("/api/status-history")

    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["review_note"] == "Your application was rejected. Please join the Discord."


def test_get_status_history_review_note_is_null_when_absent(client):
    test_client, session_factory = client
    _seed_status_checks(session_factory, 1)

    response = test_client.get("/api/status-history")

    assert response.status_code == 200
    assert response.json()["items"][0]["review_note"] is None


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


def test_post_status_check_dispatches_to_celery_and_returns_result(client, monkeypatch):
    test_client, session_factory = client

    with session_factory() as session:
        check = ApplicationStatusCheck(
            checked_at=BASE_TIME,
            status=ApplicationStatus.PENDING,
            raw_text="Status:pending",
        )
        session.add(check)
        session.commit()
        check_id = check.id

    mock_async_result = MagicMock()
    mock_async_result.get.return_value = check_id
    mock_task = MagicMock()
    mock_task.delay.return_value = mock_async_result
    monkeypatch.setattr("app.api.routers.status.check_application_status_task", mock_task)

    response = test_client.post("/api/status-check")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == check_id
    assert body["status"] == "pending"
    assert body["raw_text"] == "Status:pending"
    mock_task.delay.assert_called_once()
    mock_async_result.get.assert_called_once()


def test_post_status_check_returns_500_on_task_timeout(client, monkeypatch):
    test_client, _ = client

    mock_async_result = MagicMock()
    mock_async_result.get.side_effect = Exception("Task timed out")
    mock_task = MagicMock()
    mock_task.delay.return_value = mock_async_result
    monkeypatch.setattr("app.api.routers.status.check_application_status_task", mock_task)

    response = test_client.post("/api/status-check")

    assert response.status_code == 500
