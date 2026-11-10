"""The panels the lab reads, each with its discovery and validation windows.

- `energy`: EIA's NYMEX contracts 1-3 of WTI, heating oil, RBOB and natural gas (ENG-1's data, on branch eng1-run). The
  tradable return is that of holding the contract that is contract 2, rolled when contract 1 expires, exactly as ENG-1
  identifies contracts (scripts/eng1.py). State series: each curve's two slopes, and each product's price against
  WTI's.
- `crypto_hourly`: BTCUSDT and ETHUSDT perpetual hours with open interest (LIQ-1's development data, on liq1-run).
- `synthetic`: built markets with or without a planted structure, for the tests and the operating characteristic.

A loader takes `last` and returns nothing at or after it: discovery cannot read its validation window, because the
rows are not in memory.
"""

from __future__ import annotations

import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from .panel import Panel

ROOT = Path(__file__).resolve().parents[3]
#: discovery (fit, then check) and validation windows, [start, end). The validation window is read once, by a
#: preregistered judge. Energy: ENG-1 judged 1985..2018 once (monthly, the curve's slope); 2019 on is unread.
WINDOWS = {
    "energy-futures-eia": {"fit": (date(1994, 3, 1), date(2004, 1, 1)), "check": (date(2004, 1, 1), date(2012, 1, 1)),
                           "validation": (date(2012, 1, 1), date(2024, 4, 6))},
    "crypto-binance-usdtm": {"fit": (datetime(2020, 9, 1, tzinfo=timezone.utc), datetime(2022, 7, 1, tzinfo=timezone.utc)),
                             "check": (datetime(2022, 7, 1, tzinfo=timezone.utc), datetime(2024, 1, 1, tzinfo=timezone.utc)),
                             "validation": (datetime(2024, 1, 1, tzinfo=timezone.utc),
                                            datetime(2026, 11, 1, tzinfo=timezone.utc))},
}


#: WTI and natural gas only. EIA prices heating oil on about half the days before 2007 and RBOB only from 2005-10:
#: neither has the rows the fit window needs.
ENERGY = ("WTI", "NATGAS")


def energy(last: date, data: Path | None = None, assets: tuple = ENERGY, first: date = date(1993, 1, 1)) -> Panel:
    """The energy panel from `first`, with nothing on or after `last`."""
    import scripts.eng1 as e
    if data is not None:
        e.DATA = Path(data)
    curves, bdays = e.load(last)
    names = tuple(n for n in assets if n in curves)
    days = sorted({d for n in names for d in curves[n].days if first <= d < last})
    row = {d: i for i, d in enumerate(days)}
    ret = np.full((len(days), len(names)), np.nan)
    hold = np.zeros_like(ret)
    aux = {f"{n}.{s}": np.full(len(days), np.nan) for n in names for s in ("s12", "s23")}
    aux.update({f"{n}.vs_wti": np.full(len(days), np.nan) for n in names if n != "WTI"})
    for j, n in enumerate(names):
        cv = curves[n]
        prev = None
        for d in cv.days:
            if d >= last:
                break
            if d < first:
                continue
            c1, c2, c3 = cv.c[d]
            i = row[d]
            if c1 > 0 and c2 > 0 and c3 > 0:
                aux[f"{n}.s12"][i], aux[f"{n}.s23"][i] = math.log(c1 / c2), math.log(c2 / c3)
                w = curves["WTI"].c.get(d) if n != "WTI" else None
                if w is not None and w[1] > 0:
                    aux[f"{n}.vs_wti"][i] = math.log(c2 / w[1])
            if prev is not None:
                f0 = e.front_delivery(cv.kind, prev, bdays)
                held = e._month_add(*f0, 1)  # contract 2 at the previous priced day
                p0, p1 = cv.c[prev][1], e.price_of(cv, held, d, bdays)
                if p1 is not None and p0 > 0 and p1 > 0:
                    ret[i, j] = p1 / p0 - 1.0
                    if e.front_delivery(cv.kind, d, bdays) != f0:  # contract 1 expired: the position is rolled
                        hold[row[prev], j] = e.COST_BP[n] / 1e4
            prev = d
    return Panel("energy-futures-eia", days, names, ret, aux, {n: e.COST_BP[n] / 1e4 for n in names}, 252.0, hold)


