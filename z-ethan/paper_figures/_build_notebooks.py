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
from paperlib import MC_FIG, MC_EXP, S3_FIG, S3_EXP, S4_FIG, S4_EXP, S3C_EXP, S4C_EXP

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
| **Dual (shadow price)** | The price the model puts on the mandate rule. It equals the yearly rental payment, per kilowatt of mandated capacity, that would just make builders willing to build. Units: dollars per kW per year, in 2024 dollars. A dual of zero means the mandate needs no subsidy that year. |
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
| **The floor / instrument menu** | The floor is the minimum net government cost that delivers the required support to every build — a flat dollar-per-MW payment at commissioning, elective pay. The menu prices every instrument as a multiple of it. |
| **κ (kappa) coupling** | A dial for how strongly the two technologies' cost uncertainties move together. κ = 1: what is expensive for one is expensive for the other. κ = 0: independent. |
| **EVPI (expected value of perfect information)** | The most that knowing the true cost world in advance could be worth, as a share of expected program cost. |
| **LP / reduced cost** | ReEDS solves a linear program (LP) — a cost-minimization with linear rules. A builder's "reduced cost" is its cost disadvantage at the optimum; zero means it is competitive at the margin. |
"""

# ============================================================================
# MAIN NOTEBOOK
# ============================================================================

main_cells = [
    md(r"""
    # Main-paper display items — figures and tables with explanations

    **Purpose.** This notebook assembles the eight display items of the paper
    ("The learning-consistent required subsidy", outline: `z-ethan/paper_outline.md`).
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
    targets are usually set independently, so they often contradict each other.
    We couple them: Monte Carlo learning-conditional cost worlds feed a capacity
    mandate in ReEDS, and the mandate's dual is the subsidy that makes the pair
    consistent. The subsidy behaves like a bridge (it decays as the fleet learns)
    in cheap worlds, but not in expensive ones. Translated into the US tax
    credit, median worlds need 2.0–2.5 times the current base credit, and no
    real delivery instrument gets the money out for less than the flat
    dollar-per-MW floor.
    """),
    md(GLOSSARY),
    code(SETUP),

    # ---------------------------------------------------------------- Fig 1
    md(r"""
    ## Figure 1 — The six schedules, and the cost worlds each one implies

    **What this shows.** Panel (a): the six deployment schedules (the "ambition
    ladder"), from 117 GW (EIA) to 400 GW (2025 Executive Order) of new capacity
    by 2050. One schedule per source type: modeled projection, study assumption,
    intergovernmental outlook, consultancy outlook, pledge, policy aspiration.
    Panels (b) and (c): for each schedule, the fan of overnight capital cost
    (OCC) paths that our Monte Carlo produces **conditional on that schedule
    happening** — SMR in (b), large reactors in (c).

    **How to read it.** Each fan is a distribution, never a single projection.
    The band spans the 5th to 95th percentile of 10,000 joint draws; the middle
    line is the median. More ambitious schedules buy more learning, so their
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
         [MC_FIG / "occ_fans_smr.png"],
         [MC_FIG / "occ_fans_large.png"]],
        "Fig1_schedules_and_cost_fans.png",
    )
    P.source_ref(
        (S3_FIG / "f01_mandate_trajectories.png", "step3_analysis/step3_analysis.ipynb",
         "cell 10", "`inputs/nuclear_learning/nuclear_cap_trajectory_*.csv` (the mandate files ReEDS reads)"),
        (MC_FIG / "occ_fans_smr.png", "mc/mc_cost_trajectories.ipynb", "cell 23",
         "the in-memory MC results (10,000 joint draws per schedule); percentile export: `mc/exports/mc_occ_percentiles_by_schedule.csv`"),
        (MC_FIG / "occ_fans_large.png", "mc/mc_cost_trajectories.ipynb", "cell 23",
         "same MC results, large-reactor arrays"),
    )

    # Caption numbers computed from the exported percentiles, so text and data cannot drift.
    occ = pd.read_csv(MC_EXP / "mc_occ_percentiles_by_schedule.csv", header=[0, 1, 2], index_col=0)
    smr50_2050 = occ.loc[2050, ("smr", slice(None), "P50")]
    print(f"SMR P50 OCC in 2050, by schedule token:\n{smr50_2050.round(0).to_string()}")
    lo = occ.loc[2050, (slice(None), slice(None), "P5")].min()
    hi = occ.loc[2050, (slice(None), slice(None), "P95")].max()
    print(f"2050 P5-P95 span across schedules and techs: {lo:,.0f} - {hi:,.0f} $/kW")

    P.caption("Fig 1", f'''
    Deployment schedules and the conditional cost worlds they imply.
    (a) Six new-nuclear deployment schedules for the United States, 117-400 GW by 2050,
    one per provenance class; the paper prices these schedules and does not rank them.
    (b, c) Overnight capital cost fans (5th-95th percentile of 10,000 joint Monte Carlo
    draws; line = median) conditional on each schedule, for SMR (b) and large reactors (c).
    Median 2050 SMR cost falls from {smr50_2050.max():,.0f} $/kW (117 GW schedule) to
    {smr50_2050.min():,.0f} $/kW (400 GW schedule). Every fan is conditional on its
    schedule; none is a projection.
    ''')
    """),

    # ---------------------------------------------------------------- Fig 2
    md(r"""
    ## Figure 2 — Why all priced cases commit to a 100%-SMR program

    **What this shows.** Before pricing any schedule, we must choose which
    technology carries the program. Panel (a): the probability that SMR is the
    cheaper program carrier, across schedules and across the κ dependence grid
    (κ is glossed above; each grid cell is a different assumption about how the
    two technologies' uncertainties move together). Panel (b): the winning
    margin m across the same grid (m > 0 means SMR wins). Panels (c, d): the
    cost of hedging instead of committing — the financed-capex paths of the
    three program strategies under the McKinsey schedule (c) and the extra
    cost of splitting the program 50/50 ("fragmentation penalty", d).

    **How to read it.** In panel (a), values above 0.5 mean SMR is the majority
    winner in that cell. In panel (d), the distribution sits almost entirely
    above zero: splitting the program is not a free hedge, because it splits
    the learning.

    **Key results.** SMR is the cheaper carrier with probability 0.82–0.89 under
    the tightest coupling, and stays the majority winner in every primary κ
    cell (the worst cell gives 0.509). Splitting 50/50 costs a median 16.7% of
    program cost. A per-draw optimizer over mixed programs beats the pure
    programs in only 10 of 60,000 draws, and by at most 0.51%.

    **Fair-warning results, stated with equal prominence.** When large wins in
    decoupled worlds, its margins can reach about 30%. And a stress test that
    inflates SMR costs by 1.5× (an optimism-bias stress) breaks the claim.
    The commitment is majority-optimal, not certain.
    """),
    code(r"""
    P.compose(
        [[MC_FIG / "tc_robustness_map.png"],
         [MC_FIG / "fragmentation_penalty.png"]],
        "Fig2_smr_conditioning.png",
        letters="",  # both sources carry their final letters (a,b / c,d)
    )
    P.source_ref(
        (MC_FIG / "tc_robustness_map.png", "mc/tech_comparison.ipynb", "cell 18",
         "`mc/exports/mc_perdraw.npz` + the κ-grid per-draw exports; table: `mc/exports/tech_comparison/robustness_map.csv`"),
        (MC_FIG / "fragmentation_penalty.png", "mc/mc_cost_trajectories.ipynb", "cell 39",
         "in-memory MC worlds for the McKinsey schedule (the fragmentation experiment)"),
    )

    rm = pd.read_csv(MC_EXP / "tech_comparison" / "robustness_map.csv")
    prim = rm[rm["kind"] == "primary"]
    print(f"P(SMR cheaper), primary κ cells: min {rm['P_smr'].min():.3f} "
          f"(incl. probes), comonotone range {prim[prim['kappa_lr'] == 1.0]['P_smr'].min():.2f}"
          f"-{prim[prim['kappa_lr'] == 1.0]['P_smr'].max():.2f}")

    P.caption("Fig 2", '''
    The 100%-SMR conditioning. (a) Probability that a 100%-SMR program is cheaper than a
    100%-large program, across schedules and across the dependence grid (kappa = how strongly
    the two technologies' cost uncertainties move together). SMR is the majority winner in
    every primary cell; the minimum is 0.509 at the decoupled-anchor probe. (b) The winning
    margin m across the same grid (m > 0 = SMR wins; median and quantile fans).
    (c) Financed capex of the three program strategies under the McKinsey schedule
    (medians, P5-P95 bands). (d) Fragmentation penalty: the extra program cost of the
    50/50 split, median 16.7% — splitting the program splits the learning. The commitment
    is majority-optimal, not certain: large can win by ~30% in decoupled worlds, and a
    1.5x SMR optimism-bias stress breaks the claim.
    ''')
    """),

    # ---------------------------------------------------------------- Fig 3
    md(r"""
    ## Figure 3 — The required subsidy is a bridge — in cheap worlds

    **What this shows.** The paper's central object: the mandate's dual — the
    yearly rental price, per kW of mandated capacity, that makes each schedule
    worth building (see glossary). Panel (a): the dual over time for each
    schedule, in cheap (P5), median (P50), and expensive (P95) cost worlds,
    with the large-reactor comparator overlaid at P50. Panel (b): the same
    duals divided by their own peak, so every case starts at 1 and we can
    compare shapes. Panel (c): the average binding dual against schedule
    ambition.

    **How to read it.** A "bridge" subsidy should decay: high at first, near
    zero once the fleet has walked down the learning curve. Panel (b) tests
    exactly that. In panel (c), read left to right as more ambitious mandates.

    **Key results.**
    - The dual is monotone in the cost world: expensive worlds need more in
      every year, with no crossings. Mean binding duals run 70–201 (P5),
      314–390 (P50), and 610–698 (P95) in 2024\$/kW-yr; the single peak is 894
      (EO schedule, P95 world, 2031).
    - In cheap worlds the bridge comes down: end-of-horizon duals are 3–19% of
      peak. Median worlds are mixed. **In P95 worlds the subsidy does not come
      down: 66–84% of peak in 2050, and no P95 case falls below half its peak
      by 2050.** Under slow learning the subsidy is not a bridge but a standing
      commitment. We give this adverse result the same prominence as the decay
      result.
    - Across the ladder the P50 dual first rises (334→390 going 117→134 GW),
      then falls monotonically to 314 at 400 GW: more ambitious mandates buy
      more learning per mandated year. This is a cross-section of different
      conditional worlds, not a supply curve.
    """),
    code(r"""
    P.compose(
        [[S3_FIG / "f04_dual_fans.png"],
         [S3_FIG / "f07_dual_shape_normalized.png", S3_FIG / "f06_dual_vs_ambition.png"]],
        "Fig3_required_subsidy_bridge.png",
        center=True,  # row widths differ; do not leave a blank corner
    )
    P.source_ref(
        (S3_FIG / "f04_dual_fans.png", "step3_analysis/step3_analysis.ipynb", "cell 18",
         "`step3_checks/exports/duals_by_year.csv` (+ step4 checks for the large100 overlay)"),
        (S3_FIG / "f07_dual_shape_normalized.png", "step3_analysis/step3_analysis.ipynb", "cell 26",
         "same duals, normalized by each case's peak"),
        (S3_FIG / "f06_dual_vs_ambition.png", "step3_analysis/step3_analysis.ipynb", "cell 21",
         "`step3_analysis/exports/t03_dual_summary.csv`"),
    )

    t03 = pd.read_csv(S3_EXP / "t03_dual_summary.csv")
    t04 = pd.read_csv(S3_EXP / "t04_bridge_metrics.csv")
    smr = t03[t03["case"].str.startswith("smr100")]
    for pct in ["p05", "p50", "p95"]:
        sel = smr[smr["case"].str.endswith(pct)]
        print(f"{pct}: mean binding dual {sel['mean_binding_dual_2024_kWyr'].min():.0f}"
              f"-{sel['mean_binding_dual_2024_kWyr'].max():.0f} 2024$/kW-yr")
    pk = t03.loc[t03["peak_dual_2024_kWyr"].idxmax()]
    print(f"peak dual: {pk['peak_dual_2024_kWyr']:.0f} ({pk['case']}, {int(pk['peak_year'])})")
    p95 = t04[t04["case"].str.startswith("smr100") & t04["case"].str.endswith("p95")]
    n_below = int((p95["first_year_below_half_peak"] <= 2050).sum())
    print(f"p95 end/peak: {p95['end_over_peak'].min():.2f}-{p95['end_over_peak'].max():.2f}; "
          f"p95 cases below half-peak by 2050: {n_below} of {len(p95)}")

    P.caption("Fig 3", f'''
    The required subsidy and its bridge shape. (a) The mandate's dual — the yearly rental
    price per kW of mandated capacity (2024$) — by solve year, for each schedule in cheap
    (P5), median (P50), and expensive (P95) cost worlds; large-reactor P50 comparators
    overlaid. Duals are monotone in the cost world, peaking at
    {pk['peak_dual_2024_kWyr']:.0f} $/kW-yr ({pk['case']}, {int(pk['peak_year'])}).
    (b) Duals normalized by their own peak: cheap worlds decay to 3-19% of peak; no P95
    case reaches half its peak by 2050 — under slow learning the subsidy is a standing
    commitment, not a bridge. (c) Mean binding dual against ambition: the P50 level rises
    117->134 GW, then falls monotonically to 400 GW. Cross-sectional, conditional worlds;
    not a supply curve.
    ''')
    """),

    # ---------------------------------------------------------------- Fig 4
    md(r"""
    ## Figure 4 — Required tax-credit rates and the instrument menu

    **What this shows.** The dual is a model price. This figure translates it
    into the actual US policy instrument and then prices the alternatives.
    Panel (a): the required investment tax credit (ITC) rate, by year and case,
    on the **model credit convention** (i_model: the fin_mult inversion plus
    the 10% monetization haircut; the placed-in-service overnight-cost-only
    conversion i_pis = i_model x ccmult is exported per year). The shaded band
    marks the current 48E credit range (30–50%); the line at 100% marks where
    an ITC alone cannot deliver. Panel (b): the **subsidy instrument menu** —
    each instrument's net-of-tax present-value cost as a multiple of the
    minimum-cost floor (a flat dollar-per-MW payment at commissioning,
    elective pay), per case.

    **How to read it.** Rates are per-region requirements; the headline is the
    maximum building region. Where a line sits above the 48E band, current law
    is not enough. Where it crosses 100%, no credit percentage can close the
    gap. In panel (b), distance above 1.0 is money an instrument wastes
    relative to the floor; the mandate and the commitment bound can sit below
    1.0 because compliance is compelled and commitment pays only each
    vintage's foresight value.

    **Key results.** Median-world required rates average 0.59–0.74 across
    schedules — 2.0–2.5 times the current base credit. Expensive worlds need
    2.7–3.1 times; on the headline convention only 5 of 329 rated case-years
    exceed 100% (the i_pis conversion exceeds 100% in 82). The uniform
    percentage credit costs 1.17–1.25x the floor everywhere — the ~10%
    monetization haircut plus a 5–13% uniform-rate oversubsidy, both
    removable: an elective-pay dollar-per-MW credit attains the floor. The
    capacity-standard mandate runs 0.29–1.18x the floor for the SMR program
    but 1.0–6.3x for the large-reactor arm, where the pre-existing fleet's
    rent dominates.

    Two legal inputs are still open and are flagged `[LEGAL]` in the paper: the
    monetization haircut size, and the depreciation recovery class. Both move
    every rate in panel (a) by a known formula; neither changes the shape.
    """),
    code(r"""
    P.compose(
        [[S3_FIG / "f13_required_itc.png"],
         [S3_FIG / "f16_instrument_menu.png"]],
        "Fig4_required_itc_and_menu.png",
        letters="ab",
    )
    P.source_ref(
        (S3_FIG / "f13_required_itc.png", "step3_analysis/step3_analysis.ipynb", "cell 40",
         "`step3_analysis/exports/t09_required_itc.csv` (model convention, regenerated 2026-08-18)"),
        (S3_FIG / "f16_instrument_menu.png", "step3_analysis/step3_analysis.ipynb", "cell t18cd001",
         "`t18_instrument_menu.csv` (from t13 + t17)"),
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
    print(f"uniform ITC vs floor: {m18['uniform_itc'].min():.2f}-{m18['uniform_itc'].max():.2f}x")

    P.caption("Fig 4", f'''
    Required ITC rates and the instrument menu. (a) The required investment-tax-credit rate by
    solve year on the model credit convention (fin_mult inversion + 10% monetization haircut;
    the placed-in-service overnight-cost-only conversion is exported per year), P50 lines with
    P5-P95 whiskers; band = current 48E range (30-50%), line = 100%. Median-world schedule
    averages run {p50.min():.2f}-{p50.max():.2f} ({p50.min()/0.30:.1f}-{p50.max()/0.30:.1f}x
    the base credit); {n100} of {len(ded)} rated case-years exceed 100% ({n100p} on the
    placed-in-service conversion). (b) The subsidy instrument menu: net-of-tax PV cost per
    instrument as a multiple of the minimum-cost floor (flat $/MW at commissioning, elective
    pay), per case; the uniform percentage credit costs
    {m18['uniform_itc'].min():.2f}-{m18['uniform_itc'].max():.2f}x the floor (haircut +
    uniform-rate oversubsidy, both removable), the capacity-standard mandate and the
    commitment bound bracket it on both sides.
    Rates are final up to two flagged legal inputs (monetization haircut; depreciation class).
    ''')
    """),

    # ---------------------------------------------------------------- Fig 5
    md(r"""
    ## Figure 5 — What it would take for the ATB cost trajectories to happen

    **What this shows.** The NREL Annual Technology Baseline (ATB) publishes
    nuclear cost trajectories that many models consume as inputs. We invert the
    question: which learning worlds, and how much deployment, would make those
    trajectories come true? Panel (a): the deployment each ATB trajectory
    requires, as a function of the learning rate, with the ATB's own paired
    deployments marked. Panel (b): maps of the parameter worlds that come
    within \$250/kW of each ATB trajectory ("feasible sets"), for large
    reactors and SMR.

    **How to read it.** In panel (a), compare each curve against its marked
    pairing: if the curve sits far above the mark, the ATB trajectory assumes
    more learning than its own deployment can deliver. In panel (b), small
    colored regions mean few defensible worlds reproduce the trajectory.

    **Key results.** Worlds that reproduce an ATB trajectory at its paired
    deployment are 0.03–1.7% of the support-restricted grid, and the best fits
    for the moderate and advanced trajectories need firm-level learning rates
    of 12.5–13.5% against the source study's own 9.5% (the conservative
    trajectories need 17.5–20%).
    The large-conservative trajectory (a 23% decline on 12 GW) is reproduced
    nowhere in the sampled support. Read as required deployment, the ATB pairings
    understate what their own cost declines demand by a factor of about 2–3.4
    (for example, large-advanced needs about 677 GW against a 199 GW pairing).
    Every model consuming ATB nuclear costs inherits these implicit bets.
    This inversion uses about 0.79 million sampled worlds per trajectory and
    zero ReEDS runs.
    """),
    code(r"""
    P.compose(
        [[MC_FIG / "atb_required_deployment_vs_lr.png"],
         [MC_FIG / "atb_feasible_maps_large.png", MC_FIG / "atb_feasible_maps_smr.png"]],
        "Fig5_atb_inversion.png",
        letters="a",   # the two feasible-map sources carry b/c themselves
        center=True,   # row widths differ; do not leave a blank corner
    )
    P.source_ref(
        (MC_FIG / "atb_required_deployment_vs_lr.png", "mc/atb_parameter_space.ipynb", "cell 22",
         "the grid inversion (~0.79M worlds/trajectory); anchors: `mc/exports/atb/required_deployment_anchors.csv`"),
        (MC_FIG / "atb_feasible_maps_large.png", "mc/atb_parameter_space.ipynb", "cell 15",
         "per-world misfit grids (`mc/exports/atb/atb_misfit_perworld.npz`), $250/kW tolerance"),
        (MC_FIG / "atb_feasible_maps_smr.png", "mc/atb_parameter_space.ipynb", "cell 15",
         "same misfit grids, SMR trajectories"),
    )

    fs = pd.read_csv(MC_EXP / "atb" / "feasible_share.csv")
    print(fs.to_string(index=False))

    P.caption("Fig 5", '''
    What the ATB nuclear cost trajectories require. (a) Deployment required to reproduce each
    ATB trajectory as a function of the learning rate, with the ATB's own paired deployment
    marked: at the source study's parameters the pairings understate required deployment by
    ~2-3.4x. (b, c) Feasible-set maps for large reactors (b) and SMR (c): parameter worlds
    within $250/kW of each trajectory at its paired deployment cover 0.03-1.7% of the
    support-restricted grid; the large-conservative trajectory clears the tolerance nowhere.
    Grid inversion over ~0.79M worlds per trajectory; no ReEDS runs.
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
    the dual paths for the ladder's end schedules, overlaid across market
    worlds. Panel (c): the large-reactor comparator against the SMR program,
    by cost-world percentile.

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
    - Only the level moves, and it moves as economics predicts: median dual
      −27% under high gas prices, +18% under low, −8% under high demand,
      +9%/−10% under cheap/dear renewables, −5% transmission-limited.
    - The large-reactor premium is not a constant. Large needs 1.4–3.5× the
      SMR dual in cheap worlds, 1.23–1.36× at the median — but at P95 the two
      technologies reach parity (0.95–1.02×): in expensive worlds both need
      the same subsidy.
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
    {len(surv)} cells — the expensive-world non-decay is generic. (b) Dual overlays for the
    ladder's end schedules across market worlds: only the level moves, in the direction
    economics predicts (median -27% to +18%). (c) Large-reactor vs SMR duals by percentile:
    the large premium is 1.4-3.5x in cheap worlds and 1.23-1.36x at the median, but the two
    technologies reach parity (0.95-1.02x) in expensive worlds.
    ''')
    """),

    # ---------------------------------------------------------------- Table 1
    md(r"""
    ## Table 1 — Case-level results: dual level, bridge shape, required rate

    **What this shows.** One row per priced run (37 runs: 25 SMR-program cases
    and 12 large-reactor comparators). Three groups of columns:
    - **Dual level** (from `t03`): number of binding years, mean binding dual,
      peak dual and its year, and the 2050 dual — all 2024\$/kW-yr.
    - **Bridge shape** (from `t04`): end-over-peak ratio, the first year the
      dual falls below half its peak (blank = never by 2050), and mandated
      years with a zero dual ("needs no subsidy" years — a legitimate outcome
      we report with the same prominence).
    - **Required ITC rate** (from `t09`, model convention): the number of rated
      years, the mean and maximum headline rate, and how many years exceed
      100%.

    **How to read a row.** Case names are `family_schedule_percentile`:
    for example `smr100_eo_p95` = the 100%-SMR program, EO schedule (400 GW),
    expensive world. Compare `end_over_peak` down the percentile column to see
    the bridge result; compare `i_model_mean` against 0.30 (the base credit)
    for the policy gap.
    """),
    code(r"""
    t03 = pd.read_csv(S3_EXP / "t03_dual_summary.csv")
    t04 = pd.read_csv(S3_EXP / "t04_bridge_metrics.csv")
    t09 = pd.read_csv(S3_EXP / "t09_required_itc.csv")

    rated = t09[t09["status"] == "rate"]
    rate_agg = (rated.groupby("case")
                .agg(rated_years=("t", "count"),
                     i_model_mean=("i_model_headline", "mean"),
                     i_model_max=("i_model_headline", "max"),
                     years_over_100pct=("i_model_headline", lambda s: int((s > 1.0).sum())))
                .reset_index())

    table1 = (t03
              .merge(t04.drop(columns=["peak_year"]), on="case")
              .merge(rate_agg, on="case", how="left"))
    table1 = table1.round({"mean_binding_dual_2024_kWyr": 0, "peak_dual_2024_kWyr": 0,
                           "dual_2050_2024_kWyr": 0, "end_over_peak": 2,
                           "i_model_mean": 2, "i_model_max": 2})
    table1.to_csv(P.OUT_EXP / "Table1_case_level_results.csv", index=False)
    print(f"exports/Table1_case_level_results.csv ({len(table1)} rows)")

    P.caption("Table 1", '''
    Case-level results for all 37 priced runs. Dual level (binding years; mean, peak, and
    2050 dual, 2024$/kW-yr), bridge-shape metrics (end-over-peak; first year below half-peak,
    blank = never by 2050; zero-dual mandated years), and the required ITC rate on the model
    convention (mean and maximum headline rate over rated years; years above 100%). Sources:
    t03_dual_summary, t04_bridge_metrics, t09_required_itc (model convention).
    ''')
    table1
    """),

    # ---------------------------------------------------------------- Table 2
    md(r"""
    ## Table 2 (reserve) — The fiscal comparison

    **What this shows.** Two present-value fiscal totals per case, 2026–2050,
    in billions of 2024 dollars, and their ratio:
    - **PV rental transfer**: the benchmark of paying the dual directly, each
      year, on the program's mandated post-2030 capacity (the fleet-inclusive
      large100 mandates are netted of the pre-existing fleet).
    - **PV ITC outlay**: what delivering the same support through the
      investment tax credit costs the treasury, gross (face value accrued to
      commissioning — invariant to the 08-18 convention revision).

    **How to read it.** The ratio column is the point: an outlay-over-rental
    ratio near 1 means the credit delivers the rental value roughly
    dollar-for-dollar; above 1 means the instrument costs more than the
    support it delivers. The net-of-tax instrument comparison (which reverses
    the gross ranking) is in the appendix notebook (SF11b).

    **Status.** The outline holds this slot in reserve: it ships if the word
    count allows the schedule facts of the introduction to stay in prose;
    otherwise the schedules table replaces it.
    """),
    code(r"""
    table2 = P.table(S3_EXP / "t12_fiscal_comparison.csv", "Table2_fiscal_comparison.csv",
                     index_col=0, round_=2)
    P.caption("Table 2", '''
    Fiscal totals per case, 2026-2050 (billion 2024$, present value): the rental-transfer
    benchmark (paying the dual directly each year on the program's post-2030 capacity),
    the gross ITC outlay (face value accrued to commissioning), and their ratio. Source:
    t12_fiscal_comparison.
    ''')
    table2
    """),

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
    every existing panel is the already-generated, checked artifact; each item
    carries a source block naming the notebook and cell that made it. Three
    figures at the end are new: they close a known re-export gap (quotable
    results that never got a static figure).

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
    ## Supplementary Notes (SN1–SN5) — pointers

    The five supplementary notes are text, not display items. They are drafted
    from these sources:

    | Note | Content | Source of record |
    |---|---|---|
    | SN1 | The Monte Carlo engine and its priors (the cost model, the copula, spillover routing, the duration model) | `z-ethan/paper plan.md` (engine sections) + `mc/mc_cost_trajectories.ipynb` |
    | SN2 | The ITC translation procedure (dual → required credit rate, 9 steps) | `z-ethan/step3_analysis/ITC calculation procedure.md` |
    | SN3 | The technology-comparison claims ledger C1–C7, with the pre-registered failures | `z-ethan/tech-comparison-notebook-spec.md` + `mc/tech_comparison.ipynb` |
    | SN4 | Case selection: joint-draw discipline and the layered coverage claim | `z-ethan/paper plan.md` (case-selection sections) + `mc/smr100_case_export.ipynb` |
    | SN5 | Validation registries (pilot forensics; output checks) | `z-ethan/step3_checks/`, `z-ethan/step4_checks/` (summaries in ST8 below) |
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
        (MC_FIG / "tornado_fincapex.png", "mc/mc_cost_trajectories.ipynb", "cell 41",
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
        (MC_FIG / "duration_medians_by_schedule.png", "mc/mc_cost_trajectories.ipynb", "cell 24",
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
        (MC_FIG / "hindcast_learning_rates.png", "mc/mc_cost_trajectories.ipynb", "cell 49",
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
    the decoupled-anchor probe). The value concentrates in the learning-rate gap
    under tight coupling and flips to the starting-cost gap when decoupled.
    These are upper bounds: no realistic noisy-signal tier is modeled.
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
    5.88% at the decoupled-anchor probe — a pre-registered failure case,
    reported as such). Early commitment forfeits little in coherent worlds.
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
    whose present value appears in Table 2. (Figure 4's panel b became the
    instrument menu on 2026-08-18, so this page now ships the rental-transfer
    exhibit.)
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
    is shown as the budget-scoring line only. State-resolved or
    dollar-denominated rates remove the oversubsidy; elective pay removes the
    haircut; the two together attain the floor.
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
    the 5-13% uniform-rate oversubsidy - are both removable (elective pay; dollar-per-MW
    denomination), so a credit can attain the floor within the tax code.
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

    # -------------------------------------------------------------- SF15-19
    md(r"""
    ## SF15–SF17 — ATB inversion detail

    **What this shows.** The detail behind Figure 5. SF15: how closely the best
    sampled worlds fit each ATB trajectory (fit envelopes). SF16: which dial
    values the near-fitting worlds require (dial marginals), per technology.
    SF17: the cross-pairing check — each ATB cost trajectory tested against
    every deployment pairing, showing the internal inconsistencies (some
    trajectories fit better under other schedules than their own).
    """),
    code(r"""
    P.show_panel(MC_FIG / "atb_fit_envelopes.png")
    P.compose(
        [[MC_FIG / "atb_dial_marginals_large.png", MC_FIG / "atb_dial_marginals_smr.png"]],
        "SF16_atb_dial_marginals.png",
        letters="",  # sources carry a/b themselves (compose letters collided
                     # with the block titles, 2026-08-17 audit)
    )
    P.show_panel(MC_FIG / "atb_cross_pairing.png")
    P.source_ref(
        (MC_FIG / "atb_fit_envelopes.png", "mc/atb_parameter_space.ipynb", "figure cells",
         "per-world misfit grids (`mc/exports/atb/`)"),
        (MC_FIG / "atb_dial_marginals_large.png", "mc/atb_parameter_space.ipynb", "figure cells",
         "feasible-set worlds (`mc/exports/atb/feasible_set_*.csv.gz`)"),
        (MC_FIG / "atb_dial_marginals_smr.png", "mc/atb_parameter_space.ipynb", "figure cells",
         "feasible-set worlds, SMR"),
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

    # ------------------------------------------------------------ gap items
    md(r"""
    ## Gap re-exports — three quotable results that had no static figure

    `mc/winner_boundary.ipynb` and `mc/npv_winner_check.ipynb` hold three
    quotable results but write no PNGs (their figures are interactive). The
    three cells below rebuild them as static figures, mirroring those
    notebooks' logic, with the exported summary tables as cross-checks.

    They need the local per-draw export `mc/exports/mc_perdraw.npz` (50 MB,
    gitignored, regenerable by `mc/mc_cost_trajectories.ipynb`). If the file
    is absent, the cells print a skip message instead of failing.

    All three use the McKinsey schedule (200 GW) as the representative
    schedule, matching the source notebooks. The two "dials" are copula
    percentiles: U0 = the learning dial (0 slow → 1 fast, both technologies
    move together), U1 = the starting-cost dial (0 cheap → 1 expensive).
    """),
    code(r"""
    import numpy as np

    NPZ = MC_EXP / "mc_perdraw.npz"
    HAVE_NPZ = NPZ.exists()
    if HAVE_NPZ:
        Z = np.load(NPZ)
        WCOLS = [str(c) for c in Z["world_columns"]]
        YEARS, DISC = Z["years"], Z["disc"]
        REP_TOK, REP_NAME = "mckinsey", "McKinsey GEP 2025"
        w = pd.DataFrame(Z[f"worlds_{REP_TOK}"], columns=WCOLS)
        d = pd.DataFrame({
            "U0": (w["lr_large"] - 0.03) / 0.09,
            "U1": (w["boak_large"] - 5250.0) / 2500.0,
            "conv_full": w["conv_full"].astype(int),
            "n_vendors": w["n_vendors"].astype(int),
        })
        # the comonotone-dial identities the source notebooks assert
        assert np.allclose(w["lr_smr"], 0.03 + 0.13 * d["U0"])
        assert np.allclose(w["boak_smr"], 5500.0 + 4500.0 * d["U1"])
        Rl, Rs = Z[f"R_{REP_TOK}_large"], Z[f"R_{REP_TOK}_smr"]
        d["m_pct"] = 200.0 * (Rl - Rs) / (Rl + Rs)   # SMR advantage, % of program cost
        d["winner"] = Z[f"winners_{REP_TOK}"].astype(str)
        assert ((d["winner"] == "large") == (Rl <= Rs)).all()
        # cross-check the exported headline: P(smr wins) for the representative schedule
        wbh = pd.read_csv(MC_EXP / "wb_headline.csv", index_col=0)
        p_smr = (d["winner"] == "smr").mean()
        assert abs(p_smr - wbh.loc[REP_NAME, "P(smr wins)"]) <= 5e-4 + 1e-9
        print(f"loaded {NPZ.name}; {REP_NAME}: P(smr wins) = {p_smr:.3f} (matches wb_headline.csv)")
    else:
        print(f"SKIP: {NPZ} not found - run mc/mc_cost_trajectories.ipynb (S10b) to regenerate.")
    """),
    md(r"""
    ### Gap 1 — The two-dial flip map

    **What this shows.** Every cost world placed on the two dials (learning,
    starting cost), colored by who wins the program. The black contour is the
    flip boundary. Large reactors win only in the slow-learning, expensive
    corner; SMR wins everywhere else.

    *Mirrors `winner_boundary.ipynb` section W4 (cell 11).*
    """),
    code(r"""
    if HAVE_NPZ:
        import matplotlib.pyplot as plt
        from matplotlib.colors import TwoSlopeNorm
        from scipy.ndimage import uniform_filter

        P.apply_style()
        CMAP_DIV = P.cmap_div()

        def binned_grid(dd, value, mask=None, nbins=20, stat="median"):
            m = np.ones(len(dd), bool) if mask is None else np.asarray(mask)
            x, y = dd["U0"].to_numpy()[m], dd["U1"].to_numpy()[m]
            v = (dd[value].to_numpy()[m] if isinstance(value, str)
                 else np.asarray(value)[m]).astype(float)
            edges = np.linspace(0, 1, nbins + 1)
            ix = np.clip(np.digitize(x, edges) - 1, 0, nbins - 1)
            iy = np.clip(np.digitize(y, edges) - 1, 0, nbins - 1)
            grid = np.full((nbins, nbins), np.nan)
            for j in range(nbins):
                for i in range(nbins):
                    sel = (ix == i) & (iy == j)
                    if sel.any():
                        grid[j, i] = (np.median(v[sel]) if stat == "median" else v[sel].mean())
            return 0.5 * (edges[:-1] + edges[1:]), grid

        def smooth(grid):
            return uniform_filter(np.where(np.isnan(grid), np.nanmedian(grid), grid),
                                  size=3, mode="nearest")

        C20, WIN = binned_grid(d, (d["winner"] == "smr").to_numpy(), stat="mean")
        _, MARGIN = binned_grid(d, "m_pct")
        X, Y = np.meshgrid(C20, C20)

        fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.5))
        for ax, grid, norm, lvl, cblab in (
                (axes[0], WIN, TwoSlopeNorm(vcenter=0.5, vmin=0, vmax=1), [0.5],
                 "share of draws SMR wins"),
                (axes[1], MARGIN,
                 TwoSlopeNorm(vcenter=0.0, vmin=-np.nanmax(np.abs(MARGIN)),
                              vmax=np.nanmax(np.abs(MARGIN))), [0.0],
                 "median margin m (%), m > 0 = SMR")):
            im = ax.imshow(grid, origin="lower", extent=[0, 1, 0, 1], cmap=CMAP_DIV,
                           norm=norm, aspect="auto", interpolation="nearest")
            ax.contour(X, Y, smooth(grid), levels=lvl, colors=[P.INK], linewidths=1.4)
            ax.set_xlabel("U0 — learning dial (0 slow -> 1 fast)")
            ax.set_ylabel("U1 — starting-cost dial (0 cheap -> 1 expensive)")
            ax.grid(False)
            plt.colorbar(im, ax=ax, shrink=0.85, label=cblab)
        axes[0].text(0.93, 0.06, "SMR", color=P.INK, fontsize=11, ha="right", fontweight="bold")
        axes[0].text(0.07, 0.94, "large", color="white", fontsize=11, va="top", fontweight="bold")
        P.panel_letter(axes[0], "a")
        P.panel_letter(axes[1], "b")
        fig.tight_layout()
        P.savefig(fig, "SFgap1_two_dial_flip_map.png")
        plt.show()
        P.caption("SF gap 1", f'''
        The winner-flip boundary on the two cost dials ({REP_NAME} schedule, 10,000 draws).
        a, share of draws the 100%-SMR program wins per bin, with the 50% contour.
        b, median cost margin (% of program cost) with the zero contour. Large reactors
        win only in the slow-learning, expensive-anchor corner.
        ''')
    else:
        print("SKIP (no mc_perdraw.npz)")
    """),
    md(r"""
    ### Gap 2 — The learning-for-cost exchange rate

    **What this shows.** The flip boundary by experience-base stratum, and the
    exchange rate it implies. Along the boundary, each percentage point of
    SMR's learning-rate edge over large buys a fixed amount of tolerable
    starting-cost premium — about \$800/kW per point. Under the full-stock
    convention (crediting the ~140-unit legacy fleet to large's experience
    base) the boundary nearly vanishes: diluted learning weakens large's case.

    *Mirrors `winner_boundary.ipynb` sections W5/W10 (cells 13, 26); the
    break-even table is the exported `wb_breakeven.csv`.*
    """),
    code(r"""
    if HAVE_NPZ:
        import matplotlib.pyplot as plt

        def boundary_curve(dd, mask, nbins=12):
            cc, g = binned_grid(dd, "m_pct", mask=mask, nbins=nbins)
            gs = smooth(g)
            u1s = np.full(len(cc), np.nan)
            for i in range(len(cc)):
                col = gs[:, i]
                if np.nanmin(col) < 0 < np.nanmax(col):
                    ok = ~np.isnan(col)
                    u1s[i] = np.interp(0.0, col[ok][::-1], cc[ok][::-1])
            return cc, u1s

        STRATA = [("tiny-base, 4-5 vendors", (d["conv_full"] == 0) & (d["n_vendors"] <= 5), P.C_TINY, "-"),
                  ("tiny-base, 6-8 vendors", (d["conv_full"] == 0) & (d["n_vendors"] >= 6), P.C_TINY, "--"),
                  ("full-stock, 4-5 vendors", (d["conv_full"] == 1) & (d["n_vendors"] <= 5), P.C_FULL, "-"),
                  ("full-stock, 6-8 vendors", (d["conv_full"] == 1) & (d["n_vendors"] >= 6), P.C_FULL, "--")]

        fig, ax = plt.subplots(figsize=(7.4, 5.2))
        cc_all, u1_all = boundary_curve(d, None)
        ax.plot(cc_all, u1_all, color=P.MUTED, lw=3, alpha=0.8, label="all draws pooled")
        for name, mask, c, ls in STRATA:
            cc, u1s = boundary_curve(d, mask.to_numpy())
            if (~np.isnan(u1s)).sum() < 2:
                ax.plot([], [], color=c, ls=ls, lw=2, label=f"{name}: no boundary in range")
            else:
                ax.plot(cc, u1s, color=c, ls=ls, lw=2, label=f"{name} (n={int(mask.sum()):,})")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.set_xlabel("U0 — learning dial")
        ax.set_ylabel("U1 — starting-cost dial")
        ax.legend(fontsize=8, loc="lower right")
        fig.tight_layout()
        P.savefig(fig, "SFgap2_exchange_rate_boundary.png")
        plt.show()

        # the exchange rate: slope of the tiny-base boundary
        cc_tb, u1_tb = boundary_curve(d, (d["conv_full"] == 0).to_numpy())
        ok = ~np.isnan(u1_tb)
        slope = np.polyfit(cc_tb[ok], u1_tb[ok], 1)[0]
        xrate_gap = 2000 * slope / 4.0   # $/kW premium per pp of SMR's lr edge over large
        xrate_lr = 2000 * slope / 9.0    # per pp of the industry-wide learning rate
        print(f"exchange rate (tiny-base boundary slope): ~{xrate_gap:,.0f} $/kW of tolerable"
              f" SMR anchor premium per pp of SMR's learning-rate edge"
              f" (~{xrate_lr:,.0f} $/kW per pp of the shared industry rate)")
        print("cross-check against the exported break-even table:")
        print(pd.read_csv(MC_EXP / "wb_breakeven.csv").to_string(index=False))
        P.caption("SF gap 2", f'''
        The flip boundary by experience-base stratum ({REP_NAME} schedule; SMR wins below
        each line). Along the tiny-base boundary, each percentage point of SMR's
        learning-rate edge buys ~{xrate_gap:,.0f} $/kW of tolerable starting-cost premium.
        Under the full-stock convention the boundary nearly vanishes: crediting the legacy
        fleet dilutes large's learning progression and weakens its case.
        ''')
    else:
        print("SKIP (no mc_perdraw.npz)")
    """),
    md(r"""
    ### Gap 3 — Does the winner survive non-capital costs? (NPV-margin scatter)

    **What this shows.** The winner analysis above ranks programs by capital
    cost only. This check adds the 30-year present value of fixed and variable
    operations costs and fuel, per draw, and re-ranks. Each point is one world:
    the capital-only margin against the full-NPV margin. Points hug the
    45-degree line: operations costs nudge every margin but flip only
    near-ties, and every flip starts inside the 2% close-call band.

    *Mirrors `npv_winner_check.ipynb` sections N2–N4 (cells 6, 8, 11); the
    summary table is the exported `npv_winner_summary.csv`. The operations-cost
    stack is rebuilt here from in-repo inputs (ATB plant characteristics,
    AEO uranium prices, the deflator), tied to the cost dial exactly as there:
    fixed and variable O&M move with U1 from the ATB advanced to conservative
    columns (the comonotone convention), and the capacity factor is the exported
    replication value.*
    """),
    code(r"""
    if HAVE_NPZ:
        import matplotlib.pyplot as plt

        # --- rebuild the non-CAPEX stack (mirrors npv_winner_check cell 6) ---
        nws = pd.read_csv(MC_EXP / "npv_winner_summary.csv")
        CF = float(nws["CF"].iloc[0])
        d_real = float(DISC[-1] / DISC[-2])
        EVAL_YEARS = 30
        ks = np.arange(1, EVAL_YEARS + 1)
        pvf = float((d_real ** -ks).sum())

        def atb_row(tech, scen):
            f = P.REPO / "inputs" / "plant_characteristics" / f"{tech}_ATB_2024_{scen}.csv"
            return pd.read_csv(f).set_index("t").loc[2030]

        TECH_FILE = {"large": "nuclear", "smr": "nuclear-smr"}
        OM = {}
        for t in ["large", "smr"]:
            adv, con, mod = (atb_row(TECH_FILE[t], s) for s in
                             ["advanced", "conservative", "moderate"])
            OM[t] = {"fom": (float(adv["fom"]), float(con["fom"])),
                     "vom": (float(adv["vom"]), float(con["vom"])),
                     "hr": float(mod["heatrate"])}

        defl = pd.read_csv(P.REPO / "inputs" / "financials" / "deflator.csv")
        defl.columns = ["year", "deflator"]
        defl = defl.set_index("year")["deflator"]
        U2022 = float(defl.loc[2025] / defl.loc[2022])
        uran = pd.read_csv(P.REPO / "inputs" / "fuelprices" /
                           "uranium_AEO_2026_baseline.csv").set_index("year")["cost"]
        Pu = (uran * U2022).reindex(range(2024, int(YEARS.max()) + EVAL_YEARS + 1)).ffill()

        MWH_PER_KWYR = 8.760

        def fuel_pv(tech):
            out = np.zeros(len(YEARS))
            for j, t in enumerate(YEARS):
                out[j] = (Pu.loc[t + 1: t + EVAL_YEARS].to_numpy() * (d_real ** -ks)).sum()
            return CF * MWH_PER_KWYR * OM[tech]["hr"] * out

        def om_npv(tech, U1):
            lo_f, hi_f = OM[tech]["fom"]
            lo_v, hi_v = OM[tech]["vom"]
            fom = lo_f + np.asarray(U1)[:, None] * (hi_f - lo_f)
            vom = lo_v + np.asarray(U1)[:, None] * (hi_v - lo_v)
            return pvf * (fom + CF * MWH_PER_KWYR * vom) + fuel_pv(tech)[None, :]

        w_t = Z[f"gw_additions_{REP_TOK}"] / DISC
        m_capex = d["m_pct"].to_numpy()
        Rn = {}
        for t in ["large", "smr"]:
            Rn[t] = Z[f"R_{REP_TOK}_{t}"] + om_npv(t, d["U1"].to_numpy()) @ w_t
        m_npv = 200.0 * (Rn["large"] - Rn["smr"]) / (Rn["large"] + Rn["smr"])
        win_npv = np.where(Rn["large"] <= Rn["smr"], "large", "smr")

        # cross-check the exported summary for the representative schedule
        row = nws.set_index("schedule").loc[REP_NAME]
        assert abs((win_npv == "smr").mean() - row["P(smr) npv"]) <= 5e-4 + 1e-9
        fl = int(((d["winner"] == "large") & (win_npv == "smr")).sum())
        fs = int(((d["winner"] == "smr") & (win_npv == "large")).sum())
        assert (fl, fs) == (int(row["flips large->smr"]), int(row["flips smr->large"]))
        print(f"QA green: P(smr) npv and flip counts match npv_winner_summary.csv "
              f"({fl} large->smr, {fs} smr->large)")

        cls = np.select(
            [(d["winner"] == "smr") & (win_npv == "smr"),
             (d["winner"] == "large") & (win_npv == "large"),
             (d["winner"] == "large") & (win_npv == "smr"),
             (d["winner"] == "smr") & (win_npv == "large")],
            ["smr both", "large both", "flip to smr", "flip to large"])

        fig, ax = plt.subplots(figsize=(6.4, 5.6))
        for name, color, alpha, size, z in [
                ("smr both", P.COL["smr"], 0.18, 6, 2),
                ("large both", P.COL["large"], 0.18, 6, 2),
                ("flip to smr", P.COL["smr"], 1.0, 24, 4),
                ("flip to large", P.COL["large"], 1.0, 24, 4)]:
            sel = cls == name
            ax.scatter(m_capex[sel], m_npv[sel], s=size, lw=0, color=color, alpha=alpha,
                       zorder=z, label=f"{name} ({int(sel.sum()):,})")
        lim = np.nanpercentile(np.abs(np.r_[m_capex, m_npv]), 99.5)
        ax.plot([-lim, lim], [-lim, lim], color=P.EDGE_C, lw=1, zorder=1)
        ax.axhline(0, color=P.EDGE_C, lw=1)
        ax.axvline(0, color=P.EDGE_C, lw=1)
        ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim)
        ax.set_xlabel("margin, capital cost only (%) — SMR wins right of 0")
        ax.set_ylabel("margin, full NPV (%)")
        ax.legend(fontsize=8, loc="upper left")
        fig.tight_layout()
        P.savefig(fig, "SFgap3_npv_margin_scatter.png")
        plt.show()
        P.caption("SF gap 3", f'''
        Capital-only vs full-NPV winner margins ({REP_NAME} schedule). Adding the 30-year
        present value of O&M and fuel (tied to the cost dial) shifts every margin slightly
        and flips only near-ties: {fl} draws flip to SMR and {fs} to large out of 10,000,
        all starting inside the 2% close-call band.
        ''')
    else:
        print("SKIP (no mc_perdraw.npz)")
    """),

    # ---------------------------------------------------------------- ST1-8
    md(r"""
    ## Supplementary tables (ST1–ST8)

    Each table below is loaded from its checked export, displayed, and
    re-exported to this notebook's `exports/` folder (Nature Energy ships
    complex tables as csv). The source path in each cell is the file of record.
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

    The full versions of Table 1's first two column groups: t03 (dual levels)
    and t04 (bridge-shape metrics) for all 37 runs.
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
