"""Prediction feed, frozen calls and offline replay for the Prometheus site."""

import copy
import gzip
import hashlib
import json
import math
import os
import pickle
import sqlite3
import tempfile
import time
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from urllib.error import URLError
from urllib.parse import quote

from promcs.evaluation import series_probability
from promcs.kalshi.api import Client
from promcs.link import events_from_markets, link, market_row
from promcs.liquipedia.http import Fetcher
from promcs.liquipedia.parse import blocks, params, parse_scheduled, positional
from promcs.quotes import candle_quote
from promcs.ratings.models import ADOPTED, MODELS
from promcs.ratings.replay import load_lineups, load_maps

STATE_VERSION = 1
# The adopted model; its weights and series temperatures come from
# elo_weights.json (`evaluate_elo.py --write-weights`).
MODEL = ADOPTED

SECTIONS = [
    ("INTL", "International"),
    ("T1", "Tier 1"),
    ("T2", "Tier 2"),
    ("T3", "Tier 3"),
    ("?", "Unknown"),
]


def instant(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def stamp(value):
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%MZ")


def atomic(path, value, compressed=False):
    """Replace one complete JSON snapshot, preserving non-ASCII names."""
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode()
    if compressed:
        raw = gzip.compress(raw)
    fd, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def pages_in(responses):
    if isinstance(responses, dict):
        responses = [responses]
    for response in responses:
        pages = response.get("query", {}).get("pages", [])
        yield from pages.values() if isinstance(pages, dict) else pages


def page_text(page):
    revisions = page.get("revisions", [])
    if not revisions:
        return ""
    slot = revisions[0].get("slots", {}).get("main", revisions[0])
    return slot.get("*", slot.get("content", ""))


def section(event):
    return (
        "INTL"
        if event["international"]
        else {"tier1": "T1", "tier2": "T2", "tier3": "T3"}.get(event["section"], "?")
    )


def probabilities(p, best_of, temperatures):
    length = best_of if best_of in (1, 3, 5) else None
    series = series_probability(p, length or 3)
    temperature = temperatures.get(str(length), 1.0)
    if length != 1 and 0 < series < 1:
        series = 1 / (1 + math.exp(-temperature * math.log(series / (1 - series))))
    return {"p_game": p, "p_series": series, "best_of": length}


def oriented(call, team1):
    return {
        k: call[k] if call["team1_id"] == team1 else 1 - call[k]
        for k in ("p_game", "p_series")
    }


def join_calls(matches, calls, now):
    """Globally closest eligible pair wins; each call/result is consumed once."""
    pairs = []
    by_pair = {}
    for key, call in calls.items():
        if instant(call["start"]) <= now:
            by_pair.setdefault(
                frozenset((call["team1_id"], call["team2_id"])), []
            ).append((key, call))
    for match in matches:
        for key, call in by_pair.get(
            frozenset((match["team1_id"], match["team2_id"])), []
        ):
            delta = abs(
                (instant(call["start"]) - instant(match["start_utc"])).total_seconds()
            )
            if delta <= 36 * 3600:
                pairs.append((delta, str(match["match_id"]), key))
    joined, used = {}, set()
    for _, mid, key in sorted(pairs):
        if mid not in joined and key not in used:
            joined[mid] = key
            used.add(key)
    return joined, used


def market_url(ticker):
    return "https://kalshi.com/markets/kxcs2game/" + ticker.lower()


def linked_current_markets(raw, candidates, aliases):
    """Retain raw linked contracts in our team order for prices and execution."""
    events = events_from_markets([market_row(m, "KXCS2GAME") for m in raw])
    linked = link(events, candidates, initial_aliases=aliases)
    by_event = {e.event_ticker: e for e in events}
    by_ticker = {m["ticker"]: m for m in raw}
    by_id = {m["match_id"]: m for m in candidates}
    pairs = {}
    for result in linked.links:
        if result.match_id is None or result.reason:
            continue
        match = by_id[result.match_id]
        options = sorted(
            zip(by_event[result.event_ticker].markets, result.team_ids),
            key=lambda pair: pair[1] != match["team1_id"],
        )
        pairs[result.match_id] = [
            by_ticker[market["ticker"]]
            for market, tid in options
            if tid in (match["team1_id"], match["team2_id"])
        ]
    return pairs


def current_prices(raw, candidates, aliases, now, *, linked=None):
    pairs = (
        linked
        if linked is not None
        else linked_current_markets(raw, candidates, aliases)
    )
    prices = {}
    for mid, pair in pairs.items():
        for side, source in enumerate(pair):
            try:
                bid, ask = (
                    float(source.get(k) or 0)
                    for k in ("yes_bid_dollars", "yes_ask_dollars")
                )
            except (TypeError, ValueError):
                continue
            if not (0 < bid <= ask <= 1 and ask - bid <= 0.10 + 1e-9):
                continue
            price = (bid + ask) / 2
            prices[mid] = {
                "p": price if side == 0 else 1 - price,
                "at": stamp(now),
                "url": market_url(source["event_ticker"]),
            }
            break
    return prices


def closing_prices(conn, matches, root):
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master")}
    if not {"kalshi_links", "kalshi_markets", "team_aliases"} <= tables:
        return {}
    by_id = {m["match_id"]: m for m in matches}
    prices, preferred = {}, set()
    rows = conn.execute("""SELECT l.match_id, l.event_ticker, k.ticker, a.liquipedia_team_id
        FROM kalshi_links l JOIN kalshi_markets k USING(event_ticker)
        JOIN team_aliases a USING(competitor_id)
        WHERE l.kind='series' AND l.match_id IS NOT NULL ORDER BY k.ticker""")
    for mid, event, ticker, tid in rows:
        match = by_id.get(mid)
        if (
            match is None
            or mid in preferred
            or tid not in (match["team1_id"], match["team2_id"])
        ):
            continue
        path = root / "kalshi" / "candles" / f"{ticker}.json.gz"
        if not path.exists():
            continue
        with gzip.open(path, "rt") as handle:
            value = candle_quote(
                json.load(handle), match["start_utc"], with_timestamp=True
            )
        if value is None:
            continue
        bid, ask, ts = value
        p = (bid + ask) / 2
        first = tid == match["team1_id"]
        prices[mid] = {
            "p": p if first else 1 - p,
            "at": stamp(datetime.fromtimestamp(ts, UTC)),
            "url": market_url(event),
        }
        if first:
            preferred.add(mid)
    return prices


def feed_row(
    key, call, status, *, reconstructed=False, score1=None, score2=None, winner=None
):
    row = {
        k: call[k]
        for k in (
            "start",
            "section",
            "event",
            "best_of",
            "name1",
            "name2",
            "p_game",
            "p_series",
        )
    }
    row.update(
        match_id=str(key),
        status=status,
        reconstructed=reconstructed,
        score1=score1,
        score2=score2,
        winner=winner,
        url="https://liquipedia.net/counterstrike/" + quote(call["page"], safe="/"),
        market=None,
    )
    return row


def build_state(conn, data_root=None) -> dict:
    """Replay ratings and closing prices into a portable, versioned snapshot."""
    root = Path(data_root or os.environ.get("PROMCS_DATA", "data"))
    conn.row_factory = sqlite3.Row
    events = {
        r["title"]: dict(r)
        for r in conn.execute("SELECT * FROM events WHERE excluded=0")
    }
    teams = {r["team_id"]: dict(r) for r in conn.execute("SELECT * FROM teams")}
    weights = json.loads(
        Path(__file__).with_name("ratings").joinpath("elo_weights.json").read_text()
    )[MODEL]
    temperatures = weights["series_temperature"]
    model = MODELS[MODEL](
        lineups=load_lineups(conn),
        **{
            k: v
            for k, v in weights.items()
            if k not in ("fit_through", "series_temperature")
        },
    )
    first, seen, eligible = {}, set(), set()
    for row in load_maps(conn).itertuples(index=False):
        p = model.predict(row)
        if row.match_id not in first:
            first[row.match_id] = p
            if row.team1_id in seen and row.team2_id in seen:
                eligible.add(row.match_id)
        model.update(row)
        seen.update((row.team1_id, row.team2_id))
    matches = [
        dict(r)
        for r in conn.execute(
            "SELECT * FROM matches WHERE start_utc >= '2026-01-01' ORDER BY start_utc, match_id"
        )
        if r["match_id"] in eligible and r["page"] in events
    ]
    close = closing_prices(conn, matches, root)
    rows = []
    for match in matches:
        mid = str(match["match_id"])
        event = events[match["page"]]
        call = dict(
            page=match["page"],
            start=stamp(instant(match["start_utc"])),
            section=section(event),
            event=event["name"] or match["page"],
            name1=teams[match["team1_id"]]["name"],
            name2=teams[match["team2_id"]]["name"],
            **probabilities(first[match["match_id"]], match["best_of"], temperatures),
        )
        row = feed_row(
            mid,
            call,
            "final",
            reconstructed=True,
            score1=match["score1"],
            score2=match["score2"],
            winner=match["winner"],
        )
        row["market"] = close.get(match["match_id"])
        rows.append(row)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master")}
    aliases = (
        dict(conn.execute("SELECT competitor_id, liquipedia_team_id FROM team_aliases"))
        if "team_aliases" in tables
        else {}
    )
    newest = conn.execute(
        "SELECT max(start_utc) FROM matches WHERE winner IN (1, 2)"
    ).fetchone()[0]
    return {
        "version": STATE_VERSION,
        "built": stamp(datetime.now(UTC)),
        "model": model,
        "seen": seen,
        "temperatures": temperatures,
        "rows": rows,
        "matches": matches,
        "events": events,
        "teams": teams,
        "team_aliases": aliases,
        "data_through": newest[:10] if newest else None,
    }


def save_state(state, path):
    """Atomically save a gzip-compressed pickle snapshot."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = gzip.compress(
        pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL), compresslevel=6
    )
    fd, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_state(path):
    """Load a trusted internal snapshot, rejecting incompatible versions."""
    with gzip.open(path, "rb") as handle:
        state = pickle.load(handle)
    if state.get("version") != STATE_VERSION:
        raise ValueError(
            f"Unsupported feed state version {state.get('version')!r}; expected {STATE_VERSION}"
        )
    return state


def export(
    state=None,
    *,
    db=Path("db/cs2.db"),
    out=None,
    candidates_path=None,
    data=None,
    no_fetch=False,
    now=None,
    liquipedia_fetcher=None,
    kalshi_fetcher=None,
):
    """Write a site feed. Fetchers accept query keyword arguments and return JSON.

    Liquipedia receives MediaWiki parameters; Kalshi receives series/status/cursor.
    No fetcher is called with ``no_fetch``. Return the written feed dictionary.
    """
    started = time.monotonic()
    now = (now or datetime.now(UTC)).astimezone(UTC)
    root = Path(data or os.environ.get("PROMCS_DATA", "data"))
    out = Path(out) if out is not None else root / "feed/cs2.json"
    cache = root / "upcoming/latest.json.gz"
    log_path = root / "predictions.json"
    calls = json.loads(log_path.read_text()) if log_path.exists() else {}
    if state is None:
        with sqlite3.connect(db) as conn:
            state = build_state(conn, root)
    events, teams = state["events"], state["teams"]
    events_by_id = {event["event_id"]: event for event in events.values()}
    model, seen = state["model"], state["seen"]
    temperatures, matches = state["temperatures"], state["matches"]
    aliases = state["team_aliases"]
    titles = sorted(
        t
        for t, e in events.items()
        if e["start_date"]
        and e["end_date"]
        and e["start_date"] <= (now + timedelta(days=7)).date().isoformat()
        and e["end_date"] >= (now - timedelta(days=1)).date().isoformat()
    )
    responses, fetched, stale = [], 0, False
    if not no_fetch:
        fetch = liquipedia_fetcher or Fetcher().query
        try:
            for offset in range(0, len(titles), 50):
                batch = titles[offset : offset + 50]
                responses.append(
                    fetch(
                        action="query",
                        prop="revisions",
                        titles="|".join(batch),
                        rvprop="ids|timestamp|content",
                        rvslots="main",
                    )
                )
                fetched += len(batch)
        except (URLError, TimeoutError) as exc:
            # Liquipedia can rate-limit shared runner IPs past the fetcher's
            # retries; the last good schedule beats a failed feed.
            if not cache.exists():
                raise
            print(f"Liquipedia fetch failed ({exc}); using cached schedule")
            responses, fetched, stale = [], 0, True
        else:
            atomic(cache, responses, compressed=True)
    if (no_fetch or stale) and cache.exists():
        with gzip.open(cache, "rt") as handle:
            responses = json.load(handle)
    skipped = Counter()
    schedule = {}
    for page in pages_in(responses):
        title = page["title"]
        if title not in events and page.get("pageid") in events_by_id:
            title = events_by_id[page["pageid"]]["title"]
        if title not in events:
            continue
        text = page_text(page)
        for block in blocks(text, "Match"):
            fields = params(block)
            for side in (1, 2):
                opponents = blocks(fields.get(f"opponent{side}", ""), "TeamOpponent")
                pos = positional(opponents[0]) if len(opponents) == 1 else []
                if not pos or pos[0].strip().lower() in ("", "tbd", "bye"):
                    skipped["tbd"] += 1
                    break
        for match in parse_scheduled(title, text):
            ids = [
                int(hashlib.sha1(("team:" + key).encode()).hexdigest()[:12], 16)
                for key in (match.team1_key, match.team2_key)
            ]
            key = f"{title}|{ids[0]}|{ids[1]}|{match.ordinal}"
            s1 = sum(a > b for a, b in match.maps)
            s2 = len(match.maps) - s1
            final = (match.best_of and max(s1, s2) > match.best_of / 2) or (
                match.finished and s1 != s2
            )
            status = (
                "final"
                if final
                else "live"
                if match.start_utc <= now or match.maps
                else "upcoming"
            )
            if status == "upcoming" and match.start_utc > now + timedelta(days=7):
                continue
            event = events[title]
            metadata = {
                "page": title,
                "team1_id": ids[0],
                "team2_id": ids[1],
                "name1": teams.get(ids[0], {}).get("name", match.team1_key),
                "name2": teams.get(ids[1], {}).get("name", match.team2_key),
                "start": stamp(match.start_utc),
                "section": section(event),
                "event": event["name"] or title,
            }
            if status == "upcoming" and (
                key not in calls or instant(calls[key]["start"]) > now
            ):
                if not all(t in seen for t in ids):
                    skipped["unrated"] += 1
                    continue
                prediction = model.predict(
                    SimpleNamespace(
                        team1_id=ids[0],
                        team2_id=ids[1],
                        start_utc=match.start_utc.isoformat(),
                        section=event["section"],
                        region=event["region"],
                        international=event["international"],
                        game_id=None,
                    )
                )
                calls[key] = dict(
                    metadata,
                    **probabilities(prediction, match.best_of, temperatures),
                    saved_at=stamp(now),
                )
            schedule[key] = (metadata, status, s1, s2)
    calls = {
        k: v for k, v in calls.items() if instant(v["start"]) <= now or k in schedule
    }
    atomic(log_path, calls)
    joined, used = join_calls(matches, calls, now)
    # Suppress schedule duplicates of DB results even if no frozen call exists.
    schedule_calls = {
        k: dict(meta, p_game=0.5, p_series=0.5)
        for k, (meta, _, _, _) in schedule.items()
    }
    _, represented = join_calls(matches, schedule_calls, now)
    rows = copy.deepcopy(state["rows"])
    by_id = {str(m["match_id"]): m for m in matches}
    for row in rows:
        mid = row["match_id"]
        if mid in joined:
            logged = calls[joined[mid]]
            row.update(
                oriented(logged, by_id[mid]["team1_id"]),
                best_of=logged["best_of"],
                reconstructed=False,
            )
    candidates = []
    for key, call in calls.items():
        if key in used or key in represented:
            continue
        if key in schedule:
            _, status, s1, s2 = schedule[key]
            if status != "upcoming" and instant(call["start"]) > now:
                continue
            if status == "upcoming":
                s1 = s2 = None
            winner = (1 if s1 > s2 else 2) if status == "final" and s1 != s2 else None
        else:
            age = now - instant(call["start"])
            if age < timedelta(0) or age > timedelta(days=7):
                continue
            status = "live" if age < timedelta(hours=6) else "final"
            s1 = s2 = winner = None
        row = feed_row(key, call, status, score1=s1, score2=s2, winner=winner)
        rows.append(row)
        if status in ("upcoming", "live") and key in schedule:
            candidates.append(
                {
                    "match_id": key,
                    "start_utc": call["start"],
                    "team1_id": call["team1_id"],
                    "team2_id": call["team2_id"],
                    "team1_name": call["name1"],
                    "team2_name": call["name2"],
                    "team1_key": teams.get(call["team1_id"], {}).get("key", ""),
                    "team2_key": teams.get(call["team2_id"], {}).get("key", ""),
                }
            )
    prices, linked = {}, {}
    if not no_fetch:
        client = Client()
        fetch = kalshi_fetcher or (lambda **kw: client.json("/markets", **kw))
        raw, cursor = [], None
        while True:
            response = fetch(
                series_ticker="KXCS2GAME", status="open", limit=1000, cursor=cursor
            )
            raw.extend(response["markets"])
            cursor = response.get("cursor")
            if not cursor or not response["markets"]:
                break
        linked = linked_current_markets(raw, candidates, aliases)
        prices = current_prices(raw, candidates, aliases, now, linked=linked)
    from promcs.trading import candidates as execution_candidates

    private = execution_candidates(
        rows, linked, now, data_through=state["data_through"], skipped=skipped
    )
    atomic(
        Path(candidates_path)
        if candidates_path is not None
        else root / "feed/candidates.json",
        private,
    )
    for row in rows:
        if row["match_id"] in prices:
            row["market"] = prices[row["match_id"]]
        for field in ("p_game", "p_series"):
            row[field] = round(row[field], 4)
        if row["market"]:
            row["market"]["p"] = round(row["market"]["p"], 4)
    present = {r["section"] for r in rows}
    feed = {
        "version": 1,
        "game": "cs2",
        "name": "Counter-Strike 2",
        "model": "Player round Elo",
        "generated": stamp(now),
        "data_through": state["data_through"],
        "source": {
            "name": "Liquipedia",
            "url": "https://liquipedia.net/counterstrike/",
            "license": "CC BY-SA 3.0",
        },
        "sections": [
            {"key": k, "label": label, "major": k in ("INTL", "T1")}
            for k, label in SECTIONS
            if k in present
        ],
        "matches": rows,
    }
    atomic(out, feed)
    counts = Counter(r["status"] for r in rows)
    print(
        f"upcoming={counts['upcoming']} live={counts['live']} final={counts['final']} kalshi_priced={sum(r['market'] is not None for r in rows)} candidates={len(private['matches'])} skipped_candidates={skipped['candidates']} skipped_unrated={skipped['unrated']} skipped_tbd={skipped['tbd']} pages_fetched={fetched} liquipedia_stale={int(stale)} bytes={out.stat().st_size} seconds={time.monotonic() - started:.2f}"
    )
    return feed
