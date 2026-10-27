"""The dual-AI desk in the production runtime, PAPER_FORWARD, OpenRouter mocked (no request leaves the test):

    MARKET DATA -> CHART -> TRADER 1 -> TRADER 2 -> AGREE -> RISK ENGINE -> HARD GATE -> PAPER BROKER
                                                  -> DISAGREE -> NO TRADE (the debate in shadow only)

The market is a deterministic replay and the traders' answers are scripted, so the right result is known by
construction. Everything else is the real service: orchestrator, risk engine, gate, execution engine, paper
broker, forward ledger, learning records and the dashboard views. LIVE does not exist."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

import aitrader.service.runtime as runtime_mod
from aitrader.broker.paper import PaperBroker
from aitrader.data.bars import BarSeries
from aitrader.decision.edge_status import execution_route
from aitrader.learning import dual_ai_stats
from aitrader.memory.db import Database
from aitrader.risk.profile import PAPER_FORWARD_200K
from aitrader.service.config import ServiceConfig, ServiceConfigError
from aitrader.service.runtime import Runtime

from tests.openrouter_kit import DEBATE, KEY, TRADER, VISION, FakeOpenRouter, answer, client, packet_of
from .test_cadence import LiveLikeFeed, minute_bars
from .test_paper_forward import SYMS, close_one, cycles, pipeline
from .test_pipeline import START, market
from .test_service import Clock, _write_kb


def desk_reply(t1="BUY", t2="BUY", debate="BUY", target_atr=2.0, c1=80, c2=80):
    def reply(role, body):
        p = packet_of(body)
        q, atr = p["quote"], p["chart_marks"]["atr_h1"]
        if role == "trader1":
            return answer(t1, q["bid"], q["ask"], atr, confidence=c1, stop_atr=1.0, target_atr=target_atr)
        if role == "trader2":
            return answer(t2, q["bid"], q["ask"], atr, confidence=c2, stop_atr=1.0, target_atr=target_atr)
        return {"direction": debate, "confidence": 66, "reason": f"{debate} has the stronger structure"}
    return reply


def desk_runtime(tmp_path, monkeypatch, reply=None, mode="PAPER_FORWARD", clock=None):
    fake = FakeOpenRouter(reply or desk_reply())
    monkeypatch.setattr(runtime_mod, "OpenRouterClient", lambda cfg: client(fake))
    monkeypatch.setenv("DECISION_MODE", "dual_ai")
    if not (tmp_path / "kb").exists():
        _write_kb(tmp_path / "kb")
    data = {s: market(s, START, 24 * 7 * 20, i + 1, 1.30 if "JPY" not in s else 110.0) for i, s in enumerate(SYMS)}
    clock = clock or Clock(int(data["EURUSD"].available_at[2000]))
    lower = {}
    for s, h1 in data.items():
        mid = float(h1.mid_close[2000])
        b = minute_bars(s, clock.t - 300 * 60, [mid * 0.999] * 60, [mid * 1.001] * 60, mid)
        lower[(s, "M5")] = BarSeries.from_columns(s, "M5", "test", **{f: getattr(b, f) for f in (
            "bid_open", "bid_high", "bid_low", "bid_close", "ask_open", "ask_high", "ask_low", "ask_close",
            "ticks", "spread_mean", "spread_max")}, open_time=clock.t - 300 * 60 + 300 * np.arange(60))
    feed = LiveLikeFeed(data, lower)
    data_dir = tmp_path / "rt"
    data_dir.mkdir(parents=True, exist_ok=True)
    broker = PaperBroker(feed, clock, Database(data_dir / "aitrader.db"), start_balance=200_000)
    rt = Runtime(ServiceConfig(mode=mode, data_dir=str(data_dir), port=0, symbols=SYMS, dashboard_token="t",
                               decision_interval_min=5, symbols_per_cycle=1, hard_profile=PAPER_FORWARD_200K),
                 feed=feed, broker=broker, clock=clock, knowledge_dir=tmp_path / "kb")
    rt.broker.db = rt.db
    return rt, clock, fake


def test_agreement_becomes_a_paper_position_through_the_risk_engine_and_the_gate(tmp_path, monkeypatch):
    rt, clock, fake = desk_runtime(tmp_path, monkeypatch)
    cycles(rt, clock)
    (pos,) = rt.broker.positions()
    assert pos.symbol == "EURUSD" and pos.side == 1  # BUY
    trail = pipeline(rt)[-1]
    assert trail["stages"] == ["AI DECISION", "RISK APPROVED", "PAPER EXECUTED"] and trail["edge_status"] == "EXPERIMENTAL"
    row = rt.db.one("SELECT * FROM positions WHERE status='OPEN'")
    p = json.loads(row["payload"])
    assert p["source"] == "DUAL_AI" and p["paper_forward"] is True and p["max_loss"] <= 500  # the risk engine's size
    assert [c["role"] for c in fake.calls] == ["trader1", "trader2"]
    assert {c["model"] for c in fake.calls} == {VISION, TRADER}
    dec = json.loads(rt.db.one("SELECT payload FROM decisions WHERE id=?", (row["decision_id"],))["payload"])
    assert dec["family"] == "DUAL_AI" and dec["signal_class"] == "DUAL_AI" and dec["versions"]["dual_ai"]
    assert dec["ai"]["dual_ai"]["consensus"]["rule"] == "AGREE"


def test_a_disagreement_is_no_trade_and_both_sides_are_followed_forward_never_executed(tmp_path, monkeypatch):
    rt, clock, fake = desk_runtime(tmp_path, monkeypatch, desk_reply(t1="SELL", t2="BUY", debate="SELL"))
    cycles(rt, clock)
    assert rt.broker.positions() == [] and rt.db.one("SELECT * FROM positions") is None
    assert [c["role"] for c in fake.calls] == ["trader1", "trader2", "debate"]  # the debate, once, in shadow
    assert fake.calls[2]["model"] == DEBATE
    rows = [json.loads(r["payload"]) for r in rt.db.query("SELECT payload FROM forward_proposals")]
    pick = [r for r in rows if r["family"] == "DUAL_AI_DEBATE_PICK"]
    loser = [r for r in rows if r["family"] == "DUAL_AI_DEBATE_LOSER"]
    assert len(pick) == 1 and pick[0]["side"] == -1 and pick[0]["route"] == "COUNTERFACTUAL"
    assert len(loser) == 1 and loser[0]["side"] == 1 and loser[0]["route"] == "COUNTERFACTUAL"
    assert all(r["executed"] is False for r in pick + loser)
    assert [r for r in rows if r["family"] == "DUAL_AI"] == []  # nothing proposed for execution
    assert not [s for t in pipeline(rt) for s in t["stages"] if s == "PAPER EXECUTED"]
    rec = dual_ai_stats.record(rt.db)
    assert rec["decisions_by_rule"].get("DISAGREE") == 1 and rec["agreement_rate"] == 0.0
    assert rec["trades_taken"]["n"] == 0 and "debate_pick_if_taken" in rec
    last = rt.dual_ai()["last_analysis"]
    assert last["decision"] == "NO_TRADE" and last["consensus"]["debate_pick"] == "SELL"


def test_the_trade_is_sized_on_the_price_after_the_traders_answered_the_one_the_gate_verifies(tmp_path, monkeypatch):
    # found live (2026-10-13, EURJPY): the size came from the quote read before the models answered (minutes
    # earlier); the price had moved away from the stop, and the hard gate rightly refused $523 > $500
    moved = {"by": 0.0}
    base = desk_reply()

    def reply(role, body):
        out = base(role, body)
        if role == "trader2":  # the market moves 0.1 ATR away from the stop while the traders think
            moved["by"] = 0.1 * packet_of(body)["chart_marks"]["atr_h1"]
        return out
    rt, clock, _ = desk_runtime(tmp_path, monkeypatch, reply)
    feed, orig = rt.broker.feed, rt.broker.feed.quote

    def quote(symbol, now):
        q = orig(symbol, now)
        return None if q is None else type(q)(q.symbol, q.bid + moved["by"], q.ask + moved["by"], q.time)
    monkeypatch.setattr(feed, "quote", quote)
    cycles(rt, clock)
    trail = pipeline(rt)[-1]
    assert trail["stages"] == ["AI DECISION", "RISK APPROVED", "PAPER EXECUTED"], trail
    p = json.loads(rt.db.one("SELECT payload FROM positions WHERE status='OPEN'")["payload"])
    assert moved["by"] > 0 and p["max_loss"] <= 500 + 1e-6  # all-in, at the price it was sized and filled on


def test_a_trade_taken_is_followed_forward_under_shadow_exits_never_executed(tmp_path, monkeypatch):
    rt, clock, _ = desk_runtime(tmp_path, monkeypatch)
    cycles(rt, clock)
    (pos,) = rt.broker.positions()
    rows = [json.loads(r["payload"]) for r in rt.db.query("SELECT payload FROM forward_proposals")]
    (taken,) = [r for r in rows if r["family"] == "DUAL_AI"]
    shadows = sorted((r for r in rows if r["family"].startswith("DUAL_AI_EXIT_")), key=lambda r: r["family"])
    assert [r["exit_variant"] for r in shadows] == ["BE1R", "HOLD24H", "HOLD8H", "WIDE2X"]
    assert all(r["base_decision_id"] == taken["decision_id"] and r["route"] == "COUNTERFACTUAL"
               and r["executed"] is False for r in shadows)
    assert len(rt.broker.positions()) == 1  # nothing more was traded
    rec = dual_ai_stats.record(rt.db)
    assert set(rec["exits_in_shadow"]) >= {"BE1R", "HOLD24H", "WIDE2X", "HOLD8H"} and "LATE" in rec["taken_by_session"]


def test_a_trade_is_placed_on_trader_1s_levels_and_trader_2s_are_followed_in_shadow(tmp_path, monkeypatch):
    # dual-ai 1.10.0 (H3): Trader 2 surer, with its own levels; the trade is on Trader 1's, Trader 2's are measured
    base = desk_reply(c1=70)

    def reply(role, body):
        if role == "trader2":
            p = packet_of(body)
            q, atr = p["quote"], p["chart_marks"]["atr_h1"]
            return answer("BUY", q["bid"], q["ask"], atr, confidence=95, stop_atr=1.5, target_atr=3.0)
        return base(role, body)
    rt, clock, _ = desk_runtime(tmp_path, monkeypatch, reply)
    cycles(rt, clock)
    (pos,) = rt.broker.positions()
    rows = [json.loads(r["payload"]) for r in rt.db.query("SELECT payload FROM forward_proposals")]
    (taken,) = [r for r in rows if r["family"] == "DUAL_AI"]
    (t2,) = [r for r in rows if r["family"] == "DUAL_AI_T2_LEVELS"]
    assert t2["decision_id"] == taken["decision_id"] + ":t2-levels" and t2["route"] == "COUNTERFACTUAL"
    assert t2["executed"] is False and t2["side"] == taken["side"] == 1
    assert abs(t2["entry"] - t2["stop"]) == pytest.approx(1.5 * abs(taken["entry"] - taken["stop"]), rel=0.02)
    assert pos.stop == pytest.approx(taken["stop"]) and len(rt.broker.positions()) == 1  # Trader 1's, and one trade
    dec = json.loads(rt.db.one("SELECT payload FROM decisions WHERE id=?", (taken["decision_id"],))["payload"])
    assert dec["ai"]["dual_ai"]["consensus"]["levels_from"] == "trader1"
    assert dec["ai"]["dual_ai"]["consensus"]["more_confident"] == "trader2"
    rec = dual_ai_stats.record(rt.db)
    assert "trader2_levels_in_shadow" in rec and "every_agreement" in rec["trader2_levels_in_shadow"]


def test_the_traders_plan_for_8h_and_the_trade_stays_open_up_to_24h_never_past_the_friday_close(tmp_path,
                                                                                               monkeypatch):
    # dual-ai 1.7.0 (registered hypothesis H4): of 31 trades followed again in shadow, holding 24 h did better in 7
    # and worse in none; the 8 h exit had closed trades still running toward their targets
    from aitrader.agents.dual_ai import time_exit_minutes
    rt, clock, fake = desk_runtime(tmp_path, monkeypatch)
    cycles(rt, clock)
    row = rt.db.one("SELECT * FROM positions WHERE status='OPEN'")
    dec = json.loads(rt.db.one("SELECT payload FROM decisions WHERE id=?", (row["decision_id"],))["payload"])
    tf = dec["ai"]["dual_ai"]["chart"]["execution_timeframe"]
    assert dec["max_hold_minutes"] == time_exit_minutes(tf, dec["timestamp"]) == dec["ai"]["dual_ai"]["time_exit_minutes"]
    assert {packet_of(c["body"])["holding_time_minutes"] for c in fake.calls} == {dec["ai"]["dual_ai"]["hold_minutes"]}
    clock.t = int(row["opened"]) + dec["max_hold_minutes"] * 60 - 60
    rt.orch.time_exits(clock.t)
    assert rt.broker.positions()  # a minute before its time exit: still open
    clock.t += 60
    rt.orch.time_exits(clock.t)
    assert not rt.broker.positions()  # closed by its time exit, at its own time


def test_the_risk_engine_still_refuses_what_it_refuses(tmp_path, monkeypatch):
    # both traders agree, but reward:risk 0.8 is below the risk engine's minimum: blocked, never executed
    rt, clock, _ = desk_runtime(tmp_path, monkeypatch, desk_reply(target_atr=0.8))
    cycles(rt, clock)
    assert rt.broker.positions() == []
    trail = pipeline(rt)[-1]
    assert trail["stages"][-1] == "RISK REJECTED" and "reward_risk" in trail["reason"]
    view = rt.dual_ai()
    assert view["last_analysis"]["risk"]["approved"] is False


def test_an_open_position_on_the_pair_means_no_second_order_and_nothing_asked(tmp_path, monkeypatch):
    rt, clock, fake = desk_runtime(tmp_path, monkeypatch)
    rt.cfg = rt.cfg.__class__(**{**rt.cfg.__dict__, "symbols_per_cycle": 0})  # every pair, every cycle
    cycles(rt, clock)
    n_pos, n_calls = len(rt.broker.positions()), len(fake.calls)
    assert n_pos >= 1
    cycles(rt, clock)
    assert len(rt.broker.positions()) == n_pos  # duplicate protection: one position per pair
    held = {p.symbol for p in rt.broker.positions()}
    asked_again = [c for c in fake.calls[n_calls:] if packet_of(c["body"])["instrument"] in held]
    assert asked_again == []


def test_a_closed_trade_is_scored_per_trader_and_joins_the_desks_record(tmp_path, monkeypatch):
    rt, clock, _ = desk_runtime(tmp_path, monkeypatch, desk_reply(c1=85, c2=78))
    cycles(rt, clock)
    outcome, _ = close_one(rt, clock, "TARGET")
    ev = outcome["dual_ai"]
    assert ev["rule"] == "AGREE" and ev["trader1_correct"] is True and ev["trader2_correct"] is True
    assert ev["target_reached"] is True and ev["trader1_confidence"] == 85 and ev["models"]["trader1"] == VISION
    assert ev["trader1_input"] == "image"
    for k in ("net_r", "mfe_r", "mae_r", "regime", "desk_confidence"):
        assert k in ev
    rec = dual_ai_stats.record(rt.db)
    assert rec["trades_taken"]["n"] == 1 and rec["trades_taken"]["sample"] == "insufficient"
    assert rec["by_rule"]["AGREE"]["n"] == 1 and rec["trader1_hit_rate"]["rate"] == 1.0
    assert rec["by_trader1_input"]["image"]["n"] == 1 and rec["by_trader1_input"]["numbers"]["n"] == 0
    view = rt.dual_ai()
    assert view["performance"]["trades"] == 1 and view["performance"]["wins"] == 1


def journal_trade_as(rt, template: dict, *, rule, net_pnl, r, closed):
    """A closed desk trade booked in the journal as an earlier desk version recorded it (dual-ai 1.1.0 traded a
    debate's pick), or with no rule at all: the same append-only call the orchestrator makes."""
    o = {**template["outcome"], "net_pnl": net_pnl, "r": r, "closed": closed,
         "decision_id": f"old-{rule}-{closed}"}
    if rule is None:
        o.pop("dual_ai", None)
    else:
        o["dual_ai"] = {**o["dual_ai"], "rule": rule, "net_r": r}
    rt.db.append("trades", {"position_id": f"pos-{rule}-{closed}", "decision_id": o["decision_id"],
                            "symbol": o["symbol"], "r": r, "pnl": net_pnl, "payload": {**template, "outcome": o}})


def test_each_rule_is_its_own_figure_and_the_retired_debate_rule_is_shown_apart_never_deleted(tmp_path, monkeypatch):
    import sqlite3

    from scripts.paper_forward_shift import report_md
    rt, clock, _ = desk_runtime(tmp_path, monkeypatch)
    cycles(rt, clock)
    won, _ = close_one(rt, clock, "TARGET")  # the agreement rule, through the real pipeline: a win
    template = json.loads(rt.db.query("SELECT payload FROM trades")[-1]["payload"])
    journal_trade_as(rt, template, rule="DEBATE", net_pnl=-400.0, r=-0.8, closed=won["closed"] - 7200)
    journal_trade_as(rt, template, rule=None, net_pnl=-50.0, r=-0.1, closed=won["closed"] + 60)
    view = rt.dual_ai()
    perf, rules = view["performance"], view["performance_by_rule"]
    assert perf["rule"] == "AGREE" and perf["trades"] == 1 and perf["wins"] == 1 and perf["net_pnl"] == round(won["net_pnl"], 2)
    assert rules["DEBATE"]["trades"] == 1 and rules["DEBATE"]["net_pnl"] == -400.0 and rules["DEBATE"]["wins"] == 0
    assert rules["UNKNOWN"]["trades"] == 1 and set(rules) == {"AGREE", "DEBATE", "UNKNOWN"}  # never read as agreement
    assert view["performance_all_rules"]["trades"] == 3  # every desk trade is still counted somewhere
    assert [t["decision_id"] for t in view["recent_trades"]] == [won["decision_id"]]
    old = view["retired_rules"]["DEBATE"]
    assert old["stopped_in"] == "dual-ai-1.2.0" and old["performance"]["trades"] == 1
    assert [t["rule"] for t in old["trades"]] == ["DEBATE"] and old["trades"][0]["net_pnl"] == -400.0
    assert "NO TRADE" in view["rules"]["desk"] and "DEBATE picks" not in view["rules"]["desk"]
    pf = rt.paper_forward()
    assert pf["performance"]["overall"]["trades"] == 3  # the account's own figures keep every trade
    assert {k: b["trades"] for k, b in pf["performance"]["by_rule"].items()} == {"AGREE": 1, "DEBATE": 1, "UNKNOWN": 1}
    assert sorted(t["rule"] for t in pf["recent_trades"]) == ["AGREE", "DEBATE", "UNKNOWN"]
    md = report_md({**pf, "dual_ai": view}, {"started": "now", "decision_mode": "dual_ai"})
    head = md.split("## Paper account")[0]
    assert "## The rule that trades: a trade only when both AIs agree" in head and "| 1 (insufficient) | 1 | 0 |" in head
    assert "the old DEBATE rule, stopped in dual-ai-1.2.0" in head and "net $-400.00, 0 won" in head
    assert "rule could not be read: 1, net $-50.00" in head
    total = f"| ${pf['account']['total_pnl']:,.2f} |"  # the real account, as it is, after the rule that trades
    assert "| Account | Equity |" not in head and "| Account | Equity |" in md and total in md.split(head)[1]
    assert "| DEBATE |" in md and "| AGREE |" in md  # each closed trade carries its rule
    assert "Paid trial `paid-trial-2026-10-26`" in md and "(the key's own reading)" in md  # its spend is shown
    # who lost it: the two trades written straight into the journal passed no check (no verdict, no gate): ours
    b = pf["blame"]
    assert (b["trades"], b["losses"], b["market_losses"], b["ours_losses"], b["ours_loss_usd"]) == (3, 2, 0, 2, -450.0)
    assert "## Who lost it: the market or us" in md and "**the market 0**" in md and "**us 2**" in md
    assert "**WARNING: 2 trade(s) failed a check: a defect, not the market.**" in md
    assert "RULES: no approving risk verdict" in md and "| **us** |" in md
    won_row = next(t for t in pf["recent_trades"] if t["decision_id"] == won["decision_id"])
    assert won_row["blame"] == "MARKET"  # the trade through the real pipeline passes every check
    # the new account of the setup trading now: its own trades only; the ones before it apart; nothing moved
    per = pf["period"]
    assert per["start_balance"] == 200_000.0 and "## The new account: the setup trading now" in md
    assert per["performance"]["trades"] + per["before"]["performance"]["trades"] == 3
    assert per["equity"] == pytest.approx(200_000.0 + per["total_pnl"]) and "Before it, kept and apart" in md
    assert {t["period"] for t in pf["recent_trades"]} <= {per["id"], "before"}
    with pytest.raises(sqlite3.DatabaseError, match="immutable"):  # and the old rule's trades cannot be deleted
        with rt.db.tx() as c:
            c.execute("DELETE FROM trades WHERE decision_id LIKE 'old-DEBATE-%'")
    assert rt.db.verify_chain("trades")[0] and len(rt.db.query("SELECT 1 FROM trades")) == 3


def test_a_declared_adjustment_takes_the_retired_rules_trades_out_of_the_account_once_and_says_so(tmp_path,
                                                                                                  monkeypatch):
    from aitrader.broker import adjustments
    from scripts.paper_forward_shift import report_md
    rt, clock, _ = desk_runtime(tmp_path, monkeypatch)
    assert rt.health["paper_adjustments"][0]["status"] == "NOT_APPLICABLE"  # the declared trades: another journal
    cycles(rt, clock)
    won, _ = close_one(rt, clock, "TARGET")  # an agreement trade, through the real pipeline
    template = json.loads(rt.db.query("SELECT payload FROM trades")[-1]["payload"])
    journal_trade_as(rt, template, rule="DEBATE", net_pnl=-400.0, r=-0.8, closed=won["closed"] - 7200)
    debate = f"old-DEBATE-{won['closed'] - 7200}"
    declared = ({"id": "remove-debate", "rule": "DEBATE", "reason": "operator: remove the debate trade",
                 "decision_ids": (debate,)},)
    before = rt.broker.account().balance
    wrong = ({**declared[0], "id": "wrong", "decision_ids": (won["decision_id"],)},)
    partial = ({**declared[0], "id": "partial", "decision_ids": (debate, "not-in-this-journal")},)
    assert adjustments.apply(rt.broker, rt.db, wrong)[0]["status"] == "NOT_APPLIED"  # an agreement trade: never
    assert adjustments.apply(rt.broker, rt.db, partial)[0]["status"] == "NOT_APPLIED"  # all its trades or nothing
    assert rt.broker.account().balance == before and rt.broker.adjustments() == []
    assert adjustments.apply(rt.broker, rt.db, declared) == [{"id": "remove-debate", "status": "APPLIED", "amount": 400.0}]
    assert adjustments.apply(rt.broker, rt.db, declared)[0]["status"] == "ALREADY_APPLIED"  # once
    assert rt.broker.account().balance == pytest.approx(before + 400.0)
    (ev,) = [json.loads(e["payload"]) for e in rt.db.query("SELECT payload FROM events WHERE type='PAPER_ADJUSTMENT'")]
    assert ev["balance_before"] == pytest.approx(before) and ev["balance_after"] == pytest.approx(before + 400.0)
    assert ev["decision_ids"] == [debate] and ev["removed_pnl"] == -400.0
    monkeypatch.setattr(adjustments, "DECLARED", declared)
    clock.t += 60
    rt2, _, _ = desk_runtime(tmp_path, monkeypatch, clock=clock)  # a restart: the same account, never applied twice
    assert rt2.health["paper_adjustments"][0]["status"] == "ALREADY_APPLIED"
    assert rt2.broker.account().balance == pytest.approx(before + 400.0)
    pf = rt2.paper_forward()
    acct = pf["account"]
    assert acct["adjustments_total"] == 400.0 and acct["equity_before_adjustments"] == pytest.approx(acct["equity"] - 400)
    assert acct["today_pnl"] == pytest.approx(acct["equity"] - acct["day_reference"] - 400.0, abs=0.01)
    assert pf["performance"]["overall"]["trades"] == 1 and set(pf["performance"]["by_rule"]) == {"AGREE"}
    assert [t["decision_id"] for t in pf["removed_trades"]] == [debate]
    assert [t["decision_id"] for t in pf["recent_trades"]] == [won["decision_id"]]
    assert rt2.db.verify_chain("trades")[0] and len(rt2.db.query("SELECT 1 FROM trades")) == 2  # nothing deleted
    view = rt2.dual_ai()
    assert [a["id"] for a in view["retired_rules"]["DEBATE"]["removed_from_account"]] == ["remove-debate"]
    md = report_md({**pf, "dual_ai": view}, {"started": "now", "decision_mode": "dual_ai"})
    assert "removed from the paper account at the operator's request" in md
    assert "put back by a declared adjustment ($400.00)" in md and "It also holds" not in md
    assert "Equity includes declared operator adjustments of $400.00" in md
    status = rt2.gate.observe(rt2.broker)  # the hard gate reads the adjusted account: no kill, no lock
    assert status.get("kill") is None and status.get("lock") is None and status.get("state") == "ACTIVE"


def test_the_model_is_not_asked_for_a_trade_the_gate_would_refuse_for_open_risk_and_each_decision_has_a_budget(
        tmp_path, monkeypatch):
    # found live (2026-10-16): six trades the risk engine approved were refused by the hard gate (OPEN_RISK_LIMIT):
    # it values open positions to their stops from the current price, so profitable ones count for more
    rt, clock, fake = desk_runtime(tmp_path, monkeypatch)
    seen = []
    real = rt.orch.brain.dual_ai.decide

    def spy(ctx, *a, **kw):
        seen.append(ctx.decide_within_s)
        return real(ctx, *a, **kw)
    monkeypatch.setattr(rt.orch.brain.dual_ai, "decide", spy)
    monkeypatch.setattr(rt.execution.gate, "open_risk_room", lambda broker: 120.0)  # less than one trade's 500
    cycles(rt, clock)
    assert not fake.calls and not rt.broker.positions()
    last = rt.dual_ai()["last_analysis"]
    assert last["decision"] == "NO_TRADE" and "gate_open_risk" in last["reason"]
    monkeypatch.setattr(rt.execution.gate, "open_risk_room", lambda broker: 2_000.0)
    cycles(rt, clock)
    assert fake.calls and rt.broker.positions()  # room for it: asked, and taken
    assert seen and all(isinstance(s, (int, float)) and 0 < s <= 900 - 150 for s in seen)


class Calendar:
    """The economic calendar's view, as data.calendar.EconomicCalendar.for_symbol gives it: here a fixed schedule."""

    def __init__(self, minutes_away=None, status="FRESH"):
        self.minutes_away, self.status = minutes_away, status

    def for_symbol(self, symbol, t):
        events = [] if self.minutes_away is None else [
            {"minutes_away": self.minutes_away, "currency": symbol[3:], "title": "CPI y/y", "impact": "High"}]
        return {"feed": {"status": self.status, "reason": "HTTP 429" if self.status == "UNAVAILABLE" else None},
                "currencies": [symbol[:3], symbol[3:]], "events": None if self.status == "UNAVAILABLE" else events}


def test_around_a_high_impact_release_the_traders_are_not_asked_and_nothing_is_traded(tmp_path, monkeypatch):
    import dataclasses
    from aitrader.risk.engine import RiskEngine
    rt, clock, fake = desk_runtime(tmp_path, monkeypatch)
    rt.orch.risk = RiskEngine(dataclasses.replace(rt.orch.risk.limits, news_blackout_min=(30, 30), news_required=True))
    rt.orch.news = Calendar(minutes_away=12)  # a High-impact release for the pair in 12 minutes
    cycles(rt, clock)
    assert not fake.calls and not rt.broker.positions()
    assert "High-impact release" in rt.dual_ai()["last_analysis"]["reason"]
    rt.orch.news = Calendar(status="UNAVAILABLE")  # no readable calendar: event risk unknown, stand aside
    cycles(rt, clock)
    assert not fake.calls and not rt.broker.positions()
    rt.orch.news = Calendar(minutes_away=None)  # nothing scheduled near: asked, and traded
    cycles(rt, clock)
    assert fake.calls and rt.broker.positions()


def test_in_an_h1_range_the_agreement_is_refused_and_followed_forward_and_in_a_clear_trend_it_trades(tmp_path,
                                                                                                    monkeypatch):
    # the operator (2026-10-19): "do not trade into chop". Registered hypothesis H1: of the first 50 agreement trades,
    # the 23 opened in an H1 range won 30%, -0.24 R each; the 27 in a clear H1 trend won 63%, +0.23 R
    import dataclasses
    from aitrader.risk.engine import RiskEngine
    rt, clock, fake = desk_runtime(tmp_path, monkeypatch)
    rt.orch.risk = RiskEngine(dataclasses.replace(rt.orch.risk.limits, require_clear_structure="H1"))
    cycles(rt, clock)  # EURUSD first
    dec = json.loads(rt.db.one("SELECT payload FROM decisions WHERE symbol='EURUSD'")["payload"])
    assert dec["context"]["market_map"]["structure"]["H1"]["trend"] == "range (mixed swings)"  # the replay, checked
    trail = pipeline(rt)[-1]
    assert trail["symbol"] == "EURUSD" and trail["stages"] == ["AI DECISION", "RISK REJECTED"]
    assert "structure" in trail["reason"] and "range (mixed swings)" in trail["reason"]
    assert [c["role"] for c in fake.calls] == ["trader1", "trader2"] and not rt.broker.positions()  # asked, refused
    (prop,) = [json.loads(r["payload"]) for r in rt.db.query("SELECT payload FROM forward_proposals")]
    assert prop["family"] == "DUAL_AI" and prop["route"] == "REJECTED" and not prop["executed"]
    assert any("structure" in r for r in prop["risk_reasons"])  # followed forward: the rule stays measured
    cycles(rt, clock)  # GBPUSD next: the same desk, the same answers
    dec = json.loads(rt.db.one("SELECT payload FROM decisions WHERE symbol='GBPUSD'")["payload"])
    assert dec["context"]["market_map"]["structure"]["H1"]["trend"] == "up (HH+HL)"
    (pos,) = rt.broker.positions()
    assert pos.symbol == "GBPUSD" and pipeline(rt)[-1]["stages"] == ["AI DECISION", "RISK APPROVED", "PAPER EXECUTED"]


def test_the_dashboard_shows_the_desk_and_never_the_key(tmp_path, monkeypatch):
    rt, clock, _ = desk_runtime(tmp_path, monkeypatch)
    cycles(rt, clock)
    view = rt.dual_ai()
    assert view["active"] and view["live_trading"] is False and view["money"] == "NOT REAL MONEY"
    o = view["openrouter"]
    assert o["status"] == "READY" and o["vision_model"] == VISION and o["judge_model"] == TRADER
    assert o["verifier_model"] == DEBATE and o["key_hint"] == "…" + KEY[-4:]
    last = view["last_analysis"]
    assert last["trader1"]["direction"] == "BUY" and last["trader2"]["confidence"] == 80 and last["risk"]["approved"]
    assert last["trader1_input"] == "image" and last["version"].startswith("dual-ai-")  # the report's "(numbers)" mark
    assert view["open_positions"] and rt.dual_ai_chart("EURUSD")[:4] == b"\x89PNG"
    everything = json.dumps([view, rt.status(), rt.paper_forward(), rt.logs(), rt.events(0, 500)], default=str)
    assert KEY not in everything and KEY[:-4] not in everything
    raw = b"".join(f.read_bytes() for f in Path(rt.cfg.data_dir).rglob("*") if f.is_file())
    assert KEY.encode() not in raw  # nor in the database, the charts or anything else on disk


def test_dual_ai_is_refused_outside_paper_forward_and_live_does_not_exist(tmp_path, monkeypatch):
    with pytest.raises(ServiceConfigError):
        desk_runtime(tmp_path, monkeypatch, mode="PAPER")
    for env in ({"MODE": "LIVE"}, {"MODE": "PAPER_FORWARD", "LIVE_TRADING": "true"}, {"MODE": "DEMO"},
                {"MODE": "PAPER_FORWARD", "PAPER_MODE": "false"}):
        with pytest.raises(ServiceConfigError):
            ServiceConfig.from_env(env)
    # a model's trade executes only in PAPER_FORWARD; anywhere else it is SHADOW
    for mode in ("PAPER", "DEMO", "LIVE", "BACKTEST", "anything"):
        assert execution_route("EXPERIMENTAL", mode, True, ai_originated=True) == "SHADOW"
    assert execution_route("EXPERIMENTAL", "PAPER_FORWARD", False, ai_originated=True) == "EXECUTE"


def test_the_execution_engine_refuses_a_dual_ai_trade_on_anything_but_the_paper_broker(tmp_path, monkeypatch):
    rt, clock, _ = desk_runtime(tmp_path, monkeypatch)
    rt.execution.paper_forward = False  # as if the mode were not PAPER_FORWARD: the engine's own check
    cycles(rt, clock)
    assert rt.broker.positions() == []


def test_every_model_mode_is_a_model_signal_class_for_the_execution_engine():
    from aitrader.agents.brain import MODEL_MODES
    from aitrader.decision.edge_status import SIGNAL_CLASS
    from aitrader.execution.engine import MODEL_SIGNAL_CLASSES
    assert {SIGNAL_CLASS[m] for m in MODEL_MODES} <= MODEL_SIGNAL_CLASSES  # a new model mode cannot slip through
    assert "EVIDENCE" not in MODEL_SIGNAL_CLASSES and "EDGE" not in MODEL_SIGNAL_CLASSES


# ── time (orchestrator 1.22.0, risk 1.13.0): each pair decides at its own turn; the time rules are judged when the
#    position would open, after the traders answered ──

def slow_desk(minutes, clock_of):
    """The desk's scripted answers, each taking `minutes` of the clock."""
    base = desk_reply()

    def reply(role, body):
        clock_of().t += int(minutes * 60)
        return base(role, body)
    return reply


def test_each_pair_of_a_cycle_decides_at_its_own_turn_with_its_whole_budget(tmp_path, monkeypatch):
    # found live (2026-10-19): the pairs of a cycle are decided one after another; stamped with the cycle's start, the
    # second began already aged by the first one's model calls (13-14 min) and reached its traders with 0 s left
    box = {}
    rt, clock, fake = desk_runtime(tmp_path, monkeypatch, slow_desk(400 / 60, lambda: box["clock"]))
    box["clock"] = clock
    seen = []
    real = rt.orch.brain.dual_ai.decide

    def spy(ctx, *a, **kw):
        seen.append((ctx.symbol, ctx.t, ctx.decide_within_s))
        return real(ctx, *a, **kw)
    monkeypatch.setattr(rt.orch.brain.dual_ai, "decide", spy)
    clock.t += 300
    start = clock.t
    rt.orch.cycle(start, ["EURUSD", "GBPUSD"])
    (eu, gb) = seen
    assert eu[:2] == ("EURUSD", start) and gb[:2] == ("GBPUSD", start + 800)  # after EURUSD's two 400 s answers
    assert gb[2] == pytest.approx(900 - 150)  # its whole budget, not the 0 s EURUSD left of the cycle's
    assert [c["role"] for c in fake.calls] == ["trader1", "trader2", "trader1", "trader2"]  # both reached their traders


def test_a_decision_begun_before_a_closed_window_does_not_open_a_position_inside_it(tmp_path, monkeypatch):
    import dataclasses
    from datetime import datetime, timezone
    from aitrader.risk.engine import RiskEngine
    box = {}
    rt, clock, fake = desk_runtime(tmp_path, monkeypatch, slow_desk(4, lambda: box["clock"]))
    box["clock"] = clock
    u = datetime.fromtimestamp(clock.t + 300, timezone.utc)  # the next cycle's decision time
    m = u.hour * 60 + u.minute
    assert m + 60 <= 1440  # the window below stays inside the day
    rt.orch.risk = RiskEngine(dataclasses.replace(rt.orch.risk.limits, closed_utc_windows=((m + 5, m + 60),)))
    cycles(rt, clock)  # open when it began, so the traders are asked; closed 8 min later, when it would open
    assert [c["role"] for c in fake.calls] == ["trader1", "trader2"] and not rt.broker.positions()
    trail = pipeline(rt)[-1]
    assert trail["stages"] == ["AI DECISION", "RISK REJECTED"] and "trading_calendar" in trail["reason"]


class Release:
    """One High-impact release at a fixed time: the view gives minutes_away from the time it is asked about."""

    def __init__(self, at):
        self.at = at

    def for_symbol(self, symbol, t):
        return {"feed": {"status": "FRESH"}, "currencies": [symbol[:3], symbol[3:]],
                "events": [{"minutes_away": (self.at - t) // 60, "currency": symbol[3:], "title": "CPI y/y",
                            "impact": "High"}]}


def test_the_news_window_is_judged_when_the_position_would_open(tmp_path, monkeypatch):
    import dataclasses
    from aitrader.risk.engine import RiskEngine
    box = {}
    rt, clock, fake = desk_runtime(tmp_path, monkeypatch, slow_desk(4, lambda: box["clock"]))
    box["clock"] = clock
    rt.orch.risk = RiskEngine(dataclasses.replace(rt.orch.risk.limits, news_blackout_min=(30, 30), news_required=True))
    rt.orch.news = Release(clock.t + 300 + 35 * 60)  # 35 min after the decision begins: outside the window then
    cycles(rt, clock)  # the traders are asked; 8 min later the release is 27 min away
    assert [c["role"] for c in fake.calls] == ["trader1", "trader2"] and not rt.broker.positions()
    trail = pipeline(rt)[-1]
    assert trail["stages"] == ["AI DECISION", "RISK REJECTED"]
    assert "High-impact release" in trail["reason"] and "in 27 min" in trail["reason"]
