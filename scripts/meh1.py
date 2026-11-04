"""MEH-1: the month-end equity-hedge rebalancing flow at the London 4 pm fix (research/preregistrations/MEH-1.md).

The owner, 2026-11-04: "change everything if you must; the most important thing is a profit; don't stop". FLOW-1
asked whether the 4 pm fix's own move reverses (it did not). MEH-1 asks the question Melvin & Prins (2015, "Equity
hedging and exchange rates at the London 4 p.m. fix", Journal of Financial Markets) put: investors who hold foreign
equities and hedge their currency exposure must re-hedge at month-end, when their holdings' value has changed, and
much of that is executed at the fix. When US equities have beaten a market over the month, foreign holders of US
equities need to sell more dollars forward than that market's holders of US-hedged foreign equities need to buy, so
the dollar should weaken into the fix; and the reverse.

The rule, fixed before any MEH-1 outcome was computed:
- the last weekday of each month (T), for each USD major: D = the S&P 500's return minus the pair's home index's,
  each in its own currency, from the last close of the previous month to the last close before T;
- D > 0: the dollar should weaken, so buy EUR, GBP, AUD, NZD against it and sell USD against JPY, CHF, CAD; D < 0: the
  reverse; D = 0 or an index without both closes: no trade for that pair;
- H1 enters at 13:00 London and exits at 16:00 London (the fix); H2 enters at 15:00;
- the month-end's observation is the mean net bps across its pairs (they share the dollar leg: one month-end is one
  observation), and it needs MIN_FIX_PAIRS pairs.

    python scripts/meh1.py spec          # freeze the design (reads no outcome)
    python scripts/meh1.py preregister   # register in research/registry.jsonl
    python scripts/meh1.py fetch         # the indices' daily closes (on GitHub's runner: Yahoo is blocked here)
    python scripts/meh1.py judge         # 2009-2016: development, validation, the gates

Prices are FLOW-1's: bid/ask at each bar's open, 0.1 pip of slippage a fill and 0.7 pip of commission a round trip.
Every command refuses to run if the code or the spec changed since registration. Nothing here changes the bot.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time as _time
import urllib.request
from bisect import bisect_left, bisect_right
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.research.discovery import flow  # noqa: E402
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict  # noqa: E402

R = ROOT / "research"
PID = "MEH-1"
DOC = "research/preregistrations/MEH-1.md"
SPEC = R / "specs" / "MEH-1.json"
OUT = R / "knowledge"
FX = ROOT / "data" / "m5"
EQ = ROOT / "data" / "meh"
CODE = ("scripts/meh1.py", "aitrader/research/discovery/flow.py")
UNIVERSE = "fx-majors"
DEV = (date(2009, 1, 1), date(2013, 1, 1))
VAL = (date(2013, 1, 1), date(2017, 1, 1))
JUDGE = (DEV[0], VAL[1])
HOLD = (date(2017, 1, 1), date(2018, 6, 1))
US = "^GSPC"
HOME = {"EURUSD": "^STOXX50E", "GBPUSD": "^FTSE", "AUDUSD": "^AXJO", "NZDUSD": "^NZ50", "USDJPY": "^N225",
        "USDCHF": "^SSMI", "USDCAD": "^GSPTSE"}
USD_QUOTE = ("EURUSD", "GBPUSD", "AUDUSD", "NZDUSD")  # the dollar is the quote: a weaker dollar is a higher pair
HYPOTHESES = {
    "MEH1-H1-13-16": "On the last weekday of the month each USD major moves from 13:00 to 16:00 London in the direction "
                     "month-end equity-hedge rebalancing implies: the dollar weakens when the S&P 500 beat the pair's "
                     "home index month to date through the day before, and strengthens when it trailed",
    "MEH1-H2-15-16": "The same, from 15:00 to 16:00 London",
}
ENTRY = {"MEH1-H1-13-16": (13, 0), "MEH1-H2-15-16": (15, 0)}
EXIT = (16, 0)
GATES = {
    "t": "t of the mean net bps over 2009-2016 >= the registry's Bonferroni threshold",
    "development": "mean net > 0 in 2009-2012",
    "validation": "mean net > 0 in 2013-2016",
    "years": ">= 60% of the years have positive net",
    "costs_x2": "mean net > 0 with spread, slippage and commission all doubled",
    "top_year": "no single year supplies more than 50% of the total net",
    "leave_one_pair_out": "mean net > 0 leaving out any one pair",
    "specificity": "the month-end mean exceeds the same rule on every other weekday of the month (Welch t >= 2)",
}
HOLDOUT_RULE = ("only for a passer, through the registry's final-test procedure on 2017-01..2018-05 (the sealed "
                "fx-majors holdout): mean net > 0 and mean net > 0 with costs x2")
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader MEH-1)"}


def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()


def spec(reg: Registry) -> dict:
    return {"program": PID, "question": "does month-end equity-hedge rebalancing move the USD majors into the London "
                                        "4 pm fix, in the direction the month's US-versus-home equity returns imply?",
            "hypotheses": HYPOTHESES, "entry_london": ENTRY, "exit_london": EXIT, "home_index": HOME, "us_index": US,
            "pairs": flow.FIX_PAIRS, "min_pairs": flow.MIN_FIX_PAIRS, "costs": flow.Costs().__dict__,
            "periods": {"development": [str(d) for d in DEV], "validation": [str(d) for d in VAL],
                        "holdout": [str(d) for d in HOLD]},
            "gates": GATES, "holdout_rule": HOLDOUT_RULE,
            "threshold_t": round(reg.threshold_for_next(UNIVERSE, JUDGE[0], JUDGE[1], new_tests=len(HYPOTHESES)), 4),
            "after": {"a passer validated on the holdout": "proposed to the owner as a paper strategy of its own "
                                                           "(rule 14), sized by the risk engine; never real money",
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
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1=1199145600&period2={int(_time.time())}"
           "&interval=1d")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        res = json.loads(r.read())["chart"]["result"][0]
    tz = ZoneInfo(res["meta"]["exchangeTimezoneName"])
    rows = {}
    for t, c in zip(res["timestamp"], res["indicators"]["quote"][0]["close"]):
        if c is not None and c > 0:
            rows[datetime.fromtimestamp(t, timezone.utc).astimezone(tz).date().isoformat()] = float(c)
    return sorted(rows.items())


def cmd_fetch() -> None:
    EQ.mkdir(parents=True, exist_ok=True)
    man = {}
    for sym in (US, *HOME.values()):
        rows = _yahoo(sym)
        body = "date,close\n" + "".join(f"{d},{v!r}\n" for d, v in rows)
        name = sym.lstrip("^")
        (EQ / f"{name}.csv").write_text(body)
        man[sym] = {"file": f"{name}.csv", "rows": len(rows), "first": rows[0][0], "last": rows[-1][0],
                    "sha256": hashlib.sha256(body.encode()).hexdigest()}
        print(sym, man[sym]["first"], man[sym]["last"], man[sym]["rows"])
    (EQ / "manifest.json").write_text(_dump({"retrieved": datetime.now(timezone.utc).isoformat(), "series": man}))


def equities() -> dict[str, tuple[list[date], list[float]]]:
    """Each index's closes, by its own local date, only if the file matches the manifest's sha256."""
    man = json.loads((EQ / "manifest.json").read_text())["series"]
    out = {}
    for sym, m in man.items():
        body = (EQ / m["file"]).read_text()
        if hashlib.sha256(body.encode()).hexdigest() != m["sha256"]:
            raise SystemExit(f"{m['file']} does not match its manifest: nothing is judged on it")
        rows = [ln.split(",") for ln in body.strip().splitlines()[1:]]
        out[sym] = ([date.fromisoformat(d) for d, _ in rows], [float(c) for _, c in rows])
    return out


class _Bars:
    def __init__(self, symbol: str, z) -> None:
        self.symbol, self.open_time = symbol, z["open_time"]
        self.bid_open, self.ask_open = z["bid_open"], z["ask_open"]


def opens(until: date) -> dict[str, flow.Opens]:
    """The pairs' M5 bid/ask opens before `until`: the sealed 2017+ data is not read (nor kept here)."""
    out = {}
    cut = int(datetime.combine(until, datetime.min.time(), tzinfo=timezone.utc).timestamp())
    for s in flow.FIX_PAIRS:
        z = np.load(FX / f"{s}_M5_2009_2016.npz")
        keep = z["open_time"] < cut
        out[s] = flow.Opens(_Bars(s, {k: z[k][keep] for k in ("open_time", "bid_open", "ask_open")}))
    return out


