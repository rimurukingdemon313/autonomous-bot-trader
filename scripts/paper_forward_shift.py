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
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aitrader.service.config import ServiceConfig  # noqa: E402


def money(x) -> str:
    return "n/a" if x is None else f"${x:,.2f}"


def fmt(x, spec: str) -> str:
    return "n/a" if x is None else spec.format(x)


def blame_lines(b: dict) -> list[str]:
    """Who lost it, the market or us (aitrader/learning/blame.py): every closed trade checked."""
    if not b:
        return []
    if b.get("available") is False:
        return [f"**Who lost it: not checked** ({b.get('reason')}): no loss is called the market's without the check.", ""]
    kinds = b.get("market_by_kind") or {}
    say = {"STOP": "at the stop, within the plan", "TIME_EXIT": "by the time exit", "STOP_BEYOND_PLAN":
           "stopped beyond the plan (a gap or the spread at the stop)"}
    out = ["## Who lost it: the market or us", "",
           f"Losses {b.get('losses', 0)}, {money(b.get('loss_usd'))}: **the market {b.get('market_losses', 0)}** ("
           + ", ".join(f"{say.get(k, k)} {x['n']}" for k, x in kinds.items()) + f") · **us {b.get('ours_losses', 0)}**"
           + (f" ({money(b.get('ours_loss_usd'))})" if b.get("ours_losses") else "") + ". Every closed trade is checked: "
           "the rules and the gate approved it, its data and the fill's quote were fresh, it was sized within the "
           "per-trade risk, both traders chose its side, it closed on time and not over a weekend, its costs were as "
           "planned. A check that cannot be read counts as ours.", ""]
    if b.get("ours"):
        out += [f"**WARNING: {b['ours']} trade(s) failed a check: a defect, not the market.**", ""]
        out += [f"- {datetime.fromtimestamp(t['closed'], timezone.utc):%m-%d %H:%M} {t.get('symbol')} {t.get('direction')} "
                f"{money(t.get('net_pnl'))}: " + "; ".join(t.get("faults") or []) for t in b.get("ours_trades") or []]
        out.append("")
    for t in b.get("beyond_plan") or []:
        out += [f"Beyond the plan, the market's: {datetime.fromtimestamp(t['closed'], timezone.utc):%m-%d %H:%M} "
                f"{t.get('symbol')} {t.get('direction')} lost {money(-t['net_pnl'])} against a planned "
                f"{money(t.get('planned_max_loss'))}{' in the rollover' if 'rollover' in (t.get('market') or '') else ''}.", ""]
    gone = b.get("removed_trades") or {}
    if gone.get("trades"):
        out += [f"The {gone['trades']} trade(s) taken out of the account, checked the same way: {gone.get('ours', 0)} ours"
                + (f" ({'; '.join(sorted({f for t in gone.get('ours_trades') or [] for f in t.get('faults') or []}))})"
                   if gone.get("ours") else "") + ".", ""]
    return out


def period_lines(p: dict | None) -> list[str]:
    """The account of the setup now trading (aitrader/broker/periods.py), first: its own trades, from its start."""
    if not p:
        return []
    if p.get("available") is False:
        return [f"**New account `{p.get('id')}`: not readable** ({p.get('reason')}).", ""]
    g, b = p.get("performance") or {}, p.get("before") or {}
    bp = b.get("performance") or {}
    return [f"## The new account: the setup trading now (from {p['starts'].replace('T', ' ').replace(':00Z', ' UTC')})", "",
            f"{p.get('setup')}. Opened at the owner's request ({p.get('requested')}): {p.get('reason')}.", "",
            "| Start | Equity | Total P&L | Closed | Open | Trades | Win rate | Expectancy | Profit factor |",
            "|---|---|---|---|---|---|---|---|---|",
            f"| {money(p.get('start_balance'))} | {money(p.get('equity'))} | {money(p.get('total_pnl'))} | "
            f"{money(p.get('closed_pnl'))} | {p.get('open', 0)} ({money(p.get('open_pnl'))}) | "
            f"{g.get('trades', 0)} ({g.get('sample', 'none')}) | {fmt(g.get('win_rate'), '{:.1%}')} | "
            f"{fmt(g.get('expectancy_r'), '{:+.3f}R')} | {fmt(g.get('profit_factor'), '{:.2f}')} |", "",
            f"Before it, kept and apart (not in the figures above): {bp.get('trades', 0)} trades, net "
            f"{money(b.get('closed_pnl'))}" + (f", {b['open']} still open ({money(b.get('open_pnl'))})" if b.get("open") else "")
            + ". The whole paper journal, which the hard gate and the risk engine still guard, is under Paper account "
            "below; nothing in it was moved or removed.", ""]


