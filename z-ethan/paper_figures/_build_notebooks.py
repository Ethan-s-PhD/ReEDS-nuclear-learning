"""Generate main_paper_figures.ipynb and appendix_figures.ipynb.

Repo pattern: like step4_analysis/_build_notebook.py, the .ipynb files are
emitted from this script so they stay regenerable and diffable. Run:

    python _build_notebooks.py

then execute both notebooks headless on the playground-env kernel.
"""

from textwrap import dedent

import nbformat as nbf

KERNEL = {"display_name": "playground-env", "language": "python", "name": "python3"}


def md(s):
    return nbf.v4.new_markdown_cell(dedent(s).strip())


def code(s):
    return nbf.v4.new_code_cell(dedent(s).strip())


def write(cells, path):
    nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": KERNEL})
    nbf.write(nb, path)
    print(f"wrote {path} ({len(cells)} cells)")


SETUP = """
import pandas as pd

import paperlib as P
from paperlib import (MC_FIG, MC_EXP, S3_FIG, S3_EXP, S4_FIG, S4_EXP, S3C_EXP,
                      S4C_EXP, ITCFB_FIG, ITCFB_EXP, ITCFBM_FIG, ITCFBM_EXP,
                      BD_FIG, BD_EXP, IC_FIG, IC_EXP, RD_FIG, RD_EXP, MT_FIG, MT_EXP)

pd.set_option("display.max_columns", 40)
pd.set_option("display.width", 160)
TO2024 = P.to2024()
print(f"repo: {P.REPO}")
print(f"2004$ -> 2024$ multiplier (from inputs/financials/deflator.csv): {TO2024:.4f}")
"""

GLOSSARY = r"""
## Glossary — read this first

We use each term below many times. We give its plain meaning once, here.
The same word always has the same meaning in this notebook.

| Term | Plain meaning |
|---|---|
| **Schedule** | A target path for new US nuclear capacity, in gigawatts (GW), from now to 2050. The paper prices six schedules. It does not rank or endorse them. |
| **Mandate** | A rule added to the model: "at least this much new nuclear capacity must exist in year t." Each schedule becomes one mandate. |
| **ReEDS** | The national power-system planning model (NREL). It chooses the cheapest mix of plants and transmission that meets demand and all rules. |
| **Shadow price (dual)** | The price the model puts on the mandate rule. It equals the yearly rental payment, per kilowatt of mandated capacity, that would just make builders willing to build. Units: dollars per kW per year, in 2024 dollars. A shadow price of zero means the mandate needs no subsidy that year. The main text says "shadow price"; "dual" is the optimization term, used only in Methods (and in the exported file and column names, which keep it). |
| **Learning rate** | The percent cost drop each time total built capacity doubles. Example: a 10% learning rate means the second 10 GW costs 10% less per kW than the first 10 GW. |
| **Learning curve** | The cost path that a learning rate produces as capacity grows. |
| **OCC (overnight capital cost)** | The cost to build a plant if it could be built "overnight" — no construction-period interest. Units: \$/kW. |
| **Financed capex** | OCC plus the interest that accrues during the construction years. Long builds raise it. |
| **SMR / large** | The two reactor technology families: small modular reactors, and large conventional reactors. |
| **Cost world** | One complete random draw of all uncertain cost inputs (learning rates, starting costs, build durations, and so on). The Monte Carlo makes 10,000 worlds per schedule. |
| **P5 / P50 / P95 world** | Actual single draws ranked by total program cost: a cheap world (5th percentile), the median world, and an expensive world (95th percentile). |
| **Conditional cost trajectory** | A cost path that is only valid if its paired deployment schedule actually happens. None of our cost fans is a forecast. |
| **ITC (investment tax credit)** | The main US subsidy instrument: the government returns a set percentage of a plant's capital cost through the tax system. The current base credit (section 48E) is 30%, with bonuses up to about 50%. |
| **Model credit convention (i_model)** | The paper's headline rate convention: the credit is valued inside ReEDS's own financing arithmetic, where a credit dollar also carries construction-period carrying cost. Two real designs deliver it (a progress payment during construction, or a placed-in-service claim on the interest-inclusive tax basis), and both cost the government the same present value. The exported companion i_pis = i_model x ccmult converts to a placed-in-service credit on an overnight-cost-only basis. |
| **The floor / instrument menu** | The floor is the minimum net government cost that delivers the required support to every build — a flat dollar-per-MW payment at commissioning with no monetization loss. It is the cost benchmark, not a proposed design; the menu prices every instrument as a multiple of it. |
| **κ (kappa) coupling** | A dial for how strongly the two technologies' cost uncertainties move together. κ = 1: what is expensive for one is expensive for the other. κ = 0: independent. The grid couples two uncertainties separately: the learning rates, and the anchor costs. |
| **Anchor cost (BOAK)** | Each technology's 2030 starting cost, in \$/kW: the point that pins its learning curve. The Monte Carlo draws it per technology. |
| **Decoupled-anchor probe** | One cell of the dependence grid: the two technologies' learning rates stay fully coupled, but each technology draws its anchor cost independently. This differs from κ = 0, which decouples both. It is the hardest cell for SMR, because a large program can draw a cheap start against an expensive SMR one. |
| **EVPI (expected value of perfect information)** | The most that knowing the true cost world in advance could be worth, as a share of expected program cost. |
| **LP / reduced cost** | ReEDS solves a linear program (LP) — a cost-minimization with linear rules. A builder's "reduced cost" is its cost disadvantage at the optimum; zero means it is competitive at the margin. |
| **Credit path** | A declared dollars-per-kW credit for each build year (the rate-design analysis's object). "Schedule" always means a deployment schedule in this notebook, never a credit path. |
| **Demonstration window** | The build years through 2035, in which grant-type federal cost share to first units (the ARDP model) is the assumed vehicle for support above the statutory rate cap; after the window the instrument is the capped credit alone. |
"""

# ============================================================================
# MAIN NOTEBOOK
# ============================================================================

