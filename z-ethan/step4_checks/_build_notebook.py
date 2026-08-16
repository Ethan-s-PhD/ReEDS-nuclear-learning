"""Generate step4_output_checks.ipynb. Edit cell sources here, re-run to regenerate.

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


md("""# Step 4 output checks — 120 sensitivity and large100 percentile runs

This notebook tests the 120 Step 4 run outputs from NREL.
The output files are in `D:\\ReEDS files\\nuclear-learning\\step4 runs`.
The run matrix is `cases_nuclearlearning_step4.csv`.
The matrix has 108 market-sensitivity cases and 12 large100 percentile cases.

The 108 sensitivity cases are file-pointer copies of the 18 Step 3 base cases.
Their nuclear inputs are byte-identical to the base case.
Only the market switches differ: `gaslo`, `gashi`, `demhi`, `relo`, `rehi`, `translim`.
Note: `gaslo` = `AEO_2026_HOG` = high oil and gas supply = **low** gas price.
The 12 large100 percentile cases carry new nuclear input files.

The notebook makes sure that:

- The file set is complete and the solves are clean (phase A).
- Each sensitivity run kept the base-case nuclear inputs and applied its market switch (phase B).
- The 12 large100 percentile runs used the correct new input data (phase B).
- The mandate and the dual prices operate correctly in all 120 runs (phase C).
- The results move in the expected direction against the Step 3 base cases (phase D).
- The load data is not corrupted (phase E).
- The results show no unexpected values (phase F).

Each test writes one row to a check registry.
The last cell writes the registry to `exports/checks_summary.csv`.
The last cell also writes the report `step4_check_results.md`.

Run this notebook on the **playground-env** kernel.
This notebook only reads the files on drive D. It does not change them.
The notebook opens 120 files on an external drive. A full run takes a long time.""")

code("""import hashlib
import json
from datetime import date
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

pd.set_option("display.width", 200)

HERE = Path.cwd()
assert HERE.name == "step4_checks", f"run from z-ethan/step4_checks/, not {HERE}"
REPO = HERE.parents[1]
EXPORTS = HERE / "exports"
EXPORTS.mkdir(exist_ok=True)

H5_DIR = Path("D:/ReEDS files/nuclear-learning/step4 runs")
BASE_DIR = Path("D:/ReEDS files/nuclear-learning/smr100 first run")
STEP3_EXPORTS = REPO / "z-ethan" / "step3_checks" / "exports"

# ---- case matrices ----------------------------------------------------------------
cases4 = pd.read_csv(REPO / "cases_nuclearlearning_step4.csv", index_col=0)
CASES = [c for c in cases4.columns if c != "Default Value"]
assert len(CASES) == 120, len(CASES)

cases3 = pd.read_csv(REPO / "cases_nuclearlearning_smr100.csv", index_col=0)
CASES3 = [c for c in cases3.columns if c != "Default Value"]
assert len(CASES3) == 25, len(CASES3)

def sw(case, name, csv=None):
    \"\"\"Read one switch value for one case. An empty cell uses the default value.\"\"\"
    src = cases4 if csv is None else csv
    if case in cases3.columns and csv is None:
        src = cases3
    v = src.loc[name, case]
    if pd.isna(v) or str(v).strip() == "":
        v = src.loc[name, "Default Value"]
    return str(v).strip()

SENS = ["gaslo", "gashi", "demhi", "relo", "rehi", "translim"]
SCHEDULES = ["eia", "aj", "iaea", "mck", "cop28", "eo"]

def parse_case(c):
    \"\"\"Split a case name into (family, schedule, percentile, sensitivity).\"\"\"
    fam = "large" if c.startswith("large100") else "smr"
    parts = c.split("_")
    sens = parts[3] if len(parts) > 3 else ""
    return fam, parts[1], parts[2], sens

META = {}
for c in CASES:
    fam, sched, pct, sens = parse_case(c)
    ts = sw(c, "GSw_NuclearCapMandateTechScen")
    META[c] = dict(
        fam=fam, sched=sched, pct=pct, sens=sens,
        scen=sw(c, "GSw_NuclearCapMandateScen"),
        mode=int(float(sw(c, "GSw_NuclearCapMandate"))),
        techscen=ts,
        mandated_tech={"smr": "nuclear-smr", "large": "nuclear"}[ts],
        pc={"nuclear": sw(c, "plantchar_nuclear"), "nuclear-smr": sw(c, "plantchar_nuclear_smr")},
        fin=sw(c, "financials_tech_suffix"),
        base="_".join(c.split("_")[:3]) if sens else None,
    )
SENS_CASES = [c for c in CASES if META[c]["sens"]]
LARGE_CASES = [c for c in CASES if META[c]["fam"] == "large"]
assert len(SENS_CASES) == 108 and len(LARGE_CASES) == 12
BASE_CASES = sorted({META[c]["base"] for c in SENS_CASES})
assert len(BASE_CASES) == 18 and all(b in CASES3 for b in BASE_CASES)
LARGE_P50 = [f"large100_{tok}_p50" for tok in SCHEDULES]   # Step 3 runs, reused
REF = "smr100_eia_p50"                                     # Step 3 reference case

# every step4 case reads from H5_DIR with the step4_ prefix;
# the Step 3 base cases read from BASE_DIR with the test1_ prefix.
H5 = {c: H5_DIR / f"step4_{c}_outputs.h5" for c in CASES}
for b in set(BASE_CASES) | set(LARGE_P50) | {REF}:
    H5[b] = BASE_DIR / f"test1_{b}_outputs.h5"

# 2022$ -> 2004$ (ReEDS-internal dollars). deflator.csv: Deflator(t) relative to 2004.
DEFL = pd.read_csv(REPO / "inputs" / "financials" / "deflator.csv")
DEFL.columns = ["t", "Deflator"]
DEFL = DEFL.set_index("t")["Deflator"]
D2022 = float(DEFL.loc[2022])
TO2024 = 1.0 / float(DEFL.loc[2024])

# ---- check registry -------------------------------------------------------------
CHECKS = []

def record(phase, name, status, detail=""):
    assert status in ("PASS", "FAIL", "BLOCKED", "INFO")
    CHECKS.append(dict(phase=phase, check=name, status=status, detail=str(detail)))
    print(f"[{status}] {phase} :: {name}" + (f" — {detail}" if detail else ""))

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
print(f"cases: {len(CASES)} ({len(SENS_CASES)} sensitivity + {len(LARGE_CASES)} large100 percentile)")
print(f"base cases referenced from Step 3: {len(BASE_CASES)} smr100 + {len(LARGE_P50)} large100 p50")
print(f"2022$->2004$ deflator: {D2022:.6f}; 2004$->2024$: {TO2024:.4f}")
""")

md("""## Phase A — File inventory and solve health

These tests make sure that the file set is complete and that each solve is clean.

- Test A1 makes sure that the folder has one output file for each of the 120 cases.
- Test A2 reads the extraction manifest and makes sure that the delivery was verified.
- Test A3 makes sure that all files have the same data keys.
- Test A4 makes sure that the solver residuals are small in each file.
- Test A5 makes sure that the model years are correct in each file.
- Test A6 makes sure that each run used the sequential solve mode.

