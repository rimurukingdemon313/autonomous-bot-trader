"""CR-1 carry and CR-2 momentum (aitrader/research/crypto/cr.py) on synthetic coins whose answer is known."""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pytest

from aitrader.research.crypto import cr as C

T0 = int(datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp())
H, D = 3600, 86400


def coin(days=60, spot=None, perp=None, rates=None, symbol="ADAUSDT", seed=0):
    n = days * 24
    t = T0 + np.arange(n) * H
    s = np.full(n, 100.0) if spot is None else spot(np.arange(n))
    p = s.copy() if perp is None else perp(np.arange(n))
    ft = T0 + np.arange(days * 3) * 8 * H
    fr = np.full(len(ft), 0.0001) if rates is None else rates(np.arange(len(ft)))
    return C.Coin(symbol, t, s, t.copy(), p, ft, fr)


def test_carry_collects_the_funding_and_pays_the_declared_costs():
    c = coin(rates=lambda i: np.full(len(i), 0.0002))
    pos, _ = C.carry_positions(c, theta_in=0.0001, theta_out=0.0, k=1, costs=C.CrCosts(), start=T0, end=T0 + 30 * D)
    (p,) = pos
    assert p.reason == "end" and p.entry_t == T0 + H  # decided at the first settlement, filled an hour later
    n_settle = int(((c.fund_t > p.entry_t) & (c.fund_t < p.exit_t)).sum())
    assert p.funding_bp == pytest.approx(2.0 * n_settle)
    assert p.basis_bp == pytest.approx(0.0)
    assert p.cost_bp == pytest.approx(2 * (10 + 2 + 1) + 2 * (5 + 2 + 1))


def test_carry_is_delta_neutral_when_spot_and_perp_move_together():
    c = coin(spot=lambda i: 100 * 1.001 ** i, rates=lambda i: np.full(len(i), 0.0002))
    (p,) = C.carry_positions(c, 0.0001, 0.0, 1, C.CrCosts(), T0, T0 + 20 * D)[0]
    assert abs(p.basis_bp) < 1e-6


def test_carry_exits_when_funding_turns_negative_and_basis_is_measured():
    rates = lambda i: np.where(i < 30, 0.0003, -0.0002)  # noqa: E731
    perp = lambda i: 100 * (1 + 0.002 * (i > 200))  # noqa: E731 - the perpetual rises 0.2% vs spot
    c = coin(perp=perp, rates=rates)
    pos, _ = C.carry_positions(c, 0.0001, 0.0, 1, C.CrCosts(), T0, T0 + 40 * D)
    assert pos[0].reason == "signal" and pos[0].exit_t == int(c.fund_t[30]) + H
    assert pos[0].basis_bp == pytest.approx(-20.0)  # short perp loses when the perpetual richens


def test_higher_threshold_trades_less():
    rng = np.random.default_rng(1)
    rates = rng.normal(0.0001, 0.0002, 180)
    c = coin(rates=lambda i: rates[i])
    a = C.carry_positions(c, 0.00005, 0.0, 3, C.CrCosts(), T0, T0 + 60 * D)[0]
    b = C.carry_positions(c, 0.0003, 0.0, 3, C.CrCosts(), T0, T0 + 60 * D)[0]
    assert sum(p.exit_t - p.entry_t for p in b) < sum(p.exit_t - p.entry_t for p in a)


def test_carry_decisions_use_only_the_past():
    rng = np.random.default_rng(2)
    rates = rng.normal(0.00005, 0.0002, 180)
    c = coin(spot=lambda i: 100 * np.exp(np.cumsum(rng.normal(0, 0.003, len(i)))), rates=lambda i: rates[i])
    full = C.carry_positions(c, 0.0001, 0.0, 3, C.CrCosts(), T0, T0 + 60 * D)[0]
    for cut in (T0 + 10 * D, T0 + 25 * D + 5 * H, T0 + 41 * D):
        part = C.carry_positions(c.truncated(cut + 4 * H), 0.0001, 0.0, 3, C.CrCosts(), T0, T0 + 60 * D)[0]
        done = [p for p in full if p.exit_t <= cut]
        assert [p for p in part if p.exit_t <= cut] == done


