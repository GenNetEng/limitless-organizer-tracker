from unittest.mock import MagicMock

import pytest

from app.config import settings
from app.scraper.browser import LoginFailed, login
from app.scraper.selectors import (
    LOGIN_PASSWORD_SELECTOR,
    LOGIN_PATH,
    LOGIN_SUBMIT_SELECTOR,
    LOGIN_USERNAME_SELECTOR,
)


def test_login_fills_form_and_persists_storage_state(tmp_path):
    page = MagicMock()
    page.url = f"{settings.limitless_base_url}/dashboard"
    storage_state_path = tmp_path / "storage_state.json"

    login(page, "alice", "s3cret", storage_state_path=storage_state_path)

    page.goto.assert_called_once_with(f"{settings.limitless_base_url}{LOGIN_PATH}")
    page.fill.assert_any_call(LOGIN_USERNAME_SELECTOR, "alice")
    page.fill.assert_any_call(LOGIN_PASSWORD_SELECTOR, "s3cret")
    page.click.assert_called_once_with(LOGIN_SUBMIT_SELECTOR)
    page.wait_for_load_state.assert_called_once_with("networkidle")
    page.context.storage_state.assert_called_once_with(path=str(storage_state_path))


def test_login_raises_login_failed_when_still_on_login_page(tmp_path):
    page = MagicMock()
    page.url = f"{settings.limitless_base_url}{LOGIN_PATH}"
    storage_state_path = tmp_path / "storage_state.json"

    with pytest.raises(LoginFailed):
        login(page, "alice", "wrong", storage_state_path=storage_state_path)

    page.context.storage_state.assert_not_called()
