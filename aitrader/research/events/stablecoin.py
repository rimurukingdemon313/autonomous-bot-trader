"""SCX-1: do stablecoins drift from par while their primary market is shut, and come back when it opens?
(research/preregistrations/SCX-1.md)

A dollar stablecoin's price on an exchange is held near $1 by arbitrageurs who mint and redeem with its issuer, and
issuers move dollars only on US banking days. At weekends the peg rests on market makers' stock alone, so a flow can
push the price further and for longer; on Monday the primary market reopens and the price is pulled back.

The rule decides at 22:00 UTC on Sunday (the close of the hour 21:00-22:00): if a pair of stablecoins (USDC against
USDT, and the others Binance quotes against USDT) stands at least theta from par, swap from the dear one into the
cheap one, from a stock of both (a spot exchange, hand to hand: no borrowing, no short sale), and swap back 23 hours
later, at 21:00 UTC on Monday, after the US banking day. The judged figure is that swap's return less the costs.
The contrast is the same rule on Wednesday 22:00 to Thursday 21:00, when the primary market is open throughout: if
the mechanism is the weekend closure, Sundays must do better. Nothing here trades.
"""

from __future__ import annotations

import math
import random
from datetime import date, datetime, timedelta, timezone

from aitrader.research.events.cascade import nw_t

SCX_VERSION = "scx-1.0.0"
HOUR = 3_600_000
DAY = 86_400_000
#: the stablecoin pairs Binance quotes against USDT (PAX was renamed USDP; BUSD was wound down from 2023)
PAIRS = ("USDCUSDT", "TUSDUSDT", "USDPUSDT", "PAXUSDT", "BUSDUSDT", "FDUSDUSDT")


def ms_of(day: str) -> int:
    return int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp() * 1000)


def weekdays_in(a: str, b: str, weekday: int) -> list[str]:
    """The dates in [a, b] that fall on `weekday` (Monday 0 .. Sunday 6)."""
    d, e, out = date.fromisoformat(a), date.fromisoformat(b), []
    while d <= e:
        if d.weekday() == weekday:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def close_at(bars: dict[int, float], t_close: int) -> float | None:
    """The close at t_close: that of the hourly bar opening an hour before."""
    v = bars.get(t_close - HOUR)
    return v if isinstance(v, (int, float)) and math.isfinite(v) and v > 0 else None


def trade(pair: str, bars: dict[int, float], t_in: int, hold_hours: int, theta: float, cost: float) -> dict | None:
    """None if the pair is within theta of par at t_in (or has no close there); otherwise the swap into the cheap
    side and back `hold_hours` later, recorded as missing if its exit has no close."""
    p0 = close_at(bars, t_in)
    if p0 is None:
        return None
    d = math.log(p0)
    if abs(d) < theta:
        return None
    p1 = close_at(bars, t_in + hold_hours * HOUR)
    if p1 is None:
        return {"pair": pair, "t": t_in, "delta": d, "missing": True}
    g = -math.copysign(1.0, d) * (math.log(p1) - d)
    return {"pair": pair, "t": t_in, "delta": d, "gross": g, "net": g - cost}


def entries(bars: dict[str, dict[int, float]], days: list[str], hour: int, hold_hours: int, theta: float, cost: float,
            lag_hours: int = 0) -> list[dict]:
    """The rule on each of `days` at `hour` UTC (plus a lag), for every pair; each entry keyed by its day."""
    out = []
    for day in days:
        t = ms_of(day) + (hour + lag_hours) * HOUR
        for pair in sorted(bars):
            e = trade(pair, bars[pair], t, hold_hours, theta, cost)
            if e is not None:
                e["day"] = day
                out.append(e)
    return out


def placebos(bars: dict[str, dict[int, float]], evs: list[dict], hold_hours: int, theta: float, cost: float,
             span_days: int, draws: int, seed: int, window: tuple[int, int]) -> dict[tuple[str, str], list[float]]:
    """For each traded entry, the same rule on the same pair at up to `draws` random hours within `span_days` either
    side, at least two days away, whose deviation also reached theta, inside the stage's own hours."""
    rng, out = random.Random(seed), {}
    lo, hi = window
    for e in evs:
        if e.get("missing"):
            continue
        b, t0 = bars[e["pair"]], e["t"]
        cand = []
        for k in range(-span_days * 24, span_days * 24 + 1):
            t = t0 + k * HOUR
            if abs(k) < 48 or not lo <= t <= hi - hold_hours * HOUR:
                continue
            p = close_at(b, t)
            if p is not None and abs(math.log(p)) >= theta:
                cand.append(t)
        nets = []
        for t in rng.sample(cand, min(draws, len(cand))):
            x = trade(e["pair"], b, t, hold_hours, theta, cost)
            if x is not None and not x.get("missing"):
                nets.append(x["net"])
        if nets:
            out[(e["pair"], e["day"])] = nets
    return out


