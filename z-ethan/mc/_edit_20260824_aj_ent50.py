"""Fig 1 axis-registration fix (adjudicated 2026-08-24): score the AJ pairing on the
through-2049 stock that prices 2050.

The closed-form 2050 evaluator (shape_2050) and required_gw are defined on the engine's
entering-2050 contract: the stock that prices 2050 is the build completed through 2049.
But T4/T5/T6, the F6 contour, the F7 reference line, the F8 (Fig 1a/b) ATB marker, and
QA-3 (ii) all fed/plotted Abou-Jaoude's BY-2050 cumulative deployment on that axis --
crediting 2050's own completions (advanced adds ~15.2 GW/yr over 2045-2050, a ~7.6%
overstatement of the credited stock; ~1.4% in cost). Part 1's SHAPES/FITS and the F9
endpoint maps run the AJ ANNUAL PATH through the full engine (lag applied internally),
so they were already on the correct basis and are untouched.

Fix: define AJ_GW_ENT50 (post-2030 cumulative completed through 2049, from the same
annual interpolation N_AJ uses) and use it wherever the closed-form evaluator meets the
AJ program; labels/captions state the basis. The QUOTED paired-program totals
(12/33/199 GW by 2050) are unchanged wherever they describe the AJ program itself.

Code cells change -> re-execute the notebook headless afterwards. Idempotent.
"""
import json
import re
from pathlib import Path

NB = Path(__file__).resolve().parent / "atb_parameter_space.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
CELLS = {c["id"]: c for c in nb["cells"]}

if "AJ_GW_ENT50" in "".join(CELLS["atb-08-a08_targets"]["source"]):
    print("ENT50 fix already applied; nothing to do")
    raise SystemExit(0)

n = 0


def rep(cid, old, new):
    global n
    s = "".join(CELLS[cid]["source"])
    assert s.count(old) == 1, f"cell {cid}: pattern not unique/found:\n{old[:160]}"
    CELLS[cid]["source"] = s.replace(old, new).splitlines(keepends=True)
    n += 1


def rep_ws(cid, old, new):
    global n
    s = "".join(CELLS[cid]["source"])
    pat = re.compile(r"\s+".join(re.escape(t) for t in old.split()))
    ms = list(pat.finditer(s))
    assert len(ms) == 1, f"cell {cid}: {len(ms)} ws-tolerant matches for:\n{old[:160]}"
    m = ms[0]
    CELLS[cid]["source"] = (s[:m.start()] + new + s[m.end():]).splitlines(keepends=True)
    n += 1


# ---- targets cell: define the entering-2050 basis -----------------------------------
rep("atb-08-a08_targets",
    "AJ_GW_POST = {s: float(AJ_GW[s][-1] - AJ_GW[s][0]) for s in SCEN_ORDER}",
    "AJ_GW_POST = {s: float(AJ_GW[s][-1] - AJ_GW[s][0]) for s in SCEN_ORDER}\n"
    "\n"
    "# Entering-2050 scoring basis (adjudicated 2026-08-24): the engine's one-year lag means\n"
    "# the stock that PRICES 2050 is the build completed through 2049. Wherever the closed-form\n"
    "# 2050 evaluator (shape_2050 / required_gw, both defined on that contract) is compared\n"
    "# against the AJ program (T4/T5/T6, the F6 contour, F7's reference line, F8's marker,\n"
    "# QA-3 (ii)), the paired deployment must be the through-2049 cumulative - feeding the\n"
    "# by-2050 total credits 2050's own completions (advanced: ~15.2 GW/yr over 2045-2050,\n"
    "# a ~7.6% overstatement). Part 1 / F9 run the AJ annual path through the full engine\n"
    "# (lag applied internally) and were already on this basis. The QUOTED paired-program\n"
    "# totals (12/33/199 GW by 2050) stay by-2050 wherever they describe the program itself.\n"
    "AJ_GW_ENT50 = {s: float(np.interp(2049.0, AJ_YEARS, AJ_GW[s]) - AJ_GW[s][0])\n"
    "               for s in SCEN_ORDER}")

# ---- T4: add the through-2049 column, relabel the print -----------------------------
rep("atb-20-a21_solve_d",
    '        row = {"tech": tech, "scenario": scen, "AJ deployment (GW)": AJ_GW_POST[scen]}',
    '        row = {"tech": tech, "scenario": scen, "AJ deployment (GW)": AJ_GW_POST[scen],\n'
    '               "AJ completed through 2049 (GW)": round(AJ_GW_ENT50[scen], 1)}')
rep("atb-20-a21_solve_d",
    'print("\\nT4 - required 2030-2050 new build (GW) to hit the ATB 2050 cost, at literature anchor "\n'
    '      "worlds (u=0.5, rho=0) -> exports/atb/required_deployment_anchors.csv")',
    'print("\\nT4 - required post-2030 build completed through 2049 (GW - the stock that prices "\n'
    '      "2050) to hit the ATB 2050 cost, at literature anchor worlds (u=0.5, rho=0) "\n'
    '      "-> exports/atb/required_deployment_anchors.csv")')

# ---- T5: score on the through-2049 stock --------------------------------------------
rep("atb-20-a21_solve_d",
    '        n50 = AJ_GW_POST[scen] / TECH[tech]["unit_gw"]',
    '        n50 = AJ_GW_ENT50[scen] / TECH[tech]["unit_gw"]   # scoring basis: builds thru 2049')
rep("atb-20-a21_solve_d",
    'print("\\nT5 - minimum firm-level LR to reach the ATB 2050 cost at the paired deployment "\n'
    '      "(m=6, u=0.5, rho=0; NaN = unreachable even at LR 30%) -> exports/atb/min_lr_at_aj_deployment.csv")',
    'print("\\nT5 - minimum firm-level LR to reach the ATB 2050 cost at the paired deployment, "\n'
    '      "scored on the through-2049 stock that prices 2050 (m=6, u=0.5, rho=0; NaN = "\n'
    '      "unreachable even at LR 30%) -> exports/atb/min_lr_at_aj_deployment.csv")')

