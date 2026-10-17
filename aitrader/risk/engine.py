"""The deterministic risk engine: final authority, only source of size.

The AI proposes; this decides whether anything is sent, and at what size
(RISK_CONTRACT.md). Properties, each tested:

- It is the ONLY code that computes a position size or a risk amount.
- Size depends on equity, the stop distance and the limits. It does NOT
  depend on the decision's confidence, expected edge or anything else the
  AI says about itself: a more confident AI cannot buy a bigger position.
- Risk may be reduced by adverse state (loss streak, drawdown) and is never
  increased by it. There is no martingale and no "recover the loss" branch.
- Fail closed: unreadable kill switch, unknown equity, stale or missing
  quote, missing instrument spec -> rejected.
- Every check is recorded, passed or failed, so a rejection names its cause.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from math import floor
from zoneinfo import ZoneInfo

from .profile import HardRiskProfile, loss_per_lot

#: 1.1.0: the cost ceiling counts the WHOLE round trip (spread + commission + slippage on both fills)
#: against the stop, not the spread alone: a 5-pip stop paid ~0.9 pip of commission and slippage
#: that the old check never saw. Evidence: every gross edge measured in this project is below 0.31R
#: and H1 gross edges are within +/-0.03R, so a trade whose costs exceed a quarter of its risk
#: cannot be profitable on anything this system has found (docs/FINAL_ENGINEERING_AUDIT.md).
#: 1.2.0 (takeover audit, docs/TAKEOVER_AUDIT.md):
#:   - per-trade risk is capped at UNVALIDATED_MAX_RISK_PCT (0.25%) while no edge is VALIDATED;
#:     the default is 0.25%;
#:   - a weekly loss limit and a ceiling on the total open risk;
#:   - an unknown start-of-day, start-of-week or peak equity FAILS the check (it used to be replaced by
#:     the current equity, which made the daily-loss and drawdown checks pass);
#:   - flagged market data (stale bars) is a rejection in every decision mode;
#:   - a time-exit trade (exit_kind == "TIME") needs no target, but still needs a protective stop:
#:     without one its loss is unbounded and no size can be computed.
#: 1.3.0 (hard risk gate): with a `hard` profile (the FTMO-style $200K evaluation), the size is computed from
#:   the trade's ALL-IN maximum loss - stop distance from the executable price, round-trip commission, slippage
#:   on both fills, financing allowance - within min(equity x risk%, the profile's fixed risk per trade). So risk
#:   never grows with a winning account, and the size is the one the hard gate will verify. Without a profile,
#:   unchanged.
#: 1.4.0: a profile may set a window either side of the daily rollover (17:00 New York) in which no new position is
#:   opened (PAPER-FORWARD-200K: 60 min). It only ever refuses an entry; sizes and every other check unchanged.
#: 1.5.0: the window is set in New York time from a start to an end (16:00-20:00, an hour before the rollover to the
#:   Tokyo open); 1.4.0's 60 min after the rollover left 18:00-20:00 open.
#: 1.6.0 (live, 2026-10-14): the window is the risk engine's own limit (RiskLimits), set for MODE=PAPER_FORWARD, no
#:   longer a field of the evaluation profile. As a profile field it changed the profile's hash, and the hard gate
#:   (rightly: a profile cannot change during an evaluation) refused every new trade with PROFILE_CHANGED. Trading
#:   hours are a choice of this engine, not a rule of the evaluation; the profile is back to the run's own.
#: 1.7.0: with no_weekend_carry (MODE=PAPER_FORWARD), no new position whose maximum holding time would run past the
#:   Friday close (17:00 New York): the market shuts for two days and reopens where it likes. A decision without a
#:   holding time is taken to hold 48 h. It only ever refuses an entry.
#: 1.8.0 (operator's choice, 2026-10-17): a trading calendar of closed UTC weekdays and closed UTC windows in which no
#:   new position is opened (MODE=PAPER_FORWARD: Friday, like the weekend; and the London/New York overlap, 12:00-16:00
#:   UTC, the session the desk's trades did worst in: 8 trades, -0.38 R). `trade_risk_budget` states the most the next
#:   trade would be sized to lose. It only ever refuses an entry; sizes and every other check unchanged.
RISK_VERSION = "risk-1.8.0"
NEW_YORK = ZoneInfo("America/New_York")
#: MODE=PAPER_FORWARD: no new position from 16:00 to 20:00 New York (an hour before the rollover to the Tokyo open)
PAPER_FORWARD_QUIET_NY = (16 * 60, 20 * 60)
#: MODE=PAPER_FORWARD: no new position on Friday (UTC), as on Saturday and Sunday
PAPER_FORWARD_CLOSED_WEEKDAYS_UTC = (4,)
#: MODE=PAPER_FORWARD: no new position in the London/New York overlap, 12:00-16:00 UTC (as learning.forward.session_of)
PAPER_FORWARD_CLOSED_UTC = ((12 * 60, 16 * 60),)
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

#: No configuration can take per-trade risk above this.
HARD_MAX_RISK_PCT = 1.0
#: While no edge is VALIDATED (research_status.json: none is), no configuration can take per-trade risk
#: above this. Raising it requires a validated edge and a reviewed code change, never an environment variable.
UNVALIDATED_MAX_RISK_PCT = 0.25


@dataclass(frozen=True)
class FundedRules:
    """A funded/prop account's constraints, supplied by the operator. Never guessed."""

    name: str
    daily_loss_pct: float | None = None
    max_loss_pct: float | None = None  # from the starting balance
    trailing_drawdown_pct: float | None = None  # from the equity peak
    max_risk_per_trade_pct: float | None = None
    no_weekend_holding: bool = False
    max_lots: float | None = None


