"""Digitize the figure-only series added on 2026-09-08 (second batch) for lit_comparison.ipynb.

Run with the BASE python (needs PyMuPDF `fitz`, scipy; playground-env lacks fitz):

    python _digitize_figures_b.py

Inputs (local-only, `sources/`; sha256 recorded in `data/digitize_calib_b.json`):
  * MIT ANP-TR-194 (Stewart & Shirvan, June 2022), page 58 Figure 2.24 (overnight TOTAL cost,
    FOAK and 10-OAK, eight reactor architectures, 2018 $/kWe) and page 59 Figure 2.25 (cumulative
    overnight cost, $B, against cumulative capacity, MWe, for sequential units 1-10 of each
    architecture). Both charts are VECTOR: bars are filled rectangles and the Fig 2.25 markers are
    small filled paths whose centres are exact, so every value is exact up to the axis
    calibration (tick-label centres, linear fit). Unit k's cost = the k-th increment of cumulative
    cost divided by the k-th increment of capacity; unit 1 and unit 10 are cross-checked against
    the Fig 2.24 bars and against the text anchors of Table 2.14.
  * IEA "The Path to a New Era for Nuclear Energy" (Jan 2025), page 50 Figure 2.4 (SMR capital
    cost, USD 2023 per kW, US and EU / China / India, 2030-2050, STEPS / APS / NZE + large-scale
    reactor) and page 63 Figure 2.11 (left: SMR construction cost in 2040, APS vs High SMR Case;
    right: global installed SMR capacity by scenario and case, 2025-2050). VECTOR.
  * Breakthrough Institute "Advancing Nuclear Energy" (2022), page 41 Figure 2-6: NOAK-to-FOAK
    overnight-cost ratio against cumulative capacity (GW, log) for SMR / ARTES / HTGR under four
    cost x learning scenarios. RASTER (813 x 434 px embedded image). Only the 2050 END POINT of
    each of the twelve curves carries information beyond the report's own equation B-2, so the
    read is: colour -> technology, marker shape -> scenario, rightmost marker -> end point. The
    ratio at the end point is compared with equation B-2 evaluated at the read capacity (with the
    $1,800/kW floor) as the identification check.

Outputs:
  * data/mit_anp194_fig225_digitized.csv, data/iea_2025_digitized.csv, data/bti_fig26_endpoints.csv
  * data/digitize_calib_b.json (pages, colours, calibrations, read errors, sha256s, gate G1b)
  * figures/e92_anp194_overlay.png, e93_iea_overlay.png, e94_bti_overlay.png
"""
import hashlib
import json
from pathlib import Path

import fitz  # PyMuPDF
import numpy as np
import pandas as pd
from PIL import Image

HERE = Path(__file__).resolve().parent
SRC = HERE / "sources"
DATA = HERE / "data"
FIG = HERE / "figures"

SS_PDF = SRC / "MIT_ANP-194_Stewart_Shirvan_uncertainty.pdf"
IEA_PDF = SRC / "IEA_2025_Path_to_New_Era_Nuclear.pdf"
BTI_PDF = SRC / "Breakthrough_Advancing_Nuclear_Energy_v3.pdf"
SS_P224, SS_P225, IEA_P24, IEA_P211, BTI_P26 = 58, 59, 50, 63, 41      # 1-based page numbers


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tick_fit(pairs):
    """pairs = [(value, coordinate)]; returns (a, b, max_resid) with value = a*coord + b."""
    v = np.array([p[0] for p in pairs], float)
    c = np.array([p[1] for p in pairs], float)
    a, b = np.polyfit(c, v, 1)
    return float(a), float(b), float(np.abs(v - (a * c + b)).max())


def text_lines(page):
    out = []
    for blk in page.get_text("dict")["blocks"]:
        for ln in blk.get("lines", []):
            s = "".join(sp["text"] for sp in ln["spans"]).strip()
            if s:
                x0, y0, x1, y1 = ln["bbox"]
                out.append((s, 0.5 * (x0 + x1), 0.5 * (y0 + y1), x0, y0, x1, y1))
    return out


def near(c, ref, tol=0.06):
    return all(abs(a - b) < tol for a, b in zip(c, ref))


calib = {}
G1 = []          # (name, got, want, tol)

# =============================================================================== ANP-194
SS_ARCH = ["PWR12", "LPSR", "MMNC", "NC-SMR", "DC-PWR", "LASR", "LM-BWR", "SM-BWR"]
SS_SID = {"PWR12": "ss_pwr12", "LPSR": "ss_lpsr", "MMNC": "ss_mmnc", "NC-SMR": "ss_ncsmr",
          "DC-PWR": "ss_dcpwr", "LASR": "ss_lasr", "LM-BWR": "ss_lmbwr", "SM-BWR": "ss_smbwr"}
