"""KRP-1: does a coin's Korean premium lift its global price the next day? (research/preregistrations/KRP-1.md)

Korean residents trade on KRW venues that foreigners cannot use, and capital controls slow and cap moving KRW abroad.
A coin can then cost more on Upbit than abroad, beyond what bitcoin's own Korean premium explains. That relative gap
can be closed without moving KRW out of Korea: sell the coin on Upbit, buy bitcoin there, ship the bitcoin out, buy
the coin abroad. That buying should lift the coin against bitcoin on the global venue over the following hours.

The relative premium of coin i at the 00:00 UTC daily close is its price in bitcoin on Upbit over its price in
bitcoin on Binance: rho = ln(U_i / U_btc) - ln(B_i / B_btc). No exchange rate is needed: it cancels. An entry is a
FRESH spike: rho >= theta while the median of rho over the 30 days before stayed below theta / 2 (a persistent gap is
a blocked arbitrage, a renamed or redenominated asset, or a data mismatch: none is the mechanism), with |rho| <= 1.

The trade: buy the coin on Binance spot an hour after the close (the close of the hour 00:00-01:00 UTC), and sell
24 hours later, against a short of bitcoin over the same hours (a swap-free BTC CFD): the judged figure is the coin's
return minus bitcoin's, minus the costs of both legs. The contrast is the same spike with the opposite sign (a Korean
discount): if the mechanism is arbitrage, discounts must not do as well. Nothing here trades.
"""

from __future__ import annotations

import math
import random
from datetime import date, datetime, timedelta, timezone

import numpy as np

from aitrader.research.events.cascade import nw_t

KRP_VERSION = "krp-1.0.0"
HOUR = 3_600_000
DAY = 86_400_000
#: stablecoins and the numeraire are never entries
EXCLUDED = frozenset({"BTC", "USDT", "USDC", "TUSD", "BUSD", "DAI", "FDUSD", "USDP", "PAX", "USDS", "PYUSD", "USDE",
                      "EURC", "USD1", "RLUSD", "XUSD", "USDD", "GUSD"})


def ms_of(day: str) -> int:
    return int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp() * 1000)


def day_of_ms(t: int) -> str:
    return datetime.fromtimestamp(t / 1000, timezone.utc).date().isoformat()


def days_between(a: str, b: str) -> list[str]:
    d, e, out = date.fromisoformat(a), date.fromisoformat(b), []
    while d <= e:
        out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def relative_premium(u_coin: float | None, u_btc: float | None, b_coin: float | None,
                     b_btc: float | None) -> float | None:
    """ln(U_i / U_btc) - ln(B_i / B_btc), or None if any price is missing or not positive."""
    xs = (u_coin, u_btc, b_coin, b_btc)
    if not all(isinstance(x, (int, float)) and math.isfinite(x) and x > 0 for x in xs):
        return None
    return math.log(u_coin / u_btc) - math.log(b_coin / b_btc)


