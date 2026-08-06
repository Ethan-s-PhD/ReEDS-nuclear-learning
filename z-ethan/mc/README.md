# MC cost-trajectory notebook (Track B)

`mc_cost_trajectories.ipynb` is the paper's Monte Carlo engine: for each of the six locked US
nuclear deployment schedules it simulates 10,000 joint draws of the uncertain learning parameters and
produces the overnight-cost (OCC), construction-duration, and financed-capital-cost trajectories
consistent with that schedule, for both large reactors and SMRs. From each schedule's MC it extracts
three representative joint draws (P5/P50/P95 of financed CAPEX) and exports them as ready-to-run
ReEDS cases. See the notebook's opening cell for a full reader's guide; it is written to be readable
by non-experts.

> **Reading the mc_ 18-case files.** The cases are actual *joint* draws ranked by **program**
> cost, so a per-tech file is not that tech's own cost percentile: where the winner flips
> between percentiles (it does in 3 of 6 schedules at p95), the loser tech rides the loser
> channel (international spillover plus the drawn cross-tech fraction x of the winner's
> program, S5 Step 5′) and its capcost can be *cheaper* in a nominally more
> expensive case (QA12b in the notebook prints the ordering table). The mc_ family also ranks
> on financed CAPEX, while the smr100 family ranks on full NPV — the two families' percentile
> labels are not on a common scale. All ReEDS analysis uses `cases_nuclearlearning_smr100.csv`.

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
| `npv_winner_check.ipynb` | Robustness check: re-ranks every draw on the **full NPV** (financed CAPEX + 30-yr PV of FOM/VOM/fuel, capacity factor = ReEDS's own `avail`, replicated bit-exactly from its raw inputs) instead of CAPEX alone — does the winner change? FOM/VOM ride the draw's cost-dial percentile across the ATB advanced→conservative range (they are not independent sensitivities). Reads `exports/mc_perdraw.npz`; needs `h5py` for the state-temperature h5. |
| `atb_parameter_space.ipynb` | The RQ2 inversion (Step 2): what learning-parameter worlds reproduce the ATB 2024 nuclear cost trajectories at the Abou-Jaoude deployments, and what deployment the 2050 costs require when deployment is free. Ports the OCC engine verbatim (QA-0 parity vs `exports/mc_perdraw.npz` — run the MC notebook first); OCC-only, no ReEDS runs, no draws. Writes `exports/atb/` and `figures/atb_*.png`. |
| `pris_loader.py`, `rds2_2025_units.csv`, `pris_data_spec.md` | IAEA RDS-2 2025 unit-level data + loader (verbatim copies from the reference repo) |
| `exports/` | Notebook-local outputs: percentile tables per schedule, the 18 selected draws, run metadata, the per-draw `.npz`, the winner-analysis tables (`wb_*.csv`), and the NPV-check tables (`npv_*.csv`) |
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
It relaxes the assumptions that stack the deck against mixing: it pioneered the drawn
cross-technology spillover (up to 30% each direction, `x_ls`/`x_sl` — since adopted into the
main engine, 2026-08-06), and it draws each
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

## The ATB inversion (RQ2 / Step 2)

`atb_parameter_space.ipynb` answers research question 2 without a single ReEDS run: **what
conditions would make the ATB 2024 nuclear cost projections happen?** The ATB numbers (both
techs, conservative/moderate/advanced) come from Abou-Jaoude et al., who pair each cost
trajectory with a deployment projection (12/34/200 GW of new builds by 2050 —
`z-ethan/abou-jaoude nuclear deployment projections.csv`). Part 1 fixes deployment at the
paired projection, pins BOAK at the ATB 2030 anchor (the anchor convention makes OCC(2030) ≡
BOAK, so the fit is on curve shape only), and enumerates ~1.06 M designed worlds per fit over
(LR × s × u × m × experience base × CES ρ) to map the **feasible set** — every world within
$250/kW of the ATB trajectory at the 2035–2050 milestones. The LR grid deliberately extends to
30%, past the MC's sampled support, so "reachable only outside the prior" is a reportable
outcome, not a blind spot. Part 2 uses the engine's path-memorylessness (OCC(2050) depends on
deployment only through the cumulative 2050 stock — QA-verified) to chart the **required
deployment** surface that delivers each ATB 2050 cost when deployment is free. Outputs:
best-fit/feasible-share/cross-pairing/required-deployment tables in `exports/atb/` (with an
integrity-hash manifest) and the `figures/atb_*.png` set.