SS_LONG = {"PWR12": "PWR12 (1,147 MWe EEDB reference PWR)", "LPSR": "Large passive-safety PWR (1,117 MWe, AP1000-like)",
           "MMNC": "Multi-module natural-circulation SMR plant (12 x 74 MWe)", "NC-SMR": "Natural-circulation SMR (160 MWe)",
           "DC-PWR": "Double-containment PWR (1,650 MWe, EPR-like)", "LASR": "Large active-safety PWR (1,400 MWe, APR1400-like)",
           "LM-BWR": "Large modular BWR (1,350 MWe, ABWR-like)", "SM-BWR": "Small modular BWR (300 MWe, BWRX-300-like)"}
# Fig 2.25 series colours (stroke RGB 0-1) in legend order.
SS_COL = [(0.267, 0.447, 0.769), (0.929, 0.490, 0.192), (0.647, 0.647, 0.647), (1.0, 0.753, 0.0),
          (0.357, 0.608, 0.835), (0.439, 0.678, 0.278), (0.149, 0.267, 0.471), (0.620, 0.282, 0.055)]
doc = fitz.open(SS_PDF)

# --- Fig 2.24 (total OCC bars): lower chart of page 58
pg = doc[SS_P224 - 1]
tl = text_lines(pg)
yt = [(float(s), yc) for s, xc, yc, x0, y0, x1, y1 in tl if s.isdigit() and x1 < 118 and 400 < yc < 590]
a24, b24, r24 = tick_fit(yt)
xlab = {s: xc for s, xc, yc, *_ in tl if s in SS_ARCH and 585 < yc < 600}
bars = {"FOAK": [], "10-OAK": []}
for dr in pg.get_drawings():
    f = dr.get("fill")
    if not f or dr["rect"].y0 < 400 or dr["rect"].width < 100:
        continue
    key = "FOAK" if near(f, (0.243, 0.580, 0.753)) else "10-OAK" if near(f, (0.737, 0.263, 0.545)) else None
    if key:
        for it in dr["items"]:
            if it[0] == "re":
                r = it[1]
                bars[key].append((0.5 * (r.x0 + r.x1), r.y0, r.y1))
assert len(bars["FOAK"]) == 8 and len(bars["10-OAK"]) == 8, {k: len(v) for k, v in bars.items()}
fig224 = {}
for key, lst in bars.items():
    for xc, y0, y1 in lst:
        arch = min(xlab, key=lambda s: abs(xlab[s] - xc))
        fig224[(arch, key)] = -a24 * (y1 - y0)            # height-based (bars sit on the axis)
calib["anp194_fig224"] = {"page": SS_P224, "ticks": yt, "usd_per_pt": a24, "intercept": b24, "tick_fit_max_resid_usd": r24,
                          "values_2018usd": {f"{k[0]} {k[1]}": round(v, 1) for k, v in fig224.items()}}

# --- Fig 2.25 (cumulative cost vs cumulative capacity): page 59
pg = doc[SS_P225 - 1]
tl = text_lines(pg)
xt = [(float(s), xc) for s, xc, yc, x0, y0, x1, y1 in tl if s.isdigit() and 560 < yc < 580]
yt = [(float(s), yc) for s, xc, yc, x0, y0, x1, y1 in tl if s.isdigit() and x1 < 110 and 320 < yc < 570]
# The axis tick MARKS are drawn as short lines (8 on the y axis, 10 on the x axis); their
# positions are the exact tick coordinates (label centres sit ~0.7 pt above the y ticks).
ytick_px = sorted({round(it[1].y, 2) for dr in pg.get_drawings() if len(dr["items"]) == 8 and dr["rect"].width < 4
                   for it in dr["items"] if it[0] == "l"}, reverse=True)
xtick_px = sorted({round(it[1].x, 2) for dr in pg.get_drawings() if len(dr["items"]) == 10 and dr["rect"].height < 4
                   for it in dr["items"] if it[0] == "l"})
assert len(ytick_px) == 8 and len(xtick_px) == 10, (ytick_px, xtick_px)
xt_marks = [(2000.0 * i, x) for i, x in enumerate(xtick_px)]
yt_marks = [(10.0 * i, y) for i, y in enumerate(ytick_px)]
ax25, bx25, rx25 = tick_fit(xt_marks)    # MWe = ax*x + bx   (exact tick marks)
ay25, by25, ry25 = tick_fit(yt_marks)    # $B  = ay*y + by
_lab_vs_tick = max(abs(yc - dict(yt_marks)[v]) for v, yc in yt if v in dict(yt_marks))
LEG = fitz.Rect(130, 339, 222, 449)      # legend box (markers there are ignored)
pts = {i: [] for i in range(8)}
for dr in pg.get_drawings():
    r = dr["rect"]
    if r.width > 6 or r.height > 6 or r.intersects(LEG) or r.y0 < 330 or r.y1 > 562:
        continue
    col = dr.get("fill") or dr.get("color")
    if not col:
        continue
    for i, ref in enumerate(SS_COL):
        if near(col, ref):
            pts[i].append((0.5 * (r.x0 + r.x1), 0.5 * (r.y0 + r.y1)))
            break
