"""The canonical bid/ask engine (aitrader/research/canon): every fill rule on bars built so the right answer is
known, the cost ledger's identity, financing, stress, and the placebo property: on a driftless random walk no
entry/exit combination may show a gross edge."""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pytest

from aitrader.research.canon import engine as E
from aitrader.research.canon import validate as V

H = 3600
T0 = int(datetime(2015, 3, 2, 14, tzinfo=timezone.utc).timestamp())  # Monday 09:00 New York (EST)


def bars(mids, spread=0.2, hl=None, t0=T0, period=H, one_sided=()):
    """Bars whose mid opens at mids[i] and closes at mids[i+1]; high/low default to the open/close range
    unless `hl` gives (high, low) per bar."""
    mids = np.asarray(mids, float)
    o, c = mids[:-1], mids[1:]
    h = np.maximum(o, c) if hl is None else np.array([x[0] for x in hl], float)
    lo = np.minimum(o, c) if hl is None else np.array([x[1] for x in hl], float)
    n = len(o)
    hs = np.full(n, spread / 2)
    for i in one_sided:
        hs[i] = 0.0
    t = t0 + np.arange(n) * period
    return E.Quotes("X", period, t, o - hs, h - hs, lo - hs, c - hs, o + hs, h + hs, lo + hs, c + hs)


def ohlc(rows, spread=0.2, t0=T0, period=H):
    """Bars from explicit mid (open, high, low, close) rows, so gaps between bars can be built."""
    o, h, lo, c = (np.array([r[k] for r in rows], float) for k in range(4))
    hs = spread / 2
    t = t0 + np.arange(len(rows)) * period
    return E.Quotes("X", period, t, o - hs, h - hs, lo - hs, c - hs, o + hs, h + hs, lo + hs, c + hs)


def test_a_long_buys_at_the_ask_and_sells_at_the_bid_and_the_ledger_adds_up():
    q = bars([100, 101, 102, 103, 104], spread=0.2)
    run = E.simulate(q, [E.Order(0, 1, max_bars=2)], E.Costs(slip_frac=0.0))
    (x,) = run.trades
    assert x.entry_px == pytest.approx(101.1) and x.exit_px == pytest.approx(102.9)  # ask in, bid out
    assert x.gross_bp == pytest.approx(2 / 101 * 1e4)  # the mid moved 101 -> 103
    assert x.spread_bp == pytest.approx(0.2 / 101 * 1e4)  # half spread each side
    assert x.net_bp == pytest.approx((102.9 - 101.1) / 101 * 1e4)


def test_a_short_sells_at_the_bid_and_slippage_is_a_fraction_of_the_bars_spread():
    q = bars([100, 99, 98, 97], spread=0.4)
    (x,) = E.simulate(q, [E.Order(0, -1, max_bars=1)], E.Costs(slip_frac=0.25)).trades
    assert x.entry_px == pytest.approx(99 - 0.2 - 0.1)
    assert x.exit_px == pytest.approx(98 + 0.2 + 0.1)
    assert x.slip_bp == pytest.approx(0.2 / 99 * 1e4)


def test_a_stop_fills_through_its_level_and_a_gap_fills_at_the_open():
    # bar 1 (entry) trades down to 99.4: the long's stop at 100.1 - 0.5 = 99.6 (bid side) triggers inside the bar
    q = bars([100, 100, 99.8, 99.9], spread=0.2, hl=[(100, 100), (100.1, 99.4), (100, 99.7)])
    (x,) = E.simulate(q, [E.Order(0, 1, stop_bp=0.5 / 100 * 1e4)], E.Costs(slip_frac=0.0)).trades
    stop = 100.1 - 0.5
    assert x.reason == "stop" and x.exit_px == pytest.approx(stop - 0.5 * 0.2)  # half a spread through
    assert x.through_bp == pytest.approx(0.1 / 100 * 1e4)
    # a gap: bar 2 opens at 98, far below the stop: the fill is the open's bid, not the level
    q2 = ohlc([(100, 100, 100, 100), (100, 100.05, 99.95, 100), (98, 98.6, 97.9, 98.5), (98.5, 98.5, 98.5, 98.5)])
    (y,) = E.simulate(q2, [E.Order(0, 1, stop_bp=0.5 / 100 * 1e4)], E.Costs(slip_frac=0.0)).trades
    assert y.reason == "stop" and y.exit_px == pytest.approx(98 - 0.1) and y.through_bp == 0.0


