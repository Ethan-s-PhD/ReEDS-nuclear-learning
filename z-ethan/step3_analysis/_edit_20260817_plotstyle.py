"""Bring step3_analysis.ipynb onto the z-ethan plot-formatting standard (2026-08-17).

Edit method per the established convention (id-targeted, assert-guarded string
replacements on the raw json; `_build_notebook.py` is STALE-by-policy and must
never be recreated or run). Idempotent: re-running exits 0 without changes.

What this applies (normative standard: z-ethan/plotstyle.py docstring):
A. cell 3785f291 (house-style cell): the local token tuple, rcParams block,
   viridis SCHED_C ramp, PCT_STYLE dict, and dpi-150 savefig are replaced by
   `import plotstyle as ps; ps.apply()` plus central-palette aliases and a
   savefig shim that delegates to ps.savefig (dpi 150 -> 300 is intended).
   The script asserts the notebook's SCHEDULES literal matches ps.SCHED_ORDER
   and that the old viridis ramp / PCT_STYLE values equal the central ones.
B. Nature title policy on the 16 saved figures (f01..f15 + t13 figure):
   suptitles and descriptive axes titles removed; categorical per-axes titles
   (SCHED_LABEL grids, family labels on f01, percentile labels on f07) kept;
   removed descriptive text preserved as one italic *Figure note:* line
   appended to the section's existing markdown cell; title text that encoded a
   legend (dotted floor / open circles on f03, dashed large100 on f07 and f10,
   band meaning on f15, cap/floor annotation on f02) moved into legends in the
   same cell; heterogeneous multi-panel figures lettered (f10 via
   ps.letter_panels; f12 panel-group letters a/b via ps.panel_letter).
C. Unit-string normalization in figure labels. Spaced variants found by grep:
   "(2024$ / kW-yr)" -> "(2024$/kW-yr)"   [cells 50efbfee, 6d2bd87e, b8178deb, t15cd001]
   "(2024 $B / yr)"  -> "(2024$B/yr)"     [cells 44ef5584, 3fed34f2]
   "2024 $B / yr" bare ylabel -> "annual cost difference (2024$B/yr)" [afbb2ec2]
   "(2024 $B/yr)"    -> "(2024$B/yr)"     [cell bca1c170]
   "(2024 $B)"       -> "(2024$B)"        [cells bca1c170, dcecba76]
   "(2024 $ / kW)"   -> "(2024$/kW)"      [cell 203eb154]
   Prose/print/comment mentions ("2024 $B:" print in dcecba76, the R_t comment
   in bca1c170, "2024 $B (B_t statutory)" in 4d0b4dcc) are not figure labels
   and stay unchanged.
D. Idempotency guard: "import plotstyle" already in cell 3785f291 -> exit 0.
"""
import json
import sys
from pathlib import Path

HERE_ = Path(__file__).resolve().parent
NB = HERE_ / "step3_analysis.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
CELLS = {c["id"]: c for c in nb["cells"]}

# ---- D. idempotency guard ----------------------------------------------------------
if "import plotstyle" in "".join(CELLS["3785f291"]["source"]):
    print("plotstyle edits already applied; nothing to do")
    raise SystemExit(0)

# ---- sanity: the central palette really equals what the notebook computed ----------
sys.path.insert(0, str(HERE_.parent))
import plotstyle as ps  # noqa: E402

assert ps.SCHED_ORDER == ["eia", "aj", "iaea", "mck", "cop28", "eo"]
assert 'SCHEDULES = ["eia", "aj", "iaea", "mck", "cop28", "eo"]' in \
    "".join(CELLS["e9a82fe7"]["source"]), "SCHEDULES literal moved; re-check"
assert ps.PCT_STYLE == {"p05": dict(lw=1.2, alpha=0.55, ls="-"),
                        "p50": dict(lw=2.2, alpha=1.00, ls="-"),
                        "p95": dict(lw=1.6, alpha=0.85, ls="--")}, ps.PCT_STYLE
try:
    import numpy as _np
    from matplotlib import cm as _cm, colors as _colors
    _hexes = [_colors.to_hex(c) for c in _cm.viridis(_np.linspace(0.02, 0.72, 6))]
    assert _hexes == [ps.SCHED_C[s] for s in ps.SCHED_ORDER], _hexes
