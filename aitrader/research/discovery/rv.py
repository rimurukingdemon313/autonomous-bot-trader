"""RV-1: cross-sectional, numeraire-free information in eight currencies (research only, no sizing).

The question is not "will EURUSD rise?" but "which currencies will outperform the others?":

- every currency's value is measured in USD (USD itself = 1), and its RELATIVE return is its return
  minus the mean of all eight -- the common dollar move cancels;
- each week the currencies are ranked by a signal, and the signal's information is the Spearman
  rank correlation (IC) between that ranking and the next week's relative returns;
- the tradable form is a currency-neutral book: rank weights over the eight currencies that sum to
  zero with gross exposure 2 (one unit long, one unit short). USD is one of the eight, not a base.

Timing (H.10 audit, docs/H10_DATA_AUDIT.md): a decision is taken on Friday at 17:00 New York with
the H.10 rates usable then (`aitrader.data.h10.available_at`: the next business day, 17:00 New
York) and the policy rates public then. The forward week runs from the first H.10 fixing AFTER the
decision (normally Monday noon) to the first fixing at least seven days later. Nothing is fitted:
lookbacks, levels and the regime rule are fixed in the spec.

Stage 2 executes the same book on the repository's bid/ask bars at the forward window's fixing
times, with measured spreads, slippage, commission and a financing proxy; AUDUSD is synthesised from
AUDJPY / USDJPY (the direct Dukascopy AUDUSD series is defective in 2008-2009). This module never
computes a position size in money: weights are fractions of a notional, the Risk Engine's job is
untouched.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

RV_VERSION = "rv-1.0.0"
NY = ZoneInfo("America/New_York")
CURRENCIES = ("USD", "EUR", "JPY", "GBP", "CHF", "CAD", "AUD", "NZD")
NON_USD = CURRENCIES[1:]
PAIR = {"EUR": "EURUSD", "GBP": "GBPUSD", "AUD": "AUDUSD", "NZD": "NZDUSD", "JPY": "USDJPY", "CHF": "USDCHF",
        "CAD": "USDCAD"}
QUOTED_PER_USD = {"JPY", "CHF", "CAD"}  # the pair is units of the currency per USD
DECISION_HOUR = 17
SKIP_DAYS = 7
MOM_DAYS = (91, 364)  # 3 and 12 months, from the skip point
REV_DAYS = 7
VALUE_DAYS = 1820  # five years
GV_CHANGES = 20  # daily changes in the global-volatility measure
REGIME_WINDOW, REGIME_MIN = 156, 52  # weeks of prior GV values for the median
HOLD_MIN_DAYS, HOLD_MAX_DAYS = 7, 10
MIN_CROSS_SECTION = 6
SIGNALS = ("carry", "momentum", "reversal", "value")


def ny_epoch(d: date, hour: int, minute: int = 0) -> int:
    return int(datetime(d.year, d.month, d.day, hour, minute, tzinfo=NY).timestamp())


def fridays(start: date, end: date) -> list[date]:
    d = start + timedelta(days=(4 - start.weekday()) % 7)
    out = []
    while d < end:
        out.append(d)
        d += timedelta(days=7)
    return out


# ── the panel: log USD value of each currency on common H.10 dates ─────────────────────────────────

@dataclass
class Panel:
    dates: tuple  # H.10 observation dates on which all seven rates exist, ascending
    available: np.ndarray  # epoch seconds from which each date's rates may be used
    logv: dict  # currency -> log value in USD (USD = 0)

    def __post_init__(self) -> None:
        self._ord = np.array([d.toordinal() for d in self.dates], np.int64)

    def last_on_or_before(self, d: date) -> int:
        return int(np.searchsorted(self._ord, d.toordinal(), side="right")) - 1

    def first_after(self, d: date) -> int:
        return int(np.searchsorted(self._ord, d.toordinal(), side="right"))

    def first_on_or_after(self, d: date) -> int:
        return int(np.searchsorted(self._ord, d.toordinal(), side="left"))

    def last_available(self, t: int) -> int:
        return int(np.searchsorted(self.available, t, side="right")) - 1


def panel_from_h10(series: dict) -> Panel:
    """Only dates on which every currency has a rate, from the first date all seven exist (the euro's,
    1999-01-04): H.10's no-rate days are common to all seven (audit), so this drops no information;
    a later date missing for one currency only is refused."""
    by = {c: dict(zip(s.dates, s.value)) for c, s in series.items()}
    start = max(min(v) for v in by.values())  # the euro's first rate, 1999-01-04: before it there is no eight
    alld = sorted(d for d in set().union(*[set(v) for v in by.values()]) if d >= start)
    common = [d for d in alld if all(d in by[c] for c in NON_USD)]
    if len(common) != len(alld):
        partial = [d for d in alld if d not in set(common)][:5]
        raise ValueError(f"H.10 dates missing for only some currencies (e.g. {partial}); refusing to align")
    avail = {d: a for s in series.values() for d, a in zip(s.dates, s.available_at)}
    logv = {"USD": np.zeros(len(common))}
    for c in NON_USD:
        x = np.log(np.array([by[c][d] for d in common], float))
        logv[c] = -x if c in QUOTED_PER_USD else x
    return Panel(tuple(common), np.array([avail[d] for d in common], np.int64), logv)


@dataclass(frozen=True)
class Week:
    friday: date
    d: int  # last date usable at the decision
    e: int  # entry fixing (first date after the Friday)
    x: int  # exit fixing (first date >= entry + 7 days)


def week(panel: Panel, friday: date) -> Week | None:
    d = panel.last_available(ny_epoch(friday, DECISION_HOUR))
    e = panel.first_after(friday)
    if d < 0 or e >= len(panel.dates):
        return None
    x = panel.first_on_or_after(panel.dates[e] + timedelta(days=HOLD_MIN_DAYS))
    if x >= len(panel.dates) or (panel.dates[x] - panel.dates[e]).days > HOLD_MAX_DAYS:
        return None
    return Week(friday, d, e, x)


def _lv(panel: Panel, i: int) -> np.ndarray:
    return np.array([panel.logv[c][i] for c in CURRENCIES])


def _back(panel: Panel, i: int, days: int) -> int:
    """Index of the last date at least `days` before date i; -1 if the panel does not reach back."""
    j = panel.last_on_or_before(panel.dates[i] - timedelta(days=days))
    return j


# ── signals: one score per currency (+ = expected to outperform under the literature's sign) ──────

def momentum_raw(panel: Panel, w: Week) -> dict[int, np.ndarray] | None:
    s = _back(panel, w.d, SKIP_DAYS)
    if s < 0:
        return None
    out = {}
    for L in MOM_DAYS:
        b = _back(panel, s, L)
        if b < 0:
            return None
        out[L] = _lv(panel, s) - _lv(panel, b)
    return out


def scores(panel: Panel, w: Week, rates_now: np.ndarray) -> dict[str, np.ndarray]:
    """Every signal at a decision (NaN where undefined). `rates_now`: policy rates public at the decision,
    in CURRENCIES order, NaN where a currency has none (never filled)."""
    out = {k: np.full(len(CURRENCIES), np.nan) for k in SIGNALS}
    out["carry"] = np.asarray(rates_now, float)
    m = momentum_raw(panel, w)
    if m is not None:
        out["momentum"] = 0.5 * (ranks(m[MOM_DAYS[0]]) + ranks(m[MOM_DAYS[1]]))
    r = _back(panel, w.d, REV_DAYS)
    if r >= 0:
        out["reversal"] = -(_lv(panel, w.d) - _lv(panel, r))
    v = _back(panel, w.d, VALUE_DAYS)
    if v >= 0:
        out["value"] = -(_lv(panel, w.d) - _lv(panel, v))
    return out


def raw_dispersion(panel: Panel, w: Week, rates_now: np.ndarray) -> dict[str, float]:
    """Cross-sectional standard deviation of each signal's raw quantity (for the abstention rule)."""
    out = {k: np.nan for k in SIGNALS}
    c = np.asarray(rates_now, float)
    if np.isfinite(c).sum() >= MIN_CROSS_SECTION:
        out["carry"] = float(np.nanstd(c, ddof=1))
    m = momentum_raw(panel, w)
    if m is not None:
        out["momentum"] = float(np.std(m[MOM_DAYS[0]] + m[MOM_DAYS[1]], ddof=1))
    for k, days in (("reversal", REV_DAYS), ("value", VALUE_DAYS)):
        j = _back(panel, w.d, days)
        if j >= 0:
            out[k] = float(np.std(_lv(panel, w.d) - _lv(panel, j), ddof=1))
    return out


