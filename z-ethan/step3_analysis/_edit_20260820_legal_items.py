"""Resolve the [LEGAL] rate-level inputs (open item 7, 2026-08-20).

7a (monetization haircut): the default stays 0.10 - the all-in cost of a bank
tax-equity partnership, and the value in every run's incentives input. A 0.05
best-transfer-market variant is reported as an exact linear range (Crux 2025:
investment-grade ITC transfers averaged $0.93-0.94, large deals 2-3 cents
higher). Elective pay (Section 6417) survived OBBBA but reaches only
tax-exempt "applicable entities", so it is the floor instrument's payment
mechanism, not a rung of the haircut range.

7b (depreciation class): ReEDS prices nuclear on 15-year MACRS
(depreciation_sch = 15 in every financials_tech input). Current law is more
favorable - 48E property keeps 5-year MACRS post-OBBBA, and OBBBA's permanent
100% bonus depreciation allows full expensing - so the in-model convention is
the conservative end, and a conversion-only factor bounds the favorable-law
rate.

Edits: cell 0c9c4e73 (md, convention), cell e3e7fc5c (code, PEN_LO), new t20
cell after the t09 rate cell (5375aaf6), cell t13md001 (md, net-ratio range),
cell ebc6728a (md, caveat 6). Code changes -> full re-execution required.
"""
import json
from pathlib import Path

NB = Path(__file__).resolve().parent / "step3_analysis.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
CELLS = {c["id"]: c for c in nb["cells"]}

if "t20cd001" in CELLS:
    print("legal-items edit already applied; nothing to do")
    raise SystemExit(0)

# ---- cell 0c9c4e73 (md): the resolved haircut convention ----------------------------------------
s = "".join(CELLS["0c9c4e73"]["source"])
old = """The penalty (0.1, from the OBBBA incentives input) covers the monetization
haircut."""
new = """The penalty covers the monetization haircut - the share of a credit's face
value the owner loses because it cannot absorb the credit against its own
tax bill and must monetize it, either through a tax-equity partnership (a
financing structure in which a bank supplies capital and takes the credit)
or through a transfer sale under Section 6418. Resolved 2026-08-20 (open
item 7a): the default stays 0.10 - the all-in cost of a bank tax-equity
partnership, and the value in the OBBBA incentives input that every run and
every headline number uses. The best observed transfer-market conditions
support 0.05: investment-grade sellers averaged $0.93-0.94 per dollar of
ITC face value in 2025 (Crux market intelligence reports), and single
transactions above roughly $20M price 2-3 cents higher. Rates are linear in
1/(1 - penalty), so every quoted rate converts to the 5% haircut by the
exact factor (1 - 0.10)/(1 - 0.05) = 0.947; the t20 cell below reports the
range. Elective pay (Section 6417 "direct pay" - the IRS refunds the credit
in cash, so no haircut arises; it survived OBBBA) is restricted to
tax-exempt "applicable entities" such as governments, tribes, and
cooperatives, so a merchant developer cannot reach it; it is the payment
mechanism of the floor instrument (t18), not a rung of this range."""
assert s.count(old) == 1, "penalty paragraph not found/unique in 0c9c4e73"
CELLS["0c9c4e73"]["source"] = s.replace(old, new).splitlines(keepends=True)

# ---- cell e3e7fc5c (code): the 5% companion constant --------------------------------------------
s = "".join(CELLS["e3e7fc5c"]["source"])
old = 'print(f"itc_tax_equity_penalty = {PEN}; statutory i = m / (1 - {PEN})")'
new = '''print(f"itc_tax_equity_penalty = {PEN}; statutory i = m / (1 - {PEN})")

# haircut range (2026-08-20, open item 7a): default 0.10 = bank tax-equity
# partnership all-in cost; 0.05 = best observed transfer-market conditions
PEN_LO = 0.05
print(f"haircut range: default {PEN} (all headline numbers); best transfer-market "
      f"conditions {PEN_LO}; exact linear factor {(1 - PEN) / (1 - PEN_LO):.4f}")'''
assert s.count(old) == 1, "PEN print not found/unique in e3e7fc5c"
CELLS["e3e7fc5c"]["source"] = s.replace(old, new).splitlines(keepends=True)

