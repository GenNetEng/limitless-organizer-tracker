#!/usr/bin/env bash
set -euo pipefail

# First-time (or post-rebuild) dev container setup.
# Run this after "Reopen in Container" or losing auth state.
# Idempotent — skips any step that's already satisfied.

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }

echo "Limitless Organizer Tracker — dev environment setup"
echo "----------------------------------------------------"

# --- GitHub CLI ---
if gh auth status &>/dev/null; then
  ok "GitHub CLI already authenticated"
else
  warn "GitHub CLI not authenticated — launching gh auth login"
  gh auth login
fi

# --- Claude Code ---
CLAUDE_CREDS="$HOME/.claude/.credentials.json"
if [ -s "$CLAUDE_CREDS" ]; then
  ok "Claude Code already authenticated"
else
  warn "Claude Code not authenticated — launching claude auth login"
  if ! command -v claude &>/dev/null; then
    warn "claude CLI not found in PATH — open VS Code and sign in via the Claude Code extension instead"
  else
    claude auth login
  fi
fi

# --- .env ---
if [ ! -f /workspace/.env ]; then
  if [ -f /workspace/.env.example ]; then
    cp /workspace/.env.example /workspace/.env
    warn ".env created from .env.example — edit it with real credentials before the stack will work end-to-end"
  fi
else
  ok ".env already exists"
fi

echo ""
echo "Done. Next steps:"
echo "  cd /workspace/backend && pytest         # run the backend test suite"
echo "  cd /workspace/backend && ruff check app tests"
echo "  docker compose ps                       # postgres/redis/celery/frontend run as sibling containers"
