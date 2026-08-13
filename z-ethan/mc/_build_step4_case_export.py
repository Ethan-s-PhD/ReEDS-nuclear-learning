"""Compose step4_case_export.ipynb — the Step 4 sensitivity-batch case generator.

The notebook is built from two kinds of cells:
  * PORTED cells lifted verbatim (or with asserted single-string patches) from
    smr100_case_export.ipynb at build time, so the MC worlds, ranking, case records,
    and file writers are the production generator's own code by construction;
  * NEW cells (inline below) for the Step-4-specific work: large100 P5/P95 selection,
    the sensitivity switch definitions, the 120-column cases matrix, and the QA suite.

Rebuild with:  python _build_step4_case_export.py   (any python with nbformat-compatible json)
Then run the notebook end to end on the playground-env kernel.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = json.loads((HERE / "smr100_case_export.ipynb").read_text(encoding="utf-8"))
OUT_PATH = HERE / "step4_case_export.ipynb"


def src_cell(i, must_contain, patches=()):
    """Return smr100_case_export cell i's source, asserting identity + applying patches."""
    cell = SRC["cells"][i]
    text = "".join(cell["source"])
    assert must_contain in text, f"cell {i} drifted: {must_contain!r} not found"
    for old, new in patches:
        assert text.count(old) == 1, f"cell {i} patch target not unique: {old!r}"
        text = text.replace(old, new)
    return cell["cell_type"], text


def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": text.splitlines(keepends=True)}


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def ported(i, must_contain, patches=()):
    kind, text = src_cell(i, must_contain, patches)
    return code(text) if kind == "code" else md(text)


cells = []

# ---------------------------------------------------------------- 0: intro
cells.append(md("""\
# Step 4: the sensitivity batch — 120 ReEDS cases

**What this notebook does.** Step 3's 25 production runs (18 `smr100_{sched}_{p05|p50|p95}`
+ 6 `large100_{sched}_p50` comparators + the equality flip copy) are back and checked green
(2026-08-12, `z-ethan/step3_checks/`). This notebook generates the Step 4 batch —
`cases_nuclearlearning_step4.csv`, 120 run columns — from two ratified decisions
(2026-08-12):

1. **Market sensitivities, full coverage:** every smr100 percentile case × six sensitivities
   (`gaslo`/`gashi` gas price, `demhi` high demand, `relo`/`rehi` RE+storage cost,
   `translim` constrained transmission) = 108 columns. These need **no new nuclear input
   files**: each column points at its base case's plantchar/financials/construction-times
   files (the same file-pointer mechanism the Step 3 equality flip copy uses) and overrides
   only the sensitivity switches.
2. **Traditional-nuclear arm completed to percentiles:** `large100_{sched}_{p05|p95}` = 12
   columns, the drawn worlds at P5/P95 of the **pure-large** program-NPV ranking over the
   identical 10k worlds (the P50 cases already ran in Step 3 and are never re-run). These
   12 are the only cases needing new input files (24 plantchar + 12 financials + 12
   construction-times).

A third arm — 18 intertemporal (`timetype=int`) foresight columns — was ratified 2026-08-12
and **cancelled 2026-08-13**: NREL confirmed by email that the intertemporal solver has not
worked for years. The sequential/myopic caveat stays a caveat (issue 5's foresight-vs-myopia
wedge remains analytical, not empirical).

Run arithmetic: 25 (Step 3, spent) + 120 = **145 total; the run ceiling is amended
133 → 145** (163 with the int arm was ratified 2026-08-12, reduced 2026-08-13 on its
cancellation).

The MC re-run below is verbatim `smr100_case_export.ipynb` code (ported at build time by
`_build_step4_case_export.py` with content asserts): same worlds, same seed streams, QA-0
pinned to `mc_perdraw.npz`, base-case selections asserted identical to the frozen
`exports/smr100/` registrations. Step 3 input artifacts are **read-only** here — a snapshot
guard asserts they are byte-identical at the end.
"""))

# ---------------------------------------------------------------- 1: setup (ported, patched)
cells.append(ported(1, "MASTER_SEED = 20260715", patches=[
    ('EXPORTS = NB_DIR / "exports" / "smr100"', 'EXPORTS = NB_DIR / "exports" / "step4"'),
    ('os.environ.get("SMR100_DRAWS", 10000)', 'os.environ.get("STEP4_DRAWS", 10000)'),
]))

# ---------------------------------------------------------------- 2: step-3 artifact guard
cells.append(code("""\
# --- Step 3 artifact guard: everything Step 3 shipped must be byte-identical after this
# notebook runs (the sensitivity columns REUSE those files; nothing may rewrite them).
# construction_schedules_mc.csv is deliberately in the list: the Export-2 cell below
# re-writes it from the same deterministic code, so equality doubles as a determinism check.
import hashlib

def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

GUARDED_STEP3_FILES = [
    REPO_ROOT / "cases_nuclearlearning_smr100.csv",
    REPO_ROOT / "inputs" / "financials" / "construction_schedules_mc.csv",
    REPO_ROOT / "inputs" / "financials" / "financials_tech_mc_smr100_eia_p50.csv",
    REPO_ROOT / "inputs" / "financials" / "construction_times_mc_large100_eo_p50.csv",
    REPO_ROOT / "inputs" / "plant_characteristics" / "nuclear_mc_smr100_eia_p50.csv",
    REPO_ROOT / "inputs" / "plant_characteristics" / "nuclear-smr_mc_large100_eo_p50.csv",
]
GUARD_SHA = {p: _sha(p) for p in GUARDED_STEP3_FILES}
print(f"snapshotted {len(GUARD_SHA)} Step 3 artifacts (verified unchanged in QA-S6)")
"""))

