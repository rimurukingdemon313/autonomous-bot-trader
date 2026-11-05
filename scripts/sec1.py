"""SEC-1: US sector momentum, monthly (research/preregistrations/SEC-1.md).

The owner, 2026-11-05: "don't fixate on the AI trading; anything that makes us a profit; never stop". Moskowitz &
Grinblatt (1999, "Do Industries Explain Momentum?", Journal of Finance) found that industries that rose most over
the past six months kept beating the others over the next month, and that much of stock momentum is industry
momentum. Sector funds made it tradable. SEC-1 asks whether it held after its publication, across the nine sectors of
the S&P 500 that have had a fund since 1998, at a retail trader's costs.

The rule, fixed before any SEC-1 data was fetched:
- at each month's last close, rank the nine Select Sector SPDR funds (XLB, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLY) by
  their total return over the six months to that close (dividends in), ties by name;
- the book holds the top three, equally weighted, for the next month; the benchmark holds all nine, equally weighted;
- each month both are traded back to their weights, the month's drift included, paying 0.05% of the notional traded;
- a fund without its closes for the month or the six before is no trade that month, for the book and the benchmark;
- the question: the monthly difference, the book's net minus the benchmark's.

    python scripts/sec1.py spec          # freeze the design (reads no data)
    python scripts/sec1.py preregister   # register SEC-1 in research/registry.jsonl
    python scripts/sec1.py fetch         # Yahoo daily closes (on GitHub's runner: Yahoo is blocked here)
    python scripts/sec1.py judge         # 2000..2017: development, validation, the gates
    python scripts/sec1.py holdout       # only if SEC-1 PASSED: 2018-01..2026-09, once

Each command refuses to run if the code or the spec changed since registration. Nothing here changes the bot.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402

R = ROOT / "research"
PID, HID = "SEC-1", "SEC-1-H"
DOC = "research/preregistrations/SEC-1.md"
SPEC = R / "specs" / "SEC-1.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "sec"
CODE = ("scripts/sec1.py",)
UNIVERSE = "us-equity-etf"
#: every earlier test on S&P 500 or US equity-index data counts against this one's threshold
EQUITY_UNIVERSES = ("multi-asset-etf", "multi-asset-long", "equity-index-b", "us-vol-etp", UNIVERSE)
SECTORS = ("XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY")
DEV = (date(2000, 1, 1), date(2009, 1, 1))
VAL = (date(2009, 1, 1), date(2018, 1, 1))
JUDGE = (DEV[0], VAL[1])
HOLD = (date(2018, 1, 1), date(2026, 10, 1))
FORMATION, HELD = 6, 3
COST = 0.0005          # per unit of notional traded
TESTS = 1              # the monthly difference's t (G1)
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader SEC-1)"}

GATES = {
    "t": "t of the mean monthly difference (book net minus benchmark net), 2000..2017, >= the threshold",
    "development": "mean monthly difference > 0 in 2000..2008",
    "validation": "mean monthly difference > 0 in 2009..2017",
    "costs_x2": "mean monthly difference > 0 with the cost doubled",
    "top_year": "no calendar year supplies more than 50% of the total difference",
}
HOLDOUT_RULE = ("2018-01..2026-09: mean monthly difference > 0 with one-sided t >= 1.645, and > 0 with the cost "
                "doubled")


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
    return {"program": PID, "question": "do the three US sectors that rose most over six months beat all nine over the "
                                        "next month, after costs?",
            "sectors": SECTORS, "formation_months": FORMATION, "held": HELD, "cost_per_unit_traded": COST,
            "rule": "at each month's last close, the top three sector funds by six-month total return (ties by "
                    "name), equally weighted, held for the month; the benchmark holds all nine equally; both traded "
                    "back to their weights monthly",
            "data": "Yahoo daily closes adjusted for dividends and splits; each file's sha256 in the manifest; a "
                    "fund without the closes a month needs is no trade that month for both books",
            "periods": {"development": [str(d) for d in DEV], "validation": [str(d) for d in VAL],
                        "holdout": [str(d) for d in HOLD]},
            "gates": GATES, "holdout_rule": HOLDOUT_RULE, "threshold_t": round(threshold(reg), 4), "tests": TESTS,
            "after": {"PASSED and VALIDATED": "proposed to the owner as a paper strategy of its own (rule 14), sized "
                                              "by the risk engine, followed forward on paper; never real money",
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
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1=912470400"
           f"&period2={int(datetime.now(timezone.utc).timestamp())}&interval=1d&events=div%7Csplit")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        res = json.loads(r.read())["chart"]["result"][0]
    tz = ZoneInfo(res["meta"]["exchangeTimezoneName"])
    adj = ((res["indicators"].get("adjclose") or [{}])[0] or {}).get("adjclose")
    closes = adj if adj else res["indicators"]["quote"][0]["close"]
    rows = {}
    for t, c in zip(res["timestamp"], closes):
        if c is not None and math.isfinite(c) and c > 0:
            rows[datetime.fromtimestamp(t, timezone.utc).astimezone(tz).date().isoformat()] = float(c)
    return sorted(rows.items())


def cmd_fetch() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    man = {}
    for sym in SECTORS:
        rows = _yahoo(sym)
        body = "date,close\n" + "".join(f"{d},{v!r}\n" for d, v in rows)
        (DATA / f"{sym}.csv").write_text(body)
        man[sym] = {"file": f"{sym}.csv", "rows": len(rows), "first": rows[0][0], "last": rows[-1][0],
                    "sha256": hashlib.sha256(body.encode()).hexdigest()}
        print(sym, man[sym]["first"], man[sym]["last"], man[sym]["rows"])
    (DATA / "manifest.json").write_text(_dump({"retrieved": datetime.now(timezone.utc).isoformat(), "series": man}))


def load(until: date) -> dict[str, dict[date, float]]:
    """Each fund's closes before `until`, only if its file matches the manifest: the judge never reads the holdout."""
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