ss_rows = []
for i, arch in enumerate(SS_ARCH):
    P = sorted(set((round(x, 1), round(y, 1)) for x, y in pts[i]))
    # merge filled+outline duplicates (same centre within 0.3 pt)
    merged = []
    for x, y in P:
        if merged and abs(merged[-1][0] - x) < 0.3 and abs(merged[-1][1] - y) < 0.3:
            continue
        merged.append((x, y))
    assert len(merged) == 10, (arch, len(merged), merged)
    mw = np.array([ax25 * x + bx25 for x, _ in merged])
    cb = np.array([ay25 * y + by25 for _, y in merged])
    d_mw = np.diff(np.r_[0.0, mw])
    d_cb = np.diff(np.r_[0.0, cb])
    unit_mw = float(np.median(d_mw))
    unit_cost = d_cb * 1e6 / d_mw                      # $B / MWe -> $/kWe (increments: intercept-free)
    fig225_unit1 = float(unit_cost[0])
    unit_cost[0] = fig224[(arch, "FOAK")]              # unit 1 = the Fig 2.24 FOAK bar (text-verified)
    calib.setdefault("anp194_fig225_unit1_vs_fig224", {})[arch] = {
        "fig225_first_marker_usd_per_kw": round(fig225_unit1, 0), "fig224_foak_bar": round(fig224[(arch, "FOAK")], 0),
        "gap_busd": round((fig224[(arch, "FOAK")] - fig225_unit1) * unit_mw / 1e6, 3)}
    for k in range(10):
        ss_rows.append(dict(series_id=SS_SID[arch], architecture=arch, design=SS_LONG[arch], unit_index=k + 1,
                            n_units=k + 1, unit_mw=round(unit_mw, 0), cum_mw=round(float(mw[k]), 0),
                            cum_gw=round(float(mw[k]) / 1000.0, 4), cum_cost_busd=round(float(cb[k]), 3),
                            occ=round(float(unit_cost[k]), 0), read_err=(20.0 if k == 0 else round(30.0 + 5e3 / unit_mw, 0)),
                            dollar_year=2018, provenance="digitized-vector",
                            foak_fig224=round(fig224[(arch, "FOAK")], 0), tenoak_fig224=round(fig224[(arch, "10-OAK")], 0)))
ss = pd.DataFrame(ss_rows)
ss.to_csv(DATA / "mit_anp194_fig225_digitized.csv", index=False)
calib["anp194_fig225"] = {"page": SS_P225, "x_ticks": xt, "y_ticks": yt, "mwe_per_pt": ax25, "busd_per_pt": ay25,
                          "x_fit_max_resid_mwe": rx25, "y_fit_max_resid_busd": ry25, "x_ticks_px": xtick_px, "y_ticks_px": ytick_px,
                          "label_centre_vs_tick_max_pt": _lab_vs_tick,
                          "series_colours": dict(zip(SS_ARCH, SS_COL)),
                          "unit_mw_from_spacing": {a: float(ss[ss.architecture == a].unit_mw.iloc[0]) for a in SS_ARCH},
                          "read_err_note": ("vector-exact marker centres; +-$30/kWe plus 5,000/unit_MWe covers the two axis "
                                            "fits on the increments; unit 1 is the Fig 2.24 bar (+-$20)"),
                          "unit1_note": ("Fig 2.25's first marker lies a near-constant ~0.4 $B below FOAK x unit size for all "
                                         "eight architectures (see anp194_fig225_unit1_vs_fig224); unit 1 therefore comes from "
                                         "the Fig 2.24 bar, which reproduces the text (LPSR 4,290; SM-BWR 6,089). Units 2-10 "
                                         "are increments and independent of that offset; unit 10 reproduces the 10-OAK bars.")}
# G1b: unit 1 and unit 10 of Fig 2.25 vs the Fig 2.24 bars; text anchors of Table 2.14
for arch in SS_ARCH:
    s = ss[ss.architecture == arch].set_index("unit_index")["occ"]
    G1.append((f"ANP-194 {arch}: Fig 2.25 unit-10 increment = Fig 2.24 10-OAK bar", s[10], fig224[(arch, "10-OAK")],
               float(ss[ss.architecture == arch].read_err.max()) + 20.0))
s = ss.set_index(["architecture", "unit_index"])["occ"]
G1.append(("ANP-194 Table 2.14: LPSR FOAK 4,290 (text) = Fig 2.24 bar", s[("LPSR", 1)], 4290, 40))
G1.append(("ANP-194 Table 2.14: MMNC 12x74 10th-OAK 3,590 (text) = Fig 2.24 bar", fig224[("MMNC", "10-OAK")], 3590, 40))
G1.append(("ANP-194 Table 2.14: LM-BWR 10th-OAK 2,550 (text) = Fig 2.24 bar", fig224[("LM-BWR", "10-OAK")], 2550, 40))
G1.append(("ANP-194 Table 2.14: SM-BWR FOAK 6,089 (text) = Fig 2.24 bar", s[("SM-BWR", 1)], 6089, 40))
G1.append(("ANP-194 Table 2.14: LASR first-4-unit average 4,900 (text)", float(np.mean([s[("LASR", k)] for k in (1, 2, 3, 4)])), 4900, 80))
G1.append(("ANP-194 unit size from marker spacing: LPSR 1,117 MWe (text p.24)", float(ss[ss.architecture == "LPSR"].unit_mw.iloc[0]), 1117, 15))
G1.append(("ANP-194 unit size from marker spacing: DC-PWR 1,650 MWe (text)", float(ss[ss.architecture == "DC-PWR"].unit_mw.iloc[0]), 1650, 15))
G1.append(("ANP-194 unit size from marker spacing: MMNC 12x74 = 888 MWe", float(ss[ss.architecture == "MMNC"].unit_mw.iloc[0]), 888, 15))

