# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
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
