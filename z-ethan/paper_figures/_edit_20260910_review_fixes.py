"""Figure-review fixes (2026-09-10, the fresh-context figure review of the draft-v3 cut).

MAJOR items: the renumbering regex had mapped the old figure-4 panel references (the solved
shadow-price figure, now SF59) onto the new Fig 3; ST14 had no refit tables; the Fig 3/4
captions did not disclose that the map's fit gate GM1 failed; the Fig 5 caption compared the
2035-window transfer with the 2038-window wall; stale composed PNGs. MINOR items: internal
codes in captions, one right-edge definition, one 60%-cap term, the SF56 cite, glosses in the
Fig 3 walk-through, Table 2 source names, the SF5 history note, the Fig 2 caption phrase.

Marker-based surgery on `_build_notebooks.py`; idempotent; rebuild + execute both notebooks.
"""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
BP = HERE / "_build_notebooks.py"
text = BP.read_text(encoding="utf-8")
if "ST14k_requirement_fans_refit.csv" in text:
    print("already applied")
    raise SystemExit(0)


def sub1(old, new):
    global text
    assert text.count(old) == 1, old[:90]
    text = text.replace(old, new)


# ---- 1. the mis-mapped old figure-4 references (SF32 page, SF36 page, SF48 page) ----------------
sub1("so every case starts at 1 and shapes compare directly. Main-text Fig 3b\n    until 2026-08-26,",
     "so every case starts at 1 and shapes compare directly. Main-text figure 4b (now SF59)\n    until 2026-08-26,")
sub1("    in the S3 text and the Fig 3 caption. In cheap worlds the curves decay to",
     "    in the S3 text and the SF59 caption. In cheap worlds the curves decay to")
sub1('"cell 26", "same shadow prices as Fig 3, normalized by each case\'s peak"),',
     '"cell 26", "same shadow prices as SF59, normalized by each case\'s peak"),')
sub1("    Shadow prices normalized by their own peak (main-text Fig 3b until 2026-08-26):",
     "    Shadow prices normalized by their own peak (main-text figure 4b until 2026-08-26; now SF59):")
sub1("    oversubsidy — so the panel largely re-plots the Fig 3 bill shape in",
     "    oversubsidy — so the panel largely re-plots the SF59 bill shape in")
sub1("    here. Ratios are unit-free, so the Fig 3/Fig 5 re-denomination does not",
     "    here. Ratios are unit-free, so the SF59/Fig 5 re-denomination does not")
# history notes that the regex turned into "main-text SF57x" / "main-text SF58x"
n57 = len(re.findall(r"main-text SF57([a-d]?)", text))
text = re.sub(r"main-text SF57([a-d]?)", lambda m: f"main-text figure 3{m.group(1)} (now SF57{m.group(1)})", text)
text = re.sub(r"Main-text SF57([a-d]?)", lambda m: f"Main-text figure 3{m.group(1)} (now SF57{m.group(1)})", text)
n58 = len(re.findall(r"main-text SF58([ab]?)", text))
text = re.sub(r"main-text SF58([ab]?)", lambda m: f"main-text figure 5{m.group(1)} (now SF58{m.group(1)})", text)
text = re.sub(r"Main-text SF58([ab]?)", lambda m: f"Main-text figure 5{m.group(1)} (now SF58{m.group(1)})", text)
sub1("    This panel was SF57b until the 2026-08-26 recomposition; the main text\n    keeps the probability panel (SF57a), and this page keeps the sizes.",
     "    This panel was main-text figure 3b (now SF57b) until the 2026-08-26 recomposition; SF57\n    keeps the probability panel (SF57a), and this page keeps the sizes.")

# ---- 2. ST14k-o: the refit tables behind Fig 3 / Fig 4 / Table 2 ---------------------------------
sub1('    P.table(RD_EXP / "u54_exposure_summary.csv", "ST14j_exposure_summary_3a.csv", round_=3)\n',
     '    P.table(RD_EXP / "u54_exposure_summary.csv", "ST14j_exposure_summary_3a.csv", round_=3)\n'
     '    # the batch-6 refit map (2026-09-10; the basis of main-text Fig 3, Fig 4 and Table 2): registered one-point tables\n'
     '    P.table(RD2_EXP / "m20_requirement_fans.csv", "ST14k_requirement_fans_refit.csv", round_=4)\n'
     '    P.table(RD2_EXP / "m21_feasibility_mask.csv", "ST14l_feasibility_mask_refit.csv", round_=4)\n'
     '    P.table(RD2_EXP / "m22_demonstration_gap.csv", "ST14m_demonstration_gap_refit.csv", round_=3)\n'
     '    P.table(RD2_EXP / "m23_common_window_table.csv", "ST14n_common_window_refit.csv", round_=4)\n'
     '    P.table(RD2_EXP / "m13_band_e6.csv", "ST14o_band_e6_refit.csv", round_=3)\n')
