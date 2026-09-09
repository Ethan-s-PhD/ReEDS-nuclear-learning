"""Compose ratedesign2_case_export.ipynb — run infrastructure for batch 6 (rate_design2,
2026-09-08: 93 runs = 36 designed map anchors + 57 credit-arm runs in the 30 solved anchor
worlds; registered in z-ethan/rate_design/methods.md v2.4 BEFORE emission).

The batch is pre-specified by z-ethan/rate_design2/rate_design2.ipynb:
  m01_map_anchor_spec.csv   the 36 Arm-A worlds (maximin placement rule)
  m02_credit_run_spec.csv   the 57 credit runs (arms B-F; convention fbB or fbC; form)
  m04_offers.csv            the offered credit rate per run-year
This notebook is a pure TRANSCRIPTION of those three tables into ReEDS inputs, with the
machinery of the previous batch (`_build_ratedesign_case_export.py`) reused verbatim:
the smr100 case-export cells ported at build time with content asserts, the Export 1/2/2b
writers, the incentives row template, LEARN_FMT, the resolved-switch QA. It emits:

  * per-world input files for the 36 map-anchor worlds (`ma_{ab}_d{w}`) and the 7 fbC
    worlds (`rd_{ab}_d{w}`, the anchor draws of arms D/F) — plantchar x2, financials_tech,
    construction_times; foreign_experience for the fbC worlds only;
  * 57 per-run incentives files (`incentives_obbba_rd_{run}.csv`);
  * cases_nuclearlearning_ratedesign2.csv — 93 columns: Arm A first, then the credit runs
    in m02 order (each boundary world's control precedes its capped run);
  * a QA suite (QA-0 + R1-R11) asserting the transcription against the spec tables and the
    frozen registrations. The fbB runs point at the anchors' EXISTING files (nothing new is
    written for them) — asserted byte-for-byte.

Build with:   python _build_ratedesign2_case_export.py    (json-only; any python)
Execute with: the playground-env kernel (JUPYTER_PATH recipe), end to end.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = json.loads((HERE / "smr100_case_export.ipynb").read_text(encoding="utf-8"))
OUT_PATH = HERE / "ratedesign2_case_export.ipynb"


def src_cell(i, must_contain, patches=()):
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

cells.append(md("""\
# Batch 6 (rate_design2): run infrastructure for the 93 launchable runs

**What this notebook does.** Batch 6 is pre-registered (`z-ethan/rate_design/methods.md`
v2.4, 2026-09-08) and pre-specified by `z-ethan/rate_design2/rate_design2.ipynb`
(`m01` the 36 map-anchor worlds, `m02` the 57 credit runs, `m04` the offered credit rate per
run-year). This notebook TRANSCRIBES those tables into ReEDS inputs; every emission is
asserted back against them. It makes no decision of its own.

1. **36 map-anchor worlds** (`ma_{ab}_d{w}`, Arm A): the smr100 anchor pattern — mandate
   ON, learning OFF, the no-nuclear-ITC baseline, endyear 2050 — with their own plantchar,
   financials and construction-time files from the production generator's own code (ported
   verbatim from `smr100_case_export.ipynb`, QA-0 pinned to `mc_perdraw.npz`).
2. **57 credit runs in the 30 solved anchor worlds** (Arms B–F). Two conventions:
   * **fbB** (arms B, C, E; 43 runs): mandate OFF, learning OFF, the anchor's own EXISTING
     input files, a per-run incentives file, `GSw_TCPhaseout_NuclearExempt = 1`. The run
     sees exactly the cost path the wall was computed on.
   * **fbC** (arms D, F; 14 runs): mandate OFF, learning ON with the world's drawn
     parameters, `rd_{ab}_d{w}` world files + foreign-experience file, a per-run incentives
     file. Seven new fbC worlds (the anchor draws of six far-above worlds and one twin).
3. **57 incentives files** on the minus-probe row template: Nuclear-SMR rows only, one per
   offered year, `safe_harbor=0`, penalty 0.1, `itc_frac` = the m04 offer at 3 decimals
   (headline rate; ReEDS monetizes ×0.9 in-model). The flat-cap runs carry 0.60 in every
   model year 2031–2050.
4. **`cases_nuclearlearning_ratedesign2.csv`** — 93 columns on the previous batch's 31-row
   template (its `Default Value` column). Arm A first, then the credit runs in m02 order.
   All runs are standard-horizon (endyear 2050): no horizon plumbing, no `futurefiles.csv`
   or `cases.csv` edits (the `rd_*` Choices token from the previous batch covers the new
   fbC worlds — asserted).

Frozen inputs (byte-identity asserted at the end): the three spec tables, u80/u81/u82, the
smr100 registrations, the two casefile templates, the baseline incentives file, the shared
construction schedules, `futurefiles.csv`, `cases.csv`.
"""))

cells.append(ported(1, "MASTER_SEED = 20260715", patches=[
    ('EXPORTS = NB_DIR / "exports" / "smr100"', 'EXPORTS = NB_DIR / "exports" / "ratedesign2"'),
    ('os.environ.get("SMR100_DRAWS", 10000)', 'os.environ.get("RATEDESIGN2_DRAWS", 10000)'),
]))

cells.append(code("""\
# --- Frozen-artifact guard: the spec tables and every reused registration must be
# byte-identical after this notebook runs (construction_schedules_mc.csv is re-written from
# the same deterministic code, so equality doubles as a determinism check).
import hashlib

def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

