"""The hard risk profile: an FTMO-style evaluation account's limits, and the one cost model both the risk engine
(which sizes) and the hard risk gate (which verifies) use to compute a trade's maximum loss.

The default is the $200,000 FTMO-style profile:

| | |
|---|---|
| Starting balance | $200,000 |
| Daily loss limit | $10,000 (5% of the starting balance), from the day's reference, measured on equity |
| Maximum total loss | $20,000 (10%): equity may never reach $180,000 |
| Challenge / verification target | $20,000 (10%) / $10,000 (5%): reported, never pursued (a target is a filter, not a quota) |
| Minimum trading days | 4 |
| Risk per trade | $500 (0.25% of the STARTING balance, all costs included); it never grows with equity |
| Total open risk | $2,000 (1%) |
| Daily reset | 00:00 Europe/Prague (FTMO resets at midnight CE(S)T); configurable, never assumed UTC |

A profile is frozen and validated on construction: an inconsistent profile cannot exist. Changing it during an
evaluation is refused by the gate (the run records the profile's sha256).
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, fields, replace
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

#: 1.1.0: `daily_breach` (LOCK_RUN, FTMO's rule: a daily breach ends the run; LOCK_DAY: no new trade until the
#:        next reset, the breach recorded as a violation) and the PAPER-FORWARD-200K profile.
PROFILE_VERSION = "hard-profile-1.1.0"
DAILY_BREACH = ("LOCK_RUN", "LOCK_DAY")


class ProfileError(ValueError):
    """The profile is inconsistent or incomplete: nothing may trade under it."""


def _finite(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


@dataclass(frozen=True)
class HardRiskProfile:
    name: str = "FTMO-200K"
    currency: str = "USD"
    starting_balance: float = 200_000.0
    daily_loss_limit: float = 10_000.0
    max_total_loss: float = 20_000.0
    challenge_target: float = 20_000.0
    verification_target: float = 10_000.0
    min_trading_days: int = 4
    risk_per_trade: float = 500.0
    max_open_risk: float = 2_000.0
    reset_timezone: str = "Europe/Prague"
    reset_hour: int = 0
    # ── market data tolerance ──
    max_quote_age_s: int = 30
    max_spread_rel: float = 0.002  # spread / mid
    max_entry_deviation_rel: float = 0.002  # proposed entry vs the live executable price
    # ── conservative cost model (per lot) ──
    commission_per_lot_rt: float = 7.0  # account currency, round trip
    slippage_pips: float = 0.5  # per fill; the paper broker fills at 0.1, so this is pessimistic
    swap_nights_allowance: int = 3  # financing charged as if held over a Wednesday (triple) rollover
    # ── broker / account constraints ──
    leverage: float = 30.0  # required margin = notional / leverage
    max_lots: float = 50.0
    max_open_positions: int = 5
    permit_ttl_s: int = 10  # an execution permit is single-use and expires
    #: LOCK_RUN: a daily breach locks the evaluation run (FTMO fails the account). LOCK_DAY: no new trade until
    #: the next daily reset, and the breach is recorded as an FTMO-rule violation. A maximum-loss breach always
    #: locks the run.
    daily_breach: str = "LOCK_RUN"

    def __post_init__(self) -> None:
        problems = self.problems()
        if problems:
            raise ProfileError(f"profile {self.name!r} refused: " + "; ".join(problems))

    def problems(self) -> list[str]:
        p: list[str] = []
        money = ("starting_balance", "daily_loss_limit", "max_total_loss", "challenge_target", "verification_target",
                 "risk_per_trade", "max_open_risk", "max_spread_rel", "max_entry_deviation_rel", "leverage", "max_lots")
        for k in money:
            if not _finite(getattr(self, k)) or getattr(self, k) <= 0:
                p.append(f"{k} must be a finite number > 0 (got {getattr(self, k)!r})")
        for k in ("commission_per_lot_rt", "slippage_pips"):
            if not _finite(getattr(self, k)) or getattr(self, k) < 0:
                p.append(f"{k} must be a finite number >= 0 (got {getattr(self, k)!r})")
        for k in ("min_trading_days", "max_quote_age_s", "max_open_positions", "permit_ttl_s"):
            v = getattr(self, k)
            if not isinstance(v, int) or isinstance(v, bool) or v < 1:
                p.append(f"{k} must be an integer >= 1 (got {v!r})")
        if not isinstance(self.swap_nights_allowance, int) or self.swap_nights_allowance < 0:
            p.append(f"swap_nights_allowance must be an integer >= 0 (got {self.swap_nights_allowance!r})")
        if not isinstance(self.reset_hour, int) or isinstance(self.reset_hour, bool) or not 0 <= self.reset_hour <= 23:
            p.append(f"reset_hour must be an integer 0..23 (got {self.reset_hour!r})")
        if self.daily_breach not in DAILY_BREACH:
            p.append(f"daily_breach must be one of {DAILY_BREACH} (got {self.daily_breach!r})")
        if not (isinstance(self.currency, str) and len(self.currency) == 3 and self.currency.isupper()):
            p.append(f"currency must be a 3-letter code (got {self.currency!r})")
        try:
            ZoneInfo(self.reset_timezone)
        except (ZoneInfoNotFoundError, ValueError, TypeError):
            p.append(f"reset_timezone {self.reset_timezone!r} is not a known IANA time zone")
        if not p:
            if not self.risk_per_trade <= self.max_open_risk:
                p.append("risk_per_trade must be <= max_open_risk")
            if not self.max_open_risk <= self.daily_loss_limit:
                p.append("max_open_risk must be <= daily_loss_limit")
            if not self.daily_loss_limit <= self.max_total_loss:
                p.append("daily_loss_limit must be <= max_total_loss")
            if not self.max_total_loss < self.starting_balance:
                p.append("max_total_loss must be < starting_balance")
        return p

    # ── derived, read-only ──

    @property
    def total_loss_floor(self) -> float:
        """Equity at or below this fails the evaluation (static, from the starting balance)."""
        return self.starting_balance - self.max_total_loss

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.reset_timezone)

    def as_dict(self) -> dict:
        return asdict(self)

    def sha256(self) -> str:
        d = self.as_dict()
        if d["daily_breach"] == "LOCK_RUN":  # the 1.0.0 behaviour: a run started before the field keeps its hash
            del d["daily_breach"]
        return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()

    def scaled(self, starting_balance: float, name: str | None = None) -> "HardRiskProfile":
        """The same percentages on another balance (a $20,000 paper account, a backtest). Per-lot costs and
        tolerances are unchanged."""
        k = starting_balance / self.starting_balance
        money = ("daily_loss_limit", "max_total_loss", "challenge_target", "verification_target", "risk_per_trade",
                 "max_open_risk")
        return replace(self, name=name or f"{self.name}-scaled-{starting_balance:g}", starting_balance=starting_balance,
                       **{f: getattr(self, f) * k for f in money})

    @classmethod
    def from_overrides(cls, base: "HardRiskProfile", overrides: dict) -> "HardRiskProfile":
        known = {f.name for f in fields(cls)}
        unknown = sorted(set(overrides) - known)
        if unknown:  # a typo must not silently leave a limit at its default
            raise ProfileError(f"unknown profile fields: {unknown}")
        return replace(base, **overrides)


FTMO_200K = HardRiskProfile()
#: The PAPER_FORWARD account: the same limits; a daily breach stops new trades for the day and is recorded as a
#: violation, so the forward measurement continues. The maximum loss still ends the run.
PAPER_FORWARD_200K = replace(FTMO_200K, name="PAPER-FORWARD-200K", daily_breach="LOCK_DAY")
PROFILES = {FTMO_200K.name: FTMO_200K, PAPER_FORWARD_200K.name: PAPER_FORWARD_200K}


def pip_of(symbol: str) -> float:
    return 0.1 if symbol.startswith("XAU") else 0.01 if symbol.endswith("JPY") else 0.0001


def loss_per_lot(profile: HardRiskProfile, *, stop_distance: float, pip: float, contract_size: float,
                 value_per_price_unit: float, swap_per_night: float = 0.0) -> dict[str, float]:
    """Maximum loss of ONE lot, in account currency, if the stop is hit: the distance from the executable entry
    (which already contains the spread) to the stop, the round-trip commission, slippage on BOTH fills, and
    financing for the declared allowance of nights. A financing credit is never counted in the trade's favour."""
    units = contract_size * value_per_price_unit
    parts = {"stop": stop_distance * units,
             "commission": profile.commission_per_lot_rt,
             "slippage": 2 * profile.slippage_pips * pip * units,
             "financing": max(0.0, swap_per_night) * profile.swap_nights_allowance * units}
    parts["total"] = parts["stop"] + parts["commission"] + parts["slippage"] + parts["financing"]
    return parts


__all__ = ["DAILY_BREACH", "FTMO_200K", "PAPER_FORWARD_200K", "PROFILES", "PROFILE_VERSION", "HardRiskProfile", "ProfileError", "loss_per_lot", "pip_of"]
