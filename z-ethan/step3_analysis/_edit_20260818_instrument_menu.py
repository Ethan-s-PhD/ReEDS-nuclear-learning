"""Instrument-menu reframing (2026-08-18).

Edit method per the established convention (the notebook is edited in place by
id-targeted, assert-guarded string replacements; `_build_notebook.py` is STALE and
must never be run). Idempotent. Run with any python (json + stdlib only), then
re-execute the notebook headless on the playground-env kernel with drive D mounted.

What this applies (decisions D1-D8 of 2026-08-18, after the legal consultation;
supersedes the 2026-08-14 statutory-timing lock):
1. cell 0c9c4e73 (S8 convention md): i_model is the headline rate; the credit
   convention is stated mechanism-agnostically (progress payment during
   construction, or a placed-in-service claim on the interest-inclusive Section
   263A basis - the literal reading of reeds/financials.py:683); timing is
   PV-neutral (ccmult accrues at 8.0% nominal vs 7.99% ledger WACC); the
   placed-in-service OCC-only conversion (x ccmult) stays as the i_pis_* columns.
2. cell 5375aaf6 (t09): statutory columns i_min/i_max/i_headline renamed
   i_pis_min/i_pis_max/i_pis_headline; i_model_* names UNCHANGED (itc_feedback
   asserts on i_model_headline); itc_insufficient recomputed on the model basis
   (5 of 329 vs 82 on the pis basis); pis_insufficient companion added.
3. cells 0f97e237 (f13) and t16cd001 (t16): re-pointed at i_model_headline.
4. cells bb201490 (md) + 4d0b4dcc (t10/t12): B_t = i_model x ccmult x base -
   the face value accrued to commissioning at interest_rate_nom; algebraically
   the old statutory B_t (asserted); no separate "QPE counterfactual" outlay.
5. cells t13md001/t13cd001/t13fg001 (t13): symmetric scoring - every
   commissioning-date dollar is valued through ReEDS's financing machinery, so
   the risk/eval leverage cancels between grant and credit; new floor column
   PV_floor = (1-tau)T/(risk x eval); identity net ratio vs floor =
   overshoot/(1-penalty) (asserted); commitment-bound columns from t11's C_b.
6. cells t14md001/t14cd001 (t14): rate per geography on the model convention
   (ccmult moved from the rate into the accrued cost weight; federal==t10
   assert survives).
7. NEW cells t17md001/t17cd001 (after t11): the mandate restated per vintage
   (capacity-standard reading) with the cut/hold bracket; the cut variant
   reproduces the t08 PV exactly (asserted); fleet-rent column for large100.
8. NEW cells t18md001/t18cd001 (after t14): the subsidy instrument menu -
   net PV cost of each instrument as a multiple of the floor + f16 figure.
9. NEW cells t19md001/t19cd001: the commitment ITC schedule (C_b through the
   same inversion; flatter, gaming-resistant under foresight, underpays under
   myopia).
10. cells ff3cf5d2 (S8 header) and ebc6728a (S10 caveats) restated.
"""
import json
from pathlib import Path

NB = Path(__file__).resolve().parent / "step3_analysis.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
CELLS = {c["id"]: c for c in nb["cells"]}

if "i_pis_headline" in "".join(CELLS["5375aaf6"]["source"]):
    print("instrument-menu edits already applied; nothing to do")
    raise SystemExit(0)

n = 0


def rep(cid, old, new):
    global n
    s = "".join(CELLS[cid]["source"])
    assert s.count(old) == 1, f"cell {cid}: pattern not unique/found:\n{old[:160]}"
    CELLS[cid]["source"] = s.replace(old, new).splitlines(keepends=True)
    n += 1


def put(cid, sentinel, src):
    """Full-source replacement, guarded by a must-exist sentinel in the old source."""
    global n
    s = "".join(CELLS[cid]["source"])
    assert sentinel in s, f"cell {cid}: sentinel missing:\n{sentinel[:160]}"
    CELLS[cid]["source"] = src.splitlines(keepends=True)
    n += 1


def md_cell(cid, src):
    return {"id": cid, "cell_type": "markdown", "metadata": {},
            "source": src.splitlines(keepends=True)}


def code_cell(cid, src):
    return {"id": cid, "cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": src.splitlines(keepends=True)}


# ---- 1. cell ff3cf5d2 (S8 header md) ------------------------------------------------
put("ff3cf5d2", "The section makes two different fiscal quantities.", """\
## S8 — Rental transfer, ITC translation, and the instrument menu

This section follows the procedure in `ITC calculation procedure.md` (this
folder). The solve is sequential. Each year's LP prices its own builds fully.
Because of this, the ITC translation does not discount across years.

The compliance-market reading of the mandate is a **capacity standard with
tradable capacity credits**: the constraint is written on MW standing, and
the dual is the capacity-credit clearing price. (An RPS/REC is the per-MWh
cousin, not the analog.)

The section builds three fiscal exhibits. Their names stay separate:

- **Rental transfer** R_t = dual(t) x program capacity(t): the by-year bill
  of the capacity standard. Its PV discounts each solve year over its forward
  gap (years to the next solve year; the terminal 2050 gap is 1). t17
  restates the same bill per vintage to remove the 2050 truncation.
- **ITC outlay** B_t = i_model(t) x ccmult(t) x capex base of all builds in
  year t: the credit's face value accrued to commissioning. It appears after
  the rate calculation below.
- **The instrument menu** (t18): every instrument's net-of-tax PV cost as a
  multiple of the minimum-cost floor, with the commitment bound below the
  floor and the commitment ITC (t19) as its rate schedule.

The rental transfer pays inframarginal capacity as well as the marginal unit.
That is a property of uniform instruments, not a bug.

*Figure note (f12): the rental transfer R_t = dual × mandated capacity — panel a: R_t fans per schedule (smr100 solid with p05–p95 band, large100 dashed); panel b: PV of R_t over 2026–2050, per case.*""")

