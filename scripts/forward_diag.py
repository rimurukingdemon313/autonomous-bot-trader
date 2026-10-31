"""One-off diagnostic (side branch only): the H1 desk of dual-ai 1.12.0, end to end, with the REAL free models.

The market is closed (Saturday), so each decision replays a past hour when new positions were allowed (Thursday
29 and Friday 30 October, London morning), with Yahoo bars as they were then and a quote at that close. Every pair
runs on its own throw-away paper account, so no open position or currency exposure blocks the next. FREE models
only: OPENROUTER_PAID_TRIAL=off, and the client runs on the real clock, past the paid trial's window. It checks
that the H1 chart is drawn, that the free traders answer on it, what confidences they state on H1, and that the
floor (65) and the risk engine do what they say."""
import json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["OPENROUTER_PAID_TRIAL"] = "off"
from scripts import dual_ai_check as C  # noqa: E402
from aitrader.agents.dual_ai import DUAL_AI_VERSION, EXECUTION_TF, MIN_CONFIDENCE  # noqa: E402

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
TIMES = [datetime(2026, 10, 29, 8, 0, 30, tzinfo=timezone.utc), datetime(2026, 10, 30, 9, 0, 30, tzinfo=timezone.utc)]
PAIRS = ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "EURJPY")
rep = {"version": DUAL_AI_VERSION, "execution_tf": EXECUTION_TF, "floor": MIN_CONFIDENCE, "runs": []}
started = time.time()
for when in TIMES:
    for sym in PAIRS:
        if time.time() - started > 95 * 60:
            rep["runs"].append({"symbol": sym, "at": when.isoformat(), "skipped": "time budget of the check"})
            continue
        d = out / f"{when:%d%H}_{sym}"
        d.mkdir(parents=True, exist_ok=True)  # the desk writes its chart there
        res = C.guarded(C.desk, sym, int(when.timestamp()), True, d, scripted=False)
        rep["runs"].append({"symbol": sym, "at": when.isoformat(), **res})
        print(sym, when.isoformat(), json.dumps({k: res.get(k) for k in ("ok", "error", "seconds")}), flush=True)
        (out / "check.json").write_text(json.dumps(rep, indent=1, default=str))

lines = [f"# H1 desk, live check with the free models ({DUAL_AI_VERSION}, execution {EXECUTION_TF}, floor {MIN_CONFIDENCE})", "",
         "| At (UTC) | Pair | Trader 1 | Trader 2 | Rule | Final | Risk | Models | Seconds |", "|---|---|---|---|---|---|---|---|---|"]
conf = []
for r in rep["runs"]:
    for d in r.get("decisions") or []:
        t1, t2 = d.get("trader1") or {}, d.get("trader2") or {}
        risk = d.get("risk") or {}
        if isinstance(t1.get("confidence"), (int, float)) and isinstance(t2.get("confidence"), (int, float)):
            conf.append((t1["direction"] == t2["direction"], min(t1["confidence"], t2["confidence"])))
        lines.append(f"| {r['at'][5:16]} | {d['symbol']} | {t1.get('direction', '-')} {t1.get('confidence', '')} | "
                     f"{t2.get('direction', '-')} {t2.get('confidence', '')} | {d.get('rule')} | {d.get('decision')} | "
                     f"{('APPROVED' if risk.get('approved') else 'REFUSED: ' + '; '.join((risk.get('reasons') or [])[:2])) if risk else '-'} | "
                     f"{(d.get('models') or {}).get('trader1')} / {(d.get('models') or {}).get('trader2')} | {r.get('seconds')} |")
        if d.get("reason"):
            lines.append(f"|  |  | {str(d['reason'])[:220].replace('|', '/')} |  |  |  |  |  |  |")
    if r.get("error") or r.get("skipped"):
        lines.append(f"| {r['at'][5:16]} | {r['symbol']} | ERROR {str(r.get('error') or r.get('skipped'))[:200]} |  |  |  |  |  |  |")
agree = [m for a, m in conf if a]
lines += ["", f"Both traders answered: {len(conf)} · agreed: {len(agree)} · agreed with both at {MIN_CONFIDENCE} or more: "
          f"{sum(1 for m in agree if m >= MIN_CONFIDENCE)} · lower confidences when agreeing: {sorted(agree)}"]
(out / "check.json").write_text(json.dumps(rep, indent=1, default=str))
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
