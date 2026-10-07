"""One shift of the continuous PAPER_FORWARD run, on a GitHub runner (.github/workflows/paper-forward.yml).

    MODE=PAPER_FORWARD DATA_DIR=pf-state python scripts/paper_forward_shift.py --publish pf-pub --minutes 345

It starts the real service (`Runtime`: the same scheduler, risk engine, hard gate, paper broker and learning as
a deployment). It runs that for `--minutes`, then stops it cleanly. Every `--every` minutes it writes the PAPER
FORWARD TEST dashboard view, the same object `/api/paper_forward` serves, to the publish directory, which the
workflow commits to the `paper-forward-data` branch. The state directory (database, live memory) is carried from
shift to shift by the workflow, so the paper account, its positions and its locks persist.

PAPER ONLY. There is no live path; this script cannot create one.
"""

from __future__ import annotations

import argparse
import gzip
import json
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aitrader.service.config import ServiceConfig  # noqa: E402


def money(x) -> str:
    return "n/a" if x is None else f"${x:,.2f}"


def fmt(x, spec: str) -> str:
    return "n/a" if x is None else spec.format(x)


def report_md(v: dict, shift: dict) -> str:
    a, o = v.get("account") or {}, (v.get("performance") or {}).get("overall") or {}
    lines = [
        "# PAPER FORWARD TEST — NOT REAL MONEY", "",
        f"Updated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC · mode `{v['mode']}` · profile `{v['profile']}` · "
        f"shift started {shift['started']} · decision system `{shift['decision_mode']}`", "",
        f"Research status (historical, unchanged): **{v['research_status']}**. This run measures the system forward; "
        "it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.", "",
        "| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
        f"| {money(v.get('start_balance'))} | {money(a.get('equity'))} | {money(a.get('today_pnl'))} | "
        f"{money(a.get('total_pnl'))} | {money(a.get('drawdown_from_start'))} | {len(v.get('open_positions') or [])} | "
        f"{o.get('trades', 0)} ({o.get('sample', 'none')}) | {fmt(o.get('win_rate'), '{:.1%}')} | "
        f"{fmt(o.get('expectancy_r'), '{:+.3f}R')} | {fmt(o.get('profit_factor'), '{:.2f}')} | "
        f"{v.get('risk_status')} | {v.get('bot_status')} |", "",
        "## Last decisions (decision → risk → paper execution)", ""]
    for e in v.get("pipeline") or []:
        when = datetime.fromtimestamp(e["t"], timezone.utc).strftime("%m-%d %H:%M")
        lines.append(f"- {when} {e['symbol']} {e['decision']}: {' → '.join(e['stages'])}"
                     + (f" — {e['reason'][:200]}" if e.get("reason") else ""))
    lines += ["", "## Open paper positions", "", "| Symbol | Side | Qty | Entry | Stop | Target | P&L |", "|---|---|---|---|---|---|---|"]
    for p in v.get("open_positions") or []:
        lines.append(f"| {p['symbol']} | {p['side']} | {p['qty']} | {p['entry']} | {p['stop']} | {p['target']} | {money(p.get('pnl'))} |")
    lines += ["", "## Closed paper trades (latest 20)", "",
              "| Closed | Symbol | Side | Net | R | Costs | Exit | Source |", "|---|---|---|---|---|---|---|---|"]
    for t in v.get("recent_trades") or []:
        when = datetime.fromtimestamp(t["closed"], timezone.utc).strftime("%m-%d %H:%M")
        lines.append(f"| {when} | {t['symbol']} | {t['direction']} | {money(t.get('net_pnl'))} | "
                     f"{fmt(t.get('r'), '{:+.2f}')} | {money(t.get('costs_total'))} | "
                     f"{t.get('exit_reason')} | {t.get('source') or t.get('agent')} |")
    lines += ["", "Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.", ""]
    return "\n".join(lines)


def publish(rt, pub: Path, shift: dict, push: bool) -> None:
    v = rt.paper_forward()
    v["shift"] = shift
    v["health"] = {k: rt.health.get(k) for k in ("last_cycle", "last_cycle_error", "cycles")}
    (pub / "paper_forward.json").write_text(json.dumps(v, indent=1, default=str) + "\n")
    (pub / "REPORT.md").write_text(report_md(v, shift))
    if push:
        subprocess.run(["git", "add", "-A"], cwd=pub, check=False)
        if subprocess.run(["git", "commit", "-qm", f"paper forward {datetime.now(timezone.utc):%Y-%m-%dT%H:%MZ}"],
                          cwd=pub, check=False).returncode == 0:
            for i in range(4):
                if subprocess.run(["git", "push", "-q", "origin", "HEAD:paper-forward-data"], cwd=pub).returncode == 0:
                    break
                time.sleep(2 ** (i + 1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--publish", required=True)
    ap.add_argument("--minutes", type=float, default=345)
    ap.add_argument("--every", type=float, default=15)
    ap.add_argument("--no-push", action="store_true")
    a = ap.parse_args()
    cfg = ServiceConfig.from_env()
    if cfg.mode != "PAPER_FORWARD":
        raise SystemExit("this script runs MODE=PAPER_FORWARD only")
    from aitrader.service.runtime import Runtime
    pub = Path(a.publish)
    pub.mkdir(parents=True, exist_ok=True)
    rt = Runtime(cfg)
    shift = {"started": f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC",
             "decision_mode": rt.orch.brain.config.decision_mode, "llm": rt.llm.config.public().get("model") or "none"}
    rep = rt.execution.reconcile()
    print(json.dumps({"reconcile": rep, "gate": rt.gate.status().get("risk_status")}, default=str), flush=True)
    stop = {"now": False}
    signal.signal(signal.SIGTERM, lambda *_: stop.update(now=True))
    rt.start()
    end = time.time() + a.minutes * 60
    next_pub = 0.0
    try:
        while time.time() < end and not stop["now"]:
            if time.time() >= next_pub:
                publish(rt, pub, shift, not a.no_push)
                next_pub = time.time() + a.every * 60
            time.sleep(5)
    finally:
        rt.stop()
        publish(rt, pub, shift, False)
        snap = Path(cfg.data_dir) / "snapshot.db"  # a consistent copy (the live file has a write-ahead log)
        snap.unlink(missing_ok=True)
        with sqlite3.connect(Path(cfg.data_dir) / "aitrader.db") as src, sqlite3.connect(snap) as dst:
            src.backup(dst)
        with snap.open("rb") as f, gzip.open(pub / "aitrader.db.gz", "wb") as out:  # restorable if the cache is lost
            shutil.copyfileobj(f, out)
        snap.unlink()
        publish(rt, pub, shift, not a.no_push)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
