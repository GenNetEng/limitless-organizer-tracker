from dataclasses import dataclass, field
from datetime import date, datetime

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


def _extract_tournament_id(row) -> str:
    link = row.select_one("a[href*='/tournament/']")
    if link:
        parts = link["href"].split("/")
        if len(parts) >= 3:
            return parts[2]
    return ""


def _parse_tournament_row(row) -> TournamentEntry:
    return TournamentEntry(
        tournament_id=_extract_tournament_id(row),
        name=row.get("data-name", ""),
        date=row.get("data-date", ""),
        game=row.get("data-platform", ""),
        players=_safe_int(row.get("data-players", "0")),
    )


def parse_organizer_profile(html: str, organizer_id: int) -> OrganizerProfile | None:
    from app.scraper.selectors import (
        PROFILE_COMPLETED_TABLE_SELECTOR,
        PROFILE_NAME_SELECTOR,
        PROFILE_UPCOMING_TABLE_SELECTOR,
    )

    soup = BeautifulSoup(html, "html.parser")
    name_el = soup.select_one(PROFILE_NAME_SELECTOR)
    if name_el is None:
        return None

    upcoming = [_parse_tournament_row(row) for row in soup.select(PROFILE_UPCOMING_TABLE_SELECTOR)]
    recent = [_parse_tournament_row(row) for row in soup.select(PROFILE_COMPLETED_TABLE_SELECTOR)]

    return OrganizerProfile(
        organizer_id=organizer_id,
        name=name_el.get_text(strip=True),
        upcoming_tournaments=upcoming,
        recent_tournaments=recent,
    )


def earliest_tournament_date(profile: OrganizerProfile) -> date | None:
    all_tournaments = profile.recent_tournaments + profile.upcoming_tournaments
    dates = []
    for t in all_tournaments:
        if t.date:
            try:
                dates.append(datetime.fromisoformat(t.date.replace("Z", "+00:00")).date())
            except ValueError:
                continue
    return min(dates) if dates else None