RD_EXPORTS = REPO_ROOT / "z-ethan" / "rate_design" / "exports"
RD2_EXPORTS = REPO_ROOT / "z-ethan" / "rate_design2" / "exports"
S3_EXPORTS = REPO_ROOT / "z-ethan" / "step3_analysis" / "exports"
GUARDED_FILES = [
    RD2_EXPORTS / "m01_map_anchor_spec.csv",
    RD2_EXPORTS / "m02_credit_run_spec.csv",
    RD2_EXPORTS / "m04_offers.csv",
    RD_EXPORTS / "u80_batch_spec.csv",
    RD_EXPORTS / "u81_run_schedules.csv",
    RD_EXPORTS / "u82_anchor_spec.csv",
    S3_EXPORTS / "t09_required_itc.csv",
    NB_DIR / "exports" / "smr100" / "selected_draws.csv",
    NB_DIR / "exports" / "smr100" / "selected_draws_p25p75.csv",
    REPO_ROOT / "cases_nuclearlearning_smr100.csv",
    REPO_ROOT / "cases_nuclearlearning_ratedesign.csv",
    REPO_ROOT / "cases_nuclearlearning_itcfb.csv",
    REPO_ROOT / "cases.csv",
    REPO_ROOT / "inputs" / "userinput" / "futurefiles.csv",
    REPO_ROOT / "inputs" / "financials" / "incentives_obbba_nonuclearitc.csv",
    REPO_ROOT / "inputs" / "financials" / "construction_schedules_mc.csv",
    REPO_ROOT / "inputs" / "plant_characteristics" / "nuclear_mc_smr100_eo_p50.csv",
    REPO_ROOT / "inputs" / "plant_characteristics" / "nuclear-smr_mc_smr100_eo_p50.csv",
]
GUARD_SHA = {p: _sha(p) for p in GUARDED_FILES}
print(f"snapshotted {len(GUARD_SHA)} frozen artifacts (verified unchanged in QA-R7)")
"""))

cells.append(md("""\
## Ported foundations

Verbatim from `smr100_case_export.ipynb`: schedules, PRIS experience stocks, the OCC engine,
the INL duration model, the ReEDS financing replication, the copula draw, and the program-NPV
ranking. Same worlds, same seed streams; QA-0 below pins them to `mc_perdraw.npz`.
"""))
cells.append(ported(3, "US_GW_2024 = 97.0"))
cells.append(ported(4, "def occ_paths_ces"))
cells.append(ported(5, "def load_reeds_financials"))
cells.append(ported(7, "def draw_world"))
cells.append(ported(9, "def om_npv_per_kw"))
cells.append(ported(10, "def rank_smr"))
cells.append(code("""\
mc_score = {s: rank_smr(s) for s in SCHED_ORDER}
print("program-NPV scores computed for all six schedules (labels only; no selection here)")
"""))
cells.append(ported(17, "PCT_TAGS = {"))
cells.append(code("""\
# Continuity pin: the re-derived smr100 selection == the frozen Step-1 registration.
_frozen_sel_full = pd.read_csv(NB_DIR / "exports" / "smr100" / "selected_draws.csv",
                               index_col=["schedule", "percentile"])
assert (_frozen_sel_full["draw_index"] == sel_df["draw_index"]).all(), "selection diverged"
_frozen_sel = _frozen_sel_full.reset_index()
_frozen_p2575 = pd.read_csv(NB_DIR / "exports" / "smr100" / "selected_draws_p25p75.csv")
_frozen30 = pd.concat([_frozen_sel, _frozen_p2575], ignore_index=True)
assert len(_frozen30) == 30
print("continuity pin PASSED: smr100 selections identical to the frozen registration; 30 anchors loaded")
"""))

cells.append(md("""\
## The batch-6 spec

`m01` (36 map-anchor worlds), `m02` (57 credit runs) and `m04` (the offers) are the single
source of truth. Counts are derived from them and echoed against the v2.4 registration
(36 / 57; arms B 26, C 9, D 12, E 8, F 2; fbC 14).
"""))
cells.append(code("""\
m01 = pd.read_csv(RD2_EXPORTS / "m01_map_anchor_spec.csv")
m02 = pd.read_csv(RD2_EXPORTS / "m02_credit_run_spec.csv")
m04 = pd.read_csv(RD2_EXPORTS / "m04_offers.csv")
assert len(m01) == 36 and m01["run"].is_unique
assert len(m02) == 57 and m02["run"].is_unique
assert m02["arm"].value_counts().to_dict() == {"B": 26, "C": 9, "D": 12, "E": 8, "F": 2}
assert set(m04["run"]) == set(m02["run"])
STEM2SCHED = {SHORT[SCEN_TOKEN[s]]: s for s in SCHED_ORDER}     # 'aj' -> 'Abou-Jaoude mod'

# fbB runs point at the anchor's existing files; fbC runs get rd_{ab}_d{w} world files
m02["src_case"] = m02["case"]                                       # smr100_{ab}_{pct}
m02["world_case"] = np.where(m02["convention"] == "fbC",
                             "rd_" + m02["ab"] + "_d" + m02["draw_index"].astype(str),
                             m02["case"])
RUN2WORLD = dict(zip(m02["run"], m02["world_case"]))
FBC_WORLDS = sorted(set(m02.loc[m02["convention"] == "fbC", "world_case"]))
assert len(FBC_WORLDS) == 7, FBC_WORLDS
N_MA, N_CREDIT = len(m01), len(m02)
N_COLS = N_MA + N_CREDIT
assert N_COLS == 93
# distinctness of the new worlds from the previous batch's 48 ITC-arm worlds and the orphans
u80 = pd.read_csv(RD_EXPORTS / "u80_batch_spec.csv")
_itc_arm = {(r["schedule"], int(r["draw_index"])) for _, r in u80[u80["block"] != "horizon"].iterrows()}
_orphans = {("aj", 8436), ("eia", 5843), ("eo", 5602), ("eo", 6903), ("iaea", 1004)}
_new_ma = {(r["ab"], int(r["draw_index"])) for _, r in m01.iterrows()}
_new_rd = {(r["ab"], int(r["draw_index"])) for _, r in m02[m02["convention"] == "fbC"].iterrows()}
assert not (_new_ma & (_itc_arm | _orphans)) and not (_new_rd & (_itc_arm | _orphans))
print(f"spec loaded: {N_MA} map anchors + {N_CREDIT} credit runs ({len(FBC_WORLDS)} new fbC worlds); "
      f"no draw collides with the previous batch's worlds or the orphans")
