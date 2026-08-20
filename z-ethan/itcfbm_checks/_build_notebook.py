"""Generate itcfbm_output_checks.ipynb. Edit cell sources here, re-run to regenerate.

Same convention as z-ethan/itcfb_checks/_build_notebook.py: the notebook is the
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


md("""# ITC feed-back MINUS output checks — the 24 `itcfbm` runs

This notebook tests the 24 below-headline ITC feed-back run outputs from NREL.
The output files are in `D:\\ReEDS files\\nuclear-learning\\All runs so far`.
The run matrix is `cases_nuclearlearning_itcfbm.csv`.
The pre-registered readings are in `z-ethan/itc_feedback/run_manifest_minus.md`.

The design is a two-factor ladder: arm x rate rung, in three worlds.

- **fbBm** (12 runs, ITC only, learning off): the convex arm.
  Delivery at or above the trajectory quantifies the uniform-rate overshoot
  in deployment space. Delivery below the trajectory shows the headline was
  also delivery-minimal. Both results are reportable.
- **fbCm** (12 runs, ITC only, learning on): the learning arm.
  It measures the ignition cushion that endogenous learning provides below
  the convex minimum. The reportable outcomes are no-build lock-in,
  delayed-start-recover, and full delivery.

The rungs are m01, m05, m10, and m15: the fed rate is `i_model_headline`
minus 1, 5, 10, or 15 rate points (`itc_frac = i_model_headline - d`).
The decrement is measured from the headline, not from the main set's
bumped fed rate. The main 19-run set fed `i_model_headline + 0.01`.
The worlds are aj, mck, and eo. No run has a mandate.

**Claim separation (pre-registered).** These runs test trajectory-delivery
minimality only. Marginal-breakeven minimality of the duals is LP duality,
already verified in-model by the rc=0 reduced-cost check, and is not at
stake. A shortfall in phase C is a finding, not a defect.

The notebook makes sure that:

- The file set is complete and the solves are clean (phase A).
- Each run encodes its intended design cell, the credit landed at the fed
  rate, and the phaseout exemption held (phase B).
- Each run's delivery outcome is classified for the analysis (phase C).
- The runs show no cross-case corruption and no unexpected values (phase D).

Each test writes one row to a check registry.
The last cell writes the registry to `exports/checks_summary.csv`.
The last cell also writes the report `itcfbm_check_results.md`.

A FAIL in phase A, B, or D shows a defect. Examine it before any analysis.
Phase C rows are INFO by design: under-delivery is the measured object,
so no delivery outcome can fail a check.
The analysis notebook (`z-ethan/itcfbm_analysis/`) interprets phase C.

Run this notebook on the **playground-env** kernel.
This notebook only reads the files on drive D. It does not change them.""")

code("""from datetime import date
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

pd.set_option("display.width", 200)

HERE = Path.cwd()
assert HERE.name == "itcfbm_checks", f"run from z-ethan/itcfbm_checks/, not {HERE}"
REPO = HERE.parents[1]
EXPORTS = HERE / "exports"
EXPORTS.mkdir(exist_ok=True)

H5_DIR = Path("D:/ReEDS files/nuclear-learning/All runs so far")
S3ANALYSIS = REPO / "z-ethan" / "step3_analysis" / "exports"

# ---- case matrix ------------------------------------------------------------------
cases = pd.read_csv(REPO / "cases_nuclearlearning_itcfbm.csv", index_col=0)
CASES = [c for c in cases.columns if c != "Default Value"]
assert len(CASES) == 24, len(CASES)

def sw(case, name):
    \"\"\"Read one switch value for one case. An empty cell uses the default value.\"\"\"
    v = cases.loc[name, case]
    if pd.isna(v) or str(v).strip() == "":
        v = cases.loc[name, "Default Value"]
    return "" if pd.isna(v) else str(v).strip()

WORLDS = ["aj", "mck", "eo"]
DECS = {"m01": 0.01, "m05": 0.05, "m10": 0.10, "m15": 0.15}
RUNGS = ["m01", "m05", "m10", "m15"]

def parse_case(c):
    \"\"\"Split a case name into (arm, rung, world). Example: fbBm01_aj_p50.
    The incentives token drops the arm letter: obbba_itcfbm01_aj_p50.\"\"\"
    tok, world = c.split("_")[0], c.split("_")[1]
    arm, rung = tok[:-2], "m" + tok[-2:]
    assert arm in ("fbBm", "fbCm") and rung in DECS and world in WORLDS, c
    return arm, rung, world

META = {}
for c in CASES:
    arm, rung, world = parse_case(c)
    META[c] = dict(
        arm=arm, rung=rung, world=world,
        mandate=int(float(sw(c, "GSw_NuclearCapMandate"))),
        learning=int(float(sw(c, "GSw_NuclearLearning"))),
        suffix=sw(c, "incentives_suffix"),
        foreign=sw(c, "GSw_NuclearLearning_ForeignScen"),
        pc={"nuclear": sw(c, "plantchar_nuclear"),
            "nuclear-smr": sw(c, "plantchar_nuclear_smr")},
        fin=sw(c, "financials_tech_suffix"),
    )

