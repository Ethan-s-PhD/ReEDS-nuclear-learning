# -*- coding: utf-8 -*-
"""Second 08-28 Fig 1 spec (Ethan, after the label-vs-fan percentile question):
the on-panel labels must read off the geometry they annotate. Per panel, at the
paired deployment: (1) the black bar now spans the target +-$250/kW band, labeled
with the stratum share of supported worlds WITHIN $250/kW of the target (two-sided);
(2) a red dimension bracket to its left spans the envelope floor to the target,
labeled with the share STRICTLY BELOW the target. The paper's one-sided
reach-within-$250 criterion and its shares move to text + SI only.

Patches atb_parameter_space.ipynb in place (cells atb-a6b-f8 / -f8_caption / -hdr).
Companion caption change: paper_figures/_build_notebooks.py.
"""
import nbformat

NB = "atb_parameter_space.ipynb"

OLD_BLOCK = '''            # Stratum share of support-restricted worlds reaching the target at the paired
            # deployment (one-sided, within TOL): identical formula and population to
            # endpoint_feasible_share.csv's share_support_tiny/_full columns.
            pred50 = BOAK_PIN[tech][scen] * SHAPES[(tech, scen)][:, -1].astype(np.float64)
            strat = sup1 & (P["conv_full"] == conv)
            share = float((pred50[strat] - t50 <= TOL).mean())
            # Envelope floor exactly at the paired deployment (not interpolated).
            sh_aj = shape_2050(tech, lr, s, u, m, conv, rho, d_aj / TECH[tech]["unit_gw"])
            floor_aj = float(sh_aj.min()) * BOAK_PIN[tech][scen]
            ax.plot([d_aj, d_aj], [min(t50, floor_aj), max(t50, floor_aj)],
                    color=INK, lw=2.2, alpha=0.8, solid_capstyle="butt", zorder=4)
            ax.annotate(f"{100*share:.0f}% of supported\\nworlds reach it",
                        (d_aj, max(t50, floor_aj)), xytext=(6, 4),
                        textcoords="offset points", fontsize=7.5, color=INK, va="bottom")'''

NEW_BLOCK = '''            # Panel reads at the paired deployment (second 08-28 spec, Ethan): each label
            # reads off the geometry it annotates. Populations identical to
            # endpoint_feasible_share.csv (SHAPES-based, support-restricted stratum); the
            # paper's ONE-SIDED reach-within-TOL criterion is reported in text + SI only.
            pred50 = BOAK_PIN[tech][scen] * SHAPES[(tech, scen)][:, -1].astype(np.float64)
            strat = sup1 & (P["conv_full"] == conv)
            share_band = float((np.abs(pred50[strat] - t50) <= TOL).mean())
            share_below = float((pred50[strat] <= t50).mean())
            # Envelope floor exactly at the paired deployment (not interpolated).
            sh_aj = shape_2050(tech, lr, s, u, m, conv, rho, d_aj / TECH[tech]["unit_gw"])
            floor_aj = float(sh_aj.min()) * BOAK_PIN[tech][scen]
            # Black bar: the +-TOL band around the target; label = share inside the band.
            ax.plot([d_aj, d_aj], [t50 - TOL, t50 + TOL], color=INK, lw=2.2, alpha=0.85,
                    solid_capstyle="butt", zorder=4)
            ax.annotate(f"{100*share_band:.0f}% within\\n$250/kW", (d_aj, t50 + TOL),
                        xytext=(5, 3), textcoords="offset points", fontsize=7.5,
                        color=INK, va="bottom")
            # Red dimension bracket (left of the bar): envelope floor -> target;
            # label = share strictly below the target.
            x_dim = d_aj * 0.7
            lo_d, hi_d = min(t50, floor_aj), max(t50, floor_aj)
            ax.annotate("", (x_dim, hi_d), xytext=(x_dim, lo_d),
                        arrowprops=dict(arrowstyle="|-|,widthA=0.22,widthB=0.22",
                                        color=ps.ACCENT["red"], lw=1.2,
                                        shrinkA=0, shrinkB=0))
            ax.annotate(f"{100*share_below:.0f}%\\nbelow", (x_dim, 0.5*(lo_d + hi_d)),
                        xytext=(-4, 0), textcoords="offset points", fontsize=7.5,
                        color=ps.ACCENT["red"], ha="right", va="center")'''

