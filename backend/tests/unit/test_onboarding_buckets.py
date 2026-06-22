from datetime import date

import pytest

from app.analytics.buckets import bucket_dates


def test_bucket_by_day_groups_each_date_separately():
    dates = [date(2026, 6, 1), date(2026, 6, 1), date(2026, 6, 2)]
    result = bucket_dates(dates, "day")
    assert result == [(date(2026, 6, 1), 2), (date(2026, 6, 2), 1)]


def test_bucket_by_week_groups_dates_to_monday():
    dates = [
        date(2026, 6, 1),  # Monday
        date(2026, 6, 3),  # Wednesday — same week
        date(2026, 6, 8),  # next Monday
    ]
    result = bucket_dates(dates, "week")
    assert result == [(date(2026, 6, 1), 2), (date(2026, 6, 8), 1)]


def test_returns_sorted_ascending():
    dates = [date(2026, 6, 5), date(2026, 6, 2), date(2026, 6, 1)]
    result = bucket_dates(dates, "day")
    periods = [r[0] for r in result]
    assert periods == sorted(periods)


def test_empty_list_returns_empty():
    assert bucket_dates([], "day") == []
    assert bucket_dates([], "week") == []


def test_invalid_interval_raises():
    with pytest.raises(ValueError):
        bucket_dates([date(2026, 6, 1)], "bogus")
