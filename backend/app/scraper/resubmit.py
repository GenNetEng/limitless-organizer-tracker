from playwright.sync_api import Page

from app.config import settings
from app.scraper.parsing import parse_resubmit_result
from app.scraper.selectors import ORG_SETTINGS_PATH, RESUBMIT_BUTTON_SELECTOR


def resubmit_application(page: Page) -> bool:
    """Resubmit the organization application using an authenticated Page.

    The page's session must already be logged in (see app.scraper.browser).
    Returns whether the resubmission succeeded, based on the resulting page
    state parsed by app.scraper.parsing.parse_resubmit_result.
    """
    page.goto(f"{settings.limitless_base_url}{ORG_SETTINGS_PATH}")
    page.click(RESUBMIT_BUTTON_SELECTOR)
    page.wait_for_load_state("networkidle")
    return parse_resubmit_result(page.content())