Note: the model removes an all-zero dual parameter from the file.
Thus an absent dual key means a zero dual. It does not mean lost data.
A sensitivity can make a mandate slack in every year.
Then the file has no dual key at all. This is a finding, not a defect.""")

code("""# --- A1: file census -------------------------------------------------------------
missing = [c for c in CASES if not H5[c].exists()]
record("A", "one output file exists for each of the 120 cases",
       "PASS" if not missing else "FAIL",
       f"missing: {missing}" if missing else f"{len(CASES)} files in {H5_DIR}")
base_missing = [b for b in set(BASE_CASES) | set(LARGE_P50) | {REF} if not H5[b].exists()]
record("A", "the Step 3 base-case files are available for comparison",
       "PASS" if not base_missing else "FAIL",
       f"missing: {base_missing}" if base_missing else f"{len(set(BASE_CASES) | set(LARGE_P50) | {REF})} files in {BASE_DIR}")

all_files = sorted(p.name for p in H5_DIR.glob("*.h5"))
extra = [f for f in all_files if f not in {H5[c].name for c in CASES}]
record("A", "no unexpected files are in the folder",
       "PASS" if not extra else "INFO", extra or f"{len(all_files)} files, all expected")

# --- A2: extraction manifest -------------------------------------------------------
man = pd.read_csv(EXPORTS / "extraction_manifest.csv")
n_ext = int((man.disposition.isin(["extracted", "already-extracted"])).sum())
n_ver = int((man.disposition == "verified-identical-to-existing").sum())
n_bad = int((~man.disposition.isin(
    ["extracted", "already-extracted", "verified-identical-to-existing"])).sum())
record("A", "the delivery archive was extracted and verified",
       "PASS" if (n_ext == 120 and n_ver == 28 and n_bad == 0) else "FAIL",
       f"{n_ext} step4 members extracted; {n_ver} re-shipped Step 3/pilot members "
       f"byte-identical to the validated local copies; {n_bad} problems")
""")

code("""# --- A3: key inventory -------------------------------------------------------------
DUAL_KEYS = {"nuclear_cap_price", "nuclear_cap_price_raw",
             "nuclear_cap_price_ub", "nuclear_cap_price_ub_raw"}
keysets = {c: set(h5_keys(c)) for c in CASES}
union = set.union(*keysets.values())
ref_keys = set(h5_keys(REF))
bad = {}
for c in CASES:
    diff = (union - keysets[c]) | (keysets[c] - union)
    if diff - DUAL_KEYS:
        bad[c] = sorted(diff - DUAL_KEYS)
drift = sorted((union - ref_keys) | (ref_keys - union) - DUAL_KEYS)
no_dual = sorted(c for c in CASES if "nuclear_cap_price" not in keysets[c])
record("A", "all 120 files have the same data keys (dual keys can be absent when zero)",
       "PASS" if not bad else "FAIL",
       f"key counts {sorted(set(len(keysets[c]) for c in CASES))}"
       + (f"; unexpected differences: {bad}" if bad else ""))
record("A", "the key set agrees with the Step 3 vintage",
       "PASS" if not drift else "FAIL",
       f"drift vs {REF}: {drift}" if drift else f"{len(ref_keys)} keys, no drift")
record("A", "cases with no dual key (all-zero dual, possibly unbound)", "INFO",
       no_dual or "every case has a dual key")

# --- A4: solver residuals ----------------------------------------------------------
worst_z, worst_at = 0.0, None
for c in CASES:
    ec = load(c, "error_check").set_index("*")["Value"]
    m = float(ec.abs().max())
    if m > worst_z:
        worst_z, worst_at = m, c
record("A", "the solver residuals are small in every file",
       "PASS" if worst_z < 1e-2 else "FAIL", f"worst |residual| {worst_z:.2e} at {worst_at}")

obj = {c: float(load(c, "objfn_raw")["Value"].iloc[0]) for c in CASES}
for b in set(BASE_CASES) | set(LARGE_P50):
    obj[b] = float(load(b, "objfn_raw")["Value"].iloc[0])
ok_obj = all(np.isfinite(v) and v > 0 for v in obj.values())
record("A", "the objective value is a normal positive number in every file",
       "PASS" if ok_obj else "FAIL",
       f"range {min(obj.values()):.4e} to {max(obj.values()):.4e}")
""")

code("""# --- A5: model years ---------------------------------------------------------------
EXPECT_YEARS = [int(y) for y in sw(REF, "yearset").split("_")]
YEARS_BY_CASE = {c: sorted(load(c, "cap")["t"].unique()) for c in CASES}
bad_years = {c: y for c, y in YEARS_BY_CASE.items() if y != EXPECT_YEARS}
YEARS_RUN = EXPECT_YEARS
record("A", "the model years are correct in every file (annual 2031-2035 block present)",
       "PASS" if not bad_years else "FAIL",
       f"expected {EXPECT_YEARS}" + (f"; wrong in {bad_years}" if bad_years else ""))

# --- A6: sequential solve mode -----------------------------------------------------
# pvf_onm = 1/crf(t). It is flat from 2026 on. The history years use other rates.
worst = dict(pvfc=0.0, pvfo=0.0, cs=0.0, zrep=0)
for c in CASES:
    pvfc = load(c, "pvf_capital").set_index("t")["Value"]
    pvfo = load(c, "pvf_onm").set_index("t")["Value"]
    pvfo = pvfo[pvfo.index >= 2026]
    cs = load(c, "cost_scale")["Value"].iloc[0]
    worst["pvfc"] = max(worst["pvfc"], float((pvfc - 1.0).abs().max()))
    worst["pvfo"] = max(worst["pvfo"], float((pvfo - pvfo.mean()).abs().max()))
    worst["cs"] = max(worst["cs"], abs(float(cs) - 1.0))
    worst["zrep"] = max(worst["zrep"], abs(len(load(c, "z_rep")) - len(EXPECT_YEARS)))
ok_seq = worst["pvfc"] < 1e-9 and worst["pvfo"] < 1e-3 and worst["cs"] < 1e-9 and worst["zrep"] == 0
record("A", "every run used the sequential solve mode",
       "PASS" if ok_seq else "FAIL",
       f"pvf_capital==1 (max dev {worst['pvfc']:.1e}); pvf_onm flat from 2026 "
       f"(max dev {worst['pvfo']:.1e}); cost_scale==1; "
       f"z_rep has {len(EXPECT_YEARS)} years in every file")
""")

md("""## Phase B1 — Sensitivity runs: pointer-copy identity and no-ITC baseline

The 108 sensitivity cases point at the same nuclear input files as their Step 3 base case.
Thus the nuclear data in each sensitivity output must be identical to the base-case output.
This is a stronger test than a fingerprint against the repository files.
It also proves that no input drift occurred between the two NREL batches.

- Test B1a compares the nuclear capital cost with the base-case output.
- Test B1b compares the nuclear finance multiplier with the base-case output.
- Test B1c makes sure that the runs give no ITC to nuclear technology.
- Test B1d makes sure that the other technologies keep their ITC.

Test B1c is important.
The paper reads the mandate dual as the full required subsidy.
This is only correct if the runs give no other subsidy to nuclear technology.""")

code("""NUC = ["nuclear", "nuclear-smr"]

def nuc_slice(case, key):
    df = load(case, key)
    df = df[df["i"].isin(NUC)]
    dims = [c for c in df.columns if c != "Value"]
    return df.set_index(dims)["Value"]

