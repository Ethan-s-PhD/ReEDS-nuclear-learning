# -*- coding: utf-8 -*-
"""08-28 (Ethan): Fig 1 becomes the two F8 planes STACKED (a = large over b = smr);
the F9 endpoint maps leave the composition (diagnostic — the s-axis carried little).
F8 panels gain: dashed P0/P100 envelope (lowest/highest supported world per deployment)
and, at the paired deployment, a bracket from the ATB target to the envelope floor
labeled with the stratum's share of support-restricted worlds reaching the target
(the exact endpoint_feasible_share.csv numbers, recomputed in-cell from SHAPES).

Patches atb_parameter_space.ipynb in place (cells atb-a6b-hdr / -f8_caption / -f8 /
-f9_caption / -f9). Companion composition change: paper_figures/_build_notebooks.py.
"""
import nbformat

NB = "atb_parameter_space.ipynb"

F8_SOURCE = r'''# F8 (Fig 1a/b, augmented 08-28) - the 2050 cost-deployment plane: the 2050 OCC each amount of
# cumulative building can buy, across the support-restricted grid worlds, with the ATB
# (paired deployment, 2050 cost) point overlaid. One figure per technology; rows = the
# experience-base strata (matching F3/F6); the quantile fan is over all grid worlds in the
# stratum with LR restricted to the MC sampled support (uniform grid weights over
# LR x s x u3 x m x rho, the Part-2 grid — no dial held fixed). The shape quantiles are
# computed once per stratum and scaled by each scenario's pinned anchor (quantiles commute
# with the positive per-scenario BOAK scaling).
# 08-28 (Ethan): Fig 1 = these two figures STACKED (a = large over b = smr); the endpoint
# maps (F9) leave the composition. Added per panel: dashed P0/P100 envelope (lowest and
# highest supported world at each deployment) and, at the paired deployment, a bracket
# from the ATB target to the envelope floor labeled with the stratum's share of
# support-restricted worlds that reach the target (one-sided, within TOL) - the exact
# Part-1 numbers behind endpoint_feasible_share.csv, recomputed from SHAPES in-cell so
# the on-panel labels cannot drift from the exported CSV.
D_PLANE_GW = np.logspace(0.0, np.log10(3000.0), 28)          # 1 -> 3,000 GW by 2050

for tech in TECH:
    sup2 = (LR2 >= TECH[tech]["lr_lo"]) & (LR2 <= TECH[tech]["lr_hi"])
    sup1 = (P["lr"] >= TECH[tech]["lr_lo"]) & (P["lr"] <= TECH[tech]["lr_hi"])
    fig, axes = plt.subplots(2, 3, figsize=(13, 7.2), sharex=True)
    for r, conv in enumerate(CONV_GRID):
        combos = [(rho, m) for (rho, cv, m) in DISC_COMBOS if cv == conv]
        lr = np.concatenate([LR2[sup2]] * len(combos))
        s = np.concatenate([S2[sup2]] * len(combos))
        u = np.concatenate([U2[sup2]] * len(combos))
        m = np.concatenate([np.full(int(sup2.sum()), mm) for _, mm in combos])
        rho = np.concatenate([np.full(int(sup2.sum()), rr) for rr, _ in combos])
        q = np.empty((len(D_PLANE_GW), 5))
        env = np.empty((len(D_PLANE_GW), 2))     # P0/P100: lowest/highest supported world
        for k, d in enumerate(D_PLANE_GW):
            sh = shape_2050(tech, lr, s, u, m, conv, rho, d / TECH[tech]["unit_gw"])
            q[k] = np.quantile(sh, [0.05, 0.25, 0.50, 0.75, 0.95])
            env[k] = sh.min(), sh.max()
        for c, scen in enumerate(SCEN_ORDER):
            ax = axes[r, c]
            occ_q = q * BOAK_PIN[tech][scen]
            occ_env = env * BOAK_PIN[tech][scen]
            col = SCEN_COLOR[tech][scen]
            ax.fill_between(D_PLANE_GW, occ_q[:, 0], occ_q[:, 4], color=col, alpha=0.14,
                            lw=0, label="P5-P95 of worlds")
            ax.fill_between(D_PLANE_GW, occ_q[:, 1], occ_q[:, 3], color=col, alpha=0.30,
                            lw=0, label="P25-P75")
            ax.plot(D_PLANE_GW, occ_q[:, 2], color=col, lw=2, label="median world")
            ax.plot(D_PLANE_GW, occ_env[:, 0], color=col, lw=1.0, ls="--",
                    label="lowest / highest\nsupported world")
            ax.plot(D_PLANE_GW, occ_env[:, 1], color=col, lw=1.0, ls="--")
            t50, d_aj = TARGET[tech][scen][-1], AJ_GW_ENT50[scen]   # thru-2049 scoring basis
            ax.axhline(t50, color=INK, lw=0.8, ls=":", alpha=0.6)
            ax.axvline(d_aj, color=INK, lw=0.8, ls=":", alpha=0.6)
            ax.plot([d_aj], [t50], "o", color=INK, ms=6, zorder=5,
                    label="ATB 2050 target at\nits paired deployment")
            # Stratum share of support-restricted worlds reaching the target at the paired
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
            ax.annotate(f"{100*share:.0f}% of supported\nworlds reach it",
                        (d_aj, max(t50, floor_aj)), xytext=(6, 4),
                        textcoords="offset points", fontsize=7.5, color=INK, va="bottom")
            ax.set_xscale("log")
            ax.set_xlim(1.0, 3000.0)
            if r == 0:
                ax.set_title(f"{scen} (2050 target ${t50:,.0f}/kW)", fontsize=10)
            if c == 0:
                ax.set_ylabel(("tiny-base" if conv == 0 else "full-stock")
                              + "\n2050 occ (2022$/kW)")
            if r == 1:
                ax.set_xlabel("post-2030 build completed through 2049 (GW; prices 2050)")
    # Paper Fig 1 letters baked at source (house rule): "a" (large) / "b" (smr); the
    # composed Fig 1 stacks a over b since 08-28 (the F9 maps left the composition).
    ps.panel_letter(axes[0, 0], "a" if tech == "large" else "b")
    axes[0, 0].legend(fontsize=7.5, loc="lower left")
    fig.tight_layout()
    fig.suptitle(TECH_LABEL[tech], color=TECH_COLOR[tech], x=0.01, ha="left", y=1.03)
    ps.savefig(fig, FIGURES / f"atb_cost_deployment_plane_{tech}.png")
    plt.show()'''

