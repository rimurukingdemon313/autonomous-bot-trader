"""VRP-1: the volatility risk premium, short VIX futures in contango (research/preregistrations/VRP-1.md).

The owner, 2026-11-05: "don't fixate on the AI trading; anything that makes us a profit; never stop". About 58 programs
here asked whether some signal PREDICTS a price; none survived costs since 2008. VRP-1 asks about a PREMIUM: buyers of
crash insurance pay for it. Short-term VIX futures usually trade above the VIX (contango) and roll down toward it, so a
holder of them loses, on average, what an insurance seller earns (Simon & Campasano 2014, "The VIX futures basis";
Whaley 2013). The cost is rare, violent losses when volatility spikes. The rule holds the short only while the VIX's
term structure is in contango, and stands aside when it inverts, which is when spikes usually run.

The rule, fixed before any VRP-1 data was fetched:
- each trading day, with the VIX and the 3-month VIX (VIX3M) of the PREVIOUS close (one day of lag, so the 15 minutes
  between the indices' 16:15 and the ETF's 16:00 close can never be read early): ratio < 1 (contango) means short
  VIXY (1x the short-term VIX futures index) from today's close to the next; ratio >= 1 means flat;
- the short is held at a constant notional, resized each day; a change of exposure and each day's resizing pay 0.10%
  of the notional traded; a short pays a borrow fee of 3% a year on the notional;
- a day without its prices is no trade, never filled.

    python scripts/vrp1.py spec          # freeze the design (reads no data)
    python scripts/vrp1.py preregister   # register VRP-1 in research/registry.jsonl
    python scripts/vrp1.py fetch         # Yahoo daily closes (on GitHub's runner: Yahoo is blocked here)
    python scripts/vrp1.py judge         # 2011..2021: development, validation, the gates
    python scripts/vrp1.py holdout       # only if VRP-1 PASSED: 2022-01..2026-09, once

Each command refuses to run if the code or the spec changed since registration. Nothing here changes the bot.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time as _time
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from statistics import NormalDist
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402
from scripts.xts1 import drawdown, stats  # noqa: E402

R = ROOT / "research"
PID, HID = "VRP-1", "VRP-1-H"
DOC = "research/preregistrations/VRP-1.md"
SPEC = R / "specs" / "VRP-1.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "vrp"
CODE = ("scripts/vrp1.py", "scripts/xts1.py")
UNIVERSE = "us-vol-etp"
ETP, VIX, VIX3M = "VIXY", "^VIX", "^VIX3M"
DEV = (date(2011, 2, 1), date(2017, 1, 1))
VAL = (date(2017, 1, 1), date(2022, 1, 1))
JUDGE = (DEV[0], VAL[1])
HOLD = (date(2022, 1, 1), date(2026, 10, 1))
COST = 0.0010          # per unit of notional traded, each side
BORROW_PA = 0.03       # the short's borrow fee, a year, on the notional held
TESTS = 2              # the mean's t (G1) and the timing t (G7)
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader VRP-1)"}

GATES = {
    "t": "t of the mean daily net return over 2011-02..2021-12 >= the threshold",
    "development": "mean daily net > 0 in 2011-02..2016",
    "validation": "mean daily net > 0 in 2017..2021",
    "costs_x2": "mean daily net > 0 with the trading cost and the borrow fee doubled",
    "top_year": "no calendar year supplies more than 50% of the total net",
    "timing": "the rule beats an always-held short at its own average exposure: mean daily difference > 0, t >= 2.0",
}
HOLDOUT_RULE = ("2022-01..2026-09: mean daily net > 0 with one-sided t >= 1.645, mean daily net > 0 with costs doubled, "
                "and the timing difference's mean > 0")


def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()


def threshold(reg: Registry) -> float:
    return max(3.0, bonferroni_t(reg.tests_on(UNIVERSE, JUDGE[0], HOLD[1]) + TESTS))


def spec(reg: Registry) -> dict:
    return {"program": PID, "question": "does shorting short-term VIX futures while the VIX term structure is in "
                                        "contango earn a positive net return, and beat always holding the short?",
            "instrument": ETP, "signal": [VIX, VIX3M], "lag_days": 1, "cost_per_side": COST, "borrow_pa": BORROW_PA,
            "rule": "exposure for the day = -1 (short) when VIX / VIX3M at the previous close < 1, else 0; constant "
                    "notional resized daily; costs on exposure changes and on each day's resizing; borrow on the short",
            "data": "Yahoo daily closes (VIXY adjusted for its splits; the two indices as published), each file's "
                    "sha256 in the manifest; a missing day is no trade",
            "periods": {"development": [str(d) for d in DEV], "validation": [str(d) for d in VAL],
                        "holdout": [str(d) for d in HOLD]},
            "gates": GATES, "holdout_rule": HOLDOUT_RULE, "threshold_t": round(threshold(reg), 4), "tests": TESTS,
            "after": {"PASSED and VALIDATED": "proposed to the owner as a paper strategy of its own (rule 14), sized "
                                              "by the risk engine for its tail, followed forward on paper; never real "
                                              "money",
                      "otherwise": "reported as it is; nothing changes"}}


def _dump(x) -> str:
    return json.dumps(x, indent=1, sort_keys=True, default=str) + "\n"


def _write(name: str, body: dict) -> dict:
    body = json.loads(json.dumps(body, sort_keys=True, default=str))
    body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(_dump(body))
    return body


# ── the data ─────────────────────────────────────────────────────────────

def _yahoo(sym: str) -> list[tuple[str, float]]:
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1=1262304000&period2={int(_time.time())}"
           "&interval=1d&events=split")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        res = json.loads(r.read())["chart"]["result"][0]
    tz = ZoneInfo(res["meta"]["exchangeTimezoneName"])
    adj = ((res["indicators"].get("adjclose") or [{}])[0] or {}).get("adjclose")
    closes = adj if adj else res["indicators"]["quote"][0]["close"]
    rows = {}
    for t, c in zip(res["timestamp"], closes):
        if c is not None and c > 0:
            rows[datetime.fromtimestamp(t, timezone.utc).astimezone(tz).date().isoformat()] = float(c)
    return sorted(rows.items())


def cmd_fetch() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    man = {}
    for sym in (ETP, VIX, VIX3M):
        rows = _yahoo(sym)
        body = "date,close\n" + "".join(f"{d},{v!r}\n" for d, v in rows)
        name = sym.lstrip("^")
        (DATA / f"{name}.csv").write_text(body)
        man[sym] = {"file": f"{name}.csv", "rows": len(rows), "first": rows[0][0], "last": rows[-1][0],
                    "sha256": hashlib.sha256(body.encode()).hexdigest()}
        print(sym, man[sym]["first"], man[sym]["last"], man[sym]["rows"])
    (DATA / "manifest.json").write_text(_dump({"retrieved": datetime.now(timezone.utc).isoformat(), "series": man}))


def load(until: date) -> dict[str, dict[date, float]]:
    """Each series' closes before `until`, only if its file matches the manifest: the judge never reads the holdout."""
    man = json.loads((DATA / "manifest.json").read_text())["series"]
    out = {}
    for sym, m in man.items():
        body = (DATA / m["file"]).read_text()
        if hashlib.sha256(body.encode()).hexdigest() != m["sha256"]:
            raise SystemExit(f"{m['file']} does not match its manifest: nothing is judged on it")
        rows = [ln.split(",") for ln in body.strip().splitlines()[1:]]
        out[sym] = {date.fromisoformat(d): float(c) for d, c in rows if date.fromisoformat(d) < until}
    return out


