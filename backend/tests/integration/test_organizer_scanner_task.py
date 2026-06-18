from datetime import date, datetime, timezone

import httpx
import respx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.tasks.organizer_tasks as organizer_tasks
from app.celery_app import celery_app
from app.config import settings
from app.db.base import Base
from app.db.models import Organizer, OrganizerActivity


def _activity(organizer_id, game="PTCG"):
    return OrganizerActivity(
        organizer_id=organizer_id,
        game=game,
        first_tournament_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        first_tournament_id="t1",
        last_seen_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


@respx.mock
def test_scan_new_organizers_task_inserts_row_and_commits(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    test_session_factory = sessionmaker(bind=engine)

    monkeypatch.setattr(organizer_tasks, "SessionLocal", test_session_factory)
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 2)

    with test_session_factory() as session:
        session.add(_activity(100))
        session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/101").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/102").mock(
        return_value=httpx.Response(404)
    )

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    organizer_tasks.scan_new_organizers_task.delay()

    with test_session_factory() as session:
        organizer = session.get(Organizer, 101)
        assert organizer is not None
        assert organizer.onboarded_at == date.today()
        assert organizer.detected_at is not None
