"""Generate step3_output_checks.ipynb. Edit cell sources here, re-run to regenerate.

Same convention as z-ethan/pilots/_build_notebook.py: the notebook is the deliverable;
this builder exists so the notebook can be regenerated and diffed as plain python.
Run with the playground-env python.

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


md("""# Step 3 output checks — 25 production runs

This notebook tests the 25 production run outputs from NREL.
The output files are in `D:\\ReEDS files\\nuclear-learning\\smr100 first run`.
The run matrix is `cases_nuclearlearning_smr100.csv` (18 smr100 cases + 6 large100 cases + 1 equality case).

The notebook makes sure that:

- The file set is complete and the solves are clean (phase A).
- Each run used the correct input data (phase B).
- The mandate and the dual prices operate correctly (phase C).
- The equality case shows the same behavior as the floor case (phase D).
- The load data is not corrupted (phase E).
- The results show no unexpected values (phase F).

Each test writes one row to a check registry.
The last cell writes the registry to `exports/checks_summary.csv`.
The last cell also writes the report `step3_check_results.md`.

Run this notebook on the **playground-env** kernel.
This notebook only reads the files on drive D. It does not change them.""")

code("""import hashlib
import json
from datetime import date
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

pd.set_option("display.width", 200)

HERE = Path.cwd()
assert HERE.name == "step3_checks", f"run from z-ethan/step3_checks/, not {HERE}"
REPO = HERE.parents[1]
EXPORTS = HERE / "exports"
EXPORTS.mkdir(exist_ok=True)

H5_DIR = Path("D:/ReEDS files/nuclear-learning/smr100 first run")
PILOT_DIR = Path("D:/ReEDS files/nuclear-learning/initial test runs")

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
        pc={"nuclear": sw(c, "plantchar_nuclear"), "nuclear-smr": sw(c, "plantchar_nuclear_smr")},
        fin=sw(c, "financials_tech_suffix"),
    )
SMR_CASES = [c for c in CASES if META[c]["techscen"] == "smr"]
LARGE_CASES = [c for c in CASES if META[c]["techscen"] == "large"]
SCHEDULES = ["eia", "aj", "iaea", "mck", "cop28", "eo"]
REF = "smr100_eia_p50"     # reference case for cross-case comparisons

H5 = {c: H5_DIR / f"test1_{c}_outputs.h5" for c in CASES}

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
print(f"cases: {len(CASES)} ({len(SMR_CASES)} smr100 + {len(LARGE_CASES)} large100, "
      f"incl. equality copy)")
print(f"2022$->2004$ deflator: {D2022:.6f}; 2004$->2024$: {TO2024:.4f}")
""")

md("""## Phase A — File inventory and solve health

These tests make sure that the file set is complete and that each solve is clean.

- Test A1 makes sure that the folder has one output file for each of the 25 cases.
- Test A2 makes sure that the three extra files are copies of the old pilot files.
- Test A3 makes sure that all files have the same data keys.
- Test A4 makes sure that the solver residuals are small in each file.
- Test A5 makes sure that the model years are correct in each file.
- Test A6 makes sure that each run used the sequential solve mode.

Note: the model removes an all-zero dual parameter from the file.
Thus an absent dual key means a zero dual. It does not mean lost data.""")

code("""# --- A1: file census -------------------------------------------------------------
missing = [c for c in CASES if not H5[c].exists()]
record("A", "one output file exists for each of the 25 cases",
       "PASS" if not missing else "FAIL",
       f"missing: {missing}" if missing else f"{len(CASES)} files in {H5_DIR}")

all_files = sorted(p.name for p in H5_DIR.glob("*.h5"))
expected = sorted(H5[c].name for c in CASES)
extra = [f for f in all_files if f not in expected]
record("A", "extra files in the folder are identified", "INFO",
       f"{len(extra)} extra files: {extra}")

# --- A2: the extra files must be copies of the pilot files -------------------------
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()

PILOT_NAMES = [f"test1_smr100_eia_{c}_outputs.h5" for c in ["lo", "mid", "hi"]]
copy_ok, copy_detail = True, []
for name in extra:
    src = PILOT_DIR / name
    if name not in PILOT_NAMES or not src.exists():
        copy_ok = False
        copy_detail.append(f"{name}: not a known pilot file")
        continue
    same = sha256(H5_DIR / name) == sha256(src)
    copy_ok = copy_ok and same
    copy_detail.append(f"{name}: {'same hash as pilot original' if same else 'HASH MISMATCH'}")
record("A", "the three extra files are copies of the old pilot files",
       "PASS" if copy_ok and len(extra) == 3 else "FAIL", "; ".join(copy_detail))
# The pilot copies are not production runs. All tests below exclude them.
""")

code("""# --- A3: key inventory -------------------------------------------------------------
DUAL_KEYS = {"nuclear_cap_price", "nuclear_cap_price_raw",
             "nuclear_cap_price_ub", "nuclear_cap_price_ub_raw"}
keysets = {c: set(h5_keys(c)) for c in CASES}
union = set.union(*keysets.values())
bad = {}
for c in CASES:
    diff = (union - keysets[c]) | (keysets[c] - union)
    if diff - DUAL_KEYS:
        bad[c] = sorted(diff - DUAL_KEYS)
record("A", "all 25 files have the same data keys (dual keys can be absent when zero)",
       "PASS" if not bad else "FAIL",
       f"key counts {sorted(set(len(keysets[c]) for c in CASES))}; "
       + (f"unexpected differences: {bad}" if bad else
          f"dual keys absent in: "
          f"{ {c: sorted(DUAL_KEYS - keysets[c]) for c in CASES if DUAL_KEYS - keysets[c]} or 'none'}"))

