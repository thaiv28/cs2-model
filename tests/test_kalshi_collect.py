"""Offline Kalshi collection using captured responses and a fake clock."""

import gzip
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

import pytest
from typer.testing import CliRunner

from promcs.kalshi.api import API, Client
from promcs.kalshi.cli import app
from promcs.kalshi.collect import SERIES, collect, data_dir, snapshot_books

FIXTURES = Path(__file__).parent / "fixtures" / "kalshi"
NOW = datetime(2026, 10, 28, 23, 10, 12, 345678, tzinfo=UTC)


def fixture(name):
    return json.loads((FIXTURES / name).read_text())


class FakeClock:
    def __init__(self):
        self.time = 0.0
        self.sleeps = []

    def __call__(self):
        return self.time

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.time += seconds


class FakeGet:
    def __init__(self):
        self.calls = []
        self.fail_trade = None
        self.fail_catalog = None
        self.fail_book = None
        self.empty_trade = None
        self.empty_candles = None
        self.page2 = dict(
            fixture("markets_settled_game.json")["markets"][0], ticker="PAGE2"
        )

    def __call__(self, url):
        parts = urlsplit(url)
        path = parts.path.removeprefix("/trade-api/v2")
        query = {k: v[0] for k, v in parse_qs(parts.query).items()}
        self.calls.append((path, query))
        if path in ("/markets", "/historical/markets"):
            source = query["series_ticker"]
            if source == self.fail_catalog:
                raise HTTPError(url, 400, "bad catalog", {}, None)
            if query.get("cursor"):
                return {
                    "markets": [self.page2] if query["cursor"] == "page2" else [],
                    "cursor": "",
                }
            if source == SERIES[1]:
                return (
                    fixture("markets_open_map.json")
                    if path == "/markets"
                    else {"markets": []}
                )
            if query.get("status") == "open":
                return {"markets": []}
            if path == "/historical/markets":
                response = fixture("historical_markets_game.json")
                # Synthetic overlap: the current catalog's copy must win.
                response["markets"].append(
                    dict(
                        fixture("markets_settled_game.json")["markets"][0],
                        title="stale",
                    )
                )
                return response
            response = fixture("markets_settled_game.json")
            response["cursor"] = "page2"
            return response
        if path in ("/markets/trades", "/historical/trades"):
            if query["ticker"] == self.fail_trade:
                raise HTTPError(url, 400, "bad trade", {}, None)
            if query.get("cursor") or query["ticker"] == self.empty_trade:
                return {"cursor": "", "trades": []}
            return fixture(
                "historical_trades.json"
                if path == "/historical/trades"
                else "trades.json"
            )
        if path.endswith("/candlesticks"):
            assert query["period_interval"] == "60"
            assert int(query["start_ts"]) < int(query["end_ts"])
            if self.empty_candles and self.empty_candles in path:
                return {"candlesticks": []}
            return fixture(
                "candles_historical.json"
                if path.startswith("/historical/")
                else "candles.json"
            )
        if path.endswith("/orderbook"):
            if self.fail_book and self.fail_book in path:
                raise ValueError("bad book")
            return fixture("orderbook_open.json")
        raise AssertionError(f"Unexpected URL: {url}")


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv("PROMCS_DATA", str(tmp_path))
    fake, clock = FakeGet(), FakeClock()
    return fake, Client(get=fake, sleep=clock.sleep, clock=clock), tmp_path / "kalshi"