# ---- 2. cell 0c9c4e73 (convention statement) ----------------------------------------
put("0c9c4e73", "The statutory rate applies two corrections to m:", """\
### ITC translation for a sequential run

The translation follows `ITC calculation procedure.md`. Convention revised
2026-08-18 (supersedes the 2026-08-14 statutory-timing lock): the headline is
the model-convention rate i_model, and every instrument in this section is
priced inside ReEDS's own financing arithmetic.

The logic: each yearly LP is the full decision problem for its builds. The raw
dual of the floor constraint is the capitalized gap of the marginal build in
that solve. Thus the subsidy for a build in year t is:

S_t = raw dual(t) / cost_scale = converted dual(t) x pvf_onm(t)

S_t is in 2004 dollars per MW. It contains capital cost, fixed O&M, and
variable costs, minus the market value of the build. No discounting across
years applies, because the year-t solve prices the build fully.

A year enters the ITC schedule only if three conditions hold: the dual is
positive, the mandate increases in that year, and the model builds new
mandated capacity in that year (`cap_new_ann` > 0). Slack years get a zero
required ITC and stay in the table as results.

The rate calculation inverts the ReEDS financing arithmetic
(`reeds/financials.py`, lines 683-694). fin_mult is a linear function of the
monetized fraction m. The per-region solution is:

m_t(r) = S_t / (cost_cap(t) x fin_mult_noITC(r, t)) x k(t)

with k(t) = (1 - tax x PV_dep) / (1 - tax x PV_dep / 2). k is below 1: one
dollar of credit gives more than one dollar of support, because of the tax
grossup, less the half-basis depreciation reduction.

The headline rate applies one correction to m:

i_model(r) = m_t(r) / (1 - itc_tax_equity_penalty)

The penalty (0.1, from the OBBBA incentives input) covers the monetization
haircut.

The credit convention, stated mechanism-agnostically: in the fin_mult formula
the credit fraction and the half-basis clawback both apply to the invested
basis OCC x ccmult, so a credit dollar carries construction-period carrying
cost. At least two real designs deliver exactly this value to the developer:
(i) a progress payment during construction (the old Section 46 QPE design),
and (ii) a placed-in-service claim on the interest-inclusive Section 263A
basis - the literal reading of the formula. Payment timing is PV-neutral
here: ccmult accrues at interest_rate_nom = 8.0% nominal, and the ledger's
after-tax nominal WACC is 7.99%, so the two mechanisms also cost the
government the same present value. The convention does not assume how the
credit is paid; it fixes what a credit dollar is worth.

Conversion for readers: a placed-in-service credit written on an
overnight-cost-only basis must be ccmult(t) times larger; the table carries
that companion as the i_pis_* columns. Under Section 263A(f), capitalized
construction interest (debt interest actually paid) enters the eligible
basis, so the true statutory rate for a given owner lies between i_model and
i_model x ccmult. That placement is a legal fact about the owner, not a
modeling choice; readers convert with the exported ccmult column.

The run does not identify the marginal region (result P7). The table reports
the rate range over the regions that build. The headline rate is the maximum
of the range. The maximum is enough for the last mandated MW. If the required
rate is above 100%, an ITC alone cannot supply S_t; an operating subsidy must
supply the remainder. The table flags those years.

The 48E band in the figure is 30% (base) to 50% (base plus bonuses); rates on
different conventions are compared with law only after the reader's own basis
conversion.

*Figure note (f13): required ITC rate (model convention) per solve year, smr100.*""")

# ---- 3. cell 5375aaf6 (t09) ---------------------------------------------------------
rep("5375aaf6",
    """        row = dict(case=c, t=t, status=status, S_t_2004_per_MW=None, n_build_regions=0,
                   ccmult=None, i_min=None, i_max=None, i_headline=None,
                   i_model_min=None, i_model_max=None, i_model_headline=None,
                   S_x_2p2GW_2024B=None, itc_insufficient=False)""",
    """        row = dict(case=c, t=t, status=status, S_t_2004_per_MW=None, n_build_regions=0,
                   ccmult=None, i_model_min=None, i_model_max=None,
                   i_model_headline=None, i_pis_min=None, i_pis_max=None,
                   i_pis_headline=None, S_x_2p2GW_2024B=None,
                   itc_insufficient=False, pis_insufficient=False)""")
rep("5375aaf6",
    """            i_r = m_r / (1.0 - PEN)                # QPE / model convention, per region
            ccm_t = float(CCM.loc[t])
            i_stat = i_r * ccm_t                   # statutory: credit cash at placed-in-service
            row.update(S_t_2004_per_MW=round(S), n_build_regions=len(i_r),
                       ccmult=round(ccm_t, 4),
                       i_min=round(float(i_stat.min()), 3), i_max=round(float(i_stat.max()), 3),
                       i_headline=round(float(i_stat.max()), 3),
                       i_model_min=round(float(i_r.min()), 3),
                       i_model_max=round(float(i_r.max()), 3),
                       i_model_headline=round(float(i_r.max()), 3),
                       # marginal-build gap on one Vogtle-pair-equivalent (2.2 GW)
                       S_x_2p2GW_2024B=round(S * 2200.0 * TO2024 / 1e9, 1),
                       itc_insufficient=bool(i_stat.max() > 1.0))""",
    """            i_r = m_r / (1.0 - PEN)   # the headline: ReEDS's credit convention
            ccm_t = float(CCM.loc[t])
            # conversion companion: placed-in-service credit on an OCC-only basis
            i_pis = i_r * ccm_t
            row.update(S_t_2004_per_MW=round(S), n_build_regions=len(i_r),
                       ccmult=round(ccm_t, 4),
                       i_model_min=round(float(i_r.min()), 3),
                       i_model_max=round(float(i_r.max()), 3),
                       i_model_headline=round(float(i_r.max()), 3),
                       i_pis_min=round(float(i_pis.min()), 3),
                       i_pis_max=round(float(i_pis.max()), 3),
                       i_pis_headline=round(float(i_pis.max()), 3),
                       # marginal-build gap on one Vogtle-pair-equivalent (2.2 GW)
                       S_x_2p2GW_2024B=round(S * 2200.0 * TO2024 / 1e9, 1),
                       itc_insufficient=bool(i_r.max() > 1.0),
                       pis_insufficient=bool(i_pis.max() > 1.0))""")
