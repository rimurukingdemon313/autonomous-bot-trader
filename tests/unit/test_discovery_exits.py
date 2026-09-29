"""The declared exit menu, on price paths built by hand so every R is known in advance.

Costs are zero unless a test is about costs, and ATR is fixed at 0.0010, so a stop of 1 ATR is
10 pips and every result can be checked with a pencil.
"""

from __future__ import annotations

import numpy as np
import pytest

from aitrader.data.bars import BarSeries
from aitrader.research.discovery.exits import EXIT_BY_KEY, EXIT_MENU, ExitSpec, simulate
from aitrader.research.labels import BUY, SELL, CostModel, TEMPLATES, compute_labels

T0 = 1_262_563_200  # 2010-01-04 00:00 UTC, a Monday
ATR = 0.0010
FREE = CostModel(slippage_pips=0.0, commission_pips_rt=0.0, swap_atr_per_night=0.0)


def bars(ohlc, half=0.0):
    a = np.asarray(ohlc, float)
    n = len(a)
    return BarSeries.from_columns("EURUSD", "H1", "test", open_time=T0 + 3600 * np.arange(n),
                                  bid_open=a[:, 0] - half, bid_high=a[:, 1] - half, bid_low=a[:, 2] - half,
                                  bid_close=a[:, 3] - half, ask_open=a[:, 0] + half, ask_high=a[:, 1] + half,
                                  ask_low=a[:, 2] + half, ask_close=a[:, 3] + half, ticks=np.ones(n),
                                  spread_mean=np.full(n, 2 * half), spread_max=np.full(n, 2 * half))


def flat(n, px=1.1000):
    return [[px, px + 0.00002, px - 0.00002, px]] * n


def run(path, exit_, side=BUY, costs=FREE, delay=0, half=0.0):
    s = bars(path, half)
    return simulate(s, np.array([0]), side, exit_, 0.0001, costs, atr=np.full(len(s), ATR), delay=delay)


def one(o, field="r"):
    return float(getattr(o, field)[0])


def test_the_menu_is_declared_and_its_keys_are_unique():
    assert [e.key for e in EXIT_MENU] == [f"E{i}" for i in range(1, 9)]
    assert {e.kind for e in EXIT_MENU} == {"barrier", "time", "trailing", "breakeven", "partial", "structure"}
    with pytest.raises(ValueError):
        ExitSpec("X", "martingale")


def test_a_barrier_reaches_its_target():
    path = flat(1) + [[1.1000, 1.1005, 1.0996, 1.1004], [1.1004, 1.1016, 1.1003, 1.1015]] + flat(30, 1.1015)
    o = run(path, EXIT_BY_KEY["E1"])
    assert one(o) == pytest.approx(1.5) and o.reason[0] == 1 and o.exit_index[0] == 2 and o.bars_held[0] == 2


def test_a_bar_touching_stop_and_target_is_a_stop_and_a_gap_fills_at_the_open():
    both = flat(1) + [[1.1000, 1.1020, 1.0985, 1.1000]] + flat(30)
    assert one(run(both, EXIT_BY_KEY["E1"])) == pytest.approx(-1.0)
    gap = flat(1) + [[1.1000, 1.1002, 1.0998, 1.1000], [1.0980, 1.0985, 1.0975, 1.0982]] + flat(30, 1.0982)
    assert one(run(gap, EXIT_BY_KEY["E1"])) == pytest.approx(-2.0)  # opened 20 pips below: the gap is the loss


def test_the_time_exit_closes_at_the_last_bars_close():
    path = flat(1) + [[1.1000, 1.1003, 1.0997, 1.1001]] * 23 + [[1.1001, 1.1006, 1.1000, 1.1005]] + flat(10, 1.1005)
    o = run(path, EXIT_BY_KEY["E4"])
    assert o.reason[0] == 0 and o.bars_held[0] == 24 and one(o) == pytest.approx(0.0005 / 0.0020)


def test_a_trailing_stop_follows_the_best_close_from_the_next_bar():
    # closes climb to 1.1030, then price falls; the stop was trailed to 1.1030 - 1.5 ATR = 1.1015
    up = [[1.1000 + 0.0005 * k, 1.1003 + 0.0005 * k, 1.0999 + 0.0005 * k, 1.1005 + 0.0005 * k] for k in range(6)]
    down = [[1.1030, 1.1030, 1.1010, 1.1012]] + flat(60, 1.1012)
    o = run(flat(1) + up + down, EXIT_BY_KEY["E5"])
    assert o.reason[0] == -1 and one(o) == pytest.approx((1.1015 - 1.1000) / 0.0015)