class Panel:
    """Upbit's daily candles (KRW close and KRW turnover by UTC day), and Binance's hourly bars (close and quote
    volume) on one grid starting at t0 (ms), for each coin and for bitcoin."""

    def __init__(self, coins: list[str], t0: int, hours: int):
        self.coins, self.t0, self.n = sorted(coins), t0, hours
        self.idx = {c: k for k, c in enumerate(self.coins)}
        self.close = np.full((len(self.coins), hours), np.nan)
        self.qvol = np.full((len(self.coins), hours), np.nan)
        self.btc = np.full(hours, np.nan)
        self.upbit: dict[str, dict[str, tuple[float, float]]] = {c: {} for c in self.coins + ["BTC"]}
        self.first_upbit: dict[str, str] = {}
        self.first_binance: dict[str, int] = {}

    def put_hourly(self, coin: str, bars: dict[int, tuple[float, float]]) -> None:
        """{bar open time ms: (close, quote volume)}; BTC goes to its own row."""
        for t, (c, q) in bars.items():
            i = (t - self.t0) // HOUR
            if 0 <= i < self.n and c > 0:
                if coin == "BTC":
                    self.btc[i] = c
                else:
                    k = self.idx[coin]
                    self.close[k, i] = c
                    self.qvol[k, i] = q

    def put_upbit(self, coin: str, candles: dict[str, tuple[float, float]]) -> None:
        """{UTC day: (KRW close, KRW turnover)} of the daily candle that opens at 00:00 UTC that day."""
        self.upbit.setdefault(coin, {}).update(candles)
        if candles:
            first = min(candles)
            self.first_upbit[coin] = min(first, self.first_upbit.get(coin, first))

    def hour(self, t: int) -> int:
        return (t - self.t0) // HOUR

    def bar_close(self, coin: str, t_open: int) -> float | None:
        """The close of the hourly bar that opens at t_open (it closes an hour later)."""
        i = self.hour(t_open)
        if not 0 <= i < self.n:
            return None
        v = self.btc[i] if coin == "BTC" else self.close[self.idx[coin], i]
        return float(v) if math.isfinite(v) else None

    def day_close(self, coin: str, day: str) -> float | None:
        """Binance's close at 00:00 UTC after `day`: the close of the bar that opens at 23:00 that day."""
        return self.bar_close(coin, ms_of(day) + 23 * HOUR)

    def day_quote_volume(self, coin: str, day: str) -> float | None:
        i = self.hour(ms_of(day))
        if not (0 <= i and i + 24 <= self.n):
            return None
        q = self.qvol[self.idx[coin], i:i + 24]
        return float(np.nansum(q)) if np.isfinite(q).any() else None

    def rho(self, coin: str, day: str) -> float | None:
        u, ub = self.upbit.get(coin, {}).get(day), self.upbit.get("BTC", {}).get(day)
        return relative_premium(u[0] if u else None, ub[0] if ub else None, self.day_close(coin, day),
                                self.day_close("BTC", day))


def seasoned(p: Panel, coin: str, day: str, min_age_days: int) -> bool:
    """Both listings at least min_age_days old on `day` (Upbit's first candle; Binance's first bar or listing)."""
    fu, fb = p.first_upbit.get(coin), p.first_binance.get(coin)
    if fu is None or fb is None:
        return False
    d = date.fromisoformat(day)
    return (d - date.fromisoformat(fu)).days >= min_age_days and (ms_of(day) - fb) // DAY >= min_age_days


def rho_series(p: Panel, coin: str, days: list[str]) -> dict[str, float]:
    out = {}
    for d in days:
        r = p.rho(coin, d)
        if r is not None:
            out[d] = r
    return out


def _trailing_median(series: dict[str, float], day: str, window: int) -> float | None:
    d = date.fromisoformat(day)
    xs = [series[k] for k in ((d - timedelta(days=j)).isoformat() for j in range(1, window + 1)) if k in series]
    if len(xs) < window // 2:
        return None
    xs.sort()
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else 0.5 * (xs[m - 1] + xs[m])


def eligible(p: Panel, coin: str, day: str, spec: dict) -> bool:
    """A coin-day the rule may look at: seasoned on both venues, Korean and global turnover above their floors."""
    if coin in EXCLUDED or not seasoned(p, coin, day, spec["min_age_days"]):
        return False
    u = p.upbit.get(coin, {}).get(day)
    if not u or not (u[1] >= spec["min_upbit_krw"]):
        return False
    q = p.day_quote_volume(coin, day)
    return q is not None and q >= spec["min_binance_usd"]


def classify(p: Panel, coin: str, day: str, series: dict[str, float], theta: float, sign: int, spec: dict) -> bool:
    """A fresh spike of the given sign: sign*rho >= theta, |rho| <= the cap, the trailing median below theta/2."""
    r = series.get(day)
    if r is None or abs(r) > spec["rho_cap"] or sign * r < theta:
        return False
    m = _trailing_median(series, day, spec["trailing_days"])
    return m is not None and sign * m < theta / 2