def test_collect_layout_pagination_and_idempotency(setup):
    fake, client, root = setup
    result = collect(client, now=lambda: NOW)
    assert not result.errors
    assert result.series[SERIES[0]].markets == 9
    assert result.series[SERIES[0]].by_status == {"finalized": 9}
    assert result.series[SERIES[0]].new_trade_files == 9
    assert result.series[SERIES[0]].new_candle_files == 9
    assert result.series[SERIES[1]].book_snapshots == 4
    catalog = json.loads((root / "markets" / f"{SERIES[0]}.json").read_text())
    assert [m["ticker"] for m in catalog] == sorted(m["ticker"] for m in catalog)
    assert (
        next(m for m in catalog if m["ticker"].endswith("KRTL-TL"))["title"] != "stale"
    )
    assert any(q.get("cursor") == "page2" for _, q in fake.calls)
    for market in catalog:
        ticker = market["ticker"]
        with gzip.open(root / "trades" / f"{ticker}.jsonl.gz", "rt") as handle:
            trades = [json.loads(line) for line in handle]
        expected = fixture(
            "historical_trades.json" if "AUG" in ticker else "trades.json"
        )["trades"]
        assert trades == sorted(
            expected, key=lambda t: (t["created_time"], t["trade_id"])
        )
        with gzip.open(root / "candles" / f"{ticker}.json.gz", "rt") as handle:
            assert (
                json.load(handle)
                == fixture(
                    "candles_historical.json" if "AUG" in ticker else "candles.json"
                )["candlesticks"]
            )
        assert not (root / "books" / f"{ticker}.jsonl").exists()
    book_paths = list((root / "books").rglob("*.jsonl.gz"))
    assert book_paths == [root / "books/2026-10-28/20261028T231012Z.jsonl.gz"]
    with gzip.open(book_paths[0], "rt") as handle:
        snapshots = [json.loads(line) for line in handle]
    assert len(snapshots) == 4
    for market in fixture("markets_open_map.json")["markets"]:
        ticker = market["ticker"]
        assert not (root / "trades" / f"{ticker}.jsonl.gz").exists()
        assert not (root / "candles" / f"{ticker}.json.gz").exists()
        snapshot = next(row for row in snapshots if row["ticker"] == ticker)
        assert snapshot == {
            "at": "2026-10-28T23:10:12Z",
            "ticker": ticker,
            **fixture("orderbook_open.json"),
        }
    saved = {
        p: (p.read_bytes(), p.stat().st_mtime_ns)
        for kind in ("trades", "candles")
        for p in (root / kind).iterdir()
    }
    old_book = book_paths[0].read_bytes()
    fake.calls.clear()
    second = collect(client, now=lambda: NOW)
    assert not second.errors
    assert all(
        path in ("/markets", "/historical/markets") or path.endswith("/orderbook")
        for path, _ in fake.calls
    )
    assert all(
        (p.read_bytes(), p.stat().st_mtime_ns) == old for p, old in saved.items()
    )
    assert book_paths[0].read_bytes() == old_book
    book_paths = sorted((root / "books").rglob("*.jsonl.gz"))
    assert len(book_paths) == 2
    for path in book_paths:
        with gzip.open(path, "rt") as handle:
            assert len(handle.readlines()) == 4
    assert not list((root / "books").rglob("*.jsonl"))
    assert not list(root.rglob("*.tmp"))


def test_catalog_origin_selects_history_endpoints(setup):
    fake, client, _ = setup
    collect(client, books=False)
    historical = fixture("historical_markets_game.json")["markets"][0]["ticker"]
    recent = fixture("markets_settled_game.json")["markets"][0]["ticker"]
    for ticker, trade_path, candle_path in (
        (
            historical,
            "/historical/trades",
            f"/historical/markets/{historical}/candlesticks",
        ),
        (
            recent,
            "/markets/trades",
            f"/series/{SERIES[0]}/markets/{recent}/candlesticks",
        ),
    ):
        trade_calls = [(p, q) for p, q in fake.calls if q.get("ticker") == ticker]
        assert trade_calls
        assert all(p == trade_path and q["limit"] == "1000" for p, q in trade_calls)
        assert any(q.get("cursor") for _, q in trade_calls)
        assert [p for p, _ in fake.calls if p.endswith(f"/{ticker}/candlesticks")] == [
            candle_path
        ]


