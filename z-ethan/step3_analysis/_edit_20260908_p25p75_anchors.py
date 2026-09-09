"""Extend step3_analysis.ipynb from 37 to 49 base-world cases (2026-09-08).

Adds the 12 `smr100_{sched}_{p25,p75}` mandate-arm anchors from the rate_design
delivery (anchor densification, rate_design/methods.md v2.2 + v2.3; Ethan's
2026-09-08 ruling: the anchors join this notebook). Every existing table
(t01-t20) gains the anchors as new rows; every existing figure stays on the
37 production cases (`CASES_PROD`) so the paper's embedded exhibits do not
change. New: t21 (five-percentile shadow-price ordering), t22 (five-percentile
bridge metrics), f18 (five-percentile shadow-price fans).

Edit method per the established convention (id-targeted, assert-guarded string
replacements; `_build_notebook.py` is STALE and must never be run). Idempotent.
Run with any python (json + stdlib only), then re-execute the notebook headless
on the playground-env kernel with drive D mounted. The regression tie is
`_regress_20260908.py` (every pre-existing exported row byte-identical).
"""
import json
from pathlib import Path

NB = Path(__file__).resolve().parent / "step3_analysis.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
CELLS = {c["id"]: c for c in nb["cells"]}
IDX = {c["id"]: i for i, c in enumerate(nb["cells"])}

ALREADY = "CASES_RD_ANCHOR" in "".join(CELLS["e9a82fe7"]["source"])
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


def new_code(cid, text):
    return {"cell_type": "code", "execution_count": None, "id": cid, "metadata": {},
            "outputs": [], "source": text.splitlines(keepends=True)}


def new_md(cid, text):
    return {"cell_type": "markdown", "id": cid, "metadata": {},
            "source": text.splitlines(keepends=True)}


# ---- cell 0 (header md) -----------------------------------------------------------
rep("56f7a390",
    "# Step 3 analysis \u2014 37 base-world runs\n\n"
    "This notebook characterizes the 37 base-world run outputs from NREL: the 25\n"
    "Step 3 production runs plus the 12 `large100_{sched}_{p05,p95}` percentile\n"
    "runs that returned with the Step 4 delivery (2026-08-15).\n",
    "# Step 3 analysis \u2014 49 base-world runs\n\n"
    "This notebook characterizes the 49 base-world run outputs from NREL: the 25\n"
    "Step 3 production runs, the 12 `large100_{sched}_{p05,p95}` percentile\n"
    "runs that returned with the Step 4 delivery (2026-08-15), and the 12\n"
    "`smr100_{sched}_{p25,p75}` mandate-arm anchors that returned with the\n"
    "rate_design delivery (2026-09-08; anchor densification, registered in\n"
    "`z-ethan/rate_design/methods.md` v2.2). The anchors enter every table as\n"
    "new rows. The pre-existing figures stay on the 37 production cases; the\n"
    "anchors get their own exhibits (t21, t22, f18).\n")
rep("56f7a390",
    "the large100 percentile files are in `D:\\ReEDS files\\nuclear-learning\\step4 runs`.\n",
    "the large100 percentile files are in `D:\\ReEDS files\\nuclear-learning\\step4 runs`;\n"
    "every file now also sits in `D:\\ReEDS files\\nuclear-learning\\All runs so far`\n"
    "(the p25/p75 anchors as `rate_design_{case}_outputs.h5`).\n")
rep("56f7a390",
    "The QA notebooks (`z-ethan/step3_checks/`, 44 pass/fail tests, and\n"
    "`z-ethan/step4_checks/`, 44 pass/fail tests) already passed on these files.",
    "The QA notebooks (`z-ethan/step3_checks/`, 44 pass/fail tests,\n"
    "`z-ethan/step4_checks/`, 44 pass/fail tests, and `z-ethan/rate_design_checks/`\n"
    "for the anchors) already passed on these files.")

