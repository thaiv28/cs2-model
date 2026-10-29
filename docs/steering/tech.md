# Tech

## Stack

Python ≥ 3.12 with uv; SQLite rebuilt from raw caches; raw SQL; Typer CLI (`promcs`); ruff; pytest (offline, fixtures in `tests/fixtures/`).

## Layout

| Path | Purpose |
|---|---|
| `promcs/main.py` | CLI entry; mounts `kalshi` (Liquipedia group planned) |
| `promcs/kalshi/api.py` | Public HTTP client, pacing, retries and pagination |
| `promcs/kalshi/collect.py` | Raw catalog, trade, candle and book files |
| `promcs/kalshi/cli.py` | Collector, manifest and book-loop commands |
| `scripts/kalshi_data.sh` | S3 pull/push helper |
| `.github/workflows/ci.yml`, `kalshi-collect.yml` | CI and scheduled Kalshi collection |
| `.githooks/pre-commit`, `scripts/work_log.py` | Work-log rotation and tooling |
| `tests/test_kalshi_collect.py` | Offline fixture-based collector and CLI tests |
| `tests/test_workflows.py`, `tests/test_steering.py` | Workflow and document guards |
| `tests/fixtures/kalshi/` | Saved Kalshi API responses |

## Kalshi collector

`promcs kalshi collect [--no-books] [--limit N]` refreshes `KXCS2GAME` and `KXCS2MAP`, saves final-market histories and snapshots active books. `--limit` caps new trade/candle fetches combined. `promcs kalshi books --every 60 --minutes 60` refreshes active tickers each pass. Data root is `PROMCS_DATA` (default `data/`); files live under `kalshi/`. GitHub Actions is intended to collect every six hours (see Deployment).

## Model change rules

No benchmark is ported yet. Do not tune or select on holdout. Stage 1 tunes on outcomes only, 2024-01-01 to 2026-01-01. Stage 2 freezes parameters and validates outcomes and Kalshi's tradeable quote, 2026-01-01 to 2026-11-01. Holdout is 2026-11-01 on, opened once. Tradeable quote: first hourly bid/ask at least 30 minutes after listing and at least 2 hours before start, spread ≤ 0.06. Use paired match-clustered intervals; require significant stage-1 gain and no stage-2 regression, including guarded sections: all, tier1, tier2, tier3, international. Benchmark command (planned, not ported): `scripts/evaluate_elo.py`.

- An added parameter, feature or layer also needs a stage-1 gain of at least 0.0005 log loss.
- A stage-2 gain is reported but never rescues a change that failed stage 1; don't tune on stage 2 to pass it.
- Removals ship when every guarded section's interval stays below +0.0005 on both stages (non-inferior).
- Every test goes in the [research ledger](../research/README.md), adopted or not, with its numbers; count the tests run against stage 2.
- Trading results are reported, not gates. Data fixes (a link, alias, tier, parser bug) are not model changes: they ship when correct and the benchmark doesn't get significantly worse.

## Ratings and benchmark

Planned port from valorant-model: `team_elo` and `player_round_glicko`, chronological replay, stage-separated scoring, market comparison and clustered intervals. Keep feature histories causal and select parameters using stage 1 only. Run `scripts/evaluate_elo.py` when ported; report results and every model idea in the research ledger.
