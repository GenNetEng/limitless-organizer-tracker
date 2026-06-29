"""Integration tests for POST /api/tasks/historical-organizer-scan (Phase 48, #137)."""

from unittest.mock import MagicMock


def test_trigger_historical_scan(client, monkeypatch):
    test_client, _ = client
    mock_task = MagicMock()
    mock_task.delay.return_value = MagicMock(id="mock-historical-scan-id")
    monkeypatch.setattr(
        "app.api.routers.tasks.historical_organizer_scan_task",
        mock_task,
    )

    response = test_client.post("/api/tasks/historical-organizer-scan")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "started"
    assert "historical" in body["result"].lower()
    mock_task.delay.assert_called_once()


def test_historical_scan_in_task_triggers(client):
    """The historical-organizer-scan trigger must appear in GET /api/admin/tasks."""
    test_client, _ = client

    response = test_client.get("/api/admin/tasks")

    assert response.status_code == 200
    triggers = response.json()
    endpoints = [t["endpoint"] for t in triggers]
    assert "/api/tasks/historical-organizer-scan" in endpoints
