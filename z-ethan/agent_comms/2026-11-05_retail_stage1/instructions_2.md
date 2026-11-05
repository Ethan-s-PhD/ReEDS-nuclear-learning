# Retail stage 1, round 2: one extra read-only extract per run (while the task runs)

*From Claude on Ethan's machine, 2026-11-05. Ethan says this task is already running. This round adds one small step. It changes nothing in `instructions.md`.*

## Bottom line

1. **Do not pause, restart or reorder** the stage-1 work in progress. The `new_runs` batch keeps its priority.
2. **After the retail module has run for a run folder** (step 7 of `instructions.md`), run one read-only script on that folder.
   - Run it for each of the five stage-1 runs, as each one finishes step 7. For runs that are already past step 7, run it now.
   - Also run it for the two pilot runs, `agretail_smr100_eo_p50` and `agretail_fbR_none`. You can do those at any time.
3. **Report and commit:** add the files to your next progress or final commit, and report them in `response.md` under a new section, **O30 extract**.

## Why

Claude logged observation O30: for supply-curve technologies (`rsc_dat`), the retail module sets the historical capital cost to `rsc_dat` cost ÷ `rsc_dat` capacity. `rsc_dat` holds that cost already per MW. Ethan will decide on the review page whether that matters. To show him its size, Claude needs four things the module uses for historical plants; Ethan's machine has none of them.

## The step

From the repo root, in the `reeds` environment:

```
python z-ethan/agent_comms/2026-11-05_retail_stage1/scripts/o30_extract.py agretail_<case>
```

- **What it reads:** `runs/agretail_<case>/inputs_case/` only. It runs no model, no GAMS and no Julia, and it takes a few seconds.
- **What it writes:** four files to `results/o30/<case>/` in this folder:
  - `o30_df_capex_init.csv`: the module's historical builds and capital cost, copied unchanged;
  - `o30_retail_eval_period.csv` and `o30_retail_depreciation_sch.csv`: the module's evaluation periods and depreciation schedules;
  - `o30_rsc_dat.csv`: the `rsc_dat` rows of `inputs.gdx` for the technologies in the first file.
- **Missing file:** if `df_capex_init.csv` does not exist yet for a run, its step 7 has not run. Run the script after step 7.
- **Test:** Claude tested the script on a scratch copy of a local Utah run, where it wrote all four files.

## Report

In `response.md`, add a section **O30 extract**. For each of the 7 runs, give:
- the exit code;
- the row count of each of the four files;
- the MD5 of `o30_df_capex_init.csv`.

No file here should be over 20 MB. If one is, leave it out and name it.
