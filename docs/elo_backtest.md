# Elo variants benchmark

## Combined summary (validation, all sections)

| Model | Series Δ log loss | Series flat ROI | Series Kelly (LoL caps) $ | Series flat ROI depth-capped | Series Kelly depth-capped $ | Map Δ log loss | Map flat ROI | Map Kelly (LoL caps) $ | Map flat ROI depth-capped | Map Kelly depth-capped $ | Series blended Δ log loss | Series blended flat ROI | Series blended Kelly (LoL caps) $ | Series blended flat ROI depth-capped | Series blended Kelly depth-capped $ | Map blended Δ log loss | Map blended flat ROI | Map blended Kelly (LoL caps) $ | Map blended flat ROI depth-capped | Map blended Kelly depth-capped $ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| team_elo | 0.025040 | -7.18% | $0.09 | -5.72% | $0.08 | 0.023569 | -6.37% | $0.08 | -12.61% | $0.10 | -0.001233 | 0.96% | $14.00 | 2.53% | $25.07 | 0.001058 | -2.22% | $31.69 | -10.09% | $34.17 |
| player_round_glicko | 0.000349 | 1.97% | $0.03 | 0.94% | $0.06 | 0.005111 | -4.62% | $0.09 | -14.96% | $0.08 | -0.011751 | 7.97% | $6738.98 | 5.54% | $607.97 | -0.002692 | 2.87% | $677.73 | -6.72% | $6.17 |
| player_round_glicko_rookie_weights | -0.004138 | 2.94% | $0.03 | 1.04% | $2.70 | 0.003221 | -3.33% | $0.07 | -15.74% | $0.10 | -0.014536 | 8.97% | $9338.30 | 5.92% | $793.67 | -0.003778 | 4.31% | $2453.59 | -8.46% | $8.63 |
| team_elo+none | 0.025040 | -7.18% | $0.09 | -5.72% | $0.08 | 0.023569 | -6.37% | $0.08 | -12.61% | $0.10 | -0.001233 | 0.96% | $14.00 | 2.53% | $25.07 | 0.001058 | -2.22% | $31.69 | -10.09% | $34.17 |
| player_round_glicko+none | 0.000349 | 1.97% | $0.03 | 0.94% | $0.06 | 0.005111 | -4.62% | $0.09 | -14.96% | $0.08 | -0.011751 | 7.97% | $6738.98 | 5.54% | $607.97 | -0.002692 | 2.87% | $677.73 | -6.72% | $6.17 |
| player_round_glicko_rookie_weights+none | -0.004138 | 2.94% | $0.03 | 1.04% | $2.70 | 0.003221 | -3.33% | $0.07 | -15.74% | $0.10 | -0.014536 | 8.97% | $9338.30 | 5.92% | $793.67 | -0.003778 | 4.31% | $2453.59 | -8.46% | $8.63 |

Series temperatures (stage 1; p′ = σ(T·logit p), T < 1 pulls odds toward 50%): team_elo Bo3 0.70, Bo5 0.62; player_round_glicko_rookie_weights Bo3 0.86, Bo5 0.68; player_round_glicko Bo3 0.83, Bo5 0.62; team_elo+none Bo3 0.70, Bo5 0.62; player_round_glicko+none Bo3 0.83, Bo5 0.62; player_round_glicko_rookie_weights+none Bo3 0.86, Bo5 0.68

Parameters minimize tuning map log loss across all sections. Replay predicts before update; Replay starts at the first map. Tuning: [2024-01-01, 2026-01-01); validation: [2026-01-01, 2026-11-01). Holdout is scored only with --holdout and never selects parameters. Series use the first map prediction and independent maps in an odd best-of; missing/even best-of or unknown results are skipped. Accuracy gives 0.5 predictions half credit; ECE uses 10 equal-width bins. Log loss clips probabilities at 1e-6. Paired bootstrap uses 2,000 resamples, seed 0, clustered by match_id. Differences are the named model minus its comparator; negative favors the model. Significance requires a 95% percentile interval excluding zero. Tuning scores are selection diagnostics, not independent evidence of improvement.

Fit through 2025-12-31. Unknown host-region map rows: 911 (including missing/un).

## Stage 1 — tuning (outcomes)

### Leaderboard

| Model | Best params | Map log loss | Series log loss | Rows |
|---|---|---:|---:|---:|
| player_round_glicko_rookie_weights | {"k": 32, "new_player": "teammates", "online_k": 1.0, "rd_info": 0.125, "rd_new": 350, "rookie_maps": 400, "rookie_penalty": 200, "tau": 0.5, "tier3_k": 0.75} | 0.630853 | 0.601048 | 73819 |
| player_round_glicko | {"k": 32, "new_player": "teammates", "rd_info": 0.125, "rd_new": 350, "tau": 0.5} | 0.640438 | 0.619448 | 73819 |
| team_elo | {"k": 32} | 0.662311 | 0.647815 | 73819 |

Kalshi uses the first hourly bid/ask (midpoint for log loss, ask/bid for bets) ending ≥30 min after the market opened and ≥2 h before the scheduled start, with a spread ≤ 0.06: a price a bot could trade before any veto. Markets without such a quote are skipped. oriented to team1 using aliases. One contract per event, preferring team1. Compare identical rows; map predictions use the first map's pre-match chance. Missing links, aliases or candles are skipped; unplayed maps are not in the rows. Returns use frozen stage-1 parameters. Each bet buys $1 of contracts, fees extra; order fees ceil to a cent (0.07 × contracts × price × (1−price)). Edge selection uses unrounded per-contract fees. ROI divides profit by stake plus fees; intervals resample matches 2,000 times. Unlimited depth and depth-capped returns are shown together. Depth uses 0.5 of acceptable-price tape volume in the 6 hours after the quote, missing tapes give zero fills. Partial Kelly fills are allowed; flat bets require the full $1 stake. Kelly uses LoL caps and rounded-fee affordability, from a $50 seed. Each slice runs independently. Tape volume is a fill proxy; no slippage is modeled.

### Maps

| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |
|---|---|---:|---:|---:|---:|---:|
| coin | all | 73819 | 0.693147 | 0.250000 | 0.500000 | 0.047813 |
| coin | tier1 | 4470 | 0.693147 | 0.250000 | 0.500000 | 0.041163 |
| coin | tier2 | 18909 | 0.693147 | 0.250000 | 0.500000 | 0.047464 |
| coin | tier3 | 50234 | 0.693147 | 0.250000 | 0.500000 | 0.048732 |
| coin | unknown | 206 | 0.693147 | 0.250000 | 0.500000 | 0.000000 |
| coin | international=1 | 2557 | 0.693147 | 0.250000 | 0.500000 | 0.029918 |
| coin | international=0 | 71262 | 0.693147 | 0.250000 | 0.500000 | 0.048455 |

| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |
|---|---|---:|---:|---:|---:|---:|
| team_elo | all | 73819 | 0.662311 | 0.234947 | 0.600279 | 0.029382 |
| team_elo | tier1 | 4470 | 0.678715 | 0.242288 | 0.590492 | 0.046219 |
| team_elo | tier2 | 18909 | 0.665657 | 0.236329 | 0.599582 | 0.026667 |
| team_elo | tier3 | 50234 | 0.659619 | 0.233785 | 0.601386 | 0.031173 |
| team_elo | unknown | 206 | 0.655716 | 0.232119 | 0.606796 | 0.057565 |
| team_elo | international=1 | 2557 | 0.672091 | 0.239073 | 0.606179 | 0.038953 |
| team_elo | international=0 | 71262 | 0.661960 | 0.234799 | 0.600067 | 0.029473 |

team_elo − coin (paired log loss):

| Section | Rows | team_elo log loss | coin log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 73819 | 0.662311 | 0.693147 | -0.030836 | [-0.033031, -0.028737] | yes |

| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |
|---|---|---:|---:|---:|---:|---:|
| player_round_glicko | all | 73819 | 0.640438 | 0.225132 | 0.625814 | 0.020785 |
| player_round_glicko | tier1 | 4470 | 0.664089 | 0.236026 | 0.594183 | 0.015347 |
| player_round_glicko | tier2 | 18909 | 0.648714 | 0.228984 | 0.612407 | 0.016386 |
| player_round_glicko | tier3 | 50234 | 0.635223 | 0.222705 | 0.633814 | 0.023211 |
| player_round_glicko | unknown | 206 | 0.639405 | 0.226708 | 0.592233 | 0.059067 |
| player_round_glicko | international=1 | 2557 | 0.661855 | 0.235023 | 0.601095 | 0.016882 |
| player_round_glicko | international=0 | 71262 | 0.639670 | 0.224777 | 0.626701 | 0.021278 |

player_round_glicko − coin (paired log loss):

| Section | Rows | player_round_glicko log loss | coin log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 73819 | 0.640438 | 0.693147 | -0.052709 | [-0.055092, -0.050357] | yes |

| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |
|---|---|---:|---:|---:|---:|---:|
| player_round_glicko_rookie_weights | all | 73819 | 0.630853 | 0.220812 | 0.638332 | 0.016673 |
| player_round_glicko_rookie_weights | tier1 | 4470 | 0.662291 | 0.234655 | 0.602237 | 0.017643 |
| player_round_glicko_rookie_weights | tier2 | 18909 | 0.646405 | 0.227760 | 0.619758 | 0.014344 |
| player_round_glicko_rookie_weights | tier3 | 50234 | 0.622220 | 0.216967 | 0.648585 | 0.018140 |
| player_round_glicko_rookie_weights | unknown | 206 | 0.626325 | 0.220345 | 0.626214 | 0.083042 |
| player_round_glicko_rookie_weights | international=1 | 2557 | 0.658316 | 0.233376 | 0.606961 | 0.022340 |
| player_round_glicko_rookie_weights | international=0 | 71262 | 0.629868 | 0.220361 | 0.639457 | 0.017146 |

player_round_glicko_rookie_weights − coin (paired log loss):

| Section | Rows | player_round_glicko_rookie_weights log loss | coin log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 73819 | 0.630853 | 0.693147 | -0.062294 | [-0.064826, -0.059778] | yes |

player_round_glicko_rookie_weights − team_elo (paired log loss):

| Section | Rows | player_round_glicko_rookie_weights log loss | team_elo log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 73819 | 0.630853 | 0.662311 | -0.031458 | [-0.033425, -0.029498] | yes |

player_round_glicko − team_elo (paired log loss):

| Section | Rows | player_round_glicko log loss | team_elo log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 73819 | 0.640438 | 0.662311 | -0.021872 | [-0.023603, -0.020135] | yes |

player_round_glicko − player_round_glicko_rookie_weights (paired log loss):

| Section | Rows | player_round_glicko log loss | player_round_glicko_rookie_weights log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 73819 | 0.640438 | 0.630853 | 0.009585 | [0.008597, 0.010607] | yes |

### Series

| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |
|---|---|---:|---:|---:|---:|---:|
| coin | all | 35914 | 0.693147 | 0.250000 | 0.500000 | 0.062260 |
| coin | tier1 | 2047 | 0.693147 | 0.250000 | 0.500000 | 0.055447 |
| coin | tier2 | 8853 | 0.693147 | 0.250000 | 0.500000 | 0.064328 |
| coin | tier3 | 24957 | 0.693147 | 0.250000 | 0.500000 | 0.062047 |
| coin | unknown | 57 | 0.693147 | 0.250000 | 0.500000 | 0.078947 |
| coin | international=1 | 1101 | 0.693147 | 0.250000 | 0.500000 | 0.038601 |
| coin | international=0 | 34813 | 0.693147 | 0.250000 | 0.500000 | 0.063008 |

| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |
|---|---|---:|---:|---:|---:|---:|
| team_elo | all | 35914 | 0.647815 | 0.228329 | 0.616514 | 0.037711 |
| team_elo | tier1 | 2047 | 0.666406 | 0.236331 | 0.603566 | 0.047103 |
| team_elo | tier2 | 8853 | 0.648431 | 0.228434 | 0.621315 | 0.030236 |
| team_elo | tier3 | 24957 | 0.645979 | 0.227592 | 0.616000 | 0.042211 |
| team_elo | unknown | 57 | 0.688489 | 0.247659 | 0.561404 | 0.175937 |
| team_elo | international=1 | 1101 | 0.655023 | 0.230996 | 0.618529 | 0.040831 |
| team_elo | international=0 | 34813 | 0.647587 | 0.228245 | 0.616451 | 0.038677 |

team_elo − coin (paired log loss):

| Section | Rows | team_elo log loss | coin log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 35914 | 0.647815 | 0.693147 | -0.045332 | [-0.048354, -0.042268] | yes |

| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |
|---|---|---:|---:|---:|---:|---:|
| player_round_glicko | all | 35914 | 0.619448 | 0.215365 | 0.653102 | 0.028715 |
| player_round_glicko | tier1 | 2047 | 0.648729 | 0.228987 | 0.615291 | 0.020370 |
| player_round_glicko | tier2 | 8853 | 0.624454 | 0.218044 | 0.643115 | 0.027977 |
| player_round_glicko | tier3 | 24957 | 0.615064 | 0.213198 | 0.660115 | 0.031142 |
| player_round_glicko | unknown | 57 | 0.709887 | 0.258925 | 0.491228 | 0.139781 |
| player_round_glicko | international=1 | 1101 | 0.643493 | 0.226834 | 0.618074 | 0.019919 |
| player_round_glicko | international=0 | 34813 | 0.618688 | 0.215002 | 0.654210 | 0.029402 |

player_round_glicko − coin (paired log loss):

| Section | Rows | player_round_glicko log loss | coin log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 35914 | 0.619448 | 0.693147 | -0.073699 | [-0.077493, -0.069825] | yes |

| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |
|---|---|---:|---:|---:|---:|---:|
| player_round_glicko_rookie_weights | all | 35914 | 0.601048 | 0.206992 | 0.673275 | 0.023050 |
| player_round_glicko_rookie_weights | tier1 | 2047 | 0.648547 | 0.226789 | 0.623351 | 0.017715 |
| player_round_glicko_rookie_weights | tier2 | 8853 | 0.620414 | 0.215685 | 0.650570 | 0.021133 |
| player_round_glicko_rookie_weights | tier3 | 24957 | 0.590117 | 0.202208 | 0.685679 | 0.024559 |
| player_round_glicko_rookie_weights | unknown | 57 | 0.672906 | 0.240730 | 0.561404 | 0.126948 |
| player_round_glicko_rookie_weights | international=1 | 1101 | 0.638671 | 0.224407 | 0.626703 | 0.029462 |
| player_round_glicko_rookie_weights | international=0 | 34813 | 0.599858 | 0.206441 | 0.674748 | 0.023655 |

player_round_glicko_rookie_weights − coin (paired log loss):

| Section | Rows | player_round_glicko_rookie_weights log loss | coin log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 35914 | 0.601048 | 0.693147 | -0.092100 | [-0.096285, -0.087713] | yes |

player_round_glicko_rookie_weights − team_elo (paired log loss):

| Section | Rows | player_round_glicko_rookie_weights log loss | team_elo log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 35914 | 0.601048 | 0.647815 | -0.046768 | [-0.050176, -0.043202] | yes |

player_round_glicko − team_elo (paired log loss):

| Section | Rows | player_round_glicko log loss | team_elo log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 35914 | 0.619448 | 0.647815 | -0.028367 | [-0.031333, -0.025414] | yes |

player_round_glicko − player_round_glicko_rookie_weights (paired log loss):

| Section | Rows | player_round_glicko log loss | player_round_glicko_rookie_weights log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 35914 | 0.619448 | 0.601048 | 0.018401 | [0.016410, 0.020411] | yes |

## Stage 2 — validation (outcomes)

### Leaderboard (frozen stage-1 parameters)

| Model | Best params | Map log loss | Series log loss | Rows |
|---|---|---:|---:|---:|
| player_round_glicko_rookie_weights | {"k": 32, "new_player": "teammates", "online_k": 1.0, "rd_info": 0.125, "rd_new": 350, "rookie_maps": 400, "rookie_penalty": 200, "tau": 0.5, "tier3_k": 0.75} | 0.619451 | 0.581653 | 36077 |
| player_round_glicko_rookie_weights+none | {"k": 32, "new_player": "teammates", "online_k": 1.0, "rd_info": 0.125, "rd_new": 350, "rookie_maps": 400, "rookie_penalty": 200, "tau": 0.5, "tier3_k": 0.75} | 0.619451 | 0.581653 | 36077 |
| player_round_glicko | {"k": 32, "new_player": "teammates", "rd_info": 0.125, "rd_new": 350, "tau": 0.5} | 0.626260 | 0.595439 | 36077 |
| player_round_glicko+none | {"k": 32, "new_player": "teammates", "rd_info": 0.125, "rd_new": 350, "tau": 0.5} | 0.626260 | 0.595439 | 36077 |
| team_elo | {"k": 32} | 0.652391 | 0.629957 | 36077 |
| team_elo+none | {"k": 32} | 0.652391 | 0.629957 | 36077 |

### Maps

| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |
|---|---|---:|---:|---:|---:|---:|
| coin | all | 36077 | 0.693147 | 0.250000 | 0.500000 | 0.053760 |
| coin | tier1 | 2097 | 0.693147 | 0.250000 | 0.500000 | 0.037911 |
| coin | tier2 | 9801 | 0.693147 | 0.250000 | 0.500000 | 0.056984 |
| coin | tier3 | 23489 | 0.693147 | 0.250000 | 0.500000 | 0.053067 |
| coin | unknown | 690 | 0.693147 | 0.250000 | 0.500000 | 0.079710 |
| coin | international=1 | 1194 | 0.693147 | 0.250000 | 0.500000 | 0.030151 |
| coin | international=0 | 34883 | 0.693147 | 0.250000 | 0.500000 | 0.054568 |

| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |
|---|---|---:|---:|---:|---:|---:|
| team_elo | all | 36077 | 0.652391 | 0.230428 | 0.613424 | 0.028588 |
| team_elo | tier1 | 2097 | 0.674661 | 0.238679 | 0.604435 | 0.043184 |
| team_elo | tier2 | 9801 | 0.659961 | 0.233827 | 0.608356 | 0.038003 |
| team_elo | tier3 | 23489 | 0.648448 | 0.228798 | 0.615160 | 0.027770 |
| team_elo | unknown | 690 | 0.611439 | 0.212553 | 0.653623 | 0.068574 |
| team_elo | international=1 | 1194 | 0.646788 | 0.227343 | 0.637353 | 0.029602 |
| team_elo | international=0 | 34883 | 0.652583 | 0.230533 | 0.612605 | 0.029068 |

team_elo − coin (paired log loss):

| Section | Rows | team_elo log loss | coin log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 36077 | 0.652391 | 0.693147 | -0.040756 | [-0.044232, -0.037291] | yes |
| tier1 | 2097 | 0.674661 | 0.693147 | -0.018486 | [-0.034901, -0.000820] | yes |
| tier2 | 9801 | 0.659961 | 0.693147 | -0.033186 | [-0.040697, -0.026142] | yes |
| tier3 | 23489 | 0.648448 | 0.693147 | -0.044700 | [-0.048683, -0.040683] | yes |
| unknown | 690 | 0.611439 | 0.693147 | -0.081708 | [-0.109116, -0.054963] | yes |
| international=1 | 1194 | 0.646788 | 0.693147 | -0.046359 | [-0.069677, -0.023168] | yes |
| international=0 | 34883 | 0.652583 | 0.693147 | -0.040564 | [-0.044131, -0.037045] | yes |

| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |
|---|---|---:|---:|---:|---:|---:|
| player_round_glicko | all | 36077 | 0.626260 | 0.219076 | 0.641600 | 0.018393 |
| player_round_glicko | tier1 | 2097 | 0.661100 | 0.234238 | 0.607058 | 0.021157 |
| player_round_glicko | tier2 | 9801 | 0.632278 | 0.221972 | 0.633099 | 0.014803 |
| player_round_glicko | tier3 | 23489 | 0.621607 | 0.216919 | 0.647473 | 0.020083 |
| player_round_glicko | unknown | 690 | 0.593259 | 0.205284 | 0.667391 | 0.055349 |
| player_round_glicko | international=1 | 1194 | 0.643761 | 0.226468 | 0.636935 | 0.031372 |
| player_round_glicko | international=0 | 34883 | 0.625661 | 0.218823 | 0.641760 | 0.019014 |

player_round_glicko − coin (paired log loss):

| Section | Rows | player_round_glicko log loss | coin log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 36077 | 0.626260 | 0.693147 | -0.066887 | [-0.070511, -0.063157] | yes |
| tier1 | 2097 | 0.661100 | 0.693147 | -0.032047 | [-0.044186, -0.019775] | yes |
| tier2 | 9801 | 0.632278 | 0.693147 | -0.060869 | [-0.067314, -0.054626] | yes |
| tier3 | 23489 | 0.621607 | 0.693147 | -0.071540 | [-0.076140, -0.066941] | yes |
| unknown | 690 | 0.593259 | 0.693147 | -0.099888 | [-0.127200, -0.072400] | yes |
| international=1 | 1194 | 0.643761 | 0.693147 | -0.049386 | [-0.066228, -0.033562] | yes |
| international=0 | 34883 | 0.625661 | 0.693147 | -0.067487 | [-0.071254, -0.063639] | yes |

| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |
|---|---|---:|---:|---:|---:|---:|
| player_round_glicko_rookie_weights | all | 36077 | 0.619451 | 0.215993 | 0.649001 | 0.015926 |
| player_round_glicko_rookie_weights | tier1 | 2097 | 0.658998 | 0.233216 | 0.605627 | 0.020894 |
| player_round_glicko_rookie_weights | tier2 | 9801 | 0.632473 | 0.221618 | 0.637333 | 0.019141 |
| player_round_glicko_rookie_weights | tier3 | 23489 | 0.611418 | 0.212485 | 0.657414 | 0.016692 |
| player_round_glicko_rookie_weights | unknown | 690 | 0.587761 | 0.203147 | 0.660145 | 0.071593 |
| player_round_glicko_rookie_weights | international=1 | 1194 | 0.641858 | 0.225649 | 0.631910 | 0.032961 |
| player_round_glicko_rookie_weights | international=0 | 34883 | 0.618684 | 0.215662 | 0.649586 | 0.016589 |

