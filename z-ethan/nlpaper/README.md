# nlpaper

`nlpaper` is the only non-notebook code of the analysis. The notebooks in `z-ethan/notebooks`
import it for paths, the plot style, figure composition, ReEDS output extracts, the requirement-map
fit, the PRIS loader and the text-number check. Submodules load lazily, so `import nlpaper` alone
imports no heavy dependency. Create the environment from `z-ethan/environment.yml` (or
`z-ethan/requirements.txt`) first.

**`paths`.** This module defines every location relative to the repository root `REPO`, which it
finds by walking up from its own file to the folder that contains `z-ethan/nlpaper`. It names
`ANALYSIS`, `DATA`, `NOTEBOOKS`, `RESULTS`, `EXTRACTS`, `FIGS_MAIN`, `FIGS_SI` and `TABLES`.
`exports(nb)` creates and returns `results/exports/<nb>`. `casefile(batch)`, `reeds_inputs()` and
`deflator_path()` point into the ReEDS fork. `reeds_outputs()` returns the unpacked ReEDS output
archive: it reads the environment variable `NL_REEDS_OUTPUTS`, defaults to the sibling folder
`../nuclear-learning-reeds-outputs`, and returns None with a one-line notice when the archive is
absent. `require(path, produced_by)` raises an error that names the notebook that produces a
missing file.

**`setup`.** `nlpaper.setup(threads=4)` goes in the first code cell of every notebook. It sets the
BLAS, OpenMP, numexpr and numba thread variables (only where they are unset), limits the live
thread pools with `threadpoolctl`, applies the plot style and prints one line with the Python,
numpy, pandas and matplotlib versions and the thread count. The paper's results were produced with
4 threads; a different count can change the last digits of least-squares results. The module is
callable, so `nlpaper.setup.notebook_header(name, produces)` reaches the optional header helper.

**`plotstyle`.** This module is the house plot style: palettes (`SCHED_C`, `COL`, `SENS_C`,
`ACCENT`), paper-facing names (`SCHED_SHORT`, `SCHED_LABEL`, `PCT_LABEL`, `PROGRAM_LABEL`), the
type specification (`PAPER_FONT`, `fonts()`, `font_rc()`), `apply()`, `savefig()`, panel letters,
the unit grammar `usd()` and the dollar-year multiplier `to2025(year)`, which reads the ReEDS
deflator table. It is a port of the working-tree module with no change to any colour, label or
size; only `plotly_layout` was dropped. `resolve_font(family, weight)` finds a font through
matplotlib's font manager.

**Font note.** Figures render in matplotlib's default DejaVu Sans on every machine. Only the panel
letters that `compose` stamps use Arial Bold. Where Arial is not installed (most Linux machines),
`resolve_font` substitutes Liberation Sans Bold, which has Arial's metrics, or DejaVu Sans Bold,
and prints one warning. The composed figures are then not pixel-identical to the paper's; install
Arial (for example the `ttf-mscorefonts-installer` package) for pixel identity.

**`compose`.** `compose(rows, out, letters=..., center=..., letter_pt=...)` pastes source PNGs at
their native pixel size into one multi-panel figure and stamps panel letters. The house rule holds:
letters are unique and continuous across the composed page, and a source that is internally
lettered carries its final letters (pass a blank entry in `letters` for it). The module also holds
the small paper-figure helpers `show_panel`, `source_ref`, `caption`, `write_captions`, `table`,
`savefig` and `to2024`.

**`h5io`.** Only notebook 05 opens ReEDS `outputs.h5` files. `read_key(h5path, key)` turns one
report group into a DataFrame exactly as the original analysis did: byte-string columns decode to
`str`, `Value` stays float, and `t` / `allt` become `int`. `run_file(batch, case)` locates a run in
the archive (`<batch>/<prefix><case>_outputs.h5`; prefix `test1_` for smr100, `step4_`,
`rate_design_` for ratedesign, otherwise `<batch>_`; smr100 pilots in `smr100/pilots/`).
`cases(batch)` reads the casefile columns. `extract(spec)` applies `data/extract_spec.csv` and
writes `results/extracts/<batch>/<key>.parquet` (pyarrow, zstd) plus `manifest.csv`. Every later
notebook calls `load(batch, key)`; `available(batch)` lists the extracted keys. Runs that lack a
key (the batch-3 CO2-cap runs have no `nuclear_cap_price`) and runs that never returned are
recorded as missing, not fatal. The extracts manifest also records `pilot_cases`, the smr100 pilot runs included in an extract.

`data/extract_spec.csv` has one row per extracted key. `batches` is a semicolon list or `all`.
`tech_filter` is blank or a regex matched in full against the tech column `i` (`col=regex` targets
another column). `aggregate_to` is blank, `national` (sum over region `r`), `sum:<col>;<col>`, `mean:<col>;<col>` (mean of the rows present) or `national_except:<regex>` (rows whose `i` matches keep every dimension; all other rows are summed over `r` and carry `r = "national"`).
`dims_kept` is blank or a semicolon list of dimensions to keep (Value is summed over the others).
Three example rows:

```
cap_new_ann,all,nuclear|nuclear-smr,national,,national nuclear build by year
nuclear_cap_price,all,,,,shadow price of the nuclear mandate (absent in runs without an active mandate)
systemcost,smr100;step4,,,,full system cost table
```

**`mapfit`.** The requirement-map families (M00, M0, M1, M2 and the later v2.7 to v2.9 fits) and
their leave-one-out machinery, used by notebook 10. The code is a verbatim copy of the registered
module; it holds no data.

**`pris_loader`.** Helpers that turn IAEA PRIS / RDS-2 unit data into the retirement schedule,
the committed pipeline and the construction-duration panel that the cost engine uses (notebooks 01
and 02). The code is a verbatim copy of the working-tree module.

**`numbers`.** The text-number resolver. The draft marks each quoted number with a token such as
`{m10c:eo:monetized:3pt:p05|p50|p95:2025$}`. `resolve(token, file_map)` returns the raw export
values and the rendered string; `render_all(tokens, file_map)` returns a table with token, source
file, filter, raw and rendered. The module docstring gives the token grammar and the rounding
rules. `python -m nlpaper.numbers --m10c ... --m102c ... --b17 ... --json ...` runs a self-test
against a token file.
