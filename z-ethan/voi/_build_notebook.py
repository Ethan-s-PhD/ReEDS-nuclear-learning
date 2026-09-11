"""Generate voi.ipynb — the decision value of cost information (EVPI / EVPPI / EVSI,
the Bayes sequential stopping decision, the grant cut-off year).

Same convention as the other z-ethan analysis builders: the notebook is the
deliverable; this builder exists so it can be regenerated and diffed as plain
python. Edit cell sources here, re-run to regenerate, then execute the notebook
headless on the playground-env kernel from z-ethan/voi/ (`_run_voi.py`).

Registered in z-ethan/voi/methods.md (2026-09-09, BEFORE emission and BEFORE any
run). Tables pNN_*.csv, figures yNN_*.png. All markdown is plain technical
English: short sentences, active voice, every term of art explained at first use.

Reuse (verbatim, then gated): the five-anchor requirement machinery of
rate_design/_build_notebook_v2.py (S1 cell + the 5a patches), the stage-3 observer
as copied in rate_design/_build_notebook.py (sweep_ci; seed 20260901, v1 draw
order), and the stage-3 ledger/exceedance construction of
bridge_detection/_build_notebook_stage3.py.
"""
import nbformat as nbf

nb = nbf.v4.new_notebook()
nb.metadata = {
    "kernelspec": {"name": "python3", "display_name": "Python 3 (ipykernel)", "language": "python"},
    "language_info": {"name": "python", "version": "3.12"},
}

C = []


def md(src):
    C.append(nbf.v4.new_markdown_cell(src))


def code(src):
    C.append(nbf.v4.new_code_cell(src))


# ====================================================================================
md(r"""# The decision value of cost information

**Who this is for.** A reader who advises on nuclear deployment targets and
subsidy design and wants to know, in dollars, what not knowing the technology's
cost path costs, what watching the first completed units buys, when to stop
paying, and when grant funding for the first units can end. No statistics
background is assumed; every term of art is explained in parentheses at its
first use.

**The setting.** The paper prices the subsidy each deployment schedule needs in
10,000 "cost worlds" (complete, internally consistent build-cost futures for
small modular reactors, SMRs). The government does not know which world it is
in. It can commit now, or it can watch the reported costs of the units completed
each year and update. Figure 5 today reports precision: how much is committed
when a spending-cap alarm fires, and how wide the uncertainty on the required
credit still is. This notebook replaces precision with decision value:

1. **EVPI, EVPPI, EVSI** (the expected value of perfect, partial-perfect and
   sample information) on the credit-scale decision, in 2024 billion dollars.
2. **The stopping decision as a Bayes sequential decision**: each year the
   government holds a posterior probability that the bill will exceed a cap and
   stops when that probability crosses a threshold chosen to minimize expected
   loss — not to hit a fixed false-alarm budget. Today's 5% alarm is kept only
   as a reference point, with the false-stop price it implies.
3. **The grant cut-off year** as an output: a coverage-versus-grant-dollars
   frontier for the demonstration window (the build years in which grants pay
   the part of the requirement above the statutory credit ceiling), and, with
   learning, an abandonment trigger for worlds that will never become
   credit-feasible.

Gates, kill rules and predictions were fixed in `methods.md` before this
notebook was first executed. Tables are `p01` and up; figures `y01` and up.
Register: information, never a recommendation — no benefit of nuclear delivery
is priced; where two error costs trade off, the exchange rate is the reader's
parameter. Run on the **playground-env** kernel.""")

code(r"""import json
import os
import re
import time
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

import sys
sys.path.insert(0, str(Path.cwd().parent))
import plotstyle as ps

ps.apply()
pd.set_option("display.width", 220)

HERE = Path.cwd()
assert HERE.name == "voi", f"run from z-ethan/voi/, not {HERE}"
REPO = HERE.parents[1]
EXPORTS = HERE / "exports"
FIGURES = HERE / "figures"
EXPORTS.mkdir(exist_ok=True)
FIGURES.mkdir(exist_ok=True)

MC_EXPORTS = REPO / "z-ethan" / "mc" / "exports"
CHECKS3 = REPO / "z-ethan" / "step3_checks" / "exports"
S3ANALYSIS = REPO / "z-ethan" / "step3_analysis" / "exports"
BRIDGE = REPO / "z-ethan" / "bridge_detection" / "exports"
RD_EXPORTS = REPO / "z-ethan" / "rate_design" / "exports"

# ---- registered constants (methods.md) --------------------------------------------
SEED = 20260901           # the rate_design v1 observer seed (u10 reproduces exactly)
SEED_VOI = 20260909       # every NEW random draw in this notebook
TOL_SHORT = 0.01          # delivery cushion, statutory rate points (r03-certified)
DISPLAY_CUT = 0.03        # the paper's display allowance (Ethan 2026-09-09), companion
CUTS = {"reg": TOL_SHORT, "disp": DISPLAY_CUT}
UNIT_MW = 300
LEVELS = [(0.15, 0.05), (0.30, 0.10), (0.50, 0.20)]   # (sigma, tau); mid = headline
LV_MID = (0.30, 0.10)
LV_SMALL = (1e-3, 1e-3)   # the small-noise pass (separate seed)
R = 10                    # noise histories per truth world
N_TRUTH = 500             # truth worlds per schedule
CAPS = [0.50, 0.60]       # statutory ceilings (0.50 = today's stacked maximum)
ALPHAS = [0.5, 0.75, 0.90, 0.95]
ALPHA_HEAD = 0.90         # the paper's coverage rule
RHOS = [0.1, 0.25, 0.5, 1.0, 2.0]     # false-stop price, x the P50 bill (reader's parameter)
RHO_FINE = np.logspace(np.log10(0.02), np.log10(10.0), 60)
XMULTS = [1.0, 1.25, 1.5, 2.0]        # spending caps, x the P50 bill
X_HEAD = 1.5
W_PRIMARY, W_SENS = 2035, 2033        # today's windows (reproduction only)
QS = [5, 25, 50, 75, 95]
ESS_FLOOR = 100.0
N_BOOT = 1000
MIN_SIDE = 30                          # K4: worlds needed on each side of a split
PCTS = ["p05", "p25", "p50", "p75", "p95"]   # the five-anchor map
INTERIOR = ["p25", "p50", "p75"]
VERDICT = []                           # (kind, name, result, detail) rows -> p90

def lvtag(lv):
    return f"s{int(round(lv[0] * 100)):02d}t{int(round(lv[1] * 100)):02d}"

LV_LABEL = {LEVELS[0]: "light observation noise (σ 0.15, τ 0.05)",
            LEVELS[1]: "medium noise (σ 0.30, τ 0.10)",
            LEVELS[2]: "heavy noise (σ 0.50, τ 0.20)",
            LV_SMALL: "near-perfect observation (σ = τ = 0.001)"}
LV_STYLE = {LEVELS[0]: dict(lw=1.0, alpha=0.45), LEVELS[1]: dict(lw=1.8, marker="o", ms=2.5),
            LEVELS[2]: dict(lw=1.0, alpha=0.7, ls="--"), LV_SMALL: dict(lw=0.9, ls=":")}

def price_axis(ax, p50, label):
    # x = price in 2024 $B (log); a secondary axis on top reads the same price as a multiple of
    # the schedule's median-world bill
    ax.set_xscale("log")
    ax.set_xlabel(label)
    sec = ax.secondary_xaxis("top", functions=(lambda x, p=p50: x / p, lambda m, p=p50: m * p))
    sec.set_xlabel("× median-world bill", fontsize=6.5, labelpad=2)
    sec.tick_params(labelsize=6)
    return sec
print("constants loaded")
""")

# ====================================================================================
md(r"""## Data and shared machinery

Everything below is offline: the 10,000-world Monte Carlo ensemble, the 30
model-run anchors (five per schedule: the cheapest 5%, 25%, 50%, 75% and most
expensive 95% cost worlds), the published required credit rates and outlays
for those anchors, the mandate build calendar, and the per-world subsidy
bills from the bridge-detection notebooks. The requirement machinery is the
five-anchor version of `rate_design/_build_notebook_v2.py`, copied line for
line and then checked against its frozen exports (gate G0) before anything new
is computed.""")

code(r"""# ---- the MC ensemble --------------------------------------------------------------
Z = np.load(MC_EXPORTS / "mc_perdraw.npz")
META = json.loads(str(Z["meta_json"]))
assert META["n_draws"] == 10000 and META["master_seed"] == 20260715, META
YI = {int(y): i for i, y in enumerate(Z["years"])}

SCHEDULES = ["eia", "aj", "iaea", "mck", "cop28", "eo"]  # ambition order
assert SCHEDULES == list(ps.SCHED_ORDER), ps.SCHED_ORDER
AB2TOK = {"eia": "eia_aeo_high", "aj": "abou_jaoude", "iaea": "iaea_high",
          "mck": "mckinsey", "cop28": "cop28", "eo": "eo2025"}
TOK2AB = {v: k for k, v in AB2TOK.items()}
NAME2AB = {str(n): TOK2AB[str(t)] for n, t in zip(Z["sched_order"], Z["scen_tokens"])}
WCOLS = [str(c) for c in Z["world_columns"]]
DIALS = {ab: Z[f"worlds_{AB2TOK[ab]}"] for ab in SCHEDULES}          # (10000, 13)
LR_SMR = {ab: DIALS[ab][:, WCOLS.index("lr_smr")] for ab in SCHEDULES}

reg_smr = pd.concat([pd.read_csv(MC_EXPORTS / "smr100" / "selected_draws.csv"),
                     pd.read_csv(MC_EXPORTS / "smr100" / "selected_draws_p25p75.csv")],
                    ignore_index=True)
reg_smr["ab"] = reg_smr["schedule"].map(NAME2AB)
assert len(reg_smr) == 30 and reg_smr["ab"].notna().all()
ANCH = {ab: {} for ab in SCHEDULES}
for _, r in reg_smr.iterrows():
    ANCH[r["ab"]][r["percentile"]] = int(r["draw_index"])
assert all(set(ANCH[ab]) == set(PCTS) for ab in SCHEDULES)

# ---- discount rate and price level (must reproduce the study constants) -----------
FIN_DIR = REPO / "inputs" / "financials"
sys_fin = pd.read_csv(FIN_DIR / "financials_sys_ATB2024.csv")
infl = pd.read_csv(FIN_DIR / "inflation_default.csv")
sys_fin = sys_fin.merge(infl, on="t", how="left")
sys_fin["d_nom"] = ((1 - sys_fin["debt_fraction"]) * (sys_fin["rroe_nom"] - 1)
                    + sys_fin["debt_fraction"] * (sys_fin["interest_rate_nom"] - 1)
                      * (1 - sys_fin["tax_rate"]) + 1)
sys_fin["d_real"] = sys_fin["d_nom"] / sys_fin["inflation_rate"]
_s = sys_fin.set_index("t")["d_real"].reindex(range(1990, 2051)).ffill()
DR = float(np.mean(_s.loc[np.arange(2010, 2051)].to_numpy(float)))
assert round(DR, 4) == 1.0455, DR
_infl = infl.set_index("t")["inflation_rate"]
D2224 = float(_infl.loc[2023] * _infl.loc[2024])
assert 1.0 < D2224 < 1.2, D2224

# ---- mandate additions ------------------------------------------------------------
duals3 = pd.read_csv(CHECKS3 / "duals_by_year.csv")
FLOOR = duals3[duals3["t"] <= 2030].groupby("case")["mandate_MW"].max()
duals3["program_MW"] = (duals3["mandate_MW"]
                        - duals3["case"].map(FLOOR).fillna(0.0)).clip(lower=0.0)
DCASE = {c: g.set_index("t") for c, g in duals3.groupby("case")}

# ---- published tables -------------------------------------------------------------
t08 = pd.read_csv(S3ANALYSIS / "t08_rental_transfer.csv").set_index("case")
t09 = pd.read_csv(S3ANALYSIS / "t09_required_itc.csv")
t09r = t09[t09["status"] == "rate"].set_index(["case", "t"])["i_model_headline"]
t12 = pd.read_csv(S3ANALYSIS / "t12_fiscal_comparison.csv").set_index("case")

def rate_of(case, t):
    v = t09r.get((case, t), 0.0)
    return float(v) if np.isfinite(v) else 0.0

cens = (t09[t09["itc_insufficient"].fillna(False).astype(bool)]
        if "itc_insufficient" in t09.columns else t09.iloc[0:0])
CENSORED = set()
for _, r in cens.iterrows():
    parts = str(r["case"]).split("_")
    if len(parts) >= 3 and parts[0] == "smr100":
        CENSORED.add(("_".join(parts[1:-1]), int(r["t"])))
print("censored anchor year-cells (schedule, year):", sorted(CENSORED))

# ---- per-world bills (five-anchor run) + the certificate band ---------------------
BW = np.load(BRIDGE / "b07_bills_perworld_5a.npz")
E5 = float(BW["e5_band"])
BAND = {"base": 1.0, "lo": 1.0 - E5, "hi": 1.0 + E5}
BILL_YEARS = [int(y) for y in BW["obs_years"]]
assert BILL_YEARS == list(range(2031, 2051))
B2050 = {ab: BW[f"b2050_{ab}"] for ab in SCHEDULES}
BILLS_T = {ab: BW[f"bills_{ab}"] for ab in SCHEDULES}          # (10000, 20) cumulative PV
g0_fail = []
for ab in SCHEDULES:
    for p in PCTS:
        pub = float(t08.loc[f"smr100_{ab}_{p}", "PV_rental_transfer_2024B"])
        if abs(B2050[ab][ANCH[ab][p]] - pub) > 0.051:
            g0_fail.append((ab, p))
assert not g0_fail, g0_fail
P50BILL = {ab: float(t08.loc[f"smr100_{ab}_p50", "PV_rental_transfer_2024B"]) for ab in SCHEDULES}
print(f"five-anchor certificate band E5 = {E5:.2f}; bills reproduce t08 at all 30 anchors")
print("P50 bills (2024 $B):", {k: round(v, 1) for k, v in P50BILL.items()})
""")

