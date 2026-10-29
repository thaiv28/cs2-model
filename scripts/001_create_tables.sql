PRAGMA foreign_keys = ON;
CREATE TABLE events (
    event_id INTEGER PRIMARY KEY, title TEXT UNIQUE NOT NULL, parent_title TEXT,
    name TEXT, tier TEXT, tier_type TEXT, section TEXT NOT NULL, country TEXT,
    region TEXT, international INTEGER NOT NULL, online INTEGER,
    start_date TEXT, end_date TEXT, mode TEXT, prize_usd REAL,
    excluded INTEGER NOT NULL, revid INTEGER
);
CREATE TABLE teams (team_id INTEGER PRIMARY KEY, key TEXT UNIQUE NOT NULL, name TEXT);
CREATE TABLE players (player_id INTEGER PRIMARY KEY, key TEXT UNIQUE NOT NULL, name TEXT);
CREATE TABLE matches (
    match_id INTEGER PRIMARY KEY, event_id INTEGER NOT NULL REFERENCES events,
    page TEXT NOT NULL, ordinal INTEGER NOT NULL, start_utc TEXT NOT NULL,
    time_known INTEGER NOT NULL, best_of INTEGER,
    team1_id INTEGER NOT NULL REFERENCES teams, team2_id INTEGER NOT NULL REFERENCES teams,
    score1 INTEGER NOT NULL, score2 INTEGER NOT NULL,
    winner INTEGER CHECK (winner IN (1, 2)), hltv_id INTEGER
);
CREATE TABLE maps (
    game_id INTEGER PRIMARY KEY, match_id INTEGER NOT NULL REFERENCES matches,
    "order" INTEGER NOT NULL, map TEXT, score1 INTEGER NOT NULL, score2 INTEGER NOT NULL,
    team1_first_side TEXT CHECK (team1_first_side IN ('ct','t')),
    team1_t INTEGER, team1_ct INTEGER, team2_t INTEGER, team2_ct INTEGER,
    ot1 INTEGER NOT NULL, ot2 INTEGER NOT NULL, UNIQUE (match_id, "order")
);
CREATE TABLE rosters (
    event_id INTEGER REFERENCES events, team_id INTEGER REFERENCES teams,
    slot INTEGER, player_id INTEGER REFERENCES players,
    PRIMARY KEY (event_id, team_id, slot)
);
CREATE TABLE player_maps (
    game_id INTEGER REFERENCES maps, player_id INTEGER REFERENCES players,
    team INTEGER CHECK (team IN (1, 2)), PRIMARY KEY (game_id, player_id)
);
CREATE INDEX matches_start_utc ON matches(start_utc);
CREATE INDEX maps_match_id ON maps(match_id);
