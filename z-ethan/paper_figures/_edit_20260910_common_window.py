"""Fig 6 on one common demonstration-window end (2038) + main-text Table 2 (Ethan, 2026-09-10).

Patches _build_notebooks.py in place (re-runnable). Then rebuild + execute both notebooks.
"""
from pathlib import Path

p = Path(__file__).with_name("_build_notebooks.py")
s = p.read_text(encoding="utf-8")
n0 = len(s)
log = []


def sub(old, new, name):
    global s
    if old in s:
        assert s.count(old) == 1, (name, s.count(old))
        s = s.replace(old, new)
        log.append(f"applied  {name}")
    elif new in s:
        log.append(f"already  {name}")
    else:
        raise AssertionError(f"anchor missing for {name}: {old[:80]!r}")


# ---- glossary row --------------------------------------------------------------------
sub("| **Demonstration window** | The build years through each schedule's window end, in which grant-type "
    "federal cost share to first units (the ARDP model) is the assumed vehicle for support above the statutory "
    "rate cap; after the window the instrument is the capped credit alone. Since 2026-09-09 the window end is an "
    "output: the last grant year that minimizes expected loss (grant dollars plus one median-world bill per world "
    "cut off before it would have graduated; `voi/`, SF56), 2031–2044 by schedule. The registered rate_design "
    "kills and the market-world transfer stay on the earlier fixed 2035 window. |",
    "| **Demonstration window** | The build years through 2038, one common window end for every schedule, in "
    "which grant-type federal cost share to first units (the ARDP model) is the assumed vehicle for support above "
    "the statutory rate cap; after the window the instrument is the capped credit alone. 2038 is the year by which "
    "every world that ever becomes credit-feasible has done so, in every schedule at both ceilings (EIA, whose "
    "builds start in 2038, by 2044; Table 2; `voi/` p36). The per-schedule expected-loss minimizers of the "
    "decision-value analysis stay in SF56/ST19. The registered rate_design kills and the market-world transfer "
    "stay on the earlier fixed 2035 window. |",
    "glossary row")

# ---- display-item count ----------------------------------------------------------------
sub("    seven figures and Table 1 — all eight display items. (The Table 2 slot was freed\n"
    "    2026-08-19 when the Monte Carlo variables table moved to the SI as ST10; the last\n"
    "    open slot was consumed 2026-08-26 by Figure 5, the cost-of-detection figure.)\n",
    "    seven figures and two tables — nine display items since 2026-09-10, when Ethan\n"
    "    added Table 2 (what the capped credit alone reaches, by schedule; the outline's\n"
    "    eight-item display budget needs his ruling). (The Table 2 slot had been freed\n"
    "    2026-08-19 when the Monte Carlo variables table moved to the SI as ST10 and was\n"
    "    consumed 2026-08-26 by Figure 5, the cost-of-detection figure.)\n",
    "display count")

# ---- Fig 6 markdown ----------------------------------------------------------------------
sub("    and a red edge marks the span. Panel (b): the **credit-feasibility\n"
    "    mask** — the share of worlds above the cap by build year (solid 60%,\n"
    "    dotted 50%; the vertical dashed lines are the per-schedule\n"
    "    demonstration-window ends). Panel (c): the **demonstration funding\n"
    "    requirement** in 2024\\$B — the fixed-basis PV of above-cap need inside\n"
    "    each schedule's own window (median solid, p95 faint).\n",
    "    and a red edge marks the span. Panel (b): the **credit-feasibility\n"
    "    mask**, drawn as the share of samples covered by the credit — the share\n"
    "    of worlds whose required rate sits at or below the 50% statutory maximum\n"
    "    in each build year (the existing incentive structure; the 60% case is in\n"
    "    ST14 and Table 2). The dashed line is the common demonstration-window\n"
    "    end, 2038; the right-edge label on each curve is the share covered in\n"
    "    the last build year, which equals the share of worlds that ever become\n"
    "    credit-feasible. Panel (c): the **demonstration funding requirement** in\n"
    "    2024\\$B — the fixed-basis PV of above-cap need inside the common window\n"
    "    (median solid, p95 faint).\n",
    "Fig 6 md panels")

