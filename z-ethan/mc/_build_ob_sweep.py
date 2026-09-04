"""Compose ob_sweep.ipynb — the optimism-bias multiplier sweep.

The notebook finds, for each headline claim of paper section S2, the flip boundary:
the SMR-only optimism-bias multiplier m* at which the claim stops holding. The T9
stress in tech_comparison.ipynb fixed one point (m = 1.5) and found it inverts the
recommendation; this notebook sweeps m over 1.00–2.00 at the three stress anchors.

The notebook is built from two kinds of cells:
  * PORTED cells lifted verbatim (or with asserted single-string patches) from
    tech_comparison.ipynb at build time, so the marginals, copula draws, learning
    engine, durations, financing, and cost objects are the production code by
    construction;
  * NEW cells (inline below) for the sweep-specific work: the multiplier grid, the
    common-random-numbers sweep loop, flip-boundary interpolation, the figure, the
    exports, and the QA pin suite.

Rebuild with:  python _build_ob_sweep.py   (any python with json)
Then run the notebook end to end on the playground-env kernel.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = json.loads((HERE / "tech_comparison.ipynb").read_text(encoding="utf-8"))
OUT_PATH = HERE / "ob_sweep.ipynb"


def src_cell(i, must_contain, patches=()):
    """Return tech_comparison cell i's source, asserting identity + applying patches."""
    cell = SRC["cells"][i]
    text = "".join(cell["source"])
    assert must_contain in text, f"cell {i} drifted: {must_contain!r} not found"
    for old, new in patches:
        assert text.count(old) == 1, f"cell {i} patch target not unique: {old!r}"
        text = text.replace(old, new)
    return cell["cell_type"], text


def code(text, cid):
    return {"cell_type": "code", "execution_count": None, "id": cid, "metadata": {},
            "outputs": [], "source": text.splitlines(keepends=True)}


def md(text, cid):
    return {"cell_type": "markdown", "id": cid, "metadata": {},
            "source": text.splitlines(keepends=True)}


def ported(i, must_contain, cid, patches=()):
    kind, text = src_cell(i, must_contain, patches)
    return code(text, cid) if kind == "code" else md(text, cid)


cells = []

# ---------------------------------------------------------------- 0: intro
cells.append(md("""\
# Optimism-bias multiplier sweep — flip boundaries for the S2 headline claims

**What this notebook does.** The T9 stress in `tech_comparison.ipynb` inflates the drawn
2030 SMR anchor cost (the starting cost the learning curve descends from) by a single
optimism-bias multiplier m = 1.5, and that one point does not just break the majority
claim — it inverts the recommendation (P(SMR wins) falls to 0.002–0.21 at κ = 1, from a
0.82–0.89 baseline). This notebook sweeps m over 1.00–2.00 and reports, for each headline
claim of paper section S2, the **flip boundary** m* — the multiplier at which the claim
stops holding:

- **S2-d** (majority): SMR wins the majority of sampled worlds. Fails when the minimum
  over schedules of P(SMR wins) crosses 0.5 — the pre-registered C1 criterion.
- **S2-c claim 1** (EVPI): committing now, without waiting for perfect information,
  forfeits little. EVPI (the expected value of perfect information — the most a planner
  would pay to know the drawn world before committing) is judged against the
  pre-registered C5 "low value" threshold, 1% of expected program cost (2% also reported).
- **S2-c claim 2** (switch bound): one perfect-information technology switch in 2036
  recovers little. Same C5 threshold.
- **S2-b** (fragmentation): a split program dilutes learning. Fails when the median
  penalty of the 50/50 constant split, relative to the best pure program in the same
  drawn world, crosses zero.

**Engine.** Every model component is ported verbatim from `tech_comparison.ipynb` by
`_build_ob_sweep.py` with build-time content asserts — the sweep runs the production
marginals, copula, learning engine, durations, financing, and cost objects by
construction. The multiplier enters at its single production site: `marginal_ppf`'s
`variant="ob"` branch multiplies the drawn SMR anchor (`OB_MULT`), and deliberately does
NOT move the O&M percentile (the T1/T9 convention).

**Common random numbers, and one deliberate stream reuse.** At κ = 1 the worlds come from
the frozen `mc_perdraw.npz` uniforms, so every multiplier reuses the same latent draws and
the sweep is fully deterministic. At κ = 0.5 and κ = 0 the sweep draws with the SAME
stream names tech_comparison used for its ob cells (`tccomp/world/ob@{aid}/{tok}`), held
fixed across all m. Two consequences, both intended: (i) m = 1.5 reproduces the published
`stress_survival.csv` ob rows bit-for-bit, and (ii) every m shares latents, so the curves
in m are smooth and the interpolated boundaries are not draw-noise artifacts. The QA cell
at the end pins both ends of the sweep to the published exports.

**Outputs.** `exports/ob_sweep/{sweep_metrics.csv, flip_boundaries.csv,
ob_sweep_metadata.json}`, the diagnostic `figures/obs_flip_curves.png`, and the paper
Fig 3 panels `figures/{obs_majority_vs_m.png, obs_evpi_vs_m.png}` (baked letters c/d —
the sweep curves replaced the κ-profile insets in the 2026-08-26 Fig 3c/d swap; the
2026-08-31 third recomposition made the majority flip panel c and the EVPI sweep
panel d, and retired the standalone bound sweep `obs_bound_vs_m.png` from the paper).
""", "obs-intro"))

