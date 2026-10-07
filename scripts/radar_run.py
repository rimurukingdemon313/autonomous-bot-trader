"""One run of the live funding radar (research/preregistrations/RADAR-1.md). Run hourly by .github/workflows/radar.yml.

    python scripts/radar_run.py --state STATE_DIR --publish PUB_DIR [--rf 0.04]

STATE_DIR holds the full state (history + ledger) as state.json.gz, kept in the Actions cache. PUB_DIR receives the
small public files committed to the `radar-data` branch: ledger.json (positions and marks), opportunities.json (this
hour's candidates) and REPORT.md. If the cache was evicted, the ledger is restored from PUB_DIR/ledger.json and the
history restarts (decisions then wait for 72 hours of new observations: nothing is assumed).
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.radar import core as R  # noqa: E402
from aitrader.radar import venues as V  # noqa: E402


def load_state(state_dir: Path, pub: Path) -> tuple[R.State, str]:
    f = state_dir / "state.json.gz"
    if f.exists():
        return R.State.from_json(json.loads(gzip.decompress(f.read_bytes()))), "cache"
    led = pub / "ledger.json"
    if led.exists():
        d = json.loads(led.read_text())
        return R.State.from_json({"open": d.get("open", []), "closed": d.get("closed", []),
                                  "marks": d.get("marks", []), "runs": d.get("runs", 0)}), "ledger (history restarted)"
    return R.State(), "new"


def keep_for_history(quotes: list[V.Quote]) -> list[V.Quote]:
    """Only coins quoted on at least two venues can ever be traded: the rest are not stored."""
    by: dict[str, set] = {}
    for q in quotes:
        by.setdefault(q.coin, set()).add(q.venue)
    return [q for q in quotes if len(by[q.coin]) >= 2]


def fmt_pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x * 100:.1f}%"


def report(state: R.State, opps: list[dict], perf: dict, now: int, origin: str, n_quotes: int,
           look: dict | None = None) -> str:
    ts = datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Funding radar: live paper ledger",
        "",
        f"Updated **{ts}**, run {state.runs}, version `{R.RADAR_VERSION}`. State from: {origin}. "
        f"Quotes this hour: {n_quotes}.",
        "",
        "**PAPER ONLY.** No order is ever sent. Every number is computed from public live quotes. Positions are "
        "short the perpetual on the venue paying more funding and long it on the other, on the same coin. Costs "
        "are each venue's taker fee plus 5 bp per fill.",
        "",
        "| Venue | Status |",
        "|---|---|",
    ]
    for v in V.FETCHERS:
        lines.append(f"| {v} | {'ERROR: ' + state.venue_errors[v] if v in state.venue_errors else 'ok'} |")
    if look is None:
        t_look = state.marks[0]["t"] + int(R.FORWARD["look_days"] * 86400) if state.marks else now
        verdict = f"**WAIT**: the single look is on {datetime.fromtimestamp(t_look, timezone.utc):%Y-%m-%d %H:%M} UTC"
    else:
        verdict = (f"**{look['status']}** at the look of {datetime.fromtimestamp(look['t'], timezone.utc):%Y-%m-%d %H:%M}"
                   f" UTC, gates {look['gates']} (frozen in RADAR-1-look*.json)")
    lines += ["", "## Forward test RADAR-1", "", verdict, "",
              "## Performance (paper; capital = 2N per slot x 10 slots; excess = net P&L minus cash on 2N while open)",
              ""]
    for k, v in perf.items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Open positions", "", "| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | "
              "Cost bp | Net bp |", "|---|---|---|---|---|---|---|---|---|"]
    for p in state.open:
        lines.append(f"| {p.coin} | {p.short_venue} | {p.long_venue} | "
                     f"{datetime.fromtimestamp(p.opened, timezone.utc):%Y-%m-%d %H:%M} | {fmt_pct(p.entry_spread_apr)} | "
                     f"{p.funding_bp:.1f} | {p.basis_bp:.1f} | {p.cost_bp:.1f} | **{p.net_bp:.1f}** |")
    lines += ["", f"## Closed positions ({len(state.closed)})", "", "| Coin | Short | Long | Days | Reason | Net bp |",
              "|---|---|---|---|---|---|"]
    for p in state.closed[-30:][::-1]:
        lines.append(f"| {p.coin} | {p.short_venue} | {p.long_venue} | {(p.closed - p.opened) / 86400:.1f} | {p.reason} | "
                     f"{p.net_bp:.1f} |")
    lines += ["", "## Top opportunities this hour (passing the entry rule)", "",
              "| Coin | Short | Long | 72 h spread APR | Now APR |", "|---|---|---|---|---|"]
    for o in opps[:15]:
        lines.append(f"| {o['coin']} | {o['short']} | {o['long']} | {fmt_pct(o['trail_apr'])} | {fmt_pct(o['now_apr'])} |")
    lines += ["", "Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.", ""]
    return "\n".join(lines)


def freeze_looks(pub: Path, perf: dict, now: int) -> dict | None:
    """Write the forward test's look exactly once, at the first run past the look date: the verdict is read from
    this frozen file, never from a later, luckier day. The second look exists only if the first had too few
    closed positions."""
    f1, f2 = pub / "RADAR-1-look1.json", pub / "RADAR-1-look2.json"
    if not f1.exists():
        status, gates = R.forward_verdict(perf)
        if status == "WAIT":
            return None
        f1.write_text(json.dumps({"t": now, "status": status, "gates": gates, "perf": perf}, indent=1) + "\n")
        return json.loads(f1.read_text())
    first = json.loads(f1.read_text())
    if first["status"] != "INCONCLUSIVE" or f2.exists():
        return json.loads(f2.read_text()) if f2.exists() else first
    status, gates = R.forward_verdict(perf, extended=True)
    if status == "WAIT":
        return first
    f2.write_text(json.dumps({"t": now, "status": status, "gates": gates, "perf": perf}, indent=1) + "\n")
    return json.loads(f2.read_text())


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--state", required=True)
    p.add_argument("--publish", required=True)
    p.add_argument("--rf", type=float, default=0.04)
    p.add_argument("--now", type=int, default=None)
    a = p.parse_args()
    state_dir, pub = Path(a.state), Path(a.publish)
    state_dir.mkdir(parents=True, exist_ok=True)
    pub.mkdir(parents=True, exist_ok=True)
    now = a.now if a.now is not None else int(time.time()) // 3600 * 3600
    state, origin = load_state(state_dir, pub)
    if state.marks and state.marks[-1]["t"] >= now:  # a delayed cron run landing in an hour already recorded
        print(json.dumps({"now": now, "skipped": "this hour is already recorded"}))
        return 0
    quotes, errors = V.snapshot()
    stored = keep_for_history(quotes)
    rules = R.Rules()
    R.step(state, stored, errors, now, rules)
    opps = R.opportunities(stored, state.history, now, rules)
    perf = R.performance(state, rules, a.rf)
    (state_dir / "state.json.gz").write_bytes(gzip.compress(json.dumps(state.to_json()).encode()))
    led = state.to_json()
    led.pop("history")
    (pub / "ledger.json").write_text(json.dumps(led, indent=1) + "\n")
    (pub / "opportunities.json").write_text(json.dumps(
        [{k: v for k, v in o.items() if not k.endswith("_q")} for o in opps], indent=1) + "\n")
    look = freeze_looks(pub, perf, now)
    (pub / "REPORT.md").write_text(report(state, opps, perf, now, origin, len(quotes), look))
    print(json.dumps({"now": now, "quotes": len(quotes), "stored": len(stored), "errors": errors,
                      "open": len(state.open), "closed": len(state.closed), "opportunities": len(opps), "perf": perf}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