@pytest.mark.parametrize("volume_field", ["volume_fp", "volume"])
@pytest.mark.parametrize("volume", ["0.00", "0.01"])
def test_empty_tape_volume_guard_and_retry(setup, volume_field, volume):
    fake, client, root = setup
    ticker = fake.page2["ticker"]
    fake.page2.pop("volume_fp", None)
    fake.page2.pop("volume", None)
    fake.page2[volume_field] = volume
    fake.empty_trade = ticker
    result = collect(client, books=False)
    path = root / "trades" / f"{ticker}.jsonl.gz"
    if volume == "0.00":
        assert not result.errors
        with gzip.open(path, "rt") as handle:
            assert handle.read() == ""
    else:
        assert result.errors == [(ticker, "empty tape for traded market")]
        assert not path.exists()
    fake.empty_trade = None
    fake.calls.clear()
    result = collect(client, books=False)
    assert not result.errors
    assert path.exists()
    assert result.series[SERIES[0]].new_trade_files == (volume != "0.00")
    trade_calls = [q for _, q in fake.calls if q.get("ticker") == ticker]
    if volume == "0.00":
        assert not trade_calls
    else:
        assert trade_calls
        with gzip.open(path, "rt") as handle:
            assert [json.loads(line) for line in handle]


def test_empty_candles_are_retried(setup):
    fake, client, root = setup
    ticker = fixture("historical_markets_game.json")["markets"][0]["ticker"]
    fake.empty_candles = ticker
    result = collect(client, books=False)
    assert result.errors == [(ticker, "empty candlesticks")]
    path = root / "candles" / f"{ticker}.json.gz"
    assert not path.exists()
    fake.empty_candles = None
    result = collect(client, books=False)
    assert not result.errors
    assert result.series[SERIES[0]].new_candle_files == 1
    with gzip.open(path, "rt") as handle:
        assert json.load(handle) == fixture("candles_historical.json")["candlesticks"]


def test_failures_are_isolated(setup):
    fake, client, root = setup
    fake.fail_trade = fixture("historical_markets_game.json")["markets"][0]["ticker"]
    result = collect(client, books=False)
    assert result.errors == [(fake.fail_trade, "HTTP Error 400: bad trade")]
    assert result.series[SERIES[0]].new_trade_files == 8
    assert result.series[SERIES[0]].new_candle_files == 9
    assert not (root / "trades" / f"{fake.fail_trade}.jsonl.gz").exists()
    assert not (root / "books").exists()
    fake.fail_catalog = SERIES[0]
    result = collect(client)
    assert result.catalog_errors == [SERIES[0]]
    assert result.series[SERIES[1]].book_snapshots == 4


def test_limit_and_nonfinal(setup):
    fake, client, root = setup
    fake.page2["status"] = "closed"
    result = collect(client, books=False, limit=1)
    assert result.series[SERIES[0]].new_trade_files == 1
    assert result.series[SERIES[0]].new_candle_files == 0
    collect(client, books=False)
    assert not (root / "trades" / "PAGE2.jsonl.gz").exists()
    fake.page2["status"] = "settled"
    collect(client, books=False)
    assert (root / "trades" / "PAGE2.jsonl.gz").exists()
    with pytest.raises(ValueError):
        collect(client, limit=-1)


def test_snapshot_books_refreshes_and_reports_errors(setup):
    fake, client, root = setup
    fake.fail_book = fixture("markets_open_map.json")["markets"][0]["ticker"]
    count = snapshot_books(client, now=lambda: NOW)
    assert isinstance(count, int) and count == 3
    assert count.errors == [(fake.fail_book, "bad book")]
    assert all(q["status"] == "open" for p, q in fake.calls if p == "/markets")
    paths = list((root / "books").rglob("*.jsonl.gz"))
    assert len(paths) == 1
    with gzip.open(paths[0], "rt") as handle:
        rows = [json.loads(line) for line in handle]
    assert len(rows) == 3
    assert fake.fail_book not in {row["ticker"] for row in rows}
    fake.fail_catalog = SERIES[0]
    count = snapshot_books(client)
    assert count == 3 and len(count.errors) == 2


@pytest.mark.parametrize("error", [429, 500, 503, "url", "timeout"])
def test_retries_and_pacing(error):
    clock, calls = FakeClock(), []

    def get(url):
        calls.append((url, clock()))
        if len(calls) == 1:
            if error == "url":
                raise URLError("offline")
            if error == "timeout":
                raise TimeoutError("offline")
            raise HTTPError(url, error, "retry", {}, None)
        return {"ok": True}

    client = Client(get=get, sleep=clock.sleep, clock=clock)
    assert client.json("/markets", ticker="A B", absent=None) == {"ok": True}
    client.json("/markets")
    assert calls[0][0] == f"{API}/markets?ticker=A+B"
    assert [at for _, at in calls] == pytest.approx([0, 1, 1.06])


