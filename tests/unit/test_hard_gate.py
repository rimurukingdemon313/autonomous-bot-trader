"""The hard risk gate (aitrader/risk/hard_gate.py) on the FTMO-style $200K paper account.

Every scenario is built so the right answer is known by construction: a controllable quote, a paper broker
whose balance is set to a realised result, and a pinned clock. The fake feed replaces the market only. The
gate, the paper broker and the execution engine are the production code."""

from __future__ import annotations

import dataclasses
import json
import math
import random
import threading
from types import SimpleNamespace

import pytest

from aitrader.broker.base import BrokerRejected
from aitrader.broker.paper import PaperBroker
from aitrader.execution.engine import ExecutionEngine
from aitrader.memory.db import Database
from aitrader.risk.engine import AccountState, InstrumentSpec, Quote, RiskEngine, RiskLimits, RiskVerdict
from aitrader.risk.hard_gate import (CLEAR_KILL_CONFIRMATION, RESET_CONFIRMATION, HardRiskGate, Permit,
                                     TradeProposal)
from aitrader.risk.profile import FTMO_200K, HardRiskProfile, ProfileError, loss_per_lot

T0 = 1_768_298_400  # Tuesday 2026-01-13 10:00 UTC (11:00 in Prague, winter time)
BID, ASK = 1.09995, 1.10005  # EURUSD, 1 pip spread


class Clock:
    def __init__(self, t): self.t = t
    def __call__(self): return self.t


class Feed:
    """Quotes the test sets; time defaults to 'now' (fresh) unless a test pins it."""

    def __init__(self):
        self.q = {"EURUSD": [BID, ASK, None], "GBPUSD": [1.27495, 1.27505, None]}

    def quote(self, symbol, now):
        if symbol not in self.q:
            return None
        bid, ask, t = self.q[symbol]
        return Quote(symbol, bid, ask, now if t is None else t)

    def move(self, symbol, mid, spread=0.0001):
        self.q[symbol][0], self.q[symbol][1] = mid - spread / 2, mid + spread / 2


def env(balance=200_000.0, profile=FTMO_200K, t=T0, path=":memory:"):
    db = Database(path)
    if db.get_kv("kill_switch") is None:
        db.set_kv("kill_switch", {"active": False})
    clock, feed = Clock(t), Feed()
    gate = HardRiskGate(db, profile, clock)
    broker = PaperBroker(feed, clock, db, start_balance=balance, gate=gate)
    ex = ExecutionEngine(db, broker, clock, gate=gate, allow_unvalidated=True)
    return SimpleNamespace(db=db, clock=clock, feed=feed, gate=gate, broker=broker, ex=ex)


def prop(did="d1", qty=5.0, stop=ASK - 0.0008, side=1, entry=ASK, target=None, swap=0.0, symbol="EURUSD",
         source="STRATEGY"):
    target = target if target is not None else (entry + 0.0020 * side if entry else 1.2)
    return TradeProposal(did, f"ai-{did}", symbol, side, qty, entry, stop, target, swap, source)


def set_balance(e, balance):
    """A realised result: what closed trades would have left in the account."""
    e.broker.state["balance"] = balance


def decision(did, side="BUY", **extra):
    return SimpleNamespace(id=did, decision=side, instrument="EURUSD", timestamp=None, edge_status="EXPERIMENTAL",
                           **extra)


def execute(e, did, qty=5.0, stop=ASK - 0.0008, side="BUY", **extra):
    d = decision(did, side, **extra)
    d.timestamp = e.clock()
    s = 1 if side == "BUY" else -1
    entry = ASK if s > 0 else BID
    v = RiskVerdict(did, True, qty=qty, risk_amount=500, risk_pct=0.25, entry_ref=entry, stop=stop,
                    target=entry + 0.0030 * s)
    return e.ex.execute(d, v)


# ── the profile ───────────────────────────────────────────────────────────

def test_the_default_profile_is_the_200k_ftmo_style_account():
    p = FTMO_200K
    assert (p.starting_balance, p.daily_loss_limit, p.max_total_loss) == (200_000, 10_000, 20_000)
    assert (p.challenge_target, p.verification_target, p.min_trading_days) == (20_000, 10_000, 4)
    assert (p.risk_per_trade, p.max_open_risk) == (500, 2_000)  # 0.25% and 1.0% of the starting balance
    assert p.daily_loss_limit / p.starting_balance == 0.05 and p.max_total_loss / p.starting_balance == 0.10
    assert p.total_loss_floor == 180_000 and (p.reset_timezone, p.reset_hour) == ("Europe/Prague", 0)


