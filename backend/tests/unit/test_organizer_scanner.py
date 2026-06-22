from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

import httpx
import respx

import app.tasks.organizer_tasks as organizer_tasks
from app.config import settings
from app.db.models import Organizer, OrganizerActivity

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "html"


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
def test_audit_dispatches_tasks_for_200_responses(db_session_factory, monkeypatch):
    monkeypatch.setattr("app.db.session.SessionLocal", db_session_factory)
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 3)
    with db_session_factory() as session:
        session.add(_scanned(100))
        session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/101").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/102").mock(
        return_value=httpx.Response(404)
    )

    with patch.object(organizer_tasks.scan_single_organizer_task, "delay") as mock_delay:
        organizer_tasks.audit_organizer_scan_task()

    assert mock_delay.call_count == 1
    mock_delay.assert_called_with(organizer_id=101)


@respx.mock
def test_audit_stops_at_404(db_session_factory, monkeypatch):
    monkeypatch.setattr("app.db.session.SessionLocal", db_session_factory)
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 5)
    with db_session_factory() as session:
        session.add(_scanned(100))
        session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/101").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/102").mock(
        return_value=httpx.Response(404)
    )

    with patch.object(organizer_tasks.scan_single_organizer_task, "delay") as mock_delay:
        organizer_tasks.audit_organizer_scan_task()

    assert mock_delay.call_count == 1


@respx.mock
def test_audit_starts_from_highest_scanned_organizer_id(db_session_factory, monkeypatch):
    """Watermark uses only scanned organizers (onboarded_at IS NOT NULL), not OrganizerActivity."""
    monkeypatch.setattr("app.db.session.SessionLocal", db_session_factory)
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 2)
    with db_session_factory() as session:
        session.add(_activity(200))
        session.add(Organizer(organizer_id=150, onboarded_at=date(2026, 1, 1), detected_at=datetime(2026, 1, 1, tzinfo=timezone.utc)))
        session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/151").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/152").mock(
        return_value=httpx.Response(404)
    )

    with patch.object(organizer_tasks.scan_single_organizer_task, "delay") as mock_delay:
        organizer_tasks.audit_organizer_scan_task()

    mock_delay.assert_called_with(organizer_id=151)


@respx.mock
def test_audit_respects_scan_limit(db_session_factory, monkeypatch):
    monkeypatch.setattr("app.db.session.SessionLocal", db_session_factory)
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 2)
    with db_session_factory() as session:
        session.add(_scanned(100))
        session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/101").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/102").mock(
        return_value=httpx.Response(200)
    )

    with patch.object(organizer_tasks.scan_single_organizer_task, "delay") as mock_delay:
        organizer_tasks.audit_organizer_scan_task()

    assert mock_delay.call_count == 2


@respx.mock
def test_audit_stops_on_unexpected_status_code(db_session_factory, monkeypatch):
    monkeypatch.setattr("app.db.session.SessionLocal", db_session_factory)
    monkeypatch.setattr(organizer_tasks.settings, "organizer_scan_limit", 3)
    with db_session_factory() as session:
        session.add(_scanned(100))
        session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/101").mock(
        return_value=httpx.Response(500)
    )

    with patch.object(organizer_tasks.scan_single_organizer_task, "delay") as mock_delay:
        organizer_tasks.audit_organizer_scan_task()

    assert mock_delay.call_count == 0


@respx.mock
def test_scan_single_organizer_creates_row(db_session_factory, monkeypatch):
    monkeypatch.setattr("app.db.session.SessionLocal", db_session_factory)

    respx.get(f"{settings.limitless_base_url}/organizer/101").mock(
        return_value=httpx.Response(200, text="<html><body>No profile</body></html>")
    )

    result = organizer_tasks.scan_single_organizer_task(organizer_id=101)

    assert result is True
    with db_session_factory() as session:
        org = session.get(Organizer, 101)
        assert org is not None
        assert org.onboarded_at == datetime.now(timezone.utc).date()


@respx.mock
def test_scan_single_organizer_parses_first_tournament_date(db_session_factory, monkeypatch):
    monkeypatch.setattr("app.db.session.SessionLocal", db_session_factory)

    html = (FIXTURE_DIR / "organizer_profile_200.html").read_text()
    respx.get(f"{settings.limitless_base_url}/organizer/101").mock(
        return_value=httpx.Response(200, text=html)
    )

    organizer_tasks.scan_single_organizer_task(organizer_id=101)

    with db_session_factory() as session:
        org = session.get(Organizer, 101)
        assert org is not None
        assert org.onboarded_at == datetime.now(timezone.utc).date()
        assert org.first_tournament_date == date(2026, 6, 10)


@respx.mock
def test_scan_single_organizer_backfills_existing_stub(db_session_factory, monkeypatch):
    """Updating an ingestion-created stub (onboarded_at=None) sets onboarded_at."""
    monkeypatch.setattr("app.db.session.SessionLocal", db_session_factory)
    with db_session_factory() as session:
        session.add(Organizer(organizer_id=100, onboarded_at=None))
        session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/100").mock(
        return_value=httpx.Response(200, text="<html><body>No profile</body></html>")
    )

    organizer_tasks.scan_single_organizer_task(organizer_id=100)

    with db_session_factory() as session:
        org = session.get(Organizer, 100)
        assert org.onboarded_at == datetime.now(timezone.utc).date()


@respx.mock
def test_scan_single_organizer_returns_false_on_non_200(db_session_factory, monkeypatch):
    monkeypatch.setattr("app.db.session.SessionLocal", db_session_factory)

    respx.get(f"{settings.limitless_base_url}/organizer/101").mock(
        return_value=httpx.Response(404)
    )

    result = organizer_tasks.scan_single_organizer_task(organizer_id=101)
    assert result is False