def test_retry_exhaustion():
    clock, calls = FakeClock(), []

    def get(url):
        calls.append(url)
        raise HTTPError(url, 503, "unavailable", {}, None)

    with pytest.raises(HTTPError):
        Client(get=get, sleep=clock.sleep, clock=clock).json("/markets")
    assert len(calls) == 5
    assert clock.sleeps == [1, 2, 4, 8]


def test_cli_collect_exit_and_error_bound(setup, monkeypatch):
    fake, client, _ = setup
    monkeypatch.setattr("promcs.kalshi.cli.Client", lambda: client)
    runner = CliRunner()
    result = runner.invoke(app, ["collect", "--no-books", "--limit", "0"])
    assert result.exit_code == 0, result.output
    assert "markets=9" in result.output and "errors=0" in result.output
    fake.fail_catalog = SERIES[0]
    result = runner.invoke(app, ["collect", "--limit", "0"])
    assert result.exit_code == 1
    assert "errors=1" in result.output
    fake.fail_catalog = None
    fake.fail_trade = fixture("historical_markets_game.json")["markets"][0]["ticker"]
    result = runner.invoke(app, ["collect", "--no-books"])
    assert result.exit_code == 0 and "errors=1" in result.output
    from promcs.kalshi.cli import _errors

    line = _errors([(f"ticker{i}", "failed") for i in range(12)])
    assert "errors=12" in line and "ticker10" not in line


def test_cli_books_loop(setup, monkeypatch):
    _, client, root = setup
    clock = FakeClock()
    monkeypatch.setattr("promcs.kalshi.cli.Client", lambda: client)
    monkeypatch.setattr("promcs.kalshi.cli.time.monotonic", clock)
    monkeypatch.setattr("promcs.kalshi.cli.time.sleep", clock.sleep)
    monkeypatch.setattr(
        "promcs.kalshi.cli.snapshot_books",
        lambda client: snapshot_books(
            client, now=lambda: NOW + timedelta(seconds=clock())
        ),
    )
    result = CliRunner().invoke(app, ["books", "--every", "30", "--minutes", "1"])
    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == ["books=4 errors=0"] * 2
    assert clock.sleeps == [30, 30]
    assert len(list((root / "books").rglob("*.jsonl.gz"))) == 2
    assert CliRunner().invoke(app, ["books", "--every", "0"]).exit_code == 2


def test_data_dir_default(monkeypatch):
    monkeypatch.delenv("PROMCS_DATA", raising=False)
    assert data_dir() == Path(__file__).resolve().parents[1] / "data" / "kalshi"


def test_failed_trade_page_leaves_no_complete_file(setup):
    _, client, root = setup
    original_get = client.get
    ticker = fixture("historical_markets_game.json")["markets"][0]["ticker"]

    def get(url):
        query = parse_qs(urlsplit(url).query)
        if query.get("ticker") == [ticker] and "cursor" in query:
            raise HTTPError(url, 400, "bad second page", {}, None)
        return original_get(url)

    client.get = get
    result = collect(client, books=False)
    assert result.errors == [(ticker, "HTTP Error 400: bad second page")]
    path = root / "trades" / f"{ticker}.jsonl.gz"
    assert not path.exists()
    client.get = original_get
    result = collect(client, books=False)
    assert not result.errors and path.exists()
    assert result.series[SERIES[0]].new_trade_files == 1
    assert result.series[SERIES[0]].new_candle_files == 0


def test_atomic_write_preserves_destination_on_failure(tmp_path, monkeypatch):
    from promcs.kalshi.collect import _atomic_write

    path = tmp_path / "markets.json"
    path.write_text("old catalog")

    def fail_replace(source, destination):
        assert Path(source).read_text() == "new catalog"
        raise OSError("interrupted")

    monkeypatch.setattr("promcs.kalshi.collect.os.replace", fail_replace)
    with pytest.raises(OSError, match="interrupted"):
        _atomic_write(path, "new catalog")
    assert path.read_text() == "old catalog"
    assert not list(tmp_path.glob("*.tmp"))
    new_path = tmp_path / "new.json"
    with pytest.raises(OSError):
        _atomic_write(new_path, "new catalog")
    assert not new_path.exists()


