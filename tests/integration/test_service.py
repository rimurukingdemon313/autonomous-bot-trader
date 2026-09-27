"""The service over real HTTP: health, read models, control authorisation, restart."""

from __future__ import annotations

import hashlib
import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from pathlib import Path

import numpy as np
import pytest

from aitrader.broker.paper import PaperBroker
from aitrader.data.feed import ReplayFeed
from aitrader.service.config import ServiceConfig, ServiceConfigError
from aitrader.service.runtime import Runtime
from aitrader.service.server import make_handler

from .test_pipeline import START, market

TOKEN = "t0ken-for-tests"


class Clock:
    def __init__(self, t): self.t = t
    def __call__(self): return self.t


def build(tmp_path, token=TOKEN, knowledge_dir=None):
    data = {"EURUSD": market("EURUSD", START, 24 * 7 * 20, 1, 1.30), "GBPUSD": market("GBPUSD", START, 24 * 7 * 20, 2, 1.55)}
    feed = ReplayFeed(data)
    clock = Clock(int(data["EURUSD"].available_at[2000]))
    cfg = ServiceConfig(mode="PAPER", data_dir=str(tmp_path), port=0, symbols=("EURUSD", "GBPUSD"),
                        dashboard_token=token)
    broker = PaperBroker(feed, clock, None, start_balance=20_000)
    # Never the repository's own models/artifacts: a test must not depend on what was last built.
    rt = Runtime(cfg, feed=feed, broker=broker, clock=clock, knowledge_dir=knowledge_dir or tmp_path / "no-kb")
    broker.db = rt.db
    return rt, clock


@pytest.fixture()
def server(tmp_path):
    rt, clock = build(tmp_path)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(rt, TOKEN))
    th = threading.Thread(target=httpd.serve_forever, daemon=True)
    th.start()
    yield rt, f"http://127.0.0.1:{httpd.server_address[1]}", clock
    httpd.shutdown()


def call(base, path, method="GET", body=None, token=None):
    req = urllib.request.Request(base + path, method=method, data=json.dumps(body or {}).encode() if method == "POST" else None,
                                 headers={"Content-Type": "application/json", **({"X-Dashboard-Token": token} if token else {})})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def test_health_and_read_models_answer(server):
    rt, base, _ = server
    assert call(base, "/healthz")[0] == 200
    code, st = call(base, "/api/status")
    assert code == 200 and st["mode"] == "PAPER"
    for path in ("/api/account", "/api/market", "/api/memory", "/api/research", "/api/risk", "/api/agents",
                 "/api/performance", "/api/trades", "/api/trades?status=open", "/api/decisions", "/api/events",
                 "/api/market/EURUSD/bars"):
        code, body = call(base, path)
        assert code == 200, path


def test_missing_knowledge_is_reported_not_papered_over(server):
    rt, base, _ = server
    rt.regime = None
    rep = rt.run_cycle()
    assert rep["decisions"] == []
    st = call(base, "/api/status")[1]
    assert "knowledge" in st["last_cycle_error"] or st["components"]["regime_model"] in ("MISSING", "LOADED")


def _write_kb(d, tamper=False):
    from aitrader.features.store import compute_matrix
    from aitrader.memory.patterns import PatternMemory
    from aitrader.orchestrator.tracker import ACTIONS
    from aitrader.regime.model import RegimeModel

    s = market("EURUSD", START, 24 * 7 * 20, 1, 1.30)
    reg = RegimeModel.fit(compute_matrix(s), s.available_at, trained_until=int(s.available_at[-1]))
    d.mkdir()
    PatternMemory(np.zeros(18), np.ones(18), ACTIONS).save(d / "memory.npz")
    (d / "regime.json").write_text(reg.to_json())
    digest = hashlib.sha256((d / "memory.npz").read_bytes() + (d / "regime.json").read_bytes()).hexdigest()
    (d / "knowledge_card.json").write_text(json.dumps({"id": "kb-test", "hash": digest[:16], "sha256": digest}))
    if tamper:
        (d / "regime.json").write_text(reg.to_json() + " ")


