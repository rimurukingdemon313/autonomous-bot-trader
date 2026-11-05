"""VOLM-1: volatility-managed S&P 500 exposure (research/preregistrations/VOLM-1.md).

The owner, 2026-11-05: "don't fixate on the AI trading; anything that makes us a profit; never stop". Moreira & Muir
(2017, "Volatility-Managed Portfolios", Journal of Finance) found that scaling the market's exposure by the inverse
of last month's realised variance raises its risk-adjusted return: volatility clusters, but expected returns do not
rise with it, so holding less after turbulent months gives up little return for a lot less risk. Cederburg,
O'Doherty, Wang & Yan (2020) found the gain weak out of sample. VOLM-1 asks whether it holds for the S&P 500 since
1995, held as a retail CFD would hold it, after costs.

The rule, fixed before any VOLM-1 data was fetched:
- at each month's last close, RV = the sum of the month's squared daily S&P 500 returns (SPY, dividends in);
- the exposure for the next month is the mean RV of every month so far (this one included) divided by this month's
  RV: about 1 after an ordinary month, less after a turbulent one, more after a calm one, never above 2;
- the position is held for the month; its exposure drifts with the market and is traded back at the next month's
  last close, paying 0.05% of the notional traded;
- a CFD's long financing is the short rate plus a markup: every unit of exposure pays the 3-month T-bill rate plus
  2.5% a year, by calendar days. The market it is compared with pays the same;
- the question: the alpha of the managed book's monthly excess return on the market's (OLS, White standard errors).
  A positive alpha means it beats the market at the market's own risk, not only by holding more of it.

    python scripts/volm1.py spec          # freeze the design (reads no data)
    python scripts/volm1.py preregister   # register VOLM-1 in research/registry.jsonl
    python scripts/volm1.py fetch         # Yahoo daily closes (on GitHub's runner: Yahoo is blocked here)
    python scripts/volm1.py judge         # 1995..2021: development, validation, the gates
    python scripts/volm1.py holdout       # only if VOLM-1 PASSED: 2022-01..2026-09, once

Each command refuses to run if the code or the spec changed since registration. Nothing here changes the bot.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time as _time
import urllib.request
from bisect import bisect_right
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402

R = ROOT / "research"
PID, HID = "VOLM-1", "VOLM-1-H"
DOC = "research/preregistrations/VOLM-1.md"
SPEC = R / "specs" / "VOLM-1.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "volm"
CODE = ("scripts/volm1.py",)
UNIVERSE = "us-equity-etf"
#: every earlier test on S&P 500 or US equity-index data counts against this one's threshold
EQUITY_UNIVERSES = ("multi-asset-etf", "multi-asset-long", "equity-index-b", "us-vol-etp", UNIVERSE)
MARKET, RATE = "SPY", "^IRX"
DEV = (date(1995, 1, 1), date(2009, 1, 1))
VAL = (date(2009, 1, 1), date(2022, 1, 1))
JUDGE = (DEV[0], VAL[1])
HOLD = (date(2022, 1, 1), date(2026, 10, 1))
MAX_EXPOSURE = 2.0
COST = 0.0005          # per unit of notional traded
MARKUP_PA = 0.025      # a CFD's long financing over the short rate, a year, by calendar days
RATE_STALE_DAYS = 7    # the T-bill yield last published within this many days is the one known; older is none
TESTS = 1              # the alpha's t (G1)
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader VOLM-1)"}

GATES = {
    "t": "White t of the managed book's monthly alpha on the market, 1995..2021, >= the threshold",
    "development": "alpha > 0 in 1995..2008",
    "validation": "alpha > 0 in 2009..2021",
    "costs_x2": "alpha > 0 with the trading cost and the markup doubled",
    "book_pays": "the managed book's own mean monthly excess return, net, > 0",
    "top_year": "no calendar year supplies more than 50% of the total alpha",
}
HOLDOUT_RULE = ("2022-01..2026-09: alpha > 0 with one-sided White t >= 1.645, alpha > 0 with the costs doubled, and "
                "the managed book's own mean monthly excess return > 0")


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
    return {"program": PID, "question": "does scaling S&P 500 exposure by the inverse of last month's realised "
                                        "variance earn a positive alpha on the market, after a retail CFD's costs?",
            "market": MARKET, "rate": RATE, "max_exposure": MAX_EXPOSURE, "cost_per_unit_traded": COST,
            "markup_pa": MARKUP_PA,
            "rule": "exposure for month m+1 = mean RV of months up to m / RV of m, capped at 2; RV = sum of squared "
                    "daily returns in the month; held for the month, its drift traded back at the next month's "
                    "last close",
            "test": "OLS of the managed book's monthly net excess return on the market's (both pay the short rate "
                    "plus the markup on their exposure), White standard errors",
            "data": "Yahoo daily closes: SPY adjusted for dividends and splits, ^IRX as published; each file's "
                    "sha256 in the manifest; a missing day is not filled: a month without all its days is no trade",
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

def _yahoo(sym: str, allow_zero: bool = False) -> list[tuple[str, float]]:
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1=725846400&period2={int(_time.time())}"
           "&interval=1d&events=div%7Csplit")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        res = json.loads(r.read())["chart"]["result"][0]
    tz = ZoneInfo(res["meta"]["exchangeTimezoneName"])
    adj = ((res["indicators"].get("adjclose") or [{}])[0] or {}).get("adjclose")
    closes = adj if adj else res["indicators"]["quote"][0]["close"]
    rows = {}
    for t, c in zip(res["timestamp"], closes):
        if c is not None and math.isfinite(c) and (c > 0 or (allow_zero and c == 0)):
            rows[datetime.fromtimestamp(t, timezone.utc).astimezone(tz).date().isoformat()] = float(c)
    return sorted(rows.items())


def cmd_fetch() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    man = {}
    for sym in (MARKET, RATE):
        rows = _yahoo(sym, allow_zero=sym == RATE)  # a zero T-bill yield is real (2009-2015, 2020-2021)
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
    """The T-bill yield last published on or before d (the bond market closes on some days the stock market trades),
    or None if the last one is more than RATE_STALE_DAYS old."""
    i = bisect_right(rate_days, d) - 1
    if i < 0 or d - rate_days[i] > timedelta(days=RATE_STALE_DAYS):
        return None
    return rate[rate_days[i]]


def months_of(data: dict) -> list[dict]:
    """Each calendar month of the market's trading days: its daily returns, its compounded return, its compounded
    short rate (the T-bill yield known at the previous close, by calendar days), its calendar days, and its RV. A
    month with a day whose rate is unknown has no rate (None): no trade."""
    px, rate = data[MARKET], data[RATE]
    days, rate_days = sorted(px), sorted(rate)
    out: list[dict] = []
    for prev, d in zip(days, days[1:]):
        key = (d.year, d.month)
        if not out or out[-1]["key"] != key:
            out.append({"key": key, "rets": [], "rf": 1.0, "cal": 0, "last": d})
        m = out[-1]
        m["rets"].append(px[d] / px[prev] - 1.0)
        y, gap = known_rate(rate, rate_days, prev), (d - prev).days
        m["rf"] = None if m["rf"] is None or y is None else m["rf"] * (1 + y / 100.0 * gap / 365.0)
        m["cal"] += gap
        m["last"] = d
    for m in out:
        m["R"] = math.prod(1 + r for r in m["rets"]) - 1.0
        m["RF"] = None if m["rf"] is None else m["rf"] - 1.0
        m["RV"] = sum(r * r for r in m["rets"])
    return out


def book(data: dict, start: date, end: date, cost: float = COST, markup: float = MARKUP_PA) -> list[dict]:
    """Per month in [start, end): the managed book's net excess return, the market's, and the exposure held. The
    exposure for a month is set at the previous month's last close from RVs known then."""
    ms = months_of(data)
    out, past, w_prev, drifted = [], [], None, 0.0
    for i, m in enumerate(ms):
        if i > 0 and ms[i - 1]["RV"] > 0:
            past.append(ms[i - 1]["RV"])
        if not past or i == 0:
            continue
        w = min(MAX_EXPOSURE, (sum(past) / len(past)) / ms[i - 1]["RV"]) if ms[i - 1]["RV"] > 0 else MAX_EXPOSURE
        first = date(m["key"][0], m["key"][1], 1)
        if not (start <= first < end) or m["RF"] is None:
            w_prev, drifted = None, 0.0
            continue
        traded = abs(w - drifted) if w_prev is not None else w
        fin = markup * m["cal"] / 365.0
        x = m["R"] - m["RF"] - fin
        y = w * (m["R"] - m["RF"]) - w * fin - cost * traded
        out.append({"month": first, "w": w, "managed": y, "market": x})
        w_prev = w
        drifted = w * (1 + m["R"]) / (1 + w * m["R"]) if 1 + w * m["R"] > 0 else 0.0
    return out


