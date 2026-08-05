"""
pris_loader.py — turn IAEA RDS-2 / PRIS unit-level data into the inputs the
nuclear learning model needs.

WHY THIS EXISTS
---------------
PRIS is a status-and-history database: it has no forward view. It cannot give
international builds through 2050. What it CAN give is:
  (a) the fleet vintage structure  -> a RETIREMENT schedule under a lifetime rule
  (b) the committed pipeline       -> near-term (approx 2025-2035) builds, bottom-up
  (c) completed unit durations     -> the empirical duration panel, by design family

Gross builds through 2050 then come from the identity:

    gross_additions(t) = delta_net_capacity(t) [IAEA RDS-1]  +  retirements(t) [PRIS]

DATA SOURCE (see pris_data_spec.md)
-----------------------------------
The PRIS website disallows automated access (robots.txt) and has no free bulk
export. Use RDS-2 ("Nuclear Power Reactors in the World"), the free annual IAEA
PDF generated FROM PRIS, and extract its tables.

Expected input schema (one row per reactor) - column names are normalized by
`load_units()`, so minor variations are tolerated:

    country, reactor_name, reactor_type, model, capacity_net_mw,
    construction_start, grid_connection, commercial_operation,
    permanent_shutdown (optional), status

Dates from RDS-2 are MONTH precision (e.g. "2013-3"). `parse_pris_date` handles
both "YYYY-M" and full ISO dates.
"""

from __future__ import annotations
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 1. Country -> model region mapping
# ---------------------------------------------------------------------------
# Follows the UN geoscheme groupings that IAEA RDS-1 regions are built on.
# VALIDATED: aggregating PRIS 31-Dec-2023 operating capacity through this map
# reproduces the model's 2024 regional milestones to within ~2.6 GW everywhere
# (SAM matches exactly, confirming Mexico belongs to Latin America, not
# Northern America). See `validate_region_mapping()`.

REGION_OF_COUNTRY = {
    # US and Canada are separate regions in this model (Northern America split)
    "USA": "US", "UNITED STATES OF AMERICA": "US",
    "CANADA": "CA",
    # Latin America and the Caribbean
    "ARGENTINA": "SAM", "BRAZIL": "SAM", "MEXICO": "SAM",
    # Northern, Western and Southern Europe
    "BELGIUM": "WEU", "FINLAND": "WEU", "FRANCE": "WEU", "GERMANY": "WEU",
    "ITALY": "WEU", "LITHUANIA": "WEU", "NETHERLANDS": "WEU", "SLOVENIA": "WEU",
    "SPAIN": "WEU", "SWEDEN": "WEU", "SWITZERLAND": "WEU", "UK": "WEU",
    "UNITED KINGDOM": "WEU",
    # Eastern Europe
    "BELARUS": "EEU", "BULGARIA": "EEU", "CZECH REP.": "EEU", "CZECH REPUBLIC": "EEU",
    "CZECHIA": "EEU", "HUNGARY": "EEU", "POLAND": "EEU", "ROMANIA": "EEU",
    "RUSSIA": "EEU", "RUSSIAN FEDERATION": "EEU", "SLOVAKIA": "EEU", "UKRAINE": "EEU",
    # Africa
    "EGYPT": "AF", "SOUTH AFRICA": "AF",
    # Western Asia
    "ARMENIA": "WA", "IRAN,ISL.REP": "WA", "IRAN, ISLAMIC REPUBLIC OF": "WA",
    "TURKEY": "WA", "TÜRKIYE": "WA", "UAE": "WA", "UNITED ARAB EMIRATES": "WA",
    # Southern Asia
    "BANGLADESH": "SA", "INDIA": "SA", "PAKISTAN": "SA",
    # Central and Eastern Asia
    "CHINA": "CEA", "JAPAN": "CEA", "KAZAKHSTAN": "CEA", "KOREA,REP.OF": "CEA",
    "KOREA, REPUBLIC OF": "CEA", "TAIWAN, CHINA": "CEA", "TAIWAN,CHINA": "CEA", "TAIWAN": "CEA",
    # South-Eastern Asia / Oceania — no units yet, listed for completeness
    "PHILIPPINES": "SEA", "VIET NAM": "SEA", "VIETNAM": "SEA", "INDONESIA": "SEA",
    "AUSTRALIA": "OC",
}
FOREIGN_REGIONS = ["CA", "SAM", "WEU", "EEU", "AF", "WA", "SA", "CEA", "SEA", "OC"]
ALL_REGIONS = ["US"] + FOREIGN_REGIONS