def trade(p: Panel, coin: str, day: str, lag_hours: int, hold_hours: int, cost: float) -> dict:
    """Long the coin, short bitcoin, from the close of the hour `lag_hours` after the daily close to `hold_hours`
    later. Missing prices are recorded as missing, never filled."""
    t_in = ms_of(day) + DAY + (lag_hours - 1) * HOUR  # the bar opening then closes lag_hours after 00:00 UTC
    t_out = t_in + hold_hours * HOUR
    a, b, x, y = (p.bar_close(coin, t_in), p.bar_close(coin, t_out), p.bar_close("BTC", t_in),
                  p.bar_close("BTC", t_out))
    if None in (a, b, x, y):
        return {"coin": coin, "day": day, "missing": True}
    r, rb = b / a - 1, y / x - 1
    return {"coin": coin, "day": day, "ret": r, "btc_ret": rb, "excess": r - rb, "net": r - rb - cost}


def entries(p: Panel, days: list[str], theta: float, sign: int, spec: dict, lag_hours: int | None = None,
            series: dict[str, dict[str, float]] | None = None) -> list[dict]:
    """Every fresh spike of the sign in `days` with its trade. One position per coin at a time: an entry while the
    coin's previous trade is still open is skipped."""
    lag = spec["lag_hours"] if lag_hours is None else lag_hours
    out = []
    for c in p.coins:
        if c in EXCLUDED:
            continue
        s = series[c] if series is not None else rho_series(p, c, days_with_lookback(days, spec["trailing_days"]))
        busy_until = -1
        for d in days:
            t_in = ms_of(d) + DAY + (lag - 1) * HOUR
            if t_in <= busy_until or not eligible(p, c, d, spec) or not classify(p, c, d, s, theta, sign, spec):
                continue
            e = trade(p, c, d, lag, spec["hold_hours"], spec["cost_round_trip"])
            e["rho"] = s[d]
            out.append(e)
            busy_until = t_in + spec["hold_hours"] * HOUR - 1
    return out


def days_with_lookback(days: list[str], trailing: int) -> list[str]:
    return days_between((date.fromisoformat(days[0]) - timedelta(days=trailing)).isoformat(), days[-1])


def placebos(p: Panel, evs: list[dict], theta: float, spec: dict, series: dict[str, dict[str, float]],
             seed: int, window: tuple[str, str]) -> dict[tuple[str, str], list[float]]:
    """For each traded entry, the same coin's net (against bitcoin) from up to `draws` random ordinary days within
    `span` days either side (|rho| below theta/3, not within two days of the entry), each eligible itself and inside
    the stage's own decision window: a placebo never reads a day the stage may not."""
    rng, out = random.Random(seed), {}
    span, draws = spec["placebo_span_days"], spec["placebo_draws_per_entry"]
    lo, hi = window
    for e in evs:
        if e.get("missing"):
            continue
        c, d0 = e["coin"], date.fromisoformat(e["day"])
        s = series[c]
        cand = []
        for j in range(-span, span + 1):
            if abs(j) < 2:
                continue
            d = (d0 + timedelta(days=j)).isoformat()
            if not lo <= d <= hi:
                continue
            r = s.get(d)
            if r is not None and abs(r) < theta / 3 and eligible(p, c, d, spec):
                cand.append(d)
        nets = []
        for d in rng.sample(cand, min(draws, len(cand))):
            t = trade(p, c, d, spec["lag_hours"], spec["hold_hours"], spec["cost_round_trip"])
            if not t.get("missing"):
                nets.append(t["net"])
        if nets:
            out[(c, e["day"])] = nets
    return out


def cohorts(evs: list[dict], key: str = "net") -> dict[str, float]:
    acc: dict[str, list[float]] = {}
    for e in evs:
        acc.setdefault(e["day"], []).append(e[key])
    return {d: sum(v) / len(v) for d, v in sorted(acc.items())}


def _stat(xs: list[dict], key: str = "net") -> float | None:
    c = cohorts(xs, key)
    return sum(c.values()) / len(c) if c else None


