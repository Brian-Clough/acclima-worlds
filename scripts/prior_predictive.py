"""Prior predictive run: draw worlds, weight by K-consistency, run project and baseline, summarise.

Pre-registration note: this run only looks at the prior. No prior has been tuned to its output.
Usage: python scripts/prior_predictive.py [n_worlds] [seed]
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import numpy as np
from acclima_worlds import priors as P
from acclima_worlds.prior import draw_worlds
from acclima_worlds.envelope import k_stock, trait_implied_stock, k_consistency_weights, effective_sample_size
from acclima_worlds.scenarios import run_project, run_baseline
from acclima_worlds.accounting import creditable_tco2e, weighted_quantile
from acclima_worlds.pools import C_TO_CO2E

N = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 20261124
YEARS = 40
OUT = pathlib.Path(__file__).resolve().parents[1] / "docs"


def run(n=N, seed=SEED, years=YEARS):
    w = draw_worlds(n, seed)
    wt, log_ratio = k_consistency_weights(w)
    base = run_baseline(w, years)
    ref = run_project(w, P.PLANTING_REFORESTATION, years)
    silvo = run_project(w, P.PLANTING_SILVOPASTURE, years)
    cred = {"reforestation": creditable_tco2e(ref, base, w), "silvopasture": creditable_tco2e(silvo, base, w)}
    return dict(world=w, weights=wt, log_ratio=log_ratio, baseline=base, project={"reforestation": ref, "silvopasture": silvo}, creditable=cred)


def summarise(res):
    w, wt = res["world"], res["weights"]
    n = len(wt)
    u = np.full(n, 1.0 / n)
    lines = []
    ess = effective_sample_size(wt)
    K = k_stock(w) / 1000.0
    Bw = trait_implied_stock(w)[0] / 1000.0
    lines.append(f"worlds {n}, seed {SEED}, effective sample size after K weighting {ess:.0f} ({100*ess/n:.0f}%)")
    q = [0.05, 0.5, 0.95]
    lines.append("K = NPP x tau (tC/ha), p5/p50/p95 prior: " + " / ".join(f"{weighted_quantile(K, u, x):.0f}" for x in q))
    lines.append("B_WBE trait-implied mature stock (tC/ha), prior: " + " / ".join(f"{weighted_quantile(Bw, u, x):.0f}" for x in q))
    lines.append("kappa (young-stand budget multiplier), prior p5/p50/p95: " + " / ".join(f"{weighted_quantile(w['kappa'], u, x):.2f}" for x in q))
    lines.append("ratio B_WBE / K, prior: " + " / ".join(f"{weighted_quantile(np.exp(res['log_ratio']), u, x):.2f}" for x in q))
    lines.append("share of prior worlds within a factor 1.5 of K: " + f"{np.mean(np.abs(res['log_ratio']) < np.log(1.5)):.2f}")
    lines.append("")
    lines.append("Creditable carbon, project minus baseline, live AGB + BGB (tCO2e/ha), p5 / p50 / p95")
    lines.append("activity       year  prior (unweighted)      K-weighted")
    for act, c in res["creditable"].items():
        for yr in (5, 10, 20, 40):
            a = [weighted_quantile(c[yr], u, x) for x in q]
            b = [weighted_quantile(c[yr], wt, x) for x in q]
            lines.append(f"{act:<14} {yr:>3}   {a[0]:6.0f} {a[1]:6.0f} {a[2]:6.0f}      {b[0]:6.0f} {b[1]:6.0f} {b[2]:6.0f}")
    lines.append("")
    ref = res["project"]["reforestation"]
    for yr in (5, 10, 20, 40):
        lines.append(f"reforestation year {yr}: share of worlds where the NPP cap binds (phi < 0.9): {np.mean(ref['phi'][yr] < 0.9):.2f}; "
                     f"median phi {np.median(ref['phi'][yr]):.2f}")
    B40 = ref["B"][-1] / 1000.0
    lines.append(f"reforestation live AGB at year 40 / K: p5/p50/p95 = " + " / ".join(f"{weighted_quantile(B40 / K, u, x):.2f}" for x in q)
                 + f"; share of worlds above K: {np.mean(B40 > K):.2f}")
    rate = (res["creditable"]["reforestation"][-1] / YEARS)
    lines.append("reforestation mean creditable rate over 40 yr (tCO2e/ha/yr), p5/p50/p95 prior: "
                 + " / ".join(f"{weighted_quantile(rate, u, x):.1f}" for x in q))
    return "\n".join(lines)


def figure(res, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    w, wt = res["world"], res["weights"]
    n = len(wt); u = np.full(n, 1.0 / n)
    yrs = np.arange(YEARS + 1)
    colors = {"reforestation": "#1f6fb4", "silvopasture": "#c8660a"}
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.6), gridspec_kw={"width_ratios": [1.35, 1, 1]})
    a = ax[0]
    for act, c in res["creditable"].items():
        lo = [weighted_quantile(c[t], wt, 0.05) for t in yrs]
        md = [weighted_quantile(c[t], wt, 0.5) for t in yrs]
        hi = [weighted_quantile(c[t], wt, 0.95) for t in yrs]
        md_u = [weighted_quantile(c[t], u, 0.5) for t in yrs]
        a.fill_between(yrs, lo, hi, color=colors[act], alpha=0.18, lw=0)
        a.plot(yrs, md, color=colors[act], lw=2)
        a.plot(yrs, md_u, color=colors[act], lw=1, ls="--")
        a.text(40.6, md[-1], act, color=colors[act], va="center", fontsize=10)
    a.axhline(0, color="#888", lw=0.8)
    a.set_xlim(0, 52); a.set_xlabel("years since planting"); a.set_ylabel("creditable carbon, tCO2e / ha")
    a.set_title("A. Prior predictive creditable carbon\nmedian and 5-95% (K-weighted); dashed = unweighted median", fontsize=10, loc="left")
    b = ax[1]
    ref = res["project"]["reforestation"]
    frac = [np.mean(ref["phi"][t] < 0.9) for t in yrs[1:]]
    medphi = [np.median(ref["phi"][t]) for t in yrs[1:]]
    b.plot(yrs[1:], frac, color="#1f6fb4", lw=2)
    b.plot(yrs[1:], medphi, color="#555", lw=2, ls="-.")
    b.text(41, frac[-1], "share of worlds\nwhere cap binds", color="#1f6fb4", fontsize=9, va="center")
    b.text(41, medphi[-1] - 0.06, "median phi\n(growth realised)", color="#555", fontsize=9, va="center")
    b.set_ylim(0, 1.05); b.set_xlim(0, 56); b.set_xlabel("years since planting")
    b.set_title("B. NPP supply cap, reforestation\nphi = realised / potential growth", fontsize=10, loc="left")
    c = ax[2]
    lr = res["log_ratio"]
    c.hist(np.exp(lr), bins=np.geomspace(0.05, 20, 50), color="#777", alpha=0.8)
    c.axvspan(1 / P.K_TOLERANCE_FACTOR, P.K_TOLERANCE_FACTOR, color="#1f6fb4", alpha=0.15)
    c.set_xscale("log"); c.set_xlabel("B_WBE / K  (trait-implied mature stock / NPP x tau)")
    c.set_ylabel("prior worlds")
    c.text(1.0, c.get_ylim()[1] * 0.93, "tolerance\n(factor 1.5)", ha="center", fontsize=9, color="#1f6fb4")
    c.set_title("C. Do the traits agree with K?", fontsize=10, loc="left")
    for x in ax:
        x.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.005, "All priors are placeholders (see src/acclima_worlds/priors.py). Prior only: no data used.", fontsize=8, color="#555")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(path, dpi=140)


if __name__ == "__main__":
    res = run()
    txt = summarise(res)
    print(txt)
    OUT.mkdir(exist_ok=True)
    (OUT / "prior_predictive_summary.txt").write_text(txt + "\n")
    figure(res, OUT / "prior_predictive.png")
