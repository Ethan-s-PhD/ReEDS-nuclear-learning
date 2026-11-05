# Retail rates for the other five stage-1 runs: instructions for the lab agent

*From Claude on Ethan's machine, 2026-11-05. Read `../README.md` first; its rules apply to this task. This task repeats the retail pilot (`../2026-11-05_retail_pilot/`) for five more cases, with the steps that worked in its round 3.*

## Bottom line

1. **Priority.** The `new_runs` batch comes first. Run this task only while there is memory to spare for it (step 1).
2. **For each of the five cases:**
   - build `inputs_case`;
   - compile the model;
   - run the 2010 block;
   - copy in the supplied output tables;
   - run the retail module.
3. Report the checks, then commit and push `response.md` and `results/`.

## The cases

The approved plan (Phase 6, step 3) extends the pilot to the six stage-1 P50 runs once the pilot works. The pilot covered `smr100_eo_p50` and the baseline `fbR_none`. This task covers the other five:

| Case | Archived run (source of the outputs) | Source casefile and case |
|---|---|---|
| `smr100_eia_p50` | `test1_smr100_eia_p50` | `cases_nuclearlearning_smr100.csv`, `smr100_eia_p50` |
| `smr100_aj_p50` | `test1_smr100_aj_p50` | same file, `smr100_aj_p50` |
| `smr100_iaea_p50` | `test1_smr100_iaea_p50` | same file, `smr100_iaea_p50` |
| `smr100_mck_p50` | `test1_smr100_mck_p50` | same file, `smr100_mck_p50` |
| `smr100_cop28_p50` | `test1_smr100_cop28_p50` | same file, `smr100_cop28_p50` |

- **Casefile:** `cases_nuclearlearning_agretail1.csv` at the repo root. Each case is its source switches plus `input_processing_only = 1`.
- **Supplied outputs:** `outputs/<case>/` holds the 11 output tables and `tc_phaseout_data/tc_phaseout_mult_2050.gdx`. `outputs/MD5SUMS.txt` lists 60 files. Claude wrote them from the archived h5 files with `scripts/dump_outputs.py`.

## Rules for this task

- **The `new_runs` batch comes first.** Never stop, pause or reorder its runs. If this task competes with them for memory, pause this task, not the runs.
- **One case at a time** (`-r 1`).
- **Do not delete anything** outside `runs/agretail_*`. Do not edit any casefile, input file, `Manifest.toml` or ReEDS code.
- **Downloads.** None. The 7 remote files are already in `inputs/remote/`. If a step tries to download, stop it and report.
- **Report observations only:** numbers, errors and timings (README rule 7).

## Step 0: update the checkout

1. On branch `paper-AG`, run `git pull --rebase`.
2. Record the commit hash.

## Step 1: resource check

1. Record:
   - the available memory;
   - the `new_runs` processes running and their memory;
   - the free disk space.
2. **Go rule:** available memory is at least 20 GB with the `new_runs` batch at its current load, and free disk is at least 10 GB.
   - In the pilot, input processing peaked at 13 GB for the process tree, and `check_inputs.py` in the 2010 block reached 11.6 GB.
   - If the rule fails, wait, and check again after the next `new_runs` group finishes. Record each check.
3. **Stop rule:** sample the available memory every 60 s. If it falls below 4 GB, stop this task's process (never a batch run) and report it.

## Step 2: environment

Use the same environment as in the pilot (`instructions.md` step 2 there): the `reeds` env on `PATH`, with `CONDA_DEFAULT_ENV=reeds` and `PYTHONPATH=.`.

## Step 3: check the casefile

```
python z-ethan/agent_comms/2026-11-05_retail_stage1/scripts/build_retail_cases.py
```

1. The script must print `5 cases; ... verified`.
2. If it rewrote the line endings, restore the committed bytes with `git checkout -- cases_nuclearlearning_agretail1.csv`, as in pilot round 1, deviation 3.
3. `git diff --stat cases_nuclearlearning_agretail1.csv` must then show no change.

## Step 4: input processing

```
python runreeds.py -b agretail -c nuclearlearning_agretail1 -r 1
```

