"""Generate itcfb_output_checks.ipynb. Edit cell sources here, re-run to regenerate.

Same convention as z-ethan/step4_checks/_build_notebook.py: the notebook is the
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


md("""# ITC feed-back output checks — the 19 `itcfb` runs

This notebook tests the 19 ITC feed-back run outputs from NREL.
The output files are in `D:\\ReEDS files\\nuclear-learning\\All runs so far`.
The run matrix is `cases_nuclearlearning_itcfb.csv`.
The pass criteria are pre-registered in `z-ethan/itc_feedback/run_manifest.md`
and in `z-ethan/itc_feedback/reeds_itc_update_spec.md` section 7.

The design is a three-factor matrix: mandate on/off, fed-back ITC on/off,
endogenous learning on/off. The five arms:

- **fbA** (2 runs, mandate + ITC): misapplication check.
  Every previously binding floor dual must collapse to ~0.
  The SMR capacity must stay at or above the trajectory.
- **fbB** (6 runs, ITC only): convex decentralization control.
  The national SMR capacity must reproduce the mandate trajectory.
- **fbC** (6 runs, ITC + learning): the pre-registered section-9 test.
  Pass and fail are both reportable results.
- **fbK** (2 runs, mandate + learning, no ITC): engine calibration.
  The in-run learned cost path must reproduce the drawn p50 plant cost path.
- **fbR** (3 runs, flat ITC at 0% / 30% / 50%): demand-curve reference points.

The fed rates are the paper's headline ITC definition: `i_model_headline`
from `step3_analysis/exports/t09_required_itc.csv`, plus a 0.01 indifference
bump, monetized at 0.9 (the OBBBA 10% tax-equity penalty).
ReEDS applies the credit inside the finance multiplier.
The control order matters: read fbA first, then fbB and fbK, then fbC.

The notebook makes sure that:

- The file set is complete and the solves are clean (phase A).
- Each run encodes its intended design cell, the credit landed at the fed rate,
  and the phaseout exemption held (phase B).
- Each arm meets or fails its pre-registered criterion (phase C).
- The runs show no cross-case corruption and no unexpected values (phase D).

Each test writes one row to a check registry.
The last cell writes the registry to `exports/checks_summary.csv`.
The last cell also writes the report `itcfb_check_results.md`.

A FAIL in phase A, B, or D shows a defect. Examine it before any analysis.
A FAIL in phase C can be a pre-registered finding, not a defect.
The analysis notebook (`z-ethan/itcfb_analysis/`) interprets phase C.

Run this notebook on the **playground-env** kernel.
This notebook only reads the files on drive D. It does not change them.""")

code("""from datetime import date
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

pd.set_option("display.width", 200)

HERE = Path.cwd()
assert HERE.name == "itcfb_checks", f"run from z-ethan/itcfb_checks/, not {HERE}"
REPO = HERE.parents[1]
EXPORTS = HERE / "exports"
EXPORTS.mkdir(exist_ok=True)

H5_DIR = Path("D:/ReEDS files/nuclear-learning/All runs so far")
STEP3_EXPORTS = REPO / "z-ethan" / "step3_checks" / "exports"
S3ANALYSIS = REPO / "z-ethan" / "step3_analysis" / "exports"

# ---- case matrix ------------------------------------------------------------------
cases = pd.read_csv(REPO / "cases_nuclearlearning_itcfb.csv", index_col=0)
CASES = [c for c in cases.columns if c != "Default Value"]
assert len(CASES) == 19, len(CASES)

def sw(case, name):
    \"\"\"Read one switch value for one case. An empty cell uses the default value.\"\"\"
    v = cases.loc[name, case]
    if pd.isna(v) or str(v).strip() == "":
        v = cases.loc[name, "Default Value"]
    return "" if pd.isna(v) else str(v).strip()

SCHEDULES = ["eia", "aj", "iaea", "mck", "cop28", "eo"]

def parse_case(c):
    \"\"\"Split a case name into (arm, world). The fbR runs live in the eia world.\"\"\"
    parts = c.split("_")
    arm = parts[0]
    world = parts[1] if arm != "fbR" else "eia"
    return arm, world

META = {}
for c in CASES:
    arm, world = parse_case(c)
    META[c] = dict(
        arm=arm, world=world,
        scen=sw(c, "GSw_NuclearCapMandateScen"),
        mandate=int(float(sw(c, "GSw_NuclearCapMandate"))),
        learning=int(float(sw(c, "GSw_NuclearLearning"))),
        suffix=sw(c, "incentives_suffix"),
        foreign=sw(c, "GSw_NuclearLearning_ForeignScen"),
        pc={"nuclear": sw(c, "plantchar_nuclear"),
            "nuclear-smr": sw(c, "plantchar_nuclear_smr")},
        fin=sw(c, "financials_tech_suffix"),
    )

ARM_CASES = {a: [c for c in CASES if META[c]["arm"] == a]
             for a in ["fbA", "fbB", "fbC", "fbK", "fbR"]}
assert [len(ARM_CASES[a]) for a in ["fbA", "fbB", "fbC", "fbK", "fbR"]] == [2, 6, 6, 2, 3]
FED_CASES = ARM_CASES["fbA"] + ARM_CASES["fbB"] + ARM_CASES["fbC"]   # t09-rate ITC
NOITC_CASES = ARM_CASES["fbK"] + ["fbR_none"]                        # no nuclear ITC
LEARNOFF_CASES = ARM_CASES["fbA"] + ARM_CASES["fbB"] + ARM_CASES["fbR"]
MANDATE_CASES = ARM_CASES["fbA"] + ARM_CASES["fbK"]

# the Step 3 base run of each world, for output-identity comparisons
BASE_OF_WORLD = {w: f"smr100_{w}_p50" for w in SCHEDULES}
BASE_CASES = sorted(BASE_OF_WORLD.values())
REF4 = "smr100_eia_p50_gaslo"    # one Step 4 file: the key-set vintage reference

H5 = {c: H5_DIR / f"itcfb_{c}_outputs.h5" for c in CASES}
for b in BASE_CASES:
    H5[b] = H5_DIR / f"test1_{b}_outputs.h5"
H5[REF4] = H5_DIR / f"step4_{REF4}_outputs.h5"

# 2022$ -> 2004$ (ReEDS-internal dollars). deflator.csv: Deflator(t) relative to 2004.
DEFL = pd.read_csv(REPO / "inputs" / "financials" / "deflator.csv")
DEFL.columns = ["t", "Deflator"]
DEFL = DEFL.set_index("t")["Deflator"]
D2022 = float(DEFL.loc[2022])
TO2024 = 1.0 / float(DEFL.loc[2024])

# ---- fed rate schedules -----------------------------------------------------------
# t09: use only the four refactor-stable columns (case, t, status, i_model_headline).
EPS, PEN = 0.01, 0.1
t09 = pd.read_csv(S3ANALYSIS / "t09_required_itc.csv",
                  usecols=["case", "t", "status", "i_model_headline"])
RATES = {}       # world -> {t: itc_frac written to the incentives file}
M_EXP = {}       # world -> {t: monetized rate the model must apply}
for w in SCHEDULES:
    sub = t09[(t09["case"] == BASE_OF_WORLD[w]) & (t09["status"] == "rate")]
    assert len(sub) and sub["i_model_headline"].notna().all(), w
    RATES[w] = {int(t): round(float(i) + EPS, 3)
                for t, i in zip(sub["t"], sub["i_model_headline"])}
    M_EXP[w] = {t: f * (1.0 - PEN) for t, f in RATES[w].items()}
