"""XTS-1: time-series momentum in bitcoin and ether, after costs (research/preregistrations/XTS-1.md).

The owner, 2026-11-04: "change everything if you must; the most important thing is a profit; don't stop". The project
tested about 50 ideas on FX, equity indices and crypto funding; none survived costs since 2008. Momentum in crypto
prices was never tested here. The literature finds it strong at horizons of one to four weeks (Liu & Tsyvinski 2021,
"Risks and Returns of Cryptocurrency"), and a market dominated by retail flows is where such an effect could last.

The rule, fixed before any XTS-1 data was fetched:
- each day at the daily close (00:00 UTC), for BTC and ETH: the share of the lookbacks 7, 14 and 28 days over which
  the close rose (0, 1/3, 2/3 or 1) is the exposure held over the next day, long or flat, never short;
- each coin gets half the capital; a change of exposure pays 0.15% of the notional traded (a 0.10% taker fee and
  0.05% of spread and slippage);
- a day without its price (the close, or the close a lookback before) is no trade, never filled.

    python scripts/xts1.py spec          # freeze the design (reads no data)
    python scripts/xts1.py preregister   # register XTS-1 in research/registry.jsonl
    python scripts/xts1.py fetch         # Binance's public daily klines, each month checked against its sha256
    python scripts/xts1.py judge         # 2018-01..2024-06: development, validation, the gates
    python scripts/xts1.py holdout       # only if XTS-1 PASSED: 2024-07..2026-09, once

Each command refuses to run if the code or the spec changed since registration. Nothing here changes the bot.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sys
import time
import urllib.error
import urllib.request
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402

R = ROOT / "research"
PID, HID = "XTS-1", "XTS-1-H"
DOC = "research/preregistrations/XTS-1.md"
SPEC = R / "specs" / "XTS-1.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "xts"
CODE = ("scripts/xts1.py",)
UNIVERSE = "crypto-binance-spot"
#: every earlier crypto test counts against this one's threshold (the same coins, other signals)
CRYPTO_UNIVERSES = ("crypto-binance-usdtm", "crypto-binance-usdtm-all", "crypto-xvenue-hl-binance",
                    "crypto-perp-live-xvenue", UNIVERSE)
SYMBOLS = ("BTCUSDT", "ETHUSDT")
FIRST_MONTH, LAST_MONTH = "2017-09", "2026-09"
DEV = (date(2018, 1, 1), date(2022, 1, 1))
VAL = (date(2022, 1, 1), date(2024, 7, 1))
JUDGE = (DEV[0], VAL[1])
HOLD = (date(2024, 7, 1), date(2026, 10, 1))
LOOKBACKS = (7, 14, 28)
COST = 0.0015            # per unit of notional traded, each side
CFD_FINANCING_PA = 0.20  # a retail CFD's overnight financing on the exposure held: reported, never a gate
TESTS = 2                # the mean's t (G1) and the timing t (G7)
BASE = "https://data.binance.vision/data/spot/monthly/klines/{s}/1d/{s}-1d-{m}.zip"
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader xts1)"}

GATES = {
    "t": "t of the mean daily net return of the two-coin book over 2018-01..2024-06 >= the threshold",
    "development": "mean daily net > 0 in 2018..2021",
    "validation": "mean daily net > 0 in 2022-01..2024-06",
    "costs_x2": "mean daily net > 0 with the cost doubled",
    "leave_one_coin_out": "mean daily net > 0 for BTC alone and for ETH alone",
    "top_year": "no calendar year supplies more than 50% of the total net",
    "timing": "the book beats holding each coin at its own average exposure: mean daily difference > 0 with t >= 2.0",
}
HOLDOUT_RULE = ("2024-07..2026-09: mean daily net > 0 with one-sided t >= 1.645, mean daily net > 0 with the cost "
                "doubled, and the timing difference's mean > 0")


def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()


def threshold(reg: Registry) -> float:
    earlier = sum(reg.tests_on(u, JUDGE[0], HOLD[1]) for u in CRYPTO_UNIVERSES)
    return max(3.0, bonferroni_t(earlier + TESTS))


def spec(reg: Registry) -> dict:
    return {"program": PID, "question": "does time-series momentum in bitcoin and ether earn a positive net return, "
                                        "and beat holding them at the same average exposure?",
            "symbols": SYMBOLS, "lookbacks_days": LOOKBACKS, "cost_per_side": COST,
            "cfd_financing_pa_reported_only": CFD_FINANCING_PA,
            "rule": "exposure for the next day = share of the lookbacks over which the close rose (long or flat); "
                    "half the capital per coin; a change of exposure pays the cost on the notional traded; a day "
                    "without its prices is no trade",
            "data": "Binance spot daily klines (data.binance.vision), monthly archives checked against their sha256; "
                    "a month that cannot be fetched or checked stops the judge, never filled",
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

def months(a: str, b: str) -> list[str]:
    y, m = map(int, a.split("-"))
    out = []
    while f"{y:04d}-{m:02d}" <= b:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def _get(url: str, tries: int = 6) -> bytes | None:
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
        except Exception:  # noqa: BLE001 - retried, then recorded as failed
            pass
        time.sleep(min(60, 2 * 2 ** k))
    return None


def parse_month(data: bytes, checksum: bytes) -> list[tuple[str, float]]:
    """A month's archive as (UTC date, close), only if its sha256 matches the published one; else ValueError."""
    want = checksum.decode().split()[0].strip().lower()
    if hashlib.sha256(data).hexdigest() != want:
        raise ValueError("sha256 does not match the published checksum")
    z = zipfile.ZipFile(io.BytesIO(data))
    with z.open(z.namelist()[0]) as f:
        rows = [x for x in csv.reader(io.TextIOWrapper(f)) if x and x[0][:1].isdigit()]
    out = []
    for x in rows:
        t = int(float(x[0]))
        t = t // 1_000_000 if t > 10 ** 14 else t // 1000  # microseconds from 2025, milliseconds before
        close = float(x[4])
        if not (close > 0 and math.isfinite(close)):
            raise ValueError(f"an invalid close {x[4]!r}")
        out.append((datetime.fromtimestamp(t, timezone.utc).date().isoformat(), close))
    return out


