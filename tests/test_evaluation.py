import gzip
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from promcs.blend import combine, fit, walk_forward
from promcs.evaluation import (
    ece,
    game_losses,
    interval,
    paired_bootstrap,
    resamples,
    series_probability,
)
from promcs.ratings.models import TeamEloModel
from promcs.ratings.replay import load_lineups, load_maps, replay

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "evaluate_elo", ROOT / "scripts/evaluate_elo.py"
)
benchmark = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark)


def test_series_probability():
    assert series_probability(0.6, 1) == 0.6
    assert series_probability(0.6, 3) == pytest.approx(0.648)
    assert series_probability(0.5, 5) == pytest.approx(0.5)
    assert series_probability(0, 5) == 0
    assert series_probability(1, 5) == 1
    assert np.diff([series_probability(p, 5) for p in np.linspace(0, 1, 21)]).min() > 0
    for n in (0, 2, -1):
        with pytest.raises(ValueError):
            series_probability(0.5, n)


def test_scoring_helpers():
    losses = game_losses([0.5, 0.8, 0.2], [1, 1, 1])
    assert losses.accuracy.tolist() == [0.5, 1, 0]
    assert losses.brier.tolist() == pytest.approx([0.25, 0.04, 0.64])
    assert losses.log_loss.tolist() == pytest.approx(-np.log([0.5, 0.8, 0.2]))
    assert np.isfinite(game_losses([0, 1], [1, 0]).log_loss).all()
    assert ece([0.2, 0.2, 0.8, 1], [0, 1, 1, 1]) == pytest.approx(0.2)
    assert interval([0, 1, 2, 3, 4]) == pytest.approx((0.1, 3.9))
    draws = list(resamples(3, 2, seed=0))
    assert [x.tolist() for x in draws] == [[2, 1, 1], [0, 0, 0]]
    clustered = list(resamples([np.array([0, 1]), np.array([2])], 1, seed=0))
    assert clustered[0].tolist() == [2, 2]
    assert paired_bootstrap([2, 4], [1, 3], clusters=[1, 2]) == (1, 1, 1)
    # A single match's unequal map errors must stay together in every draw.
    assert paired_bootstrap([0, 4], [0, 0], clusters=[7, 7]) == (2, 2, 2)
    with pytest.raises(ValueError, match="equal length"):
        paired_bootstrap([1, 2], [0, 0], clusters=[1])


@pytest.mark.parametrize(
    "fixture,key",
    [("candles.json", "close_dollars"), ("candles_historical.json", "close")],
)
def test_candle_formats(fixture, key):
    raw = json.loads((ROOT / "tests/fixtures/kalshi" / fixture).read_text())
    candles = raw["candlesticks"]
    end = candles[1]["end_period_ts"]
    expected = sum(float(candles[1][side][key]) for side in ("yes_bid", "yes_ask")) / 2
    from datetime import UTC, datetime

    start = datetime.fromtimestamp(end, UTC).isoformat()
    assert benchmark.candle_mid(raw, start) == pytest.approx(expected)
    assert benchmark.candle_mid(list(reversed(candles)), start) == pytest.approx(
        expected
    )
    assert benchmark.candle_mid(candles, "2000-01-01T00:00:00Z") is None


