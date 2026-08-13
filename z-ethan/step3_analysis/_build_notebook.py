"""Generate step3_analysis.ipynb. Edit cell sources here, re-run to regenerate.

Same convention as z-ethan/step3_checks/_build_notebook.py: the notebook is the
deliverable; this builder exists so the notebook can be regenerated and diffed as
plain python. Run with the playground-env python.

All notebook markdown text follows ASD-STE100 Simplified Technical English:
short sentences, active voice, one instruction per sentence, approved words.
"""
import nbformat as nbf

nb = nbf.v4.new_notebook()
nb.metadata = {
    "kernelspec": {"name": "python3", "display_name": "Python 3 (ipykernel)", "language": "python"},
    "language_info": {"name": "python", "version": "3.12"},
}

C = []  # cells


def md(src):
    C.append(nbf.v4.new_markdown_cell(src))


def code(src):
    C.append(nbf.v4.new_code_cell(src))


# ================================================================================
# S0 — header + setup
# ================================================================================

md("""# Step 3 analysis — 25 production runs

This notebook characterizes the 25 production run outputs from NREL.
The output files are in `D:\\ReEDS files\\nuclear-learning\\smr100 first run`.
The run matrix is `cases_nuclearlearning_smr100.csv`
(18 smr100 cases + 6 large100 cases + 1 equality case).
The QA notebook `z-ethan/step3_checks/step3_output_checks.ipynb` already passed
all 44 pass/fail tests on these files. This notebook does the analysis that
follows: the mandate duals, the system costs, the system NPV, and the years in
which the mandates do not bind.

Sections:

- S1 — run inventory and mandate schedules.
- S2 — where the mandates bind, and where they do not (adverse findings first).
- S3 — dual price trajectories (the headline object).
- S4 — dual price against schedule ambition (cross-section).
- S5 — bridge shape: dual decay metrics.
- S6 — system costs.
- S7 — system NPV.
- S8 — rental transfer, ITC translation, and fiscal outputs.
- S9 — equality-flip note.
- S10 — caveats and output manifest.

**Units.** The h5 files hold dollars of 2004. This notebook shows dollars of
2024 in all figures and tables. Dual prices show as $/kW-yr. Costs show as
billion $ per year. NPV shows as billion $.

**Two standing rules.**

1. Each schedule x percentile case is its own joint cost-world draw. The clean
   comparison axes are: (a) dual trajectories, (b) percentile fans inside one
   schedule, and (c) smr100 against large100 at p50 as conditional what-ifs.
   Comparisons across schedules mix the mandate and the drawn cost world. They
   are descriptive, not causal.
2. Adverse results get equal prominence. The notebook reports slack mandates,
   zero duals, and large subsidies as visibly as the favorable results. The
   notebook does not rank the trajectories by desirability.

Run this notebook on the **playground-env** kernel, from `z-ethan/step3_analysis/`.
This notebook only reads the files on drive D. It does not change them.""")

code("""import json
from pathlib import Path

import h5py
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

pd.set_option("display.width", 200)

HERE = Path.cwd()
assert HERE.name == "step3_analysis", f"run from z-ethan/step3_analysis/, not {HERE}"
REPO = HERE.parents[1]
EXPORTS = HERE / "exports"
FIGURES = HERE / "figures"
EXPORTS.mkdir(exist_ok=True)
FIGURES.mkdir(exist_ok=True)
CHECKS_EXPORTS = REPO / "z-ethan" / "step3_checks" / "exports"

H5_DIR = Path("D:/ReEDS files/nuclear-learning/smr100 first run")

# ---- case matrix ----------------------------------------------------------------
cases_csv = pd.read_csv(REPO / "cases_nuclearlearning_smr100.csv", index_col=0)
CASES = [c for c in cases_csv.columns if c != "Default Value"]
assert len(CASES) == 25, CASES

def sw(case, name):
    \"\"\"Read one switch value for one case. An empty cell uses the default value.\"\"\"
    v = cases_csv.loc[name, case]
    if pd.isna(v) or str(v).strip() == "":
        v = cases_csv.loc[name, "Default Value"]
    return str(v).strip()

META = {}
for c in CASES:
    ts = sw(c, "GSw_NuclearCapMandateTechScen")
    META[c] = dict(
        scen=sw(c, "GSw_NuclearCapMandateScen"),
        mode=int(float(sw(c, "GSw_NuclearCapMandate"))),
        techscen=ts,
        mandated_tech={"smr": "nuclear-smr", "large": "nuclear"}[ts],
    )
SMR_CASES = [c for c in CASES if META[c]["techscen"] == "smr"]
LARGE_CASES = [c for c in CASES if META[c]["techscen"] == "large"]
SCHEDULES = ["eia", "aj", "iaea", "mck", "cop28", "eo"]      # ordered by 2050 ambition
SCHED_GW = {"eia": 117.3, "aj": 134.0, "iaea": 172.3, "mck": 200.0,
            "cop28": 300.0, "eo": 400.0}                     # 2050 schedule ambition, GW
SCHED_LABEL = {"eia": "EIA AEO high (117 GW)", "aj": "Abou-Jaoude (134 GW)",
               "iaea": "IAEA high (172 GW)", "mck": "McKinsey (200 GW)",
               "cop28": "COP28 (300 GW)", "eo": "EO 2025 (400 GW)"}
REF = "smr100_eia_p50"     # reference case for single-case exhibits

def parse_case(c):
    \"\"\"Split a case name into (family, schedule, percentile, variant).\"\"\"
    fam = "large" if c.startswith("large100") else "smr"
    parts = c.split("_")
    return fam, parts[1], parts[2], ("eq" if c.endswith("_eq") else "")

H5 = {c: H5_DIR / f"test1_{c}_outputs.h5" for c in CASES}
missing = [c for c in CASES if not H5[c].exists()]
assert not missing, f"missing h5 files: {missing}"

# 2022$ -> 2004$ (ReEDS-internal dollars). deflator.csv: Deflator(t) relative to 2004.
DEFL = pd.read_csv(REPO / "inputs" / "financials" / "deflator.csv")
DEFL.columns = ["t", "Deflator"]
DEFL = DEFL.set_index("t")["Deflator"]
D2022 = float(DEFL.loc[2022])
TO2024 = 1.0 / float(DEFL.loc[2024])

# ---- self-contained outputs.h5 reader (no `reeds` import: env/DLL constraints) --
_CACHE = {}

def load(case, key):
    \"\"\"Read one report parameter from an outputs.h5 file as a DataFrame.
    Layout per reeds/io.py::write_output_to_h5: one group per parameter, a `columns`
    dataset for order, one dataset per column (byte strings) + float `Value`.
    Do not change the returned frame in place: it is cached.\"\"\"
    if (case, key) in _CACHE:
        return _CACHE[(case, key)]
    with h5py.File(H5[case], "r") as f:
        if key not in f:
            raise KeyError(f"{key} not in {H5[case].name}")
        g = f[key]
        cols = [c.decode() for c in g["columns"][:]]
        data = {}
        for c in cols:
            arr = g[c][:]
            data[c] = arr.astype(str) if arr.dtype.kind == "S" else arr
        df = pd.DataFrame(data)[cols]
    for c in ("t", "allt"):
        if c in df.columns:
            df[c] = df[c].astype(int)
    _CACHE[(case, key)] = df
    return df

def h5_keys(case):
    with h5py.File(H5[case], "r") as f:
        return sorted(f.keys())

print(f"repo: {REPO}")
print(f"cases: {len(CASES)} ({len(SMR_CASES)} smr100 + {len(LARGE_CASES)} large100, "
      f"incl. equality copy)")
print(f"2022$->2004$ deflator: {D2022:.6f}; 2004$->2024$: {TO2024:.4f}")
""")

code("""# ---- house figure style (same tokens as z-ethan/mc/npv_winner_check.ipynb) -------
COL = {"large": "#2a78d6", "smr": "#eb6834"}
INK, MUTED, FAINT, GRID_C, EDGE_C, SURFACE = ("#0b0b0b", "#52514e", "#898781",
                                              "#e1e0d9", "#c3c2b7", "#fcfcfb")
mpl.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": EDGE_C, "axes.labelcolor": MUTED, "text.color": INK,
    "xtick.color": FAINT, "ytick.color": FAINT, "axes.grid": True, "grid.color": GRID_C,
    "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlecolor": INK, "font.size": 9, "axes.titlesize": 10, "figure.dpi": 110,
    "legend.frameon": False,
})

# Schedule identity: one fixed, ambition-ordered hue per schedule (viridis segment;
# perceptually ordered and colorblind-safe). Never cycled; identity keeps its hue.
_ramp = mpl.cm.viridis(np.linspace(0.02, 0.72, len(SCHEDULES)))
SCHED_C = {s: mpl.colors.to_hex(c) for s, c in zip(SCHEDULES, _ramp)}
# Percentile weight inside a schedule hue: p05 light, p50 solid, p95 heavy-dashed.
PCT_STYLE = {"p05": dict(lw=1.2, alpha=0.55, ls="-"),
             "p50": dict(lw=2.2, alpha=1.00, ls="-"),
             "p95": dict(lw=1.6, alpha=0.85, ls="--")}

def savefig(fig, name):
    p = FIGURES / name
    fig.savefig(p, dpi=150, bbox_inches="tight")
    print(f"wrote {p.relative_to(HERE)}")

print("schedule colors:", SCHED_C)
""")

code("""# ---- real discount rate (same derivation as step3_checks B5) ----------------------
FIN_DIR = REPO / "inputs" / "financials"
YEARS = np.arange(2010, 2051)

sys_fin = pd.read_csv(FIN_DIR / "financials_sys_ATB2024.csv")
infl = pd.read_csv(FIN_DIR / "inflation_default.csv")
sys_fin = sys_fin.merge(infl, on="t", how="left")
sys_fin["d_nom"] = ((1 - sys_fin["debt_fraction"]) * (sys_fin["rroe_nom"] - 1)
                    + sys_fin["debt_fraction"] * (sys_fin["interest_rate_nom"] - 1)
                      * (1 - sys_fin["tax_rate"]) + 1)
sys_fin["d_real"] = sys_fin["d_nom"] / sys_fin["inflation_rate"]

def on_years(col):
    s = sys_fin.set_index("t")[col].reindex(range(1990, YEARS[-1] + 1)).ffill()
    return s.loc[YEARS].to_numpy(float)

D_REAL = on_years("d_real")
D_NOM = on_years("d_nom")
TAX = on_years("tax_rate")
IB = on_years("interest_rate_nom")
DR = float(np.mean(D_REAL))     # scalar real rate for the PV formulas (choice on record)

def yi(t):
    return int(t - YEARS[0])

print(f"d_real: min {D_REAL.min():.4f}, max {D_REAL.max():.4f}, mean DR = {DR:.4f}")
print(f"tax rate: {TAX.min():.3f}..{TAX.max():.3f}; d_nom mean {np.mean(D_NOM):.4f}")
""")