# ---------------------------------------------------------------------------
# 2. Loading / normalization
# ---------------------------------------------------------------------------
_COLUMN_ALIASES = {
    "country": "country", "code": "code",
    "reactor name": "reactor_name", "reactor_name": "reactor_name", "name": "reactor_name",
    "type": "reactor_type", "reactor_type": "reactor_type",
    "model": "model", "reactor model": "model",
    "net": "capacity_net_mw", "capacity_net_mw": "capacity_net_mw",
    "reference unit power (mwe)": "capacity_net_mw", "net capacity mw(e)": "capacity_net_mw",
    "const. start": "construction_start", "construction start": "construction_start",
    "construction_start": "construction_start", "construction_start_date": "construction_start",
    "grid connection": "grid_connection", "grid_connection": "grid_connection",
    "first_grid_connection_date": "grid_connection",
    "comm. operation": "commercial_operation", "commercial operation": "commercial_operation",
    "commercial_operation": "commercial_operation", "commercial_operation_date": "commercial_operation",
    "permanent shutdown": "permanent_shutdown", "permanent_shutdown": "permanent_shutdown",
    "permanent_shutdown_date": "permanent_shutdown",
    "status": "status",
}

REQUIRED = ["country", "reactor_name", "capacity_net_mw", "construction_start", "grid_connection"]


def parse_pris_date(v):
    """RDS-2 prints dates as 'YYYY-M' (month precision). PRIS pages give ISO days."""
    if pd.isna(v) or str(v).strip() in ("", "-", "nan"):
        return pd.NaT
    s = str(v).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y/%m/%d", "%Y/%m"):
        try:
            return pd.to_datetime(s, format=fmt)
        except (ValueError, TypeError):
            continue
    return pd.to_datetime(s, errors="coerce")


def load_units(path_or_df, status=None):
    """Load an RDS-2/PRIS unit table, normalize columns, assign regions."""
    df = path_or_df.copy() if isinstance(path_or_df, pd.DataFrame) else pd.read_csv(path_or_df)
    df.columns = [_COLUMN_ALIASES.get(str(c).strip().lower(), str(c).strip().lower())
                  for c in df.columns]
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"missing required columns: {missing}. Got: {list(df.columns)}")

    for c in ["construction_start", "grid_connection", "commercial_operation", "permanent_shutdown"]:
        if c in df.columns:
            df[c] = df[c].map(parse_pris_date)

    df["capacity_net_mw"] = pd.to_numeric(df["capacity_net_mw"], errors="coerce")
    df["country_key"] = df["country"].astype(str).str.strip().str.upper()
    df["region"] = df["country_key"].map(REGION_OF_COUNTRY)
    if status is not None and "status" in df.columns:
        df = df[df["status"].astype(str).str.lower().str.startswith(status.lower())]
    return df


def validate_units(df, milestones_2024=None):
    """Report data-quality issues rather than failing silently."""
    issues = []
    unmapped = sorted(df.loc[df["region"].isna(), "country_key"].unique())
    if unmapped:
        issues.append(f"UNMAPPED COUNTRIES (add to REGION_OF_COUNTRY): {unmapped}")
    if df["capacity_net_mw"].isna().any():
        issues.append(f"{int(df['capacity_net_mw'].isna().sum())} rows missing net capacity")
    if df["construction_start"].isna().any():
        issues.append(f"{int(df['construction_start'].isna().sum())} rows missing construction_start")
    bad = df.dropna(subset=["construction_start", "grid_connection"])
    rev = bad[bad["grid_connection"] < bad["construction_start"]]
    if len(rev):
        issues.append(f"{len(rev)} rows with grid_connection before construction_start")
    if milestones_2024 is not None:
        agg = df.groupby("region")["capacity_net_mw"].sum() / 1000.0
        for r, m in milestones_2024.items():
            d = agg.get(r, 0.0) - m
            if abs(d) > 6.0:
                issues.append(f"region {r}: PRIS sum {agg.get(r,0):.1f} GW vs model milestone {m:.1f} GW ({d:+.1f})")
    return issues


# ---------------------------------------------------------------------------
# 3. Retirement schedule (the piece PRIS uniquely supplies)
# ---------------------------------------------------------------------------
def retirement_schedule(operating, years, lifetime_years=60.0, region=None,
                        vintage_field="grid_connection"):
    """GW retired per year, from fleet vintage + a licence-life rule.

    lifetime_years is the SCENARIO KNOB: pair a shorter life with the IAEA Low
    net path (no/low LTO) and a longer life with the High path (extensive LTO).
    Applying one lifetime to both paths is incoherent — see spec.

    Calibration (2026-08-05): the notebooks pair ~65 yr with Low and ~70 yr with
    High (life = 65 + 5u) — the uniform lives that reproduce IAEA RDS-1 2025's own
    stated retirement assumptions against this fleet's vintages (low case: 156 GW
    of the 2024 fleet retired by 2050; high case: LTO holds retirements to ~81 GW).
    The earlier 60/80-yr bracket retired 233/4 GW — double the IAEA spread.
    """
    df = operating if region is None else operating[operating["region"] == region]
    df = df.dropna(subset=[vintage_field, "capacity_net_mw"])
    retire_year = df[vintage_field].dt.year + lifetime_years
    out = pd.Series(0.0, index=years)
    for y, gw in zip(retire_year, df["capacity_net_mw"] / 1000.0):
        yi = int(np.floor(y))
        if yi < years.min():
            yi = int(years.min())   # still operating past the rule -> retires at window start
        if yi in out.index:
            out.loc[yi] += gw
    return out


