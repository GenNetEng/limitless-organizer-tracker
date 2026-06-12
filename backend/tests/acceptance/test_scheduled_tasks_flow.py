"""Acceptance tests: scheduled status-check and resubmission tasks (FR2, FR5, NFR3).

Given a Celery beat schedule driven by `application_status_check_interval_hours`
and `resubmit_times_utc`,
When the status-check and resubmission tasks run,
Then each run is recorded as a timestamped datapoint in the database, and a
Discord notification is posted when the application status changes (FR2) or
whenever a resubmission occurs (FR5).
"""

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import respx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.tasks.resubmit_tasks as resubmit_tasks
import app.tasks.status_tasks as status_tasks
from app.celery_app import celery_app
from app.db.base import Base
from app.db.models import ApplicationStatus, ApplicationStatusCheck, ResubmissionEvent

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "html"
WEBHOOK_URL = "https://discord.com/api/webhooks/123/abc"


@contextmanager
def _fake_authenticated_page(page):
    yield page


@respx.mock
def test_status_change_is_recorded_and_notified(monkeypatch):
    # Given a prior "pending" status check on record
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    test_session_factory = sessionmaker(bind=engine)

    with test_session_factory() as seed_session:
        seed_session.add(
            ApplicationStatusCheck(
                checked_at=datetime(2026, 6, 11, 9, 0, tzinfo=timezone.utc),
                status=ApplicationStatus.PENDING,
                raw_text="Pending review",
            )
        )
        seed_session.commit()

    monkeypatch.setattr(status_tasks, "SessionLocal", test_session_factory)
    monkeypatch.setattr(status_tasks.settings, "discord_webhook_url", WEBHOOK_URL)

    mock_page = MagicMock()
    mock_page.content.return_value = (FIXTURE_DIR / "org_settings_approved.html").read_text()
    monkeypatch.setattr(
        status_tasks, "authenticated_page", lambda: _fake_authenticated_page(mock_page)
    )

    route = respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    # When the scheduled status-check task runs and the status has changed
    status_tasks.check_application_status_task.delay()

    # Then a new status-check datapoint is recorded and Discord is notified
    with test_session_factory() as session:
        checks = session.query(ApplicationStatusCheck).order_by(ApplicationStatusCheck.checked_at).all()
        assert len(checks) == 2
        assert checks[-1].status == ApplicationStatus.APPROVED

    assert route.called
    payload = route.calls.last.request.content.decode()
    assert "approved" in payload.lower()


@respx.mock
def test_resubmission_is_recorded_and_notified(monkeypatch):
    # Given an authenticated session and an empty resubmission log
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    test_session_factory = sessionmaker(bind=engine)

    monkeypatch.setattr(resubmit_tasks, "SessionLocal", test_session_factory)
    monkeypatch.setattr(resubmit_tasks.settings, "discord_webhook_url", WEBHOOK_URL)

    mock_page = MagicMock()
    mock_page.content.return_value = (FIXTURE_DIR / "org_settings_resubmit_success.html").read_text()
    monkeypatch.setattr(
        resubmit_tasks, "authenticated_page", lambda: _fake_authenticated_page(mock_page)
    )

    route = respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    # When the scheduled resubmission task runs
    resubmit_tasks.resubmit_application_task.delay()

    # Then the resubmission outcome is recorded and Discord is notified
    with test_session_factory() as session:
        events = session.query(ResubmissionEvent).all()
        assert len(events) == 1
        assert events[0].success is True
        assert events[0].discord_notified is True

    assert route.called
    payload = route.calls.last.request.content.decode()
    assert "succeeded" in payload.lower()
