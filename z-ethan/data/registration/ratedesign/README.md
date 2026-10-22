# ratedesign batch registration

These three files are the frozen design record of the `ratedesign` batch (casefile
`cases_nuclearlearning_ratedesign.csv`, 66 runs). The working analysis's rate-design notebook wrote
them before the batch was emitted, and they are copied here unchanged.

- `u80_batch_spec.csv`: one row per credit run (48) and horizon run (6): block (envelope,
  boundary, hybrid, horizon), schedule, cost-sample draw index, expected outcome, gate, margin and
  target in rate points, cap, and the deficit years of the spec.
- `u81_run_schedules.csv`: the credit path of each of the 48 credit runs by build year
  (`rate_on_world`, the rate written to the run's incentives file) with the sample's overnight
  capital cost (`occ_world_kW`, 2024 $/kW).
- `u82_anchor_spec.csv`: the 12 p25/p75 mandate anchors with their draw indices.

Notebook `06b_run_tables_rate_design` reads them to join the spec to the delivery outcomes and to
check that the casefile, the incentives files and the plant-characteristics files encode the design.
