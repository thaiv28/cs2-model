"""Causal homes and frozen seven-region layer fits."""

import sqlite3

import numpy as np
import pandas as pd
import pytest

from promcs.ratings.layers import (
    LAYERS,
    REGIONS,
    CalibrationLayer,
    RegionalLayer,
    causal_features,
)


def planted(n=10000):
    rng = np.random.default_rng(38)
    a = rng.integers(0, len(REGIONS), n)
    b = (a + rng.integers(1, len(REGIONS), n)) % len(REGIONS)
    logits = rng.normal(0, 1, n)
    frame = pd.DataFrame({"game_id": np.arange(n), "p": 1 / (1 + np.exp(-logits))})
    features = pd.DataFrame(
        {"home1": np.array(REGIONS)[a], "home2": np.array(REGIONS)[b]}
    )
    features.index.name = "game_id"
    effects = np.array([0.45, -0.35, 0.15, -0.25, 0.2, -0.1, -0.1])
    return rng, frame, features, logits, effects[a] - effects[b]


def sample(rng, z):
    return rng.binomial(1, 1 / (1 + np.exp(-z)))


def test_regional_recovery_scope_zero_sum_and_index():
    rng, frame, features, logits, effect = planted()
    frame["won"] = sample(rng, 1.25 * logits + effect)
    layer = RegionalLayer()
    layer._features = features
    layer.fit(frame)
    assert layer.rows == len(frame)
    assert layer.s == pytest.approx(1.25, abs=0.08)
    assert list(layer.effects.values()) == pytest.approx(
        [0.45, -0.35, 0.15, -0.25, 0.2, -0.1, -0.1], abs=0.08
    )
    assert sum(layer.effects.values()) == pytest.approx(0, abs=1e-14)
    features.loc[0, "home2"] = features.loc[0, "home1"]
    features.loc[1, "home1"] = None
    apply = frame.iloc[:4].copy()
    apply.index = [8, 3, 3, 7]
    adjusted = layer.apply(apply)
    assert adjusted.index.equals(apply.index)
    assert adjusted.iloc[:2].tolist() == apply.p.iloc[:2].tolist()
    assert not np.allclose(adjusted.iloc[2:], apply.p.iloc[2:])
    assert "rows=10000" in layer.describe() and "ridge=4" in layer.describe()


def test_regional_threshold_ridge_and_refit():
    _, frame, features, logits, effect = planted(100)
    # Fractional targets make the unpenalized optimum exact, isolating shrinkage.
    frame["won"] = 1 / (1 + np.exp(-(1.7 * logits + effect)))
    small = RegionalLayer()
    small._features = features
    small.fit(frame.iloc[:49])
    pd.testing.assert_series_equal(small.apply(frame), frame.p)
    assert "identity (<50" in small.describe()
    small.fit(frame.iloc[:50])
    large = RegionalLayer()
    large._features = features
    large.fit(pd.concat([frame.iloc[:50]] * 100, ignore_index=True))
    assert abs(small.s - 1) < abs(large.s - 1)
    assert np.linalg.norm(list(small.effects.values())) < np.linalg.norm(
        list(large.effects.values())
    )
    small.fit(frame.iloc[:0])
    assert small.s == 1 and all(e == 0 for e in small.effects.values())


def test_causal_homes_and_excluded_events():
    conn = sqlite3.connect(":memory:")
    conn.executescript("""CREATE TABLE events(event_id, region, international, excluded);
        CREATE TABLE matches(match_id, start_utc, team1_id, team2_id, event_id);
        CREATE TABLE maps(game_id, match_id, "order", score1, score2);
        INSERT INTO events VALUES (1,'NA',0,0),(2,'EU',0,0),(3,'CIS',1,0),(4,'AS',0,1);
        INSERT INTO matches VALUES (1,'2024-01-01',10,20,1),(2,'2024-01-02',10,20,2),
            (3,'2024-01-03',10,20,3),(4,'2024-01-04',10,20,4),(5,'2024-01-05',10,20,2);
        INSERT INTO maps VALUES (1,1,1,13,8),(2,1,2,13,8),(3,2,1,13,8),(4,3,1,13,8),
            (5,4,1,13,8),(6,5,1,13,8),(7,5,2,13,8),(8,5,3,0,0);""")
    features = causal_features(conn, {})
    assert features.index.tolist() == [1, 2, 3, 4, 6, 7]
    assert features.home1.tolist() == [None, "NA", "NA", "NA", "NA", "NA"]
    assert features.home1.tolist() == features.home2.tolist()
    assert set(LAYERS) == {"none", "regional", "calibration"}
    conn.close()


def test_regional_frozen_outcomes():
    rng, frame, features, logits, effects = planted(1000)
    frame["won"] = sample(rng, logits + effects)
    layer = RegionalLayer()
    layer._features = features
    layer.fit(frame.iloc[:700])
    before = layer.apply(frame.iloc[700:])
    description = layer.describe()
    frame.loc[700:, "won"] = 1 - frame.loc[700:, "won"]
    layer.fit(frame.iloc[:700])
    assert layer.describe() == description
    pd.testing.assert_series_equal(before, layer.apply(frame.iloc[700:]))


def test_calibration_recovery_threshold_and_frozen_groups():
    rng = np.random.default_rng(38)
    logits = rng.normal(0, 2, 10000)
    frame = pd.DataFrame(
        {
            "p": 1 / (1 + np.exp(-logits)),
            "won": sample(rng, 0.7 * logits),
            "section": "tier1",
            "online": 0,
        }
    )
    small = frame.iloc[:299].assign(section="tier3", online=1)
    layer = CalibrationLayer()
    layer.fit(pd.concat([frame, small], ignore_index=True))
    assert layer.temperatures[("tier1", 0)] == pytest.approx(0.7, abs=0.04)
    assert layer.temperatures[("tier3", 1)] == 1
    assert "tier1/online=0: rows=10000, T=" in layer.describe()
    assert "tier3/online=1: rows=299, T=1.0000" in layer.describe()
    expected = 1 / (1 + np.exp(-layer.temperatures[("tier1", 0)] * logits))
    np.testing.assert_allclose(layer.apply(frame), expected)
    np.testing.assert_allclose(layer.apply(small), small.p)
    unseen = small.assign(section="tier2")
    np.testing.assert_allclose(layer.apply(unseen), unseen.p)
    before = layer.apply(frame)
    pd.testing.assert_series_equal(before, layer.apply(frame.assign(won=1 - frame.won)))
    layer.fit(small)
    assert layer.temperatures == {("tier3", 1): 1}


def test_calibration_identity_index_clipping_and_threshold():
    frame = pd.DataFrame(
        {
            "p": [0.1, 0.3, 0.8],
            "won": [0, 1, 1],
            "section": ["tier1", "tier2", "tier3"],
            "online": [0, 1, 1],
        },
        index=[8, 3, 3],
    )
    layer = LAYERS["calibration"]()
    layer.fit(frame)
    pd.testing.assert_series_equal(layer.apply(frame), frame.p, check_exact=False)
    extremes = frame.assign(p=[0, 1, 0.5])
    np.testing.assert_allclose(layer.apply(extremes), [1e-6, 1 - 1e-6, 0.5])
    threshold = pd.concat([frame.iloc[:1]] * 300, ignore_index=True)
    layer.fit(threshold)
    assert layer.temperatures[("tier1", 0)] != 1
