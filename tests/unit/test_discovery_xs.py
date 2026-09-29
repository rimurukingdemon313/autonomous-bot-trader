"""The cross-sectional momentum primitive: causal, signed to the pair, and absent rather than guessed."""

from __future__ import annotations

import numpy as np

from aitrader.research.discovery.primitives import PRIMITIVE_BY_NAME, USD_SIGN, primitive_leakage
from tests.unit.discovery_market import series

XS = PRIMITIVE_BY_NAME["xs_mom"]
N = 400


def market(drift: dict[str, float], seed: int = 5, pairs=tuple(USD_SIGN)):
    """D1 bars for the USD pairs; `drift` is each non-USD currency's daily log move against the dollar."""
    rng = np.random.default_rng(seed)
    out = {}
    for k, sym in enumerate(pairs):
        ccy = sym.replace("USD", "")
        strength = np.cumsum(drift.get(ccy, 0.0) + rng.normal(0, 0.003, N))
        # a pair quoted against USD rises with its currency; USDxxx falls when xxx strengthens
        mid = (110.0 if sym.endswith("JPY") else 1.2) * np.exp(-USD_SIGN[sym] * strength)
        out[sym] = series(sym, mid, np.random.default_rng(100 + k), wick=0.003, half=0.00004, timeframe="D1")
    return out


def column(mk, sym):
    return XS.column(mk[sym], None, {k: v for k, v in mk.items() if k != sym})


def test_it_is_causal_for_both_quote_directions():
    mk = market({"EUR": 0.002, "JPY": -0.002})
    rows = list(range(150, N, 41)) + [N - 1]
    for sym in ("EURUSD", "USDJPY", "NZDUSD"):
        assert primitive_leakage(XS, mk[sym], {k: v for k, v in mk.items() if k != sym}, rows) == []


def test_buying_the_pair_buys_the_strong_currency_whichever_side_the_dollar_is_quoted():
    mk = market({"EUR": 0.004, "JPY": -0.004})  # EUR strongest, JPY weakest, the rest flat
    last = slice(200, N)
    eur, jpy, cad = column(mk, "EURUSD")[last], column(mk, "USDJPY")[last], column(mk, "USDCAD")[last]
    assert np.nanmean(eur) > 1.0  # long EURUSD = long the strongest currency
    assert np.nanmean(jpy) > 1.0  # long USDJPY = short the weakest currency
    assert abs(np.nanmean(cad)) < 0.5 * min(np.nanmean(eur), np.nanmean(jpy))


def test_a_pair_without_usd_or_a_thin_cross_section_is_nan_not_zero():
    mk = market({})
    cross = series("EURGBP", np.full(N, 0.85), np.random.default_rng(9), wick=0.002, half=0.00003, timeframe="D1")
    assert np.isnan(XS.column(cross, None, mk)).all()
    thin = market({}, pairs=("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"))  # 5 of 7: below the minimum
    assert np.isnan(column(thin, "EURUSD")).all()
