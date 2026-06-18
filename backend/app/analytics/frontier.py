def compute_frontier(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Return the Pareto-optimal (lower-envelope) subset of (organizer_id, date_ordinal) points.

    A point is on the frontier iff no other point with an equal-or-higher organizer_id
    has a strictly earlier date — i.e., it represents the fastest observed
    onboarding-to-first-event lag for its ID range.

    Input may be in any order. Output is sorted ascending by organizer_id.
    """
    if not points:
        return []

    frontier: list[tuple[float, float]] = []
    running_min = float("inf")

    for organizer_id, date_ordinal in sorted(points, key=lambda p: p[0], reverse=True):
        if date_ordinal <= running_min:
            frontier.append((organizer_id, date_ordinal))
            running_min = date_ordinal

    frontier.reverse()
    return frontier
