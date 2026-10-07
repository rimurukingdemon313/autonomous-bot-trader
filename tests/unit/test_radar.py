"""The funding radar (aitrader/radar): venue parsing on recorded payload shapes, and the paper ledger on simulated
hourly runs whose correct answer is known."""

from __future__ import annotations

import json

import pytest

from aitrader.radar import core as R
from aitrader.radar import venues as Vn

T0 = 1_760_000_400  # an hour boundary
H = 3600
APR = 1 / 8760  # one unit of annualised rate expressed per hour


def q(venue, coin, apr, px=100.0, vol=50e6, scale=1.0):
    return Vn.Quote(venue, coin, scale, apr * APR, px, vol)


def run(hours, quote_fn, state=None, rules=R.Rules()):
    state = state or R.State()
    for k in range(hours):
        R.step(state, quote_fn(k), {}, T0 + k * H, rules)
    return state


def test_nothing_opens_before_72_hours_of_history():
    s = run(60, lambda k: [q("hyperliquid", "ABC", 0.60), q("gate", "ABC", 0.05)])
    assert not s.open and not s.closed


def test_a_persistent_spread_opens_short_high_long_low_and_accrues_the_funding():
    s = run(100, lambda k: [q("hyperliquid", "ABC", 0.60), q("gate", "ABC", 0.05)])
    (p,) = s.open
    assert (p.short_venue, p.long_venue) == ("hyperliquid", "gate")
    held_h = (T0 + 99 * H - p.opened) / H
    assert p.funding_bp == pytest.approx(0.55 * APR * held_h * 1e4)
    assert p.cost_bp == pytest.approx(Vn.TAKER_BP["hyperliquid"] + 5 + Vn.TAKER_BP["gate"] + 5)


def test_the_position_closes_when_the_spread_decays_and_pays_closing_costs():
    s = run(200, lambda k: [q("hyperliquid", "ABC", 0.60 if k < 120 else 0.05), q("gate", "ABC", 0.05)])
    assert not s.open and s.closed[0].reason == "spread_decayed"
    c = s.closed[0]
    assert c.cost_bp == pytest.approx(2 * (Vn.TAKER_BP["hyperliquid"] + 5 + Vn.TAKER_BP["gate"] + 5))
    assert c.net_bp == pytest.approx(c.funding_bp + c.basis_bp - c.cost_bp)


def test_a_different_token_under_the_same_ticker_is_refused():
    s = run(100, lambda k: [q("hyperliquid", "ABC", 0.60, px=100), q("gate", "ABC", 0.05, px=3.0)])
    assert not s.open


def test_illiquid_contracts_are_refused():
    s = run(100, lambda k: [q("hyperliquid", "ABC", 0.60, vol=1e6), q("gate", "ABC", 0.05)])
    assert not s.open


def test_a_contract_per_1000_units_is_compared_at_its_scale():
    s = run(100, lambda k: [q("hyperliquid", "PEPE", 0.60, px=0.01, scale=1000), q("gate", "PEPE", 0.05, px=0.00001)])
    assert len(s.open) == 1


def test_a_venue_missing_for_a_day_closes_the_position():
    def quotes(k):
        base = [q("hyperliquid", "ABC", 0.60)]
        return base + ([q("gate", "ABC", 0.05)] if k < 100 else [])
    s = run(140, quotes)
    assert s.closed and s.closed[0].reason == "venue_unavailable"


def test_a_25_percent_move_closes_for_rebalance():
    s = run(120, lambda k: [q("hyperliquid", "ABC", 0.60, px=100 * (1.3 if k > 100 else 1)),
                            q("gate", "ABC", 0.05, px=100 * (1.3 if k > 100 else 1))])
    assert any(p.reason == "rebalance" for p in s.closed)


def test_at_most_max_open_and_one_per_coin():
    coins = [f"C{i}" for i in range(15)]
    s = run(100, lambda k: [x for c in coins for x in (q("hyperliquid", c, 0.60), q("gate", c, 0.05),
                                                        q("mexc", c, 0.02))])
    assert len(s.open) == R.Rules().max_open and len({p.coin for p in s.open}) == len(s.open)


def test_state_round_trips_through_json():
    s = run(100, lambda k: [q("hyperliquid", "ABC", 0.60), q("gate", "ABC", 0.05)])
    s2 = R.State.from_json(json.loads(json.dumps(s.to_json())))
    assert s2.open[0].funding_bp == s.open[0].funding_bp and len(s2.history) == len(s.history)


def test_performance_is_the_excess_over_cash_on_the_capital_deployed():
    s = run(24 * 10, lambda k: [q("hyperliquid", "ABC", 0.60), q("gate", "ABC", 0.05)])
    perf = R.performance(s, R.Rules(), 0.04)
    (p,) = s.open
    held_y = (T0 + (24 * 10 - 1) * H - p.opened) / H / 8760
    cost = 2 * (Vn.TAKER_BP["hyperliquid"] + 5 + Vn.TAKER_BP["gate"] + 5) / 1e4  # opening, and closing as if now
    expected = (0.55 * held_y - cost) / (2 * held_y) - 0.04  # funding on N, capital 2N, cash rate on 2N
    assert perf["ann_excess_deployed_pct"] == pytest.approx(expected * 100, abs=1e-3)
    assert perf["days"] > 9 and perf["open_positions"] == 1 and perf["run_coverage"] == 1.0
    assert perf["ann_excess_deployed_costs_x2_pct"] < perf["ann_excess_deployed_costs_x1.5_pct"] < expected * 100


