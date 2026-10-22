# Literature records

These files are frozen records that notebook `02_atb_basis_and_literature.ipynb` reads. Each file is a transcription or a digitization of a published source. No notebook writes to this folder.

| File | What it is | Where it came from |
|---|---|---|
| `abou_jaoude_deployment_projections.csv` | Cumulative new US nuclear deployment (GW) at 5-year milestones, 2030–2050, for the conservative, moderate and advanced scenarios. The ATB 2024 pairs each nuclear cost trajectory with one of these deployment paths. | Transcribed from the deployment table of Abou-Jaoude et al. 2024 (INL/RPT-24-77048), the source of the ATB 2024 nuclear costs. The notebook asserts the values against the published table. |
| `lit_sources.csv` | Hand-transcribed (cost, cumulative units or GW, year) points of the published cost projections, one row per point, with the dollar year, the stated band, the page or table quoted and the URL. | Transcribed from the reports themselves (DOE Liftoff 2023 and 2024, EIA/Sargent & Lundy, EPRI, IEA/NEA 2020, Steigerwald et al. 2023, Vanatta et al. 2024, and the realized Vogtle 3&4 and quoted Darlington projects). |
| `lit_assumptions.csv` | One row per source: model form, stated learning rate, anchor attachment, unit size, vendor structure, spillover, dollar year, construction durations, and whether cost is paired with deployment. The learning model is the last row. | Compiled from the same reports. Exported unchanged as `c01_assumptions.csv`. |
| `lit_cite_only.csv` | Studies found by the literature sweeps that give no (cost, unit-count) pair. They are cited in the paper but never plotted or scored. | Compiled from the two literature sweeps. Exported unchanged as `c08_cite_only.csv`. |
| `mit_anp201_fig2_digitized.csv` | Bar tops of MIT ANP-201 (Shirvan 2024) Fig. 2, AP1000 and SMR programs, with the read error. | Digitized from the raster figure against its own gridlines (read error about $190/kW). |
| `inl_pathways_fig10_digitized.csv` | Plant-by-plant cost totals of INL's cost-reduction pathways study (Bolisetti et al. 2024) Fig. 10, Concepts A and B. | Digitized from the vector figure (exact up to the axis calibration). |
| `mit_anp194_fig225_digitized.csv` | Units 1–10 of eight reactor architectures from Stewart & Shirvan 2022 (MIT ANP-194) Figs. 2.24 and 2.25. | Digitized from the vector figures (exact). |
| `iea_2025_digitized.csv` | IEA 2025 SMR cost paths (US and EU) and global SMR capacity by scenario, Figs. 2.4 and 2.11. | Digitized from the vector figures (exact). |
| `bti_fig26_endpoints.csv` | The 2050 end points of the twelve Breakthrough Institute 2022 cost curves (Fig. 2-6), with the report's eq. B-2 parameters and the read error. | Read by hand from zoomed crops of the raster figure and checked against eq. B-2. |
| `digitize_calib.json` | Axis calibration of the two first digitized figures and the gate G1 record: each digitized series reproduces the values the report states in its text. | Written by the digitizer when the figures were read; the notebook re-asserts gate G1 from it. |
| `digitize_calib_b.json` | The same record for the second set of digitized figures (gate G1b). | Written by the digitizer; the notebook re-asserts gate G1b from it. |
