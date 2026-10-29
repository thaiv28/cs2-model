"""Raw Kalshi catalogs, final-market histories and open-market books."""

import gzip
import json
import os
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

SERIES = ("KXCS2GAME", "KXCS2MAP")
FINAL = {"finalized", "settled"}
HISTORIES = {"trades": ".jsonl.gz", "candles": ".json.gz"}


def utc_now():
    return datetime.now(UTC)


def data_dir() -> Path:
    return (
        Path(
            os.environ.get("PROMCS_DATA", Path(__file__).resolve().parents[2] / "data")
        )
        / "kalshi"
    )


@dataclass
class SeriesSummary:
    markets: int = 0
    by_status: dict[str, int] = field(default_factory=dict)
    new_trade_files: int = 0
    new_candle_files: int = 0
    book_snapshots: int = 0


@dataclass
class Summary:
    series: dict[str, SeriesSummary] = field(default_factory=dict)
    errors: list[tuple[str, str]] = field(default_factory=list)
    catalog_errors: list[str] = field(default_factory=list)


class SnapshotCount(int):
    """An integer count carrying failures for the CLI's per-pass report."""

    def __new__(cls, count, errors):
        result = super().__new__(cls, count)
        result.errors = errors
        return result


def _atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            raw = text.encode("utf-8")
            handle.write(gzip.compress(raw) if path.suffix == ".gz" else raw)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def _load_manifest(root):
    path = root / "manifest.json"
    if not path.exists():
        return {kind: set() for kind in HISTORIES}
    manifest = json.loads(path.read_text())
    if manifest["version"] != 1:
        raise ValueError("unsupported Kalshi manifest version")
    return {kind: set(manifest[kind]) for kind in HISTORIES}


def _write_manifest(root, saved):
    manifest = {"version": 1}
    for kind, suffix in HISTORIES.items():
        present = {
            path.name.removesuffix(suffix)
            for path in (root / kind).glob(f"*{suffix}")
            if path.is_file()
        }
        manifest[kind] = sorted(saved[kind] | present)
    _atomic_write(root / "manifest.json", json.dumps(manifest) + "\n")
    return manifest


def rebuild_manifest():
    """Replace the manifest with only the histories present locally."""
    return _write_manifest(data_dir(), {kind: set() for kind in HISTORIES})


def _book(client, ticker, now):
    book = client.json(f"/markets/{ticker}/orderbook")["orderbook_fp"]
    at = now().astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    return json.dumps({"at": at, "ticker": ticker, "orderbook_fp": book}) + "\n"


def _write_books(root, snapshots, now):
    if not snapshots:
        return
    stamp = now().astimezone(UTC).replace(microsecond=0)
    # Keep distinct passes immutable even when they finish within one second.
    while True:
        path = root / "books" / stamp.strftime("%Y-%m-%d/%Y%m%dT%H%M%SZ.jsonl.gz")
        if not path.exists():
            break
        stamp += timedelta(seconds=1)
    _atomic_write(path, "".join(snapshots))


def collect(client, series=SERIES, books=True, limit=None, now=utc_now) -> Summary:
    """Refresh catalogs; limit counts attempted new trade/candle files combined."""
    if limit is not None and limit < 0:
        raise ValueError("limit must be nonnegative")
    root = data_dir()
    saved = _load_manifest(root)
    snapshots = []
    summary = Summary()
    fetched = 0
    for source in series:
        stats = summary.series[source] = SeriesSummary()
        try:
            catalog = {}
            origins = {}
            for endpoint in ("/historical/markets", "/markets"):
                for market in client.pages(
                    endpoint, "markets", series_ticker=source, limit=1000
                ):
                    catalog[market["ticker"]] = market
                    origins[market["ticker"]] = endpoint
            markets = sorted(catalog.values(), key=lambda m: m["ticker"])
            _atomic_write(root / "markets" / f"{source}.json", json.dumps(markets))
            stats.markets = len(markets)
            stats.by_status = dict(Counter(m["status"] for m in markets))
        except Exception as exc:
            summary.errors.append((source, str(exc)))
            summary.catalog_errors.append(source)
            continue
        for market in markets:
            ticker = market["ticker"]
            historical = origins[ticker] == "/historical/markets"
            if market["status"] in FINAL:
                for kind, suffix in HISTORIES.items():
                    path = root / kind / f"{ticker}{suffix}"
                    if (
                        path.exists()
                        or ticker in saved[kind]
                        or (limit is not None and fetched >= limit)
                    ):
                        continue
                    fetched += 1
                    try:
                        if kind == "trades":
                            trades = sorted(
                                client.pages(
                                    "/historical/trades"
                                    if historical
                                    else "/markets/trades",
                                    "trades",
                                    ticker=ticker,
                                    limit=1000,
                                ),
                                key=lambda t: (t["created_time"], t["trade_id"]),
                            )
                            if (
                                not trades
                                and Decimal(
                                    str(
                                        market.get("volume_fp", market.get("volume", 0))
                                    )
                                )
                                > 0
                            ):
                                raise ValueError("empty tape for traded market")
                            _atomic_write(
                                path, "".join(json.dumps(t) + "\n" for t in trades)
                            )
                            stats.new_trade_files += 1
                        else:
                            candles = client.json(
                                f"/historical/markets/{ticker}/candlesticks"
                                if historical
                                else f"/series/{source}/markets/{ticker}/candlesticks",
                                start_ts=int(
                                    datetime.fromisoformat(
                                        market["open_time"]
                                    ).timestamp()
                                ),
                                end_ts=int(
                                    datetime.fromisoformat(
                                        market["close_time"]
                                    ).timestamp()
                                ),
                                period_interval=60,
                            )["candlesticks"]
                            if not candles:
                                raise ValueError("empty candlesticks")
                            _atomic_write(path, json.dumps(candles))
                            stats.new_candle_files += 1
                    except Exception as exc:
                        summary.errors.append((ticker, str(exc)))
            elif market["status"] == "active" and books:
                try:
                    snapshots.append(_book(client, ticker, now))
                    stats.book_snapshots += 1
                except Exception as exc:
                    summary.errors.append((ticker, str(exc)))
    _write_manifest(root, saved)
    _write_books(root, snapshots, now)
    return summary


def snapshot_books(client, series=SERIES, now=utc_now) -> int:
    root = data_dir()
    snapshots, errors = [], []
    for source in series:
        try:
            markets = list(
                client.pages(
                    "/markets",
                    "markets",
                    series_ticker=source,
                    status="open",
                    limit=1000,
                )
            )
        except Exception as exc:
            errors.append((source, str(exc)))
            continue
        for ticker in sorted({m["ticker"] for m in markets if m["status"] == "active"}):
            try:
                snapshots.append(_book(client, ticker, now))
            except Exception as exc:
                errors.append((ticker, str(exc)))
    _write_books(root, snapshots, now)
    return SnapshotCount(len(snapshots), errors)
