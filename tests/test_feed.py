"""Offline schedule, frozen-call lifecycle and market feed checks."""

import gzip
import json
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest
from test_liquipedia_db import loader, match, record

from promcs.feed import (
    current_prices,
    export,
    join_calls,
    page_text,
    pages_in,
    probabilities,
)
from promcs.liquipedia.parse import parse_scheduled

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/upcoming"
NOW = datetime(2026, 10, 29, 12, tzinfo=UTC)


def response(text, title="P"):
    return {
        "query": {
            "pages": [
                {"title": title, "revisions": [{"slots": {"main": {"content": text}}}]}
            ]
        }
    }


def scheduled(a="Alpha", b="Beta", date="Oct 30, 2026 - 12:00", bestof=3):
    return f"{{{{Match|opponent1={{{{TeamOpponent|{a}}}}}|opponent2={{{{TeamOpponent|{b}}}}}|date={date} {{{{Abbr/UTC}}}}|bestof={bestof}|map1={{{{Map}}}}}}}}"


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "test.db"
    with sqlite3.connect(path) as conn:
        conn.executescript((ROOT / "scripts/001_create_tables.sql").read_text())
        text = "{{Infobox league|name=Test Event|liquipediatier=A-Tier|sdate=2026-10-24|edate=2026-10-31}}"
        text += match().replace("Jan 1", "Jan 2")
        text += match().replace("Jan 1", "Jan 3")
        _, errors = loader.build(conn, {"P": record("P", 1, text)})
        assert not errors
    return path


def run(database, tmp_path, text="", now=NOW, **kwargs):
    return export(
        db=database,
        data=tmp_path / "data",
        now=now,
        liquipedia_fetcher=lambda **kw: response(text),
        kalshi_fetcher=lambda **kw: {"markets": [], "cursor": ""},
        **kwargs,
    )


def test_scheduled_fixture():
    with gzip.open(FIXTURE / "liquipedia_ongoing.json.gz", "rt") as handle:
        pages = list(pages_in(json.load(handle)))
    matches = [m for p in pages for m in parse_scheduled(p["title"], page_text(p))]
    upcoming = next(
        m for m in matches if (m.team1_key, m.team2_key) == ("vit", "nemiga")
    )
    assert upcoming.start_utc == datetime(2026, 10, 30, 12, tzinfo=UTC)
    assert upcoming.best_of == 3 and not upcoming.maps
    assert any(
        m.team1_key == "vit" and m.team2_key == "navi" and m.maps and m.finished
        for m in matches
    )
    assert not parse_scheduled("P", scheduled("TBD"))
    assert not parse_scheduled("P", scheduled("bye"))
    assert not parse_scheduled("P", scheduled(date=""))
    assert not parse_scheduled(pages[1]["title"], page_text(pages[1]))


def test_export_lifecycle(database, tmp_path):
    feed = run(database, tmp_path, scheduled(bestof=1))
    assert set(feed) == {
        "version",
        "game",
        "name",
        "model",
        "generated",
        "data_through",
        "source",
        "sections",
        "matches",
    }
    upcoming = next(r for r in feed["matches"] if r["status"] == "upcoming")
    assert upcoming["p_game"] == upcoming["p_series"]
    assert feed["sections"] == [{"key": "T1", "label": "Tier 1", "major": True}]
    for row in feed["matches"]:
        assert set(row) == {
            "match_id",
            "start",
            "status",
            "section",
            "event",
            "best_of",
            "name1",
            "name2",
            "p_game",
            "p_series",
            "reconstructed",
            "score1",
            "score2",
            "winner",
            "url",
            "market",
        }
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z", row["start"])
        assert isinstance(row["p_game"], float) and 0 <= row["p_game"] <= 1
        assert isinstance(row["match_id"], str)
    log = tmp_path / "data/predictions.json"
    frozen = log.read_bytes()
    later = datetime(2026, 10, 30, 13, tzinfo=UTC)
    feed = run(database, tmp_path, scheduled(bestof=5), now=later)
    assert log.read_bytes() == frozen
    live = next(r for r in feed["matches"] if r["status"] == "live")
    assert live["best_of"] == 1 and not live["reconstructed"]
    assert json.loads((tmp_path / "data/feed/cs2.json").read_text()) == feed
    # Missing pages retain a started call until the seven-day expiry.
    feed = run(database, tmp_path, now=datetime(2026, 10, 30, 19, tzinfo=UTC))
    pending = next(r for r in feed["matches"] if r["match_id"] == upcoming["match_id"])
    assert pending["status"] == "final" and pending["winner"] is None
    feed = run(database, tmp_path, now=datetime(2026, 11, 8, tzinfo=UTC))
    assert upcoming["match_id"] not in {r["match_id"] for r in feed["matches"]}