def gross_additions(net_capacity_gw, retirements_gw):
    """gross(t) = max(0, delta_net(t) + retirements(t)).

    This is the fix for the net-delta bias: a region like WEU whose net path
    declines still BUILDS reactors — the builds are simply masked by retirements.
    """
    dnet = pd.Series(net_capacity_gw, index=retirements_gw.index).diff().fillna(0.0)
    return (dnet + retirements_gw).clip(lower=0.0)


def committed_pipeline(under_construction, years, lead_time_months=None):
    """GW/yr completions from units already under construction (bottom-up, replaces
    the interpolated RDS-1 path over its horizon — do NOT add both)."""
    df = under_construction.dropna(subset=["capacity_net_mw"]).copy()
    if "grid_connection" in df.columns and df["grid_connection"].notna().any():
        done = df["grid_connection"]
    else:
        done = pd.Series(pd.NaT, index=df.index)
    if lead_time_months is not None:
        est = df["construction_start"] + pd.to_timedelta(lead_time_months * 30.44, unit="D")
        done = done.fillna(est)
    df["complete_year"] = done.dt.year
    out = pd.Series(0.0, index=years)
    for y, gw in zip(df["complete_year"], df["capacity_net_mw"] / 1000.0):
        if pd.isna(y):
            continue
        yi = int(y)
        if yi < years.min():
            yi = int(years.min())   # stale planned date / already-connected: lands at window start
        if yi in out.index:
            out.loc[yi] += gw
    return out


# ---------------------------------------------------------------------------
# 4. Duration panel (design-family resolved)
# ---------------------------------------------------------------------------
FAMILY_PATTERNS = {
    "AP1000":  ["AP-1000", "AP1000", "CAP1000", "CAP-1000", "CAP1400", "CAP-1400"],
    "APR1400": ["APR-1400", "APR1400"],
    # ACP-1000 is how PRIS records the exported Hualong One units (KANUPP-2/3, Karachi);
    # the pattern is safe against ACPR-1000 (CPR family) and ACP100 (Linglong SMR)
    "HPR1000": ["HPR1000", "HPR-1000", "HRP1000", "HUALONG", "ACP-1000"],
    "EPR":     ["EPR", "EPR-1750"],
    "VVER1200": ["VVER-1200", "VVER V-491", "VVER V-509", "VVER V-510", "VVER V-523"],
    "OPR1000": ["OPR-1000", "OPR1000"],
    "CPR1000": ["CPR-1000", "ACPR-1000"],
}


def assign_family(df, patterns=FAMILY_PATTERNS):
    # .fillna("") before the cast: pandas 3 propagates NA through astype(str), so missing
    # model strings would otherwise reach the pattern match as floats
    m = df.get("model", pd.Series("", index=df.index)).fillna("").astype(str).str.upper()
    fam = pd.Series(pd.NA, index=df.index, dtype="object")
    for name, pats in patterns.items():
        hit = m.apply(lambda s: any(p.upper() in s for p in pats))
        fam = fam.mask(hit & fam.isna(), name)
    return fam


def duration_panel(df, endpoint="grid_connection"):
    """Construction duration in months, with within-family sequence index.

    ENDPOINT NOTE: RDS-2/PRIS convention is construction start -> GRID CONNECTION
    (RDS-2 Table 8 states this explicitly). The earlier AP1000 panel used
    FNC -> COMMERCIAL OPERATION. Harmonize before combining: grid_connection is
    the PRIS-consistent choice.
    """
    d = df.dropna(subset=["construction_start", endpoint]).copy()
    d["family"] = assign_family(d)
    d = d.dropna(subset=["family"])
    d["months"] = (d[endpoint] - d["construction_start"]).dt.days / 30.44
    d = d.sort_values(["family", "construction_start"])
    d["family_seq"] = d.groupby("family").cumcount() + 1
    return d[["reactor_name", "country", "region", "family", "model", "capacity_net_mw",
              "construction_start", endpoint, "months", "family_seq"]]


def validate_region_mapping(df, milestones_2024):
    agg = (df.groupby("region")["capacity_net_mw"].sum() / 1000.0)
    out = pd.DataFrame({"pris_gw": agg}).reindex(ALL_REGIONS).fillna(0.0)
    out["model_milestone_gw"] = pd.Series(milestones_2024)
    out["diff"] = out["pris_gw"] - out["model_milestone_gw"]
    return out.round(2)