# ---- new t20 cell after the t09 rate cell (5375aaf6) --------------------------------------------
T20_SRC = '''# ---- t20: legal-parameter range for the quoted rates (open item 7, resolved 2026-08-20) --------
# Two legal parameters move every quoted rate by an exact scalar factor; neither moves the shape.
# (a) Monetization haircut: i is linear in 1/(1 - penalty), so the 5% variant is the exact factor
#     (1 - PEN)/(1 - PEN_LO) on every rate, ratio, and rung.
# (b) Depreciation class: every run prices nuclear on 15-year MACRS (depreciation_sch = 15).
#     Current law is more favorable - 48E property keeps 5-year MACRS post-OBBBA, and OBBBA's
#     permanent 100% bonus depreciation allows full expensing (PV_dep = 1). m is linear in
#     k(t) = (1 - tau x PV_dep)/(1 - tau x PV_dep/2), so the conversion-only factor is
#     k_expense/k(t), holding S_t at the run's 15-year economics. Expensing would also cheapen
#     the no-credit baseline and shrink S_t itself, so this factor is an upper bound on the
#     favorable-law rate; the 15-year headline is the conservative end.
TAXR = np.asarray(TAX, dtype=float)[YEARS >= 2026]
assert float(TAXR.max() - TAXR.min()) < 1e-9    # flat from 2018 on; a scalar is exact
TAUX = float(TAXR.flat[0])
k_exp = (1.0 - TAUX) / (1.0 - TAUX / 2.0)
fac_pen = (1.0 - PEN) / (1.0 - PEN_LO)
rows20 = []
for c in CASES:
    _, K20, _ = natfin(c)
    sub = t09[(t09["case"] == c) & (t09["status"] == "rate")]
    if not len(sub):
        continue
    # conservative (largest) conversion factor across the case's rate years
    fac_dep = float((k_exp / K20.reindex(sub["t"]).astype(float)).max())
    hi = float(sub["i_model_headline"].max())
    rows20.append(dict(case=c,
                       i_model_peak_pen10=round(hi, 3),
                       i_model_peak_pen05=round(hi * fac_pen, 3),
                       dep_conversion_factor=round(fac_dep, 4),
                       i_model_peak_best=round(hi * fac_pen * fac_dep, 3)))
t20 = pd.DataFrame(rows20)
t20.to_csv(EXPORTS / "t20_legal_range.csv", index=False)
print(f"haircut factor (5% vs 10% haircut): {fac_pen:.4f}; full-expensing conversion factor: "
      f"{t20['dep_conversion_factor'].min():.4f}..{t20['dep_conversion_factor'].max():.4f}")
print(t20.to_string(index=False))
for fam in ("smr100", "large100"):
    f = t20[t20["case"].str.startswith(fam) & ~t20["case"].str.endswith("_eq")]
    print(f"{fam}: peak headline rate "
          f"{f['i_model_peak_pen10'].min():.2f}..{f['i_model_peak_pen10'].max():.2f} at the "
          f"10% haircut; {f['i_model_peak_pen05'].min():.2f}..{f['i_model_peak_pen05'].max():.2f} "
          f"at 5%; {f['i_model_peak_best'].min():.2f}..{f['i_model_peak_best'].max():.2f} "
          f"adding full expensing")
'''
idx = next(i for i, c in enumerate(nb["cells"]) if c["id"] == "5375aaf6")
nb["cells"].insert(idx + 1, dict(
    id="t20cd001", cell_type="code", metadata={}, execution_count=None,
    outputs=[], source=T20_SRC.splitlines(keepends=True)))

# ---- cell t13md001 (md): the net-ratio range ----------------------------------------------------
s = "".join(CELLS["t13md001"]["source"])
old = """(it understates the credit's relative cost because it ignores the tax the
grant returns).
"""
new = """(it understates the credit's relative cost because it ignores the tax the
grant returns).

Haircut range (2026-08-20, open item 7a): the identity makes the penalty's
effect exact. At the best-transfer-market haircut of 5%, every net ratio in
the table scales by (1 - 0.10)/(1 - 0.05) = 0.947; the default 10% (bank
tax-equity partnership) stays the headline. The depreciation terms use the
in-model 15-year MACRS convention; current law (5-year 48E recovery, or full
expensing under OBBBA's permanent 100% bonus depreciation) is strictly more
favorable to the credit, so the quoted ratios are the conservative end (see
t20).
"""
assert s.count(old) == 1, "grant-returns paragraph end not found/unique in t13md001"
CELLS["t13md001"]["source"] = s.replace(old, new).splitlines(keepends=True)

# ---- cell ebc6728a (md): caveat 6 records the resolution ----------------------------------------
s = "".join(CELLS["ebc6728a"]["source"])
old = """Two legal inputs can still move the rate level: the
   monetization haircut (0.1 here) and the depreciation recovery class
   (15-year MACRS here)."""
new = """The two legal rate-level inputs were resolved 2026-08-20 (open
   item 7): the monetization haircut defaults to 0.10 (bank tax-equity
   partnership) with an exact x0.947 range to the 5% best-transfer-market
   variant, and the depreciation class stays 15-year MACRS as the
   conservative in-model convention - current law (5-year MACRS for 48E
   property, plus OBBBA's permanent 100% bonus depreciation) only lowers
   the required rate. Both factors and the per-case ranges are in t20;
   the legal detail is in `ITC calculation procedure.md`."""
assert s.count(old) == 1, "caveat-6 legal sentence not found/unique in ebc6728a"
CELLS["ebc6728a"]["source"] = s.replace(old, new).splitlines(keepends=True)

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("legal-items edit applied: md convention, PEN_LO, t20 cell, t13 range, caveat 6")
print("code changed -> re-execute the notebook (playground-env JUPYTER_PATH recipe)")
