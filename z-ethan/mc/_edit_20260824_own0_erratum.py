"""own0 anchor adjudication erratum (2026-08-24) + companion documentation sentences.

Ethan challenged N_BOAK_UNITS = 2 as an off-by-one ("prices the 3OAK at the 2OAK cost");
a unit-by-unit hand check reversed the diagnosis: own(t) = own0 + post-anchor completions
entering t is the INCLUSIVE Wright index of the unit currently being built (given one
completed FOAK per vendor), so the base must be the inclusive index of the anchor-cost
unit -- BOAK = 2nd unit => own0 = 2, exact at every unit. own0 = 1 would price unit N at
C(2(N-1)): asymptotically one full doubling of excess learning. The ARITHMETIC was always
right; the "O_0 = 2 own units" completed-stock PROSE was wrong and caused the scare.

Edits (mc_cost_trajectories.ipynb):
- S5 Step 4 (cell e8044b0e): inclusive-index statement + the adjudication's worked check.
- S5 Step 6: tiny-base bullet rephrased; hist_us per-unit note (135 units, 116.9 GW,
  avg 866 MW); pipeline-base caveat after D8; cross-tech per-unit asymmetry sentence.
- Engine cell c09fbf4f: own0 semantics comment.
- Duration cell 0305c9eb: series-2 anchor note (published-level pins; conv_full never
  enters durations).
- QA4 cell 8ba226ac: the $500 tolerance is one structural artifact, not rounding.
- Fan figure note (cell 01ff8862): 2030 splice kink explanation.
- New S14 cell pipe-base-sensitivity (after c4112c4e): self-contained re-pricing with the
  theta-weighted committed pipeline credited to the 2030 cross-firm base at weight s ->
  exports/pipeline_base_sensitivity.csv.

Code cells change (comments + one new cell), so the notebook needs one headless
re-execution (deterministic seed; existing exports regenerate identically). Idempotent.
"""
import json
import re
from pathlib import Path

NB = Path(__file__).resolve().parent / "mc_cost_trajectories.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
CELLS = {c["id"]: c for c in nb["cells"]}

if "inclusive Wright index" in "".join(CELLS["e8044b0e"]["source"]):
    print("erratum already applied; nothing to do")
    raise SystemExit(0)

n = 0


def rep(cid, old, new):
    """Exact replace (code cells: formatting is significant)."""
    global n
    s = "".join(CELLS[cid]["source"])
    assert s.count(old) == 1, f"cell {cid}: pattern not unique/found:\n{old[:160]}"
    CELLS[cid]["source"] = s.replace(old, new).splitlines(keepends=True)
    n += 1


def rep_ws(cid, old, new):
    """Whitespace-tolerant replace (markdown cells: prose wraps at arbitrary columns)."""
    global n
    s = "".join(CELLS[cid]["source"])
    pat = re.compile(r"\s+".join(re.escape(t) for t in old.split()))
    ms = list(pat.finditer(s))
    assert len(ms) == 1, f"cell {cid}: {len(ms)} ws-tolerant matches for:\n{old[:160]}"
    m = ms[0]
    CELLS[cid]["source"] = (s[:m.start()] + new + s[m.end():]).splitlines(keepends=True)
    n += 1