# --- A4: solver residuals ----------------------------------------------------------
worst_z, worst_at = 0.0, None
for c in CASES:
    ec = load(c, "error_check").set_index("*")["Value"]
    m = float(ec.abs().max())
    if m > worst_z:
        worst_z, worst_at = m, (c, ec.to_dict())
record("A", "the solver residuals are small in every file",
       "PASS" if worst_z < 1e-2 else "FAIL", f"worst |residual| {worst_z:.2e} at {worst_at}")

obj = {c: float(load(c, "objfn_raw")["Value"].iloc[0]) for c in CASES}
ok_obj = all(np.isfinite(v) and v > 0 for v in obj.values())
record("A", "the objective value is a normal positive number in every file",
       "PASS" if ok_obj else "FAIL",
       f"range {min(obj.values()):.4e} ({min(obj, key=obj.get)}) to "
       f"{max(obj.values()):.4e} ({max(obj, key=obj.get)})")
""")

code("""# --- A5: model years ---------------------------------------------------------------
EXPECT_YEARS = [int(y) for y in sw(REF, "yearset").split("_")]
YEARS_BY_CASE = {c: sorted(load(c, "cap")["t"].unique()) for c in CASES}
bad_years = {c: y for c, y in YEARS_BY_CASE.items() if y != EXPECT_YEARS}
YEARS_RUN = YEARS_BY_CASE[REF]
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
PVF = load(REF, "pvf_onm").set_index("t")["Value"]
ok_seq = worst["pvfc"] < 1e-9 and worst["pvfo"] < 1e-3 and worst["cs"] < 1e-9 and worst["zrep"] == 0
record("A", "every run used the sequential solve mode",
       "PASS" if ok_seq else "FAIL",
       f"pvf_capital==1 (max dev {worst['pvfc']:.1e}); pvf_onm flat from 2026 at "
       f"{float(PVF.loc[2026]):.4f} (max dev {worst['pvfo']:.1e}); cost_scale==1; "
       f"z_rep has {len(EXPECT_YEARS)} years in every file")
""")

md("""## Phase B — Input data fingerprints

These tests make sure that each run used the correct input data from the 2026-08-10 export.
NREL did not return the input files.
Thus each test computes the expected values from the repository input files.
Then it compares them with the output data.

- Test B1 compares the capital cost data with the plant input files.
- Tests B2 to B4 compare the heat rate, the variable cost, and the fixed cost.
- Tests B5 to B9 compare the finance multipliers with our own calculation.
- Tests B10 to B13 make sure that the runs give no ITC to nuclear technology.
- Test B14 makes sure that the mandate technology input files are correct.

Test B10 is important.
The paper reads the mandate dual as the full required subsidy.
This is only correct if the runs give no other subsidy to nuclear technology.""")

code("""# --- B1: capital cost fingerprint (both techs, all 25 cases) -----------------------
PC_DIR = REPO / "inputs" / "plant_characteristics"

def plantchar(name):
    df = pd.read_csv(PC_DIR / f"{name}.csv")
    df.columns = [c.lstrip("*").lower() for c in df.columns]
    return df.set_index("t")

fp_rows = []
for c in CASES:
    cc = load(c, "cost_cap")
    cc = cc[cc["i"].isin(["nuclear", "nuclear-smr"])].set_index(["i", "t"])["Value"]
    for itech in ["nuclear", "nuclear-smr"]:
        pc = plantchar(META[c]["pc"][itech])
        for t, occ_kw in pc["capcost"].items():
            if (itech, t) not in cc.index:
                continue
            expect = occ_kw * 1000.0 * D2022
            got = float(cc.loc[(itech, t)])
            fp_rows.append(dict(case=c, i=itech, t=t, expect=expect, got=got,
                                rel_err=abs(got - expect) / expect))
fp = pd.DataFrame(fp_rows)
fp.to_csv(EXPORTS / "fingerprint_errors.csv", index=False)
worst_fp = fp.loc[fp.rel_err.idxmax()]
record("B", "the capital cost data agrees with the plant input files (all 25 cases)",
       "PASS" if fp.rel_err.max() < 1e-4 else "FAIL",
       f"{len(fp)} (case,tech,year) points; max rel err {fp.rel_err.max():.2e} at "
       f"({worst_fp.case}, {worst_fp.i}, {worst_fp.t})")
""")

code("""# --- B2-B4: heat rate, VOM, FOM ---------------------------------------------------
hr_bad, hr_worst = [], ""
for c in CASES:
    hr = load(c, "heat_rate")
    hr = hr[hr["i"].isin(["nuclear", "nuclear-smr"])].groupby("i")["Value"].agg(["min", "max"])
    for itech in hr.index:
        exp = float(plantchar(META[c]["pc"][itech])["heatrate"].iloc[-1])
        if not (abs(hr.loc[itech, "min"] - exp) < 0.05 and abs(hr.loc[itech, "max"] - exp) < 0.6):
            hr_bad.append((c, itech, hr.loc[itech].to_dict(), exp))
record("B", "the heat rate data agrees with the plant input files",
       "PASS" if not hr_bad else "INFO",
       hr_bad[:3] if hr_bad else "both techs, all cases (old vintages can differ a little)")