pc_rows = []
for c in SENS_CASES:
    b = META[c]["base"]
    for key in ["cost_cap", "cost_cap_fin_mult_noITC"]:
        a = nuc_slice(c, key)
        r = nuc_slice(b, key)
        j = pd.concat([a, r], axis=1, keys=["sens", "base"]).fillna(0.0)
        d = (j["sens"] - j["base"]).abs()
        rel = float((d / j["base"].abs().clip(lower=1e-9)).max())
        pc_rows.append(dict(case=c, base=b, key=key, n_points=len(j),
                            max_abs_diff=float(d.max()), max_rel_diff=rel))
pc = pd.DataFrame(pc_rows)
pc.to_csv(EXPORTS / "pointer_copy_comparison.csv", index=False)
worst_cc = pc[pc.key == "cost_cap"].max_rel_diff.max()
worst_fm = pc[pc.key == "cost_cap_fin_mult_noITC"].max_rel_diff.max()
record("B1", "the nuclear capital cost is identical to the base-case output (108 cases)",
       "PASS" if worst_cc < 1e-6 else "FAIL", f"max rel difference {worst_cc:.2e}")
record("B1", "the nuclear finance multiplier is identical to the base-case output (108 cases)",
       "PASS" if worst_fm < 1e-6 else "FAIL", f"max rel difference {worst_fm:.2e}")
""")

code("""# --- B1c/B1d: no-ITC baseline ------------------------------------------------------
worst_wedge, wedge_at = 0.0, None
for c in CASES:   # all 120: the large100 percentile cases share the baseline
    fm = nuc_slice(c, "cost_cap_fin_mult")
    fmno = nuc_slice(c, "cost_cap_fin_mult_noITC")
    d = (fm - fmno).abs()
    m = float(d.max())
    if m > worst_wedge:
        worst_wedge, wedge_at = m, c
record("B1", "the model gives no ITC to nuclear technology (fin_mult == fin_mult_noITC, all 120)",
       "PASS" if worst_wedge < 1e-6 else "FAIL",
       f"max |difference| {worst_wedge:.2e}" + (f" at {wedge_at}" if worst_wedge >= 1e-6 else ""))

worst_itc, itc_at = 0.0, None
for c in CASES:
    sc = load(c, "systemcost_techba")
    it = sc[sc["sys_costs"].str.contains("itc", case=False) & sc["i"].isin(NUC)]
    m = float(it["Value"].abs().max()) if len(it) else 0.0
    if m > worst_itc:
        worst_itc, itc_at = m, c
record("B1", "the system cost data shows no ITC payments for nuclear technology (all 120)",
       "PASS" if worst_itc < 1.0 else "FAIL",
       f"max |nuclear ITC row| ${worst_itc:,.0f}" + (f" in {itc_at}" if worst_itc >= 1.0 else ""))

itc_mag = {c: abs(float(load(c, "tax_expenditure_itc")["Value"].sum())) for c in CASES}
record("B1", "the other technologies keep their ITC (all 120)",
       "PASS" if min(itc_mag.values()) > 1e8 else "FAIL",
       f"total ITC tax expenditure magnitude {min(itc_mag.values())/1e9:.1f} to "
       f"{max(itc_mag.values())/1e9:.1f} B$ per case")
""")

md("""## Phase B2 — Sensitivity runs: market-switch echoes

Each sensitivity arm changes exactly one market assumption.
These tests read the output data and make sure that each switch had its intended effect.
They also make sure that the switch did not leak into the other arms.

- `gaslo` / `gashi`: the national gas price must sit below / above the base case.
  Note: `AEO_2026_HOG` means high oil and gas **supply**. This makes the price **low**.
- `demhi`: the national exogenous load must sit above the base case.
- `relo` / `rehi`: the renewable capital costs must sit below / above the base case.
- `translim`: the new transmission build must not go above the base case.

The transmission test uses national totals only.
The P7 caveat applies: regional data across cost worlds is siting-degenerate.""")

code("""echo_rows = []

def nat_series(case, key, filt=None):
    df = load(case, key)
    if filt is not None:
        df = filt(df)
    return df.groupby("t")["Value"].sum()

# --- gas price echo ----------------------------------------------------------------
gas_bad = []
for c in SENS_CASES:
    s = META[c]["sens"]
    if s not in ("gaslo", "gashi"):
        continue
    g = load(c, "repgasprice_nat").set_index("t")["Value"]
    gb = load(META[c]["base"], "repgasprice_nat").set_index("t")["Value"]
    yrs = [t for t in g.index if t >= 2026 and t in gb.index]
    d = (g.reindex(yrs) - gb.reindex(yrs))
    frac_dir = float((d < 0).mean()) if s == "gaslo" else float((d > 0).mean())
    echo_rows.append(dict(case=c, sens=s, metric="gas_price_mean_rel",
                          value=float((g.reindex(yrs) / gb.reindex(yrs)).mean())))
    if frac_dir < 0.9:
        gas_bad.append((c, round(frac_dir, 2)))
record("B2", "the gas price sits below the base in gaslo and above it in gashi",
       "PASS" if not gas_bad else "FAIL",
       gas_bad[:5] or "correct direction in >=90% of model years, all 36 gas cases")

# --- demand echo -------------------------------------------------------------------
dem_bad = []
DEMHI = [c for c in SENS_CASES if META[c]["sens"] == "demhi"]
for c in DEMHI:
    lr = nat_series(c, "load_rt")
    lb = nat_series(META[c]["base"], "load_rt")
    yrs = [t for t in lr.index if t >= 2031]
    ratio = float((lr.reindex(yrs) / lb.reindex(yrs)).mean())
    echo_rows.append(dict(case=c, sens="demhi", metric="load_mean_rel", value=ratio))
    if not (lr.reindex(yrs) >= lb.reindex(yrs) - 1.0).all():
        dem_bad.append(c)
record("B2", "the exogenous load sits above the base case in every demhi case",
       "PASS" if not dem_bad else "FAIL",
       dem_bad[:5] or f"18 demhi cases; mean load ratio "
       f"{np.mean([r['value'] for r in echo_rows if r['metric']=='load_mean_rel']):.3f}")

# demhi cases must share one exogenous load path.
ref_l = load(DEMHI[0], "load_rt").set_index(["r", "t"])["Value"]
dem_same = 0.0
for c in DEMHI[1:]:
    j = pd.concat([ref_l, load(c, "load_rt").set_index(["r", "t"])["Value"]],
                  axis=1, keys=["a", "b"]).fillna(0.0)
    dem_same = max(dem_same, float(((j["a"] - j["b"]).abs()
                                    / j["a"].abs().clip(lower=1.0)).max()))
record("B2", "the exogenous load is identical inside the demhi block",
       "PASS" if dem_same < 1e-6 else "FAIL", f"max rel difference {dem_same:.2e}")
""")

code("""# --- renewable cost echo -----------------------------------------------------------
RE_FAMS = ["upv", "wind-ons", "wind-ofs", "battery", "csp", "geo"]

def re_cost(case):
    cc = load(case, "cost_cap")
    fam = cc["i"].str.extract(r"^([a-z\\-]+)", expand=False)
    cc = cc.assign(fam=fam)
    cc = cc[cc["fam"].isin(RE_FAMS) & (cc["t"] >= 2026)]
    return cc.groupby(["fam", "t"])["Value"].mean()

