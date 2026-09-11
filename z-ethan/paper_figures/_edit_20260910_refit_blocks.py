"""Draft v3 main figures on the batch-6 refit (2026-09-10).

The coauthor cut (Wesley Cole, 09-05/09-10) leaves five main figures and two tables:
Fig 1 literature comparison, Fig 2 schedules + financed-capex fans, **Fig 3 the cost gap**
(the $/kW requirement fans on the batch-6 refit map: 5/25/50/75/95 percentiles across the
10,000 cost worlds by build year), **Fig 4 the statutory wall** (the old figure 6, repointed
to the refit map: `rate_design2` n38/n39/n43, m20–m23), Fig 5 the market worlds (the old
figure 7), Table 1, Table 2 (repointed to `rate_design2` m23).

Moves: the technology-choice figure (old figure 3) → SF57; the cost-of-detection figure
(old figure 5) → SF58; the three-anchor solved cost gap (old figure 4, `f04b`) → SF59. SF38
is retitled as the pre-refit dollar fans.

Edit method per the established convention (`_edit_20260909_fig_revisions.py`):
marker-based block surgery on `_build_notebooks.py`, then rebuild + execute both
notebooks with the JUPYTER_PATH recipe. Idempotent. Needs `rate_design2/exports/m12,
m13, m20–m23, m31` and `rate_design2/figures/n31_dollar_fans_cut, n38, n39, n43` at
execution time (not at build time).

Order of operations (the renumbering is a one-pass regex over "Fig N" / "Figure N" tokens
with the map 3→SF57, 4→3, 5→SF58, 6→4, 7→5): (1) cut the four moving blocks; (2) rewrite
the relocated blocks' own headings/tags, then renumber their internal cross-references;
(3) renumber the old figure-6 block first, then repoint it as the new Fig 4; (4) apply the
old-token edits to the surviving text (Table 2, glossary, preamble), then renumber it;
(5) stitch in the new Fig 3 block (never renumbered) and the new Fig 4 block; (6) append
SF57–SF59. History notes written here say "figure N" in lowercase so the regex leaves them.
"""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
BP = HERE / "_build_notebooks.py"
text = BP.read_text(encoding="utf-8")
if "n31_dollar_fans_cut.png" in text:
    print("already applied")
    raise SystemExit(0)

MARK = "    # ---------------------------------------------------------------- "
NEWNUM = {"1": "1", "2": "2", "3": "SF57", "4": "3", "5": "SF58", "6": "4", "7": "5"}


def cut_between(start, end):
    """Return the text from `start` (inclusive) up to `end` (exclusive) and remove it."""
    global text
    assert text.count(start) == 1, start
    assert text.count(end) == 1, end
    i = text.index(start)
    j = text.index(end, i + len(start))
    block = text[i:j]
    text = text[:i] + text[j:]
    return block


def sub1(old, new, where=None):
    """Replace exactly one occurrence (in `where` if given, else in the builder text)."""
    global text
    src = text if where is None else where
    assert src.count(old) == 1, old[:80]
    out = src.replace(old, new)
    if where is None:
        text = out
    return out


def ren(s):
    """One-pass renumbering of every 'Fig N[a-d]' / 'Figure N' cross-reference."""
    for a, b in [("Fig 6b/6c", "Fig 6b/Fig 6c"), ("Fig 7a/7b", "Fig 7a/Fig 7b"),
                 ("Fig 3c/d", "Fig 3c/Fig 3d"), ("Fig 6a/6b", "Fig 6a/Fig 6b")]:
        s = s.replace(a, b)

    def _r(m):
        word, n, suf = m.group(1), m.group(2), m.group(3) or ""
        new = NEWNUM[n]
        return f"{new}{suf}" if new.startswith("SF") else f"{word} {new}{suf}"

    return re.sub(r"\b(Fig|Figure)\s([1-7])([a-d])?\b", _r, s)


# ----------------------------------------------------------------------------- 1. cut the moving blocks
old_fig3 = cut_between(MARK + "Fig 3\n", MARK + "Fig 4\n")      # technology choice -> SF57
old_fig4 = cut_between(MARK + "Fig 4\n", MARK + "Fig 5\n")      # three-anchor cost gap -> SF59 (replaced by the new Fig 3)
old_fig5 = cut_between(MARK + "Fig 5\n", MARK + "Fig 6\n")      # cost of detection -> SF58
old_fig6 = cut_between(MARK + "Fig 6\n", MARK + "Fig 7\n")      # statutory wall -> the new Fig 4 (repointed)

