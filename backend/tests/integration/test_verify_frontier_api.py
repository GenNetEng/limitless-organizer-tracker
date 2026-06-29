"""Integration tests for POST /api/tasks/verify-frontier-regression (Phase 49, #139)."""

from unittest.mock import MagicMock


def test_trigger_verify_frontier_regression(client, monkeypatch):
    test_client, _ = client
    mock_task = MagicMock()
    mock_task.delay.return_value = MagicMock(id="mock-verify-frontier-id")
    monkeypatch.setattr(
        "app.api.routers.tasks.verify_frontier_regression_task",
        mock_task,
    )

    response = test_client.post("/api/tasks/verify-frontier-regression")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "started"
    assert "frontier" in body["result"].lower()
    mock_task.delay.assert_called_once()


def test_verify_frontier_regression_in_task_triggers(client):
    """The verify-frontier-regression trigger must appear in GET /api/admin/tasks."""
    test_client, _ = client

    response = test_client.get("/api/admin/tasks")

    assert response.status_code == 200
    triggers = response.json()
    endpoints = [t["endpoint"] for t in triggers]
    assert "/api/tasks/verify-frontier-regression" in endpoints
