"""IX-1: intraday momentum into the cash close of equity-index CFDs (research only). ix-1.0.0

Economic reason (Gao, Han, Li & Zhou 2018, JFE; Baltussen, Da, Lammers & Martens 2021, JFE): the return
from the previous cash close to shortly before today's close predicts the return over the last part of
the session, across more than 60 futures markets, because hedgers who are short gamma (option dealers,
leveraged/inverse ETFs rebalancing at the close) must trade in the direction of the day's move, and they
trade late. The flow is mechanical and not informational, so it need not be arbitraged away by people
who are better informed: they would have to absorb the rebalancing.

Everything here is a causal function of M5 bid/ask bars up to the signal bar (the close and the entry
time are bar boundaries):

- day d's close time C_d is the exchange's cash close in its own time zone (DST-correct);
- signal s_d = mid(C_d - offset) / mid(C_{d-1}) - 1, using the bar that OPENS at C - offset as the entry
  bar and the mid at its open (so nothing after the entry quote is read);
- the trade enters at the open of the entry bar (ASK + slippage for a buy, BID - slippage for a sell) in
  the direction of s_d, or `delay` bars later, and exits at the open of the bar that opens at C_d (BID -
  slippage / ASK + slippage), unless its protective stop is hit first;
- the protective stop is 2.5 x the standard deviation of the last-`offset` mid return over the previous
  60 eligible days (causal), and never closer than 3 spreads. It is checked bar by bar on the side the
  position would close on; a bar opening beyond the stop fills at that open;
- no financing: the position is flat before the broker's 17:00 New York rollover for every instrument
  traded here (all closes are before it);
- costs: the bar's real spread at entry and exit, plus `slip_pts` per fill and `commission_pts` per round
  trip (metals; index CFDs are spread-only), all multiplied by `cost_mult` for stress tests.

R = net P&L / (entry - stop distance). Nothing here sizes a live trade: the risk engine is the only sizing
authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

import numpy as np

IX_VERSION = "ix-1.0.0"
M5 = 300

#: symbol -> (exchange time zone, cash close local time). The CFD tracks the index future, which keeps
#: trading after the cash close; the hedging flow concentrates into the CASH close.
CLOSES: dict[str, tuple[str, time]] = {
    "USA500IDXUSD": ("America/New_York", time(16, 0)),
    "USATECHIDXUSD": ("America/New_York", time(16, 0)),
    "USA30IDXUSD": ("America/New_York", time(16, 0)),
    "USSC2000IDXUSD": ("America/New_York", time(16, 0)),
    "DEUIDXEUR": ("Europe/Berlin", time(17, 30)),
    "FRAIDXEUR": ("Europe/Paris", time(17, 30)),
    "EUSIDXEUR": ("Europe/Berlin", time(17, 30)),
    "ESPIDXEUR": ("Europe/Madrid", time(17, 30)),
    "NLDIDXEUR": ("Europe/Amsterdam", time(17, 30)),
    "CHEIDXCHF": ("Europe/Zurich", time(17, 30)),
    "GBRIDXGBP": ("Europe/London", time(16, 30)),
    "JPNIDXJPY": ("Asia/Tokyo", time(15, 0)),
    "HKGIDXHKD": ("Asia/Hong_Kong", time(16, 0)),
    "AUSIDXAUD": ("Australia/Sydney", time(16, 0)),
    # Metals: the COMEX settlement (gold 13:30 ET, silver 13:25 ET).
    "XAUUSD": ("America/New_York", time(13, 30)),
    "XAGUSD": ("America/New_York", time(13, 25)),
}


@dataclass
class Bars:
    """One instrument's bid/ask bars."""

    symbol: str
    t: np.ndarray
    bo: np.ndarray
    bh: np.ndarray
    bl: np.ndarray
    ao: np.ndarray
    ah: np.ndarray
    al: np.ndarray

    @classmethod
    def from_series(cls, s) -> "Bars":
        return cls(s.symbol, np.asarray(s.open_time, dtype=np.int64), s.bid_open, s.bid_high, s.bid_low,
                   s.ask_open, s.ask_high, s.ask_low)

    def index(self) -> dict[int, int]:
        return {int(x): i for i, x in enumerate(self.t)}


