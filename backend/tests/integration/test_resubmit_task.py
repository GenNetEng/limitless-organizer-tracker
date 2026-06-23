from unittest.mock import MagicMock

import httpx
import respx

import app.tasks.resubmit_tasks as resubmit_tasks
from app.celery_app import celery_app
from app.db.models import ResubmissionEvent
from tests.helpers import fake_authenticated_page

WEBHOOK_URL = "https://discord.com/api/webhooks/123/abc"

FORM_DATA = {"name": "Test Org", "discord": "user", "message": "msg", "answers": {"q1": "a1"}}


def _mock_resubmit_page(server_response):
    mock_page = MagicMock()
    mock_page.evaluate.side_effect = [None, FORM_DATA, server_response]
    return mock_page


@respx.mock
def test_resubmit_application_task_records_event_and_notifies_on_success(monkeypatch, db_session_factory):
    monkeypatch.setattr("app.db.session.SessionLocal", db_session_factory)
    monkeypatch.setattr(resubmit_tasks.settings, "discord_webhook_url", WEBHOOK_URL)

    mock_page = _mock_resubmit_page({"status": "ok", "ok": True})
    monkeypatch.setattr(
        resubmit_tasks, "authenticated_page", lambda: fake_authenticated_page(mock_page)
    )

    route = respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    resubmit_tasks.resubmit_application_task.delay()

    with db_session_factory() as session:
        events = session.query(ResubmissionEvent).all()
        assert len(events) == 1
        assert events[0].success is True
        assert events[0].discord_notified is True

    assert route.called
    payload = route.calls.last.request.content.decode()
    assert "succeeded" in payload.lower()


@respx.mock
def test_resubmit_application_task_records_event_on_failure(monkeypatch, db_session_factory):
    monkeypatch.setattr("app.db.session.SessionLocal", db_session_factory)
    monkeypatch.setattr(resubmit_tasks.settings, "discord_webhook_url", WEBHOOK_URL)

    mock_page = _mock_resubmit_page({"status": "error", "ok": False})
    monkeypatch.setattr(
        resubmit_tasks, "authenticated_page", lambda: fake_authenticated_page(mock_page)
    )

    route = respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    resubmit_tasks.resubmit_application_task.delay()

    with db_session_factory() as session:
        events = session.query(ResubmissionEvent).all()
        assert len(events) == 1
        assert events[0].success is False

    assert route.called
    payload = route.calls.last.request.content.decode()
    assert "failed" in payload.lower()


def test_resubmit_application_task_records_event_when_discord_webhook_unset(monkeypatch, db_session_factory):
    monkeypatch.setattr("app.db.session.SessionLocal", db_session_factory)
    monkeypatch.setattr(resubmit_tasks.settings, "discord_webhook_url", "")

    mock_page = _mock_resubmit_page({"status": "ok", "ok": True})
    monkeypatch.setattr(
        resubmit_tasks, "authenticated_page", lambda: fake_authenticated_page(mock_page)
    )

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    resubmit_tasks.resubmit_application_task.delay()

    with db_session_factory() as session:
        events = session.query(ResubmissionEvent).all()
        assert len(events) == 1
        assert events[0].success is True
        assert events[0].discord_notified is False
