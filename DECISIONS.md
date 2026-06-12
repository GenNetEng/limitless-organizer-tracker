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
