"""RBL-1: the month-end rebalancing reversal in the S&P 500 (research/preregistrations/RBL-1.md).

The owner, 2026-11-05: "never stop; keep going until something comes out". Harvey, Mazzoleni & Melone (2025, "The
Unintended Consequences of Rebalancing") found that pension and balanced funds that hold stocks and bonds at fixed
weights trade predictably at month-end: when stocks have beaten bonds since the last rebalance, the funds are
overweight stocks and sell them, and equity returns fall by about 16-17 basis points the next day; when bonds have
beaten stocks, the opposite. They measure it with a 60/40 portfolio rebalanced at each month-end, whose predictability
concentrates in the last week of the month. RBL-1 asks whether that pays on the S&P 500 alone, held as a retail CFD
holds the US 500.

The rule, fixed before any RBL-1 price was fetched:
- the month's last trading day T and the four before it are computed from the NYSE's rules and its known unscheduled
  closures (scripts/phd1.py); T+1 is the next month's first trading day;
- the signal at the close of T-4: a 60/40 portfolio of the S&P 500 (SPY) and the 10-year Treasury (IEF), rebalanced at
  the previous month's last close, has drifted to an equity weight w; the signal is w - 60%;
- from the close of T-4 to the close of T+1 (five trading days), short the S&P 500 if the signal is positive (stocks
  overweight, so the funds sell them) and long if it is negative; no trade if it is exactly zero;
- 0.02% a side; a long pays the T-bill yield (the one last published, at most 7 days old) plus 2.5% a year for each
  night, a short is paid the T-bill yield minus 2.5% a year; a month whose closes or financing are unknown is no trade.

    python scripts/rbl1.py spec          # freeze the design (reads no data)
    python scripts/rbl1.py preregister   # register RBL-1 in research/registry.jsonl
    python scripts/rbl1.py fetch         # Yahoo daily closes (on GitHub's runner: Yahoo is blocked here)
    python scripts/rbl1.py judge         # 2003..2018: development, validation, the gates
    python scripts/rbl1.py holdout       # only if RBL-1 PASSED: 2019-01..2026-09, once

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
PID, HID = "RBL-1", "RBL-1-H"
DOC = "research/preregistrations/RBL-1.md"
SPEC = R / "specs" / "RBL-1.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "rbl"
CODE = ("scripts/rbl1.py", "scripts/phd1.py")
UNIVERSE = "us-equity-etf"
#: every earlier test on S&P 500, US equity or US Treasury data counts against this one's threshold
COUNTED_UNIVERSES = ("multi-asset-etf", "multi-asset-long", "equity-index-b", "us-vol-etp", "us-equity-etf",
                     "us-treasury-daily")
MARKET, BOND, RATE = "SPY", "IEF", "^IRX"
DEV = (date(2003, 1, 1), date(2011, 1, 1))
VAL = (date(2011, 1, 1), date(2019, 1, 1))
JUDGE = (DEV[0], VAL[1])
HOLD = (date(2019, 1, 1), date(2026, 10, 1))
EQUITY_TARGET = 0.6
LAST_WEEK = 4          # the hold opens at the close of T-4
COST_SIDE = 0.0002
MARKUP_PA = 0.025
RATE_STALE_DAYS = 7
TESTS = 1
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader RBL-1)"}

GATES = {
    "t": "t of the mean net return per month, holds closing in 2003..2018, >= the threshold",
    "development": "mean net per month > 0, holds closing in 2003..2010",
    "validation": "mean net per month > 0, holds closing in 2011..2018",
    "costs_x2": "mean net per month > 0 with the cost per side and the markup doubled",
    "both_signs": "the months it shorts and the months it holds long each have a mean net > 0",
    "top_year": "no calendar year supplies more than 50% of the total",
}
HOLDOUT_RULE = ("holds closing in 2019-01..2026-09: mean net per month > 0 with one-sided t >= 1.645, and > 0 with "
                "the costs doubled")


def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()


def threshold(reg: Registry) -> float:
    earlier = sum(reg.tests_on(u, date.min, date.max) for u in COUNTED_UNIVERSES)
    return max(3.0, bonferroni_t(earlier + TESTS))


def spec(reg: Registry) -> dict:
    return {"program": PID, "question": "does trading the S&P 500 against the month-end rebalancing of 60/40 funds, "
                                        "from the close of the month's fifth-last trading day to the close of the "
                                        "next month's first, earn a positive net return at a CFD's costs?",
            "market": MARKET, "bond": BOND, "rate": RATE, "equity_target": EQUITY_TARGET,
            "opens_at": f"the close of T-{LAST_WEEK}", "closes_at": "the close of T+1",
            "cost_each_side": COST_SIDE, "markup_pa": MARKUP_PA, "rate_stale_days": RATE_STALE_DAYS,
            "calendar": "NYSE trading days computed from its rules and its unscheduled closures (scripts/phd1.py)",
            "signal": "the equity weight of a 60/40 SPY/IEF portfolio rebalanced at the previous month's last close, "
                      "drifted to the close of T-4, minus 60%; short when positive, long when negative",
            "data": "Yahoo daily closes: SPY and IEF adjusted for dividends and splits, ^IRX as published (negative "
                    "and zero yields kept); each file's sha256 in the manifest",
            "periods": {"development": [str(d) for d in DEV], "validation": [str(d) for d in VAL],
                        "holdout": [str(d) for d in HOLD],
                        "membership": "a month belongs to the period its hold closes in"},
            "gates": GATES, "holdout_rule": HOLDOUT_RULE, "threshold_t": round(threshold(reg), 4), "tests": TESTS,
            "after": {"PASSED and VALIDATED": "proposed to the owner as a paper strategy of its own (rule 14), on the "
                                              "US 500 CFD, twelve trades a year, sized by the risk engine, followed "
                                              "forward on paper; never real money",
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


def months(start: date, end: date) -> list[dict]:
    """For each month in [start, end): the previous month's last trading day (the rebalance), T-4, T and T+1."""
    out, y, m = [], start.year, start.month
    while date(y, m, 1) < end:
        py, pm = (y - 1, 12) if m == 1 else (y, m - 1)
        ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
        days = trading_days(y, m)
        out.append({"rebalance": trading_days(py, pm)[-1], "open": days[-1 - LAST_WEEK], "month_end": days[-1],
                    "close": trading_days(ny, nm)[0]})
        y, m = ny, nm
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
    for sym in (MARKET, BOND, RATE):
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