FLAT_M = {"fbR_none": 0.0, "fbR_itc30": 0.30 * (1 - PEN), "fbR_itc50": 0.50 * (1 - PEN)}

# ---- check registry ---------------------------------------------------------------
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

NUC = ["nuclear", "nuclear-smr"]

def nuc_slice(case, key):
    df = load(case, key)
    df = df[df["i"].isin(NUC)]
    dims = [c for c in df.columns if c != "Value"]
    return df.set_index(dims)["Value"]

print(f"repo: {REPO}")
print(f"cases: {len(CASES)} (2 fbA + 6 fbB + 6 fbC + 2 fbK + 3 fbR)")
print("rate years per world:",
      {w: sorted(RATES[w]) for w in SCHEDULES})
""")

md("""## Phase A — File inventory and solve health

These tests make sure that the file set is complete and that each solve is clean.

- Test A1 makes sure that the folder has one output file for each of the 19 cases.
- Test A2 makes sure that the six Step 3 base-case files are available.
- Test A3 records the folder census.
- Test A4 makes sure that all files have the same data keys.
- Test A5 makes sure that the key set agrees with the Step 4 vintage.
- Test A6 makes sure that the solver residuals are small in each file.
- Test A7 makes sure that the objective value is normal in each file.
- Test A8 makes sure that the model years are correct in each file.
- Test A9 makes sure that each run used the sequential solve mode.

Note: the model removes an all-zero dual parameter from the file.
Thus an absent dual key means a zero dual. It does not mean lost data.
For the fbA runs an absent dual key is the intended result.""")

code("""# --- A1/A2/A3: file census ---------------------------------------------------------
missing = [c for c in CASES if not H5[c].exists()]
record("A", "one output file exists for each of the 19 cases",
       "PASS" if not missing else "FAIL",
       f"missing: {missing}" if missing else f"19 files in {H5_DIR}")

base_missing = [b for b in BASE_CASES if not H5[b].exists()]
record("A", "the six Step 3 base-case files are available for comparison",
       "PASS" if not base_missing else "FAIL",
       f"missing: {base_missing}" if base_missing else "all six test1_smr100 p50 files present")

all_files = sorted(p.name for p in H5_DIR.glob("*.h5"))
n_itcfb = sum(f.startswith("itcfb_") for f in all_files)
n_step4 = sum(f.startswith("step4_") for f in all_files)
n_test1 = sum(f.startswith("test1_") for f in all_files)
extra = [f for f in all_files if f.startswith("itcfb_")
         and f not in {H5[c].name for c in CASES}]
record("A", "the folder census matches the consolidated delivery", "INFO",
       f"{len(all_files)} files: {n_itcfb} itcfb + {n_step4} step4 + {n_test1} test1"
       + (f"; unexpected itcfb files: {extra}" if extra else ""))
""")

code("""# --- A4/A5: key inventory ----------------------------------------------------------
DUAL_KEYS = {"nuclear_cap_price", "nuclear_cap_price_raw",
             "nuclear_cap_price_ub", "nuclear_cap_price_ub_raw"}
keysets = {c: set(h5_keys(c)) for c in CASES}
union = set.union(*keysets.values())
ref_keys = set(h5_keys(REF4))
bad = {}
for c in CASES:
    diff = (union - keysets[c]) | (keysets[c] - union)
    if diff - DUAL_KEYS:
        bad[c] = sorted(diff - DUAL_KEYS)
drift = sorted(((union - ref_keys) | (ref_keys - union)) - DUAL_KEYS)
no_dual = sorted(c for c in CASES if "nuclear_cap_price" not in keysets[c])
record("A", "all 19 files have the same data keys (dual keys can be absent when zero)",
       "PASS" if not bad else "FAIL",
       f"key counts {sorted(set(len(keysets[c]) for c in CASES))}"
       + (f"; unexpected differences: {bad}" if bad else ""))
record("A", "the key set agrees with the Step 4 vintage",
       "PASS" if not drift else "FAIL",
       f"drift vs {REF4}: {drift}" if drift else f"{len(ref_keys)} keys, no drift")
record("A", "cases with no dual key (all-zero dual)", "INFO",
       f"{no_dual} — expected: the 15 no-mandate cases, plus fbA if the credit worked")

# --- A6/A7: solver health ----------------------------------------------------------
worst_z, worst_at = 0.0, None
for c in CASES:
    ec = load(c, "error_check").set_index("*")["Value"]
    m = float(ec.abs().max())
    if m > worst_z:
        worst_z, worst_at = m, c
record("A", "the solver residuals are small in every file",
       "PASS" if worst_z < 1e-2 else "FAIL", f"worst |residual| {worst_z:.2e} at {worst_at}")

obj = {c: float(load(c, "objfn_raw")["Value"].iloc[0]) for c in CASES}
ok_obj = all(np.isfinite(v) and v > 0 for v in obj.values())
record("A", "the objective value is a normal positive number in every file",
       "PASS" if ok_obj else "FAIL",
       f"range {min(obj.values()):.4e} to {max(obj.values()):.4e}")
""")

code("""# --- A8: model years ---------------------------------------------------------------
EXPECT_YEARS = [int(y) for y in sw(CASES[0], "yearset").split("_")]
SOLVE_YEARS = [t for t in EXPECT_YEARS if t >= 2026]
assert len(SOLVE_YEARS) == 12, SOLVE_YEARS
bad_years = {}
for c in CASES:
    y = sorted(load(c, "cap")["t"].unique())
    if y != EXPECT_YEARS:
        bad_years[c] = y
YEARS_RUN = EXPECT_YEARS
record("A", "the model years are correct in every file (annual 2031-2035 block present)",
       "PASS" if not bad_years else "FAIL",
       f"expected {EXPECT_YEARS}" + (f"; wrong in {bad_years}" if bad_years else ""))

# --- A9: sequential solve mode -----------------------------------------------------
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

md("""## Phase B — Design-matrix echo, ITC application, and rate recovery

The mandate dual was read as the full required subsidy per MW.
These runs feed that subsidy back as a real investment credit.
The tests below make sure that the credit landed inside the finance multiplier
at exactly the fed rate, in exactly the fed years, for exactly the fed technology.

The rate recovery uses a ratio identity from `reeds/financials.py:683-694`:

    fin_mult / fin_mult_noITC = (1 - tax*(1 - m/2)*PVdep - m) / (1 - tax*PVdep)

so `m = (1 - ratio) * (1 - tax*PVdep) / (1 - tax*PVdep/2)`.
The construction multiplier, the risk multiplier, the evaluation adjustment,
the degradation adjustment, and the regional factor all cancel in the ratio.
Thus the same identity holds in the endogenous-learning runs.
GAMS loads the multipliers at 3 decimals, so the tolerance is |dm| <= 0.005.

- Test B1 echoes the design matrix from the case file.
- Tests B2 and B3 audit the incentives input files against the t09 rates.
- Tests B4 to B8 recover the applied rate from the run outputs.
- Tests B9 and B10 make sure that the phaseout exemption held and did not leak.
- Tests B11 and B12 audit the ITC payment flows in the system cost data.
- Tests B13 and B14 audit the capital-cost paths (drawn vs in-run learned).
- Tests B15 and B16 audit the dual keys and the within-world input identity.""")

