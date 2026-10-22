"""House plot style of the analysis — the normative formatting standard (2026-08-17).

Every plotting notebook imports this module and applies it in its setup cell
(``nlpaper.setup()`` calls ``apply()``). This file is the single source of
truth for figure formatting; per-notebook style blocks are forbidden.

How to import from a notebook::

    import nlpaper
    nlpaper.setup()                      # applies these rcParams
    from nlpaper import plotstyle as ps

Port note (public repository, 2026-09-25). This module is a port of the
working tree's ``plotstyle.py`` with no change to any colour, label, size or
rcParam. Four things changed: ``to2025`` reads the deflator through
``nlpaper.paths.deflator_path()``; ``resolve_font`` is new (``compose`` uses it
for the Arial Bold panel letters); ``plotly_layout`` was dropped, because only
retired plotly notebooks (winner_boundary, tech_comparison_explainer) called
it; the docstring's import recipe changed. Every other public name is used by
at least one paper-facing notebook or is a dependency of one that is (CYCLE
feeds ``apply``; PAPER_WIDTH_IN feeds ``fonts``).

Fonts. ``apply()`` does not set a font family, so figures render in
matplotlib's default DejaVu Sans on every machine (as the paper's figures do).
Only the panel letters that ``compose`` stamps use Arial Bold. Where Arial is
not installed, ``resolve_font`` substitutes Liberation Sans (metric-compatible
with Arial) or DejaVu Sans and warns once; pixel identity with the paper's
composed figures needs Arial.

The standard
============
1.  Saved figures use ``plotstyle.savefig`` (dpi 300, tight bbox, opaque
    WHITE background). Transparency was tried on 2026-08-17 and rejected:
    alpha fill-between bands need an opaque ground to composite correctly.
    Inline display stays at figure.dpi 110.
2.  Titles follow the Nature Energy convention: saved figures carry NO
    suptitle and NO descriptive title. The description lives in the caption
    (paper items) or the adjacent markdown cell (analysis notebooks).
    In-panel text is allowed only for short categorical labels that
    distinguish otherwise-identical panels (schedule name, tech name).
    Where a title must remain, it is left-aligned (rcParam
    ``axes.titlelocation: left``). Title text that encodes a legend must be
    moved to a legend, an in-axes annotation, or the caption — never dropped.
3.  Panel letters: heterogeneous multi-panel figures letter their axes with
    ``letter_panels`` (bold lowercase, Nature style). Homogeneous
    small-multiples grids whose panels differ only by a categorical label
    (the 2x3 schedule grids) are NOT lettered. In a composed paper figure the
    letters must be UNIQUE AND CONTINUOUS across the whole page (a, b, c, ...
    in reading order). A source figure that is internally lettered carries
    the FINAL letters for its panels (even when that means it starts at "c"
    standalone); ``nlpaper.compose`` stamps letters only on source images
    that carry none (pass ``letters=`` with a blank entry per pre-lettered
    image). Never letter the same panel at both levels (2026-08-17 audit:
    that produced duplicate a/b letters inside lettered figures).
4.  Colors come from the semantic palettes below. One concept, one hue,
    everywhere: schedules use SCHED_C, the two techs use COL, percentile
    weight uses PCT_STYLE, step4 market arms use SENS_C, experience-base
    strata use C_TINY / C_FULL. Ad-hoc hex codes in notebooks are forbidden;
    one-off accents come from ACCENT.
5.  Axis labels are lowercase with units in parentheses, built with ``usd``
    for money: ``(2022$/kW)`` for ATB-basis MC quantities (they really are
    2022 dollars), ``(2024$/kW-yr)`` / ``(2024$B/yr)`` for ReEDS-side
    quantities. No spaces inside the unit; dollar-year prefix, never suffix.
    Mathtext stays ON (``text.parse_math`` default True): log-axis tick
    labels are mathtext and render as raw ``$mathdefault{10^4}$`` strings
    (with a leading backslash) without it (found 2026-08-17 in the ATB
    inversion figure). A single
    literal ``$`` in a label renders literally; never put TWO ``$`` in one
    rendered string — matplotlib would parse the span between them as math.
6.  Grids are on (rc), light, and always below artists; top/right spines are
    off; legends are frameless. Do not call ``ax.grid(alpha=...)`` locally —
    the rc grid supersedes it. Heatmaps call ``ax.grid(False)``.
7.  Existing output filenames are frozen (paper_figures and
    build_paper_draft.py reference them by name). Naming exception, accepted:
    mc_cost_trajectories PNGs carry no ``mc_`` prefix.
8.  (Retired: the plotly figures and their ``plotly_layout`` helper are not
    part of the public analysis.)

Provenance of the tokens: the retired winner_boundary notebook, cell 2 ("dataviz reference
palette, light mode"), consolidated through the paper-figure helper (now ``nlpaper.compose``). The
viridis schedule ramp and PCT_STYLE come from step3_analysis cell 2; SENS_C
(Okabe-Ito) from step4_analysis. dpi 300, all-notebook scope, and the Nature
title convention are Ethan's decisions of 2026-08-17.
"""

