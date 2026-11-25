import numpy as np
from acclima_worlds import priors as P
from acclima_worlds.prior import draw_worlds


def test_seed_is_deterministic():
    a, b = draw_worlds(20, 7), draw_worlds(20, 7)
    for k in a:
        assert np.array_equal(a[k], b[k])


def test_priors_are_positive_and_have_expected_shapes():
    w = draw_worlds(200, 5)
    for k in ("npp", "mu_bar", "mu_c", "kappa", "root_shoot", "survival"):
        assert w[k].shape == (200,)
    for k in ("M", "r", "mu", "m0", "n_ref"):
        assert w[k].shape == (200, len(P.GROUPS))
    assert np.all(w["npp"] > 0) and np.all(w["M"] > 0) and np.all(w["r"] > 0)
    assert np.all(w["kappa"] >= 1.0)                       # kappa = 1 + a positive excess
    assert np.all((w["survival"] > 0) & (w["survival"] < 1))
    assert np.all(w["mu"][:, P.GROUPS.index("mid")] == w["mu_bar"])   # mid group is the turnover reference
