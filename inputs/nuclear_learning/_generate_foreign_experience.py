"""
Generate the precomputed foreign nuclear experience trajectories and historical
stock values used by the endogenous nuclear-learning module (nuclear_learning.py).

Reproduces the theta-weighted foreign experience stock of
`mc_nuclear_smr_learning.ipynb` (Kim & Verdolini theta vector; IAEA RDS-1 2025
Low/High regional milestones; gross builds via the retirement identity
gross = max(0, delta_net + retirements) with the committed pipeline replacing
the interpolated path through 2030 — its real visibility horizon; the latest
RDS-2 construction starts are 2024, so with the 72-month lead it is
structurally zero afterwards).

Two modes:

EXACT (preferred): pass --rds2 <path to rds2_2025_units.csv> (and optionally
    --pris-loader <dir containing pris_loader.py>, default: the rds2 file's dir).
    Runs the notebook's own logic via pris_loader: PRIS fleet vintage ->
    retirement schedule under L(u) = 65 + 5u years (calibrated 2026-08-05 to
    IAEA RDS-1 2025's stated retirement assumptions: low case 156 GW of the
    2024 fleet retired by 2050, high case ~81 GW under LTO), bottom-up
    committed pipeline (construction start + 72 months) replacing 2025-2030,
    retirement identity afterwards. Validated against the recomputed
    diagnostics below (TARGET_POSTANCHOR_2050).

CALIBRATED FALLBACK (no --rds2): net-path additions plus (a) the notebook's
    printed per-region committed-pipeline totals spread over 2025-2034
    (replacing the net path there) and (b) a retirement-replacement residual
    calibrated so the post-anchor 2050 gross-unit totals match the exact-mode
    diagnostics at u = 0 / 0.5 / 1 (265 / 376 / 501 units, 2026-08-05 basis),
    allocated across regions in proportion to their historical fleets (the
    retiring stock) and spread uniformly over 2031-2050. This closes the ~35%
    understatement of the plain net-path approximation while introducing no
    numbers that are not in the notebook's executed output.

Output (written next to this script, i.e. inputs/nuclear_learning/):
  foreign_experience_low.csv   (u = 0.0, IAEA Low envelope, ~65-yr fleet life)
  foreign_experience_mid.csv   (u = 0.5)
  foreign_experience_high.csv  (u = 1.0, IAEA High envelope, ~70-yr LTO life)
  historical_stock.csv         (H_US, H_KV from the notebook's PRIS extraction:
                                units EVER grid-connected, printed in cell 4)

The trajectories store RAW cumulative theta-weighted foreign units by year,
END-of-year basis; the engine derives the post-anchor stock and applies the
one-year completion lag at the point of pricing (nuclear_learning.py reads
cum(t-1) when pricing year t), so the trajectories are independent of both the
anchor year and the lag convention.

Rerun with:  python inputs/nuclear_learning/_generate_foreign_experience.py
             [--rds2 "D:/nuclear learning/rds2_2025_units.csv"]
"""
import argparse
import os
import sys
import numpy as np
import pandas as pd

# Non-US regional milestones (GW): 2024, 2030L, 2030H, 2040L, 2040H, 2050L, 2050H
# (IAEA RDS-1 2025 + WNA/CNA), transcribed from mc_nuclear_smr_learning.ipynb.
REGION_MILESTONES = {
    "CA": (12.7, 12.7, 12.7, 18.8, 23.0, 30.0, 63.7),
    "SAM": (5.1, 5, 5, 8, 11, 8, 20),
    "WEU": (95.4, 86, 92, 81, 114, 68, 136),
    "EEU": (53.6, 57, 57, 58, 82, 68, 103),
    "AF": (1.9, 4, 5, 7, 12, 12, 30),
    "WA": (5.8, 11, 11, 12, 20, 15, 35),
    "SA": (11.1, 18, 22, 25, 43, 45, 85),
    "CEA": (94.5, 136, 144, 215, 264, 242, 328),
    "SEA": (0, 0, 0, 3, 7, 4, 18),
    "OC": (0, 0, 0, 0, 0, 0, 2),
}

# Kim & Verdolini (2023)-derived spillover ceilings (US as recipient).
THETA_KV = {
    "CA": 0.28, "SAM": 0.14, "WEU": 0.17794117647, "EEU": 0.1325,
    "AF": 0.16688725490, "WA": 0.13375, "SA": 0.185, "CEA": 0.135,
    "SEA": 0.16583333, "OC": 0.18,
}

