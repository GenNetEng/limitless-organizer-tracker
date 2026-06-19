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
    assert t.players == 1


def test_parse_organizer_profile_extracts_completed_tournaments():
    html = (FIXTURE_DIR / "organizer_profile_200.html").read_text()

    result = parse_organizer_profile(html, organizer_id=2720)

    assert result is not None
    assert len(result.recent_tournaments) == 2
    t = result.recent_tournaments[0]
    assert t.tournament_id == "5920b5d51c86e2a9b1506c22"
    assert t.name == "Test Tournament Past"
    assert t.date == "2026-06-17T01:30:00.000Z"
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


def test_parse_tournament_row_handles_non_numeric_players():
    html = """<html><body>
    <div class="organizer-info"><div><h1 class="name">Test Org</h1></div></div>
    <table class="striped upcoming-tournaments">
      <tr><th>Date</th><th>Name</th></tr>
      <tr data-name="Some Tournament" data-date="2026-06-24T01:30:00.000Z"
          data-platform="PTCGL" data-players="TBD">
        <td><a href="/tournament/abc123/details">Some Tournament</a></td>
      </tr>
    </table>
    </body></html>"""

    result = parse_organizer_profile(html, organizer_id=1)

    assert result is not None
    assert result.upcoming_tournaments[0].players == 0
    assert result.upcoming_tournaments[0].tournament_id == "abc123"
