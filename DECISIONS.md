# Technical Decisions

A log of non-trivial technical decisions for this project: new dependencies,
choices between libraries/patterns, file/module structure, API/auth design,
repo/CI configuration, etc. Every entry was presented to the owner with
alternatives before implementation, per [`CONTRIBUTING.md`](CONTRIBUTING.md).

Newest entries first.

## 2026-06-22: Event log — centralized EventLog table with partitioning (Phase 21a)

**Decision**: Create a single **`event_log`** table as the centralized audit/event log for all application operations. All significant functions log events here — task lifecycle (via Celery signals), scraper operations, data ingestion, notifications, and API triggers. The table uses a JSON `metadata` column for flexible structured data per event type.

**Schema**: `id PK, timestamp UTCDateTime (indexed), event_type VARCHAR (indexed), severity VARCHAR, source VARCHAR, message TEXT, metadata JSON, correlation_id VARCHAR (nullable)`.

**Partitioning**: PostgreSQL native range partitioning on `timestamp` (monthly partitions) for log rotation. Tests use SQLite (no partitioning support), so the migration conditionally applies partitioning only on PostgreSQL.

**Alternatives considered**:

- Separate `TaskExecution` table for Celery + general `EventLog` — two tables to query/maintain for admin views; task events are just one category of event
- Celery result backend (Redis) for task history — results expire in 24h, no start time/duration, hard to query by task name
- Application-level log files instead of DB — not queryable from the admin API, no structured metadata, harder to correlate with business data

**Why**: Owner requested a centralized event log following industry best practices, with all functions instrumented. A single table with typed events + JSON metadata covers both structured task tracking (for diagnostics) and general audit logging (for the admin event log view). Partitioning ensures log rotation without manual cleanup.

---

## 2026-06-22: Celery task event capture via signals (Phase 21a)

**Decision**: Wire `task_prerun`, `task_postrun`, and `task_failure` **Celery signals** in `celery_app.py` to automatically log task lifecycle events to the `event_log` table. No changes to individual task modules needed for task-level events.

**Alternatives considered**: Decorator/wrapper on each `@celery_app.task` — more explicit but requires touching all 4 task files and maintaining the wrapper for new tasks.

**Why**: Signals are the idiomatic Celery mechanism; they fire automatically for all registered tasks without per-task boilerplate.

---

## 2026-06-22: Admin API design — single diagnostics endpoint, config allowlist (Phase 21a)

**Decision**: Four admin endpoints under `/api/admin/`:

1. `GET /api/admin/event-log` — paginated, filterable event log query
2. `GET /api/admin/diagnostics` — single endpoint returning DB/Redis/worker/beat status + last success per task
3. `GET /api/admin/config` — hardcoded allowlist of non-sensitive settings fields
4. `GET /api/admin/tasks` — static list of available task trigger endpoints

**Config allowlist fields**: `application_status_check_interval_hours`, `resubmit_times_utc`, `tournament_ingest_interval_hours`, `tournament_ingest_limit`, `tournament_backfill_months`, `organizer_scan_interval_hours`, `organizer_scan_limit`.

**Alternatives considered**: Separate endpoints per health check (more granular, more frontend complexity); `Settings.model_dump(exclude=...)` for config (risky if new sensitive fields added later).

**Why**: Owner approved all recommended approaches. Single diagnostics endpoint keeps the admin panel simple (one fetch, one loading state). Hardcoded config allowlist is safer than an exclusion list.

---

## 2026-06-18: Organizer onboarding scraper — httpx + BeautifulSoup 4, no auth (Phase 18)

**Decision**: Use plain **httpx** (no Playwright) + **BeautifulSoup 4** (`beautifulsoup4`) to fetch and parse `play.limitlesstcg.com/organizer/{id}` pages for the `scan_new_organizers_task` and the `GET /api/organizers/{id}/scrape` endpoint.

**Rationale**: The organizer profile page is publicly accessible (HTTP 200 without credentials, confirmed via `curl -v` against `/organizer/2720`). Content is server-rendered HTML — organizer name and tournament data are present in the initial response without executing JavaScript. Playwright is only needed for auth-gated pages. `httpx` is already a project dependency; `beautifulsoup4` is the standard Python HTML-parsing library.

