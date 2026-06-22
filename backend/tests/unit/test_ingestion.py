from datetime import datetime, timezone

from app.db.models import OrganizerActivity, Tournament
from app.limitless_client.ingestion import ingest_tournaments
from app.limitless_client.schemas import TournamentDTO


def _dto(id_, organizer_id, game, date, name="Tournament", players=10, fmt="STANDARD"):
    return TournamentDTO(
        id=id_,
        name=name,
        game=game,
        format=fmt,
        date=date,
        players=players,
        organizer_id=organizer_id,
    )


def test_ingest_creates_tournament_rows(db_session):
    dto = _dto("t1", 100, "PTCG", datetime(2026, 6, 1, tzinfo=timezone.utc))

    ingest_tournaments(db_session, [dto])

    tournament = db_session.get(Tournament, "t1")
    assert tournament is not None
    assert tournament.organizer_id == 100
    assert tournament.game == "PTCG"


def test_ingest_sets_first_and_last_seen_for_organizer(db_session):
    dtos = [
        _dto("t1", 100, "PTCG", datetime(2026, 6, 5, tzinfo=timezone.utc)),
        _dto("t2", 100, "PTCG", datetime(2026, 6, 1, tzinfo=timezone.utc)),
        _dto("t3", 100, "PTCG", datetime(2026, 6, 10, tzinfo=timezone.utc)),
    ]

    ingest_tournaments(db_session, dtos)

    activity = db_session.get(OrganizerActivity, (100, "PTCG"))
    assert activity is not None
    assert activity.first_tournament_date == datetime(2026, 6, 1, tzinfo=timezone.utc)
    assert activity.first_tournament_id == "t2"
    assert activity.last_seen_date == datetime(2026, 6, 10, tzinfo=timezone.utc)


def test_ingest_tracks_separate_activity_per_game(db_session):
    dtos = [
        _dto("t1", 100, "PTCG", datetime(2026, 6, 5, tzinfo=timezone.utc)),
        _dto("t2", 100, "VGC", datetime(2026, 5, 1, tzinfo=timezone.utc)),
    ]

    ingest_tournaments(db_session, dtos)

    ptcg = db_session.get(OrganizerActivity, (100, "PTCG"))
    vgc = db_session.get(OrganizerActivity, (100, "VGC"))
    assert ptcg.first_tournament_date == datetime(2026, 6, 5, tzinfo=timezone.utc)
    assert vgc.first_tournament_date == datetime(2026, 5, 1, tzinfo=timezone.utc)


def test_reingesting_earlier_tournament_updates_first_seen(db_session):
    ingest_tournaments(db_session, [_dto("t1", 100, "PTCG", datetime(2026, 6, 5, tzinfo=timezone.utc))])
    activity = db_session.get(OrganizerActivity, (100, "PTCG"))
    assert activity.first_tournament_date == datetime(2026, 6, 5, tzinfo=timezone.utc)

    ingest_tournaments(db_session, [_dto("t0", 100, "PTCG", datetime(2026, 5, 1, tzinfo=timezone.utc))])

    activity = db_session.get(OrganizerActivity, (100, "PTCG"))
    assert activity.first_tournament_date == datetime(2026, 5, 1, tzinfo=timezone.utc)
    assert activity.first_tournament_id == "t0"


def test_reingesting_same_tournament_updates_in_place(db_session):
    ingest_tournaments(db_session, [_dto("t1", 100, "PTCG", datetime(2026, 6, 5, tzinfo=timezone.utc), players=10)])
    ingest_tournaments(db_session, [_dto("t1", 100, "PTCG", datetime(2026, 6, 5, tzinfo=timezone.utc), players=42)])

    count = db_session.query(Tournament).count()
    assert count == 1
    assert db_session.get(Tournament, "t1").players == 42