# ----------------------------------------------------------------------------- 2. SF57 / SF58 / SF59 from the old blocks
sf57 = old_fig3
sf57 = sub1(MARK + "Fig 3\n", MARK + "SF57 (main-text figure 3 until 2026-09-10)\n", sf57)
sf57 = sub1("    ## Figure 3 — Why all priced cases commit to a 100%-SMR program, now\n",
            "    ## SF57 — Why all priced cases commit to a 100%-SMR program, now (main-text figure 3 until 2026-09-10)\n\n"
            "    Moved to the SI on 2026-09-10 (the coauthor cut for draft v3: five main figures).\n"
            "    The main text keeps one sentence on the technology choice; this page keeps the full case.\n", sf57)
sf57 = sub1('"Fig3_technology_choice.png"', '"SF57_technology_choice.png"', sf57)
sf57 = sub1('P.caption("Fig 3", ', 'P.caption("SF57", ', sf57)

sf58 = old_fig5
sf58 = sub1(MARK + "Fig 5\n", MARK + "SF58 (main-text figure 5 until 2026-09-10)\n", sf58)
sf58 = sub1("    ## Figure 5 — What observation buys, and what it cannot\n",
            "    ## SF58 — What observation buys, and what it cannot (main-text figure 5 until 2026-09-10)\n\n"
            "    Moved to the SI on 2026-09-10 (the coauthor cut for draft v3). Panel (b) stays on the\n"
            "    five-anchor requirement map and the bill band E5 (pre-refit; the bridge notebooks are\n"
            "    not re-run under methods.md v2.4).\n", sf58)
sf58 = sub1('"Fig5_cost_of_detection.png"', '"SF58_cost_of_detection.png"', sf58)
sf58 = sub1('P.caption("Fig 5", ', 'P.caption("SF58", ', sf58)

sf59 = old_fig4
sf59 = sub1(MARK + "Fig 4\n", MARK + "SF59 (main-text figure 4 until 2026-09-10)\n", sf59)
sf59 = sub1("    ## Figure 4 — The required subsidy as a capital-cost gap: a bridge in cheap worlds\n",
            "    ## SF59 — The solved cost gap at the anchor worlds (main-text figure 4 until 2026-09-10)\n\n"
            "    Moved to the SI on 2026-09-10: the new main-text figure 3 shows the same quantity fanned\n"
            "    across the 10,000 cost worlds on the batch-6 refit map; this page keeps the direct model\n"
            "    solutions at the three percentile anchors per schedule (the evidence the map\n"
            "    interpolates) and the decay reading.\n", sf59)
sf59 = sub1('"Fig4_shadow_price.png"', '"SF59_shadow_price.png"', sf59)
sf59 = sub1('P.caption("Fig 4", ', 'P.caption("SF59", ', sf59)
sf57, sf58, sf59 = ren(sf57), ren(sf58), ren(sf59)

# ----------------------------------------------------------------------------- 3. the new Fig 3 (never renumbered)
NEW_FIG3 = (HERE / "_edit_20260910_blocks" / "fig3.txt").read_text(encoding="utf-8")

# ----------------------------------------------------------------------------- 4. the new Fig 4 = the old figure 6 renumbered, then repointed
f4 = ren(old_fig6)
assert f4.startswith(MARK + "Fig 4\n"), f4[:80]
f4 = sub1("    ## Figure 4 — The statutory wall: what caps can and cannot buy\n",
          "    ## Figure 4 — The statutory wall: what caps can and cannot buy\n\n"
          "    **Repointed 2026-09-10 to the batch-6 refit map** (`rate_design2_v2.ipynb`:\n"
          "    the registered family fit on 66 solved anchor worlds, band E6 = the\n"
          "    density-weighted leave-one-out p90, additive in rate points; the five-anchor\n"
          "    map and its ±E5 band are the pre-refit record, SF38/ST14). Renumbered figure 6\n"
          "    → figure 4 in the draft-v3 cut. Panels and encodings unchanged.\n", f4)
f4 = sub1('''        [[RD_FIG / "w38_rate_fans_pct_5a.png"],
         [RD_FIG / "w39_mask_paper_5a.png", RD_FIG / "w43_gap_paper_5a.png"]],
        "Fig6_required_itc_and_menu.png",''',
          '''        [[RD2_FIG / "n38_rate_fans_pct.png"],
         [RD2_FIG / "n39_mask_paper.png", RD2_FIG / "n43_gap_paper.png"]],
        "Fig4_statutory_wall.png",''', f4)
