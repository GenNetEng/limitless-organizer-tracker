from unittest.mock import MagicMock, patch

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from app.config import settings
from app.scraper.selectors import APPLY_PATH, LOGIN_PATH
from app.scraper.session import AuthenticatedPageContext, authenticated_page


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

        with authenticated_page(storage_state_path=storage_state_path) as ctx:
            assert ctx.page is mock_page

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

        with authenticated_page(storage_state_path=storage_state_path) as ctx:
            assert ctx.page is mock_page

    mock_browser.new_context.assert_called_once_with(storage_state=None)
    mock_login.assert_called_once_with(
        mock_page,
        settings.limitless_username,
        settings.limitless_password,
        storage_state_path=storage_state_path,
    )
    mock_browser.close.assert_called_once()


def test_authenticated_page_closes_browser_even_if_login_fails(tmp_path):
    storage_state_path = tmp_path / "storage_state.json"

    mock_page = MagicMock()
    mock_playwright, mock_browser = _mock_playwright(mock_page)

    with patch("app.scraper.session.sync_playwright") as mock_sync_playwright, \
            patch("app.scraper.session.login", side_effect=RuntimeError("login failed")):
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright

        with pytest.raises(RuntimeError, match="login failed"):
            with authenticated_page(storage_state_path=storage_state_path):
                pass

    mock_browser.close.assert_called_once()


def test_authenticated_page_validates_stored_session_and_skips_login_when_valid(tmp_path):
    """When the stored session is valid (no redirect to login), login is not called."""
    storage_state_path = tmp_path / "storage_state.json"
    storage_state_path.write_text("{}")

    mock_page = MagicMock()
    mock_page.url = f"{settings.limitless_base_url}{APPLY_PATH}"
    mock_playwright, mock_browser = _mock_playwright(mock_page)

    with patch("app.scraper.session.sync_playwright") as mock_sync_playwright, \
            patch("app.scraper.session.login") as mock_login:
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright

        with authenticated_page(storage_state_path=storage_state_path) as ctx:
            assert ctx.page is mock_page

    mock_page.goto.assert_called_once()
    mock_login.assert_not_called()
    assert storage_state_path.exists()


def test_authenticated_page_detects_expired_session_and_relogs_in(tmp_path):
    """When stored session is expired (redirected to login), storage_state is deleted and login is called."""
    storage_state_path = tmp_path / "storage_state.json"
    storage_state_path.write_text("{}")

    mock_page = MagicMock()
    mock_page.url = f"{settings.limitless_base_url}{LOGIN_PATH}?next=/user/apply"
    mock_playwright, mock_browser = _mock_playwright(mock_page)

    with patch("app.scraper.session.sync_playwright") as mock_sync_playwright, \
            patch("app.scraper.session.login") as mock_login:
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright

        with authenticated_page(storage_state_path=storage_state_path) as ctx:
            assert ctx.page is mock_page

    assert not storage_state_path.exists()
    mock_login.assert_called_once_with(
        mock_page,
        settings.limitless_username,
        settings.limitless_password,
        storage_state_path=storage_state_path,
    )


# --- Phase 31: AuthenticatedPageContext tests ---


def test_authenticated_page_yields_context_with_session_refreshed_false_when_valid(tmp_path):
    """When the stored session is valid, yields AuthenticatedPageContext with session_refreshed=False."""
    storage_state_path = tmp_path / "storage_state.json"
    storage_state_path.write_text("{}")

    mock_page = MagicMock()
    mock_page.url = f"{settings.limitless_base_url}{APPLY_PATH}"
    mock_playwright, mock_browser = _mock_playwright(mock_page)

    with patch("app.scraper.session.sync_playwright") as mock_sync_playwright, \
            patch("app.scraper.session.login"):
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright

        with authenticated_page(storage_state_path=storage_state_path) as ctx:
            assert isinstance(ctx, AuthenticatedPageContext)
            assert ctx.page is mock_page
            assert ctx.session_refreshed is False


def test_authenticated_page_yields_context_with_session_refreshed_true_when_expired(tmp_path):
    """When the stored session is expired and re-login occurs, yields session_refreshed=True."""
    storage_state_path = tmp_path / "storage_state.json"
    storage_state_path.write_text("{}")

    mock_page = MagicMock()
    mock_page.url = f"{settings.limitless_base_url}{LOGIN_PATH}?next=/user/apply"
    mock_playwright, mock_browser = _mock_playwright(mock_page)

    with patch("app.scraper.session.sync_playwright") as mock_sync_playwright, \
            patch("app.scraper.session.login"):
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright

        with authenticated_page(storage_state_path=storage_state_path) as ctx:
            assert isinstance(ctx, AuthenticatedPageContext)
            assert ctx.page is mock_page
            assert ctx.session_refreshed is True


def test_authenticated_page_yields_context_with_session_refreshed_false_on_fresh_login(tmp_path):
    """When no storage state exists (fresh login), yields session_refreshed=False."""
    storage_state_path = tmp_path / "storage_state.json"

    mock_page = MagicMock()
    mock_playwright, mock_browser = _mock_playwright(mock_page)

    with patch("app.scraper.session.sync_playwright") as mock_sync_playwright, \
            patch("app.scraper.session.login"):
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright

        with authenticated_page(storage_state_path=storage_state_path) as ctx:
            assert isinstance(ctx, AuthenticatedPageContext)
            assert ctx.page is mock_page
            assert ctx.session_refreshed is False


# --- Phase 32: Configurable session validation timeout tests ---


def test_session_validation_timeout_ms_setting_exists():
    """Settings has session_validation_timeout_ms with default 10000."""
    assert hasattr(settings, "session_validation_timeout_ms")
    assert settings.session_validation_timeout_ms == 10000


def test_authenticated_page_passes_timeout_to_goto(tmp_path):
    """page.goto() is called with timeout=settings.session_validation_timeout_ms."""
    storage_state_path = tmp_path / "storage_state.json"
    storage_state_path.write_text("{}")

    mock_page = MagicMock()
    mock_page.url = f"{settings.limitless_base_url}{APPLY_PATH}"
    mock_playwright, mock_browser = _mock_playwright(mock_page)

    with patch("app.scraper.session.sync_playwright") as mock_sync_playwright, \
            patch("app.scraper.session.login"):
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright

        with authenticated_page(storage_state_path=storage_state_path) as ctx:
            assert ctx.page is mock_page

    mock_page.goto.assert_called_once_with(
        f"{settings.limitless_base_url}{APPLY_PATH}",
        timeout=settings.session_validation_timeout_ms,
    )


def test_authenticated_page_treats_timeout_as_expired_session(tmp_path):
    """When page.goto() raises TimeoutError, treat as expired session: delete state, re-login, session_refreshed=True."""
    storage_state_path = tmp_path / "storage_state.json"
    storage_state_path.write_text("{}")

    mock_page = MagicMock()
    mock_page.goto.side_effect = PlaywrightTimeoutError("Timeout 10000ms exceeded")
    mock_playwright, mock_browser = _mock_playwright(mock_page)

    with patch("app.scraper.session.sync_playwright") as mock_sync_playwright, \
            patch("app.scraper.session.login") as mock_login:
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright

        with authenticated_page(storage_state_path=storage_state_path) as ctx:
            assert isinstance(ctx, AuthenticatedPageContext)
            assert ctx.page is mock_page
            assert ctx.session_refreshed is True

    assert not storage_state_path.exists()
    mock_login.assert_called_once_with(
        mock_page,
        settings.limitless_username,
        settings.limitless_password,
        storage_state_path=storage_state_path,
    )
