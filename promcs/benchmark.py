"""Shared benchmark series orientation, temperature and cached quote rows."""

import gzip
import json

import numpy as np
import pandas as pd

from promcs.evaluation import series_probability
from promcs.kalshi.collect import SERIES
from promcs.quotes import PRESTART, TRADEABLE, candle_quote


def series_rows(maps):
    """Use the first map's pre-update chance and the recorded series winner."""
    first = maps.drop_duplicates("match_id").copy()
    first = first[
        first.best_of.notna()
        & (first.best_of > 0)
        & (first.best_of % 2 == 1)
        & first.series_won.notna()
    ].copy()
    first["p"] = [series_probability(p, int(n)) for p, n in zip(first.p, first.best_of)]
    if "series_t" in first:
        # Stage-1 temperature per best-of: independent-map odds run too extreme.
        first["p"] = temper(first.p, first.series_t)
    first["won"] = first.series_won.astype(int)
    return first


def temper(p, t):
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    return 1 / (1 + np.exp(-np.asarray(t, dtype=float) * np.log(p / (1 - p))))


def with_series_temperature(frame, temperatures):
    frame = frame.copy()
    frame["series_t"] = frame.best_of.map(temperatures).fillna(1.0)
    return frame


def kalshi_rows(conn, maps, series, directory, rule=PRESTART):
    """One usable market per event, preferring the team1-side contract."""
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master")}
    if not {"kalshi_links", "kalshi_markets", "team_aliases"} <= tables:
        return pd.DataFrame()
    markets = pd.read_sql(
        """SELECT l.event_ticker, l.match_id, l.game_id, l.kind,
                  k.ticker, k.open_time, a.liquipedia_team_id
           FROM kalshi_links l JOIN kalshi_markets k USING (event_ticker)
           JOIN team_aliases a USING (competitor_id)
           WHERE l.match_id IS NOT NULL AND k.series IN (?, ?) ORDER BY k.ticker""",
        conn,
        params=SERIES,
    )
    map_index = maps.set_index("game_id")
    # Kalshi quotes are taken before the match, so maps are compared with the
    # model's pre-match chance (the first map's), not one updated on earlier maps.
    prematch = maps.sort_values(["match_id", "order"]).groupby("match_id").p.first()
    series_index = series.set_index("match_id")
    candidates = []
    for market in markets.itertuples(index=False):
        index = series_index if market.kind == "series" else map_index
        key = market.match_id if market.kind == "series" else market.game_id
        if key not in index.index:
            continue
        row = index.loc[key]
        if market.kind == "map" and row.match_id != market.match_id:
            continue
        if market.liquipedia_team_id not in (row.team1_id, row.team2_id):
            continue
        path = directory / "candles" / f"{market.ticker}.json.gz"
        if not path.exists():
            continue
        with gzip.open(path, "rt") as handle:
            quote = candle_quote(
                json.load(handle),
                row.start_utc,
                market.open_time,
                rule,
                with_timestamp=True,
            )
        if quote is None:
            continue
        bid, ask, quote_ts = quote
        mid = (bid + ask) / 2
        team1 = market.liquipedia_team_id == row.team1_id
        candidate = row.to_dict()
        if market.kind == "map":
            candidate["p"] = prematch[market.match_id]
        candidate.update(
            match_id=market.match_id,
            kind=market.kind,
            event_ticker=market.event_ticker,
            ticker=market.ticker,
            quote_ts=quote_ts,
            market_p=mid if team1 else 1 - mid,
            team1_side=team1,
            ask=ask if team1 else 1 - bid,
            bid=bid if team1 else 1 - ask,
        )
        candidates.append(candidate)
    if not candidates:
        return pd.DataFrame()
    return (
        pd.DataFrame(candidates)
        .sort_values("team1_side", ascending=False, kind="stable")
        .drop_duplicates("event_ticker")
        .reset_index(drop=True)
    )


def report_market_rows(
    conn, source, directory, rule=TRADEABLE, validate_from="2026-01-01"
):
    """The report's validation rows, including later holdout dates for causal fits."""
    dates = pd.to_datetime(source.start_utc, utc=True)
    source = source.loc[dates >= pd.Timestamp(validate_from, tz="UTC")].copy()
    return kalshi_rows(conn, source, series_rows(source), directory, rule)