f4 = sub1('''        (RD_FIG / "w38_rate_fans_pct_5a.png", "rate_design/rate_design_v2_5a.ipynb",
         "S7 paper cell w38 (added 2026-09-09 by `_edit_20260909_display_cut.py`; the FIVE-ANCHOR twin)",
         "`u50_requirement_fans_cut_5a.csv` (the display twin: every value DISPLAY_CUT = 3 points below "
         "the mapped requirement; certificate: 30 exact anchors + the five-anchor leave-one-out band E5; "
         "GA1/GA2 PASS in `u101_verdict.csv`; the registered one-point fans are w34 / ST14)"),
        (RD_FIG / "w39_mask_paper_5a.png", "rate_design/rate_design_v2_5a.ipynb", "S7 paper cell w39 (2026-09-09)",
         "`u51_feasibility_mask_cut_5a.csv` (display twin of u51; the kills stay adjudicated on the registered "
         "twin in `u91_verdict_5a.csv`)"),
        (RD_FIG / "w43_gap_paper_5a.png", "rate_design/rate_design_v2_5a.ipynb", "S7 paper cell w43 (2026-09-09)",
         "`u52_demonstration_gap_cut_5a.csv` (display twin of u52)"),''',
          '''        (RD2_FIG / "n38_rate_fans_pct.png", "rate_design2/rate_design2_v2.ipynb",
         "figures cell (n38; the DISPLAY_CUT display twin)",
         "`m20_requirement_fans_cut.csv` (every value DISPLAY_CUT = 3 points below the mapped requirement; "
         "the chosen map of `m12_selection.csv` on 66 exact anchors + the leave-one-out band E6 of `m13_band_e6.csv`; "
         "R0/GA1'/GP' PASS in `m31_verdict.csv`; the registered one-point fans are n32 / ST14)"),
        (RD2_FIG / "n39_mask_paper.png", "rate_design2/rate_design2_v2.ipynb", "figures cell (n39)",
         "`m21_feasibility_mask_cut.csv` (display twin of m21; the kills stay adjudicated on the registered "
         "twin in `m31_verdict.csv`)"),
        (RD2_FIG / "n43_gap_paper.png", "rate_design2/rate_design2_v2.ipynb", "figures cell (n43)",
         "`m22_demonstration_gap_cut.csv` (display twin of m22)"),''', f4)
f4 = sub1('''    _e5 = float(pd.read_csv(BD_EXP / "b07_bill_attachment_5a.csv")["band_e5"].iloc[0])
    u50 = pd.read_csv(RD_EXP / "u50_requirement_fans_5a.csv")
    u50c = pd.read_csv(RD_EXP / "u50_requirement_fans_cut_5a.csv")
    br, brc = [d[(d["band"] == "base") & (d["quantity"] == "rate")].reset_index(drop=True) for d in (u50, u50c)]
    assert len(br) == len(brc) == 55''',
          '''    m12 = pd.read_csv(RD2_EXP / "m12_selection.csv")
    m31 = pd.read_csv(RD2_EXP / "m31_verdict.csv").set_index("name")
    CHOSEN, E6_PTS = m12["chosen"].iloc[0], int(m12["E6_pts"].iloc[0])
    assert m31.loc["R0", "result"] == "PASS" and m12["n_anchors"].iloc[0] == 66
    u50 = pd.read_csv(RD2_EXP / "m20_requirement_fans.csv")
    u50c = pd.read_csv(RD2_EXP / "m20_requirement_fans_cut.csv")
    br, brc = [d[(d["band"] == "base") & (d["quantity"] == "rate")].reset_index(drop=True) for d in (u50, u50c)]
    assert len(br) == len(brc) and len(br) == sum(1 for _ in br.itertuples())
    _kb1, _kb2 = m31.loc["KB1", "result"], m31.loc["KB2", "result"]
    print(f"refit map {CHOSEN}; E6 = {E6_PTS} points; KB1 {_kb1}; KB2 {_kb2}")''', f4)
