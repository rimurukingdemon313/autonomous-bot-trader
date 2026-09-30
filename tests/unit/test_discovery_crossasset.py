"""Round 4 states: fixed levels, signed to the pair, blind to later data, and the own-move control."""

from __future__ import annotations

import numpy as np

from aitrader.data.external import ExternalSeries
from aitrader.research.discovery.catalog import truncation_leaks
from aitrader.research.discovery.crossasset import crossasset_primitives
from tests.unit.discovery_market import series

N = 300


def bars(sym, drift=0.0, seed=1, base=None):
    rng = np.random.default_rng(seed)
    start = base or (110.0 if sym.endswith("JPY") else 1.2)
    mid = start * np.exp(np.cumsum(drift + rng.normal(0, 0.002, N)))
    return series(sym, mid, np.random.default_rng(seed + 50), wick=0.001, half=0.00002, timeframe="D1")


def ext_on(s, values, every=1, delay=3600):
    idx = np.arange(0, len(s), every)
    t = s.available_at[idx] - delay
    return ExternalSeries("x", t, np.asarray(values, float)[: len(idx)], t)


def test_gold_speaks_only_to_aud_base_pairs_and_the_control_is_the_pairs_own_move():
    aud, eur = bars("AUDUSD"), bars("EURUSD", seed=2)
    gold = bars("XAUUSD", drift=0.006, seed=3, base=1300.0)  # ~+3% per 5 days: favours buying AUD
    p = crossasset_primitives({}, gold)
    g = p["gold_pull"].column(aud, None, {})
    assert np.isnan(g[:5]).all() and (g[10:] == 2).mean() > 0.8
    assert np.isnan(p["gold_pull"].column(eur, None, {})).all()
    up = bars("AUDUSD", drift=0.004, seed=4)
    own = p["own5"].column(up, None, {})
    assert np.isnan(own[:5]).all() and (own[5:] == 2).mean() > 0.8


def test_vix_jumps_and_inflation_acceleration_use_fixed_levels_signed_to_the_pair():
    eur, jpy = bars("EURUSD"), bars("USDJPY", seed=5)
    vix = np.r_[np.full(100, 15.0), np.full(200, 19.0)]  # +26.7% at bar 100
    j = crossasset_primitives({"vix": ext_on(eur, vix)})["vix_jump"].column(eur, None, {})
    assert j[100] == 2 and j[99] == 1 and j[110] == 1
    # monthly CPI: flat, then 12-month inflation accelerates by far more than 0.3pp
    cpi = np.r_[np.full(20, 100.0), 100.0 * 1.01 ** np.arange(1, 19)]  # one print every 8 bars: 38 prints
    for s, favoured in ((eur, 0.0), (jpy, 2.0)):  # accelerating US inflation: sell EURUSD, buy USDJPY
        col = crossasset_primitives({"cpi_us": ext_on(s, cpi, every=8)})["usd_infl"].column(s, None, {})
        assert favoured in col[np.isfinite(col)]
        assert (2.0 - favoured) not in col[np.isfinite(col)]


def test_no_state_sees_anything_published_after_the_bar():
    s = bars("AUDUSD", seed=7)
    gold = bars("XAUUSD", seed=8, base=1300.0)
    rng = np.random.default_rng(9)
    ext = {"vix": ext_on(s, 15 + 10 * rng.random(N)), "cpi_us": ext_on(s, 100 + np.cumsum(rng.random(N // 20 + 1)),
                                                                       every=20)}
    rows = list(range(40, N, 19))
    for name in ("own5", "gold_pull", "vix_jump", "usd_infl"):
        def col(s_, o_, name=name):
            cut_t = int(s_.available_at[-1])
            e = {k: v.truncated(cut_t) for k, v in ext.items()}
            g = gold.take(slice(0, int(np.searchsorted(gold.available_at, cut_t, side="right"))))
            return crossasset_primitives(e, g)[name].column(s_, None, o_)
        assert truncation_leaks(col, s, {}, rows) == [], name
