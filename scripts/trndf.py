"""TRND-F: TRND-1's rule followed forward on the broker's four index CFDs, judged once
(research/preregistrations/TRND-F.md).

TRND-1 passed on the S&P 500's 1929-1989, and its holdout (the four index CFDs, 2021-01..2026-09) validated it. Both
were data that existed when the rule was chosen. TRND-F fixes now how the same rule, unchanged, is judged on months
that have not happened yet: December 2026 to November 2029. It is recorded so that no later result can be chosen
after the fact. Nothing here trades or changes the bot: whether TRND-1 becomes a paper strategy is the owner's
decision.

    python scripts/trndf.py spec          # freeze the design (reads no data)
    python scripts/trndf.py preregister   # register TRND-F in research/registry.jsonl
    python scripts/trndf.py fetch         # on or after 2029-12-03 only: Yahoo daily closes (on GitHub's runner)
    python scripts/trndf.py judge         # once, on or after 2029-12-03

Each command refuses to run if this code, TRND-1's rule code or the spec changed since registration.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import scripts.trnd1 as T  # noqa: E402
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict  # noqa: E402

R = ROOT / "research"
PID = "TRND-F"
DOC = "research/preregistrations/TRND-F.md"
SPEC = R / "specs" / "TRND-F.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "trndf"
CODE = ("scripts/trndf.py", "scripts/trnd1.py")  # the rule itself is TRND-1's, frozen with it
FORWARD = (date(2026, 12, 1), date(2029, 12, 1))  # the months held: December 2026 to November 2029
WARMUP_FROM = date(2026, 1, 1)  # December 2026's decision reads the ten month-ends from February 2026
JUDGE_FROM = date(2029, 12, 3)  # the first weekday after November 2029's close
TESTS = 1

GATES = {
    "complete": "all 36 months, December 2026 to November 2029, for all four indices",
    "mean": "mean net monthly return of the equal-weight basket > 0",
    "costs_x2": "mean net monthly return > 0 with the switching cost doubled",
    "smaller_crash": "a worst fall smaller than holding all four all the time",
}


def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()


def spec() -> dict:
    return {"program": PID, "forward_of": "TRND-1",
            "question": "does TRND-1's rule, unchanged, still earn a positive net return with a smaller worst fall "
                        "than holding the four index CFDs, on months that did not exist when it was chosen?",
            "indices": list(T.HOLDOUT_INDICES), "months": T.MONTHS, "cost_each_switch_side": T.COST_SIDE,
            "rule": "TRND-1's, unchanged: at each month-end close, hold each index for the next month if the close is "
                    "above the mean of its last 10 month-end closes (this one included), otherwise hold nothing for "
                    "it; the four at equal weight; a calendar month without a close is never bridged",
            "financing": "none (a swap-free account)", "dividends": "not counted (price indices)",
            "forward": [str(d) for d in FORWARD], "warmup_from": str(WARMUP_FROM), "judge_from": str(JUDGE_FROM),
            "gates": GATES, "tests": TESTS,
            "t": "no t gate: 36 months cannot show significance. The check is whether the validated rule still earns "
                 "and still protects, as its holdout's was",
            "after": {"PASSED": "reported as a forward confirmation of TRND-1; it changes nothing by itself",
                      "FAILED": "reported as it is; if TRND-1 is then a paper strategy, the owner is told it failed "
                                "forward, and it is stopped unless they decide otherwise"}}


def _dump(x) -> str:
    return json.dumps(x, indent=1, sort_keys=True, default=str) + "\n"


def _write(name: str, body: dict) -> dict:
    body = json.loads(json.dumps(body, sort_keys=True, default=str))
    body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(_dump(body))
    return body


def _not_before(now: datetime, what: str) -> None:
    if now.date() < JUDGE_FROM:
        raise SystemExit(f"nothing is {what} before {JUDGE_FROM}: the forward months are not complete")


# ── the data ─────────────────────────────────────────────────────────────

def cmd_fetch(now: datetime) -> None:
    _not_before(now, "fetched")
    DATA.mkdir(parents=True, exist_ok=True)
    man = {}
    for sym in T.HOLDOUT_INDICES:
        rows = T._yahoo(sym, now)
        body = "date,close\n" + "".join(f"{d},{v!r}\n" for d, v in rows)
        name = sym.lstrip("^")
        (DATA / f"{name}.csv").write_text(body)
        man[sym] = {"file": f"{name}.csv", "rows": len(rows), "first": rows[0][0], "last": rows[-1][0],
                    "sha256": hashlib.sha256(body.encode()).hexdigest()}
        print(sym, man[sym]["first"], man[sym]["last"], man[sym]["rows"])
    (DATA / "manifest.json").write_text(_dump({"retrieved": now.isoformat(), "series": man}))


def load(start: date, until: date) -> dict[str, dict[date, float]]:
    """Each index's closes in [start, until), only if its file matches the manifest."""
    man = json.loads((DATA / "manifest.json").read_text())["series"]
    out = {}
    for sym in T.HOLDOUT_INDICES:
        m = man[sym]
        body = (DATA / m["file"]).read_text()
        if hashlib.sha256(body.encode()).hexdigest() != m["sha256"]:
            raise SystemExit(f"{m['file']} does not match its manifest: nothing is judged on it")
        rows = [ln.split(",") for ln in body.strip().splitlines()[1:]]
        out[sym] = {date.fromisoformat(d): float(c) for d, c in rows if start <= date.fromisoformat(d) < until}
    return out


