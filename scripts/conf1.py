"""CONF-1: on H1, would the agreements under the confidence floor have paid? (research/preregistrations/CONF-1.md)

The desk trades an agreement only when both traders state 65 or more (dual-ai 1.12.0, the owner's floor). On the H1
chart its seat holders state their confidence out of habit: in the first two H1 days Trader 1's model said 55-57
nearly every time (65 or more in 1 of its last 100 answers), Trader 2's said 65. So the floor refused 141 agreements
and let 5 through. Every agreement it refuses is followed forward as the trade it would have been
(DUAL_AI_LOW_CONFIDENCE). This asks that record, once, at dates fixed before any of them had an outcome: did those
agreements pay after costs?

One rule, two looks:
- LEARNING (decided 2026-11-02 to 2026-11-16 UTC, judged on 2026-11-20): does the mean net R reach +0.10 with t of
  2.0 or more over 100 or more agreements, and t of 2.0 or more over the days' own means (agreements of one day move
  together: a USD day is several pairs at once)? If not, FAILED and EVALUATION is not judged.
- EVALUATION (decided 2026-11-16 to 2026-11-23, judged on 2026-11-27), only if LEARNING qualified: mean net R > 0
  with t of 2.0 or more over 50 or more, and the days' mean above 0. CONFIRMED, or NOT CONFIRMED.
Too few agreements in a look: INCONCLUSIVE, nothing changes.

An outcome counts only if the ledger recorded it by the look's date (its row's `ts`), so a later database gives the
same answer. Nothing here changes the bot.

    python scripts/conf1.py freeze                       # writes research/specs/CONF-1.json (spec + both sha256)
    python scripts/conf1.py status <aitrader.db> [now]   # BLIND: how many agreements per look, no outcome read
    python scripts/conf1.py run <aitrader.db> [now]      # refuses before a look's date; judges what is due
"""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = ROOT / "research" / "specs" / "CONF-1.json"
DOC = ROOT / "research" / "preregistrations" / "CONF-1.md"
OUT = ROOT / "research" / "knowledge" / "CONF-1.json"

SPEC = {
    "program": "CONF-1",
    "question": "on the H1 chart, would the desk's agreements under the confidence floor have paid, after costs?",
    "units": "every DUAL_AI_LOW_CONFIDENCE proposal on the H1 chart decided inside the look's window, in the look's "
             "partition, whose outcome the ledger recorded as RESOLVED by the look's date (forward_outcomes.ts), each "
             "decision once",
    "looks": {
        "LEARNING": {"from": "2026-11-02T00:00:00Z", "to": "2026-11-16T00:00:00Z", "judge_at": "2026-11-20T00:00:00Z",
                     "min_n": 100, "min_mean_r": 0.10, "min_t": 2.0, "min_days_t": 2.0},
        "EVALUATION": {"from": "2026-11-16T00:00:00Z", "to": "2026-11-23T00:00:00Z",
                       "judge_at": "2026-11-27T00:00:00Z", "min_n": 50, "min_mean_r": 0.0, "min_t": 2.0,
                       "min_days_mean_r": 0.0},
    },
    "measure": "net R as followed forward (forward.walk: the trader's levels, the H1 time exit, spread, slippage and "
               "commission); t of the mean over agreements; and the same over the UTC days' own mean net R",
    "verdicts": {
        "LEARNING": "QUALIFIED if n >= min_n, mean >= min_mean_r, t >= min_t and the days' t >= min_days_t; "
                    "INCONCLUSIVE if n < min_n; FAILED otherwise (EVALUATION is then not judged)",
        "EVALUATION": "only after QUALIFIED: CONFIRMED if n >= min_n, mean > min_mean_r, t >= min_t and the days' mean "
                      "> min_days_mean_r; INCONCLUSIVE if n < min_n; NOT CONFIRMED otherwise",
    },
    "after": {
        "CONFIRMED": "the floor stops refusing H1 agreements, in a new dual-ai version, the owner told first; the "
                     "lesson check, the senior, the risk engine and the always-sure seat rule stay as they are",
        "otherwise": "the floor stays; the result is reported as it is",
    },
    "reported_never_judged": "the agreements the floor let through (DUAL_AI) in the same windows, the win rate, the "
                             "profit factor, the number decided but not resolved by the date",
}
H1_FAMILY, FLOOR_FAMILY = "DUAL_AI_LOW_CONFIDENCE", "DUAL_AI"


def spec_sha(spec: dict) -> str:
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


def code_sha() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def ts(iso: str) -> int:
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc).timestamp())


# ── the record ───────────────────────────────────────────────────────────

def units(db_path: str, look: str, spec: dict = SPEC, family: str = H1_FAMILY, read_outcomes: bool = True) -> dict:
    """The look's agreements: decided in its window, in its partition, on H1. With `read_outcomes`, each one's net R if
    the ledger recorded it RESOLVED by the look's date; without, none is read (the blind status)."""
    w = spec["looks"][look]
    t0, t1, due = ts(w["from"]), ts(w["to"]), ts(w["judge_at"])
    db = sqlite3.connect(db_path)
    decided = {}
    for did, t, part, payload in db.execute("SELECT decision_id, t, partition, payload FROM forward_proposals"):
        p = json.loads(payload)
        if (p.get("family") == family and p.get("timeframe") == "H1" and part == look and t0 <= int(t) < t1
                and did not in decided):
            decided[did] = int(t)
    out = {"decided": len(decided), "rows": []}
    if not read_outcomes:
        return out
    seen = set()
    for did, rec_ts, payload in db.execute("SELECT decision_id, ts, payload FROM forward_outcomes ORDER BY seq"):
        if did not in decided or did in seen or float(rec_ts) > due:
            continue
        o = json.loads(payload)
        if o.get("status") != "RESOLVED" or not isinstance(o.get("net_r"), (int, float)):
            continue
        seen.add(did)
        out["rows"].append({"id": did, "t": decided[did], "net_r": float(o["net_r"])})
    out["not_resolved_by_the_date"] = len(decided) - len(out["rows"])
    return out


