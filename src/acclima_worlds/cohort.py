"""Size-structured cohort dynamics (basic version).

Each cohort has N stems per ha of mean carbon m (kg C) with West-Brown-Enquist ontogenetic growth
    dm/dt = a m^(3/4) [1 - (m/M)^(1/4)].
With u = (m/M)^(1/4) this is du/dt = r (1 - u), r = a / (4 M^(1/4)), so one year of unconstrained
growth has the closed form  u' = 1 - (1 - u) exp(-r).

Competition is a shared budget. Potential stand increment D = sum N dm_pot is compared with the NPP
supply S(B) (see `npp_budget`) through a smooth minimum, R = D / (1 + (D/S)^p)^(1/p): R ~ D when D << S, R -> S when D >> S.
Every cohort's growth is scaled by phi = R / D (symmetric sharing in this basic version; size-asymmetric
sharing is a later swap of `share_budget`). Stems die at a background hazard mu_j plus a competition
hazard mu_c (1 - phi), so crowded stands thin themselves. Mean-tree approximation: size variation
within a cohort is ignored.
"""
import numpy as np


def smooth_min(D, S, p):
    D = np.asarray(D, float)
    out = np.zeros_like(D)
    pos = D > 0
    out[pos] = D[pos] / (1.0 + (D[pos] / S[pos]) ** p) ** (1.0 / p)
    return out


def wbe_mass(t, M, r, m0):
    """Closed-form unconstrained WBE mass (kg C per tree) at age t."""
    u0 = (m0 / M) ** 0.25
    u = 1.0 - (1.0 - u0) * np.exp(-r * t)
    return M * u ** 4


def npp_budget(npp, kappa, B, K):
    """Supply S(B): kappa x NPP at B = 0, falling linearly to NPP at B = K, never below NPP.

    S = NPP [1 + (kappa - 1) max(0, 1 - B/K)].  With the cap binding and loss L = mu B this gives
    dB/dt = kappa mu (K - B): exponential approach to K with time constant tau / kappa.
    """
    return npp * (1.0 + (kappa - 1.0) * np.clip(1.0 - B / K, 0.0, None))


def share_budget(D, R):
    """Fraction of potential growth each cohort realizes. Basic: the same for all cohorts."""
    return np.where(D > 0, R / np.where(D > 0, D, 1.0), 1.0)


def run_stand(world, n0, years, sharpness=4.0):
    """Run one stand per world. n0: (W, G) planted/recruited stems per ha. Returns dict of (years+1, ...) arrays."""
    M, r, mu, m0 = world["M"], world["r"], world["mu"], world["m0"]
    W, G = M.shape
    N = n0.astype(float).copy()
    m = m0.copy()
    K = world["npp"] / world["mu_bar"]
    B = np.zeros((years + 1, W))
    B[0] = (N * m).sum(1)
    out = {"B": B, "growth": np.zeros((years + 1, W)), "dead": np.zeros((years + 1, W)),
           "demand": np.zeros((years + 1, W)), "phi": np.ones((years + 1, W)),
           "supply": np.zeros((years + 1, W))}
    for t in range(1, years + 1):
        u = (m / M) ** 0.25
        m_pot = M * (1.0 - (1.0 - u) * np.exp(-r)) ** 4
        dm_pot = m_pot - m
        D = (N * dm_pot).sum(1)
        S = npp_budget(world["npp"], world["kappa"], B[t - 1], K)
        R = smooth_min(D, S, sharpness)
        phi = share_budget(D, R)
        m = m + phi[:, None] * dm_pot
        growth = (N * phi[:, None] * dm_pot).sum(1)
        hazard = mu + world["mu_c"][:, None] * (1.0 - phi[:, None])
        N_new = N * np.exp(-hazard)
        dead = ((N - N_new) * m).sum(1)
        N = N_new
        B[t] = (N * m).sum(1)
        out["growth"][t], out["dead"][t], out["demand"][t], out["phi"][t] = growth, dead, D, phi
        out["supply"][t] = S
    out["N"], out["m"] = N, m
    return out