@dataclass(frozen=True)
class RiskLimits:
    risk_per_trade_pct: float = 0.25
    daily_loss_limit_pct: float = 2.0
    weekly_loss_limit_pct: float = 4.0  # from the equity at the start of the ISO week (Monday 00:00 UTC)
    max_open_risk_pct: float = 0.75  # the sum of every open position's risk at its stop, plus the new one
    max_drawdown_pct: float = 8.0
    max_open_positions: int = 3
    max_positions_per_currency: int = 2
    max_leverage: float = 10.0
    max_spread_to_stop: float = 0.25
    #: round-trip cost (spread + commission + 2 x slippage) as a share of the stop distance
    max_cost_to_risk: float = 0.25
    commission_pips_rt: float = 0.7
    slippage_pips: float = 0.1
    min_reward_risk: float = 1.2
    min_stop_spreads: float = 3.0
    max_quote_age_s: int = 30
    loss_streak_step: int = 3  # every N consecutive losses halves risk...
    loss_streak_floor: float = 0.25  # ...down to this multiple
    funded: FundedRules | None = None
    #: the hard risk gate's profile: sizing then budgets the all-in maximum loss (see RISK_VERSION 1.3.0)
    hard: HardRiskProfile | None = None
    #: no NEW position from the start to the end, minutes after midnight New York (DST-aware); equal: no window.
    #: It only ever refuses an entry; open positions are managed. Not part of the evaluation profile (1.6.0).
    quiet_ny_start_min: int = 0
    quiet_ny_end_min: int = 0
    #: no new position whose maximum holding time would run past the Friday close (17:00 New York)
    no_weekend_carry: bool = False
    #: no NEW position on these UTC weekdays (0 Monday .. 6 Sunday) or inside these UTC windows ((start, end) minutes
    #: after 00:00 UTC, start < end). Open positions are managed as usual.
    closed_weekdays_utc: tuple = ()
    closed_utc_windows: tuple = ()

    def __post_init__(self) -> None:
        for k in ("quiet_ny_start_min", "quiet_ny_end_min"):
            v = getattr(self, k)
            if not isinstance(v, int) or isinstance(v, bool) or not 0 <= v < 1440:
                raise ValueError(f"{k} must be an integer 0..1439, minutes after midnight New York (got {v!r})")
        def minute(v) -> bool:
            return isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 1440
        if not isinstance(self.closed_weekdays_utc, tuple) or not all(
                isinstance(d, int) and not isinstance(d, bool) and 0 <= d <= 6 for d in self.closed_weekdays_utc):
            raise ValueError(f"closed_weekdays_utc must be a tuple of weekdays 0..6 (got {self.closed_weekdays_utc!r})")
        if not isinstance(self.closed_utc_windows, tuple) or not all(
                isinstance(w, tuple) and len(w) == 2 and minute(w[0]) and minute(w[1]) and w[0] < w[1]
                for w in self.closed_utc_windows):
            raise ValueError("closed_utc_windows must be a tuple of (start, end) minutes after 00:00 UTC, 0 <= start < "
                             f"end <= 1440 (got {self.closed_utc_windows!r})")

    def effective_risk_pct(self) -> float:
        pct = min(self.risk_per_trade_pct, HARD_MAX_RISK_PCT, UNVALIDATED_MAX_RISK_PCT)
        if self.funded and self.funded.max_risk_per_trade_pct is not None:
            pct = min(pct, self.funded.max_risk_per_trade_pct)
        return max(0.0, pct)


