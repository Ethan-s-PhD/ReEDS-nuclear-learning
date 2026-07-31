# Nuclear Learning Paper — Project Plan

**Status:** Step 0 in progress (July 2026). **v8, updated 2026-07-31.** This document is the authority on the paper's methods and architecture. The v2.4 analysis notebook (`mc_nuclear_smr_learning.ipynb`) is **reference-only**; where any older artifact disagrees with this plan, this plan wins.

## Version history (compressed)

- **v2** (07-28, after the fit assessment in the *ReEDS paper development* project): issue 2 (2030 anchor) resolved; terminology locked ("learning-consistent required subsidy"); subsidy deliverables expanded to rate + fiscal bill + transfer share; appendix check pre-registered both ways; framing commitments added; issues 6–7 opened.
- **v3** (07-30): Step 0 added — pipeline build + pilot runs before the matrix is spent.
- **v4** (07-30): issue 1 resolved — **winner-take-all technology assignment computed in the MC**; both-tech trajectories in every run (loser learns from international spillover only); 12-run sub-experiment dropped; standardization result becomes the zero-run MC fragmentation figure; issue 8 opened.
- **v5** (07-30): issue 3 resolved — 6 schedules locked with renames; **per-trajectory MC architecture** (separate MC per schedule, 5,000 draws each, no weights, no schedule-as-random-variable); issue 9 (u drawing) opened and resolved same day (independent, full envelope).
- **v6** (07-30): issue 4 resolved — high/mid/low = **P95/P50/P5 of calculated financed CAPEX as joint draws** (duration enters via IDC); ReEDS-side survey: mandate mechanism found complete in the hybrid branch, dual reporting identified as the one gap; wiring paths confirmed.
- **v7** (07-31): ReEDS repo strategy — **fork upstream `ReEDS-Model/ReEDS`, branch `nuclear-learning`**, port with all storage-hybrid limbs stripped; port kit prepared.
- **v8** (07-31): **port applied** — 23 files written into the fork clone, adapted to upstream's restructured layout, including the new dual reporting. Track A code work complete; shakedown runs are next, **concurrent with the Track B notebook build**.

## Current status

**Done:** issues 1, 2, 3, 4, 9 resolved (see Decisions). ReEDS fork ported end to end — mandate (floor/equality), six trajectory files, dual reporting (`nuclear_cap_price` + ub + raw twins), endogenous-learning engine, all wiring (`runreeds.py`, `runfiles.csv`, switches) — details and watch items in `claude/reeds-mandate-mechanism-notes.md` §0.

**Now (concurrent):**

- **Track A — Ethan:** review diff, commit + push `nuclear-learning`; run the **small-scale shortened shakedown runs** (short horizon, reduced spatial resolution; on NLR or local — GAMS required): floor smoke test, equality flip, slack floor, engine smoke test (watch gdxpds 4.0 API), financing cross-check. Outside the paper's run count.
- **Track B — new MC notebook repository:** build per this plan (scope below). Neither track blocks the other.

**Step 0 build status (2026-07-31, see notes doc §0.1):** the engine's experience dump was found unwired (a port omission at the `d3_data_dump`→`6_data_dump.gms` rename) and fixed; Utah shakedown cases built (`cases_utshakedown.csv`: floor 500 MW @ 2035, equality flip, slack floor, engine smoke — 2032 dropped because `firstyear_nuclear`=2033) and launched (first-run input sync in progress; A6 verification pending); **Track B built** at `z-ethan/mc/mc_cost_trajectories.ipynb` (in-fork per decision, not a separate repo): 6×5,000 per-trajectory MCs, financing replication verified, winner-take-all + 18-case joint-draw exports, `US_SCHEDULES.csv` single-source-of-truth + `cop29`→`cop28` regeneration, fragmentation figure (median split penalty 10%), hindcasts, QA1–QA13 green (QA10 awaits the shakedown run).

**Then:** NLR regroup (issue 8 + ranking functional + non-CAPEX parameter check) → Step 0 pilots with real MC trajectories → issues 5 + 6 → issue 7 + Step 4 budget variant → 2030-anchor documentation.

## Core idea

