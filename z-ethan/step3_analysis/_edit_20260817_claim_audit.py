"""Section-4 claim-audit fixes (2026-08-17).

Edit method per the established convention (the notebook is edited in place by
id-targeted, assert-guarded string replacements; `_build_notebook.py` is STALE and
must never be run). Idempotent. Run with any python (json + stdlib only), then
re-execute the notebook headless on the playground-env kernel with drive D mounted.

What this applies (from the 2026-08-17 audit of paper_outline.md section 4):
1. cell f4ead676 (t02): the "25 runs" print string is stale at 37 cases -> dynamic.
2. cell b2c98357 (t03): the pointwise monotonicity assert covered smr100 only;
   large100 was verified monotone by hand in the audit - now asserted too.
3. cell 5375aaf6 (t09): (a) new column `S_x_2p2GW_2024B` = the marginal-build dual
   gap on one Vogtle-pair-equivalent (2.2 GW) - the artifact behind the paper's
   per-pair benchmark sentence (the PV-per-program-pair reading gives $2-3B and is
   NOT the quotable number); (b) pooled counts now also printed excluding the
   equality duplicate (which double-counts one world) and scoped to smr100.
4. new cells t16md001/t16cd001 (before the "### ITC outlay" markdown): t16 - the
   BOC 6-year rate-lock windfall over declining rate segments, previously an
   artifact-less outline number ("~13 points" is reference-case-specific; the
   family median is ~5 points).
5. cell t13md001: three disclosure clauses (rc = 0 is LP optimality at basic
   builds; tau is the model effective rate; eval_adj = 1 / exact tax cancellation).
6. cell t13cd001 (t13): exports the net-ratio identity terms
   (`capex_overshoot`, `risk_premium_factor`, `pred_net_ratio`) and asserts the
   identity against the computed ratio (audit verified it to ~1e-7).
7. new cell t13fg001 (after t13): regenerates figures/t13_instrument_comparison.png
   on the 37-case basis (the on-disk PNG was orphaned: dated 08-14, written by no
   current cell).
8. cell ebc6728a (S10): caveat 6 gains the p95 hold-is-a-lower-bound sentence;
   caveat 7 restated on the de-duplicated basis with the correct per-schedule
   large100 p95 counts (8-10 in five schedules, 2 in eia).
"""
import json
from pathlib import Path

NB = Path(__file__).resolve().parent / "step3_analysis.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
CELLS = {c["id"]: c for c in nb["cells"]}

if "S_x_2p2GW_2024B" in "".join(CELLS["5375aaf6"]["source"]):
    print("claim-audit edits already applied; nothing to do")
    raise SystemExit(0)

n = 0


def rep(cid, old, new):
    global n
    s = "".join(CELLS[cid]["source"])
    assert s.count(old) == 1, f"cell {cid}: pattern not unique/found:\n{old[:160]}"
    CELLS[cid]["source"] = s.replace(old, new).splitlines(keepends=True)
    n += 1


def md_cell(cid, src):
    return {"id": cid, "cell_type": "markdown", "metadata": {},
            "source": src.splitlines(keepends=True)}


def code_cell(cid, src):
    return {"id": cid, "cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": src.splitlines(keepends=True)}


# ---- 1. cell f4ead676 (t02 print) --------------------------------------------------
rep("f4ead676",
    'print(f"\\n{len(t02)} clearly slack (case, year) points across the 25 runs.")',
    'print(f"\\n{len(t02)} clearly slack (case, year) points across the {len(CASES)} runs.")')

# ---- 2. cell b2c98357 (t03 monotonicity assert, both families) ---------------------
rep("b2c98357",
    'print("dual is monotone p95 >= p50 >= p05 pointwise in all six schedules.")',
    'for s in SCHEDULES:\n'
    '    piv = (DUALS[(DUALS["family"] == "large") & (DUALS["schedule"] == s)]\n'
    '           .pivot_table(index="t", columns="pct", values="dual_2004_MWyr"))\n'
    '    assert ((piv["p95"] >= piv["p50"] - 1e-6) & (piv["p50"] >= piv["p05"] - 1e-6)).all(), s\n'
    'print("dual is monotone p95 >= p50 >= p05 pointwise in all six schedules, "\n'
    '      "both families.")')

