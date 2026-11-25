# AcClima worlds

Private repo. A world generator for the AcClima ARR project: a prior predictive model, an update step, posterior worlds, and a loop that brings pilot, monitoring and remote-sensing data back into the model.

Rules
- Any number that goes into a memo or report comes from a script in this repo.
- One piece per branch and PR, with tests. `main` only holds reviewed work.
- Every prior is a placeholder unless `src/acclima_worlds/priors.py` gives a source. Priors start wide on purpose.
- A choice is written to `DECISIONS.md` before a result is used to pick between designs. Do not tune a prior to match a project document.
- Credited pools: live biomass only for now, built so other pools can be added without refactoring.
- No plot allocation or layout work without explicit go-ahead from the project owner.

See `DESIGN.md` for the loop and the modules.

Run the tests: `pip install -r requirements.txt && python -m pytest -q`
