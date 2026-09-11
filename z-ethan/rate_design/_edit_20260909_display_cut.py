"""Paper display twins of the Fig 6 exhibits, DISPLAY_CUT below the mapped requirement
(2026-09-09, Ethan's figure revisions; plan "zesty-purring-breeze").

Ruling (Ethan, AskUserQuestion 09-09): every value shown in the paper's Fig 6a/6b/6c is
lowered by THREE statutory rate points "for now", to reflect the cliff finding that the
delivery-minimal credit lies below the mapped requirement (r03: delivery at headline-1 in
6/6 ladders, failure at headline-5 in 6/6). The registered objects keep their one-point
cushion TOL_SHORT (gates, verdicts, u50/u51/u52 unchanged, byte-identical); the paper reads
TWIN exports `u50/u51/u52_*_cut` computed from max(requirement - DISPLAY_CUT, 0) and three
new paper cells:
  w38  the rate fans in percent, y clipped at 100% with a red edge where the p95 band
       exceeds it (no censor triangles; no reference path / minimal-rate band -- they
       moved to SF24 with the cliff)            -> Fig 6a
  w39  the credit-feasibility mask alone         -> Fig 6b
  w43  the demonstration funding requirement alone -> Fig 6c   (w40-w42 are taken)

This script patches the LIVE builder `_build_notebook_v2.py`; both notebooks are then
rebuilt (plain and RD_ANCHORS=5a) and re-executed. Idempotent.
"""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
BP = HERE / "_build_notebook_v2.py"
text = BP.read_text(encoding="utf-8")
if "DISPLAY_CUT = 0.03" in text:
    print("builder already patched")
    raise SystemExit(0)


def sub_once(old, new):
    global text
    assert text.count(old) == 1, (text.count(old), old[:120])
    text = text.replace(old, new)


# ---- 1. the constant -----------------------------------------------------------------------
sub_once('TOL_SHORT = 0.01          # delivery cushion, statutory rate points (r03-certified)\n',
         'TOL_SHORT = 0.01          # delivery cushion, statutory rate points (r03-certified)\n'
         'DISPLAY_CUT = 0.03        # paper display allowance below the mapped rate (Ethan 09-09,\n'
         '                          # "for now"; the r03 bracket is (head-5, head-1]; twins only)\n')

# ---- 2. u50 -> requirement_fans(cut) + the _cut twin ------------------------------------------
U50_OLD_HEAD = '''code("""fan_rows = []
BAND = {"base": 1.0, "lo": 0.8, "hi": 1.2}
QS = [5, 25, 50, 75, 95]
for ab in SCHEDULES:
    occ_ref = OCCW[ab][ANCH[ab]["p50"]]
    for band, mult in BAND.items():
        iwm = IW[ab] * mult
        needm = np.maximum(iwm - TOL_SHORT, 0.0) * OCCW[ab]
        for qty, arr, ref in [("rate", iwm, IREF[ab] * mult),
                              ("need_kw", needm, REFC[ab] * mult)]:
            P = np.percentile(arr, QS, axis=0)
            for j, t in enumerate(BUILD_TS[ab]):
                above = round(float(1 - TOPKNOT_PCT[ab][j]) * 100, 1)
                below = round(float(BOTKNOT_PCT[ab][j]) * 100, 1)
                fan_rows.append(dict(schedule=ab, band=band, quantity=qty, year=t,
                                     **{f"p{q:02d}": round(float(P[i, j]), 4)
                                        for i, q in enumerate(QS)},
                                     ref=round(float(ref[j]), 4),
                                     censored=(ab, t) in CENSORED,
                                     above_top_pct=above, below_bot_pct=below,
                                     p95_clamp_pinned=above > 5.0))
u50 = pd.DataFrame(fan_rows)
u50.to_csv(EXPORTS / "u50_requirement_fans.csv", index=False)
'''
U50_NEW_HEAD = '''code("""BAND = {"base": 1.0, "lo": 0.8, "hi": 1.2}
QS = [5, 25, 50, 75, 95]

def requirement_fans(cut=None):
    \\"\\"\\"u50 rows. cut=None: the registered fans (rate = the mapped requirement; need =
    requirement - TOL_SHORT). cut=x: the paper display twin (Ethan 09-09) -- rate and
    need both x points below the mapped requirement, never below zero, reference
    paths likewise.\\"\\"\\"
    fan_rows = []
    for ab in SCHEDULES:
        occ_ref = OCCW[ab][ANCH[ab]["p50"]]
        for band, mult in BAND.items():
            iwm = IW[ab] * mult
            if cut is None:
                needm = np.maximum(iwm - TOL_SHORT, 0.0) * OCCW[ab]
                pairs = [("rate", iwm, IREF[ab] * mult), ("need_kw", needm, REFC[ab] * mult)]
            else:
                ratec = np.maximum(iwm - cut, 0.0)
                refc = np.maximum(IREF[ab] * mult - cut, 0.0)
                pairs = [("rate", ratec, refc), ("need_kw", ratec * OCCW[ab], refc * occ_ref)]
            for qty, arr, ref in pairs:
                P = np.percentile(arr, QS, axis=0)
                for j, t in enumerate(BUILD_TS[ab]):
                    above = round(float(1 - TOPKNOT_PCT[ab][j]) * 100, 1)
                    below = round(float(BOTKNOT_PCT[ab][j]) * 100, 1)
                    fan_rows.append(dict(schedule=ab, band=band, quantity=qty, year=t,
                                         **{f"p{q:02d}": round(float(P[i, j]), 4)
                                            for i, q in enumerate(QS)},
                                         ref=round(float(ref[j]), 4),
                                         censored=(ab, t) in CENSORED,
                                         above_top_pct=above, below_bot_pct=below,
                                         p95_clamp_pinned=above > 5.0))
    return pd.DataFrame(fan_rows)

u50 = requirement_fans()
u50.to_csv(EXPORTS / "u50_requirement_fans.csv", index=False)
u50c = requirement_fans(DISPLAY_CUT)     # the paper display twin (Fig 6a since 2026-09-09)
u50c.to_csv(EXPORTS / "u50_requirement_fans_cut.csv", index=False)
'''
sub_once(U50_OLD_HEAD, U50_NEW_HEAD)

