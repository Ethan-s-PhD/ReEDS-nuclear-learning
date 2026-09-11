"""2026-09-09 — register the voi/ decision-value exhibits in the SI (Ethan's ruling: SI only
until he reads the cut-off frontier; SF49–53 stay reserved for batch 6).

Patches (each substitution asserted exactly once):
  paperlib.py            VOI, VOI_FIG, VOI_EXP path constants
  _build_notebooks.py    SETUP aliases; glossary rows (EVSI, Bayes risk); SN header SN1–SN11 + SN11
                         row; SF54–SF56 after SF48; ST header ST1–ST19; ST19 after ST18.
Caption delimiters inside the raw blocks are written as @@Q@@ and restored on insertion.
Run from z-ethan/paper_figures/, then rebuild + execute appendix_figures.ipynb.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
assert HERE.name == "paper_figures", HERE


def sub_once(path, old, new):
    s = path.read_text(encoding="utf-8")
    assert s.count(old) == 1, (path.name, old[:80], s.count(old))
    path.write_text(s.replace(old, new), encoding="utf-8")


# ---- paperlib: the path constants ---------------------------------------------------
sub_once(HERE / "paperlib.py",
         'LIT = REPO / "z-ethan" / "lit_comparison"\nLIT_FIG, LIT_EXP = LIT / "figures", LIT / "exports"\n',
         'LIT = REPO / "z-ethan" / "lit_comparison"\nLIT_FIG, LIT_EXP = LIT / "figures", LIT / "exports"\n'
         'VOI = REPO / "z-ethan" / "voi"\nVOI_FIG, VOI_EXP = VOI / "figures", VOI / "exports"\n')

B = HERE / "_build_notebooks.py"

# ---- SETUP aliases -------------------------------------------------------------------
sub_once(B, "                      LIT_FIG, LIT_EXP)\n", "                      LIT_FIG, LIT_EXP, VOI_FIG, VOI_EXP)\n")

# ---- glossary rows -------------------------------------------------------------------
sub_once(B,
         "| **EVPI (expected value of perfect information)** | The most that knowing the true cost world in advance could be worth, as a share of expected program cost. |\n",
         "| **EVPI (expected value of perfect information)** | The most that knowing the true cost world in advance could be worth, as a share of expected program cost. |\n"
         "| **EVSI (expected value of sample information)** | What the noisy costs of the units completed so far are worth to the decision, computed before seeing them; never more than EVPI. |\n"
         "| **Bayes risk** | The expected loss of a decision rule, averaged over the cost worlds; the Bayes rule is the rule with the smallest Bayes risk. |\n")

# ---- SN pointers ---------------------------------------------------------------------
sub_once(B, "    ## Supplementary Notes (SN1–SN10) — pointers\n", "    ## Supplementary Notes (SN1–SN11) — pointers\n")
sub_once(B,
         "(tables in ST18, figures SF40-SF41; the envelopes in the Fig 7 caption) |\n",
         "(tables in ST18, figures SF40-SF41; the envelopes in the Fig 7 caption) |\n"
         "    | SN11 | The decision value of cost information (new 2026-09-09; SI only until Ethan's reading): EVPI, EVPPI (cross-fitted, permutation-floored) and EVSI on the credit-scale decision under the quantile loss whose optimal act is the paper's 90%-coverage rule, sunk years excluded, leave-one-out posterior; the stopping decision as a Bayes sequential decision (threshold minimizing the Bayes risk at a swept false-stop price, LSMC optimal-stopping check, the conformal 5% rule as a reference point with its implied false-stop price); the grant cut-off year as a coverage-vs-grant-dollars frontier plus an abandonment trigger; gates G0–G7, kills K1–K5, predictions P1–P5 | `z-ethan/voi/methods.md` + `status.md` + `exports/p90_verdict.csv` (tables in ST19, figures SF54–SF56) |\n")

# ---- SF54–SF56 after SF48 ------------------------------------------------------------
SF_BLOCK = r'''
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
    P.caption("SF54", f@@Q@@
    The value of watching. Top: expected value of the completed-unit cost observations so far
    (EVSI, 2024$B of avoided loss under the quantile loss whose optimal act is the 90%-coverage
    rule), against the spend committed before the observation, one column per schedule, three
    noise levels and the near-perfect-observation limit; dashed = the value of perfect
    information about the years still to be priced (full-horizon EVPI {ev_lo:.1f}-{ev_hi:.1f} B$
    across schedules). Bottom: the share of that remaining value recovered; after the last usable
    observation at medium noise it is {fr_lo:.2f}-{fr_hi:.2f}. Second figure: the value of knowing
    one input dial exactly as a share of EVPI (cross-fitted; error bars = two permutation SDs);
    the two SMR cost dials jointly carry {grp.min():.2f}-{grp.max():.2f} of EVPI. Leave-one-out
    posterior; sunk years excluded; SMR program. Tables: ST19. Registration: voi/methods.md (SN11).
    @@Q@@)
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
    P.caption("SF55", f@@Q@@
    The stopping decision as a Bayes sequential decision (cap = 1.5x the median-world bill).
    Top: expected loss of the Bayes rule (stop the first year the posterior probability of
    exceeding the cap reaches the optimal threshold) against the price of a false stop, in
    multiples of the median-world bill, at three noise levels (shaded: cluster-bootstrap 95%
    interval); dashed: the ledger-only rule, which is the whole prior risk because perfect
    information would stop every exceeding world at once; diamond: today's 5% false-alarm rule
    at the false-stop price it implies ({h22v["rho_implied"].min():.2f}-{h22v["rho_implied"].max():.2f}
    median-world bills across the reported schedules). At a one-to-one price the Bayes rule
    removes {r1["frac_recovered"].min():.2f}-{r1["frac_recovered"].max():.2f} of the prior risk with
    false-stop rates {r1["false_stop_rate"].min():.2f}-{r1["false_stop_rate"].max():.2f}. Bottom: the
    optimal threshold and its false-stop rate against the price for four caps (medium noise).
    Cells with fewer than 30 truth worlds on one side are omitted. Information, never a
    recommendation: the false-stop price is the reader's parameter. Tables: ST19.
    @@Q@@)
    """),

    md(r"""
    ## SF56 — The grant cut-off year: commitment horizon and abandonment trigger

    **What this shows** (new 2026-09-09; the Fig 6 window of 2035 stays until
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
    def _fmt(s):
        return ", ".join(f"{k} {int(v) if v > 0 else 'none'}" for k, v in s.items())
    p33v = pd.read_csv(VOI_EXP / "p33_abandonment_bayes.csv")
    h33v = p33v[(p33v["sigma"] == 0.3) & (p33v["cap"] == 0.6) & (p33v["cut"] == "reg") & (p33v["rho_g"] == 0.5)]
    P.show_panel(VOI_FIG / "y04_cutoff_frontier.png")
    P.show_panel(VOI_FIG / "y05_abandonment_frontier.png")
    P.source_ref(
        (VOI_FIG / "y04_cutoff_frontier.png", "voi/voi.ipynb", "C1 cells (y04)",
         "`voi/exports/p31_cutoff_frontier.csv` + `p32_cutoff_pick.csv` (generalizes u51/u52 over the window end; "
         "reproduces them exactly at 2033/2035 — gate G0)"),
        (VOI_FIG / "y05_abandonment_frontier.png", "voi/voi.ipynb", "C2 cells (y05)", "`voi/exports/p33_abandonment_bayes.csv`"),
    )
    P.caption("SF56", f@@Q@@
    The grant cut-off year. Top: coverage (share of cost worlds with no above-ceiling need
    after the window) against the expected grant cost of the window (2024$B) as the window end
    moves through the build years, 60% ceiling (solid, labelled by end year) and 50% ceiling
    (dashed), requirement band ends faint, the 3-point display allowance dotted; dashed
    horizontals = 75% and 90% coverage. Shortest window reaching 90% coverage at the 60%
    ceiling (registered cushion, base band): {_fmt(pk90)}; reaching 75%: {_fmt(pk75)} (none = not
    within the horizon; picks at 2047 or later are horizon-censored; EIA builds from 2038 and is
    not comparable). Bottom: expected loss of the Bayes abandonment rule against the price of
    abandoning a world that would graduate (multiples of the median-world bill), three noise
    levels; dashed = never stop grants. At a price of one half, the rule lowers the risk by
    {h33v["value_B"].min():.1f}-{h33v["value_B"].max():.1f} B$ in the reported schedules. No dollar
    value of information is computed for the horizon choice itself (a perfect-information
    planner would choose which worlds to serve, which is not a realizable policy). Tables: ST19.
    @@Q@@)
    """),
