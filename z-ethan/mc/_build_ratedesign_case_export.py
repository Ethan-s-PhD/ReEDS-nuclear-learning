"""Compose ratedesign_case_export.ipynb — run infrastructure for the rate_design batch
(v2.2, 2026-09-04: 66 launchable runs = 48 ITC-arm + 12 p25/p75 anchors + 6 horizon).

The batch itself is pre-registered: `z-ethan/rate_design/exports/u80_batch_spec.csv`
(54 rows: 27 envelope + 7 boundary + 14 hybrid + 6 horizon; no reserve) and
`u81_run_schedules.csv` (the 48 offered credit paths). The 12 anchor-densification runs are
registered in `rate_design/methods.md` v2.2 and SELECTED HERE by the frozen smr100 rule
(argsort of the program-NPV score at q = 0.25 / 0.75) — the only decision this notebook
makes, and it is a registered rule, not a choice. Everything else is a pure TRANSCRIPTION
of u80/u81 into ReEDS inputs. It emits:

  * per-world input files for the new Monte-Carlo worlds (plantchar x2, financials_tech,
    construction_times; foreign_experience for the ITC-arm worlds only) — the smr100
    case-export machinery, ported verbatim at build time with content asserts (the step4
    pattern);
  * per-run incentives files (ITC-arm runs) on the itcfb minus-probe row template;
  * `u82_anchor_spec.csv` + `exports/smr100/selected_draws_p25p75.csv` (the anchor
    registration; the frozen `selected_draws.csv` is never rewritten);
  * cases_nuclearlearning_ratedesign.csv — 66 columns, ordered envelope → boundary →
    hybrid → anchor → HORIZON BLOCK LAST (Ethan 09-02: standard-horizon results return
    first if the 2055 extension path fails);
  * the 2055 horizon plumbing: extended mandate trajectories ({token}_smr_ext, flat at the
    2050 level — the registered design) and futurefiles.csv ignore-rows so forecast.py's
    missing-file check passes;
  * a QA suite asserting the transcription against u80/u81 and the frozen registrations.

Build with:   python _build_ratedesign_case_export.py    (json-only; any python)
Execute with: the playground-env kernel (JUPYTER_PATH recipe), end to end.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = json.loads((HERE / "smr100_case_export.ipynb").read_text(encoding="utf-8"))
OUT_PATH = HERE / "ratedesign_case_export.ipynb"


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
# rate_design batch: run infrastructure for the 66 launchable runs (v2.2)

**What this notebook does.** The rate_design batch is pre-registered
(`z-ethan/rate_design/exports/u80_batch_spec.csv`, 54 rows; `u81_run_schedules.csv`, the 48
offered credit paths; gates GE1/GE2/GH1/GH2/GX1/GA1/GA2 in `z-ethan/rate_design/methods.md`
v2.1 + v2.2). This notebook TRANSCRIBES that spec into ReEDS inputs — every emission is
asserted back against u80/u81 — and applies exactly one registered rule of its own: the
selection of the 12 p25/p75 anchor worlds (v2.2) by the frozen smr100 quantile rule.

1. **48 new ITC-arm cost worlds** (27 envelope + 7 boundary-depth + 14 hybrid runs; each
   run has its own world). The MC is re-run with the production generator's own code —
   ported verbatim at build time from `smr100_case_export.ipynb` with content asserts, QA-0
   pinned to `mc_perdraw.npz` — and the u80 draw indices are selected from the materialized
   10,000 draws. Each world gets the standard file set: two plantchar files,
   `financials_tech_mc_*`, `construction_times_mc_*`, and a `foreign_experience_rd_*` file
   at its own drawn `u` (via `_generate_foreign_experience.py --u`, the itcfb precedent).
2. **48 per-run incentives files** on the exact minus-probe row template
   (`build_itcfb_minus.py`): Nuclear-SMR rows only, one per build year, `safe_harbor=0`,
   `itc_tax_equity_penalty=0.1` (ReEDS monetizes at 0.9 internally — the registered
   monetized-parity convention), `itc_frac` = the u81 `rate_on_world` at 3 decimals.
   The hybrid runs' post-window cap (0.60, or 0.50 for the `cb50` probes) is already baked
   into u81's offers.
3. **12 anchor-densification worlds** (`smr100_{sched}_p25` / `_p75`, v2.2): selected here
   by the frozen smr100 rule `argsort(score)[ceil(q·(N−1))]` at q = 0.25 / 0.75 on the
   program-NPV ranking, asserted distinct from the 18 frozen anchors and from every ITC-arm
   world, registered in `u82_anchor_spec.csv` and `exports/smr100/selected_draws_p25p75.csv`
   (the frozen `selected_draws.csv` is never rewritten). Their columns are the smr100 anchor
   pattern verbatim (mandate ON, learning OFF, no-nuclear-ITC baseline, endyear 2050) with
   their own plantchar/financials/construction-time files; no foreign-experience file
   (learning OFF) and no incentives file (baseline).
4. **`cases_nuclearlearning_ratedesign.csv`** — 66 columns on the itcfbm 31-row template,
   ordered envelope → boundary → hybrid → anchor → **horizon last** (Ethan 09-02: the
   standard-horizon runs return results first if the extension path fails). No reserve
   (v2.2: the constraint is one batch, so every slot is live).
5. **Horizon plumbing (endyear 2055).** The 6 horizon runs are reruns of the
   `smr100_{sched}_p50` anchor columns (their worlds ARE the frozen p50 draws — asserted)
   with `endyear=2055`, yearset extended `..._2050_2053_2055`, and the mandate held flat at
   its 2050 level via explicit `nuclear_cap_trajectory_{token}_smr_ext.csv` files (the
   registered design; pre-extended so forecast.py never has to parse the GAMS `*t` header).
   `futurefiles.csv` gets ignore-rows for the nuclear-learning inputs_case files so
   forecast.py's raise-on-missing check passes; everything else is projected by its
   existing rows (`plantcharout.csv` constant = the drawn 2050 cost held flat — "the world
   after 2050 looks like 2050").

**Run-arm convention (logged as a build-time clarification, not a spec change):** the 48
envelope/boundary/hybrid runs use the **fbC convention** — `GSw_NuclearLearning=1` with the
run world's own drawn parameters, no mandate, credit as the only instrument — because the
delivery certificate the batch extends (fbC full-headline delivery + the r03 bracket) was
earned on that arm, and methods.md v2.1 registers "the feed-back tier convention". The 6
horizon runs are mandate-dual reruns (mandate ON, no-nuclear-ITC baseline, learning OFF),
exactly the anchor configuration.

Frozen inputs (byte-identity asserted at the end): u80/u81, the smr100 registrations and
input files, the itcfbm casefile template, `incentives_obbba_nonuclearitc.csv`.
"""))

