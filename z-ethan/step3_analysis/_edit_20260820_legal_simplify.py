"""Simplification ruling (Ethan, 2026-08-20, same day as the legal-items edit).

The paper reports the plain uniform ITC only: no elective-pay or
dollar-denomination design claims (the floor benchmark already shows the
frictionless cost), and depreciation stays 15-year MACRS throughout as a
hypothetical-policy convention - no current-law (OBBBA) conversion is
reported. The 10%/5% haircut range from the same day's ruling stands.

Edits: cell 0c9c4e73 (md - drop the elective-pay tail), cell t20cd001
(haircut-only; export renamed t20_haircut_range.csv), cell t13md001 (md -
depreciation sentence replaced), cell ebc6728a (md - caveat 6 restated),
cell t18md001 (md - floor rung reworded as benchmark). Code changes ->
full re-execution required; delete the stale t20_legal_range.csv.
"""
import json
from pathlib import Path

NB = Path(__file__).resolve().parent / "step3_analysis.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))
CELLS = {c["id"]: c for c in nb["cells"]}

if "t20_haircut_range" in "".join(CELLS["t20cd001"]["source"]):
    print("simplification edit already applied; nothing to do")
    raise SystemExit(0)

# ---- cell 0c9c4e73 (md): drop the elective-pay tail ---------------------------------------------
s = "".join(CELLS["0c9c4e73"]["source"])
old = """exact factor (1 - 0.10)/(1 - 0.05) = 0.947; the t20 cell below reports the
range. Elective pay (Section 6417 "direct pay" - the IRS refunds the credit
in cash, so no haircut arises; it survived OBBBA) is restricted to
tax-exempt "applicable entities" such as governments, tribes, and
cooperatives, so a merchant developer cannot reach it; it is the payment
mechanism of the floor instrument (t18), not a rung of this range."""
new = """exact factor (1 - 0.10)/(1 - 0.05) = 0.947; the t20 cell below reports the
range. The paper reports this plain credit only (simplification ruling
2026-08-20): no elective-pay or dollar-denomination design variants - the
floor already shows what frictionless delivery would cost."""
assert s.count(old) == 1, "elective-pay tail not found/unique in 0c9c4e73"
CELLS["0c9c4e73"]["source"] = s.replace(old, new).splitlines(keepends=True)

# ---- cell t20cd001 (code): haircut-only range ---------------------------------------------------
CELLS["t20cd001"]["source"] = '''# ---- t20: haircut range for the quoted rates (open item 7a, resolved 2026-08-20) ---------------
# The haircut is the one legal parameter reported as a range: i is linear in 1/(1 - penalty),
# so the 5% best-transfer-market variant is the exact factor (1 - PEN)/(1 - PEN_LO) on every
# rate, ratio, and rung. Depreciation stays 15-year MACRS everywhere by convention: the
# instrument is hypothetical policy, so no current-law depreciation conversion is reported
# (simplification ruling 2026-08-20).
fac_pen = (1.0 - PEN) / (1.0 - PEN_LO)
rows20 = []
for c in CASES:
    sub = t09[(t09["case"] == c) & (t09["status"] == "rate")]
    if not len(sub):
        continue
    hi = float(sub["i_model_headline"].max())
    rows20.append(dict(case=c,
                       i_model_peak_pen10=round(hi, 3),
                       i_model_peak_pen05=round(hi * fac_pen, 3)))
t20 = pd.DataFrame(rows20)
t20.to_csv(EXPORTS / "t20_haircut_range.csv", index=False)
print(f"haircut factor (5% vs 10% haircut): {fac_pen:.4f}")
print(t20.to_string(index=False))
for fam in ("smr100", "large100"):
    f = t20[t20["case"].str.startswith(fam) & ~t20["case"].str.endswith("_eq")]
    print(f"{fam}: peak headline rate "
          f"{f['i_model_peak_pen10'].min():.2f}..{f['i_model_peak_pen10'].max():.2f} at the "
          f"10% haircut; {f['i_model_peak_pen05'].min():.2f}.."
          f"{f['i_model_peak_pen05'].max():.2f} at 5%")
'''.splitlines(keepends=True)

# ---- cell t13md001 (md): depreciation sentence replaced -----------------------------------------
s = "".join(CELLS["t13md001"]["source"])
old = """tax-equity partnership) stays the headline. The depreciation terms use the
in-model 15-year MACRS convention; current law (5-year 48E recovery, or full
expensing under OBBBA's permanent 100% bonus depreciation) is strictly more
favorable to the credit, so the quoted ratios are the conservative end (see
t20).
"""
new = """tax-equity partnership) stays the headline. The depreciation terms use the
15-year MACRS convention throughout: the instrument is hypothetical policy,
so no current-law depreciation conversion is reported (simplification
ruling 2026-08-20).
"""
assert s.count(old) == 1, "depreciation sentence not found/unique in t13md001"
CELLS["t13md001"]["source"] = s.replace(old, new).splitlines(keepends=True)

# ---- cell ebc6728a (md): caveat 6 restated ------------------------------------------------------
s = "".join(CELLS["ebc6728a"]["source"])
old = """The two legal rate-level inputs were resolved 2026-08-20 (open
   item 7): the monetization haircut defaults to 0.10 (bank tax-equity
   partnership) with an exact x0.947 range to the 5% best-transfer-market
   variant, and the depreciation class stays 15-year MACRS as the
   conservative in-model convention - current law (5-year MACRS for 48E
   property, plus OBBBA's permanent 100% bonus depreciation) only lowers
   the required rate. Both factors and the per-case ranges are in t20;
   the legal detail is in `ITC calculation procedure.md`."""
new = """The two legal rate-level inputs were resolved 2026-08-20 (open
   item 7): the monetization haircut defaults to 0.10 (bank tax-equity
   partnership) with an exact x0.947 range to the 5% best-transfer-market
   variant (per-case ranges in t20), and the depreciation class is 15-year
   MACRS throughout - a hypothetical-policy convention held fixed, with no
   current-law conversion reported (simplification ruling, same day). The
   legal detail is in `ITC calculation procedure.md`."""
assert s.count(old) == 1, "caveat-6 text not found/unique in ebc6728a"
CELLS["ebc6728a"]["source"] = s.replace(old, new).splitlines(keepends=True)

# ---- cell t18md001 (md): floor rung is a benchmark, not a design --------------------------------
s = "".join(CELLS["t18md001"]["source"])
old = """- **floor** (1.00): flat $-per-MW support at commissioning, elective pay -
  needs a statute that pays dollars per MW with no monetization haircut."""
new = """- **floor** (1.00): flat $-per-MW support at commissioning with no
  monetization haircut - the cost benchmark the other rungs are measured
  against, not a proposed credit design (simplification ruling 2026-08-20:
  the paper reports the plain uniform ITC against this benchmark)."""
assert s.count(old) == 1, "floor rung not found/unique in t18md001"
CELLS["t18md001"]["source"] = s.replace(old, new).splitlines(keepends=True)

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
stale = NB.parent / "exports" / "t20_legal_range.csv"
if stale.exists():
    stale.unlink()
    print("stale exports/t20_legal_range.csv deleted")
print("simplification edit applied: 0c9c4e73, t20cd001, t13md001, ebc6728a, t18md001")
print("code changed -> re-execute the notebook (playground-env JUPYTER_PATH recipe)")
