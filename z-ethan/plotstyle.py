"""z-ethan house plot style — the normative formatting standard (2026-08-17).

Every plotting notebook under z-ethan imports this module and calls
``plotstyle.apply()`` in its setup cell. This file is the single source of
truth for figure formatting; per-notebook style blocks are forbidden.

How to import from a notebook (notebooks execute with cwd = their own dir)::

    import sys; from pathlib import Path
    sys.path.insert(0, str(Path.cwd().parent))
    import plotstyle as ps
    ps.apply()

From a module with a stable file location (e.g. paper_figures/paperlib.py),
use ``Path(__file__).resolve().parents[1]`` instead of ``Path.cwd()``.

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
    standalone); ``paperlib.compose`` stamps letters only on source images
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
8.  Plotly figures (winner_boundary, tech_comparison_explainer) use
    ``plotly_layout`` so their look matches the matplotlib figures.

Provenance of the tokens: mc/winner_boundary.ipynb cell 2 ("dataviz reference
palette, light mode"), consolidated through paper_figures/paperlib.py. The
viridis schedule ramp and PCT_STYLE come from step3_analysis cell 2; SENS_C
(Okabe-Ito) from step4_analysis. dpi 300, all-notebook scope, and the Nature
title convention are Ethan's decisions of 2026-08-17.
"""

from __future__ import annotations

from pathlib import Path

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
        shown = path
    print(f"saved -> {shown}")
    return path


def panel_letter(ax, letter):
    """Stamp one Nature-style panel letter: bold lowercase, top-left.

    Anchored just LEFT of the axes' left edge (right-aligned at x=-0.02) so it
    never collides with a left-aligned categorical panel title starting at x=0.
    """
    ax.text(-0.02, 1.02, letter, transform=ax.transAxes,
            fontsize=10, fontweight="bold", color=INK,
            ha="right", va="bottom")


def letter_panels(axes):
    """Letter axes a, b, c, ... in reading order."""
    import numpy as np

    flat = np.ravel(axes)
    for ax, letter in zip(flat, "abcdefghijklmnop"):
        panel_letter(ax, letter)


# ---------------------------------------------------------------------------
# Unit-label grammar
# ---------------------------------------------------------------------------
def usd(per, basis):
    """Money unit string: usd('kW', 2022) -> '(2022$/kW)'."""
    return f"({basis}$/{per})"


# ---------------------------------------------------------------------------
# Plotly (winner_boundary, tech_comparison_explainer)
# ---------------------------------------------------------------------------
def plotly_layout(fig, **overrides):
    """Apply the house look to a plotly figure; overrides pass through."""
    axis = dict(gridcolor=GRID_C, zerolinecolor=EDGE_C, linecolor=EDGE_C,
                tickfont=dict(color=FAINT), title_font=dict(color=MUTED))
    fig.update_layout(
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        font=dict(color=MUTED, size=12),
        title_font=dict(color=INK, size=15),
        xaxis=axis, yaxis=dict(axis),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
        margin=dict(l=60, r=20, t=50, b=45),
        **overrides,
    )
    return fig
