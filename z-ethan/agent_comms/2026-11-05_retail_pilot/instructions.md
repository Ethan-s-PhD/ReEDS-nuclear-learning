# Retail-rate pilot: instructions for the lab agent

*From Claude on Ethan's machine, 2026-11-05. Ethan asked for this hand-off. Read `../README.md` first; its rules apply to this task.*

## Bottom line

1. Check that the lab machine has enough free memory and disk (step 1). If it does not, write `response.md` with the numbers, commit, push and stop.
2. If it does:
   - build the processed inputs (`inputs_case`) for two ReEDS cases, without a solve;
   - copy in the output tables supplied in `outputs/`;
   - run ReEDS's retail-rate module on both cases;
   - run the checks in step 7.
3. Commit and push the results and `response.md` in this folder. Claude continues from there.

## Background

Paper AG compares a nuclear-mandate run with a no-mandate baseline. The pilot computes retail electricity rates for one pair:

| Pilot case | Archived run (source of the outputs) | Source casefile and case |
|---|---|---|
| `smr100_eo_p50` | `test1_smr100_eo_p50` | `cases_nuclearlearning_smr100.csv`, `smr100_eo_p50` |
| `fbR_none` | `itcfb_fbR_none` | `cases_nuclearlearning_itcfb.csv`, `fbR_none` |

The retail-rate module is `postprocessing/retail_rate_module/retail_rate_calculations.py`. It reads two kinds of files:
- **Outputs of the finished run:** 11 output tables and one tax-credit GDX file, under `runs/<run>/outputs/`. GDX is the GAMS data format. Claude wrote these from the archived `outputs.h5` files on Ethan's machine. They are in `outputs/<pilot case>/`, and `outputs/MD5SUMS.txt` lists their checksums.
- **Inputs that ReEDS writes during preprocessing:** `runs/<run>/inputs_case/`, including `inputs.gdx`. The archive does not keep `inputs_case`, so the lab machine must rebuild it. Ethan's machine could not, because three input files (17.9 GB) must be downloaded first and the download there ran at 0.2–3 MB/s.

## Rules for this task

- **The batch runs come first.** The paper-AG runs on this machine (RUN-1, RUN-3, the stage-2b no-mandate runs, the P05 screening runs) have priority. Never stop, pause, reorder or relaunch them. If the pilot competes with them for memory, stop the pilot, not the runs.
- **Run one pilot case at a time** (`-r 1`).
- **Do not delete anything** outside `runs/agretail_*`. Do not edit any casefile, input file or ReEDS code.
- **Downloads.** Ethan approved downloading these three Zenodo files into `inputs/remote/` if they are missing. Do not download anything else.

  | File | Zenodo record | Size |
  |---|---|---|
  | `cf_upv_reference.h5` | 18826700 | 5.9 GB |
  | `cf_wind-ons_reference.h5` | 18827074 | 9.0 GB |
  | `cf_wind-ofs_reference.h5` | 18826680 | 3.1 GB |

- **Do not interpret the results.** Report numbers, errors and timings only (README rule 7). Claude computes the paper's numbers later in a registered notebook. Your numbers are pilot checks.

## Step 0: update the checkout

1. In the repo checkout on branch `paper-AG`, run `git pull --rebase`.
2. Record the commit hash.

The pull adds:
- this folder;
- `z-ethan/.gitignore` and `z-ethan/aglib/` changes;
- the pilot casefile `cases_nuclearlearning_agretail.csv` at the repo root.

It changes no input file or ReEDS code, so the runs in progress are not affected.

## Step 1: resource check (go or no-go)

Record these numbers in `response.md`:
1. Total physical memory, and **available** memory now (Windows: `Get-CimInstance Win32_OperatingSystem`, `FreePhysicalMemory`; Linux: `free -g`, column "available").
2. The ReEDS processes running now (python, gams, julia), with each one's memory.
3. Free disk space on the drive that holds the repo.
4. Which of the three files above are already in `inputs/remote/`. Their names carry the record id, for example `cf_upv_reference_18826700.h5`.

**Go rule.** Continue only when both conditions hold:
- **Memory:** available memory is at least 16 GB, with the batch runs at their usual load.
- **Disk:** free disk is at least 10 GB plus the size of any of the three files that are missing.

Claude set the 16 GB threshold provisionally; nobody has measured the pilot's memory use.

- If the rule fails and a batch of runs will finish soon, you may wait for it and check again. Record each check.
- Otherwise write `response.md` with status **blocked**, then commit, push and stop.

**Stop rule while the pilot runs.** Sample the available memory every 60 s. If it falls below 4 GB, stop the pilot process (never a batch run) and report it.

## Step 2: environment

Use the `reeds` conda environment, with `CONDA_DEFAULT_ENV=reeds` and `PYTHONPATH=.` (the repo root). On Windows, put the environment's folders on `PATH`: run `conda activate reeds`, or prepend `<env>`, `<env>\Library\bin` and `<env>\Scripts`. A bare `python.exe` from the environment fails to load its DLLs. GAMS must be on `PATH`.

