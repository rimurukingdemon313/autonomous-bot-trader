"""ID-2: the intraday opportunity engine, judged once (research/preregistrations/ID-2.md).

    python scripts/id2.py spec          # freeze the design (writes research/specs/ID-2.json)
    python scripts/id2.py preregister   # register the trial (after the document quotes the spec hash)
    python scripts/id2.py run           # development walk-forward -> promotion -> validation (if earned)
    python scripts/id2.py holdout       # fx-majors 2017+ (only validation passers; needs M5 2017+ bars)

Every candidate M5 bar 07:00-19:55 UTC is scanned on both sides; a walk-forward model estimates
the standard trade's net R; the portfolio takes candidates whose estimate exceeds tau, under the
production risk engine's entry checks and account limits. Simple deterministic rules go through
the identical trade template and portfolio, so the comparison is like for like.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from statistics import NormalDist

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import id1  # noqa: E402
from aitrader.research.discovery import intraday as ID  # noqa: E402
from aitrader.research.discovery import opportunity as OP  # noqa: E402
from aitrader.research.discovery import rc  # noqa: E402
from aitrader.research.discovery.stats import welch_t  # noqa: E402
from aitrader.data.store import open_final_test  # noqa: E402
from aitrader.research.registry import Registry, Trial, Use, Verdict  # noqa: E402

PID, HID = "ID-2", "ID-2-H"
R = ROOT / "research"
DOC = "research/preregistrations/ID-2.md"
SPEC = R / "specs" / "ID-2.json"
OUT = R / "knowledge"
CACHE = ROOT / "data" / "id2"
CODE = ("aitrader/research/discovery/intraday.py", "aitrader/research/discovery/opportunity.py", "scripts/id1.py",
        "scripts/id2.py")
SYMBOLS = id1.SYMBOLS
_ts = id1._ts

DEV = (date(2009, 1, 1), date(2014, 1, 1))  # loaded for development: models train from 2009
DEV_OOS = (date(2011, 1, 1), date(2014, 1, 1))  # judged for development: every year predicted out of sample
VAL = (date(2014, 1, 1), date(2017, 1, 1))
HOLD = id1.HOLD
FOLDS_DEV = (2011, 2012, 2013)
FOLDS_VAL = (2014, 2015, 2016)
COSTS = ID.Costs()
RISK_PCT = 0.5
COST_GRID = (1.25, 1.5, 2.0)
SLIP_STRESS = 0.3
RANDOM_SEEDS = (31, 32, 33)
FAMILY_LIST = ("ridge", "trees")
TAUS = (0.0, 0.05, 0.10)
TAU_STEP = 0.05
RULES = {  # deterministic baselines through the same template and portfolio: (description, primary, neighbours)
    "MOM": ("12-bar move z >= z0: trade with it", {"z": 2.0}, [{"z": 1.75}, {"z": 2.25}]),
    "MR": ("close >= d ATR from EMA(20): fade it", {"d": 2.5}, [{"d": 2.25}, {"d": 2.75}]),
    "BRK": ("first close beyond the previous n bars' high/low: trade the break", {"n": 20}, [{"n": 15}, {"n": 25}]),
    "SWEEP": ("A1/A2/A3 liquidity sweep event: fade it", {"pen": 0.10}, [{"pen": 0.05}, {"pen": 0.15}]),
}
CONTROLS = ("RANDOM",)  # one random candidate bar per instrument-day, random side
PROMOTE = {"min_trades": 300, "net_r": "> 0", "t_day": 2.0, "profit_factor": 1.10, "costs_x1.25_net_r": "> 0",
           "beats_matched_random_welch_t": 2.0, "symbols_positive_share": 0.6}
JUDGE = {"t_day": "max(3.0, registry Bonferroni)", "net_r": "> 0", "profit_factor": 1.20, "costs_x1.5_net_r": "> 0",
         "slippage_0.3_net_r": "> 0", "symbols_positive_share": 0.6, "three_month_windows_profitable": 0.6,
         "beats_matched_random_welch_t": 2.0, "neighbours_net_r": "both > 0"}
HOLDOUT_RULE = ("validation passers only, fx-majors 2017-01 -> 2022-07 (M5 built only then), models refitted each "
                "January on every trade resolved before it: t_day >= z(1-0.05/k), net R > 0, PF >= 1.1, "
                "costs x1.5 > 0, >= 55% of 3-month windows profitable")
VERDICTS = {
    "PRODUCTION CANDIDATE": "passed the holdout and the executability checks (paper/demo first, never live)",
    "STRONG RESEARCH CANDIDATE": "passed validation; holdout not yet run or failed narrowly",
    "PROMISING BUT NEEDS MORE DATA": "promoted, validation net R > 0 with t >= 2.0 but below the threshold",
    "NO EDGE": "not promoted, or validation net R <= 0",
    "INVALID / DATA PROBLEM": "the data or the pipeline cannot support a judgement",
}


def code_hash() -> str:
    h = hashlib.sha256()
    for f in CODE:
        h.update((ROOT / f).read_bytes())
    return h.hexdigest()


def _registry() -> Registry:
    return id1._registry()


def tests() -> int:
    return len(FAMILY_LIST) * len(OP.SCALES) * len(TAUS) + len(RULES) * len(OP.SCALES)


def spec(reg: Registry) -> dict:
    t_req = max(3.0, reg.threshold_for_next("fx-majors", VAL[0], VAL[1], new_tests=tests()))
    return {"program": PID, "version": OP.OPP_VERSION, "intraday_version": ID.INTRADAY_VERSION,
            "symbols": list(SYMBOLS), "development": [str(DEV[0]), str(DEV[1])],
            "development_judged": [str(DEV_OOS[0]), str(DEV_OOS[1])], "validation": [str(VAL[0]), str(VAL[1])],
            "holdout": [str(HOLD[0]), str(HOLD[1])], "folds_development": list(FOLDS_DEV),
            "folds_validation": list(FOLDS_VAL), "embargo_s": 86400,
            "template": {"stop_atr": OP.STOP_ATR, "reward_risk": OP.RR, "exit_by_utc": "20:55",
                         "entry_hours_utc": list(OP.ENTRY_HOURS), "scales": {k: list(v) for k, v in OP.SCALES.items()}},
            "features": {k: list(v) for k, v in {**OP.FEATURES, **OP.SCALE_FEATURES}.items()},
            "memory": {"n_own": OP.MEMORY_N, "n_hour": OP.MEMORY_HOUR_N, "grid_bars": OP.GRID},
            "families": {"ridge": {"alpha": 10.0}, "trees": {"depth": 3, "rounds": 150, "shrink": 0.1, "bins": 32,
                                                             "min_leaf": 1000}},
            "taus": list(TAUS), "tau_neighbour_step": TAU_STEP,
            "rules": {k: {"rule": v[0], "primary": v[1], "neighbours": v[2]} for k, v in RULES.items()},
            "controls": list(CONTROLS), "costs": COSTS.__dict__, "cost_grid": list(COST_GRID),
            "slippage_stress_pips": SLIP_STRESS, "limits": OP.Limits().__dict__, "risk_pct": RISK_PCT,
            "promote": PROMOTE, "judge": JUDGE, "holdout_rule": HOLDOUT_RULE, "tests": tests(),
            "t_required_validation": round(t_req, 4), "verdicts": VERDICTS}


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True, default=str).encode()).hexdigest()


# ── the panel: features, labels and memory for one period ──────────────

class Panel:
    """Everything the engine knows about one loaded period, per instrument and scale."""

    def __init__(self, period, tag="_2009_2016", key=None, costs: ID.Costs = COSTS, rates=None, data=None):
        self.bars = data if data is not None else id1.load(period, tag, key)
        self.period = period
        self.symbols = [s for s in SYMBOLS if s in self.bars]
        self.costs = costs
        self.rates = rates
        ctx = OP.cross_context(self.bars)
        self.ticks = {s: (_ticks(s, self.bars[s], tag) if data is None else np.full(len(self.bars[s]), np.nan))
                      for s in self.symbols}
        self.base = {s: OP.base_features(self.bars[s], self.ticks[s], ctx.get(s)) for s in self.symbols}
        self.idx = {s: OP.candidates(self.bars[s]) for s in self.symbols}
        self.lab, self.mem, self.cost_r, self.rows = {}, {}, {}, {}
        for sc in OP.SCALES:
            self._scale(sc)

    def _carry(self, s):
        return id1.carry_fn(s, self.rates) if self.rates is not None else None

    def _scale(self, sc, costs: ID.Costs | None = None):
        costs = costs or self.costs
        labs = {s: OP.label_scale(self.bars[s], self.idx[s], sc, costs, self._carry(s)) for s in self.symbols}
        if costs is self.costs:
            self.lab[sc] = labs
            self.mem[sc] = {s: OP.memory(self.bars[s], labs[s]) for s in self.symbols}
            self.cost_r[sc] = {s: OP.cost_ratio(self.bars[s], sc, costs) for s in self.symbols}
            self.rows[sc] = self._table(labs)
        return labs

    def _table(self, labs) -> dict:
        cols = {k: [] for k in ("sym", "q", "i", "side", "status", "r", "t_dec", "t_free", "day", "hour", "grid",
                                "twin")}
        start = 0
        for k, s in enumerate(self.symbols):
            b, lab = self.bars[s], labs[s]
            cols["sym"].append(np.full(len(lab.i), k, np.int16))
            cols["q"].append(np.arange(len(lab.i)))
            cols["i"].append(lab.i)
            cols["side"].append(lab.side.astype(np.int8))
            cols["status"].append(lab.status)
            cols["r"].append(lab.r.astype(np.float32))
            cols["t_dec"].append(b.t[lab.i] + ID.M5)
            cols["t_free"].append(np.where(lab.status == 0, b.t[np.maximum(lab.exit_i, 0)] + ID.M5, 0))
            cols["day"].append(b.day[lab.i])
            cols["hour"].append(b.hour[lab.i].astype(np.int8))
            cols["grid"].append(b.minute[lab.i] % (5 * OP.GRID) == 0)
            half = len(lab.i) // 2  # label_scale rows: [buys..., sells...] of the same bars
            q = np.arange(len(lab.i))
            cols["twin"].append(start + np.where(q < half, q + half, q - half))
            start += len(lab.i)
        return {k: np.concatenate(v) for k, v in cols.items()}

    def X(self, sc, rows: np.ndarray, drop=(), only=()) -> np.ndarray:
        """Design matrix for global rows of scale sc, in the given order."""
        T = self.rows[sc]
        out = None
        for k, s in enumerate(self.symbols):
            for side in (1, -1):
                m = np.flatnonzero((T["sym"][rows] == k) & (T["side"][rows] == side))
                if not len(m):
                    continue
                x, _ = OP.design(self.base[s], T["i"][rows[m]], side, self.cost_r[sc][s], self.mem[sc][s], k,
                                 len(SYMBOLS), drop, only)
                if out is None:
                    out = np.full((len(rows), x.shape[1]), np.nan, np.float32)
                out[m] = x
        return out if out is not None else np.zeros((len(rows), 0), np.float32)

    def trades(self, sc, rows, labs=None) -> list[ID.Trade]:
        labs = labs or self.lab[sc]
        T = self.rows[sc]
        out = []
        for k, s in enumerate(self.symbols):
            m = rows[T["sym"][rows] == k]
            out += OP.to_trades(s, self.bars[s], labs[s], T["q"][m])
        return sorted(out, key=lambda t: t.exit_t)


def _ticks(symbol, b: ID.Bars, tag) -> np.ndarray:
    f = id1.DATA / f"{symbol}_M5{tag}.npz"
    if not f.exists():
        return np.full(len(b), np.nan)
    d = np.load(f)
    pos = np.searchsorted(d["open_time"], b.t)
    pos = np.minimum(pos, len(d["open_time"]) - 1)
    ok = d["open_time"][pos] == b.t
    return np.where(ok, d["ticks"][pos], np.nan).astype(float)


# ── models, selection, rules ────────────────────────────────────────────

def _folds(years):
    return [(_ts(date(y, 1, 1)), _ts(date(y + 1, 1, 1))) for y in years]


def predict(P: Panel, sc: str, family: str, years, drop=(), only=(), log=None) -> np.ndarray:
    """Walk-forward predictions for every tradable row of scale sc entering in `years` (NaN
    elsewhere). Training rows: tradable GRID rows that exited before the fold (minus the embargo)."""
    T = P.rows[sc]
    tradable = T["status"] == 0
    t0 = [time.time()]

    def note(lo, n_tr, n_te):
        if log:
            log(f"  fit {family} {sc} {datetime.fromtimestamp(lo, timezone.utc).year} drop={drop} only={only} "
                f"train={n_tr} test={n_te} {time.time() - t0[0]:.0f}s")
        t0[0] = time.time()

    y = np.where(tradable, T["r"], np.nan).astype(float)
    return OP.walk_forward(T["t_dec"], np.where(tradable, T["t_free"], np.iinfo(np.int64).max), tradable & T["grid"],
                           y, lambda rows: P.X(sc, rows, drop, only), _folds(years), OP.FAMILIES[family], log=note)


def select(P: Panel, sc: str, eligible: np.ndarray, priority: np.ndarray, table: dict | None = None) -> np.ndarray:
    """The portfolio's choice among eligible rows; `table` = the rows under other costs."""
    T = table if table is not None else P.rows[sc]
    return OP.portfolio(T["sym"], T["t_dec"], T["t_free"], T["day"], T["r"], priority,
                        eligible & (T["status"] == 0), P.symbols)


