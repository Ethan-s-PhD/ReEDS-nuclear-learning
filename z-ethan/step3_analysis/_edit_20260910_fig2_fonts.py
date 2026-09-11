"""Fig 2a legibility (2026-09-10, coauthor review: "bigger fonts").

The composed figure is pasted at native pixel size and scaled to the page width by the docx,
so the lever is the panel width: f01b goes from W2 x 4 in to W1 x 3 in, and the in-plot
schedule annotations from 8 to 9 pt. Nothing else changes; every pre-existing export and
figure must stay byte-identical (`_regress_20260909.py` against a pre-run snapshot).

Edit method per the established convention (id-targeted, assert-guarded nbformat surgery on
the cell `f01b-new-nuclear`; `_build_notebook.py` is STALE and must never be run). Idempotent.
"""
import json
from pathlib import Path

NB = Path(__file__).resolve().parent / "step3_analysis.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
CELLS = {c["id"]: c for c in nb["cells"]}
cell = CELLS["f01b-new-nuclear"]
src = "".join(cell["source"])
MARK = "figsize=(ps.W1, 3.0)"
if MARK in src:
    print("edits already applied; nothing to do")
    raise SystemExit(0)
REPS = [
    ("fig, ax = plt.subplots(figsize=(ps.W2, 4))",
     "fig, ax = plt.subplots(figsize=(ps.W1, 3.0))   # 09-10: W1 for print legibility"),
    ('textcoords="offset points", color=SCHED_C[s], fontsize=8, va="center")',
     'textcoords="offset points", color=SCHED_C[s], fontsize=9, va="center")'),
]
for old, new in REPS:
    assert src.count(old) == 1, old[:60]
    src = src.replace(old, new)
cell["source"] = src.splitlines(keepends=True)
NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("edited cell 'f01b-new-nuclear': W1 x 3.0 in, annotations 9 pt")
