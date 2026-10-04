"""RC programs: retail-CFD-compatible, low-turnover candidates (research only). rc-1.0.0

Data helpers and the signal rules of the RC-EQ (equity-index CFD) and RC-FX programs
(research/preregistrations/RC-EQ.md, RC-FX.md). Every rule returns TARGET POSITIONS (fractions of
equity) that `retail.simulate` turns into P&L after retail costs. A target set at an instrument's
close uses only:

- that instrument's closes up to and including that close (own-price rules: E2, E4, E5);
- the exchange calendar, which is published in advance (E1 knows which day is the last trading
  day of the month; it reads no price at all);
- for cross-sectional rules (E3), closes dated on or before the decision date, filled at each
  instrument's NEXT close after the decision, never the same one;
- for FX (H.10 noon fixings), fixings published before the fill: a fixing dated d is public from
  17:00 New York on the next business day (aitrader/data/h10.py), so a fill at fixing j uses
  fixings up to j-2.

Nothing here sizes a live trade or reads anything after the fill it decides.
"""

from __future__ import annotations

import bisect
import csv
import math
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

RC_VERSION = "rc-1.0.0"
MAX_RATE_PCT = 25.0  # a currency above this policy rate is not held (hyperinflation episodes): excluded
STALE_DAYS = 7  # a policy-rate observation older than this is not carried forward


# ── policy rates (BIS, data/rc/policy_rates.csv) ────────────────────────

class Rates:
    """The rate public at the close (22:00 UTC) of day d, by BIS area. A key "DE|XM" means the
    national rate before the euro (to 1998-12-31) and the euro-area rate from 1999-01-01. NaN when
    unknown, stale, or above MAX_RATE_PCT."""

    EURO = date(1999, 1, 1)

    def __init__(self, path: Path | str) -> None:
        by: dict[str, list] = {}
        with open(path) as f:
            for r in csv.DictReader(f):
                by.setdefault(r["area"], []).append((int(r["available_at_epoch"]),
                                                     date.fromisoformat(r["effective_date"]), float(r["value_pct"])))
        self.by = {a: sorted(v) for a, v in by.items()}
        self.avail = {a: np.array([x[0] for x in v], np.int64) for a, v in self.by.items()}
        self._cache: dict = {}

    def at(self, key: str, d: date) -> float:
        k = (key, d)
        if k in self._cache:
            return self._cache[k]
        if "|" in key:
            pre, post = key.split("|")
            area = pre if d < self.EURO else post
        else:
            area = key
        v = float("nan")
        if area in self.by:
            t = int(datetime(d.year, d.month, d.day, 22, tzinfo=timezone.utc).timestamp())
            i = int(np.searchsorted(self.avail[area], t, "right")) - 1
            if i >= 0:
                _, eff, x = self.by[area][i]
                if (d - eff).days <= STALE_DAYS and x <= MAX_RATE_PCT:
                    v = x
        self._cache[k] = v
        return v


# ── daily closes ────────────────────────────────────────────────────────

def clean(days: list[date], closes: list[float]) -> tuple[list[date], list[float], dict]:
    """Two declared vendor-error rules; a removed close is missing, never replaced.
    - spike: a close more than 20% (log) away from BOTH neighbours, in opposite directions, while
      the neighbours agree within 5%: a one-day misprint;
    - stale: from the 5th identical consecutive close on, closes repeat a frozen feed."""
    c = list(closes)
    spikes = stale = 0
    for t in range(1, len(c) - 1):
        a, b, n = c[t - 1], c[t], c[t + 1]
        if min(a, b, n) > 0:
            up, dn, span = math.log(b / a), math.log(n / b), abs(math.log(n / a))
            if abs(up) > 0.20 and abs(dn) > 0.20 and up * dn < 0 and span < 0.05:
                c[t] = float("nan")
                spikes += 1
    run = 1
    for t in range(1, len(c)):
        run = run + 1 if closes[t] == closes[t - 1] else 1  # the vendor's values, not the cleaned ones
        if run >= 5:
            c[t] = float("nan")
            stale += 1
    keep = [(d, x) for d, x in zip(days, c) if np.isfinite(x) and x > 0]
    return [d for d, _ in keep], [x for _, x in keep], {"spikes_removed": spikes, "stale_removed": stale}


def panel(series: dict[str, tuple[list[date], list[float]]], start: date, end: date):
    """Union calendar in [start, end) and a close matrix with NaN where an instrument has no close."""
    days = sorted({d for ds, _ in series.values() for d in ds if start <= d < end})
    pos = {d: i for i, d in enumerate(days)}
    out = {}
    for name, (ds, vs) in series.items():
        a = np.full(len(days), np.nan)
        for d, v in zip(ds, vs):
            if d in pos:
                a[pos[d]] = v
        out[name] = a
    return days, out


