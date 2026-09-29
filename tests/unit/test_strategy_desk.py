"""The strategy desk: sixteen classic rules and their scoreboard, never looking past the last closed bar.

Scenarios are built by hand, so each right answer is known: a breakout that fires, a trade that
reaches its target, one that touches stop and target in the same bar (stop first), one still open
(not counted), and the spread paid on entry.
"""

from __future__ import annotations

import numpy as np

from aitrader.data.bars import BarSeries
from aitrader.features.strategy_desk import STRATEGIES, TARGET_ATR, scoreboard, signals, indicators, strategy_desk

from tests.integration.test_pipeline import START, market

FIELDS = ("open_time", "bid_open", "bid_high", "bid_low", "bid_close", "ask_open", "ask_high", "ask_low",
          "ask_close", "ticks", "spread_mean", "spread_max")


def bars(ohlc, tf="M5", half=0.00005, start=START):
    a = np.asarray(ohlc, dtype=float)
    period = {"M5": 300, "H1": 3600}[tf]
    n = len(a)
    return BarSeries.from_columns("EURUSD", tf, "test", open_time=start + period * np.arange(n),
                                  bid_open=a[:, 0] - half, bid_high=a[:, 1] - half, bid_low=a[:, 2] - half,
                                  bid_close=a[:, 3] - half, ask_open=a[:, 0] + half, ask_high=a[:, 1] + half,
                                  ask_low=a[:, 2] + half, ask_close=a[:, 3] + half, ticks=np.ones(n),
                                  spread_mean=np.full(n, 2 * half), spread_max=np.full(n, 2 * half))


def test_every_strategy_is_evaluated_and_described():
    h1 = market("EURUSD", START, 24 * 40, 5, 1.10)
    ind = indicators(h1)
    sig = signals(ind, h1.open_time)
    assert set(sig) == set(STRATEGIES) and len(STRATEGIES) == 16
    assert all(len(v) == len(h1) and set(np.unique(v)) <= {-1, 0, 1} for v in sig.values())
    assert sum(int(np.abs(v).sum()) for v in sig.values()) > 50  # the rules do fire on a real-looking market


def test_a_close_above_the_last_twenty_highs_fires_the_breakout_now():
    flat = [[1.1000, 1.1005, 1.0995, 1.1000]] * 80
    d = strategy_desk("EURUSD", {"M5": bars(flat + [[1.1000, 1.1030, 1.0999, 1.1028]])}, START + 81 * 300)
    assert {"strategy": "donchian20_breakout", "tf": "M5", "signal": "BUY"}.items() <= next(
        f for f in d["firing_now"] if f["strategy"] == "donchian20_breakout").items()
    d0 = strategy_desk("EURUSD", {"M5": bars(flat)}, START + 80 * 300)
    assert not any(f["strategy"] == "donchian20_breakout" for f in d0["firing_now"])


def test_the_scoreboard_walks_each_trade_forward_stop_first_and_skips_open_ones():
    px = [[1.1000, 1.1002, 1.0998, 1.1000]] * 5
    atr = np.full(12, 0.0010)
    # a BUY at bar 4 (entry at the ask 1.10005): bar 6 reaches the target 1.10005 + 0.0015 on the bid
    win = px + [[1.1000, 1.1005, 1.0996, 1.1003], [1.1003, 1.1018, 1.1001, 1.1016]] + [[1.1016, 1.1017, 1.1014, 1.1015]] * 5
    s = {"x": np.zeros(12, int)}
    s["x"][4] = 1
    r = scoreboard(bars(win), s, atr, 24)[0]
    assert (r["trades"], r["win_rate"], r["avg_R"]) == (1, 1.0, TARGET_ATR)
    # the same bar touches both the stop and the target: counted as the stop
    both = px + [[1.1000, 1.1020, 1.0985, 1.1000]] + [[1.1000, 1.1001, 1.0999, 1.1000]] * 6
    assert scoreboard(bars(both), s, atr, 24)[0]["avg_R"] == -1.0
    # never reaching either before the last completed bar: still open, not counted
    open_ = px + [[1.1000, 1.1004, 1.0996, 1.1001]] * 7
    assert scoreboard(bars(open_), s, atr, 24)[0]["trades"] == 0


def test_the_spread_is_paid_on_entry():
    """A time exit at an unchanged mid price loses exactly the spread."""
    px = [[1.1000, 1.1002, 1.0998, 1.1000]] * 12
    s = {"x": np.zeros(12, int)}
    s["x"][2] = 1
    r = scoreboard(bars(px, half=0.0001), s, np.full(12, 0.0010), 3)[0]
    assert r["trades"] == 1 and r["avg_R"] == round(-0.0002 / 0.0010, 3)


def test_the_desk_at_a_time_cannot_see_any_later_bar():
    h1 = market("EURUSD", START, 24 * 40, 5, 1.10)
    for i in (300, 500):
        as_of = int(h1.available_at[i])
        noisy = market("EURUSD", START, 24 * 40, 42, 1.40)
        spliced = BarSeries.from_columns("EURUSD", "H1", "test", **{
            f: np.concatenate([getattr(h1, f)[:i + 1], getattr(noisy, f)[i + 1:]]) for f in FIELDS})
        assert strategy_desk("EURUSD", {"H1": spliced}, as_of) == strategy_desk("EURUSD", {"H1": h1}, as_of)