# overlay e92
pix = pg.get_pixmap(dpi=200, clip=fitz.Rect(70, 320, 545, 600))
pix.save(FIG / "_e92_base.png")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
img = plt.imread(FIG / "_e92_base.png")
fig, ax = plt.subplots(figsize=(11, 6.5))
ax.imshow(img, extent=(70, 545, 600, 320))
for i, arch in enumerate(SS_ARCH):
    sub = ss[ss.architecture == arch]
    xs = (sub.cum_mw.values - bx25) / ax25
    ys = (sub.cum_cost_busd.values - by25) / ay25
    ax.scatter(xs, ys, s=26, facecolor="none", edgecolor="red", lw=0.9)
    ax.annotate(f"{arch}: u1 {sub.occ.iloc[0]:,.0f}  u10 {sub.occ.iloc[-1]:,.0f} $/kWe", (xs[-1], ys[-1]), xytext=(4, 0),
                textcoords="offset points", fontsize=6, color="red")
ax.set_axis_off()
fig.savefig(FIG / "e92_anp194_fig225_overlay.png", dpi=220, bbox_inches="tight")
plt.close(fig)
(FIG / "_e92_base.png").unlink()

# =============================================================================== IEA 2025
doc = fitz.open(IEA_PDF)
pg = doc[IEA_P24 - 1]
tl = text_lines(pg)
yt = [(float(s.replace(" ", "")), yc) for s, xc, yc, x0, y0, x1, y1 in tl if s.replace(" ", "").isdigit() and x1 < 117 and 110 < yc < 265]
ay, by, ry = tick_fit(yt)
IEA_COL = {"iea_steps": (0.28, 0.83, 1.0), "iea_aps": (0.24, 0.478, 0.83), "iea_nze": (0.40, 0.955, 0.577), "iea_large": (0.1, 0.678, 0.631)}
PANEL = {"US and EU": (120, 232), "China": (250, 369), "India": (387, 504)}
year_x = {}
for s, xc, yc, *_ in tl:
    if s in ("2030", "2040", "2050") and 260 < yc < 275:
        for reg, (x0, x1) in PANEL.items():
            if x0 <= xc <= x1:
                year_x[(reg, int(s))] = xc
iea_rows = []
for dr in pg.get_drawings():
    col = dr.get("color")
    r = dr["rect"]
    if not col or r.y1 > 240 or r.width < 50:
        continue
    sid = next((k for k, ref in IEA_COL.items() if near(col, ref, 0.12)), None)
    if sid is None:
        continue
    reg = next(rg for rg, (x0, x1) in PANEL.items() if x0 - 3 <= r.x0 and r.x1 <= x1 + 3)
    nodes = []
    for it in dr["items"]:
        if it[0] == "c":
            nodes += [it[1], it[4]]
        elif it[0] == "l":
            nodes += [it[1], it[2]]
    seen = {}
    for p in nodes:
        seen[round(p.x, 1)] = p.y
    for x, y in sorted(seen.items()):
        yr = min((2030, 2040, 2050), key=lambda Y: abs(year_x[(reg, Y)] - x))
        assert abs(year_x[(reg, yr)] - x) < 4, (sid, reg, x, yr)
        iea_rows.append(dict(series_id=sid, region=reg, year=yr, occ=round(ay * y + by, 0), figure="2.4",
                             dollar_year=2023, provenance="digitized-vector", read_err=round(ry + 25.0, 0)))
iea = pd.DataFrame(iea_rows).drop_duplicates(["series_id", "region", "year"]).sort_values(["region", "series_id", "year"])
calib["iea_fig24"] = {"page": IEA_P24, "ticks": yt, "usd_per_pt": ay, "tick_fit_max_resid_usd": ry, "colours": IEA_COL}

