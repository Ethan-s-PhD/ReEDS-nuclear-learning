# step4 case-selection registration

`selected_draws_large.csv` is the frozen record of which Monte Carlo draws became the large-reactor
comparator runs `large100_{target}_{p05|p50|p95}`. The step4 case-export notebook of the working
analysis wrote it (2026-08-13) when it built the 12 `large100_*_p05/p95` columns of
`cases_nuclearlearning_step4.csv`; it is copied here unchanged. Each row is the draw at the 5th,
50th or 95th percentile rank of the discounted large-reactor program cost over the 10,000 draws of
`mc_perdraw.npz`, with its index, score and full parameter row. The `p50` rows repeat
`../smr100/selected_draws_large.csv` (those runs are in the smr100 casefile).

Reader: notebook `13a_bridge_calibration` (stage 1, the large-reactor side check of the
cost-based failure label).
