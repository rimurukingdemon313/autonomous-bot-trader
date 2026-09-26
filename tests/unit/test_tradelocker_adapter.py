"""TradeLocker adapter and the transferred transport, with a fake client / fake network."""

from __future__ import annotations

import io
import urllib.error
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from aitrader.broker.base import AmbiguousExecution, BrokerError
from aitrader.broker.tradelocker._compat import BrokerConfig, TradingConfig
from aitrader.broker.tradelocker.adapter import TradeLockerAdapter
from aitrader.broker.tradelocker.http import HttpTransport

DEMO = TradingConfig(BrokerConfig("e", "p", "S", "1", "https://demo.tradelocker.com/backend-api"))
LIVE = TradingConfig(BrokerConfig("e", "p", "S", "1", "https://live.tradelocker.com/backend-api"))
NOW = 1_700_000_000


def pos(pid, sym="EURUSD", side="BUY", qty=0.5, opened=NOW):
    return SimpleNamespace(position_id=pid, symbol=sym, direction=side, quantity=qty, entry_price=1.1,
                           stop_loss=1.09, take_profit=1.12, opened_at=datetime.fromtimestamp(opened, timezone.utc))


class FakeClient:
    def __init__(self, meta=None, positions=(), spec=None, rows=None, quote=(1.1000, 1.1001)):
        self.meta = meta if meta is not None else {"accountType": "DEMO"}
        self._positions = list(positions)
        self.opened_after_order = []
        self._spec = spec or SimpleNamespace(tick_value=1.0, tick_size=0.00001, contract_size=100000,
                                             min_lot=0.01, lot_step=0.01, max_lot=50, quote_currency="USD",
                                             account_currency="USD")
        self.rows = rows or []
        self.q = quote
        self.orders = 0

    def ensure_session(self): pass
    def account_metadata(self): return self.meta
    def session_claims(self): return {}
    def instrument(self, symbol):
        if symbol == "MISSING":
            raise BrokerError("no such instrument")
        return self._spec
    def quote(self, spec): return SimpleNamespace(bid=self.q[0], ask=self.q[1], timestamp=datetime.fromtimestamp(NOW, timezone.utc))
    def positions(self): return list(self._positions)
    def candles(self, spec, tf, count): return self.rows
    def place_market_order(self, spec, **kw):
        self.orders += 1
        self._positions += self.opened_after_order
        return SimpleNamespace(order_id="O1", raw={})


def adapter(client, config=DEMO, intents=None, claimed=()):
    return TradeLockerAdapter(config, ["EURUSD"], intent_lookup=lambda cid: (intents or {}).get(cid),
                              claimed_positions=lambda: set(claimed), client=client, clock=lambda: NOW,
                              sleep=lambda s: None)


def test_demo_needs_both_signals():
    assert adapter(FakeClient()).is_demo() is True
    assert adapter(FakeClient(), config=LIVE).is_demo() is False
    assert adapter(FakeClient(meta={"accountType": "LIVE"})).is_demo() is False
    # A user-settable name can never PASS the check (the archive accepted it; this does not)...
    assert adapter(FakeClient(meta={"name": "my demo nickname"})).is_demo() is False
    # ...but it can still FAIL it, the safe direction.
    assert adapter(FakeClient(meta={"accountType": "DEMO", "name": "LIVE account"})).is_demo() is False


def test_demo_evidence_that_cannot_be_read_is_not_true():
    c = FakeClient()
    c.ensure_session = lambda: (_ for _ in ()).throw(BrokerError("down"))
    assert adapter(c).is_demo() is None


def test_accepted_order_returns_the_new_position():
    c = FakeClient(positions=[pos("OLD")])
    c.opened_after_order = [pos("NEW")]
    f = adapter(c).place_market("EURUSD", 1, 0.5, 1.09, 1.12, "ai-x")
    assert f.position_id == "NEW" and c.orders == 1


