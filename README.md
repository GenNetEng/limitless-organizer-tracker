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

> Full setup/usage docs are in progress — see the project plan for the build
> order. This section will be expanded as each piece lands.
