"""The paper-AG ledger: money flows and emissions changes of a policy run against its baseline.

Every definition follows ``docs/protocol.md`` (signed 2026-10-28; amendments in its §11). Inputs are
the AG extracts written by notebook 20 (``results/extracts_ag``), the external values in
``data/external`` and two read-only ReEDS files (``postprocessing/air_quality/rcm.h5`` and the z90
county map). No function here opens a ReEDS outputs.h5 file.

Conventions (protocol §3):
* Money stays in 2004 $ until :func:`pv`, which converts to 2025 $ with ``plotstyle.to2025``.
* Solve years before 2026 are dropped. A key missing at a solve year means zero (ReEDS drops zeros).
* Annual flows are interpolated linearly between solve years. Lumps (``inv_*`` rows, the ITC, the
  support lump) sit in their solve year.
* Horizon A (amendment A1): flows 2026-2050; each lump becomes 30 payments of lump x CRF from the
  year after its solve year (ReEDS's loan convention), kept to 2050.
* Horizon B: flows 2026-2050, then the 2050 value held for 2051-2080; lumps whole.
* Every account is stored as a *gain level*: the sign is chosen so that run minus baseline is the
  actor's gain. Consumer payments are stored negative, credits as ReEDS reports them (negative =
  money to owners), owner revenue positive and owner costs negative.
"""

from __future__ import annotations

import re
from itertools import product

import numpy as np
import pandas as pd

from nlpaper import paths, plotstyle as ps

EXTRACTS_AG = paths.RESULTS / "extracts_ag"
EXTERNAL = paths.DATA / "external"
Y_A = np.arange(2026, 2051)
Y_B = np.arange(2026, 2081)
ANNUITY_YEARS = 30
DEV_RATE = 0.053585                     # ReEDS post-2026 real system rate (1/CRF = pvf_onm = 14.7645)
PVF_PAPER1 = 14.7645                    # paper 1's shadow-price-to-support factor
QUAD_MMBTU = 1e9                        # MMBtu per quad
TO2025_FROM_2004 = ps.to2025(2004)      # computed once: plotstyle.to2025 reads the deflator CSV on every call
RATES = {"1.5%": 0.015, "2.0%": 0.02, "2.5%": 0.025, "3%": 0.03, "7%": 0.07, "5.36%": DEV_RATE}
# carbon-value basis -> (rate key paired with it, protocol §9 item 6)
SCC_PAIRS = {"global EPA2023 1.5%": "1.5%", "global EPA2023 2.0%": "2.0%", "global EPA2023 2.5%": "2.5%",
             "domestic EPA2019 3%": "3%", "domestic EPA2019 7%": "7%"}
MCPF = [1.0, 1.25, 1.33]
PHI = [0.0, 0.067, 0.42]
HEALTH = [f"{m} {c}" for m in ("AP2", "EASIUR", "InMAP") for c in ("ACS", "H6C")]
GHG = ["CO2", "CH4", "N2O"]
# allowance variants (protocol §9 item 1; amendments A14-A15). "none" = no programme has a price in run or baseline
ALLOWANCE = {"national": ("free", "auctioned"), "state": ("free", "auctioned", "policy")}
ALLOW_ENTRY = {"national": "allowances: national cap", "state": "allowances: state programmes"}
# "policy" for the state scope (amendment A20; review page item 13): each programme as actual state policy.
# RGGI auctioned; the CA cap auctioned, with a share of the receipts returned to electricity consumers
# (CARB summary of proceeds, FY2025-26: utilities $2,445.1M of $5,820.1M; provisional, item 15);
# the DE and NJ caps kept by emitters, because the laws behind them create no allowances.
STATE_POLICY = {"CA": "auctioned_split", "DE": "free", "NJ": "free"}
CA_UTILITY_SHARE = 0.42
ZONE_STATE = pd.read_csv(paths.REPO / "inputs" / "zones" / "z90" / "hierarchy.csv").set_index("r")["st"]
RGGI_STATES = set(pd.read_csv(paths.REPO / "inputs" / "emission_constraints" / "rggi_states.csv")["*st"])

# ---------------------------------------------------------------------------
# Technology groups (protocol §4.5)
# ---------------------------------------------------------------------------
GROUPS = ["SMR (new)", "existing nuclear", "gas", "coal", "wind + solar", "hydro", "storage",
          "Canadian imports", "H2 and DAC production", "other"]


def group(i: str) -> str:
    s = i.lower()
    if s == "nuclear-smr":
        return "SMR (new)"
    if s == "nuclear":
        return "existing nuclear"
    if s == "can-imports":
        return "Canadian imports"
    if s == "electrolyzer" or s.startswith("dac"):
        return "H2 and DAC production"
    if s.startswith(("battery", "pumped")):
        return "storage"
    if s.startswith(("wind", "upv", "dupv", "distpv", "csp")):
        return "wind + solar"
    if s.startswith("hyd"):
        return "hydro"
    if s.startswith("coal"):
        return "coal"
    if s.startswith(("gas-cc", "gas-ct")) or s == "o-g-s":
        return "gas"
    return "other"      # biopower, beccs, landfill gas, geothermal, H2-CC/CT