code(r"""# ---- the requirement map (rate_design v2 S1 cell, five-anchor form) ---------------
ADD, DISC, BUILD_TS = {}, {}, {}
IREF, IW, OCCW, NEED = {}, {}, {}, {}
REFC, FSTAR, COVER, BINDY, RATIO = {}, {}, {}, {}, {}
KAPPA, KAP_RES, SPREF, IBAR, WPRICE = {}, {}, {}, {}, {}
TOPKNOT_PCT, UPCLAMP = {}, {}
g1_fail = []

for ab in SCHEDULES:
    d0 = DCASE[f"smr100_{ab}_p05"]
    build_ts = [int(t) for t in d0.index if t >= 2026 and d0.loc[t, "program_MW"] > 0]
    prog = np.array([d0.loc[t, "program_MW"] for t in build_ts])
    add = np.diff(prog, prepend=0.0).clip(min=0.0)
    disc = np.array([DR ** -(t - 2026) for t in build_ts])
    keep = add > 0
    BUILD_TS[ab] = [t for t, k in zip(build_ts, keep) if k]
    ADD[ab] = add[keep]
    DISC[ab] = disc[keep]

    occ = Z[f"occ_{AB2TOK[ab]}_smr"]
    occ_t = np.stack([occ[:, YI[t]] for t in BUILD_TS[ab]], axis=1)  # 2022 $/kW
    OCCW[ab] = occ_t * D2224                                        # 2024 $/kW
    cases = {p: f"smr100_{ab}_{p}" for p in PCTS}

    iw = np.empty_like(occ_t)
    topknot = np.empty(len(BUILD_TS[ab]))
    for j, t in enumerate(BUILD_TS[ab]):
        xs = np.array([occ[ANCH[ab][p], YI[t]] for p in PCTS])
        ys = np.array([rate_of(cases[p], t) for p in PCTS])
        o = np.argsort(xs)
        xs, ys = xs[o], ys[o]
        assert np.all(np.diff(xs) > 0), (ab, t, xs)
        iw[:, j] = np.interp(occ_t[:, j], xs, ys)
        topknot[j] = xs[-1]
    IW[ab] = iw
    IREF[ab] = np.array([rate_of(cases["p50"], t) for t in BUILD_TS[ab]])
    TOPKNOT_PCT[ab] = np.array([float((occ_t[:, j] <= topknot[j]).mean())
                                for j in range(len(BUILD_TS[ab]))])
    UPCLAMP[ab] = np.any(occ_t > topknot[None, :], axis=1)

    for p in PCTS:
        w_ = ANCH[ab][p]
        tru = np.array([rate_of(cases[p], t) for t in BUILD_TS[ab]])
        if np.max(np.abs(iw[w_] - tru)) > 1e-9:
            g1_fail.append((ab, p, "anchor rate identity"))

    need_rate = np.maximum(iw - TOL_SHORT, 0.0)
    NEED[ab] = need_rate * OCCW[ab]                       # 2024 $/kW per year
    occ_ref = OCCW[ab][ANCH[ab]["p50"]]
    REFC[ab] = IREF[ab] * occ_ref                          # reference $/kW path
    with np.errstate(divide="ignore", invalid="ignore"):
        f_ratio = np.where(NEED[ab] > 0,
                           NEED[ab] / np.where(REFC[ab] > 0, REFC[ab], np.nan)[None, :],
                           0.0)
    uncov = np.any((NEED[ab] > 0) & (REFC[ab][None, :] <= 0), axis=1)
    COVER[ab] = ~uncov
    RATIO[ab] = np.where(NEED[ab] > 0, f_ratio, 0.0)      # (10000, T) year ratios
    FSTAR[ab] = np.where(uncov, np.inf, np.nanmax(RATIO[ab], axis=1, initial=0.0))
    BINDY[ab] = np.array(BUILD_TS[ab])[
        np.nanargmax(np.where(NEED[ab] > 0, f_ratio, -1.0), axis=1)]

    w50 = ANCH[ab]["p50"]
    exp50 = float(np.max(np.maximum(IREF[ab] - TOL_SHORT, 0.0)
                         / np.where(IREF[ab] > 0, IREF[ab], np.inf)))
    if abs(FSTAR[ab][w50] - exp50) > 1e-9:
        g1_fail.append((ab, "p50", "calibration-point identity"))

    raw_own = {}
    for p in ["p05", "p50", "p95"]:
        w_ = ANCH[ab][p]
        i_own = np.array([rate_of(cases[p], t) for t in BUILD_TS[ab]])
        raw_own[p] = float(np.sum(i_own * OCCW[ab][w_] * ADD[ab] * DISC[ab]) * 1000 / 1e9)
    pub = {p: float(t12.loc[cases[p], "PV_ITC_outlay_2024B"]) for p in ["p05", "p50", "p95"]}
    KAPPA[ab] = float(np.mean([pub[p] / raw_own[p] for p in ["p05", "p50", "p95"]]))
    KAP_RES[ab] = max(abs(KAPPA[ab] * raw_own[p] / pub[p] - 1) for p in ["p05", "p50", "p95"])
    WPRICE[ab] = KAPPA[ab] * ADD[ab] * DISC[ab] * 1000 / 1e9   # $B per ($/kW offered)
    SPREF[ab] = float(REFC[ab] @ WPRICE[ab])
    wgt_val = occ_ref * ADD[ab] * DISC[ab]
    IBAR[ab] = float(np.sum(IREF[ab] * wgt_val) / wgt_val.sum())

assert not g1_fail, g1_fail
assert all(KAP_RES[ab] <= 0.07 for ab in SCHEDULES), {ab: round(KAP_RES[ab], 3) for ab in SCHEDULES}
assert all(COVER[ab].all() for ab in SCHEDULES), "uncoverable worlds appeared"

# ---- G0 (requirement side): reproduce the frozen five-anchor per-world table ------
u01 = pd.read_csv(RD_EXPORTS / "u01_per_world_requirements_5a.csv")
g0_detail = {}
for ab in SCHEDULES:
    ref = u01[u01["schedule"] == ab].sort_values("world")
    assert len(ref) == 10000 and (ref["world"].to_numpy() == np.arange(10000)).all(), ab
    d_f = float(np.max(np.abs(np.round(FSTAR[ab], 4) - ref["fstar"].to_numpy())))
    same_by = bool((BINDY[ab] == ref["binding_year"].to_numpy()).all())
    same_cl = bool((UPCLAMP[ab] == ref["upper_clamped"].to_numpy().astype(bool)).all())
    g0_detail[ab] = (d_f, same_by, same_cl)
    assert d_f <= 1.5e-4 and same_by and same_cl, (ab, g0_detail[ab])
WEDGE = {ab: SPREF[ab] / P50BILL[ab] for ab in SCHEDULES}
print("G0 (u01_5a f*/binding year/clamp) reproduced:",
      {k: f"max|df*| {v[0]:.1e}" for k, v in g0_detail.items()})
print("reference outlay SPREF (2024 $B):", {k: round(v, 1) for k, v in SPREF.items()},
      "| outlay/bill wedge:", {k: round(v, 2) for k, v in WEDGE.items()})
""")

# ====================================================================================
md(r"""## C1 — Graduation years and the static cut-off frontier

Grants pay only the part of the requirement above the statutory ceiling (the
maximum credit rate the statute allows: 50% today, 60% as the registered outer
case). A world "graduates" when no later build year needs an above-ceiling
rate; its **graduation year** is the last build year that does. A world whose
last build year is still above the ceiling never becomes credit-feasible
within the horizon (horizon-censored). For a demonstration window ending in
build year T, **coverage(T)** is the share of cost worlds that graduate by T,
and the **grant cost G(T)** is the priced above-ceiling need in build years
up to T. Sweeping T over the build years gives the frontier a decision maker
reads to pick a commitment horizon; the pick `T_α` is the shortest window that
covers a share α of worlds. The reproduction check first: at T = 2035 and 2033
these objects must equal the frozen `u51` / `u52` tables exactly (gate G0).""")

code(r"""def feasibility_tables(cut, windows):
    mask_rows, world_rows, gap_rows = [], [], []
    for ab in SCHEDULES:
        for band, mult in BAND.items():
            iwm = IW[ab] * mult
            for cap in CAPS:
                above = iwm > cap + cut
                for j, t in enumerate(BUILD_TS[ab]):
                    mask_rows.append(dict(schedule=ab, band=band, cap=cap, year=t,
                                          share_above=round(float(above[:, j].mean()), 4),
                                          censored=(ab, t) in CENSORED))
                for wname, wend in windows:
                    post = [j for j, t in enumerate(BUILD_TS[ab]) if t > wend]
                    infeas = np.any(above[:, post], axis=1) if post else np.zeros(10000, bool)
                    world_rows.append(dict(schedule=ab, band=band, cap=cap, window=wname,
                                           share_not_credit_feasible=round(float(infeas.mean()), 4)))
                    win = [j for j, t in enumerate(BUILD_TS[ab]) if t <= wend]
                    gap_kw = np.maximum(iwm[:, win] - cut - cap, 0.0) * OCCW[ab][:, win]
                    gap_B = gap_kw @ WPRICE[ab][win] if win else np.zeros(10000)
                    gq = np.percentile(gap_B, QS)
                    gap_rows.append(dict(schedule=ab, band=band, cap=cap, window=wname,
                                         window_applicable=bool(win),
                                         share_needing_demo=round(float((gap_B > 0).mean()), 4),
                                         **{f"gap_p{q:02d}_B": round(float(gq[i]), 3)
                                            for i, q in enumerate(QS)},
                                         gap_mean_B=round(float(gap_B.mean()), 3)))
    u51 = pd.DataFrame(mask_rows); u51["kind"] = "per_year"
    u51w = pd.DataFrame(world_rows); u51w["kind"] = "per_world"
    return u51, u51w, pd.DataFrame(gap_rows)

# G0 (window side): exact reproduction of the frozen u51/u52 five-anchor tables
u51, u51w, u52 = feasibility_tables(TOL_SHORT, [("w2035", W_PRIMARY), ("w2033", W_SENS)])
ref51 = pd.read_csv(RD_EXPORTS / "u51_feasibility_mask_5a.csv")
ref52 = pd.read_csv(RD_EXPORTS / "u52_demonstration_gap_5a.csv")
k_y = ["schedule", "band", "cap", "year"]
m = ref51[ref51["kind"] == "per_year"].merge(u51, on=k_y, suffixes=("_ref", ""))
assert len(m) == len(u51) and np.allclose(m["share_above_ref"], m["share_above"], atol=1e-9)
k_w = ["schedule", "band", "cap", "window"]
mw = ref51[ref51["kind"] == "per_world"].merge(u51w, on=k_w, suffixes=("_ref", ""))
assert len(mw) == len(u51w) and np.allclose(mw["share_not_credit_feasible_ref"],
                                            mw["share_not_credit_feasible"], atol=1e-9)
mg = ref52.merge(u52, on=k_w, suffixes=("_ref", ""))
gcols = [f"gap_p{q:02d}_B" for q in QS] + ["gap_mean_B"]
assert len(mg) == len(u52) and all(np.allclose(mg[c + "_ref"], mg[c], atol=1e-9) for c in gcols)
assert (mg["window_applicable_ref"] == mg["window_applicable"]).all()
VERDICT.append(("gate", "G0", "PASS",
                "requirement map reproduces u01_5a (f*, binding year, clamp), u51_5a and u52_5a "
                "(both windows) exactly; 30 anchors, E5 and bills from the 5a run; kappa residual <= 7%"))
print("G0 PASS: u51/u52 five-anchor tables reproduced exactly at windows 2035 and 2033")

# ---- graduation years, grant cost by window, the static frontier -------------------
LASTABOVE = {}     # (ab, cap, band, cutname) -> (10000,) last above-ceiling build year (0 = never)
GRANTCUM = {}      # (ab, cap, band, cutname) -> (10000, T) grant $B paid through build year j
rows30, rows31, rows32 = [], [], []
for ab in SCHEDULES:
    ts = np.array(BUILD_TS[ab])
    T = len(ts)
    for cutname, cut in CUTS.items():
        for band, mult in BAND.items():
            iwm = IW[ab] * mult
            for cap in CAPS:
                above = iwm > cap + cut                                   # (10000, T)
                anyab = above.any(axis=1)
                last_j = np.where(anyab, T - 1 - np.argmax(above[:, ::-1], axis=1), -1)
                last_year = np.where(anyab, ts[np.clip(last_j, 0, T - 1)], 0)
                key = (ab, cap, band, cutname)
                LASTABOVE[key] = last_year
                gap_year_B = np.maximum(iwm - cut - cap, 0.0) * OCCW[ab] * WPRICE[ab][None, :]
                GRANTCUM[key] = np.cumsum(gap_year_B, axis=1)
                never = last_year == ts[-1]
                if band == "base":
                    rows30.extend(dict(schedule=ab, cap=cap, cut=cutname, world=w,
                                       last_above_year=int(last_year[w]),
                                       never_within_horizon=bool(never[w]))
                                  for w in range(10000))
                for j, Tw in enumerate(ts):
                    grad = last_year <= Tw
                    g = GRANTCUM[key][:, j]
                    gq = np.percentile(g, QS)
                    rows31.append(dict(schedule=ab, cap=cap, band=band, cut=cutname, T=int(Tw),
                                       coverage=round(float(grad.mean()), 4),
                                       **{f"grant_p{q:02d}_B": round(float(gq[i]), 3) for i, q in enumerate(QS)},
                                       grant_mean_B=round(float(g.mean()), 3),
                                       grant_in_graduating_B=round(float(g[grad].sum() / 10000), 3),
                                       grant_in_nongraduating_B=round(float(g[~grad].sum() / 10000), 3),
                                       share_never_within_horizon=round(float(never.mean()), 4),
                                       horizon_censored=bool(Tw >= 2047),
                                       n_window_years=j + 1))
                cov = np.array([(last_year <= Tw).mean() for Tw in ts])
                for a in [0.75, 0.90]:
                    hit = np.flatnonzero(cov >= a)
                    j0 = int(hit[0]) if len(hit) else -1
                    rows32.append(dict(schedule=ab, cap=cap, band=band, cut=cutname, alpha=a,
                                       T_alpha=int(ts[j0]) if j0 >= 0 else -1,
                                       coverage_at_pick=(round(float(cov[j0]), 4) if j0 >= 0 else np.nan),
                                       grant_med_B=(round(float(np.median(GRANTCUM[key][:, j0])), 3) if j0 >= 0 else np.nan),
                                       horizon_censored=bool(j0 >= 0 and ts[j0] >= 2047),
                                       first_build_year=int(ts[0])))
p30 = pd.DataFrame(rows30); p30.to_csv(EXPORTS / "p30_graduation_year.csv", index=False)
p31 = pd.DataFrame(rows31); p31.to_csv(EXPORTS / "p31_cutoff_frontier.csv", index=False)
p32 = pd.DataFrame(rows32)
# K3: the pick is a range when the band ends disagree
rng_flag = (p32.groupby(["schedule", "cap", "cut", "alpha"])["T_alpha"]
            .transform(lambda s: s.nunique() > 1))
p32["range_flag"] = rng_flag.to_numpy()
p32["comparable"] = p32["schedule"] != "eia"     # eia builds from 2038: its own build years only
# repair R2 (2026-09-09): the last build year covers every world by construction (the window is
# the whole program), so a pick there is "no cut-off before the horizon", not a year
p32["within_horizon"] = (p32["T_alpha"] > 0) & (p32["T_alpha"] < p32["schedule"].map({ab: BUILD_TS[ab][-1] for ab in SCHEDULES}))
p32.to_csv(EXPORTS / "p32_cutoff_pick.csv", index=False)
show = p32[(p32["cut"] == "reg") & (p32["band"] == "base")].pivot_table(
    index=["schedule"], columns=["cap", "alpha"], values="T_alpha").reindex(SCHEDULES)
print("T_alpha (registered cushion, base band; a pick at the last build year = no cut-off before the horizon):")
print(show.to_string())
print("within-horizon picks:", p32[p32["within_horizon"]][["schedule", "cap", "band", "cut", "alpha", "T_alpha"]].values.tolist())
""")

