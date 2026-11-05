"""Build a patched copy of the ReEDS retail-rate module for observation O33. The repo's module stays unedited.

Run from the repo root, in the reeds environment:
    python z-ethan/agent_comms/2026-11-05_retail_patched/scripts/make_patched_module.py

It copies postprocessing/retail_rate_module/ to runs/agretail_module_patch/ (git ignores runs/), at the same depth
below the repo root, so the copy finds the `reeds` package and runs/<run>/ exactly as the original does. A copy that
already exists is replaced. Then it applies the patches below, each of which must match exactly once, and writes
patch.diff next to this folder's results/.

Patches (marked "AG patch" in the copy):
1. retail_rate_calculations.py, generator capex (lines 878-889 and 907-930 of the original): the evaluation period
   and the tax depreciation schedule are matched to each technology by name ignoring case, and the fill of
   unmatched rows (20 years; schedule '20') is assigned. The original's `df[col].fillna(..., inplace=True)` does
   nothing under pandas 3. The copy writes the rows that still have no match before the fill to
   outputs/retail/agpatch_eval_unmatched.csv.
2. ferc_distadmin.py lines 383 and 449: the two chained assignments that pandas 3 ignores are assigned.
"""
import difflib
import hashlib
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
SRC = os.path.join(REPO, 'postprocessing', 'retail_rate_module')
DST = os.path.join(REPO, 'runs', 'agretail_module_patch')
RESULTS = os.path.join(HERE, '..', 'results')

# MD5 of the original files (trailing whitespace stripped, LF line ends), as committed on paper-AG
EXPECTED = {
    'retail_rate_calculations.py': '90061ca2ac28abc1373b0bd02785bd7b',
    'ferc_distadmin.py': 'b55c953972b8d5204dc69ec035a47461',
}

