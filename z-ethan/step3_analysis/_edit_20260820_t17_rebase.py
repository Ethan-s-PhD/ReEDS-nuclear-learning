"""t17 capacity-payment rebase (2026-08-20) — resolves the [REBASE] open item.

Edit method per the established convention (the notebook is edited in place by
id-targeted, assert-guarded string replacements; `_build_notebook.py` is STALE and
must never be run). Idempotent. Run with any python (json + stdlib only), then
re-execute the notebook headless on the playground-env kernel with drive D mounted.

What this applies (ruling of 2026-08-20, Ethan):
1. cell t17cd001: every payment stream becomes a true 30-year per-vintage
   window on the t11 convention (calendar years via year_rep, ordinary
   annuity at DRW). cut and hold now differ only in the post-2050 clearing
   price — cut = it drops to zero in 2051 (support self-terminates), hold =
   the 2050 dual persists flat in real terms (support stays necessary) —
   uniformly across vintages, so the band is state-contingency, not a
   window-length artifact. The result is the band; neither edge is a
   headline.
2. Fleet on the same convention: the pre-existing fleet earns the clearing
   price over the 30-year program window that starts in 2026; its hold
   variant extends 2051-2055 at the 2050 fleet level and 2050 dual.
   Convention choice on record: this avoids inventing a post-2050 fleet
   retirement schedule ("paid while standing" via the 65+5u rule was
   considered and not chosen). New columns PV_fleet_cut/PV_fleet_hold
   replace PV_fleet_rent.
3. The old truncated solve-block sum survives as a diagnostic column
   (PV_diag_solveblock_2024B) still asserted per case against the t08 PV,
   so the cross-check is kept while the headline columns move basis.
4. Per-vintage window values are asserted against t11's C_cut/C_hold where
   the vintage year is a t09 rate year (same arithmetic, independent code
   path).
5. cell t17md001: basis and band semantics restated.
6. cell t18md001: mandate bullet restated with the band semantics. t18cd001
   needs no change (it joins t17 on the PV_mandate_* columns, unchanged).
"""
import json
from pathlib import Path

NB = Path(__file__).resolve().parent / "step3_analysis.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
CELLS = {c["id"]: c for c in nb["cells"]}

if "PV_fleet_cut_2024B" in "".join(CELLS["t17cd001"]["source"]):
    print("t17 rebase already applied; nothing to do")
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


# ---- 1. cell t17md001 (basis + band semantics) --------------------------------------
put("t17md001", "capacity-standard reading", """\
### t17 - the mandate priced per vintage (capacity-standard reading)

Rebased 2026-08-20 (closes the [REBASE] item; the pre-rebase numbers are
void). R_t (t08) bills the capacity-credit market by year and stops at the
model horizon, so a late vintage was credited only a few payment-years while
an early one got most of its window - a truncation artifact, not a price
statement. t17 now prices every stream as a true 30-year window on the t11
convention (calendar years via year_rep; ordinary annuity at DRW): each
vintage of program additions earns the clearing price over the 30 years from
its build year, and the pre-existing fleet - which the fleet-inclusive
large100 standard also pays - earns it over the 30-year program window that
starts in 2026 (its 2051-2055 remainder held at the 2050 fleet level).
Cut and hold now differ only in the post-2050 clearing price, uniformly
across vintages: **cut** is the world where the price drops to zero in 2051
- support has become unnecessary and the instrument self-terminates -
and **hold** is the world where the 2050 dual persists flat in real terms -
support stays necessary. The result is the band, not either edge; it
collapses in strong-learning worlds and is widest in expensive ones. The old
truncated solve-block sum survives only as the diagnostic column
PV_diag_solveblock, still asserted per case against the t08 PV, and each
vintage's window value is asserted against t11's C_cut/C_hold where the
vintage year is a rate year.
""")

