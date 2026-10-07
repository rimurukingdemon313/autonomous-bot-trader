"""PAPER_FORWARD (docs/PAPER_FORWARD.md): the system's own decisions, a model's included, become real simulated
paper positions through the unchanged chain: decision -> risk engine -> hard gate -> paper broker. They are
managed, closed, costed, recorded and learned from. Real money is never involved.

The market is a deterministic replay. The language model is a scripted transport whose answer is known, so the
correct result is known by construction. Everything between them is the production runtime: orchestrator, risk
engine, gate, execution engine, paper broker, forward ledger and dashboard view."""

from __future__ import annotations

import dataclasses
import json

import numpy as np
import pytest

import aitrader.service.runtime as runtime_mod
from aitrader.broker.paper import PaperBroker
from aitrader.data.bars import BarSeries
from aitrader.decision.edge_status import execution_route
from aitrader.execution.engine import ExecutionEngine
from aitrader.learning import paper_metrics, taxonomy
from aitrader.learning.forward import partition
from aitrader.llm.provider import LLMClient, LLMConfig
from aitrader.memory.db import Database
from aitrader.memory.trade_memory import TradeMemory
from aitrader.risk.engine import RiskVerdict
from aitrader.risk.hard_gate import HardRiskGate
from aitrader.risk.profile import FTMO_200K, PAPER_FORWARD_200K
from aitrader.service.config import ServiceConfig, ServiceConfigError
from aitrader.service.runtime import Runtime

from .test_cadence import LiveLikeFeed, minute_bars
from .test_pipeline import START, market
from .test_service import Clock, _write_kb

SYMS = ("EURUSD", "GBPUSD", "USDJPY")


def buy_reply(user, stop_atr=1.0, target_atr=1.5, **extra):
    ask, atr = user["quote"]["ask"], user["timeframes"]["H1"]["atr14"]
    return {"action": "BUY", "timeframe": "M5", "stop": ask - stop_atr * atr, "target": ask + target_atr * atr,
            "max_hold_hours": 1, "thesis": "scripted M5 long", "invalidation": "stop", "memory_used": "none",
            "confidence": 0.9, **extra}


def pf_runtime(tmp_path, monkeypatch, decide=buy_reply, mode="PAPER_FORWARD", profile=PAPER_FORWARD_200K,
               data_dir=None, clock=None):
    """A PAPER_FORWARD runtime whose language model answers with `decide(user_packet)`."""
    def transport(url, headers, body, timeout):
        system, user = body["messages"][0]["content"], json.loads(body["messages"][1]["content"])
        if "reviewing one of YOUR OWN" in system:
            reply = {"what_happened": "closed", "was_it_a_mistake": False}
        elif "holds this open paper position" in system:
            reply = {"action": "HOLD", "reason": "let it work"}
        else:
            reply = decide(user)
        return {"choices": [{"message": {"content": json.dumps(reply)}}]}

    monkeypatch.setattr(runtime_mod, "LLMClient",
                        lambda cfg: LLMClient(LLMConfig("openai_compatible", "https://x.test/v1", "k", "m1"), transport))
    if not (tmp_path / "kb").exists():
        _write_kb(tmp_path / "kb")
    monkeypatch.setenv("DECISION_MODE", "llm_trader")
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
    data_dir = data_dir or tmp_path / "rt"
    data_dir.mkdir(parents=True, exist_ok=True)
    # as in production (runtime._connect): the paper account lives in the service's database and is restored from it
    broker = PaperBroker(feed, clock, Database(data_dir / "aitrader.db"), start_balance=200_000)
    rt = Runtime(ServiceConfig(mode=mode, data_dir=str(data_dir), port=0, symbols=SYMS,
                               dashboard_token="t", decision_interval_min=5, symbols_per_cycle=1, hard_profile=profile),
                 feed=feed, broker=broker, clock=clock, knowledge_dir=tmp_path / "kb")
    rt.broker.db = rt.db
    return rt, clock, feed


def cycles(rt, clock, n=1):
    for _ in range(n):
        clock.t += 300
        rt.run_cycle(decide=True)


def pipeline(rt):
    return [json.loads(r["payload"]) for r in rt.db.query("SELECT payload FROM events WHERE type='PIPELINE' ORDER BY seq")]


