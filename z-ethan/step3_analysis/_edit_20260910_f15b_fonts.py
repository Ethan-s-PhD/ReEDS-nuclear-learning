"""Fig 5b (f15b) legibility (2026-09-10, coauthor review: print size).

The composed figure is pasted at native pixel size and scaled to ~7 in by the docx, so the
lever is the panel width: f15b goes from 12.5 x 6.5 in to 8.4 x 4.8 in with text >= 9 pt and
the percentile labels in the paper's form ("5th-95th percentile"). Nothing else changes; every
pre-existing export and figure must stay byte-identical (`_regress_20260909.py`).

Edit method per the established convention (id-targeted, assert-guarded nbformat surgery on
the cell `f15b-large-band-capex`; `_build_notebook.py` is STALE and must never be run). Idempotent.
"""
import json
from pathlib import Path

NB = Path(__file__).resolve().parent / "step3_analysis.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
CELLS = {c["id"]: c for c in nb["cells"]}
cell = CELLS["f15b-large-band-capex"]
src = "".join(cell["source"])
MARK = "figsize=(8.4, 4.8)"
if MARK in src:
    print("edits already applied; nothing to do")
    raise SystemExit(0)
REPS = [
    ("fig, axes = plt.subplots(2, 3, figsize=(12.5, 6.5), sharex=True, sharey=True)",
     "fig, axes = plt.subplots(2, 3, figsize=(8.4, 4.8), sharex=True, sharey=True)   # 09-10: print legibility"),
    ("    ax.set_title(SCHED_LABEL[s], fontsize=9)",
     "    ax.set_title(ps.SCHED_SHORT[s], fontsize=10)\n    ax.tick_params(labelsize=9)"),
    ("        ax.set_ylabel(CAPEX_GAP_LABEL)", "        ax.set_ylabel(CAPEX_GAP_LABEL, fontsize=9)"),
    ('        ax.set_xlabel("year")', '        ax.set_xlabel("year", fontsize=9)'),
    ('    l15b + ["SMR program, P5–P95", "large-reactor program, P5–P95"], fontsize=7)',
     '    l15b + ["SMR program, 5th–95th percentile", "large-reactor program, 5th–95th percentile"], fontsize=9)'),
]
for old, new in REPS:
    assert src.count(old) == 1, old[:70]
    src = src.replace(old, new)
cell["source"] = src.splitlines(keepends=True)
NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("edited cell 'f15b-large-band-capex': 8.4 x 4.8 in, text >= 9 pt, percentile labels")