def close_epoch(symbol: str, d: date) -> int:
    tz, hm = CLOSES[symbol]
    return int(datetime.combine(d, hm, tzinfo=ZoneInfo(tz)).astimezone(timezone.utc).timestamp())


def trading_days(b: Bars) -> list[date]:
    """Local exchange dates on which the bar opening at the cash close exists (the CFD was quoted then)."""
    tz = ZoneInfo(CLOSES[b.symbol][0])
    idx = b.index()
    days = sorted({datetime.fromtimestamp(int(x), timezone.utc).astimezone(tz).date() for x in b.t[::12]})
    return [d for d in days if d.weekday() < 5 and close_epoch(b.symbol, d) in idx]


@dataclass(frozen=True)
class Trade:
    symbol: str
    day: date
    side: int
    signal: float  # rest-of-day return (fraction)
    entry: float
    exit: float
    stop: float
    gross_bps: float  # mid to mid
    net_bps: float
    cost_bps: float
    r: float  # net, in units of the stop distance
    stopped: bool


def _quote(b: Bars, i: int, side: int, opening: bool, slip: float) -> float:
    """Fill price at the open of bar i: a buy (opening long / closing short) pays the ask."""
    pays_ask = (side > 0) == opening
    return float(b.ao[i] + slip) if pays_ask else float(b.bo[i] - slip)


def trades(b: Bars, offset_min: int = 30, delay: int = 0, min_abs_z: float = 0.0, slip_pts: float = 0.0,
           cost_mult: float = 1.0, vol_days: int = 60, stop_sd: float = 2.5, commission_pts: float = 0.0,
           days: list[date] | None = None) -> list[Trade]:
    """The IX-1 trades for one instrument. `min_abs_z` keeps only days whose |signal| exceeds that many
    causal standard deviations of past signals (the same 60-day window); 0 trades every day."""
    idx = b.index()
    days = trading_days(b) if days is None else days
    off = offset_min * 60
    out: list[Trade] = []
    past_sig: list[float] = []
    past_last: list[float] = []
    prev_close_mid = None
    for d in days:
        c = close_epoch(b.symbol, d)
        i_c = idx.get(c)
        i_e = idx.get(c - off)
        if i_c is None or i_e is None:
            prev_close_mid = None
            continue
        mid_c = (b.bo[i_c] + b.ao[i_c]) / 2
        mid_e = (b.bo[i_e] + b.ao[i_e]) / 2
        s = mid_e / prev_close_mid - 1.0 if prev_close_mid is not None else None
        if s is not None and len(past_last) >= vol_days:
            sd_last = float(np.std(past_last[-vol_days:]))
            strong = min_abs_z <= 0 or (len(past_sig) >= vol_days
                                        and abs(s) > min_abs_z * float(np.std(past_sig[-vol_days:])))
            i_in = i_e + delay
            if s != 0 and sd_last > 0 and strong and i_in < i_c and b.t[i_in] < c:
                side = 1 if s > 0 else -1
                spread_in = float(b.ao[i_in] - b.bo[i_in])
                mid_in = (b.bo[i_in] + b.ao[i_in]) / 2
                extra = (cost_mult - 1.0) * spread_in / 2 + cost_mult * slip_pts
                entry = _quote(b, i_in, side, True, extra)
                dist = max(stop_sd * sd_last * mid_in, 3 * spread_in)
                stop = entry - side * dist
                exit_px, stopped = None, False
                # From the entry fill to the exit bar's open: the entry bar's own range counts (the
                # fill is at its open), every later bar's open (a gap) and then its range.
                for k in range(i_in, i_c):
                    if b.t[k] >= c:
                        break
                    if k > i_in:
                        o_close = b.bo[k] if side > 0 else b.ao[k]
                        if (side > 0 and o_close <= stop) or (side < 0 and o_close >= stop):
                            sp = float(b.ao[k] - b.bo[k])
                            exit_px = float(o_close) - side * ((cost_mult - 1.0) * sp / 2 + cost_mult * slip_pts)
                            stopped = True
                            break
                    touch = b.bl[k] if side > 0 else b.ah[k]
                    if (side > 0 and touch <= stop) or (side < 0 and touch >= stop):
                        sp = float(b.ao[k] - b.bo[k])
                        exit_px = float(stop) - side * ((cost_mult - 1.0) * sp / 2 + cost_mult * slip_pts)
                        stopped = True
                        break
                if exit_px is None:
                    spread_out = float(b.ao[i_c] - b.bo[i_c])
                    exit_px = _quote(b, i_c, side, False, (cost_mult - 1.0) * spread_out / 2 + cost_mult * slip_pts)
                mid_out = mid_c
                gross = side * (mid_out - mid_in) / mid_in * 1e4
                comm = cost_mult * commission_pts
                net = (side * (exit_px - entry) - comm) / mid_in * 1e4
                out.append(Trade(b.symbol, d, side, float(s), entry, exit_px, stop, float(gross), float(net),
                                 float(gross - net), float((side * (exit_px - entry) - comm) / dist), stopped))
        if s is not None:
            past_sig.append(s)
        past_last.append(mid_c / mid_e - 1.0)
        prev_close_mid = mid_c
    return out


