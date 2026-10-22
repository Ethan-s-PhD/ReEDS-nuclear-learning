"""Compose multi-panel paper figures from source PNGs, and small paper-figure helpers.

Port of the working tree's ``paper_figures/paperlib.py``. The design rule is
unchanged (Ethan, 2026-08-17): never re-plot an existing figure. A composed
paper figure pastes the source PNGs that the analysis notebooks saved, at their
native pixel size, and stamps panel letters.

What changed in the port: no absolute paths (outputs go under
``nlpaper.paths``); the Arial Bold panel-letter font comes from
``plotstyle.resolve_font("Arial", "bold")`` instead of a Windows font path;
``compose`` takes the output path (a bare file name lands in
``paths.FIGS_MAIN``) and ``show=False`` skips the inline display. The
per-folder path constants (MC_FIG, S3_EXP, ...) and the stale long schedule
names (SCHED_NAME) were dropped; use ``paths.exports(nb)`` and
``plotstyle.SCHED_SHORT`` / ``SCHED_LABEL``.
"""

from __future__ import annotations

import datetime as _dt
import textwrap
from pathlib import Path

from . import paths
from . import plotstyle as ps

# Re-exports under the names the paper-figure cells use (P.SCHEDULES, P.SCHED_SHORT, P.ps).
SCHEDULES = list(ps.SCHED_ORDER)
SCHED_SHORT = ps.SCHED_SHORT
panel_letter = ps.panel_letter
letter_panels = ps.letter_panels
apply_style = ps.apply
to2025 = ps.to2025


def to2024() -> float:
    """Multiplier from 2004$ to 2024$, from inputs/financials/deflator.csv."""
    import pandas as pd

    defl = pd.read_csv(paths.require(paths.deflator_path(), "the ReEDS fork (inputs/financials)"))
    defl.columns = ["year", "deflator"]
    return float(1.0 / defl.set_index("year")["deflator"].loc[2024])


def _check(path) -> Path:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Source figure not found: {paths.rel(path)}\n"
            "Re-run its generating notebook (see the source block above this cell).")
    return path


def _display(path: Path) -> None:
    try:
        from IPython import get_ipython
        from IPython.display import Image, display
    except ImportError:
        return
    if get_ipython() is not None:
        display(Image(filename=str(path)))


def show_panel(path):
    """Display one source PNG at native resolution, with a freshness stamp."""
    path = _check(path)
    mtime = _dt.datetime.fromtimestamp(path.stat().st_mtime)
    print(f"{paths.rel(path)}  (generated {mtime:%Y-%m-%d %H:%M})")
    _display(path)


def _out_path(out, out_dir=None) -> Path:
    out = Path(out)
    if not out.is_absolute() and len(out.parts) == 1:
        out = Path(out_dir or paths.FIGS_MAIN) / out
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def compose(rows, out, labels=True, letters=None, pad=None,
            bg=(255, 255, 255), center=False, letter_pt=None, show=True, out_dir=None):
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
    letter_pt overrides that size (2026-09-24, Ethan E11): a main figure whose
    canvas is wider than plotstyle.PAPER_WIDTH_IN is shrunk by the page, so it
    passes plotstyle.fonts(width)["panel_letter"] and its letters print at the
    same size as every other figure's.

    Panel letters (house rule: unique and continuous across the composed
    page; a source that is internally lettered carries the final letters):
    letters=None (default) stamps bare bold a, b, ... on every image in
    reading order; letters="" (or labels=False, the legacy switch) disables
    stamping entirely (all sources pre-lettered); a string or list with blank
    entries skips those images (e.g. letters=["", "", "e"] letters only the
    third image; letters="a" letters only the first). Never letter the same
    panel at both levels.

    The letters are drawn in Arial Bold, found by
    ``plotstyle.resolve_font("Arial", "bold")``; without Arial a substitute is
    used and a warning names it.

    out: output path; a bare file name is placed in ``out_dir`` (default
    ``paths.FIGS_MAIN``). Saves, displays the result in a notebook (show=True),
    and returns the path.
    """
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
        font = ImageFont.truetype(
            ps.resolve_font("Arial", "bold"),
            round((10 if letter_pt is None else letter_pt) / 72 * ps.STD_DPI))
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
    out = _out_path(out, out_dir)
    canvas.save(out)
    print(f"composed -> {paths.rel(out)}  ({W}x{H} px)")
    if show:
        _display(out)
    return out


def source_ref(*entries):
    """Render a standard source block: where each panel comes from and how to change it.

    Each entry: (png_path, generating_notebook, cell, inputs_description).
    """
    lines = ["**Sources — edit the figure at its origin, not here:**", ""]
    for png, notebook, cell, inputs in entries:
        lines.append(f"- `{paths.rel(png)}` — generated by `{notebook}` ({cell}) from {inputs}")
    text = "\n".join(lines)
    try:
        from IPython import get_ipython
        from IPython.display import Markdown, display
        if get_ipython() is not None:
            display(Markdown(text))
            return
    except ImportError:
        pass
    print(text)


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


def write_captions(name: str, out_dir=None) -> Path:
    """Write every registered caption to ``<out_dir>/captions_<name>.txt`` (default TABLES)."""
    out_dir = Path(out_dir or paths.TABLES)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"captions_{name}.txt"
    with open(out, "w", encoding="utf-8") as f:
        for tag, text in CAPTIONS.items():
            f.write(f"[{tag}]\n{textwrap.fill(text, width=96)}\n\n")
    print(f"{len(CAPTIONS)} captions -> {paths.rel(out)}")
    return out


def table(csv_path, out_name=None, index_col=None, round_=None, out_dir=None):
    """Load an exported CSV, optionally re-export a copy (default into TABLES), return the frame."""
    import pandas as pd

    csv_path = _check(csv_path)
    df = pd.read_csv(csv_path, index_col=index_col)
    if round_ is not None:
        df = df.round(round_)
    if out_name:
        out_dir = Path(out_dir or paths.TABLES)
        out_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_dir / out_name, index=index_col is not None)
        print(f"{paths.rel(csv_path)} -> {paths.rel(out_dir / out_name)}")
    else:
        print(f"{paths.rel(csv_path)}")
    return df


def savefig(fig, name, out_dir=None):
    """Save a figure with ``plotstyle.savefig``; a bare name lands in ``out_dir`` (default FIGS_MAIN)."""
    return ps.savefig(fig, _out_path(name, out_dir))