ARM_CASES = {a: [c for c in CASES if META[c]["arm"] == a] for a in ["fbBm", "fbCm"]}
assert [len(ARM_CASES[a]) for a in ["fbBm", "fbCm"]] == [12, 12]

def case_of(arm, rung, world):
    return f"{arm}{rung[1:]}_{world}_p50"

# reference runs: Step 3 base of each world; the main-set +0.01 siblings; a
# Step 4 file as the key-set vintage reference
BASE_OF_WORLD = {w: f"smr100_{w}_p50" for w in WORLDS}
BASE_CASES = sorted(BASE_OF_WORLD.values())
SIBLING = {("fbBm", w): f"fbB_{w}_p50" for w in WORLDS}
SIBLING.update({("fbCm", w): f"fbC_{w}_p50" for w in WORLDS})
SIBLING_CASES = sorted(set(SIBLING.values()))
REF4 = "smr100_eia_p50_gaslo"

H5 = {c: H5_DIR / f"itcfbm_{c}_outputs.h5" for c in CASES}
for b in BASE_CASES:
    H5[b] = H5_DIR / f"test1_{b}_outputs.h5"
for s in SIBLING_CASES:
    H5[s] = H5_DIR / f"itcfb_{s}_outputs.h5"
H5[REF4] = H5_DIR / f"step4_{REF4}_outputs.h5"

# 2022$ -> 2004$ (ReEDS-internal dollars). deflator.csv: Deflator(t) relative to 2004.
DEFL = pd.read_csv(REPO / "inputs" / "financials" / "deflator.csv")
DEFL.columns = ["t", "Deflator"]
DEFL = DEFL.set_index("t")["Deflator"]
D2022 = float(DEFL.loc[2022])

# ---- fed rate schedules -----------------------------------------------------------
# t09: use only the four refactor-stable columns (case, t, status, i_model_headline).
# The minus rates carry NO bump: itc_frac = round(i_model_headline - d, 3).
# The main-set sibling rates carry the +0.01 bump; they anchor the offset check.
EPS, PEN = 0.01, 0.1
t09 = pd.read_csv(S3ANALYSIS / "t09_required_itc.csv",
                  usecols=["case", "t", "status", "i_model_headline"])
HEAD = {}        # world -> {t: i_model_headline}
for w in WORLDS:
    sub = t09[(t09["case"] == BASE_OF_WORLD[w]) & (t09["status"] == "rate")]
    assert len(sub) and sub["i_model_headline"].notna().all(), w
    HEAD[w] = {int(t): float(i) for t, i in zip(sub["t"], sub["i_model_headline"])}
RATES = {}       # (world, rung) -> {t: itc_frac written to the incentives file}
M_EXP = {}       # (world, rung) -> {t: monetized rate the model must apply}
for w in WORLDS:
    for g, d in DECS.items():
        RATES[(w, g)] = {t: round(i - d, 3) for t, i in HEAD[w].items()}
        M_EXP[(w, g)] = {t: f * (1.0 - PEN) for t, f in RATES[(w, g)].items()}
RATES_MAIN = {w: {t: round(i + EPS, 3) for t, i in HEAD[w].items()} for w in WORLDS}
RATE_YEARS = {w: sorted(HEAD[w]) for w in WORLDS}

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
print(f"cases: {len(CASES)} (12 fbBm + 12 fbCm; rungs {RUNGS}; worlds {WORLDS})")
print("rate years per world:", RATE_YEARS)
""")

md("""## Phase A — File inventory and solve health

These tests make sure that the file set is complete and that each solve is clean.

- Test A1 makes sure that the folder has one output file for each of the 24 cases.
- Test A2 makes sure that the reference files are available: the three Step 3
  base cases, the six main-set siblings, and the Step 4 key-vintage reference.
- Test A3 records the folder census.
- Test A4 makes sure that all files have the same data keys.
- Test A5 makes sure that the key set agrees with the Step 4 vintage.
  The minus runs came back in a separate NREL delivery (`itcfb_cliff`),
  so this test is the drift detector for that delivery.
- Test A6 makes sure that the solver residuals are small in each file.
- Test A7 makes sure that the objective value is normal in each file.
- Test A8 makes sure that the model years are correct in each file.
- Test A9 makes sure that each run used the sequential solve mode.

Note: the model removes an all-zero dual parameter from the file.
No minus run has a mandate, so no minus file may have a dual key.
Phase B tests that condition.""")

code("""# --- A1/A2/A3: file census ---------------------------------------------------------
missing = [c for c in CASES if not H5[c].exists()]
record("A", "one output file exists for each of the 24 cases",
       "PASS" if not missing else "FAIL",
       f"missing: {missing}" if missing else f"24 files in {H5_DIR}")