# ---------------------------------------------------------------- 1: setup (ported, patched)
cells.append(ported(1, "MASTER_SEED = 20260715", patches=[
    ('EXPORTS = NB_DIR / "exports" / "smr100"', 'EXPORTS = NB_DIR / "exports" / "ratedesign"'),
    ('os.environ.get("SMR100_DRAWS", 10000)', 'os.environ.get("RATEDESIGN_DRAWS", 10000)'),
]))

# ---------------------------------------------------------------- 2: frozen-artifact guard
cells.append(code("""\
# --- Frozen-artifact guard: the batch spec and every reused registration must be
# byte-identical after this notebook runs. construction_schedules_mc.csv is in the list
# deliberately: the Export-2 cell re-writes it from the same deterministic code, so
# equality doubles as a determinism check (the step4 pattern).
import hashlib

def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

RD_EXPORTS = REPO_ROOT / "z-ethan" / "rate_design" / "exports"
GUARDED_FILES = [
    RD_EXPORTS / "u80_batch_spec.csv",
    RD_EXPORTS / "u81_run_schedules.csv",
    RD_EXPORTS / "u80_batch_spec_v21.csv",        # the v2.1 audit record (frozen 09-04)
    RD_EXPORTS / "u81_run_schedules_v21.csv",
    NB_DIR / "exports" / "smr100" / "selected_draws.csv",
    REPO_ROOT / "cases_nuclearlearning_smr100.csv",
    REPO_ROOT / "cases_nuclearlearning_itcfbm.csv",
    REPO_ROOT / "inputs" / "financials" / "incentives_obbba_nonuclearitc.csv",
    REPO_ROOT / "inputs" / "financials" / "construction_schedules_mc.csv",
    REPO_ROOT / "inputs" / "plant_characteristics" / "nuclear_mc_smr100_eo_p50.csv",
]
GUARD_SHA = {p: _sha(p) for p in GUARDED_FILES}
print(f"snapshotted {len(GUARD_SHA)} frozen artifacts (verified unchanged in QA-R7)")
"""))

# ---------------------------------------------------------------- foundations (ported)
cells.append(md("""\
## Ported foundations

Verbatim from `smr100_case_export.ipynb` (itself porting `mc_cost_trajectories.ipynb`
S2–S7): schedules, PRIS experience stocks, the OCC engine, the INL duration model, the
ReEDS financing replication, the copula draw, and the program-NPV ranking. Same worlds,
same seed streams; QA-0 below pins them to `mc_perdraw.npz`.
"""))
cells.append(ported(3, "US_GW_2024 = 97.0"))
cells.append(ported(4, "def occ_paths_ces"))
cells.append(ported(5, "def load_reeds_financials"))
cells.append(ported(7, "def draw_world"))
cells.append(ported(9, "def om_npv_per_kw"))
cells.append(ported(10, "def rank_smr"))
cells.append(code("""\
# Program-NPV score vectors (labels the selected worlds' pctile_in_MC; the selection
# itself comes from u80, never from these scores).
mc_score = {s: rank_smr(s) for s in SCHED_ORDER}
print("program-NPV scores computed for all six schedules")
"""))
# ported percentile-selection cell: re-derives the smr100 registration (written under
# exports/ratedesign) and defines _npz_sel_path + the per-selection npz identity gate
cells.append(ported(17, "PCT_TAGS = {"))
cells.append(code("""\
# Continuity pin: the re-derived smr100 selection == the frozen Step-1 registration
# (the horizon runs rerun exactly those p50 cases, so this pin licenses the reuse).
_frozen_sel_full = pd.read_csv(NB_DIR / "exports" / "smr100" / "selected_draws.csv",
                               index_col=["schedule", "percentile"])
assert (_frozen_sel_full["draw_index"] == sel_df["draw_index"]).all(), "selection diverged"
print("continuity pin PASSED: smr100 selections identical to the frozen registration")
"""))

# ---------------------------------------------------------------- batch spec load
cells.append(md("""\
## The frozen batch spec

`u80_batch_spec.csv` is the single source of truth for the ITC-arm and horizon run names,
blocks, schedules, and draw indices (v2.2: 54 rows, no reserve). The horizon rows must sit
on the frozen smr100 p50 draws — asserted against `exports/smr100/selected_draws.csv` — and
the live runs must have distinct worlds within each schedule. The counts below are DERIVED
from u80, never hard-coded, and echoed against the v2.2 registration (48 / 6).
"""))
cells.append(code("""\
u80 = pd.read_csv(RD_EXPORTS / "u80_batch_spec.csv")
u81 = pd.read_csv(RD_EXPORTS / "u81_run_schedules.csv")
assert (u80["block"] == "reserve").sum() == 0, "v2.2 retired the reserve"

STEM2SCHED = {SHORT[SCEN_TOKEN[s]]: s for s in SCHED_ORDER}   # 'aj' -> 'Abou-Jaoude mod'
LIVE_BLOCKS = ["envelope", "boundary", "hybrid"]
live = u80[u80["block"].isin(LIVE_BLOCKS)].reset_index(drop=True)
horiz = u80[u80["block"] == "horizon"].reset_index(drop=True)
N_LIVE, N_HZ = len(live), len(horiz)
assert (N_LIVE, N_HZ) == (48, 6), (N_LIVE, N_HZ)          # methods.md v2.2 registration
assert len(u80) == N_LIVE + N_HZ
assert (live["max_rate_on_world"] < 1.0).all()
assert (live["max_rate_on_world"] <= 0.95).all()          # the registered rate screen
# u80's own row order is envelope -> boundary -> hybrid -> horizon; the casefile keeps it
# (anchor block inserted before horizon; horizon last by construction). Assert:
blocks_seq = list(u80["block"])
_order = ["envelope", "boundary", "hybrid", "horizon"]
assert blocks_seq == sorted(blocks_seq, key=_order.index), "u80 block order changed"
BLOCK_N = {b: int((u80["block"] == b).sum()) for b in _order}

# one distinct world per live run within a schedule; case token rd_{stem}_d{draw}
live_worlds = list(zip(live["schedule"], live["draw_index"].astype(int)))
assert len(set(live_worlds)) == N_LIVE, "live worlds are not all distinct"
live = live.assign(case=[f"rd_{ab}_d{w}" for ab, w in live_worlds])

# horizon rows sit on the frozen p50 draws
_frozen_sel = pd.read_csv(NB_DIR / "exports" / "smr100" / "selected_draws.csv")
_p50 = {r["schedule"]: int(r["draw_index"])
        for _, r in _frozen_sel[_frozen_sel["percentile"] == "p50"].iterrows()}
for _, r in horiz.iterrows():
    assert int(r["draw_index"]) == _p50[STEM2SCHED[r["schedule"]]], r["run"]

# u81 covers exactly the live runs, and every offered rate is < 1
assert set(u81["run"]) == set(live["run"])
assert (u81["rate_on_world"] < 1.0).all() and (u81["rate_on_world"] > 0).all()
print(f"batch spec loaded: {N_LIVE} live runs ({N_LIVE} distinct worlds; blocks {BLOCK_N}), "
      f"{N_HZ} horizon reruns on the frozen p50 draws, no reserve (v2.2)")
"""))

