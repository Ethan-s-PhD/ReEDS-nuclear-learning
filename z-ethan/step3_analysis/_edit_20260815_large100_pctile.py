"""Extend step3_analysis.ipynb from 25 to 37 base-world cases (2026-08-15).

Adds the 12 `large100_{sched}_{p05,p95}` percentile runs from the Step 4
delivery: config + duals sourcing (step4_checks exports), figure/table
extensions (f02/f04/f06/f07/f10/f11/f12 + new t15/f15), and header text.

Edit method per the established convention (the notebook is edited in place by
id-targeted, assert-guarded string replacements; `_build_notebook.py` is STALE
and must never be run). Idempotent: re-running this script is a no-op after the
first application.

Run with any python (json + stdlib only), then re-execute the notebook
headless on the playground-env kernel with drive D mounted.
"""
import json
from pathlib import Path

NB = Path(__file__).resolve().parent / "step3_analysis.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
CELLS = {c["id"]: c for c in nb["cells"]}
IDX = {c["id"]: i for i, c in enumerate(nb["cells"])}

ALREADY = "CASES4_LARGE" in "".join(CELLS["e9a82fe7"]["source"])
if ALREADY:
    print("edits already applied; nothing to do")
    raise SystemExit(0)

n_edits = 0


def src(cid):
    return "".join(CELLS[cid]["source"])


def put(cid, text):
    CELLS[cid]["source"] = text.splitlines(keepends=True)


def rep(cid, old, new, count=1):
    global n_edits
    s = src(cid)
    found = s.count(old)
    assert found == count, f"cell {cid}: expected {count} occurrence(s), found {found}:\n{old[:200]}"
    put(cid, s.replace(old, new))
    n_edits += 1


# ---- cell 0 (header md) -----------------------------------------------------------
rep("56f7a390",
    "# Step 3 analysis \u2014 25 production runs\n\n"
    "This notebook characterizes the 25 production run outputs from NREL.\n"
    "The output files are in `D:\\ReEDS files\\nuclear-learning\\smr100 first run`.\n"
    "The run matrix is `cases_nuclearlearning_smr100.csv`\n"
    "(18 smr100 cases + 6 large100 cases + 1 equality case).\n"
    "The QA notebook `z-ethan/step3_checks/step3_output_checks.ipynb` already passed\n"
    "all 44 pass/fail tests on these files.",
    "# Step 3 analysis \u2014 37 base-world runs\n\n"
    "This notebook characterizes the 37 base-world run outputs from NREL: the 25\n"
    "Step 3 production runs plus the 12 `large100_{sched}_{p05,p95}` percentile\n"
    "runs that returned with the Step 4 delivery (2026-08-15).\n"
    "The Step 3 files are in `D:\\ReEDS files\\nuclear-learning\\smr100 first run`;\n"
    "the large100 percentile files are in `D:\\ReEDS files\\nuclear-learning\\step4 runs`.\n"
    "The run matrices are `cases_nuclearlearning_smr100.csv`\n"
    "(18 smr100 cases + 6 large100 p50 cases + 1 equality case) and the 12\n"
    "large100 percentile columns of `cases_nuclearlearning_step4.csv`.\n"
    "The QA notebooks (`z-ethan/step3_checks/`, 44 pass/fail tests, and\n"
    "`z-ethan/step4_checks/`, 44 pass/fail tests) already passed on these files.")

rep("56f7a390",
    "and (c) smr100 against large100 at p50 as conditional what-ifs.",
    "and (c) smr100 against large100 percentile bands as conditional what-ifs.")

# ---- cell 1 (config) --------------------------------------------------------------
rep("e9a82fe7",
    'H5_DIR = Path("D:/ReEDS files/nuclear-learning/smr100 first run")',
    'H5_DIR = Path("D:/ReEDS files/nuclear-learning/smr100 first run")\n'
    'H5_DIR4 = Path("D:/ReEDS files/nuclear-learning/step4 runs")   '
    '# large100 p05/p95 (Step 4 delivery)')

