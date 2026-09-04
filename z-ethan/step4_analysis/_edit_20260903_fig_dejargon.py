"""g02 / g03 (paper Fig 7a, 7b) — plain-word labels (2026-09-03, Ethan's coauthor review).

Row labels and panel titles use plotstyle.SCHED_SHORT / PCT_SHORT / PCT_LABEL
instead of "eia p05"; "dual" reads "shadow price"; "mandate unbound" reads
"mandate not binding"; the schedule label convention is "2025 EO". Label
strings only; no numeric change. The builder is patched and the identical
edit mirrored into the executed notebook (the h5 drive is unmounted, so no
rebuild + re-execute); the two PNGs are re-emitted once from the QA exports
(duals_by_year.csv, the cells' own input) by the session-scratchpad emitter,
validated pixel-identical against the current PNGs before the edit.
"""
import io
import sys
from pathlib import Path

import nbformat

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent

SUBS = [
    ('"cop28": "COP28 (300 GW)", "eo": "EO 2025 (400 GW)"}',
     '"cop28": "COP28 (300 GW)", "eo": "2025 EO (400 GW)"}'),
    ('"0 = mandate unbound"', '"0 = mandate not binding"'),
    ('ax.set_yticklabels([f"{tok} {p}" for tok, p in CASE_ORDER])\n'
     'ax.grid(False)\n'
     'fig.colorbar(im, ax=ax, shrink=0.6, label="end-of-horizon dual / peak dual")',
     'ax.set_yticklabels([f"{ps.SCHED_SHORT[tok]}, {ps.PCT_SHORT[p]}" for tok, p in CASE_ORDER])\n'
     'ax.grid(False)\n'
     'fig.colorbar(im, ax=ax, shrink=0.6, label="2050 shadow price ÷ peak shadow price")'),
    ('        ax.set_title(f"{SCHED_LABEL[tok]} — {p}")',
     '        ax.set_title(f"{ps.SCHED_SHORT[tok]}, {ps.PCT_LABEL[p]}", fontsize=9)'),
    ('            ax.set_ylabel("mandate dual (2024$/kW-yr)")',
     '            ax.set_ylabel("shadow price of the mandate (2024$/kW-yr)")'),
]

bp = HERE / "_build_notebook.py"
text = bp.read_text(encoding="utf-8")
for old, new in SUBS:
    assert text.count(old) == 1, (old, text.count(old))
    text = text.replace(old, new)
bp.write_text(text, encoding="utf-8")
print("patched _build_notebook.py (setup label, g02, g03)")

nbp = HERE / "step4_analysis.ipynb"
nb = nbformat.read(nbp, as_version=4)
for old, new in SUBS:
    hits = [c for c in nb.cells if c.cell_type == "code" and old in c.source]
    assert len(hits) == 1 and hits[0].source.count(old) == 1, (old, len(hits))
    hits[0].source = hits[0].source.replace(old, new)
nbformat.write(nb, nbp)
print("mirrored into step4_analysis.ipynb")
