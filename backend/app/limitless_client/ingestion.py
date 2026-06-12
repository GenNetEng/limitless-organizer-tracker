from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import OrganizerActivity, Tournament
from app.limitless_client.schemas import TournamentDTO


def upsert_tournaments(session: Session, tournaments: list[TournamentDTO]) -> set[tuple[int, str]]:
    """Insert or update tournament rows. Returns the set of (organizer_id, game) pairs touched."""
    now = datetime.now(timezone.utc)
    touched: set[tuple[int, str]] = set()

    for dto in tournaments:
        session.merge(
            Tournament(
                id=dto.id,
                name=dto.name,
                game=dto.game,
                format=dto.format,
                date=dto.date,
                players=dto.players,
                organizer_id=dto.organizer_id,
                ingested_at=now,
            )
        )
        touched.add((dto.organizer_id, dto.game))

    session.flush()
    return touched


def recompute_organizer_activity(session: Session, pairs: set[tuple[int, str]]) -> None:
    """Recompute first/last-seen tournament dates for each (organizer_id, game) pair."""
    now = datetime.now(timezone.utc)

    for organizer_id, game in pairs:
        rows = session.scalars(
            select(Tournament)
            .where(Tournament.organizer_id == organizer_id, Tournament.game == game)
            .order_by(Tournament.date.asc())
        ).all()

        if not rows:
            continue

        first, last = rows[0], rows[-1]
        activity = session.get(OrganizerActivity, (organizer_id, game))
        if activity is None:
            activity = OrganizerActivity(organizer_id=organizer_id, game=game)
            session.add(activity)

        activity.first_tournament_date = first.date
        activity.first_tournament_id = first.id
        activity.last_seen_date = last.date
        activity.updated_at = now

    session.flush()


def ingest_tournaments(session: Session, tournaments: list[TournamentDTO]) -> None:
    """Upsert tournaments and recompute affected organizer activity, then commit."""
    pairs = upsert_tournaments(session, tournaments)
    recompute_organizer_activity(session, pairs)
    session.commit()
