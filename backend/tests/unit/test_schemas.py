from datetime import datetime, timezone

from app.limitless_client.schemas import TournamentDTO


def test_tournament_dto_parses_organizer_id_alias():
    raw = {
        "game": "PTCG",
        "name": "Torneo Relámpago #50 PTCG Live",
        "date": "2026-06-12T02:00:00.000Z",
        "format": "STANDARD",
        "id": "6a0b39da13f957d6d4b4acba",
        "players": 32,
        "organizerId": 2512,
    }

    dto = TournamentDTO.model_validate(raw)

    assert dto.id == "6a0b39da13f957d6d4b4acba"
    assert dto.organizer_id == 2512
    assert dto.game == "PTCG"
    assert dto.players == 32
    assert dto.date == datetime(2026, 6, 12, 2, 0, tzinfo=timezone.utc)


def test_tournament_dto_allows_null_format():
    raw = {
        "game": "POCKET",
        "name": "Storm x Knowtice Pop Up Blitz-$5",
        "date": "2026-06-12T00:15:00.000Z",
        "format": None,
        "id": "6a2b202c2d97f3b0c26142e6",
        "players": 86,
        "organizerId": 2461,
    }

    dto = TournamentDTO.model_validate(raw)

    assert dto.format is None
