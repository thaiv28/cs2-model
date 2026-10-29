# Work log

Newest first. Each entry: what changed, checks run, remaining limits. At most 150 words.

## 2026-10-29 — Execution inputs

Branch `game-candidates`, base `main`. Added frozen `promcs/blend_artifact.json`, private atomic candidates with Kalshi rules names/start checks and raw series provenance; shared benchmark helpers are unchanged. Feed uploads `cs2-model/feed/candidates.json` for Prometheus's Lambda. Real artifact: 8 snapshots; latest a=1.243027236, b=0.653439642, n=4136. Checks: pytest 297 passed/15.06 s versus 283 existing tests/13.60 s (+1.46 s locally); 14 new tests alone 0.18 s; ruff format/check, diff check and helper syntax-tree equality passed. Artifact, feed-state (8.33 s) and snapshot no-fetch export (0.42 s, candidates=0, skipped_candidates=0) passed. Used UV_NO_SYNC/UV_OFFLINE after plain uv's macOS panic. Limits: GitHub/S3/Lambda execution and runner timings unverified. No network or commits.

## 2026-10-29 — Actions site feed snapshots

Branch `game-feed`, base phase-1 `f31f2fe`. Split DB/candle replay into a versioned gzip-pickle snapshot; export accepts it without SQLite. Added hourly refresh and frequent feed workflows with OIDC, raw caches, conditional prediction-log persistence and optional Prometheus dispatch. S3: `cs2-model/{liquipedia/,kalshi/,feed/{state.pkl.gz,predictions.json,cs2.json.gz,upcoming/}}`. Checks: 261 tests passed/12.93 s (phase-1: 255/14.99 s; six added guards); ruff format/check, bash syntax and normalized feed cmp passed. Offline state: 6,164,779 bytes/7.84 s; export 0.44 s versus DB 8.47 s. Used UV_NO_SYNC/UV_OFFLINE for uv’s local macOS panic. Limits: workflows not yet run on GitHub; runner times unmeasured; raw caches must be seeded in S3 once. No network or commits. Merged main: the feed replays the adopted `player_round_glicko_rookie_weights`; `evaluate_elo.py --write-weights` (report to scratch; docs/elo_backtest.md unchanged) reproduced its parameters and stored stage-1 series temperatures Bo3 0.86, Bo5 0.68.

## 2026-10-29 — Prometheus game feed

Branch `game-feed`, base `main`. Added `promcs export`: upcoming/live calls, replayed results, current Kalshi series mids and cached prestart closes. Stored existing stage-1 weights; benchmark exports string-keyed series temperatures. Calls refresh until their saved start, then freeze; results consume closest team-pair calls once, correcting orientation. Nine offline tests cover scheduling, lifecycle, joins, batching, pagination and prices. Checks: existing suite 246 passed/13.13 s; added feed tests 9 passed/0.23 s; combined 255 passed/14.99 s (+1.86 s versus baseline); ruff format/check and diff check passed. Used `UV_NO_SYNC=1` for uv's sandbox macOS panic. Real offline export: 15,538 finals, 4,774 priced, 8.30 s; 6,280,217 bytes. Limits: ratings only as fresh as last crawl + setup_db; tournaments not yet in DB are not scanned for upcoming matches; TBD sides omitted. No network or commits.

## 2026-10-29 — Pin adopted model; regional retest

Branch `pin-adopted`, base `main` (4d7fa70). Pinned `player_round_glicko_rookie_weights` (rookie 200/400, tier-3 K 0.75) as `models.ADOPTED`; new `--baseline` (default ADOPTED) adds candidate − baseline paired tables by section in both stages; existing benchmark tests pass `--baseline team_elo`. Regional layer over the adopted model rejected: stage-2 maps −0.00044 (significant, below 0.0005), Kalshi blended unchanged (ledger). Run: 453 s for three models × two layers. Holdout not opened: no maps on or after 2026-11-01. Checks: ruff, `uv run pytest -q`.

## 2026-10-29 — Pinned base grid

Branch `bench-speed`, base `elo-candidates` (0cdba0a). `player_round_glicko` now scores its stage-1 winner (`models.PINNED`: K=32, τ=0.5, rd_new=350, info=0.125, teammates) instead of re-searching 640 combinations every run; `--full-grid` restores the search, and `--k-grid` still overrides K. Two-model run (`team_elo,player_round_glicko`) 517 s → 214 s with identical stage-2 results. Candidate verdicts in the ledger: rookie 200/400 + tier-3 K 0.75 adopted (stage 2 −0.0068 maps); calibration, online K, tier moves rejected; regional pending intervals. S3 seeded (82,216 objects). Checks: ruff, `uv run pytest -q` (267 passed).

## 2026-10-29 — CS2 Elo candidates

Branch `elo-candidates`, base `main` (0807b8c). Added tier×LAN calibration and online/tier3 K weighting candidates; anchored rookie/moves grids to the base stage-1 parameters. Replay carries online metadata; offline tests cover calibration, thresholds, neutral multipliers, compounded updates and invalid inputs. Checks: pytest 266 passed/12.56 s; 18 new calibration/multiplier cases 0.29 s (clean before-change timing unavailable); ruff format/check, CLI help, registry listing and diff check passed. Used `UV_NO_SYNC=1 UV_OFFLINE=1`: plain uv panics in macOS configuration. Updated the evaluation fixture for online metadata. Limit: benchmark run pending (run by reviewer). No weights or benchmark report written.

## 2026-10-29 — Full Kalshi backfill and validation

