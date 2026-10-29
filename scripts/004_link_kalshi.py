"""Link cached Kalshi markets to Liquipedia and report settlement disagreements."""

import sqlite3
import sys
from dataclasses import asdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from promcs.link import cross_check, events_from_markets, link

SCHEMA = """
CREATE TABLE IF NOT EXISTS team_aliases (
    competitor_id TEXT PRIMARY KEY, kalshi_name TEXT, kalshi_code TEXT,
    liquipedia_team_id INTEGER, liquipedia_name TEXT, events INTEGER
);
CREATE TABLE IF NOT EXISTS kalshi_links (
    event_ticker TEXT PRIMARY KEY, match_id INTEGER REFERENCES matches(match_id),
    game_id INTEGER REFERENCES maps(game_id),
    kind TEXT CHECK (kind IN ('series', 'map')), method TEXT, reason TEXT
);
"""


def main():
    directory = REPO / "db"
    with sqlite3.connect(directory / "cs2.db") as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA)
        events = events_from_markets(conn.execute("SELECT * FROM kalshi_markets"))
        matches = {
            r["match_id"]: dict(r)
            for r in conn.execute(
                "SELECT m.*, t1.name AS team1_name, t1.key AS team1_key, "
                "t2.name AS team2_name, t2.key AS team2_key "
                "FROM matches m JOIN events e USING (event_id) "
                "JOIN teams t1 ON t1.team_id=m.team1_id "
                "JOIN teams t2 ON t2.team_id=m.team2_id WHERE e.excluded=0"
            )
        }
        for match in matches.values():
            match["maps"] = []
        for row in conn.execute("SELECT * FROM maps"):
            if row["match_id"] in matches:
                matches[row["match_id"]]["maps"].append(dict(row))
        result = link(events, matches.values())
        checked = cross_check(events, result.links, matches.values())
        conn.execute("DELETE FROM team_aliases")
        conn.execute("DELETE FROM kalshi_links")
        for alias in result.aliases:
            conn.execute(
                "INSERT INTO team_aliases VALUES (?, ?, ?, ?, ?, ?)",
                tuple(asdict(alias).values()),
            )
        for linked in result.links:
            row = asdict(linked)
            row.pop("team_ids")
            conn.execute(
                "INSERT INTO kalshi_links VALUES (?, ?, ?, ?, ?, ?)",
                tuple(row.values()),
            )
    by_event = {event.event_ticker: event for event in events}
    report = ["Unlinked events / unplayed maps:"]
    report.extend(
        f"{row.event_ticker}: {row.reason}; "
        + " vs ".join(m["team_name"] for m in by_event[row.event_ticker].markets)
        + f"; scheduled={by_event[row.event_ticker].markets[0].get('scheduled_utc')}; "
        + f"event={by_event[row.event_ticker].markets[0].get('event_name')}"
        for row in result.links
        if row.reason
    )
    report.append("\nAnchor links:")
    for row in result.links:
        if row.method != "anchor":
            continue
        match = matches[row.match_id]
        names = {match[f"team{s}_id"]: match[f"team{s}_name"] for s in (1, 2)}
        report.append(
            f"{row.event_ticker}: "
            + "; ".join(
                f"{market['team_name']} → {names.get(tid, 'unknown')}"
                for market, tid in zip(by_event[row.event_ticker].markets, row.team_ids)
            )
        )
    report.append("\nResult mismatches:")
    report.extend(checked.mismatches)
    (directory / "link_report.txt").write_text("\n".join(report) + "\n")
    counts = []
    for kind in ("series", "map"):
        rows = [row for row in result.links if row.kind == kind]
        linked = sum(
            row.match_id is not None and (kind == "series" or row.game_id is not None)
            for row in rows
        )
        counts.append(f"{kind}={linked}/{len(rows)}")
    print(
        " ".join(counts) + f" aliases={len(result.aliases)} "
        f"results={checked.agreements}/{checked.checked} mismatches={len(checked.mismatches)}"
    )


if __name__ == "__main__":
    main()