Take a set of exogenous US nuclear deployment trajectories, compute the cost trajectories they imply under uncertain learning parameters (learning rate, cross-firm spillover, international spillover, domestic and international builds), force each deployment trajectory into ReEDS as a mandate paired with its consistent cost trajectory, and read the shadow price on the capacity constraint as the subsidy required to make that deployment happen. Endogenous learning inside ReEDS is demoted to an appendix consistency check, not the main method.

**Naming and positioning.** The output quantity is the **learning-consistent required subsidy** — not "required cost." Mai et al. (2019) prescribe deployment and read the dual as a cost target with cost assumptions canceled out; here costs are *prescribed* (conditioned on the deployment they accompany) and the dual is the residual subsidy. The methodological contribution is the consistency closure: deployment-conditional costs feeding a deployment mandate, so cost and deployment are never contradictory. State the distinction from Mai explicitly in the methods; a referee who knows that paper will check.

## Research questions

1. **What subsidy level is needed to achieve each deployment target?** Measured as the marginal cost on the ReEDS capacity (mandate) constraint in $/MW. Because an ITC applies uniformly to all builds in a year, the dual reads directly as the **required uniform ITC rate**. Deliverable is three numbers per scenario: the rate, the fiscal bill (rate × all builds), and the inframarginal transfer share. The transfer is not a bug — it is a property of uniform instruments — and quantifying it is part of the finding.
2. **What conditions are needed for ATB cost trajectories to happen?** Where do the ATB nuclear cost projections sit within the learning-parameter-conditional cost ranges, and what combination of deployment, learning rate, and spillover would deliver them? Audience: every modeler who consumes ATB nuclear costs. RQ2 requires no ReEDS runs — complete after Step 2 — and gets a full results subsection with its own deliverable sentence. May seed a standalone input-audit paper.

## Framing commitments

- **Working mechanism hypothesis:** the subsidy is a *bridge* — the dual should decay toward zero as the fleet walks down the learning curve. The shape of the dual trajectory, not its level, is the durable object; figures are designed around dual trajectories. (Secondary mechanism: experience fragmentation — quantified by the MC fragmentation figure.)
- **Conditional-cost discipline:** every MC cost fan is conditional and never presented as a cost projection; every caption and abstract sentence preserves the conditional. The per-trajectory MC architecture makes this structural: no unconditional cost distribution exists anywhere in the analysis.
- **Advocacy defenses:** report implausibly-large subsidies as prominently as small ones; report zero-dual and overbuild cases; never rank trajectories by desirability — the paper prices them, it does not endorse them. The paper also does not *weight* them: schedule probability weights are gone by design.
- **Report the results that undercut us:** the inframarginal transfer, the appendix check whichever way it comes out, and any slack-mandate / sign-flipped-dual cases.

## Tools

1. **ReEDS — fork of upstream `ReEDS-Model/ReEDS`, branch `nuclear-learning`** (ported v8; local clone `~/code/research/ReEDS-nuclear-learning`). Mandate, dual reporting, and learning engine in place; layout mapping and watch items in `claude/reeds-mandate-mechanism-notes.md`.
2. **New MC cost-trajectory notebook** (new repository, Track B) — one separate Monte Carlo per build trajectory (5,000 draws each) producing **OCC and construction-duration trajectories jointly** (same draws, same copula) for SMR and traditional (large) nuclear. Port source: the v2.4 reference notebook.
3. **Endogenous-learning engine** (`reeds/core/solve/nuclear_learning.py` in the fork, hybrid branches defaulted off) — appendix check only.

## Methods / analysis pipeline

### Step 0 — Pipeline build + pilot runs

**Track A — ReEDS fork (code complete v8; shakedown pending).** Runs **concurrently with Track B** — the shakedown proves the ReEDS architecture on placeholder inputs while the real trajectory machinery is being built.

