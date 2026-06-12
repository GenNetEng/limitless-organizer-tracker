from pathlib import Path
from unittest.mock import MagicMock

from app.config import settings
from app.scraper.resubmit import resubmit_application
from app.scraper.selectors import ORG_SETTINGS_PATH, RESUBMIT_BUTTON_SELECTOR

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "html"


def test_resubmit_application_returns_true_on_success():
    page = MagicMock()
    page.content.return_value = (FIXTURE_DIR / "org_settings_resubmit_success.html").read_text()

    result = resubmit_application(page)

    page.goto.assert_called_once_with(f"{settings.limitless_base_url}{ORG_SETTINGS_PATH}")
    page.click.assert_called_once_with(RESUBMIT_BUTTON_SELECTOR)
    page.wait_for_load_state.assert_called_once_with("networkidle")
    assert result is True


def test_resubmit_application_returns_false_on_failure():
    page = MagicMock()
    page.content.return_value = (FIXTURE_DIR / "org_settings_resubmit_failure.html").read_text()

    result = resubmit_application(page)

    assert result is False
