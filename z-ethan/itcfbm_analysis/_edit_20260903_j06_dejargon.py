"""j06 (paper Fig 6c) — plain-word labels (2026-09-03, Ethan's coauthor review).

Schedule names come from plotstyle.SCHED_SHORT; "headline only" -> "single
run"; the fbC/fbB arm codes drop out of the legend ("with learning" / "no
learning"); the x label names the quantity and points at the sibling panel.
Label strings only; no numeric change. Same method as the 08-24 j06 script:
the builder is patched and the identical edit is mirrored into the executed
notebook (the h5 drive is unmounted, so no rebuild + re-execute); the PNG is
re-emitted once from the committed r04 export by the session-scratchpad
emitter (the cell's only input).
"""
import io
import sys
from pathlib import Path

import nbformat

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent

SUBS = [
    ('J06_LAB = {"eia": "EIA AEO high", "aj": "Abou-Jaoude", "iaea": "IAEA high",\n'
     '           "mck": "McKinsey", "cop28": "COP28", "eo": "EO 2025"}',
     'J06_LAB = dict(ps.SCHED_SHORT)                     # paper-facing schedule names (09-03)'),
    ('zorder=4, label="flat credit (eia world)")',
     'zorder=4, label="flat credit, all years (EIA AEO high world)")'),
    ('zorder=5, label=J06_LAB[w] + " (headline only)")',
     'zorder=5, label=J06_LAB[w] + " (single run)")'),
    ('label="with learning (fbC)")', 'label="with learning")'),
    ('label="no learning (fbB)")', 'label="no learning")'),
    ('ax.set_xlabel("ITC rate (model convention; same basis as Fig 5a)")',
     'ax.set_xlabel("tax credit rate (same basis as panel a)")'),
]

bp = HERE / "_build_notebook.py"
text = bp.read_text(encoding="utf-8")
for old, new in SUBS:
    assert text.count(old) == 1, (old, text.count(old))
    text = text.replace(old, new)
bp.write_text(text, encoding="utf-8")
print("patched _build_notebook.py (j06)")

nbp = HERE / "itcfbm_analysis.ipynb"
nb = nbformat.read(nbp, as_version=4)
c = next(c for c in nb.cells if c.get("id") == "j06cd001")
for old, new in SUBS:
    assert c.source.count(old) == 1, (old, c.source.count(old))
    c.source = c.source.replace(old, new)
nbformat.write(nb, nbp)
print("mirrored into itcfbm_analysis.ipynb (j06cd001)")
