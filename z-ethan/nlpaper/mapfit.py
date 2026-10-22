"""Requirement-map families and the leave-one-out (LOO) machinery for rate_design2.

Registered in the project methods register (methods.md) v2.4 (2026-09-08, before any run):

* M00 - the current five-anchor per-year interpolation in cost space (today's display).
* M0  - the same family with every anchor as a knot (equal-cost ties averaged).
* M1  - pooled ridge on standardized path features + schedule and year dummies.
* M2  - M1 + schedule x (occ_t/1000) interactions.

Target = the anchor's t09 `i_model_headline` on rate-status, UNCENSORED cells. Censored
cells (`itc_insufficient`) are lower bounds: excluded from the fit and from the band,
reported separately. Predictions are clipped to [0, 1.2].

Selection = the smallest pooled LOO MAE (hide one anchor world at a time); ties ->
M00 < M0 < M1 < M2, then smaller lambda. Band E6 = the density-weighted p90 of |LOO error|
(each anchor weighted by the share of its schedule's draws nearest to it on the placement
plane), ceiled to one rate point.

This module was first imported by rate_design2.ipynb (dry run on the 30 existing anchors, before
the batch returns) and by rate_design2_v2.ipynb (the 66-anchor refit). It holds no data.
In the public analysis, notebook 10_requirement_map imports it as ``nlpaper.mapfit``; the
code is a verbatim copy of the working-tree module (only comments changed).
"""
from __future__ import annotations

import copy

import numpy as np
import pandas as pd

SCHEDULES = ["eia", "aj", "iaea", "mck", "cop28", "eo"]
AB2TOK = {"eia": "eia_aeo_high", "aj": "abou_jaoude", "iaea": "iaea_high",
          "mck": "mckinsey", "cop28": "cop28", "eo": "eo2025"}
LAMBDAS = [0.3, 1.0, 3.0, 10.0]
CLIP = (0.0, 1.2)


# ----------------------------------------------------------------------------- cells
def anchor_cells(t09: pd.DataFrame, anchors: pd.DataFrame, Z, YI: dict) -> pd.DataFrame:
    """One row per (anchor world, rate-status year).

    anchors: columns case, ab, draw_index (one row per anchor world).
    Returns: case, ab, w, t, rate, censored, occ, occ31, lr, boak, u, s, dur.
    """
    W = [str(c) for c in Z["world_columns"]]
    t09r = t09[t09["status"] == "rate"]
    cens_col = t09r["itc_insufficient"].fillna(False).astype(bool) if "itc_insufficient" in t09r else False
    rows = []
    for a in anchors.itertuples():
        occ = Z[f"occ_{AB2TOK[a.ab]}_smr"][a.draw_index]
        world = Z[f"worlds_{AB2TOK[a.ab]}"][a.draw_index]
        sub = t09r[t09r["case"] == a.case]
        for i, r in sub.iterrows():
            t = int(r["t"])
            rows.append(dict(case=a.case, ab=a.ab, w=int(a.draw_index), t=t,
                             rate=float(r["i_model_headline"]),
                             censored=bool(cens_col.loc[i]) if not isinstance(cens_col, bool) else False,
                             occ=float(occ[YI[t]]), occ31=float(occ[YI[2031]]),
                             lr=float(world[W.index("lr_smr")]), boak=float(world[W.index("boak_smr")]),
                             u=float(world[W.index("u")]), s=float(world[W.index("s")]),
                             dur=float(world[W.index("dur_lambda")])))
    return pd.DataFrame(rows)


def population_cells(ab: str, Z, YI: dict, years: list[int]) -> pd.DataFrame:
    """Feature rows for every draw of one schedule at the given build years (for scoring)."""
    W = [str(c) for c in Z["world_columns"]]
    occ = Z[f"occ_{AB2TOK[ab]}_smr"]
    world = Z[f"worlds_{AB2TOK[ab]}"]
    n = occ.shape[0]
    frames = []
    for t in years:
        frames.append(pd.DataFrame(dict(
            ab=ab, w=np.arange(n), t=t, occ=occ[:, YI[t]], occ31=occ[:, YI[2031]],
            lr=world[:, W.index("lr_smr")], boak=world[:, W.index("boak_smr")],
            u=world[:, W.index("u")], s=world[:, W.index("s")], dur=world[:, W.index("dur_lambda")])))
    return pd.concat(frames, ignore_index=True)


# ----------------------------------------------------------------------------- families
def _design(g: pd.DataFrame, years: list[int], interact: bool) -> pd.DataFrame:
    X = pd.DataFrame({"occ_k": g["occ"].to_numpy() / 1000.0,
                      "logocc": np.log(g["occ"].to_numpy()),
                      "lr": g["lr"].to_numpy(), "boak_k": g["boak"].to_numpy() / 1000.0,
                      "u": g["u"].to_numpy(), "s": g["s"].to_numpy(), "dur": g["dur"].to_numpy(),
                      "lr_x_occ": g["lr"].to_numpy() * g["occ"].to_numpy() / 1000.0,
                      "decl": g["occ"].to_numpy() / g["occ31"].to_numpy()})
    for ab in SCHEDULES[1:]:
        X[f"ab_{ab}"] = (g["ab"].to_numpy() == ab).astype(float)
    for t in years[1:]:
        X[f"t_{t}"] = (g["t"].to_numpy() == t).astype(float)
    if interact:
        for ab in SCHEDULES[1:]:
            X[f"occ_x_{ab}"] = X["occ_k"] * X[f"ab_{ab}"]
    return X


