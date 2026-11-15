"""NEWL-1: do perpetuals in their first month underperform perpetuals in their second half-year?

research/preregistrations/NEWL-1.md. Every definition here is frozen by the code hash quoted there. Pure functions:
no data access, no clock. Prices are daily closes {"YYYY-MM-DD": price}; funding is {"YYYY-MM-DD": the sum of that
UTC day's funding rates}, the fraction of notional a long paid (a short received it).

The mechanism tested: a contract's first weeks carry supply that was not trading before (unlocks, airdrops, the
market maker's borrowed inventory) and the attention of its listing, while shorting it elsewhere is hard. If that
makes new contracts overpriced, a short in the new contract, hedged with a long basket of contracts listed half a
year to a year earlier, earns after funding and costs. The hedge keeps the bet off the market's direction, and its
members are listings themselves, not the old coins of the discovery lab's panel.
"""

from __future__ import annotations

import math
import random
from datetime import date, timedelta

NEWL_VERSION = "newl-1.0.0"
QUOTES = ("USDT", "USDC", "BUSD")
PREFIXES = ("1000000", "1000", "1M")
#: contracts on an index or a basket, not on one coin
SPECIAL = frozenset({"BTCDOMUSDT", "DEFIUSDT", "FOOTBALLUSDT", "BLUEBIRDUSDT", "ALTUSDT"})
#: bases that are dollars: no supply overhang to speak of
STABLE = frozenset({"USDC", "BUSD", "TUSD", "FDUSD", "USDP", "DAI", "USDE", "PYUSD", "UST", "EUR", "USD1"})


def base_of(symbol: str) -> str | None:
    """The coin a contract is on: its quote and any 1000/1000000/1M prefix removed. None if the quote is not one of
    ours (delivery contracts carry a date after an underscore and are not perpetuals)."""
    if "_" in symbol:
        return None
    for q in QUOTES:
        if symbol.endswith(q) and len(symbol) > len(q):
            b = symbol[: -len(q)]
            for p in PREFIXES:
                if b.startswith(p) and len(b) > len(p):
                    return b[len(p):]
            return b
    return None


def classify(first_month: dict[str, str]) -> dict:
    """Which contracts were listings of a coin: {symbol: first archive month "YYYY-MM"} -> eligible and excluded,
    each excluded symbol with its reason. Contracts are read in the order they appeared; a coin that already had a
    contract is a re-denomination or a re-listing, not a new coin, and is excluded."""
    seen: dict[str, str] = {}
    eligible, excluded = {}, {}
    for sym, m in sorted(first_month.items(), key=lambda kv: (kv[1], kv[0])):
        b = base_of(sym)
        if b is None:
            excluded[sym] = "not a perpetual on a USDT, USDC or BUSD quote"
        elif sym in SPECIAL:
            excluded[sym] = "an index or basket contract"
        elif b in STABLE:
            excluded[sym] = "a dollar-pegged coin"
        elif b in seen:
            excluded[sym] = f"the coin {b} already had a contract ({seen[b]})"
        else:
            seen[b] = sym
            eligible[sym] = m
    return {"eligible": eligible, "excluded": excluded}


def _day(d: str) -> date:
    return date.fromisoformat(d)


def _plus(d: str, n: int) -> str:
    return (_day(d) + timedelta(days=n)).isoformat()


def listing_day(closes: dict[str, float]) -> str | None:
    return min(closes) if closes else None


def leg(closes: dict[str, float], funding: dict[str, float], a: str, b: str, side: int, cost: float) -> dict | None:
    """One position held from the close of day a to the close of day b (or of its last priced day, if it stopped
    trading first): side -1 short, +1 long, per unit of notional at entry. The price move, the funding on the
    position's notional each day (the notional follows the price), and two fills. None if there is no close on a."""
    if a not in closes:
        return None
    pa = closes[a]
    days = sorted(d for d in closes if a < d <= b)
    last = days[-1] if days else a
    move = closes[last] / pa - 1
    fund, prev = 0.0, pa
    d = a
    while d < last:
        d = _plus(d, 1)
        fund += funding.get(d, 0.0) * prev / pa  # paid by a long, received by a short, on yesterday's notional
        if d in closes:
            prev = closes[d]
    gross = side * move - side * fund
    return {"move": move, "funding": fund, "gross": gross, "net": gross - 2 * cost, "exit": last,
            "stopped_early": last < b}


