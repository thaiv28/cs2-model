# Current state

## Status

2026-10-29: Kalshi collector, Liquipedia crawler, offline SQLite build, Kalshi ↔ Liquipedia linking, ratings and the two-stage benchmark are implemented and tested. Real cache: 4,713 pages; DB: 58,034 matches and 119,185 maps, zero parse errors. Kalshi: 15,795 markets; series linked 5,138/7,897; maps 0/0 (catalog absent); 599 aliases; result agreements 10,172/10,188, 16 mismatches. Stage 1 (73,819 maps): player_round_glicko map/series log loss 0.640438/0.619448; team_elo 0.662311/0.647815. Kalshi validation pending.

## Known limits

- Kalshi backfill is incomplete; map links are tested offline only. Settlement mismatches need source review; 2,210 markets lack a parseable scheduled time and use the open-time fallback.
- No form layer: per-player statistics are absent.
- Liquipedia has tournament rosters, not per-match lineups, so stand-ins are missed; no veto data.
- Time zones are converted from a fixed abbreviation table (0 unknown on 2026-10-29); unknown ones would be treated as UTC with time_known=0. International classification is approximate.
- Liquipedia terms do not address betting/trading use; ask in their #api-help Discord.
- The scheduled Kalshi collector fails until S3 holds `manifest.json` (seed with a local backfill and `scripts/kalshi_data.sh push`).

## Future work

1. Complete the Kalshi backfill, including historical endpoints and map catalogs; rebuild links as catalogs arrive; review the 2,032 "no team match" unlinked events.
2. Run `team_elo` and `player_round_glicko` against Kalshi tradeable quotes now that links exist.
3. Then, one at a time through the model change rules: rookie discount, form layer (needs per-player stats: find a source), region offsets/regional calibration, map strength.
4. Collect legacy `KXCSGOGAME`/`KXCSGOMAP` if the backfill shows they hold priced 2025 matches.
5. Per-match lineups (Liquipedia LPDB by approval, or GRID Open Access) if stand-ins prove costly.
