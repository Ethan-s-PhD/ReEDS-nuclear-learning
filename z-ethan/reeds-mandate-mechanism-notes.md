# ReEDS-hybrid-plant branch — nuclear mandate & learning machinery (survey 2026-07-30)
 
Survey of the existing implementation in `ReEDS-hybrid-plant` relevant to the nuclear learning paper (see `claude/paper-plan.md`). Bottom line: **the capacity mandate the plan called "to be replicated" already exists in this branch, fully wired**, along with the endogenous-learning engine (appendix machinery) and a Python implementation of the duration→IDC financing chain.
 
## 0. PORT APPLIED (2026-07-31) — status
 
Ethan forked upstream `ReEDS-Model/ReEDS` and cloned to `~/code/research/ReEDS-nuclear-learning` (branch `nuclear-learning`). The full port was **applied directly into the clone** from the Cowork session (23 files written; anchor-based insertions verified; Python files syntax-checked; GAMS conditionals balanced 16/16).
 
**Upstream restructured since the hybrid branch — layout mapping used by the port:**
 
| Hybrid-plant | Upstream fork |
|---|---|
| `b_inputs.gms` | `reeds/core/setup/b_inputs.gms` |
| `c_supplymodel.gms` | `reeds/core/setup/c_model.gms` |
| `d_solveoneyear.gms` | `reeds/core/solve/3_solve_oneyear.gms` |
| `d1_financials.gms` | `reeds/core/solve/2_financials.gms` |
| `tc_phaseout.py` | `reeds/core/solve/1_tc_phaseout.py` |
| `e_report.gms` / `e_report_params.csv` | `reeds/core/terminus/report.gms` / `report_params.csv` |
| `runbatch.py` | `runreeds.py` |
| `runfiles.csv` | `reeds/input_processing/runfiles.csv` |
| `nuclear_learning.py` (root) | `reeds/core/solve/nuclear_learning.py` |
 
