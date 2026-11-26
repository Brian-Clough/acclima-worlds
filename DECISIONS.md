# Decisions log

## 2026-11-24 to 25: design agreed with the project owner (Brian)
- Architecture: prior predictive -> updated model -> posterior world simulation -> model updates. The Odisha pilot is the template for the idea, not the structure.
- Focus on live biomass. Other pools are added later through the pool interface. Pilot plot data are not assumed to be used: the pilot is dominated by dead wood and this is an ARR project; planting mixes describe time 0 better.
- The baseline is simulated in every world (same engine as the project). Chloris biomass is a benchmark, not an input.
- Growth comes from fundamental ecology (West-Brown-Enquist, size-structured cohorts), not from the project's fitted curves. The project curves may be compared against it later.
- K = NPP x tau, with tau tied to the mortality prior. K is a soft constraint on the metabolic-scaling asymptotes (both are uncertain, so neither is exact).
- The stand-level increment is also soft capped by an NPP budget S, separate from K. Young stands get a higher budget (kappa x mature NPP) that falls to the mature value as B approaches K.
- Priors start wide. Uncertainty is treated as information about which dataset is worth getting.
- Build one piece at a time, one PR per piece.

## 2026-11-25 kappa prior (set before comparing with any project document)
- kappa = 1 + excess, excess log-normal (median 0.5, log-sd 0.8): kappa about 1.1 to 2.8 (5th to 95th percentile), median 1.5. Placeholder.

## 2026-11-25 priors are data, with tiers and a status gate (agreed with the project owner)
- Setting the prior set is the first analysis of any new project and gets deliberate thought. The pipeline is automated, with friction only where a wrong assumption would propagate silently: priors, project config and reported results. Routine re-runs do not loop back through the config.
- Four tiers say what a new project must revisit. **Structural** (confirm once): cap sharpness, K tolerance, root:shoot. **Regional** (set for each biome): wood NPP, turnover, competition mortality, kappa, mature stocking. **Trait** (revisit when the planting mix or species mapping changes): M, r and mortality multiplier by group. **Project/site** (always filled in): seedling stock, survival, regeneration, planting plans.
- Every prior has a status: `placeholder`, `reviewed`, `evidence-based` or `methodology-set`. Reviewed and evidence-based entries record who, when and the evidence. A headline output (figure, table, memo number) calls `check_gate`: placeholders block it unless explicitly allowed, and an allowed run carries a PLACEHOLDER PRIORS stamp naming the prior set fingerprint.
- `methodology-set` is for values a program dictates (root:shoot may become one). It is a fixed value that names the standard that sets it, so it is never reported as an estimate and can become a normal prior if a program allows a range.
- The 3/4 metabolic scaling exponent stays in code. Moving away from it is a reevaluation of the underlying science, not a config change.
- The memo's prior summary table is standard in model memos so a reader can see which priors rest on evidence and which are close to placeholders. The generator comes in a later piece.
- Moving the priors into `priorsets/peru_arr.yaml` changed no number: `draw_worlds(4, 11)` matches the pre-move draws to 1e-9 (reference values pinned in `tests/test_priorset.py`). root:shoot keeps its placeholder width for now.

## 2026-11-26 sharing of the NPP budget is a placeholder (project owner doubts every candidate rule)
- Basic rule, as built in `cohort.py`: every cohort realizes the same fraction phi of its own potential growth. This is not equal absolute shares: a larger cohort has larger potential growth and takes more carbon. It is a neutral baseline, not a claim about how forest competition works.
- The project owner does not think this is the ecologically correct rule, and does not think a size-dependent rule is correct either. The question is open. We keep the basic rule for now.
- It matters: with placeholder priors the cap binds in about 94% of worlds at year 10, so the rule decides who gets the limited growth in most worlds. It can move the pioneer / mid / slow mix and through it the carbon trajectory.
- Candidate rules, all swapped in through `share_budget`: equal fraction (current); mass-weighted (larger cohorts take disproportionately more, as in asymmetric competition for light); group-specific weights for shade tolerance (a separate axis from size); a light-capture model.
- Next step: a sensitivity run on the same worlds under alternative rules (`scripts/sharing_sensitivity.py`) to measure how much carbon and group mix move. If they barely move, the question waits. If they move a lot, it goes on the list for the first lit-review pilot, with wood NPP and mu_bar.
