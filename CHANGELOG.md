# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
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
  MVPs" section.
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
- Unit tests for the `ApplicationStatus` enum, model table names, the
  `TournamentDTO` schema, tournament ingestion/activity aggregation
  (first-seen tracking, per-game separation, re-ingestion updates, upserts),
  and application-status HTML parsing against hand-authored fixtures for
  each status plus the "no application yet" case.
- Integration tests for `/healthz`, DB model round-trips, and the
  tournaments API client (mocked via `respx` using real sample payloads).
