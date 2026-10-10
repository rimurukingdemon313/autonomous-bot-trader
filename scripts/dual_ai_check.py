"""A live check of the dual-AI desk: the real OpenRouter, real Yahoo prices, the owner's key from the Actions
secret, on a GitHub runner (.github/workflows/dual-ai-check.yml). Paper only, on a temporary account that is
thrown away. It answers one question: does every part work with the real services, and if not, which and why.

    OPENROUTER_API_KEY=... python scripts/dual_ai_check.py --out dai-check

1 catalog   GET /models, the FREE selection per role (no key needed)
2 key       GET /key: accepted? free tier? daily quota? (never the key itself)
3 models    one small JSON request to each selected model; the vision model is also asked to read the chart
4 chart     the PNG Trader 1 would read, from live Yahoo bars
5 desk      one complete decision per symbol through the production runtime (PAPER_FORWARD, dual_ai): both
            traders, the debate if they disagree, the risk engine, the paper broker
On a weekend or holiday (the latest bar hours old) section 5 replays the last market close and says so.

Writes check.json, REPORT.md and the charts. Refuses to write anything that contains the key. About 10 of the
key's free daily requests are used.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402

from aitrader.llm.openrouter import OpenRouterClient, OpenRouterConfig  # noqa: E402

SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY")


def iso(t) -> str:
    return datetime.fromtimestamp(int(t), timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def ping(client: OpenRouterClient, role: str, model: str, image_url: str | None = None) -> dict:
    """One small request to one model, outside the desk's selection, to see that it answers valid JSON."""
    if image_url:
        user = [{"type": "text", "text": "Which instrument and which execution timeframe does this chart's header name?"},
                {"type": "image_url", "image_url": {"url": image_url}}]
        system = 'Reply with ONE JSON object only: {"instrument": "...", "timeframe": "..."}'
        check = (lambda d: None if isinstance(d.get("instrument"), str) else "instrument missing")
    else:
        user = "Reply with the JSON object now."
        system = 'Reply with ONE JSON object only: {"ok": true}'
        check = (lambda d: None if d.get("ok") is True else "ok must be true")
    t0 = time.time()
    res = client._one_model(role, model, [{"role": "system", "content": system}, {"role": "user", "content": user}],
                            check, 800)
    out = {**res.record(), "seconds": round(time.time() - t0, 1)}
    if res.ok:
        out["answer"] = res.data
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dai-check")
    ap.add_argument("--symbols", default=",".join(SYMBOLS))
    a = ap.parse_args()
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    key = (os.environ.get("OPENROUTER_API_KEY") or "").strip()
    cfg = OpenRouterConfig.from_env()
    rep: dict = {"time": iso(time.time()), "key": cfg.public(), "sections": {}}
    client = OpenRouterClient(cfg)

    # 1 catalog
    sel = client.refresh_models(force=True)
    rep["sections"]["catalog"] = {"ok": bool(sel.vision and sel.judge), "catalog_models": sel.catalog_total,
                                  "free_models": sel.free_total, "error": sel.error,
                                  "trader1": [r["id"] for r in sel.vision[:3]], "trader2": [r["id"] for r in sel.judge[:3]],
                                  "debate": [r["id"] for r in sel.verifier[:3]]}

    # 2 key
    if cfg.configured:
        info = client.check_key(force=True)
        rep["sections"]["key"] = {"ok": bool(info.get("ok")), **info}
    else:
        rep["sections"]["key"] = {"ok": False, "status": "NOT_CONFIGURED",
                                  "fix": "add the repository secret OPENROUTER_API_KEY"}

    # 4 chart (before 3: the vision model is asked to read it)
    from aitrader.agents.dual_ai import build_chart  # noqa: E402
    from aitrader.agents.types import MarketContext  # noqa: E402
    from aitrader.data.yahoo import YahooFeed  # noqa: E402
    now = int(time.time())
    feed = YahooFeed(list(a.symbols.split(",")), lambda: now)
    last_close = None
    charts = {}
    for s in a.symbols.split(","):
        h1 = feed.bars(s, now, 24 * 30)
        if h1 is None or len(h1) == 0:
            charts[s] = {"ok": False, "error": feed.data_error(s) if hasattr(feed, "data_error") else "no bars"}
            continue
        full = np.nonzero(np.asarray(h1.mid_high) > np.asarray(h1.mid_low))[0]
        if len(full):
            last_close = max(last_close or 0, int(h1.available_at[full[-1]]))
        q = feed.quote(s, now)
        t = int(h1.available_at[-1])
        try:
            from aitrader.research.labels import atr24  # noqa: E402
            atr = float(atr24(h1)[-1])
            ctx = MarketContext(s, "H1", t, None, None, atr if np.isfinite(atr) else None,
                                q.bid if q else float(h1.bid_close[-1]), q.ask if q else float(h1.ask_close[-1]),
                                t, {}, None)
            ctx.bars = {"H1": h1}
            m15 = feed.bars_tf(s, "M15", now, 300)
            if m15 is not None and len(m15):
                ctx.bars["M15"] = m15
            ch = build_chart(ctx)
            (out_dir / f"chart_{s}.png").write_bytes(ch.png)
            charts[s] = {"ok": True, "bytes": len(ch.png), "execution_timeframe": ch.meta["execution_timeframe"],
                         "last_bar_closed": iso(ch.meta["last_bar_available"]), "trend": ch.facts["trend"],
                         "_url": ch.data_url()}
        except Exception as exc:  # noqa: BLE001
            charts[s] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    rep["sections"]["chart"] = {"ok": any(c.get("ok") for c in charts.values()),
                                **{s: {k: v for k, v in c.items() if k != "_url"} for s, c in charts.items()}}

    # 3 models
    if cfg.configured and rep["sections"]["key"]["ok"]:
        pings = {}
        url = next((c["_url"] for c in charts.values() if c.get("ok")), None)
        for role, rows in (("vision", sel.vision), ("judge", sel.judge), ("verifier", sel.verifier)):
            if rows:
                pings[rows[0]["id"]] = guarded(ping, client, role, rows[0]["id"])
        if url and sel.vision:
            pings[sel.vision[0]["id"] + " (reads the chart)"] = guarded(ping, client, "vision", sel.vision[0]["id"], url)
        rep["sections"]["models"] = {"ok": bool(pings) and all(p["ok"] for p in pings.values()), **pings}
    else:
        rep["sections"]["models"] = {"ok": False, "skipped": "no accepted key"}

    # 5 the desk, end to end: first with scripted traders (no request is sent: it checks everything around the
    # models on real prices), then with the real models when the key is accepted
    replay = last_close is not None and now - last_close > 2 * 3600
    clock_t = (last_close + 90) if replay else now
    rep["sections"]["desk_dry_run"] = guarded(desk, a.symbols, clock_t, replay, out_dir, scripted=True)
    if cfg.configured and rep["sections"]["key"]["ok"]:
        rep["sections"]["desk"] = guarded(desk, a.symbols, clock_t, replay, out_dir, scripted=False)
    else:
        rep["sections"]["desk"] = {"ok": False, "skipped": "no accepted key"}

    rep["all_ok"] = all(v.get("ok") for v in rep["sections"].values())
    text = json.dumps(rep, indent=1, default=str)
    md = report_md(rep)
    if key and len(key) >= 8 and (key in text or key in md):
        raise SystemExit("refusing to write: the key appears in the output")
    (out_dir / "check.json").write_text(text + "\n")
    (out_dir / "REPORT.md").write_text(md)
    print(md)
    return 0