def test_a_target_fills_at_its_level_never_better_even_on_a_gap():
    q = ohlc([(100, 100, 100, 100), (100, 100.05, 99.95, 100), (105, 106, 104.9, 105.5), (105.5, 105.5, 105.5, 105.5)])
    (x,) = E.simulate(q, [E.Order(0, 1, target_bp=1.0 / 100 * 1e4)], E.Costs(slip_frac=0.0)).trades
    assert x.reason == "target" and x.exit_px == pytest.approx(100.1 + 1.0)


def test_a_bar_that_reaches_both_stop_and_target_is_a_stop():
    q = bars([100, 100, 100], spread=0.2, hl=[(100, 100), (103, 97)])
    (x,) = E.simulate(q, [E.Order(0, 1, stop_bp=100, target_bp=100)], E.Costs(slip_frac=0.0)).trades
    assert x.reason == "stop"


def test_latency_enters_whole_bars_later():
    q = bars(np.arange(100, 110, 1.0))
    a = E.simulate(q, [E.Order(0, 1, max_bars=2)]).trades[0]
    b = E.simulate(q, [E.Order(0, 1, max_bars=2)], E.Costs(latency_bars=2)).trades[0]
    assert b.entry_t - a.entry_t == 2 * H


def test_a_one_sided_bar_is_never_a_fill_price():
    q = bars([100, 100, 101, 102, 103], spread=0.2, one_sided=(1,))
    (x,) = E.simulate(q, [E.Order(0, 1, max_bars=2)], E.Costs(slip_frac=0.0)).trades
    assert x.entry_t == q.t[2] and x.entry_px == pytest.approx(101.1)


def test_a_one_sided_bar_still_triggers_a_stop_priced_with_a_real_spread():
    q = bars([100, 100, 100, 100], spread=0.2, hl=[(100, 100), (100, 100), (100, 98)], one_sided=(2,))
    (x,) = E.simulate(q, [E.Order(0, 1, stop_bp=50)], E.Costs(slip_frac=0.0)).trades
    assert x.reason == "stop" and x.spread_bp > 0


def test_doubling_costs_doubles_spread_slippage_and_markup():
    q = bars(np.linspace(100, 101, 30), t0=T0)
    rate = lambda t: 1.0  # noqa: E731
    o = [E.Order(0, 1, max_bars=26)]
    a = E.simulate(q, o, E.Costs(), rate).trades[0]
    b = E.simulate(q, o, E.Costs().stressed(2.0), rate).trades[0]
    assert b.spread_bp == pytest.approx(2 * a.spread_bp) and b.slip_bp == pytest.approx(2 * a.slip_bp)
    assert b.gross_bp == pytest.approx(a.gross_bp)
    assert b.fin_bp > a.fin_bp


def test_financing_counts_each_rollover_and_three_days_on_friday():
    fri = int(datetime(2015, 3, 6, 20, tzinfo=timezone.utc).timestamp())  # Friday 15:00 New York
    q = bars(np.full(80, 100.0), t0=fri)  # through Monday
    rate = lambda t: 2.0  # noqa: E731
    (x,) = E.simulate(q, [E.Order(0, 1, max_bars=70)], E.Costs(markup_pa=2.5), rate).trades
    assert x.days_financed == 3  # Friday 17:00 only (no rollover yet on Monday before 17:00 is crossed)
    assert x.fin_bp == pytest.approx((2.0 + 2.5) * 3 / 360 * 100)
    (y,) = E.simulate(q, [E.Order(0, -1, max_bars=70)], E.Costs(markup_pa=2.5), rate).trades
    assert y.fin_bp == pytest.approx((-2.0 + 2.5) * 3 / 360 * 100)  # a short receives the rate, pays the markup