# ---- S5 Step 4: the inclusive-index statement + worked check (cell e8044b0e) --------
rep_ws("e8044b0e",
    "So at the 2030 anchor the representative vendor has $O_0 = 2$ own units and, in a "
    "symmetric market where every vendor is at the same point, the other $m-1$ vendors "
    "contribute $A_0 = 2(m-1)$.",
    "So the anchor sits at **inclusive Wright index 2** on each vendor's curve: one completed\n"
    "FOAK plus the BOAK itself, the unit whose cost the 2030 estimate quotes. $O_0 = 2$ is that\n"
    "index, **not** a count of two completed units — the convention embeds exactly *one*\n"
    "completed build per vendor. With the entering-year lag (S5 `lag1`), the state variable\n"
    "$O(t) = O_0 + N^{US}(t)/m$ is then exactly the inclusive index of the unit currently being\n"
    "built (completed predecessors plus one), so the anchored ratio prices every unit at its own\n"
    "curve position. Unit-by-unit check (adjudicated 2026-08-24 — LR 10%, FOAK \\$10{,}000,\n"
    "BOAK \\$9{,}000, one completed FOAK, one build per year; true Wright costs of units 2/3/4\n"
    "are \\$9{,}000 / \\$8{,}462 / \\$8{,}100): the engine at $O_0 = 2$ reproduces all three\n"
    "*exactly*, while the superficially \"exclusive\" $O_0 = 1$ gives \\$9{,}000 / \\$8{,}100 /\n"
    "\\$7{,}615 — it prices unit $N$ at $C(2(N-1))$, asymptotically one full doubling of excess\n"
    "learning, re-earning the FOAK→BOAK decline already embedded in the BOAK price. In a\n"
    "ratio-form engine the base must be the inclusive index of the anchor-cost unit. In a\n"
    "symmetric market where every vendor is at the same point, the other $m-1$ vendors\n"
    "contribute $A_0 = 2(m-1)$.")

# ---- S5 Step 6: tiny-base bullet (cell e8044b0e) ------------------------------------
rep_ws("e8044b0e",
    "a genuinely new design restarts its curve — the vendor's base is just its 2 BOAK units "
    "(Abou-Jaoude et al. 2024 convention).",
    "a genuinely new design restarts its curve — the vendor's base is just the BOAK anchor\n"
    "  index of 2 (one completed FOAK plus the BOAK itself; Abou-Jaoude et al. 2024 convention).")

# ---- S5 Step 6: hist_us per-unit note (cell e8044b0e) -------------------------------
rep_ws("e8044b0e",
    "Each vendor inherits its share $H^{US}/m$ of the ~140 historical US units,",
    "Each vendor inherits its share $H^{US}/m$ of the historical US units (135 ever\n"
    "  grid-connected, 116.9 GW — average 866 MW; counted as raw units on the per-unit\n"
    "  convention: the project, not its megawatts, is the experience quantum),")

# ---- S5 Step 6: pipeline-base caveat after D8 (cell e8044b0e) -----------------------
rep_ws("e8044b0e",
    "where $H^{KV} = \\sum_r \\theta_r H_r$ is the θ-weighted historical world stock, entering "
    "the cross-firm stock at weight $s$ for both technologies alike (Step 5's unsplit "
    "convention).",
    "where $H^{KV} = \\sum_r \\theta_r H_r$ is the θ-weighted historical world stock, entering\n"
    "the cross-firm stock at weight $s$ for both technologies alike (Step 5's unsplit\n"
    "convention).\n"
    "\n"
    "One conservatism is carried knowingly (adjudicated 2026-08-24): the ~62 foreign units under\n"
    "construction — mostly completing before 2030 — are counted in neither $H^{KV}$ nor the\n"
    "post-anchor flows (the committed pipeline is blanked at the anchor, S3), understating the\n"
    "2030 cross-firm base by roughly 10% of $H^{KV}$ and steepening post-2030 foreign-driven\n"
    "learning by about one point of 2050 OCC. The S14 pipeline-base sensitivity quantifies it;\n"
    "it is bracketed by the same structural dial ($c$) that excludes the entire historical stock\n"
    "in tiny-base worlds, and is flagged to fold into any future full regeneration.")