re_bad = []
for c in SENS_CASES:
    s = META[c]["sens"]
    if s not in ("relo", "rehi"):
        continue
    a = re_cost(c)
    b = re_cost(META[c]["base"])
    j = pd.concat([a, b], axis=1, keys=["sens", "base"]).dropna()
    rel = j["sens"] / j["base"]
    frac_dir = float((rel <= 1.0 + 1e-9).mean()) if s == "relo" else float((rel >= 1.0 - 1e-9).mean())
    echo_rows.append(dict(case=c, sens=s, metric="re_cost_mean_rel", value=float(rel.mean())))
    if frac_dir < 0.9:
        re_bad.append((c, round(frac_dir, 2), round(float(rel.mean()), 3)))
record("B2", "the renewable capital costs sit below the base in relo and above it in rehi",
       "PASS" if not re_bad else "FAIL",
       re_bad[:5] or "correct direction in >=90% of (family, year) points, all 36 RE cases")

# --- transmission echo -------------------------------------------------------------
tr_bad = []
for c in SENS_CASES:
    if META[c]["sens"] != "translim":
        continue
    a = float(load(c, "invtran_out")["Value"].sum())
    b = float(load(META[c]["base"], "invtran_out")["Value"].sum())
    echo_rows.append(dict(case=c, sens="translim", metric="new_transmission_rel",
                          value=a / b if b else np.nan))
    if a > b * 1.01:
        tr_bad.append((c, round(a / b, 3)))
record("B2", "the new transmission build does not go above the base case in translim",
       "PASS" if not tr_bad else "FAIL",
       tr_bad[:5] or "national new-transmission totals <= base, all 18 translim cases "
       "(national totals only; the P7 caveat applies)")

# --- cross-invariance: switches do not leak into other arms ------------------------
# Only the truly exogenous inputs can carry a leak test: the exogenous load and the
# RE capital costs. The gas price is an equilibrium output on the supply curve, so
# every arm moves it (demhi moves it the most: more load = more gas demand);
# it is context, not a leak signal.
leak, gas_move = [], {}
for c in SENS_CASES:
    s, b = META[c]["sens"], META[c]["base"]
    if s not in ("gaslo", "gashi"):
        g = load(c, "repgasprice_nat").set_index("t")["Value"]
        gb = load(b, "repgasprice_nat").set_index("t")["Value"]
        rel = float(((g - gb).abs() / gb.abs().clip(lower=1e-9)).max())
        gas_move.setdefault(s, []).append(rel)
    if s != "demhi":
        lr = nat_series(c, "load_rt")
        lb = nat_series(b, "load_rt")
        rel = float(((lr - lb).abs() / lb.abs().clip(lower=1.0)).max())
        if rel > 1e-6:
            leak.append((c, "load_rt", round(rel, 6)))
    if s not in ("relo", "rehi"):
        j = pd.concat([re_cost(c), re_cost(b)], axis=1, keys=["a", "b"]).dropna()
        rel = float(((j["a"] - j["b"]).abs() / j["b"].abs().clip(lower=1e-9)).max())
        if rel > 1e-6:
            leak.append((c, "re_cost", round(rel, 6)))
record("B2", "no market switch leaks into the other arms (exogenous inputs only)",
       "PASS" if not leak else "FAIL",
       leak[:8] or "exogenous load and RE capital costs identical to base outside their arms")
record("B2", "endogenous gas-price response outside the gas arms", "INFO",
       {s: f"max {max(v):.3f}" for s, v in sorted(gas_move.items())})

pd.DataFrame(echo_rows).to_csv(EXPORTS / "switch_echo.csv", index=False)
""")

md("""## Phase B3 — large100 percentile runs: input data fingerprints

The 12 large100 percentile cases carry new input files.
These tests are the Step 3 fingerprint tests, applied to the new cases.
Each test computes the expected values from the repository input files.
Then it compares them with the output data.

- Test B3a compares the capital cost data with the plant input files.
- Tests B3b and B3c compare the heat rate and the variable cost.
- Tests B3d to B3g compare the finance multipliers with our own calculation.""")

code("""# --- B3a: capital cost fingerprint (both techs, 12 cases) --------------------------
PC_DIR = REPO / "inputs" / "plant_characteristics"

def plantchar(name):
    df = pd.read_csv(PC_DIR / f"{name}.csv")
    df.columns = [c.lstrip("*").lower() for c in df.columns]
    return df.set_index("t")

fp_rows = []
for c in LARGE_CASES:
    cc = load(c, "cost_cap")
    cc = cc[cc["i"].isin(NUC)].set_index(["i", "t"])["Value"]
    for itech in NUC:
        pc_df = plantchar(META[c]["pc"][itech])
        for t, occ_kw in pc_df["capcost"].items():
            if (itech, t) not in cc.index:
                continue
            expect = occ_kw * 1000.0 * D2022
            got = float(cc.loc[(itech, t)])
            fp_rows.append(dict(case=c, i=itech, t=t, expect=expect, got=got,
                                rel_err=abs(got - expect) / expect))
fp = pd.DataFrame(fp_rows)
fp.to_csv(EXPORTS / "fingerprint_errors.csv", index=False)
worst_fp = fp.loc[fp.rel_err.idxmax()]
record("B3", "the capital cost data agrees with the plant input files (12 large100 cases)",
       "PASS" if fp.rel_err.max() < 1e-4 else "FAIL",
       f"{len(fp)} (case,tech,year) points; max rel err {fp.rel_err.max():.2e} at "
       f"({worst_fp.case}, {worst_fp.i}, {worst_fp.t})")

# --- B3b/B3c: heat rate, VOM -------------------------------------------------------
hr_bad = []
for c in LARGE_CASES:
    hr = load(c, "heat_rate")
    hr = hr[hr["i"].isin(NUC)].groupby("i")["Value"].agg(["min", "max"])
    for itech in hr.index:
        exp = float(plantchar(META[c]["pc"][itech])["heatrate"].iloc[-1])
        if not (abs(hr.loc[itech, "min"] - exp) < 0.05 and abs(hr.loc[itech, "max"] - exp) < 0.6):
            hr_bad.append((c, itech, hr.loc[itech].to_dict(), exp))
record("B3", "the heat rate data agrees with the plant input files",
       "PASS" if not hr_bad else "INFO",
       hr_bad[:3] if hr_bad else "both techs, all 12 cases (old vintages can differ a little)")

vom_bad = []
for c in LARGE_CASES:
    vom = load(c, "cost_vom")
    for itech in NUC:
        v = vom[vom["i"] == itech]
        if not len(v):
            continue
        got = float(v["Value"].mode().iloc[0])
        exp = float(plantchar(META[c]["pc"][itech])["vom"].iloc[-1]) * D2022
        if abs(got - exp) / exp > 0.02:
            vom_bad.append((c, itech, round(got, 3), round(exp, 3)))
record("B3", "the variable cost (VOM) data agrees with the plant input files",
       "PASS" if not vom_bad else "FAIL", vom_bad[:5] or "modal VOM within 2%, all 12 cases")
""")

code("""# --- B3d-B3g: finance-multiplier replication (2_financials.gms) --------------------
FIN_DIR = REPO / "inputs" / "financials"
YEARS = np.arange(2010, 2051)

def yi(t):
    return int(t - YEARS[0])

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

IB = on_years("interest_rate_nom")
TAX = on_years("tax_rate")
D_NOM = on_years("d_nom")
D_REAL = on_years("d_real")
DEP = pd.read_csv(FIN_DIR / "depreciation_schedules_default.csv")
CS_MC = pd.read_csv(FIN_DIR / "construction_schedules_mc.csv")
CC_EXPS = np.append([0.0], np.arange(0.5, 10.5, 1.0))
assert len(CS_MC) == len(CC_EXPS), (len(CS_MC), len(CC_EXPS))