from __future__ import annotations

import warnings
from functools import lru_cache
from pathlib import Path

from . import paths as _paths

# ---------------------------------------------------------------------------
# Saved-figure resolution. Inline display stays at figure.dpi 110.
# ---------------------------------------------------------------------------
STD_DPI = 300

# ---------------------------------------------------------------------------
# Ink / surface tokens (canonical names; identical hexes were previously also
# known as INK2/MUTED/GRID/BASE in winner_boundary and atb_parameter_space).
# ---------------------------------------------------------------------------
INK, MUTED, FAINT = "#0b0b0b", "#52514e", "#898781"
GRID_C, EDGE_C = "#e1e0d9", "#c3c2b7"
# SURFACE is the figure/axes ground. Pure white (Ethan, 2026-08-17; was the
# off-white #fcfcfb) so saved figures sit flush on a journal page.
SURFACE, NEUTRAL = "#ffffff", "#f0efec"

# ---------------------------------------------------------------------------
# Semantic palettes — one concept, one hue, in every notebook.
# ---------------------------------------------------------------------------
COL = {"large": "#2a78d6", "smr": "#eb6834"}  # tech identity
TECH_LABEL = {"large": "Large LWR (1 GWe)", "smr": "SMR (300 MWe)"}

C_TINY, C_FULL = "#1baf7a", "#4a3aa7"  # experience-base strata (aqua / violet)

# Schedule identity: fixed, ambition-ordered viridis segment (perceptually
# ordered, colorblind-safe). Values = mpl.cm.viridis(linspace(0.02, 0.72, 6)),
# hardcoded so importing this module never needs matplotlib.
SCHED_ORDER = ["eia", "aj", "iaea", "mck", "cop28", "eo"]
SCHED_C = {
    "eia": "#46085c", "aj": "#453781", "iaea": "#355f8d",
    "mck": "#26828e", "cop28": "#20a386", "eo": "#4ec36b",
}

# Paper-facing names (2026-09-03 de-jargon pass for the coauthor review; 2026-09-18
# the paper's own terms: a Monte Carlo draw is a "sample", never a "world", and the
# Abou-Jaoude schedule is the "ATB moderate" target): one short name per schedule
# code, one label per cost-sample percentile, one name per priced program. Every
# figure that labels a schedule, a percentile sample or a program uses these, so
# the same word means the same thing on every panel. The internal codes
# (eia/aj/.., p05/p50/p95, smr100/large100) stay in file names, column names and
# case names only - never in saved pixels.
# 2026-09-23 (Ethan, comments C7/C14/C21): target names are proper names, so every word is
# capitalized wherever a figure or a caption prints one.
SCHED_SHORT = {"eia": "EIA AEO High", "aj": "ATB Moderate", "iaea": "IAEA High",
               "mck": "McKinsey", "cop28": "COP28", "eo": "2025 EO"}