def month_ends(data: dict) -> list[date]:
    """The market's month-end trading days: the last day of each month on which any fund closed. The data's own last
    day counts when no weekday of its month follows it (a judge's data ends at its period's last close)."""
    days = sorted(set().union(*(set(v) for v in data.values())))
    ends = [a for a, b in zip(days, days[1:]) if (a.year, a.month) != (b.year, b.month)]
    if days:
        nxt = days[-1] + timedelta(days=1)
        while nxt.month == days[-1].month and nxt.weekday() >= 5:
            nxt += timedelta(days=1)
        if nxt.month != days[-1].month:
            ends.append(days[-1])
    return ends


def book(data: dict, start: date, end: date, cost: float = COST) -> list[dict]:
    """Per month whose holding starts in [start, end): the book's and the benchmark's gross and net, and the funds
    held. The ranking reads only the closes up to the month-end it is made at."""
    ends = month_ends(data)
    out: list[dict] = []
    drift: dict[str, dict] = {"book": {}, "bench": {}}
    for k in range(FORMATION, len(ends) - 1):
        e0, e1, past = ends[k], ends[k + 1], ends[k - FORMATION]
        month = date(e1.year, e1.month, 1)
        if not (start <= month < end):
            continue
        if any(data[s].get(d) is None for s in SECTORS for d in (past, e0, e1)):
            drift = {"book": {}, "bench": {}}  # no trade: the next month starts from flat and pays to enter
            continue
        ranked = sorted(SECTORS, key=lambda s: (-(data[s][e0] / data[s][past]), s))
        held = ranked[:HELD]
        rets = {s: data[s][e1] / data[s][e0] - 1.0 for s in SECTORS}
        row: dict = {"month": month, "held": held}
        for name, members in (("book", held), ("bench", list(SECTORS))):
            target = {s: 1.0 / len(members) for s in members}
            traded = sum(abs(target.get(s, 0.0) - drift[name].get(s, 0.0)) for s in set(target) | set(drift[name]))
            gross = sum(w * rets[s] for s, w in target.items())
            row[name] = {"gross": gross, "net": gross - cost * traded}
            drift[name] = {s: w * (1 + rets[s]) / (1 + gross) for s, w in target.items()} if gross > -1 else {}
        out.append(row)
    return out


