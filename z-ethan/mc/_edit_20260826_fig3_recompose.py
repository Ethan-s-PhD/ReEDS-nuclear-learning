"""Fig 3 recomposition (Ethan, 2026-08-26): the composed figure becomes a 2x2 of
single-panel sources -- (a) probability panel, (b) fragmentation histogram,
(c) EVPI inset, (d) 2036 switch-bound inset.

Rulings: the winning-margin fans (old Fig 3b) move to the SI as SF5a; the McKinsey
financed-capex paths (old Fig 3c) leave the paper entirely (Fig 2's fans and the
fragmentation histogram carry that story); the SF8 perfect-information switch bound
is promoted to panel (d), completing the commitment case -- choose SMR, don't split,
don't wait, don't count on switching. House letter rule: sources carry the final
baked letters; the paper composes with letters="".

Edits (tech_comparison.ipynb):
- new cell t5b-fig3a-panel after T5a (c16fddcb): panel-a re-emission (P(SMR) vs kappa
  + pins + probes), baked "a" -> figures/tc_robustness_prob.png
- new cell t5c-margin-fans-si after it: old panel b standalone for the SI (SF5a),
  with its own schedule legend, no letter -> figures/tc_margin_fans.png
- new cell t7b-fig3d-inset after T7 (a7361914): the PI sequencing bound WITHOUT the
  C5 threshold rule (claims-ledger internals stay on SF8's tc_adaptive_bound.png),
  baked "d" -> figures/tc_adaptive_bound_inset.png
- T8b (t8b-evpi-inset): baked letter e -> c; provenance comment restated.

Code cells change -> re-execute the notebook headless afterwards. Idempotent.
(The fragmentation histogram's standalone emission is the companion edit in
_edit_20260826_frag_hist.py on mc_cost_trajectories.ipynb.)
"""
import json
from pathlib import Path

NB = Path(__file__).resolve().parent / "tech_comparison.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
CELLS = {c["id"]: c for c in nb["cells"]}

if any(c["id"] == "t5b-fig3a-panel" for c in nb["cells"]):
    print("Fig 3 recomposition already applied; nothing to do")
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


# ---- T5b: paper Fig 3 panel a, standalone -------------------------------------------
T5B = '''\
# T5b - paper Fig 3 panel a (added 2026-08-26): the probability panel alone.
# The composed Fig 3 became a 2x2 of single-panel sources (a = this, b = the
# fragmentation histogram, c = the EVPI inset, d = the switch-bound inset), so
# T5a's two-panel figure stays a notebook-record artifact and this cell re-emits
# panel a with its final baked letter (house rule: sources carry the letters).
diag = ROBUST[ROBUST["cell"].isin(KAPPA_ID.values())]
fig, ax = plt.subplots(figsize=(6.8, 4.8))
for sched in SCHED_ORDER:
    d = diag[diag["schedule"] == sched].sort_values("kappa_lr")
    ax.errorbar(d["kappa_lr"], d["P_smr"], yerr=[d["P_smr"]-d["ci_lo"], d["ci_hi"]-d["P_smr"]],
                color=SCHED_COLORS[sched], lw=1.8, marker="o", ms=4, capsize=2, label=sched)
ax.plot(np.ones(len(SCHED_ORDER)), [PIN_K1_NPV[s] for s in SCHED_ORDER], ls="",
        marker="D", ms=6, mfc="none", mec=INK, label="pin: companion κ=1 (npv)")
ax.plot(np.zeros(len(SCHED_ORDER)), [PIN_K0_CAPEX[s] for s in SCHED_ORDER], ls="",
        marker="s", ms=6, mfc="none", mec=MUTED, label="pin: mixed_build κ=0 (capex)")
for iid, xoff, mk, cap in [("probe_lr0_boak1", -0.06, "^", "probe\\nlr0/boak1"),
                           ("probe_lr1_boak0", 1.06, "v", "probe\\nlr1/boak0")]:
    d = ROBUST[ROBUST["cell"] == iid]
    ax.scatter(np.full(len(d), xoff), d["P_smr"], marker=mk, s=28,
               c=[SCHED_COLORS[s] for s in d["schedule"]], zorder=4)
    ax.text(xoff, d["P_smr"].min() - 0.015, cap, ha="center", va="top",
            fontsize=7, color=MUTED)
ax.axhline(0.5, color=EDGE_C, lw=1, ls="--")
ax.set_xlabel("cross-tech coupling κ  (κ_lr = κ_boak on the diagonal)")
ax.set_ylabel("P(SMR wins the pure-program NPV contest)")
ax.set_ylim(0.45, 1.0)
ax.legend(fontsize=6.5, loc="upper center", bbox_to_anchor=(0.5, -0.15), ncols=3)
ps.panel_letter(ax, "a")
fig.tight_layout()
ps.savefig(fig, FIGURES / "tc_robustness_prob.png")
plt.show()
'''

