"""The time machine (dual-ai 1.16.0): a trade's levels replayed on the pair's own recent hours. On a market with no
drift it finds the odds the levels alone give (a coin flip at 1R); a drift shows; the stop is checked first; nothing
after the decision is read; the same inputs give the same numbers; too little history gives no answer, never a guess."""

from __future__ import annotations

import numpy as np
import pytest

from aitrader.data.bars import BarSeries
from aitrader.learning import timemachine as TM

T0 = 1_790_000_000 - (1_790_000_000 % 3600)  # an hour boundary


def bars(closes, wick=0.0002, t0=T0, opens=None):
    c = np.asarray(closes, float)
    n = len(c)
    o = np.r_[c[0], c[:-1]] if opens is None else np.asarray(opens, float)
    hi, lo = np.maximum(o, c) + wick, np.minimum(o, c) - wick
    s = 0.00001
    cols = dict(bid_open=o - s, bid_high=hi - s, bid_low=lo - s, bid_close=c - s, ask_open=o + s, ask_high=hi + s,
                ask_low=lo + s, ask_close=c + s, ticks=np.ones(n), spread_mean=np.full(n, 2 * s),
                spread_max=np.full(n, 2 * s))
    return BarSeries.from_columns("EURUSD", "H1", "test", open_time=t0 + 3600 * np.arange(n), **cols)