class Ridge:
    """M1 (interact=False) / M2 (interact=True): pooled ridge on standardized features."""

    def __init__(self, lam: float, interact: bool):
        self.lam, self.interact = lam, interact
        self.name = f"{'M2' if interact else 'M1'}(lam={lam:g})"

    def fit(self, cells: pd.DataFrame, years: list[int]):
        self.years = years
        X = _design(cells, years, self.interact)
        self.cols = list(X.columns)
        self.mu, self.sd = X.mean(), X.std().replace(0, 1.0)
        Xs = ((X - self.mu) / self.sd).to_numpy()
        y = cells["rate"].to_numpy()
        self.ym = float(y.mean())
        A = Xs.T @ Xs + self.lam * np.eye(Xs.shape[1])
        self.beta = np.linalg.solve(A, Xs.T @ (y - self.ym))
        return self

    def predict(self, cells: pd.DataFrame) -> np.ndarray:
        X = _design(cells, self.years, self.interact)[self.cols]
        Xs = ((X - self.mu) / self.sd).to_numpy()
        return np.clip(Xs @ self.beta + self.ym, *CLIP)

    def coefficients(self) -> pd.DataFrame:
        return pd.DataFrame({"feature": ["intercept"] + self.cols,
                             "beta_standardized": [self.ym] + list(self.beta)})


class Interp:
    """M00 (knots = the five percentile anchors) / M0 (knots = every anchor): per-schedule,
    per-year linear interpolation of the rate over that year's anchor cost, flat clamp
    outside the outer knots. Equal-cost ties average the rates (registered tie rule)."""

    def __init__(self, knots: str):
        assert knots in ("five", "all")
        self.knots = knots
        self.name = "M00" if knots == "five" else "M0"

    def fit(self, cells: pd.DataFrame, years: list[int]):
        self.years = years
        self.tab = {}
        for (ab, t), g in cells.groupby(["ab", "t"]):
            if self.knots == "five":
                g = g[g["case"].str.contains(r"_p(?:05|25|50|75|95)$", regex=True)]
            if len(g) == 0:
                continue
            agg = g.groupby("occ")["rate"].mean().sort_index()   # tie rule: average
            self.tab[(ab, t)] = (agg.index.to_numpy(float), agg.to_numpy(float))
        return self

    def predict(self, cells: pd.DataFrame) -> np.ndarray:
        out = np.full(len(cells), np.nan)
        for (ab, t), idx in cells.groupby(["ab", "t"]).groups.items():
            if (ab, t) not in self.tab:
                continue
            xs, ys = self.tab[(ab, t)]
            if len(xs) == 1:
                out[cells.index.get_indexer(idx)] = ys[0]
            else:
                out[cells.index.get_indexer(idx)] = np.interp(cells.loc[idx, "occ"].to_numpy(), xs, ys)
        return np.clip(out, *CLIP)

    def coefficients(self) -> pd.DataFrame:
        rows = [dict(ab=ab, t=t, occ=float(x), rate=float(y))
                for (ab, t), (xs, ys) in self.tab.items() for x, y in zip(xs, ys)]
        return pd.DataFrame(rows)


def family() -> list:
    fam = [Interp("five"), Interp("all")]
    fam += [Ridge(lam, False) for lam in LAMBDAS]
    fam += [Ridge(lam, True) for lam in LAMBDAS]
    return fam


# ----------------------------------------------------------------------------- LOO
def loo(model, cells: pd.DataFrame, years: list[int]) -> pd.DataFrame:
    """Hide one anchor world at a time; fit on the uncensored cells of the others; predict
    every cell (censored included, flagged) of the hidden world. Returns the cell table with
    pred and err_pts (100 x (pred - true)); censored cells carry err_pts = NaN."""
    fit_cells = cells[~cells["censored"]]
    parts = []
    for case in cells["case"].unique():
        tr = fit_cells[fit_cells["case"] != case]
        te = cells[cells["case"] == case].copy()
        if te["ab"].iloc[0] not in set(tr["ab"]):
            continue
        model.fit(tr, years)
        te["pred"] = model.predict(te)
        te["err_pts"] = np.where(te["censored"], np.nan, 100.0 * (te["pred"] - te["rate"]))
        parts.append(te)
    out = pd.concat(parts, ignore_index=True)
    out["model"] = model.name
    return out


