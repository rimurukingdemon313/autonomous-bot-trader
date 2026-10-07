"""The funding radar's decision and paper-ledger logic (pure functions; the clock is always passed in).

Every run (hourly):

1. append the venues' current quotes to a rolling history (only the radar's own past observations are used for
   decisions: nothing is back-filled, nothing is looked up after the fact);
2. mark every open paper position: funding accrues at the average of the previous and current snapshot rates of
   each leg over the elapsed hours (a declared approximation of the settlements), price P&L from the legs' marks;
3. close positions whose 24-hour trailing spread has decayed, whose spread has turned against them, that are 30
   days old, whose legs moved 25% (margin must be rebalanced: closed, may reopen), or whose venue has been
   missing for 24 hours;
4. open new positions where the 72-hour trailing spread between two venues for the same coin is wide enough and
   the current spread confirms it, on liquid contracts whose prices agree (a different token listed under the
   same ticker shows up as a price mismatch and is refused).

A position is short the perpetual on the venue paying more funding and long it on the other: market-neutral on
one coin. P&L is in bp of the notional N of each leg; capital is 2N (1x margin on each venue).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from itertools import permutations

import numpy as np

from .venues import TAKER_BP, Quote

RADAR_VERSION = "radar-1.0.0"
HOUR = 3600
YEAR_H = 8760


@dataclass(frozen=True)
class Rules:
    entry_trailing_apr: float = 0.25  # 72 h mean spread, annualised
    entry_now_apr: float = 0.15
    exit_trailing_apr: float = 0.05  # 24 h mean spread
    exit_now_apr: float = -0.10
    min_vol_usd: float = 10e6  # 24 h traded notional on BOTH venues
    max_price_gap: float = 0.02
    max_open: int = 10
    max_age_days: float = 30.0
    rebalance_move: float = 0.25
    venue_missing_h: float = 24.0
    slip_bp: float = 5.0  # half-spread + slippage per fill (declared)
    trailing_entry_h: int = 72
    trailing_exit_h: int = 24
    min_coverage: float = 0.8  # share of hourly snapshots required in a trailing window


@dataclass
class Position:
    id: str
    coin: str
    short_venue: str
    long_venue: str
    opened: int
    short_px0: float
    long_px0: float
    last_t: int
    short_rate_last: float
    long_rate_last: float
    short_px: float
    long_px: float
    funding_bp: float = 0.0
    cost_bp: float = 0.0
    entry_spread_apr: float = 0.0
    closed: int | None = None
    reason: str | None = None
    missing_since: int | None = None

    @property
    def basis_bp(self) -> float:
        return ((self.long_px / self.long_px0 - 1) - (self.short_px / self.short_px0 - 1)) * 1e4

    @property
    def net_bp(self) -> float:
        return self.funding_bp + self.basis_bp - self.cost_bp


@dataclass
class State:
    history: list[dict] = field(default_factory=list)  # {"t","venue","coin","scale","rate","mark","vol"}
    open: list[Position] = field(default_factory=list)
    closed: list[Position] = field(default_factory=list)
    marks: list[dict] = field(default_factory=list)  # {"t", "pnl_bp_total"} mark-to-market of the whole book
    runs: int = 0
    venue_errors: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        return {"version": RADAR_VERSION, "history": self.history, "open": [asdict(p) for p in self.open],
                "closed": [asdict(p) for p in self.closed], "marks": self.marks, "runs": self.runs,
                "venue_errors": self.venue_errors}

    @classmethod
    def from_json(cls, d: dict) -> "State":
        return cls(d.get("history", []), [Position(**p) for p in d.get("open", [])],
                   [Position(**p) for p in d.get("closed", [])], d.get("marks", []), d.get("runs", 0),
                   d.get("venue_errors", {}))


def fill_cost_bp(venue: str, rules: Rules) -> float:
    return TAKER_BP[venue] + rules.slip_bp


HistIndex = dict[tuple[str, str], list[tuple[int, float]]]


def index_history(history: list[dict]) -> HistIndex:
    idx: HistIndex = {}
    for h in history:
        idx.setdefault((h["venue"], h["coin"]), []).append((h["t"], h["rate"]))
    for v in idx.values():
        v.sort()
    return idx


def trailing(history: list[dict] | HistIndex, venue: str, coin: str, now: int, hours: int, min_cov: float
             ) -> float | None:
    """Mean per-hour rate of the radar's own snapshots in (now - hours, now]. None unless the radar has watched this
    venue and coin for the whole window (first snapshot at least hours - 1 ago) and holds >= min_cov of its hourly
    snapshots: a short history is never read as a full one."""
    idx = history if isinstance(history, dict) else index_history(history)
    mine = [(t, r) for t, r in idx.get((venue, coin), []) if t <= now]
    if not mine or mine[0][0] > now - (hours - 1) * HOUR:
        return None
    xs = [r for t, r in mine if now - hours * HOUR < t]
    return float(np.mean(xs)) if len(xs) >= min_cov * hours else None


def _index(quotes: list[Quote]) -> dict[tuple[str, str], Quote]:
    out: dict[tuple[str, str], Quote] = {}
    for q in quotes:
        k = (q.venue, q.coin)
        if k not in out or q.vol24_usd > out[k].vol24_usd:  # one contract per venue and coin: the most traded
            out[k] = q
    return out


def prices_agree(a: Quote, b: Quote, tol: float) -> bool:
    pa, pb = a.mark / a.scale, b.mark / b.scale
    return pa > 0 and pb > 0 and abs(pa / pb - 1) <= tol


def opportunities(quotes: list[Quote], history: list[dict], now: int, rules: Rules) -> list[dict]:
    """Every (coin, short venue, long venue) whose trailing and current spreads pass the entry rule, best first."""
    idx = _index(quotes)
    hidx = index_history(history)
    coins: dict[str, list[Quote]] = {}
    for q in idx.values():
        coins.setdefault(q.coin, []).append(q)
    out = []
    for coin, qs in coins.items():
        liquid = [q for q in qs if q.vol24_usd >= rules.min_vol_usd]
        for a, b in permutations(liquid, 2):  # a = short (pays more), b = long
            if not prices_agree(a, b, rules.max_price_gap):
                continue
            ta = trailing(hidx, a.venue, coin, now, rules.trailing_entry_h, rules.min_coverage)
            tb = trailing(hidx, b.venue, coin, now, rules.trailing_entry_h, rules.min_coverage)
            if ta is None or tb is None:
                continue
            s_trail, s_now = (ta - tb) * YEAR_H, (a.rate_per_hour - b.rate_per_hour) * YEAR_H
            if s_trail >= rules.entry_trailing_apr and s_now >= rules.entry_now_apr:
                out.append({"coin": coin, "short": a.venue, "long": b.venue, "trail_apr": s_trail, "now_apr": s_now,
                            "short_q": a, "long_q": b})
    best: dict[str, dict] = {}
    for o in sorted(out, key=lambda o: -o["trail_apr"]):
        best.setdefault(o["coin"], o)
    return sorted(best.values(), key=lambda o: -o["trail_apr"])


def step(state: State, quotes: list[Quote], errors: dict, now: int, rules: Rules = Rules(),
         keep_history_h: int = 240) -> State:
    """One radar run at time `now`. Mutates and returns `state`."""
    state.runs += 1
    state.venue_errors = errors
    for q in quotes:
        state.history.append({"t": now, "venue": q.venue, "coin": q.coin, "scale": q.scale, "rate": q.rate_per_hour,
                              "mark": q.mark, "vol": q.vol24_usd})
    state.history = [h for h in state.history if h["t"] > now - keep_history_h * HOUR]
    idx = _index(quotes)
    hidx = index_history(state.history)
    still = []
    for p in state.open:
        s, lq = idx.get((p.short_venue, p.coin)), idx.get((p.long_venue, p.coin))
        if s is None or lq is None:
            p.missing_since = p.missing_since or now
            if now - p.missing_since >= rules.venue_missing_h * HOUR:
                _close(p, now, "venue_unavailable", rules)
                state.closed.append(p)
            else:
                still.append(p)
            continue
        p.missing_since = None
        h = (now - p.last_t) / HOUR
        p.funding_bp += ((p.short_rate_last + s.rate_per_hour) / 2 - (p.long_rate_last + lq.rate_per_hour) / 2) * h * 1e4
        p.short_rate_last, p.long_rate_last, p.last_t = s.rate_per_hour, lq.rate_per_hour, now
        p.short_px, p.long_px = s.mark, lq.mark
        ts = trailing(hidx, p.short_venue, p.coin, now, rules.trailing_exit_h, rules.min_coverage)
        tl = trailing(hidx, p.long_venue, p.coin, now, rules.trailing_exit_h, rules.min_coverage)
        trail = (ts - tl) * YEAR_H if ts is not None and tl is not None else None
        now_apr = (s.rate_per_hour - lq.rate_per_hour) * YEAR_H
        moved = max(abs(p.short_px / p.short_px0 - 1), abs(p.long_px / p.long_px0 - 1)) >= rules.rebalance_move
        reason = ("spread_decayed" if trail is not None and trail < rules.exit_trailing_apr else
                  "spread_reversed" if now_apr < rules.exit_now_apr else
                  "max_age" if now - p.opened >= rules.max_age_days * 86400 else
                  "rebalance" if moved else None)
        if reason:
            _close(p, now, reason, rules)
            state.closed.append(p)
        else:
            still.append(p)
    state.open = still
    held = {p.coin for p in state.open}
    for o in opportunities(quotes, state.history, now, rules):
        if len(state.open) >= rules.max_open:
            break
        if o["coin"] in held:
            continue
        a, b = o["short_q"], o["long_q"]
        p = Position(f"{o['coin']}-{a.venue}-{b.venue}-{now}", o["coin"], a.venue, b.venue, now, a.mark, b.mark, now,
                     a.rate_per_hour, b.rate_per_hour, a.mark, b.mark,
                     cost_bp=fill_cost_bp(a.venue, rules) + fill_cost_bp(b.venue, rules),
                     entry_spread_apr=o["trail_apr"])
        state.open.append(p)
        held.add(o["coin"])
    total = sum(p.net_bp for p in state.open) + sum(p.net_bp for p in state.closed)
    state.marks.append({"t": now, "pnl_bp_total": round(total, 4), "open": len(state.open)})
    return state


def _close(p: Position, now: int, reason: str, rules: Rules) -> None:
    p.cost_bp += fill_cost_bp(p.short_venue, rules) + fill_cost_bp(p.long_venue, rules)
    p.closed, p.reason = now, reason


def performance(state: State, rules: Rules, rf_apr: float) -> dict:
    """The book against cash (research/preregistrations/RADAR-1.md).

    Capital is 2N per slot x max_open slots (1x margin on each leg). Idle capital is assumed to earn the risk-free
    rate, so EXCESS is what the radar adds: each position's net P&L minus the risk-free rate on its 2N for the time
    it was open. Open positions are valued as if closed now (their closing fills are charged). Totals come from the
    positions; the daily series (t-statistic) and the drawdown come from the hourly marks."""
    if len(state.marks) < 2:
        return {"days": 0}
    t = np.array([m["t"] for m in state.marks], dtype=float)
    pnl = np.array([m["pnl_bp_total"] for m in state.marks]) / 1e4  # in units of N
    n_open = np.array([m.get("open", 0) for m in state.marks], dtype=float)
    cap = 2.0 * rules.max_open
    dt_y = np.diff(t) / (YEAR_H * HOUR)
    exc_inc = np.diff(pnl) - rf_apr * 2 * n_open[:-1] * dt_y
    _, inv = np.unique(t[1:] // 86400, return_inverse=True)
    daily = np.bincount(inv, weights=exc_inc) / cap
    span_y = (t[-1] - t[0]) / (YEAR_H * HOUR)
    last = int(t[-1])
    by_coin: dict[str, float] = {}
    tot_exc = tot_cost = tot_cap_y = 0.0
    for p in state.closed + state.open:
        close_cost = 0.0 if p.closed is not None else fill_cost_bp(p.short_venue, rules) + fill_cost_bp(p.long_venue, rules)
        dur_y = ((p.closed if p.closed is not None else last) - p.opened) / (YEAR_H * HOUR)
        e = (p.net_bp - close_cost) / 1e4 - rf_apr * 2 * dur_y
        by_coin[p.coin] = by_coin.get(p.coin, 0.0) + e
        tot_exc += e
        tot_cost += (p.cost_bp + close_cost) / 1e4
        tot_cap_y += 2 * dur_y
    best = max(by_coin, key=by_coin.get) if by_coin else None
    cum = np.r_[0.0, pnl / cap]
    out = {"days": round(float(span_y * 365), 2),
           "run_coverage": round(len(np.unique(t)) / ((t[-1] - t[0]) / HOUR + 1), 4),
           "closed_positions": len(state.closed), "open_positions": len(state.open),
           "utilisation": round(float(np.mean(n_open) / rules.max_open), 4),
           "rf_apr_pct_declared": round(rf_apr * 100, 3),
           "book_pnl_pct": round(float(pnl[-1] / cap * 100), 4),
           "book_excess_pct": round(tot_exc / cap * 100, 4),
           "ann_excess_deployed_pct": round(tot_exc / tot_cap_y * 100, 3) if tot_cap_y > 0 else None,
           "ann_excess_deployed_costs_x1.5_pct": round((tot_exc - 0.5 * tot_cost) / tot_cap_y * 100, 3) if tot_cap_y > 0 else None,
           "ann_excess_deployed_costs_x2_pct": round((tot_exc - tot_cost) / tot_cap_y * 100, 3) if tot_cap_y > 0 else None,
           "best_coin": best,
           "book_excess_without_best_coin_pct": round((tot_exc - by_coin[best]) / cap * 100, 4) if best else None,
           "max_dd_pct": round(float(np.max(np.maximum.accumulate(cum) - cum) * 100), 4)}
    if len(daily) >= 2 and daily.std(ddof=1) > 0:
        out["t_excess_daily"] = round(float(daily.mean() / (daily.std(ddof=1) / np.sqrt(len(daily)))), 3)
    return out


#: The forward test's single verdict (research/preregistrations/RADAR-1.md). Frozen with the preregistration.
FORWARD = {"look_days": 60.0, "extend_days": 120.0, "min_closed": 30, "min_ann_excess_deployed_pct": 10.0,
           "min_t": 2.0, "min_t_extended": 2.5, "max_dd_pct": 10.0, "min_run_coverage": 0.9}


def forward_verdict(perf: dict, extended: bool = False) -> tuple[str, dict]:
    """WAIT before the look; at the look, INCONCLUSIVE if too few positions closed (one extension allowed, with a
    stricter t), else PASSED only if every gate holds, FAILED otherwise. Missing figures fail their gate."""
    f = FORWARD
    if perf.get("days", 0) < (f["extend_days"] if extended else f["look_days"]):
        return "WAIT", {}
    if perf.get("closed_positions", 0) < f["min_closed"]:
        return "INCONCLUSIVE", {"closed_positions": False}

    def has(k):
        return perf.get(k) is not None

    gates = {"ann_excess_deployed": has("ann_excess_deployed_pct")
             and perf["ann_excess_deployed_pct"] >= f["min_ann_excess_deployed_pct"],
             "t_excess_daily": has("t_excess_daily")
             and perf["t_excess_daily"] >= (f["min_t_extended"] if extended else f["min_t"]),
             "costs_x1.5": has("ann_excess_deployed_costs_x1.5_pct") and perf["ann_excess_deployed_costs_x1.5_pct"] > 0,
             "without_best_coin": has("book_excess_without_best_coin_pct") and perf["book_excess_without_best_coin_pct"] > 0,
             "max_dd": has("max_dd_pct") and perf["max_dd_pct"] <= f["max_dd_pct"],
             "run_coverage": has("run_coverage") and perf["run_coverage"] >= f["min_run_coverage"]}
    return ("PASSED" if all(gates.values()) else "FAILED"), gates


__all__ = ["FORWARD", "RADAR_VERSION", "Position", "Rules", "State", "forward_verdict", "index_history",
           "opportunities", "performance", "prices_agree", "step", "trailing"]