# ---- 3. u51/u52 -> feasibility_tables(cut) + the _cut twins ----------------------------------
m = re.search(r'code\("""mask_rows, world_rows, gap_rows = \[\], \[\], \[\]\n(.*?)'
              r'u52\.to_csv\(EXPORTS / "u52_demonstration_gap\.csv", index=False\)\n',
              text, flags=re.S)
assert m, "u51/u52 block not found"
block = m.group(0)
body = m.group(1)
assert body.count("TOL_SHORT") == 2, body.count("TOL_SHORT")
tail_old = ('u51 = pd.DataFrame(mask_rows)\n'
            'u51w = pd.DataFrame(world_rows)\n'
            'u51["kind"] = "per_year"\n'
            'u51w["kind"] = "per_world"\n'
            'pd.concat([u51, u51w], ignore_index=True).to_csv(\n'
            '    EXPORTS / "u51_feasibility_mask.csv", index=False)\n'
            'u52 = pd.DataFrame(gap_rows)\n')
assert body.endswith(tail_old), body[-400:]
loop = body[: -len(tail_old)]
loop_c = "\n".join(("    " + l if l.strip() else l) for l in loop.rstrip("\n").split("\n"))
loop_c = loop_c.replace("TOL_SHORT", "cut")
new_block = (
    'code("""def feasibility_tables(cut):\n'
    '    \\"\\"\\"(u51 per-year mask, u51w per-world mask, u52 demonstration gap) for a cushion\n'
    '    `cut` below the mapped requirement: TOL_SHORT = the registered tables; DISPLAY_CUT =\n'
    '    the paper display twins (Ethan 09-09).\\"\\"\\"\n'
    '    mask_rows, world_rows, gap_rows = [], [], []\n'
    + loop_c + '\n'
    '    u51 = pd.DataFrame(mask_rows)\n'
    '    u51w = pd.DataFrame(world_rows)\n'
    '    u51["kind"] = "per_year"\n'
    '    u51w["kind"] = "per_world"\n'
    '    return u51, u51w, pd.DataFrame(gap_rows)\n'
    '\n'
    'u51, u51w, u52 = feasibility_tables(TOL_SHORT)\n'
    'pd.concat([u51, u51w], ignore_index=True).to_csv(\n'
    '    EXPORTS / "u51_feasibility_mask.csv", index=False)\n'
    'u52.to_csv(EXPORTS / "u52_demonstration_gap.csv", index=False)\n'
    'u51c, u51wc, u52c = feasibility_tables(DISPLAY_CUT)   # paper display twins (Fig 6b/6c since 09-09)\n'
    'pd.concat([u51c, u51wc], ignore_index=True).to_csv(\n'
    '    EXPORTS / "u51_feasibility_mask_cut.csv", index=False)\n'
    'u52c.to_csv(EXPORTS / "u52_demonstration_gap_cut.csv", index=False)\n'
)
assert text.count(block) == 1
text = text.replace(block, new_block)

