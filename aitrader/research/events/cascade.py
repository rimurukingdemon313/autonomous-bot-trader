"""CASC-1: is a liquidation-led crash bought back? (research/preregistrations/CASC-1.md)

When leveraged longs are liquidated, the exchange's engine sells their perpetuals at market: the perpetual falls
below its own spot price, and arbitrageurs who buy the cheap perpetual and sell spot drag spot down with it. That
selling is forced, not informed. Once it ends, spot should recover part of the fall. A fall led by spot itself
(spot falling as fast or faster than the perpetual) is more likely informed and should not recover.

The rule decides at the close of hour h: if a seasoned coin's spot fell at least X over the last four hours and its
perpetual closed at least 0.5% below spot, buy the coin's SPOT at that close and sell 24 hours later. One position
per coin at a time. The judged figure is the trade's own net return: in a market-wide cascade the market's rebound
is part of the mechanism, so it is not subtracted; the coin's drift is controlled instead by the same coin at hours
when it had not fallen (placebo), and the mechanism by falls led by spot (contrast). The return against the
equal-weight market is reported beside it. Nothing here trades.
"""

from __future__ import annotations

import math
import random
from datetime import datetime, timezone

import numpy as np

CASC_VERSION = "casc-1.0.0"
HOUR = 3_600_000
LOOK = 4  # hours over which the fall is measured
HOLD = 24  # hours held


