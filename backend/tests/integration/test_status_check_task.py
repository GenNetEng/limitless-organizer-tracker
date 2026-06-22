from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import respx

import app.tasks.status_tasks as status_tasks
from app.celery_app import celery_app
from app.db.models import ApplicationStatus, ApplicationStatusCheck
from tests.conftest import fake_authenticated_page

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "html"
WEBHOOK_URL = "https://discord.com/api/webhooks/123/abc"


@respx.mock
def test_check_application_status_task_records_check_and_notifies_on_change(monkeypatch, db_session_factory):
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

    mock_page = MagicMock()
    mock_page.content.return_value = (FIXTURE_DIR / "application_approved.html").read_text()
    monkeypatch.setattr(
        status_tasks, "authenticated_page", lambda: fake_authenticated_page(mock_page)
    )

    route = respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    status_tasks.check_application_status_task.delay()

    with db_session_factory() as session:
        checks = session.query(ApplicationStatusCheck).order_by(ApplicationStatusCheck.checked_at).all()
        assert len(checks) == 2
        assert checks[-1].status == ApplicationStatus.APPROVED

    assert route.called
    payload = route.calls.last.request.content.decode()
    assert "approved" in payload.lower()


@respx.mock
def test_check_application_status_task_skips_notification_when_unchanged(monkeypatch, db_session_factory):
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

    mock_page = MagicMock()
    mock_page.content.return_value = (FIXTURE_DIR / "application_pending.html").read_text()
    monkeypatch.setattr(
        status_tasks, "authenticated_page", lambda: fake_authenticated_page(mock_page)
    )

    route = respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    status_tasks.check_application_status_task.delay()

    with db_session_factory() as session:
        checks = session.query(ApplicationStatusCheck).all()
        assert len(checks) == 2

    assert not route.called


def test_check_application_status_task_records_check_when_discord_webhook_unset(monkeypatch, db_session_factory):
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
    monkeypatch.setattr(status_tasks.settings, "discord_webhook_url", "")

    mock_page = MagicMock()
    mock_page.content.return_value = (FIXTURE_DIR / "application_approved.html").read_text()
    monkeypatch.setattr(
        status_tasks, "authenticated_page", lambda: fake_authenticated_page(mock_page)
    )

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    status_tasks.check_application_status_task.delay()

    with db_session_factory() as session:
        checks = session.query(ApplicationStatusCheck).order_by(ApplicationStatusCheck.checked_at).all()
        assert len(checks) == 2
        assert checks[-1].status == ApplicationStatus.APPROVED