OLD_PARA_START = "    **The window end is an output (2026-09-09, Ethan's ruling; `z-ethan/voi/`\n"
OLD_PARA_END = "    SF40, ST18) stay on the earlier fixed 2035 window.\n"
NEW_PARA = (
    "    **One common window end, 2038 (Ethan, 2026-09-10).** The decision-value\n"
    "    analysis (`z-ethan/voi/`, SF56, ST19) showed that graduation years are\n"
    "    bimodal: worlds that ever become credit-feasible do so early, the rest\n"
    "    never do within the horizon. Every world that ever graduates has done so\n"
    "    by 2038 in every schedule at both ceilings, except EIA, whose builds start\n"
    "    in 2038 and finish graduating in 2044 (Table 2; voi p36). So the paper\n"
    "    carries one window end for every schedule — build years through 2038 —\n"
    "    and after it any grant dollar goes to a world that will never become\n"
    "    credit-feasible. The per-schedule expected-loss minimizers and their\n"
    "    price sensitivity stay in SF56/ST19; the anchor sensitivity of the IAEA\n"
    "    pick is logged in voi/status.md (2026-09-10). The registered rate_design\n"
    "    kills KB1/KB2, ST14 and the market-world transfer (Fig 7, SF40, ST18)\n"
    "    stay on the earlier fixed 2035 window.\n")
if OLD_PARA_START in s:
    i0 = s.index(OLD_PARA_START)
    i1 = s.index(OLD_PARA_END, i0) + len(OLD_PARA_END)
    s = s[:i0] + NEW_PARA + s[i1:]
    log.append("applied  Fig 6 window paragraph")
else:
    assert "**One common window end, 2038" in s
    log.append("already  Fig 6 window paragraph")

sub("    that cap in that year. Before a schedule's window end the demonstration\n"
    "    window absorbs the excess as grant cost share; after it, above-cap need means the capped\n"
    "    credit alone fails that world. In panel (b), the post-window share above\n"
    "    the cap is the not-credit-feasible share — the mask's key output. Panel\n"
    "    (c) prices the window.\n",
    "    that cap in that year. Through 2038 the demonstration window absorbs the\n"
    "    excess as grant cost share; after it, above-cap need means the capped\n"
    "    credit alone fails that world. In panel (b), the height of each curve's\n"
    "    flat tail is the share of worlds the credit alone ever reaches; one minus\n"
    "    it is the not-credit-feasible share — the mask's key output. Panel (c)\n"
    "    prices the window.\n",
    "Fig 6 how-to-read")

# ---- Fig 6 code ---------------------------------------------------------------------------
sub('    u51c = pd.read_csv(RD_EXP / "u51_feasibility_mask_cut_5a.csv")\n'
    '    p34 = pd.read_csv(VOI_EXP / "p34_window_decision.csv")\n'
    '    _wv = p34[(p34["rule"] == "bayes") & (p34["param"] == 1.0) & (p34["cap"] == 0.6) & (p34["cut"] == "reg")\n'
    '              & (p34["band"] == "base")].set_index("schedule")\n'
    '    WY = {ab: int(_wv.loc[ab, "T_pick"]) for ab in P.SCHEDULES}\n'
    '    wtxt = ", ".join(f"{P.SCHED_NAME[ab].split(\' (\')[0]} {WY[ab]}" for ab in P.SCHEDULES)\n'
    '    print("per-schedule window ends (expected-loss minimizer, rho_g = 1):", WY)\n'
    '    pw = u51c[(u51c["kind"] == "per_world") & (u51c["window"] == "wvoi")]\n',
    '    u51c = pd.read_csv(RD_EXP / "u51_feasibility_mask_cut_5a.csv")\n'
    '    W_COMMON = 2038\n'
    '    assert (u51c["window"].dropna() == "w2038").any(), "u51 twin lacks the w2038 rows: rebuild rate_design_v2_5a"\n'
    '    p36 = pd.read_csv(VOI_EXP / "p36_common_window_table.csv")\n'
    '    assert (p36["common_year"] == W_COMMON).all()\n'
    '    _c50 = u51c[(u51c["kind"] == "per_year") & (u51c["band"] == "base") & (u51c["cap"] == 0.5)]\n'
    '    end50 = {ab: 1 - float(_c50[_c50["schedule"] == ab].sort_values("year")["share_above"].iloc[-1]) for ab in P.SCHEDULES}\n'
    '    _p36d = p36[(p36["cut"] == "disp") & (p36["band"] == "base") & (p36["cap"] == 0.5)].set_index("schedule")\n'
    '    assert all(abs(end50[ab] - (1 - float(_p36d.loc[ab, "share_never"]))) < 1e-3 for ab in P.SCHEDULES)\n'
    '    print("share covered by the credit in the last build year (50% cap, display twin) = 1 - never share:",\n'
    '          {k: round(v, 2) for k, v in end50.items()})\n'
    '    _late = _p36d["share_graduating_after_common"]\n'
    '    print(f"worlds graduating after {W_COMMON} (50% cap, display twin): max {_late.max():.3f} ({_late.idxmax()})")\n'
    '    pw = u51c[(u51c["kind"] == "per_world") & (u51c["window"] == "w2038")]\n',
    "Fig 6 code window")