"""))

cells.append(ported(22, "def build_case_rec"))
cells.append(code("""\
# --- world records: the 36 map anchors (smr100 anchor pattern, case_type 'ma') and the 7
# fbC worlds (case_type 'rd'), selected from the materialized draws by index ---
CASES_MA, CASES_RD2 = {}, {}
for _, r in m01.iterrows():
    sched, idx, case = STEM2SCHED[r["ab"]], int(r["draw_index"]), r["run"]
    w1 = WORLDS[sched].iloc[[idx]].reset_index(drop=True)
    CASES_MA[case] = build_case_rec(case, sched, "ma", w1, float(mc_score[sched][idx]),
                                    {"draw_index": idx})
for _, r in m02[m02["convention"] == "fbC"].drop_duplicates("world_case").iterrows():
    sched, idx, case = STEM2SCHED[r["ab"]], int(r["draw_index"]), r["world_case"]
    w1 = WORLDS[sched].iloc[[idx]].reset_index(drop=True)
    CASES_RD2[case] = build_case_rec(case, sched, "rd", w1, float(mc_score[sched][idx]),
                                     {"draw_index": idx}, program="smr", score_dist=mc_score[sched])
assert len(CASES_MA) == N_MA and len(CASES_RD2) == len(FBC_WORLDS)
ALL_CASES = {**CASES_MA, **CASES_RD2}       # the ported Export 1/2 cells iterate ALL_CASES

sel_rows = []
for case, rec in ALL_CASES.items():
    sched, idx = rec["schedule"], rec["draw_index"]
    sel_rows.append({"case": case, "schedule": sched, "draw_index": idx, "score": rec["score"],
                     "pctile_in_MC": round(100 * float((mc_score[sched] < rec["score"]).mean()), 2),
                     **{c: float(WORLDS[sched].iloc[idx][c]) for c in WORLDS[sched].columns}})
pd.DataFrame(sel_rows).set_index("case").to_csv(EXPORTS / "selected_draws_ratedesign2.csv")

# draw identity vs mc_perdraw.npz for every new world
_npz_rd = np.load(_npz_sel_path, allow_pickle=False)
_rd_cols = list(_npz_rd["world_columns"].astype(str))
for case, rec in ALL_CASES.items():
    tok = SCEN_TOKEN[rec["schedule"]]
    assert _npz_rd[f"worlds_{tok}"].shape[0] == N_DRAWS
    assert _rd_cols == list(WORLDS[rec["schedule"]].columns)
    assert np.allclose(_npz_rd[f"worlds_{tok}"][rec["draw_index"]],
                       WORLDS[rec["schedule"]].iloc[rec["draw_index"]].to_numpy(dtype=float),
                       rtol=1e-9, atol=0), case
print(f"built {len(CASES_MA)} map-anchor + {len(CASES_RD2)} fbC world records; draw identity vs "
      f"mc_perdraw.npz holds for all {len(ALL_CASES)}")
"""))

cells.append(md("""\
## Exports to ReEDS: per-world input files

The Export 1/2 cells are ported verbatim; with `ALL_CASES` bound to the 36 map-anchor + 7 fbC
worlds they write 86 plantchar files, 43 `financials_tech_mc_*`, 43 `construction_times_mc_*`,
the idempotent `dollaryear.csv` registration, and re-write the shared
`construction_schedules_mc.csv` byte-identically (guard-verified in QA-R7). The fbB runs
reuse the anchors' existing files; nothing is written for them.
"""))
cells.append(ported(29, "Export 1: plant-characteristics"))
cells.append(ported(31, "Export 2: shared construction-schedules"))
cells.append(code("""\
# --- Export 2b: foreign-experience files for the 7 fbC worlds at their own drawn u ---
import subprocess, sys

_gen = REPO_ROOT / "inputs" / "nuclear_learning" / "_generate_foreign_experience.py"
_rds2 = REPO_ROOT / "z-ethan" / "mc" / "rds2_2025_units.csv"
assert _gen.exists() and _rds2.exists()
for case, rec in CASES_RD2.items():
    u_val = float(WORLDS[rec["schedule"]].iloc[rec["draw_index"]]["u"])
    out_f = REPO_ROOT / "inputs" / "nuclear_learning" / f"foreign_experience_{case}.csv"
    res = subprocess.run([sys.executable, str(_gen), "--u", f"{u_val:.6f}", "--tag", case,
                          "--rds2", str(_rds2)], capture_output=True, text=True, cwd=str(REPO_ROOT))
    assert res.returncode == 0, (case, res.stdout[-2000:], res.stderr[-2000:])
    fx = pd.read_csv(out_f)
    assert list(fx.columns)[0] == "t" and fx["t"].max() == 2050
    assert fx["foreign_units_cum"].is_monotonic_increasing
print(f"wrote {len(CASES_RD2)} foreign_experience_rd_* files (exact mode, per-world u)")
"""))

cells.append(md("""\
## Per-run incentives files