def owner_actor(g: str) -> str:
    # Canadian imports are sold by foreign owners: their profit leaves the US ledger (amendment A11)
    return "foreign sellers: Canadian imports" if g == "Canadian imports" else f"owners: {g}"


def on_gas_curve(i: str) -> bool:
    """Technologies whose fuel ReEDS prices on the gas supply curve (gascost_cendiv). o-g-s is not one."""
    return i.lower().startswith(("gas-cc", "gas-ct"))


CREDIT = re.compile(r"payments_negative|incentive_negative")   # credits: transfers, not resource costs
ITC = re.compile(r"^inv_itc_payments_negative")
ACP = "op_acp_compliance_costs"                                 # alternative compliance payments: to states


# ---------------------------------------------------------------------------
# Extract access
# ---------------------------------------------------------------------------
_CACHE: dict = {}


def _read(batch, key):
    k = (batch, key)
    if k not in _CACHE:
        f = EXTRACTS_AG / batch / f"{key}.parquet"
        _CACHE[k] = pd.read_parquet(f) if f.exists() else pd.DataFrame(columns=["case", "t", "Value"])
    return _CACHE[k]


def _sel(batch, key, case):
    d = _read(batch, key)
    d = d[d["case"] == case].drop(columns="case").copy()
    if len(d):
        d["t"] = d["t"].astype(int)
    return d


def _by_t(d, years):
    s = d.groupby("t")["Value"].sum() if len(d) else pd.Series(dtype=float)
    return s.reindex(years).fillna(0.0).astype(float)


# ---------------------------------------------------------------------------
# External values
# ---------------------------------------------------------------------------
def deflate_to_2004(dollar_year: int) -> float:
    """Multiplier from ``dollar_year`` dollars to 2004 dollars (ReEDS's deflator series)."""
    return ps.to2025(dollar_year) / ps.to2025(2004)


def load_external():
    """Gas quantities (MMBtu/yr by year), carbon values (2004 $/t by year) and CACES damages (2004 $/t)."""
    ext = {}
    q = pd.read_csv(EXTERNAL / "aeo_gas_nonpower_quads.csv")
    q["row_code"] = q["row_code"].astype(str)
    rows = {"1", "2", "3a", "3c", "4a"}                                  # protocol §9 item 7
    pick = lambda codes: q[q["row_code"].isin(codes)].groupby("year")["quantity"].sum() * QUAD_MMBTU
    ext["Q_np"] = pick(rows)
    ext["Q_np_sensitivity"] = {"with pipeline fuel": pick(rows | {"4b"}),
                               "with liquefaction fuel": pick(rows | {"4c"}),
                               "without H2 feedstock": pick(rows - {"3c"})}
    heat = pd.read_csv(EXTERNAL / "gas_heat_content.csv")
    h = heat[heat["measure"].str.startswith("Natural Gas Consumption, Total Heat Content") & (heat["year"] == 2025)]
    ext["export_btu_per_cf"] = float(h["value"].iloc[0])                 # MER Table A4, 2025 (S30)
    x = pd.read_excel(EXTERNAL / "aeo2026_cb2026_aeotab13.xlsx", header=None)
    hdr = list(x.iloc[9])
    ni = x[x[0].astype(str).str.contains("ca_NetImports", na=False)].iloc[0]
    tcf_mmbtu = 1e12 * ext["export_btu_per_cf"] / 1e6
    ext["Q_exp"] = pd.Series({int(y): -float(ni[i]) * tcf_mmbtu for i, y in enumerate(hdr)
                              if isinstance(y, (int, float, np.integer, np.floating)) and 2025 <= y <= 2050})
    # carbon values -> 2004 $ per tonne, by (basis, gas) as Series over emission year
    sc = pd.read_csv(EXTERNAL / "sc_ghg_epa2023.csv")
    scc = {}
    for rate in ("1.5%", "2.0%", "2.5%"):
        for g in GHG:
            d = sc[(sc["gas"] == g) & (sc["discount_rate"] == rate)]
            scc[(f"global EPA2023 {rate}", g)] = (d.set_index("emission_year")["value"]
                                                   * deflate_to_2004(int(d["dollar_year"].iloc[0])))
    dom = pd.read_csv(EXTERNAL / "sc_co2_domestic.csv")
    dom = dom[dom["estimate"].str.contains("EPA 2019 interim domestic", na=False)
              & dom["estimate"].str.contains("average", na=False)]
    for rate in ("3%", "7%"):
        d = dom[dom["discount_rate"].str.startswith(rate)]
        s = d.set_index("emission_year")["value"] * deflate_to_2004(int(d["dollar_year"].iloc[0]))
        scc[(f"domestic EPA2019 {rate}", "CO2")] = s
        for g in ("CH4", "N2O"):                       # the domestic sensitivity values CO2 only
            scc[(f"domestic EPA2019 {rate}", g)] = s * 0.0
    ext["scc"] = scc
    ext["md"] = marginal_damages()
    return ext


