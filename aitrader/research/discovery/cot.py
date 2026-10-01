"""COT-1: CFTC positioning as directional information for the seven direct USD pairs.

Everything is computed per COT REPORT and placed on one D1 bar: the DECISION BAR, the first bar
whose close (17:00 New York) is at or after the report's release time (aitrader/data/cot.py). A
report superseded before any bar closed (the next report already public) makes no decision. Each
decision is one trade at most, entered at the next bar's open by the shared exit simulator.

Features of a report, all signed so that + is BULLISH THE CURRENCY (its value in USD rises):

    spec          Leveraged Money net position / open interest (TFF's speculators)
    dealer, am    Dealer and Asset Manager net / open interest (descriptive only)
    *_pct         percentile of the value among the reports of the previous 52 weeks
                  (as-of in [as-of - 364 days, as-of)); ties count half; >= 39 reports or NaN
    *_z           z-score against the same window (sample standard deviation)
    spec_flow     spec minus spec of the report 25..31 days earlier (4 weeks); NaN if none
    spec_step     spec minus spec of the report 4..10 days earlier (1 week); NaN if none
    px            log value of the currency in USD at the decision bar's close (mid)
    px_flow       px minus px of the report 25..31 days earlier
    trend         log change of the currency's value over the 65 D1 bars before the decision bar
    vix           Cboe VIX close public at the decision bar (16:45 New York)

The price features are sampled on the SAME weekly decision bars as the positioning, so a price-only
control and a positioning rule see the same opportunities, timing and exits. Every rule also
requires `spec_pct` to be defined, so the decision set is identical across controls and rules.

A rule maps a report to a CURRENCY direction (+1 buy the currency, -1 sell it, 0 nothing); the pair's
side is that times the pair's orientation (+1 for CCYUSD, -1 for USDCCY). Thresholds are fixed:
an extreme is a percentile >= 0.90 or <= 0.10. Nothing is fitted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import NormalDist
from typing import Callable

import numpy as np

from ...data.bars import BarSeries
from ...data.cot import CotSeries
from ..labels import BUY, SELL
from .exits import EXIT_BY_KEY
from .study import Study, Trades

COT_STUDY_VERSION = "cot-study-1.0.0"
#: pair -> (currency of its CME future, orientation: +1 the pair rises with the currency)
PAIRS = {"AUDUSD": ("AUD", 1), "EURUSD": ("EUR", 1), "GBPUSD": ("GBP", 1), "NZDUSD": ("NZD", 1),
         "USDCAD": ("CAD", -1), "USDCHF": ("CHF", -1), "USDJPY": ("JPY", -1)}
DAY = 86400
WINDOW_DAYS = 364
MIN_HISTORY = 39
HI, LO = 0.90, 0.10
NEIGHBOURS = ((0.85, 0.15), (0.95, 0.05))
FLOW_DAYS = (25, 31)
STEP_DAYS = (4, 10)
TREND_BARS = 65
VIX_LEVEL = 20.0
TRAILED = ("spec", "spec_flow", "px", "px_flow")


def trailing(x: np.ndarray, days: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(percentile, z) of each value among the finite values of the previous 52 weeks."""
    m = len(x)
    pct, z = np.full(m, np.nan), np.full(m, np.nan)
    lo = np.searchsorted(days, days - WINDOW_DAYS, side="left")
    for j in range(m):
        if not np.isfinite(x[j]):
            continue
        prev = x[lo[j]:j]
        prev = prev[np.isfinite(prev)]
        if len(prev) < MIN_HISTORY:
            continue
        pct[j] = (np.sum(prev < x[j]) + 0.5 * np.sum(prev == x[j])) / len(prev)
        sd = prev.std(ddof=1)
        if sd > 0:
            z[j] = (x[j] - prev.mean()) / sd
    return pct, z


def lagged(x: np.ndarray, days: np.ndarray, window: tuple[int, int]) -> np.ndarray:
    """The value of the latest earlier report dated `window[0]..window[1]` days before; NaN if none."""
    k = np.searchsorted(days, days - window[0], side="right") - 1
    out = np.full(len(x), np.nan)
    ok = k >= 0
    ok[ok] &= days[k[ok]] >= days[ok] - window[1]
    out[ok] = x[k[ok]]
    return out


@dataclass
class Weekly:
    """One row per COT report for one pair: its decision bar and every feature, point in time."""

    symbol: str
    currency: str
    orient: int
    n_bars: int
    as_of: np.ndarray
    available_at: np.ndarray
    row: np.ndarray  # decision bar index, -1 when the report made no decision
    f: dict = field(default_factory=dict)


