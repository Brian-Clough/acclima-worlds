"""Biophysical envelope: K = NPP x tau, and consistency of the trait priors with it.

K is the equilibrium live carbon a world's NPP can sustain given its turnover: K = NPP_wood / mu_bar.
The metabolic-scaling traits (M, r) and the mortality prior imply their own mature-stand carbon,
B_WBE = sum_j n_ref_j * mbar_j, where mbar_j is the mean tree carbon when stems are recruited
continuously and die at hazard mu_j (exponential age distribution) and each grows unconstrained:
    mbar = integral mu exp(-mu t) m(t) dt.
A world is weighted by how well B_WBE and K agree, with a log-normal tolerance (soft, two-sided):
neither the K estimate nor the asymptote implied by the traits is treated as exact.
"""
import numpy as np
from .cohort import wbe_mass
from . import priors as P


def mean_mass_exponential_age(M, r, m0, mu, horizon=1200):
    t = np.arange(horizon, dtype=float)
    m = wbe_mass(t[None, None, :], M[..., None], r[..., None], m0[..., None])
    w = np.exp(-mu[..., None] * t)
    w = w / w.sum(-1, keepdims=True)
    return (w * m).sum(-1)


def k_stock(world):
    """K = NPP * tau, tau = 1 / mu_bar (kg C / ha)."""
    return world["npp"] / world["mu_bar"]


def trait_implied_stock(world):
    mbar = mean_mass_exponential_age(world["M"], world["r"], world["m0"], world["mu"])
    return (world["n_ref"] * mbar).sum(1), mbar


def k_consistency_weights(world, factor=P.K_TOLERANCE_FACTOR):
    b_wbe, _ = trait_implied_stock(world)
    log_ratio = np.log(b_wbe / k_stock(world))
    sigma = np.log(factor)
    w = np.exp(-0.5 * (log_ratio / sigma) ** 2)
    return w / w.sum(), log_ratio


def effective_sample_size(w):
    return 1.0 / np.sum(np.asarray(w) ** 2)
