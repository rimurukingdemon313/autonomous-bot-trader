"""CR-3 cross-sectional carry (aitrader/research/crypto/xs.py) on synthetic universes with known answers."""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pytest

from aitrader.research.crypto import cr as C
from aitrader.research.crypto import xs as X

T0 = int(datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp())
H, D = 3600, 86400


def coin(sym, rate, days=120, start_d=0, end_d=None, seed=0, sd=0.004):
    rng = np.random.default_rng(seed)
    end_d = days if end_d is None else end_d
    n = (end_d - start_d) * 24
    t = T0 + start_d * D + np.arange(n) * H
    px = 100 * np.exp(np.cumsum(rng.normal(0, sd, n)))
    ft = T0 + start_d * D + np.arange((end_d - start_d) * 3) * 8 * H
    fr = rate(np.arange(len(ft))) if callable(rate) else np.full(len(ft), rate)
    return C.Coin(sym, t, px, t.copy(), px.copy(), ft, fr)


def test_the_book_holds_the_coins_paying_the_most_funding():
    coins = {f"C{i}USDT": coin(f"C{i}USDT", 0.0001 * i, seed=i) for i in range(1, 7)}
    pos = X.run_book(coins, slots=2, theta_in=0.0003, theta_out=0.0, seasoning_d=30, costs=X.XsCosts(),
                     start=T0 + 40 * D, end=T0 + 100 * D)
    assert {p.symbol for p in pos} == {"C6USDT", "C5USDT"}


def test_a_new_coin_is_ineligible_until_seasoned_and_a_delisted_coin_is_closed_at_its_last_bar():
    coins = {"OLDUSDT": coin("OLDUSDT", 0.0001, seed=1), "NEWUSDT": coin("NEWUSDT", 0.001, start_d=50, seed=2),
             "GONEUSDT": coin("GONEUSDT", 0.0009, end_d=70, seed=3)}
    pos = X.run_book(coins, slots=1, theta_in=0.0001, theta_out=0.0, seasoning_d=30, costs=X.XsCosts(),
                     start=T0 + 40 * D, end=T0 + 115 * D)
    gone = [p for p in pos if p.symbol == "GONEUSDT"]
    assert gone and gone[0].reason == "data_end" and gone[0].exit_t <= T0 + 70 * D
    new = coins["NEWUSDT"]
    assert not X.eligible(new, T0 + 79 * D, 30) and X.eligible(new, T0 + 80 * D, 30)  # listed day 50 + 30 days
    alone = X.run_book({"NEWUSDT": new}, 1, 0.0001, 0.0, 30, X.XsCosts(), T0 + 40 * D, T0 + 115 * D)
    assert alone and min(p.entry_t for p in alone) == T0 + 80 * D + H


def test_decisions_use_only_the_past():
    rng = np.random.default_rng(9)
    rates = {i: rng.normal(0.0001 * i / 3, 0.0003, 400) for i in range(1, 6)}
    coins = {f"C{i}USDT": coin(f"C{i}USDT", lambda k, i=i: rates[i][k], seed=i) for i in range(1, 6)}
    kw = dict(slots=2, theta_in=0.0003, theta_out=0.0, seasoning_d=30, costs=X.XsCosts(), start=T0 + 35 * D,
              end=T0 + 110 * D)
    full = X.run_book(coins, **kw)
    for cut in (T0 + 60 * D + 9 * H, T0 + 90 * D + 17 * H):
        part = X.run_book({s: c.truncated(cut + 3 * H) for s, c in coins.items()}, **kw)
        done = sorted((p for p in full if p.exit_t <= cut), key=lambda p: (p.entry_t, p.symbol))
        assert sorted((p for p in part if p.exit_t <= cut), key=lambda p: (p.entry_t, p.symbol)) == done


def test_the_book_ledger_adds_up():
    rng = np.random.default_rng(4)
    coins = {f"C{i}USDT": coin(f"C{i}USDT", lambda k, i=i: rng.normal(0.0002, 0.0003, len(k)), seed=i)
             for i in range(1, 5)}
    a, b = T0 + 35 * D, T0 + 110 * D
    pos = X.run_book(coins, 2, 0.0003, 0.0, 30, X.XsCosts(), a, b)
    daily = X.book_daily(coins, pos, 2, a, b + 3 * D)
    assert sum(daily.values()) == pytest.approx(sum(p.net_bp for p in pos) / 1e4 / (2 * 2), abs=1e-9)


def test_costs_by_tier_and_stress():
    c = X.XsCosts()
    assert c.rt_bp("BTCUSDT") == pytest.approx(2 * (10 + 1 + 1) + 2 * (5 + 1 + 1))
    assert c.rt_bp("ADAUSDT") == pytest.approx(2 * (10 + 2 + 1) + 2 * (5 + 2 + 1))
    assert c.rt_bp("PEPEUSDT") == pytest.approx(2 * (10 + 5 + 3) + 2 * (5 + 5 + 3))
    assert c.stressed(2).rt_bp("PEPEUSDT") == pytest.approx(2 * c.rt_bp("PEPEUSDT"))


def test_the_placebo_picks_other_coins_at_the_same_times():
    coins = {f"C{i}USDT": coin(f"C{i}USDT", 0.0001 * i, seed=i) for i in range(1, 9)}
    kw = dict(slots=2, theta_in=0.0003, theta_out=0.0, seasoning_d=30, costs=X.XsCosts(), start=T0 + 40 * D,
              end=T0 + 100 * D)
    real = X.run_book(coins, **kw)
    pl = X.run_book(coins, rng=np.random.default_rng(1), **kw)
    assert {p.symbol for p in pl} != {p.symbol for p in real}
    assert min(p.entry_t for p in pl) == min(p.entry_t for p in real)


def test_mean_zero_funding_gives_no_gross_edge():
    gross = []
    for seed in range(12):
        rng = np.random.default_rng(200 + seed)
        coins = {f"C{i}USDT": coin(f"C{i}USDT", lambda k: rng.normal(0, 0.0003, len(k)), seed=seed * 10 + i)
                 for i in range(1, 7)}
        gross += [p.gross_bp for p in X.run_book(coins, 2, 0.0003, 0.0, 30, X.XsCosts(), T0 + 35 * D, T0 + 115 * D)]
    g = np.array(gross)
    assert len(g) > 100
    assert abs(g.mean() / (g.std(ddof=1) / np.sqrt(len(g)))) < 2.5
