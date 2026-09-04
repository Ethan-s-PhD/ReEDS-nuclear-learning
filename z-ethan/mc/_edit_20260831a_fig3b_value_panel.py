"""Fig 3 recomposition, third pass (Ethan, 2026-08-31): panel b becomes the
baseline value-of-waiting panel -- total EVPI and the 2036 switch bound against
kappa in one panel -- and the fragmentation histogram moves to the SI (SF6).

Ruling (S2 drafting session): the main 2x2 pairs the winner and the value of
waiting, each at baseline and under optimism stress --
    a  P(SMR wins) vs kappa            (unchanged)
    b  EVPI + 2036 switch bound vs kappa   (this edit; was the fragmentation histogram)
    c  majority flip vs the optimism multiplier m   (ob_sweep edit)
    d  EVPI vs m                        (ob_sweep edit)
The fragmentation histogram joins SF6 (the mixing page) as panel f -- companion
edit _edit_20260831b_frag_to_sf6.py on mc_cost_trajectories.ipynb. House letter
rule: sources carry the final baked letters; the paper composes with letters="".

Edits (tech_comparison.ipynb):
- new cell t8c-fig3b-value-panel after t8b-evpi-inset: self-contained emission
  (reads evpi_total.csv + adaptive_value.csv) of the combined panel, baked "b"
  -> figures/tc_value_of_waiting.png
- T8b / T7b header comments: mark both inset PNGs as notebook-record artifacts
  (retired from the paper 2026-08-26; their content returns to the main text
  2026-08-31 combined in panel b).

Code cells change -> re-execute the notebook headless afterwards. Idempotent.
"""
import json
from pathlib import Path

NB = Path(__file__).resolve().parent / "tech_comparison.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
CELLS = {c["id"]: c for c in nb["cells"]}

if any(c["id"] == "t8c-fig3b-value-panel" for c in nb["cells"]):
    print("Fig 3b value panel already applied; nothing to do")
    raise SystemExit(0)

n = 0


def rep(cid, old, new):
    global n
    s = "".join(CELLS[cid]["source"])
    assert s.count(old) == 1, f"cell {cid}: pattern not unique/found:\n{old[:160]}"
    CELLS[cid]["source"] = s.replace(old, new).splitlines(keepends=True)
    n += 1


def code_cell(cid, src):
    return {"cell_type": "code", "execution_count": None, "id": cid,
            "metadata": {}, "outputs": [],
            "source": src.splitlines(keepends=True)}


def insert_after(anchor_id, cell):
    global n
    idx = next(i for i, c in enumerate(nb["cells"]) if c["id"] == anchor_id)
    nb["cells"].insert(idx + 1, cell)
    n += 1


# ---- t8c: paper Fig 3 panel b -- the baseline value-of-waiting panel ----------------
T8C = '''\
# t8c - paper Fig 3 panel b (added 2026-08-31): total EVPI and the 2036 switch
# bound against kappa, one panel -- the baseline "value of waiting" next to the
# optimism-stressed versions in panels c/d (ob_sweep). Self-contained like T8b:
# it reads the exports written above (evpi_total.csv, adaptive_value.csv), so it
# re-runs alone in a fresh kernel. Diagonal kappa cells only; the two probe
# cells stay on the SI page (SF7). Baked letter "b" (house rule: sources carry
# the final letters; the paper composes with letters="").
import sys as _sys
from pathlib import Path as _Path

import matplotlib.pyplot as _plt
from matplotlib.lines import Line2D as _Line2D
import pandas as _pd

_NB_DIR = _Path.cwd()
assert (_NB_DIR / "tech_comparison.ipynb").exists(), "run from z-ethan/mc"
if str(_NB_DIR.parent) not in _sys.path:
    _sys.path.insert(0, str(_NB_DIR.parent))
import plotstyle as _ps

_ps.apply()
_evpi = _pd.read_csv(_NB_DIR / "exports" / "tech_comparison" / "evpi_total.csv")
_adap = _pd.read_csv(_NB_DIR / "exports" / "tech_comparison" / "adaptive_value.csv")
_frames = {}
for _name, _df, _col in [("evpi", _evpi, "EVPI_pct"), ("bound", _adap, "bound_pct")]:
    _kap = _df["cell"].str.extract(r"^k(\\d{3})$", expand=False)
    _d = _df[_kap.notna()].copy()
    _d["kappa"] = _kap[_kap.notna()].astype(int) / 100.0
    _frames[_name] = _d
_scheds = list(dict.fromkeys(_frames["evpi"]["schedule"]))  # ambition order, as written by T8
assert list(dict.fromkeys(_frames["bound"]["schedule"])) == _scheds and len(_scheds) == 6
_col = {s: _ps.SCHED_C[t] for s, t in zip(_scheds, _ps.SCHED_ORDER)}

_fig, _ax = _plt.subplots(figsize=(6.4, 4.2))
for _s in _scheds:
    _dd = _frames["evpi"][_frames["evpi"]["schedule"] == _s].sort_values("kappa")
    _ax.plot(_dd["kappa"], _dd["EVPI_pct"], color=_col[_s], lw=1.8, marker="o", ms=4)
    _dd = _frames["bound"][_frames["bound"]["schedule"] == _s].sort_values("kappa")
    _ax.plot(_dd["kappa"], _dd["bound_pct"], color=_col[_s], lw=1.4, ls="--",
             marker="o", ms=3, mfc="none")
_ax.set_xlabel("cross-tech coupling κ  (κ_lr = κ_boak on the diagonal)")
_ax.set_ylabel("value of waiting\\n(% of expected program cost)")
_handles = ([_Line2D([], [], color=_col[_s], lw=1.8, label=_s) for _s in _scheds]
            + [_Line2D([], [], color=_ps.INK, lw=1.8, label="total EVPI"),
               _Line2D([], [], color=_ps.INK, lw=1.4, ls="--", label="2036 switch bound")])
_ax.legend(handles=_handles, fontsize=6.5, ncols=2)
_ps.panel_letter(_ax, "b")
_fig.tight_layout()
_ps.savefig(_fig, _NB_DIR / "figures" / "tc_value_of_waiting.png")
_plt.show()
'''

insert_after("t8b-evpi-inset", code_cell("t8c-fig3b-value-panel", T8C))

# ---- T8b / T7b headers: record-artifact status --------------------------------------
rep("t8b-evpi-inset",
    "# T8b - paper Fig 3 inset (panel c): total EVPI vs kappa, one compact panel.",
    "# T8b - notebook-record artifact (retired from the paper 2026-08-26, when the\n"
    "# sweep curves took Fig 3c/d; since 2026-08-31 the kappa profile is back in the\n"
    "# main text combined with the switch bound as panel b -- see t8c below).")
rep("t7b-fig3d-inset",
    "# T7b - paper Fig 3 panel d (added 2026-08-26): the switch bound without the",
    "# T7b - notebook-record artifact (retired from the paper 2026-08-26, when the\n"
    "# sweep curves took Fig 3c/d; since 2026-08-31 the kappa profile is back in the\n"
    "# main text combined with total EVPI as panel b -- see t8c below).\n"
    "# Originally: paper Fig 3 panel d (added 2026-08-26): the switch bound without the")

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"applied {n} edits -> {NB.name}")