- This creates `runs/agretail_smr100_<t>_p50/` for each case, and each takes about 27 minutes.
- **Check:**
  - `inputs_case/inputs_0.gdx` exists;
  - `gamslog.txt` has no `Traceback`.

## Step 5: compile the model, then run the 2010 block

For each run folder, use the method of pilot round 1, deviation 4: a temporary `.cmd` file that `cd`s to the run folder and then runs lines copied verbatim from `call_agretail_<case>.bat`.

1. Run the `gams ... a_createmodel.gms` line under "Compile model".
2. Run every command line of the `Year: 2010` block, up to the next `Year:` comment. Run nothing after that comment.
   - In the pilot, this block held `1_tc_phaseout.py`, `solve.py`, `check_inputs.py` and `diagnostic_plots.py`.
   - `diagnostic_plots.py` ended with an `AttributeError` traceback and exit 0 in both pilot cases. If it does so here, record it and continue.

**Check:**
- the 2010 solve's lines in `lstfiles/agretail_<case>_2010i0.lst`: `SOLVER STATUS 1`, `MODEL STATUS 1 Optimal`, and the objective value;
- `check_inputs.py` reports no failed check.

## Step 6: confirm the multipliers

For each run, from the repo root:

```
python z-ethan/agent_comms/2026-11-05_retail_stage1/scripts/diag_hydnd.py agretail_<case>
```

This is the pilot's diagnostic script. It writes five CSV files into this folder's `results/<case>/`.

1. **Pass:**
   - `cost_cap_fin_mult_out` has more than 0 rows in `D2`;
   - `D5` lists no technology other than `pumped-hydro`. An empty `D5` passes; it was empty in pilot round 3.
2. If the check fails for a case, skip step 7 for that case and report.

## Step 7: outputs and the retail module

For each case:
1. From this folder, run `md5sum -c outputs/MD5SUMS.txt` (on Windows, `Get-FileHash -Algorithm MD5`). All 60 files must match.
2. Copy `outputs/<case>/` into `runs/agretail_<case>/outputs/`.
3. From `postprocessing/retail_rate_module/`, run `python retail_rate_calculations.py agretail_<case>`.

## Step 8: checks

Money is in the module's units as written. Report each check as a table, and put it in `results/` as a CSV file.

| # | Check |
|---|---|
| F1 | For each case, `retail_rate_components.csv`: rows, columns, states and years. Are its columns the same as the pilot's? |
| F2 | For each case: the switches in `inputs_case/switches.csv` against the casefile column, apart from `input_processing_only`. |
| F3 | For years up to 2023, each case against the pilot's `fbR_none` (`../2026-11-05_retail_pilot/results/fbR_none/retail_rate_components.csv`): for each column with a nonzero difference, the largest absolute difference of the state sum, its year, and the number of years with a nonzero difference. This is the method of pilot check E3. |
| F4 | National retail rate by year, 2010–2050, from `retail_rate_USA_centsperkWh.csv` (`source = ReEDS`, as written). Give each case's rate and its difference from the pilot's `fbR_none` file, `../2026-11-05_retail_pilot/results/fbR_none/retail_rate_USA_centsperkWh.csv`. |
| F5 | Every warning and error line from steps 4–7. Give a count by source line for repeated pandas warnings, as in pilot round 3 check E6. Also give the run time and peak memory of each step. |

## Step 9: reply

1. Write `response.md` in this folder with these sections:
   1. **Status:** ready, partly ready (name the cases), blocked or failed, in one sentence.
   2. **Resource check.**
   3. **Steps run:** commands, times and exit codes.
   4. **Deviations.**
   5. **Checks F1–F5.**
   6. **Questions for Claude.**
2. Put these files in `results/<case>/`:
   - the `outputs/retail/*.csv` files;
   - `inputs_case/switches.csv`;
   - the diagnostic CSV files;
   - the last 200 lines of `gamslog.txt`.

   Do not commit `inputs.gdx`, h5 files or plots, or any file over 20 MB.
3. Commit only this folder's `response.md` and `results/`. Use the message `agent_comms: retail_stage1 - response (lab)`, then run `git pull --rebase` and `git push`.
4. You may push a progress `response.md` after each case (message `agent_comms: retail_stage1 - progress (lab)`).
