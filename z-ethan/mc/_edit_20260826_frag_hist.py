"""Fragmentation histogram standalone emission (2026-08-26) -- companion to the Fig 3
recomposition in _edit_20260826_fig3_recompose.py (tech_comparison.ipynb).

The recomposed paper Fig 3 is a 2x2 of single-panel sources; the fragmentation
histogram is its panel (b), and the McKinsey capex-path panel (old Fig 3c) leaves the
paper entirely. The S13 cell keeps emitting the two-panel record figure
(fragmentation_penalty.png, internal letters c/d now historical) and additionally
saves the histogram standalone with its final baked letter "b".

Code cell changes -> re-execute the notebook headless afterwards (deterministic seed;
exports regenerate identically). Idempotent.
"""
import json
from pathlib import Path

NB = Path(__file__).resolve().parent / "mc_cost_trajectories.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
CELLS = {c["id"]: c for c in nb["cells"]}

if "fragmentation_hist.png" in "".join(CELLS["0f9efe09"]["source"]):
    print("fragmentation_hist emission already applied; nothing to do")
    raise SystemExit(0)

n = 0


def rep(cid, old, new):
    global n
    s = "".join(CELLS[cid]["source"])
    assert s.count(old) == 1, f"cell {cid}: pattern not unique/found:\n{old[:160]}"
    CELLS[cid]["source"] = s.replace(old, new).splitlines(keepends=True)
    n += 1


# ---- S13 code cell: retire the stale letter comment, add the standalone emission ----
rep("0f9efe09",
    "# Panel letters continue paper Figure 2: its first pasted source (tc_robustness_map)\n"
    "# carries panels a/b, so this second source carries c/d (plotstyle rule 3: unique\n"
    "# continuous letters across the composed page).",
    "# The two-panel figure keeps letters c/d as a notebook-record artifact (it left\n"
    "# the composed paper figure in the 2026-08-26 Fig 3 recomposition); the paper\n"
    '# panel is the standalone histogram emitted below with its final baked "b".')

rep("0f9efe09",
    'ps.savefig(fig, FIGURES / "fragmentation_penalty.png")\n'
    "plt.show()",
    'ps.savefig(fig, FIGURES / "fragmentation_penalty.png")\n'
    "plt.show()\n"
    "\n"
    "# Paper Fig 3 panel b (added 2026-08-26): the penalty histogram standalone. The\n"
    "# capex-path panel (old Fig 3c) left the paper in the same recomposition; Fig 2's\n"
    "# fans and this distribution carry that story.\n"
    "fig2, ax2 = plt.subplots(figsize=(6.2, 4.6))\n"
    'ax2.hist(100*penalty, bins=60, color=ps.ACCENT["violet"], alpha=0.8)\n'
    'for q, ls in [(50, "-"), (90, "--")]:\n'
    "    v = np.percentile(100*penalty, q)\n"
    "    ax2.plot([v, v], [0, ax2.get_ylim()[1]*0.9], color=ps.INK, ls=ls, lw=1.5)\n"
    '    ax2.text(v, ax2.get_ylim()[1]*0.93, f"P{q}: {v:.1f}%", ha="center", fontsize=8)\n'
    'ax2.set_xlabel("fragmentation penalty: split vs best concentrated program (%)")\n'
    'ax2.set_ylabel("draws")\n'
    'ps.panel_letter(ax2, "b")\n'
    "fig2.tight_layout()\n"
    'ps.savefig(fig2, FIGURES / "fragmentation_hist.png")\n'
    "plt.show()")

# ---- S13 markdown: extend the figure note -------------------------------------------
rep("9e4a38d8",
    "with its P50 (solid) and P90 (dashed) marked.*",
    "with its P50 (solid) and P90 (dashed) marked.*\n"
    "\n"
    "*Recomposition note (2026-08-26): the penalty histogram is additionally saved standalone as\n"
    "`fragmentation_hist.png` (baked letter b) — the recomposed paper Fig 3's panel b; the\n"
    "capex-path panel (old Fig 3c) left the paper.*")

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"applied {n} edits -> {NB.name}")
