# smr100 case-selection registration

These three files are the frozen record of which Monte Carlo draws became ReEDS cases. The case-export notebook of the working analysis wrote them when it built the input files and the casefile `cases_nuclearlearning_smr100.csv`; they are copied here unchanged.

- `selected_draws.csv`: the 18 priced cases `smr100_{target}_{p05|p50|p95}`. For each target trajectory, the draws at the 5th, 50th and 95th percentile ranks of the discounted SMR program cost (rank = `ceil(q * (N - 1))` of a stable sort over the 10,000 draws), with each draw's index, score and full parameter row.
- `selected_draws_large.csv`: the six large-reactor comparator cases `large100_{target}_p50`. The draw at the 50th percentile rank of the discounted large-reactor program cost over the same 10,000 draws.
- `selected_draws_p25p75.csv`: the 12 anchor draws at the 25th and 75th percentile ranks of the SMR program cost, added on 2026-09-04 by the same rule. The later batches (ratedesign, ratedesign2, batch2, batch3) reuse them.

Notebook `04_case_selection` regenerates all three files from `mc_perdraw.npz` and asserts that the regenerated selection equals these records. The notebook never writes these files and never writes under `inputs/`.