@pytest.mark.parametrize("bad", [{"risk_per_trade": 3_000}, {"max_total_loss": 250_000}, {"daily_loss_limit": -1},
                                 {"reset_timezone": "Mars/Olympus"}, {"reset_hour": 24}, {"leverage": math.nan},
                                 {"risk_per_trade": "500"}, {"min_trading_days": 0}])
def test_an_inconsistent_profile_cannot_exist(bad):
    with pytest.raises(ProfileError):
        dataclasses.replace(FTMO_200K, **bad)


def test_profile_is_frozen_and_unknown_overrides_are_refused():
    with pytest.raises(dataclasses.FrozenInstanceError):
        FTMO_200K.risk_per_trade = 5_000  # type: ignore[misc]
    with pytest.raises(ProfileError):
        HardRiskProfile.from_overrides(FTMO_200K, {"risk_per_trad": 1})


# ── 1-2: accept and per-trade risk ──────────────────────────────────────────

def test_1_a_valid_trade_is_accepted_and_filled_with_a_bounded_loss():
    e = env()
    r = execute(e, "ok")
    assert r.status == "FILLED"
    (pos,) = e.broker.positions()
    st = e.gate.status()
    assert st["state"] == "ACTIVE" and st["open"] == {"ai-ok": "OPEN"}
    row = e.db.one("SELECT payload FROM risk_gate_log WHERE kind='DECISION' AND approved=1")
    audit = json.loads(row["payload"])
    # 8 pips x 5 lots = 400, commission 5 x 7 = 35, slippage 2 x 0.5 pip x 5 lots = 50: 485 <= 500
    assert audit["monetary_risk"] == pytest.approx(485.0)
    assert audit["final_execution_decision"] == "PERMIT_ISSUED"


def test_2_a_trade_risking_more_than_0_25_percent_is_rejected_before_the_broker():
    e = env()
    r = execute(e, "big", qty=7.0)  # 8 pips x 7 lots = 560 at the stop alone
    assert r.status == "BLOCKED" and "reason=PER_TRADE_RISK" in r.detail
    assert e.broker.positions() == [] and e.broker.state["clients"] == {}


# ── 3-7: daily and total loss on equity ─────────────────────────────────────

def test_3_daily_loss_exactly_at_the_limit_is_rejected_and_locks():
    e = env()
    e.gate.observe(e.broker)  # day reference 200,000
    set_balance(e, 190_000.0)
    r = e.gate.authorize(prop("x", qty=0.1), e.broker)
    assert not r.approved and r.code == "DAILY_LOSS_LIMIT"
    assert r.calc["daily_pnl"] == -10_000 and e.gate.status()["state"] == "LOCKED"


def test_4_daily_loss_beyond_the_limit_is_rejected_with_the_calculation_logged(capsys):
    e = env()
    e.gate.observe(e.broker)
    set_balance(e, 189_500.0)
    r = e.gate.authorize(prop("x", qty=0.1), e.broker)
    assert not r.approved and r.code == "DAILY_LOSS_LIMIT"
    assert "RISK_GATE_REJECTED reason=DAILY_LOSS_LIMIT equity_conservative=189500.00 daily_pnl=-10500.00 " \
           "daily_limit=-10000.00" in r.line
    assert "RISK_GATE_REJECTED reason=DAILY_LOSS_LIMIT" in capsys.readouterr().out  # structured stdout line too
    audit = json.loads(e.db.one("SELECT payload FROM risk_gate_log WHERE kind='DECISION' AND approved=0")["payload"])
    for k in ("timestamp", "symbol", "side", "proposed_entry", "stop_loss", "proposed_size", "monetary_risk",
              "balance", "equity", "daily_pnl", "total_drawdown", "open_risk", "estimated_fees",
              "estimated_slippage", "risk_gate_result", "rejection_reason", "final_execution_decision"):
        assert k in audit, k
    assert audit["rejection_reason"] == "DAILY_LOSS_LIMIT" and audit["final_execution_decision"] == "NO TRADE"
    assert audit["calculation"]["daily_reference"] == 200_000 and audit["calculation"]["daily_floor"] == 190_000


def _walk_down_three_days(e, last_balance):
    """Day 1: -9,000; day 2: -9,000; day 3 ends at `last_balance`. No single day reaches -10,000."""
    e.gate.observe(e.broker)
    set_balance(e, 191_000.0)
    e.gate.observe(e.broker)
    e.clock.t += 86_400
    e.gate.observe(e.broker)  # day 2 reference 191,000
    set_balance(e, 182_000.0)
    e.gate.observe(e.broker)
    e.clock.t += 86_400
    e.gate.observe(e.broker)  # day 3 reference 182,000
    set_balance(e, last_balance)


