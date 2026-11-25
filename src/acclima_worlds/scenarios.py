"""Project and baseline are switches on the same world and the same engine."""
import numpy as np
from . import priors as P
from .cohort import run_stand


def planting_n0(world, plan):
    n = np.array([plan[g] for g in P.GROUPS])[None, :]
    return n * world["survival"][:, None]


def baseline_n0(world):
    n0 = np.zeros_like(world["M"])
    n0[:, P.GROUPS.index("pioneer")] = world["regen"] * world["n_regen"]
    return n0


def run_project(world, plan, years):
    return run_stand(world, planting_n0(world, plan), years, P.CAP_SHARPNESS)


def run_baseline(world, years):
    return run_stand(world, baseline_n0(world), years, P.CAP_SHARPNESS)