def weekly(series: BarSeries, cot: CotSeries, vix=None) -> Weekly:
    ccy, orient = PAIRS[series.symbol]
    if cot.currency != ccy:
        raise ValueError(f"{series.symbol} needs the {ccy} future, not {cot.currency}")
    t_bar = np.asarray(series.available_at, np.int64)
    n, m = len(t_bar), len(cot)
    av = np.asarray(cot.available_at, np.int64)
    row = np.searchsorted(t_bar, av, side="left")
    nxt = np.full(m, np.iinfo(np.int64).max, np.int64)
    nxt[:-1] = av[1:]
    ok = row < n
    ok[ok] &= t_bar[row[ok]] < nxt[ok]  # superseded before any bar closed: no decision
    row = np.where(ok, row, -1)
    days = np.asarray(cot.as_of, np.int64) // DAY
    oi = cot.fields["oi"]
    f = {}
    with np.errstate(invalid="ignore", divide="ignore"):
        f["spec"] = np.where(oi > 0, cot.net("lev") / oi, np.nan)
        f["dealer"] = np.where(oi > 0, cot.net("dealer") / oi, np.nan)
        f["am"] = np.where(oi > 0, cot.net("am") / oi, np.nan)
    f["spec_flow"] = f["spec"] - lagged(f["spec"], days, FLOW_DAYS)
    f["spec_step"] = f["spec"] - lagged(f["spec"], days, STEP_DAYS)
    lc = np.log(np.asarray(series.mid_close, float))
    px = np.full(m, np.nan)
    px[ok] = orient * lc[row[ok]]
    f["px"] = px
    f["px_flow"] = px - lagged(px, days, FLOW_DAYS)
    tr = np.full(m, np.nan)
    okt = ok & (row >= TREND_BARS)
    tr[okt] = orient * (lc[row[okt]] - lc[row[okt] - TREND_BARS])
    f["trend"] = tr
    vx = np.full(m, np.nan)
    if vix is not None and ok.any():
        vx[ok] = vix.asof(t_bar[row[ok]])
    f["vix"] = vx
    for name in TRAILED:
        f[f"{name}_pct"], f[f"{name}_z"] = trailing(f[name], days)
    return Weekly(series.symbol, ccy, orient, n, np.asarray(cot.as_of), av, row, f)


# ── rules: a report -> a currency direction ───────────────────────────────────────────────────────

class Extremes:
    """+1 where a trailed feature is at a bullish extreme, -1 at a bearish one, 0 otherwise or unknown.
    `z`: the z-score definition with the normal quantiles of the same levels (a robustness variant)."""

    def __init__(self, f: dict, hi: float = HI, lo: float = LO, z: bool = False) -> None:
        self.f, self.hi, self.lo, self.z = f, hi, lo, z

    def __call__(self, name: str) -> np.ndarray:
        if self.z:
            x, h, l = self.f[f"{name}_z"], NormalDist().inv_cdf(self.hi), NormalDist().inv_cdf(self.lo)
        else:
            x, h, l = self.f[f"{name}_pct"], self.hi, self.lo
        out = np.zeros(len(x), np.int8)
        ok = np.isfinite(x)
        out[ok & (x >= h)] = 1
        out[ok & (x <= l)] = -1
        return out

    def defined(self, name: str) -> np.ndarray:
        return np.isfinite(self.f[f"{name}_z" if self.z else f"{name}_pct"])


