from datetime import datetime

import httpx

_SUCCESS_TEMPLATE = "Resubmission succeeded at {timestamp}."
_FAILURE_TEMPLATE = "Resubmission failed at {timestamp}."


def build_resubmission_message(timestamp: datetime, success: bool) -> str:
    """Build the Discord message content for a resubmission event."""
    template = _SUCCESS_TEMPLATE if success else _FAILURE_TEMPLATE
    return template.format(timestamp=timestamp.isoformat())


def post_resubmission_notice(webhook_url: str, timestamp: datetime, success: bool) -> httpx.Response:
    """Post a Discord notification for a resubmission event via webhook."""
    message = build_resubmission_message(timestamp, success)
    return httpx.post(webhook_url, json={"content": message})
