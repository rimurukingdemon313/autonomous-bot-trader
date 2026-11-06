"""TRND-1: the long-only 10-month trend filter on stock indices, at a swap-free account's costs
(research/preregistrations/TRND-1.md).

The owner, 2026-11-06: "everything is allowed; test everything; find a way", and "the most important thing is
Islamic". This is not a prediction edge. It is owning a stock index with one exit rule: hold it while its month-end
close is above the mean of its last 10 month-end closes, and hold nothing otherwise (Faber 2007). It never sells
short, uses no leverage and holds nothing that pays interest. In a swap-free (Islamic) account, holding costs only the
spread. The question is whether it earned a positive return, with a smaller worst fall than holding the index all the
time, on data no test here has read: the S&P 500 from 1929 to 1989.

RC-EQ judged the same rule (its E4) on ten index CFDs over 1990-2020, at a CFD's financing costs, and rejected it.
Those years are not used again. The holdout is the broker's four index CFDs from 2021. Those years are not untouched:
DIV-2-H read three of the indices for a different trend rule, and two intraday tests read the US 500's hour bars. No
test has computed this rule on them.

The rule, fixed before any TRND-1 price was fetched:
- at each month-end close, if the close is above the mean of the last 10 month-end closes (this one included), hold
  the index for the next month; otherwise hold nothing for it, and earn nothing;
- each switch in or out pays 0.05% (spread and slippage); there is no financing (swap-free), and no dividend is
  counted (price index only), which understates a long CFD's return;
- a calendar month with no close is never bridged: no decision is taken across it, and the judged years must have all
  732 months.

    python scripts/trnd1.py spec          # freeze the design (reads no data)
    python scripts/trnd1.py preregister   # register TRND-1 in research/registry.jsonl
    python scripts/trnd1.py fetch         # Yahoo daily closes (on GitHub's runner: Yahoo is blocked here)
    python scripts/trnd1.py judge         # the S&P 500, 1929..1989: development, validation, the gates
    python scripts/trnd1.py holdout       # only if TRND-1 PASSED: the four index CFDs, 2021-01..2026-09, once

Each command refuses to run if the code or the spec changed since registration. Nothing here changes the bot.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402

R = ROOT / "research"
PID, HID = "TRND-1", "TRND-1-H"
DOC = "research/preregistrations/TRND-1.md"
SPEC = R / "specs" / "TRND-1.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "trnd"
CODE = ("scripts/trnd1.py",)
UNIVERSE = "equity-index-monthly"
#: every earlier test on stock-index or US equity data counts against this one's threshold, intraday ones included
COUNTED_UNIVERSES = ("multi-asset-etf", "multi-asset-long", "equity-index-b", "equity-index-forward",
                     "index-cfd-intraday", "us-equity-etf", "us-vol-etp", UNIVERSE)
JUDGED_INDEX = "^GSPC"
HOLDOUT_INDICES = ("^GSPC", "^NDX", "^GDAXI", "^FTSE")  # the US 500, US Tech 100, GER 40 and UK 100 CFDs
FIRST = date(1927, 1, 1)  # the fetch's first day; the judge's ten-month warm-up is read from here
DEV = (date(1929, 1, 1), date(1959, 1, 1))
VAL = (date(1959, 1, 1), date(1990, 1, 1))
JUDGE = (DEV[0], VAL[1])
HOLD = (date(2021, 1, 1), date(2026, 10, 1))
WARMUP_FROM = date(2020, 1, 1)  # the holdout's first decision needs ten month-end closes; no 2020 return is used
MONTHS = 10
COST_SIDE = 0.0005
TESTS = 1
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader TRND-1)"}

GATES = {
    "complete": "every one of the 732 months 1929-01..1989-12 has its close and its decision",
    "t": "t of the mean net monthly return, 1929..1989, >= the threshold",
    "development": "mean net monthly return > 0 in 1929..1958",
    "validation": "mean net monthly return > 0 in 1959..1989",
    "costs_x2": "mean net monthly return > 0 with the switching cost doubled",
    "smaller_crash": "the worst peak-to-trough fall is smaller than holding the index all the time",
    "top_year": "no calendar year supplies more than 50% of the total",
}
HOLDOUT_RULE = ("the four index CFDs at equal weight, each with its own filter, over all 69 months 2021-01..2026-09: "
                "mean net monthly return > 0, > 0 with the cost doubled, and a worst fall smaller than holding all "
                "four all the time; a missing month fails it")


def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()


def threshold(reg) -> float:
    earlier = sum(reg.tests_on(u, date.min, date.max) for u in COUNTED_UNIVERSES)
    return max(3.0, bonferroni_t(earlier + TESTS))


def months_between(a: date, b: date) -> int:
    return (b.year - a.year) * 12 + b.month - a.month


def spec(reg) -> dict:
    return {"program": PID, "question": "does holding a stock index only while its month-end close is above its "
                                        "10-month mean earn a positive net return, with a smaller worst fall than "
                                        "holding it all the time, in a swap-free account?",
            "judged_index": JUDGED_INDEX, "holdout_indices": list(HOLDOUT_INDICES), "months": MONTHS,
            "cost_each_switch_side": COST_SIDE, "financing": "none (a swap-free account)",
            "dividends": "not counted (price indices; ^GDAXI is a performance index)",
            "rule": "at each month-end close, hold the index for the next month if the close is above the mean of "
                    "the last 10 month-end closes (this one included); otherwise hold nothing and earn nothing. A "
                    "calendar month without a close is never bridged",
            "islamic": "long or flat only; no short sale, no leverage, no interest-bearing instrument",
            "data": "Yahoo daily closes from 1927; month-end closes are each month's last close; each file's "
                    "sha256 in the manifest",
            "periods": {"development": [str(d) for d in DEV], "validation": [str(d) for d in VAL],
                        "holdout": [str(d) for d in HOLD], "membership": "a month belongs to the period of the "
                                                                          "month it is held"},
            "gates": GATES, "holdout_rule": HOLDOUT_RULE, "threshold_t": round(threshold(reg), 4), "tests": TESTS,
            "counted_universes": list(COUNTED_UNIVERSES),
            "after": {"PASSED and VALIDATED": "proposed to the owner as a paper strategy of its own (rule 14) on the "
                                              "four index CFDs, a decision a month, sized by the risk engine, "
                                              "followed forward on paper; never real money. It is described as "
                                              "owning the market with an exit rule, not as an edge",
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

def _yahoo(sym: str, now: datetime) -> list[tuple[str, float]]:
    first = int(datetime(FIRST.year, FIRST.month, FIRST.day, tzinfo=timezone.utc).timestamp())
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?period1={first}"
           f"&period2={int(now.timestamp())}&interval=1d")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        res = json.loads(r.read())["chart"]["result"][0]
    tz = ZoneInfo(res["meta"]["exchangeTimezoneName"])
    closes = res["indicators"]["quote"][0]["close"]
    rows = {}
    for t, c in zip(res["timestamp"], closes):
        if c is not None and math.isfinite(c) and c > 0:
            rows[datetime.fromtimestamp(t, timezone.utc).astimezone(tz).date().isoformat()] = float(c)
    return sorted(rows.items())


def cmd_fetch(now: datetime) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    man = {}
    for sym in HOLDOUT_INDICES:
        rows = _yahoo(sym, now)
        body = "date,close\n" + "".join(f"{d},{v!r}\n" for d, v in rows)
        name = sym.lstrip("^")
        (DATA / f"{name}.csv").write_text(body)
        man[sym] = {"file": f"{name}.csv", "rows": len(rows), "first": rows[0][0], "last": rows[-1][0],
                    "sha256": hashlib.sha256(body.encode()).hexdigest()}
        print(sym, man[sym]["first"], man[sym]["last"], man[sym]["rows"])
    (DATA / "manifest.json").write_text(_dump({"retrieved": now.isoformat(), "series": man}))


def load(symbols, start: date, until: date) -> dict[str, dict[date, float]]:
    """Each series' closes in [start, until), only if its file matches the manifest: the judge never reads the
    holdout, and the holdout never reads the judged years."""
    man = json.loads((DATA / "manifest.json").read_text())["series"]
    out = {}
    for sym in symbols:
        m = man[sym]
        body = (DATA / m["file"]).read_text()
        if hashlib.sha256(body.encode()).hexdigest() != m["sha256"]:
            raise SystemExit(f"{m['file']} does not match its manifest: nothing is judged on it")
        rows = [ln.split(",") for ln in body.strip().splitlines()[1:]]
        out[sym] = {date.fromisoformat(d): float(c) for d, c in rows if start <= date.fromisoformat(d) < until}
    return out


# ── the rule, and what it earned ─────────────────────────────────────────

def month_ends(closes: dict[date, float]) -> list[tuple[date, float]]:
    """Each calendar month's last close, in order."""
    last: dict = {}
    for d in sorted(closes):
        last[(d.year, d.month)] = (d, closes[d])
    return [last[k] for k in sorted(last)]