The minus-probe template: the `obbba_nonuclearitc` baseline with its 8 zeroed `NUCLEAR` rows
removed and one `Nuclear-SMR` row per offered year — `safe_harbor=0`, `t_max_online=t`,
penalty 0.1, no bonuses, `itc_frac` = the m04 `offer_rate` (already at 3 decimals). The file
stores the headline rate; ReEDS monetizes at ×0.9 internally. Map-anchor runs carry no
incentives file (the no-nuclear-ITC baseline).
"""))
cells.append(code("""\
FIN_DIR_ = REPO_ROOT / "inputs" / "financials"
base_inc = (FIN_DIR_ / "incentives_obbba_nonuclearitc.csv").read_text(encoding="utf-8")
base_lines = [ln for ln in base_inc.splitlines() if ln.strip()]
kept = [ln for ln in base_lines if not ln.startswith("NUCLEAR,")]
assert len(base_lines) - len(kept) == 8
PEN = 0.1

def itc_row(tech, t, frac):
    return (f"{tech},usa,{t},0,{t},0.0,0.0,0,0.0,{frac:.3f},0.0,0.0,{PEN},"
            f"0.0,0,0.0,0.0,0,0.0")

INC_SUFFIX = {}
for run, grp in m04.groupby("run", sort=False):
    grp = grp.sort_values("year")
    fed = dict(zip(grp["year"].astype(int), grp["offer_rate"].astype(float)))
    assert 0.0 < min(fed.values()) and max(fed.values()) < 1.0, run
    rows = [itc_row("Nuclear-SMR", t, round(f, 3)) for t, f in fed.items()]
    suffix = f"obbba_rd_{run}"
    INC_SUFFIX[run] = suffix
    (FIN_DIR_ / f"incentives_{suffix}.csv").write_text("\\n".join(kept + rows) + "\\n", encoding="utf-8")
assert len(INC_SUFFIX) == N_CREDIT
print(f"wrote {len(INC_SUFFIX)} incentives files (headline-rate convention, x0.9 monetized in-model)")
"""))

cells.append(md("""\
## Export 3: the cases file

93 columns on the previous batch's 31-row template. **Arm A** = the smr100 anchor column
pattern (mandate ON, no-nuclear-ITC default, learning OFF, endyear 2050) with the world's own
four file pointers and `GSw_TCPhaseout_NuclearExempt = 0`. **fbB runs** = the anchor's own
column (mandate token + its four existing file pointers) with mandate OFF, learning OFF
(explicit), the per-run incentives suffix, phaseout exempt 1 (explicit). **fbC runs** = the
previous batch's ITC-arm pattern with the world's drawn parameters, `rd_*` file pointers and
foreign tag, phaseout exempt 1 (explicit). Column order: Arm A, then m02 order.
"""))
cells.append(code("""\
tmpl = pd.read_csv(REPO_ROOT / "cases_nuclearlearning_ratedesign.csv", index_col=0, dtype=str).fillna("")
base_s100 = pd.read_csv(REPO_ROOT / "cases_nuclearlearning_smr100.csv", index_col=0, dtype=str).fillna("")
_prev = pd.read_csv(REPO_ROOT / "cases_nuclearlearning_ratedesign.csv", index_col=0, dtype=str).fillna("")

def anchor_col(src_case):
    # the anchor's own casefile column: p05/p50/p95 live in the smr100 casefile, p25/p75 in
    # the previous batch's casefile (both frozen, SHA-guarded)
    return base_s100 if src_case in base_s100.columns else _prev

ROWS = list(tmpl.index)
assert len(ROWS) == 31 and ROWS[0] == "ignore"
YEARSET_STD = tmpl.loc["yearset", "Default Value"]
assert [int(y) for y in YEARSET_STD.split("_") if int(y) >= 2031] == [2031, 2032, 2033, 2034, 2035, 2038, 2041, 2044, 2047, 2050]

COPY_ROWS = ["GSw_NuclearCapMandateScen", "plantchar_nuclear", "plantchar_nuclear_smr",
             "financials_tech_suffix", "construction_times_suffix"]
LEARN_FMT = {
    "GSw_NuclearLearning_LR_large":      ("lr_large",   lambda v: f"{v:.6f}"),
    "GSw_NuclearLearning_LR_smr":        ("lr_smr",     lambda v: f"{v:.6f}"),
    "GSw_NuclearLearning_BOAK_large":    ("boak_large", lambda v: f"{v:.2f}"),
    "GSw_NuclearLearning_BOAK_smr":      ("boak_smr",   lambda v: f"{v:.2f}"),
    "GSw_NuclearLearning_Vendors":       ("n_vendors",  lambda v: str(int(v))),
    "GSw_NuclearLearning_Convention":    ("conv_full",  lambda v: str(int(v))),
    "GSw_NuclearLearning_CES_rho":       ("ces_rho",    lambda v: f"{v:g}"),
    "GSw_NuclearLearning_Spillover":     ("s",          lambda v: f"{v:.6f}"),
    "GSw_NuclearLearning_CrossTech_x_ls": ("x_ls",      lambda v: f"{v:.6f}"),
    "GSw_NuclearLearning_CrossTech_x_sl": ("x_sl",      lambda v: f"{v:.6f}"),
    "GSw_NuclearLearning_Dur_Lambda":    ("dur_lambda", lambda v: f"{v:.6f}"),
}

cols = {}
# Arm A: the anchor pattern with the world's own pointers
for _, r in m01.iterrows():
    case, stem = r["run"], r["ab"]
    c = {row: "" for row in ROWS}
    for row in COPY_ROWS:
        c[row] = base_s100.loc[row, f"smr100_{stem}_p50"]
    c["plantchar_nuclear"] = plantchar_name("large", case)
    c["plantchar_nuclear_smr"] = plantchar_name("smr", case)
    c["financials_tech_suffix"] = f"mc_{case}"
    c["construction_times_suffix"] = f"mc_{case}"
    c["GSw_TCPhaseout_NuclearExempt"] = "0"
    cols[case] = c