def global_vol(panel: Panel, w: Week) -> float:
    """Mean absolute daily log change of the seven currencies against USD over the last 20 changes
    usable at the decision (the global FX volatility of Menkhoff, Sarno, Schmeling & Schrimpf, 2012)."""
    a = w.d - GV_CHANGES
    if a < 0:
        return float("nan")
    x = np.vstack([panel.logv[c][a:w.d + 1] for c in NON_USD])
    return float(np.mean(np.abs(np.diff(x, axis=1))))


def regimes(gv: list[float]) -> list[str | None]:
    """HIGH when this week's global volatility is above the median of the previous (up to) 156 weekly
    values, LOW otherwise; None with fewer than 52 prior values. Strictly prior values only."""
    out: list[str | None] = []
    hist: list[float] = []
    for g in gv:
        prev = [x for x in hist[-REGIME_WINDOW:] if np.isfinite(x)]
        if not np.isfinite(g) or len(prev) < REGIME_MIN:
            out.append(None)
        else:
            out.append("HIGH" if g > float(np.median(prev)) else "LOW")
        hist.append(g)
    return out


def forward_relative(panel: Panel, w: Week) -> np.ndarray:
    r = _lv(panel, w.x) - _lv(panel, w.e)
    return r - r.mean()


# ── statistics and the book ───────────────────────────────────────────────────────────────────────