# ---- 2. cell t17cd001 (corrected computation) ---------------------------------------
put("t17cd001", "stream_cut", """\
# ---- t17: mandate cost restated per vintage (capacity-standard reading) --------------------------
# Rebased 2026-08-20: true 30-year windows on the t11 convention (year_rep
# calendar years, ordinary annuity at DRW). cut = post-2050 clearing price
# zero (support self-terminates); hold = 2050 dual flat in real terms
# (support stays necessary). The old solve-block sum survives only as the
# t08-identity diagnostic.
cw17 = t11.set_index(["case", "t"])
per_rows = []
for c in CASES:
    d = DUALS[(DUALS["case"] == c) & (DUALS["t"] >= 2026)].set_index("t").sort_index()
    dual = d["dual_2004_MWyr"]
    prog = d["program_MW"]
    assert (prog.diff().dropna() >= -1e-6).all(), c    # additions basis is nondecreasing
    d2050 = float(dual.get(2050, 0.0))
    fleet = (d["mandate_MW"] - d["program_MW"]).clip(lower=0.0)

    def window_at(b):
        # per-MW window value at the vintage year; t11's arithmetic exactly
        w_cut = w_hold = 0.0
        for j in range(EVAL_W):
            y = b + j
            w = DRW ** -(j + 1)
            if y <= 2050:
                v = float(dual.get(year_rep(y), 0.0))
                w_cut += v * w
                w_hold += v * w
            else:
                w_hold += d2050 * w
        return w_cut, w_hold

    # diagnostic: the pre-rebase truncated solve-block stream (t08 basis)
    stream_diag = {t: sum(float(dual[u]) * GAP[u] / DR ** (u - 2026)
                          for u in d.index if u >= t) for t in d.index}
    pv_cut = pv_hold = pv_diag = 0.0
    for k_i, t in enumerate(d.index):
        prev = d.index[k_i - 1] if k_i > 0 else None
        add = float(prog[t]) - (float(prog[prev]) if prev is not None else 0.0)
        if add <= 0:
            continue
        w_cut, w_hold = window_at(t)
        if (c, t) in cw17.index:    # t11 already computed this window for rate years
            assert abs(w_cut - float(cw17.loc[(c, t), "C_cut_2004_per_MW"])) <= 1.0, (c, t)
            assert abs(w_hold - float(cw17.loc[(c, t), "C_hold_2004_per_MW"])) <= 1.0, (c, t)
        disc = DRW ** -(t - 2026)
        pv_cut += add * w_cut * disc
        pv_hold += add * w_hold * disc
        pv_diag += add * stream_diag[t]
    assert pv_hold >= pv_cut - 1e-9, c
    if d2050 == 0.0:
        assert abs(pv_hold - pv_cut) <= 1e-6, c    # band closes when support ends by 2050

    # fleet on the same convention: paid over the 30-year program window from
    # 2026; hold extends 2051-2055 at the 2050 fleet level and 2050 dual
    # (convention on record - no post-2050 retirement schedule is invented)
    fl2050 = float(fleet.get(2050, 0.0))
    fl_cut = sum(float(dual.get(year_rep(y), 0.0)) * float(fleet.get(year_rep(y), 0.0))
                 * DRW ** -(y - 2025) for y in range(2026, 2051))
    fl_hold = fl_cut + sum(d2050 * fl2050 * DRW ** -(y - 2025)
                           for y in range(2051, 2026 + EVAL_W))

    t08_pv = float(t08.set_index("case").loc[c, "PV_rental_transfer_2024B"])
    pv_diag24 = pv_diag * TO2024 / 1e9
    assert abs(pv_diag24 - t08_pv) <= max(0.06, 5e-3 * max(t08_pv, 1e-9)), (c, pv_diag24, t08_pv)
    per_rows.append(dict(case=c,
                         PV_newbuild_cut_2024B=round(pv_cut * TO2024 / 1e9, 1),
                         PV_newbuild_hold_2024B=round(pv_hold * TO2024 / 1e9, 1),
                         PV_fleet_cut_2024B=round(fl_cut * TO2024 / 1e9, 1),
                         PV_fleet_hold_2024B=round(fl_hold * TO2024 / 1e9, 1),
                         PV_mandate_cut_2024B=round((pv_cut + fl_cut) * TO2024 / 1e9, 1),
                         PV_mandate_hold_2024B=round((pv_hold + fl_hold) * TO2024 / 1e9, 1),
                         PV_diag_solveblock_2024B=round(pv_diag24, 1)))
t17 = pd.DataFrame(per_rows)
t17.to_csv(EXPORTS / "t17_mandate_perbuild.csv", index=False)
print("t08 identity: the truncated solve-block DIAGNOSTIC reproduces the t08 PV per case (asserted);")
print("headline columns are true 30-year windows (asserted against t11 C_cut/C_hold at rate years).")
e5 = t17.set_index("case").loc["smr100_eia_p05"]
print(f"band collapse under strong learning: smr100_eia_p05 mandate cut "
      f"{e5['PV_mandate_cut_2024B']} vs hold {e5['PV_mandate_hold_2024B']} (2024$B)")
print(t17.to_string(index=False))
""")

# ---- 3. cell t18md001 (mandate bullet restated) -------------------------------------
rep("t18md001", """\
- **capacity-standard mandate** (t17, cut-hold band, net of tax): pays every
  standing vintage the clearing price - including the pre-existing fleet in
  the large100 cases - so it is the expensive end wherever a fleet collects
  rent.
""", """\
- **capacity-standard mandate** (t17, cut-hold band, net of tax): pays every
  standing vintage the clearing price over a true 30-year window - including
  the pre-existing fleet in the large100 cases - so it is the expensive end
  wherever a fleet collects rent. Its band is the instrument's
  state-contingency, not a costing wrinkle: cut is the world where the
  post-2050 price collapses and support self-terminates; hold is the world
  where support stays necessary. The band closes on its own under strong
  learning.
""")

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"applied {n} edits; wrote {NB.name}")
print("now re-execute the notebook headless on the playground-env kernel "
      "with drive D mounted.")