# credit runs, m02 order
for _, r in m02.iterrows():
    run, stem = r["run"], r["ab"]
    c = {row: "" for row in ROWS}
    c["GSw_NuclearCapMandate"] = "0"
    c["incentives_suffix"] = INC_SUFFIX[run]
    c["GSw_TCPhaseout_NuclearExempt"] = "1"
    if r["convention"] == "fbB":
        for row in COPY_ROWS:
            c[row] = anchor_col(r["src_case"]).loc[row, r["src_case"]]      # the anchor's own token + pointers
        c["GSw_NuclearLearning"] = "0"
    else:
        case = r["world_case"]
        rec = CASES_RD2[case]
        w = WORLDS[rec["schedule"]].iloc[rec["draw_index"]]
        c["GSw_NuclearCapMandateScen"] = SCEN_TOKEN[rec["schedule"]] + "_smr"
        c["plantchar_nuclear"] = plantchar_name("large", case)
        c["plantchar_nuclear_smr"] = plantchar_name("smr", case)
        c["financials_tech_suffix"] = f"mc_{case}"
        c["construction_times_suffix"] = f"mc_{case}"
        c["GSw_NuclearLearning"] = "1"
        c["GSw_NuclearLearning_OCC"] = "1"
        c["GSw_NuclearLearning_Duration"] = "1"
        c["GSw_NuclearLearning_CrossTech"] = "1"
        for sw, (dcol, fmt) in LEARN_FMT.items():
            c[sw] = fmt(float(w[dcol]))
        c["GSw_NuclearLearning_ForeignScen"] = case
    cols[run] = c

assert len(cols) == N_COLS == 93, (len(cols), N_COLS)
defaults = {row: tmpl.loc[row, "Default Value"] for row in ROWS}
cases_rd2 = pd.DataFrame({"Default Value": defaults} | cols).reindex(ROWS)
cases_rd2.index.name = ""
RD2_CASES_PATH = REPO_ROOT / "cases_nuclearlearning_ratedesign2.csv"
cases_rd2.to_csv(RD2_CASES_PATH)
print(f"wrote {RD2_CASES_PATH.name}: {cases_rd2.shape[0]} switch rows x {cases_rd2.shape[1] - 1} run columns "
      f"(launch: python runreeds.py -b <batch> -c nuclearlearning_ratedesign2)")
"""))

cells.append(md("""\
## QA suite

QA-0 (ported world-identity gate) plus the transcription gates R1–R11: casefile ↔ spec order
and count; incentives ↔ m04 + baseline byte-identity; rate bounds; fbC world-switch identity
and fbB switch pattern; plantchar ↔ m04 occ round-trip (D2224); resolved-switch parity per
arm against the reference columns; Choices validation + frozen-artifact byte-identity
(`futurefiles.csv` and `cases.csv` untouched); the maximin placement rule reproduced
independently; fbC plantchar identity with the anchor's file (the pre-override path);
draw distinctness; fbB pointer files present and equal to the anchor column's.
"""))
cells.append(ported(34, "QA-0"))
cells.append(code("""\
# QA-R1 -- casefile transcription: names, order (Arm A, then m02), N_COLS columns, rows.
_back = pd.read_csv(RD2_CASES_PATH, index_col=0, dtype=str).fillna("")
_expected = list(m01["run"]) + list(m02["run"])
assert list(_back.columns) == ["Default Value"] + _expected
assert list(_back.index) == ROWS
_runcols = [c for c in _back.columns if c != "Default Value"]
assert (_back.loc["endyear", _runcols] == "").all() and (_back.loc["yearset", _runcols] == "").all()   # standard horizon everywhere
print(f"QA-R1 PASSED: {N_COLS} columns in spec order (36 map anchors, then the 57 credit runs); "
      f"{len(ROWS)} template rows; all standard-horizon")
"""))
cells.append(code("""\
# QA-R2 -- incentives echo vs m04 + baseline byte-identity; flat-cap rows on all ten model years.
MODEL_YEARS = [2031, 2032, 2033, 2034, 2035, 2038, 2041, 2044, 2047, 2050]
for run in list(m02["run"]):
    txt = (FIN_DIR_ / f"incentives_{INC_SUFFIX[run]}.csv").read_text(encoding="utf-8")
    lines = [ln for ln in txt.splitlines() if ln.strip()]
    body = [ln for ln in lines if not ln.startswith("Nuclear-SMR,")]
    assert body == kept, run
    nuc = [ln.split(",") for ln in lines if ln.startswith("Nuclear-SMR,")]
    got = {int(p[2]): float(p[9]) for p in nuc}
    grp = m04[m04["run"] == run]
    want = {int(t): round(float(x), 3) for t, x in zip(grp["year"], grp["offer_rate"])}
    assert got == want, (run, got, want)
    for p in nuc:
        assert p[3] == "0" and p[4] == p[2] and p[12] == "0.1" and p[10] == "0.0" and p[11] == "0.0", run
    form = m02.loc[m02["run"] == run, "form"].iloc[0]
    if form == "flat60":
        assert sorted(got) == MODEL_YEARS and set(got.values()) == {0.6}, run
    else:
        assert all(t in MODEL_YEARS for t in got), run
