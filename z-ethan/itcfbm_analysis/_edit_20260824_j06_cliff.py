"""j06 — the cliff on the statutory basis, new nuclear only (2026-08-24).

Promoted to main-text Fig 5c by team review 2026-08-24 (explicit one-exhibit
reversal of the delivery-to-SI demotion; the validation exhibits stay in the
SI). The builder (`_build_notebook.py`) already carries the same two cells —
this script mirrors them into the EXECUTED notebook without wiping its
outputs, because the h5 drive (D:) is unmounted and a full builder-regenerate
+ re-execute is not possible right now. Cell sources are byte-identical to
what the builder emits, so the next full rebuild produces no diff.

Idempotent; json + stdlib only.
"""
import json
from pathlib import Path

NB = Path(__file__).resolve().parent / "itcfbm_analysis.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))

if any(c.get("id") == "j06cd001" for c in nb["cells"]):
    print("j06 cells already present; nothing to do")
    raise SystemExit(0)

MD = """\
### j06 — The cliff on the statutory basis, new nuclear only (main-text panel)

Promoted to main-text Fig 5c on 2026-08-24 (team review; an explicit
one-exhibit reversal of the delivery-to-SI demotion — the validation exhibits
stay in the SI). Two changes against j04, both team rulings: (1) **new nuclear
only**, so every point shares the no-credit baseline — exact, because large
additions are credit-invariant in every run (the r06 zero-substitution
result, asserted); (2) the x axis is the **statutory rate on the model
convention** (monetized / (1 − PEN)), the same basis as Fig 5a, so the flat
anchors sit at their familiar 30% and 50% and the 48E band overlays exactly
as in that panel. The cell reads the committed r04 export, so it re-runs
without the h5 drive.\
"""

CODE = """\
# ---- j06: the cliff, statutory basis, new nuclear only (main-text Fig 5c; 2026-08-24) -----------
j06 = pd.read_csv(EXPORTS / "r04_rate_deployment.csv")
assert j06["large_2050_GW"].nunique() == 1          # large never moves with the credit
j06["new_GW"] = j06["smr_2050_GW"]                  # so new nuclear = SMR exactly
j06["i_stat"] = j06["m_monetized"] / (1 - PEN)      # statutory rate, model convention
J06_LAB = {"eia": "EIA AEO high", "aj": "Abou-Jaoude", "iaea": "IAEA high",
           "mck": "McKinsey", "cop28": "COP28", "eo": "EO 2025"}

fig, ax = plt.subplots(figsize=(6.4, 4.2))
ax.axvspan(0.30, 0.50, color=ps.NEUTRAL, alpha=0.55, zorder=1)
ax.text(0.40, 220, "48E range\\n30–50%", fontsize=7.5, color=MUTED,
        ha="center", va="top")

flat = j06[j06["kind"] == "flat-anchor"].sort_values("i_stat")
assert [round(v, 2) for v in flat["i_stat"]] == [0.0, 0.30, 0.50]
ax.plot(flat["i_stat"], flat["new_GW"], marker="s", ms=5, lw=1.6, color=INK,
        zorder=4, label="flat credit (eia world)")

for w in WORLDS:                                    # the three minus-probe ladder worlds
    fbc = j06[j06["kind"].isin(["schedule-fbCm", "schedule-fbC"])
              & (j06["world"] == w)].sort_values("i_stat")
    ax.plot(fbc["i_stat"], fbc["new_GW"], marker="o", ms=5, lw=1.8,
            color=SCHED_C[w], zorder=5, label=J06_LAB[w])
    fbb = j06[j06["kind"].isin(["schedule-fbBm", "schedule-fbB"])
              & (j06["world"] == w)].sort_values("i_stat")
    ax.plot(fbb["i_stat"], fbb["new_GW"], lw=1.1, ls="--", alpha=0.45,
            color=SCHED_C[w], zorder=3)
for w in ["eia", "iaea", "cop28"]:                  # headline-only worlds
    pt = j06[(j06["kind"] == "schedule-fbC") & (j06["world"] == w)]
    ax.scatter(pt["i_stat"], pt["new_GW"], marker="o", s=30, color=SCHED_C[w],
               zorder=5, label=J06_LAB[w] + " (headline only)")
ax.plot([], [], color=MUTED, lw=1.8, marker="o", ms=5, label="with learning (fbC)")
ax.plot([], [], color=MUTED, lw=1.1, ls="--", alpha=0.6, label="no learning (fbB)")
ax.set_xlabel("ITC rate (model convention; same basis as Fig 5a)")
ax.set_ylabel("new nuclear 2050 capacity (GW)")
ax.set_xlim(-0.02, 0.79)
ax.legend(fontsize=7, ncol=2, loc="upper left", handletextpad=0.5,
          columnspacing=1.0)
fig.tight_layout()
savefig(fig, "j06_new_nuclear_cliff.png")
plt.show()\
"""


def cell(kind, cid, src):
    c = {"cell_type": kind, "id": cid, "metadata": {},
         "source": src.splitlines(keepends=True)}
    if kind == "code":
        c["execution_count"] = None
        c["outputs"] = []
    return c


at = next(i for i, c in enumerate(nb["cells"])
          if "j04_deployment_vs_rate_cliff.png" in "".join(c["source"])
          and c["cell_type"] == "code") + 1
nb["cells"][at:at] = [cell("markdown", "j06md001", MD),
                      cell("code", "j06cd001", CODE)]

OLD_LIST = ("  `j04` — the deployment-vs-rate cliff; `j05` — the ignition "
            "cushion.")
NEW_LIST = ("  `j04` — the deployment-vs-rate cliff; `j05` — the ignition "
            "cushion;\n  `j06` — the cliff on the statutory basis, new "
            "nuclear only (main-text\n  Fig 5c).")
hits = 0
for c in nb["cells"]:
    if c["cell_type"] == "markdown":
        s = "".join(c["source"])
        if OLD_LIST in s:
            c["source"] = s.replace(OLD_LIST, NEW_LIST).splitlines(keepends=True)
            hits += 1
assert hits == 1, f"figure-list cell replacements: {hits}"

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"inserted j06md001 + j06cd001 at position {at}; figure list updated; wrote {NB.name}")