# --- Fig 2.11: left bars (2040 cost, APS vs High SMR Case) and right curves (global GW by year)
pg = doc[IEA_P211 - 1]
tl = text_lines(pg)
ytL = [(float(s.replace(" ", "")), yc) for s, xc, yc, x0, y0, x1, y1 in tl if s.replace(" ", "").isdigit() and x1 < 115 and 480 < yc < 650]
aL, bL, rL = tick_fit(ytL)
ytR = [(float(s), yc) for s, xc, yc, x0, y0, x1, y1 in tl if s.isdigit() and 280 < x1 < 300 and 480 < yc < 650]
aR, bR, rR = tick_fit(ytR)
xtR = [(float(s), xc) for s, xc, yc, x0, y0, x1, y1 in tl if s in ("2025", "2030", "2035", "2040", "2045", "2050") and 645 < yc < 660]
axR, bxR, rxR = tick_fit(xtR)
regL = {s: xc for s, xc, yc, *_ in tl if s in ("US and EU", "China", "India") and 645 < yc < 660}
high_rows = []
for dr in pg.get_drawings():
    f = dr.get("fill")
    r = dr["rect"]
    if not f or r.x1 > 280 or r.y1 < 640 or r.width < 100:
        continue
    key = "iea_aps" if near(f, (0.243, 0.478, 0.827)) else "iea_high_smr" if near(f, (0.286, 0.827, 1.0)) else None
    if key is None:
        continue
    for it in dr["items"]:
        if it[0] == "re":
            rr = it[1]
            reg = min(regL, key=lambda s: abs(regL[s] - 0.5 * (rr.x0 + rr.x1)))
            high_rows.append(dict(series_id=key, region=reg, year=2040, occ=round(-aL * (rr.y1 - rr.y0), 0), figure="2.11",
                                  dollar_year=2023, provenance="digitized-vector", read_err=round(rL + 25.0, 0)))
large_marks = []
for dr in pg.get_drawings():
    r = dr["rect"]
    if dr.get("color") == (0.0, 0.0, 0.0) and 40 < r.width < 60 and r.height < 0.5 and 500 < r.y0 < 640 and r.x0 > 115:
        reg = min(regL, key=lambda s: abs(regL[s] - 0.5 * (r.x0 + r.x1)))
        large_marks.append(dict(series_id="iea_large", region=reg, year=2040, occ=round(aL * r.y0 + bL, 0), figure="2.11",
                                dollar_year=2023, provenance="digitized-vector", read_err=round(rL + 25.0, 0)))
gw_curves = {}
for dr in pg.get_drawings():
    r = dr["rect"]
    if r.x0 < 300 or r.y0 < 480 or r.y1 > 650:
        continue
    col = dr.get("fill") or dr.get("color")
    key = ("iea_aps" if near(col, (0.243, 0.478, 0.827)) else "iea_high_smr" if near(col, (0.286, 0.827, 1.0)) else
           "iea_steps" if near(col, (0.408, 0.953, 0.58)) else "iea_nze" if near(col, (0.0, 0.678, 0.631)) else None)
    if key is None or key in gw_curves:
        continue
    top = {}
    for it in dr["items"]:
        if it[0] == "l":
            for p in (it[1], it[2]):
                x = round(p.x, 1)
                top[x] = min(top.get(x, 1e9), p.y)
    xs = np.array(sorted(top))
    ys = np.array([top[x] for x in xs])
    gw_curves[key] = (xs, ys)
iea_gw = []
for key, (xs, ys) in gw_curves.items():
    for yr in (2030, 2035, 2040, 2045, 2050):
        x = (yr - bxR) / axR
        y = float(np.interp(x, xs, ys))
        iea_gw.append(dict(series_id=key, year=yr, gw_global=round(aR * y + bR, 1)))
iea_gw = pd.DataFrame(iea_gw)
iea = pd.concat([iea, pd.DataFrame(high_rows + large_marks)], ignore_index=True)
iea = iea.merge(iea_gw, on=["series_id", "year"], how="left")
# High SMR Case costs before 2040 follow the APS (it is "based on the APS"); the GW path is its own.
iea = iea.sort_values(["region", "series_id", "year"]).reset_index(drop=True)
iea.to_csv(DATA / "iea_2025_digitized.csv", index=False)
calib["iea_fig211"] = {"page": IEA_P211, "left_ticks": ytL, "left_usd_per_pt": aL, "left_fit_resid": rL,
                       "right_gw_ticks": ytR, "right_gw_per_pt": aR, "right_fit_resid": rR, "year_ticks": xtR,
                       "gw_curves_read_at": [2030, 2035, 2040, 2045, 2050]}
def _iea(sid, reg, yr, figure):
    q = iea[(iea.series_id == sid) & (iea.region == reg) & (iea.year == yr) & (iea.figure == figure)]
    assert len(q) == 1, (sid, reg, yr, figure, len(q))
    return float(q.occ.iloc[0])
