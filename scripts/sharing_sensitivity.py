"""How much does the rule for sharing the NPP budget matter?

Runs the same prior worlds and the same planting plan under alternative sharing rules and compares
live carbon and the pioneer / mid / slow mix. Rules differ only in how the realized stand growth R is
split among cohorts; R itself (the smooth minimum of demand and supply), mortality and everything
else are the cohort-core code. A cohort never receives more than its own potential growth; any excess
is passed to the other cohorts.

    python scripts/sharing_sensitivity.py [n_worlds] [seed]
"""
import sys
import numpy as np

from acclima_worlds.prior import draw_worlds
from acclima_worlds import priors as P
from acclima_worlds.cohort import smooth_min, npp_budget, run_stand

YEARS = 40
RULES = {
    "equal fraction (current)": lambda m, N: np.ones_like(m),
    "mass-weighted (beta=1)": lambda m, N: m,
    "mass-weighted (beta=2)": lambda m, N: m ** 2,
    "pioneers favoured (2, 1, 0.5)": lambda m, N: np.broadcast_to(np.array([2.0, 1.0, 0.5]), m.shape),
    "slow favoured (0.5, 1, 2)": lambda m, N: np.broadcast_to(np.array([0.5, 1.0, 2.0]), m.shape),
}


def split_budget(R, demand, weight):
    """Split R among cohorts in proportion to weight x demand, capped at each cohort's demand."""
    alloc = np.zeros_like(demand)
    left = R.copy()
    open_ = demand > 0
    for _ in range(demand.shape[1] + 1):
        w = np.where(open_, weight * demand, 0.0)
        tot = w.sum(1, keepdims=True)
        give = np.where(tot > 0, left[:, None] * w / np.where(tot > 0, tot, 1.0), 0.0)
        new = np.minimum(alloc + give, demand)
        left = left - (new - alloc).sum(1)
        alloc = new
        open_ = open_ & (alloc < demand * (1 - 1e-12))
    return alloc


def run(world, n0, years, rule, sharpness=P.CAP_SHARPNESS):
    M, r, mu, m0 = world["M"], world["r"], world["mu"], world["m0"]
    W, G = M.shape
    N, m = n0.astype(float).copy(), m0.copy()
    K = world["npp"] / world["mu_bar"]
    B = np.zeros((years + 1, W))
    Bg = np.zeros((years + 1, W, G))
    B[0] = (N * m).sum(1)
    Bg[0] = N * m
    binding = np.zeros((years + 1, W))
    for t in range(1, years + 1):
        u = (m / M) ** 0.25
        dm = M * (1.0 - (1.0 - u) * np.exp(-r)) ** 4 - m
        demand = N * dm
        D = demand.sum(1)
        S = npp_budget(world["npp"], world["kappa"], B[t - 1], K)
        R = smooth_min(D, S, sharpness)
        alloc = split_budget(R, demand, rule(m, N))
        phi = np.where(demand > 0, alloc / np.where(demand > 0, demand, 1.0), 1.0)
        m = m + phi * dm
        N = N * np.exp(-(mu + world["mu_c"][:, None] * (1.0 - phi)))
        B[t], Bg[t] = (N * m).sum(1), N * m
        binding[t] = (R / np.where(D > 0, D, 1.0)) < 0.9
    return B / 1000, Bg / 1000, binding


def main(n=2000, seed=1):
    world = draw_worlds(n, seed)
    n0 = np.tile([P.PLANTING_REFORESTATION[g] for g in P.GROUPS], (n, 1)).astype(float)
    ref = run_stand(world, n0, YEARS)["B"] / 1000
    print(f"{n} worlds, seed {seed}, reforestation plan, live carbon in t C/ha (5th / 50th / 95th percentile)\n")
    print(f"{'rule':32s} {'year 10':>16s} {'year 20':>16s} {'year 40':>16s}   cap binds y10   share of carbon y40 (pioneer/mid/slow)")
    for name, rule in RULES.items():
        B, Bg, binding = run(world, n0, YEARS, rule)
        if name.startswith("equal"):
            assert np.allclose(B, ref, rtol=1e-9), "equal-fraction rule must reproduce run_stand"
        cols = []
        for y in (10, 20, 40):
            p = np.percentile(B[y], [5, 50, 95])
            cols.append(f"{p[0]:4.0f}/{p[1]:4.0f}/{p[2]:4.0f}")
        share = np.median(Bg[40] / np.where(B[40] > 0, B[40], 1)[:, None], axis=0)
        print(f"{name:32s} {cols[0]:>16s} {cols[1]:>16s} {cols[2]:>16s}   {binding[10].mean():10.0%}      "
              f"{share[0]:.2f} / {share[1]:.2f} / {share[2]:.2f}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2000, int(sys.argv[2]) if len(sys.argv) > 2 else 1)