f4 = sub1('''    u51c = pd.read_csv(RD_EXP / "u51_feasibility_mask_cut_5a.csv")
    W_COMMON = 2038
    assert (u51c["window"].dropna() == "w2038").any(), "u51 twin lacks the w2038 rows: rebuild rate_design_v2_5a"
    p36 = pd.read_csv(VOI_EXP / "p36_common_window_table.csv")
    assert (p36["common_year"] == W_COMMON).all()''',
          '''    u51c = pd.read_csv(RD2_EXP / "m21_feasibility_mask_cut.csv")
    W_COMMON = 2038
    assert (u51c["window"].dropna() == "w2038").any(), "m21 twin lacks the w2038 rows: re-run rate_design2_v2"
    p36 = pd.read_csv(RD2_EXP / "m23_common_window_table.csv")     # the refit-map common-window table (Table 2)
    assert (p36["common_year"] == W_COMMON).all()
    _p36_voi = pd.read_csv(VOI_EXP / "p36_common_window_table.csv")   # the pre-refit five-anchor table (SF56/ST19)
    _cmp = (p36[(p36["cut"] == "disp") & (p36["band"] == "base") & (p36["cap"] == 0.5)].set_index("schedule")["share_never"]
            - _p36_voi[(_p36_voi["cut"] == "disp") & (_p36_voi["band"] == "base") & (_p36_voi["cap"] == 0.5)].set_index("schedule")["share_never"])
    print("never-credit-feasible share, refit map minus five-anchor map (50% cap, display twin):", _cmp.round(3).to_dict())''', f4)
f4 = sub1('''    u52c = pd.read_csv(RD_EXP / "u52_demonstration_gap_cut_5a.csv")''',
          '''    u52c = pd.read_csv(RD2_EXP / "m22_demonstration_gap_cut.csv")''', f4)
f4 = sub1('''    gk = g[g["schedule"] != "cop28"]  # cop28's demonstration framing is killed (KB1)
    gmin, gmax = gk["gap_p50_B"].min(), gk["gap_p50_B"].max()
    gcop = float(g[g["schedule"] == "cop28"]["gap_p50_B"].iloc[0])''',
          '''    _killed = sorted(set(re.findall(r"\\('(\\w+)', '", m31.loc["KB1", "detail"]))) if _kb1 != "PASS-EXC" else []
    gk = g[~g["schedule"].isin(_killed)]   # schedules whose demonstration framing KB1 killed on the refit band
    gmin, gmax = gk["gap_p50_B"].min(), gk["gap_p50_B"].max()
    gkill_txt = ("; " + ", ".join(f"{P.SCHED_SHORT[s]} {float(g[g['schedule'] == s]['gap_p50_B'].iloc[0]):.1f} B$" for s in _killed if s in set(g["schedule"]))
                 + " quoted only as band ranges (KB1: above-cap need persists past the window at a band end)") if _killed else ""''', f4)
f4 = sub1('''    P.caption("Fig 4", f\'\'\'
    The statutory wall: what caps can and cannot buy. Every value is shown {CUT:.0%} of basis
    below the mapped requirement — the allowance for the finding that the credit which
    actually delivers the mandated build lies below the requirement the shadow prices imply
    (delivery one point below in 6 of 6 feed-back ladders, failure five points below; SF24a,
    ST9); the registered one-point values are in ST14. (a) Required statutory credit rate on
    each world's own build cost, per schedule and build year, fanned across the 10,000 cost
    worlds (five-anchor per-year map; median solid; interquartile and 5th-95th percentile
    bands; thin dotted = the +-{_e5*100:.0f}% certificate-band medians, the five-anchor
    leave-one-out band); dotted red line = the 50% stackable statutory maximum (30% base +''',
          '''    P.caption("Fig 4", f\'\'\'
    The statutory wall: what caps can and cannot buy. Every value is shown {CUT:.0%} of basis
    below the mapped requirement — the allowance for the finding that the credit which
    actually delivers the mandated build lies below the requirement the shadow prices imply
    (delivery one point below in 6 of 6 feed-back ladders, failure five points below; SF24a,
    ST9); the registered one-point values are in ST14. (a) Required statutory credit rate on
    each world's own build cost, per schedule and build year, fanned across the 10,000 cost
    worlds (the requirement map fit on 66 model-solved worlds, 11 per schedule; median solid;
    interquartile and 5th-95th percentile bands; thin dotted = the medians at the two ends of
    the map's leave-one-out error band, ∓{E6_PTS} rate points); dotted red line = the 50% stackable statutory maximum (30% base +''', f4)
