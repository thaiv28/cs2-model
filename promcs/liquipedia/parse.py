"""Pure parsing of cached Liquipedia templates; no fetching or filesystem access."""

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import NamedTuple

PARSER_VERSION = 1
TZ = dict(
    zip(
        "UTC GMT WET WEST BST CET CEST EET EEST MSK TRT AST GST IST ICT SGT PHT HKT AWST KST JST AEST AEDT NZST NZDT EST EDT CST CDT MST MDT PST PDT BRT ART CLT CLST".split(),
        [
            0,
            0,
            0,
            1,
            1,
            1,
            2,
            2,
            3,
            3,
            3,
            3,
            4,
            5.5,
            7,
            8,
            8,
            8,
            8,
            9,
            9,
            10,
            11,
            12,
            13,
            -5,
            -4,
            -6,
            -5,
            -7,
            -6,
            -8,
            -7,
            -3,
            -3,
            -4,
            -3,
        ],
    )
)
# Less common zones seen in the cache (2026-10-29 tally); ALMT is +5 since March 2024.
TZ.update(
    ALMT=5,
    AQTT=5,
    UZT=5,
    TJT=5,
    PKT=5,
    KGT=6,
    ULAT=8,
    SAST=2,
    WAT=1,
    GET=4,
    AZT=4,
    AMT=4,
    MUT=4,
    IDT=3,
    IRST=3.5,
    NPT=5.75,
    MMT=6.5,
    THA=7,
    WIB=7,
    MYT=8,
    TST=8,
    PHST=8,
    BNT=8,
    VLAT=10,
    PET=-5,
    COT=-5,
    VET=-4,
    CT=-6,
    AKDT=-8,
)


def clean(value):
    return re.sub(r"<!--.*?-->", "", value, flags=re.S).strip()


def blocks(text, name):
    """Return balanced templates with exactly this name, including nested values."""
    text = clean(text)
    pattern = re.compile(r"\{\{\s*" + re.escape(name) + r"\s*(?=[|\n}])")
    out, i = [], 0
    while match := pattern.search(text, i):
        depth, j = 1, match.start() + 2
        while j < len(text) and depth:
            if text.startswith("{{", j):
                depth += 1
                j += 2
            elif text.startswith("}}", j):
                depth -= 1
                j += 2
            else:
                j += 1
        if depth == 0:
            out.append(text[match.start() : j])
        i = j
    return out


def _parts(block):
    body = clean(block)[2:-2]
    depth, start, i, out = 0, 0, 0, []
    while i < len(body):
        two = body[i : i + 2]
        if two in ("{{", "[["):
            depth += 1
            i += 2
        elif two in ("}}", "]]"):
            depth -= 1
            i += 2
        else:
            if body[i] == "|" and depth == 0:
                out.append(body[start:i].strip())
                start = i + 1
            i += 1
    return [*out, body[start:].strip()][1:]


def params(block):
    return {
        k.strip(): clean(v)
        for p in _parts(block)
        if "=" in p
        for k, v in [p.split("=", 1)]
    }


def positional(block) -> list[str]:
    return [clean(p) for p in _parts(block) if "=" not in p]


def fold(value):
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", value).lower())


def normalize_tier(value):
    return {
        "S-Tier": "S",
        "A-Tier": "A",
        "B-Tier": "B",
        "C-Tier": "C",
        "C": "C",
        "C-tier": "C",
        "4": "D",
    }.get(value)


def section(tier):
    return {"S": "tier1", "A": "tier1", "B": "tier2", "C": "tier3", "D": "tier3"}.get(
        tier, "unknown"
    )


