"""j06 (the rate-deployment cliff) — x axis in percent (2026-09-09, Ethan's figure revisions).

The cliff leaves main-text Fig 6 for the SI (SF24, two panels with h06), and
every ITC value in the paper now reads as a percentage. The x axis gets a
percent formatter; the label drops the stale "same basis as panel a" (it no
longer sits next to the Fig 6a fans) and names the basis instead. Label and
tick-format strings only; no numeric change; the flat-anchor assert stays on
the fraction. Same method as the 08-24/09-03 j06 scripts: the builder is
patched and the identical edit is mirrored into the executed notebook, then
the notebook is re-executed headless (drive D mounted). Idempotent.
"""
import io
import sys
from pathlib import Path

import nbformat

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent

SUBS = [
    ('# ---- j06: the cliff, statutory basis, new nuclear only (main-text Fig 5c; 2026-08-24) -----------\n',
     '# ---- j06: the cliff, statutory basis, new nuclear only (main-text Fig 5c 2026-08-24; Fig 6c\n'
     '# 08-26; SI SF24 since 2026-09-09 -- x axis in percent) -----------------------------------------\n'),
    ('ax.set_xlabel("tax credit rate (same basis as panel a)")',
     'from matplotlib.ticker import PercentFormatter\n'
     'ax.set_xlabel("tax credit rate (statutory, model convention)")\n'
     'ax.xaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=0))'),
]

bp = HERE / "_build_notebook.py"
text = bp.read_text(encoding="utf-8")
if all(new in text for _, new in SUBS):
    print("builder already patched")
else:
    for old, new in SUBS:
        assert text.count(old) == 1, (old, text.count(old))
        text = text.replace(old, new)
    bp.write_text(text, encoding="utf-8")
    print("patched _build_notebook.py (j06)")

nbp = HERE / "itcfbm_analysis.ipynb"
nb = nbformat.read(nbp, as_version=4)
c = next(c for c in nb.cells if c.get("id") == "j06cd001")
if all(new in c.source for _, new in SUBS):
    print("notebook already mirrored")
else:
    for old, new in SUBS:
        assert c.source.count(old) == 1, (old, c.source.count(old))
        c.source = c.source.replace(old, new)
    nbformat.write(nb, nbp)
    print("mirrored into itcfbm_analysis.ipynb (j06cd001)")