n_forms = m02["form"].value_counts().to_dict()
print(f"QA-R2 PASSED: {N_CREDIT} incentives files echo m04 exactly (forms {n_forms}); baselines byte-identical")
"""))
cells.append(code("""\
# QA-R3 -- rate bounds: every fed rate < 1.0; the maximum named (registered: eo_p75 2050 = 0.998).
_mx = m04.loc[m04["offer_rate"].idxmax()]
assert (m04["offer_rate"] < 1.0).all()
assert _mx["run"].startswith("ax_eo_p75") and int(_mx["year"]) == 2050 and abs(_mx["offer_rate"] - 0.998) < 1e-9, _mx
_n_over95 = int((m04.groupby("run")["offer_rate"].max() > 0.95).sum())
print(f"QA-R3 PASSED: all offered rates < 1.0; max {_mx['offer_rate']:.3f} at {_mx['run']} {int(_mx['year'])}; "
      f"{_n_over95} runs exceed the (exempted) 0.95 screen — exact-world runs by registration")
"""))
cells.append(code("""\
# QA-R4 -- fbC columns carry the world's exact drawn parameters, learning ON, an existing
# foreign file; fbB columns carry learning OFF, mandate OFF, no foreign tag, no LEARN switches.
_nl = REPO_ROOT / "inputs" / "nuclear_learning"
for _, r in m02.iterrows():
    run = r["run"]
    assert _back.loc["GSw_NuclearCapMandate", run] == "0"
    if r["convention"] == "fbC":
        rec = CASES_RD2[r["world_case"]]
        w = WORLDS[rec["schedule"]].iloc[rec["draw_index"]]
        for sw, (dcol, fmt) in LEARN_FMT.items():
            assert _back.loc[sw, run] == fmt(float(w[dcol])), (run, sw)
        tag = _back.loc["GSw_NuclearLearning_ForeignScen", run]
        assert tag == r["world_case"] and (_nl / f"foreign_experience_{tag}.csv").exists(), run
        assert _back.loc["GSw_NuclearLearning", run] == "1"
    else:
        assert _back.loc["GSw_NuclearLearning", run] == "0"
        assert _back.loc["GSw_NuclearLearning_ForeignScen", run] == ""
        assert all(_back.loc[sw, run] == "" for sw in LEARN_FMT)
print(f"QA-R4 PASSED: {int((m02['convention'] == 'fbC').sum())} fbC columns carry their world's drawn "
      f"parameters + foreign file; {int((m02['convention'] == 'fbB').sum())} fbB columns are learning OFF")
"""))
cells.append(code("""\
# QA-R5 -- plantchar <-> m04 round-trip: the occ path in the file the run will read (native
# 2022 $/kW) x D2224 equals m04's occ_world_kW (2024 $/kW) in every offered year, for fbB
# (the anchor's existing file) and fbC (the new rd_ file) alike.
PLANTCHAR_DIR_ = REPO_ROOT / "inputs" / "plant_characteristics"
_infl_rd = pd.read_csv(REPO_ROOT / "inputs" / "financials" / "inflation_default.csv").set_index("t")["inflation_rate"]
D2224 = float(_infl_rd.loc[2023] * _infl_rd.loc[2024])
assert 1.0 < D2224 < 1.2, D2224
for _, r in m02.iterrows():
    fname = _back.loc["plantchar_nuclear_smr", r["run"]]
    back = pd.read_csv(PLANTCHAR_DIR_ / f"{fname}.csv").set_index("t")["capcost"]
    grp = m04[m04["run"] == r["run"]]
    for _, q in grp.iterrows():
        occ_2024 = float(back.loc[int(q["year"])]) * D2224
        assert abs(occ_2024 - float(q["occ_world_kW"])) <= 0.06 + 1e-4 * occ_2024, (r["run"], q["year"])
        assert abs(float(q["offer_kW"]) / occ_2024 - float(q["offer_rate"])) <= 5e-4, (r["run"], q["year"])
print(f"QA-R5 PASSED: every credit run's plantchar occ path x D2224 ({D2224:.4f}) equals m04's 2024$ world "
      "path, and offer/occ reproduces the offered rate (<= 5e-4)")
"""))
cells.append(code("""\
# QA-R6 -- RESOLVED-switch parity per arm (cell -> casefile default -> cases.csv default):
#   Arm A vs the smr100 p50 anchor of its schedule: equal except the four file pointers;
#   fbB vs its own smr100 anchor column: equal except mandate (0 vs 1), incentives_suffix,
#     GSw_TCPhaseout_NuclearExempt (1 vs 0); learning resolves to 0 on both;
#   fbC vs the previous batch's fb_aj_m100_cw pattern: equal except the world-specific rows.
_cm6 = pd.read_csv(REPO_ROOT / "cases.csv", index_col=0)
_cm6_def = {str(k): ("" if pd.isna(v) else str(v)) for k, v in _cm6["Default Value"].items()}

def _resolved(df, col, row):
    v = str(df.loc[row, col]) if row in df.index else ""
    if v == "":
        v = str(df.loc[row, "Default Value"]) if row in df.index else ""
    if v == "":
        v = _cm6_def.get(row, "")
    return v

_POINTERS = {"plantchar_nuclear", "plantchar_nuclear_smr", "financials_tech_suffix", "construction_times_suffix"}
for _, r in m01.iterrows():
    run, src = r["run"], f"smr100_{r['ab']}_p50"
    diff = {row for row in ROWS if row != "ignore" and _resolved(_back, run, row) != _resolved(base_s100, src, row)}
    assert diff == _POINTERS, (run, diff)
    assert _resolved(_back, run, "GSw_NuclearCapMandate") == "1" and _resolved(_back, run, "GSw_NuclearLearning") == "0"
    assert _resolved(_back, run, "GSw_TCPhaseout_NuclearExempt") == "0"
