"""DAY-1: buy a short, sharp pullback in an index that is in an uptrend, and sell the bounce, at a swap-free account's
costs (research/preregistrations/DAY-1.md).

The owner, 2026-11-08: "$4,000 a month; trades so I see the account moving; more profit than loss; make it happen".
TRND-1 trades a few times a year. This asks whether a published short-term rule, which trades several times a month
on the same four index CFDs, earned a positive net return after costs on years it was not published from.

The rule (Connors & Alvarez, "Short Term Trading Strategies That Work", 2009), fixed before any DAY-1 outcome:
- an index is in an uptrend when its close is above the mean of its last 200 closes, that one included;
- in an uptrend, buy at the close when its 2-day RSI (Wilder's) is below 10;
- sell at the first close above the mean of its last 5 closes, and at the latest at the 10th close after the entry;
- a protective stop 6% below the entry close, hit by a day's low; a day that opens below it fills at the open;
- one position per index at a time; long or flat, never short;
- each fill pays 0.05% (spread, slippage and commission); no financing (a swap-free account); price indices only.

The test: the four indices at equal weight, a quarter of the capital each while it holds a trade. The statistic is the
basket's mean daily net return, judged over 1990..2020: development 1990..2005, validation 2006..2020. The holdout,
2021-01..2026-09, is opened once, and only after a pass. These years have been read before. RC-EQ (1990-2020) judged
other rules on index CFDs, and TRND-1-H read the month-end closes of 2021-2026. No test here has computed a
short-term rule on them, and the threshold counts every earlier test on index or US equity data.

    python scripts/day1.py spec          # freeze the design (reads no data)
    python scripts/day1.py preregister   # register DAY-1 in research/registry.jsonl
    python scripts/day1.py fetch         # Yahoo daily bars (on GitHub's runner: Yahoo is blocked here)
    python scripts/day1.py judge         # 1990..2020: development, validation, the gates
    python scripts/day1.py holdout       # only if DAY-1 PASSED: 2021-01..2026-09, once

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
PID, HID = "DAY-1", "DAY-1-H"
DOC = "research/preregistrations/DAY-1.md"
SPEC = R / "specs" / "DAY-1.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "day1"
CODE = ("scripts/day1.py",)
UNIVERSE = "equity-index-daily"
#: every earlier test on stock-index or US equity data counts against this one's threshold, intraday ones included
COUNTED_UNIVERSES = ("multi-asset-etf", "multi-asset-long", "equity-index-b", "equity-index-forward",
                     "equity-index-monthly", "index-cfd-intraday", "us-equity-etf", "us-vol-etp", UNIVERSE)
INDICES = ("^GSPC", "^NDX", "^GDAXI", "^FTSE")  # the US 500, US Tech 100, GER 40 and UK 100 CFDs
FIRST = date(1988, 6, 1)  # the fetch's first day: 200 closes of warm-up before 1990
DEV = (date(1990, 1, 1), date(2006, 1, 1))
VAL = (date(2006, 1, 1), date(2021, 1, 1))
JUDGE = (DEV[0], VAL[1])
HOLD = (date(2021, 1, 1), date(2026, 10, 1))
WARMUP_FROM = date(2019, 9, 1)  # the holdout's first decisions need 200 closes; no return before 2021 is used
TREND_N, RSI_N, EXIT_N = 200, 2, 5
RSI_BUY = 10.0
MAX_DAYS = 10
STOP = 0.06
COST_SIDE = 0.0005
TESTS = 1
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader DAY-1)"}

GATES = {
    "complete": "each index has bars from before 1989-06 through 2020-12",
    "t": "t of the basket's mean daily net return, 1990..2020, >= the threshold",
    "development": "mean daily net return > 0 in 1990..2005",
    "validation": "mean daily net return > 0 in 2006..2020",
    "costs_x2": "mean daily net return > 0 with every fill's cost doubled",
    "top_year": "no calendar year supplies more than 50% of the total",
}
HOLDOUT_RULE = ("the same basket over every trading day 2021-01-04..2026-09-30: mean daily net return > 0, and > 0 "
                "with the cost doubled; its t is reported, and the registry validates it only at t >= 2.5")


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


def spec(reg) -> dict:
    return {"program": PID, "question": "in an index above its 200-day mean, does buying at the close when the 2-day "
                                        "RSI is below 10 and selling at the first close above the 5-day mean earn a "
                                        "positive net return at a swap-free account's costs?",
            "indices": list(INDICES), "trend_closes": TREND_N, "rsi_closes": RSI_N, "rsi_buy_below": RSI_BUY,
            "exit_mean_closes": EXIT_N, "max_days": MAX_DAYS, "stop": STOP, "cost_each_fill": COST_SIDE,
            "financing": "none (a swap-free account)", "dividends": "not counted (price indices)",
            "rule": "for each index separately: flat, and the close is above the mean of the last 200 closes and the "
                    "2-day Wilder RSI is below 10 -> buy at that close. Holding: a day whose low reaches 6% below the "
                    "entry close exits at that level, or at its open if it opened below it; otherwise exit at the "
                    "first close above the mean of the last 5 closes, or at the 10th close after the entry. One "
                    "position per index; a signal is acted on only at the close it appears",
            "basket": "a quarter of the capital per index while it holds a trade; the basket's daily return is the "
                      "mean of the four indices' daily strategy returns, an index without a bar that day counting 0",
            "source": "Connors & Alvarez (2009), Short Term Trading Strategies That Work: the 2-period RSI with a "
                      "200-day filter and a 5-day-mean exit; the 6% stop is the bot's own one-day stop",
            "islamic": "long or flat only; no short sale, no interest-bearing instrument",
            "data": "Yahoo daily open, high, low and close from 1988-06; each file's sha256 in the manifest",
            "periods": {"development": [str(d) for d in DEV], "validation": [str(d) for d in VAL],
                        "holdout": [str(d) for d in HOLD], "membership": "a day belongs to the period it is in"},
            "gates": GATES, "holdout_rule": HOLDOUT_RULE, "threshold_t": round(threshold(reg), 4), "tests": TESTS,
            "counted_universes": list(COUNTED_UNIVERSES),
            "after": {"PASSED and VALIDATED": "proposed as a paper desk of its own (rule 14) on the four index CFDs, "
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


# ── the data ─────────────────────────────────────────────────────────────

def _yahoo(sym: str, now: datetime) -> list[list]:
    first = int(datetime(FIRST.year, FIRST.month, FIRST.day, tzinfo=timezone.utc).timestamp())
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?period1={first}"
           f"&period2={int(now.timestamp())}&interval=1d")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        res = json.loads(r.read())["chart"]["result"][0]
    tz = ZoneInfo(res["meta"]["exchangeTimezoneName"])
    q = res["indicators"]["quote"][0]
    rows = {}
    for i, t in enumerate(res.get("timestamp") or []):
        o, h, lo, c = (q[k][i] for k in ("open", "high", "low", "close"))
        if all(isinstance(v, (int, float)) and math.isfinite(v) and v > 0 for v in (o, h, lo, c)):
            rows[datetime.fromtimestamp(t, timezone.utc).astimezone(tz).date().isoformat()] = \
                [float(o), max(float(h), float(o), float(c)), min(float(lo), float(o), float(c)), float(c)]
    return [[d, *v] for d, v in sorted(rows.items())]


def cmd_fetch(now: datetime) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    man = {}
    for sym in INDICES:
        rows = _yahoo(sym, now)
        body = "date,open,high,low,close\n" + "".join(f"{d},{o!r},{h!r},{lo!r},{c!r}\n" for d, o, h, lo, c in rows)
        name = sym.lstrip("^")
        (DATA / f"{name}.csv").write_text(body)
        man[sym] = {"file": f"{name}.csv", "rows": len(rows), "first": rows[0][0], "last": rows[-1][0],
                    "sha256": hashlib.sha256(body.encode()).hexdigest()}
        print(sym, man[sym]["first"], man[sym]["last"], man[sym]["rows"])
    (DATA / "manifest.json").write_text(_dump({"retrieved": now.isoformat(), "series": man}))


def load(symbols, start: date, until: date) -> dict[str, list[tuple]]:
    """Each series' bars (day, open, high, low, close) in [start, until), only if its file matches the manifest."""
    man = json.loads((DATA / "manifest.json").read_text())["series"]
    out = {}
    for sym in symbols:
        m = man[sym]
        body = (DATA / m["file"]).read_text()
        if hashlib.sha256(body.encode()).hexdigest() != m["sha256"]:
            raise SystemExit(f"{m['file']} differs from the manifest")
        rows = []
        for line in body.splitlines()[1:]:
            d, o, h, lo, c = line.split(",")
            day = date.fromisoformat(d)
            if start <= day < until:
                rows.append((day, float(o), float(h), float(lo), float(c)))
        out[sym] = rows
    return out