rep("5375aaf6",
    """n_over = int(t09["itc_insufficient"].sum())
print(f"gated (case, year) points: {len(t09)}; rate rows: "
      f"{int((t09['status'] == 'rate').sum())}; statutory rate above 100%: {n_over}")""",
    """n_over = int(t09["itc_insufficient"].sum())
print(f"gated (case, year) points: {len(t09)}; rate rows: "
      f"{int((t09['status'] == 'rate').sum())}; model-convention rate above 100%: {n_over}")""")
rep("5375aaf6",
    """print(f"excluding the equality duplicate: rate rows "
      f"{int((ne9['status'] == 'rate').sum())}; "
      f"above 100%: {int(ne9['itc_insufficient'].sum())}")""",
    """print(f"excluding the equality duplicate: rate rows "
      f"{int((ne9['status'] == 'rate').sum())}; "
      f"above 100%: {int(ne9['itc_insufficient'].sum())} "
      f"(pis conversion: {int(ne9['pis_insufficient'].sum())})")""")
rep("5375aaf6",
    """print("\\nstatutory headline rate (credit cash at placed-in-service), smr100 p50:")
p50 = t09[(t09["case"].isin([f"smr100_{s}_p50" for s in SCHEDULES]))
          & (t09["status"] == "rate")]
print(p50.pivot_table(index="t", columns="case", values="i_headline").round(2).to_string())
print("\\nmodel-convention (QPE-counterfactual) headline, same cases:")
print(p50.pivot_table(index="t", columns="case", values="i_model_headline").round(2).to_string())""",
    """print("\\nrequired ITC rate (model convention), smr100 p50:")
p50 = t09[(t09["case"].isin([f"smr100_{s}_p50" for s in SCHEDULES]))
          & (t09["status"] == "rate")]
print(p50.pivot_table(index="t", columns="case", values="i_model_headline").round(2).to_string())
print("\\nconversion companion (placed-in-service, OCC-only basis), same cases:")
print(p50.pivot_table(index="t", columns="case", values="i_pis_headline").round(2).to_string())""")

# ---- 4. cell 0f97e237 (f13) ---------------------------------------------------------
rep("0f97e237",
    '# ---- f13: required statutory ITC rate against solve year',
    '# ---- f13: required ITC rate (model convention) against solve year')
rep("0f97e237",
    't09i = t09[t09["status"] == "rate"].set_index(["case", "t"])["i_headline"]',
    't09i = t09[t09["status"] == "rate"].set_index(["case", "t"])["i_model_headline"]')
rep("0f97e237",
    'ax.set_ylabel("required statutory ITC rate")',
    'ax.set_ylabel("required ITC rate (model convention)")')

# ---- 5. cells t16md001 / t16cd001 ---------------------------------------------------
rep("t16md001",
    "Where the statutory rate schedule declines",
    "Where the required-rate schedule declines")
rep("t16cd001",
    '           .set_index("t")["i_headline"])',
    '           .set_index("t")["i_model_headline"])')

# ---- 6. cell bb201490 (outlay md) ---------------------------------------------------
put("bb201490", "QPE-counterfactual outlay", """\
### ITC outlay

The year-assignment rule (procedure step 7), written one time: solve year t
represents the calendar years after the previous solve year, through t. ReEDS
itself annualizes new builds this way (`cap_new_ann` divides the block by the
gap). The rate i_t applies to all builds in that group. R_t keeps the forward
convention, because capacity in year t persists to the next solve year.

The outlay is B_t = i_model(t) x ccmult(t) x (sum of the capex bases of all
builds in year t): the credit's face value accrued to commissioning at
interest_rate_nom. By timing neutrality this is the PV-consistent booking
under either delivery mechanism (progress payment during construction, or a
placed-in-service claim on the interest-inclusive basis); there is no
separate counterfactual outlay. The capex base per MW in region r is
cost_cap(t) x regional factor(r), with the regional factor from the h5
multiplier divided by natbase.""")

