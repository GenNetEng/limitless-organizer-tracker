# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/). Per
[DECISIONS.md](DECISIONS.md), each MVP milestone bumps the minor version
(0.1.0, 0.2.0, ...) until a 1.0.0 release is determined.

## [Unreleased]

### Added
- `LIMITLESS_APPLICATION_ID` (`.env.example`, `app/config.py`): the
  organizer application's ID, taken from the URL of the application page
  (`https://play.limitlesstcg.com/user/application/<id>`) or the Discord
  resubmission message's link. Used by FR2's status check to build the
  application page URL.
- `POST /api/status-check` (FR14, `app/api/routers/status.py`): runs an
  on-demand application-status check synchronously (login, scrape, record
  datapoint, post a Discord notice if the status changed) and returns the
  recorded `StatusCheckOut`. Lets you verify scraper selectors / check status
  immediately instead of waiting for the next
  `application_status_check_interval_hours` tick. No auth, matching the rest
  of the API. `app/tasks/status_tasks.py` now exposes
  `run_application_status_check(session)`, shared by both the Celery task and
  this endpoint.

### Fixed
- `app/main.py`: `CORSMiddleware` now allows `POST` (in addition to `GET`), so
  the new `POST /api/status-check` (FR14) can be called cross-origin from the
  dashboard's configured origin. Previously only `GET` was allowed, which
  would fail the browser's preflight check for any `POST` request.
- `backend/Dockerfile` / `backend/pyproject.toml`: pin `playwright==1.60.0`
  and bump the base image to `mcr.microsoft.com/playwright/python:v1.60.0-noble`
  so the installed `playwright` package matches the browsers bundled in the
  image. Previously `playwright>=1.45` resolved to `1.60.0` at build time
  while the `v1.48.0-noble` base image only bundled `1.48.0`'s browsers,
  causing every `authenticated_page()` call (FR2/FR3/FR14) to fail with
  `BrowserType.launch: Executable doesn't exist at
  /ms-playwright/chromium_headless_shell-1223/...` (500 from
  `POST /api/status-check`).
- FR2 (`app/scraper/selectors.py`, `app/scraper/application_status.py`): the
  status check now navigates to the organizer's own application page
  (`/user/application/<LIMITLESS_APPLICATION_ID>`) and reads the status from
  `.organizer-application .status .code`, both verified against a live,
  authenticated session. Previously it navigated to
  `/account/settings/orgs` (a placeholder that returns no content for this
  account) and looked for a non-existent `.application-status` element, so
  `POST /api/status-check` returned 200 with `status: "unknown"` and an
  empty `raw_text` instead of the real status. The "pending" wording is
  verified live; "approved"/"rejected"/"expired" fixtures
  (`tests/fixtures/html/application_*.html`) are best-guess based on the same
  structure — if a real status doesn't match, `parse_status_html` falls back
  to `UNKNOWN` and preserves `raw_text` for manual reading.

### Changed
- Clarified FR4/BR2 (`.env.example`, `README.md`, `docs/requirements.md`):
  `DISCORD_WEBHOOK_URL` points to a webhook on the user's own server, not the
  Limitless organizer Discord. The tracker posts a notification there for the
  user to manually copy/paste into the organizer Discord. No code change —
  `app/notifications/discord.py` already just posts to whatever webhook URL
  is configured. See `DECISIONS.md`.

## [0.1.0] - 2026-06-13

### Added
- **MVP1 acceptance (Phase 9)**: verified via `docker compose up --build` —
  `postgres`/`redis` report healthy, `backend` serves `/healthz` (200) after
  applying migrations on startup, `celery-worker`/`celery-beat` connect to
  Redis and start without error, and `frontend` serves the dashboard at
  `:5173`. `docker compose run --rm backend pytest` (68/68) and
  `docker compose run --rm frontend npm test -- --run` (5/5) both pass inside
  the containers. Closes the MVP1 acceptance checkpoint in
  `docs/requirements.md`.