# ---- 3. cell 5375aaf6 (t09) --------------------------------------------------------
rep("5375aaf6",
    "                   ccmult=None, i_min=None, i_max=None, i_headline=None,\n"
    "                   i_model_min=None, i_model_max=None, i_model_headline=None,\n"
    "                   itc_insufficient=False)",
    "                   ccmult=None, i_min=None, i_max=None, i_headline=None,\n"
    "                   i_model_min=None, i_model_max=None, i_model_headline=None,\n"
    "                   S_x_2p2GW_2024B=None, itc_insufficient=False)")

rep("5375aaf6",
    "                       i_model_headline=round(float(i_r.max()), 3),\n"
    "                       itc_insufficient=bool(i_stat.max() > 1.0))",
    "                       i_model_headline=round(float(i_r.max()), 3),\n"
    "                       # marginal-build gap on one Vogtle-pair-equivalent (2.2 GW)\n"
    "                       S_x_2p2GW_2024B=round(S * 2200.0 * TO2024 / 1e9, 1),\n"
    "                       itc_insufficient=bool(i_stat.max() > 1.0))")

rep("5375aaf6",
    "print(f\"gated (case, year) points: {len(t09)}; rate rows: \"\n"
    "      f\"{int((t09['status'] == 'rate').sum())}; statutory rate above 100%: {n_over}\")",
    "print(f\"gated (case, year) points: {len(t09)}; rate rows: \"\n"
    "      f\"{int((t09['status'] == 'rate').sum())}; statutory rate above 100%: {n_over}\")\n"
    "ne9 = t09[~t09[\"case\"].str.endswith(\"_eq\")]     # the eq copy duplicates one world\n"
    "print(f\"excluding the equality duplicate: rate rows \"\n"
    "      f\"{int((ne9['status'] == 'rate').sum())}; \"\n"
    "      f\"above 100%: {int(ne9['itc_insufficient'].sum())}\")\n"
    "s9 = ne9[ne9[\"case\"].str.startswith(\"smr100\") & (ne9[\"status\"] == \"rate\")]\n"
    "print(f\"smr100 only: rate rows {len(s9)}; \"\n"
    "      f\"above 100%: {int(s9['itc_insufficient'].sum())}\")")

# ---- 4. t16 windfall cells (inserted before the '### ITC outlay' markdown) ---------
T16_MD = """### t16 - BOC rate-lock windfall

Where the statutory rate schedule declines, a beginning-of-construction (BOC)
rate lock pays a 6-year build the spread between the locked rate and the
placed-in-service-year rate. t16 quantifies that spread over every 6-year
span of every case's rate schedule (annual, linearly interpolated between
solve years), with the declining-segment conditioning explicit: rates rise
into the late horizon in most p50 worlds, where the same lock is a shortfall,
not a windfall."""

T16_CODE = """# ---- t16: BOC 6-year rate-lock windfall over declining rate segments -----------------
wrows = []
for c in sorted(t09["case"].unique()):
    if c.endswith("_eq"):
        continue
    sub = (t09[(t09["case"] == c) & (t09["status"] == "rate")]
           .set_index("t")["i_headline"])
    if len(sub) < 2:
        continue
    yrs = list(range(int(sub.index.min()), int(sub.index.max()) + 1))
    ann = sub.reindex(yrs).interpolate(method="index")
    for y in yrs:
        if y + 6 > yrs[-1]:
            break
        w = float(ann.loc[y] - ann.loc[y + 6])
        wrows.append(dict(case=c, boc_year=y, windfall_pts=round(w * 100, 1),
                          declining=bool(w > 0)))
t16 = pd.DataFrame(wrows)
t16.to_csv(EXPORTS / "t16_boc_windfall.csv", index=False)
w50 = t16[t16["case"].str.startswith("smr100") & t16["case"].str.endswith("_p50")]
d50 = w50[w50["declining"]]["windfall_pts"]
print(f"smr100 p50, declining 6-year spans: n={len(d50)} of {len(w50)} "
      f"({w50['declining'].mean():.0%}); windfall median {d50.median():.1f} pts, "
      f"IQR {d50.quantile(0.25):.1f}-{d50.quantile(0.75):.1f}, max {d50.max():.1f}")
ref16 = t16[(t16["case"] == REF) & t16["declining"]]["windfall_pts"]
print(f"reference case {REF}: declining-span windfall median {ref16.median():.1f} pts, "
      f"max {ref16.max():.1f}")"""

