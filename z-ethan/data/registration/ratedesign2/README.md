# ratedesign2 batch registration

These three files are the frozen design record of the `ratedesign2` batch (casefile
`cases_nuclearlearning_ratedesign2.csv`, 93 runs). The working analysis's rate_design2 notebook
wrote them before the batch was emitted, and they are copied here unchanged.

- `m01_map_anchor_spec.csv`: the 36 map anchors `ma_{schedule}_d{draw}`: draw index and the full
  drawn parameter row of each cost sample.
- `m02_credit_run_spec.csv`: the 57 credit runs `ax_*`: arm, convention (fbB or fbC), cost sample,
  form (exact, capped_post2035, flat60), cap, gate, registered prediction and eligibility.
- `m04_offers.csv`: the offered credit path of each credit run by year (`offer_rate`) with the
  sample's overnight capital cost (`occ_world_kW`, 2024 $/kW).

Notebook `06b_run_tables_rate_design` reads them; batch 2 reuses the m04 offers of its three
ratedesign2 learning-on controls.
