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
                      BD_FIG, BD_EXP)

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
"""

# ============================================================================
# MAIN NOTEBOOK
# ============================================================================

main_cells = [
    md(r"""
    # Main-paper display items — figures and tables with explanations

    **Purpose.** This notebook assembles the main-text display items of the paper
    ("The learning-consistent required subsidy", outline: `z-ethan/paper_outline.md`):
    six figures and Table 1. The Table 2 slot is a freed reserve (2026-08-19: the
    Monte Carlo variables table moved to the SI as ST10, in the appendix notebook).
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
    percentage credit costs 1.17–1.25 times the floor.
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
    reach it (Ethan, 08-21/08-24). Panels (a, b): the cost–deployment plane —
    for each amount of cumulative building by 2050, the 2050 overnight cost
    that the defensible worlds deliver (fan across support-restricted grid
    worlds), with the ATB 2050 target as a black dot at its paired
    Abou-Jaoude deployment; large reactors (a), SMR (b). Panels (c, d):
    endpoint feasibility maps — the shortfall of the 2050 cost against each
    target over learning rate × spillover, with a contour bounding the worlds
    that reach the target within \$250/kW. Both halves split tiny-base
    (learning clock restarts) vs full-stock (legacy fleet credited) rows.

    **How to read it.** In (a, b), a dot below the fan means fewer than 5% of
    defensible worlds reach that cost at that amount of building; reading
    right along the target's dotted line shows how much building would put
    the target inside the fan. In (c, d), feasibility is **one-sided**:
    a world counts when it reaches the target or beats it (overshoot is
    success, not misfit). Each scenario is scored at its own paired
    deployment — conservative 12, moderate 33, advanced 199 GW — so
    cross-scenario comparisons reflect the ATB's pairing structure, not the
    targets alone.

    **Key results.** The engine is pinned to the ATB's source: run at
    Abou-Jaoude's own parameters and experience basis, it reproduces his
    published SMR OCC tables within report rounding (max error \$500/kW).
    Reaching an ATB 2050 cost at its paired deployment takes a firm-level
    learning rate of 12.5–18% at the central discrete world (tiny base,
    spillover-dependent; T5) against the source study's own 9.5% — the gap
    is the expected anchor-convention premium, and it puts the large targets
    at or above the top of large's sampled support (3–12%). On the
    support-restricted grid the feasible shares are 1.1–7.6% for the large
    targets and 12.5–31.9% for SMR — the cheaper scenarios owe their wider
    reach to the much larger deployments the ATB pairs them with. Under
    full-stock accounting no large target is reachable at all: zero feasible
    worlds in all three scenarios, and no learning rate up to 30% closes the
    gap at the paired deployment — every large trajectory presumes
    fresh-start accounting (the empty-contour full-stock rows in c). The
    differences from the source are designed basis conventions (anchor
    convention, experience basis; SN7), not disagreements. This inversion
    uses about 0.79 million sampled worlds per target and zero ReEDS runs.
    """),
    code(r"""
    P.compose(
        [[MC_FIG / "atb_cost_deployment_plane_large.png", MC_FIG / "atb_cost_deployment_plane_smr.png"],
         [MC_FIG / "atb_endpoint_feasible_maps_large.png", MC_FIG / "atb_endpoint_feasible_maps_smr.png"]],
        "Fig1_atb_placement.png",
        letters="",  # all four sources carry their letters (a/b plane, c/d maps)
        center=True,
    )
    P.source_ref(
        (MC_FIG / "atb_cost_deployment_plane_large.png", "mc/atb_parameter_space.ipynb",
         "cell F8 (2050-endpoint reframing, 08-24)",
         "the closed-form 2050 evaluator over the support-restricted Part-2 grid"),
        (MC_FIG / "atb_cost_deployment_plane_smr.png", "mc/atb_parameter_space.ipynb",
         "cell F8", "same evaluator, SMR"),
        (MC_FIG / "atb_endpoint_feasible_maps_large.png", "mc/atb_parameter_space.ipynb",
         "cell F9 (one-sided criterion, 08-24)",
         "2050 shortfall per world at the paired deployment; shares: `mc/exports/atb/endpoint_feasible_share.csv`"),
        (MC_FIG / "atb_endpoint_feasible_maps_smr.png", "mc/atb_parameter_space.ipynb",
         "cell F9", "same shortfalls, SMR"),
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
    print(f"support-restricted feasible shares (one-sided): "
          f"large {100*lg['share_support'].min():.1f}-{100*lg['share_support'].max():.1f}%, "
          f"smr {100*sm['share_support'].min():.1f}-{100*sm['share_support'].max():.1f}%; "
          f"large full-stock: 0 in all three scenarios")

    P.caption("Fig 1", f'''
    Where the ATB 2050 nuclear costs sit in learning space (endpoint basis: the 2030 anchor
    convention discards pre-2030 experience by design, so only the 2050 cost and the builds
    that reach it are scored). (a, b) The cost-deployment plane for large reactors (a) and
    SMR (b): the 2050 overnight cost delivered across support-restricted learning worlds
    (P5-P95 and P25-P75 fans, median line) as a function of cumulative new build, tiny-base
    vs full-stock experience accounting; black dots mark each ATB 2050 target at its paired
    deployment. (c, d) Endpoint feasibility maps: the 2050 shortfall against each target
    over learning rate x spillover, with the $250/kW reach contour; feasibility is
    one-sided (overshoot is success). Reaching a target at its paired deployment takes a
    firm-level rate of {100*lr_lo:.3g}-{100*lr_hi:.3g}% at the central world against the
    source's own 9.5%; feasible shares on the sampled support are
    {100*lg['share_support'].min():.1f}-{100*lg['share_support'].max():.1f}% (large) and
    {100*sm['share_support'].min():.1f}-{100*sm['share_support'].max():.1f}% (SMR), and
    under full-stock accounting no large target is reachable at any learning rate up to
    30%. The engine reproduces the ATB source's published tables under its own parameters
    and experience basis (max error $500/kW); the differences are designed basis
    conventions. ~0.79M sampled worlds per target; no ReEDS runs.
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

    **What this shows.** Before pricing any schedule, we must choose which
    technology carries the program. Panel (a): the probability that SMR is the
    cheaper program carrier, across schedules and across the κ dependence grid
    (κ is glossed above; each grid cell is a different assumption about how the
    two technologies' uncertainties move together). Panel (b): the winning
    margin m across the same grid (m > 0 means SMR wins). Panels (c, d): the
    cost of hedging instead of committing — the financed-capex paths of the
    three program strategies under the McKinsey schedule (c) and the extra
    cost of splitting the program 50/50 ("fragmentation penalty", d).
    Panel (e): the cost of committing **now** instead of waiting — the
    expected value of perfect information (EVPI: the most a decision-maker
    would pay to know the drawn world before committing), across the same
    dependence grid.

    **How to read it.** In panel (a), values above 0.5 mean SMR is the majority
    winner in that cell. In panel (d), the distribution sits almost entirely
    above zero: splitting the program is not a free hedge, because it splits
    the learning.

    **Key results.** SMR is the cheaper carrier with probability 0.82–0.89 under
    the tightest coupling, and stays the majority winner in every primary κ
    cell. The worst cell gives 0.509. That cell is the decoupled-anchor probe
    (see the glossary): the learning rates stay coupled, but each technology
    draws its starting cost independently — not the κ = 0 cell, which
    decouples both. Splitting 50/50 costs a median 16.7% of
    program cost. A per-draw optimizer over mixed programs beats the pure
    programs in only 10 of 60,000 draws, and by at most 0.51%.

    Committing now, rather than waiting to learn which world we are in,
    forfeits little (panel e): EVPI is 0.57–0.66% of expected program cost at
    κ = 1, rising to 2.3–4.6% fully decoupled and up to about 6.0% at the
    decoupled-anchor probe (learning rates stay fully coupled, but each
    technology draws its 2030 starting cost independently — not κ = 0, which
    decouples both). A perfect-information switch of technology in 2036
    recovers at most 0.12–0.66% at κ = 1. These are perfect-information
    upper bounds; no noisy-signal tier was built.

    **Fair-warning results, stated with equal prominence.** When large wins in
    decoupled worlds, its margins can reach about 30%. And a stress test that
    inflates SMR costs by 1.5× (an optimism-bias stress) breaks the claim.
    The commitment is majority-optimal, not certain.
    """),
    code(r"""
    P.compose(
        [[MC_FIG / "tc_robustness_map.png"],
         [MC_FIG / "fragmentation_penalty.png"],
         [MC_FIG / "tc_evpi_inset.png"]],
        "Fig3_technology_choice.png",
        letters="",  # all sources carry their final letters (a,b / c,d / e)
        center=True,  # the EVPI inset row is narrower; do not leave a corner blank
    )
    P.source_ref(
        (MC_FIG / "tc_robustness_map.png", "mc/tech_comparison.ipynb", "cell 18",
         "`mc/exports/mc_perdraw.npz` + the κ-grid per-draw exports; table: `mc/exports/tech_comparison/robustness_map.csv`"),
        (MC_FIG / "fragmentation_penalty.png", "mc/mc_cost_trajectories.ipynb", "cell 40",
         "in-memory MC worlds for the McKinsey schedule (the fragmentation experiment)"),
        (MC_FIG / "tc_evpi_inset.png", "mc/tech_comparison.ipynb", "cell T8b (added 2026-08-21)",
         "`mc/exports/tech_comparison/evpi_total.csv` (the full total+partial figure stays in the SI, SF7)"),
    )

    rm = pd.read_csv(MC_EXP / "tech_comparison" / "robustness_map.csv")
    prim = rm[rm["kind"] == "primary"]
    print(f"P(SMR cheaper), primary κ cells: min {rm['P_smr'].min():.3f} "
          f"(incl. probes), comonotone range {prim[prim['kappa_lr'] == 1.0]['P_smr'].min():.2f}"
          f"-{prim[prim['kappa_lr'] == 1.0]['P_smr'].max():.2f}")

    P.caption("Fig 3", '''
    The technology choice, and the cost of committing now. (a) Probability that a 100%-SMR
    program is cheaper than a 100%-large program, across schedules and across the dependence
    grid (kappa = how strongly the two technologies' cost uncertainties move together). SMR
    is the majority winner in every primary cell; the minimum is 0.509 at the
    decoupled-anchor probe (learning rates coupled, 2030 starting costs drawn independently
    — unlike kappa = 0, which decouples both). (b) The winning
    margin m across the same grid (m > 0 = SMR wins; median and quantile fans).
    (c) Financed capex of the three program strategies under the McKinsey schedule
    (medians, P5-P95 bands). (d) Fragmentation penalty: the extra program cost of the
    50/50 split, median 16.7% — splitting the program splits the learning. (e) Expected
    value of perfect information: committing now instead of waiting forfeits 0.57-0.66% of
    expected program cost in coherent (kappa = 1) worlds, up to ~6.0% at the
    decoupled-anchor probe — a perfect-information upper bound. The commitment
    is majority-optimal, not certain: large can win by ~30% in decoupled worlds, and a
    1.5x SMR optimism-bias stress breaks the claim.
    ''')
    """),

    # ---------------------------------------------------------------- Fig 4
    md(r"""
    ## Figure 4 — The required subsidy is a bridge — in cheap worlds

    **What this shows.** The paper's central object: the mandate's shadow
    price — the yearly rental price, per kW of mandated capacity, that makes
    each schedule worth building (see glossary). Panel (a): the shadow price
    over time for each schedule, in cheap (P5), median (P50), and expensive
    (P95) cost worlds, with the large-reactor comparator overlaid at P50.
    Panel (b): the same shadow prices divided by their own peak, so every
    case starts at 1 and we can compare shapes.

    **How to read it.** A "bridge" subsidy should decay: high at first, near
    zero once the fleet has walked down the learning curve. Panel (b) tests
    exactly that.

    **Key results.**
    - The shadow price is monotone in the cost world: expensive worlds need
      more in every year, with no crossings (visually apparent in the fans;
      quantified in Methods). Mean binding shadow prices run 70–201 (P5),
      314–390 (P50), and 610–698 (P95) in 2024\$/kW-yr; the single peak is 894
      (EO schedule, P95 world, 2031).
    - In cheap worlds the bridge comes down: end-of-horizon shadow prices are
      3–19% of peak. Median worlds are mixed. **In P95 worlds the subsidy does
      not come down: 66–84% of peak in 2050, and no P95 case falls below half
      its peak by 2050.** Under slow learning the subsidy is not a bridge but
      a standing commitment. We give this adverse result the same prominence
      as the decay result.
    - The cross-section of the mean binding shadow price against schedule
      ambition moved to the SI in the 08-20 restructure (SF-ambition, `f06`).
    """),
    code(r"""
    P.compose(
        [[S3_FIG / "f04_dual_fans.png"],
         [S3_FIG / "f07_dual_shape_normalized.png"]],
        "Fig4_shadow_price.png",
        center=True,  # row widths differ; do not leave a blank corner
    )
    P.source_ref(
        (S3_FIG / "f04_dual_fans.png", "step3_analysis/step3_analysis.ipynb", "cell 18",
         "`step3_checks/exports/duals_by_year.csv` (+ step4 checks for the large100 overlay)"),
        (S3_FIG / "f07_dual_shape_normalized.png", "step3_analysis/step3_analysis.ipynb", "cell 26",
         "same shadow prices, normalized by each case's peak"),
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
    The required subsidy and its bridge shape. (a) The mandate's shadow price — the yearly
    rental price per kW of mandated capacity (2024$) — by solve year, for each schedule in
    cheap (P5), median (P50), and expensive (P95) cost worlds; large-reactor P50 comparators
    overlaid. Shadow prices rise with the cost world in every year, with no crossings,
    peaking at {pk['peak_dual_2024_kWyr']:.0f} $/kW-yr ({pk['case']}, {int(pk['peak_year'])}).
    (b) Shadow prices normalized by their own peak: cheap worlds decay to 3-19% of peak; no
    P95 case reaches half its peak by 2050 — under slow learning the subsidy is a standing
    commitment, not a bridge.
    ''')
    """),

    # ---------------------------------------------------------------- Fig 5
    md(r"""
    ## Figure 5 — Required tax-credit rates and the cost of voluntary delivery

    Recomposed 2026-08-24 (team review, option B): the f16 menu panel moved
    to SF31 and the closed-loop delivery panel to SF23 — delivery validates
    the funding claim, it is not a standalone finding. Fig 5 is now three
    panels, all on the voluntary instruments only, and panels (b) and (c)
    are linear. Panel (c) — the rate–deployment cliff — was promoted the
    same day (an explicit one-exhibit reversal of the delivery-to-SI
    demotion: the cliff is a rate result, not a validation exhibit; the
    validation exhibits stay in SF23).

    **What this shows.** The shadow price is a model price. This figure
    translates it into the actual US policy instrument, prices the
    translation, and shows what under-paying it buys. Panel (a): the
    required investment tax
    credit (ITC) rate, by year and case,
    on the **model credit convention** (i_model: the fin_mult inversion plus
    the 10% monetization haircut; the placed-in-service overnight-cost-only
    conversion i_pis = i_model x ccmult is exported per year). The shaded band
    marks the current 48E credit range (30–50%); the line at 100% marks where
    an ITC alone cannot deliver. Panel (b): the **cost of buying the same
    deployment voluntarily** — the uniform percentage credit's net-of-tax
    present-value cost as a multiple of the minimum-cost floor (a flat
    dollar-per-MW payment at commissioning with frictionless monetization),
    by schedule, ordered by 2050 ambition (f17). Panel (c): the
    **rate–deployment cliff** (j06) — new-nuclear 2050 capacity against the
    credit rate on the same basis as panel (a), combining the flat-credit
    anchors, the 24-run minus-probe ladders, and the headline schedule
    points; new nuclear equals SMR capacity exactly because large-reactor
    additions are credit-invariant in every run (the zero-substitution
    result).

    **How to read it.** In panel (a), rates are per-region requirements; the
    headline is the maximum building region. Where a line sits above the 48E
    band, current law is not enough. Where it crosses 100%, no credit
    percentage can close the gap. In panel (b), distance above 1.0 is money
    the instrument wastes relative to the floor: the solid line is the floor,
    the dotted line is the floor with only the 10% monetization haircut
    applied (x1.111), markers are the median (P50) cost world, and whiskers
    span P5–P95. In panel (c), the shaded band is the same 48E range as in
    panel (a): the entire current-law range sits in the flat tail of the
    response, and the cliff starts a few points past its right edge.

    **Key results.** Median-world required rates average 0.59–0.74 across
    schedules — 2.0–2.5 times the current base credit. Expensive worlds need
    2.7–3.1 times; on the headline convention only 5 of 329 rated case-years
    exceed 100% (the i_pis conversion exceeds 100% in 82). The uniform
    percentage credit costs 1.17–1.25x the floor in every case — the ~10%
    monetization haircut plus a 5–13% uniform-rate oversubsidy, two frictions
    and nothing else — and the premium does not grow with ambition, cost
    world, or technology; the unleveraged cash grant sits at 1.04x. The
    mandate and commitment-bound benchmarks are context, not results
    (demotion ruling 08-20 — the paper reports the floor and the ITC): the
    full menu with the mandate's cut-hold band (0.23–0.90x the floor for the
    SMR program, 0.83–5.65x for the large-reactor arm where the pre-existing
    fleet's rent of 141–675 B$ PV dominates) is SF31. The mandate prices the
    same deployment by coercion: the shortfall against the builders'
    requirement lands on early-vintage capital, a first-cohort transfer
    rather than a repeatable voluntary price.

    **The cliff (panel c) and the delivery validation (SI).** The response
    to the rate is a cliff, not a slope: zero SMR at a flat 30% credit,
    9.8 GW at 50% — the entire current-law 48E range buys almost nothing —
    against 27–381 GW at the schedule rates. The 24-run minus probe brackets
    the delivery-minimal rate within five points below the headline, and
    below the boundary the learning feed-back amplifies the shortfall
    instead of cushioning it (solid fbC curves under the dashed fbB curves
    on the low side, over them at the headline). The closed-loop delivery
    validation stays in the SI: the credit alone reproduces the mandated
    deployment in 5 of 6 median worlds (EIA partial: a delayed start under
    myopic lagged costs, recovering past its trajectory by 2050) and
    over-delivers (1.3–2.7x), never under (SF23, ST9, SN6).

    The two legal rate-level inputs are resolved (2026-08-20, open item 7):
    the monetization haircut defaults to 10% (bank tax-equity partnership)
    with an exact x0.947 conversion to the 5% best-transfer-market variant,
    and depreciation is 15-year MACRS throughout (hypothetical-policy
    convention; no current-law conversion reported). The haircut range moves
    every rate in panel (a) by an exact factor; nothing changes the shape.
    Per-case ranges: step3 t20 export; legal detail:
    `ITC calculation procedure.md`.
    """),
    code(r"""
    P.compose(
        [[S3_FIG / "f13_required_itc.png"],
         [S3_FIG / "f17_itc_vs_ambition.png", ITCFBM_FIG / "j06_new_nuclear_cliff.png"]],
        "Fig5_required_itc_and_menu.png",
        letters="abc",
        center=True,  # row widths differ; do not leave a blank corner
    )
    P.source_ref(
        (S3_FIG / "f13_required_itc.png", "step3_analysis/step3_analysis.ipynb", "cell 40",
         "`step3_analysis/exports/t09_required_itc.csv` (model convention, regenerated 2026-08-18)"),
        (S3_FIG / "f17_itc_vs_ambition.png", "step3_analysis/step3_analysis.ipynb", "cell f17cd001",
         "`t18_instrument_menu.csv` (voluntary instruments only; option B panel, 2026-08-24)"),
        (ITCFBM_FIG / "j06_new_nuclear_cliff.png", "itcfbm_analysis/itcfbm_analysis.ipynb",
         "cell j06cd001", "`r04_rate_deployment.csv` (statutory basis, new nuclear only; "
         "promoted 2026-08-24)"),
    )

    t09 = pd.read_csv(S3_EXP / "t09_required_itc.csv")
    r = t09[t09["status"] == "rate"]
    smr_r = r[r["case"].str.startswith("smr100")]
    p50 = smr_r[smr_r["case"].str.endswith("p50")].groupby("case")["i_model_headline"].mean()
    print(f"p50 required rate (model convention), schedule averages: {p50.min():.2f}-{p50.max():.2f} "
          f"(= {p50.min()/0.30:.1f}x-{p50.max()/0.30:.1f}x the 30% base 48E credit)")
    ded = r[~r["case"].str.endswith("_eq")]
    n100 = int((ded["i_model_headline"] > 1.0).sum())
    n100p = int((ded["i_pis_headline"] > 1.0).sum())
    print(f"case-years over 100%: {n100} of {len(ded)} on the model convention; "
          f"{n100p} on the placed-in-service OCC-only conversion")

    t18 = pd.read_csv(S3_EXP / "t18_instrument_menu.csv")
    m18 = t18[~t18["case"].str.endswith("_eq")]
    hair = float(m18["dpmw_haircut"].iloc[0])
    ov_lo = (m18["uniform_itc"].min() / hair - 1) * 100
    ov_hi = (m18["uniform_itc"].max() / hair - 1) * 100
    print(f"uniform ITC vs floor: {m18['uniform_itc'].min():.2f}-{m18['uniform_itc'].max():.2f}x "
          f"(haircut x{hair:.3f} + oversubsidy {ov_lo:.0f}-{ov_hi:.0f}%); "
          f"cash grant {m18['cash_grant'].iloc[0]:.2f}x")

    P.caption("Fig 5", f'''
    Required ITC rates and the cost of voluntary delivery. (a) The required
    investment-tax-credit rate by
    solve year on the model credit convention (fin_mult inversion + 10% monetization haircut;
    the placed-in-service overnight-cost-only conversion is exported per year), P50 lines with
    P5-P95 whiskers; band = current 48E range (30-50%), line = 100%. Median-world schedule
    averages run {p50.min():.2f}-{p50.max():.2f} ({p50.min()/0.30:.1f}-{p50.max()/0.30:.1f}x
    the base credit); {n100} of {len(ded)} rated case-years exceed 100% ({n100p} on the
    placed-in-service conversion). (b) The net-of-tax present-value cost of a uniform
    percentage credit, as a multiple of the minimum-cost floor — a flat dollar-per-MW
    payment at commissioning with frictionless monetization — by mandate schedule,
    ordered by 2050 ambition; markers = median (P50) cost world, whiskers = P5-P95
    range. The credit costs
    {m18['uniform_itc'].min():.2f}-{m18['uniform_itc'].max():.2f}x the floor in every
    case: the ~10% monetization haircut (dotted line, x{hair:.2f}) plus a
    {ov_lo:.0f}-{ov_hi:.0f}% oversubsidy from paying one flat rate where required rates
    differ across regions and years; an unleveraged cash grant (grey line) prices at
    {m18['cash_grant'].iloc[0]:.2f}x. The premium does not grow with ambition, cost
    world, or technology. Rates are final: 10% haircut headline (x0.947 at the 5%
    best-transfer variant); 15-year MACRS convention throughout. (c) New-nuclear
    deployment against the credit rate, on the same rate basis as (a); shaded band =
    the 48E range. New nuclear equals SMR capacity: large-reactor additions are
    credit-invariant in every run (the zero-substitution result), so all points share
    the no-credit baseline. Black squares: flat credits — zero at 30%, 9.8 GW at 50%;
    the entire current-law range buys almost nothing. Colored curves: the minus-probe
    ladders (headline-0.15 ... -0.01, then the headline) with draw-calibrated
    endogenous learning (solid) and learning frozen (faint dashed); single dots mark
    headline-only worlds. The response is a cliff, not a slope: five rate points below
    the headline, delivery fails in every world, and below the boundary learning
    amplifies the shortfall while above it learning amplifies delivery. A
    capacity-standard mandate can price the same deployment below the floor only by
    coercion — its shortfall lands on early-vintage capital, a first-cohort transfer
    rather than a repeatable voluntary price (SF31); closed-loop delivery validation:
    SF23 and ST9.
    ''')
    """),

    # ---------------------------------------------------------------- Fig 6
    md(r"""
    ## Figure 6 — Robustness across market worlds

    **What this shows.** Do the headline results depend on our base market
    assumptions? We re-ran 18 cases under six market sensitivities (gas price
    high/low, high-electrification demand, renewable costs cheap/dear, and a
    transmission-limited world): 108 runs, all output checks green. Panel (a):
    for every case × market world, does the bridge shape survive? Panel (b):
    the shadow-price paths for the ladder's end schedules, overlaid across
    market worlds. Panel (c): the large-reactor comparator against the SMR
    program, by cost-world percentile.

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
    - The ambition ladder's fiscal ordering survives (Kendall τ ≥ 0.867 in
      every cell against base, mean 0.993).
    - Only the level moves, and it moves as economics predicts: the median
      shadow price is −27% under high gas prices, +18% under low, −8% under
      high demand, +9%/−10% under cheap/dear renewables, −5%
      transmission-limited.
    - The large-reactor premium is not a constant. Large needs 1.4–3.5× the
      SMR shadow price in cheap worlds, 1.23–1.36× at the median — but at P95
      the two technologies reach parity (0.95–1.02×): in expensive worlds both
      need the same subsidy.
    """),
    code(r"""
    P.compose(
        [[S4_FIG / "g02_shape_survival_matrix.png", S4_FIG / "g03_dual_overlays.png"],
         [S3_FIG / "f15_large_band.png"]],
        "Fig6_robustness.png",
    )
    P.source_ref(
        (S4_FIG / "g02_shape_survival_matrix.png", "step4_analysis/step4_analysis.ipynb", "cell 11",
         "`step4_analysis/exports/s02_shape_survival.csv`"),
        (S4_FIG / "g03_dual_overlays.png", "step4_analysis/step4_analysis.ipynb", "cell 12",
         "step3+step4 checks `duals_by_year.csv` (eia/eo x p05/p50/p95 x 7 arms)"),
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

    P.caption("Fig 6", f'''
    Robustness across market worlds (108 sensitivity runs: 18 cases x six market arms).
    (a) Bridge-shape survival matrix: the shape survives in {n_surv} of
    {len(surv)} cells — the expensive-world non-decay is generic. (b) Shadow-price overlays
    for the ladder's end schedules across market worlds: only the level moves, in the
    direction economics predicts (median -27% to +18%). (c) Large-reactor vs SMR shadow
    prices by percentile: the large premium is 1.4-3.5x in cheap worlds and 1.23-1.36x at
    the median, but the two technologies reach parity (0.95-1.02x) in expensive worlds.
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
    ## Table 2 — freed reserve slot

    The Monte Carlo variables table held this slot until 2026-08-19. It
    moved to the SI as ST10 (appendix notebook): it is methods detail,
    not a result, and the move frees the eighth display slot. Candidate
    to refill the slot, decided at draft: the fiscal comparison (t12, now
    ST7b). The other former candidate — promoting the closed-loop delivery
    panel — is moot since 2026-08-24: the panel moved the other way, into
    the SI (SF23a).
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
         "tiny-base or full-stock, probability 1/2 each",
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
    ## Supplementary Notes (SN1–SN8) — pointers

    The eight supplementary notes are text, not display items. They are
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
    | SN8 | Bridge-failure detection: the ensemble observer, the bill attachment, the noise model, the conformal false-alarm calibration, and the bias experiment | `z-ethan/bridge_detection/methods.md` + `status.md` (tables in ST11, figures in SF25–27 below) |
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
    ## SF6 — Mixed builds: does any split beat the pure programs?

    **What this shows.** A per-draw optimizer searches all mixed strategies
    (splitting the program between the technologies in any share). Maps show
    where in parameter space a mix would win and by how much.

    **Key result.** Mixes beat the best pure program in 10 of 60,000 draws, by
    at most 0.51%. Fragmentation costs (split learning) dominate hedging value
    almost everywhere.
    """),
    code(r"""
    P.compose(
        [[MC_FIG / "mixed_build_advantage.png"],
         [MC_FIG / "mixed_build_margin_map.png", MC_FIG / "mixed_build_parameter_space.png"]],
        "SF6_mixed_build.png",
        letters=["", "", "e"],  # first two sources carry a,b / c,d themselves
    )
    P.source_ref(
        (MC_FIG / "mixed_build_advantage.png", "mc/mixed_build_optimizer.ipynb", "cell 28",
         "its own draw set over `US_SCHEDULES.csv` + ReEDS financials"),
        (MC_FIG / "mixed_build_margin_map.png", "mc/mixed_build_optimizer.ipynb", "cell 30",
         "same optimizer output"),
        (MC_FIG / "mixed_build_parameter_space.png", "mc/mixed_build_optimizer.ipynb", "cell 31",
         "same optimizer output"),
    )
    P.caption("SF6", '''
    Mixed-build optimizer results: where any split of the program between the two
    technologies would beat the best pure program, and by how much. Mixes win in 10 of
    60,000 draws, by at most 0.51%: splitting the program splits the learning.
    ''')
    """),
    md(r"""
    ## SF7 — The value of perfect information (EVPI)

    **What this shows.** What would it be worth to know the true cost world
    before committing the program? Total EVPI and its decomposition (which
    uncertainty carries the value), by dependence cell.

    **Key results.** EVPI is 0.57–0.66% of expected program cost under the
    tightest coupling, rising to 2.3–4.6% fully decoupled (up to about 6.0% at
    the decoupled-anchor probe — the cell where learning stays coupled and the
    starting costs are drawn independently; see the glossary). The value
    concentrates in the learning-rate gap under tight coupling and flips to
    the starting-cost gap when decoupled.
    These are upper bounds: no realistic noisy-signal tier is modeled.
    (The total-EVPI panel also appears in the main text as Fig 3e, exported
    separately as `tc_evpi_inset.png`; this page keeps the full
    total + partial detail.)
    """),
    code(r"""
    P.show_panel(MC_FIG / "tc_evpi.png")
    P.source_ref(
        (MC_FIG / "tc_evpi.png", "mc/tech_comparison.ipynb", "cell 27",
         "per-draw program costs; tables: `mc/exports/tech_comparison/evpi_total.csv`, `evpi_partial.csv`"),
    )
    P.table(MC_EXP / "tech_comparison" / "evpi_total.csv", round_=4)
    """),
    md(r"""
    ## SF8 — The 2036 switch bound (adaptive commitment)

    **What this shows.** A cheaper form of information value: commit now, but
    allow one perfect-information switch of technology in 2036. The recoverable
    value is at most 0.12–0.66% of program cost under tight coupling (maximum
    5.88% at the decoupled-anchor probe — the independent-starting-cost cell,
    see the glossary; a pre-registered failure case, reported as such). Early
    commitment forfeits little in coherent worlds — worlds where the two
    technologies' uncertainties move together.
    """),
    code(r"""
    P.show_panel(MC_FIG / "tc_adaptive_bound.png")
    P.source_ref(
        (MC_FIG / "tc_adaptive_bound.png", "mc/tech_comparison.ipynb", "cell 25",
         "per-draw program costs with a 2036 switch; table: `mc/exports/tech_comparison/adaptive_value.csv`"),
    )
    P.table(MC_EXP / "tech_comparison" / "adaptive_value.csv", round_=4)
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
    (Figure 4's panel b became the instrument menu on 2026-08-18, so this
    page now ships the rental-transfer exhibit.)
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
    ATB pairings correspond to about 2–3.4× more required deployment at the
    source study's own parameters. The two conventions serve different
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

    **What this shows.** The step4 sensitivity detail behind Figure 6: which
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
    (SN6). Until 2026-08-24 the summary panel was main-text Fig 5c; the team
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
    ## SF24 — The deployment-vs-rate demand curve (detail behind Fig 5c)

    **What this shows.** The as-exported view behind the main-text cliff
    panel (Fig 5c, promoted 2026-08-24): 2050 capacity against the
    **monetized** credit rate (Fig 5c converts to the statutory model
    convention), showing both technologies and total nuclear rather than
    new nuclear only. The large-reactor series is flat at 94.11 GW at every
    rate — the credit never moves it (the zero-substitution result) — which
    is the fact that lets Fig 5c plot new nuclear as SMR alone. The response
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
    The deployment-vs-rate response on the monetized basis (the detail behind Fig 5c):
    2050 capacity by technology and in total, under flat credit rates and at the
    schedule-derived rates. The large-reactor series is flat at 94.11 GW at every rate
    (the zero-substitution result), so Fig 5c's new-nuclear axis equals the SMR series.
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

    **What this shows.** The design-relevant gradient (S3-3): a cumulative-
    spend cap is a far more noise-robust trigger than the decay-shape
    criterion — 5–13% of adverse worlds never flagged by 2050, against
    20–50% for the shape rule — and moving from low to high observation
    noise roughly quadruples the spend committed before detection (EO
    schedule: 32→139 B$). That difference is the dollar value of cost
    surveillance. Framed as information, never as a recommendation.
    """),
    code(r"""
    P.show_panel(BD_FIG / "d12_exceedance_by_cap_noisy.png")
    P.source_ref(
        (BD_FIG / "d12_exceedance_by_cap_noisy.png", "bridge_detection/bridge_detection_stage3.ipynb",
         "figure cells", "`b17_exceedance_noisy.csv` / `b18_cost_of_waiting_noisy.csv`"),
    )
    P.caption("SF27", '''
    Detection by cumulative-spend cap under noise: the cap rule leaves 5-13% of adverse
    worlds never flagged by 2050 (against 20-50% for the decay-shape rule), and low-to-high
    observation noise roughly quadruples the spend committed before detection (EO 32->139
    B$) — the dollar value of cost surveillance. Information, not a recommendation.
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

    **What this shows.** The full instrument menu that main-text panel 5b
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

    # ---------------------------------------------------------------- ST1-8
    md(r"""
    ## Supplementary tables (ST1–ST11)

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

    The three consolidated detection tables (SN8; cited from S3-3): detection
    years under the calibrated 5%-false-alarm rule — perfect observation
    (b09) and the three noise levels (b15); the cost of waiting, with the
    noise gradient and the never-detected shares (b18); and the bias
    experiment (b19: an observer who mistakes a 30% systematic overrun for an
    expensive world false-alarms on 23–35% of benign worlds; an observer who
    knows the bias loses nothing).
    """),
    code(r"""
    P.table(BD_EXP / "b09_detection_calibrated.csv", "ST11a_detection_calibrated.csv", round_=3)
    P.table(BD_EXP / "b15_detection_noisy.csv", "ST11b_detection_noisy.csv", round_=3)
    P.table(BD_EXP / "b18_cost_of_waiting_noisy.csv", "ST11c_cost_of_waiting.csv", round_=3)
    P.table(BD_EXP / "b19_bias_experiment.csv", "ST11d_bias_experiment.csv", round_=3)
    P.caption("ST11", '''
    Bridge-failure detection tables: calibrated detection years under perfect observation
    (b09) and three noise levels (b15), the cost of waiting with never-detected shares and
    the noise gradient (b18), and the bias experiment (b19). Observer design, noise model,
    and calibration in SN8.
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
