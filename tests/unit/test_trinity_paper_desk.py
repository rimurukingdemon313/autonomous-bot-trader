"""The TRINITY desk (aitrader/position/trinity_paper_desk.py) on built markets: it trades the package's map on paper
only, the risk engine sizes every position at the unvalidated cap, stops sit 3.2% below each rebalance close, a stop
leaves the instrument flat until the next rebalance, the rule decides every 15th trading day from the anchor and on
nothing later than the day it is at, and nothing opens for a rule nobody promoted for paper."""

import json
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

import pytest

from aitrader.broker.paper import PaperBroker, contract_size, pip_of
from aitrader.data.instruments import COMMODITY_CFDS, quote_currency
from aitrader.decision.edge_status import classify
from aitrader.memory.db import Database
from aitrader.position import trinity as T
from aitrader.position import trinity_paper_desk as D
from aitrader.position.trend_desk import DailyBar, DeskClock, PromotedRule, load_promoted_rules
from aitrader.risk import engine as E
from aitrader.risk.profile import TRINITY_PAPER_200K, pip_of as profile_pip

ROOT = Path(__file__).resolve().parents[2]
G = 0.0005  # a steady rise: 0.05% a trading day
BASE = {"QQQ": 400.0, "SPY": 500.0, "GLD": 300.0, "DBC": 25.0}
CFD0 = {"NAS100": 20_000.0, "US500": 6_000.0, "XAUUSD": 3_000.0, "USOIL": 70.0}


def _weekdays(first: date, n: int) -> list[date]:
    out, d = [], first
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


DAYS = _weekdays(date(2025, 1, 2), 260)
ANCHOR = DAYS[200]  # 200 trading days of history before it: thirteen grid rows


def market(days=DAYS, g=G):
    """Every fund and CFD rising steadily, the VIX calm at 14, TLT and UUP flat: TRND-1 PRO's simplest branch, so
    the package holds the equity indices, by construction."""
    signals = {a: {d: BASE[a] * (1 + g) ** i for i, d in enumerate(days)} for a in T.ASSETS}
    signals |= {"VIX": {d: 14.0 for d in days}, "TLT": {d: 100.0 for d in days}, "UUP": {d: 25.0 for d in days}}
    bars = {}
    for s, p0 in CFD0.items():
        bs, prev = [], p0
        for i, d in enumerate(days):
            c = p0 * (1 + g) ** i
            bs.append(DailyBar(d, prev, max(prev, c) * 1.001, min(prev, c) * 0.999, c))
            prev = c
        bars[s] = bs
    return signals, bars


RULE = PromotedRule(D.RULE_ID, "EXPERIMENTAL", "HEALTHY", D.INSTRUMENTS, "PAPER", "a test", "2026-11-21", {})


def build(tmp_path, bars, rules=(RULE,), anchor=ANCHOR):
    db = Database(tmp_path / "desk.db")
    feed = D.TrinityFeed(bars)
    return D.TrinityPaperDesk.build(db, feed, DeskClock(D.close_time(anchor) - 1), list(rules), "test", anchor=anchor)


def run_days(desk, signals, bars, days):
    by = {s: {b.day: b for b in bs} for s, bs in bars.items()}
    out = []
    for d in days:
        out += desk.session(d, {s: by[s][d] for s in D.INSTRUMENTS}, signals, DAYS)
    return out


def kinds(events, kind):
    return [e for e in events if e["kind"] == kind]


def test_the_desk_refuses_any_broker_but_the_paper_one(tmp_path):
    signals, bars = market()
    desk = build(tmp_path, bars)

    class NotPaper:
        name = "demo"
    with pytest.raises(ValueError, match="paper broker only"):
        replace(desk, broker=NotPaper())
    assert isinstance(desk.broker, PaperBroker) and desk.ex.allow_unvalidated is True


def test_it_buys_what_the_package_holds_sized_by_the_risk_engine_at_the_unvalidated_cap(tmp_path):
    signals, bars = market()
    desk = build(tmp_path, bars)
    ev = run_days(desk, signals, bars, [ANCHOR])
    reb = kinds(ev, "DESK_REBALANCE")
    assert len(reb) == 1 and reb[0]["decided"]
    want = sorted(T.CFD_OF[a] for a in T.ASSETS if reb[0]["weights"][a] > T.MIN_WEIGHT)
    assert {"NAS100", "US500"} <= set(want)  # TRND-1 PRO's branch holds both, by construction
    held = {p.symbol: p for p in desk.broker.positions()}
    assert sorted(held) == want
    close = {s: bars[s][DAYS.index(ANCHOR)].close for s in D.INSTRUMENTS}
    for e in kinds(ev, "DESK_DECISION"):
        if e["action"] != "BUY":
            continue
        assert e["edge_status"] == "EXPERIMENTAL" and e["result"] == "FILLED"
        assert e["risk"]["risk_pct"] <= E.UNVALIDATED_MAX_RISK_PCT + 1e-9  # 0.25%, whatever the weight
        assert e["stop"] == round(close[e["symbol"]] * (1 - T.STOP_REL), 2)
    for s, p in held.items():
        units = p.qty * contract_size(s)
        assert units * (p.entry - p.stop) <= 0.0025 * 200_000  # the loss at its stop, before costs
        assert units * p.entry < 0.10 * 200_000  # nowhere near the weight's own size (0.3 to 0.9 of the account)