rep("e9a82fe7",
    "assert len(CASES) == 25, CASES\n",
    "assert len(CASES) == 25, CASES\n"
    "\n"
    "# Step 4 delivery (2026-08-15): the 12 large100 percentile cases complete the\n"
    "# traditional-nuclear arm to p05/p50/p95. They are base-world runs and belong\n"
    "# in this notebook; the 108 market-sensitivity runs live in z-ethan/step4_analysis.\n"
    'cases_csv4 = pd.read_csv(REPO / "cases_nuclearlearning_step4.csv", index_col=0)\n'
    'CASES4_LARGE = [c for c in cases_csv4.columns if c.startswith("large100_")]\n'
    "assert len(CASES4_LARGE) == 12, CASES4_LARGE\n"
    "CASES = CASES + CASES4_LARGE\n"
    "assert len(CASES) == 37, len(CASES)\n")

rep("e9a82fe7",
    'def sw(case, name):\n'
    '    """Read one switch value for one case. An empty cell uses the default value."""\n'
    '    v = cases_csv.loc[name, case]\n'
    '    if pd.isna(v) or str(v).strip() == "":\n'
    '        v = cases_csv.loc[name, "Default Value"]\n'
    '    return str(v).strip()',
    'def sw(case, name):\n'
    '    """Read one switch value for one case. An empty cell uses the default value."""\n'
    '    csv_ = cases_csv4 if case in CASES4_LARGE else cases_csv\n'
    '    v = csv_.loc[name, case]\n'
    '    if pd.isna(v) or str(v).strip() == "":\n'
    '        v = csv_.loc[name, "Default Value"]\n'
    '    return str(v).strip()')

rep("e9a82fe7",
    'H5 = {c: H5_DIR / f"test1_{c}_outputs.h5" for c in CASES}',
    'H5 = {c: (H5_DIR4 / f"step4_{c}_outputs.h5" if c in CASES4_LARGE\n'
    '          else H5_DIR / f"test1_{c}_outputs.h5") for c in CASES}')

# ---- cell 4 (data-assembly md) ----------------------------------------------------
rep("aa79feab",
    "One pass reads the small keys from each of the 25 h5 files into tidy frames.",
    "One pass reads the small keys from each of the 37 h5 files into tidy frames.")
rep("aa79feab",
    "The mandate and dual data come from the QA exports\n"
    "`z-ethan/step3_checks/exports/duals_by_year.csv` and `overbuild_by_case.csv`.\n"
    "Those files passed the QA tests. A spot test below re-derives three cases from\n"
    "the h5 files and makes sure that the export is current.",
    "The mandate and dual data come from the QA exports\n"
    "`z-ethan/step3_checks/exports/` (the 25 Step 3 cases) and\n"
    "`z-ethan/step4_checks/exports/` (the 12 large100 percentile cases).\n"
    "Those files passed the QA tests. A spot test below re-derives four cases from\n"
    "the h5 files and makes sure that the exports are current.")

# ---- cell 5 (duals from QA exports) -----------------------------------------------
rep("c78b98c2",
    'DUALS = pd.read_csv(CHECKS_EXPORTS / "duals_by_year.csv")\n'
    'OVB = pd.read_csv(CHECKS_EXPORTS / "overbuild_by_case.csv")\n'
    'assert set(DUALS["case"]) == set(CASES) and set(OVB["case"]) == set(CASES)',
    'CHECKS4_EXPORTS = REPO / "z-ethan" / "step4_checks" / "exports"\n'
    'DUALS = pd.read_csv(CHECKS_EXPORTS / "duals_by_year.csv")\n'
    'OVB = pd.read_csv(CHECKS_EXPORTS / "overbuild_by_case.csv")\n'
    'D4 = pd.read_csv(CHECKS4_EXPORTS / "duals_by_year.csv")\n'
    'O4 = pd.read_csv(CHECKS4_EXPORTS / "overbuild_by_case.csv")\n'
    'DUALS = pd.concat([DUALS, D4[D4["case"].isin(CASES4_LARGE)]], ignore_index=True)\n'
    'OVB = pd.concat([OVB, O4[O4["case"].isin(CASES4_LARGE)]], ignore_index=True)\n'
    'assert set(DUALS["case"]) == set(CASES) and set(OVB["case"]) == set(CASES)')

