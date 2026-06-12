# Requirements & MVP Traceability

This document tracks the Business Requirements (BR), Functional Requirements
(FR), and Non-Functional Requirements (NFR) for the Limitless Organizer
Tracker, and maps them to the MVPs and build phases that implement them.

## Business Requirements (BR)

- **BR1**: Provide visibility into organizer-application throughput
  (status-check history, outcomes) that Limitless does not report on.
- **BR2**: Maximize approval likelihood by automating frequent, scheduled
  resubmission per Limitless's LIFO-favoring review process, with a Discord
  post per resubmission (matching the existing manual habit).
- **BR3**: Provide visibility into platform-wide organizer growth — how many
  new organizers (across all games) become active each week/month, based on
  each organizer's first tournament date.

## Functional Requirements (FR)

| ID | Requirement | Serves | Status / Phase |
|----|-------------|--------|-----------------|
| FR1 | Log into play.limitlesstcg.com via Playwright using stored username/password, persisting session for reuse | BR1, BR2 | Pending — Phase 5 (`app/scraper/browser.py`) |
| FR2 | Check organizer/organization application status on a configurable schedule; record each check as a timestamped datapoint (status enum + raw text) | BR1 | Parsing done (Phase 4); login + scheduled task pending — Phase 5/6 |
| FR3 | Resubmit the organization application 1-2x/day on a configurable schedule | BR2 | Pending — Phase 5 (`app/scraper/resubmit.py`) |
| FR4 | Post a Discord notification when a resubmission occurs | BR2 | Pending — Phase 5 (`app/notifications/discord.py`) |
| FR5 | Log each resubmission as a timestamped datapoint (success flag, discord-notified flag) | BR1, BR2 | Model done (Phase 2); persistence wiring pending — Phase 5/6 |
| FR6 | Ingest tournament data from `GET /api/tournaments` across all games | BR3 | **Done — Phase 3** |
| FR7 | Determine each organizer's ID and first-tournament date per game from ingested data | BR3 | **Done — Phase 3** (`OrganizerActivity`) |
| FR8 | Compute counts of newly-active organizers per week/month, overall and filterable by game | BR3 | Pending — Phase 11 |
| FR9 | Dashboard displays application status-check history (timeline) | BR1 | Pending — Phase 8 |
| FR10 | Dashboard displays resubmission log | BR1, BR2 | Pending — Phase 8 |
| FR11 | Dashboard displays newly-active-organizer counts per week/month, filterable by game | BR3 | Pending — Phase 12 |

## Non-Functional Requirements (NFR)

| ID | Requirement | Status |
|----|-------------|--------|
| NFR1 | TDD (red→green→refactor) for all code, with unit/integration/acceptance coverage | **Established — Phases 1-4** (18 tests, ongoing each phase) |
| NFR2 | API-first backend, written in Python (FastAPI), decoupled from frontend | **Established — Phases 1-2** |
| NFR3 | Always-running architecture via Celery worker + beat scheduler | Pending — Phase 6 (MVP1 tasks), Phase 10 (MVP2 task) |
| NFR4 | Monorepo, public on GitHub, with GitHub Actions CI | **Established — Phase 1** |
| NFR5 | Scraper logic decoupled from live site; tested via fixture HTML, no live calls in CI (`@pytest.mark.live` reserved for future) | **Established — Phase 4**, continues in Phase 5 |
| NFR6 | Configuration via environment variables (`.env`), no secrets committed | **Established — Phases 1-2** |

## MVP Breakdown

### MVP1 — Application Status & Resubmission Tracker
Serves BR1, BR2 / FR1-5, FR9-10, partial NFR3. Phases 5-9.

**Acceptance**: `docker compose up` runs backend + celery worker/beat +
postgres/redis + frontend; status checks and resubmissions are logged on
schedule; Discord notified on resubmission; dashboard shows status timeline
and resubmission log.

### MVP2 — Organizer Activity Analytics
Serves BR3 / FR6-8, FR11, remaining NFR3. Phases 10-13.

**Acceptance**: tournament ingestion runs on schedule; `/api/organizers/activity`
returns correct weekly/monthly counts; dashboard chart renders, filterable by
game.

### MVP3 — Documentation & Traceability
Project hygiene / final NFR coverage. Phase 14.

**Acceptance**: README fully documents setup/env/scheduling/scraper-selector
caveat; this traceability table shows all FR/NFR as Done with final phase
references.

## Build Order

Tracked via [GitHub milestones](https://github.com/GenNetEng/limitless-organizer-tracker/milestones)
(one per MVP) and one issue per phase.

| Phase | Description | MVP | Issue |
|-------|-------------|-----|-------|
| 1 | Repo scaffold + CI | — | — |
| 2 | Backend foundation (config, FastAPI healthz, models, Alembic) | — | — |
| 3 | Tournament ingestion + organizer activity aggregation | MVP2 | — |
| 4 | Application-status scraper (fixture-based HTML parsing) | MVP1 | — |
| 4.5 | Requirements traceability doc (this file) | — | [#1](https://github.com/GenNetEng/limitless-organizer-tracker/pull/1) |
| 5 | Resubmit scraper + Discord notifier | MVP1 | [#2](https://github.com/GenNetEng/limitless-organizer-tracker/issues/2) |
| 6 | Celery app + beat schedule for status-check/resubmit tasks | MVP1 | [#3](https://github.com/GenNetEng/limitless-organizer-tracker/issues/3) |
| 7 | FastAPI routers: status history, resubmissions | MVP1 | [#4](https://github.com/GenNetEng/limitless-organizer-tracker/issues/4) |
| 8 | Frontend scaffold + MVP1 dashboard (status timeline, resubmission log) | MVP1 | [#5](https://github.com/GenNetEng/limitless-organizer-tracker/issues/5) |
| 9 | MVP1 docker-compose verification (acceptance checkpoint) | MVP1 | [#6](https://github.com/GenNetEng/limitless-organizer-tracker/issues/6) |
| 10 | Tournament ingestion Celery task + beat schedule | MVP2 | [#7](https://github.com/GenNetEng/limitless-organizer-tracker/issues/7) |
| 11 | FastAPI routers: organizer activity, games | MVP2 | [#8](https://github.com/GenNetEng/limitless-organizer-tracker/issues/8) |
| 12 | Frontend organizer-activity chart | MVP2 | [#9](https://github.com/GenNetEng/limitless-organizer-tracker/issues/9) |
| 13 | MVP2 docker-compose verification (acceptance checkpoint) | MVP2 | [#10](https://github.com/GenNetEng/limitless-organizer-tracker/issues/10) |
| 14 | README + traceability finalization | MVP3 | [#11](https://github.com/GenNetEng/limitless-organizer-tracker/issues/11) |