player_round_glicko_rookie_weights − coin (paired log loss):

| Section | Rows | player_round_glicko_rookie_weights log loss | coin log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 36077 | 0.619451 | 0.693147 | -0.073696 | [-0.077594, -0.069668] | yes |
| tier1 | 2097 | 0.658998 | 0.693147 | -0.034150 | [-0.045949, -0.021366] | yes |
| tier2 | 9801 | 0.632473 | 0.693147 | -0.060674 | [-0.067442, -0.054321] | yes |
| tier3 | 23489 | 0.611418 | 0.693147 | -0.081730 | [-0.086648, -0.076910] | yes |
| unknown | 690 | 0.587761 | 0.693147 | -0.105386 | [-0.133865, -0.077871] | yes |
| international=1 | 1194 | 0.641858 | 0.693147 | -0.051289 | [-0.068404, -0.034528] | yes |
| international=0 | 34883 | 0.618684 | 0.693147 | -0.074463 | [-0.078181, -0.070331] | yes |

| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |
|---|---|---:|---:|---:|---:|---:|
| team_elo+none | all | 36077 | 0.652391 | 0.230428 | 0.613424 | 0.028588 |
| team_elo+none | tier1 | 2097 | 0.674661 | 0.238679 | 0.604435 | 0.043184 |
| team_elo+none | tier2 | 9801 | 0.659961 | 0.233827 | 0.608356 | 0.038003 |
| team_elo+none | tier3 | 23489 | 0.648448 | 0.228798 | 0.615160 | 0.027770 |
| team_elo+none | unknown | 690 | 0.611439 | 0.212553 | 0.653623 | 0.068574 |
| team_elo+none | international=1 | 1194 | 0.646788 | 0.227343 | 0.637353 | 0.029602 |
| team_elo+none | international=0 | 34883 | 0.652583 | 0.230533 | 0.612605 | 0.029068 |

team_elo+none − coin (paired log loss):

| Section | Rows | team_elo+none log loss | coin log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 36077 | 0.652391 | 0.693147 | -0.040756 | [-0.044232, -0.037291] | yes |
| tier1 | 2097 | 0.674661 | 0.693147 | -0.018486 | [-0.034901, -0.000820] | yes |
| tier2 | 9801 | 0.659961 | 0.693147 | -0.033186 | [-0.040697, -0.026142] | yes |
| tier3 | 23489 | 0.648448 | 0.693147 | -0.044700 | [-0.048683, -0.040683] | yes |
| unknown | 690 | 0.611439 | 0.693147 | -0.081708 | [-0.109116, -0.054963] | yes |
| international=1 | 1194 | 0.646788 | 0.693147 | -0.046359 | [-0.069677, -0.023168] | yes |
| international=0 | 34883 | 0.652583 | 0.693147 | -0.040564 | [-0.044131, -0.037045] | yes |

| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |
|---|---|---:|---:|---:|---:|---:|
| player_round_glicko+none | all | 36077 | 0.626260 | 0.219076 | 0.641600 | 0.018393 |
| player_round_glicko+none | tier1 | 2097 | 0.661100 | 0.234238 | 0.607058 | 0.021157 |
| player_round_glicko+none | tier2 | 9801 | 0.632278 | 0.221972 | 0.633099 | 0.014803 |
| player_round_glicko+none | tier3 | 23489 | 0.621607 | 0.216919 | 0.647473 | 0.020083 |
| player_round_glicko+none | unknown | 690 | 0.593259 | 0.205284 | 0.667391 | 0.055349 |
| player_round_glicko+none | international=1 | 1194 | 0.643761 | 0.226468 | 0.636935 | 0.031372 |
| player_round_glicko+none | international=0 | 34883 | 0.625661 | 0.218823 | 0.641760 | 0.019014 |

player_round_glicko+none − coin (paired log loss):

| Section | Rows | player_round_glicko+none log loss | coin log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 36077 | 0.626260 | 0.693147 | -0.066887 | [-0.070511, -0.063157] | yes |
| tier1 | 2097 | 0.661100 | 0.693147 | -0.032047 | [-0.044186, -0.019775] | yes |
| tier2 | 9801 | 0.632278 | 0.693147 | -0.060869 | [-0.067314, -0.054626] | yes |
| tier3 | 23489 | 0.621607 | 0.693147 | -0.071540 | [-0.076140, -0.066941] | yes |
| unknown | 690 | 0.593259 | 0.693147 | -0.099888 | [-0.127200, -0.072400] | yes |
| international=1 | 1194 | 0.643761 | 0.693147 | -0.049386 | [-0.066228, -0.033562] | yes |
| international=0 | 34883 | 0.625661 | 0.693147 | -0.067487 | [-0.071254, -0.063639] | yes |

| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |
|---|---|---:|---:|---:|---:|---:|
| player_round_glicko_rookie_weights+none | all | 36077 | 0.619451 | 0.215993 | 0.649001 | 0.015926 |
| player_round_glicko_rookie_weights+none | tier1 | 2097 | 0.658998 | 0.233216 | 0.605627 | 0.020894 |
| player_round_glicko_rookie_weights+none | tier2 | 9801 | 0.632473 | 0.221618 | 0.637333 | 0.019141 |
| player_round_glicko_rookie_weights+none | tier3 | 23489 | 0.611418 | 0.212485 | 0.657414 | 0.016692 |
| player_round_glicko_rookie_weights+none | unknown | 690 | 0.587761 | 0.203147 | 0.660145 | 0.071593 |
| player_round_glicko_rookie_weights+none | international=1 | 1194 | 0.641858 | 0.225649 | 0.631910 | 0.032961 |
| player_round_glicko_rookie_weights+none | international=0 | 34883 | 0.618684 | 0.215662 | 0.649586 | 0.016589 |

player_round_glicko_rookie_weights+none − coin (paired log loss):

| Section | Rows | player_round_glicko_rookie_weights+none log loss | coin log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 36077 | 0.619451 | 0.693147 | -0.073696 | [-0.077594, -0.069668] | yes |
| tier1 | 2097 | 0.658998 | 0.693147 | -0.034150 | [-0.045949, -0.021366] | yes |
| tier2 | 9801 | 0.632473 | 0.693147 | -0.060674 | [-0.067442, -0.054321] | yes |
| tier3 | 23489 | 0.611418 | 0.693147 | -0.081730 | [-0.086648, -0.076910] | yes |
| unknown | 690 | 0.587761 | 0.693147 | -0.105386 | [-0.133865, -0.077871] | yes |
| international=1 | 1194 | 0.641858 | 0.693147 | -0.051289 | [-0.068404, -0.034528] | yes |
| international=0 | 34883 | 0.618684 | 0.693147 | -0.074463 | [-0.078181, -0.070331] | yes |

player_round_glicko − team_elo (paired log loss):

| Section | Rows | player_round_glicko log loss | team_elo log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 36077 | 0.626260 | 0.652391 | -0.026132 | [-0.028814, -0.023537] | yes |

player_round_glicko_rookie_weights − team_elo (paired log loss):

| Section | Rows | player_round_glicko_rookie_weights log loss | team_elo log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 36077 | 0.619451 | 0.652391 | -0.032940 | [-0.035909, -0.029975] | yes |

team_elo+none − team_elo (paired log loss):

| Section | Rows | team_elo+none log loss | team_elo log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 36077 | 0.652391 | 0.652391 | 0.000000 | [0.000000, 0.000000] | no |

player_round_glicko+none − team_elo (paired log loss):

| Section | Rows | player_round_glicko+none log loss | team_elo log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 36077 | 0.626260 | 0.652391 | -0.026132 | [-0.028814, -0.023537] | yes |

player_round_glicko_rookie_weights+none − team_elo (paired log loss):

| Section | Rows | player_round_glicko_rookie_weights+none log loss | team_elo log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 36077 | 0.619451 | 0.652391 | -0.032940 | [-0.035909, -0.029975] | yes |

player_round_glicko − player_round_glicko_rookie_weights (paired log loss):

| Section | Rows | player_round_glicko log loss | player_round_glicko_rookie_weights log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 36077 | 0.626260 | 0.619451 | 0.006809 | [0.005421, 0.008216] | yes |
| tier1 | 2097 | 0.661100 | 0.658998 | 0.002103 | [-0.000310, 0.004519] | no |
| tier2 | 9801 | 0.632278 | 0.632473 | -0.000195 | [-0.002216, 0.001550] | no |
| tier3 | 23489 | 0.621607 | 0.611418 | 0.010190 | [0.008272, 0.012165] | yes |
| unknown | 690 | 0.593259 | 0.587761 | 0.005498 | [0.000276, 0.011280] | yes |
| international=1 | 1194 | 0.643761 | 0.641858 | 0.001903 | [-0.001055, 0.005166] | no |
| international=0 | 34883 | 0.625661 | 0.618684 | 0.006977 | [0.005583, 0.008368] | yes |

team_elo+none − player_round_glicko_rookie_weights (paired log loss):

| Section | Rows | team_elo+none log loss | player_round_glicko_rookie_weights log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 36077 | 0.652391 | 0.619451 | 0.032940 | [0.029975, 0.035909] | yes |
| tier1 | 2097 | 0.674661 | 0.658998 | 0.015664 | [0.005571, 0.026501] | yes |
| tier2 | 9801 | 0.659961 | 0.632473 | 0.027487 | [0.022348, 0.032577] | yes |
| tier3 | 23489 | 0.648448 | 0.611418 | 0.037030 | [0.033182, 0.040819] | yes |
| unknown | 690 | 0.611439 | 0.587761 | 0.023679 | [0.006902, 0.041396] | yes |
| international=1 | 1194 | 0.646788 | 0.641858 | 0.004930 | [-0.008170, 0.017670] | no |
| international=0 | 34883 | 0.652583 | 0.618684 | 0.033899 | [0.030872, 0.036879] | yes |

player_round_glicko+none − player_round_glicko_rookie_weights (paired log loss):

| Section | Rows | player_round_glicko+none log loss | player_round_glicko_rookie_weights log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 36077 | 0.626260 | 0.619451 | 0.006809 | [0.005421, 0.008216] | yes |
| tier1 | 2097 | 0.661100 | 0.658998 | 0.002103 | [-0.000310, 0.004519] | no |
| tier2 | 9801 | 0.632278 | 0.632473 | -0.000195 | [-0.002216, 0.001550] | no |
| tier3 | 23489 | 0.621607 | 0.611418 | 0.010190 | [0.008272, 0.012165] | yes |
| unknown | 690 | 0.593259 | 0.587761 | 0.005498 | [0.000276, 0.011280] | yes |
| international=1 | 1194 | 0.643761 | 0.641858 | 0.001903 | [-0.001055, 0.005166] | no |
| international=0 | 34883 | 0.625661 | 0.618684 | 0.006977 | [0.005583, 0.008368] | yes |

player_round_glicko_rookie_weights+none − player_round_glicko_rookie_weights (paired log loss):

| Section | Rows | player_round_glicko_rookie_weights+none log loss | player_round_glicko_rookie_weights log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 36077 | 0.619451 | 0.619451 | 0.000000 | [0.000000, 0.000000] | no |
| tier1 | 2097 | 0.658998 | 0.658998 | 0.000000 | [0.000000, 0.000000] | no |
| tier2 | 9801 | 0.632473 | 0.632473 | 0.000000 | [0.000000, 0.000000] | no |
| tier3 | 23489 | 0.611418 | 0.611418 | 0.000000 | [0.000000, 0.000000] | no |
| unknown | 690 | 0.587761 | 0.587761 | 0.000000 | [0.000000, 0.000000] | no |
| international=1 | 1194 | 0.641858 | 0.641858 | 0.000000 | [0.000000, 0.000000] | no |
| international=0 | 34883 | 0.618684 | 0.618684 | 0.000000 | [0.000000, 0.000000] | no |

### Series

| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |
|---|---|---:|---:|---:|---:|---:|
| coin | all | 16918 | 0.693147 | 0.250000 | 0.500000 | 0.070812 |
| coin | tier1 | 897 | 0.693147 | 0.250000 | 0.500000 | 0.046265 |
| coin | tier2 | 4498 | 0.693147 | 0.250000 | 0.500000 | 0.079813 |
| coin | tier3 | 11240 | 0.693147 | 0.250000 | 0.500000 | 0.067883 |
| coin | unknown | 283 | 0.693147 | 0.250000 | 0.500000 | 0.121908 |
| coin | international=1 | 503 | 0.693147 | 0.250000 | 0.500000 | 0.034791 |
| coin | international=0 | 16415 | 0.693147 | 0.250000 | 0.500000 | 0.071916 |

| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |
|---|---|---:|---:|---:|---:|---:|
| team_elo | all | 16918 | 0.629957 | 0.220403 | 0.638551 | 0.035174 |
| team_elo | tier1 | 897 | 0.648564 | 0.226385 | 0.630992 | 0.039996 |
| team_elo | tier2 | 4498 | 0.638324 | 0.223889 | 0.636616 | 0.041479 |
| team_elo | tier3 | 11240 | 0.626909 | 0.219252 | 0.638212 | 0.039184 |
| team_elo | unknown | 283 | 0.559052 | 0.191764 | 0.706714 | 0.103839 |
| team_elo | international=1 | 503 | 0.613896 | 0.212376 | 0.670974 | 0.028384 |
| team_elo | international=0 | 16415 | 0.630449 | 0.220649 | 0.637557 | 0.036578 |

team_elo − coin (paired log loss):

| Section | Rows | team_elo log loss | coin log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 16918 | 0.629957 | 0.693147 | -0.063190 | [-0.067917, -0.058265] | yes |
| tier1 | 897 | 0.648564 | 0.693147 | -0.044583 | [-0.071885, -0.015822] | yes |
| tier2 | 4498 | 0.638324 | 0.693147 | -0.054823 | [-0.065863, -0.043994] | yes |
| tier3 | 11240 | 0.626909 | 0.693147 | -0.066238 | [-0.071731, -0.060569] | yes |
| unknown | 283 | 0.559052 | 0.693147 | -0.134096 | [-0.173073, -0.095930] | yes |
| international=1 | 503 | 0.613896 | 0.693147 | -0.079251 | [-0.114812, -0.043166] | yes |
| international=0 | 16415 | 0.630449 | 0.693147 | -0.062698 | [-0.067843, -0.057582] | yes |

| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |
|---|---|---:|---:|---:|---:|---:|
| player_round_glicko | all | 16918 | 0.595439 | 0.205158 | 0.677799 | 0.025511 |
| player_round_glicko | tier1 | 897 | 0.641270 | 0.224875 | 0.630992 | 0.027225 |
| player_round_glicko | tier2 | 4498 | 0.599020 | 0.207171 | 0.671521 | 0.023210 |
| player_round_glicko | tier3 | 11240 | 0.591753 | 0.203280 | 0.683274 | 0.027538 |
| player_round_glicko | unknown | 283 | 0.539658 | 0.185262 | 0.708481 | 0.080770 |
| player_round_glicko | international=1 | 503 | 0.617316 | 0.214670 | 0.660040 | 0.037389 |
| player_round_glicko | international=0 | 16415 | 0.594769 | 0.204866 | 0.678343 | 0.026294 |

player_round_glicko − coin (paired log loss):

| Section | Rows | player_round_glicko log loss | coin log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 16918 | 0.595439 | 0.693147 | -0.097708 | [-0.103728, -0.091565] | yes |
| tier1 | 897 | 0.641270 | 0.693147 | -0.051877 | [-0.071628, -0.029298] | yes |
| tier2 | 4498 | 0.599020 | 0.693147 | -0.094127 | [-0.105019, -0.083510] | yes |
| tier3 | 11240 | 0.591753 | 0.693147 | -0.101394 | [-0.108759, -0.093815] | yes |
| unknown | 283 | 0.539658 | 0.693147 | -0.153490 | [-0.193225, -0.111088] | yes |
| international=1 | 503 | 0.617316 | 0.693147 | -0.075831 | [-0.104084, -0.047276] | yes |
| international=0 | 16415 | 0.594769 | 0.693147 | -0.098378 | [-0.104565, -0.091977] | yes |

| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |
|---|---|---:|---:|---:|---:|---:|
| player_round_glicko_rookie_weights | all | 16918 | 0.581653 | 0.198965 | 0.691926 | 0.022578 |
| player_round_glicko_rookie_weights | tier1 | 897 | 0.638121 | 0.223483 | 0.637681 | 0.028362 |
| player_round_glicko_rookie_weights | tier2 | 4498 | 0.598446 | 0.206018 | 0.679080 | 0.026958 |
| player_round_glicko_rookie_weights | tier3 | 11240 | 0.571799 | 0.194642 | 0.701068 | 0.021834 |
| player_round_glicko_rookie_weights | unknown | 283 | 0.527109 | 0.180835 | 0.704947 | 0.082998 |
| player_round_glicko_rookie_weights | international=1 | 503 | 0.615878 | 0.213964 | 0.660040 | 0.037654 |
| player_round_glicko_rookie_weights | international=0 | 16415 | 0.580604 | 0.198505 | 0.692903 | 0.022915 |

player_round_glicko_rookie_weights − coin (paired log loss):

| Section | Rows | player_round_glicko_rookie_weights log loss | coin log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 16918 | 0.581653 | 0.693147 | -0.111494 | [-0.118067, -0.105028] | yes |
| tier1 | 897 | 0.638121 | 0.693147 | -0.055027 | [-0.076196, -0.031192] | yes |
| tier2 | 4498 | 0.598446 | 0.693147 | -0.094701 | [-0.106526, -0.082848] | yes |
| tier3 | 11240 | 0.571799 | 0.693147 | -0.121348 | [-0.129111, -0.113138] | yes |
| unknown | 283 | 0.527109 | 0.693147 | -0.166038 | [-0.207432, -0.123091] | yes |
| international=1 | 503 | 0.615878 | 0.693147 | -0.077270 | [-0.106563, -0.046462] | yes |
| international=0 | 16415 | 0.580604 | 0.693147 | -0.112543 | [-0.119148, -0.105576] | yes |

| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |
|---|---|---:|---:|---:|---:|---:|
| team_elo+none | all | 16918 | 0.629957 | 0.220403 | 0.638551 | 0.035174 |
| team_elo+none | tier1 | 897 | 0.648564 | 0.226385 | 0.630992 | 0.039996 |
| team_elo+none | tier2 | 4498 | 0.638324 | 0.223889 | 0.636616 | 0.041479 |
| team_elo+none | tier3 | 11240 | 0.626909 | 0.219252 | 0.638212 | 0.039184 |
| team_elo+none | unknown | 283 | 0.559052 | 0.191764 | 0.706714 | 0.103839 |
| team_elo+none | international=1 | 503 | 0.613896 | 0.212376 | 0.670974 | 0.028384 |
| team_elo+none | international=0 | 16415 | 0.630449 | 0.220649 | 0.637557 | 0.036578 |

team_elo+none − coin (paired log loss):

| Section | Rows | team_elo+none log loss | coin log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 16918 | 0.629957 | 0.693147 | -0.063190 | [-0.067917, -0.058265] | yes |
| tier1 | 897 | 0.648564 | 0.693147 | -0.044583 | [-0.071885, -0.015822] | yes |
| tier2 | 4498 | 0.638324 | 0.693147 | -0.054823 | [-0.065863, -0.043994] | yes |
| tier3 | 11240 | 0.626909 | 0.693147 | -0.066238 | [-0.071731, -0.060569] | yes |
| unknown | 283 | 0.559052 | 0.693147 | -0.134096 | [-0.173073, -0.095930] | yes |
| international=1 | 503 | 0.613896 | 0.693147 | -0.079251 | [-0.114812, -0.043166] | yes |
| international=0 | 16415 | 0.630449 | 0.693147 | -0.062698 | [-0.067843, -0.057582] | yes |

| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |
|---|---|---:|---:|---:|---:|---:|
| player_round_glicko+none | all | 16918 | 0.595439 | 0.205158 | 0.677799 | 0.025511 |
| player_round_glicko+none | tier1 | 897 | 0.641270 | 0.224875 | 0.630992 | 0.027225 |
| player_round_glicko+none | tier2 | 4498 | 0.599020 | 0.207171 | 0.671521 | 0.023210 |
| player_round_glicko+none | tier3 | 11240 | 0.591753 | 0.203280 | 0.683274 | 0.027538 |
| player_round_glicko+none | unknown | 283 | 0.539658 | 0.185262 | 0.708481 | 0.080770 |
| player_round_glicko+none | international=1 | 503 | 0.617316 | 0.214670 | 0.660040 | 0.037389 |
| player_round_glicko+none | international=0 | 16415 | 0.594769 | 0.204866 | 0.678343 | 0.026294 |

player_round_glicko+none − coin (paired log loss):

| Section | Rows | player_round_glicko+none log loss | coin log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 16918 | 0.595439 | 0.693147 | -0.097708 | [-0.103728, -0.091565] | yes |
| tier1 | 897 | 0.641270 | 0.693147 | -0.051877 | [-0.071628, -0.029298] | yes |
| tier2 | 4498 | 0.599020 | 0.693147 | -0.094127 | [-0.105019, -0.083510] | yes |
| tier3 | 11240 | 0.591753 | 0.693147 | -0.101394 | [-0.108759, -0.093815] | yes |
| unknown | 283 | 0.539658 | 0.693147 | -0.153490 | [-0.193225, -0.111088] | yes |
| international=1 | 503 | 0.617316 | 0.693147 | -0.075831 | [-0.104084, -0.047276] | yes |
| international=0 | 16415 | 0.594769 | 0.693147 | -0.098378 | [-0.104565, -0.091977] | yes |

| Model | Section | Rows | Log loss | Brier | Accuracy | ECE |
|---|---|---:|---:|---:|---:|---:|
| player_round_glicko_rookie_weights+none | all | 16918 | 0.581653 | 0.198965 | 0.691926 | 0.022578 |
| player_round_glicko_rookie_weights+none | tier1 | 897 | 0.638121 | 0.223483 | 0.637681 | 0.028362 |
| player_round_glicko_rookie_weights+none | tier2 | 4498 | 0.598446 | 0.206018 | 0.679080 | 0.026958 |
| player_round_glicko_rookie_weights+none | tier3 | 11240 | 0.571799 | 0.194642 | 0.701068 | 0.021834 |
| player_round_glicko_rookie_weights+none | unknown | 283 | 0.527109 | 0.180835 | 0.704947 | 0.082998 |
| player_round_glicko_rookie_weights+none | international=1 | 503 | 0.615878 | 0.213964 | 0.660040 | 0.037654 |
| player_round_glicko_rookie_weights+none | international=0 | 16415 | 0.580604 | 0.198505 | 0.692903 | 0.022915 |