def test_a_dynamic_stop_moves_on_closes_never_on_the_same_bars_high():
    # one bar spikes to +3 ATR but closes at +0.2 ATR: the trail comes from the close, not the spike
    spike = [[1.1000, 1.1030, 1.0999, 1.1002], [1.1002, 1.1004, 1.0990, 1.0995]] + flat(60, 1.0995)
    o = run(flat(1) + spike, EXIT_BY_KEY["E5"])
    assert o.reason[0] != -1 or one(o) < 0.5  # a spike-based trail would have locked +1.5R


def test_breakeven_moves_the_stop_to_entry_after_one_r():
    path = flat(1) + [[1.1000, 1.1011, 1.0999, 1.1008], [1.1008, 1.1009, 1.0995, 1.0997]] + flat(60, 1.0997)
    o = run(path, EXIT_BY_KEY["E6"])
    assert o.reason[0] == -1 and one(o) == pytest.approx(0.0)


def test_a_partial_takes_half_at_one_r_and_trails_the_rest():
    rise = [[1.1000, 1.1011, 1.0999, 1.1010], [1.1010, 1.1025, 1.1009, 1.1024]]
    fall = [[1.1024, 1.1024, 1.1010, 1.1012]] + flat(60, 1.1012)
    o = run(flat(1) + rise + fall, EXIT_BY_KEY["E7"])
    # half: +1R; rest: stopped at the trail 1.1024 - 1 ATR = 1.1014 -> +1.4R
    assert o.reason[0] == 2 and one(o) == pytest.approx(0.5 * 1.0 + 0.5 * 1.4)


def test_the_structure_stop_sits_beyond_the_last_confirmed_swing():
    # a swing low at 1.0985 confirmed three bars later; the stop goes 0.1 ATR below it
    v = [1.1000, 1.0995, 1.0990, 1.0985, 1.0990, 1.0995, 1.1000, 1.1000, 1.1000]
    path = [[x, x + 0.00005, x - 0.00005 if x != 1.0985 else 1.0985, x] for x in v]
    path += [[1.1000, 1.1000, 1.0983, 1.0990]] + flat(60, 1.0990)
    s = bars(path)
    o = simulate(s, np.array([8]), BUY, EXIT_BY_KEY["E8"], 0.0001, FREE, atr=np.full(len(s), ATR))
    risk = 1.1000 - (1.0985 - 0.1 * ATR)  # 16 pips, not the 10 of a fixed 1-ATR stop
    # the bar trades through the stop, so it fills AT the stop: exactly -1R; the excursion shows the distance
    assert o.reason[0] == -1 and float(o.r[0]) == pytest.approx(-1.0)
    assert float(o.mae_r[0]) == pytest.approx((1.0983 - 1.1000) / risk)


def test_sells_mirror_buys_and_pay_the_spread_on_the_ask():
    path = flat(1) + [[1.1000, 1.1004, 1.0983, 1.0986]] + flat(30, 1.0986)
    o = run(path, EXIT_BY_KEY["E1"], side=SELL, half=0.00005)
    # sold at the bid 1.09995; the target 1.5 ATR lower (1.09845) is reached on the ASK (low 1.09835)
    assert o.reason[0] == 1 and one(o) == pytest.approx(1.5)


def test_costs_and_a_delayed_entry_are_charged():
    path = flat(1) + [[1.1000, 1.1016, 1.0999, 1.1015]] + flat(30, 1.1015)
    base = one(run(path, EXIT_BY_KEY["E1"]))
    costly = one(run(path, EXIT_BY_KEY["E1"], costs=CostModel(0.1, 0.7, 0.0)))
    assert costly < base
    late = run(path, EXIT_BY_KEY["E1"], delay=1)  # enters one bar later, after the move: no target, a time exit
    assert late.reason[0] == 0 and late.exit_index[0] == 2 + 23 and abs(one(late)) < 0.05


def test_e1_and_e2_reproduce_the_existing_templates_exactly():
    rng = np.random.default_rng(3)
    mid = 1.2 * np.exp(np.cumsum(rng.normal(0, 0.0008, 600)))
    o = np.concatenate(([mid[0]], mid[:-1]))
    w = np.abs(rng.normal(0, 0.0004, 600)) * 1.2
    s = bars(np.column_stack([o, np.maximum(o, mid) + w, np.minimum(o, mid) - w, mid]), half=0.00004)
    rows = np.arange(30, 500, 3)
    lab = compute_labels(s, 0.0001, rows=rows)
    for key, tpl in (("E1", TEMPLATES[0]), ("E2", TEMPLATES[1])):
        for side in (BUY, SELL):
            mine = simulate(s, rows, side, EXIT_BY_KEY[key], 0.0001)
            ref = lab.outcomes[(tpl.key, side)]
            assert np.allclose(mine.r, ref.r, equal_nan=True) and np.array_equal(mine.exit_index, ref.exit_index)