# Historical units EVER grid-connected (RDS-2 2025 edition, data through 31 Dec 2024),
# EXCLUDING under-construction units: 5 of them carry PLANNED grid dates (Angra-3 SAM,
# Rajasthan-7 SA, Kursk 2-1/2-2 + Leningrad 2-3 EEU), which are not completed experience
# (notebook fix 2026-08-05: SAM 8->7, EEU 97->94, SA 32->31).
HIST_UNITS = {
    "CA": 25, "SAM": 7, "WEU": 200, "EEU": 94, "AF": 2, "WA": 7,
    "SA": 31, "CEA": 152, "SEA": 0, "OC": 0, "US": 135,
}

# Committed-pipeline totals 2025-2030 (GW) per region, from the notebook's
# executed output (bottom-up from the 62 under-construction units, construction
# start + 72 months for the 57 units without planned grid dates; identical to
# the old 2025-2034 totals - the pipeline is structurally zero after 2030).
PIPELINE_GW_2025_2030 = {
    "SAM": 1.4, "WEU": 3.3, "EEU": 6.4, "AF": 4.4, "WA": 5.4, "SA": 8.7, "CEA": 35.0,
}

# Calibration targets: foreign post-anchor (>2030) gross units by 2050 vs u,
# recomputed 2026-08-05 from rds2_2025_units.csv under the current conventions
# (PIPE_END = 2030, L(u) = 65 + 5u). Monotone in u: the IAEA-calibrated
# lifetime spread no longer lets Low-path retirement backfill overtake the
# High path's net additions.
TARGET_POSTANCHOR_2050 = {0.0: 264.8, 0.5: 375.8, 1.0: 501.5}

UNIT_FOREIGN_GW = 1.0   # foreign large new build treated as ~1 GWe reactors
UNIT_FOREIGN_SMR_GW = 0.3   # foreign SMR unit size (domestic SMR convention)

# Tech split of foreign new capacity (2026-08-06): IAEA RDS-1 2025 — "Small modular
# reactors (SMRs) are estimated to account for 24% of the 676 GW(e) new capacity added by
# 2050 in the high case and for 5% of the 320 GW(e) new capacity added in the low case" —
# applied uniformly across regions/years, interpolated in u like the lifetime rule.
# ANALYSIS GROUNDWORK ONLY: the engine (nuclear_learning.py) consumes the unsplit
# foreign_units_cum column — international experience sits in the cross-firm channel,
# which does not distinguish designs. The per-tech columns feed the notebooks' S14
# own-routing sensitivity and the design-lineage methods work.
SMR_FRAC_LO, SMR_FRAC_HI = 0.05, 0.24


def smr_frac(u):
    return SMR_FRAC_LO + u * (SMR_FRAC_HI - SMR_FRAC_LO)


YEARS = np.arange(2020, 2051)
ANCHOR = 2030
PIPE_END = 2030   # pipeline's real visibility horizon; structurally zero after 2030
SCENS = [("low", 0.0), ("mid", 0.5), ("high", 1.0)]


def net_path_gw(region, u):
    c = REGION_MILESTONES[region]
    vals = [c[0], c[1] + u * (c[2] - c[1]), c[3] + u * (c[4] - c[3]), c[5] + u * (c[6] - c[5])]
    return np.interp(YEARS, [2024, 2030, 2040, 2050], vals)


def additions_base_gw(region, u):
    """Pipeline (uniform 2025-2034, replacing the net path there) + net-path additions after."""
    net = net_path_gw(region, u)
    gross = np.clip(np.diff(net, prepend=net[0]), 0.0, None)
    pipe_total = PIPELINE_GW_2025_2030.get(region, 0.0)
    pipe_mask = (YEARS >= 2025) & (YEARS <= PIPE_END)
    gross[pipe_mask] = pipe_total / pipe_mask.sum()
    return gross


def postanchor_units(additions_by_region):
    tot = 0.0
    for r, g in additions_by_region.items():
        tot += g[YEARS > ANCHOR].sum() / UNIT_FOREIGN_GW
    return tot


def trajectories_fallback(u):
    """Calibrated net-path approximation (see module docstring)."""
    additions = {r: additions_base_gw(r, u) for r in REGION_MILESTONES}
    base = postanchor_units(additions)
    residual = TARGET_POSTANCHOR_2050[u] - base
    spread_mask = YEARS > ANCHOR
    if residual >= 0:
        # Undercount = missing retirement-replacement builds. Allocate across
        # regions in proportion to the retiring stock (historical fleet) and
        # spread uniformly over 2031-2050.
        hist_foreign = {r: HIST_UNITS[r] for r in REGION_MILESTONES}
        hist_total = sum(hist_foreign.values())
        for r in additions:
            add_units_per_yr = residual * hist_foreign[r] / hist_total / spread_mask.sum()
            additions[r][spread_mask] += add_units_per_yr * UNIT_FOREIGN_GW
    else:
        # Overcount (High path): the uniform pipeline spread puts too much of the
        # committed pipeline after 2030 (real completions are front-loaded) and the
        # interpolated ramp over-runs the bottom-up build rate. Scale the
        # post-anchor additions down proportionally to hit the notebook total.
        scale = TARGET_POSTANCHOR_2050[u] / base
        for r in additions:
            additions[r][spread_mask] *= scale
    return additions