# ---------------------------------------------------------------- anchor densification (v2.2)
cells.append(md("""\
## Anchor densification (v2.2): the p25/p75 mandate-arm worlds

Registered in `rate_design/methods.md` v2.2 (2026-09-04, before any run). Selection = the
frozen smr100 rule at two new quantiles: `idx = argsort(program-NPV score, stable)[ceil(q ·
(N − 1))]`, q = 0.25 / 0.75 — the same `rank_smr` ranking and the same index arithmetic
that placed p05/p50/p95 (continuity-pinned above). The frozen `selected_draws.csv` is never
rewritten; the new picks go to `u82_anchor_spec.csv` (rate_design exports) and
`exports/smr100/selected_draws_p25p75.csv`. Asserted distinct from the 18 frozen anchors
and from every ITC-arm world. Gates GA1/GA2 (methods.md v2.2) are adjudicated post-return.
"""))
cells.append(code("""\
ANCHOR_Q = {"p25": 0.25, "p75": 0.75}
_frozen18 = {(r["schedule"], int(r["draw_index"])) for _, r in _frozen_sel.iterrows()}
_live_set = {(STEM2SCHED[ab], int(w)) for ab, w in live_worlds}
anchor_rows, anchor_reg = [], []
for sched in SCHED_ORDER:
    order = np.argsort(mc_score[sched], kind="stable")
    stem = SHORT[SCEN_TOKEN[sched]]
    for tag, q in ANCHOR_Q.items():
        idx = int(order[int(np.ceil(q * (N_DRAWS - 1)))])
        assert (sched, idx) not in _frozen18, (sched, tag, idx, "collides with a frozen anchor")
        assert (sched, idx) not in _live_set, (sched, tag, idx, "collides with an ITC-arm world")
        score = float(mc_score[sched][idx])
        pct = round(100 * float((mc_score[sched] < score).mean()), 3)
        params = {c: float(WORLDS[sched].iloc[idx][c]) for c in WORLDS[sched].columns}
        anchor_rows.append({"run": f"smr100_{stem}_{tag}", "block": "anchor",
                            "schedule": stem, "percentile": tag, "q": q, "draw_index": idx,
                            "score": score, "pctile_in_MC": pct,
                            "expected": "diagnostic", "gate": "GA1/GA2", **params})
        anchor_reg.append({"schedule": sched, "percentile": tag, "draw_index": idx,
                           "score": score, "pctile_in_MC": pct, **params})
u82 = pd.DataFrame(anchor_rows)
N_ANCHOR = len(u82)
assert N_ANCHOR == 12 and u82["run"].is_unique
assert (abs(u82["pctile_in_MC"] - 100 * u82["q"]) <= 0.5).all(), "quantile placement drifted"
u82.to_csv(RD_EXPORTS / "u82_anchor_spec.csv", index=False)
pd.DataFrame(anchor_reg).set_index(["schedule", "percentile"]).to_csv(
    NB_DIR / "exports" / "smr100" / "selected_draws_p25p75.csv")
print(f"anchor densification: {N_ANCHOR} p25/p75 worlds selected by the frozen rule "
      f"(distinct from the 18 frozen anchors and the {N_LIVE} ITC-arm worlds)")
print(u82[["run", "schedule", "percentile", "draw_index", "pctile_in_MC"]].to_string(index=False))
"""))

# ---------------------------------------------------------------- case records
cells.append(ported(22, "def build_case_rec"))
cells.append(code("""\
# --- The ITC-arm world records, selected from the materialized draws by u80 index ---
CASES_RD, RUN2CASE = {}, {}
for _, r in live.iterrows():
    ab, idx, case = r["schedule"], int(r["draw_index"]), r["case"]
    RUN2CASE[r["run"]] = case
    if case in CASES_RD:
        continue
    sched = STEM2SCHED[ab]
    w1 = WORLDS[sched].iloc[[idx]].reset_index(drop=True)
    CASES_RD[case] = build_case_rec(case, sched, "rd", w1,
                                    float(mc_score[sched][idx]), {"draw_index": idx},
                                    program="smr", score_dist=mc_score[sched])
assert len(CASES_RD) == N_LIVE

# --- The anchor world records (v2.2): built exactly as the smr100 p05/p50/p95 cases were
# (tag = percentile label, default program/score_dist), so their files are the smr100
# pattern with a new percentile label ---
CASES_ANCHOR = {}
for _, r in u82.iterrows():
    sched, idx, case = STEM2SCHED[r["schedule"]], int(r["draw_index"]), r["run"]
    w1 = WORLDS[sched].iloc[[idx]].reset_index(drop=True)
    CASES_ANCHOR[case] = build_case_rec(case, sched, r["percentile"], w1,
                                        float(mc_score[sched][idx]), {"draw_index": idx})
assert len(CASES_ANCHOR) == N_ANCHOR
assert not (set(CASES_ANCHOR) & set(CASES_RD))

# registration export: one row per world, all draw parameters + placement
sel_rows = []
for case, rec in {**CASES_RD, **CASES_ANCHOR}.items():
    sched, idx = rec["schedule"], rec["draw_index"]
    sel_rows.append({"case": case, "schedule": sched, "draw_index": idx,
                     "score": rec["score"],
                     "pctile_in_MC": round(100 * float(
                         (mc_score[sched] < rec["score"]).mean()), 2),
                     **{c: float(WORLDS[sched].iloc[idx][c])
                        for c in WORLDS[sched].columns}})
sel_df_rd = pd.DataFrame(sel_rows).set_index("case")
sel_df_rd.to_csv(EXPORTS / "selected_draws_ratedesign.csv")

# draw-identity assert vs mc_perdraw.npz for every selected world (ITC-arm + anchors)
ALL_CASES = {**CASES_RD, **CASES_ANCHOR}   # the ported Export 1/2 cells iterate ALL_CASES
if _npz_sel_path.exists():
    _npz_rd = np.load(_npz_sel_path, allow_pickle=False)
    _rd_cols = list(_npz_rd["world_columns"].astype(str))
    _rd_checked = 0
    for case, rec in ALL_CASES.items():
        tok = SCEN_TOKEN[rec["schedule"]]
        if _npz_rd[f"worlds_{tok}"].shape[0] != N_DRAWS:
            break
        assert _rd_cols == list(WORLDS[rec["schedule"]].columns)
        assert np.allclose(_npz_rd[f"worlds_{tok}"][rec["draw_index"]],
                           WORLDS[rec["schedule"]].iloc[rec["draw_index"]]
                           .to_numpy(dtype=float), rtol=1e-9, atol=0), case
        _rd_checked += 1
    if _rd_checked:
        print(f"draw identity vs mc_perdraw.npz: {_rd_checked}/{len(ALL_CASES)} worlds match")

print(f"built {len(CASES_RD)} ITC-arm + {len(CASES_ANCHOR)} anchor world records; "
      "input files follow")
"""))