# ── the rule ─────────────────────────────────────────────────────────────

def rsi(closes: list[float], n: int = RSI_N) -> list[float | None]:
    """Wilder's RSI of each close; None until n changes exist."""
    out: list[float | None] = [None] * len(closes)
    gain = loss = None
    for i in range(1, len(closes)):
        ch = closes[i] - closes[i - 1]
        g, lo = max(ch, 0.0), max(-ch, 0.0)
        if i < n:
            gain = (gain or 0.0) + g
            loss = (loss or 0.0) + lo
            continue
        if i == n:
            gain, loss = ((gain or 0.0) + g) / n, ((loss or 0.0) + lo) / n
        else:
            gain, loss = (gain * (n - 1) + g) / n, (loss * (n - 1) + lo) / n
        out[i] = 100.0 if loss == 0 else 100.0 - 100.0 / (1.0 + gain / loss)
    return out


def trades(bars: list[tuple], cost_x: float = 1.0) -> tuple[list[dict], dict[date, float]]:
    """Walk forward bar by bar. Returns the trades and each day's strategy return for this index (days in a trade
    only). A decision at bar i reads bars[:i+1] and nothing after it."""
    closes = [b[4] for b in bars]
    r2 = rsi(closes)
    cost = COST_SIDE * cost_x
    out, daily = [], {}
    pos = None  # {"i", "entry"}
    for i, (day, op, hi, lo, cl) in enumerate(bars):
        if pos is not None:
            prev = closes[i - 1]
            stop = pos["entry"] * (1 - STOP)
            exit_px, why = None, None
            if lo <= stop:
                exit_px, why = (op if op < stop else stop), "STOP"
            elif i >= EXIT_N - 1 and cl > sum(closes[i - EXIT_N + 1:i + 1]) / EXIT_N:
                exit_px, why = cl, "MEAN"
            elif i - pos["i"] >= MAX_DAYS:
                exit_px, why = cl, "TIME"
            px = exit_px if exit_px is not None else cl
            daily[day] = daily.get(day, 0.0) + px / prev - 1.0 - (cost if exit_px is not None else 0.0)
            if exit_px is not None:
                gross = exit_px / pos["entry"] - 1.0
                out.append({"entry_day": bars[pos["i"]][0], "exit_day": day, "entry": pos["entry"], "exit": exit_px,
                            "why": why, "days": i - pos["i"], "net": gross - 2 * cost})
                pos = None
            continue
        if i + 1 < TREND_N or r2[i] is None:
            continue
        if cl > sum(closes[i - TREND_N + 1:i + 1]) / TREND_N and r2[i] < RSI_BUY:
            pos = {"i": i, "entry": cl}
            daily[day] = daily.get(day, 0.0) - cost  # bought at the close: only the fill's cost today
    return out, daily