def cohorts(evs: list[dict], key: str = "net") -> dict[str, float]:
    acc: dict[str, list[float]] = {}
    for e in evs:
        acc.setdefault(e["day"], []).append(e[key])
    return {d: sum(v) / len(v) for d, v in sorted(acc.items())}


def _stat(xs: list[dict], key: str = "net") -> float | None:
    c = cohorts(xs, key)
    return sum(c.values()) / len(c) if c else None


def judge(evs: list[dict], late: list[dict], contra: list[dict], plac: dict, bar: float, cost: float,
          min_events: int, min_weeks: int, seed: int, draws: int, lag: int = 1) -> dict:
    """One threshold's Sunday entries against every preregistered gate; too few is INCONCLUSIVE, never a pass."""
    ok = [e for e in evs if not e.get("missing")]
    c = cohorts(ok)
    m, t = nw_t(list(c.values()), lag)
    out = {"entries": len(evs), "traded": len(ok), "missing": len(evs) - len(ok), "weeks": len(c), "mean_net": m,
           "t": t, "bar": bar}
    if len(ok) < min_events or len(c) < min_weeks:
        return {**out, "verdict": "INCONCLUSIVE",
                "why": f"{len(ok)} entries in {len(c)} weeks: {min_events} and {min_weeks} are needed"}
    ks = list(c)
    h = len(ks) // 2
    first, second = sum(c[k] for k in ks[:h]) / h, sum(c[k] for k in ks[h:]) / (len(ks) - h)
    top = set(sorted(range(len(ok)), key=lambda i: ok[i]["net"], reverse=True)[:5])
    no_top = _stat([e for i, e in enumerate(ok) if i not in top])
    weight = {d: c[d] * sum(1 for e in ok if e["day"] == d) for d in c}
    best_week = max(weight, key=weight.get)
    no_week = _stat([e for e in ok if e["day"] != best_week])
    pairs: dict[str, float] = {}
    for e in ok:
        pairs[e["pair"]] = pairs.get(e["pair"], 0.0) + e["net"]
    bp = max(pairs, key=pairs.get)
    no_pair = _stat([e for e in ok if e["pair"] != bp])
    x2 = _stat([{**e, "net": e["net"] - cost} for e in ok])
    late_ok = [e for e in late if not e.get("missing")]
    lt = _stat(late_ok) if late_ok else None
    contra_ok = [e for e in contra if not e.get("missing")]
    cm = _stat(contra_ok) if contra_ok else None
    rng = random.Random(seed)
    usable = [e for e in ok if plac.get((e["pair"], e["day"]))]
    wks = sorted({e["day"] for e in usable})
    pos = {d: i for i, d in enumerate(wks)}
    wi = [pos[e["day"]] for e in usable]
    cnt = [0] * len(wks)
    for i in wi:
        cnt[i] += 1
    ds = []
    for _ in range(draws if usable else 0):
        acc = [0.0] * len(wks)
        for i, e in zip(wi, usable):
            acc[i] += rng.choice(plac[(e["pair"], e["day"])])
        ds.append(sum(a / n for a, n in zip(acc, cnt)) / len(wks))
    ds.sort()
    p95 = ds[int(0.95 * draws) - 1] if ds else None
    gates = {"t": t is not None and t >= bar, "costs_x2": x2 is not None and x2 > 0,
             "halves": first > 0 and second > 0, "top5_removed": no_top is not None and no_top > 0,
             "late_entry": lt is not None and lt > 0, "beats_placebo": p95 is not None and m is not None and m > p95,
             "without_best_week": no_week is not None and no_week > 0,
             "without_best_pair": no_pair is not None and no_pair > 0,
             "beats_weekdays": cm is not None and m is not None and m > cm}
    xs = sorted(e["net"] for e in ok)
    return {**out, "verdict": "PASSED" if all(gates.values()) else "FAILED", "gates": gates,
            "gross_mean": _stat(ok, "gross"), "costs_x2_mean": x2, "first_half": first, "second_half": second,
            "without_top5_mean": no_top, "late_mean": lt, "placebo_p95": p95,
            "placebo_share_at_or_above": (sum(d >= m for d in ds) / len(ds)) if ds and m is not None else None,
            "best_week": best_week, "without_best_week_mean": no_week, "best_pair": bp, "without_best_pair_mean": no_pair,
            "weekday_entries": len(contra_ok), "weekday_mean_net": cm, "median_net": xs[len(xs) // 2],
            "positive_share": sum(x > 0 for x in xs) / len(xs), "worst_net": xs[0], "best_net": xs[-1],
            "pairs": sorted(pairs), "mean_abs_delta": sum(abs(e["delta"]) for e in ok) / len(ok)}