# ---------------------------------------------------------------- foundations (ported)
cells.append(md("""\
## Ported foundations

Verbatim from `smr100_case_export.ipynb` (itself porting `mc_cost_trajectories.ipynb`
S2–S7): schedules, PRIS experience stocks, the OCC engine, the INL duration model, the
ReEDS financing replication, the copula draw, and the program-NPV ranking.
"""))
cells.append(ported(3, "US_GW_2024 = 97.0"))
cells.append(ported(4, "def occ_paths_ces"))
cells.append(ported(5, "def load_reeds_financials"))
cells.append(ported(7, "def draw_world"))
cells.append(ported(9, "def om_npv_per_kw"))
cells.append(ported(10, "def rank_smr"))

# ---------------------------------------------------------------- mc_score
cells.append(code("""\
# The per-schedule program-NPV score vectors. In smr100_case_export.ipynb this line lives
# inside the OAT/monotonicity cell; the bounds/monotonicity machinery itself is NOT ported
# (it is documentation of the Step-1 case selection, already frozen -- see that notebook).
mc_score = {s: rank_smr(s) for s in SCHED_ORDER}
print("program-NPV scores computed for all six schedules")
"""))

# ---------------------------------------------------------------- base selection (ported) + pin
cells.append(md("""\
## Base-case selection, re-derived and pinned

The smr100 P5/P50/P95 selection is re-derived by the ported cell (writing this notebook's
own copy under `exports/step4/`) and then asserted identical to the frozen Step-1
registration in `exports/smr100/selected_draws.csv` — the sensitivity columns point at
those cases' files, so the identity pin is what licenses the reuse.
"""))
cells.append(ported(17, "PCT_TAGS = {"))
cells.append(code("""\
# --- Continuity pin: the re-derived smr100 selection == the frozen Step-1 registration ---
_frozen_sel = pd.read_csv(NB_DIR / "exports" / "smr100" / "selected_draws.csv",
                          index_col=["schedule", "percentile"])
assert list(_frozen_sel.index) == list(sel_df.index)
assert (_frozen_sel["draw_index"] == sel_df["draw_index"]).all(), "draw indices diverged"
_fcols = [c for c in _frozen_sel.columns if c != "draw_index"]
assert np.allclose(_frozen_sel[_fcols].to_numpy(float), sel_df[_fcols].to_numpy(float),
                   rtol=1e-9, atol=0), "selection values diverged from the frozen registration"
print("base-selection pin PASSED: all 18 smr100 selections identical to "
      "exports/smr100/selected_draws.csv (draw indices exact, values rtol 1e-9)")
"""))
cells.append(ported(22, "def build_case_rec"))