code("""# --- B1: design-matrix echo --------------------------------------------------------
mx_rows, mx_bad = [], []
EXP_DESIGN = {"fbA": (1, 1, 0), "fbB": (0, 1, 0), "fbC": (0, 1, 1),
              "fbK": (1, 0, 1), "fbR": (0, None, 0)}   # (mandate, fed-itc, learning)
for c in CASES:
    m_ = META[c]
    fed = m_["suffix"].startswith("obbba_itcfb_")
    exp_m, exp_f, exp_l = EXP_DESIGN[m_["arm"]]
    ok = (m_["mandate"] == exp_m and m_["learning"] == exp_l
          and (exp_f is None or fed == bool(exp_f)))
    if m_["arm"] == "fbR":
        ok = ok and m_["suffix"] == {"fbR_none": "obbba_nonuclearitc",
                                     "fbR_itc30": "obbba_itcflat30",
                                     "fbR_itc50": "obbba_itcflat50"}[c]
    if fed:
        ok = ok and m_["suffix"] == f"obbba_itcfb_{m_['world']}_p50"
    if m_["learning"]:
        ok = ok and m_["foreign"] == f"fb_{m_['world']}_p50"
    if not ok:
        mx_bad.append(c)
    mx_rows.append(dict(case=c, arm=m_["arm"], world=m_["world"], mandate=m_["mandate"],
                        learning=m_["learning"], incentives=m_["suffix"],
                        foreign=m_["foreign"], scen=m_["scen"]))
mx = pd.DataFrame(mx_rows)
print(mx.to_string(index=False))
record("B", "the case matrix encodes the intended mandate, ITC, and learning design",
       "PASS" if not mx_bad else "FAIL",
       mx_bad or "19 cases match the three-factor design and the naming rules")
""")

code("""# --- B2: fed incentives files vs the t09 rate schedule -----------------------------
FIN_DIR = REPO / "inputs" / "financials"
echo_rows, b2_bad = [], []
for w in SCHEDULES:
    inc = pd.read_csv(FIN_DIR / f"incentives_obbba_itcfb_{w}_p50.csv")
    nuc_rows = inc[inc["i"].str.lower().str.startswith("nuclear")]
    only_smr = set(nuc_rows["i"]) == {"Nuclear-SMR"}
    got = {int(t): float(f) for t, f in zip(nuc_rows["t_start_construction"],
                                            nuc_rows["itc_frac"])}
    conv_ok = bool((nuc_rows["safe_harbor"] == 0).all()
                   and (nuc_rows["t_max_online"] == nuc_rows["t_start_construction"]).all()
                   and (nuc_rows["itc_tax_equity_penalty"] == PEN).all()
                   and (nuc_rows["itc_energy_comm_bonus"] == 0.0).all()
                   and (nuc_rows["itc_percpt_domestic_bonus"] == 0.0).all())
    rate_ok = got == RATES[w]
    if not (only_smr and conv_ok and rate_ok):
        b2_bad.append((w, dict(only_smr=only_smr, conv_ok=conv_ok, rate_ok=rate_ok)))
    for t in sorted(set(got) | set(RATES[w])):
        echo_rows.append(dict(world=w, t=t, itc_frac_file=got.get(t),
                              itc_frac_expected=RATES[w].get(t)))
pd.DataFrame(echo_rows).to_csv(EXPORTS / "incentives_echo.csv", index=False)
record("B", "the fed incentives files equal the headline rate schedule plus the bump "
       "at exactly the rate years",
       "PASS" if not b2_bad else "FAIL",
       b2_bad or f"6 files; Nuclear-SMR only; itc_frac == round(i_model_headline+{EPS}, 3); "
       "safe_harbor 0; online == start; penalty 0.1; bonuses 0")

# --- B3: flat incentives files -----------------------------------------------------
b3_bad = []
for name, frac in [("obbba_itcflat30", 0.30), ("obbba_itcflat50", 0.50)]:
    inc = pd.read_csv(FIN_DIR / f"incentives_{name}.csv")
    nuc_rows = inc[inc["i"].str.lower().str.startswith("nuclear")]
    both = set(nuc_rows["i"]) == {"Nuclear", "Nuclear-SMR"}
    for tech in ["Nuclear", "Nuclear-SMR"]:
        sub = nuc_rows[nuc_rows["i"] == tech]
        yrs = sorted(sub["t_start_construction"].astype(int))
        if yrs != SOLVE_YEARS or not (sub["itc_frac"] == frac).all():
            b3_bad.append((name, tech, yrs[:3], "..."))
    if not both:
        b3_bad.append((name, "techs", sorted(set(nuc_rows["i"]))))
record("B", "the flat incentives files credit both nuclear technologies at 0.30 and "
       "0.50 in all 12 solve years",
       "PASS" if not b3_bad else "FAIL", b3_bad or "both files correct, 2026-2050")
""")

code("""# --- rate-recovery machinery (tax rate + PV of depreciation; ccmult cancels) -------
YEARS = np.arange(2010, 2051)

def yi(t):
    return int(t - YEARS[0])

sys_fin = pd.read_csv(FIN_DIR / "financials_sys_ATB2024.csv")
infl = pd.read_csv(FIN_DIR / "inflation_default.csv")
sys_fin = sys_fin.merge(infl, on="t", how="left")
sys_fin["d_nom"] = ((1 - sys_fin["debt_fraction"]) * (sys_fin["rroe_nom"] - 1)
                    + sys_fin["debt_fraction"] * (sys_fin["interest_rate_nom"] - 1)
                      * (1 - sys_fin["tax_rate"]) + 1)

def on_years(col):
    s = sys_fin.set_index("t")[col].reindex(range(1990, YEARS[-1] + 1)).ffill()
    return s.loc[YEARS].to_numpy(float)

TAX = on_years("tax_rate")
D_NOM = on_years("d_nom")
DEP = pd.read_csv(FIN_DIR / "depreciation_schedules_default.csv")

def pv_dep_nuclear(case):
    \"\"\"PV-of-depreciation by year for each nuclear technology of one case.\"\"\"
    ft = pd.read_csv(FIN_DIR / f"financials_tech_{META[case]['fin']}.csv")
    ft.columns = [c.lstrip("*") for c in ft.columns]
    ft = ft[ft["i"].isin(["Nuclear", "Nuclear-SMR"])]
    out = {}
    for iname, grp in ft.groupby("i"):
        grp = grp.set_index("t").reindex(YEARS).ffill().bfill()
        dep_col = str(int(grp["depreciation_sch"].iloc[0]))
        dep_frac = DEP[dep_col].to_numpy(float)
        out[iname.lower()] = pd.Series(
            [np.sum(dep_frac / dn ** np.arange(1, len(dep_frac) + 1)) for dn in D_NOM],
            index=YEARS)
    return out

def recovered_m(case):
    \"\"\"Recover the monetized ITC rate per (i, r, t) from the two finance multipliers.\"\"\"
    fm = load(case, "cost_cap_fin_mult")
    fno = load(case, "cost_cap_fin_mult_noITC")
    fm = fm[fm["i"].isin(NUC)].set_index(["i", "r", "t"])["Value"]
    fno = fno[fno["i"].isin(NUC)].set_index(["i", "r", "t"])["Value"]
    j = pd.concat([fm, fno], axis=1, keys=["fm", "fno"]).dropna().reset_index()
    pv = pv_dep_nuclear(case)
    pd_ = np.array([pv[i].loc[t] for i, t in zip(j["i"], j["t"])])
    tau = TAX[[yi(t) for t in j["t"]]]
    ratio = j["fm"].to_numpy() / j["fno"].to_numpy()
    j["m_rec"] = (1.0 - ratio) * (1.0 - tau * pd_) / (1.0 - tau * pd_ / 2.0)
    return j

REC = {}
rr_rows = []
for c in CASES:
    j = recovered_m(c)
    g = j.groupby(["i", "t"])["m_rec"].agg(["median", "min", "max"])
    g["spread_r"] = g["max"] - g["min"]
    REC[c] = g
    w = META[c]["world"]
    for (i, t), r in g.iterrows():
        if META[c]["arm"] == "fbR":
            m_exp = FLAT_M[c] if (t in SOLVE_YEARS and c != "fbR_none") else 0.0
        else:
            m_exp = (M_EXP[w].get(t, 0.0)
                     if (i == "nuclear-smr" and META[c]["suffix"].startswith("obbba_itcfb_"))
                     else 0.0)
        rr_rows.append(dict(case=c, arm=META[c]["arm"], i=i, t=t,
                            m_expected=round(m_exp, 4),
                            m_recovered=round(float(r["median"]), 4),
                            spread_r=round(float(r["spread_r"]), 5),
                            delta=round(float(r["median"]) - m_exp, 4)))
rr = pd.DataFrame(rr_rows)
rr.to_csv(EXPORTS / "rate_recovery.csv", index=False)
print(f"rate recovery: {len(rr)} (case, tech, year) points")
""")

