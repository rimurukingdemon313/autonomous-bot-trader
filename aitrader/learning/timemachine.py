"""The time machine (dual-ai 1.16.0): a trade's levels replayed against the pair's own recent hours before it is taken.

The owner shared the day-trader-skill's /trader-timemachine on 2026-11-02 ("replays every possible outcome of a trade
before you risk a dollar"). This is that idea for the desk's H1 trades:

- the pool: the pair's completed H1 bars of the last LOOKBACK_H hours, each as four ratios to the close before it (open,
  high, low, close). A bar after a gap (a weekend, a missing hour) is left out: its jump is not an hour's move;
- one replay: from the entry, each hour of the trade's life is a bar drawn at random from the pool's bars of the same
  hour of day (plus or minus WINDOW_H), scaled to the price reached. The stop is checked first, then the target: a bar
  touching both is a stop, and a bar opening through the stop fills at its open. What is still open at the time exit
  closes at that hour's close;
- REPLAYS of them answer how often the target comes first, the stop first, or neither; the average R before and after
  costs; and one verdict: of the replays that reached a side, how often it was the target, against the win rate the
  levels need to pay their costs, (1 + c) / (1 + R).

It is a simulation of the pair's recent past, never a forecast. It says whether the levels are reachable in the time
given and how the recent drift leans; it cannot say whether the traders' reading is right. Nothing here refuses or
sizes a trade: it is recorded and measured (dual_ai_stats.analysis reads its verdict as a condition), and becomes a
rule only if the desk's own record ever shows that it should.

Deterministic: the same bars, levels and seed give the same numbers. Only bars completed by `as_of` are read.
"""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

TIME_MACHINE_VERSION = "time-machine-1.0.0"
REPLAYS = 10_000
LOOKBACK_H = 60 * 24      # sixty days of hours
WINDOW_H = 1              # the same hour of day, plus or minus one
MIN_POOL = 200            # fewer usable bars than this: no replay, never a guess
#: verdict thresholds, in points of the target's share of the replays that reached a side, against the win rate needed
CLOSE, STRONG = 0.05, 0.15
FAN_EVERY = 2             # the fan chart keeps every second hour's percentiles


def verdict(share: float | None, needed: float) -> str:
    if share is None:
        return "no replay reached a side"
    d = share - needed
    if abs(d) < CLOSE:
        return "close to break-even"
    side = "the target" if d > 0 else "the stop"
    return f"{'strongly toward' if abs(d) >= STRONG else 'leans toward'} {side}"


def replay(bars, *, as_of: int, entry: float, stop: float, target: float, hold_minutes: int, cost: float = 0.0,
           replays: int = REPLAYS, seed: int = 19) -> dict | None:
    """The levels replayed `replays` times from `bars` (H1, as of `as_of`); None when there is too little to replay."""
    risk = abs(entry - stop)
    side = 1 if target > entry else -1
    if not risk > 0 or (stop - entry) * side >= 0 or (target - entry) * side <= 0:
        return None
    b = bars.as_of(int(as_of))
    t = np.asarray(b.open_time, np.int64)[-LOOKBACK_H - 1:]
    o, h, lo, c = (np.asarray(x, float)[-LOOKBACK_H - 1:] for x in (b.mid_open, b.mid_high, b.mid_low, b.mid_close))
    if len(t) < 2:
        return None
    ok = (np.diff(t) == 3600) & (c[:-1] > 0)
    prev = c[:-1][ok]
    ro, rh, rl, rc = o[1:][ok] / prev, h[1:][ok] / prev, lo[1:][ok] / prev, c[1:][ok] / prev
    hour = ((t[1:][ok] // 3600) % 24).astype(int)
    if len(prev) < MIN_POOL:
        return None
    steps = max(1, int(hold_minutes) // 60)
    first_hour = int(as_of // 3600) % 24
    pools = {}
    for hh in range(24):
        near = np.minimum(np.abs(hour - hh), 24 - np.abs(hour - hh)) <= WINDOW_H
        pools[hh] = np.flatnonzero(near) if near.any() else np.arange(len(hour))
    rng = np.random.default_rng(int(seed))
    p = np.full(replays, float(entry))
    state = np.zeros(replays, np.int8)   # 0 open, 1 target first, -1 stop first
    r = np.zeros(replays)
    rr = abs(target - entry) / risk
    fan = []
    for k in range(steps):
        j = rng.choice(pools[(first_hour + k) % 24], size=replays)
        bo, bh, bl, bc = p * ro[j], p * rh[j], p * rl[j], p * rc[j]
        live = state == 0
        if side > 0:
            hit_s = live & (bl <= stop)
            hit_t = live & ~hit_s & (bh >= target)
            gap = bo <= stop
        else:
            hit_s = live & (bh >= stop)
            hit_t = live & ~hit_s & (bl <= target)
            gap = bo >= stop
        r[hit_s] = np.where(gap, (bo - entry) * side / risk, -1.0)[hit_s]
        r[hit_t] = rr
        state[hit_s], state[hit_t] = -1, 1
        p = bc
        if k % FAN_EVERY == FAN_EVERY - 1 or k == steps - 1:
            fan.append([k + 1, *np.round(np.percentile(p, [5, 25, 50, 75, 95]), 6).tolist()])
    still = state == 0
    r[still] = (p[still] - entry) * side / risk
    cost_r = max(0.0, float(cost)) / risk
    pt, ps, pn = float(np.mean(state == 1)), float(np.mean(state == -1)), float(np.mean(still))
    share = pt / (pt + ps) if pt + ps > 0 else None
    need = (1 + cost_r) / (1 + rr)
    iso = lambda x: datetime.fromtimestamp(int(x), timezone.utc).strftime("%Y-%m-%d")  # noqa: E731
    return {"version": TIME_MACHINE_VERSION, "replays": int(replays), "hours": steps, "seed": int(seed),
            "side": "BUY" if side > 0 else "SELL", "entry": float(entry), "stop": float(stop), "target": float(target),
            "reward_risk": round(rr, 3), "target_first": round(pt, 4), "stop_first": round(ps, 4),
            "neither": round(pn, 4), "target_share_of_decided": None if share is None else round(share, 4),
            "win_rate_needed": round(need, 4), "mean_r": round(float(r.mean()), 4),
            "mean_r_after_costs": round(float(r.mean()) - cost_r, 4), "verdict": verdict(share, need),
            "fan": {"columns": ["hour", "p05", "p25", "p50", "p75", "p95"], "rows": fan},
            "based_on": f"{len(prev)} H1 bars, {iso(t[0])} to {iso(t[-1])}, each hour drawn from the same hour of day "
                        f"plus or minus {WINDOW_H}; a simulation of the recent past, not a forecast"}


__all__ = ["REPLAYS", "TIME_MACHINE_VERSION", "replay", "verdict"]
