"""The trend desk's permanent ledger and its paper-trading report (scripts/desk_ledger.py), driven through the desk's
own runner on markets built so that every answer is known in advance. The ledger only reads the record: these tests
check that it books every trade with costs that add up, keeps the daily figures apart from the cumulative ones, never
records a session twice, never hides an intraday fall, never invents a figure, and never stops the desk when it fails."""

from __future__ import annotations

import csv
import json
from datetime import date, datetime, timezone

import scripts.desk_ledger as DL
import scripts.trend_desk as R
from aitrader.memory.db import Database
from aitrader.position.trend_desk import close_time
from tests.unit.test_trend_desk import market

START = 200_000.0


def at(day: date, h: int = 22, m: int = 40) -> datetime:
    return datetime(day.year, day.month, day.day, h, m, tzinfo=timezone.utc)


def record(tmp_path, kind: str) -> list[dict]:
    db = Database(tmp_path / "desk.db")
    return [json.loads(r["payload"]) | {"_ref": r["ref"]}
            for r in db.query("SELECT payload, ref FROM events WHERE type=? ORDER BY seq", (kind,))]


def rows(tmp_path) -> list[dict]:
    with open(tmp_path / "ledger.csv") as f:
        return list(csv.DictReader(f))


def perf_of(tmp_path):
    """The ledger and the performance the report was written from, rebuilt from the same desk.db."""
    import scripts.trend_desk as runner
    from aitrader.position.trend_desk import DailyFeed, DeskClock, TrendDesk, load_promoted_rules
    db = Database(tmp_path / "desk.db")
    st = db.get_kv(runner.STATE_KEY)
    rules, note = load_promoted_rules()
    bars, rates = market(date(2026, 12, 31))
    desk = TrendDesk.build(db, DailyFeed(bars, rates), DeskClock(st["last_session"]), rules, note)
    led = DL.ledger(db, desk)
    return led, DL.performance(led, START)


# ── the record ───────────────────────────────────────────────────────────


def test_each_session_is_recorded_once_and_a_rerun_records_nothing_more(tmp_path):
    bars, rates = market(date(2026, 11, 11))
    s = R.run(tmp_path, at(date(2026, 11, 11)), bars, rates)
    eq, lows = record(tmp_path, "DESK_EQUITY"), record(tmp_path, "DESK_INTRADAY_LOW")
    assert len(s["processed_this_run"]) == 6 and len(eq) == 6 == len(lows)  # Europe and the US, three days
    assert [(e["day"], e["symbols"]) for e in eq] == [(e["day"], e["symbols"]) for e in lows]
    assert eq[-1]["equity"] == s["account"]["equity"]  # the last record is the account the desk reports
    assert len(eq[-1]["positions"]) == 4 and eq[-1]["gross_exposure_usd"] > 0
    R.run(tmp_path, at(date(2026, 11, 11), 23, 50), bars, rates)  # the same day again: nothing new to apply
    assert len(record(tmp_path, "DESK_EQUITY")) == 6
    db = Database(tmp_path / "desk.db")
    from aitrader.position.trend_desk import DailyFeed, DeskClock, TrendDesk, load_promoted_rules
    rules, note = load_promoted_rules()
    t = close_time("US500", date(2026, 11, 11))
    desk = TrendDesk.build(db, DailyFeed(bars, rates), DeskClock(t), rules, note)
    assert DL.record_session(db, desk, t, date(2026, 11, 11), ["US500", "NAS100"]) is None  # already there
    assert len(record(tmp_path, "DESK_EQUITY")) == 6