def basket(data: dict[str, list[tuple]], start: date, end: date, cost_x: float = 1.0) -> tuple[dict, dict]:
    """The basket's daily net returns over every trading day in [start, end) on which any index has a bar, and each
    index's trades that closed in it."""
    per, all_trades = {}, {}
    days: set[date] = set()
    for sym, bars in data.items():
        t, daily = trades(bars, cost_x)
        per[sym] = daily
        all_trades[sym] = [x for x in t if start <= x["exit_day"] < end]
        days |= {b[0] for b in bars if start <= b[0] < end}
    n = len(data)
    return {d: sum(per[s].get(d, 0.0) for s in per) / n for d in sorted(days)}, all_trades


def stats(xs: list[float]) -> dict:
    n = len(xs)
    if n < 2:
        return {"n": n, "mean": xs[0] if xs else None, "t": None}
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    return {"n": n, "mean": m, "t": m / (sd / math.sqrt(n)) if sd > 0 else None, "sd": sd}


def worst_fall(xs: list[float]) -> float:
    level, peak, worst = 1.0, 1.0, 0.0
    for x in xs:
        level *= 1.0 + x
        peak = max(peak, level)
        worst = max(worst, 1.0 - level / peak)
    return worst


def trade_summary(all_trades: dict) -> dict:
    ts = [t for v in all_trades.values() for t in v]
    wins = [t for t in ts if t["net"] > 0]
    return {"trades": len(ts), "won": round(len(wins) / len(ts), 3) if ts else None,
            "mean_net": round(sum(t["net"] for t in ts) / len(ts), 6) if ts else None,
            "by_exit": {w: sum(1 for t in ts if t["why"] == w) for w in ("MEAN", "TIME", "STOP")},
            "by_index": {s: len(v) for s, v in all_trades.items()}}


