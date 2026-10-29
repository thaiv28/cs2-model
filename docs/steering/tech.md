# Tech

## Stack

Python ≥ 3.12 with uv; SQLite rebuilt from raw caches; raw SQL; Typer CLI (`promcs`); ruff; pytest (offline, fixtures in `tests/fixtures/`).

## Layout

| Path | Purpose |
|---|---|
| `promcs/main.py` | CLI entry; mounts `kalshi`, `liquipedia`, `feed-state` and `export` |
| `promcs/kalshi/api.py` | Public HTTP client, pacing, retries and pagination |
| `promcs/kalshi/collect.py` | Raw catalog, trade, candle and book files |
| `promcs/liquipedia/` | Rate-limited API queries, incremental raw cache and CLI |
| `promcs/liquipedia/parse.py` | Pure balanced-template, infobox, match/map and roster parser (version 1) |
| `promcs/liquipedia/regions.py` | Tournament host country → macro region |
| `promcs/feed.py`, `promcs/quotes.py` | Site feed orchestration, frozen calls and shared candle rules |
| `promcs/ratings/elo_weights.json` | Existing stage-1 fit and string-keyed series temperatures |
| `tests/test_feed.py` | Offline feed, schedule, freeze, join and market checks |
| `promcs/ratings/` | Team/player Elo, round conversion, chronological replay, regional layers |
| `promcs/evaluation.py`, `backtest.py`, `blend.py` | Scoring, match bootstrap, execution simulation, causal market blend |
| `scripts/evaluate_elo.py`, `series_independence.py` | Two-stage benchmark and series diagnostics |
| `tests/test_elo.py`, `test_elo_variants.py`, `test_evaluation.py`, `test_backtest.py`, `test_layers.py` | Synthetic CS2 ratings, layers, quotes and report checks |
| `scripts/001_create_tables.sql` | SQLite schema and indexes |
| `scripts/002_load_liquipedia.py` | Offline cache loader, inheritance and deduplication |
| `promcs/link.py` | Pure catalog parsing, team matching, aliases and settlement checks |
| `scripts/003_load_kalshi.py` | Offline Kalshi catalog loader |
| `scripts/004_link_kalshi.py` | Liquipedia linking and real-data report |
| `tests/test_link.py` | Offline linking and catalog-to-DB checks |
| `scripts/setup_db.sh` | Rebuild `db/cs2.db` from raw cache |
| `tests/test_liquipedia_parse.py`, `tests/test_liquipedia_db.py` | Offline fixture parser and DB checks |
| `tests/test_liquipedia_crawl.py` | Offline crawler, HTTP, cache and CLI tests |
| `promcs/kalshi/cli.py` | Collector, manifest and book-loop commands |
| `scripts/kalshi_data.sh`, `feed_data.sh` | S3 archives and conditional prediction-log persistence |
| `.github/workflows/ci.yml`, `kalshi-collect.yml` | CI and scheduled Kalshi collection |
| `.github/workflows/refresh-db.yml`, `feed.yml` | Hourly ratings snapshot and frequent DB-free site feed |
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

`uv run bash scripts/setup_db.sh` rebuilds `db/cs2.db` offline from the cache (`PROMCS_DATA` supported). The loader accepts `--db`; errors go beside the DB in `parse_errors.txt`. Tables: `events`, `teams`, `players`, `matches`, `maps`, `rosters`, `player_maps`, `kalshi_markets`, `team_aliases`, `kalshi_links`. SQL foreign keys are enabled.

Event IDs are page IDs. Team/player IDs are the first 12 SHA-1 hex digits of `team:<key>` / `player:<key>`. Match IDs hash `hltv:<id>` when available, otherwise `match:<page>|<team1>|<team2>|<UTC ISO with Z>|<ordinal>`. Map IDs are match ID × 10 + order (1–9). Duplicate IDs or unordered team pairs with the same timestamp and sorted, team-oriented map scores keep the first page-title occurrence.

Missing infobox fields inherit independently from the nearest cached ancestor. S/A tiers map to tier1, B to tier2, C/D to tier3; absent tiers are unknown. International means S tier or World/International/Global/Americas country. Showmatches and non-team modes are excluded. Online means type exactly Online.

Rosters use five-player TeamCards or Opponent/Persons, excluding non-player roles. Matches use the nearest ancestor with any cards. Folded alphanumeric team names match exactly, then by unique containment with both strings at least three characters. Roster rows belong to the supplying event. Team display names use the most frequent matched card; players on both sides are omitted from that map.

Maps require unequal parsed scores, maximum ≥13, and finished neither skip nor false. Regulation sides and overtime totals are retained. Dates convert listed zones to UTC; missing times use noon UTC. Unknown zones use UTC with time_known=0 and are counted; dateless matches are skipped and counted.

## Kalshi ↔ Liquipedia links