# ---- 7. cell 4d0b4dcc (t10 + t12) ---------------------------------------------------
rep("4d0b4dcc", "    nb, K, _ = natfin(c)", "    nb, K, CCM = natfin(c)")
rep("4d0b4dcc",
    """        i_head = float(sub.loc[t, "i_headline"])
        blt = bl.xs(t, level="t")
        blt = blt[blt > 0]
        fmb = fm.xs(t, level="t").reindex(blt.index)
        base = float(cc.loc[t]) * fmb / float(nb.loc[t])          # OCC x regfac, 2004$/MW
        B_ann = i_head * float((base * blt).sum())                # 2004$/yr (builds MW/yr)
        bgap = t - TPREV[t]
        pv_w = sum(1.0 / DR ** (y - 2026) for y in range(t - bgap + 1, t + 1))
        out_rows.append(dict(case=c, t=t, i_headline=i_head,""",
    """        i_head = float(sub.loc[t, "i_model_headline"])
        ccm_t = float(CCM.loc[t])
        blt = bl.xs(t, level="t")
        blt = blt[blt > 0]
        fmb = fm.xs(t, level="t").reindex(blt.index)
        base = float(cc.loc[t]) * fmb / float(nb.loc[t])          # OCC x regfac, 2004$/MW
        B_ann = i_head * ccm_t * float((base * blt).sum())  # face accrued to commissioning
        # timing-neutrality invariance: identical to the old statutory booking
        # i_pis x base, up to the 3-dp rounding of both rates in t09
        assert (abs(i_head * ccm_t - float(sub.loc[t, "i_pis_headline"]))
                <= 5.5e-4 * (1.0 + ccm_t)), (c, t)
        bgap = t - TPREV[t]
        pv_w = sum(1.0 / DR ** (y - 2026) for y in range(t - bgap + 1, t + 1))
        out_rows.append(dict(case=c, t=t, i_model_headline=i_head,""")
rep("4d0b4dcc",
    'print("PV of the two fiscal quantities, 2026-2050, 2024 $B (B_t statutory):")',
    'print("PV of the two fiscal quantities, 2026-2050, 2024 $B '
    '(B_t accrued to commissioning):")')

# ---- 8. NEW cells t17md001 / t17cd001 (after t11 cell 203eb154) ---------------------
T17_MD = """\
### t17 - the mandate priced per vintage (capacity-standard reading)

R_t (t08) bills the capacity-credit market by year, which truncates at 2050:
a 2047 vintage is credited three years of payments, a 2031 vintage twenty.
t17 removes the truncation by regrouping the same sum per vintage - each
vintage of program additions earns the clearing price over its 30-year
window - and bracketing the post-2050 price with the same cut/hold
conventions as C_b. The cut variant is the t08 sum in a different order, and
the cell asserts that identity per case. Inside the horizon the stream keeps
t08's solve-block discounting (which is what makes the identity exact); the
held tail discounts calendar years at the ledger rate. The fleet-rent column
is the pre-existing fleet's rent under the fleet-inclusive large100 standard
(within the horizon only); smr100 fleet rent is zero by construction.
"""

T17_CODE = """\
# ---- t17: mandate cost restated per vintage (capacity-standard reading) --------------------------
per_rows = []
for c in CASES:
    d = DUALS[(DUALS["case"] == c) & (DUALS["t"] >= 2026)].set_index("t").sort_index()
    dual = d["dual_2004_MWyr"]
    prog = d["program_MW"]
    assert (prog.diff().dropna() >= -1e-6).all(), c    # additions basis is nondecreasing
    d2050 = float(dual.get(2050, 0.0))
    fleet = (d["mandate_MW"] - d["program_MW"]).clip(lower=0.0)
    pv_fleet = sum(float(dual[t]) * float(fleet[t]) * GAP[t] / DR ** (t - 2026)
                   for t in d.index)
    # per-vintage compliance stream: solve-block arithmetic inside the horizon
    # (reused from t08 - this keeps the cut identity exact), calendar years at
    # the held 2050 dual beyond it, through the vintage's 30-year window.
    stream_cut = {t: sum(float(dual[u]) * GAP[u] / DR ** (u - 2026)
                         for u in d.index if u >= t) for t in d.index}
    pv_cut = pv_hold = 0.0
    for k_i, t in enumerate(d.index):
        prev = d.index[k_i - 1] if k_i > 0 else None
        add = float(prog[t]) - (float(prog[prev]) if prev is not None else 0.0)
        if add <= 0:
            continue
        tail = sum(d2050 / DR ** (y - 2026) for y in range(2051, t + 30))
        pv_cut += add * stream_cut[t]
        pv_hold += add * (stream_cut[t] + tail)
    t08_pv = float(t08.set_index("case").loc[c, "PV_rental_transfer_2024B"])
    pv_cut24 = pv_cut * TO2024 / 1e9
    assert abs(pv_cut24 - t08_pv) <= max(0.06, 5e-3 * max(t08_pv, 1e-9)), (c, pv_cut24, t08_pv)
    per_rows.append(dict(case=c,
                         PV_newbuild_cut_2024B=round(pv_cut24, 1),
                         PV_newbuild_hold_2024B=round(pv_hold * TO2024 / 1e9, 1),
                         PV_fleet_rent_2024B=round(pv_fleet * TO2024 / 1e9, 1),
                         PV_mandate_cut_2024B=round((pv_cut + pv_fleet) * TO2024 / 1e9, 1),
                         PV_mandate_hold_2024B=round((pv_hold + pv_fleet) * TO2024 / 1e9, 1)))
t17 = pd.DataFrame(per_rows)
t17.to_csv(EXPORTS / "t17_mandate_perbuild.csv", index=False)
print("cut identity: the per-vintage restatement reproduces the t08 PV in every case (asserted).")
print(t17.to_string(index=False))
"""