def ccmult_reeds(sched_name, ib):
    x = pd.to_numeric(CS_MC[str(sched_name)], errors="coerce").fillna(0.0).to_numpy()
    return 1.0 + float(np.sum(x * (ib ** CC_EXPS - 1.0)))

def national_base(case):
    \"\"\"ccmult(i,t) x 1/(1-tax) x (1-tax*pv_dep(i,t)) x risk_mult(i,t) x eval_adj — the
    region-free part of cost_cap_fin_mult_noITC (degradation_adj = 1 for nuclear).\"\"\"
    ft = pd.read_csv(FIN_DIR / f"financials_tech_{META[case]['fin']}.csv")
    ft.columns = [c.lstrip("*") for c in ft.columns]
    ft = ft[ft["i"].isin(["Nuclear", "Nuclear-SMR"])]
    out = {}
    for iname, grp in ft.groupby("i"):
        grp = grp.set_index("t").reindex(YEARS).ffill().bfill()
        dep_col = str(int(grp["depreciation_sch"].iloc[0]))
        dep_frac = DEP[dep_col].to_numpy(float)
        pv_dep = np.array([np.sum(dep_frac / dn ** np.arange(1, len(dep_frac) + 1)) for dn in D_NOM])
        eval_p = float(grp["eval_period"].iloc[0])
        risk = 1.0 + grp["finance_diff_real"].to_numpy(float) * (
            (1 - (1 / D_REAL) ** eval_p) / (D_REAL - 1.0))
        sys_pvf = (1 - (1 / D_REAL) ** (30 - 1)) / (D_REAL - 1.0) + 1
        tech_pvf = (1 - (1 / D_REAL) ** (eval_p - 1)) / (D_REAL - 1.0) + 1
        eval_adj = sys_pvf / tech_pvf
        ccm = np.array([ccmult_reeds(grp.loc[t, "construction_sch"], IB[yi(t)]) for t in YEARS])
        out[iname.lower()] = pd.Series(
            ccm / (1 - TAX) * (1 - TAX * pv_dep) * risk * eval_adj, index=YEARS)
    return out

fin_rows, reg_factors = [], {}
for c in LARGE_CASES:
    base = national_base(c)
    h5f = load(c, "cost_cap_fin_mult_noITC")
    h5f = h5f[h5f["i"].isin(NUC)]
    for iname, grp in h5f.groupby("i"):
        piv = grp.pivot_table(index="r", columns="t", values="Value")
        exp = base[iname].reindex(piv.columns)
        ratio = piv / exp.values[None, :]
        reg = ratio.mean(axis=1)
        reg_factors[(c, iname)] = reg
        resid = (piv - reg.values[:, None] * exp.values[None, :]).abs()
        fin_rows.append(dict(
            case=c, i=iname, n_regions=len(piv),
            ratio_spread_over_t=float((ratio.max(axis=1) - ratio.min(axis=1)).max()),
            worst_resid_after_regional=float(resid.max().max()),
            reg_factor_mean=float(reg.mean()), reg_factor_min=float(reg.min()),
            reg_factor_max=float(reg.max())))
fin_cmp = pd.DataFrame(fin_rows)
fin_cmp.to_csv(EXPORTS / "fin_mult_noITC_comparison.csv", index=False)
print(fin_cmp.round(5).to_string(index=False))

record("B3", "the finance multiplier has the correct regional structure",
       "PASS" if (fin_cmp.ratio_spread_over_t < 2e-3).all() else "FAIL",
       f"max ratio spread over years {fin_cmp.ratio_spread_over_t.max():.2e} (12 cases)")
record("B3", "the finance multiplier agrees with our own calculation",
       "PASS" if (fin_cmp.worst_resid_after_regional < 1.5e-3).all() else "FAIL",
       f"worst |residual| {fin_cmp.worst_resid_after_regional.max():.2e} "
       "(GAMS rounds to 3 decimals)")
county = pd.read_csv(FIN_DIR / "reg_cap_cost_diff_default.csv")["NUCLEAR"]
lo_b, hi_b = 1 + county.min() - 0.005, 1 + county.max() + 0.005
ok_reg = (((fin_cmp.reg_factor_mean - (1 + county.mean())).abs() < 0.02).all()
          and (fin_cmp.reg_factor_min > lo_b).all() and (fin_cmp.reg_factor_max < hi_b).all())
record("B3", "the regional factors are inside the county data range",
       "PASS" if ok_reg else "FAIL",
       f"implied range [{fin_cmp.reg_factor_min.min():.4f}, {fin_cmp.reg_factor_max.max():.4f}] "
       f"inside county range [{lo_b:.4f}, {hi_b:.4f}]")
""")

md("""## Phase C — Mandate mechanics and dual prices, all 120 runs

These tests make sure that the capacity mandate and its dual price operate correctly.

- Test C1 makes sure that the capacity satisfies the mandate floor in every case.
- Test C2 makes sure that the capacity equals the floor in each binding year.
- Test C3 makes sure that a positive dual occurs only in the binding years.
- Test C4 makes sure that the dual conversion is correct.
- Tests C5 and C6 make sure that each case builds only its own technology.
- Test C7 makes sure that no SMR capacity exists before 2031.
- Test C8 records the overbuild data for the slack cases.

The dual is a rental price in dollars of 2004 per MW and year.
The export `duals_by_year.csv` covers all 120 Step 4 cases.
The Step 3 base-case duals stay canonical in `step3_checks/exports/duals_by_year.csv`.""")

code("""# --- mandate trajectories + dual tables --------------------------------------------
NL_DIR = REPO / "inputs" / "nuclear_learning"

def trajectory(scen):
    tr = pd.read_csv(NL_DIR / f"nuclear_cap_trajectory_{scen}.csv")
    tr.columns = [c.lstrip("*") for c in tr.columns]
    return tr.set_index(tr.columns[0])["MW"]

TRAJ = {c: trajectory(META[c]["scen"]) for c in CASES}
DUAL, RAW = {}, {}
for c in CASES:
    if "nuclear_cap_price" in keysets[c]:
        DUAL[c] = load(c, "nuclear_cap_price").set_index("t")["Value"]
        RAW[c] = load(c, "nuclear_cap_price_raw").set_index("t")["Value"]
    else:
        DUAL[c] = pd.Series(dtype=float)
        RAW[c] = pd.Series(dtype=float)
# the Step 3 base + large p50 duals, for phase D/F comparisons
for b in set(BASE_CASES) | set(LARGE_P50):
    if "nuclear_cap_price" in set(h5_keys(b)):
        DUAL[b] = load(b, "nuclear_cap_price").set_index("t")["Value"]
    else:
        DUAL[b] = pd.Series(dtype=float)

MAND_CAP = {}
for c in CASES:
    cap = load(c, "cap")
    MAND_CAP[c] = cap[cap["i"] == META[c]["mandated_tech"]].groupby("t")["Value"].sum()

