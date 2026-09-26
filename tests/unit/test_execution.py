"""Execution and the paper broker: idempotency, ambiguity, recovery, fills."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from aitrader.broker.base import AmbiguousExecution, BrokerRejected
from aitrader.broker.paper import PaperBroker
from aitrader.data.bars import BarSeries
from aitrader.data.feed import ReplayFeed
from aitrader.execution.engine import UNKNOWN_RECHECKS, ExecutionEngine, client_id_for
from aitrader.memory.db import Database
from aitrader.risk.engine import RiskVerdict

T0 = 1_600_000_000 // 3600 * 3600


def h1(symbol, mids, spread=0.0001, wick=0.0005, t0=T0):
    mids = np.asarray(mids, float)
    n = len(mids)
    o = np.concatenate(([mids[0]], mids[:-1]))
    hi, lo = np.maximum(o, mids) + wick, np.minimum(o, mids) - wick
    half = spread / 2
    return BarSeries.from_columns(symbol, "H1", "t", open_time=t0 + 3600 * np.arange(n),
                                  bid_open=o - half, bid_high=hi - half, bid_low=lo - half, bid_close=mids - half,
                                  ask_open=o + half, ask_high=hi + half, ask_low=lo + half, ask_close=mids + half,
                                  ticks=np.full(n, 10), spread_mean=np.full(n, spread), spread_max=np.full(n, spread))


class Clock:
    def __init__(self, t): self.t = t
    def __call__(self): return self.t


def setup(mids=None, db=None):
    feed = ReplayFeed({"EURUSD": h1("EURUSD", mids if mids is not None else [1.1] * 50)})
    clock = Clock(T0 + 3600 * 10)
    db = db or Database(":memory:")
    db.set_kv("kill_switch", {"active": False})
    return feed, clock, db


def decision(did="d1", side="BUY"):
    return SimpleNamespace(id=did, decision=side, instrument="EURUSD")


def verdict(did="d1", stop=1.098, target=1.104, qty=0.5):
    return RiskVerdict(did, True, qty=qty, risk_amount=100, risk_pct=0.5, entry_ref=1.10005, stop=stop, target=target)


def test_fill_then_duplicate_is_not_resent():
    feed, clock, db = setup()
    ex = ExecutionEngine(db, PaperBroker(feed, clock, db), clock)
    r1 = ex.execute(decision(), verdict())
    assert r1.status == "FILLED"
    r2 = ex.execute(decision(), verdict())
    assert r2.status == "DUPLICATE"
    assert len(ex.broker.positions()) == 1


def test_unapproved_verdicts_never_reach_the_broker():
    feed, clock, db = setup()
    broker = PaperBroker(feed, clock, db)
    v = verdict()
    v.approved = False
    assert ExecutionEngine(db, broker, clock).execute(decision(), v).status == "SKIPPED"
    assert broker.positions() == []


@pytest.mark.parametrize("state,reason", [
    ({"kill_switch": {"active": True}}, "kill switch"),
    ({"kill_switch": None}, "kill switch"),
    ({"paused": True}, "paused"),
])
def test_final_checks_block_submission(state, reason):
    feed, clock, db = setup()
    for k, v in state.items():
        db.set_kv(k, v)
    broker = PaperBroker(feed, clock, db)
    r = ExecutionEngine(db, broker, clock).execute(decision(), verdict())
    assert r.status == "BLOCKED" and reason in r.detail and broker.positions() == []


def test_a_non_demo_broker_is_refused_unless_live_is_explicitly_allowed():
    feed, clock, db = setup()
    broker = PaperBroker(feed, clock, db)
    broker.is_demo = lambda: None  # could not be verified
    assert ExecutionEngine(db, broker, clock).execute(decision(), verdict()).status == "BLOCKED"


def test_price_through_the_stop_blocks():
    feed, clock, db = setup()
    r = ExecutionEngine(db, PaperBroker(feed, clock, db), clock).execute(decision(), verdict(stop=1.2, target=1.3))
    assert r.status == "BLOCKED" and "stop" in r.detail


class AmbiguousBroker(PaperBroker):
    """The order DID go through, but the response was lost."""

    def place_market(self, *a, **kw):
        super().place_market(*a, **kw)
        raise AmbiguousExecution("connection reset after send")


class LostBroker(PaperBroker):
    """The order did NOT go through, and the response was lost."""
    calls = 0

    def place_market(self, *a, **kw):
        LostBroker.calls += 1
        raise AmbiguousExecution("timeout")


def test_ambiguous_write_is_resolved_by_query_not_by_resending():
    feed, clock, db = setup()
    broker = AmbiguousBroker(feed, clock, db)
    r = ExecutionEngine(db, broker, clock).execute(decision(), verdict())
    assert r.status == "FILLED" and "query" in r.detail
    assert len(broker.positions()) == 1


def test_ambiguous_write_with_no_order_stays_unknown_and_is_never_resent():
    feed, clock, db = setup()
    LostBroker.calls = 0
    broker = LostBroker(feed, clock, db)
    ex = ExecutionEngine(db, broker, clock)
    assert ex.execute(decision(), verdict()).status == "UNKNOWN"
    for _ in range(UNKNOWN_RECHECKS + 2):
        ex.reconcile()
    assert LostBroker.calls == 1
    assert db.one("SELECT status FROM intents")["status"] == "NOT_FOUND"
    assert ex.execute(decision(), verdict()).status == "DUPLICATE"


def test_crash_between_intent_and_submit_is_recovered_on_restart(tmp_path):
    path = tmp_path / "s.db"
    feed, clock, db = setup(db=Database(path))
    broker = PaperBroker(feed, clock, db)
    ex = ExecutionEngine(db, broker, clock)
    # Simulate: intent written, order sent, process died before recording the fill.
    ex._final_checks = lambda d, v: None
    orig = ex._record_fill
    ex._record_fill = lambda *a: (_ for _ in ()).throw(SystemExit("crash"))
    with pytest.raises(SystemExit):
        ex.execute(decision(), verdict())
    assert db.one("SELECT status FROM intents")["status"] == "SUBMITTING"
    # Restart: new objects over the same database and broker state.
    db2 = Database(path)
    broker2 = PaperBroker(feed, clock, db2)
    ex2 = ExecutionEngine(db2, broker2, clock)
    rep = ex2.reconcile()
    assert rep["resolved"] == [client_id_for("d1")]
    assert db2.one("SELECT status FROM intents")["status"] == "FILLED"
    assert len(broker2.positions()) == 1
    assert ex2.execute(decision(), verdict()).status == "DUPLICATE"


def test_paper_state_survives_restart(tmp_path):
    path = tmp_path / "s.db"
    feed, clock, db = setup(db=Database(path))
    PaperBroker(feed, clock, db).place_market("EURUSD", 1, 0.1, 1.09, 1.12, "c1")
    again = PaperBroker(feed, clock, Database(path))
    assert len(again.positions()) == 1
    with pytest.raises(BrokerRejected):
        again.place_market("EURUSD", 1, 0.1, 1.09, 1.12, "c1")


def test_stop_is_checked_before_target_in_the_same_bar():
    mids = [1.1] * 12 + [1.1]
    s = h1("EURUSD", mids)
    feed = ReplayFeed({"EURUSD": s})
    clock = Clock(int(s.available_at[10]))
    b = PaperBroker(feed, clock)
    b.place_market("EURUSD", 1, 1.0, 1.0995, 1.1005, "c1")
    bar = {"open_time": int(s.open_time[11]), "close_time": int(s.available_at[11]),
           "bid_open": 1.1, "bid_high": 1.101, "bid_low": 1.099, "bid_close": 1.1,
           "ask_open": 1.1001, "ask_high": 1.1011, "ask_low": 1.0991, "ask_close": 1.1001}
    closed = b.on_bar("EURUSD", bar)
    assert closed[0].reason == "STOP"
    assert closed[0].pnl < 0


def test_gap_through_the_stop_fills_at_the_open_and_pnl_is_in_usd():
    s = h1("EURUSD", [1.1] * 20)
    feed = ReplayFeed({"EURUSD": s})
    clock = Clock(int(s.available_at[10]))
    b = PaperBroker(feed, clock, commission_per_lot_rt=0.0, slippage_pips=0.0)
    fill = b.place_market("EURUSD", 1, 1.0, 1.098, 1.104, "c1")
    bar = {"open_time": int(s.open_time[11]), "close_time": int(s.available_at[11]),
           "bid_open": 1.095, "bid_high": 1.096, "bid_low": 1.094, "bid_close": 1.095,
           "ask_open": 1.0951, "ask_high": 1.0961, "ask_low": 1.0941, "ask_close": 1.0951}
    ct = b.on_bar("EURUSD", bar)[0]
    assert ct.exit == pytest.approx(1.095)
    assert ct.pnl == pytest.approx((1.095 - fill.price) * 100_000)


def test_missing_conversion_rate_means_no_spec_and_no_trade():
    feed = ReplayFeed({"EURGBP": h1("EURGBP", [0.85] * 20)})
    b = PaperBroker(feed, Clock(T0 + 3600 * 15))
    assert b.spec("EURGBP") is None  # no GBPUSD quote to convert with


def test_sync_closures_turns_broker_exits_into_closed_positions():
    feed, clock, db = setup()
    broker = PaperBroker(feed, clock, db)
    ex = ExecutionEngine(db, broker, clock)
    r = ex.execute(decision(), verdict(stop=1.0999 - 0.0005, target=1.1004))
    assert r.status == "FILLED"
    s = feed.series["EURUSD"]
    bar = {"open_time": int(s.open_time[11]), "close_time": int(s.available_at[11]),
           "bid_open": 1.1, "bid_high": 1.1010, "bid_low": 1.09995, "bid_close": 1.1,
           "ask_open": 1.1001, "ask_high": 1.1011, "ask_low": 1.1, "ask_close": 1.1001}
    broker.on_bar("EURUSD", bar)
    done = ex.sync_closures()
    assert len(done) == 1 and done[0][1].reason == "TARGET"
    assert db.one("SELECT status FROM positions")["status"] == "CLOSED"
