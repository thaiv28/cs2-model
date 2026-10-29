"""Kalshi taker backtest with rounded order fees and match-level settlement.

Quotes are oriented to CS2 team1. Fills assume the last pre-start hourly ask/bid,
with optional tape-based depth caps and no slippage. Each summary is an independent $50 path.
"""

import gzip
import json
from decimal import ROUND_CEILING, Decimal
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from promcs.evaluation import interval, resamples


def fee(cost):
    """Unrounded Kalshi taker fee per contract: 0.07 * c * (1 - c)."""
    return 0.07 * cost * (1 - cost)


def order_fee(contracts, price):
    """Dollar fee per order, rounded up using decimal arithmetic."""
    c, p = Decimal(str(contracts)), Decimal(str(price))
    return float(
        (Decimal("0.07") * c * p * (1 - p)).quantize(
            Decimal("0.01"), rounding=ROUND_CEILING
        )
    )


@lru_cache(maxsize=4096)
def _tape(path):
    if not Path(path).exists():
        return ()
    with gzip.open(path, "rt") as handle:
        return tuple(
            (
                pd.Timestamp(t["created_time"]).timestamp(),
                float(t["count_fp"]),
                float(t["yes_price_dollars"]),
            )
            for line in handle
            if (t := json.loads(line))
        )


def depth_limits(frame, directory, window_hours=6, share=0.5):
    """Attach available contracts on each oriented side; missing tapes never fill."""
    if not np.isfinite(window_hours) or window_hours < 0 or not 0 <= share <= 1:
        raise ValueError("depth window must be nonnegative and share in [0,1]")
    result = frame.copy()
    limits = {1: [], 2: []}
    for row in frame.itertuples():
        tape = _tape(str(Path(directory) / "trades" / f"{row.ticker}.jsonl.gz"))
        for side in (1, 2):
            yes = (side == 1) == row.team1_side
            price = row.ask if side == 1 else 1 - row.bid
            threshold = price if yes else 1 - price
            limits[side].append(
                share
                * sum(
                    count
                    for ts, count, p in tape
                    if row.quote_ts <= ts <= row.quote_ts + window_hours * 3600
                    and (p <= threshold + 1e-12 if yes else p >= threshold - 1e-12)
                )
            )
    for side in (1, 2):
        result[f"depth{side}"] = limits[side]
    return result


def _affordable(stake, price, budget):
    """Largest contract stake within a cash budget, fee charged on top."""
    lo, hi = 0.0, min(stake, budget)
    if hi + order_fee(hi / price, price) <= budget:
        return hi
    for _ in range(55):
        mid = (lo + hi) / 2
        if mid + order_fee(mid / price, price) <= budget:
            lo = mid
        else:
            hi = mid
    return lo


def _settle(match, stakes, budget):
    # Hand-built historical path fixtures have no price column.
    if "price" not in match:
        return (
            float(np.dot(stakes, match["profit"])),
            float(sum(stakes)),
            float(max(stakes, default=0)),
        )
    # Kelly fractions and execution limits are cash budgets. Convert each to
    # a contract stake with its own rounded fee, then apply available depth.
    stakes = np.array(
        [
            _affordable(target, price, target)
            for target, price in zip(stakes, match.price)
        ]
    )
    stakes = np.minimum(stakes, match.get("max_contracts", float("inf")) * match.price)

    def outlay(scale):
        return sum(
            stake * scale + order_fee(stake * scale / price, price)
            for stake, price in zip(stakes, match.price)
            if stake > 0
        )

    if outlay(1.0) > budget:
        lo, hi = 0.0, 1.0
        for _ in range(55):
            mid = (lo + hi) / 2
            if outlay(mid) <= budget:
                lo = mid
            else:
                hi = mid
        stakes = stakes * lo
    remaining, profit, largest = budget, 0.0, 0.0
    for (_, bet), stake in zip(match.iterrows(), stakes):
        stake = min(stake, bet.get("max_contracts", float("inf")) * bet.price)
        stake = _affordable(stake, bet.price, remaining)
        charge = order_fee(stake / bet.price, bet.price) if stake > 0 else 0
        remaining -= stake + charge
        profit += stake / bet.price * bet.side_won - stake - charge
        largest = max(largest, stake)
    return profit, budget - remaining, largest


