"""scripts/demo_desk.py end to end against the fake proxy: not configured, a full run, a refused demo check (the
kill switch, and later runs refusing), and a person's acts (clearing the switch; resuming only when no outcome is
unknown). Nothing reaches the network: Yahoo's bars are built, the broker is the fake."""

from __future__ import annotations

import json
from datetime import date

import pytest

from aitrader.memory.db import Database
from scripts import demo_desk as S
from tests.ctrader_kit import LOGIN, FakeTradingCTrader, env
from tests.unit.test_demo_desk import DETAILS, bar, month_end_bars

LIGHT = [{"symbolId": 101, "symbolName": "US500.cash", "baseAssetId": 50, "quoteAssetId": 1, "enabled": True}]


def fetch_for(bars):
    return lambda now: ({"US500": bars}, {}, [])


@pytest.fixture
def made():
    fakes = []
    yield fakes
    for f in fakes:
        f.close()


def fake(made, **kw):
    f = FakeTradingCTrader(symbols=LIGHT, details=DETAILS, prices={101: (5000.0, 5000.5)}, **kw)
    made.append(f)
    return f


def test_without_settings_it_reports_and_sends_nothing(tmp_path):
    calls = []
    rc = S.main(["--state", str(tmp_path)], env={}, connect=lambda *a: calls.append(a), fetch=lambda now: 1 / 0)
    st = json.loads((tmp_path / "state.json").read_text())
    assert rc == 0 and st["status"] == "NOT_CONFIGURED" and calls == []  # nothing fetched, nothing connected
    assert "CTRADER_ACCESS_TOKEN" in st["missing"] and "أسرار GitHub ناقصة" in (tmp_path / "REPORT.md").read_text()


def test_a_full_run_records_the_starting_balance_and_reports_without_secrets(made, tmp_path):
    f = fake(made)
    bars = month_end_bars(5000.0) + [bar(date(2026, 11, 13), 5000.0)]
    rc = S.main(["--state", str(tmp_path)], env=env(), connect=f.connect, fetch=fetch_for(bars))
    st = json.loads((tmp_path / "state.json").read_text())
    assert rc == 0 and st["status"] == "DONE" and st["start_balance"] == 200_000.0 and st["mapped"] == ["US500"]
    assert st["promoted"] is False  # no DEMO promotion in the repository yet: the entry is blocked, nothing sent
    assert not any(n == "ProtoOANewOrderReq" for n in f.names())
    db = Database(tmp_path / "demo.db")
    assert db.get_kv(S.START_KEY) == 200_000.0
    for p in (tmp_path / "state.json", tmp_path / "REPORT.md"):
        text = p.read_text()
        assert str(LOGIN) not in text and env()["CTRADER_ACCESS_TOKEN"] not in text


def test_a_refused_demo_check_trips_the_switch_and_a_person_clears_it(made, tmp_path):
    f = fake(made, accounts=[{"ctidTraderAccountId": 5550001, "isLive": True, "traderLogin": LOGIN}])
    bars = month_end_bars(5000.0) + [bar(date(2026, 11, 13), 5000.0)]
    rc = S.main(["--state", str(tmp_path)], env=env(), connect=f.connect, fetch=fetch_for(bars))
    st = json.loads((tmp_path / "state.json").read_text())
    assert rc == 1 and st["status"] == "REFUSED" and "LIVE" in st["why"]
    assert Database(tmp_path / "demo.db").get_kv("kill_switch")["active"] is True
    # a person clears it, by a hand-started run, with a reason that is kept
    f2 = fake(made)
    S.main(["--state", str(tmp_path), "--clear-kill-switch", "checked: the account is the demo one"], env=env(),
           connect=f2.connect, fetch=fetch_for(bars))
    ks = Database(tmp_path / "demo.db").get_kv("kill_switch")
    assert ks["active"] is False and ks["reason"] == "checked: the account is the demo one"


def test_a_pause_is_lifted_only_when_no_outcome_is_unknown(tmp_path):
    db = Database(tmp_path / "demo.db")
    db.set_kv("paused", True)
    db.query("INSERT INTO intents(id, decision_id, ts, symbol, side, status, payload, updated) "
             "VALUES ('c1', 'd1', 0, 'US500', 'BUY', 'UNKNOWN', '{}', 0)")
    acts = S.operator_acts(db, None, "looked at the account")
    assert acts == ["NOT resumed: 1 order(s) still have an unknown outcome"] and db.get_kv("paused") is True
    db.query("UPDATE intents SET status='FILLED' WHERE id='c1'")
    assert S.operator_acts(db, None, "settled")[0] == "resumed: settled" and db.get_kv("paused") is False
