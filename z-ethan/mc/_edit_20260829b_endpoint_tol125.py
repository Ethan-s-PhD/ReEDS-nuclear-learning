# 2026-08-29b - endpoint criterion moves to $125/kW (Ethan's ruling, 08-29).
# Rationale: the ATB rounds its published costs to the nearest $250/kW, so the true value
# lies within one half-step ($125) of the published number - the criterion now grants
# exactly that reported-precision noise, superseding the one-increment $250 criterion.
# Scope: ENDPOINT machinery only (F8 panel reads, F9 maps + endpoint_feasible_share.csv,
# F10 marginals, ST12 his-anchor cell). The Part-1 trajectory/milestone tolerance stays
# at $250 - it is a different object (max-abs fit at the 2035-2050 milestones).
# F8 panel spec (third spec, 08-29): black bar = target +-$125 band share (two-sided);
# red bracket = envelope floor -> target + $125, labeled with the ONE-SIDED criterion
# share itself; bracket omitted where that share is zero (the large legacy-fleet rows).
# The strictly-below read (second 08-28 spec) is retired from notebook and tables.
import io
import sys

import nbformat

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

NB = "atb_parameter_space.ipynb"
nb = nbformat.read(NB, as_version=4)


def cell(cid):
    for c in nb.cells:
        if c.get("id") == cid:
            return c
    raise KeyError(cid)


def sub(c, old, new, n=1):
    if old not in c.source:
        raise AssertionError(f"pattern not found in {c.id!r}: {old[:90]!r}")
    assert c.source.count(old) == n, f"pattern count != {n} in {c.id!r}: {old[:90]!r}"
    c.source = c.source.replace(old, new)


# --- a12: scope the milestone tolerance, add the endpoint tolerance -------------------
c = cell("atb-12-a12_fit")
sub(c,
    "TOL = 250.0                      # primary feasibility tolerance ($/kW, max-abs at 2035-2050)",
    "TOL = 250.0                      # trajectory (milestone) fit tolerance ($/kW, max-abs at 2035-2050)\n"
    "TOL_END = 125.0                  # endpoint feasibility tolerance ($/kW) - 08-29 (Ethan): the ATB\n"
    "                                 # rounds to the nearest $250/kW, so the true value lies within one\n"
    "                                 # half-step ($125) of the published number; supersedes the\n"
    "                                 # one-increment $250 endpoint criterion in F8/F9/F10 + the exports")

# --- A6b header markdown --------------------------------------------------------------
c = cell("atb-a6b-hdr")
sub(c,
    "cost (OCC(2050) ≤ target + \\$250/kW at the paired deployment).",
    "cost (OCC(2050) ≤ target + \\$125/kW at the paired deployment; \\$125 since 08-29 — one\n"
    "rounding half-step of the ATB's nearest-\\$250 reporting, i.e. the published-precision\n"
    "noise — superseding the one-increment \\$250 criterion).")
sub(c,
    "content moved onto the F8 panels — since the second 08-28 spec as a ±\\$250-band\n"
    "share (black bar) and a strictly-below share (red floor-to-target dimension\n"
    "bracket); the one-sided criterion shares are quoted in the text and SI only.",
    "content moved onto the F8 panels — since the third spec (08-29) as a ±\\$125-band\n"
    "share (black bar) and the one-sided criterion share itself (red dimension bracket\n"
    "from the envelope floor to target + \\$125, omitted where the share is zero); the\n"
    "strictly-below read is retired from notebook and tables.")

# --- F8 code --------------------------------------------------------------------------
c = cell("atb-a6b-f8")
sub(c,
    "# 08-28 spec): a black bar spanning the target +-TOL band labeled with the stratum share\n"
    "# of supported worlds inside the band (two-sided), and a red dimension bracket from the\n"
    "# envelope floor to the target labeled with the share strictly below the target. Both\n"
    "# shares are SHAPES-based (the endpoint_feasible_share.csv population) so panel and CSV\n"
    "# cannot drift; the paper's one-sided reach-within-TOL criterion is text + SI only.",
    "# 08-28 spec, amended 08-29): a black bar spanning the target +-TOL_END band labeled\n"
    "# with the stratum share of supported worlds inside the band (two-sided), and a red\n"
    "# dimension bracket from the envelope floor to target + TOL_END labeled with the\n"
    "# ONE-SIDED criterion share (OCC(2050) <= target + $125) - the S1 share itself, so\n"
    "# panel and prose cannot drift; the bracket is omitted where that share is zero (the\n"
    "# large legacy-fleet rows). The strictly-below read is retired (08-29). Both shares\n"
    "# are SHAPES-based (the endpoint_feasible_share.csv population).")