SCHED_GW = {"eia": 117, "aj": 134, "iaea": 172, "mck": 200, "cop28": 300, "eo": 400}
SCHED_LABEL = {k: f"{SCHED_SHORT[k]} ({SCHED_GW[k]} GW)" for k in SCHED_ORDER}
# 2026-09-23 (Ethan C23, the SI pass): a percentile case is named by its percentile, never
# by an adjective and never as "median sample": "median" names the median statistic of a
# distribution, not one drawn cost sample.
PCT_LABEL = {"p05": "P5 sample", "p50": "P50 sample", "p95": "P95 sample"}
PCT_SHORT = {"p05": "P5", "p50": "P50", "p95": "P95"}
PROGRAM_LABEL = {"smr100": "SMR program", "large100": "large-reactor program"}

# Percentile weight inside a schedule hue: p05 light, p50 solid, p95 dashed.
PCT_STYLE = {
    "p05": dict(lw=1.2, alpha=0.55, ls="-"),
    "p50": dict(lw=2.2, alpha=1.00, ls="-"),
    "p95": dict(lw=1.6, alpha=0.85, ls="--"),
}

# Step-4 market arms: Okabe-Ito (colorblind-safe); base world stays ink-grey.
# Okabe-Ito is reserved for these arms — never reuse it for schedules.
SENS_C = {
    "gaslo": "#56b4e9", "gashi": "#0072b2", "demhi": "#e69f00",
    "relo": "#009e73", "rehi": "#d55e00", "translim": "#cc79a7",
    "co2cap": "#a89f00",   # the seventh world (batch 3, 2026-09-18): Okabe-Ito yellow darkened for print
}
BASE_C = "#4a4945"

# One-off accents for quantities with no semantic palette of their own.
ACCENT = {
    "blue": "#2a78d6", "orange": "#eb6834", "green": "#1baf7a",
    "violet": "#4a3aa7", "red": "#c2404f", "gold": "#b5850a",
}
CYCLE = list(ACCENT.values())  # default prop_cycle

# Colormaps: CMAP_SEQ for sequential heatmaps; CMAP_DIV for anything
# diverging around a large-vs-smr midpoint (blue -> neutral -> orange).
CMAP_SEQ = "cividis"


def cmap_div():
    """House diverging colormap: COL['large'] -> NEUTRAL -> COL['smr']."""
    from matplotlib.colors import LinearSegmentedColormap

    return LinearSegmentedColormap.from_list(
        "large_smr", [COL["large"], NEUTRAL, COL["smr"]])


# Figsize width bands (inches): single / wide-single / full multi-panel.
# Heights stay per-figure.
W1, W2, W3 = 6.4, 9.0, 13.0


# ---------------------------------------------------------------------------
# Paper type specification (2026-09-24, Ethan's comment E11)
# ---------------------------------------------------------------------------
# One type specification for every main figure. Ethan: "Figure text should be
# consistent throughout the paper. We can't have different tick label and legend
# sizes between figures. Find a middle ground that is readable but fits the
# denser figures."
#
# PAPER_FONT is stated in PRINTED points - the size the reader measures on the
# page, where every main figure is placed at PAPER_WIDTH_IN inches wide. A
# figure drawn on a canvas wider than that is shrunk by the page, so the points
# an emitter must ask matplotlib for are larger than the printed points by the
# ratio canvas width / printed width. `fonts()` does that arithmetic, and
# PAPER_CANVAS_IN records the composed canvas width of each main figure, so one
# dict and one function decide the type of the whole figure set.
#
# The values are the middle ground Ethan asked for: they are readable at 6.5 in
# and they fit Fig 5, the densest figure (two 2x3 blocks of panels plus a
# legend strip).
PAPER_WIDTH_IN = 6.5          # the width every main figure is printed at

