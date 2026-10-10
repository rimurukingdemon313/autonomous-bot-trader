"""A PAPER_FORWARD run of the dual-AI desk with OpenRouter MOCKED: the production runtime, scripted traders.

    python scripts/dual_ai_simulation.py --days 5 --out research/results/dual-ai-mock-simulation.json

What is real: the runtime, orchestrator, chart renderer, validation, agreement/debate, risk engine, hard gate,
execution engine, paper broker (fills, costs, stops, targets, time exits), forward ledger, learning records and
dashboard views. What is not: the market (a deterministic synthetic replay, tests/integration/test_pipeline.py)
and the three "traders", which answer by fixed rules read from the same packets the real models receive
(Trader 1: the chart's trend and last structure break; Trader 2: 20-bar momentum in the raw rows; the debate:
the higher timeframe). No request reaches openrouter.ai and no key is used.

It shows the pipeline working end to end and how often each path is taken. Its P&L is the P&L of fixed rules on
synthetic prices: it says nothing about any model, and nothing about profitability.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

import aitrader.service.runtime as runtime_mod  # noqa: E402
from aitrader.broker.paper import PaperBroker  # noqa: E402
from aitrader.data.bars import BarSeries  # noqa: E402
from aitrader.memory.db import Database  # noqa: E402
from aitrader.risk.profile import PAPER_FORWARD_200K  # noqa: E402
from aitrader.service.config import ServiceConfig  # noqa: E402
from aitrader.service.runtime import Runtime  # noqa: E402
from tests.integration.test_cadence import LiveLikeFeed, minute_bars  # noqa: E402
from tests.integration.test_pipeline import START, market  # noqa: E402
from tests.integration.test_service import Clock, _write_kb  # noqa: E402
from tests.openrouter_kit import FakeOpenRouter, KEY, answer, client, packet_of  # noqa: E402

SYMS = ("EURUSD", "GBPUSD", "USDJPY")


class SimFeed(LiveLikeFeed):
    """The replay, serving H1 through bars_tf as the live Yahoo feed does (the forward ledger resolves on it).
    The replay has M5 bars only before the start; once they are hours old they are not served, as a live feed
    would serve current ones."""

    def bars_tf(self, symbol, timeframe, as_of, count):
        if timeframe == "H1":
            b = self.bars(symbol, as_of, count)
            return b if b is not None and len(b) else None
        b = super().bars_tf(symbol, timeframe, as_of, count)
        return b if b is not None and len(b) and int(b.available_at[-1]) >= as_of - 3600 else None


def side_of(word: str | None) -> str | None:
    w = (word or "").upper()
    return "BUY" if w.startswith(("UP", "BULL")) else "SELL" if w.startswith(("DOWN", "BEAR")) else None


def rules(role, body):
    p = packet_of(body)
    q, marks = p["quote"], p["chart_marks"]
    atr = marks["atr_h1"]
    ex_tf, htf = marks["execution_timeframe"], marks.get("higher_timeframe")
    breaks = marks.get("structure_breaks") or []
    htf_side = side_of((marks.get("trend") or {}).get(htf)) or side_of(
        (marks.get("higher_timeframe_breaks") or [{}])[-1].get("direction"))
    if role == "trader1":
        side = side_of((marks.get("trend") or {}).get(ex_tf)) or side_of(breaks[-1]["direction"] if breaks else None)
        side = side or htf_side or "BUY"
        conf = 80 if side == htf_side else 62
        return answer(side, q["bid"], q["ask"], atr, confidence=conf, stop_atr=1.2, target_atr=2.0)
    if role == "trader2":
        rows = p["execution_bars"]["rows"]
        move = (rows[-1][4] - rows[-20][4]) / atr if len(rows) >= 20 else 0.0
        side = "BUY" if move >= 0 else "SELL"
        return answer(side, q["bid"], q["ask"], atr, confidence=int(min(90, 55 + 8 * abs(move))),
                      stop_atr=1.0, target_atr=1.8)
    return {"direction": htf_side or p["trader1_analysis"]["direction"], "confidence": 65,
            "reason": "the higher timeframe decides"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=float, default=5)
    ap.add_argument("--every-min", type=int, default=75)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="dual-ai-sim-"))
    fake = FakeOpenRouter(rules)
    clock_box: dict = {}
    # the client counts its daily quota on the simulated clock, as production counts it on the real one
    runtime_mod.OpenRouterClient = lambda cfg: client(fake, clock=lambda: float(clock_box["c"].t))
    import os
    os.environ["DECISION_MODE"] = "dual_ai"
    _write_kb(tmp / "kb")
    data = {s: market(s, START, 24 * 7 * 20, i + 1, 1.30 if "JPY" not in s else 110.0) for i, s in enumerate(SYMS)}
    clock = Clock(int(data["EURUSD"].available_at[2000]))
    clock_box["c"] = clock
    lower = {}
    for s, h1 in data.items():
        mid = float(h1.mid_close[2000])
        b = minute_bars(s, clock.t - 300 * 60, [mid * 0.999] * 60, [mid * 1.001] * 60, mid)
        lower[(s, "M5")] = BarSeries.from_columns(s, "M5", "test", **{f: getattr(b, f) for f in (
            "bid_open", "bid_high", "bid_low", "bid_close", "ask_open", "ask_high", "ask_low", "ask_close",
            "ticks", "spread_mean", "spread_max")}, open_time=clock.t - 300 * 60 + 300 * np.arange(60))
    feed = SimFeed(data, lower)
    (tmp / "rt").mkdir()
    broker = PaperBroker(feed, clock, Database(tmp / "rt" / "aitrader.db"), start_balance=200_000)
    rt = Runtime(ServiceConfig(mode="PAPER_FORWARD", data_dir=str(tmp / "rt"), port=0, symbols=SYMS,
                               dashboard_token="t", decision_interval_min=a.every_min, symbols_per_cycle=1,
                               hard_profile=PAPER_FORWARD_200K),
                 feed=feed, broker=broker, clock=clock, knowledge_dir=tmp / "kb")
    rt.broker.db = rt.db
    end = clock.t + int(a.days * 86400)
    next_decision = clock.t
    while clock.t < end:
        clock.t += 900
        rt.monitor_once()
        if clock.t >= next_decision:
            rt.run_cycle(decide=True)
            next_decision = clock.t + a.every_min * 60
    rules_seen = Counter()
    for row in rt.db.query("SELECT payload FROM decisions"):
        p = json.loads(row["payload"])
        rules_seen[(((p.get("ai") or {}).get("dual_ai") or {}).get("consensus") or {}).get("rule")] += 1
    stages = Counter(" -> ".join(json.loads(r["payload"])["stages"]) for r in
                     rt.db.query("SELECT payload FROM events WHERE type='PIPELINE'"))
    view = rt.dual_ai()
    pf = rt.paper_forward()
    raw = b"".join(f.read_bytes() for f in (tmp / "rt").rglob("*") if f.is_file())
    out = {
        "note": "MOCKED OpenRouter (fixed-rule traders) on a synthetic replay: shows the pipeline, not a model's "
                "skill and not profitability",
        "simulated_days": a.days, "decision_every_min": a.every_min, "decisions": sum(rules_seen.values()),
        "decisions_by_rule": dict(rules_seen), "pipeline_paths": dict(stages),
        "requests_by_role": dict(Counter(c["role"] for c in fake.calls)), "requests_total": len(fake.calls),
        "models_used": dict(Counter(c["model"] for c in fake.calls)),
        "performance": view["performance"], "desk_record": view["record"],
        "account": pf.get("account"), "risk_status": pf.get("risk_status"), "bot_status": pf.get("bot_status"),
        "open_positions": len(rt.broker.positions()), "forward_ledger": dict(rt.orch.forward.stats),
        "key_leaked": KEY.encode() in raw or KEY in json.dumps([view, pf, rt.status()], default=str),
        "live_trading": rt.cfg.public()["live_trading"], "mode": rt.cfg.mode,
    }
    text = json.dumps(out, indent=1, default=str)
    print(text)
    if a.out:
        Path(a.out).write_text(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
