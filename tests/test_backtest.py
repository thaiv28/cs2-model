"""Hand cases for after-fee selection, simultaneous stakes, and match bootstrap."""

import numpy as np
import pandas as pd
import pytest

from promcs.backtest import (
    LOL_SIZING,
    capped_path,
    depth_limits,
    fee,
    kelly_path,
    order_fee,
    select_bets,
    summarize,
)


def rows(*updates):
    defaults = {
        "match_id": 1,
        "start_utc": "2026-01-01T00:00:00Z",
        "p": 0.8,
        "won": 1,
        "ask": 0.5,
        "bid": 0.4,
    }
    return pd.DataFrame([{**defaults, **update} for update in updates])


def test_fee_edge_fraction_and_flat_profit():
    bet = select_bets(rows({})).iloc[0]
    assert fee(0.5) == pytest.approx(0.0175)
    assert bet["side"] == 1
    assert bet["cost"] == pytest.approx(0.5175)
    assert bet["edge"] == pytest.approx(0.2825)
    assert bet["fraction"] == pytest.approx(0.2825 / 0.4825)
    assert bet["profit"] == pytest.approx(0.96)
    assert bet["outlay"] == 1.04


def test_side_choice_and_no_positive_edge():
    bets = select_bets(rows({"p": 0.1, "won": 0}, {"p": 0.5}))
    assert len(bets) == 1
    bet = bets.iloc[0]
    assert bet["side"] == 2
    assert bet["price"] == pytest.approx(0.6)
    assert bet["edge"] == pytest.approx(0.9 - 0.6 - fee(0.6))
    assert bet["side_won"] == 1
    crossed = select_bets(rows({"ask": 0.2, "bid": 0.8, "p": 0.4}))
    assert crossed.iloc[0]["side"] == 2


def test_skip_missing_and_boundary_quotes():
    frame = rows(
        {"ask": None},
        {"bid": None},
        {"ask": 0},
        {"bid": 1},
        {"bid": 0},
        {"ask": 1},
        {"ask": "bad"},
        {},
    )
    assert len(select_bets(frame)) == 1
    assert select_bets(frame.drop(columns="bid")).empty
    assert summarize(frame.iloc[:0])["bankroll"] == 50
    empty = summarize(pd.DataFrame())
    assert empty["bets"] == empty["matches"] == 0
    assert empty["bankroll"] == 50
    assert np.isnan(empty["flat_roi"])


def test_same_match_stakes_scaled_from_prematch_bankroll():
    bets = select_bets(rows({}, {}))
    assert bets["fraction"].sum() > 1
    path, drawdown, largest = kelly_path(bets)
    assert largest == pytest.approx(24.15)
    assert path == pytest.approx([50, 96.60])
    assert drawdown == 0


def test_three_match_path_and_drawdown_in_start_order():
    frame = rows(
        {"match_id": 3, "start_utc": "2026-01-03T00:00:00Z"},
        {"match_id": 1},
        {"match_id": 2, "start_utc": "2026-01-02T00:00:00Z", "won": 0},
    )
    fraction = 0.2825 / 0.4825
    expected = [50.0]
    stakes = []
    for won in (1, 0, 1):
        budget = expected[-1] * fraction
        # At price .50 the rounded fees for these cash budgets are hand cases.
        charge = (0.99, 1.54, 0.64)[len(stakes)]
        stake = budget - charge
        stakes.append(stake)
        expected.append(
            expected[-1] + stake * (2 * won - 1) - order_fee(stake / 0.5, 0.5)
        )
    path, drawdown, largest = kelly_path(select_bets(frame))
    assert path == pytest.approx(expected)
    assert drawdown == pytest.approx((expected[1] - expected[2]) / expected[1])
    assert largest == pytest.approx(stakes[1])
    result = summarize(frame, sizing="full")
    assert result["bankroll"] == pytest.approx(expected[-1])
    assert result["multiple"] == pytest.approx(expected[-1] / 50)
    assert result["matches"] == 3


