from pathlib import Path

from app.scraper.organizer_profile import parse_organizer_profile

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "html"


def test_parse_organizer_profile_extracts_name():
    html = (FIXTURE_DIR / "organizer_profile_200.html").read_text()

    result = parse_organizer_profile(html, organizer_id=2720)

    assert result is not None
    assert result.name == "Pudding Weekly"
    assert result.organizer_id == 2720


def test_parse_organizer_profile_extracts_upcoming_tournaments():
    html = (FIXTURE_DIR / "organizer_profile_200.html").read_text()

    result = parse_organizer_profile(html, organizer_id=2720)

    assert result is not None
    assert len(result.upcoming_tournaments) == 2
    t = result.upcoming_tournaments[0]
    assert t.tournament_id == "6a30c6e62d97f3b0c2617d33"
    assert t.name == "Pudding Weekly #1 | A New Beginning!"
    assert t.date == "2026-06-24T01:30:00.000Z"
    assert t.game == "PTCGL"
    assert t.players == 0


def test_parse_organizer_profile_extracts_recent_tournaments():
    html = (FIXTURE_DIR / "organizer_profile_200.html").read_text()

    result = parse_organizer_profile(html, organizer_id=2720)

    assert result is not None
    assert len(result.recent_tournaments) == 2
    t = result.recent_tournaments[0]
    assert t.tournament_id == "5920b5d51c86e2a9b1506c22"
    assert t.name == "Test Tournament Past"
    assert t.date == "2026-06-17T01:30:00.000Z"
    assert t.game == "Pokemon"
    assert t.players == 12


def test_parse_organizer_profile_handles_empty_tournament_tables():
    html = (FIXTURE_DIR / "organizer_profile_empty.html").read_text()

    result = parse_organizer_profile(html, organizer_id=100)

    assert result is not None
    assert result.name == "New Organizer"
    assert result.upcoming_tournaments == []
    assert result.recent_tournaments == []


def test_parse_organizer_profile_returns_none_when_no_name_element():
    html = "<html><body><p>Not a profile page</p></body></html>"

    result = parse_organizer_profile(html, organizer_id=9999)

    assert result is None