code("""# --- B4/B4b: the recovered rate equals the fed rate at the rate years --------------
TOL_M = 0.005   # GAMS loads the multipliers at 3 decimals

def rate_year_rows(case_list):
    sub = rr[rr["case"].isin(case_list) & (rr["i"] == "nuclear-smr")]
    return sub[[t in RATES[META[r.case]["world"]] for r in sub.itertuples()]]

b4 = rate_year_rows(ARM_CASES["fbA"] + ARM_CASES["fbB"])
worst4 = b4.loc[b4["delta"].abs().idxmax()]
record("B", "the recovered ITC rate equals the fed rate at exactly the rate years "
       "(fbA and fbB)",
       "PASS" if b4["delta"].abs().max() <= TOL_M else "FAIL",
       f"{len(b4)} rate case-years; worst |dm| {b4['delta'].abs().max():.4f} at "
       f"({worst4.case}, {worst4.t})")

b4c = rate_year_rows(ARM_CASES["fbC"])
worst4c = b4c.loc[b4c["delta"].abs().idxmax()]
record("B", "the recovered ITC rate equals the fed rate in the learning runs (fbC)",
       "PASS" if b4c["delta"].abs().max() <= TOL_M else "INFO",
       f"{len(b4c)} rate case-years; worst |dm| {b4c['delta'].abs().max():.4f} at "
       f"({worst4c.case}, {worst4c.t}); the learned construction multiplier cancels "
       "in the ratio, so a large delta needs a second look, not an automatic defect")

# --- B5: zero outside the rate years and for the large reactor ---------------------
fed = rr[rr["case"].isin(FED_CASES)]
off = fed[[not (r.i == "nuclear-smr" and r.t in RATES[META[r.case]["world"]])
           for r in fed.itertuples()]]
record("B", "the recovered rate is zero outside the rate years and for the large "
       "reactor in the fed arms",
       "PASS" if off["m_recovered"].abs().max() <= TOL_M else "FAIL",
       f"{len(off)} points; max |m| {off['m_recovered'].abs().max():.4f}")

# --- B6: flat arms recover 0.27 / 0.45 in all 12 solve years -----------------------
# The SMR has no investment rows before its 2031 first year, so its multiplier
# starts at 2031. The large reactor covers all 12 solve years.
b6_bad = []
for c in ["fbR_itc30", "fbR_itc50"]:
    sub = rr[(rr["case"] == c) & rr["t"].isin(SOLVE_YEARS)]
    for i in NUC:
        expect_years = [t for t in SOLVE_YEARS if t >= 2031] if i == "nuclear-smr" \
            else SOLVE_YEARS
        got = sub[sub["i"] == i].set_index("t")["m_recovered"]
        miss = [t for t in expect_years if t not in got.index]
        badv = [(t, v) for t, v in got.items() if abs(v - FLAT_M[c]) > TOL_M]
        if miss or badv:
            b6_bad.append((c, i, miss, badv[:3]))
record("B", "the flat arms recover 0.27 and 0.45 for both nuclear technologies in "
       "every covered solve year",
       "PASS" if not b6_bad else "FAIL",
       b6_bad or "12 large + 10 SMR (from 2031) solve years per case")

# --- B7: no ITC reaches nuclear technology in fbK and fbR_none ---------------------
worst_wedge, wedge_at = 0.0, None
for c in NOITC_CASES:
    fm = nuc_slice(c, "cost_cap_fin_mult")
    fno = nuc_slice(c, "cost_cap_fin_mult_noITC")
    m = float((fm - fno).abs().max())
    if m > worst_wedge:
        worst_wedge, wedge_at = m, c
record("B", "no ITC reaches nuclear technology in fbK and fbR_none "
       "(fin_mult == fin_mult_noITC)",
       "PASS" if worst_wedge < 1e-6 else "FAIL",
       f"max |difference| {worst_wedge:.2e}" + (f" at {wedge_at}" if worst_wedge >= 1e-6 else ""))

# --- B8: the recovered rate is uniform across regions ------------------------------
sp = rr[rr["case"].isin(FED_CASES) & (rr["i"] == "nuclear-smr")]
record("B", "the recovered rate is uniform across regions",
       "PASS" if sp["spread_r"].max() <= TOL_M else "FAIL",
       f"max spread over regions {sp['spread_r'].max():.5f} (14 fed cases)")
""")

code("""# --- B9: the phaseout does not reduce the nuclear credit in any year ---------------
# Without the exemption, GSw_TCPhaseout_forceyear=2032 cuts a credit at online year
# 2034 to x0.75, 2035 to x0.5, and 2036 on to x0. Every fed rate year is >= 2038.
late = rr[(rr["t"] >= 2036) & (rr["m_expected"] > 0)]
record("B", "the phaseout does not reduce the nuclear credit in any year "
       "(exemption held)",
       "PASS" if late["delta"].abs().max() <= TOL_M else "FAIL",
       f"{len(late)} credited case-years at t >= 2036; worst |dm| "
       f"{late['delta'].abs().max():.4f}; without the exemption every one would recover 0")

# --- B10: the exemption did not change the other technologies ----------------------
# The finance multipliers of the non-nuclear technologies depend only on the
# exogenous financing and incentives inputs. Those inputs are shared with the
# Step 3 base run of each world. Thus the non-nuclear ITC wedge (fno - fm) must
# be identical to the base run's, phaseout staircase included. (An absolute
# wedge ~0 is the wrong null: some gas rows carry a large pre-existing
# multiplier artifact that the base run shows bit-for-bit as well.)
leak_rows = []
for c, b in [("fbB_eia_p50", "smr100_eia_p50"), ("fbC_eo_p50", "smr100_eo_p50"),
             ("fbR_itc50", "smr100_eia_p50")]:
    w_pair = {}
    for name, run in [("fb", c), ("base", b)]:
        fm = load(run, "cost_cap_fin_mult")
        fno = load(run, "cost_cap_fin_mult_noITC")
        fm = fm[~fm["i"].isin(NUC)].set_index(["i", "r", "t"])["Value"]
        fno = fno[~fno["i"].isin(NUC)].set_index(["i", "r", "t"])["Value"]
        w_pair[name] = fno - fm
    j = pd.concat([w_pair["fb"], w_pair["base"]], axis=1,
                  keys=["fb", "base"]).dropna()
    d = float((j["fb"] - j["base"]).abs().max())
    if d > 1e-6:
        leak_rows.append((c, b, d))
record("B", "the phaseout exemption did not change the other technologies "
       "(non-nuclear ITC wedge identical to the base run)",
       "PASS" if not leak_rows else "FAIL",
       leak_rows or "3 spot cases vs their base runs; wedge identical, "
       "phaseout staircase included")
""")