def test_roi_interval_resamples_whole_matches_deterministically():
    # Unequal match sizes and mixed outcomes distinguish this interval from
    # resampling individual bets.
    updates = [
        {"match_id": match_id, "won": int(match_id % 3 != 0)}
        for match_id in range(10)
        for _ in range(match_id % 4 + 1)
    ]
    frame = rows(*updates)
    first = summarize(frame)
    assert first == summarize(frame)
    win_profit = 0.96
    counts = np.array([match_id % 4 + 1 for match_id in range(10)])
    sums = counts * np.array(
        [win_profit if match_id % 3 != 0 else -1.04 for match_id in range(10)]
    )
    rng = np.random.default_rng(0)
    expected = []
    for _ in range(2000):
        picks = rng.integers(0, 10, 10)
        expected.append(sums[picks].sum() / (1.04 * counts[picks].sum()))
    assert first["flat_roi"] == pytest.approx(sums.sum() / (1.04 * counts.sum()))
    assert (first["roi_low"], first["roi_high"]) == pytest.approx(
        np.percentile(expected, [2.5, 97.5])
    )


def test_alternative_probability_selects_and_sizes_blended_bets():
    frame = rows({"p_blend": 0.1}, {"p_blend": 0.5})
    bets = select_bets(frame, probability="p_blend")
    assert len(bets) == 1
    assert bets.iloc[0]["side"] == 2
    expected = frame.copy()
    expected["p"] = frame.p_blend
    assert summarize(frame, probability="p_blend") == summarize(expected)


def _bets(rows):
    """rows: (match_id, start_utc, fraction, profit)."""
    return pd.DataFrame(rows, columns=["match_id", "start_utc", "fraction", "profit"])


def test_capped_path_fixture_cap_and_start_of_day_capital():
    # Full Kelly would stake 40%; the fixture cap is 10% of capital.
    path, _, largest = capped_path(_bets([(1, "2026-03-01T10:00Z", 0.4, 1.0)]))
    assert largest == pytest.approx(5.0)
    assert path[-1] == pytest.approx(55.0)
    # Two matches on one day are both sized from the day's opening capital.
    path, _, _ = capped_path(
        _bets(
            [
                (1, "2026-03-01T10:00Z", 0.1, 1.0),
                (2, "2026-03-01T15:00Z", 0.1, -1.0),
            ]
        )
    )
    assert path == pytest.approx([50.0, 50.0])


def test_capped_path_dollar_caps_and_stop_at_zero():
    big = dict(LOL_SIZING, fixture_fraction=1.0)
    _, _, largest = capped_path(
        _bets([(1, "2026-03-01T10:00Z", 1.0, 0.0)]), initial=10_000, sizing=big
    )
    assert largest == pytest.approx(250.0)  # order and fixture caps
    lose_all = dict(LOL_SIZING, fixture_fraction=1.0)
    path, drawdown, _ = capped_path(
        _bets(
            [
                (1, "2026-03-01T10:00Z", 1.0, -1.0),
                (2, "2026-03-02T10:00Z", 0.5, 1.0),
            ]
        ),
        sizing=lose_all,
    )
    assert path == pytest.approx([50.0, 0.0, 0.0])  # no orders once capital is $0
    assert drawdown == pytest.approx(1.0)


@pytest.mark.parametrize(
    "contracts,price,expected",
    [(1, 0.5, 0.02), (2, 0.5, 0.04), (4, 0.5, 0.07), (0, 0.5, 0), (1, 0.01, 0.01)],
)
def test_order_fee_cent_ceiling(contracts, price, expected):
    assert order_fee(contracts, price) == expected


