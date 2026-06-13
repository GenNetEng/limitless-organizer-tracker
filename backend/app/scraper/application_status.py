from playwright.sync_api import Page

from app.config import settings
from app.scraper.parsing import ApplicationStatusResult, parse_status_html
from app.scraper.selectors import APPLICATION_PATH_TEMPLATE


def check_application_status(page: Page) -> ApplicationStatusResult:
    """Check the organizer application status using an authenticated Page.

    The page's session must already be logged in (see app.scraper.browser).
    Parsing logic lives in app.scraper.parsing and is covered by unit tests
    against fixture HTML; this function is a thin, Playwright-dependent
    wrapper exercised by a live smoke test once real credentials are
    available (see app.scraper.selectors for the known-gap note).
    """
    path = APPLICATION_PATH_TEMPLATE.format(application_id=settings.limitless_application_id)
    page.goto(f"{settings.limitless_base_url}{path}")
    page.wait_for_load_state("networkidle")
    return parse_status_html(page.content())