# ---- S5 cross-tech per-unit asymmetry sentence (cell e8044b0e) ----------------------
rep_ws("e8044b0e",
    "a fraction $x$ of the other technology's **domestic program** $N^{US}_{oth}$ joins the "
    "cross-firm stock $A$, learning at ω·LR like any other not-own-design experience.",
    "a fraction $x$ of the other technology's **domestic program** $N^{US}_{oth}$ joins the\n"
    "cross-firm stock $A$, learning at ω·LR like any other not-own-design experience. Because\n"
    "stocks count units, a gigawatt of SMR program contributes $1/0.3 \\approx 3.3\\times$ the\n"
    "units of a gigawatt of large program — per-GW cross-tech spillover is tech-asymmetric by\n"
    "construction, the per-unit convention applied consistently.")

# ---- Engine cell: own0 semantics comment (cell c09fbf4f) ----------------------------
rep("c09fbf4f",
    "    own0 = N_BOAK_UNITS + conv*hist_us/m                     # per-vendor domestic base (D8/D8')",
    "    # own0 is the anchor's INCLUSIVE Wright index (one completed FOAK + the BOAK itself),\n"
    "    # not a completed-unit count; own(t) below is then the inclusive index of the unit\n"
    "    # currently being built (completed predecessors + 1) - see the S5 Step 4 worked check\n"
    "    # (adjudicated 2026-08-24: own0 = 1 would over-credit one full doubling).\n"
    "    own0 = N_BOAK_UNITS + conv*hist_us/m                     # per-vendor domestic base (D8/D8')")

# ---- Duration cell: series-2 anchor note (cell 0305c9eb) ----------------------------
rep("0305c9eb",
    "    series = np.clip(2 + np.floor(n_own/2.0).astype(int), 2, len(INL_DUR_MOD))  # next build = series 2",
    "    # Anchor note (2026-08-24): the series-2 start is where the published duration LEVELS\n"
    "    # attach (INL Fig. 18's next-build 88/70 months for large; Abou-Jaoude's 55/43-month\n"
    "    # SMR estimates via the 55/82 ratio at this same point). It credits each vendor one\n"
    "    # completed two-unit plant - one unit more generous than the cost anchor's inclusive\n"
    "    # index 2 (one completed FOAK) - a deliberate, separately pinned convention; the\n"
    "    # experience-base dial (conv_full) never enters durations.\n"
    "    series = np.clip(2 + np.floor(n_own/2.0).astype(int), 2, len(INL_DUR_MOD))  # next build = series 2")

# ---- QA4: the saturated tolerance is one structural artifact (cell 8ba226ac) --------
rep("8ba226ac",
    "assert worst <= 500.0, worst",
    "# NOTE (2026-08-24): worst lands on $500 exactly via ONE structural artifact, not rounding:\n"
    "# fref is pinned at 1 GW for all three scenarios while Conservative has 0 GW in 2030, so\n"
    "# the N > 0 branch forces mult = 1 at 2030/2035; every other year's error is <= $164.\n"
    "assert worst <= 500.0, worst")

# ---- Fan figure note: 2030 splice kink (cell 01ff8862) ------------------------------
rep_ws("01ff8862",
    "the fans start in 2025 with the plot-only FOAK→BOAK backcast segment descending into the "
    "2030 anchor.",
    "the fans start in 2025 with the plot-only FOAK→BOAK backcast segment descending into the\n"
    "2030 anchor. The backcast credits the θ-weighted committed pipeline in its cross-firm base\n"
    "while the engine's 2030 base does not (the documented conservatism quantified in S14's\n"
    "pipeline-base sensitivity), so the fan's slope can kink slightly at the 2030 splice — a\n"
    "display artifact, not a level discontinuity (both segments share the anchor value).")