# ── the rule ─────────────────────────────────────────────────────────────

def month_to_date(series: tuple[list[date], list[float]], day: date) -> float | None:
    """The index's return from its last close on or before the previous month's last day to its last close strictly
    before `day`, both in its own currency; None when either close is missing."""
    ds, cs = series
    base_day = day.replace(day=1) - timedelta(days=1)
    i0 = bisect_right(ds, base_day) - 1
    i1 = bisect_left(ds, day) - 1
    if i0 < 0 or i1 < 0 or i1 <= i0 or (base_day - ds[i0]).days > 7:
        return None
    return cs[i1] / cs[i0] - 1.0


def side(pair: str, d: float) -> int:
    """+1 buys the pair. D > 0 (US equities beat the home market): the dollar should weaken."""
    if d == 0:
        return 0
    weak = 1 if d > 0 else -1
    return weak if pair in USD_QUOTE else -weak


def events(op: dict, eq: dict, days: list[date], hid: str, costs: flow.Costs,
           leave_out: str | None = None) -> list[dict]:
    """One observation per day: the mean net bps across the pairs that traded (at least MIN_FIX_PAIRS)."""
    out = []
    hh, mm = ENTRY[hid]
    for d in days:
        t_in, t_out = flow.epoch_at(d, hh, mm, flow.LONDON), flow.epoch_at(d, *EXIT, flow.LONDON)
        us = month_to_date(eq[US], d)
        legs = {}
        for pair, o in op.items():
            if pair == leave_out:
                continue
            home = month_to_date(eq[HOME[pair]], d)
            if us is None or home is None:
                continue
            s = side(pair, us - home)
            r = flow.trade(o, t_in, t_out, s, costs) if s else None
            if r is not None:
                legs[pair] = r
        if len(legs) >= flow.MIN_FIX_PAIRS:
            out.append({"date": d, "pairs": len(legs),
                        **{k: float(np.mean([v[k] for v in legs.values()])) for k in ("gross_bps", "net_bps",
                                                                                      "cost_bps")},
                        "legs": {p: round(v["net_bps"], 4) for p, v in legs.items()}})
    return out


