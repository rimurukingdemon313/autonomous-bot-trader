"""LVOL-1: the low-volatility anomaly through its ETFs (research/preregistrations/LVOL-1.md).

The owner, 2026-11-05: "don't fixate on the AI trading; anything that makes us a profit; never stop". Stocks that move
less have earned about as much as those that move more, so per unit of risk they have earned more: investors who
cannot borrow buy risky stocks to reach for return and overpay for them (Black 1972; Ang, Hodrick, Xing & Zhang 2006;
Frazzini & Pedersen 2014, "Betting Against Beta"). Since 2011 two ETFs have held the low-volatility side of the S&P
500 and the US market (SPLV, USMV). No test here has used them. LVOL-1 asks whether they beat the S&P 500 at its own
risk, since 2012, held as a retail CFD holds them.

The rule, fixed before any LVOL-1 data was fetched:
- the book holds SPLV and USMV, half each, traded back to half each at every month's last close common to all three
  funds (0.05% of what is traded);
- its monthly excess return: its return, minus the T-bill yield known at the month's start (^IRX, at most 7 days old)
  and a CFD's 2.5% a year markup, by calendar days; SPY's the same way;
- the question: the alpha of the book on SPY (OLS, White standard errors), as in VOLM-1.

    python scripts/lvol1.py spec          # freeze the design (reads no data)
    python scripts/lvol1.py preregister   # register LVOL-1 in research/registry.jsonl
    python scripts/lvol1.py fetch         # Yahoo daily closes (on GitHub's runner: Yahoo is blocked here)
    python scripts/lvol1.py judge         # 2012..2020: development, validation, the gates
    python scripts/lvol1.py holdout       # only if LVOL-1 PASSED: 2021-01..2026-09, once

Each command refuses to run if the code or the spec changed since registration. Nothing here changes the bot.
"""

from __future__ import annotations

import hashlib
import json
import sys
from bisect import bisect_right
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402
from scripts.volm1 import _yahoo, alpha, monthly  # noqa: E402

R = ROOT / "research"
PID, HID = "LVOL-1", "LVOL-1-H"
DOC = "research/preregistrations/LVOL-1.md"
SPEC = R / "specs" / "LVOL-1.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "lvol"
CODE = ("scripts/lvol1.py", "scripts/volm1.py")
UNIVERSE = "us-equity-etf"
#: every earlier test on S&P 500 or US equity data counts against this one's threshold
EQUITY_UNIVERSES = ("multi-asset-etf", "multi-asset-long", "equity-index-b", "us-vol-etp", UNIVERSE)
LOW_VOL, MARKET, RATE = ("SPLV", "USMV"), "SPY", "^IRX"
DEV = (date(2012, 1, 1), date(2017, 1, 1))
VAL = (date(2017, 1, 1), date(2021, 1, 1))
JUDGE = (DEV[0], VAL[1])
HOLD = (date(2021, 1, 1), date(2026, 10, 1))
COST = 0.0005
MARKUP_PA = 0.025
RATE_STALE_DAYS = 7
TESTS = 1