code(r"""# ---- C1c: the common-window table (Ethan, 2026-09-10) ------------------------------
# One window end for every schedule. Per schedule, ceiling, band and cushion: the share of
# worlds under the ceiling from the first build year, the share under it by the common year,
# the share that graduates after the common year, the share that never gets under it within
# the horizon, and the year by which every world that ever gets under it has done so.
# Descriptive only: no price, no optimization (voi/methods.md v1.2). Main-text Table 2 and
# the Fig 6b right-edge labels read this table.
W_COMMON = 2038
rows36 = []
for ab in SCHEDULES:
    ts = np.array(BUILD_TS[ab])
    for cutname in CUTS:
        for band in BAND:
            for cap in CAPS:
                ly = LASTABOVE[(ab, cap, band, cutname)]
                never = ly == ts[-1]
                ever = (~never) & (ly > 0)                        # graduates after needing grants
                rows36.append(dict(schedule=ab, cap=cap, band=band, cut=cutname, common_year=W_COMMON,
                                   first_build_year=int(ts[0]),
                                   share_under_from_start=round(float((ly == 0).mean()), 4),
                                   share_under_by_common=round(float((ly <= W_COMMON).mean()), 4),
                                   share_graduating_after_common=round(float((ever & (ly > W_COMMON)).mean()), 4),
                                   share_never=round(float(never.mean()), 4),
                                   share_ever_after_grants=round(float(ever.mean()), 4),
                                   complete_year=(int(ly[ever].max()) if ever.any() else -1),
                                   complete_year_q90=(int(np.quantile(ly[ever], 0.9, method="inverted_cdf")) if ever.any() else -1),
                                   complete_year_q95=(int(np.quantile(ly[ever], 0.95, method="inverted_cdf")) if ever.any() else -1),
                                   complete_year_q99=(int(np.quantile(ly[ever], 0.99, method="inverted_cdf")) if ever.any() else -1)))
p36 = pd.DataFrame(rows36)
p36.to_csv(EXPORTS / "p36_common_window_table.csv", index=False)
for cutname in CUTS:
    show = p36[(p36["cut"] == cutname) & (p36["band"] == "base")].pivot_table(
        index="schedule", columns="cap",
        values=["share_never", "share_under_by_common", "share_graduating_after_common", "complete_year"]).reindex(SCHEDULES)
    print(f"\ncommon window end {W_COMMON}, cushion '{cutname}', base band:")
    print(show.to_string())
""")

code(r"""# y04: the cut-off frontier — coverage vs expected grant dollars, one panel per schedule
fig, axes = plt.subplots(2, 3, figsize=(ps.W3, 6.2), sharey=True)
for ax, ab in zip(axes.flat, SCHEDULES):
    for cap, ls in [(0.60, "-"), (0.50, "--")]:
        for band, alpha_ in [("lo", 0.25), ("hi", 0.25), ("base", 1.0)]:
            if cap == 0.50 and band != "base":
                continue
            f = p31[(p31["schedule"] == ab) & (p31["cap"] == cap) & (p31["band"] == band)
                    & (p31["cut"] == "reg")].sort_values("T")
            ax.plot(f["grant_mean_B"], f["coverage"], ls=ls, color=ps.SCHED_C[ab],
                    alpha=alpha_, lw=1.6 if band == "base" else 0.9, marker="o" if band == "base" else None, ms=2.5)
            if band == "base" and cap == 0.60:
                for _, r in f.iterrows():
                    ax.annotate(str(int(r["T"])), (r["grant_mean_B"], r["coverage"]),
                                textcoords="offset points", xytext=(3, -7), fontsize=5.5, color=ps.MUTED)
    fd = p31[(p31["schedule"] == ab) & (p31["cap"] == 0.60) & (p31["band"] == "base")
             & (p31["cut"] == "disp")].sort_values("T")
    ax.plot(fd["grant_mean_B"], fd["coverage"], ls=":", color="0.35", lw=1.0)
    for a in [0.75, 0.90]:
        ax.axhline(a, color=ps.BASE_C, lw=0.7, ls="--")
    ax.set_title(ps.SCHED_SHORT[ab])
    ax.set_ylim(0, 1.02)
    ax.set_xlim(0, None)
for ax in axes[:, 0]:
    ax.set_ylabel("share of cost worlds covered\n(no above-ceiling need after the window)")
for ax in axes[1, :]:
    ax.set_xlabel("expected grant cost of the window (2024 $B)")
handles = [Line2D([], [], color="0.3", lw=1.6, marker="o", ms=2.5, label="60% ceiling (labels: window end year)"),
           Line2D([], [], color="0.3", lw=1.6, ls="--", label="50% ceiling"),
           Line2D([], [], color="0.3", lw=0.9, alpha=0.4, label="60% ceiling, requirement ±E5 band ends"),
           Line2D([], [], color="0.35", lw=1.0, ls=":", label="60% ceiling, 3-point display allowance"),
           Line2D([], [], color=ps.BASE_C, lw=0.7, ls="--", label="coverage targets 75% and 90%")]
fig.tight_layout()
fig.legend(handles=handles, ncol=3, fontsize=6.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 0.0))
ps.savefig(fig, FIGURES / "y04_cutoff_frontier.png")
plt.show()
""")

# ====================================================================================
md(r"""## C1b — The window end as a decision: the expected-loss minimizer

The frontier above bends because the graduation years are bimodal: worlds that
ever become credit-feasible do so early, and the rest never do within the
horizon. After the bend, the marginal grant dollar goes almost entirely to
worlds that will never graduate. Three ways to turn that bend into a year, from
most to least formal (v1.1 addendum, 2026-09-09, Ethan's request):

1. **The Bayes window** (headline). Loss of ending the window at T = expected
   grant dollars paid through T, plus a price ρ_g (in median-world bills) for
   every world that would have graduated after T and is cut off. The optimal T
   is where one more year of grants costs more than the graduations it buys at
   that price. ρ_g is swept as in the stopping decisions; the year quoted for
   the paper is the ρ_g = 1 optimum, with the range over which the optimum
   does not move as its stability read.
2. **The conditional-quantile window** (price-free companion): the shortest
   window that covers a share q of the worlds that ever become credit-feasible
   after needing grants — the attainable set, not all worlds.
3. **The marginal-cost ladder**: grant dollars per extra point of coverage,
   step by step, and the share of each step's grant dollars that goes to
   worlds graduating by that year. The ladder is the audit trail behind 1 and
   2; a geometric knee is reported for reference only (chord method, the
   artificial 2050 end point excluded).
""")

code(r"""RHO_HEAD_WINDOW = 1.0
Q_WINDOW = [0.75, 0.90]
rows34, rows35 = [], []
for ab in SCHEDULES:
    ts = np.array(BUILD_TS[ab]); T = len(ts)
    for cutname in CUTS:
        for band in BAND:
            for cap in CAPS:
                key = (ab, cap, band, cutname)
                ly = LASTABOVE[key]; G = GRANTCUM[key]
                never = ly == ts[-1]
                ever = (~never) & (ly > 0)                        # graduates after needing grants
                # --- 1. the Bayes window: R(T) = E[G(T)] + rho * P50 * P(graduates after T)
                Gmean = G.mean(axis=0)                                            # (T,)
                cut_share = np.array([((~never) & (ly > Tw)).mean() for Tw in ts])   # would graduate after T
                for rho in RHOS:
                    Rw = Gmean + rho * P50BILL[ab] * cut_share
                    j = int(np.argmin(Rw))
                    rows34.append(dict(schedule=ab, cap=cap, band=band, cut=cutname, rule="bayes", param=rho,
                                       T_pick=int(ts[j]), risk_B=round(float(Rw[j]), 3),
                                       grant_mean_B=round(float(Gmean[j]), 3), coverage=round(float((ly <= ts[j]).mean()), 4),
                                       cut_share=round(float(cut_share[j]), 4),
                                       risk_never_end_B=round(float(Rw[-1]), 3),
                                       within_horizon=bool(ts[j] < ts[-1]), first_build_year=int(ts[0])))
                # --- 2. the conditional-quantile window
                for q in Q_WINDOW:
                    if ever.sum() == 0:
                        rows34.append(dict(schedule=ab, cap=cap, band=band, cut=cutname, rule="cond_quantile", param=q,
                                           T_pick=-1, within_horizon=False, first_build_year=int(ts[0])))
                        continue
                    gy = ly[ever]
                    Tq = int(np.quantile(gy, q, method="inverted_cdf"))
                    rows34.append(dict(schedule=ab, cap=cap, band=band, cut=cutname, rule="cond_quantile", param=q,
                                       T_pick=Tq, grant_mean_B=round(float(Gmean[list(ts).index(Tq)]), 3),
                                       coverage=round(float((ly <= Tq).mean()), 4),
                                       cond_coverage=round(float((gy <= Tq).mean()), 4),
                                       share_ever_graduate=round(float(ever.mean()), 4),
                                       share_never=round(float(never.mean()), 4),
                                       within_horizon=bool(Tq < ts[-1]), first_build_year=int(ts[0])))
                # --- 3. the marginal-cost ladder (base band, both cuts)
                if band == "base":
                    cov = np.array([(ly <= Tw).mean() for Tw in ts])
                    x = (Gmean[:-1] - Gmean[0]) / max(Gmean[-2] - Gmean[0], 1e-9)
                    y = (cov[:-1] - cov[0]) / max(cov[-2] - cov[0], 1e-9)
                    knee = int(ts[:-1][int(np.argmax(y - x))])
                    for j in range(T - 1):
                        dG = float(Gmean[j + 1] - Gmean[j]); dc = float(cov[j + 1] - cov[j]) * 100
                        grad_next = ly <= ts[j + 1]
                        dG_grad = float((G[grad_next, j + 1] - G[grad_next, j]).sum() / 10000)
                        rows35.append(dict(schedule=ab, cap=cap, cut=cutname, T_from=int(ts[j]), T_to=int(ts[j + 1]),
                                           d_coverage_pts=round(dc, 2), d_grant_B=round(dG, 3),
                                           B_per_coverage_pt=(round(dG / dc, 3) if dc > 1e-9 else np.inf),
                                           productive_share=(round(dG_grad / dG, 3) if dG > 1e-9 else np.nan),
                                           knee_chord_excl_2050=knee))
p34 = pd.DataFrame(rows34)
stab = (p34[p34["rule"] == "bayes"].groupby(["schedule", "cap", "band", "cut"])["T_pick"]
        .agg(lambda s: f"{int(s.min())}-{int(s.max())}").rename("T_range_over_rho"))
p34 = p34.merge(stab.reset_index(), on=["schedule", "cap", "band", "cut"], how="left")
bandspan = (p34.groupby(["schedule", "cap", "cut", "rule", "param"])["T_pick"].transform(lambda s: s.nunique() > 1))
p34["band_range_flag"] = bandspan.to_numpy()
p34.to_csv(EXPORTS / "p34_window_decision.csv", index=False)
p35 = pd.DataFrame(rows35); p35.to_csv(EXPORTS / "p35_marginal_cost_ladder.csv", index=False)

hb = p34[(p34["rule"] == "bayes") & (p34["band"] == "base") & (p34["cut"] == "reg")]
print("Bayes window T*(rho_g), registered cushion, base band:")
print(hb.pivot_table(index="schedule", columns=["cap", "param"], values="T_pick").reindex(SCHEDULES).to_string())
hq = p34[(p34["rule"] == "cond_quantile") & (p34["band"] == "base") & (p34["cut"] == "reg")]
print("\nconditional-quantile window T_q (worlds that ever graduate after needing grants):")
print(hq.pivot_table(index="schedule", columns=["cap", "param"], values="T_pick").reindex(SCHEDULES).to_string())
head34 = p34[(p34["rule"] == "bayes") & (p34["param"] == RHO_HEAD_WINDOW) & (p34["cap"] == 0.60) & (p34["cut"] == "reg")]
print("\nheadline (rho_g = 1, 60% ceiling, registered cushion) by band end:")
print(head34.pivot_table(index="schedule", columns="band", values="T_pick").reindex(SCHEDULES).to_string())
print("stability over rho_g 0.1-2 (base):", head34[head34["band"] == "base"].set_index("schedule")["T_range_over_rho"].reindex(SCHEDULES).to_dict())
""")

code(r"""# y06: the window as a decision — expected loss by window end (top) and the optimal year by price (bottom)
fig, axes = plt.subplots(2, 6, figsize=(ps.W3 * 1.15, 5.6))
for i, ab in enumerate(SCHEDULES):
    ax, axl = axes[0, i], axes[1, i]
    ts = np.array(BUILD_TS[ab])
    key = (ab, 0.60, "base", "reg")
    ly = LASTABOVE[key]; G = GRANTCUM[key]; never = ly == ts[-1]
    Gmean = G.mean(axis=0); cut_share = np.array([((~never) & (ly > Tw)).mean() for Tw in ts])
    for rho in RHOS:
        Rw = Gmean + rho * P50BILL[ab] * cut_share
        ax.plot(ts, Rw, color=ps.SCHED_C[ab], lw=1.8 if rho == RHO_HEAD_WINDOW else 0.9,
                alpha=1.0 if rho == RHO_HEAD_WINDOW else 0.45, marker="o" if rho == RHO_HEAD_WINDOW else None, ms=2.5)
        j = int(np.argmin(Rw)); ax.plot([ts[j]], [Rw[j]], marker="v", ms=4, color=ps.ACCENT["red"], ls="none")
    ax.set_title(ps.SCHED_SHORT[ab]); ax.set_ylim(0, None)
    ax.set_xticks(ts[::2]); ax.tick_params(axis="x", labelsize=6)
    for band, alpha_ in [("base", 1.0), ("lo", 0.35), ("hi", 0.35)]:
        f = p34[(p34["schedule"] == ab) & (p34["rule"] == "bayes") & (p34["cap"] == 0.60) & (p34["cut"] == "reg")
                & (p34["band"] == band)].sort_values("param")
        axl.plot(f["param"] * P50BILL[ab], f["T_pick"], color=ps.SCHED_C[ab], alpha=alpha_, lw=1.6 if band == "base" else 0.9,
                 marker="o" if band == "base" else None, ms=2.5, drawstyle="steps-mid")
    fq = p34[(p34["schedule"] == ab) & (p34["rule"] == "cond_quantile") & (p34["cap"] == 0.60) & (p34["cut"] == "reg")
             & (p34["band"] == "base")]
    for q, ls in [(0.75, ":"), (0.90, "--")]:
        v = fq[fq["param"] == q]["T_pick"]
        if len(v) and int(v.iloc[0]) > 0:
            axl.axhline(int(v.iloc[0]), color=ps.BASE_C, lw=0.8, ls=ls)
    price_axis(axl, P50BILL[ab], "price of cutting off a world that\nwould graduate (2024 $B)")
    axl.set_ylim(ts[0] - 1, ts[-1] + 1)
axes[0, 0].set_ylabel("expected loss of ending grants\nin that year (2024 $B)")
axes[1, 0].set_ylabel("optimal last grant year")
handles = [Line2D([], [], color="0.3", lw=1.8, marker="o", ms=2.5, label="price = one median-world bill (headline)"),
           Line2D([], [], color="0.3", lw=0.9, alpha=0.45, label="prices 0.1, 0.25, 0.5, 2 × the median-world bill"),
           Line2D([], [], color=ps.ACCENT["red"], marker="v", ms=4, ls="none", label="optimal year at each price"),
           Line2D([], [], color="0.3", lw=0.9, alpha=0.35, label="requirement ±E5 band ends (bottom)"),
           Line2D([], [], color=ps.BASE_C, lw=0.8, ls=":", label="covers 75% of worlds that ever graduate"),
           Line2D([], [], color=ps.BASE_C, lw=0.8, ls="--", label="covers 90% of worlds that ever graduate")]
fig.tight_layout()
fig.legend(handles=handles, ncol=3, fontsize=6.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 0.0))
ps.savefig(fig, FIGURES / "y06_window_decision.png")
plt.show()
""")

# ====================================================================================
md(r"""## The observer and the posterior-summary cache

The observer is the bridge-detection stage-3 observer, formula unchanged. Each
observation year it sees the geometric mean of that year's unit costs,
corrupted by a shared industry shock (tau) and per-project scatter that
averages down with the number of units (sigma / sqrt(n)). Every candidate
world carries a running weight: how probable the observations so far would be
if that world were true. Costs are dated to the build year ("observed at
construction start"), an optimistic convention.

Two things are new. **Leave-one-out:** the truth world sits in the candidate
set, and at low noise the posterior would collapse onto it and overstate what
observation buys; so for every decision quantity the truth world's own weight
is set to zero (the frozen `u10` check keeps it, as the original did).
**The cache:** instead of discarding the 10,000-world weight tensor, the sweep
stores the handful of posterior summaries every later cell needs — the
weighted quantiles of the residual credit scale, the probability that the world
never becomes credit-feasible, the spend-aware probability that the bill will
exceed each cap in each calendar year, and the effective sample size (ESS, the
number of equally weighted worlds the posterior is worth). The seed and draw
order are the `rate_design` v1 ones, so gate G1 can demand that the frozen
uncertainty-width table reproduces exactly.""")

