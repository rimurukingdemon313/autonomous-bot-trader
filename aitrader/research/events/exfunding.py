"""EXF-1: the ex-funding pass-through of perpetual futures (research/preregistrations/EXF-1.md).

A perpetual pays its funding at discrete settlement times T: whoever holds a long at T pays F_T times the notional
(a short receives it). A contract that costs nothing to enter and pays a known cash flow at a known time must, absent
frictions, move by that cash flow at that time, as a share goes ex-dividend. With r_index the index's return and
prem = perp / index - 1, the frictionless prediction for a window [T-5m, T+5m] is

    E[prem(T+5m) - prem(T-5m) | F_T] = beta * F_T,  with beta = 1.

If the market passes on only a fraction beta < 1 of the payment, the side that receives it and holds only across T
earns (1 - beta)|F_T| before costs, and nothing at any other time of the interval. This module measures beta on
5-minute bars and judges one fixed rule built on it. It reads bars, it never trades.

The rule decides at T-5m from what is known then: the previous settlement's rate F_hat (known one interval earlier)
predicts the sign and the size of F_T. It takes the side F_hat says receives the funding, enters at the close of the
bar ending at T-5m, pays or receives the ACTUAL F_T, and exits at the close of the bar ending at T+5m.
"""

from __future__ import annotations

import csv
import io
import math
import random
import zipfile
from datetime import datetime, timezone

EXF_VERSION = "exf-1.0.0"
M5 = 300_000  # five minutes, in milliseconds
HOUR = 3_600_000
#: a previous settlement older than this is no prediction (a gap in the archive, or a contract that was halted)
MAX_GAP = 9 * HOUR


def rows(raw: bytes) -> list[list[str]]:
    """The rows of the CSV file inside a Binance archive zip."""
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        return list(csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]), encoding="utf-8")))


def ms(x: str) -> int:
    """A Binance timestamp in milliseconds (the newer files write microseconds)."""
    v = int(float(x))
    return v // 1000 if v > 10**14 else v


def parse_bars(rs: list[list[str]]) -> dict[int, tuple[float, float]]:
    """{open time in ms: (close, quote volume)} of 5-minute klines (a perpetual's or its index's). A header row, or a
    row that cannot be read, is skipped, never repaired."""
    out = {}
    for r in rs:
        if len(r) > 7 and r[0].strip()[:1].isdigit():
            try:
                t, c, qv = ms(r[0]), float(r[4]), float(r[7] or 0)
            except ValueError:
                continue
            if c > 0:
                out[t] = (c, qv)
    return out


