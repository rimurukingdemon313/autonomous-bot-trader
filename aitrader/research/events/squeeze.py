"""SQZ-1: do crowded shorts pay the spot buyer? (research/preregistrations/SQZ-1.md)

When a perpetual's funding stays deeply negative, its shorts are paying its longs to keep their positions: short
interest is crowded, and crowded shorts are covered in squeezes (liquidations and stops buy at any price). A spot
buyer pays and receives no funding and uses no leverage; if crowded shorts are, on average, forced out faster than
they are proved right, the coin's spot price beats the market over the following days, in a right-skewed way.

The rule decides at 00:00 UTC of day d from what is known then: the funding settled on the coin's USDT-M perpetual
in the 72 hours before, as an 8-hour rate. If it is at most -theta, buy the coin's SPOT at that moment (the close of
day d-1) and sell it seven days later (the close of day d+6). One position per coin at a time. The test measures
the trade against the equal-weight spot return of every seasoned coin over the same seven days. Nothing here
trades.
"""

from __future__ import annotations

import math
import random
from bisect import bisect_left
from datetime import date, datetime, timedelta, timezone

SQZ_VERSION = "sqz-1.0.0"
HOUR = 3_600_000
DAY = 86_400_000
WINDOW = 72 * HOUR
#: the funding settled in the window must cover at least this much of it, or the day has no signal
MIN_COVER = 48 * HOUR


def day_ms(d: str) -> int:
    return int(datetime.fromisoformat(d).replace(tzinfo=timezone.utc).timestamp() * 1000)


def iso(t: int) -> str:
    return datetime.fromtimestamp(t / 1000, timezone.utc).date().isoformat()


def plus(d: str, n: int) -> str:
    return (date.fromisoformat(d) + timedelta(days=n)).isoformat()


class Funding:
    """A contract's settlements, for fast window sums."""

    def __init__(self, settle: list[tuple[int, float]]):
        settle = sorted(settle)
        self.t = [x for x, _ in settle]
        self.pf, self.pg = [0.0], [0]
        for k, (x, f) in enumerate(settle):
            self.pf.append(self.pf[-1] + f)
            self.pg.append(self.pg[-1] + (min(x - self.t[k - 1], 9 * HOUR) if k else 0))  # a long gap is not cover

    def signal(self, at: int) -> float | None:
        """The funding a long paid in the 72 hours before `at` (settled from at-72h on, strictly before `at`), per 8
        hours: nine 8-hourly settlements make 72 hours. None when they cover less than 48 of those hours."""
        i, j = bisect_left(self.t, at - WINDOW), bisect_left(self.t, at)
        if j <= i or self.pg[j] - self.pg[i] < MIN_COVER:
            return None
        return (self.pf[j] - self.pf[i]) * 8 / 72


def ret(closes: dict[str, float], a: str, b: str) -> float | None:
    """The spot return from the close of day a to the close of day b, or None when either close is missing."""
    if a in closes and b in closes and closes[a] > 0:
        return closes[b] / closes[a] - 1
    return None


class Bench:
    """The equal-weight return, from the close of a to the close of b, of every coin seasoned by day a (cached)."""

    def __init__(self, spot: dict[str, dict[str, float]], seasoned: dict[str, str]):
        self.spot, self.seasoned, self.cache = spot, seasoned, {}

    def __call__(self, a: str, b: str) -> float | None:
        if (a, b) not in self.cache:
            rs = [r for c, xs in self.spot.items() if self.seasoned.get(c, "9999") <= a for r in [ret(xs, a, b)]
                  if r is not None]
            self.cache[(a, b)] = sum(rs) / len(rs) if rs else None
        return self.cache[(a, b)]


def events(fund: dict[str, Funding], spot: dict[str, dict[str, float]], seasoned: dict[str, str], bench: Bench,
           first: str, last: str, theta: float, cost: float, hold: int = 7, lag: int = 0) -> list[dict]:
    """Every entry the rule takes in [first, last]: entry at the close of day d-1+lag, exit `hold` days later.
    A coin is held at most once at a time. Entries without a close at either end are counted, never filled."""
    out = []
    for c in sorted(fund):
        if c not in spot or c not in seasoned:
            continue
        busy_until = ""
        d = first
        while d <= last:
            if d >= seasoned[c] and d > busy_until:
                f = fund[c].signal(day_ms(d))
                if f is not None and f <= -theta:
                    a, b = plus(d, -1 + lag), plus(d, -1 + lag + hold)
                    r, m = ret(spot[c], a, b), bench(a, b)
                    e = {"coin": c, "day": d, "signal": f, "entry": a, "exit": b}
                    if r is None or m is None:
                        e["missing"] = True
                    else:
                        e.update(ret=r, bench=m, net=r - 2 * cost, excess=r - 2 * cost - m)
                    out.append(e)
                    busy_until = plus(d, hold - 1)
            d = plus(d, 1)
    return out