code(r"""# observation calendar (stage-3 construction, re-derived) — must equal the build calendar
OBSCAL, N_UNITS, CUMU, LOGOCC = {}, {}, {}, {}
for ab in SCHEDULES:
    d = duals3[duals3["case"] == f"smr100_{ab}_p05"].set_index("t").sort_index()
    ts = [int(t) for t in d.index if t >= 2031]
    prev, years, units = 0.0, [], []
    for t in ts:
        add = float(d.loc[t, "program_MW"]) - prev
        prev = float(d.loc[t, "program_MW"])
        if add > 0:
            years.append(t)
            units.append(max(1, int(round(add / UNIT_MW))))
    OBSCAL[ab] = np.array(years)
    N_UNITS[ab] = np.array(units, dtype=float)
    CUMU[ab] = np.cumsum(N_UNITS[ab])
    occ = Z[f"occ_{AB2TOK[ab]}_smr"]
    LOGOCC[ab] = np.log(occ[:, [YI[t] for t in years]])
    assert list(OBSCAL[ab]) == BUILD_TS[ab], (ab, OBSCAL[ab], BUILD_TS[ab])
print("observation calendar = build calendar in all six schedules;",
      {ab: len(OBSCAL[ab]) for ab in SCHEDULES}, "observation years")

# the FIRST use of the observer stream: the truth draws, v1 order
rng = np.random.default_rng(SEED)
TRUTH = {ab: np.sort(rng.choice(10000, size=N_TRUTH, replace=False)) for ab in SCHEDULES}

# residual credit-scale objects: after observation k, only build years > t_k are re-priced
FRES, ORD_RES, VS_RES = {}, {}, {}
for ab in SCHEDULES:
    K = len(BUILD_TS[ab])
    fres = np.full((10000, K), np.nan)
    ords, vss = [], []
    for k in range(K - 1):
        fres[:, k] = RATIO[ab][:, k + 1:].max(axis=1)
        o = np.argsort(fres[:, k], kind="stable")
        ords.append(o)
        vss.append(fres[o, k])
    FRES[ab], ORD_RES[ab], VS_RES[ab] = fres, ords, vss
ORD_FULL = {ab: np.argsort(FSTAR[ab], kind="stable") for ab in SCHEDULES}
VS_FULL = {ab: FSTAR[ab][ORD_FULL[ab]] for ab in SCHEDULES}
ORD_LR = {ab: np.argsort(LR_SMR[ab], kind="stable") for ab in SCHEDULES}
VS_LR = {ab: LR_SMR[ab][ORD_LR[ab]] for ab in SCHEDULES}

# never-credit-feasible indicators (base band), columns = (cap, cutname)
NG_COLS = [(cap, cn) for cap in CAPS for cn in CUTS]
NGI = {ab: np.stack([(LASTABOVE[(ab, cap, "base", cn)] == BUILD_TS[ab][-1]).astype(float)
                     for cap, cn in NG_COLS], axis=1) for ab in SCHEDULES}      # (10000, 4)

# the annual ledger (stage-3 construction): per calendar year, each world's remaining bill
ANNUAL_YEARS = np.arange(2031, 2051)
OBS_J = {ab: np.searchsorted(OBSCAL[ab], ANNUAL_YEARS, side="right") for ab in SCHEDULES}
FUT_ORDER, FUT_SORTED = {}, {}
for ab in SCHEDULES:
    fo, fs = [], []
    for i_ in range(len(ANNUAL_YEARS)):
        f_ = B2050[ab] - BILLS_T[ab][:, i_]
        o_ = np.argsort(f_)
        fo.append(o_)
        fs.append(f_[o_])
    FUT_ORDER[ab], FUT_SORTED[ab] = fo, fs
XV = {ab: np.array(XMULTS) * P50BILL[ab] for ab in SCHEDULES}
print("residual scale objects, never-feasible indicators and the ledger are ready")
""")

code(r"""def sweep(ab, lv, worlds, rng_local, want_u10=True):
    '''One schedule x noise level. Returns the posterior summaries per truth world x
    observation index k x history r (leave-one-out), plus the truth-included widths
    that reproduce u10 (gate G1).'''
    sig, tau = lv
    L0 = LOGOCC[ab]
    n = N_UNITS[ab]
    var = tau ** 2 + sig ** 2 / n
    K = L0.shape[1]
    nW, nA, nY, nX, nG = len(worlds), len(ALPHAS), len(ANNUAL_YEARS), len(XMULTS), len(NG_COLS)
    fq = np.full((nW, K, R, nA), np.nan, dtype=np.float32)
    ng = np.empty((nW, K, R, nG), dtype=np.float32)
    ex = np.empty((nW, R, nY, nX), dtype=np.float32)
    ess = np.empty((nW, K, R), dtype=np.float32)
    w10 = {k_: np.empty((nW, K, R), dtype=np.float32) for k_ in ("lr", "fstar")}
    ess_in = np.empty((nW, K, R), dtype=np.float32)
    ngi = NGI[ab]
    for i, w in enumerate(worlds):
        eta = rng_local.normal(0, tau, size=(K, R))
        zbar = rng_local.normal(0, 1, size=(K, R)) * (sig / np.sqrt(n))[:, None]
        Y = L0[w][:, None] + eta + zbar
        D = (L0[:, :, None] - Y[None, :, :]) ** 2 / (2 * var)[None, :, None]
        cl = -np.cumsum(D, axis=1)
        cl -= cl.max(axis=0, keepdims=True)
        W = np.exp(cl)                        # (10000, K, R), truth included
        tw = W.sum(axis=0)
        if want_u10:
            ess_in[i] = (tw ** 2 / (W ** 2).sum(axis=0)).astype(np.float32)
            for k_, (ordv, vs) in (("lr", (ORD_LR[ab], VS_LR[ab])), ("fstar", (ORD_FULL[ab], VS_FULL[ab]))):
                cw = np.cumsum(W[ordv], axis=0) / tw[None, :, :]
                i_lo = (cw < 0.05).sum(axis=0).clip(0, 9999)
                i_hi = (cw < 0.95).sum(axis=0).clip(0, 9999)
                w10[k_][i] = (vs[i_hi] - vs[i_lo]).astype(np.float32)
        # ---- leave-one-out from here on --------------------------------------------
        W[w] = 0.0
        tw = W.sum(axis=0)
        ess[i] = (tw ** 2 / (W ** 2).sum(axis=0)).astype(np.float32)
        Wf = W.reshape(10000, K * R)
        ng[i] = ((ngi.T @ Wf).reshape(nG, K, R) / tw[None]).transpose(1, 2, 0)
        for k in range(K - 1):
            Ws = W[ORD_RES[ab][k], k, :]
            cw = np.cumsum(Ws, axis=0) / tw[k][None, :]
            for a_i, a in enumerate(ALPHAS):
                idx = (cw < a).sum(axis=0).clip(0, 9999)
                fq[i, k, :, a_i] = VS_RES[ab][k][idx]
        Bw = BILLS_T[ab][w]
        W0 = np.ones((10000, R)); W0[w] = 0.0
        for yi_ in range(nY):
            j = int(OBS_J[ab][yi_])
            if j == 0:
                Wo, twy = W0, np.full(R, 9999.0)
            else:
                Wo, twy = W[:, j - 1, :], tw[j - 1]
            Ws = Wo[FUT_ORDER[ab][yi_]]
            tail = np.concatenate([np.flip(np.cumsum(np.flip(Ws, axis=0), axis=0), axis=0),
                                   np.zeros((1, R))], axis=0)
            pos = np.searchsorted(FUT_SORTED[ab][yi_], XV[ab] - Bw[yi_], side="right")
            ex[i, :, yi_, :] = np.clip((tail[pos] / twy).T, 1e-9, 1 - 1e-9)
    return dict(fq=fq, ng=ng, ex=ex, ess=ess, w10_lr=w10["lr"], w10_fstar=w10["fstar"], ess_in=ess_in)

FINGERPRINT = json.dumps(dict(v=1, seed=SEED, seed_voi=SEED_VOI, n_truth=N_TRUTH, R=R, levels=LEVELS,
                              small=LV_SMALL, alphas=ALPHAS, xmults=XMULTS, caps=CAPS, cuts=CUTS,
                              e5=round(E5, 4), truth={ab: int(TRUTH[ab].sum()) for ab in SCHEDULES}))
CACHE_PATH = EXPORTS / "p00_posterior_summaries.npz"
RES = {}
reuse = CACHE_PATH.exists() and not os.environ.get("VOI_FORCE")
if reuse:
    zc = np.load(CACHE_PATH)
    reuse = str(zc["fingerprint"]) == FINGERPRINT
    if reuse:
        for key in zc.files:
            if "|" in key:
                ab, tag, name = key.split("|")
                RES.setdefault((ab, tag), {})[name] = zc[key]
        print("posterior-summary cache reused (fingerprint match):", CACHE_PATH.name)
if not reuse:
    t_all = time.time()
    for ab in SCHEDULES:                       # v1 order: schedule, then level, then truth
        for lv in LEVELS:
            t0 = time.time()
            RES[(ab, lvtag(lv))] = sweep(ab, lv, TRUTH[ab], rng)
            print(f"  {ab} {lvtag(lv)}  {time.time() - t0:5.0f} s", flush=True)
    rng_small = np.random.default_rng(SEED_VOI)          # the small-noise pass: separate seed
    for ab in SCHEDULES:
        t0 = time.time()
        RES[(ab, "small")] = sweep(ab, LV_SMALL, TRUTH[ab], rng_small, want_u10=False)
        print(f"  {ab} small  {time.time() - t0:5.0f} s", flush=True)
    out = {"fingerprint": np.array(FINGERPRINT)}
    for (ab, tag), d in RES.items():
        for name, arr in d.items():
            if tag == "small" and name in ("w10_lr", "w10_fstar", "ess_in"):
                continue
            out[f"{ab}|{tag}|{name}"] = arr
    np.savez_compressed(CACHE_PATH, **out)
    print(f"sweep done in {(time.time() - t_all) / 60:.1f} min; cache written "
          f"({CACHE_PATH.stat().st_size / 1e6:.0f} MB)")

# ---- G1: the frozen u10 five-anchor widths reproduce exactly ------------------------
u10 = pd.read_csv(RD_EXPORTS / "u10_ci_curves_5a.csv")
g1_bad = []
for ab in SCHEDULES:
    for lv in LEVELS:
        d = RES[(ab, lvtag(lv))]
        ref = u10[(u10["schedule"] == ab) & (u10["sigma"] == lv[0]) & (u10["tau"] == lv[1])
                  & (u10["k"] > 0)].sort_values("k")
        K = d["w10_fstar"].shape[1]
        assert len(ref) == K, (ab, lv, len(ref), K)
        for j in range(K):
            r_ = ref.iloc[j]
            d_f = abs(round(float(np.median(d["w10_fstar"][:, j, :])), 4) - r_["fstar_w_med"])
            d_l = abs(round(float(np.median(d["w10_lr"][:, j, :])), 4) - r_["lr_w_med"])
            d_e = abs(round(float(np.median(d["ess_in"][:, j, :])), 1) - r_["ess_med"])
            if d_f > 1.5e-4 or d_l > 1.5e-4 or d_e > 0.15:
                g1_bad.append((ab, lv, j + 1, d_f, d_l, d_e))
assert not g1_bad, g1_bad[:5]
VERDICT.append(("gate", "G1", "PASS",
                "re-implemented observer reproduces u10_ci_curves_5a (f* width, learning-rate width, "
                "ESS medians) at every k and noise level to the stored rounding"))
print("G1 PASS: u10_5a reproduced at all", sum(len(OBSCAL[ab]) for ab in SCHEDULES) * 3, "cells")
""")

md(r"""### G4a — the weight formula against a brute-force reimplementation

One seeded spot case (McKinsey schedule, medium noise, one truth world, one
history) is re-done with a plain per-world loop that multiplies Gaussian
likelihoods year by year. The two weight vectors must agree to 1e-10.""")

code(r"""ab0, (sig0, tau0) = "mck", LV_MID
rng_g4 = np.random.default_rng(SEED + 1)
L0 = LOGOCC[ab0]; n0 = N_UNITS[ab0]; var0 = tau0 ** 2 + sig0 ** 2 / n0; K0 = L0.shape[1]
w0 = int(TRUTH[ab0][0])
eta0 = rng_g4.normal(0, tau0, size=K0)
zb0 = rng_g4.normal(0, 1, size=K0) * (sig0 / np.sqrt(n0))
Y0 = L0[w0] + eta0 + zb0
D0 = (L0 - Y0[None, :]) ** 2 / (2 * var0)[None, :]
clv = -np.cumsum(D0, axis=1); clv -= clv.max(axis=0, keepdims=True)
Wv = np.exp(clv[:, -1]); Wv /= Wv.sum()
Wb = np.zeros(10000)
for m_ in range(10000):
    p_ = 1.0
    for j in range(K0):
        p_ *= np.exp(-(L0[m_, j] - Y0[j]) ** 2 / (2 * var0[j]))
    Wb[m_] = p_
Wb /= Wb.sum()
g4a_err = float(np.max(np.abs(Wv - Wb)))
assert g4a_err < 1e-10, g4a_err
VERDICT.append(("gate", "G4a", "PASS", f"vectorized weights = brute-force Gaussian product (max diff {g4a_err:.1e})"))
print(f"G4a PASS (max weight diff {g4a_err:.2e})")
""")

# ====================================================================================
md(r"""## A — The credit-scale decision: EVPI, EVSI

**The decision.** Declare a scale f on the reference credit path (the p50
anchor's declared $/kW path). A world is delivered in a year if f times the
reference covers its need that year.

**Sequential structure.** After the units of observation year t_k are seen,
the build years up to t_k are sunk at the prior act; only the later years are
re-priced. So every quantity below is defined on the residual years, and the
value of watching is a quasi-option value: the information only arrives because
building proceeds.

**Two losses.** The *scale-space quantile loss* weights a unit of scale
deficit α/(1−α) times a unit of scale excess; its optimal act under any belief
is the α-quantile of the required scale, so at α = 0.90 it is exactly the
paper's rule "cover the requirement in 90% of worlds". The *dollar loss*
prices the same act in outlay dollars: over-payment is the credit paid above
need, summed over residual years; shortfall is the need left uncovered, summed
the same way and weighted α/(1−α). The paper's delivery semantics are
threshold (any shortfall in a year is a failed build), so the linear shortfall
price is a stylization, stated once here.

**Estimators.** Prior act, posterior act and perfect act are all scored on the
same 500 truth worlds and 10 histories (paired). EVPI = prior loss minus
perfect loss; EVSI(k) = prior loss minus posterior loss after observation k;
the *fraction of remaining EVPI recovered* is their ratio. Cluster bootstrap
over truth worlds gives confidence intervals. The posterior is leave-one-out.
Gate G2 checks that the posterior rule really covers α of worlds under the
model; gate G3 that EVSI never exceeds EVPI.""")

