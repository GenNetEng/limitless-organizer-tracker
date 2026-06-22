"""Integration tests for on-demand Celery task trigger endpoints (#69)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.db.models import ResubmissionEvent


def _mock_task(monkeypatch, attr_path, return_value):
    mock_async_result = MagicMock()
    mock_async_result.get.return_value = return_value
    mock_async_result.id = "test-task-id"
    mock_task = MagicMock()
    mock_task.delay.return_value = mock_async_result
    monkeypatch.setattr(attr_path, mock_task)
    return mock_task


# --- POST /api/tasks/ingest-tournaments ---


def test_trigger_ingest_tournaments(client, monkeypatch):
    test_client, _ = client
    mock = _mock_task(
        monkeypatch,
        "app.api.routers.tasks.ingest_tournaments_task",
        42,
    )

    response = test_client.post("/api/tasks/ingest-tournaments")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["result"] == "Ingested 42 tournaments"
    mock.delay.assert_called_once()


def test_trigger_ingest_tournaments_returns_500_on_failure(client, monkeypatch):
    test_client, _ = client
    mock_async_result = MagicMock()
    mock_async_result.get.side_effect = Exception("boom")
    mock_task = MagicMock()
    mock_task.delay.return_value = mock_async_result
    monkeypatch.setattr("app.api.routers.tasks.ingest_tournaments_task", mock_task)

    response = test_client.post("/api/tasks/ingest-tournaments")

    assert response.status_code == 500


# --- POST /api/tasks/scan-organizers ---


def test_trigger_scan_organizers(client, monkeypatch):
    test_client, _ = client
    mock_task = MagicMock()
    mock_task.delay.return_value = MagicMock(id="mock-task-id")
    monkeypatch.setattr("app.api.routers.tasks.audit_organizer_scan_task", mock_task)

    response = test_client.post("/api/tasks/scan-organizers")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "started"
    mock_task.delay.assert_called_once()


# --- POST /api/tasks/resubmit-application ---


def test_trigger_resubmit_application(client, monkeypatch):
    test_client, session_factory = client

    with session_factory() as session:
        event = ResubmissionEvent(
            submitted_at=datetime(2026, 6, 22, tzinfo=timezone.utc),
            success=True,
            discord_notified=True,
        )
        session.add(event)
        session.commit()
        event_id = event.id

    mock = _mock_task(
        monkeypatch,
        "app.api.routers.tasks.resubmit_application_task",
        event_id,
    )

    response = test_client.post("/api/tasks/resubmit-application")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == event_id
    assert body["success"] is True
    mock.delay.assert_called_once()


def test_trigger_resubmit_application_returns_500_on_failure(client, monkeypatch):
    test_client, _ = client
    mock_async_result = MagicMock()
    mock_async_result.get.side_effect = Exception("boom")
    mock_task = MagicMock()
    mock_task.delay.return_value = mock_async_result
    monkeypatch.setattr("app.api.routers.tasks.resubmit_application_task", mock_task)

    response = test_client.post("/api/tasks/resubmit-application")

    assert response.status_code == 500