PATCHES = {
    'retail_rate_calculations.py': [
        # new builds: match ignoring case; assign the fills
        ("""    df_gen_capex = df_gen_capex.merge(
        eval_period[['i', 't', 'eval_period']],
        on=['i', 't'], how='left')
    # Fill in any missing eval_period with the default 20 years
    # This should apply to upgrades only
    df_gen_capex['eval_period'].fillna(20, inplace=True)
    df_gen_capex = df_gen_capex.merge(
        depreciation_sch[['i', 't', 'depreciation_sch']],
        on=['i', 't'], how='left')
    # Fill in any missing eval_period with the default 20 years
    # This should also apply to upgrades only
    df_gen_capex['depreciation_sch'].fillna('20', inplace=True)""",
         """    # AG patch (O33): match technology names ignoring case, and assign the fills
    # (pandas 3 ignores df[col].fillna(..., inplace=True))
    _ep = eval_period[['i', 't', 'eval_period']].assign(_il=lambda x: x['i'].str.lower()).drop(columns='i')
    _ds = depreciation_sch[['i', 't', 'depreciation_sch']].assign(_il=lambda x: x['i'].str.lower()).drop(columns='i')
    df_gen_capex['_il'] = df_gen_capex['i'].str.lower()
    df_gen_capex = df_gen_capex.merge(_ep, on=['_il', 't'], how='left')
    _agpatch_unmatched = [df_gen_capex.loc[df_gen_capex['eval_period'].isna()].assign(src='new')]
    # Fill in any missing eval_period with the default 20 years
    # This should apply to upgrades only
    df_gen_capex['eval_period'] = df_gen_capex['eval_period'].fillna(20)
    df_gen_capex = df_gen_capex.merge(_ds, on=['_il', 't'], how='left')
    # Fill in any missing eval_period with the default 20 years
    # This should also apply to upgrades only
    df_gen_capex['depreciation_sch'] = df_gen_capex['depreciation_sch'].fillna('20')
    df_gen_capex = df_gen_capex.drop(columns='_il')"""),
        # historical builds: same
        ("""    init_irt = df_gen_capex_init[['i', 'region', 't']].copy().drop_duplicates()""",
         """    init_irt = df_gen_capex_init[['i', 'region', 't']].copy().drop_duplicates()
    init_irt['_il'] = init_irt['i'].str.lower()  # AG patch (O33)"""),
        ("""        eval_period[eval_period['t']==first_year][['i', 'eval_period']],
        on='i', how='left')""",
         """        _ep[_ep['t']==first_year][['_il', 'eval_period']],
        on='_il', how='left')  # AG patch (O33)"""),
        ("""        depreciation_sch[depreciation_sch['t']==first_year][['i', 'depreciation_sch']],
        on='i', how='left')""",
         """        _ds[_ds['t']==first_year][['_il', 'depreciation_sch']],
        on='_il', how='left')  # AG patch (O33)"""),
        ("""    df_gen_capex_init['eval_period'].fillna(20, inplace=True)""",
         """    _agpatch_unmatched.append(df_gen_capex_init.loc[df_gen_capex_init['eval_period'].isna()].assign(src='historical'))
    df_gen_capex_init['eval_period'] = df_gen_capex_init['eval_period'].fillna(20)  # AG patch (O33)"""),
        ("""    df_gen_capex_init['depreciation_sch'].fillna('20', inplace=True)""",
         """    df_gen_capex_init['depreciation_sch'] = df_gen_capex_init['depreciation_sch'].fillna('20')  # AG patch (O33)
    os.makedirs(os.path.join(run_dir, 'outputs', 'retail'), exist_ok=True)
    pd.concat(_agpatch_unmatched)[['src', 'i', 'region', 't', 'capex']].to_csv(
        os.path.join(run_dir, 'outputs', 'retail', 'agpatch_eval_unmatched.csv'), index=False)"""),
    ],
    'ferc_distadmin.py': [
        ("""    dfall.state.replace({'DC':'MD'}, inplace=True)""",
         """    dfall['state'] = dfall['state'].replace({'DC':'MD'})  # AG patch (pandas 3)"""),
        ("""        df_extrapolate_dim['index'][df_extrapolate_dim['index'].values < 0] = 0""",
         """        df_extrapolate_dim.loc[df_extrapolate_dim['index'] < 0, 'index'] = 0  # AG patch (pandas 3)"""),
    ],
}


def normalized(path):
    with open(path, encoding='utf-8') as f:
        return '\n'.join(line.rstrip() for line in f.read().splitlines()) + '\n'


def main():
    for name, md5 in EXPECTED.items():
        got = hashlib.md5(normalized(os.path.join(SRC, name)).encode('utf-8')).hexdigest()
        print(f'original {name}: md5 {got}')
        assert got == md5, f'{name} differs from the paper-AG commit; stop and report'
    if os.path.isdir(DST):
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns('__pycache__'))
    os.makedirs(RESULTS, exist_ok=True)
    diff = []
    for name, pairs in PATCHES.items():
        old_text = normalized(os.path.join(SRC, name))
        text = old_text
        for old, new in pairs:
            n = text.count(old)
            assert n == 1, f'{name}: a patch matched {n} times; stop and report:\n{old}'
            text = text.replace(old, new)
        with open(os.path.join(DST, name), 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        diff += difflib.unified_diff(old_text.splitlines(True), text.splitlines(True),
                                     f'postprocessing/retail_rate_module/{name}', f'runs/agretail_module_patch/{name}')
        print(f'{name}: {len(pairs)} patches applied')
    with open(os.path.join(RESULTS, 'patch.diff'), 'w', encoding='utf-8', newline='\n') as f:
        f.writelines(diff)
    print(f'patched copy: {DST}')
    print(f'diff: {os.path.abspath(os.path.join(RESULTS, "patch.diff"))} ({sum(l.startswith("+") and not l.startswith("+++") for l in diff)} lines added)')


if __name__ == '__main__':
    main()
