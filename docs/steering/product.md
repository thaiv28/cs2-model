# Product

## Goal

Price CS2 matches before each map well enough to beat Kalshi's prices after fees, then trade them. Edge comes from a better rating model, as in Prometheus and valorant-model.

## Markets

- `KXCS2GAME`: series winner. Live API holds markets settled after 2026-08-29; older markets require Kalshi historical endpoints. First listing date is unknown until backfill.
- `KXCS2MAP`: map winner by slot.
- Legacy 2025 `KXCSGOGAME` / `KXCSGOMAP` markets exist and are not collected yet.
- 2026-10-28 study: about 50 CS2 series per day, the largest esports series on Kalshi. 85–90% of volume trades in-play. Tier 1 has deep pregame books; tier 2/3 median pregame volume is under $500.

## Where the edge comes from

From a better rating model, as in Prometheus and valorant-model.

## Model

Plan: player round Elo with RD (Glicko-style), rookie discount, region offsets, form and map strength, then calibration and market blend.

## Trading rules

League's limits ($250 per order and fixture, $1k exposure, $2k per day, same Kelly settings) from a $50 seed. No new orders once seed + settled profit − open stakes is $0 or less. Paper trading before live.

## Data

Liquipedia (results, per-map round scores by half and side, tournament rosters, tiers and host country) and Kalshi public API. Liquipedia has no veto data. Holdout: matches from 2026-11-01 on.
