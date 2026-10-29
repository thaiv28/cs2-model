# Research ledger

Every model idea tested, adopted or not, newest first, with its numbers. These preliminary leads used parameters tuned on 2025-01-01–2026-08-15 and 1,009 Kalshi series from Aug 16–Oct 29 2026 linked by fuzzy names. Kalshi's last hourly mid before start is sharper than the tradeable quote the benchmark will use; results are leads, not verdicts.

## Scratch study (2026-10-28, before this repo)

- Kalshi pregame mids were under-confident in every tier (calibration slope >1); significant only tier 2: 1.35 [1.02, 1.74].
- Plain team map Elo (K 24, new 1300): log loss 0.598 vs Kalshi 0.534, Δ +0.064 [+0.045, +0.084]; weight beside market +0.08 [−0.14, +0.31]; 5¢-edge bets −25%.
- LoL-style team Elo (margin credit 0.55+0.45·margin, region offsets 0.25, new −50, scale 1.40): Δ +0.071.
- Player Elo (tournament rosters, same credit/offsets, K 32, calibration scale 1.85): tuning log loss 0.620, after 2026-08-16 0.613; vs Kalshi 0.585, Δ +0.050 [+0.034, +0.066]; weight +0.02 [−0.27, +0.32]; bets −24%. Rosters were the largest gain (−0.017 tuning).
- Quote 30 minutes after listing: books mostly empty (median spread 76¢ tier 2, 23¢ tier 1); 122 usable rows, inconclusive.
- Reference: LoL (Prometheus calibration audit, 1,733 series, 12 h quote): model−Kalshi +0.012, weight +0.34 [+0.19, +0.49]; Valorant's first stage-2 run beat Kalshi on series (−0.011 raw, −0.017 blended).