def parse_infobox(wikitext) -> dict:
    boxes = blocks(wikitext, "Infobox league")
    p = params(boxes[0]) if boxes else {}
    result = {
        k: p.get(k) or None
        for k in ("name", "country", "type", "sdate", "edate", "mode")
    }
    result["tier"] = normalize_tier(p.get("liquipediatier"))
    result["tier_type"] = p.get("liquipediatiertype", "").strip().lower() or None
    try:
        result["prize_usd"] = float(p["prizepoolusd"].replace(",", ""))
    except (KeyError, ValueError):
        result["prize_usd"] = None
    return result


class PlayerRef(NamedTuple):
    key: str
    name: str


def roster_cards(wikitext):
    """Keep display names alongside the public folded roster keys."""
    cards = {}
    for block in blocks(wikitext, "TeamCard"):
        p = params(block)
        names = [p.get(f"p{i}", "") for i in range(1, 6)]
        if p.get("team") and all(names):
            cards[fold(p["team"])] = (
                p["team"],
                tuple(PlayerRef(n.lower(), n) for n in names),
            )
    for block in blocks(wikitext, "Opponent"):
        names = positional(block)
        if not names:
            continue
        people = []
        for person in blocks(params(block).get("players", ""), "Person"):
            p, pos = params(person), positional(person)
            if pos and ("role" not in p or p["role"] == "player"):
                people.append(PlayerRef((p.get("link") or pos[0]).lower(), pos[0]))
        if len(people) >= 5:
            cards.setdefault(fold(names[0]), (names[0], tuple(people[:5])))
    return cards


def parse_rosters(wikitext) -> dict[str, tuple[PlayerRef, ...]]:
    return {key: players for key, (_, players) in roster_cards(wikitext).items()}


def parse_date(value):
    """Return UTC time, precision flag and whether an unknown zone was seen."""
    match = re.match(r"\s*([A-Za-z]+ \d{1,2}, \d{4})(?:\s*-\s*(\d{1,2}:\d{2}))?", value)
    if not match:
        return None, 0, False
    date = match[1].replace("Sept ", "Sep ")
    dt = None
    for fmt in ("%B %d, %Y %H:%M", "%b %d, %Y %H:%M"):
        try:
            dt = datetime.strptime(date + " " + (match[2] or "12:00"), fmt)
            break
        except ValueError:
            pass
    if dt is None:
        return None, 0, False
    zone = re.search(r"Abbr/([^}|\s]+)", value)
    explicit = zone and re.fullmatch(r"UTC([+-]\d{1,2})(?::(\d\d))?", zone[1])
    if explicit:
        sign = -1 if explicit[1].startswith("-") else 1
        hours = int(explicit[1]) + sign * int(explicit[2] or 0) / 60
    unknown = bool(zone and not explicit and zone[1] not in TZ)
    offset = hours if explicit else TZ.get(zone[1], 0) if zone else 0
    offset = offset if match[2] else 0
    return (
        (dt - timedelta(hours=offset)).replace(tzinfo=UTC),
        int(bool(match[2]) and not unknown),
        unknown,
    )


@dataclass
class ParsedMap:
    order: int
    map: str
    score1: int
    score2: int
    team1_first_side: str | None
    team1_t: int | None
    team1_ct: int | None
    team2_t: int | None
    team2_ct: int | None
    ot1: int
    ot2: int


@dataclass
class ParsedMatch:
    ordinal: int
    team1_key: str
    team2_key: str
    start_utc: datetime
    time_known: int
    hltv_id: int | None
    best_of: int
    maps: list[ParsedMap]
    winner: int | None


def _number(p, key):
    try:
        return int(p.get(key, ""))
    except ValueError:
        return None


