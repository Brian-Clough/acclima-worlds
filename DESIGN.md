# Design

## The loop
1. **Prior predictive:** draw worlds from assumptions alone and check they are plausible.
2. **Update:** condition on data (remote sensing, plots, early monitoring) to get the posterior.
3. **Posterior worlds:** many draws, each an internally consistent trajectory of live carbon, project and baseline.
4. **Simulate:** run surveys, monitoring designs and accounting on worlds where the truth is known.
5. **New data** arrives and the loop returns to step 2.

Creditable carbon is project minus baseline, computed inside every world, so its uncertainty is integrated over the whole posterior. Chloris biomass is a benchmark to compare against, not an input.

## Modules
Each has a fixed interface and a deliberately basic first version, so a later version does not touch the others.

| Module | Basic version | Later |
|---|---|---|
| `priors`, `prior` | placeholder priors, one parameter draw per world | elicited priors, hierarchy over sites |
| `cohort` | West-Brown-Enquist cohorts sharing an NPP budget | size-asymmetric sharing, recruitment |
| `envelope` | K = NPP x tau consistency weights | other evidence on K |
| `pools` | live biomass (AGB, BGB) | dead wood, litter, soil |
| `scenarios` | project and baseline on the same engine | disturbance, replanting |
| `accounting` | project minus baseline | methodology rules, buffer, Chloris check |
| observation models, inference, simulation, export | not yet | |

## The biophysical envelope
- **Stock:** K = NPP_wood x tau is the equilibrium live carbon (kg C/ha). tau = 1/mu_bar, tied to the mortality prior.
- **Flow:** S(B) is the NPP budget (kg C/ha/yr), a cap on stand growth. S = NPP[1 + (kappa - 1) max(0, 1 - B/K)], so a young stand gets up to kappa times the mature value and settles to NPP as B approaches K.
- With the cap binding and loss mu B, dB/dt = kappa mu (K - B): exponential approach to K with time constant tau/kappa.
- Far from the cap, each cohort grows at its own West-Brown-Enquist rate, du/dt = r(1 - u) with u = (m/M)^(1/4).
- Both the K estimate and the trait-implied asymptotes are soft: worlds are weighted by log(B_WBE/K) with a log-normal tolerance (factor 1.5).

Assumptions to revisit: loss is a fixed fraction of the stock; S(B) is linear in B; mean-tree cohorts; the reference mature stocking by group is a placeholder.