def alpha(rows: list[dict]) -> dict:
    """OLS of managed on market, with White (HC0) standard errors."""
    n = len(rows)
    if n < 3:
        return {"n": n, "alpha": None, "t": None}
    y = [r["managed"] for r in rows]
    x = [r["market"] for r in rows]
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    beta = sum((a - mx) * (b - my) for a, b in zip(x, y)) / sxx
    a0 = my - beta * mx
    e = [b - a0 - beta * a for a, b in zip(x, y)]
    # HC0 variance of the intercept: (X'X)^-1 X' diag(e^2) X (X'X)^-1, element [0, 0]
    sx, sxx2 = sum(x), sum(a * a for a in x)
    det = n * sxx2 - sx * sx
    inv = ((sxx2 / det, -sx / det), (-sx / det, n / det))
    m00 = sum(ei * ei for ei in e)
    m01 = sum(ei * ei * a for ei, a in zip(e, x))
    m11 = sum(ei * ei * a * a for ei, a in zip(e, x))
    meat = ((m00, m01), (m01, m11))
    v00 = sum(inv[0][i] * meat[i][j] * inv[j][0] for i in range(2) for j in range(2))
    se = math.sqrt(v00) if v00 > 0 else None
    return {"n": n, "alpha": a0, "beta": beta, "t": a0 / se if se else None, "alpha_annual": a0 * 12,
            "contributions": [b - beta * a for a, b in zip(x, y)]}


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
    a = alpha(rows)
    dev = alpha([r for r in rows if r["month"] < VAL[0]])
    val = alpha([r for r in rows if r["month"] >= VAL[0]])
    x2 = alpha(book(data, *JUDGE, cost=2 * COST, markup=2 * MARKUP_PA))
    own = monthly([r["managed"] for r in rows])
    by_year: dict = {}
    for r, c in zip(rows, a.get("contributions") or []):
        by_year[r["month"].year] = by_year.get(r["month"].year, 0.0) + c
    total = sum(by_year.values())
    top = max(by_year.values()) / total if total > 0 and by_year else None
    ok = {"t": a["t"] is not None and a["t"] >= thr,
          "development": (dev["alpha"] or 0) > 0, "validation": (val["alpha"] or 0) > 0,
          "costs_x2": (x2["alpha"] or 0) > 0, "book_pays": (own["mean"] or 0) > 0,
          "top_year": top is not None and top <= 0.5}
    strip = lambda d: {k: v for k, v in d.items() if k != "contributions"}  # noqa: E731
    ws = [r["w"] for r in rows]
    return {"alpha": strip(a), "development": strip(dev), "validation": strip(val), "costs_x2": strip(x2),
            "managed_net": own, "market_net": monthly([r["market"] for r in rows]),
            "managed_max_drawdown": round(drawdown([r["managed"] for r in rows]), 4),
            "market_max_drawdown": round(drawdown([r["market"] for r in rows]), 4),
            "exposure": {"mean": sum(ws) / len(ws) if ws else None, "min": min(ws, default=None),
                         "max": min(max(ws, default=0.0), MAX_EXPOSURE),
                         "months_at_cap": sum(1 for w in ws if w >= MAX_EXPOSURE)},
            "by_year": {str(k): round(v, 5) for k, v in sorted(by_year.items())},
            "top_year_share": None if top is None else round(top, 3), "months": len(rows),
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
    reg.register(Trial(id=PID, registered=now, title="VOLM-1: volatility-managed S&P 500 exposure",
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
    print(body["verdict"], "failed:", res["failed_gates"], "alpha", json.dumps(res["alpha"]), "managed",
          json.dumps(res["managed_net"]), "exposure", json.dumps(res["exposure"]))


def cmd_holdout(now: datetime) -> None:
    reg = _registry()
    frozen = _check_frozen(reg)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    if judged["verdict"] != "PASSED":
        raise SystemExit("VOLM-1 did not pass: the holdout stays unread")
    if any(t.id == HID for t in reg.trials):
        raise SystemExit("the holdout was opened once already")
    reg.register(Trial(id=HID, registered=now, title="VOLM-1 holdout: 2022-01..2026-09", hypothesis=HOLDOUT_RULE,
                       uses=(Use(UNIVERSE, HOLD[0], HOLD[1], "judge"),), tests=1, configurations=1,
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"]}))
    data = load(HOLD[1])
    rows = book(data, *HOLD)
    a = alpha(rows)
    a2 = alpha(book(data, *HOLD, cost=2 * COST, markup=2 * MARKUP_PA))
    own = monthly([r["managed"] for r in rows])
    ok = bool(a["alpha"] and a["alpha"] > 0 and a["t"] is not None and a["t"] >= 1.6448536269514722
              and (a2["alpha"] or 0) > 0 and (own["mean"] or 0) > 0)
    verdict = "PASSED" if ok else "FAILED"
    strip = lambda d: {k: v for k, v in d.items() if k != "contributions"}  # noqa: E731
    body = _write(HID, {"program": HID, "holdout_of": PID, "period": [str(d) for d in HOLD], "alpha": strip(a),
                        "costs_x2": strip(a2), "managed_net": own, "rule": HOLDOUT_RULE,
                        "classification": "VALIDATED" if ok else "REJECTED", "verdict": verdict})
    reg.record_verdict(Verdict(HID, now, verdict, {"artifact": f"research/knowledge/{HID}.json",
                                                   "artifact_sha256": body["sha256"]}))
    print(verdict, json.dumps(strip(a)), "x2", a2["alpha"], "own", own["mean"])


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc)  # the command line's clock: every function above takes its dates as arguments
    {"spec": cmd_spec, "preregister": lambda: cmd_preregister(now), "fetch": cmd_fetch,
     "judge": lambda: cmd_judge(now), "holdout": lambda: cmd_holdout(now)}.get(cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
