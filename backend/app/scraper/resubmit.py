from dataclasses import dataclass

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


@dataclass
class ResubmitResult:
    success: bool
    failure_stage: str | None = None
    page_html: str | None = None
    network_log: list | None = None


def resubmit_application(page: Page) -> ResubmitResult:
    """Resubmit the organization application using an authenticated Page.

    Returns a ResubmitResult with success status and, on failure, the
    stage that failed and a snapshot of the page HTML for diagnosis.
    Captures network responses from the resubmit POST for debugging.
    """
    network_responses: list[dict] = []

    def _capture_response(response):
        if "/user/application" in response.url or "/api/" in response.url:
            try:
                body = response.text()[:2000]
            except Exception:
                body = "(could not read body)"
            network_responses.append({
                "url": response.url,
                "status": response.status,
                "body": body,
            })

    page.on("response", _capture_response)

    path = APPLICATION_PATH_TEMPLATE.format(application_id=settings.limitless_application_id)
    page.goto(f"{settings.limitless_base_url}{path}")

    try:
        page.click(RESUBMIT_CONTINUE_BUTTON_SELECTOR, timeout=10000)
    except PlaywrightTimeoutError:
        return ResubmitResult(
            success=False,
            failure_stage="continue_button_not_found",
            page_html=page.content()[:20000],
            network_log=network_responses,
        )

    try:
        page.wait_for_selector(RESUBMIT_PAGE2_SELECTOR, state="visible", timeout=10000)
    except PlaywrightTimeoutError:
        return ResubmitResult(
            success=False,
            failure_stage="page2_not_visible",
            page_html=page.content()[:20000],
            network_log=network_responses,
        )

    try:
        page.click(RESUBMIT_BUTTON_SELECTOR, timeout=10000)
    except PlaywrightTimeoutError:
        return ResubmitResult(
            success=False,
            failure_stage="submit_button_not_found",
            page_html=page.content()[:20000],
            network_log=network_responses,
        )

    try:
        page.wait_for_selector(RESUBMIT_RESULT_SELECTOR, state="visible", timeout=15000)
    except PlaywrightTimeoutError:
        return ResubmitResult(
            success=False,
            failure_stage="result_page_not_visible",
            page_html=page.content()[:20000],
            network_log=network_responses,
        )

    return ResubmitResult(success=parse_resubmit_result(page.content()))
