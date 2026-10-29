"""Causal monthly market/model logistic blends, oriented to either team."""

import numpy as np
import pandas as pd

from promcs.evaluation import HOLDOUT_START


def features(p, mid):
    p, mid = (
        np.clip(np.asarray(p, dtype=float), 0.01, 0.99),
        np.clip(np.asarray(mid, dtype=float), 0.01, 0.99),
    )
    market = np.log(mid / (1 - mid))
    return np.column_stack((market, np.log(p / (1 - p)) - market))


def combine(p, mid, a=1.0, b=0.0):
    """Apply a frozen fit; (1, 0) returns the clipped market midpoint."""
    z = features(p, mid) @ np.array([a, b])
    return np.exp(-np.logaddexp(0, -z))


def fit(p, mid, won):
    """Return (a, b, n): no-intercept binomial MLE with 1e-6 ridge.

    Damped Newton steps minimize the summed negative log likelihood. Ridge
    keeps the Hessian invertible even for collinear or separated samples.
    """
    x = features(p, mid)
    y = np.asarray(won, dtype=float)
    ridge = 1e-6
    beta = np.array([1.0, 0.0])

    def objective(value):
        z = x @ value
        return np.sum(np.logaddexp(0, z) - y * z) + ridge / 2 * (value @ value)

    for _ in range(100):
        z = x @ beta
        probability = np.exp(-np.logaddexp(0, -z))
        gradient = x.T @ (probability - y) + ridge * beta
        hessian = x.T @ ((probability * (1 - probability))[:, None] * x)
        step = np.linalg.solve(hessian + ridge * np.eye(2), gradient)
        scale = 1.0
        previous = objective(beta)
        while scale > 1e-8 and objective(beta - scale * step) > previous:
            scale *= 0.5
        beta -= scale * step
        if np.max(np.abs(scale * step)) < 1e-8:
            break
    return float(beta[0]), float(beta[1]), len(y)


def walk_forward(frame, validate_from="2026-01-01", min_rows=100):
    """Return annotated rows and monthly fits, using strictly earlier months.

    Training is separate by kind, starts at validate_from, and excludes holdout.
    Unfitted rows retain the exact midpoint and are flagged for report exclusion.
    """
    if min_rows < 1:
        raise ValueError("min_rows must be positive")
    rows = frame.copy()
    for column in ("p_blend", "blend_a", "blend_b", "blend_n"):
        rows[column] = np.nan
    rows["blend_fitted"] = False
    columns = ["month", "kind", "n", "a", "b", "fitted"]
    if rows.empty:
        return rows, pd.DataFrame(columns=columns)
    dates = pd.to_datetime(rows.start_utc, utc=True)
    months = dates.dt.strftime("%Y-%m")
    eligible = (dates >= pd.Timestamp(validate_from, tz="UTC")) & (
        dates < pd.Timestamp(HOLDOUT_START, tz="UTC")
    )
    snapshots = []
    for month in sorted(months.unique()):
        boundary = pd.Timestamp(month, tz="UTC")
        for kind in ("series", "map"):
            current = (months == month) & (rows.kind == kind)
            if not current.any():
                continue
            training = rows[eligible & (dates < boundary) & (rows.kind == kind)]
            n = len(training)
            fitted = n >= min_rows
            a, b, n = (
                fit(training.p, training.market_p, training.won)
                if fitted
                else (1, 0, n)
            )
            rows.loc[current, "p_blend"] = (
                combine(rows.loc[current, "p"], rows.loc[current, "market_p"], a, b)
                if fitted
                else rows.loc[current, "market_p"]
            )
            rows.loc[current, ["blend_a", "blend_b", "blend_n"]] = [a, b, n]
            rows.loc[current, "blend_fitted"] = fitted
            snapshots.append([month, kind, n, a, b, fitted])
    rows["blend_n"] = rows.blend_n.astype(int)
    return rows, pd.DataFrame(snapshots, columns=columns)