The numbered rebuild loads `kalshi_markets` from `collect.data_dir()/markets/{KXCS2GAME,KXCS2MAP}.json`; missing catalogs load zero rows with a note. Rules supply EDT/EST schedules converted to UTC Z. Tournament names split at the last matchup colon. Tickers supply team codes and map numbers.

`team_aliases` maps consistent competitor IDs to Liquipedia team IDs with confident evidence counts; conflicts permanently drop aliases. `kalshi_links` stores each event's match/map, method and failure reason. Only events with `excluded=0` supply candidates.

Candidates lie within ±30 hours of schedule (fallback: open time +24 hours). Exact → alias → anchor passes repeat; a final fuzzy pass requires both similarities ≥0.8. Anchors require one confirmed team unique in the window and a plausible opponent (shared tokens, code initials/token or similarity ≥0.6). Exact opponents take precedence; ambiguity stays unresolved. Name variants union display names and template keys, including trailing parentheticals. Normalization removes accents/generic words and `gg`, equates female/women/GC, and retains `academy`. CS2 guard: `academy` is ignored in opponent plausibility overlap/similarity. `1w`/`1WIN` reaches the existing anchor threshold with a unique confirmed opponent. Map links inherit series identity, selecting played map order; absent maps are `unplayed`.

Binary settlements are cross-checked against winners. `db/link_report.txt` lists failures, anchor mappings and mismatches; reruns replace derived rows.

## Model change rules

Do not tune or select on holdout. Stage 1 tunes on outcomes only, 2024-01-01 to 2026-01-01. Stage 2 freezes parameters and validates outcomes and Kalshi's tradeable quote, 2026-01-01 to 2026-11-01. Holdout is 2026-11-01 on, opened once. Tradeable quote: first hourly bid/ask at least 30 minutes after listing and at least 2 hours before start, spread ≤ 0.06. Use paired match-clustered intervals; require significant stage-1 gain and no stage-2 regression, including guarded sections: all, tier1, tier2, tier3, international. Benchmark: `uv run python scripts/evaluate_elo.py --models team_elo,player_round_glicko --report-models team_elo,player_round_glicko --layers none --tune-from 2024-01-01 --tune-to 2026-01-01 --validate-from 2026-01-01`.

- An added parameter, feature or layer also needs a stage-1 gain of at least 0.0005 log loss.
- A stage-2 gain is reported but never rescues a change that failed stage 1; don't tune on stage 2 to pass it.
- Removals ship when every guarded section's interval stays below +0.0005 on both stages (non-inferior).
- Every test goes in the [research ledger](../research/README.md), adopted or not, with its numbers; count the tests run against stage 2.
- Trading results are reported, not gates. Data fixes (a link, alias, tier, parser bug) are not model changes: they ship when correct and the benchmark doesn't get significantly worse.

## Ratings and benchmark

`uv run python scripts/evaluate_elo.py` reads `db/cs2.db` and writes `docs/elo_backtest.md`. `--models` selects candidates; `--report-models` selects detailed reports (default team_elo, player_round_glicko and best two by tuning loss). Explicit report models are tuned too; team_elo is always the comparator. `--jobs` defaults to min(cpu,8), `--k-grid` overrides K, `player_round_glicko` and the adopted model (`models.ADOPTED`) score their pinned parameters (`models.PINNED`) unless `--full-grid` re-searches their grids (do so after major data changes and update `PINNED`), `--baseline` (default the adopted model) adds candidate − baseline paired tables by section, and `--write-weights` saves parameters and fit date in `promcs/ratings/elo_weights.json`. No dependencies or network are needed beyond the installed environment and caches.

Models: coin (0.5), team_elo (original binary team model), team/player × binary/margin/round × optional region offsets, player_round_glicko and its regional, rookie, moves and rookie_moves variants. Initial rating 1500, scale 400. Predict before updating in (UTC start, match_id, map order). Maps join matches/events and require unequal scores and excluded=0; starters come from player_maps. Player strength is mean starter rating; missing starters use the team's latest earlier lineup, then a namespaced pseudo-player. New players start at 1500 or known teammates' mean. Any nonempty lineup size is accepted.

Expected round/team share is 1/(1+10^(−Δ/400)). Binary credit is win/loss; margin winner credit is 0.5+0.5·tanh(abs(score difference)/c), loser its complement; round credit is score1/(score1+score2). Updates move ±K·(credit−expectation). Round models predict first-to-13 independent-round map probability with win-by-two overtime at 12–12, then temperature τ on map log odds; round share caches at four decimals. Binary/margin predict the Elo expectation directly.

Event regions are identity codes EU, CIS, NA, SA, AS, OCE, AF; other/missing codes are unknown. Team home uses earlier known non-international event-host map counts; ties retain the previous home. Regional Elo adds home offsets; only differing known homes update offsets, preserving zero sum. Current hosts are recorded after updating. Tier move ranks are tier3=1, tier2=2, tier1=3; unknown neither changes tier home nor applies moves. Rookie discounts decay logarithmically with earlier maps; move adjustments decay linearly with earlier maps at the target rank. They affect effective strength, never directly subtract stored rating.

