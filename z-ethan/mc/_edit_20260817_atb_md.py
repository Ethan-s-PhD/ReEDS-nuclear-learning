"""Refresh atb_parameter_space.ipynb markdown against the current 2026-08-06 exports.

Markdown-only edits (no code cell touched, so no re-execution is needed), found by
the 2026-08-17 section-4 claim audit:
- A4 (cell atb-10-a10_part1_md): the "RMSE is stored for ranking" clause is a ghost —
  no RMSE exists anywhere in the notebook (ranking is argmin of max-abs misfit).
- A7 (cell atb-23-a24_synth_md): the "What the run shows" bullets still carried the
  2026-08-04 grid's numbers; restated from the current exports
  (feasible_share.csv / best_fits.csv / synthesis.csv / required_deployment_anchors.csv).
Idempotent.
"""
import json
from pathlib import Path

NB = Path(__file__).resolve().parent / "atb_parameter_space.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
CELLS = {c["id"]: c for c in nb["cells"]}

if "0.03-0.86%" in "".join(CELLS["atb-23-a24_synth_md"]["source"]):
    print("md edits already applied; nothing to do")
    raise SystemExit(0)

n = 0


def rep(cid, old, new):
    global n
    s = "".join(CELLS[cid]["source"])
    assert s.count(old) == 1, f"cell {cid}: pattern not unique/found:\n{old[:160]}"
    CELLS[cid]["source"] = s.replace(old, new).splitlines(keepends=True)
    n += 1


# ---- A4 method cell (atb-10-a10_part1_md) -----------------------------------------
rep("atb-10-a10_part1_md",
    "Feasible-set sizes at $100 and $500 are reported alongside as\n"
    "a robustness check; RMSE is stored for ranking but decides nothing.",
    "Feasible-set sizes at $100 and $500 are reported alongside as\n"
    "a robustness check.")

# ---- A7 synthesis cell (atb-23-a24_synth_md) --------------------------------------
rep("atb-23-a24_synth_md",
    "**What the run shows** (2026-08-04 grid; the table below and T2–T5 carry the exact numbers):",
    "**What the run shows** (2026-08-06 export; the table below and T2–T5 carry the exact numbers):")

rep("atb-23-a24_synth_md",
    "anchor and re-anchors at the per-vendor 2OAK point, which costs roughly 2–3 points of firm-level\n"
    "  LR relative to the source's accounting (QA-3 (ii) shows the same setting overshooting the 2050\n"
    "  targets by $360–860/kW). In-support feasible shares are thin — 0.2–0.9% of the sampled space at\n"
    "  the $250/kW tolerance.",
    "anchor and re-anchors at the per-vendor 2OAK point, which costs roughly 2–3 points of firm-level\n"
    "  LR relative to the source's accounting (QA-3 (ii) shows the same setting overshooting the 2050\n"
    "  targets by $360–860/kW). Grid-best fits: moderate/advanced at LR 12.5–13% (in-support);\n"
    "  conservative's grid best sits at 17.5%, outside the 16% cap, with in-support fits only near the\n"
    "  tolerance edge (min in-support misfit $220/kW). In-support feasible shares are thin —\n"
    "  0.03-0.86% of the support-restricted grid at the $250/kW tolerance.")

rep("atb-23-a24_synth_md",
    "- **The ATB large-nuclear trajectories are harder to rationalize.** Moderate and advanced are\n"
    "  reachable in-support only in the maximum-spillover corner (best fits at LR 12.5%, just past the\n"
    "  12% cap; in-support shares 1–3%). Conservative — a 23% cost decline on just 12 GW of builds —\n"
    "  clears the tolerance nowhere in the support (min in-support misfit ≈ $286/kW) and needs\n"
    "  LR ≈ 18% without spillover help.",
    "- **The ATB large-nuclear trajectories are harder to rationalize.** Moderate and advanced are\n"
    "  reachable in-support only in the upper-spillover corner (grid-best fits at LR 13–13.5%, just\n"
    "  past the 12% cap; in-support shares 0.45–1.74%). Conservative — a 23% cost decline on just\n"
    "  12 GW of builds — clears the tolerance nowhere in the support (min in-support misfit\n"
    "  ≈ $277/kW) and needs LR ≈ 18% without spillover help.")

rep("atb-23-a24_synth_md",
    "wants roughly **2–3.4× the paired deployments** (SMR advanced: 484 GW vs the assumed 200; large\n"
    "  advanced: 677 GW), and at MC-central in-support worlds 3.5–18×.",
    "wants roughly **2–3.4× the paired deployments** (SMR advanced: 484 GW vs the assumed 200; large\n"
    "  advanced: 677 GW), and at MC-central in-support worlds ≈3–18×.")

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"applied {n} markdown edits -> {NB.name}")
