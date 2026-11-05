"""TSY-1: the Treasury auction cycle (research/preregistrations/TSY-1.md).

The owner, 2026-11-05: "don't fixate on the AI trading; anything that makes us a profit; never stop". Lou, Yan & Zhang
(2013) found that Treasury prices fall in the few days before each auction and recover in the days after, although
every auction's date and size are announced in advance: dealers must absorb the new supply, and the investors who will
finally hold it arrive slowly. Their sample ended in 2008. TSY-1 asks whether the cycle around the 10-year note's
auctions still pays since 2009, held as a retail CFD holds the 7-10 year Treasury ETF (IEF).

The rule, fixed before any TSY-1 price was fetched:
- the events: every auction of a 10-year nominal note, new issue or reopening, from the Treasury's own auction records
  (dates, terms and type flags only: no yield, price or amount is read). An auction whose day is not an IEF trading day
  is no trade;
- for an auction on trading day a: short IEF from the close of day a-6 to the close of day a-1 (five days), flat on
  the auction day, and long from the close of day a to the close of day a+5 (five days);
- each leg pays 0.03% a side (spread and slippage). The long leg pays the T-bill yield (the one last published, at
  most 7 days old) plus 2.5% a year for each night; the short leg is paid the T-bill yield minus 2.5% a year;
- an event whose window overlaps the previous traded event's, or whose financing is unknown, is no trade.

    python scripts/tsy1.py spec          # freeze the design (reads no data)
    python scripts/tsy1.py preregister   # register TSY-1 in research/registry.jsonl
    python scripts/tsy1.py fetch         # Yahoo closes and the auction records (on GitHub's runner: blocked here)
    python scripts/tsy1.py judge         # 2009..2020: development, validation, the gates
    python scripts/tsy1.py holdout       # only if TSY-1 PASSED: 2021-01..2026-09, once

Each command refuses to run if the code or the spec changed since registration. Nothing here changes the bot.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
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

R = ROOT / "research"
PID, HID = "TSY-1", "TSY-1-H"
DOC = "research/preregistrations/TSY-1.md"
SPEC = R / "specs" / "TSY-1.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "tsy"
CODE = ("scripts/tsy1.py",)
UNIVERSE = "us-treasury-daily"
#: earlier tests that read Treasury prices or yields: DIV-1 (TLT, IEF), DIV-2 (^TNX, ^FVX) and those sharing their data
TREASURY_UNIVERSES = ("multi-asset-etf", "multi-asset-long", UNIVERSE)
BOND, RATE = "IEF", "^IRX"
DEV = (date(2009, 1, 1), date(2015, 1, 1))
VAL = (date(2015, 1, 1), date(2021, 1, 1))
JUDGE = (DEV[0], VAL[1])
HOLD = (date(2021, 1, 1), date(2026, 10, 1))
PRE, POST = 5, 5
COST_SIDE = 0.0003
MARKUP_PA = 0.025
RATE_STALE_DAYS = 7
TESTS = 1
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader TSY-1)"}
AUCTIONS_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query"
#: the only fields read from an auction record
AUCTION_FIELDS = ("auction_date", "security_type", "security_term", "original_security_term", "reopening",
                  "inflation_index_security", "floating_rate")

GATES = {
    "t": "t of the mean net return per event, 2009..2020, >= the threshold",
    "development": "mean net per event > 0 in 2009..2014",
    "validation": "mean net per event > 0 in 2015..2020",
    "costs_x2": "mean net per event > 0 with the cost per side and the markup doubled",
    "both_legs": "the short leg's mean net > 0 and the long leg's mean net > 0",
    "top_year": "no calendar year supplies more than 50% of the total",
}
HOLDOUT_RULE = "2021-01..2026-09: mean net per event > 0 with one-sided t >= 1.645, and > 0 with the costs doubled"


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
    return {"program": PID, "question": "does shorting the 7-10 year Treasury ETF in the five trading days before each "
                                        "10-year note auction and holding it long in the five after earn a positive "
                                        "net return at a CFD's costs?",
            "bond": BOND, "rate": RATE, "pre_days": PRE, "post_days": POST, "cost_each_side": COST_SIDE,
            "markup_pa": MARKUP_PA, "rate_stale_days": RATE_STALE_DAYS,
            "events": "every auction of a 10-year nominal note (new issue or reopening; not TIPS, not floating), from "
                      "the Treasury's auction records (fiscaldata auctions_query: dates, terms and type flags only)",
            "rule": "short from the close of trading day a-6 to the close of a-1; flat on the auction day a; long "
                    "from the close of a to the close of a+5; an auction off IEF's calendar, an event overlapping the "
                    "previous traded one, or one with unknown financing is no trade",
            "data": "Yahoo daily closes: IEF adjusted for distributions and splits, ^IRX as published (negative and "
                    "zero yields kept); each file's sha256 in the manifest",
            "periods": {"development": [str(d) for d in DEV], "validation": [str(d) for d in VAL],
                        "holdout": [str(d) for d in HOLD]},
            "gates": GATES, "holdout_rule": HOLDOUT_RULE, "threshold_t": round(threshold(reg), 4), "tests": TESTS,
            "after": {"PASSED and VALIDATED": "proposed to the owner as a paper strategy of its own (rule 14), on a "
                                              "10-year Treasury CFD if the broker quotes one, about twelve events a "
                                              "year, sized by the risk engine, followed forward on paper; never real "
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


# ── the events ───────────────────────────────────────────────────────────

def is_ten_year_note(r: dict) -> bool:
    """A 10-year nominal note: sold as a 10-year, or reopened as a 9-year and some months; never TIPS or floating."""
    if r.get("security_type") != "Note" or r.get("inflation_index_security") == "Yes" or r.get("floating_rate") == "Yes":
        return False
    term, orig = r.get("security_term") or "", r.get("original_security_term") or ""
    return term == "10-Year" or orig == "10-Year" or bool(re.fullmatch(r"9-Year \d{1,2}-Month", term))


def auction_days(records: list[dict]) -> list[date]:
    return sorted({date.fromisoformat(r["auction_date"][:10]) for r in records if is_ten_year_note(r)})


def events(days: list[date], auctions: list[date]) -> tuple[list[int], dict[str, list[str]]]:
    """The index (in `days`) of each traded auction day, and each auction left out, by reason. An event needs PRE+1
    closes before its auction day and POST after it."""
    pos = {d: i for i, d in enumerate(days)}
    out: list[int] = []
    skipped: dict[str, list[str]] = {"off_calendar": [], "no_window": [], "overlap": []}
    for d in auctions:
        a = pos.get(d)
        if a is None:
            skipped["off_calendar"].append(str(d))
        elif a - PRE - 1 < 0 or a + POST >= len(days):
            skipped["no_window"].append(str(d))
        elif out and a - PRE - 1 < out[-1] + POST:
            skipped["overlap"].append(str(d))
        else:
            out.append(a)
    return out, skipped


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


def _auctions() -> list[dict]:
    q = {"fields": ",".join(AUCTION_FIELDS), "filter": "security_type:eq:Note,auction_date:gte:2002-01-01",
         "sort": "auction_date", "page[size]": "10000"}
    with urllib.request.urlopen(urllib.request.Request(AUCTIONS_URL + "?" + urllib.parse.urlencode(q), headers=UA),
                                timeout=120) as r:
        data = json.loads(r.read())
    if int(data["meta"]["total-count"]) != len(data["data"]):
        raise SystemExit("the auction records came back in more than one page")
    return [{k: (row.get(k) or "") for k in AUCTION_FIELDS} for row in data["data"]]


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
    recs = _auctions()
    body = ",".join(AUCTION_FIELDS) + "\n" + "".join(",".join(r[k].replace(",", " ") for k in AUCTION_FIELDS) + "\n"
                                                    for r in recs)
    (DATA / "auctions.csv").write_text(body)
    ten = auction_days(recs)
    man["auctions"] = {"file": "auctions.csv", "rows": len(recs), "ten_year": len(ten), "first": str(ten[0]),
                       "last": str(ten[-1]), "sha256": hashlib.sha256(body.encode()).hexdigest()}
    print("auctions", len(recs), "ten-year", len(ten), ten[0], ten[-1])
    (DATA / "manifest.json").write_text(_dump({"retrieved": datetime.now(timezone.utc).isoformat(), "series": man}))


def _read(m: dict) -> str:
    body = (DATA / m["file"]).read_text()
    if hashlib.sha256(body.encode()).hexdigest() != m["sha256"]:
        raise SystemExit(f"{m['file']} does not match its manifest: nothing is judged on it")
    return body


def load(until: date) -> dict:
    """Each price series before `until` and the auction days before it, only if every file matches the manifest:
    the judge never reads the holdout."""
    man = json.loads((DATA / "manifest.json").read_text())["series"]
    out: dict = {}
    for sym in (BOND, RATE):
        rows = [ln.split(",") for ln in _read(man[sym]).strip().splitlines()[1:]]
        out[sym] = {date.fromisoformat(d): float(c) for d, c in rows if date.fromisoformat(d) < until}
    lines = _read(man["auctions"]).strip().splitlines()
    head = lines[0].split(",")
    recs = [dict(zip(head, ln.split(","))) for ln in lines[1:]]
    out["auctions"] = [d for d in auction_days(recs) if d < until]
    return out


# ── the rule, and what it earned ─────────────────────────────────────────

def known_rate(rate: dict, rate_days: list, d: date) -> float | None:
    i = bisect_right(rate_days, d) - 1
    if i < 0 or d - rate_days[i] > timedelta(days=RATE_STALE_DAYS):
        return None
    return rate[rate_days[i]]


def book(data: dict, start: date, end: date, cost_x: float = 1.0) -> tuple[list[dict], dict]:
    """Every traded event whose auction day is in [start, end) and whose last close is before `end`, with each leg's
    net return; and the auctions left out."""
    px, rate = data[BOND], data[RATE]
    days, rate_days = sorted(px), sorted(rate)
    idx, skipped = events(days, data["auctions"])
    skipped["no_rate"] = []
    rows = []
    for a in idx:
        d = days[a]
        if not start <= d < end or not days[a + POST] < end:
            continue
        s0, s1, l0, l1 = days[a - PRE - 1], days[a - 1], days[a], days[a + POST]
        ys, yl = known_rate(rate, rate_days, s0), known_rate(rate, rate_days, l0)
        if ys is None or yl is None:
            skipped["no_rate"].append(str(d))
            continue
        short_gross = -(px[s1] / px[s0] - 1.0)
        long_gross = px[l1] / px[l0] - 1.0
        short = short_gross - cost_x * 2 * COST_SIDE + (ys / 100.0 - cost_x * MARKUP_PA) * (s1 - s0).days / 365.0
        long = long_gross - cost_x * 2 * COST_SIDE - (yl / 100.0 + cost_x * MARKUP_PA) * (l1 - l0).days / 365.0
        rows.append({"auction": d, "short": short, "long": long, "net": short + long,
                     "short_gross": short_gross, "long_gross": long_gross})
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
    dev = stats([r["net"] for r in rows if r["auction"] < VAL[0]])
    val = stats([r["net"] for r in rows if r["auction"] >= VAL[0]])
    x2 = stats([r["net"] for r in book(data, *JUDGE, cost_x=2.0)[0]])
    short, long = stats([r["short"] for r in rows]), stats([r["long"] for r in rows])
    by_year: dict = {}
    for r in rows:
        by_year[r["auction"].year] = by_year.get(r["auction"].year, 0.0) + r["net"]
    total = sum(x)
    top = max(by_year.values()) / total if total > 0 and by_year else None
    ok = {"t": s["t"] is not None and s["t"] >= thr,
          "development": (dev["mean"] or 0) > 0, "validation": (val["mean"] or 0) > 0,
          "costs_x2": (x2["mean"] or 0) > 0, "both_legs": (short["mean"] or 0) > 0 and (long["mean"] or 0) > 0,
          "top_year": top is not None and top <= 0.5}
    return {"events": s, "development": dev, "validation": val, "costs_x2": x2, "short_leg": short,
            "long_leg": long, "short_leg_gross": stats([r["short_gross"] for r in rows]),
            "long_leg_gross": stats([r["long_gross"] for r in rows]),
            "hit_rate": sum(1 for v in x if v > 0) / len(x) if x else None,
            "by_year": {str(k): round(v, 5) for k, v in sorted(by_year.items())},
            "top_year_share": None if top is None else round(top, 3),
            "auctions_traded": [str(r["auction"]) for r in rows],
            "skipped": {k: [d for d in v if JUDGE[0] <= date.fromisoformat(d) < JUDGE[1]] for k, v in skipped.items()},
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
    reg.register(Trial(id=PID, registered=now, title="TSY-1: the Treasury auction cycle",
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
    print(body["verdict"], "failed:", res["failed_gates"], "events", json.dumps(res["events"]), "short",
          json.dumps(res["short_leg"]), "long", json.dumps(res["long_leg"]))


def cmd_holdout(now: datetime) -> None:
    reg = _registry()
    frozen = _check_frozen(reg)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    if judged["verdict"] != "PASSED":
        raise SystemExit("TSY-1 did not pass: the holdout stays unread")
    if any(t.id == HID for t in reg.trials):
        raise SystemExit("the holdout was opened once already")
    reg.register(Trial(id=HID, registered=now, title="TSY-1 holdout: 2021-01..2026-09", hypothesis=HOLDOUT_RULE,
                       uses=(Use(UNIVERSE, HOLD[0], HOLD[1], "judge"),), tests=1, configurations=1,
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"]}))
    data = load(HOLD[1])
    rows, _ = book(data, *HOLD)
    s = stats([r["net"] for r in rows])
    s2 = stats([r["net"] for r in book(data, *HOLD, cost_x=2.0)[0]])
    ok = bool(s["mean"] and s["mean"] > 0 and s["t"] is not None and s["t"] >= 1.6448536269514722
              and (s2["mean"] or 0) > 0)
    verdict = "PASSED" if ok else "FAILED"
    body = _write(HID, {"program": HID, "holdout_of": PID, "period": [str(d) for d in HOLD], "events": s,
                        "costs_x2": s2, "short_leg": stats([r["short"] for r in rows]),
                        "long_leg": stats([r["long"] for r in rows]), "rule": HOLDOUT_RULE,
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
