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


def test_resubmit_application_returns_true_on_success():
    page = MagicMock()
    page.content.return_value = (FIXTURE_DIR / "application_resubmit_success.html").read_text()

    result = resubmit_application(page)

    path = APPLICATION_PATH_TEMPLATE.format(application_id=settings.limitless_application_id)
    page.goto.assert_called_once_with(f"{settings.limitless_base_url}{path}")
    page.click.assert_has_calls(
        [call(RESUBMIT_CONTINUE_BUTTON_SELECTOR), call(RESUBMIT_BUTTON_SELECTOR)]
    )
    page.wait_for_selector.assert_any_call(
        RESUBMIT_PAGE2_SELECTOR, state="visible", timeout=10000
    )
    page.wait_for_selector.assert_any_call(
        RESUBMIT_RESULT_SELECTOR, state="visible", timeout=10000
    )
    page.wait_for_load_state.assert_not_called()
    assert result is True


def test_resubmit_application_returns_false_when_page2_never_appears():
    page = MagicMock()
    page.wait_for_selector.side_effect = [PlaywrightTimeoutError("timeout")]

    result = resubmit_application(page)

    assert result is False
    page.click.assert_called_once_with(RESUBMIT_CONTINUE_BUTTON_SELECTOR)
    page.content.assert_not_called()


def test_resubmit_application_returns_false_when_page3_never_appears():
    page = MagicMock()
    # First call (page2 visible): succeeds; second call (page3 visible): times out
    page.wait_for_selector.side_effect = [None, PlaywrightTimeoutError("timeout")]

    result = resubmit_application(page)

    assert result is False
    page.content.assert_not_called()
