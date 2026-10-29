# AGENTS.md

Guidance for AI coding agents (and humans) working in this repo.

## Read before work

Read only what your change touches. If a task names files and docs, read those and skip this list.

- **Always:** newest work-log entries, `python3 scripts/work_log.py recent 5`.
- **Data sources, tables, layout:** [Tech](docs/steering/tech.md).
- **Status and future work:** [Current state](docs/steering/current_state.md).
- **Goals and model plan:** [Product](docs/steering/product.md).
- **Schedules, storage, AWS:** [Deployment](docs/steering/deployment.md).
- **Before a model change:** tech.md, Model change rules, and the [research ledger](docs/research/README.md).

Read large docs by section (`grep -n '^## '`), not whole. Code and built data are the source of truth; if a doc disagrees, verify and fix it. The user's latest instructions override these docs.

## Required document updates

- Every substantive code or behavior change: dated entry at the top of `docs/steering/work_log.md`, what changed, checks actually run, remaining limit; at most 150 words.
- Feature status and limits: `current_state.md`; sources, tables, algorithms and layout: `tech.md`; schedules, storage, secrets and AWS: `deployment.md`.
- Every tested model idea: `docs/research/README.md` with stage-1 and stage-2 numbers. Model or benchmark changes also regenerate `docs/elo_backtest.md` when the benchmark exists.

`uv run pytest -q` includes `tests/test_steering.py`, which requires a work-log update for code changes and enforces doc budgets. The pre-commit hook rotates the work log. Enable with `git config core.hooksPath .githooks`.

## What this is

A pre-map trading model for CS2 esports: player-based round Elo, a map layer, priced against Kalshi's CS2 series (`KXCS2GAME`) and map-winner (`KXCS2MAP`) markets. It follows Prometheus (`../Prometheus`) and valorant-model (`../valorant-model`), whose Elo, benchmark and Kalshi code it reuses.

## Quick commands

```bash
uv sync
uv run pytest -q
uv run ruff format && uv run ruff check
uv run promcs --help                     # kalshi and liquipedia groups
uv run promcs liquipedia crawl            # Liquipedia CS2 pages (first run ~5 min)
```

`data/` and `db/` are build artifacts; never commit them.

### Worktrees

Share raw caches by symlink (`data/liquipedia` and `data/kalshi`); never share `db/`.

## Conventions

- **Network is polite and cached.** Liquipedia MediaWiki API (`https://liquipedia.net/counterstrike/api.php`) only via `action=query` wikitext; never `action=parse` or scrape HTML pages. At most one request per 2 s, gzip, User-Agent naming this repo with a contact. Cache raw responses; never re-fetch finished tournaments. Credit Liquipedia (CC BY-SA 3.0). HLTV is not scraped; its terms forbid it.
- Changing parser output requires bumping `PARSER_VERSION`.
- **Raw first, parse later.** Save raw responses unchanged (gzip); rebuild the DB from them; parsers never fetch.
- **Data access is raw SQL** on SQLite; no ORM. Schema changes use a new numbered `scripts/NNN_*.sql`; rebuild from scratch, no migrations.
- **Times are UTC** (ISO 8601 with `Z`).
- **Model changes need a significant stage-1 gain and no stage-2 regression**, judged with the two-stage benchmark. Holdout: matches from 2026-11-01 on. Full rules: tech.md, Model change rules.
- **Trading** reuses Prometheus's executor rules and limits from a $50 seed; no new orders once capital (seed + settled profit − open stakes) is $0 or less.
- **CI time is a budget.** Measure added CI work and record before/after in the work log.
- **Token use is a budget.** Keep docs short; scripts print summaries, not per-row logs.
- Formatting and linting: `ruff` (configured in `pyproject.toml`).

## Before you finish a change

1. `uv run pytest -q` and `uv run ruff format --check && uv run ruff check` pass.
2. Inspect the diff and keep docs aligned with code. State anything not verified.