**Alternatives considered**:
- Playwright (already in deps) — no benefit for public pages; adds browser-launch overhead on every scan tick and every API call
- stdlib `html.parser` directly — no new dependency, but more verbose and error-prone for navigating nested HTML than BS4

**Scanner task note**: The `scan_new_organizers_task` itself only needs the HTTP status code (200 vs 404) and does not parse HTML — BS4 is used only by the scrape endpoint and its fixture-based tests.

## 2026-06-18: Organizer table design — separate `Organizer` table, not `OrganizerActivity` amendment (Phase 18)

**Decision**: Create a new **`Organizer`** table (`organizer_id PK, onboarded_at DATE NULL, first_tournament_date DATE NULL, detected_at TIMESTAMP`) rather than adding `onboarded_at` as a column to the existing `OrganizerActivity` table.

**Rationale**: `OrganizerActivity` has a `(organizer_id, game)` composite primary key — it is per-organizer-per-game. `onboarded_at` is a per-organizer signal (the organizer profile page is not game-specific). Placing it in `OrganizerActivity` would require a game to be chosen or the row to be duplicated per game, both of which are wrong. A separate `Organizer` table keeps the onboarding signal at the correct grain and pairs naturally with the `first_tournament_date` (MIN across games) for delta analytics.

**`first_tournament_date` maintenance**: The tournament ingestion task (`ingest_tournaments_task`) will upsert `Organizer.first_tournament_date = MIN(OrganizerActivity.first_tournament_date)` for each organizer after each ingest run, keeping the delta fresh without a JOIN at query time.

**Alternatives considered**:
- Adding `onboarded_at` to `OrganizerActivity` — wrong grain (per-game vs per-organizer)
- Computing `first_tournament_date` via JOIN at query time rather than materializing — cleaner but slower; the delta query benefits from having both columns in a single row

## 2026-06-18: Kubernetes database: Percona Distribution for PostgreSQL (Phase 17)

**Decision**: Use **Percona Distribution for PostgreSQL** (via the Percona Operator for PostgreSQL, `percona/pg-operator` Helm chart) instead of the Bitnami PostgreSQL subchart for the k3s deployment.

**Rationale**: Owner specified Percona Postgres as the target. Percona Distribution for PostgreSQL adds enterprise-grade features over vanilla PostgreSQL: enhanced monitoring (pg_stat_monitor), PITR backups, and HA support — relevant for a long-running local cluster. The Percona Operator manages the lifecycle via CRDs, which is the idiomatic Kubernetes approach.

**Alternatives considered**:
- `bitnami/postgresql` subchart — simpler, no operator overhead, but plain PostgreSQL with no enhanced monitoring or backup primitives
- Vanilla `postgres:16-alpine` (current docker-compose image) — not suitable for production k8s

**Note**: docker-compose development environment continues to use `postgres:16-alpine` (unchanged). The Percona Operator is k8s-only.

---

## 2026-06-18: Wait-estimate redesign: global top-1000 Pareto-frontier regression (Phase 12.5, FR12/FR13)

**Decision**: Redesign `GET /api/organizers/wait-estimate` around two owner-approved choices:

1. **Global top-1000, no game filter**: query the 1000 highest `organizer_id`s across all
   games, one point per organizer using `MIN(first_tournament_date)` across their games.
   `organizer_id` is a global account-creation-ordered ID — per-game filtering obscures the
   global onboarding-rate signal. (Alternative considered: per-game filter as before.)