rows, viol, bind_bad, slack_bad = [], [], [], []
for c in CASES:
    tr, s, d = TRAJ[c], MAND_CAP[c], DUAL[c]
    mand_years = [t for t in YEARS_RUN if tr.get(t, 0) > 0]
    for t in YEARS_RUN:
        req = float(tr.get(t, 0.0))
        have = float(s.get(t, 0.0))
        dual = float(d.get(t, 0.0))
        rows.append(dict(case=c, t=t, mandate_MW=req, cap_MW=round(have, 1),
                         slack_MW=round(have - req, 1), dual_2004_MWyr=dual,
                         dual_raw=float(RAW[c].get(t, 0.0)),
                         dual_2024_MWyr=dual * TO2024))
        if t in mand_years:
            if have - req < -5:
                viol.append((c, t, round(have - req, 1)))
            if dual > 1.0 and abs(have - req) > 5:
                bind_bad.append((c, t, dual, round(have - req, 1)))
            if have - req > 100 and dual > 1e-3:
                slack_bad.append((c, t, dual, round(have - req, 1)))
duals_tbl = pd.DataFrame(rows)
duals_tbl.to_csv(EXPORTS / "duals_by_year.csv", index=False)

record("C", "the capacity satisfies the mandate floor in every case",
       "PASS" if not viol else "FAIL",
       viol[:5] or "no violation larger than 5 MW in any mandated year")
record("C", "the capacity equals the floor in each binding year (positive dual)",
       "PASS" if not bind_bad else "FAIL",
       bind_bad[:5] or "every year with dual > $1/MW-yr has |slack| <= 5 MW")
record("C", "a positive dual occurs only in the binding years",
       "PASS" if not slack_bad else "FAIL",
       slack_bad[:5] or "every year with slack > 100 MW has a zero dual")
""")

code("""# --- C4: dual conversion audit -----------------------------------------------------
worst_conv = 0.0
for c in CASES:
    if not len(DUAL[c]):
        continue
    pvf = load(c, "pvf_onm").set_index("t")["Value"]
    cs = float(load(c, "cost_scale")["Value"].iloc[0])
    implied = RAW[c] / DUAL[c] / cs
    rel = (implied - pvf.reindex(implied.index)).abs() / pvf.reindex(implied.index)
    worst_conv = max(worst_conv, float(rel.max()))
record("C", "the dual conversion is correct (raw = cost_scale x pvf_onm x converted)",
       "PASS" if worst_conv < 1e-4 else "FAIL",
       f"max rel err {worst_conv:.2e} across all cases with duals")

# --- C5/C6: technology purity ------------------------------------------------------
bad_large, bad_smr = [], []
for c in SENS_CASES:
    nb_ = load(c, "cap_new_ann")
    lg = nb_[(nb_["i"] == "nuclear") & (nb_["t"] > 2030)]["Value"].sum()
    if lg > 0:
        bad_large.append((c, float(lg)))
for c in LARGE_CASES:
    nb_ = load(c, "cap_new_ann")
    sm = nb_[nb_["i"] == "nuclear-smr"]["Value"].sum()
    if sm > 0:
        bad_smr.append((c, float(sm)))
record("C", "no large-reactor builds occur after 2030 in the sensitivity cases",
       "PASS" if not bad_large else "FAIL", bad_large or "all 108 sensitivity cases clean")
record("C", "no SMR builds occur in the large100 percentile cases",
       "PASS" if not bad_smr else "FAIL", bad_smr or "all 12 large100 cases clean")

# --- C7: no SMR capacity before 2031 -----------------------------------------------
pre = {}
for c in SENS_CASES:
    s = load(c, "cap")
    s = s[(s["i"] == "nuclear-smr") & (s["t"] < 2031)]["Value"].sum()
    pre[c] = float(s)
record("C", "no SMR capacity exists before 2031",
       "PASS" if max(pre.values()) == 0 else "FAIL",
       f"max pre-2031 SMR capacity {max(pre.values()):.1f} MW")

# --- C8: overbuild + first binding year --------------------------------------------
ob_rows = []
for c in CASES:
    tr = TRAJ[c]
    mand_years = [t for t in YEARS_RUN if tr.get(t, 0) > 0]
    sub = duals_tbl[(duals_tbl.case == c) & duals_tbl.t.isin(mand_years)]
    slackers = sub[sub.slack_MW > 100]
    first_dual = int(sub[sub.dual_2004_MWyr > 1.0].t.min()) if (sub.dual_2004_MWyr > 1.0).any() else None
    ob_rows.append(dict(case=c, n_mandated_years=len(mand_years),
                        n_binding_years=int((sub.dual_2004_MWyr > 1.0).sum()),
                        n_slack_years=len(slackers), first_binding_year=first_dual,
                        max_overbuild_ratio=round(float((sub.cap_MW / sub.mandate_MW).max()), 2)))
ob = pd.DataFrame(ob_rows)
ob.to_csv(EXPORTS / "overbuild_by_case.csv", index=False)
unbound = ob[ob.n_binding_years == 0]
record("C", "overbuild and binding years by case", "INFO",
       f"{len(unbound)} cases with zero binding years: {list(unbound.case)}"
       if len(unbound) else "every case has at least one binding year")
""")

md("""## Phase D — Consistency against the Step 3 base cases

These tests compare each Step 4 run with its Step 3 base case.
A sensitivity changes one market assumption.
Linear-program logic gives the expected direction of the objective change.

- Cheaper inputs (`gaslo`, `relo`) must not increase the system cost.
- More expensive inputs (`gashi`, `rehi`) must not decrease the system cost.
- More load (`demhi`) must not decrease the system cost.
- The large100 percentile objectives must bracket the Step 3 p50 objective.

The parameter arms have a valid direction inside each yearly LP.
`translim` changes constraints, not parameters, and the solve is sequential and myopic.
A restriction in an early year changes the state that the later years inherit.
Thus the restricted path total can land below the base path total.
The test records the `translim` shift as context, with no pass condition.""")

code("""TOL = 1e-6
DIR_UP = {"gashi", "rehi", "demhi"}
DIR_DN = {"gaslo", "relo"}
dir_bad, translim_rel = [], []
for c in SENS_CASES:
    b = META[c]["base"]
    rel = (obj[c] - obj[b]) / obj[b]
    s = META[c]["sens"]
    if s in DIR_UP and rel < -TOL:
        dir_bad.append((c, round(rel, 6)))
    if s in DIR_DN and rel > TOL:
        dir_bad.append((c, round(rel, 6)))
    if s == "translim":
        translim_rel.append(rel)
record("D", "the objective moves in the expected direction against the base case",
       "PASS" if not dir_bad else "FAIL",
       dir_bad[:8] or "gaslo/relo never above base; gashi/rehi/demhi never below base")
record("D", "translim objective shift (no pass condition: myopic path dependence)", "INFO",
       f"range {min(translim_rel):+.4f} to {max(translim_rel):+.4f} rel to base; "
       "a restriction can lower the myopic path total because early-year "
       "restrictions change the inherited state")
shift = {s: round(float(np.mean([(obj[c] - obj[META[c]['base']]) / obj[META[c]['base']]
                                 for c in SENS_CASES if META[c]["sens"] == s])), 4)
         for s in SENS}
record("D", "mean objective shift by sensitivity arm", "INFO", shift)

# large100 percentile bracketing (p50 from Step 3)
br_bad = []
for tok in SCHEDULES:
    o05 = obj[f"large100_{tok}_p05"]
    o50 = obj[f"large100_{tok}_p50"]
    o95 = obj[f"large100_{tok}_p95"]
    if not (o05 <= o50 <= o95):
        br_bad.append((tok, o05, o50, o95))
record("D", "the large100 percentile objectives bracket the Step 3 p50 objective",
       "PASS" if not br_bad else "FAIL",
       br_bad or "p05 <= p50 <= p95 for all 6 schedules")