- Done: mandate equations (LHS `nuclear(i)` only), trajectory loading + `firstyear_nuclear`, 24 switches, six trajectory CSVs, dual reporting (converted + raw, floor + ub; **deflation convention to verify at the pilot logging audit** — rental `1/pvf_onm` default vs `crf` alternative, raw `.m` reported for the audit), engine + scheduling + timetype guard, runfiles wiring.
- Pending (Ethan): commit + push; **shakedown runs** — floor smoke test (`nuclear_cap_price` lands in outputs, plausible sign/magnitude), equality flip (both marginals), slack floor (dual = 0, overbuild visible), engine smoke test (`check` passes; gdxpds 4.0 watch item), financing cross-check (dump ccmult/cost_cap_fin_mult for fixed inputs — the notebook replication must reproduce them).
- Open wiring question for Step 0: **winner-only mandate** — the ported constraint mandates both nuclear techs jointly; the winner-take-all design needs a per-tech variant or the loser held out of the mandate set.

**Track B — new MC notebook repository (not started).** Scope:

- **Per-trajectory MC architecture:** one independent MC per locked schedule, 5,000 draws each (30,000 total), each draw producing OCC *and* duration trajectories jointly. No schedule weights, no sched↔u rank-coupling; u drawn independently over the full IAEA Low/High envelope, identically in all six MCs.
- **Port from the reference notebook:** OCC engine (Abou-Jaoude eq. 12 generalized, CES aggregation, spillover), duration model (INL series-reduction curves), PRIS/RDS-2 loader, permanent regression cells (anchor checks, eq. 11/12 reproduction, hindcasts — hindcasts promoted to paper body), export machinery.
- **Financing-factor replication:** ReEDS's OCC→CAPEX conversion — duration-dependent IDC (ccmult) + financial multiplier (`2_financials.gms`: `ccmult/(1−tax_rate)×…`). **Port source: the engine's Python ccmult implementation** (self-verifies against GAMS). Basis discipline: OCC is IDC-exclusive 2022$ (ATB convention) — the multiplier must *add* IDC. **Triply load-bearing:** winner selection, case extraction, subsidy translation.
- **Winner computation:** per draw, financed CAPEX trajectories for both techs under winner-take-all allocation; winner determined per the Decisions (granularity = issue 8).
- **Both-tech exports:** every ReEDS case ships OCC + duration for *both* techs (winner: domestic learning + international spillover; loser: international spillover only). Duration must ride along — ReEDS computes IDC internally from OCC + duration.
- **Extraction rule:** rank draws by calculated financed CAPEX within each trajectory's MC; select P95/P50/P5 as actual joint draws; export in the exact per-case format (plantchar files + construction-times files + mandate scen switches; template: `cases_nuclearlearning_nrel.csv`). Default ranking functional: discounted, schedule-weighted total financed CAPEX (confirm at NLR regroup with issue 8).
- **Schedule single-source-of-truth:** the notebook exports `US_SCHEDULES.csv` from its locked definitions; mandate trajectory CSVs regenerate from the same export via `_generate_cap_trajectories.py` (rename `cop29`; keep the documented −3 GW base-year adjustment). Residual check: construction-times CSV granularity carries time-varying durations.
- **MC fragmentation figure (zero ReEDS runs):** split-schedule cost trajectory vs the two concentrated ones — prices the fragmentation penalty and justifies winner-take-all. Convention: zero domestic cross-class spillover.

**Pilot half (after both tracks + NLR regroup).** Pilot subset: one modest trajectory (EIA 2026 AEO high or Abou-Jaoude mod) + one aggressive (2025 EO), optionally one low-cost/aggressive to probe zero-dual/overbuild. Purposes: bug flushing (mandate + dual reporting with real trajectories; both-tech cost + duration ingestion; units/dollar-year; tech mapping); financing-factor validation (notebook vs ReEDS — a silent mismatch corrupts winner selection *and* case extraction); dual reconnaissance for issue 6 (the 1↔2 switch makes floor-vs-equality a zero-code flip); logging audit for issue 5 (including the deflation convention); loser-build check (material loser builds ⇒ mix contingency); first look at dual-decay shape. Pilots and shakedowns are diagnostics, outside the paper's run count (~3 pilot runs).

### Step 1 — Cost ranges for the 6 trajectories

Extract high/mid/low cases from each trajectory's dedicated MC: P95/P50/P5 of financed CAPEX as joint draws. Output: **18 cases**, each carrying both techs' OCC + duration trajectories with the mandate on the winner. Blocked only by issue 8; machinery built and debugged in Step 0.

