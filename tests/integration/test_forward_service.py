"""The forward evidence engine inside the running service: experimental trades end to end, DEMO
shadow routing, restart recovery of unresolved proposals, and the readiness / metrics / evidence
endpoints over real HTTP."""

from __future__ import annotations

import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from aitrader.llm.provider import LLMClient, LLMConfig
from aitrader.service.server import make_handler

from .test_service import TOKEN, _write_kb, build, call


def model(seen=None):
    def reply(body):
        system, user = body["messages"][0]["content"], json.loads(body["messages"][1]["content"])
        if "A colleague proposed" in system:
            return json.dumps({"verdict": "AGREE", "direction": "BUY", "objections": [], "summary": "fine"})
        if "reviewing one of YOUR OWN" in system:
            return json.dumps({"what_happened": "x", "was_it_a_mistake": False})
        if "holds this open paper position" in system:
            return json.dumps({"action": "HOLD", "reason": "let it work"})
        if seen is not None:
            seen.append(user)
        ask, atr = user["quote"]["ask"], user["timeframes"]["H1"]["atr14"]
        return json.dumps({"action": "BUY", "timeframe": "H1", "stop": ask - 1.5 * atr, "target": ask + 2.0 * atr,
                           "max_hold_minutes": 720, "thesis": "test", "invalidation": "below the stop",
                           "confidence": 0.55, "reasons_against": ["thin evidence"], "method": "trend"})

    def transport(url, headers, body, timeout):
        return {"choices": [{"message": {"content": reply(body)}}],
                "usage": {"prompt_tokens": 50, "completion_tokens": 10, "total_tokens": 60}}
    return transport


def runtime(tmp_path, monkeypatch, mode="experimental_ai", seen=None):
    import aitrader.service.runtime as runtime_mod
    monkeypatch.setenv("DECISION_MODE", mode)
    monkeypatch.setattr(runtime_mod, "LLMClient",
                        lambda cfg: LLMClient(LLMConfig("openai_compatible", "https://x.test/v1", "k", "m1"), model(seen)))
    if not (tmp_path / "kb").exists():
        _write_kb(tmp_path / "kb")
    rt, clock = build(tmp_path / "rt", knowledge_dir=tmp_path / "kb")
    return rt, clock


def run(rt, clock, hours):
    for _ in range(hours):
        clock.t += 3600
        rt.monitor_once()
        rt.run_cycle(decide=rt.is_decision_hour(clock.t))


def test_experimental_trades_run_end_to_end_on_paper_and_are_labelled_and_measured(tmp_path, monkeypatch):
    rt, clock = runtime(tmp_path, monkeypatch)
    rt.resume()
    run(rt, clock, 24 * 10)
    props = [json.loads(r["payload"]) for r in rt.db.query("SELECT payload FROM forward_proposals")]
    assert props, "the experimental AI should have proposed trades"
    assert {p["signal_class"] for p in props} == {"EXPERIMENTAL_AI"}
    assert {p["edge_status"] for p in props} == {"EXPERIMENTAL"}  # never VALIDATED, whatever it says
    assert all(p["route"] in ("EXECUTE", "REJECTED") for p in props)  # PAPER simulates
    assert all(p["confidence"] == 0.55 and p["partition"] in ("LEARNING", "EVALUATION") for p in props)
    trades = rt.db.query("SELECT payload FROM trades")
    assert trades and all(json.loads(t["payload"])["decision"]["family"] == "EXPERIMENTAL_AI" for t in trades)
    outs = rt.db.query("SELECT payload FROM forward_outcomes")
    assert outs, "forward outcomes resolve as bars complete"
    for o in map(lambda r: json.loads(r["payload"]), outs):
        if o["net_r"] is not None:
            assert o["gross_r"] - o["cost_r"] == pytest.approx(o["net_r"], abs=1e-5)
    ev = rt.evidence()
    assert ev["all"]["n"] >= 1 and "EXPERIMENTAL_AI" in ev["by_signal_class"]
    assert ev["by_signal_class"]["EXPERIMENTAL_AI"]["eligibility"]["status"] in ("INSUFFICIENT", "NOT_POSITIVE",
                                                                                  "COLLECTING")
    d = rt.decisions(limit=200)
    traded = [x for x in d if x["decision"] in ("BUY", "SELL")]
    assert traded and all(x["edge_status"] == "EXPERIMENTAL" and x["ai_verdict"] == "TRADE" for x in traded)
    assert all(x["ai_model"] == "m1" and x["cost_r"] is not None for x in traded)
    assert all(x["edge_status"] == "NONE" for x in d if x["decision"] == "NO_TRADE")


