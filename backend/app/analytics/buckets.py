from datetime import date, datetime, timedelta

VALID_INTERVALS = ("week", "month")
VALID_ONBOARDING_INTERVALS = ("day", "week")


def bucket_activity(dates: list[datetime], interval: str) -> list[tuple[date, int]]:
    """Group dates into week- or month-start buckets, returning sorted (period_start, count) pairs.

    Week buckets start on Monday (ISO week); month buckets start on the 1st.
    """
    if interval not in VALID_INTERVALS:
        raise ValueError(f"invalid interval: {interval!r}, expected one of {VALID_INTERVALS}")

    counts: dict[date, int] = {}
    for dt in dates:
        day = dt.date()
        if interval == "week":
            period = day - timedelta(days=day.weekday())
        else:
            period = day.replace(day=1)
        counts[period] = counts.get(period, 0) + 1

    return sorted(counts.items())


def bucket_onboarding(dates: list[date], interval: str) -> list[tuple[date, int]]:
    """Group onboarding dates into day or week-start buckets, returning sorted (period_start, count) pairs.

    Week buckets start on Monday (ISO week).
    """
    if interval not in VALID_ONBOARDING_INTERVALS:
        raise ValueError(f"invalid interval: {interval!r}, expected one of {VALID_ONBOARDING_INTERVALS}")

    counts: dict[date, int] = {}
    for d in dates:
        period = d if interval == "day" else d - timedelta(days=d.weekday())
        counts[period] = counts.get(period, 0) + 1

    return sorted(counts.items())
