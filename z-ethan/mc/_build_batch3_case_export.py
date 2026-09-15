"""Compose batch3_case_export.ipynb — run infrastructure for batch 3 (2026-09-15: 151 runs =
72 map anchors p25/p75 in six market worlds + 30 map anchors p05–p95 in the CO2-cap world
+ 18 flat-50% credit runs in the high-gas-price world + 24 flat-50% credit runs in the
CO2-cap world + 6 flat-50% credit runs at p05 in the high-RE-cost world + 1 re-run of the
unreturned batch-2 run; review round 1 applied; registered in
z-ethan/rate_design/methods.md v2.6 BEFORE emission).

Every column is a TRANSCRIPTION of an existing, already-run column (ratedesign / smr100 /
batch2 casefiles) plus the world's switch overrides. No nuclear input file is written; no MC
re-run is needed (the notebook is pandas-only and runs on any python). The step-4 switch set
is copied verbatim from `_build_step4_case_export.py` and asserted identical to the emitted
step-4 casefile. It emits:

  * cases_nuclearlearning_batch3.csv — 151 columns (A1 by world, A2, B1, B2, B3, R);
  * exports/batch3/b3_run_spec.csv     — the 151 runs (block, world, schedule, percentile,
                                         draw index, source casefile/column, form);
  * exports/batch3/b3_predictions.csv  — the registered block-B predictions (v2.6 rule; the
                                         inputs that exist today, the rest 'from block A');
  * exports/batch3/batch3_metadata.json;
  * a QA suite (B1–B9) asserting the transcription: resolved-switch parity against the source
    column equals exactly the world's override set; Choices validation; pointer-file
    existence; draw identity with the frozen registrations; frozen-artifact byte identity.

Build with:   python _build_batch3_case_export.py    (json-only; any python)
Execute with: the playground-env kernel (JUPYTER_PATH recipe), or any python with pandas.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = json.loads((HERE / "smr100_case_export.ipynb").read_text(encoding="utf-8"))
OUT_PATH = HERE / "batch3_case_export.ipynb"

# The step-4 switch set, copied verbatim from _build_step4_case_export.py (asserted there
# against cases.csv Choices and the input tree; re-asserted below against the emitted
# step-4 casefile so the two definitions cannot drift).
STEP4_SRC = (HERE / "_build_step4_case_export.py").read_text(encoding="utf-8")
_s = STEP4_SRC.index("SENS = {")
_e = STEP4_SRC.index("SENS_ORDER = ")
SENS_BLOCK = STEP4_SRC[_s:_e]
assert '"gashi":    {"ngscen": "AEO_2026_LOG"}' in SENS_BLOCK


def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": text.splitlines(keepends=True)}


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


cells = []

cells.append(md("""\
# Batch 3: run infrastructure for the 151 launchable runs

**What this notebook does.** Batch 3 is pre-registered (`z-ethan/rate_design/methods.md`
v2.6, 2026-09-15). Every column is a transcription of an existing, already-run column plus
one world's switch overrides; the notebook makes no selection of its own. Blocks:

1. **A1 — map anchors, six market worlds (72, mandate ON, learning OFF):** the p25/p75
   anchors of the six schedules (`smr100_{ab}_{p25,p75}` in `cases_nuclearlearning_ratedesign.csv`)
   copied into `gaslo`, `gashi`, `demhi`, `relo`, `rehi`, `translim` with the step-4 switch set.
   Together with the step-4 p05/p50/p95 copies these give every world the same eleven-anchor
   ladder the reference map is read at.
2. **A2 — map anchors, CO2-cap world (30, mandate ON, learning OFF):** all five percentile
   anchors copied into a seventh world: the Standard Scenarios 2025 95%-by-2050 national CO2
   cap (`GSw_AnnualCap = 1`, `GSw_AnnualCapScen = start2027_95pct2050`, matching `distpvscen`).
3. **B1 — flat 50% credit, high-gas-price world (18, fbC):** `bx_{ab}_{p05,p25,p50}_f50` from
   batch 2, copied with `ngscen = AEO_2026_LOG`. The only step-4 world whose 2031 exact rate
   reaches 0.50.
4. **B2 — flat 50% credit, CO2-cap world (24, fbC):** `bx_{ab}_{p05,p25,p50,p75}_f50` copied
   with the CO2-cap switch set.
5. **B3 — flat 50% credit, high-RE-cost world (6, fbC):** `bx_{ab}_p05_f50` copied with the
   `rehi` switch set; the second world whose 2031 exact rate reaches 0.50 (iaea 0.492, mck
   0.509 at p05; review round 1).
6. **R — re-run (1):** `bm_cop28_d9396_e2`, the batch-2 run NREL did not return, copied verbatim
   under its own name.

No new nuclear input file is written: every pointer (plantchar, financials, construction
times, foreign experience, incentives) names a file that already exists and is SHA-guarded.
The run ceiling is 200 (Ethan, 2026-09-15); 49 slots stay in reserve (nominal: nothing marks them).
"""))

cells.append(code("""\
import hashlib, json, re
from pathlib import Path
import numpy as np
import pandas as pd