# ------------------------------------------------- ported setup (patched paths)
cells.append(ported(1, "MASTER_SEED = 20260715", "port-t0-setup", patches=[
    ('EXPORTS = NB_DIR / "exports" / "tech_comparison"',
     'EXPORTS = NB_DIR / "exports" / "ob_sweep"'),
    ('os.environ.get("TCCOMP_DRAWS", 10000)',
     'os.environ.get("OBSWEEP_DRAWS", 10000)'),
]))

cells.append(md("""\
## Ported foundations

Verbatim from `tech_comparison.ipynb` (ported at build time by `_build_ob_sweep.py` with
content asserts): the six deployment schedules, historical and international experience,
foreign stocks and gross additions, the learning-curve engine, durations and financing,
the marginal variants (including the `OB_MULT` optimism-bias site), the latent copula and
cell draws, and the blended program costing with the 49-candidate strategy library.
""", "obs-port-note"))

cells.append(ported(3, "US_SCHEDULES_CSV", "port-schedules"))
cells.append(ported(4, "REGION_MILESTONES", "port-experience"))
cells.append(ported(5, "def gross_additions_gw", "port-stocks"))
cells.append(ported(6, "def occ_paths_ces", "port-engine"))
cells.append(ported(7, "def load_reeds_financials", "port-financing"))
cells.append(ported(9, "def marginal_ppf", "port-marginals"))
cells.append(ported(11, "def draw_cell", "port-copula"))
cells.append(ported(13, "def screen_components", "port-costing"))

# ---------------------------------------------------------------- S1: config
cells.append(md("""\
## S1 — Sweep configuration

The multiplier grid is dense (step 0.05) over 1.00–1.50, where the published endpoints
say every boundary of interest must lie for the κ = 1 claims, and coarse (step 0.10)
over 1.50–2.00 to close out the fragmentation question. The three dependence anchors are
the T9 stress cells. The continuation library for the 2036 switch bound and the EVPI
strategy library are identical to tech_comparison T7/T8.
""", "obs-s1-md"))

cells.append(code("""\
# S1 - grid, anchors, continuation library, thresholds.
M_GRID = np.array([1.00, 1.05, 1.10, 1.15, 1.20, 1.25, 1.30, 1.35, 1.40, 1.45, 1.50,
                   1.60, 1.70, 1.80, 1.90, 2.00])
AIDS = {"k100": 1.0, "k050": 0.5, "k000": 0.0}     # the three T9 stress anchors

SWITCH_TAUS = [y for y in BUILD_YEARS if 2036 <= y <= 2045]
CONT_L = [I_PL] + [CAND_NAMES.index(f"large_then_smr_{y}") for y in SWITCH_TAUS]
CONT_S = [I_PS] + [CAND_NAMES.index(f"smr_then_large_{y}") for y in SWITCH_TAUS]
I_C5 = CAND_NAMES.index("const_0.5")

EVPI_THRESHOLDS = [C5_THRESH_PCT, 2.0]             # 1% pre-registered; 2% companion readout

def binom_ci(p, n, z=1.96):
    se = np.sqrt(max(p*(1-p), 1e-12)/n)
    return max(0.0, p - z*se), min(1.0, p + z*se)

print(f"sweep: {len(M_GRID)} multipliers x {len(AIDS)} anchors x {len(SCHED_ORDER)} "
      f"schedules, N = {N_DRAWS_TC}/point/schedule, library = {len(CAND_NAMES)} candidates")
""", "obs-s1-config"))

# ---------------------------------------------------------------- S2: the sweep
cells.append(md("""\
## S2 — The sweep

Per (anchor, multiplier, schedule): rebind `OB_MULT`, draw (or reconstruct) the worlds,
and reduce immediately to the claim metrics — the (49, n) candidate matrices are dropped
before the next point, so memory stays flat. The pure-program contest is computed in
float64 exactly as tech_comparison T4 (the library matrices are float32 there too), so
the QA pins compare like for like.
""", "obs-s2-md"))