def bar_through(rt, symbol, low, high):
    """A completed bar after the position opened, with the given bid range."""
    t = rt.clock()
    half = 0.00005
    return {"open_time": t, "close_time": t + 60, "bid_open": (low + high) / 2, "bid_high": high, "bid_low": low,
            "bid_close": (low + high) / 2, "ask_open": (low + high) / 2 + 2 * half, "ask_high": high + 2 * half,
            "ask_low": low + 2 * half, "ask_close": (low + high) / 2 + 2 * half}


def close_one(rt, clock, which):
    """Drive the open EURUSD position to its stop or its target with one bar, then book the closure."""
    (pos,) = [p for p in rt.broker.positions() if p.symbol == "EURUSD"]
    clock.t += 60
    bar = (bar_through(rt, "EURUSD", pos.stop - 0.0010, pos.entry) if which == "STOP"
           else bar_through(rt, "EURUSD", pos.entry - 0.00001, pos.target + 0.0010))
    clock.t += 60
    assert rt.broker.on_bar("EURUSD", bar)[0].reason == which
    rt.run_cycle(decide=False)
    rows = rt.db.query("SELECT payload FROM trades")
    return json.loads(rows[-1]["payload"])["outcome"], pos


# ── 1-4: the decision becomes a paper position only through the risk engine ─────────────────

def test_1_a_valid_experimental_ai_decision_becomes_a_paper_execution(tmp_path, monkeypatch):
    rt, clock, _ = pf_runtime(tmp_path, monkeypatch)
    cycles(rt, clock)
    (pos,) = rt.broker.positions()
    trail = pipeline(rt)[-1]
    assert trail["stages"] == ["AI DECISION", "RISK APPROVED", "PAPER EXECUTED"] and trail["edge_status"] == "EXPERIMENTAL"
    row = rt.db.one("SELECT * FROM positions WHERE status='OPEN'")
    p = json.loads(row["payload"])
    for k in ("trade_id", "decision_id", "opened", "source", "edge_status", "confidence", "notional", "max_loss",
              "expected_costs", "equity_at_entry"):
        assert p.get(k) is not None, k
    assert p["source"] == "LLM_TRADER" and p["edge_status"] == "EXPERIMENTAL" and p["paper_forward"] is True
    assert p["max_loss"] <= 500 and row["stop"] < row["entry"] < row["target"]
    assert rt.paper_forward()["bot_status"] == "RUNNING"  # MODE=PAPER_FORWARD runs from its first start


def test_2_the_same_decision_never_becomes_live_and_is_shadow_in_plain_paper(tmp_path, monkeypatch):
    rt, clock, _ = pf_runtime(tmp_path, monkeypatch, mode="PAPER")
    rt.resume()
    cycles(rt, clock)
    assert rt.broker.positions() == []  # plain PAPER keeps a model's trade SHADOW
    assert pipeline(rt)[-1]["stages"][-1] == "SHADOW (not executed)"
    for mode in ("LIVE", "DEMO", "REAL", "live", "PAPER_FORWARD_LIVE"):
        assert execution_route("EXPERIMENTAL", mode, True, ai_originated=True) == "SHADOW"
    assert {execution_route(s, "PAPER_FORWARD", False, True) for s in ("EXPERIMENTAL", "VALIDATED")} == {"EXECUTE"}


def test_3_the_ai_cannot_bypass_the_risk_engine(tmp_path, monkeypatch):
    # the model asks for 40 lots, a 5% risk and an override: none of it is read; the size is the risk engine's
    rt, clock, _ = pf_runtime(tmp_path, monkeypatch, decide=lambda u: buy_reply(
        u, qty=40, lots=40, risk_pct=5.0, override_risk=True, ignore_limits=True))
    cycles(rt, clock)
    (pos,) = rt.broker.positions()
    verdict = json.loads(rt.db.one("SELECT payload FROM risk_verdicts")["payload"])
    assert pos.qty == verdict["qty"] < 40 and verdict["risk_amount"] <= 500


def test_4_a_risk_rejection_prevents_paper_execution_and_says_why(tmp_path, monkeypatch):
    # target at 0.5 ATR for a 1 ATR stop: reward/risk 0.5, below the risk engine's minimum
    rt, clock, _ = pf_runtime(tmp_path, monkeypatch, decide=lambda u: buy_reply(u, target_atr=0.5))
    cycles(rt, clock)
    assert rt.broker.positions() == []
    trail = pipeline(rt)[-1]
    assert trail["stages"] == ["AI DECISION", "RISK REJECTED"] and "reward_risk" in trail["reason"]