def test_5_maximum_total_loss_exactly_at_the_limit_is_rejected_and_locks():
    e = env()
    _walk_down_three_days(e, 180_000.0)
    r = e.gate.authorize(prop("x", qty=0.1), e.broker)
    assert not r.approved and r.code == "MAX_TOTAL_LOSS" and r.calc["total_pnl"] == -20_000
    assert e.gate.status()["lock"]["code"] == "MAX_TOTAL_LOSS"


def test_6_maximum_total_loss_beyond_the_limit_is_rejected():
    e = env()
    _walk_down_three_days(e, 179_000.0)
    r = e.gate.authorize(prop("x", qty=0.1), e.broker)
    assert not r.approved and r.code == "MAX_TOTAL_LOSS"


def test_7_an_open_position_s_unrealised_loss_triggers_the_daily_protection():
    e = env()
    e.gate.observe(e.broker)
    set_balance(e, 191_000.0)  # -9,000 realised today
    assert execute(e, "open").status == "FILLED"  # worst case 191,000 - 485 > 190,000
    e.feed.move("EURUSD", 1.0975)  # 25 pips against 5 lots: -1,250 unrealised (the stop has not been processed)
    r = e.gate.authorize(prop("next", qty=0.1, entry=1.09755, stop=1.0965, target=1.1), e.broker)
    assert not r.approved and r.code == "DAILY_LOSS_LIMIT"
    assert r.calc["equity_conservative"] < 190_000 and e.gate.status()["state"] == "LOCKED"


def test_a_trade_that_would_breach_the_daily_floor_if_every_stop_hit_is_refused_without_locking():
    e = env()
    e.gate.observe(e.broker)
    set_balance(e, 190_400.0)
    r = e.gate.authorize(prop("x"), e.broker)  # 190,400 - 485 = 189,915 <= 190,000
    assert not r.approved and r.code == "DAILY_LOSS_LIMIT" and r.calc["worst_case_equity"] == pytest.approx(189_915)
    assert e.gate.status()["state"] == "ACTIVE"  # nothing breached yet: refused, not locked


# ── 8-12: the trade's own numbers ──────────────────────────────────────────

def test_8_fees_are_part_of_the_trade_s_risk():
    e = env()
    r = e.gate.authorize(prop("fees", qty=6.0), e.broker)  # stop 480 <= 500, +42 commission = 522
    assert not r.approved and r.code == "FEES_EXCEED_RISK"
    assert r.calc["loss_breakdown"]["commission"] == pytest.approx(42.0)


def test_9_slippage_is_part_of_the_trade_s_risk():
    e = env()
    r = e.gate.authorize(prop("slip", qty=5.0, stop=ASK - 0.0009), e.broker)  # 450 + 35 = 485, + 50 slippage = 535
    assert not r.approved and r.code == "SLIPPAGE_EXCEEDS_RISK"
    assert r.calc["loss_breakdown"]["slippage"] == pytest.approx(50.0)


def test_financing_is_part_of_the_trade_s_risk_and_a_credit_never_helps():
    e = env()
    r = e.gate.authorize(prop("swap", qty=5.0, swap=0.00002), e.broker)  # 3 nights x 2 pips... 485 + 30 = 515
    assert not r.approved and r.code == "FINANCING_EXCEEDS_RISK"
    credit = e.gate.authorize(prop("credit", qty=5.0, swap=-0.001), e.broker)
    assert credit.approved and credit.calc["loss_breakdown"]["financing"] == 0.0


def test_10_a_missing_stop_loss_is_rejected():
    e = env()
    r = e.gate.authorize(prop("nostop", stop=None), e.broker)
    assert not r.approved and r.code == "MISSING_STOP_LOSS"


@pytest.mark.parametrize("stop", [ASK + 0.001, math.nan, -1.0, 0.0, "1.09"])
def test_an_invalid_stop_loss_is_rejected(stop):
    e = env()
    r = e.gate.authorize(prop("badstop", stop=stop), e.broker)
    assert not r.approved and r.code == "INVALID_STOP_LOSS"


@pytest.mark.parametrize("qty", [0.0, -1.0, math.nan, math.inf, 0.123, 0.001, "1", None, True])
def test_11_an_invalid_position_size_is_rejected(qty):
    e = env()
    r = e.gate.authorize(prop("badqty", qty=qty), e.broker)
    assert not r.approved and r.code == "INVALID_POSITION_SIZE"