# ---------------------------------------------------------------- exports (ported writers)
cells.append(md("""\
## Exports to ReEDS: per-world input files

The Export 1/2 cells are ported verbatim; with `ALL_CASES` bound to the 48 ITC-arm +
12 anchor worlds they write 120 plantchar files, 60 `financials_tech_mc_*`, 60
`construction_times_mc_*` (`rd_*` for the ITC-arm worlds, `smr100_*_p25/_p75` for the
anchors), the idempotent `dollaryear.csv` registration, and re-write the shared
`construction_schedules_mc.csv` byte-identically (guard-verified in QA-R7).
"""))
cells.append(ported(29, "Export 1: plant-characteristics"))
cells.append(ported(31, "Export 2: shared construction-schedules"))

# ---------------------------------------------------------------- foreign experience
cells.append(code("""\
# --- Export 2b: per-world foreign-experience files at each world's own drawn u ---
# The generator's documented arbitrary-u mode (itcfb spec section 5); exact mode via the
# PRIS loader. Skips a file whose tag already exists with the same u (recorded in-file as
# a comment by the generator? no — recorded here in the registration export instead).
import subprocess, sys

_gen = REPO_ROOT / "inputs" / "nuclear_learning" / "_generate_foreign_experience.py"
_rds2 = REPO_ROOT / "z-ethan" / "mc" / "rds2_2025_units.csv"
assert _gen.exists() and _rds2.exists()

FOREIGN_TAG = {case: case for case in CASES_RD}      # foreign_experience_rd_{ab}_d{idx}.csv
for case, rec in CASES_RD.items():
    u_val = float(WORLDS[rec["schedule"]].iloc[rec["draw_index"]]["u"])
    out_f = REPO_ROOT / "inputs" / "nuclear_learning" / f"foreign_experience_{case}.csv"
    res = subprocess.run(
        [sys.executable, str(_gen), "--u", f"{u_val:.6f}", "--tag", case,
         "--rds2", str(_rds2)],
        capture_output=True, text=True, cwd=str(REPO_ROOT))
    assert res.returncode == 0, (case, res.stdout[-2000:], res.stderr[-2000:])
    assert out_f.exists(), case
    fx = pd.read_csv(out_f)
    assert list(fx.columns)[0] == "t" and fx["t"].max() == 2050
    assert fx["foreign_units_cum"].is_monotonic_increasing
print(f"wrote {len(CASES_RD)} foreign_experience_rd_* files (exact mode, per-world u)")
"""))

# ---------------------------------------------------------------- incentives
cells.append(md("""\
## Per-run incentives files

Exact minus-probe template (`build_itcfb_minus.py`): the `obbba_nonuclearitc` baseline with
its 8 zeroed `NUCLEAR` rows removed and one `Nuclear-SMR` row appended per build year —
`safe_harbor=0`, `t_max_online=t`, penalty 0.1, no bonuses, `itc_frac` = the u81
`rate_on_world` at 3 decimals. The file stores the headline rate; ReEDS monetizes at
×0.9 internally (`financials.py`). The hybrid runs' post-window cap (0.60; 0.50 for the
v2.2 `cb50` probes) is already baked into u81's offers, so no run needs special-casing
here. Anchor runs carry no incentives file (the no-nuclear-ITC baseline).
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
for run, grp in u81.groupby("run", sort=False):
    grp = grp.sort_values("year")
    fed = dict(zip(grp["year"].astype(int), grp["rate_on_world"].astype(float)))
    assert 0.0 < min(fed.values()) and max(fed.values()) < 1.0, run
    rows = [itc_row("Nuclear-SMR", t, round(f, 3)) for t, f in fed.items()]
    suffix = f"obbba_rd_{run}"
    INC_SUFFIX[run] = suffix
    (FIN_DIR_ / f"incentives_{suffix}.csv").write_text(
        "\\n".join(kept + rows) + "\\n", encoding="utf-8")
assert len(INC_SUFFIX) == N_LIVE
print(f"wrote {len(INC_SUFFIX)} incentives files "
      f"(headline-rate convention, x0.9 monetized in-model)")
"""))

# ---------------------------------------------------------------- horizon plumbing
cells.append(md("""\
## Horizon plumbing: 2055 extension

Registered configuration (methods.md v2.1): end year extended to 2055, mandate held flat
at its 2050 level, monetized-parity convention as in the feed-back runs. Implementation:

* **Extended mandate trajectories** `nuclear_cap_trajectory_{token}_smr_ext.csv` — the
  standard file's lines verbatim plus rows 2051–2055 repeating the 2050 MW value. Explicit
  files rather than a forecast.py fit: flat-at-2050 IS the registered design, and this
  keeps forecast.py away from the GAMS `*t` comment header.
* **futurefiles.csv ignore-rows** for the inputs_case files forecast.py would otherwise
  raise on (its missing-file check is a hard error): the five nuclear-learning files
  (trajectory pre-extended; the others historical/year-invariant — and the learning
  engine already clamps the foreign stock flat past its last year via `np.interp`), plus
  `wst_surface.csv` and the three run-root utility files, all uncovered in the shipped
  file. Idempotent append; the QA-R7 simulation asserts full coverage.
"""))
cells.append(code("""\
_nl_dir = REPO_ROOT / "inputs" / "nuclear_learning"
EXT_TOKEN = {}
for _, r in horiz.iterrows():
    tok = SCEN_TOKEN[STEM2SCHED[r["schedule"]]]
    src = _nl_dir / f"nuclear_cap_trajectory_{tok}_smr.csv"
    dst = _nl_dir / f"nuclear_cap_trajectory_{tok}_smr_ext.csv"
    lines = src.read_text(encoding="utf-8").rstrip("\\n").split("\\n")
    assert lines[0].startswith("*t"), src
    last_y, last_mw = lines[-1].split(",")
    assert int(last_y) == 2050, src
    ext = lines + [f"{y},{last_mw}" for y in range(2051, 2056)]
    dst.write_text("\\n".join(ext) + "\\n", encoding="utf-8")
    EXT_TOKEN[r["run"]] = f"{tok}_smr_ext"
print(f"wrote {len(set(EXT_TOKEN.values()))} extended mandate trajectories "
      f"(2051-2055 flat at the 2050 level)")
"""))
cells.append(code("""\
# --- futurefiles.csv ignore-rows (idempotent) ---
_ff_path = REPO_ROOT / "inputs" / "userinput" / "futurefiles.csv"
_ff_text = _ff_path.read_text(encoding="utf-8")
_NOTE = "rate_design horizon block 2026-09-02: leave alone (pre-extended or year-invariant)"
_NEW_FF = [
    ("nuclear_cap_trajectory.csv", ".csv"),
    ("nuclear_cap_mandate_techs.csv", ".csv"),
    ("foreign_experience.csv", ".csv"),
    ("historical_stock.csv", ".csv"),
    ("inl_duration_curves.csv", ".csv"),
    ("wst_surface.csv", ".csv"),
    ("gamslice.txt", ".txt"),
    ("Project.toml", ".toml"),
    ("runreeds.py", ".py"),
]
_added = []
for name, ftype in _NEW_FF:
    if f"\\n{name}," in _ff_text or _ff_text.startswith(f"{name},"):
        continue
    _ff_text = _ff_text.rstrip("\\n") + \\
        f"\\n{name},{ftype},1,None,9999,None,9999,0,constant,None,None,{_NOTE},\\n"
    _added.append(name)
if _added:
    _ff_path.write_text(_ff_text, encoding="utf-8")
print(f"futurefiles.csv: added {len(_added)} ignore-rows {_added or '(none - already present)'}")
"""))
cells.append(code("""\
# --- cases.csv Choices registration for the rd_* foreign-experience tags (idempotent) ---
# ReEDS validates switch values against cases.csv's Choices column with an unanchored
# re.match (reeds/inputs.py:227-241); GSw_NuclearLearning_ForeignScen enumerates its
# allowed tags, so the itcfb batch registered its fb_*_p50 tags there and this batch
# registers one regex token covering every rd_{sched}_d{draw} tag (any count). Comma-free (the
# cell is unquoted CSV); text-level edit so the rest of cases.csv is untouched.
_cases_path = REPO_ROOT / "cases.csv"
_cases_text = _cases_path.read_text(encoding="utf-8")
_RD_CHOICE = r"rd_(eia|aj|iaea|mck|cop28|eo)_d\\d+"
if _RD_CHOICE not in _cases_text:
    _anchor = "fb_eo_p50,mid,"
    assert _cases_text.count(_anchor) == 1, "cases.csv ForeignScen row drifted"
    _cases_text = _cases_text.replace(_anchor, f"fb_eo_p50; {_RD_CHOICE},mid,")
    _cases_path.write_text(_cases_text, encoding="utf-8")
    print(f"cases.csv: registered Choices token {_RD_CHOICE!r} for "
          "GSw_NuclearLearning_ForeignScen")
else:
    print("cases.csv: rd_* Choices token already registered")
"""))