def test_5_a_missing_stop_loss_prevents_execution(tmp_path, monkeypatch):
    rt, clock, _ = pf_runtime(tmp_path, monkeypatch, decide=lambda u: {k: v for k, v in buy_reply(u).items() if k != "stop"})
    cycles(rt, clock)
    assert rt.broker.positions() == [] and rt.db.query("SELECT 1 FROM intents") == []


# ── execution-level checks with a model-originated decision (signal class LLM_TRADER) ─────────

def engine(paper_forward=True, profile=PAPER_FORWARD_200K, balance=200_000.0, db=None):
    from tests.unit.test_hard_gate import Clock as GClock, Feed, T0
    db = db or Database(":memory:")
    if db.get_kv("kill_switch") is None:
        db.set_kv("kill_switch", {"active": False})
    clock, feed = GClock(T0), Feed()
    gate = HardRiskGate(db, profile, clock)
    broker = PaperBroker(feed, clock, db, start_balance=balance, gate=gate)
    return ExecutionEngine(db, broker, clock, gate=gate, allow_unvalidated=True, paper_forward=paper_forward), feed


def model_trade(ex, did, qty=5.0, stop_pips=8, side="BUY"):
    from types import SimpleNamespace
    ask, bid = 1.10005, 1.09995
    s = 1 if side == "BUY" else -1
    entry = ask if s > 0 else bid
    d = SimpleNamespace(id=did, decision=side, instrument="EURUSD", timestamp=ex.clock(), edge_status="EXPERIMENTAL",
                        signal_class="LLM_TRADER", family="llm_trader", confidence=0.95)
    v = RiskVerdict(did, True, qty=qty, risk_amount=485.0, risk_pct=0.24, entry_ref=entry,
                    stop=entry - s * stop_pips * 0.0001, target=entry + s * 0.0030)
    return ex.execute(d, v)


def test_6_excess_risk_prevents_execution():
    ex, _ = engine()
    r = model_trade(ex, "big", qty=9.0)
    assert r.status == "BLOCKED" and "PER_TRADE_RISK" in r.detail and ex.broker.positions() == []


def test_7_the_daily_loss_limit_stops_new_trades_for_the_day_only():
    ex, _ = engine()
    ex.gate.observe(ex.broker)
    ex.broker.state["balance"] = 189_900.0  # -10,100 today, realised
    r = model_trade(ex, "a")
    assert r.status == "BLOCKED" and "DAILY_LOSS_LIMIT" in r.detail
    assert model_trade(ex, "b").detail.count("DAILY_LOCK") == 1  # the rest of the day: refused as locked
    st = ex.gate.status()
    assert st["risk_status"] == "DAILY_LOCK" and st["daily_limit_violations"] == 1 and not st["ftmo_rules_passed_so_far"]
    ex.clock.t += 86_400  # the next day (reference now 189,900): trading resumes, the violation stays on record
    assert model_trade(ex, "c").status == "FILLED" and ex.gate.status()["daily_limit_violations"] == 1


def test_8_the_maximum_loss_locks_the_run_permanently():
    ex, _ = engine()
    ex.gate.observe(ex.broker)
    for day, bal in enumerate((191_000.0, 182_000.0, 179_900.0)):
        ex.broker.state["balance"] = bal
        ex.gate.observe(ex.broker)
        ex.clock.t += 86_400
    # the heartbeat saw equity at 179,900 and locked the run at once, stopping the whole system with it
    assert ex.gate.status()["risk_status"] == "MAX_LOSS_LOCK" and ex.db.get_kv("kill_switch")["active"] is True
    r = model_trade(ex, "m0")
    assert r.status == "BLOCKED" and ex.broker.positions() == []
    ex.db.set_kv("kill_switch", {"active": False})  # an operator clears the system switch: the run stays locked
    for i in range(1, 4):
        ex.clock.t += 86_400
        r = model_trade(ex, f"m{i}")
        assert r.status == "BLOCKED" and "RISK_LOCKED" in r.detail and ex.broker.positions() == []


def test_9_aggregate_open_risk_is_enforced():
    ex, _ = engine()
    out = [model_trade(ex, f"p{i}").status for i in range(6)]
    assert out == ["FILLED"] * 4 + ["BLOCKED"] * 2


def test_19_duplicate_execution_cannot_create_duplicate_positions():
    ex, _ = engine()
    assert [model_trade(ex, "same").status for _ in range(3)] == ["FILLED", "DUPLICATE", "DUPLICATE"]
    assert len(ex.broker.positions()) == 1


