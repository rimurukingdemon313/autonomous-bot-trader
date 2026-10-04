"""TOM-D: diagnostics of the turn-of-the-month candidate (research only). tomdiag-1.0.0

Descriptive analysis of RC-EQ's E1 TOM (research/preregistrations/TOM-D.md). Nothing here judges
or tunes: the rule is `rc.tom` exactly as frozen. Every simulation goes through
`retail.simulate`. These helpers only cut its output into the views the diagnosis needs:

- trades, with their cost components;
- relative trading days around the month end;
- the decomposition of cost and financing;
- concentration;
- break-even costs;
- bootstrap intervals;
- and one alternative weighting (inverse volatility), which is a DIAGNOSTIC VARIANT, not a rule.
"""

from __future__ import annotations

import math
import warnings
from datetime import date

import numpy as np

from . import retail

TOMDIAG_VERSION = "tomdiag-1.0.0"


def _valid(c: np.ndarray) -> list[int]:
    return [j for j in range(len(c)) if np.isfinite(c[j]) and c[j] > 0]


def relative_days(dates, c: np.ndarray, before: int = 5, after: int = 6) -> dict[int, int]:
    """For an instrument's own trading days: date index -> relative day of the turn of the month.
    -1 is the last trading day of a month, +1 the first of the next, and so on. The return ON a day
    is the close-to-close move ending at that day's close. Days farther than `before`/`after` from
    a month end are absent. Uses the calendar only."""
    idx = _valid(c)
    months: dict = {}
    for j in idx:
        months.setdefault((dates[j].year, dates[j].month), []).append(j)
    out: dict[int, int] = {}
    for key, js in months.items():
        for k in range(1, min(before, len(js)) + 1):
            out[js[-k]] = -k
        for k in range(1, min(after, len(js)) + 1):
            out.setdefault(js[k - 1], k)
    return out


def day_returns(dates, closes: dict, start: date, end: date, before: int = 5, after: int = 6) -> dict:
    """Mean close-to-close return of each relative day, against all other days (the drift).
    Per instrument and pooled: {"by_day": {rel: (mean, n)}, "other": (mean, n), "tom": (...)}."""
    pooled: dict = {}
    other: list = []
    tom: list = []
    for name, c in closes.items():
        idx = _valid(c)
        rel = relative_days(dates, c, before, after)
        for a, b in zip(idx, idx[1:]):
            if not (start <= dates[b] < end):
                continue
            r = c[b] / c[a] - 1.0
            d = rel.get(b)
            if d is not None:
                pooled.setdefault(d, []).append(r)
            if d in (-1, 1, 2, 3):
                tom.append(r)
            else:
                other.append(r)

    def ms(x):
        x = np.asarray(x, float)
        return {"mean_bps": round(float(np.mean(x)) * 1e4, 3) if len(x) else None, "n": int(len(x)),
                "t": round(float(np.mean(x) / np.std(x, ddof=1) * math.sqrt(len(x))), 3) if len(x) > 2 else None}

    t_o, t_t = np.asarray(other, float), np.asarray(tom, float)
    diff = None
    if len(t_o) > 2 and len(t_t) > 2:
        se = math.sqrt(np.var(t_t, ddof=1) / len(t_t) + np.var(t_o, ddof=1) / len(t_o))
        diff = {"tom_minus_other_bps": round((float(np.mean(t_t)) - float(np.mean(t_o))) * 1e4, 3),
                "welch_t": round((float(np.mean(t_t)) - float(np.mean(t_o))) / se, 3)}
    return {"by_day": {d: ms(v) for d, v in sorted(pooled.items())}, "tom_days": ms(tom), "other_days": ms(other),
            "difference": diff}


def trade_ledger(res: retail.Result, closes: dict, instruments: dict, costs: retail.Costs,
                 bench: retail.Result) -> list[dict]:
    """One row per trade with its entry/exit close and its cost components, each as a fraction of
    equity. `bench` is the same targets simulated with Costs.frictionless(): its financing is the
    benchmark alone, so markup = financing - benchmark financing."""
    out = []
    pos = {d: i for i, d in enumerate(res.dates)}
    for t in res.trades:
        n = t["instrument"]
        inst = instruments[n]
        i0, i1 = pos[t["entry"]], pos[t["exit"]]
        sl = slice(i0, i1 + 1)
        traded = float(np.sum(res.traded[n][sl]))
        spread = traded * inst.spread_bps * costs.spread_mult / 2.0 / 1e4
        slip = traded * costs.slippage_bps / 1e4
        fin = float(np.sum(res.financing[n][sl]))
        b = float(np.sum(bench.financing[n][sl]))
        gross = float(np.sum(res.gross[n][sl]))
        div = float(np.sum(res.dividends[n][sl]))
        idx = [j for j in range(i0, i1 + 1) if np.isfinite(closes[n][j])]
        out.append({"instrument": n, "entry": str(t["entry"]), "entry_close": round(float(closes[n][i0]), 4),
                    "exit": str(t["exit"]), "exit_close": round(float(closes[n][i1]), 4),
                    "trading_days": len(idx) - 1, "calendar_days": t["days"], "weight": round(float(res.position[n][i0]), 6),
                    "gross": gross, "spread": -spread, "slippage": -slip, "commission": 0.0, "benchmark": b,
                    "markup": fin - b, "dividends": div, "net": gross - spread - slip + fin + div,
                    "price_return": float(closes[n][i1] / closes[n][i0] - 1.0), "open": bool(t.get("open"))})
    return out


def components(ledger: list[dict], years: float) -> dict:
    """Annual totals (fraction of equity a year) of every component, from the trade ledger."""
    keys = ("gross", "spread", "slippage", "commission", "benchmark", "markup", "dividends", "net")
    return {k: round(sum(r[k] for r in ledger) / years, 6) for k in keys}


