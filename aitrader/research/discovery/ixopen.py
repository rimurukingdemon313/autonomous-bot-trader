"""IX-4: the NASDAQ opening-candle EMA(12) signal (research only). ixo-1.0.0

Source of the hypothesis: a video claiming a NASDAQ intraday strategy. Its reported return is an external
claim and is never used as a target. Only the disclosed ENTRY signal is tested; the undisclosed exit is
replaced by a small, preregistered exit family (research/preregistrations/IX-4.md).

Definitions (all causal; M5 bid/ask bars of the Nasdaq-100 CFD):

- the signal bar is the 5-minute bar OPENING at 09:30 New York (DST-correct): it closes at 09:35;
- EMA(n) of the mid CLOSE, alpha = 2 / (n + 1), recursive (EMA_t = a x_t + (1 - a) EMA_{t-1}), seeded with
  the first close of the loaded series. PRIMARY: over the full continuous 5-minute series (the CFD trades
  nearly 24 hours). VARIANT "rth": over regular-session bars only (09:30-16:00 New York), concatenated;
- LONG if the signal bar's mid close > EMA(n) at that bar, SHORT if <, no trade if equal;
- entry at the OPEN of the next bar (09:35) on the correct side of the quote plus slippage, or `delay`
  bars later. Nothing of the signal bar is used before it has closed; nothing after the entry quote is
  used to decide anything;
- ATR(14) = mean true range of the 14 completed mid bars up to and including the signal bar;
- exits (every exit also closes at the open of the bar starting 16:00 New York; nothing is held past it,
  so no financing is ever charged):
    T30/T60/T120/T240/TCLOSE  time exit, with a catastrophic stop at 2 ATR;
    S1.0/S1.5/S2.0            stop k ATR, target 2k ATR;
    TRATR                     1.5 ATR stop trailed from the best mid close of completed bars;
    TRBAR                     1.5 ATR initial stop, then the previous completed bar's low (long) / high
                              (short), ratcheting only in the trade's favour;
- a stop fills half a spread THROUGH the stop (or at a gapping bar's open), less slippage; a target fills at
  the target; a bar touching both is a STOP;
- every initial stop is at least 3 spreads from the entry (the risk engine's entry rule);
- R = net P&L / initial stop distance.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

import numpy as np

IXO_VERSION = "ixo-1.0.0"
M5 = 300
NY = ZoneInfo("America/New_York")
OPEN, CLOSE = time(9, 30), time(16, 0)
EXITS = ("T30", "T60", "T120", "T240", "TCLOSE", "S1.0", "S1.5", "S2.0", "TRATR", "TRBAR")


@dataclass
class OBars:
    symbol: str
    t: np.ndarray
    bo: np.ndarray
    bh: np.ndarray
    bl: np.ndarray
    bc: np.ndarray
    ao: np.ndarray
    ah: np.ndarray
    al: np.ndarray
    ac: np.ndarray

    @classmethod
    def from_series(cls, s) -> "OBars":
        return cls(s.symbol, np.asarray(s.open_time, dtype=np.int64), s.bid_open, s.bid_high, s.bid_low,
                   s.bid_close, s.ask_open, s.ask_high, s.ask_low, s.ask_close)

    def mid(self, k: str) -> np.ndarray:
        return (getattr(self, "b" + k) + getattr(self, "a" + k)) / 2


def ny_epoch(d: date, hm: time) -> int:
    return int(datetime.combine(d, hm, tzinfo=NY).astimezone(timezone.utc).timestamp())


def ema(x: np.ndarray, n: int) -> np.ndarray:
    a = 2.0 / (n + 1)
    out = np.empty(len(x))
    acc = x[0] if len(x) else 0.0
    for i, v in enumerate(x):
        acc = a * v + (1 - a) * acc
        out[i] = acc
    return out


def rth_mask(b: OBars) -> np.ndarray:
    local = [datetime.fromtimestamp(int(x), timezone.utc).astimezone(NY) for x in b.t]
    return np.array([lt.weekday() < 5 and OPEN <= lt.time() < CLOSE for lt in local])


def ema_series(b: OBars, n: int, rth: bool = False) -> np.ndarray:
    """EMA(n) of mid closes at every bar; for `rth`, computed over regular-session bars only and NaN
    outside them."""
    c = b.mid("c")
    if not rth:
        return ema(c, n)
    m = rth_mask(b)
    out = np.full(len(c), np.nan)
    out[m] = ema(c[m], n)
    return out


def atr14(b: OBars) -> np.ndarray:
    h, lo, c = b.mid("h"), b.mid("l"), b.mid("c")
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - lo, np.maximum(abs(h - pc), abs(lo - pc)))
    out = np.full(len(tr), np.nan)
    cs = np.cumsum(tr)
    out[13:] = (cs[13:] - np.r_[0, cs[:-14]]) / 14
    return out


@dataclass(frozen=True)
class Trade:
    day: date
    exit_rule: str
    side: int
    entry_t: int
    exit_t: int
    entry: float
    exit: float
    stop0: float
    gross_bps: float
    net_bps: float
    cost_bps: float
    r: float
    reason: str


def signals(b: OBars, n: int = 12, rth: bool = False, how: str = "ema") -> list[tuple[date, int, int]]:
    """(day, signal bar index, side) for every New York weekday whose 09:30 bar exists.
    how: "ema" (close vs EMA), "first" (close vs open of the signal bar, no EMA)."""
    idx = {int(x): i for i, x in enumerate(b.t)}
    e = ema_series(b, n, rth) if how == "ema" else None
    c, o = b.mid("c"), b.mid("o")
    days = sorted({datetime.fromtimestamp(int(x), timezone.utc).astimezone(NY).date() for x in b.t[::48]})
    out = []
    for d in days:
        if d.weekday() >= 5:
            continue
        i = idx.get(ny_epoch(d, OPEN))
        if i is None or i < 30:
            continue
        ref = e[i] if how == "ema" else o[i]
        if not np.isfinite(ref) or c[i] == ref:
            continue
        out.append((d, i, 1 if c[i] > ref else -1))
    return out


def simulate(b: OBars, sigs: list[tuple[date, int, int]], exit_rule: str, delay: int = 0, slip: float = 0.0,
             cost_mult: float = 1.0, commission: float = 0.0) -> list[Trade]:
    """Trade every signal with one exit rule. `sigs` may also come from a baseline (any bar, any side)."""
    idx = {int(x): i for i, x in enumerate(b.t)}
    atr = atr14(b)
    mc = b.mid("c")
    out = []
    for d, i, side in sigs:
        k0 = i + 1 + delay
        close_t = ny_epoch(d, CLOSE)
        if k0 >= len(b.t) or b.t[k0] != b.t[i] + (1 + delay) * M5 or b.t[k0] >= close_t:
            continue
        a = atr[i]
        if not np.isfinite(a) or a <= 0:
            continue
        sp_in = b.ao[k0] - b.bo[k0]
        extra_in = (cost_mult - 1) * sp_in / 2 + cost_mult * slip
        entry = (b.ao[k0] + extra_in) if side > 0 else (b.bo[k0] - extra_in)
        mid_in = (b.ao[k0] + b.bo[k0]) / 2
        if exit_rule.startswith("T") and exit_rule[1:].isdigit():
            end_t = min(b.t[k0] + int(exit_rule[1:]) * 60, close_t)
            dist, target = 2 * a, None
        elif exit_rule == "TCLOSE":
            end_t, dist, target = close_t, 2 * a, None
        elif exit_rule.startswith("S"):
            kk = float(exit_rule[1:])
            end_t, dist = close_t, kk * a
            target = entry + side * 2 * dist
        else:
            end_t, dist, target = close_t, 1.5 * a, None
        dist = max(dist, 3 * sp_in)  # never closer than 3 spreads (the risk engine's own entry rule)
        if target is not None:
            target = entry + side * 2 * dist
        stop = entry - side * dist
        j_end = idx.get(int(end_t))
        exit_px, exit_t, reason, level, jj = None, None, "time", None, None
        best = mid_in
        k = k0
        while k < len(b.t) and b.t[k] < end_t:
            if k > k0:  # a gap through the stop at this bar's open
                o = b.bo[k] if side > 0 else b.ao[k]
                if (side > 0 and o <= stop) or (side < 0 and o >= stop):
                    level, jj, reason = float(o), k, "stop"
                    break
            touch = b.bl[k] if side > 0 else b.ah[k]
            if (side > 0 and touch <= stop) or (side < 0 and touch >= stop):
                level, jj, reason = float(stop), k, "stop"
                break
            if target is not None:
                hi = b.bh[k] if side > 0 else b.al[k]
                if (side > 0 and hi >= target) or (side < 0 and hi <= target):
                    level, jj, reason = float(target), k, "target"
                    break
            # trailing updates use the bar just COMPLETED, effective from the next bar
            if exit_rule == "TRATR":
                best = max(best, mc[k]) if side > 0 else min(best, mc[k])
                stop = max(stop, best - 1.5 * a) if side > 0 else min(stop, best + 1.5 * a)
            elif exit_rule == "TRBAR":
                stop = max(stop, b.bl[k]) if side > 0 else min(stop, b.ah[k])
            k += 1
        if level is not None:
            # Stop / target levels live on the closing side of the quote (bid for a long, ask for a short).
            # A triggered stop is a market order: it fills THROUGH the level by half a spread (the price
            # path overshoots a level between quotes) plus slippage; filling exactly at the level is
            # optimistic and manufactures a few bp of edge on a pure random walk (tests/unit/test_ixopen.py).
            # A target is a limit order: it fills at its price, never better.
            half = (b.ao[jj] - b.bo[jj]) / 2
            if reason == "stop" and level == stop:
                level = level - side * half
            mid_out = level + side * half
            slip_x = 0.0 if reason == "target" else (cost_mult - 1) * half + cost_mult * slip
            exit_px, exit_t = level - side * slip_x, int(b.t[jj])
        else:
            j = j_end if j_end is not None else (k if k < len(b.t) else None)
            if j is None:
                continue
            sp = b.ao[j] - b.bo[j]
            ex = (cost_mult - 1) * sp / 2 + cost_mult * slip
            exit_px = (b.bo[j] - ex) if side > 0 else (b.ao[j] + ex)
            exit_t = int(b.t[j])
            mid_out = (b.ao[j] + b.bo[j]) / 2
        comm = cost_mult * commission
        gross = side * (mid_out - mid_in) / mid_in * 1e4
        net = (side * (exit_px - entry) - comm) / mid_in * 1e4
        out.append(Trade(d, exit_rule, side, int(b.t[k0]), exit_t, float(entry), float(exit_px), float(stop),
                         float(gross), float(net), float(gross - net), float((side * (exit_px - entry) - comm) / dist),
                         reason))
    return out


def random_signals(b: OBars, base: list[tuple[date, int, int]], seed: int, mode: str, n: int = 12):
    """Baselines. "dir": the same bars, random side. "time": a random 5-minute bar between 09:35 and 15:00
    New York each day with the EMA(n) side at that bar (EMA without the opening timing). "both": random bar,
    random side."""
    rng = np.random.default_rng(seed)
    if mode == "dir":
        return [(d, i, int(rng.choice((-1, 1)))) for d, i, _ in base]
    idx = {int(x): i for i, x in enumerate(b.t)}
    e = ema_series(b, n)
    c = b.mid("c")
    out = []
    for d, _, _ in base:
        lo, hi = ny_epoch(d, time(9, 35)), ny_epoch(d, time(15, 0))
        cand = [idx[x] for x in range(lo, hi + 1, M5) if x in idx]
        if not cand:
            continue
        i = int(rng.choice(cand))
        if mode == "time":
            if c[i] == e[i]:
                continue
            out.append((d, i, 1 if c[i] > e[i] else -1))
        else:
            out.append((d, i, int(rng.choice((-1, 1)))))
    return out


def session_long(base: list[tuple[date, int, int]]) -> list[tuple[date, int, int]]:
    """Benchmark: long every day from 09:35 (use with TCLOSE)."""
    return [(d, i, 1) for d, i, _ in base]


def summary(ts: list[Trade]) -> dict:
    if not ts:
        return {"trades": 0}
    by_day: dict[date, float] = {}
    for x in ts:
        by_day[x.day] = by_day.get(x.day, 0.0) + x.net_bps
    book = np.array(list(by_day.values()))
    net = np.array([x.net_bps for x in ts])
    gross = np.array([x.gross_bps for x in ts])
    r = np.array([x.r for x in ts])
    wins, losses = r[r > 0], r[r < 0]
    eq = np.cumsum(r)
    sd = book.std(ddof=1) if len(book) > 2 else 0.0
    t = float(book.mean() / sd * np.sqrt(len(book))) if sd > 0 else None
    months: dict[tuple[int, int], float] = {}
    for x in ts:
        months[(x.day.year, x.day.month)] = months.get((x.day.year, x.day.month), 0.0) + x.r
    keys = sorted(months)
    w3 = [sum(months[k] for k in keys[i:i + 3]) for i in range(max(0, len(keys) - 2))]
    years = sorted({x.day.year for x in ts})
    return {
        "trades": len(ts), "trades_per_month": round(len(ts) / max(len(keys), 1), 2),
        "gross_bps": round(float(gross.mean()), 3), "cost_bps": round(float((gross - net).mean()), 3),
        "net_bps": round(float(net.mean()), 3), "net_r": round(float(r.mean()), 4),
        "net_bps_ci95": [round(float(net.mean() - 1.96 * net.std(ddof=1) / np.sqrt(len(net))), 3),
                         round(float(net.mean() + 1.96 * net.std(ddof=1) / np.sqrt(len(net))), 3)],
        "win_rate": round(float((r > 0).mean()), 4),
        "avg_win_r": round(float(wins.mean()), 3) if len(wins) else None,
        "avg_loss_r": round(float(losses.mean()), 3) if len(losses) else None,
        "profit_factor": round(float(wins.sum() / -losses.sum()), 3) if len(losses) else None,
        "max_drawdown_r": round(float(np.max(np.maximum.accumulate(eq) - eq)), 2), "t_day": round(t, 3) if t else t,
        "rolling_3m_profitable": round(float(np.mean([v > 0 for v in w3])), 3) if w3 else None,
        "by_year_net_bps": {y: round(float(np.mean([x.net_bps for x in ts if x.day.year == y])), 3) for y in years},
        "exit_reasons": {k: int(sum(x.reason == k for x in ts)) for k in ("time", "stop", "target")},
    }


def welch_t(a: list[float], b: list[float]) -> float | None:
    if len(a) < 3 or len(b) < 3:
        return None
    va, vb = np.var(a, ddof=1), np.var(b, ddof=1)
    den = np.sqrt(va / len(a) + vb / len(b))
    return float((np.mean(a) - np.mean(b)) / den) if den > 0 else None


__all__ = ["EXITS", "IXO_VERSION", "OBars", "Trade", "atr14", "ema", "ema_series", "ny_epoch", "random_signals",
           "session_long", "signals", "simulate", "summary", "welch_t"]
