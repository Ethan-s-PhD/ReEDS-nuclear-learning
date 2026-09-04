# 2026-09-03 — de-jargon the main-paper panels this notebook emits (Fig 2a, Fig 4, Fig 7c).
# Ethan's request (coauthor review, 09-03): no internal codes in saved pixels —
# smr100/large100, p05/p50/p95, "dual", "additions basis", "fleet-inclusive" and the
# schedule codes all read in plain words. Label strings only; no numeric change.
# Shared vocabulary: z-ethan/plotstyle.py (SCHED_SHORT, PCT_LABEL, PROGRAM_LABEL).
#
# Execution note: the h5 drive is unmounted, so the notebook cannot re-run in full.
# The three PNGs are re-emitted once by executing these cells' exact sources against
# the QA exports (f01: mandate CSVs; f04/f15: duals_by_year.csv) — the same data the
# cells read anyway — via the session-scratchpad emitter, validated pixel-identical
# against the current PNGs before the edit. The cells run normally on the next full pass.
import io
import sys
from pathlib import Path

import nbformat

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
NB = Path(__file__).resolve().parent / "step3_analysis.ipynb"
nb = nbformat.read(NB, as_version=4)


def cell(cid):
    for c in nb.cells:
        if c.get("id") == cid:
            return c
    raise KeyError(cid)


def sub(c, old, new):
    assert c.source.count(old) == 1, f"{c.id!r}: {old!r} x{c.source.count(old)}"
    c.source = c.source.replace(old, new)


YLAB_OLD = 'ax.set_ylabel("mandate dual (2024$/kW-yr)")'
YLAB_NEW = 'ax.set_ylabel("shadow price of the mandate (2024$/kW-yr)")'

# setup: one schedule label convention across the paper ("2025 EO")
sub(cell("e9a82fe7"), '"cop28": "COP28 (300 GW)", "eo": "EO 2025 (400 GW)"}',
    '"cop28": "COP28 (300 GW)", "eo": "2025 EO (400 GW)"}')

# f01 — Fig 2a: the twelve mandate trajectories
f01 = cell("fbcb9fe1")
sub(f01, "# ---- f01: the twelve mandate trajectories ------------------------------------------\n",
    "# ---- f01: the twelve mandate trajectories ------------------------------------------\n"
    "# 09-03 (Ethan, coauthor review): plain-word titles and schedule names in the pixels.\n")
sub(f01, '(axes[0], "smr", "smr100 (additions basis)")',
    '(axes[0], "smr", "SMR program: new capacity")')
sub(f01, '(axes[1], "large", "large100 (fleet-inclusive)")',
    '(axes[1], "large", "large-reactor program: existing fleet + new capacity")')
sub(f01, "ax.annotate(s, (tr.index[-1], tr.values[-1]), xytext=(4, 0),",
    "ax.annotate(ps.SCHED_SHORT[s], (tr.index[-1], tr.values[-1]), xytext=(4, 0),")

# f04 — Fig 4: shadow-price fans
f04 = cell("50efbfee")
sub(f04, "# ---- f04: dual fans per schedule, large100 overlay -----------------------------------\n",
    "# ---- f04: dual fans per schedule, large100 overlay -----------------------------------\n"
    "# 09-03 (Ethan, coauthor review): axis and legend read 'shadow price', percentile\n"
    "# worlds and the large-reactor program in plain words.\n")
sub(f04, YLAB_OLD, YLAB_NEW)
sub(f04, 'axes.flat[0].legend(handles, ["p05", "p50", "p95", "large100 p05-p95", "mandated, near-zero dual"],',
    'axes.flat[0].legend(handles, [ps.PCT_LABEL[p] for p in ("p05", "p50", "p95")]\n'
    '                    + ["large-reactor program, P5–P95", "mandated year, shadow price ≈ 0"],')

# f15 — Fig 7c: the two programs' shadow-price bands
f15 = cell("t15cd001")
sub(f15, "# f15: the two families' dual bands per schedule (Fig 6 panel c)\n",
    "# f15: the two families' dual bands per schedule (Fig 7 panel c)\n"
    "# 09-03 (Ethan, coauthor review): plain-word program and percentile labels.\n")
sub(f15, 'label=f"{fam}100 p50" if k == 0 else None)',
    'label=f"{ps.PROGRAM_LABEL[fam + \'100\']}, median world" if k == 0 else None)')
sub(f15, YLAB_OLD, YLAB_NEW)
sub(f15, 'l15 + ["smr100 p05-p95", "large100 p05-p95"], fontsize=7)',
    'l15 + ["SMR program, P5–P95", "large-reactor program, P5–P95"], fontsize=7)')

nbformat.write(nb, NB)
print("patched", NB.name, "- setup label, f01, f04, f15 de-jargonned")
