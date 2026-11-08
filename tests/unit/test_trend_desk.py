"""The trend desk (aitrader/position/trend_desk.py) on markets built so the answer is known: its monthly decision is
TRND-1's own; an entry is sized by the risk engine at $1,500 to its stop and passes the hard gate's permit; the stop
follows each close, 6% below it, through the gate; a day whose range crosses the stop closes the position there, and
the index waits for the next month-end; a month-end FLAT closes it by the rule; a holiday month-end switches at the next
close; an unpromoted rule trades nothing; a session is applied once; a day that breaches the limit at its intraday low
fails the account and closes it. The fake feed replaces the market only: the risk engine, the gate, the paper broker
and the execution engine are the production code."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

import scripts.funded_paper as FP
from aitrader.memory.db import Database
from aitrader.position import trend_desk as TD
from aitrader.position.trend_desk import (DailyBar, DailyFeed, DeskClock, PromotedRule, RuleFileError, TrendDesk,
                                          close_time, decision_for, is_last_weekday, sessions)

RULE = PromotedRule("TRND-1", "VALIDATED", "HEALTHY", TD.INDICES, "PAPER", "a test", "2026-11-08", {})


def weekdays(a: date, b: date) -> list[date]:
    out, d = [], a
    while d <= b:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def series(days: list[date], start: float, daily: float = 0.0004, shocks: dict | None = None) -> list[DailyBar]:
    """Closes rising `daily` a day; `shocks` {day: (open, high, low, close) as multiples of the previous close}."""
    out, p = [], start
    for d in days:
        if shocks and d in shocks:
            o, h, lo, c = (p * k for k in shocks[d])
            out.append(DailyBar(d, o, h, lo, c))
            p = c
            continue
        p *= 1 + daily
        out.append(DailyBar(d, p / (1 + daily / 2), p * 1.002, p * 0.998, p))
    return out


LEVELS = {"US500": 6000.0, "NAS100": 21000.0, "GER40": 22000.0, "UK100": 9000.0}


def market(until: date, shocks: dict | None = None, only: tuple[str, ...] = TD.INDICES, holidays: dict | None = None):
    days = weekdays(date(2025, 9, 1), until)
    bars = {s: series([d for d in days if d not in (holidays or {}).get(s, ())], LEVELS[s],
                      shocks=(shocks or {}).get(s)) for s in only}
    rates = {"EURUSD": {d: 1.25 for d in weekdays(date(2025, 8, 1), until)},
             "GBPUSD": {d: 1.30 for d in weekdays(date(2025, 8, 1), until)}}
    return bars, rates


def desk_for(bars, rates, rules=(RULE,), start=date(2026, 11, 9), db=None):
    feed = DailyFeed(bars, rates)
    first = min(close_time(s, start) for s in bars) - 1
    desk = TrendDesk.build(db or Database(":memory:"), feed, DeskClock(first), list(rules), "test rules")
    return desk, first


def replay(desk, bars, after, until_day: date) -> list[dict]:
    by_day = {s: {b.day: b for b in bs} for s, bs in bars.items()}
    until = max(close_time(s, until_day) for s in bars)
    out = []
    for t, d, syms in sessions(bars, after=after, until=until):
        out += desk.session(d, {s: by_day[s][d] for s in syms})
    return out


def kinds(events, kind, **match):
    return [e for e in events if e["kind"] == kind and all(e.get(k) == v for k, v in match.items())]


# ── the rule ──────────────────────────────────────────────────────────────


def test_its_monthly_decision_is_trnd1s_own_and_reads_only_the_months_before():
    days = weekdays(date(1995, 1, 2), date(2003, 12, 31))
    closes, p = {}, 100.0
    for i, d in enumerate(days):
        p *= 1.012 if (i // 60) % 3 else 0.985  # trends up and down, months long
        closes[d] = p
    gap = {d: c for d, c in closes.items() if (d.year, d.month) != (1999, 6)}
    for data in (closes, gap):
        theirs = FP.decisions(data)
        for y in range(1996, 2004):
            for m in range(1, 13):
                assert decision_for(data, (y, m))["hold"] == theirs.get((y, m)), (y, m)
    assert decision_for(gap, (1999, 7))["hold"] is None and decision_for(gap, (2000, 4))["hold"] is None
    later = {**closes, **{d + timedelta(days=0): c * 3 for d, c in closes.items() if d >= date(2001, 6, 1)}}
    assert decision_for(later, (2001, 6)) == decision_for(closes, (2001, 6))  # June's own closes are never read


def test_the_switch_day_is_the_months_last_weekday():
    assert is_last_weekday(date(2026, 11, 30)) and not is_last_weekday(date(2026, 11, 27))
    assert is_last_weekday(date(2027, 4, 30)) and is_last_weekday(date(2026, 10, 30))  # Friday the 30th, 31st Saturday
    assert not is_last_weekday(date(2026, 12, 30)) and is_last_weekday(date(2026, 12, 31))


# ── trading it ────────────────────────────────────────────────────────────


def test_a_held_index_is_entered_at_its_close_sized_by_the_risk_engine_with_a_gate_permit():
    bars, rates = market(date(2026, 11, 9))
    desk, first = desk_for(bars, rates)
    ev = replay(desk, bars, first, date(2026, 11, 9))
    buys = kinds(ev, "DESK_DECISION", action="BUY")
    assert [e["symbol"] for e in buys] == ["GER40", "UK100", "US500", "NAS100"]  # Europe closes first
    for e in buys:
        assert e["result"] == "FILLED" and e["edge_status"] == "VALIDATED"
        assert 1_450 < e["risk"]["risk_amount"] <= 1_500  # the risk engine's size: $1,500 all-in at the stop
    held = {p.symbol: p for p in desk.broker.positions()}
    for s, p in held.items():
        bar = bars[s][-1]
        assert p.stop == round(bar.close * 0.94, 2) and p.target is None
        spec = desk.broker.spec(s)
        notional = p.qty * spec.contract_size * spec.value_per_price_unit * p.entry
        assert 23_500 < notional < 25_500  # about $25,000: a quarter of half the account
    gate_log = desk.db.query("SELECT payload FROM risk_gate_log WHERE kind='DECISION'")
    assert sum(json.loads(r["payload"])["risk_gate_result"] == "APPROVED" for r in gate_log) == 4


def test_ger40_is_valued_in_euros_at_the_rate():
    bars, rates = market(date(2026, 11, 10))
    desk, first = desk_for(bars, rates)
    replay(desk, bars, first, date(2026, 11, 10))
    p = next(p for p in desk.broker.positions() if p.symbol == "GER40")
    q = desk.broker.quote("GER40")
    assert desk.broker.unrealised_by_position()[p.id] == pytest.approx((q.bid - p.entry) * p.qty * 1.25)


def test_the_stop_follows_each_close_6_percent_below_it_through_the_gate():
    bars, rates = market(date(2026, 11, 13))
    desk, first = desk_for(bars, rates)
    ev = replay(desk, bars, first, date(2026, 11, 13))
    p = next(p for p in desk.broker.positions() if p.symbol == "US500")
    assert p.stop == round(bars["US500"][-1].close * 0.94, 2)
    moves = kinds(ev, "DESK_STOP", symbol="US500")
    assert len(moves) == 4 and all(m["status"] == "MOVED" for m in moves)  # Tuesday to Friday, each close
    logged = desk.db.query("SELECT payload FROM risk_gate_log WHERE kind='STOP_MOVE'")
    assert len(logged) == 16 and all(json.loads(r["payload"])["approved"] for r in logged)


def test_a_day_through_the_stop_closes_it_there_and_the_index_waits_for_the_month_end():
    shocks = {"NAS100": {date(2026, 11, 18): (1.0, 1.001, 0.90, 0.95)}}  # the low 10% under the previous close
    bars, rates = market(date(2026, 12, 2), shocks=shocks)
    desk, first = desk_for(bars, rates)
    ev = replay(desk, bars, first, date(2026, 12, 2))
    stop = kinds(ev, "DESK_TRADE_CLOSED", symbol="NAS100")
    assert len(stop) == 1 and stop[0]["reason"] == "STOP"
    prev = next(b for b in bars["NAS100"] if b.day == date(2026, 11, 17)).close
    assert stop[0]["exit"] == pytest.approx(round(prev * 0.94, 2) - 0.1)  # the bid reached the stop: filled there, slipped
    assert -1_600 < stop[0]["pnl"] < -1_300 and stop[0]["r"] == pytest.approx(stop[0]["pnl"] / 1_493, rel=0.05)
    later = [e for e in kinds(ev, "DESK_DECISION", symbol="NAS100") if e["day"] > "2026-11-18"]
    assert [(e["day"], e["action"]) for e in later] == [("2026-11-30", later[0]["action"])]  # nothing before then
    assert later[0]["action"] == ("BUY" if later[0]["hold"] else "FLAT")


def test_a_gap_through_the_stop_fills_at_the_open():
    shocks = {"US500": {date(2026, 11, 18): (0.88, 0.90, 0.87, 0.89)}}  # opens 12% down
    bars, rates = market(date(2026, 11, 18), shocks=shocks)
    desk, first = desk_for(bars, rates)
    ev = replay(desk, bars, first, date(2026, 11, 18))
    t = kinds(ev, "DESK_TRADE_CLOSED", symbol="US500")[0]
    bar = next(b for b in bars["US500"] if b.day == date(2026, 11, 18))
    assert t["reason"] == "STOP" and t["exit"] == pytest.approx(bar.open - 0.25 - 0.1)  # the open, not the stop


def test_a_month_end_flat_closes_it_by_the_rule_at_that_close():
    falling = {d: (1.0, 1.0, 0.97, 0.975) for d in weekdays(date(2026, 11, 10), date(2026, 11, 27))}
    falling = {d: (1.0, 1.001, 0.97, 0.985) for d in falling}  # 1.5% a day for three weeks, never 6% in a day
    bars, rates = market(date(2026, 11, 30), shocks={"UK100": falling})
    desk, first = desk_for(bars, rates)
    ev = replay(desk, bars, first, date(2026, 11, 30))
    out = kinds(ev, "DESK_DECISION", symbol="UK100", day="2026-11-30")
    assert len(out) == 1 and out[0]["hold"] is False and out[0]["action"] == "SELL" and out[0]["result"] == "CLOSED"
    t = kinds(ev, "DESK_TRADE_CLOSED", symbol="UK100")
    assert len(t) == 1 and t[0]["reason"] == "RULE"
    assert t[0]["exit"] == pytest.approx(bars["UK100"][-1].close - 0.5 - 0.1)
    assert "UK100" not in {p.symbol for p in desk.broker.positions()}
    assert kinds(ev, "DESK_DECISION", symbol="US500", day="2026-11-30")[0]["action"] == "HOLD"  # no trade


def test_a_holiday_month_end_switches_at_the_next_close_one_day_late():
    falling = {d: (1.0, 1.001, 0.97, 0.985) for d in weekdays(date(2026, 11, 10), date(2026, 11, 27))}
    bars, rates = market(date(2026, 12, 2), shocks={"UK100": falling}, holidays={"UK100": (date(2026, 11, 30),)})
    desk, first = desk_for(bars, rates)
    ev = replay(desk, bars, first, date(2026, 12, 2))
    out = kinds(ev, "DESK_DECISION", symbol="UK100", for_month="2026-12")
    assert len(out) == 1 and out[0]["day"] == "2026-12-01" and out[0]["late"] is True
    assert out[0]["month_end"] == "2026-11-27" and out[0]["action"] == "SELL"  # the right month-end, a day later


def test_an_unpromoted_or_degraded_rule_trades_nothing_and_says_why():
    bars, rates = market(date(2026, 11, 9))
    for rules in ((), (replace(RULE, health="DEGRADED"),)):
        desk, first = desk_for(bars, rates, rules=rules)
        ev = replay(desk, bars, first, date(2026, 11, 9))
        buys = kinds(ev, "DESK_DECISION", action="BUY")
        assert len(buys) == 4 and all(e["result"] == "BLOCKED" for e in buys)
        assert all("not VALIDATED" in e["detail"] for e in buys)
        assert all(e["risk"]["risk_amount"] <= 500 for e in buys)  # and the engine would have sized it at 0.25%
        assert desk.broker.positions() == []


def test_a_session_is_applied_once_and_a_later_bar_changes_nothing_before_it(tmp_path):
    bars, rates = market(date(2026, 11, 20))
    db = Database(tmp_path / "desk.db")
    desk, first = desk_for(bars, rates, db=db)
    replay(desk, bars, first, date(2026, 11, 13))
    before = (desk.broker.account(), [(p.symbol, p.qty, p.entry, p.stop) for p in desk.broker.positions()],
              db.one("SELECT COUNT(*) AS n FROM intents")["n"])
    assert replay(desk, bars, first, date(2026, 11, 13)) == []  # the same sessions again: nothing
    # a restart on the same database, with more days and a different future, replays nothing already done
    more, _ = market(date(2026, 11, 20), shocks={"US500": {date(2026, 11, 19): (1.0, 1.0, 0.5, 0.5)}})
    again, _ = desk_for(more, rates, db=db)
    last = again.state()["last_session"]
    assert last == max(close_time(s, date(2026, 11, 13)) for s in TD.INDICES)
    again.clock.t = last  # the runner resumes its clock at the last session
    assert replay(again, more, first, date(2026, 11, 13)) == []
    assert (again.broker.account(), [(p.symbol, p.qty, p.entry, p.stop) for p in again.broker.positions()],
            db.one("SELECT COUNT(*) AS n FROM intents")["n"]) == before


def test_each_sessions_intraday_low_is_seen_by_the_gate_before_its_close():
    # every index 5.5% under the previous close at its low (above its 6% stop), back to -1% at the close
    dip = {date(2026, 11, 18): (1.0, 1.0, 0.945, 0.99)}
    bars, rates = market(date(2026, 11, 18), shocks={s: dip for s in TD.INDICES})
    desk, first = desk_for(bars, rates)
    ev = replay(desk, bars, first, date(2026, 11, 18))
    lows = kinds(ev, "DESK_INTRADAY_LOW", day="2026-11-18")
    assert [e["symbols"] for e in lows] == [["GER40", "UK100"], ["US500", "NAS100"]]
    obs = [json.loads(r["payload"]) for r in desk.db.query("SELECT payload FROM risk_gate_log ORDER BY seq")]
    assert not kinds(ev, "DESK_TRADE_CLOSED") and desk.gate.status()["state"] == "ACTIVE"
    us_low, us_close = lows[1]["equity"], desk.gate.status()["equity_conservative"]
    assert us_close - us_low == pytest.approx(0.045 * sum(p.qty * desk.broker.spec(p.symbol).contract_size
                                                           * desk.broker.spec(p.symbol).value_per_price_unit
                                                           * next(b for b in bars[p.symbol] if b.day == date(2026, 11, 17)).close
                                                           for p in desk.broker.positions() if p.symbol in ("US500", "NAS100")),
                                              rel=0.02)
    assert obs  # every observation is in the gate's own hash-chained log


def test_a_day_that_breaches_the_daily_limit_fails_the_account_and_closes_what_is_left():
    # three indices gap 15% down through their stops: about $11,000 in a day, more than the $10,000 limit
    gap = {date(2026, 11, 18): (0.85, 0.86, 0.84, 0.85)}
    bars, rates = market(date(2026, 11, 19), shocks={s: gap for s in ("US500", "NAS100", "GER40")})
    desk, first = desk_for(bars, rates)
    ev = replay(desk, bars, first, date(2026, 11, 19))
    failed = kinds(ev, "DESK_ACCOUNT_FAILED")
    assert len(failed) == 1 and failed[0]["day"] == "2026-11-18" and failed[0]["lock"]["code"] == "DAILY_LOSS_LIMIT"
    closed = {t["symbol"]: t["reason"] for t in kinds(ev, "DESK_TRADE_CLOSED")}
    assert closed == {"GER40": "STOP", "US500": "STOP", "NAS100": "STOP", "UK100": "FAILED"}
    assert desk.broker.positions() == [] and desk.gate.status()["state"] == "LOCKED"
    assert desk.broker.account().balance < 200_000 - 10_000
    assert not kinds(ev, "DESK_DECISION", day="2026-11-19")  # nothing more is traded


def test_the_promotion_file_is_strict_and_never_carries_a_size(tmp_path):
    good = {"rule_id": "TRND-1", "status": "VALIDATED", "health": "HEALTHY", "instruments": ["US500"], "mode": "PAPER",
            "promoted_by": "x", "promoted_on": "2026-11-08", "evidence": {}}
    for bad in ({**good, "risk_pct": 1.0}, {**good, "mode": "LIVE"}, {**good, "instruments": ["EURUSD"]},
                {k: v for k, v in good.items() if k != "health"}):
        (tmp_path / "r.json").write_text(json.dumps({"rules": [bad]}))
        with pytest.raises(RuleFileError):
            TD.load_promoted_rules(tmp_path / "r.json")
    assert TD.load_promoted_rules(tmp_path / "none.json")[0] == []
    rules, _ = TD.load_promoted_rules()  # the repository's own: the owner's promotion of TRND-1, paper only
    assert [(r.rule_id, r.status, r.health, r.mode) for r in rules] == [("TRND-1", "VALIDATED", "HEALTHY", "PAPER")]


def test_the_runner_waits_for_a_late_bar_and_writes_the_report(tmp_path):
    import scripts.trend_desk as R
    bars, rates = market(date(2026, 11, 11))
    bars["UK100"] = [b for b in bars["UK100"] if b.day < date(2026, 11, 11)]  # FTSE's Wednesday bar is late
    now = datetime(2026, 11, 11, 22, 40, tzinfo=timezone.utc)
    s = R.run(tmp_path, now, bars, rates)
    assert s["last_session"] == datetime.fromtimestamp(close_time("US500", date(2026, 11, 10)), timezone.utc).isoformat()
    assert all("2026-11-11" not in x for x in s["processed_this_run"])  # held back, not skipped
    full, _ = market(date(2026, 11, 11))
    s2 = R.run(tmp_path, now, full, rates)
    assert [x.split(" UTC")[0] for x in s2["processed_this_run"]] == ["2026-11-11 16:30", "2026-11-11 21:00"]
    text = (tmp_path / "REPORT.md").read_text()
    assert "PAPER ONLY · NOT REAL MONEY" in text and "بالعربي" in text and "| US500 |" in text
    assert json.loads((tmp_path / "state.json").read_text())["real_money"] is False


def test_a_malformed_bar_ends_its_series_there():
    import scripts.trend_desk as R
    day = date(2026, 11, 10)
    ts = [int(datetime(2026, 11, d, 14, 30, tzinfo=timezone.utc).timestamp()) for d in (9, 10, 11)]
    res = {"meta": {"exchangeTimezoneName": "America/New_York"}, "timestamp": ts,
           "indicators": {"quote": [{"open": [1.0, 1.0, 1.0], "high": [1.1, 0.9, 1.1], "low": [0.9, 0.95, 0.9],
                                     "close": [1.0, 1.0, 1.0]}]}}
    bars, problems = R.parse_bars("US500", res, datetime(2026, 11, 12, tzinfo=timezone.utc))
    assert [b.day for b in bars] == [date(2026, 11, 9)] and problems and str(day) in problems[0]


def test_a_conversion_rate_is_filed_under_its_own_london_day_never_the_day_before():
    import scripts.trend_desk as R
    summer = int(datetime(2026, 7, 14, 23, 0, tzinfo=timezone.utc).timestamp())  # 00:00 London on 15 July
    winter = int(datetime(2026, 11, 16, 0, 0, tzinfo=timezone.utc).timestamp())  # 00:00 London on 16 November
    res = {"meta": {"exchangeTimezoneName": "Europe/London"}, "timestamp": [summer, winter],
           "indicators": {"quote": [{"close": [1.17, 1.16]}]}}
    assert R.parse_rates(res) == {date(2026, 7, 15): 1.17, date(2026, 11, 16): 1.16}
    feed = DailyFeed({}, {"EURUSD": R.parse_rates(res)})
    assert feed.quote("EURUSD", int(datetime(2026, 7, 15, 21, 0, tzinfo=timezone.utc).timestamp())) is None
    assert feed.quote("EURUSD", int(datetime(2026, 7, 16, 0, 0, tzinfo=timezone.utc).timestamp())).bid < 1.17