def test_a_knowledge_base_loads_only_if_it_matches_its_card(tmp_path):
    _write_kb(tmp_path / "good")
    rt, _ = build(tmp_path / "a", knowledge_dir=tmp_path / "good")
    assert rt.regime is not None and rt.knowledge_meta["integrity"] == "VERIFIED"
    assert rt.orch.versions["knowledge_base"] == rt.knowledge_meta["hash"]

    _write_kb(tmp_path / "bad", tamper=True)
    rt, _ = build(tmp_path / "b", knowledge_dir=tmp_path / "bad")
    assert rt.regime is None and rt.knowledge_meta["integrity"] == "MISMATCH"
    assert rt.orch.versions["knowledge_base"] == "none"
    assert rt.run_cycle()["decisions"] == []
    assert "MISMATCH" in rt.health["last_cycle_error"]

    (tmp_path / "partial").mkdir()
    (tmp_path / "partial" / "regime.json").write_text((tmp_path / "good" / "regime.json").read_text())
    rt, _ = build(tmp_path / "c", knowledge_dir=tmp_path / "partial")
    assert rt.regime is None and rt.knowledge_meta["integrity"] == "INCOMPLETE"


def test_the_service_decides_at_the_cadence_the_knowledge_was_tested_with(tmp_path):
    rt, clock = build(tmp_path)
    assert rt.decide_every_bars == 4  # no card: the research default
    delay = rt.cfg.cycle_delay_s
    base = 1_600_000_000 // 86400 * 86400  # a midnight UTC
    hours = [h for h in range(24) if rt.is_decision_hour(base + h * 3600 + delay)]
    assert hours == [0, 4, 8, 12, 16, 20]
    rt.knowledge_meta = {**rt.knowledge_meta, "decision_every_bars": 2}
    assert sum(rt.is_decision_hour(base + h * 3600 + delay) for h in range(24)) == 12
    # A bookkeeping-only cycle decides nothing.
    rep = rt.run_cycle(decide=False)
    assert rep.get("decisions", []) == []


def test_stopping_is_always_allowed_without_a_token(server):
    rt, base, _ = server
    assert call(base, "/api/control/pause", "POST")[0] == 200
    assert call(base, "/api/control/kill", "POST", {"reason": "test"})[0] == 200
    assert rt.db.get_kv("kill_switch")["active"] is True and rt.db.get_kv("paused") is True


@pytest.mark.parametrize("path", ["/api/control/resume", "/api/control/kill/clear", "/api/control/scan",
                                  "/api/control/knowledge/revert"])
def test_resuming_or_initiating_needs_the_token(server, path):
    rt, base, _ = server
    code, body = call(base, path, "POST", {"version": 0})
    assert code == 401 and body["code"] == "UNAUTHORIZED"
    assert call(base, path, "POST", {"version": 0}, token="wrong")[0] == 401
    assert call(base, path, "POST", {"version": 0}, token=TOKEN)[0] in (200, 202)


def test_with_no_token_configured_dangerous_controls_are_refused_not_open(tmp_path):
    rt, _ = build(tmp_path, token="")
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(rt, ""))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    try:
        code, body = call(base, "/api/control/resume", "POST", token="anything")
        assert code == 503 and body["code"] == "NO_TOKEN_CONFIGURED" and "DASHBOARD_TOKEN" in body["error"]
        assert call(base, "/api/control/kill", "POST")[0] == 200
    finally:
        httpd.shutdown()


def test_no_secret_is_ever_served(server, monkeypatch):
    rt, base, _ = server
    monkeypatch.setenv("AI_API_KEY", "sk-supersecretvalue123")
    blob = "".join(json.dumps(call(base, p)[1]) for p in ("/api/status", "/api/agents", "/api/risk", "/api/memory"))
    assert TOKEN not in blob and "sk-supersecretvalue123" not in blob


def test_static_dashboard_is_served_and_path_traversal_is_refused(server):
    rt, base, _ = server
    with urllib.request.urlopen(base + "/", timeout=5) as r:
        assert b"AI Trader" in r.read()
    assert call(base, "/../../etc/passwd")[0] == 404


def test_live_mode_is_refused_at_configuration():
    with pytest.raises(ServiceConfigError, match="MODE=LIVE is not available"):
        ServiceConfig.from_env({"MODE": "LIVE"})
    with pytest.raises(ServiceConfigError, match="PAPER or DEMO"):
        ServiceConfig.from_env({"MODE": "REAL"})


def test_risk_configuration_cannot_exceed_the_ceiling():
    cfg = ServiceConfig.from_env({"RISK_PER_TRADE_PCT": "25"})
    assert cfg.risk.risk_per_trade_pct <= 1.0