def crypto_hourly(last: datetime, data: Path | None = None, cost: float = 0.0015) -> Panel:
    """BTCUSDT and ETHUSDT perpetual hours, close to close, with nothing at or after `last`. The open-interest state is
    the change over the PREVIOUS hour: the snapshot taken at an hour's close may not be published when it closes."""
    data = Path(data) if data else ROOT / "data" / "liq1"
    syms = ("BTCUSDT", "ETHUSDT")
    kl = {s: json.loads((data / f"{s}-klines.json").read_text()) for s in syms}
    oi = {s: json.loads((data / f"{s}-oi.json").read_text()) for s in syms}
    fmt = "%Y-%m-%dT%H"
    first = min(datetime.strptime(min(kl[s]), fmt) for s in syms).replace(tzinfo=timezone.utc)
    end = min(last, max(datetime.strptime(max(kl[s]), fmt) for s in syms).replace(tzinfo=timezone.utc) + timedelta(hours=1))
    n = int((end - first).total_seconds() // 3600)
    times = [first + timedelta(hours=i) for i in range(n)]
    ret = np.full((n, len(syms)), np.nan)
    aux = {}
    for j, s in enumerate(syms):
        close, q = np.full(n, np.nan), np.full(n, np.nan)
        for i, t in enumerate(times):
            k = t.strftime(fmt)
            if k in kl[s] and kl[s][k][1] > 0:
                close[i] = kl[s][k][1]
            if k in oi[s] and oi[s][k] > 0:
                q[i] = oi[s][k]
        ok = np.isfinite(close)
        rows = np.nonzero(ok)[0]
        ret[rows[1:], j] = close[rows[1:]] / close[rows[:-1]] - 1.0
        with np.errstate(invalid="ignore", divide="ignore"):
            d = np.log(q[1:] / q[:-1])  # the change over hour i - 1, known at hour i's start
        aux[f"{s}.d_oi"] = np.concatenate([[np.nan], d])
    return Panel("crypto-binance-usdtm", times, syms, ret, aux, {s: cost for s in syms}, 24.0 * 365.0)


def synthetic(rows: int = 4000, assets: int = 3, seed: int = 0, plant: dict | None = None, cost: float = 0.0002,
              start: date = date(2000, 1, 3)) -> Panel:
    """A built market: a common factor, each instrument's own noise, volatility that clusters, and one state series
    that is pure noise. `plant` adds a structure of known size to instrument A1's next-row return:

        {"leadlag": ic}      A0's last return moves A1's next one: a correlation of about `ic`
        {"ushape": a}        a large move of A0 in EITHER direction lifts A1's next return: no linear correlation
        {"regime": drift}    a persistent hidden state, visible in the series "state", adds +/- drift to A1 each row
        {"shock": a}         after a row in which every instrument moves hard, A1 reverses its own move
    """
    rng = np.random.default_rng(seed)
    plant = plant or {}
    vol = np.empty(rows)
    v = 1.0
    shocks = rng.standard_normal(rows)
    for t in range(rows):  # one volatility process for the market
        vol[t] = math.sqrt(v)
        v = 0.05 + 0.85 * v + 0.10 * v * shocks[t] ** 2
    sig = 0.012
    factor = rng.standard_normal(rows) * vol
    e = rng.standard_normal((rows, assets))
    r = sig * (0.5 * factor[:, None] + e * vol[:, None])
    state = np.zeros(rows)
    s = 1.0
    for t in range(rows):
        if rng.random() < 0.02:
            s = -s
        state[t] = s
    seen = state + rng.standard_normal(rows) * 0.5
    add = np.zeros(rows)
    z0 = r[:, 0] / (sig * vol * math.sqrt(1.25))
    if "leadlag" in plant:
        add[1:] += plant["leadlag"] * sig * vol[1:] * z0[:-1]
    if "ushape" in plant:
        add[1:] += plant["ushape"] * sig * vol[1:] * (np.abs(z0[:-1]) - math.sqrt(2 / math.pi))
    if "regime" in plant:
        add[1:] += plant["regime"] * sig * state[:-1]
    if "shock" in plant:
        big = (np.abs(r / (sig * vol[:, None])) > 1.5).all(axis=1)
        add[1:] -= plant["shock"] * np.where(big[:-1], r[:-1, 1], 0.0)
    r[:, 1] += add
    days, d = [], start
    while len(days) < rows:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    names = tuple(f"A{i}" for i in range(assets))
    return Panel("synthetic", days, names, np.expm1(r), {"state": seen if "regime" in plant else rng.standard_normal(rows)},
                 {n: cost for n in names}, 252.0)


def closed(p: Panel) -> list[tuple[str, dict]]:
    """The families the record has already judged on this panel's market, each as a rule: a discovery that behaves
    like one of them is that family under another name (docs/DISCOVERY_PROGRAM.md, closed families)."""
    out = []
    for a in p.assets:
        if f"{a}.s23" in p.aux:
            out.append((f"ENG-1 (hold {a} while its curve is backwardated)",
                        {"kind": "level", "target": a, "feat": {"f": "aux", "name": f"{a}.s23"}, "op": ">", "x": 0.0,
                         "side": 1}))
        if f"{a}.d_oi" in p.aux:
            out.append((f"LIQ-1 (buy {a} after its open interest and price collapse together)",
                        {"kind": "tree", "target": a, "side": 1, "hold": 24, "node": {"and": [
                            {"feat": {"f": "ret", "a": a, "k": 1}, "w": 2160, "op": "<", "q": 0.01},
                            {"feat": {"f": "aux", "name": f"{a}.d_oi"}, "w": 2160, "op": "<", "q": 0.01}]}}))
        year = int(round(p.ppy))
        for k, label in ((year, "12-month"), (year // 2, "6-month")):
            out.append((f"trend following (hold {a} while its {label} return is positive: DIV-2, XTS-1)",
                        {"kind": "level", "target": a, "feat": {"f": "ret", "a": a, "k": k}, "op": ">", "x": 0.0,
                         "side": 1}))
    return out


HINTS = {
    "energy-futures-eia": "Brent, gasoil and the complete heating-oil and RBOB curves (from 2007), then the metals' and "
                          "grains' curves, are independent instruments for the same mechanism",
    "crypto-binance-usdtm": "the next eight most liquid USDT-M perpetuals, and the hours from 2024-01 (unfetched)",
}

__all__ = ["ENERGY", "HINTS", "WINDOWS", "closed", "crypto_hourly", "energy", "synthetic"]