# ---------------------------------------------------------------- large100 percentiles
cells.append(md("""\
## The large100 arm, completed to percentiles

The pure-large ranking (`rank_large` over the identical worlds) is ported verbatim,
including its P50 selection and the `tech_comparison` κ=1 pin. A new cell then extends the
selection to P5/P95 (same rank rule), pins the re-derived P50 draws to the Step-3 hard pin
and the frozen `selected_draws_large.csv`, and registers all three percentiles to
`exports/step4/selected_draws_large.csv`. Only the P5/P95 cases get input files — the P50
runs completed in Step 3.
"""))
cells.append(ported(25, "results_large, mc_score_large = {}, {}"))
cells.append(code("""\
# --- P5/P50/P95 of the pure-large ranking; P50 pinned to Step 3 ---
SELECTED_LARGE_PCT = {}
_sel_rows_lpct = []
for sched in SCHED_ORDER:
    order = np.argsort(mc_score_large[sched], kind="stable")
    for tag, q in PCT_TAGS.items():
        idx = int(order[int(np.ceil(q * (N_DRAWS - 1)))])
        SELECTED_LARGE_PCT[(sched, tag)] = {"idx": idx,
                                            "score": float(mc_score_large[sched][idx])}
        _sel_rows_lpct.append({"schedule": sched, "percentile": tag, "draw_index": idx,
                               "score": float(mc_score_large[sched][idx]),
                               "pctile_in_MC": round(100*float(
                                   (mc_score_large[sched] < mc_score_large[sched][idx]).mean()), 3),
                               **{c: float(WORLDS[sched].iloc[idx][c])
                                  for c in WORLDS[sched].columns}})
    # the re-derived P50 must equal the ported cell's (and therefore Step 3's) selection
    assert SELECTED_LARGE_PCT[(sched, "p50")]["idx"] == SELECTED_LARGE[sched]["idx"], sched
sel_large_pct_df = pd.DataFrame(_sel_rows_lpct).set_index(["schedule", "percentile"])
# overwrites the ported cell's p50-only file with the full three-percentile registration
sel_large_pct_df.to_csv(EXPORTS / "selected_draws_large.csv")

# Step-3 hard pin (ratified 2026-08-10) + frozen-file identity for the p50 rows
_LARGE100_PIN = {"eia_aeo_high": 4588, "abou_jaoude": 6297, "iaea_high": 5712,
                 "mckinsey": 7176, "cop28": 8155, "eo2025": 9427}
if N_DRAWS == 10000:
    for sched in SCHED_ORDER:
        assert SELECTED_LARGE_PCT[(sched, "p50")]["idx"] == _LARGE100_PIN[SCEN_TOKEN[sched]], sched
_frozen_lg = pd.read_csv(NB_DIR / "exports" / "smr100" / "selected_draws_large.csv",
                         index_col=["schedule", "percentile"])
for sched in SCHED_ORDER:
    assert int(_frozen_lg.loc[(sched, "p50"), "draw_index"]) \
        == SELECTED_LARGE_PCT[(sched, "p50")]["idx"], sched
    assert np.isclose(float(_frozen_lg.loc[(sched, "p50"), "score"]),
                      SELECTED_LARGE_PCT[(sched, "p50")]["score"], rtol=1e-9), sched

# draw-identity assert vs mc_perdraw.npz for every selected large draw (as the smr cell does)
if _npz_sel_path.exists():
    _npz_lg = np.load(_npz_sel_path, allow_pickle=False)
    _lg_cols = list(_npz_lg["world_columns"].astype(str))
    _lg_checked = 0
    for (sched, tag), s in SELECTED_LARGE_PCT.items():
        tok = SCEN_TOKEN[sched]
        if _npz_lg[f"worlds_{tok}"].shape[0] != N_DRAWS:
            break
        assert _lg_cols == list(WORLDS[sched].columns)
        assert np.allclose(_npz_lg[f"worlds_{tok}"][s["idx"]],
                           WORLDS[sched].iloc[s["idx"]].to_numpy(dtype=float),
                           rtol=1e-9, atol=0), (sched, tag)
        _lg_checked += 1
    if _lg_checked:
        print(f"large-draw identity vs mc_perdraw.npz: {_lg_checked} selections match")

print("\\nSelected large100 percentile draws (p50 = the Step 3 runs, pinned):")
print(sel_large_pct_df[["draw_index", "score", "pctile_in_MC"]].to_string())
"""))
cells.append(code("""\
# --- The 18 large100 percentile records; input files for the 12 NEW cases only ---
CASES_LARGE_PCT = {}
for sched in SCHED_ORDER:
    tok = SCEN_TOKEN[sched]
    for tag in ("p05", "p50", "p95"):
        case = f"large100_{SHORT[tok]}_{tag}"
        idx = SELECTED_LARGE_PCT[(sched, tag)]["idx"]
        w1 = WORLDS[sched].iloc[[idx]].reset_index(drop=True)
        CASES_LARGE_PCT[case] = build_case_rec(case, sched, tag, w1,
                                               SELECTED_LARGE_PCT[(sched, tag)]["score"],
                                               {"draw_index": idx}, program="large",
                                               score_dist=mc_score_large[sched])

# p50 record continuity vs the frozen Step-1 registration (the Step 3 runs' inputs)
_frozen_lgc = pd.read_csv(NB_DIR / "exports" / "smr100" / "selected_cases_large.csv",
                          index_col="case")
for sched in SCHED_ORDER:
    case = f"large100_{SHORT[SCEN_TOKEN[sched]]}_p50"
    assert int(_frozen_lgc.loc[case, "draw_index"]) == CASES_LARGE_PCT[case]["draw_index"], case
    assert np.isclose(float(_frozen_lgc.loc[case, "score"]),
                      CASES_LARGE_PCT[case]["score"], rtol=1e-9), case
    assert float(_frozen_lgc.loc[case, "occ_large_2050"]) \
        == CASES_LARGE_PCT[case]["occ_large_2050"], case

selected_cases_large_pct = pd.DataFrame(
    {c: {k: v for k, v in rec.items() if not isinstance(v, np.ndarray)}
     for c, rec in CASES_LARGE_PCT.items()}).T.set_index("case")
selected_cases_large_pct.to_csv(EXPORTS / "selected_cases_large.csv")

# Only the P5/P95 cases are new runs -- the export cells below write files for these alone.
NEW_CASES = {c: r for c, r in CASES_LARGE_PCT.items() if r["case_type"] in ("p05", "p95")}
ALL_CASES = NEW_CASES        # the ported Export 1/2 cells iterate ALL_CASES
print(f"built {len(CASES_LARGE_PCT)} large100 percentile records "
      f"(p50 continuity vs Step 3 asserted); {len(NEW_CASES)} new cases get input files")
"""))

# ---------------------------------------------------------------- exports (ported writers)
cells.append(md("""\
## Exports to ReEDS

The Export 1/2 cells are ported verbatim; with `ALL_CASES` bound to the 12 new large100
percentile cases they write exactly 24 plantchar files, 12 `financials_tech_mc_*`, 12
`construction_times_mc_*`, the idempotent `dollaryear.csv` registration, and re-write the
shared `construction_schedules_mc.csv` byte-identically (guard-verified). The new cases
matrix is then assembled by the Step-4 assembler below.
"""))
cells.append(ported(29, "Export 1: plant-characteristics"))
cells.append(ported(31, "Export 2: shared construction-schedules"))

