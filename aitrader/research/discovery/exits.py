"""Exits beyond the two fixed templates: a DECLARED menu, simulated with the labels' pessimistic fills.

The research question "how should this position be managed?" is part of a hypothesis, so the
answers it may try are declared in advance and counted like any other configuration:

    E1  barrier     stop 1.0 ATR, target 1.5 ATR, 24 bars      (= template T1, the baseline)
    E2  barrier     stop 1.5 ATR, target 3.0 ATR, 48 bars      (= T2, asymmetric reward/risk)
    E3  barrier     stop 1.0 ATR, target 1.0 ATR, 12 bars      (short and symmetric)
    E4  time        protective stop 2.0 ATR, no target, exit after 24 bars   (holding period)
    E5  trailing    stop 1.5 ATR trailed from the best close, 48 bars
    E6  breakeven   stop 1.0 ATR, target 2.0 ATR; stop to entry once +1R was reached, 48 bars
    E7  partial     stop 1.0 ATR; half closed at +1R, the rest trailed 1.0 ATR, 48 bars
    E8  structure   stop beyond the last CONFIRMED swing (clipped to 0.5..3 ATR), target 2R, 48 bars

Fill conventions, identical to aitrader/research/labels.py:
- entry at the next bar's open (ASK for a buy, BID for a sell) plus slippage;
- stop checked first in every bar: a bar touching stop and target is a stop; a gap through the
  stop fills at the open; a target fills at its price, never better;
- dynamic stops (trailing, breakeven, after a partial) move only at a bar's CLOSE, so they apply
  from the next bar: nothing inside a bar is known before the bar ends;
- commission per round trip, swap per New York close crossed; R is net of all costs and
  measured in units of the INITIAL risk.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from ...data.bars import BarSeries
from ...data.resample import bucket_start
from ...features.store import SWING_K, _swings
from ..labels import BUY, CostModel, _widen, atr24

#: 1.1.0: the daily menu (D1..D5); the hourly menu is unchanged.
EXITS_VERSION = "exits-1.1.0"


@dataclass(frozen=True)
class ExitSpec:
    key: str
    kind: str  # barrier | time | trailing | breakeven | partial | structure
    stop_atr: float = 1.0
    target_atr: float | None = 1.5
    max_bars: int = 24
    trail_atr: float | None = None
    breakeven_at_r: float | None = None
    partial_at_r: float | None = None
    target_r: float | None = None  # structure: target as a multiple of the initial risk

    def __post_init__(self) -> None:
        if self.kind not in ("barrier", "time", "trailing", "breakeven", "partial", "structure"):
            raise ValueError(f"unknown exit kind {self.kind!r}")
        if self.max_bars < 1 or self.stop_atr <= 0:
            raise ValueError("an exit needs a positive stop and at least one bar")

    def describe(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


EXIT_MENU: tuple[ExitSpec, ...] = (
    ExitSpec("E1", "barrier", 1.0, 1.5, 24),
    ExitSpec("E2", "barrier", 1.5, 3.0, 48),
    ExitSpec("E3", "barrier", 1.0, 1.0, 12),
    ExitSpec("E4", "time", 2.0, None, 24),
    ExitSpec("E5", "trailing", 1.5, None, 48, trail_atr=1.5),
    ExitSpec("E6", "breakeven", 1.0, 2.0, 48, breakeven_at_r=1.0),
    ExitSpec("E7", "partial", 1.0, None, 48, trail_atr=1.0, partial_at_r=1.0),
    ExitSpec("E8", "structure", 1.0, None, 48, target_r=2.0),
)
#: the same kinds for DAILY bars (counted in D1 bars, ATR = 24-day ATR): decided once a day, where the
#: spread and commission are a far smaller fraction of the risk than on H1 (DP-001)
DAILY_EXITS: tuple[ExitSpec, ...] = (
    ExitSpec("D1", "barrier", 1.0, 1.5, 10),
    ExitSpec("D2", "barrier", 1.5, 3.0, 20),
    ExitSpec("D3", "time", 2.0, None, 5),
    ExitSpec("D4", "time", 3.0, None, 20),
    ExitSpec("D5", "trailing", 2.0, None, 40, trail_atr=2.0),
)
EXIT_BY_KEY = {e.key: e for e in EXIT_MENU + DAILY_EXITS}
STRUCTURE_BUFFER_ATR, STRUCTURE_MIN_ATR, STRUCTURE_MAX_ATR = 0.1, 0.5, 3.0


@dataclass
class ExitOutcome:
    r: np.ndarray  # net R, NaN when not computable (too close to the end of the data, no ATR)
    reason: np.ndarray  # 1 target, 2 partial+rest, -1 stop, 0 time, -9 not computable
    exit_index: np.ndarray
    resolve_time: np.ndarray
    mfe_r: np.ndarray
    mae_r: np.ndarray
    cost_r: np.ndarray
    bars_held: np.ndarray


def simulate(series: BarSeries, rows: np.ndarray, side: int, exit_: ExitSpec, pip: float,
             costs: CostModel = CostModel(), atr: np.ndarray | None = None, delay: int = 0) -> ExitOutcome:
    """Outcome of entering `side` after each decision row and managing it with `exit_`."""
    n = len(series)
    rows = np.asarray(rows, dtype=np.int64)
    m = len(rows)
    atr = atr24(series) if atr is None else atr
    out = ExitOutcome(np.full(m, np.nan), np.full(m, -9, np.int64), np.full(m, -1, np.int64),
                      np.full(m, -1, np.int64), np.full(m, np.nan), np.full(m, np.nan), np.full(m, np.nan),
                      np.full(m, -1, np.int64))
    ei_all = rows + 1 + delay
    ok = (ei_all + exit_.max_bars - 1 < n) & np.isfinite(atr[np.clip(rows, 0, n - 1)]) & (atr[np.clip(rows, 0, n - 1)] > 0)
    idx = np.flatnonzero(ok)
    if len(idx) == 0:
        return out
    px = _widen(series, costs.spread_multiple)
    slip, comm = costs.slippage_pips * pip, costs.commission_pips_rt * pip
    ei, a = ei_all[idx], atr[rows[idx]]
    if side == BUY:
        entry = px["ask_open"][ei] + slip
    else:
        entry = px["bid_open"][ei] - slip

    # the initial risk distance
    if exit_.kind == "structure":
        sw_hi, _, sw_lo, _ = _swings(series.mid_high, series.mid_low, SWING_K, 120)
        level = (sw_lo if side == BUY else sw_hi)[rows[idx]]  # known at the decision row
        raw = np.where(np.isfinite(level), (entry - level) * side + STRUCTURE_BUFFER_ATR * a, exit_.stop_atr * a)
        dist = np.clip(raw, STRUCTURE_MIN_ATR * a, STRUCTURE_MAX_ATR * a)
    else:
        dist = exit_.stop_atr * a
    stop = entry - side * dist
    if exit_.kind in ("barrier", "breakeven"):
        target = entry + side * exit_.target_atr * a
    elif exit_.kind == "structure":
        target = entry + side * exit_.target_r * dist
    else:
        target = np.full(len(idx), np.nan)
    ptarget = entry + side * (exit_.partial_at_r or 0) * dist if exit_.kind == "partial" else np.full(len(idx), np.nan)

    open_ = np.ones(len(idx), bool)
    part = np.zeros(len(idx), bool)  # half already closed (partial)
    part_px = np.full(len(idx), np.nan)
    ex_px, ex_i = np.full(len(idx), np.nan), np.full(len(idx), -1, np.int64)
    why = np.zeros(len(idx), np.int64)
    best, worst = np.full(len(idx), -np.inf), np.full(len(idx), np.inf)
    best_close = entry.copy()

    for h in range(exit_.max_bars):
        j = ei + h
        if side == BUY:
            lo, hi, op, cl = px["bid_low"][j], px["bid_high"][j], px["bid_open"][j], px["bid_close"][j]
            fav, adv = hi - entry, lo - entry
            stop_hit = open_ & (lo <= stop)
            fill_stop = np.minimum(op, stop) - slip
        else:
            lo, hi, op, cl = px["ask_low"][j], px["ask_high"][j], px["ask_open"][j], px["ask_close"][j]
            fav, adv = entry - lo, entry - hi
            stop_hit = open_ & (hi >= stop)
            fill_stop = np.maximum(op, stop) + slip
        best = np.where(open_, np.maximum(best, fav), best)
        worst = np.where(open_, np.minimum(worst, adv), worst)
        ex_px = np.where(stop_hit, fill_stop, ex_px)
        why = np.where(stop_hit, -1, why)
        ex_i = np.where(stop_hit, j, ex_i)
        open_ &= ~stop_hit
        reach = (hi >= target) if side == BUY else (lo <= target)
        tgt_hit = open_ & np.isfinite(target) & reach
        ex_px = np.where(tgt_hit, target, ex_px)
        why = np.where(tgt_hit, 1, why)
        ex_i = np.where(tgt_hit, j, ex_i)
        open_ &= ~tgt_hit
        if exit_.kind == "partial":
            preach = (hi >= ptarget) if side == BUY else (lo <= ptarget)
            take = open_ & ~part & preach
            part_px = np.where(take, ptarget, part_px)
            part |= take
        if h == exit_.max_bars - 1:
            t_exit = cl - side * slip
            ex_px = np.where(open_, t_exit, ex_px)
            ex_i = np.where(open_, j, ex_i)
            why = np.where(open_, 0, why)
            open_[:] = False
            break
        # stops move at the close, for the next bar
        best_close = np.where(open_, np.maximum(best_close * side, cl * side) * side, best_close)
        if exit_.kind == "trailing" or (exit_.kind == "partial" and exit_.trail_atr):
            trail = best_close - side * exit_.trail_atr * a
            active = open_ if exit_.kind == "trailing" else open_ & part
            stop = np.where(active, np.maximum(stop * side, trail * side) * side, stop)
        if exit_.kind == "partial":
            stop = np.where(open_ & part, np.maximum(stop * side, entry * side) * side, stop)
        if exit_.kind == "breakeven":
            reached = open_ & (best >= exit_.breakeven_at_r * dist)
            stop = np.where(reached, np.maximum(stop * side, entry * side) * side, stop)

    day = bucket_start(series.open_time, "D1")
    nights = np.maximum(0, (day[ex_i] - day[ei]) // 86400)
    swap = costs.swap_atr_per_night * a * nights
    full = (ex_px - entry) * side
    if exit_.kind == "partial":
        gross = np.where(part, 0.5 * (part_px - entry) * side + 0.5 * full, full)
        why = np.where(part & (why != 1), 2, why)
    else:
        gross = full
    out.r[idx] = (gross - comm - swap) / dist
    out.reason[idx] = why
    out.exit_index[idx] = ex_i
    out.resolve_time[idx] = series.available_at[ex_i]
    out.mfe_r[idx] = best / dist
    out.mae_r[idx] = worst / dist
    spread_entry = px["ask_open"][ei] - px["bid_open"][ei]
    out.cost_r[idx] = (spread_entry + 2 * slip + comm + swap) / dist
    out.bars_held[idx] = ex_i - ei + 1
    return out
