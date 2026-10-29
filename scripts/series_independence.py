"""Offline diagnostics for the independent-map series assumption."""

import argparse
import json
import sqlite3
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from promcs.evaluation import (
    HOLDOUT_START,
    game_losses,
    interval,
    resamples,
    series_probability,
)


def series_check(maps, start="2026-01-01", end=HOLDOUT_START, n_resamples=2000, seed=0):
    """Match-clustered calibration, map-2 dependence and Bo3 decider residuals."""
    ordered = maps.sort_values(["match_id", "order"])
    first = ordered.drop_duplicates("match_id")
    dates = pd.to_datetime(first.start_utc, utc=True)
    valid = (
        (dates >= pd.Timestamp(start, tz="UTC"))
        & first.best_of.isin([3, 5])
        & first.series_won.isin([0, 1])
        & (first.order == 1)
    )
    if end is not None:
        valid &= dates < pd.Timestamp(end, tz="UTC")
    first = first.loc[valid].copy()
    first["series_p"] = [
        series_probability(p, int(n)) for p, n in zip(first.p, first.best_of)
    ]
    bins, losses = [], {}
    for best_of in (3, 5):
        group = first[first.best_of == best_of]
        losses[best_of] = (
            float(game_losses(group.series_p, group.series_won).log_loss.mean())
            if len(group)
            else float("nan")
        )
        which = np.minimum((group.series_p * 10).astype(int), 9)
        for b in range(10):
            part = group[which == b]
            bins.append(
                {
                    "best_of": best_of,
                    "bin": b,
                    "rows": len(part),
                    "predicted": part.series_p.mean(),
                    "actual": part.series_won.mean(),
                }
            )
    second, decider = [], []
    for match_id, group in ordered[ordered.match_id.isin(first.match_id)].groupby(
        "match_id"
    ):
        by_order = group.set_index("order")
        if 1 not in by_order.index or 2 not in by_order.index:
            continue
        one, two = by_order.loc[1], by_order.loc[2]
        second.append(
            {
                "match_id": match_id,
                "first_won": int(one.won),
                "residual": two.won - two.p,
                "won": two.won,
                "model_p": two.p,
            }
        )
        if one.best_of == 3 and one.won + two.won == 1 and 3 in by_order.index:
            three = by_order.loc[3]
            decider.append({"match_id": match_id, "residual": three.won - three.p})

    def estimate(frame):
        if frame.empty:
            return {
                "rows": 0,
                "mean": float("nan"),
                "low": float("nan"),
                "high": float("nan"),
            }
        # Each diagnostic has at most one observation per match.
        values = frame.residual.to_numpy()
        low, high = interval(
            [values[pick].mean() for pick in resamples(len(values), n_resamples, seed)]
        )
        return {
            "rows": len(values),
            "mean": float(values.mean()),
            "low": float(low),
            "high": float(high),
        }

    second = pd.DataFrame(
        second, columns=["match_id", "first_won", "residual", "won", "model_p"]
    )
    dependence = {side: estimate(second[second.first_won == side]) for side in (1, 0)}
    for side in (1, 0):
        part = second[second.first_won == side]
        dependence[side].update(
            win_rate=float(part.won.mean()), model_p=float(part.model_p.mean())
        )
    contrast = []
    if len(second) and second.first_won.nunique() == 2:
        for pick in resamples(len(second), n_resamples, seed):
            draw = second.iloc[pick]
            if draw.first_won.nunique() == 2:
                contrast.append(
                    draw[draw.first_won == 1].residual.mean()
                    - draw[draw.first_won == 0].residual.mean()
                )
    contrast_ci = (
        tuple(interval(contrast)) if contrast else (float("nan"), float("nan"))
    )
    decider_stats = estimate(pd.DataFrame(decider))
    lines = [
        "| Best of | Probability bin | Rows | Predicted | Actual |",
        "|---:|---|---:|---:|---:|",
    ]
    for row in bins:
        lines.append(
            f"| {row['best_of']} | {row['bin'] / 10:.1f}–{(row['bin'] + 1) / 10:.1f} | {row['rows']} | {row['predicted']:.4f} | {row['actual']:.4f} |"
        )
    summary = [f"Series independence [{start}, {end}): {len(first)} matches."]
    for best_of in (3, 5):
        summary.append(
            f"Bo{best_of}: {(first.best_of == best_of).sum()} series, log loss {losses[best_of]:.6f}."
        )
    for side in (1, 0):
        stat = dependence[side]
        summary.append(
            f"Map 2 after map-1 {'win' if side else 'loss'}: win rate {stat['win_rate']:.4f}, model {stat['model_p']:.4f}, residual {stat['mean']:.4f} [{stat['low']:.4f}, {stat['high']:.4f}], n={stat['rows']}."
        )
    summary.append(
        f"Map-2 residual contrast (win minus loss): 95% [{contrast_ci[0]:.4f}, {contrast_ci[1]:.4f}]."
    )
    d = decider_stats
    summary.append(
        f"Bo3 1–1 decider: residual {d['mean']:.4f} [{d['low']:.4f}, {d['high']:.4f}], n={d['rows']}."
    )
    summary.append(
        "Intervals resample whole matches; residual = won − model pre-map chance."
    )
    return {
        "rows": len(first),
        "bins": pd.DataFrame(bins),
        "log_loss": losses,
        "dependence": dependence,
        "contrast_interval": contrast_ci,
        "decider": d,
        "summary": "\n".join(summary),
        "markdown": "\n\n".join(summary) + "\n\n" + "\n".join(lines),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("db/cs2.db"))
    parser.add_argument("--from", dest="start", default="2026-01-01")
    parser.add_argument("--to", dest="end", default=HOLDOUT_START)
    parser.add_argument("--out", type=Path, default=Path("docs/series_independence.md"))
    parser.add_argument("--model", default="team_elo")
    parser.add_argument(
        "--params", default="{}", help="Frozen model parameters as JSON; no tuning"
    )
    args = parser.parse_args(argv)
    from promcs.ratings.models import MODELS
    from promcs.ratings.replay import load_lineups, load_maps, replay

    if args.model not in MODELS:
        parser.error("unknown model")
    try:
        if any(date.fromisoformat(v).isoformat() != v for v in (args.start, args.end)):
            raise ValueError
        params = json.loads(args.params)
        if not isinstance(params, dict):
            raise ValueError
    except (ValueError, TypeError):
        parser.error("use ISO dates and --params as a JSON object")
    if not args.db.is_file():
        parser.error(f"database does not exist: {args.db}")
    if args.start >= args.end or args.end > HOLDOUT_START:
        parser.error("require from < to <= 2026-11-01 (holdout remains closed)")
    with sqlite3.connect(args.db) as conn:
        maps = load_maps(conn)
        maps = maps[maps.start_utc < args.end]
        predictions = replay(
            maps,
            MODELS[args.model](lineups=load_lineups(conn), **params),
        )
    result = series_check(predictions, args.start, args.end)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(result["markdown"] + "\n")
    print(result["summary"])
    print(f"Report: {args.out}")


if __name__ == "__main__":
    main()
