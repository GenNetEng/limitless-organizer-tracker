"""Unit tests for backfill_organizers_from_tournaments (Phase 47, #136)."""

from datetime import datetime, timezone

from app.db.models import EventLog, Organizer, OrganizerActivity, Tournament
from app.tasks.backfill_tasks import run_backfill_organizers


def _add_tournament(session, id_, organizer_id, game="PTCG", dt=None):
    if dt is None:
        dt = datetime(2026, 6, 1, tzinfo=timezone.utc)
    session.add(Tournament(
        id=id_, name="T", game=game, format="STANDARD",
        date=dt, players=10, organizer_id=organizer_id,
        ingested_at=datetime.now(timezone.utc),
    ))
    session.flush()


def _add_activity(session, organizer_id, game="PTCG", first_dt=None):
    if first_dt is None:
        first_dt = datetime(2026, 6, 1, tzinfo=timezone.utc)
    session.add(OrganizerActivity(
        organizer_id=organizer_id, game=game,
        first_tournament_date=first_dt, first_tournament_id="t-dummy",
        last_seen_date=first_dt, updated_at=datetime.now(timezone.utc),
    ))
    session.flush()


def test_creates_organizer_rows_for_orphan_ids(db_session):
    """Orphan organizer_ids (in tournaments, not in organizers) get Organizer rows."""
    _add_tournament(db_session, "t1", 100)
    _add_tournament(db_session, "t2", 200)
    _add_activity(db_session, 100)
    _add_activity(db_session, 200)
    db_session.commit()

    count = run_backfill_organizers(db_session)

    assert count == 2
    assert db_session.get(Organizer, 100) is not None
    assert db_session.get(Organizer, 200) is not None


def test_skips_organizer_ids_that_already_have_rows(db_session):
    """Organizer IDs that already have Organizer rows are not counted as backfilled."""
    db_session.add(Organizer(
        organizer_id=100,
        detected_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    ))
    _add_tournament(db_session, "t1", 100)
    _add_tournament(db_session, "t2", 200)
    _add_activity(db_session, 100)
    _add_activity(db_session, 200)
    db_session.commit()

    count = run_backfill_organizers(db_session)

    assert count == 1
    assert db_session.get(Organizer, 200) is not None


def test_sets_detected_at_on_new_organizer_rows(db_session):
    """Backfilled Organizer rows must have detected_at set."""
    _add_tournament(db_session, "t1", 100)
    _add_activity(db_session, 100)
    db_session.commit()

    run_backfill_organizers(db_session)

    organizer = db_session.get(Organizer, 100)
    assert organizer.detected_at is not None


def test_sets_first_tournament_date(db_session):
    """Backfilled Organizer rows get first_tournament_date from OrganizerActivity."""
    _add_tournament(db_session, "t1", 100, dt=datetime(2026, 3, 15, tzinfo=timezone.utc))
    _add_activity(db_session, 100, first_dt=datetime(2026, 3, 15, tzinfo=timezone.utc))
    db_session.commit()

    run_backfill_organizers(db_session)

    organizer = db_session.get(Organizer, 100)
    assert organizer.first_tournament_date is not None


def test_returns_zero_when_no_orphans(db_session):
    """Returns 0 when all tournament organizer_ids already have Organizer rows."""
    db_session.add(Organizer(
        organizer_id=100,
        detected_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    ))
    _add_tournament(db_session, "t1", 100)
    _add_activity(db_session, 100)
    db_session.commit()

    count = run_backfill_organizers(db_session)

    assert count == 0


def test_returns_zero_when_no_tournaments(db_session):
    """Returns 0 when the tournaments table is empty."""
    count = run_backfill_organizers(db_session)

    assert count == 0


def test_logs_event(db_session):
    """Backfill logs an event with the count of created Organizer rows."""
    _add_tournament(db_session, "t1", 100)
    _add_activity(db_session, 100)
    db_session.commit()

    run_backfill_organizers(db_session)

    events = db_session.query(EventLog).filter(
        EventLog.event_type == "backfill.organizers_from_tournaments"
    ).all()
    assert len(events) == 1
    assert "1" in events[0].message


def test_does_not_overwrite_existing_organizer_fields(db_session):
    """Existing Organizer rows are untouched — onboarded_at and detected_at preserved."""
    from datetime import date
    db_session.add(Organizer(
        organizer_id=100,
        onboarded_at=date(2026, 4, 1),
        detected_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
    ))
    _add_tournament(db_session, "t1", 100)
    _add_tournament(db_session, "t2", 200)
    _add_activity(db_session, 100)
    _add_activity(db_session, 200)
    db_session.commit()

    run_backfill_organizers(db_session)

    org100 = db_session.get(Organizer, 100)
    assert org100.onboarded_at == date(2026, 4, 1)
    assert org100.detected_at == datetime(2026, 4, 1, tzinfo=timezone.utc)