def gates(data: dict, thr: float) -> dict:
    daily, tr = basket(data, *JUDGE)
    x = list(daily.values())
    s = stats(x)
    dev = stats([v for d, v in daily.items() if d < VAL[0]])
    val = stats([v for d, v in daily.items() if d >= VAL[0]])
    daily2, _ = basket(data, *JUDGE, cost_x=2.0)
    x2 = stats(list(daily2.values()))
    by_year: dict = {}
    for d, v in daily.items():
        by_year[d.year] = by_year.get(d.year, 0.0) + v
    total = sum(x)
    top = max(by_year.values()) / total if total > 0 and by_year else None
    complete = all(bars and bars[0][0] <= date(1989, 6, 1) and bars[-1][0] >= date(2020, 12, 28)
                   for bars in data.values())
    ok = {"complete": complete, "t": s["t"] is not None and s["t"] >= thr,
          "development": (dev["mean"] or 0) > 0, "validation": (val["mean"] or 0) > 0,
          "costs_x2": (x2["mean"] or 0) > 0, "top_year": top is not None and top <= 0.5}
    return {"days": s, "development": dev, "validation": val, "costs_x2": x2,
            "a_year": round(s["mean"] * 252, 5) if s["mean"] is not None else None,
            "worst_fall": round(worst_fall(x), 4), "trades": trade_summary(tr),
            "by_year": {str(k): round(v, 5) for k, v in sorted(by_year.items())},
            "top_year_share": None if top is None else round(top, 3),
            "threshold_t": thr, "gates": ok, "failed_gates": [g for g, v in ok.items() if not v],
            "passed": all(ok.values())}


def holdout_result(data: dict) -> dict:
    daily, tr = basket(data, *HOLD)
    daily2, _ = basket(data, *HOLD, cost_x=2.0)
    s, s2 = stats(list(daily.values())), stats(list(daily2.values()))
    ok = {"mean": (s["mean"] or 0) > 0, "costs_x2": (s2["mean"] or 0) > 0}
    passed = all(ok.values())
    return {"days": s, "costs_x2": s2, "a_year": round(s["mean"] * 252, 5) if s["mean"] is not None else None,
            "worst_fall": round(worst_fall(list(daily.values())), 4), "trades": trade_summary(tr), "gates": ok,
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
    reg.register(Trial(id=PID, registered=now, title="DAY-1: the 2-day RSI pullback in an uptrend, swap-free",
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
    res = gates(load(INDICES, FIRST, JUDGE[1]), frozen["spec"]["threshold_t"])
    body = _write(PID, {"program": PID, "verdict": "PASSED" if res["passed"] else "FAILED", **res,
                        "periods": frozen["spec"]["periods"], "spec_sha256": frozen["sha256"],
                        "code_sha256": frozen["code_sha256"], "data": json.loads((DATA / "manifest.json").read_text())})
    reg.record_verdict(Verdict(PID, now, body["verdict"], {"artifact": f"research/knowledge/{PID}.json",
                                                           "artifact_sha256": body["sha256"]}))
    print(body["verdict"], "failed:", res["failed_gates"], "days", json.dumps(res["days"]), "a year", res["a_year"],
          "trades", json.dumps(res["trades"]))


def cmd_holdout(now: datetime) -> None:
    reg = _registry()
    frozen = _check_frozen(reg)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    if judged["verdict"] != "PASSED":
        raise SystemExit("DAY-1 did not pass: the holdout stays unread")
    if any(t.id == HID for t in reg.trials):
        raise SystemExit("the holdout was opened once already")
    reg.register(Trial(id=HID, registered=now, title="DAY-1 holdout: four index CFDs, 2021-01..2026-09",
                       hypothesis=HOLDOUT_RULE, uses=(Use(UNIVERSE, WARMUP_FROM, HOLD[1], "judge"),), tests=1,
                       configurations=1, preregistration=DOC, design={"spec_sha256": frozen["sha256"]}))
    res = holdout_result(load(INDICES, WARMUP_FROM, HOLD[1]))
    body = _write(HID, {"program": HID, "holdout_of": PID, "period": [str(d) for d in HOLD], **res})
    reg.record_verdict(Verdict(HID, now, body["verdict"], {"artifact": f"research/knowledge/{HID}.json",
                                                           "artifact_sha256": body["sha256"]}))
    print(body["verdict"], "failed:", res["failed_gates"], json.dumps(res["days"]), "a year", res["a_year"],
          "trades", json.dumps(res["trades"]))


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc)  # the command line's clock: every function above takes its dates as arguments
    {"spec": cmd_spec, "preregister": lambda: cmd_preregister(now), "fetch": lambda: cmd_fetch(now),
     "judge": lambda: cmd_judge(now), "holdout": lambda: cmd_holdout(now)}.get(cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
