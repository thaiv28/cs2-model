"""Collect Kalshi CS2 histories and open-market order books."""

import time

import typer

from promcs.kalshi.api import Client
from promcs.kalshi.collect import collect as collect_markets
from promcs.kalshi.collect import rebuild_manifest, snapshot_books

app = typer.Typer(no_args_is_help=True)


def _errors(errors):
    tickers = ", ".join(ticker for ticker, _ in errors[:10])
    return f"errors={len(errors)}" + (f" ({tickers})" if tickers else "")


@app.command()
def collect(
    no_books: bool = typer.Option(False, "--no-books"),
    limit: int | None = typer.Option(
        None, min=0, help="Cap new trade/candle fetches combined."
    ),
):
    """Save catalogs, final-market tapes and hourly candles, plus open books."""
    summary = collect_markets(Client(), books=not no_books, limit=limit)
    for source, stats in summary.series.items():
        statuses = " ".join(
            f"{key}={value}" for key, value in sorted(stats.by_status.items())
        )
        typer.echo(
            f"{source}: markets={stats.markets} {statuses} "
            f"trades={stats.new_trade_files} candles={stats.new_candle_files} "
            f"books={stats.book_snapshots}"
        )
    typer.echo(_errors(summary.errors))
    if summary.catalog_errors:
        raise typer.Exit(1)


@app.command()
def books(
    every: float = typer.Option(
        60, min=0, clamp=False, help="Seconds between passes (positive)."
    ),
    minutes: float = typer.Option(60, min=0, help="Run duration in minutes."),
):
    """Refresh open tickers and save one snapshot file per pass."""
    if every <= 0:
        raise typer.BadParameter("must be positive", param_hint="--every")
    client = Client()
    deadline = time.monotonic() + minutes * 60
    try:
        while time.monotonic() < deadline:
            started = time.monotonic()
            count = snapshot_books(client)
            typer.echo(f"books={count} {_errors(count.errors)}")
            delay = min(started + every, deadline) - time.monotonic()
            if delay > 0:
                time.sleep(delay)
    except KeyboardInterrupt:
        return


@app.command()
def manifest():
    """Rebuild the history manifest from local trade and candle files."""
    saved = rebuild_manifest()
    typer.echo(f"trades={len(saved['trades'])} candles={len(saved['candles'])}")
