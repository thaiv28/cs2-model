# Research ledger

Every model idea tested, adopted or not, newest first, with its numbers. These preliminary leads used parameters tuned on 2025-01-01–2026-08-15 and 1,009 Kalshi series from Aug 16–Oct 29 2026 linked by fuzzy names. Kalshi's last hourly mid before start is sharper than the tradeable quote the benchmark will use; results are leads, not verdicts.

## Two-stage runs

2026-10-29 Regional layer retest over the adopted model (fourth stage-2 look; `--baseline` paired tables). Fit on 5,211 cross-region stage-1 maps: s = 0.76 (map), effects EU +0.44, CIS +0.24, AS +0.16, NA +0.10, SA +0.04, OCE −0.45, AF −0.53.

- **Rejected (below the 0.0005 bar, no market gain).** Stage-2 maps −0.00044 [−0.00084, −0.00001]; series −0.00077 [−0.00145, −0.00010]; tier2 significant, no section worse. Vs Kalshi: raw series −0.0046 (adopted −0.0041), blended −0.0144 (−0.0145), blended flat ROI +8.7% (+9.0%).

2026-10-29 Elo candidates (third stage-2 look). Map log loss, candidate − base, paired bootstrap by match; base `player_round_glicko` (K 32, τ 0.5, rd_new 350, info 0.125). Kalshi columns: raw / blended series vs Kalshi, blended series flat ROI (base +0.0003 / −0.0118 / +8.0%).

- **Adopted: rookie discount 200 / 400 maps + tier-3 K × 0.75** (`player_round_glicko_rookie_weights`, online_k 1). Stage 1 −0.0096 [−0.0106, −0.0086], stage 2 −0.0068 [−0.0082, −0.0054]; tier3 −0.0102 significant, tier1 −0.0021 and tier2 +0.0002 n.s. Tier-3 K over rookie alone: stage 1 −0.0015, stage 2 −0.0016 [−0.0020, −0.0012], significant in every tier on both. Kalshi −0.0041 / −0.0145 / +9.0%.
- Rookie alone (200 / 400): stage 2 −0.0052, tier3 significant; Kalshi −0.0017 / −0.0141 / +9.0%. With rd_new 280 / info 0.25 (old variant grid): stage 2 −0.0061 but tier2 significantly worse (+0.0019 [+0.0000, +0.0040]).
- Online K: stage 1 chose 1.0 in every grid — rejected. Tier-3 K without rookie also chose 1.0.
- Rejected: calibration layer by tier × LAN (stage-2 maps −0.0002 over rookie_weights, below 0.0005); tier moves (+0.0004 over rookie). Regional layer not adopted: stage-2 maps −0.0006 (base) / −0.0005 (rookie), interval not computed, blended Kalshi series unchanged (−0.0118 / −0.0138); retest with intervals over the adopted model.
- Scratch script for the paired numbers: candidate replays at frozen parameters (not in repo).

2026-10-29 Kalshi validation on the full backfill (41,545 markets; links: series 5,138/7,907, maps 9,131/12,865). Report: [`docs/elo_backtest.md`](../elo_backtest.md). Frozen stage-1 models, tradeable quote. Supersedes the preliminary run below.

- player_round_glicko, series (4,136): raw +0.0003 [−0.0080, +0.0083]; blended −0.0118 [−0.0170, −0.0066] (significant); tier2 −0.0097 and tier3 −0.0188 significant; tier1 +0.0022 and international +0.0008 n.s. Blended beats Kalshi in 7 of 8 fitted months.
- Maps (4,087): raw +0.0051 (n.s.); blended −0.0027 [−0.0069, +0.0015] (n.s.).
- Flat returns at the ask after fees: blended series +8.0% [+3.7, +12.2] (positive all 8 months), depth-capped +5.5% [+0.2, +11.3]; tier3 +12.1% [+5.5, +19.4]; tier1 −0.1%. Raw series +2.0% [−2.6, +6.8]; raw maps −4.6%, depth-capped −15.0%. Raw full Kelly goes broke; blended LoL-capped series $50 → $6,739 (82.8% drawdown), depth-capped $608.
- team_elo: series raw +0.025, blended n.s.
- Two stage-2 runs so far (this and the preliminary).