def summarize(E: pd.DataFrame, weights: dict | None = None) -> tuple[pd.DataFrame, dict]:
    """Per-schedule + pooled LOO summary on uncensored cells; weighted p90 if weights
    (case -> density weight) are given."""
    ok = E[E["err_pts"].notna()].copy()
    per = ok.groupby("ab")["err_pts"].agg(
        mae=lambda x: float(np.mean(np.abs(x))), p90=lambda x: float(np.quantile(np.abs(x), 0.9)),
        mx=lambda x: float(np.max(np.abs(x))), within4=lambda x: float(np.mean(np.abs(x) <= 4)),
        n="size").reset_index()
    pooled = dict(mae=float(np.mean(np.abs(ok["err_pts"]))),
                  p90=float(np.quantile(np.abs(ok["err_pts"]), 0.9)),
                  mx=float(np.max(np.abs(ok["err_pts"]))),
                  within4=float(np.mean(np.abs(ok["err_pts"]) <= 4)), n=int(len(ok)))
    if weights is not None:
        wv = ok["case"].map(weights).to_numpy(float)
        pooled["p90_weighted"] = weighted_quantile(np.abs(ok["err_pts"].to_numpy()), wv, 0.9)
    return per, pooled


def weighted_quantile(x: np.ndarray, w: np.ndarray, q: float) -> float:
    o = np.argsort(x)
    x, w = x[o], w[o]
    cw = np.cumsum(w) / w.sum()
    return float(x[np.searchsorted(cw, q, side="left")])


def density_weights(anchors: pd.DataFrame, plane: dict) -> dict:
    """Share of each schedule's draws nearest to each anchor on the standardized placement
    plane (Voronoi share). plane[ab] = (Zpop (n,2), Zanch dict draw->(2,))."""
    out = {}
    for ab, g in anchors.groupby("ab"):
        Zpop, zanch = plane[ab]
        pts = np.stack([zanch[int(w)] for w in g["draw_index"]])
        d = np.linalg.norm(Zpop[:, None, :] - pts[None, :, :], axis=2)
        nearest = np.argmin(d, axis=1)
        share = np.bincount(nearest, minlength=len(pts)) / len(Zpop)
        for case, sh in zip(g["case"], share):
            out[case] = float(sh)
    return out


def select(results: list[tuple[str, dict]]) -> str:
    """results: [(model name, pooled summary)] in family order. Smallest MAE; ties by order."""
    best = None
    for name, pooled in results:
        if best is None or pooled["mae"] < best[1] - 1e-12:
            best = (name, pooled["mae"])
    return best[0]


# =============================================================================== v2.7 (2026-09-16)
# Registered in the project methods register (methods.md) v2.7 before rate_design2_v4.ipynb ran. Everything
# above this line is the v2.4 machinery and is unchanged (rate_design2_v2.ipynb reproduces).
#
# * Target: the capitalized shadow price in 2024 $/kW (column `S_kw` of the cell table) instead of
#   the rate. Each world's rate is S_kw x c_{s,t} / occ24, with c_{s,t} the schedule-year
#   conversion factor (the geometric mean over the solved uncensored cells of that schedule-year
#   of rate x occ24 / S_kw; equal to k / (0.9 x F_t x regional factor of the headline region)).
# * Family v4: M00, M0 (interpolation in the target), M1/M2 (as above), M3 = M2 + schedule x year
#   intercepts. Same penalty grid.
# * Selection: the smallest pooled leave-one-world-out MAE in rate points, end to end (the
#   prediction converted to a rate with the factors of the training fold). Ties -> family order.
# * The ridge here is the same arithmetic as `Ridge` above on a precomputed design matrix so the
#   nested (double) leave-one-out is affordable; `check_v4_reproduces_v2` asserts equality.

def design_v4(cells: pd.DataFrame, years: list[int], interact: bool, sy: bool) -> pd.DataFrame:
    X = _design(cells, years, interact)
    if sy:
        ab_arr, t_arr = cells["ab"].to_numpy(), cells["t"].to_numpy()
        for ab in SCHEDULES:
            for t in years[1:]:
                X[f"sy_{ab}_{t}"] = ((ab_arr == ab) & (t_arr == t)).astype(float)
    return X


class RidgeV4:
    """Ridge on standardized features (the `Ridge` arithmetic) for any target column, with a
    settable clip and optional schedule x year intercepts (M3). `prepare` precomputes the raw
    design for a fixed cell table so many folds can be fit with numpy only."""

    def __init__(self, lam: float, interact: bool, sy: bool, target: str = "rate", clip=CLIP):
        self.lam, self.interact, self.sy, self.target, self.clip = lam, interact, sy, target, clip
        self.name = f"{'M3' if sy else ('M2' if interact else 'M1')}(lam={lam:g})"

    # -- generic path (any cell table)
    def fit(self, cells: pd.DataFrame, years: list[int]):
        self.years = years
        X = design_v4(cells, years, self.interact, self.sy)
        self.cols = list(X.columns)
        self._fit_np(X.to_numpy(float), cells[self.target].to_numpy(float))
        return self

    def predict(self, cells: pd.DataFrame) -> np.ndarray:
        X = design_v4(cells, self.years, self.interact, self.sy)[self.cols].to_numpy(float)
        return self._predict_np(X)

    # -- fast path (precomputed design of one fixed table)
    def prepare(self, cells: pd.DataFrame, years: list[int]) -> np.ndarray:
        self.years = years
        X = design_v4(cells, years, self.interact, self.sy)
        self.cols = list(X.columns)
        return X.to_numpy(float)

    def _fit_np(self, X: np.ndarray, y: np.ndarray):
        self.mu = X.mean(0)
        sd = X.std(0, ddof=1)
        sd[sd == 0] = 1.0
        self.sd = sd
        Xs = (X - self.mu) / self.sd
        self.ym = float(y.mean())
        A = Xs.T @ Xs + self.lam * np.eye(Xs.shape[1])
        self.beta = np.linalg.solve(A, Xs.T @ (y - self.ym))
        return self

    def _predict_np(self, X: np.ndarray) -> np.ndarray:
        return np.clip(((X - self.mu) / self.sd) @ self.beta + self.ym, *self.clip)

    def coefficients(self) -> pd.DataFrame:
        return pd.DataFrame({"feature": ["intercept"] + self.cols,
                             "beta_standardized": [self.ym] + list(self.beta)})


