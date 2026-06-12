# Contributing

This project is built incrementally, one phase per pull request, against the
requirements and build order tracked in
[`docs/requirements.md`](docs/requirements.md). See
[`docs/dev_guide.md`](docs/dev_guide.md) for local setup.

## Workflow

Each phase corresponds to a GitHub issue (see the Build Order table in
`docs/requirements.md`) and follows the same cycle:

1. **Branch off `main`**: `git checkout -b feature/<phase-slug>`. Branch
   before any code or test changes — never commit phase work to `main`
   directly.
2. **Write tests first (RED)**: acceptance tests (in `tests/acceptance/`,
   with Given/When/Then docstrings referencing the FR IDs they cover), then
   unit tests, then integration tests. Confirm they fail before implementing.
3. **Implement until GREEN**: write the minimum code to pass the new tests.
4. **Run the full suite**: `pytest` (backend) and, from Phase 8 onward,
   `npm test` (frontend). Run `ruff check app tests` / `npm run lint`.
5. **Update docs**: `docs/requirements.md` status column for any FR/NFR the
   phase completes, plus any other affected docs.
6. **Update `CHANGELOG.md`**: add an entry under `[Unreleased]` describing
   what was added/changed, referencing the FR/NFR IDs.
7. **Commit** tests, implementation, and docs together.
8. **Push and open a PR**: `git push -u origin feature/<phase-slug>`, then
   `gh pr create` referencing `Closes #<issue>`.
9. **Review**: `/code-review` and `/security-review` are run on the PR
   before merge. Address any findings with follow-up commits on the same
   branch.
10. **Merge**: only after review passes and the owner approves.

## Commit messages

[Conventional Commits](https://www.conventionalcommits.org/) format:
`type(scope): short description`. Every commit must include:

```
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

## General rules

- Never push directly to `main`.
- Never amend or force-push commits that are part of an open PR unless
  explicitly approved — prefer new commits.
- Stage files by name (`git add <file>`), not `-A` or `.`.
- No secrets, credentials, or webhook URLs in committed files — use `.env`
  (gitignored), following `.env.example`.
- Keep each PR scoped to one phase, reviewable in roughly 30 minutes.