PAPER_FONT = dict(
    tick=8.0,                 # tick labels
    axis_label=9.0,           # x and y axis labels
    panel_title=9.5,          # the name above a panel
    legend=8.0,               # legend entries
    annotation=8.0,           # text drawn inside a panel (end labels, notes)
    panel_letter=10.0,        # the bold a, b, ... stamps
)

# Composed width of each main figure, in inches, as `compose.compose` saves it
# (the source panels at their own size plus a 0.16 in pad on each side). Measure
# the composed PNG and update this table if a figure's layout changes.
PAPER_CANVAS_IN = {
    "fig1": 6.65,             # lit_comparison e11, one panel row
    "fig2": 6.65,             # step3 f01b over the mc 2x2 block
    "fig3": 8.62,             # rate_design2 n104c
    "fig4": 8.62,             # rate_design2 n105 over n106
    "fig5": 8.62,             # market_transfer y05, y03, y06
    "fig6": 8.62,             # voi y01
}


def fonts(canvas_width_in=PAPER_WIDTH_IN, **overrides):
    """PAPER_FONT converted to the points to author on a canvas this wide.

    Pass the composed width of the figure the emitter feeds, in inches (the
    PAPER_CANVAS_IN entry for it). The returned sizes print at the PAPER_FONT
    values once the page scales that canvas to PAPER_WIDTH_IN, so two figures
    composed at different widths still carry the same type on the page.
    Keyword overrides replace single entries and are scaled the same way.
    """
    spec = dict(PAPER_FONT)
    spec.update(overrides)
    scale = float(canvas_width_in) / PAPER_WIDTH_IN
    return {k: round(v * scale, 2) for k, v in spec.items()}


def font_rc(canvas_width_in=PAPER_WIDTH_IN, **overrides):
    """`fonts()` as an rcParams dict, for `matplotlib.rc_context`.

    Covers the sizes an emitter usually leaves to the defaults; anything the
    emitter sets explicitly still wins, so set those from `fonts()` too.
    """
    f = fonts(canvas_width_in, **overrides)
    return {"font.size": f["tick"], "axes.labelsize": f["axis_label"],
            "axes.titlesize": f["panel_title"], "xtick.labelsize": f["tick"],
            "ytick.labelsize": f["tick"], "legend.fontsize": f["legend"]}


# ---------------------------------------------------------------------------
# rcParams
# ---------------------------------------------------------------------------
def apply():
    """Apply the house style to matplotlib. Call once per notebook, at setup."""
    import matplotlib as mpl
    from cycler import cycler

    mpl.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE, "axes.edgecolor": EDGE_C,
        "axes.labelcolor": MUTED, "text.color": INK,
        "xtick.color": FAINT, "ytick.color": FAINT,
        "axes.grid": True, "grid.color": GRID_C, "grid.linewidth": 0.6,
        "axes.axisbelow": True, "axes.linewidth": 0.8,
        "font.size": 9, "axes.titlesize": 10, "axes.titlecolor": INK,
        "axes.titlelocation": "left",
        "axes.spines.top": False, "axes.spines.right": False,
        "figure.dpi": 110, "legend.frameon": False,
        # parse_math stays True (mpl default): log tick labels are mathtext.
        # Money labels carry a SINGLE literal $ and render literally.
        "axes.prop_cycle": cycler(color=CYCLE),
    })


# ---------------------------------------------------------------------------
# Saving and lettering
# ---------------------------------------------------------------------------
def savefig(fig, path, dpi=None):
    """Save a figure the standard way: STD_DPI, tight bbox, white ground."""
    path = Path(path)
    fig.savefig(path, dpi=dpi or STD_DPI, bbox_inches="tight",
                facecolor=SURFACE)
    try:
        shown = path.relative_to(Path.cwd())
    except ValueError:
        shown = _paths.rel(path)   # repo-relative, so no machine path is printed
    print(f"saved -> {shown}")
    return path