sub1("    The tables behind Fig 4a/Fig 4b and SF34/SF38 (new 2026-09-02; SN9; cited\n    from S3-4):",
     "    The tables behind main-text Fig 3, Fig 4 and Table 2 (k–o, the batch-6 refit map,\n"
     "    registered one-point cushion, band E6 per schedule; 2026-09-10) and behind SF34/SF38\n"
     "    (a–j, the pre-refit five- and three-anchor maps; new 2026-09-02; SN9; cited from S3-4):")
sub1("    Declining-credit tables (behind Fig 4a/Fig 4b, SF34, SF38), on the five-anchor map (a-e;",
     "    Declining-credit tables. (k-o) The batch-6 refit map behind main-text Fig 3, Fig 4 and Table 2:\n"
     "    requirement fans (m20), the feasibility mask (m21), the demonstration gap (m22), the common-window\n"
     "    table (m23) and the per-schedule leave-one-out error with the band E6 (m13); registered one-point\n"
     "    cushion; the paper's display twins subtract three points. (a-j) The pre-refit maps behind SF34/SF38,\n"
     "    on the five-anchor map (a-e;")

# ---- 3. GM1 disclosure + pointers + glosses in the Fig 3 block ---------------------------------
sub1("    SF24a); the registered one-point values are in the SI tables.",
     "    SF24a); the registered one-point values are in ST14k–o.")
sub1("    (`rate_design/methods.md` v2.4), and the selected map's leave-one-out\n"
     "    error sets the band E6 (density-weighted 90th percentile, rounded up to\n"
     "    one rate point).",
     "    (`rate_design/methods.md` v2.4). The leave-one-out error (hide one solved\n"
     "    world, predict its rates from the others) sets the band E6: its 90th\n"
     "    percentile with each solved world counted in proportion to how many of\n"
     "    the 10,000 worlds lie nearest to it, rounded up to one rate point. The\n"
     "    fit gate registered for the map (every schedule within 4 points on\n"
     "    average) did not pass: the EIA schedule's own error is about 14 points at\n"
     "    the 90th percentile, against 6–10 for the others, so the band is the\n"
     "    pooled one and the EIA panel is the least certain (`m31_verdict.csv`,\n"
     "    gate GM1).")
sub1("    (11 per schedule: the 5th, 25th, 50th, 75th and 95th percentile worlds of\n"
     "    program cost, plus six worlds per schedule placed to fill the corners of\n"
     "    the cost-path plane — batch 6).",
     "    (11 per schedule: the 5th, 25th, 50th, 75th and 95th percentile worlds of\n"
     "    program cost, plus six worlds per schedule placed to fill the corners of\n"
     "    the plane spanned by each world's 2031 cost and its 2050-to-2031 cost\n"
     "    ratio — the third and last model batch).")
sub1("    Every value is shown three statutory rate points below the mapped\n"
     "    requirement, the paper's display allowance (Ethan 09-09: the credit that\n"
     "    delivers the build lies below the requirement the shadow prices imply,\n"
     "    SF24a);",
     "    Every value is shown three statutory rate points below the mapped\n"
     "    requirement, the paper's display allowance (the feed-back runs showed that\n"
     "    the credit which delivers the build lies below the requirement the shadow\n"
     "    prices imply, SF24a);")
sub1('    CHOSEN, E6_PTS, GM1 = m12["chosen"].iloc[0], int(m12["E6_pts"].iloc[0]), m12["GM1"].iloc[0]\n',
     '    CHOSEN, E6_PTS, GM1 = m12["chosen"].iloc[0], int(m12["E6_pts"].iloc[0]), m12["GM1"].iloc[0]\n'
     '    _p90 = m13.set_index("ab")["p90"]\n'
     '    eia_p90, other_p90 = float(_p90["eia"]), (float(_p90.drop("eia").min()), float(_p90.drop("eia").max()))\n')
sub1("    points, the leave-one-out band E6 of the requirement map fit on 66 model-solved worlds,\n"
     "    11 per schedule); dashed vertical, the common demonstration-window end (2038, Fig 4).",
     "    points, the leave-one-out band E6 of the requirement map fit on 66 model-solved worlds,\n"
     "    11 per schedule; the registered fit gate GM1 did not pass — the EIA panel's own\n"
     "    leave-one-out 90th-percentile error is {eia_p90:.0f} points against\n"
     "    {other_p90[0]:.0f}–{other_p90[1]:.0f} for the others, so the pooled band understates it there);\n"
     "    dashed vertical, the common demonstration-window end (2038, Fig 4).")
sub1("    shadow-price requirement; SF24a); registered one-point values: ST14. The median world's",
     "    shadow-price requirement; SF24a); registered one-point values: ST14k. The median world's")

# ---- 4. Fig 4 block: pointers, codes, definitions, terms, GM1 ------------------------------------
sub1("    ST9); the registered one-point values are in ST14. (a) Required statutory credit rate on",
     "    ST9); the registered one-point values are in ST14k–n. (a) Required statutory credit rate on")
sub1('    CHOSEN, E6_PTS = m12["chosen"].iloc[0], int(m12["E6_pts"].iloc[0])\n'
     '    assert m31.loc["R0", "result"] == "PASS" and m12["n_anchors"].iloc[0] == 66\n',
     '    CHOSEN, E6_PTS = m12["chosen"].iloc[0], int(m12["E6_pts"].iloc[0])\n'
     '    assert m31.loc["R0", "result"] == "PASS" and m12["n_anchors"].iloc[0] == 66\n'
     '    m13 = pd.read_csv(RD2_EXP / "m13_band_e6.csv").set_index("ab")\n'
     '    eia_p90 = float(m13.loc["eia", "p90"])\n')