def select_bets(frame, probability="p"):
    """Choose the larger positive after-fee edge; skip incomplete quotes.

    Returned ``cost`` includes fees, ``fraction`` is full Kelly, and ``profit``
    is realized profit for $1 of contracts, with fees extra.
    """
    bets = frame.copy()
    for name in ("ask", "bid", probability, "won", "match_id", "start_utc"):
        if name not in bets:
            bets[name] = np.nan
    ask = pd.to_numeric(bets["ask"], errors="coerce")
    other_ask = 1 - pd.to_numeric(bets["bid"], errors="coerce")
    valid = ask.between(0, 1, inclusive="neither") & other_ask.between(
        0, 1, inclusive="neither"
    )
    bets = bets.loc[valid].copy()
    ask, other_ask = ask.loc[valid], other_ask.loc[valid]
    p = bets[probability].astype(float)
    first_edge = p - ask - fee(ask)
    second_edge = 1 - p - other_ask - fee(other_ask)
    first = first_edge >= second_edge
    bets["side"] = np.where(first, 1, 2)
    bets["price"] = np.where(first, ask, other_ask)
    bets["cost"] = bets["price"] + fee(bets["price"])
    bets["edge"] = np.where(first, first_edge, second_edge)
    bets = bets.loc[bets["edge"] > 0].copy()
    bets["fraction"] = bets["edge"] / (1 - bets["cost"])
    bets["side_won"] = np.where(bets["side"] == 1, bets["won"], 1 - bets["won"])
    bets["order_fee"] = [order_fee(1 / price, price) for price in bets.price]
    bets["outlay"] = 1 + bets["order_fee"]
    bets["profit"] = bets["side_won"] / bets["price"] - bets["outlay"]
    bets["max_contracts"] = np.where(
        bets["side"] == 1,
        bets.get("depth1", float("inf")),
        bets.get("depth2", float("inf")),
    )
    return bets.reset_index(drop=True)


def kelly_path(bets, initial=50.0):
    """Settle each match together, sizing all its bets from pre-match capital.

    Returns the settled bankroll path (including initial capital), maximum
    fractional drawdown, and largest single contract stake in dollars (fees extra).
    """
    bankroll = float(initial)
    path = [bankroll]
    largest = 0.0
    if not bets.empty:
        ordered = bets.sort_values("start_utc", kind="stable")
        for _, match in ordered.groupby("match_id", sort=False):
            fractions = match["fraction"].to_numpy(dtype=float)
            fractions = fractions / max(1.0, fractions.sum())
            stakes = bankroll * fractions
            result, _, biggest = _settle(match, stakes, bankroll)
            largest = max(largest, biggest)
            bankroll += result
            # Prevent tiny negative balances from floating-point cancellation.
            bankroll = max(0.0, bankroll)
            path.append(bankroll)
    values = np.asarray(path)
    peaks = np.maximum.accumulate(values)
    drawdown = float(np.max((peaks - values) / peaks))
    return path, drawdown, largest


# Prometheus's pregame execution limits (LoL, 2026-10-28): full Kelly, at most
# 10% of capital per fixture, $250 per order and per fixture, $1k exposure,
# $2k per UTC day, from a $50 seed; no orders once capital is $0.
LOL_SIZING = {
    "kelly_fraction": 1.0,
    "fixture_fraction": 0.10,
    "order_cap": 250.0,
    "fixture_cap": 250.0,
    "exposure_cap": 1000.0,
    "day_cap": 2000.0,
}