cells.append(code("""\
# S2 - the sweep loop (reduce-and-discard; heavy cell, ~40 min at 10k draws).
rows = []
_OB_BASE = OB_MULT                       # the ported T9 constant (1.5); restored below
t_all = time.time()
for aid, kap in AIDS.items():
    for m in M_GRID:
        OB_MULT = float(m)               # the single production site reads this global
        t0 = time.time()
        for sched in SCHED_ORDER:
            tok = SCEN_TOKEN[sched]
            if kap >= 1.0:               # frozen npz uniforms: deterministic across m
                world = comonotone_cell(sched, "ob",
                                        n=None if N_DRAWS_TC >= N_NPZ else N_DRAWS_TC)
            else:                        # same stream for every m: common random numbers
                world = draw_cell(N_DRAWS_TC, kap, kap, True, True, "ob",
                                  f"tccomp/world/ob@{aid}/{tok}")
            skv = intl_stock(world)
            # pure-program NPV contest, float64, ties -> large (tech_comparison T4)
            cl, ol = program_components(world, sched, P_LARGE, S_KV=skv)
            cs, os_ = program_components(world, sched, P_SMR, S_KV=skv)
            Rl, Rs = cl + ol, cs + os_
            p = float((Rl > Rs).mean())
            lo, hi = binom_ci(p, len(world))
            # the 49-candidate library under the npv object (EVPI / switch bound / split)
            cap, omc = screen_components(world, sched, skv)
            costs = score_matrix(cap, omc, sched=sched)
            e_fixed = costs.mean(axis=1)
            best_e = float(e_fixed.min())
            evpi_pct = 100.0 * (best_e - float(costs.min(axis=0).mean())) / best_e
            v_pi = min(float(costs[CONT_L].min(axis=0).mean()),
                       float(costs[CONT_S].min(axis=0).mean()))
            bound_pct = 100.0 * max(0.0, best_e - v_pi) / best_e
            pen = costs[I_C5] / np.minimum(costs[I_PL], costs[I_PS]) - 1.0
            costs_cap = score_matrix(cap, omc, obj="capex")
            pen_cap = costs_cap[I_C5] / np.minimum(costs_cap[I_PL], costs_cap[I_PS]) - 1.0
            rows.append({
                "m": float(m), "cell": aid, "kappa": kap, "schedule": sched,
                "n": len(world), "acceptance": float(world.attrs.get("acceptance", 1.0)),
                "P_smr": p, "ci_lo": lo, "ci_hi": hi,
                "EVPI_pct": evpi_pct, "bound_pct": bound_pct,
                "emin_strategy": CAND_NAMES[int(e_fixed.argmin())],
                "frag_npv_P10": float(np.percentile(100*pen, 10)),
                "frag_npv_P50": float(np.percentile(100*pen, 50)),
                "frag_npv_P90": float(np.percentile(100*pen, 90)),
                "P_split_wins": float((pen < 0).mean()),
                "frag_cap_P10": float(np.percentile(100*pen_cap, 10)),
                "frag_cap_P50": float(np.percentile(100*pen_cap, 50)),
                "frag_cap_P90": float(np.percentile(100*pen_cap, 90)),
                "P_split_wins_cap": float((pen_cap < 0).mean()),
            })
            del cap, omc, costs, costs_cap, pen, pen_cap, world
        sub = [r for r in rows if r["cell"] == aid and r["m"] == float(m)]
        ps_ = [r["P_smr"] for r in sub]
        print(f"  {aid} m={m:.2f}  P(SMR) {min(ps_):.3f}-{max(ps_):.3f}  "
              f"EVPI max {max(r['EVPI_pct'] for r in sub):.2f}%  "
              f"bound max {max(r['bound_pct'] for r in sub):.2f}%  "
              f"split-median min {min(r['frag_npv_P50'] for r in sub):+.1f}%  "
              f"({time.time()-t0:5.1f}s)")
OB_MULT = _OB_BASE
SWEEP = pd.DataFrame(rows)
print(f"\\nsweep complete: {len(SWEEP)} points in {(time.time()-t_all)/60:.1f} min")
""", "obs-s2-sweep"))

# ---------------------------------------------------------------- S3: boundaries
cells.append(md("""\
## S3 — Flip boundaries

Linear interpolation in m of each claim's summary statistic (the common-random-numbers
design makes these curves smooth, so interpolation between the 0.05-grid points is
sound). EVPI and the switch bound are not monotone in m: they rise while the winner is
genuinely contested and fall again once large is near-certain, so each threshold gets a
first up-crossing, the peak, and (where the curve comes back down) a recovery crossing.
A claim already past its threshold at m = 1.00 gets `m_star = 1.0` with a note — that is
the baseline state, not a sweep finding.
""", "obs-s3-md"))