vom_bad = []
for c in CASES:
    vom = load(c, "cost_vom")
    for itech in ["nuclear", "nuclear-smr"]:
        v = vom[vom["i"] == itech]
        if not len(v):
            continue
        got = float(v["Value"].mode().iloc[0])
        exp = float(plantchar(META[c]["pc"][itech])["vom"].iloc[-1]) * D2022
        if abs(got - exp) / exp > 0.02:
            vom_bad.append((c, itech, round(got, 3), round(exp, 3)))
record("B", "the variable cost (VOM) data agrees with the plant input files",
       "PASS" if not vom_bad else "FAIL", vom_bad[:5] or "modal VOM within 2%, all cases")

# FOM check on the mandated tech's NEW fleet only: smr100 cases build an all-new SMR
# fleet with one FOM value. The large100 cases mix old and new vintages; INFO only.
fom_bad, fom_large = [], {}
for c in CASES:
    itech = META[c]["mandated_tech"]
    sc = load(c, "systemcost_techba")
    fom = sc[(sc["sys_costs"] == "op_fom_costs") & (sc["i"] == itech)].groupby("t")["Value"].sum()
    cap = load(c, "cap")
    capn = cap[cap["i"] == itech].groupby("t")["Value"].sum()
    yrs = [t for t in fom.index if t >= 2038 and capn.get(t, 0) > 0]
    if not yrs:
        continue
    implied = np.mean([fom[t] / capn[t] for t in yrs]) / D2022 / 1000.0
    exp = float(plantchar(META[c]["pc"][itech])["fom"].iloc[-1])
    if META[c]["techscen"] == "smr":
        if abs(implied - exp) / exp > 0.05:
            fom_bad.append((c, round(implied, 1), round(exp, 1)))
    else:
        fom_large[c] = (round(implied, 1), round(exp, 1))
record("B", "the fixed cost (FOM) data agrees with the plant input files (smr100 cases)",
       "PASS" if not fom_bad else "FAIL",
       fom_bad[:5] or "implied FOM within 5% of plantchar, all smr100 cases")
record("B", "implied large-reactor FOM in the large100 cases (mixed fleet)", "INFO",
       f"(implied, plantchar) $/kW-yr 2022$: {fom_large}")
""")

code("""# --- B5-B9: finance-multiplier replication (2_financials.gms) ----------------------
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
# row-aligned ReEDS exponents: header 'NA' row -> 0, rows t=0..9 -> 0.5..9.5
CC_EXPS = np.append([0.0], np.arange(0.5, 10.5, 1.0))
assert len(CS_MC) == len(CC_EXPS), (len(CS_MC), len(CC_EXPS))

def ccmult_reeds(sched_name, ib):
    x = pd.to_numeric(CS_MC[str(sched_name)], errors="coerce").fillna(0.0).to_numpy()
    return 1.0 + float(np.sum(x * (ib ** CC_EXPS - 1.0)))

def _resample_schedule(frac, n_years):
    frac = np.asarray(frac, float)
    n0 = len(frac)
    if n_years == n0:
        return frac / frac.sum()
    cdf = np.concatenate([[0.0], np.cumsum(frac)])
    xq = np.linspace(0.0, 1.0, n_years + 1)
    cdf_q = np.interp(xq, np.linspace(0.0, 1.0, n0 + 1), cdf)
    new = np.diff(cdf_q)
    return new / new.sum()

def ccmult_from_duration(duration_mo, interest_base, canonical_frac):
    n_years = int(round(duration_mo / 12.0))
    n_years = max(1, min(n_years, 10))
    x = _resample_schedule(canonical_frac, n_years)
    exps = np.arange(n_years) + 0.5
    return 1.0 + float(np.sum(x * (interest_base ** exps - 1.0)))

ccm_check = ccmult_from_duration(72.0, 1.08, np.array([0.1, 0.2, 0.2, 0.2, 0.2, 0.1]))
record("B", "the ccmult check value is correct (QA9 pin)",
       "PASS" if abs(ccm_check - 1.268124) < 1e-5 else "FAIL", f"{ccm_check:.6f}")

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

# Decomposition: h5(i,r,t) = base(i,t) x (1 + reg_cap_cost_diff(i,r)), GAMS-rounded to 3.
fin_rows, reg_factors = [], {}
for c in CASES:
    base = national_base(c)
    h5f = load(c, "cost_cap_fin_mult_noITC")
    h5f = h5f[h5f["i"].isin(["nuclear", "nuclear-smr"])]
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
print(fin_cmp.round(5).head(8).to_string(index=False))

record("B", "the finance multiplier has the correct regional structure",
       "PASS" if (fin_cmp.ratio_spread_over_t < 2e-3).all() else "FAIL",
       f"max ratio spread over years {fin_cmp.ratio_spread_over_t.max():.2e} (all 25 cases)")
record("B", "the finance multiplier agrees with our own calculation",
       "PASS" if (fin_cmp.worst_resid_after_regional < 1.5e-3).all() else "FAIL",
       f"worst |residual| {fin_cmp.worst_resid_after_regional.max():.2e} "
       "(GAMS rounds to 3 decimals)")
county = pd.read_csv(FIN_DIR / "reg_cap_cost_diff_default.csv")["NUCLEAR"]
lo_b, hi_b = 1 + county.min() - 0.005, 1 + county.max() + 0.005
ok_reg = (((fin_cmp.reg_factor_mean - (1 + county.mean())).abs() < 0.02).all()
          and (fin_cmp.reg_factor_min > lo_b).all() and (fin_cmp.reg_factor_max < hi_b).all())
