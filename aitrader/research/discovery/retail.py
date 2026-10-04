"""Retail CFD economics for daily-bar portfolio research (research only).

The question every RC study answers is not "does the signal predict" but "does a retail CFD account
make money trading it". So every position pays what such an account pays:

    trading     |change in position| x (spread/2 + slippage [+ commission/2 for FX]) at every fill
    financing   index CFD:  long pays (benchmark + markup), short receives (benchmark - markup),
                            per calendar day held, day count 360 (the broker convention for USD/EUR;
                            conservative for 365-day currencies)
                FX CFD:     the position earns (foreign rate - USD rate) and pays the markup on its
                            notional, per calendar day held, day count 365
    dividends   a long position in a PRICE-return index is credited nothing (conservative: real CFDs
                credit a dividend adjustment); a short pays a declared dividend yield. A total-return
                series (DAX, S&P 500 TR) already contains its dividends, so neither applies

Benchmarks are central-bank policy rates (BIS), public at the close at which the position is held.
A position is never held where its rate is unknown: the target is forced to zero (excluded, never
filled with a guess).

Positions are fractions of account equity (1.0 = notional equal to equity). Each instrument trades
on its OWN valid closes: the position set at close j earns the move from close j to its next valid
close. The caller builds targets from information available at the close it fills at
(`rcsignals.py`), and `delay` shifts them by whole closes for the execution-delay check.

Nothing here sizes a live trade: research positions are notional fractions for measurement, and the
risk engine remains the only sizing authority (CLAUDE.md rule 2).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from datetime import date
from typing import Callable

import numpy as np

RETAIL_VERSION = "retail-1.0.0"


@dataclass(frozen=True)
class Instrument:
    name: str
    kind: str  # "index" | "fx"
    ccy: str  # financing currency (index) or the foreign currency vs USD (fx)
    spread_bps: float = 0.0  # index: full bid/ask spread, basis points of price
    total_return: bool = False  # index: the series already includes dividends
    spread_pips: float = 0.0  # fx: full spread in pips of the market quote
    pip: float = 0.0001  # fx: pip size in the market quote
    usd_per_unit_quote: bool = True  # fx: market quote is USD per unit (EURUSD) or units per USD (USDJPY)

    def __post_init__(self) -> None:
        if self.kind not in ("index", "fx"):
            raise ValueError(f"{self.name}: unknown kind {self.kind!r}")


@dataclass(frozen=True)
class Costs:
    slippage_bps: float = 1.0  # index, per fill
    index_markup_pa: float = 2.5  # percent a year, charged on every index position's notional
    short_dividend_pa: float = 3.0  # percent a year, paid by a short in a price-return index
    fx_commission_pips_rt: float = 0.7  # the risk engine's value (risk/engine.py)
    fx_slippage_pips: float = 0.1  # per fill, the risk engine's value
    fx_markup_pa: float = 1.5  # percent a year, charged on every FX position's notional
    spread_mult: float = 1.0
    index_days: int = 360
    fx_days: int = 365

    def stressed(self, k: float = 2.0) -> "Costs":
        """Every cost assumption multiplied by k: spreads, slippage, commission and both markups."""
        return replace(self, slippage_bps=self.slippage_bps * k, index_markup_pa=self.index_markup_pa * k,
                       fx_commission_pips_rt=self.fx_commission_pips_rt * k, fx_slippage_pips=self.fx_slippage_pips * k,
                       fx_markup_pa=self.fx_markup_pa * k, spread_mult=self.spread_mult * k)

    def frictionless(self) -> "Costs":
        """No trading cost and no markup: what the signal earns before the broker (gross + carry)."""
        return replace(self, slippage_bps=0.0, index_markup_pa=0.0, fx_commission_pips_rt=0.0, fx_slippage_pips=0.0,
                       fx_markup_pa=0.0, spread_mult=0.0, short_dividend_pa=0.0)


RateFn = Callable[[str, date], float]  # percent, public at the close of that date; NaN when unknown


@dataclass
class Result:
    dates: list
    gross: dict  # instrument -> per-date price P&L (fraction of equity)
    cost: dict  # trading costs (positive = paid)
    financing: dict  # benchmark + markup + carry (signed: + received)
    dividends: dict  # signed
    position: dict  # position held after each date's close (carried on non-trading dates)
    traded: dict  # |change in position| at each date's fill
    trades: list = field(default_factory=list)  # dicts: instrument, side, entry, exit, days, ret_per_unit

    def series(self, part: str, names=None) -> np.ndarray:
        src = getattr(self, part)
        names = list(src) if names is None else names
        return np.sum([src[n] for n in names], axis=0) if names else np.zeros(len(self.dates))

    def net(self, names=None) -> np.ndarray:
        return (self.series("gross", names) - self.series("cost", names) + self.series("financing", names)
                + self.series("dividends", names))


def _unit_cost(inst: Instrument, price: float, c: Costs) -> float:
    if inst.kind == "index":
        return (inst.spread_bps * c.spread_mult / 2.0 + c.slippage_bps) / 1e4
    market = price if inst.usd_per_unit_quote else 1.0 / price
    pips = inst.spread_pips * c.spread_mult / 2.0 + c.fx_commission_pips_rt / 2.0 + c.fx_slippage_pips
    return pips * inst.pip / market


def simulate(dates: list[date], closes: dict[str, np.ndarray], targets: dict[str, np.ndarray],
             instruments: dict[str, Instrument], rate: RateFn, costs: Costs, usd: str = "USD") -> Result:
    """Run target positions through retail CFD economics.

    closes[n][t]   the instrument's close on dates[t], NaN when it has none (FX: USD per unit of the
                   foreign currency, whatever the market quote)
    targets[n][t]  the position to hold after the close of dates[t]; read only on the instrument's
                   valid closes. Forced to 0 where the instrument's financing rate is unknown.
    """
    n_d = len(dates)
    zeros = {n: np.zeros(n_d) for n in targets}
    res = Result(list(dates), {n: np.zeros(n_d) for n in targets}, {n: np.zeros(n_d) for n in targets},
                 {n: np.zeros(n_d) for n in targets}, {n: np.zeros(n_d) for n in targets},
                 {n: np.zeros(n_d) for n in targets}, zeros)
    for name, tgt in targets.items():
        inst = instruments[name]
        c = closes[name]
        idx = [j for j in range(n_d) if np.isfinite(c[j]) and c[j] > 0]
        pos = 0.0
        trade = None  # the open trade: [side, entry_j, pnl, peak_abs_pos]
        for k, j in enumerate(idx):
            if k:
                i = idx[k - 1]
                days = (dates[j] - dates[i]).days
                if pos != 0.0:
                    g = pos * (c[j] / c[i] - 1.0)
                    if inst.kind == "index":
                        r = rate(inst.ccy, dates[i])
                        f = (-pos * r - abs(pos) * costs.index_markup_pa) / 100.0 * days / costs.index_days
                        dv = 0.0 if (inst.total_return or pos > 0) else -abs(pos) * costs.short_dividend_pa / 100.0 * days / 365.0
                    else:
                        rf, ru = rate(inst.ccy, dates[i]), rate(usd, dates[i])
                        f = (pos * (rf - ru) - abs(pos) * costs.fx_markup_pa) / 100.0 * days / costs.fx_days
                        dv = 0.0
                    res.gross[name][j] += g
                    res.financing[name][j] += f
                    res.dividends[name][j] += dv
                    if trade is not None:
                        trade[2] += g + f + dv
            want = float(tgt[j]) if np.isfinite(tgt[j]) else 0.0
            if want != 0.0:
                if inst.kind == "index":
                    known = math.isfinite(rate(inst.ccy, dates[j]))
                else:
                    known = math.isfinite(rate(inst.ccy, dates[j])) and math.isfinite(rate(usd, dates[j]))
                if not known:
                    want = 0.0
            if want != pos:
                u = _unit_cost(inst, c[j], costs)
                res.cost[name][j] += abs(want - pos) * u
                res.traded[name][j] += abs(want - pos)
                flip = pos != 0.0 and (want == 0.0 or np.sign(want) != np.sign(pos))
                if flip and trade is not None:
                    trade[2] -= abs(pos) * u
                    res.trades.append(_close(name, trade, dates, j))
                    trade = None
                if want != 0.0:
                    if trade is None:
                        trade = [1 if want > 0 else -1, j, -abs(want) * u, abs(want)]
                    else:  # a resize within the same side: its cost belongs to the open trade
                        trade[2] -= abs(want - pos) * u
                        trade[3] = max(trade[3], abs(want))
            pos = want
            res.position[name][j] = pos
        # carry the held position across dates on which this instrument had no close
        p = res.position[name]
        last = 0.0
        valid = set(idx)
        for t in range(n_d):
            if t in valid:
                last = p[t]
            else:
                p[t] = last
        if trade is not None:  # still open at the end of the data: reported, marked open
            res.trades.append({**_close(name, trade, dates, idx[-1]), "open": True})
    return res


def _close(name, trade, dates, j) -> dict:
    side, entry, pnl, peak = trade
    return {"instrument": name, "side": side, "entry": dates[entry], "exit": dates[j],
            "days": (dates[j] - dates[entry]).days, "ret_per_unit": pnl / peak if peak else 0.0}


def delay(targets: dict[str, np.ndarray], closes: dict[str, np.ndarray], n: int = 1) -> dict[str, np.ndarray]:
    """Execute every target n of the instrument's own valid closes later (the execution-delay check)."""
    out = {}
    for name, tgt in targets.items():
        c = closes[name]
        idx = [j for j in range(len(c)) if np.isfinite(c[j]) and c[j] > 0]
        shifted = np.zeros(len(c))
        for k, j in enumerate(idx):
            shifted[j] = tgt[idx[k - n]] if k >= n else 0.0
        out[name] = shifted
    return out