cells.append(code("""\
# S3 - boundary interpolation and the claim-by-claim readout.
def _interp(ms, vals, i, level):
    a, b = vals[i-1], vals[i]
    return float(ms[i-1] + (ms[i] - ms[i-1]) * (level - a) / (b - a))

def cross_down(ms, vals, level):
    \"\"\"First m where the series falls below level; (nan, note) if it never does.\"\"\"
    ms, vals = np.asarray(ms, float), np.asarray(vals, float)
    if vals[0] < level:
        return float(ms[0]), "below threshold at m=1.00 (baseline)"
    for i in range(1, len(ms)):
        if vals[i-1] >= level > vals[i]:
            return _interp(ms, vals, i, level), ""
    return np.nan, f"no crossing on [{ms[0]:.2f}, {ms[-1]:.2f}]"

def cross_up(ms, vals, level):
    \"\"\"First m where the series rises above level; (nan, note) if it never does.\"\"\"
    ms, vals = np.asarray(ms, float), np.asarray(vals, float)
    if vals[0] > level:
        return float(ms[0]), "above threshold at m=1.00 (baseline)"
    for i in range(1, len(ms)):
        if vals[i-1] <= level < vals[i]:
            return _interp(ms, vals, i, level), ""
    return np.nan, f"no crossing on [{ms[0]:.2f}, {ms[-1]:.2f}]"

def recovery_down(ms, vals, level):
    \"\"\"First m AFTER the peak where the series falls back below level.\"\"\"
    ms, vals = np.asarray(ms, float), np.asarray(vals, float)
    j = int(vals.argmax())
    if vals[j] <= level:
        return np.nan, "never above threshold"
    for i in range(j + 1, len(ms)):
        if vals[i-1] >= level > vals[i]:
            return _interp(ms, vals, i, level), ""
    return np.nan, f"still above threshold at m={ms[-1]:.2f}"

BOUND_ROWS = []
def brow(claim, cell, schedule, criterion, threshold, m_star, note="", value=np.nan):
    BOUND_ROWS.append(dict(claim=claim, cell=cell, schedule=schedule,
                           criterion=criterion, threshold=threshold,
                           m_star=m_star, value=value, note=note))

for aid in AIDS:
    sub = SWEEP[SWEEP["cell"] == aid]
    g = sub.groupby("m")
    ms = np.array(sorted(sub["m"].unique()))

    # --- S2-d: majority claim (C1 criterion) ---
    minP = g["P_smr"].min().loc[ms].to_numpy()
    mstar, note = cross_down(ms, minP, 0.5)
    brow("S2-d majority", aid, "min over schedules", "min P(SMR) crosses 0.5", 0.5,
         mstar, note)
    for sched in SCHED_ORDER:
        ss = sub[sub["schedule"] == sched].set_index("m")["P_smr"].loc[ms].to_numpy()
        mstar, note = cross_down(ms, ss, 0.5)
        brow("S2-d majority", aid, sched, "P(SMR) crosses 0.5", 0.5, mstar, note)

    # --- S2-c claim 1: EVPI ---
    maxE = g["EVPI_pct"].max().loc[ms].to_numpy()
    for th in EVPI_THRESHOLDS:
        mstar, note = cross_up(ms, maxE, th)
        brow("S2-c1 EVPI", aid, "max over schedules", f"EVPI crosses {th}%", th,
             mstar, note)
        mrec, rnote = recovery_down(ms, maxE, th)
        brow("S2-c1 EVPI", aid, "max over schedules", f"EVPI back below {th}%", th,
             mrec, rnote)
    jpk = int(maxE.argmax())
    brow("S2-c1 EVPI", aid, "max over schedules", "peak", np.nan,
         float(ms[jpk]), value=float(maxE[jpk]))

    # --- S2-c claim 2: 2036 switch bound ---
    maxB = g["bound_pct"].max().loc[ms].to_numpy()
    mstar, note = cross_up(ms, maxB, C5_THRESH_PCT)
    brow("S2-c2 switch bound", aid, "max over schedules",
         f"bound crosses {C5_THRESH_PCT}% (C5)", C5_THRESH_PCT, mstar, note)
    mrec, rnote = recovery_down(ms, maxB, C5_THRESH_PCT)
    brow("S2-c2 switch bound", aid, "max over schedules",
         f"bound back below {C5_THRESH_PCT}%", C5_THRESH_PCT, mrec, rnote)
    jpk = int(maxB.argmax())
    brow("S2-c2 switch bound", aid, "max over schedules", "peak", np.nan,
         float(ms[jpk]), value=float(maxB[jpk]))

    # --- S2-b: fragmentation (split vs best pure, npv object) ---
    minF = g["frag_npv_P50"].min().loc[ms].to_numpy()
    mstar, note = cross_down(ms, minF, 0.0)
    brow("S2-b fragmentation", aid, "min over schedules",
         "median split penalty crosses 0", 0.0, mstar, note,
         value=float(minF.min()))
    maxW = g["P_split_wins"].max().loc[ms].to_numpy()
    mstar, note = cross_up(ms, maxW, 0.5)
    brow("S2-b fragmentation", aid, "max over schedules",
         "P(split beats best pure) crosses 0.5", 0.5, mstar, note,
         value=float(maxW.max()))

BOUNDS = pd.DataFrame(BOUND_ROWS)

print("=== Flip boundaries (m* = the optimism multiplier where the claim turns) ===\\n")
for aid in AIDS:
    b = BOUNDS[BOUNDS["cell"] == aid]
    d = b[(b["claim"] == "S2-d majority") & (b["schedule"] == "min over schedules")].iloc[0]
    e1 = b[(b["claim"] == "S2-c1 EVPI") &
           (b["criterion"] == f"EVPI crosses {C5_THRESH_PCT}%")].iloc[0]
    ep = b[(b["claim"] == "S2-c1 EVPI") & (b["criterion"] == "peak")].iloc[0]
    c2 = b[(b["claim"] == "S2-c2 switch bound") &
           (b["criterion"] == f"bound crosses {C5_THRESH_PCT}% (C5)")].iloc[0]
    cp = b[(b["claim"] == "S2-c2 switch bound") & (b["criterion"] == "peak")].iloc[0]
    f = b[(b["claim"] == "S2-b fragmentation") &
          (b["criterion"] == "median split penalty crosses 0")].iloc[0]
    def _fmt(r):
        return f"{r['m_star']:.3f}" + (f"  [{r['note']}]" if r["note"] else "")
    print(f"{aid} (kappa = {AIDS[aid]}):")
    print(f"  S2-d majority claim fails (min P(SMR) < 0.5) at m* = {_fmt(d)}")
    print(f"  S2-c1 EVPI exceeds {C5_THRESH_PCT}% at m* = {_fmt(e1)}; "
          f"peak {ep['value']:.2f}% at m = {ep['m_star']:.2f}")
    print(f"  S2-c2 switch bound exceeds {C5_THRESH_PCT}% at m* = {_fmt(c2)}; "
          f"peak {cp['value']:.2f}% at m = {cp['m_star']:.2f}")
    print(f"  S2-b split-beats-committed at m* = {_fmt(f)} "
          f"(most negative median penalty on the grid: {f['value']:+.1f}%)")
    print()
""", "obs-s3-bounds"))