def daily_book(ts: list[Trade]) -> dict[date, float]:
    """Equal-weight portfolio: per day, the mean net bps across the instruments that traded."""
    by: dict[date, list[float]] = {}
    for x in ts:
        by.setdefault(x.day, []).append(x.net_bps)
    return {d: float(np.mean(v)) for d, v in sorted(by.items())}


def summary(ts: list[Trade]) -> dict:
    """Per-trade and per-day statistics. t is on the daily equal-weight book (cross-index dependence)."""
    if not ts:
        return {"trades": 0}
    net = np.array([x.net_bps for x in ts])
    gross = np.array([x.gross_bps for x in ts])
    r = np.array([x.r for x in ts])
    book = np.array(list(daily_book(ts).values()))
    t_day = float(book.mean() / book.std(ddof=1) * np.sqrt(len(book))) if len(book) > 2 and book.std() > 0 else None
    wins, losses = r[r > 0].sum(), -r[r < 0].sum()
    eq = np.cumsum(r)
    dd = float(np.max(np.maximum.accumulate(eq) - eq)) if len(eq) else 0.0
    years = sorted({x.day.year for x in ts})
    by_year = {y: round(float(np.mean([x.net_bps for x in ts if x.day.year == y])), 3) for y in years}
    by_sym = {}
    for s in sorted({x.symbol for x in ts}):
        v = [x.net_bps for x in ts if x.symbol == s]
        by_sym[s] = {"trades": len(v), "net_bps": round(float(np.mean(v)), 3)}
    return {
        "trades": len(ts), "days": len(book), "gross_bps": round(float(gross.mean()), 3),
        "cost_bps": round(float((gross - net).mean()), 3), "net_bps": round(float(net.mean()), 3),
        "net_r": round(float(r.mean()), 4), "win_rate": round(float((r > 0).mean()), 4),
        "profit_factor": round(float(wins / losses), 3) if losses > 0 else None,
        "max_drawdown_r": round(dd, 2), "t_day": round(t_day, 3) if t_day is not None else None,
        "sharpe_annual": round(float(book.mean() / book.std(ddof=1) * np.sqrt(252)), 3) if len(book) > 2 else None,
        "stopped_share": round(float(np.mean([x.stopped for x in ts])), 4),
        "by_year_net_bps": by_year, "by_symbol": by_sym,
    }


__all__ = ["CLOSES", "IX_VERSION", "Bars", "Trade", "close_epoch", "daily_book", "summary", "trades",
           "trading_days"]

