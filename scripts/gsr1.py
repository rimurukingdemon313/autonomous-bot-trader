"""GSR-1: gold/silver ratio mean reversion (research/preregistrations/GSR-1.md).

The owner, 2026-11-05: "don't fixate on the AI trading; anything that makes us a profit; never stop". Gold and silver
share their drivers (the dollar, real rates, the demand for a store of value); silver adds industrial demand and
twice the swings. Their ratio has swung between about 30 and 120, and traders have long bought the cheap metal
against the dear one when the ratio stretched. GSR-1 asks whether that pays: a pair trade against an unusually
stretched ratio, held until it is back to its year's mean, at a retail CFD's costs.

The rule, fixed before any GSR-1 price was read (scripts/gsr_probe.py read only which sources answer):
- each day's close: L = ln(gold / silver) from Yahoo's front-month futures (GC=F, SI=F), and z = (L - the mean of L
  over the 252 trading days to that close) / their standard deviation;
- flat and z >= 2 (the ratio stretched high): at the NEXT day's close, buy silver and sell gold, one dollar each;
  flat and z <= -2: buy gold and sell silver. Out at the next day's close after z crosses back through 0, or after
  252 trading days held, whichever comes first. One trade at a time; a day without both closes is no trade;
- costs, each side: 0.03% on gold, 0.10% on silver (spread and slippage); financing: the long leg pays the short rate
  plus 2.5% a year and the short leg receives the short rate minus 2.5%, so the pair pays 5% a year while held.

    python scripts/gsr1.py spec          # freeze the design (reads no data)
    python scripts/gsr1.py preregister   # register GSR-1 in research/registry.jsonl
    python scripts/gsr1.py fetch         # Yahoo daily closes (on GitHub's runner: Yahoo is blocked here)
    python scripts/gsr1.py judge         # 2002..2019: development, validation, the gates
    python scripts/gsr1.py holdout       # only if GSR-1 PASSED: 2020-01..2026-09, once

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
PID, HID = "GSR-1", "GSR-1-H"
DOC = "research/preregistrations/GSR-1.md"
SPEC = R / "specs" / "GSR-1.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "gsr"
CODE = ("scripts/gsr1.py",)
UNIVERSE = "metals-futures-daily"
GOLD, SILVER = "GC=F", "SI=F"
DEV = (date(2002, 1, 1), date(2011, 1, 1))
VAL = (date(2011, 1, 1), date(2020, 1, 1))
JUDGE = (DEV[0], VAL[1])
HOLD = (date(2020, 1, 1), date(2026, 10, 1))
WINDOW, ENTER_Z, MAX_HELD = 252, 2.0, 252
COST = {GOLD: 0.0003, SILVER: 0.0010}  # each side
PAIR_FINANCING_PA = 0.05
TESTS = 1                  # the mean's t (G1)
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader GSR-1)"}

GATES = {
    "t": "t of the mean daily net return (flat days count as zero), 2002..2019, >= the threshold",
    "development": "mean daily net > 0 in 2002..2010",
    "validation": "mean daily net > 0 in 2011..2019",
    "costs_x2": "mean daily net > 0 with every cost and the financing doubled",
    "both_sides": "the trades against a high ratio and those against a low one each net > 0 in total",
    "top_year": "no calendar year supplies more than 50% of the total net",
}
HOLDOUT_RULE = ("2020-01..2026-09: mean daily net > 0 with one-sided t >= 1.645, > 0 with every cost and the "
                "financing doubled")


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
    return {"program": PID, "question": "does a gold/silver pair traded against a ratio two standard deviations from "
                                        "its year's mean, held until it is back, pay after a retail CFD's costs?",
            "instruments": [GOLD, SILVER], "window_days": WINDOW, "enter_z": ENTER_Z, "exit": "z crosses 0",
            "max_held_days": MAX_HELD, "cost_each_side": COST, "pair_financing_pa": PAIR_FINANCING_PA,
            "lag": "the signal at a close, the trade at the next close",
            "data": "Yahoo daily closes of the front-month futures GC=F and SI=F (the probe of 2026-11-05: stooq "
                    "answered a page without data, LBMA refused); each file's sha256 in the manifest",
            "periods": {"development": [str(d) for d in DEV], "validation": [str(d) for d in VAL],
                        "holdout": [str(d) for d in HOLD]},
            "gates": GATES, "holdout_rule": HOLDOUT_RULE, "threshold_t": round(threshold(reg), 4), "tests": TESTS,
            "after": {"PASSED and VALIDATED": "proposed to the owner as a paper strategy of its own (rule 14), on "
                                              "XAUUSD and XAGUSD, sized by the risk engine, followed forward on paper; "
                                              "never real money",
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
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?period1=946684800"
           f"&period2={int(datetime.now(timezone.utc).timestamp())}&interval=1d")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        res = json.loads(r.read())["chart"]["result"][0]
    tz = ZoneInfo(res["meta"]["exchangeTimezoneName"])  # the session's own date, as the exchange dates it
    rows = {}
    for t, c in zip(res["timestamp"], res["indicators"]["quote"][0]["close"]):
        if c is not None and math.isfinite(c) and c > 0:
            rows[datetime.fromtimestamp(t, timezone.utc).astimezone(tz).date().isoformat()] = float(c)
    return sorted(rows.items())


def cmd_fetch() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    man = {}
    for sym in (GOLD, SILVER):
        rows = _yahoo(sym)
        body = "date,close\n" + "".join(f"{d},{v!r}\n" for d, v in rows)
        name = sym.replace("=", "_")
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

def zscores(data: dict) -> tuple[list[date], dict[date, float]]:
    """The days with both closes, and each one's z of ln(gold / silver) against the WINDOW days to it."""
    days = sorted(set(data[GOLD]) & set(data[SILVER]))
    lr = [math.log(data[GOLD][d] / data[SILVER][d]) for d in days]
    z = {}
    for i in range(WINDOW - 1, len(days)):
        w = lr[i - WINDOW + 1:i + 1]
        m = sum(w) / WINDOW
        sd = math.sqrt(sum((x - m) ** 2 for x in w) / (WINDOW - 1))
        if sd > 0:
            z[days[i]] = (lr[i] - m) / sd
    return days, z