# ---- New S14 cell: pipeline-base sensitivity (after c4112c4e) -----------------------
PIPE_CELL = r'''# Pipeline-base sensitivity (structural, SELF-CONTAINED - not an engine path): re-price
# with the theta-weighted committed pipeline (S3's real under-construction units, completing
# 2025-2030) credited to the 2030 CROSS-FIRM BASE at weight s, exactly as the plot-only
# backcast already does (S9's PIPE_PRE). The production engine excludes it (S3: the pipeline
# is blanked at the anchor), which understates the 2030 cross-firm base and steepens
# post-2030 foreign-driven learning. Adjudicated 2026-08-24: kept as a documented caveat -
# the effect (below) is ~1 point of 2050 OCC, inside the structural bracket the tiny/full
# dial already spans - and flagged to fold into any future full regeneration.
_PIPE_TOT = float(sum(THETA_KV[r]*sum(PIPELINE_GW[r].values())/UNIT_FOREIGN_GW
                      for r in REGIONS))

def _occ_ces_pipe_base(world, tech, n_us, n_oth=None):
    """SENSITIVITY ONLY. occ_paths_ces with s*_PIPE_TOT added to the cross-firm stock at
    ALL years (a base credit shifts anchor and path alike; only the ratio prices)."""
    own, oth = experience_channels(world, tech, n_us, n_oth=n_oth)
    oth = oth + world["s"].values[:, None]*_PIPE_TOT
    lr = world[f"lr_{tech}"].values[:, None]
    b1, b2 = np.log2(1.0 - lr), np.log2(1.0 - OMEGA*lr)
    b, w = -(b1 + b2), b1/(b1 + b2)
    rho = world["ces_rho"].values[:, None]
    geo = np.abs(rho) < CES_EPS
    lnO, lnA = np.log(own), np.log(oth)
    lnE = np.where(geo, w*lnO + (1.0-w)*lnA,
                   lnO + np.log1p((1.0-w)*np.expm1(np.where(geo, 0.0, rho)*(lnA - lnO)))
                       / np.where(geo, 1.0, rho))
    return world[f"boak_{tech}"].values[:, None] * np.exp(-b*(lnE - lnE[:, [yi(ANCHOR)]]))

pipe_rows = {}
for tech in TECH:
    base = occ_paths_ces(WORLDS[FRAG_SCHED], tech, USN_NEW[tech][FRAG_SCHED])[:, yi(2050)]
    cred = _occ_ces_pipe_base(WORLDS[FRAG_SCHED], tech, USN_NEW[tech][FRAG_SCHED])[:, yi(2050)]
    pipe_rows[tech] = {
        "P50 engine": np.percentile(base, 50), "P50 credited": np.percentile(cred, 50),
        "P50 delta %": 100.0*(np.percentile(cred, 50)/np.percentile(base, 50) - 1.0),
        "P95 delta %": 100.0*(np.percentile(cred, 95)/np.percentile(base, 95) - 1.0),
        "max |draw delta| %": 100.0*np.abs(cred/base - 1.0).max()}
pipe_tab = pd.DataFrame(pipe_rows).T.round(2)
print(f"2050 OCC with the committed pipeline ({_PIPE_TOT:.1f} theta-weighted units) credited"
      f" to the 2030 cross-firm base ($/kW 2022, {FRAG_SCHED}):")
print(pipe_tab.to_string())
assert (pipe_tab["P50 delta %"] > 0).all() and (pipe_tab["P50 delta %"] < 5.0).all(), \
    "pipeline base credit outside the expected ~1-point scale"
pipe_tab.to_csv(EXPORTS / "pipeline_base_sensitivity.csv")
print("-> exports/pipeline_base_sensitivity.csv (caveat: S5 Step 6 / D8 note; ledger: fold"
      " into any future full regeneration)")
'''
idx = next(i for i, c in enumerate(nb["cells"]) if c["id"] == "c4112c4e")
assert not any(c["id"] == "pipe-base-sensitivity" for c in nb["cells"])
nb["cells"].insert(idx + 1, {
    "cell_type": "code", "id": "pipe-base-sensitivity", "metadata": {},
    "execution_count": None, "outputs": [],
    "source": PIPE_CELL.splitlines(keepends=True)})
n += 1

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"applied {n} edits (8 text + 1 new cell) -> {NB.name}")
