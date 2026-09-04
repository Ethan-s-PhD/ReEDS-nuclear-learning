# -*- coding: utf-8 -*-
"""QA4b (2026-08-28): extend the published-source pin to the LARGE-reactor tables.

QA4 replicates only Abou-Jaoude's SMR OCC tables (Tables 50/52/54, SMR columns).
The large columns were never replicated, and they turn out to encode a DIFFERENT
anchor attachment than the SMR columns: back-solving the three large columns
against eq. (12) at LR 8% puts the reference index at ~2 industry units
(grid best fit N = 1.96, all fits within $50 land in [1.87, 2.22]; max error
$271/kW at Nref = 2 vs $994/kW at the SMR-style first-1-GW reading Nref = 1).
That matches the report's eq. (10) "BOAK = 2OAK" with N counted INDUSTRY-wide
(0.5 units per firm at m = 4), while the SMR columns attach at the first 1 GW
(3.33 units = 0.83 per firm). Our production anchor reads 2OAK PER VENDOR
(own0 = 2). This cell pins the large replication at Nref = 2 and documents the
three-way fork for the anchor-convention memo.

Inserts one code cell directly after QA4 (cell id 8ba226ac). Reuses QA4's
eq12_factor / AJ_DEPLOY_GW, in scope by execution order.
"""
import nbformat

NB = "mc_cost_trajectories.ipynb"

QA4B_SOURCE = '''# QA4b - published-source pin, large-reactor half: reproduce Abou-Jaoude's large OCC
# tables (Tables 50/52/54) with his eq. (12) at LR 8%, m = 4, 1 GW units. The large
# columns attach the learning index at Nref = 2 INDUSTRY units (report eq. (10)
# "BOAK = 2OAK" with N counted industry-wide = 0.5 units/firm), NOT at the first 1 GW
# used by the SMR columns (3.33 units = 0.83/firm): back-solve best fit N = 1.96,
# $50-band [1.87, 2.22]; Nref = 2 max error $271 vs $994 for the first-GW reading.
# Our engine reads the same "BOAK = 2OAK" phrase PER VENDOR (own0 = 2/firm = 8 industry
# units at m = 4) - the three-way fork the anchor-convention memo puts to Abou-Jaoude.
# (Report-side note: Table 53's advanced large/SMR decline columns are swapped relative
# to Table 54's OCC values; replication targets the OCC tables, so QA is unaffected.)
AJ_OCC_LGE = {"Conservative": {2030: 7750, 2035: 7750, 2040: 7500, 2045: 6750, 2050: 6000},
              "Moderate":     {2030: 5750, 2035: 5500, 2040: 4750, 2045: 4250, 2050: 3750},
              "Advanced":     {2030: 5250, 2035: 4000, 2040: 3000, 2045: 2500, 2050: 2250}}
AJ_BOAK_LGE = {"Conservative": 7750.0, "Moderate": 5750.0, "Advanced": 5250.0}

worst_lge, worst_1gw = 0.0, 0.0
for name in AJ_BOAK_LGE:
    yrs = sorted(AJ_DEPLOY_GW[name])
    N = np.array([AJ_DEPLOY_GW[name][y] for y in yrs], float) / 1.0   # 1 GW per unit
    tab = np.array([AJ_OCC_LGE[name][y] for y in yrs], float)
    for nref, tracker in ((2.0, "lge"), (1.0, "1gw")):
        mult = np.minimum(1.0, np.where(N > 0,
                                        eq12_factor(N, 0.08)/eq12_factor(nref, 0.08), 1.0))
        err = np.abs(AJ_BOAK_LGE[name]*mult - tab).max()
        if tracker == "lge":
            worst_lge = max(worst_lge, err)
        else:
            worst_1gw = max(worst_1gw, err)
assert worst_lge <= 300.0, worst_lge          # $250 table rounding + fit slack
assert worst_1gw >= 900.0, worst_1gw          # the SMR-style first-GW reading is rejected
print(f"QA4b PASSED: Abou-Jaoude LARGE tables reproduced at Nref = 2 industry units, "
      f"max error ${worst_lge:,.0f}/kW (first-1-GW reading fails at ${worst_1gw:,.0f}/kW)")'''


def main():
    nb = nbformat.read(NB, as_version=4)
    idx = next(i for i, c in enumerate(nb.cells) if c.get("id") == "8ba226ac")
    assert "QA4b" not in nb.cells[idx + 1].get("source", ""), "QA4b already inserted"
    cell = nbformat.v4.new_code_cell(source=QA4B_SOURCE)
    cell["id"] = "qa4b-large-tables"
    nb.cells.insert(idx + 1, cell)
    nbformat.write(nb, NB)
    print(f"patched: {NB} (QA4b inserted after QA4 at index {idx + 1})")


if __name__ == "__main__":
    main()