_FBB_DIFF = {"GSw_NuclearCapMandate", "incentives_suffix", "GSw_TCPhaseout_NuclearExempt"}
_FBC_WORLD = set(LEARN_FMT) | _POINTERS | {"GSw_NuclearLearning_ForeignScen", "incentives_suffix", "GSw_NuclearCapMandateScen"}
for _, r in m02.iterrows():
    run = r["run"]
    if r["convention"] == "fbB":
        diff = {row for row in ROWS if row != "ignore" and _resolved(_back, run, row) != _resolved(anchor_col(r["src_case"]), r["src_case"], row)}
        assert diff == _FBB_DIFF, (run, diff)
        assert _resolved(_back, run, "GSw_TCPhaseout_NuclearExempt") == "1"
    else:
        diff = {row for row in ROWS if row != "ignore" and _resolved(_back, run, row) != _resolved(_prev, "fb_aj_m100_cw", row)}
        assert diff <= _FBC_WORLD, (run, diff - _FBC_WORLD)
        assert _resolved(_back, run, "GSw_TCPhaseout_NuclearExempt") == "1"
print("QA-R6 PASSED: resolved-switch parity — Arm A = the p50 anchor pattern except the four pointers; "
      "fbB = the anchor's own column except mandate/incentives/phaseout-exempt; fbC = the previous "
      "batch's ITC-arm pattern except the world-specific rows")
"""))
cells.append(code("""\
# QA-R7 -- (b) cases.csv Choices validation (ReEDS's unanchored re.match semantics), the rd_*
# ForeignScen token present; (c) frozen artifacts byte-identical (incl. futurefiles.csv and
# cases.csv — nothing in this batch touches them).
import re as _re
cases_master = pd.read_csv(REPO_ROOT / "cases.csv", index_col=0)
assert r"rd_(eia|aj|iaea|mck|cop28|eo)_d\\d+" in (REPO_ROOT / "cases.csv").read_text(encoding="utf-8")
for switch in _back.index:
    if switch == "ignore":
        continue
    assert switch in cases_master.index, f"unknown switch {switch}"
    choices = str(cases_master.loc[switch, "Choices"])
    for col in _back.columns:
        val = _back.loc[switch, col]
        if val == "" or choices in ("N/A", "nan", "None"):
            continue
        if choices.lower() in ("int", "integer"):
            int(val); continue
        if choices.lower() in ("float", "numeric", "number", "num"):
            float(val); continue
        i_choices = [str(j).strip() for j in np.ravel([c.split(",") for c in choices.split(";")]).tolist()]
        assert any(_re.match(ch, str(val)) for ch in i_choices), (switch, val, choices)
print("QA-R7b PASSED: the casefile passes ReEDS's own Choices validation (prefix re.match)")
for p, sha0 in GUARD_SHA.items():
    assert _sha(p) == sha0, f"frozen artifact changed: {p}"
print("QA-R7c PASSED: all snapshotted frozen artifacts byte-identical (futurefiles.csv, cases.csv untouched)")
"""))
cells.append(code("""\
# QA-R8 -- the map-anchor placement rule reproduced independently from mc_perdraw.npz
# (standardized (log occ2031, occ2050/occ2031) plane; seeds = the five existing anchors;
# candidates inside the 1-99% box minus the anchors, the 48 ITC-arm draws and the orphans;
# greedy maximin, ties -> lowest index; six picks per schedule).
_yi = {int(y): i for i, y in enumerate(_npz_rd["years"])}
_anch30 = {(SHORT[SCEN_TOKEN[s]], int(i)) for s, i in zip(_frozen30["schedule"], _frozen30["draw_index"])}
_PCT = ["p05", "p25", "p50", "p75", "p95"]
for stem, sched in STEM2SCHED.items():
    occ = _npz_rd[f"occ_{SCEN_TOKEN[sched]}_smr"]
    X = np.column_stack([np.log(occ[:, _yi[2031]]), occ[:, _yi[2050]] / occ[:, _yi[2031]]])
    Zs = (X - X.mean(0)) / X.std(0)
    lo, hi = np.quantile(X, [0.01, 0.99], axis=0)
    inbox = (X >= lo).all(1) & (X <= hi).all(1)
    excl = {w for (a, w) in (_itc_arm | _orphans | _anch30) if a == stem}
    cand = np.array([i for i in np.where(inbox)[0] if i not in excl])
    seeds = [int(_frozen30[(_frozen30["schedule"] == sched) & (_frozen30["percentile"] == p)]["draw_index"].iloc[0]) for p in _PCT]
    sel, picks = list(seeds), []
    for _ in range(6):
        d = np.min(np.linalg.norm(Zs[cand][:, None, :] - Zs[sel][None, :, :], axis=2), axis=1)
        j = int(cand[np.argmax(d)]); sel.append(j); picks.append(j)
    want = list(m01[m01["ab"] == stem].sort_values("pick")["draw_index"].astype(int))
    assert picks == want, (stem, picks, want)
print("QA-R8 PASSED: the maximin placement rule reproduces all 36 map-anchor picks in order")
"""))
cells.append(code("""\
# QA-R9 -- fbC plantchar identity: the new rd_ world file's capcost column (y >= ANCHOR)
# equals the anchor's existing smr100 file for the same draw (the pre-override path: the
# learning engine overrides it from 2031 in-run, which is the point of the fbC arm).
for _, r in m02[m02["convention"] == "fbC"].drop_duplicates("world_case").iterrows():
    for tech in ("smr", "large"):
        a = pd.read_csv(PLANTCHAR_DIR_ / f"{plantchar_name(tech, r['world_case'])}.csv").set_index("t")["capcost"]
        b = pd.read_csv(PLANTCHAR_DIR_ / f"{plantchar_name(tech, r['src_case'])}.csv").set_index("t")["capcost"]
        assert (a.loc[a.index >= ANCHOR] == b.loc[b.index >= ANCHOR]).all(), (r["world_case"], tech)