def test_depth_window_prices_orientation_and_missing(tmp_path):
    import gzip
    import json

    directory = tmp_path / "trades"
    directory.mkdir()
    trades = [
        (0, 2, 0.5),
        (3600, 4, 0.4),
        (21600, 8, 0.6),
        (21601, 100, 0.5),
        (-1, 100, 0.5),
    ]
    with gzip.open(directory / "T.jsonl.gz", "wt") as handle:
        for ts, count, price in trades:
            handle.write(
                json.dumps(
                    {
                        "created_time": pd.Timestamp(
                            ts, unit="s", tz="UTC"
                        ).isoformat(),
                        "count_fp": str(count),
                        "yes_price_dollars": str(price),
                        "taker_side": "yes",
                    }
                )
                + "\n"
            )
    frame = rows(
        {"ticker": "T", "quote_ts": 0, "team1_side": True},
        {"ticker": "T", "quote_ts": 0, "team1_side": False},
        {"ticker": "absent", "quote_ts": 0, "team1_side": True},
    )
    depth = depth_limits(frame, tmp_path, share=0.5)
    assert depth.depth1.tolist() == [3, 5, 0]
    assert depth.depth2.tolist() == [7, 7, 0]
    stats = summarize(depth, depth=True)
    assert stats["bets"] == 2 and stats["unfilled"] == 1
    shallow = depth_limits(frame.iloc[:1], tmp_path, share=0.1)
    assert summarize(shallow, depth=True)["unfilled"] == 1
    assert summarize(frame.iloc[2:], depth=True)["bankroll"] == 50


def test_kelly_depth_cap_and_rounded_cash_budget():
    frame = rows({"depth1": 1, "depth2": 0})
    stats = summarize(frame, depth=True)
    assert stats["bets"] == 0 and stats["unfilled"] == 1
    assert stats["largest_stake"] == 0.5
    assert stats["bankroll"] == pytest.approx(50.48)
    # Full-Kelly simultaneous orders share fee-inclusive cash proportionately.
    bets = select_bets(rows({}, {}))
    path, _, stake = kelly_path(bets, initial=1)
    assert 2 * (stake + order_fee(stake / 0.5, 0.5)) <= 1 + 1e-12
    assert path[-1] >= 0


def test_flat_roi_uses_total_cash_for_unequal_rounded_fees():
    frame = rows({}, {"match_id": 2, "ask": 0.25, "bid": 0.2, "won": 0})
    # Win: 2 contracts, .04 fee, .96 profit. Loss: 4 contracts, .06 fee.
    stats = summarize(frame, n_resamples=100)
    assert stats["flat_roi"] == pytest.approx((0.96 - 1.06) / (1.04 + 1.06))
    draws = np.random.default_rng(0).integers(0, 2, (100, 2))
    expected = np.array([0.96, -1.06])[draws].sum(axis=1) / np.array([1.04, 1.06])[
        draws
    ].sum(axis=1)
    assert (stats["roi_low"], stats["roi_high"]) == pytest.approx(
        np.percentile(expected, [2.5, 97.5])
    )
    assert summarize(frame, depth=True)["unfilled"] == 2


def test_no_side_fill_and_custom_depth_window(tmp_path):
    import gzip
    import json

    (tmp_path / "trades").mkdir()
    with gzip.open(tmp_path / "trades/T.jsonl.gz", "wt") as handle:
        for ts, price, count in [
            (0, "0.40", "2.5"),
            (3600, "0.39", "50"),
            (3601, "0.50", "100"),
        ]:
            handle.write(
                json.dumps(
                    {
                        "created_time": pd.Timestamp(
                            ts, unit="s", tz="UTC"
                        ).isoformat(),
                        "yes_price_dollars": price,
                        "count_fp": count,
                        "taker_side": "no",
                    }
                )
                + "\n"
            )
    frame = rows({"ticker": "T", "quote_ts": 0, "team1_side": True, "p": 0.1})
    limited = depth_limits(frame, tmp_path, window_hours=1, share=1)
    assert limited.depth2.iloc[0] == 2.5
    assert summarize(limited, depth=True)["bets"] == 1
    assert select_bets(limited).side.iloc[0] == 2
    assert summarize(limited, depth=True)["largest_stake"] <= 2.5 * 0.6
