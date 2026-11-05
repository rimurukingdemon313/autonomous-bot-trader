"""EMC-1: emerging-market currency carry (research/preregistrations/EMC-1.md).

The owner, 2026-11-05: "don't fixate on the AI trading; anything that makes us a profit; never stop". A currency whose
interest rate is high does not, on average, fall by as much as its rate differential: holding it against the dollar
has paid the differential on average, as pay for the risk that it crashes in a crisis (Lustig & Verdelhan 2007;
Burnside, Eichenbaum, Kleshchelski & Rebelo 2011; Menkhoff, Sarno, Schmeling & Schrimpf 2012). No test here has used
emerging currencies. EMC-1 asks whether the carry of the six that a CFD broker quotes paid since 2005, at a CFD's
costs.

The rule, fixed before any EMC-1 price or rate was read (scripts/emc_probe.py read only which sources answer):
- the currencies: MXN, ZAR, TRY, PLN, HUF, CZK against the dollar (Yahoo's daily closes, units per dollar);
- at each month's last close common to all six, the differential of each = its central bank's policy rate minus the
  Fed's, both as the BIS publishes them (WS_CBPOL daily, the value in force that day, at most 10 days old);
- the book holds the three with the largest differential (ties by name), long against the dollar, a third each, until
  the next month's common last close;
- it earns the spot move and the differential known at the month's start, by calendar days; it pays a CFD's swap
  markup of 2.5% a year on what it holds, and each currency's spread on what it trades (the month's drift included);
- a month with a rate unknown for any of the seven is no trade, never filled.

    python scripts/emc1.py spec          # freeze the design (reads no data)
    python scripts/emc1.py preregister   # register EMC-1 in research/registry.jsonl
    python scripts/emc1.py fetch         # Yahoo closes and the BIS policy rates (on GitHub's runner)
    python scripts/emc1.py judge         # 2005-02..2019-12: development, validation, the gates
    python scripts/emc1.py holdout       # only if EMC-1 PASSED: 2020-01..2026-09, once

Each command refuses to run if the code or the spec changed since registration. Nothing here changes the bot.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sys
import urllib.request
import zipfile
from bisect import bisect_right
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402

R = ROOT / "research"
PID, HID = "EMC-1", "EMC-1-H"
DOC = "research/preregistrations/EMC-1.md"
SPEC = R / "specs" / "EMC-1.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "emc"
CODE = ("scripts/emc1.py",)
UNIVERSE = "em-fx-daily"
#: currency -> (Yahoo symbol, BIS area, spread cost each side)
CURRENCIES = {"MXN": ("MXN=X", "MX", 0.0003), "ZAR": ("ZAR=X", "ZA", 0.0006), "TRY": ("TRY=X", "TR", 0.0015),
              "PLN": ("PLN=X", "PL", 0.0005), "HUF": ("HUF=X", "HU", 0.0006), "CZK": ("CZK=X", "CZ", 0.0005)}
USD_AREA = "US"
DEV = (date(2005, 2, 1), date(2013, 1, 1))
VAL = (date(2013, 1, 1), date(2020, 1, 1))
JUDGE = (DEV[0], VAL[1])
HOLD = (date(2020, 1, 1), date(2026, 10, 1))
HELD = 3
MARKUP_PA = 0.025
RATE_STALE_DAYS = 10
TESTS = 1
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader EMC-1)"}
BIS_BULK = "https://data.bis.org/static/bulk/WS_CBPOL_csv_flat.zip"

GATES = {
    "t": "t of the mean monthly net return of the carry book, 2005-02..2019-12, >= the threshold",
    "development": "mean monthly net > 0 in 2005-02..2012",
    "validation": "mean monthly net > 0 in 2013..2019",
    "costs_x2": "mean monthly net > 0 with the spreads and the markup doubled",
    "leave_one_out": "the rule run without any one of the six currencies still earns a mean monthly net > 0",
    "top_year": "no calendar year supplies more than 50% of the total net",
}
HOLDOUT_RULE = ("2020-01..2026-09: mean monthly net > 0 with one-sided t >= 1.645, and > 0 with the spreads and the "
                "markup doubled")


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
    return {"program": PID, "question": "does holding the three highest-yielding of six emerging currencies against "
                                        "the dollar, monthly, earn a positive net return after a CFD's costs?",
            "currencies": {k: {"yahoo": v[0], "bis_area": v[1], "spread_each_side": v[2]}
                           for k, v in CURRENCIES.items()},
            "held": HELD, "markup_pa": MARKUP_PA, "rate_stale_days": RATE_STALE_DAYS,
            "rule": "at each month's last close common to all six, rank by policy-rate differential against the Fed "
                    "(BIS WS_CBPOL, in force that day); hold the top three, a third each, long against the dollar, "
                    "to the next common month-end; earn the spot move and the differential by calendar days; pay "
                    "the markup on what is held and each spread on what is traded",
            "data": "Yahoo daily closes (units per dollar, dated by the source's own calendar); the BIS WS_CBPOL bulk "
                    "file, its daily rows for the seven areas; each file's sha256 in the manifest",
            "periods": {"development": [str(d) for d in DEV], "validation": [str(d) for d in VAL],
                        "holdout": [str(d) for d in HOLD]},
            "gates": GATES, "holdout_rule": HOLDOUT_RULE, "threshold_t": round(threshold(reg), 4), "tests": TESTS,
            "after": {"PASSED and VALIDATED": "proposed to the owner as a paper strategy of its own (rule 14), on the "
                                              "broker's USD pairs, sized by the risk engine, followed forward on "
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

def _get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read()


def _yahoo(sym: str) -> list[tuple[str, float]]:
    res = json.loads(_get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1=1070236800"
                          f"&period2={int(datetime.now(timezone.utc).timestamp())}&interval=1d"))["chart"]["result"][0]
    tz = ZoneInfo(res["meta"]["exchangeTimezoneName"])
    rows = {}
    for t, c in zip(res["timestamp"], res["indicators"]["quote"][0]["close"]):
        if c is not None and math.isfinite(c) and c > 0:
            rows[datetime.fromtimestamp(t, timezone.utc).astimezone(tz).date().isoformat()] = float(c)
    return sorted(rows.items())


def parse_bis(raw: bytes, areas) -> dict[str, list[tuple[str, float]]]:
    """The daily rows of the BIS WS_CBPOL flat file for `areas`, as (date, percent). The file's columns and values are
    "CODE:Label"; only the code is read."""
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    cols = reader.fieldnames or []
    col = {k: next((c for c in cols if c == k or c.startswith(k + ":")), k)
           for k in ("FREQ", "REF_AREA", "TIME_PERIOD", "OBS_VALUE")}
    out: dict[str, list] = {a: [] for a in areas}
    for r in reader:
        area = (r.get(col["REF_AREA"]) or "").split(":")[0].strip()
        if area not in out or (r.get(col["FREQ"]) or "").split(":")[0].strip() != "D":
            continue
        t, v = (r.get(col["TIME_PERIOD"]) or "").strip(), (r.get(col["OBS_VALUE"]) or "").strip()
        try:
            x = float(v)
        except ValueError:
            continue
        if t and math.isfinite(x):
            out[area].append((t, x))
    return {a: sorted(v) for a, v in out.items()}


def cmd_fetch() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    man: dict = {"retrieved": datetime.now(timezone.utc).isoformat(), "series": {}}
    for ccy, (sym, _, _) in CURRENCIES.items():
        rows = _yahoo(sym)
        body = "date,close\n" + "".join(f"{d},{v!r}\n" for d, v in rows)
        (DATA / f"{ccy}.csv").write_text(body)
        man["series"][ccy] = {"file": f"{ccy}.csv", "rows": len(rows), "first": rows[0][0], "last": rows[-1][0],
                              "sha256": hashlib.sha256(body.encode()).hexdigest()}
        print(ccy, man["series"][ccy]["first"], man["series"][ccy]["last"], len(rows), flush=True)
    raw = _get(BIS_BULK)
    z = zipfile.ZipFile(io.BytesIO(raw))
    areas = [v[1] for v in CURRENCIES.values()] + [USD_AREA]
    rates = parse_bis(z.read(z.namelist()[0]), areas)
    body = "area,date,rate\n" + "".join(f"{a},{d},{v!r}\n" for a in areas for d, v in rates[a])
    (DATA / "rates.csv").write_text(body)
    man["rates"] = {"file": "rates.csv", "source": BIS_BULK, "zip_sha256": hashlib.sha256(raw).hexdigest(),
                    "sha256": hashlib.sha256(body.encode()).hexdigest(),
                    "areas": {a: {"rows": len(rates[a]), "first": rates[a][0][0] if rates[a] else None,
                                  "last": rates[a][-1][0] if rates[a] else None} for a in areas}}
    print("rates", json.dumps(man["rates"]["areas"]), flush=True)
    (DATA / "manifest.json").write_text(_dump(man))


def load(until: date) -> dict:
    """The closes and the rates before `until`, only if each file matches its manifest: the judge never reads the
    holdout."""
    man = json.loads((DATA / "manifest.json").read_text())
    out: dict = {"fx": {}, "rates": {}}
    for ccy, m in man["series"].items():
        body = (DATA / m["file"]).read_text()
        if hashlib.sha256(body.encode()).hexdigest() != m["sha256"]:
            raise SystemExit(f"{m['file']} does not match its manifest: nothing is judged on it")
        rows = [ln.split(",") for ln in body.strip().splitlines()[1:]]
        out["fx"][ccy] = {date.fromisoformat(d): float(c) for d, c in rows if date.fromisoformat(d) < until}
    body = (DATA / man["rates"]["file"]).read_text()
    if hashlib.sha256(body.encode()).hexdigest() != man["rates"]["sha256"]:
        raise SystemExit("rates.csv does not match its manifest: nothing is judged on it")
    for ln in body.strip().splitlines()[1:]:
        a, d, v = ln.split(",")
        if date.fromisoformat(d) < until:
            out["rates"].setdefault(a, []).append((date.fromisoformat(d), float(v)))
    for a in out["rates"]:
        out["rates"][a].sort()
    return out


# ── the rule, and what it earned ─────────────────────────────────────────

def rate_at(series: list[tuple[date, float]], d: date) -> float | None:
    """The policy rate in force on d (the last published on or before d), or None if it is over RATE_STALE_DAYS old."""
    i = bisect_right(series, (d, math.inf)) - 1
    if i < 0 or d - series[i][0] > timedelta(days=RATE_STALE_DAYS):
        return None
    return series[i][1]


def month_ends(fx: dict) -> list[date]:
    """The last day of each month on which all six have a close."""
    common = sorted(set.intersection(*(set(v) for v in fx.values())))
    ends: dict = {}
    for d in common:
        ends[(d.year, d.month)] = d
    return [ends[k] for k in sorted(ends)]


def book(data: dict, start: date, end: date, cost_x: float = 1.0, exclude: tuple = ()) -> list[dict]:
    """Per month whose holding ends in [start, end): what the book held and earned, net."""
    fx, rates = data["fx"], data["rates"]
    ccys = [c for c in CURRENCIES if c not in exclude]
    ends = month_ends({c: fx[c] for c in CURRENCIES})
    out: list[dict] = []
    drift: dict[str, float] = {}
    for t0, t1 in zip(ends, ends[1:]):
        month = date(t1.year, t1.month, 1)
        if not start <= month < end:
            continue
        us = rate_at(rates.get(USD_AREA, []), t0)
        diffs = {c: rate_at(rates.get(CURRENCIES[c][1], []), t0) for c in CURRENCIES}
        if us is None or any(v is None for v in diffs.values()):
            drift = {}  # no trade: the next month starts from flat and pays to enter
            continue
        diff = {c: diffs[c] - us for c in ccys}
        held = sorted(ccys, key=lambda c: (-diff[c], c))[:HELD]
        days = (t1 - t0).days
        ret = {c: fx[c][t0] / fx[c][t1] - 1.0 + diff[c] / 100.0 * days / 365.0 for c in held}
        target = {c: 1.0 / len(held) for c in held}
        traded = {c: abs(target.get(c, 0.0) - drift.get(c, 0.0)) for c in set(target) | set(drift)}
        cost = sum(v * CURRENCIES[c][2] for c, v in traded.items()) + MARKUP_PA * days / 365.0
        gross = sum(w * ret[c] for c, w in target.items())
        spot = sum(w * (fx[c][t0] / fx[c][t1] - 1.0) for c, w in target.items())
        out.append({"month": month, "held": held, "gross": gross, "spot": spot, "carry": gross - spot,
                    "net": gross - cost_x * cost})
        drift = {c: w * (1 + ret[c]) / (1 + gross) for c, w in target.items()} if gross > -1 else {}
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
    x = [r["net"] for r in rows]
    s = monthly(x)
    dev = monthly([r["net"] for r in rows if r["month"] < VAL[0]])
    val = monthly([r["net"] for r in rows if r["month"] >= VAL[0]])
    x2 = monthly([r["net"] for r in book(data, *JUDGE, cost_x=2.0)])
    loo = {c: monthly([r["net"] for r in book(data, *JUDGE, exclude=(c,))])["mean"] for c in CURRENCIES}
    by_year: dict = {}
    for r in rows:
        by_year[r["month"].year] = by_year.get(r["month"].year, 0.0) + r["net"]
    total = sum(x)
    top = max(by_year.values()) / total if total > 0 and by_year else None
    ok = {"t": s["t"] is not None and s["t"] >= thr,
          "development": (dev["mean"] or 0) > 0, "validation": (val["mean"] or 0) > 0,
          "costs_x2": (x2["mean"] or 0) > 0, "leave_one_out": all((v or 0) > 0 for v in loo.values()),
          "top_year": top is not None and top <= 0.5}
    held: dict = {}
    for r in rows:
        for c in r["held"]:
            held[c] = held.get(c, 0) + 1
    return {"net": s, "development": dev, "validation": val, "costs_x2": x2, "leave_one_out_means": loo,
            "spot_part": monthly([r["spot"] for r in rows]), "carry_part": monthly([r["carry"] for r in rows]),
            "max_drawdown": round(drawdown(x), 4), "worst_month": round(min(x), 4) if x else None,
            "months": len(rows), "months_held": dict(sorted(held.items(), key=lambda kv: (-kv[1], kv[0]))),
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
    reg.register(Trial(id=PID, registered=now, title="EMC-1: emerging-market currency carry", hypothesis=s["question"],
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
    print(body["verdict"], "failed:", res["failed_gates"], "net", json.dumps(res["net"]), "months", res["months"],
          "held", json.dumps(res["months_held"]))


def cmd_holdout(now: datetime) -> None:
    reg = _registry()
    frozen = _check_frozen(reg)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    if judged["verdict"] != "PASSED":
        raise SystemExit("EMC-1 did not pass: the holdout stays unread")
    if any(t.id == HID for t in reg.trials):
        raise SystemExit("the holdout was opened once already")
    reg.register(Trial(id=HID, registered=now, title="EMC-1 holdout: 2020-01..2026-09", hypothesis=HOLDOUT_RULE,
                       uses=(Use(UNIVERSE, HOLD[0], HOLD[1], "judge"),), tests=1, configurations=1,
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"]}))
    data = load(HOLD[1])
    s = monthly([r["net"] for r in book(data, *HOLD)])
    s2 = monthly([r["net"] for r in book(data, *HOLD, cost_x=2.0)])
    ok = bool(s["mean"] and s["mean"] > 0 and s["t"] is not None and s["t"] >= 1.6448536269514722
              and (s2["mean"] or 0) > 0)
    verdict = "PASSED" if ok else "FAILED"
    body = _write(HID, {"program": HID, "holdout_of": PID, "period": [str(d) for d in HOLD], "net": s, "costs_x2": s2,
                        "rule": HOLDOUT_RULE, "classification": "VALIDATED" if ok else "REJECTED", "verdict": verdict})
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
