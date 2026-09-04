# 2026-09-03a — de-jargon the main-paper panels that z-ethan/mc emits (Figs 1, 2b/c, 3).
# Ethan's request (coauthor review, 09-03): every label baked into a paper figure must
# read in plain words — no internal codes (probe/pin, lr0/boak1, kappa = coherent,
# "supported world", "paired deployment", "occ"). Label strings only; no numeric change.
# Shared vocabulary lives in z-ethan/plotstyle.py (SCHED_SHORT, PCT_LABEL, ...).
#
# Targets:
#   atb_parameter_space.ipynb  cell atb-a6b-f8        -> Fig 1 a/b (re-executed in full)
#   mc_cost_trajectories.ipynb cell b7321195           -> Fig 2 b/c (re-executed in full)
#   tech_comparison.ipynb      cells t5b / t8c         -> Fig 3 a/b (PNGs re-emitted from the
#                                                        exports; the 32-min notebook re-runs later)
#   _build_ob_sweep.py + ob_sweep.ipynb (S4, S4b)      -> Fig 3 c/d (same: exports now, 70-min
#                                                        notebook later; builder and notebook
#                                                        sources stay byte-identical)
import io
import sys
from pathlib import Path

import nbformat

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent


def cell(nb, cid):
    for c in nb.cells:
        if c.get("id") == cid:
            return c
    raise KeyError(cid)


def sub(c, old, new, n=1):
    assert c.source.count(old) == n, f"{c.id!r}: expected {n} of {old!r}, got {c.source.count(old)}"
    c.source = c.source.replace(old, new)


XLAB_KAPPA = ('"cross-technology coupling κ\\n'
              '(0 = independent, 1 = shared learning rate and starting cost)"')

# --- Fig 1: atb_parameter_space F8 --------------------------------------------------
nb = nbformat.read(HERE / "atb_parameter_space.ipynb", as_version=4)
f8 = cell(nb, "atb-a6b-f8")
sub(f8, '# Fig 1 caption (fresh-start / legacy-fleet-credited).\n',
    '# Fig 1 caption (fresh-start / legacy-fleet-credited).\n'
    '# 09-03 (Ethan, coauthor review): the remaining labels read in plain words - "occ",\n'
    '# "supported world", "paired deployment", "reach" and the x label; no numeric change.\n')
sub(f8, 'label="lowest / highest\\nsupported world")',
    'label="lowest / highest world\\nin the learning-rate range")')
sub(f8, 'label="ATB 2050 target ±$125/kW\\nat its paired deployment")',
    'label="ATB 2050 target ±$125/kW\\nat the deployment the ATB assumes")')
sub(f8, 'ax.annotate(lbl + "\\nreach", (x_dim, 0.5*(lo_d + hi_d)),',
    'ax.annotate(lbl + " reach\\ntarget", (x_dim, 0.5*(lo_d + hi_d)),')
sub(f8, 'ax.set_title(f"{scen} (2050 target ${t50:,.0f}/kW)", fontsize=10)',
    'ax.set_title(f"ATB {scen} (2050 target ${t50:,.0f}/kW)", fontsize=10)')
sub(f8, '+ "\\n2050 occ (2022$/kW)")', '+ "\\n2050 overnight cost (2022$/kW)")')
sub(f8, 'ax.set_xlabel("post-2030 build completed through 2049 (GW; prices 2050)")',
    'ax.set_xlabel("cumulative new build, 2031–2049 (GW)")')
nbformat.write(nb, HERE / "atb_parameter_space.ipynb")
print("patched atb_parameter_space.ipynb (F8)")

# --- Fig 2b/c: mc_cost_trajectories OCC fans ----------------------------------------
nb = nbformat.read(HERE / "mc_cost_trajectories.ipynb", as_version=4)
c24 = cell(nb, "b7321195")
sub(c24, '# anchor -- the engine owns 2030 (equality there is QA-B-guaranteed, so the choice is\n'
         '# cosmetic). 2024 is dropped: no defined pre-FOAK vendor state.\n',
         '# anchor -- the engine owns 2030 (equality there is QA-B-guaranteed, so the choice is\n'
         '# cosmetic). 2024 is dropped: no defined pre-FOAK vendor state.\n'
         '# 09-03 (Ethan, coauthor review): y label reads "overnight cost", not "occ".\n')
