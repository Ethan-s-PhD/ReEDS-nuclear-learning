"""f17 — the uniform-ITC premium by ambition (2026-08-24, Fig 5b option B).

Team ruling 2026-08-24: panel 5b of the main figure is replaced. The paper
reports the floor and the ITC (demotion ruling of 08-20), so the main panel
shows only the voluntary instruments on a linear axis; the full menu (f16,
with the mandate cut-hold band and the commitment bound) moves to the SI, and
the closed-loop delivery panel (h04) moves to the SI as validation.

Edit method per the established convention (id-targeted, assert-guarded edits
on the notebook JSON; idempotent; json + stdlib only). This script only
INSERTS two cells (f17md001, f17cd001) after t18cd001. It does not touch any
existing cell.

Execution note: the notebook's run folders were consolidated into "All runs
so far" on 2026-08-18 and the notebook's h5 paths are stale, so a full
headless re-execution would fail before reaching this cell. The new cell
depends only on the in-memory t18 frame (identical to the committed
exports/t18_instrument_menu.csv — t18 is rounded before both uses), so the
PNG is emitted once by executing this cell's exact source against the CSV
(see _emit_f17 in the session scratchpad); the cell itself runs normally on
the next full pass.
"""
import json
from pathlib import Path

NB = Path(__file__).resolve().parent / "step3_analysis.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
ids = [c["id"] for c in nb["cells"]]

if "f17cd001" in ids:
    print("f17 cells already present; nothing to do")
    raise SystemExit(0)

MD = """\
### f17 - the uniform-ITC premium by ambition (main-text panel)

Chosen 2026-08-24 (team review, option B) as the main-figure replacement for
f16. The paper reports the floor and the ITC (demotion ruling of 08-20), so
the main panel keeps only the voluntary instruments, and the axis goes
linear: the uniform percentage ITC per schedule, ordered by 2050 ambition
(marker = P50 cost world, whisker = P5-P95 range, one series per
technology), over the floor line and the haircut-only line, with the cash
grant as context. The read: the premium is 1.17-1.25x the floor everywhere
and does not grow with ambition, cost world, or technology; it decomposes
into the 10% monetization haircut (x1.111) plus the 5-13% uniform-rate
oversubsidy. f16 keeps the full menu (mandate cut-hold band, commitment
bound) and moves to the SI.
"""

CODE = """\
# ---- f17: the uniform-ITC premium by ambition (main-text Fig 5b; option B, 2026-08-24) -----------
# Voluntary instruments only, per the 08-20 demotion ruling: the mandate and
# commitment marks stay in f16 (SI).
f17 = t18[~t18["case"].str.endswith("_eq")].copy()
cparts = f17["case"].str.split("_", expand=True)
f17["fam"], f17["sched"], f17["pct"] = cparts[0], cparts[1], cparts[2]
HAIR17 = float(f17["dpmw_haircut"].iloc[0])            # 1/(1-PEN) = 1.111
GRANT17 = float(f17["cash_grant"].iloc[0])
assert (f17["cash_grant"] == GRANT17).all()            # the grant is flat across cases

FAM_C = {"smr100": COL["smr"], "large100": COL["large"]}
FAM_LAB = {"smr100": ps.TECH_LABEL["smr"], "large100": ps.TECH_LABEL["large"]}
fig, ax = plt.subplots(figsize=(ps.W1, 4.0))
x0 = np.arange(len(SCHEDULES))
OFF17 = {"smr100": -0.14, "large100": +0.14}
ax.axhline(GRANT17, color=MUTED, lw=2.4, alpha=0.35, zorder=1,
           label=f"unleveraged cash grant ({GRANT17:.2f}×, all cases)")
for fam in ("smr100", "large100"):
    for i, s in enumerate(SCHEDULES):
        sub = f17[(f17["fam"] == fam) & (f17["sched"] == s)]
        assert len(sub) == 3, (fam, s)                 # p05/p50/p95 all present
        x = x0[i] + OFF17[fam]
        ax.vlines(x, sub["uniform_itc"].min(), sub["uniform_itc"].max(),
                  color=FAM_C[fam], lw=1.4, alpha=0.8, zorder=3)
        p50v = float(sub.loc[sub["pct"] == "p50", "uniform_itc"].iloc[0])
        ax.scatter([x], [p50v], s=26, color=FAM_C[fam], zorder=4,
                   label=FAM_LAB[fam] if i == 0 else None)
ax.axhline(1.0, lw=1.1, color=INK, zorder=2)
ax.axhline(HAIR17, lw=0.9, color=MUTED, ls=":", zorder=2)
ax.text(-0.42, 1.0, "floor: flat $/MW at commissioning, frictionless",
        fontsize=7.5, color=INK, va="bottom", ha="left")
ax.text(-0.42, HAIR17, f"floor + 10% monetization haircut (×{HAIR17:.2f})",
        fontsize=7.5, color=MUTED, va="bottom", ha="left")
ax.set_xlim(-0.5, len(x0) - 0.3)
ax.set_ylim(0.96, 1.29)
ax.set_xticks(x0)
ax.set_xticklabels([SCHED_LABEL[s].replace(" (", "\\n").rstrip(")")
                    for s in SCHEDULES], fontsize=7.5)
ax.set_xlabel("mandate schedule, by 2050 ambition")
ax.set_ylabel("net PV cost / floor")
ax.legend(loc="upper right", fontsize=7.5, handletextpad=0.4)
fig.tight_layout()
savefig(fig, "f17_itc_vs_ambition.png")
plt.show()
print(f"uniform ITC / floor, all cases: "
      f"{f17['uniform_itc'].min():.2f}-{f17['uniform_itc'].max():.2f}; oversubsidy "
      f"{(f17['uniform_itc'].min() / HAIR17 - 1) * 100:.0f}-"
      f"{(f17['uniform_itc'].max() / HAIR17 - 1) * 100:.0f}%")
"""


def cell(kind, cid, src):
    c = {"cell_type": kind, "id": cid, "metadata": {},
         "source": src.splitlines(keepends=True)}
    if kind == "code":
        c["execution_count"] = None
        c["outputs"] = []
    return c


at = ids.index("t18cd001") + 1
nb["cells"][at:at] = [cell("markdown", "f17md001", MD),
                      cell("code", "f17cd001", CODE)]

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"inserted f17md001 + f17cd001 after t18cd001 (position {at}); wrote {NB.name}")