class InterpV4(Interp):
    """`Interp` on any target column with a settable clip (M00 / M0 in the target's units)."""

    def __init__(self, knots: str, target: str = "rate", clip=CLIP):
        super().__init__(knots)
        self.target, self.clip = target, clip

    def fit(self, cells: pd.DataFrame, years: list[int]):
        return super().fit(cells.assign(rate=cells[self.target]), years)

    def predict(self, cells: pd.DataFrame) -> np.ndarray:
        out = np.full(len(cells), np.nan)
        for (ab, t), idx in cells.groupby(["ab", "t"]).groups.items():
            if (ab, t) not in self.tab:
                continue
            xs, ys = self.tab[(ab, t)]
            pos = cells.index.get_indexer(idx)
            out[pos] = ys[0] if len(xs) == 1 else np.interp(cells.loc[idx, "occ"].to_numpy(), xs, ys)
        return np.clip(out, *self.clip)


def family_v4(target: str = "S_kw", clip=(0.0, np.inf)) -> list:
    fam = [InterpV4("five", target, clip), InterpV4("all", target, clip)]
    fam += [RidgeV4(lam, False, False, target, clip) for lam in LAMBDAS]
    fam += [RidgeV4(lam, True, False, target, clip) for lam in LAMBDAS]
    fam += [RidgeV4(lam, True, True, target, clip) for lam in LAMBDAS]
    return fam


def conversion_factors(fit_cells: pd.DataFrame) -> tuple[dict, dict]:
    """c_{s,t} = geometric mean over the (uncensored, fitting) cells of schedule s, year t of
    rate x occ24 / S_kw; the year-only mean is the fallback for a schedule-year without cells.
    Returns ({(ab, t): c}, {t: c_year})."""
    g = np.log(fit_cells["rate"].to_numpy(float) * fit_cells["occ24"].to_numpy(float)
               / fit_cells["S_kw"].to_numpy(float))
    d = fit_cells.assign(_g=g)
    by_sy = {k: float(np.exp(v)) for k, v in d.groupby(["ab", "t"])["_g"].mean().items()}
    by_t = {int(k): float(np.exp(v)) for k, v in d.groupby("t")["_g"].mean().items()}
    return by_sy, by_t


def apply_factors(cells: pd.DataFrame, by_sy: dict, by_t: dict) -> np.ndarray:
    return np.array([by_sy.get((ab, int(t)), by_t[int(t)]) for ab, t in zip(cells["ab"], cells["t"])])


def to_rate(pred_native: np.ndarray, cells: pd.DataFrame, target: str, by_sy: dict, by_t: dict) -> np.ndarray:
    """A prediction in the target's units -> a rate (fraction) through the schedule-year factor."""
    if target == "rate":
        return pred_native
    c = apply_factors(cells, by_sy, by_t)
    return np.clip(pred_native * c / cells["occ24"].to_numpy(float), 0.0, CLIP[1])


def loo_v4(model, cells: pd.DataFrame, years: list[int]) -> pd.DataFrame:
    """Hide one anchor world at a time; fit on the uncensored cells of the others (the target's
    units); convert the hidden world's predictions to rates with the training fold's factors.
    Returns cells + pred (native), pred_rate, err_pts (NaN where censored), model, target."""
    fit_cells = cells[~cells["censored"]]
    parts = []
    for case in cells["case"].unique():
        tr = fit_cells[fit_cells["case"] != case]
        te = cells[cells["case"] == case].copy()
        model.fit(tr, years)
        te["pred"] = model.predict(te)
        by_sy, by_t = conversion_factors(tr)
        te["pred_rate"] = to_rate(te["pred"].to_numpy(), te, model.target, by_sy, by_t)
        te["err_pts"] = np.where(te["censored"], np.nan, 100.0 * (te["pred_rate"] - te["rate"]))
        parts.append(te)
    out = pd.concat(parts, ignore_index=True)
    out["model"], out["target"] = model.name, model.target
    return out