def marginal_damages() -> pd.DataFrame:
    """CACES marginal damages by ReEDS zone, model and C-R function (2004 $/t), as ReEDS's own
    ``health_damage_calculations.py:get_marginal_damage_rates`` computes them: annual season only,
    counties mapped to z90 zones, simple mean over the counties of each zone."""
    import h5py
    with h5py.File(paths.REPO / "postprocessing" / "air_quality" / "rcm.h5", "r") as f:
        g = f["data"]
        cols = [c.decode() for c in g["columns"][:]]
        dollar_year = int(g.attrs["dollar_year"])                          # 2017
        md = pd.DataFrame({c: (lambda a: a.astype(str) if a.dtype.kind == "S" else a)(g[c][:]) for c in cols})
    md = md[md["season"] == "annual"]
    c2z = pd.read_csv(paths.REPO / "inputs" / "zones" / "z90" / "county2zone.csv", dtype=str)
    c2z["FIPS"] = c2z["FIPS"].str.zfill(5)
    md["FIPS"] = md["FIPS"].str.zfill(5)
    md = md.merge(c2z, on="FIPS", how="inner")
    out = md.groupby(["r", "model", "cr", "pollutant"], as_index=False)["damage"].mean()
    out["pollutant"] = out["pollutant"].str.upper()
    out["damage"] *= deflate_to_2004(dollar_year)
    out["variant"] = out["model"] + " " + out["cr"]
    return out


def crf_after_2026() -> float:
    c = pd.read_csv(paths.DATA / "reeds_inputs" / "crf.csv")
    c.columns = ["t", "crf"]
    return float(c.loc[c["t"] >= 2026, "crf"].iloc[0])


def series_on(years, s: pd.Series) -> np.ndarray:
    """A by-year series on ``years``: linear inside its range, flat outside."""
    s = s.sort_index()
    return np.interp(years, s.index.values.astype(float), s.values.astype(float))


