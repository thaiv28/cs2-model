# Current state

## Status

Hourly `refresh-db.yml` and 10-minute `feed.yml` are implemented for S3 snapshot/publication and optional Prometheus dispatch (cron-job.org; hourly GitHub backups). Offline snapshot equality is tested; GitHub runs/timings remain unverified and raw S3 caches need initial seeding.

`promcs export` writes the site feed with frozen calls, replayed results and Kalshi prices; `--no-fetch` runs offline. Ratings require a fresh crawl + setup_db; only DB tournaments are scanned; TBD sides are omitted.

2026-10-29: Kalshi collector, Liquipedia crawler, offline SQLite build, Kalshi ↔ Liquipedia linking, ratings and the two-stage benchmark are implemented and tested. Real cache: 4,713 pages; DB: 58,034 matches and 119,185 maps, zero parse errors. Kalshi: 41,545 markets (backfill complete); series linked 5,138/7,907, maps 9,131/12,865; result agreements 28,362/28,396. Stage 1 (73,819 maps): player_round_glicko map/series log loss 0.640438/0.619448; team_elo 0.662311/0.647815. Kalshi validation (full backfill): player_round_glicko blended series −0.0118 vs Kalshi (significant; tiers 2–3), raw level; maps no edge; see the research ledger. Adopted 2026-10-29: rookie discount 200/400 + tier-3 K × 0.75 (`player_round_glicko_rookie_weights`): stage-2 maps −0.0068 vs base, blended series −0.0145 vs Kalshi.

## Known limits

- Settlement mismatches need source review; 2,210 markets lack a parseable scheduled time and use the open-time fallback.
- No form layer: per-player statistics are absent.
- Liquipedia has tournament rosters, not per-match lineups, so stand-ins are missed; no veto data.
- Time zones are converted from a fixed abbreviation table (0 unknown on 2026-10-29); unknown ones would be treated as UTC with time_known=0. International classification is approximate.
- Liquipedia terms do not address betting/trading use; ask in their #api-help Discord.
- The scheduled Kalshi collector fails until S3 holds `manifest.json` (seed with a local backfill and `scripts/kalshi_data.sh push`).

## Future work

1. Review the unlinked "no team match" events.
2. Then, one at a time through the model change rules: form layer (needs per-player stats: find a source), map strength, a veto-aware map model. Rookie + tier-3 K adopted (ledger, 2026-10-29); calibration, online K and tier moves rejected; regional pending intervals.
3. Collect legacy `KXCSGOGAME`/`KXCSGOMAP` if the backfill shows they hold priced 2025 matches.
4. Resolve Liquipedia team-template aliases (`gl`/`gamerlegion`, `vit`/`vitality`) to one team: they split team history, and cardless keys show as names (`navi`, `tl`) in the site feed.
5. Per-match lineups (Liquipedia LPDB by approval, or GRID Open Access) if stand-ins prove costly.
