"""PHD-1: the pre-holiday effect in the S&P 500 (research/preregistrations/PHD-1.md).

The owner, 2026-11-05: "don't fixate on the AI trading; anything that makes us a profit; never stop". Lakonishok &
Smidt (1988) and Ariel (1990) found that US stocks earned many times their usual daily return on the trading day
before a market holiday. Later studies found it fading in large stocks. PHD-1 asks whether the S&P 500 still pays on
that day, since 1995, after a retail CFD's costs, and more than on an ordinary day.

The rule, fixed before any PHD-1 data was fetched:
- the scheduled NYSE holidays are computed from their published rules (`nyse_holidays`); the event day is the last
  trading day before each one, so a Monday holiday's event is the Friday before it;
- buy the S&P 500 (SPY, dividends in) at the close of the trading day before the event day, and sell at the event
  day's close; each side pays 0.02% (spread and slippage) and each night held pays the T-bill yield (the one last
  published, at most 7 days old) plus 2.5% a year;
- the control: every other trading day, held the same way at the same costs;
- the computed calendar is checked against the data's own trading days before anything is judged: no computed
  holiday may have a close, and every weekday without a close must be a computed holiday or a known unscheduled
  closure (`UNSCHEDULED`), or nothing is judged.

    python scripts/phd1.py spec          # freeze the design (reads no data)
    python scripts/phd1.py preregister   # register PHD-1 in research/registry.jsonl
    python scripts/phd1.py fetch         # Yahoo daily closes (on GitHub's runner: Yahoo is blocked here)
    python scripts/phd1.py judge         # 1995..2021: development, validation, the gates
    python scripts/phd1.py holdout       # only if PHD-1 PASSED: 2022-01..2026-09, once

Each command refuses to run if the code or the spec changed since registration. Nothing here changes the bot.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from bisect import bisect_right
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402
from scripts.volm1 import _yahoo  # noqa: E402

R = ROOT / "research"
PID, HID = "PHD-1", "PHD-1-H"
DOC = "research/preregistrations/PHD-1.md"
SPEC = R / "specs" / "PHD-1.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "phd"
CODE = ("scripts/phd1.py", "scripts/volm1.py")
UNIVERSE = "us-equity-etf"
#: every earlier test on S&P 500 or US equity data counts against this one's threshold
EQUITY_UNIVERSES = ("multi-asset-etf", "multi-asset-long", "equity-index-b", "us-vol-etp", UNIVERSE)
MARKET, RATE = "SPY", "^IRX"
DEV = (date(1995, 1, 1), date(2009, 1, 1))
VAL = (date(2009, 1, 1), date(2022, 1, 1))
JUDGE = (DEV[0], VAL[1])
HOLD = (date(2022, 1, 1), date(2026, 10, 1))
COST_SIDE = 0.0002
MARKUP_PA = 0.025
RATE_STALE_DAYS = 7
TESTS = 2              # the events' mean t (G1) and the events-against-ordinary-days t (G5)
#: the market's closures that were not scheduled holidays: never events, and allowed to have no close
UNSCHEDULED = frozenset(date.fromisoformat(d) for d in (
    "1994-04-27",  # President Nixon's funeral
    "2001-09-11", "2001-09-12", "2001-09-13", "2001-09-14",  # the attacks of 11 September
    "2004-06-11",  # President Reagan's funeral
    "2007-01-02",  # President Ford's funeral
    "2012-10-29", "2012-10-30",  # Hurricane Sandy
    "2018-12-05",  # President G. H. W. Bush's funeral
    "2025-01-09",  # President Carter's funeral
))

GATES = {
    "t": "t of the mean net return on event days, 1995..2021, >= the threshold",
    "development": "mean net per event > 0 in 1995..2008",
    "validation": "mean net per event > 0 in 2009..2021",
    "costs_x2": "mean net per event > 0 with the costs and the markup doubled",
    "beats_ordinary_days": "event days beat every other day held the same way: mean difference > 0, Welch t >= 2.0",
    "top_year": "no calendar year supplies more than 50% of the total net",
}
HOLDOUT_RULE = ("2022-01..2026-09: mean net per event > 0 with one-sided t >= 1.645, > 0 with the costs doubled, and "
                "above the ordinary days' mean")


def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()


def threshold(reg: Registry) -> float:
    earlier = sum(reg.tests_on(u, JUDGE[0], HOLD[1]) for u in EQUITY_UNIVERSES)
    return max(3.0, bonferroni_t(earlier + TESTS))


def spec(reg: Registry) -> dict:
    return {"program": PID, "question": "does the S&P 500 earn a positive net return on the trading day before a "
                                        "market holiday, and more than on an ordinary day, after a CFD's costs?",
            "market": MARKET, "rate": RATE, "cost_each_side": COST_SIDE, "markup_pa": MARKUP_PA,
            "holidays": "NYSE scheduled full-day holidays by their rules: New Year's Day (not observed on a Friday), "
                        "Martin Luther King Jr. Day from 1998, Washington's Birthday, Good Friday, Memorial Day, "
                        "Juneteenth from 2022, Independence Day, Labor Day, Thanksgiving, Christmas; Saturday "
                        "holidays observed on Friday, Sunday ones on Monday",
            "unscheduled": sorted(str(d) for d in UNSCHEDULED),
            "data": "Yahoo daily closes: SPY adjusted for dividends and splits, ^IRX as published; each file's "
                    "sha256 in the manifest; the computed calendar checked against the data's trading days",
            "periods": {"development": [str(d) for d in DEV], "validation": [str(d) for d in VAL],
                        "holdout": [str(d) for d in HOLD]},
            "gates": GATES, "holdout_rule": HOLDOUT_RULE, "threshold_t": round(threshold(reg), 4), "tests": TESTS,
            "after": {"PASSED and VALIDATED": "proposed to the owner as a paper strategy of its own (rule 14), on the "
                                              "US 500 CFD, about nine trades a year, sized by the risk engine, "
                                              "followed forward on paper; never real money",
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

def easter(y: int) -> date:
    """Gregorian Easter Sunday (the anonymous algorithm)."""
    a, b, c = y % 19, y // 100, y % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    month = (h + l_ - 7 * m + 114) // 31
    day = (h + l_ - 7 * m + 114) % 31 + 1
    return date(y, month, day)


def nth_weekday(y: int, month: int, weekday: int, n: int) -> date:
    d = date(y, month, 1)
    d += timedelta(days=(weekday - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)


def last_weekday(y: int, month: int, weekday: int) -> date:
    d = date(y + (month == 12), month % 12 + 1, 1) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() - weekday) % 7)


def observed(d: date) -> date:
    return d - timedelta(days=1) if d.weekday() == 5 else d + timedelta(days=1) if d.weekday() == 6 else d


def nyse_holidays(y: int) -> set[date]:
    """The NYSE's scheduled full-day closures in year y, by the published rules."""
    out = {nth_weekday(y, 2, 0, 3), easter(y) - timedelta(days=2), last_weekday(y, 5, 0),
           observed(date(y, 7, 4)), nth_weekday(y, 9, 0, 1), nth_weekday(y, 11, 3, 4), observed(date(y, 12, 25))}
    ny = date(y, 1, 1)
    if ny.weekday() != 5:  # a Saturday New Year's Day is not observed on the Friday before
        out.add(observed(ny))
    if y >= 1998:
        out.add(nth_weekday(y, 1, 0, 3))
    if y >= 2022:
        out.add(observed(date(y, 6, 19)))
    return out