def test_an_unknown_rate_skips_the_trade_rather_than_assuming_one():
    q = bars(np.full(40, 100.0))
    run = E.simulate(q, [E.Order(0, 1, max_bars=30)], E.Costs(), rate=lambda t: float("nan"))
    assert not run.trades and run.skipped["no_rate"] == 1
    run = E.simulate(q, [E.Order(0, 1, max_bars=30)], E.Costs(), rate=None)
    assert not run.trades and run.skipped["no_rate"] == 1


def test_an_intraday_trade_needs_no_rate():
    q = bars(np.full(5, 100.0))
    assert len(E.simulate(q, [E.Order(0, 1, max_bars=2)]).trades) == 1


def test_a_second_order_while_a_position_is_open_is_refused():
    q = bars(np.full(12, 100.0))
    run = E.simulate(q, [E.Order(0, 1, max_bars=5), E.Order(2, 1, max_bars=2)])
    assert len(run.trades) == 1 and run.skipped["busy"] == 1


def test_a_time_exit_uses_the_first_valid_open_at_or_after_the_time():
    q = bars(np.arange(100, 110, 1.0))
    (x,) = E.simulate(q, [E.Order(0, 1, exit_at=int(q.t[4]) - 60)]).trades
    assert x.exit_t == q.t[4] and x.reason == "time"


def _random_walk(n_bars: int, sub: int, sd_sub: float, spread: float, seed: int) -> E.Quotes:
    """Bars aggregated from a fine driftless path: high/low are the true extremes of the path inside the
    bar, so a stop or target is triggered exactly when the path crossed it."""
    rng = np.random.default_rng(seed)
    path = 1000.0 + np.cumsum(rng.normal(0, sd_sub, n_bars * sub + 1))
    seg = path[:-1].reshape(n_bars, sub)
    o, c = seg[:, 0], path[sub::sub]
    h, lo = np.maximum(seg.max(1), c), np.minimum(seg.min(1), c)
    hs = spread / 2
    t = T0 + np.arange(n_bars) * 300
    return E.Quotes("RW", 300, t, o - hs, h - hs, lo - hs, c - hs, o + hs, h + hs, lo + hs, c + hs)


@pytest.mark.parametrize("exit_kind", ["time", "stop_only", "stop_target_1_1", "stop_target_1_2", "target_only"])
def test_no_exit_shows_a_gross_edge_on_a_driftless_random_walk(exit_kind):
    """The placebo property. Ticks are finer than the spread (as in an index CFD: a 0.25-point tick against
    a ~0.5-point spread), each bar holds 64 path steps, and 4,000 random entries in random directions are
    taken. No exit rule may show a gross edge (t < 2.5), and the net must be below zero (costs are real)."""
    q = _random_walk(n_bars=250_000, sub=64, sd_sub=0.05, spread=0.4, seed=11)
    rng = np.random.default_rng(5)
    idx = np.sort(rng.choice(np.arange(10, 249_000, 50), 4000, replace=False))
    sides = rng.choice([-1, 1], len(idx))
    sd_bar = 0.05 * 8  # one bar's standard deviation
    stop_bp = 3 * sd_bar / 1000 * 1e4
    kw = {"time": dict(max_bars=6), "stop_only": dict(stop_bp=stop_bp, max_bars=40),
          "stop_target_1_1": dict(stop_bp=stop_bp, target_bp=stop_bp, max_bars=40),
          "stop_target_1_2": dict(stop_bp=stop_bp, target_bp=2 * stop_bp, max_bars=40),
          "target_only": dict(target_bp=stop_bp, max_bars=40)}[exit_kind]
    orders = [E.Order(int(i), int(s), **kw) for i, s in zip(idx, sides)]
    trades = E.simulate(q, orders, E.Costs()).trades
    assert len(trades) > 3000
    g = np.array([x.gross_bp for x in trades])
    t = g.mean() / (g.std(ddof=1) / np.sqrt(len(g)))
    assert t < 2.5, (exit_kind, g.mean(), t)
    assert np.mean([x.net_bp for x in trades]) < 0