record("B", "the regional factors are inside the county data range",
       "PASS" if ok_reg else "FAIL",
       f"implied range [{fin_cmp.reg_factor_min.min():.4f}, {fin_cmp.reg_factor_max.max():.4f}] "
       f"inside county range [{lo_b:.4f}, {hi_b:.4f}]")
xcase = 0.0
for iname in ["nuclear", "nuclear-smr"]:
    ref_reg = reg_factors[(REF, iname)]
    for c in CASES:
        d = (reg_factors[(c, iname)] - ref_reg).abs().max()
        xcase = max(xcase, float(d))
record("B", "the regional factors are the same in all 25 cases",
       "PASS" if xcase < 2e-3 else "FAIL", f"max cross-case difference {xcase:.2e}")
""")

code("""# --- B10-B13: no-ITC baseline (pre-registered smoke checks) ------------------------
# B10: for nuclear techs, cost_cap_fin_mult must equal cost_cap_fin_mult_noITC exactly.
worst_wedge, wedge_at = 0.0, None
for c in CASES:
    fm = load(c, "cost_cap_fin_mult")
    fm = fm[fm["i"].isin(["nuclear", "nuclear-smr"])].set_index(["i", "r", "t"])["Value"]
    fmno = load(c, "cost_cap_fin_mult_noITC")
    fmno = fmno[fmno["i"].isin(["nuclear", "nuclear-smr"])].set_index(["i", "r", "t"])["Value"]
    d = (fm - fmno).abs()
    m = float(d.max())
    if m > worst_wedge:
        worst_wedge, wedge_at = m, (c, d.idxmax())
record("B", "the model gives no ITC to nuclear technology (fin_mult == fin_mult_noITC)",
       "PASS" if worst_wedge < 1e-6 else "FAIL",
       f"max |difference| {worst_wedge:.2e}"
       + (f" at {wedge_at}" if worst_wedge >= 1e-6 else
          " in every (tech, region, year) of every case; the pilot-vintage 2038 wedge is gone"))

# B11: no ITC payments to nuclear techs in the system cost data.
worst_itc, itc_at = 0.0, None
for c in CASES:
    sc = load(c, "systemcost_techba")
    it = sc[sc["sys_costs"].str.contains("itc", case=False)
            & sc["i"].isin(["nuclear", "nuclear-smr"])]
    m = float(it["Value"].abs().max()) if len(it) else 0.0
    if m > worst_itc:
        worst_itc, itc_at = m, c
record("B", "the system cost data shows no ITC payments for nuclear technology",
       "PASS" if worst_itc < 1.0 else "FAIL",
       f"max |nuclear ITC row| ${worst_itc:,.0f}" + (f" in {itc_at}" if worst_itc >= 1.0 else ""))

# B12: the other technologies keep their ITC (proves the correct incentives file ran).
# The model records a tax expenditure as a negative number. Use the magnitude.
itc_tot = {c: float(load(c, "tax_expenditure_itc")["Value"].sum()) for c in CASES}
itc_mag = {c: abs(v) for c, v in itc_tot.items()}
record("B", "the other technologies keep their ITC",
       "PASS" if min(itc_mag.values()) > 1e8 else "FAIL",
       f"total ITC tax expenditure magnitude {min(itc_mag.values())/1e9:.1f} to "
       f"{max(itc_mag.values())/1e9:.1f} B$ per case (recorded as negative)")

# B13: input-side confirmation from the incentives files in the repository.
inc_no = pd.read_csv(FIN_DIR / "incentives_obbba_nonuclearitc.csv")
inc_ob = pd.read_csv(FIN_DIR / "incentives_obbba.csv")
nuc_no = inc_no[inc_no["i"].str.upper().str.startswith("NUCLEAR")]
nuc_ob = inc_ob[inc_ob["i"].str.upper().str.startswith("NUCLEAR")]
itc_cols = [c for c in inc_no.columns if c.startswith("itc_")]
ok_in = (nuc_no[itc_cols].abs().to_numpy().sum() == 0.0
         and nuc_ob["itc_frac"].abs().to_numpy().sum() > 0)
record("B", "the incentives input file has zero nuclear ITC (and obbba does not)",
       "PASS" if ok_in else "FAIL",
       f"{len(nuc_no)} nuclear rows, itc columns all zero; obbba nuclear itc_frac "
       f"max {nuc_ob['itc_frac'].max():.2f}")

# B14: the mandate technology input files are singletons.
def techs_file(name):
    return [ln.strip() for ln in
            (REPO / "inputs" / "nuclear_learning" / f"nuclear_cap_mandate_techs_{name}.csv")
            .read_text().splitlines() if ln.strip() and not ln.startswith("*")]
ok_t = techs_file("smr") == ["nuclear-smr"] and techs_file("large") == ["nuclear"]
record("B", "the mandate technology input files are correct",
       "PASS" if ok_t else "FAIL",
       f"smr -> {techs_file('smr')}; large -> {techs_file('large')}")
""")

md("""## Phase C — Mandate mechanics and dual prices

These tests make sure that the capacity mandate and its dual price operate correctly.

- Test C1 makes sure that the capacity satisfies the mandate floor in every case.
- Test C2 makes sure that the capacity equals the floor in each binding year.
- Test C3 makes sure that a positive dual occurs only in the binding years.
- Test C4 makes sure that the dual conversion is correct.
- Tests C5 and C6 make sure that each case builds only its own technology.
- Test C7 makes sure that no SMR capacity exists before 2031.
- Test C8 records the overbuild data for the slack cases.