def trajectories_exact(u, rds2_path, pris_loader_dir):
    """The notebook's own logic (cell 4) via pris_loader + the RDS-2 unit table."""
    sys.path.insert(0, pris_loader_dir)
    import pris_loader as pl
    units = pl.load_units(rds2_path)
    fleet = units[units["status"] == "operational"]
    uc = units[units["status"] == "under construction"]
    years_idx = pd.Index(YEARS)
    additions = {}
    for r in REGION_MILESTONES:
        net = net_path_gw(r, u)
        ret = pl.retirement_schedule(fleet, years_idx, lifetime_years=65.0 + 5.0 * u,
                                     region=r).to_numpy()
        dnet = np.diff(net, prepend=net[0])
        gross = np.clip(dnet + ret, 0.0, None)
        pipe = pl.committed_pipeline(uc[uc["region"] == r],
                                     pd.Index(np.arange(2025, PIPE_END + 1)),
                                     lead_time_months=72)
        pipe_mask = (YEARS >= 2025) & (YEARS <= PIPE_END)
        gross[pipe_mask] = [pipe.get(int(y), 0.0) for y in YEARS[pipe_mask]]
        additions[r] = gross
    # Validate against the notebook's printed diagnostic
    tot = postanchor_units(additions)
    target = TARGET_POSTANCHOR_2050[u]
    if abs(tot - target) > 0.03 * target:
        raise ValueError(
            f"exact-mode validation failed at u={u}: post-anchor 2050 units {tot:.0f} "
            f"vs recomputed diagnostic {target:.0f} (>3% off — check the RDS-2 extraction)")
    return additions


def theta_weighted_cum(additions_by_region):
    total = np.zeros(len(YEARS))
    for r, g in additions_by_region.items():
        total += THETA_KV[r] * np.cumsum(g) / UNIT_FOREIGN_GW
    return total


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rds2", default=None,
                   help="path to rds2_2025_units.csv for exact mode (see pris_data_spec.md)")
    p.add_argument("--pris-loader", default=None,
                   help="dir containing pris_loader.py (default: the rds2 file's directory)")
    args = p.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    exact = args.rds2 is not None
    if not exact:
        print("NOTE: no --rds2 given; using the CALIBRATED FALLBACK (net path + printed "
              "pipeline totals + retirement-replacement residual calibrated to the "
              "notebook's printed 2050 diagnostics). For the exact retirement identity, "
              "provide rds2_2025_units.csv.")

    for scen, u in SCENS:
        if exact:
            adds = trajectories_exact(u, args.rds2,
                                      args.pris_loader or os.path.dirname(args.rds2))
        else:
            adds = trajectories_fallback(u)
        cum = theta_weighted_cum(adds)
        # Tech split: the share is uniform across regions/years at fixed u, so the split
        # cumulative stocks are scalar multiples of the unsplit one — SMR units convert at
        # the 0.3-GW domestic unit size (units, not GW, drive learning).
        f = smr_frac(u)
        df = pd.DataFrame({
            "t": YEARS,
            "foreign_units_cum": np.round(cum, 4),
            "foreign_units_cum_large": np.round(cum * (1.0 - f), 4),
            "foreign_units_cum_smr": np.round(cum * f * (UNIT_FOREIGN_GW / UNIT_FOREIGN_SMR_GW), 4),
        })
        df.to_csv(os.path.join(here, f"foreign_experience_{scen}.csv"), index=False)
        post = cum[-1] - cum[YEARS == ANCHOR][0]
        print(f"wrote foreign_experience_{scen}.csv "
              f"(mode={'exact' if exact else 'fallback'}; post-anchor theta-wtd units "
              f"by 2050 = {post:.1f}; raw post-anchor = {postanchor_units(adds):.0f} "
              f"vs target {TARGET_POSTANCHOR_2050[u]:.0f})")

    h_kv = sum(THETA_KV[r] * HIST_UNITS[r] for r in REGION_MILESTONES)
    pd.DataFrame({"key": ["H_US", "H_KV"], "value": [float(HIST_UNITS["US"]), round(h_kv, 4)]}) \
        .to_csv(os.path.join(here, "historical_stock.csv"), index=False)
    print(f"wrote historical_stock.csv (H_US = {HIST_UNITS['US']}, H_KV = {h_kv:.2f} "
          "— units EVER grid-connected excl. under-construction, per the notebook)")


if __name__ == "__main__":
    main()