# ---------------------------------------------------------------------------
# Accounts of one run (gain levels at solve years >= 2026, 2004 $)
# ---------------------------------------------------------------------------
def accounts(batch: str, case: str, ext: dict) -> tuple[pd.DataFrame, dict]:
    """Long table ``actor, entry, kind, t, Value`` plus a dict of memo series for the checks."""
    years = np.array(sorted(_sel(batch, "pvf_onm", case)["t"]))
    years = years[years >= 2026]
    rows = []

    def add(actor, entry, kind, s):
        s = s.reindex(years).fillna(0.0).astype(float)
        rows.append(pd.DataFrame({"actor": actor, "entry": entry, "kind": kind, "t": years, "Value": s.values}))

    der = _sel(batch, "derived_ledger", case)
    der = der.pivot_table(index="t", columns="item", values="Value", aggfunc="sum").reindex(years).fillna(0.0)
    it = lambda k: der[k] if k in der else pd.Series(0.0, index=years)

    # 4.1 electricity consumers. P_E includes exports to Canada; their energy payment X leaves the US
    # ledger (amendment A10): X = value of Canadian imports - expenditure_flow_int (report.gms)
    rev_all = _sel(batch, "revenue_nat", case)
    imp = _by_t(rev_all[(rev_all["rev_cat"] == "load") & (rev_all["i"] == "can-imports")], years)
    x_can = imp - _by_t(_sel(batch, "expenditure_flow_int", case), years)
    add("electricity consumers", "energy payments", "flow", -(it("P_E") - x_can))
    add("foreign buyers", "electricity: exports to Canada (energy)", "flow", -x_can)
    add("electricity consumers", "capacity payments", "flow", -it("P_C"))
    add("electricity consumers", "RPS payments", "flow", -it("P_R"))

    # 4.2 / 4.6 gas
    p = _by_t(_sel(batch, "repgasprice_nat", case), years)            # 2004 $/MMBtu
    q_pow = _by_t(_sel(batch, "repgasquant_nat", case), years) * QUAD_MMBTU
    q_np = pd.Series(series_on(years, ext["Q_np"]), index=years)
    q_exp = pd.Series(series_on(years, ext["Q_exp"]), index=years)
    g_obj = _by_t(_sel(batch, "gascost_cendiv", case), years)
    add("non-power gas consumers", "gas purchases", "flow", -p * q_np)
    add("gas producers", "sales: power sector", "flow", p * q_pow)
    add("gas producers", "sales: non-power", "flow", p * q_np)
    add("gas producers", "sales: exports", "flow", p * q_exp)
    add("foreign buyers", "gas: exports", "flow", -p * q_exp)
    add("gas producers", "supply cost (ReEDS objective)", "flow", -g_obj)

    # 4.3 taxpayers: credit rows of systemcost (negative = credit paid), ACP receipts
    sc = _sel(batch, "systemcost", case)
    sc = sc[sc["t"] >= 2026]
    cr = sc[sc["sys_costs"].str.contains(CREDIT)]
    add("taxpayers", "credits: ITC", "lump", _by_t(cr[cr["sys_costs"].str.contains(ITC)], years))
    add("taxpayers", "credits: PTC and 45Q", "flow",
        _by_t(cr[cr["sys_costs"].isin(["op_ptc_payments_negative", "op_co2_incentive_negative"])], years))
    add("taxpayers", "credits: H2 PTC", "flow", _by_t(cr[cr["sys_costs"] == "op_h2_ptc_payments_negative"], years))
    add("taxpayers", "state ACP receipts", "flow", _by_t(sc[sc["sys_costs"] == ACP], years))

    # 4.4 / 4.5 owners by technology group
    rev = _sel(batch, "revenue_nat", case)
    rev = rev[rev["t"] >= 2026].assign(g=lambda d: d["i"].map(group))
    tb = _sel(batch, "systemcost_techba", case)
    tb = tb[(tb["t"] >= 2026) & tb["sys_costs"].isin(set(sc["sys_costs"]))].assign(g=lambda d: d["i"].map(group))
    tb["Value"] = tb["Value"].astype(float)
    # generators pay the marginal gas price: scale the objective gas cost of gas-curve techs to p x Q_power
    fuel = (tb["sys_costs"] == "op_fuelcosts_objfn") & tb["i"].map(on_gas_curve)
    scale = (p * q_pow / g_obj.where(g_obj != 0)).fillna(1.0)
    tb.loc[fuel, "Value"] = tb.loc[fuel, "Value"] * tb.loc[fuel, "t"].map(scale).values
    for g in GROUPS:
        a = owner_actor(g)
        for cat in ("load", "res_marg", "rps", "charge"):
            add(a, f"revenue: {cat}", "flow", _by_t(rev[(rev["g"] == g) & (rev["rev_cat"] == cat)], years))
        t_g = tb[tb["g"] == g]
        crg = t_g[t_g["sys_costs"].str.contains(CREDIT)]
        add(a, "credits received: ITC", "lump", -_by_t(crg[crg["sys_costs"].str.contains(ITC)], years))
        add(a, "credits received: PTC, 45Q, H2 PTC", "flow",
            -_by_t(crg[~crg["sys_costs"].str.contains(ITC)], years))
        nc = t_g[~t_g["sys_costs"].str.contains(CREDIT)]
        add(a, "operating costs", "flow", -_by_t(nc[nc["sys_costs"].str.startswith("op_")], years))
        add(a, "capital costs", "lump", -_by_t(nc[nc["sys_costs"].str.startswith("inv_")], years))
    add("owners: H2 and DAC production", "electricity payments", "flow", -(it("P_H2_E") + it("P_H2_C")))

    # 4.7 network: congestion rent (includes the hurdle wedge) less system-level rows not in techba
    add("network", "congestion rent: energy", "flow", it("CR_E") + it("CR_E_vsc"))
    add("network", "congestion rent: capacity", "flow", it("CR_C") + it("CR_C_vsc"))
    # system-level rows = systemcost minus the unscaled techba rows (transmission, converters, spur-line
    # FOM, H2 network); credit rows and ACP are excluded here and handled above
    sc_nc = sc[~sc["sys_costs"].str.contains(CREDIT) & (sc["sys_costs"] != ACP)]
    tb_raw = _sel(batch, "systemcost_techba", case)
    tb_raw = tb_raw[(tb_raw["t"] >= 2026) & tb_raw["sys_costs"].isin(set(sc_nc["sys_costs"]))]
    gap = sc_nc.groupby(["sys_costs", "t"])["Value"].sum().sub(
        tb_raw.groupby(["sys_costs", "t"])["Value"].sum(), fill_value=0.0).rename("Value").reset_index()
    add("network", "capital costs (system-level rows)", "lump", -_by_t(gap[gap["sys_costs"].str.startswith("inv_")], years))
    add("network", "operating costs (system-level rows)", "flow", -_by_t(gap[gap["sys_costs"].str.startswith("op_")], years))

    # support (mandate runs): lump = shadow price x pvf_onm x new SMR MW; rental = shadow price x SMR fleet
    dual = _by_t(_sel(batch, "nuclear_cap_price", case), years)
    pvf = _by_t(_sel(batch, "pvf_onm", case), years)
    cn = _sel(batch, "cap_new_ivrt", case)
    cap = _sel(batch, "cap_nat", case)
    new_mw = _by_t(cn[cn["i"] == "nuclear-smr"], years)
    fleet_mw = _by_t(cap[cap["i"] == "nuclear-smr"], years)
    add("support", "lump", "lump", dual * pvf * new_mw)
    add("support", "rental", "flow", dual * fleet_mw)

    # resource cost (view 2): systemcost without credits and ACP
    add("system", "resource cost: capital", "lump", -_by_t(sc_nc[sc_nc["sys_costs"].str.startswith("inv_")], years))
    add("system", "resource cost: operating", "flow", -_by_t(sc_nc[sc_nc["sys_costs"].str.startswith("op_")], years))

    # 4.8 allowance values (amendments A14-A15). ReEDS prices each carbon cap as a constraint, so nobody
    # pays for allowances: under free allocation the value stays with the emitters (inside market revenue;
    # for imports into a state cap, inside the congestion rent). The "allowance" rows carry the auctioned
    # variant: emitters pay price x covered process CO2, governments receive price x covered emissions.
    eirt = _sel(batch, "emit_irt", case)
    if len(eirt):
        eirt = eirt[(eirt["etype"] == "process") & (eirt["eall"] == "CO2") & (eirt["t"] >= 2026)]
        eirt = eirt.assign(g=eirt["i"].map(group), st=eirt["r"].map(ZONE_STATE))
    else:
        eirt = pd.DataFrame(columns=["i", "r", "t", "Value", "g", "st"])
    e_g = lambda d, g: _by_t(d[d["g"] == g], years)
    # national cap: CO2 only, process emissions only (GSw_AnnualCap = 1, GSw_Upstream = 0); DAC removals,
    # which are negative emissions, earn the price (amendment A15)
    co2p = _by_t(_sel(batch, "co2_price", case), years)
    for g in GROUPS:
        add("allowance", f"national|{owner_actor(g)}", "flow", -co2p * e_g(eirt, g))
    add("allowance", "national|taxpayers", "flow", co2p * _by_t(eirt, years))
    # state programmes: a state cap covers in-state process CO2 plus imports at the sending zone's rate
    # (eq_state_cap). A positive price means the cap binds, so the import part = cap - in-state emissions;
    # the network actor pays it, because it holds that value in the congestion rent. RGGI covers in-region
    # process CO2 (eq_RGGI_cap).
    sp, sq = _sel(batch, "state_cap_and_trade_price", case), _sel(batch, "state_cap_and_trade_quant", case)
    zero = lambda: pd.Series(0.0, index=years)
    st_pay, pol_pay = {g: zero() for g in GROUPS}, {g: zero() for g in GROUPS}
    st_imp, st_rec, pol_imp, pol_rec, pol_cons = zero(), zero(), zero(), zero(), zero()
    for st in (sp["st"].unique() if len(sp) else []):
        pr = _by_t(sp[sp["st"] == st], years)
        if not pr.abs().sum():
            continue
        es = eirt[eirt["st"] == st]
        cap_st = _by_t(sq[sq["st"] == st], years)
        pay = {g: pr * e_g(es, g) for g in GROUPS}
        imp, rec = pr * (cap_st - _by_t(es, years)), pr * cap_st
        for g in GROUPS:
            st_pay[g] = st_pay[g] + pay[g]
        st_imp, st_rec = st_imp + imp, st_rec + rec
        rule = STATE_POLICY[st]                    # a state cap outside the map stops the ledger
        if rule == "auctioned_split":
            for g in GROUPS:
                pol_pay[g] = pol_pay[g] + pay[g]
            pol_imp = pol_imp + imp
            pol_cons = pol_cons + CA_UTILITY_SHARE * rec
            pol_rec = pol_rec + (1 - CA_UTILITY_SHARE) * rec
    rp = _by_t(_sel(batch, "rggi_price", case), years)
    er = eirt[eirt["st"].isin(RGGI_STATES)]
    for g in GROUPS:
        st_pay[g] = st_pay[g] + rp * e_g(er, g)
        pol_pay[g] = pol_pay[g] + rp * e_g(er, g)
    st_rec = st_rec + rp * _by_t(er, years)
    pol_rec = pol_rec + rp * _by_t(er, years)
    rggi_slack = rp * (_by_t(_sel(batch, "rggi_quant", case), years) - _by_t(er, years))
    for g in GROUPS:
        add("allowance", f"state|{owner_actor(g)}", "flow", -st_pay[g])
    add("allowance", "state|network", "flow", -st_imp)
    add("allowance", "state|taxpayers", "flow", st_rec)
    for g in GROUPS:
        add("allowance", f"statepol|{owner_actor(g)}", "flow", -pol_pay[g])
    add("allowance", "statepol|network", "flow", -pol_imp)
    add("allowance", "statepol|taxpayers", "flow", pol_rec)
    add("allowance", "statepol|electricity consumers", "flow", pol_cons)

    # emissions (tonnes; the environment entries are valued after differencing)
    em = _sel(batch, "emit_nat", case)
    for gname in GHG:
        for et in ("process", "upstream"):
            add("emissions", f"{gname} {et}", "flow", _by_t(em[(em["eall"] == gname) & (em["etype"] == et)], years))

    memo = dict(years=years, p=p, q_pow=q_pow, q_np=q_np, q_exp=q_exp, g_obj=g_obj, dual=dual, pvf=pvf,
                new_mw=new_mw, fleet_mw=fleet_mw, der=der,
                rev=rev.groupby(["rev_cat", "t"])["Value"].sum().unstack(0).reindex(years).fillna(0.0),
                hurdle=_by_t(_sel(batch, "tran_hurdle_cost_ann", case), years),
                tax_itc=_by_t(_sel(batch, "tax_expenditure_itc", case), years),
                tax_ptc=_by_t(_sel(batch, "tax_expenditure_ptc", case), years),
                acp=_by_t(sc[sc["sys_costs"] == ACP], years),
                gas_curve_fuel=_by_t(tb_raw[(tb_raw["sys_costs"] == "op_fuelcosts_objfn")
                                            & tb_raw["i"].map(on_gas_curve)], years),
                credit_sys=_by_t(cr, years),
                credit_tb=_by_t(tb[tb["sys_costs"].str.contains(CREDIT)], years),
                emit_r=_sel(batch, "emit_r", case),
                co2_price=co2p, state_import_part=st_imp, rggi_slack=rggi_slack,
                allowance_live={"national": bool(co2p.abs().sum()), "state": bool(st_rec.abs().sum())},
                co2_process_irt=_by_t(eirt, years),
                co2_process_nat=_by_t(_sel(batch, "emit_nat", case).query("eall == 'CO2' and etype == 'process'"),
                                      years))
    return pd.concat(rows, ignore_index=True), memo