# ---- T5c: old panel b standalone for the SI (SF5a) ----------------------------------
T5C = '''\
# T5c - SI figure SF5a (added 2026-08-26): the winning-margin fans standalone.
# Old Fig 3b; evicted in the 2x2 recomposition (Ethan) and re-homed in the SI
# next to the gap-plane maps. Same content as T5a's panel b, plus its own
# schedule legend (panel a's shared legend no longer travels with it).
diag = ROBUST[ROBUST["cell"].isin(KAPPA_ID.values())]
fig, ax = plt.subplots(figsize=(8.5, 4.4))
for sched in SCHED_ORDER:
    d = diag[diag["schedule"] == sched].sort_values("kappa_lr")
    ax.plot(d["kappa_lr"], d["m_pct_P50"], color=SCHED_COLORS[sched], lw=1.8, marker="o",
            ms=4, label=sched)
    ax.fill_between(d["kappa_lr"], d["m_pct_P25"], d["m_pct_P75"],
                    color=SCHED_COLORS[sched], alpha=0.10, lw=0)
ax.axhline(0, color=EDGE_C, lw=1)
ax.set_xlabel("cross-tech coupling κ")
ax.set_ylabel("pure-program margin m (%)  —  m > 0 ⇒ SMR wins")
ax.legend(fontsize=7)
fig.tight_layout()
ps.savefig(fig, FIGURES / "tc_margin_fans.png")
plt.show()
'''

# ---- T7b: paper Fig 3 panel d, the bound without the claims-ledger dressing ---------
T7B = '''\
# T7b - paper Fig 3 panel d (added 2026-08-26): the switch bound without the
# claims-ledger dressing. SF8's tc_adaptive_bound.png keeps the C5 threshold
# rule; the main-text panel shows only the bound itself, lettered "d" to close
# the composed 2x2 (a prob / b fragmentation / c EVPI / d this).
fig, ax = plt.subplots(figsize=(6.4, 4.2))
for sched in SCHED_ORDER:
    d = ADAPT[(ADAPT["schedule"] == sched)
              & (ADAPT["cell"].isin(KAPPA_ID.values()))].copy()
    d["kappa"] = d["cell"].map({v: k for k, v in KAPPA_ID.items()})
    d = d.sort_values("kappa")
    ax.plot(d["kappa"], d["bound_pct"], color=SCHED_COLORS[sched], lw=1.8, marker="o",
            ms=4, label=sched)
ax.set_xlabel("cross-tech coupling κ")
ax.set_ylabel("value of one 2036 technology switch\\n(% of expected program cost)")
ax.legend(fontsize=7)
ps.panel_letter(ax, "d")
fig.tight_layout()
ps.savefig(fig, FIGURES / "tc_adaptive_bound_inset.png")
plt.show()
'''

insert_after("c16fddcb", code_cell("t5b-fig3a-panel", T5B))
insert_after("t5b-fig3a-panel", code_cell("t5c-margin-fans-si", T5C))
insert_after("a7361914", code_cell("t7b-fig3d-inset", T7B))

# ---- T8b: reletter e -> c, restate the provenance comment ---------------------------
rep("t8b-evpi-inset",
    "# T8b - paper Fig 3 inset (panel e): total EVPI vs kappa, one compact panel.",
    "# T8b - paper Fig 3 inset (panel c): total EVPI vs kappa, one compact panel.")
rep("t8b-evpi-inset",
    '# the T4 grid in memory. The baked letter "e" follows the robustness map\'s a/b and\n'
    "# the fragmentation figure's c/d in the composed paper figure (Fig 3).",
    '# the T4 grid in memory. The baked letter "c" follows the 2026-08-26 2x2\n'
    "# recomposition (a = probability panel, b = fragmentation histogram, d = the\n"
    "# 2036 switch-bound inset).")
rep("t8b-evpi-inset",
    '_ps.panel_letter(_ax, "e")',
    '_ps.panel_letter(_ax, "c")')

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"applied {n} edits -> {NB.name}")