def test_candle_missing_closes_and_cutoff():
    candles = [
        {"end_period_ts": 10, "yes_bid": {"close": "0.2"}, "yes_ask": {"close": "0.4"}},
        {"end_period_ts": 20, "yes_bid": {"close": "0.8"}, "yes_ask": {}},
        {"end_period_ts": 30, "yes_bid": {"close": "0.8"}, "yes_ask": {"close": "1.0"}},
    ]
    assert benchmark.candle_mid(candles, "1970-01-01T00:00:20Z") == pytest.approx(0.3)


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "tiny.db"
    with sqlite3.connect(path) as conn:
        conn.executescript("""
            CREATE TABLE events(event_id PRIMARY KEY, section, international, region, excluded DEFAULT 0);
            CREATE TABLE teams(team_id PRIMARY KEY, name);
            CREATE TABLE matches(match_id PRIMARY KEY, event_id, start_utc, best_of, team1_id, team2_id, score1, score2, winner);
            CREATE TABLE maps(game_id PRIMARY KEY, match_id, "order", map, score1, score2);
            CREATE TABLE player_maps(game_id, player_id, team);
            CREATE TABLE kalshi_markets(ticker, series, event_ticker, kind, competitor_id, open_time);
            CREATE TABLE team_aliases(competitor_id, liquipedia_team_id);
            CREATE TABLE kalshi_links(event_ticker, match_id, game_id, kind, method, reason);
            INSERT INTO events VALUES (1, 'tier1', 1, NULL, 0), (99, 'unknown', 0, NULL, 0);
            INSERT INTO teams VALUES (10, 'A'), (20, 'B');
        """)
        for match_id, start, best_of, winner, wins in (
            (1, "2023-01-01T00:00:00Z", 1, 1, [1]),
            (2, "2024-01-01T00:00:00Z", 3, 1, [1, 0, 1]),
            (3, "2026-10-31T23:00:00Z", 2, None, [1, 0]),
            (4, "2026-11-01T00:00:00Z", 1, 2, [0]),
            (5, "2026-11-02T00:00:00Z", None, 1, [1]),
        ):
            conn.execute(
                "INSERT INTO matches VALUES (?, ?, ?, ?, 10, 20, ?, ?, ?)",
                (
                    match_id,
                    1 if match_id != 3 else 99,
                    start,
                    best_of,
                    sum(wins),
                    len(wins) - sum(wins),
                    winner,
                ),
            )
            for order, won in enumerate(wins, 1):
                conn.execute(
                    """INSERT INTO maps(game_id,match_id,"order",map,score1,score2)
                       VALUES (?, ?, ?, 'Mirage', ?, ?)""",
                    (
                        match_id * 10 + order,
                        match_id,
                        order,
                        13 if won else 8,
                        8 if won else 13,
                    ),
                )
        conn.executemany(
            "INSERT INTO player_maps(game_id,player_id,team) VALUES (?,?,?)",
            [
                (game_id, side * 100 + starter, side)
                for (game_id,) in conn.execute("SELECT game_id FROM maps")
                for side in (1, 2)
                for starter in range(5)
            ],
        )
        for competitor, team in (("a", 10), ("b", 20), ("other", 99)):
            conn.execute(
                "INSERT INTO team_aliases(competitor_id,liquipedia_team_id) VALUES (?,?)",
                (competitor, team),
            )
        for event, kind, game_id in (("S", "series", None), ("M", "map", 22)):
            conn.execute(
                "INSERT INTO kalshi_links VALUES (?,2,?,?, 'exact', NULL)",
                (event, game_id, kind),
            )
            for competitor in ("a", "b", "other", "unresolved"):
                conn.execute(
                    "INSERT INTO kalshi_markets(ticker,series,event_ticker,kind,competitor_id) VALUES (?,?,?,?,?)",
                    (event + competitor, "KXCS2GAME", event, kind, competitor),
                )
    directory = tmp_path / "data/kalshi/candles"
    directory.mkdir(parents=True)
    for event in ("S", "M"):
        for competitor, mid in (
            ("a", 0.7),
            ("b", 0.4),
            ("other", 0.9),
            ("unresolved", 0.1),
        ):
            with gzip.open(directory / f"{event + competitor}.json.gz", "wt") as handle:
                json.dump(
                    [
                        {
                            "end_period_ts": 1672531200,
                            "yes_bid": {"close_dollars": str(mid - 0.01)},
                            "yes_ask": {"close_dollars": str(mid + 0.01)},
                        }
                    ],
                    handle,
                )
    return path, tmp_path / "data"


def test_load_series_and_market_pairing(database):
    path, data = database
    with sqlite3.connect(path) as conn:
        loaded = load_maps(conn)
        assert loaded.loc[loaded.game_id == 11, ["score1", "score2"]].iloc[
            0
        ].tolist() == [13, 8]
        lineups = load_lineups(conn)
        assert lineups[11] == (tuple(range(100, 105)), tuple(range(200, 205)))
        assert set(lineups) == set(loaded.game_id)
        maps = replay(loaded, TeamEloModel())
        assert list(maps.game_id) == [11, 21, 22, 23, 31, 32, 41, 51]
        assert set(maps[maps.match_id == 3].section) == {"unknown"}
        assert set(maps[maps.match_id == 3].international) == {0}
        series = benchmark.series_rows(maps)
        assert list(series.match_id) == [1, 2, 4]
        first = maps[maps.match_id == 2].iloc[0]
        assert series[series.match_id == 2].p.iloc[0] == pytest.approx(
            series_probability(first.p, 3)
        )
        market = benchmark.kalshi_rows(conn, maps, series, data / "kalshi")
        assert len(market) == 2
        assert set(market.ticker) == {"Sa", "Ma"}
        assert set(market.quote_ts) == {1672531200}
        assert market.market_p.tolist() == pytest.approx([0.7, 0.7])
        assert market.ask.tolist() == pytest.approx([0.71, 0.71])
        assert market.bid.tolist() == pytest.approx([0.69, 0.69])
        map_row = market[market.kind == "map"].iloc[0]
        # Map markets are compared with the pre-match chance (first map of match 2).
        assert map_row.p == maps[maps.game_id == 21].p.iloc[0]
        assert map_row.won == 0
        (data / "kalshi/candles/Ma.json.gz").unlink()
        market = benchmark.kalshi_rows(conn, maps, series, data / "kalshi")
        assert market[market.kind == "map"].market_p.iloc[0] == pytest.approx(0.6)
        assert market[market.kind == "map"].ask.iloc[0] == pytest.approx(0.61)
        assert market[market.kind == "map"].bid.iloc[0] == pytest.approx(0.59)
        for candle in (data / "kalshi/candles").glob("*.json.gz"):
            candle.unlink()
        assert benchmark.kalshi_rows(conn, maps, series, data / "kalshi").empty
        conn.execute("DROP TABLE kalshi_links")
        assert benchmark.kalshi_rows(conn, maps, series, data / "kalshi").empty


