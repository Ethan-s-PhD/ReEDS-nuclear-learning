"""Add the capex-denominated paper panels to step3_analysis.ipynb (2026-09-09).

Ethan's figure revisions (plan "zesty-purring-breeze"):
  * f01b — Fig 2a: the new-nuclear schedules alone (the SMR-program additions
    basis), one panel, no title, no smr100/large100 wording.
  * f04b — Fig 4: the mandate's shadow price capitalized over the model's own
    30-year evaluation window (x pvf_onm = 14.7645, flat from 2026), SMR program
    only, in 2024$/kW: the required reduction in financed capital cost.
  * f15b — Fig 7 (large vs SMR bands) on the same capitalized basis.

Nothing existing changes: three new code cells are inserted after f01
(fbcb9fe1), f04 (50efbfee) and t15/f15 (t15cd001). Every pre-existing export
and figure must stay byte-identical (`_regress_20260909.py`).

Edit method per the established convention (id-targeted, assert-guarded;
`_build_notebook.py` is STALE and must never be run). Idempotent. Run with any
python (json + stdlib only), then re-execute the notebook headless on the
playground-env kernel with drive D mounted.
"""
import json
from pathlib import Path

NB = Path(__file__).resolve().parent / "step3_analysis.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
IDS = [c["id"] for c in nb["cells"]]
CELLS = {c["id"]: c for c in nb["cells"]}

NEW = {"f01b-new-nuclear": "fbcb9fe1", "f04b-capex-gap": "50efbfee",
       "f15b-large-band-capex": "t15cd001"}
if all(k in IDS for k in NEW):
    print("edits already applied; nothing to do")
    raise SystemExit(0)
assert not any(k in IDS for k in NEW), "partially applied"


def src(cid):
    return "".join(CELLS[cid]["source"])


def new_code(cid, text):
    return {"cell_type": "code", "execution_count": None, "id": cid, "metadata": {},
            "outputs": [], "source": text.strip("\n").splitlines(keepends=True)}


# guards: the names the new cells lean on are defined in the cells they copy from
s01 = src("fbcb9fe1")
for tok in ["SMR_CASES", "parse_case", "TRAJ[", "SCHED_C[s]", "ps.SCHED_SHORT[s]",
            'savefig(fig, "f01_mandate_trajectories.png")']:
    assert tok in s01, tok
s04 = src("50efbfee")
for tok in ["* KWYR", "PCT_STYLE[p]", 'ps.PCT_LABEL[p]', "in_program", "SCHED_LABEL[s]",
            'savefig(fig, "f04_dual_fans.png")']:
    assert tok in s04, tok
s15 = src("t15cd001")
for tok in ["* KWYR", 'ps.PROGRAM_LABEL[fam', 'savefig(fig, "f15_large_band.png")']:
    assert tok in s15, tok
assert "PVF[c] = load(c, \"pvf_onm\")" in src("e2510eca")
assert "KWYR = 1e-3" in src("b2c98357")

F01B = r'''
# ---- f01b: the new-nuclear schedules alone (paper Fig 2a since 2026-09-09) --------------
# Ethan (09-09): one panel, the additions-basis mandate of each schedule ("new nuclear"),
# no program wording. The SMR-program mandate IS the new-capacity path (floor = 0), so it
# is the schedule itself; the fleet-inclusive large comparator stays in f01 above.
# Single panel: no title (house rule); the y label carries the meaning.
fig, ax = plt.subplots(figsize=(ps.W2, 4))
for s in SCHEDULES:
    cs = [c for c in SMR_CASES if parse_case(c)[1] == s and parse_case(c)[3] != "eq"]
    tr = TRAJ[cs[0]] / 1e3
    tr = tr[tr.index >= 2024]
    nz = tr[tr > 0]
    if len(nz):                    # blank the pre-start zero run,
        tr = tr[tr.index >= int(nz.index.min()) - 1]  # keep one zero year
    ax.plot(tr.index, tr.values, color=SCHED_C[s], lw=1.8)
    ax.annotate(ps.SCHED_SHORT[s], (tr.index[-1], tr.values[-1]), xytext=(4, 0),
                textcoords="offset points", color=SCHED_C[s], fontsize=8, va="center")
ax.set_xlabel("year")
ax.set_xlim(2029, 2052.5)    # the schedules start in 2031; one zero year kept
ax.set_ylabel("new nuclear capacity (GW)")
fig.tight_layout()
savefig(fig, "f01b_new_nuclear_trajectories.png")
plt.show()
'''