def test_filling_stops_at_their_level_is_caught_as_a_manufactured_edge():
    """The detector works: with coarse path steps (gaps bigger than the spread) and the through-fill switched
    off, a stop-only rule on a random walk shows a positive gross bias, which is exactly the bug class the
    placebo test exists to catch."""
    q = _random_walk(n_bars=200_000, sub=4, sd_sub=0.6, spread=0.2, seed=3)
    rng = np.random.default_rng(1)
    idx = np.sort(rng.choice(np.arange(10, 199_000, 40), 4000, replace=False))
    orders = [E.Order(int(i), int(s), stop_bp=8.0, max_bars=30) for i, s in zip(idx, rng.choice([-1, 1], len(idx)))]
    lenient = E.simulate(q, orders, E.Costs(stop_through_frac=0.0, slip_frac=0.0)).trades
    g = np.array([x.gross_bp for x in lenient])
    assert g.mean() / (g.std(ddof=1) / np.sqrt(len(g))) > 2.0


def test_the_engine_never_reads_bars_after_the_exit():
    q = bars(np.arange(100, 130, 1.0))
    a = E.simulate(q, [E.Order(0, 1, max_bars=3)]).trades[0]
    b = E.simulate(q.truncated(5), [E.Order(0, 1, max_bars=3)]).trades[0]
    assert a == b


# ── validation battery ────────────────────────────────────────────────────

def _t(net, day, side=1):
    t = T0 + day * 86400
    return E.Trade("X", "", side, t, t, t + 3600, "time", 100.0, 100.0, 100.0, net, 0.0, 0.0, 0.0, 0.0, 0.0, 0, None)


def test_summary_reports_every_cost_component_and_labels_small_samples():
    s = V.summary([_t(1.0, d) for d in range(10)])
    for k in ("gross_bp", "spread_bp", "slip_bp", "through_bp", "comm_bp", "fin_bp", "net_bp", "t_day",
              "max_drawdown_bp_daybook", "net_bp_without_top_5", "exposure", "trades_per_month"):
        assert k in s
    assert s["sample"] == "insufficient"


def test_the_daily_book_counts_same_day_trades_once():
    days, book = V.daily_book([_t(2.0, 0), _t(4.0, 0), _t(1.0, 1)])
    assert len(days) == 2 and list(book) == [3.0, 1.0]


def test_permutation_finds_a_planted_direction_effect_and_not_noise():
    rng = np.random.default_rng(0)
    move = rng.normal(0, 10, 600)
    good = [_t(abs(m) + 0.0 if True else 0, i, side=int(np.sign(m) or 1)) for i, m in enumerate(move)]
    # gross is the signed move: the side always matches the move
    good = [E.Trade("X", "", x.side, x.decided_t, x.entry_t, x.exit_t, "time", 100, 100, 100, abs(m), 0, 0, 0, 0, 0,
                    0, None) for x, m in zip(good, move)]
    assert V.permutation_sides(good, n=500, seed=1)["p"] < 0.01
    noise_sides = rng.choice([-1, 1], len(move))
    noise = [E.Trade("X", "", int(s), 0, T0 + i * 86400, T0 + i * 86400 + 1, "time", 100, 100, 100, s * m, 0, 0, 0, 0,
                     0, 0, None) for i, (s, m) in enumerate(zip(noise_sides, move))]
    assert V.permutation_sides(noise, n=500, seed=1)["p"] > 0.05


def test_monte_carlo_is_deterministic_for_a_seed():
    tr = [_t(float(v), i) for i, v in enumerate(np.random.default_rng(2).normal(0.5, 5, 300))]
    assert V.monte_carlo(tr, n=300, seed=4) == V.monte_carlo(tr, n=300, seed=4)


def test_removing_the_best_trades_exposes_a_result_carried_by_a_few():
    tr = [_t(-1.0, i) for i in range(200)] + [_t(500.0, 300 + i) for i in range(3)]
    s = V.summary(tr)
    assert s["net_bp"] > 0 and s["net_bp_without_top_5"] < 0