def test_end_to_end_variants_and_weights(database, tmp_path, monkeypatch):
    path, data = database
    env = dict(os.environ, PROMCS_DATA=str(data))
    report_path = tmp_path / "report.md"
    command = [
        sys.executable,
        str(ROOT / "scripts/evaluate_elo.py"),
        "--db",
        str(path),
        "--quote",
        "prestart",
        "--out",
        str(report_path),
        "--tune-from",
        "2023-01-01",
        "--tune-to",
        "2024-01-01",
        "--validate-from",
        "2024-01-01",
        "--k-grid",
        "16,32",
        "--jobs",
        "2",
        "--models",
        "team_elo,team_round,player_binary_region",
        "--report-models",
        "team_elo,team_round,player_binary_region",
    ]
    result = subprocess.run(
        command, env=env, text=True, capture_output=True, check=True
    )
    report = report_path.read_text()
    assert "## Holdout" not in report
    assert "Holdout maps=" not in result.stdout
    assert "### Leaderboard" in report
    assert "Series blended Δ log loss" in report
    assert "Map blended flat ROI" in report
    assert "Map blended Kelly (LoL caps) $" in report
    assert report.count("#### Log loss vs Kalshi (blended)") == 6
    assert report.count("#### Full-Kelly returns (blended)") == 6
    assert "excluded from blended tables: 2 rows" in report
    assert "| 2024-01 | series | 0 | 1.000000 | 0.000000 | unfitted |" in report
    blended = report.split("#### Log loss vs Kalshi (blended)")[1]
    assert "| series | all | 0 |" in blended
    assert "| team_elo | all | 5 |" in report
    assert "| team_elo | all | 1 |" in report
    for name in ("team_elo", "team_round", "player_binary_region"):
        assert f"| {name} |" in report
        assert f"### {name}: Kalshi comparison and returns" in report
    assert "team_round − team_elo (paired log loss)" in report
    assert "player_binary_region − team_elo (paired log loss)" in report
    assert "Unknown host-region map rows: 6" in report
    assert "Total wall time:" in result.stdout
    assert len(result.stdout.splitlines()) <= 20
    # Redirect learned artifacts into scratch space, and run imported workers inline.
    monkeypatch.setattr(benchmark, "REPO", tmp_path)
    (tmp_path / "promcs/ratings").mkdir(parents=True)
    monkeypatch.setenv("PROMCS_DATA", str(data))
    args = command[2:] + ["--jobs", "1", "--write-weights"]
    selected = benchmark.main(args)
    weights = json.loads((tmp_path / "promcs/ratings/elo_weights.json").read_text())
    assert set(weights) == {"team_elo", "team_round", "player_binary_region"}
    for name, params in selected.items():
        assert weights[name] == {**params, "fit_through": "2023-01-01"}
    # Future rows must not affect the tuning leaderboard or chosen parameters.
    leaderboard = report.split("### Leaderboard")[1].split("Kalshi uses")[0]
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE maps SET score1=13,score2=1 WHERE match_id>=2")
        conn.execute("DROP TABLE kalshi_links")
    assert benchmark.main(args) == selected
    assert (
        report_path.read_text().split("### Leaderboard")[1].split("Kalshi uses")[0]
        == leaderboard
    )
    assert "Kalshi sections skipped" in report_path.read_text()


def test_empty_windows_and_invalid_selection(database, tmp_path, monkeypatch):
    path, data = database
    monkeypatch.setenv("PROMCS_DATA", str(data))
    with sqlite3.connect(path) as conn:
        tuning = benchmark.scored_rows(load_maps(conn), "2024-01-01")
        assert set(tuning.match_id) == {2, 3}
    args = [
        "--db",
        str(path),
        "--quote",
        "prestart",
        "--out",
        str(tmp_path / "report.md"),
        "--models",
        "team_elo",
        "--jobs",
        "1",
        "--k-grid",
        "32",
    ]
    for extra in (
        ["--tune-from", "2026-11-01"],
        ["--k-grid", "nan"],
        ["--validate-from", "2026-10-31T23:30:00"],
        ["--tune-to", "2026-02-01"],
        ["--validate-from", "2026-11-02"],
        ["--tune-to", "2024-01-01"],
        ["--seed-from", "2025-01-01"],
        ["--validate-from", "NaT"],
        ["--layers", "missing"],
        ["--score-from", "2024-01-01"],
        ["--models", "nonexistent"],
        ["--jobs", "0"],
        ["--blend-min", "0"],
    ):
        with pytest.raises(SystemExit) as error:
            benchmark.main(args + extra)
        assert error.value.code == 2


