"""Acceptance test: scraper login (FR1).

Given stored username/password credentials and a browser page,
When the scraper logs in to play.limitlesstcg.com,
Then the session is authenticated via the password login form and the
session state is persisted to disk for reuse by later tasks.
"""

from unittest.mock import MagicMock

from app.config import settings
from app.scraper.browser import login
from app.scraper.selectors import LOGIN_PATH


def test_login_authenticates_and_persists_session_for_reuse(tmp_path):
    # Given stored credentials and a browser page
    page = MagicMock()
    storage_state_path = tmp_path / "storage_state.json"

    # When the scraper logs in
    login(page, "alice", "s3cret", storage_state_path=storage_state_path)

    # Then the page navigated to the login form and the session was persisted
    page.goto.assert_called_once_with(f"{settings.limitless_base_url}{LOGIN_PATH}")
    page.context.storage_state.assert_called_once_with(path=str(storage_state_path))