def cmd_fetch() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for s in SYMBOLS:
        closes, failed = {}, []
        for m in months(FIRST_MONTH, LAST_MONTH):
            url = BASE.format(s=s, m=m)
            data, chk = _get(url), _get(url + ".CHECKSUM")
            try:
                if data is None or chk is None:
                    raise ValueError("not fetched")
                for d, c in parse_month(data, chk):
                    closes[d] = c
            except Exception as exc:  # noqa: BLE001 - recorded, never filled
                failed.append({"month": m, "why": str(exc)})
        rows = sorted(closes.items())
        with open(DATA / f"{s}_1d.csv", "w") as f:
            f.write("date,close\n" + "".join(f"{d},{c!r}\n" for d, c in rows))
        manifest[s] = {"days": len(rows), "first": rows[0][0] if rows else None, "last": rows[-1][0] if rows else None,
                       "failed_months": failed,
                       "sha256": hashlib.sha256((DATA / f"{s}_1d.csv").read_bytes()).hexdigest()}
        print(s, manifest[s]["days"], "days", manifest[s]["first"], "..", manifest[s]["last"], "failed", failed)
    (DATA / "manifest.json").write_text(_dump({"retrieved": datetime.now(timezone.utc).isoformat(),
                                               "source": BASE, "symbols": manifest}))


def load(until: date) -> dict[str, dict[date, float]]:
    """Each coin's daily closes, cut at `until` (exclusive): the judge never reads the holdout's prices."""
    man = json.loads((DATA / "manifest.json").read_text())
    out = {}
    for s in SYMBOLS:
        bad = [f["month"] for f in man["symbols"][s]["failed_months"] if f["month"] < until.isoformat()[:7]
               and f["month"] >= "2017-12"]
        if bad:
            raise SystemExit(f"{s}: months not fetched or not checked: {bad}; nothing is filled")
        with open(DATA / f"{s}_1d.csv") as f:
            next(f)
            out[s] = {date.fromisoformat(d): float(c) for d, c in (ln.strip().split(",") for ln in f)
                      if date.fromisoformat(d) < until}
    return out