# ---------------------------------------------------------------- cases matrix
cells.append(md("""\
## Export 3: the cases file

66 columns on the itcfbm 31-row template. Live runs = the fbC pattern with per-world
values: no mandate, per-run incentives, learning ON with the world's own drawn parameters,
per-world file pointers. Anchor runs (v2.2) = the `smr100_{sched}_p50` anchor columns
verbatim (mandate ON, no-nuclear-ITC default, learning OFF, endyear 2050) with their own
four file pointers. Horizon runs = the same anchor columns except `endyear=2055`, the
extended yearset, and the `_ext` mandate token. Column order: live → anchor → horizon.
"""))
cells.append(code("""\
tmpl = pd.read_csv(REPO_ROOT / "cases_nuclearlearning_itcfbm.csv",
                   index_col=0, dtype=str).fillna("")
base_s100 = pd.read_csv(REPO_ROOT / "cases_nuclearlearning_smr100.csv",
                        index_col=0, dtype=str).fillna("")
ROWS = list(tmpl.index)
assert len(ROWS) == 31 and ROWS[0] == "ignore"

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
YEARSET_STD = tmpl.loc["yearset", "Default Value"]
YEARSET_EXT = YEARSET_STD + "_2053_2055"

cols = {}
for _, r in live.iterrows():
    case = RUN2CASE[r["run"]]
    rec = CASES_RD[case]
    w = WORLDS[rec["schedule"]].iloc[rec["draw_index"]]
    c = {row: "" for row in ROWS}
    c["GSw_NuclearCapMandate"] = "0"
    c["incentives_suffix"] = INC_SUFFIX[r["run"]]
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
    cols[r["run"]] = c

# anchor block (v2.2): the smr100 anchor column pattern with the world's own file pointers;
# the mandate token is the schedule's standard {tok}_smr (copied from the p50 column)
for _, r in u82.iterrows():
    stem, case = r["schedule"], r["run"]
    src_case = f"smr100_{stem}_p50"
    c = {row: "" for row in ROWS}
    for row in COPY_ROWS:
        c[row] = base_s100.loc[row, src_case]
    c["plantchar_nuclear"] = plantchar_name("large", case)
    c["plantchar_nuclear_smr"] = plantchar_name("smr", case)
    c["financials_tech_suffix"] = f"mc_{case}"
    c["construction_times_suffix"] = f"mc_{case}"
    c["GSw_TCPhaseout_NuclearExempt"] = "0"     # resolved-switch parity with the anchors
    cols[case] = c

for _, r in horiz.iterrows():
    stem = r["schedule"]
    src_case = f"smr100_{stem}_p50"
    c = {row: "" for row in ROWS}
    for row in COPY_ROWS:
        c[row] = base_s100.loc[row, src_case]
    c["GSw_NuclearCapMandateScen"] = EXT_TOKEN[r["run"]]
    c["endyear"] = "2055"
    c["yearset"] = YEARSET_EXT
    # resolved-switch parity with the anchors (registered 09-02): the itcfbm template's
    # Default Value pins GSw_TCPhaseout_NuclearExempt=1 (the fb runs need it), but the
    # smr100 anchors ran the cases.csv default 0 — pin the horizon cells to 0 explicitly.
    c["GSw_TCPhaseout_NuclearExempt"] = "0"
    cols[r["run"]] = c

N_COLS = N_LIVE + N_ANCHOR + N_HZ
assert len(cols) == N_COLS == 66, (len(cols), N_COLS)
defaults = {row: tmpl.loc[row, "Default Value"] for row in ROWS}
cases_rd = pd.DataFrame({"Default Value": defaults} | cols).reindex(ROWS)
cases_rd.index.name = ""
RD_CASES_PATH = REPO_ROOT / "cases_nuclearlearning_ratedesign.csv"
cases_rd.to_csv(RD_CASES_PATH)
print(f"wrote {RD_CASES_PATH.name}: {cases_rd.shape[0]} switch rows x "
      f"{cases_rd.shape[1] - 1} run columns "
      f"(launch: python runreeds.py -b <batch> -c nuclearlearning_ratedesign)")
"""))