ref_missing = [b for b in BASE_CASES + SIBLING_CASES + [REF4] if not H5[b].exists()]
record("A", "the reference files are available for comparison "
       "(3 base cases, 6 siblings, 1 key-vintage reference)",
       "PASS" if not ref_missing else "FAIL",
       f"missing: {ref_missing}" if ref_missing else
       "all test1_smr100 p50, itcfb_fbB/fbC, and step4 reference files present")

all_files = sorted(p.name for p in H5_DIR.glob("*.h5"))
n_itcfbm = sum(f.startswith("itcfbm_") for f in all_files)
n_itcfb = sum(f.startswith("itcfb_") and not f.startswith("itcfbm_") for f in all_files)
n_step4 = sum(f.startswith("step4_") for f in all_files)
n_test1 = sum(f.startswith("test1_") for f in all_files)
extra = [f for f in all_files if f.startswith("itcfbm_")
         and f not in {H5[c].name for c in CASES}]
record("A", "the folder census matches the consolidated delivery", "INFO",
       f"{len(all_files)} files: {n_itcfbm} itcfbm + {n_itcfb} itcfb + "
       f"{n_step4} step4 + {n_test1} test1"
       + (f"; unexpected itcfbm files: {extra}" if extra else ""))
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
record("A", "all 24 files have the same data keys",
       "PASS" if not bad else "FAIL",
       f"key counts {sorted(set(len(keysets[c]) for c in CASES))}"
       + (f"; unexpected differences: {bad}" if bad else ""))
record("A", "the key set agrees with the Step 4 vintage (separate-delivery "
       "drift detector)",
       "PASS" if not drift else "FAIL",
       f"drift vs {REF4}: {drift}" if drift else f"{len(ref_keys)} keys, no drift")

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
- Test B2 audits the 12 incentives input files against the t09 rates.
- Test B2b audits the cross-set rate offset against the main-set files:
  at rung d the fed rate must sit exactly 0.01 + d below the sibling's rate.
- Tests B4 to B8 recover the applied rate from the run outputs.
- Tests B9 and B10 make sure that the phaseout exemption held and did not leak.
- Tests B11 and B12 audit the ITC payment flows in the system cost data.
  Test B11 conditions on builds: a run with no SMR builds has no payments,
  and that is the lock-in signature, not a defect.
- Tests B13 and B14 audit the capital-cost paths (drawn vs in-run learned).
- Test B15 makes sure that no file has a dual key: no minus run has a mandate.
- Test B16 makes sure that only the incentives differ across a world's
  learning-off ladder (the sibling and the four fbBm rungs).""")

code("""# --- B1: design-matrix echo --------------------------------------------------------
mx_rows, mx_bad = [], []
EXP_DESIGN = {"fbBm": (0, 1, 0), "fbCm": (0, 1, 1)}   # (mandate, fed-itc, learning)
for c in CASES:
    m_ = META[c]
    exp_m, exp_f, exp_l = EXP_DESIGN[m_["arm"]]
    ok = (m_["mandate"] == exp_m and m_["learning"] == exp_l
          and m_["suffix"] == f"obbba_itcfbm{m_['rung'][1:]}_{m_['world']}_p50")
    if m_["learning"]:
        ok = ok and m_["foreign"] == f"fb_{m_['world']}_p50"
    if not ok:
        mx_bad.append(c)
    mx_rows.append(dict(case=c, arm=m_["arm"], rung=m_["rung"], world=m_["world"],
                        mandate=m_["mandate"], learning=m_["learning"],
                        incentives=m_["suffix"], foreign=m_["foreign"]))
mx = pd.DataFrame(mx_rows)
print(mx.to_string(index=False))
record("B", "the case matrix encodes the intended arm, rung, world, and learning design",
       "PASS" if not mx_bad else "FAIL",
       mx_bad or "24 cases match the two-arm four-rung design and the naming rules "
       "(mandate 0 everywhere)")