2. **Pareto-frontier regression instead of plain OLS over all points**: `first_tournament_date`
   is *not* the onboarding/approval date — it's "sometime after" with a variable scheduling
   lag per organizer. For a cohort of organizers onboarded around the same time (similar ID
   range), the ones with the shortest lag (earliest `first_tournament_date`) are the best
   proxy for the true onboarding date — "highest IDs with earliest dates" (owner's framing).
   The frontier = points not dominated by any other point with a higher-or-equal ID and
   earlier-or-equal date; fitting OLS on the frontier removes high-lag noise from the slope
   estimate. (Alternative considered: plain OLS over top-1000 without frontier filtering —
   rejected because variable lag biases the slope upward.)

Frontend: chart renders on load (no form submission required); two `Scatter` series (general
population in light blue, frontier organizers in red) plus the fitted trend line.

## 2026-06-15: Organizer-activity chart + wait-time estimator (Phase 12)

**Decision**: Three design points for the new frontend dashboard sections
(FR11, FR13):

1. **Scatter data for FR13**: extend `GET /api/organizers/wait-estimate`
   (rather than adding a new endpoint) with an `intercept` field and a
   `points` array of `{organizer_id, first_tournament_date}` for every
   `OrganizerActivity` row used to fit the regression. The frontend derives
   both the scatter plot and the fitted line from this single response.
2. **Chart type for FR11**: render both a bar and a line over the same
   weekly activity counts in a single Recharts `ComposedChart`
   (`OrganizerActivityChart`), rather than choosing one chart type. Chart
   data shaping is done by a pure, unit-tested transform
   (`src/lib/activityChartData.ts`) rather than hardcoded inline.
3. **Interval toggle**: the activity chart shows week buckets only for this
   phase; no week/month toggle in the UI (the backend still supports
   `interval=month` for future use).

**Alternatives considered**: a separate `/api/organizers/wait-estimate/points`
endpoint (avoids growing the existing response, but means two requests and
two loading states for one chart); a single bar-only or line-only chart for
FR11 (simpler, but loses one of the two "stories" the owner wanted to see);
a week/month toggle now (more flexible, deferred since the owner asked for
week-only in this phase).

**Why**: Owner sign-off via AskUserQuestion — one response shape keeps the
wait-time estimator's fetch/loading logic simple, a combined bar+line chart
shows both the per-period counts and the trend without two separate charts,
and the reusable transform utility (`toActivityChartData`) keeps the chart
component free of date-formatting/shaping logic.

## 2026-06-15: Organizer-activity API design (Phase 11)

**Decision**: Three design points for the new `app/api/routers/organizers.py`
endpoints (FR8, FR12):

1. **Regression implementation**: `app/analytics/regression.py` implements
   ordinary least squares by hand (sums of x, y, xy, x², y²) using only the
   stdlib, returning slope/intercept/r_squared. No numpy/scipy/scikit-learn
   dependency added.
2. **Activity bucket format**: `GET /api/organizers/activity` returns
   `{"period": "YYYY-MM-DD", "count": N}` items, where `period` is the
   bucket *start* date — Monday for `interval=week` (ISO week), the 1st of
   the month for `interval=month`.
3. **Wait-estimate insufficient-data handling**: `GET
   /api/organizers/wait-estimate?organizer_id=&game=` returns `404 Not
   Found` if the given `game` has fewer than 2 `OrganizerActivity` rows
   (can't fit a regression).

**Alternatives considered**: numpy/`polyfit` for the regression (more
standard, but a new dependency for one small calculation on a tiny per-game
dataset); ISO week/month labels (`"2026-W24"`/`"2026-06"`) for activity
buckets (more compact, but needs extra frontend parsing to plot on a date
axis for Phase 12's chart); `200` with null fields + `sample_size` for the
insufficient-data wait-estimate case (lets the frontend always parse the
same shape, but `404` is simpler for `response.ok` checks).

**Why**: Owner sign-off via AskUserQuestion — keep the backend dependency
surface minimal (dataset per game is small, one row per organizer), make
activity buckets directly usable as a chart x-axis without frontend
date-math, and keep the wait-estimate error case a simple HTTP-status check.

## 2026-06-14: Tournament-ingestion backfill strategy (Phase 10)

**Decision**: `ingest_tournaments_task` pages through
`GET /api/tournaments?limit=<tournament_ingest_limit>&page=N` starting at
`page=1`, ingesting each page via the existing `ingest_tournaments()`, and
stops when either a page is empty or the oldest tournament on the page is
older than `TOURNAMENT_BACKFILL_MONTHS` (default 3) ago. This runs on every
scheduled tick (`tournament_ingest_interval_hours`).

**Alternatives considered**: a separate one-time `backfill_tournaments_task`
run manually once after deploy, with the regular task only fetching page 1
(less ongoing API load, but an easy-to-forget manual step and not purely
beat-scheduled per NFR3); a "catch-up" variant that stops early once a page's
tournaments are all already in the DB, with a first-run cap at
`TOURNAMENT_BACKFILL_MONTHS` (more efficient after the first run, but more
complex stop logic and doesn't re-check old data for retroactive edits).

**Why**: Confirmed live against `play.limitlesstcg.com/api/tournaments` —
`?page=N` paginates (ordered newest-first), `?offset=` is ignored, and
`limit=2000` covers ~2 months. So a 3-month window is ~2-3 requests of
~1-3k upserts per hourly run, which the owner judged an acceptable cost for
a simple, idempotent, self-healing (re-checks the whole window for retroactive
edits) single task with no extra scheduling/state.

## Template

```
## YYYY-MM-DD: <short title>

**Decision**: <what was chosen>

**Alternatives considered**: <other options and their tradeoffs>

**Why**: <reasoning / owner's stated rationale>
```

---

## 2026-06-14: FR3 live selector fix for the resubmit flow

**Decision**: Point FR3's resubmit at `/user/application/<LIMITLESS_APPLICATION_ID>`
(the same page as FR2) instead of `/account/settings/orgs`. A live,
read-only investigation (no click on the actual "Resubmit" button) showed
the page renders all three steps of the resubmit wizard in one DOM: a
`.page1` form, a `.page2` confirmation step, and a `.page3` success message,
with `.page2`/`.page3` hidden via inline `display: none` until revealed.
`resubmit_application()` now clicks `.page1 button.continue` (a verified
pure client-side reveal of `.page2`, no network request) and then
`.page2 button.submit` (the actual resubmit, not exercised live).
`parse_resubmit_result()` now checks whether `.page3` has been revealed with
its `success` class intact. The failure-path structure (an error in
`.response`) is best-guess, following the same `UNKNOWN`-fallback philosophy
as FR2's unverified non-pending statuses — `application_resubmit_failure.html`
reflects this best guess.

**Alternatives considered**: Leave the failure-path detection unimplemented
pending a live failure case — rejected because `parse_resubmit_result`
already defaults to `False` for any state other than a fully-revealed
`.page3.success`, so no real failure can be misread as a success.

**Why**: Deferred from PR #26 (FR2 live fix), which scoped out FR3 because
clicking "Resubmit" has a real side effect. The org-settings-based selectors
(`ORG_SETTINGS_PATH`, `.resubmit-result`, `button.resubmit`/`a.resubmit`)
were placeholders from before any live verification and pointed at a page
that returns no content for this account — same root cause as the FR2 bug.

---

## 2026-06-13: FR2 live URL/selector fix + LIMITLESS_APPLICATION_ID config

**Decision**: Point FR2's status check at the organizer's own application
page, `/user/application/<LIMITLESS_APPLICATION_ID>`, and read the status
from `.organizer-application .status .code` (verified live for the
"pending" state). Add a new required-in-practice config var,
`LIMITLESS_APPLICATION_ID`, sourced from the application page URL or the
Discord resubmission message's link. Best-guess fixtures for
approved/rejected/expired follow the same verified structure but their
wording is unverified; `parse_status_html`'s existing `UNKNOWN` +
preserved-`raw_text` fallback is the safety net if the real wording differs.

**Alternatives considered**: Click through from `/account/settings/orgs` to
discover the application URL/ID at runtime instead of configuring it —
avoids a new env var, but adds a scrape step and another selector to keep in
sync, for a value (the application ID) that doesn't change once an account
has applied.

**Why**: The first live run of `POST /api/status-check` (after the Phase 9/
PR #25 Playwright fix) returned 200 but `status: "unknown"` with empty
`raw_text` — `/account/settings/orgs` returns no content for this account,
and `.application-status` doesn't exist on the real page. Investigating the
Discord-linked application URL (`/user/application/<id>`) with the
already-persisted session showed the real `.organizer-application .status
.code` structure. Scope was limited to FR2 (status check); FR3 (resubmit,
which lives on the same page behind a "Continue" step) is deferred to a
follow-up to avoid triggering a real resubmission while verifying.

---

## 2026-06-13: Playwright/browser image version pin

**Decision**: Bump `backend/Dockerfile`'s base image to
`mcr.microsoft.com/playwright/python:v1.60.0-noble` and pin
`playwright==1.60.0` in `backend/pyproject.toml` (previously `>=1.45`), so
the installed `playwright` package version always matches the browsers
bundled in the image.

**Alternatives considered**: pin `playwright==1.48.0` to match the
then-current `v1.48.0-noble` base image instead — smaller diff, no new
~2GB image pull, but keeps the stack on an older Playwright.

**Why**: First live run of `POST /api/status-check` (FR14) returned 500 —
`playwright>=1.45` had resolved to `1.60.0` at image build time, but the
`v1.48.0-noble` base image only bundles `1.48.0`'s browsers, so
`BrowserType.launch()` couldn't find the browser executable. Owner chose to
move forward to `v1.60.0-noble`/`1.60.0` rather than pin back to `1.48.0`.
Pinning (rather than leaving an open `>=` floor) keeps the pip-resolved
version and the image's bundled browsers from drifting apart again on a
future rebuild.

---

## 2026-06-13: On-demand status-check API trigger (FR14), no auth

**Decision**: Add `POST /api/status-check` (FR14), which runs the FR2
application-status check synchronously and returns the recorded
`StatusCheckOut`. `app/tasks/status_tasks.py` exposes
`run_application_status_check(session)`, shared by the Celery task
(`check_application_status_task`) and this endpoint. No authentication is
added to this or any other endpoint.

**Alternatives considered**: also adding `POST /api/resubmit` to trigger
FR3 on demand — deferred, since a resubmission has real side effects (counts
as an actual submission to Limitless and posts a Discord notice) and isn't
needed for the immediate goal; shared-secret API-key auth for the new
endpoint — deferred since the existing API has no auth at all and this is
still local/single-user.

**Why**: Owner wants to verify the scraper selectors / current status
on demand (e.g. right after deploying) without waiting for the next
`application_status_check_interval_hours` tick, and confirmed no auth is
needed yet given current (local, single-user) deployment.

---

## 2026-06-13: Discord notification target — user's own server, not the organizer Discord (FR4/BR2 clarification)

**Decision**: `DISCORD_WEBHOOK_URL` (FR4) points to a webhook on the user's
own Discord server, not the Limitless organizer Discord. The tracker posts a
notification describing each resubmission/status-change event there; the
user manually copies/pastes it into the organizer Discord, preserving the
existing manual habit (BR2).

**Alternatives considered**: posting directly to the organizer Discord via
webhook — rejected, since a webhook/bot post is tagged "APP" and visibly
distinct from a normal user message; a "self-bot" using the user's actual
account credentials to post indistinguishably from a manual post — rejected,
violates Discord's Terms of Service (account automation) and would post
automated content into a channel/server the user doesn't control without the
moderators' knowledge.

**Why**: Owner doesn't control the organizer Discord and wants the automated
post there to remain genuinely manual (and honestly attributed to them as a
human action), while still getting an automated reminder/notification with
ready-to-paste text. No code changes required — `app/notifications/discord.py`
already just posts `{"content": message}` to whatever webhook URL is
configured; this is a configuration/documentation clarification of FR4/BR2's
intended deployment.

---

## 2026-06-13: Versioning scheme — minor bump per MVP (MVP1 = v0.1.0)

**Decision**: Tag the MVP1 acceptance checkpoint (Phase 9) as `v0.1.0`.
Going forward, each completed MVP milestone bumps the minor version
(`0.1.0` → `0.2.0` for MVP2, `0.3.0` for MVP3, ...), with the corresponding
`[Unreleased]` section in `CHANGELOG.md` cut over to a dated release section.
A `1.0.0` major release will be determined later once the project reaches a
stable, fully-traced state (per `docs/requirements.md`).

**Alternatives considered**: none — owner specified this scheme directly.

**Why**: Owner's choice, to give each MVP milestone a citable release
version without committing to a 1.0.0 definition yet.

---

## 2026-06-13: Auto-apply DB migrations on container startup (Phase 9)

**Decision**: Add `backend/entrypoint.sh`, which runs `alembic upgrade head`
then `exec "$@"`. `backend/Dockerfile` sets it as `ENTRYPOINT`; the `backend`
service's existing `command:` (uvicorn) becomes the entrypoint's arguments,
so it applies migrations before starting.

**Amendment (same day, found during verification)**: running the same
entrypoint concurrently in `celery-worker` and `celery-beat` against a fresh
DB caused all three containers to race on `alembic upgrade head` —
`CREATE TABLE alembic_version` collided (`duplicate key value violates unique
constraint "pg_type_typname_nsp_index"`), crashing two of the three
containers. `celery-worker`/`celery-beat` now set `entrypoint: []` in
`docker-compose.yml` to skip migrations — only `backend` (the service
serving DB-backed endpoints immediately on startup) applies them; Celery
itself doesn't touch the DB until a scheduled task runs, by which point
`backend` has already migrated.

**Alternatives considered**: a one-off `migrate` service in
`docker-compose.yml` with `depends_on: condition: service_completed_successfully`
on the other services (migrations run exactly once, but adds a new service
and `depends_on` edges to maintain); documenting `docker compose exec backend
alembic upgrade head` as a required first-time manual step (no code change,
but every fresh environment hits a 500 on `/api/status-history` etc. until a
contributor finds the doc).

**Why**: Discovered during Phase 9 docker-compose verification — a fresh
`docker compose up` left the DB schema-less and `/api/status-history`
returned 500 until migrations were applied manually. Owner preferred the
entrypoint script: one small file, self-contained in the backend image,
idempotent (alembic no-ops at head), and applies automatically for
`backend`/`celery-worker`/`celery-beat` without new compose services or
dependency wiring.

---

## 2026-06-13: Frontend styling approach (Phase 8)

**Decision**: Use Tailwind CSS for styling the MVP1 dashboard
(`StatusTimeline`, `ResubmissionLog`, `Dashboard`), via `tailwindcss` +
`postcss` + `autoprefixer` and a `src/index.css` with the standard
`@tailwind base/components/utilities` directives.

**Alternatives considered**: plain CSS / CSS Modules (no new deps, but more
manual layout work); a full component library such as Mantine (faster
polished UI, but adds several dependencies and requires wrapping the app and
tests in a `MantineProvider`).

**Why**: Owner preferred Tailwind as a middle ground — utility classes give a
reasonably polished look without a component-library dependency or
provider-wrapping overhead in component tests.

## 2026-06-12: Status/resubmission API design (Phase 7)

**Decision**: `GET /api/status-history` and `GET /api/resubmissions` use
`?limit=&offset=` query params (defaults 50, max 200) and return a JSON
envelope `{items, total, limit, offset}`, ordered by timestamp descending.
Response models use snake_case field names matching the SQLAlchemy column
names (`checked_at`, `raw_text`, `submitted_at`, `discord_notified`, etc.),
defined in a new shared `app/api/schemas.py`, with both endpoints living in
`app/api/routers/status.py` per the existing plan.

**Alternatives considered**: bare-array response with an `X-Total-Count`
header instead of an envelope; cursor-based (keyset) pagination; camelCase
field aliases matching the `TournamentDTO` precedent; colocating the response
models directly in `status.py` instead of a shared schemas module.

**Why**: Owner preferred the explicit pagination envelope (easier for the
Phase 8 dashboard to render page/total info), snake_case fields (simplest
Pydantic models, no alias config, frontend maps names in its API client), and
a shared `schemas.py` so Phase 11's organizer-activity router can reuse the
pagination envelope type.

## 2026-06-12: Celery task session/browser lifecycle (Phase 6)

**Decision**: Add `app/scraper/session.py` with an `authenticated_page()`
context manager: launches chromium, loads `storage_state.json` if present,
falls back to `browser.login()` with settings credentials if missing/expired,
yields a `Page`, closes the browser on exit. Both `status_tasks.py` and
`resubmit_tasks.py` use this single helper.

**Alternatives considered**: Inline per-task browser/session setup,
duplicating the launch + fallback-login logic in each task module.

**Why**: Single seam to mock in tests (consistent with NFR5 — no live calls
in CI), avoids duplicating session-management logic across tasks.

## 2026-06-12: Branch protection on `main`

**Decision**: Rely on workflow convention only (branch -> PR -> review ->
owner merge, per `CONTRIBUTING.md`). Do not enable GitHub branch protection
rules on `main`.

**Alternatives considered**: Enable GitHub branch protection requiring PRs
and owner approval before merge, enforcing the convention at the platform
level.

**Why**: Owner chose convention-only enforcement for now.

## 2026-06-12: Technical decisions log format

**Decision**: Single `DECISIONS.md` at repo root, newest entries first.

**Alternatives considered**: `docs/decisions/` with one numbered ADR file per
decision (Context/Decision/Consequences template).

**Why**: Owner preferred lower overhead and a single chronological file over
per-decision ADR files.

## (retroactive) GitHub over GitLab

**Decision**: Host this project on GitHub (`gh` CLI, GitHub Actions CI,
GitHub Issues/PRs).

**Alternatives considered**: GitLab (issues, CI/CD, MRs).

**Why**: Owner's choice, recorded retroactively here for traceability.
