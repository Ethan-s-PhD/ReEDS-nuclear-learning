"""Read-only extract for sizing observation O30 (the retail module's historical capital cost for supply-curve techs).

Run from the repo root, in the reeds environment, after the retail module has run for the run folder
(the module writes inputs_case/df_capex_init.csv):
    python z-ethan/agent_comms/2026-11-05_retail_stage1/scripts/o30_extract.py agretail_<case>

It reads runs/<run>/inputs_case/ only and writes four files to results/o30/<case>/ in this folder:
- o30_df_capex_init.csv          the module's historical builds and capex (copied unchanged)
- o30_retail_eval_period.csv     the module's evaluation periods (retail_eval_period, as the module reads it)
- o30_retail_depreciation_sch.csv  the module's tax depreciation schedules (same)
- o30_rsc_dat.csv                inputs.gdx rsc_dat rows for the technologies in df_capex_init
"""
import os
import shutil
import sys

import gdxpds

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'postprocessing', 'retail_rate_module'))
sys.path.insert(0, REPO)
import pandas as pd  # noqa: E402
from retail_rate_calculations import read_file  # noqa: E402


def main(run):
    inputs_case = os.path.join(REPO, 'runs', run, 'inputs_case')
    case = run.replace('agretail_', '', 1)
    out = os.path.join(HERE, '..', 'results', 'o30', case)
    os.makedirs(out, exist_ok=True)

    shutil.copyfile(os.path.join(inputs_case, 'df_capex_init.csv'), os.path.join(out, 'o30_df_capex_init.csv'))
    init = pd.read_csv(os.path.join(out, 'o30_df_capex_init.csv'))
    for name in ['retail_eval_period', 'retail_depreciation_sch']:
        read_file(os.path.join(inputs_case, name)).to_csv(os.path.join(out, f'o30_{name}.csv'), index=False)

    rsc = gdxpds.to_dataframe(os.path.join(inputs_case, 'inputs.gdx'), 'rsc_dat')
    rsc = rsc['rsc_dat'] if isinstance(rsc, dict) else rsc
    rsc = rsc.loc[rsc['i'].str.lower().isin(set(init['i'].str.lower()))]
    rsc.to_csv(os.path.join(out, 'o30_rsc_dat.csv'), index=False)

    print(f'== {run}')
    for f in sorted(os.listdir(out)):
        print(f'{f}: {len(pd.read_csv(os.path.join(out, f)))} rows')


if __name__ == '__main__':
    main(sys.argv[1])
