# -*- coding: utf-8 -*-
"""Dual-convention sensitivity (2026-08-28, anchor-convention memo companion).

Adds one cell after atb-a6b-f9 that recomputes T5 (minimum LR at the paired
deployment) and the one-sided endpoint feasible shares with ONLY the anchor
attachment moved from our per-vendor 2OAK (own0 = 2 units/firm) to the
attachment Abou-Jaoude's published tables apply:
  SMR:   first 1 GW  = 3.333 industry units = 0.833 units/firm (QA4, companion nb);
  large: industry unit 2 = 0.5 units/firm (QA4b back-solve; eq. (10) "BOAK = 2OAK"
         read with N counted industry-wide).
Every other dial (completion lag, through-2049 scoring basis, s, u, m, rho, conv)
is unchanged, so the new columns isolate the attachment convention. Exports:
  exports/atb/min_lr_at_aj_deployment_his_anchor.csv
  exports/atb/endpoint_feasible_share_his_anchor.csv
"""
import nbformat

NB = "atb_parameter_space.ipynb"

SRC = '''# T5-his + endpoint-shares-his - dual-convention sensitivity (08-28, memo companion).
# Identical computations to T5 (atb-20-a21_solve_d) and the F9 share export, with ONLY the
# anchor attachment moved from our per-vendor 2OAK (own0 = 2 units/firm) to the attachment
# Abou-Jaoude's published tables apply: SMR first 1 GW = 3.333 industry units = 0.833/firm
# (companion QA4); large industry unit 2 = 0.5/firm (companion QA4b; eq. (10) "BOAK = 2OAK"
# with N counted industry-wide). own0 is per-firm in the engine, so his attachment is
# carried as a per-firm value at every m (it was derived at his m = 4). Lag, through-2049
# scoring basis, and all other dials unchanged - the columns isolate the convention.
OWN0_HIS = {"smr": (1.0/0.3)/4.0, "large": 2.0/4.0}

def shape_2050_at_own0(own0_val, tech, *args):
    """shape_2050 with the global anchor attachment temporarily overridden."""
    global N_BOAK_UNITS
    _saved = N_BOAK_UNITS
    N_BOAK_UNITS = float(own0_val)
    try:
        return shape_2050(tech, *args)
    finally:
        N_BOAK_UNITS = _saved

# Guard: the override round-trips (later cells keep the production anchor).
_probe = shape_2050("smr", 0.1, 0.5, 0.5, 6.0, 0.0, 0.0, 100.0)
_ = shape_2050_at_own0(OWN0_HIS["smr"], "smr", 0.1, 0.5, 0.5, 6.0, 0.0, 0.0, 100.0)
assert N_BOAK_UNITS == 2.0 and np.allclose(
    shape_2050("smr", 0.1, 0.5, 0.5, 6.0, 0.0, 0.0, 100.0), _probe)

# (1) T5 under his attachment - same loops, evaluator swapped.
_rows = []
for tech in TECH:
    for scen in SCEN_ORDER:
        ratio = TARGET[tech][scen][-1] / BOAK_PIN[tech][scen]
        n50 = AJ_GW_ENT50[scen] / TECH[tech]["unit_gw"]
        for conv in (0.0, 1.0):
            row = {"tech": tech, "scenario": scen, "base": "full" if conv else "tiny"}
            for s_val in (0.0, 0.5, 1.0):
                sh = shape_2050_at_own0(OWN0_HIS[tech], tech,
                                        LR_GRID, s_val, 0.5, 6.0, conv, 0.0, n50)
                ok = np.flatnonzero(sh <= ratio)
                row[f"min LR @ s={s_val}"] = LR_GRID[ok[0]] if ok.size else np.nan
            _rows.append(row)
min_lr_his = pd.DataFrame(_rows).set_index(["tech", "scenario", "base"])
min_lr_his.to_csv(ATB_OUT / "min_lr_at_aj_deployment_his_anchor.csv")
print("T5-his - minimum firm-level LR at the paired deployment under HIS attachment "
      "(all else as T5) -> exports/atb/min_lr_at_aj_deployment_his_anchor.csv")
_cmp = min_lr.join(min_lr_his, lsuffix=" [ours]", rsuffix=" [his]")
print(_cmp.to_string())
_delta = (min_lr - min_lr_his).stack()
print(f"\\nours-minus-his spread over finite cells: "
      f"{_delta.min():.3f} to {_delta.max():.3f} LR points "
      f"(median {_delta.median():.3f})")

# (2) One-sided endpoint feasible shares under his attachment, on the same flat Part-1
# population; closed-form evaluation (QA-5a: closed form == engine 2050 column), with a
# baseline cross-check against the SHAPES-based F9 export before trusting the new column.
_rows = []
for tech in TECH:
    sup = (P["lr"] >= TECH[tech]["lr_lo"]) & (P["lr"] <= TECH[tech]["lr_hi"])
    tiny, full = P["conv_full"] == 0, P["conv_full"] == 1
    for scen in SCEN_ORDER:
        n50 = AJ_GW_ENT50[scen] / TECH[tech]["unit_gw"]
        t50 = TARGET[tech][scen][-1]
        args = (P["lr"], P["s"], P["u"], P["n_vendors"], P["conv_full"], P["ces_rho"], n50)
        base50 = BOAK_PIN[tech][scen] * shape_2050(tech, *args)
        chk = float((np.maximum(base50 - t50, 0.0) <= TOL)[sup].mean())
        ref = float((GAP50[(tech, scen)] <= TOL)[sup].mean())
        assert abs(chk - ref) < 2e-3, (tech, scen, chk, ref)   # float32 SHAPES vs float64
        his50 = BOAK_PIN[tech][scen] * shape_2050_at_own0(OWN0_HIS[tech], tech, *args)
        feas = np.maximum(his50 - t50, 0.0) <= TOL
        _rows.append({"tech": tech, "scenario": scen,
                      "share_support_his": round(float(feas[sup].mean()), 4),
                      "share_support_tiny_his": round(float(feas[sup & tiny].mean()), 4),
                      "share_support_full_his": round(float(feas[sup & full].mean()), 4),
                      "share_support_ours": round(ref, 4)})
end_share_his = pd.DataFrame(_rows).set_index(["tech", "scenario"])
end_share_his.to_csv(ATB_OUT / "endpoint_feasible_share_his_anchor.csv")
print("\\nendpoint feasible shares (one-sided, support-restricted) under HIS attachment "
      "-> exports/atb/endpoint_feasible_share_his_anchor.csv")
print(end_share_his.to_string())'''


def main():
    nb = nbformat.read(NB, as_version=4)
    idx = next(i for i, c in enumerate(nb.cells) if c.get("id") == "atb-a6b-f9")
    nxt = nb.cells[idx + 1].get("source", "") if idx + 1 < len(nb.cells) else ""
    assert "T5-his" not in nxt, "sensitivity cell already inserted"
    cell = nbformat.v4.new_code_cell(source=SRC)
    cell["id"] = "atb-a6c-dualconv"
    nb.cells.insert(idx + 1, cell)
    nbformat.write(nb, NB)
    print(f"patched: {NB} (dual-convention cell inserted after atb-a6b-f9 at {idx + 1})")


if __name__ == "__main__":
    main()
