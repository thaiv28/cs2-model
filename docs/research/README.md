# Research ledger

Every model idea tested, adopted or not, newest first, with its numbers. These preliminary leads used parameters tuned on 2025-01-01–2026-08-15 and 1,009 Kalshi series from Aug 16–Oct 29 2026 linked by fuzzy names. Kalshi's last hourly mid before start is sharper than the tradeable quote the benchmark will use; results are leads, not verdicts.

## Two-stage runs

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
