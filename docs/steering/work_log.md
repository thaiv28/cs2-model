# Work log

Newest first. Each entry: what changed, checks run, remaining limits. At most 150 words.

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
