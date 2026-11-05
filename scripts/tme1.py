"""TME-1: the Treasury month-end effect (research/preregistrations/TME-1.md).

The owner, 2026-11-05: "don't fixate on the AI trading; anything that makes us a profit; never stop". Hartley & Schwarz
(2019) found that coupon Treasuries earned their excess return in the last few days of each month and about nothing on
other days, over 1990-2018: insurers buy more Treasuries at month-end than on any other day, and funds that track bond
indices extend their duration when the indices rebalance at month-end. TME-1 asks whether holding the 7-10 year
Treasury ETF (IEF) over each month's last three trading days pays, held as a retail CFD holds it.

The rule, fixed before any TME-1 price was fetched:
- the month's last four NYSE trading days T-3, T-2, T-1, T are computed from the NYSE's rules and its known unscheduled
  closures (scripts/phd1.py); the month is no trade unless IEF has a close on each of them;
- long IEF from the close of T-3 to the close of T (the last three trading days);
- 0.03% a side (spread and slippage), and the T-bill yield (the one last published, at most 7 days old) plus 2.5% a
  year for each night; a month whose financing is unknown is no trade;
- reported, never a gate: every other run of three trading days held the same way, as the control.

    python scripts/tme1.py spec          # freeze the design (reads no data)
    python scripts/tme1.py preregister   # register TME-1 in research/registry.jsonl
    python scripts/tme1.py fetch         # Yahoo daily closes (on GitHub's runner: Yahoo is blocked here)
    python scripts/tme1.py judge         # 2003..2018: development, validation, the gates
    python scripts/tme1.py holdout       # only if TME-1 PASSED: 2019-01..2026-09, once

Each command refuses to run if the code or the spec changed since registration. Nothing here changes the bot.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time as _time
import urllib.parse
import urllib.request
from bisect import bisect_right
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402
from scripts.phd1 import UNSCHEDULED, nyse_holidays  # noqa: E402

R = ROOT / "research"
PID, HID = "TME-1", "TME-1-H"
DOC = "research/preregistrations/TME-1.md"
SPEC = R / "specs" / "TME-1.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "tme"
CODE = ("scripts/tme1.py", "scripts/phd1.py")
UNIVERSE = "us-treasury-daily"
#: earlier tests that read Treasury prices or yields: DIV-1 (TLT, IEF), DIV-2 (^TNX, ^FVX), those sharing their data,
#: and TSY-1
TREASURY_UNIVERSES = ("multi-asset-etf", "multi-asset-long", UNIVERSE)
BOND, RATE = "IEF", "^IRX"
DEV = (date(2003, 1, 1), date(2011, 1, 1))
VAL = (date(2011, 1, 1), date(2019, 1, 1))
JUDGE = (DEV[0], VAL[1])
HOLD = (date(2019, 1, 1), date(2026, 10, 1))
HOLD_DAYS = 3
COST_SIDE = 0.0003
MARKUP_PA = 0.025
RATE_STALE_DAYS = 7
TESTS = 1
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader TME-1)"}

GATES = {
    "t": "t of the mean net return per month-end, 2003..2018, >= the threshold",
    "development": "mean net per month-end > 0 in 2003..2010",
    "validation": "mean net per month-end > 0 in 2011..2018",
    "costs_x2": "mean net per month-end > 0 with the cost per side and the markup doubled",
    "top_year": "no calendar year supplies more than 50% of the total",
}
HOLDOUT_RULE = ("2019-01..2026-09: mean net per month-end > 0 with one-sided t >= 1.645, and > 0 with the costs "
                "doubled")


def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()


def threshold(reg: Registry) -> float:
    earlier = sum(reg.tests_on(u, date.min, date.max) for u in TREASURY_UNIVERSES)
    return max(3.0, bonferroni_t(earlier + TESTS))


def spec(reg: Registry) -> dict:
    return {"program": PID, "question": "does holding the 7-10 year Treasury ETF over each month's last three trading "
                                        "days earn a positive net return at a CFD's costs?",
            "bond": BOND, "rate": RATE, "hold_days": HOLD_DAYS, "cost_each_side": COST_SIDE, "markup_pa": MARKUP_PA,
            "rate_stale_days": RATE_STALE_DAYS,
            "calendar": "NYSE trading days computed from its rules and its unscheduled closures (scripts/phd1.py); "
                        "a month is no trade unless IEF has a close on each of its last four",
            "rule": "long from the close of the month's fourth-last trading day to the close of its last",
            "data": "Yahoo daily closes: IEF adjusted for distributions and splits, ^IRX as published (negative and "
                    "zero yields kept); each file's sha256 in the manifest",
            "control": "every other run of three trading days in the same period, held the same way (reported only)",
            "periods": {"development": [str(d) for d in DEV], "validation": [str(d) for d in VAL],
                        "holdout": [str(d) for d in HOLD]},
            "gates": GATES, "holdout_rule": HOLDOUT_RULE, "threshold_t": round(threshold(reg), 4), "tests": TESTS,
            "after": {"PASSED and VALIDATED": "proposed to the owner as a paper strategy of its own (rule 14), on a "
                                              "10-year Treasury CFD if the broker quotes one, twelve trades a year, "
                                              "sized by the risk engine, followed forward on paper; never real money",
                      "otherwise": "reported as it is; nothing changes"}}


def _dump(x) -> str:
    return json.dumps(x, indent=1, sort_keys=True, default=str) + "\n"


def _write(name: str, body: dict) -> dict:
    body = json.loads(json.dumps(body, sort_keys=True, default=str))
    body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(_dump(body))
    return body


# ── the calendar ─────────────────────────────────────────────────────────

def trading_days(y: int, m: int) -> list[date]:
    """The NYSE's trading days in a month, by its rules and its known unscheduled closures."""
    d, out = date(y, m, 1), []
    while d.month == m:
        if d.weekday() < 5 and d not in nyse_holidays(y) and d not in UNSCHEDULED:
            out.append(d)
        d += timedelta(days=1)
    return out