# ---------------------------------------------------------------- SENS definitions
cells.append(code("""\
# --- The Step 4 sensitivity definitions: single source of truth (embedded in metadata) ---
# Current-switch-name translations of the NREL Standard Scenarios sensitivities.
# cases_standardscenarios.csv in this fork is STALE (dead switch names: convscen, upvscen,
# ...) and will not parse -- do not copy it. Values verified against cases.csv Choices and
# against the input tree (existence checks below).
#   gaslo/gashi: AEO 2026 High/Low Oil & Gas supply (HOG = LOW gas price, LOG = HIGH).
#   demhi: EER2025 family required -- EER2023 hard-errors against the default
#          resource_adequacy_years; demand_EER2025_100by2050.h5 is fetched from Zenodo via
#          inputs/remote_files.csv (one heads-up line in the email to NREL).
#   relo:  full StdScen Adv_RE fidelity (incl. hydro low, geodiscov TI, distpv low-RE-cost).
#   rehi:  StdScen Con_RE (no hydro/geodiscov override there -- no hydro 'high' exists).
#   translim: StdScen Limited_Trans verbatim. P7 caveat applies: regional/transmission
#          readouts across cost worlds are siting-degenerate -- read national aggregates.
# (An "int" intertemporal arm was defined here 2026-08-12 and removed 2026-08-13: NREL
#  confirmed the intertemporal solver has not worked for years.)
SENS = {
    "gaslo":    {"ngscen": "AEO_2026_HOG"},
    "gashi":    {"ngscen": "AEO_2026_LOG"},
    "demhi":    {"GSw_LoadProfiles": "EER2025_100by2050"},
    "relo":     {"plantchar_upv": "upv_ATB_2024_advanced",
                 "plantchar_onswind": "ons-wind_ATB_2024_advanced",
                 "plantchar_ofswind": "ofs-wind_ATB_2024_advanced",
                 "plantchar_battery": "battery_ATB_2024_advanced",
                 "plantchar_csp": "csp_ATB_2024_advanced",
                 "plantchar_geo": "geo_ATB_2024_advanced",
                 "plantchar_hydro": "hydro_ATB_2019_low",
                 "geodiscov": "TI",
                 "distpvscen": "stscen2023_lowre"},
    "rehi":     {"plantchar_upv": "upv_ATB_2024_conservative",
                 "plantchar_onswind": "ons-wind_ATB_2024_conservative",
                 "plantchar_ofswind": "ofs-wind_ATB_2024_conservative",
                 "plantchar_battery": "battery_ATB_2024_conservative",
                 "plantchar_csp": "csp_ATB_2024_conservative",
                 "plantchar_geo": "geo_ATB_2024_conservative",
                 "distpvscen": "stscen2023_highre"},
    "translim": {"GSw_TransRestrict": "transreg", "GSw_TransInvMaxLongTerm": "1.07"},
}
SENS_ORDER = ["gaslo", "gashi", "demhi", "relo", "rehi", "translim"]
# matrix rows added beyond the Step 3 set (blank Default cells inherit root cases.csv
# defaults)
SENS_SWITCH_ROWS = ["ngscen", "GSw_LoadProfiles", "plantchar_upv", "plantchar_onswind",
                    "plantchar_ofswind", "plantchar_battery", "plantchar_csp",
                    "plantchar_geo", "plantchar_hydro", "geodiscov", "distpvscen",
                    "GSw_TransRestrict", "GSw_TransInvMaxLongTerm"]
assert {k for ov in SENS.values() for k in ov} <= set(SENS_SWITCH_ROWS)

# referenced-input existence: every value must resolve to real files in this fork
for scen in ("AEO_2026_HOG", "AEO_2026_LOG"):
    for stem in ("alpha", "ng", "ng_demand", "ng_tot_demand"):
        assert (REPO_ROOT / "inputs" / "fuelprices" / f"{stem}_{scen}.csv").exists(), (stem, scen)
for ov in SENS.values():
    for row, val in ov.items():
        if row.startswith("plantchar_"):
            assert (REPO_ROOT / "inputs" / "plant_characteristics" / f"{val}.csv").exists(), val
        if row == "distpvscen":
            assert (REPO_ROOT / "inputs" / "dgen_model_inputs" / val).is_dir(), val
_remote = (REPO_ROOT / "inputs" / "remote_files.csv").read_text()
assert "demand_EER2025_100by2050.h5" in _remote, "demand h5 not in remote_files.csv"
print(f"SENS defined: {len(SENS)} sensitivity arms; all referenced input files exist "
      "(demand h5 via Zenodo remote_files entry)")
"""))

