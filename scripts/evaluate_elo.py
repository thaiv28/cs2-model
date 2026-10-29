"""Offline Elo selection and benchmark against coin and cached Kalshi prices."""

import argparse
import gzip
import json
import math
import os
import sqlite3
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from promcs.backtest import depth_limits, summarize
from promcs.blend import walk_forward
from promcs.evaluation import (
    HOLDOUT_START,
    ece,
    game_losses,
    paired_bootstrap,
    series_probability,
)
from promcs.kalshi.collect import SERIES, data_dir
from promcs.quotes import PRESTART, QuoteRule, candle_quote
from promcs.quotes import TRADEABLE as TRADEABLE
from promcs.ratings.layers import LAYERS
from promcs.ratings.models import MODELS, PARAM_GRIDS, PINNED
from promcs.ratings.regions import macro_region
from promcs.ratings.replay import load_lineups, load_maps, replay


def candle_mid(candles, start_utc):
    quote = candle_quote(candles, start_utc)
    return sum(quote) / 2 if quote is not None else None


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


TEMPERATURE_GRID = np.round(np.arange(0.40, 1.501, 0.01), 2)


def fit_series_temperature(stage1_maps, min_rows=30):
    """{best_of: T} minimizing stage-1 series log loss of σ(T·logit p); Bo1 stays 1."""
    rows = series_rows(stage1_maps.drop(columns="series_t", errors="ignore"))
    temperatures = {1: 1.0}
    for best_of, group in rows.groupby("best_of"):
        best_of = int(best_of)
        if best_of == 1 or len(group) < min_rows:
            temperatures[best_of] = 1.0
            continue
        losses = [
            game_losses(temper(group.p, t), group.won).log_loss.mean()
            for t in TEMPERATURE_GRID
        ]
        temperatures[best_of] = float(TEMPERATURE_GRID[int(np.argmin(losses))])
    return temperatures


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


def sections(frame):
    yield "all", frame
    for name in ("tier1", "tier2", "tier3", "unknown"):
        yield name, frame[frame.section == name]
    for flag in (1, 0):
        yield f"international={flag}", frame[frame.international == flag]