def test_accepted_order_without_a_visible_position_is_ambiguous_not_resent():
    c = FakeClient()
    with pytest.raises(AmbiguousExecution):
        adapter(c).place_market("EURUSD", 1, 0.5, 1.09, 1.12, "ai-x")
    assert c.orders == 1


def test_reconciliation_matches_exactly_one_unclaimed_position():
    intents = {"ai-x": {"symbol": "EURUSD", "side": "BUY", "qty": 0.5, "ts": NOW - 10}}
    one = adapter(FakeClient(positions=[pos("P1")]), intents=intents)
    assert one.find_by_client_id("ai-x").id == "P1"
    claimed = adapter(FakeClient(positions=[pos("P1")]), intents=intents, claimed={"P1"})
    assert claimed.find_by_client_id("ai-x") is None
    two = adapter(FakeClient(positions=[pos("P1"), pos("P2")]), intents=intents)
    assert two.find_by_client_id("ai-x") is None  # refuses to guess
    older = adapter(FakeClient(positions=[pos("P0", opened=NOW - 3600)]), intents=intents)
    assert older.find_by_client_id("ai-x") is None


def test_bars_exclude_the_forming_bar_and_only_the_latest_spread_is_known():
    rows = [{"timestamp": datetime.fromtimestamp(NOW - 3600 * k, timezone.utc), "open": 1.1, "high": 1.101,
             "low": 1.099, "close": 1.1, "volume": 100} for k in range(5, 0, -1)]
    rows.append({"timestamp": datetime.fromtimestamp(NOW, timezone.utc), "open": 1.1, "high": 1.2, "low": 1.0,
                 "close": 1.15, "volume": 5})  # still forming at NOW
    b = adapter(FakeClient(rows=rows)).bars("EURUSD", NOW + 60, 10)
    assert int(b.open_time[-1]) == NOW - 3600
    assert b.ask_close[-1] - b.bid_close[-1] == pytest.approx(0.0001)
    import numpy as np
    assert np.isnan(b.spread_mean[0]) and b.spread_mean[-1] == pytest.approx(0.0001)


def test_spec_without_a_way_to_value_a_move_is_none():
    spec = SimpleNamespace(tick_value=None, tick_size=0.00001, contract_size=100000, min_lot=0.01, lot_step=0.01,
                           max_lot=50, quote_currency="GBP", account_currency="USD")
    c = FakeClient(spec=spec)
    c.quote = lambda s: (_ for _ in ()).throw(BrokerError("no quote"))
    assert adapter(c).spec("EURGBP") is None
    assert adapter(FakeClient()).spec("EURUSD").value_per_price_unit == pytest.approx(1.0)


# ── the transferred transport: writes are never retried ────────────────


def test_a_write_that_hits_a_server_error_is_ambiguous_and_sent_once(monkeypatch):
    calls = []

    def boom(request, timeout=None):
        calls.append(request.get_method())
        raise urllib.error.HTTPError("http://x", 502, "bad gateway", {}, io.BytesIO(b"oops"))
    monkeypatch.setattr("urllib.request.urlopen", boom)
    t = HttpTransport(timeout=1, max_attempts=4)
    with pytest.raises(AmbiguousExecution):
        t.request("POST", "https://demo.tradelocker.com/x", body={"a": 1})
    assert calls == ["POST"]


def test_a_read_that_hits_a_server_error_is_retried(monkeypatch):
    calls = []

    def boom(request, timeout=None):
        calls.append(request.get_method())
        raise urllib.error.HTTPError("http://x", 503, "unavailable", {}, io.BytesIO(b"x"))
    monkeypatch.setattr("urllib.request.urlopen", boom)
    monkeypatch.setattr("time.sleep", lambda s: None)
    t = HttpTransport(timeout=1, max_attempts=3)
    with pytest.raises(BrokerError):
        t.request("GET", "https://demo.tradelocker.com/x")
    assert len(calls) == 3