def _valid(c: np.ndarray) -> list[int]:
    return [j for j in range(len(c)) if np.isfinite(c[j]) and c[j] > 0]


# ── RC-EQ rules ─────────────────────────────────────────────────────────

def tom(dates, closes, n_universe: int, k_pre: int = 1, k_post: int = 3) -> dict:
    """E1 turn of the month: long the last k_pre trading days of a month and the first k_post of
    the next (McConnell & Xu 2008: days -1..+3). Reads the calendar only, never a price."""
    out = {}
    w = 1.0 / n_universe
    for name, c in closes.items():
        idx = _valid(c)
        tgt = np.zeros(len(c))
        months: dict = {}
        for j in idx:
            months.setdefault((dates[j].year, dates[j].month), []).append(j)
        keys = sorted(months)
        for a, b in zip(keys, keys[1:]):
            if (b[0] * 12 + b[1]) - (a[0] * 12 + a[1]) != 1:
                continue  # a missing month in the data: no window across it
            cur, nxt = months[a], months[b]
            if len(cur) < k_pre + 1 or len(nxt) < k_post:
                continue
            for j in cur[-(k_pre + 1):] + nxt[:k_post - 1]:
                tgt[j] = w
        out[name] = tgt
    return out


def dip(dates, closes, n_universe: int, lookback: int = 5, threshold: float = -1.0, max_hold: int = 10,
        vol_n: int = 60, vol_min: int = 50) -> dict:
    """E2 short-horizon reversal: long after a fall of `threshold` volatility-scaled units over
    `lookback` closes; out when the scaled move is back to >= 0 or after `max_hold` closes."""
    out = {}
    w = 1.0 / n_universe
    for name, c in closes.items():
        idx = _valid(c)
        tgt = np.zeros(len(c))
        lc = np.log(np.array([c[j] for j in idx]))
        r = np.r_[np.nan, np.diff(lc)]
        held, count = False, 0
        for k, j in enumerate(idx):
            z = np.nan
            if k >= lookback and k >= vol_n:
                win = r[k - vol_n + 1:k + 1]
                win = win[np.isfinite(win)]
                if len(win) >= vol_min:
                    sd = float(np.std(win, ddof=1))
                    if sd > 0:
                        z = (lc[k] - lc[k - lookback]) / (sd * math.sqrt(lookback))
            if held:
                count += 1
                if (np.isfinite(z) and z >= 0.0) or count >= max_hold:
                    held = False
                else:
                    tgt[j] = w
            elif np.isfinite(z) and z <= threshold:
                held, count = True, 0
                tgt[j] = w
        out[name] = tgt
    return out


def _month_ends(dates, idx) -> list[int]:
    """The last valid close of each calendar month (known in advance from the exchange calendar)."""
    ends = []
    for a, b in zip(idx, idx[1:] + [None]):
        if b is None or (dates[b].year, dates[b].month) != (dates[a].year, dates[a].month):
            ends.append(a)
    return ends


def regime(dates, closes, n_universe: int, months: int = 10) -> dict:
    """E4 trend regime (Faber 2007): at each month-end close, long if the close is above the mean of
    the last `months` month-end closes (including this one), else flat; held for the month."""
    out = {}
    w = 1.0 / n_universe
    for name, c in closes.items():
        idx = _valid(c)
        ends = _month_ends(dates, idx)
        tgt = np.zeros(len(c))
        state = 0.0
        e = set(ends)
        me_vals: list[float] = []
        for j in idx:
            if j in e:
                me_vals.append(c[j])
                state = w if len(me_vals) >= months and c[j] > np.mean(me_vals[-months:]) else 0.0
            tgt[j] = state
        out[name] = tgt
    return out


def volman(dates, closes, n_universe: int, target: float = 0.15, window: int = 21, cap: float = 1.5) -> dict:
    """E5 volatility-managed long (Moreira & Muir 2017, with a fixed target instead of their
    full-sample constant): at each month-end close, weight min(cap, target / realised vol)."""
    out = {}
    for name, c in closes.items():
        idx = _valid(c)
        ends = set(_month_ends(dates, idx))
        tgt = np.zeros(len(c))
        lc = np.log(np.array([c[j] for j in idx]))
        state = 0.0
        for k, j in enumerate(idx):
            if j in ends:
                state = 0.0
                if k >= window:
                    sd = float(np.std(np.diff(lc[k - window:k + 1]), ddof=1)) * math.sqrt(252)
                    if sd > 0:
                        state = min(cap, target / sd) / n_universe
            tgt[j] = state
        out[name] = tgt
    return out


