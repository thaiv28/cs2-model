"""Offline execution contract and causal frozen-coefficient checks."""

import hashlib
import json
from collections import Counter
from datetime import UTC, datetime

import numpy as np
import pandas as pd
import pytest

from promcs import blend
from promcs.trading import build_blend_artifact, candidates

NOW = datetime(2026, 10, 29, 12, tzinfo=UTC)


def test_artifact_causal_subsets_and_minimum():
    rng = np.random.default_rng(42)
    rows = pd.DataFrame(
        {
            "kind": ["series"] * 800,
            "p": rng.uniform(0.1, 0.9, 800),
            "market_p": rng.uniform(0.1, 0.9, 800),
            "won": rng.integers(0, 2, 800),
            "start_utc": pd.date_range("2025-12-01", periods=800, freq="12h", tz="UTC"),
        }
    )
    # Map rows and unknown outcomes must not affect the fits.
    rows.loc[10:20, "kind"] = "map"
    rows.loc[80, "won"] = np.nan
    artifact = build_blend_artifact(rows, "cs2", "KXCS2GAME", NOW)
    assert artifact["version"] == "game-blend-v1" and artifact["clip"] == 0.01
    snapshots = artifact["snapshots"]
    assert snapshots and snapshots[-1]["available_from"] == "2026-11-01T00:00:00+00:00"
    boundaries = [s["available_from"] for s in snapshots]
    assert boundaries == sorted(set(boundaries))
    for snapshot in snapshots:
        boundary = pd.Timestamp(snapshot["available_from"])
        subset = rows[
            (rows.kind == "series")
            & rows.won.notna()
            & (rows.start_utc >= pd.Timestamp("2026-01-01", tz="UTC"))
            & (rows.start_utc < boundary)
        ]
        a, b, n = blend.fit(subset.p, subset.market_p, subset.won)
        assert snapshot["training_series"] == n >= 300
        assert snapshot["market_slope"] == a and snapshot["gap_slope"] == b
        assert snapshot["trained_through"] == subset.start_utc.max().isoformat()
        assert snapshot["trained_through"] < snapshot["available_from"]
    assert snapshots[0]["available_from"] == "2026-06-01T00:00:00+00:00"
    assert (
        build_blend_artifact(rows.iloc[:100], "cs2", "KXCS2GAME", NOW)["snapshots"]
        == []
    )
    # No blanket holdout exclusion: December fits may learn November outcomes.
    later = build_blend_artifact(
        rows, "cs2", "KXCS2GAME", datetime(2026, 11, 29, tzinfo=UTC)
    )
    assert later["snapshots"][-1]["trained_through"].startswith("2026-11-")


@pytest.fixture
def inputs():
    row = {
        "match_id": "our-match",
        "status": "upcoming",
        "start": "2026-10-29T18:00Z",
        "best_of": 3,
        "section": "INTL",
        "name1": "hotu",
        "name2": "gl",
        "p_game": 0.6,
        "p_series": 0.712345678,
    }
    pair = [
        {
            "event_ticker": "KXCS2GAME-TEST",
            "status": "active",
            "yes_sub_title": side,
            "rules_primary": f"If {side} wins the Tesla Cup 2026: GamerLegion vs. HOTU CS2 match originally scheduled for Oct 29, 2026 at 2:00 PM EDT, then Yes.",
        }
        for side in ("HOTU", "GamerLegion")
    ]
    return row, {row["match_id"]: pair}


def test_candidate_names_orientation_start_and_validation_shape(inputs):
    row, linked = inputs
    doc = candidates([row], linked, NOW, data_through="2026-10-28")
    assert doc["generated"] == "2026-10-29T12:00:00Z"
    saved = doc["matches"][0]["execution_candidate"]
    assert saved["teams"] == ["GamerLegion", "HOTU"]
    assert saved["raw"] == {"HOTU": 0.712346, "GamerLegion": 0.287654}
    assert saved["start"] == "2026-10-29T18:00Z"
    identity = json.dumps(
        ["cs2", saved["teams"], saved["event_ticker"]],
        separators=(",", ":"),
        ensure_ascii=False,
    )
    assert saved["fixture_id"] == hashlib.sha256(identity.encode()).hexdigest()
    assert saved["provenance"]["p_series"] == row["p_series"]
    assert saved["provenance"]["names"] == ["hotu", "gl"]
    assert saved["provenance"]["data_through"] == "2026-10-28"
    # Mirror saved_candidates' input validation without importing its live runtime.
    assert saved["kind"] == "candidate-v1" and saved["schema_version"] == 1
    assert saved["group"] == "cs2-series"
    assert isinstance(saved["teams"], list) and len(set(saved["teams"])) == 2
    assert all(isinstance(t, str) and t for t in saved["teams"])
    assert all(
        isinstance(saved[k], str) and saved[k] for k in ("fixture_id", "event_ticker")
    )
    assert isinstance(saved["international"], bool) and saved["international"]
    assert isinstance(saved["team_homes"], dict) and isinstance(
        saved["provenance"], dict
    )
    assert all(isinstance(v, (int, float)) and 0 < v < 1 for v in saved["raw"].values())
    assert saved["game"] == "cs2" and saved["series_ticker"] == "KXCS2GAME"


@pytest.mark.parametrize(
    "change",
    [
        "subtitle",
        "teams",
        "same-side",
        "rules",
        "closed",
        "missing",
        "time",
        "started",
        "unknown",
        "live",
        "kalshi-started",
    ],
)
def test_rejected_candidates_counted(inputs, change):
    row, linked = inputs
    pair = linked[row["match_id"]]
    if change == "subtitle":
        pair[0]["yes_sub_title"] = "Other"
    elif change == "teams":
        pair[1]["rules_primary"] = pair[1]["rules_primary"].replace(
            "GamerLegion vs.", "Other vs."
        )
    elif change == "same-side":
        pair[1] = pair[0].copy()
    elif change == "rules":
        pair[0]["rules_primary"] = "not rules"
    elif change == "closed":
        pair[0]["status"] = "closed"
    elif change == "missing":
        pair.pop()
    elif change == "time":
        row["start"] = "2026-10-30T13:00Z"
    elif change == "started":
        row["start"] = "2026-10-29T12:00Z"
    elif change == "unknown":
        row["best_of"] = None
    elif change == "live":
        row["status"] = "live"
    elif change == "kalshi-started":
        for market in pair:
            market["rules_primary"] = market["rules_primary"].replace(
                "2:00 PM", "8:00 AM"
            )
    skipped = Counter()
    assert candidates([row], linked, NOW, skipped=skipped)["matches"] == []
    assert skipped["candidates"] == 1


def test_no_current_markets(inputs):
    row, _ = inputs
    assert candidates([row], {}, NOW)["matches"] == []
