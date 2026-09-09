"""Regression tie for the 2026-09-08 anchor append (37 -> 49 cases).

Compares the pre-edit snapshot of `exports/` and `figures/` (copied to the
scratch folder given as argv[1] BEFORE `_edit_20260908_p25p75_anchors.py` ran)
with the re-executed notebook's outputs:

  * every line of every pre-existing t01-t20 CSV must appear unchanged in the
    new CSV (row-level byte identity);
  * every NEW line must belong to one of the 12 p25/p75 anchor cases (or, for
    schedule-keyed tables, must be absent -- t06/t07 are schedule-keyed and
    must be byte-identical whole);
  * every pre-existing figure PNG must be byte-identical (the anchors enter no
    pre-existing figure).

Prints a report and exits 1 on any violation. stdlib only.
"""
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRE = Path(sys.argv[1]) if len(sys.argv) > 1 else None
assert PRE and (PRE / "exports").is_dir(), "usage: _regress_20260908.py <snapshot dir with exports/ and figures/>"

ANCHOR_TOKENS = tuple(f"smr100_{s}_{p}" for s in ["eia", "aj", "iaea", "mck", "cop28", "eo"]
                      for p in ["p25", "p75"])
WHOLE_IDENTICAL = {"t06_cost_deltas.csv", "t07_system_npv.csv"}   # schedule-keyed tables

bad = []
report = []
for old in sorted((PRE / "exports").glob("t*.csv")):
    new = HERE / "exports" / old.name
    if not new.exists():
        bad.append(f"{old.name}: missing after re-run")
        continue
    o = old.read_text(encoding="utf-8").splitlines()
    n = new.read_text(encoding="utf-8").splitlines()
    if old.name in WHOLE_IDENTICAL:
        if o != n:
            bad.append(f"{old.name}: schedule-keyed table changed")
        report.append(f"{old.name:32s} identical whole ({len(o)} lines)")
        continue
    if o[0] != n[0]:
        bad.append(f"{old.name}: header changed")
    nset = set(n)
    lost = [ln for ln in o[1:] if ln not in nset]
    oset = set(o)
    added = [ln for ln in n[1:] if ln not in oset]
    foreign = [ln for ln in added if not any(tok in ln for tok in ANCHOR_TOKENS)]
    if lost:
        bad.append(f"{old.name}: {len(lost)} pre-existing rows changed/lost, e.g. {lost[0][:120]}")
    if foreign:
        bad.append(f"{old.name}: {len(foreign)} new rows not from an anchor case, e.g. {foreign[0][:120]}")
    report.append(f"{old.name:32s} {len(o) - 1:5d} old rows kept; +{len(added)} anchor rows")

for old in sorted((PRE / "figures").glob("*.png")):
    new = HERE / "figures" / old.name
    if not new.exists():
        bad.append(f"{old.name}: figure missing after re-run")
        continue
    same = hashlib.sha256(old.read_bytes()).hexdigest() == hashlib.sha256(new.read_bytes()).hexdigest()
    report.append(f"{old.name:32s} {'byte-identical' if same else 'CHANGED'}")
    if not same:
        bad.append(f"{old.name}: figure bytes changed")

new_only = sorted(p.name for p in (HERE / "exports").glob("t*.csv")
                  if not (PRE / "exports" / p.name).exists())
report.append(f"new exports: {new_only}")
new_figs = sorted(p.name for p in (HERE / "figures").glob("*.png")
                  if not (PRE / "figures" / p.name).exists())
report.append(f"new figures: {new_figs}")

print("\n".join(report))
if bad:
    print("\nREGRESSION TIE BROKEN:")
    for b in bad:
        print("  " + b)
    sys.exit(1)
print("\nregression tie holds: every pre-existing row and figure byte-identical; "
      "new rows belong to the 12 anchors only.")
