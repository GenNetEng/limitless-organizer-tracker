from datetime import datetime, timezone

from app.notifications.discord import build_resubmission_message


def test_build_resubmission_message_for_success():
    timestamp = datetime(2026, 6, 12, 9, 0, tzinfo=timezone.utc)

    message = build_resubmission_message(timestamp, success=True)

    assert "2026-06-12T09:00:00+00:00" in message
    assert "succeeded" in message.lower()


def test_build_resubmission_message_for_failure():
    timestamp = datetime(2026, 6, 12, 21, 0, tzinfo=timezone.utc)

    message = build_resubmission_message(timestamp, success=False)

    assert "2026-06-12T21:00:00+00:00" in message
    assert "failed" in message.lower()