code(r"""def uq_uniform(vs_sorted, alpha):
    n = len(vs_sorted)
    idx = int((np.arange(1, n + 1) / n < alpha).sum())
    return float(vs_sorted[min(idx, n - 1)])

def loss_scale(f, fstar, spref, alpha):
    lam = alpha / (1 - alpha)
    return spref * (np.maximum(f - fstar, 0.0) + lam * np.maximum(fstar - f, 0.0))

def loss_dollar(f, need, ref, wp, alpha):
    '''f: (...,) scales broadcastable against need (..., T); returns (total, overpay, shortfall)'''
    lam = alpha / (1 - alpha)
    gap = f[..., None] * ref - need
    over = np.maximum(gap, 0.0) @ wp
    short = np.maximum(-gap, 0.0) @ wp
    return over + lam * short, over, short

def dollar_opt(need, ref, wp, alpha):
    '''per-world minimum of the dollar loss over the scale; candidates = the year ratios (+0)'''
    with np.errstate(divide="ignore", invalid="ignore"):
        cand = np.where(need > 0, need / np.where(ref > 0, ref, np.nan)[None, :], 0.0)
    cand = np.concatenate([np.nan_to_num(cand), np.zeros((need.shape[0], 1))], axis=1)   # (n, Tc)
    tot, _, _ = loss_dollar(cand, need[:, None, :], ref, wp, alpha)                       # (n, Tc)
    return tot.min(axis=1)

rng_boot = np.random.default_rng(SEED_VOI + 1)
BOOT_IDX = rng_boot.integers(0, N_TRUTH, size=(N_BOOT, N_TRUTH))
def boot_ci(per_world):
    b = per_world[BOOT_IDX].mean(axis=1)
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))

TAGS = [lvtag(lv) for lv in LEVELS] + ["small"]
TAG2LV = {lvtag(lv): lv for lv in LEVELS}; TAG2LV["small"] = LV_SMALL
rows12 = []
g2_bad, g3_bad = [], []
for ab in SCHEDULES:
    tr = TRUTH[ab]
    K = len(BUILD_TS[ab])
    ts = np.array(BUILD_TS[ab])
    spend_tr = BILLS_T[ab][tr][:, [BILL_YEARS.index(t) for t in ts]]
    for tag in TAGS:
        d = RES[(ab, tag)]
        lv = TAG2LV[tag]
        for a_i, a in enumerate(ALPHAS):
            f_full = uq_uniform(VS_FULL[ab], a)
            for k in range(-1, K - 1):
                res = slice(k + 1, K)
                ref_r, wp_r = REFC[ab][res], WPRICE[ab][res]
                spref_k = float(ref_r @ wp_r)
                fres_all = FSTAR[ab] if k < 0 else FRES[ab][:, k]
                f_pk = uq_uniform(VS_FULL[ab] if k < 0 else VS_RES[ab][k], a)
                fs_tr = fres_all[tr]
                need_tr = NEED[ab][tr][:, res]
                Lp_s = loss_scale(f_pk, fs_tr, spref_k, a)
                Lf_s = loss_scale(f_full, fs_tr, spref_k, a)
                Lp_d, _, _ = loss_dollar(np.full(N_TRUTH, f_pk), need_tr, ref_r, wp_r, a)
                Lf_d, _, _ = loss_dollar(np.full(N_TRUTH, f_full), need_tr, ref_r, wp_r, a)
                Lperf_d = dollar_opt(need_tr, ref_r, wp_r, a)
                Lfloor_d, _, _ = loss_dollar(fs_tr, need_tr, ref_r, wp_r, a)   # the scaled-path floor
                evpi_s = float(Lp_s.mean())
                evpi_d = float((Lp_d - Lperf_d).mean())
                row = dict(schedule=ab, sigma=lv[0], tau=lv[1], alpha=a, k=k,
                           year=int(ts[k]) if k >= 0 else 0, units=int(CUMU[ab][k]) if k >= 0 else 0,
                           spend_med_B=round(float(np.median(spend_tr[:, k])), 2) if k >= 0 else 0.0,
                           n_residual_years=K - 1 - k, spref_res_B=round(spref_k, 3),
                           f_prior=round(f_pk, 4), f_full=round(f_full, 4),
                           prior_loss_scale_B=round(evpi_s, 4), evpi_scale_B=round(evpi_s, 4),
                           prior_loss_dollar_B=round(float(Lp_d.mean()), 4),
                           perfect_loss_dollar_B=round(float(Lperf_d.mean()), 4),
                           shape_floor_dollar_B=round(float(Lfloor_d.mean()), 4),
                           evpi_dollar_B=round(evpi_d, 4),
                           flex_scale_B=round(float((Lf_s - Lp_s).mean()), 4),
                           flex_dollar_B=round(float((Lf_d - Lp_d).mean()), 4),
                           evpi_dollar_over_spref=round(evpi_d / spref_k, 4) if spref_k > 0 else np.nan)
                if k >= 0:
                    fh = d["fq"][:, k, :, a_i].astype(float)                      # (nW, R)
                    Lpost_s = loss_scale(fh, fs_tr[:, None], spref_k, a)
                    Lpost_d, over_d, short_d = loss_dollar(fh, need_tr[:, None, :], ref_r, wp_r, a)
                    dw_s = Lp_s - Lpost_s.mean(axis=1)
                    dw_d = Lp_d - Lpost_d.mean(axis=1)
                    evsi_s, evsi_d = float(dw_s.mean()), float(dw_d.mean())
                    ci_lo, ci_hi = boot_ci(dw_d)
                    cov_w = (fh >= fs_tr[:, None]).mean(axis=1)
                    cov = float(cov_w.mean())
                    se = float(cov_w.std(ddof=1) / np.sqrt(N_TRUTH))
                    regret = Lpost_d - Lperf_d[:, None]
                    ess_k = d["ess"][:, k, :]
                    row.update(evsi_scale_B=round(evsi_s, 4), evsi_dollar_B=round(evsi_d, 4),
                               evsi_dollar_ci_lo=round(ci_lo, 4), evsi_dollar_ci_hi=round(ci_hi, 4),
                               frac_recovered_scale=round(evsi_s / evpi_s, 4) if evpi_s > 0 else np.nan,
                               frac_recovered_dollar=round(evsi_d / evpi_d, 4) if evpi_d > 0 else np.nan,
                               realized_coverage=round(cov, 4), coverage_se=round(se, 4),
                               post_overpay_B=round(float(over_d.mean()), 4),
                               post_shortfall_B=round(float(short_d.mean()), 4),
                               regret_p50_B=round(float(np.percentile(regret, 50)), 4),
                               regret_p95_B=round(float(np.percentile(regret, 95)), 4),
                               ess_med=round(float(np.median(ess_k)), 1),
                               ess_q10=round(float(np.percentile(ess_k, 10)), 1))
                    if evsi_s > evpi_s + 1e-9 or evsi_d > evpi_d + 1e-9:
                        g3_bad.append((ab, tag, a, k, evsi_s - evpi_s, evsi_d - evpi_d))
                    if lv == LV_MID and a == ALPHA_HEAD and abs(cov - a) > 2.576 * se + 0.005:
                        g2_bad.append((ab, k, round(cov, 3), round(se, 4)))
                rows12.append(row)
p12 = pd.DataFrame(rows12)
p12.to_csv(EXPORTS / "p12_evsi_curves.csv", index=False)
assert not g3_bad, g3_bad[:5]
VERDICT.append(("gate", "G3", "PASS", "EVSI(k) <= EVPI_{>k} in both losses at every schedule x noise x alpha x k"))
if g2_bad:
    VERDICT.append(("gate", "G2", "FAIL", f"posterior 0.90-rule coverage outside the 99% band at mid noise: {g2_bad}"))
else:
    VERDICT.append(("gate", "G2", "PASS", "posterior alpha-rule realized coverage under the model within the "
                    "cluster-robust 99% band at mid noise, alpha 0.90, every k (self-consistency, not calibration)"))
assert not g2_bad, g2_bad
h = p12[(p12["alpha"] == ALPHA_HEAD) & (p12["sigma"] == LV_MID[0]) & (p12["k"] >= 0)]
last = h[h["k"] == h.groupby("schedule")["k"].transform("max")].set_index("schedule").reindex(SCHEDULES)
print("mid noise, alpha 0.90 — after the last usable observation (k = K-2):")
print(last[["year", "evpi_dollar_B", "evsi_dollar_B", "evsi_dollar_ci_lo", "evsi_dollar_ci_hi",
            "frac_recovered_dollar", "frac_recovered_scale", "realized_coverage", "ess_q10"]].to_string())
pri = p12[(p12["alpha"] == ALPHA_HEAD) & (p12["sigma"] == LV_MID[0]) & (p12["k"] == -1)].set_index("schedule").reindex(SCHEDULES)
print("\nfull-horizon EVPI (2024 $B), alpha 0.90, truth-sample basis:")
print(pri[["spref_res_B", "f_prior", "prior_loss_dollar_B", "perfect_loss_dollar_B", "evpi_dollar_B",
           "evpi_scale_B", "evpi_dollar_over_spref"]].to_string())
""")

code(r"""# p10: prior loss and EVPI on the full ensemble, per band end and alpha, with the clamp share (K2)
rows10 = []
for ab in SCHEDULES:
    for band, mult in BAND.items():
        need_b = np.maximum(IW[ab] * mult - TOL_SHORT, 0.0) * OCCW[ab]
        with np.errstate(divide="ignore", invalid="ignore"):
            rat_b = np.where(need_b > 0, need_b / np.where(REFC[ab] > 0, REFC[ab], np.nan)[None, :], 0.0)
        fs_b = np.nanmax(rat_b, axis=1, initial=0.0)
        vs_b = np.sort(fs_b)
        for a in ALPHAS:
            f_a = uq_uniform(vs_b, a)
            Ls = loss_scale(f_a, fs_b, SPREF[ab], a)
            Ld, over, short = loss_dollar(np.full(10000, f_a), need_b, REFC[ab], WPRICE[ab], a)
            Lperf = dollar_opt(need_b, REFC[ab], WPRICE[ab], a)
            above = fs_b > f_a
            clamp_share = float(UPCLAMP[ab][above].mean()) if above.any() else np.nan
            rows10.append(dict(schedule=ab, band=band, alpha=a, basis="ensemble-10000",
                               f_alpha=round(f_a, 4), outlay_at_f_alpha_B=round(f_a * SPREF[ab], 3),
                               prior_loss_scale_B=round(float(Ls.mean()), 4),
                               prior_loss_dollar_B=round(float(Ld.mean()), 4),
                               overpay_B=round(float(over.mean()), 4), shortfall_B=round(float(short.mean()), 4),
                               perfect_loss_dollar_B=round(float(Lperf.mean()), 4),
                               evpi_scale_B=round(float(Ls.mean()), 4),
                               evpi_dollar_B=round(float((Ld - Lperf).mean()), 4),
                               evpi_dollar_over_spref=round(float((Ld - Lperf).mean()) / SPREF[ab], 4),
                               clamp_share_above_q=round(clamp_share, 3) if np.isfinite(clamp_share) else np.nan,
                               k2_lower_bound=bool(np.isfinite(clamp_share) and clamp_share > 0.5)))
p10 = pd.DataFrame(rows10)
p10.to_csv(EXPORTS / "p10_prior_evpi.csv", index=False)
k2 = p10[p10["k2_lower_bound"]][["schedule", "band", "alpha"]].values.tolist()
VERDICT.append(("kill", "K2", "DISCLOSED" if k2 else "PASS",
                ("EVPI quoted as a lower bound (top-knot clamp among worlds above the alpha-quantile > 50%): "
                 f"{k2}") if k2 else "clamp share among worlds above the alpha-quantile <= 50% in every cell"))
print(p10[(p10["band"] == "base") & (p10["alpha"] == ALPHA_HEAD)].set_index("schedule")[
    ["f_alpha", "outlay_at_f_alpha_B", "prior_loss_dollar_B", "overpay_B", "shortfall_B",
     "evpi_dollar_B", "evpi_dollar_over_spref", "clamp_share_above_q"]].to_string())
""")

code(r"""# y01: EVSI in dollars against cumulative spend (top) and the fraction of remaining EVPI recovered (bottom)
fig, axes = plt.subplots(2, 6, figsize=(ps.W3 * 1.15, 5.4))
shaded = False
for i, ab in enumerate(SCHEDULES):
    ax, axl = axes[0, i], axes[1, i]
    for lv in LEVELS + [LV_SMALL]:
        f = p12[(p12["schedule"] == ab) & (p12["alpha"] == ALPHA_HEAD) & (p12["sigma"] == lv[0])
                & (p12["tau"] == lv[1]) & (p12["k"] >= 0)].sort_values("k")
        ax.plot(f["spend_med_B"], f["evsi_dollar_B"], color=ps.SCHED_C[ab], **LV_STYLE[lv])
        axl.plot(f["spend_med_B"], f["frac_recovered_dollar"], color=ps.SCHED_C[ab], **LV_STYLE[lv])
        if lv == LV_MID:
            ax.plot(f["spend_med_B"], f["evpi_dollar_B"], color=ps.BASE_C, lw=0.9, ls="--")
            starved = f[f["ess_q10"] < ESS_FLOOR]
            if len(starved):
                shaded = True
                s0 = float(starved["spend_med_B"].iloc[0])
                for a_ in (ax, axl):
                    a_.axvspan(s0, float(f["spend_med_B"].iloc[-1]), color="0.85", zorder=0)
    ax.set_title(ps.SCHED_SHORT[ab])
    for a_ in (ax, axl):
        a_.set_xlim(0, None)
        a_.set_ylim(0, None)
    axl.set_ylim(0, 1.0)
    axl.set_xlabel("spend committed before\nthe observation (2024 $B)")
axes[0, 0].set_ylabel("value of the observations so far\n(2024 $B of avoided loss)")
axes[1, 0].set_ylabel("share of the remaining value of\nperfect information recovered")
handles = [Line2D([], [], color="0.3", label=LV_LABEL[lv], **LV_STYLE[lv]) for lv in LEVELS + [LV_SMALL]]
handles.append(Line2D([], [], color=ps.BASE_C, lw=0.9, ls="--", label="value of perfect information about the remaining years"))
if shaded:
    handles.append(Patch(facecolor="0.85", label="effective sample below 100 worlds"))
fig.tight_layout()
fig.legend(handles=handles, ncol=3, fontsize=6.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 0.0))
ps.savefig(fig, FIGURES / "y01_evsi_curves.png")
plt.show()
""")

# ====================================================================================
md(r"""### EVPPI — which uncertainty is worth resolving

EVPPI for one input dial (for example the SMR learning rate) is the expected
loss reduction from knowing that dial exactly while the others stay uncertain.
Following the single-sample idea of Strong, Oakley and Brennan (2014), the
10,000 worlds are binned on the dial and the α-quantile act is fitted within
each bin. Two safeguards against over-fitting: the fit uses one half of each
bin's worlds and is scored on the other half (cross-fitting, then the halves
swap), and the dial is shuffled 20 times to measure the value a completely
uninformative dial would show by chance (the permutation floor). A prior
stress cell then tilts the prior on the learning rate by one standard
deviation each way.""")

