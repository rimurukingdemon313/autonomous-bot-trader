"""One-off diagnostic (side branch only): why do forward proposals stay unresolved, and what would the trades the
hard gate refused on 2026-10-14 have made? Reads the published paper database and live Yahoo bars. Never trades."""
import gzip, json, shutil, sqlite3, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, ".")
from aitrader.data.yahoo import YahooFeed
from aitrader.learning.forward import ForwardLedger, POST_WINDOW_MAX_S, walk

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
subprocess.run(["git", "fetch", "-q", "origin", "paper-forward-data"], check=True)
raw = subprocess.run(["git", "show", "FETCH_HEAD:aitrader.db.gz"], check=True, capture_output=True).stdout
(out / "db.sqlite").write_bytes(gzip.decompress(raw))
c = sqlite3.connect(out / "db.sqlite")
outs = {d for (d,) in c.execute("select decision_id from forward_outcomes")}
props = [json.loads(p) for (p,) in c.execute("select payload from forward_proposals order by seq")]
pending = [p for p in props if p["decision_id"] not in outs]
syms = sorted({p["symbol"] for p in pending})
now = int(time.time())
feed = YahooFeed(syms, lambda: int(time.time()))
rows, refused = [], []
for p in pending:
    until = p["t"] + p["hold_s"] + POST_WINDOW_MAX_S
    span = max(0, min(until, now) - p["t"])
    tried = []
    for tf, per in (("M1", 60), ("M5", 300), ("M15", 900), ("H1", 3600)):
        n = span // per + 3
        b = None if n > 1500 else feed.bars_tf(p["symbol"], tf, now, int(n))
        tried.append({"tf": tf, "n": int(n), "bars": None if b is None else len(b),
                      "first": None if b is None or len(b) == 0 else int(b.open_time[0]),
                      "reaches": None if b is None or len(b) == 0 else bool(int(b.open_time[0]) <= p["t"] + per)})
    tf, bars = ForwardLedger._bars(feed, p["symbol"], p["t"], until, now)
    o = walk(p, bars, now) if bars is not None else None
    r = {"decision_id": p["decision_id"], "symbol": p["symbol"], "t": p["t"], "family": p.get("family"),
         "route": p.get("route"), "risk_approved": p.get("risk_approved"), "executed": p.get("executed"),
         "chosen_tf": tf, "tried": tried, "outcome": o}
    if bars is not None and o is None:  # walk to the end, ignoring the post-exit wait, to see the exit
        q = dict(p); q["hold_s"] = p["hold_s"]
        r["note"] = "walk returned None with bars available"
    rows.append(r)
    if p.get("family") == "DUAL_AI" and p.get("risk_approved") and not p.get("executed") and p["t"] >= 1791960000:
        refused.append(r)
(out / "forward_diag.json").write_text(json.dumps({"now": now, "pending": rows, "errors": {f"{k[0]} {k[1]}": v for k, v in feed.errors.items()}}, indent=1, default=str))
lines = [f"pending {len(pending)}; refused-by-gate trades {len(refused)}", ""]
for r in rows[:40]:
    lines.append(f"{time.strftime('%m-%d %H:%M', time.gmtime(r['t']))} {r['symbol']} {r['family']} chosen={r['chosen_tf']} "
                 f"outcome={None if not r['outcome'] else (r['outcome'].get('reason'), r['outcome'].get('net_r'))} "
                 + " ".join(f"{x['tf']}:{x['bars']}/{x['n']}{'' if x['reaches'] else '!'}" for x in r["tried"]))
(out / "REPORT.md").write_text("\n".join(lines) + "\n\nerrors: " + json.dumps({f"{k[0]} {k[1]}": v for k, v in feed.errors.items()})[:3000] + "\n")
import traceback
from aitrader.memory.db import Database
try:
    led = ForwardLedger(Database(out / "db.sqlite"), lambda: int(time.time()))
    t0 = time.time()
    done = led.resolve(feed, now, limit=20)
    lines.append(f"\nresolve(): {len(done)} resolved in {time.time() - t0:.1f}s; stats {led.stats}")
except Exception:
    lines.append("\nresolve() RAISED:\n" + traceback.format_exc())
(out / "REPORT.md").write_text("\n".join(lines) + "\n\nerrors: " + json.dumps({f"{k[0]} {k[1]}": v for k, v in feed.errors.items()})[:3000] + "\n")
print("\n".join(lines[-12:]))
(out / "db.sqlite").unlink()
print("\n".join(lines[:50]))
