# Step 3 output checks — report

Date of this report: 2026-08-12.
Input folder: `D:\ReEDS files\nuclear-learning\smr100 first run`.
The folder has 28 files: 25 production runs and 3 copies of old pilot runs.
The tests cover only the 25 production runs.
The notebook `step3_output_checks.ipynb` performs all tests.

## Summary

The notebook performed 54 checks.
Result counts: {'PASS': 44, 'INFO': 10}.
**All pass/fail tests passed.** No test found a defect in the 25 runs.
Rows with the status INFO give context data. They have no pass condition.

Status meanings:

- **PASS** — the condition holds.
- **FAIL** — the condition does not hold. This shows a defect.
- **INFO** — context data only. There is no pass condition.
- **BLOCKED** — the test could not run. Data is missing.

## Phase A — File inventory and solve health

These tests make sure that the file set is complete and that each solve is clean.

| Test | Result | Data |
|---|---|---|
| one output file exists for each of the 25 cases | **PASS** | 25 files in D:\ReEDS files\nuclear-learning\smr100 first run |
| extra files in the folder are identified | **INFO** | 3 extra files: ['test1_smr100_eia_hi_outputs.h5', 'test1_smr100_eia_lo_outputs.h5', 'test1_smr100_eia_mid_outputs.h5'] |
| the three extra files are copies of the old pilot files | **PASS** | test1_smr100_eia_hi_outputs.h5: same hash as pilot original; test1_smr100_eia_lo_outputs.h5: same hash as pilot original; test1_smr100_eia_mid_outputs.h5: same hash as pilot original |
| all 25 files have the same data keys (dual keys can be absent when zero) | **PASS** | key counts [209]; dual keys absent in: {'smr100_eia_p05': ['nuclear_cap_price_ub', 'nuclear_cap_price_ub_raw'], 'smr100_eia_p50': ['nuclear_cap_price_ub', 'nuclear_cap_price_ub_raw'], 'smr100_eia_p95': ['nuclear_cap_p... |
| the solver residuals are small in every file | **PASS** | worst /residual/ 7.36e-04 at ('smr100_eia_p05', {'z': 0.0007360000163316727, 'm_rsc_dat': 2.631204587544289e-09}) |
| the objective value is a normal positive number in every file | **PASS** | range 1.4470e+12 (smr100_eo_p05) to 1.8856e+12 (smr100_eo_p95) |
| the model years are correct in every file (annual 2031-2035 block present) | **PASS** | expected [2010, 2015, 2020, 2023, 2026, 2029, 2031, 2032, 2033, 2034, 2035, 2038, 2041, 2044, 2047, 2050] |
| every run used the sequential solve mode | **PASS** | pvf_capital==1 (max dev 0.0e+00); pvf_onm flat from 2026 at 14.7645 (max dev 9.5e-07); cost_scale==1; z_rep has 16 years in every file |

## Phase B — Input data fingerprints

These tests make sure that each run used the correct input data. The tests compute the expected values from the repository input files.

| Test | Result | Data |
|---|---|---|
| the capital cost data agrees with the plant input files (all 25 cases) | **PASS** | 2050 (case,tech,year) points; max rel err 4.24e-07 at (smr100_eo_p05, nuclear-smr, 2050) |
| the heat rate data agrees with the plant input files | **PASS** | both techs, all cases (old vintages can differ a little) |
| the variable cost (VOM) data agrees with the plant input files | **PASS** | modal VOM within 2%, all cases |
| the fixed cost (FOM) data agrees with the plant input files (smr100 cases) | **PASS** | implied FOM within 5% of plantchar, all smr100 cases |
| implied large-reactor FOM in the large100 cases (mixed fleet) | **INFO** | (implied, plantchar) $/kW-yr 2022$: {'large100_eia_p50': (228.1, 171.9), 'large100_aj_p50': (228.7, 178.3), 'large100_iaea_p50': (218.9, 182.0), 'large100_mck_p50': (218.4, 186.9), 'large100_cop28_p50': (194.2, 152.8)... |
| the ccmult check value is correct (QA9 pin) | **PASS** | 1.268124 |
| the finance multiplier has the correct regional structure | **PASS** | max ratio spread over years 7.66e-04 (all 25 cases) |
| the finance multiplier agrees with our own calculation | **PASS** | worst /residual/ 8.35e-04 (GAMS rounds to 3 decimals) |
| the regional factors are inside the county data range | **PASS** | implied range [0.9528, 1.2539] inside county range [0.9456, 1.2717] |
| the regional factors are the same in all 25 cases | **PASS** | max cross-case difference 5.11e-04 |
| the model gives no ITC to nuclear technology (fin_mult == fin_mult_noITC) | **PASS** | max /difference/ 0.00e+00 in every (tech, region, year) of every case; the pilot-vintage 2038 wedge is gone |
| the system cost data shows no ITC payments for nuclear technology | **PASS** | max /nuclear ITC row/ $0 |
| the other technologies keep their ITC | **PASS** | total ITC tax expenditure magnitude 123.5 to 124.8 B$ per case (recorded as negative) |
| the incentives input file has zero nuclear ITC (and obbba does not) | **PASS** | 8 nuclear rows, itc columns all zero; obbba nuclear itc_frac max 0.30 |
| the mandate technology input files are correct | **PASS** | smr -> ['nuclear-smr']; large -> ['nuclear'] |

## Phase C — Mandate mechanics and dual prices

These tests make sure that the capacity mandate and its dual price operate correctly.

| Test | Result | Data |
|---|---|---|
| the capacity satisfies the mandate floor in every case | **PASS** | no violation larger than 5 MW in any mandated year |
| the capacity equals the floor in each binding year (positive dual) | **PASS** | every year with dual > $1/MW-yr has /slack/ <= 5 MW |
| a positive dual occurs only in the binding years | **PASS** | every year with slack > 100 MW has a zero dual |
| the dual conversion is correct (raw = cost_scale x pvf_onm x converted) | **PASS** | max rel err 1.29e-07 across all cases with duals |
| no large-reactor builds occur after 2030 in the smr100 cases | **PASS** | all 19 smr100 cases clean |
| no SMR builds occur in the large100 cases | **PASS** | all 6 large100 cases clean |
| no SMR capacity exists before 2031 | **PASS** | max pre-2031 SMR capacity 0.0 MW |
| the technology names are correct (no stray SMR names) | **PASS** | tech set clean; nuclear filters use the exact name nuclear-smr |
| overbuild and binding years by case | **INFO** | binding-year counts {'smr100_eia_p05': 4, 'smr100_eia_p50': 5, 'smr100_eia_p95': 5, 'smr100_aj_p05': 10, 'smr100_aj_p50': 10, 'smr100_aj_p95': 10, 'smr100_iaea_p05': 10, 'smr100_iaea_p50': 10, 'smr100_iaea_p95': 10, '... |

## Phase D — Equality case behavior

These tests make sure that the equality case shows the same behavior as the floor case.

| Test | Result | Data |
|---|---|---|
| the equality case gives the same objective value | **PASS** | rel difference 0.00e+00 (1.631947e+12 vs 1.631947e+12) |
| the equality case gives the same national capacity and generation | **INFO** | {'cap': '4.38e-04', 'gen_ann': '2.78e-02'} |
| the equality case gives the same floor dual values | **PASS** | max rel difference 1.67e-05 over years [2038, 2041, 2044, 2047, 2050] |
| the ceiling dual is zero in the equality case | **PASS** | ceiling dual keys absent = all zero (zero-suppression rule) |
| verdict: the constraint form causes no change in behavior | **PASS** | issue-6 behavior check passed; floor results stand |

## Phase E — Load data integrity

These tests make sure that the load inputs were not corrupted. The output load must be identical in all 25 cases. The repository load files must be complete and correct.

| Test | Result | Data |
|---|---|---|
| the exogenous load data is the same in all 25 cases | **PASS** | load_rt, hours, load_cat[end_use], load_cat[dist_loss] compared against smr100_eia_p50; max rel difference 0.00e+00 (load_rt, smr100_eia_p05) |
| the endogenous load parts differ only a little between cases | **INFO** | max rel difference of national totals vs smr100_eia_p50: {'load_cat[stor_charge]': 0.0423, 'load_cat[h2_prod]': 0.7131, 'load_cat[trans_loss]': 0.0488, 'load_stress': 0.0107} (these parts move with each case's solutio... |
| no load is dropped after 2025 | **PASS** | historical 2010-2023 artifact 2.96 TWh, case spread 0.0 MWh (case-invariant) |
| the demand input file is complete and correct | **PASS** | 48 states x years 2010-2050; multiplier range [0.763, 2.785] |
| the hourly load profiles are complete and correct | **PASS** | demand_EER2025_IRAlow.h5 + demand_historic.h5: 2021: 48 states x 131400 h, min 144, max 87645; 2025: 48 states x 131400 h, min 159, max 94543; 2030: 48 states x 131400 h, min 211, max 104083 ... |
| the output load agrees with the old pilot runs on the shared years | **PASS** | 1170 shared (region, year) points; max rel difference 0.00e+00 |
| the output load grows like the demand scenario | **INFO** | national load 2026->2050 x1.52; demand multiplier mean x1.39 (busbar load also moves with electrification and losses) |
| generation covers the load in every model year | **INFO** | generation / busbar load range [1.007, 1.008] (trade, storage, and losses cause small deviations from 1) |

## Phase F — Cross-case checks and unexpected values

These tests compare the cases against each other. They also scan all data for bad values.

| Test | Result | Data |
|---|---|---|
| the dual values do not cross between p05, p50, and p95 (all 6 schedules) | **PASS** | p95 >= p50 >= p05 in every year of every schedule |
| the objective values are in the correct order (p05 <= p50 <= p95) | **PASS** | a more expensive world always costs more, all 6 schedules |
| no data value is NaN or infinite in any file | **PASS** | all 209 keys x 25 files scanned |
| no negative values occur where values must not be negative | **PASS** | checked ['cap', 'cap_nat', 'load_rt', 'stor_in', 'stor_out', 'curt_ann', 'hours'] |
| the nuclear build and generation data is not negative | **PASS** | cap_new_ann and gen_ann nuclear rows >= 0, all 25 cases (storage charging and upgrades make some non-nuclear rows negative; this is a normal convention) |
| the national totals equal the sum of the regional data | **PASS** | cap, gen_ann, cap_new_ann, ret_ann; all 25 cases within 1e-3 |
| dual decay shape by case (bridge hypothesis, first look) | **INFO** | peak year + end/peak ratio: {'smr100_eia_p05': {'peak_year': 2038, 'end_over_peak': 0.03}, 'smr100_eia_p50': {'peak_year': 2038, 'end_over_peak': 0.76}, 'smr100_eia_p95': {'peak_year': 2038, 'end_over_peak': 0.84}, 's... |
| dual level by schedule ambition (p50 cases) | **INFO** | {'eia': {'n_binding': 5, 'mean_dual_2024': 334356}, 'aj': {'n_binding': 10, 'mean_dual_2024': 389702}, 'iaea': {'n_binding': 10, 'mean_dual_2024': 370822}, 'mck': {'n_binding': 10, 'mean_dual_2024': 362049}, 'cop28': ... |
| large100 dual level over smr100 dual level (shared binding years) | **INFO** | mean ratio by schedule: {'eia': 1.25, 'aj': 1.29, 'iaea': 1.24, 'mck': 1.27, 'cop28': 1.23, 'eo': 1.36} |

## Files that this notebook writes

- `exports/checks_summary.csv` — the full check registry.
- `exports/duals_by_year.csv` — the dual prices for each case and year.
- `exports/overbuild_by_case.csv` — the binding and slack years for each case.
- `exports/fingerprint_errors.csv` — the capital cost comparison points.
- `exports/fin_mult_noITC_comparison.csv` — the finance multiplier comparison.
- `exports/eq_flip_comparison.csv` — the equality case comparison.
- `exports/load_invariance.csv` — the load comparison across cases.
