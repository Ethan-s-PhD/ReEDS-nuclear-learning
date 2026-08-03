# Nuclear Learning Paper — Project Plan

**Status:** Step 0 build half complete; NLR regroup + pilots next (August 2026). **v9, updated 2026-08-03.** This document is the authority on the paper's methods and architecture. The v2.4 analysis notebook (`mc_nuclear_smr_learning.ipynb`) is **reference-only**; where any older artifact disagrees with this plan, this plan wins.

## Version history (compressed)

- **v2** (07-28, after the fit assessment in the *ReEDS paper development* project): issue 2 (2030 anchor) resolved; terminology locked ("learning-consistent required subsidy"); subsidy deliverables expanded to rate + fiscal bill + transfer share; appendix check pre-registered both ways; framing commitments added; issues 6–7 opened.
- **v3** (07-30): Step 0 added — pipeline build + pilot runs before the matrix is spent.
- **v4** (07-30): issue 1 resolved — **winner-take-all technology assignment computed in the MC**; both-tech trajectories in every run (loser learns from international spillover only); 12-run sub-experiment dropped; standardization result becomes the zero-run MC fragmentation figure; issue 8 opened.
- **v5** (07-30): issue 3 resolved — 6 schedules locked with renames; **per-trajectory MC architecture** (separate MC per schedule, no weights, no schedule-as-random-variable); issue 9 (u drawing) opened and resolved same day (independent, full envelope).
- **v6** (07-30): issue 4 resolved — high/mid/low = **P95/P50/P5 of calculated financed CAPEX as joint draws** (duration enters via IDC); ReEDS-side survey: mandate mechanism found complete in the hybrid branch, dual reporting identified as the one gap; wiring paths confirmed.
- **v7** (07-31): ReEDS repo strategy — **fork upstream `ReEDS-Model/ReEDS`, branch `nuclear-learning`**, port with all storage-hybrid limbs stripped; port kit prepared.
- **v8** (07-31): **port applied** — 23 files written into the fork clone, adapted to upstream's restructured layout, including the new dual reporting. Track A code work complete; shakedown runs next, concurrent with the Track B notebook build.
- **v9** (08-03): **Step 0 build half complete.** Track B built at `z-ethan/mc/` and extended beyond scope: per-schedule MCs at **10,000 draws** (doubling the planned 5,000); `winner_boundary.ipynb` (issue-8 evidence); **`mixed_build_optimizer.ipynb` stress test** — a per-draw optimizer over 20-year SMR-share profiles beats the best pure strategy in only 6 of 60,000 draws, closest margin 0.22%, wins vanish undiscounted ⇒ pure single-technology programs are truly optimal. **Issue 8 resolved: deployment assumed 100% SMR** (SMR wins 87–90% of draws in every schedule; ranking functional confirmed robust). Production export `smr100_case_export.ipynb` supersedes the winner-take-all 18-case export; `cases_nuclearlearning_smr100.csv` + full ReEDS input set written and round-trip checked. Hindcast nuance recorded (France/US negative observed rates fall below the sampled support).

## Current status

**Done:** issues 1, 2, 3, 4, 8, 9 resolved (see Decisions). ReEDS fork ported end to end (v8) and committed (fork heads a0c5ea9 → 14ee3fd across the Track B exports); a shakedown run directory (`runs/utshake_ut_learn`) is wired in as the financing cross-check target. **Track B complete** — the MC notebook repo at `z-ethan/mc/` covers the full planned scope plus three extensions (winner-boundary analysis, mixed-build stress test, smr100 production export); details in Step 0 below. **Step 1 output exists:** the 18 production cases (`cases_nuclearlearning_smr100.csv` + 36 plantchar + 18+18 financials/construction-times files) are exported and QA'd, pending NLR-regroup ratification of the 100%-SMR supersession.

**Now:**

1. **NLR regroup** — ratify the 100%-SMR supersession and the ranking functional with the evidence tables in hand (`win_probabilities.csv`, `wb_*.csv`, `winner_ranking_invariance.csv`, `mixed_build/verdict_by_schedule.csv`); run the non-CAPEX parameter check (FOM, CF, lifetime).
2. **Step 0 pilots** — 2–3 smr100 cases via `python runreeds.py -b <batch> -c nuclearlearning_smr100` (pilot purposes unchanged; see Step 0).

