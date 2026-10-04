"""FLOW-1: scheduled order flow at the Tokyo and London fixes (research only).

Every earlier hypothesis in this repository asked whether PRICE PATTERNS predict price. All 54
were rejected. FLOW-1 asks a different question: do SCHEDULED, NON-INFORMATIONAL ORDERS move
prices in a predictable direction at a predictable time? The mechanism is institutional, not a
pattern:

- TOKYO FIX ("gotobi"). Japanese importers settle dollar invoices on gotobi days (the 5th, 10th,
  15th, 20th, 25th and the last day of the month; the preceding business day when that falls on a
  weekend). Banks buy the dollars before the 09:55 JST fixing, at which their customers pay. Ito &
  Yamada (2017) document USDJPY rising into the fix on those days. H1 buys USDJPY from 08:00 to
  10:00 JST; H2 sells it from 10:00 to 12:00 JST (the demand is gone after the fix).
- LONDON 4 P.M. FIX (WM/Reuters). Benchmark orders are executed around 15:57:30-16:02:30 London.
  Dealers pre-position, prices are pushed in the direction of the net order, and the pressure
  reverses once it is absorbed (Evans 2018; Melvin & Prins 2015). The orders are largest at
  month-end, when index funds and hedgers rebalance. H3 fades the 15:00-15:45 London move from
  16:15 to 17:15 London on the last business day of the month; H4 does the same on all other
  business days.

The data cannot see 00:00-01:00 UTC (09:00-10:00 JST): the source mirror has no hour-00 files
for 12 of 13 instruments. H1 and H2 are therefore defined on the bar opens at 23:00, 01:00 and
03:00 UTC, which exist; a position held through the missing hour has no stop to miss in this
study (no stops are used), so only the two endpoints matter.

Prices are bid/ask: a buy pays the ask plus slippage, a sell receives the bid minus slippage, and
commission is charged per round trip. Results are in basis points of the entry mid. Nothing here
sizes a position or reaches a broker.
"""

from __future__ import annotations

import calendar as _cal
import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np

FLOW_VERSION = "flow-1.0.0"
LONDON = ZoneInfo("Europe/London")
TOKYO = ZoneInfo("Asia/Tokyo")
GOTOBI_DAYS = (5, 10, 15, 20, 25)
FIX_PAIRS = ("EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD")
MIN_FIX_PAIRS = 4


def pip(symbol: str) -> float:
    return 0.01 if symbol.endswith("JPY") else 0.0001


@dataclass(frozen=True)
class Costs:
    """Costs NOT in the bid/ask: slippage per fill and commission per round trip, in pips."""
    slippage_pips: float = 0.1
    commission_pips_rt: float = 0.7
    spread_multiple: float = 1.0  # stress: widen the measured spread around the mid

    def stressed(self, k: float = 2.0) -> "Costs":
        return Costs(self.slippage_pips * k, self.commission_pips_rt * k, self.spread_multiple * k)


# ── calendars ───────────────────────────────────────────────────────────

def business_days(start: date, end: date) -> list[date]:
    out, d = [], start
    while d < end:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def gotobi_dates(start: date, end: date) -> list[date]:
    """Tokyo settlement days in [start, end): the 5th/10th/15th/20th/25th and the month's last day,
    moved to the preceding weekday when they fall on a weekend. Japanese public holidays are not
    modelled (declared: on a holiday there is no fixing, so the effect can only be diluted)."""
    out = set()
    y, m = start.year, start.month
    while date(y, m, 1) < end:
        last = _cal.monthrange(y, m)[1]
        for day in (*GOTOBI_DAYS, last):
            d = date(y, m, day)
            while d.weekday() >= 5:
                d -= timedelta(days=1)
            if start <= d < end:
                out.add(d)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return sorted(out)


def last_business_days(start: date, end: date) -> list[date]:
    out = []
    y, m = start.year, start.month
    while date(y, m, 1) < end:
        d = date(y, m, _cal.monthrange(y, m)[1])
        while d.weekday() >= 5:
            d -= timedelta(days=1)
        if start <= d < end:
            out.append(d)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def epoch_at(d: date, hh: int, mm: int, tz) -> int:
    return int(datetime.combine(d, time(hh, mm), tzinfo=tz).timestamp())


def tokyo_times(d: date) -> dict[str, int]:
    """The H1/H2 clock for Tokyo date d (Japan has no daylight saving)."""
    return {"pre_entry": epoch_at(d, 8, 0, TOKYO), "fix_exit": epoch_at(d, 10, 0, TOKYO),
            "post_exit": epoch_at(d, 12, 0, TOKYO)}


def london_times(d: date) -> dict[str, int]:
    """The H3/H4 clock for London date d, in UTC epochs (BST handled by the time zone)."""
    return {"pre_start": epoch_at(d, 15, 0, LONDON), "pre_end": epoch_at(d, 15, 45, LONDON),
            "entry": epoch_at(d, 16, 15, LONDON), "exit": epoch_at(d, 17, 15, LONDON)}


# ── prices ──────────────────────────────────────────────────────────────