sub('    print(f"post-window infeasible share (display twin, per-schedule windows; quoted ONLY as cap x band ranges): "\n',
    '    print(f"post-window infeasible share (display twin, common {W_COMMON} window; quoted ONLY as cap x band ranges): "\n',
    "Fig 6 print 1")
sub('             & (u52c["window"] == "wvoi") & (u52c["window_applicable"] == True)]  # noqa: E712\n',
    '             & (u52c["window"] == "w2038") & (u52c["window_applicable"] == True)]  # noqa: E712\n',
    "Fig 6 u52 filter")
sub('    print(f"demonstration gap medians (display twin, base band, 60% cap, per-schedule windows): "\n',
    '    print(f"demonstration gap medians (display twin, base band, 60% cap, common {W_COMMON} window): "\n',
    "Fig 6 print 2")

# ---- Fig 6 caption ------------------------------------------------------------------------
sub("    quantile). (b) Share of worlds above the cap by build year (solid 60%, dotted 50%;\n"
    "    vertical dashed lines = the per-schedule demonstration-window ends: {wtxt} — the last\n"
    "    grant year that minimizes expected grant dollars plus one median-world bill per world cut\n"
    "    off before it would have graduated (SF56; the shaded span in (a) is its range as that price\n"
    "    runs 0.5-2x) — inside the window, grant-type federal cost share to first units is the\n"
    "    assumed vehicle for above-cap need).\n"
    "    Post-window, the share above the cap is the not-credit-feasible share:\n"
    "    {r60.min():.2f}-{r60.max():.2f} at the 60% cap and {r50.min():.2f}-{r50.max():.2f} at\n"
    "    the 50% cap, across schedules and the +-{_e5*100:.0f}% certificate band — quoted only\n"
    "    as ranges.",
    "    quantile). (b) Share of samples covered by the credit — worlds whose required rate is at\n"
    "    or below the 50% statutory maximum in that build year (the existing incentive structure).\n"
    "    The dashed line is the demonstration-window end, {W_COMMON}, common to every schedule:\n"
    "    through {W_COMMON}, grant-type federal cost share to first units is the assumed vehicle for\n"
    "    above-cap need, and every world that ever becomes credit-feasible has done so by\n"
    "    {W_COMMON} in every schedule (EIA, whose builds start in {W_COMMON}, by 2044; Table 2, SF56).\n"
    "    The right-edge labels are the share covered in the last build year, the share of worlds\n"
    "    the credit alone ever reaches ({min(end50.values()):.0%}-{max(end50.values()):.0%}).\n"
    "    Post-window, the uncovered share is the not-credit-feasible share:\n"
    "    {r50.min():.2f}-{r50.max():.2f} at the 50% cap and {r60.min():.2f}-{r60.max():.2f} at\n"
    "    the 60% cap, across schedules and the +-{_e5*100:.0f}% certificate band — quoted only\n"
    "    as ranges.",
    "Fig 6 caption b")
sub("    range). (c) The demonstration funding requirement — the fixed-basis present value of\n"
    "    above-cap need inside each schedule's own window (median solid, 95th percentile faint).\n",
    "    range). (c) The demonstration funding requirement — the fixed-basis present value of\n"
    "    above-cap need inside the common window, build years through {W_COMMON} (median solid,\n"
    "    95th percentile faint; left bar 50% cap, right bar 60%).\n",
    "Fig 6 caption c")

