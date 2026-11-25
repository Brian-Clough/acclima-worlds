import copy
import hashlib

import numpy as np
import pytest
import yaml

from acclima_worlds.prior import draw_worlds
from acclima_worlds.priorset import (DEFAULT_PATH, PlaceholderPriorsError, PriorSet, PriorSetError,
                                     TIERS, load_priorset)

# Hash of draw_worlds(50, 11) taken before priors moved into a file: moving them must not change a draw.
GOLDEN = "3ba68f68a3e0a055e71ad3fe4a7a73b2d0ed3b9daf909e81d02b20a472a4ce8a"


def raw():
    with open(DEFAULT_PATH) as f:
        return yaml.safe_load(f)


def test_default_draws_are_unchanged_by_the_move_to_a_file():
    w = draw_worlds(50, 11)
    h = hashlib.sha256(b"".join(np.ascontiguousarray(w[k]).tobytes() for k in sorted(w))).hexdigest()
    assert h == GOLDEN


def test_default_set_loads_and_every_entry_has_a_tier():
    ps = load_priorset()
    assert ps.groups == ("pioneer", "mid", "slow")
    assert all(e.tier in TIERS for e in ps.entries())
    assert ps.group("mu_mult", "mid") is None and ps.group("n_ref", "pioneer") is None


def test_every_default_entry_is_a_placeholder_until_someone_reviews_it():
    ps = load_priorset()
    assert set(ps.placeholders()) == {e.name for e in ps.entries()}


def test_gate_blocks_placeholders_and_stamps_when_allowed():
    ps = load_priorset()
    with pytest.raises(PlaceholderPriorsError, match="still placeholders"):
        ps.check_gate()
    stamp = ps.check_gate(allow_placeholders=True)
    assert "PLACEHOLDER PRIORS" in stamp and ps.fingerprint() in stamp


def test_gate_passes_with_empty_stamp_once_everything_is_reviewed():
    d = raw()
    for e in [*d["priors"].values(), *d["constants"].values(),
              *(p for g in d["group_priors"].values() for p in g.values())]:
        e.update(status="reviewed", reviewed_by="B. Clough", reviewed_on="2026-11-25", evidence="test")
    ps = PriorSet.from_dict(d)
    assert ps.placeholders() == [] and ps.check_gate() == ""


def test_fingerprint_changes_with_any_content_and_is_stable_otherwise():
    d = raw()
    a, b = PriorSet.from_dict(d), PriorSet.from_dict(copy.deepcopy(d))
    assert a.fingerprint() == b.fingerprint()
    d["priors"]["npp_wood"]["median"] = 3001.0
    assert PriorSet.from_dict(d).fingerprint() != a.fingerprint()


def test_methodology_set_is_a_fixed_value_and_draws_no_random_numbers():
    d = raw()
    d["priors"]["root_shoot"] = dict(dist="fixed", value=0.17, units="-", tier="structural",
                                     status="methodology-set", standard="VM0047 (test)",
                                     basis="Fixed by the methodology.")
    ps = PriorSet.from_dict(d)
    w = draw_worlds(30, 4, ps)
    assert np.all(w["root_shoot"] == 0.17)
    base = draw_worlds(30, 4)                      # fixing one prior must not shift the others' draws
    assert np.array_equal(w["npp"], base["npp"]) and np.array_equal(w["mu_bar"], base["mu_bar"])


@pytest.mark.parametrize("mutate, message", [
    (lambda d: d["priors"]["npp_wood"].update(tier="national"), "tier"),
    (lambda d: d["priors"]["npp_wood"].update(status="probably fine"), "status"),
    (lambda d: d["priors"]["npp_wood"].update(basis=""), "basis"),
    (lambda d: d["priors"]["npp_wood"].update(units=""), "units"),
    (lambda d: d["priors"]["npp_wood"].update(sdlog=0.0), "sdlog"),
    (lambda d: d["priors"]["npp_wood"].update(status="reviewed"), "reviewed_by"),
    (lambda d: d["priors"]["npp_wood"].update(status="reviewed", reviewed_by="x", reviewed_on="yesterday",
                                              evidence="e"), "YYYY-MM-DD"),
    (lambda d: d["priors"]["npp_wood"].update(status="methodology-set", standard="x"), "fixed"),
    (lambda d: d["priors"]["root_shoot"].update(dist="fixed", value=0.17), "methodology-set"),
    (lambda d: d["priors"]["root_shoot"].update(dist="fixed", value=0.17, status="methodology-set"), "standard"),
    (lambda d: d["priors"].pop("kappa_excess"), "kappa_excess"),
    (lambda d: d["priors"].update(mystery=d["priors"]["m0"]), "unknown"),
    (lambda d: d["group_priors"]["mid"].pop("M"), "missing group prior"),
    (lambda d: d["group_priors"].pop("slow"), "one entry per group"),
    (lambda d: d["constants"].pop("cap_sharpness"), "cap_sharpness"),
])
def test_malformed_prior_sets_are_rejected_with_a_clear_message(mutate, message):
    d = raw()
    mutate(d)
    with pytest.raises(PriorSetError, match=message):
        PriorSet.from_dict(d)


def test_draw_worlds_uses_the_prior_set_it_is_given():
    d = raw()
    d["priors"]["npp_wood"]["median"] = 6000.0
    shifted = draw_worlds(400, 3, PriorSet.from_dict(d))
    base = draw_worlds(400, 3)
    assert np.allclose(shifted["npp"], 2.0 * base["npp"])