f4 = sub1('''    the 60% cap, across schedules and the +-{_e5*100:.0f}% certificate band — quoted only
    as ranges. The cap choice alone moves the eia/aj shares by
    {int(kb2.min())}-{int(kb2.max())} points (the mask is a cap-sensitivity table), and
    cop28's above-cap need persists past the window at the low band end, so its
    demonstration framing is withdrawn (its median, {gcop:.1f} B$, is quoted only as a band
    range). (c) The demonstration funding requirement — the fixed-basis present value of''',
          '''    the 60% cap, across schedules and the ∓{E6_PTS}-point band — quoted only
    as ranges. The cap choice alone moves the eia/aj shares by
    {int(kb2.min())}-{int(kb2.max())} points (the mask is a cap-sensitivity table){gkill_txt}.
    (c) The demonstration funding requirement — the fixed-basis present value of''', f4)
f4 = sub1('''    60% cap run {gmin:.2f}-{gmax:.1f} B$ (base band; 95th percentile to {g95:.0f} B$, larger
    at the band ends — ST14); the outlay calibration carries a +-5% systematic. A''',
          '''    60% cap run {gmin:.2f}-{gmax:.1f} B$ (base band; 95th percentile to {g95:.0f} B$, larger
    at the band ends — ST14); the outlay calibration carries a +-5% systematic. Model-run
    tests of the wall's definition in the solved anchor worlds (batch 6, 57 credit runs):
    SF49–SF53, `rate_design2` m31. A''', f4)
f4 = sub1("solid; interquartile and p5–p95 bands; thin dotted lines = the ±E5\n    certificate-band medians). The horizontal red lines are the statutory",
          "solid; interquartile and p5–p95 bands; thin dotted lines = the medians at\n    the ∓E6 band ends). The horizontal red lines are the statutory", f4)
f4 = sub1("    **Key results** (computed in the cell below from the `_cut_5a` twins;\n",
          "    **Key results** (computed in the cell below from the `m2x_*_cut` twins;\n", f4)
f4 = sub1("analysis (`z-ethan/voi/`, SF56, ST19) showed that graduation years are\n",
          "analysis (`z-ethan/voi/`, SF56, ST19; on the five-anchor map) showed that graduation years are\n", f4)
assert "re.findall" in f4 and 'P.caption("Fig 4"' in f4
sub1('SETUP = """\nimport pandas as pd\n', 'SETUP = """\nimport re\n\nimport pandas as pd\n')

# ----------------------------------------------------------------------------- 5. old-token edits on the surviving text (before its renumbering)
sub1('''    p36 = pd.read_csv(VOI_EXP / "p36_common_window_table.csv")
    W_COMMON = int(p36["common_year"].iloc[0])''',
     '''    p36 = pd.read_csv(RD2_EXP / "m23_common_window_table.csv")   # 2026-09-10: the refit map (rate_design2 m23), band E6
    W_COMMON = int(p36["common_year"].iloc[0])''')
sub1('''    in {W_COMMON}; the last year is set by a handful of tail worlds. Sources: voi
    p36_common_window_table (rate_design five-anchor map).''',
     '''    in {W_COMMON}; the last year is set by a handful of tail worlds. Source: rate_design2
    m23_common_window_table (the batch-6 refit map, 66 solved anchor worlds; the pre-refit
    five-anchor table is voi p36, ST19o).''')
sub1('''    world gets under it. Values are the 3-point display twin (as Fig 6); the
    registered one-point cushion, the ±E5 band ends and the q90/q95/q99
    graduation years are in ST19o.''',
     '''    world gets under it. Values are the 3-point display twin (as Fig 6); the
    registered one-point cushion, the ∓E6 band ends and the q90/q95/q99
    graduation years are in ST19o. **Repointed 2026-09-10 to the batch-6 refit
    map** (`rate_design2` m23; the five-anchor voi p36 is the pre-refit record).''')
sub1('''    basis below the mapped requirement, as in Fig 6 (registered one-point values, the
    certificate-band ends and the q90/q95/q99 graduation years: ST19o). After {W_COMMON} at most''',
     '''    basis below the mapped requirement, as in Fig 6 (registered one-point values, the
    band ends and the q90/q95/q99 graduation years: ST19o). After {W_COMMON} at most''')