2026-10-29 first Kalshi validation — **preliminary: Kalshi backfill ~40% done** (series candles only, no map catalog). Same frozen stage-1 models; tradeable quote (first hourly bid/ask ≥30 min after listing, ≥2 h before start, spread ≤0.06). 1,876 linked series with a quote.

- player_round_glicko raw vs Kalshi: +0.0014 [−0.0100, +0.0130] (n.s.); tier1 +0.024 (n.s.), tier2 +0.002, tier3 −0.009.
- Blended (walk-forward monthly, 1,683 fitted rows): −0.0105 [−0.0191, −0.0028] (significant); tier2 −0.0123 [−0.0235, −0.0009] (significant); tier1 +0.005 (n.s.). Fits a = 1.24–1.41, b = 0.54–0.76 (Apr–Aug).
- Returns, $1 flat at the ask after fees: raw +1.6% [−5.3, +9.1]; blended +6.0% [−0.4, +12.9], tier2 +11.8% [+2.8, +21.7]. Raw full Kelly goes broke (99.9% drawdown); blended LoL-capped Kelly $50 → $480.
- team_elo: raw +0.025, blended +0.0009.
- One stage-2 run; rerun on the full backfill before any decision.

2026-10-29 baseline port — **stage 1 only; Kalshi validation pending**. Tune [2024-01-01,2026-01-01), frozen outcome validation [2026-01-01,2026-11-01); no holdout opened or model adoption decision. Benchmark 201.85 s; offline DB rebuild plus benchmark 227.81 s. Kalshi sections skipped: linking tables absent; zero stage-2 market selection tests.

| Model | Best params | Stage-1 map log loss | Stage-1 series log loss | Map rows | Series rows |
|---|---|---:|---:|---:|---:|
| player_round_glicko | k=32, new_player=teammates, rd_info=0.125, rd_new=350, tau=0.5 | 0.640438 | 0.619448 | 73,819 | 35,914 |
| team_elo | k=32 | 0.662311 | 0.647815 | 73,819 | 35,914 |

Frozen stage-2 outcomes (36,077 maps; 16,918 series): player_round_glicko map/series log loss 0.626260/0.595439; team_elo 0.652391/0.629957. These outcome scores do not replace validation against Kalshi. Series temperatures fitted only on stage 1: Bo3 player=0.83, team=0.70; Bo5 both=0.62.

## Scratch study (2026-10-28, before this repo)

- Kalshi pregame mids were under-confident in every tier (calibration slope >1); significant only tier 2: 1.35 [1.02, 1.74].
- Plain team map Elo (K 24, new 1300): log loss 0.598 vs Kalshi 0.534, Δ +0.064 [+0.045, +0.084]; weight beside market +0.08 [−0.14, +0.31]; 5¢-edge bets −25%.
- LoL-style team Elo (margin credit 0.55+0.45·margin, region offsets 0.25, new −50, scale 1.40): Δ +0.071.
- Player Elo (tournament rosters, same credit/offsets, K 32, calibration scale 1.85): tuning log loss 0.620, after 2026-08-16 0.613; vs Kalshi 0.585, Δ +0.050 [+0.034, +0.066]; weight +0.02 [−0.27, +0.32]; bets −24%. Rosters were the largest gain (−0.017 tuning).
- Quote 30 minutes after listing: books mostly empty (median spread 76¢ tier 2, 23¢ tier 1); 122 usable rows, inconclusive.
- Reference: LoL (Prometheus calibration audit, 1,733 series, 12 h quote): model−Kalshi +0.012, weight +0.34 [+0.19, +0.49]; Valorant's first stage-2 run beat Kalshi on series (−0.011 raw, −0.017 blended).