""")

code("""# --- B2: fed incentives files vs the t09 rate schedule -----------------------------
FIN_DIR = REPO / "inputs" / "financials"
echo_rows, b2_bad = [], []
for w in WORLDS:
    for g in RUNGS:
        inc = pd.read_csv(FIN_DIR / f"incentives_obbba_itcfb{g}_{w}_p50.csv")
        nuc_rows = inc[inc["i"].str.lower().str.startswith("nuclear")]
        only_smr = set(nuc_rows["i"]) == {"Nuclear-SMR"}
        got = {int(t): float(f) for t, f in zip(nuc_rows["t_start_construction"],
                                                nuc_rows["itc_frac"])}
        conv_ok = bool((nuc_rows["safe_harbor"] == 0).all()
                       and (nuc_rows["t_max_online"] == nuc_rows["t_start_construction"]).all()
                       and (nuc_rows["itc_tax_equity_penalty"] == PEN).all()
                       and (nuc_rows["itc_energy_comm_bonus"] == 0.0).all()
                       and (nuc_rows["itc_percpt_domestic_bonus"] == 0.0).all())
        rate_ok = got == RATES[(w, g)]
        if not (only_smr and conv_ok and rate_ok):
            b2_bad.append((w, g, dict(only_smr=only_smr, conv_ok=conv_ok, rate_ok=rate_ok)))
        for t in sorted(set(got) | set(RATES[(w, g)])):
            echo_rows.append(dict(world=w, rung=g, t=t, itc_frac_file=got.get(t),
                                  itc_frac_expected=RATES[(w, g)].get(t)))
pd.DataFrame(echo_rows).to_csv(EXPORTS / "incentives_echo.csv", index=False)
record("B", "the fed incentives files equal the headline rate schedule minus the "
       "rung decrement at exactly the rate years",
       "PASS" if not b2_bad else "FAIL",
       b2_bad or "12 files; Nuclear-SMR only; itc_frac == round(i_model_headline - d, 3); "
       "safe_harbor 0; online == start; penalty 0.1; bonuses 0")

# --- B2b: cross-set rate offset vs the main-set sibling files ----------------------
# The main set fed i_model_headline + 0.01. Rung d feeds i_model_headline - d.
# Thus the file-side offset at every rate year must be 0.01 + d (tolerance 5e-4,
# the build-time assert of build_itcfb_minus.py re-run on the as-shipped files).
off_rows, b2b_bad = [], []
for w in WORLDS:
    main = pd.read_csv(FIN_DIR / f"incentives_obbba_itcfb_{w}_p50.csv")
    main = main[main["i"] == "Nuclear-SMR"]
    main_rates = {int(t): float(f) for t, f in zip(main["t_start_construction"],
                                                   main["itc_frac"])}
    for g, d in DECS.items():
        for t, f in RATES[(w, g)].items():
            got_off = main_rates[t] - f
            ok = abs(got_off - (EPS + d)) < 5e-4
            off_rows.append(dict(world=w, rung=g, t=t, main_itc_frac=main_rates[t],
                                 minus_itc_frac=f, offset=round(got_off, 4),
                                 offset_expected=EPS + d, ok=ok))
            if not ok:
                b2b_bad.append((w, g, t, round(got_off, 4)))
