"""Round 2 features: information the bars do not contain, and the regime engine built on it.

Every feature is a categorical STATE at a FIXED, economically interpretable level, not a fitted
tercile: nothing about it is estimated from outcomes, so it adds no degree of freedom for a
backtest to fit. External values are read point in time (`ExternalSeries.asof` on the bar's
close), so a D1 decision at the 17:00 New York close sees only what was public by then.

    feature      states (0 / 1 / 2)                                       source
    vix_state    VIX < 20 calm / 20-30 elevated / >= 30 stress             Cboe VIX close
    vix_trend    VIX vs 5 closes earlier: < -10% falling / flat / > +10% rising
    usd_rate     US 10y monthly-average change, SIGNED TO THE PAIR:       Fed H.15
                 2 = the change (> +10bp or < -10bp) favours BUYING the pair (yields up and the pair
                 buys USD, or yields down and the pair sells USD); 0 = it favours selling; 1 = no move
    oil_pull     Brent 20-observation log change, signed to the pair's     EIA Brent
                 oil-linked currency (USDCAD only): 2 = favours buying the pair, 0 = selling,
                 1 = |change| < 5%
    trend_sign   sign of the pair's own 120-bar move (time-series momentum): 0 down / 1 flat / 2 up

The regime engine (`regime_frame`) reports these together with the Round 1 price regimes
(er120 trend/range, atr_pctile volatility, usd_basket USD strength) for every decision row, so
every result can be broken down by the state it was taken in.
"""

from __future__ import annotations

import numpy as np

from ...data.external import ExternalSeries
from ...features.store import INDEX
from .catalog import FeatureRecord
from .primitives import USD_SIGN, Primitive

MACRO_VERSION = "macro-1.0.0"
VIX_LEVELS = (20.0, 30.0)
VIX_MOVE = 0.10
RATE_MOVE = 0.10  # percentage points of the monthly average
OIL_MOVE = 0.05
OIL_SIGN = {"USDCAD": -1}  # buying USDCAD sells the oil-linked currency
GROUPS3 = ((0.0,), (1.0,), (2.0,))


def _state(x: np.ndarray, lo: float, hi: float) -> np.ndarray:
    out = np.full(len(x), np.nan)
    ok = np.isfinite(x)
    out[ok] = np.where(x[ok] < lo, 0.0, np.where(x[ok] >= hi, 2.0, 1.0))
    return out


def _signed_move(x: np.ndarray, sign: float, threshold: float) -> np.ndarray:
    """2 when sign * x > threshold (favours buying), 0 when < -threshold, 1 otherwise; NaN stays NaN."""
    y = sign * x
    out = np.full(len(x), np.nan)
    ok = np.isfinite(y)
    out[ok] = np.where(y[ok] > threshold, 2.0, np.where(y[ok] < -threshold, 0.0, 1.0))
    return out


def macro_primitives(ext: dict[str, ExternalSeries]) -> dict[str, Primitive]:
    """The Round 2 primitives bound to loaded external series (only those whose series is given)."""

    def vix_state(s, m, o):
        return _state(ext["vix"].asof(s.available_at), *VIX_LEVELS)

    def vix_trend(s, m, o):
        now, before = ext["vix"].asof(s.available_at), ext["vix"].asof_lag(s.available_at, 5)
        with np.errstate(invalid="ignore", divide="ignore"):
            ch = now / before - 1.0
        return _signed_move(ch, 1.0, VIX_MOVE)

    def usd_rate(s, m, o):
        if s.symbol not in USD_SIGN:
            return np.full(len(s), np.nan)
        y = ext["us10y"]
        ch = y.asof(s.available_at) - y.asof_lag(s.available_at, 1)
        return _signed_move(ch, float(USD_SIGN[s.symbol]), RATE_MOVE)  # USD_SIGN +1: the pair rises with USD

    def oil_pull(s, m, o):
        if s.symbol not in OIL_SIGN:
            return np.full(len(s), np.nan)
        b = ext["brent"]
        with np.errstate(invalid="ignore", divide="ignore"):
            ch = np.log(b.asof(s.available_at) / b.asof_lag(s.available_at, 20))
        return _signed_move(ch, float(OIL_SIGN[s.symbol]), OIL_MOVE)

    def trend_sign(s, m, o):
        r = m[:, INDEX["r120"]]
        out = np.full(len(s), np.nan)
        ok = np.isfinite(r)
        out[ok] = np.sign(r[ok]) + 1.0
        return out

    defs = {
        "vix_state": ("vix", "risk regime: VIX close < 20 calm / 20-30 elevated / >= 30 stress", vix_state),
        "vix_trend": ("vix", "VIX against 5 closes earlier: < -10% falling / flat / > +10% rising", vix_trend),
        "usd_rate": ("us10y", "change of the US 10y monthly average, signed to the pair: 2 favours buying the pair "
                              "(> 10bp in the pair's USD direction), 0 favours selling, 1 no move", usd_rate),
        "oil_pull": ("brent", "Brent 20-observation log change signed to the oil-linked currency (USDCAD): 2 favours "
                              "buying the pair (> 5%), 0 selling, 1 no move", oil_pull),
        "trend_sign": (None, "sign of the pair's own 120-bar move: 0 down / 1 flat / 2 up (time-series momentum)",
                       trend_sign),
    }
    return {name: Primitive(name, "round 2 state", text, "categorical",
                            ("own bars",) + ((f"external:{src}",) if src else ()), fn, (0, 1, 2))
            for name, (src, text, fn) in defs.items() if src is None or src in ext}


def macro_records(program: str, prims: dict[str, Primitive], timeframe: str = "D1") -> dict[str, FeatureRecord]:
    return {n: FeatureRecord(
        f"{n}.{timeframe}", f"on {timeframe} bars: {p.definition}", p.dimension, "categorical", timeframe, p.requires,
        f"aitrader/research/discovery/macro.py ({MACRO_VERSION}); research only", MACRO_VERSION,
        "external values as public at the bar close (ExternalSeries.asof); fixed levels, nothing fitted; NaN "
        "when a value is unavailable, never a default",
        "does this state carry information about the pair's direction?", program) for n, p in prims.items()}


def external_leaks(name: str, series, ext: dict[str, ExternalSeries], rows, factory=None) -> list[int]:
    """Rows whose value changes when every external series is cut at that row's decision time:
    a value computed from anything published later is a leak."""
    factory = factory or macro_primitives
    full = factory(ext)[name].column(series, None, {})
    bad = []
    for i in rows:
        t = int(series.available_at[int(i)])
        cut = {k: v.truncated(t) for k, v in ext.items()}
        rebound = factory(cut)[name]
        v = rebound.column(series, None, {})[int(i)]
        a = full[int(i)]
        if not ((np.isnan(a) and np.isnan(v)) or a == v):
            bad.append(int(i))
    return bad


def regime_frame(sd, prims: dict[str, Primitive]) -> dict[str, np.ndarray]:
    """Every regime state on every bar of one instrument (SymbolData): the Round 2 states plus the
    Round 1 price regimes, for breaking results down by the state they were taken in."""
    out = {n: np.asarray(p.column(sd.series, None, {}), float) for n, p in prims.items()}
    for n in ("er120", "atr_pctile", "usd_basket"):
        if n in sd.columns:
            out[n] = np.asarray(sd.columns[n], float)
    return out


__all__ = ["GROUPS3", "MACRO_VERSION", "OIL_SIGN", "external_leaks", "macro_primitives", "macro_records",
           "regime_frame"]