# ── the rule, and what it earned ─────────────────────────────────────────

def days_of(data: dict, start: date, end: date) -> list[date]:
    """The ETF's trading days in [start, end), each with the previous trading day (the ETF's own calendar)."""
    return sorted(d for d in data[ETP] if start <= d < end)


def book(data: dict, start: date, end: date, cost: float = COST, borrow: float = BORROW_PA,
         always: bool = False) -> dict[date, dict]:
    """Per trading day d: the short's exposure over (previous close, d's close], set from the VIX / VIX3M ratio at the
    close BEFORE that one, and the net return it earned. `always` holds the short every day (the timing benchmark)."""
    etp = data[ETP]
    cal = sorted(etp)
    out, prev_e = {}, None
    for i in range(2, len(cal)):
        d, p, pp = cal[i], cal[i - 1], cal[i - 2]
        if not start <= d < end:
            continue
        v, v3 = data[VIX].get(pp), data[VIX3M].get(pp)
        if v is None or v3 is None:
            prev_e = None  # no signal: no trade that day, never filled
            continue
        e = 1.0 if always or v / v3 < 1.0 else 0.0
        r = etp[d] / etp[p] - 1.0
        traded = abs(e - (prev_e if prev_e is not None else 0.0)) + e * abs(r)  # entry/exit, then the daily resize
        out[d] = {"ret": r, "exp": e, "net": -e * r - cost * traded - e * borrow / 252.0}
        prev_e = e
    return out