main_cells = [
    md(r"""
    # Main-paper display items — figures and tables with explanations

    **Purpose.** This notebook assembles the main-text display items of the paper
    ("The learning-consistent required subsidy", outline: `z-ethan/paper_outline.md`):
    seven figures and Table 1 — all eight display items. (The Table 2 slot was freed
    2026-08-19 when the Monte Carlo variables table moved to the SI as ST10; the last
    open slot was consumed 2026-08-26 by Figure 5, the cost-of-detection figure.)
    Every panel is the already-generated, checked artifact from the analysis
    notebooks. This notebook does not redraw any of them. Each item carries a
    **source block** that names the notebook and cell that made each panel.
    To change a panel, edit it there and re-run this notebook.

    **How to read this notebook.** Each section has three parts:
    1. A text block that explains the item in plain language.
    2. A code cell that composes the panels and writes `figures/FigN_*.png`.
    3. A printed draft caption, collected into `exports/captions_main.txt`.

    **Language.** We use simplified technical English: short sentences, one
    idea per sentence, active voice. Terms of art are kept, but each one is
    glossed in the table below.

    **What the paper claims, in one paragraph.** Cost assumptions and deployment
    targets are set independently in current practice, and nothing enforces
    their consistency. We couple them: Monte Carlo learning-conditional cost
    worlds feed a capacity mandate in ReEDS, and the mandate's shadow price is
    the subsidy that makes the pair consistent. The minimum public cost of each
    target — the floor — is a flat dollar-per-MW payment at commissioning,
    31–332 B$ (present value, median worlds) across the ambition ladder. The
    subsidy behaves like a bridge (it decays as the fleet learns) in cheap
    worlds, but not in expensive ones. Translated into the US tax credit,
    median worlds need 2.0–2.5 times the current base credit, and the uniform
    percentage credit costs 1.17–1.25 times the floor. Most cost worlds need
    above-cap support in at least one year after the demonstration window, so
    a statutory-capped credit alone buys only the cheap tail of the cost
    distribution; and observation flags a failing world early but never
    calibrates the required credit scale — it tells the government when to
    stop paying, not how much to pay.
    """),
    md(GLOSSARY),
    code(SETUP),

    # ---------------------------------------------------------------- Fig 1
    md(r"""
    ## Figure 1 — Where the ATB 2050 costs sit in learning space

    **What this shows.** The NREL Annual Technology Baseline (ATB) publishes
    nuclear cost trajectories that many models consume as inputs. Our 2030
    anchor convention discards pre-2030 experience by design, so no engine
    path can match an ATB trajectory year by year; the paper therefore scores
    only the **2050 endpoint** — the 2050 cost, and the builds required to
    reach it (Ethan, 08-21/08-24). Two stacked blocks (08-28, Ethan: the
    endpoint maps left the figure — their spillover axis carried little —
    and the share content moved onto these panels): the cost–deployment
    plane for large reactors (a, top) and SMR (b, bottom) — for each amount
    of post-2030 building completed through 2049 (the stock that prices
    2050, per the engine's one-year lag), the 2050 overnight cost that the
    defensible worlds deliver (fan across support-restricted grid worlds,
    every dial varying jointly; dashed lines bound the lowest and highest
    supported world), with the ATB 2050 target marked by its ±\$125 bar at
    its paired Abou-Jaoude deployment (the separate target dot was removed
    08-29 — the bar is the marker). Each block splits fresh-start (legacy fleet
    excluded) vs legacy-fleet-credited rows — the paper-facing labels since
    08-29; the internal stratum names (tiny-base / full-stock) stay in
    code and SI only.

    **How to read it.** A target bar below the fan means fewer than 5% of
    defensible worlds reach that cost at that amount of building; reading
    right along the target's dotted line shows how much building would put
    the target inside the fan. Two reads at the paired deployment (third
    spec, 08-29): the black bar spans the target ±\$125/kW — one rounding
    half-step of the ATB's nearest-\$250 reporting, so a cost inside the
    bar meets the projection at its published precision — labeled with the
    share of that stratum's supported worlds inside the band; the red
    dimension bracket to its left spans the lowest supported cost to the
    upper tolerance bound (target + \$125/kW) and is labeled with the share
    at or below that bound — the paper's **one-sided** feasibility
    criterion (overshoot is success, not misfit), so the bracket label is
    the S1 share for that stratum. The bracket is omitted where that share
    is zero (the large legacy-fleet-credited rows); sub-1% labels keep one
    decimal. Each scenario is scored at its own paired
    deployment — conservative 12, moderate 33, advanced 199 GW — so
    cross-scenario comparisons reflect the ATB's pairing structure, not the
    targets alone.

    **Key results.** The engine is pinned to the ATB's source: run at
    Abou-Jaoude's own parameters and experience basis, it reproduces his
    published SMR OCC tables within report rounding (max error \$500/kW).
    Reaching an ATB 2050 cost at its paired deployment takes a firm-level
    learning rate of 13–19.5% at the central discrete world (fresh-start basis,
    spillover-dependent; T5, scored on the through-2049 stock that prices
    2050 — the 08-24 registration fix) against the source study's own 9.5% —
    the gap
    is the expected anchor-convention premium, and it puts the large targets
    at or above the top of large's sampled support (3–12%); the T5 solve
    carries no tolerance (it requires exactly reaching the published
    target), so those spans are criterion-invariant. On the
    support-restricted grid the feasible shares (\$125 criterion, reported
    split by experience accounting since 08-29 — the 50/50 pooled ranges
    are retired) are 16.3–33.4% for SMR and 0.2–11.4% for large under
    fresh-start accounting, and 3.8–21.5% / zero with the legacy fleet
    credited. For SMR the cheaper scenarios owe their wider reach to the
    much larger deployments the ATB pairs them with; large runs the other
    way — its conservative target is the most reachable. When the
    legacy fleet is credited no large target is reachable at all: zero feasible
    worlds in all three scenarios, and no learning rate up to 30% closes the
    gap at the paired deployment — every large trajectory presumes
    fresh-start accounting (the large legacy-fleet-credited rows, where the target
    sits below the dashed floor and the bracket is omitted, third spec). The
    differences from the source are designed basis conventions (anchor
    convention, experience basis; SN7), not disagreements. This inversion
    uses about 0.79 million sampled worlds per target and zero ReEDS runs.
    """),
    code(r"""
    P.compose(
        [[MC_FIG / "atb_cost_deployment_plane_large.png"],
         [MC_FIG / "atb_cost_deployment_plane_smr.png"]],
        "Fig1_atb_placement.png",
        letters="",  # both sources carry their letters (a = large, b = smr); stacked a over b (08-28)
        center=True,
    )
    P.source_ref(
        (MC_FIG / "atb_cost_deployment_plane_large.png", "mc/atb_parameter_space.ipynb",
         "cell F8 (2050-endpoint reframing 08-24; envelope + share labels + stacking, 08-28)",
         "the closed-form 2050 evaluator over the support-restricted Part-2 grid; "
         "bracket labels = `mc/exports/atb/endpoint_feasible_share.csv` stratum shares, recomputed in-cell"),
        (MC_FIG / "atb_cost_deployment_plane_smr.png", "mc/atb_parameter_space.ipynb",
         "cell F8", "same evaluator, SMR"),
    )

    es = pd.read_csv(MC_EXP / "atb" / "endpoint_feasible_share.csv")
    print(es.to_string(index=False))
    t5 = pd.read_csv(MC_EXP / "atb" / "min_lr_at_aj_deployment.csv")
    tiny = t5[t5["base"] == "tiny"]
    lr_cols = [c for c in t5.columns if c.startswith("min LR")]
    lr_lo, lr_hi = tiny[lr_cols].min().min(), tiny[lr_cols].max().max()
    print(f"\nmin firm-level LR to reach the 2050 cost at the paired deployment "
          f"(tiny base, central world): {lr_lo:.3f}-{lr_hi:.3f}")
    lg, sm = es[es["tech"] == "large"], es[es["tech"] == "smr"]
    assert float(lg["share_support_full"].max()) == 0.0    # the full-stock large claim
    print(f"support-restricted feasible shares (one-sided, $125 criterion; split by "
          f"experience accounting): fresh start smr "
          f"{100*sm['share_support_tiny'].min():.1f}-{100*sm['share_support_tiny'].max():.1f}%, "
          f"large {100*lg['share_support_tiny'].min():.1f}-{100*lg['share_support_tiny'].max():.1f}%; "
          f"legacy credited smr "
          f"{100*sm['share_support_full'].min():.1f}-{100*sm['share_support_full'].max():.1f}%, "
          f"large: 0 in all three scenarios")

    P.caption("Fig 1", '''
    Where the ATB 2050 nuclear costs sit in learning space (endpoint basis: the 2030 anchor
    convention discards pre-2030 experience by design, so only the 2050 cost and the builds
    that reach it are scored). The cost-deployment plane for large reactors (a) and SMR
    (b): the 2050 overnight cost delivered across the sampled learning worlds restricted
    to each technology's learning-rate support, every other input varying jointly (P5-P95
    and P25-P75 fans, median line; dashed lines bound the lowest and highest supported
    world), as a function of cumulative new build, split by experience accounting
    (fresh-start vs legacy-fleet-credited rows). Dotted crosshairs locate each ATB 2050 target
    at its paired deployment - conservative 12, moderate 33, advanced 199 GW - so
    cross-scenario comparisons reflect the ATB's pairing structure, not the targets
    alone. At each paired
    deployment the black bar spans the target +-$125/kW - one rounding half-step of the
    ATB's nearest-$250 reporting, so costs inside the bar meet the projection at its
    published precision - labeled with the share of that stratum's supported worlds
    inside the band; the red bracket to its left spans the lowest supported cost to the
    upper tolerance bound (target + $125/kW), labeled with the share at or below that
    bound - the paper's one-sided feasibility criterion (overshoot is success). The
    bracket is omitted where that share is zero: in the large legacy-fleet-credited
    rows the target sits below the lowest supported world and no world reaches it. The engine
    reproduces the ATB source's published tables under its own parameters and experience
    basis (max error $500/kW); the differences are designed basis conventions. ~0.79M
    sampled worlds per target; no ReEDS runs.
    ''')
    """),

    # ---------------------------------------------------------------- Fig 2
    md(r"""
    ## Figure 2 — The six schedules, and the cost worlds each one implies

    **What this shows.** Panel (a): the six deployment schedules (the "ambition
    ladder"), from 117 GW (EIA) to 400 GW (2025 Executive Order) of new capacity
    by 2050. One schedule per source type: modeled projection, study assumption,
    intergovernmental outlook, consultancy outlook, pledge, policy aspiration.
    Panels (b) and (c): for each schedule, the fan of overnight capital cost
    (OCC) paths that our Monte Carlo produces **conditional on that schedule
    happening** — large reactors in (b), SMR in (c).

    **How to read it.** Each fan is a distribution, never a single projection.
    The band spans the 5th to 95th percentile of 10,000 joint draws; the middle
    line is the median. Each fan begins in 2025 at that draw's first-of-a-kind
    premium and descends into its 2030 anchor cost (a plot-only backcast of the
    FOAK→BOAK approach and the completion of the world's committed construction
    pipeline); the schedules only separate the fans after 2030, when the US
    build programs begin. More ambitious schedules buy more learning, so their
    fans sit lower.

    **Key results.** The median SMR cost in 2050 falls from about \$5,494/kW
    under the least ambitious schedule (EIA, 117 GW) to about \$3,483/kW under
    the most ambitious (EO, 400 GW). Across schedules the 5th–95th percentile
    span runs from roughly \$1,700 to \$8,200/kW. The wide bands are the point:
    a deployment target does not pin down a cost; it pins down a distribution.

    **Discipline to keep in every caption.** These are conditional cost
    trajectories. Each fan answers: "if this schedule happens, what may costs
    do?" It never answers: "what will costs be?"
    """),
    code(r"""
    P.compose(
        [[S3_FIG / "f01_mandate_trajectories.png"],
         [MC_FIG / "occ_fans_large.png"],
         [MC_FIG / "occ_fans_smr.png"]],
        "Fig2_schedules_and_cost_fans.png",
    )
    P.source_ref(
        (S3_FIG / "f01_mandate_trajectories.png", "step3_analysis/step3_analysis.ipynb",
         "cell 10", "`inputs/nuclear_learning/nuclear_cap_trajectory_*.csv` (the mandate files ReEDS reads)"),
        (MC_FIG / "occ_fans_large.png", "mc/mc_cost_trajectories.ipynb", "cell 24",
         "the in-memory MC results (10,000 joint draws per schedule); percentile export: `mc/exports/mc_occ_percentiles_by_schedule.csv`"),
        (MC_FIG / "occ_fans_smr.png", "mc/mc_cost_trajectories.ipynb", "cell 24",
         "same MC results, SMR arrays"),
    )

    # Caption numbers computed from the exported percentiles, so text and data cannot drift.
    occ = pd.read_csv(MC_EXP / "mc_occ_percentiles_by_schedule.csv", header=[0, 1, 2], index_col=0)
    smr50_2050 = occ.loc[2050, ("smr", slice(None), "P50")]
    print(f"SMR P50 OCC in 2050, by schedule token:\n{smr50_2050.round(0).to_string()}")
    lo = occ.loc[2050, (slice(None), slice(None), "P5")].min()
    hi = occ.loc[2050, (slice(None), slice(None), "P95")].max()
    print(f"2050 P5-P95 span across schedules and techs: {lo:,.0f} - {hi:,.0f} $/kW")

    P.caption("Fig 2", f'''
    Deployment schedules and the conditional cost worlds they imply.
    (a) Six new-nuclear deployment schedules for the United States, 117-400 GW by 2050,
    one per provenance class; the paper prices these schedules and does not rank them.
    (b, c) Overnight capital cost fans (5th-95th percentile of 10,000 joint Monte Carlo
    draws; line = median) conditional on each schedule, for large reactors (b) and SMR (c).
    Fans start in 2025 at each draw's backcast first-of-a-kind premium and pass through
    the drawn 2030 anchor cost. Median 2050 SMR cost falls from {smr50_2050.max():,.0f} $/kW (117 GW schedule) to
    {smr50_2050.min():,.0f} $/kW (400 GW schedule). Every fan is conditional on its
    schedule; none is a projection.
    ''')
    """),

    # ---------------------------------------------------------------- Fig 3
    md(r"""
    ## Figure 3 — Why all priced cases commit to a 100%-SMR program, now

    Recomposed 2026-08-26 (Ethan): a 2×2 of single-panel sources; second
    recomposition the same day swapped panels c/d to the optimism-bias sweep
    curves. Third recomposition 2026-08-31 (Ethan, S2 drafting): the 2×2 now
    pairs the two questions with the two stress axes — the **winner** (left
    column) and the **value of waiting** (right column), each at baseline
    against κ (top row) and under optimism stress against m (bottom row).
    Panel (b) is a new combined panel (total EVPI + 2036 switch bound vs κ,
    `tech_comparison.ipynb` cell t8c); the fragmentation histogram moved to
    the SI mixing page (SF6), the majority flip curve joined the paper as
    panel (c), and the standalone bound sweep left the paper (its curve stays
    on the SI flip-curve page, SF8). The four panels are the complete
    commitment case: choose SMR, don't wait — and here is exactly how much
    cost optimism that case tolerates.

    **What this shows.** Before pricing any schedule, we must choose which
    technology carries the program — and whether to commit at all. Left
    column, the winner. Panel (a): the probability that SMR is the cheaper
    program carrier, across schedules and across the κ dependence grid (κ is
    glossed above; each grid cell is a different assumption about how the two
    technologies' uncertainties move together). Panel (c): how much SMR cost
    optimism it takes to flip that majority — the minimum over schedules of
    P(SMR wins), against the SMR optimism multiplier m (the factor by which
    the drawn 2030 SMR anchor cost would understate the truth; m = 1 is the
    elicitation at face value, the T9 stress point is m = 1.5). Right column,
    the value of waiting. Panel (b), at face-value costs: the expected value
    of perfect information (EVPI: the most a decision-maker would pay to know
    the drawn world before committing; solid) and the escape-hatch bound —
    the most that one perfect-information technology switch in 2036 could
    recover (dashed), per schedule, against κ. Panel (d): EVPI under optimism
    stress — the maximum over schedules per dependence anchor, with the
    pre-registered 1% "low value" threshold marked.

    **How to read it.** In panel (a), values above 0.5 mean SMR is the majority
    winner in that cell. In panel (b), both curve families stay below ~0.7%
    of program cost in coherent (κ = 1) worlds and rise as the draws
    decouple: committing now forfeits little where the technologies'
    uncertainties move together. In panel (c), the dots mark the interpolated
    flip points m* where the majority inverts. In panel (d), the hump shape
    is generic: information is valuable only while the winner is genuinely
    contested, so the curve rises as optimism pushes the choice into the
    contested band and falls again once large is the near-certain winner.
    Panels (b) and (d) are perfect-information upper bounds — the true value
    of waiting, or of keeping a switch option, is smaller still.

    **Key results.** SMR is the cheaper carrier with probability 0.82–0.89 under
    the tightest coupling, and stays the majority winner in every primary κ
    cell. The worst cell gives 0.509. That cell is the decoupled-anchor probe
    (see the glossary): the learning rates stay coupled, but each technology
    draws its starting cost independently — not the κ = 0 cell, which
    decouples both.

    At the elicited costs (m = 1), committing now forfeits little in coherent
    worlds: EVPI is 0.57–0.66% of expected program cost at κ = 1, rising to
    2.3–4.6% fully decoupled (about 6.0% at the decoupled-anchor probe — the
    partial decomposition and the probe cells are SF7), and one
    perfect-information 2036 switch recovers at most 0.12–0.66% at κ = 1,
    rising to 0.86–4.6% at κ = 0 (5.88% at the probe — a pre-registered
    failure case, reported as such; SF7). The sweep prices the optimism
    sensitivity of that comfort: at κ = 1 the value of waiting crosses the 1%
    threshold at m ≈ 1.02 and EVPI peaks at 5.3% of program cost at m = 1.25
    (9.8% at m = 1.45 fully decoupled), before decaying as large becomes the
    near-certain winner. These are perfect-information upper bounds; no
    noisy-signal tier was built.

    **Fair-warning results, stated with equal prominence.** When large wins in
    decoupled worlds, its margins can reach about 30% (the margin
    distributions are SF5a). Panel (c) localizes the optimism flip: the
    majority inverts at m* = 1.10 at κ = 1 (1.15–1.16 at κ = 0.5/0), so a
    ~10% SMR anchor error flips the winner in coherent worlds; per-schedule
    flip points span 1.10–1.25 at κ = 1 and 1.16–1.49 at κ = 0 (full curves
    and the boundary table: SF8). Only the no-split claim is optimism-proof:
    the 50/50-split penalty (median 16.7%, now on the SI mixing page SF6)
    rises with m. The commitment is majority-optimal, not certain.
    """),
    code(r"""
    P.compose(
        [[MC_FIG / "tc_robustness_prob.png", MC_FIG / "tc_value_of_waiting.png"],
         [MC_FIG / "obs_majority_vs_m.png", MC_FIG / "obs_evpi_vs_m.png"]],
        "Fig3_technology_choice.png",
        letters="",  # all four single-panel sources carry their final baked letters (a-d)
        center=True,  # panel sizes differ slightly; do not leave a corner blank
    )
    P.source_ref(
        (MC_FIG / "tc_robustness_prob.png", "mc/tech_comparison.ipynb", "cell T5b (added 2026-08-26)",
         "`mc/exports/mc_perdraw.npz` + the κ-grid per-draw exports; table: `mc/exports/tech_comparison/robustness_map.csv`"),
        (MC_FIG / "tc_value_of_waiting.png", "mc/tech_comparison.ipynb", "cell t8c (added 2026-08-31)",
         "`mc/exports/tech_comparison/evpi_total.csv` + `adaptive_value.csv` (diagonal κ cells; the probe cells and the partial decomposition stay in the SI, SF7)"),
        (MC_FIG / "obs_majority_vs_m.png", "mc/ob_sweep.ipynb", "cell S4b (added 2026-08-31; S4's majority panel at paper size)",
         "`mc/exports/ob_sweep/sweep_metrics.csv` + `flip_boundaries.csv` (full flip curves for all four claims stay in the SI, SF8)"),
        (MC_FIG / "obs_evpi_vs_m.png", "mc/ob_sweep.ipynb", "cell S4b (added 2026-08-26; re-lettered c → d in the 2026-08-31 recomposition)",
         "`mc/exports/ob_sweep/sweep_metrics.csv` + `flip_boundaries.csv`"),
    )

    rm = pd.read_csv(MC_EXP / "tech_comparison" / "robustness_map.csv")
    prim = rm[rm["kind"] == "primary"]
    print(f"P(SMR cheaper), primary κ cells: min {rm['P_smr'].min():.3f} "
          f"(incl. probes), comonotone range {prim[prim['kappa_lr'] == 1.0]['P_smr'].min():.2f}"
          f"-{prim[prim['kappa_lr'] == 1.0]['P_smr'].max():.2f}")

    ev = pd.read_csv(MC_EXP / "tech_comparison" / "evpi_total.csv")
    ad = pd.read_csv(MC_EXP / "tech_comparison" / "adaptive_value.csv")
    for name, df, col in [("EVPI", ev, "EVPI_pct"), ("2036 switch bound", ad, "bound_pct")]:
        d = df[df["cell"].str.fullmatch(r"k\d{3}")]
        for cell in ("k100", "k000"):
            v = d[d["cell"] == cell][col]
            print(f"panel b, {name} at {cell}: {v.min():.2f}-{v.max():.2f}% of expected program cost")

    P.caption("Fig 3", '''
    The technology choice, and the cost of committing now. (a) Probability that a 100%-SMR
    program is cheaper than a 100%-large program, across schedules and across the dependence
    grid (kappa = how strongly the two technologies' cost uncertainties move together). SMR
    is the majority winner in every primary cell; the minimum is 0.509 at the
    decoupled-anchor probe (learning rates coupled, 2030 starting costs drawn independently
    — unlike kappa = 0, which decouples both). (b) The value of waiting at face-value
    costs, per schedule against kappa: total EVPI (solid; the most a decision-maker would
    pay to know the drawn world before committing) and the 2036 switch bound (dashed; the
    most one perfect-information technology switch in 2036 could recover). EVPI is
    0.57-0.66% of expected program cost at kappa = 1, rising to 2.3-4.6% at kappa = 0;
    the switch bound is 0.12-0.66%, rising to 0.86-4.6% (probe cells and the partial
    decomposition: SF7). (c, d) The same two questions under optimism stress, against the
    SMR optimism multiplier m (the factor by which the drawn 2030 SMR anchor cost would
    understate the truth). (c) Minimum over schedules of P(SMR wins): the majority inverts
    at m* = 1.10 at kappa = 1 and 1.15-1.16 decoupled; per-schedule flip points span
    1.10-1.25 at kappa = 1 and 1.16-1.49 at kappa = 0 (full curves and the boundary
    table: SF8). (d) EVPI against m (maximum over schedules, 1% threshold marked):
    crossing 1% at m ~ 1.02 and peaking at 5.3% of program cost at m = 1.25 at kappa = 1
    (9.8% at m = 1.45, kappa = 0) — information is worth most where optimism makes the
    winner genuinely contested. Panels b and d are perfect-information upper bounds. The
    commitment is majority-optimal, not certain: large can win by ~30% in decoupled worlds
    (margin distributions: SF5a), and splitting the program 50/50 costs a median 16.7%
    (fragmentation histogram: SF6).
    ''')
    """),

    # ---------------------------------------------------------------- Fig 4
    md(r"""
    ## Figure 4 — The required subsidy is a bridge — in cheap worlds

    Recomposed 2026-08-26 (Ethan): the normalized-decay panel (old 4b,
    `f07`) moved to the SI as SF32 — the decay-class finding is carried by
    the S3 text and quantified in Methods, and the freed weight went to the
    new Figure 5 (the cost of detection).

    **What this shows.** The paper's central object: the mandate's shadow
    price — the yearly rental price, per kW of mandated capacity, that makes
    each schedule worth building (see glossary): the shadow price
    over time for each schedule, in cheap (P5), median (P50), and expensive
    (P95) cost worlds, with the large-reactor comparator overlaid at P50.

    **How to read it.** A "bridge" subsidy should decay: high at first, near
    zero once the fleet has walked down the learning curve. The normalized
    decay curves that test that shape directly are SF32.

    **Key results.**
    - The shadow price is monotone in the cost world: expensive worlds need
      more in every year, with no crossings (visually apparent in the fans;
      quantified in Methods). Mean binding shadow prices run 70–201 (P5),
      314–390 (P50), and 610–698 (P95) in 2024\$/kW-yr; the single peak is 894
      (EO schedule, P95 world, 2031).
    - In cheap worlds the bridge comes down: end-of-horizon shadow prices are
      3–19% of peak. Median worlds are mixed. **In P95 worlds the subsidy does
      not come down: 66–84% of peak in 2050, and no P95 case falls below half
      its peak by 2050** (normalized decay curves: SF32). Under slow learning
      the subsidy is not a bridge but a standing commitment. We give this
      adverse result the same prominence as the decay result.
    - The cross-section of the mean binding shadow price against schedule
      ambition moved to the SI in the 08-20 restructure (SF-ambition, `f06`).
    """),
    code(r"""
    P.compose(
        [[S3_FIG / "f04_dual_fans.png"]],
        "Fig4_shadow_price.png",
        letters="",  # single panel: no letter stamp
    )
    P.source_ref(
        (S3_FIG / "f04_dual_fans.png", "step3_analysis/step3_analysis.ipynb", "cell 18",
         "`step3_checks/exports/duals_by_year.csv` (+ step4 checks for the large100 overlay)"),
    )

    t03 = pd.read_csv(S3_EXP / "t03_dual_summary.csv")
    t04 = pd.read_csv(S3_EXP / "t04_bridge_metrics.csv")
    smr = t03[t03["case"].str.startswith("smr100")]
    for pct in ["p05", "p50", "p95"]:
        sel = smr[smr["case"].str.endswith(pct)]
        print(f"{pct}: mean binding shadow price {sel['mean_binding_dual_2024_kWyr'].min():.0f}"
              f"-{sel['mean_binding_dual_2024_kWyr'].max():.0f} 2024$/kW-yr")
    pk = t03.loc[t03["peak_dual_2024_kWyr"].idxmax()]
    print(f"peak shadow price: {pk['peak_dual_2024_kWyr']:.0f} ({pk['case']}, {int(pk['peak_year'])})")
    p95 = t04[t04["case"].str.startswith("smr100") & t04["case"].str.endswith("p95")]
    n_below = int((p95["first_year_below_half_peak"] <= 2050).sum())
    print(f"p95 end/peak: {p95['end_over_peak'].min():.2f}-{p95['end_over_peak'].max():.2f}; "
          f"p95 cases below half-peak by 2050: {n_below} of {len(p95)}")

    P.caption("Fig 4", f'''
    The required subsidy. The mandate's shadow price — the yearly rental price per kW of
    mandated capacity (2024$) — by solve year, for each schedule in cheap (P5), median
    (P50), and expensive (P95) cost worlds; large-reactor P50 comparators overlaid.
    Shadow prices rise with the cost world in every year, with no crossings, peaking at
    {pk['peak_dual_2024_kWyr']:.0f} $/kW-yr ({pk['case']}, {int(pk['peak_year'])}). In
    cheap worlds the shadow price decays to 3-19% of its peak by 2050; no P95 case
    reaches half its peak — under slow learning the subsidy is a standing commitment,
    not a bridge (normalized decay curves: SF32).
    ''')
    """),

    # ---------------------------------------------------------------- Fig 5
    md(r"""
    ## Figure 5 — What observation buys, and what it cannot

    New main figure 2026-08-26 (Ethan). **Recomposed 2026-09-02 (Ethan,
    outline fourteenth pass): the detection panel cannot stand alone** —
    presented by itself it invites the inference that observation can steer
    the policy level, and the cost-of-information analysis
    (`z-ethan/rate_design/`, Part A, audited and verdicted INCLUDE) shows it
    cannot. The figure is now two panels. Panel (a): the bridge-detection
    result (S3-3) as money — how much subsidy is committed before a
    spending cap flags a world whose total bill will exceed that cap.
    Panel (b): the calibration limit — the same completed-unit observations
    never pin down the required credit scale. The pair reads: observation
    tells the government when to stop paying, not how much to pay.

    **What panel (a) shows.** The observer watches noisy realized project costs
    and the government's own outlay ledger — the subsidy already paid,
    which the paying government knows exactly, read every year (the
    spend-aware standard, a 2026-08-25 amendment to the pre-registered
    stage-3 design). Each candidate cost world's total bill is scored as
    the sunk spend plus that world's remaining payments; the alarm fires
    when the weighted share of candidate worlds whose total stays under the
    cap falls below a conformal bar set to a 5% false-alarm budget. One
    panel per schedule. The y-axis is the spending cap (2024\$B), over a
    grid from the cap that only 25% of prior worlds stay under, up to
    1.75–2.2 times the median-world (P50) bill; the x-axis is the present value
    committed at detection. Bands span the exceeding worlds and observation
    histories at the middle noise level (30% per-project scatter plus a
    shared 10% yearly shock): light = p05–p95, dark = interquartile, line =
    median. The dotted diagonal is spend = cap.

    **How to read panel (a).** Under the spend-aware standard, every world that
    truly exceeds the cap is detected — at the latest in the year spend
    crosses the cap — and a world that never exceeds the cap never spends
    up to it, so the ledger backstop adds no false alarms. The question the
    panel answers is therefore not *whether* the alarm fires but *how much
    is committed first*: the gap between the light band's right edge and
    the diagonal is the observer's margin over the worst case.

    **What panel (b) shows.** An observer with the model's own cost-world
    ensemble updates on the same noisy completed-unit costs and tracks the
    90% confidence interval on the support level the program needs. The
    y-axis is that interval's width in **statutory ITC points**: the
    credit-scale interval (the multiple of the reference credit path that
    covers the per-world requirement) converted at the reference path's
    outlay-weighted average rate — an exact one-constant-per-schedule
    conversion, so the registered design tolerance is five points in every
    panel (dashed). A width of 40 means the government cannot tell a
    45% credit from an 85% one. One panel per schedule on its own linear
    spend axis (2024\$B; one column per schedule, top row), three declared
    noise levels, the pre-observation prior at zero spend.
    No schedule approaches the target at any noise level; the final
    mid-noise widths are 24–39 points. Only aj and eo even plateau by 2050
    under the registered ≤5%-per-observation labeling rule; the other four
    are still declining at the horizon, so their curves say "not within the
    program horizon", not "never". The bottom row shows the learning-rate
    interval on the same spend axes (points, no target): it narrows
    steadily, from 11.7 to 4.3–9.3 points — the coarse quantity is learned
    while the design quantity is not (the same grid in scale units: SF39).
    The learning-rate width is set by the shared yearly shock: a 10%
    industry-wide shock over ten observation years and about five
    doublings bounds the slope estimate at roughly 4–5 points (the OLS
    limit), and more units per year do not help — only more years and
    more doublings do. Disclosures carried: the
    light-noise robustness read sits where the effective sample thins (a
    bias against the finding); the v1 sweep is the frozen input (restated,
    not recomputed; audit record in `rate_design/status.md`).

    **Key results** (computed in the cell below from `b17`/`b18` and `u30`):
    - Median committed spend at detection sits far below the cap — 4 to 15
      times below at a cap of 1.5x the median-world (P50) bill, where it is
      4.0 (EIA) to 32.2 (EO) B2024\$ — 5–24% of the failing world's total
      bill.
    - The p95 committed spend stays at or below the cap at every cap on
      every schedule (the one-year-accrual bound; the ledger is read
      annually).
    - The held-out false-alarm rate stays within the 7.5% gate at every
      cap.
    - The required-credit interval never reaches the five-point design
      target: after the whole program it is still 24–39 statutory points
      wide at mid noise (14–25 light, 36–52 heavy; 87–151 before any
      unit completes), 4.8–7.7x the target, and only aj/eo plateau
      (2.9%/1.6% decline per observation at the horizon). The
      learning-rate CI narrows from 11.7 to 4.3–9.3 points (SF39/ST16).

    **Carried caveats (mandatory).** The observer knows the model's own
    ensemble and the noise model — an upper bound on real detectability.
    The ledger it reads is the perfectly-informed floor payment stream
    (shadow price times capacity); under a real instrument, outlays would
    track costs rather than the exact model prices, so the ledger enters
    the update additively only (never to tell worlds apart). Framed as
    information, never as a recommendation.
    """),
    code(r"""
    P.compose(
        [[BD_FIG / "d13_paid_by_cap_noisy.png"],
         [RD_FIG / "w37_ci_rate_points_paper.png"]],
        "Fig5_cost_of_detection.png",
        letters="ab",
        center=True,
    )
    P.source_ref(
        (BD_FIG / "d13_paid_by_cap_noisy.png", "bridge_detection/bridge_detection_stage3.ipynb",
         "figure cells", "`b17_exceedance_noisy.csv` (spend-aware standard, 2026-08-25 amendment; "
         "spec: `bridge_detection/methods.md` section 6)"),
        (RD_FIG / "w37_ci_rate_points_paper.png", "rate_design/rate_design_v2.ipynb",
         "S7 w37 cell (the w36/w20 grid with the credit-scale row re-denominated in "
         "statutory rate points; Ethan's reading review 2026-09-02)",
         "`u32_ci_rate_points.csv` (= u10 widths x the reference path's outlay-weighted "
         "average rate) + `u30_part_a_restated.csv` (the frozen v1 sweep restated with every "
         "audit repair; registration: `rate_design/methods.md` v2/v2.1, verdict INCLUDE in "
         "`u91_verdict.csv`)"),
    )

    b17 = pd.read_csv(BD_EXP / "b17_exceedance_noisy.csv")
    mid = b17[(b17["sigma"] == 0.3) & (b17["tau"] == 0.1)]
    m15 = mid[mid["mult"] == 1.5].set_index("schedule")
    print("median paid at the 1.5x cap (2024$B): "
          + ", ".join(f"{s} {m15.loc[s, 'paid_at_det_p50_2024B']:.1f}" for s in m15.index))
    sh_lo, sh_hi = m15["median_share_paid"].min(), m15["median_share_paid"].max()
    print(f"median share of the failing world's bill paid at detection (1.5x cap): "
          f"{sh_lo:.2f}-{sh_hi:.2f}")
    worst = (mid["paid_at_det_p95_2024B"] / mid["X_2024B"]).groupby(mid["schedule"]).max()
    print("p95 paid / cap, per-schedule worst point over the grid: "
          + ", ".join(f"{s} {v:.2f}" for s, v in worst.items()))
    fpr_max = mid["fpr_holdout"].max()
    print(f"held-out false-alarm rate: max {fpr_max:.3f} (gate 0.075); "
          f"share of exceeding worlds detected: {mid['share_detected'].min():.1f} "
          f"everywhere (by construction)")

    b18 = pd.read_csv(BD_EXP / "b18_cost_of_waiting_noisy.csv")
    m18d = b18[(b18["sigma"] == 0.3) & (b18["tau"] == 0.1)].set_index("schedule")
    pd_lo = m18d["c2_150_median_paid_at_det_2024B"].min()
    pd_hi = m18d["c2_150_median_paid_at_det_2024B"].max()
    assert float(m18d["c2_150_share_never_detected"].max()) == 0.0

    u30 = pd.read_csv(RD_EXP / "u30_part_a_restated.csv").set_index("schedule")
    assert not u30["crosses_band5"].any()
    ratio_lo, ratio_hi = u30["final_over_tgt"].min(), u30["final_over_tgt"].max()
    plateau = "/".join(u30.index[u30["label"] == "asymptote"])
    lr0 = u30["prior_lr_w_pts"].max()
    lr_lo, lr_hi = u30["final_lr_w_pts"].min(), u30["final_lr_w_pts"].max()
    print(f"credit-scale CI never crosses the design target (0/6 schedules, all noise "
          f"levels); final mid-noise width {ratio_lo:.1f}-{ratio_hi:.1f}x the target; "
          f"plateau label: {plateau} only")
    print(f"learning-rate CI narrows {lr0:.1f} -> {lr_lo:.1f}-{lr_hi:.1f} points (5-95)")

    u32 = pd.read_csv(RD_EXP / "u32_ci_rate_points.csv")
    fin32 = u32[u32["k"] == u32.groupby(["schedule", "sigma"])["k"].transform("max")]
    def _rng(sig):
        f = fin32[fin32["sigma"] == sig]["width_pts"]
        return f.min(), f.max()
    pm_lo, pm_hi = _rng(0.30); pl_lo, pl_hi = _rng(0.15); ph_lo, ph_hi = _rng(0.50)
    pri32 = u32[(u32["k"] == 0) & (u32["sigma"] == 0.30)]["width_pts"]
    assert pm_hi < 60 and pm_lo > 5, (pm_lo, pm_hi)
    print(f"required-credit 90% interval width, statutory points: prior {pri32.min():.0f}-{pri32.max():.0f}; "
          f"final mid {pm_lo:.0f}-{pm_hi:.0f}, light {pl_lo:.0f}-{pl_hi:.0f}, heavy {ph_lo:.0f}-{ph_hi:.0f}; target 5")

    P.caption("Fig 5", f'''
    What observation buys, and what it cannot. (a) The cost of learning that the bridge
    is failing: present value of subsidy committed when a spending cap flags a world
    whose total bill will exceed the cap, against the cap itself (both in 2024$B), one
    panel per schedule; light band p05-p95, dark band interquartile, line median, across
    exceeding worlds and observation histories at the middle noise level (30%
    per-project scatter + a shared 10% industry-wide yearly shock); dotted diagonal:
    spend = cap. The observer holds a conformal 5% false-alarm budget over the model's
    own cost-world ensemble and also reads the outlay ledger every year, so detection is
    guaranteed no later than the year spend crosses the cap: the p95 committed spend
    stays at or below the cap everywhere (per-schedule worst points
    {worst.min():.2f}-{worst.max():.2f}x), and the median runs far below it — at a cap
    of 1.5x the median-world (P50) bill, a median of {pd_lo:.1f}-{pd_hi:.1f} B$
    ({sh_lo*100:.0f}-{sh_hi*100:.0f}% of the failing world's total bill) is committed
    before the alarm. Held-out false alarms stay within the budget (max {fpr_max:.3f}
    against the 0.075 gate). (b) The calibration limit: how well the same observations
    pin down the support level the program needs. Width of the 90% confidence interval
    on the average statutory rate the credit path must carry (the credit-scale interval
    converted at the reference path's outlay-weighted average rate; top row) and on the
    SMR learning rate (bottom row, points), against cumulative committed spend (2024$B),
    one column per schedule, three noise levels (thick with markers = middle); the point
    at zero spend is the range before any unit completes; dashed line = the registered
    design tolerance of five statutory points (top row only). No schedule approaches the target at any noise level: after the whole
    program the interval is still {pm_lo:.0f}-{pm_hi:.0f} points wide at the middle
    noise level ({pl_lo:.0f}-{pl_hi:.0f} light, {ph_lo:.0f}-{ph_hi:.0f} heavy;
    {pri32.min():.0f}-{pri32.max():.0f} before observation), {ratio_lo:.1f}-{ratio_hi:.1f}x
    the target, and only {plateau} plateau by 2050 under the registered rule (the others
    are still declining at the horizon) — while the learning-rate interval narrows from
    {lr0:.1f} to {lr_lo:.1f}-{lr_hi:.1f} points: the coarse quantity is learned, the
    design quantity is not (audit grid in scale units: SF39). Together: observation tells the government when to stop
    paying, not how much to pay. Both observers know the ensemble and the noise model —
    upper bounds on real learnability; information, not a recommendation.
    ''')
    """),

    # ---------------------------------------------------------------- Fig 6
    md(r"""
    ## Figure 6 — The statutory wall: what caps can and cannot buy

    Recomposed 2026-08-24 (option B), renumbered 2026-08-26, panel (a)
    swapped + menu reframing 2026-08-31 (plan v10.42/v10.43).
    **Recomposed again 2026-09-02 (Ethan, outline fourteenth pass):** the
    budget menu (k02) is superseded by the statutory-cap feasibility mask
    and moves to SF35 (ST13 stays its table); the uniform-ITC-vs-ambition
    panel (f17) moves to SF36 — the instrument premium over the floor is
    modest in practice (1.17–1.25x at p50), so that panel re-plots the
    Fig 4 bill shape in rate units. Panels (a) and (b) now come from the
    zero-run declining-credit analysis (`z-ethan/rate_design/` v2.1; three
    fresh-context audits adjudicated; Part B verdict INCLUDE AS REPAIRED
    in `u91_verdict.csv`). Panel (c) — the rate–deployment cliff — is
    unchanged.

    **What this shows.** The shadow price is a model price. This figure
    translates it into statutory credit terms and shows where the
    translation hits a wall. Panels (a) and (b) are the legended paper
    variants (w34/w35, emitted 2026-09-02 after Ethan's legend review —
    the analysis originals w30/w32 explained their encodings in notebook
    markdown, which a composed figure does not carry). Panel (a):
    **per-world required statutory rates** — for each schedule and build
    year, the credit rate on the world's own build cost that just covers
    its cushioned requirement, fanned across the 10,000 cost worlds
    (median solid; interquartile and p5–p95 bands; thin dotted lines =
    the ±20% certificate-band medians; grey dashed = the reference credit
    path, the model-certified headline; the grey band on aj/mck/eo = the
    run-certified minimal-rate bracket, one to five rate points below the
    reference — the delivery-minimal rate lies inside it). The horizontal
    red lines are the statutory ceilings: dotted 0.50 (today's stackable
    maximum: 30% base + 10% energy community + 10% domestic content) and
    dash-dot 0.60 (the registered outer bound). Red triangles mark the
    three censored cells (cop28 2050, eo 2047/2050): the source rates
    there exceed 100% of basis, so the drawn values are lower bounds.
    The full legend is in the figure.
    Panel (b): the **credit-feasibility mask and the demonstration tier**
    — left, the share of worlds above the cap by build year (solid 60%,
    dotted 50%; the vertical dashed line is the demonstration-window edge,
    2035); right, the demonstration funding requirement in 2024\$B (the
    fixed-basis PV of above-cap need inside the window; median solid, p95
    faint; eia not applicable — its first build year is 2038, so the
    window contains no eia year). Panel (c): the **rate–deployment cliff**
    (j06) — new-nuclear 2050 capacity against the credit rate, combining
    the flat-credit anchors, the 24-run minus-probe ladders, and the
    headline schedule points; new nuclear equals SMR capacity exactly
    because large-reactor additions are credit-invariant in every run
    (the zero-substitution result).

    **How to read it.** In panel (a), wherever a fan sits above a ceiling
    line, that share of worlds cannot be served by a statutory credit at
    that cap in that year. Before 2035 the demonstration window absorbs
    the excess as grant cost share; after it, above-cap need means the
    capped credit alone fails that world. In panel (b), the post-window
    share above the cap is the not-credit-feasible share — the mask's key
    output. In panel (c), the shaded band is the current 48E credit range
    (30–50%): the entire current-law range sits in the flat tail of the
    response, and the cliff starts a few points past its right edge.

    **Key results** (computed in the cell below from `u50`/`u51`/`u52`).
    Most cost worlds need above-cap support in at least one post-window
    year, in every schedule: the post-window infeasible share is
    ~0.27–0.90 at the 60% cap and ~0.56–1.00 at the 50% statutory
    maximum, quoted ONLY as cap x certificate-band ranges. The
    demonstration tier is priced: base-case medians at the 60% cap run
    \$0.85B (aj) to \$23.5B (eo), p95 \$114B (base band; the band values
    are larger — ST14). The message: a statutory-capped credit alone
    reaches only the cheap tail of the cost distribution, and observation
    cannot rescue this by fine-tuning (Fig 5b).

    **Mandatory framings (from the adjudicated audit record — never quote
    past them).** The mask is a range table, never a single number (the
    ±20% certificate band moves the shares); it is presented at both caps
    because the cap choice moves the eia/aj shares 20–23 points
    (registered kill KB2 fired — a cap-sensitivity table, not a
    single-cap exhibit). cop28's demonstration framing is killed
    (registered kill KB1: its above-cap need persists past the window at
    the low band end — its gap is a band range with no early-concentration
    story). eia is N/A for the demonstration framing (empty window), not
    satisfied by it. The p95 fan edge is clamp-pinned in 31 of 55
    schedule-year cells (there the drawn p95 is the top anchor's own
    rate, not a distribution quantile); the outlay calibration carries a
    ±5% systematic. Paper text is written from the `u91` dispositions,
    never from exhibit markdown.

    **The cliff (panel c) and the delivery validation (SI).** The response
    to the rate is a cliff, not a slope: zero SMR at a flat 30% credit,
    9.8 GW at 50% — the entire current-law 48E range buys almost nothing —
    against 27–381 GW at the schedule rates. The 24-run minus probe brackets
    the delivery-minimal rate within five points below the headline, and
    below the boundary the learning feed-back amplifies the shortfall
    instead of cushioning it. The closed-loop delivery validation stays in
    the SI: the credit alone reproduces the mandated deployment in 5 of 6
    median worlds (EIA partial: a delayed start under myopic lagged costs,
    recovering past its trajectory by 2050) and over-delivers (1.3–2.7x),
    never under (SF23, ST9, SN6). The budget menu and the
    uniform-ITC-vs-floor panel live on as SF35/SF36 with their tables
    (ST13, ST6); the required-rate-by-solve-year detail is SF33/ST6.
    """),
    code(r"""
    P.compose(
        [[RD_FIG / "w34_rate_fans_paper.png"],
         [RD_FIG / "w35_mask_gap_paper.png", ITCFBM_FIG / "j06_new_nuclear_cliff.png"]],
        "Fig6_required_itc_and_menu.png",
        letters="abc",
        center=True,  # row widths differ; do not leave a blank corner
    )
    P.source_ref(
        (RD_FIG / "w34_rate_fans_paper.png", "rate_design/rate_design_v2.ipynb",
         "S7 paper-variant cell (legended twin of the w30 audit artifact)",
         "`u50_requirement_fans.csv` (certificate: 18 exact anchors G1 + stage-2 +-20% band + "
         "r03 cushion; registration: `rate_design/methods.md` v2/v2.1)"),
        (RD_FIG / "w35_mask_gap_paper.png", "rate_design/rate_design_v2.ipynb",
         "S7 paper-variant cell (legended twin of the w32 audit artifact)",
         "`u51_feasibility_mask.csv` + `u52_demonstration_gap.csv` (kills KB1/KB2 adjudicated; "
         "verdicts + dispositions in `u91_verdict.csv`)"),
        (ITCFBM_FIG / "j06_new_nuclear_cliff.png", "itcfbm_analysis/itcfbm_analysis.ipynb",
         "cell j06cd001", "`r04_rate_deployment.csv` (statutory basis, new nuclear only; "
         "promoted 2026-08-24)"),
    )

    u50 = pd.read_csv(RD_EXP / "u50_requirement_fans.csv")
    br = u50[(u50["band"] == "base") & (u50["quantity"] == "rate")]
    cen = br[br["censored"] == True]  # noqa: E712 — literal bool column
    cen_txt = ", ".join(f"{r.schedule} {int(r.year)}" for r in cen.itertuples())
    n_clamp, n_cells = int((br["p95_clamp_pinned"] == True).sum()), len(br)  # noqa: E712
    assert len(cen) == 3 and n_cells == 55
    print(f"censored cells (source rates exceed 100% of basis; drawn values are lower "
          f"bounds): {cen_txt}")
    print(f"p95 clamp-pinned cells: {n_clamp}/{n_cells}")

    u51 = pd.read_csv(RD_EXP / "u51_feasibility_mask.csv")
    pw = u51[(u51["kind"] == "per_world") & (u51["window"] == "w2035")]
    r60 = pw[pw["cap"] == 0.6]["share_not_credit_feasible"]
    r50 = pw[pw["cap"] == 0.5]["share_not_credit_feasible"]
    print(f"post-window infeasible share (quoted ONLY as cap x band ranges): "
          f"60% cap {r60.min():.2f}-{r60.max():.2f}; 50% cap {r50.min():.2f}-{r50.max():.2f}")

    u52 = pd.read_csv(RD_EXP / "u52_demonstration_gap.csv")
    g = u52[(u52["band"] == "base") & (u52["cap"] == 0.6)
            & (u52["window"] == "w2035") & (u52["window_applicable"] == True)]  # noqa: E712
    gk = g[g["schedule"] != "cop28"]  # cop28's demonstration framing is killed (KB1)
    gmin, gmax = gk["gap_p50_B"].min(), gk["gap_p50_B"].max()
    gcop = float(g[g["schedule"] == "cop28"]["gap_p50_B"].iloc[0])
    g95 = g["gap_p95_B"].max()
    print(f"demonstration gap medians (base band, 60% cap, window <= 2035): "
          + ", ".join(f"{r.schedule} {r.gap_p50_B:.1f}" for r in g.itertuples())
          + f" B$; p95 max {g95:.0f} B$ (base band; band ends larger -> ST14)")

    P.caption("Fig 6", f'''
    The statutory wall: what caps can and cannot buy. (a) Required statutory credit
    rate on each world's own build cost, per schedule and build year, fanned across
    the 10,000 cost worlds (median solid; interquartile and p5-p95 bands; thin dotted
    = the +-20% certificate-band medians; grey dashed = the reference credit path,
    the model-certified headline; grey band on aj/mck/eo = the run-certified
    minimal-rate bracket, one to five rate points below the reference); dotted red
    horizontal line = the 0.50 stackable statutory maximum (30% base + 10% energy
    community + 10% domestic content), dash-dot = the 0.60 registered outer bound.
    Red triangles mark the three censored cells ({cen_txt}):
    their source rates exceed 100% of basis, so the drawn values are lower bounds; the
    p95 fan edge is clamp-pinned in {n_clamp} of {n_cells} schedule-year cells (the
    drawn p95 is then the top anchor's own rate, not a distribution quantile).
    (b) Left: share of worlds above the cap by build year (solid 60%, dotted 50%;
    vertical dashed line = the demonstration-window edge, 2035 — inside the window,
    grant-type federal cost share to first units is the assumed vehicle for above-cap
    need). Right: the demonstration funding requirement — the fixed-basis present
    value of above-cap need inside the window (median solid, p95 faint; eia not
    applicable: its first build year is 2038, so the window contains no eia year).
    Post-window, the share above the cap is the not-credit-feasible share:
    {r60.min():.2f}-{r60.max():.2f} at the 60% cap and {r50.min():.2f}-{r50.max():.2f}
    at the 50% cap, across schedules and the +-20% certificate band — quoted only as
    ranges. The cap choice alone moves the eia/aj shares 20-23 points (the mask is a
    cap-sensitivity table), and cop28's above-cap need persists past the window at the
    low band end, so its demonstration framing is withdrawn (its median,
    {gcop:.1f} B$, is quoted only as a band range). Where the framing stands, the
    demonstration-gap medians at the 60% cap run {gmin:.2f}-{gmax:.1f} B$ (base band;
    p95 to {g95:.0f} B$, larger at the band ends — ST14); the outlay calibration
    carries a +-5% systematic. A statutory-capped credit alone reaches only the cheap
    tail of the cost distribution, in every schedule — and observation cannot rescue
    this by fine-tuning the scale (Fig 5b). (c) New-nuclear deployment against the
    credit rate, on the model credit convention; shaded band = the 48E range (30-50%).
    New nuclear equals SMR capacity: large-reactor additions are credit-invariant in
    every run (the zero-substitution result). Black squares: flat credits — zero at
    30%, 9.8 GW at 50%; the entire current-law range buys almost nothing. Colored
    curves: the minus-probe ladders (headline-0.15 ... -0.01, then the headline) with
    draw-calibrated endogenous learning (solid) and learning frozen (faint dashed).
    The response is a cliff, not a slope: five rate points below the headline,
    delivery fails in every world, and below the boundary learning amplifies the
    shortfall while above it learning amplifies delivery. The budget menu and the
    uniform-ITC-vs-floor comparison live in SF35/SF36 (tables ST13/ST6); required-rate
    detail by solve year: SF33.
    ''')
    """),

    # ---------------------------------------------------------------- Fig 7
    md(r"""
    ## Figure 7 — Robustness across market worlds

    **What this shows.** Do the headline results depend on our base market
    assumptions? We re-ran the 18 SMR percentile cases under six market
    worlds (gas price high/low, high-electrification demand, renewable costs
    cheap/dear, and a transmission-limited world): 108 runs, all output checks
    green. Panel (a): for every case × market world, does the bridge shape
    survive? Panel (b): the shadow-price paths for the smallest and largest
    schedules, overlaid across market worlds. Panel (c): the large-reactor
    comparator against the SMR program, by cost-world percentile (base market
    world only). The two threshold results of S3 — the statutory wall and the
    spending-cap alarm — are transferred to the same six alternative market
    worlds in `market_transfer/` (ST18, SF40–SF41); the caption carries the
    six-world envelopes, the base ranges stay in the Fig 6b and Fig 5a captions.

    **How to read it.** Panel (a) is pass/fail: a cell "survives" when the case
    keeps its decay class **or** its end-over-peak ratio moves by at most 0.15
    (the ratified tolerance for classifier-edge flips: the class is stable in
    105 of 108 cells, the ratio moves ≤ 0.15 in 96 of 108, and the three class
    flips all sit within 0.02 of the 0.5 decay boundary).
    In panel (b), the spread across colored lines is what market conditions do
    to the subsidy level. Panel (c) compares technologies at the same
    percentile.

    **Key results.**
    - The bridge shape survives in **108 of 108** cells, and no market world
      unbinds a mandate. The expensive-world non-decay is generic, not a
      base-world artifact.
    - The fiscal ordering of the six schedules survives (Kendall τ ≥ 0.867 in
      every cell against base, mean 0.993).
    - Only the level moves, and it moves as economics predicts: the median
      shadow price moves −27% to +18% across the six market worlds (the
      six-number list is in SF22/ST17).
    - The level shift passes straight into the required tax-credit rate (the
      conversion is linear in the shadow price for a fixed case-year), so the
      statutory wall of S3-4 is a base-market-world number — across the six
      alternative worlds the 0.60-ceiling share runs from none of the cost
      worlds to all of them (the band-qualified high-gas and low-gas statements
      are in the SF40 caption; ST18). The spending-cap alarm's
      committed spend moves with the bill scale; its share of the failing
      world's bill barely moves (ST18, SF41).
    - The large-reactor premium is not a constant. Large needs 1.4–3.5× the
      SMR shadow price in cheap worlds, 1.23–1.36× at the median — but at P95
      the two technologies reach parity (0.95–1.02×): in expensive worlds both
      need the same subsidy.
    """),
    code(r"""
    P.compose(
        [[S4_FIG / "g02_shape_survival_matrix.png", S4_FIG / "g03_dual_overlays.png"],
         [S3_FIG / "f15_large_band.png"]],
        "Fig7_robustness.png",
    )
    P.source_ref(
        (S4_FIG / "g02_shape_survival_matrix.png", "step4_analysis/step4_analysis.ipynb", "cell 11",
         "`step4_analysis/exports/s02_shape_survival.csv`"),
        (S4_FIG / "g03_dual_overlays.png", "step4_analysis/step4_analysis.ipynb", "cell 12",
         "step3+step4 checks `duals_by_year.csv` (eia/eo x p05/p50/p95 x base + six market worlds)"),
        (S3_FIG / "f15_large_band.png", "step3_analysis/step3_analysis.ipynb", "cell 23",
         "combined duals, large100 vs smr100 shared binding years; table: `t15_large_ratio.csv`"),
    )

    s02 = pd.read_csv(S4_EXP / "s02_shape_survival.csv")
    surv = s02[s02["survives"].notna()]
    n_surv = int((surv["survives"] == "yes").sum())
    print(f"shape survival: {n_surv}/{len(surv)}")
    s03 = pd.read_csv(S4_EXP / "s03_ranking_preservation.csv")
    fis = s03[(s03["metric"] == "disc_program_bill") & (s03["sens"] != "base")]
    print(f"Kendall tau vs base (fiscal-bill metric, 18 non-base cells): "
          f"min {fis['kendall_tau_vs_base'].min():.3f}, "
          f"mean {fis['kendall_tau_vs_base'].mean():.3f}")
    t15 = pd.read_csv(S3_EXP / "t15_large_ratio.csv")
    print(t15.groupby("pct")["ratio_large_over_smr"].agg(["min", "max"]).round(2).to_string())

    # the market-world transfer of the S3 threshold results (market_transfer, v04/v06)
    v04 = pd.read_csv(MT_EXP / "v04_mask_range_table.csv")
    v04 = v04[v04["window"] == "w2035"]
    assert set(v04["world"]) == {"base", "gaslo", "gashi", "demhi", "relo", "rehi", "translim"}
    env = (v04[v04["world"] != "base"].groupby("cap")
           .agg(base_lo=("base_lo", "min"), base_hi=("base_hi", "max"), lo=("lo", "min"), hi=("hi", "max"),
                mid_lo=("mid", "min"), mid_hi=("mid", "max")))
    assert set(env.index) == {0.5, 0.6}
    # the base ranges must equal the S3-4 / rate_design ones (u91 mask-range 0.27-0.90 at 0.60)
    assert abs(env.loc[0.6, "base_lo"] - 0.265) < 5e-4 and abs(env.loc[0.6, "base_hi"] - 0.9045) < 5e-4
    v06 = pd.read_csv(MT_EXP / "v06_detection_summary.csv")
    own = v06[v06["normalization"] == "own_p50"]
    assert len(own) == 6 and (own["n_worlds_clean"] >= 1).all()
    n_excl = int((own["n_worlds_in_grid"] - own["n_worlds_clean"]).sum())
    _wname = {"gaslo": "low gas", "gashi": "high gas", "demhi": "high demand", "relo": "cheap renewables",
              "rehi": "dear renewables", "translim": "transmission-limited"}
    excl = sorted({f"{_wname[w]}/{ab}" for ab, ws in zip(own["schedule"], own["worlds_excluded"].fillna(""))
                   for w in ws.split(";") if w})
    e60, e50 = env.loc[0.6], env.loc[0.5]
    print(f"wall envelope 0.60: base {e60['base_lo']:.2f}-{e60['base_hi']:.2f}, "
          f"worlds {e60['lo']:.2f}-{e60['hi']:.2f}; 0.50: base {e50['base_lo']:.2f}-"
          f"{e50['base_hi']:.2f}, worlds {e50['lo']:.2f}-{e50['hi']:.2f}")

    P.caption("Fig 7", f'''
    Robustness across market worlds (108 sensitivity runs: the 18 SMR percentile cases x six
    market worlds). (a) Bridge-shape survival matrix: the shape survives in {n_surv} of
    {len(surv)} cells — the expensive-world non-decay is generic. (b) Shadow-price overlays
    for the smallest and largest schedules across market worlds: only the level moves, in
    the direction economics predicts (median -27% to +18%). (c) Large-reactor vs SMR shadow
    prices by percentile, base market world: the large premium is 1.4-3.5x in cheap worlds
    and 1.23-1.36x at the median, but the two technologies reach parity (0.95-1.02x) in
    expensive worlds. Transfer of the S3 threshold results
    (ST18; SF40-SF41), quoted over the six alternative market worlds with the base ranges in
    the Fig 6b and Fig 5a captions: the share of cost worlds needing an above-ceiling credit
    rate in a post-window build year (build years after 2035) spans {e60['lo']:.2f}-{e60['hi']:.2f}
    at the 0.60 ceiling (band centre {e60['mid_lo']:.2f}-{e60['mid_hi']:.2f}) and {e50['lo']:.2f}-{e50['hi']:.2f}
    at 0.50 (band centre {e50['mid_lo']:.2f}-{e50['mid_hi']:.2f}); the median spend committed
    before the spending-cap alarm (1.5x the world's own median-world (P50) bill, middle noise)
    spans {own['worlds_paid_p50_B_min'].min():.1f}-{own['worlds_paid_p50_B_max'].max():.1f} B$
    ({own['worlds_share_paid_min'].min():.0%}-{own['worlds_share_paid_max'].max():.0%} of the
    failing world's bill; starting probability of exceedance
    {own['worlds_prior_min'].min():.2f}-{own['worlds_prior_max'].max():.2f}), excluding the
    {n_excl} world-schedule cells whose bill interpolation fails its +/-20% test
    ({", ".join(excl) if excl else "none"}; range-only, ST18). Ranges are min-max over
    schedules, certificate-band ends, and worlds; SMR program throughout.
    ''')
    """),

    # ---------------------------------------------------------------- Table 1
    md(r"""
    ## Table 1 — The six deployment schedules

    **What this table shows.** One row for each deployment schedule. The
    columns give the source, the source type, the 2050 target, and the
    mandate that ReEDS enforces. The glossary defines "schedule" and
    "mandate". This table replaces the case-level results table
    (2026-08-19); the full case-level tables are in the SI (ST5, ST6).

    **Source type.** Each schedule comes from a different type of source.
    We call this type its "provenance class". The six classes are: a
    modeled projection, a study assumption, an intergovernmental outlook,
    a consultancy outlook, a pledge, and a policy aspiration. The paper
    prices one schedule from each class. The paper does not rank the
    schedules, and it gives them no probability weights.

    **The two capacity columns.** `fleet_target_2050_GW` is the source's
    target for the total US nuclear fleet in 2050. `new_capacity_2050_GW`
    is the new capacity that the SMR-program mandate enforces by 2050.
    This mandate counts post-2030 builds only (the "additions basis").
    Three things make the gap between the two columns: the existing 2024
    fleet (97 GW), the 3-GW index rounding correction, and any pre-2031
    schedule growth, which the post-2030 mandate does not count (see
    Methods).

    **The large-reactor comparator.** `large_comparator_2050_GW` is the
    2050 mandate of the large-reactor comparator runs. These mandates
    count the whole fleet (the "fleet-inclusive basis"), because the
    existing large fleet can satisfy a large-reactor floor. Each value
    equals the mandated new capacity plus the existing fleet that
    survives to 2050 under 80-year licenses. The code asserts this
    identity.

    **How to read a case name.** A case name joins a program family, a
    schedule, and a cost world. Example: `smr100_eo_p95` is the 100%-SMR
    program, on the 2025 EO schedule, in the expensive world.
    """),
    code(r"""
    t01 = pd.read_csv(S3_EXP / "t01_case_inventory.csv")

    # Schedule metadata: token -> (source, provenance class). The tokens, the
    # source names, and the one-per-class design are the locked schedule set
    # (mc/mc_cost_trajectories.ipynb S2; outline I1).
    SCHED_META = {
        "eia":   ("EIA 2026 AEO high",       "modeled projection"),
        "aj":    ("Abou-Jaoude mod",         "study assumption"),
        "iaea":  ("IAEA high",               "intergovernmental outlook"),
        "mck":   ("McKinsey GEP 2025",       "consultancy outlook"),
        "cop28": ("COP28 tripling pledge",   "pledge"),
        "eo":    ("2025 EO",                 "policy aspiration"),
    }

    smr = t01[t01["case"].str.startswith("smr100") & (t01["variant"] == "floor")]
    lrg = t01[t01["case"].str.startswith("large100")]
    rows = []
    for tok, (source, sclass) in SCHED_META.items():
        s, l = smr[smr["schedule"] == tok], lrg[lrg["schedule"] == tok]
        # one mandate per schedule: identical across the three cost worlds
        for fam in (s, l):
            assert len(fam) == 3, (tok, len(fam))
            for col in ["ambition_2050_GW", "n_mandated_years",
                        "first_mandated_year", "mandate_2050_GW"]:
                assert fam[col].nunique() == 1, (tok, col)
        rows.append({
            "schedule": tok,
            "source": source,
            "provenance_class": sclass,
            "fleet_target_2050_GW": s["ambition_2050_GW"].iloc[0],
            "new_capacity_2050_GW": s["mandate_2050_GW"].iloc[0],
            "first_mandated_year": int(s["first_mandated_year"].iloc[0]),
            "n_mandated_years": int(s["n_mandated_years"].iloc[0]),
            "large_comparator_2050_GW": l["mandate_2050_GW"].iloc[0],
        })
    table1 = pd.DataFrame(rows)
    # fleet-inclusive comparator mandate = mandated additions + the one shared
    # surviving-fleet term (the 2024 fleet net of 80-yr-license retirements;
    # NOT fleet target - 3: aj's 1 GW of pre-2031 schedule growth is excluded
    # from the post-2030 additions mandate)
    fleet_2050 = (table1["large_comparator_2050_GW"]
                  - table1["new_capacity_2050_GW"]).round(6)
    assert fleet_2050.nunique() == 1 and 90.0 < fleet_2050.iloc[0] < 97.0, fleet_2050
    print(f"existing fleet surviving to 2050 (shared across schedules): "
          f"{fleet_2050.iloc[0]:.1f} GW")
    assert set(t01["schedule"]) == set(table1["schedule"])
    table1.to_csv(P.OUT_EXP / "Table1_deployment_schedules.csv", index=False)
    print(f"exports/Table1_deployment_schedules.csv ({len(table1)} rows)")

    P.caption("Table 1", '''
    The six deployment schedules. One schedule per provenance class; the paper prices the
    schedules and does not rank or weight them. The fleet target is the source's 2050 goal
    for the total US nuclear fleet. The SMR-program mandate enforces new capacity only
    (additions basis); the large-reactor comparator mandates are fleet-inclusive (the same
    mandated new capacity plus the existing fleet that survives to 2050 under 80-year
    licenses). Mandated years are ReEDS solve years that carry
    a mandate row. Sources: t01_case_inventory; the locked schedule set
    (mc_cost_trajectories S2).
    ''')
    table1
    """),

    # ------------------------------------------------- Table 2: freed reserve
    md(r"""
    ## Table 2 — slot consumed by Figure 5

    The Monte Carlo variables table held this slot until 2026-08-19, when
    it moved to the SI as ST10 (appendix notebook): it is methods detail,
    not a result. The freed eighth display slot went to Figure 5 — the
    cost-of-detection figure — on 2026-08-26 (Ethan). All eight display
    items are now used; the former refill candidates (the t12 fiscal
    comparison, now ST7b, and the closed-loop delivery panel, in the SI as
    SF23 since 2026-08-24) stay in the SI, and any further main-text
    exhibit must displace one.
    """),
]

