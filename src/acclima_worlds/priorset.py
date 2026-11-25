"""Prior sets: priors as data, with a tier and a status on every entry.

tier    structural | regional | trait | project   what a new project must revisit
status  placeholder | reviewed | evidence-based | methodology-set

The structure of the model is code. The numbers live in a prior set file (see priorsets/).
Reports and figures call `check_gate` so a placeholder prior cannot reach a headline output unnoticed.
"""
import datetime
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

TIERS = ("structural", "regional", "trait", "project")
STATUSES = ("placeholder", "reviewed", "evidence-based", "methodology-set")
DISTS = ("lognormal", "beta", "fixed")
WORLD_PRIORS = ("npp_wood", "mu_bar", "mu_comp", "root_shoot", "kappa_excess", "m0",
                "survival", "p_regen", "n_regen")
GROUP_KEYS = ("M", "r", "mu_mult", "n_ref")          # M and r are required for every group
CONSTANTS = ("cap_sharpness", "k_tolerance_factor")
DEFAULT_PATH = Path(__file__).resolve().parents[2] / "priorsets" / "peru_arr.yaml"


class PriorSetError(ValueError):
    """The prior set file is malformed."""


class PlaceholderPriorsError(RuntimeError):
    """A headline output was requested while placeholder priors are still in the set."""


def _check_common(name, d):
    if d.get("tier") not in TIERS:
        raise PriorSetError(f"{name}: tier must be one of {TIERS}, got {d.get('tier')!r}")
    status = d.get("status")
    if status not in STATUSES:
        raise PriorSetError(f"{name}: status must be one of {STATUSES}, got {status!r}")
    if not str(d.get("basis", "")).strip():
        raise PriorSetError(f"{name}: basis is required (where the number came from)")
    if status in ("reviewed", "evidence-based"):
        for k in ("reviewed_by", "reviewed_on", "evidence"):
            if not str(d.get(k, "")).strip():
                raise PriorSetError(f"{name}: status {status} needs {k}")
        try:
            datetime.date.fromisoformat(str(d["reviewed_on"]))
        except ValueError:
            raise PriorSetError(f"{name}: reviewed_on must be YYYY-MM-DD, got {d['reviewed_on']!r}")
    if status == "methodology-set" and not str(d.get("standard", "")).strip():
        raise PriorSetError(f"{name}: methodology-set needs `standard` naming the rule that sets it")


@dataclass(frozen=True)
class Prior:
    name: str
    dist: str
    params: dict
    units: str
    tier: str
    status: str
    basis: str
    meta: dict = field(default_factory=dict)       # reviewed_by, reviewed_on, evidence, standard

    @classmethod
    def from_dict(cls, name, d):
        d = dict(d)
        _check_common(name, d)
        dist = d.get("dist")
        if dist not in DISTS:
            raise PriorSetError(f"{name}: dist must be one of {DISTS}, got {dist!r}")
        keys = {"lognormal": ("median", "sdlog"), "beta": ("alpha", "beta"), "fixed": ("value",)}[dist]
        params = {}
        for k in keys:
            if k not in d:
                raise PriorSetError(f"{name}: {dist} prior needs {k}")
            params[k] = float(d[k])
        if dist == "lognormal" and not (params["median"] > 0 and params["sdlog"] > 0):
            raise PriorSetError(f"{name}: lognormal needs median > 0 and sdlog > 0")
        if dist == "beta" and not (params["alpha"] > 0 and params["beta"] > 0):
            raise PriorSetError(f"{name}: beta needs alpha > 0 and beta > 0")
        if dist == "fixed" and d["status"] != "methodology-set":
            raise PriorSetError(f"{name}: a fixed value must be status methodology-set "
                                "(a fixed value on any other status would hide uncertainty)")
        if d["status"] == "methodology-set" and dist != "fixed":
            raise PriorSetError(f"{name}: methodology-set priors must be dist: fixed")
        if not str(d.get("units", "")).strip():
            raise PriorSetError(f"{name}: units are required")
        meta = {k: d[k] for k in ("reviewed_by", "reviewed_on", "evidence", "standard") if k in d}
        return cls(name, dist, params, str(d["units"]), d["tier"], d["status"], str(d["basis"]), meta)

    def draw(self, rng, size):
        p = self.params
        if self.dist == "lognormal":
            return p["median"] * np.exp(p["sdlog"] * rng.standard_normal(size))
        if self.dist == "beta":
            return rng.beta(p["alpha"], p["beta"], size=size)
        return np.full(size, p["value"])           # fixed: consumes no random numbers

    def to_dict(self):
        return dict(name=self.name, dist=self.dist, params=self.params, units=self.units,
                    tier=self.tier, status=self.status, basis=self.basis, meta=self.meta)


