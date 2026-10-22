"""Compose multi-panel paper figures from source PNGs.

Port of the working tree's ``paper_figures/paperlib.py``. The design rule is
unchanged (Ethan, 2026-08-17): never re-plot an existing figure. A composed
paper figure pastes the source PNGs that the analysis notebooks saved, at their
native pixel size, and stamps panel letters.

What changed in the port: no absolute paths; the Arial Bold panel-letter font
comes from ``plotstyle.resolve_font("Arial", "bold")`` instead of a Windows font
path; ``compose`` takes the output path and ``show=False`` skips the inline
display. The EF kit (2026-10-22) keeps only ``compose``: no notebook of the kit
called the other paper-figure helpers or the re-exported style names.
"""

from __future__ import annotations

from pathlib import Path

from . import paths
from . import plotstyle as ps


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


def _out_path(out, out_dir=None) -> Path:
    out = Path(out) if out_dir is None else Path(out_dir) / out
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

    out: output path, or a file name inside ``out_dir``. Saves, displays the
    result in a notebook (show=True), and returns the path.
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
