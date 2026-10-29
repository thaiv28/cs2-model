"""Shared cached hourly Kalshi quote selection."""

import math
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class QuoteRule:
    """Which hourly quote stands for the price a bot could have traded.

    `tradeable` (the default for reports): the first candle ending at least
    `open_delay_minutes` after the market opened, no later than `buffer_hours` before the
    scheduled start (so no veto or lineup news), whose bid/ask spread is at most
    `max_spread`. `prestart`: the last candle ending at or before the start,
    which can already price the veto. `hours24`/`hours6`: last tight candle
    ending at least 24/6 hours before start and 30 minutes after open.
    """

    mode: str = "prestart"
    max_spread: float = 0.06
    open_delay_minutes: float = 30.0
    buffer_hours: float = 2.0


PRESTART = QuoteRule()
TRADEABLE = QuoteRule("tradeable")


def candle_quote(
    candles, start_utc, open_time=None, rule=PRESTART, with_timestamp=False
):
    """(bid, ask) closes in dollars under `rule`, or None when no candle qualifies."""
    if isinstance(candles, dict):
        candles = candles.get("candlesticks", [])
    start = pd.Timestamp(start_utc)
    if rule.mode in ("tradeable", "hours24", "hours6"):
        if open_time is None or pd.isna(open_time):
            return None
        opened = pd.Timestamp(open_time)
        if pd.isna(opened):
            return None
        delay = pd.Timedelta(minutes=rule.open_delay_minutes)
        earliest = (opened + delay).timestamp()
        hours = {"hours24": 24, "hours6": 6}.get(rule.mode, rule.buffer_hours)
        cutoff = (start - pd.Timedelta(hours=hours)).timestamp()
    else:
        earliest, cutoff = float("-inf"), start.timestamp()
    valid = []
    for candle in candles:
        end = candle.get("end_period_ts")
        if end is None or end > cutoff or end < earliest:
            continue
        closes = []
        for side in ("yes_bid", "yes_ask"):
            quote = candle.get(side) or {}
            value = quote.get("close_dollars")
            if value is None:
                value = quote.get("close")
            try:
                value = float(value)
            except (TypeError, ValueError):
                break
            if not math.isfinite(value) or not 0 <= value <= 1:
                break
            closes.append(value)
        if len(closes) == 2:
            if rule.mode != "prestart" and not (
                0 < closes[0] < closes[1] < 1
                and closes[1] - closes[0] <= rule.max_spread + 1e-9
            ):
                continue
            valid.append((end, tuple(closes)))
    if not valid:
        return None
    pick = min if rule.mode == "tradeable" else max
    end, quote = pick(valid, key=lambda item: item[0])
    return (*quote, end) if with_timestamp else quote