code(r"""rng_cf = np.random.default_rng(SEED_VOI + 2)
rng_perm = np.random.default_rng(SEED_VOI + 3)
HALF_A = {ab: np.zeros(10000, bool) for ab in SCHEDULES}
for ab in SCHEDULES:
    HALF_A[ab][rng_cf.permutation(10000)[:5000]] = True

def rank_bins(x, B):
    rank = np.empty(len(x), int)
    rank[np.argsort(x, kind="stable")] = np.arange(len(x))
    return (rank * B) // len(x)

def cond_loss(ab, bin_id, nb, alpha, fallback_f):
    '''cross-fitted conditional-quantile losses (scale, dollar) averaged over all 10,000 worlds'''
    fs = FSTAR[ab]; need = NEED[ab]; ref = REFC[ab]; wp = WPRICE[ab]; hA = HALF_A[ab]
    out_s = np.empty(10000); out_d = np.empty(10000)
    for b in range(nb):
        inb = bin_id == b
        for fit, ev in ((hA, ~hA), (~hA, hA)):
            fi, ei = inb & fit, inb & ev
            if not ei.any():
                continue
            f_b = uq_uniform(np.sort(fs[fi]), alpha) if fi.any() else fallback_f
            out_s[ei] = loss_scale(f_b, fs[ei], SPREF[ab], alpha)
            out_d[ei], _, _ = loss_dollar(np.full(int(ei.sum()), f_b), need[ei], ref, wp, alpha)
    return float(out_s.mean()), float(out_d.mean())

rows11 = []
BINS = [10, 25, 50, 100]
N_PERM = 20
base10 = p10[(p10["band"] == "base")].set_index(["schedule", "alpha"])
for ab in SCHEDULES:
    for a in ALPHAS:
        b_s = float(base10.loc[(ab, a), "prior_loss_scale_B"])
        b_d = float(base10.loc[(ab, a), "prior_loss_dollar_B"])
        perf_d = float(base10.loc[(ab, a), "perfect_loss_dollar_B"])
        f_a = float(base10.loc[(ab, a), "f_alpha"])
        evpi_d = b_d - perf_d
        targets = [(WCOLS[j], DIALS[ab][:, j]) for j in range(len(WCOLS))]
        for name, x in targets + [("group:lr_smr+boak_smr", None)]:
            bins_here = BINS if a == ALPHA_HEAD else [50]
            for B in bins_here:
                if x is None:
                    g = int(round(np.sqrt(B)))            # 7 x 7 cells at B = 50
                    bid = rank_bins(LR_SMR[ab], g) * g + rank_bins(DIALS[ab][:, WCOLS.index("boak_smr")], g)
                    nb = g * g
                else:
                    bid, nb = rank_bins(x, B), B
                cs, cd = cond_loss(ab, bid, nb, a, f_a)
                row = dict(schedule=ab, alpha=a, dial=name, bins=nb,
                           evppi_scale_B=round(b_s - cs, 4), evppi_dollar_B=round(b_d - cd, 4),
                           share_of_evpi_dollar=round((b_d - cd) / evpi_d, 4) if evpi_d > 0 else np.nan)
                if a == ALPHA_HEAD and B == 50:
                    ps_, pd_ = [], []
                    for _ in range(N_PERM):
                        if x is None:
                            perm = rng_perm.permutation(10000)
                            bidp = rank_bins(LR_SMR[ab][perm], g) * g + rank_bins(
                                DIALS[ab][perm, WCOLS.index("boak_smr")], g)
                        else:
                            bidp = rank_bins(x[rng_perm.permutation(10000)], B)
                        cs_p, cd_p = cond_loss(ab, bidp, nb, a, f_a)
                        ps_.append(b_s - cs_p); pd_.append(b_d - cd_p)
                    row.update(perm_mean_scale_B=round(float(np.mean(ps_)), 4), perm_sd_scale_B=round(float(np.std(ps_)), 4),
                               perm_mean_dollar_B=round(float(np.mean(pd_)), 4), perm_sd_dollar_B=round(float(np.std(pd_)), 4),
                               evppi_dollar_net_B=round(b_d - cd - float(np.mean(pd_)), 4),
                               informative=bool(b_d - cd - np.mean(pd_) > 2 * np.std(pd_)))
                rows11.append(row)
p11 = pd.DataFrame(rows11)
# plateau flag (alpha 0.90): B = 25 and B = 100 within 15% of the B = 50 dollar value
plat = {}
for (ab, name), g_ in p11[p11["alpha"] == ALPHA_HEAD].groupby(["schedule", "dial"]):
    v = g_.set_index("bins")["evppi_dollar_B"]
    v50 = v.get(50, v.get(49, np.nan))
    ok = np.nan
    if np.isfinite(v50) and abs(v50) > 1e-6:
        near = [v.get(b_, np.nan) for b_ in (25, 100)] if name.startswith("group") is False else [v.get(25, np.nan), v.get(100, np.nan)]
        ok = bool(all(np.isfinite(n_) and abs(n_ - v50) <= 0.15 * abs(v50) for n_ in near))
    plat[(ab, name)] = ok
p11["plateau"] = [plat.get((r.schedule, r.dial), np.nan) if r.alpha == ALPHA_HEAD else np.nan for r in p11.itertuples()]
p11.to_csv(EXPORTS / "p11_evppi.csv", index=False)

# G4: EVPPI <= EVPI in both losses (hard); the soft reads are recorded
g4 = p11.merge(base10.reset_index()[["schedule", "alpha", "prior_loss_scale_B", "prior_loss_dollar_B", "perfect_loss_dollar_B"]],
               on=["schedule", "alpha"])
g4["evpi_d"] = g4["prior_loss_dollar_B"] - g4["perfect_loss_dollar_B"]
bad4 = g4[(g4["evppi_scale_B"] > g4["prior_loss_scale_B"] + 1e-6) | (g4["evppi_dollar_B"] > g4["evpi_d"] + 1e-6)]
assert bad4.empty, bad4[["schedule", "alpha", "dial", "bins", "evppi_scale_B", "evppi_dollar_B"]].head()
VERDICT.append(("gate", "G4", "PASS", "EVPPI_j <= EVPI in both losses for every dial, bin count and alpha"))
h11 = p11[(p11["alpha"] == ALPHA_HEAD) & (p11["bins"].isin([49, 50]))]
grp = h11[h11["dial"].str.startswith("group")].set_index("schedule")["share_of_evpi_dollar"]
single_max = h11[~h11["dial"].str.startswith("group")].groupby("schedule")["share_of_evpi_dollar"].max()
VERDICT.append(("gate", "G4-soft", "PASS" if (grp.reindex(SCHEDULES) >= single_max.reindex(SCHEDULES) - 0.02).all() else "DISCLOSED",
                "group {lr_smr, boak_smr} EVPPI vs the best single dial (share of EVPI): "
                + str({ab: (round(float(grp[ab]), 3), round(float(single_max[ab]), 3)) for ab in SCHEDULES})))
uninf = h11[(h11["informative"] == False) & ~h11["dial"].str.startswith("group")].groupby("schedule")["dial"].apply(list).to_dict()  # noqa: E712
VERDICT.append(("note", "EVPPI-floor", "DISCLOSED", f"dials below two permutation SDs (uninformative) per schedule: {uninf}"))
piv = h11.pivot_table(index="dial", columns="schedule", values="share_of_evpi_dollar").reindex(columns=SCHEDULES)
piv["mean"] = piv.mean(axis=1)
print("EVPPI as a share of dollar EVPI (alpha 0.90, 50 bins, cross-fitted):")
print(piv.sort_values("mean", ascending=False).round(3).to_string())
""")

code(r"""# y02: EVPPI shares per schedule with the permutation floor
h11 = p11[(p11["alpha"] == ALPHA_HEAD) & (p11["bins"].isin([49, 50]))].copy()
order = (h11[~h11["dial"].str.startswith("group") & ~h11["dial"].isin(["lr_large", "boak_large"])]
         .groupby("dial")["share_of_evpi_dollar"].mean().sort_values(ascending=False).index.tolist())
# lr_large/boak_large are identical to the SMR dials in these worlds (the ensemble couples the two
# technologies' dials, kappa = 1) and are dropped from the bars; they stay in p11 (repair R3)
labels = {d: d for d in order}
labels["group:lr_smr+boak_smr"] = "lr_smr + boak_smr\n(jointly)"
fig, axes = plt.subplots(2, 3, figsize=(ps.W3, 6.4), sharey=True)
for ax, ab in zip(axes.flat, SCHEDULES):
    g_ = h11[h11["schedule"] == ab].set_index("dial")
    names = ["group:lr_smr+boak_smr"] + order
    vals = [g_.loc[n_, "share_of_evpi_dollar"] for n_ in names]
    floors = [2 * g_.loc[n_, "perm_sd_dollar_B"] / max(g_.loc[n_, "evppi_dollar_B"] / g_.loc[n_, "share_of_evpi_dollar"], 1e-9)
              if np.isfinite(g_.loc[n_, "share_of_evpi_dollar"]) and g_.loc[n_, "share_of_evpi_dollar"] != 0 else 0.0 for n_ in names]
    colors = [ps.SCHED_C[ab] if n_.startswith("group") else ps.NEUTRAL for n_ in names]
    ax.barh(range(len(names)), vals, color=colors, edgecolor=ps.EDGE_C, lw=0.4)
    ax.errorbar(vals, range(len(names)), xerr=floors, fmt="none", ecolor=ps.MUTED, elinewidth=0.7, capsize=1.5)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels([labels[n_] for n_ in names], fontsize=6)
    ax.invert_yaxis()
    ax.set_title(ps.SCHED_SHORT[ab])
    ax.set_xlim(0, 1.0)
for ax in axes[1, :]:
    ax.set_xlabel("value of knowing this input exactly,\nshare of the value of perfect information")
fig.tight_layout()
fig.legend(handles=[Patch(facecolor=ps.NEUTRAL, label="single input dial"),
                    Patch(facecolor="0.3", label="the two SMR cost dials jointly"),
                    Line2D([], [], color=ps.MUTED, lw=0.7, label="two permutation SDs (noise floor)")],
           ncol=3, fontsize=6.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 0.0))
ps.savefig(fig, FIGURES / "y02_evppi.png")
plt.show()

# p13: prior stress — tilt the prior on the SMR learning rate by one standard deviation
rows13 = []
for ab in SCHEDULES:
    z = (LR_SMR[ab] - LR_SMR[ab].mean()) / LR_SMR[ab].std()
    perf = dollar_opt(NEED[ab], REFC[ab], WPRICE[ab], ALPHA_HEAD)
    for theta in (-1.0, 0.0, 1.0):
        wts = np.exp(theta * z); wts /= wts.sum()
        o = ORD_FULL[ab]
        cw = np.cumsum(wts[o])
        f_a = float(VS_FULL[ab][min(int((cw < ALPHA_HEAD).sum()), 9999)])
        Ls = loss_scale(f_a, FSTAR[ab], SPREF[ab], ALPHA_HEAD)
        Ld, _, _ = loss_dollar(np.full(10000, f_a), NEED[ab], REFC[ab], WPRICE[ab], ALPHA_HEAD)
        rows13.append(dict(schedule=ab, alpha=ALPHA_HEAD, theta=theta,
                           prior_mean_lr=round(float((wts * LR_SMR[ab]).sum()), 4),
                           f_alpha=round(f_a, 4), prior_loss_scale_B=round(float((wts * Ls).sum()), 4),
                           evpi_dollar_B=round(float((wts * (Ld - perf)).sum()), 4)))
p13 = pd.DataFrame(rows13)
p13.to_csv(EXPORTS / "p13_prior_stress.csv", index=False)
print(p13.pivot_table(index="schedule", columns="theta", values="evpi_dollar_B").reindex(SCHEDULES).to_string())
""")

# ====================================================================================
md(r"""## B — The stopping decision as a Bayes sequential decision

Each calendar year the government knows the posterior probability that the
program's total bill will exceed a spending cap X: the weighted share of
candidate worlds whose remaining bill, added to the spend already paid (the
outlay ledger, which the paying government knows exactly), exceeds X. It can
stop (abandon the program) or continue one more year; stopping is forced when
spend reaches X.

**Loss.** In a world whose bill truly exceeds X, every dollar paid before
stopping is wasted. In a world that would have stayed under X, stopping
forfeits delivery; that loss is priced at ρ times the median-world bill, where
ρ (the false-stop price) is the reader's parameter. The **Bayes risk** of a
rule is its expected loss over worlds. The **Bayes rule** in the family "stop
the first year the posterior reaches a threshold" is the threshold that
minimizes the Bayes risk. Two references: the ledger-only rule (never stop on
the posterior; the whole prior risk, since perfect information would stop
every exceeding world at once), and today's conformal 5%-false-alarm rule,
whose implied false-stop price is read off. A least-squares Monte Carlo
backward induction (Longstaff and Schwartz) checks how far the threshold
family is from the optimal stopping value (gate G7).""")

