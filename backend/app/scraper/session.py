import logging
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

from app.config import settings
from app.db.session import task_session
from app.events import log_event
from app.scraper.browser import DEFAULT_STORAGE_STATE_PATH, login
from app.scraper.selectors import APPLY_PATH, LOGIN_PATH

logger = logging.getLogger(__name__)


@dataclass
class AuthenticatedPageContext:
    page: Page
    session_refreshed: bool


def _is_login_page(page: Page) -> bool:
    return LOGIN_PATH in page.url


@contextmanager
def authenticated_page(
    storage_state_path: Path | str = DEFAULT_STORAGE_STATE_PATH,
) -> Iterator[AuthenticatedPageContext]:
    """Yield an AuthenticatedPageContext with the page and whether the session was refreshed.

    Reuses `storage_state_path` if it exists and the session is still valid;
    otherwise logs in with the configured credentials and persists the
    resulting session for reuse by later runs.

    When a stored session is found, navigates to an auth-required page to
    validate it.  If the server redirects to the login page, the stale
    storage state is deleted and a fresh login is performed.
    """
    storage_state_path = Path(storage_state_path)
    state = str(storage_state_path) if storage_state_path.exists() else None
    session_refreshed = False

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
            else:
                try:
                    page.goto(
                        f"{settings.limitless_base_url}{APPLY_PATH}",
                        timeout=settings.session_validation_timeout_ms,
                    )
                    expired = _is_login_page(page)
                except PlaywrightTimeoutError:
                    logger.warning(
                        "Session validation timed out (%d ms) — treating as expired",
                        settings.session_validation_timeout_ms,
                    )
                    expired = True

                if expired:
                    logger.warning("Stored session expired — re-authenticating")
                    storage_state_path.unlink(missing_ok=True)
                    login(
                        page,
                        settings.limitless_username,
                        settings.limitless_password,
                        storage_state_path=storage_state_path,
                    )
                    session_refreshed = True

            if session_refreshed:
                try:
                    with task_session() as db_session:
                        log_event(
                            session=db_session,
                            event_type="scraper.session_refreshed",
                            source="session",
                            message="Expired session detected and refreshed",
                            severity="WARNING",
                        )
                        db_session.commit()
                except Exception:
                    logger.debug("Failed to log session refresh event", exc_info=True)

            yield AuthenticatedPageContext(page=page, session_refreshed=session_refreshed)
        finally:
            browser.close()
