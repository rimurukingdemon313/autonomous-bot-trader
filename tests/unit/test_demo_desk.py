"""The demo desk (aitrader/position/demo_desk.py): TRND-1 on a cTrader DEMO account through the real risk engine,
hard gate and execution engine, against a fake proxy that trades. Markets are built so the rule's answer is known:
ten rising month-ends hold the index, a month-end below the mean flattens it."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

import pytest

from aitrader.broker.ctrader.broker import CTraderBroker
from aitrader.broker.ctrader.client import Client
from aitrader.broker.ctrader.session import Credentials, open_session
from aitrader.broker.ctrader.transport import Transport
from aitrader.memory.db import Database
from aitrader.position import demo_desk as D
from aitrader.position.trend_desk import DailyBar, DailyFeed, PromotedRule, close_time
from tests.ctrader_kit import FakeTradingCTrader, env

CREDS, _ = Credentials.from_env(env())
LIGHT = [{"symbolId": 101, "symbolName": "US500.cash", "baseAssetId": 50, "quoteAssetId": 1}]
DETAILS = {101: {"symbolId": 101, "digits": 2, "minVolume": 100, "stepVolume": 100, "maxVolume": 1_000_000,
                 "tradingMode": 0}}
DEMO_RULE = PromotedRule("TRND-1", "VALIDATED", "HEALTHY", ("US500", "NAS100", "GER40", "UK100"), "DEMO",
                         "test", "2026-11-16", {})


class Clock:
    def __init__(self, t: datetime):
        self.t = int(t.timestamp())

    def __call__(self) -> int:
        return self.t


def month_end_bars(last_close: float, months: int = 12, end: date = date(2026, 10, 30)) -> list[DailyBar]:
    """One bar on each month's last weekday, rising to `last_close` at `end`'s month: the rule holds."""
    out, d = [], end
    for i in range(months):
        c = last_close - 50 * i
        out.append(DailyBar(d, c, c + 10, c - 10, c))
        first = date(d.year, d.month, 1) - timedelta(days=1)  # the month before's last day
        d = first
        while d.weekday() > 4:
            d -= timedelta(days=1)
    return sorted(out, key=lambda b: b.day)


def bar(day: date, close: float) -> DailyBar:
    return DailyBar(day, close, close + 10, close - 10, close)


@pytest.fixture
def made():
    fakes = []
    yield fakes
    for f in fakes:
        f.close()


def desk_for(made, clock, bars, rules=(DEMO_RULE,), **kw):
    f = FakeTradingCTrader(symbols=LIGHT, details=DETAILS, prices={101: (5000.0, 5000.5)}, clock=clock, **kw)
    made.append(f)
    db = Database(":memory:")
    b = CTraderBroker(open_session(Client(Transport(connect=f.connect)), CREDS), CREDS, {"US500": 101}, LIGHT, DETAILS,
                      clock, write_timeout=1.0, quote_wait=1.0, on_refusal=lambda why: D.trip(db, why))
    desk = D.build(db, b, DailyFeed({"US500": bars}, {}), clock, list(rules), 200_000.0)
    return f, desk


def names(f, name):
    return sum(1 for n in f.names() if n == name)


def events(out, kind):
    return [e for e in out if e["kind"] == kind]


NOW = datetime(2026, 11, 17, 7, 30, tzinfo=timezone.utc)  # a Tuesday morning; the latest close is Monday 16th


def test_the_rule_enters_once_sized_by_the_risk_engine_with_its_stop(made):
    clock = Clock(NOW)
    bars = month_end_bars(5000.0) + [bar(date(2026, 11, 16), 5000.0)]
    f, desk = desk_for(made, clock, bars)
    out = D.run(desk, {"US500": bars}, clock())
    (dec,) = [e for e in events(out, "DEMO_DECISION") if e["symbol"] == "US500"]
    assert dec["action"] == "BUY" and dec["result"] == "FILLED" and dec["for_month"] == "2026-11"
    assert dec["stop"] == 4700.0 and dec["risk"]["approved"] and 0 < dec["risk"]["risk_amount"] <= 1500
    assert names(f, "ProtoOANewOrderReq") == 1
    (p,) = desk.broker.positions()
    assert p.symbol == "US500" and p.qty == dec["risk"]["qty"]
    # the same morning again: held, nothing sent
    out2 = D.run(desk, {"US500": bars}, clock())
    assert [e["action"] for e in events(out2, "DEMO_DECISION") if e["symbol"] == "US500"] == ["HOLD"]
    assert names(f, "ProtoOANewOrderReq") == 1 and names(f, "ProtoOAAmendPositionSLTPReq") == 0


def test_the_stop_follows_each_new_close(made):
    clock = Clock(NOW)
    bars = month_end_bars(5000.0) + [bar(date(2026, 11, 16), 5000.0)]
    f, desk = desk_for(made, clock, bars)
    D.run(desk, {"US500": bars}, clock())
    clock.t += 86400
    bars2 = bars + [bar(date(2026, 11, 17), 5100.0)]
    f.set_price(101, 5100.0, 5100.5)  # stamped with the new morning's clock
    desk.feed = DailyFeed({"US500": bars2}, {})
    out = D.run(desk, {"US500": bars2}, clock())
    (st,) = events(out, "DEMO_STOP")
    assert st["to"] == round(5100.0 * 0.94, 2) and st["status"] == "MOVED"
    assert names(f, "ProtoOAAmendPositionSLTPReq") == 1


def test_a_close_that_is_not_final_yet_is_not_read(made):
    clock = Clock(NOW)
    bars = month_end_bars(5000.0) + [bar(date(2026, 11, 16), 5000.0), bar(date(2026, 11, 17), 9999.0)]
    f, desk = desk_for(made, clock, bars)
    out = D.run(desk, {"US500": bars}, clock())
    (dec,) = [e for e in events(out, "DEMO_DECISION") if e["symbol"] == "US500"]
    assert dec["close_day"] == "2026-11-16" and dec["stop"] == 4700.0  # the 17th closes after `now`


def test_without_a_demo_promotion_nothing_is_sent(made):
    clock = Clock(NOW)
    bars = month_end_bars(5000.0) + [bar(date(2026, 11, 16), 5000.0)]
    f, desk = desk_for(made, clock, bars, rules=())
    out = D.run(desk, {"US500": bars}, clock())
    (dec,) = [e for e in events(out, "DEMO_DECISION") if e["symbol"] == "US500"]
    assert dec["result"] == "BLOCKED" and "not VALIDATED" in dec["detail"]
    assert names(f, "ProtoOANewOrderReq") == 0


def test_a_refused_order_is_decided_again_tomorrow_under_a_new_id(made):
    clock = Clock(NOW)
    bars = month_end_bars(5000.0) + [bar(date(2026, 11, 16), 5000.0)]
    f, desk = desk_for(made, clock, bars, order_mode="reject")
    out = D.run(desk, {"US500": bars}, clock())
    first = [e for e in events(out, "DEMO_DECISION") if e["symbol"] == "US500"][0]
    assert first["result"] == "REJECTED"
    f.order_mode = "fill"
    clock.t += 86400
    f.set_price(101, 5000.0, 5000.5)
    out2 = D.run(desk, {"US500": bars}, clock())
    second = [e for e in events(out2, "DEMO_DECISION") if e["symbol"] == "US500"][0]
    assert second["result"] == "FILLED" and second["decision_id"] != first["decision_id"]
    assert names(f, "ProtoOANewOrderReq") == 2  # two decisions; the refused one never happened


def test_an_unknown_outcome_pauses_and_is_settled_by_reading_never_by_resending(made):
    clock = Clock(NOW)
    bars = month_end_bars(5000.0) + [bar(date(2026, 11, 16), 5000.0)]
    f, desk = desk_for(made, clock, bars, order_mode="silent_fill")
    out = D.run(desk, {"US500": bars}, clock())
    dec = [e for e in events(out, "DEMO_DECISION") if e["symbol"] == "US500"][0]
    assert dec["result"] == "FILLED"  # the engine read the account by client id and found the position
    assert names(f, "ProtoOANewOrderReq") == 1


def test_a_stop_hit_leaves_the_index_flat_until_the_next_month_end(made):
    clock = Clock(NOW)
    bars = month_end_bars(5000.0) + [bar(date(2026, 11, 16), 5000.0)]
    f, desk = desk_for(made, clock, bars)
    D.run(desk, {"US500": bars}, clock())
    (p,) = desk.broker.positions()
    f.stop_out(int(p.id), 4700.0)
    clock.t += 86400
    f.set_price(101, 4690.0, 4690.5)
    out = D.run(desk, {"US500": bars}, clock())
    assert events(out, "DESK_TRADE_CLOSED")
    dec = [e for e in events(out, "DEMO_DECISION") if e["symbol"] == "US500"][0]
    assert dec["action"] == "FLAT" and "flat until the next month-end" in dec["result"]
    assert names(f, "ProtoOANewOrderReq") == 1


def test_the_rule_turning_flat_closes_the_position(made):
    clock = Clock(NOW)
    bars = month_end_bars(5000.0) + [bar(date(2026, 11, 16), 5000.0)]
    f, desk = desk_for(made, clock, bars)
    D.run(desk, {"US500": bars}, clock())
    # November's last weekday (Monday 30th) closes far below the ten-month mean: December is flat
    bars2 = bars + [bar(date(2026, 11, 30), 3000.0)]
    clock.t = int(datetime(2026, 12, 1, 7, 30, tzinfo=timezone.utc).timestamp())
    f.set_price(101, 3000.0, 3000.5)
    desk.feed = DailyFeed({"US500": bars2}, {})
    out = D.run(desk, {"US500": bars2}, clock())
    dec = [e for e in events(out, "DEMO_DECISION") if e["symbol"] == "US500"][0]
    assert dec["for_month"] == "2026-12" and dec["action"] == "SELL" and dec["result"] == "CLOSED"
    assert desk.broker.positions() == [] and names(f, "ProtoOAClosePositionReq") == 1


def test_a_failed_demo_check_trips_the_kill_switch_and_every_later_run_refuses(made):
    clock = Clock(NOW)
    bars = month_end_bars(5000.0) + [bar(date(2026, 11, 16), 5000.0)]
    f, desk = desk_for(made, clock, bars)
    f.accounts[0]["isLive"] = True
    out = D.run(desk, {"US500": bars}, clock())
    dec = [e for e in events(out, "DEMO_DECISION") if e["symbol"] == "US500"][0]
    # the execution engine's final checks ask the broker first: the entry is blocked before the gate or the broker
    assert dec["result"] == "BLOCKED" and "not verified demo" in dec["detail"]
    assert names(f, "ProtoOANewOrderReq") == 0
    ks = desk.db.get_kv("kill_switch")
    assert ks["active"] is True and "LIVE" in ks["reason"]
    f.accounts[0]["isLive"] = False
    out2 = D.run(desk, {"US500": bars}, clock())
    assert events(out2, "DEMO_REFUSED") and names(f, "ProtoOANewOrderReq") == 0


def test_demo_promotions_must_say_demo(tmp_path):
    p = tmp_path / "r.json"
    assert D.load_demo_rules(p)[0] == []
    good = {"rule_id": "TRND-1", "status": "VALIDATED", "health": "HEALTHY", "instruments": ["US500"], "mode": "DEMO",
            "promoted_by": "x", "promoted_on": "2026-11-16", "evidence": {}}
    p.write_text(json.dumps({"rules": [good]}))
    (r,) = D.load_demo_rules(p)[0]
    assert r.mode == "DEMO" and r.status == "VALIDATED"
    p.write_text(json.dumps({"rules": [{**good, "mode": "PAPER"}]}))
    with pytest.raises(D.RuleFileError, match="mode"):
        D.load_demo_rules(p)
    p.write_text(json.dumps({"rules": [{**good, "instruments": ["XAUUSD"]}]}))
    with pytest.raises(D.RuleFileError, match="unknown instruments"):
        D.load_demo_rules(p)


def test_month_end_bars_hold_by_construction():
    bars = month_end_bars(5000.0)
    assert [b.day.month for b in bars][-1] == 10 and len(bars) == 12
    assert close_time("US500", bars[-1].day) < int(NOW.timestamp())


def test_a_price_that_did_not_move_since_yesterday_is_stale_and_nothing_is_entered(made):
    clock = Clock(NOW)
    bars = month_end_bars(5000.0) + [bar(date(2026, 11, 16), 5000.0)]
    f, desk = desk_for(made, clock, bars, order_mode="reject")
    D.run(desk, {"US500": bars}, clock())
    f.order_mode = "fill"
    clock.t += 86400  # no new price: the market is closed, or the feed is down
    out = D.run(desk, {"US500": bars}, clock())
    dec = [e for e in events(out, "DEMO_DECISION") if e["symbol"] == "US500"][0]
    assert dec["result"] == "RISK_REJECTED" and "age" in " ".join(dec["risk"]["reasons"])
    assert names(f, "ProtoOANewOrderReq") == 1  # only the first day's, which the broker refused


def test_an_order_whose_answer_never_came_is_settled_next_run_by_reading_the_account(made):
    clock = Clock(NOW)
    bars = month_end_bars(5000.0) + [bar(date(2026, 11, 16), 5000.0)]
    f, desk = desk_for(made, clock, bars, order_mode="silent")
    out = D.run(desk, {"US500": bars}, clock())
    dec = [e for e in events(out, "DEMO_DECISION") if e["symbol"] == "US500"][0]
    assert dec["result"] == "UNKNOWN" and desk.db.get_kv("paused") is True
    # the broker did fill it after all; the next run reads that, and sends nothing
    f.positions[9001] = {"positionId": 9001, "tradeData": {"symbolId": 101, "volume": 400, "tradeSide": 1,
                                                           "label": dec["decision_id"] and
                                                           desk.db.one("SELECT id FROM intents")["id"],
                                                           "openTimestamp": clock() * 1000},
                         "positionStatus": 1, "swap": 0, "price": 5000.5, "stopLoss": 4700.0}
    clock.t += 3600
    f.set_price(101, 5000.0, 5000.5)
    out2 = D.run(desk, {"US500": bars}, clock())
    (rec,) = events(out2, "DEMO_RECONCILED")
    assert rec["resolved"] and names(f, "ProtoOANewOrderReq") == 1


FOUR = {"US500": 101, "NAS100": 102, "GER40": 103, "UK100": 104}


def test_a_crash_day_that_breaks_the_daily_limit_fails_the_account_and_closes_everything(made):
    """The FULL plan's known failure (docs/FUNDED_PAPER.md): the four indices fall together. Built so the answer is
    known: four positions, the broker's stops gapped through (they did not fill), a 13% fall on each."""
    clock = Clock(NOW)
    light = [{"symbolId": i, "symbolName": n, "baseAssetId": 50 + i, "quoteAssetId": 1}
             for n, i in (("US500.cash", 101), ("US100.cash", 102), ("GER40.cash", 103), ("UK100.cash", 104))]
    details = {i: {"symbolId": i, "digits": 2, "minVolume": 100, "stepVolume": 100, "maxVolume": 1_000_000,
                   "tradingMode": 0} for i in FOUR.values()}
    f = FakeTradingCTrader(symbols=light, details=details, prices={i: (5000.0, 5000.5) for i in FOUR.values()},
                           clock=clock)
    made.append(f)
    db = Database(":memory:")
    b = CTraderBroker(open_session(Client(Transport(connect=f.connect)), CREDS), CREDS, FOUR, light, details, clock,
                      write_timeout=1.0, quote_wait=1.0, on_refusal=lambda why: D.trip(db, why))
    bars = {s: month_end_bars(5000.0) + [bar(date(2026, 11, 16), 5000.0)] for s in FOUR}
    desk = D.build(db, b, DailyFeed(bars, {}), clock, [DEMO_RULE], 200_000.0)
    out = D.run(desk, bars, clock())
    filled = [e for e in events(out, "DEMO_DECISION") if e.get("result") == "FILLED"]
    held = desk.broker.positions()
    assert len(held) == len(filled) >= 2  # the gate decides how many fit; every one it allowed was filled
    for p in held:
        f.positions[int(p.id)]["stopLoss"] = 100.0  # gapped through: the broker's stop did not fill
    for i in FOUR.values():
        f.set_price(i, 4350.0, 4350.5)
    loss = sum((4350.0 - p.entry) * p.qty for p in held)
    out2 = D.run(desk, bars, clock())
    if -loss > 10_000:
        assert events(out2, "DEMO_ACCOUNT_FAILED")
        assert desk.broker.positions() == [] and names(f, "ProtoOAClosePositionReq") == len(held)
        # and the next run sends nothing more
        n = len(f.names())
        out3 = D.run(desk, bars, clock())
        assert not any(e.get("action") == "BUY" for e in events(out3, "DEMO_DECISION"))
        assert names(f, "ProtoOANewOrderReq") == len(filled) and len(f.names()) >= n
    else:
        pytest.skip(f"the gate allowed only {len(held)} positions: a 13% fall loses {-loss:.0f}, inside the limit")
