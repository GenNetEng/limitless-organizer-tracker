from datetime import date, datetime, timezone

import pytest

from app.analytics.buckets import bucket_activity


def _dt(*args):
    return datetime(*args, tzinfo=timezone.utc)


def test_bucket_activity_by_week_groups_to_monday_start():
    dates = [
        _dt(2026, 6, 1),  # Monday
        _dt(2026, 6, 3),  # Wednesday, same week
        _dt(2026, 6, 8),  # next Monday
    ]

    result = bucket_activity(dates, "week")

    assert result == [
        (date(2026, 6, 1), 2),
        (date(2026, 6, 8), 1),
    ]


def test_bucket_activity_by_month_groups_to_first_of_month():
    dates = [
        _dt(2026, 6, 1),
        _dt(2026, 6, 30),
        _dt(2026, 7, 4),
    ]

    result = bucket_activity(dates, "month")

    assert result == [
        (date(2026, 6, 1), 2),
        (date(2026, 7, 1), 1),
    ]


def test_bucket_activity_returns_empty_list_for_no_dates():
    assert bucket_activity([], "week") == []


def test_bucket_activity_rejects_invalid_interval():
    with pytest.raises(ValueError):
        bucket_activity([_dt(2026, 6, 1)], "year")
