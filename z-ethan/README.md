# z-ethan on branch `paper-EF`: starting kit

This folder holds the minimum analysis that paper EF needs to start and design its work. Paper EF
surveys nuclear cost-estimation methods. For each method choice, it asks which technology the
choice favours, large reactors or SMRs (small modular reactors), and by how much. It measures each
effect on one learning engine. The working outline is `docs/paper_EF_cost_methods_lineage_outline.md`.

Claude created this branch for Ethan on 2026-10-21 from `nuclear-learning` at commit `963599a`.
Everything outside `z-ethan/` is paper 1's ReEDS fork, unchanged. The worktree sits at
`C:\Users\ethan\code\research\ReEDS-paper-EF`. The outline plans no new ReEDS runs.

## What is here

| Path | Contents | In Git |
|---|---|---|
| `nlpaper/` | The helper package of paper 1's public analysis, without the modules that no EF notebook uses: repository paths, thread and plot setup, plot style, figure composition and the PRIS loader. | yes |
| `notebooks/` | Four notebooks from paper 1's public analysis, with the changes listed below. `00_run_all.ipynb` runs them in order. The committed notebooks hold the outputs of the kit's full run on 2026-10-22. | yes |
| `data/literature/` | Frozen records of the published cost projections: transcribed cost points, one row of method assumptions per source, digitized figures, and the cite-only list. `data/literature/README.md` describes each file. | yes |
| `data/reeds_inputs/` | Small frozen slices of ReEDS inputs that notebook 03a reads. | yes |
| `mc/` | `pris_loader.py` and `rds2_2025_units.csv`, the reactor unit list. Notebook 01 and `inputs/nuclear_learning/_generate_cap_trajectories.py` read them here. | yes |
| `environment.yml` | The pinned Python environment of paper 1's public analysis. | yes |
| `results/` | A local cache of the exports of the four notebooks, copied from paper 1's public results. The notebooks overwrite this cache when they run. | no |
| `docs/` | The master plan (`master_plan.md`: goals, route and status), the file ledger (`file_ledger.md`: one row per file, used to prune and merge files), the outline, the literature review for EF (review, gap-list extract, the EF rows of the claims and bibliography tables, the broad assessment) and the 10-14 stocktake (synthesis and report 01). | no |

`z-ethan/.gitignore` decides what Git tracks. The repository's shared `.git/info/exclude` holds
paper 1's rule that ignores most of `z-ethan`. The rules in `z-ethan/.gitignore` take precedence
over it inside this folder.

### The four notebooks

| Notebook | What EF uses it for | Runtime, reference machine | Runtime, laptop |
|---|---|---|---|
| 01 Monte Carlo cost engine | The learning engine: the 10,000-draw cost ensemble per target trajectory. | 0.5 min | 0.4 min |
| 02 ATB basis and literature | The ATB feasibility tables, which test which cost inputs reproduce the ATB (NREL's Annual Technology Baseline), and the published cost points placed on the engine (the source of paper 1's Fig 1). | 2.5 min | 1.3 min |
| 03a NPV winner and mixed build | The probability that each technology wins on net present value, and the mixed build. | 17 min | 12.4 min |
| 03b Technology comparison and observation | The large-against-SMR comparison in cost space, the claims ledger and the optimism-bias sweep. | 80 min | 32.0 min |

The reference machine is paper 1's, with four threads, and it often shared the CPU with other runs.
The laptop column comes from the full run of 2026-10-22 (see "Full run"). That run used four threads
on an Intel i7-1355U, at below-normal priority, while other work ran on the laptop.

## Changes from the public analysis

The source is `nuclear-learning-target-analysis-ReEDS/analysis/` as published for paper 1.
The kit changes the paths, corrects two notebooks and drops unused code. The analysis code that
runs is unchanged.

- `nlpaper/paths.py` finds the repository by the folder `z-ethan/nlpaper`, and `ANALYSIS` is `z-ethan/`.
- `nlpaper/pris_loader.py` loads the loader and the unit list from `z-ethan/mc/`, because this fork keeps them there.
- In the notebooks and the package messages, the string `analysis/` reads `z-ethan/`.
- `00_run_all.ipynb` lists only the four notebooks of this kit. Since 2026-10-22, its text also
  describes only these four notebooks: their order, their runtimes and the `NL_REEDS_OUTPUTS` warning.
- The kit build stored two cells with one character per line: the runtimes cell of `00_run_all.ipynb`
  and the matched-pair fit cell of notebook 02 (cell 13). Jupyter still ran them. On 2026-10-22 Claude
  stored both cells as ordinary lines. The code text of both cells is unchanged.
- On 2026-10-22 the kit dropped the files that no EF notebook uses: the `nlpaper` modules `h5io`,
  `mapfit` and `numbers`; `data/reeds_inputs/budget_parity_context.csv`, which only paper 1's
  notebook 09 reads; and `requirements.txt`, because `environment.yml` holds the same pins. The
  setup cells of notebooks 01 to 03b no longer import `h5io`, which they never called, and
  `nlpaper.paths` no longer defines `EXTRACTS` or `casefile`, which only `h5io` used. Commit
  `1099bc9` holds the last copies of the dropped files. `docs/file_ledger.md` logs each removal.

