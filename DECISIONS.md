# Technical Decisions

A log of non-trivial technical decisions for this project: new dependencies,
choices between libraries/patterns, file/module structure, API/auth design,
repo/CI configuration, etc. Every entry was presented to the owner with
alternatives before implementation, per [`CONTRIBUTING.md`](CONTRIBUTING.md).

Newest entries first.

## Template

```
## YYYY-MM-DD: <short title>

**Decision**: <what was chosen>

**Alternatives considered**: <other options and their tradeoffs>

**Why**: <reasoning / owner's stated rationale>
```

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