def test_20_stale_market_data_prevents_new_trades():
    ex, feed = engine()
    feed.q["EURUSD"][2] = ex.clock() - 600
    r = model_trade(ex, "stale")
    assert r.status == "BLOCKED" and ex.broker.positions() == []


def test_21_the_kill_switch_prevents_new_trades(tmp_path, monkeypatch):
    rt, clock, _ = pf_runtime(tmp_path, monkeypatch)
    rt.db.set_kv("kill_switch", {"active": True}, reason="operator")
    cycles(rt, clock, 2)
    assert rt.broker.positions() == [] and rt.paper_forward()["bot_status"] == "RISK LOCK"


def test_a_model_trade_never_executes_outside_paper_forward_or_off_the_paper_broker():
    ex, _ = engine(paper_forward=False)
    r = model_trade(ex, "x")
    assert r.status == "BLOCKED" and "language model" in r.detail

    class NotPaper:
        name = "other"
    with pytest.raises(ValueError, match="paper broker only"):
        ExecutionEngine(Database(":memory:"), NotPaper(), lambda: 0, gate=ex.gate, paper_forward=True)


# ── 10-16, 22: positions persist, update, close, cost and produce outcomes ─────────────────────

def test_10_and_22_a_paper_position_and_the_account_persist_across_a_restart(tmp_path, monkeypatch):
    rt, clock, _ = pf_runtime(tmp_path, monkeypatch, data_dir=tmp_path / "state")
    cycles(rt, clock)
    (pos,) = rt.broker.positions()
    bal = rt.broker.state["balance"]
    rt2, _, _ = pf_runtime(tmp_path, monkeypatch, data_dir=tmp_path / "state", clock=clock)
    (again,) = rt2.broker.positions()
    assert (again.id, again.qty, again.entry, again.stop) == (pos.id, pos.qty, pos.entry, pos.stop)
    assert rt2.broker.state["balance"] == bal and rt2.gate.status()["open"] == {again.client_id: "OPEN"}
    assert rt2.db.one("SELECT status FROM positions")["status"] == "OPEN"


def test_11_an_open_position_is_marked_to_the_market(tmp_path, monkeypatch):
    rt, clock, feed = pf_runtime(tmp_path, monkeypatch)
    cycles(rt, clock)
    (pos,) = rt.broker.positions()
    before = rt.broker.unrealised_by_position()[pos.id]
    data = feed.series["EURUSD"]
    feed.series["EURUSD"] = dataclasses.replace(data, bid_close=data.bid_close + 0.0020, ask_close=data.ask_close + 0.0020)
    after = rt.broker.unrealised_by_position()[pos.id]
    assert after == pytest.approx(before + 0.0020 * pos.qty * 100_000, rel=1e-6)
    live = rt.paper_forward()
    assert live["account"]["equity"] == pytest.approx(rt.broker.account().equity, abs=0.01)


def test_12_14_15_16_a_stop_closes_the_position_with_every_cost_and_a_full_outcome(tmp_path, monkeypatch):
    rt, clock, _ = pf_runtime(tmp_path, monkeypatch)
    cycles(rt, clock)
    o, pos = close_one(rt, clock, "STOP")
    assert rt.broker.positions() == [] and o["exit_reason"] == "STOP" and o["win"] is False
    units = pos.qty * 100_000
    assert o["fees"] == pytest.approx(7.0 * pos.qty)  # commission
    assert o["slippage"] == pytest.approx(2 * 0.1 * 0.0001 * units)  # 0.1 pip on entry and on the stop fill
    assert o["spread"] > 0 and o["financing"] == pytest.approx(0.0)
    assert o["costs_total"] == pytest.approx(o["fees"] + o["financing"] + o["slippage"] + o["spread"])
    assert o["net_pnl"] == pytest.approx(o["gross_pnl"] - o["costs_total"])  # the cost identity, exactly
    for k in ("trade_id", "r", "mfe_r", "mae_r", "holding_s", "entry_reasoning", "exit_reasoning", "source", "agent",
              "edge_status", "regime", "prediction_correct", "risk_estimate_correct", "partition"):
        assert k in o, k
    assert o["source"] == "LLM_TRADER" and o["edge_status"] == "EXPERIMENTAL" and o["risk_estimate_correct"] is True
    assert o["r"] < 0 and o["net_pnl"] >= -o["planned_max_loss"]