# ---- Table 2 ------------------------------------------------------------------------------
T2_START = "    # ------------------------------------------------- Table 2: freed reserve\n"
T2_END = "    exhibit must displace one.\n    \"\"\"),\n]\n"
NEW_T2 = '''    # ------------------------------------------------- Table 2: credit feasibility
    md(r"""
    ## Table 2 — What the capped credit alone reaches, by schedule

    **What this table shows.** One row per deployment schedule, at the 50%
    statutory maximum (today's stackable ceiling) and at the 60% registered
    outer bound. For each ceiling: the share of cost worlds that never get
    under the ceiling within the horizon (the credit alone never reaches
    them), the share under the ceiling by 2038 (the common demonstration-window
    end), and the year by which every world that ever gets under the ceiling
    has done so. Values are the 3-point display twin (as Fig 6); the
    registered one-point cushion and the ±E5 band ends are in ST19o.

    **Why 2038.** Graduation years are bimodal: worlds that ever become
    credit-feasible do so early, the rest never do. The last column shows
    that every such world has graduated by 2038 in every schedule except
    EIA, whose builds start in 2038 and finish graduating in 2044. The
    demonstration window therefore ends in 2038 for every schedule in Fig 6;
    the per-schedule expected-loss minimizers stay in SF56/ST19.

    **Display budget.** Added 2026-09-10 at Ethan's request as the ninth
    main-text display item; the outline's eight-item budget needs his ruling
    (this slot was freed 2026-08-19 and consumed by Figure 5 on 2026-08-26).
    """),
    code(r"""
    p36 = pd.read_csv(VOI_EXP / "p36_common_window_table.csv")
    W_COMMON = int(p36["common_year"].iloc[0])
    assert W_COMMON == 2038 and (p36["common_year"] == W_COMMON).all()
    d = p36[(p36["cut"] == "disp") & (p36["band"] == "base")]
    rows = []
    for ab in P.SCHEDULES:
        r = {"schedule": ab, "source": P.SCHED_NAME[ab].split(" (")[0]}
        for cap in (0.5, 0.6):
            x = d[(d["schedule"] == ab) & (d["cap"] == cap)].iloc[0]
            tag = f"{int(round(cap * 100))}pct"
            r[f"never_credit_feasible_{tag}"] = round(float(x["share_never"]), 2)
            r[f"credit_feasible_by_{W_COMMON}_{tag}"] = round(float(x["share_under_by_common"]), 2)
            r[f"all_feasible_worlds_by_{tag}"] = int(x["complete_year"])
        rows.append(r)
    table2 = pd.DataFrame(rows)
    late = d.groupby("cap")["share_graduating_after_common"].max()
    print(f"largest share of worlds graduating after {W_COMMON} (display twin, base band): "
          + ", ".join(f"{int(round(c * 100))}% cap {v:.3f}" for c, v in late.items()))
    table2.to_csv(P.OUT_EXP / "Table2_credit_feasibility.csv", index=False)
    print(f"exports/Table2_credit_feasibility.csv ({len(table2)} rows)")

    P.caption("Table 2", f\'\'\'
    What the capped credit alone reaches. For each deployment schedule and statutory ceiling
    (50% = today's stackable maximum; 60% = the registered outer bound): the share of the 10,000
    cost worlds that never get under the ceiling within the horizon, the share under it by
    {W_COMMON} (the common demonstration-window end in Fig 6), and the year by which every world
    that ever gets under the ceiling has done so. Values are shown 3 points of basis below the
    mapped requirement, as in Fig 6 (registered one-point values and the certificate-band ends:
    ST19o). Graduation is complete by {W_COMMON} in every schedule except EIA, whose builds start
    in {W_COMMON}. Sources: voi p36_common_window_table (rate_design five-anchor map).
    \'\'\')
    table2
    """),
]
'''
if T2_START in s:
    i0 = s.index(T2_START)
    i1 = s.index(T2_END, i0) + len(T2_END)
    s = s[:i0] + NEW_T2 + s[i1:]
    log.append("applied  Table 2 block")
else:
    assert "Table 2 — What the capped credit alone reaches" in s
    log.append("already  Table 2 block")

# ---- ST19: the p36 copy -------------------------------------------------------------------
sub('    P.table(VOI_EXP / "p35_marginal_cost_ladder.csv", "ST19m_marginal_cost_ladder.csv", round_=4)\n',
    '    P.table(VOI_EXP / "p35_marginal_cost_ladder.csv", "ST19m_marginal_cost_ladder.csv", round_=4)\n'
    '    P.table(VOI_EXP / "p36_common_window_table.csv", "ST19o_common_window_table.csv", round_=4)\n',
    "ST19o table")
sub("    rule (p33); the window decision (p34) and the marginal-cost ladder (p35); gates,\n",
    "    rule (p33); the window decision (p34), the marginal-cost ladder (p35) and the\n"
    "    common-window table behind main-text Table 2 (p36, ST19o); gates,\n",
    "ST19 md")

assert '"wvoi"' not in s and "wtxt" not in s, "stale per-schedule window code remains"
p.write_text(s, encoding="utf-8")
print("\n".join(log))
print(f"patched _build_notebooks.py ({n0} -> {len(s)} chars)")
# leftovers worth a look
for i, line in enumerate(s.splitlines(), 1):
    if ("per-schedule window" in line or "Fig 6 carries" in line or "2031–2044" in line) and "SF56" not in line:
        print(f"  check line {i}: {line.strip()[:110]}")
