"""Labels: known answers built by construction, real bid/ask, declared costs."""

from __future__ import annotations

import numpy as np
import pytest

from aitrader.data.bars import BarSeries
from aitrader.research.labels import BUY, SELL, TEMPLATE_BY_KEY, CostModel, atr24, compute_labels

PIP = 0.0001
T0 = 1_300_000_000 // 3600 * 3600  # a Sunday is irrelevant: tests don't cross nights unless stated


def build(mid_path, spread=0.0, wick=0.0005):
    """H1 bars: open = previous close; high/low = max/min(open, close) +/- wick."""
    mid = np.asarray(mid_path, float)
    n = len(mid)
    o = np.concatenate(([mid[0]], mid[:-1]))
    hi = np.maximum(o, mid) + wick
    lo = np.minimum(o, mid) - wick
    half = spread / 2
    return BarSeries.from_columns(
        "EURUSD", "H1", "t", open_time=T0 + 3600 * np.arange(n),
        bid_open=o - half, bid_high=hi - half, bid_low=lo - half, bid_close=mid - half,
        ask_open=o + half, ask_high=hi + half, ask_low=lo + half, ask_close=mid + half,
        ticks=np.full(n, 10), spread_mean=np.full(n, spread), spread_max=np.full(n, spread))


def flat_then(after, n_flat=40):
    return [1.1] * n_flat + list(after)


ZERO = CostModel(slippage_pips=0, commission_pips_rt=0, swap_atr_per_night=0)


def outcome(s, row, key, side, costs=ZERO, delay=0):
    ls = compute_labels(s, PIP, rows=np.array([row]), costs=costs, delay_bars=delay)
    o = ls.outcomes[(key, side)]
    return {k: getattr(o, k)[0] for k in ("r", "reason", "exit_index", "resolve_time", "mfe_r", "mae_r", "cost_r")}


def test_atr_is_known_on_flat_bars():
    s = build([1.1] * 60, wick=0.0005)
    assert atr24(s)[50] == pytest.approx(0.001)  # high - low = 2 * wick


def test_buy_hits_target_and_sell_hits_stop_on_a_rally():
    s = build(flat_then([1.1 + 0.0005 * k for k in range(1, 60)]))
    row = 39  # decide at the close of the last flat bar; ATR = 0.001
    b = outcome(s, row, "T1", BUY)
    assert b["reason"] == 1 and b["r"] == pytest.approx(1.5)  # target = 1.5 ATR, stop = 1 ATR
    sl = outcome(s, row, "T1", SELL)
    assert sl["reason"] == -1 and sl["r"] <= -1.0


def test_stop_and_target_in_the_same_bar_resolve_as_the_stop():
    path = [1.1] * 70  # enough future bars for the 24-bar template
    s = build(path)
    # Make bar 41 span both barriers.
    cols = {f: np.array(getattr(s, f)) for f in (
        "open_time", "bid_open", "bid_high", "bid_low", "bid_close", "ask_open", "ask_high",
        "ask_low", "ask_close", "ticks", "spread_mean", "spread_max")}
    for side in ("bid", "ask"):
        cols[f"{side}_high"][41] = 1.105
        cols[f"{side}_low"][41] = 1.095
    s2 = BarSeries.from_columns("EURUSD", "H1", "t", **cols)
    b = outcome(s2, 39, "T1", BUY)
    assert b["reason"] == -1 and b["r"] == pytest.approx(-1.0)


def test_time_exit_on_a_dead_market_costs_exactly_the_frictions():
    s = build([1.1] * 120, spread=0.0002, wick=0.0005)
    costs = CostModel(slippage_pips=0.1, commission_pips_rt=0.7, swap_atr_per_night=0.0)
    b = outcome(s, 60, "T1", BUY, costs)
    assert b["reason"] == 0
    atr = 0.001
    # enter at ask + slip, leave at bid - slip, pay commission; risk = 1 ATR
    expected = -(0.0002 + 2 * 0.1 * PIP + 0.7 * PIP) / atr
    assert b["r"] == pytest.approx(expected)
    assert b["cost_r"] == pytest.approx(-expected)


def test_a_wider_spread_can_only_make_outcomes_worse():
    rng = np.random.default_rng(3)
    s = build(1.1 + np.cumsum(rng.normal(0, 0.0007, 600)), spread=0.00015)
    rows = np.arange(60, 500, 7)
    base = compute_labels(s, PIP, rows=rows)
    wide = compute_labels(s, PIP, rows=rows, costs=CostModel(spread_multiple=2.0))
    for key in [("T1", BUY), ("T1", SELL), ("T2", BUY), ("T2", SELL)]:
        a, b = base.outcomes[key].r, wide.outcomes[key].r
        ok = np.isfinite(a) & np.isfinite(b)
        assert np.nanmean(b[ok]) < np.nanmean(a[ok])


def test_outcome_is_known_only_after_the_decision_and_at_the_exit_close():
    s = build(flat_then([1.1 + 0.0005 * k for k in range(1, 60)]))
    b = outcome(s, 39, "T1", BUY)
    assert b["resolve_time"] > int(s.available_at[39])
    assert b["resolve_time"] == int(s.available_at[b["exit_index"]])


def test_latency_moves_the_entry_later():
    s = build(flat_then([1.1 + 0.0005 * k for k in range(1, 60)]))
    now = outcome(s, 39, "T1", BUY)
    late = outcome(s, 39, "T1", BUY, delay=3)
    assert late["exit_index"] > now["exit_index"]


def test_rows_without_enough_future_are_not_computable_not_zero():
    s = build([1.1] * 60)
    b = outcome(s, 58, "T2", BUY)
    assert np.isnan(b["r"]) and b["reason"] == -9


def test_mfe_and_mae_are_reported_in_r():
    s = build(flat_then([1.1 + 0.0005 * k for k in range(1, 60)]))
    b = outcome(s, 39, "T1", BUY)
    assert b["mfe_r"] >= 1.5 - 1e-9 and b["mae_r"] <= 0


def test_templates_are_declared_and_rr_known():
    assert TEMPLATE_BY_KEY["T1"].reward_risk == pytest.approx(1.5)
    assert TEMPLATE_BY_KEY["T2"].reward_risk == pytest.approx(2.0)