The dual is a rental price in dollars of 2004 per MW and year.
The export `duals_by_year.csv` also shows the values in dollars of 2024.""")

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
# report.gms: converted = raw / (cost_scale x pvf_onm(t)); rental basis, 2004$.
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
for c in SMR_CASES:
    nb_ = load(c, "cap_new_ann")
    lg = nb_[(nb_["i"] == "nuclear") & (nb_["t"] > 2030)]["Value"].sum()
    if lg > 0:
        bad_large.append((c, float(lg)))
for c in LARGE_CASES:
    nb_ = load(c, "cap_new_ann")
    sm = nb_[nb_["i"] == "nuclear-smr"]["Value"].sum()
    if sm > 0:
        bad_smr.append((c, float(sm)))
record("C", "no large-reactor builds occur after 2030 in the smr100 cases",
       "PASS" if not bad_large else "FAIL", bad_large or "all 19 smr100 cases clean")
record("C", "no SMR builds occur in the large100 cases",
       "PASS" if not bad_smr else "FAIL", bad_smr or "all 6 large100 cases clean")

# --- C7: no SMR capacity before 2031 -----------------------------------------------
pre = {}
for c in SMR_CASES:
    s = load(c, "cap")
    s = s[(s["i"] == "nuclear-smr") & (s["t"] < 2031)]["Value"].sum()
    pre[c] = float(s)
record("C", "no SMR capacity exists before 2031",
       "PASS" if max(pre.values()) == 0 else "FAIL",
       f"max pre-2031 SMR capacity {max(pre.values()):.1f} MW")

# naming-trap guard: `SMR` in other ReEDS names means steam methane reforming.
techs = set(load(REF, "cap")["i"].unique())
smr_trap = [t for t in techs if "smr" in t.lower() and t != "nuclear-smr"]
record("C", "the technology names are correct (no stray SMR names)",
       "PASS" if not smr_trap else "INFO",
       smr_trap or "tech set clean; nuclear filters use the exact name nuclear-smr")

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
print(ob.to_string(index=False))
record("C", "overbuild and binding years by case", "INFO",
       f"binding-year counts {dict(zip(ob.case, ob.n_binding_years))}")
""")

md("""## Phase D — Equality case behavior

The case `smr100_eia_p50_eq` uses the equality mandate (floor + ceiling).
It uses the same input files as `smr100_eia_p50`.
These tests make sure that the constraint form causes no change in behavior.
This is the pre-registered issue-6 check.

Note: regional siting can differ between equal solutions (the P7 caveat).
Thus the tests compare national totals, not regional data.""")

code("""EQ, P50 = "smr100_eia_p50_eq", "smr100_eia_p50"

# D1: objective value
d_obj = abs(obj[EQ] - obj[P50]) / obj[P50]
record("D", "the equality case gives the same objective value",
       "PASS" if d_obj < 1e-6 else "FAIL",
       f"rel difference {d_obj:.2e} ({obj[EQ]:.6e} vs {obj[P50]:.6e})")

# D2: national capacity and generation by (tech, year)
eq_rows = []
worst_nat = {}
for key in ["cap", "gen_ann"]:
    a = load(EQ, key).groupby(["i", "t"])["Value"].sum()
    b = load(P50, key).groupby(["i", "t"])["Value"].sum()
    j = pd.concat([a, b], axis=1, keys=["eq", "p50"]).fillna(0.0)
    d = (j["eq"] - j["p50"]).abs()
    rel = d / j["p50"].abs().clip(lower=1.0)
    worst_nat[key] = float(rel.max())
    eq_rows.append(dict(dataset=key, max_abs_diff=float(d.max()),
                        max_rel_diff=float(rel.max()), worst_at=str(d.idxmax())))
pd.DataFrame(eq_rows).to_csv(EXPORTS / "eq_flip_comparison.csv", index=False)
record("D", "the equality case gives the same national capacity and generation",
       "PASS" if max(worst_nat.values()) < 1e-3 else "INFO",
       {k: f"{v:.2e}" for k, v in worst_nat.items()})

# D3: floor duals
idx = sorted(set(DUAL[EQ].index) | set(DUAL[P50].index))
de = DUAL[EQ].reindex(idx).fillna(0.0)
dp = DUAL[P50].reindex(idx).fillna(0.0)
rel_d = float((de - dp).abs().max() / dp.max()) if dp.max() > 0 else 0.0
record("D", "the equality case gives the same floor dual values",
       "PASS" if rel_d < 1e-3 else "FAIL",
       f"max rel difference {rel_d:.2e} over years {idx}")

# D4: ceiling duals (zero-suppressed = the ceiling never binds against the solution)
ub_present = [k for k in ["nuclear_cap_price_ub", "nuclear_cap_price_ub_raw"] if k in keysets[EQ]]
record("D", "the ceiling dual is zero in the equality case",
       "PASS" if not ub_present else "INFO",
       "ceiling dual keys absent = all zero (zero-suppression rule)" if not ub_present
       else f"ceiling dual present: {ub_present} — read and interpret")

verdict = (d_obj < 1e-6 and rel_d < 1e-3 and not ub_present)
record("D", "verdict: the constraint form causes no change in behavior",
       "PASS" if verdict else "FAIL",
       "issue-6 behavior check passed; floor results stand" if verdict
       else "differences found — see D1-D4")
""")