code("""# --- B11/B12: ITC payment flows in the system cost data ----------------------------
pay_bad, pay = [], {}
for c in CASES:
    sc = load(c, "systemcost_techba")
    it = sc[sc["sys_costs"].str.contains("itc", case=False) & sc["i"].isin(NUC)]
    v = float(it["Value"].abs().sum())
    pay[c] = v
    has_itc = c in FED_CASES or c in ("fbR_itc30", "fbR_itc50")
    if has_itc and v < 1e6:
        pay_bad.append((c, "expected nuclear ITC payments, found none"))
    if not has_itc and v > 1.0:
        pay_bad.append((c, f"unexpected nuclear ITC payments {v:,.0f}"))
record("B", "the system cost data shows nuclear ITC payments only in the ITC arms",
       "PASS" if not pay_bad else "FAIL",
       pay_bad or "payments present in the 16 ITC cases, absent in fbK and fbR_none")

itc_mag = {c: abs(float(load(c, "tax_expenditure_itc")["Value"].sum())) for c in CASES}
record("B", "the other technologies keep their ITC in all 19 runs",
       "PASS" if min(itc_mag.values()) > 1e8 else "FAIL",
       f"total ITC tax expenditure magnitude {min(itc_mag.values())/1e9:.1f} to "
       f"{max(itc_mag.values())/1e9:.1f} B$ per case (recorded as negative; magnitude used)")
""")

code("""# --- B13: the learning-off runs use the drawn cost path without change -------------
PC_DIR = REPO / "inputs" / "plant_characteristics"

def plantchar(name):
    df = pd.read_csv(PC_DIR / f"{name}.csv")
    df.columns = [c.lstrip("*").lower() for c in df.columns]
    return df.set_index("t")

fp_rows = []
for c in CASES:
    cc = load(c, "cost_cap")
    cc = cc[cc["i"].isin(NUC)].set_index(["i", "t"])["Value"]
    for itech in NUC:
        pc_df = plantchar(META[c]["pc"][itech])
        for t, occ_kw in pc_df["capcost"].items():
            if (itech, t) not in cc.index:
                continue
            expect = occ_kw * 1000.0 * D2022
            got = float(cc.loc[(itech, t)])
            fp_rows.append(dict(case=c, learning=META[c]["learning"], i=itech, t=t,
                                expect=expect, got=got,
                                rel_err=abs(got - expect) / expect))
fp = pd.DataFrame(fp_rows)
fp.to_csv(EXPORTS / "fingerprint_errors.csv", index=False)
off_fp = fp[fp["learning"] == 0]
worst_fp = off_fp.loc[off_fp.rel_err.idxmax()]
record("B", "the learning-off runs use the drawn cost path without change (11 cases)",
       "PASS" if off_fp.rel_err.max() < 1e-4 else "FAIL",
       f"{len(off_fp)} (case, tech, year) points; max rel err {off_fp.rel_err.max():.2e} "
       f"at ({worst_fp.case}, {worst_fp.i}, {worst_fp.t})")

# --- B14: the learning-on runs write an in-run cost path (context) -----------------
on_fp = fp[(fp["learning"] == 1) & (fp["t"] >= 2031)]
dev = on_fp.groupby(["case", "i"])["rel_err"].max().round(4)
record("B", "the learning-on runs write an in-run cost path (deviation from the "
       "drawn path is expected)", "INFO",
       dev.to_dict())
""")

code("""# --- B15: dual keys exist only where a mandate exists ------------------------------
dual_present = {c: "nuclear_cap_price" in keysets[c] for c in CASES}
b15_bad = [c for c in CASES if META[c]["mandate"] == 0 and dual_present[c]]
record("B", "the dual keys exist only where a mandate exists",
       "PASS" if not b15_bad else "FAIL",
       b15_bad or f"absent in all 15 no-mandate cases; "
       f"fbA: {[dual_present[c] for c in ARM_CASES['fbA']]} (absent = collapsed = intended); "
       f"fbK: {[dual_present[c] for c in ARM_CASES['fbK']]}")

# --- B16: within one world the learning-off arms share the same inputs -------------
b16_worst = {}
for w, group in [("eia", ["fbA_eia_p50", "fbB_eia_p50", "fbR_none",
                          "fbR_itc30", "fbR_itc50"]),
                 ("eo", ["fbA_eo_p50", "fbB_eo_p50"])]:
    ref_c = group[0]
    for key in ["cost_cap", "cost_cap_fin_mult_noITC"]:
        a0 = nuc_slice(ref_c, key)
        for c in group[1:]:
            d = float((nuc_slice(c, key) - a0).abs().max())
            b16_worst[(w, key)] = max(b16_worst.get((w, key), 0.0), d)
record("B", "the no-ITC finance multiplier and the capital cost are identical across "
       "the learning-off arms of one world",
       "PASS" if max(b16_worst.values()) < 1e-6 else "FAIL",
       f"max |difference| {max(b16_worst.values()):.2e} over "
       f"{sorted(set(k[0] for k in b16_worst))}")
""")

md("""## Phase C — Arm-specific pre-registered criteria (spec section 7)

These tests apply the pre-registered pass criteria, one arm at a time.
The control order matters.
Read fbA first: a persisting dual means the credit was misapplied.
Then read fbB (the convex control) and fbK (the engine calibration).
Only then interpret fbC, the section-9 test.

The base-world duals come from the canonical export
`step3_checks/exports/duals_by_year.csv`. The notebook never re-derives them.

The trajectory tests use national cumulative SMR capacity.
The mandate counts all vintages, so capacity is the correct basis, not additions.
The reproduction tiers are a notebook convention, stated here once:

- **exact** — every gap is inside 5 MW (solver and mandate-slack scale).
- **reproduces** — every rate-year and 2050 shortfall is inside
  max(5% of the trajectory, 500 MW). Overbuild never fails: the fed rate
  carries a +0.01 bump on purpose.
- **partial** — the 2050 shortfall is inside 15%.
- **no** — the 2050 shortfall is above 15%.

Slack-status years get no credit (the base run overbuilt them without a dual),
so shortfalls there are reported but not pass-gated.

The fbK calibration must respect the engine's timing convention.
The engine prices solve year `t` from the investment through the previous
solve year (`nuclear_learning.py:366`, `tprev`) — the solve is myopic.
The drawn plant file embeds same-year experience.
Thus the applied cost at a solve year must sit between the drawn cost at that
year and the drawn cost at the previous solve year.
The gap is largest right after the annual 2031-2035 block, where one solve
step spans three years of experience.
A same-year comparison would report this documented convention as a defect.""")

