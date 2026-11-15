"""BAS-1: does the arbitrage that high funding attracts lift the spot price? (research/preregistrations/BAS-1.md)

When a perpetual's funding stays high, its longs pay its shorts to keep leveraged long positions. That payment is
what cash-and-carry capital earns by buying the coin's spot and shorting its perpetual, so high funding draws
arbitrage capital whose first leg is a spot purchase; and the leveraged demand that made funding high is itself
trend-following. Both push the coin's spot up against the market while funding stays high. The opposite force is
crash risk: crowded longs end in liquidations (Schmeling, Schrimpf & Todorov's "crypto carry" is positively skewed
and crash-prone).

The rule is SQZ-1's on the other tail: at 00:00 UTC of day d, if the funding settled over the 72 hours before is at
least +theta per 8 hours, buy the coin's SPOT at the close of d-1 and sell it at the close of d+6. One position per
coin at a time; each trade against the equal-weight spot return of every seasoned coin. The signal, the benchmark,
the statistic and the gates are SQZ-1's code (aitrader/research/events/squeeze.py), unchanged. Nothing here trades.
"""

from __future__ import annotations

from aitrader.research.events import squeeze as Q

BAS_VERSION = "bas-1.0.0"


def events(fund: dict[str, Q.Funding], spot: dict[str, dict[str, float]], seasoned: dict[str, str], bench: Q.Bench,
           first: str, last: str, theta: float, cost: float, hold: int = 7, lag: int = 0) -> list[dict]:
    """Every entry the rule takes in [first, last] when the signal is at least +theta: entry at the close of day
    d-1+lag, exit `hold` days later; a coin held once at a time; an entry without a close counted, never filled."""
    out = []
    for c in sorted(fund):
        if c not in spot or c not in seasoned:
            continue
        busy_until, d = "", first
        while d <= last:
            if d >= seasoned[c] and d > busy_until:
                f = fund[c].signal(Q.day_ms(d))
                if f is not None and f >= theta:
                    a, b = Q.plus(d, -1 + lag), Q.plus(d, -1 + lag + hold)
                    r, m = Q.ret(spot[c], a, b), bench(a, b)
                    e = {"coin": c, "day": d, "signal": f, "entry": a, "exit": b}
                    if r is None or m is None:
                        e["missing"] = True
                    else:
                        e.update(ret=r, bench=m, net=r - 2 * cost, excess=r - 2 * cost - m)
                    out.append(e)
                    busy_until = Q.plus(d, hold - 1)
            d = Q.plus(d, 1)
    return out


def placebos(fund: dict[str, Q.Funding], spot: dict[str, dict[str, float]], seasoned: dict[str, str], bench: Q.Bench,
             evs: list[dict], theta: float, cost: float, hold: int = 7, span: int = 30) -> dict[tuple[str, str], list[float]]:
    """For each traded entry, the same coin's excess over the same holding from every day within `span` days on
    which its funding was not high (signal below theta/2): what the coin did without the signal."""
    out = {}
    for e in evs:
        if e.get("missing"):
            continue
        c, xs = e["coin"], []
        for k in range(-span, span + 1):
            d = Q.plus(e["day"], k)
            if abs(k) < hold or d < seasoned[c]:
                continue
            f = fund[c].signal(Q.day_ms(d))
            if f is None or f >= theta / 2:
                continue
            a, b = Q.plus(d, -1), Q.plus(d, hold - 1)
            r, m = Q.ret(spot[c], a, b), bench(a, b)
            if r is not None and m is not None:
                xs.append(r - 2 * cost - m)
        out[(c, e["day"])] = xs
    return out
