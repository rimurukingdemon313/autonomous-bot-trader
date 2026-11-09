"""FXT-1: time-series momentum in the major currencies, on the untouched 1975-1989 years (research/preregistrations/
FXT-1.md).

    python scripts/fxt1.py spec | preregister | judge

The rule (Moskowitz, Ooi & Pedersen 2012, time-series momentum): at each month's turn, hold each currency against the
dollar in the direction of its own past 12 months, sized to a 10% annual volatility from its last 60 daily returns
(at most 3x), equal risk across the currencies that float. It is long or short, and rebalanced monthly. The
1970s-1980s are when currency trend profits were documented (Sweeney 1986; Levich & Thomas 1993), and no test in this
registry has read FX before 1990.

Point in time: H.10 noon New York rates (aitrader/data/h10.py), each usable only from 17:00 New York on the next
business day. A month's decision is taken at 17:00 New York on its first business day, from rates through the last
business day before it, and filled at the next noon rate, the one after the decision. The H.10 store truncates at the
2017 seal unless it is given the final test's key.

Costs: the H.10 rates are mid rates with no bid and ask, so a retail account's cost is declared: 2 bp of notional each
way, for spread, commission and slippage together, x1.5 and x2. Financing: no policy rates exist here before 1988, so
the judge is a swap-free account's (spot only). A standard account's swaps are computed only in the holdout.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data.h10 import H10Store, available_at, fed_holidays  # noqa: E402
from aitrader.research.discovery.stats import welch_t  # noqa: E402
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict  # noqa: E402

PID = "FXT-1"
VERSION = "fxt-1.0.0"
R = ROOT / "research"
DOC = "research/preregistrations/FXT-1.md"
SPEC = R / "specs" / "FXT-1.json"
OUT = R / "knowledge"
CODE = ("scripts/fxt1.py",)
UNIVERSE = "fx-majors"
CURRENCIES = ("GBP", "JPY", "CHF", "CAD", "AUD", "NZD")  # the H.10 majors that exist before 1999 (EUR starts then)
#: a currency is traded only once its whole 12-month look-back lies after it began to float
FLOAT_FROM = {"GBP": date(1972, 6, 23), "JPY": date(1973, 2, 14), "CHF": date(1973, 1, 23), "CAD": date(1970, 6, 1),
              "AUD": date(1983, 12, 12), "NZD": date(1985, 3, 4)}
INVERT = {"JPY", "CHF", "CAD"}  # quoted as units per dollar: inverted to dollars per unit
LOOKBACK_M, VOL_N, TARGET_VOL, MAX_LEV = 12, 60, 0.10, 3.0
PERIOD = (date(1975, 1, 1), date(1990, 1, 1))
DEV = (date(1975, 1, 1), date(1983, 1, 1))
VAL = (date(1983, 1, 1), date(1990, 1, 1))
HOLD = (date(2017, 1, 1), date(2026, 10, 1))
COST_BP = 2.0  # each way, per unit of notional traded
COST_GRID = (1.0, 1.5, 2.0)
RANDOM_SEEDS = (11, 12, 13)
BOOT_N, BOOT_SEED, BOOT_BLOCK = 10_000, 7, 12  # blocks of 12 months
GATES = {"t": "monthly net t over 1975-1989 >= the registry threshold over every earlier FX test (never below 3.0)",
         "development": "mean monthly net > 0 over 1975-1982", "validation": "mean monthly net > 0 over 1983-1989",
         "costs_x2": "mean monthly net > 0 at costs x2 (x1.5 reported)",
         "beats_random": "Welch t of the monthly net against random-sign books of the same sizes >= 2.0",
         "currencies": "at least 60% of the currencies traded are net positive",
         "top_year": "no calendar year above 50% of the total net",
         "bootstrap": "the 95% interval of the mean monthly net from 12-month block bootstrap is above 0",
         "one_month_late": "mean monthly net > 0 with every signal one month old"}
HOLDOUT_RULE = ("only if every gate passes: 2017-01 -> 2026-09 (the H.10 2026-09-29 vintage, with EUR added as the "
                "seventh currency), opened once as FXT-1-H. Gates: mean monthly net > 0 in a swap-free account, and > 0 "
                "at costs x2. A standard account's swaps (BIS policy rates plus a 1.5% a year markup) are reported. The "
                "edge registry calls it VALIDATED only at a holdout t of 2.5 or more")


# ── the calendar ─────────────────────────────────────────────────────────

def is_business(d: date) -> bool:
    return d.weekday() < 5 and d not in fed_holidays(d.year)


def last_business_day(year: int, month: int) -> date:
    d = date(year + month // 12, month % 12 + 1, 1) - timedelta(days=1)
    while not is_business(d):
        d -= timedelta(days=1)
    return d


def months(period: tuple[date, date]) -> list[tuple[int, int]]:
    y, m, out = period[0].year, period[0].month, []
    while date(y, m, 1) < period[1]:
        out.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def _prev(y: int, m: int, k: int = 1) -> tuple[int, int]:
    n = y * 12 + (m - 1) - k
    return n // 12, n % 12 + 1


def decision_time(y: int, m: int) -> int:
    """17:00 New York on month (y, m)'s first business day: the moment the last business day before it is usable."""
    py, pm = _prev(y, m)
    return available_at(last_business_day(py, pm))


