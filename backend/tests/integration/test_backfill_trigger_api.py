"""Integration tests for POST /api/tasks/backfill-organizers (Phase 47, #136)."""

from unittest.mock import MagicMock


def test_trigger_backfill_organizers(client, monkeypatch):
    test_client, _ = client
    mock_task = MagicMock()
    mock_task.delay.return_value = MagicMock(id="mock-backfill-id")
    monkeypatch.setattr(
        "app.api.routers.tasks.backfill_organizers_from_tournaments_task",
        mock_task,
    )

    response = test_client.post("/api/tasks/backfill-organizers")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "started"
    assert "backfill" in body["result"].lower()
    mock_task.delay.assert_called_once()


def test_backfill_organizers_in_task_triggers(client):
    """The backfill-organizers trigger must appear in GET /api/admin/tasks."""
    test_client, _ = client

    response = test_client.get("/api/admin/tasks")

    assert response.status_code == 200
    triggers = response.json()
    endpoints = [t["endpoint"] for t in triggers]
    assert "/api/tasks/backfill-organizers" in endpoints