def test_a_size_above_the_broker_maximum_is_rejected():
    e = env()
    r = e.gate.authorize(prop("huge", qty=60.0, stop=ASK - 0.00001), e.broker)
    assert not r.approved and r.code == "BROKER_CONSTRAINT"


@pytest.mark.parametrize("setup,code", [
    (lambda f: f.q["EURUSD"].__setitem__(2, T0 - 31), "MARKET_DATA_STALE"),
    (lambda f: f.q.pop("EURUSD"), "MARKET_DATA_MISSING"),
    (lambda f: f.q.__setitem__("EURUSD", [1.1001, 1.1000, None]), "MARKET_DATA_CONTRADICTORY"),
    (lambda f: f.q.__setitem__("EURUSD", [math.nan, 1.1000, None]), "MARKET_DATA_MISSING"),
    (lambda f: f.q.__setitem__("EURUSD", [1.0900, 1.1100, None]), "MARKET_DATA_OUT_OF_TOLERANCE"),
])
def test_12_stale_missing_contradictory_or_out_of_tolerance_market_data_is_rejected(setup, code):
    e = env()
    e.gate.observe(e.broker)
    setup(e.feed)
    r = e.gate.authorize(prop("md"), e.broker)
    assert not r.approved and r.code in (code, "INVALID_INSTRUMENT" if code == "MARKET_DATA_MISSING" else code)


@pytest.mark.parametrize("entry,code", [(None, "INVALID_ENTRY"), (0.0, "INVALID_ENTRY"), (math.nan, "INVALID_ENTRY"),
                                        (1.12, "MARKET_DATA_OUT_OF_TOLERANCE")])
def test_an_invalid_or_off_market_entry_is_rejected(entry, code):
    e = env()
    r = e.gate.authorize(prop("entry", entry=entry, target=1.2), e.broker)
    assert not r.approved and r.code == code


@pytest.mark.parametrize("symbol", ["EUR/USD", "", "eurusd", "XXXYYY", None])
def test_an_invalid_instrument_is_rejected(symbol):
    e = env()
    r = e.gate.authorize(prop("sym", symbol=symbol), e.broker)
    assert not r.approved and r.code == "INVALID_INSTRUMENT"


def test_unavailable_margin_is_rejected():
    e = env(profile=dataclasses.replace(FTMO_200K, name="FTMO-200K-1x", leverage=1.0))
    r = e.gate.authorize(prop("margin", qty=5.0), e.broker)  # 550,000 notional at 1:1 > 200,000 equity
    assert not r.approved and r.code == "MARGIN_UNAVAILABLE"


# ── 13-14: kill switch and the AI ──────────────────────────────────────────

@pytest.mark.parametrize("ks", [{"active": True}, None, "off", {"active": "false"}])
def test_13_an_active_or_unreadable_kill_switch_blocks_every_new_trade(ks):
    e = env()
    e.gate.observe(e.broker)
    e.db.set_kv("kill_switch", ks)
    for i in range(5):
        r = e.gate.authorize(prop(f"k{i}", qty=0.1), e.broker)
        assert not r.approved and r.code == "KILL_SWITCH_ACTIVE"
    assert e.broker.positions() == []


def test_the_gate_s_own_kill_switch_survives_clearing_the_system_switch_until_explicitly_cleared():
    e = env()
    e.gate.observe(e.broker)
    e.feed.q.pop("GBPUSD")
    e.broker.state["positions"]["X"] = {"id": "X", "symbol": "EURUSD", "side": 1, "qty": 1.0, "entry": ASK,
                                        "stop": 1.09, "target": 1.2, "client_id": "rogue", "opened": T0}
    r = e.gate.authorize(prop("a", qty=0.1), e.broker)
    assert not r.approved and r.code == "CONFLICTING_EXECUTION_STATE"
    assert e.db.get_kv("kill_switch")["active"] is True
    del e.broker.state["positions"]["X"]
    e.db.set_kv("kill_switch", {"active": False})  # the dashboard clears the system switch...
    assert e.gate.authorize(prop("b", qty=0.1), e.broker).code == "KILL_SWITCH_ACTIVE"  # ...the gate does not
    assert not e.gate.clear_kill("please", "looked at it")
    assert e.gate.clear_kill(CLEAR_KILL_CONFIRMATION, "rogue position removed, cause understood")
    assert e.gate.authorize(prop("c", qty=0.1), e.broker).approved