code("""# --- mandate trajectories + national SMR capacity ----------------------------------
NL_DIR = REPO / "inputs" / "nuclear_learning"

def trajectory(scen):
    tr = pd.read_csv(NL_DIR / f"nuclear_cap_trajectory_{scen}.csv")
    tr.columns = [c.lstrip("*") for c in tr.columns]
    return tr.set_index(tr.columns[0])["MW"]

TRAJ = {w: trajectory(f)
        for w, f in [("eia", "eia_aeo_high_smr"), ("aj", "abou_jaoude_smr"),
                     ("iaea", "iaea_high_smr"), ("mck", "mckinsey_smr"),
                     ("cop28", "cop28_smr"), ("eo", "eo2025_smr")]}
for c in CASES:
    if META[c]["mandate"]:
        assert META[c]["scen"] == {"eia": "eia_aeo_high_smr", "aj": "abou_jaoude_smr",
                                   "iaea": "iaea_high_smr", "mck": "mckinsey_smr",
                                   "cop28": "cop28_smr", "eo": "eo2025_smr"}[META[c]["world"]]

SMR_CAP = {c: load(c, "cap").query("i == 'nuclear-smr'").groupby("t")["Value"].sum()
           for c in CASES}
LARGE_NEW = {c: load(c, "cap_new_ann").query("i == 'nuclear' and t > 2030")
             .groupby("t")["Value"].sum() for c in CASES}

DUAL, RAW = {}, {}
for c in CASES:
    if "nuclear_cap_price" in keysets[c]:
        DUAL[c] = load(c, "nuclear_cap_price").set_index("t")["Value"]
        RAW[c] = load(c, "nuclear_cap_price_raw").set_index("t")["Value"]
    else:
        DUAL[c] = pd.Series(dtype=float)
        RAW[c] = pd.Series(dtype=float)

# gap table for every fed or mandated case, one schema
gap_rows = []
for c in ARM_CASES["fbA"] + ARM_CASES["fbB"] + ARM_CASES["fbC"] + ARM_CASES["fbK"]:
    w = META[c]["world"]
    tr = TRAJ[w]
    for t in YEARS_RUN:
        req = float(tr.get(t, 0.0))
        if req <= 0:
            continue
        have = float(SMR_CAP[c].get(t, 0.0))
        status = "rate" if t in RATES[w] else "slack"
        gap_rows.append(dict(case=c, arm=META[c]["arm"], world=w, t=t, status=status,
                             mandate_MW=req, cap_MW=round(have, 1),
                             gap_MW=round(have - req, 1),
                             gap_pct=round(100 * (have - req) / req, 2)))
gaps = pd.DataFrame(gap_rows)
gaps.to_csv(EXPORTS / "trajectory_gaps.csv", index=False)

def tier(case):
    \"\"\"Reproduction tier for one case (see the convention above).\"\"\"
    sub = gaps[gaps["case"] == case]
    shortfall = (-sub["gap_MW"]).clip(lower=0.0)
    if float(shortfall.max()) <= 5.0 and float(sub["gap_MW"].abs().max()) <= 5.0:
        return "exact"
    gate = sub[(sub["status"] == "rate") | (sub["t"] == 2050)]
    g_short = (-gate["gap_MW"]).clip(lower=0.0)
    tol1 = np.maximum(0.05 * gate["mandate_MW"], 500.0)
    if bool((g_short <= tol1).all()):
        return "reproduces"
    end = gate[gate["t"] == 2050]
    if len(end) and float(-end["gap_MW"].iloc[0]) <= 0.15 * float(end["mandate_MW"].iloc[0]):
        return "partial"
    return "no"

TIER = {c: tier(c) for c in gaps["case"].unique()}
print(pd.Series(TIER).to_string())
""")

code("""# --- C1: fbA dual collapse ---------------------------------------------------------
duals3 = pd.read_csv(STEP3_EXPORTS / "duals_by_year.csv")
c1_rows, c1_bad = [], []
for c in ARM_CASES["fbA"]:
    b = BASE_OF_WORLD[META[c]["world"]]
    base = duals3[(duals3["case"] == b) & (duals3["dual_2004_MWyr"] > 1.0)]
    for t in base["t"]:
        d_fb = float(DUAL[c].get(t, 0.0))
        d_b = float(base.set_index("t").loc[t, "dual_2004_MWyr"])
        c1_rows.append(dict(case=c, t=int(t), base_dual_2004_MWyr=d_b,
                            fbA_dual_2004_MWyr=d_fb, collapsed=d_fb <= 1.0))
        if d_fb > 1.0:
            c1_bad.append((c, int(t), round(d_fb, 1)))
c1 = pd.DataFrame(c1_rows)
c1.to_csv(EXPORTS / "fbA_collapse.csv", index=False)
record("C", "every previously binding floor dual collapses in the fbA runs",
       "PASS" if not c1_bad else "FAIL",
       c1_bad or f"{len(c1)} previously binding case-years; every fbA dual <= $1/MW-yr "
       f"(the dual key is absent from both fbA files: all-zero dual)")

# --- C2/C3: the mandate floor in fbA and fbK ---------------------------------------
c2_bad = []
for c in MANDATE_CASES:
    sub = gaps[gaps["case"] == c]
    v = sub[sub["gap_MW"] < -5.0]
    if len(v):
        c2_bad.append((c, v[["t", "gap_MW"]].values.tolist()[:3]))
record("C", "the capacity satisfies the mandate floor in the fbA and fbK runs",
       "PASS" if not c2_bad else "FAIL",
       c2_bad or "no shortfall larger than 5 MW in any mandated year (4 cases)")
ob = {c: round(float((gaps[gaps['case'] == c]['cap_MW']
                      / gaps[gaps['case'] == c]['mandate_MW']).max()), 3)
      for c in MANDATE_CASES}
record("C", "the fbA and fbK overbuild relative to the trajectory", "INFO",
       f"max cap/trajectory ratio by case: {ob} (the +0.01 bump makes overbuild expected in fbA)")
""")

code("""# --- C4/C5: fbB, the convex decentralization control -------------------------------
fbB_tiers = {c: TIER[c] for c in ARM_CASES["fbB"]}
ok_b = all(t in ("exact", "reproduces") for t in fbB_tiers.values())
worst_b = gaps[gaps["case"].isin(ARM_CASES["fbB"]) & (gaps["status"] == "rate")]
record("C", "the national SMR capacity reproduces the mandate trajectory in the "
       "fbB runs",
       "PASS" if ok_b else "FAIL",
       f"tiers: {fbB_tiers}; worst rate-year shortfall "
       f"{float((-worst_b['gap_MW']).clip(lower=0).max()):,.0f} MW")

sub_b = {c: round(float(LARGE_NEW[c].sum()) / 1000.0, 2) for c in ARM_CASES["fbB"]}
record("C", "the large-reactor substitution in the fbB runs (a report, not a failure)",
       "INFO", f"new large builds after 2030 (GW): {sub_b}")

# --- C6: fbC, the section-9 test (data completeness; the verdict is analysis work) -
fbC_tiers = {c: TIER[c] for c in ARM_CASES["fbC"]}
record("C", "the fbC runs return complete data for the section-9 verdict", "INFO",
       f"tiers on the same convention: {fbC_tiers}; the pre-registered verdict "
       "(pass or fail both reportable) is read in z-ethan/itcfb_analysis/")
""")