# ================================================================================
# data assembly
# ================================================================================

md("""## Data assembly

One pass reads the small keys from each of the 25 h5 files into tidy frames.
All later cells use these frames. They do not read the disk again.

The mandate and dual data come from the QA exports
`z-ethan/step3_checks/exports/duals_by_year.csv` and `overbuild_by_case.csv`.
Those files passed the QA tests. A spot test below re-derives three cases from
the h5 files and makes sure that the export is current.

Note: the model removes an all-zero dual parameter from the h5 file. Thus an
absent dual key means a zero dual. It does not mean lost data.""")

code("""# ---- mandate + dual frames from the QA exports ------------------------------------
DUALS = pd.read_csv(CHECKS_EXPORTS / "duals_by_year.csv")
OVB = pd.read_csv(CHECKS_EXPORTS / "overbuild_by_case.csv")
assert set(DUALS["case"]) == set(CASES) and set(OVB["case"]) == set(CASES)

for df in (DUALS,):
    fam, sched, pct, var = zip(*[parse_case(c) for c in df["case"]])
    df["family"], df["schedule"], df["pct"], df["variant"] = fam, sched, pct, var
DUALS["mandated"] = DUALS["mandate_MW"] > 0
DUALS["binding"] = DUALS["dual_2004_MWyr"] > 1.0          # QA convention
DUALS["clearly_slack"] = DUALS["mandated"] & (DUALS["slack_MW"] > 100)  # QA convention

YEARS_RUN = sorted(DUALS["t"].unique())
assert len(YEARS_RUN) == 16, YEARS_RUN
print(f"solve years: {YEARS_RUN}")
print(DUALS.head(3).to_string(index=False))
""")

code("""# ---- freshness spot test: the QA export matches the h5 files ----------------------
# Re-derive the dual and the mandated-tech capacity for three cases straight from
# the h5 files. If this fails, re-run z-ethan/step3_checks/step3_output_checks.ipynb
# to refresh the exports, then re-run this notebook.
SPOT = ["smr100_eia_p05", "smr100_eo_p95", "large100_eia_p50"]
for c in SPOT:
    keys = h5_keys(c)
    d_h5 = (load(c, "nuclear_cap_price").set_index("t")["Value"]
            if "nuclear_cap_price" in keys else pd.Series(dtype=float))
    cap = load(c, "cap")
    cap_h5 = cap[cap["i"] == META[c]["mandated_tech"]].groupby("t")["Value"].sum()
    exp = DUALS[DUALS["case"] == c].set_index("t")
    for t in YEARS_RUN:
        dv, cv = float(d_h5.get(t, 0.0)), float(cap_h5.get(t, 0.0))
        assert abs(exp.loc[t, "dual_2004_MWyr"] - dv) <= max(1e-4, 1e-6 * abs(dv)), (c, t)
        assert abs(exp.loc[t, "cap_MW"] - cv) <= 0.5, (c, t, exp.loc[t, "cap_MW"], cv)
print(f"QA export is current: {len(SPOT)} spot cases match the h5 files.")
""")

code("""# ---- one pass over the 25 files: costs, NPV inputs, ITC, finance -------------------
SC_ROWS, ZREP, RAWIO, OBJ, ITC_TOT = [], {}, {}, {}, {}
COSTCAP, FINMULT, FMDIFF, CAPNEW, PVF = {}, {}, {}, {}, {}
for c in CASES:
    scc = load(c, "systemcost").copy()
    scc["case"] = c
    SC_ROWS.append(scc)
    ZREP[c] = load(c, "z_rep").set_index("t")["Value"]
    RAWIO[c] = (load(c, "raw_inv_cost").set_index("t")["Value"],
                load(c, "raw_op_cost").set_index("t")["Value"])
    OBJ[c] = float(load(c, "objfn_raw")["Value"].iloc[0])
    ITC_TOT[c] = float(load(c, "tax_expenditure_itc")["Value"].sum())
    PVF[c] = load(c, "pvf_onm").set_index("t")["Value"]
    tech = META[c]["mandated_tech"]
    cc = load(c, "cost_cap")
    COSTCAP[c] = cc[cc["i"] == tech].groupby("t")["Value"].mean()   # 2004$/MW (i,t input)
    fmn = load(c, "cost_cap_fin_mult_noITC")
    FINMULT[c] = fmn[fmn["i"] == tech].set_index(["r", "t"])["Value"]   # per region
    fmi = load(c, "cost_cap_fin_mult")
    fmi = fmi[fmi["i"] == tech].set_index(["r", "t"])["Value"]
    FMDIFF[c] = float((fmi - FINMULT[c]).abs().max())    # 0 = no nuclear ITC in run
    cn = load(c, "cap_new_ann")
    CAPNEW[c] = cn[cn["i"] == tech].set_index(["r", "t"])["Value"]  # MW/yr, annualized
SYSCOST = pd.concat(SC_ROWS, ignore_index=True)
fam, sched, pct, var = zip(*[parse_case(c) for c in SYSCOST["case"]])
SYSCOST["family"], SYSCOST["schedule"], SYSCOST["pct"], SYSCOST["variant"] = fam, sched, pct, var
STREAMS = sorted(SYSCOST["sys_costs"].unique())
print(f"systemcost: {len(SYSCOST)} rows, {len(STREAMS)} streams; "
      f"objfn_raw range {min(OBJ.values()):.4e} .. {max(OBJ.values()):.4e} (2004$)")
""")

# ================================================================================
# S1 — inventory + schedules
# ================================================================================

md("""## S1 — Run inventory and mandate schedules

The six deployment schedules form an ambition ladder from 117 GW to 400 GW of
national nuclear capacity in 2050. Each smr100 case forces the schedule with a
national **additions-basis** floor on the technology `nuclear-smr`: the
trajectory counts cumulative post-2030 builds, with backfill for retirements.
Each large100 case forces the same schedule with a **fleet-inclusive** floor on
the technology `nuclear` (all vintages count), so its trajectory starts at the
existing fleet in 2024.

The percentiles p05 / p50 / p95 are joint cost-world draws. Each one is the
draw at that percentile of the discounted SMR program NPV over 10,000 draws for
that schedule. They are real sampled worlds, not pointwise envelopes.

The folder also holds three copies of the old pilot runs
(`test1_smr100_eia_{lo,mid,hi}_outputs.h5`). They are not part of step 3.
This notebook does not read them.""")

code("""# ---- t01: case inventory ----------------------------------------------------------
NL_DIR = REPO / "inputs" / "nuclear_learning"

def trajectory(scen):
    tr = pd.read_csv(NL_DIR / f"nuclear_cap_trajectory_{scen}.csv")
    tr.columns = [c.lstrip("*") for c in tr.columns]
    return tr.set_index(tr.columns[0])["MW"]

TRAJ = {c: trajectory(META[c]["scen"]) for c in CASES}

inv_rows = []
for c in CASES:
    f, s, p, v = parse_case(c)
    tr = TRAJ[c]
    mand_years = [t for t in YEARS_RUN if tr.get(t, 0) > 0]
    o = OVB.set_index("case").loc[c]
    inv_rows.append(dict(
        case=c, schedule=s, ambition_2050_GW=SCHED_GW[s], pct=p,
        variant=(v or "floor"), mandated_tech=META[c]["mandated_tech"],
        basis=("fleet-inclusive" if f == "large" else "additions"),
        n_mandated_years=int(o["n_mandated_years"]),
        first_mandated_year=(min(mand_years) if mand_years else None),
        mandate_2050_GW=round(float(tr.get(2050, 0.0)) / 1e3, 1),
        n_binding_years=int(o["n_binding_years"]),
        n_slack_years=int(o["n_slack_years"]),
        objfn_raw_2004=OBJ[c],
    ))
t01 = pd.DataFrame(inv_rows)
t01.to_csv(EXPORTS / "t01_case_inventory.csv", index=False)
print(t01.drop(columns="objfn_raw_2004").to_string(index=False))
""")

code("""# ---- f01: the twelve mandate trajectories ------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharex=True)
for ax, fam, ttl in [(axes[0], "smr", "smr100: additions-basis floors (nuclear-smr)"),
                     (axes[1], "large", "large100: fleet-inclusive floors (nuclear)")]:
    for s in SCHEDULES:
        cs = [c for c in (SMR_CASES if fam == "smr" else LARGE_CASES)
              if parse_case(c)[1] == s and parse_case(c)[3] != "eq"]
        tr = TRAJ[cs[0]] / 1e3
        tr = tr[tr.index >= 2024]
        ax.plot(tr.index, tr.values, color=SCHED_C[s], lw=1.8)
        ax.annotate(s, (tr.index[-1], tr.values[-1]), xytext=(4, 0),
                    textcoords="offset points", color=SCHED_C[s], fontsize=8, va="center")
    ax.set_title(ttl)
    ax.set_xlabel("year")
    ax.set_xlim(2024, 2053)
axes[0].set_ylabel("mandated capacity (GW)")
fig.suptitle("Mandate trajectories: six schedules, two bases", y=1.02)
fig.tight_layout()
savefig(fig, "f01_mandate_trajectories.png")
plt.show()
""")

code("""# ---- objective sanity: p05 <= p50 <= p95 inside each schedule ----------------------
rows = []
for s in SCHEDULES:
    o = {p: OBJ[f"smr100_{s}_{p}"] for p in ("p05", "p50", "p95")}
    rows.append(dict(schedule=s, **{k: f"{v:.4e}" for k, v in o.items()},
                     ordered=bool(o["p05"] <= o["p50"] <= o["p95"])))
obj_tbl = pd.DataFrame(rows)
assert obj_tbl["ordered"].all(), obj_tbl
print(obj_tbl.to_string(index=False))
print("objective is ordered p05 <= p50 <= p95 in all six schedules.")
""")

# ================================================================================
# S2 — binding structure
# ================================================================================

