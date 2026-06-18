from datetime import date

from app.analytics.buckets import bucket_onboarding


def test_bucket_by_day_groups_each_date_separately():
    dates = [date(2026, 6, 1), date(2026, 6, 1), date(2026, 6, 2)]
    result = bucket_onboarding(dates, "day")
    assert result == [(date(2026, 6, 1), 2), (date(2026, 6, 2), 1)]


def test_bucket_by_week_groups_to_monday():
    dates = [
        date(2026, 6, 1),  # Monday
        date(2026, 6, 3),  # Wednesday — same week
        date(2026, 6, 8),  # next Monday
    ]
    result = bucket_onboarding(dates, "week")
    assert result == [(date(2026, 6, 1), 2), (date(2026, 6, 8), 1)]


def test_returns_sorted_ascending():
    dates = [date(2026, 6, 5), date(2026, 6, 2), date(2026, 6, 1)]
    result = bucket_onboarding(dates, "day")
    periods = [r[0] for r in result]
    assert periods == sorted(periods)


def test_empty_list_returns_empty():
    assert bucket_onboarding([], "day") == []
    assert bucket_onboarding([], "week") == []


def test_invalid_interval_raises():
    import pytest
    with pytest.raises(ValueError):
        bucket_onboarding([date(2026, 6, 1)], "month")
