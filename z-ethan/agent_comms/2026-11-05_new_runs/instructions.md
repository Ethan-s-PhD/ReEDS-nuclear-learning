# New paper-AG runs (RUN-1, RUN-3, stage-2b, P05 screening): instructions for the lab agent

*From Claude on Ethan's machine, 2026-11-05. Ethan asked for this hand-off. Read `../README.md` first; its rules apply to this task.*

## Bottom line

1. Launch the 23 active cases of `cases_nuclearlearning_ag.csv`, three at a time. Ethan chose that compute route on 2026-11-04 (decision D4).
2. Watch the runs, and push a progress update in `response.md` each time a group of runs finishes.
3. When every run has finished:
   - run the checks in step 5;
   - copy each `outputs.h5` into one collection folder, for Ethan to carry to his machine;
   - push the final `response.md`.

The h5 files do not go through git.

## The runs

The casefile and its input files came in commits 25f71ea and 12c893c. Five more cases are in the casefile, but `ignore = 1` turns them off; do not run them.

| Group | Cases (`ignore = 0`) | What each run changes | Decided |
|---|---|---|---|
| RUN-3 | `recfix_fbR_none`, `recfix_smr100_{eia,aj,iaea,mck,cop28,eo}_p50` (7) and the controls `recctl_fbR_none`, `recctl_smr100_eo_p50` (2) | The source run with `GSw_RECExportFix` = 1 (fix) or 0 (control). The fix removes the double count of REC exports in `eq_REC_Requirement`. A REC is a renewable energy credit. | D8, 2026-11-04 |
| RUN-1 | `run1_smr100_{eia,aj,iaea,mck,cop28,eo}_p50_grow` (6) | Solve years run to 2055, and the SMR mandate keeps growing after 2050 at its 2041–2050 pace (`*_smr_grow` mandate files). | D3, 2026-11-04 |
| Stage-2b no-mandate | `nomand_fbR_none_{gaslo,gashi,demhi,relo,rehi,translim}` (6) | The no-mandate baseline `fbR_none` under each of six market conditions. | review page, 2026-11-04 |
| P05 screening | `p05base_eia_p05`, `p05base_cop28_p05_co2cap` (2) | Learning on, no mandate and no nuclear ITC, with the P05 plant characteristics; the second run is under the national CO2 cap. | item 14 and amendment A19, 2026-11-04 |

That is 23 runs. Each run solves 2010–2050, or 2010–2055 for RUN-1.

## Rules for this task

- **Run three at a time** (`-r 3`). Do not raise or lower that number. If the machine cannot hold three runs (step 1), report it and ask.
- **Order.** Run the cases in the casefile's column order, as `runreeds.py` does by default, unless Ethan gives another order in person.
- **A failed run.** Do not relaunch it, edit it or delete its folder. Report its last 50 `gamslog.txt` lines and continue with the others.
- **Do not edit** any casefile, input file or ReEDS code. Do not delete anything.
- **The retail pilot** (`../2026-11-05_retail_pilot/`) runs only when these runs leave enough memory. These runs come first.
- **Report observations only:** numbers, errors and timings (README rule 7).

## Step 0: update the checkout

1. On branch `paper-AG`, run `git pull --rebase`.
2. Record the commit hash.
3. Confirm that these files are present:
   - `cases_nuclearlearning_ag.csv`;
   - the six files `inputs/nuclear_learning/nuclear_cap_trajectory_*_smr_grow.csv`.

## Step 1: resource check

Record these numbers in `response.md`:
- total physical memory and available memory;
- the ReEDS processes already running;
- free disk space on the repo drive.

Paper 1's archived runs are about 64 MB of `outputs.h5` each, but a run folder is much larger while the run is going. Record each run folder's size when it finishes.

- **Memory.** Ethan set three runs at a time. If you have a measured peak memory for a ReEDS run on this machine, check that three such runs fit in the available memory. If they do not fit, report and ask before launching.
- **Disk.** If free disk space looks short for 23 run folders, report and ask before launching.

## Step 2: environment