def test_the_rule_decides_every_fifteenth_trading_day_from_the_anchor_and_never_before(tmp_path):
    signals, bars = market()
    desk = build(tmp_path, bars)
    before = DAYS[DAYS.index(ANCHOR) - 3:DAYS.index(ANCHOR)]
    assert kinds(run_days(desk, signals, bars, before), "DESK_REBALANCE") == []  # the account starts at the anchor
    desk = build(tmp_path / "b", bars)
    ev = run_days(desk, signals, bars, DAYS[DAYS.index(ANCHOR):DAYS.index(ANCHOR) + 46])
    days = [e["day"] for e in kinds(ev, "DESK_REBALANCE")]
    i0 = DAYS.index(ANCHOR)
    assert days == [str(DAYS[i0]), str(DAYS[i0 + 15]), str(DAYS[i0 + 30]), str(DAYS[i0 + 45])]


def test_a_held_position_keeps_its_size_and_its_stop_moves_only_at_a_rebalance(tmp_path):
    signals, bars = market()
    desk = build(tmp_path, bars)
    i0 = DAYS.index(ANCHOR)
    run_days(desk, signals, bars, DAYS[i0:i0 + 14])
    p0 = {p.symbol: p for p in desk.broker.positions()}
    assert all(p.stop == p0[s].stop for s, p in p0.items())
    ev = run_days(desk, signals, bars, [DAYS[i0 + 15]])
    p1 = {p.symbol: p for p in desk.broker.positions()}
    assert set(p1) == set(p0)
    close15 = {s: bars[s][i0 + 15].close for s in p1}
    for s, p in p1.items():
        assert p.qty == p0[s].qty  # no resizing
        assert p.stop == round(close15[s] * (1 - T.STOP_REL), 2)
    assert {e["action"] for e in kinds(ev, "DESK_DECISION") if e["symbol"] in p1} == {"HOLD"}


def test_a_stop_leaves_the_instrument_flat_until_the_next_rebalance(tmp_path):
    signals, bars = market()
    i0 = DAYS.index(ANCHOR)
    hit = DAYS[i0 + 5]
    nas = bars["NAS100"]
    b = nas[i0 + 5]
    nas[i0 + 5] = DailyBar(hit, b.open, b.high, b.close * 0.95, b.close)  # the day's low falls through the stop
    desk = build(tmp_path, bars)
    run_days(desk, signals, bars, DAYS[i0:i0 + 5])
    assert "NAS100" in {p.symbol for p in desk.broker.positions()}
    ev = run_days(desk, signals, bars, DAYS[i0 + 5:i0 + 15])
    closed = kinds(ev, "DESK_TRADE_CLOSED")
    assert [(c["symbol"], c["reason"]) for c in closed] == [("NAS100", "STOP")]
    assert "NAS100" not in {p.symbol for p in desk.broker.positions()}  # flat for the rest of the period
    ev = run_days(desk, signals, bars, [DAYS[i0 + 15]])
    buys = [e for e in kinds(ev, "DESK_DECISION") if e["symbol"] == "NAS100"]
    assert buys and buys[0]["action"] == "BUY" and buys[0]["result"] == "FILLED"


def test_a_weight_that_falls_to_nothing_closes_the_position(tmp_path):
    signals, bars = market()
    i0 = DAYS.index(ANCHOR)
    # from just after the anchor the VIX jumps and stays at 45: no branch of the package holds the equities then
    for d in DAYS[i0 + 1:]:
        signals["VIX"][d] = 45.0
    desk = build(tmp_path, bars)
    run_days(desk, signals, bars, DAYS[i0:i0 + 15])
    assert {"NAS100", "US500"} <= {p.symbol for p in desk.broker.positions()}
    ev = run_days(desk, signals, bars, [DAYS[i0 + 15]])
    w = kinds(ev, "DESK_REBALANCE")[0]["weights"]
    assert w["QQQ"] <= T.MIN_WEIGHT and w["SPY"] <= T.MIN_WEIGHT
    sells = {e["symbol"]: e for e in kinds(ev, "DESK_DECISION") if e["action"] == "SELL"}
    assert {"NAS100", "US500"} <= set(sells) and all(e["result"] == "CLOSED" for e in sells.values())
    assert not ({"NAS100", "US500"} & {p.symbol for p in desk.broker.positions()})


@pytest.mark.parametrize("rules", [(), (replace(RULE, status="RETIRED"),), (replace(RULE, health="DEGRADED"),)])
def test_nothing_opens_for_a_rule_not_promoted_for_paper(tmp_path, rules):
    signals, bars = market()
    desk = build(tmp_path, bars, rules=rules)
    ev = run_days(desk, signals, bars, [ANCHOR])
    assert desk.broker.positions() == []
    buys = [e for e in kinds(ev, "DESK_DECISION") if e["action"] == "BUY"]
    assert buys and all(e["result"] == "NOT_PROMOTED" for e in buys)


