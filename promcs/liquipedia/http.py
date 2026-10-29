"""Injectable, rate-limited MediaWiki query client."""

import gzip
import json
import os
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://liquipedia.net/counterstrike/api.php"
USER_AGENT = "cs2-model/0.1 (+https://github.com/thaiv28/cs2-model)"
# Liquipedia's API terms ask for contact details; LIQUIPEDIA_CONTACT overrides this.
CONTACT = "thaivillaluna@gmail.com"


def user_agent():
    contact = os.environ.get("LIQUIPEDIA_CONTACT") or CONTACT
    return USER_AGENT[:-1] + "; " + contact + ")"


def http_get(params: dict) -> dict:
    request = Request(
        API + "?" + urlencode(params | {"format": "json"}),
        headers={"User-Agent": user_agent(), "Accept-Encoding": "gzip"},
    )
    with urlopen(request, timeout=60) as response:
        raw = response.read()
        if response.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return json.loads(raw)


class Fetcher:
    def __init__(
        self, get=http_get, sleep=time.sleep, clock=time.monotonic, min_interval=2.2
    ):
        if min_interval < 0:
            raise ValueError("min_interval must be nonnegative")
        self.get, self.sleep, self.clock = get, sleep, clock
        self.min_interval = min_interval
        self._last = None
        self._lock = threading.Lock()
        self._paused_until = None

    def _wait_for_slot(self):
        with self._lock:
            now = self.clock()
            start = now
            if self._last is not None:
                start = max(start, self._last + self.min_interval)
            if self._paused_until is not None:
                start = max(start, self._paused_until)
            self._last = start
        if start > now:
            self.sleep(start - now)

    def query(self, **params) -> dict:
        if params.get("action") != "query":
            raise ValueError("Only action=query is permitted")
        for attempt in range(5):
            self._wait_for_slot()
            try:
                result = self.get(params)
            except (URLError, TimeoutError) as exc:
                if isinstance(exc, HTTPError) and not (
                    exc.code == 429 or 500 <= exc.code < 600
                ):
                    raise
                if attempt == 4:
                    raise
                with self._lock:
                    self._paused_until = self.clock() + 5 * 2**attempt
            else:
                if "error" in result:
                    raise RuntimeError(f"Liquipedia API error: {result['error']}")
                return result
        raise AssertionError("unreachable")
