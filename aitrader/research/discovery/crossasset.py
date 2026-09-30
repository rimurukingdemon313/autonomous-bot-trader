"""Round 4: information from outside the FX pair, tested for what it adds BEYOND the pair's own price.

Every state is categorical at a FIXED, economically interpretable level (nothing fitted), signed so
that 2 favours BUYING the pair, and read point in time:

    own5       the pair's own 5-bar move: 0 down / 1 flat / 2 up. The CONTROL: a hypothesis that pairs a
               cross-asset state with the OPPOSITE own move asks whether the outside information leads
               FX, i.e. adds what the pair's own recent price does not already contain
    gold_pull  gold's 5-bar log move >= +2% favours buying an AUD-base pair (2), <= -2% selling it (0);
               NaN for pairs without AUD as base. Gold bars (XAUUSD, Dukascopy) close at the same
               17:00 New York instant as the FX bars and are aligned on open time
    vix_jump   VIX close / VIX 5 closes earlier - 1: >= +20% (2) / <= -20% (0) / else 1
    usd_infl   US CPI-U (NSA, never revised) 12-month inflation now minus 3 months earlier, signed to
               the pair: 2 when an acceleration >= 0.3pp favours buying the pair (the pair buys USD) or a
               deceleration favours it (the pair sells USD); 0 the opposite; NaN for non-USD pairs.
               Each CPI print is used only from the last day of the month after its reference month
"""

from __future__ import annotations

import numpy as np

from ...data.external import ExternalSeries
from .primitives import USD_SIGN, Primitive, _aligned

CROSSASSET_VERSION = "crossasset-1.0.0"
GOLD_MOVE, VIX_MOVE, INFL_MOVE = 0.02, 0.20, 0.30
GOLD_SIGN = {"AUDUSD": 1, "AUDJPY": 1}  # AUD is the base: a gold rise favours buying


def _signed(x: np.ndarray, sign: float, threshold: float) -> np.ndarray:
    y = sign * x
    out = np.full(len(x), np.nan)
    ok = np.isfinite(y)
    out[ok] = np.where(y[ok] >= threshold, 2.0, np.where(y[ok] <= -threshold, 0.0, 1.0))
    return out


def crossasset_primitives(ext: dict[str, ExternalSeries], gold=None) -> dict[str, Primitive]:
    """The Round 4 states; `ext` may hold "vix" and "cpi_us", `gold` is the XAUUSD bar series."""

    def own5(s, m, o):
        c = s.mid_close
        out = np.full(len(s), np.nan)
        if len(c) > 5:
            r = np.log(c[5:] / c[:-5])
            out[5:] = np.sign(r) + 1.0
        return out

    def gold_pull(s, m, o):
        if gold is None or s.symbol not in GOLD_SIGN or len(gold) < 6:
            return np.full(len(s), np.nan)
        gc = gold.mid_close
        g5 = np.full(len(gc), np.nan)
        g5[5:] = np.log(gc[5:] / gc[:-5])
        return _signed(_aligned(s, gold, g5), float(GOLD_SIGN[s.symbol]), GOLD_MOVE)

    def vix_jump(s, m, o):
        v = ext["vix"]
        with np.errstate(invalid="ignore", divide="ignore"):
            ch = v.asof(s.available_at) / v.asof_lag(s.available_at, 5) - 1.0
        return _signed(ch, 1.0, VIX_MOVE)

    def usd_infl(s, m, o):
        if s.symbol not in USD_SIGN:
            return np.full(len(s), np.nan)
        c, t = ext["cpi_us"], s.available_at
        with np.errstate(invalid="ignore", divide="ignore"):
            yoy_now = c.asof(t) / c.asof_lag(t, 12) - 1.0
            yoy_3m = c.asof_lag(t, 3) / c.asof_lag(t, 15) - 1.0
        accel_pp = (yoy_now - yoy_3m) * 100.0
        return _signed(accel_pp, float(USD_SIGN[s.symbol]), INFL_MOVE)  # +1: the pair rises with USD

    defs = {"own5": (None, "sign of the pair's own 5-bar move (the price-only control)", own5),
            "gold_pull": ("gold", "gold 5-bar log move >= +/-2%, signed to an AUD-base pair", gold_pull),
            "vix_jump": ("vix", "VIX change over 5 closes >= +20% / <= -20%", vix_jump),
            "usd_infl": ("cpi_us", "US CPI-U 12-month inflation now minus 3 months earlier >= +/-0.3pp, signed "
                                   "to the pair's USD leg", usd_infl)}
    out = {}
    for name, (src, text, fn) in defs.items():
        if src == "gold" and gold is None or src in ("vix", "cpi_us") and src not in ext:
            continue
        out[name] = Primitive(name, "round 4 state", text, "categorical",
                              ("own bars",) + ((f"external:{src}",) if src else ()), fn, (0, 1, 2))
    return out


__all__ = ["CROSSASSET_VERSION", "GOLD_SIGN", "crossasset_primitives"]