# ---------------------------------------------------------------------------
# Time handling
# ---------------------------------------------------------------------------
def flow(s: pd.Series, horizon: str) -> np.ndarray:
    a = np.interp(Y_A, s.index.values.astype(float), s.values.astype(float))
    if horizon == "A":
        return a
    return np.concatenate([a, np.full(len(Y_B) - len(Y_A), a[-1])])


def lump(s: pd.Series, horizon: str, crf: float) -> np.ndarray:
    yrs = Y_A if horizon == "A" else Y_B
    out = np.zeros(len(yrs))
    for t, v in s.items():
        if horizon == "B":
            out[yrs == t] += v
        else:
            out[(yrs > t) & (yrs <= t + ANNUITY_YEARS)] += v * crf
    return out


def annual(df: pd.DataFrame, horizon: str, crf: float) -> pd.DataFrame:
    """Rows ``actor, entry`` x columns years: each entry as annual values on the horizon."""
    out = {}
    for (a, e, k), d in df.groupby(["actor", "entry", "kind"], sort=False):
        s = d.set_index("t")["Value"]
        out[(a, e)] = flow(s, horizon) if k == "flow" else lump(s, horizon, crf)
    return pd.DataFrame(out, index=Y_A if horizon == "A" else Y_B).T


def pv(arr, horizon: str, rate: float) -> float:
    """Present value to 2026 in 2025 $B of an annual 2004 $ array on the horizon's years."""
    yrs = Y_A if horizon == "A" else Y_B
    return float((np.asarray(arr) / (1.0 + rate) ** (yrs - 2026)).sum()) * TO2025_FROM_2004 / 1e9


