"""Load the saved Kalshi catalog into SQLite without network access."""

import json
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from promcs.kalshi.collect import SERIES, data_dir
from promcs.link import market_row

SCHEMA = """
CREATE TABLE IF NOT EXISTS kalshi_markets (
    ticker TEXT PRIMARY KEY, series TEXT NOT NULL, event_ticker TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('series', 'map')), map_number INTEGER,
    team_code TEXT, team_name TEXT, competitor_id TEXT, scheduled_utc TEXT,
    event_name TEXT, status TEXT, result TEXT, volume REAL,
    open_time TEXT, close_time TEXT
);
"""


def main():
    directory = REPO / "db"
    directory.mkdir(exist_ok=True)
    with sqlite3.connect(directory / "cs2.db") as conn:
        conn.executescript(SCHEMA)
        conn.execute("DELETE FROM kalshi_markets")
        count = 0
        for series in SERIES:
            path = data_dir() / "markets" / f"{series}.json"
            if not path.exists():
                print(
                    f"Missing Kalshi catalog: {path}; loading zero markets for {series}"
                )
                continue
            for raw in json.loads(path.read_text()):
                row = market_row(raw, series)
                columns = ", ".join(row)
                placeholders = ", ".join("?" for _ in row)
                conn.execute(
                    f"INSERT INTO kalshi_markets ({columns}) VALUES ({placeholders})",
                    tuple(row.values()),
                )
                count += 1
    print(f"kalshi_markets={count}")


if __name__ == "__main__":
    main()