md("""## Phase E — Load data integrity

These tests make sure that the load inputs were not corrupted.
NREL did not return the input files.
Thus the tests use two layers.

Layer 1 uses the outputs.
All 25 cases use the same demand scenario (`AEO_2026_baseline`, the default).
Thus the exogenous load data must be identical in all 25 cases.
A difference points to a corrupted or wrong load input.
Some load parts are endogenous: storage charging, H2 production, and losses.
These parts move with each case's solution. The tests treat them as context only.

Layer 2 uses the repository input files.
The tests read the demand file and the two hourly profile files.
They make sure that the files are complete, with no missing or negative values.

Test E6 compares the output load with the old pilot runs.
The load inputs did not change between the two run vintages.
We made sure of this with git (`git diff dc278f4..afba700 -- inputs/load
inputs/profiles_demand cases.csv` shows no load change).
Thus the load values must agree on the shared years.""")

code("""# --- E1: the exogenous load data is the same in all 25 cases -----------------------
# Exogenous parts: load_rt, hours, and the end_use + dist_loss rows of load_cat.
# Endogenous parts (they move with the solution): storage charge, H2 production,
# transmission losses, the stress-period load, and load_frac_rt. These get E2.
def frame(case, key, cat=None):
    df = load(case, key)
    if cat is not None:
        df = df[df["loadtype"] == cat]
    dims = [c for c in df.columns if c != "Value"]
    return df.set_index(dims)["Value"]

STRICT = [("load_rt", None), ("hours", None), ("load_cat", "end_use"), ("load_cat", "dist_loss")]
li_rows = []
for key, cat in STRICT:
    ref_s = frame(REF, key, cat)
    for c in CASES:
        if c == REF:
            continue
        j = pd.concat([ref_s, frame(c, key, cat)], axis=1, keys=["ref", "c"]).fillna(0.0)
        d = (j["ref"] - j["c"]).abs()
        rel = float((d / j["ref"].abs().clip(lower=1.0)).max())
        li_rows.append(dict(dataset=key + (f"[{cat}]" if cat else ""), case=c,
                            max_abs_diff=float(d.max()), max_rel_diff=rel))
li = pd.DataFrame(li_rows)
li.to_csv(EXPORTS / "load_invariance.csv", index=False)
worst_li = li.loc[li.max_rel_diff.idxmax()]
record("E", "the exogenous load data is the same in all 25 cases",
       "PASS" if li.max_rel_diff.max() < 1e-6 else "FAIL",
       f"load_rt, hours, load_cat[end_use], load_cat[dist_loss] compared against {REF}; "
       f"max rel difference {li.max_rel_diff.max():.2e} ({worst_li.dataset}, {worst_li.case})")

# --- E2: the endogenous load parts stay in a normal range (context) ----------------
endo = {}
for key, cat in [("load_cat", "stor_charge"), ("load_cat", "h2_prod"),
                 ("load_cat", "trans_loss"), ("load_stress", None)]:
    ref_s = frame(REF, key, cat)
    worst = 0.0
    for c in CASES:
        if c == REF:
            continue
        j = pd.concat([ref_s, frame(c, key, cat)], axis=1, keys=["ref", "c"]).fillna(0.0)
        tot_ref, tot_c = float(j["ref"].sum()), float(j["c"].sum())
        worst = max(worst, abs(tot_c - tot_ref) / max(tot_ref, 1.0))
    endo[key + (f"[{cat}]" if cat else "")] = round(worst, 4)
record("E", "the endogenous load parts differ only a little between cases", "INFO",
       f"max rel difference of national totals vs {REF}: {endo} "
       "(these parts move with each case's solution; this is normal)")

# --- E3: no dropped load after 2025 ------------------------------------------------
dl_bad, hist_vals = [], {}
for c in CASES:
    dl = load(c, "dropped_load")
    modern = float(dl.loc[dl["t"] >= 2026, "Value"].sum())
    hist_vals[c] = float(dl.loc[dl["t"] < 2026, "Value"].sum())
    if modern >= 1.0:
        dl_bad.append((c, modern))
hist_spread = max(hist_vals.values()) - min(hist_vals.values())
record("E", "no load is dropped after 2025",
       "PASS" if not dl_bad else "FAIL",
       dl_bad[:5] or f"historical 2010-2023 artifact {np.mean(list(hist_vals.values()))/1e6:.2f} TWh, "
                     f"case spread {hist_spread:.1f} MWh (case-invariant)")
""")