# ---- cell 1 (config) --------------------------------------------------------------
rep("e9a82fe7",
    "CASES = CASES + CASES4_LARGE\n"
    "assert len(CASES) == 37, len(CASES)\n",
    "CASES = CASES + CASES4_LARGE\n"
    "assert len(CASES) == 37, len(CASES)\n"
    "CASES_PROD = list(CASES)      # the 37 production cases: every pre-existing figure stays on them\n"
    "\n"
    "# rate_design delivery (2026-09-08): the 12 smr100 p25/p75 mandate-arm anchors\n"
    "# (anchor densification, rate_design/methods.md v2.2). Mandate ON, learning OFF,\n"
    "# no-nuclear-ITC baseline, standard horizon: the smr100 column pattern verbatim.\n"
    "cases_rd = pd.read_csv(REPO / \"cases_nuclearlearning_ratedesign.csv\", index_col=0)\n"
    "CASES_RD_ANCHOR = [c for c in cases_rd.columns if c.startswith(\"smr100_\")]\n"
    "assert len(CASES_RD_ANCHOR) == 12, CASES_RD_ANCHOR\n"
    "assert all(c.split(\"_\")[2] in (\"p25\", \"p75\") for c in CASES_RD_ANCHOR)\n"
    "CASES = CASES + CASES_RD_ANCHOR\n"
    "assert len(CASES) == 49, len(CASES)\n"
    "DESIGN = {c: (\"anchor-densification\" if c in CASES_RD_ANCHOR else \"production\") for c in CASES}\n")
rep("e9a82fe7",
    "    csv_ = cases_csv4 if case in CASES4_LARGE else cases_csv\n",
    "    csv_ = (cases_csv4 if case in CASES4_LARGE\n"
    "            else cases_rd if case in CASES_RD_ANCHOR else cases_csv)\n")
rep("e9a82fe7",
    'H5 = {c: (H5_DIR4 / f"step4_{c}_outputs.h5" if c in CASES4_LARGE\n'
    '          else H5_DIR / f"test1_{c}_outputs.h5") for c in CASES}',
    'H5 = {c: (H5_DIR4 / f"step4_{c}_outputs.h5" if c in CASES4_LARGE\n'
    '          else H5_DIR / f"rate_design_{c}_outputs.h5" if c in CASES_RD_ANCHOR\n'
    '          else H5_DIR / f"test1_{c}_outputs.h5") for c in CASES}')
rep("e9a82fe7",
    'print(f"cases: {len(CASES)} ({len(SMR_CASES)} smr100 + {len(LARGE_CASES)} large100, "\n'
    '      f"incl. equality copy)")',
    'print(f"cases: {len(CASES)} ({len(SMR_CASES)} smr100 + {len(LARGE_CASES)} large100, "\n'
    '      f"incl. equality copy; {len(CASES_RD_ANCHOR)} of the smr100 are p25/p75 anchors)")')

# ---- cell 4 (data-assembly md) ----------------------------------------------------
rep("aa79feab",
    "One pass reads the small keys from each of the 37 h5 files into tidy frames.",
    "One pass reads the small keys from each of the 49 h5 files into tidy frames.")
rep("aa79feab",
    "`z-ethan/step4_checks/exports/` (the 12 large100 percentile cases).\n",
    "`z-ethan/step4_checks/exports/` (the 12 large100 percentile cases), and\n"
    "`z-ethan/rate_design_checks/exports/` (the 12 smr100 p25/p75 anchors; their\n"
    "binding/slack summary is derived here with the QA definitions).\n")

# ---- cell 5 (duals from QA exports) -----------------------------------------------
rep("c78b98c2",
    'DUALS = pd.concat([DUALS, D4[D4["case"].isin(CASES4_LARGE)]], ignore_index=True)\n'
    'OVB = pd.concat([OVB, O4[O4["case"].isin(CASES4_LARGE)]], ignore_index=True)\n'
    'assert set(DUALS["case"]) == set(CASES) and set(OVB["case"]) == set(CASES)',
    'DUALS = pd.concat([DUALS, D4[D4["case"].isin(CASES4_LARGE)]], ignore_index=True)\n'
    'OVB = pd.concat([OVB, O4[O4["case"].isin(CASES4_LARGE)]], ignore_index=True)\n'
    '# rate_design delivery: the 12 p25/p75 anchors (canonical duals schema; the\n'
    '# binding/slack summary is derived here with the step3_checks C8 definitions)\n'
    'CHECKS_RD_EXPORTS = REPO / "z-ethan" / "rate_design_checks" / "exports"\n'
    'DRD = pd.read_csv(CHECKS_RD_EXPORTS / "duals_by_year.csv")\n'
    'DRD = DRD[DRD["case"].isin(CASES_RD_ANCHOR) & (DRD["t"] <= 2050)].reset_index(drop=True)\n'
    'assert set(DRD["case"]) == set(CASES_RD_ANCHOR)\n'
    'ord_rows = []\n'
    'for c in CASES_RD_ANCHOR:\n'
    '    sub = DRD[(DRD["case"] == c) & (DRD["mandate_MW"] > 0)]\n'
    '    ord_rows.append(dict(case=c, n_mandated_years=len(sub),\n'
    '                         n_binding_years=int((sub["dual_2004_MWyr"] > 1.0).sum()),\n'
    '                         n_slack_years=int((sub["slack_MW"] > 100).sum()),\n'
    '                         first_binding_year=(int(sub[sub["dual_2004_MWyr"] > 1.0]["t"].min())\n'
    '                                             if (sub["dual_2004_MWyr"] > 1.0).any() else None),\n'
    '                         max_overbuild_ratio=round(float((sub["cap_MW"] / sub["mandate_MW"]).max()), 2)))\n'
    'DUALS = pd.concat([DUALS, DRD[DUALS.columns]], ignore_index=True)\n'
    'OVB = pd.concat([OVB, pd.DataFrame(ord_rows)[OVB.columns]], ignore_index=True)\n'
    'assert set(DUALS["case"]) == set(CASES) and set(OVB["case"]) == set(CASES)')