def parse_settlements(rs: list[list[str]]) -> list[tuple[int, float]]:
    """[(settlement time in ms, to the minute; rate)] of a funding file, in time order. The rate is what a long paid,
    as a fraction of notional."""
    out = {}
    for r in rs:
        if len(r) > 2 and r[0].strip()[:1].isdigit():
            try:
                t, f = ms(r[0]), float(r[2])
            except ValueError:
                continue
            out[(t + 30_000) // 60_000 * 60_000] = f
    return sorted(out.items())


def _close(bars: dict[int, tuple[float, float]], at: int) -> float | None:
    """The price at `at`: the close of the 5-minute bar that ends there."""
    b = bars.get(at - M5)
    return b[0] if b else None


def placebo_times(t: int, gap: int) -> list[int]:
    """Three times inside the interval before T, a quarter, a half and three quarters of it earlier, on the 5-minute
    grid. No funding is paid across a window around them."""
    return [t - (gap * j // 4) // M5 * M5 for j in (1, 2, 3)]


def events(symbol: str, settle: list[tuple[int, float]], perp: dict[int, tuple[float, float]],
           index: dict[int, tuple[float, float]], first: int, last: int) -> list[dict]:
    """Every settlement of one contract with T in [first, last], with what the rule and the measurement need. A
    settlement whose previous one is missing or stale has no prediction; one with a bar missing is incomplete. Both
    are kept and counted, never filled."""
    out = []
    for (t0, f0), (t, f) in zip(settle, settle[1:]):
        if not first <= t <= last:
            continue
        gap = t - t0
        e = {"symbol": symbol, "T": t, "F": f, "F_hat": f0, "gap_h": round(gap / HOUR, 3)}
        if gap <= 0 or gap > MAX_GAP:
            e["no_prediction"] = True
            out.append(e)
            continue
        at = {"early": t - 2 * M5, "entry": t - M5, "pre": t, "exit": t + M5}  # price times: T-10m, T-5m, T, T+5m
        p = {k: _close(perp, v) for k, v in at.items()}
        q = {k: _close(index, v) for k, v in at.items()}
        if None in p.values() or None in q.values():
            e["incomplete"] = True
            out.append(e)
            continue
        prem = {k: p[k] / q[k] - 1 for k in at}
        e.update(complete=True, r=p["exit"] / p["entry"] - 1, r_early=p["exit"] / p["early"] - 1,
                 r_index=q["exit"] / q["entry"] - 1, dprem=prem["exit"] - prem["entry"],
                 pre_move=prem["pre"] - prem["entry"], post_move=prem["exit"] - prem["pre"],
                 prem_entry=prem["entry"], qv=perp[at["entry"] - M5][1])
        pl = []
        for tp in placebo_times(t, gap):
            a, b = _close(perp, tp - M5), _close(perp, tp + M5)
            pl.append(b / a - 1 if a and b else None)
        e["placebo"] = pl
        out.append(e)
    return out


# ── the rule ────────────────────────────────────────────────────────────────

def trades(evs: list[dict], theta: float, cost: float, min_qv: float) -> list[dict]:
    """The settlements where the prediction |F_hat| is at least theta and the bar before entry traded at least
    min_qv (quote currency): the side F_hat says receives the funding, held from T-5m to T+5m. Its net is the price
    move on that side, the funding it actually paid or received at T, and two fills."""
    out = []
    for e in evs:
        if not e.get("complete") or abs(e["F_hat"]) < theta or e["qv"] < min_qv:
            continue
        s = -1 if e["F_hat"] > 0 else 1
        out.append({"symbol": e["symbol"], "T": e["T"], "side": s, "F": e["F"], "F_hat": e["F_hat"],
                    "net": s * e["r"] - s * e["F"] - 2 * cost, "early": s * e["r_early"] - s * e["F"] - 2 * cost,
                    "funding": -s * e["F"], "placebo": [s * x - 2 * cost for x in e["placebo"] if x is not None]})
    return out


def week(t: int) -> str:
    y, w, _ = datetime.fromtimestamp(t / 1000, timezone.utc).isocalendar()
    return f"{y:04d}-W{w:02d}"


def cohorts(ts: list[dict], key: str = "net") -> dict[str, float]:
    """The mean of `key` over the trades of each ISO week, in week order."""
    acc: dict[str, list[float]] = {}
    for x in ts:
        acc.setdefault(week(x["T"]), []).append(x[key])
    return {k: sum(v) / len(v) for k, v in sorted(acc.items())}


def nw_t(xs: list[float], lag: int = 2) -> tuple[float | None, float | None]:
    """The mean and its t-statistic with a Newey-West standard error (Bartlett weights). None when undefined."""
    n = len(xs)
    if n < 3:
        return (sum(xs) / n if n else None), None
    m = sum(xs) / n
    d = [x - m for x in xs]
    if max(abs(v) for v in d) <= 1e-12 * max(1.0, abs(m)):  # no spread: rounding must not make a t-statistic
        return m, None
    s = sum(v * v for v in d) / n
    for k in range(1, min(lag, n - 1) + 1):
        s += 2 * (1 - k / (lag + 1)) * sum(d[i] * d[i - k] for i in range(k, n)) / n
    return (m, None) if s <= 0 else (m, m / math.sqrt(s / n))


def _stat(ts: list[dict], key: str = "net") -> float | None:
    c = cohorts(ts, key)
    return sum(c.values()) / len(c) if c else None


def judge(ts: list[dict], bar: float, cost: float, min_events: int, min_weeks: int, seed: int = 20261115,
          placebos: int = 1000, lag: int = 2) -> dict:
    """One threshold's trades against every preregistered gate. Every gate is required; too few trades or weeks is
    INCONCLUSIVE, never a pass."""
    c = cohorts(ts)
    m, t = nw_t(list(c.values()), lag)
    out = {"trades": len(ts), "weeks": len(c), "mean": m, "t": t, "bar": bar}
    if len(ts) < min_events or len(c) < min_weeks:
        return {**out, "verdict": "INCONCLUSIVE",
                "why": f"{len(ts)} trades in {len(c)} weeks: {min_events} and {min_weeks} are needed"}
    ks = list(c)
    h = len(ks) // 2
    first, second = sum(c[k] for k in ks[:h]) / h, sum(c[k] for k in ks[h:]) / (len(ks) - h)
    top = sorted(range(len(ts)), key=lambda i: ts[i]["net"], reverse=True)[:5]
    no_top = _stat([x for i, x in enumerate(ts) if i not in set(top)])
    years: dict[str, float] = {}
    syms: dict[str, float] = {}
    for x in ts:
        y = datetime.fromtimestamp(x["T"] / 1000, timezone.utc).strftime("%Y")
        years[y] = years.get(y, 0.0) + x["net"]
        syms[x["symbol"]] = syms.get(x["symbol"], 0.0) + x["net"]
    best_year, best_sym = max(years, key=years.get), max(syms, key=syms.get)
    no_year = _stat([x for x in ts if datetime.fromtimestamp(x["T"] / 1000, timezone.utc).strftime("%Y") != best_year])
    no_sym = _stat([x for x in ts if x["symbol"] != best_sym])
    x2 = _stat([{**x, "net": x["net"] - 2 * cost} for x in ts])
    early = _stat(ts, "early")
    rng = random.Random(seed)
    usable = [x for x in ts if x["placebo"]]
    keys = sorted({week(x["T"]) for x in usable})
    pos = {k: i for i, k in enumerate(keys)}
    wi = [pos[week(x["T"])] for x in usable]
    cnt = [0] * len(keys)
    for i in wi:
        cnt[i] += 1
    draws = []
    for _ in range(placebos if usable else 0):  # one placebo window drawn per trade, the same weeks, no funding
        acc = [0.0] * len(keys)
        for i, x in zip(wi, usable):
            acc[i] += rng.choice(x["placebo"])
        draws.append(sum(a / n for a, n in zip(acc, cnt)) / len(keys))
    draws.sort()
    p95 = draws[int(0.95 * placebos) - 1] if draws else None
    gates = {"t": t is not None and t >= bar, "costs_x2": x2 is not None and x2 > 0,
             "halves": first > 0 and second > 0, "top5_removed": no_top is not None and no_top > 0,
             "early_entry": early is not None and early > 0,
             "beats_placebo": p95 is not None and m is not None and m > p95,
             "without_best_year": no_year is not None and no_year > 0,
             "without_best_symbol": no_sym is not None and no_sym > 0}
    gross = _stat([{**x, "net": x["net"] + 2 * cost} for x in ts])
    return {**out, "verdict": "PASSED" if all(gates.values()) else "FAILED", "gates": gates,
            "gross_mean": gross, "costs_x2_mean": x2, "first_half": first, "second_half": second,
            "without_top5_mean": no_top, "early_mean": early, "placebo_p95": p95,
            "placebo_share_at_or_above": (sum(d >= m for d in draws) / len(draws)) if draws and m is not None else None,
            "best_year": best_year, "without_best_year_mean": no_year, "best_symbol": best_sym,
            "without_best_symbol_mean": no_sym, "funding_mean": _stat(ts, "funding"),
            "positive_share": sum(x["net"] > 0 for x in ts) / len(ts), "symbols": len(syms),
            "by_year_sum": {k: years[k] for k in sorted(years)}}


# ── the mechanism, measured on every settlement ─────────────────────────────

BUCKETS = ((0.0, 0.00011), (0.00011, 0.0005), (0.0005, 0.001), (0.001, 0.002), (0.002, 0.005), (0.005, 1.0))


def ols(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    return None if sxx <= 0 else sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx


def mechanism(evs: list[dict]) -> dict:
    """How much of the payment the premium passes on across T, by size of the payment: the pass-through ratio
    E[sign(F) dprem] / E[|F|] (1 when fully priced, 0 when ignored), and how much of the move comes before T and
    how much after. Descriptive: no gate is set on it."""
    ok = [e for e in evs if e.get("complete")]
    out = {"settlements": len(evs), "complete": len(ok), "no_prediction": sum(1 for e in evs if e.get("no_prediction")),
           "incomplete": sum(1 for e in evs if e.get("incomplete")),
           "beta_pooled": ols([e["F"] for e in ok], [e["dprem"] for e in ok]), "buckets": []}
    for lo, hi in BUCKETS:
        b = [e for e in ok if lo <= abs(e["F"]) < hi]
        if not b:
            continue
        af = sum(abs(e["F"]) for e in b) / len(b)
        sgn = [1 if e["F"] >= 0 else -1 for e in b]
        mv = sum(s * e["dprem"] for s, e in zip(sgn, b)) / len(b)
        out["buckets"].append({"abs_F_from": lo, "abs_F_to": hi, "n": len(b), "mean_abs_F": af,
                               "mean_signed_dprem": mv, "pass_through": mv / af if af > 0 else None,
                               "pre": sum(s * e["pre_move"] for s, e in zip(sgn, b)) / len(b),
                               "post": sum(s * e["post_move"] for s, e in zip(sgn, b)) / len(b)})
    return out