code(r"""PIBAR = np.round(np.arange(0.05, 1.0001, 0.01), 2)
PIBAR_ALL = np.concatenate([PIBAR, [1.5]])          # 1.5 = the ledger-only sentinel

def stop_outcomes(exx, bills_tr, is_ex, X, pibar):
    '''exx (nW, R, 20) posterior; returns stop index (nW, R) in 0..19 (exceeding: <=ledger) or 20, paid (nW,R)'''
    ledger = (bills_tr <= X).sum(axis=1)                  # first annual index with spend > X (20 = never)
    hit = exx >= pibar
    first = np.where(hit.any(axis=2), hit.argmax(axis=2), 20)
    stop = np.minimum(first, ledger[:, None])
    paid = bills_tr[np.arange(len(bills_tr))[:, None], np.clip(stop, 0, 19)]
    return stop, paid, ledger

def bayes_risk(stop, paid, is_ex, rho, p50):
    '''per-world contributions (nW,) whose mean is R = P(ex) E[paid|ex] + P(not ex) rho P50 P(stop|not ex)'''
    stopped = stop < 20
    c = np.where(is_ex, paid.mean(axis=1), rho * p50 * stopped.mean(axis=1))
    return c

def conformal_bar(maxvals, alpha=0.035):
    n = len(maxvals)
    k = min(int(np.ceil((n + 1) * (1 - alpha))), n)
    return float(np.sort(maxvals)[k - 1])

b17 = pd.read_csv(BRIDGE / "b17_exceedance_noisy.csv")
rows20, rows22 = [], []
g6_detail = {}
PI_OPT = {}      # (ab, tag, x_i, rho) -> pibar*
for ab in SCHEDULES:
    tr = TRUTH[ab]
    bills_tr = BILLS_T[ab][tr]
    b2050_tr = B2050[ab][tr]
    for tag in [lvtag(lv) for lv in LEVELS]:
        lv = TAG2LV[tag]
        exa = RES[(ab, tag)]["ex"].astype(float)
        for x_i, xm in enumerate(XMULTS):
            X = float(xm * P50BILL[ab])
            is_ex = b2050_tr > X
            n_ex, n_non = int(is_ex.sum()), int((~is_ex).sum())
            if n_ex < MIN_SIDE or n_non < MIN_SIDE:
                continue
            exx = exa[:, :, :, x_i]
            # risk over the threshold grid for every rho
            outs = [stop_outcomes(exx, bills_tr, is_ex, X, pb) for pb in PIBAR_ALL]
            C = np.stack([[bayes_risk(s, p, is_ex, rho, P50BILL[ab]) for (s, p, _) in outs] for rho in RHOS])  # (nR, nPi, nW)
            Rm = C.mean(axis=2)                                        # (nR, nPi)
            r_ledger = float(Rm[0, -1])
            for r_i, rho in enumerate(RHOS):
                j = int(np.argmin(Rm[r_i]))
                pb = float(PIBAR_ALL[j])
                PI_OPT[(ab, tag, x_i, rho)] = pb
                s, p, _ = outs[j]
                stopped_non = (s[~is_ex] < 20).mean()
                ci = boot_ci(C[r_i, j])
                rows20.append(dict(schedule=ab, sigma=lv[0], tau=lv[1], mult=xm, X_B=round(X, 1),
                                   prior_exceed_sample=round(n_ex / N_TRUTH, 3), n_exceed=n_ex, n_nonexceed=n_non,
                                   rho=rho, pi_bar_opt=pb if pb <= 1 else np.nan, ledger_only=bool(pb > 1),
                                   risk_B=round(float(Rm[r_i, j]), 4), risk_ci_lo=round(ci[0], 4), risk_ci_hi=round(ci[1], 4),
                                   risk_ledger_only_B=round(r_ledger, 4),
                                   frac_recovered=round(1 - float(Rm[r_i, j]) / r_ledger, 4) if r_ledger > 0 else np.nan,
                                   false_stop_rate=round(float(stopped_non), 4),
                                   stop_year_med_exceed=float(np.median(2031 + s[is_ex])),
                                   paid_at_stop_med_B=round(float(np.median(p[is_ex])), 2),
                                   paid_ledger_med_B=round(float(np.median(outs[-1][1][is_ex])), 2)))
                assert Rm[r_i, j] <= r_ledger + 1e-12
            # ---- today's rule as a reference point: the conformal 5% alarm ----------------
            mx_non = exx[~is_ex].max(axis=2)                          # (n_non, R) running max
            c_all = conformal_bar(mx_non.ravel())
            hit_c = (exx > c_all)
            first_c = np.where(hit_c.any(axis=2), hit_c.argmax(axis=2), 20)
            ledger = (bills_tr <= X).sum(axis=1)
            stop_c = np.minimum(first_c, ledger[:, None])
            paid_c = bills_tr[np.arange(N_TRUTH)[:, None], np.clip(stop_c, 0, 19)]
            fsr_in = float((stop_c[~is_ex] < 20).mean())
            # two-fold by-world cross-fit of the false-stop rate
            non_idx = np.flatnonzero(~is_ex)
            hv = np.zeros(N_TRUTH, bool); hv[non_idx[HALF_A[ab][tr][non_idx]]] = True
            fsr_cf = []
            for fit, ev in ((hv, ~hv & ~is_ex), (~hv & ~is_ex, hv)):
                if fit.sum() < 10 or ev.sum() < 10:
                    continue
                c_f = conformal_bar(exx[fit].max(axis=2).ravel())
                fsr_cf.append(float(((exx[ev] > c_f).any(axis=2)).mean()))
            fsr_cf = float(np.mean(fsr_cf)) if fsr_cf else np.nan
            paid_c_med = float(np.median(paid_c[is_ex]))
            # implied false-stop price: the rho whose Bayes rule matches the conformal false-stop rate
            fsr_grid = np.array([(outs[k_][0][~is_ex] < 20).mean() for k_ in range(len(PIBAR_ALL))])
            best = []
            for rho in RHO_FINE:
                Rr = np.array([bayes_risk(s, p, is_ex, rho, P50BILL[ab]).mean() for (s, p, _) in outs])
                best.append(fsr_grid[int(np.argmin(Rr))])
            best = np.array(best)
            i_r = int(np.argmin(np.abs(best - fsr_in)))
            rho_imp = float(RHO_FINE[i_r])
            r_conf = {rho: float(bayes_risk(stop_c, paid_c, is_ex, rho, P50BILL[ab]).mean()) for rho in RHOS}
            row22 = dict(schedule=ab, sigma=lv[0], tau=lv[1], mult=xm, X_B=round(X, 1), bar=round(c_all, 4),
                         false_stop_rate_insample=round(fsr_in, 4), false_stop_rate_crossfit=round(fsr_cf, 4),
                         paid_at_det_med_B=round(paid_c_med, 2), stop_year_med=float(np.median(2031 + stop_c[is_ex])),
                         rho_implied=round(rho_imp, 3), rho_match_gap=round(float(abs(best[i_r] - fsr_in)), 4),
                         **{f"risk_conformal_rho{rho}_B": round(v, 4) for rho, v in r_conf.items()})
            if xm == X_HEAD:
                bref = b17[(b17["schedule"] == ab) & (b17["sigma"] == lv[0]) & (b17["tau"] == lv[1]) & (b17["mult"] == X_HEAD)]
                if len(bref):
                    lo_, hi_ = float(bref["paid_at_det_p25_2024B"].iloc[0]), float(bref["paid_at_det_p75_2024B"].iloc[0])
                    row22.update(b17_p25_B=lo_, b17_p75_B=hi_, b17_p50_B=float(bref["paid_at_det_p50_2024B"].iloc[0]),
                                 within_b17_iqr=bool(lo_ <= paid_c_med <= hi_))
                    if lv == LV_MID:
                        g6_detail[ab] = (round(paid_c_med, 1), lo_, hi_)
            rows22.append(row22)
p20 = pd.DataFrame(rows20); p20.to_csv(EXPORTS / "p20_stopping_bayes.csv", index=False)
p22 = pd.DataFrame(rows22); p22.to_csv(EXPORTS / "p22_conformal_reference.csv", index=False)
VERDICT.append(("gate", "G5", "PASS", "Bayes risk of the optimal threshold <= ledger-only risk at every rho (search verified)"))
g6_ok = all(lo_ <= v <= hi_ for v, lo_, hi_ in g6_detail.values())
VERDICT.append(("gate", "G6", "PASS" if g6_ok else "DISCLOSED",
                "conformal reference (1.5x cap, mid noise) paid-at-detection median vs published b17 IQR "
                f"(different truth sample): {g6_detail}"))
h20 = p20[(p20["sigma"] == LV_MID[0]) & (p20["mult"] == X_HEAD)]
print("mid noise, cap 1.5x the P50 bill — the Bayes rule by false-stop price rho:")
print(h20.pivot_table(index="schedule", columns="rho", values=["pi_bar_opt", "frac_recovered", "false_stop_rate"])
      .reindex(SCHEDULES).round(3).to_string())
print("\nimplied false-stop price of today's 5% conformal rule (mid noise, 1.5x):")
print(p22[(p22["sigma"] == LV_MID[0]) & (p22["mult"] == X_HEAD)].set_index("schedule")[
    ["false_stop_rate_insample", "false_stop_rate_crossfit", "paid_at_det_med_B", "rho_implied", "within_b17_iqr"]].to_string())
""")

code(r"""# y03: Bayes risk against the false-stop price, cap = 1.5x the P50 bill
fig, axes = plt.subplots(2, 3, figsize=(ps.W3, 6.2))
for ax, ab in zip(axes.flat, SCHEDULES):
    f = p20[(p20["schedule"] == ab) & (p20["mult"] == X_HEAD)]
    if f.empty:
        ax.text(0.5, 0.5, "cell omitted:\nfewer than 30 worlds on one side", ha="center", va="center",
                transform=ax.transAxes, fontsize=7, color=ps.MUTED)
        ax.set_title(ps.SCHED_SHORT[ab]); continue
    for lv in LEVELS:
        g_ = f[(f["sigma"] == lv[0]) & (f["tau"] == lv[1])].sort_values("rho")
        xd = g_["rho"] * P50BILL[ab]                                  # price in 2024 $B
        ax.plot(xd, g_["risk_B"], color=ps.SCHED_C[ab], **LV_STYLE[lv])
        ax.fill_between(xd, g_["risk_ci_lo"], g_["risk_ci_hi"], color=ps.SCHED_C[ab], alpha=0.10, lw=0)
    ax.axhline(float(f["risk_ledger_only_B"].iloc[0]), color=ps.BASE_C, lw=0.9, ls="--")
    c22 = p22[(p22["schedule"] == ab) & (p22["mult"] == X_HEAD) & (p22["sigma"] == LV_MID[0])]
    if len(c22):
        rr = float(c22["rho_implied"].iloc[0])
        # the conformal rule's own risk at its implied rho (interpolated over the RHOS columns)
        rv = np.interp(np.log(rr), np.log(RHOS), [float(c22[f"risk_conformal_rho{rho}_B"].iloc[0]) for rho in RHOS])
        ax.plot([rr * P50BILL[ab]], [rv], marker="D", ms=4, color=ps.ACCENT["red"], ls="none")
    price_axis(ax, P50BILL[ab], "price of a false stop (2024 $B)")
    ax.set_ylim(0, None)
    ax.set_title(ps.SCHED_SHORT[ab], pad=22)
for ax in axes[:, 0]:
    ax.set_ylabel("expected loss of the stopping rule\n(2024 $B)")
handles = [Line2D([], [], color="0.3", label="Bayes rule, " + LV_LABEL[lv], **LV_STYLE[lv]) for lv in LEVELS]
handles += [Line2D([], [], color=ps.BASE_C, lw=0.9, ls="--", label="ledger only (stop when spend reaches the cap)"),
            Line2D([], [], color=ps.ACCENT["red"], marker="D", ms=4, ls="none",
                   label="today's 5% false-alarm rule at its implied false-stop price")]
fig.tight_layout()
fig.legend(handles=handles, ncol=3, fontsize=6.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 0.0))
ps.savefig(fig, FIGURES / "y03_bayes_risk_frontier.png")
plt.show()

# y03b: the optimal threshold and its false-stop rate against rho (mid noise, all caps)
fig, axes = plt.subplots(2, 6, figsize=(ps.W3 * 1.15, 5.0))
for i, ab in enumerate(SCHEDULES):
    ax, axl = axes[0, i], axes[1, i]
    for xm, ls in zip(XMULTS, ["-", "--", "-.", ":"]):
        g_ = p20[(p20["schedule"] == ab) & (p20["mult"] == xm) & (p20["sigma"] == LV_MID[0])].sort_values("rho")
        if g_.empty:
            continue
        xd = g_["rho"] * P50BILL[ab]
        ax.plot(xd, g_["pi_bar_opt"].fillna(1.0), color=ps.SCHED_C[ab], ls=ls, lw=1.3, marker="o", ms=2.2)
        axl.plot(xd, g_["false_stop_rate"], color=ps.SCHED_C[ab], ls=ls, lw=1.3, marker="o", ms=2.2)
    ax.set_title(ps.SCHED_SHORT[ab], pad=22)
    price_axis(ax, P50BILL[ab], "")
    price_axis(axl, P50BILL[ab], "price of a false stop (2024 $B)")
    ax.set_ylim(0, 1.02); axl.set_ylim(0, None)
axes[0, 0].set_ylabel("optimal posterior threshold\n(stop when P(bill > cap) reaches it)")
axes[1, 0].set_ylabel("false-stop rate of the\noptimal rule")
handles = [Line2D([], [], color="0.3", ls=ls, lw=1.3, label=f"cap {xm}x the median-world bill") for xm, ls in zip(XMULTS, ["-", "--", "-.", ":"])]
fig.tight_layout()
fig.legend(handles=handles, ncol=4, fontsize=6.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 0.0))
ps.savefig(fig, FIGURES / "y03b_threshold_vs_rho.png")
plt.show()
""")

md(r"""### G7 — the optimal-stopping check (least-squares Monte Carlo)

The threshold family may leave value on the table. A backward induction over
the simulated histories estimates the optimal stopping rule with state (the
posterior probability of exceeding the cap; spend itself is not a state variable — in
the model the outlay ledger is the exact shadow-price stream and would identify the
world, so the registered additive-only rule keeps it out; repair R1, 2026-09-09):
at each year the expected loss of stopping now and the expected loss of
continuing are both regressed on the state, and the rule stops when the first
is smaller. Fitted on half the truth worlds, scored on the other half, then
swapped. The threshold rule's risk should lie within the bootstrap interval of
the LSMC risk; if not, the gap is disclosed.""")

code(r"""def lsmc_policy(exx, bills_tr, is_ex, X, rho, p50, fit_mask):
    '''backward induction on fit paths; returns per-year regression coefficients (stop, continue)'''
    nW, R_, nY = exx.shape
    s_norm = bills_tr / X
    ledger = (bills_tr <= X).sum(axis=1)                   # forced end index for exceeding worlds
    end_loss = np.where(is_ex, bills_tr[np.arange(nW), np.clip(ledger, 0, nY - 1)], 0.0)   # (nW,)
    Cval = np.repeat(end_loss[:, None], R_, axis=1)         # realized loss if never stopping voluntarily
    coefs = {}
    def basis(pi, s):
        # state = the posterior only (repair R1, 2026-09-09): spend is the exact shadow-price
        # ledger, which would identify the world — the registered additive-only rule forbids it
        return np.stack([np.ones_like(pi), pi, pi ** 2, pi ** 3], axis=1)
    for yi in range(nY - 2, -1, -1):
        alive = fit_mask[:, None] & (ledger[:, None] > yi) & np.ones((nW, R_), bool)
        if alive.sum() < 30:
            continue
        pi = exx[:, :, yi][alive]; s = s_norm[:, yi][None, :].T.repeat(R_, 1)[alive]
        Phi = basis(pi, s)
        stop_loss = np.where(is_ex[:, None], bills_tr[:, yi][:, None], rho * p50).repeat(R_, 1)[alive]
        bS = np.linalg.lstsq(Phi, stop_loss, rcond=None)[0]
        bC = np.linalg.lstsq(Phi, Cval[alive], rcond=None)[0]
        coefs[yi] = (bS, bC)
        stop_now = (Phi @ bS) < (Phi @ bC)
        newC = Cval[alive].copy()
        newC[stop_now] = stop_loss[stop_now]
        Cval[alive] = newC
    return coefs

def lsmc_evaluate(exx, bills_tr, is_ex, X, rho, p50, coefs, ev_mask):
    nW, R_, nY = exx.shape
    s_norm = bills_tr / X
    ledger = (bills_tr <= X).sum(axis=1)
    stop = np.full((nW, R_), 20)
    for yi in range(nY - 1):
        if yi not in coefs:
            continue
        bS, bC = coefs[yi]
        pi = exx[:, :, yi]; s = np.repeat(s_norm[:, yi][:, None], R_, axis=1)
        Phi = np.stack([np.ones_like(pi), pi, pi ** 2, pi ** 3], axis=2)
        dec = (Phi @ bS) < (Phi @ bC)
        newly = dec & (stop == 20) & (ledger[:, None] > yi)
        stop[newly] = yi
    stop = np.minimum(stop, ledger[:, None])
    paid = bills_tr[np.arange(nW)[:, None], np.clip(stop, 0, nY - 1)]
    c = bayes_risk(stop, paid, is_ex, rho, p50)
    return c[ev_mask]

rows21 = []
for ab in SCHEDULES:
    tr = TRUTH[ab]; bills_tr = BILLS_T[ab][tr]; is_ex = B2050[ab][tr] > X_HEAD * P50BILL[ab]
    X = float(X_HEAD * P50BILL[ab])
    if is_ex.sum() < MIN_SIDE or (~is_ex).sum() < MIN_SIDE:
        continue
    exx = RES[(ab, lvtag(LV_MID))]["ex"].astype(float)[:, :, :, XMULTS.index(X_HEAD)]
    hA = HALF_A[ab][tr]
    for rho in (0.25, 1.0):
        c_lsmc, c_thr = [], []
        for fit, ev in ((hA, ~hA), (~hA, hA)):
            coefs = lsmc_policy(exx, bills_tr, is_ex, X, rho, P50BILL[ab], fit)
            c_lsmc.append(lsmc_evaluate(exx, bills_tr, is_ex, X, rho, P50BILL[ab], coefs, ev))
            # the threshold rule, fitted on the same half
            Rfit = []
            for pb in PIBAR_ALL:
                s_, p_, _ = stop_outcomes(exx, bills_tr, is_ex, X, pb)
                Rfit.append(bayes_risk(s_, p_, is_ex, rho, P50BILL[ab])[fit].mean())
            pb = PIBAR_ALL[int(np.argmin(Rfit))]
            s_, p_, _ = stop_outcomes(exx, bills_tr, is_ex, X, pb)
            c_thr.append(bayes_risk(s_, p_, is_ex, rho, P50BILL[ab])[ev])
        c_l = np.concatenate(c_lsmc); c_t = np.concatenate(c_thr)
        n_ = len(c_l)
        bi = rng_boot.integers(0, n_, size=(N_BOOT, n_))
        d_ = (c_t - c_l)
        ci = np.percentile(d_[bi].mean(axis=1), [2.5, 97.5])
        rows21.append(dict(schedule=ab, rho=rho, X_B=round(X, 1), risk_lsmc_B=round(float(c_l.mean()), 4),
                           risk_threshold_B=round(float(c_t.mean()), 4), gap_B=round(float(d_.mean()), 4),
                           gap_ci_lo=round(float(ci[0]), 4), gap_ci_hi=round(float(ci[1]), 4),
                           threshold_not_dominated=bool(ci[0] <= 0.0 <= ci[1] or d_.mean() <= 0)))
p21 = pd.DataFrame(rows21); p21.to_csv(EXPORTS / "p21_stopping_lsmc.csv", index=False)
VERDICT.append(("gate", "G7", "PASS" if p21["threshold_not_dominated"].all() else "DISCLOSED",
                "threshold-rule risk minus LSMC optimal-stopping risk (out-of-sample halves, mid noise, 1.5x): "
                + str({(r.schedule, r.rho): (r.gap_B, r.gap_ci_lo, r.gap_ci_hi) for r in p21.itertuples()})))
print(p21.to_string(index=False))
""")