def test_every_trade_is_booked_with_its_signal_size_and_costs_that_add_up_to_its_net(tmp_path):
    # Every index is bought at the 9 November close; on the 12th the S&P 500 opens 10% down, through its 6% stop.
    gap = {"US500": {date(2026, 11, 12): (0.90, 0.905, 0.88, 0.89)}}
    bars, rates = market(date(2026, 11, 13), shocks=gap)
    s = R.run(tmp_path, at(date(2026, 11, 13)), bars, rates)
    closed = record(tmp_path, "DESK_TRADE_CLOSED")
    assert [(c["symbol"], c["reason"]) for c in closed] == [("US500", "STOP")]
    led = rows(tmp_path)
    assert [(r["instrument"], r["status"]) for r in led] == [("US500", "CLOSED"), ("GER40", "OPEN"),
                                                             ("UK100", "OPEN"), ("NAS100", "OPEN")]
    t = led[0]
    g, sp, cm, sl, fi, net = (float(t[k]) for k in ("gross_pnl", "spread", "commission", "slippage", "financing",
                                                     "net_pnl"))
    assert net == closed[0]["pnl"] < -1_500  # a gap through the stop loses more than the risk: shown, not hidden
    assert abs(g - sp - cm - sl - fi - net) < 0.01 and t["reconciles"] == "True"
    assert fi == 0.0 and sp > 0 and cm > 0 and sl > 0  # swap-free; every other cost paid and itemized
    assert t["strategy"] == "TRND-1" and "BUY for 2026-11" in t["signal"] and "ten month-end" in t["signal"]
    assert t["direction"] == "LONG" and t["opened"].startswith("2026-11-09 21:00") and t["closed"].startswith("2026-11-12")
    assert 1_450 < float(t["risk_usd"]) <= 1_500 and 0 < float(t["entry_leverage"]) < 0.2
    assert float(t["entry_notional_usd"]) > 20_000
    for r in led[1:]:
        assert r["net_pnl"] == "" and r["open_pnl"] != "" and r["gross_pnl"] == ""  # an open trade has no booked net
    led2, perf = perf_of(tmp_path)
    assert perf["closed_trades"] == 1 and perf["lost"] == 1 and perf["won"] == 0
    assert perf["realized_net"] == round(net, 2) and perf["costs"]["financing"] == 0.0
    # the account's change is exactly what was booked plus what is open: nothing added, nothing left out
    assert abs(perf["net_since_start"] - (perf["realized_net"] + perf["unrealized"])) < 0.02
    assert perf["equity"] == s["account"]["equity"]
    # The entry day loses too: bought at the ask with slippage and marked at the bid, it pays its entry costs at once.
    assert [d["period"] for d in perf["losing_days"]] == ["2026-11-09", "2026-11-12"]
    entry_day = perf["losing_days"][0]
    assert -200 < entry_day["net"] < 0 and entry_day["opened"] == 4
    text = (tmp_path / "TRADING_REPORT.md").read_text()
    days_line = next(x for x in text.splitlines() if x.startswith("- **Days:**"))
    assert "2026-11-09 -$" in days_line and "2026-11-12 -$" in days_line and "| 1 | CLOSED | US500 | LONG |" in text


def test_daily_figures_are_kept_apart_from_the_cumulative_ones_and_the_months_chain(tmp_path):
    bars, rates = market(date(2026, 12, 3))
    R.run(tmp_path, at(date(2026, 12, 3)), bars, rates)
    led, perf = perf_of(tmp_path)
    days, months = perf["daily"], perf["monthly"]
    eq = record(tmp_path, "DESK_EQUITY")
    closes = {}
    for e in eq:
        closes[e["day"]] = e["equity"]
    prev = START
    for d in days:  # each day: its own close less the day before's, never a running total
        assert d["start"] == prev and d["end"] == closes[d["period"]] and abs(d["net"] - (d["end"] - prev)) < 0.01
        prev = d["end"]
    assert [m["period"] for m in months] == ["2026-11", "2026-12"] and months[1]["start"] == months[0]["end"]
    assert abs(sum(d["net"] for d in days) - perf["net_since_start"]) < 0.05
    assert abs(sum(m["net"] for m in months) - perf["net_since_start"]) < 0.02
    assert months[0]["target_progress"] == round(months[0]["net"] / 4_000, 4)
    text = (tmp_path / "TRADING_REPORT.md").read_text()
    assert "| 2026-12 (in progress) |" in text and "| 2026-11 |" in text
    daily_part = text.split("## Daily")[1].split("## Cumulative")[0]
    assert "2026-12-03" in daily_part and "Starting equity" not in daily_part


def test_the_drawdown_counts_every_intraday_low_even_when_each_day_closes_up(tmp_path):
    # The S&P 500 falls 5% intraday on 11 November (not through its 6% stop) and closes up: no losing day.
    dip = {"US500": {date(2026, 11, 11): (1.0, 1.001, 0.95, 1.0005)}}
    bars, rates = market(date(2026, 11, 12), shocks=dip)
    R.run(tmp_path, at(date(2026, 11, 12)), bars, rates)
    _, perf = perf_of(tmp_path)
    assert not record(tmp_path, "DESK_TRADE_CLOSED")
    assert [d["period"] for d in perf["losing_days"]] == ["2026-11-09"]  # only the entry costs; the dip day closes up
    assert perf["max_drawdown_usd"] > 1_000  # about 5% of a ~$25,000 position, seen at the low
    dip_day = next(d for d in perf["daily"] if d["period"] == "2026-11-11")
    assert dip_day["net"] > 0 and dip_day["drawdown_usd"] > 1_000
    closes_only = [START] + [e["equity"] for e in record(tmp_path, "DESK_EQUITY")]
    assert DL._drawdown(closes_only)[0] < 200 < perf["max_drawdown_usd"]  # at the closes alone it would be hidden


