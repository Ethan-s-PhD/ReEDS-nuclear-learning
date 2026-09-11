"""Fig 5b (f15b) follow-up (2026-09-10): at 8.4 in the in-axes legend of the first panel collides
with its y-axis labels, and the 3-year ticks crowd. Move the legend below the grid (as g03b does)
and thin the ticks. Id-targeted, assert-guarded nbformat surgery on `f15b-large-band-capex`; idempotent.
"""
import json
from pathlib import Path

NB = Path(__file__).resolve().parent / "step3_analysis.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
cell = {c["id"]: c for c in nb["cells"]}["f15b-large-band-capex"]
src = "".join(cell["source"])
MARK = 'fig.legend('
if MARK in src:
    print("edits already applied; nothing to do")
    raise SystemExit(0)
REPS = [
    ("axes.flat[0].legend(\n    h15b + [mpl.patches.Patch(facecolor=COL[\"smr\"], alpha=0.15),\n"
     "            mpl.patches.Patch(facecolor=COL[\"large\"], alpha=0.15)],\n"
     "    l15b + [\"SMR program, 5th–95th percentile\", \"large-reactor program, 5th–95th percentile\"], fontsize=9)",
     "fig.legend(\n    h15b + [mpl.patches.Patch(facecolor=COL[\"smr\"], alpha=0.15),\n"
     "            mpl.patches.Patch(facecolor=COL[\"large\"], alpha=0.15)],\n"
     "    l15b + [\"SMR program, 5th–95th percentile\", \"large-reactor program, 5th–95th percentile\"],\n"
     "    fontsize=9, ncol=2, frameon=False, loc=\"lower center\", bbox_to_anchor=(0.5, -0.06))"),
    ("    ax.xaxis.set_major_locator(mpl.ticker.MaxNLocator(integer=True))",
     "    ax.xaxis.set_major_locator(mpl.ticker.MaxNLocator(nbins=5, integer=True))"),
    ("fig.tight_layout()\nsavefig(fig, \"f15b_large_band_capex.png\")",
     "fig.tight_layout(rect=(0, 0.06, 1, 1))\nsavefig(fig, \"f15b_large_band_capex.png\")"),
]
for old, new in REPS:
    assert src.count(old) == 1, old[:70]
    src = src.replace(old, new)
cell["source"] = src.splitlines(keepends=True)
NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("edited cell 'f15b-large-band-capex': legend below the grid, 5-bin year ticks")