# ---------------------------------------------------------------------------
# One pair: deltas, environment, views, checks
# ---------------------------------------------------------------------------
_ACC: dict = {}


def accounts_cached(batch: str, case: str, ext: dict):
    """``accounts`` memoized per run, so a baseline shared by many pairs is built once. Callers must not
    modify the returned frame or memo."""
    k = (batch, case, id(ext))
    if k not in _ACC:
        _ACC[k] = accounts(batch, case, ext)
    return _ACC[k]


def pair(run: tuple, base: tuple, ext: dict, crf: float, mandate: bool = True) -> dict:
    """Ledger of ``run`` against ``base`` (each a (batch, case) tuple), for both horizons."""
    A, ma = accounts_cached(*run, ext)
    B, mb = accounts_cached(*base, ext)
    if not np.array_equal(ma["years"], mb["years"]):
        raise ValueError(f"solve years differ: {run} vs {base}")
    key = ["actor", "entry", "kind", "t"]
    D = A.merge(B, on=key, how="outer", suffixes=("_run", "_base")).fillna(0.0)
    D["Value"] = D["Value_run"] - D["Value_base"]
    years = ma["years"]

    out = {"years": years, "memo_run": ma, "memo_base": mb, "delta_accounts": D}
    for h in ("A", "B"):
        yrs = Y_A if h == "A" else Y_B
        ann = annual(D[key + ["Value"]], h, crf)
        # environment: GHG at each carbon basis, health at each CACES variant (gain = -damage change)
        env = {}
        for basis in SCC_PAIRS:
            tot = np.zeros(len(yrs))
            for g in GHG:
                de = ann.loc[("emissions", f"{g} process")].values + ann.loc[("emissions", f"{g} upstream")].values
                tot += -de * series_on(yrs, ext["scc"][(basis, g)])
            env[("environment", f"GHG: {basis}")] = tot
        er = pd.concat([ma["emit_r"].assign(s=1.0), mb["emit_r"].assign(s=-1.0)])
        er = er[(er["etype"] == "process") & er["eall"].isin(["NOX", "SO2"]) & (er["t"] >= 2026)]
        for v in HEALTH:
            mdv = ext["md"][ext["md"]["variant"] == v]
            m = er.merge(mdv, left_on=["r", "eall"], right_on=["r", "pollutant"], how="inner")
            dmg = (m["Value"] * m["s"] * m["damage"]).groupby(m["t"]).sum().reindex(years).fillna(0.0)
            env[("environment", f"health: {v}")] = -flow(dmg, h)
        ann = pd.concat([ann, pd.DataFrame(env, index=yrs).T])
        out[h] = ann
    out["checks"] = market_checks(ma, mb)
    return out