def _map(order, block):
    p = params(block)
    if p.get("finished", "").lower() in ("skip", "false"):
        return None
    halves = [_number(p, k) for k in ("t1t", "t1ct", "t2t", "t2ct")]
    ot = [0, 0]
    for n in range(1, 10):
        values = [_number(p, f"o{n}{k}") for k in ("t1t", "t1ct", "t2t", "t2ct")]
        if None in values:
            break
        ot[0] += values[0] + values[1]
        ot[1] += values[2] + values[3]
    scores = [_number(p, k) for k in ("score1", "score2")]
    if None not in scores:
        halves = [None] * 4
    elif None not in halves:
        scores = [sum(halves[:2]) + ot[0], sum(halves[2:]) + ot[1]]
    else:
        return None
    if scores[0] == scores[1] or max(scores) < 13:
        return None
    side = p.get("t1firstside", "").lower()
    return ParsedMap(
        order,
        p.get("map", "").strip(),
        *scores,
        side if side in ("ct", "t") else None,
        *halves,
        *ot,
    )


def parse_matches(
    title, wikitext, *, counts: Counter | None = None
) -> list[ParsedMatch]:
    counts = counts if counts is not None else Counter()
    matches = []
    for ordinal, block in enumerate(blocks(wikitext, "Match")):
        p = params(block)
        teams = []
        for side in (1, 2):
            opponent = p.get(f"opponent{side}", "")
            b = blocks(opponent, "TeamOpponent")
            pos = positional(b[0]) if len(b) == 1 and opponent.strip() == b[0] else []
            teams.append(pos[0].strip().lower() if pos else "")
        if any(t in ("", "tbd", "bye") for t in teams):
            continue
        dt, known, unknown = parse_date(p.get("date", ""))
        counts["unknown_tz"] += unknown
        if dt is None:
            counts["dateless"] += 1
            continue
        mapkeys = sorted(
            (k for k in p if re.fullmatch(r"map\d+", k)), key=lambda k: int(k[3:])
        )
        maps = []
        for key in mapkeys:
            order = int(key[3:])
            if order > 9:
                counts["map_order_gt9"] += 1
                continue
            for b in blocks(p[key], "Map")[:1]:
                if game := _map(order, b):
                    maps.append(game)
        if maps:
            wins1 = sum(g.score1 > g.score2 for g in maps)
            wins2 = len(maps) - wins1
            winner = None if wins1 == wins2 else (1 if wins1 > wins2 else 2)
            matches.append(
                ParsedMatch(
                    ordinal,
                    *teams,
                    dt,
                    known,
                    _number(p, "hltv"),
                    len(mapkeys) or len(maps),
                    maps,
                    winner,
                )
            )
    return matches


@dataclass
class ScheduledMatch:
    title: str
    ordinal: int
    team1_key: str
    team2_key: str
    start_utc: datetime
    time_known: int
    best_of: int | None
    maps: list[tuple[int, int]]
    finished: bool


def parse_scheduled(title, wikitext) -> list[ScheduledMatch]:
    """Read dated, named Match blocks, including those without played maps."""
    matches = []
    for ordinal, block in enumerate(blocks(wikitext, "Match")):
        p = params(block)
        teams = []
        for side in (1, 2):
            opponent = p.get(f"opponent{side}", "")
            b = blocks(opponent, "TeamOpponent")
            pos = positional(b[0]) if len(b) == 1 and opponent.strip() == b[0] else []
            teams.append(pos[0].strip().lower() if pos else "")
        if any(t in ("", "tbd", "bye") for t in teams):
            continue
        dt, known, _ = parse_date(p.get("date", ""))
        if dt is None:
            continue
        mapkeys = [k for k in p if re.fullmatch(r"map\d+", k)]
        maps = []
        for key in sorted(mapkeys, key=lambda k: int(k[3:])):
            order = int(key[3:])
            if order > 9:
                continue
            for b in blocks(p[key], "Map")[:1]:
                if game := _map(order, b):
                    maps.append((game.score1, game.score2))
        matches.append(
            ScheduledMatch(
                title,
                ordinal,
                *teams,
                dt,
                known,
                _number(p, "bestof") if "bestof" in p else len(mapkeys) or None,
                maps,
                p.get("finished", "").strip().lower()
                not in ("", "0", "false", "no", "skip"),
            )
        )
    return matches