# ---- cell 6 (freshness) -----------------------------------------------------------
rep("b3e5441c",
    'SPOT = ["smr100_eia_p05", "smr100_eo_p95", "large100_eia_p50", "large100_eo_p95"]',
    'SPOT = ["smr100_eia_p05", "smr100_eo_p95", "large100_eia_p50", "large100_eo_p95",\n'
    '        "smr100_eo_p75", "smr100_aj_p25"]')
rep("b3e5441c",
    "# Re-derive the dual and the mandated-tech capacity for four cases straight from",
    "# Re-derive the dual and the mandated-tech capacity for six cases straight from")

# ---- cell 7 (one-pass loop header comment) ----------------------------------------
rep("e2510eca",
    "# ---- one pass over the 37 files: costs, NPV inputs, ITC, finance",
    "# ---- one pass over the 49 files: costs, NPV inputs, ITC, finance")

# ---- cell 8 (S1 md): anchor provenance --------------------------------------------
rep("cd93ac1c",
    "program NPV (`selected_draws_large.csv`). They are real sampled worlds, not\n"
    "pointwise envelopes.",
    "program NPV (`selected_draws_large.csv`). They are real sampled worlds, not\n"
    "pointwise envelopes. The p25 / p75 smr100 anchors (2026-09-08) are the same\n"
    "rule at q = 0.25 and 0.75 (`selected_draws_p25p75.csv`); they densify the\n"
    "cost-world axis for the offline interpolation in `z-ethan/rate_design/`.")

# ---- cell 14 (f02): the heatmap stays on the production cases ---------------------
rep("f0b32c20",
    "assert set(CASE_ORDER) == set(CASES)",
    "assert set(CASE_ORDER) == set(CASES_PROD)     # figure stays on the 37 production cases")

# ---- cell 52 (t13 figure): production cases only ----------------------------------
rep("t13fg001",
    'fcmp = t13[~t13["case"].str.endswith("_eq")].set_index("case")',
    'fcmp = t13[~t13["case"].str.endswith("_eq") & t13["case"].isin(CASES_PROD)].set_index("case")')

# ---- cell 56 (f16): production cases only ------------------------------------------
rep("t18cd001",
    'f18 = t18[~t18["case"].str.endswith("_eq")].set_index("case")',
    'f18 = t18[~t18["case"].str.endswith("_eq") & t18["case"].isin(CASES_PROD)].set_index("case")')

# ---- cell 58 (f17): production percentiles only ------------------------------------
rep("f17cd001",
    'f17 = t18[~t18["case"].str.endswith("_eq")].copy()',
    'f17 = t18[~t18["case"].str.endswith("_eq") & t18["case"].isin(CASES_PROD)].copy()')

# ---- cell 64 (S10 md): count scope -------------------------------------------------
rep("ebc6728a",
    "The required\n"
    "   model-convention ITC exceeds 100% in 5 of 329 unique rate case-years\n"
    "   (334 rows counting the equality duplicate, which adds none)",
    "The required\n"
    "   model-convention ITC exceeds 100% in 5 of 329 unique production rate\n"
    "   case-years (334 rows counting the equality duplicate, which adds none;\n"
    "   the 12 p25/p75 anchors add their own rows, counted in t21)")