class Opens:
    """Bid/ask at the OPEN of each M15 bar, looked up by exact open time (no nearest-bar guessing:
    a missing bar means no trade, counted)."""

    def __init__(self, bars) -> None:
        self.symbol = bars.symbol
        self.index = {int(t): i for i, t in enumerate(bars.open_time)}
        self.bid, self.ask = bars.bid_open, bars.ask_open

    def at(self, t: int) -> tuple[float, float] | None:
        i = self.index.get(int(t))
        if i is None:
            return None
        b, a = float(self.bid[i]), float(self.ask[i])
        if not (math.isfinite(b) and math.isfinite(a)) or b <= 0 or a < b:
            return None
        return b, a


def trade(opens: Opens, t_entry: int, t_exit: int, side: int, costs: Costs) -> dict | None:
    """A market entry at the open of the bar starting t_entry, closed at the open of the bar starting
    t_exit. Gross = mid to mid; net pays the (stressed) spread, slippage on both fills and commission."""
    e, x = opens.at(t_entry), opens.at(t_exit)
    if e is None or x is None or t_exit <= t_entry:
        return None
    p = pip(opens.symbol)
    k = costs.spread_multiple
    em, xm = (e[0] + e[1]) / 2, (x[0] + x[1]) / 2
    eh, xh = (e[1] - e[0]) / 2 * k, (x[1] - x[0]) / 2 * k
    slip = costs.slippage_pips * p
    entry = em + side * (eh + slip)
    exit_ = xm - side * (xh + slip)
    net_px = (exit_ - entry) * side - costs.commission_pips_rt * p
    gross_px = (xm - em) * side
    return {"gross_bps": gross_px / em * 1e4, "net_bps": net_px / em * 1e4, "cost_bps": (gross_px - net_px) / em * 1e4,
            "net_pips": net_px / p, "gross_pips": gross_px / p, "entry_t": t_entry, "side": side}


def mid(opens: Opens, t: int) -> float | None:
    q = opens.at(t)
    return None if q is None else (q[0] + q[1]) / 2


# ── the four hypotheses ─────────────────────────────────────────────────

def gotobi_events(opens: Opens, days: list[date], window: str, costs: Costs) -> list[dict]:
    """H1 (window="pre": long 08:00->10:00 JST) or H2 ("post": short 10:00->12:00 JST), one per day."""
    out = []
    for d in days:
        tt = tokyo_times(d)
        r = (trade(opens, tt["pre_entry"], tt["fix_exit"], +1, costs) if window == "pre"
             else trade(opens, tt["fix_exit"], tt["post_exit"], -1, costs))
        if r is not None:
            out.append({"date": d, **r})
    return out


def fix_events(opens_by_pair: dict[str, Opens], days: list[date], costs: Costs) -> list[dict]:
    """H3/H4: per day, every pair fades its own 15:00-15:45 London move from 16:15 to 17:15 London.
    The day's observation is the mean across pairs (they share the dollar leg: one day is one
    observation, not seven). Days with fewer than MIN_FIX_PAIRS usable pairs are skipped."""
    out = []
    for d in days:
        tt = london_times(d)
        legs = {}
        for sym, op in opens_by_pair.items():
            a, b = mid(op, tt["pre_start"]), mid(op, tt["pre_end"])
            if a is None or b is None or b == a:
                continue
            r = trade(op, tt["entry"], tt["exit"], -1 if b > a else +1, costs)
            if r is not None:
                legs[sym] = r
        if len(legs) >= MIN_FIX_PAIRS:
            out.append({"date": d, "entry_t": tt["entry"], "pairs": len(legs),
                        **{k: float(np.mean([v[k] for v in legs.values()])) for k in ("gross_bps", "net_bps", "cost_bps")},
                        "legs": {s: round(v["net_bps"], 4) for s, v in legs.items()}})
    return out


# ── statistics ──────────────────────────────────────────────────────────

def summary(events: list[dict], key: str = "net_bps") -> dict:
    x = np.array([e[key] for e in events], float)
    n = len(x)
    if n < 2:
        return {"n": n, "mean": float(x.mean()) if n else None, "t": None}
    sd = float(x.std(ddof=1))
    return {"n": n, "mean": round(float(x.mean()), 4), "sd": round(sd, 4),
            "t": round(float(x.mean() / (sd / math.sqrt(n))), 3) if sd > 0 else None,
            "win_rate": round(float((x > 0).mean()), 4), "total": round(float(x.sum()), 3)}


def by_year(events: list[dict], key: str = "net_bps") -> dict:
    out: dict = {}
    for e in events:
        out.setdefault(e["date"].year, []).append(e[key])
    return {y: {"n": len(v), "mean": round(float(np.mean(v)), 4), "total": round(float(np.sum(v)), 3)}
            for y, v in sorted(out.items())}


def welch_t(a: list[float], b: list[float]) -> float | None:
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 2 or len(b) < 2:
        return None
    se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return None if se == 0 else float((a.mean() - b.mean()) / se)


def max_drawdown(x: list[float]) -> float:
    eq = np.cumsum(np.asarray(x, float))
    if not len(eq):
        return 0.0
    peak = np.maximum.accumulate(np.concatenate(([0.0], eq)))[1:]
    return float((peak - eq).max())
