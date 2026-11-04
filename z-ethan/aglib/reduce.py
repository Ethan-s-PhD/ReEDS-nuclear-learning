"""Per-run reducers for paper AG: products of prices and quantities that the extract spec cannot express.

``nlpaper.h5io.extract`` applies one filter or aggregation per report key. The AG ledger
(``docs/protocol.md`` §4) needs sums of price x quantity over timeslices and regions, which
must be formed before any aggregation. :func:`reduce_run` forms them for one ``outputs.h5``
file and returns one tidy table with columns ``t, item, Value``.

Units. Money items are 2004 $ per year; ``Q_*`` items are MWh per year (``Q_oper_res``:
MW-h of reserve requirement). Definitions, from ``reeds/core/terminus/report.gms`` and the
supply-demand balance ``eq_supply_demand_balance`` (``reeds/core/setup/c_model.gms``):

=============  ==============================================================================
item           definition
=============  ==============================================================================
P_E            sum over r, h of reqt_price(load) x reqt_quant(load); the quantity is
               hours x (LOAD - production load), so it includes Canadian exports
P_C            sum over r, stress slices s of reqt_price(res_marg) x reqt_quant(res_marg);
               the quantity is LOAD in the slice ($/MW per slice x MW)
P_R            sum over RPS category, r of reqt_price(state_rps) x reqt_quant(state_rps)
P_H2_E         sum over r, h of reqt_price(load) x hours x prod_load (H2/DAC load)
P_H2_C         sum over r, s of reqt_price(res_marg) x prod_load in stress slices
CR_E           congestion rent on the representative timeslices, AC/B2B/LCC routes:
               sum of hours x FLOW(r->rr) x (p_rr x (1 - tranloss(r,rr)) - p_r)
CR_E_vsc       the same sum on VSC routes (these enter the AC balance through converters,
               so they are reported apart)
CR_C           congestion rent in the stress slices (stress prices, no hours), non-VSC
CR_C_vsc       the same on VSC routes
Q_E            sum of reqt_quant(load)
Q_oper_res     sum of reqt_quant(oper_res); reqt_price carries no oper_res rows
P_C_ann_firstcut  res_marg_ann price x quantity: the first cut's overstated capacity term, for check C5 only
REC_paid       sum of rec_outputs (RECs from state st to ast) x the RPS price of the buying state ast
REC_recv       the same RECs x the RPS price of the selling state st. Bundled RECs (RPS_Bundled,
               CES_Bundled) have no requirement of their own: they count toward RPS_All and CES
               (c_model.gms eq_REC_Requirement), so both prices are those of the parent category
=============  ==============================================================================

Balance identities that these items close (protocol §6, checks C1 and C2):
    C1  P_E + P_H2_E = revenue(load) + revenue(charge) + CR_E      (charge is negative)
    C2  P_C          = revenue(res_marg) + CR_C + P_H2_C
Residual terms not formed here: VSC conversion, hybrid-storage grid charging, dropped load.

The RPS account does not close the same way. P_R prices the requirement quantity; buyers pay for
RECs at their own state's price (``expenditure_flow_rps``, report.gms:1938); ``revenue('rps')``
pays each generator's eligible output at its own state's price. Hence
    P_R - revenue(rps) = (REC_paid - REC_recv)          REC trade wedge (buyer-state minus seller-state price)
                       + (P_R - REC_paid)               reported requirement minus RECs bought (ACP;
                                                        CES credits that exports to Canada consume)
                       - (revenue(rps) - REC_recv)      reporting difference (about zero)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from nlpaper import h5io, paths

ITEMS = ["P_E", "P_C", "P_R", "P_H2_E", "P_H2_C", "CR_E", "CR_E_vsc", "CR_C", "CR_C_vsc", "P_C_ann_firstcut",
         "REC_paid", "REC_recv", "Q_E", "Q_oper_res"]
ZONE_STATE = paths.REPO / "inputs" / "zones" / "z90" / "hierarchy.csv"     # the runs' zone set (GSw_ZoneSet)


def _key(f, name, key):
    """``h5io.read_key`` on an open file, or None when the group is absent (ReEDS drops all-zero groups)."""
    return h5io.read_key(name, key, f=f) if key in f else None


def _by_t(df, value="Value"):
    return df.groupby("t")[value].sum() if df is not None and len(df) else pd.Series(dtype=float)


def _rent(flow, loss, price, hours=None):
    """Congestion rent by year: sum of [hours x] F(r->rr) x (p_rr x (1 - loss) - p_r)."""
    m = flow.merge(loss, on=["r", "rr", "trtype"], how="left").fillna({"loss": 0.0})
    pr = price.rename(columns={"r": "rr", "p": "p_to"})
    m = m.merge(price.rename(columns={"p": "p_from"}), on=["r", "allh", "t"], how="left")
    m = m.merge(pr, on=["rr", "allh", "t"], how="left").fillna({"p_from": 0.0, "p_to": 0.0})
    m["v"] = m["F"] * (m["p_to"] * (1.0 - m["loss"]) - m["p_from"])
    if hours is not None:
        m = m.merge(hours, on="allh", how="left")
        m["v"] *= m["hours"]
    vsc = m["trtype"] == "VSC"
    return _by_t(m[~vsc], "v"), _by_t(m[vsc], "v")


def reduce_run(h5path) -> pd.DataFrame:
    """The ITEMS of one run as a long table ``t, item, Value`` (all solve years)."""
    import h5py

    name = Path(h5path).name
    with h5py.File(h5path, "r") as f:
        price = _key(f, name, "reqt_price")
        quant = _key(f, name, "reqt_quant")
        hours = _key(f, name, "hours").rename(columns={"Value": "hours"})
        prod = _key(f, name, "prod_load")
        loss = _key(f, name, "tranloss").rename(columns={"Value": "loss"})
        flow_e = _key(f, name, "tran_flow_all_rep")
        flow_c = _key(f, name, "tran_flow_all_stress")
        recs = _key(f, name, "rec_outputs")

    def cat(df, c):
        return df[df["*"] == c].rename(columns={"*.2": "allh"})

    p_load = cat(price, "load")[["r", "allh", "t", "Value"]].rename(columns={"Value": "p"})
    q_load = cat(quant, "load")[["r", "allh", "t", "Value"]].rename(columns={"Value": "q"})
    p_rm = cat(price, "res_marg")[["r", "allh", "t", "Value"]].rename(columns={"Value": "p"})
    q_rm = cat(quant, "res_marg")[["r", "allh", "t", "Value"]].rename(columns={"Value": "q"})
    p_rps = price[price["*"] == "state_rps"][["*.1", "r", "t", "Value"]].rename(columns={"Value": "p"})
    q_rps = quant[quant["*"] == "state_rps"][["*.1", "r", "t", "Value"]].rename(columns={"Value": "q"})

    out = {}
    m = p_load.merge(q_load, on=["r", "allh", "t"])
    out["P_E"] = _by_t(m.assign(v=m.p * m.q), "v")
    m = p_rm.merge(q_rm, on=["r", "allh", "t"])
    out["P_C"] = _by_t(m.assign(v=m.p * m.q), "v")
    m = p_rps.merge(q_rps, on=["*.1", "r", "t"])
    out["P_R"] = _by_t(m.assign(v=m.p * m.q), "v")
    # first-cut capacity term (res_marg_ann price x quantity), kept only for check C5 (protocol §6)
    m = price[price["*"] == "res_marg_ann"].merge(quant[quant["*"] == "res_marg_ann"],
                                                 on=["*", "*.1", "r", "*.2", "t"], suffixes=("_p", "_q"))
    out["P_C_ann_firstcut"] = _by_t(m.assign(v=m.Value_p * m.Value_q), "v")
    if recs is not None:
        st_of = pd.read_csv(ZONE_STATE).set_index("r")["st"]
        ps = p_rps.assign(st=p_rps["r"].map(st_of)).groupby(["*.1", "st", "t"], as_index=False)["p"].first()
        ps = ps.rename(columns={"*.1": "pcat"})
        recs = recs.assign(pcat=recs["RPSCat"].replace({"RPS_Bundled": "RPS_All", "CES_Bundled": "CES"}))
        m = recs.merge(ps.rename(columns={"p": "p_src"}), on=["pcat", "st", "t"], how="left")
        m = m.merge(ps.rename(columns={"st": "ast", "p": "p_dst"}), on=["pcat", "ast", "t"], how="left")
        m = m.fillna({"p_src": 0.0, "p_dst": 0.0})
        out["REC_paid"] = _by_t(m.assign(v=m.Value * m.p_dst), "v")
        out["REC_recv"] = _by_t(m.assign(v=m.Value * m.p_src), "v")
    out["Q_E"] = _by_t(q_load, "q")
    out["Q_oper_res"] = _by_t(quant[quant["*"] == "oper_res"])

    if prod is not None:
        pl = prod.groupby(["r", "allh", "t"], as_index=False)["Value"].sum()
        m = pl.merge(p_load, on=["r", "allh", "t"]).merge(hours, on="allh")
        out["P_H2_E"] = _by_t(m.assign(v=m.Value * m.p * m.hours), "v")
        m = pl.merge(p_rm, on=["r", "allh", "t"])
        out["P_H2_C"] = _by_t(m.assign(v=m.Value * m.p), "v")

    for flow, p, h, tag in [(flow_e, p_load, hours, "E"), (flow_c, p_rm, None, "C")]:
        if flow is not None:
            fl = flow.rename(columns={"Value": "F"})[["r", "rr", "allh", "trtype", "t", "F"]]
            out[f"CR_{tag}"], out[f"CR_{tag}_vsc"] = _rent(fl, loss[["r", "rr", "trtype", "loss"]], p, h)

    rows = [pd.DataFrame({"t": s.index.astype("int64"), "item": k, "Value": s.values})
            for k, s in out.items() if len(s)]
    return pd.concat(rows, ignore_index=True).sort_values(["item", "t"]).reset_index(drop=True)


WEDGE_ORIGINS = ["seller_unbound", "double_count", "trade_limits", "voluntary"]
PRICE_TOL = 1e-6   # 2004 $/REC: a selling state's price at or below this counts as zero


def reduce_run_recs(h5path) -> pd.DataFrame:
    """The REC trade wedge (``REC_paid - REC_recv``) of one run, split by origin. Long table ``t, item, Value``.

    Items ``wedge|<origin>`` are 2004 $ per year. Items ``Q|seller_unbound``, ``Q|seller_priced`` and ``Q|voluntary``
    are RECs (MWh) per year; the double_count and trade_limits parts share the ``seller_priced`` RECs. The prices and
    the merge are those of :func:`reduce_run`, so the four wedge items sum to ``REC_paid - REC_recv``.
    RECs a state uses itself (st = ast) carry no wedge. The origins of the other RECs:

    =============== ===========================================================================================
    seller_unbound  interstate RECs whose selling state has a zero price for that category (no rule, or a rule
                    that does not bind). The buyer's whole price is wedge. Any trade-limit value on these RECs
                    is inside it: the outputs hold no dual of the trade limits, so it cannot be split off.
    double_count    interstate RECs from a selling state with a positive price: min(p_dst - p_src, p_src) per
                    REC. eq_REC_Generation (c_model.gms) removes exports from the seller's credit supply, and
                    eq_REC_Requirement subtracts them again from the RECs that count toward the seller's requirement, so an export costs the
                    seller two RECs of compliance and the buyer's price is about twice the seller's or more
    trade_limits    the same RECs: the rest of p_dst - p_src (above 2 x p_src), from the bundled-REC transmission
                    limit, the unbundled and out-of-state caps and the ACP export rule (eq_REC_launder)
    voluntary       RECs sold to the voluntary market. ReEDS reports no price for it, so the wedge is -p_src
    =============== ===========================================================================================

    Item ``min_ratio|seller_priced`` is the smallest p_dst / p_src over the RECs from priced sellers in each year
    (a ratio, not money; do not sum it)."""
    import h5py

    name = Path(h5path).name
    with h5py.File(h5path, "r") as f:
        price = _key(f, name, "reqt_price")
        recs = _key(f, name, "rec_outputs")
    if recs is None:
        return pd.DataFrame(columns=["t", "item", "Value"])
    p_rps = price[price["*"] == "state_rps"][["*.1", "r", "t", "Value"]].rename(columns={"Value": "p"})
    st_of = pd.read_csv(ZONE_STATE).set_index("r")["st"]
    ps = p_rps.assign(st=p_rps["r"].map(st_of)).groupby(["*.1", "st", "t"], as_index=False)["p"].first()
    ps = ps.rename(columns={"*.1": "pcat"})
    recs = recs.assign(pcat=recs["RPSCat"].replace({"RPS_Bundled": "RPS_All", "CES_Bundled": "CES"}))
    m = recs.merge(ps.rename(columns={"p": "p_src"}), on=["pcat", "st", "t"], how="left")
    m = m.merge(ps.rename(columns={"st": "ast", "p": "p_dst"}), on=["pcat", "ast", "t"], how="left")
    m = m.fillna({"p_src": 0.0, "p_dst": 0.0})
    own = m["st"] == m["ast"]
    assert ((m.loc[own, "p_dst"] - m.loc[own, "p_src"]).abs() < 1e-9).all(), "own-state RECs carry no wedge"
    m = m[~own]
    vol = m["ast"] == "voluntary"
    unb = ~vol & (m["p_src"] <= PRICE_TOL)
    pri = ~vol & ~unb
    gap = m["p_dst"] - m["p_src"]
    dc = gap.where(gap < m["p_src"], m["p_src"])
    parts = {"seller_unbound": (unb, gap), "double_count": (pri, dc), "trade_limits": (pri, gap - dc), "voluntary": (vol, gap)}
    out = []
    for k, (sel, w) in parts.items():
        d = m[sel]
        out.append(pd.DataFrame({"t": d["t"], "item": f"wedge|{k}", "Value": (d["Value"] * w[sel]).astype(float)}))
    for k, sel in (("seller_unbound", unb), ("seller_priced", pri), ("voluntary", vol)):
        out.append(pd.DataFrame({"t": m.loc[sel, "t"], "item": f"Q|{k}", "Value": m.loc[sel, "Value"].astype(float)}))
    out = pd.concat(out, ignore_index=True).groupby(["t", "item"], as_index=False)["Value"].sum()
    d = m[pri]
    ratio = (d["p_dst"] / d["p_src"]).groupby(d["t"]).min()          # smallest buyer/seller price ratio
    out = pd.concat([out, pd.DataFrame({"t": ratio.index, "item": "min_ratio|seller_priced", "Value": ratio.values})])
    out["t"] = out["t"].astype("int64")
    return out[["t", "item", "Value"]].sort_values(["item", "t"]).reset_index(drop=True)


STATE_CENDIV = paths.REPO / "inputs" / "zones" / "state_groups.csv"


SEASON = {12: "winter", 1: "winter", 2: "winter", 3: "spring", 4: "spring", 5: "spring",
          6: "summer", 7: "summer", 8: "summer", 9: "fall", 10: "fall", 11: "fall"}


def reduce_run_hourly(h5path, first_year: int = 2026) -> pd.DataFrame:
    """Energy value by technology group and time of day of one run (protocol amendment A17).

    Long table ``t, season, hod, item, Value`` over the representative timeslices of each solve year
    from ``first_year``. A timeslice label ``y2012d004h003`` gives the weather year, the day of year and the
    hour-ending of a chunk (``reeds/input_processing/hourly_writetimeseries.py``, chunks are hour-ending;
    ``reeds/timeseries.py::h2timestamp`` places them at UTC-6). ``season`` comes from the month of that day
    (winter = Dec-Feb, spring = Mar-May, summer = Jun-Aug, fall = Sep-Nov); ``hod`` is the hour-ending.

    Items, each summed over the zones and the timeslices of one (season, hod) cell:

    ============  ======================================================================================
    load_MWh      reqt_quant(load) (MWh; includes Canadian exports, as in P_E)
    load_pay      reqt_price(load) x reqt_quant(load) (2004 $); the cells sum to P_E of :func:`reduce_run`
    gen_MWh|g     gen_h x hours of the technologies in owner group g (``aglib.ledger.group``); storage = discharge
    gen_val|g     gen_h x hours x the zone's load price (2004 $): the energy value of g's output
    ============  ======================================================================================

    Capture price of g = gen_val|g / gen_MWh|g; load-weighted price = load_pay / load_MWh.
    """
    import h5py

    from aglib.ledger import group

    name = Path(h5path).name
    with h5py.File(h5path, "r") as f:
        price = _key(f, name, "reqt_price")
        quant = _key(f, name, "reqt_quant")
        hours = _key(f, name, "hours").rename(columns={"Value": "hours"})
        gen = _key(f, name, "gen_h")

    def cat(df):
        d = df[(df["*"] == "load") & (df["t"] >= first_year)].rename(columns={"*.2": "allh"})
        return d[["r", "allh", "t", "Value"]]

    p = cat(price).rename(columns={"Value": "p"})
    q = cat(quant).rename(columns={"Value": "q"})
    lab = pd.Series(sorted(set(p["allh"]) | set(hours["allh"])), name="allh")
    lab = lab[lab.str.match(r"^y\d{4}d\d{3}h\d{3}$")]
    day = pd.to_datetime(lab.str[1:5] + lab.str[6:9], format="%Y%j")
    cells = pd.DataFrame({"allh": lab, "season": day.dt.month.map(SEASON).values,
                          "hod": lab.str[-3:].astype(int).values})

    m = p.merge(q, on=["r", "allh", "t"]).merge(cells, on="allh")
    load = (m.assign(load_MWh=m.q, load_pay=m.p * m.q)
             .groupby(["t", "season", "hod"])[["load_MWh", "load_pay"]].sum()
             .stack().rename("Value").reset_index().rename(columns={"level_3": "item"}))

    g = gen[gen["t"] >= first_year].merge(hours, on="allh").merge(cells, on="allh")
    g = g.merge(p, on=["r", "allh", "t"], how="left").fillna({"p": 0.0})
    g = g.assign(grp=g["i"].map(lambda i: group(str(i))), MWh=g.Value * g.hours)
    g = g.assign(val=g.MWh * g.p).groupby(["t", "season", "hod", "grp"])[["MWh", "val"]].sum().reset_index()
    rows = [g.assign(item="gen_MWh|" + g.grp, Value=g.MWh), g.assign(item="gen_val|" + g.grp, Value=g.val)]
    out = pd.concat([load, *[r[["t", "season", "hod", "item", "Value"]] for r in rows]], ignore_index=True)
    out["t"] = out["t"].astype("int64")
    return out.sort_values(["item", "t", "season", "hod"]).reset_index(drop=True)


def zone_cendiv() -> pd.Series:
    """Census division of each zone of the runs' zone set: zone -> state (hierarchy) -> division (state_groups)."""
    st = pd.read_csv(ZONE_STATE).set_index("r")["st"]
    return st.map(pd.read_csv(STATE_CENDIV).set_index("st")["cendiv"])