# ── prices ───────────────────────────────────────────────────────────────

class Prices:
    """One currency in dollars per unit, by observation date, with each rate's availability time."""

    def __init__(self, ccy: str, dates, values, avail) -> None:
        v = np.asarray(values, float)
        self.ccy, self.dates = ccy, list(dates)
        self.p = 1.0 / v if ccy in INVERT else v
        self.avail = np.asarray(avail, np.int64)
        self.noon = np.asarray([_noon(d) for d in self.dates], np.int64)
        self.ord = np.asarray([d.toordinal() for d in self.dates], np.int64)

    def known_at(self, t: int) -> int:
        """Index of the last rate usable at time t, or -1."""
        return int(np.searchsorted(self.avail, t, side="right")) - 1

    def on_or_before(self, d: date) -> int:
        return int(np.searchsorted(self.ord, d.toordinal(), side="right")) - 1

    def fill_after(self, t: int) -> int | None:
        """The first noon rate observed after time t: where an order decided at t is filled."""
        i = int(np.searchsorted(self.noon, t, side="right"))
        return i if i < len(self.dates) else None


def _noon(d: date) -> int:
    from aitrader.data.h10 import NY
    return int(datetime(d.year, d.month, d.day, 12, tzinfo=NY).timestamp())


def prices_from_store(series: dict) -> dict[str, Prices]:
    return {c: Prices(c, s.dates, s.value, s.available_at) for c, s in series.items() if c in CURRENCIES}


# ── the book ─────────────────────────────────────────────────────────────

def signal(px: Prices, y: int, m: int, vol_scaled: bool = True) -> float | None:
    """The weight for month (y, m), from what is usable at its decision time only; None if the currency is not yet
    tradeable (floating for the whole look-back, with 60 daily returns)."""
    t = decision_time(y, m)
    now = px.known_at(t)
    ly, lm = _prev(y, m, LOOKBACK_M + 1)
    start_day = last_business_day(ly, lm)
    if now < VOL_N or start_day < FLOAT_FROM[px.ccy]:
        return None
    then = px.on_or_before(start_day)
    if then < 0 or then >= now:
        return None
    side = 1.0 if px.p[now] > px.p[then] else -1.0
    if not vol_scaled:
        return side
    r = np.diff(np.log(px.p[now - VOL_N:now + 1]))
    vol = float(r.std(ddof=1) * math.sqrt(252))
    return side * min(MAX_LEV, TARGET_VOL / vol) if vol > 0 else None


