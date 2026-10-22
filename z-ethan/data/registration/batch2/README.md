# batch2 registration

These three files are the frozen design record of `batch2` (casefile
`cases_nuclearlearning_batch2.csv`, 89 runs). The working analysis's rate_design2 notebook wrote
them before the batch was emitted (methods v2.5 and the 2026-09-11 amendment), and they are copied
here unchanged.

- `m50_b2_run_spec.csv`: one row per run: block (S statute, K learning-on control, R1 map margin),
  form (flat50, grants50, exact, map_plus_1e6, map_plus_2e6), cost sample, window, the post-window
  excess, the registered prediction and the control run of each statute run.
- `m51_b2_offers.csv`: the offered credit path of each run by year (`offer_rate`, `status`) with
  the sample's overnight capital cost (`occ_world_kW`, 2024 $/kW).
- `m41b_b21_offers.csv`: the map-plus offers of the ten fresh R1 samples (the source of the R1 rows
  of m51, including the two 2031 cells clipped at 0.95).

Notebook `06b_run_tables_rate_design` reads them; batch 3 reuses m50/m51 for its flat-credit copies.