# ---- cell 6 (freshness) -----------------------------------------------------------
rep("b3e5441c",
    'SPOT = ["smr100_eia_p05", "smr100_eo_p95", "large100_eia_p50"]',
    'SPOT = ["smr100_eia_p05", "smr100_eo_p95", "large100_eia_p50", "large100_eo_p95"]')
rep("b3e5441c",
    "# Re-derive the dual and the mandated-tech capacity for three cases straight from",
    "# Re-derive the dual and the mandated-tech capacity for four cases straight from")

# ---- cell 7 (one-pass loop header comment) ----------------------------------------
rep("e2510eca",
    "# ---- one pass over the 25 files: costs, NPV inputs, ITC, finance",
    "# ---- one pass over the 37 files: costs, NPV inputs, ITC, finance")

# ---- cell 8 (S1 md): ranking provenance of the large100 percentiles ---------------
rep("cd93ac1c",
    "The percentiles p05 / p50 / p95 are joint cost-world draws. Each one is the\n"
    "draw at that percentile of the discounted SMR program NPV over 10,000 draws for\n"
    "that schedule. They are real sampled worlds, not pointwise envelopes.",
    "The percentiles p05 / p50 / p95 are joint cost-world draws. Each smr100 one is\n"
    "the draw at that percentile of the discounted SMR program NPV over 10,000\n"
    "draws for that schedule; each large100 one ranks on the sibling **pure-large**\n"
    "program NPV (`selected_draws_large.csv`). They are real sampled worlds, not\n"
    "pointwise envelopes.")

# ---- cell 11 (objective sanity) ---------------------------------------------------
rep("2eec15a3",
    "obj_tbl = pd.DataFrame(rows)",
    'for s in SCHEDULES:\n'
    '    o = {p: OBJ[f"large100_{s}_{p}"] for p in ("p05", "p50", "p95")}\n'
    '    rows.append(dict(schedule=f"{s} (large)", **{k: f"{v:.4e}" for k, v in o.items()},\n'
    '                     ordered=bool(o["p05"] <= o["p50"] <= o["p95"])))\n'
    "obj_tbl = pd.DataFrame(rows)")
rep("2eec15a3",
    'print("objective is ordered p05 <= p50 <= p95 in all six schedules.")',
    'print("objective is ordered p05 <= p50 <= p95 in all six schedules, both families.")')

# ---- cell 14 (f02 CASE_ORDER + figure height) -------------------------------------
rep("f0b32c20",
    '+ ["smr100_eia_p50_eq"] + [f"large100_{s}_p50" for s in SCHEDULES])',
    '+ ["smr100_eia_p50_eq"]\n'
    '              + [f"large100_{s}_{p}" for s in SCHEDULES for p in ("p05", "p50", "p95")])')
rep("f0b32c20",
    "fig, ax = plt.subplots(figsize=(9, 8.5))",
    "fig, ax = plt.subplots(figsize=(9, 11.5))")

# ---- cell 18 (f04: large100 band instead of the p50 overlay) ----------------------
rep("50efbfee",
    '    dl = (DUALS[(DUALS["case"] == f"large100_{s}_p50") & (DUALS["t"] >= 2029)]\n'
    '          .set_index("t")["dual_2024_MWyr"] * KWYR)\n'
    '    ax.plot(dl.index, dl.values, color=COL["large"], lw=1.4, ls="--")',
    '    pivL = (DUALS[(DUALS["family"] == "large") & (DUALS["schedule"] == s)\n'
    '                  & (DUALS["t"] >= 2029)]\n'
    '            .pivot_table(index="t", columns="pct", values="dual_2024_MWyr") * KWYR)\n'
    '    ax.fill_between(pivL.index, pivL["p05"], pivL["p95"], color=COL["large"],\n'
    '                    alpha=0.12, lw=0)\n'
    '    for p in ("p05", "p50", "p95"):\n'
    '        ax.plot(pivL.index, pivL[p], color=COL["large"], ls="--",\n'
    '                lw=PCT_STYLE[p]["lw"] * 0.7, alpha=PCT_STYLE[p]["alpha"] * 0.8)')
rep("50efbfee",
    '["p05", "p50", "p95", "large100 p50", "mandated, near-zero dual"]',
    '["p05", "p50", "p95", "large100 p05-p95", "mandated, near-zero dual"]')