- **Environment variables:** use the `reeds` conda environment, with `CONDA_DEFAULT_ENV=reeds` and `PYTHONPATH=.` (the repo root).
- **Windows:** put the environment's folders on `PATH`, or the environment's `python.exe` fails to load its DLLs.
- **Path:** GAMS must be on `PATH`. Julia must be set up for this checkout.
- **Missing `Manifest.toml`:** if `runreeds.py` stops with "Manifest.toml does not exist", check whether another ReEDS checkout on this machine has a `Manifest.toml`.
  - If it does, and its `Project.toml` is identical to this checkout's, copy that `Manifest.toml` into the repo root and record that you did. Git ignores the file.
  - If not, report and ask.

## Step 3: launch

From the repo root, run:

```
python runreeds.py -b ag -c nuclearlearning_ag -r 3
```

- Run folders are named `runs/ag_<case>/`.
- On Windows, `runreeds.py` opens one command window per running case.
- **Record:** the launch time, and for each case its start time, end time and exit state.

## Step 4: monitor and post progress

- **Check every 30 minutes or so:**
  - the last solve year reached by each running case (its `gamslog.txt`);
  - available memory;
  - any `error` lines.
- **Progress posts.** Each time a group of three runs finishes, update the progress table in `response.md`, commit it and push. That is about eight updates in all. The table has one row per case, with columns: status (queued, running, done, failed), last solve year, start time, end time and peak memory if known.
- **Memory pressure.** If available memory stays below 2 GB for more than 10 minutes, write that in `response.md`, then commit and push. Do not stop a run on your own.

## Step 5: checks when all runs have finished

Report each check as a table in `response.md`. Work only from the run folders. Money is in 2004 $ and capacity in MW, as ReEDS writes them.

| # | Check | Runs |
|---|---|---|
| N1 | Did the run finish? Report: `outputs/outputs.h5` exists; the last solve year (2055 for RUN-1, 2050 for the others); the run time; the size of the run folder. | all |
| N2 | Do the switches in `inputs_case/switches.csv` equal the casefile column? List any difference. | all |
| N3 | Which keys listed in `expected_keys.txt` are missing from `outputs.h5`? ReEDS does not write empty tables, so a missing key is a report, not a failure. | all |
| N4 | `can_exports_stress`: its total by solve year. If the key is missing, say so. | all |
| N5 | New capacity of `nuclear` and of `nuclear-smr` (from `cap_new_ivrt`), summed over regions, for each solve year. | P05 screening; stage-2b no-mandate |
| N6 | `nuclear-smr` capacity (from `cap`), summed over regions, for each solve year from 2041 on, beside the value in the case's mandate file `inputs/nuclear_learning/nuclear_cap_trajectory_<GSw_NuclearCapMandateScen>.csv` for the same year. | RUN-1 |
| N7 | Every `error` or `warning` line from each run's `gamslog.txt`. | all |

## Step 6: collect the outputs

1. Create a folder **outside** the repo, for example `<repo parent>/collected_outputs_ag/`.
2. Copy each run's `runs/ag_<case>/outputs/outputs.h5` into it as `ag_<case>_outputs.h5`. This is the naming of paper 1's archive.
3. Compute the MD5 checksum of every copied file, and write them as `results/MD5SUMS_outputs.txt` in this folder.
4. Do not move or delete the run folders.
5. Ethan carries the collection folder to his machine. Write its full path in `response.md`.

## Step 7: reply

1. Keep `response.md` in this folder current, with these sections:
   1. **Status:** running, finished, blocked or failed, in one sentence.
   2. **Resource check.**
   3. **Progress table.**
   4. **Deviations:** anything you did differently from these instructions, and why.
   5. **Checks N1–N7** (once every run has finished).
   6. **Collection folder:** its path and the number of files.
   7. **Questions for Claude.**
2. Put the check tables as CSV files in `results/`, plus `results/MD5SUMS_outputs.txt`. Do not commit h5 files, GDX files or logs over 1 MB.
3. Commit only this folder's `response.md` and `results/`. Use the message `agent_comms: new_runs - <progress|final> (lab)`. Then run `git pull --rebase` and `git push`.
4. **"Finished"** means: all 23 runs have ended (done or failed), N1–N7 are reported, and the collection folder is complete.