def concentration(values: dict, total: float | None = None) -> dict:
    """Share of the total net that the best 1, 3 and 5 contributors supply (a share > 1 means the
    rest lose money), and how many contributors are positive."""
    v = sorted(values.values(), reverse=True)
    tot = sum(v) if total is None else total
    out = {"total": round(tot, 6), "positive": sum(x > 0 for x in v), "count": len(v)}
    for k in (1, 3, 5):
        out[f"best_{k}_share"] = round(sum(v[:k]) / tot, 3) if tot > 0 else None
    return out


def top_trades_share(ledger: list[dict], frac: float = 0.10) -> float | None:
    nets = sorted((r["net"] for r in ledger), reverse=True)
    tot = sum(nets)
    k = max(1, int(round(len(nets) * frac)))
    return round(sum(nets[:k]) / tot, 3) if tot > 0 else None


def cagr(dates, daily: np.ndarray, start: date, end: date) -> float | None:
    sel = [k for k, d in enumerate(dates) if start <= d < end]
    if not sel:
        return None
    months = len(retail.monthly(dates, daily, start, end))
    eq = float(np.prod(1.0 + daily[sel]))
    return round(eq ** (12.0 / months) - 1.0, 5) if months else None


def breakeven(net_annual: float, part_annual: float, assumed: float) -> float | None:
    """The value of one cost assumption at which the annual net reaches zero, the cost being linear
    in it: part_annual is that cost line (negative = paid) at the assumed value."""
    if part_annual >= 0:
        return None
    per_unit = -part_annual / assumed
    return round(assumed + net_annual / per_unit, 3)


def bootstrap_mean_ci(months: list[float], block: int = 12, draws: int = 4000, seed: int = 20261005) -> dict:
    """Moving-block bootstrap of the mean monthly net: 95% interval, annualised, and P(mean <= 0)."""
    x = np.asarray(months, float)
    n = len(x)
    if n < block * 2:
        return {}
    rng = np.random.default_rng(seed)
    starts = np.arange(n - block + 1)
    means = np.empty(draws)
    for d in range(draws):
        s = rng.choice(starts, size=int(math.ceil(n / block)))
        means[d] = np.mean(np.concatenate([x[i:i + block] for i in s])[:n])
    return {"annual_lo": round(float(np.quantile(means, 0.025)) * 12, 4),
            "annual_hi": round(float(np.quantile(means, 0.975)) * 12, 4),
            "p_mean_le_zero": round(float(np.mean(means <= 0)), 4)}


def inverse_vol(targets: dict, closes: dict, window: int = 60, min_obs: int = 50) -> dict:
    """Diagnostic variant: the same windows and the same total notional, reallocated in proportion to
    1/volatility. At each window's entry close, an instrument's weight is (1/N) x (1/sd_i) / mean_j(1/sd_j),
    with sd from the `window` daily log returns up to that close and the mean over the instruments
    whose sd is known on that date. The weight is held for the window. Uses only past closes."""
    names = list(targets)
    n_d = len(next(iter(closes.values())))
    inv = {}
    for n in names:
        c = closes[n]
        idx = _valid(c)
        a = np.full(n_d, np.nan)
        lc = np.log(np.array([c[j] for j in idx]))
        r = np.diff(lc)
        for k in range(window, len(idx)):
            w = r[k - window:k]
            if np.sum(np.isfinite(w)) >= min_obs:
                sd = float(np.nanstd(w, ddof=1))
                if sd > 0:
                    a[idx[k]] = 1.0 / sd
        last = np.nan  # carry the latest known value across this instrument's non-trading dates
        for t in range(n_d):
            if np.isfinite(a[t]):
                last = a[t]
            a[t] = last
        inv[n] = a
    with warnings.catch_warnings():  # a date before any instrument has a volatility: NaN, held at zero weight
        warnings.simplefilter("ignore", RuntimeWarning)
        mean_inv = np.nanmean(np.vstack([inv[n] for n in names]), axis=0)
    out = {}
    for n in names:
        tg = targets[n]
        o = np.zeros(n_d)
        cur, prev = 0.0, 0.0
        for t in _valid(closes[n]):  # the instrument's own closes: a holiday never resets a window
            want = tg[t] if np.isfinite(tg[t]) else 0.0
            if want > 0 and prev == 0:
                cur = want * inv[n][t] / mean_inv[t] if np.isfinite(inv[n][t]) and np.isfinite(mean_inv[t]) else 0.0
            elif want == 0:
                cur = 0.0
            o[t] = cur
            prev = want
        out[n] = o
    return out


def adverse_excursion(ledger: list[dict], closes: dict, dates) -> dict:
    """Close-to-close worst move against each trade inside its window (no intraday data): the share
    of trades a protective stop at 3%, 5% or 10% below entry would have closed on a close."""
    pos = {str(d): i for i, d in enumerate(dates)}
    worst = []
    for r in ledger:
        c = closes[r["instrument"]]
        i0, i1 = pos[r["entry"]], pos[r["exit"]]
        seg = [c[j] for j in range(i0, i1 + 1) if np.isfinite(c[j])]
        worst.append(min(seg) / seg[0] - 1.0 if seg else 0.0)
    w = np.asarray(worst)
    return {f"share_below_{p}pct": round(float(np.mean(w <= -p / 100)), 4) for p in (3, 5, 10)} | {
        "median_worst": round(float(np.median(w)), 5) if len(w) else None}


__all__ = ["TOMDIAG_VERSION", "adverse_excursion", "bootstrap_mean_ci", "breakeven", "cagr", "components",
           "concentration", "day_returns", "inverse_vol", "relative_days", "top_trades_share", "trade_ledger"]