# ---- 4. the paper cells w38 / w39 / w43, appended to the S7 cell after w35 --------------------
W35_END = 'ps.savefig(fig, FIGURES / "w35_mask_gap_paper.png")\nplt.show()\n'
NEW_CELLS = W35_END + r'''
# w38: the rate fans, paper display twin (Fig 6a since 2026-09-09, Ethan's revisions):
# every value DISPLAY_CUT below the mapped requirement (u50c); rates in percent; the y axis
# clipped at 100% with a red edge along the clipped span (no censor triangles: the edge
# carries that); no reference path / minimal-rate band (they went to SF24 with the cliff).
from matplotlib.ticker import PercentFormatter

def _clip_spans(ts, top, lim=1.0):
    \"\"\"x spans where `top` exceeds `lim`; crossings linearly interpolated.\"\"\"
    ts, top = np.asarray(ts, float), np.asarray(top, float)
    spans, x0 = [], None
    for j in range(len(ts)):
        if top[j] > lim and x0 is None:
            x0 = ts[j] if j == 0 else ts[j-1] + (lim - top[j-1]) / (top[j] - top[j-1]) * (ts[j] - ts[j-1])
        elif top[j] <= lim and x0 is not None:
            spans.append((x0, ts[j-1] + (lim - top[j-1]) / (top[j] - top[j-1]) * (ts[j] - ts[j-1])))
            x0 = None
    if x0 is not None:
        spans.append((x0, ts[-1]))
    return spans

fig, axes = plt.subplots(2, 3, figsize=(ps.W3, 6.2), sharey=True)
for ax, ab in zip(axes.flat, SCHEDULES):
    sub = u50c[(u50c["schedule"] == ab) & (u50c["band"] == "base")
               & (u50c["quantity"] == "rate")]
    ts = sub["year"].to_numpy()
    ax.fill_between(ts, sub["p05"], sub["p95"], color=ps.SCHED_C[ab], alpha=0.12, lw=0)
    ax.fill_between(ts, sub["p25"], sub["p75"], color=ps.SCHED_C[ab], alpha=0.25, lw=0)
    ax.plot(ts, sub["p50"], color=ps.SCHED_C[ab], lw=1.5)
    for bnd in ["lo", "hi"]:
        sb = u50c[(u50c["schedule"] == ab) & (u50c["band"] == bnd)
                  & (u50c["quantity"] == "rate")]
        ax.plot(sb["year"], sb["p50"], color=ps.SCHED_C[ab], lw=0.6, ls=":", alpha=0.7)
    for cap, ls in zip(CAPS, [":", "-."]):
        ax.axhline(cap, color=ps.ACCENT["red"], lw=0.9, ls=ls)
    ax.set_ylim(0.0, 1.0)
    for x0, x1 in _clip_spans(ts, sub["p95"]):
        ax.plot([x0, x1], [1.0, 1.0], color=ps.ACCENT["red"], lw=2.4,
                solid_capstyle="butt", clip_on=False, zorder=6)
    ax.set_title(ps.SCHED_SHORT[ab])
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=0))
for ax in axes[1]:
    ax.set_xlabel("build year")
for ax in axes[:, 0]:
    ax.set_ylabel("required tax credit rate\\n(% of plant cost)")
handles = [
    Line2D([], [], color=GREY, lw=1.5, label="median required rate"),
    Patch(facecolor=GREY, alpha=0.30, label="interquartile band"),
    Patch(facecolor=GREY, alpha=0.12, label="p5\u2013p95 band"),
    Line2D([], [], color=GREY, lw=0.6, ls=":",
           label="median with the requirement \u00b120%"),
    Line2D([], [], color=ps.ACCENT["red"], lw=0.9, ls=":",
           label="current statutory maximum 50% (48E with bonuses)"),
    Line2D([], [], color=ps.ACCENT["red"], lw=0.9, ls="-.",
           label="hypothetical 60% cap"),
]
fig.tight_layout()
fig.legend(handles=handles, ncol=3, fontsize=6.5, frameon=False,
           loc="upper center", bbox_to_anchor=(0.5, 0.0))
ps.savefig(fig, FIGURES / "w38_rate_fans_pct.png")
plt.show()

# w39: the credit-feasibility mask alone, display twin (Fig 6b since 2026-09-09)
fig, ax = plt.subplots(figsize=(ps.W2 * 0.62, 3.6))
for ab in SCHEDULES:
    sub = u51c[(u51c["schedule"] == ab) & (u51c["band"] == "base") & (u51c["cap"] == 0.60)]
    ax.plot(sub["year"], sub["share_above"] * 100, color=ps.SCHED_C[ab],
            lw=1.4, label=ps.SCHED_SHORT[ab])
    sub5 = u51c[(u51c["schedule"] == ab) & (u51c["band"] == "base") & (u51c["cap"] == 0.50)]
    ax.plot(sub5["year"], sub5["share_above"] * 100, color=ps.SCHED_C[ab],
            lw=0.8, ls=":")
ax.axvline(W_PRIMARY + 0.5, color="k", lw=0.8, ls="--")
ax.set_xlabel("build year")
ax.set_ylabel("share of worlds above the cap (%)")
ax.xaxis.set_major_locator(MaxNLocator(integer=True))
leg_sched = ax.legend(fontsize=6, frameon=False, ncol=2, loc="upper right",
                      title="schedule", title_fontsize=6)
ax.add_artist(leg_sched)
ax.legend(handles=[
    Line2D([], [], color="0.35", lw=1.4, label="60% cap"),
    Line2D([], [], color="0.35", lw=0.8, ls=":", label="50% cap"),
    Line2D([], [], color="k", lw=0.8, ls="--",
           label="end of demonstration window (2035)")],
    fontsize=6, frameon=False, loc="lower left")
fig.tight_layout()
ps.savefig(fig, FIGURES / "w39_mask_paper.png")
plt.show()

# w43: the demonstration funding requirement alone, display twin (Fig 6c since 2026-09-09)
fig, ax = plt.subplots(figsize=(ps.W2 * 0.62, 3.6))
GAP_SCHED = [ab for ab in SCHEDULES if ab != "eia"]
xpos = np.arange(len(GAP_SCHED))
for k_, (cap, off, al) in enumerate([(0.50, -0.17, 0.55), (0.60, 0.17, 1.0)]):
    sub = u52c[(u52c["band"] == "base") & (u52c["window"] == "w2035")
               & (u52c["cap"] == cap)].set_index("schedule").reindex(GAP_SCHED)
    ax.bar(xpos + off, sub["gap_p95_B"], width=0.3, alpha=al * 0.35,
           color=[ps.SCHED_C[ab] for ab in GAP_SCHED])
    ax.bar(xpos + off, sub["gap_p50_B"], width=0.3, alpha=al,
           color=[ps.SCHED_C[ab] for ab in GAP_SCHED])
ax.set_xticks(xpos, [ps.SCHED_SHORT[ab] for ab in GAP_SCHED])
ax.set_ylabel("demonstration funding requirement (2024 $B)")
ax.legend(handles=[
    Patch(facecolor="0.35", alpha=0.55, label="left bar: 50% cap"),
    Patch(facecolor="0.35", alpha=1.0, label="right bar: 60% cap"),
    Patch(facecolor="0.35", alpha=0.35,
          label="faint extension: expensive world (P95; lower bound where censored)"),
    Patch(facecolor="0.35", alpha=1.0, label="solid: median world")],
    fontsize=6, frameon=False, loc="upper left")
ax.text(0.02, 0.55, "EIA AEO high: no builds\\nbefore 2036", transform=ax.transAxes,
        fontsize=6, color=ps.MUTED, va="top")
fig.tight_layout()
ps.savefig(fig, FIGURES / "w43_gap_paper.png")
plt.show()
'''
sub_once(W35_END, NEW_CELLS)

