"""One-off diagnostic (side branch only): the desk of dual-ai 1.18.0, end to end, with the REAL free models.

What changed since the last live check: one model per seat with no stand-ins (1.17.0), 16,000 tokens for each
trader's answer, and the desk's playbook in every packet (1.18.0, about 1,300 tokens more). This checks that the free
traders still answer usably with it: how many answers are cut at max_tokens, how many tokens each prompt takes, and
which model holds each seat.

Each decision replays a past hour of Monday 2 November (London morning), with Yahoo bars as they were then. Every pair
runs on its own throw-away paper account. FREE models only: OPENROUTER_PAID_TRIAL=off, and the hours replayed are before
the senior's funded window opens (15:00 UTC), so the senior is not asked and nothing is spent."""
import json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["OPENROUTER_PAID_TRIAL"] = "off"
from scripts import dual_ai_check as C  # noqa: E402
from aitrader.agents.dual_ai import DUAL_AI_VERSION, MIN_CONFIDENCE, PLAYBOOK  # noqa: E402

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
TIMES = [datetime(2026, 11, 2, 8, 0, 30, tzinfo=timezone.utc), datetime(2026, 11, 2, 9, 0, 30, tzinfo=timezone.utc)]
PAIRS = ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "EURJPY")
rep = {"version": DUAL_AI_VERSION, "playbook": PLAYBOOK["version"], "floor": MIN_CONFIDENCE, "runs": []}
started = time.time()
for when in TIMES:
    for sym in PAIRS:
        if time.time() - started > 95 * 60:
            rep["runs"].append({"symbol": sym, "at": when.isoformat(), "skipped": "time budget of the check"})
            continue
        d = out / f"{when:%d%H}_{sym}"
        d.mkdir(parents=True, exist_ok=True)
        res = C.guarded(C.desk, sym, int(when.timestamp()), True, d, scripted=False)
        rep["runs"].append({"symbol": sym, "at": when.isoformat(), **res})
        print(sym, when.isoformat(), json.dumps({k: res.get(k) for k in ("ok", "error", "seconds")}), flush=True)
        (out / "check.json").write_text(json.dumps(rep, indent=1, default=str))

lines = [f"# Desk {DUAL_AI_VERSION} ({PLAYBOOK['version']}), live check with the free models, floor {MIN_CONFIDENCE}", "",
         "| At (UTC) | Pair | Trader 1 | Trader 2 | Rule | Final | Risk | Models | Seconds |", "|---|---|---|---|---|---|---|---|---|"]
calls, conf = [], []
for r in rep["runs"]:
    for d in r.get("decisions") or []:
        t1, t2 = d.get("trader1") or {}, d.get("trader2") or {}
        risk = d.get("risk") or {}
        calls += d.get("calls") or []
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
cut = [c for c in calls if "cut at max_tokens" in str(c.get("status") or "") + str(c.get("error") or "")]
lines += ["", f"Both traders answered: {len(conf)} · agreed: {len(agree)} · agreed with both at {MIN_CONFIDENCE} or more: "
          f"{sum(1 for m in agree if m >= MIN_CONFIDENCE)} · lower confidences when agreeing: {sorted(agree)}", "",
          f"Calls: {len(calls)} · usable: {sum(1 for c in calls if c.get('status') == 'OK')} · cut at max_tokens: {len(cut)}"]
for role in ("vision", "judge", "verifier", "senior"):
    toks = sorted(c["tokens"] for c in calls if c.get("role") == role and isinstance(c.get("tokens"), int))
    if toks:
        lines.append(f"- {role}: {len(toks)} answers, tokens median {toks[len(toks) // 2]}, max {toks[-1]}")
(out / "check.json").write_text(json.dumps(rep, indent=1, default=str))
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