def timing(data: dict, start: date, end: date) -> dict[date, float]:
    """Each day, the rule's net minus an always-held short scaled to the rule's average exposure."""
    rule, every = book(data, start, end), book(data, start, end, always=True)
    days = sorted(set(rule) & set(every))
    avg = sum(rule[d]["exp"] for d in days) / len(days) if days else 0.0
    return {d: rule[d]["net"] - avg * every[d]["net"] for d in days}


def gates(data: dict, thr: float) -> dict:
    b = book(data, *JUDGE)
    net = {d: v["net"] for d, v in b.items()}
    x = list(net.values())
    s = stats(x)
    dev, val = stats([v for d, v in net.items() if d < VAL[0]]), stats([v for d, v in net.items() if d >= VAL[0]])
    x2 = stats([v["net"] for v in book(data, *JUDGE, cost=2 * COST, borrow=2 * BORROW_PA).values()])
    by_year: dict = {}
    for d, v in net.items():
        by_year[d.year] = by_year.get(d.year, 0.0) + v
    total = sum(x)
    top = max(by_year.values()) / total if total > 0 else None
    tm = stats(list(timing(data, *JUDGE).values()))
    always = {d: v["net"] for d, v in book(data, *JUDGE, always=True).items()}
    ok = {"t": s["t"] is not None and s["t"] >= thr,
          "development": (dev["mean"] or 0) > 0, "validation": (val["mean"] or 0) > 0,
          "costs_x2": (x2["mean"] or 0) > 0, "top_year": top is not None and top <= 0.5,
          "timing": (tm["mean"] or 0) > 0 and tm["t"] is not None and tm["t"] >= 2.0}
    return {"net": s, "development": dev, "validation": val, "costs_x2": x2,
            "by_year": {str(k): round(v, 4) for k, v in sorted(by_year.items())},
            "top_year_share": None if top is None else round(top, 3), "timing": tm,
            "share_of_days_short": round(sum(v["exp"] for v in b.values()) / max(1, len(b)), 4),
            "max_drawdown": round(drawdown(net), 4), "worst_day": round(min(x), 4) if x else None,
            "reported_always_short": {**stats(list(always.values())), "max_drawdown": round(drawdown(always), 4),
                                      "worst_day": round(min(always.values()), 4) if always else None},
            "threshold_t": thr, "gates": ok, "failed_gates": [g for g, v in ok.items() if not v],
            "passed": all(ok.values())}


# ── the commands ─────────────────────────────────────────────────────────

def _registry() -> Registry:
    return Registry.load(R / "registry.jsonl", Holdout.load(R / "holdout.json"))


def _check_frozen(reg: Registry) -> dict:
    trial = reg.get(PID)
    frozen = json.loads(SPEC.read_text())
    if trial.design.get("spec_sha256") != frozen["sha256"] or frozen["code_sha256"] != code_hash():
        raise SystemExit("the spec or the code differs from what was preregistered")
    return frozen


def cmd_spec() -> None:
    reg = _registry()
    if any(t.id == PID for t in reg.trials):
        raise SystemExit(f"{PID} is registered; its spec is frozen")
    s = spec(reg)
    SPEC.parent.mkdir(parents=True, exist_ok=True)
    SPEC.write_text(_dump({"spec": s, "sha256": spec_sha(s), "code_sha256": code_hash()}))
    print(spec_sha(s), "threshold", s["threshold_t"])