sub1("| **Certificate band (E5)** | How far the per-year requirement map may be off. We build the map from five model-solved cost worlds per schedule (the 5th, 25th, 50th, 75th and 95th percentiles) and interpolate between them. Hiding each interior anchor in turn and predicting it from the other four gives a largest error of 18% of the bill; every fan and mask is shown at the base case and at both ends of that band. |",
     "| **Map error band (E6)** | How far the per-year requirement map may be off. The map is fit to 66 model-solved cost worlds (11 per schedule: the 5th, 25th, 50th, 75th and 95th percentile worlds plus six placed to fill the corners of the cost-path plane; batch 6). Hiding one solved world at a time and predicting its rates from the others gives the leave-one-out error; E6 is its density-weighted 90th percentile, rounded up to one statutory rate point, and every fan and mask is shown at the base case and at rate ∓ E6. The pre-refit five-anchor map carried the bill band E5 (18% of the bill), which the detection analysis (SF58) still uses. |")
sub1("By 2038 all but a few percent of the worlds that ever become credit-feasible have done so, in every schedule at both ceilings (at most 1.5% of worlds graduate later at the 50% ceiling and 3.4% at 60%; EIA, whose builds start in 2038, is the exception; Table 2; `voi/` p36).",
     "By 2038 all but a few percent of the worlds that ever become credit-feasible have done so, in every schedule at both ceilings (EIA, whose builds start in 2038, is the exception; the shares are computed in Table 2 from the refit map, `rate_design2` m23; the five-anchor basis of the decision is `voi/` p36).")
sub1('''    seven figures and two tables — nine display items since 2026-09-10, when Ethan
    added Table 2 (what the capped credit alone reaches, by schedule; the outline's
    eight-item display budget needs his ruling). (The Table 2 slot had been freed
    2026-08-19 when the Monte Carlo variables table moved to the SI as ST10 and was
    consumed 2026-08-26 by Figure 5, the cost-of-detection figure.)''',
     '''    five figures and two tables — seven display items since the draft-v3 cut of
    2026-09-10 (the coauthor review: the technology-choice figure moved to SF57, the
    cost-of-detection figure to SF58, and the three-anchor cost-gap figure to SF59; the
    cost gap became figure 3 on the batch-6 refit map). Renaming on 2026-09-10: old figure 4
    → SF59 (replaced by the new figure 3), old figure 6 → figure 4, old figure 7 → figure 5;
    every cross-reference in this notebook and the SI notebook uses the new numbers.''')
sub1("    of cumulative new build after the 2030 anchor. Grey: every published projection that pairs a cost with a unit",
     "    of cumulative capacity built after 2030. Grey: every published projection that pairs a cost with a unit")
sub1("    ## SF38 — The dollar requirement fans (\\$/kW)\n",
     "    ## SF38 — The dollar requirement fans (\\$/kW) on the five-anchor map (pre-refit; main-text figure 3 is the refit)\n")
text = ren(text)
sub1('"Fig7_robustness.png"', '"Fig5_market_worlds.png"')

# ----------------------------------------------------------------------------- 6. stitch: Fig 3 (new) + Fig 4 (repointed) before the old figure 7 (now Fig 5)
anchor5 = MARK + "Fig 5\n"
assert text.count(anchor5) == 1
text = text.replace(anchor5, NEW_FIG3 + f4 + anchor5)

# ----------------------------------------------------------------------------- 7. SF57-59 before the tables section
anchor_st = MARK + "ST1-8\n"
assert text.count(anchor_st) == 1
text = text.replace(anchor_st, sf57 + sf58 + sf59 + anchor_st)

# ----------------------------------------------------------------------------- 8. checks
assert text.count('"Fig1_engine_vs_literature.png"') == 1 and text.count('"Fig2_schedules_and_cost_fans.png"') == 1
assert text.count('"Fig3_cost_gap_fans.png"') == 1 and text.count('"Fig4_statutory_wall.png"') == 1
assert text.count('"Fig5_market_worlds.png"') == 1
assert text.count('P.caption("Fig 3"') == 1 and text.count('P.caption("Fig 4"') == 1 and text.count('P.caption("Fig 5"') == 1
assert text.count('P.caption("SF57"') == 1 and text.count('P.caption("SF58"') == 1 and text.count('P.caption("SF59"') == 1
assert "Fig 6" not in text and "Fig 7" not in text and "Figure 6" not in text and "Figure 7" not in text
assert text.count("## Figure 3 —") == 1 and text.count("## Figure 4 —") == 1 and text.count("## Figure 5 —") == 1

BP.write_text(text, encoding="utf-8")
print("applied: Fig 3 (cost-gap fans, refit) + Fig 4 (wall, refit) + Fig 5 (market worlds); SF57/SF58/SF59; Table 2 on m23; renumbered")