def breakout(dates, closes, n_universe: int, entry: int = 100, exit_ratio: float = 0.5) -> dict:
    """E6 long-only channel breakout (Donchian): long when the close exceeds the highest of the
    previous `entry` closes; out when it falls below the lowest of the previous entry*exit_ratio."""
    out = {}
    w = 1.0 / n_universe
    ex = max(2, int(round(entry * exit_ratio)))
    for name, c in closes.items():
        idx = _valid(c)
        v = np.array([c[j] for j in idx])
        tgt = np.zeros(len(c))
        held = False
        for k, j in enumerate(idx):
            if held and k >= ex and v[k] < np.min(v[k - ex:k]):
                held = False
            elif not held and k >= entry and v[k] > np.max(v[k - entry:k]):
                held = True
            tgt[j] = w if held else 0.0
        out[name] = tgt
    return out


def xsmom(dates, closes, rate_ok, lookback: int = 12, skip: int = 1, k: int = 3, max_age_days: int = 5) -> dict:
    """E3 cross-sectional index momentum: at the last union date of each month, rank the eligible
    indices by their (lookback, skip) month return; long the top k, short the bottom k, 1/(2k) each.
    Filled at each instrument's first close AFTER the decision date. `rate_ok(name, d)` says whether
    the instrument can be financed (held) on d."""
    names = list(closes)
    idx = {n: _valid(closes[n]) for n in names}
    me = {n: {} for n in names}  # (y, m) -> month-end close index, own calendar
    for n in names:
        for j in _month_ends(dates, idx[n]):
            me[n][(dates[j].year, dates[j].month)] = j
    union_ends = _month_ends(dates, list(range(len(dates))))
    decisions = []  # (decision date index, {name: weight})
    for d in union_ends:
        y, m = dates[d].year, dates[d].month

        def back(n, months):
            yy, mm = y, m - months
            while mm <= 0:
                yy, mm = yy - 1, mm + 12
            return me[n].get((yy, mm))

        score = {}
        for n in names:
            p = bisect.bisect_right(idx[n], d) - 1
            if p < 0 or (dates[d] - dates[idx[n][p]]).days > max_age_days or not rate_ok(n, dates[d]):
                continue
            a, b = back(n, skip), back(n, lookback)
            if a is None or b is None or a > d:
                continue
            score[n] = closes[n][a] / closes[n][b] - 1.0
        wts = {}
        if len(score) >= 2 * k:
            order = sorted(score, key=lambda n: (score[n], n))
            for n in order[:k]:
                wts[n] = -1.0 / (2 * k)
            for n in order[-k:]:
                wts[n] = 1.0 / (2 * k)
        decisions.append((d, wts))
    out = {}
    for n in names:
        tgt = np.zeros(len(dates))
        di = 0
        cur = 0.0
        for j in idx[n]:
            while di < len(decisions) and decisions[di][0] < j:
                cur = decisions[di][1].get(n, 0.0)
                di += 1
            tgt[j] = cur
        out[n] = tgt
    return out


def average(*targets: dict) -> dict:
    """One account running several rules: the mean of their targets (offsetting trades net out)."""
    names = set().union(*[set(t) for t in targets])
    n = len(targets)
    return {k: np.sum([t[k] for t in targets if k in t], axis=0) / n for k in names}


# ── RC-FX rules (H.10 fixings; a fill at fixing j uses fixings up to j-2) ──

FX_LAG = 2


def _first_of_month(dates) -> list[int]:
    return [j for j in range(len(dates)) if j == 0 or (dates[j].year, dates[j].month) != (dates[j - 1].year, dates[j - 1].month)]