def test_momentum_goes_with_the_trend_and_pays_funding_when_long():
    c = coin(days=90, spot=lambda i: 100 * 1.0005 ** i, rates=lambda i: np.full(len(i), 0.0001))
    pos, _ = C.momentum_positions(c, 28, C.CrCosts(), T0 + 30 * D, T0 + 80 * D)
    (p,) = pos
    assert p.side == 1 and p.basis_bp > 0 and p.funding_bp < 0
    c2 = coin(days=90, spot=lambda i: 100 * 0.9995 ** i, rates=lambda i: np.full(len(i), 0.0001))
    (q,) = C.momentum_positions(c2, 28, C.CrCosts(), T0 + 30 * D, T0 + 80 * D)[0]
    assert q.side == -1 and q.basis_bp > 0 and q.funding_bp > 0  # a short receives positive funding


def test_momentum_decisions_use_only_the_past():
    rng = np.random.default_rng(3)
    path = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 120 * 24)))
    c = coin(days=120, spot=lambda i: path[i])
    full = C.momentum_positions(c, 14, C.CrCosts(), T0 + 20 * D, T0 + 110 * D)[0]
    for cut in (T0 + 50 * D + 3 * H, T0 + 90 * D):
        part = C.momentum_positions(c.truncated(cut + 4 * H), 14, C.CrCosts(), T0 + 20 * D, T0 + 110 * D)[0]
        assert [p for p in part if p.exit_t <= cut] == [p for p in full if p.exit_t <= cut]


@pytest.mark.parametrize("kind", ["carry", "momentum"])
def test_the_daily_ledger_adds_up_to_the_positions(kind):
    rng = np.random.default_rng(4)
    path = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, 90 * 24)))
    basis = 1 + np.cumsum(rng.normal(0, 0.0001, 90 * 24))
    rates = rng.normal(0.0001, 0.0002, 270)
    c = coin(days=90, spot=lambda i: path[i], perp=lambda i: path[i] * basis[i], rates=lambda i: rates[i])
    start, end = T0 + 20 * D, T0 + 85 * D
    if kind == "carry":
        pos = C.carry_positions(c, 0.0001, 0.0, 3, C.CrCosts(), start, end)[0]
        cap = 2.0
    else:
        pos = C.momentum_positions(c, 14, C.CrCosts(), start, end)[0]
        cap = 1.0
    daily = C.daily_returns(c, pos, cap, start, end + 2 * D, kind)
    assert sum(daily.values()) == pytest.approx(sum(p.net_bp for p in pos) / 1e4 / cap, abs=1e-9)


def test_no_carry_edge_from_mean_zero_funding_and_a_random_basis():
    """The carry earns exactly what funding pays: with mean-zero funding and a driftless basis, the timing
    rule cannot manufacture a gross edge."""
    gross = []
    for seed in range(40):
        rng = np.random.default_rng(100 + seed)
        path = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, 120 * 24)))
        basis = 1 + np.cumsum(rng.normal(0, 0.00005, 120 * 24))
        rates = rng.normal(0.0, 0.0002, 360)
        c = coin(days=120, spot=lambda i: path[i], perp=lambda i: path[i] * basis[i], rates=lambda i: rates[i])
        gross += [p.gross_bp for p in C.carry_positions(c, 0.0001, 0.0, 3, C.CrCosts(), T0, T0 + 118 * D)[0]]
    g = np.array(gross)
    assert len(g) > 200
    assert abs(g.mean() / (g.std(ddof=1) / np.sqrt(len(g)))) < 2.5


def test_stress_scales_every_cost():
    b = C.CrCosts().stressed(1.5)
    assert b.spot_fee_bp == 15 and b.perp_fee_bp == 7.5 and b.half("XRPUSDT") == 3 and b.slip_bp == 1.5


def test_a_carry_through_a_doubling_is_charged_a_forced_rebalance():
    c = coin(spot=lambda i: 100 * (1 + (i > 100) * 1.0), rates=lambda i: np.full(len(i), 0.0002))
    (p,) = C.carry_positions(c, 0.0001, 0.0, 1, C.CrCosts(), T0, T0 + 20 * D)[0]
    base = 2 * (10 + 2 + 1) + 2 * (5 + 2 + 1)
    assert p.rebalances == 1 and p.cost_bp == pytest.approx(2 * base)