# ---------------------------------------------------------------- QA
cells.append(md("""\
## QA suite

Ported world-identity gate (QA-0) plus the transcription gates: QA-R1 casefile ↔ u80,
QA-R2 incentives ↔ u81 + baseline byte-identity, QA-R3 rate bounds, QA-R4 per-world
switch identity, QA-R5 plantchar ↔ u81 occ round-trip (closes the loop between the
rate_design offline machinery and the emitted run inputs), QA-R6 horizon columns +
extended trajectories + yearset, QA-R7 futurefiles coverage simulation + cases.csv
validation + frozen-artifact byte-identity, QA-R8 (v2.2) anchor columns: resolved-switch
parity with the p50 anchor of the same schedule except the four file pointers, pointer
files present, quantile placement, distinctness.
"""))
cells.append(ported(34, "QA-0"))
cells.append(code("""\
# QA-R1 -- casefile transcription of u80 + u82: names, order, horizon last, N_COLS columns.
_back = pd.read_csv(RD_CASES_PATH, index_col=0, dtype=str).fillna("")
_expected = list(live["run"]) + list(u82["run"]) + list(horiz["run"])
assert list(_back.columns) == ["Default Value"] + _expected
assert [c for c in _back.columns if c.startswith("hz_")] == list(_back.columns[-N_HZ:])
assert list(_back.columns[1 + N_LIVE:1 + N_LIVE + N_ANCHOR]) == list(u82["run"])
assert list(_back.index) == ROWS
assert not any(c.startswith("reserve") for c in _back.columns)   # v2.2: no reserve
print(f"QA-R1 PASSED: {N_COLS} columns in u80/u82 order (envelope, boundary, hybrid, "
      f"anchor, horizon LAST); {len(ROWS)} template rows; no reserve")
"""))
cells.append(code("""\
# QA-R2 -- incentives echo vs u81 + baseline byte-identity.
for run in list(live["run"]):
    txt = (FIN_DIR_ / f"incentives_{INC_SUFFIX[run]}.csv").read_text(encoding="utf-8")
    lines = [ln for ln in txt.splitlines() if ln.strip()]
    body = [ln for ln in lines if not ln.startswith("Nuclear-SMR,")]
    assert body == kept, run                      # non-nuclear rows byte-identical
    nuc = [ln.split(",") for ln in lines if ln.startswith("Nuclear-SMR,")]
    got = {int(p[2]): float(p[9]) for p in nuc}
    grp = u81[u81["run"] == run]
    want = {int(t): round(float(x), 3)
            for t, x in zip(grp["year"], grp["rate_on_world"])}
    assert got == want, (run, got, want)
    for p in nuc:                                  # row shape: the minus-probe template
        assert p[3] == "0" and p[4] == p[2] and p[12] == "0.1", run
        assert p[10] == "0.0" and p[11] == "0.0", run
print(f"QA-R2 PASSED: {N_LIVE} incentives files echo u81 exactly (rate years, 3-dp headline "
      "rates, safe_harbor 0, penalty 0.1, no bonuses); baselines byte-identical")
"""))
cells.append(code("""\
# QA-R3 -- rate bounds: every fed rate < 1.0; per-run max matches u80's registered max.
for _, r in live.iterrows():
    grp = u81[u81["run"] == r["run"]]
    mx = round(float(grp["rate_on_world"].max()), 3)
    assert mx < 1.0
    assert abs(mx - float(r["max_rate_on_world"])) <= 0.0011, (r["run"], mx)
print("QA-R3 PASSED: all offered rates < 1.0; per-run maxima match u80")
"""))
cells.append(code("""\
# QA-R4 -- per-world switch identity: the casefile's learning switches reproduce the
# drawn world exactly (via LEARN_FMT), and the foreign tag matches the emitted file.
for _, r in live.iterrows():
    rec = CASES_RD[RUN2CASE[r["run"]]]
    w = WORLDS[rec["schedule"]].iloc[rec["draw_index"]]
    for sw, (dcol, fmt) in LEARN_FMT.items():
        assert _back.loc[sw, r["run"]] == fmt(float(w[dcol])), (r["run"], sw)
    tag = _back.loc["GSw_NuclearLearning_ForeignScen", r["run"]]
    assert (REPO_ROOT / "inputs" / "nuclear_learning"
            / f"foreign_experience_{tag}.csv").exists(), r["run"]
    assert _back.loc["GSw_NuclearLearning", r["run"]] == "1"
    assert _back.loc["GSw_NuclearCapMandate", r["run"]] == "0"
print(f"QA-R4 PASSED: all {N_LIVE} live columns carry their world's exact drawn parameters, "
      "fbC learning flags, no mandate, and an existing foreign-experience file")
"""))
cells.append(code("""\
# QA-R5 -- plantchar <-> u81 round-trip: the occ path in the written plantchar file
# (native 2022 $/kW) equals u81's occ_world_kW after the SAME 2022->2024 conversion the
# rate_design builder registers (D2224 = infl_2023 * infl_2024 from deflator.csv), and
# offer/occ reproduces rate_on_world (rates are unitless, so the incentives files are
# dollar-year-invariant). This closes the loop between the rate_design offline machinery
# and the run inputs ReEDS will actually see.
PLANTCHAR_DIR_ = REPO_ROOT / "inputs" / "plant_characteristics"
_infl_rd = pd.read_csv(REPO_ROOT / "inputs" / "financials" / "inflation_default.csv")
_infl_rd = _infl_rd.set_index("t")["inflation_rate"]
D2224 = float(_infl_rd.loc[2023] * _infl_rd.loc[2024])
assert 1.0 < D2224 < 1.2, D2224
for _, r in live.iterrows():
    case = RUN2CASE[r["run"]]
    back = pd.read_csv(PLANTCHAR_DIR_ / f"{plantchar_name('smr', case)}.csv")
    back = back.set_index("t")["capcost"]
    grp = u81[u81["run"] == r["run"]]
    for _, q in grp.iterrows():
        occ_file = float(back.loc[int(q["year"])])            # 2022 $/kW (native)
        occ_2024 = occ_file * D2224
        assert abs(occ_2024 - float(q["occ_world_kW"])) <= 0.06 + 1e-4 * occ_2024, \\
            (r["run"], q["year"], occ_2024, float(q["occ_world_kW"]))
        assert abs(float(q["offer_kW"]) / occ_2024
                   - float(q["rate_on_world"])) <= 5e-4, (r["run"], q["year"])
print(f"QA-R5 PASSED: every run's plantchar occ path x D2224 ({D2224:.4f}) equals u81's "
      "2024$ world path, and offer/occ reproduces the registered rate (<= 5e-4)")
"""))
cells.append(code("""\
# QA-R6 -- horizon columns: RESOLVED-switch-verbatim vs the smr100 p50 anchors except the
# three registered fields; extended trajectories correct; endyear in the extended yearset.
# Resolution follows reeds/inputs.py:169-185: case cell -> casefile Default Value ->
# cases.csv Default Value. (Amended 09-02 after external review: the raw-cell comparison
# was blind to Default-column divergence — GSw_TCPhaseout_NuclearExempt resolved to 1 here
# vs 0 in the anchors; the six horizon cells now pin it to 0 explicitly.)
_cm6 = pd.read_csv(REPO_ROOT / "cases.csv", index_col=0)
_cm6_def = {str(k): ("" if pd.isna(v) else str(v))
            for k, v in _cm6["Default Value"].items()}

def _resolved(df, col, row):
    v = str(df.loc[row, col]) if row in df.index else ""
    if v == "":
        v = str(df.loc[row, "Default Value"]) if row in df.index else ""
    if v == "":
        v = _cm6_def.get(row, "")
    return v

_EXEMPT6 = {"endyear", "yearset", "GSw_NuclearCapMandateScen", "ignore"}
for _, r in horiz.iterrows():
    run, stem = r["run"], r["schedule"]
    src_case = f"smr100_{stem}_p50"
    assert _back.loc["endyear", run] == "2055", run
    assert _back.loc["yearset", run] == YEARSET_EXT, run
    assert _back.loc["GSw_NuclearCapMandateScen", run] == EXT_TOKEN[run] == \\
        base_s100.loc["GSw_NuclearCapMandateScen", src_case] + "_ext", run
    for row in ROWS:
        if row in _EXEMPT6:
            continue
        got = _resolved(_back, run, row)
        want = _resolved(base_s100, src_case, row)
        assert got == want, (run, row, got, want)
    tok = SCEN_TOKEN[STEM2SCHED[stem]]
    std = (_nl_dir / f"nuclear_cap_trajectory_{tok}_smr.csv").read_text(encoding="utf-8")
    ext = (_nl_dir / f"nuclear_cap_trajectory_{tok}_smr_ext.csv").read_text(encoding="utf-8")
    std_l = std.rstrip("\\n").split("\\n")
    ext_l = ext.rstrip("\\n").split("\\n")
    assert ext_l[:len(std_l)] == std_l, tok                 # prefix byte-identical
    mw2050 = std_l[-1].split(",")[1]
    assert ext_l[len(std_l):] == [f"{y},{mw2050}" for y in range(2051, 2056)], tok
ys = [int(t) for t in YEARSET_EXT.split("_")]
assert 2055 in ys and 2053 in ys and ys == sorted(ys)
print("QA-R6 PASSED: horizon columns match the p50 anchors on RESOLVED switch values "
      "except endyear/yearset/mandate-scen; _ext trajectories flat at the 2050 MW value; "
      "endyear 2055 is a yearset member")
"""))
cells.append(code("""\
# QA-R8 (v2.2) -- anchor columns: RESOLVED-switch parity with the smr100 p50 anchor of the
# same schedule except the four per-world file pointers; pointer files exist and carry the
# world's own occ path; quantile placement by the frozen rule; distinct from the frozen 18
# and from every ITC-arm world; no incentives/foreign files (baseline, learning OFF).
_EXEMPT8 = {"plantchar_nuclear", "plantchar_nuclear_smr", "financials_tech_suffix",
            "construction_times_suffix", "ignore"}
_frozen18_r8 = {(r["schedule"], int(r["draw_index"])) for _, r in _frozen_sel.iterrows()}
for _, r in u82.iterrows():
    run, stem = r["run"], r["schedule"]
    src_case = f"smr100_{stem}_p50"
    sched = STEM2SCHED[stem]
    for row in ROWS:
        if row in _EXEMPT8:
            continue
        got, want = _resolved(_back, run, row), _resolved(base_s100, src_case, row)
        assert got == want, (run, row, got, want)
    assert _resolved(_back, run, "GSw_NuclearLearning") == "0", run
    assert _resolved(_back, run, "GSw_NuclearCapMandate") == "1", run
    assert _resolved(_back, run, "endyear") == "2050", run
    assert _back.loc["plantchar_nuclear_smr", run] == plantchar_name("smr", run)
    assert _back.loc["plantchar_nuclear", run] == plantchar_name("large", run)
    for p in [PLANTCHAR_DIR_ / f"{plantchar_name('smr', run)}.csv",
              PLANTCHAR_DIR_ / f"{plantchar_name('large', run)}.csv",
              FIN_DIR_ / f"financials_tech_mc_{run}.csv",
              FIN_DIR_ / f"construction_times_mc_{run}.csv"]:
        assert p.exists(), (run, p.name)
    assert not (FIN_DIR_ / f"incentives_obbba_rd_{run}.csv").exists(), run
    # the written plantchar occ path is the world's own designed path (2022 $/kW, rounded)
    back8 = pd.read_csv(PLANTCHAR_DIR_ / f"{plantchar_name('smr', run)}.csv")
    back8 = back8.set_index("t")["capcost"]
    occ8 = CASES_ANCHOR[run]["occ_smr"]
    for t_i, y in enumerate(YEARS):
        if y >= ANCHOR:
            assert abs(float(back8.loc[y]) - round(float(occ8[t_i]), 1)) < 1e-6, (run, y)
    # quantile placement + distinctness
    idx = int(r["draw_index"])
    order8 = np.argsort(mc_score[sched], kind="stable")
    assert idx == int(order8[int(np.ceil(float(r["q"]) * (N_DRAWS - 1)))]), run
    assert (sched, idx) not in _frozen18_r8, run
    assert (stem, idx) not in set(live_worlds), run
print(f"QA-R8 PASSED: {N_ANCHOR} anchor columns match the p50 anchors on RESOLVED switch "
      "values except the four file pointers; pointer files present with the world's own "
      "occ path; frozen quantile rule reproduced; distinct from the 18 frozen anchors and "
      "all ITC-arm worlds; no incentives file")
"""))
cells.append(code("""\
# QA-R7 -- (a) futurefiles coverage simulation for the horizon configs, (b) cases.csv
# Choices validation of the new casefile, (c) frozen-artifact byte-identity.
import re as _re

# (a) simulate forecast.py's missing-file check: every runfiles.csv file required under
# the horizon switch config must have a futurefiles.csv row (forecast.py raises otherwise).
runfiles = pd.read_csv(REPO_ROOT / "reeds" / "input_processing" / "runfiles.csv",
                       comment="#")
ff_names = set(pd.read_csv(REPO_ROOT / "inputs" / "userinput" / "futurefiles.csv")
               ["filename"])
cases_master = pd.read_csv(REPO_ROOT / "cases.csv", index_col=0)

class _SW:
    def __init__(self, d): self.__dict__.update(d)

for run in [r["run"] for _, r in horiz.iterrows()]:
    swd = {k: str(cases_master.loc[k, "Default Value"])
           for k in cases_master.index if isinstance(k, str)}
    for row in ROWS:
        v = _back.loc[row, run] or _back.loc[row, "Default Value"]
        if v != "":
            swd[row] = str(v)
    sw = _SW(swd)
    missing = []
    for _, rf in runfiles.iterrows():
        name, req = str(rf["filename"]), str(rf["required_if"])
        if "." not in name or "{" in name:
            continue      # brace names are switch-formatted before landing; their
                          # inputs_case names are the runfiles 'filename' column, no braces
        try:
            required = bool(eval(req, {"int": int, "float": float, "str": str},
                                 {"sw": sw}))
        except Exception:
            required = True                      # conservative: assume it lands
        if required and name not in ff_names:
            missing.append(name)
    assert not missing, (run, missing)
print("QA-R7a PASSED: every inputs_case file implied by the horizon configs has a "
      "futurefiles.csv row (forecast.py's raise-on-missing check will pass)")

# (b) the new casefile validates against cases.csv's own index and Choices, replicating
# ReEDS's ACTUAL validation semantics (reeds/inputs.py:227-241): unanchored re.match,
# i.e. prefix matching — the same gate the itcfb/itcfbm suffixes passed through.
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
            int(val)
            continue
        if choices.lower() in ("float", "numeric", "number", "num"):
            float(val)
            continue
        i_choices = [str(j).strip() for j in
                     np.ravel([c.split(",") for c in choices.split(";")]).tolist()]
        assert any(_re.match(ch, str(val)) for ch in i_choices), \\
            (switch, val, choices)
print("QA-R7b PASSED: the casefile passes ReEDS's own Choices validation "
      "(reeds/inputs.py semantics, prefix re.match)")

# (c) frozen artifacts byte-identical (incl. the deterministically re-written
# construction_schedules_mc.csv)
for p, sha0 in GUARD_SHA.items():
    assert _sha(p) == sha0, f"frozen artifact changed: {p}"
print("QA-R7c PASSED: all snapshotted frozen artifacts byte-identical")
"""))

