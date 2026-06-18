from app.analytics.frontier import compute_frontier


def test_compute_frontier_empty_input():
    assert compute_frontier([]) == []


def test_compute_frontier_single_point():
    assert compute_frontier([(5.0, 100.0)]) == [(5.0, 100.0)]


def test_compute_frontier_all_on_frontier_when_dates_decrease_with_id():
    # id increases -> date increases (monotone), so each point is on the frontier
    # when scanning descending by id, each new point has a lower date than running_min
    points = [(100.0, 10.0), (200.0, 20.0), (300.0, 30.0)]

    result = compute_frontier(points)

    assert result == [(100.0, 10.0), (200.0, 20.0), (300.0, 30.0)]


def test_compute_frontier_excludes_dominated_points():
    # (200, 30) is dominated by (300, 20) — higher id, earlier date
    points = [(100.0, 10.0), (200.0, 30.0), (300.0, 20.0)]

    result = compute_frontier(points)

    assert (200.0, 30.0) not in result
    assert (100.0, 10.0) in result
    assert (300.0, 20.0) in result


def test_compute_frontier_all_identical_dates():
    # All same date — the first point scanned (highest id) sets running_min;
    # every subsequent point ties running_min so all are included.
    points = [(100.0, 50.0), (200.0, 50.0), (300.0, 50.0)]

    result = compute_frontier(points)

    assert len(result) == 3


def test_compute_frontier_only_highest_id_when_monotone_increasing_id_and_date():
    # Dates strictly increase as id decreases — only the highest-id point is on frontier
    points = [(100.0, 30.0), (200.0, 20.0), (300.0, 10.0)]

    result = compute_frontier(points)

    assert result == [(300.0, 10.0)]


def test_compute_frontier_output_sorted_ascending_by_organizer_id():
    points = [(300.0, 20.0), (100.0, 10.0), (200.0, 30.0)]

    result = compute_frontier(points)

    ids = [p[0] for p in result]
    assert ids == sorted(ids)


def test_compute_frontier_ties_in_organizer_id_both_kept_when_both_on_frontier():
    # Two rows with the same organizer_id and same date — both meet running_min <= check
    points = [(100.0, 10.0), (100.0, 10.0), (200.0, 20.0)]

    result = compute_frontier(points)

    assert all(p in result for p in [(100.0, 10.0), (200.0, 20.0)])


def test_compute_frontier_single_dominated_point_excluded():
    # (150, 50) is dominated by (200, 20)
    points = [(100.0, 10.0), (150.0, 50.0), (200.0, 20.0)]

    result = compute_frontier(points)

    dominated_ids = {p[0] for p in result}
    assert 150.0 not in dominated_ids
    assert 100.0 in dominated_ids
    assert 200.0 in dominated_ids