except ImportError:
    print("matplotlib unavailable; viridis-hex identity not re-verified here")

n = 0


def rep(cid, old, new, count=1):
    global n
    s = "".join(CELLS[cid]["source"])
    assert s.count(old) == count, \
        f"cell {cid}: pattern count {s.count(old)} != {count}:\n{old[:160]}"
    CELLS[cid]["source"] = s.replace(old, new).splitlines(keepends=True)
    n += 1


def note(cid, tail, text):
    """Append one italic *Figure note:* line after the cell's unique tail string."""
    rep(cid, tail, tail + "\n\n" + text)


# ====================================================================================
# A. cell 3785f291 — the house-style cell delegates to plotstyle
# ====================================================================================
rep("3785f291",
    '# ---- house figure style (same tokens as z-ethan/mc/npv_winner_check.ipynb) -------\n'
    'COL = {"large": "#2a78d6", "smr": "#eb6834"}\n'
    'INK, MUTED, FAINT, GRID_C, EDGE_C, SURFACE = ("#0b0b0b", "#52514e", "#898781",\n'
    '                                              "#e1e0d9", "#c3c2b7", "#fcfcfb")\n'
    'mpl.rcParams.update({\n'
    '    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,\n'
    '    "axes.edgecolor": EDGE_C, "axes.labelcolor": MUTED, "text.color": INK,\n'
    '    "xtick.color": FAINT, "ytick.color": FAINT, "axes.grid": True, "grid.color": GRID_C,\n'
    '    "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,\n'
    '    "axes.titlecolor": INK, "font.size": 9, "axes.titlesize": 10, "figure.dpi": 110,\n'
    '    "legend.frameon": False,\n'
    '})',
    '# ---- house figure style: z-ethan/plotstyle.py is the normative standard ----------\n'
    'import sys\n'
    'sys.path.insert(0, str(HERE.parent))\n'
    'import plotstyle as ps\n'
    'ps.apply()\n'
    'COL = ps.COL\n'
    'INK, MUTED, FAINT, GRID_C, EDGE_C, SURFACE = (ps.INK, ps.MUTED, ps.FAINT,\n'
    '                                              ps.GRID_C, ps.EDGE_C, ps.SURFACE)')

rep("3785f291",
    '# Schedule identity: one fixed, ambition-ordered hue per schedule (viridis segment;\n'
    '# perceptually ordered and colorblind-safe). Never cycled; identity keeps its hue.\n'
    '_ramp = mpl.cm.viridis(np.linspace(0.02, 0.72, len(SCHEDULES)))\n'
    'SCHED_C = {s: mpl.colors.to_hex(c) for s, c in zip(SCHEDULES, _ramp)}\n'
    '# Percentile weight inside a schedule hue: p05 light, p50 solid, p95 heavy-dashed.\n'
    'PCT_STYLE = {"p05": dict(lw=1.2, alpha=0.55, ls="-"),\n'
    '             "p50": dict(lw=2.2, alpha=1.00, ls="-"),\n'
    '             "p95": dict(lw=1.6, alpha=0.85, ls="--")}',
    '# Schedule identity and percentile weight come from the central palette\n'
    '# (identical hexes and values; the ramp is now hardcoded in plotstyle).\n'
    'assert SCHEDULES == ps.SCHED_ORDER, (SCHEDULES, ps.SCHED_ORDER)\n'
    'SCHED_C = dict(ps.SCHED_C)\n'
    'PCT_STYLE = dict(ps.PCT_STYLE)')

rep("3785f291",
    'def savefig(fig, name):\n'
    '    p = FIGURES / name\n'
    '    fig.savefig(p, dpi=150, bbox_inches="tight")\n'
    '    print(f"wrote {p.relative_to(HERE)}")',
    'def savefig(fig, name):\n'
    '    p = FIGURES / name\n'
    '    ps.savefig(fig, p)\n'
    '    return p')

# ====================================================================================
# B + C, figure by figure
# ====================================================================================

# ---- f01 (fbcb9fe1): panel titles cut to categorical family labels; suptitle out ---
rep("fbcb9fe1",
    'for ax, fam, ttl in [(axes[0], "smr", "smr100: additions-basis floors (nuclear-smr)"),\n'
    '                     (axes[1], "large", "large100: fleet-inclusive floors (nuclear)")]:',
    'for ax, fam, ttl in [(axes[0], "smr", "smr100 (additions basis)"),\n'
    '                     (axes[1], "large", "large100 (fleet-inclusive)")]:')