# ---------------------------------------------------------------- assembler
cells.append(code("""\
# --- Export 3 (Step 4): the 120-column cases matrix ---
# Same row schema as smr100_case_export's cases_matrix, extended with the sensitivity rows.
# smr100 sensitivity columns are pure FILE-POINTER COPIES of their Step 3 base case
# (the eq-flip mechanism) plus their switch overrides; large100 p05/p95 columns carry
# their own new files and the per-case large-only mandate.
STEP4_CASES = {}
for sens in SENS_ORDER:
    for sched in SCHED_ORDER:
        stem = SHORT[SCEN_TOKEN[sched]]
        for tag in ("p05", "p50", "p95"):
            base = f"smr100_{stem}_{tag}"
            STEP4_CASES[f"{base}_{sens}"] = {
                "scen_token": SCEN_TOKEN[sched], "winner": "smr", "file_case": base,
                "base_case": base, "sens": sens, "overrides": dict(SENS[sens])}
for sched in SCHED_ORDER:
    stem = SHORT[SCEN_TOKEN[sched]]
    for tag in ("p05", "p95"):
        case = f"large100_{stem}_{tag}"
        rec = CASES_LARGE_PCT[case]
        STEP4_CASES[case] = {"scen_token": rec["scen_token"], "winner": "large",
                             "overrides": {}}
assert len(STEP4_CASES) == 6*18 + 12 == 120

_YEARSET = "2010_2015_2020_2023_2026_2029_2031_2032_2033_2034_2035_2038_2041_2044_2047_2050"

def cases_matrix_step4(case_dict):
    n = len(case_dict)
    def _prog(c):
        return case_dict[c].get("winner", "smr")
    def _fc(c):
        return case_dict[c].get("file_case", c)
    def _ov(c, row):
        return case_dict[c].get("overrides", {}).get(row, "")
    rows = {
        "ignore": ["0"] + [""] * n,
        "timetype": ["seq"] + [""] * n,
        "yearset": [_YEARSET] + [""] * n,
        "endyear": ["2050"] + [""] * n,
        "GSw_NuclearCapMandate": ["1"] + [""] * n,          # floor everywhere (issue 6)
        "GSw_NuclearCapMandate_Scale": ["1"] + [""] * n,
        "GSw_NuclearCapMandateTechScen": ["smr"] + ["" if _prog(c) == "smr" else "large"
                                                    for c in case_dict],
        "GSw_NuclearLearning": ["0"] + [""] * n,            # exogenous costs by design
        "incentives_suffix": ["obbba_nonuclearitc"] + [""] * n,   # no-nuclear-ITC baseline
        "construction_schedules_suffix": ["mc"] + [""] * n,
        **{row: [""] + [_ov(c, row) for c in case_dict] for row in SENS_SWITCH_ROWS},
        "GSw_NuclearCapMandateScen": [""] + [case_dict[c]["scen_token"]
                                             + ("_smr" if _prog(c) == "smr" else "_large")
                                             for c in case_dict],
        "plantchar_nuclear": [""] + [plantchar_name("large", _fc(c)) for c in case_dict],
        "plantchar_nuclear_smr": [""] + [plantchar_name("smr", _fc(c)) for c in case_dict],
        "financials_tech_suffix": [""] + [f"mc_{_fc(c)}" for c in case_dict],
        "construction_times_suffix": [""] + [f"mc_{_fc(c)}" for c in case_dict],
    }
    return pd.DataFrame(rows, index=["Default Value"] + list(case_dict)).T

cases_step4 = cases_matrix_step4(STEP4_CASES)
STEP4_CASES_PATH = REPO_ROOT / "cases_nuclearlearning_step4.csv"
cases_step4.to_csv(STEP4_CASES_PATH, index_label="")
print(f"wrote {STEP4_CASES_PATH.name}: {len(STEP4_CASES)} cases "
      f"(launch: python runreeds.py -b <batch> -c nuclearlearning_step4)")
cases_step4.head(12)
"""))

