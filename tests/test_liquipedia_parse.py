"""Offline template and fixture parsing."""

import gzip
import json
from collections import Counter
from pathlib import Path

import pytest

from promcs.liquipedia import parse
from promcs.liquipedia.parse import (
    blocks,
    normalize_tier,
    params,
    parse_date,
    parse_infobox,
    parse_matches,
    parse_rosters,
    positional,
    section,
)
from promcs.liquipedia.regions import region

FIXTURES = Path(__file__).parent / "fixtures/liquipedia"


def page(name):
    return json.loads(gzip.decompress((FIXTURES / (name + ".json.gz")).read_bytes()))


def test_nested_parameters():
    block = "{{Thing|one|x={{Other|a=b}}|y=[[Target|label]]<!--x-->|z=ok}}"
    assert blocks("before" + block + "after", "Thing") == [
        block.replace("<!--x-->", "")
    ]
    assert params(block) == {"x": "{{Other|a=b}}", "y": "[[Target|label]]", "z": "ok"}
    assert positional(block) == ["one"]
    assert blocks("{{Matcher|x}}", "Match") == []


@pytest.mark.parametrize(
    ("value", "expected", "known", "unknown"),
    [
        (
            "January 18, 2026 - 10:10 {{Abbr/CET}}",
            "2026-01-18T09:10:00+00:00",
            1,
            False,
        ),
        ("June 1, 2026 - 10:10 {{Abbr/CEST}}", "2026-06-01T08:10:00+00:00", 1, False),
        ("Jan 18, 2026 - 10:10 {{Abbr/EST}}", "2026-01-18T15:10:00+00:00", 1, False),
        ("Sept 1, 2026", "2026-09-01T12:00:00+00:00", 0, False),
        ("September 1, 2026 {{Abbr/CET}}", "2026-09-01T12:00:00+00:00", 0, False),
        ("Jan 18, 2026 - 10:10 {{Abbr/WHAT}}", "2026-01-18T10:10:00+00:00", 0, True),
    ],
)
def test_dates(value, expected, known, unknown):
    dt, precision, badzone = parse_date(value)
    assert (dt.isoformat(), precision, badzone) == (expected, known, unknown)


@pytest.mark.parametrize(
    ("value", "tier", "group"),
    [
        ("S-Tier", "S", "tier1"),
        ("A-Tier", "A", "tier1"),
        ("B-Tier", "B", "tier2"),
        ("C-Tier", "C", "tier3"),
        ("C", "C", "tier3"),
        ("C-tier", "C", "tier3"),
        ("4", "D", "tier3"),
        ("Other", None, "unknown"),
    ],
)
def test_tiers(value, tier, group):
    assert normalize_tier(value) == tier
    assert section(tier) == group


@pytest.mark.parametrize(
    ("country", "expected"),
    [
        ("Europe<!--Spain-->", "EU"),
        ("Nordic Countries", "EU"),
        ("eu", "EU"),
        ("West Asia", "AS"),
        ("Arabia", "AS"),
        ("Levant", "AS"),
        ("Syria", "AS"),
        ("uae", "AS"),
        ("Brunei", "AS"),
        ("Myanmar", "AS"),
        ("Latin America North", "NA"),
        ("North Africa", "AF"),
        ("Sub-Saharan Africa", "AF"),
        ("Mauritius", "AF"),
        ("Ukraine", "CIS"),
        ("Brazil", "SA"),
        ("Australia", "OCE"),
        ("Global", None),
        ("Americas", None),
        ("International", None),
        ("World", None),
        ("unknown", None),
    ],
)
def test_regions(country, expected):
    assert region(country) == expected


def test_infobox():
    assert parse_infobox("") == dict.fromkeys(
        (
            "name",
            "tier",
            "tier_type",
            "country",
            "type",
            "sdate",
            "edate",
            "mode",
            "prize_usd",
        )
    )
    p = parse_infobox(
        "{{Infobox league|country=Europe<!--Spain-->|liquipediatiertype= Showmatch |prizepoolusd=1,200}}"
    )
    assert (p["country"], p["tier_type"], p["prize_usd"]) == (
        "Europe",
        "showmatch",
        1200,
    )


def test_cct_matches_and_cards():
    p = page("CCT_Season_3_Europe_Series_13")
    matches = parse_matches(p["title"], p["wikitext"])
    m = next(m for m in matches if (m.team1_key, m.team2_key) == ("1w", "ex-ruby"))
    assert m.start_utc.isoformat() == "2026-01-18T09:10:00+00:00"
    assert (m.hltv_id, m.best_of, m.winner) == (2389099, 3, 2)
    assert [(g.map, g.score1, g.score2) for g in m.maps] == [
        ("Dust II", 7, 13),
        ("Ancient", 11, 13),
    ]
    m = next(m for m in matches if (m.team1_key, m.team2_key) == ("sangal", "illwill"))
    g = next(g for g in m.maps if g.map == "Nuke")
    assert (g.score1, g.score2, g.ot1, g.ot2) == (17, 19, 5, 7)
    assert (g.team1_t + g.team1_ct, g.team2_t + g.team2_ct) == (12, 12)
    assert [p.key for p in parse_rosters(p["wikitext"])["gamerlegion"]] == [
        "tauson",
        "pr",
        "rez",
        "hypex",
        "snax",
    ]


def test_person_rosters():
    rosters = parse_rosters(page("Journey_2026_Autumn")["wikitext"])
    assert [p.key for p in rosters["100thieves"]] == [
        "rain",
        "poiii",
        "sirah",
        "dev1ce",
        "gizmy",
    ]
    assert "impulse (ukrainian player)" in [p.key for p in rosters["anteiku"]]
    assert parse_rosters("{{TeamCard|team=Incomplete|p1=A}}") == {}
    assert (
        parse_rosters("{{Opponent|X|players={{Persons|{{Person|A|role=coach}}}}}}")
        == {}
    )


def test_rejected_maps_and_counters():
    counts = Counter()
    text = "{{Match|opponent1={{TeamOpponent|A}}|opponent2={{TeamOpponent|B}}|date=bad|map1={{Map|score1=13|score2=1}}}}"
    assert not parse_matches("P", text, counts=counts)
    assert counts["dateless"] == 1
    text = text.replace("date=bad", "date=Jan 1, 2026 - 10:00 {{Abbr/UNKNOWN}}")
    assert parse_matches("P", text, counts=counts)
    assert counts["unknown_tz"] == 1
    for old, new in [
        ("map1=", "map10="),
        ("score2=1", "score2=13"),
        ("score1=13", "score1=2"),
        ("{{Map|", "{{Map|finished=false|"),
    ]:
        assert not parse_matches("P", text.replace(old, new), counts=counts)
    assert counts["map_order_gt9"] == 1
    assert not parse_matches("P", text.replace("TeamOpponent|A", "SoloOpponent|A"))
    assert not parse_matches("P", text.replace("TeamOpponent|A", "TeamOpponent|bye"))


def test_less_common_and_explicit_utc_zones():
    for zone, hour in (("ALMT", 5), ("ULAT", 2), ("UTC+6", 4), ("UTC-3", 13)):
        text = (
            "{{Match|opponent1={{TeamOpponent|a}}|opponent2={{TeamOpponent|b}}"
            f"|date=March 5, 2026 - 10:00 {{{{Abbr/{zone}}}}}"
            "|map1={{Map|map=Mirage|score1=13|score2=5}}}}"
        )
        (match,) = parse.parse_matches("Page", text)
        assert match.time_known == 1
        assert match.start_utc.hour == hour, zone