def test_13_a_target_closes_the_position(tmp_path, monkeypatch):
    rt, clock, _ = pf_runtime(tmp_path, monkeypatch)
    cycles(rt, clock)
    o, pos = close_one(rt, clock, "TARGET")
    assert o["exit_reason"] == "TARGET" and o["win"] is True and o["prediction_correct"] is True
    assert o["slippage"] == pytest.approx(0.1 * 0.0001 * pos.qty * 100_000)  # a target fills at its price: entry slip only
    perf = rt.paper_forward()["performance"]["overall"]
    assert perf["trades"] == 1 and perf["wins"] == 1 and perf["sample"] == "insufficient"


# ── 17-18: learning receives outcomes, partitioned ─────────────────────────────────────────

def test_17_the_closed_trade_enters_the_forward_learning_pipeline(tmp_path, monkeypatch):
    rt, clock, _ = pf_runtime(tmp_path, monkeypatch)
    cycles(rt, clock)
    o, _ = close_one(rt, clock, "TARGET")
    fp = [json.loads(r["payload"]) for r in rt.db.query("SELECT payload FROM forward_proposals")]
    mine = [p for p in fp if p["decision_id"] == o["decision_id"]]
    assert mine and mine[0]["route"] == "EXECUTE" and mine[0]["executed"] is True
    assert mine[0]["partition"] == partition(mine[0]["t"])  # fixed by the decision time, never by the result
    ep = rt.db.query("SELECT kind FROM episodes WHERE decision_id=?", (o["decision_id"],))
    assert [e["kind"] for e in ep] == ["TRADE"]  # the trade episode the learning loop reads
    assert rt.db.query("SELECT 1 FROM postmortems") and rt.orch.experience is not None


def test_18_evaluation_outcomes_never_reach_learning():
    # one scope, 40 outcomes: all EVALUATION -> no lesson candidate can be formed from them
    rows = [{"partition": "EVALUATION", "symbol": "EURUSD", "outcome": {"net_r": -1.0, "resolved_at": 1_700_000_000 + i}}
            for i in range(40)]
    assert taxonomy.evaluate(rows, {}, 1_800_000_000) == []
    # and the model's memory of its own trades keeps only those decided in a LEARNING week
    db = Database(":memory:")
    t_learn = next(t for t in range(1_700_000_000, 1_700_000_000 + 30 * 86_400, 86_400) if partition(t) == "LEARNING")
    t_eval = next(t for t in range(1_700_000_000, 1_700_000_000 + 30 * 86_400, 86_400) if partition(t) == "EVALUATION")
    for t, did in ((t_learn, "L"), (t_eval, "E")):
        db.append("decisions", {"id": did, "symbol": "EURUSD", "timeframe": "M5", "decision": "BUY", "mode": "PAPER",
                                "payload": {"family": "LLM_TRADER"}})
        db.append("trades", {"position_id": f"P{did}", "decision_id": did, "symbol": "EURUSD", "r": 1.0, "pnl": 100.0,
                             "payload": {"decision": {"family": "LLM_TRADER"}, "position": {"opened": t, "symbol": "EURUSD",
                                                                                            "side": "BUY"},
                                         "exit": {"time": t + 3600, "reason": "TARGET"}, "r": 1.0}})
    remembered = TradeMemory(db, None)._rows()
    assert [json.loads(t["payload"])["position"]["opened"] for t in remembered] == [t_learn]
    assert TradeMemory(db, None).record()["trades"] == 1  # the EVALUATION-week trade is not in the model's record


# ── 23-24: locks survive restart; live stays impossible ─────────────────────────────────────

def test_23_an_account_lock_survives_a_restart(tmp_path):
    db = Database(tmp_path / "pf.db")
    ex, _ = engine(db=db)
    ex.gate.observe(ex.broker)
    ex.broker.state["balance"] = 179_000.0
    ex.broker._save()
    assert "MAX_TOTAL_LOSS" in model_trade(ex, "a").detail
    db.set_kv("kill_switch", {"active": False})  # even with the system switch cleared
    ex2, _ = engine(db=Database(tmp_path / "pf.db"))
    ex2.broker.state["balance"] = 205_000.0
    r = model_trade(ex2, "b")
    assert r.status == "BLOCKED" and "RISK_LOCKED" in r.detail and ex2.gate.status()["risk_status"] == "MAX_LOSS_LOCK"