def test_state_survives_a_restart(tmp_path):
    rt, clock = build(tmp_path)
    rt.kill("before restart")
    rt.db.append("episodes", {"decision_id": "d-x", "kind": "NO_TRADE", "symbol": "EURUSD", "payload": {}})
    rt2, _ = build(tmp_path)
    assert rt2.db.get_kv("kill_switch")["active"] is True
    assert rt2.db.one("SELECT kind FROM episodes WHERE decision_id='d-x'")["kind"] == "NO_TRADE"


def test_learning_revert_is_a_new_version_survives_restart_and_learning_continues(tmp_path):
    rt, clock = build(tmp_path)
    ex, orch, t0 = rt.experience, rt.orch, clock()

    def change(lid, status, t, **kw):
        return ex._new_version(lid, status, t, context=["trend", 1, "RANGING", "HIGH_VOL"], created=t, **kw)

    assert orch._commit_knowledge([change("L:a", "CANDIDATE", t0)], t0) == 1
    assert orch._commit_knowledge([change("L:a", "VALIDATED", t0 + 10), change("L:b", "CANDIDATE", t0 + 10)], t0 + 10) == 2

    rep = rt.revert_knowledge(1)
    assert rep["new_version"] == 3 and orch.knowledge_version == 3
    assert ex.lessons["L:a"][-1]["status"] == "CANDIDATE" and ex.lessons["L:a"][-1]["version"] == 3
    assert ex.lessons["L:b"][-1]["status"] == "RETIRED"
    # Learning carries on without reusing a version number anywhere.
    assert orch._commit_knowledge([change("L:a", "VALIDATED", t0 + 20)], t0 + 20) == 4
    with pytest.raises(ValueError):
        rt.revert_knowledge(99)

    rt2, _ = build(tmp_path)
    assert rt2.orch.knowledge_version == 4
    assert rt2.experience.lessons["L:a"][-1]["status"] == "VALIDATED"
    assert rt2.experience.lessons["L:b"][-1]["status"] == "RETIRED"
    assert [r["version"] for r in rt2.db.query("SELECT version FROM knowledge_versions ORDER BY seq")] == [1, 2, 3, 4]
    assert all(rt2.db.verify_chain(tb)[0] for tb in ("lessons", "knowledge_versions"))


def test_skipped_candidates_outcomes_survive_a_restart(tmp_path):
    from aitrader.learning.experience import Evaluation

    rt, clock = build(tmp_path)
    e = Evaluation("d-1", "EURUSD", clock() - 7200, clock() - 3600, "trend", "T1:BUY", 1, "RANGING", "HIGH_VOL",
                   "london", ("SPREAD_WIDE",), False, -0.4, 0.1, 0.5, {"adversary_llm": "SELL"})
    import dataclasses
    rt.db.append("evaluations", {"decision_id": "d-1", "payload": {"evaluations": [dataclasses.asdict(e)]}})
    rt2, _ = build(tmp_path)
    assert rt2.experience.summary()["resolved"] == 1
    got = rt2.experience.resolved[0]
    assert got == e


