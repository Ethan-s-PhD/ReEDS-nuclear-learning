# 2026-09-10 - Fig 2b/c legibility (coauthor review: "bigger fonts"): the fincapex-fan panels are
# composed at native pixel size and the docx scales the composed figure to the page width, so the
# lever is the figure width. W2 -> W1 per panel pair, titles 10 pt, legend 7.5 pt, and an x label
# ("year") on both panels, which the 09-09 cell omitted. Exports unchanged (same data).
#
# Edit method per the established convention: id-targeted, assert-guarded nbformat surgery on the
# cell `fincapex-fans-aj-eo` (inserted 09-09 by _edit_20260909_fincapex_fans.py); idempotent.
import io
import sys
from pathlib import Path

import nbformat

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
NB = HERE / "mc_cost_trajectories.ipynb"
CID = "fincapex-fans-aj-eo"
MARK = "figsize=(ps.W1, 2.6)"

nb = nbformat.read(NB, as_version=4)
cell = [c for c in nb.cells if c.get("id") == CID]
assert len(cell) == 1, f"cell {CID} not found"
cell = cell[0]
src = cell.source
if MARK in src:
    print("edits already applied; nothing to do")
    raise SystemExit(0)
REPS = [
    ("fig, axes = plt.subplots(1, 2, figsize=(ps.W2, 3.4), sharey=True, sharex=True)",
     "fig, axes = plt.subplots(1, 2, figsize=(ps.W1, 2.6), sharey=True, sharex=True)   # 09-10: W1 for print legibility"),
    ('        ax.set_title(f"{sched} ({US_SCHEDULES[sched][-1] - OFFSET_GW:.0f} GW 2050)", fontsize=9)\n        ax.set_ylim(*YLIM_FIN)',
     '        ax.set_title(f"{sched} ({US_SCHEDULES[sched][-1] - OFFSET_GW:.0f} GW 2050)", fontsize=10)\n        ax.set_ylim(*YLIM_FIN)\n        ax.set_xlabel("year")'),
    ('                   title=tlabel, fontsize=7, loc="lower left")',
     '                   title=tlabel, fontsize=7.5, loc="lower left")'),
]
for old, new in REPS:
    assert src.count(old) == 1, old[:70]
    src = src.replace(old, new)
cell.source = src
nbformat.write(nb, NB)
print(f"edited cell {CID!r} in {NB.name}: W1 panels, title 10 pt, legend 7.5 pt, x label 'year'")
