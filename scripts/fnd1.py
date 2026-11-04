"""FND-1: extreme perpetual funding as crowded leverage, a contrarian signal for BTC and ETH (research/preregistrations/FND-1.md).

The owner, 2026-11-04: "change everything if you must; the most important thing is a profit; don't stop". CR-1 to CR-5
harvested funding (delta-neutral carry) or traded its spread between venues; none used it as a signal for the coins'
direction. Funding is what leveraged longs pay shorts each 8 hours. When it runs far above Binance's baseline of 0.01%
a settlement, long leverage is crowded, and crowded leverage unwinds in liquidations (Schmeling, Schrimpf & Todorov
2023, "Crypto Carry": high carry comes with crash risk). The rule stands aside then.

The rule, fixed before any FND-1 data was fetched:
- each day at the daily close (00:00 UTC), for BTC and ETH: F = the mean of the coin's USDT-M funding settlements
  published in the 7 days before that close (00:00, 08:00 and 16:00 UTC; never the settlement at the decision time);
- F above 0.03% a settlement (three times the baseline, about 33% a year): flat over the next day; otherwise long;
- returns are the coin's spot close to close; each coin gets half the capital; a change of exposure pays 0.15% of the
  notional traded; a day without its prices or without 18 of its 21 settlements is no trade, never filled.

    python scripts/fnd1.py spec          # freeze the design (reads no data)
    python scripts/fnd1.py preregister   # register FND-1 in research/registry.jsonl
    python scripts/fnd1.py fetch         # Binance's public archives, each month checked against its sha256
    python scripts/fnd1.py judge         # 2020-01..2024-06: development, validation, the gates
    python scripts/fnd1.py holdout       # only if FND-1 PASSED: 2024-07..2026-09, once

Each command refuses to run if the code or the spec changed since registration. Nothing here changes the bot.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import zipfile
from bisect import bisect_left
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402
from scripts.xts1 import BASE as KLINES, _get, drawdown, months, parse_month, stats  # noqa: E402

R = ROOT / "research"
PID, HID = "FND-1", "FND-1-H"
DOC = "research/preregistrations/FND-1.md"
SPEC = R / "specs" / "FND-1.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "fnd"
CODE = ("scripts/fnd1.py", "scripts/xts1.py")
UNIVERSE = "crypto-binance-spot"
CRYPTO_UNIVERSES = ("crypto-binance-usdtm", "crypto-binance-usdtm-all", "crypto-xvenue-hl-binance",
                    "crypto-perp-live-xvenue", "crypto-binance-spot")
SYMBOLS = ("BTCUSDT", "ETHUSDT")
FIRST_MONTH, LAST_MONTH = "2019-09", "2026-09"
DEV = (date(2020, 1, 1), date(2022, 7, 1))
VAL = (date(2022, 7, 1), date(2024, 7, 1))
JUDGE = (DEV[0], VAL[1])
HOLD = (date(2024, 7, 1), date(2026, 10, 1))
CROWDED = 0.0003          # a settlement's funding rate: three times Binance's 0.01% baseline
WINDOW_DAYS, MIN_SETTLEMENTS = 7, 18
COST = 0.0015             # per unit of notional traded, each side (as XTS-1)
TESTS = 2                 # the mean's t (G1) and the timing t (G7)
FUNDING = "https://data.binance.vision/data/futures/um/monthly/fundingRate/{s}/{s}-fundingRate-{m}.zip"

GATES = {
    "t": "t of the mean daily net return of the two-coin book over 2020-01..2024-06 >= the threshold",
    "development": "mean daily net > 0 in 2020-01..2022-06",
    "validation": "mean daily net > 0 in 2022-07..2024-06",
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
    earlier = sum(reg.tests_on(u, date(2018, 1, 1), HOLD[1]) for u in CRYPTO_UNIVERSES)
    return max(3.0, bonferroni_t(earlier + TESTS))


def spec(reg: Registry) -> dict:
    return {"program": PID, "question": "is crowded long leverage, read from extreme perpetual funding, followed by "
                                        "weaker bitcoin and ether returns, so that standing aside then beats holding?",
            "symbols": SYMBOLS, "crowded_rate_per_settlement": CROWDED, "window_days": WINDOW_DAYS,
            "min_settlements": MIN_SETTLEMENTS, "cost_per_side": COST,
            "rule": "exposure for the next day = 0 when the mean funding of the 7 days before the close exceeds the "
                    "crowded rate, else 1; spot returns; half the capital per coin; a change of exposure pays the cost; "
                    "a day without its prices or its settlements is no trade",
            "data": "Binance spot daily klines and USDT-M funding settlements (data.binance.vision), monthly archives "
                    "checked against their sha256; a month not fetched or not checked stops the judge, never filled",
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

def parse_funding(data: bytes, checksum: bytes) -> list[tuple[int, float]]:
    """A month's funding archive as (settlement time in UTC seconds, rate), only if its sha256 matches."""
    want = checksum.decode().split()[0].strip().lower()
    if hashlib.sha256(data).hexdigest() != want:
        raise ValueError("sha256 does not match the published checksum")
    z = zipfile.ZipFile(io.BytesIO(data))
    with z.open(z.namelist()[0]) as f:
        rows = [x for x in csv.reader(io.TextIOWrapper(f)) if x and x[0][:1].isdigit()]
    out = []
    for x in rows:
        t = int(float(x[0]))
        t = t // 1_000_000 if t > 10 ** 14 else t // 1000
        rate = float(x[2])
        if rate != rate or abs(rate) > 0.05:
            raise ValueError(f"an implausible funding rate {x[2]!r}")
        out.append((t, rate))
    return out