@dataclass(frozen=True)
class Constant:
    name: str
    value: float
    tier: str
    status: str
    basis: str

    def to_dict(self):
        return dict(name=self.name, value=self.value, tier=self.tier, status=self.status, basis=self.basis)


@dataclass(frozen=True)
class PriorSet:
    name: str
    version: int
    groups: tuple
    priors: dict            # world-level, name -> Prior
    group_priors: dict      # group -> {key -> Prior}; absent key means "not used for this group"
    constants: dict         # name -> Constant

    @classmethod
    def from_dict(cls, d):
        for k in ("name", "version", "groups", "constants", "priors", "group_priors"):
            if k not in d:
                raise PriorSetError(f"prior set is missing `{k}`")
        groups = tuple(d["groups"])
        if len(set(groups)) != len(groups) or not groups:
            raise PriorSetError("groups must be a non-empty list of distinct names")
        priors = {n: Prior.from_dict(n, v) for n, v in d["priors"].items()}
        for n in WORLD_PRIORS:
            if n not in priors:
                raise PriorSetError(f"missing world-level prior `{n}`")
        extra = set(priors) - set(WORLD_PRIORS)
        if extra:
            raise PriorSetError(f"unknown world-level priors {sorted(extra)}")
        if set(d["group_priors"]) != set(groups):
            raise PriorSetError("group_priors must have exactly one entry per group")
        gp = {}
        for g, entries in d["group_priors"].items():
            bad = set(entries) - set(GROUP_KEYS)
            if bad:
                raise PriorSetError(f"{g}: unknown group priors {sorted(bad)}")
            for req in ("M", "r"):
                if req not in entries:
                    raise PriorSetError(f"{g}: missing group prior `{req}`")
            gp[g] = {k: Prior.from_dict(f"{k}.{g}", v) for k, v in entries.items()}
        consts = {}
        for n in CONSTANTS:
            if n not in d["constants"]:
                raise PriorSetError(f"missing constant `{n}`")
            c = dict(d["constants"][n])
            _check_common(n, c)
            consts[n] = Constant(n, float(c["value"]), c["tier"], c["status"], str(c["basis"]))
        extra = set(d["constants"]) - set(CONSTANTS)
        if extra:
            raise PriorSetError(f"unknown constants {sorted(extra)}")
        return cls(str(d["name"]), int(d["version"]), groups, priors, gp, consts)

    def entries(self):
        """Every prior and constant, in a fixed order."""
        out = [self.priors[n] for n in WORLD_PRIORS]
        for g in self.groups:
            out += [self.group_priors[g][k] for k in GROUP_KEYS if k in self.group_priors[g]]
        return out + [self.constants[n] for n in CONSTANTS]

    def group(self, key, g):
        """The group-level prior `key` for group `g`, or None if it is not used there."""
        return self.group_priors[g].get(key)

    def placeholders(self):
        return [e.name for e in self.entries() if e.status == "placeholder"]

    def fingerprint(self):
        """Short hash of the full content, so any output can name the assumptions that produced it."""
        blob = json.dumps(dict(name=self.name, version=self.version, groups=self.groups,
                               entries=[e.to_dict() for e in self.entries()]), sort_keys=True, default=str)
        return hashlib.sha256(blob.encode()).hexdigest()[:12]

    def label(self):
        return f"{self.name} v{self.version} [{self.fingerprint()}]"

    def check_gate(self, allow_placeholders=False):
        """Call before producing a headline output (figure, table, memo number).

        Returns the stamp that must appear on the output: empty when every entry has been reviewed,
        otherwise a PLACEHOLDER PRIORS line. Raises unless placeholders were explicitly allowed.
        """
        ph = self.placeholders()
        if not ph:
            return ""
        if not allow_placeholders:
            raise PlaceholderPriorsError(
                f"{len(ph)} of {len(self.entries())} priors in {self.label()} are still placeholders: "
                f"{', '.join(ph)}. Review them, or pass allow_placeholders=True to produce a stamped output.")
        return f"PLACEHOLDER PRIORS ({len(ph)} of {len(self.entries())}) in {self.label()}"


def load_priorset(path=DEFAULT_PATH):
    with open(path) as f:
        return PriorSet.from_dict(yaml.safe_load(f))
