# Current state

## Status

2026-10-29: Kalshi collector, Liquipedia crawler, offline SQLite build, Kalshi ↔ Liquipedia linking, ratings and the two-stage benchmark are implemented and tested. Real cache: 4,713 pages; DB: 58,034 matches and 119,185 maps, zero parse errors. Kalshi: 41,545 markets (backfill complete); series linked 5,138/7,907, maps 9,131/12,865; result agreements 28,362/28,396. Stage 1 (73,819 maps): player_round_glicko map/series log loss 0.640438/0.619448; team_elo 0.662311/0.647815. Kalshi validation (full backfill): player_round_glicko blended series −0.0118 vs Kalshi (significant; tiers 2–3), raw level; maps no edge; see the research ledger.

## Known limits

- Settlement mismatches need source review; 2,210 markets lack a parseable scheduled time and use the open-time fallback.
- No form layer: per-player statistics are absent.
- Liquipedia has tournament rosters, not per-match lineups, so stand-ins are missed; no veto data.
- Time zones are converted from a fixed abbreviation table (0 unknown on 2026-10-29); unknown ones would be treated as UTC with time_known=0. International classification is approximate.
- Liquipedia terms do not address betting/trading use; ask in their #api-help Discord.
- The scheduled Kalshi collector fails until S3 holds `manifest.json` (seed with a local backfill and `scripts/kalshi_data.sh push`).

## Future work

1. Seed S3 (`promcs kalshi manifest`, `scripts/kalshi_data.sh push`) so the scheduled collector runs; review the unlinked "no team match" events.
2. Then, one at a time through the model change rules: rookie discount, form layer (needs per-player stats: find a source), region offsets/regional calibration, map strength.
3. Collect legacy `KXCSGOGAME`/`KXCSGOMAP` if the backfill shows they hold priced 2025 matches.
4. Per-match lineups (Liquipedia LPDB by approval, or GRID Open Access) if stand-ins prove costly.