NB_DIR = Path.cwd() if (Path.cwd() / "smr100_case_export.ipynb").exists() else Path(__file__).resolve().parent
REPO_ROOT = NB_DIR.parents[1]
assert (REPO_ROOT / "cases.csv").exists(), REPO_ROOT
EXPORTS = NB_DIR / "exports" / "batch3"
EXPORTS.mkdir(parents=True, exist_ok=True)
PC_DIR = REPO_ROOT / "inputs" / "plant_characteristics"
FIN_DIR = REPO_ROOT / "inputs" / "financials"
NL_DIR = REPO_ROOT / "inputs" / "nuclear_learning"
RD2_EXPORTS = REPO_ROOT / "z-ethan" / "rate_design2" / "exports"
SMR100_EXPORTS = NB_DIR / "exports" / "smr100"

def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_cases(name):
    return pd.read_csv(REPO_ROOT / name, index_col=0, dtype=str).fillna("")

CF = {
    "ratedesign": load_cases("cases_nuclearlearning_ratedesign.csv"),
    "smr100":     load_cases("cases_nuclearlearning_smr100.csv"),
    "batch2":     load_cases("cases_nuclearlearning_batch2.csv"),
    "step4":      load_cases("cases_nuclearlearning_step4.csv"),
}
cases_master = pd.read_csv(REPO_ROOT / "cases.csv", index_col=0, dtype=str).fillna("")
MASTER_DEFAULT = cases_master["Default Value"].to_dict()
AB = ["eia", "aj", "iaea", "mck", "cop28", "eo"]
SCEN_TOKEN = {"eia": "eia_aeo_high", "aj": "abou_jaoude", "iaea": "iaea_high",
              "mck": "mckinsey", "cop28": "cop28", "eo": "eo2025"}
SCHED_NAME = {"eia": "EIA 2026 AEO high", "aj": "Abou-Jaoude mod", "iaea": "IAEA high",
              "mck": "McKinsey GEP 2025", "cop28": "COP28 tripling pledge", "eo": "2025 EO"}
print("loaded 4 source casefiles:", {k: v.shape[1] - 1 for k, v in CF.items()})
"""))

cells.append(md("""\
## Frozen-artifact guard

The four source casefiles, the frozen draw registrations, the batch-2 spec, `cases.csv`,
`futurefiles.csv`, and every input file a new column points at are snapshotted here and
re-verified byte-for-byte in QA-B8. This notebook writes only the batch-3 casefile and its
exports.
"""))
cells.append(code("""\
m50 = pd.read_csv(RD2_EXPORTS / "m50_b2_run_spec.csv")
sel5 = pd.read_csv(SMR100_EXPORTS / "selected_draws.csv")               # p05/p50/p95 × 6
sel2575 = pd.read_csv(SMR100_EXPORTS / "selected_draws_p25p75.csv")     # p25/p75 × 6
NAME2AB = {v: k for k, v in SCHED_NAME.items()}
DRAW = {}
for _, r in pd.concat([sel5, sel2575]).iterrows():
    DRAW[(NAME2AB[r["schedule"]], r["percentile"])] = int(r["draw_index"])
assert len(DRAW) == 30
GUARDED = [REPO_ROOT / n for n in ("cases_nuclearlearning_ratedesign.csv", "cases_nuclearlearning_smr100.csv",
                                   "cases_nuclearlearning_batch2.csv", "cases_nuclearlearning_step4.csv",
                                   "cases_nuclearlearning_ratedesign2.csv", "cases.csv")] + [
    REPO_ROOT / "inputs" / "userinput" / "futurefiles.csv",
    RD2_EXPORTS / "m50_b2_run_spec.csv", RD2_EXPORTS / "m51_b2_offers.csv",
    SMR100_EXPORTS / "selected_draws.csv", SMR100_EXPORTS / "selected_draws_p25p75.csv",
    REPO_ROOT / "inputs" / "emission_constraints" / "co2_cap.csv",
]
for p in GUARDED:
    assert p.exists(), p
GUARD_SHA = {p: _sha(p) for p in GUARDED}
print(f"snapshotted {len(GUARD_SHA)} frozen artifacts; pointer files are added to the guard as they are resolved")
"""))

cells.append(md("""\
## The worlds