def capped_path(bets, initial=50.0, sizing=LOL_SIZING):
    """Kelly with Prometheus-style caps, sized from start-of-day capital.

    Matches on one UTC day overlap, so every bet that day is sized from the
    capital at the day's start and the day's stakes (open exposure) are capped;
    all settle at the end of the day. Returns the same tuple as `kelly_path`.
    """
    bankroll = float(initial)
    path = [bankroll]
    largest = 0.0
    if not bets.empty:
        ordered = bets.assign(
            day=pd.to_datetime(bets["start_utc"], utc=True).dt.strftime("%Y-%m-%d")
        ).sort_values("start_utc", kind="stable")
        day_limit = min(sizing["day_cap"], sizing["exposure_cap"])
        for _, day in ordered.groupby("day", sort=True):
            capital = bankroll
            if capital <= 0:
                path.append(bankroll)
                continue
            spent, result = 0.0, 0.0
            for _, match in day.groupby("match_id", sort=False):
                stakes = (
                    capital
                    * sizing["kelly_fraction"]
                    * match["fraction"].to_numpy(dtype=float)
                )
                stakes = np.minimum(stakes, sizing["order_cap"])
                fixture_limit = min(
                    sizing["fixture_fraction"] * capital, sizing["fixture_cap"]
                )
                limit = min(fixture_limit, day_limit - spent)
                total = stakes.sum()
                if total <= 0 or limit <= 0:
                    continue
                if total > limit:
                    stakes = stakes * (limit / total)
                gain, outlay, biggest = _settle(
                    match, stakes, min(limit, capital - spent)
                )
                spent += outlay
                largest = max(largest, biggest)
                result += gain
            bankroll = max(0.0, bankroll + result)
            path.append(bankroll)
    values = np.asarray(path)
    peaks = np.maximum.accumulate(values)
    with np.errstate(invalid="ignore", divide="ignore"):
        drawdown = float(np.nanmax(np.where(peaks > 0, (peaks - values) / peaks, 0)))
    return path, drawdown, largest


def summarize(
    frame, n_resamples=2000, seed=0, probability="p", sizing="lol", depth=False
):
    """Flat ROI with whole-match bootstrap and a Kelly path (`lol` caps or `full`)."""
    bets = select_bets(frame, probability=probability)
    selected = len(bets)
    path_bets = bets.copy()
    if depth:
        path_bets["max_contracts"] = np.where(
            path_bets.side == 1,
            path_bets.get("depth1", 0.0),
            path_bets.get("depth2", 0.0),
        )
        bets["max_contracts"] = path_bets["max_contracts"]
        bets = bets[bets.max_contracts + 1e-12 >= 1 / bets.price].copy()
    else:
        path_bets["max_contracts"] = float("inf")
    path, drawdown, largest = (
        capped_path(path_bets) if sizing == "lol" else kelly_path(path_bets)
    )
    low = high = roi = mean_edge = float("nan")
    if not bets.empty:
        profits = bets["profit"].to_numpy()
        codes, labels = pd.factorize(bets["match_id"])
        sums = np.bincount(codes, weights=profits)
        counts = np.bincount(codes, weights=bets["outlay"])
        draws = [
            sums[pick].sum() / counts[pick].sum()
            for pick in resamples(len(labels), n_resamples, seed)
        ]
        if draws:
            low, high = interval(draws)
        roi = float(profits.sum() / bets["outlay"].sum())
        mean_edge = float(bets["edge"].mean())
    return {
        "bets": len(bets),
        "unfilled": selected - len(bets),
        "matches": bets["match_id"].nunique() if not bets.empty else 0,
        "mean_edge": mean_edge,
        "flat_roi": roi,
        "roi_low": float(low),
        "roi_high": float(high),
        "bankroll": path[-1],
        "multiple": path[-1] / 50.0,
        "max_drawdown": drawdown,
        "largest_stake": largest,
    }
