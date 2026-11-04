"""CONF-2: does the strongest model's judgement pick the H1 agreements that win? (research/preregistrations/CONF-2.md)

The owner, 2026-11-04: "change everything if you must; the most important thing is a profit; the budget can be $100".
On H1 the traders' stated confidence is each model's habit, so the confidence floor refuses nearly every agreement
(CONF-1). Since dual-ai 1.20.0 the senior trader (anthropic/claude-opus-5.5) judges, in shadow only, every agreement
below the floor, as if it could be taken: APPROVE or VETO, recorded before the outcome (`senior_shadow`). The
agreement itself is followed forward as the trade it would have been (DUAL_AI_LOW_CONFIDENCE). This asks, once, at
dates fixed before any review was made: did the trades it approved pay, and did they beat the ones it did not?

One rule, two looks:
- LEARNING (decided 2026-11-05 to 2026-11-16 UTC, judged on 2026-11-20): QUALIFIED when the approved trades number 30
  or more, their mean net R is +0.10 or more with t of 2.0 or more over trades and over the days' own means, and they
  beat the rest (vetoes, and approvals below even odds) by 0.20 R or more with Welch t of 2.0 or more. Otherwise
  FAILED, and EVALUATION is not judged.
- EVALUATION (decided 2026-11-16 to 2026-11-23, judged on 2026-11-27), only after QUALIFIED: CONFIRMED when the
  approved trades number 15 or more, their mean net R is above 0 with t of 2.0 or more, the days' mean is above 0, and
  they beat the rest. Otherwise NOT CONFIRMED.
Too few approved or other trades in a look: INCONCLUSIVE, nothing changes.

An outcome counts only if the ledger recorded it by the look's date (its row's `ts`). Nothing here changes the bot.

    python scripts/conf2.py freeze                       # writes research/specs/CONF-2.json (spec + both sha256)
    python scripts/conf2.py status <aitrader.db> [now]   # BLIND: reviews per look and verdict counts, no outcome read
    python scripts/conf2.py run <aitrader.db> [now]      # refuses before a look's date; judges what is due
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
SPEC_PATH = ROOT / "research" / "specs" / "CONF-2.json"
DOC = ROOT / "research" / "preregistrations" / "CONF-2.md"
OUT = ROOT / "research" / "knowledge" / "CONF-2.json"

SPEC = {
    "program": "CONF-2",
    "question": "on the H1 chart, do the agreements below the confidence floor that the senior trader approved in "
                "shadow pay after costs, and beat the ones it did not approve?",
    "units": "every DUAL_AI_LOW_CONFIDENCE proposal on the H1 chart decided inside the look's window, in the look's "
             "partition, whose decision recorded a usable senior shadow verdict (senior_shadow: asked, APPROVE or "
             "VETO, a confidence), and whose outcome the ledger recorded as RESOLVED by the look's date "
             "(forward_outcomes.ts), each decision once",
    "groups": {"APPROVED": "verdict APPROVE with confidence of 50 or more (the live rule's even odds)",
               "REST": "verdict VETO, or APPROVE below 50"},
    "looks": {
        "LEARNING": {"from": "2026-11-05T00:00:00Z", "to": "2026-11-16T00:00:00Z", "judge_at": "2026-11-20T00:00:00Z",
                     "min_approved": 30, "min_rest": 30, "min_mean_r": 0.10, "min_t": 2.0, "min_days_t": 2.0,
                     "min_gap_r": 0.20, "min_gap_t": 2.0},
        "EVALUATION": {"from": "2026-11-16T00:00:00Z", "to": "2026-11-23T00:00:00Z",
                       "judge_at": "2026-11-27T00:00:00Z", "min_approved": 15, "min_rest": 15, "min_mean_r": 0.0,
                       "min_t": 2.0, "min_days_mean_r": 0.0, "min_gap_r": 0.0},
    },
    "measure": "net R as followed forward (forward.walk: Trader 1's levels, the H1 time exit, spread, slippage and "
               "commission); t of the mean over trades; the same over the UTC days' own mean net R; Welch t of the "
               "approved trades' mean minus the rest's",
    "verdicts": {
        "LEARNING": "QUALIFIED if both groups reach their minimum and every LEARNING condition holds; INCONCLUSIVE if a "
                    "group is short; FAILED otherwise (EVALUATION is then not judged)",
        "EVALUATION": "only after QUALIFIED: CONFIRMED if both groups reach their minimum and every EVALUATION "
                      "condition holds; INCONCLUSIVE if a group is short; NOT CONFIRMED otherwise",
    },
    "after": {
        "CONFIRMED": "on H1 the senior's approval replaces the confidence floor for the agreements it judges, in a new "
                     "dual-ai version, the owner told first; the lesson check, the risk engine and the always-sure "
                     "seat rule stay as they are, and its vetoes stay followed forward",
        "otherwise": "nothing changes; the result is reported as it is",
    },
    "reported_never_judged": "the share approved, the agreements without a usable review, the senior's reviews of "
                             "real trade candidates, and CONF-1's units without a review",
}
UNIT_FAMILY = "DUAL_AI_LOW_CONFIDENCE"
EVEN_ODDS = 50


def spec_sha(spec: dict) -> str:
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


def code_sha() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def ts(iso: str) -> int:
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc).timestamp())


# ── the record ───────────────────────────────────────────────────────────

def verdicts(db) -> dict:
    """decision id -> the senior's usable shadow verdict on it: ("APPROVED" | "REST", confidence)."""
    out = {}
    for did, payload in db.execute("SELECT id, payload FROM decisions"):
        p = json.loads(payload)
        ss = ((p.get("ai") or {}).get("dual_ai") or {}).get("senior_shadow")
        if not isinstance(ss, dict) or not ss.get("asked") or ss.get("verdict") not in ("APPROVE", "VETO"):
            continue
        c = ss.get("confidence")
        if not isinstance(c, (int, float)) or isinstance(c, bool) or not 0 <= c <= 100:
            continue
        out[did] = ("APPROVED" if ss["verdict"] == "APPROVE" and c >= EVEN_ODDS else "REST", float(c))
    return out


