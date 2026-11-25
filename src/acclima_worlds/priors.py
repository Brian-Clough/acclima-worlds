"""Defaults for the Peru ARR project.

The priors themselves are data: see priorsets/peru_arr.yaml and priorset.py. This module loads the
default set and holds the scenario inputs that are not priors yet (planting plans). Planting plans and
groups move into a project config in a later piece.
"""
from .priorset import load_priorset

DEFAULT = load_priorset()
GROUPS = DEFAULT.groups

CAP_SHARPNESS = DEFAULT.constants["cap_sharpness"].value
K_TOLERANCE_FACTOR = DEFAULT.constants["k_tolerance_factor"].value

# Planting plan: stems per ha by group. Mapping from the project memo (Table 4), grouping is a placeholder:
# pioneer = Inga + Schizolobium (704); mid = Cedrela, Cedrelinga, Handroanthus + biodiversity group (258);
# slow = Dipteryx + Bertholletia (149). Total 1,111.
PLANTING_REFORESTATION = {"pioneer": 704.0, "mid": 258.0, "slow": 149.0}
PLANTING_SILVOPASTURE = {"pioneer": 0.0, "mid": 0.0, "slow": 150.0}