md("""## S2 — Where the mandates bind, and where they do not

Adverse findings first. The floor does **not** bind everywhere:

- `smr100_eia_p05` (the cheap world on the least ambitious schedule) builds past
  the floor in one of its five mandated years. Peak overbuild is 3%.
- Every large100 case has two clearly slack years (overbuild about 1%).
- `large100_eia_p50` has a positive dual in only 6 of its 12 mandated years.
  In the other years, the existing fleet plus voluntary builds already satisfy
  the fleet-inclusive floor at a near-zero dual.
- All other smr100 cases bind in every mandated year.

A slack year means the model builds past the floor on its own. The mandate is
locally redundant there, and the dual is zero by complementary slackness (the
QA notebook verified this both ways). The EIA schedule mandates only 5 model
years, because its additions trajectory starts in 2036 and the first solve year
after that is 2038.

The heatmap shows three mandated states. **Binding** means the dual is above
$1/MW-yr. **Clearly slack** means the capacity is more than 100 MW above the
floor. **Satisfied, near-zero dual** covers the years between: the floor holds
almost exactly, but it does not price. Those years occur in the large100 cases,
where the existing fleet path meets the early floor.""")

code("""# ---- t02: slack years ---------------------------------------------------------------
slack = DUALS[DUALS["clearly_slack"]].copy()
slack["overbuild_ratio"] = (slack["cap_MW"] / slack["mandate_MW"]).round(3)
t02 = slack[["case", "t", "mandate_MW", "cap_MW", "slack_MW", "overbuild_ratio"]]
t02 = t02.sort_values(["case", "t"])
t02.to_csv(EXPORTS / "t02_slack_years.csv", index=False)
print(t02.to_string(index=False))
print(f"\\n{len(t02)} clearly slack (case, year) points across the 25 runs.")
""")

code("""# ---- f02: binding-state heatmap ------------------------------------------------------
CASE_ORDER = ([f"smr100_{s}_{p}" for s in SCHEDULES for p in ("p05", "p50", "p95")]
              + ["smr100_eia_p50_eq"] + [f"large100_{s}_p50" for s in SCHEDULES])
assert set(CASE_ORDER) == set(CASES)
myears = [t for t in YEARS_RUN if t >= 2023]
STATE = {"not mandated": 0, "satisfied, near-zero dual": 1, "clearly slack": 2, "binding": 3}
Z = np.zeros((len(CASE_ORDER), len(myears)))
du = DUALS.set_index(["case", "t"])
for i, c in enumerate(CASE_ORDER):
    for j, t in enumerate(myears):
        r = du.loc[(c, t)]
        if not r["mandated"]:
            Z[i, j] = STATE["not mandated"]
        elif r["binding"]:
            Z[i, j] = STATE["binding"]
        elif r["clearly_slack"]:
            Z[i, j] = STATE["clearly slack"]
        else:
            Z[i, j] = STATE["satisfied, near-zero dual"]
cmap = mpl.colors.ListedColormap([SURFACE, "#b8cbe4", "#eb6834", "#27506e"])
fig, ax = plt.subplots(figsize=(9, 8.5))
ax.pcolormesh(np.arange(len(myears) + 1), np.arange(len(CASE_ORDER) + 1), Z,
              cmap=cmap, vmin=-0.5, vmax=3.5, edgecolors=SURFACE, linewidth=2)
for i, c in enumerate(CASE_ORDER):        # annotate slack cells with overbuild ratio
    for j, t in enumerate(myears):
        r = du.loc[(c, t)]
        if r["mandated"] and r["clearly_slack"]:
            ax.text(j + 0.5, i + 0.5, f"{r['cap_MW'] / r['mandate_MW']:.2f}",
                    ha="center", va="center", fontsize=7, color=SURFACE)
ax.set_xticks(np.arange(len(myears)) + 0.5, myears, rotation=45)
ax.set_yticks(np.arange(len(CASE_ORDER)) + 0.5, CASE_ORDER, fontsize=7.5)
ax.invert_yaxis()
ax.grid(False)
handles = [mpl.patches.Patch(facecolor=cmap.colors[v], edgecolor=EDGE_C, label=k)
           for k, v in STATE.items()]
ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8)
ax.set_title("Mandate state by case and model year (slack cells show cap/floor)")
fig.tight_layout()
savefig(fig, "f02_binding_heatmap.png")
plt.show()
""")

code("""# ---- f03: mandate floor against delivered capacity ----------------------------------
fig, axes = plt.subplots(2, 6, figsize=(16, 6), sharex="row")
for j, s in enumerate(SCHEDULES):
    ax = axes[0, j]
    for p in ("p05", "p50", "p95"):
        c = f"smr100_{s}_{p}"
        d = DUALS[DUALS["case"] == c].set_index("t").sort_index()
        d = d[d.index >= 2029]
        ax.plot(d.index, d["cap_MW"] / 1e3, color=SCHED_C[s], **PCT_STYLE[p])
        sl = d[d["mandated"] & ~d["binding"]]
        ax.plot(sl.index, sl["cap_MW"] / 1e3, "o", mfc="none", mec=COL["smr"],
                ms=7, mew=1.4, zorder=5)
    tr = TRAJ[f"smr100_{s}_p50"] / 1e3
    tr = tr[(tr.index >= 2029) & (tr > 0)]
    ax.step(tr.index, tr.values, where="post", color=INK, lw=1.0, ls=":")
    ax.set_title(SCHED_LABEL[s], fontsize=8.5)
    if j == 0:
        ax.set_ylabel("smr100\\nnuclear-smr cap (GW)")
for j, s in enumerate(SCHEDULES):
    ax = axes[1, j]
    c = f"large100_{s}_p50"
    d = DUALS[DUALS["case"] == c].set_index("t").sort_index()
    d = d[d.index >= 2023]
    ax.plot(d.index, d["cap_MW"] / 1e3, color=SCHED_C[s], **PCT_STYLE["p50"])
    sl = d[d["mandated"] & ~d["binding"]]
    ax.plot(sl.index, sl["cap_MW"] / 1e3, "o", mfc="none", mec=COL["large"],
            ms=7, mew=1.4, zorder=5)
    tr = TRAJ[c] / 1e3
    tr = tr[(tr.index >= 2023) & (tr > 0)]
    ax.step(tr.index, tr.values, where="post", color=INK, lw=1.0, ls=":")
    ax.set_xlabel("year")
    if j == 0:
        ax.set_ylabel("large100 p50\\nnuclear cap (GW)")
fig.suptitle("Delivered capacity against the mandate floor (dotted step). "
             "Open circles: mandated years with a near-zero dual.", y=1.02)
fig.tight_layout()
savefig(fig, "f03_mandate_vs_cap.png")
plt.show()
""")

# ================================================================================
# S3 — dual trajectories
# ================================================================================

md("""## S3 — Dual price trajectories

The dual of the mandate constraint is a rental price. Its unit is dollars per
MW and year, because the floor is on cumulative national capacity in each year.
The h5 key is `nuclear_cap_price(t)`, in dollars of 2004. The figures show
dollars of 2024 per kW and year.

**Read the level as total support.** The production baseline removes the
nuclear ITC (`incentives_suffix=obbba_nonuclearitc`; QA tests B10-B13 verified
this). Thus the dual is the total support the mandated technology needs in that
year. It is not an increment on top of the 48E credit.

Known structure, re-verified below: the dual is monotone in the cost world
(p95 >= p50 >= p05 in every year, no crossing). The p05 duals decay hard toward
zero. The p95 duals stay close to flat. At p50, the large100 comparators need
about 1.2x to 1.4x the smr100 dual in shared binding years.

The equality copy `smr100_eia_p50_eq` duplicates `smr100_eia_p50` (section S9).
The fans exclude it.""")

code("""# ---- t03: dual summary per case ------------------------------------------------------
KWYR = 1e-3      # $/MW-yr -> $/kW-yr
rows = []
for c in CASES:
    d = DUALS[(DUALS["case"] == c) & DUALS["mandated"]].set_index("t").sort_index()
    b = d[d["binding"]]["dual_2024_MWyr"]
    rows.append(dict(
        case=c,
        n_binding=len(b),
        mean_binding_dual_2024_kWyr=round(float(b.mean()) * KWYR, 1) if len(b) else 0.0,
        peak_dual_2024_kWyr=round(float(b.max()) * KWYR, 1) if len(b) else 0.0,
        peak_year=int(b.idxmax()) if len(b) else None,
        dual_2050_2024_kWyr=round(float(d.loc[2050, "dual_2024_MWyr"]) * KWYR, 1)
                            if 2050 in d.index else 0.0,
    ))
t03 = pd.DataFrame(rows)
t03.to_csv(EXPORTS / "t03_dual_summary.csv", index=False)
print(t03.to_string(index=False))

# pointwise monotonicity across the cost world, re-verified from the export
for s in SCHEDULES:
    piv = (DUALS[(DUALS["family"] == "smr") & (DUALS["schedule"] == s)
                 & (DUALS["variant"] != "eq")]
           .pivot_table(index="t", columns="pct", values="dual_2004_MWyr"))
    assert ((piv["p95"] >= piv["p50"] - 1e-6) & (piv["p50"] >= piv["p05"] - 1e-6)).all(), s
print("dual is monotone p95 >= p50 >= p05 pointwise in all six schedules.")
""")

code("""# ---- f04: dual fans per schedule, large100 overlay -----------------------------------
fig, axes = plt.subplots(2, 3, figsize=(12.5, 6.5), sharex=True, sharey=True)
for k, s in enumerate(SCHEDULES):
    ax = axes.flat[k]
    piv = (DUALS[(DUALS["family"] == "smr") & (DUALS["schedule"] == s)
                 & (DUALS["variant"] != "eq") & (DUALS["t"] >= 2029)]
           .pivot_table(index="t", columns="pct", values="dual_2024_MWyr") * KWYR)
    ax.fill_between(piv.index, piv["p05"], piv["p95"], color=SCHED_C[s], alpha=0.14, lw=0)
    for p in ("p05", "p50", "p95"):
        ax.plot(piv.index, piv[p], color=SCHED_C[s], **PCT_STYLE[p])
        dd = DUALS[(DUALS["case"] == f"smr100_{s}_{p}") & (DUALS["t"] >= 2029)
                   & DUALS["mandated"]]
        bind = dd[dd["binding"]]
        ax.plot(bind["t"], bind["dual_2024_MWyr"] * KWYR, "o", ms=3.5,
                color=SCHED_C[s], alpha=PCT_STYLE[p]["alpha"])
        zz = dd[~dd["binding"]]
        ax.plot(zz["t"], zz["dual_2024_MWyr"] * KWYR, "o", ms=6, mfc="none",
                mec=COL["smr"], mew=1.2, zorder=5)
    dl = (DUALS[(DUALS["case"] == f"large100_{s}_p50") & (DUALS["t"] >= 2029)]
          .set_index("t")["dual_2024_MWyr"] * KWYR)
    ax.plot(dl.index, dl.values, color=COL["large"], lw=1.4, ls="--")
    ax.set_title(SCHED_LABEL[s], fontsize=9)
    if k % 3 == 0:
        ax.set_ylabel("mandate dual (2024$ / kW-yr)")
    if k >= 3:
        ax.set_xlabel("year")
handles = ([mpl.lines.Line2D([], [], color=INK, **{k: v for k, v in PCT_STYLE[p].items()})
            for p in ("p05", "p50", "p95")]
           + [mpl.lines.Line2D([], [], color=COL["large"], lw=1.4, ls="--"),
              mpl.lines.Line2D([], [], marker="o", mfc="none", mec=COL["smr"], ls="none")])
axes.flat[0].legend(handles, ["p05", "p50", "p95", "large100 p50", "mandated, near-zero dual"],
                    fontsize=7.5, loc="upper right")
fig.suptitle("Mandate dual trajectories: percentile fans per schedule, "
             "large100 p50 comparator dashed", y=1.02)
fig.tight_layout()
savefig(fig, "f04_dual_fans.png")
plt.show()
""")