def ReplayQuoteFeed(symbols, clock, spreads_pips):  # noqa: N802 - a class built on the real feed
    """The real Yahoo feed, replayed at `clock`: bars as they were then, and a quote at the close of the last
    completed bar (spread as the live feed estimates it), stamped with the replay time. Only for the check on a
    day the market is closed; the service itself never replays."""
    from aitrader.data.yahoo import YahooFeed  # noqa: E402
    from aitrader.risk.engine import Quote  # noqa: E402

    class _Feed(YahooFeed):
        def quote(self, symbol, now=None):
            t = self.clock()
            for tf in ("M5", "M15"):
                b = self.bars_tf(symbol, tf, t, 3)
                if b is not None and len(b):
                    break
            else:
                b = self.bars(symbol, t, 3)
            if b is None or len(b) == 0:
                return None
            mid = float(b.mid_close[-1])
            half = self.spreads.get(symbol, 0.0) / 2
            return Quote(symbol, mid - half, mid + half, int(t))

    return _Feed(symbols, clock, spreads_pips=spreads_pips)


def guarded(fn, *args, **kw) -> dict:
    """A section that raises is reported with its traceback, never lost: the report is always written."""
    try:
        return fn(*args, **kw)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc()[-3000:]}


def desk(symbols: str, clock_t: int, replay: bool, out_dir: Path, scripted: bool) -> dict:
    """One decision per symbol through the production runtime, PAPER_FORWARD, on a temporary paper account."""
    import aitrader.service.runtime as runtime_mod  # noqa: E402
    from aitrader.service.config import ServiceConfig  # noqa: E402
    from aitrader.service.runtime import Runtime  # noqa: E402
    os.environ["DECISION_MODE"] = "dual_ai"
    real_client = runtime_mod.OpenRouterClient
    if scripted:
        from scripts.dual_ai_simulation import rules  # noqa: E402
        from tests.openrouter_kit import FakeOpenRouter, client as fake_client  # noqa: E402
        fake = FakeOpenRouter(rules)
        runtime_mod.OpenRouterClient = lambda cfg: fake_client(fake, clock=lambda: float(clock_t))
    tmp = Path(tempfile.mkdtemp(prefix="dai-check-"))
    env = {**os.environ, "MODE": "PAPER_FORWARD", "DATA_DIR": str(tmp), "DATA_SOURCE": "yahoo", "SYMBOLS": symbols,
           "SYMBOLS_PER_CYCLE": "0", "DECISION_INTERVAL_MIN": "75"}
    try:
        scfg = ServiceConfig.from_env(env)
        kw = {}
        if replay:
            from aitrader.broker.paper import PaperBroker  # noqa: E402
            from aitrader.memory.db import Database  # noqa: E402
            feed = ReplayQuoteFeed(symbols.split(","), lambda: clock_t, scfg.spreads_pips)
            kw = {"feed": feed, "broker": PaperBroker(feed, lambda: clock_t, Database(tmp / "aitrader.db"),
                                                      start_balance=scfg.start_balance)}
        rt = Runtime(scfg, clock=lambda: clock_t, **kw)
        if replay:
            rt.broker.db = rt.db
        t0 = time.time()
        try:
            rt.run_cycle(t=clock_t, decide=True)
            err = rt.health.get("last_cycle_error")
        except Exception as exc:  # noqa: BLE001
            err = f"{type(exc).__name__}: {exc}"
        view = rt.dual_ai()
    finally:
        runtime_mod.OpenRouterClient = real_client
    result = {
        "ok": err is None and bool(view["analyses"]), "error": err, "seconds": round(time.time() - t0, 1),
            "replay_of_last_close": iso(clock_t) if replay else None, "openrouter_status": view["openrouter"]["status"],
            "decisions": [{"symbol": x["symbol"], "decision": x["decision"], "rule": (x.get("consensus") or {}).get("rule"),
                           "trader1": x.get("trader1"), "trader2": x.get("trader2"), "debate": x.get("verifier"),
                           "models": x.get("models"), "risk": x.get("risk"),
                           "calls": [{k: c.get(k) for k in ("role", "model", "status", "latency_ms", "tokens", "error")}
                                     for c in (x.get("calls") or [])], "reason": x.get("reason")}
                          for x in view["analyses"]],
            "paper_positions": [{k: p.get(k) for k in ("symbol", "side", "qty", "entry", "stop", "target")}
                                for p in view["open_positions"]],
            "live_trading": rt.cfg.public()["live_trading"], "scripted_traders": scripted}
    if not scripted:
        for sym in (view.get("charts") or {}):
            png = rt.dual_ai_chart(sym)
            if png:
                (out_dir / f"desk_chart_{sym}.png").write_bytes(png)
    return result


