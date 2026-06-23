"""Acceptance test: resubmission + Discord notification (FR3, FR4).

Given an authenticated browser session (FR1),
When the organization application is resubmitted on its scheduled cadence,
Then the outcome is determined from the server response and a Discord
notification reflecting that outcome is posted to the configured webhook.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import httpx
import respx

from app.notifications.discord import post_resubmission_notice
from app.scraper.resubmit import resubmit_application

WEBHOOK_URL = "https://discord.com/api/webhooks/123/abc"
FORM_DATA = {"name": "Test Org", "discord": "user", "message": "msg", "answers": {"q1": "a1"}}


@respx.mock
def test_resubmission_success_triggers_discord_notification():
    page = MagicMock()
    page.evaluate.side_effect = [None, FORM_DATA, {"status": "ok", "ok": True}]
    route = respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

    result = resubmit_application(page)
    response = post_resubmission_notice(
        WEBHOOK_URL, datetime(2026, 6, 12, 9, 0, tzinfo=timezone.utc), success=result.success
    )

    assert result.success is True
    assert response.status_code == 204
    payload = route.calls.last.request.content.decode()
    assert "succeeded" in payload.lower()


@respx.mock
def test_resubmission_failure_triggers_discord_notification():
    page = MagicMock()
    page.evaluate.side_effect = [None, FORM_DATA, {"status": "error", "ok": False}]
    route = respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

    result = resubmit_application(page)
    response = post_resubmission_notice(
        WEBHOOK_URL, datetime(2026, 6, 12, 21, 0, tzinfo=timezone.utc), success=result.success
    )

    assert result.success is False
    assert response.status_code == 204
    payload = route.calls.last.request.content.decode()
    assert "failed" in payload.lower()