def run(data: dict, start: date, end: date, cost_x: float = 1.0) -> tuple[dict[date, float], list[dict]]:
    """Each day in [start, end) with both closes: the net return of what was held over it (0 when flat), and the
    trades. A position is decided at a close and taken at the next close."""
    days, z = zscores(data)
    daily: dict[date, float] = {}
    trades: list[dict] = []
    side, held, pending, trade = 0, 0, None, None  # side +1: long silver, short gold (against a high ratio)
    for i in range(1, len(days)):
        d, p = days[i], days[i - 1]
        inside = start <= d < end
        r = 0.0
        if side and inside:
            rs, rg = data[SILVER][d] / data[SILVER][p] - 1, data[GOLD][d] / data[GOLD][p] - 1
            r = side * (rs - rg) - cost_x * PAIR_FINANCING_PA * (d - p).days / 365.0
        elif side and not inside:  # a position never runs across a period's edge: it is closed at the edge
            side, trade = 0, None
        if pending is not None and inside:  # the decision of the previous close, carried out at this close
            new = pending
            if new != side:
                if side:  # out
                    r -= cost_x * (COST[GOLD] + COST[SILVER])
                    trade["exit"], trade["days"] = d, held
                    trades.append(trade)
                if new:  # in
                    r -= cost_x * (COST[GOLD] + COST[SILVER])
                    trade = {"side": "against_high" if new > 0 else "against_low", "entry": d, "net": 0.0}
                side, held = new, 0
        pending = None
        if inside:
            daily[d] = r
            if trade is not None and (side or trade.get("exit") == d):
                trade["net"] += r
        if side:
            held += 1
        zd = z.get(d)
        if zd is None:
            continue
        if side == 0 and abs(zd) >= ENTER_Z:
            pending = 1 if zd > 0 else -1
        elif side and (side * zd <= 0 or held >= MAX_HELD):
            pending = 0
    return daily, trades