def fx_composite(dates, usd_per, carry_rate, mom: int = 252, skip: int = 21, value_years: float = 5.0,
                 k: int = 2) -> dict:
    """X1: carry + momentum + value, combined by mean cross-sectional rank among the eligible
    currencies and USD, rebalanced at the first fixing of each month. Long the top k, short the
    bottom k currencies against USD (USD in a set takes no position), 1/(2k) each.

    usd_per[ccy][j]   USD per unit (H.10), NaN on a no-rate day
    carry_rate(ccy, d) policy rate public at the close of d (USD included), NaN if unknown
    """
    ccys = list(usd_per)
    out = {c: np.zeros(len(dates)) for c in ccys}
    centre, half = int(round(value_years * 252)), 126
    reb = _first_of_month(dates)
    cur: dict = {}
    nxt = iter(reb + [len(dates)])
    stop = next(nxt)
    for j in range(len(dates)):
        if j == stop:
            stop = next(nxt)
            u = j - FX_LAG
            cur = {}
            if u >= 0:
                ls = {}
                for c in ccys + ["USD"]:
                    r = carry_rate(c, dates[j - 1])
                    if not math.isfinite(r):
                        continue
                    if c == "USD":
                        ls[c] = (r, 0.0, 0.0)
                        continue
                    s = usd_per[c]
                    need = (u, u - skip, u - mom, u - centre - half, u - centre + half)
                    if min(need) < 0 or not all(np.isfinite(s[i]) for i in need[:3]):
                        continue
                    hist = s[u - centre - half:u - centre + half + 1]
                    hist = hist[np.isfinite(hist)]
                    if len(hist) < 126:
                        continue
                    ls[c] = (r, math.log(s[u - skip] / s[u - mom]), -(math.log(s[u]) - float(np.mean(np.log(hist)))))
                if len(ls) >= max(6, 2 * k + 1):
                    names = sorted(ls)
                    comp = {n: 0.0 for n in names}
                    for f in range(3):
                        order = sorted(names, key=lambda n: (ls[n][f], n))
                        for rank, n in enumerate(order):
                            comp[n] += (rank - (len(order) - 1) / 2.0) / 3.0
                    order = sorted(names, key=lambda n: (comp[n], n))
                    for n in order[:k]:
                        if n != "USD":
                            cur[n] = -1.0 / (2 * k)
                    for n in order[-k:]:
                        if n != "USD":
                            cur[n] = 1.0 / (2 * k)
        for c in ccys:
            out[c][j] = cur.get(c, 0.0)
    return out


def fx_tsmom(dates, usd_per, lookback: int = 252) -> dict:
    """X2 base: each currency long (short) against USD when its `lookback`-fixing change is up
    (down), 1/n each, rebalanced at the first fixing of each month."""
    ccys = list(usd_per)
    out = {c: np.zeros(len(dates)) for c in ccys}
    cur: dict = {}
    reb = set(_first_of_month(dates))
    for j in range(len(dates)):
        if j in reb:
            u = j - FX_LAG
            cur = {}
            for c in ccys:
                s = usd_per[c]
                if u - lookback >= 0 and np.isfinite(s[u]) and np.isfinite(s[u - lookback]):
                    cur[c] = math.copysign(1.0 / len(ccys), s[u] / s[u - lookback] - 1.0)
        for c in ccys:
            out[c][j] = cur.get(c, 0.0)
    return out


def cot_percentile(as_of_epochs: np.ndarray, avail: np.ndarray, net_share: np.ndarray, t: int,
                   window_days: int = 364, min_reports: int = 39) -> float:
    """COT-1's positioning percentile, public at time t: the latest report available by t, ranked
    (ties half) among the reports whose as-of falls in the 364 days before it. NaN if too few."""
    i = int(np.searchsorted(avail, t, "right")) - 1
    if i < 0:
        return float("nan")
    lo = as_of_epochs[i] - window_days * 86400
    sel = (as_of_epochs >= lo) & (as_of_epochs < as_of_epochs[i]) & (avail <= t)
    hist = net_share[sel]
    if len(hist) < min_reports:
        return float("nan")
    x = net_share[i]
    return float((np.sum(hist < x) + 0.5 * np.sum(hist == x)) / len(hist))


def cot_filter(dates, base: dict, pct_at, threshold: float = 0.90) -> dict:
    """X2: the base trend positions, except that a currency is not held in the direction in which
    leveraged funds are already crowded (percentile >= threshold for a long, <= 1 - threshold for
    a short). `pct_at(ccy, j)` is the percentile public at the decision before fill j."""
    out = {}
    reb = set(_first_of_month(dates))
    for c, tgt in base.items():
        f = np.zeros(len(dates))
        cur = 0.0
        for j in range(len(dates)):
            if j in reb:
                cur = tgt[j]
                p = pct_at(c, j)
                if cur > 0 and math.isfinite(p) and p >= threshold:
                    cur = 0.0
                elif cur < 0 and math.isfinite(p) and p <= 1.0 - threshold:
                    cur = 0.0
            f[j] = cur
        out[c] = f
    return out


__all__ = ["FX_LAG", "MAX_RATE_PCT", "RC_VERSION", "Rates", "average", "breakout", "clean", "cot_filter", "cot_percentile",
           "dip", "fx_composite", "fx_tsmom", "panel", "regime", "tom", "volman", "xsmom"]