# ---- 9. cells t13md001 / t13cd001 / t13fg001 (symmetric scoring) --------------------
put("t13md001", "different tax character", """\
### Instrument comparison: the floor, the flat grant, and the ITC, net of tax

Symmetric scoring (2026-08-18): every instrument is valued through ReEDS's
own financing arithmetic. A dollar of commissioning-date cash - grant or
credit alike - pays down capital that would otherwise have to earn the
technology hurdle premium over the 30-year evaluation window, so its value
in dual currency is risk x eval_adj per after-tax dollar (eval_adj = 1
here). Scoring the credit through fin_mult but the grant as plain cash would
hand the credit a fictitious advantage; both get the leverage. (The old
asymmetric ledger's "avoided risk premium" discount was that artifact, and
it is gone.)

The floor: the minimum net government cost that delivers S_t to every build
is

floor = (1 - tau) x T / (risk x eval_adj), with T = sum of S_t x builds.

There is no cheaper targeted design: at the LP optimum every building region
has a zero reduced cost, so every builder's own gap equals S_t - verified
from the h5 `reduced_cost` output. The equalization is entry with endogenous
prices, and it means the floor needs only one public number per year (the
compliance price), not private cost information. (For a region that builds,
a zero reduced cost is LP optimality itself; the economic reading - every
builder's gap equals S_t - additionally assumes no other binding constraint
pays rent to those builds. Outside the model, private site rents and lumpy
builds would let some builders pocket part of a flat payment; that caveat
belongs to the discussion, not to this ledger.)

Tax character: T is pre-tax revenue requirement; a taxable grant returns
tau x T, so the unleveraged flat cash grant nets (1 - tau) x T = risk x
floor (tau = 0.257, the model's effective corporate rate, not the 21%
statutory rate).

The credit: face B (accrued to commissioning, see t10) is tax-free to the
developer; the government recoups tax on the halved depreciation basis,
N = B x (1 - tau x PV_dep / 2). Under symmetric scoring the identity

net ratio = N / floor = overshoot / (1 - penalty)

holds: the risk/eval leverage cancels between instrument and floor, and the
tax terms cancel exactly (k x claw = 1 - tau x PV_dep). The credit's excess
over the floor is the monetization haircut plus the uniform-rate overshoot -
two frictions, nothing else. The ratio against the flat grant stays as a
column for continuity; the gross ratio B / T stays as budget scoring only
(it understates the credit's relative cost because it ignores the tax the
grant returns).

Commitment companion: the same accumulation with C_b (t11) in place of S_t
prices the commitment bound - what vintage-b builds accept given a credible
declining schedule and foresight of the dual path (investor-side windows at
the post-2026 rate; ledger PV at DR). It is a bound, not a run: the myopic
model contains no such agent, and the dual path is itself myopic-equilibrium
output.

*Figure note (t13 figure): credit cost against the floor and the flat grant per case; gross budget scoring reverses the net-of-tax ranking.*""")