**Then:** issues 5 + 6 → issue 7 + Step 4 budget variant → documentation (2030 anchor, hindcast-support caveat).

## Core idea

Take a set of exogenous US nuclear deployment trajectories, compute the cost trajectories they imply under uncertain learning parameters (learning rate, cross-firm spillover, international spillover, domestic and international builds), force each deployment trajectory into ReEDS as a mandate paired with its consistent cost trajectory, and read the shadow price on the capacity constraint as the subsidy required to make that deployment happen. Endogenous learning inside ReEDS is demoted to an appendix consistency check, not the main method.

**Naming and positioning.** The output quantity is the **learning-consistent required subsidy** — not "required cost." Mai et al. (2019) prescribe deployment and read the dual as a cost target with cost assumptions canceled out; here costs are *prescribed* (conditioned on the deployment they accompany) and the dual is the residual subsidy. The methodological contribution is the consistency closure: deployment-conditional costs feeding a deployment mandate, so cost and deployment are never contradictory. State the distinction from Mai explicitly in the methods; a referee who knows that paper will check.

## Research questions

1. **What subsidy level is needed to achieve each deployment target?** Measured as the marginal cost on the ReEDS capacity (mandate) constraint in $/MW. Because an ITC applies uniformly to all builds in a year, the dual reads directly as the **required uniform ITC rate**. Deliverable is three numbers per scenario: the rate, the fiscal bill (rate × all builds), and the inframarginal transfer share. The transfer is not a bug — it is a property of uniform instruments — and quantifying it is part of the finding.
2. **What conditions are needed for ATB cost trajectories to happen?** Where do the ATB nuclear cost projections sit within the learning-parameter-conditional cost ranges, and what combination of deployment, learning rate, and spillover would deliver them? Audience: every modeler who consumes ATB nuclear costs. RQ2 requires no ReEDS runs — complete after Step 2 — and gets a full results subsection with its own deliverable sentence. May seed a standalone input-audit paper.

## Framing commitments

- **Working mechanism hypothesis:** the subsidy is a *bridge* — the dual should decay toward zero as the fleet walks down the learning curve. The shape of the dual trajectory, not its level, is the durable object; figures are designed around dual trajectories. (Secondary mechanism: experience fragmentation — quantified by the MC fragmentation figure.)
- **Conditional-cost discipline:** every MC cost fan is conditional and never presented as a cost projection; every caption and abstract sentence preserves the conditional. The per-trajectory MC architecture makes this structural: no unconditional cost distribution exists anywhere in the analysis.
- **Conditional-commitment discipline (v9):** all production cases additionally condition on the 100%-SMR commitment. Report the win probabilities (SMR wins 87–90% of draws) so the ~10–13% of large-favorable futures stay visible; the wb margin tables quantify what committing wrongly would cost.
- **Advocacy defenses:** report implausibly-large subsidies as prominently as small ones; report zero-dual and overbuild cases; never rank trajectories by desirability — the paper prices them, it does not endorse them. The paper also does not *weight* them: schedule probability weights are gone by design.
- **Report the results that undercut us:** the inframarginal transfer, the appendix check whichever way it comes out, and any slack-mandate / sign-flipped-dual cases.

## Tools

1. **ReEDS — fork of upstream `ReEDS-Model/ReEDS`, branch `nuclear-learning`** (ported v8; local clone `~/code/research/ReEDS-nuclear-learning`). Mandate, dual reporting, and learning engine in place; layout mapping and watch items in `claude/reeds-mandate-mechanism-notes.md`.
2. **MC cost-trajectory notebook repo (`z-ethan/mc/` in the fork clone; built v9)** — one separate Monte Carlo per build trajectory (**10,000 draws each**, seed 20260715, named per-stream seeding) producing **OCC and construction-duration trajectories jointly** (same draws, same copula) for SMR and traditional (large) nuclear, plus three companion notebooks: `winner_boundary.ipynb` (winner diagnostics), `mixed_build_optimizer.ipynb` (mixed-build stress test), `smr100_case_export.ipynb` (**the production case generator**). Port source: the v2.4 reference notebook.
3. **Endogenous-learning engine** (`reeds/core/solve/nuclear_learning.py` in the fork, hybrid branches defaulted off) — appendix check only.