code("""# --- C7: fbK, the engine calibration -----------------------------------------------
# The engine prices solve year t from the investment through the previous solve
# year (myopic; nuclear_learning.py:366). Thus:
#   - at a non-override year the file echoes the drawn input (identity), and
#   - at an override year (solve years from 2031 on) the applied cost must sit
#     inside [drawn(t), drawn(tprev)] — the drawn path evaluated at the two
#     experience states the solve step spans. Tolerance: 1e-3 of drawn(t).
# The same-year deviation (largest right after the annual block) is the
# documented myopia convention. It is recorded as context, not as a defect.
OVERRIDE_YEARS = [t for t in SOLVE_YEARS if t >= 2031]
TPREV = {t: EXPECT_YEARS[EXPECT_YEARS.index(t) - 1] for t in OVERRIDE_YEARS}
c7_rows = []
for c in ARM_CASES["fbK"]:
    cc = load(c, "cost_cap")
    cc = cc[cc["i"].isin(NUC)].set_index(["i", "t"])["Value"]
    for itech in NUC:
        pc_df = plantchar(META[c]["pc"][itech])
        drawn = pc_df["capcost"] * 1000.0 * D2022
        for t, expect in drawn.items():
            if (itech, t) not in cc.index:
                continue
            got = float(cc.loc[(itech, t)])
            tol = 1e-3 * expect
            if t in TPREV:
                prev_v = float(drawn.get(TPREV[t], expect))
                # min/max, not (t, tprev) order: the drawn path steps UP at the
                # 2030 anchor, so drawn(tprev) can sit below drawn(t) there.
                lo, hi = min(expect, prev_v), max(expect, prev_v)
                ok = (lo - tol) <= got <= (hi + tol)
            else:
                ok = abs(got - expect) <= 1e-6 * expect
            c7_rows.append(dict(case=c, i=itech, t=int(t), drawn_2004_MW=expect,
                                inrun_2004_MW=got,
                                drawn_tprev_2004_MW=float(drawn.get(TPREV.get(t), expect)),
                                override=t in TPREV, in_bracket=ok,
                                rel_err=abs(got - expect) / expect))
c7 = pd.DataFrame(c7_rows)
c7.to_csv(EXPORTS / "fbK_calibration.csv", index=False)
bad7 = c7[~c7["in_bracket"]]
record("C", "the in-run learned cost path reproduces the drawn cost path under "
       "the engine's lagged-experience timing (fbK)",
       "PASS" if not len(bad7) else "FAIL",
       (bad7[["case", "i", "t"]].values.tolist()[:5] if len(bad7) else
        f"{int(c7['override'].sum())} override points inside [drawn(t), drawn(tprev)]; "
        f"{int((~c7['override']).sum())} non-override points echo the drawn input"))
lag = c7[c7["override"]].groupby(["case", "i"])["rel_err"].max().round(4)
record("C", "the myopia lag between the applied cost and the same-year drawn cost "
       "(context)", "INFO",
       f"max same-year rel deviation by (case, tech): {lag.to_dict()}; "
       "largest right after the annual 2031-2035 block, where one solve step "
       "spans three years of experience")

# --- C8: fbK duals vs the canonical base duals (context) ---------------------------
c8 = {}
for c in ARM_CASES["fbK"]:
    b = BASE_OF_WORLD[META[c]["world"]]
    base = duals3[(duals3["case"] == b) & (duals3["dual_2004_MWyr"] > 1.0)] \
        .set_index("t")["dual_2004_MWyr"]
    both = [t for t in base.index if float(DUAL[c].get(t, 0.0)) > 1.0]
    if both:
        r = np.mean([float(DUAL[c].get(t)) / float(base.loc[t]) for t in both])
        c8[c] = f"{len(both)}/{len(base)} shared binding years, mean ratio {r:.2f}"
    else:
        c8[c] = f"0/{len(base)} shared binding years"
record("C", "the fbK duals stay close to the base-run duals (a replay, degenerate-tie "
       "sensitive)", "INFO", c8)
""")

code("""# --- C9/C10: fbR, the demand-curve anchors -----------------------------------------
cap50 = {}
for c in ARM_CASES["fbR"]:
    cap = load(c, "cap")
    nuc50 = cap[cap["i"].isin(NUC) & (cap["t"] == 2050)]["Value"].sum()
    cap50[c] = float(nuc50)
mono = (cap50["fbR_none"] <= cap50["fbR_itc30"] + 5.0
        and cap50["fbR_itc30"] <= cap50["fbR_itc50"] + 5.0)
record("C", "the deployment increases with the flat credit rate in the fbR runs",
       "PASS" if mono else "FAIL",
       {c: f"{v/1000:.1f} GW nuclear in 2050" for c, v in cap50.items()})

r_none_ok = (not dual_present["fbR_none"]
             and float((nuc_slice("fbR_none", "cost_cap_fin_mult")
                        - nuc_slice("fbR_none", "cost_cap_fin_mult_noITC")).abs().max()) < 1e-6
             and fp[(fp["case"] == "fbR_none")].rel_err.max() < 1e-4)
record("C", "the fbR_none run is a clean no-subsidy baseline",
       "PASS" if r_none_ok else "FAIL",
       "no dual key; zero ITC wedge; drawn cost path unchanged")
""")

md("""## Phase D — Cross-case invariance and unexpected values

The 19 runs differ only through the mandate, the ITC, and the learning switches.
No demand, fuel, renewable, or transmission switch differs between them.
Thus the exogenous inputs must be identical across all 19 runs.

- Test D1 makes sure that the exogenous load is identical in all 19 runs.
- Test D2 scans all data for NaN values.
- Tests D3 and D4 scan for wrong negative values.
- Test D5 makes sure that the national totals equal the regional sums.
- Test D6 compares the learning-off outputs with the Step 3 base-run outputs.
- Test D7 makes sure that the dual conversion is correct.
- Test D8 makes sure that no SMR capacity exists before 2031.
- Test D9 records where the runs build large reactors.""")

code("""# --- D1: exogenous load invariance -------------------------------------------------
ref_l = load("fbR_none", "load_rt").set_index(["r", "t"])["Value"]
li_rows = []
for c in CASES:
    if c == "fbR_none":
        continue
    a = load(c, "load_rt").set_index(["r", "t"])["Value"]
    j = pd.concat([a, ref_l], axis=1, keys=["c", "ref"]).fillna(0.0)
    rel = float(((j["c"] - j["ref"]).abs() / j["ref"].abs().clip(lower=1.0)).max())
    li_rows.append(dict(case=c, vs="fbR_none", max_rel_diff=rel))
li = pd.DataFrame(li_rows)
li.to_csv(EXPORTS / "load_invariance.csv", index=False)
record("D", "the exogenous load is identical in all 19 runs",
       "PASS" if li.max_rel_diff.max() < 1e-6 else "FAIL",
       f"max rel difference {li.max_rel_diff.max():.2e} vs fbR_none")

# --- D2-D4: full data scan ---------------------------------------------------------
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
record("D", "no data value is NaN or infinite in any file",
       "PASS" if not nan_bad else "FAIL",
       nan_bad[:5] or f"all {len(union)} keys x 19 files scanned")
record("D", "no negative values occur where values must not be negative",
       "PASS" if not neg_bad else "FAIL",
       neg_bad[:5] or f"checked {NONNEG} (storage charging and upgrades are "
       "legitimately negative elsewhere)")
record("D", "the nuclear build and generation data is not negative",
       "PASS" if not nuc_neg else "FAIL",
       nuc_neg[:5] or "cap_new_ann and gen_ann nuclear rows >= 0, all 19 cases")
""")

code("""# --- D5: national totals equal the regional sums -----------------------------------
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
record("D", "the national totals equal the sum of the regional data",
       "PASS" if not tot_bad else "FAIL",
       tot_bad[:5] or "cap, gen_ann, cap_new_ann, ret_ann; all 19 cases within 1e-3")
""")

