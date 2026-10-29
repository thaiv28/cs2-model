# Current state

## Status

2026-10-29: Kalshi collector, Liquipedia crawler, offline SQLite build and Kalshi ↔ Liquipedia linking implemented and tested. Real cache: 4,713 pages; DB: 58,034 matches and 119,185 maps, zero parse errors. Kalshi: 15,795 markets; series linked 5,138/7,897; maps 0/0 (catalog absent); 599 aliases; result agreements 10,172/10,188, 16 mismatches. Ratings remain future work.

## Known limits

- Kalshi backfill is incomplete; map links are tested offline only. Settlement mismatches need source review; 2,210 markets lack a parseable scheduled time and use the open-time fallback.
- Liquipedia has tournament rosters, not per-match lineups, so stand-ins are missed; no veto data.
- Unknown time zones are counted and treated as UTC with time_known=0; international classification is approximate.
- Liquipedia terms do not address betting/trading use; ask in their #api-help Discord.
- Kalshi collector schedule needs the repository variable and secret before it runs.

## Future work

1. Complete the Kalshi backfill, including historical endpoints and map catalogs; rebuild links as catalogs arrive.
2. Port valorant-model's ratings and two-stage benchmark (`promval/ratings/`, `evaluation.py`, `backtest.py`, `blend.py`, `scripts/evaluate_elo.py`) and run `team_elo` and `player_round_glicko` with the tradeable quote.
3. Then, one at a time through the model change rules: rookie discount, form layer (needs per-player stats: find a source), region offsets/regional calibration, map strength.
4. Collect legacy `KXCSGOGAME`/`KXCSGOMAP` if the backfill shows they hold priced 2025 matches.
5. Per-match lineups (Liquipedia LPDB by approval, or GRID Open Access) if stand-ins prove costly.