put("t13cd001", "net_loss_ratio_realistic", """\
# ---- t13: floor, flat grant, and ITC — net-of-tax government cost (symmetric scoring) ----------
rows13 = []
cw_all = t11.set_index(["case", "t"])
for c in CASES:
    tech = META[c]["mandated_tech"]
    bl = CAPNEW[c]
    # LP optimality: no building (r, t) carries a reduced-cost row (zeros are suppressed)
    rc = load(c, "reduced_cost")
    rc = rc[(rc["i"] == tech) & (rc["*.1"] == "cap")]
    builders = set(zip(bl[bl > 0].index.get_level_values("r"),
                       bl[bl > 0].index.get_level_values("t")))
    overlap = builders & set(zip(rc["r"], rc["t"]))
    assert not overlap, (c, sorted(overlap)[:5])
    nbse, K, CCM = natfin(c)
    cc, fm = COSTCAP[c], FINMULT[c]
    # the technology hurdle premium inside fin_mult_noITC (same arithmetic as natfin)
    g46 = fin_tech(c)
    g46 = g46[g46["i"] == IN_NAME[tech]].set_index("t").reindex(YEARS).ffill().bfill()
    ev46 = float(g46["eval_period"].iloc[0])
    rk46 = pd.Series(1.0 + g46["finance_diff_real"].to_numpy(float)
                     * ((1 - (1 / D_REAL) ** ev46) / (D_REAL - 1.0)), index=YEARS)
    sub = t09[(t09["case"] == c) & (t09["status"] == "rate")].set_index("t")
    pv = dict(T=0.0, T_net=0.0, FLOOR=0.0, B=0.0, N=0.0, OV=0.0, RK=0.0, PRED=0.0,
              COM_cut=0.0, COM_hold=0.0)
    for t in sub.index:
        S = float(sub.loc[t, "S_t_2004_per_MW"])
        i_head = float(sub.loc[t, "i_model_headline"])
        ccm_t = float(CCM.loc[t])
        blt = bl.xs(t, level="t")
        blt = blt[blt > 0]
        fmb = fm.xs(t, level="t").reindex(blt.index)
        base = float(cc.loc[t]) * fmb / float(nbse.loc[t])     # OCC x regfac, 2004$/MW
        B_ann = i_head * ccm_t * float((base * blt).sum())     # face accrued to commissioning
        tau = float(TAX[yi(t)])
        k_t = float(K.loc[t])
        claw = 1.0 / (2.0 - k_t)                    # 1 - tau*PV_dep/2 (dep-basis clawback)
        rk_t = float(rk46.loc[t])
        bgap = t - TPREV[t]
        pv_w = sum(1.0 / DR ** (y - 2026) for y in range(t - bgap + 1, t + 1))
        pv["T"] += S * float(blt.sum()) * pv_w
        pv["T_net"] += S * float(blt.sum()) * (1.0 - tau) * pv_w
        # the floor: commissioning-date cash scored through the same financing
        # machinery as the credit (symmetric scoring, 2026-08-18)
        w_fl = S * float(blt.sum()) * (1.0 - tau) / rk_t * pv_w
        pv["FLOOR"] += w_fl
        pv["B"] += B_ann * pv_w
        pv["N"] += B_ann * claw * pv_w
        # net-ratio identity terms, floor-PV-weighted
        ov_t = float((fmb * blt).sum() / (fmb.min() * float(blt.sum())))
        pv["OV"] += ov_t * w_fl
        pv["RK"] += rk_t * w_fl
        pv["PRED"] += ov_t / (1.0 - PEN) * w_fl
        # commitment bound: the same accumulation with C_b in place of S_t
        pv["COM_cut"] += (float(cw_all.loc[(c, t), "C_cut_2004_per_MW"])
                          * float(blt.sum()) * (1.0 - tau) / rk_t * pv_w)
        pv["COM_hold"] += (float(cw_all.loc[(c, t), "C_hold_2004_per_MW"])
                           * float(blt.sum()) * (1.0 - tau) / rk_t * pv_w)
    v = {k_: pv[k_] * TO2024 / 1e9
         for k_ in ("T", "T_net", "FLOOR", "B", "N", "COM_cut", "COM_hold")}
    ov_w = pv["OV"] / pv["FLOOR"]
    rk_w = pv["RK"] / pv["FLOOR"]
    pred = pv["PRED"] / pv["FLOOR"]
    # identity: net ratio vs floor = overshoot / (1 - penalty); the risk/eval
    # leverage cancels between instrument and floor, and the tax terms cancel
    # exactly (k x claw = 1 - tau x PV_dep). tolerance 5e-3: B uses the
    # 3-dp-rounded i_model_headline from t09 (exact when unrounded).
    assert abs(pred - v["N"] / v["FLOOR"]) < 5e-3, (c, pred, v["N"] / v["FLOOR"])
    assert abs(v["B"] - float(cmp_tbl.loc[c, "PV_ITC_outlay_2024B"])) <= max(0.06, 5e-3 * v["B"])
    rows13.append(dict(case=c,
                       PV_flat_grant_2024B=round(v["T"], 1),
                       PV_grant_net_2024B=round(v["T_net"], 1),
                       PV_floor_2024B=round(v["FLOOR"], 1),
                       PV_ITC_outlay_2024B=round(v["B"], 1),
                       PV_ITC_net_2024B=round(v["N"], 1),
                       PV_commit_cut_2024B=round(v["COM_cut"], 1),
                       PV_commit_hold_2024B=round(v["COM_hold"], 1),
                       net_ratio_vs_floor=round(v["N"] / v["FLOOR"], 2),
                       net_ratio_vs_grant=round(v["N"] / v["T_net"], 2),
                       gross_scoring_ratio=round(v["B"] / v["T"], 2),
                       capex_overshoot=round(ov_w, 4),
                       risk_premium_factor=round(rk_w, 4),
                       pred_net_ratio=round(pred, 4)))
t13 = pd.DataFrame(rows13)
t13.to_csv(EXPORTS / "t13_flat_grant.csv", index=False)
print("reduced-cost check: no building (r, t) has a nonzero reduced cost, in any "
      "case (LP optimality at basic builds; see the markdown note above).")
print(t13.to_string(index=False))
for fam in ("smr100", "large100"):
    f = t13[t13["case"].str.startswith(fam)]
    print(f"\\n{fam}  net vs floor: "
          f"{f['net_ratio_vs_floor'].min():.2f} .. {f['net_ratio_vs_floor'].max():.2f}"
          f";  net vs flat grant: {f['net_ratio_vs_grant'].min():.2f} .. "
          f"{f['net_ratio_vs_grant'].max():.2f}"
          f";  gross scoring B/T: {f['gross_scoring_ratio'].min():.2f} .. "
          f"{f['gross_scoring_ratio'].max():.2f}")
""")

put("t13fg001", "net_loss_ratio_realistic", """\
# ---- t13 figure: instrument comparison, regenerated on the 37-case basis --------------
fcmp = t13[~t13["case"].str.endswith("_eq")].set_index("case")
fig, ax = plt.subplots(figsize=(11, 4.2))
x = np.arange(len(fcmp))
ax.axhline(1.0, lw=0.8, color=MUTED, zorder=1)
ax.scatter(x, fcmp["gross_scoring_ratio"], marker="s", s=22, color=COL["large"],
           label="gross scoring B / T")
ax.scatter(x, fcmp["net_ratio_vs_grant"], marker="^", s=22, color=FAINT,
           label="net of tax, vs flat grant")
ax.scatter(x, fcmp["net_ratio_vs_floor"], marker="o", s=26, color=COL["smr"],
           label="net of tax, vs floor")
ax.set_xticks(x)
ax.set_xticklabels(fcmp.index, rotation=90, fontsize=6.5)
ax.set_ylabel("credit cost / benchmark cost")
ax.legend(fontsize=8, ncol=3)
fig.tight_layout()
savefig(fig, "t13_instrument_comparison.png")
plt.show()
""")

# ---- 10. cells t14md001 / t14cd001 --------------------------------------------------
put("t14md001", "hierarchy.csv", """\
### Rate resolution: federal, state, and zone ITC

One percentage rate (model convention) per geography per year. Each
geography uses the smallest rate that delivers S_t to every zone that builds
inside it (by the equalization above, every builder needs the full S_t). The
federal rung is then exactly the t10 headline outlay B_t; the cell asserts
this identity. Finer resolution saves money only through the rate
conversion: a percentage rate maxed for the cheapest capex base overdelivers
through every larger base. The state map comes from
`inputs/zones/z90/hierarchy.csv`. A credit denominated in dollars per MW
removes the overshoot in one step; its cost is the menu's $/MW rung (t18).""")
rep("t14cd001",
    """        i_need = (S * float(K.loc[t]) * float(CCM.loc[t])
                  / ((1.0 - PEN) * FC))                 # statutory rate that delivers S_t in r
        cost = FC / float(nbse.loc[t]) * blt                # capex base x builds, per rate point""",
    """        i_need = (S * float(K.loc[t])
                  / ((1.0 - PEN) * FC))     # model-convention rate that delivers S_t in r
        cost = (FC / float(nbse.loc[t]) * blt
                * float(CCM.loc[t]))    # capex base x builds, accrued to commissioning""")

