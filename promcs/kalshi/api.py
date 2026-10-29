"""Public Kalshi HTTP access with pacing, retries and cursor pagination."""

import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://api.elections.kalshi.com/trade-api/v2"
USER_AGENT = "cs2-model/0.1 (+https://github.com/thaiv28/cs2-model)"


def http_get(url) -> dict:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


class Client:
    def __init__(
        self, get=http_get, sleep=time.sleep, min_interval=0.06, clock=time.monotonic
    ):
        self.get = get
        self.sleep = sleep
        self.min_interval = min_interval
        self.clock = clock
        self._last_call = None

    def json(self, path, **query) -> dict:
        query = urlencode(
            {key: value for key, value in query.items() if value is not None}
        )
        url = f"{API}{path}" + (f"?{query}" if query else "")
        for attempt in range(5):
            if self._last_call is not None:
                delay = self.min_interval - (self.clock() - self._last_call)
                if delay > 0:
                    self.sleep(delay)
            self._last_call = self.clock()
            try:
                return self.get(url)
            except (HTTPError, URLError, TimeoutError) as exc:
                if isinstance(exc, HTTPError) and not (
                    exc.code == 429 or 500 <= exc.code < 600
                ):
                    raise
                if attempt == 4:
                    raise
                self.sleep(2**attempt)

    def pages(self, path, key, **query):
        while True:
            response = self.json(path, **query)
            items = response[key]
            yield from items
            cursor = response.get("cursor")
            if not items or not cursor:
                return
            query["cursor"] = cursor