F04B = r'''
# ---- f04b: the shadow price capitalized -- required reduction in financed capital cost ----
# Ethan (09-09, paper Fig 4): the same fans as f04 in 2024$/kW of capacity instead of
# $/kW-yr, SMR program only (the large overlay leaves; Fig 7 keeps the comparison).
# ReEDS reports the mandate dual on the rental basis, raw / pvf_onm (report.gms); the
# raw dual is the year's capitalized cost gap of the marginal build over the model's own
# 30-year evaluation window, on the financed basis (OCC x fin_mult_noITC, the basis of
# the MC's financed capex). So dual x pvf_onm is exactly "how much lower the financed
# capital cost would have to be" in that year's solve -- no OCC conversion. pvf_onm is
# flat from 2026 (step3_checks: 14.7645, max dev 1e-6); the plotted years start 2029.
PVFO = float(PVF[SMR_CASES[0]].loc[2031])
assert abs(PVFO - 14.7645) < 1e-3, PVFO
for c in CASES:
    pv = PVF[c]
    assert (abs(pv[pv.index >= 2026] - PVFO) < 1e-3).all(), c
CAPEX_GAP_LABEL = "required reduction in\nfinanced capital cost (2024$/kW)"
fig, axes = plt.subplots(2, 3, figsize=(12.5, 6.5), sharex=True, sharey=True)
for k, s in enumerate(SCHEDULES):
    ax = axes.flat[k]
    piv = (DUALS[(DUALS["family"] == "smr") & (DUALS["schedule"] == s)
                 & (DUALS["variant"] != "eq") & (DUALS["t"] >= 2029)
                 & DUALS["in_program"]]         # blank, not zero, before builds
           .pivot_table(index="t", columns="pct", values="dual_2024_MWyr") * KWYR * PVFO)
    ax.fill_between(piv.index, piv["p05"], piv["p95"], color=SCHED_C[s], alpha=0.14, lw=0)
    for p in ("p05", "p50", "p95"):
        ax.plot(piv.index, piv[p], color=SCHED_C[s], **PCT_STYLE[p])
        dd = DUALS[(DUALS["case"] == f"smr100_{s}_{p}") & (DUALS["t"] >= 2029)
                   & DUALS["in_program"]]
        bind = dd[dd["binding"]]
        ax.plot(bind["t"], bind["dual_2024_MWyr"] * KWYR * PVFO, "o", ms=3.5,
                color=SCHED_C[s], alpha=PCT_STYLE[p]["alpha"])
        zz = dd[~dd["binding"]]
        ax.plot(zz["t"], zz["dual_2024_MWyr"] * KWYR * PVFO, "o", ms=6, mfc="none",
                mec=COL["smr"], mew=1.2, zorder=5)
    ax.set_title(SCHED_LABEL[s], fontsize=9)
    if k % 3 == 0:
        ax.set_ylabel(CAPEX_GAP_LABEL)
    if k >= 3:
        ax.set_xlabel("year")
handles = ([mpl.lines.Line2D([], [], color=INK, **{k: v for k, v in PCT_STYLE[p].items()})
            for p in ("p05", "p50", "p95")]
           + [mpl.lines.Line2D([], [], marker="o", mfc="none", mec=COL["smr"], ls="none")])
axes.flat[0].legend(handles, [ps.PCT_LABEL[p] for p in ("p05", "p50", "p95")]
                    + ["mandated year, gap ≈ 0"], fontsize=7.5, loc="upper right")
for ax in axes.flat:   # integer year ticks (fractional after masking)
    ax.xaxis.set_major_locator(mpl.ticker.MaxNLocator(integer=True))
fig.tight_layout()
savefig(fig, "f04b_capex_gap_fans.png")
plt.show()
'''

F15B = r'''
# ---- f15b: the two programs' bands on the capitalized basis (paper Fig 7 since 09-09) ----
# Same construction as f15, in 2024$/kW of capacity (x PVFO, defined at f04b).
fig, axes = plt.subplots(2, 3, figsize=(12.5, 6.5), sharex=True, sharey=True)
for k, s in enumerate(SCHEDULES):
    ax = axes.flat[k]
    for fam, colr in (("smr", COL["smr"]), ("large", COL["large"])):
        piv = (DUALS[(DUALS["family"] == fam) & (DUALS["schedule"] == s)
                     & (DUALS["variant"] != "eq") & (DUALS["t"] >= 2029)
                     & DUALS["in_program"]]     # blank, not zero, before builds
               .pivot_table(index="t", columns="pct", values="dual_2024_MWyr") * KWYR * PVFO)
        ax.fill_between(piv.index, piv["p05"], piv["p95"], color=colr, alpha=0.15, lw=0)
        ax.plot(piv.index, piv["p50"], color=colr, lw=1.8,
                label=f"{ps.PROGRAM_LABEL[fam + '100']}, median world" if k == 0 else None)
    ax.set_title(SCHED_LABEL[s], fontsize=9)
    if k % 3 == 0:
        ax.set_ylabel(CAPEX_GAP_LABEL)
    if k >= 3:
        ax.set_xlabel("year")
h15b, l15b = axes.flat[0].get_legend_handles_labels()
axes.flat[0].legend(
    h15b + [mpl.patches.Patch(facecolor=COL["smr"], alpha=0.15),
            mpl.patches.Patch(facecolor=COL["large"], alpha=0.15)],
    l15b + ["SMR program, P5–P95", "large-reactor program, P5–P95"], fontsize=7)
for ax in axes.flat:   # integer year ticks (fractional after masking)
    ax.xaxis.set_major_locator(mpl.ticker.MaxNLocator(integer=True))
fig.tight_layout()
savefig(fig, "f15b_large_band_capex.png")
plt.show()
'''

for cid, after, text in [("f01b-new-nuclear", "fbcb9fe1", F01B),
                         ("f04b-capex-gap", "50efbfee", F04B),
                         ("f15b-large-band-capex", "t15cd001", F15B)]:
    ids = [c["id"] for c in nb["cells"]]
    k = ids.index(after)
    nb["cells"].insert(k + 1, new_code(cid, text))
    print(f"inserted {cid} after {after} (index {k + 1})")

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"wrote {NB.name}")