G1.append(("IEA Fig 2.4 US&EU 2030 FOAK ~10,000 (text: 'around USD 10 000 per kW')", _iea("iea_aps", "US and EU", 2030, "2.4"), 10000, 250))
G1.append(("IEA Fig 2.11 High SMR Case US&EU 2040 = 4,500 (text)", _iea("iea_high_smr", "US and EU", 2040, "2.11"), 4500, 100))
G1.append(("IEA Fig 2.11 High SMR Case China 2040 = 2,500 (text)", _iea("iea_high_smr", "China", 2040, "2.11"), 2500, 100))
G1.append(("IEA Fig 2.4 = Fig 2.11 for APS US&EU 2040 (two charts, same value)", _iea("iea_aps", "US and EU", 2040, "2.4"), _iea("iea_aps", "US and EU", 2040, "2.11"), 60))
G1.append(("IEA Fig 2.4 APS US&EU 2050 under 5,000 (text: 'parity ... in the 2040s, at under USD 5 000/kW')", _iea("iea_aps", "US and EU", 2050, "2.4"), (0, 5000), 0))
G1.append(("IEA Fig 2.11 High SMR Case 2040 is ~25% below APS 2040 (text)", _iea("iea_high_smr", "US and EU", 2040, "2.11") / _iea("iea_aps", "US and EU", 2040, "2.11"), (0.70, 0.80), 0))
gwi = iea_gw.set_index(["series_id", "year"])["gw_global"]
G1.append(("IEA Fig 2.11 STEPS 2050 = 40 GW (text)", float(gwi[("iea_steps", 2050)]), 40, 5))
G1.append(("IEA Fig 2.11 APS 2050 = 120 GW (text)", float(gwi[("iea_aps", 2050)]), 120, 6))
G1.append(("IEA Fig 2.11 High SMR Case 2050 ~190 GW (text)", float(gwi[("iea_high_smr", 2050)]), 190, 10))
G1.append(("IEA Fig 2.11 NZE 2050 almost 200 GW (text)", float(gwi[("iea_nze", 2050)]), (185, 200), 0))
# overlay e93
pix = doc[IEA_P24 - 1].get_pixmap(dpi=200, clip=fitz.Rect(75, 95, 520, 290))
pix.save(FIG / "_e93_base.png")
img = plt.imread(FIG / "_e93_base.png")
fig, ax = plt.subplots(figsize=(11, 5))
ax.imshow(img, extent=(75, 520, 290, 95))
for r in iea[iea.figure == "2.4"].itertuples():
    ax.scatter(year_x[(r.region, r.year)], (r.occ - by) / ay, s=22, facecolor="none", edgecolor="red", lw=0.9)
    if r.region == "US and EU":
        ax.annotate(f"{r.series_id[4:]} {r.occ:,.0f}", (year_x[(r.region, r.year)], (r.occ - by) / ay), xytext=(3, 0),
                    textcoords="offset points", fontsize=5.5, color="red")
ax.set_axis_off()
fig.savefig(FIG / "e93_iea_fig24_overlay.png", dpi=220, bbox_inches="tight")
plt.close(fig)
(FIG / "_e93_base.png").unlink()

# =============================================================================== Breakthrough Fig 2-6 (raster)
doc = fitz.open(BTI_PDF)
pg = doc[BTI_P26 - 1]
xref = pg.get_images(full=True)[0][0]
pm = fitz.Pixmap(doc, xref)
if pm.n >= 4:
    pm = fitz.Pixmap(fitz.csRGB, pm)
pm.save(FIG / "_e94_base.png")
im = np.array(Image.open(FIG / "_e94_base.png").convert("RGB")).astype(int)
H, W, _ = im.shape
# axis calibration from the tick-label text clusters (x: 0.1, 1, 10, 100 GW; y: 1.0 ... 0)
def clusters(mask, axis, gap):
    idx = np.where(mask.any(axis=axis))[0]
    out, start, prev = [], idx[0], idx[0]
    for c in idx[1:]:
        if c - prev > gap:
            out.append(0.5 * (start + prev)); start = c
        prev = c
    out.append(0.5 * (start + prev))
    return out