player_round_glicko_rookie_weights+none − coin (paired log loss):

| Section | Rows | player_round_glicko_rookie_weights+none log loss | coin log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 16918 | 0.581653 | 0.693147 | -0.111494 | [-0.118067, -0.105028] | yes |
| tier1 | 897 | 0.638121 | 0.693147 | -0.055027 | [-0.076196, -0.031192] | yes |
| tier2 | 4498 | 0.598446 | 0.693147 | -0.094701 | [-0.106526, -0.082848] | yes |
| tier3 | 11240 | 0.571799 | 0.693147 | -0.121348 | [-0.129111, -0.113138] | yes |
| unknown | 283 | 0.527109 | 0.693147 | -0.166038 | [-0.207432, -0.123091] | yes |
| international=1 | 503 | 0.615878 | 0.693147 | -0.077270 | [-0.106563, -0.046462] | yes |
| international=0 | 16415 | 0.580604 | 0.693147 | -0.112543 | [-0.119148, -0.105576] | yes |

player_round_glicko − team_elo (paired log loss):

| Section | Rows | player_round_glicko log loss | team_elo log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 16918 | 0.595439 | 0.629957 | -0.034518 | [-0.039173, -0.029965] | yes |

player_round_glicko_rookie_weights − team_elo (paired log loss):

| Section | Rows | player_round_glicko_rookie_weights log loss | team_elo log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 16918 | 0.581653 | 0.629957 | -0.048304 | [-0.053445, -0.043382] | yes |

team_elo+none − team_elo (paired log loss):

| Section | Rows | team_elo+none log loss | team_elo log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 16918 | 0.629957 | 0.629957 | 0.000000 | [0.000000, 0.000000] | no |

player_round_glicko+none − team_elo (paired log loss):

| Section | Rows | player_round_glicko+none log loss | team_elo log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 16918 | 0.595439 | 0.629957 | -0.034518 | [-0.039173, -0.029965] | yes |

player_round_glicko_rookie_weights+none − team_elo (paired log loss):

| Section | Rows | player_round_glicko_rookie_weights+none log loss | team_elo log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 16918 | 0.581653 | 0.629957 | -0.048304 | [-0.053445, -0.043382] | yes |

player_round_glicko − player_round_glicko_rookie_weights (paired log loss):

| Section | Rows | player_round_glicko log loss | player_round_glicko_rookie_weights log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 16918 | 0.595439 | 0.581653 | 0.013786 | [0.010789, 0.016835] | yes |
| tier1 | 897 | 0.641270 | 0.638121 | 0.003149 | [-0.000815, 0.006990] | no |
| tier2 | 4498 | 0.599020 | 0.598446 | 0.000574 | [-0.004210, 0.004681] | no |
| tier3 | 11240 | 0.591753 | 0.571799 | 0.019954 | [0.015814, 0.024056] | yes |
| unknown | 283 | 0.539658 | 0.527109 | 0.012548 | [0.000260, 0.024406] | yes |
| international=1 | 503 | 0.617316 | 0.615878 | 0.001439 | [-0.004047, 0.006648] | no |
| international=0 | 16415 | 0.594769 | 0.580604 | 0.014165 | [0.011239, 0.017277] | yes |

team_elo+none − player_round_glicko_rookie_weights (paired log loss):

| Section | Rows | team_elo+none log loss | player_round_glicko_rookie_weights log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 16918 | 0.629957 | 0.581653 | 0.048304 | [0.043382, 0.053445] | yes |
| tier1 | 897 | 0.648564 | 0.638121 | 0.010443 | [-0.007303, 0.029103] | no |
| tier2 | 4498 | 0.638324 | 0.598446 | 0.039878 | [0.031098, 0.049145] | yes |
| tier3 | 11240 | 0.626909 | 0.571799 | 0.055109 | [0.048394, 0.061515] | yes |
| unknown | 283 | 0.559052 | 0.527109 | 0.031942 | [0.004316, 0.059723] | yes |
| international=1 | 503 | 0.613896 | 0.615878 | -0.001981 | [-0.023544, 0.018341] | no |
| international=0 | 16415 | 0.630449 | 0.580604 | 0.049845 | [0.044739, 0.055204] | yes |

player_round_glicko+none − player_round_glicko_rookie_weights (paired log loss):

| Section | Rows | player_round_glicko+none log loss | player_round_glicko_rookie_weights log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 16918 | 0.595439 | 0.581653 | 0.013786 | [0.010789, 0.016835] | yes |
| tier1 | 897 | 0.641270 | 0.638121 | 0.003149 | [-0.000815, 0.006990] | no |
| tier2 | 4498 | 0.599020 | 0.598446 | 0.000574 | [-0.004210, 0.004681] | no |
| tier3 | 11240 | 0.591753 | 0.571799 | 0.019954 | [0.015814, 0.024056] | yes |
| unknown | 283 | 0.539658 | 0.527109 | 0.012548 | [0.000260, 0.024406] | yes |
| international=1 | 503 | 0.617316 | 0.615878 | 0.001439 | [-0.004047, 0.006648] | no |
| international=0 | 16415 | 0.594769 | 0.580604 | 0.014165 | [0.011239, 0.017277] | yes |

player_round_glicko_rookie_weights+none − player_round_glicko_rookie_weights (paired log loss):

| Section | Rows | player_round_glicko_rookie_weights+none log loss | player_round_glicko_rookie_weights log loss | Difference | 95% interval | Significant |
|---|---:|---:|---:|---:|---|---|
| all | 16918 | 0.581653 | 0.581653 | 0.000000 | [0.000000, 0.000000] | no |
| tier1 | 897 | 0.638121 | 0.638121 | 0.000000 | [0.000000, 0.000000] | no |
| tier2 | 4498 | 0.598446 | 0.598446 | 0.000000 | [0.000000, 0.000000] | no |
| tier3 | 11240 | 0.571799 | 0.571799 | 0.000000 | [0.000000, 0.000000] | no |
| unknown | 283 | 0.527109 | 0.527109 | 0.000000 | [0.000000, 0.000000] | no |
| international=1 | 503 | 0.615878 | 0.615878 | 0.000000 | [0.000000, 0.000000] | no |
| international=0 | 16415 | 0.580604 | 0.580604 | 0.000000 | [0.000000, 0.000000] | no |

## Stage 2 — validation vs Kalshi

### team_elo: Kalshi comparison and returns



#### Log loss vs Kalshi

| Kind | Slice | Rows | Model log loss | Kalshi log loss | Difference [95% interval] | Significant |
|---|---|---:|---:|---:|---|---|
| series | all | 4136 | 0.625869 | 0.600829 | 0.025040 [0.016663, 0.033211] | yes |
| series | tier1 | 685 | 0.638551 | 0.614585 | 0.023966 [0.002515, 0.045256] | yes |
| series | tier2 | 1814 | 0.628641 | 0.590902 | 0.037739 [0.025494, 0.049681] | yes |
| series | tier3 | 1595 | 0.619847 | 0.609630 | 0.010217 [-0.003083, 0.024344] | no |
| series | unknown | 42 | 0.527980 | 0.471027 | 0.056952 [-0.017412, 0.134365] | no |
| series | international=1 | 436 | 0.605667 | 0.592747 | 0.012920 [-0.009540, 0.036134] | no |
| series | international=0 | 3700 | 0.628250 | 0.601782 | 0.026468 [0.017066, 0.035174] | yes |
| map | all | 4087 | 0.660902 | 0.637334 | 0.023569 [0.015578, 0.031565] | yes |
| map | tier1 | 1117 | 0.666997 | 0.643855 | 0.023142 [0.007811, 0.039094] | yes |
| map | tier2 | 1772 | 0.663547 | 0.636583 | 0.026964 [0.015160, 0.038158] | yes |
| map | tier3 | 1144 | 0.653841 | 0.635738 | 0.018103 [0.004317, 0.033179] | yes |
| map | unknown | 54 | 0.597663 | 0.560856 | 0.036807 [-0.011319, 0.082276] | no |
| map | international=1 | 765 | 0.632264 | 0.630727 | 0.001537 [-0.015772, 0.017961] | no |
| map | international=0 | 3322 | 0.667497 | 0.638855 | 0.028643 [0.019864, 0.037566] | yes |

#### Full-Kelly returns

| Kind | Slice | Bets | Matches | Mean edge | Flat ROI [95% interval] | Kelly, LoL caps ($50 start) | Multiple | Max drawdown | Largest stake | Bets filled | Flat ROI depth-capped [95% interval] | Kelly depth-capped final |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---:|
| series | all | 3075 | 3070 | 0.0881 | -7.18% [-11.56%, -2.45%] | $0.09 | 0.002× | 99.92% | $10.63 | 1948 (1127 unfilled) | -5.72% [-11.33%, -0.25%] | $0.08 |
| series | tier1 | 505 | 505 | 0.0795 | -7.55% [-18.06%, 3.52%] | $0.06 | 0.001× | 99.96% | $16.89 | 413 (92 unfilled) | -5.76% [-17.14%, 6.03%] | $2.79 |
| series | tier2 | 1328 | 1325 | 0.0860 | -12.52% [-18.65%, -5.94%] | $0.07 | 0.001× | 99.86% | $4.97 | 823 (505 unfilled) | -12.97% [-20.79%, -4.58%] | $0.05 |
| series | tier3 | 1211 | 1209 | 0.0937 | -0.51% [-8.40%, 7.66%] | $0.08 | 0.002× | 99.92% | $9.03 | 692 (519 unfilled) | 3.58% [-6.28%, 13.49%] | $8.44 |
| series | unknown | 31 | 31 | 0.0987 | -33.30% [-59.30%, -4.68%] | $21.71 | 0.434× | 60.39% | $5.24 | 20 (11 unfilled) | -28.95% [-65.86%, 12.03%] | $29.07 |
| series | international=1 | 320 | 320 | 0.0730 | -6.60% [-20.95%, 8.37%] | $6.14 | 0.123× | 97.73% | $8.64 | 277 (43 unfilled) | -6.55% [-20.89%, 7.75%] | $8.56 |
| series | international=0 | 2755 | 2750 | 0.0898 | -7.25% [-12.13%, -2.46%] | $0.06 | 0.001× | 99.93% | $8.21 | 1671 (1084 unfilled) | -5.58% [-11.45%, 0.48%] | $0.09 |
| map | all | 2828 | 1758 | 0.0737 | -6.37% [-10.72%, -1.90%] | $0.08 | 0.002× | 99.94% | $13.69 | 849 (1979 unfilled) | -12.61% [-19.37%, -5.54%] | $0.10 |
| map | tier1 | 759 | 492 | 0.0784 | -2.39% [-10.87%, 6.12%] | $6.35 | 0.127× | 96.26% | $5.79 | 248 (511 unfilled) | -3.48% [-16.97%, 10.39%] | $24.77 |
| map | tier2 | 1216 | 748 | 0.0710 | -6.50% [-12.59%, 0.14%] | $0.09 | 0.002× | 99.89% | $7.11 | 361 (855 unfilled) | -15.56% [-25.70%, -4.62%] | $0.12 |
| map | tier3 | 817 | 496 | 0.0730 | -8.83% [-16.74%, -0.92%] | $0.98 | 0.020× | 99.64% | $19.63 | 227 (590 unfilled) | -16.23% [-29.62%, -1.92%] | $5.74 |
| map | unknown | 36 | 22 | 0.0810 | -29.73% [-55.86%, -6.41%] | $26.30 | 0.526× | 47.51% | $4.78 | 13 (23 unfilled) | -41.29% [-77.65%, -5.83%] | $36.82 |
| map | international=1 | 515 | 341 | 0.0733 | 4.03% [-6.64%, 14.79%] | $63.87 | 1.277× | 83.55% | $7.82 | 178 (337 unfilled) | 7.72% [-9.53%, 26.14%] | $87.59 |
| map | international=0 | 2313 | 1417 | 0.0738 | -8.68% [-13.44%, -3.77%] | $0.08 | 0.002× | 99.92% | $9.16 | 671 (1642 unfilled) | -17.99% [-25.44%, -10.49%] | $0.08 |
| series+map | all | 5903 | 3443 | 0.0812 | -6.79% [-10.16%, -3.20%] | $0.03 | 0.001× | 99.95% | $6.13 | 2797 (3106 unfilled) | -7.81% [-12.29%, -2.69%] | $0.08 |

#### Monthly market blend fits

UTC monthly fits use earlier rows of the same kind from 2026-01-01, excluding holdout; minimum 100 rows. logit(p_blend) = a·logit(mid) + b·(logit(p_model) − logit(mid)); inputs clipped to [0.01, 0.99], no intercept, ridge 1e-6. Unfitted rows use mid unchanged; excluded from blended tables: 346 rows. Rating parameters remain selected on the tuning window.

| Month | Kind | n | a | b | Status |
|---|---|---:|---:|---:|---|
| 2026-01 | series | 0 | 1.000000 | 0.000000 | unfitted |
| 2026-01 | map | 0 | 1.000000 | 0.000000 | unfitted |
| 2026-02 | series | 49 | 1.000000 | 0.000000 | unfitted |
| 2026-02 | map | 61 | 1.000000 | 0.000000 | unfitted |
| 2026-03 | series | 193 | 1.348589 | 0.508136 | fitted |
| 2026-03 | map | 153 | 1.179920 | -0.170761 | fitted |
| 2026-04 | series | 479 | 1.312188 | 0.424545 | fitted |
| 2026-04 | map | 285 | 1.090028 | 0.051788 | fitted |
| 2026-05 | series | 781 | 1.293180 | 0.464303 | fitted |
| 2026-05 | map | 532 | 1.007501 | 0.344396 | fitted |
| 2026-06 | series | 1106 | 1.238193 | 0.299775 | fitted |
| 2026-06 | map | 934 | 1.060575 | 0.301034 | fitted |
| 2026-07 | series | 1426 | 1.186169 | 0.287089 | fitted |
| 2026-07 | map | 1308 | 1.081621 | 0.341783 | fitted |
| 2026-08 | series | 1907 | 1.133808 | 0.151473 | fitted |
| 2026-08 | map | 1889 | 1.057818 | 0.094635 | fitted |
| 2026-09 | series | 2565 | 1.143395 | 0.237220 | fitted |
| 2026-09 | map | 2690 | 1.108272 | 0.142689 | fitted |
| 2026-10 | series | 3417 | 1.139790 | 0.213454 | fitted |
| 2026-10 | map | 3497 | 1.085817 | 0.089923 | fitted |

#### Log loss vs Kalshi (blended)

| Kind | Slice | Rows | Model log loss | Kalshi log loss | Difference [95% interval] | Significant |
|---|---|---:|---:|---:|---|---|
| series | all | 3943 | 0.600957 | 0.602190 | -0.001233 [-0.003882, 0.001585] | no |
| series | tier1 | 578 | 0.620485 | 0.615317 | 0.005168 [-0.003632, 0.013699] | no |
| series | tier2 | 1733 | 0.593473 | 0.593744 | -0.000271 [-0.004645, 0.004148] | no |
| series | tier3 | 1590 | 0.605852 | 0.610089 | -0.004237 [-0.007563, -0.001017] | yes |
| series | unknown | 42 | 0.455744 | 0.471027 | -0.015283 [-0.042914, 0.014339] | no |
| series | international=1 | 359 | 0.593817 | 0.591638 | 0.002179 [-0.007434, 0.013089] | no |
| series | international=0 | 3584 | 0.601673 | 0.603247 | -0.001575 [-0.004291, 0.001103] | no |
| map | all | 3934 | 0.639191 | 0.638132 | 0.001058 [-0.000748, 0.002904] | no |
| map | tier1 | 990 | 0.651869 | 0.647070 | 0.004799 [0.000798, 0.009333] | yes |
| map | tier2 | 1748 | 0.636768 | 0.636671 | 0.000097 [-0.002509, 0.002648] | no |
| map | tier3 | 1142 | 0.635937 | 0.636276 | -0.000339 [-0.003213, 0.002582] | no |
| map | unknown | 54 | 0.553988 | 0.560856 | -0.006869 [-0.017275, 0.002474] | no |
| map | international=1 | 665 | 0.630345 | 0.630639 | -0.000294 [-0.004947, 0.004237] | no |
| map | international=0 | 3269 | 0.640990 | 0.639657 | 0.001333 [-0.000631, 0.003255] | no |

#### Full-Kelly returns (blended)

| Kind | Slice | Bets | Matches | Mean edge | Flat ROI [95% interval] | Kelly, LoL caps ($50 start) | Multiple | Max drawdown | Largest stake | Bets filled | Flat ROI depth-capped [95% interval] | Kelly depth-capped final |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---:|
| series | all | 1202 | 1201 | 0.0226 | 0.96% [-4.21%, 6.29%] | $14.00 | 0.280× | 96.04% | $22.88 | 826 (376 unfilled) | 2.53% [-3.61%, 9.09%] | $25.07 |
| series | tier1 | 212 | 212 | 0.0298 | -2.00% [-12.59%, 9.94%] | $15.01 | 0.300× | 82.53% | $8.31 | 173 (39 unfilled) | -2.18% [-12.85%, 8.58%] | $23.74 |
| series | tier2 | 602 | 601 | 0.0246 | -2.82% [-9.65%, 3.61%] | $14.34 | 0.287× | 87.69% | $10.15 | 413 (189 unfilled) | -0.62% [-9.32%, 7.73%] | $20.73 |
| series | tier3 | 366 | 366 | 0.0146 | 9.21% [-1.04%, 20.26%] | $157.79 | 3.156× | 35.65% | $16.15 | 222 (144 unfilled) | 13.15% [-0.18%, 29.21%] | $103.60 |
| series | unknown | 22 | 22 | 0.0314 | -4.12% [-33.84%, 26.84%] | $58.95 | 1.179× | 25.97% | $6.78 | 18 (4 unfilled) | -10.74% [-47.66%, 26.85%] | $52.85 |
| series | international=1 | 129 | 129 | 0.0282 | 2.58% [-12.27%, 18.31%] | $26.29 | 0.526× | 66.27% | $7.69 | 111 (18 unfilled) | -2.17% [-15.03%, 10.40%] | $27.18 |
| series | international=0 | 1073 | 1072 | 0.0219 | 0.77% [-4.39%, 6.28%] | $31.35 | 0.627× | 90.72% | $17.29 | 715 (358 unfilled) | 3.26% [-3.76%, 10.50%] | $45.21 |
| map | all | 421 | 264 | 0.0213 | -2.22% [-11.72%, 8.66%] | $31.69 | 0.634× | 79.09% | $9.43 | 119 (302 unfilled) | -10.09% [-23.86%, 4.51%] | $34.17 |
| map | tier1 | 135 | 84 | 0.0314 | -16.84% [-29.74%, -3.73%] | $20.13 | 0.403× | 61.41% | $4.05 | 45 (90 unfilled) | -11.34% [-35.18%, 13.46%] | $42.72 |
| map | tier2 | 189 | 121 | 0.0192 | -0.97% [-17.99%, 20.95%] | $58.41 | 1.168× | 50.28% | $8.28 | 52 (137 unfilled) | -8.92% [-29.48%, 11.47%] | $42.65 |
| map | tier3 | 89 | 53 | 0.0114 | 16.85% [-3.39%, 36.46%] | $68.84 | 1.377× | 24.98% | $4.52 | 18 (71 unfilled) | -13.17% [-53.08%, 29.42%] | $46.84 |
| map | unknown | 8 | 6 | 0.0079 | 2.44% [-38.16%, 36.12%] | $50.16 | 1.003× | 4.66% | $2.89 | 4 (4 unfilled) | 2.54% [-20.42%, 38.70%] | $49.86 |
| map | international=1 | 80 | 50 | 0.0250 | -3.76% [-21.19%, 14.00%] | $45.30 | 0.906× | 27.57% | $4.05 | 36 (44 unfilled) | -6.73% [-36.79%, 22.49%] | $46.85 |
| map | international=0 | 341 | 214 | 0.0204 | -1.85% [-13.37%, 11.77%] | $35.19 | 0.704× | 78.69% | $10.57 | 83 (258 unfilled) | -11.55% [-27.15%, 4.94%] | $36.29 |
| series+map | all | 1623 | 1244 | 0.0222 | 0.14% [-4.95%, 5.27%] | $29.89 | 0.598× | 90.12% | $19.36 | 945 (678 unfilled) | 0.94% [-5.13%, 6.90%] | $23.34 |

#### Monthly breakdown

All metrics use identical linked rows within each kind/month. Unfitted blend months show —; counts include all rows.