""")

md("""## Phase E — Load data integrity

These tests make sure that the load inputs were not corrupted.

- Test E1 makes sure that the exogenous load is identical to the base case
  in the 90 non-demhi sensitivity cases and the 12 large100 cases.
  (Phase B2 already tests the demhi block.)
- Test E2 makes sure that no load is dropped after 2025.
- Test E3 tests the high-electrification profile file if it is in the repository.
  The file downloads from Zenodo on first use at NREL.
  Thus the file can be absent on this machine.""")

code("""# --- E1: load invariance -----------------------------------------------------------
li_rows = []
for c in SENS_CASES + LARGE_CASES:
    if META[c].get("sens") == "demhi":
        continue
    b = META[c]["base"] if META[c]["sens"] else REF
    a = load(c, "load_rt").set_index(["r", "t"])["Value"]
    r = load(b, "load_rt").set_index(["r", "t"])["Value"]
    j = pd.concat([a, r], axis=1, keys=["c", "ref"]).fillna(0.0)
    rel = float(((j["c"] - j["ref"]).abs() / j["ref"].abs().clip(lower=1.0)).max())
    li_rows.append(dict(case=c, vs=b, max_rel_diff=rel))
li = pd.DataFrame(li_rows)
li.to_csv(EXPORTS / "load_invariance.csv", index=False)
record("E", "the exogenous load is identical to the base case outside the demhi arm",
       "PASS" if li.max_rel_diff.max() < 1e-6 else "FAIL",
       f"{len(li)} cases; max rel difference {li.max_rel_diff.max():.2e}")

# --- E2: no dropped load after 2025 ------------------------------------------------
dl_bad = []
for c in CASES:
    dl = load(c, "dropped_load")
    modern = float(dl.loc[dl["t"] >= 2026, "Value"].sum())
    if modern >= 1.0:
        dl_bad.append((c, modern))
record("E", "no load is dropped after 2025",
       "PASS" if not dl_bad else "FAIL",
       dl_bad[:5] or "all 120 cases clean")

# --- E3: the high-electrification profile file -------------------------------------
p = REPO / "inputs" / "profiles_demand" / "demand_EER2025_100by2050.h5"
if not p.exists():
    record("E", "the high-electrification profile file is complete and correct", "INFO",
           f"{p.name} not in the repository (it downloads from Zenodo at NREL); "
           "the demhi output-side tests in phase B2 cover the load data instead")
else:
    ok, notes = True, []
    with h5py.File(p, "r") as f:
        for yr in list(f.keys())[:6]:
            g = f[yr]
            states = [k for k in g.keys() if k not in ("columns", "datetime")]
            n = {len(g[k]) for k in states}
            arrs = np.stack([g[k][:] for k in states])
            ok = ok and (len(n) == 1 and next(iter(n)) % 8760 == 0
                         and arrs.min() >= 0 and np.isfinite(arrs).all())
            notes.append(f"{yr}: {len(states)} states x {next(iter(n))} h")
    record("E", "the high-electrification profile file is complete and correct",
           "PASS" if ok else "FAIL", "; ".join(notes[:3]) + " ...")
""")

md("""## Phase F — Cross-case checks and unexpected values

These tests compare the cases against each other.
They also scan all data for bad values.

- Test F1 makes sure that the dual values do not cross between p05, p50, and p95
  inside each (schedule, sensitivity) cell and for the large100 family.
- Test F2 makes sure that the objective values are in the correct order.
- Tests F3 to F5 scan all data for NaN values and wrong negative values.
- Test F6 makes sure that the national totals equal the sum of the regional data.
- Tests F7 and F8 record context data (dual decay by arm, large100 vs smr100 ratio).

Test F1 checks the bracket claim inside each market world.
A crossing in a sensitivity world is a pre-registered finding, not a defect.
The P8 priced-coefficient identity predicts no crossing.
If a crossing occurs, record it and carry it to the analysis notebook.""")

code("""# --- F1: dual monotonicity within each (schedule, sensitivity) cell ----------------
def dual_of(name):
    return DUAL.get(name, pd.Series(dtype=float))

mono_bad = []
cells = [(tok, s) for tok in SCHEDULES for s in SENS] + [(tok, "large") for tok in SCHEDULES]
for tok, s in cells:
    if s == "large":
        names = [f"large100_{tok}_p05", f"large100_{tok}_p50", f"large100_{tok}_p95"]
    else:
        names = [f"smr100_{tok}_{p}_{s}" for p in ["p05", "p50", "p95"]]
    d05, d50, d95 = (dual_of(n) for n in names)
    idx = sorted(set(d05.index) | set(d50.index) | set(d95.index))
    if not idx:
        continue
    d05 = d05.reindex(idx).fillna(0.0)
    d50 = d50.reindex(idx).fillna(0.0)
    d95 = d95.reindex(idx).fillna(0.0)
    tol = 50.0 + 0.001 * d95.abs()
    bad_years = [int(t) for t in idx
                 if d95[t] < d50[t] - tol[t] or d50[t] < d05[t] - tol[t]]
    if bad_years:
        mono_bad.append((tok, s, bad_years))
record("F", "the dual values do not cross between p05, p50, and p95 (42 cells)",
       "PASS" if not mono_bad else "FAIL",
       mono_bad or "p95 >= p50 >= p05 in every year of every (schedule, sensitivity) "
       "cell and every large100 schedule")

# --- F2: objective order within each cell ------------------------------------------
ord_bad = []
for tok in SCHEDULES:
    for s in SENS:
        o = [obj[f"smr100_{tok}_{p}_{s}"] for p in ["p05", "p50", "p95"]]
        if not (o[0] <= o[1] <= o[2]):
            ord_bad.append((tok, s, o))
record("F", "the objective values are in the correct order (p05 <= p50 <= p95)",
       "PASS" if not ord_bad else "FAIL",
       ord_bad or "a more expensive world always costs more, all 36 cells")
""")

code("""# --- F3-F5: full data scan (NaN + negative values) ---------------------------------
NONNEG = ["cap", "cap_nat", "load_rt", "stor_in", "stor_out", "curt_ann", "hours"]
nan_bad, neg_bad, nuc_neg = [], [], []
for c in CASES:
    with h5py.File(H5[c], "r") as f:
        for k in f.keys():
            v = f[k]["Value"][:]
            if not np.isfinite(v).all():
                nan_bad.append((c, k, int((~np.isfinite(v)).sum())))
            if k in NONNEG:
                mn = float(v.min())
                if mn < -1.0:
                    neg_bad.append((c, k, mn))
    for k in ["cap_new_ann", "gen_ann"]:
        df = load(c, k)
        nuc = df[df["i"].isin(NUC)]
        if len(nuc) and float(nuc["Value"].min()) < -1.0:
            nuc_neg.append((c, k, float(nuc["Value"].min())))
record("F", "no data value is NaN or infinite in any file",
       "PASS" if not nan_bad else "FAIL",
       nan_bad[:5] or f"all {len(union)} keys x 120 files scanned")
record("F", "no negative values occur where values must not be negative",
       "PASS" if not neg_bad else "FAIL",
       neg_bad[:5] or f"checked {NONNEG}")
record("F", "the nuclear build and generation data is not negative",
       "PASS" if not nuc_neg else "FAIL",
       nuc_neg[:5] or "cap_new_ann and gen_ann nuclear rows >= 0, all 120 cases")

