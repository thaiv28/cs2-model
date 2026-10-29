"""Model registry: factories accept keyword parameters; predictions precede updates."""

from functools import partial
from typing import Protocol

from promcs.ratings.elo import EloModel


class Model(Protocol):
    def predict(self, row) -> float: ...

    def update(self, row) -> None: ...


class CoinModel:
    def predict(self, row):
        return 0.5

    def update(self, row):
        pass


class TeamEloModel(EloModel):
    """v1 name retained for team/binary Elo without offsets."""


MODELS = {"coin": CoinModel, "team_elo": TeamEloModel}
PARAM_GRIDS = {"coin": {}, "team_elo": {"k": (16, 24, 32, 48, 64, 96)}}
for unit in ("team", "player"):
    for credit in ("binary", "margin", "round"):
        for region in (False, True):
            if (unit, credit, region) == ("team", "binary", False):
                continue
            name = f"{unit}_{credit}" + ("_region" if region else "")
            MODELS[name] = partial(
                EloModel, unit=unit, credit=credit, region_k=16 if region else 0
            )
            grid = {"k": (16, 24, 32, 48, 64, 96)}
            if credit == "margin":
                grid["c"] = (4, 6, 8, 12)
            if credit == "round":
                grid["tau"] = (0.4, 0.5, 0.6, 0.8, 1.0)
            if region:
                grid["region_k"] = (2, 4, 8, 16)
            if unit == "player":
                grid["new_player"] = ("fixed", "teammates")
            PARAM_GRIDS[name] = grid

for region in (False, True):
    name = "player_round" + ("_region" if region else "") + "_glicko"
    MODELS[name] = partial(
        EloModel, unit="player", credit="round", rd=True, region_k=4 if region else 0
    )
    PARAM_GRIDS[name] = {
        "k": (16, 24, 32, 48, 64),
        "tau": (0.4, 0.5, 0.6, 0.8),
        "rd_new": (280, 350, 450, 600),
        "rd_info": (0.125, 0.25, 0.5, 1.0),
        "new_player": ("fixed", "teammates"),
    }
    if region:
        PARAM_GRIDS[name]["region_k"] = (2, 4)

# Stage-1 winners of the 640-point base grid (2026-10-29). Benchmarks score these
# by default; evaluate_elo.py --full-grid re-searches PARAM_GRIDS (update these after).
PINNED = {
    "player_round_glicko": {
        "k": 32,
        "tau": 0.5,
        "rd_new": 350,
        "rd_info": 0.125,
        "new_player": "teammates",
    },
}
# Adopted 2026-10-29 (research ledger): rookie discount + tier-3 K over the base.
ADOPTED = "player_round_glicko_rookie_weights"
PINNED[ADOPTED] = PINNED["player_round_glicko"] | {
    "rookie_penalty": 200,
    "rookie_maps": 400,
    "online_k": 1.0,
    "tier3_k": 0.75,
}

for variant in ("rookie", "moves", "rookie_moves", "weights", "rookie_weights"):
    name = f"player_round_glicko_{variant}"
    MODELS[name] = partial(EloModel, unit="player", credit="round", rd=True)
    grid = {
        "k": (32,),
        "tau": (0.5,),
        "rd_new": (350,),
        "rd_info": (0.125,),
        "new_player": ("teammates",),
    }
    if "rookie" in variant:
        grid.update(
            rookie_penalty=(150, 200, 300, 400, 600),
            rookie_maps=(50, 100, 200, 400),
        )
    if "moves" in variant:
        grid.update(move_up_penalty=(50, 100, 200), move_down_bonus=(0, 50))
    if "weights" in variant:
        grid.update(online_k=(0.5, 0.75, 1.0), tier3_k=(0.5, 0.75, 1.0))
    if variant == "rookie_weights":
        grid.update(rookie_penalty=(200, 300, 400), rookie_maps=(100, 200, 400))
    PARAM_GRIDS[name] = grid
