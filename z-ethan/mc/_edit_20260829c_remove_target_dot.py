# 2026-08-29c - remove the black target dot from the F8 panels (Ethan): the +-$125 bar
# already sits exactly at (paired deployment, target) and is the tolerance geometry, so
# the dot is redundant ink. The bar becomes the target marker and takes the legend entry;
# the dotted crosshairs stay. Caption cell synced.
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
        raise AssertionError(f"pattern not found in {c.id!r}: {old[:90]!r}")
    assert c.source.count(old) == 1, f"pattern not unique in {c.id!r}: {old[:90]!r}"
    c.source = c.source.replace(old, new)


f8 = cell("atb-a6b-f8")
sub(f8,
    '            ax.plot([d_aj], [t50], "o", color=INK, ms=6, zorder=5,\n'
    '                    label="ATB 2050 target at\\nits paired deployment")\n',
    '            # 08-29 (Ethan): the target dot is removed - the +-$125 bar below IS the\n'
    '            # target marker (it sits exactly at the paired deployment and target).\n')
sub(f8,
    '            ax.plot([d_aj, d_aj], [t50 - TOL_END, t50 + TOL_END], color=INK, lw=2.2, alpha=0.85,\n'
    '                    solid_capstyle="butt", zorder=4)',
    '            ax.plot([d_aj, d_aj], [t50 - TOL_END, t50 + TOL_END], color=INK, lw=2.2, alpha=0.85,\n'
    '                    solid_capstyle="butt", zorder=4,\n'
    '                    label="ATB 2050 target ±$125/kW\\nat its paired deployment")')

cap = cell("atb-a6b-f8_caption")
sub(cap,
    "The black dot is the ATB 2050 target at its paired Abou-Jaoude deployment on the same\nthrough-2049 basis (dotted crosshairs; the quoted by-2050 program totals remain\n12/33/199 GW).",
    "The black bar marks the ATB 2050 target ±\\$125/kW at its paired Abou-Jaoude deployment\non the same through-2049 basis (dotted crosshairs; the quoted by-2050 program totals\nremain 12/33/199 GW; the separate target dot was removed 08-29 — the bar is the marker).")

nbformat.write(nb, NB)
print("patched", NB, "- target dot removed, bar takes the legend entry")
