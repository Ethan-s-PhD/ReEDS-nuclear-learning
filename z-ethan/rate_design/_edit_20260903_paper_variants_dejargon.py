"""w34 / w35 / w37 (paper Figs 6a, 6b, 5b) — plain-word labels (2026-09-03).

Ethan's coauthor review: no internal codes or registration vocabulary in the
saved pixels. Schedule codes -> plotstyle.SCHED_SHORT; "statutory rate (on own
cost)" -> "tax credit rate (share of plant cost)"; "certified headline",
"run-certified bracket", "registered outer cap", "censored cell", "clamp",
"statutory points", "window empty" all restated in plain words. Label strings
only; no numeric change. Builder-only edit: the notebook is rebuilt and
re-executed in full (about 3 minutes; it reads exports, not the h5 drive).
"""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent

SUBS = [
    # ---- w34: the rate fans ------------------------------------------------------
    ("    ax.set_title(ab)\n    ax.xaxis.set_major_locator(MaxNLocator(integer=True))\nfor ax in axes[1]:",
     "    ax.set_title(ps.SCHED_SHORT[ab])\n    ax.xaxis.set_major_locator(MaxNLocator(integer=True))\n"
     "for ax in axes[1]:"),
    ('for ax in axes[:, 0]:\n    ax.set_ylabel("required statutory rate\\\\n(on own cost)")\nGREY = "0.35"',
     'for ax in axes[:, 0]:\n    ax.set_ylabel("required tax credit rate\\\\n(share of plant cost)")\nGREY = "0.35"'),
    ('label="\\u00b120% requirement-band medians"),',
     'label="median with the requirement \\u00b120%"),'),
    ('label="reference credit path (certified headline)"),',
     'label="credit path tested in ReEDS"),'),
    ('label="run-certified minimal-rate bracket (aj/mck/eo)"),',
     'label="ReEDS-tested band for the lowest delivering rate\\\\n(Abou-Jaoude, McKinsey, 2025 EO)"),'),
    ('label="statutory cap 0.50 (48E stacked maximum)"),',
     'label="current statutory maximum 0.50 (48E with bonuses)"),'),
    ('label="registered outer cap 0.60"),', 'label="hypothetical 0.60 cap"),'),
    ('label="censored cell (rate is a lower bound)"),', 'label="rate shown is a lower bound"),'),
    # ---- w35: the mask and the gap ---------------------------------------------
    ('           label="demonstration-window edge (2035)")],',
     '           label="end of demonstration window (2035)")],'),
    ('          label="faint extension: p95 (lower bound where the clamp binds)"),',
     '          label="faint extension: expensive world (P95; lower bound where censored)"),'),
    ('    Patch(facecolor="0.35", alpha=1.0, label="solid: median")],',
     '    Patch(facecolor="0.35", alpha=1.0, label="solid: median world")],'),
    ('axes[1].text(0.02, 0.55, "eia n/a:\\\\nwindow empty", transform=axes[1].transAxes,',
     'axes[1].text(0.02, 0.55, "EIA AEO high: no builds\\\\nbefore 2036", transform=axes[1].transAxes,'),
    # ---- w37: the calibration limit in rate points --------------------------------
    ("    ax.set_title(ab)\n    for a_ in (ax, axl):",
     "    ax.set_title(ps.SCHED_SHORT[ab])\n    for a_ in (ax, axl):"),
    ('    ax.set_ylabel("uncertainty in the required credit rate\\\\n(90% interval width, statutory points)")',
     '    ax.set_ylabel("uncertainty in the required credit rate\\\\n(90% interval width, percentage points)")'),
    ('    ax.set_ylabel("uncertainty in the learning rate\\\\n(90% interval width, points)")',
     '    ax.set_ylabel("uncertainty in the learning rate\\\\n(90% interval width, percentage points)")'),
    ('           label="light noise (σ 0.15, τ 0.05)"),\n'
     '    Line2D([], [], color="0.3", lw=1.8, marker="o", ms=2.5, label="mid noise (0.30, 0.10)"),\n'
     '    Line2D([], [], color="0.3", lw=1.0, alpha=0.55, label="heavy noise (0.50, 0.20)"),',
     '           label="light observation noise (σ 0.15, τ 0.05)"),\n'
     '    Line2D([], [], color="0.3", lw=1.8, marker="o", ms=2.5, label="medium noise (σ 0.30, τ 0.10)"),\n'
     '    Line2D([], [], color="0.3", lw=1.0, alpha=0.55, label="heavy noise (σ 0.50, τ 0.20)"),'),
    ('           label="design target: 5 statutory points (top row only)"),',
     '           label="target precision: 5 percentage points (top row)"),'),
]

# Two w35 lines are shared verbatim with the frozen w32 audit artifact, so they are
# replaced only inside the w35 paper-variant block.
SUBS_W35 = [
    ("                 lw=1.4, label=ab)", "                 lw=1.4, label=ps.SCHED_SHORT[ab])"),
    ("axes[1].set_xticks(xpos, GAP_SCHED)",
     "axes[1].set_xticks(xpos, [ps.SCHED_SHORT[ab] for ab in GAP_SCHED])"),
]
W35_START = "# w35: the mask and the gap, paper variant"
W35_END = "# w36: the CI curves, paper variant"

bp = HERE / "_build_notebook_v2.py"
text = bp.read_text(encoding="utf-8")
for old, new in SUBS:
    assert text.count(old) == 1, (old, text.count(old))
    text = text.replace(old, new)
assert text.count(W35_START) == 1 and text.count(W35_END) == 1
head, rest = text.split(W35_START)
block, tail = rest.split(W35_END)
for old, new in SUBS_W35:
    assert block.count(old) == 1, (old, block.count(old))
    block = block.replace(old, new)
text = head + W35_START + block + W35_END + tail
bp.write_text(text, encoding="utf-8")
print(f"patched _build_notebook_v2.py ({len(SUBS) + len(SUBS_W35)} label edits: w34, w35, w37)")
