"""Resolve the paper's text-number tokens against the analysis exports.

The draft marks every number it quotes from an export with a token such as
``{m10c:eia:monetized:3pt:p05|p50|p95:2025$}``. Notebook 16 resolves every token
with this module and writes ``results/tables/text_numbers.csv``; the check then
compares each rendered string with the number printed in the paper.

Token grammar
-------------
``{<src>:<seg>:<seg>:...}``. ``<src>`` names an export; the file map passed to
:func:`resolve` maps it to a CSV path. The segments, in any order:

==================  ==========================================================
segment             meaning
==================  ==========================================================
schedule code       ``eia``, ``aj``, ``iaea``, ``mck``, ``cop28``, ``eo``: row filter
percentile spec     ``p05``, ``p25``, ``p50``, ``p75``, ``p95``; ``p05|p50|p95``
                    or ``<pct>`` = the three, rendered ``"a / b / c"``
``monetized``       basis ``monetized`` (default allowance 3 points)
``headline``        basis ``face_haircut10`` with allowance 0 (the headline basis)
``<n>pt``           delivery allowance of ``n`` rate points
``2025$``           the value is shown in 2025 dollars (see below)
measure             ``per_kW``, ``first_cohort_share``, ``first_cohort_per_kW``,
                    ``spread_ratio``, ``first_cohort_share_range``,
                    ``slope_destd``, ``slope_financed_range``,
                    ``slope_overnight_range``, ``scale_ratio``, ``share``
qualifier           ``2031starts`` (only schedules whose first cohort year is
                    2031), ``base`` / ``allworlds`` (b17 world set), ``P####``
                    (a paragraph tag; ignored)
==================  ==========================================================

Sources and measures (the forms the draft uses):

* ``m10c`` = ``m10c_bill_three_bases.csv`` (2024 $B and 2024 $/kW). Row filter
  schedule + basis + allowance (default monetized, 3 points). No measure = the
  bill columns ``p05..p95``. Money is always shown in 2025 dollars: the value
  is multiplied by ``dollar_factor`` (``plotstyle.to2025(2024)`` = 1.026)
  whether or not the token spells ``2025$``, because the paper reports every
  money quantity in 2025 dollars. ``first_cohort_share`` and
  ``first_cohort_per_kW`` default to ``p50``.
* ``m102c`` (alias ``m102b``) = ``m102c_dollar_slopes.csv``; ranges are the
  minimum and maximum over the six schedule rows (the ``pooled`` row excluded).
  Slopes are ratios, so no dollar conversion.
* ``b17`` = ``b17_exceedance_noisy.csv`` at sigma 0.3, tau 0.1, mult 1.5;
  ``share`` = min-max of ``median_share_paid`` across schedules. ``allworlds``
  reads the file map entry ``b17:allworlds`` (a list of the seven world files);
  without it, every ``<stem>*.csv`` beside the ``b17`` file.

Rounding (the draft's rules): $B to the nearest 1 with one decimal below 10;
$/kW to the nearest 10; shares to a whole percent; slopes to two decimals;
thousands separated by commas; halves round up.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import numpy as np
import pandas as pd

SCHEDULES = ["eia", "aj", "iaea", "mck", "cop28", "eo"]
PCTS = ["p05", "p25", "p50", "p75", "p95"]
THREE = ["p05", "p50", "p95"]
MEASURES = {"per_kW", "first_cohort_share", "first_cohort_per_kW", "spread_ratio",
            "first_cohort_share_range", "slope_destd", "slope_financed_range",
            "slope_overnight_range", "scale_ratio", "share"}
B17_CELL = dict(sigma=0.3, tau=0.1, mult=1.5)
_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
          8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}
_CACHE: dict = {}


# ----------------------------------------------------------------------------
# Rounding and rendering
# ----------------------------------------------------------------------------
def _half_up(x: float, step: float) -> Decimal:
    q = Decimal(str(step))
    return (Decimal(repr(float(x))) / q).quantize(Decimal(1), rounding=ROUND_HALF_UP) * q


def fmt_billion(x: float) -> str:
    """$B: nearest 1, one decimal below 10."""
    if abs(x) < 10:
        return f"{float(_half_up(x, 0.1)):,.1f}"
    return f"{int(_half_up(x, 1)):,}"


def fmt_per_kw(x: float) -> str:
    """$/kW: nearest 10."""
    return f"{int(_half_up(x, 10)):,}"


def fmt_pct(frac: float) -> str:
    """A fraction as a whole percent, without the % sign."""
    return f"{int(_half_up(frac * 100, 1))}"


def fmt_2dp(x: float) -> str:
    return f"{float(_half_up(x, 0.01)):.2f}"


# ----------------------------------------------------------------------------
# Parsing
# ----------------------------------------------------------------------------
def parse(token: str) -> dict:
    """Split a token into its source and classified segments."""
    t = token.strip()
    if not (t.startswith("{") and t.endswith("}")):
        raise ValueError(f"not a token: {token!r}")
    src, *segs = t[1:-1].split(":")
    p = dict(src=src, schedule=None, pcts=None, basis=None, allowance=None,
             dollars=False, measure=None, qualifiers=[])
    for s in segs:
        if s in SCHEDULES:
            p["schedule"] = s
        elif s in PCTS:
            p["pcts"] = [s]
        elif s == "<pct>" or "|" in s:
            p["pcts"] = THREE if s == "<pct>" else s.split("|")
        elif s == "monetized":
            p["basis"] = "monetized"
        elif s == "headline":
            p["basis"] = "face_haircut10"
            p["allowance"] = 0 if p["allowance"] is None else p["allowance"]
        elif s.endswith("pt") and s[:-2].isdigit():
            p["allowance"] = int(s[:-2])
        elif s == "2025$":
            p["dollars"] = True
        elif s in MEASURES:
            p["measure"] = s
        else:
            p["qualifiers"].append(s)
    return p


def _csv(path) -> pd.DataFrame:
    path = Path(path)
    key = (str(path), path.stat().st_mtime)
    if key not in _CACHE:
        _CACHE[key] = pd.read_csv(path)
    return _CACHE[key]


def _source(file_map: dict, src: str) -> Path:
    for k in (src, {"m102b": "m102c"}.get(src, src)):
        if k in file_map:
            return Path(file_map[k])
    raise KeyError(f"file_map has no entry for source {src!r}")


# ----------------------------------------------------------------------------
# Resolvers per source
# ----------------------------------------------------------------------------
def _m10c(p, path, k):
    df = _csv(path)
    basis = p["basis"] or "monetized"
    allow = p["allowance"] if p["allowance"] is not None else 3
    m = p["measure"]
    if m in ("spread_ratio", "first_cohort_share_range"):
        rows = df[(df["allowance_pts"] == allow) & (df["basis"] == basis)]
        flt = f"allowance_pts={allow}, basis={basis}"
        if "2031starts" in p["qualifiers"]:
            rows = rows[rows["first_cohort_year"] == 2031]
            flt += ", first_cohort_year=2031"
        if m == "spread_ratio":
            raw = rows["p95_over_p05"].tolist()
            lo, hi = int(_half_up(min(raw), 1)), int(_half_up(max(raw), 1))
            return raw, f"{_WORDS[lo]}fold to {_WORDS[hi]}fold", flt + "; col p95_over_p05"
        raw = rows["first_cohort_share_p50"].tolist()
        return raw, f"{fmt_pct(min(raw))} to {fmt_pct(max(raw))}%", \
            flt + "; col first_cohort_share_p50"
    if p["schedule"] is None:
        raise ValueError("m10c token needs a schedule")
    row = df[(df["schedule"] == p["schedule"]) & (df["allowance_pts"] == allow)
             & (df["basis"] == basis)]
    if len(row) != 1:
        raise ValueError(f"m10c filter matched {len(row)} rows")
    row = row.iloc[0]
    flt = f"schedule={p['schedule']}, allowance_pts={allow}, basis={basis}"
    if m == "first_cohort_share":
        pc = (p["pcts"] or ["p50"])
        raw = [float(row[f"first_cohort_share_{q}"]) for q in pc]
        return raw, " / ".join(f"{fmt_pct(v)}%" for v in raw), \
            flt + f"; cols first_cohort_share_{'|'.join(pc)}"
    if m in ("per_kW", "first_cohort_per_kW"):
        pc = p["pcts"] or (["p50"] if m == "first_cohort_per_kW" else THREE)
        col = "support_per_kW" if m == "per_kW" else "first_cohort_per_kW"
        raw = [float(row[f"{col}_{q}"]) for q in pc]
        return raw, " / ".join(fmt_per_kw(v * k) for v in raw), \
            flt + f"; cols {col}_{'|'.join(pc)}; x{k}"
    if m is not None:
        raise ValueError(f"m10c has no measure {m!r}")
    pc = p["pcts"] or THREE
    raw = [float(row[q]) for q in pc]
    return raw, " / ".join(fmt_billion(v * k) for v in raw), flt + f"; cols {'|'.join(pc)}; x{k}"


def _m102(p, path, k):
    df = _csv(path)
    rows = df[df["schedule"].isin(SCHEDULES)]
    m = p["measure"]
    fin = rows["d_S_per_d_financed"].tolist()
    ovn = rows["d_S_per_d_overnight"].tolist()
    rng = lambda v: f"{fmt_2dp(min(v))} to {fmt_2dp(max(v))}"  # noqa: E731
    flt = "six schedule rows (pooled excluded)"
    if m == "slope_destd":
        return fin, f"the required support increases by {rng(fin)} dollars", \
            flt + "; col d_S_per_d_financed"
    if m == "slope_financed_range":
        return fin, rng(fin), flt + "; col d_S_per_d_financed"
    if m == "slope_overnight_range":
        return ovn, rng(ovn), flt + "; col d_S_per_d_overnight"
    if m == "scale_ratio":
        text = (f"Required support scales {rng(fin)} times more rapidly than the financed "
                f"plant cost, and {rng(ovn)} times more rapidly than the overnight cost, and "
                "so any uncertainty in the costs and learning parameters results in a "
                "proportionally larger uncertainty in the cost of supporting a specific "
                "nuclear goal.")
        return fin + ovn, text, flt + "; cols d_S_per_d_financed, d_S_per_d_overnight"
    raise ValueError(f"m102 has no measure {m!r}")


def _b17_rows(path):
    df = _csv(path)
    sel = np.ones(len(df), bool)
    for c, v in B17_CELL.items():
        sel &= np.isclose(df[c].astype(float), v)
    return df[sel]


def _b17(p, path, file_map):
    if p["measure"] != "share":
        raise ValueError("b17 tokens take the measure 'share'")
    flt = "sigma=0.3, tau=0.1, mult=1.5; col median_share_paid"
    if "allworlds" in p["qualifiers"]:
        files = file_map.get("b17:allworlds") or sorted(path.parent.glob(f"{path.stem}*.csv"))
        raw = [v for f in files for v in _b17_rows(f)["median_share_paid"].tolist()]
        flt += f"; {len(files)} world files"
    else:
        raw = _b17_rows(path)["median_share_paid"].tolist()
    return raw, f"{fmt_pct(min(raw))} to {fmt_pct(max(raw))}%", flt


# ----------------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------------
def _resolve(token: str, file_map: dict, dollar_factor: float = 1.026) -> dict:
    p = parse(token)
    path = _source(file_map, p["src"])
    if p["src"] == "m10c":
        raw, rendered, flt = _m10c(p, path, dollar_factor)
    elif p["src"] in ("m102b", "m102c"):
        raw, rendered, flt = _m102(p, path, dollar_factor)
    elif p["src"] == "b17":
        raw, rendered, flt = _b17(p, path, file_map)
    else:
        raise ValueError(f"unknown token source {p['src']!r}")
    return dict(token=token, source_file=path.name, filter=flt, raw=raw, rendered=rendered)


def resolve(token: str, file_map: dict, dollar_factor: float = 1.026):
    """Return ``(raw, rendered)`` for one token.

    raw      : list of the export values the token reads (native dollar year).
    rendered : the string the paper prints.
    file_map : {source id: CSV path}; ids ``m10c``, ``m102c`` (``m102b`` falls
               back to it), ``b17``, optionally ``b17:allworlds`` (list of paths).
    """
    r = _resolve(token, file_map, dollar_factor)
    return r["raw"], r["rendered"]


def render_all(tokens, file_map: dict, dollar_factor: float = 1.026) -> pd.DataFrame:
    """Resolve many tokens: DataFrame with token, source_file, filter, raw, rendered.

    A token that fails to resolve gets rendered = None and the error in ``filter``.
    """
    out = []
    for t in tokens:
        try:
            r = _resolve(t, file_map, dollar_factor)
            r["raw"] = "; ".join(f"{v:.6g}" for v in r["raw"])
        except Exception as e:  # noqa: BLE001 - reported row by row
            r = dict(token=t, source_file=None, filter=f"ERROR: {e}", raw=None, rendered=None)
        out.append(r)
    return pd.DataFrame(out, columns=["token", "source_file", "filter", "raw", "rendered"])


def _main(argv=None):
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Self-test: resolve tokens against exports.")
    ap.add_argument("--m10c", required=True)
    ap.add_argument("--m102c", required=True)
    ap.add_argument("--b17", required=True)
    ap.add_argument("--json", required=True, help="token -> expected string")
    ap.add_argument("--all", action="store_true", help="resolve every token in the JSON")
    a = ap.parse_args(argv)
    fm = {"m10c": a.m10c, "m102c": a.m102c, "b17": a.b17}
    expected = json.loads(Path(a.json).read_text(encoding="utf-8"))
    tokens = list(expected) if a.all else [
        "{m10c:eo:monetized:3pt:p05|p50|p95:2025$}",
        "{m10c:eia:first_cohort_per_kW:2025$}",
        "{b17:allworlds:share}"]
    df = render_all(tokens, fm)
    df["json"] = [expected.get(t) for t in df["token"]]
    df["match"] = df["rendered"] == df["json"]
    with pd.option_context("display.width", 200, "display.max_colwidth", 60):
        print(df[["token", "rendered", "json", "match"]].to_string(index=False))
    print(f"{int(df['match'].sum())} of {len(df)} tokens match")
    return 0 if df["match"].all() else 1


if __name__ == "__main__":
    raise SystemExit(_main())