def test_without_positions_the_book_has_no_excess_and_no_drawdown():
    perf = R.performance(run(100, lambda k: [q("hyperliquid", "ABC", 0.0), q("gate", "ABC", 0.0)]), R.Rules(), 0.04)
    assert perf["book_excess_pct"] == 0 and perf["max_dd_pct"] == 0 and perf["ann_excess_deployed_pct"] is None


def test_the_forward_verdict_waits_then_judges_once_on_every_gate():
    good = {"days": 61, "closed_positions": 40, "ann_excess_deployed_pct": 14.0, "t_excess_daily": 2.6,
            "ann_excess_deployed_costs_x1.5_pct": 9.0, "book_excess_without_best_coin_pct": 1.2, "max_dd_pct": 3.0,
            "run_coverage": 0.95}
    assert R.forward_verdict({**good, "days": 59})[0] == "WAIT"
    assert R.forward_verdict({**good, "closed_positions": 12})[0] == "INCONCLUSIVE"
    assert R.forward_verdict(good)[0] == "PASSED"
    assert R.forward_verdict({**good, "days": 121, "t_excess_daily": 2.3}, extended=True)[0] == "FAILED"
    for k, bad in (("ann_excess_deployed_pct", 9.9), ("t_excess_daily", 1.9), ("ann_excess_deployed_costs_x1.5_pct", 0.0),
                   ("book_excess_without_best_coin_pct", -0.1), ("max_dd_pct", 10.5), ("run_coverage", 0.85)):
        status, gates = R.forward_verdict({**good, k: bad})
        assert status == "FAILED" and list(gates.values()).count(False) == 1, k
    assert R.forward_verdict({k: v for k, v in good.items() if k != "t_excess_daily"})[0] == "FAILED"  # missing fails


# ── venue parsers on payload shapes ──────────────────────────────────────

def fake(payloads):
    def get(url, body=None):
        for key, v in payloads.items():
            if key in url:
                return v
        raise AssertionError(url)
    return get


def test_hyperliquid_hourly_rate_and_k_prefix():
    g = fake({"hyperliquid": ({"universe": [{"name": "BTC"}, {"name": "kPEPE"}, {"name": "OLD", "isDelisted": True}]},
                              [{"funding": "0.0000125", "markPx": "60000", "dayNtlVlm": "1e9"},
                               {"funding": "0.00002", "markPx": "0.01", "dayNtlVlm": "5e7"},
                               {"funding": "0.1", "markPx": "1", "dayNtlVlm": "1"}])})
    out = Vn.hyperliquid(g)
    assert [(x.coin, x.scale) for x in out] == [("BTC", 1.0), ("PEPE", 1000.0)]
    assert out[0].rate_per_hour == pytest.approx(0.0000125)


def test_gate_divides_by_its_funding_interval():
    g = fake({"contracts": [{"name": "BTC_USDT", "funding_interval": 28800}],
              "tickers": [{"contract": "BTC_USDT", "funding_rate": "0.0001", "mark_price": "60000",
                           "volume_24h_quote": "2e8"}]})
    (x,) = Vn.gate(g)
    assert x.rate_per_hour == pytest.approx(0.0001 / 8)


def test_mexc_divides_by_its_collect_cycle():
    g = fake({"funding_rate": {"data": [{"symbol": "ETH_USDT", "fundingRate": 0.0004, "collectCycle": 4}]},
              "ticker": {"data": [{"symbol": "ETH_USDT", "fairPrice": 3000, "amount24": 1e8}]}})
    (x,) = Vn.mexc(g)
    assert x.rate_per_hour == pytest.approx(0.0001)


def test_dydx_rate_is_hourly_and_inactive_markets_are_skipped():
    g = fake({"dydx": {"markets": {"BTC-USD": {"status": "ACTIVE", "nextFundingRate": "0.00001", "oraclePrice": "60000",
                                               "volume24H": "3e8"},
                                   "XYZ-USD": {"status": "PAUSED", "nextFundingRate": "0.1", "oraclePrice": "1"}}}})
    (x,) = Vn.dydx(g)
    assert x.coin == "BTC" and x.rate_per_hour == pytest.approx(0.00001)


def test_a_failing_venue_is_reported_not_zero_filled(monkeypatch):
    def boom(get):
        raise RuntimeError("HTTP 451")
    monkeypatch.setitem(Vn.FETCHERS, "gate", boom)
    monkeypatch.setitem(Vn.FETCHERS, "hyperliquid", lambda get: [])
    monkeypatch.setitem(Vn.FETCHERS, "mexc", lambda get: [])
    monkeypatch.setitem(Vn.FETCHERS, "dydx", lambda get: [])
    quotes, errors = Vn.snapshot()
    assert quotes == [] and "gate" in errors and "451" in errors["gate"]
