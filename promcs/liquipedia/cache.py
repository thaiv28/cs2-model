"""Atomic gzip wikitext cache, indexed by requested title."""

import gzip
import hashlib
import json
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path


def data_dir() -> Path:
    return (
        Path(
            os.environ.get("PROMCS_DATA", Path(__file__).resolve().parents[2] / "data")
        )
        / "liquipedia"
    )


def page_file(title):
    key = hashlib.sha1(title.encode("utf-8")).hexdigest()
    return Path("pages") / key[:2] / f"{key}.json.gz"


def _atomic_write(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            raw = json.dumps(record, ensure_ascii=False).encode("utf-8")
            handle.write(gzip.compress(raw) if path.suffix == ".gz" else raw)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def load_index():
    path = data_dir() / "index.json"
    return json.loads(path.read_text()) if path.exists() else {}


def save_page(record):
    _atomic_write(data_dir() / page_file(record["title"]), record)


def read_page(title) -> dict | None:
    path = data_dir() / page_file(title)
    if not path.exists():
        return None
    return json.loads(gzip.decompress(path.read_bytes()))


def save_index(index):
    _atomic_write(data_dir() / "index.json", index)


def save_category(name, titles):
    slug = re.sub(r"[^\w.-]+", "_", name)
    _atomic_write(
        data_dir() / "category" / f"{slug}.json",
        {
            "titles": titles,
            "fetched_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        },
    )
