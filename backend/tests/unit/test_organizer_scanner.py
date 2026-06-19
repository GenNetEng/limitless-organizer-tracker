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


def _scanned(organizer_id):
    """A confirmed-scanned organizer row (advances the watermark)."""
    return Organizer(
        organizer_id=organizer_id,
        onboarded_at=date(2026, 1, 1),
        detected_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


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
    session.add(_scanned(100))
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
    assert organizer.onboarded_at == datetime.now(timezone.utc).date()
    assert organizer.detected_at is not None


@respx.mock
def test_stops_at_404(session, monkeypatch):
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 5)
    session.add(_scanned(100))
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
def test_starts_from_highest_scanned_organizer_id(session, monkeypatch):
    """Watermark uses only scanned organizers (onboarded_at IS NOT NULL), not OrganizerActivity."""
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 2)
    # Scanned organizer max = 150; OrganizerActivity has a much higher ID (200)
    # but that must NOT advance the watermark past 150.
    session.add(_activity(200))
    session.add(Organizer(organizer_id=150, onboarded_at=date(2026, 1, 1), detected_at=datetime(2026, 1, 1, tzinfo=timezone.utc)))
    session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/151").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/152").mock(
        return_value=httpx.Response(404)
    )

    organizer_tasks.run_organizer_scan(session)

    # Scan should have started at 151 (scanned max=150, +1), not 201
    assert session.get(Organizer, 151) is not None
    assert session.get(Organizer, 201) is None  # never reached


@respx.mock
def test_activity_data_does_not_advance_watermark(session, monkeypatch):
    """OrganizerActivity rows must not push the watermark past the scanner's own position.

    Scenario: tournament ingestion creates activity for ID 200 while the scanner's
    highest confirmed ID is 50. After the fix, start_id = 51 (based only on scanned
    organizers), not 201.
    """
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 2)
    # Scanned organizer at 50; activity data exists for a much higher ID
    session.add(Organizer(organizer_id=50, onboarded_at=date(2026, 1, 1), detected_at=datetime(2026, 1, 1, tzinfo=timezone.utc)))
    session.add(_activity(200))
    session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/51").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/52").mock(
        return_value=httpx.Response(404)
    )

    organizer_tasks.run_organizer_scan(session)

    assert session.get(Organizer, 51) is not None   # scanner reached 51
    assert session.get(Organizer, 201) is None       # never jumped to 201


@respx.mock
def test_respects_scan_limit(session, monkeypatch):
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 2)
    session.add(_scanned(100))
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
def test_stops_on_unexpected_status_code(session, monkeypatch):
    """Non-200/non-404 status codes stop the scan so the ID can be retried next run."""
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 3)
    session.add(_scanned(100))
    session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/101").mock(
        return_value=httpx.Response(500)
    )

    organizer_tasks.run_organizer_scan(session)

    assert session.get(Organizer, 101) is None  # 500 → no row
    assert session.get(Organizer, 102) is None  # scan stopped; 102 not reached


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
    session.add(_scanned(100))
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


@respx.mock
def test_backfill_counts_toward_found(session, monkeypatch):
    """Updating an ingestion-created stub (onboarded_at=None) counts as found."""
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 2)
    session.add(_scanned(99))
    session.add(Organizer(organizer_id=100, onboarded_at=None))
    session.commit()

    # MAX(onboarded_at IS NOT NULL) = 99 → start = 100 (the stub)
    respx.get(f"{settings.limitless_base_url}/organizer/100").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/101").mock(
        return_value=httpx.Response(404)
    )

    count = organizer_tasks.run_organizer_scan(session)

    assert count == 1
    assert session.get(Organizer, 100).onboarded_at == datetime.now(timezone.utc).date()
