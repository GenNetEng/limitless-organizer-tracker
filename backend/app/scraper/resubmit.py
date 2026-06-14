from playwright.sync_api import Page

from app.config import settings
from app.scraper.parsing import parse_resubmit_result
from app.scraper.selectors import (
    APPLICATION_PATH_TEMPLATE,
    RESUBMIT_BUTTON_SELECTOR,
    RESUBMIT_CONTINUE_BUTTON_SELECTOR,
)


def resubmit_application(page: Page) -> bool:
    """Resubmit the organization application using an authenticated Page.

    The page's session must already be logged in (see app.scraper.browser).
    Advances the on-page resubmit wizard from `.page1` to `.page2` (a
    client-side reveal with no server effect) before clicking the actual
    "Resubmit" button. Returns whether the resubmission succeeded, based on
    the resulting page state parsed by app.scraper.parsing.parse_resubmit_result.
    """
    path = APPLICATION_PATH_TEMPLATE.format(application_id=settings.limitless_application_id)
    page.goto(f"{settings.limitless_base_url}{path}")
    page.click(RESUBMIT_CONTINUE_BUTTON_SELECTOR)
    page.click(RESUBMIT_BUTTON_SELECTOR)
    page.wait_for_load_state("networkidle")
    return parse_resubmit_result(page.content())
