from datetime import date, datetime, timezone

from app.db.models import Organizer
from app.limitless_client.ingestion import ingest_tournaments
from app.limitless_client.schemas import TournamentDTO


def _dto(id_, organizer_id, game, dt):
    return TournamentDTO(
        id=id_, name="Tournament", game=game, format="STANDARD",
        date=dt, players=10, organizer_id=organizer_id,
    )


def test_ingest_creates_organizer_first_tournament_date(db_session):
    """Ingestion upserts Organizer.first_tournament_date as the MIN across all games."""
    dtos = [
        _dto("t1", 100, "PTCG", datetime(2026, 6, 5, tzinfo=timezone.utc)),
        _dto("t2", 100, "VGC", datetime(2026, 5, 1, tzinfo=timezone.utc)),
    ]

    ingest_tournaments(db_session, dtos)

    organizer = db_session.get(Organizer, 100)
    assert organizer is not None
    assert organizer.first_tournament_date == date(2026, 5, 1)


def test_ingest_updates_existing_organizer_first_tournament_date(db_session):
    """Re-ingesting an earlier tournament updates Organizer.first_tournament_date."""
    ingest_tournaments(db_session, [_dto("t1", 100, "PTCG", datetime(2026, 6, 5, tzinfo=timezone.utc))])
    assert db_session.get(Organizer, 100).first_tournament_date == date(2026, 6, 5)

    ingest_tournaments(db_session, [_dto("t0", 100, "PTCG", datetime(2026, 5, 1, tzinfo=timezone.utc))])

    assert db_session.get(Organizer, 100).first_tournament_date == date(2026, 5, 1)


def test_ingest_does_not_overwrite_onboarded_at(db_session):
    """Ingestion upserts first_tournament_date but leaves scanner-set fields intact."""
    db_session.add(Organizer(
        organizer_id=100,
        onboarded_at=date(2026, 4, 1),
        detected_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
    ))
    db_session.commit()

    ingest_tournaments(db_session, [_dto("t1", 100, "PTCG", datetime(2026, 6, 5, tzinfo=timezone.utc))])

    organizer = db_session.get(Organizer, 100)
    assert organizer.onboarded_at == date(2026, 4, 1)
    assert organizer.first_tournament_date == date(2026, 6, 5)


def test_ingest_creates_organizer_rows_for_multiple_organizers(db_session):
    dtos = [
        _dto("t1", 100, "PTCG", datetime(2026, 6, 1, tzinfo=timezone.utc)),
        _dto("t2", 200, "PTCG", datetime(2026, 6, 5, tzinfo=timezone.utc)),
    ]

    ingest_tournaments(db_session, dtos)

    assert db_session.get(Organizer, 100).first_tournament_date == date(2026, 6, 1)
    assert db_session.get(Organizer, 200).first_tournament_date == date(2026, 6, 5)