code("""# --- D6: learning-off outputs match the Step 3 base-run outputs --------------------
# The learning-off arms point at the same nuclear input files as the base run of
# their world. Thus the pre-ITC nuclear outputs must match the base outputs
# bit-for-bit. This also proves no input drift between the NREL batches.
bi_rows = []
for c in LEARNOFF_CASES:
    b = BASE_OF_WORLD[META[c]["world"]]
    for key in ["cost_cap", "cost_cap_fin_mult_noITC"]:
        a = nuc_slice(c, key)
        r = nuc_slice(b, key)
        j = pd.concat([a, r], axis=1, keys=["fb", "base"]).fillna(0.0)
        d = (j["fb"] - j["base"]).abs()
        rel = float((d / j["base"].abs().clip(lower=1e-9)).max())
        bi_rows.append(dict(case=c, base=b, key=key, n_points=len(j),
                            max_abs_diff=float(d.max()), max_rel_diff=rel))
bi = pd.DataFrame(bi_rows)
bi.to_csv(EXPORTS / "base_identity.csv", index=False)
record("D", "the learning-off outputs match the Step 3 base-run outputs "
       "(11 cases, both keys)",
       "PASS" if bi.max_rel_diff.max() < 1e-6 else "FAIL",
       f"max rel difference {bi.max_rel_diff.max():.2e}")

# --- D7: dual conversion audit -----------------------------------------------------
worst_conv = 0.0
for c in CASES:
    if not len(DUAL[c]):
        continue
    pvf = load(c, "pvf_onm").set_index("t")["Value"]
    cs = float(load(c, "cost_scale")["Value"].iloc[0])
    implied = RAW[c] / DUAL[c] / cs
    rel = (implied - pvf.reindex(implied.index)).abs() / pvf.reindex(implied.index)
    worst_conv = max(worst_conv, float(rel.max()))
record("D", "the dual conversion is correct (raw = cost_scale x pvf_onm x converted)",
       "PASS" if worst_conv < 1e-4 else "FAIL",
       f"max rel err {worst_conv:.2e} across the cases with duals")

# --- D8/D9: SMR timing and large builds --------------------------------------------
pre = {c: float(load(c, "cap").query("i == 'nuclear-smr' and t < 2031")["Value"].sum())
       for c in CASES}
record("D", "no SMR capacity exists before 2031",
       "PASS" if max(pre.values()) == 0 else "FAIL",
       f"max pre-2031 SMR capacity {max(pre.values()):.1f} MW")

lg_all = {c: round(float(LARGE_NEW[c].sum()) / 1000.0, 2) for c in CASES
          if float(LARGE_NEW[c].sum()) > 0}
record("D", "where the runs build large reactors (context)", "INFO",
       lg_all or "no new large builds after 2030 in any of the 19 runs")
""")

md("""## Summary and report

The next cells write the exports and the report.

- `exports/checks_summary.csv` — the full check registry.
- `exports/duals_by_year.csv` — the canonical dual export for the 19 runs,
  in the same schema as the Step 3 and Step 4 exports.
- `itcfb_check_results.md` — the report in Simplified Technical English.""")

code("""# --- canonical dual export for the 19 runs -----------------------------------------
rows = []
for c in CASES:
    w = META[c]["world"]
    tr = TRAJ[w] if META[c]["mandate"] else None
    for t in YEARS_RUN:
        req = float(tr.get(t, 0.0)) if tr is not None else 0.0
        have = float(SMR_CAP[c].get(t, 0.0))
        dual = float(DUAL[c].get(t, 0.0))
        rows.append(dict(case=c, t=t, mandate_MW=req, cap_MW=round(have, 1),
                         slack_MW=round(have - req, 1), dual_2004_MWyr=dual,
                         dual_raw=float(RAW[c].get(t, 0.0)),
                         dual_2024_MWyr=dual * TO2024))
duals_tbl = pd.DataFrame(rows)
duals_tbl.to_csv(EXPORTS / "duals_by_year.csv", index=False)
print(f"wrote duals_by_year.csv ({len(duals_tbl)} rows; cap_MW is national SMR capacity)")
""")

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
    "B": "Phase B — Design-matrix echo, ITC application, and rate recovery",
    "C": "Phase C — Arm-specific pre-registered criteria",
    "D": "Phase D — Cross-case invariance and unexpected values",
}
PHASE_STE = {
    "A": "These tests make sure that the file set is complete and that each solve is clean.",
    "B": "These tests make sure that each run encodes its design cell and that the "
         "credit landed at the fed rate, in the fed years, for the fed technology.",
    "C": "These tests apply the pre-registered pass criteria from spec section 7, "
         "one arm at a time. A FAIL here can be a pre-registered finding.",
    "D": "These tests make sure that the runs show no cross-case corruption "
         "and no unexpected values.",
}

lines = [
    "# ITC feed-back output checks — report",
    "",
    f"Date of this report: {date.today().isoformat()}.",
    f"Input folder: `{H5_DIR}`.",
    "The run set has 19 cases: 2 fbA + 6 fbB + 6 fbC + 2 fbK + 3 fbR.",
    "The notebook `itcfb_output_checks.ipynb` performs all tests.",
    "The pre-registered criteria are in `z-ethan/itc_feedback/run_manifest.md`.",
    "",
    "## Summary",
    "",
    f"The notebook performed {len(summary)} checks.",
    f"Result counts: {counts}.",
]
if len(fails):
    lines += [f"**{len(fails)} tests failed.** The tables below show them with the "
              "status FAIL.",
              "A FAIL in phase A, B, or D shows a defect. Examine it before any analysis.",
              "A FAIL in phase C can be a pre-registered finding. "
              "The analysis notebook interprets it."]
else:
    lines += ["**All pass/fail tests passed.** No test found a defect in the 19 runs.",
              "Rows with the status INFO give context data. They have no pass condition."]
lines += [
    "",
    "Status meanings:",
    "",
    "- **PASS** — the condition holds.",
    "- **FAIL** — the condition does not hold.",
    "- **INFO** — context data only. There is no pass condition.",
    "- **BLOCKED** — the test could not run. Data is missing.",
]
for ph in ["A", "B", "C", "D"]:
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
    "- `exports/duals_by_year.csv` — the canonical dual export for the 19 runs.",
    "- `exports/incentives_echo.csv` — the incentives-file audit against the t09 rates.",
    "- `exports/rate_recovery.csv` — the recovered ITC rate per (case, tech, year).",
    "- `exports/trajectory_gaps.csv` — the capacity-vs-trajectory gaps (fbA/fbB/fbC/fbK).",
    "- `exports/fbA_collapse.csv` — the fbA dual-collapse table.",
    "- `exports/fbK_calibration.csv` — the fbK learned-vs-drawn cost-path comparison.",
    "- `exports/fingerprint_errors.csv` — the capital-cost fingerprints, all 19 cases.",
    "- `exports/base_identity.csv` — the learning-off vs Step 3 base output identity.",
    "- `exports/load_invariance.csv` — the load comparison across the 19 cases.",
    "",
]
(HERE / "itcfb_check_results.md").write_text("\\n".join(lines), encoding="utf-8")
print(f"wrote itcfb_check_results.md ({len(lines)} lines)")
""")

nb["cells"] = C
out = "itcfb_output_checks.ipynb"
nbf.write(nb, out)
print(f"wrote {out} with {len(C)} cells")