code("""# ---- f05: all six smr100 p50 dual paths on one panel ----------------------------------
fig, ax = plt.subplots(figsize=(7.5, 4.5))
for s in SCHEDULES:
    d = (DUALS[(DUALS["case"] == f"smr100_{s}_p50") & (DUALS["t"] >= 2029)]
         .set_index("t")["dual_2024_MWyr"] * KWYR)
    ax.plot(d.index, d.values, color=SCHED_C[s], lw=2.0)
    ax.annotate(s, (d.index[-1], d.values[-1]), xytext=(5, 0),
                textcoords="offset points", color=SCHED_C[s], fontsize=8.5, va="center")
ax.set_xlabel("year")
ax.set_ylabel("mandate dual (2024$ / kW-yr)")
ax.set_xlim(2029, 2053)
ax.set_title("smr100 p50 dual paths, all six schedules")
fig.tight_layout()
savefig(fig, "f05_dual_all_p50.png")
plt.show()
""")

# ================================================================================
# S4 — cross-section
# ================================================================================

md("""## S4 — Dual price against schedule ambition

The cross-section plots the mean binding dual of each case against the 2050
ambition of its schedule (117 to 400 GW).

At p50, the mean binding dual **rises** from EIA (117 GW) to Abou-Jaoude
(134 GW), and then **falls** through the more ambitious schedules down to the
EO 2025 schedule (400 GW). More deployment pushes the fleet further down the
learning curve, so the rental price of the marginal mandated MW falls even as
the mandated quantity rises. This is the learning mechanism in cross-section.

**Caveat.** The points differ in the drawn cost world as well as in ambition.
Each schedule carries its own percentile draw of its own program. The line is
descriptive. It is not a supply curve.""")

code("""# ---- f06 + cross-section table --------------------------------------------------------
t03i = t03.set_index("case")
fig, ax = plt.subplots(figsize=(7, 4.5))
xs = [SCHED_GW[s] for s in SCHEDULES]
for p in ("p05", "p50", "p95"):
    ys = [t03i.loc[f"smr100_{s}_{p}", "mean_binding_dual_2024_kWyr"] for s in SCHEDULES]
    ax.plot(xs, ys, marker="o", ms=5, color=COL["smr"], **{k: v for k, v in
            PCT_STYLE[p].items() if k != "ls"}, ls=PCT_STYLE[p]["ls"])
    ax.annotate(p, (xs[-1], ys[-1]), xytext=(6, 0), textcoords="offset points",
                color=COL["smr"], alpha=PCT_STYLE[p]["alpha"], fontsize=8.5, va="center")
ys_l = [t03i.loc[f"large100_{s}_p50", "mean_binding_dual_2024_kWyr"] for s in SCHEDULES]
ax.plot(xs, ys_l, marker="s", ms=5, color=COL["large"], lw=1.4, ls="--")
ax.annotate("large100 p50", (xs[-1], ys_l[-1]), xytext=(6, 0),
            textcoords="offset points", color=COL["large"], fontsize=8.5, va="center")
for s in SCHEDULES:
    ax.annotate(s, (SCHED_GW[s], ax.get_ylim()[0]), xytext=(0, 4),
                textcoords="offset points", ha="center", fontsize=7.5, color=FAINT)
ax.set_xlabel("2050 schedule ambition (GW)")
ax.set_ylabel("mean binding dual (2024$ / kW-yr)")
ax.set_title("Mean binding dual against schedule ambition")
fig.tight_layout()
savefig(fig, "f06_dual_vs_ambition.png")
plt.show()

ratio = {s: round(t03i.loc[f"large100_{s}_p50", "mean_binding_dual_2024_kWyr"]
                  / t03i.loc[f"smr100_{s}_p50", "mean_binding_dual_2024_kWyr"], 2)
         for s in SCHEDULES}
print("large100 / smr100 mean binding dual ratio at p50 (note: bases differ; "
      "shared-binding-year ratio in the QA report is 1.23-1.36):", ratio)
""")

# ================================================================================
# S5 — bridge shape
# ================================================================================

md("""## S5 — Bridge shape: dual decay metrics

The working hypothesis of the paper is that the subsidy is a **bridge**: the
dual should decay toward zero as the fleet walks down the learning curve. The
shape of the dual trajectory, not its level, is the durable object.

The metrics below quantify the shape per case: the peak year, the ratio of the
2050 dual to the peak dual, the first year below half of the peak, and the
count of zero-dual mandated years.

**Adverse side, with equal prominence:** in the p95 (expensive) worlds the dual
does **not** decay by 2050. The bridge does not come down inside the model
horizon in those draws. The decay result holds in the p05 worlds and, more
weakly, at p50.""")

code("""# ---- t04: bridge metrics --------------------------------------------------------------
rows = []
for c in CASES:
    d = DUALS[(DUALS["case"] == c) & DUALS["mandated"]].set_index("t").sort_index()
    b = d[d["binding"]]["dual_2004_MWyr"]
    if not len(b):
        rows.append(dict(case=c, peak_year=None, end_over_peak=None,
                         first_year_below_half_peak=None,
                         n_zero_dual_mandated_years=int((~d["binding"]).sum())))
        continue
    peak_t, peak = int(b.idxmax()), float(b.max())
    end = float(d.loc[2050, "dual_2004_MWyr"]) if 2050 in d.index else 0.0
    below = [t for t in b.index if t > peak_t and b[t] < 0.5 * peak]
    zero_after = [t for t in d.index if t > peak_t and not d.loc[t, "binding"]]
    first_half = min(below + zero_after) if (below or zero_after) else None
    rows.append(dict(case=c, peak_year=peak_t, end_over_peak=round(end / peak, 2),
                     first_year_below_half_peak=first_half,
                     n_zero_dual_mandated_years=int((~d["binding"]).sum())))
t04 = pd.DataFrame(rows)
t04.to_csv(EXPORTS / "t04_bridge_metrics.csv", index=False)
print(t04.to_string(index=False))
""")

code("""# ---- f07: normalized decay curves -------------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(12.5, 4), sharey=True)
for k, p in enumerate(("p05", "p50", "p95")):
    ax = axes[k]
    for s in SCHEDULES:
        c = f"smr100_{s}_{p}"
        d = DUALS[(DUALS["case"] == c) & DUALS["mandated"]].set_index("t").sort_index()
        peak = d["dual_2004_MWyr"].max()
        if peak <= 1.0:
            continue
        x = d.index - d.index.min()
        ax.plot(x, d["dual_2004_MWyr"] / peak, color=SCHED_C[s], lw=1.6,
                label=s if k == 0 else None)
    if p == "p50":     # large100 comparators share the p50 panel, dashed
        for s in SCHEDULES:
            c = f"large100_{s}_p50"
            d = DUALS[(DUALS["case"] == c) & DUALS["mandated"]].set_index("t").sort_index()
            peak = d["dual_2004_MWyr"].max()
            x = d.index - d.index.min()
            ax.plot(x, d["dual_2004_MWyr"] / peak, color=SCHED_C[s], lw=1.0,
                    ls="--", alpha=0.55)
    ax.set_title(p + (" (dashed: large100)" if p == "p50" else ""))
    ax.set_xlabel("years since first mandated model year")
axes[0].set_ylabel("dual / peak dual")
axes[0].legend(fontsize=8, ncols=2)
fig.suptitle("Dual decay, normalized to each case peak", y=1.03)
fig.tight_layout()
savefig(fig, "f07_dual_shape_normalized.png")
plt.show()
""")

# ================================================================================
# S6 — system costs
# ================================================================================

md("""## S6 — System costs

**There is no no-mandate baseline run.** All 25 runs carry a mandate. Thus the
system cost *of the mandate* is not computable here as a difference against a
counterfactual. Four objects are computable and shown:

1. Cost levels per case (descriptive; the conflation caveat applies across
   schedules).
2. The p95 - p05 spread inside one schedule. The mandate is identical inside a
   schedule, so this spread isolates the drawn cost world.
3. The smr100 - large100 difference at p50 per schedule. These runs differ in
   the mandated technology, the mandate basis, and the drawn world. Read them
   as conditional what-ifs.
4. The fiscal bill of the mandate from the duals (section S8). That is the
   marginal-price measure of what the mandate costs to enforce.

The 25 `systemcost` streams group into seven buckets. Policy credit streams
(ITC / PTC / CO2 / H2-PTC payments) are negative. The total keeps their sign.
The per-year LP objective `z_rep` is not an annual cost stream: in the
sequential solve it mixes lump investment with operations weighted by
`pvf_onm` (about 14.76). This notebook uses `systemcost` only.""")