## The 100%-SMR case export (next-phase inputs)

`smr100_case_export.ipynb` is the production case generator for the ReEDS phase, superseding
the main notebook's winner-take-all 18-case export: since pure single-technology programs are
truly optimal (mixed-build stress test) and the SMR program is the cheaper one in most futures,
**deployment is assumed 100% SMR**. It re-runs the main notebook's own MC — the identical
comonotone draw on the identical seed streams (QA-0 asserts the worlds match `mc_perdraw.npz`
draw-for-draw) — with the whole program feeding SMR learning in every draw, and measures
everything on the **discounted SMR program NPV** (financed CAPEX + 30-yr PV of FOM/VOM/fuel
at CF = ReEDS's own `avail`; convention and validation in `npv_winner_check.ipynb`, adopted
2026-08-03). The exported cases are the **P5/P50/P95 percentile joint draws** of that
ranking per schedule (v10, adopted 2026-08-06, reverting the short-lived 2026-08-03
designed-cases detour): actual drawn worlds with registered draw indices
(`exports/smr100/selected_draws.csv`, asserted identical to `mc_perdraw.npz`), read as a
**constrained optimizer** over the *plausible* (drawn) set at the 90% level rather than the
priors' support corners. The p05–p95 pair's coverage is a **layered claim**
(ratified 2026-08-06; all numbers in `exports/smr100/band_coverage.csv`): 90% by
construction on program cost, ~0.62–0.81 empirical simultaneous coverage for the
year-by-year subsidy bracket, and a higher one-sided coverage of the p95 path (the chance
the subsidy never exceeds the hi case's — the policy-relevant direction). The engine-optimized `lo`/`hi` corner worlds are retained as an appendix
**possibility frontier** (`bounds_record.csv`; jointly enumerated, coordinate-verified,
strictly outside all 10k draws, `dur_z` capped at ±2.33) and as the dual-monotonicity
**pilot pair** `smr100_aj_{blo|bhi}` in the separate `cases_nuclearlearning_smr100_bounds.csv`
(their input paths pointwise-dominate every draw — QA-4e — so their ReEDS dual trajectories
must not cross); the **literature-expected world** (Abou-Jaoude LR 8%/9.5% and m=4, ATB 2024
moderate BOAK/FOM/VOM; ~P38–40 of the drawn NPV) is a zero-run overlay, not a case. The
18 production cases export with U1-comonotone FOM/VOM in the plantchar files:
`cases_nuclearlearning_smr100.csv` (repo root),
36+4 plantchar files (`nuclear{,-smr}_mc_smr100_*`; the large-reactor file is the loser-channel
counterfactual — international spillover plus x × the SMR program), 20+20 financials/construction-times files, and
the shared `construction_schedules_mc.csv`. The cases mandate **SMR capacity only**: the
mandate's tech set is switchable (`GSw_NuclearCapMandateTechScen` →
`inputs/nuclear_learning/nuclear_cap_mandate_techs_{scen}.csv`), and these cases pair the
`smr` set with `{scen}_smr` **additions-basis** trajectories (cumulative post-2030 builds
incl. retirement backfill — exactly the notebook's own `cumsum(GW_ADD)`, asserted in QA-5e),
so the large counterfactual can never fulfill the mandate and is never economic without it.
Every written file is round-trip checked (QA-5, both cases files).
Launch the phase with `python runreeds.py -b <batch> -c nuclearlearning_smr100`. Cheap test
runs: env var `SMR100_DRAWS`.
