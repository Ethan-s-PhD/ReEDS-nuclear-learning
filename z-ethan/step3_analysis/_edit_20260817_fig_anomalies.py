"""Fix the 2026-08-17 figure-anomaly audit findings in step3_analysis.ipynb.

Edit method per the established convention (id-targeted, assert-guarded string
replacements on the raw json; `_build_notebook.py` is STALE-by-policy and must
never be recreated or run). Idempotent: re-running exits 0 without changes.

What this applies (Ethan's review, 2026-08-17):
A. cell c78b98c2: derive the PROGRAM (post-2030 additions) capacity basis.
   The large100 mandate files are the flat 97 GW existing-fleet floor plus the
   schedule's additions (verified against inputs/nuclear_learning/
   nuclear_cap_trajectory_*_large.csv), so the pre-2031 mandate level is the
   fleet floor and mandate_MW - floor is what the program builds. smr100
   mandates are additions already (floor = 0). Adds DUALS["program_MW"] and
   DUALS["in_program"].
B. Blank-not-zero: years with no mandated post-2030 builds were plotted as
   dual = 0 (and, in f12, billed at dual x fleet), reading as data. Dual and
   R_t lines now show nothing in those years:
   f04 (lines, fans, markers), f05, f07 (+ x realigned to the first BUILD
   year, so the dashed large100 comparators no longer start with a zero
   shelf), f12, f15, and the long pre-start zero overprint in f01's left
   panel (one leading zero year is kept so each takeoff stays visible).
C. f12 (Ethan's Fig4b finding): R_t = dual x program_MW, not dual x
   mandate_MW — the old basis multiplied the dual by the pre-existing fleet
   the fleet-inclusive large100 mandate also counts, inflating large100 bills
   (eia 2031: dual x 97 GW ~ 49 B$/yr for zero program builds). t08 and the
   t12 comparison inherit the corrected basis. smr100 values are unchanged
   (their floor is 0). Panel letters b/c (composed Fig4 stamps "a" on the
   required-ITC grid; house rule: letters unique and continuous per page).
D. Label collisions: f05 end-of-line labels dodged (eo/eia overprint); f06
   p95 vs "large p95" split apart; f08 y-locator densified so the negative
   range gets labeled ticks; f10 panel b gets its missing y-label.
"""
import json
from pathlib import Path

HERE_ = Path(__file__).resolve().parent
NB = HERE_ / "step3_analysis.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
CELLS = {c["id"]: c for c in nb["cells"]}

# ---- idempotency guard -------------------------------------------------------------
if "program_MW" in "".join(CELLS["c78b98c2"]["source"]):
    print("fig-anomaly edits already applied; nothing to do")
    raise SystemExit(0)

n = 0


def rep(cid, old, new, count=1):
    global n
    s = "".join(CELLS[cid]["source"])
    assert s.count(old) == count, \
        f"cell {cid}: pattern count {s.count(old)} != {count}:\n{old[:160]}"
    CELLS[cid]["source"] = s.replace(old, new).splitlines(keepends=True)
    n += 1


# ====================================================================================
# A. cell c78b98c2 — program (post-2030 additions) capacity basis
# ====================================================================================
rep("c78b98c2",
    'DUALS["clearly_slack"] = DUALS["mandated"] & (DUALS["slack_MW"] > 100)  '
    '# QA convention',
    'DUALS["clearly_slack"] = DUALS["mandated"] & (DUALS["slack_MW"] > 100)  '
    '# QA convention\n'
    '\n'
    '# Program (post-2030 additions) basis. The large100 mandate files are the flat\n'
    '# 97 GW existing-fleet floor plus the schedule\'s additions, so the pre-2031\n'
    '# mandate level IS the fleet floor and subtracting it leaves what the program\n'
    '# builds. smr100 mandates are additions already (floor = 0). (2026-08-17)\n'
    'FLOOR = DUALS[DUALS["t"] <= 2030].groupby("case")["mandate_MW"].max()\n'
    'DUALS["program_MW"] = (DUALS["mandate_MW"]\n'
    '                       - DUALS["case"].map(FLOOR).fillna(0.0)).clip(lower=0.0)\n'
    'DUALS["in_program"] = DUALS["program_MW"] > 0')

# ====================================================================================
# B. blank-not-zero masking
# ====================================================================================
# f04: lines/fans/markers only in program-build years
rep("50efbfee",
    '& (DUALS["variant"] != "eq") & (DUALS["t"] >= 2029)]\n'
    '           .pivot_table',
    '& (DUALS["variant"] != "eq") & (DUALS["t"] >= 2029)\n'
    '                 & DUALS["in_program"]]         # blank, not zero, before builds\n'
    '           .pivot_table')
rep("50efbfee",
    '& (DUALS["t"] >= 2029)\n'
    '                   & DUALS["mandated"]]',
    '& (DUALS["t"] >= 2029)\n'
    '                   & DUALS["in_program"]]')
rep("50efbfee",
    '(DUALS["family"] == "large") & (DUALS["schedule"] == s)\n'
    '                  & (DUALS["t"] >= 2029)]',
    '(DUALS["family"] == "large") & (DUALS["schedule"] == s)\n'
    '                  & (DUALS["t"] >= 2029) & DUALS["in_program"]]')