# ---------------------------------------------------------------- metadata
cells.append(md("## Run metadata"))
cells.append(code("""\
import json
import subprocess as _sp
from datetime import datetime, timezone

try:
    _git = _sp.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
                   capture_output=True, text=True).stdout.strip()
except Exception:
    _git = "unavailable"

meta = {
    "notebook": "ratedesign_case_export.ipynb",
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "fork_git_head": _git,
    "master_seed": MASTER_SEED,
    "built_by": "_build_ratedesign_case_export.py (ported cells verbatim from "
                "smr100_case_export.ipynb with build-time content asserts)",
    "design": {
        "batch": f"rate_design v2.2 pre-registered batch (2026-09-04), {N_COLS} launchable "
                 f"columns: {BLOCK_N['envelope']} envelope + {BLOCK_N['boundary']} "
                 f"boundary-depth + {BLOCK_N['hybrid']} hybrid (fbC convention: learning ON "
                 "with the run world's drawn parameters, no mandate, per-run credit; hybrid "
                 f"caps 0.60 and 0.50) + {N_ANCHOR} p25/p75 anchor-densification runs "
                 "(smr100 pattern: mandate ON, learning OFF, no-nuclear-ITC, endyear 2050) "
                 f"+ {N_HZ} horizon reruns of the smr100 p50 anchors (endyear 2055, mandate "
                 "flat at 2050 via _ext trajectories). No reserve (v2.2). "
                 "HORIZON BLOCK LAST (Ethan 09-02); anchor block before it.",
        "spec_source": "z-ethan/rate_design/exports/u80_batch_spec.csv + "
                       "u81_run_schedules.csv (byte-identity guarded) + u82_anchor_spec.csv "
                       "(selected here by the frozen smr100 quantile rule, methods.md v2.2)",
        "anchor_rule": "idx = argsort(rank_smr score, stable)[ceil(q*(N-1))], q = 0.25/0.75; "
                       "frozen selected_draws.csv untouched; registration in "
                       "exports/smr100/selected_draws_p25p75.csv",
        "arm_clarification": "envelope/boundary/hybrid = fbC (learning ON): the delivery "
                             "certificate the batch extends (fbC full-headline delivery + "
                             "the r03 bracket) was earned on that arm; logged in "
                             "rate_design/status.md as a build-time clarification",
        "incentives_convention": "headline rate in the file, x0.9 monetized in-model "
                                 "(the registered monetized-parity convention); "
                                 "minus-probe row template",
        "horizon": {"endyear": 2055, "yearset": "std + _2053_2055",
                    "mandate": "flat at 2050 via nuclear_cap_trajectory_{tok}_smr_ext",
                    "futurefiles": "ignore-rows added for the five nuclear-learning "
                                   "files + wst_surface + run-root utility files"},
        "copula_set": COPULA_SET, "n_draws": N_DRAWS},
    "runs": {r["run"]: {"block": r["block"], "schedule": r["schedule"],
                        "draw_index": int(r["draw_index"]),
                        "gate": r["gate"], "expected": r["expected"]}
             for _, r in pd.concat([u80, u82[["run", "block", "schedule", "draw_index",
                                               "gate", "expected"]]]).iterrows()},
    "reeds_files": {
        "cases_file": RD_CASES_PATH.name,
        "plantchar": sorted(written_plantchar),
        "financials_tech": [f"financials_tech_mc_{c}.csv" for c in ALL_CASES],
        "construction_times": [f"construction_times_mc_{c}.csv" for c in ALL_CASES],
        "foreign_experience": [f"foreign_experience_{c}.csv" for c in CASES_RD],
        "incentives": [f"incentives_{s}.csv" for s in INC_SUFFIX.values()],
        "mandate_trajectories_ext": sorted(set(EXT_TOKEN.values())),
        "construction_schedules": "construction_schedules_mc.csv (unchanged, "
                                  "byte-identity asserted)"},
    "exports": {p.name: _sha(p)[:16] for p in sorted(EXPORTS.glob("*.csv"))},
}
with open(EXPORTS / "ratedesign_metadata.json", "w") as f:
    json.dump(meta, f, indent=2)
print(json.dumps({k: meta[k] for k in ("notebook", "generated_utc", "fork_git_head")},
                 indent=2))
print(f"full metadata: {EXPORTS / 'ratedesign_metadata.json'}")
"""))

