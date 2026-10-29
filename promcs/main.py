"""The `promcs` command line."""

import typer

from promcs.kalshi.cli import app as kalshi_app

app = typer.Typer(no_args_is_help=True)
app.add_typer(kalshi_app, name="kalshi", help="Collect Kalshi CS2 markets.")

if __name__ == "__main__":
    app()