# ---------------------------------------------------------------- QA
cells.append(md("""\
## QA suite

Ported identity checks (QA-0..QA-3) plus the Step-4-specific gates: large100 percentile
identity/placement (QA-S4), export round-trips + `cases.csv` validation (QA-S5), the
matrix regression guard incl. pointer identity against the Step 3 file on disk and the
Step-3-artifact byte-identity snapshot (QA-S6), and baseline/input existence (QA-S7).
"""))
cells.append(ported(34, "QA-0"))
cells.append(ported(35, "QA-1"))
cells.append(ported(36, "QA-2"))
cells.append(ported(37, "QA-3"))
cells.append(code("""\
# QA-S4 -- large100 percentile cases: draw identity, placement, ordering, anchor identity.
NOMINAL_PCT = {"p05": 5.0, "p50": 50.0, "p95": 95.0}
for case, info in CASES_LARGE_PCT.items():
    sched, idx = info["schedule"], info["draw_index"]
    row = WORLDS[sched].iloc[idx]
    for k_rec, k_w in (("lr_large", "lr_large"), ("lr_smr", "lr_smr"),
                       ("boak_large", "boak_large"), ("boak_smr", "boak_smr"),
                       ("u", "u"), ("s_spill", "s"), ("x_ls", "x_ls"), ("x_sl", "x_sl"),
                       ("n_vendors", "n_vendors"), ("ces_rho", "ces_rho"),
                       ("dur_lambda", "dur_lambda"), ("dur_z", "dur_z")):
        assert abs(float(info[k_rec]) - float(row[k_w])) < 1e-12, (case, k_rec)
    pct = 100.0*float((mc_score_large[sched] < info["score"]).mean())
    assert abs(pct - NOMINAL_PCT[info["case_type"]]) <= 0.5, (case, pct)
    assert info["winner"] == "large", case
    # role-swap anchor identities on the exported paths
    assert abs(info["occ_large"][yi(ANCHOR)] - info["boak_large"]) < 0.5, case
    assert abs(info["occ_smr"][yi(ANCHOR)] - info["boak_smr"]) < 0.5, case
for sched in SCHED_ORDER:
    sc = {t: SELECTED_LARGE_PCT[(sched, t)]["score"] for t in NOMINAL_PCT}
    assert sc["p05"] < sc["p50"] < sc["p95"], sched
print("QA-S4 PASSED: all 18 large100 percentile records identical to their registered "
      "draws, at nominal rank +/-0.5 pctile, strictly ordered, anchors exact")
"""))
cells.append(code("""\
# QA-S5 -- export round-trips for the 12 new cases + the new cases file vs cases.csv.
import re as _re

# (a) plantchar round-trip: capcost 2030-2050 = the case's OCC path; pre-anchor = ATB;
#     case-consistent fom/vom
for case, info in NEW_CASES.items():
    for tech in TECH:
        back = pd.read_csv(PLANTCHAR_DIR / f"{plantchar_name(tech, case)}.csv").set_index("t")
        occ = info[f"occ_{tech}"]
        for y in (2030, 2040, 2050):
            assert abs(back.loc[y, "capcost"] - occ[yi(y)]) < 0.1, (case, tech, y)
            assert abs(back.loc[y, "fom"] - info[f"fom_{tech}"]) < 1e-6, (case, tech, y)
            assert abs(back.loc[y, "vom"] - info[f"vom_{tech}"]) < 1e-6, (case, tech, y)
        _atb_t = atb_base[tech].set_index("t")
        assert abs(back.loc[2025, "capcost"] - _atb_t.loc[2025, "capcost"]) < 1e-6
        assert abs(back.loc[2025, "fom"] - _atb_t.loc[2025, "fom"]) < 1e-6

# (b) ccmult from the WRITTEN schedule labels equals the notebook's ccmult (all 12 cases)
cs_back = pd.read_csv(FIN_DIR / "construction_schedules_mc.csv")
for case, info in NEW_CASES.items():
    ft_back = pd.read_csv(FIN_DIR / f"financials_tech_mc_{case}.csv")
    for tech in TECH:
        iname = REEDS_TECH_NAME[tech]
        for y in (2030, 2040, 2050):
            label = ft_back.loc[(ft_back["i"] == iname) & (ft_back["t"] == y),
                                "construction_sch"].iloc[0]
            frac = pd.to_numeric(cs_back[label], errors="coerce").fillna(0.0).to_numpy()
            frac = frac[frac > 0]
            exps = np.arange(len(frac)) + 0.5
            ccm_file = 1.0 + float(np.sum(frac/frac.sum()
                                          * (FIN["interest_base"][yi(y)]**exps - 1.0)))
            mo = info[f"dur_{tech}"][yi(y)]
            ccm_nb = ccmult_from_duration(mo, FIN["interest_base"][yi(y)], FIN["sched"][tech])
            assert abs(ccm_file - ccm_nb) < 2e-5, (case, tech, y, ccm_file, ccm_nb)

# (c) the Step 4 cases file validates against cases.csv's own index and Choices regexes
cases_master = pd.read_csv(REPO_ROOT / "cases.csv", index_col=0)
cases_back = pd.read_csv(STEP4_CASES_PATH, index_col=0, dtype=str).fillna("")
for switch in cases_back.index:
    if switch == "ignore":
        continue
    assert switch in cases_master.index, f"unknown switch {switch}"
    choices = str(cases_master.loc[switch, "Choices"])
    for col in cases_back.columns:
        val = cases_back.loc[switch, col]
        if val == "":
            continue
        if choices in ("N/A", "nan", "int", "float"):
            continue
        tokens = [c.strip() for c in _re.split("[;,]", choices)]
        assert any(_re.match(tok + "$", str(val)) for tok in tokens), (switch, val, choices)

# (d) dollaryear registration idempotent and complete for the new plantchar files
doll_back = pd.read_csv(doll_path)
for n in written_plantchar:
    assert (doll_back["Scenario"] == n).sum() == 1, n

# (e) the fleet-inclusive {scen}_large trajectories the large100 columns point at:
#     existing 80-yr fleet path + this notebook's own program additions
_fleet_gw = US_GW_2024 - np.cumsum(US_RET)
_nl_dir = REPO_ROOT / "inputs" / "nuclear_learning"
for sched in SCHED_ORDER:
    _trajs = {}
    for b in ("large", "smr"):
        tr = pd.read_csv(_nl_dir / f"nuclear_cap_trajectory_{SCEN_TOKEN[sched]}_{b}.csv",
                         comment="*", header=None, names=["t", "mw"]).set_index("t")
        _trajs[b] = tr["mw"].reindex(YEARS).to_numpy() / 1000.0
    assert np.allclose(_trajs["large"], _fleet_gw + np.cumsum(GW_ADD[sched]), atol=2e-3), sched
    assert np.allclose(_trajs["large"] - _trajs["smr"], _fleet_gw, atol=4e-3), sched

print("QA-S5 PASSED: plantchar + ccmult round-trips on all 12 new cases; the Step 4 cases "
      "file validates against cases.csv Choices; dollaryear idempotent; fleet-inclusive "
      "large trajectory identity holds")
"""))
cells.append(code("""\
# QA-S6 -- matrix regression guard + Step 3 byte-identity.
# (a) exact column order: 6 market sens x 18, then large100 p05/p95 x 12
_expected_cols = ["Default Value"]
for sens in SENS_ORDER:
    for sched in SCHED_ORDER:
        for tag in ("p05", "p50", "p95"):
            _expected_cols.append(f"smr100_{SHORT[SCEN_TOKEN[sched]]}_{tag}_{sens}")
for sched in SCHED_ORDER:
    for tag in ("p05", "p95"):
        _expected_cols.append(f"large100_{SHORT[SCEN_TOKEN[sched]]}_{tag}")
assert list(cases_step4.columns) == _expected_cols
assert len(cases_step4.columns) == 1 + 120

# (b) pointer identity vs the Step 3 file ON DISK: every sensitivity column's five
#     pointer rows byte-equal its base case's column in cases_nuclearlearning_smr100.csv
_step3 = pd.read_csv(REPO_ROOT / "cases_nuclearlearning_smr100.csv",
                     index_col=0, dtype=str).fillna("")
_step4 = pd.read_csv(STEP4_CASES_PATH, index_col=0, dtype=str).fillna("")
PTR_ROWS = ["GSw_NuclearCapMandateScen", "plantchar_nuclear", "plantchar_nuclear_smr",
            "financials_tech_suffix", "construction_times_suffix"]
for c, rec in STEP4_CASES.items():
    if "base_case" not in rec:
        continue
    b = rec["base_case"]
    for r in PTR_ROWS:
        assert _step4.loc[r, c] == _step3.loc[r, b] != "", (c, r)

# (c) override audit: each sensitivity column sets exactly its SENS rows + the five pointers
for c, rec in STEP4_CASES.items():
    nonblank = set(_step4.index[_step4[c] != ""])
    if "base_case" in rec:
        assert nonblank == set(PTR_ROWS) | set(rec["overrides"]), (c, nonblank)
        for row, val in rec["overrides"].items():
            assert _step4.loc[row, c] == val, (c, row)
    else:   # large100 percentile columns: own files + the large-only mandate
        assert nonblank == set(PTR_ROWS) | {"GSw_NuclearCapMandateTechScen"}, (c, nonblank)
        assert _step4.loc["GSw_NuclearCapMandateTechScen", c] == "large", c
        assert _step4.loc["GSw_NuclearCapMandateScen", c].endswith("_large"), c
        for r in ("plantchar_nuclear", "financials_tech_suffix"):
            assert c in _step4.loc[r, c], (c, r)   # own file names, never a pointer copy

# (d) no collision with the Step 3 matrix; Default Value column consistent with it
assert not (set(_step4.columns) - {"Default Value"}) & (set(_step3.columns) - {"Default Value"})
for r in _step3.index:
    assert _step4.loc[r, "Default Value"] == _step3.loc[r, "Default Value"], r
for r in SENS_SWITCH_ROWS:
    assert _step4.loc[r, "Default Value"] == "", r

# (e) Step 3 artifacts byte-identical (incl. the deterministically re-written
#     construction_schedules_mc.csv)
for p, sha0 in GUARD_SHA.items():
    assert _sha(p) == sha0, f"Step 3 artifact changed: {p}"

print("QA-S6 PASSED: 120 columns in the registered order; every sensitivity column's "
      "pointers byte-equal its Step 3 base column on disk; overrides exact and minimal; "
      "no column collision; shared defaults identical; all snapshotted Step 3 artifacts "
      "byte-identical")
"""))
cells.append(code("""\
# QA-S7 -- baseline + referenced inputs.
# (a) the no-nuclear-ITC baseline rides as the shared default with blank per-case cells
assert _step4.loc["incentives_suffix", "Default Value"] == "obbba_nonuclearitc"
assert (_step4.loc["incentives_suffix", _step4.columns[1:]] == "").all()
# (b) floor mode everywhere; learning off; mc construction schedules
for r, v in (("GSw_NuclearCapMandate", "1"), ("GSw_NuclearLearning", "0"),
             ("construction_schedules_suffix", "mc")):
    assert _step4.loc[r, "Default Value"] == v
    assert (_step4.loc[r, _step4.columns[1:]] == "").all()
# (c) sequential solver everywhere (the int foresight arm was cancelled 2026-08-13 --
#     NREL: the intertemporal solver has not worked for years)
assert _step4.loc["timetype", "Default Value"] == "seq"
assert (_step4.loc["timetype", _step4.columns[1:]] == "").all()
assert not any(c.endswith("_int") for c in _step4.columns)
# (d) every sensitivity value's input file existence was asserted at definition time
#     (SENS cell); re-assert the two dgen dirs + the remote demand entry here for the record
for v in ("stscen2023_lowre", "stscen2023_highre"):
    assert (REPO_ROOT / "inputs" / "dgen_model_inputs" / v).is_dir(), v
assert "demand_EER2025_100by2050.h5" in (REPO_ROOT / "inputs" / "remote_files.csv").read_text()
print("QA-S7 PASSED: no-nuclear-ITC + floor + learning-off defaults carried; sequential "
      "solver everywhere; sensitivity inputs present (demand h5 via Zenodo)")
"""))