code("""# ---- bucket the 25 streams --------------------------------------------------------------
BUCKETS = {
    "generation capex": ["inv_investment_capacity_costs",
                         "inv_investment_refurbishment_capacity",
                         "inv_investment_spurline_costs_rsc_technologies"],
    "transmission capex": ["inv_transmission_interzone_ac_investment",
                           "inv_transmission_interzone_dc_investment",
                           "inv_transmission_intrazone_investment"],
    "converter + H2 capex": ["inv_converter_costs", "inv_h2_production", "inv_h2_storage"],
    "fuel": ["op_fuelcosts_objfn"],
    "FOM": ["op_fom_costs", "op_consume_fom", "op_spurline_fom",
            "op_transmission_fom", "op_transmission_intrazone_fom"],
    "VOM + other op": ["op_vom_costs", "op_startcost", "op_acp_compliance_costs",
                       "op_co2_transport_storage", "op_h2_storage",
                       "op_h2_transport_intrareg"],
    "policy credits (neg.)": ["inv_itc_payments_negative", "op_co2_incentive_negative",
                              "op_h2_ptc_payments_negative", "op_ptc_payments_negative"],
}
covered = sorted(x for v in BUCKETS.values() for x in v)
assert covered == STREAMS, set(STREAMS) ^ set(covered)
S2B = {x: b for b, v in BUCKETS.items() for x in v}

SYSCOST["bucket"] = SYSCOST["sys_costs"].map(S2B)
SYSCOST["B2024"] = SYSCOST["Value"] * TO2024 / 1e9
CB = (SYSCOST.groupby(["case", "bucket", "t"], as_index=False)["B2024"].sum())
CTOT = SYSCOST.groupby(["case", "t"])["B2024"].sum().unstack("t")     # 2024$B per year
CB.to_csv(EXPORTS / "t05_systemcost_by_case.csv", index=False)

# consistency: raw_inv/raw_op against the stream sums (context, not a gate)
inv_streams = [x for x in STREAMS if x.startswith("inv_") and not x.endswith("negative")]
c = REF
si = SYSCOST[(SYSCOST["case"] == c) & SYSCOST["sys_costs"].isin(inv_streams)]
si = si.groupby("t")["Value"].sum()
ri = RAWIO[c][0].reindex(si.index)
print(f"{c}: raw_inv_cost vs positive inv streams, max rel diff "
      f"{float(((si - ri).abs() / ri.clip(lower=1)).max()):.2e}")
itc_mag = {k: abs(v) * TO2024 / 1e9 for k, v in ITC_TOT.items()}
print(f"ITC tax expenditure magnitude (2024$B, recorded negative in the h5): "
      f"{min(itc_mag.values()):.1f} .. {max(itc_mag.values()):.1f} "
      "- other techs keep their ITC; nuclear has none (QA B10-B13).")
""")

code("""# ---- f08: cost anatomy of the reference case ----------------------------------------------
ref = CB[(CB["case"] == REF) & (CB["t"] >= 2023)].pivot_table(
    index="t", columns="bucket", values="B2024")
order = [b for b in BUCKETS if b in ref.columns]
bcol = {b: c for b, c in zip(BUCKETS, mpl.cm.viridis(np.linspace(0.05, 0.9, len(BUCKETS))))}
fig, ax = plt.subplots(figsize=(9, 4.8))
bottom_pos = np.zeros(len(ref))
bottom_neg = np.zeros(len(ref))
for b in order:
    v = ref[b].fillna(0).to_numpy()
    base = np.where(v >= 0, bottom_pos, bottom_neg)
    ax.bar(ref.index, v, bottom=base, width=0.8, label=b, color=bcol[b],
           edgecolor=SURFACE, linewidth=0.6)
    bottom_pos += np.clip(v, 0, None)
    bottom_neg += np.clip(v, None, 0)
tot = ref.sum(axis=1)
ax.plot(ref.index, tot, color=INK, lw=1.6, marker="o", ms=3, label="total (net)")
ax.axhline(0, color=EDGE_C, lw=1)
ax.set_xlabel("model year")
ax.set_ylabel("annual system cost (2024 $B / yr)")
ax.set_title(f"System cost anatomy: {REF}")
ax.legend(fontsize=7.5, ncols=2)
fig.tight_layout()
savefig(fig, "f08_cost_decomposition_ref.png")
plt.show()
""")

code("""# ---- f09: total annual system cost fans -----------------------------------------------------
fig, axes = plt.subplots(2, 3, figsize=(12.5, 6.5), sharex=True, sharey=True)
for k, s in enumerate(SCHEDULES):
    ax = axes.flat[k]
    piv = {p: CTOT.loc[f"smr100_{s}_{p}"] for p in ("p05", "p50", "p95")}
    yrs = [t for t in YEARS_RUN if t >= 2023]
    ax.fill_between(yrs, piv["p05"][yrs], piv["p95"][yrs], color=SCHED_C[s],
                    alpha=0.14, lw=0)
    for p in ("p05", "p50", "p95"):
        ax.plot(yrs, piv[p][yrs], color=SCHED_C[s], **PCT_STYLE[p])
    lg = CTOT.loc[f"large100_{s}_p50"]
    ax.plot(yrs, lg[yrs], color=COL["large"], lw=1.4, ls="--")
    ax.set_title(SCHED_LABEL[s], fontsize=9)
    if k % 3 == 0:
        ax.set_ylabel("total system cost\\n(2024 $B / yr)")
    if k >= 3:
        ax.set_xlabel("year")
axes.flat[0].legend([mpl.lines.Line2D([], [], color=INK, **PCT_STYLE[p])
                     for p in ("p05", "p50", "p95")]
                    + [mpl.lines.Line2D([], [], color=COL["large"], lw=1.4, ls="--")],
                    ["p05", "p50", "p95", "large100 p50"], fontsize=7.5)
fig.suptitle("Total annual system cost: percentile fans per schedule "
             "(cross-schedule levels mix mandate and drawn world)", y=1.02)
fig.tight_layout()
savefig(fig, "f09_cost_totals.png")
plt.show()
""")

code("""# ---- f10 + t06: the two clean cost comparisons ----------------------------------------------
yrs = [t for t in YEARS_RUN if t >= 2026]
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharex=True)
rows = []
for s in SCHEDULES:
    spread = CTOT.loc[f"smr100_{s}_p95"] - CTOT.loc[f"smr100_{s}_p05"]
    delta = CTOT.loc[f"smr100_{s}_p50"] - CTOT.loc[f"large100_{s}_p50"]
    axes[0].plot(yrs, spread[yrs], color=SCHED_C[s], lw=1.7, label=s)
    axes[1].plot(yrs, delta[yrs], color=SCHED_C[s], lw=1.7)
    for t in yrs:
        rows.append(dict(schedule=s, t=t,
                         p95_minus_p05_B2024=round(float(spread[t]), 2),
                         smr_minus_large_p50_B2024=round(float(delta[t]), 2)))
axes[0].set_title("p95 - p05 annual cost spread\\n(same mandate, drawn world isolated)")
axes[0].set_ylabel("2024 $B / yr")
axes[0].legend(fontsize=8, ncols=2)
axes[1].set_title("smr100 - large100 annual cost at p50\\n(conditional what-if)")
axes[1].axhline(0, color=EDGE_C, lw=1)
for ax in axes:
    ax.set_xlabel("year")
fig.tight_layout()
savefig(fig, "f10_within_schedule_spread.png")
plt.show()
t06 = pd.DataFrame(rows)
t06.to_csv(EXPORTS / "t06_cost_deltas.csv", index=False)
print(t06[t06["t"] == 2050].to_string(index=False))
""")

# ================================================================================
# S7 — NPV
# ================================================================================

md("""## S7 — System NPV

**Convention (chosen 2026-08-12).** The NPV is the sum of the total annual
`systemcost` over the calendar years 2026-2050, discounted at the ReEDS system
real rate:

NPV = sum over y in [2026, 2050] of C(m(y)) / DR^(y - 2026)

where C(t) is the total annual system cost in the solve year t, m(y) maps the
calendar year y to the solve year that represents it (solve year t covers the
years from t to the next solve year minus one), and DR is the mean ReEDS system
real discount rate. Results show in billion dollars of 2024.

**Why not the objective.** In the sequential solve, `z_rep` and `objfn_raw`
mix lump investment with operations weighted over a 20-year window per solve.
A sum of them double-counts operations. The annual `systemcost` streams with
explicit discounting are transparent, and they match the discounting of the
dual PV in section S8.

**End-effect caveat.** Investment enters as a lump in the build year, and the
window stops at 2050. Late mandated builds carry full capex but show none of
their post-2050 service value. This penalizes the ambitious schedules. Keep
this in mind before any cross-schedule reading; the conflation caveat applies
on top.""")

code("""# ---- t07 + f11: system NPV -------------------------------------------------------------------
POST = [t for t in YEARS_RUN if t >= 2026]

def year_rep(y):
    return max(t for t in POST if t <= y)

def npv_of(series_by_t):
    return sum(float(series_by_t[year_rep(y)]) / DR ** (y - 2026)
               for y in range(2026, 2051))

NPV = {c: npv_of(CTOT.loc[c]) for c in CASES}      # 2024 $B
rows = []
for s in SCHEDULES:
    rows.append(dict(
        schedule=s, ambition_2050_GW=SCHED_GW[s],
        smr_p05=round(NPV[f"smr100_{s}_p05"], 1),
        smr_p50=round(NPV[f"smr100_{s}_p50"], 1),
        smr_p95=round(NPV[f"smr100_{s}_p95"], 1),
        large_p50=round(NPV[f"large100_{s}_p50"], 1),
        p95_minus_p05=round(NPV[f"smr100_{s}_p95"] - NPV[f"smr100_{s}_p05"], 1),
        smr_minus_large_p50=round(NPV[f"smr100_{s}_p50"] - NPV[f"large100_{s}_p50"], 1),
    ))
t07 = pd.DataFrame(rows)
t07.to_csv(EXPORTS / "t07_system_npv.csv", index=False)
print("system NPV, 2026-2050, mean real rate, 2024 $B:")
print(t07.to_string(index=False))

fig, ax = plt.subplots(figsize=(7, 4.5))
xs = [SCHED_GW[s] for s in SCHEDULES]
for p in ("p05", "p50", "p95"):
    ys = [NPV[f"smr100_{s}_{p}"] for s in SCHEDULES]
    ax.plot(xs, ys, marker="o", ms=5, color=COL["smr"], **PCT_STYLE[p])
    ax.annotate(p, (xs[-1], ys[-1]), xytext=(6, 0), textcoords="offset points",
                color=COL["smr"], alpha=PCT_STYLE[p]["alpha"], fontsize=8.5, va="center")
ys_l = [NPV[f"large100_{s}_p50"] for s in SCHEDULES]
ax.plot(xs, ys_l, marker="s", ms=5, color=COL["large"], lw=1.4, ls="--")
ax.annotate("large100 p50", (xs[-1], ys_l[-1]), xytext=(6, 0),
            textcoords="offset points", color=COL["large"], fontsize=8.5, va="center")
ax.set_xlabel("2050 schedule ambition (GW)")
ax.set_ylabel("system NPV 2026-2050 (2024 $B)")
ax.set_title("System NPV against schedule ambition\\n"
             "(levels mix mandate and drawn world; end effects penalize late builds)")
fig.tight_layout()
savefig(fig, "f11_npv_vs_ambition.png")
plt.show()
""")