# ---------------------------------------------------------------- closing
cells.append(md("""\
## Closing note

**One case file, 66 launchable runs (v2.2)**: `cases_nuclearlearning_ratedesign.csv`
(launch: `python runreeds.py -b <batch> -c nuclearlearning_ratedesign`). Column order:
48 ITC-arm runs (envelope, boundary, hybrid) → 12 p25/p75 anchors → the 6 horizon runs
deliberately LAST — launch in column order and the 60 standard-horizon runs return results
even if the never-before-exercised 2055 extension path fails in input processing. No
reserve (methods.md v2.2: one batch, every slot live).

New input files shipped with the batch: 120 plantchar, 60 financials_tech, 60
construction_times, 48 foreign_experience, 48 incentives, 6 extended mandate trajectories,
plus the (already present) 9 futurefiles.csv ignore-rows; new registrations
`u82_anchor_spec.csv` and `exports/smr100/selected_draws_p25p75.csv`. Nothing frozen was
touched (QA-R7c). Gates GE1/GE2/GH1/GH2/GX1 and GA1/GA2 are adjudicated when the batch
returns — nothing is drafted before then.
"""))

nb = {"cells": cells, "metadata": SRC["metadata"],
      "nbformat": SRC["nbformat"], "nbformat_minor": SRC["nbformat_minor"]}
OUT_PATH.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print(f"wrote {OUT_PATH.name}: {len(cells)} cells "
      f"({sum(c['cell_type'] == 'code' for c in cells)} code)")