# ---------------------------------------------------------------- metadata
cells.append(md("## Run metadata"))
cells.append(code("""\
import subprocess
from datetime import datetime, timezone

try:
    _git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
                          capture_output=True, text=True).stdout.strip()
except Exception:
    _git = "unavailable"

meta = {
    "notebook": "step4_case_export.ipynb",
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "fork_git_head": _git,
    "master_seed": MASTER_SEED,
    "built_by": "_build_step4_case_export.py (ported cells verbatim from "
                "smr100_case_export.ipynb with build-time content asserts)",
    "design": {
        "batch": "Step 4 sensitivities: 108 market-sensitivity columns (18 smr100 cases x "
                 "6 sensitivities, full coverage ratified 2026-08-12) + 12 large100 "
                 "percentile completions (p05/p95 of the pure-large ranking; p50 ran in "
                 "Step 3). smr100 columns are file-pointer copies of their Step 3 base "
                 "cases (the eq-flip mechanism) -- no new nuclear input files; only the "
                 "12 large100 cases carry new files.",
        "sensitivities": SENS,
        "run_arithmetic": {"step3_spent": 25, "step4_batch": len(STEP4_CASES),
                           "total": 25 + len(STEP4_CASES),
                           "ceiling": "145 (amended 2026-08-13 from 163 on cancellation "
                                      "of the int arm; 163 ratified 2026-08-12; "
                                      "previously 126 -> 133 on 2026-08-10)"},
        "issue7_invariant": "layered (ratified 2026-08-12): dual-decay (bridge) shape "
                            "primary, trajectory ranking secondary, subsidy level "
                            "tertiary -- reporting design, not a case-file input",
        "int_arm_cancelled": "the 18-column intertemporal (timetype=int) foresight arm "
                             "ratified 2026-08-12 was removed 2026-08-13: NREL confirmed "
                             "by email that the intertemporal solver has not worked for "
                             "years; the sequential/myopic caveat stays analytical",
        "selection_continuity": "smr100 selections asserted identical to "
                                "exports/smr100/selected_draws.csv; large100 p50 pinned to "
                                "the Step 3 hard pin + frozen registrations",
        "large100_pctile_draw_indices": {c: int(r["draw_index"])
                                         for c, r in CASES_LARGE_PCT.items()},
        "copula_set": COPULA_SET, "n_draws": N_DRAWS, "ranking": RANKING_FUNCTIONAL},
    "cases_sens": [c for c, r in STEP4_CASES.items() if "base_case" in r],
    "cases_large_pctile": [c for c in STEP4_CASES if c.startswith("large100")],
    "reeds_files": {"cases_file": STEP4_CASES_PATH.name,
                    "plantchar": sorted(written_plantchar),
                    "financials_tech": [f"financials_tech_mc_{c}.csv" for c in NEW_CASES],
                    "construction_times": [f"construction_times_mc_{c}.csv"
                                           for c in NEW_CASES],
                    "construction_schedules": "construction_schedules_mc.csv (unchanged, "
                                              "byte-identity asserted)"},
    "exports": {p.name: _sha(p)[:16] for p in sorted(EXPORTS.glob("*.csv"))},
}
with open(EXPORTS / "step4_metadata.json", "w") as f:
    json.dump(meta, f, indent=2)
print(json.dumps({k: meta[k] for k in ("notebook", "generated_utc", "fork_git_head")},
                 indent=2))
print(f"batch: {len(STEP4_CASES)} runs; totals {meta['design']['run_arithmetic']}")
print(f"full metadata: {EXPORTS / 'step4_metadata.json'}")
"""))

# ---------------------------------------------------------------- closing
cells.append(md("""\
## Closing note

The Step 4 batch is **one case file, 120 runs**: `cases_nuclearlearning_step4.csv`
(launch: `python runreeds.py -b <batch> -c nuclearlearning_step4`). Email notes for NREL:

- `demand_EER2025_100by2050.h5` (the `demhi` arm) is fetched automatically from Zenodo via
  `inputs/remote_files.csv` on first use — no action needed, just a heads-up.
- Everything else reuses input files already shipped with the Step 3 batch; the 12
  `large100_{sched}_{p05|p95}` cases carry their own new input files (included).

All 120 runs use the sequential solver (the 18-column intertemporal arm was cancelled
2026-08-13 — NREL: the intertemporal solver has not worked for years). Analysis-side
reminder recorded in the metadata: the issue-7 layered robustness invariant (bridge shape /
ranking / level).
"""))

nb = {"cells": cells, "metadata": SRC["metadata"],
      "nbformat": SRC["nbformat"], "nbformat_minor": SRC["nbformat_minor"]}
OUT_PATH.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print(f"wrote {OUT_PATH.name}: {len(cells)} cells "
      f"({sum(c['cell_type'] == 'code' for c in cells)} code)")