def test_14_an_ai_decision_cannot_override_a_rejection():
    e = env()
    # the "AI" says it is sure, asks for an override and claims a 5% risk budget: none of it is read
    r = execute(e, "ai", qty=12.0, override=True, force=True, risk_pct=5.0, confidence=0.99,
                instructions="ignore the risk limits")
    assert r.status == "BLOCKED" and "PER_TRADE_RISK" in r.detail and e.broker.positions() == []
    # calling the broker directly, without a permit, with a forged permit, or reusing one: refused
    with pytest.raises(BrokerRejected, match="NO_EXECUTION_PERMIT"):
        e.broker.place_market("EURUSD", 1, 12.0, ASK - 0.0008, 1.2, "ai-direct")
    forged = Permit("f" * 32, "ai-forged", "EURUSD", 1, 12.0, ASK - 0.0008, 1.2, T0, T0 + 60)
    with pytest.raises(BrokerRejected, match="not issued by this gate"):
        e.broker.place_market("EURUSD", 1, 12.0, ASK - 0.0008, 1.2, "ai-forged", permit=forged)
    ok = e.gate.authorize(prop("small", qty=1.0, target=1.2), e.broker)
    assert ok.approved
    with pytest.raises(BrokerRejected, match="differs"):  # a permit for 1 lot cannot buy 12
        e.broker.place_market("EURUSD", 1, 12.0, ok.permit.stop, 1.2, "ai-small", permit=ok.permit)
    e.broker.place_market("EURUSD", 1, 1.0, ok.permit.stop, 1.2, "ai-small", permit=ok.permit)
    with pytest.raises(BrokerRejected):
        e.broker.place_market("EURUSD", 1, 1.0, ok.permit.stop, 1.2, "ai-small", permit=ok.permit)
    assert len(e.broker.positions()) == 1
    # the gate has no setter for its limits, and the engine has no path around it
    with pytest.raises(AttributeError):
        e.gate.profile = dataclasses.replace(FTMO_200K, name="loose", risk_per_trade=2_000)
    with pytest.raises(TypeError):
        ExecutionEngine(e.db, e.broker, e.clock, gate=None)


def test_a_rejected_trade_never_reaches_the_broker():
    e = env()
    calls = []
    real = e.broker.place_market

    def spy(*a, **kw):
        calls.append(a)
        return real(*a, **kw)
    e.broker.place_market = spy
    for did, qty in (("r1", 7.0), ("r2", 0.123), ("r3", 6.0)):
        assert execute(e, did, qty=qty).status == "BLOCKED"
    assert calls == [] and e.broker.positions() == []


def test_a_broker_without_a_gate_fills_nothing():
    e = env()
    bare = PaperBroker(e.feed, e.clock, None, start_balance=200_000.0)
    with pytest.raises(BrokerRejected, match="NO_RISK_GATE"):
        bare.place_market("EURUSD", 1, 0.1, 1.09, 1.2, "c1")


def test_the_profile_cannot_change_during_an_evaluation():
    e = env()
    assert e.gate.authorize(prop("a", qty=0.1), e.broker).approved
    loose = HardRiskGate(e.db, dataclasses.replace(FTMO_200K, risk_per_trade=1_000), e.clock)
    r = loose.authorize(prop("b", qty=0.1), e.broker)
    assert not r.approved and r.code == "PROFILE_CHANGED"


# ── 15, 21, 22: aggregate risk, concurrency, duplicates ─────────────────────

def test_15_open_positions_together_never_exceed_1_percent():
    e = env()
    results = [execute(e, f"p{i}").status for i in range(6)]  # 485 each: 4 x 485 = 1,940; a 5th makes 2,425
    assert results[:4] == ["FILLED"] * 4 and results[4:] == ["BLOCKED"] * 2
    log = [json.loads(r["payload"]) for r in e.db.query("SELECT payload FROM risk_gate_log WHERE kind='DECISION' "
                                                         "AND approved=0")]
    assert {a["rejection_reason"] for a in log} == {"OPEN_RISK_LIMIT"}


def test_a_closed_position_frees_its_risk():
    e = env()
    for i in range(4):
        assert execute(e, f"p{i}").status == "FILLED"
    assert execute(e, "p4").status == "BLOCKED"
    e.broker.close(e.broker.positions()[0].id)
    assert execute(e, "p5").status == "FILLED"