sub(c,
    "            # Panel reads at the paired deployment (second 08-28 spec, Ethan): each label\n"
    "            # reads off the geometry it annotates. Populations identical to\n"
    "            # endpoint_feasible_share.csv (SHAPES-based, support-restricted stratum); the\n"
    "            # paper's ONE-SIDED reach-within-TOL criterion is reported in text + SI only.",
    "            # Panel reads at the paired deployment (third spec, 08-29, Ethan): each label\n"
    "            # reads off the geometry it annotates. Populations identical to\n"
    "            # endpoint_feasible_share.csv (SHAPES-based, support-restricted stratum); the\n"
    "            # red bracket carries the paper's ONE-SIDED criterion share directly.")
sub(c,
    '            share_band = float((np.abs(pred50[strat] - t50) <= TOL).mean())\n'
    '            share_below = float((pred50[strat] <= t50).mean())',
    '            share_band = float((np.abs(pred50[strat] - t50) <= TOL_END).mean())\n'
    '            share_feas = float((pred50[strat] <= t50 + TOL_END).mean())')
sub(c,
    '            ax.plot([d_aj, d_aj], [t50 - TOL, t50 + TOL], color=INK, lw=2.2, alpha=0.85,',
    '            ax.plot([d_aj, d_aj], [t50 - TOL_END, t50 + TOL_END], color=INK, lw=2.2, alpha=0.85,')
sub(c,
    '            ax.annotate(f"{100*share_band:.0f}% within\\n$250/kW", (d_aj, t50 + TOL),',
    '            ax.annotate(f"{100*share_band:.0f}% within\\n$125/kW", (d_aj, t50 + TOL_END),')
sub(c,
    '            # Red dimension bracket (left of the bar): envelope floor -> target;\n'
    '            # label = share strictly below the target.\n'
    '            x_dim = d_aj * 0.7\n'
    '            lo_d, hi_d = min(t50, floor_aj), max(t50, floor_aj)\n'
    '            ax.annotate("", (x_dim, hi_d), xytext=(x_dim, lo_d),\n'
    '                        arrowprops=dict(arrowstyle="|-|,widthA=0.22,widthB=0.22",\n'
    '                                        color=ps.ACCENT["red"], lw=1.2,\n'
    '                                        shrinkA=0, shrinkB=0))\n'
    '            ax.annotate(f"{100*share_below:.0f}%\\nbelow", (x_dim, 0.5*(lo_d + hi_d)),\n'
    '                        xytext=(-4, 0), textcoords="offset points", fontsize=7.5,\n'
    '                        color=ps.ACCENT["red"], ha="right", va="center")',
    '            # Red dimension bracket (left of the bar): envelope floor -> the upper\n'
    '            # tolerance bound (target + $125); label = the one-sided criterion share\n'
    '            # (worlds at or below the bound). Omitted where that share is zero\n'
    '            # (08-29 spec - the large legacy-fleet rows). Sub-1% shares keep one\n'
    '            # decimal so the large-advanced 0.2% stays visible.\n'
    '            if share_feas > 0:\n'
    '                x_dim = d_aj * 0.7\n'
    '                bound = t50 + TOL_END\n'
    '                lo_d, hi_d = min(bound, floor_aj), max(bound, floor_aj)\n'
    '                ax.annotate("", (x_dim, hi_d), xytext=(x_dim, lo_d),\n'
    '                            arrowprops=dict(arrowstyle="|-|,widthA=0.22,widthB=0.22",\n'
    '                                            color=ps.ACCENT["red"], lw=1.2,\n'
    '                                            shrinkA=0, shrinkB=0))\n'
    '                lbl = (f"{100*share_feas:.1f}%" if share_feas < 0.01\n'
    '                       else f"{100*share_feas:.0f}%")\n'
    '                ax.annotate(lbl + "\\nreach", (x_dim, 0.5*(lo_d + hi_d)),\n'
    '                            xytext=(-4, 0), textcoords="offset points", fontsize=7.5,\n'
    '                            color=ps.ACCENT["red"], ha="right", va="center")')

