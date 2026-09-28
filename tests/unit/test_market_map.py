"""The market map reads structure off completed bars, and never off a bar that has not closed.

Every scenario is built by hand, so the right answer is known by construction:
a gap that is open, then entered, then filled; two equal highs that hold, then
get taken; a downtrend whose first break up is a CHoCH and whose second is a BOS.
"""

from __future__ import annotations

import numpy as np

from aitrader.data.bars import BarSeries
from aitrader.features.market_map import market_map, swings

from tests.integration.test_pipeline import START, market

T0 = START


def bars(tf, ohlc, start=T0, symbol="EURUSD"):
    period = {"M5": 300, "M15": 900, "H1": 3600}[tf]
    a = np.asarray(ohlc, dtype=float)
    o, h, lo, c = a[:, 0], a[:, 1], a[:, 2], a[:, 3]
    half = 0.00005
    n = len(a)
    return BarSeries.from_columns(symbol, tf, "test", open_time=start + period * np.arange(n),
                                  bid_open=o - half, bid_high=h - half, bid_low=lo - half, bid_close=c - half,
                                  ask_open=o + half, ask_high=h + half, ask_low=lo + half, ask_close=c + half,
                                  ticks=np.ones(n), spread_mean=np.full(n, 2 * half), spread_max=np.full(n, 2 * half))


def flat(n, px=1.1000, w=0.0004):
    return [[px, px + w / 2, px - w / 2, px]] * n


def h1_history():
    return market("EURUSD", T0 - 3600 * 24 * 20, 24 * 20, 3, 1.10)


def mp(m15, as_of=None):
    as_of = as_of or int(m15.available_at[-1])
    return market_map("EURUSD", h1_history(), {"M15": m15}, as_of)


def test_a_fair_value_gap_is_open_then_mitigated_then_gone_once_filled():
    base = flat(20)
    gap = [[1.1000, 1.1004, 1.0998, 1.1002], [1.1002, 1.1030, 1.1001, 1.1028], [1.1028, 1.1034, 1.1012, 1.1030]]
    above = [[1.1030, 1.1036, 1.1020, 1.1030]] * 5
    f = mp(bars("M15", base + gap + above))["fair_value_gaps"]["M15"]
    g = next(x for x in f if x["side"] == "bullish")
    assert (g["low"], g["high"], g["status"]) == (1.1004, 1.1012, "open")
    f = mp(bars("M15", base + gap + above + [[1.1030, 1.1031, 1.1008, 1.1025]]))["fair_value_gaps"]["M15"]
    assert next(x for x in f if x["low"] == 1.1004)["status"] == "mitigated"
    f = mp(bars("M15", base + gap + above + [[1.1030, 1.1031, 1.0999, 1.1025]]))["fair_value_gaps"]["M15"]
    assert not any(x["low"] == 1.1004 for x in f)  # traded through: filled, no longer a gap


def zigzag(points, steps=4):
    """Bars walking straight between the given closes: each turning point becomes a swing."""
    out, px = [], points[0]
    for target in points[1:]:
        for s in range(1, steps + 1):
            nxt = px + (target - px) / (steps - s + 1)
            out.append([px, max(px, nxt) + 0.00005, min(px, nxt) - 0.00005, nxt])
            px = nxt
    return out


def test_equal_highs_are_resting_liquidity_until_price_takes_them():
    path = zigzag([1.1000, 1.1050, 1.1010, 1.1050, 1.1015, 1.1030])
    liq = mp(bars("M15", path))["liquidity"]["M15"]
    assert any(abs(p["level"] - 1.10505) < 0.0002 for p in liq["equal_highs"])
    taken = mp(bars("M15", path + zigzag([1.1030, 1.1070])))["liquidity"]["M15"]
    assert not any(abs(p["level"] - 1.10505) < 0.0002 for p in taken["equal_highs"])


def test_the_first_break_against_a_downtrend_is_a_choch_and_the_next_one_a_bos():
    down = zigzag([1.1100, 1.1060, 1.1080, 1.1040, 1.1060, 1.1020])
    first = mp(bars("M15", down + zigzag([1.1020, 1.1070])))["structure"]["M15"]["last_break"]
    assert first["kind"] == "CHoCH" and first["direction"] == "bullish"
    both = mp(bars("M15", down + zigzag([1.1020, 1.1070, 1.1045, 1.1090])))["structure"]["M15"]["last_break"]
    assert both["kind"] == "BOS" and both["direction"] == "bullish"


def test_a_swing_exists_only_once_the_bars_that_confirm_it_have_closed():
    h = np.array([1, 2, 3, 5, 4, 3, 2], dtype=float)
    assert swings(h, h - 0.5)[0] == [3]
    assert swings(h[:5], h[:5] - 0.5)[0] == []  # only one bar after the peak: not yet a swing


def test_the_map_at_a_time_cannot_see_any_later_bar():
    h1 = market("EURUSD", T0, 24 * 40, 5, 1.10)
    m15 = market("EURUSD", T0, 24 * 40, 6, 1.10)  # stands in for a lower timeframe
    for i in (250, 400, 600):
        as_of = int(h1.available_at[i])
        full = market_map("EURUSD", h1, {"M15": m15}, as_of)
        cut = market_map("EURUSD", h1.take(slice(0, i + 1)), {"M15": m15.take(slice(0, i + 1))}, as_of)
        assert full == cut
        # rewriting every later bar changes nothing at this time
        noisy = market("EURUSD", T0, 24 * 40, 99, 1.30)
        spliced_h1 = BarSeries.from_columns("EURUSD", "H1", "test", **{
            f: np.concatenate([getattr(h1, f)[:i + 1], getattr(noisy, f)[i + 1:]])
            for f in ("open_time", "bid_open", "bid_high", "bid_low", "bid_close", "ask_open", "ask_high",
                      "ask_low", "ask_close", "ticks", "spread_mean", "spread_max")})
        assert market_map("EURUSD", spliced_h1, {"M15": m15.take(slice(0, i + 1))}, as_of) == cut


def test_previous_day_and_sessions_come_from_completed_hours():
    h1 = h1_history()
    as_of = int(h1.available_at[-1])
    lv = market_map("EURUSD", h1, None, as_of)["levels"]
    day0 = as_of - as_of % 86400
    y = (h1.open_time >= day0 - 86400) & (h1.open_time < day0)
    assert lv["previous_day"]["high"] == round(float(h1.mid_high[y].max()), 5)
    assert lv["previous_day"]["low"] == round(float(h1.mid_low[y].min()), 5)
    px = float(h1.mid_close[-1])
    assert lv["round_numbers"]["below"] <= px < lv["round_numbers"]["above"]


def test_three_equal_highs_are_one_pool_with_three_touches():
    path = zigzag([1.1000, 1.1050, 1.1010, 1.1050, 1.1012, 1.10502, 1.1015, 1.1030])
    pools = mp(bars("M15", path))["liquidity"]["M15"]["equal_highs"]
    near = [p for p in pools if abs(p["level"] - 1.10505) < 0.0003]
    assert len(near) == 1 and near[0]["touches"] == 3