print(f"QA-R9 PASSED: {len(FBC_WORLDS)} fbC world files carry the same drawn cost path as the anchor's file")
"""))
cells.append(code("""\
# QA-R10 -- draw distinctness (re-asserted on the emitted files) and QA-R11 -- fbB pointer files
# exist and equal the anchor column's pointers byte-for-byte.
assert not (_new_ma & _new_rd)
assert not ((_new_ma | _new_rd) & (_itc_arm | _orphans | _anch30 - _new_rd))
for _, r in m02[m02["convention"] == "fbB"].iterrows():
    for row in _POINTERS:
        assert _back.loc[row, r["run"]] == anchor_col(r["src_case"]).loc[row, r["src_case"]], (r["run"], row)
    for p in [PLANTCHAR_DIR_ / f"{_back.loc['plantchar_nuclear_smr', r['run']]}.csv",
              PLANTCHAR_DIR_ / f"{_back.loc['plantchar_nuclear', r['run']]}.csv",
              FIN_DIR_ / f"financials_tech_{_back.loc['financials_tech_suffix', r['run']]}.csv",
              FIN_DIR_ / f"construction_times_{_back.loc['construction_times_suffix', r['run']]}.csv"]:
        assert p.exists(), (r["run"], p.name)
for _, r in m01.iterrows():
    assert not (FIN_DIR_ / f"incentives_obbba_rd_{r['run']}.csv").exists(), r["run"]
print("QA-R10 PASSED: no draw collision; QA-R11 PASSED: every fbB column points at the anchor's "
      "existing files; no incentives file for any map anchor")
"""))

cells.append(md("## Run metadata"))
cells.append(code("""\
import json
import subprocess as _sp
from datetime import datetime, timezone
try:
    _git = _sp.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip()
except Exception:
    _git = "unavailable"
meta = {
    "notebook": "ratedesign2_case_export.ipynb",
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "fork_git_head": _git, "master_seed": MASTER_SEED,
    "built_by": "_build_ratedesign2_case_export.py (ported cells verbatim from smr100_case_export.ipynb)",
    "design": {"batch": f"batch 6 / rate_design2 (methods.md v2.4, 2026-09-08): {N_COLS} columns = "
                        f"{N_MA} map anchors (smr100 pattern) + {N_CREDIT} credit runs "
                        f"({int((m02['convention'] == 'fbB').sum())} fbB, {int((m02['convention'] == 'fbC').sum())} fbC)",
               "spec_source": "z-ethan/rate_design2/exports/m01, m02, m04 (byte-identity guarded)",
               "conventions": {"fbB": "mandate OFF, learning OFF, the anchor's own files, per-run incentives, phaseout exempt 1",
                               "fbC": "mandate OFF, learning ON with drawn parameters, rd_ world files + foreign file, phaseout exempt 1",
                               "map anchor": "mandate ON, learning OFF, no-nuclear-ITC baseline, own files, phaseout exempt 0"},
               "incentives_convention": "headline rate in the file, x0.9 monetized in-model; minus-probe row template",
               "copula_set": COPULA_SET, "n_draws": N_DRAWS},
    "runs": {**{r["run"]: {"arm": "A", "convention": "mandate", "schedule": r["ab"], "draw_index": int(r["draw_index"])}
                for _, r in m01.iterrows()},
             **{r["run"]: {"arm": r["arm"], "convention": r["convention"], "schedule": r["ab"], "world": r["world"],
                           "draw_index": int(r["draw_index"]), "form": r["form"], "cap": (None if pd.isna(r["cap"]) else float(r["cap"])),
                           "gate": r["gate"], "prediction": r["prediction"]} for _, r in m02.iterrows()}},
    "reeds_files": {"cases_file": RD2_CASES_PATH.name, "plantchar": sorted(written_plantchar),
                    "financials_tech": [f"financials_tech_mc_{c}.csv" for c in ALL_CASES],
                    "construction_times": [f"construction_times_mc_{c}.csv" for c in ALL_CASES],
                    "foreign_experience": [f"foreign_experience_{c}.csv" for c in CASES_RD2],
                    "incentives": [f"incentives_{s}.csv" for s in INC_SUFFIX.values()]},
    "exports": {p.name: _sha(p)[:16] for p in sorted(EXPORTS.glob("*.csv"))},
}
with open(EXPORTS / "ratedesign2_metadata.json", "w") as f:
    json.dump(meta, f, indent=2)
print(json.dumps({k: meta[k] for k in ("notebook", "generated_utc", "fork_git_head")}, indent=2))
"""))

cells.append(md("""\
## Closing note

**One case file, 93 launchable runs**: `cases_nuclearlearning_ratedesign2.csv` (launch:
`python runreeds.py -b <batch> -c nuclearlearning_ratedesign2`). Column order: the 36 map
anchors, then the 57 credit runs in spec order. All runs are standard-horizon.

New input files shipped with the batch: 86 plantchar, 43 financials_tech, 43
construction_times, 7 foreign_experience, 57 incentives; the fbB runs reuse the anchors'
existing files. Nothing frozen was touched (QA-R7c). The gates (GC, GW1–GW5, GA1′/GP′, GM0,
GM1) are adjudicated when the batch returns — nothing is drafted before then.
"""))

nb = {"cells": cells, "metadata": SRC["metadata"], "nbformat": SRC["nbformat"], "nbformat_minor": SRC["nbformat_minor"]}
OUT_PATH.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print(f"wrote {OUT_PATH.name}: {len(cells)} cells ({sum(c['cell_type'] == 'code' for c in cells)} code)")