_ST10_MD = md(r"""
    ### ST10 — The Monte Carlo variables

    **What this table shows.** One row for each uncertain input of the
    Monte Carlo. Each draw picks one value for every row. Together those
    values make one cost world (see glossary). The engine turns each
    world into cost trajectories for both technologies at once. The
    Monte Carlo makes 10,000 draws for each schedule. (Moved here from
    main-text Table 2 on 2026-08-19: it is methods detail, and the move
    frees a display slot.)

    **Terms of art, glossed.**
    - A "prior" is the distribution an uncertain input is drawn from.
    - "Uniform, a to b" means: every value between a and b is equally
      probable, and no value outside is possible.
    - The "support" of a prior is the set of values it can produce.
    - Two inputs are "comonotone" when one random number sets both:
      high goes with high, low goes with low.
    - A "copula" ties several random draws together, so they move
      consistently.
    - A "latent" is one of the shared random axes behind the copula.

    **Why uniform ranges.** The empirical record on nuclear learning
    rates spans an order of magnitude. A flat range is an honest
    statement of that ignorance. A peaked distribution would claim
    knowledge we do not have.

    **The dependence structure.** A Gaussian copula joins three latent
    axes: learning, anchor cost, and the global deployment position u.
    The learning and anchor-cost latents have correlation −0.3 (the
    "moderate" set; 0 and −0.6 are swept as sensitivities). Across the
    two technologies, the learning rates share one latent and the anchor
    costs share another: those draws are comonotone. All other rows are
    independent.

    **Scope limit, stated with the priors.** The learning-rate ranges
    reproduce successful-program experience. Negative learning — the
    French and US historical records — lies below the support by design.
    The paper states this limit wherever a cost fan appears (SF3).

    **Verification.** The code checks every stated range against the
    drawn worlds in `mc/exports/mc_perdraw.npz`. If a stated range and
    the draws disagree, the cell fails.
    """)