@dataclass(frozen=True)
class InstrumentSpec:
    symbol: str
    contract_size: float  # units of base per lot
    min_lot: float
    lot_step: float
    max_lot: float
    #: account-currency value of a 1.0 move in price, per unit of base
    value_per_price_unit: float
    tradable: bool = True


@dataclass(frozen=True)
class Quote:
    symbol: str
    bid: float
    ask: float
    time: int


@dataclass
class AccountState:
    equity: float | None
    balance: float | None
    day_start_equity: float | None
    peak_equity: float | None
    start_balance: float | None
    open_positions: list[dict] = field(default_factory=list)  # symbol, side, qty, risk_amount, notional
    #: equity at the start of the ISO week; None = unknown, which fails the weekly check
    week_start_equity: float | None = None
    closed_r: list[float] = field(default_factory=list)  # closed-trade R, oldest first
    kill_switch: bool | None = False  # None = could not be read
    paused: bool = False
    halted: bool = False


@dataclass
class Check:
    name: str
    passed: bool
    detail: str


@dataclass
class RiskVerdict:
    decision_id: str
    approved: bool
    qty: float = 0.0
    risk_amount: float = 0.0
    risk_pct: float = 0.0
    entry_ref: float | None = None
    stop: float | None = None
    target: float | None = None
    checks: list[Check] = field(default_factory=list)
    halt: str | None = None
    version: str = RISK_VERSION

    @property
    def reasons(self) -> list[str]:
        return [f"{c.name}: {c.detail}" for c in self.checks if not c.passed]

    def as_dict(self) -> dict:
        d = asdict(self)
        d["reasons"] = self.reasons
        return d


def pip_size(symbol: str) -> float:
    return 0.1 if symbol.startswith("XAU") else 0.01 if symbol.endswith("JPY") else 0.0001