def signal(data: dict, rebalance: date, at: date) -> float | None:
    """The 60/40 portfolio's equity weight at the close of `at`, rebalanced at the close of `rebalance`, minus 60%."""
    sp, bd = data[MARKET], data[BOND]
    if any(d not in s for d in (rebalance, at) for s in (sp, bd)):
        return None
    e = EQUITY_TARGET * sp[at] / sp[rebalance]
    b = (1 - EQUITY_TARGET) * bd[at] / bd[rebalance]
    return e / (e + b) - EQUITY_TARGET


def book(data: dict, start: date, end: date, cost_x: float = 1.0) -> tuple[list[dict], list[str]]:
    """Each month whose hold closes in [start, end), net; and the months left out. A month belongs to the period its
    hold closes in, so no month falls between two periods and none is counted twice."""
    sp, rate_days = data[MARKET], sorted(data[RATE])
    rows, skipped = [], []
    first = date(start.year - (start.month == 1), (start.month - 2) % 12 + 1, 1)  # the month before `start`'s
    for mo in months(first, end):
        a, b = mo["open"], mo["close"]
        if not start <= b < end:
            continue
        s = signal(data, mo["rebalance"], a)
        y = known_rate(data[RATE], rate_days, a)
        window = [d for d in trading_days(a.year, a.month) if d >= a] + [b]
        if s is None or y is None or any(d not in sp for d in window):
            skipped.append(str(mo["month_end"]))
            continue
        if s == 0:
            continue
        side = -1 if s > 0 else 1
        nights = (b - a).days
        fin = (y / 100.0 + side * cost_x * MARKUP_PA) * nights / 365.0
        net = side * (sp[b] / sp[a] - 1.0) - cost_x * 2 * COST_SIDE - side * fin
        rows.append({"month_end": mo["month_end"], "close": b, "signal": s, "side": side, "net": net})
    return rows, skipped


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
    dev = stats([r["net"] for r in rows if r["close"] < VAL[0]])
    val = stats([r["net"] for r in rows if r["close"] >= VAL[0]])
    x2 = stats([r["net"] for r in book(data, *JUDGE, cost_x=2.0)[0]])
    shorts = stats([r["net"] for r in rows if r["side"] < 0])
    longs = stats([r["net"] for r in rows if r["side"] > 0])
    by_year: dict = {}
    for r in rows:
        by_year[r["close"].year] = by_year.get(r["close"].year, 0.0) + r["net"]
    total = sum(x)
    top = max(by_year.values()) / total if total > 0 and by_year else None
    ok = {"t": s["t"] is not None and s["t"] >= thr,
          "development": (dev["mean"] or 0) > 0, "validation": (val["mean"] or 0) > 0,
          "costs_x2": (x2["mean"] or 0) > 0, "both_signs": (shorts["mean"] or 0) > 0 and (longs["mean"] or 0) > 0,
          "top_year": top is not None and top <= 0.5}
    return {"months": s, "development": dev, "validation": val, "costs_x2": x2, "short_months": shorts,
            "long_months": longs, "hit_rate": sum(1 for v in x if v > 0) / len(x) if x else None,
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
    reg.register(Trial(id=PID, registered=now, title="RBL-1: the month-end rebalancing reversal in the S&P 500",
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
    print(body["verdict"], "failed:", res["failed_gates"], "months", json.dumps(res["months"]), "shorts",
          json.dumps(res["short_months"]), "longs", json.dumps(res["long_months"]))


def cmd_holdout(now: datetime) -> None:
    reg = _registry()
    frozen = _check_frozen(reg)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    if judged["verdict"] != "PASSED":
        raise SystemExit("RBL-1 did not pass: the holdout stays unread")
    if any(t.id == HID for t in reg.trials):
        raise SystemExit("the holdout was opened once already")
    reg.register(Trial(id=HID, registered=now, title="RBL-1 holdout: 2019-01..2026-09", hypothesis=HOLDOUT_RULE,
                       uses=(Use(UNIVERSE, HOLD[0], HOLD[1], "judge"),), tests=1, configurations=1,
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"]}))
    data = load(HOLD[1])
    rows, _ = book(data, *HOLD)
    s = stats([r["net"] for r in rows])
    s2 = stats([r["net"] for r in book(data, *HOLD, cost_x=2.0)[0]])
    ok = bool(s["mean"] and s["mean"] > 0 and s["t"] is not None and s["t"] >= 1.6448536269514722
              and (s2["mean"] or 0) > 0)
    verdict = "PASSED" if ok else "FAILED"
    body = _write(HID, {"program": HID, "holdout_of": PID, "period": [str(d) for d in HOLD], "months": s,
                        "costs_x2": s2, "short_months": stats([r["net"] for r in rows if r["side"] < 0]),
                        "long_months": stats([r["net"] for r in rows if r["side"] > 0]), "rule": HOLDOUT_RULE,
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