def cmd_fetch() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    man = {}
    for s in SYMBOLS:
        closes, fund, failed = {}, {}, []
        for m in months(FIRST_MONTH, LAST_MONTH):
            for kind, url in (("klines", KLINES.format(s=s, m=m)), ("funding", FUNDING.format(s=s, m=m))):
                data, chk = _get(url), _get(url + ".CHECKSUM")
                try:
                    if data is None or chk is None:
                        raise ValueError("not fetched")
                    if kind == "klines":
                        closes.update(parse_month(data, chk))
                    else:
                        fund.update(parse_funding(data, chk))
                except Exception as exc:  # noqa: BLE001 - recorded, never filled
                    failed.append({"month": m, "kind": kind, "why": str(exc)})
        (DATA / f"{s}_1d.csv").write_text("date,close\n" + "".join(f"{d},{c!r}\n" for d, c in sorted(closes.items())))
        (DATA / f"{s}_funding.csv").write_text("t,rate\n" + "".join(f"{t},{r!r}\n" for t, r in sorted(fund.items())))
        man[s] = {"days": len(closes), "settlements": len(fund), "failed_months": failed,
                  "sha256": {k: hashlib.sha256((DATA / f"{s}_{k}.csv").read_bytes()).hexdigest()
                             for k in ("1d", "funding")}}
        print(s, len(closes), "days", len(fund), "settlements", "failed", failed)
    (DATA / "manifest.json").write_text(_dump({"retrieved": datetime.now(timezone.utc).isoformat(),
                                               "source": [KLINES, FUNDING], "symbols": man}))


def load(until: date) -> dict:
    """Each coin's closes and settlements, cut at `until` (exclusive): the judge never reads the holdout's."""
    man = json.loads((DATA / "manifest.json").read_text())
    cut = int(datetime.combine(until, datetime.min.time(), tzinfo=timezone.utc).timestamp())
    out = {}
    for s in SYMBOLS:
        bad = [f"{f['month']} {f['kind']}" for f in man["symbols"][s]["failed_months"]
               if "2019-12" <= f["month"] < until.isoformat()[:7]]
        if bad:
            raise SystemExit(f"{s}: months not fetched or not checked: {bad}; nothing is filled")
        with open(DATA / f"{s}_1d.csv") as f:
            next(f)
            closes = {date.fromisoformat(d): float(c) for d, c in (ln.strip().split(",") for ln in f)
                      if date.fromisoformat(d) < until}
        with open(DATA / f"{s}_funding.csv") as f:
            next(f)
            fund = sorted((int(t), float(r)) for t, r in (ln.strip().split(",") for ln in f) if int(t) < cut)
        out[s] = {"closes": closes, "fund_t": [t for t, _ in fund], "fund_r": [r for _, r in fund]}
    return out


# ── the rule, and what it earned ─────────────────────────────────────────

def crowded_mean(coin: dict, d: date) -> float | None:
    """The mean funding of the settlements published in the WINDOW_DAYS before d's close (00:00 UTC of d+1), the
    settlement at that instant excluded. None with fewer than MIN_SETTLEMENTS of them."""
    end = int(datetime.combine(d + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc).timestamp())
    start = end - WINDOW_DAYS * 86400
    ts = coin["fund_t"]
    i, j = bisect_left(ts, start), bisect_left(ts, end)
    rates = coin["fund_r"][i:j]
    return sum(rates) / len(rates) if len(rates) >= MIN_SETTLEMENTS else None


