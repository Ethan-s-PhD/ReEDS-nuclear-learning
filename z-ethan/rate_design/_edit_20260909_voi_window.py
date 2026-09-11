"""2026-09-09 — Fig 6 carries per-schedule demonstration-window ends from the decision-value
analysis (Ethan's ruling): the last grant year that minimizes expected loss (grant dollars +
rho_g x P50 bill per world cut off before it would have graduated) at rho_g = 1, 60% ceiling,
registered cushion, base band (`voi/exports/p34_window_decision.csv`, voi/methods.md v1.1).

Patches (each asserted exactly once):
  rate_design/_build_notebook_v2.py
    - constants: WINDOW_RULE + W_VOI / W_VOI_RANGE read from the voi export (one constant switches the rule)
    - feasibility_tables: a third window "wvoi" (per-schedule end years) beside w2035 / w2033;
      the registered kills KB1/KB2 stay on W_PRIMARY = 2035
    - w38: per-schedule dashed line at the window end + shaded range over rho_g 0.5-2
    - w39: per-schedule dashed lines (schedule colours) instead of the single 2035 line
    - w43: the demonstration funding requirement priced through each schedule's own window (eia included)
  paper_figures/_build_notebooks.py
    - Fig 6 markdown, code filters (w2035 -> wvoi), caption; glossary row; SF56 (+y06) and ST19 (+p34, p35)
Run from z-ethan/rate_design/ with the playground-env python; then rebuild + execute rate_design_v2
(base and RD_ANCHORS=5a) and the two paper_figures notebooks.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
assert HERE.name == "rate_design", HERE
PF = HERE.parent / "paper_figures"


def sub_once(path, old, new):
    s = path.read_text(encoding="utf-8")
    if new in s and old not in s:      # already applied (the script is re-runnable)
        return
    assert s.count(old) == 1, (path.name, old[:90], s.count(old))
    path.write_text(s.replace(old, new), encoding="utf-8")


B = HERE / "_build_notebook_v2.py"

# ---- constants: the per-schedule window end ------------------------------------------
sub_once(B,
         'for _, r in reg_smr.iterrows():\n    ANCH[r["ab"]][r["percentile"]] = int(r["draw_index"])\n',
         'for _, r in reg_smr.iterrows():\n    ANCH[r["ab"]][r["percentile"]] = int(r["draw_index"])\n'
         '\n'
         '# ---- the demonstration-window end from the decision-value analysis (voi/, 2026-09-09) ----\n'
         '# Ethan\'s ruling: Fig 6 carries per-schedule window years = the last grant year that\n'
         '# minimizes expected loss (grant dollars + rho_g x P50 bill per world cut off before it\n'
         '# would have graduated) at rho_g = 1, 60% ceiling, registered cushion, base band\n'
         '# (voi/methods.md v1.1). One constant switches the rule. The registered 2035 window stays\n'
         '# the basis of KB1/KB2 and of the w2035 rows of u51/u52.\n'
         'WINDOW_RULE = ("bayes", 1.0)      # alternative: ("cond_quantile", 0.90)\n'
         '_p34 = pd.read_csv(REPO / "z-ethan" / "voi" / "exports" / "p34_window_decision.csv")\n'
         '_w = _p34[(_p34["rule"] == WINDOW_RULE[0]) & (_p34["param"] == WINDOW_RULE[1]) & (_p34["cap"] == 0.60)\n'
         '          & (_p34["cut"] == "reg") & (_p34["band"] == "base")].set_index("schedule")["T_pick"]\n'
         'W_VOI = {ab: int(_w[ab]) for ab in SCHEDULES}\n'
         '_wb = _p34[(_p34["rule"] == "bayes") & (_p34["param"].isin([0.5, 2.0])) & (_p34["cap"] == 0.60)\n'
         '           & (_p34["cut"] == "reg") & (_p34["band"] == "base")]\n'
         'W_VOI_RANGE = {ab: (int(_wb[(_wb["schedule"] == ab) & (_wb["param"] == 0.5)]["T_pick"].iloc[0]),\n'
         '                    int(_wb[(_wb["schedule"] == ab) & (_wb["param"] == 2.0)]["T_pick"].iloc[0]))\n'
         '               for ab in SCHEDULES}\n'
         'print("per-schedule window end (voi, expected-loss minimizer at rho_g = 1):", W_VOI)\n')

# ---- feasibility_tables: the third window ------------------------------------------------
sub_once(B,
         '                for wname, wend in [("w2035", W_PRIMARY), ("w2033", W_SENS)]:\n'
         '                    post = [j for j, t in enumerate(BUILD_TS[ab]) if t > wend]\n',
         '                for wname, wend_ in [("w2035", W_PRIMARY), ("w2033", W_SENS), ("wvoi", W_VOI)]:\n'
         '                    wend = wend_[ab] if isinstance(wend_, dict) else wend_   # wvoi: per schedule\n'
         '                    post = [j for j, t in enumerate(BUILD_TS[ab]) if t > wend]\n')

# ---- w38: per-schedule window end + rho range ----------------------------------------------
sub_once(B,
         '                solid_capstyle="butt", clip_on=False, zorder=6)\n    ax.set_title(ps.SCHED_SHORT[ab])\n',
         '                solid_capstyle="butt", clip_on=False, zorder=6)\n'
         '    lo_, hi_ = W_VOI_RANGE[ab]\n'
         '    ax.axvspan(min(lo_, hi_) + 0.5, max(lo_, hi_) + 0.5, color="k", alpha=0.06, lw=0)\n'
         '    ax.axvline(W_VOI[ab] + 0.5, color="k", lw=0.8, ls="--")\n'
         '    ax.set_title(ps.SCHED_SHORT[ab])\n')
sub_once(B,
         '    Line2D([], [], color=ps.ACCENT["red"], lw=0.9, ls="-.",\n'
         '           label="hypothetical 60% cap"),\n'
         ']\n'
         'fig.tight_layout()\n'
         'fig.legend(handles=handles, ncol=3, fontsize=6.5, frameon=False,\n'
         '           loc="upper center", bbox_to_anchor=(0.5, 0.0))\n'
         'ps.savefig(fig, FIGURES / "w38_rate_fans_pct.png")\n',
         '    Line2D([], [], color=ps.ACCENT["red"], lw=0.9, ls="-.",\n'
         '           label="hypothetical 60% cap"),\n'
         '    Line2D([], [], color="k", lw=0.8, ls="--",\n'
         '           label="last grant year: expected-loss minimizer, per schedule"),\n'
         '    Patch(facecolor="k", alpha=0.06,\n'
         '          label="its range as the price of a cut-off world runs 0.5–2× the median-world bill"),\n'
         ']\n'
         'fig.tight_layout()\n'
         'fig.legend(handles=handles, ncol=4, fontsize=6.5, frameon=False,\n'
         '           loc="upper center", bbox_to_anchor=(0.5, 0.0))\n'
         'ps.savefig(fig, FIGURES / "w38_rate_fans_pct.png")\n')

# ---- w39: per-schedule lines ----------------------------------------------------------------
sub_once(B,
         'ax.axvline(W_PRIMARY + 0.5, color="k", lw=0.8, ls="--")\nax.set_xlabel("build year")\n'
         'ax.set_ylabel("share of worlds above the cap (%)")\n',
         'for ab in SCHEDULES:\n'
         '    ax.axvline(W_VOI[ab] + 0.5, color=ps.SCHED_C[ab], lw=0.8, ls="--", alpha=0.9)\n'
         'ax.set_xlabel("build year")\n'
         'ax.set_ylabel("share of worlds above the cap (%)")\n')
sub_once(B,
         '           label="end of demonstration window (2035)")],\n'
         '    fontsize=6, frameon=False, loc="lower left")\n'
         'fig.tight_layout()\nps.savefig(fig, FIGURES / "w39_mask_paper.png")\n',
         '           label="last grant year, per schedule (colour = schedule)")],\n'
         '    fontsize=6, frameon=False, loc="lower left")\n'
         'fig.tight_layout()\nps.savefig(fig, FIGURES / "w39_mask_paper.png")\n')

# ---- w43: each schedule priced through its own window; eia included ------------------------
sub_once(B,
         'GAP_SCHED = [ab for ab in SCHEDULES if ab != "eia"]\nxpos = np.arange(len(GAP_SCHED))\n'
         'for k_, (cap, off, al) in enumerate([(0.50, -0.17, 0.55), (0.60, 0.17, 1.0)]):\n'
         '    sub = u52c[(u52c["band"] == "base") & (u52c["window"] == "w2035")\n',
         'GAP_SCHED = list(SCHEDULES)     # every schedule has its own window end (wvoi), eia included\n'
         'xpos = np.arange(len(GAP_SCHED))\n'
         'for k_, (cap, off, al) in enumerate([(0.50, -0.17, 0.55), (0.60, 0.17, 1.0)]):\n'
         '    sub = u52c[(u52c["band"] == "base") & (u52c["window"] == "wvoi")\n')
sub_once(B,
         'ax.text(0.02, 0.55, "EIA AEO high: no builds\\\\nbefore 2036", transform=ax.transAxes,\n'
         '        fontsize=6, color=ps.MUTED, va="top")\n'
         'fig.tight_layout()\nps.savefig(fig, FIGURES / "w43_gap_paper.png")\n',
         'ax.text(0.02, 0.55, "priced through each schedule\'s\\\\nown last grant year: "\n'
         '        + ", ".join(f"{ps.SCHED_SHORT[ab]} {W_VOI[ab]}" for ab in GAP_SCHED[:3]) + ",\\\\n"\n'
         '        + ", ".join(f"{ps.SCHED_SHORT[ab]} {W_VOI[ab]}" for ab in GAP_SCHED[3:]),\n'
         '        transform=ax.transAxes, fontsize=5.5, color=ps.MUTED, va="top")\n'
         'fig.tight_layout()\nps.savefig(fig, FIGURES / "w43_gap_paper.png")\n')

sub_once(B,
         'ax.set_xticks(xpos, [ps.SCHED_SHORT[ab] for ab in GAP_SCHED])\n',
         'ax.set_xticks(xpos, [ps.SCHED_SHORT[ab].replace(" ", "\\\\n", 1) for ab in GAP_SCHED], fontsize=7)\n')

# =============================================================================================
PB = PF / "_build_notebooks.py"

# ---- glossary ------------------------------------------------------------------------------
sub_once(PB,
         "| **Demonstration window** | The build years through 2035, in which grant-type federal cost share to first units (the ARDP model) is the assumed vehicle for support above the statutory rate cap; after the window the instrument is the capped credit alone. |",
         "| **Demonstration window** | The build years through each schedule's window end, in which grant-type federal cost share to first units (the ARDP model) is the assumed vehicle for support above the statutory rate cap; after the window the instrument is the capped credit alone. Since 2026-09-09 the window end is an output: the last grant year that minimizes expected loss (grant dollars plus one median-world bill per world cut off before it would have graduated; `voi/`, SF56), 2031–2044 by schedule. The registered rate_design kills and the market-world transfer stay on the earlier fixed 2035 window. |")

# ---- Fig 6 markdown ------------------------------------------------------------------------
sub_once(PB,
         "    mask** — the share of worlds above the cap by build year (solid 60%,\n"
         "    dotted 50%; the vertical dashed line is the demonstration-window edge,\n"
         "    2035). Panel (c): the **demonstration funding requirement** in 2024\\$B —\n"
         "    the fixed-basis PV of above-cap need inside the window (median solid,\n"
         "    p95 faint; eia not applicable — its first build year is 2038, so the\n"
         "    window contains no eia year).\n",
         "    mask** — the share of worlds above the cap by build year (solid 60%,\n"
         "    dotted 50%; the vertical dashed lines are the per-schedule\n"
         "    demonstration-window ends). Panel (c): the **demonstration funding\n"
         "    requirement** in 2024\\$B — the fixed-basis PV of above-cap need inside\n"
         "    each schedule's own window (median solid, p95 faint).\n"
         "\n"
         "    **The window end is an output (2026-09-09, Ethan's ruling; `z-ethan/voi/`\n"
         "    v1.1, SF56, ST19).** The coverage-versus-grant-dollars frontier bends\n"
         "    because graduation years are bimodal: worlds that ever become\n"
         "    credit-feasible do so early, the rest never do within the horizon, and\n"
         "    after the bend the marginal grant dollar goes almost entirely to worlds\n"
         "    that will never graduate. The window end shown is the last grant year that\n"
         "    minimizes expected loss — grant dollars paid through that year plus one\n"
         "    median-world bill for every world cut off before it would have graduated —\n"
         "    at the 60% ceiling, registered cushion, base band. The shaded span in (a)\n"
         "    is its range as that price runs from one half to two median-world bills;\n"
         "    the price-free companion (the window covering 90% of the worlds that ever\n"
         "    graduate) and the marginal-cost ladder are in SF56/ST19. The registered\n"
         "    rate_design kills KB1/KB2, ST14 and the market-world transfer (Fig 7,\n"
         "    SF40, ST18) stay on the earlier fixed 2035 window.\n")
sub_once(PB,
         "    that cap in that year. Before 2035 the demonstration window absorbs the\n"
         "    excess as grant cost share; after it, above-cap need means the capped\n",
         "    that cap in that year. Before a schedule's window end the demonstration\n"
         "    window absorbs the excess as grant cost share; after it, above-cap need means the capped\n")

# ---- Fig 6 code --------------------------------------------------------------------------
sub_once(PB,
         '    pw = u51c[(u51c["kind"] == "per_world") & (u51c["window"] == "w2035")]\n',
         '    p34 = pd.read_csv(VOI_EXP / "p34_window_decision.csv")\n'
         '    _wv = p34[(p34["rule"] == "bayes") & (p34["param"] == 1.0) & (p34["cap"] == 0.6) & (p34["cut"] == "reg")\n'
         '              & (p34["band"] == "base")].set_index("schedule")\n'
         '    WY = {ab: int(_wv.loc[ab, "T_pick"]) for ab in P.SCHEDULES}\n'
         '    wtxt = ", ".join(f"{P.SCHED_NAME[ab].split(\' (\')[0]} {WY[ab]}" for ab in P.SCHEDULES)\n'
         '    print("per-schedule window ends (expected-loss minimizer, rho_g = 1):", WY)\n'
         '    pw = u51c[(u51c["kind"] == "per_world") & (u51c["window"] == "wvoi")]\n')
sub_once(PB,
         '    print(f"post-window infeasible share (display twin; quoted ONLY as cap x band ranges): "\n',
         '    print(f"post-window infeasible share (display twin, per-schedule windows; quoted ONLY as cap x band ranges): "\n')
sub_once(PB,
         '             & (u52c["window"] == "w2035") & (u52c["window_applicable"] == True)]  # noqa: E712\n',
         '             & (u52c["window"] == "wvoi") & (u52c["window_applicable"] == True)]  # noqa: E712\n')
sub_once(PB,
         '    print(f"demonstration gap medians (display twin, base band, 60% cap, window <= 2035): "\n',
         '    print(f"demonstration gap medians (display twin, base band, 60% cap, per-schedule windows): "\n')
sub_once(PB,
         "    vertical dashed line = the demonstration-window edge, 2035 — inside the window,\n"
         "    grant-type federal cost share to first units is the assumed vehicle for above-cap need).\n",
         "    vertical dashed lines = the per-schedule demonstration-window ends: {wtxt} — the last\n"
         "    grant year that minimizes expected grant dollars plus one median-world bill per world cut\n"
         "    off before it would have graduated (SF56; the shaded span in (a) is its range as that price\n"
         "    runs 0.5-2x) — inside the window, grant-type federal cost share to first units is the\n"
         "    assumed vehicle for above-cap need).\n")
sub_once(PB,
         "    above-cap need inside the window (median solid, 95th percentile faint; eia not\n"
         "    applicable: its first build year is 2038). Where the framing stands, the medians at the\n",
         "    above-cap need inside each schedule's own window (median solid, 95th percentile faint).\n"
         "    Where the framing stands, the medians at the\n")

# ---- SF56: y06 panel + the window years in the caption -----------------------------------
sub_once(PB,
         '    P.show_panel(VOI_FIG / "y05_abandonment_frontier.png")\n'
         '    P.source_ref(\n'
         '        (VOI_FIG / "y04_cutoff_frontier.png", "voi/voi.ipynb", "C1 cells (y04)",\n',
         '    P.show_panel(VOI_FIG / "y05_abandonment_frontier.png")\n'
         '    P.show_panel(VOI_FIG / "y06_window_decision.png")\n'
         '    p34v = pd.read_csv(VOI_EXP / "p34_window_decision.csv")\n'
         '    hb = p34v[(p34v["rule"] == "bayes") & (p34v["param"] == 1.0) & (p34v["cap"] == 0.6) & (p34v["cut"] == "reg")\n'
         '              & (p34v["band"] == "base")].set_index("schedule")\n'
         '    hq9 = p34v[(p34v["rule"] == "cond_quantile") & (p34v["param"] == 0.9) & (p34v["cap"] == 0.6) & (p34v["cut"] == "reg")\n'
         '               & (p34v["band"] == "base")].set_index("schedule")\n'
         '    wb = ", ".join(f"{ab} {int(hb.loc[ab, \'T_pick\'])} ({hb.loc[ab, \'T_range_over_rho\']})" for ab in P.SCHEDULES)\n'
         '    wq = ", ".join(f"{ab} {int(hq9.loc[ab, \'T_pick\'])}" for ab in P.SCHEDULES)\n'
         '    P.source_ref(\n'
         '        (VOI_FIG / "y06_window_decision.png", "voi/voi.ipynb", "C1b cells (y06)",\n'
         '         "`voi/exports/p34_window_decision.csv` (Bayes window, conditional-quantile window) + "\n'
         '         "`p35_marginal_cost_ladder.csv`"),\n'
         '        (VOI_FIG / "y04_cutoff_frontier.png", "voi/voi.ipynb", "C1 cells (y04)",\n')
sub_once(PB,
         "    {h33v[\"value_B\"].min():.1f}-{h33v[\"value_B\"].max():.1f} B$ in the reported schedules. No dollar\n"
         "    value of information is computed for the horizon choice itself (a perfect-information\n"
         "    planner would choose which worlds to serve, which is not a realizable policy). Tables: ST19.\n",
         "    {h33v[\"value_B\"].min():.1f}-{h33v[\"value_B\"].max():.1f} B$ in the reported schedules. Third figure:\n"
         "    the window end as a decision — the expected loss of ending grants in each build year (grant\n"
         "    dollars plus a price per world cut off before it would have graduated) and the optimal year\n"
         "    against that price; the paper's Fig 6 carries the optimum at one median-world bill:\n"
         "    {wb} (range as the price runs 0.1-2x), beside the price-free window that covers 90% of the\n"
         "    worlds that ever graduate: {wq}. No dollar value of information is computed for the horizon\n"
         "    choice itself (a perfect-information planner would choose which worlds to serve, which is\n"
         "    not a realizable policy). Tables: ST19.\n")

# ---- ST19: p34, p35 -------------------------------------------------------------------------
sub_once(PB,
         '    P.table(VOI_EXP / "p33_abandonment_bayes.csv", "ST19j_abandonment_bayes.csv", round_=4)\n'
         '    P.table(VOI_EXP / "p90_verdict.csv", "ST19k_verdict.csv")\n',
         '    P.table(VOI_EXP / "p33_abandonment_bayes.csv", "ST19j_abandonment_bayes.csv", round_=4)\n'
         '    P.table(VOI_EXP / "p34_window_decision.csv", "ST19l_window_decision.csv", round_=4)\n'
         '    P.table(VOI_EXP / "p35_marginal_cost_ladder.csv", "ST19m_marginal_cost_ladder.csv", round_=4)\n'
         '    P.table(VOI_EXP / "p90_verdict.csv", "ST19n_verdict.csv")\n')
sub_once(PB,
         "    (p33); gates, kills and registered predictions (p90). Registration: voi/methods.md (SN11).\n",
         "    (p33); the window end as a decision — the expected-loss minimizer per price, the\n"
         "    conditional-quantile window and their band/display-twin flags (p34) and the marginal-cost\n"
         "    ladder with the reference knee (p35); gates, kills and registered predictions (p90).\n"
         "    Registration: voi/methods.md (SN11; v1.1 addendum for p34/p35).\n")
sub_once(PB,
         "    rule (p33); gates, kills and predictions (p90).\n    \"\"\"),\n",
         "    rule (p33); the window decision (p34) and the marginal-cost ladder (p35); gates,\n"
         "    kills and predictions (p90).\n    \"\"\"),\n")
print("patched rate_design/_build_notebook_v2.py and paper_figures/_build_notebooks.py")