def test_baseline_always_included(database, tmp_path, monkeypatch):
    path, data = database
    monkeypatch.setenv("PROMCS_DATA", str(data))
    selected = benchmark.main(
        [
            "--db",
            str(path),
            "--quote",
            "prestart",
            "--out",
            str(tmp_path / "report.md"),
            "--models",
            "team_round",
            "--report-models",
            "team_elo,team_round",
            "--jobs",
            "1",
            "--k-grid",
            "32",
        ]
    )
    assert set(selected) == {"team_elo", "team_round"}
    assert "| coin | all | 3 |" in (tmp_path / "report.md").read_text()


def test_glicko_report_default_and_explicit_models(
    database, tmp_path, monkeypatch, capsys
):
    path, data = database
    monkeypatch.setenv("PROMCS_DATA", str(data))
    # Exercise actual registry factories with a small grid in the synthetic DB.
    for name in ("player_round_glicko", "player_round_region_glicko"):
        monkeypatch.setitem(
            benchmark.PARAM_GRIDS,
            name,
            {key: (values[0],) for key, values in benchmark.PARAM_GRIDS[name].items()},
        )
    out = tmp_path / "glicko.md"
    args = [
        "--db",
        str(path),
        "--quote",
        "prestart",
        "--out",
        str(out),
        "--models",
        "team_elo",
        "--jobs",
        "1",
        "--k-grid",
        "12",
    ]
    selected = benchmark.main(args)
    assert set(selected) == {
        "team_elo",
        "player_round_glicko",
    }
    report = out.read_text()
    assert report.index("## Combined summary") < report.index("### Leaderboard")
    assert report.count("#### Log loss vs Kalshi\n") == 4
    assert report.count("#### Full-Kelly returns\n") == 4
    assert "| series | tier1 |" in report and "| map | international=0 |" in report
    assert "frozen stage-1" in report and "unrounded" in report
    assert "depth-capped returns" in report
    assert "unplayed maps are not in the rows" in report
    printed = capsys.readouterr().out
    assert "Series flat ROI" in printed and "Map Kelly (LoL caps) $" in printed
    assert len(printed.splitlines()) <= 20
    selected = benchmark.main(args + ["--report-models", "team_elo,team_elo"])
    assert set(selected) == {"team_elo"}
    assert out.read_text().count("#### Full-Kelly returns\n") == 2
    with pytest.raises(SystemExit):
        benchmark.main(args + ["--report-models", "unknown"])


def test_blend_recovers_coefficients_and_team_symmetry():
    rng = np.random.default_rng(42)
    mid, p = rng.uniform(0.05, 0.95, (2, 80000))
    expected = (0.8, 0.35)
    probability = combine(p, mid, *expected)
    won = rng.binomial(1, probability)
    a, b, n = fit(p, mid, won)
    assert (a, b) == pytest.approx(expected, abs=0.025)
    assert n == len(won)
    assert combine(p, mid) == pytest.approx(mid)
    assert combine(1 - p, 1 - mid, a, b) == pytest.approx(1 - combine(p, mid, a, b))
    assert combine([0, 1], [0, 1]) == pytest.approx([0.01, 0.99])
    # Collinearity and complete separation still produce finite fits.
    assert np.isfinite(fit([0.8] * 20, [0.8] * 20, [1] * 20)).all()


def test_blend_walk_forward_boundaries_kinds_and_exclusion():
    records = []
    for month in ("2023-12", "2024-01", "2024-02", "2024-03", "2026-11", "2026-12"):
        for kind in ("series", "map"):
            for i in range(12):
                records.append(
                    {
                        "start_utc": f"{month}-01T00:00:00Z",
                        "kind": kind,
                        "p": 0.2 + (i % 4) * 0.2,
                        "market_p": 0.3 + (i % 3) * 0.2,
                        "won": int(i % 3 == (0 if kind == "series" else 1)),
                        "section": "tier1",
                        "international": 0,
                        "match_id": len(records),
                        "ask": 0.51,
                        "bid": 0.49,
                    }
                )
    frame = pd.DataFrame(records).sample(frac=1, random_state=4)
    rows, snapshots = walk_forward(frame, "2024-01-01", min_rows=12)
    dates = pd.to_datetime(rows.start_utc, utc=True)
    january = rows[dates.dt.strftime("%Y-%m") == "2024-01"]
    assert not january.blend_fitted.any()
    assert (january.blend_n == 0).all()
    assert january.p_blend.tolist() == january.market_p.tolist()
    for kind in ("series", "map"):
        training = frame[
            (frame.start_utc.str.startswith("2024-01")) & (frame.kind == kind)
        ]
        expected = fit(training.p, training.market_p, training.won)
        february = rows[(dates.dt.month == 2) & (rows.kind == kind)]
        assert february.blend_a.tolist() == pytest.approx([expected[0]] * 12)
        assert february.blend_b.tolist() == pytest.approx([expected[1]] * 12)
        assert (february.blend_n == 12).all()
    fits = snapshots[snapshots.month == "2024-02"]
    assert fits.a.nunique() == 2
    # Changing same-month/later labels must not change February predictions.
    changed = frame.copy()
    changed.loc[changed.start_utc >= "2024-02", "won"] = 1
    later, _ = walk_forward(changed, "2024-01-01", min_rows=12)
    february = dates.dt.strftime("%Y-%m") == "2024-02"
    assert (
        rows.loc[february, "p_blend"].tolist()
        == later.loc[february, "p_blend"].tolist()
    )
    # Even August snapshots never train on July holdout outcomes.
    assert (snapshots[snapshots.month == "2026-12"].n == 36).all()
    january_losses, january_returns = benchmark.market_tables(
        january, probability="p_blend"
    )
    assert "| series | all | 0 | — |" in january_losses
    assert "| series | all | 0 | 0 |" in january_returns
    losses, _ = benchmark.market_tables(rows, probability="p_blend")
    assert (
        f"| series | all | {sum(rows.blend_fitted & (rows.kind == 'series'))} |"
        in losses
    )
    summary = benchmark.summary_table({"test": january})
    assert "Series blended Δ log loss" in summary
    assert summary.splitlines()[-1].endswith(
        "— | — | $50.00 | — | $50.00 | — | — | $50.00 | — | $50.00 |"
    )
    with pytest.raises(ValueError):
        walk_forward(frame, min_rows=0)


