"""Compose batch2_case_export.ipynb — run infrastructure for batch 2 (2026-09-10: 83 runs =
36 statute-delivery + 15 learning-ON controls + 20 B2-1 + 12 B2-2; registered in
z-ethan/rate_design/methods.md v2.5 BEFORE emission).

The batch is pre-specified by z-ethan/rate_design2/rate_design2_b2.ipynb:
  m50_b2_run_spec.csv   the 83 runs (block S/K/R1/R2; convention fbB or fbC; form; window)
  m51_b2_offers.csv     the offered credit rate per run-year
  m52_b2_predictions.csv the registered predictions (record)
This notebook is a pure TRANSCRIPTION of those tables into ReEDS inputs, with the
machinery of the previous batches (`_build_ratedesign2_case_export.py`) reused verbatim:
the smr100 case-export cells ported at build time with content asserts, the Export 1/2/2b
writers, the incentives row template, LEARN_FMT, the resolved-switch QA. It emits:

  * per-world input files for the 25 NEW fbC worlds (`rd_{ab}_d{w}`: 15 statute/control
    anchor worlds + 10 fresh B2-1 worlds) — plantchar x2, financials_tech,
    construction_times, foreign_experience; the 3 anchor worlds with existing `rd_` files
    (aj d242, cop28 d1940, eo d2664) are reused and SHA-guarded;
  * 83 per-run incentives files (`incentives_obbba_rd_{run}.csv`);
  * cases_nuclearlearning_batch2.csv — 83 columns in m50 order (S by world, K, R1, R2);
  * a QA suite (QA-0 + R1-R11) asserting the transcription against the spec tables and the
    frozen registrations. The R2 (fbB) runs point at the map anchors' EXISTING `ma_` files
    (nothing new is written for them) — asserted byte-for-byte.

Build with:   python _build_batch2_case_export.py    (json-only; any python)
Execute with: the playground-env kernel (JUPYTER_PATH recipe), end to end.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = json.loads((HERE / "smr100_case_export.ipynb").read_text(encoding="utf-8"))
OUT_PATH = HERE / "batch2_case_export.ipynb"


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
# Batch 2: run infrastructure for the 89 launchable runs

**What this notebook does.** Batch 2 is pre-registered (`z-ethan/rate_design/methods.md`
v2.5, 2026-09-10) and pre-specified by `z-ethan/rate_design2/rate_design2_b2.ipynb` (`m50`
the 89 runs, `m51` the offered credit rate per run-year, `m52` the registered predictions).
This notebook TRANSCRIBES those tables into ReEDS inputs; every emission is asserted back
against them. It makes no decision of its own.

1. **Block S — statute delivery (48 runs, fbC, window 2038):** `flat50` (0.50 in every model
   year) and `grants50` (the exact rate through 2038, then 0.50) in the p05/p25/p50/p75 worlds.
2. **Block K — learning-ON controls (21 runs, fbC):** the exact path in the S worlds without a
   batch-6 control.
3. **Block R1 — B2-1 (20 runs, fbC, window 2035):** map + E6 / + 2·E6 paths in 10 fresh worlds.
4. ~~Block R2 — B2-2~~ withdrawn 2026-09-11 (its 12 slots went to the p05 statute pairs and controls); the
   fbB branch below stays for the record but emits nothing. The withdrawn form was exact / capped-at-0.60 pairs in six
   map-anchor worlds, on the anchors' own `ma_` files.

Conventions (v2.4/v2.5): **fbC** = mandate OFF, learning ON with the world's drawn
parameters, `rd_{ab}_d{w}` world files + foreign-experience file, a per-run incentives file,
`GSw_TCPhaseout_NuclearExempt = 1`. **fbB** = mandate OFF, learning OFF, the world's existing
files, a per-run incentives file, phaseout exempt 1. The incentives file carries the headline
rate; ReEDS monetizes ×0.9 in-model. All runs are standard-horizon (endyear 2050).

Frozen inputs (byte-identity asserted at the end): the three spec tables, the batch-6 spec
and selections (m01/m02/m04, m40–m42b), the smr100 registrations, the four casefiles, the
baseline incentives file, the shared construction schedules, `futurefiles.csv`, `cases.csv`,
the reused `rd_` world files and the six `ma_` world files R2 points at.
"""))

