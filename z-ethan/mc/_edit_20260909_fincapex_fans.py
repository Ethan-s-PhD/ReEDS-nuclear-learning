# 2026-09-09 — financed-capital-cost fans for the paper's Fig 2b/c (Ethan's figure
# revisions, plan "zesty-purring-breeze"): Fig 2b/c now show only the Abou-Jaoude and
# 2025 EO schedules, on ONE shared y axis, in financed capital cost (OCC x ccmult at the
# draw's learned duration x the non-IDC financing rest; S7) instead of overnight cost.
# One new code cell is inserted after the OCC-fan cell (b7321195); nothing existing
# changes. The notebook is then re-executed in full on the playground-env kernel.
#
# Edit method per the established convention: id-targeted, assert-guarded nbformat
# surgery; the notebook has no builder.
import io
import sys
from pathlib import Path

import nbformat

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
NB = HERE / "mc_cost_trajectories.ipynb"
NEW_ID = "fincapex-fans-aj-eo"

NEW_SRC = r'''# Financed-capital-cost fans for the paper's Fig 2b/c (Ethan, 09-09): the OCC fans'
# construction, on fincapex = OCC x ccmult(learned duration) x fin_mult_rest (2022 $/kW,
# no ITC; S7) - the cost that carries construction duration and financing. Two
# schedules only (Abou-Jaoude, 2025 EO), one figure per technology, and ONE fixed
# y range shared by all four panels so the two technologies read on the same scale.
# Pre-2030 segment: the plot-only OCC backcast x the draw's own 2025-2029 multiplier
# (results[...]["ccmult"] and FIN_REST cover 2024-2050), so the 2030 splice is exact
# like the OCC fans'. Homogeneous small multiples: not lettered (compose stamps them).
FIN_FAN_SCHEDS = ["Abou-Jaoude mod", "2025 EO"]
assert all(s in SCHED_ORDER for s in FIN_FAN_SCHEDS)
_pre = slice(yi(BACK_YEARS[0]), yi(ANCHOR))                 # 2025..2029 in the YEARS grid
assert YEARS[_pre].tolist() == BACK_YEARS[:-1].tolist()
FIN_FAN_PCT = {}
for tech in TECH:
    for sched in FIN_FAN_SCHEDS:
        r = results[sched][tech]
        mult = r["ccmult"] * FIN_REST[tech][None, :]         # (N_DRAWS, T) financing multiplier
        pre = OCC_BACKCAST[sched][tech][:, :-1] * mult[:, _pre]
        assert np.isfinite(pre).all()
        # splice QA: the backcast's 2030 column x the 2030 multiplier IS the engine's fincapex
        assert np.allclose(OCC_BACKCAST[sched][tech][:, -1] * mult[:, yi(ANCHOR)],
                           r["fincapex"][:, yi(ANCHOR)]), (sched, tech)
        paths = np.concatenate([pre, r["fincapex"][:, yi(ANCHOR):]], axis=1)
        FIN_FAN_PCT[(tech, sched)] = pd.DataFrame(
            {f"P{p}": np.percentile(paths, p, axis=0) for p in (5, 25, 50, 75, 95)},
            index=PLOT_YEARS)
# one y range for all four panels: zero to the next 1,000 above the highest P95
YLIM_FIN = (0.0, float(np.ceil(max(d["P95"].max() for d in FIN_FAN_PCT.values()) / 1000.0) * 1000.0))
for tech, tlabel in [("large", "Large LWR (1 GWe)"), ("smr", "SMR (300 MWe)")]:
    fig, axes = plt.subplots(1, 2, figsize=(ps.W2, 3.4), sharey=True, sharex=True)
    c = ps.COL[tech]
    for ax, sched in zip(axes, FIN_FAN_SCHEDS):
        pct = FIN_FAN_PCT[(tech, sched)]
        ax.fill_between(PLOT_YEARS, pct["P5"], pct["P95"], alpha=0.18, color=c)
        ax.fill_between(PLOT_YEARS, pct["P25"], pct["P75"], alpha=0.35, color=c)
        ax.plot(PLOT_YEARS, pct["P50"], color=c, lw=1.8)
        ax.axvline(ANCHOR, ls=":", c=ps.FAINT, lw=1)
        ax.set_title(f"{sched} ({US_SCHEDULES[sched][-1] - OFFSET_GW:.0f} GW 2050)", fontsize=9)
        ax.set_ylim(*YLIM_FIN)
    axes[0].set_ylabel(f"financed capital cost {ps.usd('kW', 2022)}")
    axes[0].legend(handles=[Patch(color=c, alpha=0.18, label="P5-P95"),
                            Patch(color=c, alpha=0.35, label="P25-P75"),
                            Line2D([], [], color=c, lw=1.8, label="median")],
                   title=tlabel, fontsize=7, loc="lower left")
    plt.tight_layout()
    ps.savefig(fig, FIGURES / f"fincapex_fans_{tech}.png")
    plt.show()
# the plotted percentiles (2025-2050, backcast included), for the paper captions
_fin_fan_out = pd.concat({(t, SCEN_TOKEN[s]): d.round(1) for (t, s), d in FIN_FAN_PCT.items()}, axis=1)
_fin_fan_out.to_csv(EXPORTS / "fincapex_fans_aj_eo_percentiles.csv")
print(f"shared y range {YLIM_FIN}; wrote exports/fincapex_fans_aj_eo_percentiles.csv")
for (t, s), d in FIN_FAN_PCT.items():
    print(f"  {t:5s} {s:16s} 2050 P50 {d.loc[2050, 'P50']:8,.0f}  P5-P95 {d.loc[2050, 'P5']:8,.0f}-{d.loc[2050, 'P95']:8,.0f}")
'''

nb = nbformat.read(NB, as_version=4)
ids = [c.get("id") for c in nb.cells]
assert NEW_ID not in ids, "already applied"
k = ids.index("b7321195")
c24 = nb.cells[k]
assert 'ps.savefig(fig, FIGURES / f"occ_fans_{tech}.png")' in c24.source
assert "PLOT_YEARS = np.concatenate" in c24.source
new = nbformat.v4.new_code_cell(NEW_SRC.strip())
new["id"] = NEW_ID
nb.cells.insert(k + 1, new)
nbformat.write(nb, NB)
print(f"inserted cell {NEW_ID!r} after b7321195 (now index {k + 1}) in {NB.name}")
