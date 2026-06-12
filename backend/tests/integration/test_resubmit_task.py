from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import respx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.tasks.resubmit_tasks as resubmit_tasks
from app.celery_app import celery_app
from app.db.base import Base
from app.db.models import ResubmissionEvent

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "html"
WEBHOOK_URL = "https://discord.com/api/webhooks/123/abc"


@contextmanager
def _fake_authenticated_page(page):
    yield page


@respx.mock
def test_resubmit_application_task_records_event_and_notifies_on_success(monkeypatch):
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

    resubmit_tasks.resubmit_application_task.delay()

    with test_session_factory() as session:
        events = session.query(ResubmissionEvent).all()
        assert len(events) == 1
        assert events[0].success is True
        assert events[0].discord_notified is True

    assert route.called
    payload = route.calls.last.request.content.decode()
    assert "succeeded" in payload.lower()


@respx.mock
def test_resubmit_application_task_records_event_on_failure(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    test_session_factory = sessionmaker(bind=engine)

    monkeypatch.setattr(resubmit_tasks, "SessionLocal", test_session_factory)
    monkeypatch.setattr(resubmit_tasks.settings, "discord_webhook_url", WEBHOOK_URL)

    mock_page = MagicMock()
    mock_page.content.return_value = (FIXTURE_DIR / "org_settings_resubmit_failure.html").read_text()
    monkeypatch.setattr(
        resubmit_tasks, "authenticated_page", lambda: _fake_authenticated_page(mock_page)
    )

    route = respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    resubmit_tasks.resubmit_application_task.delay()

    with test_session_factory() as session:
        events = session.query(ResubmissionEvent).all()
        assert len(events) == 1
        assert events[0].success is False

    assert route.called
    payload = route.calls.last.request.content.decode()
    assert "failed" in payload.lower()