# ── statistics ──────────────────────────────────────────────────────────

def monthly(dates: list[date], daily: np.ndarray, start: date, end: date) -> list[tuple[tuple[int, int], float]]:
    """Calendar-month sums of daily net in [start, end). Months with no date in range are absent."""
    out: dict = {}
    for d, x in zip(dates, daily):
        if start <= d < end:
            out[(d.year, d.month)] = out.get((d.year, d.month), 0.0) + float(x)
    return sorted(out.items())


def _dd_sum(x) -> float:
    eq = np.cumsum(x)
    return float(np.max(np.maximum.accumulate(np.r_[0.0, eq])[1:] - eq)) if len(eq) else 0.0


def _dd_comp(x) -> float:
    eq = np.cumprod(1.0 + np.asarray(x))
    peak = np.maximum.accumulate(np.r_[1.0, eq])[1:]
    return float(np.max(1.0 - eq / peak)) if len(eq) else 0.0


def month_stats(m: list[float]) -> dict:
    x = np.asarray(m, float)
    n = len(x)
    if n < 2:
        return {"n": n}
    mu, sd = float(np.mean(x)), float(np.std(x, ddof=1))
    down = float(np.sqrt(np.mean(np.minimum(x, 0.0) ** 2)))
    pos, neg = float(np.sum(x[x > 0])), float(-np.sum(x[x < 0]))
    return {"n": n, "mean_monthly": round(mu, 6), "sd_monthly": round(sd, 6),
            "t": round(mu / sd * math.sqrt(n), 3) if sd > 0 else None,
            "annual_return": round(mu * 12, 4), "annual_vol": round(sd * math.sqrt(12), 4),
            "sharpe": round(mu / sd * math.sqrt(12), 3) if sd > 0 else None,
            "sortino": round(mu * 12 / (down * math.sqrt(12)), 3) if down > 0 else None,
            "max_drawdown": round(_dd_sum(x), 4), "positive_months": round(float(np.mean(x > 0)), 3),
            "profit_factor_months": round(pos / neg, 3) if neg > 0 else None}


