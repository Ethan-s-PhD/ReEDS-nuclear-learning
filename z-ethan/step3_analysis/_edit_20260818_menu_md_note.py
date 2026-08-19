"""Markdown-only note on the t18 menu (2026-08-18, after the first full re-run).

The re-run showed the smr100 mandate rung sitting BELOW the floor (0.29-0.57 on
the cut basis). That is coherent, not a bug, and the menu markdown must say why:
a mandate compels compliance rather than inducing it, so its implicit transfer
is the realized (declining) price stream - the commitment bound plus fleet
rent - while the floor is the minimum among voluntary subsidy instruments
facing myopic investors. Markdown-only; no re-execution needed (per the
_edit_20260815_md_findings.py precedent).
"""
import json
from pathlib import Path

NB = Path(__file__).resolve().parent / "step3_analysis.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
CELLS = {c["id"]: c for c in nb["cells"]}
s = "".join(CELLS["t18md001"]["source"])

if "compelled, not induced" in s:
    print("menu md note already applied; nothing to do")
    raise SystemExit(0)

old = """- **commitment bound** (below 1 where duals decline): pays vintage b its
  foresight value C_b - needs a credible multi-decade schedule and
  foresighted investors, and the dual path is myopic-equilibrium output, so
  it is a bound, not a run.
"""
new = """- **commitment bound** (below 1 where duals decline): pays vintage b its
  foresight value C_b - needs a credible multi-decade schedule and
  foresighted investors, and the dual path is myopic-equilibrium output, so
  it is a bound, not a run.

One reading rule: the smr100 mandate rung sits *below* the floor. That is
coherent - compliance is compelled, not induced, so the capacity market pays
only the realized declining price path (the commitment bound's stream, plus
fleet rent where a fleet exists), not each vintage's myopic requirement S_t.
The floor is the minimum among *voluntary* subsidy instruments facing myopic
investors; instruments that rely on coercion (the mandate) or on credible
commitment (the C_b schedule) can undercut it, and the gap between them and
the floor is the price of voluntariness under myopia.
"""
assert s.count(old) == 1, "commitment bullet not found/unique"
CELLS["t18md001"]["source"] = s.replace(old, new).splitlines(keepends=True)
NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("t18 menu markdown note applied (markdown-only; outputs untouched)")