# ---- new cells after f07 (cell 26): t21 / t22 / f18 --------------------------------
md21 = new_md("t21md001", """### t21, t22, f18 \u2014 the five-percentile cost-world axis (anchor densification, 2026-09-08)

The 12 `smr100_{sched}_{p25,p75}` anchors sit between the production
percentiles on the program-NPV ranking. Three exhibits read them:

- **t21** \u2014 the shadow price at all five percentiles per schedule and mandated
  year, with the pointwise ordering p05 \u2264 p25 \u2264 p50 \u2264 p75 \u2264 p95 checked
  (a crossing is reported, never hidden), and the anchors' binding/slack
  summary.
- **t22** \u2014 the bridge metrics (peak year, end/peak, first year below half
  peak) at all five percentiles: does the interior confirm the p95 reading
  that the bridge does not come down inside the horizon?
- **f18** \u2014 the shadow-price fans redrawn with the interior anchors.

The five-anchor per-year map that `z-ethan/rate_design/` builds on these
duals is certified there (gates GA1\u2013GA3, band E5), not here.""")

code21 = new_code("t21cd001", """# ---- t21: five-percentile shadow-price ordering per schedule-year --------------------------------
PCTS5 = ["p05", "p25", "p50", "p75", "p95"]
rows21, cross21 = [], []
for s in SCHEDULES:
    piv = (DUALS[(DUALS["family"] == "smr") & (DUALS["schedule"] == s)
                 & (DUALS["variant"] != "eq") & DUALS["mandated"]]
           .pivot_table(index="t", columns="pct", values="dual_2024_MWyr") * KWYR)
    assert list(piv.columns) == PCTS5, (s, list(piv.columns))
    for t, r in piv.iterrows():
        vals = [float(r[p]) for p in PCTS5]
        ordered = bool(all(vals[k + 1] >= vals[k] - 1e-6 for k in range(4)))
        rows21.append(dict(schedule=s, t=int(t), **{f"dual_{p}_2024_kWyr": round(v, 1)
                                                   for p, v in zip(PCTS5, vals)},
                           ordered=ordered))
        if not ordered:
            cross21.append((s, int(t), [round(v, 1) for v in vals]))
t21 = pd.DataFrame(rows21)
ob21 = OVB[OVB["case"].isin(CASES_RD_ANCHOR)].reset_index(drop=True)
t21.to_csv(EXPORTS / "t21_five_percentile_duals.csv", index=False)
ob21.to_csv(EXPORTS / "t21b_anchor_binding_summary.csv", index=False)
print(f"five-percentile ordering holds in {int(t21['ordered'].sum())} of {len(t21)} "
      f"schedule-years; crossings: {cross21 or 'none'}")
print(ob21.to_string(index=False))
n_over_anchor = int(t09_placeholder := 0) if False else None   # filled after t09 below
""")