# f05: masking + dodged end labels (eo/eia endpoints overprinted)
rep("6d2bd87e",
    'fig, ax = plt.subplots(figsize=(7.5, 4.5))\n'
    'for s in SCHEDULES:\n'
    '    d = (DUALS[(DUALS["case"] == f"smr100_{s}_p50") & (DUALS["t"] >= 2029)]\n'
    '         .set_index("t")["dual_2024_MWyr"] * KWYR)\n'
    '    ax.plot(d.index, d.values, color=SCHED_C[s], lw=2.0)\n'
    '    ax.annotate(s, (d.index[-1], d.values[-1]), xytext=(5, 0),\n'
    '                textcoords="offset points", color=SCHED_C[s], fontsize=8.5, '
    'va="center")',
    'fig, ax = plt.subplots(figsize=(7.5, 4.5))\n'
    'ends = {}\n'
    'for s in SCHEDULES:\n'
    '    d = (DUALS[(DUALS["case"] == f"smr100_{s}_p50") & (DUALS["t"] >= 2029)\n'
    '               & DUALS["in_program"]]        # blank, not zero, before builds\n'
    '         .set_index("t")["dual_2024_MWyr"] * KWYR)\n'
    '    ax.plot(d.index, d.values, color=SCHED_C[s], lw=2.0)\n'
    '    ends[s] = float(d.values[-1])\n'
    '# end labels, dodged upward so near-equal endpoints (eo vs eia) never overprint\n'
    'min_gap = 0.035 * (ax.get_ylim()[1] - ax.get_ylim()[0])\n'
    'pos, prev = {}, None\n'
    'for s in sorted(ends, key=ends.get):\n'
    '    pos[s] = ends[s] if prev is None else max(ends[s], prev + min_gap)\n'
    '    prev = pos[s]\n'
    'for s in SCHEDULES:\n'
    '    ax.annotate(s, (2050, pos[s]), xytext=(5, 0), textcoords="offset points",\n'
    '                color=SCHED_C[s], fontsize=8.5, va="center")')

# f07: only program-build years; x realigned to the first build year
rep("4f4de157",
    'd = DUALS[(DUALS["case"] == c) & DUALS["mandated"]].set_index("t").sort_index()',
    'd = DUALS[(DUALS["case"] == c) & DUALS["in_program"]]'
    '.set_index("t").sort_index()',
    count=2)
rep("4f4de157",
    'ax.set_xlabel("years since first mandated model year")',
    'ax.set_xlabel("years since first mandated build year")')

# f15: fans only in program-build years
rep("t15cd001",
    '& (DUALS["variant"] != "eq") & (DUALS["t"] >= 2029)]\n'
    '               .pivot_table',
    '& (DUALS["variant"] != "eq") & (DUALS["t"] >= 2029)\n'
    '                     & DUALS["in_program"]]     # blank, not zero, before builds\n'
    '               .pivot_table')

# f01: cut the six-line zero overprint (keep one leading zero year per schedule)
rep("fbcb9fe1",
    '        tr = tr[tr.index >= 2024]\n',
    '        tr = tr[tr.index >= 2024]\n'
    '        nz = tr[tr > 0]\n'
    '        if len(nz):                    # blank the pre-start zero run,\n'
    '            tr = tr[tr.index >= int(nz.index.min()) - 1]  # keep one zero year\n')

# ====================================================================================
# C. f12 — R_t on the program basis; letters b/c
# ====================================================================================
rep("bca1c170",
    '    bill = d["dual_2004_MWyr"] * d["mandate_MW"] * TO2024 / 1e9',
    '    # R_t pays the dual on the program\'s post-2030 additions; the old\n'
    '    # mandate_MW basis also billed the pre-existing ~97 GW fleet that the\n'
    '    # fleet-inclusive large100 mandate counts (fixed 2026-08-17). No-build\n'
    '    # years are blank, not zero.\n'
    '    bill = (d["dual_2004_MWyr"] * d["program_MW"] * TO2024\n'
    '            / 1e9).where(d["program_MW"] > 0)')
rep("bca1c170",
    'pv = sum(float(bill[t]) * GAP[t] / DR ** (t - 2026) for t in bill.index)',
    'pv = sum(float(bill[t]) * GAP[t] / DR ** (t - 2026)\n'
    '             for t in bill.dropna().index)')
rep("bca1c170",
    'ps.panel_letter(fig.axes[0], "a")\n'
    'ps.panel_letter(axb, "b")',
    '# continuation letters: composed Fig4 stamps "a" on the required-ITC grid\n'
    'ps.panel_letter(fig.axes[0], "b")\n'
    'ps.panel_letter(axb, "c")')

# ====================================================================================
# D. remaining label fixes
# ====================================================================================
# f06: the smr p95 and large p95 endpoints coincide (~645) — split the labels
rep("b8178deb",
    '    ax.annotate(p, (xs[-1], ys[-1]), xytext=(6, 0), textcoords="offset points",\n',
    '    ax.annotate(p, (xs[-1], ys[-1]), xytext=(6, -8 if p == "p95" else 0),\n'
    '                textcoords="offset points",\n')
rep("b8178deb",
    '    ax.annotate(f"large {p}", (xs[-1], ys_l[-1]), xytext=(6, 0),\n',
    '    ax.annotate(f"large {p}", (xs[-1], ys_l[-1]),\n'
    '                xytext=(6, 8 if p == "p95" else 0),\n')

# f08: the negative range (policy-credit bars) had no labeled tick below 0
rep("44ef5584",
    'ax.axhline(0, color=EDGE_C, lw=1)',
    'ax.axhline(0, color=EDGE_C, lw=1)\n'
    'ax.yaxis.set_major_locator(mpl.ticker.MaxNLocator(nbins=11))  '
    '# ticks below 0 too')

# f10: panel b had no y-label
rep("afbb2ec2",
    'axes[1].axhline(0, color=EDGE_C, lw=1)',
    'axes[1].axhline(0, color=EDGE_C, lw=1)\n'
    'axes[1].set_ylabel("smr100 - large100 p50 system cost (2024$B/yr)")')

# ====================================================================================
NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"applied {n} edits -> {NB.name}")
