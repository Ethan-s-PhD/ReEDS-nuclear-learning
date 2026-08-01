# MC cost-trajectory notebook (Track B)

`mc_cost_trajectories.ipynb` is the paper's Monte Carlo engine: for each of the six locked US
nuclear deployment schedules it simulates 5,000 joint draws of the uncertain learning parameters and
produces the overnight-cost (OCC), construction-duration, and financed-capital-cost trajectories
consistent with that schedule, for both large reactors and SMRs. From each schedule's MC it extracts
three representative joint draws (P5/P50/P95 of financed CAPEX) and exports them as ready-to-run
ReEDS cases. See the notebook's opening cell for a full reader's guide; it is written to be readable
by non-experts.

**Spec authority:** `z-ethan/nuclear-learning-paper-plan.md` (v8). Port source (reference only):
`ReEDS-hybrid-plant/z-ethan/mc_nuclear_smr_learning.ipynb` (v2.4).

## How to run

```bash
conda activate reeds          # the fork's environment.yml env; plain python + numpy/pandas/scipy/matplotlib
jupyter lab z-ethan/mc/mc_cost_trajectories.ipynb   # then Run All (a few minutes end to end)
```

Note (Windows): the `reeds` env must be *activated*, not just invoked by path — matplotlib's
DLLs delay-load from the env's `Library\bin`, which activation puts on `PATH`.

## Files

| File | What it is |
|---|---|
| `mc_cost_trajectories.ipynb` | The notebook (all logic lives here) |
| `winner_boundary.ipynb` | Downstream analysis of the SMR-vs-large winner: which parameters decide it and where the advantage flips (issue-8 regroup evidence). Reads `exports/mc_perdraw.npz` (written by the MC's S10b cell, gitignored) — run the MC notebook first. Uses plotly for the interactive/3D figures. |
| `pris_loader.py`, `rds2_2025_units.csv`, `pris_data_spec.md` | IAEA RDS-2 2025 unit-level data + loader (verbatim copies from the reference repo) |
| `exports/` | Notebook-local outputs: percentile tables per schedule, the 18 selected draws, run metadata, the per-draw `.npz`, and the winner-analysis tables (`wb_*.csv`) |
| `figures/` | Paper figures (hindcast check, fragmentation figure, cost fans) |

## What it writes into the ReEDS fork

- `inputs/nuclear_learning/US_SCHEDULES.csv` — the single source of truth for the six schedules;
  `inputs/nuclear_learning/_generate_cap_trajectories.py` regenerates the mandate trajectory CSVs from it.
- `inputs/plant_characteristics/nuclear_mc_{case}.csv` + `nuclear-smr_mc_{case}.csv` — per-case OCC
  trajectories (18 cases × 2 techs), plus `dollaryear.csv` rows.
- `inputs/financials/financials_tech_mc_{case}.csv`, `construction_times_mc_{case}.csv`,
  `construction_schedules_mc.csv` — per-case construction durations wired into ReEDS's IDC machinery.
- `cases_nuclearlearning_mc.csv` (repo root) — the 18-case ReEDS run matrix.

Every written file is round-trip checked by the notebook's QA section (S15).

## Mixed-build stress test

`mixed_build_optimizer.ipynb` answers one question the main notebook assumes away: **could any
mixed large+SMR build program ever be cheaper than committing to the better single technology?**
It relaxes the two assumptions that stack the deck against mixing — it allows drawn
cross-technology spillover (up to 30% each direction, `x_ls`/`x_sl`), and it draws each
technology's (learning rate, anchor cost) pair **independently**, conditioned on the two
orderings every real SMR proposal respects: `boak_smr > boak_large` (SMR starts pricier) and
`lr_smr > lr_large` (SMR learns faster), so the starting-cost gap and the learning-rate gap
vary freely against each other. Then, for every drawn future (10,000 per schedule), a per-draw
optimizer chooses the SMR share of each build year 2031–2050 (`smr_percentages`, length 20) to
minimize the discounted financed cost of hitting that future's deployment schedule. The two pure
strategies are always in the candidate set, so the headline metric is the signed *margin* of the
best genuinely mixed strategy vs the best pure one (negative = mixing wins); the S8 maps chart
the winners and the near-mixed region over the (learning-rate gap, cost gap) plane.

Run it the same way as the main notebook (same env; ~10–15 min). It is read-only toward the
ReEDS tree (consumes `US_SCHEDULES.csv` and the financing inputs; writes only to
`exports/mixed_build/` and `figures/`). Its QA section pins the engine bit-for-bit to the main
notebook at the "off" settings and reproduces the S13 fragmentation result in the shared limit.
Cheap test runs: set env vars `MIXOPT_DRAWS` / `MIXOPT_SWEEP_DRAWS` before launching.

## The 100%-SMR case export (next-phase inputs)

`smr100_case_export.ipynb` is the production case generator for the ReEDS phase, superseding
the main notebook's winner-take-all 18-case export: since the SMR program is the cheaper pure
strategy in 76–89% of futures and mixed optima are negligible, **deployment is assumed 100%
SMR**. It re-runs the MC (ordered independent draws, 10,000/schedule, no cross-tech spillover —
paper convention), ranks each schedule's draws by discounted SMR program cost, selects the
P5/P50/P95 joint draws, and exports 18 cases: `cases_nuclearlearning_smr100.csv` (repo root),
36 plantchar files (`nuclear{,-smr}_mc_smr100_*`; the large-reactor file is the
international-spillover-only counterfactual), 18+18 financials/construction-times files, and
the shared `construction_schedules_mc.csv`. Every written file is round-trip checked (QA-5).
Launch the phase with `python runreeds.py -b <batch> -c nuclearlearning_smr100`. Cheap test
runs: env var `SMR100_DRAWS`.
