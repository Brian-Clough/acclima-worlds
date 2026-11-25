import numpy as np
import pytest
from acclima_worlds.prior import draw_worlds
from acclima_worlds.cohort import wbe_mass
from acclima_worlds.envelope import mean_mass_exponential_age, k_stock, k_consistency_weights, effective_sample_size


def small_world(n=50, seed=1):
    return draw_worlds(n, seed)


def test_steady_state_flux_identity():
    # With continuous recruitment at m0 and hazard mu, flux = N mu (mbar - m0).
    w = small_world(30)
    M, r, m0 = w["M"], w["r"], w["m0"]
    mu = np.full_like(w["mu"], 0.01)   # small hazard: discrete and continuous age weights agree
    mbar = mean_mass_exponential_age(M, r, m0, mu, horizon=2000)
    t = np.arange(2000.0)
    m = wbe_mass(t[None, None, :], M[..., None], r[..., None], m0[..., None])
    g = np.gradient(m, axis=-1)
    wt = mu[..., None] * np.exp(-mu[..., None] * t)
    flux = (wt * g).sum(-1)
    assert np.allclose(flux, mu * (mbar - m0), rtol=2.5e-2, atol=1e-3)


def test_mean_mass_limits():
    M = np.array([[100.0]]); m0 = np.array([[1.0]])
    fast = mean_mass_exponential_age(M, np.array([[50.0]]), m0, np.array([[0.02]]))
    assert fast[0, 0] == pytest.approx(100.0, rel=0.05)   # reaches M almost at once


def test_weights_normalised_and_ess_sensible():
    w = small_world(500)
    wt, lr = k_consistency_weights(w)
    assert wt.sum() == pytest.approx(1.0)
    assert 1.0 <= effective_sample_size(wt) <= 500.0
    assert np.all(np.isfinite(lr))
