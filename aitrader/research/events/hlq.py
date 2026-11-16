"""HLQ-1: is the price drawn to the leveraged positions everyone can see? (research/preregistrations/HLQ-1.md)

Hyperliquid keeps its order book and its accounts on its own chain, so every account's open positions, and the price
at which each would be liquidated, can be read by anyone. A liquidation is a forced, price-insensitive order whose
only trigger is the price. When forced trades are predictable in size and trigger, it pays others to trade ahead of
them in the same direction, push the price to the trigger, and supply the liquidity the forced trades then demand
(Brunnermeier & Pedersen 2005, "Predatory trading"); and a cluster that is triggered adds its own forced flow, which
carries the price on toward the next one. Both predict that the price reaches a large visible cluster more often than
an equally distant level on the other side, where no cluster waits.

The rule, at each recorded snapshot of a coin: L is the notional of the long positions whose liquidation price lies
between `lo` and `hi` below the mark, S the notional of the short positions liquidated between `lo` and `hi` above it.
When one side holds at least `imbalance` of L + S, the larger side's mean distance D is the target: enter toward it at
the first minute that starts after the snapshot was complete, take the profit at D and stop at D on the other side,
whichever the minute's range reaches first (both in one minute: the stop), or leave at the close after `hold` minutes.
One position per coin at a time. Under a price with no drift, the target and the stop are reached first equally often.

Prices are Binance spot one-minute bars: the information is Hyperliquid's, the traded instrument would be a swap-free
CFD on bitcoin or ether (long or short), and nothing here trades.
"""

from __future__ import annotations

import math
import random

import numpy as np

HLQ_VERSION = "hlq-1.0.0"
BIN = 0.0025  # one bin of liquidation distance, as a fraction of the mark
SPAN = 0.10  # a liquidation farther than this from the mark is counted, never binned
MINUTE = 60_000
DAY = 86_400_000


def _f(x) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


# ── one snapshot: positions to liquidation levels ───────────────────────────────

def aggregate(states: list[dict], marks: dict[str, float], coins: set[str] | None = None) -> dict[str, dict]:
    """Accounts' open positions (Hyperliquid clearinghouseState answers) as, per coin, the long and the short notional
    by liquidation distance. A position's notional is its size at the snapshot's mark; its distance is
    liquidationPx / mark - 1, in bin k = floor(distance / BIN). A position with no liquidation price, or with one
    beyond SPAN, is counted in its own total and never binned. No account is named in what is returned."""
    out: dict[str, dict] = {}
    for st in states:
        for ap in (st or {}).get("assetPositions") or []:
            p = (ap or {}).get("position") or {}
            coin = p.get("coin")
            m = marks.get(coin) if coin else None
            szi = _f(p.get("szi"))
            if m is None or m <= 0 or not szi or (coins is not None and coin not in coins):
                continue
            side = "L" if szi > 0 else "S"
            usd = abs(szi) * m
            a = out.setdefault(coin, {"L": {}, "S": {}, "L_usd": 0.0, "S_usd": 0.0, "L_n": 0, "S_n": 0,
                                      "L_noliq": 0.0, "S_noliq": 0.0, "L_far": 0.0, "S_far": 0.0})
            a[side + "_usd"] += usd
            a[side + "_n"] += 1
            liq = _f(p.get("liquidationPx"))
            if liq is None or liq <= 0:
                a[side + "_noliq"] += usd
                continue
            d = liq / m - 1
            if abs(d) > SPAN:
                a[side + "_far"] += usd
                continue
            k = math.floor(d / BIN)
            a[side][k] = a[side].get(k, 0.0) + usd
    return out