class FactorFast:
    """`conversion_factors` + `to_rate` with numpy only, for many folds on one fixed cell table.
    Same arithmetic: geometric mean of rate x occ24 / S_kw per schedule-year over the training
    rows, year-only fallback where a schedule-year has no training row."""

    def __init__(self, cells: pd.DataFrame):
        self.g = np.log(cells["rate"].to_numpy(float) * cells["occ24"].to_numpy(float) / cells["S_kw"].to_numpy(float))
        sy_keys = sorted({(ab, int(t)) for ab, t in zip(cells["ab"], cells["t"])})
        self.sy = np.array([sy_keys.index((ab, int(t))) for ab, t in zip(cells["ab"], cells["t"])])
        t_keys = sorted({int(t) for t in cells["t"]})
        self.tt = np.array([t_keys.index(int(t)) for t in cells["t"]])
        self.n_sy, self.n_t = len(sy_keys), len(t_keys)
        self.occ24 = cells["occ24"].to_numpy(float)

    def factors(self, tr: np.ndarray) -> np.ndarray:
        """Per-cell factor for every row, from the training mask `tr`."""
        s_sy = np.bincount(self.sy[tr], weights=self.g[tr], minlength=self.n_sy)
        n_sy = np.bincount(self.sy[tr], minlength=self.n_sy)
        s_t = np.bincount(self.tt[tr], weights=self.g[tr], minlength=self.n_t)
        n_t = np.bincount(self.tt[tr], minlength=self.n_t)
        c_sy = np.where(n_sy > 0, np.exp(s_sy / np.maximum(n_sy, 1)), np.nan)
        c_t = np.exp(s_t / np.maximum(n_t, 1))
        c = c_sy[self.sy]
        return np.where(np.isnan(c), c_t[self.tt], c)

    def to_rate(self, pred_native: np.ndarray, rows: np.ndarray, tr: np.ndarray, target: str) -> np.ndarray:
        if target == "rate":
            return pred_native
        c = self.factors(tr)[rows]
        return np.clip(pred_native * c / self.occ24[rows], 0.0, CLIP[1])


def loo_ridge_fast(model: RidgeV4, cells: pd.DataFrame, years: list[int], X: np.ndarray | None = None,
                   ff: FactorFast | None = None, exclude: set | None = None, return_native: bool = False):
    """Leave-one-world-out predictions (rate, end to end) for a RidgeV4 on a precomputed design.
    `exclude`: worlds left out of every training fold (the outer hidden world of a nested run);
    those rows get NaN. With return_native, also the prediction in the target's own units."""
    if X is None:
        X = model.prepare(cells, years)
    if ff is None:
        ff = FactorFast(cells)
    model = copy.copy(model)          # never mutate the caller's object (its full-sample fit must survive the folds)
    y = cells[model.target].to_numpy(float)
    case = cells["case"].to_numpy()
    fit_ok = ~cells["censored"].to_numpy()
    if exclude:
        fit_ok = fit_ok & ~np.isin(case, list(exclude))
    out = np.full(len(cells), np.nan)
    native = np.full(len(cells), np.nan)
    for c in np.unique(case):
        if exclude and c in exclude:
            continue
        tr = fit_ok & (case != c)
        te = np.where(case == c)[0]
        model._fit_np(X[tr], y[tr])
        native[te] = model._predict_np(X[te])
        out[te] = ff.to_rate(native[te], te, tr, model.target)
    return (out, native) if return_native else out


def check_v4_reproduces_v2(cells: pd.DataFrame, years: list[int], tol: float = 1e-9) -> float:
    """The fast ridge on the rate target must equal `Ridge` + `loo` cell by cell (M1/M2, all
    lambdas). Returns the largest absolute difference in predicted rate."""
    worst = 0.0
    for interact in (False, True):
        for lam in LAMBDAS:
            ref = loo(Ridge(lam, interact), cells, years).set_index(["case", "t"])["pred"]
            new = RidgeV4(lam, interact, False, "rate", CLIP)
            pr = pd.Series(loo_ridge_fast(new, cells, years), index=pd.MultiIndex.from_arrays([cells["case"], cells["t"]]))
            worst = max(worst, float((pr - ref.reindex(pr.index)).abs().max()))
    assert worst < tol, worst
    return worst


# =============================================================================== v2.8 (2026-09-16)
# Registered in the project methods register (methods.md) v2.8 before rate_design2_v5.ipynb ran. Everything
# above this line (v2.4 and v2.7) is unchanged; `check_v5_reproduces_v4` asserts the v2.7 chosen
# model's leave-one-out numbers come out of the v5 code path.
#
# * Inputs are what ReEDS receives for the world: its overnight cost in the build year, its
#   construction duration in whole years (the case-export rule `clip(round(months / 12), 1, 10)`,
#   the value written to construction_times_mc_<case>.csv) and its FOM ($/kW-yr, the value written
#   to nuclear-smr_mc_<case>.csv). No learning-model parameter enters (lr, anchor cost, u, s, the
#   duration position, lr x cost, the cost decline). Schedule x year intercepts as M3; schedule
#   OCC slopes optional; log-cost optional (recorded, expected to add nothing).
# * Conversion with the world's own construction-cost multiplier: c'_{s,t} = geometric mean over
#   the fitting cells of rate x occ24 x ccmult / S_kw; rate = S_kw x c' / (ccmult_world x occ24).
#   ccmult is ReEDS's own arithmetic (step3_analysis `ccmult_reeds` on construction_schedules_mc.csv).
# * Family v5 = {M4: no slopes, M5: schedule slopes, M5L: slopes + log-cost} x lambda in
#   {0.1, 0.3, 1, 3, 10}; selection end to end in rate points with the v2.8 conversion; ties ->
#   fewer inputs, then smaller lambda (the family order).