rep("50efbfee",
    '"large100 p50 comparator dashed", y=1.02)',
    '"large100 percentile band dashed", y=1.02)')

# ---- cell 21 (f06: large lines at all three percentiles) --------------------------
rep("b8178deb",
    'ys_l = [t03i.loc[f"large100_{s}_p50", "mean_binding_dual_2024_kWyr"] for s in SCHEDULES]\n'
    'ax.plot(xs, ys_l, marker="s", ms=5, color=COL["large"], lw=1.4, ls="--")\n'
    'ax.annotate("large100 p50", (xs[-1], ys_l[-1]), xytext=(6, 0),\n'
    '            textcoords="offset points", color=COL["large"], fontsize=8.5, va="center")',
    'for p in ("p05", "p50", "p95"):\n'
    '    ys_l = [t03i.loc[f"large100_{s}_{p}", "mean_binding_dual_2024_kWyr"]\n'
    '            for s in SCHEDULES]\n'
    '    ax.plot(xs, ys_l, marker="s", ms=4, color=COL["large"], ls="--",\n'
    '            lw=PCT_STYLE[p]["lw"] * 0.8, alpha=PCT_STYLE[p]["alpha"])\n'
    '    ax.annotate(f"large {p}", (xs[-1], ys_l[-1]), xytext=(6, 0),\n'
    '                textcoords="offset points", color=COL["large"], fontsize=8,\n'
    '                va="center", alpha=PCT_STYLE[p]["alpha"])')

# ---- new cells after f06: t15 + f15 (M5-b / Fig 6 panel c) ------------------------
t15_md = {
    "cell_type": "markdown", "id": "t15md001", "metadata": {},
    "source": """### t15 + f15 — the large100 percentile band against the smr100 band

The Step 3 finding to generalize (M5-b): at p50 the large100 comparators need
about 1.2x to 1.4x the smr100 dual on shared binding years. With the percentile
arm complete, t15 recomputes that ratio at p05 and p95, and f15 draws the two
families' dual bands per schedule (the paper's Fig 6 panel c). The conditional
what-if caveat stands: the two families differ in mandated technology, mandate
basis, and drawn world.""".splitlines(keepends=True),
}
t15_code = {
    "cell_type": "code", "id": "t15cd001", "metadata": {},
    "execution_count": None, "outputs": [],
    "source": '''# ---- t15 + f15: large100 percentile band against the smr100 band (M5-b) ---------------
rows15 = []
for s in SCHEDULES:
    for p in ("p05", "p50", "p95"):
        dl = (DUALS[(DUALS["case"] == f"large100_{s}_{p}") & DUALS["binding"]]
              .set_index("t")["dual_2024_MWyr"])
        ds = (DUALS[(DUALS["case"] == f"smr100_{s}_{p}") & DUALS["binding"]]
              .set_index("t")["dual_2024_MWyr"])
        shared = sorted(set(dl.index) & set(ds.index))
        rows15.append(dict(
            schedule=s, pct=p, n_shared_binding=len(shared),
            large_mean_2024_kWyr=(round(float(dl.reindex(shared).mean()) * KWYR, 1)
                                  if shared else None),
            smr_mean_2024_kWyr=(round(float(ds.reindex(shared).mean()) * KWYR, 1)
                                if shared else None),
            ratio_large_over_smr=(round(float(dl.reindex(shared).mean()
                                              / ds.reindex(shared).mean()), 2)
                                  if shared else None)))
t15 = pd.DataFrame(rows15)
t15.to_csv(EXPORTS / "t15_large_ratio.csv", index=False)
piv15 = (t15.pivot_table(index="schedule", columns="pct", values="ratio_large_over_smr")
         .reindex(SCHEDULES))
print("large100 / smr100 mean binding dual ratio (shared binding years):")
print(piv15.to_string())

# f15: the two families' dual bands per schedule (Fig 6 panel c)
fig, axes = plt.subplots(2, 3, figsize=(12.5, 6.5), sharex=True, sharey=True)
for k, s in enumerate(SCHEDULES):
    ax = axes.flat[k]
    for fam, colr in (("smr", COL["smr"]), ("large", COL["large"])):
        piv = (DUALS[(DUALS["family"] == fam) & (DUALS["schedule"] == s)
                     & (DUALS["variant"] != "eq") & (DUALS["t"] >= 2029)]
               .pivot_table(index="t", columns="pct", values="dual_2024_MWyr") * KWYR)
        ax.fill_between(piv.index, piv["p05"], piv["p95"], color=colr, alpha=0.15, lw=0)
        ax.plot(piv.index, piv["p50"], color=colr, lw=1.8,
                label=f"{fam}100 p50" if k == 0 else None)
    ax.set_title(SCHED_LABEL[s], fontsize=9)
    if k % 3 == 0:
        ax.set_ylabel("mandate dual (2024$ / kW-yr)")
    if k >= 3:
        ax.set_xlabel("year")
axes.flat[0].legend(fontsize=8)
fig.suptitle("Required-subsidy bands: large100 p05-p95 against smr100 p05-p95 "
             "(band = percentile range, line = p50)", y=1.02)
fig.tight_layout()
savefig(fig, "f15_large_band.png")
plt.show()
'''.splitlines(keepends=True),
}
pos = IDX["2d91220d"]           # the S5 markdown cell; insert both cells before it
nb["cells"][pos:pos] = [t15_md, t15_code]

