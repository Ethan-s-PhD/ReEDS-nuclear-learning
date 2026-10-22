# ReEDS input tables read by the analysis

These files are small, frozen slices of ReEDS inputs that no notebook can rebuild from the fork's
`inputs/` folder alone. A notebook reads them through `nlpaper.paths.DATA / "reeds_inputs"`.
The run `utshake_ut_learn` is a local ReEDS shakedown run (casefile `cases_utshakedown.csv`,
Utah only). ReEDS produced it on 2026-07-31 from fork commit `a0c5ea946a163731a9ca32d6bf04eb3bc9b48325`
(branch `nuclear-learning`; the published fork state is commit `03ebfab`). The run folder itself is
not part of this repository.

| File | Source | Read by |
|---|---|---|
| `crf.csv` | `runs/utshake_ut_learn/inputs_case/crf.csv`, copied as-is. ReEDS's capital recovery factor by year; the 2026+ value 0.06773 is the 30-year factor at the post-2026 real discount rate. | 03a (QA of the 1/crf identity) |
| `utshake_hmap_myr.csv` | `runs/utshake_ut_learn/inputs_case/rep/hmap_myr.csv`, columns `*timestamp` and `h` only (8,760 rows, weather year 2012). Maps each hour to its representative time slice `h`. | 03a (QA-A) |
| `utshake_outage_forced_h_nuclear.csv` | `runs/utshake_ut_learn/inputs_case/rep/outage_forced_h.csv`, rows for `nuclear` and `nuclear-smr` only. | 03a (QA-A) |
| `utshake_outage_scheduled_h_nuclear.csv` | `runs/utshake_ut_learn/inputs_case/rep/outage_scheduled_h.csv`, rows for `nuclear` and `nuclear-smr` only. | 03a (QA-A) |
| `utshake_numhours.csv` | `runs/utshake_ut_learn/inputs_case/rep/numhours.csv`, copied as-is. | 03a (QA-A) |
| `temperature_state_hour_counts.csv` | ReEDS `inputs/profiles_temperature/temperature_state.h5` (remote file `temperature_state_19390491.h5`, 47.6 MB, not in git). Processed exactly as `reeds/io.py::get_temperatures` does for the 15 resource-adequacy weather years (2007–2013, 2016–2023): UTC converted to `Etc/GMT+6`, rounded to whole °C, 31 December dropped in leap years (15 × 8,760 hours × 48 states). Then reduced to the number of hours per (state, calendar month, whole-degree temperature). The annual and monthly outage means that notebook 03a computes depend on the hourly panel only through these counts; the national mean availability reproduces the hourly computation bit for bit. | 03a (N1) |
| `temperature_ut_2012_hourly.csv` | The same processed panel, Utah column, weather year 2012 only (8,760 hours, local time `Etc/GMT+6`). | 03a (QA-A) |
| `budget_parity_context.csv` | `z-ethan/itc_feedback/budget_parity_context.csv`, copied as-is (30 rows: worlds `aj`, `mck`, `eo` × their rate years). The design record that placed the minus-probe ladder on 2026-08-19. Per rate year it gives the headline rate `i_head` (t09 `i_model_headline`, 3 decimals), the overshoot `ov_t` of the uniform rate over the build-weighted regional need (the t13 convention, from the base mandate runs), the *monetized-parity rate* `i_par = i_head / ov_t` (the uniform rate at which the total monetized credit across builds equals the sum of the shadow-price-valued gaps) and its cut `cut_par`, and the fiscal companion `i_fiscal = i_par × 0.9`. Notebook 09 asserts that `i_head` still equals the current t09 headline. | 09 (r01 ladder placement) |