cells.append(ported(1, "MASTER_SEED = 20260715", patches=[
    ('EXPORTS = NB_DIR / "exports" / "smr100"', 'EXPORTS = NB_DIR / "exports" / "batch2"'),
    ('os.environ.get("SMR100_DRAWS", 10000)', 'os.environ.get("BATCH2_DRAWS", 10000)'),
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
PC_DIR_G = REPO_ROOT / "inputs" / "plant_characteristics"
FIN_DIR_G = REPO_ROOT / "inputs" / "financials"
NL_DIR_G = REPO_ROOT / "inputs" / "nuclear_learning"
m50 = pd.read_csv(RD2_EXPORTS / "m50_b2_run_spec.csv")
REUSED_RD = sorted(set(m50.loc[(m50["convention"] == "fbC") & (~m50["new_world_files"]), "world_case"]))
R2_WORLDS = sorted(set(m50.loc[m50["block"] == "R2", "case"]))
assert REUSED_RD == ["rd_aj_d242", "rd_cop28_d1940", "rd_eo_d2664"], REUSED_RD
assert len(R2_WORLDS) == 0     # R2 (B2-2, learning off) withdrawn 2026-09-11; batch 2 has no fbB run
def world_files(case, foreign):
    fs = [PC_DIR_G / f"nuclear_mc_{case}.csv", PC_DIR_G / f"nuclear-smr_mc_{case}.csv",
          FIN_DIR_G / f"financials_tech_mc_{case}.csv", FIN_DIR_G / f"construction_times_mc_{case}.csv"]
    if foreign:
        fs.append(NL_DIR_G / f"foreign_experience_{case}.csv")
    return fs
GUARDED_FILES = [
    RD2_EXPORTS / "m50_b2_run_spec.csv", RD2_EXPORTS / "m51_b2_offers.csv", RD2_EXPORTS / "m52_b2_predictions.csv",
    RD2_EXPORTS / "m01_map_anchor_spec.csv", RD2_EXPORTS / "m02_credit_run_spec.csv", RD2_EXPORTS / "m04_offers.csv",
    RD2_EXPORTS / "m40_map_anchor_excess.csv", RD2_EXPORTS / "m41_b21_world_spec.csv", RD2_EXPORTS / "m41b_b21_offers.csv",
    RD2_EXPORTS / "m42_b22_run_spec.csv", RD2_EXPORTS / "m42b_b22_offers.csv",
    RD_EXPORTS / "u80_batch_spec.csv", RD_EXPORTS / "u82_anchor_spec.csv",
    S3_EXPORTS / "t09_required_itc.csv",
    NB_DIR / "exports" / "smr100" / "selected_draws.csv",
    NB_DIR / "exports" / "smr100" / "selected_draws_p25p75.csv",
    REPO_ROOT / "cases_nuclearlearning_smr100.csv",
    REPO_ROOT / "cases_nuclearlearning_ratedesign.csv",
    REPO_ROOT / "cases_nuclearlearning_ratedesign2.csv",
    REPO_ROOT / "cases_nuclearlearning_itcfb.csv",
    REPO_ROOT / "cases.csv",
    REPO_ROOT / "inputs" / "userinput" / "futurefiles.csv",
    FIN_DIR_G / "incentives_obbba_nonuclearitc.csv",
    FIN_DIR_G / "construction_schedules_mc.csv",
] + [f for c in REUSED_RD for f in world_files(c, True)] + [f for c in R2_WORLDS for f in world_files(c, False)]
for p in GUARDED_FILES:
    assert p.exists(), p
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
## The batch-2 spec

`m50` (83 runs) and `m51` (the offers) are the single source of truth. Counts are derived from
them and echoed against the v2.5 registration as amended 2026-09-11 (S 48, K 21, R1 20; all fbC).
"""))
cells.append(code("""\
m51 = pd.read_csv(RD2_EXPORTS / "m51_b2_offers.csv")
m52 = pd.read_csv(RD2_EXPORTS / "m52_b2_predictions.csv")
m01 = pd.read_csv(RD2_EXPORTS / "m01_map_anchor_spec.csv")
assert len(m50) == 89 and m50["run"].is_unique
assert m50["block"].value_counts().to_dict() == {"S": 48, "K": 21, "R1": 20}
assert m50["convention"].value_counts().to_dict() == {"fbC": 89}
assert set(m51["run"]) == set(m50["run"])
STEM2SCHED = {SHORT[SCEN_TOKEN[s]]: s for s in SCHED_ORDER}     # 'aj' -> 'Abou-Jaoude mod'
RUN2WORLD = dict(zip(m50["run"], m50["world_case"]))
NEW_RD = sorted(set(m50.loc[(m50["convention"] == "fbC") & m50["new_world_files"], "world_case"]))
assert len(NEW_RD) == 31, len(NEW_RD)      # 21 statute/control anchor worlds + 10 fresh R1 worlds
assert not (set(NEW_RD) & set(REUSED_RD))
# a re-emission overwrites this batch's own world files deterministically (QA-R9 re-checks them);
# the batch-6 files are guarded, never rewritten
_b6_rd = {p.name[len("nuclear-smr_mc_"):-4] for p in PC_DIR_G.glob("nuclear-smr_mc_rd_*.csv")} & set(
    pd.read_csv(REPO_ROOT / "cases_nuclearlearning_ratedesign2.csv", index_col=0, dtype=str).fillna("").loc["GSw_NuclearLearning_ForeignScen"].unique())
assert not (set(NEW_RD) & _b6_rd), set(NEW_RD) & _b6_rd
N_COLS = len(m50)
# draw identity of the S/K worlds with the frozen anchors; R1 draws disjoint from every used world
_anch30 = {(SHORT[SCEN_TOKEN[s]], int(i)) for s, i in zip(_frozen30["schedule"], _frozen30["draw_index"])}
u80 = pd.read_csv(RD_EXPORTS / "u80_batch_spec.csv")
_itc_arm = {(r["schedule"], int(r["draw_index"])) for _, r in u80[u80["block"] != "horizon"].iterrows()}
_orphans = {("aj", 8436), ("eia", 5843), ("eo", 5602), ("eo", 6903), ("iaea", 1004)}
_ma36 = {(r["ab"], int(r["draw_index"])) for _, r in m01.iterrows()}
_sk = {(r["ab"], int(r["draw_index"])) for _, r in m50[m50["block"].isin(["S", "K"])].iterrows()}
_r1 = {(r["ab"], int(r["draw_index"])) for _, r in m50[m50["block"] == "R1"].iterrows()}
_r2 = {(r["ab"], int(r["draw_index"])) for _, r in m50[m50["block"] == "R2"].iterrows()}
assert _sk <= _anch30 and len(_sk) == 24
assert not (_r1 & (_anch30 | _itc_arm | _orphans | _ma36)) and len(_r1) == 10
assert len(_r2) == 0
print(f"spec loaded: {N_COLS} runs; {len(NEW_RD)} new fbC worlds, {len(REUSED_RD)} reused; "
      "S/K worlds are the frozen anchors; R1 draws are fresh; R2 worlds are map anchors")
"""))

cells.append(ported(22, "def build_case_rec"))
cells.append(code("""\
# --- world records: the 25 new fbC worlds (case_type 'rd'), selected from the materialized
# draws by index ---
CASES_RD_NEW = {}
for _, r in m50[m50["world_case"].isin(NEW_RD)].drop_duplicates("world_case").iterrows():
    sched, idx, case = STEM2SCHED[r["ab"]], int(r["draw_index"]), r["world_case"]
    assert case == f"rd_{r['ab']}_d{idx}", case
    w1 = WORLDS[sched].iloc[[idx]].reset_index(drop=True)
    CASES_RD_NEW[case] = build_case_rec(case, sched, "rd", w1, float(mc_score[sched][idx]),
                                        {"draw_index": idx}, program="smr", score_dist=mc_score[sched])
assert len(CASES_RD_NEW) == len(NEW_RD)
ALL_CASES = dict(CASES_RD_NEW)       # the ported Export 1/2 cells iterate ALL_CASES

sel_rows = []
for case, rec in ALL_CASES.items():
    sched, idx = rec["schedule"], rec["draw_index"]
    sel_rows.append({"case": case, "schedule": sched, "draw_index": idx, "score": rec["score"],
                     "pctile_in_MC": round(100 * float((mc_score[sched] < rec["score"]).mean()), 2),
                     **{c: float(WORLDS[sched].iloc[idx][c]) for c in WORLDS[sched].columns}})
pd.DataFrame(sel_rows).set_index("case").to_csv(EXPORTS / "selected_draws_batch2.csv")

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
print(f"built {len(CASES_RD_NEW)} new fbC world records; draw identity vs mc_perdraw.npz holds for all")
"""))

cells.append(md("""\
## Exports to ReEDS: per-world input files

The Export 1/2 cells are ported verbatim; with `ALL_CASES` bound to the 25 new fbC worlds they
write 50 plantchar files, 25 `financials_tech_mc_*`, 25 `construction_times_mc_*`, the
idempotent `dollaryear.csv` registration, and re-write the shared
`construction_schedules_mc.csv` byte-identically (guard-verified in QA-R7). Export 2b writes
the 25 foreign-experience files. The reused `rd_` worlds and the R2 `ma_` worlds keep their
existing files; nothing is written for them.
"""))
cells.append(ported(29, "Export 1: plant-characteristics"))
cells.append(ported(31, "Export 2: shared construction-schedules"))
cells.append(code("""\
# --- Export 2b: foreign-experience files for the 25 new fbC worlds at their own drawn u ---
import subprocess, sys

_gen = REPO_ROOT / "inputs" / "nuclear_learning" / "_generate_foreign_experience.py"
_rds2 = REPO_ROOT / "z-ethan" / "mc" / "rds2_2025_units.csv"
assert _gen.exists() and _rds2.exists()
for case, rec in CASES_RD_NEW.items():
    u_val = float(WORLDS[rec["schedule"]].iloc[rec["draw_index"]]["u"])
    out_f = REPO_ROOT / "inputs" / "nuclear_learning" / f"foreign_experience_{case}.csv"
    res = subprocess.run([sys.executable, str(_gen), "--u", f"{u_val:.6f}", "--tag", case,
                          "--rds2", str(_rds2)], capture_output=True, text=True, cwd=str(REPO_ROOT))
    assert res.returncode == 0, (case, res.stdout[-2000:], res.stderr[-2000:])
    fx = pd.read_csv(out_f)
    assert list(fx.columns)[0] == "t" and fx["t"].max() == 2050
    assert fx["foreign_units_cum"].is_monotonic_increasing
print(f"wrote {len(CASES_RD_NEW)} foreign_experience_rd_* files (exact mode, per-world u)")
"""))

cells.append(md("""\
## Per-run incentives files

The minus-probe template: the `obbba_nonuclearitc` baseline with its 8 zeroed `NUCLEAR` rows
removed and one `Nuclear-SMR` row per offered year — `safe_harbor=0`, `t_max_online=t`,
penalty 0.1, no bonuses, `itc_frac` = the m51 `offer_rate` (already at 3 decimals). The file
stores the headline rate; ReEDS monetizes at ×0.9 internally.
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
for run, grp in m51.groupby("run", sort=False):
    grp = grp.sort_values("year")
    fed = dict(zip(grp["year"].astype(int), grp["offer_rate"].astype(float)))
    assert 0.0 < min(fed.values()) and max(fed.values()) < 1.0, run
    rows = [itc_row("Nuclear-SMR", t, round(f, 3)) for t, f in fed.items()]
    suffix = f"obbba_rd_{run}"
    INC_SUFFIX[run] = suffix
    (FIN_DIR_ / f"incentives_{suffix}.csv").write_text("\\n".join(kept + rows) + "\\n", encoding="utf-8")
assert len(INC_SUFFIX) == N_COLS
print(f"wrote {len(INC_SUFFIX)} incentives files (headline-rate convention, x0.9 monetized in-model)")
"""))

cells.append(md("""\
## Export 3: the cases file

89 columns on the previous batches' 31-row template. **fbC runs (S, K, R1)** = the batch-6
fbC pattern: mandate OFF, the schedule's mandate token, learning ON with the world's drawn
parameters, `rd_*` file pointers and foreign tag, the per-run incentives suffix, phaseout
exempt 1. **fbB runs (R2)** = the map anchor's own batch-6 column (mandate token + its four
`ma_` file pointers) with mandate OFF, learning OFF (explicit), the per-run incentives suffix,
phaseout exempt 1. Column order: m50 order (S by world, K, R1, R2).
"""))
cells.append(code("""\
tmpl = pd.read_csv(REPO_ROOT / "cases_nuclearlearning_ratedesign.csv", index_col=0, dtype=str).fillna("")
cases_rd2 = pd.read_csv(REPO_ROOT / "cases_nuclearlearning_ratedesign2.csv", index_col=0, dtype=str).fillna("")
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
for _, r in m50.iterrows():
    run, stem = r["run"], r["ab"]
    c = {row: "" for row in ROWS}
    c["GSw_NuclearCapMandate"] = "0"
    c["incentives_suffix"] = INC_SUFFIX[run]
    c["GSw_TCPhaseout_NuclearExempt"] = "1"
    if r["convention"] == "fbB":
        assert r["block"] == "R2" and r["case"] in cases_rd2.columns, run
        for row in COPY_ROWS:
            c[row] = cases_rd2.loc[row, r["case"]]        # the map anchor's own token + pointers
        c["GSw_NuclearLearning"] = "0"
    else:
        case = r["world_case"]
        sched, idx = STEM2SCHED[stem], int(r["draw_index"])
        w = WORLDS[sched].iloc[idx]
        c["GSw_NuclearCapMandateScen"] = SCEN_TOKEN[sched] + "_smr"
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

assert len(cols) == N_COLS == 89, (len(cols), N_COLS)
defaults = {row: tmpl.loc[row, "Default Value"] for row in ROWS}
cases_b2 = pd.DataFrame({"Default Value": defaults} | cols).reindex(ROWS)
cases_b2.index.name = ""
B2_CASES_PATH = REPO_ROOT / "cases_nuclearlearning_batch2.csv"
cases_b2.to_csv(B2_CASES_PATH)
print(f"wrote {B2_CASES_PATH.name}: {cases_b2.shape[0]} switch rows x {cases_b2.shape[1] - 1} run columns "
      f"(launch: python runreeds.py -b <batch> -c nuclearlearning_batch2)")
"""))

cells.append(md("""\
## QA suite

QA-0 (ported world-identity gate) plus the transcription gates R1–R11: casefile ↔ spec order
and count; incentives ↔ m51 + baseline byte-identity, per form; rate bounds; fbC world-switch
identity and fbB switch pattern; plantchar ↔ m51 occ round-trip (D2224); resolved-switch parity
per block against the reference columns, plus the instrument-only parity of each S world's
pair against its control (R6b); Choices validation + frozen-artifact byte-identity; draw
membership per block; fbC plantchar identity with the anchor's file (S/K) or the npz path
(R1); no draw collision; fbB pointer files present and equal to the anchor column's.
"""))
cells.append(ported(34, "QA-0"))
cells.append(code("""\
# QA-R1 -- casefile transcription: names, order (m50), N_COLS columns, rows.
_back = pd.read_csv(B2_CASES_PATH, index_col=0, dtype=str).fillna("")
assert list(_back.columns) == ["Default Value"] + list(m50["run"])
assert list(_back.index) == ROWS
_runcols = [c for c in _back.columns if c != "Default Value"]
assert (_back.loc["endyear", _runcols] == "").all() and (_back.loc["yearset", _runcols] == "").all()
print(f"QA-R1 PASSED: {N_COLS} columns in m50 order; {len(ROWS)} template rows; all standard-horizon")
"""))
cells.append(code("""\
# QA-R2 -- incentives echo vs m51 + baseline byte-identity, per form.
MODEL_YEARS = [2031, 2032, 2033, 2034, 2035, 2038, 2041, 2044, 2047, 2050]
W_S, W_R, CAP_S = 2038, 2035, 0.50
POST_S = [t for t in MODEL_YEARS if t > W_S]
t09 = pd.read_csv(S3_EXPORTS / "t09_required_itc.csv")
t09r = t09[t09["status"] == "rate"].set_index(["case", "t"])["i_model_headline"]
def rate_years(case):
    return sorted(int(t) for (c, t) in t09r.index if c == case)
FORM = dict(zip(m50["run"], m50["form"]))
for _, r in m50.iterrows():
    run = r["run"]
    txt = (FIN_DIR_ / f"incentives_{INC_SUFFIX[run]}.csv").read_text(encoding="utf-8")
    lines = [ln for ln in txt.splitlines() if ln.strip()]
    body = [ln for ln in lines if not ln.startswith("Nuclear-SMR,")]
    assert body == kept, run
    nuc = [ln.split(",") for ln in lines if ln.startswith("Nuclear-SMR,")]
    got = {int(p[2]): float(p[9]) for p in nuc}
    grp = m51[m51["run"] == run]
    want = {int(t): round(float(x), 3) for t, x in zip(grp["year"], grp["offer_rate"])}
    assert got == want, (run, got, want)
    for p in nuc:
        assert p[3] == "0" and p[4] == p[2] and p[12] == "0.1" and p[10] == "0.0" and p[11] == "0.0", run
    form = r["form"]
    if form == "flat50":
        assert sorted(got) == MODEL_YEARS and set(got.values()) == {CAP_S}, run
    elif form == "grants50":
        ys = rate_years(f"smr100_{r['world']}")
        assert sorted(got) == sorted(set(t for t in ys if t <= W_S) | set(POST_S)), run
        assert all(got[t] == CAP_S for t in POST_S), run
        assert all(abs(got[t] - round(float(t09r[(f"smr100_{r['world']}", t)]), 3)) < 1e-9 for t in got if t <= W_S), run
    elif form == "exact":
        src_case = f"smr100_{r['world']}" if r["block"] == "K" else r["case"]
        if r["block"] == "K":
            assert sorted(got) == rate_years(src_case), run
    elif form == "capped_post2035":
        ctrl = m51[m51["run"] == run.replace("_c60", "_u")].set_index("year")["offer_rate"]
        assert all(got[t] == round(float(ctrl.loc[t]), 3) for t in got if t <= W_R), run
        assert all(got[t] <= 0.60 + 1e-9 for t in got if t > W_R), run
    else:
        assert form in ("map_plus_1e6", "map_plus_2e6") and max(got.values()) <= 0.95 + 1e-9, run
print(f"QA-R2 PASSED: {N_COLS} incentives files echo m51 exactly (forms {m50['form'].value_counts().to_dict()}); "
      "baselines byte-identical")
"""))
cells.append(code("""\
# QA-R3 -- rate bounds: every fed rate < 1.0; the maximum named.
_mx = m51.loc[m51["offer_rate"].idxmax()]
assert (m51["offer_rate"] < 1.0).all()
print(f"QA-R3 PASSED: all offered rates < 1.0; max {_mx['offer_rate']:.3f} at {_mx['run']} {int(_mx['year'])}")
"""))
cells.append(code("""\
# QA-R4 -- fbC columns carry the world's exact drawn parameters, learning ON, an existing
# foreign file; fbB columns carry learning OFF, mandate OFF, no foreign tag, no LEARN switches.
_nl = REPO_ROOT / "inputs" / "nuclear_learning"
for _, r in m50.iterrows():
    run = r["run"]
    assert _back.loc["GSw_NuclearCapMandate", run] == "0"
    if r["convention"] == "fbC":
        sched, idx = STEM2SCHED[r["ab"]], int(r["draw_index"])
        w = WORLDS[sched].iloc[idx]
        for sw, (dcol, fmt) in LEARN_FMT.items():
            assert _back.loc[sw, run] == fmt(float(w[dcol])), (run, sw)
        tag = _back.loc["GSw_NuclearLearning_ForeignScen", run]
        assert tag == r["world_case"] and (_nl / f"foreign_experience_{tag}.csv").exists(), run
        assert _back.loc["GSw_NuclearLearning", run] == "1"
    else:
        assert _back.loc["GSw_NuclearLearning", run] == "0"
        assert _back.loc["GSw_NuclearLearning_ForeignScen", run] == ""
        assert all(_back.loc[sw, run] == "" for sw in LEARN_FMT)
print(f"QA-R4 PASSED: {int((m50['convention'] == 'fbC').sum())} fbC columns carry their world's drawn "
      f"parameters + foreign file; {int((m50['convention'] == 'fbB').sum())} fbB columns are learning OFF")
"""))
cells.append(code("""\
# QA-R5 -- plantchar <-> m51 round-trip: the occ path in the file the run will read (native
# 2022 $/kW) x D2224 equals m51's occ_world_kW (2024 $/kW) in every offered year.
PLANTCHAR_DIR_ = REPO_ROOT / "inputs" / "plant_characteristics"
_infl_rd = pd.read_csv(REPO_ROOT / "inputs" / "financials" / "inflation_default.csv").set_index("t")["inflation_rate"]
D2224 = float(_infl_rd.loc[2023] * _infl_rd.loc[2024])
assert 1.0 < D2224 < 1.2, D2224
for _, r in m50.iterrows():
    fname = _back.loc["plantchar_nuclear_smr", r["run"]]
    back = pd.read_csv(PLANTCHAR_DIR_ / f"{fname}.csv").set_index("t")["capcost"]
    grp = m51[m51["run"] == r["run"]]
    for _, q in grp.iterrows():
        occ_2024 = float(back.loc[int(q["year"])]) * D2224
        assert abs(occ_2024 - float(q["occ_world_kW"])) <= 0.06 + 1e-4 * occ_2024, (r["run"], q["year"])
        assert abs(float(q["offer_kW"]) / occ_2024 - float(q["offer_rate"])) <= 5e-4, (r["run"], q["year"])
print(f"QA-R5 PASSED: every run's plantchar occ path x D2224 ({D2224:.4f}) equals m51's 2024$ world path, "
      "and offer/occ reproduces the offered rate (<= 5e-4)")
"""))
cells.append(code("""\
# QA-R6 -- RESOLVED-switch parity (cell -> casefile default -> cases.csv default):
#   fbC (S/K/R1) vs the batch-6 fbC pattern (ax_aj_p50_u_lrn): equal except the world-specific rows;
#   fbB (R2) vs its own ma_ column: equal except mandate (0 vs 1), incentives_suffix, phaseout exempt (1 vs 0);
#   R6b: each S world's f50 / g50 columns vs the world's control column (this batch or batch 6): only incentives_suffix.
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
_FBB_DIFF = {"GSw_NuclearCapMandate", "incentives_suffix", "GSw_TCPhaseout_NuclearExempt"}
_FBC_WORLD = set(LEARN_FMT) | _POINTERS | {"GSw_NuclearLearning_ForeignScen", "incentives_suffix", "GSw_NuclearCapMandateScen"}
for _, r in m50.iterrows():
    run = r["run"]
    if r["convention"] == "fbB":
        diff = {row for row in ROWS if row != "ignore" and _resolved(_back, run, row) != _resolved(cases_rd2, r["case"], row)}
        assert diff == _FBB_DIFF, (run, diff)
    else:
        diff = {row for row in ROWS if row != "ignore" and _resolved(_back, run, row) != _resolved(cases_rd2, "ax_aj_p50_u_lrn", row)}
        assert diff <= _FBC_WORLD, (run, diff - _FBC_WORLD)
    assert _resolved(_back, run, "GSw_TCPhaseout_NuclearExempt") == "1"
for _, r in m50[m50["block"] == "S"].iterrows():
    ctrl, cf = r["control_run"], r["control_casefile"]
    ref = _back if cf.endswith("batch2.csv") else cases_rd2
    assert ctrl in ref.columns, (r["run"], ctrl)
    diff = {row for row in ROWS if row != "ignore" and _resolved(_back, r["run"], row) != _resolved(ref, ctrl, row)}
    assert diff == {"incentives_suffix"}, (r["run"], ctrl, diff)
print("QA-R6 PASSED: resolved-switch parity — fbC = the batch-6 fbC pattern except the world rows; fbB = the map "
      "anchor's own column except mandate/incentives/phaseout-exempt; R6b: every S pair differs from its control "
      "only in the incentives file")
"""))
cells.append(code("""\
# QA-R7 -- (b) cases.csv Choices validation (ReEDS's unanchored re.match semantics), the rd_*
# ForeignScen token present, every incentives suffix on the obbba_ prefix; (c) frozen artifacts
# byte-identical (incl. futurefiles.csv, cases.csv, the reused rd_ and ma_ world files).
import re as _re
cases_master = pd.read_csv(REPO_ROOT / "cases.csv", index_col=0)
assert r"rd_(eia|aj|iaea|mck|cop28|eo)_d\\d+" in (REPO_ROOT / "cases.csv").read_text(encoding="utf-8")
assert all(s.startswith("obbba_rd_") for s in INC_SUFFIX.values())
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
print("QA-R7c PASSED: all snapshotted frozen artifacts byte-identical (futurefiles.csv, cases.csv, reused world files untouched)")
"""))
cells.append(code("""\
# QA-R8' -- draw membership per block, re-asserted on the emitted casefile; QA-R9 -- fbC
# plantchar identity: S/K world files == the anchor's smr100 file for y >= ANCHOR; R1 fresh
# world files == the npz cost path (2031-2050, native 2022 $/kW).
_yi = {int(y): i for i, y in enumerate(_npz_rd["years"])}
for _, r in m50[m50["block"].isin(["S", "K"])].drop_duplicates("world_case").iterrows():
    src = f"smr100_{r['world']}"
    for tech in ("smr", "large"):
        a = pd.read_csv(PLANTCHAR_DIR_ / f"{plantchar_name(tech, r['world_case'])}.csv").set_index("t")["capcost"]
        b = pd.read_csv(PLANTCHAR_DIR_ / f"{plantchar_name(tech, src)}.csv").set_index("t")["capcost"]
        assert (a.loc[a.index >= ANCHOR] == b.loc[b.index >= ANCHOR]).all(), (r["world_case"], tech)
for _, r in m50[m50["block"] == "R1"].drop_duplicates("world_case").iterrows():
    occ = _npz_rd[f"occ_{SCEN_TOKEN[STEM2SCHED[r['ab']]]}_smr"][int(r["draw_index"])]
    a = pd.read_csv(PLANTCHAR_DIR_ / f"{plantchar_name('smr', r['world_case'])}.csv").set_index("t")["capcost"]
    for t in range(2031, 2051):
        assert abs(float(a.loc[t]) - float(occ[_yi[t]])) <= 0.06 + 1e-4 * float(occ[_yi[t]]), (r["world_case"], t)
print("QA-R8'/R9 PASSED: S/K worlds carry the anchor's drawn cost path; R1 worlds carry their npz cost path; "
      "draw membership per block as registered")
"""))
cells.append(code("""\
# QA-R10 -- no draw collision across blocks and with every used world; QA-R11 -- fbB pointer
# files exist and equal the ma_ column's pointers byte-for-byte; the reused rd_ worlds' files exist.
assert not (_sk & _r1) and not (_r1 & _r2) and not (_sk & _r2)
for _, r in m50[m50["convention"] == "fbB"].iterrows():
    for row in _POINTERS:
        assert _back.loc[row, r["run"]] == cases_rd2.loc[row, r["case"]], (r["run"], row)
    for p in [PLANTCHAR_DIR_ / f"{_back.loc['plantchar_nuclear_smr', r['run']]}.csv",
              PLANTCHAR_DIR_ / f"{_back.loc['plantchar_nuclear', r['run']]}.csv",
              FIN_DIR_ / f"financials_tech_{_back.loc['financials_tech_suffix', r['run']]}.csv",
              FIN_DIR_ / f"construction_times_{_back.loc['construction_times_suffix', r['run']]}.csv"]:
        assert p.exists(), (r["run"], p.name)
for c in REUSED_RD:
    for p in world_files(c, True):
        assert p.exists(), p
print("QA-R10 PASSED: no draw collision; QA-R11 PASSED: every fbB column points at the map anchor's existing "
      "files; the reused rd_ worlds' files are present")
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
    "notebook": "batch2_case_export.ipynb",
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "fork_git_head": _git, "master_seed": MASTER_SEED,
    "built_by": "_build_batch2_case_export.py (ported cells verbatim from smr100_case_export.ipynb)",
    "design": {"batch": f"batch 2 (methods.md v2.5, 2026-09-10): {N_COLS} columns = "
                        + ", ".join(f"{k} {v}" for k, v in m50["block"].value_counts().to_dict().items()),
               "spec_source": "z-ethan/rate_design2/exports/m50, m51, m52 (byte-identity guarded)",
               "conventions": {"fbB": "mandate OFF, learning OFF, the map anchor's own files, per-run incentives, phaseout exempt 1",
                               "fbC": "mandate OFF, learning ON with drawn parameters, rd_ world files + foreign file, phaseout exempt 1"},
               "windows": {"S": 2038, "R": 2035},
               "incentives_convention": "headline rate in the file, x0.9 monetized in-model; minus-probe row template",
               "copula_set": COPULA_SET, "n_draws": N_DRAWS},
    "runs": {r["run"]: {"block": r["block"], "convention": r["convention"], "schedule": r["ab"], "world": r["world"],
                        "draw_index": int(r["draw_index"]), "form": r["form"], "window": int(r["window"]),
                        "gate": r["gate"], "prediction": r["prediction"]} for _, r in m50.iterrows()},
    "reeds_files": {"cases_file": B2_CASES_PATH.name, "plantchar": sorted(written_plantchar),
                    "financials_tech": [f"financials_tech_mc_{c}.csv" for c in ALL_CASES],
                    "construction_times": [f"construction_times_mc_{c}.csv" for c in ALL_CASES],
                    "foreign_experience": [f"foreign_experience_{c}.csv" for c in CASES_RD_NEW],
                    "incentives": [f"incentives_{s}.csv" for s in INC_SUFFIX.values()]},
    "exports": {p.name: _sha(p)[:16] for p in sorted(EXPORTS.glob("*.csv"))},
}
with open(EXPORTS / "batch2_metadata.json", "w") as f:
    json.dump(meta, f, indent=2)
print(json.dumps({k: meta[k] for k in ("notebook", "generated_utc", "fork_git_head")}, indent=2))
"""))

cells.append(md("""\
## Closing note

**One case file, 89 launchable runs**: `cases_nuclearlearning_batch2.csv` (launch:
`python runreeds.py -b <batch> -c nuclearlearning_batch2`). Column order: the 36 statute
runs (by world: `_f50`, `_g50`), the 15 controls, the 20 B2-1 runs, the 12 B2-2 runs. All
runs are standard-horizon.

New input files shipped with the batch: 50 plantchar, 25 financials_tech, 25
construction_times, 25 foreign_experience, 83 incentives; the R2 runs reuse the map anchors'
existing files and three statute worlds reuse batch-6 `rd_` files. Nothing frozen was touched
(QA-R7c). The gates (GS1–GS3, GC-lrn2, GD1, GC2, GW1b) are adjudicated when the batch
returns — nothing is drafted before then.
"""))

nb = {"cells": cells, "metadata": SRC["metadata"], "nbformat": SRC["nbformat"], "nbformat_minor": SRC["nbformat_minor"]}
OUT_PATH.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print(f"wrote {OUT_PATH.name}: {len(cells)} cells ({sum(c['cell_type'] == 'code' for c in cells)} code)")