def test_21_concurrent_requests_cannot_bypass_the_aggregate_limit():
    e = env()
    start = threading.Barrier(10)
    out = []

    def go(i):
        start.wait()
        out.append(execute(e, f"c{i}").status)
    threads = [threading.Thread(target=go, args=(i,)) for i in range(10)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert out.count("FILLED") == 4 and len(e.broker.positions()) == 4
    assert sum(x["max_loss"] for x in json.loads(e.db.one("SELECT value FROM risk_gate_state")["value"])
               ["ledger"].values()) <= 2_000


def test_22_duplicate_execution_requests_cannot_create_duplicate_positions():
    e = env()
    start = threading.Barrier(6)
    out = []

    def go():
        start.wait()
        out.append(execute(e, "same").status)
    threads = [threading.Thread(target=go) for _ in range(6)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert out.count("FILLED") == 1 and set(out) <= {"FILLED", "DUPLICATE"} and len(e.broker.positions()) == 1
    again = e.gate.authorize(prop("same"), e.broker)  # the gate itself refuses a decision it already authorised
    assert not again.approved and again.code == "DUPLICATE_REQUEST"


# ── 16-17: persistence and corruption ──────────────────────────────────────

def test_16_restarting_the_process_preserves_the_risk_lock(tmp_path):
    path = tmp_path / "gate.db"
    e = env(path=path)
    e.gate.observe(e.broker)
    set_balance(e, 189_000.0)
    e.broker._save()
    assert e.gate.authorize(prop("x", qty=0.1), e.broker).code == "DAILY_LOSS_LIMIT"
    e.db.set_kv("kill_switch", {"active": False})  # an operator clears the system switch, then restarts
    for day in range(1, 4):  # days later, after a "recovery": still locked
        e2 = env(path=path, t=T0 + day * 86_400)
        set_balance(e2, 205_000.0)
        r = e2.gate.authorize(prop(f"y{day}", qty=0.1), e2.broker)
        assert not r.approved and r.code == "RISK_LOCKED" and e2.gate.status()["state"] == "LOCKED"
    assert e2.gate.clear_kill(CLEAR_KILL_CONFIRMATION, "try") is False  # a lock is not a clearable kill
    with pytest.raises(PermissionError):
        e2.gate.reset_evaluation(e2.broker, "yes", "")  # no automatic or casual unlock


@pytest.mark.parametrize("tamper", [
    "UPDATE risk_gate_state SET value = replace(value, '\"lock\":{', '\"lock\":null,\"x\":{')",
    "UPDATE risk_gate_state SET value = '{not json'",
    "UPDATE risk_gate_state SET sha256 = 'deadbeef'",
    "DELETE FROM risk_gate_state",
])
def test_17_state_corruption_fails_closed_and_survives_restart(tamper, tmp_path):
    path = tmp_path / "gate.db"
    e = env(path=path)
    e.gate.observe(e.broker)
    set_balance(e, 189_000.0)
    e.broker._save()
    e.gate.authorize(prop("x", qty=0.1), e.broker)  # locked
    with e.db.tx() as c:
        c.execute(tamper)
    r = e.gate.authorize(prop("y", qty=0.1), e.broker)
    assert not r.approved and r.code == "STATE_CORRUPT"
    assert e.db.get_kv("kill_switch")["active"] is True
    e2 = env(path=path)
    assert e2.gate.authorize(prop("z", qty=0.1), e2.broker).code == "STATE_CORRUPT"
    assert e2.gate.status()["state"] == "FAULT"


def test_an_edited_but_re_checksummed_unlock_is_still_caught_by_the_log(tmp_path):
    from aitrader.memory.db import _canonical, _hash
    e = env()
    e.gate.observe(e.broker)
    set_balance(e, 189_000.0)
    e.gate.authorize(prop("x", qty=0.1), e.broker)
    st = json.loads(e.db.one("SELECT value FROM risk_gate_state")["value"])
    st["lock"], st["kill"] = None, None
    v = _canonical(st)
    with e.db.tx() as c:
        c.execute("UPDATE risk_gate_state SET value=?, sha256=?", (v, _hash("risk-gate", {"v": v})))
    assert e.gate.authorize(prop("y", qty=0.1), e.broker).code == "STATE_CORRUPT"


@pytest.mark.parametrize("acct", [{"balance": math.nan}, {"balance": -5.0}, {"balance": 0.0}])
def test_impossible_account_values_trip_the_kill_switch(acct):
    e = env()
    e.gate.observe(e.broker)
    e.broker.state.update(acct)
    r = e.gate.authorize(prop("x", qty=0.1), e.broker)
    assert not r.approved and r.code == "IMPOSSIBLE_ACCOUNT_STATE" and e.gate.status()["state"] == "KILLED"


def test_an_evaluation_starts_only_from_the_profile_s_reference_balance():
    e = env(balance=20_000.0)
    r = e.gate.authorize(prop("x", qty=0.1), e.broker)
    assert not r.approved and r.code == "EVALUATION_REFERENCE_MISMATCH" and e.broker.positions() == []


def test_only_an_explicit_reset_starts_a_new_evaluation():
    e = env()
    e.gate.observe(e.broker)
    set_balance(e, 189_000.0)
    e.gate.authorize(prop("x", qty=0.1), e.broker)
    with pytest.raises(PermissionError):  # the account must be flat at the reference again
        e.gate.reset_evaluation(e.broker, RESET_CONFIRMATION, "new evaluation")
    set_balance(e, 200_000.0)
    e.db.set_kv("kill_switch", {"active": False})
    run = e.gate.reset_evaluation(e.broker, RESET_CONFIRMATION, "new evaluation")["run_id"]
    assert e.gate.status()["state"] == "ACTIVE" and e.gate.status()["run_id"] == run
    assert e.gate.authorize(prop("y", qty=0.1), e.broker).approved


# ── 18: the daily reset ────────────────────────────────────────────────────

def test_18_the_day_resets_only_at_the_configured_time_in_the_configured_zone():
    e = env(t=T0 + 12 * 3600)  # 2026-01-13 22:00 UTC = 23:00 Prague
    e.gate.observe(e.broker)
    set_balance(e, 190_400.0)
    assert e.gate.authorize(prop("a"), e.broker).code == "DAILY_LOSS_LIMIT"  # worst case 189,915 <= 190,000
    e.clock.t = T0 + 12 * 3600 + 59 * 60 + 59  # 22:59:59 UTC: still the same Prague day
    assert e.gate.authorize(prop("b"), e.broker).code == "DAILY_LOSS_LIMIT"
    e.clock.t = T0 + 13 * 3600  # 23:00 UTC = 00:00 Prague: the new day's reference is 190,400
    r = e.gate.authorize(prop("c"), e.broker)
    assert r.approved and r.calc["daily_reference"] == 190_400
    # UTC midnight is not a reset; Prague midnight is, in winter (UTC+1) and in summer (UTC+2)
    g = e.gate
    assert g.day_id(T0 + 13 * 3600) == g.day_id(T0 + 14 * 3600 - 1) == g.day_id(T0 + 14 * 3600)
    summer = 1_783_893_600  # 2026-07-12 22:00 UTC = 00:00 Prague (CEST)
    assert g.day_id(summer - 1) != g.day_id(summer) and g.day_id(summer) == g.day_id(summer + 3600)


def test_a_utc_profile_resets_at_utc_midnight_only_because_it_says_so():
    e = env(profile=dataclasses.replace(FTMO_200K, name="UTC", reset_timezone="UTC"))
    midnight = (T0 // 86_400 + 1) * 86_400
    assert e.gate.day_id(midnight - 1) != e.gate.day_id(midnight)


# ── 19-20: risk never grows with results ───────────────────────────────────

def _size(equity, closed_r):
    spec = InstrumentSpec("EURUSD", 100_000, 0.01, 0.01, 50, 1.0)
    d = SimpleNamespace(id="s", decision="BUY", instrument="EURUSD", stop_loss=ASK - 0.0020, take_profit=ASK + 0.0040)
    acct = AccountState(equity=equity, balance=equity, day_start_equity=equity, peak_equity=max(equity, 200_000),
                        start_balance=200_000, week_start_equity=equity, closed_r=closed_r)
    v = RiskEngine(RiskLimits(hard=FTMO_200K, max_drawdown_pct=50)).evaluate(
        d, acct, spec, Quote("EURUSD", BID, ASK, T0), T0)
    assert v.approved, v.reasons
    return v


def test_19_a_losing_trade_never_increases_the_next_trade_s_risk():
    base = _size(200_000, [])
    after_loss = _size(199_500, [-1.0])
    after_streak = _size(198_500, [-1.0, -1.0, -1.0])
    assert after_loss.qty <= base.qty and after_streak.qty < base.qty
    assert after_streak.risk_amount <= base.risk_amount <= 500 + 1e-9
    e = env()  # and the gate's per-trade limit is a constant, not a function of the last result
    e.gate.observe(e.broker)
    set_balance(e, 199_500.0)
    assert e.gate.authorize(prop("x", qty=7.0), e.broker).code == "PER_TRADE_RISK"


def test_20_a_winning_trade_never_increases_the_risk_limit():
    base, rich = _size(200_000, []), _size(212_000, [1.0, 2.0, 1.5])
    assert rich.qty == base.qty and rich.risk_amount <= 500 + 1e-9  # 0.25% of 212,000 would be 530
    e = env()
    e.gate.observe(e.broker)
    set_balance(e, 212_000.0)
    assert e.gate.authorize(prop("x", qty=7.0), e.broker).code == "PER_TRADE_RISK"
    assert e.gate.profile.risk_per_trade == 500


def test_the_risk_engine_sizes_exactly_what_the_gate_will_accept():
    v = _size(200_000, [])
    per = loss_per_lot(FTMO_200K, stop_distance=0.0020, pip=0.0001, contract_size=100_000, value_per_price_unit=1.0)
    assert v.risk_amount == pytest.approx(v.qty * per["total"]) and v.risk_amount <= 500
    e = env()
    assert e.gate.authorize(prop("sized", qty=v.qty, stop=ASK - 0.0020), e.broker).approved


# ── invariants over random proposals ───────────────────────────────────────

def test_invariant_no_sequence_of_random_proposals_breaks_a_limit():
    rng = random.Random(20261007)
    e = env()
    for i in range(300):
        e.clock.t += rng.choice([1, 60, 3600])
        e.feed.move("EURUSD", 1.1 + rng.uniform(-0.002, 0.002))
        bid, ask, _ = e.feed.q["EURUSD"]
        side = rng.choice([1, -1])
        exe = ask if side > 0 else bid
        qty = rng.choice([0.01, 0.5, 1.0, 2.5, 5.0, 7.5, 12.0, rng.uniform(0, 20)])
        dist = rng.choice([0.0002, 0.0008, 0.002, 0.01, rng.uniform(-0.001, 0.02)])
        p = TradeProposal(f"r{i}", f"cr{i}", "EURUSD", side, qty, exe, exe - side * dist, exe + side * 0.03,
                          rng.choice([0.0, 0.00001, -0.00001]))
        r = e.gate.authorize(p, e.broker)
        if r.approved:
            assert r.calc["max_loss"] <= 500 + 1e-6 and r.calc["open_risk_after"] <= 2_000 + 1e-6
            assert r.calc["worst_case_equity"] > r.calc["daily_floor"]
            e.broker.place_market("EURUSD", side, qty, p.stop, p.target, p.client_id, permit=r.permit)
            e.gate.confirm(p.client_id, e.broker.positions()[-1].id)
        if rng.random() < 0.3 and e.broker.positions():
            e.broker.close(rng.choice(e.broker.positions()).id)
        st = json.loads(e.db.one("SELECT value FROM risk_gate_state")["value"])
        assert sum(x["max_loss"] for x in st["ledger"].values()) <= 2_000 + 1e-6
        assert len(e.broker.positions()) <= FTMO_200K.max_open_positions
    assert e.db.verify_chain("risk_gate_log")[0]


def test_a_malformed_financing_estimate_is_refused_not_raised():
    e = env()
    d = decision("swapbad")
    d.timestamp = e.clock()
    v = RiskVerdict("swapbad", True, qty=1.0, risk_amount=97, risk_pct=0.05, entry_ref=ASK, stop=ASK - 0.0008,
                    target=ASK + 0.003)
    r = e.ex.execute(d, v, meta={"swap_per_night": "a lot"})
    assert r.status == "BLOCKED" and "RISK_NOT_COMPUTABLE" in r.detail and e.broker.positions() == []


def test_the_service_profile_follows_the_data_source_quote_tolerance_and_refuses_bad_overrides():
    from aitrader.service.config import ServiceConfig, ServiceConfigError
    assert ServiceConfig.from_env({}).hard_profile.max_quote_age_s == 90  # Yahoo: the risk engine's 90 s, capped
    assert ServiceConfig.from_env({"DATA_SOURCE": "offline"}).hard_profile.max_quote_age_s == 30
    assert ServiceConfig.from_env({"RISK_MAX_QUOTE_AGE_S": "600"}).hard_profile.max_quote_age_s == 90  # capped
    own = ServiceConfig.from_env({"RISK_PROFILE_OVERRIDES": '{"max_quote_age_s": 15}'})
    assert own.hard_profile.max_quote_age_s == 15 and own.hard_profile.risk_per_trade == 500
    for bad in ('{"risk_per_trade": 5000}', '[1]', '{"risk_per_trad": 1}', "not json"):
        with pytest.raises(ServiceConfigError):
            ServiceConfig.from_env({"RISK_PROFILE_OVERRIDES": bad})
    with pytest.raises(ServiceConfigError, match="RISK_PROFILE"):
        ServiceConfig.from_env({"RISK_PROFILE": "FTMO-1M"})  # unknown: refused, never the default
    with pytest.raises(ServiceConfigError, match="PAPER_START_BALANCE"):
        ServiceConfig.from_env({"PAPER_START_BALANCE": "20000"})