| Kind | Month | Rows | Model log loss | Blended log loss | Kalshi log loss | Raw flat ROI (bets), unlimited Kelly final | Blended flat ROI (bets), unlimited Kelly final | Raw bets filled | Raw Flat ROI depth-capped [95% interval] | Raw Kelly depth-capped final | Blended bets filled | Blended Flat ROI depth-capped [95% interval] | Blended Kelly depth-capped final |
|---|---|---:|---:|---:|---:|---|---|---:|---|---:|---:|---|---:|
| map | 2026-01 | 61 | 0.664952 | — | 0.634669 | -13.30% (42), $38.57 | — | 6 (36 unfilled) | -29.17% [-80.10%, 27.15%] | $47.79 | — | — | — |
| map | 2026-02 | 92 | 0.648097 | — | 0.604939 | -17.60% (61), $22.63 | — | 26 (35 unfilled) | -46.72% [-77.78%, -11.60%] | $22.57 | — | — | — |
| map | 2026-03 | 132 | 0.658811 | 0.655569 | 0.650213 | 0.68% (83), $48.04 | -15.83% (22), $40.62 | 48 (35 unfilled) | 12.14% [-20.29%, 44.39%] | $60.68 | 9 (13 unfilled) | -53.91% [-87.12%, -12.78%] | $38.49 |
| map | 2026-04 | 247 | 0.652344 | 0.654163 | 0.654704 | 17.39% (168), $204.76 | 27.08% (2), $50.41 | 64 (104 unfilled) | -11.64% [-31.49%, 7.43%] | $26.64 | 1 (1 unfilled) | 38.70% [38.70%, 38.70%] | $50.28 |
| map | 2026-05 | 402 | 0.657429 | 0.638964 | 0.640045 | -0.76% (282), $14.02 | 5.41% (100), $98.29 | 95 (187 unfilled) | -1.44% [-21.75%, 16.71%] | $35.78 | 38 (62 unfilled) | -1.55% [-30.37%, 27.90%] | $53.53 |
| map | 2026-06 | 374 | 0.652839 | 0.646735 | 0.651611 | -0.43% (246), $50.91 | 22.39% (78), $68.71 | 49 (197 unfilled) | 8.07% [-17.90%, 33.46%] | $53.58 | 13 (65 unfilled) | 4.91% [-40.68%, 40.54%] | $49.96 |
| map | 2026-07 | 581 | 0.697745 | 0.653245 | 0.640757 | -22.22% (387), $0.10 | -17.51% (144), $17.35 | 87 (300 unfilled) | -27.32% [-46.00%, -8.00%] | $20.62 | 30 (114 unfilled) | -19.03% [-44.84%, 6.60%] | $40.08 |
| map | 2026-08 | 801 | 0.639868 | 0.623796 | 0.625646 | -3.41% (585), $10.94 | 27.62% (8), $52.49 | 110 (475 unfilled) | -2.91% [-21.76%, 17.30%] | $29.04 | 1 (7 unfilled) | 27.32% [27.32%, 27.32%] | $50.65 |
| map | 2026-09 | 807 | 0.677381 | 0.644128 | 0.642565 | -12.26% (588), $0.09 | -11.64% (58), $38.55 | 210 (378 unfilled) | -20.23% [-35.94%, -3.39%] | $2.05 | 22 (36 unfilled) | -11.43% [-40.22%, 18.62%] | $49.53 |
| map | 2026-10 | 590 | 0.643747 | 0.624937 | 0.626949 | -3.15% (386), $5.73 | 4.31% (9), $50.65 | 154 (232 unfilled) | -15.95% [-30.68%, -0.75%] | $4.19 | 5 (4 unfilled) | 6.70% [-64.57%, 36.59%] | $51.30 |
| series | 2026-01 | 49 | 0.539697 | — | 0.590419 | 27.27% (39), $93.52 | — | 31 (8 unfilled) | 49.42% [7.30%, 93.72%] | $102.27 | — | — | — |
| series | 2026-02 | 144 | 0.599158 | — | 0.567099 | -23.04% (101), $5.65 | — | 90 (11 unfilled) | -19.54% [-39.83%, 1.61%] | $10.05 | — | — | — |
| series | 2026-03 | 286 | 0.613771 | 0.585162 | 0.589357 | -10.34% (197), $2.36 | 2.41% (166), $85.35 | 151 (46 unfilled) | -3.64% [-20.67%, 14.97%] | $10.73 | 126 (40 unfilled) | 4.09% [-8.94%, 17.66%] | $87.55 |
| series | 2026-04 | 302 | 0.590224 | 0.569711 | 0.578002 | -1.52% (221), $17.33 | 7.20% (176), $59.82 | 167 (54 unfilled) | -4.01% [-23.96%, 17.29%] | $16.13 | 134 (42 unfilled) | 5.69% [-10.75%, 24.27%] | $33.91 |
| series | 2026-05 | 325 | 0.638646 | 0.602696 | 0.595148 | -13.89% (236), $0.67 | -7.35% (172), $20.31 | 189 (47 unfilled) | -17.07% [-32.40%, -0.85%] | $1.03 | 141 (31 unfilled) | -7.28% [-20.57%, 5.62%] | $22.65 |
| series | 2026-06 | 320 | 0.650460 | 0.635371 | 0.634132 | -3.00% (235), $6.05 | -3.44% (124), $30.20 | 153 (82 unfilled) | 13.41% [-6.77%, 34.64%] | $243.28 | 80 (44 unfilled) | -1.23% [-18.30%, 15.28%] | $44.33 |
| series | 2026-07 | 481 | 0.669358 | 0.622372 | 0.616051 | -16.34% (369), $0.05 | -3.84% (162), $21.38 | 229 (140 unfilled) | -16.72% [-33.99%, 1.90%] | $1.85 | 104 (58 unfilled) | -0.91% [-25.57%, 31.92%] | $35.25 |
| series | 2026-08 | 658 | 0.626846 | 0.612026 | 0.615564 | -2.51% (510), $0.09 | 12.97% (91), $64.73 | 259 (251 unfilled) | -3.67% [-19.68%, 14.16%] | $23.97 | 48 (43 unfilled) | 21.49% [3.92%, 38.29%] | $62.55 |
| series | 2026-09 | 852 | 0.637185 | 0.601055 | 0.601766 | -6.27% (649), $0.02 | -4.57% (182), $39.96 | 358 (291 unfilled) | -5.94% [-17.97%, 6.84%] | $0.00 | 107 (75 unfilled) | 5.93% [-9.53%, 21.58%] | $56.12 |
| series | 2026-10 | 719 | 0.596758 | 0.579691 | 0.585415 | -5.94% (518), $0.04 | 11.38% (129), $73.87 | 321 (197 unfilled) | -5.03% [-18.43%, 8.31%] | $0.45 | 86 (43 unfilled) | 4.36% [-10.81%, 19.06%] | $56.51 |

### player_round_glicko: Kalshi comparison and returns



#### Log loss vs Kalshi

| Kind | Slice | Rows | Model log loss | Kalshi log loss | Difference [95% interval] | Significant |
|---|---|---:|---:|---:|---|---|
| series | all | 4136 | 0.601179 | 0.600829 | 0.000349 [-0.007997, 0.008261] | no |
| series | tier1 | 685 | 0.630196 | 0.614585 | 0.015611 [-0.003294, 0.034073] | no |
| series | tier2 | 1814 | 0.597676 | 0.590902 | 0.006774 [-0.002949, 0.017019] | no |
| series | tier3 | 1595 | 0.595539 | 0.609630 | -0.014091 [-0.028841, 0.002195] | no |
| series | unknown | 42 | 0.493388 | 0.471027 | 0.022360 [-0.039419, 0.084664] | no |
| series | international=1 | 436 | 0.610540 | 0.592747 | 0.017793 [-0.006566, 0.041850] | no |
| series | international=0 | 3700 | 0.600076 | 0.601782 | -0.001706 [-0.010486, 0.006661] | no |
| map | all | 4087 | 0.642445 | 0.637334 | 0.005111 [-0.000899, 0.011256] | no |
| map | tier1 | 1117 | 0.655010 | 0.643855 | 0.011155 [-0.001530, 0.022670] | no |
| map | tier2 | 1772 | 0.640047 | 0.636583 | 0.003464 [-0.005262, 0.012028] | no |
| map | tier3 | 1144 | 0.636592 | 0.635738 | 0.000854 [-0.012655, 0.014382] | no |
| map | unknown | 54 | 0.585190 | 0.560856 | 0.024334 [-0.011891, 0.063343] | no |
| map | international=1 | 765 | 0.636151 | 0.630727 | 0.005424 [-0.009241, 0.019854] | no |
| map | international=0 | 3322 | 0.643894 | 0.638855 | 0.005039 [-0.002008, 0.012043] | no |

#### Full-Kelly returns

| Kind | Slice | Bets | Matches | Mean edge | Flat ROI [95% interval] | Kelly, LoL caps ($50 start) | Multiple | Max drawdown | Largest stake | Bets filled | Flat ROI depth-capped [95% interval] | Kelly depth-capped final |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---:|
| series | all | 3082 | 3077 | 0.0821 | 1.97% [-2.62%, 6.76%] | $0.03 | 0.001× | 99.97% | $8.38 | 1949 (1133 unfilled) | 0.94% [-4.59%, 6.68%] | $0.06 |
| series | tier1 | 508 | 508 | 0.0792 | 1.75% [-9.27%, 14.15%] | $0.10 | 0.002× | 99.91% | $10.97 | 419 (89 unfilled) | -1.60% [-14.49%, 11.12%] | $0.46 |
| series | tier2 | 1282 | 1279 | 0.0720 | -3.74% [-10.56%, 3.46%] | $0.04 | 0.001× | 99.93% | $5.64 | 794 (488 unfilled) | -4.05% [-11.82%, 3.89%] | $0.09 |
| series | tier3 | 1259 | 1257 | 0.0937 | 8.40% [1.33%, 15.77%] | $5425.88 | 108.518× | 94.06% | $249.12 | 713 (546 unfilled) | 8.41% [-0.92%, 17.93%] | $178.06 |
| series | unknown | 33 | 33 | 0.0790 | -18.09% [-49.38%, 16.00%] | $31.15 | 0.623× | 41.12% | $5.10 | 23 (10 unfilled) | -11.86% [-49.11%, 31.13%] | $36.49 |
| series | international=1 | 326 | 326 | 0.0804 | 0.39% [-15.53%, 16.71%] | $1.13 | 0.023× | 99.34% | $11.29 | 284 (42 unfilled) | -5.34% [-20.51%, 10.66%] | $1.06 |
| series | international=0 | 2756 | 2751 | 0.0823 | 2.16% [-2.78%, 6.98%] | $0.10 | 0.002× | 99.85% | $6.24 | 1665 (1091 unfilled) | 2.02% [-3.77%, 7.95%] | $21.42 |
| map | all | 2622 | 1664 | 0.0595 | -4.62% [-8.97%, 0.05%] | $0.09 | 0.002× | 99.99% | $83.31 | 759 (1863 unfilled) | -14.96% [-22.27%, -7.00%] | $0.08 |
| map | tier1 | 716 | 487 | 0.0610 | -3.55% [-12.41%, 6.16%] | $5.98 | 0.120× | 94.92% | $10.80 | 228 (488 unfilled) | -4.04% [-20.60%, 13.22%] | $10.78 |
| map | tier2 | 1094 | 678 | 0.0529 | -3.99% [-11.02%, 3.21%] | $0.34 | 0.007× | 99.89% | $31.32 | 305 (789 unfilled) | -18.86% [-29.52%, -7.34%] | $0.39 |
| map | tier3 | 781 | 479 | 0.0678 | -6.03% [-14.27%, 2.30%] | $9.12 | 0.182× | 97.53% | $17.95 | 214 (567 unfilled) | -21.13% [-35.22%, -5.85%] | $6.09 |
| map | unknown | 31 | 20 | 0.0509 | -15.75% [-45.13%, 13.25%] | $36.99 | 0.740× | 30.22% | $4.78 | 12 (19 unfilled) | -13.86% [-51.82%, 16.78%] | $45.92 |
| map | international=1 | 489 | 337 | 0.0636 | -0.68% [-13.06%, 12.05%] | $23.60 | 0.472× | 89.46% | $21.98 | 166 (323 unfilled) | -0.54% [-20.49%, 21.50%] | $28.58 |
| map | international=0 | 2133 | 1327 | 0.0586 | -5.52% [-10.43%, -0.41%] | $0.08 | 0.002× | 99.97% | $23.44 | 593 (1540 unfilled) | -19.01% [-27.07%, -10.23%] | $0.09 |
| series+map | all | 5704 | 3363 | 0.0717 | -1.06% [-4.84%, 2.82%] | $0.08 | 0.002× | 99.90% | $6.26 | 2708 (2996 unfilled) | -3.51% [-8.43%, 1.56%] | $0.09 |

#### Monthly market blend fits

UTC monthly fits use earlier rows of the same kind from 2026-01-01, excluding holdout; minimum 100 rows. logit(p_blend) = a·logit(mid) + b·(logit(p_model) − logit(mid)); inputs clipped to [0.01, 0.99], no intercept, ridge 1e-6. Unfitted rows use mid unchanged; excluded from blended tables: 346 rows. Rating parameters remain selected on the tuning window.

| Month | Kind | n | a | b | Status |
|---|---|---:|---:|---:|---|
| 2026-01 | series | 0 | 1.000000 | 0.000000 | unfitted |
| 2026-01 | map | 0 | 1.000000 | 0.000000 | unfitted |
| 2026-02 | series | 49 | 1.000000 | 0.000000 | unfitted |
| 2026-02 | map | 61 | 1.000000 | 0.000000 | unfitted |
| 2026-03 | series | 193 | 1.412870 | 0.637893 | fitted |
| 2026-03 | map | 153 | 1.405922 | 0.726584 | fitted |
| 2026-04 | series | 479 | 1.429697 | 0.815808 | fitted |
| 2026-04 | map | 285 | 1.241068 | 0.543244 | fitted |
| 2026-05 | series | 781 | 1.405614 | 0.816315 | fitted |
| 2026-05 | map | 532 | 1.342872 | 0.971764 | fitted |
| 2026-06 | series | 1106 | 1.359642 | 0.671898 | fitted |
| 2026-06 | map | 934 | 1.339574 | 0.816406 | fitted |
| 2026-07 | series | 1426 | 1.298197 | 0.674531 | fitted |
| 2026-07 | map | 1308 | 1.318270 | 0.810821 | fitted |
| 2026-08 | series | 1907 | 1.243317 | 0.576199 | fitted |
| 2026-08 | map | 1889 | 1.190096 | 0.579620 | fitted |
| 2026-09 | series | 2565 | 1.230493 | 0.601141 | fitted |
| 2026-09 | map | 2690 | 1.236901 | 0.632350 | fitted |
| 2026-10 | series | 3417 | 1.244692 | 0.632801 | fitted |
| 2026-10 | map | 3497 | 1.185235 | 0.506205 | fitted |

#### Log loss vs Kalshi (blended)

| Kind | Slice | Rows | Model log loss | Kalshi log loss | Difference [95% interval] | Significant |
|---|---|---:|---:|---:|---|---|
| series | all | 3943 | 0.590439 | 0.602190 | -0.011751 [-0.017008, -0.006562] | yes |
| series | tier1 | 578 | 0.617489 | 0.615317 | 0.002172 [-0.009711, 0.013949] | no |
| series | tier2 | 1733 | 0.584065 | 0.593744 | -0.009679 [-0.016565, -0.002362] | yes |
| series | tier3 | 1590 | 0.591311 | 0.610089 | -0.018778 [-0.028057, -0.008925] | yes |
| series | unknown | 42 | 0.448197 | 0.471027 | -0.022831 [-0.053549, 0.009211] | no |
| series | international=1 | 359 | 0.592419 | 0.591638 | 0.000781 [-0.012219, 0.013778] | no |
| series | international=0 | 3584 | 0.590241 | 0.603247 | -0.013006 [-0.018596, -0.007352] | yes |
| map | all | 3934 | 0.635441 | 0.638132 | -0.002692 [-0.006873, 0.001481] | no |
| map | tier1 | 990 | 0.651692 | 0.647070 | 0.004622 [-0.003077, 0.012335] | no |
| map | tier2 | 1748 | 0.631449 | 0.636671 | -0.005221 [-0.010949, 0.000158] | no |
| map | tier3 | 1142 | 0.631240 | 0.636276 | -0.005036 [-0.014252, 0.004324] | no |
| map | unknown | 54 | 0.555541 | 0.560856 | -0.005315 [-0.029567, 0.019085] | no |
| map | international=1 | 665 | 0.627729 | 0.630639 | -0.002911 [-0.011792, 0.006090] | no |
| map | international=0 | 3269 | 0.637009 | 0.639657 | -0.002647 [-0.007517, 0.002288] | no |

#### Full-Kelly returns (blended)

| Kind | Slice | Bets | Matches | Mean edge | Flat ROI [95% interval] | Kelly, LoL caps ($50 start) | Multiple | Max drawdown | Largest stake | Bets filled | Flat ROI depth-capped [95% interval] | Kelly depth-capped final |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---:|
| series | all | 2297 | 2293 | 0.0473 | 7.97% [3.69%, 12.17%] | $6738.98 | 134.780× | 82.79% | $249.12 | 1450 (847 unfilled) | 5.54% [0.22%, 11.31%] | $607.97 |
| series | tier1 | 301 | 301 | 0.0384 | -0.08% [-12.76%, 13.74%] | $17.60 | 0.352× | 86.27% | $9.03 | 237 (64 unfilled) | -3.00% [-16.29%, 11.83%] | $22.49 |
| series | tier2 | 983 | 982 | 0.0421 | 6.48% [0.88%, 12.15%] | $3940.09 | 78.802× | 50.44% | $248.95 | 610 (373 unfilled) | 2.98% [-4.23%, 10.18%] | $149.74 |
| series | tier3 | 985 | 982 | 0.0553 | 12.07% [5.51%, 19.44%] | $10161.64 | 203.233× | 58.27% | $249.12 | 583 (402 unfilled) | 11.96% [3.04%, 21.43%] | $825.25 |
| series | unknown | 28 | 28 | 0.0446 | 2.67% [-24.05%, 30.23%] | $65.96 | 1.319× | 9.26% | $6.34 | 20 (8 unfilled) | -2.09% [-37.35%, 35.01%] | $56.87 |
| series | international=1 | 185 | 185 | 0.0342 | 2.12% [-14.51%, 19.77%] | $76.25 | 1.525× | 51.79% | $11.06 | 154 (31 unfilled) | -0.61% [-18.26%, 18.15%] | $64.39 |
| series | international=0 | 2112 | 2108 | 0.0485 | 8.48% [4.43%, 13.00%] | $8758.73 | 175.175× | 82.45% | $249.12 | 1296 (816 unfilled) | 6.27% [0.59%, 12.08%] | $613.99 |
| map | all | 1806 | 1131 | 0.0384 | 2.87% [-2.34%, 8.24%] | $677.73 | 13.555× | 80.74% | $172.03 | 524 (1282 unfilled) | -6.72% [-15.08%, 2.37%] | $6.17 |
| map | tier1 | 387 | 253 | 0.0390 | 0.81% [-11.47%, 13.38%] | $44.81 | 0.896× | 83.93% | $17.48 | 132 (255 unfilled) | -0.87% [-20.67%, 21.21%] | $44.81 |
| map | tier2 | 786 | 489 | 0.0340 | 2.21% [-5.70%, 10.29%] | $214.07 | 4.281× | 53.33% | $39.13 | 215 (571 unfilled) | -11.06% [-22.36%, 0.03%] | $14.84 |
| map | tier3 | 609 | 372 | 0.0439 | 5.31% [-2.98%, 14.29%] | $125.48 | 2.510× | 77.35% | $25.30 | 166 (443 unfilled) | -6.19% [-21.56%, 10.10%] | $25.56 |
| map | unknown | 24 | 17 | 0.0339 | -4.31% [-30.87%, 21.42%] | $49.89 | 0.998× | 11.87% | $4.49 | 11 (13 unfilled) | -0.06% [-37.68%, 33.08%] | $51.47 |
| map | international=1 | 262 | 172 | 0.0384 | 7.10% [-8.40%, 24.09%] | $127.38 | 2.548× | 52.06% | $18.53 | 97 (165 unfilled) | 8.18% [-16.74%, 34.64%] | $72.48 |
| map | international=0 | 1544 | 959 | 0.0384 | 2.15% [-3.35%, 7.96%] | $219.82 | 4.396× | 83.29% | $80.68 | 427 (1117 unfilled) | -10.11% [-18.72%, -1.32%] | $3.70 |
| series+map | all | 4103 | 2453 | 0.0434 | 5.72% [2.02%, 9.49%] | $13461.29 | 269.226× | 46.20% | $249.47 | 1974 (2129 unfilled) | 2.28% [-2.61%, 7.49%] | $306.07 |

#### Monthly breakdown

All metrics use identical linked rows within each kind/month. Unfitted blend months show —; counts include all rows.

