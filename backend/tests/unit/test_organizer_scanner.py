from datetime import date, datetime, timezone

import httpx
import respx

import app.tasks.organizer_tasks as organizer_tasks
from app.config import settings
from app.db.models import Organizer, OrganizerActivity


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
def test_creates_organizer_row_for_200_response(db_session, monkeypatch):
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 3)
    db_session.add(_scanned(100))
    db_session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/101").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/102").mock(
        return_value=httpx.Response(404)
    )

    organizer_tasks.run_organizer_scan(db_session)

    organizer = db_session.get(Organizer, 101)
    assert organizer is not None
    assert organizer.onboarded_at == datetime.now(timezone.utc).date()
    assert organizer.detected_at is not None


@respx.mock
def test_stops_at_404(db_session, monkeypatch):
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 5)
    db_session.add(_scanned(100))
    db_session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/101").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/102").mock(
        return_value=httpx.Response(404)
    )

    organizer_tasks.run_organizer_scan(db_session)

    assert db_session.get(Organizer, 101) is not None
    assert db_session.get(Organizer, 102) is None
    assert db_session.get(Organizer, 103) is None


@respx.mock
def test_starts_from_highest_scanned_organizer_id(db_session, monkeypatch):
    """Watermark uses only scanned organizers (onboarded_at IS NOT NULL), not OrganizerActivity."""
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 2)
    # Scanned organizer max = 150; OrganizerActivity has a much higher ID (200)
    # but that must NOT advance the watermark past 150.
    db_session.add(_activity(200))
    db_session.add(Organizer(organizer_id=150, onboarded_at=date(2026, 1, 1), detected_at=datetime(2026, 1, 1, tzinfo=timezone.utc)))
    db_session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/151").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/152").mock(
        return_value=httpx.Response(404)
    )

    organizer_tasks.run_organizer_scan(db_session)

    # Scan should have started at 151 (scanned max=150, +1), not 201
    assert db_session.get(Organizer, 151) is not None
    assert db_session.get(Organizer, 201) is None  # never reached


@respx.mock
def test_activity_data_does_not_advance_watermark(db_session, monkeypatch):
    """OrganizerActivity rows must not push the watermark past the scanner's own position.

    Scenario: tournament ingestion creates activity for ID 200 while the scanner's
    highest confirmed ID is 50. After the fix, start_id = 51 (based only on scanned
    organizers), not 201.
    """
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 2)
    # Scanned organizer at 50; activity data exists for a much higher ID
    db_session.add(Organizer(organizer_id=50, onboarded_at=date(2026, 1, 1), detected_at=datetime(2026, 1, 1, tzinfo=timezone.utc)))
    db_session.add(_activity(200))
    db_session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/51").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/52").mock(
        return_value=httpx.Response(404)
    )

    organizer_tasks.run_organizer_scan(db_session)

    assert db_session.get(Organizer, 51) is not None   # scanner reached 51
    assert db_session.get(Organizer, 201) is None       # never jumped to 201


@respx.mock
def test_respects_scan_limit(db_session, monkeypatch):
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 2)
    db_session.add(_scanned(100))
    db_session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/101").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/102").mock(
        return_value=httpx.Response(200)
    )

    organizer_tasks.run_organizer_scan(db_session)

    assert db_session.get(Organizer, 101) is not None
    assert db_session.get(Organizer, 102) is not None
    # 103 would be beyond the limit of 2
    assert db_session.get(Organizer, 103) is None


@respx.mock
def test_stops_on_unexpected_status_code(db_session, monkeypatch):
    """Non-200/non-404 status codes stop the scan so the ID can be retried next run."""
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 3)
    db_session.add(_scanned(100))
    db_session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/101").mock(
        return_value=httpx.Response(500)
    )

    organizer_tasks.run_organizer_scan(db_session)

    assert db_session.get(Organizer, 101) is None  # 500 → no row
    assert db_session.get(Organizer, 102) is None  # scan stopped; 102 not reached


@respx.mock
def test_empty_tables_starts_from_id_1(db_session, monkeypatch):
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 2)

    respx.get(f"{settings.limitless_base_url}/organizer/1").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/2").mock(
        return_value=httpx.Response(404)
    )

    organizer_tasks.run_organizer_scan(db_session)

    assert db_session.get(Organizer, 1) is not None


@respx.mock
def test_returns_count_of_new_organizers_found(db_session, monkeypatch):
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 3)
    db_session.add(_scanned(100))
    db_session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/101").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/102").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/103").mock(
        return_value=httpx.Response(404)
    )

    count = organizer_tasks.run_organizer_scan(db_session)

    assert count == 2


@respx.mock
def test_backfill_counts_toward_found(db_session, monkeypatch):
    """Updating an ingestion-created stub (onboarded_at=None) counts as found."""
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 2)
    db_session.add(_scanned(99))
    db_session.add(Organizer(organizer_id=100, onboarded_at=None))
    db_session.commit()

    # MAX(onboarded_at IS NOT NULL) = 99 → start = 100 (the stub)
    respx.get(f"{settings.limitless_base_url}/organizer/100").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/101").mock(
        return_value=httpx.Response(404)
    )

    count = organizer_tasks.run_organizer_scan(db_session)

    assert count == 1
    assert db_session.get(Organizer, 100).onboarded_at == datetime.now(timezone.utc).date()