xc = clusters(im[266:296, 100:, :].sum(axis=2) < 300, 0, 6)
xc = [c + 100 for c in xc]
assert len(xc) == 5, xc                                     # 0.1, 1, 10, 100, 1k labels
ax_dec, bx_dec, rx_dec = tick_fit([(-1, xc[0]), (0, xc[1]), (1, xc[2]), (2, xc[3])])    # log10 GW = a*px + b ('1k' label is off-centre)
yc = clusters(im[:270, 30:75, :].sum(axis=2) < 300, 1, 4)
assert len(yc) == 11, yc
ay_r, by_r, ry_r = tick_fit([(1.0 - 0.1 * i, yc[i]) for i in range(11)])
BTI_TECH = {"SMR": (0, 57, 77), "ARTES": (0, 188, 162), "HTGR": (57, 158, 205)}
BTI_UNIT_GW = {"SMR": 0.150, "ARTES": 0.345, "HTGR": 0.080}
BTI_FOAK = {"SMR": (5108.0, 6974.0), "HTGR": (5518.0, 7500.0), "ARTES": (4000.0, 6220.0)}   # (lower, upper) 2020$, Table 1-2
BTI_LR = {"low": 0.05, "high": 0.12}
BTI_FLOOR = 1800.0
SHAPE_SCEN = {"circle": ("lower", "low"), "square": ("lower", "high"), "diamond": ("upper", "low"), "triangle": ("upper", "high")}
# Manual end-point reads (raw-image pixel coordinates of the rightmost marker of each curve), made
# 2026-09-08 from 5x zoom crops of the 813 x 434 px image; a marker-shape classifier was not
# reliable on 7-px markers in dense runs, so the reads are recorded here and drawn on e94 for
# inspection. x_err_px = +-4 px (0.025 decade) for isolated end points; +-10 px (0.06 decade)
# for the diamonds, whose runs interleave with the circles. The HTGR upper-cost/low-learning
# curve never leaves the demonstration projects (its markers overlap at ratio ~1 near 0.1-0.3 GW).
BTI_MANUAL = [  # tech, marker, x_px, y_px, x_err_px, note
    ("SMR",   "circle",   509.6,  86.4,  4, ""),
    ("SMR",   "square",   588.0, 173.0,  4, "flat at the floor from ~40 GW"),
    ("SMR",   "diamond",  434.0,  72.0, 10, "last diamond inside the circle run"),
    ("SMR",   "triangle", 620.0, 184.0,  4, ""),
    ("ARTES", "circle",   697.0, 108.6,  4, ""),
    ("ARTES", "square",   687.0, 149.0,  4, "flat at the floor from ~35 GW"),
    ("ARTES", "diamond",  674.0, 105.0, 10, "last diamond inside the circle run"),
    ("ARTES", "triangle", 687.0, 187.0,  4, ""),
    ("HTGR",  "circle",   627.0, 113.4,  4, ""),
    ("HTGR",  "square",   677.0, 179.0,  4, "flat at the floor from ~70 GW"),
    ("HTGR",  "diamond",  172.0,  16.0, 40, "demonstration projects only; no diamond run visible beyond ~0.3 GW"),
    ("HTGR",  "triangle", 664.0, 181.0,  4, "reads at the LOWER-cost floor ratio (0.33), not eq. B-2's 0.25 for the upper FOAK"),
]
bti_rows = []
for tech, shape, xpx, ypx, xerr, note in BTI_MANUAL:
    cost, lr = SHAPE_SCEN[shape]
    gw = 10 ** (ax_dec * xpx + bx_dec)
    gw_lo, gw_hi = 10 ** (ax_dec * (xpx - xerr) + bx_dec), 10 ** (ax_dec * (xpx + xerr) + bx_dec)
    ratio_read = ay_r * ypx + by_r
    b = -np.log2(1.0 - BTI_LR[lr])
    foak = BTI_FOAK[tech][0 if cost == "lower" else 1]
    ratio_eq = max(BTI_FLOOR / foak, (gw / BTI_UNIT_GW[tech]) ** (-b))
    bti_rows.append(dict(tech=tech, scenario=f"{cost} cost, {lr} learning", cost_case=cost, learning_case=lr,
                         lr=BTI_LR[lr], foak_2020usd=foak, floor_2020usd=BTI_FLOOR, unit_gw=BTI_UNIT_GW[tech],
                         gw_2050=round(gw, 1), gw_2050_lo=round(gw_lo, 1), gw_2050_hi=round(gw_hi, 1),
                         n_units_2050=round(gw / BTI_UNIT_GW[tech], 0),
                         ratio_read=round(ratio_read, 3), ratio_eq_b2=round(ratio_eq, 3),
                         occ_2050_read=round(foak * ratio_read, 0), occ_2050_eq_b2=round(foak * ratio_eq, 0),
                         marker=shape, x_px=xpx, y_px=ypx, x_err_px=xerr, x_err_decade=round(xerr * ax_dec, 3),
                         ratio_err=round(4 * abs(ay_r), 3), provenance="digitized-raster-manual", note=note))
bti = pd.DataFrame(bti_rows)
bti.to_csv(DATA / "bti_fig26_endpoints.csv", index=False)
calib["bti_fig26"] = {"page": BTI_P26, "image_size_px": [W, H], "x_label_centres_px": xc, "log10gw_per_px": ax_dec,
                      "log10gw_intercept": bx_dec, "x_fit_resid_decade": rx_dec, "y_label_centres_px": yc,
                      "ratio_per_px": ay_r, "ratio_intercept": by_r, "y_fit_resid": ry_r, "tech_rgb": BTI_TECH,
                      "read_method": "manual end-point reads from 5x zoom crops (see BTI_MANUAL in the script)",
                      "table_1_2_inputs": {"foak_2020usd_lower_upper": BTI_FOAK, "lr": BTI_LR, "floor": BTI_FLOOR, "unit_gw": BTI_UNIT_GW}}
# G1b for BTI: identification (read ratio vs eq. B-2 at the read capacity; the HTGR upper-cost
# cases are recorded discrepancies, not gates) and the report's own totals (Tables 2-1 and 2-3).
for r in bti.itertuples():
    if r.tech == "HTGR" and r.marker in ("triangle", "diamond"):
        continue
    G1.append((f"BTI Fig 2-6 {r.tech} {r.scenario}: end-point ratio read vs eq. B-2 at {r.gw_2050:,.0f} GW", r.ratio_read, r.ratio_eq_b2, 0.04))
