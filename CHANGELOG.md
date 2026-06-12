# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Monorepo scaffold: `.gitignore`, `.env.example`, `docker-compose.yml`
  (postgres, redis, backend, celery-worker, celery-beat, frontend),
  `backend/Dockerfile`, `frontend/Dockerfile`, `backend/pyproject.toml`,
  and GitHub Actions CI workflow (`.github/workflows/ci.yml`) covering
  backend lint/test, frontend lint/test, and docker builds.