# ---- 5. the 5a suffix-rewrite hit count (3 new exports + 3 new figures) ----------------------
sub_once("N_HITS_V2 = 28\n", "N_HITS_V2 = 34   # 28 + the 09-09 display twins (3 exports, 3 figures)\n")

# the S7 section note
sub_once('paper figure does not carry). The originals stay frozen as the audit\n'
         'record; the outline\'s `[FIGS]` ledger row provides for new w34+ numbers.""")',
         'paper figure does not carry). The originals stay frozen as the audit\n'
         'record; the outline\'s `[FIGS]` ledger row provides for new w34+ numbers.\n'
         '\n'
         '**2026-09-09 (Ethan\'s figure revisions):** w38/w39/w43 are the paper\'s\n'
         'Fig 6a/6b/6c — the same exhibits on the `_cut` display twins (every value\n'
         'DISPLAY_CUT = 3 rate points below the mapped requirement, the cliff-finding\n'
         'allowance; the registered one-point objects are untouched), rates in\n'
         'percent, the fans clipped at 100% with a red edge, the cliff itself demoted\n'
         'to SF24.""")')

BP.write_text(text, encoding="utf-8")
print("patched _build_notebook_v2.py: DISPLAY_CUT, requirement_fans(), feasibility_tables(), "
      "w38/w39/w43, N_HITS_V2=34")
