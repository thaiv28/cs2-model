"""Independent-round first-to-13 probability, with win-by-two overtime."""

from functools import lru_cache


def map_win(e):
    """Map win probability; quantize round share to bound the DP cache."""
    if not 0 <= e <= 1:
        raise ValueError("round probability must be between 0 and 1")
    return _map_win(round(e, 4))


@lru_cache(maxsize=10001)
def _map_win(e):
    # Work backwards from 12–12; terminal rows/columns are regulation wins.
    p = [[0.0] * 14 for _ in range(14)]
    for b in range(13):
        p[13][b] = 1.0
    p[12][12] = e * e / (e * e + (1 - e) ** 2)
    for a in range(12, -1, -1):
        for b in range(12, -1, -1):
            if a != 12 or b != 12:
                p[a][b] = e * p[a + 1][b] + (1 - e) * p[a][b + 1]
    return p[0][0]