## How to run

1. Activate the environment: `conda activate nuclear-learning-analysis`. On Windows, activate it
   rather than calling its `python.exe` by path, so that the compiled libraries on `PATH` are the
   environment's own.
2. Run the notebooks from `z-ethan/notebooks/` in the order 01, 02, 03a, 03b, or run `00_run_all.ipynb`.

No notebook in this kit needs the ReEDS outputs.

**Warning: notebook 01 writes into the output archive.** When `NL_REEDS_OUTPUTS` is set (or a
folder `nuclear-learning-reeds-outputs` sits next to the repository), notebook 01 copies its
`mc_perdraw.npz` into the archive unless the archived copy is array-identical. In this environment
the regenerated file differs from the archived one in the last digits (see "Full run"). A run of
notebook 01 with the variable set would therefore overwrite the archived file and break the
archive's `SHA256SUMS`. Leave `NL_REEDS_OUTPUTS` unset for this kit.

## Rules carried over from paper 1

- **Dollar years.** The Monte Carlo engine works in 2022 $, and paper 1 reports 2025 $. Each
  published source has its own dollar year (column `dollar_year` in `data/literature/lit_sources.csv`).
  Convert at display with `plotstyle.to2025(from_year)`.
- **Discount rate.** Current work uses 5.36%. Some frozen paper 1 analyses use 4.55%.
- **Fig 1 of paper 1.** It plots each source's reported values at the capacity that source reports.
  The placement gives context; it is not a finding. Scoring the sources is a separate step.
- **Pulling in more from paper 1.** Never execute `mc_cost_trajectories` cells [4] and [36]–[40] or
  any `*_case_export` notebook: they overwrite ReEDS inputs. Never edit `referee_response/`. The
  notebooks in this kit never write ReEDS inputs.

`docs/stocktake/00_synthesis.md` §6 lists all twelve traps of the paper 1 assets.

## Open items from paper 1 that bear on the lineage strand

- **Abou-Jaoude tables (10-15 check, not yet in any notebook).** One formula reproduces all 30
  overnight costs in Abou-Jaoude Tables 50/52/54 to the $250 rounding, with a learning rate of 9.5%
  for both technologies, best-of-a-kind (BOAK) cost at one unit per firm, and the unit count taken
  industry-wide from zero. At the report's stated large-reactor rate of 8%, the large columns miss
  by $250–500. The 9.5% is inferred; the report never states it. Ask the authors before asserting it.
- **Notebook 02 still uses paper 1's earlier placement of the Abou-Jaoude points.** It counts only
  the capacity built after 2030, and it draws the 2030 points at 0.5 (large) and 0.83 (SMR) units per
  vendor (`AJ_X_UNITS_2030`, code cell 44). The 10-15 check found that placement wrong: the tables
  count units industry-wide from zero.

## Full run (2026-10-22)

Claude ran `00_run_all.ipynb` with `nbconvert`, in the environment `nuclear-learning-analysis`, with
`NL_REEDS_OUTPUTS` unset. The driver executed the four notebooks in place, so the committed notebooks
now hold the outputs of this run. Every notebook exited 0, and the whole run took 46 minutes.
Notebook 01 found no output archive, so it skipped the archive copy. Notebook 03b ran the full
10,000 draws per schedule.

A watcher sampled the memory of the run's processes every 30 seconds. The watcher started late, so it
missed notebook 01 and the first minute of notebook 02. Claude compared every export file, figures
included, with paper 1's committed exports.

| Notebook | Exit | Time | Peak working set | Exports compared with paper 1 |
|---|---|---|---|---|
| 01 | 0 | 0.4 min | not measured | 14 files: 11 identical; `mc_perdraw.npz` and `engine_constants.json` within relative 1e-12; `mc_export_metadata.json` differs only in paths and the git commit |
| 02 | 0 | 1.3 min | at least 1.1 GB | 27 files, all identical |
| 03a | 0 | 12.4 min | 0.6 GB | 10 files: 8 identical; `npv_winner_summary.csv` within relative 1e-12; `mixed_build_metadata.json` differs only in the git commit and the timestamp |
| 03b | 0 | 32.0 min | 1.3 GB (2.9 GB committed) | 17 files: 13 identical; `dominance_tests.csv`, `large_win_margins.csv` and `robustness_map.csv` within relative 1e-12; `tc_metadata.json` differs only in those three files' hashes, the git commit and the timestamp |

The last-digit differences come from the numpy build. This environment carries conda-forge's numpy,
and paper 1's results came from the PyPI wheel. The public README documents this source.

Free memory never fell below about 4.8 GB of the laptop's 15.7 GB. Notebook 03b therefore fits on the
laptop alongside ordinary work.