def test_in_demo_an_unvalidated_trade_is_shadow_never_sent(tmp_path, monkeypatch):
    rt, clock = runtime(tmp_path, monkeypatch, mode="llm_trader")
    # The DEMO routing exactly as config builds it for MODE=DEMO without EXPERIMENTAL_EXECUTE (the paper
    # broker stands in for the demo account, so this test needs no network).
    rt.orch.cfg.mode, rt.orch.cfg.experimental_execute = "DEMO", False
    rt.execution.allow_unvalidated = False
    rt.resume()
    run(rt, clock, 24 * 5)
    assert rt.orch.counts["shadow"] > 0
    assert rt.db.query("SELECT 1 FROM intents") == []  # nothing was ever submitted
    props = [json.loads(r["payload"]) for r in rt.db.query("SELECT payload FROM forward_proposals")]
    assert props and {p["route"] for p in props} <= {"SHADOW", "REJECTED"} and any(p["route"] == "SHADOW" for p in props)
    assert any(json.loads(e["payload"]).get("edge_status") == "EXPERIMENTAL"
               for e in rt.db.query("SELECT payload FROM events WHERE type='SHADOW_TRADE'"))
    # even a direct call cannot send it: the execution engine refuses an unvalidated decision
    from types import SimpleNamespace
    from aitrader.risk.engine import RiskVerdict
    d = SimpleNamespace(id="x", decision="BUY", instrument="EURUSD", timestamp=clock(), edge_status="EXPERIMENTAL")
    v = RiskVerdict("x", True, qty=0.1, risk_amount=10, risk_pct=0.05, entry_ref=None, stop=1.0, target=2.0)
    assert rt.execution.execute(d, v).status == "BLOCKED"


def test_unresolved_proposals_survive_a_restart_and_resolve_after_it(tmp_path, monkeypatch):
    rt, clock = runtime(tmp_path, monkeypatch, mode="llm_trader")
    rt.resume()
    run(rt, clock, 8)
    before = rt.db.query("SELECT decision_id FROM forward_proposals")
    assert before
    t = clock.t
    rt2, clock2 = runtime(tmp_path, monkeypatch, mode="llm_trader")  # a redeploy on the same volume
    clock2.t = t
    assert {r["decision_id"] for r in rt2.db.query("SELECT decision_id FROM forward_proposals")} >= \
           {r["decision_id"] for r in before}
    assert rt2.orch.forward.pending()
    clock2.t += 24 * 3600 * 4
    rt2.orch.forward_tick(clock2.t)
    resolved = {r["decision_id"] for r in rt2.db.query("SELECT decision_id FROM forward_outcomes")}
    assert {r["decision_id"] for r in before} <= resolved | {p["decision_id"] for p in rt2.orch.forward.pending()}
    assert resolved & {r["decision_id"] for r in before}


def test_the_model_never_reads_an_evaluation_week_trade(tmp_path, monkeypatch):
    from aitrader.learning.forward import partition
    seen = []
    rt, clock = runtime(tmp_path, monkeypatch, mode="llm_trader", seen=seen)
    rt.resume()
    run(rt, clock, 24 * 30)
    shown = [t for u in seen for t in (u.get("memory") or {}).get("relevant_past_trades", [])]
    assert all(partition(int(t["opened"])) == "LEARNING" for t in shown)
    closed = [json.loads(r["payload"])["position"]["opened"] for r in rt.db.query("SELECT payload FROM trades")]
    assert shown and any(partition(int(o)) == "EVALUATION" for o in closed)  # the filter had work to do


@pytest.fixture()
def http(tmp_path, monkeypatch):
    rt, clock = runtime(tmp_path, monkeypatch)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(rt, TOKEN))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield rt, f"http://127.0.0.1:{httpd.server_address[1]}", clock
    httpd.shutdown()


def test_readiness_metrics_and_evidence_endpoints(http):
    rt, base, clock = http
    code, rd = call(base, "/readyz")
    assert code == 200 and rd["ready"] is True and rd["live_trading"] is False and rd["paused"] is True
    with urllib.request.urlopen(base + "/metrics", timeout=10) as r:
        text = r.read().decode()
        assert r.headers["Content-Type"].startswith("text/plain")
    assert "aitrader_live_trading 0" in text and "aitrader_ready 1" in text and "aitrader_kill_switch 0" in text
    for path in ("/api/evidence", "/api/lessons", "/api/decisions", "/api/status"):
        assert call(base, path)[0] == 200, path
    assert "No edge is VALIDATED" in call(base, "/api/evidence")[1]["statement"]
    rt.regime = None  # the knowledge base is gone: alive, but not ready
    code, rd = call(base, "/readyz")
    assert code == 503 and any("regime" in r for r in rd["reasons"])
    assert call(base, "/healthz")[0] == 200


def test_a_kill_switch_that_cannot_be_read_is_not_ready(http):
    rt, base, _ = http
    with rt.db.tx() as c:
        c.execute("UPDATE kv SET value='\"garbage\"' WHERE key='kill_switch'")
    code, rd = call(base, "/readyz")
    assert code == 503 and any("kill switch" in r for r in rd["reasons"])