def test_end_to_end_fitted_blend(database, tmp_path, monkeypatch):
    path, data = database
    monkeypatch.setenv("PROMCS_DATA", str(data))
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE matches SET start_utc='2024-02-01T00:00:00Z',best_of=3,winner=1 WHERE match_id=3"
        )
        for event, kind, game_id in (("S2", "series", None), ("M2", "map", 31)):
            conn.execute(
                "INSERT INTO kalshi_links VALUES (?,3,?,?,'exact',NULL)",
                (event, game_id, kind),
            )
            conn.execute(
                "INSERT INTO kalshi_markets(ticker,series,event_ticker,kind,competitor_id) VALUES (?,?,?,?,?)",
                (event + "a", "KXCS2GAME", event, kind, "a"),
            )
            candles = data / "kalshi/candles"
            (candles / f"{event}a.json.gz").write_bytes(
                (candles / f"{event[0]}a.json.gz").read_bytes()
            )
    report_path = tmp_path / "fitted.md"
    benchmark.main(
        [
            "--db",
            str(path),
            "--quote",
            "prestart",
            "--out",
            str(report_path),
            "--models",
            "team_elo",
            "--report-models",
            "team_elo",
            "--jobs",
            "1",
            "--k-grid",
            "32",
            "--blend-min",
            "1",
            "--tune-from",
            "2023-01-01",
            "--tune-to",
            "2024-01-01",
            "--validate-from",
            "2024-01-01",
        ]
    )
    report = report_path.read_text()
    fits = report.split("#### Monthly market blend fits")[1]
    assert "| 2024-02 | series | 1 |" in fits
    assert "| 2024-02 | map | 1 |" in fits
    assert fits.count("| fitted |") == 2
    assert "excluded from blended tables: 2 rows" in fits
    loss = report.split("#### Log loss vs Kalshi (blended)")[1]
    assert "| series | all | 1 |" in loss
    assert "| map | all | 1 |" in loss


def _candle(end, bid, ask):
    return {
        "end_period_ts": end,
        "yes_bid": {"close_dollars": f"{bid:.4f}"},
        "yes_ask": {"close_dollars": f"{ask:.4f}"},
    }


def test_tradeable_quote_is_first_tight_quote_before_veto_window():
    """The bot's price: first candle >=30 min after listing, spread <= max, and
    >=2 h before the scheduled start; never the pre-start (veto) candle."""
    opened = pd.Timestamp("2026-03-01T00:00:00Z")
    start = pd.Timestamp("2026-03-03T00:00:00Z")
    hour = 3600
    t0 = int(opened.timestamp())
    candles = [
        _candle(t0 + 0 * hour, 0.40, 0.45),  # before open + 30 min
        _candle(t0 + 1 * hour, 0.01, 0.95),  # empty book: spread too wide
        _candle(t0 + 2 * hour, 0.50, 0.55),  # first tradeable quote
        _candle(t0 + 3 * hour, 0.52, 0.54),
        _candle(int(start.timestamp()) - 1800, 0.70, 0.71),  # inside the 2 h buffer
    ]
    rule = benchmark.TRADEABLE
    assert benchmark.candle_quote(candles, start, opened, rule) == (0.50, 0.55)
    # The old rule takes the last candle before start, which may price the veto.
    assert benchmark.candle_quote(candles, start) == (0.70, 0.71)
    # No open time or no qualifying candle: skipped.
    assert benchmark.candle_quote(candles, start, None, rule) is None
    tight = benchmark.QuoteRule("tradeable", max_spread=0.01)
    assert benchmark.candle_quote(candles, start, opened, tight) is None