def units(db_path: str, look: str, spec: dict = SPEC, read_outcomes: bool = True) -> dict:
    """The look's agreements below the floor that the senior judged; with `read_outcomes`, each one's net R if the
    ledger recorded it RESOLVED by the look's date; without, none is read (the blind status)."""
    w = spec["looks"][look]
    t0, t1, due = ts(w["from"]), ts(w["to"]), ts(w["judge_at"])
    db = sqlite3.connect(db_path)
    seen = verdicts(db)
    decided, unreviewed = {}, 0
    for did, t, part, payload in db.execute("SELECT decision_id, t, partition, payload FROM forward_proposals"):
        p = json.loads(payload)
        if not (p.get("family") == UNIT_FAMILY and p.get("timeframe") == "H1" and part == look and t0 <= int(t) < t1):
            continue
        v = seen.get(str(did).split(":")[0])
        if v is None:
            unreviewed += 1
            continue
        decided[did] = (int(t), v[0])
    out = {"decided": len(decided), "without_a_usable_review": unreviewed,
           "approved_decided": sum(1 for _, g in decided.values() if g == "APPROVED"), "rows": []}
    if not read_outcomes:
        return out
    got = set()
    for did, rec_ts, payload in db.execute("SELECT decision_id, ts, payload FROM forward_outcomes ORDER BY seq"):
        if did not in decided or did in got or float(rec_ts) > due:
            continue
        o = json.loads(payload)
        if o.get("status") != "RESOLVED" or not isinstance(o.get("net_r"), (int, float)):
            continue
        got.add(did)
        t, g = decided[did]
        out["rows"].append({"id": did, "t": t, "group": g, "net_r": float(o["net_r"])})
    out["not_resolved_by_the_date"] = len(decided) - len(out["rows"])
    return out


# ── the judgement ────────────────────────────────────────────────────────

def _mean_sd(xs: list[float]) -> tuple[float | None, float | None]:
    if not xs:
        return None, None
    m = sum(xs) / len(xs)
    return m, (math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) if len(xs) > 1 else None)


def _t(xs: list[float]) -> float | None:
    m, sd = _mean_sd(xs)
    return None if m is None or not sd else m / (sd / math.sqrt(len(xs)))


