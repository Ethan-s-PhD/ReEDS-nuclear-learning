"""Read-only diagnostic for the step-6 error ("no associated capital costs: hydnd").

Run from the repo root, in the reeds environment:
    python z-ethan/agent_comms/2026-11-05_retail_pilot/scripts/diag_hydnd.py agretail_smr100_eo_p50
    python z-ethan/agent_comms/2026-11-05_retail_pilot/scripts/diag_hydnd.py agretail_fbR_none

It calls the retail module's own two functions up to the merge that raised the
error, and writes what it finds to results/<case>/diag_hydnd_*.csv in this
folder. It reads runs/<run>/inputs_case/ only. It writes nothing under runs/.
"""
import os
import sys

import gdxpds
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'postprocessing', 'retail_rate_module'))
sys.path.insert(0, REPO)
import calculate_historical_capex as chc  # noqa: E402

TECH = 'hydnd'


def gdx(inputs_case, sym):
    df = gdxpds.to_dataframe(os.path.join(inputs_case, 'inputs.gdx'), sym)
    df = df[sym] if isinstance(df, dict) else df
    df['i'] = df['i'].str.lower()
    return df


def main(run):
    inputs_case = os.path.join(REPO, 'runs', run, 'inputs_case')
    case = run.replace('agretail_', '', 1)
    out = os.path.join(HERE, '..', 'results', case)
    os.makedirs(out, exist_ok=True)

    # D1: historical units, raw tech names, that the module maps to hydnd
    sw = chc.reeds.io.get_switches(inputs_case)
    startyear = int(sw['startyear'])
    gendb = pd.read_csv(os.path.join(inputs_case, 'unitdata.csv'), low_memory=False)
    gendb = gendb.loc[gendb['StartYear'] <= startyear]
    raw = gendb['tech'].str.lower()
    mapped = raw.replace({'hyded': 'hydnd', 'hydend': 'hydnd'})
    d1 = (
        gendb.loc[mapped == TECH]
        .assign(tech_raw=raw)
        .groupby(['tech_raw', 'r'], as_index=False)['summer_power_capacity_MW'].sum()
    )
    d1.to_csv(os.path.join(out, 'diag_hydnd_D1_units.csv'), index=False)

    # D2: hydnd rows in each inputs.gdx symbol the module reads
    rows = []
    for sym in ['cost_cap', 'cost_cap_energy', 'cost_cap_fin_mult_out', 'rsc_dat']:
        df = gdx(inputs_case, sym)
        h = df.loc[df['i'] == TECH]
        rec = {'symbol': sym, 'rows_all': len(df), 'rows_hydnd': len(h),
               'regions_hydnd': h['r'].nunique() if 'r' in h else None}
        if sym == 'rsc_dat':
            for cat in ['cap', 'cost']:
                hc = h.loc[h['sc_cat'] == cat]
                rec[f'{cat}_rows'] = len(hc)
                rec[f'{cat}_rows_gt0'] = int((hc['Value'] > 0).sum())
                rec[f'{cat}_regions_gt0'] = hc.loc[hc['Value'] > 0, 'r'].nunique()
        rows.append(rec)
    d2 = pd.DataFrame(rows)
    d2.to_csv(os.path.join(out, 'diag_hydnd_D2_gdx.csv'), index=False)

    # D3: hydro tech names in each symbol, to compare with the module's map
    names = []
    for sym in ['cost_cap', 'cost_cap_energy', 'cost_cap_fin_mult_out', 'rsc_dat']:
        df = gdx(inputs_case, sym)
        for i in sorted(df['i'].unique()):
            if i.startswith('hyd'):
                names.append({'symbol': sym, 'i': i})
    d3 = pd.DataFrame(names, columns=['symbol', 'i'])
    d3.to_csv(os.path.join(out, 'diag_hydnd_D3_hydro_names.csv'), index=False)

    # D4: the module's cost tables, hydnd rows only
    regional, national = chc.get_earliest_cap_costs(inputs_case)
    d4 = pd.concat([
        regional.loc[regional['i'] == TECH].assign(table='regional'),
        national.loc[national['i'] == TECH].assign(table='national'),
    ])
    d4.to_csv(os.path.join(out, 'diag_hydnd_D4_module_costs.csv'), index=False)

    # D5: every historical tech left without a cost after the module's merge
    init_cap = chc.get_historical_units(inputs_case)
    merged = (
        init_cap.merge(regional, on=['i', 'region'], how='left')
        .merge(national, on='i', how='left')
        .assign(cost_cap=lambda x: x['cost_cap_x'].fillna(x['cost_cap_y']))
    )
    d5 = (
        merged.loc[merged['cost_cap'].isna()]
        .groupby('i', as_index=False)
        .agg(units=('cap_new', 'size'), MW=('cap_new', 'sum'), regions=('region', 'nunique'))
    )
    d5.to_csv(os.path.join(out, 'diag_hydnd_D5_no_cost.csv'), index=False)

    print(f'== {run}  (startyear {startyear})')
    for name, df in [('D1', d1), ('D2', d2), ('D3', d3), ('D4', d4), ('D5', d5)]:
        print(f'-- {name}')
        print(df.to_string(index=False) if len(df) else '(no rows)')


if __name__ == '__main__':
    main(sys.argv[1])
