# z-ethan on branch `paper-AG`: starting kit

This folder holds the minimum analysis that paper AG needs to start and design its work. Paper AG
asks who gains when a nuclear build-out deflates its own market value. Value deflation is the fall
in a technology's market value as its own fleet grows. The working outline is
`docs/paper_AG_value_deflation_transfers_outline.md`.

Claude created this branch for Ethan on 2026-10-21 from `nuclear-learning` at commit `963599a`. Everything
outside `z-ethan/` is paper 1's ReEDS fork, unchanged. The fork therefore keeps the casefiles and
model changes of all paper 1 runs, including `mapanchor2`. The worktree sits at
`C:\Users\ethan\code\research\ReEDS-paper-AG`.

## What is here

| Path | Contents | In Git |
|---|---|---|
| `nlpaper/` | The helper package of paper 1's public analysis: repository paths, thread and plot setup, plot style, figure composition, the `outputs.h5` reader and parquet extractor, and the requirement-map fitter. | yes |
| `notebooks/` | Ten notebooks from paper 1's public analysis, unchanged except for paths (see below). `00_run_all.ipynb` runs them in order. | yes |
| `data/` | Frozen inputs: the extract specification, the SHA-256 manifest of the ReEDS output archive, the registration files (which Monte Carlo draws became which ReEDS cases), and small frozen slices of ReEDS inputs (`reeds_inputs/`). | yes |
| `mc/` | `pris_loader.py` and `rds2_2025_units.csv`, the reactor unit list. Notebook 01 and `inputs/nuclear_learning/_generate_cap_trajectories.py` read them here. | yes |
| `environment.yml`, `requirements.txt` | The pinned Python environment of paper 1's public analysis. | yes |
| `results/` | A local cache of paper 1's public results: the 56 MB of parquet extracts and the exports of the ten notebooks. The notebooks overwrite this cache when they run. | no |
| `docs/` | The outline, the literature review for AG (review, gap-list extract, the AG rows of the claims and bibliography tables, the broad assessment) and the 10-14 stocktake (synthesis and reports 02–04). | no |
| `scratch/ag_firstcut_20261020/` | The 10-20 first-cut scripts and their README. They read the h5 archive directly. Nothing in them is registered. | no |

`z-ethan/.gitignore` decides what Git tracks. The repository's shared `.git/info/exclude` holds
paper 1's rule that ignores most of `z-ethan`. The rules in `z-ethan/.gitignore` take precedence
over it inside this folder.

### The ten notebooks

| Notebook | What AG uses it for |
|---|---|
| 01 Monte Carlo cost engine | The 10,000-draw cost ensemble (`mc_perdraw.npz`) that 06b, 10 and 11 read. |
| 05 Extract ReEDS outputs | Checks the extracts against their manifest. With the archive it rewrites them. |
| 06a, 06b Run tables | Shadow prices, builds and prices by year for every run. |
| 07 Required support | The support bill per target: the developer side of the transfer. |
| 08 Market conditions | Gas, renewables, demand and transmission conditions. |
| 09 Credit feedback | The closed-loop credit: ITC schedules fed back into ReEDS. |
| 10 Requirement map | The fitted map from cost sample to required support. |
| 11 Market transfer | Thresholds across the six market conditions. |
| 15 New plant value | The value of a new plant across the targets. |

## Changes from the public analysis

The source is `nuclear-learning-target-analysis-ReEDS/analysis/` as published for paper 1.
The kit changes only paths:

- `nlpaper/paths.py` finds the repository by the folder `z-ethan/nlpaper`, and `ANALYSIS` is `z-ethan/`.
- `nlpaper/pris_loader.py` loads the loader and the unit list from `z-ethan/mc/`, because this fork keeps them there.
- In the notebooks and the package messages, the string `analysis/` reads `z-ethan/`.
- `00_run_all.ipynb` lists only the ten notebooks of this kit.

## How to run

1. Activate the environment: `conda activate nuclear-learning-analysis`. On Windows, activate it
   rather than calling its `python.exe` by path, so that the compiled libraries on `PATH` are the
   environment's own.
2. Run the notebooks from `z-ethan/notebooks/` in the order 01, 05, 06a, 06b, 07, 08, 09, 10, 11, 15,
   or run `00_run_all.ipynb`. The whole set took 6 minutes on Ethan's laptop.
3. Without the archive, notebook 05 checks the cached extracts and finishes at once.

On 2026-10-21 every notebook ran without error from this kit. The section "Smoke test" below
compares the exports with paper 1's.

## Data

