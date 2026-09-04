"""Digitize the two figure-only literature series for lit_comparison.ipynb.

Run with the BASE python (needs PyMuPDF `fitz`; playground-env does not have it):

    python _digitize_figures.py

Inputs (local-only, `sources/`; sha256 recorded in `data/digitize_calib.json`):
  * MIT ANP-201 (Shirvan 2024), page 27, Figure 2 (left): overnight capital cost
    ($/kWe, 2024 USD) by "commercial offering" 1-7 for three programs. The chart is an
    embedded raster image, so bars are read from pixels (series colour -> bar top row ->
    calibrated against the chart's own gridlines).
  * INL "Quantifying Capital Cost Reduction Pathways" (Bolisetti, Abou-Jaoude et al.,
    June 2024), page 44, Figure 10: stacked-bar OCC (2022 $/kWe) for plants 1-13 of two
    reactor concepts, Scenario 1. The chart is VECTOR: every account bar is a filled
    rectangle in the page's drawing list, so totals are exact up to the axis calibration
    (tick-label centres, linear fit; residual < $10).

Outputs:
  * data/mit_anp201_fig2_digitized.csv, data/inl_pathways_fig10_digitized.csv
  * data/digitize_calib.json  (page numbers, colours, calibration, read errors, sha256s)
  * figures/e90_mit_fig2_overlay.png, figures/e91_inl_fig10_overlay.png (the reads drawn
    over the source pixels/rectangles, for eyeballing)
  * a printed gate G1 report: digitized values vs the reports' text-stated anchors.

Provenance of the unit counts: MIT's own table under Figure 2 (offering -> N-OAK and
year); INL's plant index (Concept A plant = 4 x 264 MWe units, Concept B = 1 x 311 MWe).
"""
import hashlib
import json
from pathlib import Path

import fitz  # PyMuPDF
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SRC = HERE / "sources"
DATA = HERE / "data"
FIG = HERE / "figures"
DATA.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)

MIT_PDF = SRC / "MIT_ANP-201_Shirvan_2024.pdf"
INL_PDF = SRC / "INL_Sort_109810_cost_pathways_2024.pdf"
MIT_PAGE, INL_PAGE = 27, 44          # 1-based


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


calib = {"mit": {}, "inl": {}}

# ----------------------------------------------------------------------------- INL (vector)
# Account colours (RGB 0-1, rounded to 3 dp) as they appear in the page drawing list.
INL_ACCT = {(0.082, 0.376, 0.51): "10 preconstruction", (0.059, 0.251, 0.086): "20 equipment",
            (0.914, 0.443, 0.196): "20 material", (0.376, 0.102, 0.345): "20 labor",
            (0.573, 0.816, 0.314): "30 indirect", (0.059, 0.62, 0.835): "50 supplementary"}
INL_PANELS = {"A": dict(series_id="inl_pathways_A", design="Concept A (4x264 MWe)", units_per_plant=4,
                        unit_mw=264.0, xmin=100, xmax=300, text_x=(0, 200)),
              "B": dict(series_id="inl_pathways_B", design="Concept B (1x311 MWe)", units_per_plant=1,
                        unit_mw=311.0, xmin=330, xmax=540, text_x=(300, 350))}

