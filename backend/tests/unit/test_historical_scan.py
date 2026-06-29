"""Unit tests for historical_organizer_scan_task (Phase 48, #137)."""

from datetime import date, datetime, timezone
from unittest.mock import patch

import httpx
import respx

import app.tasks.backfill_tasks as backfill_tasks
from app.config import settings
from app.db.models import EventLog, Organizer


def _existing_organizer(organizer_id, onboarded=True):
    kwargs = {
        "organizer_id": organizer_id,
        "detected_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }
    if onboarded:
        kwargs["onboarded_at"] = date(2026, 1, 1)
    return Organizer(**kwargs)


def _mock_scan_delay(monkeypatch):
    """Patch scan_single_organizer_task.delay where backfill_tasks uses it."""
    return patch.object(backfill_tasks.scan_single_organizer_task, "delay")


@respx.mock
def test_dispatches_for_200_responses(db_session_factory, monkeypatch):
    """200 responses dispatch scan_single_organizer_task."""
    monkeypatch.setattr("app.db.session.SessionLocal", db_session_factory)
    monkeypatch.setattr(backfill_tasks.settings, "organizer_scan_start_id", 5)

    for oid in range(1, 6):
        respx.get(f"{settings.limitless_base_url}/organizer/{oid}").mock(
            return_value=httpx.Response(200 if oid != 3 else 404)
        )

    with _mock_scan_delay(monkeypatch) as mock_delay:
        backfill_tasks.historical_organizer_scan_task()

    assert mock_delay.call_count == 4
    for call in mock_delay.call_args_list:
        assert call.kwargs.get("set_onboarded") is False


@respx.mock
def test_does_not_stop_at_404(db_session_factory, monkeypatch):
    """Unlike the frontier scanner, historical scan continues past 404s."""
    monkeypatch.setattr("app.db.session.SessionLocal", db_session_factory)
    monkeypatch.setattr(backfill_tasks.settings, "organizer_scan_start_id", 4)

    status_map = {1: 200, 2: 404, 3: 200, 4: 404}
    for oid, status in status_map.items():
        respx.get(f"{settings.limitless_base_url}/organizer/{oid}").mock(
            return_value=httpx.Response(status)
        )

    with _mock_scan_delay(monkeypatch) as mock_delay:
        backfill_tasks.historical_organizer_scan_task()

    assert mock_delay.call_count == 2
    mock_delay.assert_any_call(organizer_id=1, set_onboarded=False)
    mock_delay.assert_any_call(organizer_id=3, set_onboarded=False)


@respx.mock
def test_continues_past_500(db_session_factory, monkeypatch):
    """Historical scan continues past 500 errors."""
    monkeypatch.setattr("app.db.session.SessionLocal", db_session_factory)
    monkeypatch.setattr(backfill_tasks.settings, "organizer_scan_start_id", 3)

    status_map = {1: 500, 2: 200, 3: 200}
    for oid, status in status_map.items():
        respx.get(f"{settings.limitless_base_url}/organizer/{oid}").mock(
            return_value=httpx.Response(status)
        )

    with _mock_scan_delay(monkeypatch) as mock_delay:
        backfill_tasks.historical_organizer_scan_task()

    assert mock_delay.call_count == 2


@respx.mock
def test_skips_existing_organizer_ids(db_session_factory, monkeypatch):
    """IDs that already have Organizer rows are not probed via HTTP."""
    monkeypatch.setattr("app.db.session.SessionLocal", db_session_factory)
    monkeypatch.setattr(backfill_tasks.settings, "organizer_scan_start_id", 3)

    with db_session_factory() as session:
        session.add(_existing_organizer(2))
        session.commit()

    respx.get(f"{settings.limitless_base_url}/organizer/1").mock(
        return_value=httpx.Response(200)
    )
    # ID 2 should NOT be probed — already exists
    respx.get(f"{settings.limitless_base_url}/organizer/3").mock(
        return_value=httpx.Response(200)
    )

    with _mock_scan_delay(monkeypatch) as mock_delay:
        backfill_tasks.historical_organizer_scan_task()

    assert mock_delay.call_count == 2
    mock_delay.assert_any_call(organizer_id=1, set_onboarded=False)
    mock_delay.assert_any_call(organizer_id=3, set_onboarded=False)


@respx.mock
def test_logs_completion_event(db_session_factory, monkeypatch):
    """Historical scan logs a summary event on completion."""
    monkeypatch.setattr("app.db.session.SessionLocal", db_session_factory)
    monkeypatch.setattr(backfill_tasks.settings, "organizer_scan_start_id", 2)

    respx.get(f"{settings.limitless_base_url}/organizer/1").mock(
        return_value=httpx.Response(200)
    )
    respx.get(f"{settings.limitless_base_url}/organizer/2").mock(
        return_value=httpx.Response(404)
    )

    with _mock_scan_delay(monkeypatch):
        backfill_tasks.historical_organizer_scan_task()

    with db_session_factory() as session:
        events = session.query(EventLog).filter(
            EventLog.event_type == "backfill.historical_scan_complete"
        ).all()
        assert len(events) == 1
        assert "1" in events[0].message


@respx.mock
def test_returns_count_of_dispatched_tasks(db_session_factory, monkeypatch):
    """Returns the number of scan tasks dispatched."""
    monkeypatch.setattr("app.db.session.SessionLocal", db_session_factory)
    monkeypatch.setattr(backfill_tasks.settings, "organizer_scan_start_id", 3)

    status_map = {1: 200, 2: 404, 3: 200}
    for oid, status in status_map.items():
        respx.get(f"{settings.limitless_base_url}/organizer/{oid}").mock(
            return_value=httpx.Response(status)
        )

    with _mock_scan_delay(monkeypatch):
        result = backfill_tasks.historical_organizer_scan_task()

    assert result == 2


@respx.mock
def test_no_ids_to_scan_when_all_exist(db_session_factory, monkeypatch):
    """Returns 0 when all IDs below watermark already have Organizer rows."""
    monkeypatch.setattr("app.db.session.SessionLocal", db_session_factory)
    monkeypatch.setattr(backfill_tasks.settings, "organizer_scan_start_id", 2)

    with db_session_factory() as session:
        session.add(_existing_organizer(1))
        session.add(_existing_organizer(2))
        session.commit()

    with _mock_scan_delay(monkeypatch) as mock_delay:
        result = backfill_tasks.historical_organizer_scan_task()

    assert result == 0
    mock_delay.assert_not_called()
