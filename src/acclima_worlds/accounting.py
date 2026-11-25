"""Creditable carbon per world: (project change) - (baseline change), in tCO2e/ha. No rules layer yet."""
import numpy as np
from .pools import total, C_TO_CO2E


def creditable_tco2e(sim_project, sim_baseline, world):
    cp = total(sim_project, world)
    cb = total(sim_baseline, world)
    net = (cp - cp[0]) - (cb - cb[0])
    return net * C_TO_CO2E / 1000.0                    # (years+1, W)


def weighted_quantile(x, w, q):
    x, w = np.asarray(x), np.asarray(w)
    i = np.argsort(x)
    cw = np.cumsum(w[i]) - 0.5 * w[i]
    cw /= w.sum()
    return np.interp(q, cw, x[i])