# ================================================================================
# S8 — fiscal bill + DRAFT issue-5
# ================================================================================

md("""## S8 — Rental transfer, ITC translation, and fiscal outputs

This section follows the procedure in `ITC calculation procedure.md` (this
folder). The solve is sequential. Each year's LP prices its own builds fully.
Because of this, the ITC translation does not discount across years.

The section makes two different fiscal quantities. Their names stay separate:

- **Rental transfer** R_t = dual(t) x mandated capacity(t). This is the
  implicit transfer of the mandate itself. It pays all mandated capacity,
  across all vintages. Its PV discounts each solve year over its forward gap
  (years to the next solve year; the terminal 2050 gap is 1).
- **ITC outlay** B_t = statutory rate x capex base of all builds in year t.
  This is the cost of the ITC instrument that replaces the mandate. It appears
  after the rate calculation below.

The rental transfer pays inframarginal capacity as well as the marginal unit.
That is a property of uniform instruments, not a bug. The transfer calculation
below quantifies it for the ITC instrument.""")

code("""# ---- t08 + f12: rental transfer R_t ------------------------------------------------------------
GAP = {t: (YEARS_RUN[i + 1] - t if i + 1 < len(YEARS_RUN) else 1)
       for i, t in enumerate(YEARS_RUN)}

BILL = {}      # per case: R_t Series over solve years, 2024 $B / yr
rows = []
for c in CASES:
    d = DUALS[(DUALS["case"] == c) & (DUALS["t"] >= 2026)].set_index("t").sort_index()
    bill = d["dual_2004_MWyr"] * d["mandate_MW"] * TO2024 / 1e9
    BILL[c] = bill
    pv = sum(float(bill[t]) * GAP[t] / DR ** (t - 2026) for t in bill.index)
    rows.append(dict(case=c, PV_rental_transfer_2024B=round(pv, 1),
                     peak_Rt_2024B=round(float(bill.max()), 1),
                     peak_Rt_year=int(bill.idxmax()) if bill.max() > 0 else None))
t08 = pd.DataFrame(rows)
t08.to_csv(EXPORTS / "t08_rental_transfer.csv", index=False)
print(t08.to_string(index=False))

fig = plt.figure(figsize=(12.5, 8.5))
gs = fig.add_gridspec(3, 3, height_ratios=[1, 1, 1.15], hspace=0.45)
for k, s in enumerate(SCHEDULES):
    ax = fig.add_subplot(gs[k // 3, k % 3])
    yrs = [t for t in YEARS_RUN if t >= 2029]
    lo, hi = BILL[f"smr100_{s}_p05"], BILL[f"smr100_{s}_p95"]
    ax.fill_between(yrs, lo.reindex(yrs), hi.reindex(yrs), color=SCHED_C[s],
                    alpha=0.14, lw=0)
    for p in ("p05", "p50", "p95"):
        b = BILL[f"smr100_{s}_{p}"]
        ax.plot(yrs, b.reindex(yrs), color=SCHED_C[s], **PCT_STYLE[p])
    bl = BILL[f"large100_{s}_p50"]
    ax.plot(yrs, bl.reindex(yrs), color=COL["large"], lw=1.3, ls="--")
    ax.set_title(SCHED_LABEL[s], fontsize=8.5)
    if k % 3 == 0:
        ax.set_ylabel("R_t (2024 $B/yr)")
axb = fig.add_subplot(gs[2, :])
order = ([f"smr100_{s}_{p}" for s in SCHEDULES for p in ("p05", "p50", "p95")]
         + [f"large100_{s}_p50" for s in SCHEDULES])
pvv = t08.set_index("case")["PV_rental_transfer_2024B"].reindex(order)
cols = [SCHED_C[parse_case(c)[1]] if parse_case(c)[0] == "smr" else COL["large"]
        for c in order]
axb.bar(range(len(order)), pvv.values, color=cols, edgecolor=SURFACE)
axb.set_xticks(range(len(order)), order, rotation=90, fontsize=7)
axb.set_ylabel("PV of R_t (2024 $B)")
axb.set_title("PV of the rental transfer, 2026-2050")
fig.suptitle("Rental transfer of the mandate: R_t = dual x mandated capacity", y=0.995)
savefig(fig, "f12_rental_transfer.png")
plt.show()
""")

md("""### ITC translation for a sequential run

The translation follows `ITC calculation procedure.md`. The paper plan locks
the formula before results interpretation. Until then, treat the rates as
provisional.

The logic: each yearly LP is the full decision problem for its builds. The raw
dual of the floor constraint is the capitalized gap of the marginal build in
that solve. Thus the subsidy for a build in year t is:

S_t = raw dual(t) / cost_scale = converted dual(t) x pvf_onm(t)

S_t is in 2004 dollars per MW. It contains capital cost, fixed O&M, and
variable costs, minus the market value of the build. No discounting across
years applies, because the year-t solve prices the build fully.

A year enters the ITC schedule only if three conditions hold: the dual is
positive, the mandate increases in that year, and the model builds new
mandated capacity in that year (`cap_new_ann` > 0). Slack years get a zero
required ITC and stay in the table as results.

The rate calculation inverts the ReEDS financing arithmetic
(`reeds/financials.py`, lines 683-694). fin_mult is a linear function of the
monetized fraction m. The per-region solution is:

m_t(r) = S_t / (cost_cap(t) x fin_mult_noITC(r, t)) x k(t)

with k(t) = (1 - tax x PV_dep) / (1 - tax x PV_dep / 2). k is below 1: one
dollar of credit gives more than one dollar of support, because of the tax
grossup, less the half-basis depreciation reduction. The statutory rate is
i_t(r) = m_t(r) / (1 - itc_tax_equity_penalty). The penalty comes from the
OBBBA incentives input (0.1 for nuclear).

The run does not identify the marginal region (result P7). The table reports
the rate range over the regions that build. The headline rate is the maximum
of the range. The maximum is enough for the last mandated MW. If the statutory
rate is above 100%, an ITC alone cannot supply S_t; an operating subsidy must
supply the remainder. The table flags those years.

The 48E band in the figure is 30% (base) to 50% (base plus bonuses).""")

code("""# ---- financing replication: natbase, PV_dep, k (procedure steps 5-6) ---------------------------
# Ported from z-ethan/pilots/_build_notebook.py (P4, QA-verified machinery).
DEP = pd.read_csv(FIN_DIR / "depreciation_schedules_default.csv")
CS = pd.read_csv(FIN_DIR / "construction_schedules_mc.csv")
# row-aligned ReEDS exponents: header 'NA' row -> 0, rows t=0..9 -> 0.5..9.5
CC_EXPS = np.append([0.0], np.arange(0.5, 10.5, 1.0))
assert len(CS) == len(CC_EXPS), (len(CS), len(CC_EXPS))

def ccmult_reeds(sched_name, ib):
    x = pd.to_numeric(CS[str(sched_name)], errors="coerce").fillna(0.0).to_numpy()
    return 1.0 + float(np.sum(x * (ib ** CC_EXPS - 1.0)))

IN_NAME = {"nuclear": "Nuclear", "nuclear-smr": "Nuclear-SMR"}

def fin_tech(case):
    fin = sw(case, "financials_tech_suffix")
    ft = pd.read_csv(FIN_DIR / f"financials_tech_{fin}.csv")
    ft.columns = [c.lstrip("*") for c in ft.columns]
    return ft[ft["i"].isin(["Nuclear", "Nuclear-SMR"])]

_NF_CACHE = {}

def natfin(case):
    \"\"\"(natbase, k) Series pairs on YEARS for the case's mandated technology.
    natbase = ccmult / (1 - tax) x (1 - tax x PV_dep) x risk x eval_adj — the
    r-independent part of cost_cap_fin_mult_noITC (Degradation_Adj = 1 for nuclear).
    k = (1 - tax x PV_dep) / (1 - tax x PV_dep / 2) converts the financed-cost
    ratio S / (cost_cap x fin_mult_noITC) to the monetized fraction m.\"\"\"
    key = (case, META[case]["mandated_tech"])
    if key in _NF_CACHE:
        return _NF_CACHE[key]
    grp = fin_tech(case)
    grp = grp[grp["i"] == IN_NAME[META[case]["mandated_tech"]]]
    grp = grp.set_index("t").reindex(YEARS).ffill().bfill()
    dep_col = str(int(grp["depreciation_sch"].iloc[0]))
    dep_frac = pd.to_numeric(DEP[dep_col], errors="coerce").fillna(0.0).to_numpy(float)
    pv_dep = np.array([np.sum(dep_frac / dn ** np.arange(1, len(dep_frac) + 1))
                       for dn in D_NOM])
    eval_p = float(grp["eval_period"].iloc[0])
    risk = 1.0 + grp["finance_diff_real"].to_numpy(float) * (
        (1 - (1 / D_REAL) ** eval_p) / (D_REAL - 1.0))
    sys_pvf = (1 - (1 / D_REAL) ** (30 - 1)) / (D_REAL - 1.0) + 1
    tech_pvf = (1 - (1 / D_REAL) ** (eval_p - 1)) / (D_REAL - 1.0) + 1
    eval_adj = sys_pvf / tech_pvf
    ccm = np.array([ccmult_reeds(grp.loc[t, "construction_sch"], IB[yi(t)])
                    for t in YEARS])
    natbase = pd.Series(ccm / (1 - TAX) * (1 - TAX * pv_dep) * risk * eval_adj,
                        index=YEARS)
    k = pd.Series((1 - TAX * pv_dep) / (1 - TAX * pv_dep / 2), index=YEARS)
    _NF_CACHE[key] = (natbase, k)
    return natbase, k

# self-check: natbase x a time-constant regional factor reproduces the h5 multiplier.
# The time dimension makes this non-circular: it tests the time shape of natbase.
for c in ["smr100_eia_p50", "smr100_eo_p95", "large100_eo_p50"]:
    nb, _ = natfin(c)
    piv = FINMULT[c].unstack("t")
    yrs = [t for t in piv.columns if t >= 2026]
    ratio = piv[yrs].div(nb.reindex(yrs), axis=1)
    regfac = ratio.mean(axis=1)
    resid = (piv[yrs] - pd.DataFrame(np.outer(regfac, nb.reindex(yrs)),
                                     index=piv.index, columns=yrs)).abs() / piv[yrs]
    worst = float(resid.max().max())
    assert worst < 5e-3, (c, worst)
    assert 0.85 < float(regfac.min()) and float(regfac.max()) < 1.35, c
    print(f"{c}: natbase reproduces the h5 multiplier; worst rel resid {worst:.1e}; "
          f"regional factors {float(regfac.min()):.3f}..{float(regfac.max()):.3f}")
""")

