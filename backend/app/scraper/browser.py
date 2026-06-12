from pathlib import Path

from playwright.sync_api import Page

from app.config import settings
from app.scraper.selectors import (
    LOGIN_PASSWORD_SELECTOR,
    LOGIN_PATH,
    LOGIN_SUBMIT_SELECTOR,
    LOGIN_USERNAME_SELECTOR,
)

DEFAULT_STORAGE_STATE_PATH = Path("storage_state.json")


def login(
    page: Page,
    username: str,
    password: str,
    storage_state_path: Path | str = DEFAULT_STORAGE_STATE_PATH,
) -> None:
    """Log into play.limitlesstcg.com via the password login form.

    Persists the resulting session to `storage_state_path` so it can be
    reused by later scraper runs without logging in again.
    """
    page.goto(f"{settings.limitless_base_url}{LOGIN_PATH}")
    page.fill(LOGIN_USERNAME_SELECTOR, username)
    page.fill(LOGIN_PASSWORD_SELECTOR, password)
    page.click(LOGIN_SUBMIT_SELECTOR)
    page.wait_for_load_state("networkidle")
    page.context.storage_state(path=str(storage_state_path))