def held_months(closes: dict[date, float], cost_x: float = 1.0) -> list[dict]:
    """For every month whose ten preceding month-ends exist without a gap: whether the rule held the index, the
    index's own return, and the rule's net return (switching costs included). The decision for a month reads only
    the ten month-end closes before it."""
    ends = month_ends(closes)
    out, was_in = [], False
    for i in range(MONTHS - 1, len(ends) - 1):
        if months_between(ends[i - MONTHS + 1][0], ends[i + 1][0]) != MONTHS:
            was_in = False  # a month without a close: no decision is taken across it
            continue
        window = [c for _, c in ends[i - MONTHS + 1:i + 1]]
        hold = ends[i][1] > sum(window) / MONTHS
        ret = ends[i + 1][1] / ends[i][1] - 1.0
        switch = hold != was_in
        net = (ret if hold else 0.0) - (cost_x * COST_SIDE if switch else 0.0)
        out.append({"month": date(ends[i + 1][0].year, ends[i + 1][0].month, 1), "held": hold, "index": ret,
                    "net": net, "switch": switch})
        was_in = hold
    return out


def stats(xs: list[float]) -> dict:
    n = len(xs)
    if n < 2:
        return {"n": n, "mean": xs[0] if xs else None, "t": None}
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    return {"n": n, "mean": m, "t": m / (sd / math.sqrt(n)) if sd > 0 else None, "sd": sd}


