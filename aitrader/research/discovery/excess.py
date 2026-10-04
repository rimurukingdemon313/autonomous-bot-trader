"""DIV-2: futures-style daily EXCESS returns from long public histories (research only).

DIV-1 failed for two diagnosed reasons:
- 86% of its costs were financing the leverage that a volatility target implies when funded as
  ETFs at a declared 3%;
- 13 years cannot prove a Sharpe-0.5 effect.

Trend-following literature measures FUTURES excess returns, where funding is part of the
instrument, over long histories. This module builds the closest honest equivalents from data
reachable here. Every approximation is declared and none is tuned:

    equity index   r = P_t/P_{t-1} - 1 - (rf - 2%)/252        price index + declared 2% dividend yield
                                                              - USD policy rate as funding
    bond (US)      r = (y_{t-1} - rf)/252 - D (y_t - y_{t-1})  carry minus duration x yield change;
                                                              D = 8 (10y), 4.5 (5y)
    currency       r = S_t/S_{t-1} - 1 + (i_f - i_usd) days/365   spot (USD per unit) + the policy-rate
                                                              differential in force the previous day;
                                                              months without a foreign rate are
                                                              EXCLUDED (never substituted)
    commodity      r = P_t/P_{t-1} - 1                         spot as a proxy for front futures
                                                              (roll yield ignored: declared)

Rates are those public at the previous close: nothing later is read. The synthetic index of an
asset is the cumulative product of (1 + r) over its own observation days.
"""

from __future__ import annotations

import math
from datetime import date

import numpy as np

EXCESS_VERSION = "excess-1.0.0"
DIV_YIELD = 0.02
DURATION = {"US10Y": 8.0, "US5Y": 4.5}


def _index(rets: list[float]) -> np.ndarray:
    out, v = [], 100.0
    for r in rets:
        if r is None or not math.isfinite(r):
            out.append(float("nan"))
            continue
        v *= 1.0 + r
        out.append(v)
    return np.array(out, float)


def equity_index(days: list[date], price: list[float], rf_pct: list[float]) -> np.ndarray:
    """rf_pct[i] = USD funding rate (percent) in force at the close of days[i-1]."""
    rets = [float("nan")]
    for i in range(1, len(days)):
        if not (math.isfinite(price[i]) and math.isfinite(price[i - 1]) and math.isfinite(rf_pct[i])):
            rets.append(float("nan"))
            continue
        rets.append(price[i] / price[i - 1] - 1.0 - (rf_pct[i] / 100.0 - DIV_YIELD) / 252.0)
    return _index([0.0] + rets[1:]) if len(days) else np.array([])


def bond_index(days: list[date], yld_pct: list[float], rf_pct: list[float], duration: float) -> np.ndarray:
    rets = [0.0]
    for i in range(1, len(days)):
        y0, y1, rf = yld_pct[i - 1], yld_pct[i], rf_pct[i]
        if not (math.isfinite(y0) and math.isfinite(y1) and math.isfinite(rf)):
            rets.append(float("nan"))
            continue
        rets.append((y0 - rf) / 100.0 / 252.0 - duration * (y1 - y0) / 100.0)
    return _index(rets)


def fx_index(days: list[date], usd_per_unit: list[float], i_foreign: list[float], i_usd: list[float]) -> np.ndarray:
    """A long position in the foreign currency, funded in USD. A day whose differential is unknown
    (no foreign or USD rate in force) is NaN: the asset is not held then."""
    rets = [0.0]
    for i in range(1, len(days)):
        s0, s1, f, u = usd_per_unit[i - 1], usd_per_unit[i], i_foreign[i], i_usd[i]
        if not all(math.isfinite(x) for x in (s0, s1, f, u)):
            rets.append(float("nan"))
            continue
        gap = (days[i] - days[i - 1]).days
        rets.append(s1 / s0 - 1.0 + (f - u) / 100.0 * gap / 365.0)
    return _index(rets)


def spot_index(days: list[date], price: list[float]) -> np.ndarray:
    rets = [0.0] + [(price[i] / price[i - 1] - 1.0) if math.isfinite(price[i]) and math.isfinite(price[i - 1])
                    else float("nan") for i in range(1, len(days))]
    return _index(rets)