HDR_SOURCE = """## A6b — The 2050-endpoint figures (Fig 1 = F8 stacked, 08-28; endpoint basis ratified 08-24)

Ethan's 08-21 direction for S1: the section claims matching the ATB **2050 cost and the
builds it requires** only — the 2030 anchor convention guarantees the *path* cannot match,
so the trajectory criterion overstates the question. 08-24 rulings: the
endpoint criterion is **one-sided** — a world is feasible when it *reaches* the ATB 2050
cost (OCC(2050) ≤ target + \\$250/kW at the paired deployment). The earlier two-sided band
counted fast-learning worlds as infeasible by overshoot, which inverted the apparent LR
ordering across scenarios; the two-sided shares stay as a comparison column in
`endpoint_feasible_share.csv`. **08-28 (Ethan): the composed paper Fig 1 is F8 alone,
stacked a (large) over b (smr).** The F9 maps left the composition and are diagnostics —
their s-axis carried little (the reach contour is near-vertical), and the share-of-support
content moved onto the F8 panels as bracket labels. F10 remains an SI candidate; F6/F7
stay as Part-2 exhibits; T5 (`min_lr_at_aj_deployment.csv`) is the endpoint-basis
minimum-LR table (its exact spans are homed to the T5/SF captions, not main prose).

**Interpretation guard for every endpoint figure:** each scenario is scored at its own
paired Abou-Jaoude deployment (conservative 12 GW, moderate 33 GW, advanced 199 GW), so
LR orderings across scenarios reflect the ATB's pairing structure — the cheap scenarios
come bundled with big programs — not the targets alone."""

F8_CAPTION = """**F8 (Fig 1a/b, augmented + stacked 08-28) — the 2050 cost–deployment plane** (`atb_cost_deployment_plane_{tech}.png`, one figure per technology; baked letters a = large, b = smr; the composed Fig 1 stacks a over b). For each amount of post-2030 build completed through 2049 (x, log scale — the stock that
prices 2050): the 2050 OCC the support-restricted grid worlds deliver (P5–P95 and P25–P75 fans, median line; dashed lines = the lowest and highest supported world at each deployment; LR restricted to the MC sampled support, uniform grid weights over s, u, m, ρ — no dial held fixed), tiny-base vs full-stock rows. The black dot is the ATB 2050 target at its paired Abou-Jaoude deployment on the same
through-2049 basis (dotted crosshairs; the quoted by-2050 program totals remain
12/33/199 GW). The vertical bracket at the paired deployment spans the target to the lowest supported cost there; its label gives the share of the row's support-restricted stratum that reaches the target (one-sided, within \\$250/kW — the exact `endpoint_feasible_share.csv` numbers, recomputed from SHAPES in-cell). Where the target sits below the dashed floor (the large full-stock rows) the bracket shows the shortfall and the label reads 0%."""


def main():
    nb = nbformat.read(NB, as_version=4)
    cells = {c.get("id"): c for c in nb.cells}

    cells["atb-a6b-f8"]["source"] = F8_SOURCE
    cells["atb-a6b-hdr"]["source"] = HDR_SOURCE
    cells["atb-a6b-f8_caption"]["source"] = F8_CAPTION

    f9 = cells["atb-a6b-f9"]
    src = f9["source"]
    assert "# F9 (Fig 1c/d, ratified 2026-08-24)" in src
    src = src.replace(
        "# F9 (Fig 1c/d, ratified 2026-08-24)",
        "# F9 (diagnostic since 08-28; was Fig 1c/d 08-24 to 08-28)")
    old_letters = (
        '    # Paper Fig 1 letters baked at source (house rule): the cost-deployment plane (F8)\n'
        '    # leads as "a" (large) / "b" (smr); these maps carry "c"/"d".\n'
        '    ps.panel_letter(axes[0, 0], "c" if tech == "large" else "d")\n')
    assert old_letters in src, "F9 letter block not found"
    src = src.replace(old_letters, (
        '    # 08-28: these maps left the composed Fig 1 (panel letters removed); the CSV\n'
        '    # export above stays load-bearing for the S1 prose shares and the F8 labels.\n'))
    f9["source"] = src

    cap9 = cells["atb-a6b-f9_caption"]["source"]
    assert cap9.startswith("**F9 (Fig 1c/d)")
    cells["atb-a6b-f9_caption"]["source"] = cap9.replace(
        "**F9 (Fig 1c/d) — endpoint feasibility maps, one-sided** "
        "(`atb_endpoint_feasible_maps_{tech}.png`; baked letters c = large, d = smr).",
        "**F9 (diagnostic since 08-28; formerly Fig 1c/d) — endpoint feasibility maps, "
        "one-sided** (`atb_endpoint_feasible_maps_{tech}.png`; panel letters removed 08-28 "
        "when the maps left the composed Fig 1).", 1)

    nbformat.write(nb, NB)
    print("patched:", NB)


if __name__ == "__main__":
    main()