# --- F6: national totals equal the regional sums -----------------------------------
tot_bad = []
for c in CASES:
    for key, nat_key in [("cap", "cap_nat"), ("gen_ann", "gen_ann_nat"),
                         ("cap_new_ann", "cap_new_ann_nat"), ("ret_ann", "ret_ann_nat")]:
        s = load(c, key).groupby(["i", "t"])["Value"].sum()
        nat_df = load(c, nat_key)
        dims = [col for col in nat_df.columns if col in ("i", "t")]
        n = nat_df.groupby(dims)["Value"].sum()
        j = pd.concat([s, n], axis=1, keys=["sum", "nat"]).fillna(0.0)
        rel = float(((j["sum"] - j["nat"]).abs() / j["nat"].abs().clip(lower=1.0)).max())
        if rel > 1e-3:
            tot_bad.append((c, key, rel))
record("F", "the national totals equal the sum of the regional data",
       "PASS" if not tot_bad else "FAIL",
       tot_bad[:5] or "cap, gen_ann, cap_new_ann, ret_ann; all 120 cases within 1e-3")
""")

code("""# --- F7/F8: context (INFO) ---------------------------------------------------------
decay_by_arm = {}
for s in SENS:
    d_ = {}
    for tok in SCHEDULES:
        for p in ["p05", "p50", "p95"]:
            c = f"smr100_{tok}_{p}_{s}"
            d = DUAL[c]
            dd = d[d > 1.0].sort_index()
            if len(dd) >= 2:
                d_[f"{tok}_{p}"] = round(float(dd.iloc[-1] / dd.max()), 2)
    decay_by_arm[s] = d_
record("F", "dual end/peak ratio by case and sensitivity arm (bridge, first look)", "INFO",
       decay_by_arm)

l_vs_s = {}
for tok in SCHEDULES:
    for p in ["p05", "p95"]:
        dl_ = DUAL[f"large100_{tok}_{p}"]
        ds_ = dual_of(f"smr100_{tok}_{p}")
        if not len(ds_):
            ds_ = load(f"smr100_{tok}_{p}", "nuclear_cap_price").set_index("t")["Value"] \
                  if "nuclear_cap_price" in set(h5_keys(f"smr100_{tok}_{p}")) else pd.Series(dtype=float)
        shared = sorted(set(dl_[dl_ > 1.0].index) & set(ds_[ds_ > 1.0].index))
        if shared:
            l_vs_s[f"{tok}_{p}"] = round(float(dl_.reindex(shared).mean()
                                               / ds_.reindex(shared).mean()), 2)
record("F", "large100 dual level over smr100 dual level (shared binding years, p05/p95)",
       "INFO", f"mean ratio: {l_vs_s}")
""")

md("""## Summary and report

The next cell writes the check registry to `exports/checks_summary.csv`.
It also writes the report `step4_check_results.md` in Simplified Technical English.""")

code("""summary = pd.DataFrame(CHECKS)
summary.to_csv(EXPORTS / "checks_summary.csv", index=False)
counts = summary.status.value_counts().to_dict()
print(counts, "\\n")
fails = summary[summary.status == "FAIL"]
if len(fails):
    print("*** FAILURES ***\\n", fails.to_string(index=False))
else:
    print("No FAIL-status checks.")

PHASE_TITLES = {
    "A": "Phase A — File inventory and solve health",
    "B1": "Phase B1 — Sensitivity runs: pointer-copy identity and no-ITC baseline",
    "B2": "Phase B2 — Sensitivity runs: market-switch echoes",
    "B3": "Phase B3 — large100 percentile runs: input data fingerprints",
    "C": "Phase C — Mandate mechanics and dual prices",
    "D": "Phase D — Consistency against the Step 3 base cases",
    "E": "Phase E — Load data integrity",
    "F": "Phase F — Cross-case checks and unexpected values",
}
PHASE_STE = {
    "A": "These tests make sure that the file set is complete and that each solve is clean.",
    "B1": "These tests make sure that each sensitivity run kept the base-case nuclear "
          "inputs and that no run gives an ITC to nuclear technology.",
    "B2": "These tests make sure that each market switch had its intended effect "
          "and did not leak into the other arms.",
    "B3": "These tests make sure that the 12 large100 percentile runs used the "
          "correct new input data.",
    "C": "These tests make sure that the capacity mandate and its dual price operate correctly.",
    "D": "These tests make sure that each run moves in the expected direction "
         "against its Step 3 base case.",
    "E": "These tests make sure that the load inputs were not corrupted.",
    "F": "These tests compare the cases against each other. "
         "They also scan all data for bad values.",
}

lines = [
    "# Step 4 output checks — report",
    "",
    f"Date of this report: {date.today().isoformat()}.",
    f"Input folder: `{H5_DIR}`.",
    f"The folder has {len(all_files)} files: 108 market-sensitivity runs and "
    "12 large100 percentile runs.",
    "The notebook `step4_output_checks.ipynb` performs all tests.",
    "",
    "## Summary",
    "",
    f"The notebook performed {len(summary)} checks.",
    f"Result counts: {counts}.",
]
if len(fails):
    lines += [f"**{len(fails)} tests failed.** The tables below show them with the "
              "status FAIL. Examine each failed test before you use the results."]
else:
    lines += ["**All pass/fail tests passed.** No test found a defect in the 120 runs.",
              "Rows with the status INFO give context data. They have no pass condition."]
lines += [
    "",
    "Status meanings:",
    "",
    "- **PASS** — the condition holds.",
    "- **FAIL** — the condition does not hold. This shows a defect.",
    "- **INFO** — context data only. There is no pass condition.",
    "- **BLOCKED** — the test could not run. Data is missing.",
]
for ph in ["A", "B1", "B2", "B3", "C", "D", "E", "F"]:
    sub = summary[summary.phase == ph]
    if not len(sub):
        continue
    lines += ["", f"## {PHASE_TITLES[ph]}", "", PHASE_STE[ph], "",
              "| Test | Result | Data |", "|---|---|---|"]
    for _, r in sub.iterrows():
        det = str(r.detail).replace("|", "/").replace("\\n", " ")
        if len(det) > 220:
            det = det[:217] + "..."
        lines.append(f"| {r.check} | **{r.status}** | {det} |")
lines += [
    "",
    "## Files that this notebook writes",
    "",
    "- `exports/checks_summary.csv` — the full check registry.",
    "- `exports/duals_by_year.csv` — the dual prices for each of the 120 cases and years.",
    "- `exports/overbuild_by_case.csv` — the binding and slack years for each case.",
    "- `exports/extraction_manifest.csv` — the delivery extraction and verification record.",
    "- `exports/pointer_copy_comparison.csv` — the nuclear-input identity comparison.",
    "- `exports/switch_echo.csv` — the market-switch echo magnitudes.",
    "- `exports/fingerprint_errors.csv` — the large100 capital cost comparison points.",
    "- `exports/fin_mult_noITC_comparison.csv` — the large100 finance multiplier comparison.",
    "- `exports/load_invariance.csv` — the load comparison across cases.",
    "",
]
(HERE / "step4_check_results.md").write_text("\\n".join(lines), encoding="utf-8")
print(f"wrote step4_check_results.md ({len(lines)} lines)")
""")

nb["cells"] = C
out = "step4_output_checks.ipynb"
nbf.write(nb, out)
print(f"wrote {out} with {len(C)} cells")
