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
