import pytest

from app.analytics.regression import fit_linear_regression


def test_fit_linear_regression_perfect_line():
    points = [(1.0, 10.0), (2.0, 20.0), (3.0, 30.0)]

    result = fit_linear_regression(points)

    assert result.slope == pytest.approx(10.0)
    assert result.intercept == pytest.approx(0.0)
    assert result.r_squared == pytest.approx(1.0)


def test_fit_linear_regression_predict():
    points = [(1.0, 10.0), (2.0, 20.0), (3.0, 30.0)]

    result = fit_linear_regression(points)

    assert result.predict(5.0) == pytest.approx(50.0)


def test_fit_linear_regression_scattered_points_r_squared_less_than_one():
    points = [(1.0, 10.0), (2.0, 19.0), (3.0, 31.0), (4.0, 38.0)]

    result = fit_linear_regression(points)

    assert 0.0 < result.r_squared < 1.0


def test_fit_linear_regression_requires_at_least_two_points():
    with pytest.raises(ValueError):
        fit_linear_regression([(1.0, 10.0)])


def test_fit_linear_regression_constant_x_has_zero_slope():
    points = [(5.0, 1.0), (5.0, 2.0), (5.0, 3.0)]

    result = fit_linear_regression(points)

    assert result.slope == pytest.approx(0.0)
    assert result.intercept == pytest.approx(2.0)
