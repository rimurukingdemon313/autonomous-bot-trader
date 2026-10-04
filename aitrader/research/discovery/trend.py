"""DIV-1: diversified time-series momentum across asset classes (research only).

The single most replicated trading anomaly in the academic and practitioner record: an asset's own
past 12-month return predicts its next-month return, across equity indices, bonds, commodities
and currencies, in every decade studied (Moskowitz, Ooi & Pedersen 2012, "Time series
momentum"; Hurst, Ooi & Pedersen 2017, "A century of evidence on trend-following investing").
The economic explanation offered is behavioural (under-reaction to news, then over-reaction) and
institutional (hedging demand and slow-moving capital). It is a premium for bearing the risk of
sharp trend reversals, earned through DIVERSIFICATION across many weakly correlated markets.

This repository could not test it properly: it holds 12 FX pairs and gold over 10 years. That
is too few markets and too few years. CP-001 (single-pair FX trend) was rejected with a gross t
of about 1.5. DIV-1 therefore runs on a multi-asset ETF universe, fetched where the network
allows (scripts/div1.py).

Rules, fixed from the literature, no tuning:

- MONTHLY: at each month-end close, for each asset with at least 13 months of history.
- SIGNAL: H1 = sign of the trailing 12-month total return (adjusted close);
          H2 = sign of the average of sign(1m), sign(3m), sign(12m) returns (zero = flat).
- SIZE: each position targets 40% annualised volatility, from an EWMA of daily log returns
  (centre of mass 60 days, as in MOP 2012), divided by the number of assets: the portfolio is
  an equal risk-weighted average.
- RETURN: the next month's simple return of each asset, times its weight.
- COSTS: |change in weight| x cost per unit traded (declared 5 bps for liquid ETFs: half-spread
  plus commission), plus financing of gross exposure above 1 at a declared 3% a year, plus
  borrowing on short exposure at a declared 0.5% a year.

Nothing here sizes a real position, reaches a broker or reads data after its month-end.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

import numpy as np

TREND_VERSION = "trend-1.0.0"
VOL_TARGET = 0.40
COM_DAYS = 60
LOOKBACKS = (1, 3, 12)


@dataclass(frozen=True)
class TrendCosts:
    trade_bps: float = 5.0  # per unit of weight traded
    financing_pa: float = 0.03  # on gross exposure above 1
    borrow_pa: float = 0.005  # on short exposure

    def stressed(self, k: float = 2.0) -> "TrendCosts":
        return TrendCosts(self.trade_bps * k, self.financing_pa * k, self.borrow_pa * k)


def month_ends(dates: list[date]) -> list[int]:
    """Indices of the last trading day of each month in a sorted list of dates."""
    return [i for i in range(len(dates)) if i == len(dates) - 1 or dates[i + 1].month != dates[i].month]


def ewma_vol(closes: np.ndarray, com: int = COM_DAYS) -> np.ndarray:
    """Annualised EWMA volatility of daily log returns, using data up to and including each day."""
    r = np.diff(np.log(closes), prepend=np.nan)
    lam = com / (com + 1.0)
    out = np.full(len(closes), np.nan)
    m = v = None
    n = 0
    for i, x in enumerate(r):
        if not math.isfinite(x):
            continue
        n += 1
        if m is None:
            m, v = x, 0.0
        else:
            m = lam * m + (1 - lam) * x
            v = lam * v + (1 - lam) * (x - m) ** 2
        if n >= 20:
            out[i] = math.sqrt(v * 252)
    return out


def signal(month_closes: np.ndarray, k: int, rule: str) -> float:
    """The signal at month-end k from month-end closes up to k only (nothing later is read)."""
    if k < 12 or not np.all(np.isfinite(month_closes[k - 12:k + 1])):
        return float("nan")
    if rule == "tsmom12":
        return float(np.sign(month_closes[k] / month_closes[k - 12] - 1.0))
    if rule == "blend":
        s = np.mean([np.sign(month_closes[k] / month_closes[k - L] - 1.0) for L in LOOKBACKS])
        return float(np.sign(s))
    raise ValueError(f"unknown rule {rule!r}")


@dataclass
class Panel:
    """Daily adjusted closes on a common calendar (NaN before an asset's history starts)."""
    dates: list[date]
    closes: dict[str, np.ndarray]

    def monthly(self) -> tuple[list[date], dict[str, np.ndarray], dict[str, np.ndarray]]:
        idx = month_ends(self.dates)
        mc = {s: c[idx] for s, c in self.closes.items()}
        vol = {s: ewma_vol(c)[idx] for s, c in self.closes.items()}
        return [self.dates[i] for i in idx], mc, vol


def backtest(panel: Panel, rule: str, costs: TrendCosts = TrendCosts(), start: date | None = None,
             end: date | None = None) -> list[dict]:
    """Monthly portfolio returns: weights set at month-end k, earned over month k+1, judged by the
    date of the month-end at which the return is realised. Only months whose realisation date lies
    in [start, end) are returned; earlier months still build the history the signal needs."""
    mdates, mc, vol = panel.monthly()
    syms = sorted(mc)
    prev_w = {s: 0.0 for s in syms}
    out = []
    for k in range(len(mdates) - 1):
        raw = {}
        for s in syms:
            sg, sv = signal(mc[s], k, rule), vol[s][k]
            nxt = mc[s][k + 1]
            if math.isfinite(sg) and math.isfinite(sv) and sv > 0 and math.isfinite(nxt):
                raw[s] = sg * VOL_TARGET / sv
        n = len(raw)
        w = {s: (raw.get(s, 0.0) / n if n else 0.0) for s in syms}
        realised = mdates[k + 1]
        turnover = sum(abs(w[s] - prev_w[s]) for s in syms)
        prev_w = w
        if (start and realised < start) or (end and realised >= end) or n == 0:
            continue
        gross_ret = sum(w[s] * (mc[s][k + 1] / mc[s][k] - 1.0) for s in raw)
        gross_exp = sum(abs(v) for v in w.values())
        short_exp = sum(-v for v in w.values() if v < 0)
        cost = (turnover * costs.trade_bps / 1e4 + max(0.0, gross_exp - 1.0) * costs.financing_pa / 12
                + short_exp * costs.borrow_pa / 12)
        out.append({"date": realised, "gross": gross_ret, "cost": cost, "net": gross_ret - cost, "assets": n,
                    "gross_exposure": gross_exp,
                    "contrib": {s: w[s] * (mc[s][k + 1] / mc[s][k] - 1.0) for s in raw}})
    return out


def stats(rows: list[dict], key: str = "net") -> dict:
    x = np.array([r[key] for r in rows], float)
    n = len(x)
    if n < 2:
        return {"n": n, "mean": float(x.mean()) if n else None, "t": None}
    sd = float(x.std(ddof=1))
    eq = np.cumsum(x)
    peak = np.maximum.accumulate(np.concatenate(([0.0], eq)))[1:]
    return {"n": n, "mean_monthly": round(float(x.mean()), 6), "sd_monthly": round(sd, 6),
            "t": round(float(x.mean() / (sd / math.sqrt(n))), 3) if sd > 0 else None,
            "sharpe_annual": round(float(x.mean() / sd * math.sqrt(12)), 3) if sd > 0 else None,
            "annual_return": round(float(x.mean() * 12), 4), "max_drawdown": round(float((peak - eq).max()), 4),
            "positive_months": round(float((x > 0).mean()), 3)}
