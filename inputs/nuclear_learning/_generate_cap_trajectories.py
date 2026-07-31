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

Rerun with:  python inputs/nuclear_learning/_generate_cap_trajectories.py
"""
import csv
import os

OFFSET_GW = 3.0   # schedule base year lists 100 for the actual 97 GW 2024 fleet


def read_schedules(path):
    """Read US_SCHEDULES.csv: '#'-comment header, then year,scen1,scen2,... rows."""
    with open(path, newline="") as f:
        rows = [r for r in csv.reader(f) if r and not r[0].startswith("#")]
    header, data = rows[0], rows[1:]
    scens = header[1:]
    years = [int(r[0]) for r in data]
    return years, {scen: [float(r[j + 1]) for r in data] for j, scen in enumerate(scens)}


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    years, schedules = read_schedules(os.path.join(here, "US_SCHEDULES.csv"))
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


if __name__ == "__main__":
    main()
