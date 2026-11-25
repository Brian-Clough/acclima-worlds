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
