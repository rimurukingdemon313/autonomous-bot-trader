"""Outcome labels: what a trade decided at bar i would actually have returned.

Labels look forward by design, so they exist ONLY for training and
evaluation, never as inputs to a decision. Each label records the moment
its outcome became known (`resolve_time`); any consumer that learns from
labels (the analog memory, lesson validation) may only use a label at a
time after that moment.

Fills are pessimistic and use the REAL bid/ask of each bar:
- a BUY enters at the next bar's ASK open and exits on the BID; a SELL the mirror;
- stop and target inside one bar resolve as the stop;
- a stop the bar gaps through fills at the open; a target fills at its price,
  never better;
- slippage on every market fill, commission per round trip, and swap per New
  York close crossed.

Cost items that are not in the data are DECLARED approximations
(DATA_CONTRACT.md §4) and are reported with every result that uses them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..data.bars import BarSeries
from ..data.resample import bucket_start
from ..features.store import INDEX, _lag, _roll

LABEL_VERSION = "label-1.0.0"
BUY, SELL = 1, -1


@dataclass(frozen=True)
class Template:
    """A declared action template: stop and target in ATR(24), a time limit."""

    key: str
    stop_atr: float
    target_atr: float
    max_bars: int

    @property
    def reward_risk(self) -> float:
        return self.target_atr / self.stop_atr


#: The declared action menu. Growing it is a registered, counted change
#: (PROJECT_SPEC.md §3): every template is another configuration tested.
TEMPLATES: tuple[Template, ...] = (
    Template("T1", stop_atr=1.0, target_atr=1.5, max_bars=24),
    Template("T2", stop_atr=1.5, target_atr=3.0, max_bars=48),
)
TEMPLATE_BY_KEY = {t.key: t for t in TEMPLATES}


@dataclass(frozen=True)
class CostModel:
    """Costs NOT present in bid/ask data. All declared approximations."""

    slippage_pips: float = 0.1  # per market fill
    commission_pips_rt: float = 0.7  # ~ $7 per standard lot round trip
    swap_atr_per_night: float = 0.05  # of ATR24(H1), charged either direction
    spread_multiple: float = 1.0  # stress: widen the real spread

    def describe(self) -> dict:
        return {
            "spread": f"measured bid/ask x{self.spread_multiple}",
            "slippage_pips_per_fill": self.slippage_pips,
            "commission_pips_round_trip": self.commission_pips_rt,
            "swap": f"{self.swap_atr_per_night} x ATR24(H1) per New York close crossed, both directions",
            "status": "slippage, commission and swap are declared approximations",
        }


@dataclass
class Outcome:
    r: np.ndarray
    reason: np.ndarray  # 1 target, -1 stop, 0 time, -9 not computable
    exit_index: np.ndarray
    resolve_time: np.ndarray
    mfe_r: np.ndarray
    mae_r: np.ndarray
    cost_r: np.ndarray


@dataclass
class LabelSet:
    version: str
    symbol: str
    rows: np.ndarray  # decision rows (bar indices)
    decision_time: np.ndarray
    outcomes: dict[tuple[str, int], Outcome] = field(default_factory=dict)
    costs: dict = field(default_factory=dict)


def _widen(series: BarSeries, k: float) -> dict[str, np.ndarray]:
    """Bid/ask with the measured spread multiplied by k around the mid."""
    out = {}
    for x in ("open", "high", "low", "close"):
        b, a = getattr(series, f"bid_{x}"), getattr(series, f"ask_{x}")
        mid, half = (a + b) / 2, (a - b) / 2 * k
        out[f"bid_{x}"], out[f"ask_{x}"] = mid - half, mid + half
    return out


def compute_labels(series: BarSeries, pip: float, rows: np.ndarray | None = None,
                   costs: CostModel = CostModel(), atr: np.ndarray | None = None,
                   delay_bars: int = 0) -> LabelSet:
    """Outcomes for BUY and SELL under every template, for decision rows.

    `delay_bars` stresses latency: entry one or more bars later than decided.
    """
    n = len(series)
    if atr is None:
        atr = atr24(series)
    if rows is None:
        rows = np.flatnonzero(np.isfinite(atr))
    rows = np.asarray(rows, dtype=np.int64)
    px = _widen(series, costs.spread_multiple)
    slip = costs.slippage_pips * pip
    comm = costs.commission_pips_rt * pip
    day = bucket_start(series.open_time, "D1")
    avail = series.available_at

    labels = LabelSet(LABEL_VERSION, series.symbol, rows, avail[rows], costs=costs.describe())
    for tpl in TEMPLATES:
        for side in (BUY, SELL):
            labels.outcomes[(tpl.key, side)] = _simulate(
                px, day, avail, atr, rows, tpl, side, slip, comm, costs.swap_atr_per_night, n, delay_bars)
    return labels


def _simulate(px, day, avail, atr, rows, tpl, side, slip, comm, swap_frac, n, delay):
    m = len(rows)
    r = np.full(m, np.nan)
    reason = np.full(m, -9, dtype=np.int64)
    exit_idx = np.full(m, -1, dtype=np.int64)
    resolve = np.full(m, -1, dtype=np.int64)
    mfe = np.full(m, np.nan)
    mae = np.full(m, np.nan)
    cost_r = np.full(m, np.nan)

    e_idx = rows + 1 + delay
    ok = (e_idx + tpl.max_bars - 1 < n) & np.isfinite(atr[rows]) & (atr[rows] > 0)
    idx = np.flatnonzero(ok)
    if len(idx) == 0:
        return Outcome(r, reason, exit_idx, resolve, mfe, mae, cost_r)
    ei = e_idx[idx]
    a = atr[rows[idx]]
    if side == BUY:
        entry = px["ask_open"][ei] + slip
        stop = entry - tpl.stop_atr * a
        target = entry + tpl.target_atr * a
    else:
        entry = px["bid_open"][ei] - slip
        stop = entry + tpl.stop_atr * a
        target = entry - tpl.target_atr * a
    risk = np.abs(entry - stop)
    open_ = np.ones(len(idx), bool)
    ex_price = np.full(len(idx), np.nan)
    ex_i = np.full(len(idx), -1, dtype=np.int64)
    why = np.zeros(len(idx), dtype=np.int64)
    best = np.full(len(idx), -np.inf)
    worst = np.full(len(idx), np.inf)

    for h in range(tpl.max_bars):
        j = ei + h
        if side == BUY:
            lo, hi, op, cl = px["bid_low"][j], px["bid_high"][j], px["bid_open"][j], px["bid_close"][j]
            fav, adv = hi - entry, lo - entry
            stop_hit = open_ & (lo <= stop)
            fill_stop = np.minimum(op, stop) - slip
            tgt_hit = open_ & ~stop_hit & (hi >= target)
        else:
            lo, hi, op, cl = px["ask_low"][j], px["ask_high"][j], px["ask_open"][j], px["ask_close"][j]
            fav, adv = entry - lo, entry - hi
            stop_hit = open_ & (hi >= stop)
            fill_stop = np.maximum(op, stop) + slip
            tgt_hit = open_ & ~stop_hit & (lo <= target)
        best = np.where(open_, np.maximum(best, fav), best)
        worst = np.where(open_, np.minimum(worst, adv), worst)
        ex_price = np.where(stop_hit, fill_stop, ex_price)
        ex_price = np.where(tgt_hit, target, ex_price)
        why = np.where(stop_hit, -1, np.where(tgt_hit, 1, why))
        ex_i = np.where(stop_hit | tgt_hit, j, ex_i)
        open_ &= ~(stop_hit | tgt_hit)
        if h == tpl.max_bars - 1:
            t_exit = cl - side * slip
            ex_price = np.where(open_, t_exit, ex_price)
            ex_i = np.where(open_, j, ex_i)
            why = np.where(open_, 0, why)
            open_[:] = False

    nights = np.maximum(0, (day[ex_i] - day[ei]) // 86400)
    swap = swap_frac * a * nights
    gross = (ex_price - entry) * side
    r[idx] = (gross - comm - swap) / risk
    reason[idx] = why
    exit_idx[idx] = ex_i
    resolve[idx] = avail[ex_i]
    mfe[idx] = best / risk
    mae[idx] = worst / risk
    # frictions paid: the spread and slippage at both fills, commission, swap
    spread_entry = px["ask_open"][ei] - px["bid_open"][ei]
    cost_r[idx] = (spread_entry + 2 * slip + comm + swap) / risk
    return Outcome(r, reason, exit_idx, resolve, mfe, mae, cost_r)


def atr24(series: BarSeries) -> np.ndarray:
    """ATR(24) of mid prices, exactly as the feature store computes it."""
    c, h, l = series.mid_close, series.mid_high, series.mid_low
    pc = _lag(c, 1)
    tr = np.fmax(h - l, np.fmax(np.abs(h - pc), np.abs(l - pc)))
    tr[0] = np.nan
    return _roll(tr, 24, np.mean)


__all__ = ["BUY", "SELL", "TEMPLATES", "TEMPLATE_BY_KEY", "Template", "CostModel", "LabelSet",
           "Outcome", "compute_labels", "atr24", "LABEL_VERSION", "INDEX"]