# ---- 11. NEW cells t18 (menu) and t19 (commitment ITC) ------------------------------
T18_MD = """\
### t18 - the subsidy instrument menu

One exhibit, the centerpiece: each instrument's net PV cost as a multiple of
the floor, per case. The menu is indexed by institutional capability - each
step down demands more of the state, not more information about builders:

- **floor** (1.00): flat $-per-MW support at commissioning, elective pay -
  needs a statute that pays dollars per MW with no monetization haircut.
- **$/MW with the 10% haircut**: x 1/(1-0.1) = 1.11.
- **unleveraged flat cash grant** (taxable, no financing leverage): x risk =
  1.04 - shown to make the scoring convention visible.
- **uniform percentage ITC**: x overshoot/(1-0.1) - adds the uniform-rate
  overshoot, because a percentage of heterogeneous capex bases pays the
  cheapest-base rate to every costlier base (t14 prices partial repairs).
- **capacity-standard mandate** (t17, cut-hold band, net of tax): pays every
  standing vintage the clearing price - including the pre-existing fleet in
  the large100 cases - so it is the expensive end wherever a fleet collects
  rent.
- **commitment bound** (below 1 where duals decline): pays vintage b its
  foresight value C_b - needs a credible multi-decade schedule and
  foresighted investors, and the dual path is myopic-equilibrium output, so
  it is a bound, not a run.

Payment timing is not a rung: at these rates (ccmult accrual 8.0% nominal
against a 7.99% ledger WACC) early payment is PV-neutral; paying earlier
trades a government-borrowing-rate wedge against construction-completion
risk (the loan-guarantee limit), both outside this ledger. A production
credit (PTC) is also not a rung: by the same conservation-of-money logic its
net cost lands with the grant's, up to payment-window discounting.
"""

T18_CODE = """\
# ---- t18 + f16: the subsidy instrument menu ------------------------------------------------------
TAXA = np.asarray(TAX, dtype=float)[YEARS >= 2026]
assert float(TAXA.max() - TAXA.min()) < 1e-9   # flat from 2018 on; a scalar is exact
TAUC = float(TAXA.flat[0])
men = t13.set_index("case").join(t17.set_index("case"))
rows18 = []
for c, r in men.iterrows():
    fl = float(r["PV_floor_2024B"])
    if fl <= 0:
        continue
    rows18.append(dict(
        case=c,
        PV_floor_2024B=round(fl, 1),
        dpmw_electivepay=1.0,
        dpmw_haircut=round(1.0 / (1.0 - PEN), 3),
        cash_grant=round(float(r["PV_grant_net_2024B"]) / fl, 2),
        uniform_itc=round(float(r["PV_ITC_net_2024B"]) / fl, 2),
        mandate_cut=round((1.0 - TAUC) * float(r["PV_mandate_cut_2024B"]) / fl, 2),
        mandate_hold=round((1.0 - TAUC) * float(r["PV_mandate_hold_2024B"]) / fl, 2),
        commitment_cut=round(float(r["PV_commit_cut_2024B"]) / fl, 2),
        commitment_hold=round(float(r["PV_commit_hold_2024B"]) / fl, 2)))
t18 = pd.DataFrame(rows18)
t18.to_csv(EXPORTS / "t18_instrument_menu.csv", index=False)
print(t18.to_string(index=False))

f18 = t18[~t18["case"].str.endswith("_eq")].set_index("case")
fig, ax = plt.subplots(figsize=(11, 4.6))
x = np.arange(len(f18))
ax.axhline(1.0, lw=1.0, color=INK, zorder=1)
ax.axhline(1.0 / (1.0 - PEN), lw=0.8, color=MUTED, ls=":", zorder=1)
ax.vlines(x, f18["mandate_cut"], f18["mandate_hold"], color=COL["large"], lw=3.2,
          alpha=0.5, label="capacity-standard mandate (cut-hold)")
ax.vlines(x, f18["commitment_cut"], f18["commitment_hold"], color=FAINT, lw=3.2,
          alpha=0.7, label="commitment bound (cut-hold)")
ax.scatter(x, f18["uniform_itc"], marker="o", s=26, color=COL["smr"],
           label="uniform percentage ITC")
ax.scatter(x, f18["cash_grant"], marker="^", s=20, color=MUTED,
           label="unleveraged cash grant")
ax.set_yscale("log")
ax.set_yticks([0.125, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0])
ax.yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter("%g"))
ax.set_xticks(x)
ax.set_xticklabels(f18.index, rotation=90, fontsize=6.5)
ax.set_ylabel("net PV cost / floor")
ax.legend(fontsize=7.5, ncol=2)
fig.tight_layout()
savefig(fig, "f16_instrument_menu.png")
plt.show()
for fam in ("smr100", "large100"):
    f = t18[t18["case"].str.startswith(fam) & ~t18["case"].str.endswith("_eq")]
    print(f"{fam}: uniform ITC {f['uniform_itc'].min():.2f}..{f['uniform_itc'].max():.2f}"
          f" x floor;  mandate hold {f['mandate_hold'].min():.2f}.."
          f"{f['mandate_hold'].max():.2f};  commitment hold "
          f"{f['commitment_hold'].min():.2f}..{f['commitment_hold'].max():.2f}")
"""