def events(listed: dict[str, str], closes: dict[str, dict[str, float]], funding: dict[str, dict[str, float]],
           first: str, last: str, lag: int = 1, hold: int = 30, cost: float = 0.0015,
           seasoned: tuple[int, int] = (181, 365), min_pool: int = 3) -> list[dict]:
    """Every eligible contract whose entry day (its listing day plus `lag`) falls in [first, last]: its short leg, and
    the long basket of contracts aged `seasoned` days at that entry (equal weights, the same window, the same costs).
    `listed` maps every contract that may serve, as an event or in a basket, to True if it is an eligible listing."""
    born = {s: listing_day(closes.get(s, {})) for s in listed}
    out = []
    for s, eligible in sorted(listed.items()):
        L = born[s]
        if not eligible or L is None:
            continue
        a = _plus(L, lag)
        if not first <= a <= last:
            continue
        b = _plus(a, hold)
        short = leg(closes[s], funding.get(s, {}), a, b, -1, cost)
        if short is None:  # no price on its entry day: counted and shown, never silently dropped
            out.append({"symbol": s, "listed": L, "entry": a, "no_entry_price": True})
            continue
        pool = []
        for j, Lj in born.items():
            if j == s or Lj is None:
                continue
            age = (_day(a) - _day(Lj)).days
            if seasoned[0] <= age <= seasoned[1]:
                lj = leg(closes[j], funding.get(j, {}), a, b, +1, cost)
                sj = leg(closes[j], funding.get(j, {}), a, b, -1, cost)
                if lj is not None:
                    pool.append((j, lj["net"], sj["net"], lj["gross"]))
        e = {"symbol": s, "listed": L, "entry": a, "exit": short["exit"], "stopped_early": short["stopped_early"],
             "short_net": short["net"], "short_gross": short["gross"], "move": short["move"], "funding": short["funding"],
             "pool": len(pool)}
        if len(pool) >= min_pool:
            basket = sum(p[1] for p in pool) / len(pool)
            e.update(basket_net=basket, x=short["net"] + basket,
                     x_gross=short["gross"] + sum(p[3] for p in pool) / len(pool),
                     placebo_shorts=[p[2] for p in pool])
        out.append(e)
    return out


def nw_t(xs: list[float], lag: int = 1) -> tuple[float | None, float | None]:
    """The mean and its t-statistic with a Newey-West standard error (Bartlett weights). None when undefined."""
    n = len(xs)
    if n < 3:
        return (sum(xs) / n if n else None), None
    m = sum(xs) / n
    d = [x - m for x in xs]
    if max(abs(v) for v in d) <= 1e-12 * max(1.0, abs(m)):  # no spread: rounding must not make a t-statistic
        return m, None
    s = sum(v * v for v in d) / n
    for k in range(1, min(lag, n - 1) + 1):
        s += 2 * (1 - k / (lag + 1)) * sum(d[i] * d[i - k] for i in range(k, n)) / n
    if s <= 0:
        return m, None
    return m, m / math.sqrt(s / n)


def cohorts(evs: list[dict], key: str = "x") -> dict[str, float]:
    """The mean outcome of the events entered in each calendar month."""
    by: dict[str, list[float]] = {}
    for e in evs:
        if e.get(key) is not None:
            by.setdefault(e["entry"][:7], []).append(e[key])
    return {m: sum(v) / len(v) for m, v in sorted(by.items())}


