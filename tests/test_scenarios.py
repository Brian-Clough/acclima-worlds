import numpy as np
from acclima_worlds import priors as P
from acclima_worlds.prior import draw_worlds
from acclima_worlds.cohort import run_stand
from acclima_worlds.scenarios import run_project, run_baseline
from acclima_worlds.accounting import creditable_tco2e


def small_world(n=50, seed=1):
    return draw_worlds(n, seed)


def test_project_without_planting_equals_nothing():
    w = small_world(20)
    sim = run_stand(w, np.zeros_like(w["M"]), 10)
    assert np.all(sim["B"] == 0)


def test_baseline_without_regeneration_has_no_change():
    w = small_world(100); w["regen"][:] = 0
    base = run_baseline(w, 40)
    proj = run_project(w, P.PLANTING_REFORESTATION, 40)
    cred = creditable_tco2e(proj, base, w)
    assert np.all(base["B"] == 0)
    assert np.all(cred[-1] > 0)


def test_creditable_is_project_minus_baseline_in_tco2e():
    w = small_world(30); w["regen"][:] = 0
    proj = run_project(w, P.PLANTING_REFORESTATION, 10)
    base = run_baseline(w, 10)
    cred = creditable_tco2e(proj, base, w)
    expect = (proj["B"][10] - proj["B"][0]) * (1 + w["root_shoot"]) * (44 / 12) / 1000.0
    assert np.allclose(cred[10], expect, rtol=1e-9)
