from dataclasses import dataclass

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from app.config import settings
from app.scraper.selectors import (
    APPLICATION_PATH_TEMPLATE,
    RESUBMIT_CONTINUE_BUTTON_SELECTOR,
    RESUBMIT_PAGE2_SELECTOR,
)


@dataclass
class ResubmitResult:
    success: bool
    failure_stage: str | None = None
    page_html: str | None = None
    server_response: dict | None = None


def resubmit_application(page: Page) -> ResubmitResult:
    """Resubmit the organization application using an authenticated Page.

    Navigates to the application page, scrapes the form data (name,
    discord, message, quiz answers), then POSTs the JSON directly via
    Playwright's request context — bypassing the page's JS click
    handler which doesn't fire reliably in headless Chromium.
    """
    app_id = settings.limitless_application_id
    path = APPLICATION_PATH_TEMPLATE.format(application_id=app_id)
    url = f"{settings.limitless_base_url}{path}"

    page.goto(url)

    try:
        page.wait_for_selector(RESUBMIT_CONTINUE_BUTTON_SELECTOR, state="visible", timeout=10000)
    except PlaywrightTimeoutError:
        return ResubmitResult(
            success=False,
            failure_stage="page_load_failed",
            page_html=page.content()[:20000],
        )

    try:
        page.evaluate(f"document.querySelector('{RESUBMIT_CONTINUE_BUTTON_SELECTOR}').click()")
        page.wait_for_selector(RESUBMIT_PAGE2_SELECTOR, state="visible", timeout=10000)
    except (PlaywrightTimeoutError, Exception):
        return ResubmitResult(
            success=False,
            failure_stage="page2_not_visible",
            page_html=page.content()[:20000],
        )

    form_data = page.evaluate("""() => {
        const name = document.querySelector('.name')?.value || '';
        const discord = document.querySelector('.discord')?.value || '';
        const message = document.querySelector('.message')?.value || '';
        const answers = {};
        document.querySelectorAll('.question').forEach(q => {
            const qid = q.getAttribute('data-qid');
            if (qid) answers[qid] = q.value || '';
        });
        return { name, discord, message, answers };
    }""")

    if not form_data or not form_data.get("name"):
        return ResubmitResult(
            success=False,
            failure_stage="form_data_extraction_failed",
            page_html=page.content()[:20000],
        )

    try:
        body = page.evaluate("""async (data) => {
            const resp = await fetch(window.location.href, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data),
            });
            return await resp.json();
        }""", form_data)
    except Exception as exc:
        return ResubmitResult(
            success=False,
            failure_stage="post_request_failed",
            server_response={"error": str(exc)},
        )

    ok = body.get("ok", False) or body.get("status") == "ok"
    return ResubmitResult(
        success=ok,
        server_response=body,
        failure_stage=None if ok else "server_rejected",
    )
