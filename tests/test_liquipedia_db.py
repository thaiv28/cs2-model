"""Fixture and synthetic DB builds need no network or real cache."""

import gzip
import hashlib
import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "load_liquipedia", ROOT / "scripts/002_load_liquipedia.py"
)
loader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loader)


@pytest.fixture
def conn():
    with sqlite3.connect(":memory:") as conn:
        conn.executescript((ROOT / "scripts/001_create_tables.sql").read_text())
        yield conn


def fixture_pages():
    records = [
        json.loads(gzip.decompress(p.read_bytes()))
        for p in (ROOT / "tests/fixtures/liquipedia").glob("*.json.gz")
    ]
    return {p["title"]: p for p in records}


def test_fixture_build(conn):
    counts, errors = loader.build(conn, fixture_pages())
    assert errors == []
    assert counts["events"] == 7
    assert counts["matches"] > 0 and counts["maps"] > counts["matches"]
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    assert (
        conn.execute(
            "SELECT count(*) FROM maps WHERE game_id / 10 != match_id"
        ).fetchone()[0]
        == 0
    )
    assert conn.execute(
        "SELECT excluded FROM events WHERE title='1v1Me/Season 6'"
    ).fetchone() == (1,)
    assert conn.execute(
        "SELECT count(*) FROM matches WHERE page='1v1Me/Season 6'"
    ).fetchone() == (0,)
    parent = conn.execute(
        "SELECT tier, section FROM events WHERE title='BLAST/Premier/2023/Fall'"
    ).fetchone()
    assert (
        conn.execute(
            "SELECT tier, section FROM events WHERE title='BLAST/Premier/2023/Fall/Groups'"
        ).fetchone()
        == parent
    )
    assert (
        conn.execute(
            "SELECT count(*) FROM maps g JOIN matches m USING(match_id) WHERE m.page='500Bros Championship/2023'"
        ).fetchone()[0]
        > 0
    )
    # This page mixes direct scores and side scores; check each direct-score map.
    from promcs.liquipedia.parse import blocks, params

    raw = fixture_pages()["500Bros Championship/2023"]["wikitext"]
    checked = 0
    for ordinal, block in enumerate(blocks(raw, "Match")):
        p = params(block)
        for key, value in p.items():
            if not key.startswith("map") or not key[3:].isdigit():
                continue
            maps = blocks(value, "Map")
            mp = params(maps[0]) if maps else {}
            if not mp.get("score1") or not mp.get("score2"):
                continue
            row = conn.execute(
                'SELECT team1_t, team1_ct, team2_t, team2_ct FROM maps JOIN matches USING(match_id) WHERE page=? AND ordinal=? AND "order"=?',
                ("500Bros Championship/2023", ordinal, int(key[3:])),
            ).fetchone()
            if row:
                assert row == (None, None, None, None)
                checked += 1
    assert checked > 0
    assert (
        conn.execute(
            "SELECT count(*) FROM matches WHERE page='Intel Extreme Masters/2025/Cologne'"
        ).fetchone()[0]
        > 0
    )


def test_stable_ids():
    assert loader.stable_id("team:abc") == int(
        hashlib.sha1(b"team:abc").hexdigest()[:12], 16
    )
    assert loader.stable_id("team:abc") == loader.stable_id("team:abc")
    assert loader.stable_id("team:abc") != loader.stable_id("player:abc")


def match(a="Alpha", b="Beta", extra=""):
    return (
        "{{Match|opponent1={{TeamOpponent|"
        + a
        + "}}|opponent2={{TeamOpponent|"
        + b
        + "}}|date=Jan 1, 2026 - 10:00 {{Abbr/UTC}}|map1={{Map|map=Nuke|score1=13|score2=5}}"
        + extra
        + "}}"
    )


def record(title, pid, text):
    return {"title": title, "pageid": pid, "revid": 1, "wikitext": text}


def test_inheritance_dedupe_and_rosters(conn):
    cards = "{{TeamCard|team=Alpha Gaming|p1=one|p2=two|p3=three|p4=four|p5=five}}{{TeamCard|team=Beta|p1=six|p2=seven|p3=eight|p4=nine|p5=ten}}"
    pages = {
        "P/Sub": record("P/Sub", 2, match()),
        "P": record(
            "P",
            1,
            "{{Infobox league|liquipediatier=S-Tier|country=Europe}}" + cards + match(),
        ),
        "P/Other": record("P/Other", 3, match(extra="|hltv=123")),
        "P/Later": record("P/Later", 4, match().replace("Jan 1", "Jan 2")),
    }
    counts, errors = loader.build(conn, pages)
    assert errors == []
    assert (counts["matches"], counts["duplicates"], counts["both_rosters"]) == (
        2,
        2,
        2,
    )
    assert conn.execute(
        "SELECT DISTINCT page FROM matches ORDER BY page"
    ).fetchall() == [("P",), ("P/Later",)]
    assert conn.execute(
        "SELECT tier, section, parent_title, international FROM events WHERE title='P/Sub'"
    ).fetchone() == ("S", "tier1", "P", 1)
    assert conn.execute("SELECT DISTINCT event_id FROM rosters").fetchall() == [(1,)]
    assert conn.execute("SELECT count(*) FROM player_maps").fetchone() == (20,)
    assert conn.execute("SELECT name FROM teams WHERE key='alpha'").fetchone() == (
        "Alpha Gaming",
    )