# ---- F6: contour + labels -----------------------------------------------------------
rep("atb-21-a22_f6",
    "            if np.isfinite(z).any() and (z <= AJ_GW_POST[scen]).any() \\\n"
    "                    and (np.where(np.isinf(z), 1e9, z) >= AJ_GW_POST[scen]).any():",
    "            if np.isfinite(z).any() and (z <= AJ_GW_ENT50[scen]).any() \\\n"
    "                    and (np.where(np.isinf(z), 1e9, z) >= AJ_GW_ENT50[scen]).any():")
rep("atb-21-a22_f6",
    "                                levels=[AJ_GW_POST[scen]], colors=[C_SMR], linewidths=1.8)",
    "                                levels=[AJ_GW_ENT50[scen]], colors=[C_SMR], linewidths=1.8)")
rep("atb-21-a22_f6",
    'fmt=lambda v: f"AJ {v:,.0f} GW"',
    'fmt=lambda v: f"AJ {v:,.0f} GW thru 2049"')
rep("atb-21-a22_f6",
    'cb.set_label("required new build by 2050 (GW, log scale)")',
    'cb.set_label("required build completed through 2049 (GW, log scale; prices 2050)")')

# ---- F7: reference line + labels ----------------------------------------------------
rep("atb-22-a23_f7",
    "        ax.axhline(AJ_GW_POST[scen], color=INK, lw=1.1, ls=\"--\")",
    "        ax.axhline(AJ_GW_ENT50[scen], color=INK, lw=1.1, ls=\"--\")")
rep("atb-22-a23_f7",
    '        ax.annotate(f"AJ {scen}: {AJ_GW_POST[scen]:,.0f} GW", (0.297, AJ_GW_POST[scen]*1.15),',
    '        ax.annotate(f"AJ {scen}: {AJ_GW_ENT50[scen]:,.0f} GW thru 2049",\n'
    '                    (0.297, AJ_GW_ENT50[scen]*1.15),')
rep("atb-22-a23_f7",
    'ax.set_ylabel(f"{TECH_LABEL[tech]}\\nrequired new build by 2050 (GW)")',
    'ax.set_ylabel(f"{TECH_LABEL[tech]}\\nrequired build thru 2049 (GW)")')

# ---- T6: add the through-2049 column ------------------------------------------------
rep("atb-24-a25_synth",
    '            "AJ_deployment_GW": AJ_GW_POST[scen],',
    '            "AJ_deployment_GW": AJ_GW_POST[scen],\n'
    '            "AJ_completed_2049_GW": round(AJ_GW_ENT50[scen], 1),')

# ---- QA-3 (ii): precedent world on the scoring basis --------------------------------
rep("atb-26-a27_qa",
    '    prec = BOAK_PIN["smr"][s] * shape_2050("smr", 0.095, 0.0, 0.5, 4.0, 0.0, 0.0,\n'
    '                                           AJ_GW_POST[s]/0.3)',
    '    prec = BOAK_PIN["smr"][s] * shape_2050("smr", 0.095, 0.0, 0.5, 4.0, 0.0, 0.0,\n'
    '                                           AJ_GW_ENT50[s]/0.3)   # thru-2049 scoring basis')

# ---- F8 (Fig 1a/b): marker + x-label ------------------------------------------------
rep("atb-a6b-f8",
    "            t50, d_aj = TARGET[tech][scen][-1], AJ_GW_POST[scen]",
    "            t50, d_aj = TARGET[tech][scen][-1], AJ_GW_ENT50[scen]   # thru-2049 scoring basis")
rep("atb-a6b-f8",
    '                ax.set_xlabel("cumulative new build by 2050 (GW)")',
    '                ax.set_xlabel("post-2030 build completed through 2049 (GW; prices 2050)")')

# ---- captions -----------------------------------------------------------------------
rep_ws("atb-20b-f6_caption",
    "Cumulative new build required by 2050 (GW, log color scale) to reach each ATB scenario's "
    "2050 cost,",
    "Post-2030 build completed through 2049 (GW, log color scale — the stock that prices 2050\n"
    "under the engine's one-year lag) required to reach each ATB scenario's 2050 cost,")
rep_ws("atb-20b-f6_caption",
    "the orange contour marks the Abou-Jaoude deployment paired with that scenario",
    "the orange contour marks the paired Abou-Jaoude program on the same through-2049 basis")
rep_ws("atb-21b-f7_caption",
    "the dashed line is the paired Abou-Jaoude program,",
    "the dashed line is the paired Abou-Jaoude program (through-2049 basis),")
rep_ws("atb-a6b-f8_caption",
    "For each amount of cumulative new build by 2050 (x, log scale):",
    "For each amount of post-2030 build completed through 2049 (x, log scale — the stock that\n"
    "prices 2050):")
rep_ws("atb-a6b-f8_caption",
    "The black dot is the ATB 2050 target at its paired Abou-Jaoude deployment (dotted "
    "crosshairs).",
    "The black dot is the ATB 2050 target at its paired Abou-Jaoude deployment on the same\n"
    "through-2049 basis (dotted crosshairs; the quoted by-2050 program totals remain\n"
    "12/33/199 GW).")
rep_ws("atb-a6b-f9_caption",
    "max(OCC(2050) − target, 0) at the paired deployment —",
    "max(OCC(2050) − target, 0) at the paired deployment (the AJ annual path run through the\n"
    "full engine, which applies the one-year lag itself) —")

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"applied {n} edits -> {NB.name}")