LAMBDAS_V5 = [0.1, 0.3, 1.0, 3.0, 10.0]
CC_EXPS = np.append([0.0], np.arange(0.5, 10.5, 1.0))     # row-aligned ReEDS exponents (step3_analysis)
BOAK_LARGE_RANGE = (5250.0, 7750.0)                       # the anchor-cost dial (smr100_case_export TECH["large"])


def ccmult_table(cs: pd.DataFrame, ib: float, prefix: str = "NS") -> dict:
    """ReEDS's construction-financing multiplier for each whole-year duration label
    (`step3_analysis.ipynb` `ccmult_reeds`, verbatim arithmetic): 1 + sum_k x_k (ib ** e_k - 1) with
    x the spend-fraction column `<prefix><n>` of construction_schedules_mc.csv and e the row-aligned
    exponents 0, 0.5, 1.5, ..., 9.5. Returns {n_years: ccmult}."""
    assert len(cs) == len(CC_EXPS), (len(cs), len(CC_EXPS))
    out = {}
    for n in range(1, 11):
        col = f"{prefix}{n}"
        if col in cs.columns:
            x = pd.to_numeric(cs[col], errors="coerce").fillna(0.0).to_numpy(float)
            out[n] = 1.0 + float(np.sum(x * (ib ** CC_EXPS - 1.0)))
    return out


def construction_years(dur_months) -> np.ndarray:
    """The case-export rule (`smr100_case_export.ipynb` `dur_to_years`): whole years =
    clip(round(months / 12), 1, 10). This is the value ReEDS receives."""
    return np.clip(np.round(np.asarray(dur_months, float) / 12.0).astype(int), 1, 10)


def fom_of_world(boak_large, fom_lo: float, fom_hi: float, boak_range=BOAK_LARGE_RANGE) -> np.ndarray:
    """FOM ($/kW-yr) comonotone with the cost dial (`smr100_case_export.ipynb` `u1_of` / `om_at`):
    U1 = (boak_large - lo) / (hi - lo); fom = fom_lo + U1 (fom_hi - fom_lo), the value written to the
    world's nuclear-smr_mc_<case>.csv from the anchor year on."""
    u1 = (np.asarray(boak_large, float) - boak_range[0]) / (boak_range[1] - boak_range[0])
    return fom_lo + u1 * (fom_hi - fom_lo)


def design_v5(cells: pd.DataFrame, years: list[int], slopes: bool, logocc: bool) -> pd.DataFrame:
    """The v2.8 design: occ_k [, logocc], ct_yrs, fom, [occ x schedule], schedule dummies, year
    dummies, schedule x year dummies. Needs columns occ, ct_yrs, fom, ab, t."""
    occ = cells["occ"].to_numpy(float)
    X = pd.DataFrame({"occ_k": occ / 1000.0})
    if logocc:
        X["logocc"] = np.log(occ)
    X["ct_yrs"] = cells["ct_yrs"].to_numpy(float)
    X["fom"] = cells["fom"].to_numpy(float)
    ab_arr, t_arr = cells["ab"].to_numpy(), cells["t"].to_numpy()
    if slopes:
        for ab in SCHEDULES[1:]:
            X[f"occ_x_{ab}"] = X["occ_k"] * (ab_arr == ab)
    for ab in SCHEDULES[1:]:
        X[f"ab_{ab}"] = (ab_arr == ab).astype(float)
    for t in years[1:]:
        X[f"t_{t}"] = (t_arr == t).astype(float)
    for ab in SCHEDULES:
        for t in years[1:]:
            X[f"sy_{ab}_{t}"] = ((ab_arr == ab) & (t_arr == t)).astype(float)
    return X


class RidgeV5(RidgeV4):
    """The `RidgeV4` arithmetic on the v2.8 design. M4 = no schedule slopes; M5 = schedule slopes;
    M5L = slopes + log-cost."""

    def __init__(self, lam: float, slopes: bool, logocc: bool, target: str = "S_kw", clip=(0.0, np.inf)):
        super().__init__(lam, slopes, True, target, clip)
        self.slopes, self.logocc = slopes, logocc
        self.name = f"{'M5L' if (slopes and logocc) else ('M5' if slopes else 'M4')}(lam={lam:g})"

    def fit(self, cells: pd.DataFrame, years: list[int]):
        self.years = years
        X = design_v5(cells, years, self.slopes, self.logocc)
        self.cols = list(X.columns)
        self._fit_np(X.to_numpy(float), cells[self.target].to_numpy(float))
        return self

    def predict(self, cells: pd.DataFrame) -> np.ndarray:
        X = design_v5(cells, self.years, self.slopes, self.logocc)[self.cols].to_numpy(float)
        return self._predict_np(X)

    def prepare(self, cells: pd.DataFrame, years: list[int]) -> np.ndarray:
        self.years = years
        X = design_v5(cells, years, self.slopes, self.logocc)
        self.cols = list(X.columns)
        return X.to_numpy(float)

    @property
    def n_inputs(self) -> int:
        return 3 + int(self.logocc)