def test_the_rule_reads_nothing_after_the_day_it_is_at(tmp_path):
    signals, bars = market()
    a = build(tmp_path / "a", bars)
    wa = kinds(run_days(a, signals, bars, [ANCHOR]), "DESK_REBALANCE")[0]["weights"]
    later = {k: dict(v) for k, v in signals.items()}
    for k in later:
        for d in DAYS[DAYS.index(ANCHOR) + 1:]:
            later[k][d] *= 3.0
    b = build(tmp_path / "b", bars)
    wb = kinds(run_days(b, later, bars, [ANCHOR]), "DESK_REBALANCE")[0]["weights"]
    assert wa == wb


def test_a_session_is_applied_once(tmp_path):
    signals, bars = market()
    desk = build(tmp_path, bars)
    assert run_days(desk, signals, bars, [ANCHOR])
    assert run_days(desk, signals, bars, [ANCHOR]) == []


def test_a_crash_fails_the_account_and_closes_everything(tmp_path):
    signals, bars = market()
    i0 = DAYS.index(ANCHOR)
    crash = DAYS[i0 + 3]
    for s in D.INSTRUMENTS:
        b = bars[s][i0 + 3]
        # every instrument opens 45% down: each stop fills at that open, far below it
        bars[s][i0 + 3] = DailyBar(crash, b.open * 0.55, b.open * 0.56, b.open * 0.54, b.open * 0.55)
    desk = build(tmp_path, bars)
    run_days(desk, signals, bars, DAYS[i0:i0 + 3])
    assert len(desk.broker.positions()) >= 3
    ev = run_days(desk, signals, bars, [crash])
    st = desk.state()
    # three positions of about $15,000 each, filled 45% below: about $20,000 lost in a day, past the $10,000 limit
    assert 200_000 - desk.broker.account().equity > TRINITY_PAPER_200K.daily_loss_limit
    assert st["failed"]["lock"]["code"] == "DAILY_LOSS_LIMIT" and kinds(ev, "DESK_ACCOUNT_FAILED")
    assert desk.broker.positions() == []
    ev = run_days(desk, signals, bars, DAYS[i0 + 4:i0 + 16])  # the next rebalance included: nothing more opens
    assert desk.broker.positions() == [] and kinds(ev, "DESK_REBALANCE") == []


def test_each_session_audits_the_package_s_three_checks(tmp_path):
    signals, bars = market()
    desk = build(tmp_path, bars)
    ev = run_days(desk, signals, bars, DAYS[DAYS.index(ANCHOR):DAYS.index(ANCHOR) + 3])
    audits = kinds(ev, "DESK_AUDIT")
    assert len(audits) == 3
    for a in audits:
        assert a["checks"] == {"every_position_has_a_stop": True, "loss_at_stops_within_4pct": True,
                               "margin_within_equity": True}
        assert a["loss_at_stops_pct_of_start"] <= 4.0 and a["margin_usd"] <= a["equity"]
        assert all(p["stop"] is not None for p in a["positions"])


def test_the_committed_promotion_is_experimental_and_paper_only():
    rules, _ = load_promoted_rules()
    by = {r.rule_id: r for r in rules}
    t, trnd = by[D.RULE_ID], by["TRND-1"]
    assert (t.status, t.health, t.mode) == ("EXPERIMENTAL", "HEALTHY", "PAPER")
    assert set(t.instruments) == set(D.INSTRUMENTS)
    assert (trnd.status, trnd.instruments) == ("VALIDATED", ("US500", "NAS100", "GER40", "UK100"))
    dec = D.TrinityDecision("x", "BUY", "NAS100", 0, 1.0, ({"rule_id": D.RULE_ID},))
    assert classify(dec, "trend_desk", rules) == "EXPERIMENTAL"  # never VALIDATED from this file
    raw = json.loads((ROOT / "models" / "artifacts" / "promoted_rules.json").read_text())
    entry = next(r for r in raw["rules"] if r["rule_id"] == D.RULE_ID)
    assert not ({"size", "lots", "units", "notional", "risk_pct", "risk_amount", "leverage", "weights"} & set(entry))


def test_usoil_is_a_commodity_cfd_and_gold_keeps_its_metal_rules():
    assert contract_size("USOIL") == COMMODITY_CFDS["USOIL"].contract_size == 100.0
    assert pip_of("USOIL") == profile_pip("USOIL") == E.pip_size("USOIL") == 0.01
    assert quote_currency("USOIL") == "USD" and E.exposures("USOIL") == ("USOIL",)
    assert (contract_size("XAUUSD"), pip_of("XAUUSD"), E.exposures("XAUUSD")) == (100.0, 0.1, ("XAU", "USD"))
    assert (contract_size("EURUSD"), E.exposures("EURUSD")) == (100_000.0, ("EUR", "USD"))
