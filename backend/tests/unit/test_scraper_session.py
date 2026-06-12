from unittest.mock import MagicMock, patch

from app.config import settings
from app.scraper.session import authenticated_page


def _mock_playwright(mock_page):
    mock_playwright = MagicMock()
    mock_browser = mock_playwright.chromium.launch.return_value
    mock_context = mock_browser.new_context.return_value
    mock_context.new_page.return_value = mock_page
    return mock_playwright, mock_browser


def test_authenticated_page_reuses_existing_storage_state(tmp_path):
    storage_state_path = tmp_path / "storage_state.json"
    storage_state_path.write_text("{}")

    mock_page = MagicMock()
    mock_playwright, mock_browser = _mock_playwright(mock_page)

    with patch("app.scraper.session.sync_playwright") as mock_sync_playwright, \
            patch("app.scraper.session.login") as mock_login:
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright

        with authenticated_page(storage_state_path=storage_state_path) as page:
            assert page is mock_page

    mock_browser.new_context.assert_called_once_with(storage_state=str(storage_state_path))
    mock_login.assert_not_called()
    mock_browser.close.assert_called_once()


def test_authenticated_page_logs_in_when_no_storage_state(tmp_path):
    storage_state_path = tmp_path / "storage_state.json"

    mock_page = MagicMock()
    mock_playwright, mock_browser = _mock_playwright(mock_page)

    with patch("app.scraper.session.sync_playwright") as mock_sync_playwright, \
            patch("app.scraper.session.login") as mock_login:
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright

        with authenticated_page(storage_state_path=storage_state_path) as page:
            assert page is mock_page

    mock_browser.new_context.assert_called_once_with(storage_state=None)
    mock_login.assert_called_once_with(
        mock_page,
        settings.limitless_username,
        settings.limitless_password,
        storage_state_path=storage_state_path,
    )
    mock_browser.close.assert_called_once()