IDX = {c["id"]: i for i, c in enumerate(nb["cells"])}
pos = IDX["bb201490"]           # the '### ITC outlay' markdown; insert both cells before it
nb["cells"][pos:pos] = [md_cell("t16md001", T16_MD), code_cell("t16cd001", T16_CODE)]

# ---- 5. cell t13md001 (disclosure clauses) -----------------------------------------
rep("t13md001",
    "own gap equals S_t, and a perfectly informed regulator pays the same flat\n"
    "amount. The cell verifies this from the h5 `reduced_cost` output.",
    "own gap equals S_t, and a perfectly informed regulator pays the same flat\n"
    "amount. The cell verifies this from the h5 `reduced_cost` output. (For a\n"
    "region that builds, a zero reduced cost is LP optimality itself; the\n"
    "economic reading - every builder's gap equals S_t - additionally assumes\n"
    "no other binding constraint pays rent to those builds.)")

rep("t13md001",
    "payments have different tax character. T is pre-tax revenue: a taxable grant\n"
    "returns tau x T to the government, so the grant's net cost is (1 - tau) x T.",
    "payments have different tax character. T is pre-tax revenue: a taxable grant\n"
    "returns tau x T to the government, so the grant's net cost is (1 - tau) x T\n"
    "(tau = 0.257, the model's effective corporate rate, not the 21% statutory\n"
    "rate; it enters both instruments).")

rep("t13md001",
    "net ratio = overshoot / ((1 - penalty) x risk x eval_adj) holds: the",
    "net ratio = overshoot / ((1 - penalty) x risk x eval_adj) holds\n"
    "(eval_adj = 1 in every case-year here; the tax terms cancel exactly,\n"
    "k x claw = 1 - tau x PV_dep): the")

# ---- 6. cell t13cd001 (identity terms exported + asserted) -------------------------
rep("t13cd001",
    "    nbse, K, CCM = natfin(c)\n"
    "    cc, fm = COSTCAP[c], FINMULT[c]",
    "    nbse, K, CCM = natfin(c)\n"
    "    cc, fm = COSTCAP[c], FINMULT[c]\n"
    "    # the technology hurdle premium inside fin_mult_noITC (same arithmetic as natfin)\n"
    "    g46 = fin_tech(c)\n"
    "    g46 = g46[g46[\"i\"] == IN_NAME[tech]].set_index(\"t\").reindex(YEARS).ffill().bfill()\n"
    "    ev46 = float(g46[\"eval_period\"].iloc[0])\n"
    "    rk46 = pd.Series(1.0 + g46[\"finance_diff_real\"].to_numpy(float)\n"
    "                     * ((1 - (1 / D_REAL) ** ev46) / (D_REAL - 1.0)), index=YEARS)")

rep("t13cd001",
    '    pv = dict(T=0.0, T_net=0.0, B=0.0, N=0.0, N_real=0.0)',
    '    pv = dict(T=0.0, T_net=0.0, B=0.0, N=0.0, N_real=0.0, OV=0.0, RK=0.0, PRED=0.0)')

rep("t13cd001",
    '        pv["N_real"] += B_ann * claw * pv_w      # statutory timing: cash at placed-in-service',
    '        pv["N_real"] += B_ann * claw * pv_w      # statutory timing: cash at placed-in-service\n'
    '        # net-ratio identity terms, T_net-PV-weighted (audit 2026-08-17)\n'
    '        ov_t = float((fmb * blt).sum() / (fmb.min() * float(blt.sum())))\n'
    '        w_t = S * float(blt.sum()) * (1.0 - tau) * pv_w\n'
    '        pv["OV"] += ov_t * w_t\n'
    '        pv["RK"] += float(rk46.loc[t]) * w_t\n'
    '        pv["PRED"] += ov_t / ((1.0 - PEN) * float(rk46.loc[t])) * w_t')

rep("t13cd001",
    '    v = {k_: pv[k_] * TO2024 / 1e9 for k_ in pv}',
    '    v = {k_: pv[k_] * TO2024 / 1e9 for k_ in ("T", "T_net", "B", "N", "N_real")}\n'
    '    ov_w = pv["OV"] / pv["T_net"]\n'
    '    rk_w = pv["RK"] / pv["T_net"]\n'
    '    pred = pv["PRED"] / pv["T_net"]\n'
    '    # identity: net ratio = overshoot / ((1 - penalty) x risk); eval_adj = 1.\n'
    '    # tolerance 5e-3: B_ann uses the 3-dp-rounded i_headline from t09, so the\n'
    '    # identity holds to rounding, not to float precision (exact when unrounded).\n'
    '    assert abs(pred - pv["N_real"] / pv["T_net"]) < 5e-3, (c, pred)')

