"""Crypto perpetual-futures research (CR-1 funding carry, CR-2 time-series momentum), research only.

Data: Binance public archives (data.binance.vision). Per coin: 1-hour spot and USDT-M perpetual klines (open
time, open, close) and the perpetual's funding settlements (time, rate). Funding is the REAL cash flow: a short
perpetual receives `rate x notional` at each settlement and a long pays it. Nothing about financing is
approximated.

Costs (declared, `CrCosts`; stressed by `stressed(k)`):

- exchange fees, Binance VIP 0 taker: spot 10 bp, USDT-M perpetual 5 bp per side (the highest regular tier);
- half-spread per fill (no historical bid/ask is public: a declared approximation): 1 bp for BTC and ETH,
  2 bp otherwise;
- slippage per fill: 1 bp.

Time conventions (every decision uses only what was public at its time):

- a funding settlement at time T is known at T;
- a decision taken at T fills at the open of the first 1-hour bar opening at or after T + `latency_h` hours on
  which every leg it needs has a bar (at most 3 hours later, else the order is skipped);
- a daily decision at 00:00 UTC uses prices up to that time: the opens of the bars opening at 00:00.

Accounting: per coin, a mark-to-market ledger in bp of the position's notional N, sampled at 00:00 UTC each
day. Capital per coin is 2N for the carry (spot N plus perpetual margin N: 1x short, no liquidation below a
+100% move) and N for momentum (1x). The portfolio's daily return is the equal-capital mean over coins
(a flat coin earns 0: idle cash is credited nothing).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np

CR_VERSION = "cr-1.0.0"
H = 3600
DAY = 86400
#: The carry's short perpetual is margined 1x (capital 2N). If the perpetual's price reaches this multiple of its
#: entry price during the position, the margin is close to exhausted: the position is charged one more full round
#: trip on both legs (closing and reopening to move spot gains into margin), and the event is counted.
REBALANCE_AT = 1.8


@dataclass(frozen=True)
class Coin:
    symbol: str
    spot_t: np.ndarray  # 1h bar open times, epoch s
    spot_o: np.ndarray
    perp_t: np.ndarray
    perp_o: np.ndarray
    fund_t: np.ndarray  # settlement times, epoch s
    fund_r: np.ndarray  # rate per settlement (0.0001 = 1 bp)

    def __post_init__(self) -> None:
        for t in (self.spot_t, self.perp_t, self.fund_t):
            if len(t) > 1 and not np.all(np.diff(t) > 0):
                raise ValueError(f"{self.symbol}: times must be strictly increasing")

    def truncated(self, t_end: int) -> "Coin":
        """Everything public strictly before `t_end` (a bar is public at its open for its open price)."""
        a, b, c = (np.searchsorted(x, t_end, "left") for x in (self.spot_t, self.perp_t, self.fund_t))
        return Coin(self.symbol, self.spot_t[:a], self.spot_o[:a], self.perp_t[:b], self.perp_o[:b],
                    self.fund_t[:c], self.fund_r[:c])


@dataclass(frozen=True)
class CrCosts:
    spot_fee_bp: float = 10.0
    perp_fee_bp: float = 5.0
    half_spread_bp: float = 2.0  # BTC/ETH get `major_half_spread_bp`
    major_half_spread_bp: float = 1.0
    slip_bp: float = 1.0
    latency_h: int = 1
    k: float = 1.0  # the stress multiplier already applied (recorded)

    def stressed(self, k: float) -> "CrCosts":
        return replace(self, spot_fee_bp=self.spot_fee_bp * k, perp_fee_bp=self.perp_fee_bp * k,
                       half_spread_bp=self.half_spread_bp * k, major_half_spread_bp=self.major_half_spread_bp * k,
                       slip_bp=self.slip_bp * k, k=self.k * k)

    def half(self, symbol: str) -> float:
        return self.major_half_spread_bp if symbol in ("BTCUSDT", "ETHUSDT") else self.half_spread_bp


@dataclass(frozen=True)
class Position:
    symbol: str
    side: int  # carry: +1 (long spot, short perp); momentum: +1 long perp / -1 short perp
    entry_t: int
    exit_t: int
    reason: str
    funding_bp: float  # received (+) or paid (-)
    basis_bp: float  # price P&L of the legs, bp of N
    cost_bp: float  # fees + spread + slippage, both fills, all legs (plus any forced rebalance)
    rebalances: int = 0  # carry only: times the perpetual rose REBALANCE_AT above entry (margin would run out)

    @property
    def gross_bp(self) -> float:
        return self.funding_bp + self.basis_bp

    @property
    def net_bp(self) -> float:
        return self.gross_bp - self.cost_bp


@dataclass
class Result:
    positions: list[Position] = field(default_factory=list)
    daily: dict[int, float] = field(default_factory=dict)  # day start epoch -> return on capital (fraction)
    skipped: dict[str, int] = field(default_factory=lambda: {"no_bar": 0})


def _fill(t_arr: list[np.ndarray], when: int, max_wait_h: int = 3) -> tuple[int, list[int]] | None:
    """The first hour >= `when` (on the hour) at which every leg has a bar; (time, indices) or None."""
    start = -(-when // H) * H
    for k in range(max_wait_h + 1):
        t = start + k * H
        idx = []
        for arr in t_arr:
            i = int(np.searchsorted(arr, t))
            if i >= len(arr) or arr[i] != t:
                break
            idx.append(i)
        else:
            return t, idx
    return None


def _day(t: int) -> int:
    return (t // DAY) * DAY


# ── CR-1: funding carry ─────────────────────────────────────────────────

def carry_positions(c: Coin, theta_in: float, theta_out: float, k: int, costs: CrCosts, start: int, end: int,
                    entries: list[tuple[int, int]] | None = None) -> tuple[list[Position], int]:
    """Long spot + short perpetual while the mean of the last `k` funding rates (known at each settlement) is
    >= `theta_in` to open and until it is < `theta_out`. Decisions are taken only at settlements in
    [start, end). A position still open at `end` is closed at the first bar at or after `end`.
    `entries` replaces the rule with given (decision time, hold seconds) pairs: the timing placebo."""
    half = costs.half(c.symbol)
    rt_cost = 2 * (costs.spot_fee_bp + half + costs.slip_bp) + 2 * (costs.perp_fee_bp + half + costs.slip_bp)
    legs = [c.spot_t, c.perp_t]
    out: list[Position] = []
    skipped = 0

    def close(e_t, e_idx, x_when, reason):
        nonlocal skipped
        f = _fill(legs, x_when)
        if f is None:
            skipped += 1
            return None
        x_t, x_idx = f
        s_in, p_in = c.spot_o[e_idx[0]], c.perp_o[e_idx[1]]
        s_out, p_out = c.spot_o[x_idx[0]], c.perp_o[x_idx[1]]
        basis = ((s_out / s_in - 1) - (p_out / p_in - 1)) * 1e4
        m = (c.fund_t > e_t) & (c.fund_t < x_t)
        fund = float(c.fund_r[m].sum() * 1e4)  # the short perpetual receives positive funding
        held = c.perp_o[e_idx[1]:x_idx[1] + 1]
        rebal = 0
        ref = p_in
        for px in held:  # each time the perpetual reaches REBALANCE_AT x the reference, one forced round trip
            if px >= REBALANCE_AT * ref:
                rebal += 1
                ref = px
        return Position(c.symbol, 1, e_t, x_t, reason, fund, float(basis), rt_cost * (1 + rebal), rebal)

    if entries is not None:
        for when, hold in entries:
            f = _fill(legs, when + costs.latency_h * H)
            if f is None:
                skipped += 1
                continue
            p = close(f[0], f[1], f[0] + hold, "placebo")
            if p is not None:
                out.append(p)
        return out, skipped

    pos = None  # (entry time, entry indices)
    for i in range(len(c.fund_t)):
        T = int(c.fund_t[i])
        if T < start:
            continue
        if T >= end:
            break
        if i + 1 < k:
            continue
        m = float(c.fund_r[i - k + 1:i + 1].mean())
        if pos is None and m >= theta_in:
            f = _fill(legs, T + costs.latency_h * H)
            if f is None:
                skipped += 1
                continue
            pos = f
        elif pos is not None and m < theta_out:
            p = close(pos[0], pos[1], T + costs.latency_h * H, "signal")
            if p is not None:
                out.append(p)
                pos = None
    if pos is not None:
        p = close(pos[0], pos[1], end, "end")
        if p is not None:
            out.append(p)
    return out, skipped


# ── CR-2: time-series momentum on the perpetual ─────────────────────────

def momentum_positions(c: Coin, lookback_d: int, costs: CrCosts, start: int, end: int,
                       sides: dict[int, int] | None = None) -> tuple[list[Position], int]:
    """At each 00:00 UTC in [start, end): target side = sign of the perpetual's return over the previous
    `lookback_d` days (opens at 00:00), executed `latency_h` later. A position is a run of days with the same
    side; it pays or receives the actual funding. `sides` replaces the signal (day -> side): the direction
    placebo."""
    half = costs.half(c.symbol)
    per_side = costs.perp_fee_bp + half + costs.slip_bp
    legs = [c.perp_t]
    out: list[Position] = []
    skipped = 0
    cur = None  # (side, entry time, entry index)
    day = _day(start) if start % DAY == 0 else _day(start) + DAY
    while day < end:
        if sides is not None:
            want = sides.get(day, 0)
        else:
            i0, i1 = np.searchsorted(c.perp_t, [day - lookback_d * DAY, day])
            ok = (i1 < len(c.perp_t) and c.perp_t[min(i1, len(c.perp_t) - 1)] == day and i0 < len(c.perp_t)
                  and c.perp_t[i0] == day - lookback_d * DAY)
            want = int(np.sign(c.perp_o[i1] / c.perp_o[i0] - 1)) if ok else 0
        if cur is not None and want != cur[0]:
            f = _fill(legs, day + costs.latency_h * H)
            if f is None:
                skipped += 1
            else:
                x_t, (xi,) = f
                side, e_t, ei = cur
                move = (c.perp_o[xi] / c.perp_o[ei] - 1) * 1e4 * side
                m = (c.fund_t > e_t) & (c.fund_t < x_t)
                fund = float(-side * c.fund_r[m].sum() * 1e4)  # a long pays positive funding
                out.append(Position(c.symbol, side, e_t, x_t, "flip", fund, float(move), 2 * per_side))
                cur = None
        if cur is None and want != 0:
            f = _fill(legs, day + costs.latency_h * H)
            if f is None:
                skipped += 1
            else:
                cur = (want, f[0], f[1][0])
        day += DAY
    if cur is not None:
        f = _fill(legs, end)
        if f is not None:
            side, e_t, ei = cur
            x_t, (xi,) = f
            move = (c.perp_o[xi] / c.perp_o[ei] - 1) * 1e4 * side
            m = (c.fund_t > e_t) & (c.fund_t < x_t)
            out.append(Position(c.symbol, side, e_t, x_t, "end", float(-side * c.fund_r[m].sum() * 1e4),
                                float(move), 2 * per_side))
    return out, skipped


# ── daily mark-to-market ────────────────────────────────────────────────

def daily_returns(c: Coin, positions: list[Position], capital_per_n: float, start: int, end: int,
                  kind: str) -> dict[int, float]:
    """Each position's P&L spread over the days it was held, marked at 00:00 UTC from the hourly opens:
    funding on its settlement day, price moves day by day, costs half on the entry day and half on the exit
    day. Returned as a fraction of the coin's capital (capital_per_n x N)."""
    days = np.arange(_day(start), end, DAY)
    r = np.zeros(len(days))

    def px(arr_t, arr_o, t):
        i = int(np.searchsorted(arr_t, t, "right")) - 1
        return arr_o[i] if i >= 0 else np.nan

    for p in positions:
        marks = [p.entry_t] + [int(d) for d in days if p.entry_t < d < p.exit_t] + [p.exit_t]
        prev = 0.0
        for a, b in zip(marks, marks[1:]):
            if kind == "carry":
                v = ((px(c.spot_t, c.spot_o, b) / px(c.spot_t, c.spot_o, p.entry_t) - 1)
                     - (px(c.perp_t, c.perp_o, b) / px(c.perp_t, c.perp_o, p.entry_t) - 1)) * 1e4
                m = (c.fund_t > p.entry_t) & (c.fund_t <= b) & (c.fund_t < p.exit_t)
                v += c.fund_r[m].sum() * 1e4
            else:
                v = (px(c.perp_t, c.perp_o, b) / px(c.perp_t, c.perp_o, p.entry_t) - 1) * 1e4 * p.side
                m = (c.fund_t > p.entry_t) & (c.fund_t <= b) & (c.fund_t < p.exit_t)
                v += -p.side * c.fund_r[m].sum() * 1e4
            if b == p.exit_t:
                v = p.gross_bp  # the exact position total at the exit
            j = int(np.searchsorted(days, _day(b - 1) if b % DAY == 0 else _day(b), "right")) - 1
            if 0 <= j < len(days):
                r[j] += v - prev
            prev = v
        for t in (p.entry_t, p.exit_t):
            j = int(np.searchsorted(days, _day(t), "right")) - 1
            if 0 <= j < len(days):
                r[j] -= p.cost_bp / 2
    return {int(d): float(x) / 1e4 / capital_per_n for d, x in zip(days, r)}


def portfolio(per_coin: dict[str, dict[int, float]]) -> dict[int, float]:
    """Equal capital per coin: the mean of the coins' daily returns (a coin with no capital deployed earns 0)."""
    days = sorted(set().union(*[set(v) for v in per_coin.values()])) if per_coin else []
    return {d: float(np.mean([v.get(d, 0.0) for v in per_coin.values()])) for d in days}


__all__ = ["CR_VERSION", "REBALANCE_AT", "Coin", "CrCosts", "Position", "Result", "carry_positions",
           "daily_returns", "momentum_positions", "portfolio"]