sub1("    the map's leave-one-out error band, ∓{E6_PTS} rate points); dotted red line = the 50% stackable statutory maximum (30% base +",
     "    the map's leave-one-out error band, ∓{E6_PTS} rate points — the pooled band; the map's registered fit gate\n"
     "    GM1 did not pass, and the EIA panel's own leave-one-out 90th-percentile error is {eia_p90:.0f} points);\n"
     "    dotted red line = the 50% stackable statutory maximum (30% base +")
sub1("    10% energy community + 10% domestic content), dash-dot = the 60% registered outer\n    bound. Fans are clipped",
     "    10% energy community + 10% domestic content), dash-dot = the hypothetical 60% cap (the registered outer\n    bound). Fans are clipped")
sub1('    clip_txt = ", ".join(f"{r.schedule} {int(r.year)}" for r in clip.itertuples())',
     '    clip_txt = ", ".join(f"{P.SCHED_SHORT[r.schedule]} {int(r.year)}" for r in clip.itertuples())')
sub1("    as ranges. The cap choice alone moves the eia/aj shares by\n",
     "    as ranges. The cap choice alone moves the EIA AEO high and Abou-Jaoude shares by\n")
sub1("    the cap choice moves the eia/aj shares by tens of points (registered kill",
     "    the cap choice moves the EIA AEO high and Abou-Jaoude shares by tens of points (registered kill")
sub1('                 f" The map ({CHOSEN}) extrapolates beyond the most expensive solved world by regression rather than a "',
     '                 f" The map (a pooled regression) extrapolates beyond the most expensive solved world rather than a "')
sub1("    in any schedule but EIA ({_late_eia:.0%}; its builds start in {W_COMMON}) (Table 2, SF56).\n"
     "    The right-edge labels are the share covered in the last build year, the share of worlds\n"
     "    the credit alone ever reaches (",
     "    in any schedule but EIA ({_late_eia:.0%}; its builds start in {W_COMMON}) (Table 2; SF56 is the\n"
     "    pre-refit decision-value figure). The right-edge labels are the share of worlds the credit\n"
     "    alone ever reaches (")

# ---- 5. Fig 5 caption: the transfer's window and map differ from Fig 4's; panel (b) wording ------
sub1("    with the base ranges in the Fig 4b/Fig 4c and SF58a captions: the share of cost worlds needing\n"
     "    an above-ceiling credit rate in a post-window build year (build years after 2035) spans",
     "    on the pre-refit five-anchor map and the registered 2035 window (ST18; not directly comparable\n"
     "    to Fig 4 and Table 2, which read the batch-6 refit map and the common 2038 window): the share\n"
     "    of cost worlds needing an above-ceiling credit rate in a post-window build year (build years\n"
     "    after 2035) spans")
assert "(b) Large-reactor\n    vs SMR by percentile, base market world:" in text
sub1("(b) Large-reactor\n    vs SMR by percentile, base market world:",
     "(b) The large-reactor\n    and SMR programs' gaps by year for each schedule (median-world lines, 5th–95th percentile\n"
     "    bands), base market world:")
sub1('    excl = sorted({f"{_wname[w]}/{ab}" for ab, ws in zip(own["schedule"], own["worlds_excluded"].fillna(""))',
     '    excl = sorted({f"{_wname[w]}/{P.SCHED_SHORT[ab]}" for ab, ws in zip(own["schedule"], own["worlds_excluded"].fillna(""))')

# ---- 6. Fig 2 caption phrase; Table 2 source names; inventory assert ----------------------------
sub1("    (b) and SMR (c), all four panels on one axis. Fans start in 2025 at each draw's backcast",
     "    (b) and SMR (c); both panel pairs share one y axis. Fans start in 2025 at each draw's backcast")
sub1('                "source": P.SCHED_NAME[ab].split(" (")[0],',
     '                "source": P.SCHED_SHORT[ab],')
sub1('    P.write_captions("main")\n    for f in sorted(P.OUT_FIG.glob("Fig*.png")):\n        print(f"figures/{f.name}")',
     '    P.write_captions("main")\n'
     '    _expect = {"Fig1_engine_vs_literature.png", "Fig2_schedules_and_cost_fans.png", "Fig3_cost_gap_fans.png",\n'
     '               "Fig4_statutory_wall.png", "Fig5_market_worlds.png"}\n'
     '    _have = {f.name for f in P.OUT_FIG.glob("Fig*.png")}\n'
     '    assert _have == _expect, f"stale or missing composed figures in figures/: {sorted(_have ^ _expect)}"\n'
     '    for f in sorted(P.OUT_FIG.glob("Fig*.png")):\n        print(f"figures/{f.name}")')

BP.write_text(text, encoding="utf-8")
print(f"applied; history notes reworded: SF57 x{n57}, SF58 x{n58}")
