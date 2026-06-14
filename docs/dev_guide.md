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
| `DISCORD_WEBHOOK_URL` | Webhook for resubmission notifications |
| `APPLICATION_STATUS_CHECK_INTERVAL_HOURS` | How often to check application status |
| `RESUBMIT_TIMES_UTC` | Comma-separated `HH:MM` UTC times for resubmission (1-2 per day) |
| `TOURNAMENT_INGEST_INTERVAL_HOURS` | How often to ingest tournament data |
| `TOURNAMENT_INGEST_LIMIT` | Number of most-recent tournaments pulled per ingestion run |
| `VITE_API_BASE_URL` | Frontend's base URL for the backend API |

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

## VS Code dev container

`.devcontainer/devcontainer.json` (with `docker-compose.override.yml`)
attaches VS Code to the `backend` service, with the full repo (including
`.git`) mounted at `/workspace` for source control. `postgres`, `redis`,
`celery-worker`, `celery-beat`, and `frontend` run as sibling containers on
the same compose stack — "Reopen in Container" brings up the whole stack via
`docker compose up`. `shutdownAction` is `none`, so closing the VS Code
window doesn't stop the other services. Run tests from `/workspace/backend`
(`pyproject.toml`'s `testpaths` is relative to that directory).

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
