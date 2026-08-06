# Case-selection revert — coding plan (v10, 2026-08-06)

**Decision being implemented** (plan v10): production cases return to **P5/P50/P95 actual joint
draws** of the program-NPV ranking. Kept from the designed-cases detour: the lo/hi bounds as
**appendix possibility frontier + dual-monotonicity pilot instruments** (one schedule's pair);
the **constrained-optimizer framing**; a new **empirical simultaneous path-coverage** number;
mid = the **P50 draw**, with the literature-expected world demoted to a zero-run overlay.
Ranking metric unchanged (v9.1): discounted, schedule-weighted SMR program NPV.

Everything below is `smr100_case_export.ipynb` (cell indices as of the 08-06 save) unless
noted. **No changes** to `mc_cost_trajectories.ipynb`, `winner_boundary.ipynb`,
`mixed_build_optimizer.ipynb`, `npv_winner_check.ipynb`, or `atb_parameter_space.ipynb` —
the engine is untouched, so their QA-0 parity cells still pass. The pre-08-03 percentile-
selection code exists in the fork's git history for the notebook if a reference is wanted
(`git log -- z-ethan/mc/smr100_case_export.ipynb`, commits before the designed-cases adoption).

## 1. Intro (cell 0, markdown)

Rewrite item 2 of "What this notebook does" and the naming paragraph: three **percentile joint
draws** per schedule (P5/P50/P95 of the program NPV, registered draw indices), framed as the
constrained optimizer — min/max program NPV over the *plausible* set (the drawn worlds at the
90% level) rather than the prior's support corners; lo/hi engine-optimized bounds retained as
the appendix possibility frontier and the pilot monotonicity pair; literature-expected world as
overlay. Naming reverts to `smr100_{sched}_{p05|p50|p95}`; the bounds pair exports as
`smr100_{sched}_{blo|bhi}` in a separate cases file. Keep the discipline reminder verbatim.

## 2. Monotonicity section (cells 11–13)

Keep both code cells unchanged (the OAT sweeps + MC cross-check are the bounds' validity
certificate and good appendix material). Rewrite the markdown (cell 11): the section no longer
justifies *replacing* the percentile draws — it certifies the pinned directions used by the
bounds and documents why the corner design was demoted: corner worlds sit at the priors'
support endpoints (the least defensible elicitation objects) with no probability mass, and the
resulting band is a possibility statement with no content. Add the counterpoint sentence: the
"offsetting extremes" inside a percentile draw are a feature — that is what a plausible
expensive world looks like.

## 3. Bounds (cell 15) — keep, relabel

Keep the joint enumeration + coordinate verification exactly as is (it is the appendix
artifact and the pilot-instrument generator). Relabel the cell header/prints from "designed
cases" to "possibility-frontier bounds (appendix + pilot instruments)". The ±2.33 `dur_z` cap
caveat moves with it to appendix status.

## 4. Selection — NEW cell (after 15, before the fan)

For each schedule, rank the 10k draws by the existing `mc_score[sched]` and select the draws
at ranks nearest P5/P50/P95 (`np.argsort`; rank ⌈q·(N−1)⌉). Register schedule, percentile,
draw index, score, and every parameter column to `exports/smr100/selected_draws.csv`
(restoring the v9 registration file). Assert each selected draw's parameter row matches
`mc_perdraw.npz` (extends QA-0's identity guarantee to the cases themselves).

## 5. Coverage — NEW cell

Per schedule, on the SMR financed-CAPEX paths (and OCC as a secondary table): the fraction of
all 10k paths lying **entirely** inside the [P5-draw path, P95-draw path] band year-by-year
(simultaneous coverage), alongside the by-construction 90% scalar statement. Export
`exports/smr100/band_coverage.csv`; print the numbers for the methods text. Optional second
number: the calibrated pointwise-quantile pair whose empirical simultaneous coverage hits 90%
(figure/number only — never cases).

## 6. Mid overlay (cell 16)

Keep `lit_world()` / `mid_score()` but stop treating the literature world as a case: it
becomes an overlay line on the fan figure and a reference row in the exports (report its
P38–40 placement). The fan figure now shows: MC bands, the three **selected-draw**
trajectories (solid), the lo/hi bounds (dashed, labeled "possibility frontier"), and the
literature overlay (dotted). Placement figure (cell 18): mark the selected draws as the cases;
bounds and lit-world as annotations.

## 7. Case build (cell 19)

Build `CASES` from the three selected draw rows per schedule instead of `BOUNDS`/`lit_world`:
`w1 = worlds[sched].iloc[[idx]]`, score = `mc_score[sched][idx]`, FOM/VOM via the existing
comonotone `om_at(t, u1_of(w1))` (no ATB-moderate special case anymore), tags
`p05/p50/p95`, record the draw index. Keep the occ/dur path extraction verbatim. Freeze to
`exports/smr100/selected_cases.csv`; rename the bounds record to
`exports/smr100/bounds_record.csv` (the old `designed_cases.csv` name retires).

## 8. Pilot bounds pair — NEW export block

One schedule's lo/hi worlds (suggest the modest pilot schedule, `abou_jaoude` — decide at the
regroup) exported as `smr100_aj_blo` / `smr100_aj_bhi` with the same plantchar/financials/
construction-times machinery, into a separate `cases_nuclearlearning_smr100_bounds.csv` so
the production matrix stays 18 columns. Purpose: the dual-monotonicity pilot (their input
paths pointwise-dominate every draw, so their dual trajectories must not cross).

## 9. Exports (cells 21–24)

Mechanics unchanged; iterate over `CASES` ∪ the bounds pair; new case names flow through file
names automatically (`nuclear{,-smr}_mc_smr100_{sched}_{p05|p50|p95|blo|bhi}` etc.).
QA-5f (large-counterfactual ordering) keeps working on the percentile tags.

## 10. QA suite

- **QA-4 rewrite:** (a) each production case's parameters are identical to its registered draw
  row in `mc_perdraw.npz`; (b) each case's score sits at its nominal rank ±0.5 percentile;
  (c) p05 < p50 < p95 scores strictly; (d) bounds still verified (`_n_fail == 0`) and strictly
  outside all 10k draws; (e) **NEW pointwise-dominance assert:** the blo (bhi) financed-CAPEX
  and OCC paths lie ≤ (≥) every drawn path in every year — this is the certificate that makes
  the pair a valid monotonicity instrument; if it ever fails, the bounds are NPV-extreme but
  not path-extreme and the pilot pair must instead be constructed by path-dominance;
  (f) coverage numbers in a sane range (assert ≥ 0.80 simultaneous, warn if < 0.85);
  (g) lit-world placement P30–60 becomes informational (print, not assert).
- **QA-5:** extend the round-trip checks to the bounds cases file.

## 11. Metadata (cell 33) + closing note (cell 34) + README

`smr100_metadata.json` "design.selection" → percentile joint draws (v10) with draw indices,
coverage numbers, bounds-pair note; exports hash list gains `selected_draws.csv`,
`selected_cases.csv`, `band_coverage.csv`, `bounds_record.csv`. Closing note and the README's
smr100 section rewritten to the v10 design (constrained-optimizer sentence included).

## 12. ReEDS-side file retirement

Regenerating writes the `_{p05,p50,p95}` family; the stale `_{lo,mid,hi}` family (36 plantchar
+ 18 financials + 18 construction-times + the old cases csv) must be deleted in the fork and
the removal committed, or ReEDS's input scan will happily accept the dead names. Re-run QA-5
after cleanup.

## Run order

1. Implement §§1–11; Run All (needs `mc_perdraw.npz` present for QA-0 and the draw-identity
   asserts).
2. §12 cleanup + fork commit.
3. Record the coverage numbers in the plan/methods notes; pick the bounds-pair schedule at the
   NLR regroup if `aj` is not ratified.

---

## Post-run record (2026-08-06, implementation complete)

All sections implemented and Run All passed (QA-0…QA-5 green; all 18 selected draws
bit-identical to `mc_perdraw.npz`; pilot pair `smr100_aj_{blo,bhi}` passed the QA-4e
pointwise path-dominance certificate on occ + fincapex, 2030–2050). §12 cleanup done:
72 stale `_{lo,mid,hi}` input files + `designed_cases.csv` deleted, 36 stale dollaryear
rows pruned.

**Coverage numbers** (`exports/smr100/band_coverage.csv`; simultaneous over years ≥ 2030):

| schedule | simult. fincapex | simult. OCC | calibrated q* (90% simult.) |
|---|---|---|---|
| eia   | 0.619 | 0.656 | 2.43 |
| aj    | 0.636 | 0.676 | 2.49 |
| iaea  | 0.695 | 0.684 | 2.48 |
| mck   | 0.746 | 0.773 | 2.52 |
| cop28 | 0.712 | 0.745 | 2.54 |
| eo    | 0.805 | 0.787 | 2.58 |

**Deviation from §10(f), needs ratification:** the planned `assert ≥ 0.80 simultaneous`
was falsified by the data (0.62–0.81; only `eo` clears 0.80). Two sample paths make a much
tighter simultaneous band than the 90% scalar statement suggests. QA-4f now asserts a
degenerate-band floor (≥ 0.50) and WARNs loudly below 0.85; the honest numbers + the
calibrated pointwise q* (≈2.4–2.6, i.e. a ~[P2.5, P97.5] pointwise band has 90%
simultaneous coverage) are the methods-text material.

Lit-world overlay placement: P37.1–P40.2 across schedules (inside the expected P38–40 up to
rounding). Bounds-pair schedule `aj` pending ratification at the NLR regroup (§8).