def report_md(v: dict, shift: dict) -> str:
    a, o = v.get("account") or {}, (v.get("performance") or {}).get("overall") or {}
    lines = [
        "# PAPER FORWARD TEST — NOT REAL MONEY", "",
        f"Updated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC · mode `{v['mode']}` · profile `{v['profile']}` · "
        f"shift started {shift['started']} · decision system `{shift['decision_mode']}`", "",
        f"Research status (historical, unchanged): **{v['research_status']}**. This run measures the system forward; "
        "it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.", ""]
    lines += period_lines(v.get("period"))
    dai = v.get("dual_ai") or {}
    if dai.get("active"):  # the rule that trades first; two rules are never averaged into one number
        g = dai.get("performance") or {}
        lines += ["## The rule that trades: a trade only when both AIs agree", "",
                  "| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |",
                  "|---|---|---|---|---|---|---|---|",
                  f"| {g.get('trades', 0)} ({g.get('sample', 'none')}) | {g.get('wins', 0)} | {g.get('losses', 0)} | "
                  f"{fmt(g.get('win_rate'), '{:.1%}')} | {money(g.get('net_pnl'))} | "
                  f"{fmt(g.get('expectancy_r'), '{:+.3f}R')} | {fmt(g.get('profit_factor'), '{:.2f}')} | "
                  f"{money(g.get('max_drawdown_usd'))} |", ""]
        for name, r in (dai.get("retired_rules") or {}).items():
            rp = r.get("performance") or {}
            if rp.get("trades") and r.get("removed_from_account"):
                back = sum(x["amount"] for x in r["removed_from_account"])
                lines += [f"The {rp['trades']} trade(s) of the old {name} rule, stopped in {r.get('stopped_in')}, were "
                          f"removed from the paper account at the operator's request: their net "
                          f"{money(rp.get('net_pnl'))} was put back by a declared adjustment ({money(back)}). They stay "
                          "in the journal (append-only), in none of the account's figures below.", ""]
            elif rp.get("trades"):
                lines += [f"The account below is the real paper account. It also holds the {rp['trades']} trade(s) of "
                          f"the old {name} rule, stopped in {r.get('stopped_in')} ({r.get('was')}): net "
                          f"{money(rp.get('net_pnl'))}, {rp.get('wins', 0)} won, expectancy "
                          f"{fmt(rp.get('expectancy_r'), '{:+.3f}R')}. They stay in the journal, listed as theirs, and "
                          "are never averaged with the agreement figures.", ""]
        unknown = (dai.get("performance_by_rule") or {}).get("UNKNOWN") or {}
        if unknown.get("trades"):
            lines += [f"Desk trades whose rule could not be read: {unknown['trades']}, net "
                      f"{money(unknown.get('net_pnl'))}: in the account, in neither rule's figures.", ""]
        lines += ["## Paper account", ""]
    lines += [
        "| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
        f"| {money(v.get('start_balance'))} | {money(a.get('equity'))} | {money(a.get('today_pnl'))} | "
        f"{money(a.get('total_pnl'))} | {money(a.get('drawdown_from_start'))} | {len(v.get('open_positions') or [])} | "
        f"{o.get('trades', 0)} ({o.get('sample', 'none')}) | {fmt(o.get('win_rate'), '{:.1%}')} | "
        f"{fmt(o.get('expectancy_r'), '{:+.3f}R')} | {fmt(o.get('profit_factor'), '{:.2f}')} | "
        f"{v.get('risk_status')} | {v.get('bot_status')} |", ""]
    if a.get("adjustments_total"):  # declared, never folded in silently
        lines += [f"Equity includes declared operator adjustments of {money(a['adjustments_total'])} "
                  f"(without them: {money(a.get('equity_before_adjustments'))}); P&L today excludes them. "
                  + "; ".join(f"`{x['id']}`: {x.get('reason')}" for x in v.get("adjustments") or []) + ".", ""]
    lines += blame_lines(v.get("blame") or {})
    # found live (2026-10-14): the gate refused every approved trade for twelve hours, one line among many below
    def gate_code(reason: str) -> str:
        m = re.search(r"reason=([A-Z_]+)", reason)
        return m.group(1) if m else "?"
    pipe = v.get("pipeline") or []
    refused = [e for e in pipe if "RISK_GATE_REJECTED" in (e.get("reason") or "")]
    gate = Counter(gate_code(e["reason"]) for e in refused)
    if gate:
        last = max(int(e["t"]) for e in refused)
        since = [e for e in pipe if int(e["t"]) > last]
        when = (f" The latest at {datetime.fromtimestamp(last, timezone.utc):%m-%d %H:%M} UTC; "
                + (f"{len(since)} decision(s) since, none refused by the gate." if since else "none after it yet."))
        lines += [f"**WARNING: the hard risk gate refused {sum(gate.values())} of the last {len(pipe)} decisions: "
                  + ", ".join(f"{k} x{n}" for k, n in gate.most_common())
                  + ".** A refusal by the gate after the risk engine approved is never routine." + when, ""]
    lines += ["## Last decisions (decision → risk → paper execution)", ""]
    for e in v.get("pipeline") or []:
        when = datetime.fromtimestamp(e["t"], timezone.utc).strftime("%m-%d %H:%M")
        lines.append(f"- {when} {e['symbol']} {e['decision']}: {' → '.join(e['stages'])}"
                     + (f" — {e['reason'][:200]}" if e.get("reason") else ""))
    lines += ["", f"## Latest decisions, NO TRADE included ({v.get('decisions_total', 0)} so far)", ""]
    for d in (v.get("last_decisions") or [])[:12]:
        when = datetime.fromtimestamp(d["t"], timezone.utc).strftime("%m-%d %H:%M") if d.get("t") else "?"
        flags = f" [data: {'; '.join(d['data_flags'])}]" if d.get("data_flags") else ""
        lines.append(f"- {when} {d['symbol']} {d['decision']}: {d.get('reason') or ''}{flags}")
    lines += ["", "## Open paper positions", "", "| Symbol | Side | Qty | Entry | Stop | Target | P&L |", "|---|---|---|---|---|---|---|"]
    for p in v.get("open_positions") or []:
        lines.append(f"| {p['symbol']} | {p['side']} | {p['qty']} | {p['entry']} | {p['stop']} | {p['target']} | {money(p.get('pnl'))} |")
    lines += ["", "## Closed paper trades (latest 20)", "",
              "| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule | Lost to |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for t in v.get("recent_trades") or []:
        when = datetime.fromtimestamp(t["closed"], timezone.utc).strftime("%m-%d %H:%M")
        lines.append(f"| {when} | {t['symbol']} | {t['direction']} | {money(t.get('net_pnl'))} | "
                     f"{fmt(t.get('r'), '{:+.2f}')} | {money(t.get('costs_total'))} | "
                     f"{t.get('exit_reason')} | {t.get('source') or t.get('agent')} | {t.get('rule') or '-'} | "
                     f"{'**us**' if t.get('blame') == 'OURS' else '-' if (t.get('net_pnl') or 0) >= 0 else 'the market' if t.get('blame') == 'MARKET' else '?'} |")
    if dai.get("active"):
        o, perf = dai.get("openrouter") or {}, dai.get("performance") or {}

        def paid_trial_line(t):
            if not t.get("models"):
                return "Paid trial: none (FREE models only)"
            why = {r: w for r, w in (t.get("not_asked_because") or {}).items() if w}
            return (f"Paid trial `{t.get('name')}` ({t.get('starts')} to {t.get('ends')}): "
                    f"{'ACTIVE' if t.get('active') else 'not active'}"
                    + (f" ({t['stopped']})" if t.get("stopped") else "")
                    + " · " + " · ".join(f"{'trader 1' if r == 'vision' else 'trader 2'} `{m}` asked first"
                                         for r, m in (t.get("models") or {}).items())
                    + f" · spent {money(t.get('spent_total'))} of {money(t.get('total_usd'))}, today "
                    f"{money(t.get('spent_today'))} of {money(t.get('daily_usd'))} (the key's own reading)"
                    + "".join(f" · {'trader 1' if r == 'vision' else 'trader 2'} not asked: {w}" for r, w in why.items()))
        rec = dai.get("record") or {}
        pick, lose = rec.get("debate_pick_if_taken") or {}, rec.get("debate_losing_side_if_taken") or {}

        def exit_line(s):
            if not s.get("n"):
                return "none resolved yet"
            return (f"{fmt(s.get('expectancy_r'), '{:+.3f}R')} vs {fmt(s.get('as_taken_expectancy_r'), '{:+.3f}R')} "
                    f"as taken ({s['n']}, {s.get('sample')})")

        def shadow(s):
            return (f"{s.get('n', 0)} resolved ({s.get('sample', 'none')})"
                    + (f", expectancy {fmt(s.get('expectancy_r'), '{:+.3f}R')}" if s.get("n") else ""))
        lines += ["", "## Dual AI desk (two OpenRouter traders: free, or the paid trial while it runs; a trade only when they agree)", "",
                  f"OpenRouter `{o.get('status')}` · key {'set' if o.get('configured') else 'NOT SET'} · trader 1 "
                  f"`{o.get('vision_model')}` · trader 2 `{o.get('judge_model')}` · debate `{o.get('verifier_model')}` · "
                  f"calls today {o.get('calls_today')}/{o.get('daily_budget')}", "",
                  paid_trial_line(o.get("paid_trial") or {}), "",
                  f"Agreement trades {perf.get('trades', 0)} ({perf.get('sample', 'none')}) · wins {perf.get('wins', 0)} · "
                  f"losses {perf.get('losses', 0)} · net {money(perf.get('net_pnl'))} · expectancy "
                  f"{fmt(perf.get('expectancy_r'), '{:+.3f}R')} · profit factor {fmt(perf.get('profit_factor'), '{:.2f}')}"
                  + "".join(f" · old {k} rule (stopped in {r.get('stopped_in')}): {(r.get('performance') or {}).get('trades', 0)} "
                            f"trade(s), net {money((r.get('performance') or {}).get('net_pnl'))}, "
                            + ("removed from the account" if r.get("removed_from_account") else "apart")
                            for k, r in (dai.get("retired_rules") or {}).items()
                            if (r.get("performance") or {}).get("trades")), "",
                  f"Disagreements (not traded; the debate runs in shadow): "
                  f"{(rec.get('decisions_by_rule') or {}).get('DISAGREE', 0)} · the debate's pick if taken: "
                  f"{shadow(pick)} · the side it rejected if taken: {shadow(lose)}", "",
                  "Exits in shadow (the same trades, followed again; measured, never traded): " + " · ".join(
                      f"{label} {exit_line((rec.get('exits_in_shadow') or {}).get(k) or {})}"
                      for k, label in (("BE1R", "break-even at +1R"), ("HOLD24H", "held 24 h"),
                                       ("WIDE2X", "stop and target twice as far"),
                                       ("HOLD8H", "closed at 8 h (the exit before dual-ai 1.7.0)"))), "",
                  "Trader 2's own levels in shadow (a trade is on Trader 1's since dual-ai 1.10.0; measured, never "
                  f"traded): {exit_line(rec.get('trader2_levels_in_shadow') or {})}", "",
                  "Trades taken by session (UTC): " + " · ".join(
                      f"{s} {shadow(st)}" for s, st in (rec.get("taken_by_session") or {}).items()), "",
                  "| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |",
                  "|---|---|---|---|---|---|---|---|"]
        for a in dai.get("analyses") or []:
            when = datetime.fromtimestamp(a["t"], timezone.utc).strftime("%m-%d %H:%M") if a.get("t") else "?"
            t1, t2, vf = a.get("trader1") or {}, a.get("trader2") or {}, a.get("verifier") or {}
            risk = a.get("risk")
            read = " (numbers)" if t1 and a.get("trader1_input") == "numbers" else ""
            lines.append(f"| {when} | {a['symbol']} | {t1.get('direction', '-')} {t1.get('confidence', '')}{read} | "
                         f"{t2.get('direction', '-')} {t2.get('confidence', '')} | {vf.get('direction', '-')} | "
                         f"{(a.get('consensus') or {}).get('rule')} | "
                         f"{a['decision']} | {'-' if risk is None else ('APPROVED' if risk['approved'] else 'REJECTED')} |")
        lines += ["", "The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so "
                  "Trader 1 read the same chart from its numbers."]
    lines += ["", "Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.", ""]
    return "\n".join(lines)


def publish(rt, pub: Path, shift: dict, push: bool) -> None:
    v = rt.paper_forward()
    v["shift"] = shift
    if rt.orch.brain.config.decision_mode == "dual_ai":
        v["dual_ai"] = rt.dual_ai()
        last = (v["dual_ai"].get("last_analysis") or {}).get("symbol")
        png = rt.dual_ai_chart(last) if last else None
        if png:
            (pub / "last_chart.png").write_bytes(png)
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
    from aitrader.llm.paid_trial import PAID_TRIAL
    from aitrader.service.runtime import Runtime
    pub = Path(a.publish)
    pub.mkdir(parents=True, exist_ok=True)
    rt = Runtime(cfg)
    shift = {"started": f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC",
             "decision_mode": rt.orch.brain.config.decision_mode,
             "llm": (("openrouter (free models"
                      + (f"; paid trial {PAID_TRIAL.name} first while its caps allow)" if PAID_TRIAL.models else ")"))
                     if rt.orch.brain.config.decision_mode == "dual_ai"
                     else rt.llm.config.public().get("model") or "none")}
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