# ── the rule, and what it earned ─────────────────────────────────────────

def exposure(closes: dict[date, float], d: date) -> float | None:
    """The exposure held over day d+1, known at d's close: the share of LOOKBACKS over which the close rose. None when
    a close it needs is missing."""
    c = closes.get(d)
    past = [closes.get(d - timedelta(days=L)) for L in LOOKBACKS]
    if c is None or any(p is None for p in past):
        return None
    return sum(1.0 for p in past if c > p) / len(LOOKBACKS)


def sleeve(closes: dict[date, float], start: date, end: date, cost: float = COST,
           financing_pa: float = 0.0) -> dict[date, dict]:
    """Per day in [start, end): the coin's return, the exposure held over it and the net return it earned."""
    out, prev = {}, None
    d = start - timedelta(days=1)
    while d + timedelta(days=1) < end:
        e, nxt = exposure(closes, d), d + timedelta(days=1)
        if e is not None and nxt in closes:
            r = closes[nxt] / closes[d] - 1.0
            traded = abs(e - (prev if prev is not None else 0.0))
            out[nxt] = {"ret": r, "exp": e, "net": e * r - cost * traded - e * financing_pa / 365.0}
            prev = e
        else:
            prev = None  # no trade that day: the next one starts from flat, and pays to enter
        d = nxt
    return out


def book(data: dict, start: date, end: date, cost: float = COST, financing_pa: float = 0.0,
         coins: tuple = SYMBOLS) -> dict[date, float]:
    """The book's daily net return: the mean of the coins' sleeves, on the days every coin has its price."""
    sl = [sleeve(data[s], start, end, cost, financing_pa) for s in coins]
    days = set(sl[0]).intersection(*sl[1:]) if len(sl) > 1 else set(sl[0])
    return {d: sum(x[d]["net"] for x in sl) / len(sl) for d in sorted(days)}


def timing(data: dict, start: date, end: date) -> dict[date, float]:
    """Each day, the book's net minus holding each coin at its own average exposure over the period (the beta it
    carried, without its timing)."""
    sl = [sleeve(data[s], start, end) for s in SYMBOLS]
    days = sorted(set(sl[0]).intersection(*sl[1:]))
    avg = [sum(x[d]["exp"] for d in days) / len(days) for x in sl] if days else [0.0] * len(sl)
    return {d: sum(x[d]["net"] - a * x[d]["ret"] for x, a in zip(sl, avg)) / len(sl) for d in days}


def stats(xs: list[float]) -> dict:
    n = len(xs)
    if n < 2:
        return {"n": n, "mean": xs[0] if xs else None, "t": None}
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    return {"n": n, "mean": m, "t": m / (sd / math.sqrt(n)) if sd > 0 else None, "sd": sd,
            "annual_return": m * 365, "annual_sharpe": (m / sd) * math.sqrt(365) if sd > 0 else None}


def drawdown(daily: dict[date, float]) -> float:
    eq = peak = 1.0
    worst = 0.0
    for d in sorted(daily):
        eq *= 1 + daily[d]
        peak = max(peak, eq)
        worst = min(worst, eq / peak - 1)
    return worst


