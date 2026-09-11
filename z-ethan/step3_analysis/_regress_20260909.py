"""Regression tie for the 2026-09-09 capex-panel insertions (f01b / f04b / f15b).

The three new cells add figures only. Every pre-existing file in `exports/`
and `figures/` must be byte-identical to the snapshot taken BEFORE
`_edit_20260909_capex_panels.py` ran (copied to the scratch folder given as
argv[1]). Prints a report and exits 1 on any violation. stdlib only.
"""
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRE = Path(sys.argv[1]) if len(sys.argv) > 1 else None
assert PRE and (PRE / "exports").is_dir(), "usage: _regress_20260909.py <snapshot dir with exports/ and figures/>"

EXPECT_NEW = {"f01b_new_nuclear_trajectories.png", "f04b_capex_gap_fans.png",
              "f15b_large_band_capex.png"}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


bad, n_ok = [], 0
for sub in ("exports", "figures"):
    for old in sorted((PRE / sub).iterdir()):
        new = HERE / sub / old.name
        if not new.exists():
            bad.append(f"{sub}/{old.name}: missing after re-run")
        elif sha(old) != sha(new):
            bad.append(f"{sub}/{old.name}: bytes changed")
        else:
            n_ok += 1
    new_only = sorted(p.name for p in (HERE / sub).iterdir() if not (PRE / sub / p.name).exists())
    print(f"{sub}: new files {new_only}")
    if sub == "figures" and set(new_only) != EXPECT_NEW:
        bad.append(f"figures: expected exactly {sorted(EXPECT_NEW)} new, got {new_only}")
    if sub == "exports" and new_only:
        bad.append(f"exports: unexpected new files {new_only}")

print(f"{n_ok} pre-existing files byte-identical")
if bad:
    print("REGRESSION TIE BROKEN:")
    for b in bad:
        print("  " + b)
    sys.exit(1)
print("regression tie holds.")
