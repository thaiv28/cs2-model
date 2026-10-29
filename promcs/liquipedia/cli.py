"""Liquipedia collection and cache status commands."""

from typing import Annotated

import typer

from promcs.liquipedia import cache
from promcs.liquipedia.crawl import crawl as crawl_pages
from promcs.liquipedia.http import Fetcher

app = typer.Typer(no_args_is_help=True)


@app.command()
def crawl(
    limit: Annotated[int | None, typer.Option(min=0)] = None,
    full: Annotated[
        bool, typer.Option(help="Fetch content even for unchanged revisions.")
    ] = False,
):
    """Cache CS2 tournament pages and tab subpages."""
    result = crawl_pages(Fetcher(), limit=limit, full=full)
    typer.echo(
        f"listed={result.listed} new={result.new} changed={result.changed} unchanged={result.unchanged}"
    )
    typer.echo(
        f"subpages={result.subpages} missing={result.missing} fetched={result.fetched}"
    )


@app.command()
def status():
    """Show the local cache counts and newest fetch time."""
    index = cache.load_index()
    newest = max(
        (record["fetched_at"] for title in index if (record := cache.read_page(title))),
        default="none",
    )
    subpages = sum(entry["source"] == "subpage" for entry in index.values())
    typer.echo(f"pages={len(index)} subpages={subpages} newest fetched_at={newest}")