T19_MD = """\
### t19 - the commitment ITC (companion schedule)

Push C_b through the same inversion that produces i_model from S_t and you
get the rate schedule a foresighted investor accepts under a credible
declining path: flatter across vintages, and immune to rate-lock gaming
(t16 prices the windfall an S_t-based schedule hands a 6-year BOC lock; a
C_b-based schedule pays each vintage its indifference value, so there is no
spread to lock). Symmetric caveat: if investors are myopic - as ReEDS's
are - the commitment schedule underpays and deployment fails; the pair
(i_model, i_commit) brackets the behavioral assumption. Cut/hold brackets
the post-2050 duals as everywhere.
"""

T19_CODE = """\
# ---- t19: the commitment ITC rate schedule -------------------------------------------------------
rows19 = []
cw19 = t11.set_index(["case", "t"])
for c in CASES:
    nbse, K, CCM = natfin(c)
    cc, fm, bl = COSTCAP[c], FINMULT[c], CAPNEW[c]
    sub = t09[(t09["case"] == c) & (t09["status"] == "rate")].set_index("t")
    for t in sub.index:
        blt = bl.xs(t, level="t")
        blt = blt[blt > 0]
        fmb = fm.xs(t, level="t").reindex(blt.index)
        den = (1.0 - PEN) * float(cc.loc[t]) * float(fmb.min())
        i_m = float(sub.loc[t, "i_model_headline"])
        # same inversion as t09's headline (S x K / den); sanity vs the table
        assert abs(float(sub.loc[t, "S_t_2004_per_MW"]) * float(K.loc[t]) / den
                   - i_m) < 5e-3, (c, t)
        rows19.append(dict(
            case=c, t=t,
            i_commit_cut=round(float(cw19.loc[(c, t), "C_cut_2004_per_MW"])
                               * float(K.loc[t]) / den, 3),
            i_commit_hold=round(float(cw19.loc[(c, t), "C_hold_2004_per_MW"])
                                * float(K.loc[t]) / den, 3),
            i_model_headline=i_m))
t19 = pd.DataFrame(rows19)
t19["hold_over_model"] = (t19["i_commit_hold"] / t19["i_model_headline"]).round(2)
t19.to_csv(EXPORTS / "t19_commitment_itc.csv", index=False)
f19 = t19[t19["case"].str.startswith("smr100") & t19["case"].str.endswith("_p50")]
dm = f19.groupby("case")["i_model_headline"].apply(lambda s: s.diff().abs().mean())
dc = f19.groupby("case")["i_commit_hold"].apply(lambda s: s.diff().abs().mean())
print(f"smr100 p50 mean |year-over-year rate step|: myopic {dm.mean():.3f}, "
      f"commitment-hold {dc.mean():.3f} (flatter)")
print(f"hold_over_model, smr100: {f19['hold_over_model'].min():.2f} .. "
      f"{f19['hold_over_model'].max():.2f} at p50")
"""

# ---- 12. cell ebc6728a (S10 caveats) ------------------------------------------------
rep("ebc6728a",
    """6. **ITC translation status.** The rates in S8 follow
   `ITC calculation procedure.md` (sequential logic: S_t = raw dual, no
   discounting across years; fin_mult inversion; statutory conversion with
   the ccmult timing correction; formula locked 2026-08-14). Two legal
   inputs can still move the rate level: the monetization haircut (0.1 here)
   and the depreciation recovery class (15-year MACRS here).""",
    """6. **ITC translation status.** The rates in S8 follow
   `ITC calculation procedure.md` (sequential logic: S_t = raw dual, no
   discounting across years; fin_mult inversion). Convention revised
   2026-08-18 (supersedes the 2026-08-14 statutory lock): the headline is
   the model-convention rate i_model; a placed-in-service credit on an
   overnight-cost-only basis is i_model x ccmult (exported as the i_pis_*
   columns), and under Section 263A(f) a real owner's statutory rate lies
   between the two. Two legal inputs can still move the rate level: the
   monetization haircut (0.1 here) and the depreciation recovery class
   (15-year MACRS here).""")
rep("ebc6728a",
    """The required statutory
   ITC exceeds 100% in 82 of 329 unique rate case-years (334 rows counting
   the equality duplicate, which adds none), concentrated in the large100
   p95 worlds — 8–10 case-years per schedule except eia's 2 (it prices only
   6 of 12 mandated years); smr100 contributes 20, all at p95: an ITC alone
   cannot deliver those worlds.""",
    """The required
   model-convention ITC exceeds 100% in 5 of 329 unique rate case-years
   (334 rows counting the equality duplicate, which adds none) — the late
   p95 years of the eo schedule in both families plus cop28's 2050; the
   placed-in-service OCC-only conversion (i_pis) exceeds 100% in 82,
   concentrated in the large100 p95 worlds. In the most expensive worlds an
   ITC alone cannot deliver the late years.""")

# ---- insert the new cells -----------------------------------------------------------
ids = [c["id"] for c in nb["cells"]]
nb["cells"][ids.index("203eb154") + 1:ids.index("203eb154") + 1] = [
    md_cell("t17md001", T17_MD), code_cell("t17cd001", T17_CODE)]
ids = [c["id"] for c in nb["cells"]]
nb["cells"][ids.index("t14cd001") + 1:ids.index("t14cd001") + 1] = [
    md_cell("t18md001", T18_MD), code_cell("t18cd001", T18_CODE),
    md_cell("t19md001", T19_MD), code_cell("t19cd001", T19_CODE)]
n += 2

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"applied {n} edits + 6 new cells (t17/t18/t19); wrote {NB.name}")
print("now re-execute the notebook headless on the playground-env kernel "
      "with drive D mounted.")
