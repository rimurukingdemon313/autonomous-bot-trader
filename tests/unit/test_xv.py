"""CR-4 cross-venue funding differential (aitrader/research/crypto/xv.py) on synthetic pairs with known answers."""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pytest

from aitrader.research.crypto import xv as X

T0 = int(datetime(2023, 6, 1, tzinfo=timezone.utc).timestamp())
D, H = 86400, 3600


def pair(coin, hl_rate, bn_rate, days=120, seed=0, basis_sd=0.0, start_d=0):
    rng = np.random.default_rng(seed)
    t = T0 + start_d * D + np.arange(days - start_d) * D
    px = 100 * np.exp(np.cumsum(rng.normal(0, 0.03, len(t))))
    hl = px * (1 + rng.normal(0, basis_sd, len(t)))
    hft = T0 + start_d * D + np.arange((days - start_d) * 24) * H
    bft = T0 + start_d * D + np.arange((days - start_d) * 3) * 8 * H
    hfr = hl_rate(np.arange(len(hft))) if callable(hl_rate) else np.full(len(hft), hl_rate)
    bfr = bn_rate(np.arange(len(bft))) if callable(bn_rate) else np.full(len(bft), bn_rate)
    return X.Pair(coin, t, hl, t.copy(), px.copy(), hft, hfr, bft, bfr)


def test_diff_is_the_daily_funding_gap():
    p = pair("ABC", 0.0002 / 8, 0.0001)  # HL pays 2 bp per 8 h-equivalent, BN 1 bp per 8 h
    assert X.diff(p, T0 + 40 * D, 7) == pytest.approx((0.0002 * 3) - (0.0001 * 3))


def test_the_book_shorts_the_higher_paying_venue_and_collects_the_gap():
    p = pair("ABC", 0.0004 / 8, 0.0001)
    pos = X.run_book({"ABC": p}, 1, 0.0003, 0.0001, 7, 30, X.XvCosts(), T0 + 35 * D, T0 + 100 * D)
    (q,) = pos
    assert q.side == 1 and q.entry_t == T0 + 36 * D
    days = (q.exit_t - q.entry_t) / D
    assert q.funding_bp == pytest.approx((0.0004 * 3 - 0.0001 * 3) * 1e4 * days, rel=0.02)
    assert abs(q.basis_bp) < 1e-9  # identical prices: no basis


def test_the_sign_flips_the_side_and_reversal_closes():
    hl = lambda i: np.where(i < 60 * 24, 0.00005, 0.0)  # noqa: E731 - HL rich, then cheap
    bn = lambda i: np.where(i < 60 * 3, 0.0, 0.0002)  # noqa: E731
    p = pair("ABC", hl, bn)
    pos = X.run_book({"ABC": p}, 1, 0.0003, 0.0001, 3, 30, X.XvCosts(), T0 + 35 * D, T0 + 110 * D)
    assert pos[0].side == 1 and pos[0].reason == "signal" and pos[1].side == -1


def test_decisions_use_only_the_past():
    rng = np.random.default_rng(3)
    hr, br = rng.normal(0.00002, 0.00004, 120 * 24), rng.normal(0.0001, 0.0002, 360)
    pairs = {c: pair(c, lambda i, s=s: hr[i] * s, lambda i: br[i], seed=k, basis_sd=0.001)
             for k, (c, s) in enumerate((("A", 1.0), ("B", 2.0), ("C", 0.5)))}
    kw = dict(slots=2, theta_in=0.0002, theta_out=0.00005, lookback_d=5, seasoning_d=30, costs=X.XvCosts(),
              start=T0 + 35 * D, end=T0 + 115 * D)
    full = X.run_book(pairs, **kw)
    for cut in (T0 + 60 * D, T0 + 90 * D):
        part = X.run_book({c: p.truncated(cut + 2 * D) for c, p in pairs.items()}, **kw)
        key = lambda q: (q.entry_t, q.coin)  # noqa: E731
        assert sorted((q for q in part if q.exit_t <= cut), key=key) == sorted((q for q in full if q.exit_t <= cut),
                                                                             key=key)


def test_the_ledger_adds_up():
    rng = np.random.default_rng(4)
    pairs = {c: pair(c, lambda i: rng.normal(0.00003, 0.00003, len(i)), 0.0001, seed=k, basis_sd=0.002)
             for k, c in enumerate("ABCD")}
    a, b = T0 + 35 * D, T0 + 110 * D
    pos = X.run_book(pairs, 2, 0.0002, 0.00005, 5, 30, X.XvCosts(), a, b)
    daily = X.daily_returns(pairs, pos, 2, a, b + 5 * D)
    assert sum(daily.values()) == pytest.approx(sum(q.net_bp for q in pos) / 1e4 / 4, abs=1e-9)


def test_missing_funding_is_not_read_as_zero():
    p = pair("ABC", 0.0001, 0.0001)
    gap = X.Pair("ABC", p.hl_t, p.hl_o, p.bn_t, p.bn_o, p.hl_ft[(p.hl_ft <= T0 + 39 * D) | (p.hl_ft > T0 + 39 * D + 6 * H)],
                 p.hl_fr[(p.hl_ft <= T0 + 39 * D) | (p.hl_ft > T0 + 39 * D + 6 * H)], p.bn_ft, p.bn_fr)
    assert X.diff(gap, T0 + 42 * D, 7) is None  # day 39 lost 6 of its 24 hourly settlements


def test_no_edge_without_a_funding_gap():
    gross = []
    for seed in range(15):
        rng = np.random.default_rng(300 + seed)
        pairs = {c: pair(c, lambda i: rng.normal(0.0001 / 8, 0.00004, len(i)), lambda i: rng.normal(0.0001, 0.0003, len(i)),
                         seed=seed * 10 + k, basis_sd=0.002) for k, c in enumerate("ABCDEF")}
        gross += [q.gross_bp for q in X.run_book(pairs, 3, 0.0002, 0.00005, 5, 30, X.XvCosts(), T0 + 35 * D,
                                                 T0 + 115 * D)]
    g = np.array(gross)
    assert len(g) > 60
    assert abs(g.mean() / (g.std(ddof=1) / np.sqrt(len(g)))) < 2.5


def test_costs_and_stress():
    c = X.XvCosts()
    assert c.rt_bp("BTC") == pytest.approx(2 * (4.5 + 1 + 1) + 2 * (5 + 1 + 1))
    assert c.rt_bp("WIF") == pytest.approx(2 * (4.5 + 3 + 2) + 2 * (5 + 3 + 2))
    assert c.stressed(1.5).rt_bp("WIF") == pytest.approx(1.5 * c.rt_bp("WIF"))
