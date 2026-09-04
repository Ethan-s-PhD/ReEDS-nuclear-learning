"""d13 (paper Fig 5a) — plain-word labels (2026-09-03, Ethan's coauthor review).

Schedule codes become the paper-facing names (plotstyle.SCHED_SHORT), "PV" is
spelled out, and the "prior NN%" tag says what it is: the share of worlds whose
bill ends up over that cap. Label strings only; no numeric change.

Applied to the builder (`_build_notebook_stage3.py`) and mirrored into the
executed base notebook (`bridge_detection_stage3.ipynb`) so the two sources
stay byte-identical; the six market-world variant notebooks pick the change
up at their next build (their d13 panels are not in the paper). The PNG is
re-emitted once from the committed `b17_exceedance_noisy.csv` (the cell's own
input) by the session-scratchpad emitter, validated pixel-identical before
the edit; the 19-min notebook re-run is not needed for a label change.
"""
import io
import sys
from pathlib import Path

import nbformat

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent

SUBS = [
    ("# diagonal spend = cap (a hard bound up to one year's accrual). New figure,\n"
     "# 2026-08-25 amendment.\n",
     "# diagonal spend = cap (a hard bound up to one year's accrual). New figure,\n"
     "# 2026-08-25 amendment. 09-03 (Ethan, coauthor review): plain-word labels.\n"),
    ("            ax.annotate(f\"prior {rr['prior_exceed'].iloc[0]:.0%}\",\n"
     "                        (0.99, rr[\"X_2024B\"].iloc[0]),",
     "            ax.annotate(f\"{rr['prior_exceed'].iloc[0]:.0%} of worlds\\\\nover cap\",\n"
     "                        (0.99, rr[\"X_2024B\"].iloc[0]),"),
    ("    ax.set_title(ab)\nfor ax in axes[:, 0]:\n    ax.set_ylabel(\"spending cap (2024$B)\")",
     "    ax.set_title(ps.SCHED_SHORT[ab])\nfor ax in axes[:, 0]:\n"
     "    ax.set_ylabel(\"spending cap (2024$B)\")"),
    ('ax.set_xlabel("PV committed at detection (2024$B)")',
     'ax.set_xlabel("present value committed at detection (2024$B)")'),
]

bp = HERE / "_build_notebook_stage3.py"
text = bp.read_text(encoding="utf-8")
for old, new in SUBS:
    assert text.count(old) == 1, (old, text.count(old))
    text = text.replace(old, new)
bp.write_text(text, encoding="utf-8")
print("patched _build_notebook_stage3.py (d13)")

nbp = HERE / "bridge_detection_stage3.ipynb"
nb = nbformat.read(nbp, as_version=4)
for old, new in SUBS:
    o, w = old.replace("\\\\n", "\\n"), new.replace("\\\\n", "\\n")
    hits = [c for c in nb.cells if c.cell_type == "code" and o in c.source]
    assert len(hits) == 1 and hits[0].source.count(o) == 1, (o, len(hits))
    hits[0].source = hits[0].source.replace(o, w)
nbformat.write(nb, nbp)
print("mirrored into bridge_detection_stage3.ipynb (d13)")