| Kind | Month | Rows | Model log loss | Blended log loss | Kalshi log loss | Raw flat ROI (bets), unlimited Kelly final | Blended flat ROI (bets), unlimited Kelly final | Raw bets filled | Raw Flat ROI depth-capped [95% interval] | Raw Kelly depth-capped final | Blended bets filled | Blended Flat ROI depth-capped [95% interval] | Blended Kelly depth-capped final |
|---|---|---:|---:|---:|---:|---|---|---:|---|---:|---:|---|---:|
| map | 2026-01 | 61 | 0.621963 | — | 0.634669 | 3.98% (41), $57.25 | — | 5 (36 unfilled) | 11.19% [-66.65%, 89.92%] | $50.93 | — | — | — |
| map | 2026-02 | 92 | 0.622449 | — | 0.604939 | -7.66% (52), $39.96 | — | 16 (36 unfilled) | -59.39% [-100.00%, -17.67%] | $28.02 | — | — | — |
| map | 2026-03 | 132 | 0.656938 | 0.652193 | 0.650213 | 1.48% (72), $47.17 | -7.78% (61), $34.67 | 37 (35 unfilled) | 3.54% [-37.77%, 45.24%] | $42.95 | 30 (31 unfilled) | -4.61% [-38.87%, 33.25%] | $33.74 |
| map | 2026-04 | 247 | 0.624389 | 0.629977 | 0.654704 | 26.29% (140), $318.34 | 51.23% (82), $535.00 | 48 (92 unfilled) | -3.68% [-33.66%, 26.48%] | $30.39 | 24 (58 unfilled) | 1.75% [-31.65%, 38.12%] | $53.72 |
| map | 2026-05 | 402 | 0.647009 | 0.637552 | 0.640045 | -3.19% (247), $47.29 | 3.00% (244), $90.14 | 83 (164 unfilled) | 0.71% [-24.98%, 25.28%] | $41.45 | 95 (149 unfilled) | 1.29% [-18.19%, 20.79%] | $51.08 |
| map | 2026-06 | 374 | 0.643495 | 0.640900 | 0.651611 | -2.31% (233), $60.96 | 7.92% (200), $86.23 | 44 (189 unfilled) | -7.26% [-38.96%, 25.42%] | $49.48 | 41 (159 unfilled) | 7.36% [-21.04%, 36.64%] | $53.23 |
| map | 2026-07 | 581 | 0.654397 | 0.649858 | 0.640757 | -7.13% (375), $8.18 | -5.11% (333), $12.68 | 91 (284 unfilled) | -22.81% [-41.28%, -3.34%] | $16.27 | 74 (259 unfilled) | -16.74% [-35.50%, 2.90%] | $25.81 |
| map | 2026-08 | 801 | 0.621471 | 0.614855 | 0.625646 | -1.70% (561), $17.49 | 6.88% (352), $208.65 | 104 (457 unfilled) | -13.55% [-35.68%, 9.69%] | $32.04 | 66 (286 unfilled) | -2.32% [-26.08%, 24.00%] | $47.14 |
| map | 2026-09 | 807 | 0.659957 | 0.648070 | 0.642565 | -10.88% (545), $0.31 | -7.32% (348), $18.71 | 190 (355 unfilled) | -15.72% [-32.89%, 2.89%] | $3.06 | 134 (214 unfilled) | -15.07% [-33.29%, 4.23%] | $37.15 |
| map | 2026-10 | 590 | 0.640973 | 0.625557 | 0.626949 | -13.41% (356), $1.51 | 5.14% (186), $50.27 | 141 (215 unfilled) | -26.11% [-42.74%, -8.94%] | $5.86 | 60 (126 unfilled) | -7.27% [-29.77%, 14.91%] | $28.79 |
| series | 2026-01 | 49 | 0.565518 | — | 0.590419 | 11.62% (36), $68.67 | — | 29 (7 unfilled) | 39.11% [-11.77%, 90.87%] | $86.06 | — | — | — |
| series | 2026-02 | 144 | 0.588324 | — | 0.567099 | -13.74% (102), $9.05 | — | 91 (11 unfilled) | -16.78% [-37.63%, 5.73%] | $8.15 | — | — | — |
| series | 2026-03 | 286 | 0.583633 | 0.571325 | 0.589357 | 1.40% (205), $24.48 | 10.83% (176), $196.94 | 156 (49 unfilled) | 2.75% [-15.69%, 23.03%] | $40.80 | 134 (42 unfilled) | 5.49% [-7.57%, 17.82%] | $117.85 |
| series | 2026-04 | 302 | 0.575226 | 0.560668 | 0.578002 | 6.85% (225), $23.84 | 10.22% (203), $257.92 | 167 (58 unfilled) | 8.53% [-11.01%, 29.58%] | $69.38 | 148 (55 unfilled) | 14.17% [-2.80%, 32.74%] | $135.76 |
| series | 2026-05 | 325 | 0.616610 | 0.596993 | 0.595148 | -7.19% (232), $4.50 | 0.94% (209), $33.80 | 190 (42 unfilled) | -7.81% [-25.26%, 10.34%] | $5.36 | 168 (41 unfilled) | -1.36% [-15.68%, 13.33%] | $28.53 |
| series | 2026-06 | 320 | 0.621179 | 0.622716 | 0.634132 | 5.43% (242), $121.62 | 9.73% (186), $153.46 | 156 (86 unfilled) | 15.78% [-4.36%, 36.79%] | $273.51 | 126 (60 unfilled) | 15.74% [1.07%, 30.77%] | $103.85 |
| series | 2026-07 | 481 | 0.627515 | 0.613729 | 0.616051 | -0.24% (363), $3.94 | 1.50% (294), $17.50 | 229 (134 unfilled) | 0.09% [-17.63%, 19.63%] | $20.89 | 187 (107 unfilled) | -0.88% [-17.88%, 18.95%] | $17.33 |
| series | 2026-08 | 658 | 0.609026 | 0.600098 | 0.615564 | 4.84% (514), $5.61 | 6.52% (399), $213.54 | 257 (257 unfilled) | -0.53% [-16.34%, 17.18%] | $35.62 | 201 (198 unfilled) | 12.08% [-4.44%, 31.25%] | $248.79 |
| series | 2026-09 | 852 | 0.596346 | 0.584865 | 0.601766 | 2.75% (647), $3.39 | 13.29% (459), $1353.50 | 361 (286 unfilled) | -3.11% [-14.35%, 8.69%] | $4.99 | 267 (192 unfilled) | 2.38% [-9.15%, 14.24%] | $146.15 |
| series | 2026-10 | 719 | 0.589114 | 0.575405 | 0.585415 | 2.71% (516), $13.02 | 8.56% (371), $135.35 | 313 (203 unfilled) | 2.01% [-10.33%, 14.75%] | $28.52 | 219 (152 unfilled) | 2.50% [-9.05%, 13.99%] | $58.85 |

### player_round_glicko_rookie_weights: Kalshi comparison and returns



#### Log loss vs Kalshi

| Kind | Slice | Rows | Model log loss | Kalshi log loss | Difference [95% interval] | Significant |
|---|---|---:|---:|---:|---|---|
| series | all | 4136 | 0.596691 | 0.600829 | -0.004138 [-0.012401, 0.003726] | no |
| series | tier1 | 685 | 0.626057 | 0.614585 | 0.011472 [-0.006225, 0.029063] | no |
| series | tier2 | 1814 | 0.595583 | 0.590902 | 0.004681 [-0.005031, 0.015412] | no |
| series | tier3 | 1595 | 0.588161 | 0.609630 | -0.021469 [-0.035923, -0.005557] | yes |
| series | unknown | 42 | 0.489524 | 0.471027 | 0.018496 [-0.044515, 0.081152] | no |
| series | international=1 | 436 | 0.607866 | 0.592747 | 0.015119 [-0.007863, 0.037779] | no |
| series | international=0 | 3700 | 0.595374 | 0.601782 | -0.006407 [-0.015490, 0.002170] | no |
| map | all | 4087 | 0.640554 | 0.637334 | 0.003221 [-0.002813, 0.009571] | no |
| map | tier1 | 1117 | 0.654267 | 0.643855 | 0.010412 [-0.001876, 0.021884] | no |
| map | tier2 | 1772 | 0.638122 | 0.636583 | 0.001539 [-0.007717, 0.010212] | no |
| map | tier3 | 1144 | 0.633642 | 0.635738 | -0.002096 [-0.015536, 0.011545] | no |
| map | unknown | 54 | 0.583152 | 0.560856 | 0.022296 [-0.012112, 0.058557] | no |
| map | international=1 | 765 | 0.634256 | 0.630727 | 0.003529 [-0.010226, 0.017042] | no |
| map | international=0 | 3322 | 0.642005 | 0.638855 | 0.003150 [-0.003900, 0.009977] | no |

#### Full-Kelly returns

| Kind | Slice | Bets | Matches | Mean edge | Flat ROI [95% interval] | Kelly, LoL caps ($50 start) | Multiple | Max drawdown | Largest stake | Bets filled | Flat ROI depth-capped [95% interval] | Kelly depth-capped final |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---:|
| series | all | 3079 | 3074 | 0.0820 | 2.94% [-1.41%, 7.55%] | $0.03 | 0.001× | 99.98% | $11.82 | 1951 (1128 unfilled) | 1.04% [-4.44%, 6.59%] | $2.70 |
| series | tier1 | 518 | 518 | 0.0716 | -1.70% [-12.64%, 10.44%] | $1.92 | 0.038× | 99.37% | $15.61 | 423 (95 unfilled) | -4.95% [-16.73%, 7.65%] | $1.32 |
| series | tier2 | 1291 | 1288 | 0.0719 | -1.84% [-8.63%, 4.90%] | $0.06 | 0.001× | 99.93% | $8.50 | 808 (483 unfilled) | -3.56% [-11.69%, 4.56%] | $0.64 |
| series | tier3 | 1237 | 1235 | 0.0969 | 10.44% [3.37%, 18.37%] | $8440.17 | 168.803× | 92.11% | $249.12 | 697 (540 unfilled) | 10.46% [1.00%, 20.32%] | $283.66 |
| series | unknown | 33 | 33 | 0.0792 | -18.11% [-48.56%, 16.00%] | $40.36 | 0.807× | 32.95% | $5.78 | 23 (10 unfilled) | -11.86% [-49.11%, 31.13%] | $40.78 |
| series | international=1 | 324 | 324 | 0.0727 | -2.81% [-16.95%, 13.25%] | $2.49 | 0.050× | 99.18% | $13.49 | 282 (42 unfilled) | -7.49% [-22.51%, 7.83%] | $1.29 |
| series | international=0 | 2755 | 2750 | 0.0830 | 3.62% [-1.16%, 8.28%] | $0.10 | 0.002× | 99.85% | $6.01 | 1669 (1086 unfilled) | 2.48% [-3.56%, 8.33%] | $21.14 |
| map | all | 2593 | 1663 | 0.0586 | -3.33% [-7.83%, 1.36%] | $0.07 | 0.001× | 99.99% | $104.25 | 759 (1834 unfilled) | -15.74% [-23.51%, -8.08%] | $0.10 |
| map | tier1 | 709 | 485 | 0.0578 | -3.98% [-13.36%, 5.77%] | $10.65 | 0.213× | 93.96% | $15.53 | 229 (480 unfilled) | -4.69% [-20.33%, 11.45%] | $11.51 |
| map | tier2 | 1087 | 684 | 0.0524 | -1.62% [-8.63%, 5.72%] | $3.35 | 0.067× | 99.16% | $34.58 | 302 (785 unfilled) | -17.24% [-28.86%, -6.50%] | $0.33 |
| map | tier3 | 766 | 473 | 0.0684 | -4.46% [-12.61%, 3.81%] | $6.61 | 0.132× | 98.51% | $16.62 | 217 (549 unfilled) | -25.27% [-39.77%, -10.50%] | $2.78 |
| map | unknown | 31 | 21 | 0.0478 | -20.77% [-51.14%, 6.53%] | $35.77 | 0.715× | 32.85% | $4.78 | 11 (20 unfilled) | -16.99% [-56.80%, 17.05%] | $46.34 |
| map | international=1 | 476 | 332 | 0.0604 | -1.49% [-12.67%, 11.08%] | $40.66 | 0.813× | 83.03% | $23.46 | 164 (312 unfilled) | -1.90% [-22.05%, 18.01%] | $30.92 |
| map | international=0 | 2117 | 1331 | 0.0582 | -3.75% [-8.70%, 1.42%] | $0.09 | 0.002× | 99.98% | $37.95 | 595 (1522 unfilled) | -19.56% [-27.89%, -10.80%] | $0.08 |
| series+map | all | 5672 | 3350 | 0.0713 | 0.07% [-3.63%, 3.63%] | $0.06 | 0.001× | 99.97% | $23.79 | 2710 (2962 unfilled) | -3.66% [-8.59%, 1.20%] | $0.52 |

#### Monthly market blend fits

UTC monthly fits use earlier rows of the same kind from 2026-01-01, excluding holdout; minimum 100 rows. logit(p_blend) = a·logit(mid) + b·(logit(p_model) − logit(mid)); inputs clipped to [0.01, 0.99], no intercept, ridge 1e-6. Unfitted rows use mid unchanged; excluded from blended tables: 346 rows. Rating parameters remain selected on the tuning window.

| Month | Kind | n | a | b | Status |
|---|---|---:|---:|---:|---|
| 2026-01 | series | 0 | 1.000000 | 0.000000 | unfitted |
| 2026-01 | map | 0 | 1.000000 | 0.000000 | unfitted |
| 2026-02 | series | 49 | 1.000000 | 0.000000 | unfitted |
| 2026-02 | map | 61 | 1.000000 | 0.000000 | unfitted |
| 2026-03 | series | 193 | 1.406407 | 0.731095 | fitted |
| 2026-03 | map | 153 | 1.368760 | 0.660826 | fitted |
| 2026-04 | series | 479 | 1.387467 | 0.779522 | fitted |
| 2026-04 | map | 285 | 1.230334 | 0.531121 | fitted |
| 2026-05 | series | 781 | 1.378588 | 0.822527 | fitted |
| 2026-05 | map | 532 | 1.318432 | 0.947318 | fitted |
| 2026-06 | series | 1106 | 1.338913 | 0.664647 | fitted |
| 2026-06 | map | 934 | 1.326614 | 0.806518 | fitted |
| 2026-07 | series | 1426 | 1.282138 | 0.680090 | fitted |
| 2026-07 | map | 1308 | 1.316554 | 0.834904 | fitted |
| 2026-08 | series | 1907 | 1.235665 | 0.609197 | fitted |
| 2026-08 | map | 1889 | 1.186296 | 0.588510 | fitted |
| 2026-09 | series | 2565 | 1.228918 | 0.634981 | fitted |
| 2026-09 | map | 2690 | 1.239979 | 0.648329 | fitted |
| 2026-10 | series | 3417 | 1.238231 | 0.665701 | fitted |
| 2026-10 | map | 3497 | 1.188353 | 0.532750 | fitted |

#### Log loss vs Kalshi (blended)

| Kind | Slice | Rows | Model log loss | Kalshi log loss | Difference [95% interval] | Significant |
|---|---|---:|---:|---:|---|---|
| series | all | 3943 | 0.587655 | 0.602190 | -0.014536 [-0.020164, -0.008951] | yes |
| series | tier1 | 578 | 0.616594 | 0.615317 | 0.001277 [-0.011338, 0.013676] | no |
| series | tier2 | 1733 | 0.583288 | 0.593744 | -0.010456 [-0.017575, -0.002919] | yes |
| series | tier3 | 1590 | 0.585622 | 0.610089 | -0.024468 [-0.034437, -0.013939] | yes |
| series | unknown | 42 | 0.446549 | 0.471027 | -0.024479 [-0.056573, 0.008386] | no |
| series | international=1 | 359 | 0.594235 | 0.591638 | 0.002596 [-0.010965, 0.017068] | no |
| series | international=0 | 3584 | 0.586996 | 0.603247 | -0.016252 [-0.022273, -0.010515] | yes |
| map | all | 3934 | 0.634355 | 0.638132 | -0.003778 [-0.008139, 0.000379] | no |
| map | tier1 | 990 | 0.653116 | 0.647070 | 0.006046 [-0.001767, 0.014354] | no |
| map | tier2 | 1748 | 0.629894 | 0.636671 | -0.006777 [-0.012471, -0.001238] | yes |
| map | tier3 | 1142 | 0.628721 | 0.636276 | -0.007556 [-0.017875, 0.002452] | no |
| map | unknown | 54 | 0.553960 | 0.560856 | -0.006897 [-0.030375, 0.016520] | no |
| map | international=1 | 665 | 0.627865 | 0.630639 | -0.002774 [-0.011220, 0.005863] | no |
| map | international=0 | 3269 | 0.635675 | 0.639657 | -0.003982 [-0.009060, 0.000925] | no |

#### Full-Kelly returns (blended)

| Kind | Slice | Bets | Matches | Mean edge | Flat ROI [95% interval] | Kelly, LoL caps ($50 start) | Multiple | Max drawdown | Largest stake | Bets filled | Flat ROI depth-capped [95% interval] | Kelly depth-capped final |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---:|
| series | all | 2394 | 2390 | 0.0499 | 8.97% [4.81%, 13.25%] | $9338.30 | 186.766× | 68.31% | $249.12 | 1503 (891 unfilled) | 5.92% [0.91%, 11.17%] | $793.67 |
| series | tier1 | 318 | 318 | 0.0389 | -2.96% [-13.62%, 8.37%] | $19.87 | 0.397× | 88.42% | $12.26 | 251 (67 unfilled) | -6.15% [-18.57%, 5.35%] | $23.97 |
| series | tier2 | 1022 | 1020 | 0.0435 | 7.52% [2.08%, 13.17%] | $4071.46 | 81.429× | 48.42% | $249.47 | 628 (394 unfilled) | 3.67% [-3.17%, 11.18%] | $86.84 |
| series | tier3 | 1025 | 1023 | 0.0599 | 14.41% [7.88%, 21.24%] | $12868.04 | 257.361× | 61.63% | $249.12 | 605 (420 unfilled) | 13.63% [5.06%, 22.80%] | $1413.82 |
| series | unknown | 29 | 29 | 0.0463 | -1.03% [-28.26%, 25.33%] | $65.42 | 1.308× | 10.01% | $6.55 | 19 (10 unfilled) | -5.59% [-41.97%, 36.05%] | $55.83 |
| series | international=1 | 195 | 195 | 0.0349 | -4.68% [-19.64%, 11.79%] | $51.36 | 1.027× | 68.05% | $12.23 | 163 (32 unfilled) | -6.82% [-22.71%, 10.42%] | $60.48 |
| series | international=0 | 2199 | 2195 | 0.0513 | 10.18% [5.86%, 14.34%] | $14085.50 | 281.710× | 74.39% | $249.12 | 1340 (859 unfilled) | 7.47% [2.48%, 13.24%] | $689.28 |
| map | all | 1817 | 1141 | 0.0383 | 4.31% [-0.91%, 9.47%] | $2453.59 | 49.072× | 81.30% | $248.43 | 514 (1303 unfilled) | -8.46% [-16.05%, -0.01%] | $8.63 |
| map | tier1 | 391 | 259 | 0.0390 | 0.36% [-9.98%, 11.78%] | $34.13 | 0.683× | 85.14% | $17.11 | 127 (264 unfilled) | -6.72% [-23.02%, 10.90%] | $35.48 |
| map | tier2 | 777 | 486 | 0.0334 | 4.89% [-2.57%, 13.37%] | $349.57 | 6.991× | 49.90% | $69.04 | 206 (571 unfilled) | -10.49% [-21.90%, 0.77%] | $22.11 |
| map | tier3 | 626 | 380 | 0.0441 | 6.22% [-1.85%, 14.52%] | $279.09 | 5.582× | 69.32% | $32.84 | 170 (456 unfilled) | -7.83% [-22.53%, 7.93%] | $23.53 |
| map | unknown | 23 | 16 | 0.0333 | -0.07% [-27.68%, 27.11%] | $52.52 | 1.050× | 10.46% | $4.67 | 11 (12 unfilled) | -0.06% [-37.68%, 33.08%] | $54.12 |
| map | international=1 | 262 | 176 | 0.0373 | 5.81% [-8.05%, 21.04%] | $107.23 | 2.145× | 55.45% | $17.15 | 95 (167 unfilled) | 0.91% [-17.94%, 20.73%] | $56.77 |
| map | international=0 | 1555 | 965 | 0.0384 | 4.06% [-1.32%, 9.55%] | $618.25 | 12.365× | 80.55% | $114.74 | 419 (1136 unfilled) | -10.58% [-19.64%, -1.97%] | $6.85 |
| series+map | all | 4211 | 2532 | 0.0449 | 6.96% [3.41%, 10.58%] | $17702.91 | 354.058× | 45.86% | $249.47 | 2017 (2194 unfilled) | 2.25% [-2.55%, 7.14%] | $356.51 |

#### Monthly breakdown

All metrics use identical linked rows within each kind/month. Unfitted blend months show —; counts include all rows.

| Kind | Month | Rows | Model log loss | Blended log loss | Kalshi log loss | Raw flat ROI (bets), unlimited Kelly final | Blended flat ROI (bets), unlimited Kelly final | Raw bets filled | Raw Flat ROI depth-capped [95% interval] | Raw Kelly depth-capped final | Blended bets filled | Blended Flat ROI depth-capped [95% interval] | Blended Kelly depth-capped final |
|---|---|---:|---:|---:|---:|---|---|---:|---|---:|---:|---|---:|
| map | 2026-01 | 61 | 0.618405 | — | 0.634669 | 7.20% (42), $67.32 | — | 5 (37 unfilled) | 11.19% [-66.65%, 89.92%] | $50.38 | — | — | — |
| map | 2026-02 | 92 | 0.625348 | — | 0.604939 | -17.16% (53), $36.50 | — | 17 (36 unfilled) | -70.79% [-100.00%, -33.71%] | $26.53 | — | — | — |
| map | 2026-03 | 132 | 0.656094 | 0.651030 | 0.650213 | -3.86% (73), $36.23 | -16.43% (52), $39.15 | 33 (40 unfilled) | 8.67% [-36.12%, 54.57%] | $40.08 | 24 (28 unfilled) | -21.25% [-51.62%, 6.58%] | $38.63 |
| map | 2026-04 | 247 | 0.623312 | 0.628698 | 0.654704 | 25.60% (143), $405.26 | 50.71% (80), $504.14 | 52 (91 unfilled) | 2.48% [-26.46%, 32.73%] | $33.58 | 24 (56 unfilled) | -6.89% [-37.53%, 21.75%] | $50.67 |
| map | 2026-05 | 402 | 0.644816 | 0.635874 | 0.640045 | 1.30% (250), $71.18 | 4.64% (230), $83.96 | 90 (160 unfilled) | -3.53% [-25.63%, 18.61%] | $38.51 | 91 (139 unfilled) | 2.38% [-18.12%, 22.37%] | $57.08 |
| map | 2026-06 | 374 | 0.639831 | 0.638208 | 0.651611 | 4.28% (209), $102.34 | 10.00% (185), $124.97 | 44 (165 unfilled) | -10.63% [-42.05%, 22.87%] | $44.30 | 38 (147 unfilled) | 3.22% [-27.86%, 34.55%] | $56.75 |
| map | 2026-07 | 581 | 0.654599 | 0.650912 | 0.640757 | -5.87% (368), $10.09 | -4.43% (337), $13.74 | 82 (286 unfilled) | -18.28% [-38.72%, 1.75%] | $20.69 | 74 (263 unfilled) | -10.69% [-28.88%, 8.90%] | $32.13 |
| map | 2026-08 | 801 | 0.620303 | 0.613822 | 0.625646 | 0.10% (550), $42.19 | 11.86% (370), $267.23 | 106 (444 unfilled) | -10.81% [-32.85%, 10.27%] | $32.01 | 69 (301 unfilled) | 9.78% [-15.31%, 37.01%] | $57.79 |
| map | 2026-09 | 807 | 0.657411 | 0.647443 | 0.642565 | -11.87% (547), $0.42 | -6.23% (374), $21.94 | 187 (360 unfilled) | -21.27% [-37.24%, -2.58%] | $1.24 | 135 (239 unfilled) | -22.22% [-35.99%, -8.58%] | $21.38 |
| map | 2026-10 | 590 | 0.637118 | 0.623184 | 0.626949 | -11.27% (358), $1.04 | 6.02% (189), $56.65 | 143 (215 unfilled) | -26.61% [-43.18%, -9.69%] | $4.82 | 59 (130 unfilled) | -15.23% [-37.62%, 6.28%] | $27.82 |
| series | 2026-01 | 49 | 0.558665 | — | 0.590419 | 11.11% (38), $99.48 | — | 32 (6 unfilled) | 32.35% [-11.23%, 81.23%] | $114.65 | — | — | — |
| series | 2026-02 | 144 | 0.581998 | — | 0.567099 | -17.92% (98), $10.86 | — | 87 (11 unfilled) | -21.66% [-41.43%, 0.61%] | $10.09 | — | — | — |
| series | 2026-03 | 286 | 0.585913 | 0.573072 | 0.589357 | 2.54% (213), $21.34 | 5.44% (198), $177.19 | 168 (45 unfilled) | 3.42% [-14.46%, 20.63%] | $33.98 | 153 (45 unfilled) | 1.47% [-11.52%, 14.00%] | $99.70 |
| series | 2026-04 | 302 | 0.570618 | 0.558752 | 0.578002 | 7.60% (223), $70.93 | 12.33% (198), $169.72 | 161 (62 unfilled) | 10.30% [-9.36%, 31.16%] | $95.04 | 144 (54 unfilled) | 14.87% [-1.38%, 33.54%] | $112.17 |
| series | 2026-05 | 325 | 0.617296 | 0.597884 | 0.595148 | -3.48% (246), $6.01 | -1.70% (215), $40.72 | 199 (47 unfilled) | -6.89% [-23.18%, 9.57%] | $2.77 | 167 (48 unfilled) | -6.85% [-21.30%, 6.97%] | $25.12 |
| series | 2026-06 | 320 | 0.617418 | 0.619845 | 0.634132 | 10.63% (232), $206.46 | 10.55% (181), $225.77 | 157 (75 unfilled) | 20.26% [0.34%, 39.94%] | $371.39 | 124 (57 unfilled) | 11.21% [-2.59%, 27.03%] | $129.81 |
| series | 2026-07 | 481 | 0.618417 | 0.607702 | 0.616051 | 1.10% (363), $5.91 | 4.01% (308), $31.69 | 226 (137 unfilled) | 4.31% [-12.83%, 22.67%] | $36.03 | 198 (110 unfilled) | 0.63% [-15.85%, 19.36%] | $22.26 |
| series | 2026-08 | 658 | 0.603621 | 0.595359 | 0.615564 | 6.42% (524), $59.01 | 11.11% (415), $293.03 | 264 (260 unfilled) | 4.66% [-11.06%, 21.25%] | $75.45 | 206 (209 unfilled) | 16.81% [0.86%, 35.25%] | $256.27 |
| series | 2026-09 | 852 | 0.590209 | 0.581454 | 0.601766 | 5.23% (647), $13.43 | 15.52% (485), $3029.78 | 357 (290 unfilled) | -6.41% [-17.91%, 5.13%] | $5.32 | 284 (201 unfilled) | 6.72% [-3.42%, 17.46%] | $222.71 |
| series | 2026-10 | 719 | 0.585729 | 0.573530 | 0.585415 | -1.26% (495), $21.05 | 7.71% (394), $151.73 | 300 (195 unfilled) | -3.63% [-16.08%, 10.31%] | $26.36 | 227 (167 unfilled) | 3.45% [-7.70%, 14.29%] | $51.04 |