def test_research_and_backtest_figures_never_enter_the_paper_figures(tmp_path):
    bars, rates = market(date(2026, 11, 10))
    R.run(tmp_path, at(date(2026, 11, 10)), bars, rates)
    text = (tmp_path / "TRADING_REPORT.md").read_text()
    assert text.startswith("# Trend desk: paper-trading performance")
    assert "PAPER TRADING · NOT REAL MONEY · NOT A BACKTEST" in text and "بالعربي" in text
    paper, apart = text.split("## Kept apart")
    for research in ("0.785", "3.4%", "28,038", "TRND-1-H", "replay"):
        assert research not in paper and research in apart
    assert "Backtest (descriptive, not a test)" in apart and "Validated out-of-sample" in apart
    assert "$1,500" in paper and "$10,000" in paper and "$20,000" in paper  # the limits, read from the profile
    assert "never a quota" in paper


# ── nothing invented, nothing blocking ───────────────────────────────────


def test_a_trade_whose_costs_do_not_add_up_is_flagged_and_an_unknown_cost_is_never_taken_as_zero():
    good = {"gross_pnl": 100.0, "spread": 2.0, "commission": 7.0, "slippage": 1.0, "financing": 0.0, "net_pnl": 90.0}
    assert DL._reconciles(good) is True
    assert DL._reconciles({**good, "net_pnl": 95.0}) is False
    assert DL._reconciles({**good, "financing": None}) is None
    base = dict.fromkeys(DL.CSV_COLUMNS) | good | {"status": "CLOSED", "instrument": "US500", "direction": "LONG",
                                                   "opened": "2026-11-09 21:00 UTC", "closed": "2026-11-10 21:00 UTC",
                                                   "signal": "TRND-1 BUY for 2026-11", "exit_reason": "STOP"}
    led = {"rows": [base | {"position": "P9", "net_pnl": 95.0, "reconciles": False},
                    base | {"position": "P10", "financing": None, "reconciles": None}],
           "snaps": [], "lows": [], "points": []}
    perf = DL.performance(led, START)
    assert perf["not_reconciled"] == ["P9"] and perf["costs"]["financing"] is None  # unknown, not $0.00
    text = DL.report(perf, led, {}, at(date(2026, 11, 10)))
    assert "Trades whose costs do not add up to their net:** P9" in text and "financing unknown" in text


def test_before_the_first_session_the_trading_report_invents_nothing(tmp_path):
    bars, rates = market(date(2026, 11, 6))
    R.run(tmp_path, at(date(2026, 11, 8), 19, 0), bars, rates)
    text = (tmp_path / "TRADING_REPORT.md").read_text()
    assert "no session yet" in text and "$200,000.00" in text and "none yet" in text
    import re
    for bad in ("None", "nan", "inf", "unknown"):
        assert not re.search(rf"\b{bad}\b", text), bad
    assert rows(tmp_path) == [] and (tmp_path / "equity.csv").read_text().count("\n") == 1


def test_a_ledger_failure_never_stops_the_desk_and_is_said(tmp_path, monkeypatch):
    bars, rates = market(date(2026, 11, 10))

    def broken(*a, **k):
        raise RuntimeError("disk full")
    monkeypatch.setattr(DL, "session_payload", broken)
    s = R.run(tmp_path, at(date(2026, 11, 10)), bars, rates)
    assert len(s["processed_this_run"]) == 4 and len(s["positions"]) == 4  # the desk traded as it would have
    assert any("equity was not recorded" in p and "disk full" in p for p in s["problems"])
    text = (tmp_path / "TRADING_REPORT.md").read_text()
    assert "Sessions with no equity record" in text and "2026-11-10 US500,NAS100" in text
    monkeypatch.setattr(DL, "write", broken)
    (tmp_path / "ledger.csv").write_text("stale\n")
    s = R.run(tmp_path, at(date(2026, 11, 10), 23, 0), bars, rates)
    assert (tmp_path / "REPORT.md").exists() and (tmp_path / "state.json").exists()
    assert "NOT WRITTEN" in (tmp_path / "TRADING_REPORT.md").read_text()
    assert not (tmp_path / "ledger.csv").exists()  # nothing left that looks current
