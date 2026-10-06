"""CR-3: cross-sectional funding carry over the point-in-time Binance universe (research only).

At each global funding time T (00:00, 08:00, 16:00 UTC) the ELIGIBLE coins are those whose perpetual and spot
both have a bar at T and have traded for at least `seasoning_d` days. Each is scored by the funding its
perpetual actually paid over the 24 hours to T (the sum of settlements in (T - 24 h, T]; this handles 4-hour and
8-hour intervals alike). The book holds up to `slots` delta-neutral positions (long spot, short perpetual, equal
notional, 2N capital per slot):

- a held coin is kept while it stays eligible, its score is >= `theta_out`, and it ranks in the top 2 x `slots`;
- an empty slot is filled with the best-scored eligible coin not held whose score >= `theta_in`.

Fills, funding, costs and forced rebalances are exactly CR-1's (`cr.py`). A coin whose data ends while held
(delisting) is closed at its last common bar. Costs by liquidity tier (declared): BTC/ETH half-spread 1 bp and
slippage 1 bp; the 11 CR-1 coins 2 bp / 1 bp; every other coin 5 bp / 3 bp.

Everything at T uses only data up to T: scores from settlements <= T, eligibility from bars <= T.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from . import cr as C

XS_VERSION = "xs-1.0.0"
H, DAY = C.H, C.DAY
MAJORS = ("BTCUSDT", "ETHUSDT")
TIER2 = ("ADAUSDT", "BCHUSDT", "EOSUSDT", "ETCUSDT", "LINKUSDT", "LTCUSDT", "TRXUSDT", "XLMUSDT", "XRPUSDT")


@dataclass(frozen=True)
class XsCosts:
    spot_fee_bp: float = 10.0
    perp_fee_bp: float = 5.0
    latency_h: int = 1
    k: float = 1.0

    def tier(self, sym: str) -> tuple[float, float]:
        """(half-spread, slippage) in bp, stressed."""
        if sym in MAJORS:
            return 1.0 * self.k, 1.0 * self.k
        if sym in TIER2:
            return 2.0 * self.k, 1.0 * self.k
        return 5.0 * self.k, 3.0 * self.k

    def rt_bp(self, sym: str) -> float:
        h, s = self.tier(sym)
        return 2 * (self.spot_fee_bp * self.k + h + s) + 2 * (self.perp_fee_bp * self.k + h + s)

    def stressed(self, k: float) -> "XsCosts":
        return replace(self, k=self.k * k)


_CUM: dict[int, np.ndarray] = {}


def score(c: C.Coin, T: int) -> float:
    """Funding paid over (T - 24 h, T]; NaN when no settlement fell in the window."""
    cum = _CUM.get(id(c))
    if cum is None or len(cum) != len(c.fund_r) + 1:
        cum = np.r_[0.0, np.cumsum(c.fund_r)]
        _CUM[id(c)] = cum
    a = int(np.searchsorted(c.fund_t, T - DAY, "right"))
    b = int(np.searchsorted(c.fund_t, T, "right"))
    return float(cum[b] - cum[a]) if b > a else float("nan")


def eligible(c: C.Coin, T: int, seasoning_d: int) -> bool:
    if not len(c.spot_t) or not len(c.perp_t):
        return False
    if c.spot_t[0] > T - seasoning_d * DAY or c.perp_t[0] > T - seasoning_d * DAY:
        return False
    i, j = np.searchsorted(c.spot_t, T), np.searchsorted(c.perp_t, T)
    return bool(i < len(c.spot_t) and c.spot_t[i] == T and j < len(c.perp_t) and c.perp_t[j] == T)


def _close(c: C.Coin, e: tuple[int, list[int]], when: int, reason: str, costs: XsCosts) -> C.Position:
    legs = [c.spot_t, c.perp_t]
    f = C._fill(legs, when)
    if f is None:  # data ended (delisting) or a gap: the last common bar at or before `when`
        common = np.intersect1d(c.spot_t[c.spot_t <= when], c.perp_t[c.perp_t <= when])
        common = common[common > e[0]]
        if not len(common):
            common = np.array([e[0]])
        t = int(common[-1])
        f = (t, [int(np.searchsorted(c.spot_t, t)), int(np.searchsorted(c.perp_t, t))])
        reason = "data_end" if reason != "end" else reason
    x_t, x_idx = f
    e_t, e_idx = e
    s_in, p_in = c.spot_o[e_idx[0]], c.perp_o[e_idx[1]]
    s_out, p_out = c.spot_o[x_idx[0]], c.perp_o[x_idx[1]]
    basis = ((s_out / s_in - 1) - (p_out / p_in - 1)) * 1e4
    m = (c.fund_t > e_t) & (c.fund_t < x_t)
    fund = float(c.fund_r[m].sum() * 1e4)
    rebal, ref = 0, p_in
    for px in c.perp_o[e_idx[1]:x_idx[1] + 1]:
        if px >= C.REBALANCE_AT * ref:
            rebal += 1
            ref = px
    return C.Position(c.symbol, 1, e_t, x_t, reason, fund, float(basis), costs.rt_bp(c.symbol) * (1 + rebal), rebal)


def run_book(coins: dict[str, C.Coin], slots: int, theta_in: float, theta_out: float, seasoning_d: int,
             costs: XsCosts, start: int, end: int, rng: np.random.Generator | None = None) -> list[C.Position]:
    """The book's positions over [start, end). With `rng` (the selection placebo), every opening picks a uniformly
    random eligible coin not held, at the same times and with the same number of slots, and a held coin is closed
    by the same funding exit (score < theta_out) without the top-2N condition."""
    held: dict[str, tuple[int, list[int]]] = {}
    out: list[C.Position] = []
    T = -(-start // (8 * H)) * 8 * H
    while T < end:
        scores = {s: score(c, T) for s, c in coins.items() if eligible(c, T, seasoning_d)}
        scores = {s: v for s, v in scores.items() if np.isfinite(v)}
        ranked = sorted(scores, key=lambda s: -scores[s])
        top2 = set(ranked[:2 * slots])
        for s in list(held):
            c = coins[s]
            keep = s in scores and scores[s] >= theta_out and (rng is not None or s in top2)
            data_left = c.perp_t[-1] > T and c.spot_t[-1] > T
            if not keep or not data_left:
                out.append(_close(c, held.pop(s), T + costs.latency_h * H, "signal" if data_left else "data_end",
                                  costs))
        free = slots - len(held)
        if free > 0:
            cands = [s for s in ranked if s not in held and scores[s] >= theta_in]
            if rng is not None and cands:
                pool = [s for s in scores if s not in held]
                cands = list(rng.choice(pool, size=min(len(cands), len(pool)), replace=False))
            for s in cands[:free]:
                f = C._fill([coins[s].spot_t, coins[s].perp_t], T + costs.latency_h * H)
                if f is not None:
                    held[s] = f
        T += 8 * H
    for s, e in held.items():
        out.append(_close(coins[s], e, end, "end", costs))
    return out


def book_daily(coins: dict[str, C.Coin], positions: list[C.Position], slots: int, start: int, end: int
               ) -> dict[int, float]:
    """Daily return on the book's capital (2N per slot): the sum of positions' daily P&L / (2 x slots)."""
    total: dict[int, float] = {}
    by: dict[str, list[C.Position]] = {}
    for p in positions:
        by.setdefault(p.symbol, []).append(p)
    for s, ps in by.items():
        for d, x in C.daily_returns(coins[s], ps, 1.0, start, end, "carry").items():
            total[d] = total.get(d, 0.0) + x
    days = range((start // DAY) * DAY, end, DAY)
    return {d: total.get(d, 0.0) / (2 * slots) for d in days}


__all__ = ["XS_VERSION", "XsCosts", "book_daily", "eligible", "run_book", "score"]
