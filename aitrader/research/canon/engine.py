"""The canonical bid/ask event engine for new research (NEW_EDGE_AUDIT.md §7: six simulators existed, each
with its own fill rules; every hypothesis registered from NE-* onward is judged by this one).

Bar-by-bar, one position per instrument, every price an executable quote:

- **Decision.** An `Order` names the last bar whose CLOSE the decision used (`decided_i`). Nothing in
  this module reads a bar's prices before it is reached in time order.
- **Entry.** A market order at the open of the first valid bar after `decided_i` (plus `latency_bars`):
  a buy at the ask, a sell at the bid, plus slippage. A bar whose ask <= bid at the open or close is NOT
  a quote (index-CFD history before 2014 is one-sided, NEW_EDGE_AUDIT.md §3). It is skipped, never used
  as a price.
- **Spread stress** widens each side of every quote around the mid: `spread_mult` = 1.5 means a spread
  50% wider than quoted.
- **Stop** (protective, a market order once triggered). Triggered when the exit side of the quote (the
  bid for a long, the ask for a short) reaches the level. It fills `stop_through_frac` of the bar's
  spread beyond the level, plus slippage, or at the bar's open if the bar opened beyond the level.
  Filling exactly at the level manufactures edge on noise (IX-4's finding); the random-walk tests
  bound it.
- **Target** (a limit order). Triggered when the exit side reaches it. It fills AT the level, never
  better, even on a gap. A bar that reaches both stop and target counts as the stop.
- **Time exit.** A market order at the open of the first valid bar at or after `exit_at`, or after
  `max_bars` bars.
- **Financing.** For every 17:00 New York rollover strictly after the entry and at or before the exit,
  a long pays (benchmark + markup) and a short receives (benchmark − markup), per calendar day: a
  Friday rollover counts 3 days. The day count is 360. A short over a rollover also pays a declared
  dividend yield. An unknown benchmark skips the trade ("no_rate"); a rate is never assumed.

Every trade carries a cost ledger in basis points of the entry mid:
gross (the move of the mid), spread, slippage, stop through-fill, commission, financing and net.
The identity is

    net_bp = side*(exit_px - entry_px)/mid_in*1e4 - commission_bp - financing_bp

and it is asserted for every trade.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Callable
from zoneinfo import ZoneInfo

import numpy as np

CANON_VERSION = "canon-1.0.0"
NY = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class Quotes:
    """Bid and ask bars of one instrument, oldest first, labelled by their open (UTC epoch seconds)."""

    symbol: str
    period: int
    t: np.ndarray
    bo: np.ndarray
    bh: np.ndarray
    bl: np.ndarray
    bc: np.ndarray
    ao: np.ndarray
    ah: np.ndarray
    al: np.ndarray
    ac: np.ndarray

    def __post_init__(self) -> None:
        n = len(self.t)
        for k in ("bo", "bh", "bl", "bc", "ao", "ah", "al", "ac"):
            if len(getattr(self, k)) != n:
                raise ValueError(f"{k} has {len(getattr(self, k))} rows, t has {n}")
        if n and not np.all(np.diff(self.t) > 0):
            raise ValueError("bar times must be strictly increasing")
        object.__setattr__(self, "valid", (self.ao > self.bo) & (self.ac > self.bc))

    @classmethod
    def from_series(cls, s) -> "Quotes":
        f = lambda x: np.asarray(x, float)  # noqa: E731
        return cls(s.symbol, int(s.period), np.asarray(s.open_time, np.int64), f(s.bid_open), f(s.bid_high),
                   f(s.bid_low), f(s.bid_close), f(s.ask_open), f(s.ask_high), f(s.ask_low), f(s.ask_close))

    def __len__(self) -> int:
        return len(self.t)

    def mid_open(self) -> np.ndarray:
        return (self.bo + self.ao) / 2

    def mid_close(self) -> np.ndarray:
        return (self.bc + self.ac) / 2

    def at_or_after(self, epoch: int) -> int:
        """Index of the first bar opening at or after `epoch` (len(self) if none)."""
        return int(np.searchsorted(self.t, epoch, "left"))

    def truncated(self, last_i: int) -> "Quotes":
        """The bars up to and including `last_i`: what existed when bar `last_i` closed."""
        k = slice(0, last_i + 1)
        return Quotes(self.symbol, self.period, self.t[k], self.bo[k], self.bh[k], self.bl[k], self.bc[k],
                      self.ao[k], self.ah[k], self.al[k], self.ac[k])


@dataclass(frozen=True)
class Order:
    decided_i: int  # the last bar whose close the decision used
    side: int  # +1 long, -1 short
    exit_at: int | None = None  # epoch: market exit at the first valid open at or after it
    stop_bp: float | None = None  # stop distance, bp of the entry mid
    target_bp: float | None = None  # target distance, bp of the entry mid
    max_bars: int | None = None
    tag: str = ""


RateFn = Callable[[int], float]  # epoch -> benchmark annual percent public then (NaN if unknown)


@dataclass(frozen=True)
class Costs:
    spread_mult: float = 1.0
    slip_frac: float = 0.25  # slippage per market fill, as a fraction of that bar's (stressed) spread
    stop_through_frac: float = 0.5  # a triggered stop fills this fraction of the spread beyond its level
    commission_bp_side: float = 0.0  # index CFDs are spread-only
    markup_pa: float = 2.5  # financing markup, percent a year
    short_dividend_pa: float = 0.0  # declared dividend yield a short pays over rollovers
    day_count: int = 360
    latency_bars: int = 0

    def stressed(self, k: float) -> "Costs":
        """Every cost multiplied by k: spread, slippage (it scales with the widened spread), commission and
        the financing markup."""
        return replace(self, spread_mult=self.spread_mult * k, commission_bp_side=self.commission_bp_side * k,
                       markup_pa=self.markup_pa * k)


@dataclass(frozen=True)
class Trade:
    symbol: str
    tag: str
    side: int
    decided_t: int
    entry_t: int
    exit_t: int
    reason: str  # time | stop | target | max_bars | end
    mid_in: float
    entry_px: float
    exit_px: float
    gross_bp: float
    spread_bp: float
    slip_bp: float
    through_bp: float
    comm_bp: float
    fin_bp: float
    days_financed: int
    stop_bp: float | None

    @property
    def net_bp(self) -> float:
        return self.gross_bp - self.spread_bp - self.slip_bp - self.through_bp - self.comm_bp - self.fin_bp

    @property
    def cost_bp(self) -> float:
        return self.gross_bp - self.net_bp

    @property
    def net_r(self) -> float | None:
        return self.net_bp / self.stop_bp if self.stop_bp else None


@dataclass
class Run:
    trades: list[Trade] = field(default_factory=list)
    skipped: dict[str, int] = field(default_factory=lambda: {"busy": 0, "no_quote": 0, "no_rate": 0, "end": 0})


def rollovers(t0: int, t1: int) -> list[tuple[int, int]]:
    """(epoch, days) of each 17:00 New York rollover with t0 < epoch <= t1; a Friday's counts 3 days.
    Weekends hold no rollover (CFDs do not trade)."""
    out = []
    d = datetime.fromtimestamp(t0, timezone.utc).astimezone(NY).date()
    end = datetime.fromtimestamp(t1, timezone.utc).astimezone(NY).date()
    while d <= end:
        if d.weekday() < 5:
            r = int(datetime(d.year, d.month, d.day, 17, tzinfo=NY).timestamp())
            if t0 < r <= t1:
                out.append((r, 3 if d.weekday() == 4 else 1))
        d = d.fromordinal(d.toordinal() + 1)
    return out


def simulate(q: Quotes, orders: list[Order], costs: Costs = Costs(), rate: RateFn | None = None) -> Run:
    """Trades for `orders` (ascending `decided_i`), one position at a time. `rate` is required for any
    trade that crosses a rollover; without it such a trade is skipped as "no_rate"."""
    run = Run()
    n = len(q)
    valid = q.valid
    free_from = -1  # the first bar index at which a new position may be opened

    def half(j: int) -> float:
        return (q.ao[j] - q.bo[j]) / 2 * costs.spread_mult

    def widen(j: int) -> float:
        return (q.ao[j] - q.bo[j]) / 2 * (costs.spread_mult - 1.0)

    for o in sorted(orders, key=lambda x: x.decided_i):
        if o.side not in (1, -1):
            raise ValueError(f"side must be +1 or -1, got {o.side}")
        j = o.decided_i + 1 + costs.latency_bars
        while j < n and not valid[j]:
            j += 1
        if j >= n:
            run.skipped["end"] += 1
            continue
        if j <= free_from:
            run.skipped["busy"] += 1
            continue
        if j - (o.decided_i + 1 + costs.latency_bars) > 2:  # no two-sided quote near the intended entry
            run.skipped["no_quote"] += 1
            continue
        side = o.side
        ei = j
        mid_in = (q.ao[ei] + q.bo[ei]) / 2
        h_in = half(ei)
        s_in = costs.slip_frac * 2 * h_in
        entry_px = mid_in + side * (h_in + s_in)
        stop = entry_px - side * o.stop_bp * mid_in / 1e4 if o.stop_bp else None
        target = entry_px + side * o.target_bp * mid_in / 1e4 if o.target_bp else None
        last = n - 1 if o.max_bars is None else min(n - 1, ei + o.max_bars)
        xi, exit_px, why, h_out, s_out, thr = None, None, None, 0.0, 0.0, 0.0
        for k in range(ei, n):
            if valid[k] and k > ei and ((o.exit_at is not None and q.t[k] >= o.exit_at) or k >= last):
                xi = k
                why = ("time" if o.exit_at is not None and q.t[k] >= o.exit_at
                       else "max_bars" if o.max_bars is not None else "end")
                h_out = half(k)
                s_out = costs.slip_frac * 2 * h_out
                exit_px = (q.ao[k] + q.bo[k]) / 2 - side * (h_out + s_out)
                break
            # a one-sided bar is no price to fill at, but its range still happened: it can trigger the stop or
            # target, filled with the entry bar's spread (never with its own zero spread)
            hk = half(k) if valid[k] else h_in
            w = widen(k) if valid[k] else h_in  # a one-sided price is a mid: move it out by a full half spread
            if side > 0:
                lo, hi, op = q.bl[k] - w, q.bh[k] - w, q.bo[k] - w
                hit_stop = stop is not None and lo <= stop
                hit_tgt = target is not None and hi >= target
            else:
                lo, hi, op = q.al[k] + w, q.ah[k] + w, q.ao[k] + w
                hit_stop = stop is not None and hi >= stop
                hit_tgt = target is not None and lo <= target
            if hit_stop:
                h_out = hk
                s_out = costs.slip_frac * 2 * h_out
                gapped = (op <= stop) if side > 0 else (op >= stop)
                if gapped and k > ei:
                    thr = 0.0
                    exit_px = op - side * s_out
                else:
                    thr = costs.stop_through_frac * 2 * h_out
                    exit_px = stop - side * (thr + s_out)
                xi, why = k, "stop"
                break
            if hit_tgt:
                h_out, s_out, thr = hk, 0.0, 0.0
                exit_px, xi, why = target, k, "target"
                break
        if xi is None:
            run.skipped["end"] += 1
            break
        # the mid the exit is measured against: the fill with its spread, slippage and through-fill removed
        mid_out = exit_px + side * (h_out + s_out + thr)
        nights = rollovers(int(q.t[ei]), int(q.t[xi]))
        days = sum(d for _, d in nights)
        fin = 0.0
        if days:
            if rate is None:
                run.skipped["no_rate"] += 1
                free_from = xi
                continue
            fin_pct = 0.0
            bad = False
            for r_t, d in nights:
                b = rate(r_t)
                if b is None or not math.isfinite(b):
                    bad = True
                    break
                per_day = side * b + costs.markup_pa  # long pays b + markup; short receives b - markup
                if side < 0:
                    per_day += costs.short_dividend_pa
                fin_pct += per_day * d / costs.day_count
            if bad:
                run.skipped["no_rate"] += 1
                free_from = xi
                continue
            fin = fin_pct * 100.0  # percent of notional -> bp
        bp = 1e4 / mid_in
        tr = Trade(q.symbol, o.tag, side, int(q.t[o.decided_i]), int(q.t[ei]), int(q.t[xi]), why, float(mid_in),
                   float(entry_px), float(exit_px), float(side * (mid_out - mid_in) * bp),
                   float((h_in + h_out) * bp), float((s_in + s_out) * bp), float(thr * bp),
                   float(2 * costs.commission_bp_side), float(fin), int(days), o.stop_bp)
        ident = side * (exit_px - entry_px) * bp - tr.comm_bp - tr.fin_bp
        if abs(ident - tr.net_bp) > 1e-6 * max(1.0, abs(ident)):
            raise AssertionError(f"cost ledger does not add up: {ident} vs {tr.net_bp}")
        run.trades.append(tr)
        free_from = xi
    return run


__all__ = ["CANON_VERSION", "Costs", "Order", "Quotes", "Run", "Trade", "rollovers", "simulate"]