_ST10_CODE = code(r"""
    import json as _json

    import numpy as np

    # The rows mirror the S4 reference card in mc/mc_cost_trajectories.ipynb
    # (the section of record for the priors); supports are verified below.
    MC_PRIORS = [
        ("Learning rate, large reactors", "LR_large",
         "uniform, 3% to 12% per doubling",
         "learning latent (shared)",
         "firm-level rate; brackets Abou-Jaoude's 8%; low end: Grubler 2010, "
         "Eash-Gates 2020; high end: Lovering 2016, Barakah"),
        ("Learning rate, SMR", "LR_smr",
         "uniform, 3% to 16% per doubling",
         "learning latent (comonotone with large)",
         "firm-level rate; brackets Abou-Jaoude's 9.5% and the 5-15% SMR "
         "literature span (all assumptions; no empirical SMR rate exists)"),
        ("2030 anchor cost (BOAK), large", "BOAK_large",
         "uniform, 5,250 to 7,750 $/kW (2022 USD)",
         "anchor-cost latent (shared)",
         "Abou-Jaoude Table A-1; NREL ATB 2024"),
        ("2030 anchor cost (BOAK), SMR", "BOAK_smr",
         "uniform, 5,500 to 10,000 $/kW (2022 USD)",
         "anchor-cost latent (comonotone with large)",
         "Abou-Jaoude Table A-1; NREL ATB 2024"),
        ("Global deployment position", "u",
         "uniform, 0 (IAEA Low) to 1 (IAEA High)",
         "third copula latent",
         "IAEA RDS-1 2025 projection envelope; u also sets foreign fleet "
         "lifetimes (65 to 70 years)"),
        ("International spillover scale", "s",
         "uniform, 0 to 1; multiplies the regional theta ceilings",
         "independent",
         "Kim & Verdolini 2023 patent-citation barriers set the regional "
         "ranking; s sweeps the level from ambient transfer to the ceilings"),
        ("Cross-technology spillover", "x_ls, x_sl",
         "uniform, 0 to 0.30, each direction",
         "independent",
         "a drawn fraction of the other technology's domestic program also "
         "teaches this technology's vendors; capped well below own learning"),
        ("Vendor count", "m",
         "discrete uniform on {4, 5, 6, 7, 8}",
         "independent",
         "Abou-Jaoude's 4 vendors to the current 7+ US vendors"),
        ("Experience-base convention", "c",
         "fresh start (tiny base) or legacy fleet credited (full stock), "
         "probability 1/2 each",
         "independent",
         "structural (model-form) uncertainty; US large-reactor history "
         "counts for large only"),
        ("Channel substitution", "rho_CES",
         "discrete uniform on {-1, 0, 1}",
         "independent",
         "structural bracket around the multiplicative baseline (rho = 0)"),
        ("Construction-duration position", "lambda",
         "uniform, 0 (INL optimistic) to 1 (INL moderate)",
         "independent",
         "INL/RPT-25-84701 project-duration curves"),
        ("Construction-duration noise", "z",
         "one lognormal factor per world; sigma from the 21-unit panel "
         "residual",
         "independent",
         "realized dispersion of 2009-2024 Gen-III+ projects (PRIS/RDS-2)"),
        ("O&M costs (fixed and variable)", "FOM, VOM",
         "not drawn: mapped from the anchor-cost latent over the ATB "
         "advanced-to-conservative range",
         "comonotone with the anchor cost",
         "expensive-anchor worlds carry high O&M; never an independent "
         "sensitivity (ReEDS case exports)"),
    ]
    st10 = pd.DataFrame(
        MC_PRIORS, columns=["input", "symbol", "prior", "dependence", "basis"])
    st10.to_csv(P.OUT_EXP / "ST10_mc_variables.csv", index=False)
    print(f"exports/ST10_mc_variables.csv ({len(st10)} rows)")

    # Verify the stated supports against the actual drawn worlds.
    NPZ = MC_EXP / "mc_perdraw.npz"
    if NPZ.exists():
        Z = np.load(NPZ)
        meta = _json.loads(str(Z["meta_json"]))
        assert meta["n_draws"] == 10000 and meta["copula_set"] == "moderate"
        cols = [str(c) for c in Z["world_columns"]]
        w = pd.DataFrame(np.vstack([Z[f"worlds_{str(t)}"] for t in Z["scen_tokens"]]),
                         columns=cols)
        BOUNDS = {"lr_large": (0.03, 0.12), "lr_smr": (0.03, 0.16),
                  "boak_large": (5250.0, 7750.0), "boak_smr": (5500.0, 10000.0),
                  "u": (0.0, 1.0), "s": (0.0, 1.0),
                  "x_ls": (0.0, 0.30), "x_sl": (0.0, 0.30),
                  "dur_lambda": (0.0, 1.0)}
        for col, (lo, hi) in BOUNDS.items():
            v = w[col]
            assert v.min() >= lo - 1e-12 and v.max() <= hi + 1e-12, col
            assert (v.max() - v.min()) >= 0.999 * (hi - lo), col  # draws fill the range
        assert set(w["n_vendors"].astype(int)) == {4, 5, 6, 7, 8}
        assert set(w["conv_full"].astype(int)) == {0, 1}
        assert set(np.round(w["ces_rho"], 6)) == {-1.0, 0.0, 1.0}
        print(f"supports verified against {len(w):,} drawn worlds in {NPZ.name}")
    else:
        print(f"SKIP support verification: {NPZ} not found "
              "(regenerable by mc/mc_cost_trajectories.ipynb)")

    P.caption("ST10", '''
    The Monte Carlo variables. One row per uncertain input; 10,000 joint draws per schedule.
    A Gaussian copula joins the learning, anchor-cost, and global-deployment latents
    (learning-anchor correlation -0.3); the learning rates and the anchor costs are
    comonotone across the two technologies; all other inputs are independent. O&M is not
    drawn: it maps from the anchor-cost latent over the ATB advanced-to-conservative range.
    Stated supports are verified against the drawn worlds (mc_perdraw.npz). Full engine and
    elicitation detail: SN1. Source of record: mc_cost_trajectories S4.
    ''')
    st10
    """)

main_cells += [
    # ---------------------------------------------------------------- wrap
    md(r"""
    ## Output manifest

    Everything this notebook wrote, in one list. The composed figures are in
    `figures/`; the tables and the draft captions are in `exports/`.
    """),
    code(r"""
    P.write_captions("main")
    for f in sorted(P.OUT_FIG.glob("Fig*.png")):
        print(f"figures/{f.name}")
    for f in sorted(P.OUT_EXP.glob("Table*.csv")):
        print(f"exports/{f.name}")
    """),
]

# ============================================================================
# APPENDIX NOTEBOOK
# ============================================================================