def test_stage_separation_layers_and_default_market_window(
    database, tmp_path, monkeypatch
):
    from promcs.ratings.layers import IdentityLayer, Layer

    path, data = database
    monkeypatch.setenv("PROMCS_DATA", str(data))
    fitted, applied, market_sources, market_rows = [], [], [], []

    class Shift(Layer):
        name = "shift"

        def fit(self, frame):
            assert self.context["conn"].execute("SELECT 1").fetchone() == (1,)
            assert self.context["lineups"]
            assert {
                "event_id",
                "match_id",
                "region",
                "section",
                "international",
                "team1_id",
                "team2_id",
            } <= set(frame)
            fitted.append(frame.copy())
            logits = np.log(frame.p / (1 - frame.p))
            self.shift = float(frame.won.mean() - logits.mean())

        def apply(self, frame):
            applied.append(frame.copy())
            return 1 / (1 + np.exp(-(np.log(frame.p / (1 - frame.p)) + self.shift)))

    monkeypatch.setitem(benchmark.LAYERS, "shift", Shift)
    original = benchmark.kalshi_rows

    def capture(conn, maps, series, directory, rule):
        market_sources.append(maps.copy())
        result = original(conn, maps, series, directory, rule)
        market_rows.append(result)
        return result

    monkeypatch.setattr(benchmark, "kalshi_rows", capture)
    # Add validation markets alongside the existing tuning-window markets.
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE matches SET best_of=3,winner=1 WHERE match_id=3")
        for event, kind, game_id in (("S3", "series", None), ("M3", "map", 31)):
            conn.execute(
                "INSERT INTO kalshi_links VALUES (?,3,?,?,'exact',NULL)",
                (event, game_id, kind),
            )
            conn.execute(
                "INSERT INTO kalshi_markets(ticker,series,event_ticker,kind,competitor_id) VALUES (?,?,?,?,?)",
                (event + "a", "KXCS2GAME", event, kind, "a"),
            )
            candles = data / "kalshi/candles"
            (candles / f"{event}a.json.gz").write_bytes(
                (candles / f"{event[0]}a.json.gz").read_bytes()
            )
    out = tmp_path / "layers.md"
    args = [
        "--db",
        str(path),
        "--out",
        str(out),
        "--models",
        "team_elo",
        "--report-models",
        "team_elo",
        "--layers",
        "none,shift",
        "--k-grid",
        "16,32",
        "--jobs",
        "1",
        "--quote",
        "prestart",
        "--holdout",
        # The temperature fit also applies layers to stage-1 rows; this test
        # checks only which rows each stage sees.
        "--no-series-temperature",
    ]
    selected = benchmark.main(args)
    assert len(fitted) == len(applied) == 1
    assert set(fitted[0].match_id) == {2}
    assert set(applied[0].match_id) == {3, 4, 5}
    assert all(set(frame.match_id) == {3, 4, 5} for frame in market_sources)
    assert all(set(frame.match_id) == {3} for frame in market_rows)
    pd.testing.assert_frame_equal(market_sources[0], market_sources[1])
    assert not market_sources[0].p.equals(market_sources[2].p)
    pd.testing.assert_series_equal(IdentityLayer().apply(fitted[0]), fitted[0].p)
    report = out.read_text()
    assert "team_elo+shift − team_elo" in report
    assert "### team_elo+shift: Kalshi comparison and returns" in report
    assert "## Holdout" in report
    stage1 = report.split("## Stage 1")[1].split("## Stage 2")[0]
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE maps SET score1=1,score2=13 WHERE match_id>=3")
    assert benchmark.main(args) == selected
    assert out.read_text().split("## Stage 1")[1].split("## Stage 2")[0] == stage1


def test_monthly_counts_and_identical_rows():
    frame = pd.DataFrame(
        [
            {
                "kind": kind,
                "start_utc": f"2025-{month}-02T00:00:00Z",
                "p": 0.8,
                "market_p": 0.6,
                "p_blend": 0.7,
                "blend_fitted": True,
                "won": i % 2,
                "ask": 0.61,
                "bid": 0.59,
                "match_id": i,
            }
            for i, (kind, month) in enumerate(
                [("map", "09"), ("map", "09"), ("map", "10"), ("series", "10")]
            )
        ]
    )
    table = benchmark.monthly_table(frame)
    parsed = [line.split("|")[1:-1] for line in table.splitlines()[2:]]
    for kind in ("map", "series"):
        assert sum(int(row[2]) for row in parsed if row[0].strip() == kind) == sum(
            frame.kind == kind
        )
    september = next(row for row in parsed if row[1].strip() == "2025-09")
    rows = frame[frame.start_utc.str.startswith("2025-09")]
    assert float(september[3]) == pytest.approx(benchmark.mean_loss(rows), abs=1e-6)
    assert float(september[4]) == pytest.approx(
        game_losses(rows.p_blend, rows.won).log_loss.mean(), abs=1e-6
    )
    assert float(september[5]) == pytest.approx(
        game_losses(rows.market_p, rows.won).log_loss.mean(), abs=1e-6
    )