def market_checks(ma, mb) -> pd.DataFrame:
    """C1 (energy), C2 (capacity) and the RPS gap per run and for the difference; plus gas and credit echoes."""
    rows = []
    for tag, m in (("run", ma), ("base", mb)):
        der, rev = m["der"], m["rev"]
        g = lambda k: der[k] if k in der else 0.0
        r = lambda k: rev[k] if k in rev else 0.0
        rows.append(pd.DataFrame({
            "who": tag, "t": m["years"],
            "C1_residual": (g("P_E") + g("P_H2_E") - r("load") - r("charge") - g("CR_E")).values,
            "C1_vsc_rent": g("CR_E_vsc").values if hasattr(g("CR_E_vsc"), "values") else 0.0,
            "C1_gross": g("P_E").values,
            "C2_residual": (g("P_C") + g("P_H2_C") - r("res_marg") - g("CR_C")).values,
            "C2_vsc_rent": g("CR_C_vsc").values if hasattr(g("CR_C_vsc"), "values") else 0.0,
            "C2_gross": g("P_C").values,
            "RPS_residual": (g("P_R") - r("rps") - m["acp"]).values,
            "RPS_gross": g("P_R").values,
            "RPS_trade_rent": (g("REC_paid") - g("REC_recv")).values if hasattr(g("REC_paid"), "values") else 0.0,
            "RPS_requirement_minus_RECs_paid": (g("P_R") - g("REC_paid") - m["acp"]).values
            if hasattr(g("REC_paid"), "values") else 0.0,
            "RPS_revenue_minus_RECs_recv": (r("rps") - g("REC_recv")).values if hasattr(g("REC_recv"), "values") else 0.0,
            "gas_curve_fuel_minus_gascost": (m["gas_curve_fuel"] - m["g_obj"]).values,
            "gas_rent_pQ_minus_cost": (m["p"] * m["q_pow"] - m["g_obj"]).values,
            "credit_sys_minus_techba": (m["credit_sys"] - m["credit_tb"]).values,
            "tax_expenditure_echo": (m["tax_itc"] + m["tax_ptc"]).values,
            "hurdle": m["hurdle"].values,
        }))
    return pd.concat(rows, ignore_index=True)