def judge_one(op: dict, eq: dict, hid: str, thr: float) -> dict:
    ends = flow.last_business_days(*JUDGE)
    base = events(op, eq, ends, hid, flow.Costs())
    x2 = events(op, eq, ends, hid, flow.Costs().stressed(2.0))
    others = [d for d in flow.business_days(*JUDGE) if d not in set(ends)]
    placebo = events(op, eq, others, hid, flow.Costs())
    s = flow.summary(base)
    years = flow.by_year(base)
    total = sum(v["total"] for v in years.values())
    top = max(v["total"] for v in years.values()) / total if total > 0 else None
    loo = {p: flow.summary(events(op, eq, ends, hid, flow.Costs(), leave_out=p))["mean"] for p in flow.FIX_PAIRS}
    dev = flow.summary([e for e in base if e["date"] < VAL[0]])
    val = flow.summary([e for e in base if e["date"] >= VAL[0]])
    spec_t = flow.welch_t([e["net_bps"] for e in base], [e["net_bps"] for e in placebo])
    ok = {"t": s["t"] is not None and s["t"] >= thr,
          "development": (dev["mean"] or 0) > 0, "validation": (val["mean"] or 0) > 0,
          "years": bool(years) and sum(1 for v in years.values() if v["total"] > 0) >= 0.6 * len(years),
          "costs_x2": (flow.summary(x2)["mean"] or 0) > 0,
          "top_year": top is not None and top <= 0.5,
          "leave_one_pair_out": all((m or 0) > 0 for m in loo.values()),
          "specificity": spec_t is not None and spec_t >= 2.0}
    return {"net": s, "gross": flow.summary(base, "gross_bps"), "costs": flow.summary(base, "cost_bps"),
            "development": dev, "validation": val, "costs_x2": flow.summary(x2), "by_year": years,
            "top_year_share": None if top is None else round(top, 3), "leave_one_pair_out": loo,
            "placebo_other_weekdays": flow.summary(placebo), "specificity_welch_t": spec_t,
            "max_drawdown_bps": round(flow.max_drawdown([e["net_bps"] for e in base]), 3),
            "gates": ok, "failed_gates": [g for g, v in ok.items() if not v], "passed": all(ok.values())}


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
    reg.register(Trial(id=PID, registered=now, title="MEH-1: month-end equity-hedge rebalancing at the 4 pm fix",
                       hypothesis=s["question"], uses=(Use(UNIVERSE, JUDGE[0], JUDGE[1], "judge"),),
                       tests=len(HYPOTHESES), configurations=len(HYPOTHESES), preregistration=DOC,
                       design={"spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"],
                               "threshold_t": s["threshold_t"]}))
    print("registered", PID, "threshold", s["threshold_t"])


def cmd_judge(now: datetime) -> None:
    reg = _registry()
    frozen = _check_frozen(reg)
    if reg.verdict_of(PID) is not None:
        raise SystemExit(f"{PID} already has a verdict")
    thr = frozen["spec"]["threshold_t"]
    op, eq = opens(JUDGE[1]), equities()
    results = {h: judge_one(op, eq, h, thr) for h in HYPOTHESES}
    passers = [h for h, r in results.items() if r["passed"]]
    body = _write(PID, {"program": PID, "threshold": thr, "periods": frozen["spec"]["periods"], "results": results,
                        "passers": passers, "verdict": "PASSED" if passers else "FAILED",
                        "classification": {h: "HOLDOUT_ELIGIBLE" if r["passed"] else "REJECTED"
                                           for h, r in results.items()},
                        "spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"],
                        "equity_data": json.loads((EQ / "manifest.json").read_text())})
    reg.record_verdict(Verdict(PID, now, body["verdict"], {"artifact": f"research/knowledge/{PID}.json",
                                                           "artifact_sha256": body["sha256"]}))
    for h, r in results.items():
        print(h, json.dumps(r["net"]), "dev", r["development"]["mean"], "val", r["validation"]["mean"],
              "placebo", r["placebo_other_weekdays"]["mean"], "failed:", r["failed_gates"])
    print("passers:", passers)


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc)  # the command line's clock: every function above takes its dates as arguments
    {"spec": cmd_spec, "preregister": lambda: cmd_preregister(now), "fetch": cmd_fetch,
     "judge": lambda: cmd_judge(now)}.get(cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