def test_http_get_headers_timeout_and_json(monkeypatch):
    from io import BytesIO

    from promcs.kalshi.api import USER_AGENT, http_get

    def urlopen(request, timeout):
        assert request.full_url == f"{API}/markets"
        assert request.get_header("User-agent") == USER_AGENT
        assert timeout == 30
        return BytesIO(b'{"markets": []}')

    monkeypatch.setattr("promcs.kalshi.api.urlopen", urlopen)
    assert http_get(f"{API}/markets") == {"markets": []}


def test_manifest_skip_and_union(setup):
    fake, client, root = setup
    ticker = fake.page2["ticker"]
    root.mkdir()
    old = {"version": 1, "trades": [ticker, "REMOTE"], "candles": [ticker]}
    (root / "manifest.json").write_text(json.dumps(old))
    (root / "trades").mkdir()
    (root / "trades/LOCAL.jsonl.gz").write_bytes(gzip.compress(b""))
    result = collect(client, books=False)
    assert not result.errors
    assert result.series[SERIES[0]].new_trade_files == 8
    assert result.series[SERIES[0]].new_candle_files == 8
    assert not (root / "trades" / f"{ticker}.jsonl.gz").exists()
    assert not (root / "candles" / f"{ticker}.json.gz").exists()
    assert not any(
        q.get("ticker") == ticker or f"/{ticker}/candlesticks" in path
        for path, q in fake.calls
    )
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["version"] == 1
    for kind, suffix in (("trades", ".jsonl.gz"), ("candles", ".json.gz")):
        present = {p.name.removesuffix(suffix) for p in (root / kind).iterdir()}
        assert manifest[kind] == sorted(set(old[kind]) | present)
    assert not list(root.rglob("*.tmp"))


def test_manifest_command_rebuilds_from_local_files(setup):
    _, _, root = setup
    root.mkdir()
    (root / "manifest.json").write_text(
        json.dumps({"version": 1, "trades": ["REMOTE"], "candles": ["REMOTE"]})
    )
    for kind, names in {
        "trades": ["Z.jsonl.gz", "A.jsonl.gz", "ignored.tmp"],
        "candles": ["B.json.gz"],
    }.items():
        (root / kind).mkdir()
        for name in names:
            (root / kind / name).write_bytes(gzip.compress(b""))
    result = CliRunner().invoke(app, ["manifest"])
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "trades=2 candles=1"
    assert json.loads((root / "manifest.json").read_text()) == {
        "version": 1,
        "trades": ["A", "Z"],
        "candles": ["B"],
    }


def test_manifest_command_empty_archive(setup):
    _, _, root = setup
    result = CliRunner().invoke(app, ["manifest"])
    assert result.exit_code == 0, result.output
    assert json.loads((root / "manifest.json").read_text()) == {
        "version": 1,
        "trades": [],
        "candles": [],
    }


@pytest.mark.parametrize("mode", ["collect", "snapshot", "disabled"])
def test_zero_snapshots_write_no_book_file(setup, mode):
    _, client, root = setup
    if mode == "snapshot":
        assert snapshot_books(client, series=(SERIES[0],)) == 0
    else:
        result = collect(client, series=(SERIES[0],), books=mode != "disabled", limit=0)
        assert result.series[SERIES[0]].book_snapshots == 0
    assert not (root / "books").exists()


def test_failed_histories_are_excluded_from_manifest(setup):
    fake, client, root = setup
    fake.fail_trade = fake.page2["ticker"]
    fake.empty_candles = fake.page2["ticker"]
    result = collect(client, books=False)
    assert len(result.errors) == 2
    manifest = json.loads((root / "manifest.json").read_text())
    assert fake.page2["ticker"] not in manifest["trades"]
    assert fake.page2["ticker"] not in manifest["candles"]