def streak_multiplier(closed_r: list[float], step: int, floor_: float) -> float:
    """Risk multiple after the current run of consecutive losses. Never above 1."""
    run = 0
    for r in reversed(closed_r):
        if r is None:
            break
        if r < 0:
            run += 1
        else:
            break
    return max(floor_, 0.5 ** (run // step)) if step > 0 else 1.0


class RiskEngine:
    def __init__(self, limits: RiskLimits = RiskLimits()) -> None:
        self.limits = limits

    def trade_limits(self, instrument: str, spread: float) -> dict:
        """The per-trade limits `evaluate` applies at this spread, as numbers a proposer can respect when it places its
        levels. Information only: `evaluate` alone decides, with the live quote at the time."""
        L = self.limits
        cost = spread + (L.commission_pips_rt + 2 * L.slippage_pips) * pip_size(instrument)
        min_stop = max(L.min_stop_spreads * spread, spread / L.max_spread_to_stop, cost / L.max_cost_to_risk)
        return {"min_reward_risk": L.min_reward_risk, "min_stop_distance": round(min_stop, 8),
                "round_trip_cost": round(cost, 8), "max_cost_share_of_stop": L.max_cost_to_risk,
                "note": "the risk engine refuses a stop closer than min_stop_distance to the entry, or reward:risk below "
                        "min_reward_risk; it also applies the account limits (daily loss, drawdown, exposure)"}

    # ── account-level checks: one definition, used by evaluate() and by account_gates() ──

    @staticmethod
    def _c_kill(a: AccountState) -> Check:
        return Check("kill_switch", a.kill_switch is False,
                     "active" if a.kill_switch else ("unreadable: treated as active" if a.kill_switch is None else "off"))

    @staticmethod
    def _c_paused(a: AccountState) -> Check:
        return Check("paused", not a.paused, "trading paused" if a.paused else "running")

    @staticmethod
    def _c_halted(a: AccountState) -> Check:
        return Check("halted", not a.halted, "halted: human action required" if a.halted else "not halted")

    @staticmethod
    def _c_equity(a: AccountState) -> Check:
        return Check("equity", a.equity is not None and a.equity > 0, f"equity {a.equity}")

    def _c_daily(self, a: AccountState) -> Check:
        L, eq = self.limits, a.equity
        dse = a.day_start_equity
        if not dse or eq is None:  # unknown is not "no loss today": it fails
            return Check("daily_loss", False, f"start-of-day equity unknown ({dse}): cannot verify the daily loss")
        day = (eq - dse) / dse * 100
        daily_limit = L.daily_loss_limit_pct
        if L.funded and L.funded.daily_loss_pct is not None:
            daily_limit = min(daily_limit, L.funded.daily_loss_pct)
        return Check("daily_loss", day > -daily_limit, f"today {day:+.2f}% vs limit -{daily_limit}%")

    def _c_weekly(self, a: AccountState) -> Check:
        L, eq, wse = self.limits, a.equity, a.week_start_equity
        if not wse or eq is None:
            return Check("weekly_loss", False, f"start-of-week equity unknown ({wse}): cannot verify the weekly loss")
        week = (eq - wse) / wse * 100
        return Check("weekly_loss", week > -L.weekly_loss_limit_pct,
                     f"this week {week:+.2f}% vs limit -{L.weekly_loss_limit_pct}%")

    def _c_drawdown(self, a: AccountState) -> tuple[Check, float]:
        L, eq = self.limits, a.equity
        peak = a.peak_equity
        if not peak or eq is None:
            return Check("drawdown", False, f"peak equity unknown ({peak}): cannot verify the drawdown"), 0.0
        dd = (eq - peak) / peak * 100
        max_dd = L.max_drawdown_pct
        if L.funded and L.funded.trailing_drawdown_pct is not None:
            max_dd = min(max_dd, L.funded.trailing_drawdown_pct)
        return Check("drawdown", dd > -max_dd, f"drawdown {dd:.2f}% vs limit -{max_dd}%"), dd

    def _c_funded_total(self, a: AccountState) -> Check | None:
        L = self.limits
        if L.funded and L.funded.max_loss_pct is not None and a.start_balance:
            total = (a.equity - a.start_balance) / a.start_balance * 100
            return Check("funded_max_loss", total > -L.funded.max_loss_pct,
                         f"total {total:+.2f}% vs funded limit -{L.funded.max_loss_pct}%")
        return None

    def _c_positions(self, a: AccountState, instrument: str) -> list[Check]:
        L, opens = self.limits, a.open_positions
        out = [Check("open_positions", len(opens) < L.max_open_positions, f"{len(opens)} open, max {L.max_open_positions}"),
               Check("same_symbol", all(p["symbol"] != instrument for p in opens),
                     "a position in this instrument is already open" if any(p["symbol"] == instrument for p in opens)
                     else "none open")]
        ccy = {instrument[:3], instrument[3:]}
        per_ccy = max((sum(1 for p in opens if c in (p["symbol"][:3], p["symbol"][3:])) for c in ccy), default=0)
        out.append(Check("currency_exposure", per_ccy < L.max_positions_per_currency,
                         f"{per_ccy} open positions share a currency, max {L.max_positions_per_currency}"))
        return out

    def _c_quiet_hours(self, now: int) -> Check | None:
        """No new position in the profile's New York window (the New York close to the Tokyo open), if it sets one."""
        a, b = self.limits.quiet_ny_start_min, self.limits.quiet_ny_end_min
        if a == b:
            return None
        ny = datetime.fromtimestamp(now, NEW_YORK)
        m = ny.hour * 60 + ny.minute
        inside = a <= m < b if a < b else (m >= a or m < b)  # a window may run past midnight
        return Check("quiet_hours", not inside,
                     f"{ny:%H:%M} New York: no new position from {a // 60:02d}:{a % 60:02d} to {b // 60:02d}:{b % 60:02d} "
                     f"New York (the rollover to the Tokyo open: the thinnest liquidity of the day)")

    def _c_calendar(self, now: int) -> Check | None:
        """No new position on a closed UTC weekday or inside a closed UTC window, if the limits set any."""
        days, windows = self.limits.closed_weekdays_utc, self.limits.closed_utc_windows
        if not days and not windows:
            return None
        u = datetime.fromtimestamp(now, timezone.utc)
        m = u.hour * 60 + u.minute
        if u.weekday() in days:
            return Check("trading_calendar", False, f"{WEEKDAYS[u.weekday()]} (UTC): no new position on "
                                                    + ", ".join(WEEKDAYS[d] for d in sorted(days)))
        for a, b in windows:
            if a <= m < b:
                return Check("trading_calendar", False, f"{u:%H:%M} UTC: no new position from {a // 60:02d}:{a % 60:02d} "
                                                        f"to {b // 60:02d}:{b % 60:02d} UTC")
        return Check("trading_calendar", True, f"{WEEKDAYS[u.weekday()]} {u:%H:%M} UTC: open for new positions")

    def trade_risk_budget(self, account: AccountState) -> float | None:
        """The most the next trade would be sized to lose (before lot rounding), from the same rule evaluate() sizes
        with; None without a positive equity."""
        eq = account.equity
        if eq is None or not eq > 0:
            return None
        L = self.limits
        mult = streak_multiplier(account.closed_r, L.loss_streak_step, L.loss_streak_floor)
        budget = eq * L.effective_risk_pct() * mult / 100
        return min(budget, L.hard.risk_per_trade * mult) if L.hard is not None else budget

    def _c_weekend_carry(self, decision, now: int) -> Check | None:
        """No new position that could still be open at the Friday close (17:00 New York), if the limits say so."""
        if not self.limits.no_weekend_carry:
            return None
        hold_s = (int(getattr(decision, "max_hold_minutes", 0) or 0) * 60
                  or int(getattr(decision, "max_hold_hours", 0) or 0) * 3600 or 48 * 3600)
        ny = datetime.fromtimestamp(now, NEW_YORK)
        close = (ny + timedelta(days=(4 - ny.weekday()) % 7)).replace(hour=17, minute=0, second=0, microsecond=0)
        closed = ny.weekday() == 5 or (ny.weekday() == 4 and ny >= close) or (ny.weekday() == 6 and ny.hour < 17)
        latest = datetime.fromtimestamp(now + hold_s, NEW_YORK)
        return Check("weekend_carry", not closed and latest <= close,
                     f"{ny:%a %H:%M} New York: the market is closed for the weekend" if closed else
                     f"held up to {hold_s // 60} min it could still be open at the Friday close ({close:%a %H:%M} New York)")

    def _c_weekend(self, now: int) -> Check | None:
        if self.limits.funded and self.limits.funded.no_weekend_holding:
            wd = datetime.fromtimestamp(now, timezone.utc)
            return Check("funded_weekend", not (wd.weekday() == 4 and wd.hour >= 16), "no new positions late Friday")
        return None

    def account_gates(self, account: AccountState, instrument: str, now: int) -> list[Check]:
        """The checks that refuse ANY new trade on `instrument` whatever its levels: the same
        definitions evaluate() applies. Used to avoid asking a model for a trade the account cannot
        take (a spent daily loss limit, full positions); evaluate() still decides every trade."""
        out = [self._c_kill(account), self._c_paused(account), self._c_halted(account), self._c_equity(account)]
        if not out[-1].passed:
            return out
        out += [self._c_daily(account), self._c_weekly(account), self._c_drawdown(account)[0]]
        out += [c for c in (self._c_funded_total(account), self._c_weekend(now), self._c_quiet_hours(now),
                            self._c_calendar(now)) if c is not None]
        out += self._c_positions(account, instrument)
        return out

    def evaluate(self, decision, account: AccountState, spec: InstrumentSpec | None, quote: Quote | None,
                 now: int, executed_ids: set[str] | frozenset = frozenset(),
                 data_flags: tuple[str, ...] | list[str] = (), swap_per_night: float = 0.0) -> RiskVerdict:
        L = self.limits
        v = RiskVerdict(decision.id, False)
        checks = v.checks

        def check(name: str, ok: bool, detail: str) -> bool:
            checks.append(Check(name, bool(ok), detail))
            return bool(ok)

        def add(c: Check | None) -> bool:
            if c is None:
                return True
            checks.append(c)
            return c.passed

        # ── switches and state: fail closed ─────────────────────────────
        ok = add(self._c_kill(account))
        ok &= add(self._c_paused(account))
        ok &= add(self._c_halted(account))
        ok &= check("decision", decision.decision in ("BUY", "SELL"), f"decision is {decision.decision}")
        ok &= check("data_quality", not data_flags,
                    "flagged market data: " + "; ".join(data_flags) if data_flags else "no flags")
        ok &= check("duplicate", decision.id not in executed_ids, "decision already executed" if decision.id in executed_ids else "new")
        eq = account.equity
        ok &= add(self._c_equity(account))
        ok &= check("spec", spec is not None and spec.tradable, "instrument spec missing or not tradable" if not (spec and spec.tradable) else "ok")
        fresh = quote is not None and quote.bid > 0 and quote.ask >= quote.bid and now - quote.time <= L.max_quote_age_s
        ok &= check("quote", fresh, "no quote" if quote is None else f"age {now - quote.time}s, bid {quote.bid}, ask {quote.ask}")
        if not ok:
            return v

        side = 1 if decision.decision == "BUY" else -1
        entry = quote.ask if side > 0 else quote.bid
        stop, target = decision.stop_loss, decision.take_profit
        spread = quote.ask - quote.bid
        v.entry_ref, v.stop, v.target = entry, stop, target
        time_exit = getattr(decision, "exit_kind", "STOP_TARGET") == "TIME"

        # ── the trade itself ────────────────────────────────────────────
        # Every trade needs a protective stop: it is what bounds the loss and what the size is computed
        # from. A time-exit trade (exit_kind TIME) may have no target; if it has one, it must be valid.
        ok &= check("stop_side", stop is not None and (entry - stop) * side > 0,
                    f"stop {stop} vs live entry {entry}")
        if not (time_exit and target is None):
            ok &= check("target_side", target is not None and (target - entry) * side > 0,
                        f"target {target} vs live entry {entry}")
        if not ok:
            return v
        stop_dist = abs(entry - stop)
        if target is not None:
            rr = abs(target - entry) / stop_dist
            ok &= check("reward_risk", rr >= L.min_reward_risk, f"{rr:.2f} vs minimum {L.min_reward_risk}")
        else:
            checks.append(Check("reward_risk", True, "time exit: no target; the stop bounds the loss"))
        ok &= check("stop_distance", stop_dist >= L.min_stop_spreads * spread,
                    f"stop {stop_dist:.6g} vs {L.min_stop_spreads} x spread {spread:.6g}")
        ok &= check("spread", spread / stop_dist <= L.max_spread_to_stop,
                    f"spread is {spread / stop_dist:.1%} of the stop (max {L.max_spread_to_stop:.0%})")
        cost = spread + (L.commission_pips_rt + 2 * L.slippage_pips) * pip_size(decision.instrument)
        ok &= check("cost_to_risk", cost / stop_dist <= L.max_cost_to_risk,
                    f"round-trip cost is {cost / stop_dist:.1%} of the stop (max {L.max_cost_to_risk:.0%}): "
                    f"spread {spread:.6g} + commission and slippage")

        # ── account limits ──────────────────────────────────────────────
        ok &= add(self._c_daily(account))
        ok &= add(self._c_weekly(account))
        dd_check, dd = self._c_drawdown(account)
        if not add(dd_check):
            v.halt = f"max drawdown {dd:.2f}% breached"
        ok &= add(self._c_funded_total(account))
        ok = ok and v.halt is None
        for c in self._c_positions(account, decision.instrument):
            ok &= add(c)
        ok &= add(self._c_weekend(now))
        ok &= add(self._c_quiet_hours(now))
        ok &= add(self._c_calendar(now))
        ok &= add(self._c_weekend_carry(decision, now))
        if not ok:
            return v

        # ── size: equity x risk%, never the AI's opinion ────────────────
        mult = streak_multiplier(account.closed_r, L.loss_streak_step, L.loss_streak_floor)
        risk_pct = L.effective_risk_pct() * mult
        risk_amount = eq * risk_pct / 100.0
        per_lot = stop_dist * spec.value_per_price_unit * spec.contract_size
        if L.hard is not None:
            # all-in: what the hard gate verifies, within a budget that never exceeds the fixed per-trade risk
            per_lot = loss_per_lot(L.hard, stop_distance=stop_dist, pip=pip_size(decision.instrument),
                                   contract_size=spec.contract_size, value_per_price_unit=spec.value_per_price_unit,
                                   swap_per_night=swap_per_night)["total"]
            risk_amount = min(risk_amount, L.hard.risk_per_trade * mult)
        raw = risk_amount / per_lot if per_lot > 0 else 0.0
        lots = floor(raw / spec.lot_step + 1e-9) * spec.lot_step
        lots = min(lots, spec.max_lot, L.funded.max_lots if (L.funded and L.funded.max_lots) else spec.max_lot)
        ok &= check("min_lot", lots >= spec.min_lot,
                    f"{raw:.4f} lots needed for {risk_pct:.3f}% risk; broker minimum {spec.min_lot}")
        if not ok:
            return v
        actual = lots * per_lot
        notional = lots * spec.contract_size * entry * spec.value_per_price_unit
        exposure = sum(p.get("notional", 0.0) for p in account.open_positions) + notional
        ok &= check("leverage", exposure / eq <= L.max_leverage, f"{exposure / eq:.2f}x vs max {L.max_leverage}x")
        ok &= check("risk_ceiling", actual <= eq * min(HARD_MAX_RISK_PCT, UNVALIDATED_MAX_RISK_PCT) / 100 + 1e-9,
                    f"risk {actual:.2f} vs ceiling {eq * min(HARD_MAX_RISK_PCT, UNVALIDATED_MAX_RISK_PCT) / 100:.2f}")
        open_risk = sum(float(p.get("risk_amount") or 0.0) for p in account.open_positions)
        unknown = [p.get("symbol") for p in account.open_positions if p.get("risk_amount") is None]
        ok &= check("open_risk", not unknown and open_risk + actual <= eq * L.max_open_risk_pct / 100 + 1e-9,
                    (f"open positions without a known risk at their stop: {unknown}" if unknown else
                     f"open risk {open_risk:.2f} + {actual:.2f} vs ceiling {eq * L.max_open_risk_pct / 100:.2f}"))
        if not ok:
            return v
        checks.append(Check("streak", True, f"risk multiplier {mult:.2f} after recent losses (never above 1)"))
        v.approved, v.qty, v.risk_amount, v.risk_pct = True, round(lots, 8), actual, actual / eq * 100
        return v
