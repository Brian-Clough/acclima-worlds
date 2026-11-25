"""Prior register. Every number here is a PLACEHOLDER unless `basis` says otherwise.

Priors are deliberately wide. Uncertainty is information: the width of a prior is what tells us
which dataset is worth buying. Do not narrow a prior without recording the evidence in DECISIONS.md.
"""
from dataclasses import dataclass
import numpy as np

GROUPS = ("pioneer", "mid", "slow")  # placeholder functional groups; species mapping comes later


@dataclass(frozen=True)
class LogNormal:
    median: float
    sdlog: float
    units: str
    basis: str  # where the number came from, and its status

    def draw(self, rng, size):
        return self.median * np.exp(self.sdlog * rng.standard_normal(size))


# ---- world-level (shared by every cohort in a world) -------------------------------------------
NPP_WOOD = LogNormal(3000.0, 0.40, "kg C / ha / yr",
                     "PLACEHOLDER: wood NPP of mature western Amazon forest, order of magnitude only. "
                     "Replace from literature search and site productivity layers.")
MU_BAR = LogNormal(0.020, 0.35, "1 / yr",
                   "PLACEHOLDER: turnover rate of mature live biomass; tau = 1 / mu_bar (median 50 yr). "
                   "Defines K = NPP * tau.")
MU_COMP = LogNormal(0.030, 0.50, "1 / yr",
                    "PLACEHOLDER: extra stem mortality at full competition (scaled by 1 - phi).")
ROOT_SHOOT = LogNormal(0.17, 0.30, "-",
                       "Median is the IPCC planted-rainforest ratio used in the project memo (0.17); width is a placeholder.")
KAPPA_EXCESS = LogNormal(0.5, 0.80, "-",
                         "PLACEHOLDER: kappa = 1 + excess. Young-stand NPP budget at B = 0 is kappa x mature wood NPP; "
                         "it falls linearly to the mature value as live carbon B approaches K. Median kappa 1.5, 5-95% about 1.1-2.8. "
                         "Set before looking at its effect on any comparison with project documents.")
M0 = LogNormal(0.03, 0.50, "kg C / tree",
               "PLACEHOLDER: planting-stock carbon per seedling.")

# ---- group-level -------------------------------------------------------------------------------
# M: asymptotic tree carbon (WBE maximum size). r: approach rate of u = (m/M)^(1/4), r = a / (4 M^(1/4)).
# mu_mult: group mortality relative to mu_bar (mid is the reference, fixed at 1).
# n_ref: stems per ha of the group in a mature reference stand (after self-thinning).
GROUP_PRIORS = {
    "pioneer": dict(
        M=LogNormal(280.0, 0.50, "kg C / tree", "PLACEHOLDER: order of the Inga edulis asymptote in the project memo."),
        r=LogNormal(0.15, 0.30, "1 / yr", "PLACEHOLDER: gives ~25 kg C per tree at year 5."),
        mu_mult=LogNormal(2.5, 0.40, "-", "PLACEHOLDER: pioneers turn over faster (project memo uses ~20-25 yr lifespans)."),
        n_ref=None),
    "mid": dict(
        M=LogNormal(1500.0, 0.60, "kg C / tree", "PLACEHOLDER: order of the Cedrela/Handroanthus/Cedrelinga asymptotes."),
        r=LogNormal(0.050, 0.35, "1 / yr", "PLACEHOLDER."),
        mu_mult=None,
        n_ref=LogNormal(100.0, 0.50, "stems / ha", "PLACEHOLDER: mature reference stocking. Needs plot data (e.g. RAINFOR, ter Steege).")),
    "slow": dict(
        M=LogNormal(20000.0, 0.70, "kg C / tree", "PLACEHOLDER: order of the Dipteryx asymptote (project prior centred on 74 Mg AGB)."),
        r=LogNormal(0.0175, 0.35, "1 / yr", "PLACEHOLDER: gives ~1.5 Mg C per tree at year 40."),
        mu_mult=LogNormal(0.7, 0.30, "-", "PLACEHOLDER."),
        n_ref=LogNormal(15.0, 0.50, "stems / ha", "PLACEHOLDER: emergent stocking in mature forest.")),
}

# ---- scenario inputs ---------------------------------------------------------------------------
# Planting plan: stems per ha by group. Mapping from the project memo (Table 4), grouping is a placeholder:
# pioneer = Inga + Schizolobium (704); mid = Cedrela, Cedrelinga, Handroanthus + biodiversity group (258);
# slow = Dipteryx + Bertholletia (149). Total 1,111.
PLANTING_REFORESTATION = {"pioneer": 704.0, "mid": 258.0, "slow": 149.0}
PLANTING_SILVOPASTURE = {"pioneer": 0.0, "mid": 0.0, "slow": 150.0}

SURVIVAL_ALPHA_BETA = (8.0, 2.0)  # PLACEHOLDER Beta prior on establishment survival (mean 0.8)

# Baseline: pasture with possible natural regeneration (one pioneer-like cohort), same engine as the project.
P_REGEN_ALPHA_BETA = (1.0, 4.0)   # PLACEHOLDER: world-level probability that a hectare regenerates (mean 0.2)
N_REGEN = LogNormal(150.0, 0.70, "stems / ha", "PLACEHOLDER: pioneer stems per ha if the hectare regenerates.")

# ---- model constants (not drawn) ---------------------------------------------------------------
CAP_SHARPNESS = 4.0               # smooth-min exponent for the NPP supply cap; higher = harder cap
K_TOLERANCE_FACTOR = 1.5          # soft tolerance on log(B_WBE / K): about a factor of 1.5 each side (wide on purpose)