# ── the judgement ────────────────────────────────────────────────────────

def _t(xs: list[float]) -> tuple[float | None, float | None]:
    n = len(xs)
    if n < 2:
        return (xs[0] if xs else None), None
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    return m, (m / (sd / math.sqrt(n)) if sd > 0 else None)


def summary(rows: list[dict]) -> dict:
    xs = [r["net_r"] for r in rows]
    days: dict = {}
    for r in rows:
        days.setdefault(datetime.fromtimestamp(r["t"], timezone.utc).strftime("%Y-%m-%d"), []).append(r["net_r"])
    dm, dt = _t([sum(v) / len(v) for v in days.values()])
    m, t = _t(xs)
    wins, losses = sum(x for x in xs if x > 0), -sum(x for x in xs if x < 0)
    rnd = (lambda v, k=4: None if v is None else round(v, k))
    return {"n": len(xs), "mean_r": rnd(m), "t": rnd(t, 2), "days": len(days), "days_mean_r": rnd(dm),
            "days_t": rnd(dt, 2), "win_rate": round(sum(1 for x in xs if x > 0) / len(xs), 3) if xs else None,
            "profit_factor": round(wins / losses, 3) if losses > 0 else None, "total_r": round(sum(xs), 3)}


def verdict(look: str, s: dict, spec: dict = SPEC) -> str:
    w = spec["looks"][look]
    if s["n"] < w["min_n"]:
        return "INCONCLUSIVE"
    m, t = s["mean_r"], s["t"]
    if look == "LEARNING":
        ok = (m is not None and t is not None and s["days_t"] is not None and m >= w["min_mean_r"]
              and t >= w["min_t"] and s["days_t"] >= w["min_days_t"])
        return "QUALIFIED" if ok else "FAILED"
    ok = (m is not None and t is not None and s["days_mean_r"] is not None and m > w["min_mean_r"]
          and t >= w["min_t"] and s["days_mean_r"] > w["min_days_mean_r"])
    return "CONFIRMED" if ok else "NOT CONFIRMED"


def judge(db_path: str, now: int, spec: dict = SPEC) -> dict:
    """Every look that is due by `now`, in order; EVALUATION only after a QUALIFIED LEARNING look."""
    res = {"program": spec["program"], "spec_sha256": spec_sha(spec), "as_of": now, "looks": {}}
    for look in ("LEARNING", "EVALUATION"):
        if now < ts(spec["looks"][look]["judge_at"]):
            res["looks"][look] = {"verdict": "NOT DUE", "judge_at": spec["looks"][look]["judge_at"]}
            break
        if look == "EVALUATION" and res["looks"]["LEARNING"]["verdict"] != "QUALIFIED":
            res["looks"][look] = {"verdict": "NOT JUDGED", "why": "LEARNING did not qualify"}
            break
        u = units(db_path, look, spec)
        s = summary(u["rows"])
        at_floor = summary(units(db_path, look, spec, family=FLOOR_FAMILY)["rows"])
        res["looks"][look] = {"verdict": verdict(look, s, spec), "under_the_floor": s, "decided": u["decided"],
                              "not_resolved_by_the_date": u["not_resolved_by_the_date"],
                              "reported_never_judged": {"let_through_by_the_floor": at_floor}}
    final = [v["verdict"] for v in res["looks"].values()]
    res["verdict"] = next((v for v in reversed(final) if v not in ("NOT DUE", "NOT JUDGED")), "NOT DUE")
    return res


def status(db_path: str, now: int, spec: dict = SPEC) -> dict:
    """BLIND: per look, how many agreements are decided so far and when it is judged. No outcome is read."""
    return {look: {"decided_so_far": units(db_path, look, spec, read_outcomes=False)["decided"],
                   "window": f"{w['from']} to {w['to']}", "judge_at": w["judge_at"],
                   "due": now >= ts(w["judge_at"])} for look, w in spec["looks"].items()}


def main(argv: list[str]) -> int:
    if argv[:1] == ["freeze"]:
        SPEC_PATH.parent.mkdir(parents=True, exist_ok=True)
        SPEC_PATH.write_text(json.dumps({"spec": SPEC, "sha256": spec_sha(SPEC), "code_sha256": code_sha()},
                                        indent=1, sort_keys=True) + "\n")
        print(spec_sha(SPEC))
        return 0
    if argv[:1] in (["status"], ["run"]) and len(argv) in (2, 3):
        now = int(argv[2]) if len(argv) == 3 else int(time.time())  # the command line's clock; every function takes now
        frozen = json.loads(SPEC_PATH.read_text())
        if frozen["sha256"] != spec_sha(SPEC) or frozen["code_sha256"] != code_sha():
            raise SystemExit("the spec or the code changed after it was frozen: CONF-1 does not run")
        if frozen["sha256"] not in DOC.read_text():
            raise SystemExit(f"{DOC.name} must quote the spec sha256")
        if argv[0] == "status":
            print(json.dumps(status(argv[1], now), indent=1))
            return 0
        res = {**judge(argv[1], now), "code_sha256": code_sha(),
               "db_sha256": hashlib.sha256(Path(argv[1]).read_bytes()).hexdigest()}
        if res["verdict"] != "NOT DUE":
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
        print(json.dumps(res, indent=1, sort_keys=True))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