def cmd_preregister(now: datetime) -> None:
    reg = _registry()
    frozen = json.loads(SPEC.read_text())
    s = spec(reg)
    if spec_sha(s) != frozen["sha256"] or code_hash() != frozen["code_sha256"]:
        raise SystemExit("the spec or the code changed since `spec`")
    if frozen["sha256"] not in (ROOT / DOC).read_text():
        raise SystemExit(f"{DOC} must quote the spec sha256 {frozen['sha256']}")
    reg.register(Trial(id=PID, registered=now, title="VRP-1: short VIX futures in contango",
                       hypothesis=s["question"], uses=(Use(UNIVERSE, JUDGE[0], JUDGE[1], "judge"),), tests=TESTS,
                       configurations=TESTS, preregistration=DOC,
                       design={"spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"],
                               "threshold_t": s["threshold_t"]}))
    print("registered", PID, "threshold", s["threshold_t"])


def cmd_judge(now: datetime) -> None:
    reg = _registry()
    frozen = _check_frozen(reg)
    if reg.verdict_of(PID) is not None:
        raise SystemExit(f"{PID} already has a verdict")
    data = load(JUDGE[1])
    res = gates(data, frozen["spec"]["threshold_t"])
    body = _write(PID, {"program": PID, "verdict": "PASSED" if res["passed"] else "FAILED", **res,
                        "periods": frozen["spec"]["periods"], "spec_sha256": frozen["sha256"],
                        "code_sha256": frozen["code_sha256"], "data": json.loads((DATA / "manifest.json").read_text())})
    reg.record_verdict(Verdict(PID, now, body["verdict"], {"artifact": f"research/knowledge/{PID}.json",
                                                           "artifact_sha256": body["sha256"]}))
    print(body["verdict"], "failed:", res["failed_gates"], "net", json.dumps(res["net"]), "timing",
          json.dumps(res["timing"]), "short", res["share_of_days_short"], "dd", res["max_drawdown"])


def cmd_holdout(now: datetime) -> None:
    reg = _registry()
    frozen = _check_frozen(reg)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    if judged["verdict"] != "PASSED":
        raise SystemExit("VRP-1 did not pass: the holdout stays unread")
    if any(t.id == HID for t in reg.trials):
        raise SystemExit("the holdout was opened once already")
    reg.register(Trial(id=HID, registered=now, title="VRP-1 holdout: 2022-01..2026-09", hypothesis=HOLDOUT_RULE,
                       uses=(Use(UNIVERSE, HOLD[0], HOLD[1], "judge"),), tests=1, configurations=1,
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"]}))
    data = load(HOLD[1])
    b = book(data, *HOLD)
    net = {d: v["net"] for d, v in b.items()}
    s = stats(list(net.values()))
    s2 = stats([v["net"] for v in book(data, *HOLD, cost=2 * COST, borrow=2 * BORROW_PA).values()])
    tm = stats(list(timing(data, *HOLD).values()))
    ok = bool(s["mean"] and s["mean"] > 0 and s["t"] is not None and s["t"] >= NormalDist().inv_cdf(0.95)
              and (s2["mean"] or 0) > 0 and (tm["mean"] or 0) > 0)
    verdict = "PASSED" if ok else "FAILED"
    body = _write(HID, {"program": HID, "holdout_of": PID, "period": [str(d) for d in HOLD], "net": s, "costs_x2": s2,
                        "timing": tm, "max_drawdown": round(drawdown(net), 4),
                        "worst_day": round(min(net.values()), 4) if net else None, "rule": HOLDOUT_RULE,
                        "classification": "VALIDATED" if ok else "REJECTED", "verdict": verdict})
    reg.record_verdict(Verdict(HID, now, verdict, {"artifact": f"research/knowledge/{HID}.json",
                                                   "artifact_sha256": body["sha256"]}))
    print(verdict, json.dumps(s), "x2", s2["mean"], "timing", tm["mean"])


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc)  # the command line's clock: every function above takes its dates as arguments
    {"spec": cmd_spec, "preregister": lambda: cmd_preregister(now), "fetch": cmd_fetch,
     "judge": lambda: cmd_judge(now), "holdout": lambda: cmd_holdout(now)}.get(cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