def calendar_check(days: list[date]) -> list[str]:
    """Where the computed calendar and the data's own trading days disagree (empty when they agree)."""
    have = set(days)
    bad = []
    for y in range(days[0].year, days[-1].year + 1):
        for h in sorted(nyse_holidays(y)):
            if days[0] <= h <= days[-1] and h in have:
                bad.append(f"{h}: a computed holiday with a close")
    d = days[0]
    while d <= days[-1]:
        if d.weekday() < 5 and d not in have and d not in nyse_holidays(d.year) and d not in UNSCHEDULED:
            bad.append(f"{d}: a weekday without a close that is no known closure")
        d += timedelta(days=1)
    return bad


def event_days(days: list[date]) -> set[date]:
    """The last trading day before each scheduled holiday."""
    out = set()
    for y in range(days[0].year, days[-1].year + 2):
        for h in nyse_holidays(y):
            i = bisect_right(days, h - timedelta(days=1)) - 1
            if i >= 1 and (h - days[i]).days <= 4:
                out.add(days[i])
    return out


# ── the data ─────────────────────────────────────────────────────────────

def cmd_fetch() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    man = {}
    for sym in (MARKET, RATE):
        rows = _yahoo(sym, allow_zero=sym == RATE)
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


def days_held(data: dict, start: date, end: date, cost_x: float = 1.0) -> dict[str, dict[date, float]]:
    """Every trading day in [start, end) as a one-day hold from the previous close, net; split into the event days
    and the ordinary days. A day whose financing is unknown is left out of both."""
    px, rate = data[MARKET], data[RATE]
    days, rate_days = sorted(px), sorted(rate)
    events = event_days(days)
    out: dict[str, dict[date, float]] = {"event": {}, "ordinary": {}}
    for p, d in zip(days, days[1:]):
        if not start <= d < end:
            continue
        y = known_rate(rate, rate_days, p)
        if y is None:
            continue
        fin = (y / 100.0 + MARKUP_PA) * (d - p).days / 365.0
        net = px[d] / px[p] - 1.0 - cost_x * (2 * COST_SIDE + fin)
        out["event" if d in events else "ordinary"][d] = net
    return out


