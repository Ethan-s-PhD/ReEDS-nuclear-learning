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
import re

import pandas as pd

import paperlib as P
from paperlib import (MC_FIG, MC_EXP, S3_FIG, S3_EXP, S4_FIG, S4_EXP, S3C_EXP,
                      S4C_EXP, ITCFB_FIG, ITCFB_EXP, ITCFBM_FIG, ITCFBM_EXP,
                      BD_FIG, BD_EXP, IC_FIG, IC_EXP, RD_FIG, RD_EXP, RD2_FIG, RD2_EXP,
                      MT_FIG, MT_EXP, LIT_FIG, LIT_EXP, VOI_FIG, VOI_EXP)

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
| **Map error band (E6)** | How far the per-year requirement map may be off. The map is fit to 66 model-solved cost worlds (11 per schedule: the 5th, 25th, 50th, 75th and 95th percentile worlds plus six placed to fill the corners of the cost-path plane; batch 6). Hiding one solved world at a time and predicting its rates from the others gives the leave-one-out error; E6 is its density-weighted 90th percentile, rounded up to one statutory rate point, and every fan and mask is shown at the base case and at rate ∓ E6. The pre-refit five-anchor map carried the bill band E5 (18% of the bill), which the detection analysis (SF58) still uses. |
| **Learning rate** | The percent cost drop each time total built capacity doubles. Example: a 10% learning rate means the second 10 GW costs 10% less per kW than the first 10 GW. |
| **Learning curve** | The cost path that a learning rate produces as capacity grows. |
| **OCC (overnight capital cost)** | The cost to build a plant if it could be built "overnight" — no construction-period interest. Units: \$/kW. |
| **Financed capex** | OCC plus the interest that accrues during the construction years. Long builds raise it. It is the cost basis of Fig 2b/c, and the basis on which Fig 3 and Fig 5 state the required support (the shadow price capitalized over the model's 30-year evaluation window, in \$/kW). |
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
| **EVSI (expected value of sample information)** | What the noisy costs of the units completed so far are worth to the decision, computed before seeing them; never more than EVPI. |
| **Bayes risk** | The expected loss of a decision rule, averaged over the cost worlds; the Bayes rule is the rule with the smallest Bayes risk. |
| **LP / reduced cost** | ReEDS solves a linear program (LP) — a cost-minimization with linear rules. A builder's "reduced cost" is its cost disadvantage at the optimum; zero means it is competitive at the margin. |
| **Credit path** | A declared dollars-per-kW credit for each build year (the rate-design analysis's object). "Schedule" always means a deployment schedule in this notebook, never a credit path. |
| **Demonstration window** | The build years through 2038, one common window end for every schedule, in which grant-type federal cost share to first units (the ARDP model) is the assumed vehicle for support above the statutory rate cap; after the window the instrument is the capped credit alone. By 2038 all but a few percent of the worlds that ever become credit-feasible have done so, in every schedule at both ceilings (EIA, whose builds start in 2038, is the exception; the shares are computed in Table 2 from the refit map, `rate_design2` m23; the five-anchor basis of the decision is `voi/` p36). The per-schedule expected-loss minimizers of the decision-value analysis stay in SF56/ST19. The registered rate_design kills and the market-world transfer stay on the earlier fixed 2035 window. |
"""

# ============================================================================
# MAIN NOTEBOOK
# ============================================================================

main_cells = [
    md(r"""
    # Main-paper display items — figures and tables with explanations

    **Purpose.** This notebook assembles the main-text display items of the paper
    ("The learning-consistent required subsidy", outline: `z-ethan/paper_outline.md`):
    five figures and two tables — seven display items since the draft-v3 cut of
    2026-09-10 (the coauthor review: the technology-choice figure moved to SF57, the
    cost-of-detection figure to SF58, and the three-anchor cost-gap figure to SF59; the
    cost gap became figure 3 on the batch-6 refit map). Renaming on 2026-09-10: old figure 4
    → SF59 (replaced by the new figure 3), old figure 6 → figure 4, old figure 7 → figure 5;
    every cross-reference in this notebook and the SI notebook uses the new numbers.
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
    ## Figure 1 — The learning engine against the literature's cost projections

    **What this shows.** (New Fig 1, Ethan 09-08; two-panel version 09-09 —
    the coauthors judged the experience-accounting split too detailed for the
    main text, so it stays in the SI; the ATB-placement figure this replaces is
    SF42.) One panel per technology, one y axis. The coloured fans are the
    engine: for each amount of post-2030 building, the 2050 overnight cost that
    the sampled learning worlds deliver when the learning rate is restricted to
    each technology's support, the anchor cost is drawn across its prior, and
    every other input varies jointly — the experience accounting included
    (fresh-start and legacy-fleet-credited worlds pooled in the equal numbers
    the Monte Carlo samples; the split is `lit_comparison` e10 / SF42) — as
    P5–P95 and P25–P75 bands and the median world. The dashed lines are the
    lowest and highest cost any supported world reaches at that build with the
    anchor anywhere in its prior: the bounds of what the engine can produce, so
    a published point outside them is one no sampled world can reach. The grey lines and markers
    are every published projection that pairs a cost with a unit count, drawn
    at its own cumulative build in 2022 dollars and deliberately unlabeled: the
    ATB source's three trajectories per technology, DOE Liftoff, MIT ANP-201,
    INL's cost pathways, Stewart & Shirvan's eight architectures, the twelve
    Breakthrough scenario curves, the IEA 2025 scenario paths, Vanatta et al.'s
    industrial designs, and the realized Vogtle and quoted Darlington projects
    (16 large and 33 SMR series; the out-of-scope microreactor, the Steigerwald parity illustration and the INL review range band are omitted).
    Dotted grey horizontals are published values with no deployment attached
    (EIA, EPRI, IEA/NEA, the IEA large-reactor path). Hollow markers are first-
    and second-of-a-kind values. The ATB source's 2030 anchors sit at zero
    post-2030 build, off a log axis, so they are drawn at 0.1 GW (Ethan, 09-09:
    the source's own SMR curves start near 0.83 units, about 0.25 GW). The literature comparison notebook identifies every series in its
    grouped figures and scores each one against the engine (`lit_comparison`,
    gates G0–G3 + G1b).

    **How to read it.** The fan is what the paper's learning worlds allow at a
    given cumulative build; the grey cloud is what the literature has claimed.
    Where the cloud sits inside the fan, the published projections are
    reachable by the sampled worlds at that build; where it sits below the fan,
    they need faster learning, an earlier anchor, or pooled experience that the
    engine does not sample.

    **Key results.** The literature occupies the lower half of the engine's fan
    for both technologies. For large reactors nearly every published point below
    about 15 GW lies under the median world, and the bottom-up chains (Stewart &
    Shirvan's 3,000–3,500 $/kW at 10–15 GW) run along or below the P5 edge. For
    SMRs the cloud straddles the P25–P75 band to about 10 GW, then falls to the
    fan's lower edge beyond 50 GW, where the Breakthrough and IEA 2050 end
    points sit at 2,000–4,000 $/kW. The gap is the paper's designed
    difference: the engine prices each vendor's next unit from its second unit
    in 2030 and divides experience among vendors, while most published curves
    start at unit one and pool the whole program (SN7; the per-series scoring in
    the literature comparison).
    """),
    code(r"""
    P.compose(
        [[LIT_FIG / "e11_engine_vs_literature_2panel.png"]],
        "Fig1_engine_vs_literature.png",
        letters="",  # the source carries a (large) and b (SMR)
    )
    P.source_ref(
        (LIT_FIG / "e11_engine_vs_literature_2panel.png", "lit_comparison/lit_comparison.ipynb",
         "cell e11 (added 09-09; the four-panel split by experience accounting is cell e10)",
         "the closed-form 2050 evaluator over the support-restricted Part-2 grid (fans) and "
         "`lit_comparison/exports/c02_points_2022usd.csv` (every literature series, 2022$; "
         "digitized series via `_digitize_figures.py` / `_digitize_figures_b.py`, gates G1/G1b)"),
    )
    c02 = pd.read_csv(LIT_EXP / "c02_points_2022usd.csv")
    c99 = pd.read_csv(LIT_EXP / "c99_verdict.csv")
    assert (c99[c99.kind == "gate"]["result"] == "PASS").all(), c99
    paired = c02[c02.paired]
    for tech in ("large", "smr"):
        sub = c02[c02.tech == tech]
        print(f"{tech}: {sub[sub.paired]['series_id'].nunique()} paired series from "
              f"{sub[sub.paired]['source_id'].nunique()} sources, "
              f"{sub[~sub.paired]['series_id'].nunique()} unpaired reference values")
    print("sources:", ", ".join(sorted(paired["source_id"].unique())))

    P.caption("Fig 1", '''
    The learning engine against the published nuclear cost projections, for large reactors (a)
    and SMRs (b). Coloured fans: the 2050 overnight cost delivered across the sampled learning
    worlds restricted to each technology's learning-rate support, with the anchor cost drawn
    across its prior and every other input varying jointly, experience accounting included
    (5th-95th and 25th-75th percentile bands, median world; dashed lines, the lowest and highest
    cost any supported world reaches, the bounds of what the engine can produce), as a function
    of cumulative capacity built after 2030. Grey: every published projection that pairs a cost with a unit
    count - the ATB source's three trajectories per technology, DOE Liftoff, MIT ANP-201, INL's
    cost pathways, Stewart & Shirvan 2022, Breakthrough 2022, IEA 2025, Vanatta et al. 2024, and
    the realized Vogtle and quoted Darlington projects (16 large and 33 SMR series) - each at its
    own cumulative build in 2022 dollars; hollow markers are first- and second-of-a-kind values;
    dotted lines are published values with no deployment attached (EIA, EPRI, IEA/NEA, the IEA
    large-reactor path); the ATB source's 2030 anchors, which sit at zero post-2030 build, are
    drawn at 0.1 GW. The split by experience accounting, the ATB 2050
    targets at their paired deployments and the shares of worlds that reach them are in SF42 and
    the literature-comparison SI, which identifies every series.
    ''')
    """),

    # ---------------------------------------------------------------- Fig 2
    md(r"""
    ## Figure 2 — The six schedules, and the financed cost worlds two of them imply

    **Recomposed 2026-09-09 (Ethan's figure revisions).** Panel (a) is the
    new-nuclear schedule alone: the additions-basis mandate each schedule
    becomes (the fleet-inclusive large-reactor comparator panel and the
    program wording left the figure — source `f01b`). Panels (b) and (c)
    keep two schedules only — Abou-Jaoude (134 GW) and the 2025 Executive
    Order (400 GW) — on ONE y axis shared by all four panels, and read in
    **financed capital cost** instead of overnight cost: the overnight cost
    times the construction-financing multiplier at the draw's own learned
    build duration and the non-IDC financing rest (ReEDS's
    `cost_cap_fin_mult_noITC`, ported in the MC's S7), so construction
    duration and financing are inside the number; 2022 dollars, no credit.
    The six-schedule overnight-cost fans stay in the MC notebook
    (`mc/figures/occ_fans_{large,smr}.png`) as the analysis record.

    **What this shows.** Panel (a): the six deployment schedules, from 117 GW
    (EIA) to 400 GW (2025 Executive Order) of new capacity by 2050, one per
    source type: modeled projection, study assumption, intergovernmental
    outlook, consultancy outlook, pledge, policy aspiration. Panels (b) and
    (c): for a moderate and the most ambitious schedule, the fan of financed
    capital cost paths that our Monte Carlo produces **conditional on that
    schedule happening** — large reactors in (b), SMR in (c).

    **How to read it.** Each fan is a distribution, never a single projection.
    The band spans the 5th to 95th percentile of 10,000 joint draws; the middle
    line is the median. Each fan begins in 2025 at that draw's first-of-a-kind
    premium (a plot-only backcast of the FOAK→BOAK approach, financed at the
    draw's own 2025–2029 multiplier) and descends into its 2030 anchor cost;
    the schedules only separate the fans after 2030, when the US build
    programs begin. More ambitious schedules buy more learning, so their fans
    sit lower. The shared axis makes the two technologies comparable at a
    glance: SMR financed cost starts higher (the anchor prior and the FOAK
    premium) and falls further under the ambitious schedule.

    **Key results** (computed in the cell below from the MC's plotted
    percentiles). Median 2050 SMR financed capital cost falls from about
    \$6,800/kW under the Abou-Jaoude schedule to about \$4,600/kW under the
    EO schedule; large reactors from about \$8,300 to \$6,700/kW. The wide
    bands are the point: a deployment target does not pin down a cost; it
    pins down a distribution.

    **Discipline to keep in every caption.** These are conditional cost
    trajectories. Each fan answers: "if this schedule happens, what may costs
    do?" It never answers: "what will costs be?"
    """),
    code(r"""
    P.compose(
        [[S3_FIG / "f01b_new_nuclear_trajectories.png"],
         [MC_FIG / "fincapex_fans_large.png"],
         [MC_FIG / "fincapex_fans_smr.png"]],
        "Fig2_schedules_and_cost_fans.png",
    )
    P.source_ref(
        (S3_FIG / "f01b_new_nuclear_trajectories.png", "step3_analysis/step3_analysis.ipynb",
         "cell f01b-new-nuclear (added 2026-09-09 by `_edit_20260909_capex_panels.py`)",
         "`inputs/nuclear_learning/nuclear_cap_trajectory_*.csv` (the additions-basis mandate files ReEDS reads)"),
        (MC_FIG / "fincapex_fans_large.png", "mc/mc_cost_trajectories.ipynb",
         "cell fincapex-fans-aj-eo (added 2026-09-09 by `_edit_20260909_fincapex_fans.py`)",
         "the in-memory MC results (10,000 joint draws per schedule; fincapex = OCC x ccmult(learned duration) "
         "x fin_mult_rest, 2022$, no ITC); plotted percentiles: `mc/exports/fincapex_fans_aj_eo_percentiles.csv`"),
        (MC_FIG / "fincapex_fans_smr.png", "mc/mc_cost_trajectories.ipynb", "cell fincapex-fans-aj-eo",
         "same MC results, SMR arrays"),
    )

    # Caption numbers computed from the plotted percentiles, so text and data cannot drift.
    fin = pd.read_csv(MC_EXP / "fincapex_fans_aj_eo_percentiles.csv", header=[0, 1, 2], index_col=0)
    assert set(fin.columns.get_level_values(1)) == {"abou_jaoude", "eo2025"}
    # the engine's own percentile export agrees with the plotted values from the 2030 anchor on
    eng = pd.read_csv(MC_EXP / "mc_financed_capex_percentiles_by_schedule.csv", header=[0, 1, 2], index_col=0)
    for tech in ("large", "smr"):
        for tok in ("abou_jaoude", "eo2025"):
            assert abs(fin.loc[2050, (tech, tok, "P50")] - eng.loc[2050, (tech, tok, "P50")]) < 0.6, (tech, tok)
    p50 = {(tech, tok): float(fin.loc[2050, (tech, tok, "P50")])
           for tech in ("large", "smr") for tok in ("abou_jaoude", "eo2025")}
    lo = fin.loc[2050, (slice(None), slice(None), "P5")].min()
    hi = fin.loc[2050, (slice(None), slice(None), "P95")].max()
    ymax = fin.xs("P95", axis=1, level=2).max().max()
    print("2050 P50 financed capital cost (2022$/kW):", {k: round(v) for k, v in p50.items()})
    print(f"2050 P5-P95 span across the four panels: {lo:,.0f} - {hi:,.0f} $/kW; shared axis top >= {ymax:,.0f}")

    P.caption("Fig 2", f'''
    Deployment schedules and the financed cost worlds two of them imply.
    (a) Six new-nuclear deployment schedules for the United States, 117-400 GW of new
    capacity by 2050, one per provenance class; the paper prices these schedules and does
    not rank them. (b, c) Financed capital cost fans (overnight cost plus construction-period
    financing at each draw's own learned build duration; 2022$, no credit; 5th-95th and
    25th-75th percentiles of 10,000 joint Monte Carlo draws; line = median) conditional on
    the Abou-Jaoude (134 GW) and 2025 Executive Order (400 GW) schedules, for large reactors
    (b) and SMR (c); both panel pairs share one y axis. Fans start in 2025 at each draw's backcast
    first-of-a-kind premium and pass through the drawn 2030 anchor cost. Median 2050 SMR
    financed cost falls from {p50[("smr", "abou_jaoude")]:,.0f} $/kW (134 GW schedule) to
    {p50[("smr", "eo2025")]:,.0f} $/kW (400 GW schedule); large reactors from
    {p50[("large", "abou_jaoude")]:,.0f} to {p50[("large", "eo2025")]:,.0f} $/kW. Every fan
    is conditional on its schedule; none is a projection.
    ''')
    """),

    # ---------------------------------------------------------------- Fig 3
    md(r"""
    ## Figure 3 — The cost gap: how much cheaper new nuclear must become, across the cost worlds

    **New 2026-09-10 (draft v3; the batch-6 refit).** The coauthor asked to be
    talked through the old version of this figure. Here is the walk-through.

    **The question.** For each deployment schedule, and for each year in which
    it adds capacity, how much lower would the financed capital cost of that
    year's new plants have to be for them to be built without support? That
    number is the cost gap. It is what the subsidy has to close.

    **Where the number comes from.** ReEDS is run with the schedule as a build
    mandate. The mandate's shadow price is the model's own statement of the
    gap for the marginal plant in that year, on the financed basis (overnight
    cost × the financing multiplier). We ran that solve for 66 cost worlds
    (11 per schedule: the 5th, 25th, 50th, 75th and 95th percentile worlds of
    program cost, plus six worlds per schedule placed to fill the corners of
    the plane spanned by each world's 2031 cost and its 2050-to-2031 cost
    ratio — the third and last model batch). Those 66 solves are exact. A requirement
    map, fitted to them, then gives every one of the 10,000 cost worlds per
    schedule its gap in every build year: the map family, the leave-one-out
    error and the selection rule were registered before the batch ran
    (`rate_design/methods.md` v2.4). The leave-one-out error (hide one solved
    world, predict its rates from the others) sets the band E6: its 90th
    percentile with each solved world counted in proportion to how many of
    the 10,000 worlds lie nearest to it, rounded up to one rate point. The
    fit gate registered for the map (every schedule within 4 points on
    average) did not pass: the EIA schedule's own error is about 14 points at
    the 90th percentile, against 6–10 for the others, so the band is the
    pooled one and the EIA panel is the least certain (`m31_verdict.csv`,
    gate GM1).

    **What is drawn.** One panel per schedule; x = build year; y = the
    required reduction in financed capital cost, in 2024 dollars per kW of
    that year's new capacity, for one plant built in that year. Each world is
    one path; the fan shows the 5th, 25th, 50th, 75th and 95th percentiles
    across the 10,000 worlds (light band, dark band, solid median). The thin
    dotted lines redraw the median at the two ends of the band E6. The
    dashed vertical is the common demonstration-window end (2038; Fig 4).
    Every value is shown three statutory rate points below the mapped
    requirement, the paper's display allowance (the feed-back runs showed that
    the credit which delivers the build lies below the requirement the shadow
    prices imply, SF24a); the registered one-point values are in ST14k–o.

    **How to read it.** Wherever a fan sits above zero, that share of worlds
    needs support in that year. The median world's gap falls over time as the
    fleet learns; the expensive edge falls much less. The wall figure (Fig 4)
    is this same quantity divided by each world's own build cost — the gap as
    a share of plant cost, which is what a tax credit pays.

    **Key results** (computed in the cell below).
    """),
    code(r"""
    P.compose(
        [[RD2_FIG / "n31_dollar_fans_cut.png"]],
        "Fig3_cost_gap_fans.png",
        letters="",  # homogeneous small multiples: not lettered
    )
    P.source_ref(
        (RD2_FIG / "n31_dollar_fans_cut.png", "rate_design2/rate_design2_v2.ipynb",
         "figures cell (n31; the DISPLAY_CUT display twin)",
         "`m20_requirement_fans_cut.csv` (need_kw rows: (mapped rate - 3 points) x each world's own build cost, 2024$/kW; "
         "the chosen map of `m12_selection.csv` fit on the 66 solved anchors; band E6 from `m13_band_e6.csv`)"),
    )

    m12 = pd.read_csv(RD2_EXP / "m12_selection.csv")
    m13 = pd.read_csv(RD2_EXP / "m13_band_e6.csv")
    m31 = pd.read_csv(RD2_EXP / "m31_verdict.csv").set_index("name")
    CHOSEN, E6_PTS, GM1 = m12["chosen"].iloc[0], int(m12["E6_pts"].iloc[0]), m12["GM1"].iloc[0]
    _p90 = m13.set_index("ab")["p90"]
    eia_p90, other_p90 = float(_p90["eia"]), (float(_p90.drop("eia").min()), float(_p90.drop("eia").max()))
    assert m12["n_anchors"].iloc[0] == 66 and E6_PTS == int(m13["E6_pts"].iloc[0])
    assert m31.loc["R0", "result"] == "PASS" and m31.loc["rate-map-basis", "result"] == CHOSEN
    m20 = pd.read_csv(RD2_EXP / "m20_requirement_fans.csv")
    m20c = pd.read_csv(RD2_EXP / "m20_requirement_fans_cut.csv")
    for d in (m20, m20c):
        assert {"schedule", "band", "quantity", "year", "p05", "p25", "p50", "p75", "p95", "ref", "censored"} <= set(d.columns)
        assert set(d["schedule"]) == set(P.SCHEDULES) and set(d["band"]) == {"base", "lo", "hi"} and set(d["quantity"]) == {"rate", "need_kw"}
        assert ((d["p05"] <= d["p25"] + 1e-9) & (d["p25"] <= d["p50"] + 1e-9) & (d["p50"] <= d["p75"] + 1e-9) & (d["p75"] <= d["p95"] + 1e-9)).all()
    assert len(m20) == len(m20c)
    need = m20c[(m20c["band"] == "base") & (m20c["quantity"] == "need_kw")]
    rate_b, rate_c = [d[(d["band"] == "base") & (d["quantity"] == "rate")].reset_index(drop=True) for d in (m20, m20c)]
    _d = (rate_b["p50"] - rate_c["p50"])[rate_c["p50"] > 0]
    CUT = round(float(_d.median()), 4)
    assert CUT == 0.03 and (abs(_d - CUT) < 1e-3).all(), (CUT, _d.describe())
    first = need.sort_values("year").groupby("schedule").first()
    last = need[need["year"] == 2050].set_index("schedule")
    print(f"map {CHOSEN}, 66 anchors, E6 = {E6_PTS} points (GM1 {GM1}); display cut {CUT:.0%} of basis")
    print("median-world gap, first build year -> 2050 (2024$/kW):",
          {ab: (int(round(first.loc[ab, 'p50'], -1)), int(round(last.loc[ab, 'p50'], -1))) for ab in P.SCHEDULES})
    print("expensive edge (p95) at 2050:", {ab: int(round(last.loc[ab, 'p95'], -1)) for ab in P.SCHEDULES})
    print("cheap edge (p05) at 2050:", {ab: int(round(last.loc[ab, 'p05'], -1)) for ab in P.SCHEDULES})
    above0 = need.groupby("schedule").apply(lambda g: float((g["p05"] > 0).mean()))
    print("share of build years whose p05 edge is above zero:", above0.round(2).to_dict())
    peak = need.loc[need["p95"].idxmax()]
    med50_lo, med50_hi = last["p50"].min(), last["p50"].max()
    p95_50_lo, p95_50_hi = last["p95"].min(), last["p95"].max()
    decay = (last["p50"] / first["p50"]).replace([float("inf")], float("nan"))
    print("median 2050/first-year ratio:", decay.round(2).to_dict())

    P.caption("Fig 3", f'''
    The cost gap across the cost worlds. For each schedule and build year: the required
    reduction in financed capital cost (2024$/kW of that year's new capacity) that makes the
    mandated builds competitive without support, across the 10,000 cost worlds — the 5th–95th
    (light) and 25th–75th (dark) percentile bands and the median world (solid); thin dotted
    lines, the median at the two ends of the map's error band (∓{E6_PTS} statutory rate
    points, the leave-one-out band E6 of the requirement map fit on 66 model-solved worlds,
    11 per schedule; the registered fit gate GM1 did not pass — the EIA panel's own
    leave-one-out 90th-percentile error is {eia_p90:.0f} points against
    {other_p90[0]:.0f}–{other_p90[1]:.0f} for the others, so the pooled band understates it there);
    dashed vertical, the common demonstration-window end (2038, Fig 4).
    Every value is shown {CUT:.0%} of plant cost below the mapped requirement (the display
    allowance for the finding that the credit which delivers the build lies below the
    shadow-price requirement; SF24a); registered one-point values: ST14k. The median world's
    gap in 2050 runs {med50_lo:,.0f}–{med50_hi:,.0f} $/kW across schedules
    ({", ".join(f"{P.SCHED_SHORT[ab]} {decay[ab]:.0%}" for ab in P.SCHEDULES if pd.notna(decay[ab]))} of its
    first-year value); the expensive edge (95th percentile) is {p95_50_lo:,.0f}–{p95_50_hi:,.0f}
    $/kW in 2050 and peaks at {peak["p95"]:,.0f} $/kW ({P.SCHED_SHORT[peak["schedule"]]},
    {int(peak["year"])}). The gap includes the marginal build's O&M and market-value terms, so
    a capital-cost cut is one way to close it; as an overnight-cost cut it is about 1.27x
    smaller (the financing multiplier). Conditional on the schedule; not a projection. The
    solved gaps at the anchor worlds themselves are SF59.
    ''')
    """),

    # ---------------------------------------------------------------- Fig 4
    md(r"""
    ## Figure 4 — The statutory wall: what caps can and cannot buy

    **Repointed 2026-09-10 to the batch-6 refit map** (`rate_design2_v2.ipynb`:
    the registered family fit on 66 solved anchor worlds, band E6 = the
    density-weighted leave-one-out p90, additive in rate points; the five-anchor
    map and its ±E5 band are the pre-refit record, SF38/ST14). Renumbered figure 6
    → figure 4 in the draft-v3 cut. Panels and encodings unchanged.

    Recomposed 2026-08-24 (option B), renumbered 2026-08-26, panel (a)
    swapped + menu reframing 2026-08-31 (plan v10.42/v10.43), recomposed to
    the statutory wall 2026-09-02 (outline fourteenth pass; the budget menu
    `k02` → SF35, the uniform-ITC panel `f17` → SF36), five-anchor twins
    2026-09-08. **Recomposed again 2026-09-09 (Ethan's figure revisions):**
    (1) the rate–deployment cliff (`j06`, old panel c) moves to the SI as
    SF24a, beside its monetized-basis detail; (2) the old panel (b) splits —
    its credit-feasibility mask is the new (b) and its demonstration funding
    requirement the new (c); (3) **every value shown is lowered by three
    statutory rate points** (`DISPLAY_CUT = 0.03` in
    `rate_design/_build_notebook_v2.py`; the display twins
    `u50/u51/u52_*_cut_5a.csv`) to reflect what the cliff revealed — the
    credit that actually delivers the mandated build lies below the mapped
    requirement (delivery at headline−1 point in 6 of 6 feed-back ladders,
    failure at headline−5 in 6 of 6; ST9, SF24a). The registered objects
    keep their one-point cushion (gates, verdicts, ST14–ST16 unchanged);
    three points is Ethan's "for now" convention — one constant to move when
    a finer probe lands; (4) rates read in **percent**, and the fans are
    **clipped at 100%** with a red edge along the clipped span (the
    censored-cell triangles are gone; the edge carries that information);
    (5) the reference credit path and the run-certified minimal-rate band
    left panel (a) with the cliff.

    **What this shows.** The shadow price is a model price. This figure
    translates it into statutory credit terms and shows where the
    translation hits a wall. Panel (a): **per-world required statutory
    rates** — for each schedule and build year, the credit rate on the
    world's own build cost that just covers its requirement, three points
    below the mapped rate, fanned across the 10,000 cost worlds (median
    solid; interquartile and p5–p95 bands; thin dotted lines = the medians at
    the ∓E6 band ends). The horizontal red lines are the statutory
    ceilings: dotted 50% (today's stackable maximum: 30% base + 10% energy
    community + 10% domestic content) and dash-dot 60% (the registered outer
    bound). Where the p95 edge would exceed 100% of basis the fan is clipped
    and a red edge marks the span. Panel (b): the **credit-feasibility
    mask**, drawn as the share of samples covered by the credit — the share
    of worlds whose required rate sits at or below the 50% statutory maximum
    in each build year (the existing incentive structure; the 60% case is in
    ST14 and Table 2). The dashed line is the common demonstration-window
    end, 2038; the right-edge label on each curve is the share covered in
    the last build year, which equals the share of worlds that ever become
    credit-feasible within the horizon. Panel (c): the **demonstration funding requirement** in
    2024\$B — the fixed-basis PV of above-cap need inside the common window
    (median solid, p95 faint).

    **One common window end, 2038 (Ethan, 2026-09-10).** The decision-value
    analysis (`z-ethan/voi/`, SF56, ST19; on the five-anchor map) showed that graduation years are
    bimodal: worlds that ever become credit-feasible do so early, the rest
    never do within the horizon. By 2038 graduation is all but complete in
    every schedule at both ceilings: at most 1.5% of worlds graduate later at
    the 50% ceiling and 3.4% at 60%, except EIA, whose builds start in 2038
    (15–18% later; Table 2; voi p36). A handful of tail worlds graduate as
    late as 2041–2047, so the share graduating after 2038 is the operative
    statistic, not the strict last year. So the paper
    carries one window end for every schedule — build years through 2038 —
    and after it any grant dollar goes to a world that will never become
    credit-feasible. The per-schedule expected-loss minimizers and their
    price sensitivity stay in SF56/ST19; the anchor sensitivity of the IAEA
    pick is logged in voi/status.md (2026-09-10). The registered rate_design
    kills KB1/KB2, ST14 and the market-world transfer (Fig 5, SF40, ST18)
    stay on the earlier fixed 2035 window.

    **How to read it.** In panel (a), wherever a fan sits above a ceiling
    line, that share of worlds cannot be served by a statutory credit at
    that cap in that year. Through 2038 the demonstration window absorbs the
    excess as grant cost share; after it, above-cap need means the capped
    credit alone fails that world. The curves in panel (b) are per-year shares
    and need not be monotone (a cheap solve year lifts a curve for that year
    only). Their right-edge value, the share covered in the last build year,
    is the share of worlds the credit alone ever reaches; one minus it is the
    not-credit-feasible share — the mask's key output. Panel (c) prices the
    window.

    **Key results** (computed in the cell below from the `m2x_*_cut` twins;
    the registered one-point values are ST14). Most cost worlds still need
    above-cap support in at least one post-window year in every schedule;
    the post-window infeasible share is quoted ONLY as cap × certificate-band
    ranges. The message is unchanged by the three-point allowance: a
    statutory-capped credit alone reaches only the cheap tail of the cost
    distribution, and observation cannot rescue this by fine-tuning
    (SF58b).

    **Mandatory framings (from the adjudicated audit record — never quote
    past them).** The mask is a range table, never a single number (the
    certificate band moves the shares); it is presented at both caps because
    the cap choice moves the EIA AEO high and Abou-Jaoude shares by tens of points (registered kill
    KB2 fired — a cap-sensitivity table, not a single-cap exhibit). cop28's
    demonstration framing is killed (registered kill KB1: its above-cap need
    persists past the window at the low band end — its gap is a band range
    with no early-concentration story). eia is N/A for the demonstration
    framing (empty window), not satisfied by it. The p95 fan edge is
    clamp-pinned in most schedule-year cells (there the drawn p95 is the top
    anchor's own rate, not a distribution quantile); the outlay calibration
    carries a ±5% systematic. Paper text is written from the `u91`
    dispositions, never from exhibit markdown. The transfer of the wall to
    the six market worlds (Fig 5 caption, ST18, SF40) stays on the registered
    one-point cushion.
    """),
    code(r"""
    P.compose(
        [[RD2_FIG / "n38_rate_fans_pct.png"],
         [RD2_FIG / "n39_mask_paper.png", RD2_FIG / "n43_gap_paper.png"]],
        "Fig4_statutory_wall.png",
        letters="abc",
        center=True,  # row widths differ; do not leave a blank corner
    )
    P.source_ref(
        (RD2_FIG / "n38_rate_fans_pct.png", "rate_design2/rate_design2_v2.ipynb",
         "figures cell (n38; the DISPLAY_CUT display twin)",
         "`m20_requirement_fans_cut.csv` (every value DISPLAY_CUT = 3 points below the mapped requirement; "
         "the chosen map of `m12_selection.csv` on 66 exact anchors + the leave-one-out band E6 of `m13_band_e6.csv`; "
         "R0/GA1'/GP' PASS in `m31_verdict.csv`; the registered one-point fans are n32 / ST14)"),
        (RD2_FIG / "n39_mask_paper.png", "rate_design2/rate_design2_v2.ipynb", "figures cell (n39)",
         "`m21_feasibility_mask_cut.csv` (display twin of m21; the kills stay adjudicated on the registered "
         "twin in `m31_verdict.csv`)"),
        (RD2_FIG / "n43_gap_paper.png", "rate_design2/rate_design2_v2.ipynb", "figures cell (n43)",
         "`m22_demonstration_gap_cut.csv` (display twin of m22)"),
    )

    m12 = pd.read_csv(RD2_EXP / "m12_selection.csv")
    m31 = pd.read_csv(RD2_EXP / "m31_verdict.csv").set_index("name")
    CHOSEN, E6_PTS = m12["chosen"].iloc[0], int(m12["E6_pts"].iloc[0])
    assert m31.loc["R0", "result"] == "PASS" and m12["n_anchors"].iloc[0] == 66
    m13 = pd.read_csv(RD2_EXP / "m13_band_e6.csv").set_index("ab")
    eia_p90 = float(m13.loc["eia", "p90"])
    u50 = pd.read_csv(RD2_EXP / "m20_requirement_fans.csv")
    u50c = pd.read_csv(RD2_EXP / "m20_requirement_fans_cut.csv")
    br, brc = [d[(d["band"] == "base") & (d["quantity"] == "rate")].reset_index(drop=True) for d in (u50, u50c)]
    assert len(br) == len(brc) and len(br) == sum(1 for _ in br.itertuples())
    _kb1, _kb2 = m31.loc["KB1", "result"], m31.loc["KB2", "result"]
    print(f"refit map {CHOSEN}; E6 = {E6_PTS} points; KB1 {_kb1}; KB2 {_kb2}")
    # the display twin sits exactly DISPLAY_CUT below the registered median wherever the zero floor is not hit
    _d = (br["p50"] - brc["p50"])[brc["p50"] > 0]
    CUT = round(float(_d.median()), 4)
    assert CUT == 0.03 and (abs(_d - CUT) < 1e-3).all(), (CUT, _d.describe())
    clip = brc[brc["p95"] > 1.0]
    clip_txt = ", ".join(f"{P.SCHED_SHORT[r.schedule]} {int(r.year)}" for r in clip.itertuples())
    print(f"display cut = {CUT:.0%} of basis; cells whose p95 edge is clipped at 100%: {clip_txt or 'none'}")
    n_clamp, n_cells = int((brc["p95_clamp_pinned"] == True).sum()), len(brc)  # noqa: E712
    # the flat-clamp caveat applies only to the interpolation families (M00/M0); a ridge map extrapolates
    clamp_txt = (f" The 95th-percentile edge is clamp-pinned in {n_clamp} of {n_cells} schedule-year cells (the drawn "
                 "edge is then the top anchor's own rate, not a distribution quantile)." if CHOSEN in ("M00", "M0") else
                 f" The map (a pooled regression) extrapolates beyond the most expensive solved world rather than a "
                 "flat clamp; its leave-one-out band is the stated ∓E6.")

    u51c = pd.read_csv(RD2_EXP / "m21_feasibility_mask_cut.csv")
    W_COMMON = 2038
    assert (u51c["window"].dropna() == "w2038").any(), "m21 twin lacks the w2038 rows: re-run rate_design2_v2"
    p36 = pd.read_csv(RD2_EXP / "m23_common_window_table.csv")     # the refit-map common-window table (Table 2)
    assert (p36["common_year"] == W_COMMON).all()
    _p36_voi = pd.read_csv(VOI_EXP / "p36_common_window_table.csv")   # the pre-refit five-anchor table (SF56/ST19)
    _cmp = (p36[(p36["cut"] == "disp") & (p36["band"] == "base") & (p36["cap"] == 0.5)].set_index("schedule")["share_never"]
            - _p36_voi[(_p36_voi["cut"] == "disp") & (_p36_voi["band"] == "base") & (_p36_voi["cap"] == 0.5)].set_index("schedule")["share_never"])
    print("never-credit-feasible share, refit map minus five-anchor map (50% cap, display twin):", _cmp.round(3).to_dict())
    _c50 = u51c[(u51c["kind"] == "per_year") & (u51c["band"] == "base") & (u51c["cap"] == 0.5)]
    end50 = {ab: 1 - float(_c50[_c50["schedule"] == ab].sort_values("year")["share_above"].iloc[-1]) for ab in P.SCHEDULES}
    _p36d = p36[(p36["cut"] == "disp") & (p36["band"] == "base") & (p36["cap"] == 0.5)].set_index("schedule")
    assert all(abs(end50[ab] - (1 - float(_p36d.loc[ab, "share_never"]))) < 1e-3 for ab in P.SCHEDULES)
    print("share covered by the credit in the last build year (50% cap, display twin) = 1 - never share:",
          {k: round(v, 2) for k, v in end50.items()})
    _late = _p36d["share_graduating_after_common"]
    _late_ex, _late_eia = float(_late.drop("eia").max()), float(_late["eia"])
    print(f"worlds graduating after {W_COMMON} (50% cap, display twin): max outside EIA {_late_ex:.3f}, EIA {_late_eia:.3f}")
    pw = u51c[(u51c["kind"] == "per_world") & (u51c["window"] == "w2038")]
    r60 = pw[pw["cap"] == 0.6]["share_not_credit_feasible"]
    r50 = pw[pw["cap"] == 0.5]["share_not_credit_feasible"]
    print(f"post-window infeasible share (display twin, common {W_COMMON} window; quoted ONLY as cap x band ranges): "
          f"60% cap {r60.min():.2f}-{r60.max():.2f}; 50% cap {r50.min():.2f}-{r50.max():.2f}")
    pwb = pw[pw["band"] == "base"]
    _eia_aj = pwb[pwb["schedule"].isin(["eia", "aj"])].pivot(index="schedule", columns="cap",
                                                              values="share_not_credit_feasible")
    kb2 = ((_eia_aj[0.5] - _eia_aj[0.6]) * 100).round(0)
    print(f"cap sensitivity, base band (eia/aj, 50% vs 60% cap): {kb2.to_dict()} points")

    u52c = pd.read_csv(RD2_EXP / "m22_demonstration_gap_cut.csv")
    g = u52c[(u52c["band"] == "base") & (u52c["cap"] == 0.6)
             & (u52c["window"] == "w2038") & (u52c["window_applicable"] == True)]  # noqa: E712
    _killed = sorted(set(re.findall(r"\('(\w+)', '", m31.loc["KB1", "detail"]))) if _kb1 != "PASS-EXC" else []
    gk = g[~g["schedule"].isin(_killed)]   # schedules whose demonstration framing KB1 killed on the refit band
    gmin, gmax = gk["gap_p50_B"].min(), gk["gap_p50_B"].max()
    gkill_txt = ("; " + ", ".join(f"{P.SCHED_SHORT[s]} {float(g[g['schedule'] == s]['gap_p50_B'].iloc[0]):.1f} B$" for s in _killed if s in set(g["schedule"]))
                 + " quoted only as band ranges (KB1: above-cap need persists past the window at a band end)") if _killed else ""
    g95 = g["gap_p95_B"].max()
    print(f"demonstration gap medians (display twin, base band, 60% cap, common {W_COMMON} window): "
          + ", ".join(f"{r.schedule} {r.gap_p50_B:.1f}" for r in g.itertuples())
          + f" B$; p95 max {g95:.0f} B$ (base band; band ends larger -> ST14)")

    P.caption("Fig 4", f'''
    The statutory wall: what caps can and cannot buy. Every value is shown {CUT:.0%} of basis
    below the mapped requirement — the allowance for the finding that the credit which
    actually delivers the mandated build lies below the requirement the shadow prices imply
    (delivery one point below in 6 of 6 feed-back ladders, failure five points below; SF24a,
    ST9); the registered one-point values are in ST14k–n. (a) Required statutory credit rate on
    each world's own build cost, per schedule and build year, fanned across the 10,000 cost
    worlds (the requirement map fit on 66 model-solved worlds, 11 per schedule; median solid;
    interquartile and 5th-95th percentile bands; thin dotted = the medians at the two ends of
    the map's leave-one-out error band, ∓{E6_PTS} rate points — the pooled band; the map's registered fit gate
    GM1 did not pass, and the EIA panel's own leave-one-out 90th-percentile error is {eia_p90:.0f} points);
    dotted red line = the 50% stackable statutory maximum (30% base +
    10% energy community + 10% domestic content), dash-dot = the hypothetical 60% cap (the registered outer
    bound). Fans are clipped at 100% of basis; a red edge marks the clipped span
    ({clip_txt or "no cell"}), where the source rates exceed 100% and the drawn values are
    lower bounds.{clamp_txt} (b) Share of samples covered by the credit — worlds whose required rate is at
    or below the 50% statutory maximum in that build year (the existing incentive structure).
    The dashed line is the demonstration-window end, {W_COMMON}, common to every schedule:
    through {W_COMMON}, grant-type federal cost share to first units is the assumed vehicle for
    above-cap need; after {W_COMMON} at most {_late_ex:.1%} of worlds still become credit-feasible
    in any schedule but EIA ({_late_eia:.0%}; its builds start in {W_COMMON}) (Table 2; SF56 is the
    pre-refit decision-value figure). The right-edge labels are the share of worlds the credit
    alone ever reaches ({min(end50.values()):.0%}-{max(end50.values()):.0%}).
    Post-window, the uncovered share is the not-credit-feasible share:
    {r50.min():.2f}-{r50.max():.2f} at the 50% cap and {r60.min():.2f}-{r60.max():.2f} at
    the 60% cap, across schedules and the ∓{E6_PTS}-point band — quoted only
    as ranges. The cap choice alone moves the EIA AEO high and Abou-Jaoude shares by
    {int(kb2.min())}-{int(kb2.max())} points (the mask is a cap-sensitivity table){gkill_txt}.
    (c) The demonstration funding requirement — the fixed-basis present value of
    above-cap need inside the common window, build years through {W_COMMON} (median solid,
    95th percentile faint; left bar 50% cap, right bar 60%).
    Where the framing stands, the medians at the
    60% cap run {gmin:.2f}-{gmax:.1f} B$ (base band; 95th percentile to {g95:.0f} B$, larger
    at the band ends — ST14); the outlay calibration carries a +-5% systematic. Model-run
    tests of the wall's definition in the solved anchor worlds (batch 6, 57 credit runs):
    SF49–SF53, `rate_design2` m31. A
    statutory-capped credit alone reaches only the cheap tail of the cost distribution, in
    every schedule — and observation cannot rescue this by fine-tuning the scale (SF58b).
    The rate-deployment cliff behind the allowance is SF24a; the budget menu and the
    uniform-ITC-vs-floor comparison live in SF35/SF36 (tables ST13/ST6); required-rate
    detail by solve year: SF33.
    ''')
    """),

    # ---------------------------------------------------------------- Fig 5
    md(r"""
    ## Figure 5 — Robustness across market worlds

    **Recomposed 2026-09-09 (Ethan's figure revisions):** the shape-survival
    matrix (old panel a, `g02`) moves to the SI as SF48 — its survival
    criterion and the 108-of-108 count keep a caption home there — and the
    two shadow-price panels read in the Fig 3 unit, 2024\$/kW of mandated
    capacity (the shadow price capitalized over the model's 30-year
    evaluation window, ×14.76: the required reduction in financed capital
    cost). Sources `g03b` and `f15b`; the rental-basis originals `g03`/`f15`
    stay in their notebooks.

    **What this shows.** Do the headline results depend on our base market
    assumptions? We re-ran the 18 SMR percentile cases under six market
    worlds (gas price high/low, high-electrification demand, renewable costs
    cheap/dear, and a transmission-limited world): 108 runs, all output checks
    green. Panel (a): the capital-cost-gap paths for the smallest and largest
    schedules, overlaid across market worlds. Panel (b): the large-reactor
    comparator against the SMR program, by cost-world percentile (base market
    world only). Whether the bridge shape survives in every case × market
    world is SF48 (it does, 108 of 108). The two threshold results of S3 —
    the statutory wall and the spending-cap alarm — are transferred to the
    same six alternative market worlds in `market_transfer/` (ST18,
    SF40–SF41); the caption carries the six-world envelopes, the base ranges
    stay in the Fig 4b/Fig 4c and SF58a captions. The transfer stays on the
    registered one-point cushion, not the Fig 4 display allowance.

    **How to read it.** In panel (a), the spread across colored lines is what
    market conditions do to the subsidy level. Panel (b) compares
    technologies at the same percentile. Ratios (the large premium, the decay
    classes) are unit-free and unchanged by the re-denomination.

    **Key results.**
    - The bridge shape survives in **108 of 108** cells (SF48), and no market
      world unbinds a mandate. The expensive-world non-decay is generic, not a
      base-world artifact.
    - The fiscal ordering of the six schedules survives (Kendall τ ≥ 0.867 in
      every cell against base, mean 0.993).
    - Only the level moves, and it moves as economics predicts: the median
      shadow price moves −27% to +18% across the six market worlds (the
      six-number list is in SF22/ST17).
    - The level shift passes straight into the required tax-credit rate (the
      conversion is linear in the shadow price for a fixed case-year), so the
      statutory wall of S3-4 is a base-market-world number — across the six
      alternative worlds the 60%-ceiling share runs from none of the cost
      worlds to all of them (the band-qualified high-gas and low-gas statements
      are in the SF40 caption; ST18). The spending-cap alarm's
      committed spend moves with the bill scale; its share of the failing
      world's bill barely moves (ST18, SF41).
    - The large-reactor premium is not a constant. Large needs 1.4–3.5× the
      SMR gap in cheap worlds, 1.23–1.36× at the median — but at P95
      the two technologies reach parity (0.95–1.02×): in expensive worlds both
      need the same subsidy.
    """),
    code(r"""
    P.compose(
        [[S4_FIG / "g03b_dual_overlays_capex.png"],
         [S3_FIG / "f15b_large_band_capex.png"]],
        "Fig5_market_worlds.png",
    )
    P.source_ref(
        (S4_FIG / "g03b_dual_overlays_capex.png", "step4_analysis/step4_analysis.ipynb",
         "cell g03b (added 2026-09-09 to the builder after g03)",
         "step3+step4 checks `duals_by_year.csv` (eia/eo x p05/p50/p95 x base + six market worlds) x pvf_onm"),
        (S3_FIG / "f15b_large_band_capex.png", "step3_analysis/step3_analysis.ipynb",
         "cell f15b-large-band-capex (added 2026-09-09)",
         "combined duals x pvf_onm, large100 vs smr100 shared binding years; ratio table: `t15_large_ratio.csv`"),
    )

    s02 = pd.read_csv(S4_EXP / "s02_shape_survival.csv")
    surv = s02[s02["survives"].notna()]
    n_surv = int((surv["survives"] == "yes").sum())
    print(f"shape survival (SF48): {n_surv}/{len(surv)}")
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
    excl = sorted({f"{_wname[w]}/{P.SCHED_SHORT[ab]}" for ab, ws in zip(own["schedule"], own["worlds_excluded"].fillna(""))
                   for w in ws.split(";") if w})
    e60, e50 = env.loc[0.6], env.loc[0.5]
    print(f"wall envelope 60% cap: base {e60['base_lo']:.2f}-{e60['base_hi']:.2f}, "
          f"worlds {e60['lo']:.2f}-{e60['hi']:.2f}; 50% cap: base {e50['base_lo']:.2f}-"
          f"{e50['base_hi']:.2f}, worlds {e50['lo']:.2f}-{e50['hi']:.2f}")

    P.caption("Fig 5", f'''
    Robustness across market worlds (108 sensitivity runs: the 18 SMR percentile cases x six
    market worlds). Both panels read in the Fig 3 unit: the shadow price capitalized over the
    model's 30-year evaluation window, the required reduction in financed capital cost per kW
    of mandated capacity (2024$). (a) Overlays for the smallest and largest schedules across
    market worlds: only the level moves, in the direction economics predicts (median -27% to
    +18%); the bridge shape survives in {n_surv} of {len(surv)} cells (SF48). (b) The large-reactor
    and SMR programs' gaps by year for each schedule (median-world lines, 5th–95th percentile
    bands), base market world: the large premium is 1.4-3.5x in cheap worlds and
    1.23-1.36x at the median, but the two technologies reach parity (0.95-1.02x) in expensive
    worlds. Transfer of the S3 threshold results (ST18; SF40-SF41; on the registered one-point
    cushion, not the Fig 4 display allowance), quoted over the six alternative market worlds
    on the pre-refit five-anchor map and the registered 2035 window (ST18; not directly comparable
    to Fig 4 and Table 2, which read the batch-6 refit map and the common 2038 window): the share
    of cost worlds needing an above-ceiling credit rate in a post-window build year (build years
    after 2035) spans
    {e60['lo']:.2f}-{e60['hi']:.2f} at the 60% ceiling (band centre {e60['mid_lo']:.2f}-{e60['mid_hi']:.2f})
    and {e50['lo']:.2f}-{e50['hi']:.2f} at 50% (band centre {e50['mid_lo']:.2f}-{e50['mid_hi']:.2f}); the
    median spend committed before the spending-cap alarm (1.5x the world's own median-world
    (P50) bill, middle noise) spans {own['worlds_paid_p50_B_min'].min():.1f}-{own['worlds_paid_p50_B_max'].max():.1f} B$
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
    t01 = t01[~t01["case"].str.contains("_p25|_p75")]   # production cases only (anchors 09-08 excluded)

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

    # ------------------------------------------------- Table 2: credit feasibility
    md(r"""
    ## Table 2 — What the capped credit alone reaches, by schedule

    **What this table shows.** One row per deployment schedule and statutory
    ceiling (50% = today's stackable maximum; 60% = the registered outer
    bound). The columns: the share of cost worlds that never get under the
    ceiling within the horizon (the credit alone never reaches them); the
    share under the ceiling by 2038, the common demonstration-window end; the
    share that gets under it only after 2038; and the last year in which any
    world gets under it. Values are the 3-point display twin (as Fig 4); the
    registered one-point cushion, the ∓E6 band ends and the q90/q95/q99
    graduation years are in ST19o. **Repointed 2026-09-10 to the batch-6 refit
    map** (`rate_design2` m23; the five-anchor voi p36 is the pre-refit record).

    **Why 2038.** Graduation years are bimodal: worlds that ever become
    credit-feasible do so early, the rest never do. After 2038 at most a few
    percent of worlds still graduate in any schedule but EIA, whose builds
    start in 2038. The strict last graduation year (2041–2047 in four
    schedules) is set by a handful of tail worlds among 10,000 and is shown
    for completeness; the share graduating after 2038 is the operative
    column. The demonstration window therefore ends in 2038 for every
    schedule in Fig 4; the per-schedule expected-loss minimizers stay in
    SF56/ST19.

    **Display budget.** Added 2026-09-10 at Ethan's request as the ninth
    main-text display item; the outline's eight-item budget needs his ruling
    (this slot was freed 2026-08-19 and consumed by SF58 on 2026-08-26).
    """),
    code(r"""
    p36 = pd.read_csv(RD2_EXP / "m23_common_window_table.csv")   # 2026-09-10: the refit map (rate_design2 m23), band E6
    W_COMMON = int(p36["common_year"].iloc[0])
    assert W_COMMON == 2038 and (p36["common_year"] == W_COMMON).all()
    d = p36[(p36["cut"] == "disp") & (p36["band"] == "base")]
    rows = []
    for ab in P.SCHEDULES:
        for cap in (0.5, 0.6):
            x = d[(d["schedule"] == ab) & (d["cap"] == cap)].iloc[0]
            rows.append({
                "schedule": ab,
                "source": P.SCHED_SHORT[ab],
                "ceiling_pct": int(round(cap * 100)),
                "never_credit_feasible": round(float(x["share_never"]), 2),
                f"credit_feasible_by_{W_COMMON}": round(float(x["share_under_by_common"]), 2),
                f"credit_feasible_after_{W_COMMON}": round(float(x["share_graduating_after_common"]), 3),
                "last_year_any_world_becomes_feasible": int(x["complete_year"]),
            })
    table2 = pd.DataFrame(rows)
    # caption numbers from the unrounded export, keyed by ceiling in percent (matches the Fig 4 caption)
    _dd = d.assign(ceiling_pct=(d["cap"] * 100).round().astype(int))
    late = _dd[_dd["schedule"] != "eia"].groupby("ceiling_pct")["share_graduating_after_common"].max()
    late_eia = _dd[_dd["schedule"] == "eia"].set_index("ceiling_pct")["share_graduating_after_common"]
    print(f"share of worlds becoming credit-feasible after {W_COMMON}: at most "
          + ", ".join(f"{v:.1%} at the {c}% ceiling" for c, v in late.items())
          + " outside EIA; EIA " + ", ".join(f"{v:.0%} ({c}%)" for c, v in late_eia.items()))
    table2.to_csv(P.OUT_EXP / "Table2_credit_feasibility.csv", index=False)
    print(f"exports/Table2_credit_feasibility.csv ({len(table2)} rows)")

    P.caption("Table 2", f'''
    What the capped credit alone reaches. For each deployment schedule and statutory ceiling
    (50% = today's stackable maximum; 60% = the registered outer bound): the share of the 10,000
    cost worlds that never get under the ceiling within the horizon, the share under it by
    {W_COMMON} (the common demonstration-window end in Fig 4), the share that gets under it only
    after {W_COMMON}, and the last year in which any world does. Values are shown 3 points of
    basis below the mapped requirement, as in Fig 4 (registered one-point values, the
    band ends and the q90/q95/q99 graduation years: ST19o). After {W_COMMON} at most
    {late[50]:.1%} of worlds still become credit-feasible at the 50% ceiling and {late[60]:.1%} at
    60%, in every schedule but EIA ({late_eia[50]:.0%} and {late_eia[60]:.0%}), whose builds start
    in {W_COMMON}; the last year is set by a handful of tail worlds. Source: rate_design2
    m23_common_window_table (the batch-6 refit map, 66 solved anchor worlds; the pre-refit
    five-anchor table is voi p36, ST19o).
    ''')
    table2
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
    _expect = {"Fig1_engine_vs_literature.png", "Fig2_schedules_and_cost_fans.png", "Fig3_cost_gap_fans.png",
               "Fig4_statutory_wall.png", "Fig5_market_worlds.png"}
    _have = {f.name for f in P.OUT_FIG.glob("Fig*.png")}
    assert _have == _expect, f"stale or missing composed figures in figures/: {sorted(_have ^ _expect)}"
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
    carries a source block naming the notebook and cell that made it. SF28–30
    embed the winner-boundary and NPV-check exports (the former re-export gap,
    closed 2026-08-20 at the source notebooks); SF48 (the shape-survival
    matrix, main-text Fig 5a until 2026-09-09) is the newest entry.

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
    ## Supplementary Notes (SN1–SN11) — pointers

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
    | SN8 | Bridge-failure detection: the ensemble observer, the bill attachment, the noise model, the conformal false-alarm calibration, the bias experiment, and the spend-aware exceedance amendment (2026-08-25; methods.md section 6) | `z-ethan/bridge_detection/methods.md` + `status.md` (tables in ST11, figures in SF25–27 below; the committed-spend figure is main-text figure 5a (now SF58a)) |
    | SN9 | The declining-credit requirement analysis, the cost-of-information limit, and the 66-run batch verdict (zero-run section 2026-09-02; batch reallocated 2026-09-04; RETURNED and adjudicated 2026-09-08): the per-world requirement machinery and its certificate chain — now the FIVE-anchor map (p05/p25/p50/p75/p95) with the leave-one-out band E5 replacing the +-20% hide-the-middle band; the feasibility mask with its kill dispositions; the demonstration-gap accounting; the dollar-menu certificate scope; the exposure/allocation-cap argument (confirmed in the model: delivering credit paths induce 1.0-11.9x take-up); the Part A restatement; the batch gates + claim ladder ADJUDICATED (rung FAIL: GE1/GH1 true failures on the eo and cop28 marginal worlds; GE2 measured per ladder; GX1 persists, shed 0.00; GA1/GA2 PASS, GA3 partial, E5 = 0.18) | `z-ethan/rate_design/methods.md` (v2 -> v2.3) + `status.md` (adjudications) + `exports/u101_verdict.csv` (the verdict) + `u91_verdict.csv` (three-anchor) / `u91_verdict_5a.csv` (five-anchor) (tables in ST14–ST16, figures in SF34/SF37/SF38/SF39/SF43–SF47 below; the fans/mask are main-text Fig 4a/Fig 4b, the calibration limit is SF58b — all on the five-anchor basis per the u101 `display-basis` row) |
    | SN10 | The market-world transfer (new 2026-09-02): the required credit rate re-derived on every step4 sensitivity output file (the t09 chain; gate G0a reproduces t09 exactly), the exact shadow-price-ratio x region-set-factor decomposition, the statutory mask per market world (gate G0b reproduces u50/u51), the paired per-world re-run of the spending-cap alarm (common random numbers; gates G-CRN, G-H1w), and the KT1-KT5 kill rules | `z-ethan/market_transfer/methods.md` (v1–v1.4) + `status.md` (review rounds) + `exports/v09_verdict.csv` (tables in ST18, figures SF40-SF41; the envelopes in the Fig 5 caption) |
    | SN11 | The decision value of cost information (new 2026-09-09; SI only until Ethan's reading): EVPI, EVPPI (cross-fitted, permutation-floored) and EVSI on the credit-scale decision under the quantile loss whose optimal act is the paper's 90%-coverage rule, sunk years excluded, leave-one-out posterior; the stopping decision as a Bayes sequential decision (threshold minimizing the Bayes risk at a swept false-stop price, LSMC optimal-stopping check, the conformal 5% rule as a reference point with its implied false-stop price); the grant cut-off year as a coverage-vs-grant-dollars frontier plus an abandonment trigger; gates G0–G7, kills K1–K5, predictions P1–P5 | `z-ethan/voi/methods.md` + `status.md` + `exports/p90_verdict.csv` (tables in ST19, figures SF54–SF56) |
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
    This panel was main-text figure 3b (now SF57b) until the 2026-08-26 recomposition; SF57
    keeps the probability panel (SF57a), and this page keeps the sizes.

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
    was SF57b.
    ''')
    """),
    md(r"""
    ## SF6 — Mixing the program: the mixed-build search and the fragmentation penalty

    **What this shows.** A per-draw optimizer searches all mixed strategies
    (splitting the program between the technologies in any share). Maps show
    where in parameter space a mix would win and by how much. Panel (f) — the
    fragmentation histogram, main-text figure 3b (now SF57b) until the 2026-08-31
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
         "cell 40 (standalone emission 2026-08-26; re-lettered b → f 2026-08-31 when it moved here from SF57b)",
         "in-memory MC worlds for the McKinsey schedule (the fragmentation experiment; stdout + figure only — no CSV export)"),
    )
    P.caption("SF6", '''
    Mixing the program. (a-e) Mixed-build optimizer results: where any split of the
    program between the two technologies would beat the best pure program, and by how
    much. Mixes win in 10 of 60,000 draws, by at most 0.51%. (f) The fragmentation
    penalty: the extra program cost of a 50/50 split under the McKinsey schedule (median
    16.7%, P50/P90 marked) — splitting the program splits the learning. Panel f was
    main-text figure 3b (now SF57b) until 2026-08-31.
    ''')
    """),
    md(r"""
    ## SF7 — The value of information at baseline: EVPI and the 2036 switch bound

    **What this shows.** What would it be worth to know the true cost world
    before committing the program — and how much of that value could one later
    technology switch recover? The full detail behind main-text figure 3b (now SF57b): total
    EVPI and its decomposition (which uncertainty carries the value) by
    dependence cell, and the 2036 switch bound with the pre-registered 1%
    threshold (the C5 claim). (Merged 2026-08-31: the switch-bound page was
    SF8 until the third SF57 recomposition; the two measures are baseline
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
    main-text figure 3c (now SF57c)/SF57d; since 2026-08-31 the two κ profiles are combined as
    main-text figure 3b (now SF57b), and this page keeps the partial decomposition, the probe
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
    text's SF57c/SF57d: every S2 headline claim against the SMR optimism
    multiplier m (the factor by which the drawn 2030 SMR anchor cost would
    understate the truth), at the three stress anchors κ = 1, 0.5, 0. Panel
    (a) the majority claim, (b) the fragmentation penalty, (c) EVPI, (d) the
    2036 switch bound. Common random numbers across m; the m = 1.5 points
    reproduce the published `stress_survival.csv` stress rows bit-for-bit.
    (Renumbered 2026-08-31: this page was SF8a while SF8 held the switch-bound
    κ profile, which now shares SF7. Main SF57c/SF57d are this sweep's majority
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
    bit-for-bit. Main SF57c/SF57d are panels a and c at paper size; until 2026-08-31 this
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
    t13 = t13[~t13["case"].str.contains("_p25|_p75")]   # production cases only (anchors 09-08 excluded)
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

    **What this shows.** The detail behind SF42 (main-text Fig 1 until 09-08). SF15: the deployment
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
    require (dial marginals on the one-sided 2050 basis, matching SF42;
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

    **What this shows.** The step4 sensitivity detail behind Figure 5: which
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
    figure (now Fig 4); the team
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
    ## SF24 — The rate–deployment cliff, and the demand curve behind it (main-text Fig 4c until 2026-09-09)

    **What this shows.** Panel (a): the **rate–deployment cliff** (`j06`;
    main-text figure 5 (now SF58)c from 2026-08-24, Fig 4c from 08-26, demoted here on
    2026-09-09 in Ethan's figure revisions — its finding now enters Fig 4 as
    the three-point display allowance) — new-nuclear 2050 capacity against
    the statutory credit rate on the model convention, in percent, combining
    the flat-credit anchors, the 24-run minus-probe ladders, and the headline
    schedule points; new nuclear equals SMR capacity exactly because
    large-reactor additions are credit-invariant in every run (the
    zero-substitution result). The shaded band is the current 48E credit
    range (30–50%): the entire current-law range sits in the flat tail of the
    response, and the cliff starts a few points past its right edge. Panel
    (b): the as-exported view behind it (`h06`): 2050 capacity against the
    **monetized** credit rate, both technologies and total nuclear. The
    large-reactor series is flat at 94.11 GW at every rate — the fact that
    lets panel (a) plot new nuclear as SMR alone.

    **The finding.** The response to the rate is a cliff, not a slope: zero
    SMR at a flat 30% credit, 9.8 GW at 50% — the entire current-law 48E
    range buys almost nothing — against 27–381 GW at the schedule rates. The
    24-run minus probe brackets the delivery-minimal rate within five points
    below the headline (delivery at headline−1 in 6 of 6 ladders, failure at
    headline−5 in 6 of 6; ST9), and below the boundary the learning feed-back
    amplifies the shortfall instead of cushioning it. The closed-loop
    delivery validation is SF23 (5 of 6 median worlds reproduce the mandate;
    over-delivery 1.3–2.7×, never under).
    """),
    code(r"""
    P.compose(
        [[ITCFBM_FIG / "j06_new_nuclear_cliff.png", ITCFB_FIG / "h06_deployment_vs_rate.png"]],
        "SF24_cliff_and_demand_curve.png",
        letters="ab",
    )
    P.source_ref(
        (ITCFBM_FIG / "j06_new_nuclear_cliff.png", "itcfbm_analysis/itcfbm_analysis.ipynb",
         "cell j06cd001 (x axis in percent since 2026-09-09)",
         "`r04_rate_deployment.csv` (statutory basis, new nuclear only)"),
        (ITCFB_FIG / "h06_deployment_vs_rate.png", "itcfb_analysis/itcfb_analysis.ipynb",
         "figure cells", "`q06_rate_deployment.csv` (flat-rate fbR arm + schedule-rate runs)"),
    )
    P.caption("SF24", '''
    The rate-deployment cliff and the demand curve behind it (main-text Fig 4c until
    2026-09-09). (a) New-nuclear 2050 capacity against the statutory credit rate on the model
    credit convention; shaded band = the 48E range (30-50%). New nuclear equals SMR
    capacity: large-reactor additions are credit-invariant in every run (the
    zero-substitution result). Black squares: flat credits — zero at 30%, 9.8 GW at 50%; the
    entire current-law range buys almost nothing. Colored curves: the minus-probe ladders
    (headline minus 15, 10, 5 and 1 points, then the headline) with draw-calibrated
    endogenous learning (solid) and learning frozen (faint dashed). The response is a cliff,
    not a slope: five rate points below the headline, delivery fails in every world; one
    point below, it delivers in every world; below the boundary learning amplifies the
    shortfall while above it learning amplifies delivery. This bracket is the basis of the
    three-point display allowance applied throughout Fig 4. (b) The same response on the
    monetized basis, by technology and in total, under flat credit rates and at the
    schedule-derived rates: the large-reactor series is flat at 94.11 GW at every rate, so
    panel (a)'s new-nuclear axis equals the SMR series (27-381 GW at the schedule rates).
    Delivery validation: SF23; minimality verdicts: ST9.
    ''')
    """),

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
    (max 0.069). The money view of the same result is main-text figure 5 (now SF58);
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
    are the detection year and the spend committed before the alarm (main-text figure 5 (now SF58)).
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
    figure's menu panel (now Fig 4b)
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
    so every case starts at 1 and shapes compare directly. Main-text figure 4b (now SF59)
    until 2026-08-26, when the freed display slot went to the
    cost-of-detection figure (SF58); the decay-class numbers stay quoted
    in the S3 text and the SF59 caption. In cheap worlds the curves decay to
    3–19% of peak by 2050; median worlds are mixed; no P95 case reaches
    half its peak — under slow learning the subsidy is a standing
    commitment, not a bridge.
    """),
    code(r"""
    P.show_panel(S3_FIG / "f07_dual_shape_normalized.png")
    P.source_ref(
        (S3_FIG / "f07_dual_shape_normalized.png", "step3_analysis/step3_analysis.ipynb",
         "cell 26", "same shadow prices as SF59, normalized by each case's peak"),
    )
    P.caption("SF32", '''
    Shadow prices normalized by their own peak (main-text figure 4b until 2026-08-26; now SF59):
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
    Fig 4a until 2026-08-31 (plan v10.42), when the slot went to the
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
    t09 = t09[~t09["case"].str.contains("_p25|_p75")]   # production cases only (anchors 09-08 excluded)
    r = t09[t09["status"] == "rate"]
    smr_r = r[r["case"].str.startswith("smr100")]
    p50 = smr_r[smr_r["case"].str.endswith("p50")].groupby("case")["i_model_headline"].mean()
    ded = r[~r["case"].str.endswith("_eq")]
    n100 = int((ded["i_model_headline"] > 1.0).sum())
    n100p = int((ded["i_pis_headline"] > 1.0).sum())
    P.caption("SF33", f'''
    The required ITC rate by solve year on the model credit convention (main-text
    Fig 4a until 2026-08-31): median-world schedule averages run
    {p50.min():.2f}-{p50.max():.2f} ({p50.min()/0.30:.1f}-{p50.max()/0.30:.1f}x the
    base 48E credit); expensive worlds need 2.7-3.1x; {n100} of {len(ded)} rated
    case-years exceed 100% on the headline convention ({n100p} on the
    placed-in-service conversion). Rates are max-building-region sufficiency rates;
    regional minima run ~15% lower (ST6). These schedules are the per-world delivery
    thresholds behind the Fig 4a comparison.
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
    ## SF35 — The budget menu (main-text Fig 4a until 2026-09-02)

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
    main-text Fig 4a on 2026-09-02 (outline fourteenth pass): the mask
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
         "(gates G0-G5 green; main Fig 4a 2026-08-31 -> 2026-09-02)"),
    )
    s03c = pd.read_csv(IC_EXP / "s03_headline_table.csv")
    h15 = s03c[s03c["mult"] == 1.5]
    rate_lo, rate_hi = h15["menu_rate_avg_stat"].min(), h15["menu_rate_avg_stat"].max()
    kw_lo, kw_hi = h15["menu_credit_avg_kW"].min(), h15["menu_credit_avg_kW"].max()
    sh_lo, sh_hi = h15["share_flat"].min() * 100, h15["share_flat"].max() * 100
    gap_lo, gap_hi = h15["matched_rule_gap"].min() * 100, h15["matched_rule_gap"].max() * 100
    tol_hi = h15["tolerance_value_pts"].max() * 100
    P.caption("SF35", f'''
    The budget menu (main-text Fig 4a until 2026-09-02): against the budget cap
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
    ## SF36 — Uniform ITC vs ambition (main-text Fig 4b until 2026-09-02)

    **What this shows.** The net-of-tax present-value cost of a uniform
    percentage credit, as a multiple of the minimum-cost floor (a flat
    dollar-per-MW payment at commissioning with frictionless
    monetization), by schedule, ordered by 2050 ambition. Demoted from
    main-text Fig 4b on 2026-09-02 (outline fourteenth pass): the
    instrument premium over the floor is modest in practice — 1.17–1.25x
    at p50, the ~10% monetization haircut plus the 5–13% uniform-rate
    oversubsidy — so the panel largely re-plots the SF59 bill shape in
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
         "main Fig 4b 2026-08-24 -> 2026-09-02)"),
    )
    t18 = pd.read_csv(S3_EXP / "t18_instrument_menu.csv")
    m18 = t18[~t18["case"].str.endswith("_eq") & ~t18["case"].str.contains("_p25|_p75")]
    hair = float(m18["dpmw_haircut"].iloc[0])
    ov_lo = (m18["uniform_itc"].min() / hair - 1) * 100
    ov_hi = (m18["uniform_itc"].max() / hair - 1) * 100
    P.caption("SF36", f'''
    The uniform percentage credit vs the floor, by schedule ordered by 2050 ambition
    (main-text Fig 4b until 2026-09-02): the credit costs
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

    **What this shows** (new 2026-09-02; behind the SF58b plateau
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
    P.show_panel(RD_FIG / "w21_asymptote_5a.png")
    P.source_ref(
        (RD_FIG / "w21_asymptote_5a.png", "rate_design/rate_design_v2_5a.ipynb", "Part A cells (five-anchor twin)",
         "`u30_part_a_restated_5a.csv` (decline_pct_per_obs_last3 column; the <=5%/observation "
         "labeling rule is registered in `rate_design/methods.md` v2; three-anchor original ST16d)"),
    )
    _u30a = pd.read_csv(RD_EXP / "u30_part_a_restated_5a.csv").set_index("schedule")
    _asy = _u30a[_u30a["label"] == "asymptote"]
    _dec = _u30a[_u30a["label"] != "asymptote"]["decline_pct_per_obs_last3"]
    _asy_txt = ", ".join(f"{s} {abs(v):.1f}%" for s, v in _asy["decline_pct_per_obs_last3"].items()) or "none"
    P.caption("SF37", f'''
    The plateau test behind the SF58b labels (five-anchor requirement map): mid-noise
    credit-scale confidence width vs cumulative mandate spend (log scale). "Asymptote" is
    earned only where the mean decline over the last three observations is at most 5% per
    observation ({_asy_txt}); the other {len(_dec)} schedules are still declining at the
    horizon ({_dec.abs().min():.1f}-{_dec.abs().max():.1f}% per observation), so their
    verdict is "not within the program horizon", not "never". Dotted lines: the
    per-schedule design targets. Tables: ST16.
    ''')
    """),
    md(r"""
    ## SF38 — The dollar requirement fans (\$/kW) on the five-anchor map (pre-refit; main-text figure 3 is the refit)

    **What this shows** (new 2026-09-02; the companion unit behind
    main-text Fig 4a). The cushioned per-world dollar requirement in
    \$/kW, per schedule and build year — the same fans as Fig 4a in the
    unit the demonstration-gap accounting consumes. Encodings match the
    Fig 4a legend: median solid, interquartile and p5–p95 bands, thin
    dotted = the ±20% certificate-band medians, grey dashed = the
    reference credit path. The per-cell above-top and below-bottom clamp
    shares are exported with the table (ST14); the rate-unit grid at full
    size IS main-text Fig 4a (the legended w34 variant).
    """),
    code(r"""
    P.show_panel(RD_FIG / "w31_dollar_fans_5a.png")
    P.source_ref(
        (RD_FIG / "w31_dollar_fans_5a.png", "rate_design/rate_design_v2_5a.ipynb", "Part B cells (five-anchor twin)",
         "`u50_requirement_fans.csv` (need_kw rows; the demonstration-gap input; the rate-unit "
         "grid is main-text Fig 4a, the legended w34 paper variant)"),
    )
    P.caption("SF38", '''
    The dollar requirement fans: the cushioned per-world requirement in $/kW, per
    schedule and build year — the Fig 4a fans in the unit the demonstration-gap
    accounting consumes (five-anchor map; encodings as in the Fig 4a legend: median solid,
    interquartile and p5-p95 bands, thin dotted = E5-band medians, grey dashed =
    the reference credit path). Per-cell clamp shares and the band fans: ST14.
    ''')
    """),
    md(r"""
    ## SF39 — The calibration limit, full audit grid

    **What this shows** (new 2026-09-02; the SF58b source before Ethan's
    reading review re-denominated the main-text panel). The legended twin
    of the frozen w20 audit artifact: top row, the 5–95 confidence width on
    the required credit scale in scale units (multiples of the reference
    credit path; the dashed line is each schedule's registered band-5
    target, 0.068–0.078); bottom row, the width of the learning-rate
    interval in points; both against cumulative committed spend (2024\$B),
    one column per schedule, three noise levels; shading would mark
    observation years where the mid-noise 10th-percentile effective sample
    falls below 100 worlds (it never does). SF58b is this grid with the
    top row times the reference path's outlay-weighted average rate (u32);
    the learning-rate row is unchanged. **This grid is the three-anchor
    frozen audit record (v1 sweep, 2026-09-01); since 2026-09-08 SF58b is
    its five-anchor twin (`w37_5a`, band E5), so small differences between
    this grid's top row and SF58b are the anchor densification.**
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
    The calibration limit, full audit grid behind SF58b: top row, the 5-95 confidence
    width on the required credit scale (multiples of the reference credit path; dashed =
    each schedule's registered band-5 target); bottom row, the width of the learning-rate
    interval (points); both vs cumulative committed spend (2024$B), one column per
    schedule, three noise levels (thick = middle). No top-row curve reaches its target at
    any noise level; every bottom-row curve narrows steadily. SF58b re-denominates the
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
    worlds of Figure 5. The required rate is re-derived exactly on every
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
    the six alternative market worlds of Fig 5. In the
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

    # ---------------------------------------------------------------- SF42
    md(r"""
    ## SF42 — Where the ATB 2050 costs sit in learning space (main-text Fig 1 until 09-08)

    **What this shows.** (Main-text Fig 1 until 09-08, when the engine-against-the-literature
    figure took its place; the S1 shares and brackets described below live here now.)
    The NREL Annual Technology Baseline (ATB) publishes
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
        "SF42_atb_placement.png",
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

    P.caption("SF42", '''
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
    # ---------------------------------------------------------------- SF43-SF47 (batch verdict exhibits, 2026-09-08)
    md(r"""
    ## SF43 — The delivery ladders: where the offline boundary actually lies

    **What this shows** (new 2026-09-08; `z-ethan/rate_design/rate_design_v3.ipynb`;
    SN9; ST15). Per schedule, every envelope and boundary-depth run of the batch:
    the 2050 SMR capacity as a multiple of the target (log scale) against the run
    world's offline margin in rate points (negative = the credit path covers the
    world with slack; the vertical dashed line is the offline delivery boundary).
    Filled markers deliver under the feed-back tier convention; open markers do
    not; squares are the +3/+5 depth probes; faint markers are the 1.0x-budget
    ladders. Read per schedule: on aj, mck and iaea every probe up to +1 or +3
    points delivers (the offline criterion is conservative there); on eo and
    cop28 the −1-point marginal run already fails while the comfortable run
    delivers (the boundary lies inside the covered set); eia is the delayed-start
    schedule (P1). Delivering runs build 1.0–11.9x their target: induced take-up.
    """),
    code(r"""
    P.show_panel(RD_FIG / "w50_delivery_ladders.png")
    P.source_ref(
        (RD_FIG / "w50_delivery_ladders.png", "rate_design/rate_design_v3.ipynb", "S10 figure cell",
         "`u100_gate_table.csv` (from `rate_design_checks/exports/delivery_outcomes.csv` + the frozen "
         "`u80_batch_spec.csv`; verdict in `u101_verdict.csv`, depth reads in `u102_ge2_depth.csv`)"),
    )
    P.caption("SF43", '''
    The delivery ladders of the 66-run batch: 2050 SMR capacity / target (log) against the
    run world's offline margin (rate points; dashed = the offline boundary), per schedule;
    filled = delivers, open = does not, squares = depth probes, faint = 1.0x budget. aj/mck/
    iaea: every probe to +1 (aj to +3) delivers — the offline criterion is conservative; eo/
    cop28: the -1-point run fails while the comfortable run delivers — the boundary lies
    inside the covered set; eia: delayed start. Delivering runs overshoot 1.0-11.9x. Tables:
    ST15b/c.
    ''')
    """),
    md(r"""
    ## SF44 — The cap ladder: the two-tier hybrids

    **What this shows** (new 2026-09-08). The 14 hybrid runs against their
    post-window excess of the world's need over the cap (rate points; dashed =
    the offline cap boundary), circles at the 0.60 cap, diamonds at 0.50; filled
    deliver. At 0.50 the aj, mck and iaea cap-binds probes deliver despite
    predicted excesses of +1 to +5 points (the cap does not bite there); every
    eo hybrid fails, including the cap-never-binds control; eia's 0.60 probe
    fails and its control is the delayed-start shape. The 0.50 block has no
    deliver-side control (directional reading, registered).
    """),
    code(r"""
    P.show_panel(RD_FIG / "w51_cap_ladder.png")
    P.source_ref(
        (RD_FIG / "w51_cap_ladder.png", "rate_design/rate_design_v3.ipynb", "S10 figure cell",
         "`u103_gh2_cap_depth.csv` (u80 post-window excess + the checks outcomes)"),
    )
    P.caption("SF44", '''
    The cap ladder: the 14 two-tier hybrid runs against their post-window excess over the
    cap (rate points; dashed = the offline cap boundary); circles cap 0.60, diamonds cap
    0.50; filled = delivers. aj/mck/iaea deliver at 0.50 despite +1 to +5 points of
    predicted excess; every eo hybrid fails, including the slack control; eia's 0.60 probe
    fails. Directional at 0.50 (no slack control). Table: ST15d.
    ''')
    """),
    md(r"""
    ## SF45 — GX1: the 2050 uptick is not an end-of-horizon artifact

    **What this shows** (new 2026-09-08). The required credit rate by build year
    for each schedule's median-world anchor: the standard run (end year 2050)
    against the extended run (end year 2055, mandate flat after 2050). The two
    paths coincide to three decimals in every year, including 2050: the
    extended run sheds 0.00 of the 2047→2050 uptick, so the rise is a real
    terminal effect of the mandate path (the sequential solve does not see the
    horizon), and every schedule keeps the with-2050 basis.
    """),
    code(r"""
    P.show_panel(RD_FIG / "w52_gx1_horizon.png")
    P.source_ref(
        (RD_FIG / "w52_gx1_horizon.png", "rate_design/rate_design_v3.ipynb", "S10 figure cell",
         "`u106_gx1.csv` (from `rate_design_checks/exports/gx1_horizon.csv`: the t09 code path "
         "ported verbatim, SHA-pinned, on each extended run's own h5 — registration P3)"),
    )
    P.caption("SF45", '''
    GX1: required credit rate by build year for each schedule's median-world anchor, the
    standard run (end 2050) against the extended run (end 2055, mandate flat after 2050).
    The paths coincide in every year; the extended run sheds 0.00 of the 2047-2050 uptick,
    so the terminal rise is real, not an end-of-horizon artifact, and the with-2050 basis
    stands for every schedule. Table: ST15g.
    ''')
    """),
    md(r"""
    ## SF46 — GA2 and GA3: the three-anchor map tested out of sample

    **What this shows** (new 2026-09-08). (a) Each new p25/p75 anchor's bill
    from its own run against the three-anchor map's pre-run prediction (u84),
    with the ±10% (informative) and ±20% (certificate) bands: all 12 inside
    ±20%, 9 inside ±10% (GA2 PASS). (b) The per-year required-rate error
    (predicted − true, rate points) at the same anchors, with the ±5-point
    r03 bracket: only 4 of 12 anchors stay inside it in every rate-bearing
    year; the map under-predicts the late-year need of the upper-interior
    worlds by up to 19 points on the largest schedule (GA3 partial) — the
    same direction as the eo/cop28 delivery failures in SF43.
    """),
    code(r"""
    P.show_panel(RD_FIG / "w53_ga_anchors.png")
    P.source_ref(
        (RD_FIG / "w53_ga_anchors.png", "rate_design/rate_design_v3.ipynb", "S10 figure cell",
         "`u104_ga2_bills.csv` + `u105_ga3_rates.csv` (u84 pre-run predictions vs the 49-case "
         "step3_analysis t08/t09 rows of the anchors)"),
    )
    P.caption("SF46", '''
    The three-anchor map tested out of sample at the 12 p25/p75 anchors. (a) Bills: run vs
    pre-run prediction, +-10% and +-20% bands — all 12 inside +-20%, 9 inside +-10% (GA2
    PASS). (b) Per-year required-rate errors (predicted - true, points) with the +-5-point
    bracket — 4 of 12 anchors inside it every year; the map under-predicts the late-year
    need of the upper-interior worlds by up to 19 points (GA3 partial). Tables: ST15e/f.
    ''')
    """),
    md(r"""
    ## SF47 — The statutory mask on three and on five anchors

    **What this shows** (new 2026-09-08). The post-window not-credit-feasible
    share per schedule, at each cap, as the cap × band range on the
    three-anchor map (±20% hide-the-middle band; the batch-placement basis)
    beside the five-anchor map (leave-one-out band E5): the range framing
    survives the densification; the bars move but the reading — a
    statutory-capped credit reaches only the cheap tail — does not.
    """),
    code(r"""
    P.show_panel(RD_FIG / "w54_mask_three_vs_five.png")
    P.source_ref(
        (RD_FIG / "w54_mask_three_vs_five.png", "rate_design/rate_design_v3.ipynb", "S10 figure cell (second run)",
         "`u51_feasibility_mask.csv` (three-anchor) + `u51_feasibility_mask_5a.csv` (five-anchor)"),
    )
    P.caption("SF47", '''
    The post-window not-credit-feasible share as cap x band ranges, per schedule, on the
    three-anchor map (+-20% band) beside the five-anchor map (E5 band): the range framing and
    the reading survive the anchor densification. Tables: ST14b (five-anchor) / ST14g
    (three-anchor).
    ''')
    """),

    md(r"""
    ## SF48 — Bridge-shape survival across market worlds (main-text Fig 5a until 2026-09-09)

    **What this shows.** For every SMR percentile case × market world, does
    the bridge shape survive? A cell "survives" when the case keeps its decay
    class **or** its end-over-peak ratio moves by at most 0.15 (the ratified
    tolerance for classifier-edge flips: the class is stable in 105 of 108
    cells, the ratio moves ≤ 0.15 in 96 of 108, and the three class flips all
    sit within 0.02 of the 0.5 decay boundary). Demoted from Fig 5 on
    2026-09-09 (Ethan's figure revisions); the criterion and the count live
    here. Ratios are unit-free, so the SF59/Fig 5 re-denomination does not
    touch this panel.
    """),
    code(r"""
    P.show_panel(S4_FIG / "g02_shape_survival_matrix.png")
    P.source_ref(
        (S4_FIG / "g02_shape_survival_matrix.png", "step4_analysis/step4_analysis.ipynb", "cell g02",
         "`step4_analysis/exports/s02_shape_survival.csv`"),
    )
    s02 = pd.read_csv(S4_EXP / "s02_shape_survival.csv")
    surv = s02[s02["survives"].notna()]
    n_surv = int((surv["survives"] == "yes").sum())
    print(f"shape survival: {n_surv}/{len(surv)}")
    P.caption("SF48", f'''
    Bridge-shape survival matrix (main-text Fig 5a until 2026-09-09): each SMR percentile
    case x market world cell shows the 2050 shadow price over its peak, with the decay-class
    glyph; a cell survives when the case keeps its decay class or its end-over-peak ratio
    moves by at most 0.15. The shape survives in {n_surv} of {len(surv)} cells — the
    expensive-world non-decay is generic, not a base-world artifact.
    ''')
    """),

    # ------------------------------------------------------------ SF54-56
    md(r"""
    ## SF54 — The value of watching: EVSI and EVPPI on the credit-scale decision

    **What this shows** (new 2026-09-09; `z-ethan/voi/`, SN11; SF49–53 are
    reserved for the batch-6 exhibits). The decision is the scale of the
    reference credit path to declare; the loss is the quantile loss whose
    optimal act is the paper's own rule (cover the requirement in 90% of cost
    worlds), priced in outlay dollars. Top row: the expected value of the
    noisy completed-unit costs observed so far (EVSI, 2024$B of avoided loss)
    against the spend committed before the observation, at three noise levels
    and in the near-perfect-observation limit; the dashed line is the value of
    perfect information about the years still to be priced (sunk years are
    excluded — the information arrives only because building proceeds).
    Bottom row: the share of that remaining value the observations recover.
    Second panel: which input dial is worth knowing (EVPPI as a share of
    EVPI, cross-fitted, with the permutation noise floor). The posterior is
    leave-one-out (the truth world is removed from the candidate set); the
    truth-included widths reproduce the frozen `u10` table exactly (gate G1).
    """),
    code(r"""
    p90v = pd.read_csv(VOI_EXP / "p90_verdict.csv").set_index("name")
    for g_ in ["G0", "G1", "G3", "G4", "G4a", "G5"]:
        assert str(p90v.loc[g_, "result"]).startswith("PASS"), (g_, p90v.loc[g_, "result"])
    p12v = pd.read_csv(VOI_EXP / "p12_evsi_curves.csv")
    hv = p12v[(p12v["alpha"] == 0.9) & (p12v["sigma"] == 0.3) & (p12v["k"] >= 0)]
    lastv = hv[hv["k"] == hv.groupby("schedule")["k"].transform("max")].set_index("schedule")
    fr_lo, fr_hi = lastv["frac_recovered_dollar"].min(), lastv["frac_recovered_dollar"].max()
    pri = p12v[(p12v["alpha"] == 0.9) & (p12v["sigma"] == 0.3) & (p12v["k"] == -1)].set_index("schedule")
    ev_lo, ev_hi = pri["evpi_dollar_B"].min(), pri["evpi_dollar_B"].max()
    p11v = pd.read_csv(VOI_EXP / "p11_evppi.csv")
    grp = p11v[(p11v["alpha"] == 0.9) & (p11v["dial"].str.startswith("group")) & (p11v["bins"] == 49)].set_index("schedule")["share_of_evpi_dollar"]
    P.show_panel(VOI_FIG / "y01_evsi_curves.png")
    P.show_panel(VOI_FIG / "y02_evppi.png")
    P.source_ref(
        (VOI_FIG / "y01_evsi_curves.png", "voi/voi.ipynb", "A cells (y01)",
         "`voi/exports/p12_evsi_curves.csv` (paired EVSI/EVPI on 500 truth worlds x 10 histories; "
         "`p00_posterior_summaries.npz` cache; `p10_prior_evpi.csv` on the full ensemble)"),
        (VOI_FIG / "y02_evppi.png", "voi/voi.ipynb", "EVPPI cell (y02)",
         "`voi/exports/p11_evppi.csv` (cross-fitted 50-bin conditional quantiles, 20 permutations)"),
    )
    P.caption("SF54", f'''
    The value of watching. Top: expected value of the completed-unit cost observations so far
    (EVSI, 2024$B of avoided loss under the quantile loss whose optimal act is the 90%-coverage
    rule), against the spend committed before the observation, one column per schedule, three
    noise levels and the near-perfect-observation limit; dashed = the value of perfect
    information about the years still to be priced (full-horizon EVPI {ev_lo:.1f}-{ev_hi:.1f} B$
    across schedules). Bottom: the share of that remaining value recovered; after the last usable
    observation at medium noise it is {fr_lo:.2f}-{fr_hi:.2f}. Second figure: the value of knowing
    one input dial exactly as a share of EVPI (cross-fitted; error bars = two permutation SDs);
    the two SMR cost dials jointly carry {grp.min():.2f}-{grp.max():.2f} of EVPI (the large-reactor
    dials are identical to the SMR dials in these worlds — the ensemble couples the two technologies —
    and are omitted from the bars). Leave-one-out
    posterior; sunk years excluded; SMR program. Tables: ST19. Registration: voi/methods.md (SN11).
    ''')
    """),

    md(r"""
    ## SF55 — The stopping decision as a Bayes sequential decision

    **What this shows** (new 2026-09-09). Each calendar year the government
    holds the posterior probability that the program's bill will exceed a
    spending cap (costs plus its own outlay ledger). The Bayes rule stops the
    first year that probability reaches a threshold chosen to minimize the
    expected loss: wasted spend in worlds whose bill truly exceeds the cap,
    plus a false-stop price (in multiples of the median-world bill) for
    stopping a world that would have stayed under it. Top figure: the
    expected loss of the Bayes rule against the false-stop price at the 1.5x
    cap and three noise levels, with the ledger-only rule (stop when spend
    reaches the cap) as the whole prior risk, and today's 5% false-alarm rule
    marked at the false-stop price it implies. Bottom figure: the optimal
    threshold and its false-stop rate against the price, for four caps. The
    least-squares Monte Carlo optimal-stopping check is in ST19.
    """),
    code(r"""
    p20v = pd.read_csv(VOI_EXP / "p20_stopping_bayes.csv")
    h20v = p20v[(p20v["sigma"] == 0.3) & (p20v["mult"] == 1.5)]
    p22v = pd.read_csv(VOI_EXP / "p22_conformal_reference.csv")
    h22v = p22v[(p22v["sigma"] == 0.3) & (p22v["mult"] == 1.5)]
    P.show_panel(VOI_FIG / "y03_bayes_risk_frontier.png")
    P.show_panel(VOI_FIG / "y03b_threshold_vs_rho.png")
    P.source_ref(
        (VOI_FIG / "y03_bayes_risk_frontier.png", "voi/voi.ipynb", "B cells (y03)",
         "`voi/exports/p20_stopping_bayes.csv` + `p22_conformal_reference.csv` (LSMC check: `p21_stopping_lsmc.csv`)"),
        (VOI_FIG / "y03b_threshold_vs_rho.png", "voi/voi.ipynb", "B cells (y03b)", "`voi/exports/p20_stopping_bayes.csv`"),
    )
    r1 = h20v[h20v["rho"] == 1.0].set_index("schedule")
    P.caption("SF55", f'''
    The stopping decision as a Bayes sequential decision (cap = 1.5x the median-world bill).
    Top: expected loss of the Bayes rule (stop the first year the posterior probability of
    exceeding the cap reaches the optimal threshold) against the price of a false stop (2024$B;
    top axis: multiples of the median-world bill), at three noise levels (shaded: cluster-bootstrap 95%
    interval); dashed: the ledger-only rule, which is the whole prior risk because perfect
    information would stop every exceeding world at once; diamond: today's 5% false-alarm rule
    at the false-stop price it implies ({h22v["rho_implied"].min():.2f}-{h22v["rho_implied"].max():.2f}
    median-world bills across the reported schedules). At a one-to-one price the Bayes rule
    removes {r1["frac_recovered"].min():.2f}-{r1["frac_recovered"].max():.2f} of the prior risk with
    false-stop rates {r1["false_stop_rate"].min():.2f}-{r1["false_stop_rate"].max():.2f}. Bottom: the
    optimal threshold and its false-stop rate against the price for four caps (medium noise).
    Cells with fewer than 30 truth worlds on one side are omitted. Information, never a
    recommendation: the false-stop price is the reader's parameter. Tables: ST19.
    ''')
    """),

    md(r"""
    ## SF56 — The grant cut-off year: commitment horizon and abandonment trigger

    **What this shows** (new 2026-09-09; the Fig 4 window of 2035 stays until
    Ethan's reading). Grants pay only the part of the requirement above the
    statutory ceiling, so the demonstration window is either a commitment
    horizon chosen now or an abandonment trigger learned from data — never a
    "stop when graduated" rule. Top figure: for each window end year, the
    share of cost worlds with no above-ceiling need after the window
    (coverage) against the expected grant cost of the window, at the 60% and
    50% ceilings, with the requirement band ends and the paper's 3-point
    display allowance; dashed lines mark 75% and 90% coverage. Bottom figure:
    the Bayes abandonment rule — stop grants when the posterior probability
    that the world never becomes credit-feasible reaches the optimal threshold
    — against the price of abandoning a world that would have graduated.
    """),
    code(r"""
    p32v = pd.read_csv(VOI_EXP / "p32_cutoff_pick.csv")
    pk = p32v[(p32v["cut"] == "reg") & (p32v["band"] == "base") & (p32v["cap"] == 0.6)]
    pk90 = pk[pk["alpha"] == 0.9].set_index("schedule")["T_alpha"]
    pk75 = pk[pk["alpha"] == 0.75].set_index("schedule")["T_alpha"]
    lastb = {"eia": 2050, "aj": 2050, "iaea": 2050, "mck": 2050, "cop28": 2050, "eo": 2050}
    def _fmt(s):
        return ", ".join(f"{k} {int(v) if 0 < v < lastb[k] else 'none before the horizon'}" for k, v in s.items())
    p33v = pd.read_csv(VOI_EXP / "p33_abandonment_bayes.csv")
    h33v = p33v[(p33v["sigma"] == 0.3) & (p33v["cap"] == 0.6) & (p33v["cut"] == "reg") & (p33v["rho_g"] == 0.5)]
    P.show_panel(VOI_FIG / "y04_cutoff_frontier.png")
    P.show_panel(VOI_FIG / "y05_abandonment_frontier.png")
    P.show_panel(VOI_FIG / "y06_window_decision.png")
    p34v = pd.read_csv(VOI_EXP / "p34_window_decision.csv")
    hb = p34v[(p34v["rule"] == "bayes") & (p34v["param"] == 1.0) & (p34v["cap"] == 0.6) & (p34v["cut"] == "reg")
              & (p34v["band"] == "base")].set_index("schedule")
    hq9 = p34v[(p34v["rule"] == "cond_quantile") & (p34v["param"] == 0.9) & (p34v["cap"] == 0.6) & (p34v["cut"] == "reg")
               & (p34v["band"] == "base")].set_index("schedule")
    wb = ", ".join(f"{ab} {int(hb.loc[ab, 'T_pick'])} ({hb.loc[ab, 'T_range_over_rho']})" for ab in P.SCHEDULES)
    wq = ", ".join(f"{ab} {int(hq9.loc[ab, 'T_pick'])}" for ab in P.SCHEDULES)
    P.source_ref(
        (VOI_FIG / "y06_window_decision.png", "voi/voi.ipynb", "C1b cells (y06)",
         "`voi/exports/p34_window_decision.csv` (Bayes window, conditional-quantile window) + "
         "`p35_marginal_cost_ladder.csv`"),
        (VOI_FIG / "y04_cutoff_frontier.png", "voi/voi.ipynb", "C1 cells (y04)",
         "`voi/exports/p31_cutoff_frontier.csv` + `p32_cutoff_pick.csv` (generalizes u51/u52 over the window end; "
         "reproduces them exactly at 2033/2035 — gate G0)"),
        (VOI_FIG / "y05_abandonment_frontier.png", "voi/voi.ipynb", "C2 cells (y05)", "`voi/exports/p33_abandonment_bayes.csv`"),
    )
    P.caption("SF56", f'''
    The grant cut-off year. Top: coverage (share of cost worlds with no above-ceiling need
    after the window) against the expected grant cost of the window (2024$B) as the window end
    moves through the build years, 60% ceiling (solid, labelled by end year) and 50% ceiling
    (dashed), requirement band ends faint, the 3-point display allowance dotted; dashed
    horizontals = 75% and 90% coverage. Shortest window reaching 90% coverage at the 60%
    ceiling (registered cushion, base band): {_fmt(pk90)}; reaching 75%: {_fmt(pk75)} (none = not
    within the horizon; picks at 2047 or later are horizon-censored; EIA builds from 2038 and is
    not comparable). Bottom: expected loss of the Bayes abandonment rule against the price of
    abandoning a world that would graduate (2024$B; top axis: multiples of the median-world bill),
    three noise levels; dashed = never stop grants. At a price of one half, the rule lowers the risk by
    {h33v["value_B"].min():.1f}-{h33v["value_B"].max():.1f} B$ in the reported schedules. Third figure:
    the window end as a decision — the expected loss of ending grants in each build year (grant
    dollars plus a price per world cut off before it would have graduated) and the optimal year
    against that price (2024$B; top axis: multiples of the median-world bill). The optimum at one
    median-world bill is {wb} (range as the price runs 0.1-2x), beside the price-free window that
    covers 90% of the worlds that ever graduate: {wq}; the paper's Fig 4 carries instead one common
    window end, 2038, the year by which graduation is all but complete in every schedule (Table 2, ST19o). No dollar value of information is computed for the horizon
    choice itself (a perfect-information planner would choose which worlds to serve, which is
    not a realizable policy). Tables: ST19.
    ''')
    """),

    # ---------------------------------------------------------------- SF57 (main-text figure 3 until 2026-09-10)
    md(r"""
    ## SF57 — Why all priced cases commit to a 100%-SMR program, now (main-text figure 3 until 2026-09-10)

    Moved to the SI on 2026-09-10 (the coauthor cut for draft v3: five main figures).
    The main text keeps one sentence on the technology choice; this page keeps the full case.

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
        "SF57_technology_choice.png",
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

    P.caption("SF57", '''
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

    # ---------------------------------------------------------------- SF58 (main-text figure 5 until 2026-09-10)
    md(r"""
    ## SF58 — What observation buys, and what it cannot (main-text figure 5 until 2026-09-10)

    Moved to the SI on 2026-09-10 (the coauthor cut for draft v3). Panel (b) stays on the
    five-anchor requirement map and the bill band E5 (pre-refit; the bridge notebooks are
    not re-run under methods.md v2.4).

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
         [RD_FIG / "w37_ci_rate_points_paper_5a.png"]],
        "SF58_cost_of_detection.png",
        letters="ab",
        center=True,
    )
    P.source_ref(
        (BD_FIG / "d13_paid_by_cap_noisy.png", "bridge_detection/bridge_detection_stage3.ipynb",
         "figure cells", "`b17_exceedance_noisy.csv` (spend-aware standard, 2026-08-25 amendment; "
         "spec: `bridge_detection/methods.md` section 6)"),
        (RD_FIG / "w37_ci_rate_points_paper_5a.png", "rate_design/rate_design_v2_5a.ipynb",
         "S7 w37 cell (the w36/w20 grid with the credit-scale row re-denominated in "
         "statutory rate points; Ethan's reading review 2026-09-02) — the FIVE-ANCHOR twin "
         "(RD_ANCHORS=5a; 2026-09-08, methods.md v2.3; display basis per u101 `display-basis`)",
         "`u32_ci_rate_points_5a.csv` (= u10_5a widths x the reference path's outlay-weighted "
         "average rate) + `u30_part_a_restated_5a.csv` (the v1 sweep re-run on the five-anchor "
         "requirement map, band E5; the three-anchor originals are the frozen audit record: "
         "SF39/ST16d-f)"),
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

    u30 = pd.read_csv(RD_EXP / "u30_part_a_restated_5a.csv").set_index("schedule")
    assert not u30["crosses_band5"].any()
    _e5 = float(pd.read_csv(BD_EXP / "b07_bill_attachment_5a.csv")["band_e5"].iloc[0])
    _u101 = pd.read_csv(RD_EXP / "u101_verdict.csv").set_index("name")
    assert _u101.loc["display-basis", "result"] == "FIVE-ANCHOR", _u101.loc["display-basis", "result"]
    ratio_lo, ratio_hi = u30["final_over_tgt"].min(), u30["final_over_tgt"].max()
    plateau = "/".join(u30.index[u30["label"] == "asymptote"])
    lr0 = u30["prior_lr_w_pts"].max()
    lr_lo, lr_hi = u30["final_lr_w_pts"].min(), u30["final_lr_w_pts"].max()
    print(f"credit-scale CI never crosses the design target (0/6 schedules, all noise "
          f"levels); final mid-noise width {ratio_lo:.1f}-{ratio_hi:.1f}x the target; "
          f"plateau label: {plateau} only")
    print(f"learning-rate CI narrows {lr0:.1f} -> {lr_lo:.1f}-{lr_hi:.1f} points (5-95)")

    u32 = pd.read_csv(RD_EXP / "u32_ci_rate_points_5a.csv")
    fin32 = u32[u32["k"] == u32.groupby(["schedule", "sigma"])["k"].transform("max")]
    def _rng(sig):
        f = fin32[fin32["sigma"] == sig]["width_pts"]
        return f.min(), f.max()
    pm_lo, pm_hi = _rng(0.30); pl_lo, pl_hi = _rng(0.15); ph_lo, ph_hi = _rng(0.50)
    pri32 = u32[(u32["k"] == 0) & (u32["sigma"] == 0.30)]["width_pts"]
    assert pm_hi < 60 and pm_lo > 5, (pm_lo, pm_hi)
    print(f"required-credit 90% interval width, statutory points: prior {pri32.min():.0f}-{pri32.max():.0f}; "
          f"final mid {pm_lo:.0f}-{pm_hi:.0f}, light {pl_lo:.0f}-{pl_hi:.0f}, heavy {ph_lo:.0f}-{ph_hi:.0f}; target 5")

    P.caption("SF58", f'''
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
    design quantity is not (five-anchor requirement map, certificate band E5 = {_e5:.2f} — 2026-09-08; the
    three-anchor audit grid in scale units: SF39). Together: observation tells the government when to stop
    paying, not how much to pay. Both observers know the ensemble and the noise model —
    upper bounds on real learnability; information, not a recommendation.
    ''')
    """),

    # ---------------------------------------------------------------- SF59 (main-text figure 4 until 2026-09-10)
    md(r"""
    ## SF59 — The solved cost gap at the anchor worlds (main-text figure 4 until 2026-09-10)

    Moved to the SI on 2026-09-10: the new main-text figure 3 shows the same quantity fanned
    across the 10,000 cost worlds on the batch-6 refit map; this page keeps the direct model
    solutions at the three percentile anchors per schedule (the evidence the map
    interpolates) and the decay reading.

    Recomposed 2026-08-26 (Ethan): the normalized-decay panel (old 4b,
    `f07`) moved to the SI as SF32. **Re-denominated 2026-09-09 (Ethan's
    figure revisions):** the fans now read in **2024\$/kW of mandated
    capacity** — the shadow price capitalized over the model's own 30-year
    evaluation window — and the large-reactor overlay left (the comparison
    lives in Fig 5b). Source `f04b`; the rental-basis original `f04` stays
    in the step3 notebook.

    **The unit.** ReEDS reports the mandate's shadow price on a rental basis:
    the raw dual divided by `pvf_onm`, the model's 30-year annuity factor
    (14.76, flat from 2026; QA-certified in `step3_checks`). Multiplying back
    by that factor recovers the raw dual exactly: the year's capitalized cost
    gap of the marginal build — its capitalized cost over the evaluation
    window minus its capitalized market value — on ReEDS's financed basis
    (overnight cost × the financing multiplier, the same basis as Fig 2's
    financed capital cost). So the axis reads as "how much lower the financed
    capital cost would have to be, in that year's solve, for the mandated
    builds to be competitive without support"; no conversion through
    overnight cost is involved. Two caveats the caption carries once: the gap
    also contains the marginal build's O&M and market-value terms, so a
    capital-cost cut is one way to close it, not its sole cause; and as an
    overnight-cost cut the number is about 1.27× smaller (a dollar of
    overnight cost carries 1.27 dollars of capitalized cost). Under the
    sequential myopic solve the capitalized shadow price and the required
    cost reduction are the same number; only the reading differs.

    **How to read it.** A "bridge" subsidy should decay: high at first, near
    zero once the fleet has walked down the learning curve. The normalized
    decay curves that test that shape directly are SF32. Decay ratios are
    unit-free, so every shape statement below is unchanged by the
    re-denomination.

    **Key results** (computed in the cell below; the rental-basis values in
    the S3 text convert at ×14.76).
    - The gap is monotone in the cost world: expensive worlds need more in
      every year, with no crossings. Mean binding gaps run about
      1,000–3,000 (P5), 4,600–5,800 (P50), and 9,000–10,300 (P95) in
      2024\$/kW; the single peak is about 13,200 (EO schedule, P95 world,
      2031).
    - In cheap worlds the bridge comes down: end-of-horizon gaps are 3–19% of
      peak. Median worlds are mixed. **In P95 worlds the subsidy does not
      come down: 66–84% of peak in 2050, and no P95 case falls below half its
      peak by 2050** (SF32). Under slow learning the subsidy is not a bridge
      but a standing commitment. We give this adverse result the same
      prominence as the decay result.
    - The cross-section of the mean binding shadow price against schedule
      ambition is SF-ambition (`f06`, rental basis).
    """),
    code(r"""
    P.compose(
        [[S3_FIG / "f04b_capex_gap_fans.png"]],
        "SF59_shadow_price.png",
        letters="",  # single panel: no letter stamp
    )
    P.source_ref(
        (S3_FIG / "f04b_capex_gap_fans.png", "step3_analysis/step3_analysis.ipynb",
         "cell f04b-capex-gap (added 2026-09-09 by `_edit_20260909_capex_panels.py`)",
         "`step3_checks/exports/duals_by_year.csv` x pvf_onm (14.7645, read from the runs' own h5 and asserted flat)"),
    )

    PVFO = 14.7645   # pvf_onm = 1/crf, flat from 2026 in every run (step3_checks QA; asserted in f04b)
    _prod = lambda df: df[~df["case"].str.contains("_p25|_p75")]   # the 37 production cases (anchors 09-08 excluded)
    t03 = _prod(pd.read_csv(S3_EXP / "t03_dual_summary.csv"))
    t04 = _prod(pd.read_csv(S3_EXP / "t04_bridge_metrics.csv"))
    smr = t03[t03["case"].str.startswith("smr100")]
    for pct in ["p05", "p50", "p95"]:
        sel = smr[smr["case"].str.endswith(pct)]
        print(f"{pct}: mean binding gap {sel['mean_binding_dual_2024_kWyr'].min() * PVFO:,.0f}"
              f"-{sel['mean_binding_dual_2024_kWyr'].max() * PVFO:,.0f} 2024$/kW "
              f"(rental basis {sel['mean_binding_dual_2024_kWyr'].min():.0f}"
              f"-{sel['mean_binding_dual_2024_kWyr'].max():.0f} $/kW-yr)")
    pk = smr.loc[smr["peak_dual_2024_kWyr"].idxmax()]
    pk_gap = float(pk["peak_dual_2024_kWyr"]) * PVFO
    # independent chain check: t09's capitalized gap S_t (2004$/MW) for the peak case-year
    t09 = pd.read_csv(S3_EXP / "t09_required_itc.csv")
    s_t = t09[(t09["case"] == pk["case"]) & (t09["t"] == int(pk["peak_year"]))]["S_t_2004_per_MW"]
    s_t_kw = float(s_t.iloc[0]) * TO2024 / 1000.0
    assert len(s_t) == 1 and abs(s_t_kw - pk_gap) < 2.0, (s_t_kw, pk_gap)
    print(f"peak gap: {pk_gap:,.0f} 2024$/kW ({pk['case']}, {int(pk['peak_year'])}); t09 S_t agrees ({s_t_kw:,.0f})")
    p95 = t04[t04["case"].str.startswith("smr100") & t04["case"].str.endswith("p95")]
    n_below = int((p95["first_year_below_half_peak"] <= 2050).sum())
    print(f"p95 end/peak: {p95['end_over_peak'].min():.2f}-{p95['end_over_peak'].max():.2f}; "
          f"p95 cases below half-peak by 2050: {n_below} of {len(p95)}")

    P.caption("SF59", f'''
    The required subsidy as a capital-cost gap. The mandate's shadow price capitalized over
    the model's 30-year evaluation window (x {PVFO:.2f}): the reduction in financed capital
    cost per kW of mandated capacity (2024$) that would make each year's mandated builds
    competitive without support, by solve year, for each schedule in cheap (P5), median
    (P50), and expensive (P95) cost worlds; SMR program (the large-reactor comparator is in
    Fig 5b). The gap includes the marginal build's O&M and market-value terms, so a
    capital-cost cut is one way to close it; as an overnight-cost cut it is about 1.27x
    smaller (the financing multiplier), and Fig 2's 2022$ convert to 2024$ at 1.07. Gaps
    rise with the cost world in every year, with no crossings, peaking at {pk_gap:,.0f} $/kW
    ({pk['case']}, {int(pk['peak_year'])}). In cheap worlds the gap decays to 3-19% of its
    peak by 2050; no P95 case reaches half its peak — under slow learning the subsidy is a
    standing commitment, not a bridge (normalized decay curves: SF32).
    ''')
    """),

    # ---------------------------------------------------------------- ST1-8
    md(r"""
    ## Supplementary tables (ST1–ST19)

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

    The consolidated detection tables (SN8; cited from S3-3 and SF58):
    detection years under the calibrated 5%-false-alarm rule — perfect
    observation (b09) and the three noise levels (b15); the cost of waiting
    with the noise gradient (b18; under the spend-aware standard the cap
    criterion's never-detected share is zero by construction, so its
    columns carry the paid-at-detection medians); the bias experiment (b19:
    an observer who mistakes a 30% systematic overrun for an expensive
    world false-alarms on 23–35% of benign worlds; an observer who knows
    the bias loses nothing); and the full cap-grid exceedance table behind
    SF58 and SF27 (b17: detection-year quartiles, completed US units at
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
    held-out false-alarm rate, costs-only reference columns; behind SF58 and SF27).
    Observer design, noise model, and calibration in SN8.
    ''')
    """),
    md(r"""
    ### ST13 — The budget-menu sweep

    The tables behind Fig 4a (new 2026-08-31, plan v10.42; menu reframing
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
    The budget-menu sweep (behind Fig 4a): per schedule and cap, the affordable credit
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

    The tables behind main-text Fig 3, Fig 4 and Table 2 (k–o, the batch-6 refit map,
    registered one-point cushion, band E6 per schedule; 2026-09-10) and behind SF34/SF38
    (a–j, the pre-refit five- and three-anchor maps; new 2026-09-02; SN9; cited from S3-4): the requirement fans with per-cell censor and clamp
    columns (u50); the feasibility mask per year and per world, at both
    caps and all three certificate-band points — the only quotable form is
    the cap x band range (u51); the demonstration-gap fans per cap x band
    x window, with the window-applicability flag (eia N/A) (u52); the
    dollar-menu zone table (u53); and the exposure/wedge summary (u54).
    Registration and kill dispositions (KB1/KB2/KB3): `rate_design/methods.md`
    v2/v2.1 + `u91_verdict.csv`.
    """),
    code(r"""
    # five-anchor primaries (2026-09-08; the display basis per u101) ...
    P.table(RD_EXP / "u50_requirement_fans_5a.csv", "ST14a_requirement_fans_5a.csv", round_=4)
    P.table(RD_EXP / "u51_feasibility_mask_5a.csv", "ST14b_feasibility_mask_5a.csv", round_=4)
    P.table(RD_EXP / "u52_demonstration_gap_5a.csv", "ST14c_demonstration_gap_5a.csv", round_=3)
    P.table(RD_EXP / "u53_dollar_menu_5a.csv", "ST14d_dollar_menu_5a.csv", round_=4)
    P.table(RD_EXP / "u54_exposure_summary_5a.csv", "ST14e_exposure_summary_5a.csv", round_=3)
    # ... and the three-anchor originals (the frozen audit record and the batch-placement basis)
    P.table(RD_EXP / "u50_requirement_fans.csv", "ST14f_requirement_fans_3a.csv", round_=4)
    P.table(RD_EXP / "u51_feasibility_mask.csv", "ST14g_feasibility_mask_3a.csv", round_=4)
    P.table(RD_EXP / "u52_demonstration_gap.csv", "ST14h_demonstration_gap_3a.csv", round_=3)
    P.table(RD_EXP / "u53_dollar_menu.csv", "ST14i_dollar_menu_3a.csv", round_=4)
    P.table(RD_EXP / "u54_exposure_summary.csv", "ST14j_exposure_summary_3a.csv", round_=3)
    # the batch-6 refit map (2026-09-10; the basis of main-text Fig 3, Fig 4 and Table 2): registered one-point tables
    P.table(RD2_EXP / "m20_requirement_fans.csv", "ST14k_requirement_fans_refit.csv", round_=4)
    P.table(RD2_EXP / "m21_feasibility_mask.csv", "ST14l_feasibility_mask_refit.csv", round_=4)
    P.table(RD2_EXP / "m22_demonstration_gap.csv", "ST14m_demonstration_gap_refit.csv", round_=3)
    P.table(RD2_EXP / "m23_common_window_table.csv", "ST14n_common_window_refit.csv", round_=4)
    P.table(RD2_EXP / "m13_band_e6.csv", "ST14o_band_e6_refit.csv", round_=3)
    _e5 = float(pd.read_csv(BD_EXP / "b07_bill_attachment_5a.csv")["band_e5"].iloc[0])
    P.caption("ST14", f'''
    Declining-credit tables. (k-o) The batch-6 refit map behind main-text Fig 3, Fig 4 and Table 2:
    requirement fans (m20), the feasibility mask (m21), the demonstration gap (m22), the common-window
    table (m23) and the per-schedule leave-one-out error with the band E6 (m13); registered one-point
    cushion; the paper's display twins subtract three points. (a-j) The pre-refit maps behind SF34/SF38,
    on the five-anchor map (a-e;
    p05/p25/p50/p75/p95 mandate anchors, certificate band E5 = {_e5:.2f}, the leave-one-out
    error of the interior anchors; 2026-09-08) with the three-anchor originals beside them
    (f-j; the frozen audit record and the basis on which the batch was placed and scored):
    requirement fans with censor/clamp columns (u50); the feasibility mask per year and per
    world at both caps and all three certificate-band points — quotable only as cap x band
    ranges (u51); demonstration-gap fans per cap x band x window with the
    window-applicability flag (u52); the dollar-menu zone table (u53); the exposure/wedge
    summary (u54). Kill dispositions KB1/KB2/KB3 and the certificate chain:
    rate_design/methods.md v2 -> v2.3 + u91_verdict.csv / u91_verdict_5a.csv (SN9).
    ''')
    """),
    md(r"""
    ### ST15 — The 66-run batch: verdict, gate tables, and spec

    **Adjudicated 2026-09-08 (SN9; cited from S3-4.5).** The batch returned on
    2026-09-08 (66 h5 files, `rate_design_checks` 40 PASS / 13 INFO / 0 FAIL).
    Every gate registered before launch (`rate_design/methods.md` v2.1–v2.2.2)
    was applied with the mechanics registered before any output was read
    (v2.3): the verdict (u101) with the claim-ladder rung reached; the per-run
    gate table (u100); the GE2 boundary-depth reads per schedule x budget
    (u102); the GH2 cap-depth reads per cap (u103); GA2 (u104) and GA3 (u105)
    at the 12 p25/p75 anchors; GX1 per schedule (u106); the five-anchor summary
    (u107); the five-anchor re-margining of the frozen run worlds — the
    registered secondary read, never scored (u85); the per-year rate
    leave-one-out at the interior anchors (u86). The spec: the ITC-arm + horizon
    batch (u80) and the per-run offered credit paths (u81); the anchor spec (u82)
    with the pre-run predictions (u84). The capture machinery (u70/u71/u73) is
    kept for the record: on the FAIL rung no capture number is quotable (K1 rule).
    """),
    code(r"""
    P.table(RD_EXP / "u101_verdict.csv", "ST15a_verdict.csv")
    P.table(RD_EXP / "u100_gate_table.csv", "ST15b_gate_table.csv", round_=4)
    P.table(RD_EXP / "u102_ge2_depth.csv", "ST15c_ge2_depth.csv", round_=4)
    P.table(RD_EXP / "u103_gh2_cap_depth.csv", "ST15d_gh2_cap_depth.csv", round_=4)
    P.table(RD_EXP / "u104_ga2_bills.csv", "ST15e_ga2_bills.csv", round_=4)
    P.table(RD_EXP / "u105_ga3_rates.csv", "ST15f_ga3_rates.csv", round_=4)
    P.table(RD_EXP / "u106_gx1.csv", "ST15g_gx1.csv", round_=4)
    P.table(RD_EXP / "u107_five_anchor_summary.csv", "ST15h_five_anchor_summary.csv", round_=4)
    P.table(RD_EXP / "u85_remargin_5a.csv", "ST15i_remargin_5a.csv", round_=4)
    P.table(RD_EXP / "u86_anchor_loo_rates_5a.csv", "ST15j_anchor_loo_rates_5a.csv", round_=4)
    P.table(RD_EXP / "u80_batch_spec.csv", "ST15k_batch_spec.csv", round_=4)
    P.table(RD_EXP / "u81_run_schedules.csv", "ST15l_run_schedules.csv", round_=1)
    P.table(RD_EXP / "u82_anchor_spec.csv", "ST15m_anchor_spec.csv", round_=4)
    P.table(RD_EXP / "u84_anchor_predictions.csv", "ST15n_anchor_predictions.csv", round_=4)
    P.table(RD_EXP / "u70_contour_schedules_kw.csv", "ST15o_contour_schedules_kw.csv", round_=1)
    P.table(RD_EXP / "u71_capture_decomposition.csv", "ST15p_capture_decomposition.csv", round_=4)
    P.table(RD_EXP / "u73_no2050_sensitivity.csv", "ST15q_no2050_sensitivity.csv", round_=4)
    _v = pd.read_csv(RD_EXP / "u101_verdict.csv").set_index("name")
    assert _v.loc["rung", "result"] == "FAIL", _v.loc["rung", "result"]
    _u100 = pd.read_csv(RD_EXP / "u100_gate_table.csv")
    _dl = _u100[_u100["counts_as_delivering"] & _u100["block"].isin(["envelope", "boundary"])]
    _u104 = pd.read_csv(RD_EXP / "u104_ga2_bills.csv")
    _u106 = pd.read_csv(RD_EXP / "u106_gx1.csv")
    _u85 = pd.read_csv(RD_EXP / "u85_remargin_5a.csv")
    _u85e = _u85[_u85["block"] != "hybrid"]
    _nflip = int((_u85e["side_3a"] != _u85e["side_5a"]).sum())
    _e5 = float(pd.read_csv(BD_EXP / "b07_bill_attachment_5a.csv")["band_e5"].iloc[0])
    P.caption("ST15", f'''
    The 66-run batch, adjudicated 2026-09-08: the verdict (u101; claim-ladder rung
    {_v.loc["rung", "result"]}), the per-run gate table (u100), the GE2 boundary-depth reads
    (u102), the GH2 cap-depth reads (u103), GA2 at the 12 anchors (u104: signed bill errors
    {_u104["signed_rel_err"].min():+.2f} to {_u104["signed_rel_err"].max():+.2f}, all inside
    +-20%), GA3 (u105), GX1 (u106: the extended runs shed
    {_u106["shed_fraction"].max():.2f} of the 2047-2050 uptick — it persists), the
    five-anchor summary (u107: E5 = {_e5:.2f}), the five-anchor re-margining of the frozen
    run worlds (u85: {_nflip} of {len(_u85e)} envelope/boundary worlds change side, hybrids compared on the cap excess; a disclosed secondary read, never
    scored), the per-year rate leave-one-out (u86), the batch spec (u80/u81/u82/u84) and the
    capture machinery (u70/u71/u73 — not quotable on the FAIL rung; K1 stands). GE1/GH1:
    {_v.loc["GE1", "result"]}/{_v.loc["GH1", "result"]} — true failures on the eo and cop28
    marginal worlds (the -1-point runs) and the eo cap-never-binds hybrid, while the
    comfortable runs of every schedule deliver; the {len(_dl)} delivering envelope/boundary
    runs build {_dl["delivered_frac_2050"].min():.2f}-{_dl["delivered_frac_2050"].max():.1f}x
    their 2050 target (median {_dl["delivered_frac_2050"].median():.1f}x): induced take-up
    breaks any uncapped every-world outlay bound. Registration and mechanics:
    rate_design/methods.md v2.1 -> v2.3 (SN9); figures SF43-SF47.
    ''')
    """),
    md(r"""
    ### ST16 — Cost-of-information tables

    The tables behind SF58b and SF37 (new 2026-09-02; SN9; cited from
    S3-3): per schedule, the design target, the final credit-scale CI
    width and its ratio to the target (4.8–7.7x), the plateau label under
    the ≤5%-per-observation rule, the learning-rate CI narrowing
    (11.7 → 4.3–9.3 points), and the effective-sample columns (u30); the
    mid-noise width-vs-committed-spend path per observation (u31); and the
    SF58b series itself — the credit-rate interval width in statutory
    points and the learning-rate interval width in points at every
    observation, all three noise levels, with the per-schedule conversion
    constant (u32).
    """),
    code(r"""
    P.table(RD_EXP / "u30_part_a_restated_5a.csv", "ST16a_part_a_restated_5a.csv", round_=3)
    P.table(RD_EXP / "u31_part_a_slopes_5a.csv", "ST16b_part_a_slopes_5a.csv", round_=4)
    P.table(RD_EXP / "u32_ci_rate_points_5a.csv", "ST16c_ci_rate_points_5a.csv", round_=2)
    P.table(RD_EXP / "u30_part_a_restated.csv", "ST16d_part_a_restated_3a.csv", round_=3)
    P.table(RD_EXP / "u31_part_a_slopes.csv", "ST16e_part_a_slopes_3a.csv", round_=4)
    P.table(RD_EXP / "u32_ci_rate_points.csv", "ST16f_ci_rate_points_3a.csv", round_=2)
    P.caption("ST16", '''
    Cost-of-information tables (behind SF58b, SF37 and SF39), on the five-anchor map (a-c,
    the SF58b basis since 2026-09-08) with the three-anchor originals beside them (d-f, the
    frozen audit record behind SF39): per schedule, the design
    target, final credit-scale CI width and its ratio to the target, the plateau label
    under the <=5%-per-observation rule, the learning-rate CI narrowing, and the
    effective-sample columns (u30); the mid-noise width-vs-committed-spend path (u31);
    the SF58b series (credit-rate width in statutory points, learning-rate width in
    points) at all three noise levels, with the per-schedule conversion constant (u32).
    The v1 sweep is the frozen input, restated with every audit repair; registration
    and dispositions: rate_design/methods.md v2/v2.1 + u91_verdict.csv (SN9).
    ''')
    """),
    md(r"""
    ### ST17 — Market-world sensitivity tables

    The step4 tables behind Fig 5a/Fig 5b and SF20–SF22 (cited from S4-a/b/c):
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
    Market-world sensitivity tables (behind Fig 5a/Fig 5b and SF20-SF22): binding-year shifts
    (s01); the shape-survival matrix with its components - decay class and end-over-peak
    ratio vs base (s02); ranking preservation with Kendall tau and the raw orderings per
    sensitivity x percentile cell (s03); level ratios, like-for-like over shared binding
    years with the own-years companion (s04); the prior-signed mechanism check (s05). The
    18 SMR percentile cases x six market worlds = 108 runs; SMR program.
    ''')
    """),
    md(r"""
    ### ST18 — Market-world transfer tables

    The tables behind SF40, SF41 and the Fig 5 caption (new 2026-09-02;
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
    Market-world transfer tables (behind SF40, SF41 and the Fig 5 caption): the required
    credit rate per case-year on all 126 output files with the shadow-price ratio companion
    and the region-set factor (v01); the statutory-mask ranges per world, schedule, ceiling
    and window — band ends and band centre — with the base range and overlap flag (v04); the
    spending-cap alarm's headline cell per world under the own-median-world (P50)-bill and
    fixed-dollar cap readings (v05) and its cross-world summary with min, median, and max
    across worlds (v06); the region-set summary (v07); gates, kills, and quoting
    dispositions (v09). Registration: market_transfer/methods.md (SN10). SMR program.
    ''')
    """),

    md(r"""
    ### ST19 — Decision-value tables

    The tables behind SF54–SF56 (new 2026-09-09; SN11): prior loss and EVPI on
    the full ensemble per band end and coverage target (p10); EVPPI per dial
    with the permutation floor (p11); the EVSI curves with bootstrap intervals,
    realized coverage and regret (p12); the prior stress on the learning rate
    (p13); the Bayes stopping rule per schedule, noise level, cap and
    false-stop price (p20); the LSMC optimal-stopping check (p21); today's
    conformal rule as a reference point with its implied false-stop price
    (p22); the cut-off frontier and picks (p31, p32); the Bayes abandonment
    rule (p33); the window decision (p34), the marginal-cost ladder (p35) and the
    common-window table behind main-text Table 2 (p36, ST19o); gates,
    kills and predictions (p90).
    """),
    code(r"""
    P.table(VOI_EXP / "p10_prior_evpi.csv", "ST19a_prior_evpi.csv", round_=4)
    P.table(VOI_EXP / "p11_evppi.csv", "ST19b_evppi.csv", round_=4)
    P.table(VOI_EXP / "p12_evsi_curves.csv", "ST19c_evsi_curves.csv", round_=4)
    P.table(VOI_EXP / "p13_prior_stress.csv", "ST19d_prior_stress.csv", round_=4)
    P.table(VOI_EXP / "p20_stopping_bayes.csv", "ST19e_stopping_bayes.csv", round_=4)
    P.table(VOI_EXP / "p21_stopping_lsmc.csv", "ST19f_stopping_lsmc.csv", round_=4)
    P.table(VOI_EXP / "p22_conformal_reference.csv", "ST19g_conformal_reference.csv", round_=4)
    P.table(VOI_EXP / "p31_cutoff_frontier.csv", "ST19h_cutoff_frontier.csv", round_=4)
    P.table(VOI_EXP / "p32_cutoff_pick.csv", "ST19i_cutoff_pick.csv", round_=4)
    P.table(VOI_EXP / "p33_abandonment_bayes.csv", "ST19j_abandonment_bayes.csv", round_=4)
    P.table(VOI_EXP / "p34_window_decision.csv", "ST19l_window_decision.csv", round_=4)
    P.table(VOI_EXP / "p35_marginal_cost_ladder.csv", "ST19m_marginal_cost_ladder.csv", round_=4)
    P.table(VOI_EXP / "p36_common_window_table.csv", "ST19o_common_window_table.csv", round_=4)
    P.table(VOI_EXP / "p90_verdict.csv", "ST19n_verdict.csv")
    P.caption("ST19", '''
    Decision-value tables (behind SF54–SF56): prior loss and EVPI on the full ensemble per
    certificate-band end and coverage target, with the clamp share (p10); EVPPI per input dial
    and for the two SMR cost dials jointly, cross-fitted, with bin sweep and permutation floor
    (p11); EVSI by observation with cluster-bootstrap intervals, the fraction of remaining EVPI
    recovered, realized coverage, over-payment, shortfall, regret quantiles and the leave-one-out
    effective sample size (p12); EVPI under a one-standard-deviation tilt of the prior on the
    SMR learning rate (p13); the Bayes stopping rule per schedule, noise level, cap and
    false-stop price (p20); the LSMC optimal-stopping check (p21); the conformal 5% rule as a
    reference point with its implied false-stop price (p22); the cut-off frontier and the
    coverage picks with band-range and censoring flags (p31, p32); the Bayes abandonment rule
    (p33); the window end as a decision — the expected-loss minimizer per price, the
    conditional-quantile window and their band/display-twin flags (p34) and the marginal-cost
    ladder with the reference knee (p35); gates, kills and registered predictions (p90).
    Registration: voi/methods.md (SN11; v1.1 addendum for p34/p35).
    SMR program.
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