def report_md(rep: dict) -> str:
    s = rep["sections"]
    mark = lambda ok: "OK" if ok else "PROBLEM"  # noqa: E731
    lines = [f"# Dual-AI live check — {rep['time']}", "",
             f"Key: {'set (' + str(rep['key'].get('key_hint')) + ')' if rep['key'].get('configured') else 'NOT SET'} · "
             f"overall: **{'ALL OK' if rep['all_ok'] else 'SEE PROBLEMS BELOW'}**", "",
             f"1. Catalog: {mark(s['catalog']['ok'])} — {s['catalog']['free_models']} free of "
             f"{s['catalog']['catalog_models']}; trader 1 `{(s['catalog']['trader1'] or ['none'])[0]}`, trader 2 "
             f"`{(s['catalog']['trader2'] or ['none'])[0]}`, debate `{(s['catalog']['debate'] or ['none'])[0]}`",
             f"2. Key: {mark(s['key']['ok'])} — " + json.dumps({k: v for k, v in s['key'].items() if k != 'ok'}),
             f"3. Models: {mark(s['models']['ok'])}"]
    for m, p in s["models"].items():
        if isinstance(p, dict):
            lines.append(f"   - `{m}`: {p.get('status')} in {p.get('seconds')} s"
                         + (f" — {p.get('error')}" if p.get("error") else f" — {json.dumps(p.get('answer'))}"))
    lines.append(f"4. Chart: {mark(s['chart']['ok'])} — " + "; ".join(
        f"{k} {v.get('execution_timeframe') or v.get('error')}" for k, v in s["chart"].items() if isinstance(v, dict)))
    for title, d in (("5a. Desk dry run (scripted traders, real prices, no request sent)", s["desk_dry_run"]),
                     ("5b. Desk end to end with the real models", s["desk"])):
        lines += desk_lines(title, d, mark)
    lines += ["", "Paper only, on a temporary account that is discarded. Live trading: false.", ""]
    return "\n".join(lines)