class Panel:
    """Hourly closes on one grid: spot[c, i], perp[c, i] at hour t0 + i (NaN where missing), coins seasoned from
    hour index s[c]."""

    def __init__(self, coins: list[str], t0: int, hours: int, seasoned_ms: dict[str, int]):
        self.coins, self.t0, self.n = list(coins), t0, hours
        self.idx = {c: k for k, c in enumerate(self.coins)}
        self.spot = np.full((len(coins), hours), np.nan)
        self.perp = np.full((len(coins), hours), np.nan)
        self.s = np.array([max(0, (seasoned_ms[c] - t0) // HOUR) for c in self.coins])
        self._mkt: dict[tuple[int, int], float | None] = {}

    def put(self, kind: str, coin: str, closes: dict[int, float]) -> None:
        arr, k = (self.spot if kind == "spot" else self.perp), self.idx[coin]
        for t, v in closes.items():
            i = (t - self.t0) // HOUR
            if 0 <= i < self.n and v > 0:
                arr[k, i] = v

    def market(self, a: int, b: int) -> float | None:
        """Equal-weight spot return from hour a to hour b of every coin seasoned by hour a with both closes."""
        if (a, b) not in self._mkt:
            ok = (self.s <= a) & np.isfinite(self.spot[:, a]) & np.isfinite(self.spot[:, b])
            self._mkt[(a, b)] = float(np.mean(self.spot[ok, b] / self.spot[ok, a] - 1)) if ok.any() else None
        return self._mkt[(a, b)]


def hour_close_times(t0: int, i: int) -> int:
    """The time of the close of grid hour i (its bar ends there)."""
    return t0 + (i + 1) * HOUR


def _falls(p: Panel, k: int, first: int, last: int, drop: float) -> tuple[np.ndarray, np.ndarray]:
    """The decision hours in [first, last] at which coin k's spot had fallen at least `drop` over LOOK hours, with
    the perpetual's premium to spot at each (NaN where a close is missing)."""
    S, P = p.spot[k], p.perp[k]
    lo, hi = max(first, LOOK, int(p.s[k])), min(last, p.n - 1)
    if hi < lo:
        return np.array([], dtype=int), np.array([])
    hs = np.arange(lo, hi + 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        r4 = S[hs] / S[hs - LOOK] - 1
        pr = P[hs] / S[hs] - 1
    ok = np.isfinite(r4) & np.isfinite(pr) & (r4 <= -drop)
    return hs[ok], pr[ok]


def events(p: Panel, first: int, last: int, drop: float, prem: float, cost: float, lag: int = 0) -> list[dict]:
    """Every entry the rule takes with its decision hour in [first, last] (grid indices). Entry at the close of the
    decision hour plus `lag`, exit HOLD hours later. A coin is held once at a time; an entry without a close at
    either end is counted, never filled."""
    out = []
    for k, c in enumerate(p.coins):
        S = p.spot[k]
        hs, prs = _falls(p, k, first, last, drop)
        busy = -1
        for h, pr in zip(hs.tolist(), prs.tolist()):
            if h <= busy or pr > -prem:
                continue
            a, b = h + lag, h + lag + HOLD
            e = {"coin": c, "hour": h, "fall": float(S[h] / S[h - LOOK] - 1), "premium": pr}
            if b >= p.n or not (np.isfinite(S[a]) and np.isfinite(S[b])) or p.market(a, b) is None:
                e["missing"] = True
            else:
                r = float(S[b] / S[a] - 1)
                e.update(ret=r, bench=p.market(a, b), net=r - 2 * cost, excess=r - 2 * cost - p.market(a, b))
            out.append(e)
            busy = h + HOLD - 1
    return out


def contrast(p: Panel, first: int, last: int, drop: float, prem: float, cost: float) -> list[dict]:
    """The same falls led by spot: at no hour of the fall did the perpetual close more than prem/2 below spot, so no
    liquidation selling shows. What the mechanism says should NOT be bought back, measured the same way."""
    out = []
    for k, c in enumerate(p.coins):
        S, P = p.spot[k], p.perp[k]
        hs, _ = _falls(p, k, first, min(last, p.n - 1 - HOLD), drop)
        busy = -1
        for h in hs.tolist():
            if h <= busy:
                continue
            with np.errstate(invalid="ignore", divide="ignore"):
                w = P[h - LOOK:h + 1] / S[h - LOOK:h + 1] - 1
            if not np.all(np.isfinite(w)) or float(np.min(w)) < -prem / 2:
                continue
            m = p.market(h, h + HOLD)
            if np.isfinite(S[h + HOLD]) and m is not None:
                r = float(S[h + HOLD] / S[h] - 1)
                out.append({"coin": c, "hour": h, "net": r - 2 * cost, "excess": r - 2 * cost - m})
                busy = h + HOLD - 1
    return out


def placebos(p: Panel, evs: list[dict], drop: float, cost: float, span: int = 168, draws: int = 40,
             seed: int = 20261115) -> dict[tuple[str, int], list[float]]:
    """For each traded entry, the same coin's 24-hour net return from up to `draws` random hours within a week on
    either side on which it had not fallen (four-hour return above -drop/3)."""
    rng, out = random.Random(seed), {}
    for e in evs:
        if e.get("missing"):
            continue
        k, h = p.idx[e["coin"]], e["hour"]
        S = p.spot[k]
        cand = [x for x in range(max(LOOK, int(p.s[k]), h - span), min(p.n - 1 - HOLD, h + span) + 1)
                if abs(x - h) >= HOLD and np.isfinite(S[x]) and np.isfinite(S[x - LOOK]) and np.isfinite(S[x + HOLD])
                and S[x] / S[x - LOOK] - 1 > -drop / 3]
        out[(e["coin"], h)] = [float(S[x + HOLD] / S[x] - 1) - 2 * cost for x in rng.sample(cand, min(draws, len(cand)))]
    return out


def day_of(p: Panel, h: int) -> str:
    return datetime.fromtimestamp(hour_close_times(p.t0, h) / 1000, timezone.utc).date().isoformat()


def cohorts(p: Panel, evs: list[dict], key: str = "net") -> dict[str, float]:
    """The mean of `key` over the entries decided on each UTC day (cascades cluster in days)."""
    acc: dict[str, list[float]] = {}
    for e in evs:
        acc.setdefault(day_of(p, e["hour"]), []).append(e[key])
    return {d: sum(v) / len(v) for d, v in sorted(acc.items())}


def nw_t(xs: list[float], lag: int = 1) -> tuple[float | None, float | None]:
    n = len(xs)
    if n < 3:
        return (sum(xs) / n if n else None), None
    m = sum(xs) / n
    d = [x - m for x in xs]
    if max(abs(v) for v in d) <= 1e-12 * max(1.0, abs(m)):
        return m, None
    s = sum(v * v for v in d) / n
    for k in range(1, min(lag, n - 1) + 1):
        s += 2 * (1 - k / (lag + 1)) * sum(d[i] * d[i - k] for i in range(k, n)) / n
    return (m, None) if s <= 0 else (m, m / math.sqrt(s / n))


def judge(p: Panel, evs: list[dict], late: list[dict], contra: list[dict], plac: dict, bar: float, cost: float,
          min_events: int, min_days: int, seed: int = 20261115, draws: int = 1000, lag: int = 1) -> dict:
    """One threshold's entries against every preregistered gate; too few is INCONCLUSIVE, never a pass."""
    ok = [e for e in evs if not e.get("missing")]
    c = cohorts(p, ok)
    m, t = nw_t(list(c.values()), lag)
    out = {"entries": len(evs), "traded": len(ok), "missing": len(evs) - len(ok), "days": len(c), "mean_net": m,
           "t": t, "bar": bar}
    if len(ok) < min_events or len(c) < min_days:
        return {**out, "verdict": "INCONCLUSIVE",
                "why": f"{len(ok)} entries on {len(c)} days: {min_events} and {min_days} are needed"}

    def stat(xs, key="net"):
        cc = cohorts(p, xs, key)
        return sum(cc.values()) / len(cc) if cc else None
    ks = list(c)
    h = len(ks) // 2
    first, second = sum(c[k] for k in ks[:h]) / h, sum(c[k] for k in ks[h:]) / (len(ks) - h)
    top = set(sorted(range(len(ok)), key=lambda i: ok[i]["net"], reverse=True)[:5])
    no_top = stat([e for i, e in enumerate(ok) if i not in top])
    best_day = max(c, key=lambda d: c[d] * sum(1 for e in ok if day_of(p, e["hour"]) == d))
    no_day = stat([e for e in ok if day_of(p, e["hour"]) != best_day])
    coins: dict[str, float] = {}
    for e in ok:
        coins[e["coin"]] = coins.get(e["coin"], 0.0) + e["net"]
    bc = max(coins, key=coins.get)
    no_coin = stat([e for e in ok if e["coin"] != bc])
    x2 = stat([{**e, "net": e["net"] - 2 * cost} for e in ok])
    late_ok = [e for e in late if not e.get("missing")]
    lt = stat(late_ok) if late_ok else None
    cm = stat(contra) if contra else None
    rng = random.Random(seed)
    usable = [e for e in ok if plac.get((e["coin"], e["hour"]))]
    days = sorted({day_of(p, e["hour"]) for e in usable})
    pos = {d: i for i, d in enumerate(days)}
    wi = [pos[day_of(p, e["hour"])] for e in usable]
    cnt = [0] * len(days)
    for i in wi:
        cnt[i] += 1
    ds = []
    for _ in range(draws if usable else 0):
        acc = [0.0] * len(days)
        for i, e in zip(wi, usable):
            acc[i] += rng.choice(plac[(e["coin"], e["hour"])])
        ds.append(sum(a / n for a, n in zip(acc, cnt)) / len(days))
    ds.sort()
    p95 = ds[int(0.95 * draws) - 1] if ds else None
    gates = {"t": t is not None and t >= bar, "costs_x2": x2 is not None and x2 > 0,
             "halves": first > 0 and second > 0, "top5_removed": no_top is not None and no_top > 0,
             "late_entry": lt is not None and lt > 0, "beats_placebo": p95 is not None and m is not None and m > p95,
             "without_best_day": no_day is not None and no_day > 0,
             "without_best_coin": no_coin is not None and no_coin > 0,
             "beats_spot_led_falls": cm is not None and m is not None and m > cm}
    xs = sorted(e["net"] for e in ok)
    return {**out, "verdict": "PASSED" if all(gates.values()) else "FAILED", "gates": gates,
            "gross_mean": stat([{**e, "net": e["net"] + 2 * cost} for e in ok]),
            "mean_excess_vs_market": stat(ok, "excess"), "costs_x2_mean": x2, "first_half": first, "second_half": second,
            "without_top5_mean": no_top, "late_mean": lt, "placebo_p95": p95,
            "placebo_share_at_or_above": (sum(d >= m for d in ds) / len(ds)) if ds and m is not None else None,
            "best_day": best_day, "without_best_day_mean": no_day, "best_coin": bc, "without_best_coin_mean": no_coin,
            "spot_led_falls": len(contra), "spot_led_mean_net": cm, "median_net": xs[len(xs) // 2],
            "positive_share": sum(x > 0 for x in xs) / len(xs), "worst_net": xs[0], "best_net": xs[-1],
            "coins": len(coins)}
