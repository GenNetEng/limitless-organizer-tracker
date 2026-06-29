"""Acceptance test: full scheduled task flow (FR2, FR3, FR4, FR5, NFR3).

Exercises both scheduled tasks in sequence against a single shared database,
simulating what happens on a real Celery beat cycle: the status-check task
runs first and detects a status change, then the resubmission task runs and
records its outcome. Both produce Discord notifications. This is the
acceptance-level scenario that the per-task integration tests do not cover.
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import respx

import app.tasks.resubmit_tasks as resubmit_tasks
import app.tasks.status_tasks as status_tasks
from app.celery_app import celery_app
from app.db.models import ApplicationStatus, ApplicationStatusCheck, ResubmissionEvent
from tests.helpers import fake_authenticated_page

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "html"
WEBHOOK_URL = "https://discord.com/api/webhooks/123/abc"


@respx.mock
def test_full_beat_cycle_status_check_then_resubmit(monkeypatch, db_session_factory):
    """Simulate a single Celery beat cycle: status check detects approval,
    then resubmission runs and records success — both against the same DB."""

    # Seed: a prior "pending" status check exists
    with db_session_factory() as seed_session:
        seed_session.add(
            ApplicationStatusCheck(
                checked_at=datetime(2026, 6, 11, 9, 0, tzinfo=timezone.utc),
                status=ApplicationStatus.PENDING,
                raw_text="Pending review",
            )
        )
        seed_session.commit()

    monkeypatch.setattr("app.db.session.SessionLocal", db_session_factory)
    monkeypatch.setattr(status_tasks.settings, "discord_webhook_url", WEBHOOK_URL)
    monkeypatch.setattr(status_tasks.settings, "limitless_username", "test@example.com")
    monkeypatch.setattr(status_tasks.settings, "limitless_password", "testpass")
    monkeypatch.setattr(status_tasks.settings, "limitless_application_id", "test-app-id")
    monkeypatch.setattr(resubmit_tasks.settings, "discord_webhook_url", WEBHOOK_URL)

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    # --- Phase 1: status-check task detects a change to "approved" ---
    status_page = MagicMock()
    status_page.content.return_value = (FIXTURE_DIR / "application_approved.html").read_text()
    monkeypatch.setattr(
        status_tasks, "authenticated_page", lambda: fake_authenticated_page(status_page)
    )

    status_route = respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

    status_tasks.check_application_status_task.delay()

    with db_session_factory() as session:
        checks = session.query(ApplicationStatusCheck).order_by(ApplicationStatusCheck.checked_at).all()
        assert len(checks) == 2
        assert checks[0].status == ApplicationStatus.PENDING
        assert checks[1].status == ApplicationStatus.APPROVED

    assert status_route.called
    assert "approved" in status_route.calls.last.request.content.decode().lower()

    # --- Phase 2: resubmission task runs and records success ---
    form_data = {"name": "Test", "discord": "user", "message": "msg", "answers": {"q1": "a1"}}
    resubmit_page = MagicMock()
    resubmit_page.evaluate.side_effect = [None, form_data, {"status": "ok", "ok": True}]
    monkeypatch.setattr(
        resubmit_tasks, "authenticated_page", lambda: fake_authenticated_page(resubmit_page)
    )

    resubmit_route = respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

    resubmit_tasks.resubmit_application_task.delay()

    with db_session_factory() as session:
        events = session.query(ResubmissionEvent).all()
        assert len(events) == 1
        assert events[0].success is True
        assert events[0].discord_notified is True

    assert resubmit_route.called
    assert "succeeded" in resubmit_route.calls.last.request.content.decode().lower()

    # --- Verify: both tasks wrote to the same database ---
    with db_session_factory() as session:
        assert session.query(ApplicationStatusCheck).count() == 2
        assert session.query(ResubmissionEvent).count() == 1