def desk_lines(title: str, d: dict, mark) -> list:
    lines = []
    if d.get("traceback"):
        lines += [f"{title}: PROBLEM — {d['error']}", "```", d["traceback"], "```"]
        return lines
    lines.append(f"{title}: {mark(d['ok'])}" + (f" — replay of the last market close {d['replay_of_last_close']}"
                                                         if d.get("replay_of_last_close") else "")
                 + (f" — {d.get('error') or d.get('skipped')}" if d.get("error") or d.get("skipped") else ""))
    for x in d.get("decisions") or []:
        t1, t2, db = x.get("trader1") or {}, x.get("trader2") or {}, x.get("debate") or {}
        risk = x.get("risk")
        lines.append(f"   - {x['symbol']}: **{x['decision']}** ({x['rule']}) — trader 1 {t1.get('direction', '-')} "
                     f"{t1.get('confidence', '')}, trader 2 {t2.get('direction', '-')} {t2.get('confidence', '')}"
                     + (f", debate {db.get('direction')}" if db else "")
                     + (f", risk {'APPROVED' if risk['approved'] else 'REJECTED: ' + '; '.join(risk.get('reasons') or [])}"
                        if risk else ""))
        for c in x.get("calls") or []:
            lines.append(f"     - {c['role']} `{c['model']}` {c['status']} {round((c.get('latency_ms') or 0) / 1000, 1)} s"
                         + (f" — {c['error']}" if c.get("error") else ""))
        if x["decision"] == "NO_TRADE":
            lines.append(f"     - reason: {x.get('reason')}")
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
