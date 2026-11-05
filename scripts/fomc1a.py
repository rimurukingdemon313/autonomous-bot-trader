"""FOMC-1A: FOMC-1's rule, fetched in parallel shards (research/preregistrations/FOMC-1A.md).

FOMC-1A amends FOMC-1 before any outcome was computed. FOMC-1's fetch ran on one runner. Dukascopy's datafeed served
it about one day of minutes every 150 seconds: 14 of 510 days in 35 minutes. At that rate the fetch needs about 21
hours, against a job limit of hours. FOMC-1's own fetch also refused the whole run on any one day that could not be
fetched, and earlier ingests here lost a few days in a hundred that way. So the run was cancelled, nothing was judged,
and FOMC-1 is recorded as ABANDONED.

The rule, the events, the costs, the control, the periods, the gates and the holdout are FOMC-1's, unchanged: this
script imports them from scripts/fomc1.py, which is not edited. Two things change:
- the fetch is split into shards that run on separate runners at once (`fetch <shard> <shards>`), and `merge` joins
  them; a day that still fails after a second, slower pass is recorded as failed, never filled;
- a window that touches a failed day is no trade, like any missing quote. Fetch failures have nothing to do with
  what the market did, so this loses power, not honesty. If more than one in ten of a period's event windows is lost
  to failed days, that period is not judged at all.

    python scripts/fomc1a.py spec              # freeze the design (reads no price)
    python scripts/fomc1a.py preregister       # register FOMC-1A in research/registry.jsonl
    python scripts/fomc1a.py fetch <i> <n>     # shard i of n: Dukascopy minute quotes (on GitHub's runners)
    python scripts/fomc1a.py merge <n>         # join the n shards; refuses unless every day is accounted for
    python scripts/fomc1a.py judge             # 2016..2021: development, validation, the gates
    python scripts/fomc1a.py holdout           # only if FOMC-1A PASSED: 2022-01..2026-09, once

Each command after `spec` refuses to run if the code or the spec changed since registration. Nothing here changes the
bot.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.research.registry import Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402
import scripts.fomc1 as F  # noqa: E402  - the rule, unchanged

R = F.R
PID, HID = "FOMC-1A", "FOMC-1A-H"
DOC = "research/preregistrations/FOMC-1A.md"
SPEC = R / "specs" / "FOMC-1A.json"
CODE = ("scripts/fomc1a.py", *F.CODE)
#: the most event windows a period may lose to days that could not be fetched before it is not judged
MAX_LOST_SHARE = 0.10
FIRST_PASS_PACE, SECOND_PASS_PACE = 0.5, 3.0


def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def threshold(reg: Registry) -> float:
    return max(3.0, bonferroni_t(reg.tests_on(F.UNIVERSE, F.JUDGE[0], F.HOLD[1]) + F.TESTS))


def spec(reg: Registry) -> dict:
    s = F.spec(reg)
    return {**s, "program": PID, "amends": "FOMC-1 (ABANDONED before any outcome: its fetch could not finish)",
            "threshold_t": round(threshold(reg), 4),
            "data": s["data"] + "; fetched in parallel shards, a day that fails twice recorded as failed and never "
                                "filled; a window touching a failed day is no trade",
            "max_lost_share": MAX_LOST_SHARE}


# ── the shards ───────────────────────────────────────────────────────────

def all_days() -> list[date]:
    return sorted({w[k] for w in F.windows() for k in ("entry_day", "exit_day")})


def shard_days(i: int, n: int) -> list[date]:
    if not 0 <= i < n:
        raise SystemExit(f"shard {i} of {n} does not exist")
    return all_days()[i::n]


def take(m, d: date) -> list:
    """The two minutes a window can need from one day's quotes, raw (unscaled)."""
    out = []
    for hm in (F.ENTRY_NY, F.EXIT_NY):
        hit = m[m[:, 0] == F.minute_end(d, hm)] if len(m) else m
        if len(hit):
            out.append([str(d), f"{hm[0]:02d}:{hm[1]:02d}", float(hit[0, 4]), float(hit[0, 8])])
    return out