def monthly(xs: list[float]) -> dict:
    n = len(xs)
    if n < 2:
        return {"n": n, "mean": xs[0] if xs else None, "t": None}
    m = sum(xs) / n
    sd = math.sqrt(sum((v - m) ** 2 for v in xs) / (n - 1))
    return {"n": n, "mean": m, "t": m / (sd / math.sqrt(n)) if sd > 0 else None, "sd": sd, "annual": m * 12,
            "annual_sharpe": m / sd * math.sqrt(12) if sd > 0 else None}


def drawdown(xs: list[float]) -> float:
    eq = peak = 1.0
    worst = 0.0
    for v in xs:
        eq *= 1 + v
        peak = max(peak, eq)
        worst = min(worst, eq / peak - 1)
    return worst


def gates(data: dict, thr: float) -> dict:
    rows = book(data, *JUDGE)
    diff = {r["month"]: r["book"]["net"] - r["bench"]["net"] for r in rows}
    s = monthly(list(diff.values()))
    dev = monthly([v for m, v in diff.items() if m < VAL[0]])
    val = monthly([v for m, v in diff.items() if m >= VAL[0]])
    x2 = monthly([r["book"]["net"] - r["bench"]["net"] for r in book(data, *JUDGE, cost=2 * COST)])
    by_year: dict = {}
    for m, v in diff.items():
        by_year[m.year] = by_year.get(m.year, 0.0) + v
    total = sum(diff.values())
    top = max(by_year.values()) / total if total > 0 and by_year else None
    ok = {"t": s["t"] is not None and s["t"] >= thr,
          "development": (dev["mean"] or 0) > 0, "validation": (val["mean"] or 0) > 0,
          "costs_x2": (x2["mean"] or 0) > 0, "top_year": top is not None and top <= 0.5}
    held: dict = {}
    for r in rows:
        for f in r["held"]:
            held[f] = held.get(f, 0) + 1
    return {"difference": s, "development": dev, "validation": val, "costs_x2": x2,
            "book_net": monthly([r["book"]["net"] for r in rows]),
            "benchmark_net": monthly([r["bench"]["net"] for r in rows]),
            "book_max_drawdown": round(drawdown([r["book"]["net"] for r in rows]), 4),
            "benchmark_max_drawdown": round(drawdown([r["bench"]["net"] for r in rows]), 4),
            "by_year": {str(k): round(v, 4) for k, v in sorted(by_year.items())},
            "top_year_share": None if top is None else round(top, 3), "months": len(rows),
            "months_held": dict(sorted(held.items(), key=lambda x: (-x[1], x[0]))),
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
    reg.register(Trial(id=PID, registered=now, title="SEC-1: US sector momentum, monthly", hypothesis=s["question"],
                       uses=(Use(UNIVERSE, JUDGE[0], JUDGE[1], "judge"),), tests=TESTS, configurations=TESTS,
                       preregistration=DOC,
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
    print(body["verdict"], "failed:", res["failed_gates"], "difference", json.dumps(res["difference"]), "months",
          res["months"])


def cmd_holdout(now: datetime) -> None:
    reg = _registry()
    frozen = _check_frozen(reg)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    if judged["verdict"] != "PASSED":
        raise SystemExit("SEC-1 did not pass: the holdout stays unread")
    if any(t.id == HID for t in reg.trials):
        raise SystemExit("the holdout was opened once already")
    reg.register(Trial(id=HID, registered=now, title="SEC-1 holdout: 2018-01..2026-09", hypothesis=HOLDOUT_RULE,
                       uses=(Use(UNIVERSE, HOLD[0], HOLD[1], "judge"),), tests=1, configurations=1,
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"]}))
    data = load(HOLD[1])
    rows = book(data, *HOLD)
    s = monthly([r["book"]["net"] - r["bench"]["net"] for r in rows])
    s2 = monthly([r["book"]["net"] - r["bench"]["net"] for r in book(data, *HOLD, cost=2 * COST)])
    ok = bool(s["mean"] and s["mean"] > 0 and s["t"] is not None and s["t"] >= 1.6448536269514722
              and (s2["mean"] or 0) > 0)
    verdict = "PASSED" if ok else "FAILED"
    body = _write(HID, {"program": HID, "holdout_of": PID, "period": [str(d) for d in HOLD], "difference": s,
                        "costs_x2": s2, "rule": HOLDOUT_RULE, "classification": "VALIDATED" if ok else "REJECTED",
                        "verdict": verdict})
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