def reduce_run_cendiv(h5path) -> pd.DataFrame:
    """Census-division items of one run as a long table ``cendiv, t, item, Value`` (protocol amendment A16).

    Units are those of :func:`reduce_run`. Items, each summed over the zones of one division:

    ``P_E``, ``P_C``, ``P_R``, ``Q_E``     consumer payments and energy as in :func:`reduce_run`, at the load zone
    ``P_H2_E``, ``P_H2_C``               H2/DAC electricity payments, at the load zone
    ``X_can``                            exports to Canada (energy): revenue(load; can-imports) - expenditure_flow_int
    ``rev|<rev_cat>|<group>``            market revenue by category and technology group (``ledger.group``)
    ``tb|<kind>|<group>``                ``systemcost_techba`` rows by technology group; kind = ``itc`` (ITC credit),
                                         ``credit`` (other credits), ``fuel_gc`` (objective fuel of gas-curve techs,
                                         before the A6 scaling), ``op`` (other operating), ``inv`` (capital)
    ``sc|inv``, ``sc|op``, ``sc|acp``    ``systemcost_ba`` without credits and ACP (resource cost), and ACP

    Congestion rent, taxes and gas producers stay national: they have no single division.
    """
    import h5py

    from aglib import ledger as L

    cd = zone_cendiv()
    name = Path(h5path).name
    with h5py.File(h5path, "r") as f:
        price = _key(f, name, "reqt_price")
        quant = _key(f, name, "reqt_quant")
        hours = _key(f, name, "hours").rename(columns={"Value": "hours"})
        prod = _key(f, name, "prod_load")
        rev = _key(f, name, "revenue")
        xint = _key(f, name, "expenditure_flow_int")
        tb = _key(f, name, "systemcost_techba")
        sba = _key(f, name, "systemcost_ba")
        sc = _key(f, name, "systemcost")

    def by(df, item, value="Value"):
        if df is None or not len(df):
            return None
        d = df.assign(cendiv=df["r"].map(cd)).groupby(["cendiv", "t"], as_index=False)[value].sum()
        return d.rename(columns={value: "Value"}).assign(item=item)

    def cat(df, c, extra=()):
        d = df[df["*"] == c].rename(columns={"*.2": "allh"})
        return d[["r", *extra, "allh", "t", "Value"]] if "allh" in d else d

    p_load = cat(price, "load").rename(columns={"Value": "p"})
    q_load = cat(quant, "load").rename(columns={"Value": "q"})
    p_rm = cat(price, "res_marg").rename(columns={"Value": "p"})
    q_rm = cat(quant, "res_marg").rename(columns={"Value": "q"})
    p_rps = price[price["*"] == "state_rps"][["*.1", "r", "t", "Value"]].rename(columns={"Value": "p"})
    q_rps = quant[quant["*"] == "state_rps"][["*.1", "r", "t", "Value"]].rename(columns={"Value": "q"})

    parts = []
    m = p_load.merge(q_load, on=["r", "allh", "t"])
    parts.append(by(m.assign(v=m.p * m.q), "P_E", "v"))
    m = p_rm.merge(q_rm, on=["r", "allh", "t"])
    parts.append(by(m.assign(v=m.p * m.q), "P_C", "v"))
    m = p_rps.merge(q_rps, on=["*.1", "r", "t"])
    parts.append(by(m.assign(v=m.p * m.q), "P_R", "v"))
    parts.append(by(q_load, "Q_E", "q"))
    if prod is not None:
        pl = prod.groupby(["r", "allh", "t"], as_index=False)["Value"].sum()
        m = pl.merge(p_load, on=["r", "allh", "t"]).merge(hours, on="allh")
        parts.append(by(m.assign(v=m.Value * m.p * m.hours), "P_H2_E", "v"))
        m = pl.merge(p_rm, on=["r", "allh", "t"])
        parts.append(by(m.assign(v=m.Value * m.p), "P_H2_C", "v"))

    imp = rev[(rev["rev_cat"] == "load") & (rev["i"] == "can-imports")][["r", "t", "Value"]]
    x = pd.concat([imp, xint.assign(Value=-xint["Value"])[["r", "t", "Value"]] if xint is not None else None])
    parts.append(by(x, "X_can"))

    rev = rev.assign(item="rev|" + rev["rev_cat"] + "|" + rev["i"].map(L.group))
    parts.append(rev.assign(cendiv=rev["r"].map(cd)).groupby(["cendiv", "t", "item"], as_index=False)["Value"].sum())

    tb = tb[tb["sys_costs"].isin(set(sc["sys_costs"]))].copy()
    credit = tb["sys_costs"].str.contains(L.CREDIT)
    kind = pd.Series("op", index=tb.index)
    kind[tb["sys_costs"].str.startswith("inv_")] = "inv"
    kind[(tb["sys_costs"] == "op_fuelcosts_objfn") & tb["i"].map(L.on_gas_curve)] = "fuel_gc"
    kind[credit] = "credit"
    kind[credit & tb["sys_costs"].str.contains(L.ITC)] = "itc"
    tb = tb.assign(item="tb|" + kind + "|" + tb["i"].map(L.group), Value=tb["Value"].astype(float))
    parts.append(tb.assign(cendiv=tb["r"].map(cd)).groupby(["cendiv", "t", "item"], as_index=False)["Value"].sum())

    nc = ~sba["sys_costs"].str.contains(L.CREDIT) & (sba["sys_costs"] != L.ACP)
    parts.append(by(sba[nc & sba["sys_costs"].str.startswith("inv_")], "sc|inv"))
    parts.append(by(sba[nc & sba["sys_costs"].str.startswith("op_")], "sc|op"))
    parts.append(by(sba[sba["sys_costs"] == L.ACP], "sc|acp"))

    out = pd.concat([p for p in parts if p is not None], ignore_index=True)
    assert out["cendiv"].notna().all(), "every zone maps to a census division"
    out["t"] = out["t"].astype("int64")
    return out[["cendiv", "t", "item", "Value"]].sort_values(["item", "cendiv", "t"]).reset_index(drop=True)