The six step-4 switch sets are the ones `_build_step4_case_export.py` defines (copied at build
time and asserted identical to the emitted step-4 casefile). The seventh world is the
Standard Scenarios 2025 `Mid_Case_95by2050` switch set: a CO2-only national cap on the
`start2027_95pct2050` path (95% below 2005 by 2050) plus its distributed-PV scenario, nothing
else. Ethan's ruling (2026-09-15, after review round 1): this path is slack against modeled
base emissions in 2032–2035 and binds after 2038; that shape is the registered expectation
(the window's requirement barely moves, the post-window requirement falls), and it is the
scenario readers recognize. The steeper 95%-by-2035 path was considered and rejected as
implausible.
"""))
cells.append(code(SENS_BLOCK + """\
SENS["co2cap"] = {"GSw_AnnualCap": "1", "GSw_AnnualCapScen": "start2027_95pct2050",
                  "distpvscen": "stscen2023_mid_case_95_by_2050"}
WORLD_ORDER = ["gaslo", "gashi", "demhi", "relo", "rehi", "translim", "co2cap"]
WORLD_LABEL = {"gaslo": "low gas price (high oil and gas supply)", "gashi": "high gas price (low supply)",
               "demhi": "high demand", "relo": "low RE and storage cost", "rehi": "high RE and storage cost",
               "translim": "constrained transmission", "co2cap": "95%-by-2050 national CO2 cap"}
SENS_SWITCH_ROWS = ["ngscen", "GSw_LoadProfiles", "plantchar_upv", "plantchar_onswind",
                    "plantchar_ofswind", "plantchar_battery", "plantchar_csp",
                    "plantchar_geo", "plantchar_hydro", "geodiscov", "distpvscen",
                    "GSw_TransRestrict", "GSw_TransInvMaxLongTerm",
                    "GSw_AnnualCap", "GSw_AnnualCapScen"]
assert {k for ov in SENS.values() for k in ov} <= set(SENS_SWITCH_ROWS)

# (a) the six step-4 sets equal what the emitted step-4 casefile carries, column by column
s4 = CF["step4"]
for w in WORLD_ORDER[:-1]:
    for col in [c for c in s4.columns if c.endswith("_" + w)]:
        got = {row: s4.loc[row, col] for row in s4.index if s4.loc[row, col] != "" and row in SENS_SWITCH_ROWS}
        assert got == SENS[w], (col, got, SENS[w])
# (b) the CO2-cap set: scenario present, binding below the default path, distpv dir present,
#     switch choices valid, and identical to the Standard Scenarios Mid_Case_95by2050 column
cap = pd.read_csv(REPO_ROOT / "inputs" / "emission_constraints" / "co2_cap.csv").set_index("t")
assert "start2027_95pct2050" in cap.index
# Registered expectation (Ethan, 2026-09-15): against MODELED base emissions (process CO2,
# test1_smr100_aj_p50) this cap is slack in 2032-2035, marginal at 2031 and 2038, and binds
# after 2038 -- the window's requirement should barely move and the post-window (Table 2
# never-under) requirement should fall. The asserts pin that shape so a silent edit of the
# cap file cannot change the reading.
BASE_PROCESS_CO2_GT = {"2031": 1.028, "2032": 0.707, "2035": 0.684, "2038": 0.695, "2041": 0.712, "2050": 0.826}
_cap = {y: float(cap.loc["start2027_95pct2050", y]) / 1e9 for y in BASE_PROCESS_CO2_GT}
assert _cap["2032"] > BASE_PROCESS_CO2_GT["2032"] and _cap["2035"] > BASE_PROCESS_CO2_GT["2035"]   # slack mid-window
assert 0.95 < _cap["2031"] / BASE_PROCESS_CO2_GT["2031"] < 1.0 and 0.95 < _cap["2038"] / BASE_PROCESS_CO2_GT["2038"] < 1.0
assert _cap["2041"] < 0.8 * BASE_PROCESS_CO2_GT["2041"] and _cap["2050"] < 0.2 * BASE_PROCESS_CO2_GT["2050"]
assert (REPO_ROOT / "inputs" / "dgen_model_inputs" / SENS["co2cap"]["distpvscen"]).is_dir()
_std = pd.read_csv(REPO_ROOT / "cases_standardscenarios.csv", index_col=0, dtype=str).fillna("")
_std95 = {k: v for k, v in _std["Mid_Case_95by2050"].items() if v != ""}
assert _std95 == SENS["co2cap"], _std95
# (c) referenced-input existence for the six step-4 sets (re-run of the step-4 asserts)
for scen in ("AEO_2026_HOG", "AEO_2026_LOG"):
    for stem in ("alpha", "ng", "ng_demand", "ng_tot_demand"):
        assert (REPO_ROOT / "inputs" / "fuelprices" / f"{stem}_{scen}.csv").exists(), (stem, scen)
for ov in SENS.values():
    for row, val in ov.items():
        if row.startswith("plantchar_"):
            assert (PC_DIR / f"{val}.csv").exists(), val
        if row == "distpvscen":
            assert (REPO_ROOT / "inputs" / "dgen_model_inputs" / val).is_dir(), val
assert "demand_EER2025_100by2050.h5" in (REPO_ROOT / "inputs" / "remote_files.csv").read_text()
print(f"7 worlds defined; the six step-4 sets equal the emitted step-4 casefile; the CO2-cap set equals "
      "the Standard Scenarios Mid_Case_95by2050 column; every referenced input exists")
"""))

cells.append(md("""\
## The run spec

One row per run: block, world, schedule, percentile, draw index, the source casefile and
column, form and convention. The draw index of every anchor is read from the frozen smr100
registrations and asserted against the source column's file pointers; the flat-credit worlds
are the batch-2 `rd_` worlds, asserted against `m50`.
"""))
cells.append(code("""\
PCT5 = ["p05", "p25", "p50", "p75", "p95"]
rows = []
def add(run, block, world, ab, pct, src_file, src_col, form, conv, draw, note=""):
    rows.append(dict(run=run, block=block, world=world, ab=ab, pct=pct, source_casefile=src_file,
                     source_column=src_col, form=form, convention=conv, draw_index=draw,
                     schedule=SCHED_NAME[ab] if ab else "", scen_token=SCEN_TOKEN[ab] if ab else "", note=note))

# A1: p25/p75 anchors × six market worlds
for w in WORLD_ORDER[:-1]:
    for ab in AB:
        for pct in ("p25", "p75"):
            src = f"smr100_{ab}_{pct}"
            add(f"{src}_{w}", "A1", w, ab, pct, "cases_nuclearlearning_ratedesign.csv", src,
                "mandate", "map anchor (mandate ON, learning OFF)", DRAW[(ab, pct)])
# A2: all five anchors × the CO2-cap world
for ab in AB:
    for pct in PCT5:
        src = f"smr100_{ab}_{pct}"
        sf = "cases_nuclearlearning_ratedesign.csv" if pct in ("p25", "p75") else "cases_nuclearlearning_smr100.csv"
        add(f"{src}_co2cap", "A2", "co2cap", ab, pct, sf, src, "mandate",
            "map anchor (mandate ON, learning OFF)", DRAW[(ab, pct)])
# B1: flat 50% credit × high-gas-price world, p05/p25/p50
M50 = m50.set_index("run")
for ab in AB:
    for pct in ("p05", "p25", "p50"):
        src = f"bx_{ab}_{pct}_f50"
        add(f"{src}_gashi", "B1", "gashi", ab, pct, "cases_nuclearlearning_batch2.csv", src, "flat50", "fbC",
            int(M50.loc[src, "draw_index"]))
# B2: flat 50% credit × CO2-cap world, p05/p25/p50/p75
for ab in AB:
    for pct in ("p05", "p25", "p50", "p75"):
        src = f"bx_{ab}_{pct}_f50"
        add(f"{src}_co2cap", "B2", "co2cap", ab, pct, "cases_nuclearlearning_batch2.csv", src, "flat50", "fbC",
            int(M50.loc[src, "draw_index"]))
# B3: flat 50% credit × high-RE-cost world, p05
for ab in AB:
    src = f"bx_{ab}_p05_f50"
    add(f"{src}_rehi", "B3", "rehi", ab, "p05", "cases_nuclearlearning_batch2.csv", src, "flat50", "fbC",
        int(M50.loc[src, "draw_index"]))
# R: the unreturned batch-2 run, verbatim
add("bm_cop28_d9396_e2", "R", "base", "cop28", "q25 (batch-2 quantile-world tag, not a percentile anchor)", "cases_nuclearlearning_batch2.csv", "bm_cop28_d9396_e2",
    "map_plus_2e6", "fbC", int(M50.loc["bm_cop28_d9396_e2", "draw_index"]),
    note="batch-2 run not returned by NREL; re-submitted under its own name (KNOWN_MISSING in rate_design2_b2_checks)")

spec = pd.DataFrame(rows)
assert spec["run"].is_unique and len(spec) == 151
assert spec["block"].value_counts().to_dict() == {"A1": 72, "A2": 30, "B2": 24, "B1": 18, "B3": 6, "R": 1}
# every source column exists in its casefile; the flat-credit world draws equal the anchor draws
for _, r in spec.iterrows():
    assert r["source_column"] in CF[r["source_casefile"].split("_")[-1][:-4]].columns, r["run"]
    if r["block"] in ("B1", "B2", "B3"):
        assert r["draw_index"] == DRAW[(r["ab"], r["pct"])], r["run"]
        assert M50.loc[r["source_column"], "world_case"] == f"rd_{r['ab']}_d{r['draw_index']}", r["run"]
        assert M50.loc[r["source_column"], "form"] == "flat50"
# no name collision with any existing casefile column, except the deliberate re-run
_existing = set().union(*[set(df.columns) for df in CF.values()]) | set(load_cases("cases_nuclearlearning_ratedesign2.csv").columns)
_coll = set(spec["run"]) & _existing
assert _coll == {"bm_cop28_d9396_e2"}, _coll
spec.to_csv(EXPORTS / "b3_run_spec.csv", index=False)
print(f"spec: {len(spec)} runs; blocks {spec['block'].value_counts().to_dict()}; worlds {spec['world'].value_counts().to_dict()}")
"""))

cells.append(md("""\
## Export: the cases file

Row template = the 31 rows of the batch-2/ratedesign casefiles (their `Default Value` column)
plus the 15 world-switch rows (blank default: the root `cases.csv` default applies). Every
column is written **fully resolved on the 31 template rows**: the value the source run actually
resolved to (its cell, else its casefile's default, else `cases.csv`). The 15 world-switch
rows carry only the world's overrides; a blank there resolves to the root `cases.csv` default,
which is what every source run resolved to (no source casefile has those rows).
"""))
cells.append(code("""\
tmpl = CF["ratedesign"]
BASE_ROWS = list(tmpl.index)
assert len(BASE_ROWS) == 31 and BASE_ROWS[0] == "ignore"
ROWS = BASE_ROWS + SENS_SWITCH_ROWS
assert len(set(ROWS)) == len(ROWS) == 46

def resolved(df, col, row):
    v = df.loc[row, col] if row in df.index else ""
    if v == "":
        v = df.loc[row, "Default Value"] if row in df.index else ""
    if v == "":
        v = MASTER_DEFAULT.get(row, "")
    return v

cols = {}
for _, r in spec.iterrows():
    src_df = CF[r["source_casefile"].split("_")[-1][:-4]]
    c = {row: resolved(src_df, r["source_column"], row) for row in BASE_ROWS if row != "ignore"}
    c["ignore"] = ""
    c.update({row: "" for row in SENS_SWITCH_ROWS})       # blank = the root cases.csv default, as the source ran
    c.update(SENS.get(r["world"], {}))
    cols[r["run"]] = c

defaults = {row: tmpl.loc[row, "Default Value"] for row in BASE_ROWS} | {row: "" for row in SENS_SWITCH_ROWS}
cases_b3 = pd.DataFrame({"Default Value": defaults} | cols).reindex(ROWS)
cases_b3.index.name = ""
B3_CASES_PATH = REPO_ROOT / "cases_nuclearlearning_batch3.csv"
cases_b3.to_csv(B3_CASES_PATH)
print(f"wrote {B3_CASES_PATH.name}: {cases_b3.shape[0]} switch rows x {cases_b3.shape[1] - 1} run columns "
      f"(launch: python runreeds.py -b sensitivity_analysis2 -c nuclearlearning_batch3)")
cases_b3.iloc[:, :6]
"""))

cells.append(md("""\
## Registered predictions (block B)

The v2.6 rule on the exact chain: `r2031` (the world's exact 2031 required rate at the anchor;
eia reads 2038) and `x` (post-window excess = max exact rate after 2038 minus 0.51). Inputs
exist today for the high-gas-price world at p05 and p50 (`market_transfer/exports/v01`); the
p25 cells and every CO2-cap cell are scored on the block-A rates when the batch returns.
"""))
cells.append(code("""\
v01 = pd.read_csv(REPO_ROOT / "z-ethan" / "market_transfer" / "exports" / "v01_required_itc_perworld.csv")
v01 = v01[(~v01["case"].str.contains("large", na=False)) & v01["schedule"].notna()]
CAP, CUSH, W = 0.50, 0.01, 2038

def rule(r2031, x):
    if r2031 is None or x is None:
        return "from block A"
    if -0.05 < x <= 0.0:
        return "fuzzy"
    if x <= -0.05 and r2031 <= CAP + CUSH:
        return "full delivery"
    if x <= -0.05 and r2031 <= 0.65:
        return "late start, recovers"
    return "shortfall"

pred_rows = []
for _, r in spec[spec["block"].isin(["B1", "B2", "B3"])].iterrows():
    sub = v01[(v01["world"] == r["world"]) & (v01["schedule"] == r["ab"]) & (v01["pct"] == r["pct"])]
    r2031 = x = None
    src = "block A (this batch)"
    if len(sub):
        rate = sub[sub["status"] == "rate"]
        start_year = 2038 if r["ab"] == "eia" else 2031
        s = rate[rate["t"] == start_year]["i_model_headline"]
        r2031 = float(s.iloc[0]) if len(s) else 0.0          # convention: slack at the start year -> r_start = 0
        post = rate[rate["t"] > W]["i_model_headline"]
        x = (float(post.max()) if len(post) else 0.0) - (CAP + CUSH)   # convention: all post-window years slack -> x = -0.51
        src = "step 4 exact chain (v01)"
    pred_rows.append(dict(run=r["run"], block=r["block"], world=r["world"], ab=r["ab"], pct=r["pct"],
                          r_start=None if r2031 is None else round(r2031, 3), excess_post=None if x is None else round(x, 3),
                          inputs=src, prediction=rule(r2031, x)))
pred = pd.DataFrame(pred_rows)
pred.to_csv(EXPORTS / "b3_predictions.csv", index=False)
assert len(pred) == 48
print(pred["prediction"].value_counts().to_dict())
pred[pred["inputs"].str.startswith("step 4")]
"""))

cells.append(md("""\
## QA suite

B1 order/count/rows; B2 resolved-switch parity — each column differs from its source column
in exactly the world's override set (and the re-run in nothing); B3 mandate/credit switch
pattern per block; B4 pointer files exist (and are added to the frozen guard); B5 draw
identity — the pointer names carry the registered anchor (A) or the registered `rd_` world
(B) and the plantchar file's cost path equals the anchor's for the world copies; B6
incentives: the reused batch-2 `flat50` files are 0.50 on the ten model years; B7 `cases.csv`
Choices validation; B8 frozen artifacts byte-identical; B9 world-switch fingerprint per
world.
"""))
cells.append(code("""\
# QA-B1 -- transcription: names, order (spec), 145 columns, 46 rows, standard horizon.
_back = pd.read_csv(B3_CASES_PATH, index_col=0, dtype=str).fillna("")
assert list(_back.columns) == ["Default Value"] + list(spec["run"])
assert list(_back.index) == ROWS
_runcols = list(spec["run"])
assert (_back.loc["endyear", _runcols] == "2050").all() and (_back.loc["timetype", _runcols] == "seq").all()
assert (_back.loc["yearset", _runcols] == tmpl.loc["yearset", "Default Value"]).all()
print(f"QA-B1 PASSED: {len(_runcols)} columns in spec order; {len(ROWS)} rows; all standard-horizon")
"""))
cells.append(code("""\
# QA-B2 -- RESOLVED-switch parity: column vs its source column (cell -> casefile default ->
# cases.csv default) differs in exactly the world's override rows (those whose override value
# differs from what the source resolved to); the re-run differs in nothing.
def _res_b3(col, row):
    return resolved(_back, col, row)
for _, r in spec.iterrows():
    src_df = CF[r["source_casefile"].split("_")[-1][:-4]]
    diff = {row for row in ROWS if row != "ignore" and _res_b3(r["run"], row) != resolved(src_df, r["source_column"], row)}
    want = {row for row, val in SENS.get(r["world"], {}).items() if val != resolved(src_df, r["source_column"], row)}
    assert diff == want, (r["run"], diff ^ want)
    for row, val in SENS.get(r["world"], {}).items():
        assert _res_b3(r["run"], row) == val, (r["run"], row)
print("QA-B2 PASSED: every column equals its source column on every resolved switch except the world's overrides; "
      "the re-run is byte-equivalent to its batch-2 column")
"""))
cells.append(code("""\
# QA-B3 -- switch pattern per block: A = mandate ON (schedule token, smr), learning OFF,
# no-nuclear-ITC baseline, phaseout exempt as the anchor ran (0); B = mandate OFF, learning ON,
# the batch-2 flat50 incentives file, phaseout exempt 1, rd_ pointers + foreign tag.
for _, r in spec.iterrows():
    run = r["run"]
    if r["block"] in ("A1", "A2"):
        assert _res_b3(run, "GSw_NuclearCapMandate") == "1" and _res_b3(run, "GSw_NuclearLearning") == "0", run
        assert _res_b3(run, "GSw_NuclearCapMandateScen") == r["scen_token"] + "_smr", run
        assert _res_b3(run, "GSw_NuclearCapMandateTechScen") == "smr", run
        assert _res_b3(run, "incentives_suffix") == "obbba_nonuclearitc", run
        assert _res_b3(run, "GSw_TCPhaseout_NuclearExempt") == "0", run
        assert _res_b3(run, "financials_tech_suffix") == f"mc_{r['source_column']}", run
    elif r["block"] in ("B1", "B2", "B3"):
        assert _res_b3(run, "GSw_NuclearCapMandate") == "0" and _res_b3(run, "GSw_NuclearLearning") == "1", run
        assert _res_b3(run, "incentives_suffix") == f"obbba_rd_{r['source_column']}", run
        assert _res_b3(run, "GSw_TCPhaseout_NuclearExempt") == "1", run
        wc = f"rd_{r['ab']}_d{r['draw_index']}"
        assert _res_b3(run, "financials_tech_suffix") == f"mc_{wc}" and _res_b3(run, "GSw_NuclearLearning_ForeignScen") == wc, run
        assert _res_b3(run, "GSw_NuclearCapMandateScen") == r["scen_token"] + "_smr", run
    else:
        assert run == "bm_cop28_d9396_e2" and _res_b3(run, "incentives_suffix") == "obbba_rd_bm_cop28_d9396_e2"
print("QA-B3 PASSED: block A columns are mandate ON / learning OFF anchors; block B columns are fbC flat-credit runs")
"""))
cells.append(code("""\
# QA-B4 -- every pointer names an existing file; add them to the frozen guard.
POINTER_FILES = {}
for run in _runcols:
    fs = [PC_DIR / f"{_res_b3(run, 'plantchar_nuclear')}.csv", PC_DIR / f"{_res_b3(run, 'plantchar_nuclear_smr')}.csv",
          FIN_DIR / f"financials_tech_{_res_b3(run, 'financials_tech_suffix')}.csv",
          FIN_DIR / f"construction_times_{_res_b3(run, 'construction_times_suffix')}.csv",
          FIN_DIR / f"incentives_{_res_b3(run, 'incentives_suffix')}.csv",
          FIN_DIR / f"construction_schedules_{_res_b3(run, 'construction_schedules_suffix')}.csv"]
    if _res_b3(run, "GSw_NuclearLearning") == "1":
        fs.append(NL_DIR / f"foreign_experience_{_res_b3(run, 'GSw_NuclearLearning_ForeignScen')}.csv")
    for p in fs:
        assert p.exists(), (run, p.name)
        POINTER_FILES[p] = _sha(p)
GUARD_SHA.update(POINTER_FILES)
print(f"QA-B4 PASSED: {len(POINTER_FILES)} distinct pointer files exist (all pre-existing; none written here)")
"""))
cells.append(code("""\
# QA-B5 -- draw identity: A pointers name the registered anchor; B pointers name the registered
# rd_ world, whose smr plantchar cost path equals the anchor's file for t >= 2031 (the batch-2
# QA-R9 identity, re-asserted so the credit run and its anchor are the same cost world).
for _, r in spec.iterrows():
    run = r["run"]
    if r["block"] in ("A1", "A2"):
        assert _res_b3(run, "plantchar_nuclear_smr") == f"nuclear-smr_mc_smr100_{r['ab']}_{r['pct']}", run
    elif r["block"] in ("B1", "B2", "B3"):
        wc = f"rd_{r['ab']}_d{r['draw_index']}"
        assert _res_b3(run, "plantchar_nuclear_smr") == f"nuclear-smr_mc_{wc}", run
        a = pd.read_csv(PC_DIR / f"nuclear-smr_mc_{wc}.csv").set_index("t")["capcost"]
        b = pd.read_csv(PC_DIR / f"nuclear-smr_mc_smr100_{r['ab']}_{r['pct']}.csv").set_index("t")["capcost"]
        assert (a.loc[a.index >= 2031] == b.loc[b.index >= 2031]).all(), run
print("QA-B5 PASSED: every A column points at its registered anchor; every B column's rd_ world carries the anchor's cost path")
"""))
cells.append(code("""\
# QA-B6 -- the reused flat50 incentives files: one Nuclear-SMR row per model year 2031-2050 at
# itc_frac 0.500, baseline rows byte-identical to the no-nuclear-ITC baseline minus its NUCLEAR rows.
MODEL_YEARS = [2031, 2032, 2033, 2034, 2035, 2038, 2041, 2044, 2047, 2050]
base_lines = [ln for ln in (FIN_DIR / "incentives_obbba_nonuclearitc.csv").read_text(encoding="utf-8").splitlines() if ln.strip()]
kept = [ln for ln in base_lines if not ln.startswith("NUCLEAR,")]
for _, r in spec[spec["block"].isin(["B1", "B2", "B3"])].iterrows():
    lines = [ln for ln in (FIN_DIR / f"incentives_{_res_b3(r['run'], 'incentives_suffix')}.csv").read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert [ln for ln in lines if not ln.startswith("Nuclear-SMR,")] == kept, r["run"]
    nuc = [ln.split(",") for ln in lines if ln.startswith("Nuclear-SMR,")]
    assert sorted(int(p[2]) for p in nuc) == MODEL_YEARS and {float(p[9]) for p in nuc} == {0.5}, r["run"]
print("QA-B6 PASSED: the 24 reused flat50 incentives files offer 0.50 on exactly the ten model years")
"""))
cells.append(code("""\
# QA-B7 -- cases.csv Choices validation (ReEDS's unanchored re.match semantics) on every cell.
for switch in _back.index:
    if switch == "ignore":
        continue
    assert switch in cases_master.index, f"unknown switch {switch}"
    choices = str(cases_master.loc[switch, "Choices"])
    for col in _back.columns:
        val = _back.loc[switch, col]
        if val == "" or choices in ("N/A", "nan", "None", ""):
            continue
        if choices.lower() in ("int", "integer"):
            int(val); continue
        if choices.lower() in ("float", "numeric", "number", "num"):
            float(val); continue
        i_choices = [str(j).strip() for j in np.ravel([c.split(",") for c in choices.split(";")]).tolist()]
        assert any(re.match(ch, str(val)) for ch in i_choices), (switch, val, choices)
print("QA-B7 PASSED: the casefile passes ReEDS's own Choices validation (prefix re.match)")
"""))
cells.append(code("""\
# QA-B8 -- frozen artifacts (source casefiles, registrations, cases.csv, futurefiles.csv,
# co2_cap.csv, every pointer file) byte-identical after the write.
for p, sha0 in GUARD_SHA.items():
    assert _sha(p) == sha0, f"frozen artifact changed: {p}"
print(f"QA-B8 PASSED: {len(GUARD_SHA)} frozen artifacts byte-identical")
"""))
cells.append(code("""\
# QA-B9 -- world fingerprint: within a world every column carries the identical override set;
# across worlds the sets differ; the base re-run carries none.
fp = {}
for _, r in spec.iterrows():
    got = {row: _back.loc[row, r["run"]] for row in SENS_SWITCH_ROWS if _back.loc[row, r["run"]] != ""}
    fp.setdefault(r["world"], set()).add(json.dumps(got, sort_keys=True))
assert all(len(v) == 1 for v in fp.values()), {k: len(v) for k, v in fp.items()}
assert fp["base"] == {"{}"}
assert len({next(iter(v)) for k, v in fp.items() if k != "base"}) == 7   # rehi carries A1 and B3 with one set
print("QA-B9 PASSED: one override set per world (7 distinct), none on the re-run")
"""))

cells.append(md("## Run metadata"))
cells.append(code("""\
import subprocess as _sp
from datetime import datetime, timezone
try:
    _git = _sp.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip()
except Exception:
    _git = "unavailable"
meta = {
    "notebook": "batch3_case_export.ipynb",
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "fork_git_head": _git,
    "built_by": "_build_batch3_case_export.py (pure transcription; no MC re-run; no input file written)",
    "registration": "z-ethan/rate_design/methods.md v2.6 (2026-09-15)",
    "design": {"blocks": spec["block"].value_counts().to_dict(), "worlds": spec["world"].value_counts().to_dict(),
               "batch_name": "sensitivity_analysis2", "ceiling": 200, "reserve_nominal": 200 - len(spec), "world_switches": SENS, "world_labels": WORLD_LABEL},
    "runs": {r["run"]: {k: (int(v) if k == "draw_index" else v) for k, v in r.items() if k != "run"} for _, r in spec.iterrows()},
    "reeds_files": {"cases_file": B3_CASES_PATH.name, "new_input_files": [],
                    "pointer_files": sorted(p.name for p in POINTER_FILES)},
    "exports": {p.name: _sha(p)[:16] for p in sorted(EXPORTS.glob("*.csv"))},
}
with open(EXPORTS / "batch3_metadata.json", "w") as f:
    json.dump(meta, f, indent=2)
print(json.dumps({k: meta[k] for k in ("notebook", "generated_utc", "fork_git_head")}, indent=2))
"""))

cells.append(md("""\
## Closing note

**One case file, 151 launchable runs**: `cases_nuclearlearning_batch3.csv` (launch:
`python runreeds.py -b sensitivity_analysis2 -c nuclearlearning_batch3`). Column order: A1 by world
(gaslo, gashi, demhi, relo, rehi, translim; within a world by schedule then p25, p75), A2
(co2cap; by schedule then p05–p95), B1 (gashi flat50 by schedule then p05, p25, p50), B2
(co2cap flat50 by schedule then p05–p75), B3 (rehi flat50 p05 by schedule), R.

**Batch name.** `sensitivity_analysis2` (Ethan, 2026-09-15): launch with
`python runreeds.py -b sensitivity_analysis2 -c nuclearlearning_batch3`; h5 stems are
`sensitivity_analysis2_{case}_outputs.h5`.

**The re-run.** `bm_cop28_d9396_e2` returns as `sensitivity_analysis2_bm_cop28_d9396_e2_outputs.h5`
under the archive's `{batch}_{case}` convention, but the batch-2 chain looks for the `batch2_` stem
(`rate_design2_b2_checks/_consolidate_and_verify.py`, `_build_notebook.py`). The batch-3
consolidator must copy that one member into the archive as `batch2_bm_cop28_d9396_e2_outputs.h5`
(recording the rename in its manifest) before `KNOWN_MISSING` is cleared and the batch-2 chain
re-runs. Tell NREL the batch name to pass with `-b`.

**Chains.** No existing chain ingests block A as is: `market_transfer/_build_notebook.py` fixes
the world list, the percentile list (p05/p50/p95), the two casefiles it reads, and the h5
prefixes; the duals producers (`step3_checks`, `step4_checks`) read fixed case lists. A
`batch3_checks` suite (duals per year for the 102 anchors, the batch-2 check pattern for the
48 credit runs) and `market_transfer/methods.md` v2.0 are prerequisites of any block-A reading.

No input file ships with the batch beyond the casefile: every pointer is a pre-existing,
SHA-guarded file. Heads-up lines for NREL: the `demhi` columns fetch
`demand_EER2025_100by2050.h5` from Zenodo (as in step 4); the `co2cap` columns are the first
runs in this project with `GSw_AnnualCap = 1` (the Standard Scenarios `Mid_Case_95by2050` cap). Nothing is drafted before the batch returns;
the v2.6 gates and the block-B prediction record are adjudicated then.
"""))

nb = {"cells": cells, "metadata": SRC["metadata"], "nbformat": SRC["nbformat"], "nbformat_minor": SRC["nbformat_minor"]}
OUT_PATH.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print(f"wrote {OUT_PATH.name}: {len(cells)} cells ({sum(c['cell_type'] == 'code' for c in cells)} code)")