doc = fitz.open(INL_PDF)
page = doc[INL_PAGE - 1]
drawings = page.get_drawings()
textd = page.get_text("dict")
inl_rows = []
for pk, pc in INL_PANELS.items():
    # y-calibration from the tick labels ($-, $2,000 ... $14,000): value = a*y + b
    ticks = []
    for b in textd["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                t = s["text"].strip().replace("$", "").replace(",", "").replace("-", "0")
                x0, y0, x1, y1 = s["bbox"]
                if t.isdigit() and 225 < y0 and y1 < 365 and pc["text_x"][0] <= x0 < pc["text_x"][1]:
                    ticks.append((float(t), 0.5 * (y0 + y1)))
    ticks.sort()
    vals = np.array([v for v, _ in ticks])
    ys = np.array([y for _, y in ticks])
    a, b = np.polyfit(ys, vals, 1)
    resid = float(np.abs(vals - (a * ys + b)).max())
    # Bars: every 're' item of an account colour inside the panel's x-range.
    rects = []
    for dr in drawings:
        f = dr.get("fill")
        if not f:
            continue
        key = tuple(round(c, 3) for c in f)
        if key in INL_ACCT and dr["rect"].x0 > pc["xmin"] - 5 and dr["rect"].x1 < pc["xmax"] + 5 \
                and dr["rect"].width > 50:
            for it in dr["items"]:
                if it[0] == "re":
                    rects.append((INL_ACCT[key], it[1]))
    xcs = sorted(set(round(0.5 * (r.x0 + r.x1), 0) for _, r in rects))
    assert len(xcs) == 13, (pk, len(xcs))
    for j, xc in enumerate(xcs):
        col = [(acc, r) for acc, r in rects if abs(0.5 * (r.x0 + r.x1) - xc) < 2]
        # Height-based total: independent of the tick-centre intercept (bars sit on the axis).
        heights = {acc: -a * (r.y1 - r.y0) for acc, r in col}
        total = float(sum(heights.values()))
        plant = j + 1
        inl_rows.append({"series_id": pc["series_id"], "design": pc["design"], "plant": plant,
                         "n_units": plant * pc["units_per_plant"], "unit_mw": pc["unit_mw"],
                         "cum_gw": round(plant * pc["units_per_plant"] * pc["unit_mw"] / 1000.0, 4),
                         "occ": round(total, 0), "read_err": round(resid + 10.0, 0),
                         "dollar_year": 2022, "provenance": "digitized-vector",
                         **{f"acct_{acc.split()[0]}_{acc.split()[1]}": round(h, 0)
                            for acc, h in heights.items()}})
    calib["inl"][pk] = {"ticks": [(float(v), float(y)) for v, y in ticks], "usd_per_pt": float(a),
                        "intercept": float(b), "tick_fit_max_resid_usd": resid,
                        "n_bars": len(xcs), "bar_x_centres_pt": [float(x) for x in xcs]}
inl = pd.DataFrame(inl_rows)
inl.to_csv(DATA / "inl_pathways_fig10_digitized.csv", index=False)

# Overlay: redraw the extracted totals over the page render.
pix = page.get_pixmap(dpi=200, clip=fitz.Rect(70, 160, 545, 395))
pix.save(FIG / "e91_inl_fig10_overlay_base.png")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
img = plt.imread(FIG / "e91_inl_fig10_overlay_base.png")
fig, ax = plt.subplots(figsize=(11, 5.5))
ax.imshow(img, extent=(70, 545, 395, 160))
for pk, pc in INL_PANELS.items():
    c = calib["inl"][pk]
    sub = inl[inl["series_id"] == pc["series_id"]]
    y = (sub["occ"].values - c["intercept"]) / c["usd_per_pt"]
    ax.scatter(c["bar_x_centres_pt"], y, s=18, facecolor="none", edgecolor="red", lw=1.2)
    for x, yy, v in zip(c["bar_x_centres_pt"], y, sub["occ"].values):
        ax.annotate(f"{v:,.0f}", (x, yy), xytext=(0, 6), textcoords="offset points",
                    fontsize=5.5, ha="center", color="red")
ax.set_axis_off()
fig.savefig(FIG / "e91_inl_fig10_overlay.png", dpi=220, bbox_inches="tight")
(FIG / "e91_inl_fig10_overlay_base.png").unlink()

# ----------------------------------------------------------------------------- MIT (raster)
MIT_SERIES = {  # legend colour (RGB 0-255, chart image), program, unit size, per-offering N and year
    "mit_ap1000_23gw": dict(rgb=(64, 112, 192), design="AP1000 (23 GWe program, 2024-58)", unit_mw=1117.0,
                            n=[2, 4, 6, 8, 12, 16, 20], label=["FOAK (Vogtle 3&4)", "Next 2", "4-OAK", "8-OAK",
                                                                "12-OAK", "16-OAK", "20-OAK"],
                            year=[2024, 2031, 2037, 2043, 2048, 2053, 2058]),
    "mit_smr_7gw": dict(rgb=(232, 120, 48), design="300-MWe SMR (7 GWe program, 2032-56)", unit_mw=300.0,
                        n=[1, 4, 8, 12, 16, 20, 24], label=["FOAK", "4-OAK", "8-OAK", "12-OAK", "16-OAK",
                                                            "20-OAK", "24-OAK"],
                        year=[2032, 2037, 2042, 2046, 2050, 2053, 2056]),
    "mit_smr_23gw": dict(rgb=(160, 160, 160), design="300-MWe SMR (23 GWe program, 2032-58)", unit_mw=300.0,
                         n=[1, 12, 24, 36, 48, 60, 75], label=["FOAK", "12-OAK", "24-OAK", "36-OAK",
                                                               "48-OAK", "60-OAK", "75-OAK"],
                         year=[2032, 2037, 2042, 2046, 2050, 2054, 2058]),
}
# Note on N for the AP1000 chain (assumption A6, to be confirmed with the author): "FOAK" =
# Vogtle 3&4 (two units, N = 2); "Next 2" = units 3-4 (N = 4; its cost matches the report's
# text value for the next two units). MIT labels the following offerings 4-OAK, 8-OAK, 12-OAK,
# 16-OAK, 20-OAK; read literally, "4-OAK" would also be N = 4 with a different cost. We read
# "4-OAK" as the offering AFTER the next two (N = 6) and take the later labels as cumulative
# unit counts (20-OAK at 2058 matches the 23 GWe program, ~21 units). The literal label number
# is carried as `n_units_alt`.

doc = fitz.open(MIT_PDF)
page = doc[MIT_PAGE - 1]
imgs = page.get_images(full=True)
assert len(imgs) == 1, imgs
xref = imgs[0][0]
pm = fitz.Pixmap(doc, xref)
if pm.n >= 4:
    pm = fitz.Pixmap(fitz.csRGB, pm)
arr = np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.width, pm.n)[:, :, :3].astype(int)
H, W = arr.shape[:2]
# The left chart occupies roughly the left half of the image; find its plot box.
left = arr[:, : W // 2]
# Gridlines: rows where a long run of light-grey pixels exists (the chart grid colour).
grey = (np.abs(left - np.array([217, 217, 217])).max(axis=2) <= 12)
row_score = grey.sum(axis=1)
grid_rows = np.flatnonzero(row_score > 0.35 * left.shape[1])
# Cluster consecutive rows into gridlines
lines = []
for r in grid_rows:
    if lines and r - lines[-1][-1] <= 1:
        lines[-1].append(r)
    else:
        lines.append([r])
grid_y = np.array([np.mean(l) for l in lines])
# The chart draws six equally spaced light-grey lines: $0 (the axis line itself) up to $25,000.
assert len(grid_y) == 6, grid_y
axis_y = float(grid_y.max())
ys = np.sort(grid_y)[::-1]                        # bottom -> top = $0 ... $25,000
vals = np.arange(len(ys)) * 5000.0
a, b = np.polyfit(ys, vals, 1)
resid = float(np.abs(vals - (a * ys + b)).max())
px_usd = abs(a)                                   # $ per pixel
mit_rows = []
for sid, sp in MIT_SERIES.items():
    match = (np.abs(left - np.array(sp["rgb"])).max(axis=2) <= 28)
    # Bars are solid vertical runs; text and legend swatches are not. Score each column by its
    # longest contiguous run of matching pixels and remember where that run starts (bar top).
    def longest_run(colv):
        best = cur = 0
        best_start = start = None
        for i, v in enumerate(colv):
            if v:
                if cur == 0:
                    start = i
                cur += 1
                if cur > best:
                    best, best_start = cur, start
            else:
                cur = 0
        return best, best_start
    runs = [longest_run(match[:, c]) for c in range(match.shape[1])]
    col_hits = np.array([r[0] for r in runs])
    run_top = np.array([(-1 if r[1] is None else r[1]) for r in runs])
    cols = np.flatnonzero(col_hits >= 3)
    # cluster columns into bars (gap > 2 px)
    bars = []
    for c in cols:
        if bars and c - bars[-1][-1] <= 2:
            bars[-1].append(c)
        else:
            bars.append([c])
    # Keep only bar-shaped clusters: 8-14 px wide with a tall run of matching pixels (the legend
    # swatch is ~8 px tall; axis text and tick labels never form a tall run). The grey series
    # also matches text, so it is additionally anchored to the bar slot right of each orange bar.
    bars = [bb for bb in bars if 8 <= len(bb) <= 14 and col_hits[bb].max() >= 25]
    if sid == "mit_smr_23gw":
        orange_ends = [r["_x_end"] for r in mit_rows if r["series_id"] == "mit_smr_7gw"]
        bars = [bb for bb in bars if any(1 <= bb[0] - oe <= 14 for oe in orange_ends)]
    bars = sorted(bars, key=lambda bb: bb[0])
    assert len(bars) == 7, (sid, [(bb[0], bb[-1]) for bb in bars])
    for k, bb in enumerate(bars):
        # Bar top = the start row of the longest run, taken as the median over the bar's
        # interior columns (edge columns are antialiased).
        inner = bb[1:-1] if len(bb) > 4 else bb
        top = float(np.median(run_top[inner]))
        val = a * top + b
        mit_rows.append({"series_id": sid, "design": sp["design"], "offering": k + 1, "label": sp["label"][k],
                         "_x_end": float(bb[-1]),
                         "n_units": sp["n"][k],
                         "n_units_alt": ([2, 4, 4, 8, 12, 16, 20][k] if sid == "mit_ap1000_23gw" else np.nan),
                         "unit_mw": sp["unit_mw"], "cum_gw": round(sp["n"][k] * sp["unit_mw"] / 1000.0, 4),
                         "year": sp["year"][k], "occ": round(val, 0),
                         "read_err": round(resid + 1.5 * px_usd, 0), "dollar_year": 2024,
                         "provenance": "digitized-raster",
                         "_x_px": float(np.mean(bb)), "_y_px": top})
mit = pd.DataFrame(mit_rows)
calib["mit"] = {"image_xref": xref, "image_size_px": [W, H], "left_half_px": W // 2,
                "gridline_rows_px": [float(y) for y in np.sort(grid_y)], "axis_row_px": axis_y,
                "usd_per_px": float(a), "intercept": float(b), "tick_fit_max_resid_usd": resid,
                "series_rgb": {k: v["rgb"] for k, v in MIT_SERIES.items()}}
fig, ax = plt.subplots(figsize=(10, 4))
ax.imshow(arr[:, : W // 2].astype(np.uint8))
ax.scatter(mit["_x_px"], mit["_y_px"], s=22, facecolor="none", edgecolor="red", lw=1.2)
for _, r in mit.iterrows():
    ax.annotate(f"{r['occ']:,.0f}", (r["_x_px"], r["_y_px"]), xytext=(0, 5), textcoords="offset points",
                fontsize=5.5, ha="center", color="red")
for y in grid_y:
    ax.axhline(y, color="cyan", lw=0.4)
if axis_y is not None:
    ax.axhline(axis_y, color="magenta", lw=0.6)
ax.set_axis_off()
fig.savefig(FIG / "e90_mit_fig2_overlay.png", dpi=220, bbox_inches="tight")
mit.drop(columns=["_x_px", "_y_px", "_x_end"]).to_csv(DATA / "mit_anp201_fig2_digitized.csv", index=False)

# ----------------------------------------------------------------------------- gate G1
print("=== INL Fig 10 (vector-exact totals, 2022 $/kWe) ===")
print(inl[["series_id", "plant", "n_units", "cum_gw", "occ", "read_err"]].to_string(index=False))
print("\n=== MIT Fig 2 left (raster read, 2024 $/kWe) ===")
print(mit[["series_id", "offering", "label", "n_units", "cum_gw", "year", "occ", "read_err"]].to_string(index=False))

g1 = []
A = inl[inl.series_id == "inl_pathways_A"].set_index("plant")["occ"]
B = inl[inl.series_id == "inl_pathways_B"].set_index("plant")["occ"]
g1.append(("INL A plant 1 = 12,800 (text, rounded $100)", A[1], 12800, 100 + inl.read_err.max()))
g1.append(("INL A target 3,600 reached after 11 plants -> plant 12 <= 3,650", A[12], 3600, 100 + inl.read_err.max()))
g1.append(("INL A order-book average = 5,000 (text)", A.mean(), 5000, 100 + inl.read_err.max()))
g1.append(("INL B order-book average = 5,900 (text)", B.mean(), 5900, 100 + inl.read_err.max()))
ap = mit[mit.series_id == "mit_ap1000_23gw"].set_index("offering")["occ"]
g1.append(("MIT AP1000 FOAK (Vogtle) ~15,000 (text)", ap[1], 15000, 300 + mit.read_err.max()))
g1.append(("MIT AP1000 'Next 2' inside 8,300-10,375 (text range)", ap[2], (8300, 10375), mit.read_err.max()))
g1.append(("MIT AP1000 NOAK 4,625-4,750 (text) = last offering", ap[7], (4625, 4750), mit.read_err.max()))
sm7 = mit[mit.series_id == "mit_smr_7gw"].set_index("offering")["occ"]
sm23 = mit[mit.series_id == "mit_smr_23gw"].set_index("offering")["occ"]
g1.append(("MIT SMR FOAK ~20,000 (both programs, chart)", sm7[1], 20000, 300 + mit.read_err.max()))
print("\n=== Gate G1: digitized values vs text-stated anchors ===")
allok = True
for name, got, want, tol in g1:
    if isinstance(want, tuple):
        ok = want[0] - tol <= got <= want[1] + tol
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: {got:,.0f} vs [{want[0]:,}-{want[1]:,}] +-{tol:.0f}")
    else:
        ok = abs(got - want) <= tol
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: {got:,.0f} vs {want:,} +-{tol:.0f}")
    allok &= bool(ok)
calib["gate_G1"] = {"all_pass": bool(allok),
                    "checks": [{"name": n, "got": float(g), "want": (list(w) if isinstance(w, tuple) else w),
                                "tol": float(t)} for n, g, w, t in g1]}
calib["sources"] = {"mit_pdf": {"file": MIT_PDF.name, "page": MIT_PAGE, "sha256": sha256(MIT_PDF)},
                    "inl_pdf": {"file": INL_PDF.name, "page": INL_PAGE, "sha256": sha256(INL_PDF)}}
calib["mit_unit_map_note"] = ("A6: n_units = cumulative units per MIT's table under Fig 2 with FOAK = Vogtle 3&4 "
                              "(N = 2), 'Next 2' = units 3-4 (N = 4), '4-OAK' read as the offering after the "
                              "next two (N = 6), then 8/12/16/20-OAK literal. n_units_alt = the literal label "
                              "number (4-OAK -> 4). Author confirmation requested.")
(DATA / "digitize_calib.json").write_text(json.dumps(calib, indent=2), encoding="utf-8")
print(f"\nG1 {'PASS' if allok else 'FAIL'} -> data/digitize_calib.json, data/*_digitized.csv, figures/e90/e91")