# --- F8 caption markdown --------------------------------------------------------------
c = cell("atb-a6b-f8_caption")
sub(c,
    "Two reads at the paired deployment (second 08-28 spec): the black bar spans the target ±\\$250/kW, labeled with the share of the row's support-restricted stratum falling within \\$250/kW of the target; the red dimension bracket to its left spans the lowest supported cost to the target, labeled with the share strictly below the target (both SHAPES-based — the `endpoint_feasible_share.csv` population, so panel and CSV cannot drift). The paper's one-sided feasibility criterion (reach within \\$250/kW; overshoot is success) and its shares are quoted in the text and SI, not on-panel. Where the target sits below the dashed floor (the large legacy-fleet-credited rows) the red bracket shows the shortfall and both labels read 0%.",
    "Two reads at the paired deployment (third spec, 08-29): the black bar spans the target ±\\$125/kW — the ATB rounds to the nearest \\$250/kW, so \\$125 is one rounding half-step and a cost inside the bar meets the projection at its published precision — labeled with the share of the row's support-restricted stratum inside the band; the red dimension bracket to its left spans the lowest supported cost to the upper tolerance bound (target + \\$125/kW), labeled with the share at or below that bound — the paper's one-sided feasibility criterion (overshoot is success), so the bracket label is the S1 share for that stratum (both SHAPES-based — the `endpoint_feasible_share.csv` population, so panel and CSV cannot drift; sub-1% labels keep one decimal). The bracket is omitted where the criterion share is zero (the large legacy-fleet-credited rows, where the target sits below the dashed floor). The strictly-below read of the second 08-28 spec is retired.")

# --- F9 code + caption ----------------------------------------------------------------
c = cell("atb-a6b-f9")
sub(c,
    "# OCC(2050) <= target + TOL. Ruling 08-24: the section asks whether the cost is",
    "# OCC(2050) <= target + TOL_END ($125 since 08-29: one rounding half-step of the\n"
    "# ATB's nearest-$250 reporting). Ruling 08-24: the section asks whether the cost is")
sub(c, "    feas = gap <= TOL\n", "    feas = gap <= TOL_END\n")
sub(c,
    '"share_support_twosided": round(float((MIS50[(tech, scen)] <= TOL)[sup].mean()), 4),',
    '"share_support_twosided": round(float((MIS50[(tech, scen)] <= TOL_END)[sup].mean()), 4),')
sub(c,
    'print("endpoint feasible shares, ONE-SIDED (reaches the 2050 cost: OCC(2050) <= target + "\n'
    '      "$250/kW at the paired deployment; comparison columns: two-sided endpoint band, "',
    'print("endpoint feasible shares, ONE-SIDED (reaches the 2050 cost: OCC(2050) <= target + "\n'
    '      "$125/kW at the paired deployment; comparison columns: two-sided endpoint band, "')
sub(c,
    "            if (zmin <= TOL).any() and (zmin > TOL).any():\n"
    "                ax.contour(LR_GRID, S21, zmin.T, levels=[TOL], colors=[C_SMR], linewidths=1.6)",
    "            if (zmin <= TOL_END).any() and (zmin > TOL_END).any():\n"
    "                ax.contour(LR_GRID, S21, zmin.T, levels=[TOL_END], colors=[C_SMR], linewidths=1.6)")
sub(c,
    'label=f"reaches the target within ${TOL:.0f}/kW")]',
    'label=f"reaches the target within ${TOL_END:.0f}/kW")]')

c = cell("atb-a6b-f9_caption")
sub(c,
    "The contour bounds the worlds that reach the target within \\$250/kW;",
    "The contour bounds the worlds that reach the target within \\$125/kW (08-29 criterion:\n"
    "one rounding half-step of the ATB's nearest-\\$250 reporting);")

# --- ST12 dual-convention cell --------------------------------------------------------
c = cell("atb-a6c-dualconv")
sub(c, "chk = float((np.maximum(base50 - t50, 0.0) <= TOL)[sup].mean())",
       "chk = float((np.maximum(base50 - t50, 0.0) <= TOL_END)[sup].mean())")
sub(c, "ref = float((GAP50[(tech, scen)] <= TOL)[sup].mean())",
       "ref = float((GAP50[(tech, scen)] <= TOL_END)[sup].mean())")
sub(c, "feas = np.maximum(his50 - t50, 0.0) <= TOL\n",
       "feas = np.maximum(his50 - t50, 0.0) <= TOL_END\n")

# --- F10 marginals --------------------------------------------------------------------
c = cell("atb-a6b-f10")
sub(c,
    "# basis (08-24: feasible = reaches the target, GAP50 <= TOL): for each dial value, the",
    "# basis (08-24; $125 criterion since 08-29: feasible = GAP50 <= TOL_END): for each dial value, the")
sub(c, "            feas = (GAP50[(tech, scen)] <= TOL).reshape(GRID_SHAPE)",
       "            feas = (GAP50[(tech, scen)] <= TOL_END).reshape(GRID_SHAPE)")

# --- metadata export ------------------------------------------------------------------
c = cell("atb-27-a28_meta")
sub(c,
    '"tolerance_usd_per_kw": {"primary": TOL, "ladder": TOLS},',
    '"tolerance_usd_per_kw": {"primary": TOL, "endpoint": TOL_END, "ladder": TOLS},')

nbformat.write(nb, NB)
print("patched", NB, "- endpoint criterion $125, F8 third spec, strictly-below retired")
