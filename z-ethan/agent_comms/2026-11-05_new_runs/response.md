# New paper-AG runs: response from the lab agent

*Lab machine `ChemE-PowellUSI`, 2026-11-06. Reply to `instructions.md` and `instructions_2.md`. Checkout: commit `361eacae207df9f232dba259e9822bb4cdde6c62` on `paper-AG` after `git pull --rebase` (09:52).*

## 1. Status

**Running; the batch changes from `-r 3` to `-r 2` on Ethan's decision (deviation 4):**
- The `-r 3` batch was launched at 09:58:20 on 2026-11-06 (Ethan gave the start in person).
- `recfix_smr100_aj_p50` failed at 10:46:19 in the 2020 solve with a Julia `OutOfMemoryError` in `run_pras.jl`, while available memory was 0.01 GB (section 3b).
- `recfix_fbR_none` hung in its 2020 PRAS step; on Ethan's decision it was stopped at 12:45:00.
- `recfix_smr100_eia_p50` finished at 05:25:43 and `recfix_smr100_iaea_p50` at 05:55:24 on 2026-11-07, each after about 19.2–19.4 h. Both have `outputs/outputs.h5`.
- The `-r 2` batch started at 05:55:43 on 2026-11-07 with the other 21 cases, beginning with the reruns of `recfix_fbR_none` and `recfix_smr100_aj_p50`.
- **RUN-3 group finished: 9 of 23 done** as of 08:35 on 2026-11-10: all 7 `recfix_*` runs and both `recctl_*` runs. All have `outputs/outputs.h5` and last solve year 2050. The 7 `-r 2` runs took 18.39–19.62 h each. `run1_smr100_aj_p50_grow` started at 08:33:12 on 11-10.
- **`run1_smr100_eia_p50_grow` failed at the end (section 3b):** all solve years through 2055 and `report.gms` completed (13:57:04 on 11-10), but there is no `outputs/outputs.h5`. `report_dump.py` wrote no line to `gamslog.txt`. The batch window closed at 13:59:54 after 22.87 h. The batch then started `run1_smr100_iaea_p50_grow` at 14:00:12. The folder stays in `runs/` on `C:`, untouched. On Ethan's decision, `report_dump.py` was run on a copy on 11-11 (deviation 7).
- **`run1_smr100_aj_p50_grow` done** at 06:59:58 on 11-11 after 22.45 h, with `outputs.h5` (72.9 MB); moved to `E:` at 07:01:39.
- **`run1_smr100_iaea_p50_grow` failed at 06:26:07 on 11-11, in its 2044 PRAS step (section 3b):** `run_pras.jl returned code 541541187`, 24 s after a Windows low-virtual-memory event. The folder stays in `runs/` on `C:`, untouched.
- **Now (13:05 on 11-11):** 11 of 23 have an `outputs.h5` in the collection folder: 10 done in place, plus `run1_smr100_eia_p50_grow` from the copy (deviation 7). 2 running (`run1_smr100_mck_p50_grow` since 06:26:29, `run1_smr100_cop28_p50_grow` since 07:00:10), 9 queued, and the `run1_smr100_iaea_p50_grow` rerun queued last (deviations 8 and 9).
- **Batch launcher closed at about 12:54 on 11-11 (deviation 9):** the minimized PowerShell window that ran `runreeds.py` closed; `runreeds.py` had just logged `ag_run1_smr100_cop28_p50_grow has finished` (while that case's window kept running) and created `runs/ag_run1_smr100_eo_p50_grow/` with empty `autocode/` and `inputs_case/` at 12:54:50. No System or Application event between 12:52 and 12:57. At the same time Firefox, 3 of 4 idle Julia 1.13 sessions (started 10-21 to 11-02) and 22 of 38 VS Code processes were closed. The two running case windows were not affected. On Ethan's decision the queue was restarted at 12:58:52 with a script (deviation 9).
- **Commit charge (deviation 3):** from 10:45 to 12:54 on 11-11, free commit was 5.27–78 GB (lowest 5.27 GB at 10:55:32 and 7.06 GB at 11:35:29, each during one `run_pras.jl` step while the other case ran GAMS). Committed bytes exceeded the sum of process private bytes by a constant 120.4 GB (20 samples, 11:51:59–11:56:27); kernel pools were 7.3 GB; uptime since 10-14. After the closures above, at 12:57:16: committed 141.1 GB, process private 125.8 GB, difference 15.3 GB, free commit 161 GB. Estimated end of the last run: about 07:35 on 11-16, from mean run times (18.93 h for endyear 2050, 22.45 h for 2055).
- **Memory sampler:** `monitor.ps1` wrote no sample after 01:20:48 on 11-11, while its process stayed alive; it was restarted at 10:44. From 10:45 a second sampler writes commit limit, free commit and free RAM every 30 s to `commit_samples.csv` (same folder).
- **Memory at `-r 2`:** the lowest available memory in the 30-s samples since 05:55:43 on 11-07 is 17.37 GB (19:10:30 on 11-08); no sample is below 2 GB. Peak tree memory per run is 91.74–107.21 GB working set and 92.59–116.78 GB private (section 3); the highest is `recfix_smr100_eo_p50`, reached in its 2047 solve.
- **Disk:** a finished folder is about 5.85 GB. On Ethan's decision (deviation 5), each finished folder is moved to the external drive `E:\ag_new_runs\` after its checks and `outputs.h5` copy. The first 6 were moved between 09:50 and 09:57 on 11-09. From 09:58 a loop (`autopost.sh`, every 120 s) runs the checks, copy and move for each case that has ended; it moved `recfix_smr100_eo_p50` at 14:06 and `recctl_fbR_none` at 15:08 on 11-09, and `recctl_smr100_eo_p50` at 08:35 on 11-10. Free space at 08:35 on 11-10: `C:` 109 GB, `E:` 327 GB.
- **`C:` free space and `pagefile.sys`:** in the 30-min checks, free space on `C:` fell below 80 GB several times and came back to about 100 GB within the next check or two: 78 GB (13:02, 11-09), 71 GB (01:23, 11-10), 77 GB (02:56), 69 GB (03:27), 71 GB (04:28), 61 GB (05:30), 76 GB (07:33), 70 GB (08:03). `C:\pagefile.sys` was 58.3 GB at 12:44 on 11-09, 69.1 GB at 01:23 and 75.2 GB at 05:30 on 11-10. The two run folders on `C:` were 4.9–7.2 GB each at those times. The folder of `run1_smr100_eia_p50_grow` (endyear 2055) was 7.2 GB at 01:23 on 11-10, at solve year 2034.
- The lab agent was paused from 11:00 on 11-07 to about 09:45 on 11-09, on Ethan's instruction, until the drive was connected; the ReEDS runs kept going.

## 2. Resource check

Taken at 09:52:37, before launch.

| Item | Value |
|---|---|
| Total physical memory | 253.35 GB |
| Available memory | 199.81 GB |
| ReEDS processes already running | none (no `gams*.exe`, no ReEDS `python.exe`). Other processes: 4 `julia.exe` 1.13.0 (0.03, 0.07, 0.59, 1.12 GB working set) and Jupyter kernels of the `reeds2` env (≤ 0.05 GB each) |
| Free disk space, `C:` | 135.87 GB (863.42 GB used) |

- **Memory.** No full ReEDS run (2010–2050) has a measured peak on this machine. The measured peaks of this checkout's runs on 2026-11-05 are from input processing and the 2010 solve: 15.68 GB private / 12.98 GB working set (`runreeds.py`, `retail_pilot`), 11.57 GB (`check_inputs.py`), 10.64 GB (`hourly_repperiods.py`), `gamscmex.exe` 4.64 GB in the 2010 solve. Three runs at 15.68 GB each: 47.0 GB, against 199.81 GB available.
- **Disk.** The finished `agretail_fbR_none` folder (2010 block only) is 2.8 GB, of which `inputs_case/` is 2.5 GB and `g00files/` 283 MB. The casefile keeps the default `keep_g00_files = 0`. 23 folders at 2.8 GB: 64 GB, against 135.87 GB free.

Neither check stopped the launch. Folder sizes at the end of each run are in N1.

## 3. Progress table

As of 2026-11-11 12:59: 10 done, 10 queued, 2 running, 1 failed. Times are 2026 local time (MM-DD hh:mm:ss). Start is the first time stamp in `gamslog.txt`; end is the last write of `gamslog.txt` after the batch window closed. Last solve year is the largest year among `lstfiles/*_<year>i<iter>.lst`. Peak memory is the largest sum over the case's process tree in the 30-s samples (CSV in `results/memory_peaks.csv` at the end).

| # | Case | Status | Last solve year | Start | End | Peak memory, GB (working set / private) |
|---|---|---|---|---|---|---|
| 1 | `recfix_fbR_none` | done | 2050 | 11-07 05:57:05 | 11-08 01:06:04 | 99.25 / 101.24 |
| 2 | `recfix_smr100_eia_p50` | done | 2050 | 11-06 09:59:39 | 11-07 05:25:44 | 99.17 / 100.93 |
| 3 | `recfix_smr100_aj_p50` | done | 2050 | 11-07 05:57:05 | 11-08 00:59:22 | 91.74 / 94.40 |
| 4 | `recfix_smr100_iaea_p50` | done | 2050 | 11-06 10:46:31 | 11-07 05:55:26 | 90.85 / 92.59 |
| 5 | `recfix_smr100_mck_p50` | done | 2050 | 11-08 00:59:46 | 11-08 19:29:52 | 94.10 / 95.93 |
| 6 | `recfix_smr100_cop28_p50` | done | 2050 | 11-08 01:06:15 | 11-08 19:29:50 | 101.37 / 103.14 |
| 7 | `recfix_smr100_eo_p50` | done | 2050 | 11-08 19:30:06 | 11-09 14:05:16 | 107.21 / 116.78 |
| 8 | `recctl_fbR_none` | done | 2050 | 11-08 19:30:06 | 11-09 15:07:18 | 95.60 / 97.41 |
| 9 | `recctl_smr100_eo_p50` | done | 2050 | 11-09 14:05:33 | 11-10 08:32:52 | 92.89 / 94.64 |
| 10 | `run1_smr100_eia_p50_grow` | failed | 2055 | 11-09 15:07:34 | 11-10 13:59:54 | 101.02 / 102.80 |
| 11 | `run1_smr100_aj_p50_grow` | done | 2055 | 11-10 08:33:12 | 11-11 06:59:58 | 91.72 / 93.54 |
| 12 | `run1_smr100_iaea_p50_grow` | queued |  |  |  |  |
| 13 | `run1_smr100_mck_p50_grow` | running | 2032 | 11-11 06:26:29 |  | 86.57 / 88.37 |
| 14 | `run1_smr100_cop28_p50_grow` | running | 2031 | 11-11 07:00:10 |  | 89.27 / 91.09 |
| 15 | `run1_smr100_eo_p50_grow` | queued |  |  |  |  |
| 16 | `nomand_fbR_none_gaslo` | queued |  |  |  |  |
| 17 | `nomand_fbR_none_gashi` | queued |  |  |  |  |
| 18 | `nomand_fbR_none_demhi` | queued |  |  |  |  |
| 19 | `nomand_fbR_none_relo` | queued |  |  |  |  |
| 20 | `nomand_fbR_none_rehi` | queued |  |  |  |  |
| 21 | `nomand_fbR_none_translim` | queued |  |  |  |  |
| 22 | `p05base_eia_p05` | queued |  |  |  |  |
| 23 | `p05base_cop28_p05_co2cap` | queued |  |  |  |  |

## 3b. Failed runs and memory pressure

### `recfix_smr100_aj_p50`: failed at 10:46:19, 2020 solve

- **Error:** `run_pras.jl` for 2020i0, at `gamslog.txt` line 5230 of 5299: `ERROR: LoadError: OutOfMemoryError()`. The trace runs through `HDF5.read`, then `PRASFiles._systemmodel_core` (`read.jl:213`), then `run_pras` (`run_pras.jl:172`). The preceding lines are `Successfully exported the PRAS SystemModel to .pras file ...\handoff\PRAS\PRAS_2020i0.pras` and `Parsing PRAS System ...` at 10:45:00. Lines 5221–5232 are in `results/failed_recfix_smr100_aj_p50_gamslog_lines5221-5232.txt`.
- **`solve.py` then raised** `Exception: run_pras.jl returned code 1. Check gamslog.txt for error trace.` (`ra_calcs.py`, line 164), and the batch file stopped.
- **The last 50 lines** of `gamslog.txt` are in `results/failed_recfix_smr100_aj_p50_gamslog_tail50.txt`.
- **Earlier in the same log:** 318 lines `┌ Error: 2026-11-06 10:41:47 | MT_C,hydud,BoundsError(Float64[], (1,))` (first at line 4580), written before the PRAS export. The two runs that are still going have 265 (`recfix_smr100_eia_p50`) and 271 (`recfix_fbR_none`) such lines.
- **Per the instructions,** the run was not relaunched, edited or deleted at first. The batch continued: `recfix_smr100_iaea_p50` started at 10:46:31.
- **Later, on Ethan's decision (deviation 4):** the folder was renamed at 12:46 to `runs/ag_recfix_smr100_aj_p50_oom_20261106/` (6.1 GB, not deleted), and the case is rerun in the `-r 2` batch.

### `recfix_fbR_none`: hung in the 2020 PRAS step, stopped at 12:45:00

- **What was seen:** `gamslog.txt` was last written at 10:41:47, in the `ReEDS2PRAS` export (the last lines are `┌ Error: ... | WA_W,hydund,BoundsError(Float64[], (1,))`). The `run_pras.jl` `julia.exe` (pid 39048, started 10:40:57) held 50.13 GB working set at 12:24. Its CPU time stayed at 5245.28 s over a 20-s check at 12:25. For comparison, the 2020 `run_pras.jl` step of `recfix_smr100_eia_p50` ran 10:40:59–10:59:04.
- **Its tree** was at 79.90 GB private in the 10:45:41 sample, when available memory was 0.01 GB.
- **Action:** on Ethan's decision, I ran `taskkill /T /F` on the case's batch window (pid 42924) at 12:45:00, and `julia.exe` exited by 12:45:23. Available memory went from 111.92 to 123.37 GB.
- **The last 50 lines** of `gamslog.txt` are in `results/stopped_recfix_fbR_none_gamslog_tail50.txt`.
- **The folder** was renamed at 12:46 to `runs/ag_recfix_fbR_none_hung_20261106/` (6.1 GB, not deleted), and the case is rerun in the `-r 2` batch.

### `run1_smr100_eia_p50_grow`: no `outputs.h5`, 2026-11-10

- **Solve:** every solve year ran, through `ag_run1_smr100_eia_p50_grow_2055i0.lst`. The 2055 PRAS step ran 13:15:21–13:37:44 and ended with `No new stress periods to add, so moving to next solve year`.
- **`report.gms`:** started 13:42:09, `*** Status: Normal completion`, stopped 13:57:04 (`gamslog.txt` line 33233). It wrote `outputs/rep_ag_run1_smr100_eia_p50_grow.gdx` (120022074 bytes, 13:57).
- **`report_dump.py`:** the batch file runs `python reeds\core\terminus\report_dump.py <run folder> -c` next (line 395 of `call_ag_run1_smr100_eia_p50_grow.bat`, after `reeds\log.py`). `gamslog.txt` has no line from `report_dump.py`. The next line is `retail_rate_calculations.py | 2026-11-10 13:57:29 | INFO | Starting retail_rate_calculations.py`, 25 s after `report.gms` stopped. For comparison, in `recctl_smr100_eo_p50` the line after `Job report.gms Stop` is `report_dump.py | ... | INFO | Starting report_dump.py`, 12 s later. The batch file does not send this step's stderr to `gamslog.txt`, and the window has closed.
- **After that:** `retail_rate_calculations.py` stopped with `FileNotFoundError` on `outputs\load_cat.csv`, and `single_case_plots.py` with `FileNotFoundError` on `outputs\gen_h.csv` and `outputs\cap.csv`. The last line of `gamslog.txt` is at 13:59:54. `outputs/` has 42 files; `recctl_smr100_eo_p50` has 322.
- **Files:** the last 50 lines of `gamslog.txt` are in `results/failed_run1_smr100_eia_p50_grow_gamslog_tail50.txt`; lines 33203–33241 (around the report step) are in `results/failed_run1_smr100_eia_p50_grow_gamslog_report_step.txt`.
- **Resources at the time:** at 13:57 the 30-s samples show 146–177 GB available memory; `C:` had 102 GB free at 13:44 and 14:00.
- **Per the instructions,** the run was not relaunched, edited or deleted, and `report_dump.py` was not run again on it. The other 5 `run1_*_grow` cases have the same endyear (2055); `run1_smr100_aj_p50_grow` (at 2031) and `run1_smr100_iaea_p50_grow` (started 14:00:12) are running.
- **`report_dump.py` on a copy, 11-11 (deviation 7):** the folder was copied to `E:\ag_new_runs_diag\ag_run1_smr100_eia_p50_grow\` (2167 files, 5253031152 bytes, equal to the source) and `python reeds\core\terminus\report_dump.py <copy> -c` was run there at 10:45:05 with the batch environment, stdout and stderr captured (`C:\Users\egallup\ag_new_runs_work\diag_report_dump_stdout.txt`). Results:
  - It logged `Starting report_dump.py` and wrote `outputs/outputs.h5` (72840519 bytes, 10:45) and 322 files in `outputs/`.
  - It then exited with code 1 at 10:46:27: `TypeError: Invalid value '[1.07270508e+00 1.48327330e+01 nan ...]' for dtype 'float32'` at `reeds/results.py` line 398 (`df.loc[mask, 'inv_investment_capacity_costs'] = df.loc[mask, 'capex']`), in `calc_systemcost`, called from `report_dump.py` line 203 (`postprocess_outputs`).
  - The copy's state differs from the original at the time `report_dump.py` ran: `inputs_case/df_capex_init.csv` (written by `retail_rate_calculations.py`, which runs after `report_dump.py`) existed in the copy; in the original it was written at 13:57:31, after the step.
  - **All 10 finished runs** have the same `report_dump.py` error at the end of their own run: `FileNotFoundError: ... inputs_case\df_capex_init.csv` at `reeds/results.py` line 315, in `calc_systemcost`, from `postprocess_outputs` (32 ERROR lines each). Their `outputs.h5` is written before that point.
  - The original failure (no line at all from `report_dump.py`) was not reproduced; its error text is not available. `reeds/results.py`, `reeds/io.py`, `reeds/log.py` and `report_dump.py` were last changed on 2026-11-05 09:19:35, and the run's `report_dump.py` equals the repo's.
- **Used for the case (Ethan's decision, 11-11):** the copy's `outputs.h5` (MD5 `d54e900d4691ba47c810c567504b67b8`) is checked with N1–N7 and collected as `ag_run1_smr100_eia_p50_grow_outputs.h5`. N1, N2 and N7 read the original folder (`gamslog.txt`, `inputs_case/switches.csv`, `lstfiles/`); N3–N6 read the copy's `outputs.h5`. The original folder stays in `runs/` on `C:`, untouched; the copy stays on `E:`.

### `run1_smr100_iaea_p50_grow`: failed at 06:26:07 on 2026-11-11, 2044 PRAS step

- **Error:** `run_pras.jl 2044i0` started at 06:19:32. `gamslog.txt` has no Julia output between its `vvv` and `^^^` markers. Then `solve.py` raised `Exception: run_pras.jl returned code 541541187. Check gamslog.txt for error trace.` (`ra_calcs.py`, line 164). Last solve year 2044 (`_2044i0.lst`). The last 50 lines are in `results/failed_run1_smr100_iaea_p50_grow_gamslog_tail50.txt`.
- **Windows System log, event 2004 (Resource-Exhaustion-Detector), 06:25:43:** "Windows successfully diagnosed a low virtual memory condition. The following programs consumed the most virtual memory: julia.exe (27172) consumed 98870444032 bytes, julia.exe (46624) consumed 98388418560 bytes, and Code.exe (27968) consumed 3991314432 bytes." The only other event 2004 since 11-06 is at 10:46:11 on 11-06 (the `recfix_smr100_aj_p50` `OutOfMemoryError`), naming three `julia.exe` at 87.6, 85.6 and 82.8 GB.
- **Overlap:** `run1_smr100_aj_p50_grow` ran `run_pras.jl 2055i0` from 06:14:24 to 06:34:37 and finished normally.
- **Commit limit** at 10:43 on 11-11: 304.7 GB (253.35 GB RAM; `pagefile.sys` was 75.2 GB at 05:30 on 11-10). Free commit 56.6–78.1 GB at 10:46–10:47, with `mck` and `cop28` at 2031.
- **Memory samples:** none between 01:20:48 and 10:44 (see section 1).
- **Per the instructions,** the run was not relaunched, edited or deleted.

### Memory, 10:40–10:48

30-s samples (`memory_samples.csv`); the tree is the case's process tree, and private memory is given as GB.

| Time | Available, GB | `recfix_smr100_aj_p50` tree, private GB | `recfix_smr100_eia_p50` tree, private GB | Largest process |
|---|---|---|---|---|
| 10:41:06 | 190.15 | 4.80 | 4.81 | `solve.py` |
| 10:42:07 | 128.20 | 32.04 | 32.05 | `julia.exe` |
| 10:43:08 | 47.73 | 55.12 | 55.14 | `julia.exe` |
| 10:45:11 | 59.61 | 56.89 | 56.90 | `julia.exe` |
| 10:45:41 | **0.01** | 79.95 | 68.43 | `julia.exe` 66.54 / 57.69 GB working set |
| 10:46:12 | 2.88 | 72.49 | 79.83 | `julia.exe` |
| 10:46:42 | 110.48 | — (ended) | not sampled | — |

- `recfix_fbR_none` reached its PRAS step at about the same time: its tree was at 79.90 GB private at 10:45:41.
- At 10:49, two `julia.exe` 1.12.1 processes, started at 10:40:57 and 10:40:59, held 51.04 and 63.49 GB private, with 103.37 GB available. No other ReEDS run was going on the machine.
- Available memory was below 2 GB in one 30-s sample (10:45:41) and was back at 110 GB by 10:46:42, so the 10-minute rule has not fired.
- The three cases started together and reached each step within about a minute of each other, so their PRAS steps overlapped.

## 4. Deviations

1. **`Manifest.toml` (instructions_2.md, M1–M3).** The runs use paper 1's `Manifest.toml`.
   - **M1.** The swap was already done before this task: `retail_pilot` round 3 (response_3.md, deviation 1, 2026-11-05 11:27) copied `Manifest_paper1.toml` to `Manifest.toml` and backed up the lab file as `runs/Manifest_lab_instantiated_2026-11-05.toml` (MD5 `7aa95004b593f11e84db18afb09881c2`). At 09:53 today, `Manifest.toml` had MD5 `15909b0b295b9ff709e07801206864f8` (written 2026-11-05 11:02:16). No retail-pilot Julia step was running. I copied the backup to `C:\Users\egallup\manifest_backup_20261105\Manifest_lab.toml` (MD5 `7aa95004b593f11e84db18afb09881c2`), as step M1.2 asks. The copy in `runs/` was left in place.
   - **M2.** `julia +1.12.1 --project=. -e "using Pkg; Pkg.instantiate()"` at 09:54:59: exit 0, 20 s, no output (no package listed as downloaded or precompiled). `Manifest.toml` MD5 after: `15909b0b295b9ff709e07801206864f8` (unchanged).
   - **M3.** `julia +1.12.1 --project=. -e "using PRAS; println(pkgversion(PRAS))"`: printed `0.8.0`, exit 0, 3 s.
2. **Remote file copied, not downloaded.** `nomand_fbR_none_demhi` sets `GSw_LoadProfiles = EER2025_100by2050`, which needs `demand_EER2025_100by2050.h5` (record 18435264). It was not in this checkout's `inputs/remote/`, so `runreeds.py` would have downloaded it from Zenodo. The same file with the same record id was in `C:\Users\egallup\ReEDS-hybrid-plant\inputs\remote\`. I copied it to `inputs/remote/demand_EER2025_100by2050_18435264.h5`; its MD5 before and after the copy is `02aa8607339b482dc70af5facd009796`, equal to this checkout's `inputs/remote_files.csv`. Git ignores the folder. The other 7 remote files the 23 cases need were already present with matching MD5.
3. **Memory monitor.** The instructions do not ask for it. A PowerShell script samples, every 30 s, available memory and the working set and private bytes of each case's process tree (rooted at the `cmd.exe` that runs `call_ag_<case>.bat`). Its CSV and the `runreeds.py` console log are in `C:\Users\egallup\ag_new_runs_work\`.
4. **`-r 3` changed to `-r 2`, and two runs stopped or rerun (Ethan's decisions in person, 2026-11-06).** These override "Run three at a time", "A failed run: do not relaunch it" and "Do not stop a run on your own".
   - **About 12:24:** after the `OutOfMemoryError` (section 3b), Ethan chose to let the three running cases finish, then launch the rest at `-r 2`. At 12:25:36 I stopped the `runreeds.py` process (pid 36528) on its own, so it starts no new case; the three run windows kept running.
   - **About 12:44:** Ethan chose to stop the hung `recfix_fbR_none` and rerun it at `-r 2`. Stopped at 12:45:00 (section 3b).
   - **About 12:45:** Ethan chose to rerun `recfix_smr100_aj_p50` at `-r 2` as well.
   - Both old folders were renamed with suffixes `_hung_20261106` and `_oom_20261106`, not deleted, so `runreeds.py` can create the folders again.
   - **Relaunch:** when no `call_ag_*.bat` window is left, a script starts `python runreeds.py -b ag -c nuclearlearning_ag -r 2` from the repo root, with the same environment as the first launch. It answers `runreeds.py`'s prompts with `n` ("overwrite them?") and `y` ("run them and skip the rest?"), so the finished `ag_` folders are kept and skipped. The cases run in casefile order.
   - **Relaunch result:** the script started at 05:55:42 on 2026-11-07, once no `ag_` window was left. The console shows both prompts answered and lists 21 cases to run; `local version ok` is printed for the remote files.
5. **Finished run folders to move off `C:` (Ethan's decision, 2026-11-07, about 10:40).** Step 6 says not to move run folders; this overrides it.
   - **Why:** `recfix_smr100_eia_p50` uses 5.84 GB, of which `g00files/` is 1.2 GB (2 `.g00` files are kept); 21 more runs need about 123 GB, and `C:` had 101 GB free at 05:30.
   - **Plan per run:** N1–N7 on the folder in place, copy `outputs.h5` to the collection folder and check its MD5, then move the folder and compare file counts and bytes.
   - **First try, 10:49:** the target `N:\egallup\ag_new_runs\` (Ethan's choice) could not be made: `Access is denied` at `N:`'s top level. Robocopy exited 16 and copied nothing. `runs/ag_recfix_smr100_eia_p50/` is intact (2320 files, 5844920812 bytes).
   - **External drive, 2026-11-09:** Ethan connected a drive (`E:`, label `T7 Shield`, exFAT, 931.5 GB, 377.6 GB free before the moves). Target: `E:\ag_new_runs\` (new folder; nothing else on `E:` was touched).
   - **Moves, 09:50–09:57:** `robocopy /MOVE /E` per folder, exit 1 each time. For all 6 folders the file count and byte total on `E:` equal the source's, and 0 files are left at the source:

     | Case | Files | Bytes |
     |---|---|---|
     | `recfix_smr100_eia_p50` | 2320 | 5844920812 |
     | `recfix_smr100_iaea_p50` | 2318 | 5839410546 |
     | `recfix_fbR_none` | 2323 | 5848528250 |
     | `recfix_smr100_aj_p50` | 2318 | 5853142809 |
     | `recfix_smr100_mck_p50` | 2323 | 5853174958 |
     | `recfix_smr100_cop28_p50` | 2323 | 5859018338 |
     | `recfix_smr100_eo_p50` (14:06:35, by `autopost.sh`) | 2343 | 5858918697 |
     | `recctl_fbR_none` (15:08:38, by `autopost.sh`) | 2325 | 5860340001 |
     | `recctl_smr100_eo_p50` (08:35:07 on 11-10, by `autopost.sh`) | 2340 | 5856639663 |

   - The renamed old attempts `runs/ag_recfix_fbR_none_hung_20261106/` and `runs/ag_recfix_smr100_aj_p50_oom_20261106/` (6.1 GB each) are not finished runs and stay on `C:`.
   - End times in section 3 and N1 for moved runs come from the `gamslog.txt` copy on `E:` (exFAT) and differ from the earlier readings on `C:` by 1–2 s.
6. **N7 table split per case.** With 6 runs, `results/N7_error_warning_lines.csv` was 899 KB, and the full batch would pass the 1 MB limit for committed logs. From 09:57 on 11-09, the lines are in `results/N7_error_warning_lines/<case>.csv` (about 150 KB each), and `results/N7_error_warning_lines.csv` holds the line count per case.
7. **`report_dump.py` run on a copy of `run1_smr100_eia_p50_grow` (Ethan's decision, answered 10:42 on 11-11).** The original folder was not touched; the copy is `E:\ag_new_runs_diag\ag_run1_smr100_eia_p50_grow\` (section 3b). On Ethan's second decision (11-11, about 11:00) the copy's `outputs.h5` is the case's result.
8. **`run1_smr100_iaea_p50_grow` rerun, `-r 2` kept (Ethan's decision, 11-11, about 11:00).** These override "A failed run: do not relaunch it".
   - The failed folder was renamed at 11:01:09 to `runs/ag_run1_smr100_iaea_p50_grow_oom_20261111/` (not deleted).
   - A script (`wait_then_launch3.sh`) waits until the running batch has no other queued case and fewer than 2 cases running, then runs `python runreeds.py -b ag -c nuclearlearning_ag -s run1_smr100_iaea_p50_grow -r 1` with the same environment (log `runreeds_console_r3_iaea.log`). `-s` limits the launch to this case, so the moved folders are not rerun, and at most 2 cases run at a time. This script was stopped at about 12:57 on 11-11 without having launched anything (its `status.py` input failed after 12:54); the rerun is now the last entry of the queue in deviation 9.
9. **Queue restarted with a script after the launcher window closed (Ethan's decision, 11-11 about 12:58).**
   - `runs/ag_run1_smr100_eo_p50_grow/` (created 12:54:50, only empty `autocode/` and `inputs_case/`) was renamed at 12:58:24 to `runs/ag_run1_smr100_eo_p50_grow_partial_20261111/` (not deleted).
   - `queue.ps1` (window title "ReEDS ag batch queue - DO NOT CLOSE", started 12:58:52) starts the next case whenever fewer than 2 cases are active, in casefile order: `run1_smr100_eo_p50_grow`, the 6 `nomand_fbR_none_*`, the 2 `p05base_*`, then `run1_smr100_iaea_p50_grow`. Each case is started in its own window ("ReEDS ag <case> - DO NOT CLOSE") with `python runreeds.py -b ag -c nuclearlearning_ag -s <case> -r 1` and the same environment as before; logs in `C:\Users\egallup\ag_new_runs_work\launch_logs\`. A case counts as active while its `call_ag_<case>.bat` window or its launch window is open.
   - `status.py` (my progress script) failed on the folder without `gamslog.txt` and stopped `autopost.sh`; it now reports such a folder as `nolog`, and `autopost.sh` was restarted at about 13:00.

## 5. Checks N1–N7

**Partial:** 11 of 23 runs checked: the full RUN-3 group (`recfix_fbR_none`, `recfix_smr100_{eia,aj,iaea,mck,cop28,eo}_p50`, `recctl_fbR_none`, `recctl_smr100_eo_p50`), `run1_smr100_aj_p50_grow` and `run1_smr100_eia_p50_grow` (with the copy's `outputs.h5`, deviation 7). Each was checked on `C:` before its move. The CSV files in `results/` hold the rows so far and are rebuilt as more runs finish.

- **N1:** all 9 have `outputs.h5` (65.7–66.4 MB), last solve year 2050 (= `endyear`), 18.39–19.62 h (the 7 `-r 2` runs: 18.39–19.62 h; the 2 `-r 3` runs: 19.15 and 19.43 h), folders 5.84–5.86 GB.
- **N2:** no difference between `inputs_case/switches.csv` and the casefile column, for any of the 9.
- **N3:** `can_exports_stress` is missing in all 9. The two `fbR_none` runs (`recfix_fbR_none`, `recctl_fbR_none`) also lack `nuclear_cap_price` and `nuclear_cap_price_raw`; the 7 `smr100` runs have both.
- **N4:** `can_exports_stress` is missing in all 9 (see N3).
- **N5, N6:** N5 does not apply to RUN-3 or RUN-1. N6 (RUN-1, 2 runs so far): `nuclear-smr` capacity equals the mandate file in 2041–2050 for both. `run1_smr100_aj_p50_grow` (`nuclear_cap_trajectory_abou_jaoude_smr_grow.csv`) is above it by 0.00078 MW in 2053 (45465.30078 vs 45465.3) and 0.0016 MW in 2055 (51509.60156 vs 51509.6). `run1_smr100_eia_p50_grow` (`nuclear_cap_trajectory_eia_aeo_high_smr_grow.csv`) equals it in 2053 and is above it by 0.00078 MW in 2055 (22987.30078 vs 22987.3).
- **RUN-1 so far:** `run1_smr100_aj_p50_grow`: `outputs.h5` 72.9 MB, last solve year 2055 (= `endyear`), 22.45 h, folder 6.68 GB; N2 no difference; N3 only `can_exports_stress` missing; N7 960 lines. `run1_smr100_eia_p50_grow`: `outputs.h5` (copy) 72.8 MB, last solve year 2055, 22.87 h, folder 5.25 GB (original, without the files `report_dump.py` writes); N2 no difference; N3 only `can_exports_stress` missing; N7 683 lines.
- **N7:** lines matching "error" or "warning" (case-insensitive) in `gamslog.txt`: 954 (`recfix_fbR_none`, `recfix_smr100_eia_p50`) and 952 (the other 7). Lines are in `results/N7_error_warning_lines/<case>.csv` (deviation 6). In the first 2 runs, most are Python warnings logged at ERROR level by `retail_rate_calculations.py` (pandas chained-assignment warnings) and `ReEDS2PRAS` `No generators in region` warnings.

The full tables follow when every run has finished.

## 6. Collection folder

**Partial:** `C:\Users\egallup\collected_outputs_ag\` holds 11 files, `ag_<case>_outputs.h5` for each checked case in section 5 (`run1_smr100_eia_p50_grow` from the copy on `E:`, deviation 7). MD5 checksums are in `results/MD5SUMS_outputs.txt`; each copy's MD5 equals its source's, taken before the move. The run folders themselves are in `E:\ag_new_runs\ag_<case>\` (deviation 5).

## 7. Questions for Claude

1. **Three runs at a time do not fit in memory during the PRAS step (section 3b).** The `-r 3` rule says to report and ask. Each run's `julia.exe` reached about 57–67 GB working set (up to 80 GB private for the tree) in the 2020 PRAS step, three overlapped, available memory reached 0.01 GB, and one run failed. Every later solve year runs PRAS too. **Answered by Ethan in person:** let the running cases finish, then run the rest at `-r 2`, rerunning `recfix_fbR_none` and `recfix_smr100_aj_p50` (deviation 4). No open question.
2. **`run1_smr100_eia_p50_grow` has no `outputs.h5` (section 3b).** `report_dump.py` left no line in `gamslog.txt`, and its error text is not in any file. The other 5 `run1_*_grow` cases also end in 2055 and will reach the same step from about 07:30 on 11-11 (`run1_smr100_aj_p50_grow`) onward. Asked Ethan on 2026-11-10 at about 14:15; **answered 10:42 on 11-11:** run `report_dump.py` on a copy (deviation 7). **Answered about 11:00 on 11-11:** use the copy's `outputs.h5` (deviation 7). No open question.
3. **`run1_smr100_iaea_p50_grow` failed in its 2044 PRAS step during a Windows low-virtual-memory event (section 3b).** Two `julia.exe` held about 98 GB virtual memory each. `run1_smr100_mck_p50_grow` and `run1_smr100_cop28_p50_grow` (endyear 2055) are running at the same time; `run1_smr100_eo_p50_grow` is queued. **Answered by Ethan about 11:00 on 11-11:** rerun `run1_smr100_iaea_p50_grow`, keep `-r 2` (deviation 8). No open question.