def judge(evs: list[dict], late: list[dict], contra: list[dict], plac: dict, bar: float, cost: float,
          min_events: int, min_days: int, seed: int, draws: int, lag: int = 1) -> dict:
    """One threshold's entries against every preregistered gate; too few is INCONCLUSIVE, never a pass."""
    ok = [e for e in evs if not e.get("missing")]
    c = cohorts(ok)
    m, t = nw_t(list(c.values()), lag)
    out = {"entries": len(evs), "traded": len(ok), "missing": len(evs) - len(ok), "days": len(c), "mean_net": m,
           "t": t, "bar": bar}
    if len(ok) < min_events or len(c) < min_days:
        return {**out, "verdict": "INCONCLUSIVE",
                "why": f"{len(ok)} entries on {len(c)} days: {min_events} and {min_days} are needed"}
    ks = list(c)
    h = len(ks) // 2
    first, second = sum(c[k] for k in ks[:h]) / h, sum(c[k] for k in ks[h:]) / (len(ks) - h)
    top = set(sorted(range(len(ok)), key=lambda i: ok[i]["net"], reverse=True)[:5])
    no_top = _stat([e for i, e in enumerate(ok) if i not in top])
    weight = {d: c[d] * sum(1 for e in ok if e["day"] == d) for d in c}
    best_day = max(weight, key=weight.get)
    no_day = _stat([e for e in ok if e["day"] != best_day])
    coins: dict[str, float] = {}
    for e in ok:
        coins[e["coin"]] = coins.get(e["coin"], 0.0) + e["net"]
    bc = max(coins, key=coins.get)
    no_coin = _stat([e for e in ok if e["coin"] != bc])
    x2 = _stat([{**e, "net": e["net"] - cost} for e in ok])
    late_ok = [e for e in late if not e.get("missing")]
    lt = _stat(late_ok) if late_ok else None
    contra_ok = [e for e in contra if not e.get("missing")]
    cm = _stat(contra_ok) if contra_ok else None
    rng = random.Random(seed)
    usable = [e for e in ok if plac.get((e["coin"], e["day"]))]
    pdays = sorted({e["day"] for e in usable})
    pos = {d: i for i, d in enumerate(pdays)}
    wi = [pos[e["day"]] for e in usable]
    cnt = [0] * len(pdays)
    for i in wi:
        cnt[i] += 1
    ds = []
    for _ in range(draws if usable else 0):
        acc = [0.0] * len(pdays)
        for i, e in zip(wi, usable):
            acc[i] += rng.choice(plac[(e["coin"], e["day"])])
        ds.append(sum(a / n for a, n in zip(acc, cnt)) / len(pdays))
    ds.sort()
    p95 = ds[int(0.95 * draws) - 1] if ds else None
    gates = {"t": t is not None and t >= bar, "costs_x2": x2 is not None and x2 > 0,
             "halves": first > 0 and second > 0, "top5_removed": no_top is not None and no_top > 0,
             "late_entry": lt is not None and lt > 0, "beats_placebo": p95 is not None and m is not None and m > p95,
             "without_best_day": no_day is not None and no_day > 0,
             "without_best_coin": no_coin is not None and no_coin > 0,
             "beats_korean_discounts": cm is not None and m is not None and m > cm}
    xs = sorted(e["net"] for e in ok)
    return {**out, "verdict": "PASSED" if all(gates.values()) else "FAILED", "gates": gates,
            "gross_mean": _stat([{**e, "net": e["net"] + cost} for e in ok]),
            "mean_ret_unhedged": _stat(ok, "ret"), "mean_excess_before_costs": _stat(ok, "excess"),
            "costs_x2_mean": x2, "first_half": first, "second_half": second, "without_top5_mean": no_top,
            "late_mean": lt, "placebo_p95": p95,
            "placebo_share_at_or_above": (sum(d >= m for d in ds) / len(ds)) if ds and m is not None else None,
            "best_day": best_day, "without_best_day_mean": no_day, "best_coin": bc, "without_best_coin_mean": no_coin,
            "korean_discounts": len(contra_ok), "korean_discount_mean_net": cm, "median_net": xs[len(xs) // 2],
            "positive_share": sum(x > 0 for x in xs) / len(xs), "worst_net": xs[0], "best_net": xs[-1],
            "coins": len(coins)}
