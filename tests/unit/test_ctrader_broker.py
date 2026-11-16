"""The cTrader demo broker through the system's own write path (the hard risk gate's permits, the execution engine),
against a fake proxy that trades (tests/ctrader_kit.py): writes sent once and never again, an unknown outcome
resolved only by reading the account, the demo and swap-free checks repeated before each write, and no value
invented."""

from __future__ import annotations

import time

import pytest

from aitrader.broker.base import AmbiguousExecution, BrokerError, BrokerRejected
from aitrader.broker.ctrader.broker import CTraderBroker
from aitrader.broker.ctrader.client import Client
from aitrader.broker.ctrader.session import Credentials, open_session
from aitrader.broker.ctrader.transport import Transport
from aitrader.memory.db import Database
from aitrader.risk.hard_gate import HardRiskGate, TradeProposal
from aitrader.risk.profile import TRND1_PAPER_200K
from tests.ctrader_kit import FakeTradingCTrader, env, trader

CREDS, _ = Credentials.from_env(env())
LIGHT = [{"symbolId": 101, "symbolName": "US500.cash", "baseAssetId": 50, "quoteAssetId": 1},
         {"symbolId": 103, "symbolName": "GER40.cash", "baseAssetId": 51, "quoteAssetId": 2},
         {"symbolId": 110, "symbolName": "EURUSD", "baseAssetId": 2, "quoteAssetId": 1}]
DETAILS = {101: {"symbolId": 101, "digits": 2, "minVolume": 100, "stepVolume": 100, "maxVolume": 1_000_000,
                 "tradingMode": 0},
           103: {"symbolId": 103, "digits": 1, "minVolume": 100, "stepVolume": 100, "tradingMode": 0}}


class Clock:
    def __init__(self):
        self.t = int(time.time())

    def __call__(self):
        return int(time.time())


@pytest.fixture
def made():
    fakes = []
    yield fakes
    for f in fakes:
        f.close()


def broker_for(made, refusals=None, **kw):
    f = FakeTradingCTrader(symbols=LIGHT, details=DETAILS, prices={101: (5000.0, 5000.5), 103: (19000.0, 19001.0),
                                                                    110: (1.08, 1.0802)}, **kw)
    made.append(f)
    s = open_session(Client(Transport(connect=f.connect)), CREDS)
    db = Database(":memory:")
    db.set_kv("kill_switch", {"active": False})
    b = CTraderBroker(s, CREDS, {"US500": 101, "GER40": 103}, LIGHT, DETAILS, Clock(), write_timeout=1.0,
                      quote_wait=1.0, on_refusal=(refusals.append if refusals is not None else None))
    gate = HardRiskGate(db, TRND1_PAPER_200K, b.clock)
    b.attach_gate(gate)
    return f, b, gate


def permit(gate, b, symbol="US500", side=1, qty=4.0, stop=4700.0, cid="TRND-1:US500:2026-12:BUY"):
    q = b.quote(symbol)
    res = gate.authorize(TradeProposal(cid, cid, symbol, side, qty, q.ask if side > 0 else q.bid, stop, None), b)
    assert res.approved, res.reasons
    return res.permit


def count(f, name):
    return sum(1 for n in f.names() if n == name)


# ── reads ──

def test_account_equity_is_the_brokers_balance_plus_its_unrealized_pnl(made):
    f, b, _ = broker_for(made)
    a = b.account()
    assert (a.balance, a.equity, a.currency) == (200_000.0, 200_000.0, "USD")


def test_a_balance_without_its_digits_is_an_error_not_a_number(made):
    f, b, _ = broker_for(made, trader_rec={k: v for k, v in trader().items() if k != "moneyDigits"})
    with pytest.raises(BrokerError, match="moneyDigits"):
        b.account()


