"""Read ReEDS ``outputs.h5`` files, write the reduced parquet extracts, load them back.

Two data modes (plan rule R2).

* Archive mode: the unpacked ReEDS output archive (588 ``outputs.h5`` files) is
  present; ``paths.reeds_outputs()`` finds it. Only notebook 05 opens h5 files:
  it calls :func:`extract` with ``data/extract_spec.csv``.
* Extracts mode: every later notebook reads the committed parquet files with
  :func:`load`, which never touches h5.

Layout of an ``outputs.h5`` file (``reeds/io.py::write_output_to_h5``): one
group per report parameter; inside it a ``columns`` dataset (byte strings) that
gives the column order, and one dataset per column. Dimension columns hold byte
strings; ``Value`` holds floats. :func:`read_key` reproduces the reader that
every working-tree notebook used: byte-string columns decode to ``str``
(numpy ``<U`` arrays, pandas ``object`` dtype), numeric columns keep their
dtype, and the year columns ``t`` and ``allt`` are cast to ``int``.

Tolerance. Key sets differ between runs. A run without an active nuclear
mandate constraint has no ``nuclear_cap_price`` / ``nuclear_cap_price_raw``
group: 284 of the 585 archive files checked on 2026-09-25 (the flat-credit
``bx_*`` runs of batch2/batch3 including the batch-3 CO2-cap runs, the
ratedesign2 ``ax_*`` runs, the rate_design runs, and the credit runs of itcfb
and itcfbm). The CO2-cap runs also carry an extra ``co2_price`` group.
:func:`read_key` raises KeyError for a missing group; :func:`extract` records
such cases as missing (``n_missing`` in the manifest) instead of failing.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from . import paths

# Casefile suffix -> output file prefix. Any batch not listed uses "<batch>_".
PREFIX = {"smr100": "test1_", "step4": "step4_", "ratedesign": "rate_design_"}
BATCHES = ["smr100", "step4", "itcfb", "itcfbm", "ratedesign", "ratedesign2",
           "batch2", "batch3"]
# Pilot runs of the smr100 batch: not in the casefile, stored under smr100/pilots/.
PILOTS = {"smr100": ["smr100_eia_lo", "smr100_eia_mid", "smr100_eia_hi"]}
_NON_CASE_COLS = {"Default Value", "Description"}
READER_VERSION = "h5io-1"   # enters the spec hash; bump if read_key's output changes


# ----------------------------------------------------------------------------
# Reading one group
# ----------------------------------------------------------------------------
def _group_to_frame(g) -> pd.DataFrame:
    cols = [c.decode() for c in g["columns"][:]]
    data = {}
    for c in cols:
        arr = g[c][:]
        data[c] = arr.astype(str) if arr.dtype.kind == "S" else arr
    df = pd.DataFrame(data)[cols]
    for c in ("t", "allt"):
        if c in df.columns:
            df[c] = df[c].astype(int)
    return df


def read_key(h5path, key: str, f=None) -> pd.DataFrame:
    """One report parameter of one ``outputs.h5`` file as a DataFrame.

    Pass an open ``h5py.File`` as ``f`` to read several keys from one file
    without reopening it. Raises KeyError when the group is absent.
    """
    import h5py

    if f is not None:
        if key not in f:
            raise KeyError(f"{key} not in {Path(h5path).name}")
        return _group_to_frame(f[key])
    with h5py.File(h5path, "r") as fh:
        if key not in fh:
            raise KeyError(f"{key} not in {Path(h5path).name}")
        return _group_to_frame(fh[key])


def _read_prefiltered(f, key: str, tech_filter: str) -> pd.DataFrame:
    """``read_key`` followed by the spec's ``tech_filter``, decoding only the kept rows.

    Same rows, order, values and dtypes as ``read_key(...)`` filtered with
    ``str.fullmatch`` (the index is reset); it only avoids decoding the byte
    strings of rows the filter drops (``reqt_price`` has 1.2 million rows).
    """
    import re

    import numpy as np

    g = f[key]
    cols = [c.decode() for c in g["columns"][:]]
    col, rx = (tech_filter.split("=", 1) if "=" in tech_filter else ("i", tech_filter))
    if col not in cols:
        raise KeyError(f"tech_filter column {col!r} not in {cols}")
    raw = g[col][:]
    codes, uniq = pd.factorize(raw)
    pat = re.compile(rx)
    ok = np.array([pat.fullmatch(u.decode() if isinstance(u, bytes) else str(u)) is not None
                   for u in uniq], dtype=bool)
    mask = ok[codes]
    data = {}
    for c in cols:
        arr = (raw if c == col else g[c][:])[mask]
        data[c] = arr.astype(str) if arr.dtype.kind == "S" else arr
    df = pd.DataFrame(data)[cols]
    for c in ("t", "allt"):
        if c in df.columns:
            df[c] = df[c].astype(int)
    return df


def keys(h5path) -> list[str]:
    """Sorted group names of one ``outputs.h5`` file."""
    import h5py

    with h5py.File(h5path, "r") as f:
        return sorted(f.keys())


# ----------------------------------------------------------------------------
# Batches, cases and files
# ----------------------------------------------------------------------------
def prefix(batch: str) -> str:
    return PREFIX.get(batch, f"{batch}_")


def cases(batch: str, pilots: bool = False) -> list[str]:
    """Case names of one batch, in casefile column order (optionally + pilots)."""
    cf = paths.require(paths.casefile(batch), "the ReEDS fork (repository root casefiles)")
    cols = pd.read_csv(cf, nrows=0, index_col=0).columns
    out = [c for c in cols if c not in _NON_CASE_COLS and not str(c).startswith("Unnamed")]
    if pilots:
        out += PILOTS.get(batch, [])
    return out


def run_file(batch: str, case: str) -> Path:
    """Path of one run's ``outputs.h5`` inside the archive (the file may not exist).

    Layout: ``<archive>/<batch>/<prefix><case>_outputs.h5``; the smr100 pilots
    live in ``<archive>/smr100/pilots/``.
    """
    root = paths.reeds_outputs()
    if root is None:
        raise FileNotFoundError(
            "ReEDS output archive not available: set NL_REEDS_OUTPUTS to the unpacked "
            f"archive folder (default {paths.DEFAULT_OUTPUTS}). Later notebooks read the "
            "committed extracts with h5io.load() instead.")
    sub = root / batch
    if case in PILOTS.get(batch, []):
        sub = sub / "pilots"
    return sub / f"{prefix(batch)}{case}_outputs.h5"


def returned_cases(batch: str, pilots: bool = False) -> list[str]:
    """Casefile cases whose ``outputs.h5`` exists in the archive."""
    return [c for c in cases(batch, pilots) if run_file(batch, c).exists()]


# ----------------------------------------------------------------------------
# Extract spec -> parquet
# ----------------------------------------------------------------------------
SPEC_COLUMNS = ["key", "batches", "tech_filter", "aggregate_to", "dims_kept", "note"]


def read_spec(path=None) -> pd.DataFrame:
    """Read ``data/extract_spec.csv`` (lines starting with '#' are comments)."""
    path = paths.require(path or paths.DATA / "extract_spec.csv", "the repository (z-ethan/data)")
    spec = pd.read_csv(path, comment="#", dtype=str, keep_default_na=False)
    missing = set(SPEC_COLUMNS) - set(spec.columns)
    if missing:
        raise ValueError(f"extract_spec.csv lacks columns {sorted(missing)}")
    return spec[SPEC_COLUMNS]


def _split(s: str) -> list[str]:
    return [x.strip() for x in str(s or "").split(";") if x.strip()]


def _row_batches(row) -> list[str]:
    b = str(row["batches"]).strip()
    return list(BATCHES) if b in ("", "all") else _split(b)


def spec_hash(row) -> str:
    """Short hash of one spec row (as applied) plus the reader version."""
    payload = {k: str(row[k]).strip() for k in SPEC_COLUMNS if k != "note"}
    payload["reader"] = READER_VERSION
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def _apply(df: pd.DataFrame, row) -> pd.DataFrame:
    """Filter and aggregate one run's frame as the spec row says.

    tech_filter : blank, or a regex matched in full against the tech column
                  ``i``; ``col=regex`` targets another column (e.g. ``*.1=nuclear.*``).
    aggregate_to: blank (none); ``national`` = sum ``Value`` over the region
                  column ``r``; ``sum:<col>[;<col>...]`` = sum over the named columns;
                  ``mean:<col>[;<col>...]`` = mean of ``Value`` over the named
                  columns (mean of the rows present: ReEDS drops zero rows);
                  ``national_except:<regex>`` = rows whose ``i`` matches the regex in
                  full keep every dimension, all other rows are summed over ``r``
                  and carry ``r = "national"`` (so a sum over ``r`` of the extract
                  still gives the national total of every technology).
    dims_kept   : blank (all), or the dimension columns to keep; ``Value`` is
                  summed over every dropped dimension.
    """
    tf = str(row["tech_filter"]).strip()
    if tf:
        col, rx = (tf.split("=", 1) if "=" in tf else ("i", tf))
        if col not in df.columns:
            raise KeyError(f"tech_filter column {col!r} not in {list(df.columns)}")
        df = df[df[col].astype(str).str.fullmatch(rx)]
    agg = str(row["aggregate_to"]).strip()
    if agg.startswith("national_except:"):
        rx = agg[len("national_except:"):]
        if "i" not in df.columns or "r" not in df.columns:
            raise KeyError(f"national_except needs columns i and r, got {list(df.columns)}")
        hit = df["i"].astype(str).str.fullmatch(rx)
        rest = _apply(df[~hit], {**dict(row), "tech_filter": "", "aggregate_to": "national"})
        rest.insert(list(df.columns).index("r"), "r", "national")
        keep_rows = _apply(df[hit], {**dict(row), "tech_filter": "", "aggregate_to": ""})
        return pd.concat([keep_rows, rest[keep_rows.columns]], ignore_index=True)
    if agg.startswith("mean:"):
        over = _split(agg[5:])
        dims = [c for c in df.columns if c != "Value"]
        unknown = set(over) - set(dims)
        if unknown:
            raise KeyError(f"mean over {sorted(unknown)} not in {dims}")
        keep = [c for c in dims if c not in over]
        df = df.groupby(keep, sort=True, dropna=False, as_index=False)["Value"].mean()
        agg = ""
    drop = []
    if agg == "national":
        drop = ["r"]
    elif agg.startswith("sum:"):
        drop = _split(agg[4:])
    elif agg:
        raise ValueError(f"unknown aggregate_to {agg!r} (blank | national | sum:<cols> | "
                         "mean:<cols> | national_except:<regex>)")
    kept = _split(row["dims_kept"])
    dims = [c for c in df.columns if c != "Value"]
    if kept:
        unknown = set(kept) - set(dims)
        if unknown:
            raise KeyError(f"dims_kept {sorted(unknown)} not in {dims}")
        drop = drop + [c for c in dims if c not in kept]
    drop = [c for c in dims if c in set(drop)]
    if drop:
        keep = [c for c in dims if c not in drop]
        if keep:
            df = df.groupby(keep, sort=True, dropna=False, as_index=False)["Value"].sum()
        else:
            df = pd.DataFrame({"Value": [df["Value"].sum()]})
    return df.reset_index(drop=True)


def extract(spec: pd.DataFrame, batches=None, out=None, overwrite: bool = False,
            pilots: bool = False, verbose: bool = True) -> pd.DataFrame:
    """Write ``<out>/<batch>/<key>.parquet`` for every (batch, key) the spec names.

    Each run file is opened once per batch; every key the spec wants from that
    batch is read from it. A ``case`` column is prepended. Missing run files
    (the two unreturned batch-3 runs) and missing groups (``nuclear_cap_price``
    in the CO2-cap runs) are recorded, not fatal. ``out/manifest.csv`` gets one
    row per written file: batch, key, n_cases, n_missing, n_rows, bytes,
    spec_hash, pilot_cases (the pilot runs included, ';'-joined). With
    overwrite=False, a (batch, key) whose parquet exists and whose manifest
    hash matches the spec is skipped.
    """
    import h5py

    out = Path(out or paths.EXTRACTS)
    want: dict[str, list] = {}
    for _, row in spec.iterrows():
        for b in _row_batches(row):
            if batches is None or b in batches:
                want.setdefault(b, []).append(row)

    man_path = out / "manifest.csv"
    manifest = pd.read_csv(man_path) if man_path.exists() else pd.DataFrame(
        columns=["batch", "key", "n_cases", "n_missing", "n_rows", "bytes", "spec_hash",
                 "pilot_cases"])
    done = {(r.batch, r.key): r.spec_hash for r in manifest.itertuples()}

    new_rows = []
    for b, rows in want.items():
        todo = []
        for row in rows:
            dst = out / b / f"{row['key']}.parquet"
            if not overwrite and dst.exists() and done.get((b, row["key"])) == spec_hash(row):
                if verbose:
                    print(f"skip {b}/{row['key']} (up to date)")
                continue
            todo.append(row)
        if not todo:
            continue
        frames = {r["key"]: [] for r in todo}
        missing = {r["key"]: [] for r in todo}
        case_list = cases(b, pilots)
        for c in case_list:
            path = run_file(b, c)
            if not path.exists():
                for r in todo:
                    missing[r["key"]].append(c)
                continue
            with h5py.File(path, "r") as f:
                for r in todo:
                    if r["key"] not in f:
                        missing[r["key"]].append(c)
                        continue
                    tf = str(r["tech_filter"]).strip()
                    if tf:   # decode only the rows the filter keeps (same result)
                        df = _read_prefiltered(f, r["key"], tf)
                        df = _apply(df, {**dict(r), "tech_filter": ""})
                    else:
                        df = _apply(read_key(path, r["key"], f=f), r)
                    for yc in ("t", "allt"):   # int64 on every platform (np.int_ is
                        if yc in df.columns:   # int32 on Windows with numpy 1.x)
                            df[yc] = df[yc].astype("int64")
                    df.insert(0, "case", c)
                    frames[r["key"]].append(df)
        for r in todo:
            k = r["key"]
            if not frames[k]:
                print(f"WARNING {b}/{k}: no run carries this key; nothing written")
                continue
            df = pd.concat(frames[k], ignore_index=True)
            dst = out / b / f"{k}.parquet"
            dst.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(dst, engine="pyarrow", compression="zstd", index=False)
            n_cases = df["case"].nunique()
            new_rows.append(dict(batch=b, key=k, n_cases=n_cases, n_missing=len(missing[k]),
                                 n_rows=len(df), bytes=dst.stat().st_size,
                                 spec_hash=spec_hash(r),
                                 pilot_cases=";".join(c for c in df["case"].unique()
                                                      if c in PILOTS.get(b, []))))
            if verbose:
                miss = f"; missing {len(missing[k])}: {missing[k][:3]}" if missing[k] else ""
                print(f"{b}/{k}: {n_cases} cases, {len(df):,} rows, "
                      f"{dst.stat().st_size / 1e6:.2f} MB{miss}")

    if new_rows:
        new = pd.DataFrame(new_rows)
        keep = ~manifest.set_index(["batch", "key"]).index.isin(
            new.set_index(["batch", "key"]).index)
        manifest = pd.concat([manifest[keep], new], ignore_index=True)
        manifest = manifest.sort_values(["batch", "key"]).reset_index(drop=True)
        out.mkdir(parents=True, exist_ok=True)
        manifest.to_csv(man_path, index=False)
    return manifest


# ----------------------------------------------------------------------------
# Reading extracts (every notebook after 05)
# ----------------------------------------------------------------------------
def load(batch: str, key: str, extracts=None) -> pd.DataFrame:
    """The parquet extract of one (batch, key): columns ``case`` + h5 columns."""
    p = Path(extracts or paths.EXTRACTS) / batch / f"{key}.parquet"
    paths.require(p, "notebook 05_extract_reeds_outputs (add the key to data/extract_spec.csv)")
    return pd.read_parquet(p, engine="pyarrow")


def available(batch: str, extracts=None) -> list[str]:
    """Keys that have a parquet extract for ``batch``."""
    d = Path(extracts or paths.EXTRACTS) / batch
    return sorted(p.stem for p in d.glob("*.parquet")) if d.is_dir() else []

