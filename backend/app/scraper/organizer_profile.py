from dataclasses import dataclass, field

from bs4 import BeautifulSoup


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


def _safe_int(text: str) -> int:
    try:
        return int(text)
    except (ValueError, TypeError):
        return 0


def _parse_tournament_row(row) -> TournamentEntry:
    from app.scraper.selectors import (
        PROFILE_TOURNAMENT_GAME_SELECTOR,
        PROFILE_TOURNAMENT_NAME_SELECTOR,
        PROFILE_TOURNAMENT_PLAYERS_SELECTOR,
    )

    name_el = row.select_one(PROFILE_TOURNAMENT_NAME_SELECTOR)
    game_el = row.select_one(PROFILE_TOURNAMENT_GAME_SELECTOR)
    players_el = row.select_one(PROFILE_TOURNAMENT_PLAYERS_SELECTOR)
    return TournamentEntry(
        tournament_id=row["data-id"],
        name=name_el.get_text(strip=True) if name_el else "",
        date=row.get("data-date", ""),
        game=game_el.get_text(strip=True) if game_el else "",
        players=_safe_int(players_el.get_text(strip=True)) if players_el else 0,
    )


def parse_organizer_profile(html: str, organizer_id: int) -> OrganizerProfile | None:
    from app.scraper.selectors import (
        PROFILE_NAME_SELECTOR,
        PROFILE_RECENT_TABLE_SELECTOR,
        PROFILE_UPCOMING_TABLE_SELECTOR,
    )

    soup = BeautifulSoup(html, "html.parser")
    name_el = soup.select_one(PROFILE_NAME_SELECTOR)
    if name_el is None:
        return None

    upcoming = [_parse_tournament_row(row) for row in soup.select(PROFILE_UPCOMING_TABLE_SELECTOR)]
    recent = [_parse_tournament_row(row) for row in soup.select(PROFILE_RECENT_TABLE_SELECTOR)]

    return OrganizerProfile(
        organizer_id=organizer_id,
        name=name_el.get_text(strip=True),
        upcoming_tournaments=upcoming,
        recent_tournaments=recent,
    )
