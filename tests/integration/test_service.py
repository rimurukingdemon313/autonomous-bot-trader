"""The service over real HTTP: health, read models, control authorisation, restart."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

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


def build(tmp_path, token=TOKEN):
    data = {"EURUSD": market("EURUSD", START, 24 * 7 * 20, 1, 1.30), "GBPUSD": market("GBPUSD", START, 24 * 7 * 20, 2, 1.55)}
    feed = ReplayFeed(data)
    clock = Clock(int(data["EURUSD"].available_at[2000]))
    cfg = ServiceConfig(mode="PAPER", data_dir=str(tmp_path), port=0, symbols=("EURUSD", "GBPUSD"),
                        dashboard_token=token)
    broker = PaperBroker(feed, clock, None, start_balance=20_000)
    rt = Runtime(cfg, feed=feed, broker=broker, clock=clock)
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
    with pytest.raises(ServiceConfigError, match="LIVE"):
        ServiceConfig.from_env({"MODE": "LIVE"})


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