GATES = {
    "t": "White t of the book's monthly alpha on SPY, 2012..2020, >= the threshold",
    "development": "alpha > 0 in 2012..2016",
    "validation": "alpha > 0 in 2017..2020",
    "costs_x2": "alpha > 0 with the trading cost and the markup doubled",
    "each_fund": "SPLV alone and USMV alone each have an alpha > 0",
    "top_year": "no calendar year supplies more than 50% of the total alpha",
}
HOLDOUT_RULE = "2021-01..2026-09: alpha > 0 with one-sided White t >= 1.645, and alpha > 0 with the costs doubled"


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
    return {"program": PID, "question": "do the US low-volatility ETFs (SPLV, USMV) earn a positive alpha on the S&P "
                                        "500 at its own risk, held as a retail CFD holds them?",
            "book": list(LOW_VOL), "market": MARKET, "rate": RATE, "cost_per_unit_traded": COST,
            "markup_pa": MARKUP_PA,
            "rule": "half SPLV, half USMV, traded back to half each at every common month-end; monthly excess "
                    "returns net of the T-bill yield known at the month's start, the markup and the cost; OLS alpha "
                    "on SPY's excess return, White standard errors",
            "data": "Yahoo daily closes adjusted for dividends and splits, ^IRX as published; each file's sha256 in "
                    "the manifest",
            "periods": {"development": [str(d) for d in DEV], "validation": [str(d) for d in VAL],
                        "holdout": [str(d) for d in HOLD]},
            "gates": GATES, "holdout_rule": HOLDOUT_RULE, "threshold_t": round(threshold(reg), 4), "tests": TESTS,
            "after": {"PASSED and VALIDATED": "proposed to the owner as a paper strategy of its own (rule 14), if the "
                                              "broker quotes the funds, sized by the risk engine, followed forward on "
                                              "paper; never real money",
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

def cmd_fetch() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    man = {}
    for sym in (*LOW_VOL, MARKET, RATE):
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


def month_ends(data: dict) -> list[date]:
    common = sorted(set.intersection(*(set(data[s]) for s in (*LOW_VOL, MARKET))))
    ends: dict = {}
    for d in common:
        ends[(d.year, d.month)] = d
    return [ends[k] for k in sorted(ends)]


def book(data: dict, start: date, end: date, cost_x: float = 1.0, funds: tuple = LOW_VOL) -> list[dict]:
    """Per month whose holding ends in [start, end): the book's and the market's net excess returns."""
    rate, rate_days = data[RATE], sorted(data[RATE])
    out: list[dict] = []
    drift: dict[str, float] = {}
    ends = month_ends(data)
    for t0, t1 in zip(ends, ends[1:]):
        month = date(t1.year, t1.month, 1)
        if not start <= month < end:
            continue
        y = known_rate(rate, rate_days, t0)
        if y is None:
            drift = {}
            continue
        days = (t1 - t0).days
        fin = (y / 100.0 + cost_x * MARKUP_PA) * days / 365.0
        rets = {s: data[s][t1] / data[s][t0] - 1.0 for s in (*funds, MARKET)}
        target = {s: 1.0 / len(funds) for s in funds}
        traded = sum(abs(target.get(s, 0.0) - drift.get(s, 0.0)) for s in set(target) | set(drift))
        gross = sum(w * rets[s] for s, w in target.items())
        out.append({"month": month, "managed": gross - fin - cost_x * COST * traded, "market": rets[MARKET] - fin})
        drift = {s: w * (1 + rets[s]) / (1 + gross) for s, w in target.items()} if gross > -1 else {}
    return out


def gates(data: dict, thr: float) -> dict:
    rows = book(data, *JUDGE)
    a = alpha(rows)
    dev = alpha([r for r in rows if r["month"] < VAL[0]])
    val = alpha([r for r in rows if r["month"] >= VAL[0]])
    x2 = alpha(book(data, *JUDGE, cost_x=2.0))
    each = {s: alpha(book(data, *JUDGE, funds=(s,))) for s in LOW_VOL}
    by_year: dict = {}
    for r, c in zip(rows, a.get("contributions") or []):
        by_year[r["month"].year] = by_year.get(r["month"].year, 0.0) + c
    total = sum(by_year.values())
    top = max(by_year.values()) / total if total > 0 and by_year else None
    ok = {"t": a["t"] is not None and a["t"] >= thr,
          "development": (dev["alpha"] or 0) > 0, "validation": (val["alpha"] or 0) > 0,
          "costs_x2": (x2["alpha"] or 0) > 0, "each_fund": all((v["alpha"] or 0) > 0 for v in each.values()),
          "top_year": top is not None and top <= 0.5}
    strip = lambda d: {k: v for k, v in d.items() if k != "contributions"}  # noqa: E731
    return {"alpha": strip(a), "development": strip(dev), "validation": strip(val), "costs_x2": strip(x2),
            "each_fund": {s: strip(v) for s, v in each.items()},
            "book_net": monthly([r["managed"] for r in rows]), "market_net": monthly([r["market"] for r in rows]),
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
    reg.register(Trial(id=PID, registered=now, title="LVOL-1: the low-volatility anomaly through its ETFs",
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
    print(body["verdict"], "failed:", res["failed_gates"], "alpha", json.dumps(res["alpha"]), "months", res["months"])


def cmd_holdout(now: datetime) -> None:
    reg = _registry()
    frozen = _check_frozen(reg)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    if judged["verdict"] != "PASSED":
        raise SystemExit("LVOL-1 did not pass: the holdout stays unread")
    if any(t.id == HID for t in reg.trials):
        raise SystemExit("the holdout was opened once already")
    reg.register(Trial(id=HID, registered=now, title="LVOL-1 holdout: 2021-01..2026-09", hypothesis=HOLDOUT_RULE,
                       uses=(Use(UNIVERSE, HOLD[0], HOLD[1], "judge"),), tests=1, configurations=1,
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"]}))
    data = load(HOLD[1])
    a, a2 = alpha(book(data, *HOLD)), alpha(book(data, *HOLD, cost_x=2.0))
    ok = bool(a["alpha"] and a["alpha"] > 0 and a["t"] is not None and a["t"] >= 1.6448536269514722
              and (a2["alpha"] or 0) > 0)
    verdict = "PASSED" if ok else "FAILED"
    strip = lambda d: {k: v for k, v in d.items() if k != "contributions"}  # noqa: E731
    body = _write(HID, {"program": HID, "holdout_of": PID, "period": [str(d) for d in HOLD], "alpha": strip(a),
                        "costs_x2": strip(a2), "rule": HOLDOUT_RULE,
                        "classification": "VALIDATED" if ok else "REJECTED", "verdict": verdict})
    reg.record_verdict(Verdict(HID, now, verdict, {"artifact": f"research/knowledge/{HID}.json",
                                                   "artifact_sha256": body["sha256"]}))
    print(verdict, json.dumps(strip(a)))


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc)  # the command line's clock: every function above takes its dates as arguments
    {"spec": cmd_spec, "preregister": lambda: cmd_preregister(now), "fetch": cmd_fetch,
     "judge": lambda: cmd_judge(now), "holdout": lambda: cmd_holdout(now)}.get(cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