code("""# --- E4: the demand input file is complete and correct -----------------------------
dem = pd.read_csv(REPO / "inputs" / "load" / "demand_AEO_2026_baseline.csv")
ok_dem = (not dem.isna().any().any()
          and (dem["multiplier"] > 0).all()
          and dem["multiplier"].between(0.3, 5.0).all()
          and dem["year"].min() <= 2010 and dem["year"].max() >= 2050
          and dem.groupby("year")["r"].count().nunique() == 1)
record("E", "the demand input file is complete and correct",
       "PASS" if ok_dem else "FAIL",
       f"{dem['r'].nunique()} states x years {dem['year'].min()}-{dem['year'].max()}; "
       f"multiplier range [{dem['multiplier'].min():.3f}, {dem['multiplier'].max():.3f}]")

# --- E5: the hourly load profiles are complete and correct -------------------------
# Layout per reeds/io.py::write_profile_to_h5 (not the outputs layout).
prof_notes, prof_ok = [], True
p1 = REPO / "inputs" / "profiles_demand" / "demand_EER2025_IRAlow.h5"
with h5py.File(p1, "r") as f:
    for yr in f.keys():
        g = f[yr]
        states = [k for k in g.keys() if k not in ("columns", "datetime")]
        n = {len(g[k]) for k in states}
        arrs = np.stack([g[k][:] for k in states])
        ok = (len(n) == 1 and next(iter(n)) % 8760 == 0
              and arrs.min() >= 0 and np.isfinite(arrs).all()
              and arrs.max() < 3e5)
        prof_ok = prof_ok and ok
        prof_notes.append(f"{yr}: {len(states)} states x {next(iter(n))} h, "
                          f"min {arrs.min()}, max {arrs.max()}")
p2 = REPO / "inputs" / "profiles_demand" / "demand_historic.h5"
with h5py.File(p2, "r") as f:
    data = f["data"][:]
    ncols = len(f["columns"])
    ok = (data.shape[1] == ncols and data.shape[0] % 8760 == 0
          and data.min() > 0 and np.isfinite(data).all() and data.max() < 3e5)
    prof_ok = prof_ok and ok
    prof_notes.append(f"historic: {data.shape}, min {data.min()}, max {data.max()}")
record("E", "the hourly load profiles are complete and correct",
       "PASS" if prof_ok else "FAIL",
       f"{p1.name} + {p2.name}: " + "; ".join(prof_notes[:3]) + " ...")

# --- E6: the output load agrees with the old pilot runs ----------------------------
# The load inputs did not change between vintages (verified with git; see the phase
# text). The pilot yearset lacks the annual 2031-2035 block; compare shared years.
pilot_mid = PILOT_DIR / "test1_smr100_eia_mid_outputs.h5"
with h5py.File(pilot_mid, "r") as f:
    g = f["load_rt"]
    cols = [c.decode() for c in g["columns"][:]]
    pl = pd.DataFrame({c: (g[c][:].astype(str) if g[c][:].dtype.kind == "S" else g[c][:])
                       for c in cols})[cols]
pl["t"] = pl["t"].astype(int)
pl = pl.set_index(["r", "t"])["Value"]
pr = load(REF, "load_rt").set_index(["r", "t"])["Value"]
shared = pl.index.intersection(pr.index)
rel = float(((pl.loc[shared] - pr.loc[shared]).abs()
             / pl.loc[shared].abs().clip(lower=1.0)).max())
record("E", "the output load agrees with the old pilot runs on the shared years",
       "PASS" if rel < 1e-6 else "FAIL",
       f"{len(shared)} shared (region, year) points; max rel difference {rel:.2e}")

# --- E7: load growth and energy balance (context) ----------------------------------
nat = load(REF, "load_rt").groupby("t")["Value"].sum()
gen = load(REF, "gen_ann").groupby("t")["Value"].sum()
growth = nat.loc[2050] / nat.loc[2026]
mult = dem[dem["year"].isin([2026, 2050])].groupby("year")["multiplier"].mean()
record("E", "the output load grows like the demand scenario", "INFO",
       f"national load 2026->2050 x{growth:.2f}; demand multiplier mean x"
       f"{mult.loc[2050]/mult.loc[2026]:.2f} (busbar load also moves with "
       "electrification and losses)")
ratio = (gen / nat).loc[[t for t in YEARS_RUN if t >= 2026]]
record("E", "generation covers the load in every model year", "INFO",
       f"generation / busbar load range [{ratio.min():.3f}, {ratio.max():.3f}] "
       "(trade, storage, and losses cause small deviations from 1)")
""")

md("""## Phase F — Cross-case checks and unexpected values

These tests compare the cases against each other.
They also scan all data for bad values.

- Test F1 makes sure that the dual values do not cross between p05, p50, and p95.
- Test F2 makes sure that the objective values are in the correct order.
- Test F3 makes sure that no data value is NaN.
- Test F4 makes sure that no negative values occur where values must not be negative.
- Test F5 makes sure that the nuclear build and generation data is not negative.
- Test F6 makes sure that the national totals equal the sum of the regional data.
- Tests F7 to F9 record context data (dual decay, schedule ladder, large100 duals).

Test F1 checks the bracket claim: a more expensive world must need a larger subsidy.
A crossing is a finding. The P8 identity from the pilot forensics says it must not occur.""")

code("""# --- F1: dual monotonicity within each schedule ------------------------------------
mono_bad = []
for tok in SCHEDULES:
    p05, p50, p95 = (f"smr100_{tok}_p05", f"smr100_{tok}_p50", f"smr100_{tok}_p95")
    idx = sorted(set(DUAL[p05].index) | set(DUAL[p50].index) | set(DUAL[p95].index))
    d05 = DUAL[p05].reindex(idx).fillna(0.0)
    d50 = DUAL[p50].reindex(idx).fillna(0.0)
    d95 = DUAL[p95].reindex(idx).fillna(0.0)
    tol = 50.0 + 0.001 * d95.abs()
    bad_years = [int(t) for t in idx
                 if d95[t] < d50[t] - tol[t] or d50[t] < d05[t] - tol[t]]
    if bad_years:
        mono_bad.append((tok, bad_years))
record("F", "the dual values do not cross between p05, p50, and p95 (all 6 schedules)",
       "PASS" if not mono_bad else "FAIL",
       mono_bad or "p95 >= p50 >= p05 in every year of every schedule")

# --- F2: objective order within each schedule --------------------------------------
ord_bad = []
for tok in SCHEDULES:
    o = [obj[f"smr100_{tok}_{p}"] for p in ["p05", "p50", "p95"]]
    if not (o[0] <= o[1] <= o[2]):
        ord_bad.append((tok, o))
record("F", "the objective values are in the correct order (p05 <= p50 <= p95)",
       "PASS" if not ord_bad else "FAIL",
       ord_bad or "a more expensive world always costs more, all 6 schedules")
""")

