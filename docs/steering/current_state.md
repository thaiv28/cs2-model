# Current state

## Status

2026-10-29: repo scaffolded; Kalshi collector ported and tested offline. No data collected, Liquipedia crawler, DB or model yet.

## Known limits

- Liquipedia has tournament rosters, not per-match lineups, so stand-ins are missed; no veto data.
- Liquipedia terms do not address betting/trading use; ask in their #api-help Discord.
- Kalshi collector schedule needs the repository variable and secret before it runs.

## Future work

1. Liquipedia crawler (`promcs/liquipedia/`): category listing of `Category:CS2 Tournaments`, wikitext batches of 50 titles, tab subpages, raw gzip cache, polite rate limit, injectable `get`.
2. Parsers and DB (`scripts/001_create_tables.sql`, `002_load_liquipedia.py`, `setup_db.sh`): matches, maps (round scores by half/side/overtime), rosters from both `TeamCard` (before mid-2026) and `TeamParticipants`/`Opponent`/`Person` (after), tournament tier and host country → region; `PARSER_VERSION`.
3. Kalshi backfill including historical endpoints, then linking Kalshi to Liquipedia (port valorant-model's `link.py`: name variants, learned aliases, settlement cross-check).
4. Port valorant-model's ratings and two-stage benchmark (`promval/ratings/`, `evaluation.py`, `backtest.py`, `blend.py`, `scripts/evaluate_elo.py`) and run `team_elo` and `player_round_glicko` with the tradeable quote.
5. Then, one at a time through the model change rules: rookie discount, form layer (needs per-player stats: find a source), region offsets/regional calibration, map strength.
6. Collect legacy `KXCSGOGAME`/`KXCSGOMAP` if the backfill shows they hold priced 2025 matches.
7. Per-match lineups (Liquipedia LPDB by approval, or GRID Open Access) if stand-ins prove costly.