def exposure(coin: dict, d: date) -> float | None:
    f = crowded_mean(coin, d)
    return None if f is None else (0.0 if f > CROWDED else 1.0)


def sleeve(coin: dict, start: date, end: date, cost: float = COST) -> dict[date, dict]:
    """Per day in [start, end): the coin's spot return, the exposure held over it and the net return it earned."""
    closes, out, prev = coin["closes"], {}, None
    d = start - timedelta(days=1)
    while d + timedelta(days=1) < end:
        nxt = d + timedelta(days=1)
        e = exposure(coin, d)
        if e is not None and d in closes and nxt in closes:
            r = closes[nxt] / closes[d] - 1.0
            out[nxt] = {"ret": r, "exp": e, "net": e * r - cost * abs(e - (prev if prev is not None else 0.0))}
            prev = e
        else:
            prev = None
        d = nxt
    return out


def book(data: dict, start: date, end: date, cost: float = COST, coins: tuple = SYMBOLS) -> dict[date, float]:
    sl = [sleeve(data[s], start, end, cost) for s in coins]
    days = set(sl[0]).intersection(*sl[1:]) if len(sl) > 1 else set(sl[0])
    return {d: sum(x[d]["net"] for x in sl) / len(sl) for d in sorted(days)}


def timing(data: dict, start: date, end: date) -> dict[date, float]:
    sl = [sleeve(data[s], start, end) for s in SYMBOLS]
    days = sorted(set(sl[0]).intersection(*sl[1:]))
    avg = [sum(x[d]["exp"] for d in days) / len(days) for x in sl] if days else [0.0] * len(sl)
    return {d: sum(x[d]["net"] - a * x[d]["ret"] for x, a in zip(sl, avg)) / len(sl) for d in days}


def gates(data: dict, thr: float) -> dict:
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
    flat = {c: round(1 - sum(v["exp"] for v in sleeve(data[c], *JUDGE).values())
                     / max(1, len(sleeve(data[c], *JUDGE))), 4) for c in SYMBOLS}
    ok = {"t": s["t"] is not None and s["t"] >= thr,
          "development": (dev["mean"] or 0) > 0, "validation": (val["mean"] or 0) > 0,
          "costs_x2": (x2["mean"] or 0) > 0,
          "leave_one_coin_out": all((alone[c]["mean"] or 0) > 0 for c in SYMBOLS),
          "top_year": top is not None and top <= 0.5,
          "timing": (tm["mean"] or 0) > 0 and tm["t"] is not None and tm["t"] >= 2.0}
    return {"net": s, "development": dev, "validation": val, "costs_x2": x2, "alone": alone,
            "by_year": {str(k): round(v, 4) for k, v in sorted(by_year.items())},
            "top_year_share": None if top is None else round(top, 3), "timing": tm, "share_of_days_flat": flat,
            "max_drawdown": round(drawdown(net), 4), "threshold_t": thr, "gates": ok,
            "failed_gates": [g for g, v in ok.items() if not v], "passed": all(ok.values())}


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
    reg.register(Trial(id=PID, registered=now, title="FND-1: extreme perpetual funding as crowded leverage",
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
    data = load(JUDGE[1])
    res = gates(data, frozen["spec"]["threshold_t"])
    body = _write(PID, {"program": PID, "verdict": "PASSED" if res["passed"] else "FAILED", **res,
                        "periods": frozen["spec"]["periods"], "spec_sha256": frozen["sha256"],
                        "code_sha256": frozen["code_sha256"],
                        "data": json.loads((DATA / "manifest.json").read_text())})
    reg.record_verdict(Verdict(PID, now, body["verdict"], {"artifact": f"research/knowledge/{PID}.json",
                                                           "artifact_sha256": body["sha256"]}))
    print(body["verdict"], "failed:", res["failed_gates"], "net", json.dumps(res["net"]), "timing",
          json.dumps(res["timing"]), "flat", res["share_of_days_flat"])


def cmd_holdout(now: datetime) -> None:
    reg = _registry()
    frozen = _check_frozen(reg)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    if judged["verdict"] != "PASSED":
        raise SystemExit("FND-1 did not pass: the holdout stays unread")
    if any(t.id == HID for t in reg.trials):
        raise SystemExit("the holdout was opened once already")
    reg.register(Trial(id=HID, registered=now, title="FND-1 holdout: 2024-07..2026-09", hypothesis=HOLDOUT_RULE,
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
