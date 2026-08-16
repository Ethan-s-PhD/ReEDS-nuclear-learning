"""Finalize the finding text after the 37-case re-run (2026-08-15).

Markdown-only edits (no code cell touched, so no re-execution is needed):
S2/S3/S10 statements updated with the large100 percentile results verified in
the executed notebook (t01/t02/t04/t09/t15). Idempotent.
"""
import json
from pathlib import Path

NB = Path(__file__).resolve().parent / "step3_analysis.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
CELLS = {c["id"]: c for c in nb["cells"]}

if "at every percentile" in "".join(CELLS["86ab11d5"]["source"]):
    print("md edits already applied; nothing to do")
    raise SystemExit(0)

n = 0


def rep(cid, old, new):
    global n
    s = "".join(CELLS[cid]["source"])
    assert s.count(old) == 1, f"cell {cid}: pattern not unique/found:\n{old[:160]}"
    CELLS[cid]["source"] = s.replace(old, new).splitlines(keepends=True)
    n += 1


# ---- S2 (cell 86ab11d5) -----------------------------------------------------------
rep("86ab11d5",
    "- Every large100 case has two clearly slack years (overbuild about 1%).\n"
    "- `large100_eia_p50` has a positive dual in only 6 of its 12 mandated years.\n"
    "  In the other years, the existing fleet plus voluntary builds already satisfy\n"
    "  the fleet-inclusive floor at a near-zero dual.",
    "- Every large100 case — all 18, at every percentile — has two clearly slack\n"
    "  years (overbuild about 1%).\n"
    "- Each `large100_eia_*` case has a positive dual in only 6 of its 12 mandated\n"
    "  years, at every percentile. In the other years, the existing fleet plus\n"
    "  voluntary builds already satisfy the fleet-inclusive floor at a near-zero\n"
    "  dual. The other large100 schedules price 10 of 12.")

# ---- S3 (cell 255c8d67) -----------------------------------------------------------
rep("255c8d67",
    "zero. The p95 duals stay close to flat. At p50, the large100 comparators need\n"
    "about 1.2x to 1.4x the smr100 dual in shared binding years.",
    "zero. The p95 duals stay close to flat. At p50, the large100 comparators need\n"
    "about 1.2x to 1.4x the smr100 dual in shared binding years. The percentile\n"
    "arm (t15, Step 4 delivery) shows this ratio is cost-world dependent: about\n"
    "1.4x to 3.5x at p05, and near parity (0.95x to 1.02x) at p95.")

# ---- S10 (cell ebc6728a) ----------------------------------------------------------
rep("ebc6728a",
    "7. **Adverse findings recap.** `smr100_eia_p05` overbuilds its floor by up to\n"
    "   3%. Every large100 case has two clearly slack years, and `large100_eia_p50`\n"
    "   prices its floor in only 6 of 12 mandated years. In the p95 worlds the dual\n"
    "   does not decay by 2050: the bridge does not come down inside the horizon in\n"
    "   the expensive draws.",
    "7. **Adverse findings recap.** `smr100_eia_p05` overbuilds its floor by up to\n"
    "   3%. Every large100 case (all 18) has two clearly slack years, and the\n"
    "   `large100_eia_*` cases price their floor in only 6 of 12 mandated years at\n"
    "   every percentile. In the p95 worlds — both families — the dual does not\n"
    "   decay by 2050: the bridge does not come down inside the horizon in the\n"
    "   expensive draws (large100 p95 end/peak 0.84–0.95). The required statutory\n"
    "   ITC exceeds 100% in 82 of 334 rate case-years across the 37 runs,\n"
    "   concentrated in the large100 p95 worlds (8–10 case-years per schedule):\n"
    "   an ITC alone cannot deliver those worlds.")

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"applied {n} markdown edits -> {NB.name}")