# ====================================================================================
md(r"""## C2 — The abandonment trigger for grants

The feasibility twin of the stopping decision. State: the posterior probability
that the world is never credit-feasible within the horizon (its last build year
still needs an above-ceiling rate). Actions: stop grants or continue. Loss:
grants paid before the stop in a never-feasible world are wasted; stopping in a
world that would have graduated is priced at ρ_g times the median-world bill.
The Bayes rule is the threshold β* that minimizes the Bayes risk; its value is
the risk reduction against never stopping. Labeled a lower bound on the
optimal-stopping value, and never "value of information for delivery".""")

code(r"""BETAS = np.concatenate([np.round(np.arange(0.05, 1.0001, 0.05), 2), [1.5]])
rows33 = []
for ab in SCHEDULES:
    tr = TRUTH[ab]
    K = len(BUILD_TS[ab]); ts = np.array(BUILD_TS[ab])
    for c_i, (cap, cn) in enumerate(NG_COLS):
        never = NGI[ab][tr, c_i] > 0.5
        n_ng, n_gr = int(never.sum()), int((~never).sum())
        Gtr = GRANTCUM[(ab, cap, "base", cn)][tr]                   # (nW, K) grant $B through year k
        for tag in [lvtag(lv) for lv in LEVELS]:
            lv = TAG2LV[tag]
            if n_ng < MIN_SIDE or n_gr < MIN_SIDE:
                rows33.append(dict(schedule=ab, sigma=lv[0], tau=lv[1], cap=cap, cut=cn, n_never=n_ng, n_graduate=n_gr,
                                   omitted="K4: fewer than 30 truth worlds on one side"))
                continue
            png = RES[(ab, tag)]["ng"][:, :, :, c_i].astype(float)  # (nW, K, R)
            outs = []
            for b in BETAS:
                hit = png >= b
                first = np.where(hit.any(axis=1), hit.argmax(axis=1), K)       # (nW, R) obs index or K
                gpaid = Gtr[np.arange(N_TRUTH)[:, None], np.clip(first, 0, K - 1)]
                gpaid = np.where(first >= K, Gtr[:, -1][:, None], gpaid)
                outs.append((first, gpaid))
            for rho in RHOS:
                C = np.stack([np.where(never, g.mean(axis=1), rho * P50BILL[ab] * (f < K).mean(axis=1))
                              for f, g in outs])                                # (nB, nW)
                Rm = C.mean(axis=1)
                j = int(np.argmin(Rm)); b = float(BETAS[j])
                f, g = outs[j]
                r_never = float(Rm[-1])
                ci = boot_ci(C[j])
                stopped_ng = f[never] < K
                rows33.append(dict(schedule=ab, sigma=lv[0], tau=lv[1], cap=cap, cut=cn, n_never=n_ng, n_graduate=n_gr,
                                   share_never_sample=round(n_ng / N_TRUTH, 3), rho_g=rho,
                                   beta_opt=b if b <= 1 else np.nan, never_stop=bool(b > 1),
                                   risk_B=round(float(Rm[j]), 4), risk_ci_lo=round(ci[0], 4), risk_ci_hi=round(ci[1], 4),
                                   risk_never_stop_B=round(r_never, 4), value_B=round(r_never - float(Rm[j]), 4),
                                   frac_recovered=round(1 - float(Rm[j]) / r_never, 4) if r_never > 0 else np.nan,
                                   false_abandon_rate=round(float((f[~never] < K).mean()), 4),
                                   T_abandon_med=float(np.median(ts[np.clip(f[never][stopped_ng], 0, K - 1)])) if stopped_ng.any() else np.nan,
                                   grants_saved_in_never_B=round(float((Gtr[never, -1][:, None] - g[never]).mean()), 4)))
p33 = pd.DataFrame(rows33); p33.to_csv(EXPORTS / "p33_abandonment_bayes.csv", index=False)
h33 = p33[(p33["sigma"] == LV_MID[0]) & (p33["cap"] == 0.60) & (p33["cut"] == "reg") & p33["rho_g"].notna()]
print("mid noise, 60% ceiling, registered cushion — the abandonment rule by false-abandonment price:")
print(h33.pivot_table(index="schedule", columns="rho_g", values=["beta_opt", "frac_recovered", "false_abandon_rate"])
      .reindex(SCHEDULES).round(3).to_string())

# y05: abandonment Bayes risk against the false-abandonment price (60% ceiling, registered cushion)
fig, axes = plt.subplots(2, 3, figsize=(ps.W3, 6.2))
for ax, ab in zip(axes.flat, SCHEDULES):
    f = p33[(p33["schedule"] == ab) & (p33["cap"] == 0.60) & (p33["cut"] == "reg") & p33["rho_g"].notna()]
    if f.empty:
        ax.text(0.5, 0.5, "cell omitted:\nfewer than 30 worlds on one side", ha="center", va="center",
                transform=ax.transAxes, fontsize=7, color=ps.MUTED)
        ax.set_title(ps.SCHED_SHORT[ab]); continue
    for lv in LEVELS:
        g_ = f[(f["sigma"] == lv[0]) & (f["tau"] == lv[1])].sort_values("rho_g")
        xd = g_["rho_g"] * P50BILL[ab]
        ax.plot(xd, g_["risk_B"], color=ps.SCHED_C[ab], **LV_STYLE[lv])
        ax.fill_between(xd, g_["risk_ci_lo"], g_["risk_ci_hi"], color=ps.SCHED_C[ab], alpha=0.10, lw=0)
    ax.axhline(float(f["risk_never_stop_B"].iloc[0]), color=ps.BASE_C, lw=0.9, ls="--")
    price_axis(ax, P50BILL[ab], "price of wrongly abandoning a world that would graduate (2024 $B)")
    ax.set_ylim(0, None)
    ax.set_title(ps.SCHED_SHORT[ab], pad=22)
for ax in axes[:, 0]:
    ax.set_ylabel("expected loss of the grant rule\n(2024 $B)")
handles = [Line2D([], [], color="0.3", label="Bayes abandonment rule, " + LV_LABEL[lv], **LV_STYLE[lv]) for lv in LEVELS]
handles.append(Line2D([], [], color=ps.BASE_C, lw=0.9, ls="--", label="never stop grants"))
fig.tight_layout()
fig.legend(handles=handles, ncol=2, fontsize=6.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 0.0))
ps.savefig(fig, FIGURES / "y05_abandonment_frontier.png")
plt.show()
""")

# ====================================================================================
md(r"""## Predictions, verdict, manifest

The five registered predictions are scored here exactly as written in
`methods.md`; a miss is recorded, not repaired. The verdict table `p90` is the
only source from which paper text may quote this folder's numbers.""")

code(r"""# P1: fraction of remaining EVPI recovered at the last usable observation < 0.5 (mid noise, alpha 0.90)
h = p12[(p12["alpha"] == ALPHA_HEAD) & (p12["sigma"] == LV_MID[0]) & (p12["k"] >= 0)]
lastk = h[h["k"] == h.groupby("schedule")["k"].transform("max")].set_index("schedule")["frac_recovered_dollar"].reindex(SCHEDULES)
VERDICT.append(("prediction", "P1", "CONFIRMED" if (lastk < 0.5).all() else "MISSED",
                "dollar EVSI/EVPI at k = K-2, mid noise, alpha 0.90: " + str(lastk.round(3).to_dict())))
# P2: group EVPPI >= 70% of EVPI
g2_ = p11[(p11["alpha"] == ALPHA_HEAD) & (p11["dial"].str.startswith("group")) & (p11["bins"] == 49)].set_index("schedule")["share_of_evpi_dollar"].reindex(SCHEDULES)
VERDICT.append(("prediction", "P2", "CONFIRMED" if (g2_ >= 0.70).all() else "MISSED",
                "group {lr_smr, boak_smr} EVPPI share of dollar EVPI: " + str(g2_.round(3).to_dict())))
# P3: at the 0.60 ceiling (registered cushion, base band) no schedule reaches coverage 0.90 at T <= 2044
c3 = p31[(p31["cap"] == 0.60) & (p31["cut"] == "reg") & (p31["band"] == "base") & (p31["T"] <= 2044)]
r3 = c3.groupby("schedule")["coverage"].max().reindex(SCHEDULES)
VERDICT.append(("prediction", "P3", "CONFIRMED" if (r3 < 0.90).all() else "MISSED",
                "max coverage at T <= 2044, 60% ceiling, registered cushion, base band: " + str(r3.round(3).to_dict())))
# P4: the abandonment rule at rho_g = 0.5 lowers the grant risk below never-stop in every schedule with a non-empty window
c4 = p33[(p33["sigma"] == LV_MID[0]) & (p33["cap"] == 0.60) & (p33["cut"] == "reg") & (p33["rho_g"] == 0.5)]
r4 = c4.set_index("schedule")["value_B"].reindex(SCHEDULES)
VERDICT.append(("prediction", "P4", "CONFIRMED" if (r4.dropna() > 0).all() else "MISSED",
                "value of early abandonment at rho_g = 0.5 (2024 $B; NaN = cell omitted under K4): " + str(r4.round(3).to_dict())))
# P5: the implied false-stop price of the 5% conformal rule > 0.5 (mid noise, 1.5x)
c5 = p22[(p22["sigma"] == LV_MID[0]) & (p22["mult"] == X_HEAD)].set_index("schedule")["rho_implied"].reindex(SCHEDULES)
VERDICT.append(("prediction", "P5", "CONFIRMED" if (c5.dropna() > 0.5).all() else "MISSED",
                "implied false-stop price rho_5% (x median-world bill): " + str(c5.round(3).to_dict())))
# K1: ESS shading
k1 = p12[(p12["alpha"] == ALPHA_HEAD) & (p12["sigma"] == LV_MID[0]) & (p12["k"] >= 0) & (p12["ess_q10"] < ESS_FLOOR)]
VERDICT.append(("kill", "K1", "DISCLOSED" if len(k1) else "PASS",
                "observation years with leave-one-out q10 ESS < 100 at mid noise: "
                + str(k1.groupby("schedule")["year"].apply(list).to_dict())))
# K3 / K5: the cut-off picks
k3 = p32[(p32["cut"] == "reg") & (p32["range_flag"])][["schedule", "cap", "alpha"]].drop_duplicates().values.tolist()
VERDICT.append(("kill", "K3", "DISCLOSED" if k3 else "PASS", f"T_alpha quoted as a range where the E5 band ends disagree: {k3}"))
k5 = p32[(p32["cut"] == "reg") & (p32["band"] == "base") & (~p32["within_horizon"])][["schedule", "cap", "alpha"]].values.tolist()
VERDICT.append(("kill", "K5", "DISCLOSED" if k5 else "PASS",
                f"no cut-off year before the last build year reaches the coverage target in {len(k5)} of "
                f"{int(((p32['cut'] == 'reg') & (p32['band'] == 'base')).sum())} (schedule, cap, alpha) cells: {k5}"))
# the window decision (v1.1 addendum): headline years and their disclosures
hb = p34[(p34["rule"] == "bayes") & (p34["param"] == RHO_HEAD_WINDOW) & (p34["cap"] == 0.60) & (p34["cut"] == "reg")]
yrs = hb[hb["band"] == "base"].set_index("schedule")["T_pick"].reindex(SCHEDULES).astype(int).to_dict()
rngs = hb[hb["band"] == "base"].set_index("schedule")["T_range_over_rho"].reindex(SCHEDULES).to_dict()
bflag = hb[hb["band"] == "base"].set_index("schedule")["band_range_flag"].reindex(SCHEDULES).to_dict()
disp = p34[(p34["rule"] == "bayes") & (p34["param"] == RHO_HEAD_WINDOW) & (p34["cap"] == 0.60) & (p34["cut"] == "disp")
           & (p34["band"] == "base")].set_index("schedule")["T_pick"].reindex(SCHEDULES).astype(int).to_dict()
VERDICT.append(("window", "T_bayes", "REPORTED",
                f"last grant year minimizing expected loss at rho_g = 1, 60% ceiling, registered cushion, base band: {yrs}; "
                f"range over rho_g 0.1-2: {rngs}; moves across the E5 band ends: {bflag}; on the 3-point display twin: {disp}"))
c36 = p36[(p36["cut"] == "disp") & (p36["band"] == "base")]
VERDICT.append(("window", "T_common", "REPORTED",
                f"one window end for every schedule, {W_COMMON} (Ethan 2026-09-10): worlds graduating after it (display twin, base band) "
                + str({f"{r.schedule}@{r.cap}": r.share_graduating_after_common for r in c36.itertuples()})
                + "; last graduation year " + str({f"{r.schedule}@{r.cap}": r.complete_year for r in c36.itertuples()})))
hq = p34[(p34["rule"] == "cond_quantile") & (p34["cap"] == 0.60) & (p34["cut"] == "reg") & (p34["band"] == "base")]
VERDICT.append(("window", "T_condq", "REPORTED",
                "conditional-quantile window (worlds that ever graduate after needing grants), 60% ceiling: q75 "
                + str(hq[hq["param"] == 0.75].set_index("schedule")["T_pick"].reindex(SCHEDULES).astype(int).to_dict())
                + "; q90 " + str(hq[hq["param"] == 0.90].set_index("schedule")["T_pick"].reindex(SCHEDULES).astype(int).to_dict())))
# noise-monotonicity read (soft part of G3)
mono = []
for ab in SCHEDULES:
    hh = p12[(p12["schedule"] == ab) & (p12["alpha"] == ALPHA_HEAD) & (p12["k"] >= 0)]
    kk = hh["k"].max()
    v = [float(hh[(hh["k"] == kk) & (hh["sigma"] == lv[0]) & (hh["tau"] == lv[1])]["frac_recovered_dollar"].iloc[0]) for lv in LEVELS + [LV_SMALL]]
    mono.append((ab, [round(x, 3) for x in v]))
VERDICT.append(("note", "G3-soft", "DISCLOSED", "frac_recovered at k = K-2 by noise level [light, mid, heavy, small]: " + str(mono)))

p90 = pd.DataFrame(VERDICT, columns=["kind", "name", "result", "detail"])
p90.to_csv(EXPORTS / "p90_verdict.csv", index=False)
print(p90.to_string(index=False))

manifest = sorted(p.name for p in EXPORTS.glob("p*.csv")) + sorted(p.name for p in EXPORTS.glob("p*.npz")) \
    + sorted(p.name for p in FIGURES.glob("y*.png"))
for name in manifest:
    p_ = (EXPORTS / name) if name.endswith((".csv", ".npz")) else (FIGURES / name)
    print(f"{p_.relative_to(HERE)}  ({p_.stat().st_size / 1024:.0f} kB)")
""")

nb["cells"] = C
out = "voi.ipynb"
nbf.write(nb, out)
print(f"wrote {out} with {len(C)} cells")