rep("fbcb9fe1",
    'fig.suptitle("Mandate trajectories: six schedules, two bases", y=1.02)\n'
    'fig.tight_layout()',
    'fig.tight_layout()')
note("cd93ac1c", "This notebook does not read them.",
     "*Figure note (f01): mandate trajectories for the six schedules on the two "
     "bases — left panel: smr100 additions-basis floors (technology `nuclear-smr`); "
     "right panel: large100 fleet-inclusive floors (technology `nuclear`).*")

# ---- f02 (f0b32c20): title out; cap/floor annotation meaning moves to the legend ---
rep("f0b32c20",
    'handles = [mpl.patches.Patch(facecolor=cmap.colors[v], edgecolor=EDGE_C, label=k)\n'
    '           for k, v in STATE.items()]',
    'handles = [mpl.patches.Patch(facecolor=cmap.colors[v], edgecolor=EDGE_C,\n'
    '                             label=(k + " (cell shows cap/floor)"\n'
    '                                    if k == "clearly slack" else k))\n'
    '           for k, v in STATE.items()]')
rep("f0b32c20",
    'ax.set_title("Mandate state by case and model year (slack cells show cap/floor)")\n'
    'fig.tight_layout()',
    'fig.tight_layout()')

# ---- f03 (f4cd3400): suptitle encoded a legend -> real legend; SCHED_LABEL kept ----
rep("f4cd3400",
    'fig.suptitle("Delivered capacity against the mandate floor (dotted step). "\n'
    '             "Open circles: mandated years with a near-zero dual.", y=1.02)\n'
    'fig.tight_layout()',
    'axes[0, 0].legend(\n'
    '    [mpl.lines.Line2D([], [], color=INK, lw=1.0, ls=":"),\n'
    '     mpl.lines.Line2D([], [], marker="o", mfc="none", mec=COL["smr"],\n'
    '                      mew=1.4, ls="none")],\n'
    '    ["mandate floor", "mandated, near-zero dual"], fontsize=7, loc="upper left")\n'
    'fig.tight_layout()')
note("86ab11d5", "where the existing fleet path meets the early floor.",
     "*Figure note (f02): mandate state by case and model year; each clearly-slack "
     "cell shows the delivered-capacity / floor ratio.*\n\n"
     "*Figure note (f03): delivered capacity against the mandate floor (dotted "
     "step); open circles mark mandated years with a near-zero dual (orange edge "
     "in the smr100 row, blue edge in the large100 row).*")

# ---- f04 (50efbfee): suptitle out (its content is already in the axes legend) ------
rep("50efbfee",
    'fig.suptitle("Mandate dual trajectories: percentile fans per schedule, "\n'
    '             "large100 percentile band dashed", y=1.02)\n'
    'fig.tight_layout()',
    'fig.tight_layout()')
rep("50efbfee", '"mandate dual (2024$ / kW-yr)"', '"mandate dual (2024$/kW-yr)"')

# ---- f05 (6d2bd87e): descriptive title out --------------------------------------
rep("6d2bd87e",
    'ax.set_title("smr100 p50 dual paths, all six schedules")\n'
    'fig.tight_layout()',
    'fig.tight_layout()')
rep("6d2bd87e", '"mandate dual (2024$ / kW-yr)"', '"mandate dual (2024$/kW-yr)"')
note("255c8d67", "The fans exclude it.",
     "*Figure note (f04): mandate dual trajectories — percentile fans per "
     "schedule, with the large100 percentile band dashed.*\n\n"
     "*Figure note (f05): the six smr100 p50 dual paths on one panel.*")

# ---- f06 (b8178deb): descriptive title out --------------------------------------
rep("b8178deb",
    'ax.set_title("Mean binding dual against schedule ambition")\n'
    'fig.tight_layout()',
    'fig.tight_layout()')
rep("b8178deb", '"mean binding dual (2024$ / kW-yr)"', '"mean binding dual (2024$/kW-yr)"')
note("2d4dfe30", "It is not a supply curve.",
     "*Figure note (f06): mean binding dual against 2050 schedule ambition; "
     "orange circles = smr100, blue squares (dashed) = large100.*")

