from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Organizer, OrganizerActivity, Tournament
from app.limitless_client.schemas import TournamentDTO

TOURNAMENT_DATE_FLOOR = date(2020, 1, 1)


def upsert_tournaments(session: Session, tournaments: list[TournamentDTO]) -> set[tuple[int, str]]:
    """Insert or update tournament rows. Returns the set of (organizer_id, game) pairs touched."""
    now = datetime.now(timezone.utc)
    touched: set[tuple[int, str]] = set()

    for dto in tournaments:
        if dto.date.date() < TOURNAMENT_DATE_FLOOR:
            continue
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


def sync_organizer_first_tournament_dates(session: Session, organizer_ids: set[int]) -> None:
    """Upsert Organizer.first_tournament_date = MIN(OrganizerActivity.first_tournament_date) across games."""
    if not organizer_ids:
        return

    min_dates = dict(session.execute(
        select(
            OrganizerActivity.organizer_id,
            func.min(OrganizerActivity.first_tournament_date),
        )
        .where(OrganizerActivity.organizer_id.in_(organizer_ids))
        .group_by(OrganizerActivity.organizer_id)
    ).all())

    if not min_dates:
        return

    existing = {
        o.organizer_id: o
        for o in session.scalars(
            select(Organizer).where(Organizer.organizer_id.in_(min_dates.keys()))
        ).all()
    }

    for organizer_id, min_dt in min_dates.items():
        organizer = existing.get(organizer_id)
        if organizer is None:
            organizer = Organizer(organizer_id=organizer_id)
            session.add(organizer)
        organizer.first_tournament_date = min_dt.date()

    session.flush()


def ingest_tournaments(session: Session, tournaments: list[TournamentDTO]) -> None:
    """Upsert tournaments, recompute affected organizer activity, sync Organizer dates, then commit."""
    pairs = upsert_tournaments(session, tournaments)
    recompute_organizer_activity(session, pairs)
    sync_organizer_first_tournament_dates(session, {oid for oid, _ in pairs})
    session.commit()