appx_cells = [
    md(r"""
    # Supplementary display items — figures and tables with explanations

    **Purpose.** This notebook assembles the Supplementary Information items of
    the paper: the supplementary figures (SF), the supplementary tables (ST),
    and pointers to the supplementary notes (SN). As in the main notebook,
    every panel is the already-generated, checked artifact; each item
    carries a source block naming the notebook and cell that made it. The
    last three figures (SF28–30) embed the winner-boundary and NPV-check
    exports (the former re-export gap, closed 2026-08-20 at the source
    notebooks).

    **How to read this notebook.** Same pattern as the main notebook: a text
    block, then a code cell that displays or composes the item and prints a
    draft caption (collected into `exports/captions_appendix.txt`).

    **Language.** Simplified technical English; every term of art is glossed
    in the table below or where it first appears.
    """),
    md(GLOSSARY),
    code(SETUP),

    # ------------------------------------------------------------- SN notes
    md(r"""
    ## Supplementary Notes (SN1–SN10) — pointers

    The ten supplementary notes are text, not display items. They are
    drafted from these sources:

    | Note | Content | Source of record |
    |---|---|---|
    | SN1 | The Monte Carlo engine and its priors (the cost model, the copula, spillover routing, the duration model) | `z-ethan/paper plan.md` (engine sections) + `mc/mc_cost_trajectories.ipynb` |
    | SN2 | The ITC translation procedure (dual → required credit rate, 9 steps) | `z-ethan/step3_analysis/ITC calculation procedure.md` |
    | SN3 | The technology-comparison claims ledger C1–C7, with the pre-registered failures | `z-ethan/tech-comparison-notebook-spec.md` + `mc/tech_comparison.ipynb` |
    | SN4 | Case selection: joint-draw discipline and the layered coverage claim | `z-ethan/paper plan.md` (case-selection sections) + `mc/smr100_case_export.ipynb` |
    | SN5 | Validation registries (pilot forensics; output checks) | `z-ethan/step3_checks/`, `z-ethan/step4_checks/` (summaries in ST8 below) |
    | SN6 | The endogenous-learning feed-back check: arm design (fbA/fbB/fbC/fbK/fbR), verdicts, and the minus-probe minimality bracket | `z-ethan/itcfb_analysis/itcfb_analysis.ipynb` + `z-ethan/itcfbm_analysis/itcfbm_analysis.ipynb` (tables in ST9 below) |
    | SN7 | The ATB basis mapping: the QA replication pin (max error $500/kW), the anchor-convention premium, the experience-basis comparison, and the deployment-space reading | `mc/mc_cost_trajectories.ipynb` (QA4) + `mc/atb_parameter_space.ipynb` (cell `atb-26-a27_qa`) |
    | SN8 | Bridge-failure detection: the ensemble observer, the bill attachment, the noise model, the conformal false-alarm calibration, the bias experiment, and the spend-aware exceedance amendment (2026-08-25; methods.md section 6) | `z-ethan/bridge_detection/methods.md` + `status.md` (tables in ST11, figures in SF25–27 below; the committed-spend figure is main-text Fig 5a) |
    | SN9 | The declining-credit requirement analysis (zero-run), the cost-of-information limit, and the registered batch (new 2026-09-02; reallocated 2026-09-04 to 66 runs = 48 ITC-arm + 12 p25/p75 anchors + 6 horizon, reserve retired): the per-world requirement machinery and its certificate chain, the feasibility mask with its kill dispositions, the demonstration-gap accounting, the dollar-menu certificate scope, the exposure/allocation-cap argument, the Part A restatement, the batch gates + claim ladder, and the anchor-densification registration (GA1/GA2, the out-of-sample test of the three-anchor interpolation) | `z-ethan/rate_design/methods.md` (v2 + v2.1 + v2.2) + `status.md` (adjudications) + `exports/u91_verdict.csv` (tables in ST14–ST16, figures in SF34/SF37/SF38/SF39 below; the fans/mask are main-text Fig 6a/6b, the calibration limit is Fig 5b) |
    | SN10 | The market-world transfer (new 2026-09-02): the required credit rate re-derived on every step4 sensitivity output file (the t09 chain; gate G0a reproduces t09 exactly), the exact shadow-price-ratio x region-set-factor decomposition, the statutory mask per market world (gate G0b reproduces u50/u51), the paired per-world re-run of the spending-cap alarm (common random numbers; gates G-CRN, G-H1w), and the KT1-KT5 kill rules | `z-ethan/market_transfer/methods.md` (v1–v1.4) + `status.md` (review rounds) + `exports/v09_verdict.csv` (tables in ST18, figures SF40-SF41; the envelopes in the Fig 7 caption) |
    """),

    # ---------------------------------------------------------------- SF1-3
    md(r"""
    ## SF1 — Which uncertain inputs move 2050 costs (Spearman sensitivities)

    **What this shows.** For each schedule, the rank correlation between every
    uncertain input dial and the financed 2050 capital cost. Rank correlation
    (Spearman) asks: when this dial is high, is cost high — regardless of the
    exact functional form?

    **Key result.** Two dials dominate everywhere: the starting cost (positive)
    and the learning rate (negative). The minor dials matter little on their
    own. This is why the case design ranks worlds by program cost rather than
    by any single input.
    """),
    code(r"""
    P.show_panel(MC_FIG / "tornado_fincapex.png")
    P.source_ref(
        (MC_FIG / "tornado_fincapex.png", "mc/mc_cost_trajectories.ipynb", "cell 42",
         "Spearman rank correlations over the 10,000 worlds per schedule; table: `mc/exports/sensitivity_spearman.csv`"),
    )
    P.table(MC_EXP / "sensitivity_spearman.csv", index_col=0, round_=3)
    """),
    md(r"""
    ## SF2 — Construction-duration medians by schedule

    **What this shows.** The build-duration model's output: median construction
    duration by year and schedule, for both technologies. Durations shorten as
    programs mature; they drive financed capex through construction-period
    interest, and they are drawn jointly with costs (same copula — a copula is
    the statistical device that ties the draws of several uncertain inputs
    together so they move consistently).
    """),
    code(r"""
    P.show_panel(MC_FIG / "duration_medians_by_schedule.png")
    P.source_ref(
        (MC_FIG / "duration_medians_by_schedule.png", "mc/mc_cost_trajectories.ipynb", "cell 25",
         "the INL duration model inside the MC; percentiles: `mc/exports/mc_duration_percentiles_by_schedule.csv`"),
    )
    """),
    md(r"""
    ## SF3 — Hindcast: where history falls in the sampled learning-rate range

    **What this shows.** We check the priors against history. Korea's realized
    learning (+13% per doubling over 1972–2008) sits at the 77th percentile of
    our sampled industry-rate range. France (−15%) and the United States (−30%)
    experienced negative learning — costs rose with experience — and fall
    **below** the sampled support.

    **How to read it, precisely.** The priors reproduce successful-program
    experience and exclude negative learning **by design**. This is a scope
    statement, not a validation of optimism: the paper says so wherever the
    fans appear, and the limitation is repeated in the Discussion.
    """),
    code(r"""
    P.show_panel(MC_FIG / "hindcast_learning_rates.png")
    P.source_ref(
        (MC_FIG / "hindcast_learning_rates.png", "mc/mc_cost_trajectories.ipynb", "cell 50",
         "sampled industry-rate distribution + literature rates (Lovering 2016; Grubler 2010; Eash-Gates 2020); table: `mc/exports/hindcast_positions.csv`"),
    )
    P.table(MC_EXP / "hindcast_positions.csv", index_col=0)
    """),

    # ---------------------------------------------------------------- SF4-8
    md(r"""
    ## SF4 — Dominance tests: the program-cost distributions compared

    **What this shows.** The cumulative cost distributions of the 100%-SMR and
    100%-large programs, per schedule, with formal dominance tests. "First-order
    stochastic dominance" (FSD) means one program is cheaper at every
    probability level; "second-order" (SSD) means every risk-averse decision
    maker prefers it. The tests are exact (every draw checked), and the
    pre-registered failures are reported in the claims ledger (ST1).
    """),
    code(r"""
    P.show_panel(MC_FIG / "tc_dominance_cdfs.png")
    P.source_ref(
        (MC_FIG / "tc_dominance_cdfs.png", "mc/tech_comparison.ipynb", "cell 23",
         "per-draw program costs from `mc_perdraw.npz`; results: `mc/exports/tech_comparison/dominance_tests.csv`"),
    )
    P.table(MC_EXP / "tech_comparison" / "dominance_tests.csv", round_=4)
    """),
    md(r"""
    ## SF5 — Where the winner flips in the cost-gap plane

    **What this shows.** Each draw placed by its two cost gaps (learning-rate
    gap and starting-cost gap between the technologies), with the winner-flip
    boundary drawn per dependence cell. It localizes the ambiguity: the flip
    boundary moves with the dependence assumption, but always stays inside the
    slow-learning, large-favorable corner.
    """),
    code(r"""
    P.show_panel(MC_FIG / "tc_gapplane_boundaries.png")
    P.source_ref(
        (MC_FIG / "tc_gapplane_boundaries.png", "mc/tech_comparison.ipynb", "cell 20",
         "per-draw gaps and winners across the κ grid (`mc/exports/tech_comparison/perdraw/`)"),
    )
    """),
    md(r"""
    ## SF5a — The winning margin across the dependence grid

    **What this shows.** The pure-program winning margin m (m > 0 means SMR
    wins) along the κ diagonal, per schedule: medians with P25–P75 fans.
    This panel was Fig 3b until the 2026-08-26 recomposition; the main text
    keeps the probability panel (Fig 3a), and this page keeps the sizes.

    **Key results.** Median margins run 5.5–18.5% in SMR's favor and are
    nearly flat in κ; the fans widen as the draws decouple. The lower fan
    edge crossing zero is the same ambiguity SF5 localizes in the gap plane
    — and when large wins in decoupled worlds, its margins (P95 of |m| among
    large-win draws) reach ~29% on the diagonal
    (per-cell detail: `large_win_margins.csv`).
    """),
    code(r"""
    P.show_panel(MC_FIG / "tc_margin_fans.png")
    P.source_ref(
        (MC_FIG / "tc_margin_fans.png", "mc/tech_comparison.ipynb", "cell T5c (added 2026-08-26)",
         "`mc/exports/tech_comparison/robustness_map.csv` (margin percentile columns); large-win detail: `large_win_margins.csv`"),
    )
    P.caption("SF5a", '''
    The pure-program winning margin m along the dependence diagonal (m > 0 = SMR wins;
    medians with P25-P75 fans per schedule). Median margins are 5.5-18.5% in SMR's favor and
    nearly flat in kappa; the fans widen as draws decouple, and large's winning margins in
    decoupled worlds reach ~29% (P95 of the large-win draws). Until 2026-08-26 this panel
    was Fig 3b.
    ''')
    """),
    md(r"""
    ## SF6 — Mixing the program: the mixed-build search and the fragmentation penalty

    **What this shows.** A per-draw optimizer searches all mixed strategies
    (splitting the program between the technologies in any share). Maps show
    where in parameter space a mix would win and by how much. Panel (f) — the
    fragmentation histogram, main-text Fig 3b until the 2026-08-31
    recomposition — shows the cost of the simplest hedge: a 50/50 split under
    the McKinsey schedule.

    **Key result.** Mixes beat the best pure program in 10 of 60,000 draws, by
    at most 0.51%. Splitting 50/50 costs a median 16.7% of program cost.
    Fragmentation costs (split learning) dominate hedging value almost
    everywhere.
    """),
    code(r"""
    P.compose(
        [[MC_FIG / "mixed_build_advantage.png"],
         [MC_FIG / "mixed_build_margin_map.png", MC_FIG / "mixed_build_parameter_space.png"],
         [MC_FIG / "fragmentation_hist.png"]],
        "SF6_mixed_build.png",
        letters=["", "", "e", ""],  # sources 1/2 carry a,b / c,d; the histogram carries f
        center=True,  # the single-panel histogram row is narrower than the map row
    )
    P.source_ref(
        (MC_FIG / "mixed_build_advantage.png", "mc/mixed_build_optimizer.ipynb", "cell 28",
         "its own draw set over `US_SCHEDULES.csv` + ReEDS financials"),
        (MC_FIG / "mixed_build_margin_map.png", "mc/mixed_build_optimizer.ipynb", "cell 30",
         "same optimizer output"),
        (MC_FIG / "mixed_build_parameter_space.png", "mc/mixed_build_optimizer.ipynb", "cell 31",
         "same optimizer output"),
        (MC_FIG / "fragmentation_hist.png", "mc/mc_cost_trajectories.ipynb",
         "cell 40 (standalone emission 2026-08-26; re-lettered b → f 2026-08-31 when it moved here from Fig 3b)",
         "in-memory MC worlds for the McKinsey schedule (the fragmentation experiment; stdout + figure only — no CSV export)"),
    )
    P.caption("SF6", '''
    Mixing the program. (a-e) Mixed-build optimizer results: where any split of the
    program between the two technologies would beat the best pure program, and by how
    much. Mixes win in 10 of 60,000 draws, by at most 0.51%. (f) The fragmentation
    penalty: the extra program cost of a 50/50 split under the McKinsey schedule (median
    16.7%, P50/P90 marked) — splitting the program splits the learning. Panel f was
    main-text Fig 3b until 2026-08-31.
    ''')
    """),
    md(r"""
    ## SF7 — The value of information at baseline: EVPI and the 2036 switch bound

    **What this shows.** What would it be worth to know the true cost world
    before committing the program — and how much of that value could one later
    technology switch recover? The full detail behind main-text Fig 3b: total
    EVPI and its decomposition (which uncertainty carries the value) by
    dependence cell, and the 2036 switch bound with the pre-registered 1%
    threshold (the C5 claim). (Merged 2026-08-31: the switch-bound page was
    SF8 until the third Fig 3 recomposition; the two measures are baseline
    value-of-information κ profiles and the S2 text cites them together, so
    they share one page. SF8 is now the optimism-bias flip-curve page.)

    **Key results.** EVPI is 0.57–0.66% of expected program cost under the
    tightest coupling, rising to 2.3–4.6% fully decoupled (up to about 6.0% at
    the decoupled-anchor probe — the cell where learning stays coupled and the
    starting costs are drawn independently; see the glossary). The value
    concentrates in the learning-rate gap under tight coupling and flips to
    the starting-cost gap when decoupled. The 2036 switch — commit now, but
    allow one perfect-information switch of technology — recovers at most
    0.12–0.66% under tight coupling, rising to 0.86–4.6% fully decoupled
    (maximum 5.88% at the decoupled-anchor probe; a pre-registered failure
    case, reported as such). Early commitment forfeits little in coherent
    worlds — worlds where the two technologies' uncertainties move together.
    These are perfect-information upper bounds: no realistic noisy-signal tier
    is modeled.
    (History: until 2026-08-26 the total-EVPI and bound panels appeared as
    main-text Fig 3c/d; since 2026-08-31 the two κ profiles are combined as
    main-text Fig 3b, and this page keeps the partial decomposition, the probe
    cells, the C5-threshold view, and both tables. The standalone
    `tc_evpi_inset.png` and `tc_adaptive_bound_inset.png` are retired from the
    paper.)
    """),
    code(r"""
    P.show_panel(MC_FIG / "tc_evpi.png")
    P.show_panel(MC_FIG / "tc_adaptive_bound.png")
    P.source_ref(
        (MC_FIG / "tc_evpi.png", "mc/tech_comparison.ipynb", "cell 27",
         "per-draw program costs; tables: `mc/exports/tech_comparison/evpi_total.csv`, `evpi_partial.csv`"),
        (MC_FIG / "tc_adaptive_bound.png", "mc/tech_comparison.ipynb", "cell 25",
         "per-draw program costs with a 2036 switch; table: `mc/exports/tech_comparison/adaptive_value.csv`"),
    )
    P.table(MC_EXP / "tech_comparison" / "evpi_total.csv", round_=4)
    P.table(MC_EXP / "tech_comparison" / "adaptive_value.csv", round_=4)
    """),
    md(r"""
    ## SF8 — Optimism-bias flip curves (all four claims)

    **What this shows.** The full optimism-multiplier sweep behind the main
    text's Fig 3c/d: every S2 headline claim against the SMR optimism
    multiplier m (the factor by which the drawn 2030 SMR anchor cost would
    understate the truth), at the three stress anchors κ = 1, 0.5, 0. Panel
    (a) the majority claim, (b) the fragmentation penalty, (c) EVPI, (d) the
    2036 switch bound. Common random numbers across m; the m = 1.5 points
    reproduce the published `stress_survival.csv` stress rows bit-for-bit.
    (Renumbered 2026-08-31: this page was SF8a while SF8 held the switch-bound
    κ profile, which now shares SF7. Main Fig 3c/d are this sweep's majority
    and EVPI panels at paper size.)

    **Key results.** The majority inverts at m* = 1.10 at κ = 1 (1.15 at
    κ = 0.5, 1.16 at κ = 0) — a ~10–16% SMR anchor error flips the winner.
    The information values are hump-shaped (worth most where the winner is
    contested): EVPI peaks at 5.3% of program cost at m = 1.25 (κ = 1) and
    9.8% at m = 1.45 (κ = 0); the switch bound peaks at 3.0% (κ = 1) to 6.9%
    (κ = 0) near m = 1.10–1.15. The fragmentation claim never flips on
    [1, 2]: the median 50/50-split penalty stays above +5.9% and rises with
    m — hedging never becomes a free source of information. Boundary table:
    `mc/exports/ob_sweep/flip_boundaries.csv`.
    """),
    code(r"""
    P.show_panel(MC_FIG / "obs_flip_curves.png")
    P.source_ref(
        (MC_FIG / "obs_flip_curves.png", "mc/ob_sweep.ipynb", "cell S4",
         "`mc/exports/ob_sweep/sweep_metrics.csv` + `flip_boundaries.csv` (engine ported verbatim from tech_comparison; QA-pinned to `stress_survival.csv`)"),
    )
    P.table(MC_EXP / "ob_sweep" / "flip_boundaries.csv", round_=3)
    P.caption("SF8", '''
    Optimism-bias flip curves for the four commitment claims, against the SMR anchor
    multiplier m at kappa = 1, 0.5, 0. (a) min-over-schedules P(SMR wins), majority flips
    at m* = 1.10/1.15/1.16; (b) the 50/50-split penalty rises with m (no flip); (c) EVPI
    and (d) the 2036 switch bound are hump-shaped, peaking where the winner is contested
    and decaying once large is near-certain. m = 1.5 reproduces the published stress rows
    bit-for-bit. Main Fig 3c/d are panels a and c at paper size; until 2026-08-31 this
    page was numbered SF8a.
    ''')
    """),

    # --------------------------------------------------------------- SF9-14
    md(r"""
    ## SF9 — Which mandated years actually bind

    **What this shows.** For every run and every mandated year: does the
    mandate bind (dual > 0), or is the floor already exceeded (slack)? Slack
    years are "needs no subsidy" years — a legitimate pricing outcome. The
    cheapest EIA world overbuilds its floor by 3% by 2047; every large-reactor
    comparator holds two slack early years because the existing fleet covers
    the floor.
    """),
    code(r"""
    P.show_panel(S3_FIG / "f02_binding_heatmap.png")
    P.source_ref(
        (S3_FIG / "f02_binding_heatmap.png", "step3_analysis/step3_analysis.ipynb", "cell 14",
         "`step3_checks/exports/duals_by_year.csv` (+ step4 for large100)"),
    )
    """),
    md(r"""
    ## SF10 — Mandate floor against built capacity

    **What this shows.** The mandated floor and the capacity the model actually
    builds, per case. Where the built line sits above the floor, the mandate is
    slack and the dual is zero. This is the picture behind the binding/slack
    flags in SF9.
    """),
    code(r"""
    P.show_panel(S3_FIG / "f03_mandate_vs_cap.png")
    P.source_ref(
        (S3_FIG / "f03_mandate_vs_cap.png", "step3_analysis/step3_analysis.ipynb", "cell 15",
         "checks duals/capacity + `inputs/nuclear_learning/nuclear_cap_trajectory_*.csv`"),
    )
    """),
    md(r"""
    ## SF11 — Rental-transfer fans (fiscal flow by year)

    **What this shows.** The yearly fiscal flow of the rental-transfer
    benchmark: dual × mandated capacity, by year and case. This is the flow
    whose present value appears in the fiscal-comparison table (ST7b).
    (The 2026-08-18 instrument-menu recomposition moved this exhibit off
    the main figures, so this page now ships it.)
    """),
    code(r"""
    P.show_panel(S3_FIG / "f12_rental_transfer.png")
    P.source_ref(
        (S3_FIG / "f12_rental_transfer.png", "step3_analysis/step3_analysis.ipynb", "cell 35",
         "checks duals x mandate, discounted; table: `t08_rental_transfer.csv`"),
    )
    """),
    md(r"""
    ## SF11b — The floor, the flat grant, and the credit, net of tax

    **What this shows.** The instrument-cost comparison behind the menu. Under
    symmetric scoring — every commissioning-date dollar, grant or credit
    alike, valued through ReEDS's own financing arithmetic — the minimum net
    cost that delivers the required support is the floor: a flat dollar-per-MW
    payment at commissioning, 4% below the taxable flat cash grant. The
    uniform percentage credit costs 1.17–1.25x the floor, obeying the exact
    identity net ratio = capex overshoot / (1 − penalty): the ~10%
    monetization haircut (tax-equity — the market where developers sell tax
    credits they cannot use themselves — takes a cut) plus a 5–13% oversubsidy
    from quoting a flat dollar need as a uniform percentage of heterogeneous
    capital bases — two frictions, nothing else. Gross budget scoring
    reverses the ranking (the credit looks 4–10% cheaper than the grant) and
    is shown as the budget-scoring line only. State-resolved rates recover
    most of the oversubsidy (t14); the floor shows the cost with neither
    friction.
    """),
    code(r"""
    P.show_panel(S3_FIG / "t13_instrument_comparison.png")
    P.source_ref(
        (S3_FIG / "t13_instrument_comparison.png", "step3_analysis/step3_analysis.ipynb",
         "cell t13fg001 (regenerated 2026-08-18, symmetric scoring)",
         "`t13_flat_grant.csv` + `t14_itc_resolution.csv`"),
    )
    t13 = P.table(S3_EXP / "t13_flat_grant.csv", round_=3)
    smr = t13[t13["case"].str.startswith("smr100") & ~t13["case"].str.endswith("_eq")]
    lrg = t13[t13["case"].str.startswith("large100")]
    for name, fam in (("smr100", smr), ("large100", lrg)):
        print(f"{name} — net vs floor: "
              f"{fam['net_ratio_vs_floor'].min():.2f}-{fam['net_ratio_vs_floor'].max():.2f}; "
              f"net vs flat grant: {fam['net_ratio_vs_grant'].min():.2f}-{fam['net_ratio_vs_grant'].max():.2f}; "
              f"gross: {fam['gross_scoring_ratio'].min():.2f}-{fam['gross_scoring_ratio'].max():.2f}")
    P.caption("SF11b", '''
    The floor, the flat grant, and the credit. Under symmetric scoring the uniform percentage
    credit costs 1.17-1.25x the minimum-cost floor (identity: net ratio = overshoot/(1-0.1)) and
    1.12-1.20x the taxable flat grant; gross budget scoring reverses the ranking (0.90-0.96x)
    and is a budget-scoring figure only. The two frictions - the ~10% monetization haircut and
    the 5-13% uniform-rate oversubsidy - separate the credit from the floor, which shows the
    cost with neither.
    ''')
    """),
    md(r"""
    ## SF12 — The myopia wedge

    **What this shows.** ReEDS solves year by year without foresight (myopic).
    An investor with foresight would not need the same subsidy path. The wedge
    is bracketed between two accounting conventions ("cut" and "hold"):
    hold-to-required ratios run 0.23–1.82 and converge to 1.00 for 2050 builds.
    Early-build subsidies priced myopically exceed the full-foresight
    requirement when the dual path declines. (No foresight runs exist: NREL
    reports the intertemporal solver has been broken for years, so this
    analytical bracket is the quantitative substitute.)
    """),
    code(r"""
    P.show_panel(S3_FIG / "f14_myopia_wedge.png")
    P.source_ref(
        (S3_FIG / "f14_myopia_wedge.png", "step3_analysis/step3_analysis.ipynb", "cell 44",
         "duals + `t09` + pvf_onm; table: `t11_myopia_wedge.csv`"),
    )
    """),
    md(r"""
    ## SF13 — System-cost anatomy

    **What this shows.** Where the mandate's system cost goes: the cost
    decomposition by bucket (capital, fuel, operations, transmission, ...) for
    a reference case, and total system cost by case. These support the fiscal
    magnitudes in the main text; no mandate-versus-no-mandate welfare claim is
    made anywhere (no no-mandate baseline exists by design).
    """),
    code(r"""
    P.compose(
        [[S3_FIG / "f08_cost_decomposition_ref.png"],
         [S3_FIG / "f09_cost_totals.png"]],
        "SF13_cost_anatomy.png",
    )
    P.source_ref(
        (S3_FIG / "f08_cost_decomposition_ref.png", "step3_analysis/step3_analysis.ipynb", "cell 29",
         "h5 `systemcost` bucketed; table: `t05_systemcost_by_case.csv`"),
        (S3_FIG / "f09_cost_totals.png", "step3_analysis/step3_analysis.ipynb", "cell 30",
         "same buckets, totals; deltas: `t06_cost_deltas.csv`"),
    )
    """),
    md(r"""
    ## SF14 — Cost spread within schedules, and program NPV against ambition

    **What this shows.** Left: how much total system cost varies across the
    three cost worlds of the same schedule (the drawn world matters more than
    the schedule). Right: program net present value against schedule ambition.
    Cross-schedule comparisons conflate the schedule and the drawn world; the
    paper says so wherever they appear.
    """),
    code(r"""
    P.compose(
        [[S3_FIG / "f10_within_schedule_spread.png", S3_FIG / "f11_npv_vs_ambition.png"]],
        "SF14_spread_and_npv.png",
        letters=["", "c"],  # f10 carries a,b itself
    )
    P.source_ref(
        (S3_FIG / "f10_within_schedule_spread.png", "step3_analysis/step3_analysis.ipynb", "cell 31",
         "`t06_cost_deltas.csv`"),
        (S3_FIG / "f11_npv_vs_ambition.png", "step3_analysis/step3_analysis.ipynb", "cell 33",
         "`t07_system_npv.csv`"),
    )
    """),
    md(r"""
    ## SF-ambition — The mean binding shadow price across the ambition ladder

    **What this shows.** The cross-section of the mean binding shadow price
    against schedule ambition (demoted from the main shadow-price figure in
    the 08-20 restructure; cited from S3-1). The P50 level first rises
    (334→390 going 117→134 GW), then falls monotonically to 314 at 400 GW:
    more ambitious mandates buy more learning per mandated year. This is a
    cross-section of different conditional worlds, not a supply curve.
    """),
    code(r"""
    P.show_panel(S3_FIG / "f06_dual_vs_ambition.png")
    P.source_ref(
        (S3_FIG / "f06_dual_vs_ambition.png", "step3_analysis/step3_analysis.ipynb", "cell 21",
         "`step3_analysis/exports/t03_dual_summary.csv`"),
    )
    P.caption("SF-ambition", '''
    Mean binding shadow price against schedule ambition, by cost-world percentile. The P50
    level rises from 334 (117 GW) to 390 (134 GW) $/kW-yr, then falls monotonically to 314
    at 400 GW: more ambitious mandates buy more learning per mandated year. Cross-sectional,
    conditional worlds; not a supply curve.
    ''')
    """),

    # -------------------------------------------------------------- SF15-19
    md(r"""
    ## SF15–SF17 — ATB inversion detail

    **What this shows.** The detail behind Figure 1. SF15: the deployment
    each ATB trajectory would require as a function of the learning rate,
    with the ATB's own paired deployments marked. Read this as a basis
    mapping between the source's experience convention and ours (SN7): under
    our 2030 anchor convention — which discards pre-2030 experience — the
    ATB pairings correspond to about 2.1–3.7× more required deployment at the
    source study's own parameters (both sides on the through-2049 stock that
    prices 2050 — the 08-24 registration basis). The two conventions serve
    different
    modeling goals; the mapping explains the difference, it does not
    adjudicate it. SF16: which dial values the endpoint-feasible worlds
    require (dial marginals on the one-sided 2050 basis, matching Fig 1;
    each scenario is scored at its own paired deployment — 12/33/199 GW —
    so LR orderings across scenarios reflect the ATB's pairing structure,
    not the targets alone). SF17: the cross-pairing check — each
    ATB cost trajectory tested against every deployment pairing (some
    trajectories fit better under other schedules than their own).
    """),
    code(r"""
    P.show_panel(MC_FIG / "atb_required_deployment_vs_lr.png")
    P.compose(
        [[MC_FIG / "atb_endpoint_dial_marginals_large.png",
          MC_FIG / "atb_endpoint_dial_marginals_smr.png"]],
        "SF16_atb_dial_marginals.png",
        letters="ab",  # the endpoint marginals carry no baked letters (F10)
    )
    P.show_panel(MC_FIG / "atb_cross_pairing.png")
    P.source_ref(
        (MC_FIG / "atb_required_deployment_vs_lr.png", "mc/atb_parameter_space.ipynb", "cell F7",
         "the grid inversion (~0.79M worlds/trajectory); anchors: `mc/exports/atb/required_deployment_anchors.csv`"),
        (MC_FIG / "atb_endpoint_dial_marginals_large.png", "mc/atb_parameter_space.ipynb",
         "cell F10 (one-sided endpoint basis, 08-24)",
         "endpoint-feasible worlds; shares: `mc/exports/atb/endpoint_feasible_share.csv`"),
        (MC_FIG / "atb_endpoint_dial_marginals_smr.png", "mc/atb_parameter_space.ipynb",
         "cell F10", "same basis, SMR"),
        (MC_FIG / "atb_cross_pairing.png", "mc/atb_parameter_space.ipynb", "figure cells",
         "`mc/exports/atb/cross_pairing_misfit.csv`"),
    )
    """),
    md(r"""
    ## SF18 — Where the priced cases sit in the drawn distribution

    **What this shows.** The case-selection picture: the P5/P50/P95 cases are
    actual joint draws, ranked by discounted program cost, and this shows where
    each selected draw sits in its schedule's distribution, plus the selected
    cases' full cost fans. The layered coverage claim (90% on program cost by
    construction; 0.62–0.81 simultaneous path coverage; 0.83–0.92 one-sided
    below-P95) is documented in ST2/ST3.
    """),
    code(r"""
    P.compose(
        [[MC_FIG / "smr100_case_placement.png"],
         [MC_FIG / "smr100_selected_cases_fan.png"]],
        "SF18_case_placement.png",
    )
    P.source_ref(
        (MC_FIG / "smr100_case_placement.png", "mc/smr100_case_export.ipynb", "figure cells",
         "the ranked draw distribution + selected draws (`mc/exports/smr100/selected_draws.csv`)"),
        (MC_FIG / "smr100_selected_cases_fan.png", "mc/smr100_case_export.ipynb", "figure cells",
         "selected draws' trajectories"),
    )
    """),
    md(r"""
    ## SF19 — Case-design diagnostics

    **What this shows.** Three checks behind the case design. One-at-a-time
    (OAT) linearity: program cost responds near-linearly to each dial alone.
    The s×conv interaction: the one material two-dial interaction (spillover ×
    experience-base convention). The MC trend check: the ranked-draw selection
    is stable across the MC's internal ordering.
    """),
    code(r"""
    P.compose(
        [[MC_FIG / "smr100_oat_linearity.png"],
         [MC_FIG / "smr100_s_conv_interaction.png", MC_FIG / "smr100_mc_trend_check.png"]],
        "SF19_case_design_diagnostics.png",
    )
    P.source_ref(
        (MC_FIG / "smr100_oat_linearity.png", "mc/smr100_case_export.ipynb", "diagnostic cells",
         "OAT sweeps around the selected draws"),
        (MC_FIG / "smr100_s_conv_interaction.png", "mc/smr100_case_export.ipynb", "diagnostic cells",
         "two-dial interaction sweep"),
        (MC_FIG / "smr100_mc_trend_check.png", "mc/smr100_case_export.ipynb", "diagnostic cells",
         "ranking-stability check"),
    )
    """),

    # -------------------------------------------------------------- SF20-22
    md(r"""
    ## SF20 — Binding-year shifts across market worlds

    **What this shows.** The step4 sensitivity detail behind Figure 7: which
    mandated years bind, per case and market world. A high gas-price world
    removes up to six binding years (gas competes less, nuclear needs less
    help) — but never restores decay in an expensive world.
    """),
    code(r"""
    P.show_panel(S4_FIG / "g01_binding_heatmap.png")
    P.source_ref(
        (S4_FIG / "g01_binding_heatmap.png", "step4_analysis/step4_analysis.ipynb", "cell 8",
         "`step4_analysis/exports/s01_binding_shifts.csv`"),
    )
    """),
    md(r"""
    ## SF21 — Does the ambition ordering survive each market world?

    **What this shows.** The schedules ranked by fiscal bill in every market
    world × percentile cell (a "bump chart": lines that stay flat mean the
    ordering survives). Kendall τ — a rank-agreement score, 1 = identical
    order — is at least 0.867 against base in every cell, mean 0.993. The
    mean-binding-dual metric shows adjacent swaps in 13 of its 18
    sensitivity × percentile cells (the fiscal-bill metric swaps in 1 of 18),
    concentrated in cheap worlds; the raw orderings are exported (`s03`).
    """),
    code(r"""
    P.show_panel(S4_FIG / "g04_ranking_bump.png")
    P.source_ref(
        (S4_FIG / "g04_ranking_bump.png", "step4_analysis/step4_analysis.ipynb", "cell 15",
         "`step4_analysis/exports/s03_ranking_preservation.csv`"),
    )
    """),
    md(r"""
    ## SF22 — How much the subsidy level moves, by market world

    **What this shows.** The dual-level ratio of each sensitivity run to its
    base run. Medians by arm: low gas +18%, high gas −27%, high demand −8%,
    cheap renewables +9%, dear renewables −10%, transmission-limited −5%
    (per-case range 0.35–1.77). Every arm with a prior-signed prediction moves
    in the predicted direction (`s05`).
    """),
    code(r"""
    P.show_panel(S4_FIG / "g05_level_ratios.png")
    P.source_ref(
        (S4_FIG / "g05_level_ratios.png", "step4_analysis/step4_analysis.ipynb", "cell 18",
         "`step4_analysis/exports/s04_level_ratios.csv`; mechanism table: `s05_mechanism_color.csv`"),
    )
    P.table(S4_EXP / "s05_mechanism_color.csv", round_=3)
    """),

    # -------------------------------------------------------------- SF23-24
    md(r"""
    ## SF23 — Closed-loop delivery: summary and trajectories

    **What this shows.** The closed-loop validation of the funding claim
    (SN6). Until 2026-08-24 the summary panel sat in the main required-ITC
    figure (now Fig 6); the team
    demoted it to the SI — it validates the ITC translation, it is not a
    standalone finding. The computed ITC schedule replaces the mandate as an
    actual incentives input, and the model re-solves with draw-calibrated
    endogenous learning (fbC). Panel (a): 2050 SMR capacity as a multiple of
    the mandated trajectory, per schedule, with and without learning —
    over-delivery (1.3–2.7x in the median worlds), never under. Panel (b):
    the delivered SMR capacity path against the mandated trajectory, per
    schedule. The credit alone reproduces the mandated deployment in 5 of
    6 median worlds; EIA is partial — a delayed start under myopic lagged
    costs, recovering past its trajectory by 2050.
    """),
    code(r"""
    P.compose(
        [[ITCFB_FIG / "h04_delivery_summary.png"],
         [ITCFB_FIG / "h03_fbC_trajectory_panels.png"]],
        "SF23_closed_loop_delivery.png",
        letters="ab",
        center=True,
    )
    P.source_ref(
        (ITCFB_FIG / "h04_delivery_summary.png", "itcfb_analysis/itcfb_analysis.ipynb",
         "figure cells", "`q06_rate_deployment.csv` / `q04_s9_verdict.csv` (feed-back runs; SN6)"),
        (ITCFB_FIG / "h03_fbC_trajectory_panels.png", "itcfb_analysis/itcfb_analysis.ipynb",
         "figure cells", "the §9 feed-back runs; gaps: `q03_fbC_gaps.csv`; verdicts: `q04_s9_verdict.csv`"),
    )
    q04 = pd.read_csv(ITCFB_EXP / "q04_s9_verdict.csv")
    n_rep = int((q04["tier_fbC"] == "reproduces").sum())
    d_lo, d_hi = q04["delivered_frac_2050"].min(), q04["delivered_frac_2050"].max()
    print(f"closed-loop delivery (fbC): {n_rep} of {len(q04)} median worlds reproduce; "
          f"2050 delivered fraction {d_lo:.2f}-{d_hi:.2f}x")
    P.caption("SF23", f'''
    Closed-loop delivery (the required credit schedule fed back as an actual incentives
    input). a, 2050 SMR capacity as a multiple of the mandated trajectory, per schedule:
    fbB = learning frozen, fbC = draw-calibrated endogenous learning; the diamond credits
    large-reactor substitution (zero substitution was found, so it coincides with the fbC
    bar). Delivery runs {d_lo:.1f}-{d_hi:.1f}x the trajectory — over-delivery, never
    under. b, delivered SMR capacity paths (fbC) against the mandated trajectories. The
    credit reproduces the mandate in {n_rep} of {len(q04)} median worlds; EIA starts late
    under myopic lagged costs and recovers past its trajectory by 2050. The
    delivery-minimal uniform rate sits less than five points below the headline (ST9,
    SN6).
    ''')
    """),
    md(r"""
    ## SF24 — The deployment-vs-rate demand curve (detail behind Fig 6c)

    **What this shows.** The as-exported view behind the main-text cliff
    panel (Fig 6c, promoted 2026-08-24): 2050 capacity against the
    **monetized** credit rate (Fig 6c converts to the statutory model
    convention), showing both technologies and total nuclear rather than
    new nuclear only. The large-reactor series is flat at 94.11 GW at every
    rate — the credit never moves it (the zero-substitution result) — which
    is the fact that lets Fig 6c plot new nuclear as SMR alone. The response
    is strongly convex: zero SMR at a flat 30% credit, 9.8 GW at 50%,
    against 27–381 GW at the schedule-derived rates; the minus probe (ST9)
    locates the delivery boundary within five rate points below the headline
    schedules.
    """),
    code(r"""
    P.show_panel(ITCFB_FIG / "h06_deployment_vs_rate.png")
    P.source_ref(
        (ITCFB_FIG / "h06_deployment_vs_rate.png", "itcfb_analysis/itcfb_analysis.ipynb",
         "figure cells", "`q06_rate_deployment.csv` (flat-rate fbR arm + schedule-rate runs)"),
    )
    P.caption("SF24", '''
    The deployment-vs-rate response on the monetized basis (the detail behind Fig 6c):
    2050 capacity by technology and in total, under flat credit rates and at the
    schedule-derived rates. The large-reactor series is flat at 94.11 GW at every rate
    (the zero-substitution result), so Fig 6c's new-nuclear axis equals the SMR series.
    Zero SMR at a flat 30% credit, 9.8 GW at 50%, against 27-381 GW at the schedule
    rates; the minus probe (ST9) brackets the delivery boundary within five rate points
    below the headline.
    ''')
    """),

    # -------------------------------------------------------------- SF25-27
    md(r"""
    ## SF25 — What the observation noise looks like

    **What this shows.** The detection analysis (S3-3, SN8) asks when an
    observer comparing completed-unit costs against the cost-world ensemble
    can flag a never-decaying world. This page illustrates the noise model:
    per-project reported-cost scatter (σ), a shared industry-wide yearly
    shock (τ), and the systematic-bias variant. The noise levels are
    declared dials, not estimates.
    """),
    code(r"""
    P.show_panel(BD_FIG / "d09_noise_illustration.png")
    P.source_ref(
        (BD_FIG / "d09_noise_illustration.png", "bridge_detection/bridge_detection_stage3.ipynb",
         "figure cells", "the (σ, τ) noise model over the 10,000-world ensemble (SN8)"),
    )
    P.caption("SF25", '''
    The imperfect-observer noise model: per-project reported-cost scatter (sigma), a shared
    industry-wide yearly shock (tau), and the systematic-bias variant, illustrated on drawn
    cost paths. Noise levels are declared dials, not estimates.
    ''')
    """),
    md(r"""
    ## SF26 — Detection years by noise level

    **What this shows.** The distribution of the year in which the
    calibrated observer (5% false-alarm budget, conformal calibration) flags
    a never-decaying world, by noise level. Perfect observation detects at a
    median of 2035–2038; mid-noise medians run 2035–2044 even with 30%
    per-project scatter plus a shared 10% yearly shock. At detection the
    government has committed a median 8–45% of the program's total bill
    (4–85 B2024$).
    """),
    code(r"""
    P.show_panel(BD_FIG / "d10_detection_ecdf_noisy.png")
    P.source_ref(
        (BD_FIG / "d10_detection_ecdf_noisy.png", "bridge_detection/bridge_detection_stage3.ipynb",
         "figure cells", "`b15_detection_noisy.csv` (calibrated rule; three noise levels)"),
    )
    P.caption("SF26", '''
    Detection-year distributions for a never-decaying cost world under the calibrated
    5%-false-alarm rule, by observation-noise level. Mid-noise medians are 2035-2044; at
    detection a median 8-45% of the program's total bill is committed (4-85 B2024$).
    ''')
    """),
    md(r"""
    ## SF27 — Detection year vs the spending cap

    **What this shows.** Detection under the cap criterion on the
    spend-aware standard (2026-08-25 amendment; spec:
    `bridge_detection/methods.md` section 6). The observer scores each
    candidate world's total bill as the observed sunk spend plus that
    world's remaining payments, and reads the outlay ledger every year, so
    every world whose bill truly exceeds the cap is flagged — at the latest
    in the year spend crosses the cap — and the ledger backstop adds no
    false alarms. Each panel plots the detection year (median and
    interquartile band, middle noise level) against the cap, over the
    extended grid: from the cap that only 25% of prior worlds stay under
    (per-schedule floors at 0.5–0.75x the median-world (P50) bill) up to
    1.75–2.2x. Detection-year medians run 2032–2041 across the whole grid;
    the held-out false-alarm rate stays within the 7.5% gate everywhere
    (max 0.069). The money view of the same result is main-text Fig 5;
    moving from low to high observation noise raises the median spend
    committed at a 1.5x cap roughly fourfold (EO schedule: 17.5→70.6 B$) —
    the dollar value of cost surveillance. Framed as information, never as
    a recommendation.
    """),
    code(r"""
    P.show_panel(BD_FIG / "d12_exceedance_by_cap_noisy.png")
    P.source_ref(
        (BD_FIG / "d12_exceedance_by_cap_noisy.png", "bridge_detection/bridge_detection_stage3.ipynb",
         "figure cells", "`b17_exceedance_noisy.csv` / `b18_cost_of_waiting_noisy.csv` "
         "(spend-aware standard, 2026-08-25 amendment)"),
    )
    P.caption("SF27", '''
    Detection year against the cumulative-spend cap under the spend-aware standard
    (median and interquartile band, middle noise level): every truly exceeding world is
    detected, no later than the year spend crosses the cap, so the informative outputs
    are the detection year and the spend committed before the alarm (main-text Fig 5).
    Medians run 2032-2041 across the extended cap grid; held-out false alarms stay
    within the 7.5% gate (max 0.069). Low-to-high observation noise raises the median
    spend committed at a 1.5x cap roughly fourfold (EO 17.5->70.6 B$) — the dollar value
    of cost surveillance. Information, not a recommendation.
    ''')
    """),

    # ------------------------------------------------------------ gap items
    md(r"""
    ## SF28–SF30 — Winner-boundary and NPV-check exhibits

    `mc/winner_boundary.ipynb` and `mc/npv_winner_check.ipynb` hold three
    quotable results (cited from S2-d and Methods §3). They used to write no
    PNGs; the source notebooks now export the static figures themselves
    (`ps.savefig`, 2026-08-20), so the three cells below embed the source
    PNGs per the house convention. The cross-check tables stay with the
    source notebooks' exports.

    All three use the McKinsey schedule (200 GW) as the representative
    schedule, matching the source notebooks. The two "dials" are copula
    percentiles: U0 = the learning dial (0 slow → 1 fast, both technologies
    move together), U1 = the starting-cost dial (0 cheap → 1 expensive).
    """),
    md(r"""
    ### SF28 — The two-dial flip map

    **What this shows.** Every cost world placed on the two dials (learning,
    starting cost), colored by who wins the program. The black contour is the
    flip boundary. Large reactors win only in the slow-learning, expensive
    corner; SMR wins everywhere else.

    *Embeds `winner_boundary.ipynb` section W4 (cell wb011); source PNG
    `mc/figures/wb_two_dial_flip_map.png`.*
    """),
    code(r"""
    P.show_panel(MC_FIG / "wb_two_dial_flip_map.png")
    P.source_ref(
        (MC_FIG / "wb_two_dial_flip_map.png", "mc/winner_boundary.ipynb", "cell wb011 (W4)",
         "`mc/exports/mc_perdraw.npz` (50 MB, local-only; regenerated by mc_cost_trajectories.ipynb S10b)"),
    )
    P.caption("SF28", '''
    The winner-flip boundary on the two cost dials (McKinsey GEP 2025 schedule, 10,000
    draws). a, share of draws the 100%-SMR program wins per bin, with the 50% contour.
    b, median cost margin (% of program cost) with the zero contour. Large reactors
    win only in the slow-learning, expensive-anchor corner.
    ''')
    """),
    md(r"""
    ### SF29 — The learning-for-cost exchange rate

    **What this shows.** The flip boundary by experience-base stratum, and the
    exchange rate it implies. Along the boundary, each percentage point of
    SMR's learning-rate edge over large buys a fixed amount of tolerable
    starting-cost premium — about \$800/kW per point. Under the full-stock
    convention (crediting the ~140-unit legacy fleet to large's experience
    base) the boundary nearly vanishes: diluted learning weakens large's case.

    *Embeds `winner_boundary.ipynb` section W5 (cell wb013); the exchange rate
    is computed in W10 (cell wb026); the break-even table is the exported
    `wb_breakeven.csv`.*
    """),
    code(r"""
    P.show_panel(MC_FIG / "wb_exchange_rate_boundary.png")
    P.source_ref(
        (MC_FIG / "wb_exchange_rate_boundary.png", "mc/winner_boundary.ipynb", "cell wb013 (W5)",
         "`mc/exports/mc_perdraw.npz`; exchange rate: cell wb026 (W10); table: `mc/exports/wb_breakeven.csv`"),
    )
    print("break-even table (mc/exports/wb_breakeven.csv):")
    print(pd.read_csv(MC_EXP / "wb_breakeven.csv").to_string(index=False))
    P.caption("SF29", '''
    The flip boundary by experience-base stratum (McKinsey GEP 2025 schedule; SMR wins
    below each line). Along the tiny-base boundary, each percentage point of SMR's
    learning-rate edge over large buys ~823 $/kW of tolerable starting-cost premium
    (computed in winner_boundary.ipynb W10). Under the full-stock convention the
    boundary nearly vanishes: crediting the legacy fleet dilutes large's learning
    progression and weakens its case.
    ''')
    """),
    md(r"""
    ### SF30 — Does the winner survive non-capital costs? (NPV-margin scatter)

    **What this shows.** The winner analysis above ranks programs by capital
    cost only. This check adds the 30-year present value of fixed and variable
    operations costs and fuel, per draw, and re-ranks. Each point is one world:
    the capital-only margin against the full-NPV margin. Points hug the
    45-degree line: operations costs nudge every margin but flip only
    near-ties, and every flip starts inside the 2% close-call band. The
    source figure's second panel places the flipped draws on the two dials:
    they trace the flip boundary, which itself barely moves.

    *Embeds `npv_winner_check.ipynb` section N4 (cell nv011); the summary
    table is the exported `npv_winner_summary.csv`. The operations-cost stack
    is built there from in-repo inputs (ATB plant characteristics, AEO
    uranium prices, the deflator), tied to the cost dial by the comonotone
    convention.*
    """),
    code(r"""
    P.show_panel(MC_FIG / "np_npv_margin_scatter.png")
    P.source_ref(
        (MC_FIG / "np_npv_margin_scatter.png", "mc/npv_winner_check.ipynb", "cell nv011 (N4)",
         "`mc/exports/mc_perdraw.npz`; summary: `mc/exports/npv_winner_summary.csv`"),
    )
    nws = pd.read_csv(MC_EXP / "npv_winner_summary.csv").set_index("schedule")
    row = nws.loc["McKinsey GEP 2025"]
    fl, fs = int(row["flips large->smr"]), int(row["flips smr->large"])
    print(f"flips (McKinsey GEP 2025): {fl} large->smr, {fs} smr->large; "
          f"all inside the 2% band: {bool(row['flips inside 2% band'] == 1.0)}")
    P.caption("SF30", f'''
    Capital-only vs full-NPV winner margins (McKinsey GEP 2025 schedule). a, adding the
    30-year present value of O&M and fuel (tied to the cost dial) shifts every margin
    slightly and flips only near-ties: {fl} draws flip to SMR and {fs} to large out of
    10,000, all starting inside the 2% close-call band. b, the flipped draws on the two
    dials trace the flip boundary, which itself barely moves.
    ''')
    """),
    md(r"""
    ## SF31 — The full subsidy instrument menu

    **What this shows.** The full instrument menu that the main required-ITC
    figure's menu panel (now Fig 6b)
    summarized until 2026-08-24 (team review, option B: the main panel keeps
    only the voluntary instruments; this page keeps the complete menu as the
    SI anchor for the S3-2 coercion caveat). Each column is one case
    (technology x schedule x cost world); the y axis (log) is net-of-tax
    present-value cost as a multiple of the minimum-cost floor. The uniform
    percentage ITC (1.17–1.25x) and the cash grant (1.04x) are the results;
    the two barred benchmarks are context, not results (demotion ruling
    08-20). The bars are not uncertainty ranges: each spans two post-2050
    continuation worlds — **cut**, where the post-2050 clearing price
    collapses and support self-terminates, and **hold**, where the 2050
    shadow price persists because support stays necessary. The
    capacity-standard mandate can undercut the floor only because compliance
    is compelled: the shortfall against the builders' requirement lands on
    early-vintage capital, a first-cohort transfer rather than a repeatable
    voluntary price. Where a pre-existing fleet collects rent (the
    large-reactor arm) the mandate is instead the expensive end (up to
    5.65x). The commitment bound pays each vintage its foresight value and
    assumes credible multi-decade commitment with foresighted investors.
    """),
    code(r"""
    P.show_panel(S3_FIG / "f16_instrument_menu.png")
    P.source_ref(
        (S3_FIG / "f16_instrument_menu.png", "step3_analysis/step3_analysis.ipynb", "cell t18cd001",
         "`t18_instrument_menu.csv` (from t13 + t17)"),
    )
    P.caption("SF31", '''
    The full subsidy instrument menu: net-of-tax PV cost per instrument as a multiple of
    the minimum-cost floor (flat $/MW at commissioning), per case, log scale. Dots =
    uniform percentage ITC (1.17-1.25x the floor); triangles = unleveraged cash grant
    (1.04x); dotted line = the floor plus the 10% monetization haircut. The two barred
    benchmarks are context, not results, and the bars are not uncertainty ranges: each
    spans two post-2050 continuation worlds (cut = the clearing price collapses and
    support self-terminates; hold = the 2050 shadow price persists). The mandate
    undercuts the floor only by coercion — its shortfall lands on early-vintage capital
    — and is the expensive end where a pre-existing fleet collects rent; the commitment
    bound assumes foresighted investors under a credible multi-decade schedule.
    ''')
    """),
    md(r"""
    ## SF32 — Normalized shadow-price decay curves

    **What this shows.** Each case's shadow price divided by its own peak,
    so every case starts at 1 and shapes compare directly. Main-text Fig 4b
    until 2026-08-26, when the freed display slot went to the
    cost-of-detection figure (Fig 5); the decay-class numbers stay quoted
    in the S3 text and the Fig 4 caption. In cheap worlds the curves decay to
    3–19% of peak by 2050; median worlds are mixed; no P95 case reaches
    half its peak — under slow learning the subsidy is a standing
    commitment, not a bridge.
    """),
    code(r"""
    P.show_panel(S3_FIG / "f07_dual_shape_normalized.png")
    P.source_ref(
        (S3_FIG / "f07_dual_shape_normalized.png", "step3_analysis/step3_analysis.ipynb",
         "cell 26", "same shadow prices as Fig 4, normalized by each case's peak"),
    )
    P.caption("SF32", '''
    Shadow prices normalized by their own peak (main-text Fig 4b until 2026-08-26):
    cheap worlds decay to 3-19% of peak by 2050; median worlds are mixed; no P95 case
    reaches half its peak — under slow learning the subsidy is a standing commitment,
    not a bridge.
    ''')
    """),
    md(r"""
    ## SF33 — Required ITC rate by solve year

    **What this shows.** The required investment-tax-credit rate by solve
    year and case, on the model credit convention (the fin_mult inversion
    plus the 10% monetization haircut), P50 lines with P5–P95 whiskers;
    the shaded band marks the current 48E credit range (30–50%) and the
    line at 100% marks where an ITC alone cannot deliver. Main-text
    Fig 6a until 2026-08-31 (plan v10.42), when the slot went to the
    instrument comparison's achievable-share-vs-budget curves; these rate
    schedules are the thresholds behind that comparison, and the full
    rate table is ST6.
    """),
    code(r"""
    P.show_panel(S3_FIG / "f13_required_itc.png")
    P.source_ref(
        (S3_FIG / "f13_required_itc.png", "step3_analysis/step3_analysis.ipynb", "cell 40",
         "`step3_analysis/exports/t09_required_itc.csv` (model convention, regenerated 2026-08-18)"),
    )
    t09 = pd.read_csv(S3_EXP / "t09_required_itc.csv")
    r = t09[t09["status"] == "rate"]
    smr_r = r[r["case"].str.startswith("smr100")]
    p50 = smr_r[smr_r["case"].str.endswith("p50")].groupby("case")["i_model_headline"].mean()
    ded = r[~r["case"].str.endswith("_eq")]
    n100 = int((ded["i_model_headline"] > 1.0).sum())
    n100p = int((ded["i_pis_headline"] > 1.0).sum())
    P.caption("SF33", f'''
    The required ITC rate by solve year on the model credit convention (main-text
    Fig 6a until 2026-08-31): median-world schedule averages run
    {p50.min():.2f}-{p50.max():.2f} ({p50.min()/0.30:.1f}-{p50.max()/0.30:.1f}x the
    base 48E credit); expensive worlds need 2.7-3.1x; {n100} of {len(ded)} rated
    case-years exceed 100% on the headline convention ({n100p} on the
    placed-in-service conversion). Rates are max-building-region sufficiency rates;
    regional minima run ~15% lower (ST6). These schedules are the per-world delivery
    thresholds behind the Fig 6a comparison.
    ''')
    """),
    md(r"""
    ## SF34 — The certified dollar menu

    **What this shows** (new 2026-09-02; `z-ethan/rate_design/` Part B).
    The share of cost worlds a uniformly scaled credit path delivers
    (offline criterion) against its present-value credit outlay at the
    statutory worst-case bound (2024\$B), one curve per schedule. The
    thick segment is the run-certified zone — aj/mck/eo only, at scales
    within one rate point of the headline, one model world per schedule,
    earned by uniform rate-point decrements (the decrement-vs-scale family
    gap, up to ~1.8 rate points, is disclosed in the source); dots mark
    the closed-loop full-headline delivery points (eia open = partial —
    delayed start, recovers). The legend states each schedule's
    outlay-vs-bill wedge (1.8–2.6x): the statutory outlay axis is not the
    shadow-price bill axis, and the wedge is never folded into a gain.
    Delivery below the certified zone is extrapolation-within-family; the
    uncapped credit has no every-world outlay bound (delivering rates
    induce 1.15–1.85x take-up in the certified runs), so budget-cap
    readings ride an allocation cap — a design argument, not a result.
    """),
    code(r"""
    P.show_panel(RD_FIG / "w33_dollar_menu.png")
    P.source_ref(
        (RD_FIG / "w33_dollar_menu.png", "rate_design/rate_design_v2.ipynb", "Part B cells",
         "`u53_dollar_menu.csv` + `u54_exposure_summary.csv` (certified-zone re-scope per the "
         "adjudicated audit; verdicts in `u91_verdict.csv`)"),
    )
    P.caption("SF34", '''
    The certified dollar menu: delivered share of cost worlds vs present-value credit
    outlay at the statutory worst-case bound, per schedule. Thick = run-certified
    (aj/mck/eo, scales within one rate point of the headline, one world each,
    decrement-earned; family gap up to ~1.8 rate points disclosed); dots = closed-loop
    full-headline delivery points (eia open = partial); legend states each schedule's
    1.8-2.6x outlay-vs-bill wedge, never folded into a gain. Below the certified zone
    the curves are extrapolation-within-family; outlay caps assume allocation-capped
    credits (uncapped delivering rates induce 1.15-1.85x take-up). Tables: ST14.
    ''')
    """),
    md(r"""
    ## SF35 — The budget menu (main-text Fig 6a until 2026-09-02)

    **What this shows.** The budget menu: for each schedule, against the
    budget cap (multiples of the middle world's published bill, the
    detection analysis's cap grid), the share of cost worlds the
    affordable credit delivers and the affordable credit itself as the
    average statutory rate (right axis; the \$/kW conversion is ST13). The
    credit's outlay must stay inside the cap in every world (the hard
    rule; the cap is a chosen setting). The two instrument readings —
    realized-cost percentage ITC vs fixed-basis \$/kW credit — are drawn
    separately and visually overlap: the matched-rule equivalence that
    emptied the instrument-form horse race (plan v10.43). Demoted from
    main-text Fig 6a on 2026-09-02 (outline fourteenth pass): the mask
    supersedes it — the menu says what a cap affords, the mask says the
    affordable credit hits the statutory rate wall in most worlds
    regardless.
    """),
    code(r"""
    P.show_panel(IC_FIG / "k02_budget_menu.png")
    P.source_ref(
        (IC_FIG / "k02_budget_menu.png",
         "instrument_comparison/instrument_comparison.ipynb", "figure cell",
         "`instrument_comparison/exports/s02_budget_sweep.csv` + `s03_headline_table.csv` "
         "(gates G0-G5 green; main Fig 6a 2026-08-31 -> 2026-09-02)"),
    )
    s03c = pd.read_csv(IC_EXP / "s03_headline_table.csv")
    h15 = s03c[s03c["mult"] == 1.5]
    rate_lo, rate_hi = h15["menu_rate_avg_stat"].min(), h15["menu_rate_avg_stat"].max()
    kw_lo, kw_hi = h15["menu_credit_avg_kW"].min(), h15["menu_credit_avg_kW"].max()
    sh_lo, sh_hi = h15["share_flat"].min() * 100, h15["share_flat"].max() * 100
    gap_lo, gap_hi = h15["matched_rule_gap"].min() * 100, h15["matched_rule_gap"].max() * 100
    tol_hi = h15["tolerance_value_pts"].max() * 100
    P.caption("SF35", f'''
    The budget menu (main-text Fig 6a until 2026-09-02): against the budget cap
    (multiples of the middle world's published bill), the affordable credit under the
    hard-cap rule — outlay inside the cap in every cost world; the cap is a chosen
    setting — as the average statutory rate (dotted, right axis; $/kW conversion in
    ST13), and the share of cost worlds that credit delivers (solid, +-20%
    interpolation band). At the 1.5x cap the menu reads {rate_lo:.2f}-{rate_hi:.2f}
    average statutory rate (~${kw_lo:,.0f}-{kw_hi:,.0f}/kW), delivering
    {sh_lo:.0f}-{sh_hi:.0f}% of worlds. The two instrument readings coincide to within
    {gap_lo:+.1f}/{gap_hi:+.1f} points at the 1.5x cap (the matched-rule equivalence);
    a 5%-exceedance tolerance would raise only the realized-cost form's delivery (up
    to {tol_hi:.0f} points; ST13) — a property of the budget rule, not the instrument.
    ''')
    """),
    md(r"""
    ## SF36 — Uniform ITC vs ambition (main-text Fig 6b until 2026-09-02)

    **What this shows.** The net-of-tax present-value cost of a uniform
    percentage credit, as a multiple of the minimum-cost floor (a flat
    dollar-per-MW payment at commissioning with frictionless
    monetization), by schedule, ordered by 2050 ambition. Demoted from
    main-text Fig 6b on 2026-09-02 (outline fourteenth pass): the
    instrument premium over the floor is modest in practice — 1.17–1.25x
    at p50, the ~10% monetization haircut plus the 5–13% uniform-rate
    oversubsidy — so the panel largely re-plots the Fig 4 bill shape in
    rate units; the level finding (0.59–0.74 statutory, 2.0–2.5x base
    48E) stays in the S3-4 topic sentence and ST6. The two legal
    rate-level inputs are resolved (2026-08-20, open item 7): the haircut
    defaults to 10% (x0.947 to the 5% best-transfer variant) and
    depreciation is 15-year MACRS throughout.
    """),
    code(r"""
    P.show_panel(S3_FIG / "f17_itc_vs_ambition.png")
    P.source_ref(
        (S3_FIG / "f17_itc_vs_ambition.png", "step3_analysis/step3_analysis.ipynb",
         "cell f17cd001", "`t18_instrument_menu.csv` (voluntary instruments only; "
         "main Fig 6b 2026-08-24 -> 2026-09-02)"),
    )
    t18 = pd.read_csv(S3_EXP / "t18_instrument_menu.csv")
    m18 = t18[~t18["case"].str.endswith("_eq")]
    hair = float(m18["dpmw_haircut"].iloc[0])
    ov_lo = (m18["uniform_itc"].min() / hair - 1) * 100
    ov_hi = (m18["uniform_itc"].max() / hair - 1) * 100
    P.caption("SF36", f'''
    The uniform percentage credit vs the floor, by schedule ordered by 2050 ambition
    (main-text Fig 6b until 2026-09-02): the credit costs
    {m18['uniform_itc'].min():.2f}-{m18['uniform_itc'].max():.2f}x the floor in every
    case — the ~10% monetization haircut (dotted line, x{hair:.2f}) plus a
    {ov_lo:.0f}-{ov_hi:.0f}% oversubsidy from paying one flat rate where required
    rates differ across regions and years; an unleveraged cash grant prices at
    {m18['cash_grant'].iloc[0]:.2f}x. Markers = median (P50) cost world, whiskers =
    P5-P95. The premium does not grow with ambition, cost world, or technology; rates
    are final (10% haircut headline, x0.947 at the 5% best-transfer variant; 15-year
    MACRS throughout). Full menu incl. the coerced benchmarks: SF31; rate detail:
    SF33/ST6.
    ''')
    """),
    md(r"""
    ## SF37 — The plateau test on the credit-scale interval

    **What this shows** (new 2026-09-02; behind the Fig 5b plateau
    labels). The mid-noise credit-scale confidence width against
    cumulative mandate spend (2024\$B), log scale, one line per schedule,
    with each schedule's label under the registered rule: "asymptote" only
    where the mean decline over the last three observations is at most 5%
    per observation (aj 2.9%, eo 1.6%); the rest are "still declining" at
    the horizon (7.5–14.3% per observation), so their verdict is "not
    within the program horizon", not "never". The dotted lines at the
    bottom are the per-schedule design targets — an order of magnitude
    below where any curve ends.
    """),
    code(r"""
    P.show_panel(RD_FIG / "w21_asymptote.png")
    P.source_ref(
        (RD_FIG / "w21_asymptote.png", "rate_design/rate_design_v2.ipynb", "Part A cells",
         "`u30_part_a_restated.csv` (decline_pct_per_obs_last3 column; the <=5%/observation "
         "labeling rule is registered in `rate_design/methods.md` v2)"),
    )
    P.caption("SF37", '''
    The plateau test behind the Fig 5b labels: mid-noise credit-scale confidence width
    vs cumulative mandate spend (log scale). "Asymptote" is earned only where the mean
    decline over the last three observations is at most 5% per observation (aj 2.9%,
    eo 1.6%); the other four schedules are still declining at the horizon (7.5-14.3%
    per observation), so their verdict is "not within the program horizon", not
    "never". Dotted lines: the per-schedule design targets. Tables: ST16.
    ''')
    """),
    md(r"""
    ## SF38 — The dollar requirement fans (\$/kW)

    **What this shows** (new 2026-09-02; the companion unit behind
    main-text Fig 6a). The cushioned per-world dollar requirement in
    \$/kW, per schedule and build year — the same fans as Fig 6a in the
    unit the demonstration-gap accounting consumes. Encodings match the
    Fig 6a legend: median solid, interquartile and p5–p95 bands, thin
    dotted = the ±20% certificate-band medians, grey dashed = the
    reference credit path. The per-cell above-top and below-bottom clamp
    shares are exported with the table (ST14); the rate-unit grid at full
    size IS main-text Fig 6a (the legended w34 variant).
    """),
    code(r"""
    P.show_panel(RD_FIG / "w31_dollar_fans.png")
    P.source_ref(
        (RD_FIG / "w31_dollar_fans.png", "rate_design/rate_design_v2.ipynb", "Part B cells",
         "`u50_requirement_fans.csv` (need_kw rows; the demonstration-gap input; the rate-unit "
         "grid is main-text Fig 6a, the legended w34 paper variant)"),
    )
    P.caption("SF38", '''
    The dollar requirement fans: the cushioned per-world requirement in $/kW, per
    schedule and build year — the Fig 6a fans in the unit the demonstration-gap
    accounting consumes (encodings as in the Fig 6a legend: median solid,
    interquartile and p5-p95 bands, thin dotted = +-20%-band medians, grey dashed =
    the reference credit path). Per-cell clamp shares and the band fans: ST14.
    ''')
    """),
    md(r"""
    ## SF39 — The calibration limit, full audit grid

    **What this shows** (new 2026-09-02; the Fig 5b source before Ethan's
    reading review re-denominated the main-text panel). The legended twin
    of the frozen w20 audit artifact: top row, the 5–95 confidence width on
    the required credit scale in scale units (multiples of the reference
    credit path; the dashed line is each schedule's registered band-5
    target, 0.068–0.078); bottom row, the width of the learning-rate
    interval in points; both against cumulative committed spend (2024\$B),
    one column per schedule, three noise levels; shading would mark
    observation years where the mid-noise 10th-percentile effective sample
    falls below 100 worlds (it never does). Fig 5b is this grid with the
    top row times the reference path's outlay-weighted average rate (u32);
    the learning-rate row is unchanged.
    """),
    code(r"""
    P.show_panel(RD_FIG / "w36_ci_curves_paper.png")
    P.source_ref(
        (RD_FIG / "w36_ci_curves_paper.png", "rate_design/rate_design_v2.ipynb",
         "S7 paper-variant cell (legended twin of the w20 audit artifact)",
         "`u10_ci_curves.csv` + `u12_ess.csv` (frozen v1 sweep) summarized in "
         "`u30_part_a_restated.csv`; registration: `rate_design/methods.md` v2/v2.1"),
    )
    P.caption("SF39", '''
    The calibration limit, full audit grid behind Fig 5b: top row, the 5-95 confidence
    width on the required credit scale (multiples of the reference credit path; dashed =
    each schedule's registered band-5 target); bottom row, the width of the learning-rate
    interval (points); both vs cumulative committed spend (2024$B), one column per
    schedule, three noise levels (thick = middle). No top-row curve reaches its target at
    any noise level; every bottom-row curve narrows steadily. Fig 5b re-denominates the
    top row in statutory points and keeps the learning-rate row (u32). Tables: ST16.
    ''')
    """),

    # -------------------------------------------------------------- SF40-41
    md(r"""
    ## SF40 — The statutory wall in every market world

    **What this shows.** The S3-4 feasibility mask — the share of cost worlds
    whose required uniform credit rate exceeds a statutory ceiling (0.50 or
    0.60) in at least one build year after the demonstration window (build
    years after 2035) — recomputed in each of the six alternative market
    worlds of Figure 7. The required rate is re-derived exactly on every
    sensitivity output file: the conversion is linear in the shadow price for
    a fixed case-year, so what moves it is the shadow price itself, which
    regions build (the headline is a maximum over building regions; that
    factor moves 6.7% of paired case-years' rates by more than 5%, the worst
    by 28%), and which years still bind (56 of the 990 sensitivity case-years
    change status against base, ST18a; censored cells per world in ST18f). Each
    bar spans the ±20% certificate band — the stage-2 predict-the-middle
    error of the bill interpolation, carried onto the rates by convention;
    the thick grey bar is the base market world. In the high-gas world the
    four smaller schedules' 0.60-ceiling shares fall to 0.00–0.45 across the
    band (0.16–0.22 at the band centre); in the low-gas world the band-high
    share reaches 1.00 in every schedule at 0.50 and in four of six at 0.60
    (0.47–1.00 across the band). The registered kill rules and the
    disclosures are in `market_transfer/exports/v09_verdict.csv` (SN10).
    """),
    code(r"""
    v04 = pd.read_csv(MT_EXP / "v04_mask_range_table.csv")
    v04 = v04[v04["window"] == "w2035"]
    g6 = v04[(v04["world"] == "gashi") & (v04["cap"] == 0.6)].set_index("schedule")
    assert (g6.loc[["eia", "aj", "iaea", "mck"], "lo"] == 0).all() and g6.loc[["eia", "aj", "iaea", "mck"], "hi"].max() <= 0.45
    l5 = v04[(v04["world"] == "gaslo") & (v04["cap"] == 0.5)]
    l6 = v04[(v04["world"] == "gaslo") & (v04["cap"] == 0.6)]
    assert int((l5["hi"] >= 0.9999).sum()) == 6 and int((l6["hi"] >= 0.9999).sum()) == 4 and l6["lo"].min() >= 0.47
    v00 = pd.read_csv(MT_EXP / "v00_status_flips.csv")
    assert len(v00) == 56, len(v00)
    P.show_panel(MT_FIG / "x01_mask_ranges.png")
    P.source_ref(
        (MT_FIG / "x01_mask_ranges.png", "market_transfer/market_transfer.ipynb", "Part 2 mask cell",
         "`market_transfer/exports/v03_feasibility_mask_perworld.csv` + `v04_mask_range_table.csv`; "
         "rates from `v01_required_itc_perworld.csv` (the t09 chain on 126 output files)"),
    )
    P.caption("SF40", '''
    The statutory wall across market worlds: share of cost worlds needing an above-ceiling
    credit rate in a post-window build year (build years after 2035), per schedule, at the
    0.50 (left) and 0.60 (right) ceilings; each bar spans the +/-20% certificate band with a
    black tick at the band centre (the x1.0 rates), thick grey = base market world, colours =
    the six alternative market worlds of Fig 7. In the
    high-gas world the four smaller schedules' 0.60-ceiling shares fall to 0.00-0.45 across the
    band (0.16-0.22 at the band centre); in the low-gas world the band-high share reaches 1.00
    in every schedule at 0.50 and in four of six at 0.60 (0.47-1.00 across the band). SMR
    program. Tables: ST18.
    ''')
    """),
    md(r"""
    ## SF41 — The spending-cap alarm in every market world

    **What this shows.** The S3-3 detection analysis re-run per market world
    with that world's shadow-price paths and an identical seed, so every
    noise history pairs with its base counterpart: the spend committed
    (present value) before the alarm at a cap of 1.5× the world's own
    median-world (P50) bill, at the middle noise level, per schedule (dot =
    median across exceeding worlds and noise histories; thick bar =
    interquartile; thin = 5–95%; red tick = the cap). The cost observations
    that drive the alarm are engine outputs and do not change; the market
    world enters through the bill scale and through the set of worlds that
    exceed the cap (starting probability of exceedance 0.13–0.44 across the
    six alternative worlds against 0.15–0.32 in base). Cells marked × and *
    are range-only: their three-anchor bill interpolation fails the ±20%
    predict-the-middle test (in the high-gas world the cheap-world shadow
    price reaches zero mid-horizon, a floor kink a straight line cannot fit),
    so they are shown but excluded from the numeric envelope.
    """),
    code(r"""
    P.show_panel(MT_FIG / "x03_paid_at_detection_perworld.png")
    P.source_ref(
        (MT_FIG / "x03_paid_at_detection_perworld.png", "market_transfer/market_transfer.ipynb",
         "Part 3 detection cell",
         "`bridge_detection/exports/b17_exceedance_noisy_{world}.csv` (stage-3 variants) summarized in "
         "`market_transfer/exports/v05_detection_perworld.csv` + `v06_detection_summary.csv`"),
    )
    P.caption("SF41", '''
    The spending-cap alarm across market worlds: spend committed (present value, 2024$B)
    before the alarm at 1.5x the world's own median-world (P50) bill (middle noise), per
    schedule and market world; dot = median, thick bar = interquartile, thin bar = 5-95%
    range, red tick = the cap; x (drawn at that cell's median) and * = range-only cells whose
    bill interpolation fails its +/-20% test (high gas: aj, cop28, eo; iaea in the high-demand,
    dear-renewables, and transmission-limited worlds), excluded from the numeric envelope. Paired noise histories
    (same seed). The fixed-dollar companion (the base world's cap in 2024$) is in ST18. SMR
    program.
    ''')
    """),

    # ---------------------------------------------------------------- ST1-8
    md(r"""
    ## Supplementary tables (ST1–ST18)

    Each table below is loaded from its checked export, displayed, and
    re-exported to this notebook's `exports/` folder (Nature Energy ships
    complex tables as csv). The source path in each cell is the file of record.
    The numbering follows the outline and is renumbered at draft.
    """),
    md(r"""
    ### ST1 — The claims ledger

    The technology-comparison analysis pre-registered seven claims (C1–C7)
    and recorded each verdict, including the failures (C2–C6 fail in specific
    dependence cells; the paper reports them with the same prominence as the
    passes).
    """),
    code(r"""
    P.table(MC_EXP / "tech_comparison" / "claims_ledger.csv", "ST1_claims_ledger.csv")
    """),
    md(r"""
    ### ST2 — Band coverage

    The layered coverage claim behind the three-case design: the P5–P95 case
    pair covers 90% of program cost by construction; simultaneous path coverage
    is 0.62–0.81; one-sided below-P95 coverage is 0.83–0.92.
    """),
    code(r"""
    P.table(MC_EXP / "smr100" / "band_coverage.csv", "ST2_band_coverage.csv", round_=3)
    """),
    md(r"""
    ### ST3 — Bounds record

    The input-side possibility frontier: the parameter corners that bound the
    plausible set (no frontier ReEDS runs exist; this is an input-space
    record).
    """),
    code(r"""
    P.table(MC_EXP / "smr100" / "bounds_record.csv", "ST3_bounds_record.csv", round_=3)
    """),
    md(r"""
    ### ST4 — Winner headline table

    Win probabilities and margins per schedule (the wb_headline export):
    P(SMR wins), median margins in percent and \$/kW, and the share of
    close-call worlds.
    """),
    code(r"""
    P.table(MC_EXP / "wb_headline.csv", "ST4_wb_headline.csv", index_col=0, round_=3)
    """),
    md(r"""
    ### ST5 — Dual summary and bridge metrics, all cases

    The case-level results tables: t03 (dual levels) and t04 (bridge-shape
    metrics) for all 37 runs. (Until 2026-08-19 a merged version of these
    was main-text Table 1; the schedules table replaced it there.)
    """),
    code(r"""
    P.table(S3_EXP / "t03_dual_summary.csv", "ST5a_dual_summary.csv", round_=1)
    P.table(S3_EXP / "t04_bridge_metrics.csv", "ST5b_bridge_metrics.csv", round_=3)
    """),
    md(r"""
    ### ST6 — Required ITC rates, full table

    The full year-by-year required-rate table (t09, regenerated 2026-08-18):
    the year's status, the subsidy level, and both rate conventions — the
    headline model convention (`i_model_*`: fin_mult inversion plus the 10%
    monetization haircut; also the rate the decentralization runs feed back
    into ReEDS) and the placed-in-service overnight-cost-only conversion
    (`i_pis_*` = i_model x ccmult; a real owner's statutory rate lies between
    the two).
    """),
    code(r"""
    P.table(S3_EXP / "t09_required_itc.csv", "ST6_required_itc_full.csv", round_=3)
    """),
    md(r"""
    ### ST7 — Fiscal comparison and instrument benchmarks

    Seven exports: the ITC outlay (t10), the outlay-versus-rental comparison
    (t12), the floor/grant/credit comparison net of tax (t13), the
    federal/state/zone rate-resolution ladder (t14), the mandate restated per
    vintage with the cut/hold bracket (t17), the subsidy instrument menu
    (t18), and the commitment-ITC schedule (t19).
    """),
    code(r"""
    P.table(S3_EXP / "t10_itc_outlay.csv", "ST7a_itc_outlay.csv", round_=2)
    P.table(S3_EXP / "t12_fiscal_comparison.csv", "ST7b_fiscal_comparison.csv", index_col=0, round_=2)
    P.table(S3_EXP / "t13_flat_grant.csv", "ST7c_grant_vs_credit.csv", round_=3)
    P.table(S3_EXP / "t14_itc_resolution.csv", "ST7d_rate_resolution.csv", round_=3)
    P.table(S3_EXP / "t17_mandate_perbuild.csv", "ST7e_mandate_perbuild.csv", round_=1)
    P.table(S3_EXP / "t18_instrument_menu.csv", "ST7f_instrument_menu.csv", round_=2)
    P.table(S3_EXP / "t19_commitment_itc.csv", "ST7g_commitment_itc.csv", round_=3)
    """),
    md(r"""
    ### ST8 — Validation registries

    The two output-check registries (54 step3 checks; 52 step4 checks; all
    PASS/INFO). The step4 extraction manifest (148 files with sha256 hashes)
    is the archive-integrity record; we note it here and ship it as data.
    """),
    code(r"""
    s3c = P.table(S3C_EXP / "checks_summary.csv", "ST8a_step3_checks.csv")
    print(s3c["status"].value_counts().to_string())
    s4c = P.table(S4C_EXP / "checks_summary.csv", "ST8b_step4_checks.csv")
    print(s4c["status"].value_counts().to_string())
    print(f"extraction manifest: {len(pd.read_csv(S4C_EXP / 'extraction_manifest.csv'))} files"
          " with sha256 hashes (step4_checks/exports/extraction_manifest.csv)")
    """),
    md(r"""
    ### ST9 — Closed-loop feed-back verdicts and the rate–deployment tables

    The endogenous-learning feed-back check (SN6; cited from S3-5 and
    SF23): the per-world arm verdicts (q04 — fbC reproduces 5 of 6 median
    worlds, EIA partial with recovery), the combined rate–deployment table
    (q06), and the 24-run minus probe (returned 2026-08-20): the minimality
    verdicts (r03) and the minus-ladder rate–deployment table (r04).
    Delivery survives one point below the headline in 6 of 6 ladders and
    fails five points below in 6 of 6 — the delivery-minimal uniform rate is
    bracketed in (headline−0.05, headline−0.01].
    """),
    code(r"""
    P.table(ITCFB_EXP / "q04_s9_verdict.csv", "ST9a_feedback_verdicts.csv", round_=3)
    P.table(ITCFB_EXP / "q06_rate_deployment.csv", "ST9b_rate_deployment.csv", round_=3)
    P.table(ITCFBM_EXP / "r03_minimality_verdicts.csv", "ST9c_minimality_verdicts.csv", round_=3)
    r04 = P.table(ITCFBM_EXP / "r04_rate_deployment.csv", "ST9d_minus_rate_deployment.csv", round_=3)
    P.caption("ST9", '''
    Closed-loop feed-back verdicts and rate-deployment tables: per-world arm verdicts (q04),
    the combined rate-deployment table (q06), and the minus-probe minimality verdicts and
    ladder (r03/r04). The delivery-minimal uniform rate is bracketed in (headline-0.05,
    headline-0.01] in all six arm x world ladders; below the boundary the learning feed-back
    amplifies the shortfall. Sources: itcfb_analysis and itcfbm_analysis exports; design and
    verdict definitions in SN6.
    ''')
    """),
    _ST10_MD,
    _ST10_CODE,
    md(r"""
    ### ST11 — Bridge-failure detection tables

    The consolidated detection tables (SN8; cited from S3-3 and Fig 5):
    detection years under the calibrated 5%-false-alarm rule — perfect
    observation (b09) and the three noise levels (b15); the cost of waiting
    with the noise gradient (b18; under the spend-aware standard the cap
    criterion's never-detected share is zero by construction, so its
    columns carry the paid-at-detection medians); the bias experiment (b19:
    an observer who mistakes a 30% systematic overrun for an expensive
    world false-alarms on 23–35% of benign worlds; an observer who knows
    the bias loses nothing); and the full cap-grid exceedance table behind
    Fig 5 and SF27 (b17: detection-year quartiles, completed US units at
    detection, paid-at-detection percentiles p05–p95, the held-out
    false-alarm rate, and the pre-amendment costs-only observer as
    reference columns).
    """),
    code(r"""
    P.table(BD_EXP / "b09_detection_calibrated.csv", "ST11a_detection_calibrated.csv", round_=3)
    P.table(BD_EXP / "b15_detection_noisy.csv", "ST11b_detection_noisy.csv", round_=3)
    P.table(BD_EXP / "b18_cost_of_waiting_noisy.csv", "ST11c_cost_of_waiting.csv", round_=3)
    P.table(BD_EXP / "b19_bias_experiment.csv", "ST11d_bias_experiment.csv", round_=3)
    P.table(BD_EXP / "b17_exceedance_noisy.csv", "ST11e_exceedance_noisy.csv", round_=3)
    P.caption("ST11", '''
    Bridge-failure detection tables: calibrated detection years under perfect observation
    (b09) and three noise levels (b15), the cost of waiting with the noise gradient (b18),
    the bias experiment (b19), and the cap-grid exceedance table on the spend-aware
    standard (b17: detection-year quartiles, units and paid-at-detection percentiles,
    held-out false-alarm rate, costs-only reference columns; behind Fig 5 and SF27).
    Observer design, noise model, and calibration in SN8.
    ''')
    """),
    md(r"""
    ### ST13 — The budget-menu sweep

    The tables behind Fig 6a (new 2026-08-31, plan v10.42; menu reframing
    v10.43; cited from S3-4): per schedule and budget cap, the affordable
    credit under the hard-cap rule in both policy units (average statutory
    ITC fraction and average dollars per kilowatt), the delivered share
    under both instrument readings — fixed-basis and realized-cost ITC,
    whose gap is the matched-rule equivalence check — with the ±20%
    interpolation band, plus the 95%-of-worlds quantile variant of the
    realized-cost form and its exceedance probability (s02); the
    1.25/1.5/2.0x cap headline rows with the matched-rule gap and the
    tolerance value (s03). Estimator design, gates G0–G5, and the
    v1→v2→v3 log: `instrument_comparison/methods.md`.
    """),
    code(r"""
    P.table(IC_EXP / "s02_budget_sweep.csv", "ST13a_budget_sweep.csv", round_=4)
    P.table(IC_EXP / "s03_headline_table.csv", "ST13b_headline_table.csv", round_=4)
    P.caption("ST13", '''
    The budget-menu sweep (behind Fig 6a): per schedule and cap, the affordable credit
    under the hard-cap rule (outlay inside the cap in every world) as an average
    statutory rate and average dollars per kilowatt, the delivered share under both
    instrument readings with the +-20% interpolation band, and the realized-cost
    form's 95%-of-worlds quantile variant with its exceedance probability (s02);
    headline rows at the 1.25/1.5/2.0x caps with the matched-rule gap (the
    equivalence check: -10.6 to +2.2 points over the whole grid, mostly within +-3)
    and the tolerance value (the 95% relaxation helps only the realized-cost form —
    a property of the budget rule, not of the instrument) (s03). Gates G0-G5 green;
    design and the v1-v2-v3 log in instrument_comparison/methods.md.
    ''')
    """),
    md(r"""
    ### ST14 — Declining-credit zero-run tables

    The tables behind Fig 6a/6b and SF34/SF38 (new 2026-09-02; SN9; cited
    from S3-4): the requirement fans with per-cell censor and clamp
    columns (u50); the feasibility mask per year and per world, at both
    caps and all three certificate-band points — the only quotable form is
    the cap x band range (u51); the demonstration-gap fans per cap x band
    x window, with the window-applicability flag (eia N/A) (u52); the
    dollar-menu zone table (u53); and the exposure/wedge summary (u54).
    Registration and kill dispositions (KB1/KB2/KB3): `rate_design/methods.md`
    v2/v2.1 + `u91_verdict.csv`.
    """),
    code(r"""
    P.table(RD_EXP / "u50_requirement_fans.csv", "ST14a_requirement_fans.csv", round_=4)
    P.table(RD_EXP / "u51_feasibility_mask.csv", "ST14b_feasibility_mask.csv", round_=4)
    P.table(RD_EXP / "u52_demonstration_gap.csv", "ST14c_demonstration_gap.csv", round_=3)
    P.table(RD_EXP / "u53_dollar_menu.csv", "ST14d_dollar_menu.csv", round_=4)
    P.table(RD_EXP / "u54_exposure_summary.csv", "ST14e_exposure_summary.csv", round_=3)
    P.caption("ST14", '''
    Declining-credit zero-run tables (behind Fig 6a/6b, SF34, SF38): requirement fans
    with censor/clamp columns (u50); the feasibility mask per year and per world at
    both caps and all three certificate-band points — quotable only as cap x band
    ranges (u51); demonstration-gap fans per cap x band x window with the
    window-applicability flag (u52); the dollar-menu zone table (u53); the
    exposure/wedge summary (u54). Kill dispositions KB1/KB2/KB3 and the certificate
    chain: rate_design/methods.md v2/v2.1 + u91_verdict.csv (SN9).
    ''')
    """),
    md(r"""
    ### ST15 — The registered 66-run batch and the capture decomposition

    **Conditional tables (new 2026-09-02; reallocated 2026-09-04, v2.2; SN9).**
    The batch spec and the capture machinery behind the outline's `[BATCH]`
    items: the contour schedules in \$/kW (u70), the capture decomposition
    with the holdout-drop columns — kill K1 fired, so the quotable capture
    is the holdout-scored value with the worst split drop as its error bar,
    with the quantile-family capture as companion (u71); the no-2050
    sensitivity that gate GX1 adjudicates (u73); the ITC-arm + horizon
    batch spec (u80: 27 envelope + 7 boundary-depth + 14 hybrid + 6
    horizon, no reserve) and the per-run offered credit paths (u81); the
    p25/p75 anchor-densification spec (u82: 12 mandate-arm runs selected by
    the frozen smr100 quantile rule, gates GA1/GA2). **Nothing in these
    tables is paper-quotable until the batch returns and the registered
    gates (GE1/GE2/GH1/GH2/GX1/GA1/GA2) are adjudicated**; the claim ladder
    in `rate_design/methods.md` v2.1/v2.2 cannot be re-argued after outcomes.
    """),
    code(r"""
    P.table(RD_EXP / "u70_contour_schedules_kw.csv", "ST15a_contour_schedules_kw.csv", round_=1)
    P.table(RD_EXP / "u71_capture_decomposition.csv", "ST15b_capture_decomposition.csv", round_=4)
    P.table(RD_EXP / "u73_no2050_sensitivity.csv", "ST15c_no2050_sensitivity.csv", round_=4)
    P.table(RD_EXP / "u80_batch_spec.csv", "ST15d_batch_spec.csv", round_=4)
    P.table(RD_EXP / "u81_run_schedules.csv", "ST15e_run_schedules.csv", round_=1)
    P.table(RD_EXP / "u82_anchor_spec.csv", "ST15f_anchor_spec.csv", round_=4)
    P.table(RD_EXP / "u84_anchor_predictions.csv", "ST15g_anchor_predictions.csv", round_=4)
    _u80 = pd.read_csv(RD_EXP / "u80_batch_spec.csv")
    _u82 = pd.read_csv(RD_EXP / "u82_anchor_spec.csv")
    _bn = _u80["block"].value_counts().to_dict()
    assert (_u80["block"] == "reserve").sum() == 0 and len(_u82) == 12, (_bn, len(_u82))
    _live80 = _u80[_u80["block"].isin(["envelope", "boundary", "hybrid"])]
    P.caption("ST15", f'''
    The registered {len(_u80) + len(_u82)}-run batch and the capture decomposition
    (conditional — nothing here is quotable until the batch returns and gates
    GE1/GE2/GH1/GH2/GX1/GA1/GA2 are adjudicated): contour schedules in $/kW (u70); the
    capture decomposition with holdout drops — kill K1 fired, so any quotable capture is
    the holdout-scored value with its worst split drop as the error bar, quantile family
    as companion (u71); the no-2050 sensitivity behind gate GX1 (u73); the ITC-arm +
    horizon spec — {_bn["envelope"]} envelope + {_bn["boundary"]} boundary-depth +
    {_bn["hybrid"]} hybrid (caps 0.60 and 0.50) + {_bn["horizon"]} horizon, no reserve,
    every offered rate <= {_live80["max_rate_on_world"].max():.3f} on its run world (u80);
    per-run offered credit paths with credit/demonstration tier splits (u81); the
    {len(_u82)} p25/p75 anchor-densification runs selected by the frozen smr100 quantile
    rule (u82) with the three-anchor map's pre-run predictions of their rates, needs
    and bills — the GA2/GA3 out-of-sample test (u84). Registration:
    rate_design/methods.md v2/v2.1/v2.2/v2.2.1 (SN9).
    ''')
    """),
    md(r"""
    ### ST16 — Cost-of-information tables

    The tables behind Fig 5b and SF37 (new 2026-09-02; SN9; cited from
    S3-3): per schedule, the design target, the final credit-scale CI
    width and its ratio to the target (4.8–7.7x), the plateau label under
    the ≤5%-per-observation rule, the learning-rate CI narrowing
    (11.7 → 4.3–9.3 points), and the effective-sample columns (u30); the
    mid-noise width-vs-committed-spend path per observation (u31); and the
    Fig 5b series itself — the credit-rate interval width in statutory
    points and the learning-rate interval width in points at every
    observation, all three noise levels, with the per-schedule conversion
    constant (u32).
    """),
    code(r"""
    P.table(RD_EXP / "u30_part_a_restated.csv", "ST16a_part_a_restated.csv", round_=3)
    P.table(RD_EXP / "u31_part_a_slopes.csv", "ST16b_part_a_slopes.csv", round_=4)
    P.table(RD_EXP / "u32_ci_rate_points.csv", "ST16c_ci_rate_points.csv", round_=2)
    P.caption("ST16", '''
    Cost-of-information tables (behind Fig 5b, SF37 and SF39): per schedule, the design
    target, final credit-scale CI width and its ratio to the target, the plateau label
    under the <=5%-per-observation rule, the learning-rate CI narrowing, and the
    effective-sample columns (u30); the mid-noise width-vs-committed-spend path (u31);
    the Fig 5b series (credit-rate width in statutory points, learning-rate width in
    points) at all three noise levels, with the per-schedule conversion constant (u32).
    The v1 sweep is the frozen input, restated with every audit repair; registration
    and dispositions: rate_design/methods.md v2/v2.1 + u91_verdict.csv (SN9).
    ''')
    """),
    md(r"""
    ### ST17 — Market-world sensitivity tables

    The step4 tables behind Fig 7a/7b and SF20–SF22 (cited from S4-a/b/c):
    binding-year shifts per case and market world (s01); the shape-survival
    matrix with its components (s02); the ranking preservation per
    sensitivity × percentile cell with Kendall τ and the raw orderings (s03);
    the level ratios — like-for-like over shared binding years, with the
    own-years companion (s04); and the prior-signed mechanism check (s05).
    """),
    code(r"""
    P.table(S4_EXP / "s01_binding_shifts.csv", "ST17a_binding_shifts.csv")
    P.table(S4_EXP / "s02_shape_survival.csv", "ST17b_shape_survival.csv", round_=3)
    P.table(S4_EXP / "s03_ranking_preservation.csv", "ST17c_ranking_preservation.csv", round_=3)
    P.table(S4_EXP / "s04_level_ratios.csv", "ST17d_level_ratios.csv", round_=3)
    P.table(S4_EXP / "s05_mechanism_color.csv", "ST17e_mechanism_color.csv", round_=3)
    P.caption("ST17", '''
    Market-world sensitivity tables (behind Fig 7a/7b and SF20-SF22): binding-year shifts
    (s01); the shape-survival matrix with its components - decay class and end-over-peak
    ratio vs base (s02); ranking preservation with Kendall tau and the raw orderings per
    sensitivity x percentile cell (s03); level ratios, like-for-like over shared binding
    years with the own-years companion (s04); the prior-signed mechanism check (s05). The
    18 SMR percentile cases x six market worlds = 108 runs; SMR program.
    ''')
    """),
    md(r"""
    ### ST18 — Market-world transfer tables

    The tables behind SF40, SF41 and the Fig 7 caption (new 2026-09-02;
    SN10; cited from S4-d/S4-e): the required credit rate on every sensitivity
    output file with its ratio companion and region-set factor (v01); the
    per-world mask ranges (v04); the spending-cap alarm's headline cell per
    world under both cap normalizations (v05) and its cross-world summary
    (v06); the region-set summary (v07); and the gate, kill, and quoting
    dispositions (v09).
    """),
    code(r"""
    P.table(MT_EXP / "v01_required_itc_perworld.csv", "ST18a_required_itc_perworld.csv", round_=4)
    P.table(MT_EXP / "v04_mask_range_table.csv", "ST18b_mask_range_table.csv", round_=4)
    P.table(MT_EXP / "v05_detection_perworld.csv", "ST18c_detection_perworld.csv", round_=3)
    P.table(MT_EXP / "v06_detection_summary.csv", "ST18d_detection_summary.csv", round_=3)
    P.table(MT_EXP / "v07_regionset_summary.csv", "ST18e_regionset_summary.csv", round_=4)
    P.table(MT_EXP / "v09_verdict.csv", "ST18f_verdict.csv")
    P.caption("ST18", '''
    Market-world transfer tables (behind SF40, SF41 and the Fig 7 caption): the required
    credit rate per case-year on all 126 output files with the shadow-price ratio companion
    and the region-set factor (v01); the statutory-mask ranges per world, schedule, ceiling
    and window — band ends and band centre — with the base range and overlap flag (v04); the
    spending-cap alarm's headline cell per world under the own-median-world (P50)-bill and
    fixed-dollar cap readings (v05) and its cross-world summary with min, median, and max
    across worlds (v06); the region-set summary (v07); gates, kills, and quoting
    dispositions (v09). Registration: market_transfer/methods.md (SN10). SMR program.
    ''')
    """),

    # ---------------------------------------------------------------- wrap
    md(r"""
    ## Output manifest
    """),
    code(r"""
    P.write_captions("appendix")
    for f in sorted(P.OUT_FIG.glob("SF*.png")):
        print(f"figures/{f.name}")
    for f in sorted(P.OUT_EXP.glob("ST*.csv")):
        print(f"exports/{f.name}")
    """),
]


if __name__ == "__main__":
    write(main_cells, "main_paper_figures.ipynb")
    write(appx_cells, "appendix_figures.ipynb")