def book(prices: dict[str, Prices], period: tuple[date, date], k: float = 1.0, vol_scaled: bool = True,
         late: int = 0, signs=None) -> list[dict]:
    """Monthly rows: the weights decided at the month's start, the month's return per currency from fill to fill, the
    turnover cost and the net. `late` uses signals that many months old; `signs(ccy, y, m)` overrides the side."""
    rows, prev_w = [], {}
    for (y, m) in months(period):
        ny, nm = _prev(y, m, -1)
        t0, t1 = decision_time(y, m), decision_time(ny, nm)
        sy, sm = _prev(y, m, late)
        w = {}
        for c, px in prices.items():
            s = signal(px, sy, sm, vol_scaled)
            if s is None:
                continue
            if signs is not None:
                s = abs(s) * signs(c, y, m)
            w[c] = s
        n = len(w)
        ret, contrib = 0.0, {}
        for c, wc in w.items():
            px = prices[c]
            i0, i1 = px.fill_after(t0), px.fill_after(t1)
            if i0 is None or i1 is None or i1 <= i0:
                continue
            r = px.p[i1] / px.p[i0] - 1.0
            contrib[c] = wc / n * r
            ret += contrib[c]
        scaled = {c: wc / n for c, wc in w.items()} if n else {}
        turnover = sum(abs(scaled.get(c, 0.0) - prev_w.get(c, 0.0)) for c in set(scaled) | set(prev_w))
        cost = turnover * COST_BP * k / 1e4
        rows.append({"month": f"{y:04d}-{m:02d}", "n": n, "weights": scaled, "gross": ret, "cost": cost,
                     "net": ret - cost, "contrib": contrib, "turnover": turnover})
        prev_w = scaled
    return rows


# ── statistics ───────────────────────────────────────────────────────────

def _t(x: np.ndarray) -> float | None:
    if len(x) < 2 or x.std(ddof=1) == 0:
        return None
    return float(x.mean() / x.std(ddof=1) * math.sqrt(len(x)))


def block_bootstrap(x: np.ndarray, block: int = BOOT_BLOCK, n: int = BOOT_N, seed: int = BOOT_SEED):
    if len(x) < 2 * block:
        return None
    rng = np.random.default_rng(seed)
    starts = np.arange(0, len(x) - block + 1)
    k = int(math.ceil(len(x) / block))
    means = np.empty(n)
    for j in range(n):
        idx = np.concatenate([np.arange(s, s + block) for s in rng.choice(starts, k)])[:len(x)]
        means[j] = x[idx].mean()
    lo, hi = np.percentile(means, [2.5, 97.5])
    return round(float(lo), 6), round(float(hi), 6)


def summary(rows: list[dict]) -> dict:
    live = [r for r in rows if r["n"] > 0]
    if not live:
        return {"months": 0}
    x = np.array([r["net"] for r in live])
    g = np.array([r["gross"] for r in live])
    sd = float(x.std(ddof=1)) if len(x) > 1 else 0.0
    down = math.sqrt(float(np.mean(np.minimum(x, 0.0) ** 2)))
    eq = np.r_[0.0, np.cumsum(x)]
    worst = float(np.max(np.maximum.accumulate(eq) - eq))
    years: dict[str, float] = {}
    for r in live:
        years[r["month"][:4]] = years.get(r["month"][:4], 0.0) + r["net"]
    total = float(x.sum())
    per: dict[str, list[float]] = {}
    for r in live:
        for c, v in r["contrib"].items():
            per.setdefault(c, []).append(v)
    flips = sum(1 for a, b in zip(live, live[1:]) for c in set(a["weights"]) & set(b["weights"])
                if np.sign(a["weights"][c]) != np.sign(b["weights"][c]))
    return {
        "months": len(live), "mean": round(float(x.mean()), 6), "gross_mean": round(float(g.mean()), 6),
        "cost_mean": round(float(np.mean([r["cost"] for r in live])), 6), "t": _t(x) and round(_t(x), 3),
        "a_year_pct": round(float(x.mean()) * 1200, 3), "vol_a_year_pct": round(sd * math.sqrt(12) * 100, 3),
        "sharpe": round(float(x.mean()) / sd * math.sqrt(12), 3) if sd > 0 else None,
        "sortino": round(float(x.mean()) / down * math.sqrt(12), 3) if down > 0 else None,
        "worst_fall_pct": round(worst * 100, 3), "months_won": round(float((x > 0).mean()), 4),
        "flips_a_year": round(flips / max(1, len(years)), 2),
        "gross_leverage": round(float(np.mean([sum(abs(v) for v in r["weights"].values()) for r in live])), 3),
        "by_year": {y: round(v * 100, 3) for y, v in sorted(years.items())},
        "years_positive": round(float(np.mean([v > 0 for v in years.values()])), 3),
        "top_year_share": round(max(years.values()) / total * 100, 3) if total > 0 else None,
        "by_currency": {c: {"months": len(v), "contrib_mean": round(float(np.mean(v)), 6),
                            "t": _t(np.array(v)) and round(_t(np.array(v)), 3)} for c, v in sorted(per.items())},
    }


