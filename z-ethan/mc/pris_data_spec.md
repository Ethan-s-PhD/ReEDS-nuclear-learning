# PRIS data acquisition spec

## Headline: don't scrape PRIS — download RDS-2

Three things I verified before writing this:

1. **The PRIS web interface disallows automated access.** `pris.iaea.org/robots.txt` blocks crawlers, so scripted scraping is off the table (a fetch attempt returns `ROBOTS_DISALLOWED`). Manual browsing is fine, but reactor-by-reactor for ~440 units is not.
2. **There is no free bulk export.** PRIS Statistics (PRISTA) is the reporting tool, and it's restricted to registered Member State users; its reports export to PDF, not CSV.
3. **RDS-2 has everything we need and is free.** *Nuclear Power Reactors in the World* (Reference Data Series No. 2) is the annual IAEA publication **generated from PRIS**, published as an open PDF with unit-level tables. I fetched the 2024 edition and confirmed the table structures below.

**Get:** RDS-2, latest edition (2025 edition = data through 31 Dec 2024), from the IAEA publications site. Search "IAEA RDS-2 Nuclear Power Reactors in the World". The 2024 edition (data through 31 Dec 2023) is at `www-pub.iaea.org/MTCD/Publications/PDF/p15748-RDS-2-44_web.pdf`; the 2025 edition is `RDS-2-45_web.pdf` on the same host.

**Note the two publications are different things** and it's easy to conflate them (I did, earlier):
- **RDS-1** = *Energy, Electricity and Nuclear Power Estimates for the Period up to 2050* → the **projections** (Low/High), already in the model as `REGION_MILESTONES`.
- **RDS-2** = *Nuclear Power Reactors in the World* → the **unit-level history and current status** (this document).

---

## What to extract, and what each table is for

| RDS-2 table | Contents | Feeds |
|---|---|---|
| **Table 14 — Operational reactors** | Country, Code, Reactor Name, Type, **Model**, Capacity (Thermal/Gross/**Net**), Operator, NSSS Supplier, **Const. Start**, **Grid Connection**, **Comm. Operation**, EAF%, UCF% | **The core need.** Fleet vintage → retirement schedule (item 1); duration panel by family (item 7); family experience stocks (item 6) |
| **Table 13 — Reactors under construction** | Same fields + planned First Criticality / Grid Connection / Commercial Operation | Committed pipeline ~2025–2035 (bottom-up, replaces interpolation over that window) |
| **Table 12 — Reactors planned** | Country, Name, Type, Model, Capacity, Operator, NSSS, **Expected Construction Start** | Optional extension of the pipeline; treat as soft (many never start) |
| **Table 16 — Reactors permanently shut down** | Operational units that have retired, incl. shutdown dates | Retirement-rule calibration: check whether actual retirements have tracked 60y (they often haven't — Germany, Japan) |
| **Table 8 — Median construction time** | New grid connections and **median construction time in months**, by country, by 5-year block | Independent cross-check on the duration panel's level |
| **Table 7 — Annual construction starts / grid connections (1954–)** | Units and MW(e) per year | Historical gross-build series; sanity check on the identity |

**Minimum viable extraction: Table 14 + Table 13.** Everything else is validation.

---

## Extraction method

The RDS-2 tables are real text (not scans) — I extracted them successfully — but the PDF renders them with rotated/wrapped column headers, so naive `pdftotext` output is mangled. Use a table-aware extractor:

```bash
pip install camelot-py[cv]     # or: pip install tabula-py  (needs Java)
```
```python
import camelot
tables = camelot.read_pdf("RDS-2-45_web.pdf", pages="29-47", flavor="lattice")  # Table 14 page range
```

Page ranges shift between editions — check the table of contents. In the 2024 edition: Table 12 → p.24, Table 13 → p.26, Table 14 → p.29–46, Table 16 → p.49.

Expect to hand-fix a modest number of rows; budget an hour. Validate with `validate_units()` rather than eyeballing.

**Fallbacks if PDF extraction is painful:**
- **World Nuclear Association reactor database** — built on PRIS, augmented with WNA data, browsable/filterable with a friendlier interface.
- **Commercial PRIS scrapers** (e.g. Apify's "IAEA PRIS Scraper") — pre-built, ~700 reactors, returns JSON/CSV with exactly the fields we need including `reactor_model`. Paid, and it's scraping a robots-disallowed site, so check terms before relying on it.
- **Published academic datasets** — Lovering et al. (2016) released a construction-cost/date dataset for seven countries; useful for historical validation, but stale for anything post-2015.

---

## Expected schema for `pris_loader.load_units()`

One row per reactor. Column names are normalized, so RDS-2's own headers work as-is:

```
country, reactor_name, reactor_type, model, capacity_net_mw,
construction_start, grid_connection, commercial_operation,
permanent_shutdown (optional), status
```

---

## Gotchas (each of these will bite silently)

1. **Dates are month-precision.** RDS-2 prints `2013-3`, not `2013-03-12`. `parse_pris_date()` handles it. This adds up to ~1 month of noise per duration observation — immaterial against the residual spread, but don't claim day-level precision. PRIS's per-reactor web pages have exact dates if you need them for the AP1000 subset.

2. **Endpoint convention differs from the current notebook.** RDS-2 Table 8 states construction time is measured **first concrete → grid connection**. The existing AP1000 panel uses **FNC → commercial operation**, which is systematically longer (Vogtle-3: 124 vs 120 months). Harmonize on grid connection before combining, or the panel will show a spurious jump.

3. **Net vs gross capacity.** Use the **Net** column — it's what RDS-1's capacity milestones are denominated in. The Gross column will inflate your unit counts by ~5%.

4. **Suspended-operation units.** Japan's ~20 idle reactors are "operational" in PRIS but not producing. They're in the fleet vintage (correct for retirement timing) — just don't reconcile capacity totals against generation figures and expect a match.

5. **Taiwan** is reported separately from China in RDS-2 totals (in notes, not the main table rows). Mapped to CEA here; check whether your RDS-1 milestones include it.

6. **Lifetime rule is a scenario knob, not a constant.** IAEA Low and High embed *different* LTO assumptions, so pairing one retirement schedule with both net paths is incoherent. Pair short life ↔ Low, long life ↔ High. **Verify against the RDS-1 methodology notes before finalizing** — I have not confirmed the exact assumptions IAEA uses, and the whole gross-additions identity inherits that choice.

7. **Don't double-count the pipeline.** `committed_pipeline()` output should *replace* the interpolated RDS-1 path over ~2025–2035, not add to it.

8. **Model field is dirty.** RDS-2 has `AP-1000`, `AP1000`, `CAP1000`, `HPR1000`, and at least one typo (`HRP1000` for Sanaocun). `FAMILY_PATTERNS` in the loader catches the ones I saw; re-check coverage after extraction with `assign_family(df).isna().sum()`.

---

## Why this matters (the magnitude)

Illustrative run on the WEU Expected net path with a plausible retirement profile:

- Net-delta method (current model): **13 GW** of European experience counted, 2030–2050.
- Gross identity (Δnet + retirements): **83 GW** — about **6× more**.

Europe's ~95 GW fleet was largely connected in the late 1970s–80s; at a 60-year life the bulk of it retires inside the model window. A net path that ends near 100 GW in 2050 therefore implies a *large* build program that the current method scores as almost zero learning. Since WEU/EEU carry high θ, this bias flows straight into the US spillover stock.
