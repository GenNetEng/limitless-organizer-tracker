from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from app.config import settings
from app.scraper.parsing import parse_resubmit_result
from app.scraper.selectors import (
    APPLICATION_PATH_TEMPLATE,
    RESUBMIT_BUTTON_SELECTOR,
    RESUBMIT_CONTINUE_BUTTON_SELECTOR,
    RESUBMIT_PAGE2_SELECTOR,
    RESUBMIT_RESULT_SELECTOR,
)


def resubmit_application(page: Page) -> bool:
    """Resubmit the organization application using an authenticated Page.

    The page's session must already be logged in (see app.scraper.browser).
    Advances the on-page resubmit wizard from `.page1` to `.page2` (a
    client-side reveal with no server effect) before clicking the actual
    "Resubmit" button.

    Waits explicitly for .page2 to become visible after clicking Continue so
    that the JS transition completes before the Submit click is dispatched —
    without this wait, the click fires before the module script attaches its
    handler and page2 is never revealed. Then waits for .page3 to become
    visible rather than relying on networkidle, which fires after any
    post-submit page reload and misses the success state.
    """
    path = APPLICATION_PATH_TEMPLATE.format(application_id=settings.limitless_application_id)
    page.goto(f"{settings.limitless_base_url}{path}")
    page.click(RESUBMIT_CONTINUE_BUTTON_SELECTOR)
    page.wait_for_selector(RESUBMIT_PAGE2_SELECTOR, state="visible")
    page.click(RESUBMIT_BUTTON_SELECTOR)
    try:
        page.wait_for_selector(RESUBMIT_RESULT_SELECTOR, state="visible", timeout=10000)
    except PlaywrightTimeoutError:
        return False
    return parse_resubmit_result(page.content())
