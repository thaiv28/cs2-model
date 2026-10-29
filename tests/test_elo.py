from types import SimpleNamespace

import pandas as pd
import pytest

from promcs.ratings.elo import EloConfig, TeamElo
from promcs.ratings.models import MODELS, TeamEloModel
from promcs.ratings.replay import replay


def test_symmetry_and_zero_sum():
    elo = TeamElo(EloConfig(k=40))
    assert elo.expected(1, 2) == 0.5
    elo.update(1, 2, 1)
    assert elo.ratings == {1: 1520, 2: 1480}
    assert elo.expected(1, 2) + elo.expected(2, 1) == pytest.approx(1)
    elo.update(1, 2, 0)
    assert sum(elo.ratings.values()) == pytest.approx(3000)
    assert elo.expected(3, 4) == 0.5


def test_replay_order_and_no_leakage():
    maps = pd.DataFrame(
        [
            (4, 2, "2024-01-02", 2, 0),
            (2, 1, "2024-01-02", 1, 1),
            (3, 2, "2024-01-02", 1, 1),
            (1, 9, "2023-01-01", 1, 1),
        ],
        columns=["game_id", "match_id", "start_utc", "order", "won"],
    ).assign(team1_id=10, team2_id=20)
    result = replay(maps, TeamEloModel())
    assert list(result.game_id) == [1, 2, 3, 4]
    assert result.p.iloc[0] == 0.5
    assert result.p.iloc[1] > 0.5
    for game_id in result.game_id:
        flipped = maps.copy()
        flipped.loc[flipped.game_id == game_id, "won"] ^= 1
        changed = replay(flipped, TeamEloModel())
        position = result.index[result.game_id == game_id][0]
        assert changed.p.iloc[position] == result.p.iloc[position]
    assert (replay(maps, MODELS["coin"]()).p == 0.5).all()
    row = SimpleNamespace(team1_id=10, team2_id=20, won=1)
    model = MODELS["team_elo"](k=16)
    model.update(row)
    assert model.elo.ratings[10] == 1508