def stats(xs: list[float]) -> dict:
    n = len(xs)
    if n < 2:
        return {"n": n, "mean": xs[0] if xs else None, "t": None}
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    return {"n": n, "mean": m, "t": m / (sd / math.sqrt(n)) if sd > 0 else None, "sd": sd}


def welch(a: list[float], b: list[float]) -> dict:
    if len(a) < 2 or len(b) < 2:
        return {"mean": None, "t": None}
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    va = sum((x - ma) ** 2 for x in a) / (len(a) - 1)
    vb = sum((x - mb) ** 2 for x in b) / (len(b) - 1)
    se = math.sqrt(va / len(a) + vb / len(b))
    return {"mean": ma - mb, "t": (ma - mb) / se if se > 0 else None}


def gates(data: dict, thr: float) -> dict:
    held = days_held(data, *JUDGE)
    ev = held["event"]
    x = [ev[d] for d in sorted(ev)]
    s = stats(x)
    dev = stats([v for d, v in sorted(ev.items()) if d < VAL[0]])
    val = stats([v for d, v in sorted(ev.items()) if d >= VAL[0]])
    x2 = stats(list(days_held(data, *JUDGE, cost_x=2.0)["event"].values()))
    vs = welch(x, list(held["ordinary"].values()))
    by_year: dict = {}
    for d, v in ev.items():
        by_year[d.year] = by_year.get(d.year, 0.0) + v
    total = sum(x)
    top = max(by_year.values()) / total if total > 0 and by_year else None
    ok = {"t": s["t"] is not None and s["t"] >= thr,
          "development": (dev["mean"] or 0) > 0, "validation": (val["mean"] or 0) > 0,
          "costs_x2": (x2["mean"] or 0) > 0,
          "beats_ordinary_days": (vs["mean"] or 0) > 0 and vs["t"] is not None and vs["t"] >= 2.0,
          "top_year": top is not None and top <= 0.5}
    return {"events": s, "development": dev, "validation": val, "costs_x2": x2,
            "ordinary_days": stats(list(held["ordinary"].values())), "events_minus_ordinary": vs,
            "hit_rate": sum(1 for v in x if v > 0) / len(x) if x else None,
            "by_year": {str(k): round(v, 5) for k, v in sorted(by_year.items())},
            "top_year_share": None if top is None else round(top, 3),
            "event_days": sorted(str(d) for d in ev),
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


def _calendar_ok(data: dict) -> None:
    bad = calendar_check(sorted(data[MARKET]))
    if bad:
        raise SystemExit(f"the computed calendar and the data disagree ({len(bad)}): {bad[:8]}; nothing is judged")


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
    reg.register(Trial(id=PID, registered=now, title="PHD-1: the pre-holiday effect in the S&P 500",
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
    _calendar_ok(data)
    res = gates(data, frozen["spec"]["threshold_t"])
    body = _write(PID, {"program": PID, "verdict": "PASSED" if res["passed"] else "FAILED", **res,
                        "periods": frozen["spec"]["periods"], "spec_sha256": frozen["sha256"],
                        "code_sha256": frozen["code_sha256"], "data": json.loads((DATA / "manifest.json").read_text())})
    reg.record_verdict(Verdict(PID, now, body["verdict"], {"artifact": f"research/knowledge/{PID}.json",
                                                           "artifact_sha256": body["sha256"]}))
    print(body["verdict"], "failed:", res["failed_gates"], "events", json.dumps(res["events"]), "vs ordinary",
          json.dumps(res["events_minus_ordinary"]))


def cmd_holdout(now: datetime) -> None:
    reg = _registry()
    frozen = _check_frozen(reg)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    if judged["verdict"] != "PASSED":
        raise SystemExit("PHD-1 did not pass: the holdout stays unread")
    if any(t.id == HID for t in reg.trials):
        raise SystemExit("the holdout was opened once already")
    reg.register(Trial(id=HID, registered=now, title="PHD-1 holdout: 2022-01..2026-09", hypothesis=HOLDOUT_RULE,
                       uses=(Use(UNIVERSE, HOLD[0], HOLD[1], "judge"),), tests=1, configurations=1,
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"]}))
    data = load(HOLD[1])
    _calendar_ok(data)
    held = days_held(data, *HOLD)
    x = list(held["event"].values())
    s = stats(x)
    s2 = stats(list(days_held(data, *HOLD, cost_x=2.0)["event"].values()))
    vs = welch(x, list(held["ordinary"].values()))
    ok = bool(s["mean"] and s["mean"] > 0 and s["t"] is not None and s["t"] >= 1.6448536269514722
              and (s2["mean"] or 0) > 0 and (vs["mean"] or 0) > 0)
    verdict = "PASSED" if ok else "FAILED"
    body = _write(HID, {"program": HID, "holdout_of": PID, "period": [str(d) for d in HOLD], "events": s,
                        "costs_x2": s2, "events_minus_ordinary": vs, "rule": HOLDOUT_RULE,
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