### Step 2 — Compare cost ranges against ATB

Overlay ATB nuclear cost projections on the per-trajectory cost fans → answers RQ2. **External anchoring:** hindcast cells promoted to paper body ("the learning model, run backwards, reproduces realized recent-fleet cost experience"). The ATB comparison is NREL-benchmarking-NREL — the one-lab problem bites twice; an independent learning-model comparison or non-NREL collaborator is the cheapest upgrade. Basis note: ATB comparison is on OCC, not financed CAPEX — keep bases straight vs the CAPEX-ranked case selection.

### Step 3 — ReEDS runs (18 base cases)

Each case into the fork: both techs at conditional OCC + duration, deployment as a capacity mandate on the winner.

- Lock the constraint form (issue 6) before production runs, from pilot evidence.
- Read the mandate dual = required uniform ITC rate. The constraint is national *cumulative* capacity per year — a rental price — so the issue-5 formula maps year-t duals to per-build subsidies (integrate over mandated-marginal years or difference the cumulative duals); equality mode has two marginals.
- Compute fiscal bill + transfer share (issue-5 formula written before runs; logging verified in Step 0).
- **Benchmark against real instruments** (48E/45Y nuclear treatment, historical support, Vogtle's realized stack): "trajectory X needs N× the current ITC" is both external anchor and headline.

### Step 4 — Sensitivities

Base plan: 18 cases × 6 sensitivities (high/low gas, high demand, low/high RE+storage costs, transmission constrained) = 108 + 18 = **126 runs**. **Alternative (decision needed):** sensitivities on mid-cost cases only → 18 + 36 = 54 + spot checks; with the sub-experiment dropped, decide purely on whether cost × sensitivity interactions are worth ~72 runs. **Before the matrix is spent, choose the robustness invariant** (issue 7).

### Appendix — Endogenous-learning consistency check

Take a scenario's implied ITC, run the fork with endogenous learning and that ITC (no mandate), check whether deployment is reproduced. Machinery ported and verified via the engine's `check` mode. Sequential-solve caveat: the engine is myopic, which shapes what "decentralizing the target" means; ReEDS also picks its own tech winner — whether it matches the MC's is part of the interpretation.

**Pre-registered readings, reported whichever way it comes out:** pass ⇒ method validated. Fail ⇒ a finding, not a failed validation — learning-by-doing makes the problem non-convex, exactly where marginal-price instruments can fail to decentralize a target (multiple equilibria; no-build lock-in): "ITC targets sized without learning are unreliable in general"; consider promoting out of the appendix. Controls before attributing failure to learning economics: foresight, solver tolerance, the translation formula itself.

## Decisions

- **Exclude hybrid storage nuclear** — structural in the fork (all storage-hybrid machinery stripped; mandate LHS is `nuclear(i)` only).
- **Exogenous learning is the main method**; endogenous learning is appendix-only. Learning calculations are done **outside ReEDS**.
- **ReEDS repo (v7–v8):** fork of upstream `ReEDS-Model/ReEDS`, branch `nuclear-learning`; port applied 2026-07-31 (see notes doc §0). Constraint definition on record: national, annual, cumulative capacity, from `firstyear_nuclear`; equality = floor + ceiling pair with two marginals; dual reporting in `report.gms`/`report_params.csv`.
- **New repository, per-trajectory MC (v5):** separate MC per trajectory, 5,000 draws each, OCC + duration jointly; no schedule weights — the paper does not predict how much nuclear the US will build.
- **u convention (v5):** drawn independently over the full IAEA Low/High envelope, identically in all six MCs. Coupling role died with the schedule draw; uncertainty role survives (international spillover driver; the loser tech's only learning channel).
- **Case extraction (v6):** P95/P50/P5 of **calculated financed CAPEX** as actual joint draws — duration enters selection via IDC ("high-cost" can mean slow-to-build, nuclear's actual risk profile). Joint-draw discipline is worth a methods paragraph. Default ranking functional: discounted, schedule-weighted total financed CAPEX (confirm at NLR regroup).
- **Schedule set locked (v5):** one trajectory per provenance category, 117→400 ambition ladder —
  1. **EIA 2026 AEO high** (117.3) — modeled projection
  2. **Abou-Jaoude mod** (134; renamed — moderate variant, endpoint-verified) — study assumption
  3. **IAEA high** (172.3) — intergovernmental outlook
  4. **McKinsey GEP 2025** (200) — consultancy outlook
  5. **COP28 tripling pledge** (300; renamed from "COP29 target" — the Declaration to Triple Nuclear Energy launched at COP28, Dubai 2023; ReEDS scen file still `cop29`, rename at regeneration) — pledge
  6. **2025 EO** (400) — policy aspiration
  The 8-column `US_SCHEDULES.csv` is a stale pooled-notebook artifact (WNA and A-J con cluster below EIA; A-J adv duplicates the 300 endpoint). The new notebook regenerates the CSV as single source of truth. ReEDS basis: literal GW minus flat 3 GW (undoes the 97→100 rounding) — keep and document.
- **Technology assignment: winner-take-all, computed in the MC (v4).**
  - **Rationale:** with weak cross-tech spillover, concentration minimizes cost; and ReEDS cannot be offered both conditional trajectories as a choice — each assumes that tech gets all builds, so any split would double-count learning. Pre-computing the winner is the only assignment consistent with the consistency closure.
  - **Winner metric:** lower financed CAPEX (OCC × ReEDS-replicated financing factor). Pending: non-CAPEX parameter check (FOM, CF, lifetime) — extend toward levelized cost if materially different.
  - **Both trajectories always ported;** loser = international spillover only (sidesteps exogenously-declining ATB costs for the unbuilt tech). Mandate applies to the winner only — wiring variant needed in the fork (Step 0).
  - **QA:** verify loser builds negligible; material loser builds ⇒ **mix contingency** (regroup: representative endogenous-learning runs and/or split mandate at optimal mix).
  - **Convention:** zero domestic cross-class spillover, used consistently in loser trajectories and the fragmentation figure. **Standardization finding preserved at zero run cost** via the MC fragmentation figure.
- **2030 anchor convention (v2):** OCC(2030) = BOAK with no pre-2030 domestic learning (no licensed US reactor can connect before 2030 — describes reality); BOAK anchor range interpreted as embodying international spillover through 2030, so zeroing foreign stocks at the anchor is internally consistent. To-dos: the methods sentence (both halves) + source-vintage caveat.
- **Terminology (v2):** "learning-consistent required subsidy," explicitly distinguished from Mai et al.
- **Appendix check reported whichever way it comes out (v2).** **Pilots and shakedowns are diagnostics, outside the paper's run count (v3/v8).**

## Unresolved issues

1. ~~Technology assignment~~ **Resolved (v4)** — winner-take-all (Decisions).
2. ~~Pre-2030 learning~~ **Resolved (v2)** — 2030 anchor convention (Decisions).
3. ~~Schedule set~~ **Resolved (v5)** — locked with renames (Decisions).
4. ~~Case extraction~~ **Resolved (v6)** — financed-CAPEX joint draws (Decisions). Residual: ranking functional + winner-vs-per-tech distribution → NLR regroup (issue 8).
5. **Subsidy translation formula** — written before Step 3: (a) required uniform ITC rate, (b) fiscal bill, (c) transfer share; from year-t cumulative-capacity rental duals (two marginals in equality mode; sequential PV terms; verified deflation convention). Depends on issue 6; shares the financing-factor machinery.
6. **Mandate constraint form — floor vs equality.** Floor: dual = 0 when slack, overbuild observable ("needs no subsidy" is a legitimate headline). Equality: prices both directions (negative dual = trajectory is a ceiling; a tax would hold the market down). Lock before Step 3; both forms exist as the 1/2 switch — pilots compare empirically at zero code cost. Fit-assessment instinct: floor, overbuild reported wherever slack.
7. **Robustness invariant** — what must hold in every sensitivity: subsidy level, trajectory ranking, or dual-decay shape? Decide before the matrix is spent; drives reporting and run design.
8. **Winner granularity × extraction distribution** — winner per selected draw (with win probabilities reported) vs per trajectory; percentiles over winner-cost vs per-tech distributions; confirm the CAPEX ranking functional. **Deferred to the NLR regroup after the Step 0 builds**, with machinery outputs in hand.
9. ~~u drawing~~ **Resolved (v5)** — independent, full envelope (Decisions).

## Reference implementation (v2.4 notebook — port source, not the paper's code)

Monte Carlo (5,000 draws, seed 20260715) over: learning rates (large U(3–12%), SMR U(3–16%), comonotone), BOAK OCC anchors, spillover scale s × Kim & Verdolini θ ceilings, u over the IAEA RDS-1 Low/High envelope, US schedule (weighted, rank-coupled — superseded), vendor count U{4–8}, experience-base convention (tiny-base vs full-stock), ρ_CES ∈ {−2,−1,0,1}, Gaussian copula with correlation-set sensitivity. Domestic learning: Abou-Jaoude eq. (12) generalized to m vendors, per-vendor BOAK = 2OAK, cross-firm ω·LR (ω = 1/3), international spillover as additive θ-weighted stock. Experience via retirement identity on RDS-2 2025 unit data (`pris_loader.py`); committed pipeline 2025–2034. Durations: INL/RPT-25-84701 Fig. 18 series-reduction, joint with OCC. Permanent regression cells (anchor checks, eq. 11/12 reproduction, hindcasts) — port; hindcasts to paper body. OCC basis: $/kW, 2022 USD, IDC-exclusive (ATB) — keep for Step 2. **Not ported:** endogenous-learning scoping, schedule weights/rank-coupling, PCA spanning-set case selection.

## Key files

**Reference (`ReEDS-hybrid-plant/z-ethan/`, Ethan's machine):** `mc_nuclear_smr_learning.ipynb` (v2.4 port source; v1 backup alongside), `us_nuclear_pooled_learning_model.ipynb` (source of the stale 8-column `US_SCHEDULES.csv`), `rds2_2025_units.csv` + `pris_loader.py` + `pris_data_spec.md` (port), percentile/spanning-set exports (superseded), `mc_export_metadata.json`, `2024_v3_Workbook.xlsx` (ATB 2024 — BOAK anchors + Step 2).

**ReEDS fork (`~/code/research/ReEDS-nuclear-learning`, branch `nuclear-learning`, ported v8):** mandate in `reeds/core/setup/{b_inputs,c_model}.gms`; learning block in `reeds/core/solve/3_solve_oneyear.gms`; engine at `reeds/core/solve/nuclear_learning.py` (also the ccmult port source for the notebook); dual reporting in `reeds/core/terminus/report{.gms,_params.csv}`; wiring in `runreeds.py` + `reeds/input_processing/runfiles.csv`; trajectories + generators in `inputs/nuclear_learning/`. Survey + layout mapping + shakedown watch items: `claude/reeds-mandate-mechanism-notes.md`.

## Compute constraint

NLR cluster; **126 runs is the ceiling**. Budget variants: full matrix (126) or mid-cost-only sensitivities (≈54 + spot checks) — Step 4 decision. Pilots (~3) and shakedown runs are outside the count. MC draws are notebook-side and effectively free (6 × 5,000).

## Critical path (v8)

1. **Now, in parallel:**
   - **Track A (Ethan):** commit + push the fork; shakedown runs (floor smoke, equality flip, slack floor, engine smoke, financing cross-check); resolve the winner-only-mandate wiring.
   - **Track B:** build the new MC notebook repo (per-trajectory MCs, ports, financing-factor replication, winner computation, both-tech exports, CAPEX-ranked extraction, schedule regeneration, fragmentation figure).
2. **NLR regroup** — issue 8 (winner granularity × extraction; ranking functional) + the non-CAPEX winner-metric check, with both tracks' outputs in hand.
3. **Step 0 pilots** — 2–3 mandate cases with real MC trajectories (issues 5–6 evidence incl. floor↔equality flip; financing validation; loser-build check; deflation-convention verification).
4. Issues 5 + 6 — translation formula + constraint form, together (block Step 3).
5. Issue 7 + Step 4 budget variant (block Step 4 design).
6. Documentation: 2030-anchor methods sentence + source-vintage caveat.