Player RD starts at rd_new², grows rd_growth² per idle day capped at rd_new², scales moves by variance/rd_floor², and shrinks by inverse-variance information after updates. Defaults: new=280, floor=140, growth=10, info=0.125. Ordinary grids: K={16,24,32,48,64,96}; margin c={4,6,8,12}; round τ={0.4,0.5,0.6,0.8,1}; regional K={2,4,8,16}; player initialization fixed/teammates. RD grids: K={16,24,32,48,64}, τ={0.4,0.5,0.6,0.8}, new={280,350,450,600}, info={0.125,0.25,0.5,1}; regional K={2,4}. Rookie/move and weights grids anchor K=32, τ=0.5, new=350, info=0.125, teammates to the base stage-1 choice; registry defines adjustment grids. Online/tier3 K multipliers default to 1, compound when both apply, and search {0.5,0.75,1}; missing online is loaded as online.

Stage 1 tunes map outcome log loss on [2024-01-01,2026-01-01). Earlier maps seed history unless --seed-from limits it. Stage 2 freezes selected parameters on [2026-01-01,2026-11-01). Require seed-from ≤ tune-from < tune-to ≤ validate-from ≤ holdout. Only --holdout opens November onward. Series use the first map's chance and independent maps in odd best-of; missing/even lengths and unknown winners are skipped. Stage-1 Bo3/Bo5 temperature uses ≥30 series and a 0.40–1.50 grid, Bo1 stays 1; --no-series-temperature disables it. Reports include section metrics (tier1/tier2/tier3/unknown, international flags), coin and paired model comparisons with 2,000 match-clustered bootstrap resamples, seed 0.

Kalshi tables may be absent: outcome stages still run, stdout/report explicitly mark Kalshi sections skipped. Linked rows prefer team1 contracts and invert team2 quotes. --quote tradeable uses the first hourly bid/ask ≥30 minutes after listing and ≥2 hours before start, spread ≤0.06; hours24/hours6 use the last tight quote by those cutoffs; prestart uses the last valid quote by start. Missing links/aliases/candles skip rows. Map market predictions use first-map pre-match chances. --robustness compares quote rules without retuning; --series-check adds calibration and dependence diagnostics.

Returns buy the greater positive after-fee edge. Fees round up to cents per order. Flat stake is $1 plus fees; ROI divides profit by outlay. Kelly starts at $50 with Prometheus caps: 10% capital/$250 per fixture, $250/order, $1k exposure, $2k/day; same-day bets size on opening capital and settle together. Depth caps use half acceptable-price tape volume over six hours after quote; missing tape means no fills. Reports pair unlimited/depth-capped returns. Monthly logistic blends fit separate market/model coefficients by kind using earlier validation months, excluding holdout; fewer than 100 training rows use market unchanged and are excluded from blended metrics.

Layers retain fit/apply/describe factories with connection/lineup context. --layers none defaults to identity. regional fits logit(p′)=s·logit(p)+e[home1]−e[home2] on stage-1 cross-region rows, seven zero-sum effects with ridge 4; fewer than 50 eligible rows is identity. Homes are causal; validation outcomes never fit layers. Calibration fits tier×online logit temperatures on stage 1 with ridge 4 toward T=1; groups below 300 rows stay identity. Outputs clip to [1e-6,1−1e-6]. No form layer: CS2 player_maps has no per-player statistics.

## Site feed

`promcs feed-state` builds `feed/state.pkl.gz`: atomic gzip-6 pickle, version 1, replayed model/rated teams, temperatures, reconstructed finals/closes, match joins, lookups/aliases and data-through. Load only trusted internal snapshots; incompatible versions fail. `promcs export --state PATH` bypasses SQLite and candles; the DB wrapper remains available.

`promcs export [--out PATH] [--no-fetch]` atomically writes `PROMCS_DATA/feed/cs2.json` (default root `data/`) for Prometheus. Replays the adopted player_round_glicko_rookie_weights with its stored stage-1 weights; no refit. Upcoming named teams use latest rated lineups; unknown/even lengths emit null and use untempered Bo3 odds. Active DB events within the UTC date window supply revision-content queries in batches of 50. Raw snapshots go to `upcoming/latest.json.gz`; `--no-fetch` uses that snapshot and omits current prices. Raw Liquipedia/Kalshi caches stay read-only.

`predictions.json` saves upcoming calls by page/team IDs/ordinal, refreshes future calls and prunes disappeared future entries. Calls freeze once their saved start passes. Results join the closest unordered team pair within 36 hours once, flipping reversed probabilities; otherwise replay reconstructs them. Page results require a saved call. Missing started calls show live for six hours, then pending finals for seven days. Current Kalshi series prices use the offline linker's passes/window plus DB aliases, spread ≤0.10; finals use cached prestart candle mids. Only present sections are emitted. Ratings depend on crawl + setup_db freshness; tournaments absent from the DB are not scanned; TBD sides are omitted.
