"""HTTP API and dashboard. Standard library only.

Controls are split by DIRECTION, never by endpoint (ARCHITECTURE.md):
- pause and emergency stop are ALWAYS accepted, with no token: an operator
  must be able to stop the system from any device, having lost anything;
- resume, clearing the kill switch, a forced scan and reverting knowledge
  require DASHBOARD_TOKEN. With no token configured they are refused
  (503 NO_TOKEN_CONFIGURED), not left open.

No endpoint can open, size or close a trade. Nothing here returns a secret.
"""

from __future__ import annotations

import hmac
import json
import math
import mimetypes
import signal
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ..observability import log_event
from .runtime import Runtime

STATIC = Path(__file__).resolve().parent / "static"


def _finite(x):
    """`x` with every non-finite float replaced by None (shown as N/A), recursively."""
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    if isinstance(x, dict):
        return {k: _finite(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_finite(v) for v in x]
    return x


def make_handler(rt: Runtime, token: str):
    class Handler(BaseHTTPRequestHandler):
        server_version = "aitrader"

        def log_message(self, fmt, *args):  # quiet: the app logs what matters
            pass

        def _send(self, code: int, body, ctype: str = "application/json") -> None:
            # Strict JSON: a NaN or infinity (a feature the source does not provide, an undefined
            # ratio) becomes null. Python would write NaN, which browsers refuse to parse: the page
            # then silently showed "no decision" for decisions that existed.
            data = body if isinstance(body, bytes) else json.dumps(_finite(body), default=str, allow_nan=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

        def _authorised(self) -> tuple[bool, dict | None]:
            if not token:
                return False, {"code": "NO_TOKEN_CONFIGURED",
                               "error": "set DASHBOARD_TOKEN to enable controls that resume or widen trading"}
            given = self.headers.get("X-Dashboard-Token") or ""
            auth = self.headers.get("Authorization") or ""
            if auth.startswith("Bearer "):
                given = given or auth[7:]
            if given and hmac.compare_digest(given.encode(), token.encode()):
                return True, None
            return False, {"code": "UNAUTHORIZED", "error": "a valid dashboard token is required"}

        def _body(self) -> dict:
            n = int(self.headers.get("Content-Length") or 0)
            if n <= 0 or n > 10_000:
                return {}
            try:
                return json.loads(self.rfile.read(n).decode() or "{}")
            except (json.JSONDecodeError, UnicodeDecodeError):
                return {}

        # ── GET ─────────────────────────────────────────────────────────

        def do_GET(self):  # noqa: N802
            url = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(url.query).items()}
            p = url.path.rstrip("/") or "/"
            try:
                if p == "/healthz":  # liveness: the process and its database answer
                    st = rt.status()
                    ok = st["components"]["database"] == "HEALTHY"
                    return self._send(200 if ok else 503, {"ok": ok, "system": st["system"], "mode": st["mode"]})
                if p == "/readyz":  # readiness: safe to make decisions (paused is still ready)
                    rd = rt.readiness()
                    return self._send(200 if rd["ready"] else 503, rd)
                if p == "/metrics":  # Prometheus text format
                    return self._send(200, rt.metrics_text().encode(), "text/plain; version=0.0.4")
                routes = {
                    "/api/status": rt.status,
                    "/api/account": rt.account,
                    "/api/live": rt.live,
                    "/api/room": lambda: getattr(getattr(rt.orch.brain, "room", None), "live", None) or {},
                    "/api/market": rt.market,
                    "/api/memory": rt.memory_view,
                    "/api/research": rt.research,
                    "/api/logs": rt.logs,
                    "/api/risk": lambda: {"limits": rt.cfg.public()["risk"], "funded": rt.cfg.public()["funded"],
                                          "recent": [{"decision_id": r["decision_id"], "approved": bool(r["approved"]),
                                                      **json.loads(r["payload"])} for r in rt.db.query(
                                              "SELECT decision_id, approved, payload FROM risk_verdicts ORDER BY seq DESC LIMIT 20")]},
                    "/api/agents": lambda: {"llm": rt.llm.health(), "last": {s: v.get("agents") for s, v in rt.orch.status["symbols"].items()}},
                    "/api/performance": lambda: _performance(rt),
                    "/api/evidence": rt.evidence,
                    "/api/lessons": rt.lessons,
                    "/api/readyz": rt.readiness,
                }
                if p in routes:
                    return self._send(200, routes[p]())
                if p == "/api/trades":
                    return self._send(200, rt.trades(closed=q.get("status", "closed") != "open", limit=int(q.get("limit", 200))))
                if p == "/api/decisions":
                    return self._send(200, rt.decisions(int(q.get("limit", 50)), q.get("symbol")))
                if p.startswith("/api/decisions/"):
                    d = rt.decision_detail(p.split("/")[-1])
                    return self._send(200 if d else 404, d or {"error": "not found"})
                if p.startswith("/api/market/") and p.endswith("/bars"):
                    return self._send(200, rt.bars(p.split("/")[3].upper(), int(q.get("n", 200))))
                if p == "/api/events":
                    return self._send(200, rt.events(int(q.get("since", 0)), int(q.get("limit", 200))))
                if p == "/api/stream":
                    return self._stream(int(q.get("since", 0)))
                return self._static(p)
            except Exception as exc:
                log_event("API", f"GET {p} failed", severity="error", error=f"{type(exc).__name__}: {exc}")
                return self._send(500, {"error": "internal error", "type": type(exc).__name__})

        def _stream(self, since: int) -> None:
            """Server-sent events: the event log as it grows."""
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            last = since
            deadline = time.time() + 300
            try:
                while time.time() < deadline:
                    evs = list(reversed(rt.events(last, 100)))
                    for ev in evs:
                        last = max(last, ev["seq"])
                        self.wfile.write(f"id: {ev['seq']}\ndata: {json.dumps(ev, default=str)}\n\n".encode())
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
                    time.sleep(2)
            except (BrokenPipeError, ConnectionResetError):
                return

        def _static(self, p: str):
            name = "index.html" if p in ("/", "") else p.lstrip("/")
            f = (STATIC / name).resolve()
            if STATIC not in f.parents or not f.is_file():
                return self._send(404, {"error": "not found"})
            ctype = mimetypes.guess_type(str(f))[0] or "application/octet-stream"
            return self._send(200, f.read_bytes(), ctype)

        # ── POST (controls) ─────────────────────────────────────────────

        def do_POST(self):  # noqa: N802
            try:
                return self._post()
            except Exception as exc:
                log_event("API", f"POST {self.path} failed", severity="error", error=f"{type(exc).__name__}: {exc}")
                return self._send(500, {"error": "internal error", "type": type(exc).__name__})

        def _post(self):
            p = urlparse(self.path).path.rstrip("/")
            body = self._body()
            reason = str(body.get("reason", ""))[:200]
            # Reducing activity: always allowed.
            if p == "/api/control/pause":
                rt.pause(reason or "operator pause")
                return self._send(200, {"ok": True, "paused": True})
            if p == "/api/control/kill":
                rt.kill(reason or "operator emergency stop")
                return self._send(200, {"ok": True, "kill_switch": True})
            # Resuming, widening or initiating: token required.
            if p in ("/api/control/resume", "/api/control/kill/clear", "/api/control/scan",
                     "/api/control/knowledge/revert", "/api/control/verify"):
                ok, err = self._authorised()
                if not ok:
                    return self._send(503 if err["code"] == "NO_TOKEN_CONFIGURED" else 401, err)
                if p == "/api/control/verify":
                    return self._send(200, {"ok": True})
                if p == "/api/control/resume":
                    rt.resume()
                    return self._send(200, {"ok": True, "paused": False})
                if p == "/api/control/kill/clear":
                    rt.clear_kill()
                    return self._send(200, {"ok": True, "kill_switch": False})
                if p == "/api/control/scan":
                    threading.Thread(target=rt.run_cycle, daemon=True).start()
                    return self._send(202, {"ok": True, "scan": "started"})
                if p == "/api/control/knowledge/revert":
                    try:
                        v = int(body.get("version"))
                    except (TypeError, ValueError):
                        return self._send(400, {"error": "version must be an integer"})
                    try:
                        return self._send(200, rt.revert_knowledge(v))
                    except ValueError as exc:
                        return self._send(400, {"error": str(exc)})
            return self._send(404, {"error": "not found"})

    return Handler


def _performance(rt: Runtime) -> dict:
    from ..backtest.metrics import summarise
    trades = rt.trades(closed=True, limit=10_000)
    if not trades:
        return {"available": False, "reason": "no closed trades yet", "trades": 0}
    return {"available": True, **summarise(trades, rt.cfg.start_balance)}


def serve(rt: Runtime, host: str = "0.0.0.0") -> None:
    httpd = ThreadingHTTPServer((host, rt.cfg.port), make_handler(rt, rt.cfg.dashboard_token))
    httpd.daemon_threads = True

    def shutdown(signum, frame):
        log_event("SHUTDOWN", f"signal {signum}: stopping gracefully")
        rt.stop()
        threading.Thread(target=httpd.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    rt.start()
    log_event("STARTUP", f"serving on {host}:{rt.cfg.port}", mode=rt.cfg.mode)
    httpd.serve_forever()


def serve_startup_failure(port: int, reason: str) -> None:
    """Startup failed: answer every request with 503 and the reason, and never trade.

    The platform's health check fails, so the deploy is marked unhealthy,
    and anyone opening the URL reads why instead of a connection error.
    """
    body = json.dumps({"ok": False, "system": "STARTUP_FAILED", "reason": reason}).encode()

    class Failed(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def _reply(self):
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        do_GET = do_POST = _reply

    ThreadingHTTPServer(("0.0.0.0", port), Failed).serve_forever()