- **Cached extracts:** `results/extracts/`. They are a copy of paper 1's committed extracts. They are not in Git on this branch.
- **Public archive layout:** `D:\ReEDS files\nuclear-learning\public_archive\nuclear-learning-reeds-outputs\`.
  To read the h5 files through notebook 05, set `$env:NL_REEDS_OUTPUTS` to that folder, and only for
  notebook 05 (see the warning below).
- **Flat archive:** `D:\ReEDS files\nuclear-learning\All runs so far\` (600 files). The first-cut scripts read this one.
- **Hourly caches:** `z-ethan/referee_response/v1_lifetime/` in paper 1's worktree (2.1 GB). Treat them as read-only.

**Warning: notebook 01 writes into the output archive.** When `NL_REEDS_OUTPUTS` is set (or a
folder `nuclear-learning-reeds-outputs` sits next to the repository), notebook 01 copies its
`mc_perdraw.npz` into the archive unless the archived copy is array-identical. In this environment
the regenerated file differs from the archived one in the last digits (see "Smoke test"). A run of
notebook 01 with the variable set would therefore overwrite the archived file and break the
archive's `SHA256SUMS`. Leave `NL_REEDS_OUTPUTS` unset when notebook 01 runs, and do not run
`00_run_all.ipynb` with it set.

## New ReEDS runs

ReEDS needs `inputs/remote` (2.4 GB). Git ignores that folder, so this worktree lacks it. Either
copy it from paper 1's worktree or link it with a directory junction. A junction shares one copy,
so a change made through one worktree appears in both:

```powershell
New-Item -ItemType Junction -Path C:\Users\ethan\code\research\ReEDS-paper-AG\inputs\remote `
  -Target C:\Users\ethan\code\research\ReEDS-nuclear-learning\inputs\remote
```

ReEDS runs need the `reeds` environment activated on `PATH`, and `runreeds` needs `CONDA_DEFAULT_ENV=reeds`.

## Rules carried over from paper 1

- **Dollar years.** The Monte Carlo engine works in 2022 $, the ReEDS side in 2024 $, raw ReEDS
  outputs in 2004 $, and paper 1 reports 2025 $. Convert at display with `plotstyle.to2025(from_year)`.
- **Discount rate.** Current work uses 5.36%. Some frozen paper 1 analyses use 4.55%.
- **Shadow price to support.** The mandate shadow price is an annual rental price in 2004 $/MW-yr.
  Multiply it by `pvf_onm` = 14.7645 to obtain the support per MW.
- **Regional readouts.** Plant siting is degenerate across cost samples. Report national aggregates only.
- **Artifacts.** The 2031 first-cohort premium, the ATB 2032 dip and the 2047→2050 uptick carry no claim.
- **Learning off against learning on.** The requirement map is fitted on learning-off mandate runs.
- **Pulling in more from paper 1.** Never execute `mc_cost_trajectories` cells [4] and [36]–[40] or
  any `*_case_export` notebook: they overwrite ReEDS inputs. Never edit `referee_response/`. The
  notebooks in this kit never write ReEDS inputs.

`docs/stocktake/00_synthesis.md` §6 lists all twelve traps of the paper 1 assets.

## Smoke test (2026-10-21)

Claude ran every notebook of this kit once with `nbconvert`, in the environment
`nuclear-learning-analysis`, in extracts mode (`NL_REEDS_OUTPUTS` unset). The executed copies went
to a scratch folder, so the committed notebooks keep paper 1's outputs. The notebooks wrote their
exports to `results/exports/`. Claude compared those exports with paper 1's committed exports.

| Notebook | Exit | Time | Exports compared with paper 1 |
|---|---|---|---|
| 01 | 0 | 25 s | 9 identical; `mc_perdraw.npz` and `engine_constants.json` differ by at most 3 ULP (relative 7e-16) |
| 05 | 0 | 22 s | no exports; all 309 extracts match the specification and cover all 588 archive runs |
| 06a | 0 | 33 s | 34 identical |
| 06b | 0 | 60 s | 49 identical |
| 07 | 0 | 25 s | 21 identical |
| 08 | 0 | 17 s | 6 identical |
| 09 | 0 | 15 s | 17 identical |
| 10 | 0 | 133 s | 12 identical; 18 differ in the last digits (largest relative difference 6.7e-9, in the leave-one-out cells of the map fit); every verdict in `m108_verdict.csv` is unchanged |
| 11 | 0 | 33 s | 11 identical; 4 differ in the last digits (largest relative difference 5e-11) |
| 15 | 0 | 13 s | 3 identical |

ULP means unit in the last place. The public README documents two sources of last-digit
differences. First, this environment carries conda-forge's numpy build, and paper 1's results came
from the PyPI wheel; the two builds differ in the last bit of some elementary functions. Second, the
requirement-map fit of notebook 10 depends on the thread count in its last digits.