sub(c24, 'set_ylabel(f"occ {ps.usd(\'kW\', 2022)}")',
    'set_ylabel(f"overnight cost {ps.usd(\'kW\', 2022)}")', n=2)
nbformat.write(nb, HERE / "mc_cost_trajectories.ipynb")
print("patched mc_cost_trajectories.ipynb (cell 24)")

# --- Fig 3a/b: tech_comparison T5b / t8c --------------------------------------------
nb = nbformat.read(HERE / "tech_comparison.ipynb", as_version=4)
t5b = cell(nb, "t5b-fig3a-panel")
sub(t5b, "# panel a with its final baked letter (house rule: sources carry the letters).\n",
    "# panel a with its final baked letter (house rule: sources carry the letters).\n"
    "# 09-03 (Ethan, coauthor review): plain-word labels - the pins are 'checks', the\n"
    "# probes say which channel is coupled, kappa is glossed on the axis.\n")
sub(t5b, 'label="pin: companion κ=1 (npv)")', 'label="check: κ = 1 run, NPV basis")')
sub(t5b, 'label="pin: mixed_build κ=0 (capex)")', 'label="check: κ = 0 run, capital-cost basis")')
sub(t5b, '("probe_lr0_boak1", -0.06, "^", "probe\\nlr0/boak1")',
    '("probe_lr0_boak1", -0.06, "^", "starting costs\\ncoupled only")')
sub(t5b, '("probe_lr1_boak0", 1.06, "v", "probe\\nlr1/boak0")',
    '("probe_lr1_boak0", 1.06, "v", "learning rates\\ncoupled only")')
sub(t5b, 'ax.set_xlabel("cross-tech coupling κ  (κ_lr = κ_boak on the diagonal)")',
    f'ax.set_xlabel({XLAB_KAPPA})')
sub(t5b, 'ax.set_ylabel("P(SMR wins the pure-program NPV contest)")',
    'ax.set_ylabel("probability the all-SMR program\\nis cheaper than all-large (NPV)")')
t8c = cell(nb, "t8c-fig3b-value-panel")
sub(t8c, '_ax.set_xlabel("cross-tech coupling κ  (κ_lr = κ_boak on the diagonal)")',
    f'_ax.set_xlabel({XLAB_KAPPA})')
sub(t8c, 'label="total EVPI")', 'label="value of perfect information (EVPI)")')
sub(t8c, 'label="2036 switch bound")', 'label="2036 switch option (upper bound)")')
nbformat.write(nb, HERE / "tech_comparison.ipynb")
print("patched tech_comparison.ipynb (T5b, t8c)")

# --- Fig 3c/d: ob_sweep builder + the executed notebook ----------------------------
# The builder holds these strings inside regular triple-quoted literals, so a
# newline escape is written "\\n" there and lands as "\n" in the notebook source.
OBS = [
    ('KLAB = {"k100": "kappa = 1 (coherent)", "k050": "kappa = 0.5", "k000": "kappa = 0"}',
     'KLAB = {"k100": "κ = 1 (fully coupled)", "k050": "κ = 0.5", "k000": "κ = 0 (independent)"}',
     1),
    ('ax.set_ylabel("P(SMR wins), min over schedules\\\\n(band: min-max across schedules)")',
     'ax.set_ylabel("probability the all-SMR program is cheaper\\\\n'
     '(line: lowest schedule; band: range across schedules)")', 2),
    ('ax.set_xlabel("SMR optimism-bias multiplier m")',
     'ax.set_xlabel("SMR optimism-bias multiplier m\\\\n(true SMR cost = m × sampled cost)")', 3),
]
bp = HERE / "_build_ob_sweep.py"
text = bp.read_text(encoding="utf-8")
for old, new, n in OBS:
    assert text.count(old) == n, (old, text.count(old))
    text = text.replace(old, new)
bp.write_text(text, encoding="utf-8")
print("patched _build_ob_sweep.py (S4, S4b)")

nb = nbformat.read(HERE / "ob_sweep.ipynb", as_version=4)
for old, new, n in OBS:
    o, w = old.replace("\\\\n", "\\n"), new.replace("\\\\n", "\\n")
    got = 0
    for c in nb.cells:
        if c.cell_type == "code" and o in c.source:
            got += c.source.count(o)
            c.source = c.source.replace(o, w)
    assert got == n, (o, got)
nbformat.write(nb, HERE / "ob_sweep.ipynb")
print("mirrored into ob_sweep.ipynb (S4, S4b)")
