"""Build cases_nuclearlearning_agretail1.csv: the Phase 6 retail-rate runs for the other five stage-1 P50 runs
(paper AG, 2026-11-05; same method as the pilot, z-ethan/agent_comms/2026-11-05_retail_pilot/scripts/build_retail_cases.py).

Each case is the fully resolved switch set of an archived run (reeds.inputs.parse_cases on its
source casefile) with one change: input_processing_only = 1, so ReEDS writes inputs_case and stops
before the model is compiled or solved. The script re-parses the written casefile and asserts that
each case equals its source plus that change.

Run from the repo root with the reeds env (CONDA_DEFAULT_ENV=reeds, env on PATH, PYTHONPATH=.).
"""
import pandas as pd
import reeds.inputs as ri

OUT = "cases_nuclearlearning_agretail1.csv"
CHANGE = {"input_processing_only": "1"}
# pilot case -> (source casefile, source case); archived h5 = {batch}_{case}_outputs.h5
CASES = {f"smr100_{t}_p50": ("cases_nuclearlearning_smr100.csv", f"smr100_{t}_p50")   # test1_smr100_{t}_p50
         for t in ["eia", "aj", "iaea", "mck", "cop28"]}

defaults = pd.read_csv("cases.csv", index_col=0, dtype=str, keep_default_na=False)["Default Value"]
base = {name: ri.parse_cases(f)[c].copy() for name, (f, c) in CASES.items()}
want = {}
for name, s in base.items():
    s = s.copy()
    for k, v in CHANGE.items():
        s[k] = v
    s["ignore"] = "0"
    want[name] = s

df = pd.DataFrame(want).fillna("")
keep = [k for k in df.index if k in defaults.index and (k in ("ignore", *CHANGE) or (df.loc[k] != defaults[k]).any())]
df = df.loc[keep]
out = pd.concat([pd.Series("", index=df.index, name="Default Value"), df], axis=1)
out.loc["ignore", "Default Value"] = "0"
out.to_csv(OUT)

chk = ri.parse_cases(OUT)
for name, b in base.items():
    got, exp = chk[name], want[name]
    common = exp.index.intersection(got.index).intersection(defaults.index)
    bad = {k: (exp[k], got[k]) for k in common if str(exp[k]) != str(got[k])}
    assert not bad, (name, bad)
    moved = {k for k in common if k != "ignore" and str(got[k]) != str(b.get(k, ""))}
    assert moved == set(CHANGE), (name, moved)
print(f"{OUT}: {len(want)} cases; rows {len(df)}; verified")
