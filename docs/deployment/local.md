# Local Deployment

Local development runs entirely via Docker Compose (`docker-compose.yml` at
the repo root) — no Kubernetes involved. See
[Getting Started](../getting-started.md) for the day-to-day workflow; this
page covers the service topology in detail.

## Service topology

```bash
docker compose up
```

| Service | Image / build | Port mapping | Purpose |
|---------|---------------|--------------|---------|
| `postgres` | `postgres:16-alpine` | `5432:5432` | Database, with a healthcheck (`pg_isready`) other services wait on |
| `redis` | `redis:7-alpine` | `6379:6379` | Celery broker (`/0`), result backend (`/1`), beat schedule store |
| `backend` | `./backend` | `8000:8000` | FastAPI (`uvicorn --reload`); bind-mounts `./backend` for live reload |
| `celery-worker` | `./backend` | — | Runs the scraper + ingestion tasks; same image as `backend`, no entrypoint |
| `celery-beat` | `./backend` | — | Reads the dynamic schedule from Redis and enqueues tasks |
| `frontend` | `./frontend` | `5173:5173` | Vite dev server with hot reload; bind-mounts `./frontend` |

`backend`, `celery-worker`, and `celery-beat` all read `.env` and share the
same in-cluster connection strings for Postgres/Redis (set directly in
`docker-compose.yml`, overriding whatever's in `.env` for those two):

```yaml
DATABASE_URL: postgresql+psycopg://postgres:postgres@postgres:5432/limitless_tracker
CELERY_BROKER_URL: redis://redis:6379/0
CELERY_RESULT_BACKEND: redis://redis:6379/1
```

## Verifying the stack

```bash
curl localhost:8000/healthz          # {"status": "ok"}
open http://localhost:5173           # dashboard
docker compose run --rm backend pytest
docker compose run --rm frontend npm run test -- --run
```

`backend` applies Alembic migrations on startup, so a fresh `postgres`
volume is brought up to date automatically — no manual migration step
needed for local dev.

## Tearing down

```bash
docker compose down            # stop containers, keep volumes (DB data persists)
docker compose down -v         # also remove volumes (fresh DB next time)
```

For how this same application is deployed to a real cluster, see
[Staging](staging.md), [Production](production.md), and the
[Helm Reference](helm.md).