def in_period(rows: list[dict], period: tuple[date, date]) -> list[dict]:
    lo, hi = f"{period[0]:%Y-%m}", f"{period[1]:%Y-%m}"
    return [r for r in rows if lo <= r["month"] < hi]


def random_book(prices, period, seed: int) -> list[dict]:
    rng = np.random.default_rng(seed)
    draws: dict[tuple, int] = {}

    def signs(c, y, m):
        return draws.setdefault((c, y, m), int(rng.choice([-1, 1])))
    return book(prices, period, signs=signs)


def evaluate(prices: dict[str, Prices], t_req: float) -> dict:
    rows = book(prices, PERIOD)
    main = summary(rows)
    x = np.array([r["net"] for r in rows if r["n"] > 0])
    stress = {f"x{k}": summary(book(prices, PERIOD, k=k)) for k in COST_GRID if k != 1.0}
    late = summary(book(prices, PERIOD, late=1))
    plain = summary(book(prices, PERIOD, vol_scaled=False))
    rnd = [r for s in RANDOM_SEEDS for r in random_book(prices, PERIOD, s) if r["n"] > 0]
    vs = welch_t(x, np.array([r["net"] for r in rnd]))
    dev, val = summary(in_period(rows, DEV)), summary(in_period(rows, VAL))
    ci = block_bootstrap(x)
    cur = main["by_currency"]
    pos = sum(1 for v in cur.values() if v["contrib_mean"] > 0)
    gates = {"t": (main["t"] or 0) >= t_req, "development": (dev.get("mean") or 0) > 0,
             "validation": (val.get("mean") or 0) > 0, "costs_x2": (stress["x2.0"].get("mean") or 0) > 0,
             "beats_random": (vs or 0) >= 2.0, "currencies": bool(cur) and pos / len(cur) >= 0.6,
             "top_year": main["top_year_share"] is not None and main["top_year_share"] <= 50.0,
             "bootstrap": ci is not None and ci[0] > 0, "one_month_late": (late.get("mean") or 0) > 0}
    brief = lambda s: {k: s.get(k) for k in ("months", "mean", "t", "a_year_pct", "sharpe", "worst_fall_pct")}
    return {"threshold_t": round(t_req, 4), "all": main, "development": brief(dev), "validation": brief(val),
            "costs_x1.5": brief(stress["x1.5"]), "costs_x2": brief(stress["x2.0"]), "one_month_late": brief(late),
            "equal_notional": brief(plain),
            "random_signs": {"months": len(rnd), "mean": round(float(np.mean([r["net"] for r in rnd])), 6),
                             "welch_t_vs_random": round(vs, 3) if vs is not None else None},
            "bootstrap_95": ci, "currencies_positive": pos, "gates": gates,
            "failed_gates": [g for g, ok in gates.items() if not ok], "passed": all(gates.values())}


# ── the program ──────────────────────────────────────────────────────────

def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True, default=str).encode()).hexdigest()


def _dump(x) -> str:
    return json.dumps(x, indent=1, sort_keys=True, default=str) + "\n"


def _registry() -> Registry:
    return Registry.load(R / "registry.jsonl", Holdout.load(R / "holdout.json"))


def threshold(reg: Registry) -> float:
    """Every earlier test on FX data counts, whatever its years (as TRND-1 counted every test on index data)."""
    return max(3.0, reg.threshold_for_next(UNIVERSE, new_tests=1))


def spec(reg: Registry) -> dict:
    return {"program": PID, "version": VERSION, "universe": UNIVERSE,
            "question": "did the major currencies' own 12-month trends, traded monthly at equal risk, earn a positive "
                        "net return in 1975-1989, years no test here has read?",
            "currencies": CURRENCIES, "float_from": {k: str(v) for k, v in FLOAT_FROM.items()},
            "lookback_months": LOOKBACK_M, "vol_days": VOL_N, "target_vol": TARGET_VOL, "max_leverage": MAX_LEV,
            "periods": {"judged": [str(d) for d in PERIOD], "development": [str(d) for d in DEV],
                        "validation": [str(d) for d in VAL], "holdout": [str(d) for d in HOLD]},
            "cost_bp_each_way": COST_BP, "cost_grid": COST_GRID, "financing": "none in the judge (swap-free account)",
            "random_seeds": RANDOM_SEEDS, "bootstrap": {"n": BOOT_N, "seed": BOOT_SEED, "block_months": BOOT_BLOCK},
            "gates": GATES, "holdout_rule": HOLDOUT_RULE, "threshold_t": round(threshold(reg), 4)}