OLD_HEADER = '''# 08-28 (Ethan): Fig 1 = these two figures STACKED (a = large over b = smr); the endpoint
# maps (F9) leave the composition. Added per panel: dashed P0/P100 envelope (lowest and
# highest supported world at each deployment) and, at the paired deployment, a bracket
# from the ATB target to the envelope floor labeled with the stratum's share of
# support-restricted worlds that reach the target (one-sided, within TOL) - the exact
# Part-1 numbers behind endpoint_feasible_share.csv, recomputed from SHAPES in-cell so
# the on-panel labels cannot drift from the exported CSV.'''

NEW_HEADER = '''# 08-28 (Ethan): Fig 1 = these two figures STACKED (a = large over b = smr); the endpoint
# maps (F9) leave the composition. Per panel: dashed P0/P100 envelope (lowest and highest
# supported world at each deployment) plus two reads at the paired deployment (second
# 08-28 spec): a black bar spanning the target +-TOL band labeled with the stratum share
# of supported worlds inside the band (two-sided), and a red dimension bracket from the
# envelope floor to the target labeled with the share strictly below the target. Both
# shares are SHAPES-based (the endpoint_feasible_share.csv population) so panel and CSV
# cannot drift; the paper's one-sided reach-within-TOL criterion is text + SI only.'''

OLD_CAP = """The vertical bracket at the paired deployment spans the target to the lowest supported cost there; its label gives the share of the row's support-restricted stratum that reaches the target (one-sided, within \\$250/kW — the exact `endpoint_feasible_share.csv` numbers, recomputed from SHAPES in-cell). Where the target sits below the dashed floor (the large full-stock rows) the bracket shows the shortfall and the label reads 0%."""

NEW_CAP = """Two reads at the paired deployment (second 08-28 spec): the black bar spans the target ±\\$250/kW, labeled with the share of the row's support-restricted stratum falling within \\$250/kW of the target; the red dimension bracket to its left spans the lowest supported cost to the target, labeled with the share strictly below the target (both SHAPES-based — the `endpoint_feasible_share.csv` population, so panel and CSV cannot drift). The paper's one-sided feasibility criterion (reach within \\$250/kW; overshoot is success) and its shares are quoted in the text and SI, not on-panel. Where the target sits below the dashed floor (the large full-stock rows) the red bracket shows the shortfall and both labels read 0%."""

OLD_HDR_SENT = "and the share-of-support\ncontent moved onto the F8 panels as bracket labels."
NEW_HDR_SENT = ("and the share-of-support\ncontent moved onto the F8 panels — since the second 08-28 spec as a ±\\$250-band\n"
                "share (black bar) and a strictly-below share (red floor-to-target dimension\n"
                "bracket); the one-sided criterion shares are quoted in the text and SI only.")


def main():
    nb = nbformat.read(NB, as_version=4)
    cells = {c.get("id"): c for c in nb.cells}

    f8 = cells["atb-a6b-f8"]
    assert OLD_BLOCK in f8["source"], "F8 annotation block not found"
    assert OLD_HEADER in f8["source"], "F8 header comment not found"
    f8["source"] = f8["source"].replace(OLD_BLOCK, NEW_BLOCK).replace(OLD_HEADER, NEW_HEADER)

    cap = cells["atb-a6b-f8_caption"]
    assert OLD_CAP in cap["source"], "F8 caption sentence not found"
    cap["source"] = cap["source"].replace(OLD_CAP, NEW_CAP)

    hdr = cells["atb-a6b-hdr"]
    assert OLD_HDR_SENT in hdr["source"], "A6b hdr sentence not found"
    hdr["source"] = hdr["source"].replace(OLD_HDR_SENT, NEW_HDR_SENT)

    nbformat.write(nb, NB)
    print("patched:", NB)


if __name__ == "__main__":
    main()