def clusters(a: dict, lo: float, hi: float) -> tuple[float, float, float | None, float | None]:
    """L, S, and each side's notional-weighted mean distance (from bin centres): longs liquidated between lo and hi
    below the mark, shorts between lo and hi above it. Bins come back from JSON with string keys; both are read."""
    def side(bins: dict, sign: int) -> tuple[float, float | None]:
        tot = w = 0.0
        for k, usd in (bins or {}).items():
            c = sign * (int(k) + 0.5) * BIN
            if lo <= c <= hi and usd > 0:
                tot += usd
                w += usd * c
        return tot, (w / tot if tot > 0 else None)
    L, dl = side(a.get("L"), -1)
    S, ds = side(a.get("S"), +1)
    return L, S, dl, ds


def signal(a: dict, lo: float, hi: float, imbalance: float, min_share: float) -> dict | None:
    """The side the rule would trade toward, or None: L + S at least `min_share` of the coin's open interest, and
    one side at least `imbalance` of L + S (B = (L - S) / (L + S), |B| >= 2 * imbalance - 1)."""
    oi = _f(a.get("oi_usd"))
    L, S, dl, ds = clusters(a, lo, hi)
    if oi is None or oi <= 0 or L + S <= 0 or L + S < min_share * oi:
        return None
    big = max(L, S) / (L + S)
    if big < imbalance or L == S:
        return None
    down = L > S
    return {"dir": -1 if down else +1, "dist": dl if down else ds, "L": L, "S": S, "B": (L - S) / (L + S),
            "share": (L + S) / oi}


# ── prices ─────────────────────────────────────────────────────────────────