def family_v5(target: str = "S_kw", clip=(0.0, np.inf)) -> list:
    """Family order = the tie order: fewer inputs first, then smaller lambda."""
    fam = [RidgeV5(lam, False, False, target, clip) for lam in LAMBDAS_V5]
    fam += [RidgeV5(lam, True, False, target, clip) for lam in LAMBDAS_V5]
    fam += [RidgeV5(lam, True, True, target, clip) for lam in LAMBDAS_V5]
    return fam


def conversion_factors_v5(fit_cells: pd.DataFrame) -> tuple[dict, dict]:
    """c'_{s,t} = geometric mean over the fitting cells of schedule s, year t of
    rate x occ24 x ccmult / S_kw; year-only fallback. Returns ({(ab, t): c'}, {t: c'_year})."""
    g = np.log(fit_cells["rate"].to_numpy(float) * fit_cells["occ24"].to_numpy(float)
               * fit_cells["ccmult"].to_numpy(float) / fit_cells["S_kw"].to_numpy(float))
    d = fit_cells.assign(_g=g)
    by_sy = {k: float(np.exp(v)) for k, v in d.groupby(["ab", "t"])["_g"].mean().items()}
    by_t = {int(k): float(np.exp(v)) for k, v in d.groupby("t")["_g"].mean().items()}
    return by_sy, by_t


def to_rate_v5(pred_native: np.ndarray, cells: pd.DataFrame, by_sy: dict, by_t: dict) -> np.ndarray:
    """A shadow-price prediction -> a rate through c' and the world's own ccmult and occ24."""
    c = apply_factors(cells, by_sy, by_t)
    return np.clip(pred_native * c / (cells["ccmult"].to_numpy(float) * cells["occ24"].to_numpy(float)), 0.0, CLIP[1])


class FactorV5(FactorFast):
    """`conversion_factors_v5` + `to_rate_v5` with numpy only (the fold machinery). With a unit
    ccmult column this is exactly `FactorFast` (the v2.7 conversion)."""

    def __init__(self, cells: pd.DataFrame):
        super().__init__(cells)
        self.cc = cells["ccmult"].to_numpy(float)
        self.g = self.g + np.log(self.cc)

    def to_rate(self, pred_native: np.ndarray, rows: np.ndarray, tr: np.ndarray, target: str) -> np.ndarray:
        if target == "rate":
            return pred_native
        c = self.factors(tr)[rows]
        return np.clip(pred_native * c / (self.cc[rows] * self.occ24[rows]), 0.0, CLIP[1])


def check_v5_reproduces_v4(cells: pd.DataFrame, years: list[int], m80: pd.DataFrame | None = None, tol: float = 1e-9) -> dict:
    """The v2.7 chosen model (M3, lambda 0.3, S_kw) run through the v5 fold machinery with a unit
    construction-cost multiplier must equal the v2.7 code path (`FactorFast`) cell by cell and, if
    m80 is given, the recorded m80 `pred_rate`. Returns the pooled MAE / p90 (expected 1.45 / 3.06)
    and the largest differences."""
    ref = loo_ridge_fast(RidgeV4(0.3, True, True, "S_kw", (0.0, np.inf)), cells, years, ff=FactorFast(cells))
    unit = cells.assign(ccmult=1.0)
    new = loo_ridge_fast(RidgeV4(0.3, True, True, "S_kw", (0.0, np.inf)), unit, years, ff=FactorV5(unit))
    d_code = float(np.nanmax(np.abs(new - ref)))
    assert d_code < tol, d_code
    by_sy4, _ = conversion_factors(cells[~cells["censored"]])
    by_sy5, _ = conversion_factors_v5(unit[~unit["censored"]])
    d_fac = max(abs(by_sy4[k] - by_sy5[k]) for k in by_sy4)
    assert d_fac < tol, d_fac
    ok = ~cells["censored"].to_numpy()
    e = np.abs(100.0 * (new - cells["rate"].to_numpy(float)))[ok]
    out = dict(mae=float(e.mean()), p90=float(np.quantile(e, 0.9)), max_diff_code_paths=d_code, max_diff_factors=d_fac)
    if m80 is not None:
        rec = m80[(m80["model"] == "M3(lam=0.3)") & (m80["target"] == "S_kw")].set_index(["case", "t"])["pred_rate"]
        got = pd.Series(new, index=pd.MultiIndex.from_arrays([cells["case"], cells["t"].astype(int)]))
        out["max_diff_vs_m80"] = float((got - rec.reindex(got.index)).abs().max())
        assert out["max_diff_vs_m80"] < tol, out["max_diff_vs_m80"]
    return out


# =============================================================================== v2.9 (2026-09-18)
# Registered in the project methods register (methods.md) v2.9 before rate_design2_v6.ipynb ran. Everything
# above this line (v2.4, v2.7, v2.8) is unchanged; `check_v6_reproduces_v5` asserts the v2.8 chosen
# model's leave-one-out numbers come out of the v6 code path.
#
# * One more input: construction years x cost (`ct_x_occ = ct_yrs x occ_k`), the multiplicative
#   form in which ReEDS applies the construction duration (the construction-financing multiplier
#   scales the overnight cost). The v2.8 reviewer's note 6; recorded in the v2.8 outcomes on the
#   registered code path (LOO MAE 1.114 -> 0.929) and adopted by Ethan on 2026-09-18.
# * Family v6 = family v5 (M4 / M5 / M5L x five penalties) + the same fifteen members with the
#   interaction (M4X / M5X / M5LX). Tie order: fewer inputs first (the v5 members precede the X
#   members), then smaller lambda. The ccmult x cost form (`cc_x_occ`) is a diagnostic only.
# * Target, conversion (c' with the world's own ccmult), censoring (none, v2.8.1), fold machinery,
#   band derivation: unchanged.