### team_elo+none: Kalshi comparison and returns

none

#### Log loss vs Kalshi

| Kind | Slice | Rows | Model log loss | Kalshi log loss | Difference [95% interval] | Significant |
|---|---|---:|---:|---:|---|---|
| series | all | 4136 | 0.625869 | 0.600829 | 0.025040 [0.016663, 0.033211] | yes |
| series | tier1 | 685 | 0.638551 | 0.614585 | 0.023966 [0.002515, 0.045256] | yes |
| series | tier2 | 1814 | 0.628641 | 0.590902 | 0.037739 [0.025494, 0.049681] | yes |
| series | tier3 | 1595 | 0.619847 | 0.609630 | 0.010217 [-0.003083, 0.024344] | no |
| series | unknown | 42 | 0.527980 | 0.471027 | 0.056952 [-0.017412, 0.134365] | no |
| series | international=1 | 436 | 0.605667 | 0.592747 | 0.012920 [-0.009540, 0.036134] | no |
| series | international=0 | 3700 | 0.628250 | 0.601782 | 0.026468 [0.017066, 0.035174] | yes |
| map | all | 4087 | 0.660902 | 0.637334 | 0.023569 [0.015578, 0.031565] | yes |
| map | tier1 | 1117 | 0.666997 | 0.643855 | 0.023142 [0.007811, 0.039094] | yes |
| map | tier2 | 1772 | 0.663547 | 0.636583 | 0.026964 [0.015160, 0.038158] | yes |
| map | tier3 | 1144 | 0.653841 | 0.635738 | 0.018103 [0.004317, 0.033179] | yes |
| map | unknown | 54 | 0.597663 | 0.560856 | 0.036807 [-0.011319, 0.082276] | no |
| map | international=1 | 765 | 0.632264 | 0.630727 | 0.001537 [-0.015772, 0.017961] | no |
| map | international=0 | 3322 | 0.667497 | 0.638855 | 0.028643 [0.019864, 0.037566] | yes |

#### Full-Kelly returns

| Kind | Slice | Bets | Matches | Mean edge | Flat ROI [95% interval] | Kelly, LoL caps ($50 start) | Multiple | Max drawdown | Largest stake | Bets filled | Flat ROI depth-capped [95% interval] | Kelly depth-capped final |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---:|
| series | all | 3075 | 3070 | 0.0881 | -7.18% [-11.56%, -2.45%] | $0.09 | 0.002× | 99.92% | $10.63 | 1948 (1127 unfilled) | -5.72% [-11.33%, -0.25%] | $0.08 |
| series | tier1 | 505 | 505 | 0.0795 | -7.55% [-18.06%, 3.52%] | $0.06 | 0.001× | 99.96% | $16.89 | 413 (92 unfilled) | -5.76% [-17.14%, 6.03%] | $2.79 |
| series | tier2 | 1328 | 1325 | 0.0860 | -12.52% [-18.65%, -5.94%] | $0.07 | 0.001× | 99.86% | $4.97 | 823 (505 unfilled) | -12.97% [-20.79%, -4.58%] | $0.05 |
| series | tier3 | 1211 | 1209 | 0.0937 | -0.51% [-8.40%, 7.66%] | $0.08 | 0.002× | 99.92% | $9.03 | 692 (519 unfilled) | 3.58% [-6.28%, 13.49%] | $8.44 |
| series | unknown | 31 | 31 | 0.0987 | -33.30% [-59.30%, -4.68%] | $21.71 | 0.434× | 60.39% | $5.24 | 20 (11 unfilled) | -28.95% [-65.86%, 12.03%] | $29.07 |
| series | international=1 | 320 | 320 | 0.0730 | -6.60% [-20.95%, 8.37%] | $6.14 | 0.123× | 97.73% | $8.64 | 277 (43 unfilled) | -6.55% [-20.89%, 7.75%] | $8.56 |
| series | international=0 | 2755 | 2750 | 0.0898 | -7.25% [-12.13%, -2.46%] | $0.06 | 0.001× | 99.93% | $8.21 | 1671 (1084 unfilled) | -5.58% [-11.45%, 0.48%] | $0.09 |
| map | all | 2828 | 1758 | 0.0737 | -6.37% [-10.72%, -1.90%] | $0.08 | 0.002× | 99.94% | $13.69 | 849 (1979 unfilled) | -12.61% [-19.37%, -5.54%] | $0.10 |
| map | tier1 | 759 | 492 | 0.0784 | -2.39% [-10.87%, 6.12%] | $6.35 | 0.127× | 96.26% | $5.79 | 248 (511 unfilled) | -3.48% [-16.97%, 10.39%] | $24.77 |
| map | tier2 | 1216 | 748 | 0.0710 | -6.50% [-12.59%, 0.14%] | $0.09 | 0.002× | 99.89% | $7.11 | 361 (855 unfilled) | -15.56% [-25.70%, -4.62%] | $0.12 |
| map | tier3 | 817 | 496 | 0.0730 | -8.83% [-16.74%, -0.92%] | $0.98 | 0.020× | 99.64% | $19.63 | 227 (590 unfilled) | -16.23% [-29.62%, -1.92%] | $5.74 |
| map | unknown | 36 | 22 | 0.0810 | -29.73% [-55.86%, -6.41%] | $26.30 | 0.526× | 47.51% | $4.78 | 13 (23 unfilled) | -41.29% [-77.65%, -5.83%] | $36.82 |
| map | international=1 | 515 | 341 | 0.0733 | 4.03% [-6.64%, 14.79%] | $63.87 | 1.277× | 83.55% | $7.82 | 178 (337 unfilled) | 7.72% [-9.53%, 26.14%] | $87.59 |
| map | international=0 | 2313 | 1417 | 0.0738 | -8.68% [-13.44%, -3.77%] | $0.08 | 0.002× | 99.92% | $9.16 | 671 (1642 unfilled) | -17.99% [-25.44%, -10.49%] | $0.08 |
| series+map | all | 5903 | 3443 | 0.0812 | -6.79% [-10.16%, -3.20%] | $0.03 | 0.001× | 99.95% | $6.13 | 2797 (3106 unfilled) | -7.81% [-12.29%, -2.69%] | $0.08 |

#### Monthly market blend fits

UTC monthly fits use earlier rows of the same kind from 2026-01-01, excluding holdout; minimum 100 rows. logit(p_blend) = a·logit(mid) + b·(logit(p_model) − logit(mid)); inputs clipped to [0.01, 0.99], no intercept, ridge 1e-6. Unfitted rows use mid unchanged; excluded from blended tables: 346 rows. Rating parameters remain selected on the tuning window.

| Month | Kind | n | a | b | Status |
|---|---|---:|---:|---:|---|
| 2026-01 | series | 0 | 1.000000 | 0.000000 | unfitted |
| 2026-01 | map | 0 | 1.000000 | 0.000000 | unfitted |
| 2026-02 | series | 49 | 1.000000 | 0.000000 | unfitted |
| 2026-02 | map | 61 | 1.000000 | 0.000000 | unfitted |
| 2026-03 | series | 193 | 1.348589 | 0.508136 | fitted |
| 2026-03 | map | 153 | 1.179920 | -0.170761 | fitted |
| 2026-04 | series | 479 | 1.312188 | 0.424545 | fitted |
| 2026-04 | map | 285 | 1.090028 | 0.051788 | fitted |
| 2026-05 | series | 781 | 1.293180 | 0.464303 | fitted |
| 2026-05 | map | 532 | 1.007501 | 0.344396 | fitted |
| 2026-06 | series | 1106 | 1.238193 | 0.299775 | fitted |
| 2026-06 | map | 934 | 1.060575 | 0.301034 | fitted |
| 2026-07 | series | 1426 | 1.186169 | 0.287089 | fitted |
| 2026-07 | map | 1308 | 1.081621 | 0.341783 | fitted |
| 2026-08 | series | 1907 | 1.133808 | 0.151473 | fitted |
| 2026-08 | map | 1889 | 1.057818 | 0.094635 | fitted |
| 2026-09 | series | 2565 | 1.143395 | 0.237220 | fitted |
| 2026-09 | map | 2690 | 1.108272 | 0.142689 | fitted |
| 2026-10 | series | 3417 | 1.139790 | 0.213454 | fitted |
| 2026-10 | map | 3497 | 1.085817 | 0.089923 | fitted |

#### Log loss vs Kalshi (blended)

| Kind | Slice | Rows | Model log loss | Kalshi log loss | Difference [95% interval] | Significant |
|---|---|---:|---:|---:|---|---|
| series | all | 3943 | 0.600957 | 0.602190 | -0.001233 [-0.003882, 0.001585] | no |
| series | tier1 | 578 | 0.620485 | 0.615317 | 0.005168 [-0.003632, 0.013699] | no |
| series | tier2 | 1733 | 0.593473 | 0.593744 | -0.000271 [-0.004645, 0.004148] | no |
| series | tier3 | 1590 | 0.605852 | 0.610089 | -0.004237 [-0.007563, -0.001017] | yes |
| series | unknown | 42 | 0.455744 | 0.471027 | -0.015283 [-0.042914, 0.014339] | no |
| series | international=1 | 359 | 0.593817 | 0.591638 | 0.002179 [-0.007434, 0.013089] | no |
| series | international=0 | 3584 | 0.601673 | 0.603247 | -0.001575 [-0.004291, 0.001103] | no |
| map | all | 3934 | 0.639191 | 0.638132 | 0.001058 [-0.000748, 0.002904] | no |
| map | tier1 | 990 | 0.651869 | 0.647070 | 0.004799 [0.000798, 0.009333] | yes |
| map | tier2 | 1748 | 0.636768 | 0.636671 | 0.000097 [-0.002509, 0.002648] | no |
| map | tier3 | 1142 | 0.635937 | 0.636276 | -0.000339 [-0.003213, 0.002582] | no |
| map | unknown | 54 | 0.553988 | 0.560856 | -0.006869 [-0.017275, 0.002474] | no |
| map | international=1 | 665 | 0.630345 | 0.630639 | -0.000294 [-0.004947, 0.004237] | no |
| map | international=0 | 3269 | 0.640990 | 0.639657 | 0.001333 [-0.000631, 0.003255] | no |

#### Full-Kelly returns (blended)

| Kind | Slice | Bets | Matches | Mean edge | Flat ROI [95% interval] | Kelly, LoL caps ($50 start) | Multiple | Max drawdown | Largest stake | Bets filled | Flat ROI depth-capped [95% interval] | Kelly depth-capped final |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---:|
| series | all | 1202 | 1201 | 0.0226 | 0.96% [-4.21%, 6.29%] | $14.00 | 0.280× | 96.04% | $22.88 | 826 (376 unfilled) | 2.53% [-3.61%, 9.09%] | $25.07 |
| series | tier1 | 212 | 212 | 0.0298 | -2.00% [-12.59%, 9.94%] | $15.01 | 0.300× | 82.53% | $8.31 | 173 (39 unfilled) | -2.18% [-12.85%, 8.58%] | $23.74 |
| series | tier2 | 602 | 601 | 0.0246 | -2.82% [-9.65%, 3.61%] | $14.34 | 0.287× | 87.69% | $10.15 | 413 (189 unfilled) | -0.62% [-9.32%, 7.73%] | $20.73 |
| series | tier3 | 366 | 366 | 0.0146 | 9.21% [-1.04%, 20.26%] | $157.79 | 3.156× | 35.65% | $16.15 | 222 (144 unfilled) | 13.15% [-0.18%, 29.21%] | $103.60 |
| series | unknown | 22 | 22 | 0.0314 | -4.12% [-33.84%, 26.84%] | $58.95 | 1.179× | 25.97% | $6.78 | 18 (4 unfilled) | -10.74% [-47.66%, 26.85%] | $52.85 |
| series | international=1 | 129 | 129 | 0.0282 | 2.58% [-12.27%, 18.31%] | $26.29 | 0.526× | 66.27% | $7.69 | 111 (18 unfilled) | -2.17% [-15.03%, 10.40%] | $27.18 |
| series | international=0 | 1073 | 1072 | 0.0219 | 0.77% [-4.39%, 6.28%] | $31.35 | 0.627× | 90.72% | $17.29 | 715 (358 unfilled) | 3.26% [-3.76%, 10.50%] | $45.21 |
| map | all | 421 | 264 | 0.0213 | -2.22% [-11.72%, 8.66%] | $31.69 | 0.634× | 79.09% | $9.43 | 119 (302 unfilled) | -10.09% [-23.86%, 4.51%] | $34.17 |
| map | tier1 | 135 | 84 | 0.0314 | -16.84% [-29.74%, -3.73%] | $20.13 | 0.403× | 61.41% | $4.05 | 45 (90 unfilled) | -11.34% [-35.18%, 13.46%] | $42.72 |
| map | tier2 | 189 | 121 | 0.0192 | -0.97% [-17.99%, 20.95%] | $58.41 | 1.168× | 50.28% | $8.28 | 52 (137 unfilled) | -8.92% [-29.48%, 11.47%] | $42.65 |
| map | tier3 | 89 | 53 | 0.0114 | 16.85% [-3.39%, 36.46%] | $68.84 | 1.377× | 24.98% | $4.52 | 18 (71 unfilled) | -13.17% [-53.08%, 29.42%] | $46.84 |
| map | unknown | 8 | 6 | 0.0079 | 2.44% [-38.16%, 36.12%] | $50.16 | 1.003× | 4.66% | $2.89 | 4 (4 unfilled) | 2.54% [-20.42%, 38.70%] | $49.86 |
| map | international=1 | 80 | 50 | 0.0250 | -3.76% [-21.19%, 14.00%] | $45.30 | 0.906× | 27.57% | $4.05 | 36 (44 unfilled) | -6.73% [-36.79%, 22.49%] | $46.85 |
| map | international=0 | 341 | 214 | 0.0204 | -1.85% [-13.37%, 11.77%] | $35.19 | 0.704× | 78.69% | $10.57 | 83 (258 unfilled) | -11.55% [-27.15%, 4.94%] | $36.29 |
| series+map | all | 1623 | 1244 | 0.0222 | 0.14% [-4.95%, 5.27%] | $29.89 | 0.598× | 90.12% | $19.36 | 945 (678 unfilled) | 0.94% [-5.13%, 6.90%] | $23.34 |

#### Monthly breakdown

All metrics use identical linked rows within each kind/month. Unfitted blend months show —; counts include all rows.

| Kind | Month | Rows | Model log loss | Blended log loss | Kalshi log loss | Raw flat ROI (bets), unlimited Kelly final | Blended flat ROI (bets), unlimited Kelly final | Raw bets filled | Raw Flat ROI depth-capped [95% interval] | Raw Kelly depth-capped final | Blended bets filled | Blended Flat ROI depth-capped [95% interval] | Blended Kelly depth-capped final |
|---|---|---:|---:|---:|---:|---|---|---:|---|---:|---:|---|---:|
| map | 2026-01 | 61 | 0.664952 | — | 0.634669 | -13.30% (42), $38.57 | — | 6 (36 unfilled) | -29.17% [-80.10%, 27.15%] | $47.79 | — | — | — |
| map | 2026-02 | 92 | 0.648097 | — | 0.604939 | -17.60% (61), $22.63 | — | 26 (35 unfilled) | -46.72% [-77.78%, -11.60%] | $22.57 | — | — | — |
| map | 2026-03 | 132 | 0.658811 | 0.655569 | 0.650213 | 0.68% (83), $48.04 | -15.83% (22), $40.62 | 48 (35 unfilled) | 12.14% [-20.29%, 44.39%] | $60.68 | 9 (13 unfilled) | -53.91% [-87.12%, -12.78%] | $38.49 |
| map | 2026-04 | 247 | 0.652344 | 0.654163 | 0.654704 | 17.39% (168), $204.76 | 27.08% (2), $50.41 | 64 (104 unfilled) | -11.64% [-31.49%, 7.43%] | $26.64 | 1 (1 unfilled) | 38.70% [38.70%, 38.70%] | $50.28 |
| map | 2026-05 | 402 | 0.657429 | 0.638964 | 0.640045 | -0.76% (282), $14.02 | 5.41% (100), $98.29 | 95 (187 unfilled) | -1.44% [-21.75%, 16.71%] | $35.78 | 38 (62 unfilled) | -1.55% [-30.37%, 27.90%] | $53.53 |
| map | 2026-06 | 374 | 0.652839 | 0.646735 | 0.651611 | -0.43% (246), $50.91 | 22.39% (78), $68.71 | 49 (197 unfilled) | 8.07% [-17.90%, 33.46%] | $53.58 | 13 (65 unfilled) | 4.91% [-40.68%, 40.54%] | $49.96 |
| map | 2026-07 | 581 | 0.697745 | 0.653245 | 0.640757 | -22.22% (387), $0.10 | -17.51% (144), $17.35 | 87 (300 unfilled) | -27.32% [-46.00%, -8.00%] | $20.62 | 30 (114 unfilled) | -19.03% [-44.84%, 6.60%] | $40.08 |
| map | 2026-08 | 801 | 0.639868 | 0.623796 | 0.625646 | -3.41% (585), $10.94 | 27.62% (8), $52.49 | 110 (475 unfilled) | -2.91% [-21.76%, 17.30%] | $29.04 | 1 (7 unfilled) | 27.32% [27.32%, 27.32%] | $50.65 |
| map | 2026-09 | 807 | 0.677381 | 0.644128 | 0.642565 | -12.26% (588), $0.09 | -11.64% (58), $38.55 | 210 (378 unfilled) | -20.23% [-35.94%, -3.39%] | $2.05 | 22 (36 unfilled) | -11.43% [-40.22%, 18.62%] | $49.53 |
| map | 2026-10 | 590 | 0.643747 | 0.624937 | 0.626949 | -3.15% (386), $5.73 | 4.31% (9), $50.65 | 154 (232 unfilled) | -15.95% [-30.68%, -0.75%] | $4.19 | 5 (4 unfilled) | 6.70% [-64.57%, 36.59%] | $51.30 |
| series | 2026-01 | 49 | 0.539697 | — | 0.590419 | 27.27% (39), $93.52 | — | 31 (8 unfilled) | 49.42% [7.30%, 93.72%] | $102.27 | — | — | — |
| series | 2026-02 | 144 | 0.599158 | — | 0.567099 | -23.04% (101), $5.65 | — | 90 (11 unfilled) | -19.54% [-39.83%, 1.61%] | $10.05 | — | — | — |
| series | 2026-03 | 286 | 0.613771 | 0.585162 | 0.589357 | -10.34% (197), $2.36 | 2.41% (166), $85.35 | 151 (46 unfilled) | -3.64% [-20.67%, 14.97%] | $10.73 | 126 (40 unfilled) | 4.09% [-8.94%, 17.66%] | $87.55 |
| series | 2026-04 | 302 | 0.590224 | 0.569711 | 0.578002 | -1.52% (221), $17.33 | 7.20% (176), $59.82 | 167 (54 unfilled) | -4.01% [-23.96%, 17.29%] | $16.13 | 134 (42 unfilled) | 5.69% [-10.75%, 24.27%] | $33.91 |
| series | 2026-05 | 325 | 0.638646 | 0.602696 | 0.595148 | -13.89% (236), $0.67 | -7.35% (172), $20.31 | 189 (47 unfilled) | -17.07% [-32.40%, -0.85%] | $1.03 | 141 (31 unfilled) | -7.28% [-20.57%, 5.62%] | $22.65 |
| series | 2026-06 | 320 | 0.650460 | 0.635371 | 0.634132 | -3.00% (235), $6.05 | -3.44% (124), $30.20 | 153 (82 unfilled) | 13.41% [-6.77%, 34.64%] | $243.28 | 80 (44 unfilled) | -1.23% [-18.30%, 15.28%] | $44.33 |
| series | 2026-07 | 481 | 0.669358 | 0.622372 | 0.616051 | -16.34% (369), $0.05 | -3.84% (162), $21.38 | 229 (140 unfilled) | -16.72% [-33.99%, 1.90%] | $1.85 | 104 (58 unfilled) | -0.91% [-25.57%, 31.92%] | $35.25 |
| series | 2026-08 | 658 | 0.626846 | 0.612026 | 0.615564 | -2.51% (510), $0.09 | 12.97% (91), $64.73 | 259 (251 unfilled) | -3.67% [-19.68%, 14.16%] | $23.97 | 48 (43 unfilled) | 21.49% [3.92%, 38.29%] | $62.55 |
| series | 2026-09 | 852 | 0.637185 | 0.601055 | 0.601766 | -6.27% (649), $0.02 | -4.57% (182), $39.96 | 358 (291 unfilled) | -5.94% [-17.97%, 6.84%] | $0.00 | 107 (75 unfilled) | 5.93% [-9.53%, 21.58%] | $56.12 |
| series | 2026-10 | 719 | 0.596758 | 0.579691 | 0.585415 | -5.94% (518), $0.04 | 11.38% (129), $73.87 | 321 (197 unfilled) | -5.03% [-18.43%, 8.31%] | $0.45 | 86 (43 unfilled) | 4.36% [-10.81%, 19.06%] | $56.51 |

