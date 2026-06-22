from datetime import date, datetime, timedelta
from typing import Iterable, Union

VALID_INTERVALS = ("day", "week", "month")


def bucket_dates(dates: Iterable[Union[date, datetime]], interval: str) -> list[tuple[date, int]]:
    """Group dates into day, week-start, or month-start buckets.

    Accepts date or datetime objects (datetimes are converted to date).
    Week buckets start on Monday (ISO week); month buckets start on the 1st.
    Returns sorted (period_start, count) pairs.
    """
    if interval not in VALID_INTERVALS:
        raise ValueError(f"invalid interval: {interval!r}, expected one of {VALID_INTERVALS}")

    counts: dict[date, int] = {}
    for d in dates:
        if isinstance(d, datetime):
            d = d.date()
        if interval == "day":
            period = d
        elif interval == "week":
            period = d - timedelta(days=d.weekday())
        else:
            period = d.replace(day=1)
        counts[period] = counts.get(period, 0) + 1
    return sorted(counts.items())