def design_v6(cells: pd.DataFrame, years: list[int], slopes: bool, logocc: bool, inter: str | None) -> pd.DataFrame:
    """The v2.8 design plus one interaction column: `inter` = "ct" adds ct_yrs x occ_k (v2.9),
    "cc" adds ccmult x occ_k (diagnostic), None reproduces `design_v5` exactly."""
    X = design_v5(cells, years, slopes, logocc)
    if inter == "ct":
        X.insert(3, "ct_x_occ", X["ct_yrs"] * X["occ_k"])
    elif inter == "cc":
        X.insert(3, "cc_x_occ", cells["ccmult"].to_numpy(float) * X["occ_k"])
    elif inter is not None:
        raise ValueError(inter)
    return X


class RidgeV6(RidgeV5):
    """`RidgeV5` on the v6 design. Name suffix X (ct_yrs x cost) or XC (ccmult x cost); with
    inter=None this is exactly the v5 member of the same form."""

    def __init__(self, lam: float, slopes: bool, logocc: bool, inter: str | None, target: str = "S_kw", clip=(0.0, np.inf)):
        super().__init__(lam, slopes, logocc, target, clip)
        self.inter = inter
        if inter is not None:
            self.name = self.name.replace("(", {"ct": "X", "cc": "XC"}[inter] + "(")

    def _design(self, cells: pd.DataFrame, years: list[int]) -> pd.DataFrame:
        return design_v6(cells, years, self.slopes, self.logocc, self.inter)

    def fit(self, cells: pd.DataFrame, years: list[int]):
        self.years = years
        X = self._design(cells, years)
        self.cols = list(X.columns)
        self._fit_np(X.to_numpy(float), cells[self.target].to_numpy(float))
        return self

    def predict(self, cells: pd.DataFrame) -> np.ndarray:
        X = self._design(cells, self.years)[self.cols].to_numpy(float)
        return self._predict_np(X)

    def prepare(self, cells: pd.DataFrame, years: list[int]) -> np.ndarray:
        self.years = years
        X = self._design(cells, years)
        self.cols = list(X.columns)
        return X.to_numpy(float)

    @property
    def n_inputs(self) -> int:
        return 3 + int(self.logocc) + int(self.inter is not None)


def family_v6(target: str = "S_kw", clip=(0.0, np.inf)) -> list:
    """Family order = the tie order: the fifteen v5 members, then the fifteen interaction
    members (M4X, M5X, M5LX x lambda)."""
    fam = family_v5(target, clip)
    fam += [RidgeV6(lam, False, False, "ct", target, clip) for lam in LAMBDAS_V5]
    fam += [RidgeV6(lam, True, False, "ct", target, clip) for lam in LAMBDAS_V5]
    fam += [RidgeV6(lam, True, True, "ct", target, clip) for lam in LAMBDAS_V5]
    return fam


def check_v6_reproduces_v5(cells: pd.DataFrame, years: list[int], m90: pd.DataFrame | None = None, tol: float = 1e-9) -> dict:
    """The v2.8 chosen model (M5, lambda 0.1, S_kw) as a `RidgeV6` with no interaction, through the
    fold machinery, must equal the `RidgeV5` code path cell by cell and, if m90 is given, the
    recorded m90 `pred_rate` of the v5 family's M5(lam=0.1). Returns the pooled MAE / p90 (expected
    1.114 / 2.579 on the 600 cells) and the largest differences."""
    ff = FactorV5(cells)
    ref = loo_ridge_fast(RidgeV5(0.1, True, False, "S_kw", (0.0, np.inf)), cells, years, ff=ff)
    new = loo_ridge_fast(RidgeV6(0.1, True, False, None, "S_kw", (0.0, np.inf)), cells, years, ff=ff)
    d_code = float(np.nanmax(np.abs(new - ref)))
    assert d_code < tol, d_code
    ok = ~cells["censored"].to_numpy()
    e = np.abs(100.0 * (new - cells["rate"].to_numpy(float)))[ok]
    out = dict(mae=float(e.mean()), p90=float(np.quantile(e, 0.9)), max_diff_code_paths=d_code)
    if m90 is not None:
        rec = m90[(m90["family"] == "v5") & (m90["model"] == "M5(lam=0.1)")].set_index(["case", "t"])["pred_rate"]
        got = pd.Series(new, index=pd.MultiIndex.from_arrays([cells["case"], cells["t"].astype(int)]))
        out["max_diff_vs_m90"] = float((got - rec.reindex(got.index)).abs().max())
        assert out["max_diff_vs_m90"] < tol, out["max_diff_vs_m90"]
    return out
