"""Feature store: causality, research = production, missing stays missing.

The causality checker is itself tested: a deliberately leaky feature must
be caught (a guard that cannot fail guards nothing).
"""

from __future__ import annotations

import numpy as np
import pytest

from aitrader.data.bars import BarSeries
from aitrader.features.store import LOOKBACK, NAMES, SPECS, compute_at, compute_matrix


def synthetic_h1(n=900, seed=7, symbol="EURUSD"):
    rng = np.random.default_rng(seed)
    t0 = 1_300_000_000 // 3600 * 3600
    steps = rng.normal(0, 0.0008, n) + 0.0002 * np.sin(np.arange(n) / 40)
    mid = 1.2 + np.cumsum(steps)
    o = np.concatenate(([mid[0]], mid[:-1]))
    wick = np.abs(rng.normal(0, 0.0006, n))
    hi = np.maximum(o, mid) + wick
    lo = np.minimum(o, mid) - wick
    spread = 0.00008 + 0.00004 * rng.random(n)
    half = spread / 2
    return BarSeries.from_columns(
        symbol, "H1", "synthetic", open_time=t0 + 3600 * np.arange(n),
        bid_open=o - half, bid_high=hi - half, bid_low=lo - half, bid_close=mid - half,
        ask_open=o + half, ask_high=hi + half, ask_low=lo + half, ask_close=mid + half,
        ticks=rng.integers(50, 500, n), spread_mean=spread, spread_max=spread * 2)


def truncation_violations(fn, series: BarSeries, rows) -> list[tuple[int, str]]:
    """Rows where fn(full)[i] differs from fn(history up to i)[i]."""
    full = fn(series)
    bad = []
    for i in rows:
        part = fn(series.take(slice(0, i + 1)))[i]
        for j, name in enumerate(NAMES[: full.shape[1]]):
            a, b = full[i, j], part[j]
            if not ((np.isnan(a) and np.isnan(b)) or a == b or abs(a - b) <= 1e-12 * max(1.0, abs(a))):
                bad.append((i, name))
    return bad


ROWS = list(range(0, 900, 37)) + [899]


def test_every_feature_is_causal_on_every_sampled_row():
    s = synthetic_h1()
    assert truncation_violations(compute_matrix, s, ROWS) == []


def test_the_causality_check_catches_an_injected_one_bar_leak():
    def leaky(series):
        m = compute_matrix(series)
        c = series.mid_close
        nxt = np.full(len(c), np.nan)
        nxt[:-1] = c[1:]              # tomorrow's close
        m[:, 0] = nxt - c             # smuggled into feature 0
        return m
    s = synthetic_h1()
    assert truncation_violations(leaky, s, ROWS), "a one-bar leak went undetected"


@pytest.mark.parametrize("field", ["mid_high", "mid_low", "ticks"])
def test_the_check_catches_future_high_low_and_activity(field):
    def leaky(series):
        m = compute_matrix(series)
        x = getattr(series, field).astype(float)
        m[:, 1] = np.concatenate((x[1:], [np.nan]))
        return m
    assert truncation_violations(leaky, synthetic_h1(), ROWS)


def test_the_check_catches_whole_series_normalisation():
    def leaky(series):
        m = compute_matrix(series)
        c = series.mid_close
        with np.errstate(invalid="ignore", divide="ignore"):
            m[:, 2] = (c - c.mean()) / c.std()   # statistics from the future
        return m
    assert truncation_violations(leaky, synthetic_h1(), ROWS)


def test_the_check_catches_a_centred_rolling_window():
    def leaky(series):
        m = compute_matrix(series)
        c = series.mid_close
        k = 5
        centred = np.full(len(c), np.nan)
        for i in range(k, len(c) - k):
            centred[i] = c[i - k:i + k + 1].mean()
        m[:, 3] = centred
        return m
    assert truncation_violations(leaky, synthetic_h1(), ROWS)


def test_production_window_equals_research_history():
    """What the live system computes from LOOKBACK bars equals the research value."""
    s = synthetic_h1()
    full = compute_matrix(s)
    for i in range(LOOKBACK, len(s), 29):
        t = int(s.available_at[i])
        fv = compute_at(s, t)
        assert fv.bar_open_time == int(s.open_time[i])
        np.testing.assert_allclose(fv.array(), full[i], rtol=1e-12, atol=1e-15, equal_nan=True)


def test_compute_at_uses_only_bars_closed_by_the_decision_time():
    s = synthetic_h1()
    i = 500
    t = int(s.available_at[i])
    assert compute_at(s, t).bar_open_time == int(s.open_time[i])
    # One second before bar i closes, bar i is not yet known.
    assert compute_at(s, t - 1).bar_open_time == int(s.open_time[i - 1])


def test_missing_history_is_missing_not_zero():
    s = synthetic_h1(n=100)
    fv = compute_at(s, int(s.available_at[-1]))
    assert "ma_slope" in fv.missing and "vol_ratio" in fv.missing
    assert not fv.complete
    assert np.isnan(fv.values["ma_slope"])
    m = compute_matrix(s)
    for j, spec in enumerate(SPECS):
        assert np.all(np.isnan(m[: min(spec.window, len(s)), j])), spec.name


def test_features_are_scale_free():
    """The same path at 100x the price level gives the same ATR-scaled features."""
    s = synthetic_h1()
    f = {k: getattr(s, k) * 100 for k in (
        "bid_open", "bid_high", "bid_low", "bid_close", "ask_open", "ask_high", "ask_low", "ask_close",
        "spread_mean", "spread_max")}
    big = BarSeries.from_columns("USDJPY", "H1", "x", open_time=s.open_time, ticks=s.ticks, **f)
    np.testing.assert_allclose(compute_matrix(big), compute_matrix(s), rtol=1e-9, atol=1e-9, equal_nan=True)


def test_known_answer_breakout_and_efficiency():
    # A straight staircase up: efficiency 1, close above the prior high.
    n = 400
    t0 = 1_300_000_000 // 3600 * 3600
    mid = 1.0 + 0.001 * np.arange(n)
    o = mid - 0.001
    s = BarSeries.from_columns(
        "EURUSD", "H1", "x", open_time=t0 + 3600 * np.arange(n),
        bid_open=o, bid_high=mid + 0.0002, bid_low=o - 0.0002, bid_close=mid,
        ask_open=o + 1e-5, ask_high=mid + 0.00021, ask_low=o - 0.00019, ask_close=mid + 1e-5,
        ticks=np.full(n, 100), spread_mean=np.full(n, 1e-5), spread_max=np.full(n, 1e-5))
    fv = compute_at(s, int(s.available_at[-1]))
    assert fv.values["er24"] == pytest.approx(1.0)
    assert fv.values["er120"] == pytest.approx(1.0)
    assert fv.values["brk_hi120"] > 0
    assert fv.values["range_pos120"] > 0.95
    assert fv.values["r24"] > 0