def gain_tables(out: dict, mandate: bool) -> pd.DataFrame:
    """Actor entries as annual gains with the support and its funding attached (horizon, support form,
    funding case). Long table: horizon, support_form, funding, actor, entry, year, Value (2004 $)."""
    rows = []
    for h in ("A", "B"):
        ann = out[h]
        yrs = ann.columns
        forms = {"lump": ann.loc[("support", "lump")].values, "rental": ann.loc[("support", "rental")].values}
        base = ann.drop(index=[k for k in ann.index if k[0] in ("support", "system", "emissions", "allowance")])
        alw = {sc: ann.loc[[k for k in ann.index if k[0] == "allowance" and k[1].startswith(sc + "|")]]
               for sc in (*ALLOW_ENTRY, "statepol")}
        # a scope with no allowance price in run or baseline carries the single key "none"
        keys = {sc: (ALLOWANCE[sc] if (out["memo_run"]["allowance_live"][sc] or out["memo_base"]["allowance_live"][sc])
                     else ("none",)) for sc in ALLOW_ENTRY}
        for form, s in (forms.items() if mandate else [("none", np.zeros(len(yrs)))]):
            for fund, an, ast in product((("T", "R") if mandate else ("none",)), keys["national"], keys["state"]):
                t = base.copy()
                for sc, key in (("national", an), ("state", ast)):
                    if key in ("auctioned", "policy"):
                        for (_, e), v in alw["statepol" if key == "policy" else sc].iterrows():
                            t.loc[(e.split("|", 1)[1], ALLOW_ENTRY[sc]), :] = v.values
                if mandate:
                    t.loc[("owners: SMR (new)", "mandate support"), :] = s
                    payer = ("taxpayers", "mandate support") if fund == "T" else ("electricity consumers", "mandate support charge")
                    t.loc[payer, :] = -s
                t = t.stack().rename("Value").reset_index()
                t.columns = ["actor", "entry", "year", "Value"]
                rows.append(t.assign(horizon=h, support_form=form, funding=fund,
                                     allowance_national=an, allowance_state=ast))
    return pd.concat(rows, ignore_index=True)


VIEW1_ACTORS = ("electricity consumers", "non-power gas consumers", "taxpayers")


def views(out: dict, mandate: bool) -> pd.DataFrame:
    """Both resident views and check C3 for every variant (protocol §5), as PVs in 2025 $B."""
    G = gain_tables(out, mandate)
    res = []
    for (h, form, fund, an, ast), g in G.groupby(["horizon", "support_form", "funding",
                                                  "allowance_national", "allowance_state"]):
        ann = out[h]
        yrs = ann.columns.values
        tab = g.pivot_table(index=["actor", "entry"], columns="year", values="Value", aggfunc="sum")[yrs]
        actor = tab.index.get_level_values(0)
        is_v1 = actor.isin(VIEW1_ACTORS)
        is_pi = actor.str.startswith("owners: ") | actor.isin(["gas producers", "network"])
        is_env = actor == "environment"
        # state receipts (ACP, state allowance auctions) fund state programmes, not federal taxes
        state_rec = tab.index.get_level_values(1).isin(["state ACP receipts", ALLOW_ENTRY["state"]])
        tax_gain = tab[(actor == "taxpayers") & ~state_rec].sum().values
        v1_money = tab[is_v1].sum().values
        pi = tab[is_pi].sum().values
        sc_res = ann.loc[("system", "resource cost: capital")].values + ann.loc[("system", "resource cost: operating")].values
        foreign = tab[actor.str.startswith("foreign")].sum().values          # gains outside the US (amendments A10, A11)
        for basis, rk in SCC_PAIRS.items():
            r = RATES[rk]
            ghg = ann.loc[("environment", f"GHG: {basis}")].values
            for hv in HEALTH:
                env = ghg + ann.loc[("environment", f"health: {hv}")].values
                for m in MCPF:
                    dw = (m - 1.0) * tax_gain
                    v1 = v1_money + dw + env
                    for phi in PHI:
                        v2 = sc_res + dw + env - foreign - phi * pi
                        c3 = v2 - v1 - (1.0 - phi) * pi
                        res.append(dict(horizon=h, support_form=form, funding=fund, allowance_national=an,
                                        allowance_state=ast, scc_basis=basis, rate=rk,
                                        health_model=hv, mcpf=m, phi=phi,
                                        view1=pv(v1, h, r), view2=pv(v2, h, r), profits_domestic=pv((1 - phi) * pi, h, r),
                                        deadweight=pv(dw, h, r), env_ghg=pv(ghg, h, r), env_health=pv(env - ghg, h, r),
                                        minus_d_resource_cost=pv(sc_res, h, r), foreign_gain=pv(foreign, h, r),
                                        C3_residual=pv(c3, h, r)))
    return pd.DataFrame(res)


def actor_pvs(out: dict, mandate: bool) -> pd.DataFrame:
    """Every actor entry as a PV at every rate (2025 $B), per horizon, support form and funding case."""
    G = gain_tables(out, mandate)
    rows = []
    for (h, form, fund, an, ast, a, e), g in G.groupby(["horizon", "support_form", "funding", "allowance_national",
                                                        "allowance_state", "actor", "entry"]):
        v = g.sort_values("year")["Value"].values
        rows.append(dict(horizon=h, support_form=form, funding=fund, allowance_national=an, allowance_state=ast,
                         actor=a, entry=e,
                         **{f"PV_{k}": pv(v, h, r) for k, r in RATES.items()}))
    return pd.DataFrame(rows)
