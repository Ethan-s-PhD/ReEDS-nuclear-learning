"""Write the retail-rate module's output inputs for the other five stage-1 P50 runs (paper AG, 2026-11-05;
same method as the pilot, z-ethan/agent_comms/2026-11-05_retail_pilot/scripts/dump_outputs.py).

For each pilot case, read the archived outputs.h5 (read only) and write into
z-ethan/agent_comms/2026-11-05_retail_stage1/outputs/{case}/ (Claude ran this on Ethan's machine,
which holds the archive; the lab agent copies each folder to runs/agretail_{case}/outputs/):
- the 11 output tables that postprocessing/retail_rate_module/retail_rate_calculations.py reads,
  as CSVs with the h5 columns unchanged (report_dump.dfdict_to_csv writes the same tables);
- tc_phaseout_data/tc_phaseout_mult_{last year}.gdx, symbol tc_phaseout_mult_t(i, t), in the form
  that reeds/core/solve/1_tc_phaseout.py writes. The h5 key tc_phaseout_mult(i, v, t) is the same
  for every v, and the script asserts that before it drops v.

Run from the repo root with the reeds env (CONDA_DEFAULT_ENV=reeds, env on PATH, PYTHONPATH=.).
"""
import os
import gdxpds
import reeds.io as io

ARCHIVE = r"D:\ReEDS files\nuclear-learning\All runs so far"
CASES = {f"smr100_{t}_p50": f"test1_smr100_{t}_p50" for t in ["eia", "aj", "iaea", "mck", "cop28"]}
KEYS = ["load_cat", "systemcost_ba_retailrate", "expenditure_flow", "expenditure_flow_rps",
        "expenditure_flow_int", "emit_r", "cap_new_ivrt", "capex_ivrt", "systemcost_techba",
        "gen_ivrt", "tran_out"]

for case, archived in CASES.items():
    h5 = os.path.join(ARCHIVE, f"{archived}_outputs.h5")
    out = os.path.join("z-ethan", "agent_comms", "2026-11-05_retail_stage1", "outputs", case)
    os.makedirs(os.path.join(out, "tc_phaseout_data"), exist_ok=True)
    for k in KEYS:
        df = io.read_h5(h5, k)
        assert len(df), (archived, k)
        df.round(6).to_csv(os.path.join(out, f"{k}.csv"), index=False)
    tc = io.read_h5(h5, "tc_phaseout_mult")
    last = int(tc.t.max())
    tc = tc[tc.t == last]
    assert (tc.groupby("i").Value.nunique() == 1).all(), archived
    tc = tc.groupby("i", as_index=False).Value.first().rename(columns={"Value": "tc_phaseout_mult"})
    tc["t"] = last
    gdxpds.to_gdx({"tc_phaseout_mult_t": tc[["i", "t", "tc_phaseout_mult"]]},
                  os.path.join(out, "tc_phaseout_data", f"tc_phaseout_mult_{last}.gdx"))
    print(f"{out}: {len(KEYS)} tables and tc_phaseout_mult_{last}.gdx from {archived}")
