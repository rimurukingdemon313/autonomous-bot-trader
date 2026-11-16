"""SPL-1: does a rally that spot buyers led keep going? (research/preregistrations/SPL-1.md)

A coin's price can be pushed up by two kinds of buyer. Leveraged buyers bid its perpetual: the perpetual trades at a
premium to spot and arbitrageurs carry the premium into spot. Their demand is borrowed and comes back out when the
positions are closed or liquidated; this record found that coins under such leverage do worse than the market for
days to weeks (SQZ-1, BAS-1, CASC-1). Spot buyers pay in full and owe nothing: a rise they lead, with the perpetual
no richer than spot, is demand that does not have to be unwound, and the slower holders it draws in should carry it
further. The opposite force is that spot-led pumps of thin coins are often coordinated and dumped within hours.

The rule decides at the close of hour h: if a seasoned coin's spot rose at least X over the last four hours, and at
no close of those hours did its perpetual stand more than 0.25% above spot, buy the coin's SPOT at that close and
sell 24 hours later. One position per coin at a time. It is judged on the trade's own net return (CASC-1's judge,
unchanged), and it must also beat the market over the same hours, the same coin at hours it had not risen, and the
rallies the perpetual led. Nothing here trades.
"""

from __future__ import annotations

import random

import numpy as np

from aitrader.research.events import cascade as K

SPL_VERSION = "spl-1.0.0"
LOOK, HOLD, HOUR = K.LOOK, K.HOLD, K.HOUR


def _rises(p: K.Panel, k: int, first: int, last: int, rise: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The decision hours in [first, last] at which coin k's spot had risen at least `rise` over LOOK hours, with
    the perpetual's premium to spot at that hour and its largest premium over the LOOK + 1 closes of the rise
    (NaN where a close is missing)."""
    S, P = p.spot[k], p.perp[k]
    lo, hi = max(first, LOOK, int(p.s[k])), min(last, p.n - 1)
    if hi < lo:
        return np.array([], dtype=int), np.array([]), np.array([])
    hs = np.arange(lo, hi + 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        r4 = S[hs] / S[hs - LOOK] - 1
        prem = P / S - 1
    ok = np.isfinite(r4) & (r4 >= rise)
    hs = hs[ok]
    now = prem[hs] if len(hs) else np.array([])
    win = np.array([np.max(prem[h - LOOK:h + 1]) if np.all(np.isfinite(prem[h - LOOK:h + 1])) else np.nan for h in hs])
    return hs, now, win


def _trade(p: K.Panel, k: int, c: str, h: int, lag: int, cost: float) -> dict:
    S = p.spot[k]
    a, b = h + lag, h + lag + HOLD
    e = {"coin": c, "hour": h, "rise": float(S[h] / S[h - LOOK] - 1)}
    if b >= p.n or not (np.isfinite(S[a]) and np.isfinite(S[b])) or p.market(a, b) is None:
        return {**e, "missing": True}
    r = float(S[b] / S[a] - 1)
    return {**e, "ret": r, "bench": p.market(a, b), "net": r - 2 * cost, "excess": r - 2 * cost - p.market(a, b)}


def events(p: K.Panel, first: int, last: int, rise: float, prem: float, cost: float, lag: int = 0) -> list[dict]:
    """Every entry the rule takes with its decision hour in [first, last]: a rise of at least `rise` during which no
    close put the perpetual more than prem / 2 above spot. Entry at the close of the decision hour plus `lag`, exit
    HOLD hours later; one position per coin at a time; an entry without a close at either end is counted, never
    filled."""
    out = []
    for k, c in enumerate(p.coins):
        hs, _, win = _rises(p, k, first, last, rise)
        busy = -1
        for h, w in zip(hs.tolist(), win.tolist()):
            if h <= busy or not np.isfinite(w) or w > prem / 2:
                continue
            out.append(_trade(p, k, c, h, lag, cost))
            busy = h + HOLD - 1
    return out


def contrast(p: K.Panel, first: int, last: int, rise: float, prem: float, cost: float) -> list[dict]:
    """The same rises led by the perpetual: at the decision hour it stood at least `prem` above spot. What the
    mechanism says should NOT keep going, measured the same way."""
    out = []
    for k, c in enumerate(p.coins):
        hs, now, _ = _rises(p, k, first, last, rise)
        busy = -1
        for h, x in zip(hs.tolist(), now.tolist()):
            if h <= busy or not np.isfinite(x) or x < prem:
                continue
            e = _trade(p, k, c, h, 0, cost)
            if not e.get("missing"):
                out.append(e)
                busy = h + HOLD - 1
    return out


def placebo_hours(p: K.Panel, k: int, h: int, rise: float, span: int = 168) -> list[int]:
    """The hours a placebo of the entry at hour h of coin k may start at: within `span` on either side, at least
    HOLD away, with both closes of the hold, and without a rise (four-hour return below rise / 3)."""
    S = p.spot[k]
    return [x for x in range(max(LOOK, int(p.s[k]), h - span), min(p.n - 1 - HOLD, h + span) + 1)
            if abs(x - h) >= HOLD and np.isfinite(S[x]) and np.isfinite(S[x - LOOK]) and np.isfinite(S[x + HOLD])
            and S[x] / S[x - LOOK] - 1 < rise / 3]


def placebos(p: K.Panel, evs: list[dict], rise: float, cost: float, span: int = 168, draws: int = 40,
             seed: int = 20261116) -> dict[tuple[str, int], list[float]]:
    """For each traded entry, the same coin's 24-hour net return from up to `draws` random hours of placebo_hours:
    what the coin did over the same hold without a rally behind it."""
    rng, out = random.Random(seed), {}
    for e in evs:
        if e.get("missing"):
            continue
        k, h = p.idx[e["coin"]], e["hour"]
        S = p.spot[k]
        cand = placebo_hours(p, k, h, rise, span)
        out[(e["coin"], h)] = [float(S[x + HOLD] / S[x] - 1) - 2 * cost for x in rng.sample(cand, min(draws, len(cand)))]
    return out


def judge(p: K.Panel, evs: list[dict], late: list[dict], contra: list[dict], plac: dict, bar: float, cost: float,
          min_events: int, min_days: int, seed: int = 20261116, draws: int = 1000, lag: int = 1) -> dict:
    """CASC-1's judge, unchanged, with its contrast read as the perpetual-led rallies; and one gate more: the entries
    must beat the market over the same hours (their mean excess > 0)."""
    r = K.judge(p, evs, late, contra, plac, bar, cost, min_events, min_days, seed, draws, lag)
    if r["verdict"] == "INCONCLUSIVE":
        return r
    g = dict(r["gates"])
    g["beats_leverage_led_rallies"] = g.pop("beats_spot_led_falls")
    ex = r.get("mean_excess_vs_market")
    g["beats_market"] = ex is not None and ex > 0
    out = {k: v for k, v in r.items() if k not in ("spot_led_falls", "spot_led_mean_net")}
    return {**out, "gates": g, "verdict": "PASSED" if all(g.values()) else "FAILED",
            "leverage_led_rallies": r["spot_led_falls"], "leverage_led_mean_net": r["spot_led_mean_net"]}