# ---------------------------------------------------------------- S4: figure
cells.append(md("""\
## S4 — The flip-curve figure

Four panels, one per claim, each metric against the multiplier m with its threshold
line and the interpolated crossings marked. A notebook diagnostic, not a paper display —
paper placement is a separate decision.

*Figure note (saved: `obs_flip_curves.png`): panel a — min-over-schedules P(SMR wins)
per anchor cell, with the min–max band across schedules and the 0.5 majority line;
panel b — the 50/50-split penalty (median, P10–P90 band for κ = 1) vs the best pure
program; panel c — max-over-schedules EVPI; panel d — max-over-schedules 2036 switch
bound; c and d carry the 1% C5 threshold (solid) and 2% (dotted). Dots mark
interpolated crossings.*
""", "obs-s4-md"))

cells.append(code("""\
# S4 - the flip-curve figure.
KCOL = {"k100": INK, "k050": ps.ACCENT["violet"], "k000": ps.ACCENT["gold"]}
KLAB = {"k100": "κ = 1 (fully coupled)", "k050": "κ = 0.5", "k000": "κ = 0 (independent)"}

fig, axes = plt.subplots(2, 2, figsize=(ps.W2, 8.0))
ms_all = np.array(sorted(SWEEP["m"].unique()))

ax = axes[0, 0]
for aid in AIDS:
    g = SWEEP[SWEEP["cell"] == aid].groupby("m")
    ax.fill_between(ms_all, g["P_smr"].min().loc[ms_all], g["P_smr"].max().loc[ms_all],
                    color=KCOL[aid], alpha=0.12)
    ax.plot(ms_all, g["P_smr"].min().loc[ms_all], color=KCOL[aid], lw=2, label=KLAB[aid])
    r = BOUNDS[(BOUNDS["cell"] == aid) & (BOUNDS["claim"] == "S2-d majority")
               & (BOUNDS["schedule"] == "min over schedules")].iloc[0]
    if np.isfinite(r["m_star"]) and not r["note"]:
        ax.plot([r["m_star"]], [0.5], "o", color=KCOL[aid], ms=6, zorder=5)
ax.axhline(0.5, color=ps.ACCENT["red"], lw=1.2)
ax.set_ylabel("probability the all-SMR program is cheaper\\n(line: lowest schedule; band: range across schedules)")
ax.set_ylim(0, 1)
ax.legend(fontsize=8, loc="upper right")

ax = axes[0, 1]
for aid in AIDS:
    g = SWEEP[(SWEEP["cell"] == aid)].groupby("m")
    if aid == "k100":
        ax.fill_between(ms_all, g["frag_npv_P10"].min().loc[ms_all],
                        g["frag_npv_P90"].max().loc[ms_all], color=KCOL[aid], alpha=0.10)
    ax.plot(ms_all, g["frag_npv_P50"].min().loc[ms_all], color=KCOL[aid], lw=2,
            label=KLAB[aid])
ax.axhline(0.0, color=ps.ACCENT["red"], lw=1.2)
ax.set_ylabel("50/50-split penalty vs best pure program (%)\\n"
              "(median, min over schedules; band: k=1 P10-P90)")
ax.legend(fontsize=8, loc="upper left")

for ax, col, lab in [(axes[1, 0], "EVPI_pct", "EVPI (% of expected program cost)"),
                     (axes[1, 1], "bound_pct",
                      "2036 switch bound (% of expected program cost)")]:
    for aid in AIDS:
        g = SWEEP[SWEEP["cell"] == aid].groupby("m")
        ax.plot(ms_all, g[col].max().loc[ms_all], color=KCOL[aid], lw=2, label=KLAB[aid])
    ax.axhline(C5_THRESH_PCT, color=ps.ACCENT["red"], lw=1.2)
    ax.axhline(2.0, color=ps.ACCENT["red"], lw=1.0, ls=":")
    ax.set_ylabel(lab + "\\n(max over schedules)")
    ax.legend(fontsize=8, loc="upper right")

for ax in axes.ravel():
    ax.set_xlabel("SMR optimism-bias multiplier m\\n(true SMR cost = m × sampled cost)")
ps.letter_panels(list(axes.ravel()))
plt.tight_layout()
ps.savefig(fig, FIGURES / "obs_flip_curves.png")
plt.show()
""", "obs-s4-figure"))

