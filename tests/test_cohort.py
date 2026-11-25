import numpy as np
import pytest
from acclima_worlds import priors as P
from acclima_worlds.prior import draw_worlds
from acclima_worlds.cohort import smooth_min, wbe_mass, run_stand, npp_budget


def _plant(w, plan=None, years=40):
    plan = plan or P.PLANTING_REFORESTATION
    n0 = np.array([plan[g] for g in P.GROUPS])[None, :] * w["survival"][:, None]
    return run_stand(w, n0, years, P.CAP_SHARPNESS)


def small_world(n=50, seed=1):
    return draw_worlds(n, seed)


def test_smooth_min_limits_and_bounds():
    S = np.full(3, 100.0)
    D = np.array([0.1, 100.0, 1e6])
    R = smooth_min(D, S, 4.0)
    assert R[0] == pytest.approx(0.1, rel=1e-6)
    assert R[2] == pytest.approx(100.0, rel=1e-3)
    assert np.all(R <= np.minimum(D, S) + 1e-12)
    assert smooth_min(np.array([0.0]), np.array([5.0]), 4.0)[0] == 0.0


def test_unconstrained_growth_matches_closed_form():
    w = small_world()
    w["npp"] = np.full(50, 1e12)          # supply never binds
    w["mu"] = np.zeros_like(w["mu"]); w["mu_c"] = np.zeros(50)
    n0 = np.ones_like(w["M"])
    sim = run_stand(w, n0, 40)
    expect = wbe_mass(40.0, w["M"], w["r"], w["m0"]).sum(1)
    assert np.allclose(sim["B"][40], expect, rtol=1e-9)


def test_carbon_balance_each_year():
    w = small_world()
    sim = _plant(w)
    dB = sim["B"][1:] - sim["B"][:-1]
    assert np.allclose(dB, sim["growth"][1:] - sim["dead"][1:], rtol=1e-9, atol=1e-6)


def test_realized_growth_never_exceeds_supply_or_demand():
    w = small_world(200)
    sim = _plant(w)
    S = sim["supply"][1:]
    assert np.all(sim["growth"][1:] <= S + 1e-6)
    assert np.all(sim["growth"][1:] <= sim["demand"][1:] + 1e-6)
    assert np.all(sim["supply"][1:] >= w["npp"][None, :] - 1e-6)     # budget never below mature NPP


def test_cap_binds_in_dense_stands_and_not_in_sparse_ones():
    w = small_world(200)
    dense = run_stand(w, np.full_like(w["M"], 3000.0), 20)
    sparse = run_stand(w, np.full_like(w["M"], 1.0), 20)
    assert (dense["phi"][1:] < 0.9).mean() > 0.5
    assert (sparse["phi"][1:] > 0.99).all()


def test_vectorised_engine_matches_plain_loop():
    """Independent re-implementation, one world and one cohort at a time, no numpy broadcasting."""
    import math
    w = small_world(5, seed=3)
    n0 = np.array([P.PLANTING_REFORESTATION[g] for g in P.GROUPS])[None, :] * w["survival"][:, None]
    sim = run_stand(w, n0, 30, P.CAP_SHARPNESS)
    for k in range(5):
        N = list(n0[k]); m = list(w["m0"][k]); G = 3
        for t in range(1, 31):
            dm = []
            for j in range(G):
                u = (m[j] / w["M"][k, j]) ** 0.25
                mp = w["M"][k, j] * (1 - (1 - u) * math.exp(-w["r"][k, j])) ** 4
                dm.append(mp - m[j])
            D = sum(N[j] * dm[j] for j in range(G))
            Bprev = sum(N[j] * m[j] for j in range(G))
            Kk = w["npp"][k] / w["mu_bar"][k]
            S = w["npp"][k] * (1 + (w["kappa"][k] - 1) * max(0.0, 1 - Bprev / Kk))
            R = D / (1 + (D / S) ** P.CAP_SHARPNESS) ** (1 / P.CAP_SHARPNESS) if D > 0 else 0.0
            phi = R / D if D > 0 else 1.0
            for j in range(G):
                m[j] += phi * dm[j]
                N[j] *= math.exp(-(w["mu"][k, j] + w["mu_c"][k] * (1 - phi)))
        B = sum(N[j] * m[j] for j in range(G))
        assert B == pytest.approx(sim["B"][30, k], rel=1e-10)


def test_budget_endpoints_and_floor():
    npp = np.array([3000.0]); K = np.array([150000.0]); kappa = np.array([2.0])
    assert npp_budget(npp, kappa, np.array([0.0]), K)[0] == pytest.approx(6000.0)
    assert npp_budget(npp, kappa, K, K)[0] == pytest.approx(3000.0)
    assert npp_budget(npp, kappa, 2 * K, K)[0] == pytest.approx(3000.0)        # floored at mature NPP
    assert npp_budget(npp, kappa, 0.5 * K, K)[0] == pytest.approx(4500.0)      # linear in between


def test_kappa_one_gives_constant_budget():
    w = small_world(50); w["kappa"][:] = 1.0
    sim = _plant(w, years=30)
    assert np.allclose(sim["supply"][1:], w["npp"][None, :])


def _cap_bound_world(kappa, n=1):
    w = draw_worlds(n, 11)
    w["kappa"] = np.full(n, kappa)
    w["mu_c"] = np.zeros(n)
    w["mu_mult"] = np.ones_like(w["mu_mult"])
    w["mu"] = np.repeat(w["mu_bar"][:, None], 3, axis=1)
    w["M"] = np.full_like(w["M"], 1e4); w["r"] = np.full_like(w["r"], 0.3)
    return w


@pytest.mark.parametrize("kappa", [1.0, 1.5, 3.0])
def test_cap_bound_stand_follows_budget_recursion_and_approaches_K(kappa):
    """Demand >> supply: B' = exp(-mu) (B + S(B)); compare with the recursion and with K (1 - exp(-kappa mu t))."""
    w = _cap_bound_world(kappa)
    n0 = np.full_like(w["M"], 1e5)                     # enormous demand, so the cap binds from year 1
    sim = run_stand(w, n0, 60, sharpness=4.0)
    K = (w["npp"] / w["mu_bar"])[0]; npp = w["npp"][0]; mu = w["mu_bar"][0]
    B = sim["B"][0, 0]
    for t in range(1, 61):
        B = np.exp(-mu) * (B + npp * (1 + (kappa - 1) * max(0.0, 1 - B / K)))
        assert B == pytest.approx(sim["B"][t, 0], rel=2e-3)
    t = 60
    cont = K * (1 - np.exp(-kappa * mu * t))
    assert sim["B"][t, 0] == pytest.approx(cont, rel=0.12)   # discrete steps and starting stock, hence loose