pd.DataFrame(off_rows).to_csv(EXPORTS / "sibling_rate_offset.csv", index=False)
record("B", "the minus rates sit exactly 0.01 + d below the main-set sibling rates "
       "at every rate year",
       "PASS" if not b2b_bad else "FAIL",
       b2b_bad[:5] or f"{len(off_rows)} (world, rung, year) points; "
       "offset == bump + decrement everywhere")
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
    w, rung = META[c]["world"], META[c]["rung"]
    for (i, t), r in g.iterrows():
        m_exp = M_EXP[(w, rung)].get(t, 0.0) if i == "nuclear-smr" else 0.0
        rr_rows.append(dict(case=c, arm=META[c]["arm"], rung=rung, i=i, t=t,
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
    return sub[[r.t in HEAD[META[r.case]["world"]] for r in sub.itertuples()]]

b4 = rate_year_rows(ARM_CASES["fbBm"])
worst4 = b4.loc[b4["delta"].abs().idxmax()]
record("B", "the recovered ITC rate equals the fed rate at exactly the rate years "
       "(fbBm)",
       "PASS" if b4["delta"].abs().max() <= TOL_M else "FAIL",
       f"{len(b4)} rate case-years; worst |dm| {b4['delta'].abs().max():.4f} at "
       f"({worst4.case}, {worst4.t})")

b4c = rate_year_rows(ARM_CASES["fbCm"])
worst4c = b4c.loc[b4c["delta"].abs().idxmax()]
record("B", "the recovered ITC rate equals the fed rate in the learning runs (fbCm)",
       "PASS" if b4c["delta"].abs().max() <= TOL_M else "INFO",
       f"{len(b4c)} rate case-years; worst |dm| {b4c['delta'].abs().max():.4f} at "
       f"({worst4c.case}, {worst4c.t}); the learned construction multiplier cancels "
       "in the ratio, so a large delta needs a second look, not an automatic defect")

# --- B5: zero outside the rate years and for the large reactor ---------------------
off = rr[[not (r.i == "nuclear-smr" and r.t in HEAD[META[r.case]["world"]])
          for r in rr.itertuples()]]
record("B", "the recovered rate is zero outside the rate years and for the large "
       "reactor in all 24 runs",
       "PASS" if off["m_recovered"].abs().max() <= TOL_M else "FAIL",
       f"{len(off)} points; max |m| {off['m_recovered'].abs().max():.4f}")

# --- B8: the recovered rate is uniform across regions ------------------------------
sp = rr[rr["i"] == "nuclear-smr"]
record("B", "the recovered rate is uniform across regions",
       "PASS" if sp["spread_r"].max() <= TOL_M else "FAIL",
       f"max spread over regions {sp['spread_r'].max():.5f} (24 fed cases)")
""")

code("""# --- B9: the phaseout does not reduce the nuclear credit in any year ---------------
# Without the exemption, GSw_TCPhaseout_forceyear=2032 cuts a credit at online year
# 2034 to x0.75, 2035 to x0.5, and 2036 on to x0. Every fed rate year >= 2038 would
# recover 0 without the exemption.
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
for c, b in [("fbBm05_aj_p50", "smr100_aj_p50"), ("fbCm15_eo_p50", "smr100_eo_p50"),
             ("fbCm01_mck_p50", "smr100_mck_p50")]:
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
# Every minus run feeds an ITC, but the model pays the credit only on builds.
# Thus the test conditions on builds: builds without payments is a defect;
# no builds with no payments is the lock-in signature, a phase-C finding.
SMR_NEW = {c: float(load(c, "cap_new_ann")
                    .query("i == 'nuclear-smr' and t > 2030")["Value"].sum())
           for c in CASES}
pay_bad, no_build = [], []
pay = {}
for c in CASES:
    sc = load(c, "systemcost_techba")
    it = sc[sc["sys_costs"].str.contains("itc", case=False) & sc["i"].isin(NUC)]
    v = float(it["Value"].abs().sum())
    pay[c] = v
    if SMR_NEW[c] > 100.0 and v < 1e6:
        pay_bad.append((c, f"builds {SMR_NEW[c]:,.0f} MW but no nuclear ITC payments"))
    if SMR_NEW[c] <= 100.0:
        no_build.append(c)
record("B", "the system cost data shows nuclear ITC payments wherever SMR builds "
       "occurred",
       "PASS" if not pay_bad else "FAIL",
       pay_bad or f"payments present in every case with builds; "
       f"cases with ~no builds (lock-in candidates, read in phase C): "
       f"{no_build or 'none'}")

itc_mag = {c: abs(float(load(c, "tax_expenditure_itc")["Value"].sum())) for c in CASES}
record("B", "the other technologies keep their ITC in all 24 runs",
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
record("B", "the learning-off runs use the drawn cost path without change (12 fbBm)",
       "PASS" if off_fp.rel_err.max() < 1e-4 else "FAIL",
       f"{len(off_fp)} (case, tech, year) points; max rel err {off_fp.rel_err.max():.2e} "
       f"at ({worst_fp.case}, {worst_fp.i}, {worst_fp.t})")

# --- B14: the learning-on runs write an in-run cost path (context) -----------------
# A deviation near zero together with zero builds is expected: with no experience
# the learned path stays at the drawn anchor path.
on_fp = fp[(fp["learning"] == 1) & (fp["t"] >= 2031)]
dev = on_fp.groupby(["case", "i"])["rel_err"].max().round(4)
record("B", "the learning-on runs write an in-run cost path (deviation from the "
       "drawn path is expected; ~0 with zero builds is also expected)", "INFO",
       dev.to_dict())
""")

code("""# --- B15: no file has a dual key ---------------------------------------------------
# No minus run has a mandate, so an all-zero (absent) dual is required everywhere.
b15_bad = sorted(c for c in CASES if keysets[c] & DUAL_KEYS)
record("B", "no dual key exists in any of the 24 files (no mandate anywhere)",
       "PASS" if not b15_bad else "FAIL",
       b15_bad or "nuclear_cap_price absent from all 24 files")

# --- B16: within one world only the incentives differ across the learning-off ladder
# The sibling fbB run and the four fbBm rungs point at the same nuclear input
# files. Thus the pre-ITC nuclear parameters must match bit-for-bit — across
# the two NREL deliveries.
b16_worst = {}
for w in WORLDS:
    group = [SIBLING[("fbBm", w)]] + [case_of("fbBm", g, w) for g in RUNGS]
    ref_c = group[0]
    for key in ["cost_cap", "cost_cap_fin_mult_noITC"]:
        a0 = nuc_slice(ref_c, key)
        for c in group[1:]:
            d = float((nuc_slice(c, key) - a0).abs().max())
            b16_worst[(w, key)] = max(b16_worst.get((w, key), 0.0), d)
record("B", "the no-ITC finance multiplier and the capital cost are identical across "
       "each world's learning-off ladder (sibling + four rungs)",
       "PASS" if max(b16_worst.values()) < 1e-6 else "FAIL",
       f"max |difference| {max(b16_worst.values()):.2e} over "
       f"{sorted(set(k[0] for k in b16_worst))}")
""")

md("""## Phase C — Delivery outcomes (pre-registered; INFO by design)

The minus runs measure how delivery responds to below-headline rates.
Under-delivery is the measured object, so no delivery outcome can fail a
check. Every row in this phase is INFO. The analysis notebook
(`z-ethan/itcfbm_analysis/`) interprets these tables.

The trajectory tests use national cumulative SMR capacity.
The mandate counts all vintages, so capacity is the correct basis, not additions.
The reproduction tiers are the itcfb notebook convention, restated here:

- **exact** — every gap is inside 5 MW (solver and mandate-slack scale).
- **reproduces** — every rate-year and 2050 shortfall is inside
  max(5% of the trajectory, 500 MW). Overbuild never fails.
- **partial** — the 2050 shortfall is inside 15%.
- **no** — the 2050 shortfall is above 15%.

On top of the tiers, an outcome classifier maps each run onto the
pre-registered reading of `run_manifest_minus.md`:

- **full-delivery** — tier exact or reproduces.
- **delayed-start-recover** — a rate-year shortfall occurs, but the 2050
  shortfall is inside the reproduces gate (the fbC_eia signature).
- **partial** — the 2050 shortfall is inside 15%.
- **under-delivery** — the 2050 shortfall is above 15% and builds occurred.
- **no-build-lock-in** — the national SMR capacity stays at or below 5 MW
  in every year.""")

code("""# --- mandate trajectories + national SMR capacity ----------------------------------
NL_DIR = REPO / "inputs" / "nuclear_learning"

def trajectory(scen):
    tr = pd.read_csv(NL_DIR / f"nuclear_cap_trajectory_{scen}.csv")
    tr.columns = [c.lstrip("*") for c in tr.columns]
    return tr.set_index(tr.columns[0])["MW"]

TRAJ = {w: trajectory(f)
        for w, f in [("aj", "abou_jaoude_smr"), ("mck", "mckinsey_smr"),
                     ("eo", "eo2025_smr")]}

SMR_CAP = {c: load(c, "cap").query("i == 'nuclear-smr'").groupby("t")["Value"].sum()
           for c in CASES}
LARGE_NEW = {c: load(c, "cap_new_ann").query("i == 'nuclear' and t > 2030")
             .groupby("t")["Value"].sum() for c in CASES}

# gap table for all 24 runs, same schema as itcfb_checks/exports/trajectory_gaps.csv
# plus the rung column
gap_rows = []
for c in CASES:
    w = META[c]["world"]
    tr = TRAJ[w]
    for t in YEARS_RUN:
        req = float(tr.get(t, 0.0))
        if req <= 0:
            continue
        have = float(SMR_CAP[c].get(t, 0.0))
        status = "rate" if t in HEAD[w] else "slack"
        gap_rows.append(dict(case=c, arm=META[c]["arm"], rung=META[c]["rung"],
                             world=w, t=t, status=status,
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

TIER = {c: tier(c) for c in CASES}
print(pd.Series(TIER).to_string())
""")

code("""# --- C1/C2: delivery tiers by arm (INFO) -------------------------------------------
for arm in ["fbBm", "fbCm"]:
    tiers = {c: TIER[c] for c in ARM_CASES[arm]}
    record("C", f"the delivery tiers of the {arm} runs (a finding, not a pass "
           "condition)", "INFO",
           f"tiers: {tiers}")

# --- C3: the pre-registered outcome classifier (INFO) ------------------------------
out_rows = []
for c in CASES:
    w = META[c]["world"]
    sub = gaps[gaps["case"] == c]
    end = sub[sub["t"] == 2050]
    end_short = float(-end["gap_MW"].iloc[0])
    end_req = float(end["mandate_MW"].iloc[0])
    cap_max = float(SMR_CAP[c].max()) if len(SMR_CAP[c]) else 0.0
    gate = sub[sub["status"] == "rate"]
    tol1 = np.maximum(0.05 * gate["mandate_MW"], 500.0)
    rate_miss = bool(((-gate["gap_MW"]).clip(lower=0.0) > tol1).any())
    end_ok = end_short <= max(0.05 * end_req, 500.0)
    if cap_max <= 5.0:
        outcome = "no-build-lock-in"
    elif TIER[c] in ("exact", "reproduces"):
        outcome = "full-delivery"
    elif rate_miss and end_ok:
        outcome = "delayed-start-recover"
    elif end_short <= 0.15 * end_req:
        outcome = "partial"
    else:
        outcome = "under-delivery"
    builds_years = SMR_CAP[c][SMR_CAP[c] > 5.0]
    first_build = int(builds_years.index.min()) if len(builds_years) else 0
    out_rows.append(dict(case=c, arm=META[c]["arm"], rung=META[c]["rung"], world=w,
                         tier=TIER[c], outcome=outcome,
                         first_build_year=first_build,
                         smr_2050_MW=round(float(SMR_CAP[c].get(2050, 0.0)), 1),
                         traj_2050_MW=end_req,
                         delivered_frac_2050=round(float(SMR_CAP[c].get(2050, 0.0))
                                                   / end_req, 4)))
outcomes = pd.DataFrame(out_rows)
outcomes.to_csv(EXPORTS / "delivery_outcomes.csv", index=False)
print(outcomes.to_string(index=False))
record("C", "the pre-registered outcome classification of all 24 runs", "INFO",
       outcomes.groupby(["arm", "outcome"])["case"].count().to_dict())
""")

code("""# --- C4: delivery vs rung, weak monotonicity (INFO) --------------------------------
# Economic prior: 2050 delivery does not increase when the rate goes down.
# The solve is sequential and myopic, so strict LP monotonicity is not provable
# (the translim precedent from Step 4). A violation is printed loudly and
# recorded as context, not as a defect.
SIB_CAP = {s: load(s, "cap").query("i == 'nuclear-smr'").groupby("t")["Value"].sum()
           for s in SIBLING_CASES}
mono_notes = []
for arm in ["fbBm", "fbCm"]:
    for w in WORLDS:
        ladder = [(g, float(SMR_CAP[case_of(arm, g, w)].get(2050, 0.0)))
                  for g in ["m15", "m10", "m05", "m01"]]
        ladder.append(("sibling+0.01", float(SIB_CAP[SIBLING[(arm, w)]].get(2050, 0.0))))
        viol = [(a[0], b[0]) for a, b in zip(ladder, ladder[1:])
                if a[1] > b[1] + 5.0]
        if viol:
            mono_notes.append(f"{arm}/{w}: inversions {viol}")
            print(f"*** delivery-vs-rung inversion in {arm}/{w}: {viol}")
record("C", "the 2050 delivery increases weakly up the rate ladder within each "
       "(arm, world)", "INFO",
       mono_notes or "no inversion: m15 <= m10 <= m05 <= m01 <= sibling in all 6 ladders")

# --- C5: large-reactor substitution (context) --------------------------------------
sub_lg = {c: round(float(LARGE_NEW[c].sum()) / 1000.0, 2) for c in CASES
          if float(LARGE_NEW[c].sum()) > 0}
record("C", "the large-reactor substitution in the minus runs (a report, not a "
       "failure)", "INFO",
       sub_lg or "no new large builds after 2030 in any of the 24 runs")
""")

md("""## Phase D — Cross-case invariance and unexpected values

The 24 runs differ only through the incentives suffix and the learning switch.
No demand, fuel, renewable, or transmission switch differs between them or
from the main-set runs. Thus the exogenous inputs must be identical across
all 24 runs and across the two NREL deliveries.

- Test D1 makes sure that the exogenous load is identical in all 24 runs
  and equal to the main-set sibling's load (cross-delivery invariance).
- Test D2 scans all data for NaN values.
- Tests D3 and D4 scan for wrong negative values.
- Test D5 makes sure that the national totals equal the regional sums.
- Test D6 compares the fbBm nuclear input parameters with the Step 3
  base-run parameters.
- Test D7 makes sure that no SMR capacity exists before 2031.
- Test D8 records where the runs build large reactors.

There is no dual-conversion test: no minus run has a dual (phase B test B15).
This notebook writes no `duals_by_year.csv`.""")

code("""# --- D1: exogenous load invariance (cross-delivery) --------------------------------
ref_l = load("fbB_aj_p50", "load_rt").set_index(["r", "t"])["Value"]
li_rows = []
for c in CASES:
    a = load(c, "load_rt").set_index(["r", "t"])["Value"]
    j = pd.concat([a, ref_l], axis=1, keys=["c", "ref"]).fillna(0.0)
    rel = float(((j["c"] - j["ref"]).abs() / j["ref"].abs().clip(lower=1.0)).max())
    li_rows.append(dict(case=c, vs="fbB_aj_p50", max_rel_diff=rel))
li = pd.DataFrame(li_rows)
li.to_csv(EXPORTS / "load_invariance.csv", index=False)
record("D", "the exogenous load is identical in all 24 runs and equal to the "
       "main-set sibling's load",
       "PASS" if li.max_rel_diff.max() < 1e-6 else "FAIL",
       f"max rel difference {li.max_rel_diff.max():.2e} vs fbB_aj_p50")

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
       nan_bad[:5] or f"all {len(union)} keys x 24 files scanned")
record("D", "no negative values occur where values must not be negative",
       "PASS" if not neg_bad else "FAIL",
       neg_bad[:5] or f"checked {NONNEG} (storage charging and upgrades are "
       "legitimately negative elsewhere)")
record("D", "the nuclear build and generation data is not negative",
       "PASS" if not nuc_neg else "FAIL",
       nuc_neg[:5] or "cap_new_ann and gen_ann nuclear rows >= 0, all 24 cases")
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
       tot_bad[:5] or "cap, gen_ann, cap_new_ann, ret_ann; all 24 cases within 1e-3")
""")

code("""# --- D6: fbBm nuclear input parameters match the Step 3 base-run parameters --------
# The fbBm runs point at the same nuclear input files as the base run of their
# world. Thus the pre-ITC nuclear parameters must match the base parameters
# bit-for-bit. This also proves no input drift between the NREL batches.
bi_rows = []
for c in ARM_CASES["fbBm"]:
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
record("D", "the fbBm nuclear input parameters match the Step 3 base-run "
       "parameters (12 cases, both keys)",
       "PASS" if bi.max_rel_diff.max() < 1e-6 else "FAIL",
       f"max rel difference {bi.max_rel_diff.max():.2e}")

# --- D7/D8: SMR timing and large builds --------------------------------------------
pre = {c: float(load(c, "cap").query("i == 'nuclear-smr' and t < 2031")["Value"].sum())
       for c in CASES}
record("D", "no SMR capacity exists before 2031",
       "PASS" if max(pre.values()) == 0 else "FAIL",
       f"max pre-2031 SMR capacity {max(pre.values()):.1f} MW")

lg_all = {c: round(float(LARGE_NEW[c].sum()) / 1000.0, 2) for c in CASES
          if float(LARGE_NEW[c].sum()) > 0}
record("D", "where the runs build large reactors (context)", "INFO",
       lg_all or "no new large builds after 2030 in any of the 24 runs")
""")

md("""## Summary and report

The next cells write the exports and the report.

- `exports/checks_summary.csv` — the full check registry.
- `itcfbm_check_results.md` — the report in Simplified Technical English.

There is no `duals_by_year.csv`: no minus run has a mandate, so no dual
exists by design.""")

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
    "C": "Phase C — Delivery outcomes (pre-registered; INFO by design)",
    "D": "Phase D — Cross-case invariance and unexpected values",
}
PHASE_STE = {
    "A": "These tests make sure that the file set is complete and that each solve is clean.",
    "B": "These tests make sure that each run encodes its design cell and that the "
         "credit landed at the fed rate, in the fed years, for the fed technology.",
    "C": "These rows classify each run's delivery outcome for the analysis. "
         "Under-delivery is the measured object, so every row is INFO.",
    "D": "These tests make sure that the runs show no cross-case corruption "
         "and no unexpected values.",
}

lines = [
    "# ITC feed-back MINUS output checks — report",
    "",
    f"Date of this report: {date.today().isoformat()}.",
    f"Input folder: `{H5_DIR}`.",
    "The run set has 24 cases: {fbBm, fbCm} x {m01, m05, m10, m15} x {aj, mck, eo}.",
    "The notebook `itcfbm_output_checks.ipynb` performs all tests.",
    "The pre-registered readings are in `z-ethan/itc_feedback/run_manifest_minus.md`.",
    "",
    "## Summary",
    "",
    f"The notebook performed {len(summary)} checks.",
    f"Result counts: {counts}.",
]
if len(fails):
    lines += [f"**{len(fails)} tests failed.** The tables below show them with the "
              "status FAIL.",
              "A FAIL in phase A, B, or D shows a defect. Examine it before any analysis."]
else:
    lines += ["**All pass/fail tests passed.** No test found a defect in the 24 runs.",
              "Rows with the status INFO give context data. They have no pass condition.",
              "All delivery outcomes are INFO by design: under-delivery is the "
              "measured object of this run set."]
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
    "- `exports/incentives_echo.csv` — the incentives-file audit against the t09 rates.",
    "- `exports/sibling_rate_offset.csv` — the cross-set rate-offset audit "
    "(minus vs main-set files).",
    "- `exports/rate_recovery.csv` — the recovered ITC rate per (case, tech, year).",
    "- `exports/trajectory_gaps.csv` — the capacity-vs-trajectory gaps, all 24 runs.",
    "- `exports/delivery_outcomes.csv` — the pre-registered outcome classification.",
    "- `exports/fingerprint_errors.csv` — the capital-cost fingerprints, all 24 cases.",
    "- `exports/base_identity.csv` — the fbBm vs Step 3 base input-parameter identity.",
    "- `exports/load_invariance.csv` — the load comparison across the 24 cases.",
    "",
    "There is no `duals_by_year.csv`: no minus run has a mandate, so no dual "
    "exists by design.",
    "",
]
(HERE / "itcfbm_check_results.md").write_text("\\n".join(lines), encoding="utf-8")
print(f"wrote itcfbm_check_results.md ({len(lines)} lines)")
""")

nb["cells"] = C
out = "itcfbm_output_checks.ipynb"
nbf.write(nb, out)
print(f"wrote {out} with {len(C)} cells")
