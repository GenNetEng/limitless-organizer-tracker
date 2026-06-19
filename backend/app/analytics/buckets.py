from datetime import date, datetime, timedelta
from typing import Iterable

VALID_INTERVALS = ("week", "month")
VALID_ONBOARDING_INTERVALS = ("day", "week")


def _bucket_dates(dates: Iterable[date], interval: str) -> list[tuple[date, int]]:
    counts: dict[date, int] = {}
    for d in dates:
        if interval == "day":
            period = d
        elif interval == "week":
            period = d - timedelta(days=d.weekday())
        else:  # month
            period = d.replace(day=1)
        counts[period] = counts.get(period, 0) + 1
    return sorted(counts.items())


def bucket_activity(dates: list[datetime], interval: str) -> list[tuple[date, int]]:
    """Group dates into week- or month-start buckets, returning sorted (period_start, count) pairs.

    Week buckets start on Monday (ISO week); month buckets start on the 1st.
    """
    if interval not in VALID_INTERVALS:
        raise ValueError(f"invalid interval: {interval!r}, expected one of {VALID_INTERVALS}")
    return _bucket_dates((dt.date() for dt in dates), interval)


def bucket_onboarding(dates: list[date], interval: str) -> list[tuple[date, int]]:
    """Group onboarding dates into day or week-start buckets, returning sorted (period_start, count) pairs.

    Week buckets start on Monday (ISO week).
    """
    if interval not in VALID_ONBOARDING_INTERVALS:
        raise ValueError(f"invalid interval: {interval!r}, expected one of {VALID_ONBOARDING_INTERVALS}")
    return _bucket_dates(dates, interval)