def worst_fall(xs: list[float]) -> float:
    """The largest peak-to-trough fall of the compounded curve, as a positive fraction."""
    level, peak, worst = 1.0, 1.0, 0.0
    for x in xs:
        level *= 1.0 + x
        peak = max(peak, level)
        worst = max(worst, 1.0 - level / peak)
    return worst


def in_period(rows: list[dict], start: date, end: date) -> list[dict]:
    return [r for r in rows if start <= r["month"] < end]


def gates(data: dict, thr: float) -> dict:
    closes = data[JUDGED_INDEX]
    rows = in_period(held_months(closes), *JUDGE)
    x = [r["net"] for r in rows]
    s = stats(x)
    dev = stats([r["net"] for r in rows if r["month"] < VAL[0]])
    val = stats([r["net"] for r in rows if r["month"] >= VAL[0]])
    x2 = stats([r["net"] for r in in_period(held_months(closes, cost_x=2.0), *JUDGE)])
    hold_all = [r["index"] for r in rows]
    fall, fall_all = worst_fall(x), worst_fall(hold_all)
    by_year: dict = {}
    for r in rows:
        by_year[r["month"].year] = by_year.get(r["month"].year, 0.0) + r["net"]
    total = sum(x)
    top = max(by_year.values()) / total if total > 0 and by_year else None
    held = sum(1 for r in rows if r["held"])
    ok = {"complete": s["n"] == months_between(*JUDGE),
          "t": s["t"] is not None and s["t"] >= thr,
          "development": (dev["mean"] or 0) > 0, "validation": (val["mean"] or 0) > 0,
          "costs_x2": (x2["mean"] or 0) > 0, "smaller_crash": bool(rows) and fall < fall_all,
          "top_year": top is not None and top <= 0.5}
    return {"months": s, "development": dev, "validation": val, "costs_x2": x2,
            "holding_all_the_time": stats(hold_all), "worst_fall": round(fall, 4),
            "worst_fall_holding_all_the_time": round(fall_all, 4),
            "time_in_market": held / len(rows) if rows else None,
            "switches": sum(1 for r in rows if r["switch"]),
            # the yearly fee, charged only while holding, that would take the whole return: an Islamic account that
            # charges a fixed holding fee instead of a swap must charge less than this for the rule to have paid
            "breakeven_holding_fee_a_year": round(total / held * 12, 5) if held else None,
            "by_year": {str(k): round(v, 5) for k, v in sorted(by_year.items())},
            "top_year_share": None if top is None else round(top, 3),
            "threshold_t": thr, "gates": ok, "failed_gates": [g for g, v in ok.items() if not v],
            "passed": all(ok.values())}