def ranks(x: np.ndarray) -> np.ndarray:
    """Average ranks 1..n of the finite values (ties share their mean rank); NaN stays NaN."""
    x = np.asarray(x, float)
    out = np.full(len(x), np.nan)
    ok = np.flatnonzero(np.isfinite(x))
    order = ok[np.argsort(x[ok], kind="stable")]
    vals = x[order]
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[j + 1] == vals[i]:
            j += 1
        out[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return out


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < MIN_CROSS_SECTION:
        return float("nan")
    ra, rb = ranks(a[ok]), ranks(b[ok])
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def rank_weights(score: np.ndarray) -> np.ndarray:
    """Currency-neutral weights: centred ranks scaled so they sum to 0 with gross exposure 2.
    A currency without a score gets 0. Fewer than six scored currencies: no position."""
    s = np.asarray(score, float)
    w = np.zeros(len(s))
    ok = np.isfinite(s)
    if ok.sum() < MIN_CROSS_SECTION:
        return w
    r = ranks(s[ok])
    c = r - r.mean()
    g = np.abs(c).sum()
    if g > 0:
        w[ok] = 2.0 * c / g
    return w


def t_stat(x) -> float:
    x = np.asarray([v for v in x if np.isfinite(v)], float)
    if len(x) < 3 or x.std(ddof=1) == 0:
        return float("nan")
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x))))


def welch_t(a, b) -> float:
    a = np.asarray([v for v in a if np.isfinite(v)], float)
    b = np.asarray([v for v in b if np.isfinite(v)], float)
    if len(a) < 3 or len(b) < 3:
        return float("nan")
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float((a.mean() - b.mean()) / se) if se > 0 else float("nan")