def test_spec_converts_the_quote_currency_with_the_brokers_own_pair_or_refuses(made):
    f, b, _ = broker_for(made)
    us, ger = b.spec("US500"), b.spec("GER40")
    assert (us.min_lot, us.lot_step, us.value_per_price_unit, us.tradable) == (1.0, 1.0, 1.0, True)
    assert ger.value_per_price_unit == pytest.approx(1.0801)  # EURUSD mid
    b.light[110] = {"symbolId": 110, "symbolName": "EURUSD", "baseAssetId": 9, "quoteAssetId": 1}
    assert b.spec("GER40") is None  # no listed pair converts EUR: nothing is sized


# ── orders ──

def test_an_order_goes_through_the_gate_once_and_its_fill_is_the_brokers(made):
    f, b, gate = broker_for(made)
    fill = b.place_market("US500", 1, 4.0, 4700.0, None, "TRND-1:US500:2026-12:BUY",
                          permit=permit(gate, b), meta={"rule": "TRND-1"})
    assert fill.price == 5000.5 and count(f, "ProtoOANewOrderReq") == 1
    sent = [x for n, x, _ in f.requests if n == "ProtoOANewOrderReq"][0]
    assert sent["volume"] == 400 and sent["orderType"] == 1 and sent["tradeSide"] == 1
    assert sent["relativeStopLoss"] == round((5000.5 - 4700.0) * 1e5)  # market orders take a relative stop
    assert sent["label"] == sent["clientOrderId"] == "TRND-1:US500:2026-12:BUY"
    (p,) = b.positions()
    assert (p.symbol, p.side, p.qty, p.stop, p.client_id) == ("US500", 1, 4.0, 4700.0, "TRND-1:US500:2026-12:BUY")


def test_without_the_gates_permit_nothing_is_sent(made):
    f, b, gate = broker_for(made)
    with pytest.raises(BrokerRejected):
        b.place_market("US500", 1, 4.0, 4700.0, None, "x", permit=None)
    assert count(f, "ProtoOANewOrderReq") == 0


def test_an_account_the_broker_now_marks_live_is_refused_before_the_order_and_trips_the_switch(made):
    refusals = []
    f, b, gate = broker_for(made, refusals=refusals)
    p = permit(gate, b)
    f.accounts[0]["isLive"] = True
    with pytest.raises(BrokerRejected, match="DEMO_CHECK"):
        b.place_market("US500", 1, 4.0, 4700.0, None, "TRND-1:US500:2026-12:BUY", permit=p)
    assert count(f, "ProtoOANewOrderReq") == 0 and refusals and "LIVE" in refusals[0]
    assert b.is_demo() is False


def test_an_account_no_longer_swap_free_is_refused_before_the_order(made):
    f, b, gate = broker_for(made)
    p = permit(gate, b)
    f.trader["swapFree"] = False
    with pytest.raises(BrokerRejected, match="SWAP_FREE"):
        b.place_market("US500", 1, 4.0, 4700.0, None, "TRND-1:US500:2026-12:BUY", permit=p)
    assert count(f, "ProtoOANewOrderReq") == 0


@pytest.mark.parametrize("mode,needle", [("reject", "ORDER_REJECTED"), ("order_error", "MARKET_CLOSED")])
def test_a_refused_order_is_a_rejection(made, mode, needle):
    f, b, gate = broker_for(made, order_mode=mode)
    with pytest.raises(BrokerRejected, match=needle):
        b.place_market("US500", 1, 4.0, 4700.0, None, "TRND-1:US500:2026-12:BUY", permit=permit(gate, b))
    assert count(f, "ProtoOANewOrderReq") == 1


def test_an_error_answer_to_an_order_is_a_rejection(made):
    f, b, gate = broker_for(made, errors={"ProtoOANewOrderReq": ("NOT_ENOUGH_MONEY", "")})
    with pytest.raises(BrokerRejected, match="NOT_ENOUGH_MONEY"):
        b.place_market("US500", 1, 4.0, 4700.0, None, "TRND-1:US500:2026-12:BUY", permit=permit(gate, b))