def cmd_fetch(i: int, n: int, day_minutes=None) -> dict:
    if day_minutes is None:
        from scripts.ingest_dukascopy_candles import day_minutes
    F._calendar_ok()
    status: dict[str, str] = {}
    rows: list = []
    pending = shard_days(i, n)
    for pace in (FIRST_PASS_PACE, SECOND_PASS_PACE):  # a second, slower pass over the days that failed
        failed = []
        for d in pending:
            m, st = day_minutes(F.SYMBOL, d, pace=pace)
            if m is None:
                failed.append(d)
                continue
            status[str(d)] = st
            rows += take(m, d)
            print(d, st, flush=True)
        pending = failed
    for d in pending:
        status[str(d)] = "failed"
        print(d, "failed", flush=True)
    part = {"shard": i, "shards": n, "days": status, "rows": rows}
    F.DATA.mkdir(parents=True, exist_ok=True)
    (F.DATA / f"part-{i}.json").write_text(F._dump(part))
    return part


def cmd_merge(n: int) -> dict:
    """Join the shards into FOMC-1's quotes file and manifest. Every day must be accounted for, by exactly one shard."""
    from scripts.ingest_dukascopy_candles import scale_for
    status: dict[str, str] = {}
    rows: list = []
    for i in range(n):
        path = F.DATA / f"part-{i}.json"
        if not path.exists():
            raise SystemExit(f"shard {i} of {n} is missing: nothing is judged")
        part = json.loads(path.read_text())
        if (part["shard"], part["shards"]) != (i, n) or set(part["days"]) != {str(d) for d in shard_days(i, n)}:
            raise SystemExit(f"shard {i} does not cover its own days: nothing is judged")
        status.update(part["days"])
        rows += part["rows"]
    if set(status) != {str(d) for d in all_days()}:
        raise SystemExit("the shards do not cover every day: nothing is judged")
    scale = scale_for(sorted(r[2] for r in rows)[len(rows) // 2], F.BAND)
    rows.sort()
    body = "date,time_ny,bid,ask\n" + "".join(f"{d},{t},{b * scale!r},{a * scale!r}\n" for d, t, b, a in rows)
    (F.DATA / "quotes.csv").write_text(body)
    man = {"retrieved": datetime.now(timezone.utc).isoformat(), "symbol": F.SYMBOL, "scale": scale,
           "days": len(status), "rows": len(rows), "file": "quotes.csv",
           "sha256": hashlib.sha256(body.encode()).hexdigest(), "shards": n,
           "failed_days": sorted(d for d, s in status.items() if s == "failed"),
           "empty_days": sorted(d for d, s in status.items() if s == "empty")}
    (F.DATA / "manifest.json").write_text(F._dump(man))
    print("days", len(status), "quotes", len(rows), "scale", scale, "failed", len(man["failed_days"]),
          "empty", len(man["empty_days"]))
    return man


def lost_events(start: date, end: date, failed: set[str]) -> dict:
    """The period's event windows that touch a day that could not be fetched, against the events listed."""
    ev = [w for w in F.windows() if w["kind"] == "event" and start <= w["event"] < end]
    lost = [str(w["event"]) for w in ev if {str(w["entry_day"]), str(w["exit_day"])} & failed]
    return {"listed": len(ev), "lost": lost, "share": len(lost) / len(ev) if ev else 1.0}


def _complete_enough(start: date, end: date) -> dict:
    man = json.loads((F.DATA / "manifest.json").read_text())
    lost = lost_events(start, end, set(man["failed_days"]))
    if lost["share"] > MAX_LOST_SHARE:
        raise SystemExit(f"{len(lost['lost'])} of {lost['listed']} event windows touch days that could not be "
                         "fetched: too few to judge, nothing is judged")
    return lost


# ── the commands ─────────────────────────────────────────────────────────

def _check_frozen(reg: Registry) -> dict:
    trial = reg.get(PID)
    frozen = json.loads(SPEC.read_text())
    if trial.design.get("spec_sha256") != frozen["sha256"] or frozen["code_sha256"] != code_hash():
        raise SystemExit("the spec or the code differs from what was preregistered")
    return frozen


def cmd_spec() -> None:
    reg = F._registry()
    if any(t.id == PID for t in reg.trials):
        raise SystemExit(f"{PID} is registered; its spec is frozen")
    first = reg.verdict_of("FOMC-1")
    if first is None or first.status != "ABANDONED":
        raise SystemExit("FOMC-1 must be recorded as ABANDONED first")
    F._calendar_ok()
    s = spec(reg)
    SPEC.write_text(F._dump({"spec": s, "sha256": F.spec_sha(s), "code_sha256": code_hash()}))
    print(F.spec_sha(s), "threshold", s["threshold_t"])


def cmd_preregister(now: datetime) -> None:
    reg = F._registry()
    frozen = json.loads(SPEC.read_text())
    s = spec(reg)
    if F.spec_sha(s) != frozen["sha256"] or code_hash() != frozen["code_sha256"]:
        raise SystemExit("the spec or the code changed since `spec`")
    if frozen["sha256"] not in (ROOT / DOC).read_text():
        raise SystemExit(f"{DOC} must quote the spec sha256 {frozen['sha256']}")
    reg.register(Trial(id=PID, registered=now, title="FOMC-1A: the pre-FOMC drift, US 500 CFD (FOMC-1, fetched "
                                                     "in shards)", hypothesis=s["question"],
                       uses=(Use(F.UNIVERSE, F.JUDGE[0], F.JUDGE[1], "judge"),), tests=F.TESTS,
                       configurations=F.TESTS, preregistration=DOC,
                       design={"spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"],
                               "threshold_t": s["threshold_t"]}))
    print("registered", PID, "threshold", s["threshold_t"])


def cmd_judge(now: datetime) -> None:
    reg = F._registry()
    frozen = _check_frozen(reg)
    if reg.verdict_of(PID) is not None:
        raise SystemExit(f"{PID} already has a verdict")
    F._calendar_ok()
    lost = _complete_enough(*F.JUDGE)
    res = F.gates(F.load(F.JUDGE[1]), F._rates(), frozen["spec"]["threshold_t"])
    body = F._write(PID, {"program": PID, "verdict": "PASSED" if res["passed"] else "FAILED", **res,
                          "lost_to_failed_days": lost, "periods": frozen["spec"]["periods"],
                          "spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"],
                          "data": json.loads((F.DATA / "manifest.json").read_text())})
    reg.record_verdict(Verdict(PID, now, body["verdict"], {"artifact": f"research/knowledge/{PID}.json",
                                                           "artifact_sha256": body["sha256"]}))
    print(body["verdict"], "failed:", res["failed_gates"], "per event", json.dumps(res["net_per_event"]),
          "gross", res["gross_mean"], "cost", res["cost_mean"], "timing", json.dumps(res["timing"]))