def reduce_cases(batch: str, cases, out=None, verbose: bool = True, fn=None, fname="derived_ledger.parquet",
                 skip_existing: bool = False) -> Path:
    """Run ``fn`` (default :func:`reduce_run`) over ``cases`` of ``batch`` and merge into ``<out>/<batch>/<fname>``.

    Rows of cases already in the file are replaced; other cases are kept. For the census-division items pass
    ``fn=reduce_run_cendiv, fname="derived_cendiv.parquet"``. With ``skip_existing``, cases already in the file
    are not reduced again (delete the file to force a rebuild after a change to ``fn``).
    """
    fn = fn or reduce_run
    out = Path(out or paths.RESULTS / "extracts_ag")
    dst = out / batch / fname
    if skip_existing and dst.exists():
        done = set(pd.read_parquet(dst, columns=["case"])["case"])
        cases = [c for c in cases if c not in done]
        if not cases:
            return dst
    frames = []
    for c in cases:
        p = h5io.run_file(batch, c)
        if not p.exists():
            print(f"WARNING {batch}/{c}: no outputs.h5 at {p}")
            continue
        frames.append(fn(p).assign(case=c))
        if verbose:
            print(f"{batch}/{c}: reduced")
    new = pd.concat(frames, ignore_index=True)
    new = new[["case", *[k for k in new.columns if k != "case"]]]
    if dst.exists():
        old = pd.read_parquet(dst)
        new = pd.concat([old[~old["case"].isin(new["case"].unique())], new], ignore_index=True)
    dst.parent.mkdir(parents=True, exist_ok=True)
    keys = ["case", "item", *(["cendiv"] if "cendiv" in new else []), "t"]
    new.sort_values(keys).to_parquet(dst, engine="pyarrow", compression="zstd", index=False)
    return dst
