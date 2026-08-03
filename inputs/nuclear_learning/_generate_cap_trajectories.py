"""
Generate the national nuclear capacity mandate trajectories used by
GSw_NuclearCapMandate (eq_nuclear_cap_mandate in reeds/core/setup/c_model.gms).

SINGLE SOURCE OF TRUTH: this script reads US_SCHEDULES.csv (in this folder),
which is exported by the Track B notebook (z-ethan/mc/mc_cost_trajectories.ipynb,
section S2). Do not edit schedule values here or in the trajectory CSVs - edit
the notebook's US_SCHEDULES definition and re-run both.

The schedule values are read as literal GW targets (e.g. the 2025 EO is
literally 400 GW by 2050; the COP28 tripling pledge ~300 GW): the base-year
"100" is the actual 97 GW 2024 fleet rounded up, so a flat -3 GW offset undoes
that rounding rather than rescaling the stated targets multiplicatively.
Output files are in MW of total national nuclear capacity (existing + new,
net-path basis) with a GAMS-comment header, since b_inputs.gms $includes them
directly into nuclear_cap_trajectory(allt).

Each schedule is written on two bases:
- nuclear_cap_trajectory_{scen}.csv      -- total national nuclear capacity
  (existing + new); pair with GSw_NuclearCapMandateTechScen=nuclear.
- nuclear_cap_trajectory_{scen}_smr.csv  -- SMR-ONLY ADDITIONS: cumulative
  post-2030 gross builds, i.e. the schedule's net increments plus license-based
  (80-yr) retirement backfill of the existing large fleet, from the same PRIS
  unit data and identical arithmetic as GW_ADD in the Track B notebooks (which
  round-trip-check these files); pair with GSw_NuclearCapMandateTechScen=smr.

Rerun with:  python inputs/nuclear_learning/_generate_cap_trajectories.py
(the _smr variants need pandas + z-ethan/mc/pris_loader.py on the repo tree)
"""
import csv
import os
import sys

OFFSET_GW = 3.0   # schedule base year lists 100 for the actual 97 GW 2024 fleet
US_LICENSE_LIFE = 80.0   # license-based retirement of the existing fleet (as the notebooks)
ANCHOR = 2030            # no mandated additions at or before the anchor year


def read_schedules(path):
    """Read US_SCHEDULES.csv: '#'-comment header, then year,scen1,scen2,... rows."""
    with open(path, newline="") as f:
        rows = [r for r in csv.reader(f) if r and not r[0].startswith("#")]
    header, data = rows[0], rows[1:]
    scens = header[1:]
    years = [int(r[0]) for r in data]
    return years, {scen: [float(r[j + 1]) for r in data] for j, scen in enumerate(scens)}


def us_retirement_flow_gw(here, years):
    """GW of the existing US fleet retiring per model year (PRIS units, 80-yr license life),
    identical to the Track B notebooks' US_RET."""
    import pandas as pd
    mc_dir = os.path.abspath(os.path.join(here, "..", "..", "z-ethan", "mc"))
    sys.path.insert(0, mc_dir)
    import pris_loader as pl
    units = pl.load_units(os.path.join(mc_dir, "rds2_2025_units.csv"))
    fleet = units[units["status"] == "operational"]
    return pl.retirement_schedule(fleet, pd.Index(years), lifetime_years=US_LICENSE_LIFE,
                                  region="US").to_numpy()


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    years, schedules = read_schedules(os.path.join(here, "US_SCHEDULES.csv"))
    us_ret = us_retirement_flow_gw(here, years)
    for scen, idx in schedules.items():
        assert len(idx) == len(years), (scen, len(idx))
        lines = ["*t,MW"]
        for y, v in zip(years, idx):
            lines.append(f"{y},{round((v - OFFSET_GW) * 1000.0, 1)}")
        path = os.path.join(here, f"nuclear_cap_trajectory_{scen}.csv")
        with open(path, "w", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
        print(f"wrote nuclear_cap_trajectory_{scen}.csv "
              f"(2050 = {idx[-1] - OFFSET_GW:.1f} GW national)")

        # SMR-only additions basis: schedule net increments + retirement backfill,
        # zero through the anchor year, cumulative (== cumsum(GW_ADD) in the notebooks)
        cap = [v - OFFSET_GW for v in idx]
        cum, lines_smr = 0.0, ["*t,MW"]
        for j, y in enumerate(years):
            dnet = cap[j] - cap[j - 1] if j else 0.0
            flow = max(0.0, dnet + us_ret[j]) if y > ANCHOR else 0.0
            cum += flow
            lines_smr.append(f"{y},{round(cum * 1000.0, 1)}")
        path = os.path.join(here, f"nuclear_cap_trajectory_{scen}_smr.csv")
        with open(path, "w", newline="\n") as f:
            f.write("\n".join(lines_smr) + "\n")
        print(f"wrote nuclear_cap_trajectory_{scen}_smr.csv "
              f"(2050 = {cum:.1f} GW of cumulative SMR additions)")


if __name__ == "__main__":
    main()
