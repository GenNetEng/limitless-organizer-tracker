# Organizer Lifecycle

`Organizer` (`backend/app/db/models.py`) has three nullable fields that
each answer a different question about when an organizer became "real" to
the tracker. None of them is a stand-in for the others.

```python
class Organizer(Base):
    organizer_id: int          # primary key, matches Limitless's own ID
    onboarded_at: date | None  # scanner-detected "this ID now exists"
    first_tournament_date: date | None  # earliest tournament run, any game
    detected_at: datetime | None        # row first known to the tracker, by any path
```

## The three timestamps

- **`onboarded_at`** — set only by the live frontier scanner
  (`scan_single_organizer_task` with `set_onboarded=True`, the default) the
  first time it probes an ID and gets a `200`. It means "the scanner watched
  this ID transition from not-existing to existing." It is **never**
  backfilled retroactively, because backfill has no way to know the actual
  date an ID went from 404 to 200 in the past — only that it currently
  exists.
- **`first_tournament_date`** — the earliest tournament date across all
  games for that organizer, sourced from `OrganizerActivity` via
  `sync_organizer_first_tournament_dates()`
  (`backend/app/limitless_client/ingestion.py`). Driven entirely by
  tournament data, so it's backfillable: any time tournament history is
  ingested for an organizer_id, this can be computed regardless of when the
  Organizer row itself was created.
- **`detected_at`** — when the tracker's own database first learned this
  organizer_id exists, regardless of path: live scanner detection,
  ingestion-triggered upsert (Phase 46/#138), or one of the backfill tasks
  (Phase 47/#136, Phase 48/#137). It's the closest thing to "row creation
  time" but is meaningful for filtering/sorting (e.g.
  `/api/organizers/recently-onboarded` orders by it) since it's set
  consistently across every code path that creates an Organizer row.

## Why they can disagree

An organizer can have `first_tournament_date` long before `detected_at` if
it was only added to the database recently via backfill from old tournament
history — the tracker just found out about an organizer who has been
active for years. Conversely, `onboarded_at` and `detected_at` can be equal
for organizers the live scanner found in real time, but `onboarded_at` is
always `None` for anything created through a backfill path, since backfill
deliberately passes `set_onboarded=False` (or doesn't go through the
scanner task at all).

## The ID ≥ 2723 threshold

`organizer_scan_start_id` (`backend/app/config.py`, default `2722`) is the
watermark below which the live frontier scanner never operated — it scans
forward from `max(existing onboarded_at organizer_id, organizer_scan_start_id) + 1`.
In practice this means:

- **IDs ≥ 2723**: discovered (or will be discovered) by the live scanner,
  which can set a real `onboarded_at` the moment it detects them.
- **IDs ≤ 2722**: never observed transitioning into existence by the
  scanner. Their `onboarded_at` is unknowable after the fact — these
  organizers can only get `first_tournament_date` (from tournament history)
  and `detected_at` (from whichever backfill path found them), never a
  meaningful `onboarded_at`.

`historical_organizer_scan_task` (Phase 48/#137,
`backend/app/tasks/backfill_tasks.py`) probes IDs `1` through this
watermark for existence, dispatching `scan_single_organizer_task` with
`set_onboarded=False` for every `200` — unlike the live scanner, it does
**not** stop at the first `404`, because historical IDs have real gaps
(some IDs were never assigned, or belong to organizers who never ran a
tournament).

## Backfill coverage

Two backfill tasks close different gaps, and are meant to run in this
order (Phase 47 before Phase 48, to minimize HTTP requests against
Limitless):

1. **`backfill_organizers_from_tournaments_task`** (Phase 47/#136) — finds
   organizer_ids present in `tournaments` but missing an `Organizer` row
   entirely, and creates one via `sync_organizer_first_tournament_dates()`.
   Pure database backfill, no HTTP calls — every organizer it creates
   already ran at least one tournament.
2. **`historical_organizer_scan_task`** (Phase 48/#137) — probes IDs below
   the watermark that *still* have no `Organizer` row after step 1 (i.e.
   IDs that exist on Limitless but have never run a tournament), creating
   rows with `detected_at` set and `onboarded_at` left `None`.

Together they mean every organizer_id that either ran a tournament or
responds `200` on its profile page ends up with an `Organizer` row — but
only IDs ≥ 2723, discovered going forward, will ever have a populated
`onboarded_at`.