# ---- cell 24 (f07: large100 dashed on every percentile panel) ---------------------
rep("4f4de157",
    '    if p == "p50":     # large100 comparators share the p50 panel, dashed\n'
    '        for s in SCHEDULES:\n'
    '            c = f"large100_{s}_p50"\n'
    '            d = DUALS[(DUALS["case"] == c) & DUALS["mandated"]].set_index("t").sort_index()\n'
    '            peak = d["dual_2004_MWyr"].max()\n'
    '            x = d.index - d.index.min()\n'
    '            ax.plot(x, d["dual_2004_MWyr"] / peak, color=SCHED_C[s], lw=1.0,\n'
    '                    ls="--", alpha=0.55)\n'
    '    ax.set_title(p + (" (dashed: large100)" if p == "p50" else ""))',
    '    for s in SCHEDULES:     # large100 comparators share each panel, dashed\n'
    '        c = f"large100_{s}_{p}"\n'
    '        d = DUALS[(DUALS["case"] == c) & DUALS["mandated"]].set_index("t").sort_index()\n'
    '        peak = d["dual_2004_MWyr"].max()\n'
    '        if peak <= 1.0:\n'
    '            continue\n'
    '        x = d.index - d.index.min()\n'
    '        ax.plot(x, d["dual_2004_MWyr"] / peak, color=SCHED_C[s], lw=1.0,\n'
    '                ls="--", alpha=0.55)\n'
    '    ax.set_title(p + " (dashed: large100)")')

# ---- cell 29 (f10 + t06: large percentile spread added) ---------------------------
rep("afbb2ec2",
    '    spread = CTOT.loc[f"smr100_{s}_p95"] - CTOT.loc[f"smr100_{s}_p05"]\n'
    '    delta = CTOT.loc[f"smr100_{s}_p50"] - CTOT.loc[f"large100_{s}_p50"]\n'
    '    axes[0].plot(yrs, spread[yrs], color=SCHED_C[s], lw=1.7, label=s)\n'
    '    axes[1].plot(yrs, delta[yrs], color=SCHED_C[s], lw=1.7)\n'
    '    for t in yrs:\n'
    '        rows.append(dict(schedule=s, t=t,\n'
    '                         p95_minus_p05_B2024=round(float(spread[t]), 2),\n'
    '                         smr_minus_large_p50_B2024=round(float(delta[t]), 2)))',
    '    spread = CTOT.loc[f"smr100_{s}_p95"] - CTOT.loc[f"smr100_{s}_p05"]\n'
    '    spread_l = CTOT.loc[f"large100_{s}_p95"] - CTOT.loc[f"large100_{s}_p05"]\n'
    '    delta = CTOT.loc[f"smr100_{s}_p50"] - CTOT.loc[f"large100_{s}_p50"]\n'
    '    axes[0].plot(yrs, spread[yrs], color=SCHED_C[s], lw=1.7, label=s)\n'
    '    axes[0].plot(yrs, spread_l[yrs], color=SCHED_C[s], lw=1.0, ls="--", alpha=0.6)\n'
    '    axes[1].plot(yrs, delta[yrs], color=SCHED_C[s], lw=1.7)\n'
    '    for t in yrs:\n'
    '        rows.append(dict(schedule=s, t=t,\n'
    '                         p95_minus_p05_B2024=round(float(spread[t]), 2),\n'
    '                         large_p95_minus_p05_B2024=round(float(spread_l[t]), 2),\n'
    '                         smr_minus_large_p50_B2024=round(float(delta[t]), 2)))')