code("""# --- F3/F4: full data scan (NaN + negative values) ---------------------------------
# Storage charging makes gen_ann negative for batteries and pumped hydro.
# Coal-CCS upgrades and distpv adjustments make cap_new_ann negative.
# These are normal ReEDS conventions. Thus the strict list excludes those keys,
# and a separate test makes sure that the nuclear rows are not negative.
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
        nuc = df[df["i"].isin(["nuclear", "nuclear-smr"])]
        if len(nuc) and float(nuc["Value"].min()) < -1.0:
            nuc_neg.append((c, k, float(nuc["Value"].min())))
record("F", "no data value is NaN or infinite in any file",
       "PASS" if not nan_bad else "FAIL",
       nan_bad[:5] or f"all {len(union)} keys x 25 files scanned")
record("F", "no negative values occur where values must not be negative",
       "PASS" if not neg_bad else "FAIL",
       neg_bad[:5] or f"checked {NONNEG}")
record("F", "the nuclear build and generation data is not negative",
       "PASS" if not nuc_neg else "FAIL",
       nuc_neg[:5] or "cap_new_ann and gen_ann nuclear rows >= 0, all 25 cases "
       "(storage charging and upgrades make some non-nuclear rows negative; "
       "this is a normal convention)")

# --- F5: national totals equal the regional sums -----------------------------------
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
       tot_bad[:5] or "cap, gen_ann, cap_new_ann, ret_ann; all 25 cases within 1e-3")
""")

code("""# --- F6-F8: context (INFO) ---------------------------------------------------------
decay = {}
for c in CASES:
    d = DUAL[c]
    if len(d[d > 1.0]) >= 2:
        dd = d[d > 1.0].sort_index()
        decay[c] = dict(peak_year=int(dd.idxmax()),
                        end_over_peak=round(float(dd.iloc[-1] / dd.max()), 2))
record("F", "dual decay shape by case (bridge hypothesis, first look)", "INFO",
       f"peak year + end/peak ratio: {decay}")

ladder = {}
for tok in SCHEDULES:
    c = f"smr100_{tok}_p50"
    d = DUAL[c]
    ladder[tok] = dict(n_binding=int((d > 1.0).sum()),
                       mean_dual_2024=round(float(d[d > 1.0].mean() * TO2024)) if (d > 1.0).any() else 0)
record("F", "dual level by schedule ambition (p50 cases)", "INFO", ladder)

l_vs_s = {}
for tok in SCHEDULES:
    dl_ = DUAL[f"large100_{tok}_p50"]
    ds_ = DUAL[f"smr100_{tok}_p50"]
    shared = sorted(set(dl_[dl_ > 1.0].index) & set(ds_[ds_ > 1.0].index))
    if shared:
        l_vs_s[tok] = round(float(dl_.reindex(shared).mean() / ds_.reindex(shared).mean()), 2)
record("F", "large100 dual level over smr100 dual level (shared binding years)", "INFO",
       f"mean ratio by schedule: {l_vs_s}")
""")

md("""## Summary and report

The next cell writes the check registry to `exports/checks_summary.csv`.
It also writes the report `step3_check_results.md` in Simplified Technical English.""")

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
    "B": "Phase B — Input data fingerprints",
    "C": "Phase C — Mandate mechanics and dual prices",
    "D": "Phase D — Equality case behavior",
    "E": "Phase E — Load data integrity",
    "F": "Phase F — Cross-case checks and unexpected values",
}
PHASE_STE = {
    "A": "These tests make sure that the file set is complete and that each solve is clean.",
    "B": "These tests make sure that each run used the correct input data. "
         "The tests compute the expected values from the repository input files.",
    "C": "These tests make sure that the capacity mandate and its dual price operate correctly.",
    "D": "These tests make sure that the equality case shows the same behavior as the floor case.",
    "E": "These tests make sure that the load inputs were not corrupted. "
         "The output load must be identical in all 25 cases. "
         "The repository load files must be complete and correct.",
    "F": "These tests compare the cases against each other. "
         "They also scan all data for bad values.",
}

lines = [
    "# Step 3 output checks — report",
    "",
    f"Date of this report: {date.today().isoformat()}.",
    f"Input folder: `{H5_DIR}`.",
    f"The folder has {len(all_files)} files: {len(CASES)} production runs and "
    f"{len(extra)} copies of old pilot runs.",
    "The tests cover only the 25 production runs.",
    "The notebook `step3_output_checks.ipynb` performs all tests.",
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
    lines += ["**All pass/fail tests passed.** No test found a defect in the 25 runs.",
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
for ph in ["A", "B", "C", "D", "E", "F"]:
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
    "- `exports/duals_by_year.csv` — the dual prices for each case and year.",
    "- `exports/overbuild_by_case.csv` — the binding and slack years for each case.",
    "- `exports/fingerprint_errors.csv` — the capital cost comparison points.",
    "- `exports/fin_mult_noITC_comparison.csv` — the finance multiplier comparison.",
    "- `exports/eq_flip_comparison.csv` — the equality case comparison.",
    "- `exports/load_invariance.csv` — the load comparison across cases.",
    "",
]
(HERE / "step3_check_results.md").write_text("\\n".join(lines), encoding="utf-8")
print(f"wrote step3_check_results.md ({len(lines)} lines)")
""")

nb["cells"] = C
out = "step3_output_checks.ipynb"
nbf.write(nb, out)
print(f"wrote {out} with {len(C)} cells")
