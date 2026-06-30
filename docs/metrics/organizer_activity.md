# Organizer Activity

The activity chart (`OrganizerActivityChart` on the dashboard) answers "how
many organizers ran their first tournament in a given period," overlaid with
"how many organizers did the scanner detect as onboarded in that same
period." Two different signals on one chart, because they answer related
but distinct questions.

## Activity bucketing

`GET /api/organizers/activity` returns one row per `OrganizerActivity`
(per organizer, per game), and `bucket_dates()`
(`backend/app/analytics/buckets.py`) groups `first_tournament_date` values
into either:

- **week** buckets — keyed to the Monday of each ISO week
  (`d - timedelta(days=d.weekday())`)
- **month** buckets — keyed to the 1st of each month

Buckets with zero organizers don't appear in the result. The frontend
(`toActivityChartData` in `frontend/src/lib/activityChartData.ts`) maps each
returned bucket 1:1 to a chart point — it does not synthesize zero-count
periods, so the chart's x-axis only spans periods that had at least one
event (activity or onboarding).

## Game filtering

The `?game=` query parameter restricts the underlying `OrganizerActivity`
rows to a single game before bucketing (e.g. only count an organizer's
first *Pokémon TCG* tournament, ignoring a possibly-earlier first
tournament in another game). `GET /api/games` lists the distinct games
available, populating the dashboard's game dropdown. With no `game`
parameter, each organizer can contribute one count per game it plays — an
organizer active in two games shows up in two buckets, not one.

## Onboarding overlay

`GET /api/organizers/onboarding-history` returns a separate bucketed series
over `Organizer.onboarded_at` (when the scanner first saw `onboarded_at` is
not null) — i.e. detection events from `audit_organizer_scan_task`, not
tournament events. `mergeOnboardingOverlay()`
(`frontend/src/lib/activityChartData.ts`) merges this onto the same period
axis as the activity bars, rendered as a line (`OrganizerActivityChart.tsx`)
so detection and first-tournament trends can be compared on one chart.

Because `onboarded_at` is only ever set going forward by the live scanner
(never backfilled — see [Organizer Lifecycle](organizer_lifecycle.md)), the
onboarding line is flat/empty for any period before the scanner started
running, even though the activity bars for that same period are populated
from tournament history.

## Onboarding delta

`GET /api/organizers/onboarding-delta` (rendered by `OnboardingDelta.tsx`)
computes, for every organizer with both an `onboarded_at` and a
`first_tournament_date` where the tournament date is on or after onboarding,
the gap in days between the two. It returns the average and median of that
distribution plus the sample count. Organizers whose first tournament
predates their recorded `onboarded_at` are excluded from the average/median
— this can happen for an organizer the live scanner already onboarded, if a
later tournament ingestion run discovers an earlier `first_tournament_date`
than was known at onboarding time. Backfilled/historical organizers (see
[Organizer Lifecycle](organizer_lifecycle.md)) never appear in this metric
at all, since they have no `onboarded_at` to begin with.

## Scanner watermark and detection

`audit_organizer_scan_task` (`backend/app/tasks/organizer_tasks.py`) is the
live scanner: it computes a watermark as
`max(MAX(organizer_id WHERE onboarded_at IS NOT NULL), organizer_scan_start_id)`
— the higher of the highest already-onboarded ID and a configured floor (see
[Organizer Lifecycle](organizer_lifecycle.md) for that floor's role) — then
probes IDs above that watermark sequentially via HTTP, stopping at the first
404. Every `200`
dispatches `scan_single_organizer_task`, which sets `onboarded_at = today`
on first detection (`set_onboarded=True` is the default for this path) and
records `detected_at`.

This watermark-and-stop-at-404 approach assumes IDs are dense going
forward, which holds for organizers created after the tracker started
watching — but does **not** hold historically (see
[Organizer Lifecycle](organizer_lifecycle.md) for how gaps below the
watermark are handled instead).
