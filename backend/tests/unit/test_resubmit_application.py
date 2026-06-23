from pathlib import Path
from unittest.mock import MagicMock

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from app.scraper.resubmit import resubmit_application

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "html"


def _make_page(content_html=None):
    page = MagicMock()
    page.on = MagicMock()
    if content_html:
        page.content.return_value = content_html
    return page


def test_resubmit_application_returns_success():
    html = (FIXTURE_DIR / "application_resubmit_success.html").read_text()
    page = _make_page(html)

    result = resubmit_application(page)

    assert result.success is True
    assert result.failure_stage is None
    assert page.evaluate.call_count == 2


def test_resubmit_application_captures_html_when_continue_button_missing():
    page = _make_page("<html>no button</html>")
    page.wait_for_selector.side_effect = PlaywrightTimeoutError("timeout")

    result = resubmit_application(page)

    assert result.success is False
    assert result.failure_stage == "continue_button_not_found"
    assert "no button" in result.page_html


def test_resubmit_application_captures_html_when_page2_never_appears():
    page = _make_page("<html>stuck on page1</html>")
    page.wait_for_selector.side_effect = [None, PlaywrightTimeoutError("timeout")]

    result = resubmit_application(page)

    assert result.success is False
    assert result.failure_stage == "page2_not_visible"
    assert "stuck on page1" in result.page_html


def test_resubmit_application_captures_html_when_submit_click_fails():
    page = _make_page("<html>page2 visible</html>")
    page.evaluate.side_effect = [None, Exception("element not found")]

    result = resubmit_application(page)

    assert result.success is False
    assert result.failure_stage == "submit_button_not_found"


def test_resubmit_application_captures_html_when_page3_never_appears():
    page = _make_page("<html>stuck after submit</html>")
    page.wait_for_selector.side_effect = [None, None, PlaywrightTimeoutError("timeout")]

    result = resubmit_application(page)

    assert result.success is False
    assert result.failure_stage == "result_page_not_visible"
    assert "stuck after submit" in result.page_html
    assert result.network_log is not None