- `backend/entrypoint.sh`: runs `alembic upgrade head` before exec'ing the
  container command. Set as the `backend` image's `ENTRYPOINT`
  (`backend/Dockerfile`), so the `backend` service applies pending migrations
  on every `docker compose up` instead of requiring a manual
  `docker compose exec backend alembic upgrade head`.
- `frontend/`: Vite + React + TypeScript dashboard scaffold. `src/api/client.ts`
  fetches `/api/status-history` and `/api/resubmissions` (typed `Page<T>`
  envelope matching `app/api/schemas.py`) via `VITE_API_BASE_URL`.
  `src/components/StatusTimeline.tsx` and `src/components/ResubmissionLog.tsx`
  render the two feeds via TanStack Query; `src/pages/Dashboard.tsx` renders
  both. Styled with Tailwind CSS. Covers FR9/FR10 (dashboard UI).
- `app/main.py`: `CORSMiddleware` allowing cross-origin requests from the
  frontend dev server, configurable via the new `CORS_ALLOWED_ORIGINS`
  setting (default `http://localhost:5173`), so the dashboard can call the
  API directly from the browser.
- `app/api/routers/status.py`: `GET /api/status-history` and
  `GET /api/resubmissions`, returning `ApplicationStatusCheck` /
  `ResubmissionEvent` rows ordered by timestamp descending, paginated via
  `?limit=&offset=` (default `limit=50`, max `200`) in a
  `{items, total, limit, offset}` envelope (`app/api/schemas.py`). The
  count+paginate query logic is shared via `app/api/pagination.py`
  (`paginate()`), for reuse by future routers (e.g. Phase 11). Wired into
  `app/main.py`. Covers FR9/FR10 (API support for the Phase 8 dashboard).
- `app/scraper/session.py`: `authenticated_page()` context manager launches a
  Playwright browser, reuses `storage_state.json` if present, otherwise logs
  in with the configured credentials and persists the session.
- `app/celery_app.py`: Celery app bound to `celery_broker_url` /
  `celery_result_backend`, with a beat schedule built from
  `application_status_check_interval_hours` (status-check task) and
  `resubmit_times_utc` (one resubmit-task entry per configured time, via
  `parse_resubmit_times`).
- `app/tasks/status_tasks.py`: `check_application_status_task` checks the
  application status via an authenticated page, records each check as a
  timestamped datapoint (`record_status_check`, FR2), and posts a Discord
  status-change notice (`post_status_update_notice`,
  `app/notifications/discord.py`) only when the status differs from the
  previous check.
- `app/tasks/resubmit_tasks.py`: `resubmit_application_task` resubmits the
  application via an authenticated page, records the outcome
  (`record_resubmission`, FR5), and always posts a Discord resubmission
  notice (FR4).
- `docs/requirements.md`: FR2/FR3/FR5 marked done, FR4 extended to cover the
  Phase 6 status-change notice, and NFR3 marked done for MVP1 tasks.
- `DECISIONS.md`: new technical-decisions log (newest-first), with a
  "Technical decisions" section in `CONTRIBUTING.md` requiring owner sign-off
  before any non-trivial technical decision.
- `app/scraper/browser.py`: `login(page, username, password, storage_state_path=...)`
  authenticates against the play.limitlesstcg.com password login form and
  persists the session to `storage_state.json` for reuse (FR1).
- `app/scraper/resubmit.py`: `resubmit_application(page) -> bool` clicks the
  resubmit button and reports success/failure based on the resulting page
  state (FR3). `app/scraper/parsing.py` gains `parse_resubmit_result` plus a
  `RESUBMIT_RESULT_SELECTOR` and new fixtures
  (`org_settings_resubmit_success.html`, `org_settings_resubmit_failure.html`).
- `app/notifications/discord.py`: `post_resubmission_notice(webhook_url,
  timestamp, success)` posts a resubmission-outcome message to a Discord
  webhook via `httpx` (FR4).