code22 = new_code("t22cd001", """# ---- t22: five-percentile bridge metrics ---------------------------------------------------------
t04i = t04.set_index("case")
t03i5 = t03.set_index("case")
rows22 = []
for s in SCHEDULES:
    for p in PCTS5:
        c = f"smr100_{s}_{p}"
        rows22.append(dict(schedule=s, pct=p, case=c, design=DESIGN[c],
                           n_binding=int(t03i5.loc[c, "n_binding"]),
                           mean_binding_dual_2024_kWyr=t03i5.loc[c, "mean_binding_dual_2024_kWyr"],
                           peak_year=t04i.loc[c, "peak_year"],
                           end_over_peak=t04i.loc[c, "end_over_peak"],
                           first_year_below_half_peak=t04i.loc[c, "first_year_below_half_peak"],
                           n_zero_dual_mandated_years=int(t04i.loc[c, "n_zero_dual_mandated_years"])))
t22 = pd.DataFrame(rows22)
t22.to_csv(EXPORTS / "t22_five_percentile_bridge.csv", index=False)
print("end / peak by schedule and percentile (bridge shape at five cost worlds):")
print(t22.pivot_table(index="schedule", columns="pct", values="end_over_peak")
      .reindex(SCHEDULES)[PCTS5].to_string())
print("\\nmean binding shadow price (2024$/kW-yr):")
print(t22.pivot_table(index="schedule", columns="pct", values="mean_binding_dual_2024_kWyr")
      .reindex(SCHEDULES)[PCTS5].to_string())

# f18: the fans with the interior anchors
PCT5_STYLE = dict(PCT_STYLE)
PCT5_STYLE["p25"] = dict(lw=1.2, alpha=0.75, ls=":")
PCT5_STYLE["p75"] = dict(lw=1.2, alpha=0.75, ls=":")
PCT5_LABEL = dict(ps.PCT_LABEL)
PCT5_LABEL["p25"] = "P25 world"
PCT5_LABEL["p75"] = "P75 world"
fig, axes = plt.subplots(2, 3, figsize=(12.5, 6.5), sharex=True, sharey=True)
for k, s in enumerate(SCHEDULES):
    ax = axes.flat[k]
    piv = (DUALS[(DUALS["family"] == "smr") & (DUALS["schedule"] == s)
                 & (DUALS["variant"] != "eq") & (DUALS["t"] >= 2029)
                 & DUALS["in_program"]]
           .pivot_table(index="t", columns="pct", values="dual_2024_MWyr") * KWYR)
    ax.fill_between(piv.index, piv["p05"], piv["p95"], color=SCHED_C[s], alpha=0.10, lw=0)
    ax.fill_between(piv.index, piv["p25"], piv["p75"], color=SCHED_C[s], alpha=0.18, lw=0)
    for p in PCTS5:
        ax.plot(piv.index, piv[p], color=SCHED_C[s], **PCT5_STYLE[p])
    ax.set_title(SCHED_LABEL[s], fontsize=9)
    if k % 3 == 0:
        ax.set_ylabel("shadow price of the mandate (2024$/kW-yr)")
    if k >= 3:
        ax.set_xlabel("year")
    ax.xaxis.set_major_locator(mpl.ticker.MaxNLocator(integer=True))
handles = [mpl.lines.Line2D([], [], color=INK, **PCT5_STYLE[p]) for p in PCTS5]
axes.flat[0].legend(handles + [mpl.patches.Patch(facecolor=INK, alpha=0.18),
                               mpl.patches.Patch(facecolor=INK, alpha=0.10)],
                    [PCT5_LABEL[p] for p in PCTS5] + ["P25\u2013P75", "P5\u2013P95"], fontsize=7)
fig.tight_layout()
savefig(fig, "f18_five_percentile_fans.png")
plt.show()
""")

# t21 is placed after f07 (cell 26) but t22 needs t03/t04 (cells 17, 25) -- both before 26.
# The t09-dependent anchor count lands in a small cell after t09 (cell 39).
code21b = new_code("t21cd002", """# ---- t21c: the anchors' required-rate rows (the count the S10 recap scopes out) ----------------
a9 = t09[t09["case"].isin(CASES_RD_ANCHOR) & (t09["status"] == "rate")]
p9 = t09[t09["case"].isin(CASES_PROD) & ~t09["case"].str.endswith("_eq") & (t09["status"] == "rate")]
print(f"production (37 cases, eq excluded): {len(p9)} rate rows, {int(p9['itc_insufficient'].sum())} "
      f"above 100% on the model basis (the S10 recap count)")
print(f"p25/p75 anchors: {len(a9)} rate rows, {int(a9['itc_insufficient'].sum())} above 100%")
a9p = a9.pivot_table(index="t", columns="case", values="i_model_headline").round(3)
print(a9p.to_string())
pd.DataFrame(dict(scope=["production", "anchors"], n_rate_rows=[len(p9), len(a9)],
                  n_above_100=[int(p9["itc_insufficient"].sum()), int(a9["itc_insufficient"].sum())])
             ).to_csv(EXPORTS / "t21c_rate_row_counts.csv", index=False)
""")

# fix the placeholder line in code21 (kept simple: no placeholder)
code21["source"] = [ln for ln in code21["source"] if "t09_placeholder" not in ln]

insert_at = IDX["4f4de157"] + 1          # after f07
nb["cells"][insert_at:insert_at] = [md21, code21, code22]
insert_t09 = [i for i, c in enumerate(nb["cells"]) if c.get("id") == "5375aaf6"][0] + 1
nb["cells"][insert_t09:insert_t09] = [code21b]
n_edits += 4

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"applied {n_edits} edits; notebook now has {len(nb['cells'])} cells")