def placebos(fund: dict[str, Funding], spot: dict[str, dict[str, float]], seasoned: dict[str, str], bench: Bench,
             evs: list[dict], theta: float, cost: float, hold: int = 7, span: int = 30) -> dict[tuple[str, str], list[float]]:
    """For each traded entry, the same coin's excess return over the same holding period from every day within
    `span` days on which its shorts were not crowded (signal above -theta/2): what the coin did without the signal."""
    out = {}
    for e in evs:
        if e.get("missing"):
            continue
        c, xs = e["coin"], []
        for k in range(-span, span + 1):
            d = plus(e["day"], k)
            if abs(k) < hold or d < seasoned[c]:
                continue
            f = fund[c].signal(day_ms(d))
            if f is None or f <= -theta / 2:
                continue
            a, b = plus(d, -1), plus(d, hold - 1)
            r, m = ret(spot[c], a, b), bench(a, b)
            if r is not None and m is not None:
                xs.append(r - 2 * cost - m)
        out[(c, e["day"])] = xs
    return out


def week(d: str) -> str:
    y, w, _ = date.fromisoformat(d).isocalendar()
    return f"{y:04d}-W{w:02d}"


def cohorts(evs: list[dict], key: str = "excess") -> dict[str, float]:
    acc: dict[str, list[float]] = {}
    for e in evs:
        acc.setdefault(week(e["day"]), []).append(e[key])
    return {k: sum(v) / len(v) for k, v in sorted(acc.items())}


def nw_t(xs: list[float], lag: int = 2) -> tuple[float | None, float | None]:
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


def _stat(evs: list[dict], key: str = "excess") -> float | None:
    c = cohorts(evs, key)
    return sum(c.values()) / len(c) if c else None


def judge(evs: list[dict], late: list[dict], plac: dict, bar: float, cost: float, min_events: int, min_weeks: int,
          seed: int = 20261115, draws: int = 1000, lag: int = 2) -> dict:
    """One threshold's entries against every preregistered gate; too few is INCONCLUSIVE, never a pass."""
    ok = [e for e in evs if not e.get("missing")]
    c = cohorts(ok)
    m, t = nw_t(list(c.values()), lag)
    out = {"entries": len(evs), "traded": len(ok), "missing": len(evs) - len(ok), "weeks": len(c), "mean_excess": m,
           "t": t, "bar": bar}
    if len(ok) < min_events or len(c) < min_weeks:
        return {**out, "verdict": "INCONCLUSIVE",
                "why": f"{len(ok)} entries in {len(c)} weeks: {min_events} and {min_weeks} are needed"}
    ks = list(c)
    h = len(ks) // 2
    first, second = sum(c[k] for k in ks[:h]) / h, sum(c[k] for k in ks[h:]) / (len(ks) - h)
    top = set(sorted(range(len(ok)), key=lambda i: ok[i]["excess"], reverse=True)[:5])
    no_top = _stat([e for i, e in enumerate(ok) if i not in top])
    years: dict[str, float] = {}
    coins: dict[str, float] = {}
    for e in ok:
        years[e["day"][:4]] = years.get(e["day"][:4], 0.0) + e["excess"]
        coins[e["coin"]] = coins.get(e["coin"], 0.0) + e["excess"]
    by, bc = max(years, key=years.get), max(coins, key=coins.get)
    no_year = _stat([e for e in ok if e["day"][:4] != by])
    no_coin = _stat([e for e in ok if e["coin"] != bc])
    x2 = _stat([{**e, "excess": e["excess"] - 2 * cost} for e in ok])
    late_ok = [e for e in late if not e.get("missing")]
    lt = _stat(late_ok) if late_ok else None
    rng = random.Random(seed)
    usable = [e for e in ok if plac.get((e["coin"], e["day"]))]
    keys = sorted({week(e["day"]) for e in usable})
    pos = {k: i for i, k in enumerate(keys)}
    wi = [pos[week(e["day"])] for e in usable]
    cnt = [0] * len(keys)
    for i in wi:
        cnt[i] += 1
    ds = []
    for _ in range(draws if usable else 0):
        acc = [0.0] * len(keys)
        for i, e in zip(wi, usable):
            acc[i] += rng.choice(plac[(e["coin"], e["day"])])
        ds.append(sum(a / n for a, n in zip(acc, cnt)) / len(keys))
    ds.sort()
    p95 = ds[int(0.95 * draws) - 1] if ds else None
    gates = {"t": t is not None and t >= bar, "costs_x2": x2 is not None and x2 > 0,
             "halves": first > 0 and second > 0, "top5_removed": no_top is not None and no_top > 0,
             "late_entry": lt is not None and lt > 0, "beats_placebo": p95 is not None and m is not None and m > p95,
             "without_best_year": no_year is not None and no_year > 0,
             "without_best_coin": no_coin is not None and no_coin > 0}
    xs = sorted(e["excess"] for e in ok)
    return {**out, "verdict": "PASSED" if all(gates.values()) else "FAILED", "gates": gates,
            "gross_mean_excess": _stat([{**e, "excess": e["excess"] + 2 * cost} for e in ok]),
            "mean_net_long_only": _stat(ok, "net"), "costs_x2_mean": x2, "first_half": first, "second_half": second,
            "without_top5_mean": no_top, "late_mean": lt, "placebo_p95": p95, "placebo_usable": len(usable),
            "placebo_share_at_or_above": (sum(d >= m for d in ds) / len(ds)) if ds and m is not None else None,
            "best_year": by, "without_best_year_mean": no_year, "best_coin": bc, "without_best_coin_mean": no_coin,
            "median_excess": xs[len(xs) // 2], "positive_share": sum(x > 0 for x in xs) / len(xs),
            "worst_excess": xs[0], "best_excess": xs[-1], "coins": len(coins),
            "by_year_sum": {k: years[k] for k in sorted(years)}}
