"""FXS-1: the time-of-day effect in FX (research/preregistrations/FXS-1.md).

    python scripts/fxs1.py spec | preregister | judge

The hypothesis (Ranaldo 2009, Journal of Banking & Finance; Breedon & Ranaldo 2013, Journal of Money, Credit and
Banking): a currency tends to weaken during its own country's working hours and to firm during foreign working
hours. The mechanism is order flow: people buy foreign currency in their own working hours, which the authors also
see in a market maker's flow. FXS-1 holds each pair only in the hours where the hypothesis says which way it moves,
and is flat otherwise:

    TOKYO   09:00 Tokyo -> 08:00 London        buy USDJPY                               (the yen weakens)
    EUROPE  08:00 London -> 08:00 New York     sell EURUSD, sell GBPUSD, buy USDCHF      (Europe's currencies weaken)
    US      17:00 London -> 16:00 New York     buy EURUSD, buy GBPUSD, sell USDCHF, sell USDJPY (the dollar weakens)

The clock is every input: no price decides a trade, so nothing can look ahead. Windows are computed per date in each
city's own time (daylight saving included).

Data: data/m5 (Dukascopy bid/ask, 2009-2016) through scripts/id1.py's `load`, which refuses the sealed 2017 period.
Costs: the bars' own bid/ask at entry and exit, ID-1's commission (0.7 pip a round trip) and slippage (0.1 pip a
fill), and both stressed x1.5 and x2. No position crosses the 17:00 New York rollover, so neither a standard nor a
swap-free account pays or earns a swap on it.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from aitrader.research.discovery.stats import welch_t  # noqa: E402
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict  # noqa: E402

PID = "FXS-1"
VERSION = "fxs-1.0.0"
R = ROOT / "research"
DOC = "research/preregistrations/FXS-1.md"
SPEC = R / "specs" / "FXS-1.json"
OUT = R / "knowledge"
CODE = ("scripts/fxs1.py",)
UNIVERSE = "fx-majors"

#: window -> ((city, hour) it opens, (city, hour) it closes, {pair: side})
WINDOWS = {
    "TOKYO": (("Asia/Tokyo", 9), ("Europe/London", 8), {"USDJPY": 1}),
    "EUROPE": (("Europe/London", 8), ("America/New_York", 8), {"EURUSD": -1, "GBPUSD": -1, "USDCHF": 1}),
    "US": (("Europe/London", 17), ("America/New_York", 16), {"EURUSD": 1, "GBPUSD": 1, "USDCHF": -1, "USDJPY": -1}),
}
PAIRS = ("EURUSD", "GBPUSD", "USDCHF", "USDJPY")
PERIOD = (date(2009, 1, 1), date(2017, 1, 1))
DEV = (date(2009, 1, 1), date(2014, 1, 1))
VAL = (date(2014, 1, 1), date(2017, 1, 1))
HOLD = (date(2017, 1, 1), date(2022, 7, 9))
MAX_LATE_S = 600  # the first bar at or after a window's edge must open within 10 minutes of it
COMMISSION_PIPS_RT = 0.7  # ID-1's (scripts/id1.py COSTS): about $7 a standard lot
SLIPPAGE_PIPS = 0.1  # per market fill, ID-1's
COST_GRID = (1.0, 1.5, 2.0)
RANDOM_SEEDS = (11, 12, 13)
BOOT_N, BOOT_SEED = 10_000, 7
GATES = {"t": "daily net t over 2009-2016 >= the registry threshold (never below 3.0)",
         "development": "mean daily net > 0 over 2009-2013", "validation": "mean daily net > 0 over 2014-2016",
         "costs_x1.5": "mean daily net > 0 with spread, commission and slippage x1.5",
         "beats_random": "Welch t of net per trade against the same trades with random sides >= 2.0",
         "pairs": "at least 3 of the 4 pairs net > 0", "top_year": "no calendar year above 50% of the total net",
         "bootstrap": "the 95% month-block bootstrap interval of the mean daily net is above 0",
         "profit_factor": "trade-level profit factor >= 1.10",
         "delay": "mean daily net > 0 with every entry and exit one bar (5 minutes) late"}
HOLDOUT_RULE = ("only if every gate passes: fx-majors 2017-01-01 -> 2022-07-09, M5 built then through ID-1's holdout "
                "procedure, opened once as FXS-1-H. Gates: daily net t >= 1.645 (one-sided 5%), mean > 0, costs x1.5 "
                "mean > 0. The edge registry calls it VALIDATED only at a holdout t of 2.5 or more")


# ── the windows ──────────────────────────────────────────────────────────

def _at(d: date, city: str, hour: int) -> int:
    return int(datetime(d.year, d.month, d.day, hour, tzinfo=ZoneInfo(city)).timestamp())


def window_bounds(d: date) -> dict[str, tuple[int, int]]:
    """Each window's [open, close) on date d, in epoch seconds, from each city's own clock."""
    return {w: (_at(d, *o), _at(d, *c)) for w, (o, c, _) in WINDOWS.items()}


# ── trades ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Trade:
    pair: str
    window: str
    day: date
    side: int  # +1 buys the pair, -1 sells it
    t_in: int
    t_out: int
    move_bp: float  # mid to mid, (exit - entry) / entry, basis points: the market's move, whatever the side
    cost_bp: float  # half spread in and out, slippage twice and the commission, basis points of the entry mid

    @property
    def gross_bp(self) -> float:
        return self.side * self.move_bp

    @property
    def net_bp(self) -> float:
        return self.gross_bp - self.cost_bp

    def flipped(self, side: int) -> "Trade":
        """The same trade with another side: the cost does not depend on it (buy at the ask, sell at the bid)."""
        return Trade(self.pair, self.window, self.day, side, self.t_in, self.t_out, self.move_bp, self.cost_bp)


def _bar_at(b, ts: int, delay: int) -> int | None:
    i = int(np.searchsorted(b.t, ts))
    if i >= len(b.t) or b.t[i] - ts > MAX_LATE_S:
        return None
    i += delay
    return i if i < len(b.t) else None


def fill(b, pair: str, window: str, day: date, side: int, i0: int, i1: int, k: float = 1.0) -> Trade:
    """A market order at bar i0's open and its reversal at bar i1's open, on the bar's own bid and ask. Under a stress
    k, the spread widens around the mid, and commission and slippage scale, by k (ID-1's `Costs.stressed`)."""
    slip, comm = SLIPPAGE_PIPS * b.pip * k, COMMISSION_PIPS_RT * b.pip * k

    def quote(j):
        mid, half = (b.bo[j] + b.ao[j]) / 2, (b.ao[j] - b.bo[j]) / 2 * k
        return mid - half, mid + half, mid

    bid0, ask0, m0 = quote(i0)
    bid1, ask1, m1 = quote(i1)
    entry, out = (ask0 + slip, bid1 - slip) if side > 0 else (bid0 - slip, ask1 + slip)
    net = side * (out - entry) - comm
    gross = side * (m1 - m0)
    return Trade(pair, window, day, side, int(b.t[i0]), int(b.t[i1]), (m1 - m0) / m0 * 1e4, (gross - net) / m0 * 1e4)


def make_trades(panel: dict, period: tuple[date, date], k: float = 1.0, delay: int = 0) -> tuple[list[Trade], int]:
    """Every window of every weekday in [start, end) for which both edges have a bar, and no data gap inside."""
    out, skipped = [], 0
    d = period[0]
    while d < period[1]:
        if d.weekday() < 5:
            for w, (t0, t1) in window_bounds(d).items():
                for pair, side in WINDOWS[w][2].items():
                    b = panel.get(pair)
                    if b is None:
                        continue
                    i0, i1 = _bar_at(b, t0, delay), _bar_at(b, t1, delay)
                    if i0 is None or i1 is None or i1 <= i0 or bool(b.gap_after[i0:i1].any()):
                        skipped += 1
                        continue
                    out.append(fill(b, pair, w, d, side, i0, i1, k))
        d += timedelta(days=1)
    return out, skipped


def random_sides(trades: list[Trade], seed: int) -> list[Trade]:
    rng = np.random.default_rng(seed)
    return [t.flipped(int(s)) for t, s in zip(trades, rng.choice([-1, 1], size=len(trades)))]


# ── statistics ───────────────────────────────────────────────────────────

def daily(trades: list[Trade]) -> dict[date, float]:
    """The book's net per day, in basis points of one unit of notional per trade."""
    out: dict[date, float] = {}
    for t in trades:
        out[t.day] = out.get(t.day, 0.0) + t.net_bp
    return dict(sorted(out.items()))


def _series_stats(x: np.ndarray) -> dict:
    n = len(x)
    if n < 2:
        return {"n": n, "mean": float(x.mean()) if n else None, "t": None}
    sd = float(x.std(ddof=1))
    return {"n": n, "mean": round(float(x.mean()), 4), "sd": round(sd, 4),
            "t": round(float(x.mean() / sd * math.sqrt(n)), 3) if sd > 0 else None}


def block_bootstrap(days: dict[date, float], n: int = BOOT_N, seed: int = BOOT_SEED) -> tuple[float, float] | None:
    """A 95% interval for the mean daily net, resampling whole calendar months (their autocorrelation kept)."""
    blocks: dict[tuple[int, int], list[float]] = {}
    for d, v in days.items():
        blocks.setdefault((d.year, d.month), []).append(v)
    if len(blocks) < 2:
        return None
    arr = [np.array(v) for v in blocks.values()]
    rng = np.random.default_rng(seed)
    means = np.empty(n)
    for k in range(n):
        pick = rng.integers(0, len(arr), len(arr))
        means[k] = np.concatenate([arr[i] for i in pick]).mean()
    lo, hi = np.percentile(means, [2.5, 97.5])
    return round(float(lo), 4), round(float(hi), 4)


def summary(trades: list[Trade]) -> dict:
    """Trade-level and day-level figures. Account figures put one unit of the account's equity on every trade, so a
    day's return in % of equity is its net in basis points / 100 (up to four positions at once, in the US window)."""
    if not trades:
        return {"trades": 0}
    net = np.array([t.net_bp for t in trades])
    gross = np.array([t.gross_bp for t in trades])
    cost = np.array([t.cost_bp for t in trades])
    dd = daily(trades)
    x = np.array(list(dd.values()))
    s = _series_stats(x)
    sd = s.get("sd") or 0.0
    down = math.sqrt(float(np.mean(np.minimum(x, 0.0) ** 2))) if len(x) else 0.0
    eq = np.cumsum(x) / 100.0  # % of equity, not compounded
    worst = float(np.max(np.maximum.accumulate(np.r_[0.0, eq]) - np.r_[0.0, eq]))
    vol_pa = sd * math.sqrt(252) / 100.0
    a_year = (s["mean"] or 0.0) * 252 / 100.0
    years: dict[int, list[float]] = {}
    for d, v in dd.items():
        years.setdefault(d.year, []).append(v)
    by_year = {y: {"net_pct": round(sum(v) / 100.0, 3), **_series_stats(np.array(v))} for y, v in sorted(years.items())}
    total = float(x.sum())
    top = max(sum(v) for v in years.values())
    by = {}
    for key in ("pair", "window"):
        groups: dict[str, list[float]] = {}
        for t in trades:
            groups.setdefault(getattr(t, key), []).append(t.net_bp)
        by[key] = {g: {"trades": len(v), "net_bp": round(float(np.mean(v)), 4),
                       "t": _series_stats(np.array(v)).get("t")} for g, v in sorted(groups.items())}
    held = sum(t.t_out - t.t_in for t in trades) / 3600.0
    return {
        "trades": len(trades), "trades_a_year": round(len(trades) / max(1, len(years)), 1),
        "per_trade": {"gross_bp": round(float(gross.mean()), 4), "cost_bp": round(float(cost.mean()), 4),
                      "net_bp": round(float(net.mean()), 4), "won": round(float((net > 0).mean()), 4),
                      "profit_factor": round(float(net[net > 0].sum() / -net[net < 0].sum()), 4)
                      if (net < 0).any() else None},
        "days": s, "sharpe": round(s["mean"] / sd * math.sqrt(252), 3) if sd > 0 else None,
        "sortino": round(s["mean"] / down * math.sqrt(252), 3) if down > 0 else None,
        "a_year_pct": round(a_year, 3),
        "vol_a_year_pct": round(vol_pa, 3), "worst_fall_pct": round(worst, 3),
        "at_10pct_vol": {"a_year_pct": round(a_year / vol_pa * 10, 3) if vol_pa > 0 else None,
                         "worst_fall_pct": round(worst / vol_pa * 10, 3) if vol_pa > 0 else None},
        "hours_held_per_trade": round(held / len(trades), 3),
        "by_year": by_year, "years_positive": round(float(np.mean([v["net_pct"] > 0 for v in by_year.values()])), 3),
        "top_year_share": round(top / total * 100, 3) if total > 0 else None,  # percent of the total net
        "by_pair": by["pair"], "by_window": by["window"],
    }


def in_period(trades: list[Trade], period: tuple[date, date]) -> list[Trade]:
    return [t for t in trades if period[0] <= t.day < period[1]]


def evaluate(panel: dict, t_req: float) -> dict:
    trades, skipped = make_trades(panel, PERIOD)
    main = summary(trades)
    stress = {f"x{k}": summary(make_trades(panel, PERIOD, k=k)[0]) for k in COST_GRID if k != 1.0}
    late = summary(make_trades(panel, PERIOD, delay=1)[0])
    rnd = [t for s in RANDOM_SEEDS for t in random_sides(trades, s)]
    vs = welch_t(np.array([t.net_bp for t in trades]), np.array([t.net_bp for t in rnd]))
    dev, val = summary(in_period(trades, DEV)), summary(in_period(trades, VAL))
    ci = block_bootstrap(daily(trades))
    pairs_pos = sum(1 for v in main["by_pair"].values() if v["net_bp"] > 0)
    gates = {
        "t": (main["days"]["t"] or 0) >= t_req,
        "development": (dev["days"]["mean"] or 0) > 0,
        "validation": (val["days"]["mean"] or 0) > 0,
        "costs_x1.5": (stress["x1.5"]["days"]["mean"] or 0) > 0,
        "beats_random": (vs or 0) >= 2.0,
        "pairs": pairs_pos >= 3,
        "top_year": main["top_year_share"] is not None and main["top_year_share"] <= 50.0,
        "bootstrap": ci is not None and ci[0] > 0,
        "profit_factor": (main["per_trade"]["profit_factor"] or 0) >= 1.10,
        "delay": (late["days"]["mean"] or 0) > 0,
    }
    brief = lambda s: {k: s.get(k) for k in ("trades", "per_trade", "days", "sharpe", "a_year_pct", "worst_fall_pct")}
    return {"threshold_t": round(t_req, 4), "skipped_windows": skipped, "all": main,
            "development": brief(dev), "validation": brief(val),
            "costs_x1.5": brief(stress["x1.5"]), "costs_x2": brief(stress["x2.0"]), "one_bar_late": brief(late),
            "random_sides": {"trades": len(rnd), "net_bp": round(float(np.mean([t.net_bp for t in rnd])), 4),
                             "welch_t_vs_random": round(vs, 3) if vs is not None else None},
            "bootstrap_95": ci, "pairs_positive": pairs_pos, "gates": gates,
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
    return max(3.0, reg.threshold_for_next(UNIVERSE, *PERIOD, new_tests=1))


def spec(reg: Registry) -> dict:
    return {"program": PID, "version": VERSION, "universe": UNIVERSE,
            "question": "does each pair move as the time-of-day hypothesis says inside its window, enough to pay the "
                        "bid/ask, commission and slippage of a market order in and out?",
            "windows": {w: {"opens": o, "closes": c, "trades": t} for w, (o, c, t) in WINDOWS.items()},
            "pairs": PAIRS, "periods": {"judged": [str(d) for d in PERIOD], "development": [str(d) for d in DEV],
                                        "validation": [str(d) for d in VAL], "holdout": [str(d) for d in HOLD]},
            "max_late_s": MAX_LATE_S, "commission_pips_rt": COMMISSION_PIPS_RT, "slippage_pips": SLIPPAGE_PIPS,
            "cost_grid": COST_GRID, "random_seeds": RANDOM_SEEDS, "bootstrap": {"n": BOOT_N, "seed": BOOT_SEED,
                                                                              "block": "calendar month"},
            "gates": GATES, "holdout_rule": HOLDOUT_RULE, "financing": "none: no position crosses 17:00 New York",
            "threshold_t": round(threshold(reg), 4)}


def _frozen(reg: Registry) -> dict:
    """Before registration: the spec recomputed from the registry as it stands must be the frozen one."""
    frozen = json.loads(SPEC.read_text())
    if spec_sha(spec(reg)) != frozen["sha256"] or code_hash() != frozen["code_sha256"]:
        raise SystemExit("the spec or the code differs from what was frozen")
    return frozen


def _registered(reg: Registry) -> dict:
    """After registration: the frozen file must be intact and be what the registry recorded, and the code unchanged.
    (Recomputing the spec here would count FXS-1's own registration in its threshold.)"""
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
    if frozen["sha256"] not in (ROOT / DOC).read_text() or frozen["code_sha256"] not in (ROOT / DOC).read_text():
        raise SystemExit(f"{DOC} must quote the spec and code sha256")
    reg.register(Trial(id=PID, registered=now, title="FXS-1: the time-of-day effect (home currencies weaken in their "
                                                     "own working hours)",
                       hypothesis="Do EURUSD, GBPUSD, USDCHF and USDJPY move as the time-of-day hypothesis says inside "
                                  "its windows, net of measured bid/ask, commission and slippage?",
                       uses=(Use(UNIVERSE, PERIOD[0], PERIOD[1], "judge"),), tests=1, configurations=1,
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"]}))
    print("registered", PID)


def cmd_judge(now: datetime) -> None:
    import id1  # noqa: E402  (its loader refuses the sealed period without the final test's key)

    reg = _registry()
    if not any(t.id == PID for t in reg.trials):
        raise SystemExit(f"{PID} is not registered")
    if reg.verdict_of(PID) is not None:
        raise SystemExit(f"{PID} already has a verdict")
    frozen = _registered(reg)
    panel = {k: v for k, v in id1.load(PERIOD).items() if k in PAIRS}
    if set(panel) != set(PAIRS):
        raise SystemExit(f"missing bars for {sorted(set(PAIRS) - set(panel))}")
    res = evaluate(panel, frozen["spec"]["threshold_t"])
    verdict = "PASSED" if res["passed"] else "FAILED"
    body = {"program": PID, "verdict": verdict, "spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"],
            "periods": frozen["spec"]["periods"], **res}
    body = json.loads(json.dumps(body, sort_keys=True, default=str))
    body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    (OUT / f"{PID}.json").write_text(_dump(body))
    reg.record_verdict(Verdict(trial=PID, recorded=now, status=verdict,
                               result={"t": res["all"]["days"]["t"], "net_bp_per_trade": res["all"]["per_trade"]["net_bp"],
                                       "failed_gates": res["failed_gates"]}))
    a = res["all"]
    print(f"{PID} {verdict}: {a['trades']} trades, {a['per_trade']['net_bp']:+.3f} bp net a trade "
          f"({a['per_trade']['gross_bp']:+.3f} gross, {a['per_trade']['cost_bp']:.3f} cost), daily t {a['days']['t']} "
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
