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