## Methods / analysis pipeline

### Step 0 — Pipeline build + pilot runs

**Build half — COMPLETE (v9).**

**Track A — ReEDS fork (code complete v8; committed).** Mandate equations (LHS `nuclear(i)` only), trajectory loading + `firstyear_nuclear`, 24 switches, six trajectory CSVs, dual reporting (converted + raw, floor + ub; **deflation convention still to verify at the pilot logging audit**), engine + scheduling + timetype guard, runfiles wiring. Shakedown run directory `runs/utshake_ut_learn` exists and is the notebook's financing cross-check target.

- Residual wiring question, now sharpened by the smr100 decision: the ported constraint mandates both nuclear techs jointly (`nuclear(i)`), while deployment is assumed 100% SMR. Large nuclear ships at international-spillover-only costs, so it should lose on cost — but ReEDS *could* satisfy the mandate with large builds. The pilot **large-build check** (formerly loser-build check) covers this; a per-tech (SMR-only) mandate variant remains the fallback if large builds are material.

**Track B — MC notebook repo (COMPLETE, built at `z-ethan/mc/`).** As-built record:

- **`mc_cost_trajectories.ipynb`** — the MC engine. Per-trajectory architecture as planned, but at **10,000 draws per schedule** (60,000 total; MC draws are effectively free, so the plan's 5,000 was doubled). All planned ports landed: OCC engine (Abou-Jaoude eq. 12 generalized, CES aggregation, spillover), INL duration model, PRIS/RDS-2 loader (verbatim copies), permanent regression cells. Financing-factor replication done as `OCC × cost_cap_fin_mult_noITC` with ccmult at the draw's learned duration (`2_financials.gms` replication, S7). Schedule single-source-of-truth done: notebook exports `US_SCHEDULES.csv`; mandate CSVs regenerate via `_generate_cap_trajectories.py`. Fragmentation figure produced (`figures/fragmentation_penalty.png`). Every written file round-trip checked (S15). Per-draw arrays exported to `mc_perdraw.npz` (S10b, gitignored) for downstream analysis.
- **`winner_boundary.ipynb`** — issue-8 regroup evidence. Key outputs: **SMR wins 87.9–90.0% of draws** across schedules (`win_probabilities.csv`), median SMR advantage 14–25% of financed CAPEX rising with schedule ambition (`wb_headline.csv`), break-even SMR premiums ~$1,260–2,060/kW at U0=0.1–0.3 tiny-base (`wb_breakeven.csv`), and **ranking-functional invariance**: winner matches the default (discounted, schedule-weighted) in ~99% of draws undiscounted and 85–95% unweighted (`winner_ranking_invariance.csv`).
- **`mixed_build_optimizer.ipynb`** — mixed-build stress test, deliberately stacked *toward* mixing (drawn cross-tech spillover up to 30% each way; independent per-tech (lr, boak) pairs conditioned only on `boak_smr > boak_large` and `lr_smr > lr_large`; per-draw optimizer over 20-year SMR-share profiles). Verdict: mixed beats the best pure strategy in **6 of 60,000 draws** (closest margin 0.22%, median winning advantage 0.13%, none persist undiscounted). QA pins the engine bit-for-bit to the main notebook at "off" settings and reproduces the S13 fragmentation result. **The v4 mix contingency is closed** — no representative endogenous-learning runs or split mandates needed (unless pilots show material large builds).
- **`smr100_case_export.ipynb`** — **the production case generator**, superseding the main notebook's winner-take-all 18-case export. Re-runs the identical MC worlds (QA-0 asserts draw-for-draw match against `mc_perdraw.npz`), assumes the whole program feeds SMR learning in every draw, ranks each schedule's draws by discounted SMR program cost, selects P5/P50/P95 joint draws, and exports 18 cases: `cases_nuclearlearning_smr100.csv`, 36 plantchar files (the large-reactor file is the international-spillover-only counterfactual), 18+18 financials/construction-times files, shared `construction_schedules_mc.csv`. Round-trip checked (QA-5). Generated 2026-08-03.
- **Validation results worth carrying forward:** v2.4 continuity — large-reactor percentiles within ±3% of the reference notebook; SMR P50s run 15–23% *below* v2.4 (architecture changes: rank-coupling and schedule weights removed, independent u; documented in `v24_continuity_report.csv`). Copula-set sensitivity mild (`copula_sensitivity.csv`). Tornado/Spearman: financed CAPEX driven by BOAK anchor, experience-base convention, and learning rate; u and s near-zero for cost levels (`sensitivity_spearman.csv`).
- **Hindcast nuance (flag for Step 2):** Korea's realized +13%/doubling sits at P77 of the sampled range, but France (−15%) and the US (−30%) fall **below the sampled support** — the MC excludes negative learning by design. The paper-body hindcast claim must be framed as "reproduces successful-program experience" with the negative-learning exclusion stated, not as reproducing all historical experience.

**Pilot half (after NLR regroup) — NEXT.** Pilot subset: one modest trajectory (EIA 2026 AEO high or Abou-Jaoude mod) + one aggressive (2025 EO), optionally one low-cost/aggressive to probe zero-dual/overbuild — drawn from the 18 smr100 cases (`python runreeds.py -b <batch> -c nuclearlearning_smr100`). Purposes: bug flushing (mandate + dual reporting with real trajectories; both-tech cost + duration ingestion; units/dollar-year; tech mapping); financing-factor validation (notebook vs ReEDS — a silent mismatch corrupts case selection); dual reconnaissance for issue 6 (the 1↔2 switch makes floor-vs-equality a zero-code flip); logging audit for issue 5 (including the deflation convention); **large-build check** (material large builds under the joint mandate ⇒ SMR-only mandate variant); first look at dual-decay shape. Pilots and shakedowns are diagnostics, outside the paper's run count (~3 pilot runs).

### Step 1 — Cost ranges for the 6 trajectories

**Done as the smr100 variant (v9), pending regroup ratification.** P5/P50/P95 of discounted SMR program cost per schedule, as actual joint draws (registered in `exports/smr100/selected_draws.csv`), exported as **18 ReEDS-ready cases** carrying both techs' OCC + duration with the mandate schedule attached.

### Step 2 — Compare cost ranges against ATB

Overlay ATB nuclear cost projections on the per-trajectory cost fans → answers RQ2. Inputs ready: `mc_occ_percentiles_by_schedule.csv` + the OCC fan figures. **External anchoring:** hindcast cells promoted to paper body, **with the support caveat** (Korea at P77; France/US negative rates outside the sampled support). The ATB comparison is NREL-benchmarking-NREL — the one-lab problem bites twice; an independent learning-model comparison or non-NREL collaborator is the cheapest upgrade. Basis note: ATB comparison is on OCC, not financed CAPEX — keep bases straight vs the program-cost-ranked case selection.

### Step 3 — ReEDS runs (18 base cases)

Each smr100 case into the fork: both techs at conditional OCC + duration, deployment as a capacity mandate (SMR expected to take it all; large is the spillover-only counterfactual).

- Lock the constraint form (issue 6) before production runs, from pilot evidence.
- Read the mandate dual = required uniform ITC rate. The constraint is national *cumulative* capacity per year — a rental price — so the issue-5 formula maps year-t duals to per-build subsidies (integrate over mandated-marginal years or difference the cumulative duals); equality mode has two marginals.
- Compute fiscal bill + transfer share (issue-5 formula written before runs; logging verified in Step 0 pilots).
- **Benchmark against real instruments** (48E/45Y nuclear treatment, historical support, Vogtle's realized stack): "trajectory X needs N× the current ITC" is both external anchor and headline.

### Step 4 — Sensitivities

Base plan: 18 cases × 6 sensitivities (high/low gas, high demand, low/high RE+storage costs, transmission constrained) = 108 + 18 = **126 runs**. **Alternative (decision needed):** sensitivities on mid-cost cases only → 18 + 36 = 54 + spot checks; with the sub-experiment dropped, decide purely on whether cost × sensitivity interactions are worth ~72 runs. **Before the matrix is spent, choose the robustness invariant** (issue 7).

### Appendix — Endogenous-learning consistency check

Take a scenario's implied ITC, run the fork with endogenous learning and that ITC (no mandate), check whether deployment is reproduced. Machinery ported and verified via the engine's `check` mode. Sequential-solve caveat: the engine is myopic, which shapes what "decentralizing the target" means; ReEDS also picks its own tech winner — whether it picks SMR is part of the interpretation.

**Pre-registered readings, reported whichever way it comes out:** pass ⇒ method validated. Fail ⇒ a finding, not a failed validation — learning-by-doing makes the problem non-convex, exactly where marginal-price instruments can fail to decentralize a target (multiple equilibria; no-build lock-in): "ITC targets sized without learning are unreliable in general"; consider promoting out of the appendix. Controls before attributing failure to learning economics: foresight, solver tolerance, the translation formula itself.

## Decisions

- **Exclude hybrid storage nuclear** — structural in the fork (all storage-hybrid machinery stripped; mandate LHS is `nuclear(i)` only).
- **Exogenous learning is the main method**; endogenous learning is appendix-only. Learning calculations are done **outside ReEDS**.
- **ReEDS repo (v7–v8):** fork of upstream `ReEDS-Model/ReEDS`, branch `nuclear-learning`; port applied 2026-07-31 (see notes doc §0). Constraint definition on record: national, annual, cumulative capacity, from `firstyear_nuclear`; equality = floor + ceiling pair with two marginals; dual reporting in `report.gms`/`report_params.csv`.
- **New repository, per-trajectory MC (v5, built v9):** separate MC per trajectory, **10,000 draws each (v9; up from the planned 5,000)**, OCC + duration jointly; no schedule weights — the paper does not predict how much nuclear the US will build.
- **u convention (v5):** drawn independently over the full IAEA Low/High envelope, identically in all six MCs. Coupling role died with the schedule draw; uncertainty role survives (international spillover driver; the large tech's only learning channel).
- **Case extraction (v6, revised v9):** percentile cases as **actual joint draws** — duration enters selection via IDC ("high-cost" can mean slow-to-build, nuclear's actual risk profile). Joint-draw discipline is worth a methods paragraph. **As built (v9):** ranked by discounted, schedule-weighted SMR program cost within each schedule's MC; invariance evidence says the choice barely matters (99% winner agreement undiscounted, 85–95% unweighted).
- **Schedule set locked (v5):** one trajectory per provenance category, 117→400 ambition ladder —
  1. **EIA 2026 AEO high** (117.3) — modeled projection
  2. **Abou-Jaoude mod** (134; renamed — moderate variant, endpoint-verified) — study assumption
  3. **IAEA high** (172.3) — intergovernmental outlook
  4. **McKinsey GEP 2025** (200) — consultancy outlook
  5. **COP28 tripling pledge** (300; renamed from "COP29 target" — the Declaration to Triple Nuclear Energy launched at COP28, Dubai 2023) — pledge
  6. **2025 EO** (400) — policy aspiration
  The notebook-exported `US_SCHEDULES.csv` is the single source of truth (regeneration done v9, incl. the cop28 rename). ReEDS basis: literal GW minus flat 3 GW (undoes the 97→100 rounding) — keep and document.
- **Technology assignment: winner-take-all (v4), resolved to 100% SMR (v9).**
  - **Rationale (v4):** with weak cross-tech spillover, concentration minimizes cost; ReEDS cannot be offered both conditional trajectories as a choice — any split would double-count learning. Pre-computing the assignment is the only one consistent with the consistency closure.
  - **Resolution (v9):** the winner is resolved globally, not per draw or schedule. Evidence: SMR wins **87.9–90.0%** of draws in every schedule (median advantage 14–25% of financed CAPEX); the mixed-build stress test, stacked toward mixing, finds mixed programs beat pure ones in 6/60,000 draws by ≤0.2% ⇒ pure single-tech is optimal and SMR is the tech. All production cases assume **100% SMR deployment**; large nuclear ships as the international-spillover-only counterfactual in every case.
  - **QA:** the pilot large-build check verifies ReEDS doesn't meet the joint mandate with large builds; material large builds ⇒ SMR-only mandate variant (wiring fallback). ~~Mix contingency~~ closed by the stress test (v9).
  - **Convention:** zero domestic cross-class spillover, used consistently in the large-tech trajectories and the fragmentation figure. **Standardization finding preserved at zero run cost** via the MC fragmentation figure (produced v9).
  - **Framing:** report win probabilities and the wb margin tables so the ~10–13% large-favorable tail stays visible.
- **2030 anchor convention (v2):** OCC(2030) = BOAK with no pre-2030 domestic learning (no licensed US reactor can connect before 2030 — describes reality); BOAK anchor range interpreted as embodying international spillover through 2030, so zeroing foreign stocks at the anchor is internally consistent. To-dos: the methods sentence (both halves) + source-vintage caveat.
- **Terminology (v2):** "learning-consistent required subsidy," explicitly distinguished from Mai et al.
- **Appendix check reported whichever way it comes out (v2).** **Pilots and shakedowns are diagnostics, outside the paper's run count (v3/v8).**

## Unresolved issues

1. ~~Technology assignment~~ **Resolved (v4)** — winner-take-all (Decisions).
2. ~~Pre-2030 learning~~ **Resolved (v2)** — 2030 anchor convention (Decisions).
3. ~~Schedule set~~ **Resolved (v5)** — locked with renames (Decisions).
4. ~~Case extraction~~ **Resolved (v6/v9)** — joint draws, ranked by discounted schedule-weighted program cost; invariance evidence in `winner_ranking_invariance.csv`.
5. **Subsidy translation formula** — written before Step 3: (a) required uniform ITC rate, (b) fiscal bill, (c) transfer share; from year-t cumulative-capacity rental duals (two marginals in equality mode; sequential PV terms; verified deflation convention). Depends on issue 6; shares the financing-factor machinery.
6. **Mandate constraint form — floor vs equality.** Floor: dual = 0 when slack, overbuild observable ("needs no subsidy" is a legitimate headline). Equality: prices both directions (negative dual = trajectory is a ceiling; a tax would hold the market down). Lock before Step 3; both forms exist as the 1/2 switch — pilots compare empirically at zero code cost. Fit-assessment instinct: floor, overbuild reported wherever slack.
7. **Robustness invariant** — what must hold in every sensitivity: subsidy level, trajectory ranking, or dual-decay shape? Decide before the matrix is spent; drives reporting and run design.
8. ~~Winner granularity × extraction distribution~~ **Resolved (v9)** — 100% SMR globally (per-draw/per-schedule granularity mooted); ranking functional confirmed by invariance tables; mixed-build contingency closed. Formal ratification at the NLR regroup, evidence tables in hand.
9. ~~u drawing~~ **Resolved (v5)** — independent, full envelope (Decisions).

## Reference implementation (v2.4 notebook — port source, not the paper's code)

Monte Carlo (5,000 draws, seed 20260715) over: learning rates (large U(3–12%), SMR U(3–16%), comonotone), BOAK OCC anchors, spillover scale s × Kim & Verdolini θ ceilings, u over the IAEA RDS-1 Low/High envelope, US schedule (weighted, rank-coupled — superseded), vendor count U{4–8}, experience-base convention (tiny-base vs full-stock), ρ_CES ∈ {−2,−1,0,1}, Gaussian copula with correlation-set sensitivity. Domestic learning: Abou-Jaoude eq. (12) generalized to m vendors, per-vendor BOAK = 2OAK, cross-firm ω·LR (ω = 1/3), international spillover as additive θ-weighted stock. Experience via retirement identity on RDS-2 2025 unit data (`pris_loader.py`); committed pipeline 2025–2034. Durations: INL/RPT-25-84701 Fig. 18 series-reduction, joint with OCC. Permanent regression cells (anchor checks, eq. 11/12 reproduction, hindcasts) — ported; hindcasts to paper body (with the v9 support caveat). OCC basis: $/kW, 2022 USD, IDC-exclusive (ATB) — keep for Step 2. **Not ported:** endogenous-learning scoping, schedule weights/rank-coupling, PCA spanning-set case selection. v2.4 continuity vs the new build: large within ±3%; SMR P50s 15–23% lower (architecture changes, documented).

## Key files

**MC notebook repo (`~/code/research/ReEDS-nuclear-learning/z-ethan/mc/`, built v9 — Track B):** `mc_cost_trajectories.ipynb` (MC engine), `winner_boundary.ipynb` (winner diagnostics; reads `exports/mc_perdraw.npz`), `mixed_build_optimizer.ipynb` (mixed-build stress test), `smr100_case_export.ipynb` (**production case generator**), `pris_loader.py` + `rds2_2025_units.csv` + `pris_data_spec.md` (verbatim from reference repo), `README.md`. `exports/`: percentile tables, `selected_draws.csv`, `win_probabilities.csv`, `wb_*.csv`, `winner_ranking_invariance.csv`, `v24_continuity_report.csv`, `hindcast_positions.csv`, `copula_sensitivity.csv`, `sensitivity_spearman.csv`, `mc_export_metadata.json`, `mc_perdraw.npz` (gitignored), `mixed_build/`, `smr100/` (production selected draws + metadata). `figures/`: cost fans, fragmentation penalty, hindcast, tornado, duration medians, mixed-build maps, smr100 selected draws.

**ReEDS fork (`~/code/research/ReEDS-nuclear-learning`, branch `nuclear-learning`, ported v8):** mandate in `reeds/core/setup/{b_inputs,c_model}.gms`; learning block in `reeds/core/solve/3_solve_oneyear.gms`; engine at `reeds/core/solve/nuclear_learning.py` (also the ccmult port source); dual reporting in `reeds/core/terminus/report{.gms,_params.csv}`; wiring in `runreeds.py` + `reeds/input_processing/runfiles.csv`; trajectories + generators in `inputs/nuclear_learning/`. **Written by Track B (v9):** `cases_nuclearlearning_smr100.csv` (repo root; the 18-case production run matrix), 36 smr100 plantchar files, 18+18 smr100 financials/construction-times files, `construction_schedules_mc.csv`, regenerated `US_SCHEDULES.csv`. Survey + layout mapping + shakedown watch items: `claude/reeds-mandate-mechanism-notes.md`.

**Reference (`ReEDS-hybrid-plant/z-ethan/`, Ethan's machine):** `mc_nuclear_smr_learning.ipynb` (v2.4 port source), `us_nuclear_pooled_learning_model.ipynb`, `2024_v3_Workbook.xlsx` (ATB 2024 — BOAK anchors + Step 2).

## Compute constraint

NLR cluster; **126 runs is the ceiling**. Budget variants: full matrix (126) or mid-cost-only sensitivities (≈54 + spot checks) — Step 4 decision. Pilots (~3) and shakedown runs are outside the count. MC draws are notebook-side and effectively free (6 × 10,000 main + 6 × 10,000 mixed-build + the smr100 re-run).

## Critical path (v9)

1. **NLR regroup** — ratify the 100%-SMR supersession + ranking functional (evidence: win probabilities, wb tables, invariance, mixed-build verdicts); non-CAPEX winner-metric check (FOM, CF, lifetime).
2. **Step 0 pilots** — 2–3 smr100 cases (`runreeds.py -c nuclearlearning_smr100`): issues 5–6 evidence incl. floor↔equality flip; financing validation notebook↔ReEDS; large-build check under the joint mandate; deflation-convention verification; dual-decay first look.
3. Issues 5 + 6 — translation formula + constraint form, together (block Step 3).
4. Issue 7 + Step 4 budget variant (block Step 4 design).
5. Documentation: 2030-anchor methods sentence + source-vintage caveat + hindcast-support caveat (France/US below sampled support).