**What was applied:** mandate switches (24 cases.csv rows — PoolHybrid/TESIsland dropped), trajectory loading + `firstyear_nuclear` in `b_inputs.gms`, mandate equations in `c_model.gms` (LHS `nuclear(i)` only — hybrid limbs stripped), learning sets/params in `b_inputs.gms`, learning override block before the `2_financials.gms` include in `3_solve_oneyear.gms` (base-tech OCC + ccmult channels only), **new dual reporting** in `report.gms` + 4 rows in `report_params.csv` (`nuclear_cap_price(_ub)(_raw)`; pvf_onm rental basis default, crf alternative documented, raw `.m` for the audit), 4 runfiles.csv rows (grouped after `construction_times.csv`), 4 runreeds.py insertions (engine call after tc_phaseout in the seq loop; post-loop `check` call; `outputs/nuclear_learning_data` mkdir; timetype=seq guard), the adapted engine (PoolHybrid/TESIsland defaults flipped to 0; hybrid file reads already gracefully guarded; path references updated), and `inputs/nuclear_learning/` verbatim from the hybrid repo (6 trajectory CSVs — original byte format `*t,MW` with values matching the session's independent regeneration exactly — plus foreign_experience low/mid/high, historical_stock, inl_duration_curves, 3 generator scripts). Upstream `environment.yml` already pins `gdxpds==4.0.0`, so no env change.
 
**Ethan's next steps:** review `git diff`, commit as a small series (suggested: mandate / dual reporting / engine / inputs), push the branch; then shakedown runs.
 
**Shakedown watch items (beyond §6's run list):**
 
1. **gdxpds version jump:** hybrid ran the engine on gdxpds 1.4.0; upstream pins **4.0.0** — verify `to_dataframes`/`to_gdx` API compatibility in the engine smoke test.
2. **GAMS switch macros:** the learning block conditions on `%GSw_NuclearLearning%` etc. — verify upstream still passes case switches as GAMS macros into `3_solve_oneyear.gms` the same way (first shakedown run will fail loudly if not).
3. **`nuclear(i)` subset:** confirm it includes `nuclear-smr` in the upstream i-subsets (mandate LHS relies on it).
4. **Winner-only mandate (paper design, still open):** the ported constraint mandates both nuclear techs jointly; the v4 winner-take-all design needs a per-tech variant or the loser excluded — decide during Step 0.
5. `2_financials.gms` confirmed unchanged in the ccmult chain (`cost_cap_fin_mult = ccmult/(1−tax_rate)×…`), and the `Sw_PCM` guard, `firstyear` pattern, cases.csv layout, runfiles.csv header, and tc_phaseout scheduling anchor all matched upstream — drift checklist passed on those points.
---
 
### §0.1 Step 0 build session (2026-07-31, evening) — gap found & fixed; shakedown launched; Track B built

1. **Port gap found and closed.** The engine's experience feedback loop was **unwired**: `nuclear_learning.py` reads `outputs/nuclear_learning_data/cumulative_inv_{t}.gdx` (`nuc_inv_by_tech`, `nuc_cost_cap_applied`, `nuc_ccmult_applied`), but the hybrid branch's `d3_data_dump.gms` block was dropped when upstream renamed the file to `reeds/core/solve/6_data_dump.gms` — so learned OCC stayed pinned at BOAK and `check` passed vacuously (items 2–3 silently skipped). Fixed: a guarded dump block appended to `6_data_dump.gms` (runs per solve year after the solve; strict post-anchor `yeart>anchor` convention matching check item 5; uses `nuclear_learning_exptech/basetech` because `nuclear(i)` is destructively re-filtered at line 107 of that file; storage-hybrid symbols intentionally omitted — `_read_applied` degrades them gracefully).
2. **Utah shakedown configured** (laptop-scale; NLR not needed): `cases_utshakedown.csv` with 4 cases — `ut_floor` (mandate **500 MW @ 2035**, floor), `ut_equal` (=2 flip), `ut_slack` (2033=500/2035=300 → 2035 dual must be 0), `ut_learn` (2033=500/2035=1000 + `GSw_NuclearLearning=1`, exercises the §0.1(1) fix with real experience). All on `GSw_Region=st/UT` (1 BA under z90), `endyear=2035`, yearset `2010_2020_2026_2029_2033_2035`, `GSw_Retire=0`. **Note: `firstyear_nuclear = 2033`** (`this_year` 2025 + `years_until_endogenous` 8) — a 2032 mandate year would be silently guard-skipped *and* unbuildable, hence the 2033/2035 design. Trajectories `nuclear_cap_trajectory_ut_{shakedown,slack,learn}.csv`; scen tokens added to the cases.csv Choices cell.
3. **Pre-flight passed:** `reeds` env imports (gdxpds 4.0.0, gamsapi 53.5.0, pandas 3.0.5); GAMS 48.6 + CPLEX licensed; gdxpds↔GAMS-48 GDX round-trip verified both directions at full precision (watch items 1–2 retired); `parse_cases` accepts the new cases file. Windows note: the env must be *activated* (env `Library\bin` on PATH) — invoking `python.exe` by absolute path crashes matplotlib and gdx DLL delay-loads.
4. **Shakedown launched;** first run (`utshake_ut_floor`) triggered the one-time remote input sync (multi-GB renewable-profile h5 downloads) which dominates wall-clock; results land in `runs/utshake_*`. A6-checklist verification pending run completion.
5. **Track B built** (`z-ethan/mc/mc_cost_trajectories.ipynb`, 53 cells, executes end-to-end): per-trajectory MC (6 × 5,000), financing replication (ccmult regression 1.268124 reproduced; `cost_cap_fin_mult_noITC` replicated from the fork's own inputs), winner-take-all (SMR wins 63–71% of draws; ranking-functional invariance 88–99% — issue-8 regroup evidence), 18 P5/P50/P95 joint-draw cases exported in ReEDS formats (`cases_nuclearlearning_mc.csv` validates against cases.csv Choices), fragmentation figure (median penalty 10%, P90 31.5%, never negative), hindcast paper figure, QA suite QA1–QA13 green (QA10 = ReEDS-run cross-check pending the shakedown; set `REEDS_RUN_DIR` in S1).
6. **§6 to-do 4 done:** `US_SCHEDULES.csv` regenerated as single source of truth (notebook S2 exports it; `_generate_cap_trajectories.py` rewritten to read it); **`cop29` → `cop28` renamed** (file, Choices, generator); duration granularity resolved via `financials_tech(i,t).construction_sch` labels + `construction_schedules_mc.csv` `NL1–NL10`/`NS1–NS10` columns (ccmult identical by construction — `construction_times_*.csv` only feeds tax-credit safe-harbor timing, not IDC). Stale `_generate_sensitivity_casefile.py` quarantined (`.stale`; emitted `GSw_StorageHybrid*` switches this fork's `parse_cases` rejects).

### §0.2 Convention fix + basis unification (2026-07-31, late)

1. **Experience-base convention made per-tech (Ethan's design decision).** The full-stock flag was crediting the ~140-unit US LWR fleet to *both* techs' anchor bases, flattening SMR curves too and flipping the intended effect — full-stock draws *advantaged* large (P(large wins) 41–58% vs ~15% tiny-base). Semantics clarified: the convention states *where on its own curve each tech sits at the (unchanged) BOAK anchor*; the US stock applies to **large only** — the empirical SMR LR range (3–16%) already embeds prior-LWR benefits (crediting the stock would double-count and violate the zero cross-tech spillover convention); the θ-weighted foreign historical stock still enters the SMR cross-firm channel. After the fix: full-stock disadvantages large (P(large wins) 4–10%), overall SMR wins ~89%; fragmentation penalty median ≈20%, P90 ≈42%. Mirrored in the ReEDS engine (`nuclear_learning.py`: `h_us` zeroed for the smr parent). Documented in the notebook as D8′ (S5 Step 6) + S4 table.
2. **GW basis unified**: the notebook's plot + experience counting now use the same literal-GW-minus-3 basis as the mandate files (the reference notebook's proportional index/100×97 conversion produced level-dependent deltas from nominal targets).
3. **Shakedown results (A6):** all four cases ran to completion (fake-data profiles). ut_floor: exactly 500 MW (SMR) built in 2035, floor dual +282,815 $/MW-yr, constraint generated only in 2035; **deflation convention resolved empirically** — raw/converted = 1/crf(2035) exactly, i.e. in seq mode pvf_onm = 1/crf and the rental and crf conventions coincide; the reported dual is an annualized $/MW-yr rental price. ut_equal: capacity pinned at 500, ceiling slack (ub dual 0, zero-suppressed). ut_slack: 500 built 2033 persists vs 300 floor in 2035 — 2033 dual +237,631, 2035 dual exactly 0, 200 MW overbuild visible. QA10 financing cross-check: notebook ccmult == run's ccmult.csv to 3e-7 (12 tech-year values). ut_learn = engine smoke: **PASSED end-to-end** — the §0.1(1) dump fix works: `cumulative_inv_{2033,2035}.gdx` written; at 2035 the engine read 500 MW of 2033 experience, applied occ_factor 0.9923 (learned OCC 3,712,738 → 3,683,996 2004$/MW) with learned durations/ccmult (large 79 mo/1.3214, SMR 53 mo/1.1254); capacity hit both mandate rungs exactly (500 → 1000 MW); `check` mode **16/16 ALL PASS with the applied-value items 2–3 actually exercised** (previously silently skipped); the only no-experience WARNING is the correct 2033 one. gdxpds 4.0 and the `%GSw_*%` macro passing are thereby proven in anger.
4. **New fixes flushed by the shakedown:** upstream `recf.py` crash when `GSw_OfsWind=0` (unbound `df_windofs`; empty-frame fallback added); yearly-solve GAMS calls lacked the `GSw_NuclearLearning*` macros (watch item 2 confirmed — added to `solvestring_sequential` in `reeds/inputs.py`; the v8 learning block had never compiled); `nuclear_learning.py` missing the `sys.path` stanza for `import reeds` (script invocation); `GSw_FakeData=1` + `GSw_OfsWind=0` + `GSw_PRM_StressModel=user_utshake` (new `stressperiods_user_utshake.csv`) for laptop shakedowns.

**Repo-strategy decision + port kit (addendum, 2026-07-31, superseded by §0):** the fork/branch/port strategy was decided while GitHub was gated from the sandbox and the desktop bridge was down; a self-contained port kit (`reeds-nuclear-learning-port-kit.zip`) was prepared and delivered as the intermediate artifact. All of its pending extractions were completed and applied once the desktop reconnected; the kit remains a reference for the apply rationale, the upstream-drift checklist, and the shakedown-run list.
 
## 1. Capacity mandate — EXISTS, complete (hybrid survey)
 
**Switches (`cases.csv`):**
 
- `GSw_NuclearCapMandate` — `0` off; `1` **floor** (capacity ≥ trajectory); `2` **equality** (floor + upper bound pair). The issue-6 toggle the plan wanted already exists.
- `GSw_NuclearCapMandateScen` — selects `inputs/nuclear_learning/nuclear_cap_trajectory_{scen}.csv`. **All 6 locked trajectories have files:** `eia_aeo_high`, `abou_jaoude`, `iaea_high`, `mckinsey`, `cop29`, `eo2025`. Values are the `US_SCHEDULES` read as literal GW **minus a flat 3 GW** (undoes the 97→100 base-year rounding). 2050 national totals: 114.3 / 131 / 169.3 / 197 / 297 / 397 GW.
- `GSw_NuclearCapMandate_Scale` — fraction of the national trajectory for sub-national runs.
**Equations (hybrid `c_supplymodel.gms`; ported to `c_model.gms` with LHS `nuclear(i)` only):**
 
- `eq_nuclear_cap_mandate(t)`: Σ CAP ≥ `nuclear_cap_trajectory(t)`. **National** (sum over r), **annual**, **cumulative-capacity basis** (existing + new, net path). Skipped before `firstyear_nuclear` and under `Sw_PCM`.
- `eq_nuclear_cap_mandate_ub(t)`: same LHS ≤ trajectory, active only when `=2`. **Equality mode is a floor+ceiling pair**: the net capacity price is `eq_nuclear_cap_mandate.m + eq_nuclear_cap_mandate_ub.m` (ub marginal ≤ 0). Equality can be infeasible if prescribed/existing capacity exceeds the scaled trajectory.
**Implications for the plan:** the dual is on **national cumulative capacity in year t** — a capacity *rental* price per year, not a per-build price. The ITC conversion must integrate the year-t duals over the years a build's capacity remains mandated-marginal (or difference the cumulative duals); the sequential (`seq`) timetype means each year's marginal is in that year's objective PV terms.
 
## 2. Dual reporting — gap in hybrid, CLOSED in the fork (§0)
 
Hybrid never reported `eq_nuclear_cap_mandate.m`. The fork now computes `nuclear_cap_price(t)`, `nuclear_cap_price_ub(t)` and raw `.m` twins in `report.gms`, registered in `report_params.csv`. **To verify at the pilot logging audit:** the deflation convention for a capacity constraint under sequential solves — rental basis `(1/cost_scale)(1/pvf_onm)` (default, matches reserve margin/co2_price) vs annualized `(1/cost_scale)·crf(t)` (matches RE_gen_price_nat); the raw `.m` is reported precisely so the issue-5 formula can be audited. Both marginals dump in equality mode.
 
## 3. Endogenous learning engine — EXISTS, ported (appendix machinery)
 
- `GSw_NuclearLearning` (+ `_OCC`, `_Duration` channels, and ~18 parameter switches for LR/BOAK/convention/vendors/CES/spillover/duration-lambda/foreign-scen) — a **between-years Python engine**, sequential timetype only, scheduled after tc_phaseout; writes a per-year gdx that the solve loop reads **before the financials include**, overwriting `plant_char0`/`cost_cap` (OCC) and `ccmult` (duration).
- Ports the notebook's deterministic learning engine (Abou-Jaoude eq. 12 market-split + CES generalization + INL series-reduction durations), with US deployment endogenous = ReEDS's own cumulative post-anchor investment. Each case is one deterministic parameter world.
- Built-in **`check` mode**: experience == INV dump; applied `cost_cap`/`ccmult` == engine values; `occ_factor` matches the analytic formula and is monotone. This is the QA harness the appendix check needs.
- Support files in `inputs/nuclear_learning/`: `foreign_experience_{low,mid,high}.csv` (international spillover stocks — the u analogue, discretized), `historical_stock.csv`, `inl_duration_curves.csv`, generator scripts `_generate_{cap_trajectories,foreign_experience,sensitivity_casefile}.py`.
**Design note (flag for discussion, does not change the v4–v6 decisions by itself):** with the mandate in **equality** mode and the engine's parameters fixed per case, the "endogenous" engine is de facto exogenous in *total* deployment — but the **SMR/large split remains ReEDS's choice**, and sequential solves make that choice *myopic* (rich-get-richer lock-in rather than strategic standardization). The paper's exogenous-CSV route (winner-take-all computed in the MC, both-tech trajectories shipped) deliberately removes that ambiguity; the engine route is an alternative closure that leaves the split endogenous. Keep the engine as appendix machinery per the plan — the comparison of the two routes is itself appendix-grade material.
 
## 4. Existing run design artifacts (hybrid repo; predate the v5/v6 plan — review before reuse)
 
- `cases_nuclearlearning_nrel.csv`: per-trajectory column families `{eia, aj, mck, cop29, eo}` × `{ctrl, p05, p25, p50, p75, p95, lit, lr_lo, lr_hi, boak_lo, boak_hi, conv, vend, ces, spill, lam}` — percentile + one-at-a-time sensitivities over the **engine's parameters**, `GSw_NuclearCapMandate=2` (equality) default, `timetype=seq`, endyear 2050. **iaea_high has a trajectory CSV but no column family here.** Superseded for the main matrix; useful as case-file mechanics template.
- `cases_nuclearlearning.csv`, `cases_nuclearlearning_sensitivity.csv`: earlier variants.
## 5. Cost/duration wiring paths (for the case generator; paths confirmed identical in the fork)
 
- **OCC:** `plantchar_nuclear` / `plantchar_nuclear_smr` switches → `inputs/plant_characteristics/{name}.csv` (currently ATB 2024 files). Per-case learned-cost files follow this pattern.
- **Durations:** `construction_times_suffix` → `inputs/financials/construction_times_{suffix}.csv`; same per-case file + switch pattern.
- **Financing chain:** `2_financials.gms`: `cost_cap_fin_mult(i,r,t) = ccmult(i,t)/(1−tax_rate(t)) × …` (`_noITC`, `_no_credits` variants). `ccmult` is the duration-dependent IDC multiplier. **`nuclear_learning.py` implements the duration→ccmult mapping in Python** and verifies it against what GAMS applies — port source for the notebook's financing-factor replication (triply load-bearing: winner selection, case extraction, subsidy translation).
## 6. Remaining ReEDS-side to-dos
 
1. Ethan: review diff, commit series, push `nuclear-learning`.
2. Shakedown runs (short horizon, reduced spatial resolution; GAMS required — NLR or local): floor smoke test → `nuclear_cap_price` in outputs with plausible sign/magnitude; equality flip (=2, both marginals); slack floor (cheap-nuclear, dual=0 + overbuild visible); engine smoke test (`GSw_NuclearLearning=1`, `check` passes — watch gdxpds 4.0); financing cross-check (notebook ccmult vs ReEDS).
3. Resolve winner-only-mandate wiring (per-tech constraint variant vs loser exclusion) during Step 0.
4. When the new MC notebook exists: regenerate `US_SCHEDULES.csv` + trajectory CSVs via `_generate_cap_trajectories.py` (rename `cop29` → COP28 tripling pledge per the plan's citation note; keep the −3 GW basis adjustment documented in methods).
 