# ------------------------------------------------- S4b: paper Fig 3 panels c/d
cells.append(md("""\
## S4b — Paper Fig 3 panels c and d

The 2026-08-26 sweep replaced the main paper's Fig 3c (EVPI vs κ) and Fig 3d (2036
switch bound vs κ) with optimism-bias sweep curves. The 2026-08-31 third recomposition
(Ethan, S2 drafting) re-paired the 2×2 as winner/value-of-waiting × baseline/optimism:
panel c is now the **majority flip curve** (S4's panel a at paper size) and panel d the
**EVPI sweep**. The standalone bound sweep `obs_bound_vs_m.png` is retired from the
paper (the file on disk is a record artifact with its historical baked "d"): the
bound-vs-m curve stays in `obs_flip_curves.png` (SI, the flip-curve page), and the
baseline bound κ-profile moved into main Fig 3b (`tech_comparison.ipynb`, cell t8c).
House rule: the internally lettered source carries the FINAL panel letters ("c", "d");
the paper compose runs with `letters=""`.

*Figure note (saved: `obs_majority_vs_m.png`, `obs_evpi_vs_m.png`): min-over-schedules
P(SMR wins) with the min–max band, the 0.5 majority line, and the interpolated flip
points (c); max-over-schedules EVPI with the pre-registered 1% C5 threshold and its
interpolated crossings (d) — both against the optimism multiplier m per dependence
anchor.*
""", "obs-s4b-md"))

cells.append(code("""\
# S4b - paper Fig 3 panels c and d (baked final letters; composed with letters="").
# Recomposed 2026-08-31: c = the majority flip curve, d = the EVPI sweep. The
# standalone bound sweep (obs_bound_vs_m.png) is retired from the paper -- its
# curve stays in obs_flip_curves.png (SI flip-curve page), and the baseline bound
# kappa-profile is main Fig 3b (tech_comparison t8c).

# panel c - the majority claim vs m (S4's panel a at paper-panel size)
fig, ax = plt.subplots(figsize=(6.4, 4.2))
for aid in AIDS:
    g = SWEEP[SWEEP["cell"] == aid].groupby("m")
    ax.fill_between(ms_all, g["P_smr"].min().loc[ms_all], g["P_smr"].max().loc[ms_all],
                    color=KCOL[aid], alpha=0.12)
    ax.plot(ms_all, g["P_smr"].min().loc[ms_all], color=KCOL[aid], lw=2, label=KLAB[aid])
    r = BOUNDS[(BOUNDS["cell"] == aid) & (BOUNDS["claim"] == "S2-d majority")
               & (BOUNDS["schedule"] == "min over schedules")].iloc[0]
    if np.isfinite(r["m_star"]) and not r["note"]:
        ax.plot([r["m_star"]], [0.5], "o", color=KCOL[aid], ms=6, zorder=5)
ax.axhline(0.5, color=ps.ACCENT["red"], lw=1.2)
ax.set_xlabel("SMR optimism-bias multiplier m\\n(true SMR cost = m × sampled cost)")
ax.set_ylabel("probability the all-SMR program is cheaper\\n(line: lowest schedule; band: range across schedules)")
ax.set_ylim(0, 1)
ax.legend(fontsize=8, loc="upper right")
ps.panel_letter(ax, "c")
fig.tight_layout()
ps.savefig(fig, FIGURES / "obs_majority_vs_m.png")
plt.show()

# panel d - the EVPI sweep (baked letter c until 2026-08-31)
fig, ax = plt.subplots(figsize=(6.4, 4.2))
for aid in AIDS:
    g = SWEEP[SWEEP["cell"] == aid].groupby("m")
    ax.plot(ms_all, g["EVPI_pct"].max().loc[ms_all], color=KCOL[aid], lw=2,
            label=KLAB[aid])
ax.axhline(C5_THRESH_PCT, color=ps.ACCENT["red"], lw=1.2)
for aid in AIDS:
    r = BOUNDS[(BOUNDS["cell"] == aid) & (BOUNDS["claim"] == "S2-c1 EVPI")
               & (BOUNDS["criterion"] == f"EVPI crosses {C5_THRESH_PCT}%")].iloc[0]
    if np.isfinite(r["m_star"]) and not r["note"]:
        ax.plot([r["m_star"]], [C5_THRESH_PCT], "o", color=KCOL[aid], ms=6, zorder=5)
ax.set_xlabel("SMR optimism-bias multiplier m\\n(true SMR cost = m × sampled cost)")
ax.set_ylabel("value of perfect information\\n(% of expected program cost)")
ax.legend(fontsize=8, loc="upper right")
ps.panel_letter(ax, "d")
fig.tight_layout()
ps.savefig(fig, FIGURES / "obs_evpi_vs_m.png")
plt.show()
""", "obs-s4b-panels"))

