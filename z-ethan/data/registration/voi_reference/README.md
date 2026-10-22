# Reference outputs for the value-of-information gates G0 and G1

These four files are the outputs of an earlier, independent implementation of the five-anchor
requirement map and the stage-3 cost observer (the working analysis's `rate_design` notebook,
five-anchor variant, executed 2026-09-23). They are copied here unchanged. No notebook in this
repository regenerates them, and no result of the paper is read from them.

They exist for one reason. Notebook `14_value_of_information` re-derives the requirement map and
the observer from scratch, and its registered gates G0 and G1 check that re-derivation against an
implementation that was written separately. The gate rows G0 and G1 of the registration verdict
(`results/exports/14/p90_verdict.csv`, Supplementary Note 3) therefore stay reproducible only if
these references ship with the code. This is a deliberate exception to the rule that every computed
quantity is regenerated.

- `u01_per_world_requirements_5a.csv`: per cost sample and target trajectory, the required credit
  scale f* (rounded to 4 decimals), its binding online year and the upper-clamp flag (60,000 rows).
  Gate G0 requires the re-derived f* within 1.5e-4 and identical binding years and clamp flags.
- `u51_feasibility_mask_5a.csv`: the share of samples above the statutory ceiling per online year,
  and the share not credit-feasible after the 2035 and 2033 windows, per band end and ceiling.
  Gate G0 requires exact agreement (1e-9).
- `u52_demonstration_gap_5a.csv`: percentiles and mean of the above-ceiling dollar gap within the
  2035 and 2033 windows. Gate G0 requires exact agreement (1e-9).
- `u10_ci_curves_5a.csv`: the observer's median posterior widths (f* and SMR learning rate, 5 to 95%)
  and median effective sample size per observation and noise level, truth sample included, seed
  20260901. Gate G1 requires agreement to the stored rounding.
