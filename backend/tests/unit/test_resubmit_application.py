from pathlib import Path
from unittest.mock import MagicMock, call

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from app.config import settings
from app.scraper.resubmit import resubmit_application
from app.scraper.selectors import (
    APPLICATION_PATH_TEMPLATE,
    RESUBMIT_BUTTON_SELECTOR,
    RESUBMIT_CONTINUE_BUTTON_SELECTOR,
    RESUBMIT_PAGE2_SELECTOR,
    RESUBMIT_RESULT_SELECTOR,
)

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "html"


def test_resubmit_application_returns_success():
    page = MagicMock()
    page.content.return_value = (FIXTURE_DIR / "application_resubmit_success.html").read_text()

    result = resubmit_application(page)

    path = APPLICATION_PATH_TEMPLATE.format(application_id=settings.limitless_application_id)
    page.goto.assert_called_once_with(f"{settings.limitless_base_url}{path}")
    page.click.assert_has_calls(
        [call(RESUBMIT_CONTINUE_BUTTON_SELECTOR, timeout=10000), call(RESUBMIT_BUTTON_SELECTOR, timeout=10000)]
    )
    page.wait_for_selector.assert_any_call(
        RESUBMIT_PAGE2_SELECTOR, state="visible", timeout=10000
    )
    page.wait_for_selector.assert_any_call(
        RESUBMIT_RESULT_SELECTOR, state="visible", timeout=10000
    )
    assert result.success is True
    assert result.failure_stage is None


def test_resubmit_application_captures_html_when_page2_never_appears():
    page = MagicMock()
    page.content.return_value = "<html>stuck on page1</html>"
    page.wait_for_selector.side_effect = [PlaywrightTimeoutError("timeout")]

    result = resubmit_application(page)

    assert result.success is False
    assert result.failure_stage == "page2_not_visible"
    assert "stuck on page1" in result.page_html


def test_resubmit_application_captures_html_when_page3_never_appears():
    page = MagicMock()
    page.content.return_value = "<html>stuck on page2</html>"
    page.wait_for_selector.side_effect = [None, PlaywrightTimeoutError("timeout")]

    result = resubmit_application(page)

    assert result.success is False
    assert result.failure_stage == "result_page_not_visible"
    assert "stuck on page2" in result.page_html


def test_resubmit_application_captures_html_when_continue_button_missing():
    page = MagicMock()
    page.content.return_value = "<html>no button</html>"
    page.click.side_effect = PlaywrightTimeoutError("timeout")

    result = resubmit_application(page)

    assert result.success is False
    assert result.failure_stage == "continue_button_not_found"
    assert "no button" in result.page_html
