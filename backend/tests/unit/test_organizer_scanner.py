from datetime import date, datetime, timezone

import httpx
import pytest
import respx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.tasks.organizer_tasks as organizer_tasks
from app.config import settings
from app.db.base import Base
from app.db.models import Organizer, OrganizerActivity


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as s:
        yield s


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
def test_creates_organizer_row_for_200_response(session, monkeypatch):
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 3)
    session.add(_activity(100))
    session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/101").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/102").mock(
        return_value=httpx.Response(404)
    )

    organizer_tasks.run_organizer_scan(session)

    organizer = session.get(Organizer, 101)
    assert organizer is not None
    assert organizer.onboarded_at == date.today()
    assert organizer.detected_at is not None


@respx.mock
def test_stops_at_404(session, monkeypatch):
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 5)
    session.add(_activity(100))
    session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/101").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/102").mock(
        return_value=httpx.Response(404)
    )

    organizer_tasks.run_organizer_scan(session)

    assert session.get(Organizer, 101) is not None
    assert session.get(Organizer, 102) is None
    assert session.get(Organizer, 103) is None


@respx.mock
def test_starts_from_max_id_across_both_tables(session, monkeypatch):
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 2)
    # OrganizerActivity has max ID 200, Organizer has max ID 150
    session.add(_activity(200))
    session.add(Organizer(organizer_id=150, onboarded_at=date(2026, 1, 1), detected_at=datetime(2026, 1, 1, tzinfo=timezone.utc)))
    session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/201").mock(
        return_value=httpx.Response(404)
    )

    organizer_tasks.run_organizer_scan(session)

    # Should have started at 201 (max of 200 and 150 is 200, +1 = 201)
    assert session.get(Organizer, 201) is None  # 404 → no row created
    assert session.get(Organizer, 151) is None  # should NOT have started from 151


@respx.mock
def test_respects_scan_limit(session, monkeypatch):
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 2)
    session.add(_activity(100))
    session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/101").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/102").mock(
        return_value=httpx.Response(200)
    )

    organizer_tasks.run_organizer_scan(session)

    assert session.get(Organizer, 101) is not None
    assert session.get(Organizer, 102) is not None
    # 103 would be beyond the limit of 2
    assert session.get(Organizer, 103) is None


@respx.mock
def test_skips_non_200_non_404_status_codes(session, monkeypatch):
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 3)
    session.add(_activity(100))
    session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/101").mock(
        return_value=httpx.Response(500)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/102").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/103").mock(
        return_value=httpx.Response(404)
    )

    organizer_tasks.run_organizer_scan(session)

    assert session.get(Organizer, 101) is None  # 500 → no row
    assert session.get(Organizer, 102) is not None  # 200 → row created


@respx.mock
def test_empty_tables_starts_from_id_1(session, monkeypatch):
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 2)

    respx.get(f"{settings.limitless_base_url}/organizer/1").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/2").mock(
        return_value=httpx.Response(404)
    )

    organizer_tasks.run_organizer_scan(session)

    assert session.get(Organizer, 1) is not None


@respx.mock
def test_returns_count_of_new_organizers_found(session, monkeypatch):
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 3)
    session.add(_activity(100))
    session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/101").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/102").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/103").mock(
        return_value=httpx.Response(404)
    )

    count = organizer_tasks.run_organizer_scan(session)

    assert count == 2