def test_reversed_call_join(database, tmp_path):
    run(database, tmp_path, scheduled("Beta", "Alpha"))
    log_path = tmp_path / "data/predictions.json"
    calls = json.loads(log_path.read_text())
    call = next(iter(calls.values()))
    call.update(p_game=0.7, p_series=0.8)
    log_path.write_text(json.dumps(calls))
    with sqlite3.connect(database) as conn:
        conn.execute(
            "UPDATE matches SET start_utc='2026-10-30T12:00:00Z' WHERE start_utc LIKE '2026-01-03%'"
        )
    feed = run(database, tmp_path, now=datetime(2026, 10, 30, 15, tzinfo=UTC))
    final = next(r for r in feed["matches"] if r["start"] == "2026-10-30T12:00Z")
    assert final["status"] == "final" and not final["reconstructed"]
    assert (final["p_game"], final["p_series"]) == (0.3, 0.2)
    assert sum(r["start"] == final["start"] for r in feed["matches"]) == 1


def test_no_fetch_cache_and_pruning(database, tmp_path):
    run(database, tmp_path, scheduled())

    def forbidden(**kw):
        pytest.fail("network fetch in no-fetch mode")

    feed = export(
        db=database,
        data=tmp_path / "data",
        now=NOW,
        no_fetch=True,
        liquipedia_fetcher=forbidden,
        kalshi_fetcher=forbidden,
    )
    assert any(r["status"] == "upcoming" for r in feed["matches"])
    run(database, tmp_path)
    assert json.loads((tmp_path / "data/predictions.json").read_text()) == {}


def test_current_market_orientation_spread_and_aliases():
    raw = json.loads((FIXTURE / "kalshi_open_KXCS2GAME.json").read_text())["markets"]
    event = raw[0]["event_ticker"]
    pair = [dict(m) for m in raw if m["event_ticker"] == event]
    assert len(pair) == 2
    candidate = {
        "match_id": "x",
        "start_utc": "2026-10-29T18:00Z",
        "team1_id": 1,
        "team2_id": 2,
        "team1_name": "Unrelated First",
        "team2_name": "Unrelated Second",
        "team1_key": "first",
        "team2_key": "second",
    }
    aliases = {
        pair[0]["custom_strike"]["esports_competitor"]: 2,
        pair[1]["custom_strike"]["esports_competitor"]: 1,
    }
    pair[0].update(yes_bid_dollars="0.3", yes_ask_dollars="0.4")
    pair[1].update(yes_bid_dollars="0", yes_ask_dollars="0")
    price = current_prices(pair, [candidate], aliases, NOW)["x"]
    assert price["p"] == pytest.approx(0.65)
    assert price["at"] == "2026-10-29T12:00Z"
    pair[0]["yes_ask_dollars"] = "0.41"
    assert not current_prices(pair, [candidate], aliases, NOW)
    pair[1].update(yes_bid_dollars="0.6", yes_ask_dollars="0.65")
    assert current_prices(pair, [candidate], aliases, NOW)["x"]["p"] == pytest.approx(
        0.625
    )


def test_join_closest_once_and_unknown_bestof():
    calls = {"a": {"start": "2026-10-29T12:00Z", "team1_id": 1, "team2_id": 2}}
    matches = [
        {"match_id": i, "start_utc": t, "team1_id": 2, "team2_id": 1}
        for i, t in [(1, "2026-10-29T13:00Z"), (2, "2026-10-29T12:01Z")]
    ]
    assert join_calls(matches, calls, NOW) == ({"2": "a"}, {"a"})
    p = probabilities(0.7, 2, {"3": 0.83})
    assert p["best_of"] is None
    assert p["p_series"] == pytest.approx(0.784)


