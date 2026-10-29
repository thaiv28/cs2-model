"""Frozen post-model adjustments fitted exclusively on tuning predictions."""

import numpy as np
import pandas as pd

from promcs.ratings.regions import REGION_CODES, macro_region

REGIONS = tuple(REGION_CODES)


def causal_features(conn, lineups):
    """Emit homes before each scored map, using earlier eligible event hosts."""
    maps = conn.execute('''SELECT g.game_id, m.team1_id, m.team2_id, e.region,
                  COALESCE(e.international, 0)
           FROM maps g JOIN matches m USING (match_id)
           JOIN events e USING (event_id)
           WHERE g.score1 != g.score2 AND e.excluded = 0
           ORDER BY m.start_utc, m.match_id, g."order"''')
    homes, counts, features = {}, {}, []
    for game, team1, team2, host, international in maps:
        features.append(
            {"game_id": game, "home1": homes.get(team1), "home2": homes.get(team2)}
        )
        region = macro_region(host)
        if region is not None and not international:
            for team in (team1, team2):
                buckets = counts.setdefault(team, {})
                buckets[region] = buckets.get(region, 0) + 1
                if buckets[region] > buckets.get(homes.get(team), 0):
                    homes[team] = region
    result = pd.DataFrame(features, columns=["game_id", "home1", "home2"])
    for column in ("home1", "home2"):
        result[column] = pd.Series([row[column] for row in features], dtype=object)
    return result.set_index("game_id")


def _logit(p):
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(p) - np.log1p(-p)


def _sigmoid(z):
    return np.exp(-np.logaddexp(0, -z))


def _fit_newton(x, y, offset, penalty):
    """Minimize summed logistic loss plus beta.T @ penalty @ beta.

    Backtracking keeps Newton steps stable for sparse or separable samples.
    beta describes a residual adjustment, hence zero is always identity.
    """
    beta = np.zeros(x.shape[1])

    def loss(b):
        z = offset + x @ b
        return np.sum(np.logaddexp(0, z) - y * z) + b @ penalty @ b

    for _ in range(100):
        p = _sigmoid(offset + x @ beta)
        gradient = x.T @ (p - y) + 2 * penalty @ beta
        hessian = (x.T * (p * (1 - p))) @ x + 2 * penalty
        step = np.linalg.lstsq(hessian, gradient, rcond=None)[0]
        if np.max(np.abs(gradient), initial=0) < 1e-9:
            break
        current = loss(beta)
        scale = 1.0
        while scale > 1e-10 and loss(beta - scale * step) > current:
            scale *= 0.5
        beta -= scale * step
        if np.max(np.abs(scale * step), initial=0) < 1e-9:
            break
    return beta


class Layer:
    name: str

    def __init__(self, context=None):
        self.context = context or {}
        self._features = None

    def features(self, frame):
        if self._features is None:
            self._features = causal_features(
                self.context["conn"], self.context["lineups"]
            )
        return self._features.reindex(frame.game_id)

    def fit(self, frame) -> None:
        raise NotImplementedError

    def apply(self, frame) -> pd.Series:
        raise NotImplementedError

    def describe(self) -> str:
        return self.name


class IdentityLayer(Layer):
    name = "none"

    def fit(self, frame) -> None:
        pass

    def apply(self, frame) -> pd.Series:
        return frame.p.copy()


class RegionalLayer(Layer):
    name = "regional"

    def __init__(self, context=None):
        super().__init__(context)
        self.s = 1.0
        self.effects = dict.fromkeys(REGIONS, 0.0)
        self.rows = 0

    def _design(self, frame):
        features = self.features(frame)
        mask = (
            features.home1.isin(REGIONS)
            & features.home2.isin(REGIONS)
            & (features.home1 != features.home2)
        ).to_numpy()
        # e = basis @ theta enforces sum(e) = 0, including in the ridge.
        basis = np.vstack([np.eye(len(REGIONS) - 1), -np.ones(len(REGIONS) - 1)])
        difference = np.array(
            [
                (features.home1 == r).astype(float)
                - (features.home2 == r).astype(float)
                for r in REGIONS
            ]
        ).T
        x = np.column_stack([_logit(frame.p), difference @ basis])
        return mask, x, basis

    def fit(self, frame) -> None:
        mask, x, basis = self._design(frame)
        self.rows = int(mask.sum())
        self.s, self.effects = 1.0, dict.fromkeys(REGIONS, 0.0)
        if self.rows < 50:
            return
        penalty = np.zeros((len(REGIONS), len(REGIONS)))
        penalty[0, 0] = 4
        penalty[1:, 1:] = 4 * basis.T @ basis
        beta = _fit_newton(
            x[mask], frame.won.to_numpy(dtype=float)[mask], x[mask, 0], penalty
        )
        self.s = 1 + beta[0]
        self.effects = dict(zip(REGIONS, basis @ beta[1:], strict=True))

    def apply(self, frame) -> pd.Series:
        result = frame.p.copy()
        if self.rows < 50:
            return result
        mask, x, _ = self._design(frame)
        beta = np.r_[self.s - 1, [self.effects[r] for r in REGIONS[:-1]]]
        result.iloc[np.flatnonzero(mask)] = np.clip(
            _sigmoid(x[mask, 0] + x[mask] @ beta), 1e-6, 1 - 1e-6
        )
        return result

    def describe(self) -> str:
        status = "identity (<50 cross-region rows)" if self.rows < 50 else "ridge=4"
        effects = ", ".join(f"{r}={e:.6g}" for r, e in self.effects.items())
        return (
            f"regional: rows={self.rows}, {status}, s={self.s:.6g}, effects: {effects}"
        )


LAYERS = {"none": IdentityLayer, "regional": RegionalLayer}