# ---------------------------------------------------------------- S5: exports
cells.append(code("""\
# S5 - exports + metadata (tc_metadata pattern: seed, grid, streams, file hashes).
SWEEP.to_csv(EXPORTS / "sweep_metrics.csv", index=False)
BOUNDS.to_csv(EXPORTS / "flip_boundaries.csv", index=False)

def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

meta = {
    "master_seed": MASTER_SEED,
    "n_draws": N_DRAWS_TC,
    "m_grid": [float(m) for m in M_GRID],
    "anchors": AIDS,
    "thresholds": {"majority": 0.5, "evpi_pct": EVPI_THRESHOLDS,
                   "bound_pct": C5_THRESH_PCT, "frag_median_pct": 0.0},
    "stream_note": ("kappa<1 draws reuse tech_comparison's ob-cell streams "
                    "(tccomp/world/ob@{aid}/{tok}), held fixed across all m: "
                    "common random numbers + bit-exact m=1.5 pins. kappa=1 uses the "
                    "frozen mc_perdraw.npz uniforms (deterministic)."),
    "streams_used": sorted(set(STREAMS_USED)),
    "files": {f: _sha(EXPORTS / f) for f in ["sweep_metrics.csv", "flip_boundaries.csv"]},
}
(EXPORTS / "ob_sweep_metadata.json").write_text(json.dumps(meta, indent=1) + "\\n",
                                                encoding="utf-8")
print(f"exports written -> {EXPORTS}")
for f, h in meta["files"].items():
    print(f"  {f}  sha256 {h[:16]}...")
""", "obs-s5-exports"))

# ---------------------------------------------------------------- S6: QA
cells.append(md("""\
## S6 — QA: pins to the published exports

The sweep must land exactly on the published tech_comparison numbers at both ends:

- **QA-1 (exact, m = 1.5):** min/max P(SMR) over schedules reproduces the
  `stress_survival.csv` `ob@k100/k050/k000` rows — same streams, same engine, so the
  match is bit-for-bit (compared at the CSV's 4-decimal precision).
- **QA-2 (exact to float noise, m = 1.0 at κ = 1):** per-schedule P(SMR), EVPI, and the
  switch bound reproduce the published `robustness_map.csv` / `evpi_total.csv` /
  `adaptive_value.csv` k100 rows. The sweep re-derives the marginals from the recovered
  npz uniforms (the `variant="ob"` path), so agreement is to ~1e-9 float error, not
  bit-for-bit — tolerance 1e-3.
- **QA-3 (statistical, m = 1.0 at κ = 0.5/0):** the sweep's baseline estimate uses the
  ob-cell streams, not the baseline streams, so it must match the published baseline
  within Monte Carlo error (tolerance 0.03 on P, 0.5 pp on EVPI/bound).
- **QA-4 (S13 cross-check):** at m = 1.0, κ = 1, the capex-object 50/50 penalty median
  for McKinsey reproduces the S13 fragmentation headline (16.7%, tolerance 0.6 pp) —
  same frozen worlds, same arithmetic, independent implementation.
- **QA-5 (monotonicity):** P(SMR) is non-increasing in m — exactly at κ = 1 (shared
  draws; the SMR program cost is strictly increasing in m per draw), and up to a 0.02
  rejection-resampling tolerance at κ < 1.

All pins are skipped (with a notice) on smoke runs below 10k draws.
""", "obs-s6-md"))