def test_fetch_batches_pagination_and_current_price(database, tmp_path):
    with sqlite3.connect(database) as conn:
        # More than one batch, and one event outside the date window.
        for i in range(51):
            conn.execute(
                "INSERT INTO events(event_id,title,start_date,end_date,excluded,section,international) VALUES(?,?,?,?,0,'tier1',0)",
                (i + 2, f"Event/{i}", "2026-10-24", "2026-10-31"),
            )
        conn.execute(
            "INSERT INTO events(event_id,title,start_date,end_date,excluded,section,international) VALUES(99,'Old','2020-01-01','2020-01-02',0,'tier1',0)"
        )
    lp_queries, k_queries = [], []

    def lp(**kw):
        lp_queries.append(kw)
        return response(scheduled()) if "P" in kw["titles"].split("|") else response("")

    def kalshi(**kw):
        k_queries.append(kw)
        side = 1 if kw["cursor"] is None else 2
        return {
            "markets": [
                {
                    "ticker": f"KXCS2GAME-TEST-{side}",
                    "event_ticker": "KXCS2GAME-TEST",
                    "yes_sub_title": "Alpha" if side == 1 else "Beta",
                    "rules_primary": "If Alpha wins the Test: Alpha vs Beta CS2 match originally scheduled for Oct 30, 2026 at 8:00 AM EDT, then Yes.",
                    "yes_bid_dollars": "0.60",
                    "yes_ask_dollars": "0.64",
                }
            ],
            "cursor": "next" if side == 1 else "",
        }

    feed = export(
        db=database,
        data=tmp_path / "data",
        now=NOW,
        liquipedia_fetcher=lp,
        kalshi_fetcher=kalshi,
    )
    assert [len(q["titles"].split("|")) for q in lp_queries] == [50, 2]
    assert all(q["action"] == "query" and q["rvslots"] == "main" for q in lp_queries)
    assert [q["cursor"] for q in k_queries] == [None, "next"]
    upcoming = next(r for r in feed["matches"] if r["status"] == "upcoming")
    assert upcoming["market"]["p"] == 0.62
    with gzip.open(tmp_path / "data/upcoming/latest.json.gz", "rt") as handle:
        assert len(json.load(handle)) == 2


def test_page_final_requires_prior_call_and_unrated_skips(database, tmp_path, capsys):
    # Live or final first discovered after start cannot create a call.
    played = (
        scheduled(date="Oct 28, 2026 - 12:00")
        .replace("{{Map}}", "{{Map|score1=13|score2=5}}")
        .replace("|bestof=3", "|finished=true|bestof=3")
    )
    feed = run(
        database,
        tmp_path,
        played + scheduled("Unknown", "Beta") + scheduled("TBD", "Beta"),
    )
    assert not any("|" in r["match_id"] for r in feed["matches"])
    assert "skipped_unrated=1 skipped_tbd=1" in capsys.readouterr().out
    run(database, tmp_path, scheduled())
    played = (
        scheduled()
        .replace("{{Map}}", "{{Map|score1=13|score2=5}}")
        .replace("|bestof=3", "|finished=true|bestof=3")
    )
    feed = run(database, tmp_path, played, now=datetime(2026, 10, 30, 14, tzinfo=UTC))
    final = next(r for r in feed["matches"] if "|" in r["match_id"])
    assert (final["status"], final["score1"], final["score2"], final["winner"]) == (
        "final",
        1,
        0,
        1,
    )


def test_closing_candle_orientation(database, tmp_path):
    root = tmp_path / "data"
    candles = root / "kalshi/candles"
    candles.mkdir(parents=True)
    with sqlite3.connect(database) as conn:
        mid, start, team2 = conn.execute(
            "SELECT match_id,start_utc,team2_id FROM matches ORDER BY start_utc DESC LIMIT 1"
        ).fetchone()
        conn.executescript("""CREATE TABLE kalshi_links(match_id INTEGER,event_ticker TEXT,kind TEXT);
            CREATE TABLE kalshi_markets(event_ticker TEXT,ticker TEXT,competitor_id TEXT);
            CREATE TABLE team_aliases(competitor_id TEXT,liquipedia_team_id INTEGER);""")
        conn.execute(
            "INSERT INTO kalshi_links VALUES(?,'KXCS2GAME-TEST','series')", (mid,)
        )
        conn.execute(
            "INSERT INTO kalshi_markets VALUES('KXCS2GAME-TEST','TEST-SECOND','beta')"
        )
        conn.execute("INSERT INTO team_aliases VALUES('beta',?)", (team2,))
    from promcs.feed import instant

    ts = int(instant(start).timestamp())

    def candle(end, bid, ask):
        return {
            "end_period_ts": end,
            "yes_bid": {"close_dollars": bid},
            "yes_ask": {"close_dollars": ask},
        }

    with gzip.open(candles / "TEST-SECOND.json.gz", "wt") as handle:
        json.dump(
            {
                "candlesticks": [
                    candle(ts - 3600, 0.2, 0.4),
                    candle(ts, 0.3, 0.5),
                    candle(ts + 3600, 0.8, 0.9),
                ]
            },
            handle,
        )
    feed = export(db=database, data=root, now=NOW, no_fetch=True)
    final = next(r for r in feed["matches"] if r["match_id"] == str(mid))
    assert final["market"]["p"] == 0.6
    assert final["market"]["at"] == "2026-01-03T10:00Z"