def stats(xs: list[float]) -> dict:
    n = len(xs)
    if n < 2:
        return {"n": n, "mean": xs[0] if xs else None, "t": None}
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    return {"n": n, "mean": m, "t": m / (sd / math.sqrt(n)) if sd > 0 else None, "sd": sd, "annual": m * 252,
            "annual_sharpe": m / sd * math.sqrt(252) if sd > 0 else None}


def drawdown(xs: list[float]) -> float:
    eq = peak = 1.0
    worst = 0.0
    for x in xs:
        eq *= 1 + x
        peak = max(peak, eq)
        worst = min(worst, eq / peak - 1)
    return worst


def gates(data: dict, thr: float) -> dict:
    daily, trades = run(data, *JUDGE)
    x = [daily[d] for d in sorted(daily)]
    s = stats(x)
    dev = stats([v for d, v in sorted(daily.items()) if d < VAL[0]])
    val = stats([v for d, v in sorted(daily.items()) if d >= VAL[0]])
    x2 = stats([v for _, v in sorted(run(data, *JUDGE, cost_x=2.0)[0].items())])
    sides = {k: sum(t["net"] for t in trades if t["side"] == k) for k in ("against_high", "against_low")}
    by_year: dict = {}
    for d, v in daily.items():
        by_year[d.year] = by_year.get(d.year, 0.0) + v
    total = sum(x)
    top = max(by_year.values()) / total if total > 0 and by_year else None
    ok = {"t": s["t"] is not None and s["t"] >= thr,
          "development": (dev["mean"] or 0) > 0, "validation": (val["mean"] or 0) > 0,
          "costs_x2": (x2["mean"] or 0) > 0, "both_sides": all(v > 0 for v in sides.values()) and len(trades) > 0,
          "top_year": top is not None and top <= 0.5}
    return {"net": s, "development": dev, "validation": val, "costs_x2": x2, "by_side": sides,
            "trades": [{**t, "entry": str(t["entry"]), "exit": str(t.get("exit"))} for t in trades],
            "trades_count": {k: sum(1 for t in trades if t["side"] == k) for k in ("against_high", "against_low")},
            "share_of_days_held": round(sum(1 for v in x if v != 0) / max(1, len(x)), 4),
            "max_drawdown": round(drawdown(x), 4),
            "by_year": {str(k): round(v, 4) for k, v in sorted(by_year.items())},
            "top_year_share": None if top is None else round(top, 3),
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
    reg.register(Trial(id=PID, registered=now, title="GSR-1: gold/silver ratio mean reversion",
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
    print(body["verdict"], "failed:", res["failed_gates"], "net", json.dumps(res["net"]), "sides",
          json.dumps(res["by_side"]), "trades", json.dumps(res["trades_count"]))


def cmd_holdout(now: datetime) -> None:
    reg = _registry()
    frozen = _check_frozen(reg)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    if judged["verdict"] != "PASSED":
        raise SystemExit("GSR-1 did not pass: the holdout stays unread")
    if any(t.id == HID for t in reg.trials):
        raise SystemExit("the holdout was opened once already")
    reg.register(Trial(id=HID, registered=now, title="GSR-1 holdout: 2020-01..2026-09", hypothesis=HOLDOUT_RULE,
                       uses=(Use(UNIVERSE, HOLD[0], HOLD[1], "judge"),), tests=1, configurations=1,
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"]}))
    data = load(HOLD[1])
    daily, trades = run(data, *HOLD)
    s = stats([daily[d] for d in sorted(daily)])
    s2 = stats([v for _, v in sorted(run(data, *HOLD, cost_x=2.0)[0].items())])
    ok = bool(s["mean"] and s["mean"] > 0 and s["t"] is not None and s["t"] >= 1.6448536269514722
              and (s2["mean"] or 0) > 0)
    verdict = "PASSED" if ok else "FAILED"
    body = _write(HID, {"program": HID, "holdout_of": PID, "period": [str(d) for d in HOLD], "net": s, "costs_x2": s2,
                        "trades": len(trades), "rule": HOLDOUT_RULE,
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