@pytest.mark.parametrize("mode", ["silent", "silent_fill"])
def test_an_unanswered_order_is_ambiguous_and_never_resent(made, mode):
    f, b, gate = broker_for(made, order_mode=mode)
    with pytest.raises(AmbiguousExecution, match="never resent"):
        b.place_market("US500", 1, 4.0, 4700.0, None, "TRND-1:US500:2026-12:BUY", permit=permit(gate, b))
    assert count(f, "ProtoOANewOrderReq") == 1
    # the only recovery: read the account by client id
    found = b.find_by_client_id("TRND-1:US500:2026-12:BUY")
    assert (found is not None) == (mode == "silent_fill")


def test_a_volume_that_is_not_a_whole_step_or_below_the_minimum_is_refused(made):
    f, b, gate = broker_for(made)
    for qty in (4.5, 0.5, 0.0):
        with pytest.raises(BrokerRejected, match="not a valid volume"):
            b._volume("US500", qty)
    assert b._volume("US500", 4.0) == 400


def test_a_price_already_through_the_stop_is_refused_before_sending(made):
    f, b, gate = broker_for(made)
    p = permit(gate, b)
    f.set_price(101, 4690.0, 4690.5)
    time.sleep(0.05)
    with pytest.raises(BrokerRejected, match="loss side"):
        b.place_market("US500", 1, 4.0, 4700.0, None, "TRND-1:US500:2026-12:BUY", permit=p)
    assert count(f, "ProtoOANewOrderReq") == 0


def test_an_order_that_differs_from_the_permit_is_refused(made):
    f, b, gate = broker_for(made)
    with pytest.raises(BrokerRejected, match="differs from what the gate approved"):
        b.place_market("US500", 1, 5.0, 4700.0, None, "TRND-1:US500:2026-12:BUY", permit=permit(gate, b))
    assert count(f, "ProtoOANewOrderReq") == 0


# ── stops ──

def _open(f, b, gate):
    fill = b.place_market("US500", 1, 4.0, 4700.0, None, "TRND-1:US500:2026-12:BUY", permit=permit(gate, b))
    return fill.position_id


def _stop_permit(gate, b, pid, stop):
    res = gate.authorize_stop(pid, stop, b)
    assert res.approved, res.line
    return res.permit


def test_a_stop_move_is_confirmed_by_reading_the_position(made):
    f, b, gate = broker_for(made)
    pid = _open(f, b, gate)
    gate.confirm("TRND-1:US500:2026-12:BUY", pid)
    held = b.modify_stop(pid, 4750.0, permit=_stop_permit(gate, b, pid, 4750.0))
    assert held == 4750.0 and count(f, "ProtoOAAmendPositionSLTPReq") == 1


@pytest.mark.parametrize("mode,outcome", [("silent_apply", 4750.0), ("silent", None)])
def test_an_unanswered_stop_move_is_settled_by_reading_never_by_resending(made, mode, outcome):
    f, b, gate = broker_for(made, amend_mode=mode)
    pid = _open(f, b, gate)
    gate.confirm("TRND-1:US500:2026-12:BUY", pid)
    p = _stop_permit(gate, b, pid, 4750.0)
    if outcome is None:
        with pytest.raises(AmbiguousExecution, match="never resent"):
            b.modify_stop(pid, 4750.0, permit=p)
    else:
        assert b.modify_stop(pid, 4750.0, permit=p) == outcome
    assert count(f, "ProtoOAAmendPositionSLTPReq") == 1


def test_a_refused_stop_move_is_a_rejection(made):
    f, b, gate = broker_for(made, amend_mode="reject")
    pid = _open(f, b, gate)
    gate.confirm("TRND-1:US500:2026-12:BUY", pid)
    with pytest.raises(BrokerRejected, match="TRADING_BAD_STOPS"):
        b.modify_stop(pid, 4750.0, permit=_stop_permit(gate, b, pid, 4750.0))