# ---- f15 (t15cd001): suptitle's band meaning moves into the legend ----------------
rep("t15cd001",
    'axes.flat[0].legend(fontsize=8)\n'
    'fig.suptitle("Required-subsidy bands: large100 p05-p95 against smr100 p05-p95 "\n'
    '             "(band = percentile range, line = p50)", y=1.02)\n'
    'fig.tight_layout()',
    'h15, l15 = axes.flat[0].get_legend_handles_labels()\n'
    'axes.flat[0].legend(\n'
    '    h15 + [mpl.patches.Patch(facecolor=COL["smr"], alpha=0.15),\n'
    '           mpl.patches.Patch(facecolor=COL["large"], alpha=0.15)],\n'
    '    l15 + ["smr100 p05-p95", "large100 p05-p95"], fontsize=7)\n'
    'fig.tight_layout()')
rep("t15cd001", '"mandate dual (2024$ / kW-yr)"', '"mandate dual (2024$/kW-yr)"')
note("t15md001", "basis, and drawn world.",
     "*Figure note (f15): required-subsidy bands per schedule — shaded band = the "
     "family's p05–p95 percentile range, line = p50.*")

# ---- f07 (4f4de157): percentile titles kept categorical; dashed meaning -> legend --
rep("4f4de157",
    'ax.set_title(p + " (dashed: large100)")',
    'ax.set_title(p)')
rep("4f4de157",
    'axes[0].legend(fontsize=8, ncols=2)\n'
    'fig.suptitle("Dual decay, normalized to each case peak", y=1.03)\n'
    'fig.tight_layout()',
    'h7, l7 = axes[0].get_legend_handles_labels()\n'
    'axes[0].legend(h7 + [mpl.lines.Line2D([], [], color=MUTED, lw=1.0, ls="--",\n'
    '                                      alpha=0.7)],\n'
    '               l7 + ["large100"], fontsize=8, ncols=2)\n'
    'fig.tight_layout()')
note("2d91220d", "weakly, at p50.",
     "*Figure note (f07): dual decay normalized to each case's peak, one panel "
     "per percentile; solid = smr100, dashed = large100 comparators.*")

# ---- f08 (44ef5584): descriptive title out; case name preserved in the note --------
rep("44ef5584",
    'ax.set_title(f"System cost anatomy: {REF}")\n'
    'ax.legend(fontsize=7.5, ncols=2)',
    'ax.legend(fontsize=7.5, ncols=2)')
rep("44ef5584", '"annual system cost (2024 $B / yr)"', '"annual system cost (2024$B/yr)"')

# ---- f09 (3fed34f2): suptitle out --------------------------------------------------
rep("3fed34f2",
    'fig.suptitle("Total annual system cost: percentile fans per schedule "\n'
    '             "(cross-schedule levels mix mandate and drawn world)", y=1.02)\n'
    'fig.tight_layout()',
    'fig.tight_layout()')
rep("3fed34f2", '"total system cost\\n(2024 $B / yr)"', '"total system cost\\n(2024$B/yr)"')

# ---- f10 (afbb2ec2): heterogeneous pair -> lettered; titles out; dashed -> legend --
rep("afbb2ec2",
    'axes[0].set_title("p95 - p05 annual cost spread\\n(same mandate, drawn world isolated; dashed: large100)")\n'
    'axes[0].set_ylabel("2024 $B / yr")\n'
    'axes[0].legend(fontsize=8, ncols=2)\n'
    'axes[1].set_title("smr100 - large100 annual cost at p50\\n(conditional what-if)")\n'
    'axes[1].axhline(0, color=EDGE_C, lw=1)',
    'axes[0].set_ylabel("annual cost difference (2024$B/yr)")\n'
    'h10, l10 = axes[0].get_legend_handles_labels()\n'
    'axes[0].legend(h10 + [mpl.lines.Line2D([], [], color=MUTED, lw=1.0, ls="--",\n'
    '                                       alpha=0.7)],\n'
    '               l10 + ["large100"], fontsize=8, ncols=2)\n'
    'axes[1].axhline(0, color=EDGE_C, lw=1)\n'
    'ps.letter_panels(axes)')