def test_cycles_monitoring_and_scans_never_overlap(tmp_path):
    """A dashboard scan during a scheduled cycle must wait, not run beside it."""
    import time as _time

    rt, _ = build(tmp_path)
    rt.regime = object()  # any loaded model: the cycle below is a stand-in
    inside, peak = [0], [0]

    def slow_cycle(t, symbols=None):
        inside[0] += 1
        peak[0] = max(peak[0], inside[0])
        _time.sleep(0.15)
        inside[0] -= 1
        return {"t": t, "decisions": []}

    rt.orch.cycle = slow_cycle
    threads = [threading.Thread(target=rt.run_cycle) for _ in range(3)] + [threading.Thread(target=rt.monitor_once)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    assert peak[0] == 1


def test_postmortems_survive_a_restart_for_reflection(tmp_path):
    rt, _ = build(tmp_path)
    for i in range(3):
        rt.db.append("postmortems", {"episode_id": f"ep-{i}", "payload": {"cause": "STOP_BEFORE_THESIS", "i": i}})
    rt2, _ = build(tmp_path)
    assert [p["i"] for p in rt2.orch._postmortems] == [0, 1, 2]


def test_a_failed_startup_serves_its_reason_and_never_trades(tmp_path):
    """Startup incomplete: no trading, but health answers 503 with why (the real process, over HTTP)."""
    import os
    import socket
    import subprocess
    import sys
    import time as _time

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("x")
    env = {**os.environ, "MODE": "PAPER", "PORT": str(port), "DATA_DIR": str(blocker / "data"),
           "DASHBOARD_TOKEN": "t", "PYTHONPATH": str(Path(__file__).resolve().parents[2])}
    proc = subprocess.Popen([sys.executable, "-m", "aitrader"], env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    try:
        for _ in range(100):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz", timeout=1)
            except urllib.error.HTTPError as e:
                body = json.loads(e.read())
                assert e.code == 503 and body["system"] == "STARTUP_FAILED"
                assert "DATA_DIR" in body["reason"]
                break
            except OSError:
                _time.sleep(0.1)
        else:
            raise AssertionError("the failed service never answered")
    finally:
        proc.kill()
        proc.wait()


def test_first_start_is_paused_and_only_an_authenticated_resume_starts_trading(tmp_path):
    rt, _ = build(tmp_path)
    assert rt.db.get_kv("paused") is True
    rt.resume()
    rt2, _ = build(tmp_path)  # a restart keeps the operator's decision, it does not re-pause
    assert rt2.db.get_kv("paused") is False


def test_reflection_journals_experiment_proposals_once_and_changes_nothing(tmp_path, monkeypatch):
    import aitrader.orchestrator.core as core

    rt, clock = build(tmp_path)
    fake = {"t": clock(), "hypotheses": [{"kind": "REPEATED_MISTAKE", "cause": "ENTRY_TIMING", "text": "x"}]}
    monkeypatch.setattr(core, "reflect", lambda *a, **k: dict(fake))
    before = {k: rt.db.get_kv(k) for k in ("paused", "kill_switch")}
    kv_before = rt.orch.knowledge_version
    rt.orch.reflect(clock())
    rt.orch.reflect(clock())  # the same proposal again: journalled once
    rows = rt.db.query("SELECT payload FROM experiments")
    assert len(rows) == 1 and json.loads(rows[0]["payload"])["status"] == "PROPOSED"
    assert rt.orch.knowledge_version == kv_before  # a proposal is not a lesson and not a version
    assert {k: rt.db.get_kv(k) for k in ("paused", "kill_switch")} == before
    assert rt.research()["proposals"][0]["kind"] == "MISTAKE_FEATURE"
    assert rt.db.verify_chain("experiments")[0]


def test_the_llm_trader_trades_through_the_risk_engine_reviews_itself_and_remembers(tmp_path, monkeypatch):
    """End to end: model proposes -> risk engine sizes -> paper fill -> close -> self-review -> memory."""
    import aitrader.service.runtime as runtime_mod
    from aitrader.llm.provider import LLMClient, LLMConfig
    from aitrader.memory.trade_memory import TradeMemory

    seen_memory = []

    def reply(body):
        system, user = body["messages"][0]["content"], json.loads(body["messages"][1]["content"])
        if "reviewing one of YOUR OWN" in system:
            return json.dumps({"what_happened": f"{user['exit_reason']} at {user['R']:+.2f}R", "was_it_a_mistake": user["R"] < 0,
                               "mistake": "chased the move" if user["R"] < 0 else None, "lesson": "wait for a pullback"})
        seen_memory.append(user["memory"])
        ask, atr = user["quote"]["ask"], user["timeframes"]["H1"]["atr14"]
        return json.dumps({"action": "BUY", "timeframe": "H1", "stop": ask - 1.5 * atr, "target": ask + 2.0 * atr,
                           "max_hold_hours": 12, "thesis": "test trade", "invalidation": "stop", "memory_used": "none"})

    def transport(url, headers, body, timeout):
        return {"choices": [{"message": {"content": reply(body)}}], "usage": {"total_tokens": 10}}

    monkeypatch.setenv("DECISION_MODE", "llm_trader")
    monkeypatch.setattr(runtime_mod, "LLMClient",
                        lambda cfg: LLMClient(LLMConfig("openai_compatible", "https://x.test/v1", "k", "m1"), transport))
    _write_kb(tmp_path / "kb")
    rt, clock = build(tmp_path / "rt", knowledge_dir=tmp_path / "kb")
    rt.resume()
    for _ in range(24 * 12):
        clock.t += 3600
        rt.monitor_once()
        rt.run_cycle(decide=rt.is_decision_hour(clock.t))

    trades = rt.db.query("SELECT decision_id, r, payload FROM trades")
    assert trades, "the model trader should have traded on the replay"
    for tr in trades:
        assert json.loads(tr["payload"])["decision"]["family"] == "LLM_TRADER"
        verdict = rt.db.one("SELECT approved, payload FROM risk_verdicts WHERE decision_id=?", (tr["decision_id"],))
        assert verdict["approved"] == 1 and json.loads(verdict["payload"])["qty"] > 0  # sized by the risk engine
    reviews = [json.loads(r["payload"]) for r in rt.db.query("SELECT payload FROM reflections")]
    reviews = [r for r in reviews if r.get("kind") == "trade"]
    assert len(reviews) == len(trades) and all(r["lesson"] == "wait for a pullback" for r in reviews)
    brief = TradeMemory(rt.db, rt.experience).brief("EURUSD", "RANGING", clock.t)
    assert brief["my_record"]["trades"] == len(trades)
    assert any(v["my_lesson"] == "wait for a pullback" for v in brief["relevant_past_trades"])
    assert any(m["relevant_past_trades"] for m in seen_memory)  # later decisions were shown earlier trades
    assert rt.status()["versions"].get("service")


def test_the_trading_room_hunts_debates_and_trades_through_the_risk_engine(tmp_path, monkeypatch):
    """End to end: three providers hunt, debate, the head picks one member's trade, the risk engine sizes it,
    and each member's record is measured separately."""
    import aitrader.service.runtime as runtime_mod
    from aitrader.llm.provider import Endpoint, LLMClient, LLMConfig

    heads = []

    def reply(member, body):
        system, user = body["messages"][0]["content"], json.loads(body["messages"][1]["content"])
        if "reviewing one of YOUR OWN" in system:
            return {"what_happened": "closed", "was_it_a_mistake": False, "mistake": None, "lesson": None}
        if "HEAD TRADER" in system:
            heads.append(user["track_records"])
            return {"decision": "TRADE", "pick": "gemini", "reason": "wider stop"}
        if member == "bytez":
            return {"action": "NO_TRADE", "thesis": "waiting for the London open"}
        ask, atr = user["quote"]["ask"], user["timeframes"]["H1"]["atr14"]
        k = 2.0 if member == "gemini" else 1.5
        return {"action": "BUY", "timeframe": "H1", "stop": ask - k * atr, "target": ask + 2 * k * atr,
                "max_hold_hours": 12, "thesis": f"{member} buys", "invalidation": "stop", "memory_used": "none"}

    def transport(url, headers, body, timeout):
        member = url.split("//")[1].split(".")[0]
        return {"choices": [{"message": {"content": json.dumps(reply(member, body))}}]}

    cfg = LLMConfig(providers=tuple(Endpoint(m, f"https://{m}.test/v1", "k", f"{m}-m") for m in ("groq", "gemini", "bytez")))
    monkeypatch.setenv("DECISION_MODE", "trading_room")
    monkeypatch.setenv("AI_ROOM_QUORUM", "2")
    monkeypatch.setattr(runtime_mod, "LLMClient", lambda _cfg: LLMClient(cfg, transport))
    _write_kb(tmp_path / "kb")
    rt, clock = build(tmp_path / "rt", knowledge_dir=tmp_path / "kb")
    rt.resume()
    for _ in range(24 * 12):
        clock.t += 3600
        rt.monitor_once()
        rt.run_cycle(decide=rt.is_decision_hour(clock.t))

    trades = rt.db.query("SELECT decision_id FROM trades")
    assert trades, "the room should have traded on the replay"
    for tr in trades:
        dec = json.loads(rt.db.one("SELECT payload FROM decisions WHERE id=?", (tr["decision_id"],))["payload"])
        room = dec["independent_evidence"]["room"]
        assert room["picked"] == "gemini" and room["final"]["bytez"]["action"] == "NO_TRADE"
        verdict = rt.db.one("SELECT approved, payload FROM risk_verdicts WHERE decision_id=?", (tr["decision_id"],))
        assert verdict["approved"] == 1 and json.loads(verdict["payload"])["qty"] > 0  # sized by the risk engine
    st = rt.status()["components"]
    assert st["decision_mode"] == "trading_room" and st["trading_room"]["members"] == ["groq", "gemini", "bytez"]
    recs = st["trading_room"]["records"]
    assert recs["gemini"]["supported"]["trades"] == len(trades) and recs["bytez"]["supported"] == {"trades": 0}
    assert any(h.get("gemini") for h in heads)  # later heads saw the members' records