rep("afbb2ec2",
    'axes[0].set_title("p95 - p05 annual cost spread\\n(same mandate, drawn world isolated)")',
    'axes[0].set_title("p95 - p05 annual cost spread\\n'
    '(same mandate, drawn world isolated; dashed: large100)")')

# ---- cell 31 (t07 + f11: large percentile columns and lines) ----------------------
rep("dcecba76",
    '        large_p50=round(NPV[f"large100_{s}_p50"], 1),',
    '        large_p05=round(NPV[f"large100_{s}_p05"], 1),\n'
    '        large_p50=round(NPV[f"large100_{s}_p50"], 1),\n'
    '        large_p95=round(NPV[f"large100_{s}_p95"], 1),')
rep("dcecba76",
    'ys_l = [NPV[f"large100_{s}_p50"] for s in SCHEDULES]\n'
    'ax.plot(xs, ys_l, marker="s", ms=5, color=COL["large"], lw=1.4, ls="--")\n'
    'ax.annotate("large100 p50", (xs[-1], ys_l[-1]), xytext=(6, 0),\n'
    '            textcoords="offset points", color=COL["large"], fontsize=8.5, va="center")',
    'for p in ("p05", "p50", "p95"):\n'
    '    ys_l = [NPV[f"large100_{s}_{p}"] for s in SCHEDULES]\n'
    '    ax.plot(xs, ys_l, marker="s", ms=4, color=COL["large"], ls="--",\n'
    '            lw=PCT_STYLE[p]["lw"] * 0.8, alpha=PCT_STYLE[p]["alpha"])\n'
    '    ax.annotate(f"large {p}", (xs[-1], ys_l[-1]), xytext=(6, 0),\n'
    '                textcoords="offset points", color=COL["large"], fontsize=8,\n'
    '                va="center", alpha=PCT_STYLE[p]["alpha"])')

# ---- cell 33 (t08 + f12: large percentile lines + bar order) ----------------------
rep("bca1c170",
    '    bl = BILL[f"large100_{s}_p50"]\n'
    '    ax.plot(yrs, bl.reindex(yrs), color=COL["large"], lw=1.3, ls="--")',
    '    for p in ("p05", "p50", "p95"):\n'
    '        bl = BILL[f"large100_{s}_{p}"]\n'
    '        ax.plot(yrs, bl.reindex(yrs), color=COL["large"], ls="--",\n'
    '                lw=PCT_STYLE[p]["lw"] * 0.65, alpha=PCT_STYLE[p]["alpha"] * 0.8)')
rep("bca1c170",
    '         + [f"large100_{s}_p50" for s in SCHEDULES])',
    '         + [f"large100_{s}_{p}" for s in SCHEDULES for p in ("p05", "p50", "p95")])')

# ---- cell 35 (financing replication self-check: add a percentile case) ------------
rep("bfdebdc1",
    'for c in ["smr100_eia_p50", "smr100_eo_p95", "large100_eo_p50"]:',
    'for c in ["smr100_eia_p50", "smr100_eo_p95", "large100_eo_p50", "large100_eo_p95"]:')

# ---- cell 36 (baseline text 25 -> 37) ---------------------------------------------
rep("e3e7fc5c",
    '"fin_mult == fin_mult_noITC for the mandated technology in all 25 runs.")',
    '"fin_mult == fin_mult_noITC for the mandated technology in all 37 runs.")')

# ---- write ------------------------------------------------------------------------
NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"applied {n_edits} edits + 2 inserted cells (t15md001, t15cd001) -> {NB.name}")