Branch `full-bench`, base `main` (c8a3138). Backfill finished (KXCS2GAME 15,815, KXCS2MAP 25,730 markets; 106 fetch errors left for the scheduled collector). Rebuilt DB: series links 5,138/7,907, map links 9,131/12,865, results agree 28,362/28,396. Benchmark (517 s): player_round_glicko blended series −0.0118 vs Kalshi (significant), raw +0.0003; maps n.s.; blended series flat ROI +8.0% [+3.7, +12.2]. Committed `docs/elo_backtest.md`; ledger updated. S3 seeding pending (AWS SSO expired). Checks: `uv run pytest -q`.

## 2026-10-29 — First Kalshi validation (preliminary)

Branch `ledger`, base `main` (4f689df). Ran `evaluate_elo.py --models team_elo,player_round_glicko --layers none` (320 s) with the Kalshi backfill ~40% done: player_round_glicko raw +0.0014 (n.s.), blended −0.0105 (significant) vs Kalshi's tradeable quote on 1,876 series; recorded in the research ledger. `docs/elo_backtest.md` not committed until the backfill completes. Checks: `uv run pytest -q`.

## 2026-10-29 — Benchmark reads Liquipedia alias column

Branch `alias-col`, base `main` (491154a). The parallel ratings and linking branches disagreed: `evaluate_elo.py` read `team_aliases.vlr_team_id`, which the CS2 link step names `liquipedia_team_id`; the Kalshi stage crashed. Renamed in the benchmark and its test. Checks: `uv run pytest -q`, ruff format/check.

## 2026-10-29 — Ratings and benchmark port

Branch `ratings`, base `main` (`99fdabc`). Ported team/player Elo, RD/rookie/moves, seven-region causal layer, evaluation, blend, execution backtest and two-stage/series CLIs; adapted CS2 reads, tiers and dates. Missing Kalshi tables explicitly skip market sections. Added synthetic tests and aligned docs. Checks: pytest 204 passed (12.57 s unloaded, 27.18 s during benchmark; baseline 109/1.01 s, +11.56 s CI work); ruff format/check and diff check passed. Used `UV_NO_SYNC=true UV_OFFLINE=true` to avoid uv sync's local panic. Offline rebuild passed (25.53 s); rebuild plus benchmark 227.81 s, evaluation 201.85 s. Stage 1, 73,819 maps: player_round_glicko map/series loss 0.640438/0.619448 (K32, teammates, RD350/info0.125, τ0.5); team_elo 0.662311/0.647815 (K32). Scratch report only; stage-2 outcomes scored. Limits: Kalshi validation pending links; no stats/form layer; holdout closed.

## 2026-10-29 — Kalshi linking

Branch `kalshi-link`, base `main` (`99fdabc`). Ported offline catalog loading, series/map linking, display-name/key variants, learned aliases, settlement checks and report; added 42 offline tests. CS2 guard ignores academy-only overlap/similarity after a real false anchor; normalization retains academies. Real rebuild: 15,795 markets; series=5138/7897 map=0/0 aliases=599 results=10172/10188 mismatches=16. Main unlinked reasons: no team match, implausible anchor opponent, ambiguous fuzzy/alias candidates, no candidate within 30h. Checks: setup_db completed; pytest 151 passed; ruff format/check and foreign-key/excluded-event checks passed. Measured test time: baseline 109 tests 0.58 s; 151 tests 0.63 s. Plain uv run crashed in sandbox macOS system configuration; checks used UV_NO_SYNC=1 with installed dependencies. Limits: map catalog absent; backfill ongoing; 2,210 markets lack parsed schedules; 16 settlement mismatches need source review. No network/cache changes or commit.

## 2026-10-29 — Liquipedia database

Branch `liquipedia-db`, base `main` (`448bf13`). Built pure wikitext/roster/region parsers, stable-ID SQLite schema, offline loader and rebuild script; added fixture and synthetic tests and updated layout/status docs. Real-cache build: pages=4713 events=4713 excluded=65; matches=58034 maps=119185 duplicates=1; both_rosters=46914 (80.8%); unknown_tz=0 after adding 29 zones and `UTC±N` (was 2,481) dateless=183 map_order_gt9=0 players_both_sides=64; parse_errors=0, 24 s. Checks: `uv run pytest -q` 109 passed (51 added); ruff format/check passed; real DB foreign-key and map-ID checks passed. Limits: tournament rosters miss stand-ins; unknown zones assume UTC; international rule is approximate.

## 2026-10-29 — Liquipedia contact in User-Agent

The crawler's User-Agent now carries the owner's email as Liquipedia's API terms ask (`http.CONTACT`); `LIQUIPEDIA_CONTACT` still overrides it. Checks: `uv run pytest -q`, ruff format/check.

## 2026-10-29 — Liquipedia crawler

Branch `liquipedia-crawler`, base `main` (`6a320c8`). Built query-only, paced/retrying HTTP, atomic gzip wikitext cache, revision-based incremental category and tab-subpage discovery, bounded content fetches, crawl/status CLI and offline tests. Updated layout, usage and status docs. Checks: `uv run pytest -q` 58 passed (23 new); ruff format/check passed. Live: `--limit 60` 3 min 47 s; full crawl 7 min 35 s, 4,713 pages (4,536 category + 177 subpages; 359 tab links point to nonexistent pages), 73,790 Match templates, 24 MB. Limit: each run re-checks all revision IDs (~3.5 min) before fetching changes.

## 2026-10-29 — Repo documentation

Created the repo docs mirroring valorant-model. Kalshi collector, work-log tooling, steering guard and CI were ported with renamed series, package, environment variable and S3 prefix; docs written. Checks: `uv run pytest -q` (35 passed), `uv run ruff format --check && uv run ruff check` passed. Limits: nothing collected; no GitHub remote.
