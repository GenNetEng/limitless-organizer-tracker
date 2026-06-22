from datetime import date, datetime, timezone

import httpx
import respx

import app.tasks.organizer_tasks as organizer_tasks
from app.celery_app import celery_app
from app.config import settings
from app.db.models import Organizer


@respx.mock
def test_scan_new_organizers_task_dispatches_audit_and_scans(monkeypatch, db_session_factory):
    monkeypatch.setattr("app.db.session.SessionLocal", db_session_factory)
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 2)

    with db_session_factory() as session:
        session.add(Organizer(organizer_id=2730, onboarded_at=date(2026, 6, 22), detected_at=datetime(2026, 6, 22, tzinfo=timezone.utc)))
        session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/2731").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/2732").mock(
        return_value=httpx.Response(404)
    )

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    organizer_tasks.scan_new_organizers_task.delay()

    with db_session_factory() as session:
        organizer = session.get(Organizer, 2731)
        assert organizer is not None
        assert organizer.onboarded_at == datetime.now(timezone.utc).date()
        assert organizer.detected_at is not None
