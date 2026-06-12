# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
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

### Tests
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