def symmetric(n=1500, step=0.0010, start=1.10):
    """No drift by construction: each day has as many rises as falls of the same size, and each hour of day rises on
    one day and falls on the next."""
    i = np.arange(n)
    return start + np.cumsum(np.where((i % 24 + i // 24) % 2 == 0, step, -step))


def run(b, entry, stop, target, hours=48, **kw):
    return TM.replay(b, as_of=T0 + 3600 * len(b.open_time), entry=entry, stop=stop, target=target,
                     hold_minutes=hours * 60, **kw)


def test_on_a_market_without_drift_the_levels_alone_give_their_coin_flip_odds():
    b = bars(symmetric())
    px = float(b.mid_close[-1])
    one = run(b, px, px - 0.004, px + 0.004)
    assert one["target_share_of_decided"] == pytest.approx(0.5, abs=0.03) and one["neither"] < 0.05
    two = run(b, px, px - 0.004, px + 0.008, hours=400)  # twice as far, time to decide: about one in three
    assert two["target_share_of_decided"] == pytest.approx(1 / 3, abs=0.04) and two["neither"] < 0.05
    short = run(b, px, px - 0.004, px + 0.008)  # in 48 h the far target is often not reached at all
    assert short["neither"] > 0.15 and short["target_share_of_decided"] < two["target_share_of_decided"]
    assert one["win_rate_needed"] == pytest.approx(0.5) and two["win_rate_needed"] == pytest.approx(1 / 3, abs=1e-3)
    assert one["verdict"] == "close to break-even" and one["replays"] == TM.REPLAYS and one["hours"] == 48


def test_costs_raise_the_win_rate_the_levels_need():
    b = bars(symmetric())
    px = float(b.mid_close[-1])
    res = run(b, px, px - 0.004, px + 0.004, cost=0.0004)  # costs a tenth of the risk: (1 + 0.1) / (1 + 1)
    assert res["win_rate_needed"] == pytest.approx(0.55) and res["mean_r_after_costs"] == pytest.approx(
        res["mean_r"] - 0.1, abs=1e-4)


def test_a_drift_shows_and_leans_each_side_its_own_way():
    rng = np.random.default_rng(3)
    up = 1.10 + np.cumsum(0.0004 + rng.normal(0, 0.0010, 1500))
    b = bars(up)
    px = float(b.mid_close[-1])
    buy, sell = run(b, px, px - 0.004, px + 0.004), run(b, px, px + 0.004, px - 0.004)
    assert buy["verdict"] == "strongly toward the target" and sell["verdict"] == "strongly toward the stop"
    assert buy["side"] == "BUY" and sell["side"] == "SELL" and buy["target_first"] > 0.7 > sell["target_first"]


def test_a_bar_touching_both_the_stop_and_the_target_is_a_stop():
    b = bars(symmetric(), wick=0.02)  # every hour's range swallows both levels
    px = float(b.mid_close[-1])
    res = run(b, px, px - 0.004, px + 0.004)
    assert res["stop_first"] == 1.0 and res["target_first"] == 0.0 and res["verdict"] == "strongly toward the stop"


def test_a_target_out_of_reach_in_the_time_given_is_mostly_neither():
    b = bars(symmetric())
    px = float(b.mid_close[-1])
    res = run(b, px, px - 0.004, px + 0.05, hours=3)
    assert res["neither"] > 0.9 and res["hours"] == 3


def test_nothing_after_the_decision_is_read_and_the_same_inputs_give_the_same_numbers():
    closes = symmetric()
    b = bars(closes)
    px = float(b.mid_close[-1])
    later = bars(np.r_[closes, np.linspace(closes[-1], closes[-1] + 0.5, 300)])  # a rally after the decision
    a, again = run(b, px, px - 0.004, px + 0.004), run(b, px, px - 0.004, px + 0.004)
    seen = TM.replay(later, as_of=T0 + 3600 * len(closes), entry=px, stop=px - 0.004, target=px + 0.004,
                     hold_minutes=48 * 60)
    assert a == again == seen
    other = run(b, px, px - 0.004, px + 0.004, seed=7)
    assert other != a and other["target_share_of_decided"] == pytest.approx(a["target_share_of_decided"], abs=0.03)


def test_too_little_history_or_impossible_levels_give_no_answer_never_a_guess():
    b = bars(symmetric(150))
    px = float(b.mid_close[-1])
    assert run(b, px, px - 0.004, px + 0.004) is None  # under MIN_POOL usable hours
    b = bars(symmetric())
    px = float(b.mid_close[-1])
    assert run(b, px, px + 0.004, px + 0.008) is None  # a BUY's stop above its entry
    assert run(b, px, px, px + 0.004) is None          # no risk
    res = run(b, px, px - 0.004, px + 0.004)
    assert res is not None and "a simulation of the recent past, not a forecast" in res["based_on"]


def test_a_jump_across_a_gap_is_not_an_hours_move():
    """Each day opens 0.05 above the last close after a two-day gap, a "weekend" jump. Left out, the pool is the same
    as without the jumps; counted, a third of the replays would jump straight to the target."""
    n = 1488  # ends on the last hour of a day: the replay starts at the hour the jumps fall in
    day = np.arange(n) // 24
    t = T0 + 3600 * np.arange(n) + day * 48 * 3600

    def series(jump):  # multiplicative, so every hour inside a day is the same move with or without the jumps
        c = symmetric(n) * (1 + jump) ** day
        o = np.r_[c[0], c[:-1]]
        hi, lo = np.maximum(o, c) * 1.0002, np.minimum(o, c) * 0.9998
        s = 0.00001
        return BarSeries.from_columns("EURUSD", "H1", "test", open_time=t, bid_open=o - s, bid_high=hi - s,
                                      bid_low=lo - s, bid_close=c - s, ask_open=o + s, ask_high=hi + s,
                                      ask_low=lo + s, ask_close=c + s, ticks=np.ones(n), spread_mean=np.full(n, 2 * s),
                                      spread_max=np.full(n, 2 * s)), float(c[-1])
    as_of = int(t[-1]) + 3600
    assert (as_of // 3600) % 24 == (t[0] // 3600) % 24  # the first replayed hour is the hour of the jumps

    def odds(b, px):
        return TM.replay(b, as_of=as_of, entry=px, stop=px * (1 - 0.001), target=px * (1 + 0.001),
                         hold_minutes=48 * 60)
    jumpy, flat = odds(*series(0.05)), odds(*series(0.0))
    for k in ("target_first", "stop_first", "neither"):
        assert jumpy[k] == flat[k]  # the jumps are not in the pool: the very same replays


# ── on the desk, in the analysis and in the report (dual-ai 1.16.0) ────

def test_every_agreement_carries_its_time_machine_on_trader_1s_levels_and_a_disagreement_none():
    from aitrader.agents.dual_ai import DUAL_AI_VERSION, time_machine
    from tests.unit.test_dual_ai import ASK, ATR, BID, desk_ctx, scripted, think
    d, _ = think(scripted(t1=("BUY", 80), t2=("BUY", 80)))
    tm = d.ai["dual_ai"]["time_machine"]
    assert d.decision == "BUY" and tm["side"] == "BUY" and tm["replays"] == TM.REPLAYS
    assert tm["entry"] == pytest.approx(ASK) and tm["stop"] == pytest.approx(d.stop_loss)
    assert tm["target"] == pytest.approx(d.take_profit) and tm["hours"] == d.max_hold_minutes // 60
    assert tm["verdict"] and 0.0 <= tm["target_first"] <= 1.0 and d.versions["dual_ai"] == DUAL_AI_VERSION
    assert d.versions["time_machine"] == TM.TIME_MACHINE_VERSION
    low, _ = think(scripted(t1=("SELL", 60), t2=("SELL", 70)))  # under the floor: replayed all the same, followed
    assert low.decision == "NO_TRADE" and low.ai["dual_ai"]["time_machine"]["side"] == "SELL"
    assert low.ai["dual_ai"]["time_machine"]["entry"] == pytest.approx(BID)
    apart, _ = think(scripted(t1=("SELL", 80), t2=("BUY", 80)))  # no agreed levels: nothing to replay
    assert "time_machine" not in apart.ai["dual_ai"]
    bare = desk_ctx()
    bare.bars = {}
    assert time_machine(bare, "ab12cd34ef", {"direction": "BUY", "stop_loss": ASK - ATR, "take_profit": ASK + 2 * ATR},
                        {"bid": BID, "ask": ASK, "atr": ATR}, 2880) is None  # no H1 bars: no replay, never a guess


def test_the_time_machine_draws_its_fan_and_is_a_condition_of_the_analysis():
    from aitrader.charts.canvas import decode_png_size
    from aitrader.charts.fan import H, W, render_time_machine
    from aitrader.learning.dual_ai_stats import LEVEL_KEYS, conditions
    b = bars(symmetric())
    px = float(b.mid_close[-1])
    tm = run(b, px, px - 0.004, px + 0.006)
    png = render_time_machine(tm, "EURUSD")
    assert png[:8] == b"\x89PNG\r\n\x1a\n" and decode_png_size(png) == (W, H)
    assert render_time_machine(tm, "EURUSD") == png and render_time_machine({}, "EURUSD") is None
    c = conditions({"side": 1, "symbol": "EURUSD"}, {"ai": {"dual_ai": {"time_machine": tm}}})
    assert c["time_machine"] == tm["verdict"] and "time_machine" in LEVEL_KEYS


def test_the_report_shows_each_agreements_time_machine():
    from scripts.paper_forward_shift import time_machine_cell
    b = bars(symmetric())
    px = float(b.mid_close[-1])
    tm = run(b, px, px - 0.004, px + 0.004)
    cell = time_machine_cell(tm)
    assert cell.startswith(f"T {tm['target_first']:.0%} / S {tm['stop_first']:.0%}") and tm["verdict"] in cell
    assert time_machine_cell(None) == "-"