cells.append(code("""\
# S6 - QA pins.
TC_EXP = MC_EXPORTS / "tech_comparison"
qa_fail = []

def qa(name, ok, detail):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    if not ok:
        qa_fail.append(name)

if N_DRAWS_TC < 10000:
    print(f"SMOKE RUN ({N_DRAWS_TC} draws): published-export pins skipped.")
else:
    # QA-1: m=1.5 reproduces the stress rows bit-for-bit (CSV 4-decimal precision).
    stress = pd.read_csv(TC_EXP / "stress_survival.csv")
    for aid in AIDS:
        pub = stress[(stress["stress"] == "OB x1.5")
                     & (stress["cell"] == f"ob@{aid}")].iloc[0]
        sub = SWEEP[(SWEEP["cell"] == aid) & (SWEEP["m"] == 1.5)]
        lo, hi = sub["P_smr"].min(), sub["P_smr"].max()
        ok = (abs(round(lo, 4) - pub["min_P_smr"]) <= 5e-5
              and abs(round(hi, 4) - pub["max_P_smr"]) <= 5e-5)
        qa(f"QA-1 ob@{aid}", ok, f"sweep {lo:.4f}/{hi:.4f} vs published "
                                 f"{pub['min_P_smr']}/{pub['max_P_smr']}")

    # QA-2: m=1.0 at kappa=1 reproduces the published baseline (float-noise tolerance).
    rob = pd.read_csv(TC_EXP / "robustness_map.csv")
    evp = pd.read_csv(TC_EXP / "evpi_total.csv")
    ada = pd.read_csv(TC_EXP / "adaptive_value.csv")
    sub = SWEEP[(SWEEP["cell"] == "k100") & (SWEEP["m"] == 1.0)].set_index("schedule")
    for name, pub_df, pub_col, swp_col, tol in [
            ("P(SMR)", rob, "P_smr", "P_smr", 1e-3),
            ("EVPI", evp, "EVPI_pct", "EVPI_pct", 1e-3),
            ("bound", ada, "bound_pct", "bound_pct", 1e-3)]:
        pub = pub_df[pub_df["cell"] == "k100"].set_index("schedule")[pub_col]
        diff = (sub[swp_col] - pub).abs().max()
        qa(f"QA-2 k100 {name}", diff <= tol, f"max |diff| = {diff:.2e} (tol {tol})")

    # QA-3: m=1.0 at kappa=0.5/0 matches the published baseline within MC error.
    for aid in ("k050", "k000"):
        sub = SWEEP[(SWEEP["cell"] == aid) & (SWEEP["m"] == 1.0)].set_index("schedule")
        pubP = rob[rob["cell"] == aid].set_index("schedule")["P_smr"]
        dP = (sub["P_smr"] - pubP).abs().max()
        pubE = evp[evp["cell"] == aid].set_index("schedule")["EVPI_pct"]
        dE = (sub["EVPI_pct"] - pubE).abs().max()
        pubB = ada[ada["cell"] == aid].set_index("schedule")["bound_pct"]
        dB = (sub["bound_pct"] - pubB).abs().max()
        qa(f"QA-3 {aid}", dP <= 0.03 and dE <= 0.5 and dB <= 0.5,
           f"max |dP| = {dP:.4f} (tol 0.03), |dEVPI| = {dE:.3f}, "
           f"|dbound| = {dB:.3f} (tol 0.5)")

    # QA-4: S13 fragmentation headline (16.7% median, capex object, McKinsey, kappa=1).
    v = SWEEP[(SWEEP["cell"] == "k100") & (SWEEP["m"] == 1.0)
              & (SWEEP["schedule"] == REP_SCHED)]["frag_cap_P50"].iloc[0]
    qa("QA-4 S13 fragmentation", abs(v - 16.7) <= 0.6,
       f"capex-object split penalty median {v:.2f}% vs S13 16.7% (tol 0.6)")

# QA-5: monotonicity (runs at any draw count).
worst = {}
for (aid, sched), grp in SWEEP.groupby(["cell", "schedule"]):
    d = np.diff(grp.sort_values("m")["P_smr"].to_numpy())
    worst[aid] = max(worst.get(aid, 0.0), float(d.max()) if len(d) else 0.0)
qa("QA-5 monotonicity k100", worst["k100"] <= 1e-12,
   f"max P(SMR) increase step = {worst['k100']:.2e} (exact expected)")
qa("QA-5 monotonicity k050/k000", max(worst["k050"], worst["k000"]) <= 0.02,
   f"max increase step = {max(worst['k050'], worst['k000']):.4f} (tol 0.02)")

assert not qa_fail, f"QA failures: {qa_fail}"
print("\\nQA complete: all pins green.")
""", "obs-s6-qa"))

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "playground-env", "language": "python",
                       "name": "python3"},
        "language_info": {"name": "python", "version": "3.12.3"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
OUT_PATH.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"wrote {OUT_PATH} ({len(cells)} cells)")