- `docs/requirements.md`: FR1 marked done; FR2/FR3/FR4/FR5 updated to reflect
  login/resubmit/notifier logic landing in Phase 5, with scheduled-task
  wiring and persistence remaining in Phase 6. NFR5 now covers Phases 4-5.
- `docs/requirements.md`: BR3 expanded to cover wait-time estimation, and two
  new functional requirements for MVP2: FR12 (linear regression of
  `organizer_id` vs. `first_tournament_date` to estimate the onboarding rate
  and project a target organizer ID's active date) and FR13 (dashboard
  regression chart + wait-time estimator). FR6 now also covers a paginated
  historical backfill (`TOURNAMENT_BACKFILL_MONTHS`, default 3 months) needed
  to seed the FR12 regression, scoped to Phase 10. Phases 10-12 build-order
  descriptions updated accordingly.
- `docs/requirements.md`: Business/Functional/Non-Functional requirements
  (BR1-3, FR1-11, NFR1-6) with an MVP breakdown (MVP1: application status &
  resubmission tracker, MVP2: organizer activity analytics, MVP3:
  documentation & traceability) and a per-phase build order through Phase 14.
  Phases 1-4 are retroactively tagged: FR6/FR7/NFR1/NFR2/NFR4/NFR6 are done
  (Phases 1-3), and application-status HTML parsing (part of FR2) and NFR5
  are done (Phase 4). README links to this doc under a new "Requirements &
  MVPs" section.