### player_round_glicko+none: Kalshi comparison and returns

none

#### Log loss vs Kalshi

| Kind | Slice | Rows | Model log loss | Kalshi log loss | Difference [95% interval] | Significant |
|---|---|---:|---:|---:|---|---|
| series | all | 4136 | 0.601179 | 0.600829 | 0.000349 [-0.007997, 0.008261] | no |
| series | tier1 | 685 | 0.630196 | 0.614585 | 0.015611 [-0.003294, 0.034073] | no |
| series | tier2 | 1814 | 0.597676 | 0.590902 | 0.006774 [-0.002949, 0.017019] | no |
| series | tier3 | 1595 | 0.595539 | 0.609630 | -0.014091 [-0.028841, 0.002195] | no |
| series | unknown | 42 | 0.493388 | 0.471027 | 0.022360 [-0.039419, 0.084664] | no |
| series | international=1 | 436 | 0.610540 | 0.592747 | 0.017793 [-0.006566, 0.041850] | no |
| series | international=0 | 3700 | 0.600076 | 0.601782 | -0.001706 [-0.010486, 0.006661] | no |
| map | all | 4087 | 0.642445 | 0.637334 | 0.005111 [-0.000899, 0.011256] | no |
| map | tier1 | 1117 | 0.655010 | 0.643855 | 0.011155 [-0.001530, 0.022670] | no |
| map | tier2 | 1772 | 0.640047 | 0.636583 | 0.003464 [-0.005262, 0.012028] | no |
| map | tier3 | 1144 | 0.636592 | 0.635738 | 0.000854 [-0.012655, 0.014382] | no |
| map | unknown | 54 | 0.585190 | 0.560856 | 0.024334 [-0.011891, 0.063343] | no |
| map | international=1 | 765 | 0.636151 | 0.630727 | 0.005424 [-0.009241, 0.019854] | no |
| map | international=0 | 3322 | 0.643894 | 0.638855 | 0.005039 [-0.002008, 0.012043] | no |

#### Full-Kelly returns

| Kind | Slice | Bets | Matches | Mean edge | Flat ROI [95% interval] | Kelly, LoL caps ($50 start) | Multiple | Max drawdown | Largest stake | Bets filled | Flat ROI depth-capped [95% interval] | Kelly depth-capped final |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---:|
| series | all | 3082 | 3077 | 0.0821 | 1.97% [-2.62%, 6.76%] | $0.03 | 0.001× | 99.97% | $8.38 | 1949 (1133 unfilled) | 0.94% [-4.59%, 6.68%] | $0.06 |
| series | tier1 | 508 | 508 | 0.0792 | 1.75% [-9.27%, 14.15%] | $0.10 | 0.002× | 99.91% | $10.97 | 419 (89 unfilled) | -1.60% [-14.49%, 11.12%] | $0.46 |
| series | tier2 | 1282 | 1279 | 0.0720 | -3.74% [-10.56%, 3.46%] | $0.04 | 0.001× | 99.93% | $5.64 | 794 (488 unfilled) | -4.05% [-11.82%, 3.89%] | $0.09 |
| series | tier3 | 1259 | 1257 | 0.0937 | 8.40% [1.33%, 15.77%] | $5425.88 | 108.518× | 94.06% | $249.12 | 713 (546 unfilled) | 8.41% [-0.92%, 17.93%] | $178.06 |
| series | unknown | 33 | 33 | 0.0790 | -18.09% [-49.38%, 16.00%] | $31.15 | 0.623× | 41.12% | $5.10 | 23 (10 unfilled) | -11.86% [-49.11%, 31.13%] | $36.49 |
| series | international=1 | 326 | 326 | 0.0804 | 0.39% [-15.53%, 16.71%] | $1.13 | 0.023× | 99.34% | $11.29 | 284 (42 unfilled) | -5.34% [-20.51%, 10.66%] | $1.06 |
| series | international=0 | 2756 | 2751 | 0.0823 | 2.16% [-2.78%, 6.98%] | $0.10 | 0.002× | 99.85% | $6.24 | 1665 (1091 unfilled) | 2.02% [-3.77%, 7.95%] | $21.42 |
| map | all | 2622 | 1664 | 0.0595 | -4.62% [-8.97%, 0.05%] | $0.09 | 0.002× | 99.99% | $83.31 | 759 (1863 unfilled) | -14.96% [-22.27%, -7.00%] | $0.08 |
| map | tier1 | 716 | 487 | 0.0610 | -3.55% [-12.41%, 6.16%] | $5.98 | 0.120× | 94.92% | $10.80 | 228 (488 unfilled) | -4.04% [-20.60%, 13.22%] | $10.78 |
| map | tier2 | 1094 | 678 | 0.0529 | -3.99% [-11.02%, 3.21%] | $0.34 | 0.007× | 99.89% | $31.32 | 305 (789 unfilled) | -18.86% [-29.52%, -7.34%] | $0.39 |
| map | tier3 | 781 | 479 | 0.0678 | -6.03% [-14.27%, 2.30%] | $9.12 | 0.182× | 97.53% | $17.95 | 214 (567 unfilled) | -21.13% [-35.22%, -5.85%] | $6.09 |
| map | unknown | 31 | 20 | 0.0509 | -15.75% [-45.13%, 13.25%] | $36.99 | 0.740× | 30.22% | $4.78 | 12 (19 unfilled) | -13.86% [-51.82%, 16.78%] | $45.92 |
| map | international=1 | 489 | 337 | 0.0636 | -0.68% [-13.06%, 12.05%] | $23.60 | 0.472× | 89.46% | $21.98 | 166 (323 unfilled) | -0.54% [-20.49%, 21.50%] | $28.58 |
| map | international=0 | 2133 | 1327 | 0.0586 | -5.52% [-10.43%, -0.41%] | $0.08 | 0.002× | 99.97% | $23.44 | 593 (1540 unfilled) | -19.01% [-27.07%, -10.23%] | $0.09 |
| series+map | all | 5704 | 3363 | 0.0717 | -1.06% [-4.84%, 2.82%] | $0.08 | 0.002× | 99.90% | $6.26 | 2708 (2996 unfilled) | -3.51% [-8.43%, 1.56%] | $0.09 |

#### Monthly market blend fits

UTC monthly fits use earlier rows of the same kind from 2026-01-01, excluding holdout; minimum 100 rows. logit(p_blend) = a·logit(mid) + b·(logit(p_model) − logit(mid)); inputs clipped to [0.01, 0.99], no intercept, ridge 1e-6. Unfitted rows use mid unchanged; excluded from blended tables: 346 rows. Rating parameters remain selected on the tuning window.

| Month | Kind | n | a | b | Status |
|---|---|---:|---:|---:|---|
| 2026-01 | series | 0 | 1.000000 | 0.000000 | unfitted |
| 2026-01 | map | 0 | 1.000000 | 0.000000 | unfitted |
| 2026-02 | series | 49 | 1.000000 | 0.000000 | unfitted |
| 2026-02 | map | 61 | 1.000000 | 0.000000 | unfitted |
| 2026-03 | series | 193 | 1.412870 | 0.637893 | fitted |
| 2026-03 | map | 153 | 1.405922 | 0.726584 | fitted |
| 2026-04 | series | 479 | 1.429697 | 0.815808 | fitted |
| 2026-04 | map | 285 | 1.241068 | 0.543244 | fitted |
| 2026-05 | series | 781 | 1.405614 | 0.816315 | fitted |
| 2026-05 | map | 532 | 1.342872 | 0.971764 | fitted |
| 2026-06 | series | 1106 | 1.359642 | 0.671898 | fitted |
| 2026-06 | map | 934 | 1.339574 | 0.816406 | fitted |
| 2026-07 | series | 1426 | 1.298197 | 0.674531 | fitted |
| 2026-07 | map | 1308 | 1.318270 | 0.810821 | fitted |
| 2026-08 | series | 1907 | 1.243317 | 0.576199 | fitted |
| 2026-08 | map | 1889 | 1.190096 | 0.579620 | fitted |
| 2026-09 | series | 2565 | 1.230493 | 0.601141 | fitted |
| 2026-09 | map | 2690 | 1.236901 | 0.632350 | fitted |
| 2026-10 | series | 3417 | 1.244692 | 0.632801 | fitted |
| 2026-10 | map | 3497 | 1.185235 | 0.506205 | fitted |

#### Log loss vs Kalshi (blended)

| Kind | Slice | Rows | Model log loss | Kalshi log loss | Difference [95% interval] | Significant |
|---|---|---:|---:|---:|---|---|
| series | all | 3943 | 0.590439 | 0.602190 | -0.011751 [-0.017008, -0.006562] | yes |
| series | tier1 | 578 | 0.617489 | 0.615317 | 0.002172 [-0.009711, 0.013949] | no |
| series | tier2 | 1733 | 0.584065 | 0.593744 | -0.009679 [-0.016565, -0.002362] | yes |
| series | tier3 | 1590 | 0.591311 | 0.610089 | -0.018778 [-0.028057, -0.008925] | yes |
| series | unknown | 42 | 0.448197 | 0.471027 | -0.022831 [-0.053549, 0.009211] | no |
| series | international=1 | 359 | 0.592419 | 0.591638 | 0.000781 [-0.012219, 0.013778] | no |
| series | international=0 | 3584 | 0.590241 | 0.603247 | -0.013006 [-0.018596, -0.007352] | yes |
| map | all | 3934 | 0.635441 | 0.638132 | -0.002692 [-0.006873, 0.001481] | no |
| map | tier1 | 990 | 0.651692 | 0.647070 | 0.004622 [-0.003077, 0.012335] | no |
| map | tier2 | 1748 | 0.631449 | 0.636671 | -0.005221 [-0.010949, 0.000158] | no |
| map | tier3 | 1142 | 0.631240 | 0.636276 | -0.005036 [-0.014252, 0.004324] | no |
| map | unknown | 54 | 0.555541 | 0.560856 | -0.005315 [-0.029567, 0.019085] | no |
| map | international=1 | 665 | 0.627729 | 0.630639 | -0.002911 [-0.011792, 0.006090] | no |
| map | international=0 | 3269 | 0.637009 | 0.639657 | -0.002647 [-0.007517, 0.002288] | no |

#### Full-Kelly returns (blended)

| Kind | Slice | Bets | Matches | Mean edge | Flat ROI [95% interval] | Kelly, LoL caps ($50 start) | Multiple | Max drawdown | Largest stake | Bets filled | Flat ROI depth-capped [95% interval] | Kelly depth-capped final |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---:|
| series | all | 2297 | 2293 | 0.0473 | 7.97% [3.69%, 12.17%] | $6738.98 | 134.780× | 82.79% | $249.12 | 1450 (847 unfilled) | 5.54% [0.22%, 11.31%] | $607.97 |
| series | tier1 | 301 | 301 | 0.0384 | -0.08% [-12.76%, 13.74%] | $17.60 | 0.352× | 86.27% | $9.03 | 237 (64 unfilled) | -3.00% [-16.29%, 11.83%] | $22.49 |
| series | tier2 | 983 | 982 | 0.0421 | 6.48% [0.88%, 12.15%] | $3940.09 | 78.802× | 50.44% | $248.95 | 610 (373 unfilled) | 2.98% [-4.23%, 10.18%] | $149.74 |
| series | tier3 | 985 | 982 | 0.0553 | 12.07% [5.51%, 19.44%] | $10161.64 | 203.233× | 58.27% | $249.12 | 583 (402 unfilled) | 11.96% [3.04%, 21.43%] | $825.25 |
| series | unknown | 28 | 28 | 0.0446 | 2.67% [-24.05%, 30.23%] | $65.96 | 1.319× | 9.26% | $6.34 | 20 (8 unfilled) | -2.09% [-37.35%, 35.01%] | $56.87 |
| series | international=1 | 185 | 185 | 0.0342 | 2.12% [-14.51%, 19.77%] | $76.25 | 1.525× | 51.79% | $11.06 | 154 (31 unfilled) | -0.61% [-18.26%, 18.15%] | $64.39 |
| series | international=0 | 2112 | 2108 | 0.0485 | 8.48% [4.43%, 13.00%] | $8758.73 | 175.175× | 82.45% | $249.12 | 1296 (816 unfilled) | 6.27% [0.59%, 12.08%] | $613.99 |
| map | all | 1806 | 1131 | 0.0384 | 2.87% [-2.34%, 8.24%] | $677.73 | 13.555× | 80.74% | $172.03 | 524 (1282 unfilled) | -6.72% [-15.08%, 2.37%] | $6.17 |
| map | tier1 | 387 | 253 | 0.0390 | 0.81% [-11.47%, 13.38%] | $44.81 | 0.896× | 83.93% | $17.48 | 132 (255 unfilled) | -0.87% [-20.67%, 21.21%] | $44.81 |
| map | tier2 | 786 | 489 | 0.0340 | 2.21% [-5.70%, 10.29%] | $214.07 | 4.281× | 53.33% | $39.13 | 215 (571 unfilled) | -11.06% [-22.36%, 0.03%] | $14.84 |
| map | tier3 | 609 | 372 | 0.0439 | 5.31% [-2.98%, 14.29%] | $125.48 | 2.510× | 77.35% | $25.30 | 166 (443 unfilled) | -6.19% [-21.56%, 10.10%] | $25.56 |
| map | unknown | 24 | 17 | 0.0339 | -4.31% [-30.87%, 21.42%] | $49.89 | 0.998× | 11.87% | $4.49 | 11 (13 unfilled) | -0.06% [-37.68%, 33.08%] | $51.47 |
| map | international=1 | 262 | 172 | 0.0384 | 7.10% [-8.40%, 24.09%] | $127.38 | 2.548× | 52.06% | $18.53 | 97 (165 unfilled) | 8.18% [-16.74%, 34.64%] | $72.48 |
| map | international=0 | 1544 | 959 | 0.0384 | 2.15% [-3.35%, 7.96%] | $219.82 | 4.396× | 83.29% | $80.68 | 427 (1117 unfilled) | -10.11% [-18.72%, -1.32%] | $3.70 |
| series+map | all | 4103 | 2453 | 0.0434 | 5.72% [2.02%, 9.49%] | $13461.29 | 269.226× | 46.20% | $249.47 | 1974 (2129 unfilled) | 2.28% [-2.61%, 7.49%] | $306.07 |

#### Monthly breakdown

All metrics use identical linked rows within each kind/month. Unfitted blend months show —; counts include all rows.

| Kind | Month | Rows | Model log loss | Blended log loss | Kalshi log loss | Raw flat ROI (bets), unlimited Kelly final | Blended flat ROI (bets), unlimited Kelly final | Raw bets filled | Raw Flat ROI depth-capped [95% interval] | Raw Kelly depth-capped final | Blended bets filled | Blended Flat ROI depth-capped [95% interval] | Blended Kelly depth-capped final |
|---|---|---:|---:|---:|---:|---|---|---:|---|---:|---:|---|---:|
| map | 2026-01 | 61 | 0.621963 | — | 0.634669 | 3.98% (41), $57.25 | — | 5 (36 unfilled) | 11.19% [-66.65%, 89.92%] | $50.93 | — | — | — |
| map | 2026-02 | 92 | 0.622449 | — | 0.604939 | -7.66% (52), $39.96 | — | 16 (36 unfilled) | -59.39% [-100.00%, -17.67%] | $28.02 | — | — | — |
| map | 2026-03 | 132 | 0.656938 | 0.652193 | 0.650213 | 1.48% (72), $47.17 | -7.78% (61), $34.67 | 37 (35 unfilled) | 3.54% [-37.77%, 45.24%] | $42.95 | 30 (31 unfilled) | -4.61% [-38.87%, 33.25%] | $33.74 |
| map | 2026-04 | 247 | 0.624389 | 0.629977 | 0.654704 | 26.29% (140), $318.34 | 51.23% (82), $535.00 | 48 (92 unfilled) | -3.68% [-33.66%, 26.48%] | $30.39 | 24 (58 unfilled) | 1.75% [-31.65%, 38.12%] | $53.72 |
| map | 2026-05 | 402 | 0.647009 | 0.637552 | 0.640045 | -3.19% (247), $47.29 | 3.00% (244), $90.14 | 83 (164 unfilled) | 0.71% [-24.98%, 25.28%] | $41.45 | 95 (149 unfilled) | 1.29% [-18.19%, 20.79%] | $51.08 |
| map | 2026-06 | 374 | 0.643495 | 0.640900 | 0.651611 | -2.31% (233), $60.96 | 7.92% (200), $86.23 | 44 (189 unfilled) | -7.26% [-38.96%, 25.42%] | $49.48 | 41 (159 unfilled) | 7.36% [-21.04%, 36.64%] | $53.23 |
| map | 2026-07 | 581 | 0.654397 | 0.649858 | 0.640757 | -7.13% (375), $8.18 | -5.11% (333), $12.68 | 91 (284 unfilled) | -22.81% [-41.28%, -3.34%] | $16.27 | 74 (259 unfilled) | -16.74% [-35.50%, 2.90%] | $25.81 |
| map | 2026-08 | 801 | 0.621471 | 0.614855 | 0.625646 | -1.70% (561), $17.49 | 6.88% (352), $208.65 | 104 (457 unfilled) | -13.55% [-35.68%, 9.69%] | $32.04 | 66 (286 unfilled) | -2.32% [-26.08%, 24.00%] | $47.14 |
| map | 2026-09 | 807 | 0.659957 | 0.648070 | 0.642565 | -10.88% (545), $0.31 | -7.32% (348), $18.71 | 190 (355 unfilled) | -15.72% [-32.89%, 2.89%] | $3.06 | 134 (214 unfilled) | -15.07% [-33.29%, 4.23%] | $37.15 |
| map | 2026-10 | 590 | 0.640973 | 0.625557 | 0.626949 | -13.41% (356), $1.51 | 5.14% (186), $50.27 | 141 (215 unfilled) | -26.11% [-42.74%, -8.94%] | $5.86 | 60 (126 unfilled) | -7.27% [-29.77%, 14.91%] | $28.79 |
| series | 2026-01 | 49 | 0.565518 | — | 0.590419 | 11.62% (36), $68.67 | — | 29 (7 unfilled) | 39.11% [-11.77%, 90.87%] | $86.06 | — | — | — |
| series | 2026-02 | 144 | 0.588324 | — | 0.567099 | -13.74% (102), $9.05 | — | 91 (11 unfilled) | -16.78% [-37.63%, 5.73%] | $8.15 | — | — | — |
| series | 2026-03 | 286 | 0.583633 | 0.571325 | 0.589357 | 1.40% (205), $24.48 | 10.83% (176), $196.94 | 156 (49 unfilled) | 2.75% [-15.69%, 23.03%] | $40.80 | 134 (42 unfilled) | 5.49% [-7.57%, 17.82%] | $117.85 |
| series | 2026-04 | 302 | 0.575226 | 0.560668 | 0.578002 | 6.85% (225), $23.84 | 10.22% (203), $257.92 | 167 (58 unfilled) | 8.53% [-11.01%, 29.58%] | $69.38 | 148 (55 unfilled) | 14.17% [-2.80%, 32.74%] | $135.76 |
| series | 2026-05 | 325 | 0.616610 | 0.596993 | 0.595148 | -7.19% (232), $4.50 | 0.94% (209), $33.80 | 190 (42 unfilled) | -7.81% [-25.26%, 10.34%] | $5.36 | 168 (41 unfilled) | -1.36% [-15.68%, 13.33%] | $28.53 |
| series | 2026-06 | 320 | 0.621179 | 0.622716 | 0.634132 | 5.43% (242), $121.62 | 9.73% (186), $153.46 | 156 (86 unfilled) | 15.78% [-4.36%, 36.79%] | $273.51 | 126 (60 unfilled) | 15.74% [1.07%, 30.77%] | $103.85 |
| series | 2026-07 | 481 | 0.627515 | 0.613729 | 0.616051 | -0.24% (363), $3.94 | 1.50% (294), $17.50 | 229 (134 unfilled) | 0.09% [-17.63%, 19.63%] | $20.89 | 187 (107 unfilled) | -0.88% [-17.88%, 18.95%] | $17.33 |
| series | 2026-08 | 658 | 0.609026 | 0.600098 | 0.615564 | 4.84% (514), $5.61 | 6.52% (399), $213.54 | 257 (257 unfilled) | -0.53% [-16.34%, 17.18%] | $35.62 | 201 (198 unfilled) | 12.08% [-4.44%, 31.25%] | $248.79 |
| series | 2026-09 | 852 | 0.596346 | 0.584865 | 0.601766 | 2.75% (647), $3.39 | 13.29% (459), $1353.50 | 361 (286 unfilled) | -3.11% [-14.35%, 8.69%] | $4.99 | 267 (192 unfilled) | 2.38% [-9.15%, 14.24%] | $146.15 |
| series | 2026-10 | 719 | 0.589114 | 0.575405 | 0.585415 | 2.71% (516), $13.02 | 8.56% (371), $135.35 | 313 (203 unfilled) | 2.01% [-10.33%, 14.75%] | $28.52 | 219 (152 unfilled) | 2.50% [-9.05%, 13.99%] | $58.85 |

