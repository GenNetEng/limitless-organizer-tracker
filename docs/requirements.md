# Requirements & MVP Traceability

This document tracks the Business Requirements (BR), Functional Requirements
(FR), and Non-Functional Requirements (NFR) for the Limitless Organizer
Tracker, and maps them to the MVPs and build phases that implement them.

## Business Requirements (BR)

- **BR1**: Provide visibility into organizer-application throughput
  (status-check history, outcomes) that Limitless does not report on.
- **BR2**: Maximize approval likelihood by automating frequent, scheduled
  resubmission per Limitless's LIFO-favoring review process, with a Discord
  notification per resubmission sent to the user's own server (for manual
  copy/paste into the organizer Discord, matching the existing manual habit).
- **BR3**: Provide visibility into platform-wide organizer growth — how many
  new organizers (across all games) become active each week/month, based on
  each organizer's first tournament date — and estimate how long a new
  applicant should expect to wait before their organizer ID becomes active,
  based on the current onboarding rate. Also capture actual organizer
  onboarding dates (when the organizer profile page first goes live) for
  forward-looking daily onboarding-rate analytics and delta measurement
  (time from onboarding to first tournament).

## Functional Requirements (FR)

| ID | Requirement | Serves | Status / Phase |
|----|-------------|--------|-----------------|
| FR1 | Log into play.limitlesstcg.com via Playwright using stored username/password, persisting session for reuse | BR1, BR2 | **Done — Phase 5** (`app/scraper/browser.py`) |
| FR2 | Check organizer/organization application status on a configurable schedule; record each check as a timestamped datapoint (status enum + raw text) | BR1 | **Done — Phase 6** (`app/tasks/status_tasks.py`, `check_application_status_task`, beat schedule via `application_status_check_interval_hours`) |
| FR3 | Resubmit the organization application 1-2x/day on a configurable schedule | BR2 | **Done — Phase 6** (`app/tasks/resubmit_tasks.py`, `resubmit_application_task`, beat schedule via `resubmit_times_utc`) |
| FR4 | Post a Discord notification (to the user's own server, via `DISCORD_WEBHOOK_URL`) when a resubmission occurs, for manual copy/paste into the organizer Discord | BR2 | **Done — Phase 5/6** (`app/notifications/discord.py`; wired into `resubmit_application_task`. Phase 6 also adds a status-change notice for FR2.) |
| FR5 | Log each resubmission as a timestamped datapoint (success flag, discord-notified flag) | BR1, BR2 | **Done — Phase 6** (`record_resubmission` in `app/tasks/resubmit_tasks.py`) |
| FR6 | Ingest tournament data from `GET /api/tournaments` across all games | BR3 | **Done — Phase 3/10**: recent ingestion (Phase 3) plus paginated historical backfill (`TOURNAMENT_BACKFILL_MONTHS`, default 3 months) on a Celery beat schedule (`app/tasks/tournament_tasks.py`) |
| FR7 | Determine each organizer's ID and first-tournament date per game from ingested data | BR3 | **Done — Phase 3** (`OrganizerActivity`) |
| FR8 | Compute counts of newly-active organizers per week/month, overall and filterable by game | BR3 | **Done — Phase 11** (`GET /api/organizers/activity`, `app/api/routers/organizers.py`) |
| FR9 | Dashboard displays application status-check history (timeline) | BR1 | **Done — Phase 7/8** (`GET /api/status-history`; `frontend/src/components/StatusTimeline.tsx`) |
| FR10 | Dashboard displays resubmission log | BR1, BR2 | **Done — Phase 7/8** (`GET /api/resubmissions`; `frontend/src/components/ResubmissionLog.tsx`) |
| FR11 | Dashboard displays newly-active-organizer counts per week/month, filterable by game | BR3 | **Done — Phase 12** (`frontend/src/components/OrganizerActivityChart.tsx`) |
| FR12 | Identify the top 1000 highest `organizer_id`s globally (one point per organizer using `MIN(first_tournament_date)` across games), compute the Pareto frontier (lower-envelope — points not dominated by any other point with a higher ID and earlier date), fit OLS regression on the frontier to estimate the onboarding rate (slope), and optionally project when a target organizer ID will become active | BR3 | **Done — Phase 12.5** ([#41](https://github.com/GenNetEng/limitless-organizer-tracker/issues/41), `GET /api/organizers/wait-estimate`, `app/analytics/frontier.py`, `app/analytics/regression.py`) |
| FR13 | Dashboard displays the onboarding-rate scatter (general + frontier series) with fitted line and R²; optionally shows a projected active date for a user-supplied target organizer ID | BR3 | **Done — Phase 12.5** ([#41](https://github.com/GenNetEng/limitless-organizer-tracker/issues/41), `frontend/src/components/WaitTimeEstimator.tsx`) |
| FR14 | Provide an API endpoint to trigger an on-demand application-status check (extends FR2), running synchronously and returning the recorded result | BR1 | **Done** — [#23](https://github.com/GenNetEng/limitless-organizer-tracker/issues/23) (`POST /api/status-check`, `app/api/routers/status.py`) |
| FR15 | Given an organizer ID, scrape `play.limitlesstcg.com/organizer/{id}` via the FR18 endpoint and display the organizer's name, upcoming/recent tournaments, and highest known organizer ID stat card on the dashboard | BR3 | **Done — Phase 17** ([#45](https://github.com/GenNetEng/limitless-organizer-tracker/issues/45), `frontend/src/components/OrganizerProfile.tsx`) |
| FR16 | Dashboard stat card showing the highest organizer ID currently in the `Organizer` table (populated by FR17 scanner) | BR3 | **Done — Phase 16** (API) / **Phase 17** (UI: `frontend/src/components/HighestOrganizerIdCard.tsx`) — [#45](https://github.com/GenNetEng/limitless-organizer-tracker/issues/45) |
| FR17 | Detect and record actual organizer onboarding dates: daily Celery task scans `play.limitlesstcg.com/organizer/{id}` (public page, httpx, no auth) starting from `MAX(organizer_id) + 1` across `Organizer` + `OrganizerActivity` tables, increments until the first 404; each 200 records the organizer in the new `Organizer` table with `onboarded_at = today`. Tournament ingestion also upserts `Organizer.first_tournament_date` (MIN across games) so the onboarding-to-first-tournament delta is always fresh | BR3 | **Done — Phase 14** ([#51](https://github.com/GenNetEng/limitless-organizer-tracker/issues/51)) |
| FR18 | `GET /api/organizers/{id}/scrape` — httpx fetch of the public `play.limitlesstcg.com/organizer/{id}` page, parsed via BeautifulSoup 4, returning organizer name and tournament list as JSON; no DB storage (data lives on the source page). Tested against fixture HTML | BR3 | **Done — Phase 16** ([#45](https://github.com/GenNetEng/limitless-organizer-tracker/issues/45)) |
| FR19 | Centralized event log: all significant application operations (task lifecycle, scraper actions, data ingestion, notifications, API triggers) are recorded in a partitioned `event_log` table with event type, severity, source, message, and JSON metadata. Provides an `app/events.py` service callable from any module | BR1 | **Done — Phase 21a** (`app/events.py`, `app/db/models.py`) |
| FR20 | Admin event-log API: `GET /api/admin/event-log` returns paginated, filterable event log entries (by event type, severity, source, date range) | BR1 | **Done — Phase 21a** (API), **Phase 21b** (frontend: `EventLogViewer.tsx`) |
| FR21 | Admin diagnostics API: `GET /api/admin/diagnostics` returns system health (DB status, Redis connectivity, Celery worker/beat status, last successful run per task) | BR1 | **Done — Phase 21a** (API), **Phase 21b** (frontend: `Diagnostics.tsx`) |
| FR22 | Admin config API: `GET /api/admin/config` returns current non-sensitive configuration (scan intervals, backfill months, ingest limits) via hardcoded allowlist | BR1 | **Done — Phase 21a** (API), **Phase 21b** (frontend: `AdminConfig.tsx`) |
| FR23 | Admin tasks API: `GET /api/admin/tasks` returns available task trigger endpoints for frontend task-trigger buttons | BR1 | **Done — Phase 21a** (API), **Phase 21b** (frontend: `TaskTriggers.tsx`) |

## Non-Functional Requirements (NFR)

| ID | Requirement | Status |
|----|-------------|--------|
| NFR1 | TDD (red→green→refactor) for all code, with unit/integration/acceptance coverage | **Established — Phases 1-4** (18 tests, ongoing each phase) |
| NFR2 | API-first backend, written in Python (FastAPI), decoupled from frontend | **Established — Phases 1-2** |
| NFR3 | Always-running architecture via Celery worker + beat scheduler | **Done — Phases 6/10** (`app/celery_app.py`): MVP1 status-check/resubmit tasks plus MVP2 tournament-ingestion task |
| NFR4 | Monorepo, public on GitHub, with GitHub Actions CI | **Established — Phase 1** |
| NFR5 | Scraper logic decoupled from live site; tested via fixture HTML, no live calls in CI (`@pytest.mark.live` reserved for future) | **Established — Phases 4-5** |
| NFR6 | Configuration via environment variables (`.env`), no secrets committed | **Established — Phases 1-2** |

## MVP Breakdown

### MVP1 — Application Status & Resubmission Tracker
Serves BR1, BR2 / FR1-5, FR9-10, partial NFR3. Phases 5-9.

**Acceptance**: `docker compose up` runs backend + celery worker/beat +
postgres/redis + frontend; status checks and resubmissions are logged on
schedule; Discord notified on resubmission; dashboard shows status timeline
and resubmission log.

**Verified — Phase 9 (2026-06-13)**: `docker compose up --build` brings up all
six services; `backend` applies migrations on startup and serves `/healthz`
(200); `celery-worker`/`celery-beat` connect to Redis and start without
error; `frontend` serves the dashboard at `:5173`. Full test suites pass in
containers: `docker compose run --rm backend pytest` (68/68) and
`docker compose run --rm frontend npm test -- --run` (5/5).

### MVP2 — Organizer Activity Analytics
Serves BR3 / FR6-8, FR11-18, remaining NFR3. Phases 10-13, 15, 18.

**Acceptance**: tournament ingestion runs on schedule, including a paginated
historical backfill (default 3 months); `/api/organizers/activity` returns
correct weekly/monthly counts, filterable by game; `/api/organizers/wait-estimate`
returns a global Pareto-frontier regression (top-1,000 organizer IDs) with
slope/R²/frontier_size and an optional projected active date for a supplied
organizer ID; dashboard organizer-activity chart renders filterable by game;
wait-time estimator renders the scatter + fitted line on load;
`scan_new_organizers_task` runs daily and records `Organizer.onboarded_at`;
`/api/organizers/onboarding-history` returns daily/weekly counts.

**Verified — Phase 13 (2026-06-18)**: `docker compose up --build` brings up all
six services cleanly; `celery-worker` registers all 3 tasks and connects to
Redis; `celery-beat` starts. Full test suites pass in containers:
`docker compose run --rm backend pytest` (121/121) and
`docker compose run --rm frontend npm test -- --run` (30/30). Live checks:
`GET /api/games` → 12 games; `GET /api/organizers/activity?interval=week` →
weekly counts; `GET /api/organizers/wait-estimate?organizer_id=2720` →
slope/R²/projected_date (sample_size=468, frontier_size=55).

**Phase 14 extension (2026-06-18)**: FR17 (`scan_new_organizers_task` + `Organizer`
table + `GET /api/organizers/onboarding-history`) implemented and merged (PR #53).
Backend test suite extended to 121 tests; all pass.

### MVP3 — Documentation & Traceability
Project hygiene / final NFR coverage. Phase 15.

**Acceptance**: README fully documents setup/env/scheduling/scraper-selector
caveat; this traceability table shows all FR/NFR as Done with final phase
references.

**Verified — Phase 15 (2026-06-18)**: `docs/dev_guide.md` covers all env vars
(including `LIMITLESS_APPLICATION_ID`, `CORS_ALLOWED_ORIGINS`,
`TOURNAMENT_BACKFILL_MONTHS`, `ORGANIZER_SCAN_INTERVAL_HOURS`,
`ORGANIZER_SCAN_LIMIT`) and the scraper-selector caveat. FR/NFR traceability
table is complete through Phase 14. README placeholder stub removed.

## Build Order

Tracked via [GitHub milestones](https://github.com/GenNetEng/limitless-organizer-tracker/milestones)
(one per MVP) and one issue per phase.

| Phase | Description | MVP | Issue |
|-------|-------------|-----|-------|
| 1 | Repo scaffold + CI | — | — |
| 2 | Backend foundation (config, FastAPI healthz, models, Alembic) | — | — |
| 3 | Tournament ingestion + organizer activity aggregation | MVP2 | — |
| 4 | Application-status scraper (fixture-based HTML parsing) | MVP1 | — |
| 4.5 | Requirements traceability doc (this file) | — | [#1](https://github.com/GenNetEng/limitless-organizer-tracker/pull/1) |
| 5 | Resubmit scraper + Discord notifier | MVP1 | [#2](https://github.com/GenNetEng/limitless-organizer-tracker/issues/2) |
| 6 | Celery app + beat schedule for status-check/resubmit tasks | MVP1 | [#3](https://github.com/GenNetEng/limitless-organizer-tracker/issues/3) |
| 7 | FastAPI routers: status history, resubmissions | MVP1 | [#4](https://github.com/GenNetEng/limitless-organizer-tracker/issues/4) |
| 8 | Frontend scaffold + MVP1 dashboard (status timeline, resubmission log) | MVP1 | [#5](https://github.com/GenNetEng/limitless-organizer-tracker/issues/5) |
| 9 | MVP1 docker-compose verification (acceptance checkpoint) — **Done** | MVP1 | [#6](https://github.com/GenNetEng/limitless-organizer-tracker/issues/6) |
| 10 | Tournament ingestion Celery task + beat schedule, including paginated historical backfill (default 3 months) — **Done** | MVP2 | [#7](https://github.com/GenNetEng/limitless-organizer-tracker/issues/7) |
| 11 | FastAPI routers: organizer activity, games, onboarding-rate regression/wait estimate (FR12) — **Done** | MVP2 | [#8](https://github.com/GenNetEng/limitless-organizer-tracker/issues/8) |
| 12 | Frontend organizer-activity chart + wait-time estimator (FR11, FR13) — **Done** | MVP2 | [#9](https://github.com/GenNetEng/limitless-organizer-tracker/issues/9) |
| 12.5 | Redesign wait-estimate: global top-1000 Pareto-frontier regression (FR12, FR13) — **Done** | MVP2 | [#41](https://github.com/GenNetEng/limitless-organizer-tracker/issues/41) |
| 13 | MVP2 docker-compose verification (acceptance checkpoint) — **Done** | MVP2 | [#10](https://github.com/GenNetEng/limitless-organizer-tracker/issues/10) |
| 14 | Organizer onboarding scanner: `Organizer` table (organizer_id, onboarded_at, first_tournament_date, detected_at), daily `scan_new_organizers_task` Celery task, `first_tournament_date` sync in tournament ingestion, `GET /api/organizers/onboarding-history` (FR17) — **Done** | MVP2 | [#51](https://github.com/GenNetEng/limitless-organizer-tracker/issues/51) |
| 15 | README + traceability finalization — **Done** | MVP3 | [#11](https://github.com/GenNetEng/limitless-organizer-tracker/issues/11) |
| 16 | Organizer profile backend: `GET /api/organizers/{id}/scrape` (httpx + BS4, FR18) + `GET /api/organizers/highest-id` (FR16 API) — **Done** | MVP2 | [#45](https://github.com/GenNetEng/limitless-organizer-tracker/issues/45) |
| 17 | Organizer profile frontend: `OrganizerProfile` component + `HighestOrganizerIdCard` stat card + Dashboard wiring (FR15, FR16 UI) — **Done** | MVP2 | [#45](https://github.com/GenNetEng/limitless-organizer-tracker/issues/45) |
| 18 | Cyberpunk theme via DaisyUI | MVP3 | [#46](https://github.com/GenNetEng/limitless-organizer-tracker/issues/46) |
| 19 | Helm chart + Rancher Fleet GitOps deployment to local k3s/MicroOS cluster — **Done** | MVP3 | [#47](https://github.com/GenNetEng/limitless-organizer-tracker/issues/47) |
| 20 | Separate Celery worker image with Playwright; expose all tasks as API endpoints — **Done** | MVP3 | [#69](https://github.com/GenNetEng/limitless-organizer-tracker/issues/69), [#71](https://github.com/GenNetEng/limitless-organizer-tracker/pull/71) |
| 21a | Admin API backend: EventLog model (partitioned), event logging service, Celery signal handlers, instrumented business logic, admin router (event-log, diagnostics, config, tasks) (FR19-FR23) | MVP3 | [#70](https://github.com/GenNetEng/limitless-organizer-tracker/issues/70) |
| 21b | Admin frontend: Admin tab with EventLog, Diagnostics, TaskTriggers, Config components — **Done** | MVP3 | [#70](https://github.com/GenNetEng/limitless-organizer-tracker/issues/70) |
| 22 | Backend refactors: shared test fixtures ([#57](https://github.com/GenNetEng/limitless-organizer-tracker/issues/57), [#32](https://github.com/GenNetEng/limitless-organizer-tracker/issues/32)), `task_session()` context manager ([#56](https://github.com/GenNetEng/limitless-organizer-tracker/issues/56), [#17](https://github.com/GenNetEng/limitless-organizer-tracker/issues/17)), dedupe test helpers ([#18](https://github.com/GenNetEng/limitless-organizer-tracker/issues/18)), merge bucket functions ([#55](https://github.com/GenNetEng/limitless-organizer-tracker/issues/55)) — **Done** | — | [#57](https://github.com/GenNetEng/limitless-organizer-tracker/issues/57), [#56](https://github.com/GenNetEng/limitless-organizer-tracker/issues/56), [#55](https://github.com/GenNetEng/limitless-organizer-tracker/issues/55), [#32](https://github.com/GenNetEng/limitless-organizer-tracker/issues/32), [#18](https://github.com/GenNetEng/limitless-organizer-tracker/issues/18), [#17](https://github.com/GenNetEng/limitless-organizer-tracker/issues/17) |
| 23 | Frontend cleanup: restore tab/table styling ([#77](https://github.com/GenNetEng/limitless-organizer-tracker/issues/77)), date-formatting helper ([#40](https://github.com/GenNetEng/limitless-organizer-tracker/issues/40)), query-string standardization ([#39](https://github.com/GenNetEng/limitless-organizer-tracker/issues/39)), remove unreachable branch ([#38](https://github.com/GenNetEng/limitless-organizer-tracker/issues/38)) — **Done** | MVP3 | [#77](https://github.com/GenNetEng/limitless-organizer-tracker/issues/77), [#40](https://github.com/GenNetEng/limitless-organizer-tracker/issues/40), [#39](https://github.com/GenNetEng/limitless-organizer-tracker/issues/39), [#38](https://github.com/GenNetEng/limitless-organizer-tracker/issues/38) |
| 24 | Performance: fix N+1 queries in tournament ingestion ([#54](https://github.com/GenNetEng/limitless-organizer-tracker/issues/54)), add index on `OrganizerActivity.game` ([#31](https://github.com/GenNetEng/limitless-organizer-tracker/issues/31)) | — | [#54](https://github.com/GenNetEng/limitless-organizer-tracker/issues/54), [#31](https://github.com/GenNetEng/limitless-organizer-tracker/issues/31) |
