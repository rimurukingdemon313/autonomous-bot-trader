"""CR-4: cross-venue funding differential, Hyperliquid vs Binance USDT-M perpetuals (research only).

Both legs are perpetuals on the SAME coin, so the book is market-neutral. A position is short the venue whose
perpetual pays more funding and long the other; it earns the funding difference, pays both venues' costs, and
carries the basis risk between the two perpetuals' prices.

Data per coin (`Pair`): daily candles' OPEN prices on both venues (00:00 UTC), Hyperliquid's hourly funding
settlements and Binance's 8-hourly (or 4-hourly) settlements, each as (time, rate).

Rule, decided at each 00:00 UTC D using only what was public at D:

- eligible: both venues have a daily candle at D and have listed for `seasoning_d` days;
- diff(D) = mean over the last `lookback_d` days of (Hyperliquid funding paid that day - Binance funding paid that
  day), each day being the sum of settlements in (day start, day end];
- open (if a slot is free, best |diff| first): |diff| >= theta_in; side = +1 means short Hyperliquid, long Binance
  (diff > 0), -1 the reverse;
- close: |diff| < theta_out or the sign of diff flips;
- every fill is at the NEXT daily open (D + 1 day): a full day of latency, conservative.

P&L per position, bp of the notional N of each leg: funding = sum over settlements strictly inside (entry, exit) of
side x (Hyperliquid rate) on the short-HL leg and -side x (Binance rate) on the long-BN leg; basis =
side x (BN return - HL return) between entry and exit opens; costs = both legs, both fills: fee + half-spread +
slippage per venue and liquidity tier; a forced rebalance (either leg's price at 1.8x its reference) adds one full
round trip. Capital is 2N per position (1x margin on each venue).
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

XV_VERSION = "xv-1.0.0"
DAY = 86400
REBALANCE_AT = 1.8
MAJORS = ("BTC", "ETH")


@dataclass(frozen=True)
class Pair:
    coin: str
    hl_t: np.ndarray  # daily open times
    hl_o: np.ndarray
    bn_t: np.ndarray
    bn_o: np.ndarray
    hl_ft: np.ndarray  # funding settlement times
    hl_fr: np.ndarray
    bn_ft: np.ndarray
    bn_fr: np.ndarray

    def truncated(self, t_end: int) -> "Pair":
        k = lambda t: np.searchsorted(t, t_end, "left")  # noqa: E731
        a, b, c, d = k(self.hl_t), k(self.bn_t), k(self.hl_ft), k(self.bn_ft)
        return Pair(self.coin, self.hl_t[:a], self.hl_o[:a], self.bn_t[:b], self.bn_o[:b], self.hl_ft[:c],
                    self.hl_fr[:c], self.bn_ft[:d], self.bn_fr[:d])


@dataclass(frozen=True)
class XvCosts:
    hl_fee_bp: float = 4.5  # Hyperliquid base-tier taker
    bn_fee_bp: float = 5.0  # Binance VIP 0 USDT-M taker
    k: float = 1.0

    def tier(self, coin: str) -> tuple[float, float]:
        return (1.0 * self.k, 1.0 * self.k) if coin in MAJORS else (3.0 * self.k, 2.0 * self.k)

    def rt_bp(self, coin: str) -> float:
        h, s = self.tier(coin)
        return 2 * (self.hl_fee_bp * self.k + h + s) + 2 * (self.bn_fee_bp * self.k + h + s)

    def stressed(self, k: float) -> "XvCosts":
        return replace(self, k=self.k * k)


@dataclass(frozen=True)
class XvPosition:
    coin: str
    side: int
    entry_t: int
    exit_t: int
    reason: str
    funding_bp: float
    basis_bp: float
    cost_bp: float
    rebalances: int

    @property
    def gross_bp(self) -> float:
        return self.funding_bp + self.basis_bp

    @property
    def net_bp(self) -> float:
        return self.gross_bp - self.cost_bp


def _cum(t: np.ndarray, r: np.ndarray, a: int, b: int) -> float:
    i, j = np.searchsorted(t, a, "right"), np.searchsorted(t, b, "right")
    return float(r[i:j].sum())


def diff(p: Pair, D: int, lookback_d: int) -> float | None:
    """Mean daily (HL - BN) funding over the `lookback_d` complete days before D. A day counts only if Hyperliquid
    shows >= 20 of its 24 hourly settlements and Binance >= 2; otherwise None (missing data is never read as zero,
    and a partial day is never read as a whole one)."""
    vals = []
    for k in range(lookback_d, 0, -1):
        a, b = D - k * DAY, D - (k - 1) * DAY
        nh = np.searchsorted(p.hl_ft, b, "right") - np.searchsorted(p.hl_ft, a, "right")
        nb = np.searchsorted(p.bn_ft, b, "right") - np.searchsorted(p.bn_ft, a, "right")
        if nh < 20 or nb < 2:
            return None
        vals.append(_cum(p.hl_ft, p.hl_fr, a, b) - _cum(p.bn_ft, p.bn_fr, a, b))
    return float(np.mean(vals))


def _has(t: np.ndarray, D: int) -> int | None:
    i = int(np.searchsorted(t, D))
    return i if i < len(t) and t[i] == D else None


def eligible(p: Pair, D: int, seasoning_d: int) -> bool:
    if not len(p.hl_t) or not len(p.bn_t):
        return False
    if p.hl_t[0] > D - seasoning_d * DAY or p.bn_t[0] > D - seasoning_d * DAY:
        return False
    if not len(p.hl_ft) or not len(p.bn_ft) or p.hl_ft[0] > D - seasoning_d * DAY or p.bn_ft[0] > D - seasoning_d * DAY:
        return False
    return _has(p.hl_t, D) is not None and _has(p.bn_t, D) is not None


def _position(p: Pair, side: int, e: int, x: int, reason: str, costs: XvCosts) -> XvPosition:
    ie, xe = _has(p.hl_t, e), _has(p.hl_t, x)
    je, xj = _has(p.bn_t, e), _has(p.bn_t, x)
    hl_ret = p.hl_o[xe] / p.hl_o[ie] - 1
    bn_ret = p.bn_o[xj] / p.bn_o[je] - 1
    basis = side * (bn_ret - hl_ret) * 1e4
    fund = side * (_cum(p.hl_ft, p.hl_fr, e, x - 1) - _cum(p.bn_ft, p.bn_fr, e, x - 1)) * 1e4
    rebal = 0
    for arr, i0, i1 in ((p.hl_o, ie, xe), (p.bn_o, je, xj)):
        ref = arr[i0]
        for px in arr[i0:i1 + 1]:
            if px >= REBALANCE_AT * ref:
                rebal += 1
                ref = px
    return XvPosition(p.coin, side, e, x, reason, float(fund), float(basis), costs.rt_bp(p.coin) * (1 + rebal), rebal)


def _last_common(p: Pair, after: int, before: int) -> int | None:
    c = np.intersect1d(p.hl_t[(p.hl_t > after) & (p.hl_t <= before)], p.bn_t[(p.bn_t > after) & (p.bn_t <= before)])
    return int(c[-1]) if len(c) else None


def run_book(pairs: dict[str, Pair], slots: int, theta_in: float, theta_out: float, lookback_d: int,
             seasoning_d: int, costs: XvCosts, start: int, end: int, rng: np.random.Generator | None = None,
             latency_d: int = 1) -> list[XvPosition]:
    """Positions over [start, end). With `rng` (the placebo), each opening takes a uniformly random eligible coin
    not held, with a random side, at the same times; it closes by the same |diff| < theta_out rule (sign ignored)."""
    held: dict[str, tuple[int, int]] = {}  # coin -> (side, entry time)
    out: list[XvPosition] = []
    D = -(-start // DAY) * DAY
    while D < end:
        ds = {}
        for c, p in pairs.items():
            if eligible(p, D, seasoning_d):
                v = diff(p, D, lookback_d)
                if v is not None:
                    ds[c] = v
        fill = D + latency_d * DAY
        for c in list(held):
            side, e = held[c]
            p = pairs[c]
            v = ds.get(c)
            gone = v is None and (p.hl_t[-1] <= D or p.bn_t[-1] <= D)
            flip = v is not None and rng is None and np.sign(v) != side
            weak = v is not None and abs(v) < theta_out
            if gone or flip or weak or (v is None and not eligible(p, D, 0)):
                x = fill if (_has(p.hl_t, fill) is not None and _has(p.bn_t, fill) is not None) else _last_common(p, e, fill)
                if x is not None and x > e:
                    out.append(_position(p, side, e, x, "data_end" if gone else "signal", costs))
                    del held[c]
                elif gone:
                    del held[c]  # no later common bar at all: nothing can be marked (counted by the caller)
        free = slots - len(held)
        if free > 0:
            cands = sorted((c for c, v in ds.items() if c not in held and abs(v) >= theta_in), key=lambda c: -abs(ds[c]))
            if rng is not None and cands:
                pool = [c for c in ds if c not in held]
                cands = list(rng.choice(pool, size=min(len(cands), len(pool)), replace=False))
            for c in cands[:free]:
                p = pairs[c]
                if _has(p.hl_t, fill) is not None and _has(p.bn_t, fill) is not None:
                    side = (int(rng.choice([-1, 1])) if rng is not None else (1 if ds[c] > 0 else -1))
                    held[c] = (side, fill)
        D += DAY
    for c, (side, e) in held.items():
        x = _last_common(pairs[c], e, end + latency_d * DAY)
        if x is not None and x > e:
            out.append(_position(pairs[c], side, e, x, "end", costs))
    return out


def daily_returns(pairs: dict[str, Pair], positions: list[XvPosition], slots: int, start: int, end: int
                  ) -> dict[int, float]:
    """Book return per day on its capital (2N x slots): each position marked at every daily open it spans."""
    days = list(range((start // DAY) * DAY, end, DAY))
    r = {d: 0.0 for d in days}
    for q in positions:
        p = pairs[q.coin]
        marks = [d for d in days if q.entry_t < d < q.exit_t] + [q.exit_t]
        prev = 0.0
        ie, je = _has(p.hl_t, q.entry_t), _has(p.bn_t, q.entry_t)
        for m in marks:
            if m == q.exit_t:
                v = q.gross_bp
            else:
                i, j = _has(p.hl_t, m), _has(p.bn_t, m)
                if i is None or j is None:
                    continue
                v = q.side * ((p.bn_o[j] / p.bn_o[je] - 1) - (p.hl_o[i] / p.hl_o[ie] - 1)) * 1e4
                v += q.side * (_cum(p.hl_ft, p.hl_fr, q.entry_t, m) - _cum(p.bn_ft, p.bn_fr, q.entry_t, m)) * 1e4
            day = ((m - 1) // DAY) * DAY
            if day in r:
                r[day] += v - prev
            prev = v
        for t in (q.entry_t, q.exit_t):
            day = (t // DAY) * DAY
            if day in r:
                r[day] -= q.cost_bp / 2
    return {d: x / 1e4 / (2 * slots) for d, x in r.items()}


__all__ = ["XV_VERSION", "Pair", "XvCosts", "XvPosition", "daily_returns", "diff", "eligible", "run_book"]
