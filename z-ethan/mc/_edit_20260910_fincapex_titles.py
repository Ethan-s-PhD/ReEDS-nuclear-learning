# 2026-09-10 (figure review) - Fig 2b/c panel titles and legend labels: the titles read
# "Abou-Jaoude mod (131 GW 2050)" / "2025 EO (397 GW 2050)" (fleet minus the 3 GW offset, a
# quantity no table defines) while the caption and Table 1 say 134 / 400 GW; the legend used
# "P5-P95" / "P25-P75" while Figs 3/4 use "5th-95th percentile". Titles now use the paper-facing
# schedule names (plotstyle.SCHED_SHORT) and the fleet 2050 target; legends use the paper form.
# Id-targeted, assert-guarded nbformat surgery on the cell `fincapex-fans-aj-eo`; idempotent.
import io
import sys
from pathlib import Path

import nbformat

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
NB = HERE / "mc_cost_trajectories.ipynb"
CID = "fincapex-fans-aj-eo"
MARK = "_SHORT_NAME = "

nb = nbformat.read(NB, as_version=4)
cell = [c for c in nb.cells if c.get("id") == CID]
assert len(cell) == 1, f"cell {CID} not found"
cell = cell[0]
src = cell.source
if MARK in src:
    print("edits already applied; nothing to do")
    raise SystemExit(0)
REPS = [
    ('FIN_FAN_SCHEDS = ["Abou-Jaoude mod", "2025 EO"]',
     'FIN_FAN_SCHEDS = ["Abou-Jaoude mod", "2025 EO"]\n'
     '_SHORT_NAME = {"Abou-Jaoude mod": ps.SCHED_SHORT["aj"], "2025 EO": ps.SCHED_SHORT["eo"]}   # paper-facing names (09-10)'),
    ('        ax.set_title(f"{sched} ({US_SCHEDULES[sched][-1] - OFFSET_GW:.0f} GW 2050)", fontsize=10)',
     '        ax.set_title(f"{_SHORT_NAME[sched]} ({US_SCHEDULES[sched][-1]:.0f} GW in 2050)", fontsize=10)'),
    ('    axes[0].legend(handles=[Patch(color=c, alpha=0.18, label="P5-P95"),\n'
     '                            Patch(color=c, alpha=0.35, label="P25-P75"),\n'
     '                            Line2D([], [], color=c, lw=1.8, label="median")],',
     '    axes[0].legend(handles=[Patch(color=c, alpha=0.18, label="5th–95th percentile"),\n'
     '                            Patch(color=c, alpha=0.35, label="25th–75th percentile"),\n'
     '                            Line2D([], [], color=c, lw=1.8, label="median world")],'),
]
for old, new in REPS:
    assert src.count(old) == 1, old[:70]
    src = src.replace(old, new)
cell.source = src
nbformat.write(nb, NB)
print(f"edited cell {CID!r}: paper-facing titles (fleet 2050 GW), percentile legend labels")
