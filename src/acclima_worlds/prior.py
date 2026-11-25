"""This function takes draws of world parameters from the prior predictive model. 
   A world is one set of parameters that produces an initial carbon trajectory for a single simulation."""
import numpy as np
from . import priors as P


def draw_worlds(n, seed, priorset=None):
    ps = P.DEFAULT if priorset is None else priorset
    rng = np.random.default_rng(seed)
    groups = ps.groups
    G = len(groups)
    pr = ps.priors
    w = {}
    w["npp"] = pr["npp_wood"].draw(rng, n)
    w["mu_bar"] = pr["mu_bar"].draw(rng, n)
    w["mu_c"] = pr["mu_comp"].draw(rng, n)
    w["root_shoot"] = pr["root_shoot"].draw(rng, n)
    w["kappa"] = 1.0 + pr["kappa_excess"].draw(rng, n)
    for key in ("M", "r", "mu_mult", "n_ref"):
        w[key] = np.zeros((n, G))
    w["m0"] = np.repeat(pr["m0"].draw(rng, n)[:, None], G, axis=1)
    for j, g in enumerate(groups):
        w["M"][:, j] = ps.group("M", g).draw(rng, n)
        w["r"][:, j] = ps.group("r", g).draw(rng, n)
        mu_mult, n_ref = ps.group("mu_mult", g), ps.group("n_ref", g)
        w["mu_mult"][:, j] = 1.0 if mu_mult is None else mu_mult.draw(rng, n)
        w["n_ref"][:, j] = 0.0 if n_ref is None else n_ref.draw(rng, n)
    w["mu"] = w["mu_bar"][:, None] * w["mu_mult"]          # per-group background hazard
    w["survival"] = pr["survival"].draw(rng, n)
    p_regen = pr["p_regen"].draw(rng, n)
    w["regen"] = (rng.random(n) < p_regen).astype(float)
    w["n_regen"] = pr["n_regen"].draw(rng, n)
    return w
