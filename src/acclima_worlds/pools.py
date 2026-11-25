"""Carbon pools behind one interface. Basic version: live biomass only (AGB + BGB).

Dead wood, litter and soil are added later by registering another function here that maps the
dynamics output (growth, dead flux, state) to a pool trajectory; nothing upstream changes.
"""
import numpy as np

C_TO_CO2E = 44.0 / 12.0


def live_agb(sim, world):
    return sim["B"]                                   # kg C / ha, (years+1, W)


def live_bgb(sim, world):
    return sim["B"] * world["root_shoot"][None, :]


POOLS = {"live_agb": live_agb, "live_bgb": live_bgb}
CREDITED_POOLS = ("live_agb", "live_bgb")


def total(sim, world, pools=CREDITED_POOLS):
    return sum(POOLS[p](sim, world) for p in pools)
