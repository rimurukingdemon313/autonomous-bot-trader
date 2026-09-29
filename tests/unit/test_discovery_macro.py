"""Round 2 states: fixed levels, signed to the pair, and blind to anything published after the bar."""

from __future__ import annotations

import numpy as np

from aitrader.data.external import ExternalSeries
from aitrader.research.discovery.catalog import truncation_leaks
from aitrader.research.discovery.macro import external_leaks, macro_primitives
from aitrader.research.discovery.primitives import Primitive
from tests.unit.discovery_market import series

N = 300


def bars(sym, drift=0.0, seed=1):
    rng = np.random.default_rng(seed)
    mid = (110.0 if sym.endswith("JPY") else 1.2) * np.exp(np.cumsum(drift + rng.normal(0, 0.004, N)))
    return series(sym, mid, np.random.default_rng(seed + 50), wick=0.003, half=0.00004, timeframe="D1")


def ext_on(s, values, every=1, delay=3600):
    """An external series observed on every `every`-th bar, public `delay` seconds before that bar closes."""
    idx = np.arange(0, len(s), every)
    t = s.available_at[idx] - delay
    return ExternalSeries("x", t, np.asarray(values, float)[: len(idx)], t)


def test_the_vix_states_use_fixed_levels_not_fitted_ones():
    s = bars("EURUSD")
    vix = np.r_[np.full(100, 15.0), np.full(100, 25.0), np.full(100, 35.0)]
    p = macro_primitives({"vix": ext_on(s, vix)})
    st = p["vix_state"].column(s, None, {})
    assert (st[:100] == 0).all() and (st[100:200] == 1).all() and (st[200:] == 2).all()
    tr = p["vix_trend"].column(s, None, {})
    assert np.isnan(tr[:5]).all() and tr[100] == 2 and tr[150] == 1  # +67% vs five closes earlier; then flat


def test_the_rate_state_is_signed_to_the_pair():
    eur, jpy = bars("EURUSD"), bars("USDJPY", seed=2)
    y = np.r_[np.full(150, 2.0), np.full(150, 2.3)]  # US yields up 30bp
    for s, favoured in ((eur, 0.0), (jpy, 2.0)):  # yields up: sell EURUSD, buy USDJPY
        col = macro_primitives({"us10y": ext_on(s, y)})["usd_rate"].column(s, None, {})
        assert col[150] == favoured and col[151] == 1.0
    cross = bars("EURGBP", seed=3)
    assert np.isnan(macro_primitives({"us10y": ext_on(cross, y)})["usd_rate"].column(cross, None, {})).all()


def test_oil_speaks_only_to_its_currency_and_trend_is_the_sign_of_the_move():
    cad, eur = bars("USDCAD", seed=4), bars("EURUSD", seed=5)
    oil = np.exp(np.linspace(np.log(50), np.log(200), N))  # +9% per 20 days: CAD favoured, so SELL USDCAD
    col = macro_primitives({"brent": ext_on(cad, oil)})["oil_pull"].column(cad, None, {})
    assert np.isnan(col[:20]).all() and (col[20:] == 0).all()
    assert np.isnan(macro_primitives({"brent": ext_on(eur, oil)})["oil_pull"].column(eur, None, {})).all()
    up = bars("EURUSD", drift=0.003, seed=6)
    ts = macro_primitives({})["trend_sign"].column(up, None, {})
    assert ts[-1] == 2.0 and np.isnan(ts[:100]).all()


def test_no_state_can_see_a_value_published_after_the_bar():
    s = bars("USDCAD", seed=7)
    rng = np.random.default_rng(8)
    ext = {"vix": ext_on(s, 15 + 10 * rng.random(N)), "us10y": ext_on(s, 2 + rng.random(N // 20 + 1), every=20),
           "brent": ext_on(s, 60 * np.exp(np.cumsum(rng.normal(0, 0.03, N))))}
    rows = list(range(30, N, 23))
    for name in ("vix_state", "vix_trend", "usd_rate", "oil_pull"):
        assert external_leaks(name, s, ext, rows) == []
    assert truncation_leaks(lambda s_, o_: macro_primitives({})["trend_sign"].column(s_, None, o_), s, {}, rows) == []

    def leaky(e):  # reads the NEXT public VIX value: must be caught
        def fn(s_, m, o):
            v = e["vix"]
            k = np.searchsorted(v.available_at, s_.available_at, side="right")
            out = np.full(len(s_), np.nan)
            ok = k < len(v.value)
            out[ok] = v.value[k[ok]]
            return out
        return {"peek": Primitive("peek", "x", "x", "continuous", (), fn)}
    assert external_leaks("peek", s, ext, rows, factory=leaky) != []
