"""Frozen blend coefficients and private raw inputs for Prometheus execution."""

import hashlib
import json
import math
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from promcs import blend
from promcs.ratings.models import ADOPTED, MODELS

VALIDATE_FROM = "2026-01-01"
RULES = re.compile(
    r"^If (?P<side>.+?) wins the (?P<event>.+): (?P<team1>.+?) vs\.? "
    r"(?P<team2>.+?) CS2 match originally scheduled for "
    r"(?P<day>\w{3} \d{1,2}, \d{4}) at (?P<time>\d{1,2}:\d{2} [AP]M) E[DS]T"
)


def instant(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(UTC)


def build_blend_artifact(rows, game, series_ticker, now):
    """Monthly fits using every eligible completed series strictly before M."""
    snapshots = []
    if not rows.empty:
        dates = pd.to_datetime(rows.start_utc, utc=True)
        eligible = (
            (rows.kind == "series")
            & rows.won.notna()
            & (dates >= pd.Timestamp(VALIDATE_FROM, tz="UTC"))
        )
        if eligible.any():
            first = dates[eligible].min().normalize().replace(day=1)
            last = pd.Timestamp(now).tz_convert("UTC").normalize().replace(day=1)
            for boundary in pd.date_range(
                first + pd.offsets.MonthBegin(),
                last + pd.offsets.MonthBegin(),
                freq="MS",
            ):
                training = rows[eligible & (dates < boundary)]
                if len(training) < 300:
                    continue
                a, b, n = blend.fit(training.p, training.market_p, training.won)
                snapshots.append(
                    {
                        "available_from": boundary.isoformat(),
                        "trained_through": dates.loc[training.index].max().isoformat(),
                        "training_series": n,
                        "market_slope": float(a),
                        "gap_slope": float(b),
                    }
                )
    return {
        "version": "game-blend-v1",
        "game": game,
        "series_ticker": series_ticker,
        "clip": 0.01,
        "protocol": f"Tradeable quote, no intercept, monthly earlier-only fits from {VALIDATE_FROM}, {ADOPTED} + stage-1 series temperature.",
        "snapshots": snapshots,
    }


def adopted_series_rows(conn, directory):
    """Replay the adopted stage-1 fit through the shared report row builder."""
    from promcs.benchmark import report_market_rows, with_series_temperature
    from promcs.ratings.replay import load_lineups, load_maps, replay

    weights = json.loads(
        Path(__file__).with_name("ratings").joinpath("elo_weights.json").read_text()
    )[ADOPTED]
    model = MODELS[ADOPTED](
        lineups=load_lineups(conn),
        **{
            k: v
            for k, v in weights.items()
            if k not in ("fit_through", "series_temperature")
        },
    )
    source = with_series_temperature(
        replay(load_maps(conn), model),
        {int(k): v for k, v in weights["series_temperature"].items()},
    )
    rows = report_market_rows(conn, source, directory)
    return rows.loc[rows.kind == "series"].copy() if not rows.empty else rows


def candidates(feed_rows, linked_markets, now, *, data_through=None, skipped=None):
    """Build execution records; linked pairs are ordered as our team 1, team 2.

    ``skipped`` optionally receives a count of rejected linked feed matches.
    Current markets are supplied by the feed's existing linker, never fetched here.
    """
    now = now.astimezone(UTC)
    at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    matches = []
    for row in feed_rows:
        if row["match_id"] not in linked_markets:
            continue
        try:
            if (
                row["status"] != "upcoming"
                or instant(row["start"]) <= now
                or row["best_of"] is None
            ):
                raise ValueError("ineligible feed match")
            pair = linked_markets[row["match_id"]]
            if len(pair) != 2 or any(
                m.get("status") not in (None, "open", "active") for m in pair
            ):
                raise ValueError("not an open pair")
            parsed = [RULES.match(m.get("rules_primary") or "") for m in pair]
            if not all(parsed):
                raise ValueError("invalid rules")
            rules = [{k: v.strip() for k, v in p.groupdict().items()} for p in parsed]
            names = [r["side"] for r in rules]
            teams = sorted([rules[0]["team1"], rules[0]["team2"]])
            if (
                len(set(teams)) != 2
                or sorted(names) != teams
                or any(sorted([r["team1"], r["team2"]]) != teams for r in rules)
                or any(
                    (m.get("yes_sub_title") or "").strip() != r["side"]
                    for m, r in zip(pair, rules)
                )
                or pair[0]["event_ticker"] != pair[1]["event_ticker"]
            ):
                raise ValueError("inconsistent teams")
            starts = [
                datetime.strptime(f"{r['day']} {r['time']}", "%b %d, %Y %I:%M %p")
                .replace(tzinfo=ZoneInfo("America/New_York"))
                .astimezone(UTC)
                for r in rules
            ]
            start = starts[0]
            if (
                starts[1] != start
                or start <= now
                or abs(start - instant(row["start"])) > timedelta(hours=18)
            ):
                raise ValueError("inconsistent start")
            p = row["p_series"]
            raw = {names[0]: round(p, 6), names[1]: round(1 - p, 6)}
            if not all(math.isfinite(v) and 0 < v < 1 for v in raw.values()):
                raise ValueError("invalid probability")
            event = pair[0]["event_ticker"]
            identity = json.dumps(
                ["cs2", teams, event], separators=(",", ":"), ensure_ascii=False
            )
            matches.append(
                {
                    "execution_candidate": {
                        "kind": "candidate-v1",
                        "schema_version": 1,
                        "game": "cs2",
                        "series_ticker": "KXCS2GAME",
                        "at": at,
                        "fixture_id": hashlib.sha256(identity.encode()).hexdigest(),
                        "event_ticker": event,
                        "teams": teams,
                        "team_homes": {},
                        "international": row["section"] == "INTL",
                        "group": "cs2-series",
                        "start": start.strftime("%Y-%m-%dT%H:%MZ"),
                        "raw": raw,
                        "provenance": {
                            "model": ADOPTED,
                            "match_id": row["match_id"],
                            "p_game": row["p_game"],
                            "p_series": p,
                            "best_of": row["best_of"],
                            "data_through": data_through,
                            "names": [row["name1"], row["name2"]],
                            "start": row["start"],
                        },
                    }
                }
            )
        except (KeyError, TypeError, ValueError):
            if skipped is not None:
                skipped["candidates"] += 1
    return {"version": 1, "game": "cs2", "generated": at, "matches": matches}
