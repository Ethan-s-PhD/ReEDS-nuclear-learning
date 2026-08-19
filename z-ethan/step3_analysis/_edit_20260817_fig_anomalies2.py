"""Follow-up to _edit_20260817_fig_anomalies.py (2026-08-17, round 2).

After the blank-not-zero masking, the shared x-axes of the f04 and f15
schedule grids start at 2031 and matplotlib's default locator picked
fractional year ticks (2032.5, 2037.5, ...). Force integer year ticks.
Same convention: id-targeted, assert-guarded, idempotent.
"""
import json
from pathlib import Path

HERE_ = Path(__file__).resolve().parent
NB = HERE_ / "step3_analysis.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
CELLS = {c["id"]: c for c in nb["cells"]}

if "MaxNLocator(integer=True)" in "".join(CELLS["50efbfee"]["source"]):
    print("round-2 edits already applied; nothing to do")
    raise SystemExit(0)

n = 0


def rep(cid, old, new, count=1):
    global n
    s = "".join(CELLS[cid]["source"])
    assert s.count(old) == count, \
        f"cell {cid}: pattern count {s.count(old)} != {count}:\n{old[:160]}"
    CELLS[cid]["source"] = s.replace(old, new).splitlines(keepends=True)
    n += 1


TICKFIX = ('for ax in axes.flat:   # integer year ticks (fractional after masking)\n'
           '    ax.xaxis.set_major_locator(mpl.ticker.MaxNLocator(integer=True))\n')

rep("50efbfee", "fig.tight_layout()\nsavefig(fig, \"f04_dual_fans.png\")",
    TICKFIX + "fig.tight_layout()\nsavefig(fig, \"f04_dual_fans.png\")")
rep("t15cd001", "fig.tight_layout()\nsavefig(fig, \"f15_large_band.png\")",
    TICKFIX + "fig.tight_layout()\nsavefig(fig, \"f15_large_band.png\")")

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"applied {n} edits -> {NB.name}")