### player_round_glicko_rookie_weights+none: Kalshi comparison and returns

none

#### Log loss vs Kalshi

| Kind | Slice | Rows | Model log loss | Kalshi log loss | Difference [95% interval] | Significant |
|---|---|---:|---:|---:|---|---|
| series | all | 4136 | 0.596691 | 0.600829 | -0.004138 [-0.012401, 0.003726] | no |
| series | tier1 | 685 | 0.626057 | 0.614585 | 0.011472 [-0.006225, 0.029063] | no |
| series | tier2 | 1814 | 0.595583 | 0.590902 | 0.004681 [-0.005031, 0.015412] | no |
| series | tier3 | 1595 | 0.588161 | 0.609630 | -0.021469 [-0.035923, -0.005557] | yes |
| series | unknown | 42 | 0.489524 | 0.471027 | 0.018496 [-0.044515, 0.081152] | no |
| series | international=1 | 436 | 0.607866 | 0.592747 | 0.015119 [-0.007863, 0.037779] | no |
| series | international=0 | 3700 | 0.595374 | 0.601782 | -0.006407 [-0.015490, 0.002170] | no |
| map | all | 4087 | 0.640554 | 0.637334 | 0.003221 [-0.002813, 0.009571] | no |
| map | tier1 | 1117 | 0.654267 | 0.643855 | 0.010412 [-0.001876, 0.021884] | no |
| map | tier2 | 1772 | 0.638122 | 0.636583 | 0.001539 [-0.007717, 0.010212] | no |
| map | tier3 | 1144 | 0.633642 | 0.635738 | -0.002096 [-0.015536, 0.011545] | no |
| map | unknown | 54 | 0.583152 | 0.560856 | 0.022296 [-0.012112, 0.058557] | no |
| map | international=1 | 765 | 0.634256 | 0.630727 | 0.003529 [-0.010226, 0.017042] | no |
| map | international=0 | 3322 | 0.642005 | 0.638855 | 0.003150 [-0.003900, 0.009977] | no |

#### Full-Kelly returns

| Kind | Slice | Bets | Matches | Mean edge | Flat ROI [95% interval] | Kelly, LoL caps ($50 start) | Multiple | Max drawdown | Largest stake | Bets filled | Flat ROI depth-capped [95% interval] | Kelly depth-capped final |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---:|
| series | all | 3079 | 3074 | 0.0820 | 2.94% [-1.41%, 7.55%] | $0.03 | 0.001× | 99.98% | $11.82 | 1951 (1128 unfilled) | 1.04% [-4.44%, 6.59%] | $2.70 |
| series | tier1 | 518 | 518 | 0.0716 | -1.70% [-12.64%, 10.44%] | $1.92 | 0.038× | 99.37% | $15.61 | 423 (95 unfilled) | -4.95% [-16.73%, 7.65%] | $1.32 |
| series | tier2 | 1291 | 1288 | 0.0719 | -1.84% [-8.63%, 4.90%] | $0.06 | 0.001× | 99.93% | $8.50 | 808 (483 unfilled) | -3.56% [-11.69%, 4.56%] | $0.64 |
| series | tier3 | 1237 | 1235 | 0.0969 | 10.44% [3.37%, 18.37%] | $8440.17 | 168.803× | 92.11% | $249.12 | 697 (540 unfilled) | 10.46% [1.00%, 20.32%] | $283.66 |
| series | unknown | 33 | 33 | 0.0792 | -18.11% [-48.56%, 16.00%] | $40.36 | 0.807× | 32.95% | $5.78 | 23 (10 unfilled) | -11.86% [-49.11%, 31.13%] | $40.78 |
| series | international=1 | 324 | 324 | 0.0727 | -2.81% [-16.95%, 13.25%] | $2.49 | 0.050× | 99.18% | $13.49 | 282 (42 unfilled) | -7.49% [-22.51%, 7.83%] | $1.29 |
| series | international=0 | 2755 | 2750 | 0.0830 | 3.62% [-1.16%, 8.28%] | $0.10 | 0.002× | 99.85% | $6.01 | 1669 (1086 unfilled) | 2.48% [-3.56%, 8.33%] | $21.14 |
| map | all | 2593 | 1663 | 0.0586 | -3.33% [-7.83%, 1.36%] | $0.07 | 0.001× | 99.99% | $104.25 | 759 (1834 unfilled) | -15.74% [-23.51%, -8.08%] | $0.10 |
| map | tier1 | 709 | 485 | 0.0578 | -3.98% [-13.36%, 5.77%] | $10.65 | 0.213× | 93.96% | $15.53 | 229 (480 unfilled) | -4.69% [-20.33%, 11.45%] | $11.51 |
| map | tier2 | 1087 | 684 | 0.0524 | -1.62% [-8.63%, 5.72%] | $3.35 | 0.067× | 99.16% | $34.58 | 302 (785 unfilled) | -17.24% [-28.86%, -6.50%] | $0.33 |
| map | tier3 | 766 | 473 | 0.0684 | -4.46% [-12.61%, 3.81%] | $6.61 | 0.132× | 98.51% | $16.62 | 217 (549 unfilled) | -25.27% [-39.77%, -10.50%] | $2.78 |
| map | unknown | 31 | 21 | 0.0478 | -20.77% [-51.14%, 6.53%] | $35.77 | 0.715× | 32.85% | $4.78 | 11 (20 unfilled) | -16.99% [-56.80%, 17.05%] | $46.34 |
| map | international=1 | 476 | 332 | 0.0604 | -1.49% [-12.67%, 11.08%] | $40.66 | 0.813× | 83.03% | $23.46 | 164 (312 unfilled) | -1.90% [-22.05%, 18.01%] | $30.92 |
| map | international=0 | 2117 | 1331 | 0.0582 | -3.75% [-8.70%, 1.42%] | $0.09 | 0.002× | 99.98% | $37.95 | 595 (1522 unfilled) | -19.56% [-27.89%, -10.80%] | $0.08 |
| series+map | all | 5672 | 3350 | 0.0713 | 0.07% [-3.63%, 3.63%] | $0.06 | 0.001× | 99.97% | $23.79 | 2710 (2962 unfilled) | -3.66% [-8.59%, 1.20%] | $0.52 |

#### Monthly market blend fits

UTC monthly fits use earlier rows of the same kind from 2026-01-01, excluding holdout; minimum 100 rows. logit(p_blend) = a·logit(mid) + b·(logit(p_model) − logit(mid)); inputs clipped to [0.01, 0.99], no intercept, ridge 1e-6. Unfitted rows use mid unchanged; excluded from blended tables: 346 rows. Rating parameters remain selected on the tuning window.

| Month | Kind | n | a | b | Status |
|---|---|---:|---:|---:|---|
| 2026-01 | series | 0 | 1.000000 | 0.000000 | unfitted |
| 2026-01 | map | 0 | 1.000000 | 0.000000 | unfitted |
| 2026-02 | series | 49 | 1.000000 | 0.000000 | unfitted |
| 2026-02 | map | 61 | 1.000000 | 0.000000 | unfitted |
| 2026-03 | series | 193 | 1.406407 | 0.731095 | fitted |
| 2026-03 | map | 153 | 1.368760 | 0.660826 | fitted |
| 2026-04 | series | 479 | 1.387467 | 0.779522 | fitted |
| 2026-04 | map | 285 | 1.230334 | 0.531121 | fitted |
| 2026-05 | series | 781 | 1.378588 | 0.822527 | fitted |
| 2026-05 | map | 532 | 1.318432 | 0.947318 | fitted |
| 2026-06 | series | 1106 | 1.338913 | 0.664647 | fitted |
| 2026-06 | map | 934 | 1.326614 | 0.806518 | fitted |
| 2026-07 | series | 1426 | 1.282138 | 0.680090 | fitted |
| 2026-07 | map | 1308 | 1.316554 | 0.834904 | fitted |
| 2026-08 | series | 1907 | 1.235665 | 0.609197 | fitted |
| 2026-08 | map | 1889 | 1.186296 | 0.588510 | fitted |
| 2026-09 | series | 2565 | 1.228918 | 0.634981 | fitted |
| 2026-09 | map | 2690 | 1.239979 | 0.648329 | fitted |
| 2026-10 | series | 3417 | 1.238231 | 0.665701 | fitted |
| 2026-10 | map | 3497 | 1.188353 | 0.532750 | fitted |

#### Log loss vs Kalshi (blended)

| Kind | Slice | Rows | Model log loss | Kalshi log loss | Difference [95% interval] | Significant |
|---|---|---:|---:|---:|---|---|
| series | all | 3943 | 0.587655 | 0.602190 | -0.014536 [-0.020164, -0.008951] | yes |
| series | tier1 | 578 | 0.616594 | 0.615317 | 0.001277 [-0.011338, 0.013676] | no |
| series | tier2 | 1733 | 0.583288 | 0.593744 | -0.010456 [-0.017575, -0.002919] | yes |
| series | tier3 | 1590 | 0.585622 | 0.610089 | -0.024468 [-0.034437, -0.013939] | yes |
| series | unknown | 42 | 0.446549 | 0.471027 | -0.024479 [-0.056573, 0.008386] | no |
| series | international=1 | 359 | 0.594235 | 0.591638 | 0.002596 [-0.010965, 0.017068] | no |
| series | international=0 | 3584 | 0.586996 | 0.603247 | -0.016252 [-0.022273, -0.010515] | yes |
| map | all | 3934 | 0.634355 | 0.638132 | -0.003778 [-0.008139, 0.000379] | no |
| map | tier1 | 990 | 0.653116 | 0.647070 | 0.006046 [-0.001767, 0.014354] | no |
| map | tier2 | 1748 | 0.629894 | 0.636671 | -0.006777 [-0.012471, -0.001238] | yes |
| map | tier3 | 1142 | 0.628721 | 0.636276 | -0.007556 [-0.017875, 0.002452] | no |
| map | unknown | 54 | 0.553960 | 0.560856 | -0.006897 [-0.030375, 0.016520] | no |
| map | international=1 | 665 | 0.627865 | 0.630639 | -0.002774 [-0.011220, 0.005863] | no |
| map | international=0 | 3269 | 0.635675 | 0.639657 | -0.003982 [-0.009060, 0.000925] | no |

#### Full-Kelly returns (blended)

| Kind | Slice | Bets | Matches | Mean edge | Flat ROI [95% interval] | Kelly, LoL caps ($50 start) | Multiple | Max drawdown | Largest stake | Bets filled | Flat ROI depth-capped [95% interval] | Kelly depth-capped final |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---:|
| series | all | 2394 | 2390 | 0.0499 | 8.97% [4.81%, 13.25%] | $9338.30 | 186.766× | 68.31% | $249.12 | 1503 (891 unfilled) | 5.92% [0.91%, 11.17%] | $793.67 |
| series | tier1 | 318 | 318 | 0.0389 | -2.96% [-13.62%, 8.37%] | $19.87 | 0.397× | 88.42% | $12.26 | 251 (67 unfilled) | -6.15% [-18.57%, 5.35%] | $23.97 |
| series | tier2 | 1022 | 1020 | 0.0435 | 7.52% [2.08%, 13.17%] | $4071.46 | 81.429× | 48.42% | $249.47 | 628 (394 unfilled) | 3.67% [-3.17%, 11.18%] | $86.84 |
| series | tier3 | 1025 | 1023 | 0.0599 | 14.41% [7.88%, 21.24%] | $12868.04 | 257.361× | 61.63% | $249.12 | 605 (420 unfilled) | 13.63% [5.06%, 22.80%] | $1413.82 |
| series | unknown | 29 | 29 | 0.0463 | -1.03% [-28.26%, 25.33%] | $65.42 | 1.308× | 10.01% | $6.55 | 19 (10 unfilled) | -5.59% [-41.97%, 36.05%] | $55.83 |
| series | international=1 | 195 | 195 | 0.0349 | -4.68% [-19.64%, 11.79%] | $51.36 | 1.027× | 68.05% | $12.23 | 163 (32 unfilled) | -6.82% [-22.71%, 10.42%] | $60.48 |
| series | international=0 | 2199 | 2195 | 0.0513 | 10.18% [5.86%, 14.34%] | $14085.50 | 281.710× | 74.39% | $249.12 | 1340 (859 unfilled) | 7.47% [2.48%, 13.24%] | $689.28 |
| map | all | 1817 | 1141 | 0.0383 | 4.31% [-0.91%, 9.47%] | $2453.59 | 49.072× | 81.30% | $248.43 | 514 (1303 unfilled) | -8.46% [-16.05%, -0.01%] | $8.63 |
| map | tier1 | 391 | 259 | 0.0390 | 0.36% [-9.98%, 11.78%] | $34.13 | 0.683× | 85.14% | $17.11 | 127 (264 unfilled) | -6.72% [-23.02%, 10.90%] | $35.48 |
| map | tier2 | 777 | 486 | 0.0334 | 4.89% [-2.57%, 13.37%] | $349.57 | 6.991× | 49.90% | $69.04 | 206 (571 unfilled) | -10.49% [-21.90%, 0.77%] | $22.11 |
| map | tier3 | 626 | 380 | 0.0441 | 6.22% [-1.85%, 14.52%] | $279.09 | 5.582× | 69.32% | $32.84 | 170 (456 unfilled) | -7.83% [-22.53%, 7.93%] | $23.53 |
| map | unknown | 23 | 16 | 0.0333 | -0.07% [-27.68%, 27.11%] | $52.52 | 1.050× | 10.46% | $4.67 | 11 (12 unfilled) | -0.06% [-37.68%, 33.08%] | $54.12 |
| map | international=1 | 262 | 176 | 0.0373 | 5.81% [-8.05%, 21.04%] | $107.23 | 2.145× | 55.45% | $17.15 | 95 (167 unfilled) | 0.91% [-17.94%, 20.73%] | $56.77 |
| map | international=0 | 1555 | 965 | 0.0384 | 4.06% [-1.32%, 9.55%] | $618.25 | 12.365× | 80.55% | $114.74 | 419 (1136 unfilled) | -10.58% [-19.64%, -1.97%] | $6.85 |
| series+map | all | 4211 | 2532 | 0.0449 | 6.96% [3.41%, 10.58%] | $17702.91 | 354.058× | 45.86% | $249.47 | 2017 (2194 unfilled) | 2.25% [-2.55%, 7.14%] | $356.51 |

#### Monthly breakdown

All metrics use identical linked rows within each kind/month. Unfitted blend months show —; counts include all rows.

| Kind | Month | Rows | Model log loss | Blended log loss | Kalshi log loss | Raw flat ROI (bets), unlimited Kelly final | Blended flat ROI (bets), unlimited Kelly final | Raw bets filled | Raw Flat ROI depth-capped [95% interval] | Raw Kelly depth-capped final | Blended bets filled | Blended Flat ROI depth-capped [95% interval] | Blended Kelly depth-capped final |
|---|---|---:|---:|---:|---:|---|---|---:|---|---:|---:|---|---:|
| map | 2026-01 | 61 | 0.618405 | — | 0.634669 | 7.20% (42), $67.32 | — | 5 (37 unfilled) | 11.19% [-66.65%, 89.92%] | $50.38 | — | — | — |
| map | 2026-02 | 92 | 0.625348 | — | 0.604939 | -17.16% (53), $36.50 | — | 17 (36 unfilled) | -70.79% [-100.00%, -33.71%] | $26.53 | — | — | — |
| map | 2026-03 | 132 | 0.656094 | 0.651030 | 0.650213 | -3.86% (73), $36.23 | -16.43% (52), $39.15 | 33 (40 unfilled) | 8.67% [-36.12%, 54.57%] | $40.08 | 24 (28 unfilled) | -21.25% [-51.62%, 6.58%] | $38.63 |
| map | 2026-04 | 247 | 0.623312 | 0.628698 | 0.654704 | 25.60% (143), $405.26 | 50.71% (80), $504.14 | 52 (91 unfilled) | 2.48% [-26.46%, 32.73%] | $33.58 | 24 (56 unfilled) | -6.89% [-37.53%, 21.75%] | $50.67 |
| map | 2026-05 | 402 | 0.644816 | 0.635874 | 0.640045 | 1.30% (250), $71.18 | 4.64% (230), $83.96 | 90 (160 unfilled) | -3.53% [-25.63%, 18.61%] | $38.51 | 91 (139 unfilled) | 2.38% [-18.12%, 22.37%] | $57.08 |
| map | 2026-06 | 374 | 0.639831 | 0.638208 | 0.651611 | 4.28% (209), $102.34 | 10.00% (185), $124.97 | 44 (165 unfilled) | -10.63% [-42.05%, 22.87%] | $44.30 | 38 (147 unfilled) | 3.22% [-27.86%, 34.55%] | $56.75 |
| map | 2026-07 | 581 | 0.654599 | 0.650912 | 0.640757 | -5.87% (368), $10.09 | -4.43% (337), $13.74 | 82 (286 unfilled) | -18.28% [-38.72%, 1.75%] | $20.69 | 74 (263 unfilled) | -10.69% [-28.88%, 8.90%] | $32.13 |
| map | 2026-08 | 801 | 0.620303 | 0.613822 | 0.625646 | 0.10% (550), $42.19 | 11.86% (370), $267.23 | 106 (444 unfilled) | -10.81% [-32.85%, 10.27%] | $32.01 | 69 (301 unfilled) | 9.78% [-15.31%, 37.01%] | $57.79 |
| map | 2026-09 | 807 | 0.657411 | 0.647443 | 0.642565 | -11.87% (547), $0.42 | -6.23% (374), $21.94 | 187 (360 unfilled) | -21.27% [-37.24%, -2.58%] | $1.24 | 135 (239 unfilled) | -22.22% [-35.99%, -8.58%] | $21.38 |
| map | 2026-10 | 590 | 0.637118 | 0.623184 | 0.626949 | -11.27% (358), $1.04 | 6.02% (189), $56.65 | 143 (215 unfilled) | -26.61% [-43.18%, -9.69%] | $4.82 | 59 (130 unfilled) | -15.23% [-37.62%, 6.28%] | $27.82 |
| series | 2026-01 | 49 | 0.558665 | — | 0.590419 | 11.11% (38), $99.48 | — | 32 (6 unfilled) | 32.35% [-11.23%, 81.23%] | $114.65 | — | — | — |
| series | 2026-02 | 144 | 0.581998 | — | 0.567099 | -17.92% (98), $10.86 | — | 87 (11 unfilled) | -21.66% [-41.43%, 0.61%] | $10.09 | — | — | — |
| series | 2026-03 | 286 | 0.585913 | 0.573072 | 0.589357 | 2.54% (213), $21.34 | 5.44% (198), $177.19 | 168 (45 unfilled) | 3.42% [-14.46%, 20.63%] | $33.98 | 153 (45 unfilled) | 1.47% [-11.52%, 14.00%] | $99.70 |
| series | 2026-04 | 302 | 0.570618 | 0.558752 | 0.578002 | 7.60% (223), $70.93 | 12.33% (198), $169.72 | 161 (62 unfilled) | 10.30% [-9.36%, 31.16%] | $95.04 | 144 (54 unfilled) | 14.87% [-1.38%, 33.54%] | $112.17 |
| series | 2026-05 | 325 | 0.617296 | 0.597884 | 0.595148 | -3.48% (246), $6.01 | -1.70% (215), $40.72 | 199 (47 unfilled) | -6.89% [-23.18%, 9.57%] | $2.77 | 167 (48 unfilled) | -6.85% [-21.30%, 6.97%] | $25.12 |
| series | 2026-06 | 320 | 0.617418 | 0.619845 | 0.634132 | 10.63% (232), $206.46 | 10.55% (181), $225.77 | 157 (75 unfilled) | 20.26% [0.34%, 39.94%] | $371.39 | 124 (57 unfilled) | 11.21% [-2.59%, 27.03%] | $129.81 |
| series | 2026-07 | 481 | 0.618417 | 0.607702 | 0.616051 | 1.10% (363), $5.91 | 4.01% (308), $31.69 | 226 (137 unfilled) | 4.31% [-12.83%, 22.67%] | $36.03 | 198 (110 unfilled) | 0.63% [-15.85%, 19.36%] | $22.26 |
| series | 2026-08 | 658 | 0.603621 | 0.595359 | 0.615564 | 6.42% (524), $59.01 | 11.11% (415), $293.03 | 264 (260 unfilled) | 4.66% [-11.06%, 21.25%] | $75.45 | 206 (209 unfilled) | 16.81% [0.86%, 35.25%] | $256.27 |
| series | 2026-09 | 852 | 0.590209 | 0.581454 | 0.601766 | 5.23% (647), $13.43 | 15.52% (485), $3029.78 | 357 (290 unfilled) | -6.41% [-17.91%, 5.13%] | $5.32 | 284 (201 unfilled) | 6.72% [-3.42%, 17.46%] | $222.71 |
| series | 2026-10 | 719 | 0.585729 | 0.573530 | 0.585415 | -1.26% (495), $21.05 | 7.71% (394), $151.73 | 300 (195 unfilled) | -3.63% [-16.08%, 10.31%] | $26.36 | 227 (167 unfilled) | 3.45% [-7.70%, 14.29%] | $51.04 |
