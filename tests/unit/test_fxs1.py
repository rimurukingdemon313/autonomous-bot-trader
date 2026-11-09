"""FXS-1 (scripts/fxs1.py) on markets built so the answer is known: the windows follow each city's own clock through
daylight saving; a trade buys at the ask and sells at the bid of the bars at its window's edges, and its cost is the
spread, slippage and commission exactly, scaled by the stress; a late or broken window is skipped, never guessed; a
later price changes nothing before it; a market that moves as the hypothesis says passes every gate, and a market
that does not fails them; nothing reads the sealed years."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import numpy as np
import pytest

import scripts.fxs1 as F
from aitrader.research.discovery import intraday as ID

PIP = {"EURUSD": 0.0001, "GBPUSD": 0.0001, "USDCHF": 0.0001, "USDJPY": 0.01}
BASE = {"EURUSD": 1.20, "GBPUSD": 1.50, "USDCHF": 0.95, "USDJPY": 100.0}


def utc(*a) -> int:
    return int(datetime(*a, tzinfo=timezone.utc).timestamp())


def market(start: date, end: date, drift_bp: float = 0.0, noise_bp: float = 0.0, spread_pips: float = 0.2,
           seed: int = 1, drop=None) -> dict:
    """M5 bars for the four pairs, Sunday 22:00 to Friday 22:00 UTC. Inside each window a pair drifts by drift_bp in
    the direction FXS-1 expects (spread evenly over the window's bars); outside it only the noise moves it."""
    rng = np.random.default_rng(seed)
    t = np.arange(utc(start.year, start.month, start.day), utc(end.year, end.month, end.day), 300, dtype=np.int64)
    wd, hr = (t // 86400 + 3) % 7, (t // 3600) % 24
    open_ = (wd < 4) | ((wd == 4) & (hr < 22)) | ((wd == 6) & (hr >= 22))
    t = t[open_]
    panel = {}
    for pair in F.PAIRS:
        step = rng.normal(0.0, noise_bp, len(t)) if noise_bp else np.zeros(len(t))
        d = start
        while d < end:
            if d.weekday() < 5:
                for w, (t0, t1) in F.window_bounds(d).items():
                    side = F.WINDOWS[w][2].get(pair)
                    if side:
                        inside = (t >= t0) & (t < t1)
                        if inside.any():
                            step[inside] += side * drift_bp / inside.sum()
            d += timedelta(days=1)
        mid = BASE[pair] * np.exp(np.cumsum(np.r_[0.0, step[:-1]]) / 1e4)  # bar i opens at the move up to bar i-1
        keep = np.ones(len(t), bool) if drop is None else ~drop(pair, t)
        hs = spread_pips * PIP[pair] / 2
        m = mid[keep]
        panel[pair] = ID.Bars(pair, PIP[pair], t[keep], m - hs, m - hs, m - hs, m - hs, m + hs, m + hs, m + hs, m + hs)
    return panel


# ── the clock ─────────────────────────────────────────────────────────────

def test_the_windows_follow_each_citys_own_clock_through_daylight_saving():
    winter = F.window_bounds(date(2015, 1, 14))
    assert winter == {"TOKYO": (utc(2015, 1, 14, 0), utc(2015, 1, 14, 8)),
                      "EUROPE": (utc(2015, 1, 14, 8), utc(2015, 1, 14, 13)),
                      "US": (utc(2015, 1, 14, 17), utc(2015, 1, 14, 21))}
    summer = F.window_bounds(date(2015, 7, 15))
    assert summer == {"TOKYO": (utc(2015, 7, 15, 0), utc(2015, 7, 15, 7)),
                      "EUROPE": (utc(2015, 7, 15, 7), utc(2015, 7, 15, 12)),
                      "US": (utc(2015, 7, 15, 16), utc(2015, 7, 15, 20))}
    # New York moved its clocks on 8 March 2015, London only on 29 March: both European edges shift by an hour alone
    gap = F.window_bounds(date(2015, 3, 10))
    assert gap["EUROPE"] == (utc(2015, 3, 10, 8), utc(2015, 3, 10, 12))
    assert gap["US"] == (utc(2015, 3, 10, 17), utc(2015, 3, 10, 20))


# ── fills and costs ───────────────────────────────────────────────────────

def test_a_trade_buys_at_the_ask_sells_at_the_bid_and_its_cost_is_the_spread_slippage_and_commission():
    p = market(date(2015, 1, 12), date(2015, 1, 17), drift_bp=10.0, spread_pips=0.4)
    trades, skipped = F.make_trades(p, (date(2015, 1, 12), date(2015, 1, 17)))
    assert skipped == 0 and len(trades) == 5 * 8  # five weekdays, eight trades a day
    eu = next(t for t in trades if t.pair == "EURUSD" and t.window == "EUROPE")
    b = p["EURUSD"]
    i0, i1 = (int(np.searchsorted(b.t, x)) for x in F.window_bounds(eu.day)["EUROPE"])
    m0, m1 = (b.bo[i0] + b.ao[i0]) / 2, (b.bo[i1] + b.ao[i1]) / 2
    assert eu.side == -1 and eu.t_in == b.t[i0] and eu.t_out == b.t[i1]
    entry, out = b.bo[i0] - 0.1 * PIP["EURUSD"], b.ao[i1] + 0.1 * PIP["EURUSD"]  # sell at the bid, buy back at the ask
    net = (entry - out) - 0.7 * PIP["EURUSD"]
    assert eu.net_bp == pytest.approx(net / m0 * 1e4)
    assert eu.gross_bp == pytest.approx((m0 - m1) / m0 * 1e4) and eu.gross_bp == pytest.approx(10.0, rel=0.02)
    assert eu.cost_bp == pytest.approx((0.4 + 0.2 + 0.7) * PIP["EURUSD"] / m0 * 1e4)
    jp = next(t for t in trades if t.pair == "USDJPY" and t.window == "TOKYO")
    assert jp.side == 1 and jp.gross_bp == pytest.approx(10.0, rel=0.02)


def test_the_stress_scales_spread_commission_and_slippage_together():
    p = market(date(2015, 1, 12), date(2015, 1, 14), drift_bp=5.0)
    one, _ = F.make_trades(p, (date(2015, 1, 12), date(2015, 1, 14)))
    two, _ = F.make_trades(p, (date(2015, 1, 12), date(2015, 1, 14)), k=2.0)
    for a, b in zip(one, two):
        assert b.cost_bp == pytest.approx(2 * a.cost_bp) and b.gross_bp == pytest.approx(a.gross_bp)


def test_a_random_side_pays_the_same_cost_and_cannot_see_the_direction():
    p = market(date(2015, 1, 12), date(2015, 1, 17), drift_bp=10.0)
    trades, _ = F.make_trades(p, (date(2015, 1, 12), date(2015, 1, 17)))
    rnd = F.random_sides(trades, 11)
    assert [t.cost_bp for t in rnd] == [t.cost_bp for t in trades]
    assert [abs(r.gross_bp) for r in rnd] == pytest.approx([abs(t.gross_bp) for t in trades])  # the same moves
    assert F.random_sides(trades, 11) == rnd and F.random_sides(trades, 12) != rnd


# ── what is skipped, and what cannot leak ─────────────────────────────────

def test_a_window_whose_edge_has_no_bar_within_ten_minutes_or_a_gap_inside_is_skipped():
    w = F.window_bounds(date(2015, 1, 13))["EUROPE"]
    late = market(date(2015, 1, 12), date(2015, 1, 15),
                  drop=lambda pair, t: (pair == "EURUSD") & (t >= w[0]) & (t < w[0] + 900))  # first bar 15 minutes late
    trades, skipped = F.make_trades(late, (date(2015, 1, 12), date(2015, 1, 15)))
    assert skipped == 1 and not any(t.pair == "EURUSD" and t.window == "EUROPE" and t.day == date(2015, 1, 13)
                                    for t in trades)
    hole = market(date(2015, 1, 12), date(2015, 1, 15),
                  drop=lambda pair, t: (pair == "GBPUSD") & (t >= w[0] + 3600) & (t < w[0] + 3 * 3600))
    trades, skipped = F.make_trades(hole, (date(2015, 1, 12), date(2015, 1, 15)))
    assert skipped == 1 and not any(t.pair == "GBPUSD" and t.window == "EUROPE" and t.day == date(2015, 1, 13)
                                    for t in trades)


def test_one_bar_late_enters_and_exits_five_minutes_after_the_edges():
    p = market(date(2015, 1, 12), date(2015, 1, 14), drift_bp=5.0)
    trades, _ = F.make_trades(p, (date(2015, 1, 12), date(2015, 1, 14)), delay=1)
    for t in trades:
        t0, t1 = F.window_bounds(t.day)[t.window]
        assert t.t_in == t0 + 300 and t.t_out == t1 + 300


def test_a_later_price_changes_nothing_before_it():
    span = (date(2015, 1, 12), date(2015, 1, 17))
    p = market(*span, drift_bp=4.0, noise_bp=1.0)
    cut = F.window_bounds(date(2015, 1, 14))["US"][1]
    q = {}
    for k, b in p.items():
        later = b.t > cut
        q[k] = ID.Bars(k, b.pip, b.t, *(np.where(later, x * 1.05, x) for x in (b.bo, b.bh, b.bl, b.bc, b.ao, b.ah,
                                                                               b.al, b.ac)))
    before = [t for t in F.make_trades(p, span)[0] if t.t_out <= cut]
    after = [t for t in F.make_trades(q, span)[0] if t.t_out <= cut]
    assert before == after and len(before) == 3 * 8


# ── the gates ─────────────────────────────────────────────────────────────

@pytest.fixture
def short_program(monkeypatch):
    """Three years, so a steady market can keep every year under half the total (two years could not)."""
    monkeypatch.setattr(F, "PERIOD", (date(2010, 1, 1), date(2013, 1, 1)))
    monkeypatch.setattr(F, "DEV", (date(2010, 1, 1), date(2012, 1, 1)))
    monkeypatch.setattr(F, "VAL", (date(2012, 1, 1), date(2013, 1, 1)))
    monkeypatch.setattr(F, "BOOT_N", 300)


def test_a_market_that_moves_as_hypothesised_passes_every_gate(short_program):
    p = market(date(2009, 12, 28), date(2013, 1, 3), drift_bp=6.0, noise_bp=0.5)
    res = F.evaluate(p, 3.6)
    assert res["passed"], res["failed_gates"]
    assert res["all"]["per_trade"]["gross_bp"] == pytest.approx(6.0, rel=0.1)
    assert res["random_sides"]["net_bp"] < 0 < res["all"]["per_trade"]["net_bp"]
    assert res["pairs_positive"] == 4 and res["bootstrap_95"][0] > 0


def test_a_market_without_the_pattern_fails(short_program):
    p = market(date(2009, 12, 28), date(2013, 1, 3), drift_bp=0.0, noise_bp=1.0, seed=3)
    res = F.evaluate(p, 3.6)
    assert not res["passed"]
    assert {"t", "beats_random", "bootstrap"} <= set(res["failed_gates"])
    assert res["all"]["per_trade"]["net_bp"] < 0


def test_the_judged_years_end_where_the_seal_begins():
    assert F.PERIOD[1] == F.HOLD[0] == date(2017, 1, 1)
    assert F.DEV[0] == F.PERIOD[0] and F.DEV[1] == F.VAL[0] and F.VAL[1] == F.PERIOD[1]