class Path:
    """A coin's one-minute bars on a whole grid from t0: a minute the archive lacks is NaN, never filled."""

    def __init__(self, t0: int, n: int):
        self.t0, self.n = t0, n
        self.o, self.h, self.l, self.c = (np.full(n, np.nan) for _ in range(4))

    def put(self, rows: list[tuple[int, float, float, float, float]]) -> None:
        for t, o, h, lo, c in rows:
            i = (t - self.t0) // MINUTE
            if 0 <= i < self.n and (t - self.t0) % MINUTE == 0:
                self.o[i], self.h[i], self.l[i], self.c[i] = o, h, lo, c

    def first_at(self, at: int) -> int:
        """The first minute that starts at or after `at`."""
        return -((self.t0 - at) // MINUTE)


def trade(p: Path, at: int, d: int, dist: float, cost: float, hold: int, delay: int = 0) -> dict:
    """Enter at the open of the first minute starting at or after `at` (+ `delay` minutes); leave at the first minute
    whose range reaches entry x (1 + d x dist) (the target) or entry x (1 - d x dist) (the stop), at that level; when
    one minute reaches both, the stop. After `hold` minutes, at the last one's close. A missing minute before the exit
    makes the trade missing: it is counted, never filled."""
    i = p.first_at(at) + delay
    out = {"entry_ms": p.t0 + i * MINUTE, "dir": d, "dist": dist}
    if i < 0 or i + hold > p.n or not np.isfinite(p.o[i]) or dist is None or dist <= 0:
        return {**out, "missing": True}
    e = p.o[i]
    hi, lo = p.h[i:i + hold], p.l[i:i + hold]
    up, dn = e * (1 + dist), e * (1 - dist)
    bad = ~(np.isfinite(hi) & np.isfinite(lo))
    reach_up, reach_dn = hi >= up, lo <= dn
    first = [int(np.argmax(x)) if x.any() else hold for x in (reach_up, reach_dn, bad)]
    j = min(first[0], first[1])
    if first[2] <= j and (first[2] < hold):
        return {**out, "missing": True}
    if j >= hold:
        x, how = p.c[i + hold - 1], "time"
        if not np.isfinite(x):
            return {**out, "missing": True}
    else:
        target_first = first[0] if d > 0 else first[1]
        stop_first = first[1] if d > 0 else first[0]
        if stop_first <= target_first:
            x, how = (dn if d > 0 else up), "stop"
        else:
            x, how = (up if d > 0 else dn), "target"
        j = min(target_first, stop_first)
    r = d * (float(x) / float(e) - 1)
    return {**out, "exit_ms": p.t0 + (i + (j if how != "time" else hold - 1)) * MINUTE, "how": how, "ret": r,
            "net": r - 2 * cost}


# ── the study ──────────────────────────────────────────────────────────────

def events(snaps: dict[str, list[dict]], paths: dict[str, Path], first: int, last: int, cfg: dict, cost: float,
           delay: int = 0) -> list[dict]:
    """Every entry the rule takes from coin c's snapshots completed in [first, last): in time order; a snapshot with
    a signal and no open position on c opens one; the coin is busy until its exit (a missing trade: until `hold`)."""
    out = []
    for c in sorted(snaps):
        if c not in paths:
            continue
        busy = -1
        for s in sorted(snaps[c], key=lambda x: x["t_end"]):
            if not first <= s["t_end"] < last or s["t_end"] < busy:
                continue
            sig = signal(s, cfg["lo"], cfg["hi"], cfg["imbalance"], cfg["min_share"])
            if sig is None:
                continue
            tr = trade(paths[c], s["t_end"], sig["dir"], sig["dist"], cost, cfg["hold"], delay)
            out.append({"coin": c, "t": s["t_end"], **{k: sig[k] for k in ("B", "share", "L", "S")}, **tr})
            busy = tr.get("exit_ms", tr["entry_ms"] + cfg["hold"] * MINUTE) + MINUTE
    return out


def placebos(snaps: dict[str, list[dict]], paths: dict[str, Path], evs: list[dict], cfg: dict, cost: float,
             span: int = 3 * DAY, gap: int = 6 * 3_600_000, draws: int = 40, seed: int = 20261116) -> dict:
    """For each traded entry, the same trade (coin, direction, distance) entered at up to `draws` of the coin's own
    snapshots within `span` on either side, at least `gap` away, at which the rule saw no signal: what the same
    bet earned when no cluster pointed to it."""
    rng, out = random.Random(seed), {}
    by = {c: sorted(xs, key=lambda x: x["t_end"]) for c, xs in snaps.items()}
    for e in evs:
        if e.get("missing"):
            continue
        cand = [s["t_end"] for s in by.get(e["coin"], []) if gap <= abs(s["t_end"] - e["t"]) <= span
                and signal(s, cfg["lo"], cfg["hi"], cfg["imbalance"], cfg["min_share"]) is None]
        xs = []
        for t in rng.sample(cand, min(draws, len(cand))):
            tr = trade(paths[e["coin"]], t, e["dir"], e["dist"], cost, cfg["hold"])
            if not tr.get("missing"):
                xs.append(tr["net"])
        out[(e["coin"], e["t"])] = xs
    return out


def day_of(t: int) -> int:
    return t // DAY


def cohorts(evs: list[dict], key: str = "net") -> dict[int, float]:
    """The mean of `key` over the entries decided on each UTC day."""
    acc: dict[int, list[float]] = {}
    for e in evs:
        acc.setdefault(day_of(e["t"]), []).append(e[key])
    return {d: sum(v) / len(v) for d, v in sorted(acc.items())}


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


def _mean_of_days(evs: list[dict], key: str = "net") -> float | None:
    c = cohorts(evs, key)
    return sum(c.values()) / len(c) if c else None


def judge(evs: list[dict], late: list[dict], plac: dict, bar: float, cost: float, min_events: int, min_days: int,
          owner: tuple[str, ...], min_owner: int, seed: int = 20261116, draws: int = 1000, lag: int = 2) -> dict:
    """The rule's entries against every preregistered gate; too few is INCONCLUSIVE, never a pass."""
    ok = [e for e in evs if not e.get("missing")]
    c = cohorts(ok)
    m, t = nw_t(list(c.values()), lag)
    hows = {h: sum(1 for e in ok if e["how"] == h) for h in ("target", "stop", "time")}
    out = {"entries": len(evs), "traded": len(ok), "missing": len(evs) - len(ok), "days": len(c), "mean_net": m,
           "t": t, "bar": bar, "exits": hows,
           "target_share": hows["target"] / (hows["target"] + hows["stop"]) if hows["target"] + hows["stop"] else None}
    if len(ok) < min_events or len(c) < min_days:
        return {**out, "verdict": "INCONCLUSIVE",
                "why": f"{len(ok)} entries on {len(c)} days: {min_events} and {min_days} are needed"}
    ks = list(c)
    h = len(ks) // 2
    first, second = sum(c[k] for k in ks[:h]) / h, sum(c[k] for k in ks[h:]) / (len(ks) - h)
    top = set(sorted(range(len(ok)), key=lambda i: ok[i]["net"], reverse=True)[:5])
    no_top = _mean_of_days([e for i, e in enumerate(ok) if i not in top])
    best_day = max(c, key=lambda d: c[d] * sum(1 for e in ok if day_of(e["t"]) == d))
    no_day = _mean_of_days([e for e in ok if day_of(e["t"]) != best_day])
    coins: dict[str, float] = {}
    for e in ok:
        coins[e["coin"]] = coins.get(e["coin"], 0.0) + e["net"]
    bc = max(coins, key=coins.get)
    no_coin = _mean_of_days([e for e in ok if e["coin"] != bc])
    x2 = _mean_of_days([{**e, "net": e["net"] - 2 * cost} for e in ok])
    late_ok = [e for e in late if not e.get("missing")]
    lt = _mean_of_days(late_ok) if late_ok else None
    mine = [e for e in ok if e["coin"] in owner]
    own, own2 = _mean_of_days(mine), _mean_of_days([{**e, "net": e["net"] - 2 * cost} for e in mine])
    rng = random.Random(seed)
    usable = [e for e in ok if plac.get((e["coin"], e["t"]))]
    days = sorted({day_of(e["t"]) for e in usable})
    pos = {d: i for i, d in enumerate(days)}
    wi = [pos[day_of(e["t"])] for e in usable]
    cnt = [0] * len(days)
    for i in wi:
        cnt[i] += 1
    ds = []
    for _ in range(draws if usable else 0):
        acc = [0.0] * len(days)
        for i, e in zip(wi, usable):
            acc[i] += rng.choice(plac[(e["coin"], e["t"])])
        ds.append(sum(a / n for a, n in zip(acc, cnt)) / len(days))
    ds.sort()
    p95 = ds[int(0.95 * draws) - 1] if ds else None
    gates = {"t": t is not None and t >= bar, "costs_x2": x2 is not None and x2 > 0,
             "halves": first > 0 and second > 0, "top5_removed": no_top is not None and no_top > 0,
             "late_entry": lt is not None and lt > 0, "beats_placebo": p95 is not None and m is not None and m > p95,
             "without_best_day": no_day is not None and no_day > 0,
             "without_best_coin": no_coin is not None and no_coin > 0,
             "owner_instruments": len(mine) >= min_owner and own is not None and own > 0 and own2 is not None and own2 > 0}
    xs = sorted(e["net"] for e in ok)
    return {**out, "verdict": "PASSED" if all(gates.values()) else "FAILED", "gates": gates,
            "gross_mean": _mean_of_days([{**e, "net": e["net"] + 2 * cost} for e in ok]), "costs_x2_mean": x2,
            "first_half": first, "second_half": second, "without_top5_mean": no_top, "late_mean": lt,
            "placebo_p95": p95, "placebo_share_at_or_above": (sum(d >= m for d in ds) / len(ds)) if ds and m is not None else None,
            "best_day": best_day, "without_best_day_mean": no_day, "best_coin": bc, "without_best_coin_mean": no_coin,
            "owner_trades": len(mine), "owner_mean_net": own, "owner_costs_x2": own2, "median_net": xs[len(xs) // 2],
            "positive_share": sum(x > 0 for x in xs) / len(xs), "worst_net": xs[0], "best_net": xs[-1],
            "mean_dist": sum(e["dist"] for e in ok) / len(ok), "coins": len(coins)}
