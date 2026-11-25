"""This function takes draws of world parameters from the prior predictive model. 
   A world is one set of parameters that produces an initial carbon trajectory for a single simulation."""
import numpy as np
from . import priors as P


def draw_worlds(n, seed):
    rng = np.random.default_rng(seed)
    G = len(P.GROUPS)
    w = {}
    w["npp"] = P.NPP_WOOD.draw(rng, n)
    w["mu_bar"] = P.MU_BAR.draw(rng, n)
    w["mu_c"] = P.MU_COMP.draw(rng, n)
    w["root_shoot"] = P.ROOT_SHOOT.draw(rng, n)
    w["kappa"] = 1.0 + P.KAPPA_EXCESS.draw(rng, n)
    for key in ("M", "r", "mu_mult", "n_ref"):
        w[key] = np.zeros((n, G))
    w["m0"] = np.repeat(P.M0.draw(rng, n)[:, None], G, axis=1)
    for j, g in enumerate(P.GROUPS):
        gp = P.GROUP_PRIORS[g]
        w["M"][:, j] = gp["M"].draw(rng, n)
        w["r"][:, j] = gp["r"].draw(rng, n)
        w["mu_mult"][:, j] = 1.0 if gp["mu_mult"] is None else gp["mu_mult"].draw(rng, n)
        w["n_ref"][:, j] = 0.0 if gp["n_ref"] is None else gp["n_ref"].draw(rng, n)
    w["mu"] = w["mu_bar"][:, None] * w["mu_mult"]          # per-group background hazard
    w["survival"] = rng.beta(*P.SURVIVAL_ALPHA_BETA, size=n)
    p_regen = rng.beta(*P.P_REGEN_ALPHA_BETA, size=n)
    w["regen"] = (rng.random(n) < p_regen).astype(float)
    w["n_regen"] = P.N_REGEN.draw(rng, n)
    return w
