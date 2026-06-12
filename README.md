# Limitless Organizer Tracker

Tracks the status of a Limitless TCG organizer/organization application and
the platform's organizer onboarding activity over time.

- **Scraper** (Playwright, Python): logs into `play.limitlesstcg.com`, checks
  the organizer-application status on a schedule, resubmits 1-2x/day, and
  posts a Discord notification on each resubmission.
- **Tournament ingestion**: polls `https://play.limitlesstcg.com/api/tournaments`
  to build a history of organizer activity (first-tournament date per
  organizer, across all games).
- **Backend**: FastAPI + SQLAlchemy + Celery (worker/beat) + Postgres + Redis.
- **Frontend**: React + TypeScript dashboard (Vite).

## Requirements & MVPs

This project is built incrementally against a tracked set of business,
functional, and non-functional requirements, grouped into MVPs (MVP1:
application status & resubmission tracker, MVP2: organizer activity
analytics, MVP3: documentation & traceability). See
[`docs/requirements.md`](docs/requirements.md) for the full BR/FR/NFR list,
MVP acceptance criteria, and per-phase build order.

> Full setup/usage docs are in progress and will be expanded as each piece
> lands (see Phase 14 in `docs/requirements.md`).
