"""Shared helpers for the two paper-figure notebooks.

This module does three things:
1. It knows where every already-generated figure and table lives.
2. It composes multi-panel paper figures from those source PNGs without redrawing them.
3. It collects draft captions and renders standard source-reference blocks.

Design rule (Ethan, 2026-08-17): never re-plot an existing figure. Embed the
generated PNG and point at its source notebook and cell. Re-plot only when no
generated artifact exists (the three winner_boundary / npv_winner_check gap
figures). Those figures use the shared house style from z-ethan/plotstyle.py,
re-exported below.
"""

from __future__ import annotations

import datetime as _dt
import sys as _sys
import textwrap
from pathlib import Path

import pandas as pd

# ----------------------------------------------------------------------------
# Paths. This file sits at <repo>/z-ethan/paper_figures/paperlib.py.
# ----------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

# ----------------------------------------------------------------------------
# House style: z-ethan/plotstyle.py is the normative standard. Re-export its
# tokens under the names the generated notebook cells already use.
# ----------------------------------------------------------------------------
_sys.path.insert(0, str(HERE.parent))  # z-ethan (plotstyle lives there)
import plotstyle as ps  # noqa: E402

INK, MUTED, FAINT = ps.INK, ps.MUTED, ps.FAINT
GRID_C, EDGE_C, SURFACE, NEUTRAL = ps.GRID_C, ps.EDGE_C, ps.SURFACE, ps.NEUTRAL
COL, C_TINY, C_FULL = ps.COL, ps.C_TINY, ps.C_FULL
apply_style = ps.apply  # back-compat shim (generated cells call P.apply_style())
panel_letter = ps.panel_letter
letter_panels = ps.letter_panels
cmap_div = ps.cmap_div

MC = REPO / "z-ethan" / "mc"
MC_FIG, MC_EXP = MC / "figures", MC / "exports"
S3 = REPO / "z-ethan" / "step3_analysis"
S3_FIG, S3_EXP = S3 / "figures", S3 / "exports"
S4 = REPO / "z-ethan" / "step4_analysis"
S4_FIG, S4_EXP = S4 / "figures", S4 / "exports"
S3C_EXP = REPO / "z-ethan" / "step3_checks" / "exports"
S4C_EXP = REPO / "z-ethan" / "step4_checks" / "exports"
ITCFB = REPO / "z-ethan" / "itcfb_analysis"
ITCFB_FIG, ITCFB_EXP = ITCFB / "figures", ITCFB / "exports"
ITCFBM = REPO / "z-ethan" / "itcfbm_analysis"
ITCFBM_FIG, ITCFBM_EXP = ITCFBM / "figures", ITCFBM / "exports"
BD = REPO / "z-ethan" / "bridge_detection"
BD_FIG, BD_EXP = BD / "figures", BD / "exports"

OUT_FIG = HERE / "figures"
OUT_EXP = HERE / "exports"
OUT_FIG.mkdir(exist_ok=True)
OUT_EXP.mkdir(exist_ok=True)

# ----------------------------------------------------------------------------
# Schedule identity (ambition order, least to most ambitious).
# ----------------------------------------------------------------------------
SCHEDULES = ["eia", "aj", "iaea", "mck", "cop28", "eo"]
SCHED_NAME = {
    "eia": "EIA 2026 AEO high (117 GW)",
    "aj": "Abou-Jaoude moderate (134 GW)",
    "iaea": "IAEA high (172 GW)",
    "mck": "McKinsey GEP 2025 (200 GW)",
    "cop28": "COP28 tripling pledge (300 GW)",
    "eo": "2025 Executive Order (400 GW)",
}

# ----------------------------------------------------------------------------
# Deflator: ReEDS accounts in 2004 dollars; the paper reports 2024 dollars.
# Never hardcode the conversion; read it from the model input.
# ----------------------------------------------------------------------------
def to2024() -> float:
    """Multiplier from 2004$ to 2024$, from inputs/financials/deflator.csv."""
    defl = pd.read_csv(REPO / "inputs" / "financials" / "deflator.csv")
    defl.columns = ["year", "deflator"]
    return float(1.0 / defl.set_index("year")["deflator"].loc[2024])


# ----------------------------------------------------------------------------
# Embedding and composing source PNGs.
# ----------------------------------------------------------------------------
def _check(path: Path) -> Path:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Source figure not found: {path}\n"
            "Re-run its generating notebook (see the source block above this cell)."
        )
    return path


def show_panel(path):
    """Display one source PNG at native resolution, with a freshness stamp."""
    from IPython.display import Image, display

    path = _check(path)
    mtime = _dt.datetime.fromtimestamp(path.stat().st_mtime)
    print(f"{path.relative_to(REPO)}  (generated {mtime:%Y-%m-%d %H:%M})")
    display(Image(filename=str(path)))


