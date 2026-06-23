from unittest.mock import MagicMock

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from app.scraper.resubmit import resubmit_application


def _make_page(form_data=None, server_response=None):
    page = MagicMock()
    if form_data is None:
        form_data = {"name": "Test Org", "discord": "user", "message": "msg", "answers": {"q1": "a1"}}
    if server_response is None:
        server_response = {"status": "ok", "ok": True}
    page.evaluate.side_effect = [None, form_data, server_response]
    return page


def test_resubmit_application_returns_success():
    page = _make_page()

    result = resubmit_application(page)

    assert result.success is True
    assert result.failure_stage is None
    assert result.server_response == {"status": "ok", "ok": True}
    assert page.evaluate.call_count == 3


def test_resubmit_fails_when_page_load_fails():
    page = MagicMock()
    page.wait_for_selector.side_effect = PlaywrightTimeoutError("timeout")

    result = resubmit_application(page)

    assert result.success is False
    assert result.failure_stage == "page_load_failed"


def test_resubmit_fails_when_page2_not_visible():
    page = MagicMock()
    page.wait_for_selector.side_effect = [None, PlaywrightTimeoutError("timeout")]

    result = resubmit_application(page)

    assert result.success is False
    assert result.failure_stage == "page2_not_visible"


def test_resubmit_fails_when_server_rejects():
    page = _make_page(server_response={"status": "error", "ok": False})

    result = resubmit_application(page)

    assert result.success is False
    assert result.failure_stage == "server_rejected"
    assert result.server_response == {"status": "error", "ok": False}


def test_resubmit_fails_when_form_data_missing():
    page = MagicMock()
    page.evaluate.side_effect = [None, {"name": "", "discord": "", "message": "", "answers": {}}]

    result = resubmit_application(page)

    assert result.success is False
    assert result.failure_stage == "form_data_extraction_failed"


def test_resubmit_fails_when_fetch_post_raises():
    page = MagicMock()
    form_data = {"name": "Test Org", "discord": "user", "message": "msg", "answers": {"q1": "a1"}}
    page.evaluate.side_effect = [None, form_data, Exception("fetch failed")]

    result = resubmit_application(page)

    assert result.success is False
    assert result.failure_stage == "post_request_failed"
    assert "fetch failed" in result.server_response["error"]
