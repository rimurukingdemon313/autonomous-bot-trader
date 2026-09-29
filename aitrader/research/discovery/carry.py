"""Round 3: genuine interest-rate information and a RATE-DIFFERENTIAL CARRY PROXY.

States (categorical, FIXED levels, signed to the pair so that 2 always favours BUYING it). The
differential is rate(base) - rate(quote), both of ONE rate type, as public at the bar close
(aitrader/data/rates.py); a pair missing either side is NaN, never filled.

    rate_level   differential >= +1.00pp: 2 (buying earns >= 1%/yr) | <= -1.00pp: 0 | else 1   (hypotheses A, B)
    rate_change  differential now minus 91 days ago: >= +0.25pp widening in the base's favour: 2 |
                 <= -0.25pp narrowing: 0 | else 1   (0.25pp = one standard policy step)            (C, D)
    rate_accel   (change over the last 91 days) - (change over the 91 days before): >= +0.25pp: 2 |
                 <= -0.25pp: 0 | else 1                                                          (E)
    policy_move  a policy move in the last 30 days: base rate change minus quote rate change >= +0.10pp
                 (base hiked or quote cut): 2 | <= -0.10pp: 0 | none: 1                          (F, event filter)

Carry accounting (`CarryStudy`): every simulated trade's R is split into
    spot     the price move net of spread, commission and slippage (swap NOT charged)
    carry    side x the differential in force each day of the holding, x days/365 x price / risk
             -- labelled RATE-DIFFERENTIAL CARRY PROXY: it is NOT broker swap, which is not
             available historically and is never assumed
    financing a declared broker markup (FINANCING_MARKUP_PCT per year, charged on either side)
    net = spot + carry - financing
so the battery judges the combined return while every component stays reportable.
"""

from __future__ import annotations

import numpy as np

from ...data.rates import RateSeries, differential
from .primitives import Primitive
from .study import Study

CARRY_VERSION = "carry-1.0.0"
CARRY_LABEL = "RATE-DIFFERENTIAL CARRY PROXY"
FINANCING_MARKUP_PCT = 0.5  # declared: a retail broker's financing markup, % per year, either side
LEVEL, STEP, POLICY_MOVE = 1.00, 0.25, 0.10
GROUPS3 = ((0.0,), (1.0,), (2.0,))


def _state(x: np.ndarray, threshold: float) -> np.ndarray:
    out = np.full(len(x), np.nan)
    ok = np.isfinite(x)
    out[ok] = np.where(x[ok] >= threshold, 2.0, np.where(x[ok] <= -threshold, 0.0, 1.0))
    return out


def rate_primitives(series: dict, rate_type: str) -> dict[str, Primitive]:
    def diff_at(s, t):
        return differential(series, s.symbol, rate_type, t)

    def level(s, m, o):
        return _state(diff_at(s, s.available_at), LEVEL)

    def change(s, m, o):
        t = s.available_at
        return _state(diff_at(s, t) - diff_at(s, t - 91 * 86400), STEP)

    def accel(s, m, o):
        t = s.available_at
        d0, d1, d2 = diff_at(s, t), diff_at(s, t - 91 * 86400), diff_at(s, t - 182 * 86400)
        return _state((d0 - d1) - (d1 - d2), STEP)

    def policy(s, m, o):
        t = s.available_at
        a, b = series.get((s.symbol[:3], "POLICY")), series.get((s.symbol[3:], "POLICY"))
        if a is None or b is None:
            return np.full(len(s), np.nan)
        move = (a.asof(t) - a.value_days_ago(t, 30)) - (b.asof(t) - b.value_days_ago(t, 30))
        return _state(move, POLICY_MOVE)

    defs = {"rate_level": ("differential level >= +1pp / <= -1pp, signed to the pair", level),
            "rate_change": ("91-day change of the differential >= +0.25pp / <= -0.25pp", change),
            "rate_accel": ("acceleration of the differential (91d change minus the prior 91d) >= +/-0.25pp", accel),
            "policy_move": ("a policy move in the last 30 days favouring the base (+0.10pp) or the quote", policy)}
    return {n: Primitive(n, "interest rates", f"{text} ({rate_type if n != 'policy_move' else 'POLICY'})",
                         "categorical", ("own bars", f"rates:{rate_type}"), fn, (0, 1, 2))
            for n, (text, fn) in defs.items()}


def carry_r(series: dict, rate_type: str, pair: str, side: int, entry_t, exit_t, price, risk) -> np.ndarray:
    """RATE-DIFFERENTIAL CARRY PROXY in R per trade: side x mean daily differential in force over the
    holding x days/365 x price / risk. NaN where the differential is unavailable on any day held."""
    entry_t, exit_t = np.asarray(entry_t, np.int64), np.asarray(exit_t, np.int64)
    out = np.full(len(entry_t), np.nan)
    for i in range(len(entry_t)):
        if exit_t[i] <= entry_t[i] or not np.isfinite(risk[i]) or risk[i] <= 0:
            out[i] = 0.0 if exit_t[i] <= entry_t[i] else np.nan
            continue
        days = (exit_t[i] - entry_t[i]) / 86400.0
        grid = entry_t[i] + np.arange(int(np.ceil(days))) * 86400
        d = differential(series, pair, rate_type, grid)
        if not np.isfinite(d).all():
            continue
        out[i] = side * float(d.mean()) / 100.0 * days / 365.0 * price[i] / risk[i]
    return out


class CarryStudy(Study):
    """A Study whose trade R includes the carry proxy and the financing markup (see the module docstring)."""

    def __init__(self, data, segment, binnings, costs, *, rates: dict, rate_type: str,
                 markup_pct: float = FINANCING_MARKUP_PCT, **kw) -> None:
        super().__init__(data, segment, binnings, costs, **kw)
        self.rates, self.rate_type, self.markup = rates, rate_type, markup_pct

    def outcome(self, symbol, exit_, side, stress="base"):
        key = (symbol, exit_.key, side, stress)
        fresh = key not in self._out
        o = super().outcome(symbol, exit_, side, stress)
        if fresh:
            sd, rows = self.data[symbol], self.rows[symbol]
            delay = 1 if stress == "delay" else 0
            ei = np.minimum(rows + 1 + delay, len(sd.series) - 1)
            entry_t = sd.series.open_time[ei]
            price = sd.series.mid_close[rows]
            risk = exit_.stop_atr * sd.atr[rows]
            carry = carry_r(self.rates, self.rate_type, symbol, side, entry_t, o["exit_t"], price, risk)
            days = np.clip((np.asarray(o["exit_t"], float) - entry_t) / 86400.0, 0, None)
            fin = self.markup / 100.0 * days / 365.0 * price / risk
            o["spot"] = o["r"]
            o["carry"], o["financing"] = carry, fin
            o["r"] = np.where(np.isfinite(carry), o["spot"] + carry - fin, np.nan)
        return o


__all__ = ["CARRY_LABEL", "CARRY_VERSION", "CarryStudy", "FINANCING_MARKUP_PCT", "GROUPS3", "carry_r",
           "rate_primitives"]