code("""# ---- procedure step 1: baseline checks ----------------------------------------------------------
inc_no = pd.read_csv(FIN_DIR / "incentives_obbba_nonuclearitc.csv")
nuc_no = inc_no[inc_no["i"].str.upper().str.startswith("NUCLEAR")]
itc_cols = [c for c in inc_no.columns if c.startswith("itc_")]
assert float(nuc_no[itc_cols].abs().to_numpy().sum()) == 0.0, "input file has nuclear ITC"
worst_fm = max(FMDIFF.values())
assert worst_fm < 1e-9, f"fin_mult != fin_mult_noITC somewhere: {worst_fm}"
print("baseline holds: zero nuclear ITC in the incentives input; "
      "fin_mult == fin_mult_noITC for the mandated technology in all 25 runs.")
print("Thus the dual is the total required support, not an increment.")

# statutory conversion uses the OBBBA penalty for a hypothetical nuclear credit
inc_ob = pd.read_csv(FIN_DIR / "incentives_obbba.csv")
nuc_ob = inc_ob[inc_ob["i"].str.upper().str.startswith("NUCLEAR")]
PEN = float(nuc_ob["itc_tax_equity_penalty"].iloc[0])
assert (nuc_ob["itc_tax_equity_penalty"] == PEN).all()
print(f"itc_tax_equity_penalty = {PEN}; statutory i = m / (1 - {PEN})")
""")

code("""# ---- t09: required ITC rates per the procedure ---------------------------------------------------
TPREV = {t: (YEARS_RUN[i - 1] if i > 0 else None) for i, t in enumerate(YEARS_RUN)}
rate_rows = []
for c in CASES:
    tech = META[c]["mandated_tech"]
    nb, K = natfin(c)
    d = DUALS[DUALS["case"] == c].set_index("t").sort_index()
    cc, fm, bl, tr = COSTCAP[c], FINMULT[c], CAPNEW[c], TRAJ[c]
    for t in YEARS_RUN:
        if not bool(d.loc[t, "mandated"]):
            continue
        dual_pos = bool(d.loc[t, "binding"])
        m_inc = float(tr.get(t, 0.0)) - float(tr.get(TPREV[t], 0.0) if TPREV[t] else 0.0)
        blt = bl.xs(t, level="t") if t in bl.index.get_level_values("t") else pd.Series(dtype=float)
        blt = blt[blt > 0]
        if not dual_pos:
            status = "slack: required ITC is zero"
        elif m_inc <= 0:
            status = "no mandate increase: no build receives a credit"
        elif not len(blt):
            status = "no new builds: dual prices retention, not a build"
        else:
            status = "rate"
        row = dict(case=c, t=t, status=status, S_t_2004_per_MW=None, n_build_regions=0,
                   i_min=None, i_max=None, i_headline=None, itc_insufficient=False)
        if status == "rate":
            S = float(d.loc[t, "dual_raw"])                       # cost_scale = 1
            S_alt = float(d.loc[t, "dual_2004_MWyr"]) * float(PVF[c].loc[t])
            assert abs(S - S_alt) <= 1e-4 * max(1.0, abs(S)), (c, t, S, S_alt)
            fmb = fm.xs(t, level="t").reindex(blt.index).dropna()
            m_r = S / (float(cc.loc[t]) * fmb) * float(K.loc[t])  # monetized, per region
            i_r = m_r / (1.0 - PEN)                               # statutory, per region
            row.update(S_t_2004_per_MW=round(S), n_build_regions=len(i_r),
                       i_min=round(float(i_r.min()), 3), i_max=round(float(i_r.max()), 3),
                       i_headline=round(float(i_r.max()), 3),
                       itc_insufficient=bool(i_r.max() > 1.0))
        rate_rows.append(row)
t09 = pd.DataFrame(rate_rows)
t09.to_csv(EXPORTS / "t09_required_itc.csv", index=False)
n_over = int(t09["itc_insufficient"].sum())
print(f"gated (case, year) points: {len(t09)}; rate rows: "
      f"{int((t09['status'] == 'rate').sum())}; statutory rate above 100%: {n_over}")
print("\\nstatutory headline rate, smr100 p50 (provisional until the formula locks):")
p50 = t09[(t09["case"].isin([f"smr100_{s}_p50" for s in SCHEDULES]))
          & (t09["status"] == "rate")]
print(p50.pivot_table(index="t", columns="case", values="i_headline").round(2).to_string())
print("\\nexcluded mandated years by reason:")
print(t09[t09["status"] != "rate"].groupby("status").size().to_string())
""")

code("""# ---- f13: required statutory ITC rate against solve year ------------------------------------------
fig, ax = plt.subplots(figsize=(8.5, 5))
ax.axhspan(0.30, 0.50, color=GRID_C, alpha=0.5, lw=0, zorder=0)
ax.text(0.99, 0.42, "48E range 30-50%", fontsize=8, color=MUTED,
        ha="right", transform=ax.get_yaxis_transform())
ax.axhline(1.0, color=COL["smr"], lw=1.0, ls=":")
ax.text(0.01, 1.01, "ITC alone insufficient above 100%", fontsize=7.5, color=COL["smr"],
        ha="left", va="bottom", transform=ax.get_yaxis_transform())
t09i = t09[t09["status"] == "rate"].set_index(["case", "t"])["i_headline"]
mult = {}
for s in SCHEDULES:
    r50 = t09i.loc[f"smr100_{s}_p50"]
    ax.plot(r50.index, r50.values, color=SCHED_C[s], lw=2.0, marker="o", ms=3.5, label=s)
    for b in r50.index:      # p05-p95 whiskers per solve year
        lo = t09i.get((f"smr100_{s}_p05", b), np.nan)
        hi = t09i.get((f"smr100_{s}_p95", b), np.nan)
        if np.isfinite(lo) and np.isfinite(hi):
            ax.plot([b, b], [lo, hi], color=SCHED_C[s], lw=0.9, alpha=0.45)
    mult[s] = round(float(r50.mean()) / 0.30, 1)
ax.legend(fontsize=8, ncols=2, loc="upper right", title="schedule", title_fontsize=8)
ax.xaxis.set_major_locator(mpl.ticker.MaxNLocator(integer=True))
ax.set_xlabel("solve year (rate applies to the builds of that year group)")
ax.set_ylabel("required statutory ITC rate")
ax.set_title("Required statutory ITC rate per solve year, smr100\\n"
             "(lines p50, whiskers p05-p95; provisional until the formula locks)")
fig.tight_layout()
savefig(fig, "f13_required_itc.png")
plt.show()
print("mean p50 rate as a multiple of the 30% base 48E credit:", mult)
p95m = {s: round(float(t09i.loc[f'smr100_{s}_p95'].mean()) / 0.30, 1) for s in SCHEDULES}
print("same multiple in the p95 (expensive) worlds, equal prominence:", p95m)
""")

md("""### ITC outlay and within-year transfer

The year-assignment rule (procedure step 7), written one time: solve year t
represents the calendar years after the previous solve year, through t. ReEDS
itself annualizes new builds this way (`cap_new_ann` divides the block by the
gap). The rate i_t applies to all builds in that group. R_t keeps the forward
convention, because capacity in year t persists to the next solve year.

The outlay is B_t = i_t x (sum of the capex bases of all builds in year t).
The capex base per MW in region r is cost_cap(t) x regional factor(r), with
the regional factor from the h5 multiplier divided by natbase.

The within-year transfer compares each building region's payment with its own
required support. The required support per MW in region r is
S_t - (max financed capex - financed capex(r)). This uses regional cost data
only. It does not include regional differences in market value. Result P7
shows that those value differences are small in the regions that build.""")

code("""# ---- t10: ITC outlay B_t and within-year transfer share ------------------------------------------
out_rows = []
for c in CASES:
    nb, K = natfin(c)
    cc, fm, bl = COSTCAP[c], FINMULT[c], CAPNEW[c]
    sub = t09[(t09["case"] == c) & (t09["status"] == "rate")].set_index("t")
    for t in sub.index:
        S = float(sub.loc[t, "S_t_2004_per_MW"])
        i_head = float(sub.loc[t, "i_headline"])
        m_head = i_head * (1.0 - PEN)
        blt = bl.xs(t, level="t")
        blt = blt[blt > 0]
        fmb = fm.xs(t, level="t").reindex(blt.index)
        base = float(cc.loc[t]) * fmb / float(nb.loc[t])          # OCC x regfac, 2004$/MW
        B_ann = i_head * float((base * blt).sum())                # 2004$/yr (builds MW/yr)
        FC = float(cc.loc[t]) * fmb                               # financed capex, 2004$/MW
        pay = m_head * FC / float(K.loc[t])                       # support delivered per MW
        req = (S - (float(FC.max()) - FC)).clip(lower=0.0)        # equal-value assumption
        wsum = float((pay * blt).sum())
        share = float(((pay - req) * blt).sum()) / wsum if wsum > 0 else np.nan
        bgap = t - TPREV[t]
        pv_w = sum(1.0 / DR ** (y - 2026) for y in range(t - bgap + 1, t + 1))
        out_rows.append(dict(case=c, t=t, i_headline=i_head,
                             B_t_2024B_per_yr=round(B_ann * TO2024 / 1e9, 2),
                             transfer_share=round(share, 3),
                             PV_weight_years=bgap, _pv_2004=B_ann * pv_w))
t10 = pd.DataFrame(out_rows)
pv_case = (t10.groupby("case")["_pv_2004"].sum() * TO2024 / 1e9).round(1)
t10 = t10.drop(columns="_pv_2004")
t10.to_csv(EXPORTS / "t10_itc_outlay_transfer.csv", index=False)
cmp_tbl = pd.DataFrame({"PV_ITC_outlay_2024B": pv_case,
                        "PV_rental_transfer_2024B":
                            t08.set_index("case")["PV_rental_transfer_2024B"]})
cmp_tbl["outlay_over_rental"] = (cmp_tbl["PV_ITC_outlay_2024B"]
                                 / cmp_tbl["PV_rental_transfer_2024B"]).round(2)
cmp_tbl.to_csv(EXPORTS / "t12_fiscal_comparison.csv")
print("PV of the two fiscal quantities, 2026-2050, 2024 $B (B_t is provisional):")
print(cmp_tbl.to_string())
print("\\nwithin-year transfer share (cost-side approximation), range per case:")
print(t10.groupby("case")["transfer_share"].agg(["min", "max"]).round(3).to_string())
""")