'''
sub_once(B,
         "    expensive-world non-decay is generic, not a base-world artifact.\n    ''')\n    \"\"\"),\n\n    # ---------------------------------------------------------------- ST1-8\n",
         "    expensive-world non-decay is generic, not a base-world artifact.\n    ''')\n    \"\"\"),\n" + SF_BLOCK.replace("@@Q@@", "'''") +
         "\n    # ---------------------------------------------------------------- ST1-8\n")

# ---- ST header + ST19 after ST18 ---------------------------------------------------
sub_once(B, "    ## Supplementary tables (ST1–ST18)\n", "    ## Supplementary tables (ST1–ST19)\n")
ST_BLOCK = r'''
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
    rule (p33); gates, kills and predictions (p90).
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
    P.table(VOI_EXP / "p90_verdict.csv", "ST19k_verdict.csv")
    P.caption("ST19", @@Q@@
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
    (p33); gates, kills and registered predictions (p90). Registration: voi/methods.md (SN11).
    SMR program.
    @@Q@@)
    """),
'''
sub_once(B,
         "    dispositions (v09). Registration: market_transfer/methods.md (SN10). SMR program.\n    ''')\n    \"\"\"),\n\n    # ---------------------------------------------------------------- wrap\n    md(r\"\"\"\n    ## Output manifest\n    \"\"\"),\n",
         "    dispositions (v09). Registration: market_transfer/methods.md (SN10). SMR program.\n    ''')\n    \"\"\"),\n" + ST_BLOCK.replace("@@Q@@", "'''") +
         "\n    # ---------------------------------------------------------------- wrap\n    md(r\"\"\"\n    ## Output manifest\n    \"\"\"),\n")
print("patched paperlib.py and _build_notebooks.py (VOI SI wiring)")
