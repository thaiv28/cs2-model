# Work log

Newest first. Each entry: what changed, checks run, remaining limits. At most 150 words.

## 2026-10-29 — Liquipedia contact in User-Agent

The crawler's User-Agent now carries the owner's email as Liquipedia's API terms ask (`http.CONTACT`); `LIQUIPEDIA_CONTACT` still overrides it. Checks: `uv run pytest -q`, ruff format/check.

## 2026-10-29 — Liquipedia crawler

Branch `liquipedia-crawler`, base `main` (`6a320c8`). Built query-only, paced/retrying HTTP, atomic gzip wikitext cache, revision-based incremental category and tab-subpage discovery, bounded content fetches, crawl/status CLI and offline tests. Updated layout, usage and status docs. Checks: `uv run pytest -q` 58 passed (23 new); ruff format/check passed. Live: `--limit 60` 3 min 47 s; full crawl 7 min 35 s, 4,713 pages (4,536 category + 177 subpages; 359 tab links point to nonexistent pages), 73,790 Match templates, 24 MB. Limit: each run re-checks all revision IDs (~3.5 min) before fetching changes.

## 2026-10-29 — Repo documentation

Created the repo docs mirroring valorant-model. Kalshi collector, work-log tooling, steering guard and CI were ported with renamed series, package, environment variable and S3 prefix; docs written. Checks: `uv run pytest -q` (35 passed), `uv run ruff format --check && uv run ruff check` passed. Limits: nothing collected; no GitHub remote.