tot = bti.groupby("scenario")["gw_2050"].sum()
G1.append(("BTI 2050 total, max scenario = 469 GW (Table 2-1; lower cost, high learning)", float(tot["lower cost, high learning"]), 469, 469 * 0.08))
G1.append(("BTI 2050 total, min scenario = 185 GW (Table 2-1; upper cost, low learning)", float(tot["upper cost, low learning"]), 185, 185 * 0.10))
G1.append(("BTI all four 2050 totals inside 185-469 GW (+-8%)", (float(tot.min()), float(tot.max())), (185 * 0.92, 469 * 1.08), 0))
n_units = bti.groupby("scenario")["n_units_2050"].sum()
G1.append(("BTI 2050 reactor count 560-3,415 (Table 2-3; +-8%)", (float(n_units.min()), float(n_units.max())), (560 * 0.92, 3415 * 1.08), 0))
calib["bti_fig26"]["scenario_totals_gw"] = {k: float(v) for k, v in tot.items()}
calib["bti_fig26"]["scenario_totals_units"] = {k: float(v) for k, v in n_units.items()}
# overlay e94: the read end points on the raster, with eq. B-2 curves drawn through the calibration
fig, ax = plt.subplots(figsize=(11, 6))
ax.imshow(im.astype(np.uint8))
for tech in BTI_TECH:
    for cost in ("lower", "upper"):
        for lr in ("low", "high"):
            b = -np.log2(1.0 - BTI_LR[lr])
            foak = BTI_FOAK[tech][0 if cost == "lower" else 1]
            gws = np.logspace(np.log10(BTI_UNIT_GW[tech]), 2.7, 80)
            ratio = np.maximum(BTI_FLOOR / foak, (gws / BTI_UNIT_GW[tech]) ** (-b))
            ax.plot((np.log10(gws) - bx_dec) / ax_dec, (ratio - by_r) / ay_r, color="red", lw=0.5, alpha=0.5)
for r in bti.itertuples():
    ax.scatter([r.x_px], [r.y_px], s=70, facecolor="none", edgecolor="red", lw=1.4)
    ax.plot([r.x_px - r.x_err_px, r.x_px + r.x_err_px], [r.y_px] * 2, color="red", lw=1.0)
    ax.annotate(f"{r.tech} {r.cost_case[0].upper()}C/{r.learning_case[0].upper()}L {r.gw_2050:,.0f} GW", (r.x_px, r.y_px),
                xytext=(5, -9), textcoords="offset points", fontsize=6, color="red")
ax.set_axis_off()
fig.savefig(FIG / "e94_bti_fig26_overlay.png", dpi=200, bbox_inches="tight")
plt.close(fig)
(FIG / "_e94_base.png").unlink()

# =============================================================================== report + gate
pd.set_option("display.width", 200)
print("=== ANP-194 Fig 2.25 -> per-unit OCC (2018 $/kWe), with Fig 2.24 bars ===")
print(ss.pivot(index="unit_index", columns="architecture", values="occ").to_string(float_format=lambda v: f"{v:,.0f}"))
print(pd.DataFrame({k: v for k, v in calib["anp194_fig224"]["values_2018usd"].items()}, index=[0]).T.to_string())
print("\n=== IEA 2025 (2023 USD/kW; gw_global from Fig 2.11) ===")
print(iea.to_string(index=False))
print("\n=== BTI Fig 2-6 end points ===")
print(bti[["tech", "scenario", "gw_2050", "gw_2050_lo", "gw_2050_hi", "n_units_2050", "ratio_read", "ratio_eq_b2", "occ_2050_read", "occ_2050_eq_b2", "marker"]].to_string(index=False))
print(bti.groupby("scenario")[["gw_2050", "n_units_2050"]].sum())
print("\n=== Gate G1b ===")
allok = True
for name, got, want, tol in G1:
    if isinstance(want, tuple):
        if isinstance(got, tuple):
            ok = want[0] <= got[0] and got[1] <= want[1]
            print(f"  {'PASS' if ok else 'FAIL'}  {name}: [{got[0]:,.1f}, {got[1]:,.1f}] inside [{want[0]:,.1f}, {want[1]:,.1f}]")
        else:
            ok = want[0] - tol <= got <= want[1] + tol
            print(f"  {'PASS' if ok else 'FAIL'}  {name}: {got:,.3f} vs [{want[0]:,}-{want[1]:,}] +-{tol:g}")
    else:
        ok = abs(got - want) <= tol
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: {got:,.3f} vs {want:,} +-{tol:g}")
    allok &= bool(ok)
calib["gate_G1b"] = {"all_pass": bool(allok),
                     "checks": [{"name": n, "got": (list(g) if isinstance(g, tuple) else float(g)),
                                 "want": (list(w) if isinstance(w, tuple) else w), "tol": float(t)} for n, g, w, t in G1]}
calib["sources"] = {"anp194_pdf": {"file": SS_PDF.name, "pages": [SS_P224, SS_P225], "sha256": sha256(SS_PDF)},
                    "iea_pdf": {"file": IEA_PDF.name, "pages": [IEA_P24, IEA_P211], "sha256": sha256(IEA_PDF)},
                    "bti_pdf": {"file": BTI_PDF.name, "page": BTI_P26, "sha256": sha256(BTI_PDF)}}
(DATA / "digitize_calib_b.json").write_text(json.dumps(calib, indent=2, default=float), encoding="utf-8")
print(f"\nG1b {'PASS' if allok else 'FAIL'} -> data/digitize_calib_b.json, data/{{mit_anp194_fig225,iea_2025}}_digitized.csv, "
      f"data/bti_fig26_endpoints.csv, figures/e92-e94")
