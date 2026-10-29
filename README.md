# cs2-model

A pre-map trading model for Counter-Strike 2 esports: player-based round Elo and a map layer, priced against Kalshi's CS2 series and map-winner markets.
Agent guidance is in [AGENTS.md](AGENTS.md); project status and design live in `docs/steering/`.

```bash
uv sync
uv run pytest -q
uv run promcs --help
```

Results source: Liquipedia, licensed under CC BY-SA 3.0.