- GitHub milestones for MVP1-MVP3 and one tracking issue per remaining phase
  (#2-#11), linked from the `docs/requirements.md` build-order table.
- `docs/dev_guide.md`: local backend setup, test layout (unit/integration/
  acceptance/fixtures), `@pytest.mark.live` usage, environment variable
  reference, running the full stack via `docker compose`, CI overview, and
  Alembic migration workflow.
- `CONTRIBUTING.md`: per-phase contribution workflow (branch → TDD → docs →
  CHANGELOG → commit → PR → `/code-review` + `/security-review` → merge),
  commit message conventions, and general repo rules. README links to both
  new docs.
- Monorepo scaffold: `.gitignore`, `.env.example`, `docker-compose.yml`
  (postgres, redis, backend, celery-worker, celery-beat, frontend),
  `backend/Dockerfile`, `frontend/Dockerfile`, `backend/pyproject.toml`,
  and GitHub Actions CI workflow (`.github/workflows/ci.yml`) covering
  backend lint/test, frontend lint/test, and docker builds.
- Backend foundation: pydantic-settings config (`app/config.py`), FastAPI
  app with `/healthz`, SQLAlchemy models (`ApplicationStatusCheck`,
  `ResubmissionEvent`, `Tournament`, `OrganizerActivity`), DB session
  helper, and an initial Alembic migration creating all four tables.

- `UTCDateTime` SQLAlchemy type decorator so all timestamp columns
  round-trip as UTC-aware datetimes on both SQLite (tests) and Postgres.
- Limitless tournaments API client (`app/limitless_client/tournaments_api.py`)
  and `TournamentDTO` schema for `GET /api/tournaments`.
- Tournament ingestion (`app/limitless_client/ingestion.py`): upserts
  tournament rows and maintains an `OrganizerActivity` row per
  (organizer_id, game) tracking first/last-seen tournament dates.

- Application-status scraper (`app/scraper/`): `parse_status_html` extracts
  the organizer application status (pending/approved/rejected/expired/unknown)
  from the `/account/settings/orgs` page HTML, and `check_application_status`
  is a thin Playwright wrapper around it. CSS selectors are isolated in
  `app/scraper/selectors.py` as best-guess placeholders pending a live
  verification pass against an authenticated session.

### Fixed
- `docker-compose.yml`: `celery-worker` and `celery-beat` now set
  `entrypoint: []` to skip the `backend` image's migration-running
  entrypoint. Running `alembic upgrade head` concurrently in all three
  backend-image services against a fresh database raced on
  `CREATE TABLE alembic_version`, crashing two of the three containers with
  `psycopg.errors.UniqueViolation`. Only `backend` now applies migrations on
  startup.
- `backend/Dockerfile`: `COPY . .` now runs before
  `pip install -e ".[dev]"`, so the editable install's generated package
  finder includes the `app` source mapping. Previously, `docker compose run
  --rm backend pytest` failed all 24 test files with
  `ModuleNotFoundError: No module named 'app'` (the editable install was
  performed against an empty source tree); `uvicorn`/`celery` masked this
  because both prepend `cwd` to `sys.path` when resolving import strings.
- `app/tasks/resubmit_tasks.py` / `app/tasks/status_tasks.py`: Discord
  notification failures (e.g. `discord_webhook_url` unset, the default) no
  longer crash the task or prevent the FR2/FR5 datapoint from being recorded
  — `httpx.HTTPError` is caught around each notification call and
  `discord_notified` is recorded as `False`.
- `app/celery_app.py`: `parse_resubmit_times` now skips blank entries instead
  of raising on an empty `resubmit_times_utc`, and a new
  `_status_check_schedule` helper treats a non-positive
  `application_status_check_interval_hours` as hourly instead of raising
  `ValueError` from `crontab(hour="*/0")` — both previously crashed
  `app.celery_app` at import time on misconfiguration.
- `app/scraper/session.py`: `authenticated_page()` now closes the browser even
  if `login()` raises, preventing a leaked Chromium process on login failure.
- `app/tasks/status_tasks.py`: `record_status_check`'s previous-check lookup
  now breaks `checked_at` ties with `id desc`, making status-change detection
  deterministic.

### Tests
- `frontend`: Vitest + React Testing Library + MSW component tests for
  `StatusTimeline`, `ResubmissionLog`, and `Dashboard` covering loading
  states and rendering of mocked `/api/status-history` /
  `/api/resubmissions` responses.
- Integration tests for `CORSMiddleware`: a simple cross-origin `GET` and a
  preflight `OPTIONS` request from `http://localhost:5173` both receive
  `Access-Control-Allow-Origin`.
- Integration tests for `GET /api/status-history` and `GET /api/resubmissions`
  via `TestClient` against an in-memory SQLite DB (overriding `get_db`):
  envelope shape, descending-timestamp ordering, `limit`/`offset` pagination,
  the `limit<=200` validation boundary, and the empty-table case.
- Unit tests for `authenticated_page` (mocked Playwright, both with and
  without an existing `storage_state.json`), `parse_resubmit_times` and the
  beat schedule contents, `record_status_check` (first-check and
  status-change detection), `record_resubmission`, and the new
  `build_status_update_message`/`post_status_update_notice` Discord helpers.
  Integration tests run `check_application_status_task` and
  `resubmit_application_task` in Celery eager mode against an in-memory
  SQLite DB with mocked Playwright/Discord. Acceptance tests in
  `tests/acceptance/` cover the scheduled status-change and resubmission
  flows end-to-end (FR2, FR5). Additional unit/integration tests cover the
  code-review fixes above: `parse_resubmit_times` with empty/blank entries,
  `_status_check_schedule` with a non-positive interval,
  `authenticated_page` closing the browser when `login()` raises, and both
  scheduled tasks recording their datapoint when `discord_webhook_url` is
  unset.
- Unit tests for `parse_resubmit_result`, the `login` browser helper, and
  `resubmit_application` (mocked Playwright `Page`), plus Discord message
  templating. Integration test for `post_resubmission_notice` (respx-mocked).
  Acceptance tests in `tests/acceptance/` cover the login flow (FR1) and the
  resubmit-then-notify flow for both success and failure outcomes (FR3, FR4).
- Unit tests for the `ApplicationStatus` enum, model table names, the
  `TournamentDTO` schema, tournament ingestion/activity aggregation
  (first-seen tracking, per-game separation, re-ingestion updates, upserts),
  and application-status HTML parsing against hand-authored fixtures for
  each status plus the "no application yet" case.
- Integration tests for `/healthz`, DB model round-trips, and the
  tournaments API client (mocked via `respx` using real sample payloads).