# ── closes ──

def test_a_close_reports_the_change_in_the_brokers_balance(made):
    f, b, gate = broker_for(made)
    pid = _open(f, b, gate)
    f.set_price(101, 5010.0, 5010.5)
    time.sleep(0.05)
    ct = b.close(pid, "TRND-1:US500:2026-12:BUY-close", reason="RULE")
    # (5010.0 - 5000.5) x 4 units = +38.0, less the broker's 3.00 commission
    assert ct.pnl == pytest.approx(35.0) and ct.gross_pnl == pytest.approx(38.0) and ct.reason == "RULE"
    assert ct.exit == 5010.0 and ct.qty == 4.0 and b.positions() == []
    assert count(f, "ProtoOAClosePositionReq") == 1


def test_an_unanswered_close_is_ambiguous_and_never_resent(made):
    f, b, gate = broker_for(made, close_mode="silent")
    pid = _open(f, b, gate)
    with pytest.raises(AmbiguousExecution):
        b.close(pid, "c")
    assert count(f, "ProtoOAClosePositionReq") == 1


def test_a_stop_out_while_away_is_read_from_the_deals_with_its_pnl_unknown_not_guessed(made):
    f, b, gate = broker_for(made)
    t0 = int(time.time())
    pid = _open(f, b, gate)
    f.stop_out(int(pid), 4700.0)
    (ct,) = b.closed_since(t0)
    assert (ct.position_id, ct.symbol, ct.side, ct.qty, ct.exit) == (pid, "US500", 1, 4.0, 4700.0)
    assert ct.pnl is None and ct.reason == "UNKNOWN"  # the first closing deal's balance before is not known
    assert ct.gross_pnl == pytest.approx((4700.0 - 5000.5) * 4)


def test_a_broker_without_a_gate_sends_nothing(made):
    f = FakeTradingCTrader(symbols=LIGHT, details=DETAILS, prices={101: (5000.0, 5000.5)})
    made.append(f)
    b = CTraderBroker(open_session(Client(Transport(connect=f.connect)), CREDS), CREDS, {"US500": 101}, LIGHT,
                      DETAILS, Clock(), write_timeout=1.0, quote_wait=1.0)
    with pytest.raises(BrokerRejected, match="NO_RISK_GATE"):
        b.place_market("US500", 1, 4.0, 4700.0, None, "x", permit=object())
    with pytest.raises(BrokerRejected, match="NO_RISK_GATE"):
        b.modify_stop("1", 4700.0, permit=object())
    assert count(f, "ProtoOANewOrderReq") == 0


def test_a_client_id_the_broker_already_holds_is_never_sent_again(made):
    f, b, gate = broker_for(made)
    p = permit(gate, b)
    f.positions[1] = {"positionId": 1, "tradeData": {"symbolId": 101, "volume": 400, "tradeSide": 1,
                                                     "label": "TRND-1:US500:2026-12:BUY"},
                      "positionStatus": 1, "swap": 0, "price": 5000.5}
    with pytest.raises(BrokerRejected, match="already used"):
        b.place_market("US500", 1, 4.0, 4700.0, None, "TRND-1:US500:2026-12:BUY", permit=p)
    assert count(f, "ProtoOANewOrderReq") == 0


def test_the_submission_check_refuses_after_a_failed_verdict(made):
    f, b, gate = broker_for(made)
    b._at_submission("x")  # the session's verdict stands
    b._verdict = False
    with pytest.raises(BrokerRejected, match="at submission"):
        b._at_submission("x")


def test_equity_moves_with_the_brokers_unrealized_pnl(made):
    f, b, gate = broker_for(made)
    _open(f, b, gate)
    f.set_price(101, 5100.0, 5100.5)
    time.sleep(0.05)
    a = b.account()
    assert a.balance == 200_000.0 and a.equity == pytest.approx(200_000.0 + (5100.0 - 5000.5) * 4)