def month_ends(start: date, end: date) -> list[tuple[date, date]]:
    """For each month in [start, end): (the close the hold opens at, the month's last trading day)."""
    out, y, m = [], start.year, start.month
    while date(y, m, 1) < end:
        days = trading_days(y, m)
        out.append((days[-1 - HOLD_DAYS], days[-1]))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


# ── the data ─────────────────────────────────────────────────────────────

def _yahoo(sym: str, keep_any_finite: bool) -> list[tuple[str, float]]:
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?period1=725846400"
           f"&period2={int(_time.time())}&interval=1d&events=div%7Csplit")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        res = json.loads(r.read())["chart"]["result"][0]
    tz = ZoneInfo(res["meta"]["exchangeTimezoneName"])
    adj = ((res["indicators"].get("adjclose") or [{}])[0] or {}).get("adjclose")
    closes = adj if adj and not keep_any_finite else res["indicators"]["quote"][0]["close"]
    rows = {}
    for t, c in zip(res["timestamp"], closes):
        if c is not None and math.isfinite(c) and (keep_any_finite or c > 0):
            rows[datetime.fromtimestamp(t, timezone.utc).astimezone(tz).date().isoformat()] = float(c)
    return sorted(rows.items())


def cmd_fetch() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    man = {}
    for sym in (BOND, RATE):
        rows = _yahoo(sym, keep_any_finite=sym == RATE)
        body = "date,close\n" + "".join(f"{d},{v!r}\n" for d, v in rows)
        name = sym.lstrip("^")
        (DATA / f"{name}.csv").write_text(body)
        man[sym] = {"file": f"{name}.csv", "rows": len(rows), "first": rows[0][0], "last": rows[-1][0],
                    "sha256": hashlib.sha256(body.encode()).hexdigest()}
        print(sym, man[sym]["first"], man[sym]["last"], man[sym]["rows"])
    (DATA / "manifest.json").write_text(_dump({"retrieved": datetime.now(timezone.utc).isoformat(), "series": man}))


def load(until: date) -> dict[str, dict[date, float]]:
    """Each series before `until`, only if its file matches the manifest: the judge never reads the holdout."""
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

def known_rate(rate: dict, rate_days: list, d: date) -> float | None:
    i = bisect_right(rate_days, d) - 1
    if i < 0 or d - rate_days[i] > timedelta(days=RATE_STALE_DAYS):
        return None
    return rate[rate_days[i]]


def hold(data: dict, rate_days: list, a: date, b: date, cost_x: float = 1.0) -> float | None:
    """Long from the close of a to the close of b, net; None if a close or the financing is unknown."""
    px = data[BOND]
    y = known_rate(data[RATE], rate_days, a)
    if y is None or a not in px or b not in px:
        return None
    nights = (b - a).days
    return px[b] / px[a] - 1.0 - cost_x * (2 * COST_SIDE + MARKUP_PA * nights / 365.0) - y / 100.0 * nights / 365.0


def book(data: dict, start: date, end: date, cost_x: float = 1.0) -> tuple[list[dict], list[str]]:
    """Each month-end in [start, end) held, net; and the months left out."""
    px, rate_days = data[BOND], sorted(data[RATE])
    rows, skipped = [], []
    for a, b in month_ends(start, end):
        if b >= end:
            continue
        window = [d for d in trading_days(b.year, b.month) if d >= a]
        v = hold(data, rate_days, a, b, cost_x) if all(d in px for d in window) else None
        if v is None:
            skipped.append(str(b))
        else:
            rows.append({"month_end": b, "net": v})
    return rows, skipped