def rule_rows(P: Panel, sc: str, rule: str, params: dict, period) -> tuple[np.ndarray, np.ndarray]:
    """(eligible mask, priority) over the scale's rows for a deterministic rule in `period`."""
    T = P.rows[sc]
    lo, hi = _ts(period[0]), _ts(period[1])
    elig = np.zeros(len(T["r"]), bool)
    for k, s in enumerate(P.symbols):
        b, f = P.bars[s], P.base[s]
        n = len(b)
        side_at = np.zeros(n)
        if rule == "MOM":
            z = f["z12"].astype(float)
            side_at = np.where(np.abs(z) >= params["z"], np.sign(z), 0.0)
        elif rule == "MR":
            d = f["dev20"].astype(float)
            side_at = np.where(np.abs(d) >= params["d"], -np.sign(d), 0.0)
        elif rule == "BRK":
            nn = params["n"]
            ph, pl = OP.lag(ID.rolling_max(b.h, nn), 1), OP.lag(ID.rolling_min(b.l, nn), 1)
            with np.errstate(invalid="ignore"):
                brk = np.where(b.c > ph, 1.0, np.where(b.c < pl, -1.0, 0.0))
            side_at = np.where((brk != 0) & (OP.lag(brk, 1) != brk), brk, 0.0)
        elif rule == "SWEEP":
            ev = np.zeros(n)
            for fn in (ID.sweep_pd, ID.sweep_asia, ID.sweep_equal):
                for sg in fn(b, pen=params["pen"]):
                    ev[sg.i] = sg.side
            side_at = ev
        side_at = np.nan_to_num(side_at)
        m = T["sym"] == k
        rows = np.flatnonzero(m)
        want = side_at[T["i"][rows]]
        elig[rows] = (want != 0) & (want == T["side"][rows])
    elig &= (T["t_dec"] >= lo) & (T["t_dec"] < hi)
    return elig, np.ones(len(elig))