def test_parent_rosters_for_blast(conn):
    pages = fixture_pages()
    title = "BLAST/Premier/2023/Fall/Groups"
    # Remove the child's cards so the parent lookup is exercised explicitly.
    from promcs.liquipedia.parse import blocks

    text = pages[title]["wikitext"]
    for card in blocks(text, "TeamCard"):
        text = text.replace(card, "")
    pages[title] = {**pages[title], "wikitext": text}
    _, errors = loader.build(conn, pages)
    assert errors == []
    assert (
        conn.execute(
            "SELECT count(*) FROM player_maps p JOIN maps g USING(game_id) JOIN matches m USING(match_id) WHERE m.page=?",
            (title,),
        ).fetchone()[0]
        > 0
    )


def test_overlap_and_error_isolation(conn):
    cards = "".join(
        "{{TeamCard|team="
        + t
        + "|p1=shared|p2="
        + t
        + "2|p3="
        + t
        + "3|p4="
        + t
        + "4|p5="
        + t
        + "5}}"
        for t in ("Alpha", "Beta")
    )
    counts, errors = loader.build(
        conn, {"Good": record("Good", 1, cards + match()), "Bad": {"pageid": 2}}
    )
    assert counts["parse_errors"] == 1 and errors[0].startswith("Bad: KeyError:")
    assert counts["players_both_sides"] == 1
    assert conn.execute("SELECT count(*) FROM player_maps").fetchone() == (8,)
    assert conn.execute(
        "SELECT count(*) FROM player_maps JOIN players USING(player_id) WHERE key='shared'"
    ).fetchone() == (0,)


def test_id_dedupe_and_reversed_orientation(conn):
    a = match(extra="|hltv=123")
    b = match(extra="|hltv=123").replace("Jan 1", "Jan 2")
    c = match("Beta", "Alpha").replace("score1=13|score2=5", "score1=5|score2=13")
    counts, errors = loader.build(
        conn,
        {
            t: record(t, i, text)
            for i, (t, text) in enumerate([("A", a), ("B", b), ("C", c)], 1)
        },
    )
    assert not errors
    assert (counts["matches"], counts["duplicates"]) == (1, 2)
    assert conn.execute("SELECT match_id FROM matches").fetchone() == (
        loader.stable_id("hltv:123"),
    )


def test_modes_and_nearest_cards(conn):
    pages = {
        "P": record(
            "P",
            1,
            "{{Infobox league|liquipediatier=B-Tier|country=Global}}"
            + "{{TeamCard|team=Alpha|p1=A|p2=B|p3=C|p4=D|p5=E}}",
        ),
        "P/X": record("P/X", 2, "{{TeamCard|team=Other|p1=F|p2=G|p3=H|p4=I|p5=J}}"),
        "P/X/Y": record("P/X/Y", 3, match()),
        "Solo": record("Solo", 4, "{{Infobox league|mode=1v1}}" + match()),
    }
    counts, errors = loader.build(conn, pages)
    assert not errors
    assert (counts["matches"], counts["both_rosters"], counts["excluded"]) == (1, 0, 1)
    assert conn.execute(
        "SELECT parent_title, tier, international FROM events WHERE title='P/X/Y'"
    ).fetchone() == ("P/X", "B", 1)
    assert conn.execute("SELECT count(*) FROM player_maps").fetchone() == (0,)
    assert (
        loader.match_card({"alphagaming": ("A", ()), "alphateam": ("B", ())}, "alpha")
        is None
    )
    assert loader.match_card({"xx": ("X", ())}, "xxx") is None


def test_page_sql_failure_rolls_back(conn):
    # Distinct template keys with identical numeric map order violate the schema.
    broken = match().replace("|map1=", "|map01={{Map|score1=13|score2=4}}|map1=")
    counts, errors = loader.build(
        conn, {"A": record("A", 1, broken), "B": record("B", 2, match())}
    )
    assert len(errors) == 1 and "IntegrityError" in errors[0]
    assert counts["matches"] == 1
    assert conn.execute("SELECT page FROM matches").fetchall() == [("B",)]
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_cli_cache_root_and_error_log(tmp_path, monkeypatch, capsys):
    from promcs.liquipedia import cache

    monkeypatch.setenv("PROMCS_DATA", str(tmp_path / "raw"))
    cache.save_page(record("Good", 1, match()))
    cache.save_index({"Good": {}, "Missing": {}})
    db = tmp_path / "output/custom.db"
    loader.main(["--db", str(db)])
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT count(*) FROM matches").fetchone() == (1,)
    assert (
        "Missing: ValueError: cached page missing"
        in (db.parent / "parse_errors.txt").read_text()
    )
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) <= 10
    assert "parse_errors=1" in lines[-1]