def basket(data: dict, start: date, end: date, cost_x: float = 1.0) -> tuple[list[float], list[float]]:
    """The indices at equal weight, each with its own rule: the basket's net monthly returns, and holding all of
    them all the time. A month counts only when every index has it."""
    per = {sym: {r["month"]: r for r in in_period(held_months(c, cost_x), start, end)} for sym, c in data.items()}
    months = sorted(set.intersection(*(set(v) for v in per.values()))) if per else []
    net = [sum(per[s][m]["net"] for s in per) / len(per) for m in months]
    hold_all = [sum(per[s][m]["index"] for s in per) / len(per) for m in months]
    return net, hold_all


def holdout_result(data: dict) -> dict:
    net, hold_all = basket(data, *HOLD)
    net2, _ = basket(data, *HOLD, cost_x=2.0)
    s, s2 = stats(net), stats(net2)
    fall, fall_all = worst_fall(net), worst_fall(hold_all)
    ok = {"complete": s["n"] == months_between(*HOLD), "mean": (s["mean"] or 0) > 0,
          "costs_x2": (s2["mean"] or 0) > 0, "smaller_crash": bool(net) and fall < fall_all}
    passed = all(ok.values())
    return {"months": s, "costs_x2": s2, "holding_all_the_time": stats(hold_all), "worst_fall": round(fall, 4),
            "worst_fall_holding_all_the_time": round(fall_all, 4), "gates": ok,
            "failed_gates": [g for g, v in ok.items() if not v], "rule": HOLDOUT_RULE,
            "classification": "VALIDATED" if passed else "REJECTED", "verdict": "PASSED" if passed else "FAILED"}


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
    reg.register(Trial(id=PID, registered=now, title="TRND-1: the long-only 10-month trend filter, swap-free",
                       hypothesis=s["question"], uses=(Use(UNIVERSE, FIRST, JUDGE[1], "judge"),),
                       tests=TESTS, configurations=TESTS, preregistration=DOC,
                       design={"spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"],
                               "threshold_t": s["threshold_t"]}))
    print("registered", PID, "threshold", s["threshold_t"])


def cmd_judge(now: datetime) -> None:
    reg = _registry()
    frozen = _check_frozen(reg)
    if reg.verdict_of(PID) is not None:
        raise SystemExit(f"{PID} already has a verdict")
    res = gates(load((JUDGED_INDEX,), FIRST, JUDGE[1]), frozen["spec"]["threshold_t"])
    body = _write(PID, {"program": PID, "verdict": "PASSED" if res["passed"] else "FAILED", **res,
                        "periods": frozen["spec"]["periods"], "spec_sha256": frozen["sha256"],
                        "code_sha256": frozen["code_sha256"], "data": json.loads((DATA / "manifest.json").read_text())})
    reg.record_verdict(Verdict(PID, now, body["verdict"], {"artifact": f"research/knowledge/{PID}.json",
                                                           "artifact_sha256": body["sha256"]}))
    print(body["verdict"], "failed:", res["failed_gates"], "months", json.dumps(res["months"]), "worst fall",
          res["worst_fall"], "vs", res["worst_fall_holding_all_the_time"])


def cmd_holdout(now: datetime) -> None:
    reg = _registry()
    frozen = _check_frozen(reg)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    if judged["verdict"] != "PASSED":
        raise SystemExit("TRND-1 did not pass: the holdout stays unread")
    if any(t.id == HID for t in reg.trials):
        raise SystemExit("the holdout was opened once already")
    reg.register(Trial(id=HID, registered=now, title="TRND-1 holdout: four index CFDs, 2021-01..2026-09",
                       hypothesis=HOLDOUT_RULE, uses=(Use(UNIVERSE, WARMUP_FROM, HOLD[1], "judge"),), tests=1,
                       configurations=1, preregistration=DOC, design={"spec_sha256": frozen["sha256"]}))
    res = holdout_result(load(HOLDOUT_INDICES, WARMUP_FROM, HOLD[1]))
    body = _write(HID, {"program": HID, "holdout_of": PID, "period": [str(d) for d in HOLD], **res})
    reg.record_verdict(Verdict(HID, now, body["verdict"], {"artifact": f"research/knowledge/{HID}.json",
                                                           "artifact_sha256": body["sha256"]}))
    print(body["verdict"], "failed:", res["failed_gates"], json.dumps(res["months"]), "worst fall", res["worst_fall"],
          "vs", res["worst_fall_holding_all_the_time"])


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc)  # the command line's clock: every function above takes its dates as arguments
    {"spec": cmd_spec, "preregister": lambda: cmd_preregister(now), "fetch": lambda: cmd_fetch(now),
     "judge": lambda: cmd_judge(now), "holdout": lambda: cmd_holdout(now)}.get(cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