def random_rows(P: Panel, sc: str, period, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Control: one random tradable candidate per instrument-day, random side."""
    T = P.rows[sc]
    rng = np.random.default_rng(seed)
    lo, hi = _ts(period[0]), _ts(period[1])
    elig = np.zeros(len(T["r"]), bool)
    ok = (T["status"] == 0) & (T["t_dec"] >= lo) & (T["t_dec"] < hi)
    for k in range(len(P.symbols)):
        rows = np.flatnonzero(ok & (T["sym"] == k))
        if not len(rows):
            continue
        days = T["day"][rows]
        for d in np.unique(days):
            cand = rows[days == d]
            pick = cand[rng.integers(len(cand))]
            want = 1 if rng.random() < 0.5 else -1
            # the same bar on the wanted side: rows are [buys..., sells...] per instrument
            row = pick if T["side"][pick] == want else T["twin"][pick]
            if ok[row]:
                elig[row] = True
    return elig, np.ones(len(elig))


def matched_rows(P: Panel, sc: str, chosen: np.ndarray, seed: int) -> np.ndarray:
    """Matched random control for a selection: the same number of candidates, drawn at random from
    tradable rows in the same UTC hours (sampled from the selection's hours) and the same period,
    random side; then through the same portfolio."""
    T = P.rows[sc]
    if not len(chosen):
        return np.zeros(0, np.int64)
    rng = np.random.default_rng(seed)
    lo, hi = T["t_dec"][chosen].min(), T["t_dec"][chosen].max() + 1
    ok = (T["status"] == 0) & (T["t_dec"] >= lo) & (T["t_dec"] < hi)
    by_hour = {h: np.flatnonzero(ok & (T["hour"] == h)) for h in np.unique(T["hour"][chosen])}
    hours = T["hour"][chosen]
    elig = np.zeros(len(T["r"]), bool)
    for _ in range(len(chosen)):
        h = int(hours[rng.integers(len(hours))])
        pool = by_hour[h]
        elig[pool[rng.integers(len(pool))]] = True
    return select(P, sc, elig, rng.random(len(elig)))


# ── evaluation ──────────────────────────────────────────────────────────

def regimes(P: Panel, trades) -> dict:
    """`id1.regimes` (ATR in the top/bottom half of its past week; 48-bar efficiency ratio >= 0.3 =
    trending), from arrays computed once per panel."""
    if not hasattr(P, "_regime"):
        P._regime = {}
        for s in P.symbols:
            c = P.bars[s].c
            move = np.abs(np.r_[np.full(48, np.nan), c[48:] - c[:-48]])
            path = np.r_[np.full(48, np.nan), np.convolve(np.abs(np.diff(c)), np.ones(48), "valid")]
            with np.errstate(invalid="ignore", divide="ignore"):
                P._regime[s] = (P.base[s]["atr_rank"].astype(float), move / np.where(path > 0, path, np.nan))
    out = {"high_vol": [], "low_vol": [], "trending": [], "ranging": []}
    for t in trades:
        rk, er = P._regime[t.symbol]
        i = t.signal_i
        if np.isfinite(rk[i]):
            out["high_vol" if rk[i] >= 0.5 else "low_vol"].append(t.r)
        if np.isfinite(er[i]):
            out["trending" if er[i] >= 0.3 else "ranging"].append(t.r)
    return {k: {"trades": len(v), "net_r": round(float(np.mean(v)), 4) if v else None} for k, v in out.items()}


def evaluate(P: Panel, trades, period) -> dict:
    s = id1.evaluate(trades, period)
    if not trades:
        return s
    s["regimes"] = regimes(P, trades)
    s["concurrency"] = id1.concurrency(trades)
    r = np.array([t.r for t in trades])
    side = np.array([t.side for t in trades])
    s["direction"] = {nm: {"trades": int((side == v).sum()),
                           "net_r": round(float(r[side == v].mean()), 4) if (side == v).any() else None}
                      for nm, v in (("buy", 1), ("sell", -1))}
    held = np.array([(t.exit_i - t.entry_i + 1) * 5 for t in trades])
    s["holding_minutes"] = {"mean": round(float(held.mean()), 1), "median": float(np.median(held)),
                            "p90": float(np.quantile(held, 0.9))}
    s["cost_r_per_trade"] = round(float(np.mean([(t.spread + t.slippage + t.commission - t.financing) / t.risk
                                                  for t in trades])), 4)
    wk: dict = {}
    for t in trades:
        wk[(t.exit_t - 4 * 86400) // (7 * 86400)] = wk.get((t.exit_t - 4 * 86400) // (7 * 86400), 0.0) + t.r
    lo_w, hi_w = (_ts(period[0]) - 4 * 86400) // (7 * 86400), (_ts(period[1]) - 4 * 86400) // (7 * 86400)
    weeks = np.array([wk.get(w, 0.0) for w in range(lo_w, hi_w)]) * RISK_PCT
    s["weekly"] = {"weeks": len(weeks), "profitable_share": round(float(np.mean(weeks > 0)), 3),
                   "median_pct": round(float(np.median(weeks)), 3), "worst_pct": round(float(weeks.min()), 2),
                   "best_pct": round(float(weeks.max()), 2)}
    neg = r[r < 0]
    daily = None
    if s.get("sharpe") is not None and len(neg):
        dd = np.sqrt(np.mean(np.minimum(r, 0) ** 2))
        daily = round(float(r.mean() / dd), 4) if dd > 0 else None
    s["sortino_per_trade"] = daily
    s["gross_total_r"] = round(float(np.sum([t.gross_mid / t.risk for t in trades])), 2)
    w3 = s.get("windows", {}).get("3m", {})
    s["three_month"] = w3
    return s


def brief(s: dict) -> dict:
    out = id1._brief(s)
    for k in ("holding_minutes", "cost_r_per_trade", "direction", "weekly", "gross_total_r", "sortino_per_trade"):
        out[k] = s.get(k)
    return out


def promote_gates(s: dict, x125: dict, vs_random) -> dict:
    sym = [v for v in s.get("by_symbol", {}).values() if v["trades"] >= 30]
    return {"min_trades": s.get("trades", 0) >= PROMOTE["min_trades"], "net_r": (s.get("net_r") or 0) > 0,
            "t_day": (s.get("t_day") or 0) >= PROMOTE["t_day"],
            "profit_factor": (s.get("profit_factor") or 0) >= PROMOTE["profit_factor"],
            "costs_x1.25": (x125.get("net_r") or 0) > 0,
            "beats_matched_random": (vs_random or 0) >= PROMOTE["beats_matched_random_welch_t"],
            "symbols_positive": bool(sym) and np.mean([v["net_r"] > 0 for v in sym]) >= PROMOTE["symbols_positive_share"]}


def run_selection(P: Panel, sc: str, elig: np.ndarray, prio: np.ndarray, period, costs: ID.Costs | None = None):
    """Rows chosen and their trades, at the panel's costs or re-labelled under `costs` (the same
    eligibility and priority: the estimate is not refitted for a stress)."""
    if costs is None:
        rows = select(P, sc, elig, prio)
        return rows, P.trades(sc, rows)
    cache = P.__dict__.setdefault("_stress", {})
    if (sc, costs) not in cache:
        labs = P._scale(sc, costs)
        cache[(sc, costs)] = (labs, P._table(labs))
    labs, table = cache[(sc, costs)]
    rows = select(P, sc, elig, prio, table)
    return rows, P.trades(sc, rows, labs)


def rank_report(P: Panel, sc: str, pred: np.ndarray) -> dict:
    """Does the estimate rank candidates? Realised net R by predicted decile over every tradable
    out-of-sample row, the Spearman rank correlation, and the share of rows predicted above 0."""
    T = P.rows[sc]
    m = np.isfinite(pred) & (T["status"] == 0)
    p, r = pred[m], T["r"][m].astype(float)
    if len(p) < 100:
        return {"rows": int(len(p))}
    order = np.argsort(p, kind="stable")
    dec = np.empty(len(p), int)
    dec[order] = np.arange(len(p)) * 10 // len(p)
    rk_p = np.empty(len(p))
    rk_p[order] = np.arange(len(p))
    rk_r = np.empty(len(p))
    rk_r[np.argsort(r, kind="stable")] = np.arange(len(p))
    ic = float(np.corrcoef(rk_p, rk_r)[0, 1])
    return {"rows": int(len(p)), "spearman_ic": round(ic, 4),
            "deciles": [{"decile": d + 1, "mean_pred": round(float(p[dec == d].mean()), 4),
                         "mean_r": round(float(r[dec == d].mean()), 4)} for d in range(10)],
            "top_decile_r": round(float(r[dec == 9].mean()), 4), "all_r": round(float(r.mean()), 4),
            "share_pred_above_0": round(float(np.mean(p > 0)), 5),
            "share_pred_above_0.05": round(float(np.mean(p > 0.05)), 5)}


def judge_selection(P, sc, elig, prio, period, seed_base) -> tuple[dict, list, np.ndarray]:
    rows, tr = run_selection(P, sc, elig, prio, period)
    s = evaluate(P, tr, period)
    mr = []
    for sd in RANDOM_SEEDS:
        mr += P.trades(sc, matched_rows(P, sc, rows, sd + seed_base))
    vs = welch_t(np.array([t.r for t in tr]), np.array([t.r for t in mr])) if len(tr) > 1 and len(mr) > 1 else None
    return {"summary": brief(s), "detail": s, "matched_random": brief(evaluate(P, sorted(mr, key=lambda t: t.exit_t), period)),
            "vs_matched_random_welch_t": round(vs, 3) if vs is not None else None}, tr, rows


def _seed(name: str) -> int:
    """A seed fixed by the hypothesis name (Python's str hash is randomised per process)."""
    return int(hashlib.sha256(name.encode()).hexdigest()[:6], 16) % 1000


def _dump(x) -> str:
    return id1._dump(x)


def _write(name, body, where=OUT):
    body = json.loads(json.dumps(body, sort_keys=True, default=str))
    body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    (where / f"{name}.json").write_text(_dump(body))
    return body


# ── commands ────────────────────────────────────────────────────────────

def _check_frozen(reg, trial_id=PID):
    frozen = json.loads(SPEC.read_text())
    if reg.get(trial_id).design.get("spec_sha256") != frozen["sha256"] or frozen["code_sha256"] != code_hash():
        raise SystemExit("the spec or the code differs from what was preregistered")
    return frozen


def cmd_spec():
    reg = _registry()
    if any(t.id == PID for t in reg.trials):
        raise SystemExit(f"{PID} is registered; its spec is frozen")
    s = spec(reg)
    SPEC.write_text(_dump({"spec": s, "sha256": spec_sha(s), "code_sha256": code_hash()}))
    print(spec_sha(s), "tests", s["tests"], "t_required_validation", s["t_required_validation"])


def cmd_preregister(now):
    reg = _registry()
    frozen = json.loads(SPEC.read_text())
    if spec_sha(spec(reg)) != frozen["sha256"] or code_hash() != frozen["code_sha256"]:
        raise SystemExit("the spec or the code changed since `spec`")
    if frozen["sha256"] not in (ROOT / DOC).read_text():
        raise SystemExit(f"{DOC} must quote the spec sha256")
    reg.register(Trial(id=PID, registered=now, title="ID-2: intraday opportunity engine (scanner + walk-forward EV model)",
                       hypothesis="Does a walk-forward estimate of each M5 candidate's net R, built from every family "
                                  "of market information, select trades with a significant positive net expectancy "
                                  "after measured costs and the risk engine's limits, beyond matched random entries "
                                  "and simple deterministic rules?",
                       uses=(Use("fx-majors", DEV[0], DEV[1], "select"), Use("fx-majors", VAL[0], VAL[1], "judge")),
                       tests=tests(), configurations=tests() + len(CONTROLS) * len(OP.SCALES),
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"]}))
    print("registered", PID)


def _log(msg):
    print(f"{datetime.now(timezone.utc):%H:%M:%S} {msg}", flush=True)


def _cached_pred(P, sc, fam, years, drop=(), only=(), tag="dev"):
    CACHE.mkdir(parents=True, exist_ok=True)
    key = f"{tag}_{sc}_{fam}_drop-{'-'.join(drop)}_only-{'-'.join(only)}_{code_hash()[:12]}.npy"
    f = CACHE / key
    if f.exists():
        return np.load(f)
    pred = predict(P, sc, fam, years, drop, only, log=_log)
    np.save(f, pred)
    return pred


def development(P: Panel, body: dict) -> list[str]:
    """Stage 1: every model configuration, rule and control on 2011-2013, out of sample."""
    T_lo, T_hi = _ts(DEV_OOS[0]), _ts(DEV_OOS[1])
    preds = {}
    body["ranking"] = {}
    for sc in OP.SCALES:
        for fam in FAMILY_LIST:
            preds[(sc, fam)] = _cached_pred(P, sc, fam, FOLDS_DEV)
            body["ranking"][f"{fam}-{sc}"] = rank_report(P, sc, preds[(sc, fam)])
            _log(f"rank {fam}-{sc} {json.dumps({k: v for k, v in body['ranking'][f'{fam}-{sc}'].items() if k != 'deciles'})}")
    dev: dict = {}
    for sc in OP.SCALES:
        T = P.rows[sc]
        in_oos = (T["t_dec"] >= T_lo) & (T["t_dec"] < T_hi)
        for c in CONTROLS:
            tr = []
            for sd in RANDOM_SEEDS:
                e, pr = random_rows(P, sc, DEV_OOS, sd)
                tr += run_selection(P, sc, e, pr, DEV_OOS)[1]
            s = evaluate(P, sorted(tr, key=lambda t: t.exit_t), DEV_OOS)
            body["controls"][f"{c}-{sc}"] = {"development": brief(s)}
            _log(f"{c}-{sc} {json.dumps(id1._brief(s))}")
        hyps = [(f"M-{fam}-{sc}-tau{tau:.2f}", ("model", fam, tau)) for fam in FAMILY_LIST for tau in TAUS]
        hyps += [(f"R-{rule}-{sc}", ("rule", rule, RULES[rule][1])) for rule in RULES]
        for hid, (kind, a, b_) in hyps:
            if kind == "model":
                p = preds[(sc, a)]
                elig, prio = in_oos & np.isfinite(p) & (p > b_), np.nan_to_num(p, nan=-9.0)
            else:
                elig, prio = rule_rows(P, sc, a, b_, DEV_OOS)
            res, tr, rows = judge_selection(P, sc, elig, prio, DEV_OOS, seed_base=_seed(hid))
            x125 = evaluate(P, run_selection(P, sc, elig, prio, DEV_OOS, COSTS.stressed(1.25))[1], DEV_OOS)
            g = promote_gates(res["detail"], x125, res["vs_matched_random_welch_t"])
            res.update({"costs_x1.25": brief(x125), "gates": g, "promoted": all(g.values()), "scale": sc})
            dev[hid] = res
            _log(f"{hid} {json.dumps(id1._brief(res['detail']))} vsR {res['vs_matched_random_welch_t']} "
                 f"promoted {res['promoted']}")
    body["development"] = dev
    passers = [h for h, v in dev.items() if v["promoted"]]
    ranked = sorted(passers, key=lambda h: -(dev[h]["summary"]["t_day"] or 0))
    return ranked[:1]


def ablations(P: Panel, body: dict):
    """Descriptive, development out-of-sample only: which information carries the ranking?"""
    out = {}
    for sc in OP.SCALES:
        for g in OP.GROUPS:
            for mode in ("drop", "only"):
                kw = {"drop": (g,)} if mode == "drop" else {"only": (g,)}
                p = _cached_pred(P, sc, "ridge", FOLDS_DEV, **kw)
                rr = rank_report(P, sc, p)
                out[f"ridge-{sc}-{mode}-{g}"] = {k: rr.get(k) for k in ("spearman_ic", "top_decile_r", "all_r",
                                                                        "share_pred_above_0")}
    ics = {sc: body["ranking"][f"trees-{sc}"].get("spearman_ic") or -9 for sc in OP.SCALES}
    best = max(ics, key=ics.get)
    body["ablation_trees_scale"] = best
    for g in OP.GROUPS:
        p = _cached_pred(P, best, "trees", FOLDS_DEV, drop=(g,))
        rr = rank_report(P, best, p)
        out[f"trees-{best}-drop-{g}"] = {k: rr.get(k) for k in ("spearman_ic", "top_decile_r", "all_r",
                                                                 "share_pred_above_0")}
        _log(f"ablation trees-{best}-drop-{g} {json.dumps(out[f'trees-{best}-drop-{g}'])}")
    body["ablations"] = out


def validate(P: Panel, hid: str, dev_res: dict, t_req: float) -> dict:
    sc = dev_res["scale"]
    T = P.rows[sc]
    lo, hi = _ts(VAL[0]), _ts(VAL[1])
    in_val = (T["t_dec"] >= lo) & (T["t_dec"] < hi)
    if hid.startswith("M-"):
        _, fam, _, tau_s = hid.split("-")
        tau = float(tau_s[3:])
        p = _cached_pred(P, sc, fam, FOLDS_VAL, tag="val")

        def sel(t):
            return in_val & np.isfinite(p) & (p > t), np.nan_to_num(p, nan=-9.0)

        main = sel(tau)
        neigh = [sel(round(tau - TAU_STEP, 4)), sel(round(tau + TAU_STEP, 4))]
    else:
        rule = hid.split("-")[1]
        main = rule_rows(P, sc, rule, RULES[rule][1], VAL)
        neigh = [rule_rows(P, sc, rule, q, VAL) for q in RULES[rule][2]]
    res, tr, rows = judge_selection(P, sc, *main, VAL, seed_base=_seed(hid) + 7)
    s = res["detail"]
    stress = {f"x{k}": brief(evaluate(P, run_selection(P, sc, *main, VAL, COSTS.stressed(k))[1], VAL)) for k in COST_GRID}
    stress["slippage_0.3"] = brief(evaluate(P, run_selection(P, sc, *main, VAL, ID.Costs(slippage_pips=SLIP_STRESS))[1], VAL))
    nb = [brief(evaluate(P, run_selection(P, sc, *n, VAL)[1], VAL)) for n in neigh]
    sym = [v for v in s.get("by_symbol", {}).values() if v["trades"] >= 30]
    gates = {"t_day": (s.get("t_day") or 0) >= t_req, "net_r": (s.get("net_r") or 0) > 0,
             "profit_factor": (s.get("profit_factor") or 0) >= 1.2,
             "costs_x1.5": (stress["x1.5"].get("net_r") or 0) > 0,
             "slippage_0.3": (stress["slippage_0.3"].get("net_r") or 0) > 0,
             "symbols_positive": bool(sym) and np.mean([v["net_r"] > 0 for v in sym]) >= 0.6,
             "three_month_windows": (s.get("windows", {}).get("3m", {}).get("profitable_share") or 0) >= 0.6,
             "beats_matched_random": (res["vs_matched_random_welch_t"] or 0) >= 2.0,
             "neighbours": all((n.get("net_r") or 0) > 0 for n in nb)}
    res.update({"stress": stress, "neighbours": nb, "gates": gates, "passed": all(gates.values())})
    return res


def cmd_run(now):
    reg = _registry()
    frozen = _check_frozen(reg)
    if reg.verdict_of(PID) is not None:
        raise SystemExit(f"{PID} already has a verdict")
    t_req = frozen["spec"]["t_required_validation"]
    rates = rc.Rates(ROOT / "data" / "rc" / "policy_rates.csv")
    body: dict = {"program": PID, "spec_sha256": frozen["sha256"], "t_required_validation": t_req,
                  "development": {}, "controls": {}, "validation": {}}
    _log("loading development 2009-2013")
    P = Panel(DEV, rates=rates)
    body["candidates"] = {sc: {"rows": int(len(P.rows[sc]["r"])), "tradable": int((P.rows[sc]["status"] == 0).sum()),
                               "risk_check_rejected": int((P.rows[sc]["status"] == 3).sum())} for sc in OP.SCALES}
    promoted = development(P, body)
    body["promoted"] = promoted
    ablations(P, body)
    _write(f"{PID}-development", body, R / "results")  # a checkpoint, not a verdict
    del P
    if promoted:
        _log(f"loading validation (models refit each January from 2009); promoted {promoted}")
        V = Panel((DEV[0], VAL[1]), rates=rates)
        for c in CONTROLS:
            for sc in OP.SCALES:
                tr = []
                for sd in RANDOM_SEEDS:
                    tr += run_selection(V, sc, *random_rows(V, sc, VAL, sd), VAL)[1]
                body["controls"][f"{c}-{sc}"]["validation"] = brief(evaluate(V, sorted(tr, key=lambda t: t.exit_t), VAL))
        for hid in promoted:
            body["validation"][hid] = validate(V, hid, body["development"][hid], t_req)
            _log(f"{hid} val {json.dumps(id1._brief(body['validation'][hid]['detail']))} "
                 f"passed {body['validation'][hid]['passed']}")
    passers = [h for h in promoted if body["validation"][h]["passed"]]
    body["passers"], body["verdict"] = passers, ("PASSED" if passers else "FAILED")
    art = _write(PID, body)
    reg.record_verdict(Verdict(PID, now, art["verdict"], {"artifact": f"research/knowledge/{PID}.json",
                                                          "artifact_sha256": art["sha256"]}))
    _log(f"verdict {art['verdict']} promoted {promoted} passers {passers}")


def cmd_holdout(now):
    reg = _registry()
    frozen = _check_frozen(reg)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    passers = judged["passers"]
    if not passers:
        raise SystemExit("nothing passed validation: the fx-majors holdout stays sealed")
    reg.register(Trial(id=HID, registered=now, title="ID-2 holdout: fx-majors 2017-01 -> 2022-07 (M5)",
                       hypothesis=", ".join(passers), uses=(Use("fx-majors", HOLD[0], date(2100, 1, 1), "judge"),),
                       tests=len(passers), configurations=len(passers), preregistration=DOC,
                       design={"spec_sha256": frozen["sha256"], "candidates": passers}))
    key = open_final_test(reg, HID)
    rates = rc.Rates(ROOT / "data" / "rc" / "policy_rates.csv")
    hold_bars = id1.load(HOLD, tag="_2017_2022", key=key)
    train_bars = id1.load((DEV[0], VAL[1]))
    data = {s: _concat(train_bars[s], hold_bars[s]) for s in hold_bars if s in train_bars}
    H = Panel((DEV[0], HOLD[1]), rates=rates, data=data)
    z = NormalDist().inv_cdf(1 - 0.05 / len(passers))
    years = tuple(range(HOLD[0].year, HOLD[1].year + 1))
    out = {}
    for hid in passers:
        sc = judged["development"][hid]["scale"]
        T = H.rows[sc]
        lo, hi = _ts(HOLD[0]), _ts(HOLD[1])
        inh = (T["t_dec"] >= lo) & (T["t_dec"] < hi)
        if hid.startswith("M-"):
            _, fam, _, tau_s = hid.split("-")
            p = predict(H, sc, fam, years, log=_log)
            elig, prio = inh & np.isfinite(p) & (p > float(tau_s[3:])), np.nan_to_num(p, nan=-9.0)
        else:
            rule = hid.split("-")[1]
            elig, prio = rule_rows(H, sc, rule, RULES[rule][1], HOLD)
        s = evaluate(H, run_selection(H, sc, elig, prio, HOLD)[1], HOLD)
        x15 = evaluate(H, run_selection(H, sc, elig, prio, HOLD, COSTS.stressed(1.5))[1], HOLD)
        g = {"t_day": (s.get("t_day") or 0) >= z, "net_r": (s.get("net_r") or 0) > 0,
             "profit_factor": (s.get("profit_factor") or 0) >= 1.1, "costs_x1.5": (x15.get("net_r") or 0) > 0,
             "three_month_windows": (s.get("windows", {}).get("3m", {}).get("profitable_share") or 0) >= 0.55}
        out[hid] = {"summary": brief(s), "detail": s, "costs_x1.5": brief(x15), "gates": g,
                    "verdict": "VALIDATED" if all(g.values()) else "REJECTED"}
    verdict = "PASSED" if any(v["verdict"] == "VALIDATED" for v in out.values()) else "FAILED"
    art = _write(HID, {"program": HID, "holdout_of": PID, "results": out, "verdict": verdict, "t_required": round(z, 4)})
    reg.record_verdict(Verdict(HID, now, verdict, {"artifact": f"research/knowledge/{HID}.json", "artifact_sha256": art["sha256"]}))
    _log(f"holdout verdict {verdict}")


def _concat(a: ID.Bars, b: ID.Bars) -> ID.Bars:
    keep = a.t < b.t[0]
    return ID.Bars(a.symbol, a.pip, *(np.r_[getattr(a, k)[keep], getattr(b, k)] for k in
                                      ("t", "bo", "bh", "bl", "bc", "ao", "ah", "al", "ac")))


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc)
    {"spec": cmd_spec, "preregister": lambda: cmd_preregister(now), "run": lambda: cmd_run(now),
     "holdout": lambda: cmd_holdout(now)}.get(cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    sys.exit(main())