def control(data: dict, start: date, end: date) -> list[float]:
    """Every other run of three trading days in [start, end), back to back, held the same way: the month-ends'
    windows are left out."""
    days, rate_days = [d for d in sorted(data[BOND]) if start <= d < end], sorted(data[RATE])
    blocked = set()
    for a, b in month_ends(start, end):
        blocked |= {d for d in days if a < d <= b}
    out, i = [], 0
    while i + HOLD_DAYS < len(days):
        a, run = days[i], days[i + 1:i + 1 + HOLD_DAYS]
        if any(d in blocked for d in run):
            i += 1
            continue
        v = hold(data, rate_days, a, run[-1])
        if v is not None:
            out.append(v)
        i += HOLD_DAYS
    return out


def stats(xs: list[float]) -> dict:
    n = len(xs)
    if n < 2:
        return {"n": n, "mean": xs[0] if xs else None, "t": None}
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    return {"n": n, "mean": m, "t": m / (sd / math.sqrt(n)) if sd > 0 else None, "sd": sd}


def gates(data: dict, thr: float) -> dict:
    rows, skipped = book(data, *JUDGE)
    x = [r["net"] for r in rows]
    s = stats(x)
    dev = stats([r["net"] for r in rows if r["month_end"] < VAL[0]])
    val = stats([r["net"] for r in rows if r["month_end"] >= VAL[0]])
    x2 = stats([r["net"] for r in book(data, *JUDGE, cost_x=2.0)[0]])
    by_year: dict = {}
    for r in rows:
        by_year[r["month_end"].year] = by_year.get(r["month_end"].year, 0.0) + r["net"]
    total = sum(x)
    top = max(by_year.values()) / total if total > 0 and by_year else None
    ok = {"t": s["t"] is not None and s["t"] >= thr,
          "development": (dev["mean"] or 0) > 0, "validation": (val["mean"] or 0) > 0,
          "costs_x2": (x2["mean"] or 0) > 0, "top_year": top is not None and top <= 0.5}
    return {"month_ends": s, "development": dev, "validation": val, "costs_x2": x2,
            "control": stats(control(data, *JUDGE)),
            "hit_rate": sum(1 for v in x if v > 0) / len(x) if x else None,
            "by_year": {str(k): round(v, 5) for k, v in sorted(by_year.items())},
            "top_year_share": None if top is None else round(top, 3), "skipped": skipped,
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
    reg.register(Trial(id=PID, registered=now, title="TME-1: the Treasury month-end effect",
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
    res = gates(load(JUDGE[1]), frozen["spec"]["threshold_t"])
    body = _write(PID, {"program": PID, "verdict": "PASSED" if res["passed"] else "FAILED", **res,
                        "periods": frozen["spec"]["periods"], "spec_sha256": frozen["sha256"],
                        "code_sha256": frozen["code_sha256"], "data": json.loads((DATA / "manifest.json").read_text())})
    reg.record_verdict(Verdict(PID, now, body["verdict"], {"artifact": f"research/knowledge/{PID}.json",
                                                           "artifact_sha256": body["sha256"]}))
    print(body["verdict"], "failed:", res["failed_gates"], "month-ends", json.dumps(res["month_ends"]), "control",
          json.dumps(res["control"]))


def cmd_holdout(now: datetime) -> None:
    reg = _registry()
    frozen = _check_frozen(reg)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    if judged["verdict"] != "PASSED":
        raise SystemExit("TME-1 did not pass: the holdout stays unread")
    if any(t.id == HID for t in reg.trials):
        raise SystemExit("the holdout was opened once already")
    reg.register(Trial(id=HID, registered=now, title="TME-1 holdout: 2019-01..2026-09", hypothesis=HOLDOUT_RULE,
                       uses=(Use(UNIVERSE, HOLD[0], HOLD[1], "judge"),), tests=1, configurations=1,
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"]}))
    data = load(HOLD[1])
    s = stats([r["net"] for r in book(data, *HOLD)[0]])
    s2 = stats([r["net"] for r in book(data, *HOLD, cost_x=2.0)[0]])
    ok = bool(s["mean"] and s["mean"] > 0 and s["t"] is not None and s["t"] >= 1.6448536269514722
              and (s2["mean"] or 0) > 0)
    verdict = "PASSED" if ok else "FAILED"
    body = _write(HID, {"program": HID, "holdout_of": PID, "period": [str(d) for d in HOLD], "month_ends": s,
                        "costs_x2": s2, "control": stats(control(data, *HOLD)), "rule": HOLDOUT_RULE,
                        "classification": "VALIDATED" if ok else "REJECTED", "verdict": verdict})
    reg.record_verdict(Verdict(HID, now, verdict, {"artifact": f"research/knowledge/{HID}.json",
                                                   "artifact_sha256": body["sha256"]}))
    print(verdict, json.dumps(s), "x2", s2["mean"])


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc)  # the command line's clock: every function above takes its dates as arguments
    {"spec": cmd_spec, "preregister": lambda: cmd_preregister(now), "fetch": cmd_fetch,
     "judge": lambda: cmd_judge(now), "holdout": lambda: cmd_holdout(now)}.get(cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
