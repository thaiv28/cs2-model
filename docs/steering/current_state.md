# Current state

## Status

2026-10-29: Kalshi collector, Liquipedia crawler and offline SQLite build implemented and tested. Real cache: 4,713 pages; DB: 58,034 matches and 119,185 maps, zero parse errors. Ratings, causal regional calibration and the two-stage benchmark are built. Stage 1 (73,819 maps): player_round_glicko map/series log loss 0.640438/0.619448; team_elo 0.662311/0.647815. Offline rebuild plus benchmark: 227.81 s; Kalshi validation pending. Kalshi linking remains future work.

## Known limits

- No form layer: per-player statistics are absent. Kalshi comparison requires linked tables and cached quotes.
- Liquipedia has tournament rosters, not per-match lineups, so stand-ins are missed; no veto data.
- Unknown time zones are counted and treated as UTC with time_known=0; international classification is approximate.
- Liquipedia terms do not address betting/trading use; ask in their #api-help Discord.
- Kalshi collector schedule needs the repository variable and secret before it runs.

## Future work

1. Kalshi backfill including historical endpoints, then linking Kalshi to Liquipedia (port valorant-model's `link.py`: name variants, learned aliases, settlement cross-check).
2. Run `team_elo` and `player_round_glicko` against Kalshi tradeable quotes after links are available.
3. Then, one at a time through the model change rules: rookie discount, form layer (needs per-player stats: find a source), region offsets/regional calibration, map strength.
4. Collect legacy `KXCSGOGAME`/`KXCSGOMAP` if the backfill shows they hold priced 2025 matches.
5. Per-match lineups (Liquipedia LPDB by approval, or GRID Open Access) if stand-ins prove costly.
