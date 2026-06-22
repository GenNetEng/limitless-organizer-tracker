# Developer Guide

This guide covers local setup, running the backend/test suite, and the
project's environment configuration. For the requirements/MVP breakdown and
build order, see [`requirements.md`](requirements.md).

## Prerequisites

- Python 3.12+
- Docker + Docker Compose (for Postgres, Redis, and the full stack)
- Node.js 20+ (for the frontend, from Phase 8 onward)

## Backend: local development

The backend uses a local virtualenv for fast TDD; Postgres/Redis run via
Docker Compose.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the test suite (fast, no live network calls — `@pytest.mark.live` tests
are excluded by default):

```bash
pytest
```

Run lint:

```bash
ruff check app tests
```

### Test layout

- `tests/unit/` — pure logic (parsing, schemas, models, aggregation), no I/O.
- `tests/integration/` — FastAPI `TestClient`, SQLite-backed DB round-trips,
  and external APIs mocked with `respx`.
- `tests/acceptance/` — Given/When/Then style tests that trace back to the
  FR IDs in [`requirements.md`](requirements.md).
- `tests/fixtures/` — sample HTML/JSON used by unit and integration tests.

### Live tests

Tests marked `@pytest.mark.live` hit the real `play.limitlesstcg.com` and are
skipped by default (`addopts = "-m 'not live'"` in `pyproject.toml`). Run them
explicitly, with real credentials in `.env`, when verifying scraper selectors
against the live site:

```bash
pytest -m live
```

## Environment configuration

Copy `.env.example` to `.env` and fill in real values. `.env` is gitignored —
never commit real credentials or webhook URLs.

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Postgres connection string |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Redis URLs for Celery |
| `LIMITLESS_BASE_URL` | Base URL for play.limitlesstcg.com |
| `LIMITLESS_USERNAME` / `LIMITLESS_PASSWORD` | Scraper login credentials |
| `LIMITLESS_APPLICATION_ID` | Your organizer application's numeric ID — from the URL `…/user/application/<id>` |
| `DISCORD_WEBHOOK_URL` | Webhook for a channel on **your own** Discord server; the tracker posts a notice here that you copy/paste into the organizer Discord |
| `CORS_ALLOWED_ORIGINS` | Comma-separated origins allowed to call the API (default: `http://localhost:5173`) |
| `APPLICATION_STATUS_CHECK_INTERVAL_HOURS` | How often to run the application-status check, in hours (default: 4) |
| `RESUBMIT_TIMES_UTC` | Comma-separated `HH:MM` UTC times for resubmission; provide 1 or 2 (e.g. `09:00,21:00`) |
| `TOURNAMENT_INGEST_INTERVAL_HOURS` | How often to ingest tournament data, in hours (default: 1) |
| `TOURNAMENT_INGEST_LIMIT` | Number of most-recent tournaments pulled per ingestion run (default: 1000) |
| `TOURNAMENT_BACKFILL_MONTHS` | Months of historical tournament data to keep backfilled per run (default: 3) |
| `ORGANIZER_SCAN_INTERVAL_HOURS` | How often the organizer onboarding scanner runs, in hours (default: 24) |
| `ORGANIZER_SCAN_LIMIT` | Max new organizer IDs probed per scan run (default: 50) |
| `API_KEY` | Shared secret protecting `/api/*` endpoints; must match `VITE_API_KEY` |
| `VITE_API_BASE_URL` | Frontend's base URL for the backend API |
| `VITE_API_KEY` | API key baked into the frontend build; sent as `X-API-Key` header on every request |

### Scraper selectors

The Playwright-based scraper (login, status check, resubmit) targets
`play.limitlesstcg.com` CSS selectors defined in `app/scraper/selectors.py`.
These selectors were validated against the live site during development but
may drift if Limitless updates their front end. To verify them against the
live site, set real credentials in `.env` and run:

```bash
pytest -m live
```

Live tests are skipped by default in CI (`addopts = "-m 'not live'"` in
`pyproject.toml`). The organizer onboarding scanner (`scan_new_organizers_task`)
uses plain `httpx` against public profile pages — no selectors, no login.

## Running the full stack

```bash
docker compose up
```

This brings up `postgres`, `redis`, `backend` (FastAPI on :8000),
`celery-worker`, `celery-beat`, and `frontend` (Vite dev server on :5173).
Check the backend is healthy:

```bash
curl localhost:8000/healthz
```

Run the backend test suite inside Docker:

```bash
docker compose run backend pytest
```

## Admin API

The admin router (`/api/admin/*`) provides operational visibility into the
running system. All endpoints require the `X-API-Key` header.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/event-log` | GET | Paginated, filterable event log (query params: `limit`, `offset`, `event_type`, `severity`, `source`) |
| `/api/admin/diagnostics` | GET | System health: DB/Redis connectivity, Celery worker list, beat status, last success per task |
| `/api/admin/config` | GET | Current non-sensitive configuration values (intervals, limits) |
| `/api/admin/tasks` | GET | Available task trigger endpoints for the frontend trigger buttons |

The frontend Admin tab consumes these endpoints via four components:
`EventLogViewer`, `Diagnostics`, `TaskTriggers`, and `AdminConfig`.

## CI

GitHub Actions (`.github/workflows/ci.yml`) runs on every push and PR:
backend lint (`ruff`) + tests (`pytest --cov=app`, including Playwright
install), and frontend lint + tests (from Phase 8 onward). `docker-build`
runs on pushes to `main` only.

## Database migrations

Schema changes go through Alembic (`backend/alembic/`). After changing a
SQLAlchemy model:

```bash
cd backend
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

Commit the generated migration alongside the model change.