def summary(rows: list[dict]) -> dict:
    xs = [r["net_r"] for r in rows]
    days: dict = {}
    for r in rows:
        days.setdefault(datetime.fromtimestamp(r["t"], timezone.utc).strftime("%Y-%m-%d"), []).append(r["net_r"])
    dmeans = [sum(v) / len(v) for v in days.values()]
    m, _ = _mean_sd(xs)
    dm, _ = _mean_sd(dmeans)
    rnd = (lambda v, k=4: None if v is None else round(v, k))
    wins, losses = sum(x for x in xs if x > 0), -sum(x for x in xs if x < 0)
    return {"n": len(xs), "mean_r": rnd(m), "t": rnd(_t(xs), 2), "days": len(days), "days_mean_r": rnd(dm),
            "days_t": rnd(_t(dmeans), 2), "win_rate": round(sum(1 for x in xs if x > 0) / len(xs), 3) if xs else None,
            "profit_factor": round(wins / losses, 3) if losses > 0 else None, "total_r": round(sum(xs), 3)}


def gap(a: list[float], b: list[float]) -> dict:
    """The approved trades' mean net R minus the rest's, with Welch t."""
    ma, sa = _mean_sd(a)
    mb, sb = _mean_sd(b)
    if ma is None or mb is None:
        return {"gap_r": None, "welch_t": None}
    se = math.sqrt((sa or 0) ** 2 / len(a) + (sb or 0) ** 2 / len(b))
    return {"gap_r": round(ma - mb, 4), "welch_t": round((ma - mb) / se, 2) if se > 0 else None}


def verdict(look: str, approved: dict, rest: dict, g: dict, spec: dict = SPEC) -> str:
    w = spec["looks"][look]
    if approved["n"] < w["min_approved"] or rest["n"] < w["min_rest"]:
        return "INCONCLUSIVE"
    m, t, gr = approved["mean_r"], approved["t"], g["gap_r"]
    if m is None or t is None or gr is None:
        return "FAILED" if look == "LEARNING" else "NOT CONFIRMED"
    if look == "LEARNING":
        ok = (m >= w["min_mean_r"] and t >= w["min_t"] and approved["days_t"] is not None
              and approved["days_t"] >= w["min_days_t"] and gr >= w["min_gap_r"] and g["welch_t"] is not None
              and g["welch_t"] >= w["min_gap_t"])
        return "QUALIFIED" if ok else "FAILED"
    ok = (m > w["min_mean_r"] and t >= w["min_t"] and approved["days_mean_r"] is not None
          and approved["days_mean_r"] > w["min_days_mean_r"] and gr > w["min_gap_r"])
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
        a = [r for r in u["rows"] if r["group"] == "APPROVED"]
        b = [r for r in u["rows"] if r["group"] == "REST"]
        sa, sb, g = summary(a), summary(b), gap([r["net_r"] for r in a], [r["net_r"] for r in b])
        res["looks"][look] = {"verdict": verdict(look, sa, sb, g, spec), "approved": sa, "rest": sb, **g,
                              "decided": u["decided"], "approved_decided": u["approved_decided"],
                              "without_a_usable_review": u["without_a_usable_review"],
                              "not_resolved_by_the_date": u["not_resolved_by_the_date"]}
    final = [v["verdict"] for v in res["looks"].values()]
    res["verdict"] = next((v for v in reversed(final) if v not in ("NOT DUE", "NOT JUDGED")), "NOT DUE")
    return res


def status(db_path: str, now: int, spec: dict = SPEC) -> dict:
    """BLIND: per look, the reviews decided so far and how many approved, and when it is judged. No outcome is read."""
    out = {}
    for look, w in spec["looks"].items():
        u = units(db_path, look, spec, read_outcomes=False)
        out[look] = {"reviewed_so_far": u["decided"], "approved_so_far": u["approved_decided"],
                     "without_a_usable_review": u["without_a_usable_review"], "window": f"{w['from']} to {w['to']}",
                     "judge_at": w["judge_at"], "due": now >= ts(w["judge_at"])}
    return out


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
            raise SystemExit("the spec or the code changed after it was frozen: CONF-2 does not run")
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