def gates(data: dict, thr: float) -> dict:
    """Every gate on the judged period, and what each read."""
    net = book(data, *JUDGE)
    x = list(net.values())
    s = stats(x)
    dev, val = stats([v for d, v in net.items() if d < VAL[0]]), stats([v for d, v in net.items() if d >= VAL[0]])
    x2 = stats(list(book(data, *JUDGE, cost=2 * COST).values()))
    alone = {c: stats(list(book(data, *JUDGE, coins=(c,)).values())) for c in SYMBOLS}
    by_year: dict = {}
    for d, v in net.items():
        by_year[d.year] = by_year.get(d.year, 0.0) + v
    total = sum(x)
    top = max(by_year.values()) / total if total > 0 else None
    tm = stats(list(timing(data, *JUDGE).values()))
    cfd = stats(list(book(data, *JUDGE, financing_pa=CFD_FINANCING_PA).values()))
    hold = {c: stats([data[c][d + timedelta(days=1)] / data[c][d] - 1 for d in sorted(data[c])
                      if JUDGE[0] <= d + timedelta(days=1) < JUDGE[1] and d + timedelta(days=1) in data[c]])
            for c in SYMBOLS}
    ok = {"t": s["t"] is not None and s["t"] >= thr,
          "development": (dev["mean"] or 0) > 0, "validation": (val["mean"] or 0) > 0,
          "costs_x2": (x2["mean"] or 0) > 0,
          "leave_one_coin_out": all((alone[c]["mean"] or 0) > 0 for c in SYMBOLS),
          "top_year": top is not None and top <= 0.5,
          "timing": (tm["mean"] or 0) > 0 and tm["t"] is not None and tm["t"] >= 2.0}
    return {"net": s, "development": dev, "validation": val, "costs_x2": x2, "alone": alone,
            "by_year": {str(k): round(v, 4) for k, v in sorted(by_year.items())},
            "top_year_share": None if top is None else round(top, 3), "timing": tm,
            "max_drawdown": round(drawdown(net), 4), "reported_cfd_financing": cfd, "buy_and_hold": hold,
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
    reg.register(Trial(id=PID, registered=now, title="XTS-1: time-series momentum in bitcoin and ether",
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
    data = load(JUDGE[1])  # cut at the holdout: its prices are never read here
    res = gates(data, frozen["spec"]["threshold_t"])
    body = _write(PID, {"program": PID, "verdict": "PASSED" if res["passed"] else "FAILED", **res,
                        "periods": frozen["spec"]["periods"], "spec_sha256": frozen["sha256"],
                        "code_sha256": frozen["code_sha256"],
                        "data": json.loads((DATA / "manifest.json").read_text())})
    reg.record_verdict(Verdict(PID, now, body["verdict"], {"artifact": f"research/knowledge/{PID}.json",
                                                           "artifact_sha256": body["sha256"]}))
    print(body["verdict"], "failed:", res["failed_gates"], "net", json.dumps(res["net"]), "timing",
          json.dumps(res["timing"]))


def cmd_holdout(now: datetime) -> None:
    reg = _registry()
    frozen = _check_frozen(reg)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    if judged["verdict"] != "PASSED":
        raise SystemExit("XTS-1 did not pass: the holdout stays unread")
    if any(t.id == HID for t in reg.trials):
        raise SystemExit("the holdout was opened once already")
    reg.register(Trial(id=HID, registered=now, title="XTS-1 holdout: 2024-07..2026-09", hypothesis=HOLDOUT_RULE,
                       uses=(Use(UNIVERSE, HOLD[0], HOLD[1], "judge"),), tests=1, configurations=1,
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"]}))
    data = load(HOLD[1])
    net, x2 = book(data, *HOLD), book(data, *HOLD, cost=2 * COST)
    s, s2, tm = stats(list(net.values())), stats(list(x2.values())), stats(list(timing(data, *HOLD).values()))
    ok = bool(s["mean"] and s["mean"] > 0 and s["t"] is not None and s["t"] >= NormalDist().inv_cdf(0.95)
              and (s2["mean"] or 0) > 0 and (tm["mean"] or 0) > 0)
    verdict = "PASSED" if ok else "FAILED"
    body = _write(HID, {"program": HID, "holdout_of": PID, "period": [str(d) for d in HOLD], "net": s, "costs_x2": s2,
                        "timing": tm, "max_drawdown": round(drawdown(net), 4), "rule": HOLDOUT_RULE,
                        "classification": "VALIDATED" if ok else "REJECTED", "verdict": verdict})
    reg.record_verdict(Verdict(HID, now, verdict, {"artifact": f"research/knowledge/{HID}.json",
                                                   "artifact_sha256": body["sha256"]}))
    print(verdict, json.dumps(s), "x2", s2["mean"], "timing", tm["mean"])


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc)  # the command line's clock: every function above takes its dates as arguments
    {"spec": cmd_spec, "preregister": lambda: cmd_preregister(now), "fetch": cmd_fetch,
     "judge": lambda: cmd_judge(now), "holdout": lambda: cmd_holdout(now)}.get(cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
