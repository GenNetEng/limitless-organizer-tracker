from dataclasses import dataclass, field

from bs4 import BeautifulSoup

ORGANIZER_NAME_SELECTOR = ".organizer-info h1.name"
UPCOMING_TABLE_SELECTOR = "table.upcoming-tournaments tbody tr[data-id]"
RECENT_TABLE_SELECTOR = "table.recent-tournaments tbody tr[data-id]"


@dataclass(frozen=True)
class TournamentEntry:
    tournament_id: str
    name: str
    date: str
    game: str
    players: int


@dataclass(frozen=True)
class OrganizerProfile:
    organizer_id: int
    name: str
    upcoming_tournaments: list[TournamentEntry] = field(default_factory=list)
    recent_tournaments: list[TournamentEntry] = field(default_factory=list)


def _parse_tournament_row(row) -> TournamentEntry:
    name_el = row.select_one("td.name")
    game_el = row.select_one("td.game")
    players_el = row.select_one("td.players")
    return TournamentEntry(
        tournament_id=row["data-id"],
        name=name_el.get_text(strip=True) if name_el else "",
        date=row.get("data-date", ""),
        game=game_el.get_text(strip=True) if game_el else "",
        players=int(players_el.get_text(strip=True)) if players_el else 0,
    )


def parse_organizer_profile(html: str, organizer_id: int) -> OrganizerProfile | None:
    soup = BeautifulSoup(html, "html.parser")
    name_el = soup.select_one(ORGANIZER_NAME_SELECTOR)
    if name_el is None:
        return None

    upcoming = [_parse_tournament_row(row) for row in soup.select(UPCOMING_TABLE_SELECTOR)]
    recent = [_parse_tournament_row(row) for row in soup.select(RECENT_TABLE_SELECTOR)]

    return OrganizerProfile(
        organizer_id=organizer_id,
        name=name_el.get_text(strip=True),
        upcoming_tournaments=upcoming,
        recent_tournaments=recent,
    )