def cmd_holdout(now: datetime) -> None:
    reg = F._registry()
    frozen = _check_frozen(reg)
    judged = json.loads((F.OUT / f"{PID}.json").read_text())
    if judged["verdict"] != "PASSED":
        raise SystemExit("FOMC-1A did not pass: the holdout stays unread")
    if any(t.id == HID for t in reg.trials):
        raise SystemExit("the holdout was opened once already")
    reg.register(Trial(id=HID, registered=now, title="FOMC-1A holdout: 2022-01..2026-09", hypothesis=F.HOLDOUT_RULE,
                       uses=(Use(F.UNIVERSE, F.HOLD[0], F.HOLD[1], "judge"),), tests=1, configurations=1,
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"]}))
    lost = _complete_enough(*F.HOLD)
    quotes, rates = F.load(F.HOLD[1]), F._rates()
    b = F.book(quotes, *F.HOLD, rates)
    x = [w["net"] for w in b["event"]]
    s = F.per_event(x)
    s2 = F.per_event([w["net"] for w in F.book(quotes, *F.HOLD, rates, cost_x=2.0)["event"]])
    tm = F.welch(x, [w["net"] for w in b["control"]])
    ok = bool(s["mean"] and s["mean"] > 0 and s["t"] is not None and s["t"] >= NormalDist().inv_cdf(0.95)
              and (s2["mean"] or 0) > 0 and (tm["mean"] or 0) > 0)
    verdict = "PASSED" if ok else "FAILED"
    body = F._write(HID, {"program": HID, "holdout_of": PID, "period": [str(d) for d in F.HOLD],
                          "net_per_event": s, "costs_x2": s2, "timing": tm, "lost_to_failed_days": lost,
                          "rule": F.HOLDOUT_RULE, "classification": "VALIDATED" if ok else "REJECTED",
                          "verdict": verdict})
    reg.record_verdict(Verdict(HID, now, verdict, {"artifact": f"research/knowledge/{HID}.json",
                                                   "artifact_sha256": body["sha256"]}))
    print(verdict, json.dumps(s), "x2", s2["mean"], "timing", tm["mean"])


def main() -> int:
    args = sys.argv[1:]
    cmd = args[0] if args else ""
    now = datetime.now(timezone.utc)  # the command line's clock: every function above takes its dates as arguments
    if cmd == "fetch" and len(args) == 3:
        cmd_fetch(int(args[1]), int(args[2]))
    elif cmd == "merge" and len(args) == 2:
        cmd_merge(int(args[1]))
    else:
        {"spec": cmd_spec, "preregister": lambda: cmd_preregister(now), "judge": lambda: cmd_judge(now),
         "holdout": lambda: cmd_holdout(now)}.get(cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