def compose(rows, out_name, labels=True, letters=None, pad=None,
            bg=(255, 255, 255), center=False):
    """Paste source PNGs into one multi-panel figure at native pixel size.

    rows: list of rows; each row is a list of PNG paths laid out left to right.
    Panels keep their own pixel dimensions (no resampling); rows are
    top-aligned, and center=True centers rows narrower than the canvas
    (use for ragged layouts like Fig3/Fig5 instead of leaving a corner blank).
    The canvas is WHITE (the standard ground; source panels are saved on white
    too); pass bg=(r, g, b) for a deliberate one-off.
    Pixel geometry is derived from physical size at plotstyle.STD_DPI (source
    panels are saved at that dpi): pad ~ 0.16 in; letters are 10 pt bold, the
    same visual size as plotstyle.panel_letter stamps inside source figures.

    Panel letters (house rule: unique and continuous across the composed
    page; a source that is internally lettered carries the final letters):
    letters=None (default) stamps bare bold a, b, ... on every image in
    reading order; letters="" (or labels=False, the legacy switch) disables
    stamping entirely (all sources pre-lettered); a string or list with blank
    entries skips those images (e.g. letters=["", "", "e"] letters only the
    third image; letters="a" letters only the first).
    Saves to OUT_FIG/out_name, displays the result, and returns the path.
    """
    from IPython.display import Image, display
    from PIL import Image as PILImage
    from PIL import ImageDraw, ImageFont

    if pad is None:
        pad = round(0.16 * ps.STD_DPI)

    grid = [[PILImage.open(_check(p)).convert("RGBA") for p in row] for row in rows]
    row_w = [sum(im.width for im in row) + pad * (len(row) + 1) for row in grid]
    row_h = [max(im.height for im in row) + pad for row in grid]
    W, H = max(row_w), sum(row_h) + pad
    canvas = PILImage.new("RGBA", (W, H), bg + (255,))

    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf",
                                  round(10 / 72 * ps.STD_DPI))
    except OSError:
        font = ImageFont.load_default()
    draw = ImageDraw.Draw(canvas)

    if letters is None:
        letters = "abcdefghij" if labels else ""
    letter = iter(letters)
    y = pad
    for row, rw, rh in zip(grid, row_w, row_h):
        x = pad + ((W - rw) // 2 if center else 0)
        for im in row:
            canvas.paste(im, (x, y), im)
            ch = next(letter, None)
            if ch and ch.strip():
                draw.text((x + pad // 4, y + pad // 12), ch,
                          fill=(11, 11, 11, 255), font=font)
            x += im.width + pad
        y += rh
    out = OUT_FIG / out_name
    canvas.save(out)
    print(f"composed -> {out.relative_to(REPO)}  ({W}x{H} px)")
    display(Image(filename=str(out)))
    return out


def source_ref(*entries):
    """Render a standard source block: where each panel comes from and how to change it.

    Each entry: (png_path, generating_notebook, cell, inputs_description).
    """
    from IPython.display import Markdown, display

    lines = ["**Sources — edit the figure at its origin, not here:**", ""]
    for png, notebook, cell, inputs in entries:
        png = Path(png)
        rel = png.relative_to(REPO) if png.is_absolute() else png
        lines.append(f"- `{rel}` — generated by `{notebook}` ({cell}) from {inputs}")
    display(Markdown("\n".join(lines)))


# ----------------------------------------------------------------------------
# Captions and tables.
# ----------------------------------------------------------------------------
CAPTIONS: dict[str, str] = {}


def caption(tag: str, text: str):
    """Register and print a draft manuscript caption."""
    text = " ".join(text.split())
    CAPTIONS[tag] = text
    print(f"\n--- draft caption [{tag}] ---")
    print(textwrap.fill(text, width=96))


def write_captions(name: str):
    out = OUT_EXP / f"captions_{name}.txt"
    with open(out, "w", encoding="utf-8") as f:
        for tag, text in CAPTIONS.items():
            f.write(f"[{tag}]\n{textwrap.fill(text, width=96)}\n\n")
    print(f"{len(CAPTIONS)} captions -> {out.relative_to(REPO)}")


def table(csv_path, out_name=None, index_col=None, round_=None):
    """Load an exported CSV, re-export a copy next to the notebook, return the frame."""
    csv_path = _check(csv_path)
    df = pd.read_csv(csv_path, index_col=index_col)
    if round_ is not None:
        df = df.round(round_)
    if out_name:
        df.to_csv(OUT_EXP / out_name, index=index_col is not None)
        print(f"{csv_path.relative_to(REPO)} -> exports/{out_name}")
    else:
        print(f"{csv_path.relative_to(REPO)}")
    return df


# ----------------------------------------------------------------------------
# Saving — back-compat shim: generated cells pass a bare filename; the shared
# plotstyle.savefig (dpi 300, tight bbox) does the actual save.
# ----------------------------------------------------------------------------
def savefig(fig, name):
    return ps.savefig(fig, OUT_FIG / name)