def _agree(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.where((a != 0) & (a == b), a, 0).astype(np.int8)


def _trend_sign(f: dict) -> np.ndarray:
    t = f["trend"]
    out = np.zeros(len(t), np.int8)
    ok = np.isfinite(t)
    out[ok] = np.sign(t[ok]).astype(np.int8)
    return out


def _r_p(E, f):
    return E("spec")


def _r_c(E, f):
    return _agree(E("spec"), E("px"))


def _r_i(E, f):
    e, q = E("spec"), E("px")
    return np.where(E.defined("px") & (q != e), e, 0).astype(np.int8)


def _r_f(E, f):
    return E("spec_flow")


def _r_u(E, f):
    e, st = E("spec"), f["spec_step"]
    ok = np.isfinite(st)
    turning = ok & (((e == 1) & (st < 0)) | ((e == -1) & (st > 0)))
    return np.where(turning, e, 0).astype(np.int8)


def _r_v(E, f):
    v = f["vix"]
    stressed = np.isfinite(v) & (v >= VIX_LEVEL)
    return np.where(stressed, E("spec"), 0).astype(np.int8)


def _r_x(E, f):
    return _agree(_trend_sign(f), E("spec"))


def _c_a(E, f):
    return E("px")


def _c_af(E, f):
    return E("px_flow")


def _c_av(E, f):
    v = f["vix"]
    stressed = np.isfinite(v) & (v >= VIX_LEVEL)
    return np.where(stressed, E("px"), 0).astype(np.int8)


def _c_trend(E, f):
    return _trend_sign(f)


def _c_uncrowded(E, f):
    s = _trend_sign(f)
    return np.where(_agree(s, E("spec")) != 0, 0, s).astype(np.int8)


@dataclass(frozen=True)
class Rule:
    name: str
    base: Callable  # (Extremes, features) -> the state's direction (+1 bullish currency)
    mapping: int  # +1 trade with the state (continuation), -1 against it (reversal)
    text: str

    def direction(self, w: Weekly, hi: float = HI, lo: float = LO, z: bool = False) -> np.ndarray:
        E = Extremes(w.f, hi, lo, z)
        d = (self.mapping * self.base(E, w.f)).astype(np.int8)
        d[~E.defined("spec")] = 0  # one decision set for every rule and control
        return d


RULES = {r.name: r for r in (
    Rule("p_rev", _r_p, -1, "Leveraged Money net/OI at a 52-week extreme (pct >= 0.90 / <= 0.10): trade AGAINST it"),
    Rule("p_cont", _r_p, 1, "Leveraged Money net/OI at a 52-week extreme: trade WITH it"),
    Rule("c_rev", _r_c, -1, "positioning AND price both at a same-side 52-week extreme: trade against them"),
    Rule("c_cont", _r_c, 1, "positioning AND price both at a same-side 52-week extreme: trade with them"),
    Rule("i_rev", _r_i, -1, "positioning at an extreme while price is NOT at the same-side extreme: trade against "
                            "the positioning"),
    Rule("i_cont", _r_i, 1, "positioning at an extreme while price is not: trade with the positioning"),
    Rule("f_cont", _r_f, 1, "4-week change of Leveraged Money net/OI at a 52-week extreme: trade WITH the flow"),
    Rule("f_rev", _r_f, -1, "4-week positioning change at a 52-week extreme: trade AGAINST the flow"),
    Rule("u_rev", _r_u, -1, "positioning at an extreme AND last week's change points back (the unwind has "
                            "started): trade against the positioning"),
    Rule("v_rev", _r_v, -1, "positioning at an extreme while VIX >= 20: trade against the positioning"),
    Rule("x_veto", _r_x, 1, "the 13-week trend trade taken where positioning is already at an extreme in the "
                            "trend's direction (crowded)"),
    # price-only controls: the same decision bars, timing, exit and costs, no positioning information
    Rule("a_rev", _c_a, -1, "CONTROL: price at a 52-week extreme of its weekly samples: trade against it"),
    Rule("a_cont", _c_a, 1, "CONTROL: price at a 52-week extreme: trade with it"),
    Rule("af_cont", _c_af, 1, "CONTROL: 4-week price change at a 52-week extreme: trade with it"),
    Rule("af_rev", _c_af, -1, "CONTROL: 4-week price change at a 52-week extreme: trade against it"),
    Rule("av_rev", _c_av, -1, "CONTROL: price at a 52-week extreme while VIX >= 20: trade against it"),
    Rule("a_trend", _c_trend, 1, "CONTROL: trade the sign of the 13-week (65-bar) trend at every decision"),
    Rule("a_trend_uncrowded", _c_uncrowded, 1, "CONTROL: the 13-week trend trade except where positioning is at "
                                               "an extreme in the trend's direction"),
)}


def pair_sides(rule: Rule, w: Weekly, hi: float = HI, lo: float = LO, z: bool = False) -> np.ndarray:
    """The rule over the pair's whole bar series: +1 buy, -1 sell at decision bars, 0 elsewhere."""
    out = np.zeros(w.n_bars, np.int8)
    d = rule.direction(w, hi, lo, z) * w.orient
    keep = (w.row >= 0) & (d != 0)
    out[w.row[keep]] = d[keep]
    return out


@dataclass
class RuleSignal:
    """A rule as the battery's signal: masks over a study's rows, and the neighbouring-threshold masks."""

    rule: Rule
    weekly: dict = field(repr=False)
    z: bool = False

    @property
    def key(self) -> str:
        return f"rule:{self.rule.name}" + ("@z" if self.z else "")

    def masks(self, study: Study, hi: float = HI, lo: float = LO) -> dict[str, np.ndarray]:
        out = {}
        for s in study.symbols:
            out[s] = pair_sides(self.rule, self.weekly[s], hi, lo, self.z)[study.rows[s]]
        return out

    def perturbed_masks(self, study: Study) -> list[dict[str, np.ndarray]]:
        return [self.masks(study, hi, lo) for hi, lo in NEIGHBOURS]


class SignedStudy(Study):
    """A study whose signal carries the side: a mask value +1 buys, -1 sells, 0 is no signal.
    One position per instrument across BOTH sides; random entries take a random side."""

    def trades(self, masks, exit_, side: int = BUY, stress: str = "base", context: tuple[str, ...] = ()) -> Trades:
        exit_ = EXIT_BY_KEY[exit_] if isinstance(exit_, str) else exit_
        keys = ("exit_t", "r", "mfe", "mae", "cost", "bars", "reason")
        cols = {k: [] for k in ("symbol", "row", "t") + keys}
        ctx = {c: [] for c in context}
        sides_all = []
        for s in self.symbols:
            m = masks.get(s)
            if m is None:
                continue
            m = np.asarray(m)
            cand = np.flatnonzero(m != 0)
            if not len(cand):
                continue
            ob, os_ = self.outcome(s, exit_, BUY, stress), self.outcome(s, exit_, SELL, stress)
            take, sides, free = [], [], 0
            for p in cand:
                o = ob if m[p] > 0 else os_
                if p < free or not np.isfinite(o["r"][p]):
                    continue
                take.append(int(p))
                sides.append(1 if m[p] > 0 else -1)
                free = int(o["free"][p])
            if not take:
                continue
            pos, sd = np.asarray(take, np.int64), np.asarray(sides, np.int8)
            buy = sd > 0
            cols["symbol"].append(np.full(len(pos), s, dtype=object))
            cols["row"].append(self.rows[s][pos])
            cols["t"].append(self.time[s][pos])
            for k in keys:
                cols[k].append(np.where(buy, ob[k][pos], os_[k][pos]))
            for c in context:
                ctx[c].append(self.bins(s, c)[pos])
            sides_all.append(sd)
        if not cols["symbol"]:
            empty = {k: np.zeros(0, dtype=object if k == "symbol" else float) for k in cols}
            return Trades(**empty, context={**{c: np.zeros(0, np.int8) for c in context}, "side": np.zeros(0, np.int8)})
        joined = {k: np.concatenate(v) for k, v in cols.items()}
        order = np.lexsort((joined["symbol"].astype(str), joined["t"]))
        context_out = {c: np.concatenate(v)[order] for c, v in ctx.items()}
        context_out["side"] = np.concatenate(sides_all)[order]
        return Trades(**{k: v[order] for k, v in joined.items()}, context=context_out)

    def random_masks(self, counts: dict[str, int], rng: np.random.Generator) -> dict[str, np.ndarray]:
        out = {}
        for s in self.symbols:
            m = np.zeros(len(self.rows[s]), np.int8)
            k = min(int(counts.get(s, 0)), len(m))
            if k:
                m[rng.choice(len(m), size=k, replace=False)] = rng.choice(np.array([-1, 1], np.int8), size=k)
            out[s] = m
        return out


# ── point-in-time evidence ────────────────────────────────────────────────────────────────────────

FEATURES = ("spec_pct", "spec_z", "spec_flow_pct", "spec_step", "px_pct", "px_flow_pct", "trend", "vix")


def columns(series: BarSeries, cot: CotSeries, vix=None) -> dict[str, np.ndarray]:
    """Every feature and every rule's side as bar columns (values at decision bars, NaN elsewhere)."""
    w = weekly(series, cot, vix)
    out = {}
    keep = w.row >= 0
    for name in FEATURES:
        col = np.full(w.n_bars, np.nan)
        col[w.row[keep]] = w.f[name][keep]
        out[name] = col
    for name, rule in RULES.items():
        out[f"rule:{name}"] = pair_sides(rule, w).astype(float)
    return out


def truncation_leaks(series: BarSeries, cot: CotSeries, vix, rows) -> dict[str, list[int]]:
    """Per column, the rows where the full-history value differs from the value recomputed with the
    bars, the COT reports and VIX all cut at that row's close. Empty lists mean causal there."""
    full = columns(series, cot, vix)
    bad: dict[str, list[int]] = {k: [] for k in full}
    for i in rows:
        i = int(i)
        t = int(series.available_at[i])
        part = columns(series.take(slice(0, i + 1)), cot.truncated(t), vix.truncated(t) if vix is not None else None)
        for k in full:
            a, b = full[k][i], part[k][i]
            same = (np.isnan(a) and np.isnan(b)) or a == b or abs(a - b) <= 1e-9 * max(1.0, abs(a))
            if not same:
                bad[k].append(i)
    return bad


__all__ = ["COT_STUDY_VERSION", "Extremes", "FEATURES", "HI", "LO", "NEIGHBOURS", "PAIRS", "RULES", "Rule",
           "RuleSignal", "SignedStudy", "Weekly", "columns", "lagged", "pair_sides", "trailing",
           "truncation_leaks", "weekly"]