def judge(evs: list[dict], late: list[dict], bar: float, cost: float, seed: int = 20261115, placebos: int = 1000,
          min_events: int = 60, min_months: int = 18) -> dict:
    """The stage's figures and its verdict. `evs` at the registered lag, `late` the same events entered a day later.
    Every gate is required; too few events or months is INCONCLUSIVE, never a pass."""
    hedged = [e for e in evs if e.get("x") is not None]
    priced = [e for e in evs if "short_net" in e]
    coh = cohorts(hedged)
    months = list(coh)
    mean, t = nw_t([coh[m] for m in months])
    out = {"events": len(evs), "no_entry_price": len(evs) - len(priced), "unhedged_events": len(priced) - len(hedged),
           "hedged_events": len(hedged), "months": len(months), "mean_cohort_x": mean, "t": t, "bar": bar, "cohorts": coh}
    if len(hedged) < min_events or len(months) < min_months:
        return {**out, "verdict": "INCONCLUSIVE",
                "why": f"{len(hedged)} hedged events in {len(months)} months: {min_events} and {min_months} are needed"}
    # costs doubled: each event pays two more fills on each leg
    x2 = cohorts([{**e, "x": e["x"] - 4 * cost} for e in hedged])
    half = len(months) // 2
    first_half = sum(coh[m] for m in months[:half]) / half
    second_half = sum(coh[m] for m in months[half:]) / (len(months) - half)
    top = sorted(hedged, key=lambda e: e["x"], reverse=True)[:5]
    keep = [e for e in hedged if e not in top]
    without_top = cohorts(keep)
    late_coh = cohorts([e for e in late if e.get("x") is not None])
    years: dict[str, float] = {}
    for e in hedged:
        years[e["entry"][:4]] = years.get(e["entry"][:4], 0.0) + e["x"]
    best_year = max(years, key=years.get)
    without_year = cohorts([e for e in hedged if e["entry"][:4] != best_year])
    rng = random.Random(seed)
    placebo_means = []
    for _ in range(placebos):
        fake = [{"entry": e["entry"], "x": rng.choice(e["placebo_shorts"]) + e["basket_net"]} for e in hedged]
        pc = cohorts(fake)
        placebo_means.append(sum(pc.values()) / len(pc))
    placebo_means.sort()
    p95 = placebo_means[int(0.95 * placebos) - 1]

    def avg(c):
        return sum(c.values()) / len(c) if c else None
    gates = {"t": t is not None and t >= bar,
             "costs_x2": avg(x2) is not None and avg(x2) > 0,
             "halves": first_half > 0 and second_half > 0,
             "top5_removed": avg(without_top) is not None and avg(without_top) > 0,
             "one_day_late": avg(late_coh) is not None and avg(late_coh) > 0,
             "beats_random": mean > p95,
             "without_best_year": avg(without_year) is not None and avg(without_year) > 0}
    shorts = sorted(e["short_net"] for e in priced)
    cum, peak, dd = 0.0, 0.0, 0.0
    for m in months:
        cum += coh[m]
        peak = max(peak, cum)
        dd = max(dd, peak - cum)
    return {**out, "gates": gates, "verdict": "PASSED" if all(gates.values()) else "FAILED",
            "costs_x2_mean": avg(x2), "first_half": first_half, "second_half": second_half,
            "without_top5_mean": avg(without_top), "top5": [(e["symbol"], round(e["x"], 4)) for e in top],
            "one_day_late_mean": avg(late_coh), "best_year": best_year, "by_year_sum_x": years,
            "without_best_year_mean": avg(without_year), "placebo_p95": p95,
            "placebo_share_above_actual": sum(p >= mean for p in placebo_means) / placebos,
            "gross_mean_cohort_x": avg(cohorts(hedged, "x_gross")),
            "short_only": {"mean": sum(shorts) / len(shorts), "median": shorts[len(shorts) // 2],
                           "positive": sum(x > 0 for x in shorts) / len(shorts), "worst": shorts[0], "best": shorts[-1]},
            "cohort_sequence_max_drawdown": dd, "stopped_early": sum(e["stopped_early"] for e in priced)}


__all__ = ["NEWL_VERSION", "base_of", "classify", "cohorts", "events", "judge", "leg", "listing_day", "nw_t"]
