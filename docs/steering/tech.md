# Tech

## Stack

Python ≥ 3.12 with uv; SQLite rebuilt from raw caches; raw SQL; Typer CLI (`promcs`); ruff; pytest (offline, fixtures in `tests/fixtures/`).

## Layout

| Path | Purpose |
|---|---|
| `promcs/main.py` | CLI entry; mounts `kalshi` and `liquipedia` |
| `promcs/kalshi/api.py` | Public HTTP client, pacing, retries and pagination |
| `promcs/kalshi/collect.py` | Raw catalog, trade, candle and book files |
| `promcs/liquipedia/` | Rate-limited API queries, incremental raw cache and CLI |
| `promcs/liquipedia/parse.py` | Pure balanced-template, infobox, match/map and roster parser (version 1) |
| `promcs/liquipedia/regions.py` | Tournament host country → macro region |
| `scripts/001_create_tables.sql` | SQLite schema and indexes |
| `scripts/002_load_liquipedia.py` | Offline cache loader, inheritance and deduplication |
| `scripts/setup_db.sh` | Rebuild `db/cs2.db` from raw cache |
| `tests/test_liquipedia_parse.py`, `tests/test_liquipedia_db.py` | Offline fixture parser and DB checks |
| `tests/test_liquipedia_crawl.py` | Offline crawler, HTTP, cache and CLI tests |
| `promcs/kalshi/cli.py` | Collector, manifest and book-loop commands |
| `scripts/kalshi_data.sh` | S3 pull/push helper |
| `.github/workflows/ci.yml`, `kalshi-collect.yml` | CI and scheduled Kalshi collection |
| `.githooks/pre-commit`, `scripts/work_log.py` | Work-log rotation and tooling |
| `tests/test_kalshi_collect.py` | Offline fixture-based collector and CLI tests |
| `tests/test_workflows.py`, `tests/test_steering.py` | Workflow and document guards |
| `tests/fixtures/kalshi/` | Saved Kalshi API responses |

## Kalshi collector

`promcs kalshi collect [--no-books] [--limit N]` refreshes `KXCS2GAME` and `KXCS2MAP`, saves final-market histories and snapshots active books. `--limit` caps new trade/candle fetches combined. `promcs kalshi books --every 60 --minutes 60` refreshes active tickers each pass. Data root is `PROMCS_DATA` (default `data/`); files live under `kalshi/`. GitHub Actions is intended to collect every six hours (see Deployment).

## Liquipedia crawler

`promcs liquipedia crawl [--limit N] [--full]` uses only `action=query` at `https://liquipedia.net/counterstrike/api.php`, with gzip, a 2.2-second request interval and retry backoff. The User-Agent carries the owner's email (`http.CONTACT`); `LIQUIPEDIA_CONTACT` overrides it. Category members and revisions are refreshed; content is fetched only for new or changed revision IDs unless `--full` is set. `--limit` caps content titles per run. Tab `linkN` parameters discover pages under the same tournament root, through three rounds.

Under `PROMCS_DATA` (default `data/`), `liquipedia/pages/<sha1-prefix>/<sha1>.json.gz` stores unparsed wikitext and revision metadata; `index.json` tracks revisions, sources and parents, atomically saved after each batch. `category/*.json` stores the latest title lists. `promcs liquipedia status` reports cache counts and newest fetch time. Content credit: Liquipedia contributors, CC BY-SA 3.0. No HTML scraping.

## Database

`uv run bash scripts/setup_db.sh` rebuilds `db/cs2.db` offline from the cache (`PROMCS_DATA` supported). The loader accepts `--db`; errors go beside the DB in `parse_errors.txt`. Tables: `events`, `teams`, `players`, `matches`, `maps`, `rosters`, `player_maps`. SQL foreign keys are enabled.

Event IDs are page IDs. Team/player IDs are the first 12 SHA-1 hex digits of `team:<key>` / `player:<key>`. Match IDs hash `hltv:<id>` when available, otherwise `match:<page>|<team1>|<team2>|<UTC ISO with Z>|<ordinal>`. Map IDs are match ID × 10 + order (1–9). Duplicate IDs or unordered team pairs with the same timestamp and sorted, team-oriented map scores keep the first page-title occurrence.

Missing infobox fields inherit independently from the nearest cached ancestor. S/A tiers map to tier1, B to tier2, C/D to tier3; absent tiers are unknown. International means S tier or World/International/Global/Americas country. Showmatches and non-team modes are excluded. Online means type exactly Online.

Rosters use five-player TeamCards or Opponent/Persons, excluding non-player roles. Matches use the nearest ancestor with any cards. Folded alphanumeric team names match exactly, then by unique containment with both strings at least three characters. Roster rows belong to the supplying event. Team display names use the most frequent matched card; players on both sides are omitted from that map.

Maps require unequal parsed scores, maximum ≥13, and finished neither skip nor false. Regulation sides and overtime totals are retained. Dates convert listed zones to UTC; missing times use noon UTC. Unknown zones use UTC with time_known=0 and are counted; dateless matches are skipped and counted.

## Model change rules

No benchmark is ported yet. Do not tune or select on holdout. Stage 1 tunes on outcomes only, 2024-01-01 to 2026-01-01. Stage 2 freezes parameters and validates outcomes and Kalshi's tradeable quote, 2026-01-01 to 2026-11-01. Holdout is 2026-11-01 on, opened once. Tradeable quote: first hourly bid/ask at least 30 minutes after listing and at least 2 hours before start, spread ≤ 0.06. Use paired match-clustered intervals; require significant stage-1 gain and no stage-2 regression, including guarded sections: all, tier1, tier2, tier3, international. Benchmark command (planned, not ported): `scripts/evaluate_elo.py`.

- An added parameter, feature or layer also needs a stage-1 gain of at least 0.0005 log loss.
- A stage-2 gain is reported but never rescues a change that failed stage 1; don't tune on stage 2 to pass it.
- Removals ship when every guarded section's interval stays below +0.0005 on both stages (non-inferior).
- Every test goes in the [research ledger](../research/README.md), adopted or not, with its numbers; count the tests run against stage 2.
- Trading results are reported, not gates. Data fixes (a link, alias, tier, parser bug) are not model changes: they ship when correct and the benchmark doesn't get significantly worse.

## Ratings and benchmark

Planned port from valorant-model: `team_elo` and `player_round_glicko`, chronological replay, stage-separated scoring, market comparison and clustered intervals. Keep feature histories causal and select parameters using stage 1 only. Run `scripts/evaluate_elo.py` when ported; report results and every model idea in the research ledger.
