"""The dual-AI desk in the production runtime, PAPER_FORWARD, OpenRouter mocked (no request leaves the test):

    MARKET DATA -> CHART -> TRADER 1 -> TRADER 2 -> AGREE | DEBATE -> RISK ENGINE -> HARD GATE -> PAPER BROKER

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


def desk_runtime(tmp_path, monkeypatch, reply=None, mode="PAPER_FORWARD"):
    fake = FakeOpenRouter(reply or desk_reply())
    monkeypatch.setattr(runtime_mod, "OpenRouterClient", lambda cfg: client(fake))
    monkeypatch.setenv("DECISION_MODE", "dual_ai")
    if not (tmp_path / "kb").exists():
        _write_kb(tmp_path / "kb")
    data = {s: market(s, START, 24 * 7 * 20, i + 1, 1.30 if "JPY" not in s else 110.0) for i, s in enumerate(SYMS)}
    clock = Clock(int(data["EURUSD"].available_at[2000]))
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


def test_a_disagreement_is_debated_once_and_the_losing_side_is_followed_forward(tmp_path, monkeypatch):
    rt, clock, fake = desk_runtime(tmp_path, monkeypatch, desk_reply(t1="SELL", t2="BUY", debate="SELL"))
    cycles(rt, clock)
    (pos,) = rt.broker.positions()
    assert pos.side == -1 and [c["role"] for c in fake.calls] == ["trader1", "trader2", "debate"]
    assert fake.calls[2]["model"] == DEBATE
    rows = [json.loads(r["payload"]) for r in rt.db.query("SELECT payload FROM forward_proposals")]
    loser = [r for r in rows if r["family"] == "DUAL_AI_DEBATE_LOSER"]
    taken = [r for r in rows if r["family"] == "DUAL_AI"]
    assert len(loser) == 1 and loser[0]["side"] == 1 and loser[0]["route"] == "COUNTERFACTUAL"
    assert len(taken) == 1 and taken[0]["side"] == -1 and taken[0]["route"] == "EXECUTE"


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
    for k in ("net_r", "mfe_r", "mae_r", "regime", "desk_confidence"):
        assert k in ev
    rec = dual_ai_stats.record(rt.db)
    assert rec["trades_taken"]["n"] == 1 and rec["trades_taken"]["sample"] == "insufficient"
    assert rec["by_rule"]["AGREE"]["n"] == 1 and rec["trader1_hit_rate"]["rate"] == 1.0
    view = rt.dual_ai()
    assert view["performance"]["trades"] == 1 and view["performance"]["wins"] == 1


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
