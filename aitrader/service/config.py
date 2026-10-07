"""Service configuration, from environment variables only.

Secrets are read here and passed to the one component that needs them;
`public()` is the only view of configuration that leaves the process.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from ..risk.engine import HARD_MAX_RISK_PCT, UNVALIDATED_MAX_RISK_PCT, FundedRules, RiskLimits
from ..decision.edge_status import PAPER_MODES
from ..risk.profile import FTMO_200K, PAPER_FORWARD_200K, PROFILES, HardRiskProfile, ProfileError

DEFAULT_SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
                   "EURGBP", "EURJPY", "GBPJPY", "EURCHF", "AUDJPY")


class ServiceConfigError(ValueError):
    pass


def _flag(e, key: str, default: bool) -> bool:
    """A true/false variable. Anything else is refused: an ambiguous switch fails closed."""
    raw = (e.get(key) or "").strip().lower()
    if raw == "":
        return default
    if raw in ("true", "1", "yes"):
        return True
    if raw in ("false", "0", "no"):
        return False
    raise ServiceConfigError(f"{key} must be true or false, got {raw!r}")


def _f(e, key, default):
    raw = e.get(key)
    if raw in (None, ""):
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ServiceConfigError(f"{key} must be a number, got {raw!r}") from exc


@dataclass(frozen=True)
class ServiceConfig:
    #: PAPER or PAPER_FORWARD, both simulated in-process: no broker is integrated (TradeLocker removed; MetaTrader 5
    #: planned). PAPER_FORWARD also executes the model traders' proposals on paper (docs/PAPER_FORWARD.md).
    mode: str = "PAPER"
    data_dir: str = "./runtime"
    port: int = 8080
    symbols: tuple[str, ...] = DEFAULT_SYMBOLS
    start_balance: float = 200_000.0  # the FTMO-style $200K evaluation account (hard_profile)
    #: RISK_PROFILE (+ RISK_PROFILE_OVERRIDES, a JSON object of fields): the hard risk gate's limits. Fixed for an
    #: evaluation run: a different profile is refused by the gate until an explicit evaluation reset.
    hard_profile: HardRiskProfile = FTMO_200K
    dashboard_token: str = field(default="", repr=False)
    cycle_delay_s: int = 90  # after each H1 close, give the broker time to publish the bar
    monitor_interval_s: int = 20
    #: Model-trader modes only: decide every N minutes instead of every 4th H1 close.
    #: 0 = the tested cadence. The evidence system refuses anything else (runtime).
    decision_interval_min: int = 0
    #: Pairs analysed per decision cycle, in rotation; 0 = all. Keeps a frequent
    #: cadence inside the language-model providers' rate limits.
    symbols_per_cycle: int = 0
    #: SCAN_TIMEFRAME: "H1" = decide on H1 closes at the tested cadence; "M15" = the opportunity
    #: scanner: every M15 close, with H1 and H4 as context (edges / model modes only, see runtime).
    scan_timeframe: str = "H1"
    #: Where prices come from: "yahoo" (public prices, estimated spreads; the default) or "offline"
    #: (no data: the service runs, reports DATA: NOT CONNECTED and never trades). "auto" means "yahoo".
    data_source: str = "yahoo"
    spreads_pips: dict = field(default_factory=dict)  # PAPER_SPREAD_PIPS_<PAIR> overrides (yahoo)
    risk: RiskLimits = field(default_factory=RiskLimits)
    #: EXPERIMENTAL_EXECUTE: kept refused (there is no broker to send to; PAPER simulates every trade).
    experimental_execute: bool = False
    #: EXEC_MAX_DECISION_AGE_S: a decision older than this is not executed (stale).
    max_decision_age_s: int = 900

    @classmethod
    def from_env(cls, env: dict | None = None) -> "ServiceConfig":
        e = os.environ if env is None else env
        # LIVE_TRADING exists only to be refused: the default is false and true is not available.
        if _flag(e, "LIVE_TRADING", False):
            raise ServiceConfigError("LIVE_TRADING=true is not available: this build has no live path. Nothing "
                                     "reaches LIVE without every evidence gate and explicit approval "
                                     "(docs/SYSTEM_LIFECYCLE.md)")
        mode = e.get("MODE", "PAPER").strip().upper() or "PAPER"
        # PAPER_MODE, when set, must agree with MODE: a contradiction is ambiguous and refused.
        paper_mode = (e.get("PAPER_MODE") or "").strip()
        if paper_mode:
            pm = _flag(e, "PAPER_MODE", True)
            if pm and mode not in PAPER_MODES:
                raise ServiceConfigError(f"PAPER_MODE=true contradicts MODE={mode}: set one consistently")
            if not pm:
                raise ServiceConfigError("PAPER_MODE=false is not available: this build is PAPER only (no broker is "
                                         "integrated; a MetaTrader 5 adapter is planned)")
        if mode == "LIVE":
            raise ServiceConfigError("MODE=LIVE is not available: nothing reaches LIVE without every evidence gate "
                                     "and explicit approval (docs/SYSTEM_LIFECYCLE.md)")
        if mode == "DEMO":
            raise ServiceConfigError("MODE=DEMO is not available: the TradeLocker integration was removed and no "
                                     "broker is integrated. This build is PAPER only; a MetaTrader 5 adapter is "
                                     "planned once a strategy has positive forward evidence in paper")
        if mode not in PAPER_MODES:
            raise ServiceConfigError(f"MODE must be PAPER or PAPER_FORWARD, got {mode!r}")
        symbols = tuple(s.strip().upper() for s in e.get("SYMBOLS", ",".join(DEFAULT_SYMBOLS)).split(",") if s.strip())
        funded = None
        if e.get("FUNDED_NAME"):
            funded = FundedRules(
                e["FUNDED_NAME"],
                daily_loss_pct=_f(e, "FUNDED_DAILY_LOSS_PCT", None),
                max_loss_pct=_f(e, "FUNDED_MAX_LOSS_PCT", None),
                trailing_drawdown_pct=_f(e, "FUNDED_TRAILING_DD_PCT", None),
                max_risk_per_trade_pct=_f(e, "FUNDED_MAX_RISK_PCT", None),
                no_weekend_holding=e.get("FUNDED_NO_WEEKEND", "false").lower() == "true",
                max_lots=_f(e, "FUNDED_MAX_LOTS", None))
        # Every limit may be lowered (stricter) by its variable, never raised above the build's value:
        # a variable that could loosen a limit is a way around the risk engine (takeover audit).
        base = RiskLimits()

        def tighter(key, ceiling):
            v = _f(e, key, ceiling)
            if not v > 0:
                raise ServiceConfigError(f"{key} must be a positive number, got {v}")
            return min(v, ceiling)

        risk = RiskLimits(
            risk_per_trade_pct=min(tighter("RISK_PER_TRADE_PCT", base.risk_per_trade_pct), HARD_MAX_RISK_PCT,
                                   UNVALIDATED_MAX_RISK_PCT),
            daily_loss_limit_pct=tighter("RISK_DAILY_LOSS_PCT", base.daily_loss_limit_pct),
            weekly_loss_limit_pct=tighter("RISK_WEEKLY_LOSS_PCT", base.weekly_loss_limit_pct),
            max_open_risk_pct=tighter("RISK_MAX_OPEN_RISK_PCT", base.max_open_risk_pct),
            max_drawdown_pct=tighter("RISK_MAX_DRAWDOWN_PCT", base.max_drawdown_pct),
            max_open_positions=int(tighter("RISK_MAX_OPEN_POSITIONS", base.max_open_positions)),
            # A ceiling may be lowered (stricter), never raised above the evidence-based 25%.
            max_cost_to_risk=min(_f(e, "RISK_MAX_COST_TO_RISK", 0.25), 0.25),
            # A public feed timestamps its price itself and may lag a broker's by up to a minute.
            max_quote_age_s=int(_f(e, "RISK_MAX_QUOTE_AGE_S",
                                   90 if e.get("DATA_SOURCE", "yahoo").strip().lower() in ("yahoo", "auto", "") else 30)),
            funded=funded)
        source = e.get("DATA_SOURCE", "yahoo").strip().lower() or "yahoo"
        if source == "auto":
            source = "yahoo"
        if source == "tradelocker":
            raise ServiceConfigError("DATA_SOURCE=tradelocker is not available: the TradeLocker integration was "
                                     "removed. Use yahoo (public prices) or offline")
        if source not in ("yahoo", "offline"):
            raise ServiceConfigError(f"DATA_SOURCE must be yahoo or offline, got {source!r}; "
                                     "an unknown source is refused, never replaced")
        spreads = {k[len("PAPER_SPREAD_PIPS_"):].upper(): float(v) for k, v in e.items()
                   if k.startswith("PAPER_SPREAD_PIPS_") and v}
        interval = int(_f(e, "DECISION_INTERVAL_MIN", 0))
        if not 0 <= interval <= 240:
            raise ServiceConfigError(f"DECISION_INTERVAL_MIN must be 0 (the tested cadence) or 1..240, got {interval}")
        scan = e.get("SCAN_TIMEFRAME", "H1").strip().upper() or "H1"
        if scan not in ("H1", "M15"):
            raise ServiceConfigError(f"SCAN_TIMEFRAME must be H1 or M15, got {scan!r}; an unknown value is refused")
        if scan == "M15" and interval:
            raise ServiceConfigError("SCAN_TIMEFRAME=M15 already decides every 15 minutes: unset DECISION_INTERVAL_MIN")
        per_cycle = int(_f(e, "SYMBOLS_PER_CYCLE", 0))
        if not 0 <= per_cycle <= len(symbols):
            raise ServiceConfigError(f"SYMBOLS_PER_CYCLE must be 0 (all) or 1..{len(symbols)}, got {per_cycle}")
        experimental_execute = _flag(e, "EXPERIMENTAL_EXECUTE", False)
        if experimental_execute:
            # Takeover audit: no edge is VALIDATED (research_status.json), so nothing unvalidated may reach a
            # broker, demo included. DEMO runs as a shadow: every proposal is priced by the risk engine and
            # followed forward, and no order is sent.
            raise ServiceConfigError("EXPERIMENTAL_EXECUTE=true is not available: no edge is VALIDATED "
                                     "(research_status.json), so DEMO sends no unvalidated order; it records "
                                     "and follows every proposal as SHADOW")
        max_age = int(_f(e, "EXEC_MAX_DECISION_AGE_S", 900))
        if not 30 <= max_age <= 3600:
            raise ServiceConfigError(f"EXEC_MAX_DECISION_AGE_S must be 30..3600, got {max_age}")
        default_profile = PAPER_FORWARD_200K if mode == "PAPER_FORWARD" else FTMO_200K
        name = (e.get("RISK_PROFILE") or default_profile.name).strip()
        if name not in PROFILES:  # never silently replaced by the default
            raise ServiceConfigError(f"RISK_PROFILE={name!r} is unknown; available: {sorted(PROFILES)}")
        profile = PROFILES[name]
        raw = (e.get("RISK_PROFILE_OVERRIDES") or "").strip()
        try:
            overrides = json.loads(raw) if raw else {}
            if not isinstance(overrides, dict):
                raise ValueError("must be a JSON object of profile fields")
            # The quote-age tolerance follows the data source the risk engine already accepts (a public feed
            # timestamps its own price and lags a broker's by up to a minute), capped at 90 s, unless set here.
            overrides.setdefault("max_quote_age_s", min(risk.max_quote_age_s, 90))
            profile = HardRiskProfile.from_overrides(profile, overrides)
        except (ValueError, TypeError, ProfileError) as exc:
            raise ServiceConfigError(f"RISK_PROFILE_OVERRIDES refused: {exc}") from exc
        start_balance = _f(e, "PAPER_START_BALANCE", profile.starting_balance)
        if abs(start_balance - profile.starting_balance) > 0.005:
            raise ServiceConfigError(
                f"PAPER_START_BALANCE={start_balance:g} differs from the hard risk profile's starting balance "
                f"{profile.starting_balance:g} ({profile.name}): the evaluation reference must be the account's. "
                "Unset PAPER_START_BALANCE, or set starting_balance in RISK_PROFILE_OVERRIDES")
        return cls(mode=mode, data_dir=e.get("DATA_DIR", "./runtime"), port=int(e.get("PORT", "8080")),
                   experimental_execute=experimental_execute, max_decision_age_s=max_age,
                   symbols=symbols, start_balance=start_balance, hard_profile=profile,
                   dashboard_token=e.get("DASHBOARD_TOKEN", ""), risk=risk,
                   decision_interval_min=interval, symbols_per_cycle=per_cycle, scan_timeframe=scan,
                   data_source=source, spreads_pips=spreads)

    def public(self) -> dict:
        return {"mode": self.mode, "live_trading": False, "real_money": False,
                "paper_mode": self.mode in PAPER_MODES, "paper_forward": self.mode == "PAPER_FORWARD",
                "experimental_execute": self.experimental_execute, "max_decision_age_s": self.max_decision_age_s,
                "symbols": list(self.symbols), "start_balance": self.start_balance,
                "decision_interval_min": self.decision_interval_min, "symbols_per_cycle": self.symbols_per_cycle,
                "scan_timeframe": self.scan_timeframe,
                "data_source": self.data_source,
                "dashboard_token_configured": bool(self.dashboard_token),
                "risk": {k: v for k, v in self.risk.__dict__.items() if k not in ("funded", "hard")},
                "hard_profile": self.hard_profile.as_dict(),
                "funded": (self.risk.funded.__dict__ if self.risk.funded else None)}