@pytest.mark.parametrize("env", [{"MODE": "LIVE"}, {"MODE": "PAPER_FORWARD", "LIVE_TRADING": "true"},
                                 {"MODE": "DEMO"}, {"MODE": "PAPER_FORWARD", "PAPER_MODE": "false"},
                                 {"MODE": "PAPER_FORWARD", "EXPERIMENTAL_EXECUTE": "true"},
                                 {"MODE": "PAPER-FORWARD-LIVE"}])
def test_24_paper_forward_cannot_enable_live_trading(env):
    with pytest.raises(ServiceConfigError):
        ServiceConfig.from_env(env)
    ok = ServiceConfig.from_env({"MODE": "PAPER_FORWARD"})
    pub = ok.public()
    assert pub["live_trading"] is False and pub["real_money"] is False and pub["paper_forward"] is True
    assert ok.hard_profile.name == "PAPER-FORWARD-200K" and ok.start_balance == 200_000
    assert ok.hard_profile.daily_breach == "LOCK_DAY" and FTMO_200K.daily_breach == "LOCK_RUN"


def test_the_dashboard_says_paper_forward_test_not_real_money(tmp_path, monkeypatch):
    rt, clock, _ = pf_runtime(tmp_path, monkeypatch)
    cycles(rt, clock)
    v = rt.paper_forward()
    assert v["banner"] == "PAPER FORWARD TEST" and v["money"] == "NOT REAL MONEY" and v["live_trading"] is False
    assert "NO EDGE" in v["research_status"]  # the research truth is shown, not replaced
    assert v["account"]["equity"] is not None and v["risk_status"] == "ACTIVE" and len(v["open_positions"]) == 1
    assert v["pipeline"][0]["stages"][-1] == "PAPER EXECUTED"
    html = (runtime_mod.Path(runtime_mod.__file__).parent / "static" / "index.html").read_text()
    assert "PAPER FORWARD TEST" in html and "NOT REAL MONEY" in html


def test_paper_metrics_are_computed_from_every_trade_without_filtering():
    t0 = 1_700_000_000
    outs = [{"closed": t0 + i * 3600, "net_pnl": p, "r": r, "symbol": s, "direction": "BUY", "agent": "llm_trader",
             "regime": "trend", "holding_s": 3600, "costs_total": 10.0, "gross_pnl": p + 10.0, "partition": "LEARNING"}
            for i, (p, r, s) in enumerate([(500, 1.0, "EURUSD"), (-250, -0.5, "EURUSD"), (-250, -0.5, "GBPUSD"),
                                           (1000, 2.0, "GBPUSD"), (-500, -1.0, "USDJPY")])]
    s = paper_metrics.summary(outs)
    assert (s["trades"], s["wins"], s["losses"]) == (5, 2, 3) and s["win_rate"] == 0.4
    assert s["net_pnl"] == 500 and s["gross_profit"] == 1500 and s["gross_loss"] == 1000 and s["profit_factor"] == 1.5
    assert s["expectancy_r"] == pytest.approx(0.2) and s["max_drawdown_usd"] == 500
    assert (s["max_consecutive_wins"], s["max_consecutive_losses"], s["current_streak"]) == (1, 2, -1)
    assert s["costs_total"] == 50 and s["sample"] == "insufficient"
    rep = paper_metrics.report(outs)
    assert set(rep["by_symbol"]) == {"EURUSD", "GBPUSD", "USDJPY"} and rep["by_agent"]["llm_trader"]["trades"] == 5
    assert paper_metrics.summary([])["trades"] == 0 and paper_metrics.summary([])["sample"] == "none"


def test_a_timeout_or_manual_close_pays_and_records_exit_slippage_too(tmp_path, monkeypatch):
    rt, clock, _ = pf_runtime(tmp_path, monkeypatch)
    cycles(rt, clock)
    (pos,) = rt.broker.positions()
    clock.t += 120
    rt.execution.close_position(pos.id, "TIME")
    rt.run_cycle(decide=False)
    o = json.loads(rt.db.query("SELECT payload FROM trades")[-1]["payload"])["outcome"]
    assert o["exit_reason"] == "TIME" and rt.broker.positions() == []
    assert o["slippage"] == pytest.approx(2 * 0.1 * 0.0001 * pos.qty * 100_000)  # entry and exit, both paid
    assert o["net_pnl"] == pytest.approx(o["gross_pnl"] - o["costs_total"])
