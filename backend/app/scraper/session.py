from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from app.config import settings
from app.scraper.browser import DEFAULT_STORAGE_STATE_PATH, login


@contextmanager
def authenticated_page(
    storage_state_path: Path | str = DEFAULT_STORAGE_STATE_PATH,
) -> Iterator[Page]:
    """Yield an authenticated Page, logging in if no session is persisted yet.

    Reuses `storage_state_path` (see app.scraper.browser.login) if it exists;
    otherwise logs in with the configured credentials and persists the
    resulting session for reuse by later runs.
    """
    storage_state_path = Path(storage_state_path)
    state = str(storage_state_path) if storage_state_path.exists() else None

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            context = browser.new_context(storage_state=state)
            page = context.new_page()

            if state is None:
                login(
                    page,
                    settings.limitless_username,
                    settings.limitless_password,
                    storage_state_path=storage_state_path,
                )

            yield page
        finally:
            browser.close()