def ols_alpha_t(y, x) -> tuple[float, float]:
    """Intercept and its t of y = a + b x (weekly series aligned, NaN pairs dropped)."""
    y, x = np.asarray(y, float), np.asarray(x, float)
    ok = np.isfinite(y) & np.isfinite(x)
    y, x = y[ok], x[ok]
    n = len(y)
    if n < 10:
        return float("nan"), float("nan")
    X = np.column_stack([np.ones(n), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    s2 = resid @ resid / (n - 2)
    cov = s2 * np.linalg.inv(X.T @ X)
    return float(beta[0]), float(beta[0] / np.sqrt(cov[0, 0])) if cov[0, 0] > 0 else float("nan")


# ── Stage 2: the book executed on bid/ask with costs and financing ───────────────────────────────

@dataclass(frozen=True)
class Costs:
    slippage_pips: float = 0.1  # per fill
    commission_pips_rt: float = 0.7  # per round trip
    spread_multiple: float = 1.0
    financing_markup: float = 0.005  # per year on gross non-USD exposure (as R3)

    def stressed(self, k: float = 2.0) -> "Costs":
        return Costs(self.slippage_pips * k, self.commission_pips_rt * k, self.spread_multiple * k, self.financing_markup)


@dataclass
class Quote:
    mid: float  # pair price, mid
    half_spread_rel: float  # half the bid/ask spread / mid
    pip_rel: float  # one pip / mid


@dataclass
class Book:
    """Holds currency exposures (fractions of notional, long the currency against USD) between
    rebalances. P&L is marked at the execution fixings; costs are charged on every change."""

    costs: Costs = field(default_factory=Costs)
    pos: dict = field(default_factory=lambda: {c: 0.0 for c in NON_USD})
    last: dict | None = None  # currency -> USD value at the last execution
    last_t: date | None = None
    last_rates: np.ndarray | None = None

    def value(self, ccy: str, q: Quote) -> float:
        return 1.0 / q.mid if ccy in QUOTED_PER_USD else q.mid

    def step(self, when: date, quotes: dict, target: np.ndarray, rates: np.ndarray) -> dict:
        """Mark to market since the last execution, then rebalance to `target` (weights over CURRENCIES;
        the USD weight is implied). Returns this interval's gross, financing, cost and per-currency P&L."""
        vals = {c: self.value(c, quotes[c]) for c in NON_USD}
        gross, fin, contrib = 0.0, 0.0, {c: 0.0 for c in CURRENCIES}
        if self.last is not None:
            days = (when - self.last_t).days
            r = {"USD": 0.0} | {c: vals[c] / self.last[c] - 1.0 for c in NON_USD}
            rbar = sum(r.values()) / len(CURRENCIES)
            w = {"USD": -sum(self.pos.values())} | self.pos
            for c in CURRENCIES:  # relative attribution: sums to the book's P&L because the weights sum to 0
                contrib[c] = w[c] * (r[c] - rbar)
            gross = sum(self.pos[c] * r[c] for c in NON_USD)
            iu = self.last_rates[0]
            for k, c in enumerate(NON_USD, start=1):
                if self.pos[c] != 0.0:
                    fin += self.pos[c] * (self.last_rates[k] - iu) / 100.0 * days / 360.0
            fin -= self.costs.financing_markup * sum(abs(p) for p in self.pos.values()) * days / 365.0
        cost = 0.0
        new = {c: float(target[k]) for k, c in enumerate(CURRENCIES) if c != "USD"}
        for c in NON_USD:
            d = abs(new[c] - self.pos[c])
            if d:
                q = quotes[c]
                per = (self.costs.spread_multiple * q.half_spread_rel
                       + (self.costs.slippage_pips + self.costs.commission_pips_rt / 2.0) * q.pip_rel)
                cost += d * per
        self.pos, self.last, self.last_t, self.last_rates = new, vals, when, np.asarray(rates, float)
        return {"gross": gross, "financing": fin, "cost": cost, "net": gross + fin - cost, "contrib": contrib}


__all__ = ["Book", "CURRENCIES", "Costs", "NON_USD", "PAIR", "Panel", "QUOTED_PER_USD", "Quote", "RV_VERSION",
           "SIGNALS", "Week", "forward_relative", "fridays", "global_vol", "ny_epoch", "ols_alpha_t",
           "panel_from_h10", "rank_weights", "ranks", "raw_dispersion", "regimes", "scores", "spearman", "t_stat",
           "week", "welch_t"]
