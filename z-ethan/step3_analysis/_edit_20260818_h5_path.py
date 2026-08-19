"""Repoint the h5 run directories at the reorganized drive layout (2026-08-18).

Ethan consolidated all run outputs into one flat folder:
`D:/ReEDS files/nuclear-learning/All runs so far` (test1_* + step4_* + itcfb_*).
The old `smr100 first run` and `step4 runs` folders no longer exist. Same edit
convention as every `_edit_*` script (id-targeted, assert-guarded, idempotent).
"""
import json
from pathlib import Path

NB = Path(__file__).resolve().parent / "step3_analysis.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
CELLS = {c["id"]: c for c in nb["cells"]}
cid = nb["cells"][1]["id"]
s = "".join(CELLS[cid]["source"])

if "All runs so far" in s:
    print("h5 path edit already applied; nothing to do")
    raise SystemExit(0)

old = '''H5_DIR = Path("D:/ReEDS files/nuclear-learning/smr100 first run")
H5_DIR4 = Path("D:/ReEDS files/nuclear-learning/step4 runs")   # large100 p05/p95 (Step 4 delivery)'''
new = '''# all run outputs consolidated into one flat folder (drive reorganized 2026-08-18)
H5_DIR = Path("D:/ReEDS files/nuclear-learning/All runs so far")
H5_DIR4 = H5_DIR                                # large100 p05/p95 (Step 4 delivery)'''
assert s.count(old) == 1, "path block not found/unique"
CELLS[cid]["source"] = s.replace(old, new).splitlines(keepends=True)

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("h5 directories repointed at 'All runs so far'")