def panel_letter(ax, letter, size=None):
    """Stamp one Nature-style panel letter: bold lowercase, top-left.

    Anchored just LEFT of the axes' left edge (right-aligned at x=-0.02) so it
    never collides with a left-aligned categorical panel title starting at x=0.
    `size` defaults to PAPER_FONT["panel_letter"]; a main figure on a wider
    canvas passes fonts(width)["panel_letter"].
    """
    ax.text(-0.02, 1.02, letter, transform=ax.transAxes,
            fontsize=PAPER_FONT["panel_letter"] if size is None else size,
            fontweight="bold", color=INK, ha="right", va="bottom")


def letter_panels(axes, size=None):
    """Letter axes a, b, c, ... in reading order."""
    import numpy as np

    flat = np.ravel(axes)
    for ax, letter in zip(flat, "abcdefghijklmnop"):
        panel_letter(ax, letter, size=size)


# ---------------------------------------------------------------------------
# Unit-label grammar
# ---------------------------------------------------------------------------
def usd(per, basis):
    """Money unit string: usd('kW', 2022) -> '(2022$/kW)'."""
    return f"({basis}$/{per})"


# ---------------------------------------------------------------------------
# Dollar-year conversion (2026-09-23: the paper reports 2025 dollars)
# ---------------------------------------------------------------------------
PAPER_DOLLAR_YEAR = 2025


def to2025(from_year):
    """Multiplier that takes a value in ``from_year`` dollars to 2025 dollars.

    The paper reports every money quantity in 2025 dollars (Ethan, 2026-09-23).
    The chain's exports keep their native dollar years (2022$ for the ATB-basis
    MC quantities, 2024$ for the ReEDS-side quantities, 2004$ for raw ReEDS
    accounts); convert at the point of display with this multiplier. Reads
    ``inputs/financials/deflator.csv`` (the model's own table), never a literal:
    to2025(2024) = 1.0260, to2025(2022) = 1.0990, to2025(2004) = 1.7021.
    """
    import pandas as pd
    path = _paths.require(_paths.deflator_path(), "the ReEDS fork (inputs/financials)")
    defl = pd.read_csv(path)
    defl.columns = ["year", "deflator"]
    d = defl.set_index("year")["deflator"]
    return float(d.loc[int(from_year)] / d.loc[PAPER_DOLLAR_YEAR])


# ---------------------------------------------------------------------------
# Font resolution (public-repository addition, 2026-09-25)
# ---------------------------------------------------------------------------
FONT_FALLBACKS = ("Liberation Sans", "DejaVu Sans")


@lru_cache(maxsize=None)
def resolve_font(family="Arial", weight="normal"):
    """Path of the font file for ``family`` at ``weight`` ("normal" or "bold").

    Looks the family up with matplotlib's font manager, never with a
    hard-coded file path. If ``family`` is not installed, tries Liberation Sans
    (metric-compatible with Arial) and then DejaVu Sans (bundled with
    matplotlib), and warns ONCE naming the substitute: the paper's composed
    figures were stamped in Arial Bold, so pixel identity needs Arial.
    """
    from matplotlib import font_manager
    from matplotlib.font_manager import FontProperties

    for fam in (family, *[f for f in FONT_FALLBACKS if f != family]):
        try:
            path = font_manager.findfont(FontProperties(family=fam, weight=weight),
                                         fallback_to_default=False)
        except ValueError:
            continue
        if fam != family:
            msg = (f"nlpaper.plotstyle: font {family!r} ({weight}) is not installed; "
                   f"using {fam!r} ({Path(path).name}). Composed figures will not be "
                   f"pixel-identical to the paper; install {family} for that.")
            warnings.warn(msg, stacklevel=2)
            print("WARNING:", msg)
        return path
    raise RuntimeError(f"nlpaper.plotstyle: no usable font for {family!r} ({weight}).")
