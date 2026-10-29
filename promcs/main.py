"""The `promcs` command line."""

from pathlib import Path

import typer

from promcs.kalshi.cli import app as kalshi_app
from promcs.liquipedia.cli import app as liquipedia_app

app = typer.Typer(no_args_is_help=True)
app.add_typer(kalshi_app, name="kalshi", help="Collect Kalshi CS2 markets.")

app.add_typer(
    liquipedia_app, name="liquipedia", help="Crawl Liquipedia CS2 tournament pages."
)


@app.command("export")
def export_command(out: Path | None = None, no_fetch: bool = False):
    """Write the Prometheus site prediction feed."""
    from promcs.feed import export

    export(out=out, no_fetch=no_fetch)


if __name__ == "__main__":
    app()