def metrics_table(frame, model):
    lines = [
        "| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for name, rows in sections(frame):
        if rows.empty:
            lines.append(f"| {model} | {name} | 0 | — | — | — | — |")
            continue
        scores = game_losses(rows.p, rows.won).mean()
        lines.append(
            f"| {model} | {name} | {len(rows)} | {scores.log_loss:.6f} | "
            f"{scores.brier:.6f} | {scores.accuracy:.6f} | {ece(rows.p, rows.won):.6f} |"
        )
    return "\n".join(lines)


def comparison_table(frame, other, label, model="team_elo", by_section=True):
    lines = [
        f"| Section | Rows | {model} log loss | {label} log loss | Difference | 95% interval | Significant |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for name, rows in sections(frame) if by_section else [("all", frame)]:
        if rows.empty:
            continue
        model_loss = game_losses(rows.p, rows.won).log_loss
        other_p = rows[other] if other in rows else np.full(len(rows), 0.5)
        other_loss = game_losses(other_p, rows.won).log_loss
        mean, low, high = paired_bootstrap(
            model_loss, other_loss, clusters=rows.match_id
        )
        significant = "yes" if low > 0 or high < 0 else "no"
        lines.append(
            f"| {name} | {len(rows)} | {model_loss.mean():.6f} | "
            f"{other_loss.mean():.6f} | {mean:.6f} | [{low:.6f}, {high:.6f}] | {significant} |"
        )
    return "\n".join(lines)


def market_slices(frame):
    for kind in ("series", "map"):
        subset = frame[frame.kind == kind] if not frame.empty else frame
        yield kind, "all", subset
        for section in ("tier1", "tier2", "tier3", "unknown"):
            yield (
                kind,
                section,
                subset[subset.section == section] if not subset.empty else subset,
            )
        for flag in (1, 0):
            yield (
                kind,
                f"international={flag}",
                subset[subset.international == flag] if not subset.empty else subset,
            )


def depth_cells(rows, probability="p"):
    stats = summarize(rows, probability=probability, depth=True)
    roi = (
        f"{stats['flat_roi']:.2%} [{stats['roi_low']:.2%}, {stats['roi_high']:.2%}]"
        if stats["bets"]
        else "—"
    )
    return f"{stats['bets']} ({stats['unfilled']} unfilled) | {roi} | ${stats['bankroll']:.2f} |"


def market_tables(frame, probability="p"):
    if probability == "p_blend":
        frame = frame[frame.blend_fitted]
    loss_lines = [
        "| Kind | Slice | Rows | Model log loss | Kalshi log loss | Difference [95% interval] | Significant |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    bet_lines = [
        "| Kind | Slice | Bets | Matches | Mean edge | Flat ROI [95% interval] | Kelly, LoL caps ($50 start) | Multiple | Max drawdown | Largest stake | Bets filled | Flat ROI depth-capped [95% interval] | Kelly depth-capped final |",
        "|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---:|",
    ]
    for kind, label, rows in market_slices(frame):
        if rows.empty:
            loss_lines.append(f"| {kind} | {label} | 0 | — | — | — | — |")
        else:
            model_loss = game_losses(rows[probability], rows.won).log_loss
            market_loss = game_losses(rows.market_p, rows.won).log_loss
            diff, low, high = paired_bootstrap(
                model_loss, market_loss, clusters=rows.match_id
            )
            significant = "yes" if low > 0 or high < 0 else "no"
            loss_lines.append(
                f"| {kind} | {label} | {len(rows)} | {model_loss.mean():.6f} | "
                f"{market_loss.mean():.6f} | {diff:.6f} [{low:.6f}, {high:.6f}] | {significant} |"
            )
        stats = summarize(rows, probability=probability)
        edge = f"{stats['mean_edge']:.4f}" if stats["bets"] else "—"
        roi = (
            f"{stats['flat_roi']:.2%} [{stats['roi_low']:.2%}, {stats['roi_high']:.2%}]"
            if stats["bets"]
            else "—"
        )
        bet_lines.append(
            f"| {kind} | {label} | {stats['bets']} | {stats['matches']} | {edge} | {roi} | "
            f"${stats['bankroll']:.2f} | {stats['multiple']:.3f}× | "
            f"{stats['max_drawdown']:.2%} | ${stats['largest_stake']:.2f} | "
            + depth_cells(rows, probability)
        )
    # Prometheus caps apply per fixture across its series and map markets.
    stats = summarize(frame, probability=probability)
    if stats["bets"]:
        bet_lines.append(
            f"| series+map | all | {stats['bets']} | {stats['matches']} | "
            f"{stats['mean_edge']:.4f} | {stats['flat_roi']:.2%} "
            f"[{stats['roi_low']:.2%}, {stats['roi_high']:.2%}] | "
            f"${stats['bankroll']:.2f} | {stats['multiple']:.3f}× | "
            f"{stats['max_drawdown']:.2%} | ${stats['largest_stake']:.2f} | "
            + depth_cells(frame, probability)
        )
    return "\n".join(loss_lines), "\n".join(bet_lines)


def summary_table(markets):
    labels = [
        f"{kind}{suffix} {metric}"
        for suffix in ("", " blended")
        for kind in ("Series", "Map")
        for metric in (
            "Δ log loss",
            "flat ROI",
            "Kelly (LoL caps) $",
            "flat ROI depth-capped",
            "Kelly depth-capped $",
        )
    ]
    lines = ["| Model | " + " | ".join(labels) + " |", "|---|" + "---:|" * len(labels)]
    for name, frame in markets.items():
        cells = [name]
        for probability in ("p", "p_blend"):
            for kind in ("series", "map"):
                rows = frame[frame.kind == kind] if not frame.empty else frame
                if probability == "p_blend":
                    rows = rows[rows.blend_fitted]
                stats = summarize(rows, probability=probability, n_resamples=0)
                diff = (
                    (
                        game_losses(rows[probability], rows.won).log_loss.mean()
                        - game_losses(rows.market_p, rows.won).log_loss.mean()
                    )
                    if not rows.empty
                    else None
                )
                depth = summarize(
                    rows, probability=probability, depth=True, n_resamples=0
                )
                cells.extend(
                    [
                        f"{diff:.6f}" if diff is not None else "—",
                        f"{stats['flat_roi']:.2%}" if stats["bets"] else "—",
                        f"${stats['bankroll']:.2f}",
                        f"{depth['flat_roi']:.2%}" if depth["bets"] else "—",
                        f"${depth['bankroll']:.2f}",
                    ]
                )
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def robustness_table(markets):
    lines = [
        "| Quote rule | Model | Kind | Rows | Raw Δ log loss | Blended Δ log loss | Raw flat ROI depth-capped | Blended flat ROI depth-capped |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for (rule, name), frame in markets.items():
        for kind in ("series", "map"):
            rows = frame[frame.kind == kind] if not frame.empty else frame
            cells = []
            rois = []
            for probability in ("p", "p_blend"):
                part = (
                    rows
                    if probability == "p" or rows.empty
                    else rows[rows.blend_fitted]
                )
                if part.empty:
                    cells.append("—")
                    rois.append("—")
                else:
                    delta = (
                        game_losses(part[probability], part.won).log_loss.mean()
                        - game_losses(part.market_p, part.won).log_loss.mean()
                    )
                    cells.append(f"{delta:.6f}")
                    stats = summarize(
                        part, probability=probability, depth=True, n_resamples=0
                    )
                    rois.append(f"{stats['flat_roi']:.2%}" if stats["bets"] else "—")
            lines.append(
                f"| {rule} | {name} | {kind} | {len(rows)} | "
                + " | ".join(cells + rois)
                + " |"
            )
    return "\n".join(lines)


def scored_rows(frame, start, end=HOLDOUT_START):
    """Select an inclusive start and exclusive end without altering replay."""
    dates = pd.to_datetime(frame.start_utc, utc=True)
    mask = dates >= pd.Timestamp(start, tz="UTC")
    if end is not None:
        mask &= dates < pd.Timestamp(end, tz="UTC")
    return frame.loc[mask].copy()


def monthly_table(frame):
    """All metrics share linked rows; unfitted blend months show dashes."""
    lines = [
        "| Kind | Month | Rows | Model log loss | Blended log loss | Kalshi log loss | Raw flat ROI (bets), unlimited Kelly final | Blended flat ROI (bets), unlimited Kelly final | Raw bets filled | Raw Flat ROI depth-capped [95% interval] | Raw Kelly depth-capped final | Blended bets filled | Blended Flat ROI depth-capped [95% interval] | Blended Kelly depth-capped final |",
        "|---|---|---:|---:|---:|---:|---|---|---:|---|---:|---:|---|---:|",
    ]
    if frame.empty:
        return "\n".join(lines)
    monthly = frame.assign(
        month=pd.to_datetime(frame.start_utc, utc=True).dt.strftime("%Y-%m")
    )

    def roi(rows, probability):
        stats = summarize(rows, probability=probability, n_resamples=0)
        return (
            f"{stats['flat_roi']:.2%} ({stats['bets']}), ${stats['bankroll']:.2f}"
            if stats["bets"]
            else "— (0), $50.00"
        )

    for (kind, month), rows in monthly.groupby(["kind", "month"], sort=True):
        fitted = rows.blend_fitted.all()
        raw_roi = roi(rows, "p")
        blend_roi = roi(rows, "p_blend") if fitted else "—"
        blend_loss = (
            f"{game_losses(rows.p_blend, rows.won).log_loss.mean():.6f}"
            if fitted
            else "—"
        )
        lines.append(
            f"| {kind} | {month} | {len(rows)} | {mean_loss(rows):.6f} | {blend_loss} | "
            f"{game_losses(rows.market_p, rows.won).log_loss.mean():.6f} | {raw_roi} | {blend_roi} | "
            + depth_cells(rows)
            + " "
            + (depth_cells(rows, "p_blend") if fitted else "— | — | — |")
        )
    return "\n".join(lines)


def parameter_grid(model, k_grid=None, full=False):
    if model in PINNED and not full:
        pinned = dict(PINNED[model])
        return [pinned | {"k": k} for k in k_grid] if k_grid else [pinned]
    grid = dict(PARAM_GRIDS[model])
    if k_grid is not None and "k" in grid:
        grid["k"] = k_grid
    return [dict(zip(grid, values)) for values in product(*grid.values())]


def initialize_worker(maps, lineups, tune_from, tune_to):
    global _WORKER_MAPS, _WORKER_LINEUPS, _WORKER_TUNE_FROM, _WORKER_TUNE_TO
    _WORKER_MAPS, _WORKER_LINEUPS = maps, lineups
    _WORKER_TUNE_FROM, _WORKER_TUNE_TO = tune_from, tune_to


def tune_candidate(task):
    """Return just a scalar score, avoiding retention of all candidate replays."""
    name, params = task
    candidate = replay(_WORKER_MAPS, MODELS[name](lineups=_WORKER_LINEUPS, **params))
    tuning = scored_rows(candidate, _WORKER_TUNE_FROM, _WORKER_TUNE_TO)
    return name, params, float(game_losses(tuning.p, tuning.won).log_loss.mean())


def mean_loss(frame):
    return float(game_losses(frame.p, frame.won).log_loss.mean())


def main(argv=None):
    started = time.perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("db/cs2.db"))
    parser.add_argument("--out", type=Path, default=Path("docs/elo_backtest.md"))
    parser.add_argument("--models", default=",".join(n for n in MODELS if n != "coin"))
    parser.add_argument(
        "--report-models",
        help="comma list; default team_elo, player_round_glicko, best two",
    )
    parser.add_argument("--jobs", type=int, default=min(os.cpu_count() or 1, 8))
    parser.add_argument("--k-grid", help="optional K grid override for every model")
    parser.add_argument(
        "--full-grid",
        action="store_true",
        help="re-search pinned models' full grids (models.PINNED)",
    )
    parser.add_argument("--seed-from")
    parser.add_argument("--tune-from", default="2024-01-01")
    parser.add_argument("--tune-to", default="2026-01-01")
    parser.add_argument("--validate-from", default="2026-01-01")
    parser.add_argument("--layers", default="none")
    parser.add_argument("--blend-min", type=int, default=100)
    parser.add_argument(
        "--quote",
        choices=("tradeable", "prestart", "hours24", "hours6"),
        default="tradeable",
        help="Kalshi price: first tight quote ≥30 min after listing and ≥2 h "
        "before start (default); hours24/hours6 use the last tight quote by that "
        "cutoff; prestart uses the last candle before start",
    )
    parser.add_argument("--max-spread", type=float, default=0.06)
    parser.add_argument("--depth-window-hours", type=float, default=6)
    parser.add_argument("--depth-share", type=float, default=0.5)
    parser.add_argument("--robustness", action="store_true")
    parser.add_argument("--series-check", action="store_true")
    parser.add_argument(
        "--series-temperature",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="fit a stage-1 temperature per best-of on series odds (default on)",
    )
    parser.add_argument("--holdout", action="store_true")
    parser.add_argument("--write-weights", action="store_true")
    args = parser.parse_args(argv)
    quote_rule = QuoteRule(args.quote, max_spread=args.max_spread)
    try:
        k_grid = (
            None
            if args.k_grid is None
            else tuple(float(k) for k in args.k_grid.split(","))
        )
        if k_grid is not None and (
            not k_grid or any(not math.isfinite(k) or k <= 0 for k in k_grid)
        ):
            raise ValueError
        for value in (args.seed_from, args.tune_from, args.tune_to, args.validate_from):
            if value is not None and date.fromisoformat(value).isoformat() != value:
                raise ValueError
        if (
            not (args.tune_from < args.tune_to <= args.validate_from <= HOLDOUT_START)
            or (args.seed_from is not None and args.seed_from > args.tune_from)
            or args.jobs < 1
            or args.blend_min < 1
            or not math.isfinite(args.depth_window_hours)
            or args.depth_window_hours < 0
            or not 0 <= args.depth_share <= 1
            or not 0 <= args.max_spread <= 1
        ):
            raise ValueError
    except (ValueError, TypeError):
        parser.error(
            "use positive finite K values, --jobs >= 1, --blend-min >= 1 and ISO dates: seed-from <= tune-from < tune-to <= validate-from <= 2026-11-01"
        )
    layer_names = list(dict.fromkeys(name.strip() for name in args.layers.split(",")))
    if any(name not in LAYERS for name in layer_names):
        parser.error("unknown layer in --layers")
    requested = [name.strip() for name in args.models.split(",")]
    if any(name not in MODELS for name in requested):
        parser.error("unknown model in --models")
    report_names = (
        None
        if args.report_models is None
        else list(dict.fromkeys(name.strip() for name in args.report_models.split(",")))
    )
    if report_names is not None and any(
        name not in MODELS or name == "coin" for name in report_names
    ):
        parser.error("unknown rating model in --report-models")
    extras = report_names if report_names is not None else ["player_round_glicko"]
    names = list(
        dict.fromkeys(["team_elo", *(n for n in requested if n != "coin"), *extras])
    )
    if not args.db.is_file():
        parser.error(f"database does not exist: {args.db}")
    with sqlite3.connect(args.db) as conn:
        tables = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        missing_kalshi = sorted(
            {"kalshi_links", "kalshi_markets", "team_aliases"} - tables
        )
        top_summary = (
            "Kalshi sections skipped: missing tables " + ", ".join(missing_kalshi) + "."
            if missing_kalshi
            else ""
        )
        maps = load_maps(conn)
        if args.seed_from is not None:
            maps = scored_rows(maps, args.seed_from, None)
        if not args.holdout:
            maps = maps[pd.to_datetime(maps.start_utc, utc=True) < HOLDOUT_START]
        tuning_maps = scored_rows(maps, args.tune_from, args.tune_to)
        if tuning_maps.empty:
            parser.error("no tuning maps in the requested scoring window")
        lineups = load_lineups(conn)
        tasks = [
            (name, params)
            for name in names
            for params in parameter_grid(name, k_grid, args.full_grid)
        ]
        best_params, losses = {}, {}
        if args.jobs == 1:
            initialize_worker(
                maps[maps.start_utc < args.tune_to],
                lineups,
                args.tune_from,
                args.tune_to,
            )
            for name, params, loss in map(tune_candidate, tasks):
                if name not in losses or loss < losses[name]:
                    best_params[name], losses[name] = params, loss
        else:
            with ProcessPoolExecutor(
                max_workers=args.jobs,
                initializer=initialize_worker,
                initargs=(
                    maps[maps.start_utc < args.tune_to],
                    lineups,
                    args.tune_from,
                    args.tune_to,
                ),
            ) as pool:
                for name, params, loss in pool.map(tune_candidate, tasks, chunksize=1):
                    if name not in losses or loss < losses[name]:
                        best_params[name], losses[name] = params, loss
        ranked = sorted(names, key=losses.get)
        detailed = (
            report_names
            if report_names is not None
            else list(
                dict.fromkeys(
                    [
                        "team_elo",
                        "player_round_glicko",
                        *ranked[:2],
                    ]
                )
            )
        )
        winners = {
            name: replay(maps, MODELS[name](lineups=lineups, **best_params[name]))
            for name in names
        }
        temperatures = {}
        if args.series_temperature:
            for name in names:
                temperatures[name] = fit_series_temperature(
                    scored_rows(winners[name], args.tune_from, args.tune_to)
                )
                winners[name] = with_series_temperature(
                    winners[name], temperatures[name]
                )
        base_detailed = detailed.copy()
        for name in base_detailed:
            for layer_name in layer_names:
                layer = LAYERS[layer_name](context={"conn": conn, "lineups": lineups})
                layer.fit(scored_rows(winners[name], args.tune_from, args.tune_to))
                adjusted = scored_rows(winners[name], args.validate_from, None)
                adjusted["p"] = layer.apply(adjusted)
                variant = f"{name}+{layer_name}"
                adjusted.attrs["layer_description"] = layer.describe()
                if args.series_temperature:
                    stage1 = scored_rows(winners[name], args.tune_from, args.tune_to)
                    stage1["p"] = layer.apply(stage1)
                    temperatures[variant] = fit_series_temperature(stage1)
                    adjusted = with_series_temperature(adjusted, temperatures[variant])
                    adjusted.attrs["layer_description"] = layer.describe()
                winners[variant] = adjusted
                detailed.append(variant)
        coin = replay(maps, MODELS["coin"]())
        fit_through = tuning_maps.start_utc.max()[:10]
        unknown = sum(macro_region(code) is None for code in maps.region)
        report = [
            "# Elo variants benchmark",
            (
                "Series temperatures (stage 1; p′ = σ(T·logit p), T < 1 pulls odds toward 50%): "
                + "; ".join(
                    f"{name} Bo3 {t.get(3, 1.0):.2f}, Bo5 {t.get(5, 1.0):.2f}"
                    for name, t in temperatures.items()
                    if name in detailed
                )
                if temperatures
                else "Series temperatures: off."
            ),
            "Parameters minimize tuning map log loss across all sections. Replay predicts before update; "
            f"Replay starts {args.seed_from or 'at the first map'}. "
            f"Tuning: [{args.tune_from}, {args.tune_to}); validation: "
            f"[{args.validate_from}, {HOLDOUT_START}). "
            "Holdout is scored only with --holdout and never selects parameters. "
            "Series use the first map prediction and independent maps in an odd best-of; "
            "missing/even best-of or unknown results are skipped. "
            "Accuracy gives 0.5 predictions half credit; ECE uses 10 equal-width bins. "
            "Log loss clips probabilities at 1e-6. Paired bootstrap uses 2,000 resamples, "
            "seed 0, clustered by match_id. Differences are the named model minus its comparator; "
            "negative favors the model. Significance requires a 95% percentile interval excluding zero. "
            "Tuning scores are selection diagnostics, not independent evidence of improvement.",
            f"Fit through {fit_through}. Unknown host-region map rows: {unknown} (including missing/un).",
            "## Stage 1 — tuning (outcomes)\n\n### Leaderboard\n\n"
            "| Model | Best params | Map log loss | Series log loss | Rows |\n"
            "|---|---|---:|---:|---:|\n"
            + "\n".join(
                f"| {name} | {json.dumps(best_params[name], sort_keys=True)} | {losses[name]:.6f} | "
                f"{mean_loss(series_rows(scored_rows(winners[name], args.tune_from, args.tune_to))):.6f} | {len(tuning_maps)} |"
                for name in ranked
            ),
            (
                f"Kalshi uses the first hourly bid/ask (midpoint for log loss, ask/bid for bets) "
                f"ending ≥30 min after the market opened and ≥2 h before the scheduled start, "
                f"with a spread ≤ {args.max_spread:.2f}: a price a bot could trade before any veto. "
                "Markets without such a quote are skipped. "
                if args.quote == "tradeable"
                else f"Kalshi uses the last tight hourly quote ending ≥{24 if args.quote == 'hours24' else 6} h "
                "before start and ≥30 min after open. "
                if args.quote in ("hours24", "hours6")
                else "Kalshi uses the last valid hourly bid/ask midpoint ending at or before "
                "match start (can already price the veto). "
            )
            + "oriented to team1 using aliases. One contract per event, preferring team1. "
            "Compare identical rows; map predictions use the first map's pre-match chance. "
            "Missing links, aliases or candles are skipped; unplayed maps are not in the rows. "
            "Returns use frozen stage-1 parameters. "
            "Each bet buys $1 of contracts, fees extra; order fees ceil to a cent "
            "(0.07 × contracts × price × (1−price)). Edge selection uses unrounded per-contract fees. "
            "ROI divides profit by stake plus fees; intervals resample matches 2,000 times. "
            "Unlimited depth and depth-capped returns are shown together. "
            f"Depth uses {args.depth_share:g} of acceptable-price tape volume in the "
            f"{args.depth_window_hours:g} hours after the quote, missing tapes give zero fills. "
            "Partial Kelly fills are allowed; flat bets require the full $1 stake. "
            "Kelly uses LoL caps and rounded-fee affordability, from a $50 seed. "
            "Each slice runs independently. Tape volume is a fill proxy; no slippage is modeled.",
        ]
        blended_markets, monthly_fits = {}, {}
        for name in detailed:
            source = winners[name]
            source = scored_rows(source, args.validate_from, None)
            market = kalshi_rows(
                conn, source, series_rows(source), data_dir(), quote_rule
            )
            if not market.empty:
                market = depth_limits(
                    market, data_dir(), args.depth_window_hours, args.depth_share
                )
            blended_markets[name], monthly_fits[name] = walk_forward(
                market, args.validate_from, args.blend_min
            )
        if args.robustness and not missing_kalshi:
            robust = {}
            for mode in ("tradeable", "hours24", "hours6"):
                for name in detailed:
                    source = scored_rows(winners[name], args.validate_from, None)
                    market = kalshi_rows(
                        conn,
                        source,
                        series_rows(source),
                        data_dir(),
                        QuoteRule(mode, max_spread=args.max_spread),
                    )
                    if not market.empty:
                        market = depth_limits(
                            market,
                            data_dir(),
                            args.depth_window_hours,
                            args.depth_share,
                        )
                    market, _ = walk_forward(market, args.validate_from, args.blend_min)
                    robust[mode, name] = (
                        scored_rows(market, args.validate_from)
                        if not market.empty
                        else market
                    )
            report.extend(["## Quote-time robustness", robustness_table(robust)])
        if args.series_check:
            from scripts.series_independence import series_check

            for name in detailed:
                report.extend(
                    [
                        f"## Series independence: {name}",
                        series_check(winners[name], args.validate_from)["markdown"],
                    ]
                )
        windows = [
            ("Stage 1 — tuning (outcomes)", args.tune_from, args.tune_to),
            ("Stage 2 — validation (outcomes)", args.validate_from, HOLDOUT_START),
        ]
        if args.holdout:
            windows.append(("Holdout", HOLDOUT_START, None))
        for title, start, end in windows:
            tuning = start == args.tune_from and end == args.tune_to
            holdout = title == "Holdout"
            if not tuning:
                report.append(f"## {title}")
            window_names = base_detailed if tuning else detailed
            selected = {
                name: scored_rows(frame, start, end) for name, frame in winners.items()
            }
            coin_rows = scored_rows(coin, start, end)
            if not tuning:
                report.append(
                    "### Leaderboard (frozen stage-1 parameters)\n\n"
                    "| Model | Best params | Map log loss | Series log loss | Rows |\n"
                    "|---|---|---:|---:|---:|\n"
                    + "\n".join(
                        f"| {name} | {json.dumps(best_params[name.split('+')[0]], sort_keys=True)} | "
                        f"{mean_loss(selected[name]):.6f} | {mean_loss(series_rows(selected[name])):.6f} | {len(selected[name])} |"
                        for name in sorted(
                            window_names, key=lambda n: mean_loss(selected[n])
                        )
                    )
                )
            for kind in ("Maps", "Series"):
                frames = (
                    selected
                    if kind == "Maps"
                    else {n: series_rows(f) for n, f in selected.items()}
                )
                coin_frame = coin_rows if kind == "Maps" else series_rows(coin_rows)
                report.extend([f"### {kind}", metrics_table(coin_frame, "coin")])
                for name in window_names:
                    report.append(metrics_table(frames[name], name))
                    report.append(f"{name} − coin (paired log loss):")
                    report.append(
                        comparison_table(
                            frames[name], "coin_p", "coin", name, by_section=not tuning
                        )
                    )
                for name in names if tuning else detailed:
                    if name == "team_elo":
                        continue
                    frame = frames[name].merge(
                        frames["team_elo"][["game_id", "p"]].rename(
                            columns={"p": "baseline_p"}
                        ),
                        on="game_id",
                        validate="one_to_one",
                    )
                    report.append(f"{name} − team_elo (paired log loss):")
                    report.append(
                        comparison_table(
                            frame, "baseline_p", "team_elo", name, by_section=False
                        )
                    )
            if tuning:
                continue
            report.append(
                "## Holdout vs Kalshi"
                if holdout
                else "## Stage 2 — validation vs Kalshi"
            )
            if missing_kalshi:
                report.append(top_summary)
                continue
            markets = {
                name: scored_rows(frame, start, end) if not frame.empty else frame
                for name, frame in blended_markets.items()
            }
            if not holdout:
                top_summary = summary_table(markets)
                report.insert(
                    1,
                    "## Combined summary (validation, all sections)\n\n" + top_summary,
                )
            for name, market in markets.items():
                report.append(f"### {name}: Kalshi comparison and returns")
                report.append(winners[name].attrs.get("layer_description", ""))
                if market.empty:
                    report.append("no linked markets (rows: 0)")
                loss_table, bet_table = market_tables(market)
                report.extend(
                    [
                        "#### Log loss vs Kalshi",
                        loss_table,
                        "#### Full-Kelly returns",
                        bet_table,
                    ]
                )
                excluded = int((~market.blend_fitted).sum())
                loss_table, bet_table = market_tables(market, probability="p_blend")
                fits = monthly_fits[name]
                if not fits.empty:
                    months = (
                        set(
                            pd.to_datetime(market.start_utc, utc=True).dt.strftime(
                                "%Y-%m"
                            )
                        )
                        if not market.empty
                        else set()
                    )
                    fits = fits[fits.month.isin(months)]
                fit_lines = [
                    "| Month | Kind | n | a | b | Status |",
                    "|---|---|---:|---:|---:|---|",
                ]
                for row in fits.itertuples(index=False):
                    fit_lines.append(
                        f"| {row.month} | {row.kind} | {row.n} | {row.a:.6f} | {row.b:.6f} | "
                        + ("fitted |" if row.fitted else "unfitted |")
                    )
                report.extend(
                    [
                        "#### Monthly market blend fits",
                        f"UTC monthly fits use earlier rows of the same kind from {args.validate_from}, "
                        f"excluding holdout; minimum {args.blend_min} rows. "
                        "logit(p_blend) = a·logit(mid) + b·(logit(p_model) − logit(mid)); "
                        "inputs clipped to [0.01, 0.99], no intercept, ridge 1e-6. "
                        f"Unfitted rows use mid unchanged; excluded from blended tables: {excluded} rows. "
                        "Rating parameters remain selected on the tuning window.",
                        "\n".join(fit_lines),
                        "#### Log loss vs Kalshi (blended)",
                        loss_table,
                        "#### Full-Kelly returns (blended)",
                        bet_table,
                        "#### Monthly breakdown",
                        "All metrics use identical linked rows within each kind/month. Unfitted blend months show —; counts include all rows.",
                        monthly_table(market),
                    ]
                )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n\n".join(report) + "\n")
    if args.write_weights:
        path = REPO / "promcs/ratings/elo_weights.json"
        path.write_text(
            json.dumps(
                {
                    name: {
                        **params,
                        "series_temperature": {
                            str(k): v for k, v in temperatures.get(name, {}).items()
                        },
                        "fit_through": fit_through,
                    }
                    for name, params in best_params.items()
                },
                indent=2,
            )
            + "\n"
        )
    summary_lines = top_summary.splitlines()
    print("\n".join(summary_lines[:17]))
    if len(summary_lines) > 17:
        print("Additional models are in the full report.")
    print(f"Report: {args.out}")
    print(f"Total wall time: {time.perf_counter() - started:.2f}s")
    return best_params


if __name__ == "__main__":
    main()
