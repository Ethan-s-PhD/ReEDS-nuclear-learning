# 2026-09-03b — Fig 3a (tech_comparison T5b): the two probe captions move from in-panel
# text into the legend. After the 09-03a de-jargon pass the plain-word caption for the
# left probe ("starting costs coupled only") overlapped the κ = 0 check markers; the
# legend has room (a fourth row) and the caption can then say the full contrast.
# Label/legend geometry only; no numeric change. Re-emitted from the exports.
import io
import sys
from pathlib import Path

import nbformat

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
NB = HERE / "tech_comparison.ipynb"
nb = nbformat.read(NB, as_version=4)
c = next(c for c in nb.cells if c.get("id") == "t5b-fig3a-panel")


def sub(old, new):
    assert c.source.count(old) == 1, (old, c.source.count(old))
    c.source = c.source.replace(old, new)


sub('for iid, xoff, mk, cap in [("probe_lr0_boak1", -0.06, "^", "starting costs\\ncoupled only"),\n'
    '                           ("probe_lr1_boak0", 1.06, "v", "learning rates\\ncoupled only")]:\n'
    '    d = ROBUST[ROBUST["cell"] == iid]\n'
    '    ax.scatter(np.full(len(d), xoff), d["P_smr"], marker=mk, s=28,\n'
    '               c=[SCHED_COLORS[s] for s in d["schedule"]], zorder=4)\n'
    '    ax.text(xoff, d["P_smr"].min() - 0.015, cap, ha="center", va="top",\n'
    '            fontsize=7, color=MUTED)\n',
    '# 09-03b: probe captions live in the legend (in-panel text collided with the κ = 0 checks)\n'
    'probe_handles = []\n'
    'for iid, xoff, mk, cap in [("probe_lr0_boak1", -0.06, "^",\n'
    '                            "starting costs coupled, learning rates independent"),\n'
    '                           ("probe_lr1_boak0", 1.06, "v",\n'
    '                            "learning rates coupled, starting costs independent")]:\n'
    '    d = ROBUST[ROBUST["cell"] == iid]\n'
    '    ax.scatter(np.full(len(d), xoff), d["P_smr"], marker=mk, s=28,\n'
    '               c=[SCHED_COLORS[s] for s in d["schedule"]], zorder=4)\n'
    '    probe_handles.append(plt.Line2D([], [], ls="", marker=mk, ms=6, color=MUTED, label=cap))\n')
sub('ax.legend(fontsize=6.5, loc="upper center", bbox_to_anchor=(0.5, -0.15), ncols=3)',
    'ax.legend(handles=ax.get_legend_handles_labels()[0] + probe_handles,\n'
    '          fontsize=6.5, loc="upper center", bbox_to_anchor=(0.5, -0.18), ncols=3)')
nbformat.write(nb, NB)
print("patched tech_comparison.ipynb (T5b): probe captions -> legend")
