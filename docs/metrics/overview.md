# Metrics Overview

The tracker's second job (besides resubmitting one organizer's application)
is platform-wide: figuring out how fast Limitless onboards new tournament
organizers, so a pending applicant can set realistic expectations. Everything
under **Metrics** documents how that estimate is built from raw tournament
and scan data.

## What's measured

- **Frontier regression** — fits a line to the fastest-observed
  ID → first-tournament-date relationship, and projects when a given
  organizer ID is likely to go active. See
  [Frontier Regression](frontier_regression.md).
- **Organizer activity** — when organizers actually start running
  tournaments, bucketed by week or month and optionally filtered by game.
  See [Organizer Activity](organizer_activity.md).
- **Organizer lifecycle** — what each Organizer row actually represents:
  three different timestamps with different meanings and different
  coverage gaps. See [Organizer Lifecycle](organizer_lifecycle.md).

## Why it's not exact

All of this is inferred from public data, not from anything Limitless
publishes about its own review process:

- There's no way to observe an organizer's *application* date — only when
  they first appear (`detected_at`/`onboarded_at` from the scanner) and when
  they first ran a tournament (`first_tournament_date`).
- Organizer IDs below the scanner's starting watermark were never observed
  going from "doesn't exist" to "exists" — their `onboarded_at` is unknown
  even after backfill (see [Organizer Lifecycle](organizer_lifecycle.md)).
- The regression line is descriptive, not predictive in any strong sense —
  it answers "if the recent trend holds, when might ID *N* go active," not
  "this is when ID *N* will go active."

## Where the numbers come from

- `backend/app/analytics/` — `frontier.py` (frontier + regression
  selection), `regression.py` (OLS fit), `buckets.py` (date bucketing).
- `backend/app/api/routers/organizers.py` — the `/api/organizers/*`
  endpoints the frontend dashboard charts read from.
- `backend/app/tasks/backfill_tasks.py` — one-time tasks (Organizer
  backfill, historical ID scan, regression verification) that close gaps in
  the underlying data.