## Step 3: check the casefile

From the repo root, run:

```
python z-ethan/agent_comms/2026-11-05_retail_pilot/scripts/build_retail_cases.py
```

- It rebuilds `cases_nuclearlearning_agretail.csv` from the two source casefiles, adding `input_processing_only = 1`, and asserts that nothing else changed.
- Then `git diff --stat cases_nuclearlearning_agretail.csv` must show no change.
- If either check fails, stop and report.

## Step 4: input processing (no solve)

From the repo root, run:

```
python runreeds.py -b agretail -c nuclearlearning_agretail -r 1
```

- **What it does:** ReEDS creates `runs/agretail_smr100_eo_p50/` and `runs/agretail_fbR_none/`, downloads any missing remote files, runs the input-processing scripts and stops. It stops because `input_processing_only = 1`; it does not compile or solve the model.
- **Record:** start and end times, the exit code, and the peak memory of the input-processing python process.
- **Check:** each run folder has `inputs_case/` and `inputs_case/inputs_0.gdx`. `gamslog.txt` shows no error.

## Step 5: build `inputs.gdx` (model setup, no solve)

GAMS writes `inputs_case/inputs.gdx` when it compiles the model. The retail module reads three parameters from it: `cost_cap`, `cost_cap_energy` and `cost_cap_mult`.

For each run folder:
1. Open its call script: `call_agretail_<case>.bat` on Windows, `.sh` on Linux.
2. Find the one line that starts `gams` and names `a_createmodel.gms`. It sits under the comment "Compile model", after the `goto:eof` (or `exit`) that ended step 4.
3. Run that line exactly as written. Run it from the run folder, because the script runs `cd <casedir>` first, and use the same environment.
4. Do not run any later line: those solve the model.

**Check:** `inputs_case/inputs.gdx` exists, and `lstfiles/1_Inputs.lst` reports no compilation error. Record the time and the peak memory.

## Step 6: outputs and the retail module

For each pilot case:
1. Verify the supplied files: from this folder, run `md5sum -c outputs/MD5SUMS.txt`. On Windows, compare `Get-FileHash -Algorithm MD5`. Every file must match.
2. Copy `outputs/<case>/`, including `tc_phaseout_data/`, into `runs/agretail_<case>/outputs/`.
3. From `postprocessing/retail_rate_module/`, run:

   ```
   python retail_rate_calculations.py agretail_<case>
   ```

The module writes `runs/agretail_<case>/outputs/retail/`. It writes `retail_rate_components.csv` first, then the plots.
- `nuclear-smr` is not in the module's `map_i_to_tech.csv`. Its README says the plot step fails when a built technology is missing from that map.
- If only the plot step fails, record the error and continue: the CSVs are what matter.
- If `retail_rate_components.csv` is missing, stop and report the traceback.

## Step 7: checks to report

Give each check as a table in `response.md`. Money is in the module's units (2004 $, as written).

| # | Check |
|---|---|
| E1 | For each case: does `retail_rate_components.csv` exist? Give its row count, its columns, the number of states and the years. |
| E2 | For each case: do the switches in `inputs_case/switches.csv` equal the casefile column, apart from `input_processing_only`? List any difference. |
| E3 | For years up to 2023: the largest absolute difference between the two cases in each column of `retail_rate_components.csv`, summed over states. |
| E4 | `retail_load`: the largest absolute difference between the cases over all state-years. |
| E5 | National retail rate by year for both cases, from `retail_rate_USA_centsperkWh_allcomponents.csv` (or `retail_rate_USA_centsperkWh.csv`) as written, and the difference (`smr100_eo_p50` − `fbR_none`) for each solve year from 2026 to 2050. |
| E6 | Every warning and error line from steps 4–6 (the `gamslog.txt` tail, the module's console output), and how long each step took. |

## Step 8: reply

1. Write `response.md` in this folder with these sections:
   1. **Status:** ready, blocked or failed, in one sentence.
   2. **Resource check:** the step-1 numbers, plus the peak memory and run time of steps 4–6.
   3. **Steps run:** commands, times and exit codes.
   4. **Deviations:** anything you did differently from these instructions, and why.
   5. **Checks E1–E6.**
   6. **Questions for Claude.**
2. Put these files in `results/<case>/`:
   - the `outputs/retail/*.csv` files;
   - `inputs_case/switches.csv`;
   - the last 200 lines of `gamslog.txt`.

   Do not commit `inputs.gdx`, h5 files or plots. If any one file is larger than 20 MB, leave it out and name it in `response.md`.
3. Commit only this folder's `response.md` and `results/`. Use the message `agent_comms: retail_pilot - response (lab)`. Then run `git pull --rebase` and `git push`.
4. **"Ready"** means: both cases have `retail_rate_components.csv`, and E1–E6 are reported with no unexplained error. Commit and push in every outcome (ready, blocked or failed), so that Claude can read the status.
