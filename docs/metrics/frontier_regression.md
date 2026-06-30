# Frontier Regression

Powers the "wait estimate" feature (`GET /api/organizers/wait-estimate`,
rendered by the `WaitTimeEstimator` frontend component): given an organizer
ID, project roughly when that ID is likely to have its first tournament.

## The data

Each (organizer_id, game) pair in `OrganizerActivity` has a
`first_tournament_date` — the date of the earliest tournament that
organizer ran in that game. `build_frontier_regression()`
(`backend/app/analytics/frontier.py`) collapses this to one point per
organizer:

```python
(organizer_id, MIN(first_tournament_date) across all games)
```

It only looks at the **1,000 organizers with the highest IDs**
(`TOP_N_ORGANIZERS`) — recent onboarding behavior is what matters for
projecting forward, and including the entire history would let stale,
slower-onboarding eras drag the trend line around.

## Pareto frontier

Raw (id, date) points are noisy — a higher ID can easily have an *earlier*
first-tournament date than a lower one (e.g. it ran a tournament sooner
after onboarding). `compute_frontier()` reduces the point set to its
lower envelope: a point survives only if no organizer with an equal-or-higher
ID reached its first tournament strictly earlier.

The result is monotonic — as organizer ID increases, frontier date never
goes backward — and represents the **fastest observed onboarding-to-first-
tournament lag** for each part of the ID range. The regression line is fit
to this frontier subset (falling back to the raw points if fewer than 2
frontier points exist), not the raw scatter, so a few unusually slow
organizers don't pull the projection earlier than it should be.

## OLS regression

`fit_linear_regression()` (`backend/app/analytics/regression.py`) fits an
ordinary-least-squares line `y = slope·x + intercept` over
`(organizer_id, date_ordinal)` pairs, using `date.toordinal()` so dates can
be treated as plain numbers.

**Slope** is days-per-ID — how many additional days of wait each
additional organizer ID currently represents. A smaller slope means
Limitless is onboarding organizers faster (each successive ID takes less
extra time to go active).

**R²** (coefficient of determination) measures how well the line fits the
frontier points, from 0 (no fit) to 1 (perfect fit). Because the frontier
is monotonic by construction, R² tends to be high even with a handful of
points — a high R² here reflects how monotonic the *frontier* is, not how
predictable any individual organizer's onboarding will be.

## Projected dates

`_predict_date()` (`backend/app/api/routers/organizers.py`) plugs an
organizer ID into the fitted line and converts the resulting ordinal back to
a calendar date, clamping to `date.min`/`date.max` to avoid overflow for
IDs far outside the observed range. The `/wait-estimate` endpoint returns
this as `projected_active_date` for a single queried ID, plus a two-point
`fitted_line` (endpoints at the min and max organizer ID across the data and
the query) so the frontend can draw the regression line on the chart
alongside the raw and frontier points.

## Data limitations

- **Small N near the edges**: the most recent organizer IDs have the least
  data — a new ID can dominate the frontier and swing the line before
  enough history accumulates around it.
- **Game mixing**: `MIN(first_tournament_date)` is taken across all games
  per organizer, so an organizer who is fast in one game but slow to add a
  second doesn't get penalized — but it also means the regression doesn't
  distinguish "fast at TCG, slow at everything else" patterns.
- **No application-date ground truth**: the regression projects *first
  tournament*, not *application approval* — see
  [Organizer Lifecycle](organizer_lifecycle.md) for why those aren't the
  same event.
- **Backfilled organizers can shift history**: Phase 47–49 backfilled
  Organizer/OrganizerActivity rows that previously didn't exist at all,
  which changes the `TOP_N_ORGANIZERS` window and can move the slope/R²
  compared to pre-backfill snapshots. `verify_frontier_regression_task`
  (`backend/app/tasks/backfill_tasks.py`) exists specifically to re-run and
  log these metrics after such backfills, for comparison.