md("""### Companion value: the foresight requirement, and the myopia wedge

For each build year b, the companion value C_b is the discounted sum of the
converted duals over the build's full 30-year evaluation window:

C_b = sum over k = 0 .. 29 of dual(b + k) / DR^k

The calendar years inside the window map to their solve years with the same
rule as the NPV section. C_b is the support that an investor with full
foresight of the realized dual path requires. It does not control the
sequential model. The difference between S_t and C_b is an effect of the
myopic solve, and it is a result for the paper.

The model stops at 2050, but the window of a late build extends past 2050.
A cut at 2050 makes C_b fall toward zero as b comes near 2050. That fall is
an effect of the horizon, not of the costs. To remove it, the calculation
extends the dual path past 2050 in two ways, and the two results bracket the
post-2050 assumption:

- **cut**: the dual is zero after 2050. This is the lower boundary.
- **hold**: the dual after 2050 keeps its 2050 value through the window. This
  follows the same convention as the bokehpivot report, which continues
  operational values past the horizon for `sys_eval_years - 1` years.

The window discounting follows the ReEDS annuity convention: an ordinary
30-year annuity at the post-2026 system real rate, the same arithmetic that
gives pvf_onm = 1/crf. With this convention the hold variant closes an exact
identity: at b = 2050 the window holds 30 years of dual(2050), which is the
construction of S_t itself. The code checks hold / S_t = 1 at 2050.""")

code("""# ---- t11 + f14: myopia wedge with post-2050 extension band ----------------------------------------
EVAL_W = 30      # years; eval_period of both techs (financials_tech input)
# window discount rate = post-2026 system real rate; ordinary-annuity indexing
# (year b+j discounted by DRW^(j+1)) matches the ReEDS pvf_onm = 1/crf arithmetic.
DRW = float(np.mean(D_REAL[YEARS >= 2026]))
ann30 = sum(DRW ** -k for k in range(1, EVAL_W + 1))
pvf_run = float(PVF[REF].loc[2050])
assert abs(ann30 - pvf_run) / pvf_run < 0.01, (ann30, pvf_run)
print(f"window annuity at DRW={DRW - 1:.4%}: {ann30:.4f}; run pvf_onm(2050): {pvf_run:.4f}")

wed_rows = []
for c in CASES:
    d = DUALS[DUALS["case"] == c].set_index("t")["dual_2004_MWyr"].sort_index()
    d2050 = float(d.get(2050, 0.0))
    sub = t09[(t09["case"] == c) & (t09["status"] == "rate")].set_index("t")
    for b in sub.index:
        S = float(sub.loc[b, "S_t_2004_per_MW"])
        c_cut, c_hold = 0.0, 0.0
        for j in range(EVAL_W):
            y = b + j
            w = DRW ** -(j + 1)
            if y <= 2050:
                v = float(d.get(year_rep(y), 0.0))
                c_cut += v * w
                c_hold += v * w
            else:
                c_hold += d2050 * w
        wed_rows.append(dict(case=c, t=b, S_t_2004_per_MW=round(S),
                             C_cut_2004_per_MW=round(c_cut),
                             C_hold_2004_per_MW=round(c_hold),
                             cut_over_S=round(c_cut / S, 2),
                             hold_over_S=round(c_hold / S, 2),
                             tail_share_of_hold=round(1 - c_cut / c_hold, 2)
                                                if c_hold > 0 else 0.0))
t11 = pd.DataFrame(wed_rows)
t11.to_csv(EXPORTS / "t11_myopia_wedge.csv", index=False)

KW24 = TO2024 / 1e3      # 2004$/MW -> 2024$/kW
fig, axes = plt.subplots(2, 3, figsize=(12.5, 6.5), sharex=True, sharey=True)
for k, s in enumerate(SCHEDULES):
    ax = axes.flat[k]
    cse = f"smr100_{s}_p50"
    w = t11[t11["case"] == cse].set_index("t").sort_index()
    ax.plot(w.index, w["S_t_2004_per_MW"] * KW24, color=SCHED_C[s], lw=2.0,
            marker="o", ms=3.5, label="S_t (myopic, controls the model)")
    ax.fill_between(w.index, w["C_cut_2004_per_MW"] * KW24,
                    w["C_hold_2004_per_MW"] * KW24, color=SCHED_C[s],
                    alpha=0.16, lw=0, label="C_b band (post-2050 assumption)")
    ax.plot(w.index, w["C_cut_2004_per_MW"] * KW24, color=SCHED_C[s], lw=1.1,
            ls=":", label="C_b cut (zero after 2050)")
    ax.plot(w.index, w["C_hold_2004_per_MW"] * KW24, color=SCHED_C[s], lw=1.4,
            ls="--", label="C_b hold (2050 value continues)")
    ax.xaxis.set_major_locator(mpl.ticker.MaxNLocator(integer=True))
    ax.set_title(SCHED_LABEL[s], fontsize=9)
    if k % 3 == 0:
        ax.set_ylabel("support per build\\n(2024 $ / kW)")
    if k >= 3:
        ax.set_xlabel("build year")
axes.flat[0].legend(fontsize=7)
fig.suptitle("Myopic requirement S_t against the foresight companion C_b, smr100 p50\\n"
             "(band: the two post-2050 dual conventions)", y=1.03)
fig.tight_layout()
savefig(fig, "f14_myopia_wedge.png")
plt.show()

r = t11[t11["case"].str.startswith("smr100")]
early = r[r["t"] <= 2041]
print("hold / myopic ratio, smr100: "
      f"{r['hold_over_S'].min():.2f} .. {r['hold_over_S'].max():.2f} "
      f"(builds through 2041: {early['hold_over_S'].min():.2f} .. "
      f"{early['hold_over_S'].max():.2f})")
late = r[r["t"] == 2050]
print("hold / S at 2050 (identity check, expect near 1): "
      f"{late['hold_over_S'].min():.2f} .. {late['hold_over_S'].max():.2f}")
print("post-2050 tail share of C_hold at 2050 builds: "
      f"{late['tail_share_of_hold'].min():.2f} .. {late['tail_share_of_hold'].max():.2f}")
""")

# ================================================================================
# S9 — equality flip
# ================================================================================

md("""## S9 — Equality-flip note

`smr100_eia_p50_eq` runs the same world as `smr100_eia_p50` with the mandate as
a floor plus a ceiling (`GSw_NuclearCapMandate=2`). The QA notebook compared
the two runs (phase D). Summary of the evidence:""")

code("""eqf = pd.read_csv(CHECKS_EXPORTS / "eq_flip_comparison.csv")
print(eqf.to_string(index=False))
o1, o2 = OBJ["smr100_eia_p50"], OBJ["smr100_eia_p50_eq"]
print(f"\\nobjective: floor {o1:.6e}, equality {o2:.6e}, rel diff {abs(o1-o2)/o1:.1e}")
has_ub = "nuclear_cap_price_ub" in h5_keys("smr100_eia_p50_eq")
print(f"ceiling dual key present in the eq h5: {has_ub} "
      "(absent = all-zero = the ceiling never binds)")
d1 = DUALS[DUALS['case'] == 'smr100_eia_p50'].set_index('t')['dual_2004_MWyr']
d2 = DUALS[DUALS['case'] == 'smr100_eia_p50_eq'].set_index('t')['dual_2004_MWyr']
print(f"floor duals, max rel diff: "
      f"{float(((d1 - d2).abs() / d1.clip(lower=1)).max()):.1e}")
""")

md("""The objective is identical. The floor duals match. The ceiling dual is
all-zero, so the writer dropped its key. The remaining solution differences
(`cap` max relative difference about 4e-4, `gen_ann` about 3e-2) sit at the
scale of a degenerate-LP reshuffle in non-nuclear technologies. Conclusion:
the constraint form causes no change in behavior. The floor lock (issue 6)
loses nothing. The fans in this notebook exclude the equality copy.""")

# ================================================================================
# S10 — caveats + manifest
# ================================================================================

md("""## S10 — Caveats and limitations

1. **National aggregates only.** Identical national builds diverge in siting
   across cost worlds, and the reshuffle propagates to transmission and
   dispatch (P7). Regional or transmission readouts across cases are
   siting-degenerate. This notebook does not show them.
2. **No no-mandate baseline.** No number here is a mandate-against-
   counterfactual cost.
3. **Cross-schedule comparisons conflate the mandate and the drawn cost
   world.** Each schedule x percentile is its own joint draw.
4. **Sequential, myopic solve.** The duals are per-solve marginals without
   foresight. A forward-looking planner can price the same floor differently.
5. **NPV end effects.** Lump capex plus a 2050 window penalizes late builds in
   the ambitious schedules.
6. **ITC translation status.** The rates in S8 follow
   `ITC calculation procedure.md` (sequential logic: S_t = raw dual, no
   discounting across years; fin_mult inversion; statutory conversion). The
   paper plan locks the formula before results interpretation. Until then the
   rates are provisional. The companion value C_b depends on the dual path
   after 2050, which the model does not see. The notebook brackets it with two
   conventions (zero after 2050, and the 2050 value held through the window);
   read only conclusions that hold across the band. The within-year transfer
   uses regional cost data only (P7 supports this approximation).
7. **Adverse findings recap.** `smr100_eia_p05` overbuilds its floor by up to
   3%. Every large100 case has two clearly slack years, and `large100_eia_p50`
   prices its floor in only 6 of 12 mandated years. In the p95 worlds the dual
   does not decay by 2050: the bridge does not come down inside the horizon in
   the expensive draws.

The pilot runs (`smr100_eia_{lo,mid,hi}`) are not in this analysis, and their
dual levels are never quotable.""")

code("""# ---- output manifest -------------------------------------------------------------------------------
print("files that this notebook wrote:\\n")
for d in (EXPORTS, FIGURES):
    for p in sorted(d.iterdir()):
        print(f"  {p.relative_to(HERE)}  ({p.stat().st_size / 1e3:.0f} kB)")
""")

nb["cells"] = C
out = "step3_analysis.ipynb"
nbf.write(nb, out)
print(f"wrote {out} with {len(C)} cells")