note("c6bf4e0b", "This notebook uses `systemcost` only.",
     "*Figure note (f08): system cost anatomy of the reference case "
     "`smr100_eia_p50`.*\n\n"
     "*Figure note (f09): total annual system cost — percentile fans per "
     "schedule; cross-schedule levels mix mandate and drawn world.*\n\n"
     "*Figure note (f10): panel a — p95 − p05 annual cost spread (same mandate, "
     "so the drawn world is isolated; solid = smr100, dashed = large100); "
     "panel b — smr100 − large100 annual cost at p50 (a conditional what-if).*")

# ---- f11 (dcecba76): descriptive title out -----------------------------------------
rep("dcecba76",
    'ax.set_title("System NPV against schedule ambition\\n"\n'
    '             "(levels mix mandate and drawn world; end effects penalize late builds)")\n'
    'fig.tight_layout()',
    'fig.tight_layout()')
rep("dcecba76", '"system NPV 2026-2050 (2024 $B)"', '"system NPV 2026-2050 (2024$B)"')
note("d99bbc0b", "the conflation caveat applies\non top.",
     "*Figure note (f11): system NPV against schedule ambition; levels mix "
     "mandate and drawn world, and end effects penalize late builds. Orange "
     "circles = smr100, blue squares (dashed) = large100.*")

# ---- f12 (bca1c170): suptitle + bar title out; window into ylabel; letters a/b ----
rep("bca1c170", '"R_t (2024 $B/yr)"', '"R_t (2024$B/yr)"')
rep("bca1c170",
    'axb.set_ylabel("PV of R_t (2024 $B)")\n'
    'axb.set_title("PV of the rental transfer, 2026-2050")',
    'axb.set_ylabel("PV of R_t, 2026-2050 (2024$B)")')
rep("bca1c170",
    'fig.suptitle("Rental transfer of the mandate: R_t = dual x mandated capacity", y=0.995)\n'
    'savefig(fig, "f12_rental_transfer.png")',
    'ps.panel_letter(fig.axes[0], "a")\n'
    'ps.panel_letter(axb, "b")\n'
    'savefig(fig, "f12_rental_transfer.png")')
note("ff3cf5d2", "That is a property of uniform instruments, not a bug.",
     "*Figure note (f12): the rental transfer R_t = dual × mandated capacity — "
     "panel a: R_t fans per schedule (smr100 solid with p05–p95 band, large100 "
     "dashed); panel b: PV of R_t over 2026–2050, per case.*")

# ---- f13 (0f97e237): suptitle out (48E band + insufficiency already annotated) ----
rep("0f97e237",
    'fig.suptitle("Required statutory ITC rate per solve year, smr100 "\n'
    '             "(credit cash at placed-in-service)", y=1.02)\n'
    'fig.tight_layout()',
    'fig.tight_layout()')
note("0c9c4e73",
     "The 48E band in the figure is 30% (base) to 50% (base plus bonuses).",
     "*Figure note (f13): required statutory ITC rate per solve year, smr100; "
     "the credit is cash at placed-in-service.*")

# ---- f14 (203eb154): suptitle out (band meaning already in the axes legend) --------
rep("203eb154",
    'fig.suptitle("Myopic requirement S_t against the foresight companion C_b, smr100 p50\\n"\n'
    '             "(band: the two post-2050 dual conventions)", y=1.03)\n'
    'fig.tight_layout()',
    'fig.tight_layout()')
rep("203eb154", '"support per build\\n(2024 $ / kW)"', '"support per build\\n(2024$/kW)"')
note("a1966a3a", "The code checks hold / S_t = 1 at 2050.",
     "*Figure note (f14): the myopic requirement S_t against the foresight "
     "companion C_b, smr100 p50; the band spans the two post-2050 dual "
     "conventions.*")

# ---- t13 figure (t13fg001): descriptive title out ----------------------------------
rep("t13fg001",
    'ax.set_title("Flat grant vs ITC: gross budget scoring reverses the net-of-tax ranking")\n'
    'ax.legend(fontsize=8, ncol=3)',
    'ax.legend(fontsize=8, ncol=3)')
note("t13md001",
     "and a credit dollar also cancels construction-period interest.",
     "*Figure note (t13 figure): credit cost / flat-grant cost per case; gross "
     "budget scoring reverses the net-of-tax ranking.*")

# ====================================================================================
NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"applied {n} edits -> {NB.name}")