def test_blend_default_validation_start():
    frame = pd.DataFrame(
        [
            {
                "start_utc": f"{month}-15T00:00:00Z",
                "kind": "map",
                "p": 0.7,
                "market_p": 0.6,
                "won": won,
            }
            for month, won in (
                ("2025-12", 0),
                ("2026-01", 1),
                ("2026-02", 0),
                ("2026-11", 1),
                ("2026-12", 0),
            )
        ]
    )
    rows, fits = walk_forward(frame, min_rows=1)
    assert fits.n.tolist() == [0, 0, 1, 2, 2]
    assert rows.blend_fitted.tolist() == [False, False, True, True, True]


@pytest.mark.parametrize("mode,hours", [("hours24", 24), ("hours6", 6)])
def test_fixed_hours_quote_latest_eligible(mode, hours):
    start = pd.Timestamp("2026-01-03T00:00:00Z")
    cutoff = int((start - pd.Timedelta(hours=hours)).timestamp())
    candles = [
        _candle(cutoff - 3600, 0.4, 0.45),
        _candle(cutoff, 0.5, 0.55),
        _candle(cutoff + 1, 0.6, 0.65),
    ]
    opened = (start - pd.Timedelta(days=2)).isoformat()
    rule = benchmark.QuoteRule(mode)
    assert benchmark.candle_quote(candles, start, opened, rule) == (0.5, 0.55)
    for missing in (None, float("nan"), pd.NaT, ""):
        assert benchmark.candle_quote(candles, start, missing, rule) is None
    assert (
        benchmark.candle_quote(
            candles, start, pd.Timestamp(cutoff, unit="s", tz="UTC"), rule
        )
        is None
    )
    assert (
        benchmark.candle_quote([_candle(cutoff, 0.3, 0.8)], start, opened, rule) is None
    )


def test_robustness_table_rows():
    frames = {
        (mode, "model"): pd.DataFrame() for mode in ("tradeable", "hours24", "hours6")
    }
    table = benchmark.robustness_table(frames)
    assert len(table.splitlines()) == 8
    for mode in ("tradeable", "hours24", "hours6"):
        assert f"| {mode} | model | series | 0 |" in table
        assert f"| {mode} | model | map | 0 |" in table


def test_series_check_planted_dependence():
    from scripts.series_independence import series_check

    records = []
    for match in range(120):
        first_won = match % 2
        wins = [first_won, first_won, 1 - first_won]
        for order, won in enumerate(wins, 1):
            records.append(
                {
                    "match_id": match,
                    "order": order,
                    "start_utc": "2026-01-01T00:00:00Z",
                    "best_of": 3 if match < 100 else 5,
                    "p": 0.5,
                    "won": won,
                    "series_won": first_won,
                }
            )
    result = series_check(pd.DataFrame(records), n_resamples=300)
    assert result["rows"] == result["bins"].rows.sum() == 120
    assert result["dependence"][1]["mean"] == 0.5
    assert result["dependence"][0]["mean"] == -0.5
    assert result["contrast_interval"][0] > 0
    assert len(result["summary"].splitlines()) <= 15
    assert np.isfinite(result["log_loss"][3])


def test_robustness_and_series_report_reuse_frozen_models(
    database, tmp_path, monkeypatch
):
    path, data = database
    monkeypatch.setenv("PROMCS_DATA", str(data))
    calls = []
    original = benchmark.tune_candidate

    def counted(task):
        calls.append(task)
        return original(task)

    monkeypatch.setattr(benchmark, "tune_candidate", counted)
    out = tmp_path / "robust.md"
    args = [
        "--db",
        str(path),
        "--out",
        str(out),
        "--models",
        "team_elo",
        "--report-models",
        "team_elo",
        "--layers",
        "none",
        "--jobs",
        "1",
        "--k-grid",
        "16",
        "--tune-from",
        "2023-01-01",
        "--tune-to",
        "2024-01-01",
        "--validate-from",
        "2024-01-01",
        "--quote",
        "prestart",
        "--robustness",
        "--series-check",
    ]
    benchmark.main(args)
    assert len(calls) == 1  # Each quote rule uses the already selected replay.
    report = out.read_text()
    table = report.split("## Quote-time robustness")[1].split("## Series independence")[
        0
    ]
    assert (
        len([line for line in table.splitlines() if line.startswith("| tradeable")])
        == 4
    )
    for mode in ("tradeable", "hours24", "hours6"):
        assert f"| {mode} | team_elo | map |" in table
        assert f"| {mode} | team_elo+none | series |" in table
    assert "## Series independence: team_elo" in report
    assert "Bets filled" in report and "unfilled" in report
    assert "Flat ROI depth-capped [95% interval]" in report