def summarize(res: Result, start: date, end: date, names=None) -> dict:
    """The full metric set for [start, end): returns, risk, costs, financing, turnover and trades."""
    names = list(res.gross) if names is None else names
    sel = [k for k, d in enumerate(res.dates) if start <= d < end]
    if not sel:
        return {"months": 0}
    net = res.net(names)
    months = [v for _, v in monthly(res.dates, net, start, end)]
    years = len(months) / 12.0 if months else float("nan")
    s = month_stats(months)

    def part(p):
        return round(float(np.sum(res.series(p, names)[sel])) / years, 5) if years else None

    expo = np.sum([np.abs(res.position[n]) for n in names], axis=0)[sel] if names else np.zeros(len(sel))
    turnover = float(np.sum(res.series("traded", names)[sel])) / years if years else None
    trades = [t for t in res.trades if t["instrument"] in names and start <= t["exit"] < end]
    rets = np.array([t["ret_per_unit"] for t in trades]) if trades else np.array([])
    wins, losses = float(np.sum(rets[rets > 0])), float(-np.sum(rets[rets < 0]))
    roll = []
    for k in range(36, len(months) + 1):
        w = np.asarray(months[k - 36:k])
        if np.std(w, ddof=1) > 0:
            roll.append(float(np.mean(w) / np.std(w, ddof=1) * math.sqrt(12)))
    comp = _dd_comp(net[sel])
    s.update({
        "gross_annual": part("gross"), "trading_cost_annual": part("cost"), "financing_annual": part("financing"),
        "dividends_annual": part("dividends"), "net_annual": round(float(np.sum(net[sel])) / years, 5) if years else None,
        "turnover_annual": round(turnover, 3) if turnover is not None else None,
        "return_per_unit_turnover": round(float(np.sum(net[sel])) / years / turnover, 5) if turnover else None,
        "avg_gross_exposure": round(float(np.mean(expo)), 4), "time_in_market": round(float(np.mean(expo > 0)), 4),
        "max_drawdown_compounded": round(comp, 4),
        "trades": len(trades), "trades_per_year": round(len(trades) / years, 2) if years else None,
        "win_rate": round(float(np.mean(rets > 0)), 4) if len(rets) else None,
        "profit_factor": round(wins / losses, 3) if losses > 0 else None,
        "expectancy_bps_per_unit": round(float(np.mean(rets)) * 1e4, 2) if len(rets) else None,
        "median_holding_days": float(np.median([t["days"] for t in trades])) if trades else None,
        "rolling36_sharpe_min": round(min(roll), 3) if roll else None,
        "rolling36_sharpe_max": round(max(roll), 3) if roll else None,
    })
    return s


def by_year(res: Result, start: date, end: date, names=None) -> dict:
    out: dict = {}
    for d, x in zip(res.dates, res.net(names)):
        if start <= d < end:
            out[d.year] = out.get(d.year, 0.0) + float(x)
    return {y: round(v, 5) for y, v in sorted(out.items())}


def leverage_table(res: Result, start: date, end: date, levels=(1.0, 2.0, 3.0)) -> dict:
    """CFD exposure scales every line (price, costs, financing) together: the annual net and the
    compounded drawdown at each exposure. Sharpe is unchanged by construction."""
    sel = [k for k, d in enumerate(res.dates) if start <= d < end]
    net = res.net()[sel]
    years = len(monthly(res.dates, res.net(), start, end)) / 12.0
    return {f"{L:g}x": {"net_annual": round(float(np.sum(net)) * L / years, 4) if years else None,
                        "max_drawdown_compounded": round(_dd_comp(net * L), 4)} for L in levels}


__all__ = ["Costs", "Instrument", "RETAIL_VERSION", "Result", "by_year", "delay", "leverage_table", "month_stats",
           "monthly", "simulate", "summarize"]
