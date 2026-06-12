"""Acceptance test: resubmission + Discord notification (FR3, FR4).

Given an authenticated browser session (FR1),
When the organization application is resubmitted on its scheduled cadence,
Then the outcome is determined from the resulting page state and a Discord
notification reflecting that outcome is posted to the configured webhook.
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import respx

from app.notifications.discord import post_resubmission_notice
from app.scraper.resubmit import resubmit_application

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "html"
WEBHOOK_URL = "https://discord.com/api/webhooks/123/abc"


@respx.mock
def test_resubmission_success_triggers_discord_notification():
    # Given an authenticated page whose resubmit action succeeds
    page = MagicMock()
    page.content.return_value = (FIXTURE_DIR / "org_settings_resubmit_success.html").read_text()
    route = respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

    # When the application is resubmitted and the result is reported
    success = resubmit_application(page)
    response = post_resubmission_notice(
        WEBHOOK_URL, datetime(2026, 6, 12, 9, 0, tzinfo=timezone.utc), success=success
    )

    # Then the resubmission is reported as successful and Discord is notified
    assert success is True
    assert response.status_code == 204
    payload = route.calls.last.request.content.decode()
    assert "succeeded" in payload.lower()


@respx.mock
def test_resubmission_failure_triggers_discord_notification():
    # Given an authenticated page whose resubmit action fails
    page = MagicMock()
    page.content.return_value = (FIXTURE_DIR / "org_settings_resubmit_failure.html").read_text()
    route = respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(204))

    # When the application is resubmitted and the result is reported
    success = resubmit_application(page)
    response = post_resubmission_notice(
        WEBHOOK_URL, datetime(2026, 6, 12, 21, 0, tzinfo=timezone.utc), success=success
    )

    # Then the resubmission is reported as failed but Discord is still notified
    assert success is False
    assert response.status_code == 204
    payload = route.calls.last.request.content.decode()
    assert "failed" in payload.lower()