def test_series_decider_window_first_map_probability_and_empty():
    from scripts.series_independence import series_check

    frame = pd.DataFrame(
        [
            {
                "match_id": match,
                "order": order,
                "p": p,
                "won": won,
                "best_of": 3,
                "series_won": 1,
                "start_utc": start,
            }
            for match, start in [
                (1, "2026-01-01T00:00:00Z"),
                (2, "2026-11-01T00:00:00Z"),
            ]
            for order, p, won in [(1, 0.2, 1), (2, 0.9, 0), (3, 0.7, 1)]
        ]
    )
    result = series_check(frame.sample(frac=1, random_state=0), n_resamples=20)
    assert result["rows"] == 1
    assert result["bins"].rows.sum() == 1
    assert result["bins"].query("rows == 1").predicted.iloc[0] == pytest.approx(
        series_probability(0.2, 3)
    )
    assert result["dependence"][1]["mean"] == pytest.approx(-0.9)
    assert result["decider"]["mean"] == pytest.approx(0.3)
    empty = series_check(frame.iloc[:0], n_resamples=20)
    assert empty["rows"] == empty["bins"].rows.sum() == 0
    assert empty["decider"]["rows"] == 0


def test_series_standalone_cli(database, tmp_path):
    path, _ = database
    out = tmp_path / "series.md"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/series_independence.py"),
            "--db",
            str(path),
            "--from",
            "2024-01-01",
            "--to",
            "2025-01-01",
            "--params",
            '{"k": 16}',
            "--out",
            str(out),
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    assert len(result.stdout.splitlines()) <= 15
    assert "Series independence" in result.stdout
    assert "Probability bin" in out.read_text()


def test_robustness_table_populated_metrics():
    frame = pd.DataFrame(
        [
            {
                "kind": "series",
                "match_id": 1,
                "start_utc": "2026-01-01T00:00:00Z",
                "p": 0.8,
                "p_blend": 0.7,
                "blend_fitted": True,
                "won": 1,
                "market_p": 0.6,
                "ask": 0.5,
                "bid": 0.4,
                "depth1": 2,
                "depth2": 0,
            }
        ]
    )
    table = benchmark.robustness_table({("hours6", "model"): frame})
    cells = table.splitlines()[2].split("|")[1:-1]
    assert float(cells[4]) == pytest.approx(-np.log(0.8) + np.log(0.6), abs=1e-6)
    assert float(cells[5]) == pytest.approx(-np.log(0.7) + np.log(0.6), abs=1e-6)
    assert cells[6].strip() == cells[7].strip() == "92.31%"


def test_series_temperature_fit_and_apply():
    import numpy as np

    rng = np.random.default_rng(0)
    n = 4000
    p_map = rng.uniform(0.2, 0.8, n)
    raw = np.array([series_probability(p, 3) for p in p_map])
    truth = benchmark.temper(raw, 0.7)  # planted: real odds are softer
    frame = pd.DataFrame(
        {
            "match_id": np.arange(n),
            "game_id": np.arange(n),
            "best_of": 3,
            "p": p_map,
            "series_won": (rng.uniform(size=n) < truth).astype(float),
            "start_utc": "2024-06-01T00:00:00Z",
        }
    )
    temps = benchmark.fit_series_temperature(frame)
    assert temps[1] == 1.0 and abs(temps[3] - 0.7) <= 0.06
    tempered = benchmark.series_rows(benchmark.with_series_temperature(frame, temps))
    untempered = benchmark.series_rows(frame)
    assert np.allclose(tempered.p, benchmark.temper(untempered.p, temps[3]))
    # Few rows: no temperature.
    assert benchmark.fit_series_temperature(frame.head(10))[3] == 1.0


def test_excluded_events_do_not_load(database):
    path, _ = database
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE events SET excluded=1 WHERE event_id=1")
        maps = load_maps(conn)
    assert maps.match_id.tolist() == [3, 3]


def test_outcome_report_without_kalshi_tables(database, tmp_path, capsys):
    path, _ = database
    with sqlite3.connect(path) as conn:
        for table in ("kalshi_links", "kalshi_markets", "team_aliases"):
            conn.execute(f"DROP TABLE {table}")
    out = tmp_path / "outcomes.md"
    selected = benchmark.main(
        [
            "--db",
            str(path),
            "--out",
            str(out),
            "--models",
            "team_elo",
            "--report-models",
            "team_elo",
            "--k-grid",
            "32",
            "--jobs",
            "1",
            "--layers",
            "regional",
            "--robustness",
        ]
    )
    report = out.read_text()
    assert set(selected) == {"team_elo"}
    assert "Stage 1 — tuning (outcomes)" in report
    assert "Stage 2 — validation (outcomes)" in report
    assert "team_elo+regional" in report
    assert "| team_elo | all | 3 |" in report
    assert "| team_elo | all | 2 |" in report
    assert "Kalshi sections skipped: missing tables" in report
    assert "Kalshi sections skipped: missing tables" in capsys.readouterr().out
    assert "#### Full-Kelly returns" not in report
    assert "## Holdout" not in report
