# 2026-08-29a — de-jargon the Fig 1 (F8) row labels in atb_parameter_space.ipynb.
# Ethan's ruling (08-29, following the v10.34 coinage sweep): internal coinages
# ("tiny-base"/"full-stock") stay out of paper-facing artifacts. The F8 ylabels are
# baked into the Fig 1 pixels, so they switch to the descriptive terms the Fig 1
# captions already use: "fresh-start" / "legacy-fleet-credited". The notebook-side
# caption cell is synced in the same pass. Markdown + label strings only — no
# numeric change — but the PNGs must be re-emitted, so the notebook is re-executed.
import io
import sys

import nbformat

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

NB = "atb_parameter_space.ipynb"
nb = nbformat.read(NB, as_version=4)


def cell(cid):
    for c in nb.cells:
        if c.get("id") == cid:
            return c
    raise KeyError(cid)


def sub(c, old, new):
    if old not in c.source:
        raise AssertionError(f"pattern not found in {c.id!r}: {old!r}")
    assert c.source.count(old) == 1, f"pattern not unique in {c.id!r}: {old!r}"
    c.source = c.source.replace(old, new)


# --- F8 code cell: the ylabels that end up in the Fig 1 pixels -------------------
f8 = cell("atb-a6b-f8")
sub(f8,
    '("tiny-base" if conv == 0 else "full-stock")',
    '("fresh-start" if conv == 0 else "legacy-fleet-credited")')
sub(f8,
    "# shares are SHAPES-based (the endpoint_feasible_share.csv population) so panel and CSV\n"
    "# cannot drift; the paper's one-sided reach-within-TOL criterion is text + SI only.",
    "# shares are SHAPES-based (the endpoint_feasible_share.csv population) so panel and CSV\n"
    "# cannot drift; the paper's one-sided reach-within-TOL criterion is text + SI only.\n"
    "# 08-29 (Ethan): row labels de-jargonned - the internal stratum names (tiny-base /\n"
    "# full-stock) stay out of paper-facing pixels; the descriptive labels match the\n"
    "# Fig 1 caption (fresh-start / legacy-fleet-credited).")

# --- notebook-side caption cell, kept in sync with the composed Fig 1 caption ----
cap = cell("atb-a6b-f8_caption")
sub(cap,
    "tiny-base vs full-stock rows.",
    "fresh-start vs legacy-fleet-credited rows (the internal tiny-base / full-stock "
    "stratum names stay out of paper-facing artifacts, 08-29).")
sub(cap,
    "(the large full-stock rows)",
    "(the large legacy-fleet-credited rows)")

nbformat.write(nb, NB)
print("patched", NB, "- F8 ylabels + caption cell de-jargonned")