rep("t13cd001",
    "                       net_loss_ratio=round(v[\"N\"] / v[\"T_net\"], 2),\n"
    "                       net_loss_ratio_realistic=round(v[\"N_real\"] / v[\"T_net\"], 2),\n"
    "                       gross_scoring_ratio=round(v[\"B\"] / v[\"T\"], 2)))",
    "                       net_loss_ratio=round(v[\"N\"] / v[\"T_net\"], 2),\n"
    "                       net_loss_ratio_realistic=round(v[\"N_real\"] / v[\"T_net\"], 2),\n"
    "                       gross_scoring_ratio=round(v[\"B\"] / v[\"T\"], 2),\n"
    "                       capex_overshoot=round(ov_w, 4),\n"
    "                       risk_premium_factor=round(rk_w, 4),\n"
    "                       pred_net_ratio=round(pred, 4)))")

rep("t13cd001",
    'print("reduced-cost check: no building (r, t) has a nonzero reduced cost, in any case.")',
    'print("reduced-cost check: no building (r, t) has a nonzero reduced cost, in any "\n'
    '      "case (LP optimality at basic builds; see the markdown note above).")')

# ---- 7. t13 figure cell (inserted right after t13cd001) ----------------------------
T13_FIG = """# ---- t13 figure: instrument comparison, regenerated on the 37-case basis --------------
fcmp = t13[~t13["case"].str.endswith("_eq")].set_index("case")
fig, ax = plt.subplots(figsize=(11, 4.2))
x = np.arange(len(fcmp))
ax.axhline(1.0, lw=0.8, color=MUTED, zorder=1)
ax.scatter(x, fcmp["gross_scoring_ratio"], marker="s", s=22, color=COL["large"],
           label="gross scoring B / T")
ax.scatter(x, fcmp["net_loss_ratio_realistic"], marker="o", s=26, color=COL["smr"],
           label="net of tax, statutory timing")
ax.scatter(x, fcmp["net_loss_ratio"], marker="^", s=22, color=FAINT,
           label="net of tax, QPE counterfactual")
ax.set_xticks(x)
ax.set_xticklabels(fcmp.index, rotation=90, fontsize=6.5)
ax.set_ylabel("credit cost / flat-grant cost")
ax.set_title("Flat grant vs ITC: gross budget scoring reverses the net-of-tax ranking")
ax.legend(fontsize=8, ncol=3)
fig.tight_layout()
savefig(fig, "t13_instrument_comparison.png")
plt.show()"""

IDX = {c["id"]: i for i, c in enumerate(nb["cells"])}
nb["cells"][IDX["t13cd001"] + 1: IDX["t13cd001"] + 1] = [code_cell("t13fg001", T13_FIG)]

# ---- 8. cell ebc6728a (S10 caveats 6 + 7) ------------------------------------------
rep("ebc6728a",
    "   conventions (zero after 2050, and the 2050 value held through the window);\n"
    "   read only conclusions that hold across the band.",
    "   conventions (zero after 2050, and the 2050 value held through the window);\n"
    "   read only conclusions that hold across the band. In the p95 worlds the\n"
    "   dual is still rising at 2050, so there the hold variant is a lower bound,\n"
    "   not an upper bracket.")

rep("ebc6728a",
    "   expensive draws (large100 p95 end/peak 0.84–0.95). The required statutory\n"
    "   ITC exceeds 100% in 82 of 334 rate case-years across the 37 runs,\n"
    "   concentrated in the large100 p95 worlds (8–10 case-years per schedule):\n"
    "   an ITC alone cannot deliver those worlds.",
    "   expensive draws (large100 p95 end/peak 0.84–0.95). The required statutory\n"
    "   ITC exceeds 100% in 82 of 329 unique rate case-years (334 rows counting\n"
    "   the equality duplicate, which adds none), concentrated in the large100\n"
    "   p95 worlds — 8–10 case-years per schedule except eia's 2 (it prices only\n"
    "   6 of 12 mandated years); smr100 contributes 20, all at p95: an ITC alone\n"
    "   cannot deliver those worlds.")

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"applied {n} edits + 3 inserted cells (t16md001, t16cd001, t13fg001) -> {NB.name}")
