# nlpaper

`nlpaper` is the only non-notebook code of the analysis. The notebooks in `z-ethan/notebooks`
import it for paths, the plot style, figure composition and the PRIS loader. Submodules load
lazily, so `import nlpaper` alone imports no heavy dependency. Create the environment from
`z-ethan/environment.yml` first.

The public package of paper 1 had three more modules: `h5io` (the ReEDS `outputs.h5` reader and
extracts), `mapfit` (the requirement-map fit) and `numbers` (the text-number resolver of the draft).
No notebook of this kit used them, so the kit dropped them on 2026-10-22. Commit `1099bc9` holds
the last copies.

**`paths`.** This module defines every location relative to the repository root `REPO`, which it
finds by walking up from its own file to the folder that contains `z-ethan/nlpaper`. It names
`ANALYSIS`, `DATA`, `NOTEBOOKS`, `RESULTS`, `FIGS_MAIN`, `FIGS_SI` and `TABLES`.
`exports(nb)` creates and returns `results/exports/<nb>`. `reeds_inputs()` and `deflator_path()`
point into the ReEDS fork. `reeds_outputs()` returns the unpacked ReEDS output archive: it reads
the environment variable `NL_REEDS_OUTPUTS`, defaults to the sibling folder
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

**`pris_loader`.** Helpers that turn IAEA PRIS / RDS-2 unit data into the retirement schedule,
the committed pipeline and the construction-duration panel that the cost engine uses (all four
notebooks). This module is a shim: the code lives in `z-ethan/mc/pris_loader.py`, because the ReEDS
input generator `inputs/nuclear_learning/_generate_cap_trajectories.py` reads it there. The shim
keeps one copy of the loader and one unit list for both readers.
