"""Fragmentation histogram moves to the SI (Ethan, 2026-08-31) -- companion to
_edit_20260831a_fig3b_value_panel.py (tech_comparison.ipynb).

In the third Fig 3 recomposition the histogram leaves the main text: Fig 3b now
carries the baseline value-of-waiting panel (EVPI + 2036 switch bound vs kappa),
and the histogram joins SF6 -- the mixing page (mixed-build optimizer maps) --
as its panel f. SF6's other sources carry baked letters a-e, so the histogram's
baked letter changes "b" -> "f".

Code cell changes -> re-execute the notebook headless afterwards (deterministic
seed; exports regenerate identically). Idempotent.
"""
import json
from pathlib import Path

NB = Path(__file__).resolve().parent / "mc_cost_trajectories.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
CELLS = {c["id"]: c for c in nb["cells"]}

if 'ps.panel_letter(ax2, "f")' in "".join(CELLS["0f9efe09"]["source"]):
    print("fragmentation_hist SF6 re-letter already applied; nothing to do")
    raise SystemExit(0)

n = 0


def rep(cid, old, new):
    global n
    s = "".join(CELLS[cid]["source"])
    assert s.count(old) == 1, f"cell {cid}: pattern not unique/found:\n{old[:160]}"
    CELLS[cid]["source"] = s.replace(old, new).splitlines(keepends=True)
    n += 1


rep("0f9efe09",
    '# panel is the standalone histogram emitted below with its final baked "b".',
    '# panel was the standalone histogram below (baked "b" until 2026-08-31); it now\n'
    '# lives in the SI mixing page SF6 as panel f.')

rep("0f9efe09",
    "# Paper Fig 3 panel b (added 2026-08-26): the penalty histogram standalone. The\n"
    "# capex-path panel (old Fig 3c) left the paper in the same recomposition; Fig 2's\n"
    "# fans and this distribution carry that story.",
    "# SI figure SF6 panel f (was paper Fig 3b, 2026-08-26 to 2026-08-31): the penalty\n"
    "# histogram standalone. The third Fig 3 recomposition gave panel b to the baseline\n"
    "# value-of-waiting panel (EVPI + 2036 switch bound vs kappa) and re-homed this\n"
    "# histogram on the SI mixing page next to the mixed-build optimizer maps.")

rep("0f9efe09",
    'ps.panel_letter(ax2, "b")',
    'ps.panel_letter(ax2, "f")')

rep("9e4a38d8",
    "*Recomposition note (2026-08-26): the penalty histogram is additionally saved standalone as\n"
    "`fragmentation_hist.png` (baked letter b) — the recomposed paper Fig 3's panel b; the\n"
    "capex-path panel (old Fig 3c) left the paper.*",
    "*Recomposition note (2026-08-26, re-homed 2026-08-31): the penalty histogram is additionally\n"
    "saved standalone as `fragmentation_hist.png` — paper Fig 3's panel b until 2026-08-31, now\n"
    "SI figure SF6's panel f (baked letter f); Fig 3b carries the baseline value-of-waiting panel\n"
    "instead, and the capex-path panel (old Fig 3c) left the paper on 2026-08-26.*")

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"applied {n} edits -> {NB.name}")
