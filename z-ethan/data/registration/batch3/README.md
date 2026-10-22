# batch3 registration

These two files are the frozen design record of `batch3` (casefile
`cases_nuclearlearning_batch3.csv`, 151 registered runs, 149 returned). The working analysis's
batch-3 case-export script wrote them before the batch was emitted (methods v2.6), and they are
copied here unchanged.

- `b3_run_spec.csv`: one row per run: block (A1, A2 paired mandate anchors; B1, B2, B3 flat-50%
  credit runs; R the re-run), market world, schedule, percentile, draw index, and the source
  casefile and column the run copies.
- `b3_predictions.csv`: the registered prediction of each block-B run (deliver, shortfall, or
  "from block A") with its inputs.

The runs `smr100_eo_p75_demhi` and `smr100_iaea_p75_demhi` are registered here but never returned;
notebook `06b_run_tables_rate_design` asserts that exactly these two are missing.