# ── the result ───────────────────────────────────────────────────────────

def result(data: dict) -> dict:
    net, hold_all = T.basket(data, *FORWARD)
    net2, _ = T.basket(data, *FORWARD, cost_x=2.0)
    s, s2 = T.stats(net), T.stats(net2)
    fall, fall_all = T.worst_fall(net), T.worst_fall(hold_all)
    ok = {"complete": s["n"] == T.months_between(*FORWARD), "mean": (s["mean"] or 0) > 0,
          "costs_x2": (s2["mean"] or 0) > 0, "smaller_crash": bool(net) and fall < fall_all}
    return {"months": s, "costs_x2": s2, "holding_all_the_time": T.stats(hold_all),
            "worst_fall": round(fall, 4), "worst_fall_holding_all_the_time": round(fall_all, 4), "gates": ok,
            "failed_gates": [g for g, v in ok.items() if not v],
            "verdict": "PASSED" if all(ok.values()) else "FAILED"}


# ── the commands ─────────────────────────────────────────────────────────

def _registry() -> Registry:
    return Registry.load(R / "registry.jsonl", Holdout.load(R / "holdout.json"))


def cmd_spec() -> None:
    reg = _registry()
    if any(t.id == PID for t in reg.trials):
        raise SystemExit(f"{PID} is registered; its spec is frozen")
    s = spec()
    SPEC.parent.mkdir(parents=True, exist_ok=True)
    SPEC.write_text(_dump({"spec": s, "sha256": spec_sha(s), "code_sha256": code_hash()}))
    print(spec_sha(s))


def cmd_preregister(now: datetime) -> None:
    reg = _registry()
    frozen = json.loads(SPEC.read_text())
    if spec_sha(spec()) != frozen["sha256"] or code_hash() != frozen["code_sha256"]:
        raise SystemExit("the spec or the code changed since `spec`")
    if frozen["sha256"] not in (ROOT / DOC).read_text():
        raise SystemExit(f"{DOC} must quote the spec sha256 {frozen['sha256']}")
    reg.register(Trial(id=PID, registered=now, title="TRND-F: TRND-1's rule forward, 2026-12..2029-11",
                       hypothesis=spec()["question"], uses=(Use(T.UNIVERSE, WARMUP_FROM, FORWARD[1], "judge"),),
                       tests=TESTS, configurations=TESTS, preregistration=DOC,
                       design={"spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"],
                               "judge_from": str(JUDGE_FROM)}))
    print("registered", PID)


def cmd_judge(now: datetime) -> None:
    _not_before(now, "judged")
    reg = _registry()
    trial = reg.get(PID)
    frozen = json.loads(SPEC.read_text())
    if trial.design.get("spec_sha256") != frozen["sha256"] or frozen["code_sha256"] != code_hash():
        raise SystemExit("the spec or the code differs from what was preregistered")
    if reg.verdict_of(PID) is not None:
        raise SystemExit(f"{PID} already has a verdict")
    manifest = json.loads((DATA / "manifest.json").read_text())
    if datetime.fromisoformat(manifest["retrieved"]).date() < JUDGE_FROM:
        raise SystemExit("the data were fetched before the forward months were complete")
    res = result(load(WARMUP_FROM, FORWARD[1]))
    body = _write(PID, {"program": PID, "forward_of": "TRND-1", **res, "forward": [str(d) for d in FORWARD],
                        "spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"], "data": manifest})
    reg.record_verdict(Verdict(PID, now, body["verdict"], {"artifact": f"research/knowledge/{PID}.json",
                                                           "artifact_sha256": body["sha256"]}))
    print(body["verdict"], "failed:", res["failed_gates"], json.dumps(res["months"]), "worst fall", res["worst_fall"],
          "vs", res["worst_fall_holding_all_the_time"])


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc)  # the command line's clock: every function above takes its dates as arguments
    {"spec": cmd_spec, "preregister": lambda: cmd_preregister(now), "fetch": lambda: cmd_fetch(now),
     "judge": lambda: cmd_judge(now)}.get(cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
