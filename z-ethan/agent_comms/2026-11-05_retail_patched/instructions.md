# Retail module rerun from a patched copy: instructions for the lab agent

*From Claude on Ethan's machine, 2026-11-05. Read `../README.md` first; its rules apply to this task. Ethan chose this rerun on the review page (card `retail-capex`).*

## Bottom line

1. **Priority.** The `new_runs` batch comes first. Never stop, pause or reorder its runs. This task is light: about 20 s and under 1 GB per run.
2. **Build a patched copy** of the retail-rate module with one script. The repo's module stays unedited.
3. **Rerun the copy** for the 7 run folders from the retail tasks. Keep each run's first results as `outputs/retail_unpatched/`.
4. Report checks P1–P4, then commit and push `response.md` and `results/`.

## Why

Claude logged observation O33 from your `retail_stage1` results. The module looks up each generator's evaluation period by exact technology name. The run's tables write `nuclear-smr`, while `retail_eval_period` writes `Nuclear-SMR`. The module then fills unmatched rows with 20 years through `df[col].fillna(20, inplace=True)`. Under pandas 3 that call changes nothing: these are the `ChainedAssignmentError` lines you logged at `retail_rate_calculations.py:883`, `:889`, `:926` and `:930`. Rows with no period drop out of the rate. That includes all SMR capital.

The patch makes two changes:
- names match ignoring case;
- the fills are assigned.

It also fixes the two other chained assignments you logged, at `ferc_distadmin.py:383` and `:449`. `reference/patch_expected.diff` shows every changed line.

Claude tested the patched copy on a local Utah run:
- exit 0, and no `ChainedAssignmentError` line;
- the only row still without a period was an upgrade (`CoalOldScr_coal-CCS_mod`), which takes the 20-year default;
- the patched generation depreciation equals an independent rebuild outside the module to 2.4e-7 $.

## The runs

| Run folder | From |
|---|---|
| `runs/agretail_smr100_eo_p50` | retail pilot |
| `runs/agretail_fbR_none` | retail pilot |
| `runs/agretail_smr100_eia_p50`, `_aj_p50`, `_iaea_p50`, `_mck_p50`, `_cop28_p50` | `retail_stage1` |

Each folder already has its `inputs_case/`, its copied `outputs/` tables and the first module results in `outputs/retail/`. Nothing is rebuilt: no input processing, no GAMS, no Julia.

## Rules for this task

- **The `new_runs` batch comes first** (above).
- **Do not edit** any file in `postprocessing/`, any casefile, input file, `Manifest.toml` or ReEDS code. The patch goes into the copy only.
- **Do not delete anything** outside `runs/agretail_*`.
- **Downloads.** None.
- **Report observations only:** numbers, errors and timings (README rule 7).

## Step 0: update the checkout

1. On branch `paper-AG`, run `git pull --rebase`.
2. Record the commit hash.
3. Record the `new_runs` processes that are running, and the available memory.

## Step 1: environment

Use the same environment as in the retail tasks: the `reeds` env on `PATH`, with `CONDA_DEFAULT_ENV=reeds` and `PYTHONPATH=.`. Record `python -c "import pandas; print(pandas.__version__)"`.

## Step 2: build the patched copy

From the repo root:

```
python z-ethan/agent_comms/2026-11-05_retail_patched/scripts/make_patched_module.py
```

- **What it does:**
  - checks the MD5s of the two original files;
  - copies `postprocessing/retail_rate_module/` to `runs/agretail_module_patch/`, replacing any earlier copy;
  - applies the patches;
  - writes `results/patch.diff` in this folder.
- **Pass:**
  - it prints `6 patches applied` and `2 patches applied`, and exits 0;
  - `results/patch.diff` has the MD5 `9410f18ba21724cf065e11d58f6acc22`, the same as `reference/patch_expected.diff`.
- **If an MD5 assertion or a patch count fails,** stop and report. Do not edit the script.

## Step 3: rerun the module, one run at a time

For each of the 7 run folders:

1. Rename `runs/agretail_<case>/outputs/retail/` to `runs/agretail_<case>/outputs/retail_unpatched/`. If `retail_unpatched/` already exists, stop and report.
2. From `runs/agretail_module_patch/`, run `python retail_rate_calculations.py agretail_<case>`.
   - The copy sits at the same depth below the repo root as the original. It therefore finds `reeds` and `runs/agretail_<case>/` the same way.
   - It writes a new `outputs/retail/`, which also holds `agpatch_eval_unmatched.csv`.
3. Record the time and the exit code.

## Step 4: checks

Report each check as a table, and put it in `results/` as a CSV file.

| # | Check |
|---|---|
| P1 | Step 2: the printed lines, and the MD5 of `results/patch.diff`. Also the pandas version from step 1. |
| P2 | For each run: exit code, time, and every warning and error line from step 3 (console and the lines step 3 added to `gamslog.txt`), counted by source line. The count of `ChainedAssignmentError` lines should be 0. |
| P3 | For each run, `agpatch_eval_unmatched.csv` grouped by `src` and `i`: rows and the sum of `capex`. These are the rows that still have no period and get the 20-year default. |
| P4 | National retail rate by year, 2010–2050, from `retail_rate_USA_centsperkWh.csv` (`source = ReEDS`): the patched rate, the unpatched rate (`outputs/retail_unpatched/`), and patched − unpatched, for each run. |

## Step 5: reply

1. Write `response.md` in this folder with these sections:
   1. **Status:** ready, partly ready (name the runs), blocked or failed, in one sentence.
   2. **Steps run:** commands, times and exit codes.
   3. **Deviations.**
   4. **Checks P1–P4.**
   5. **Questions for Claude.**
2. Put these files in `results/<case>/` for each run:
   - `retail_rate_components.csv`, `retail_rate_USA_centsperkWh.csv`, `retail_rate_USA_centsperkWh_allcomponents.csv` and `agpatch_eval_unmatched.csv` from the new `outputs/retail/`;
   - no plots.

   Here `<case>` is the run name without `agretail_`, for example `smr100_eo_p50` or `fbR_none`. Do not commit any file over 20 MB.
3. Commit only this folder's `response.md` and `results/`. Use the message `agent_comms: retail_patched - response (lab)`, then run `git pull --rebase` and `git push`.