def _frozen(reg: Registry) -> dict:
    frozen = json.loads(SPEC.read_text())
    if spec_sha(spec(reg)) != frozen["sha256"] or code_hash() != frozen["code_sha256"]:
        raise SystemExit("the spec or the code differs from what was frozen")
    return frozen


def _registered(reg: Registry) -> dict:
    frozen = json.loads(SPEC.read_text())
    if spec_sha(frozen["spec"]) != frozen["sha256"]:
        raise SystemExit(f"{SPEC} was edited after it was frozen")
    if reg.get(PID).design.get("spec_sha256") != frozen["sha256"] or code_hash() != frozen["code_sha256"]:
        raise SystemExit("the spec or the code differs from what was registered")
    return frozen


def cmd_spec() -> None:
    reg = _registry()
    if any(t.id == PID for t in reg.trials):
        raise SystemExit(f"{PID} is registered; its spec is frozen")
    s = spec(reg)
    SPEC.write_text(_dump({"spec": s, "sha256": spec_sha(s), "code_sha256": code_hash()}))
    print(spec_sha(s), "code", code_hash(), "threshold", s["threshold_t"])


def cmd_preregister(now: datetime) -> None:
    reg = _registry()
    frozen = _frozen(reg)
    text = (ROOT / DOC).read_text()
    if frozen["sha256"] not in text or frozen["code_sha256"] not in text:
        raise SystemExit(f"{DOC} must quote the spec and code sha256")
    reg.register(Trial(id=PID, registered=now, title="FXT-1: time-series momentum in the major currencies, 1975-1989",
                       hypothesis="Did each major currency's own 12-month trend, traded monthly at equal risk against "
                                  "the dollar, earn a positive net return over 1975-1989?",
                       uses=(Use(UNIVERSE, PERIOD[0], PERIOD[1], "judge"),), tests=1, configurations=1,
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"]}))
    print("registered", PID)


def cmd_judge(now: datetime) -> None:
    reg = _registry()
    if not any(t.id == PID for t in reg.trials):
        raise SystemExit(f"{PID} is not registered")
    if reg.verdict_of(PID) is not None:
        raise SystemExit(f"{PID} already has a verdict")
    frozen = _registered(reg)
    series = H10Store(ROOT / "data" / "h10", Holdout.load(R / "holdout.json")).load()  # sealed at 2017
    prices = prices_from_store(series)
    res = evaluate(prices, frozen["spec"]["threshold_t"])
    verdict = "PASSED" if res["passed"] else "FAILED"
    a = res["all"]
    body = {"program": PID, "verdict": verdict, "spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"],
            "periods": frozen["spec"]["periods"], **res,
            # the edge registry's single-program form: the statistic is the mean net monthly return
            "months": {"n": a.get("months"), "mean": a.get("mean"), "t": a.get("t")},
            "worst_fall": (a.get("worst_fall_pct") or 0) / 100, "by_year": a.get("by_year")}
    body = json.loads(json.dumps(body, sort_keys=True, default=str))
    body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    (OUT / f"{PID}.json").write_text(_dump(body))
    reg.record_verdict(Verdict(trial=PID, recorded=now, status=verdict,
                               result={"t": a["t"], "a_year_pct": a["a_year_pct"], "failed_gates": res["failed_gates"]}))
    print(f"{PID} {verdict}: {a['months']} months, {a['a_year_pct']:+.2f}% a year net, Sharpe {a['sharpe']}, t {a['t']} "
          f"against {res['threshold_t']}; failed: {res['failed_gates']}")


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    if cmd == "spec":
        cmd_spec()
    elif cmd == "preregister":
        cmd_preregister(now)
    elif cmd == "judge":
        cmd_judge(now)
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
