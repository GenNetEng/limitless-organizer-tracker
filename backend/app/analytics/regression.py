from dataclasses import dataclass


@dataclass
class RegressionResult:
    slope: float
    intercept: float
    r_squared: float

    def predict(self, x: float) -> float:
        return self.slope * x + self.intercept


def fit_linear_regression(points: list[tuple[float, float]]) -> RegressionResult:
    """Fit an ordinary-least-squares line y = slope*x + intercept to `points`."""
    n = len(points)
    if n < 2:
        raise ValueError("at least 2 points are required to fit a regression")

    sum_x = sum(x for x, _ in points)
    sum_y = sum(y for _, y in points)
    sum_xy = sum(x * y for x, y in points)
    sum_x2 = sum(x * x for x, _ in points)

    denom = n * sum_x2 - sum_x**2
    if denom == 0:
        slope = 0.0
        intercept = sum_y / n
    else:
        slope = (n * sum_xy - sum_x * sum_y) / denom
        intercept = (sum_y - slope * sum_x) / n

    mean_y = sum_y / n
    ss_tot = sum((y - mean_y) ** 2 for _, y in points)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in points)
    r_squared = 1.0 if ss_tot == 0 else 1 - ss_res / ss_tot

    return RegressionResult(slope=slope, intercept=intercept, r_squared=r_squared)
