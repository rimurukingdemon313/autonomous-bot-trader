"""Service configuration, from environment variables only.

Secrets are read here and passed to the one component that needs them;
`public()` is the only view of configuration that leaves the process.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from ..risk.engine import HARD_MAX_RISK_PCT, FundedRules, RiskLimits

DEFAULT_SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
                   "EURGBP", "EURJPY", "GBPJPY", "EURCHF", "AUDJPY")


class ServiceConfigError(ValueError):
    pass


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
    mode: str = "PAPER"  # PAPER | DEMO
    data_dir: str = "./runtime"
    port: int = 8080
    symbols: tuple[str, ...] = DEFAULT_SYMBOLS
    start_balance: float = 20_000.0
    dashboard_token: str = field(default="", repr=False)
    cycle_delay_s: int = 90  # after each H1 close, give the broker time to publish the bar
    monitor_interval_s: int = 20
    risk: RiskLimits = field(default_factory=RiskLimits)

    @classmethod
    def from_env(cls, env: dict | None = None) -> "ServiceConfig":
        e = os.environ if env is None else env
        mode = e.get("MODE", "PAPER").strip().upper()
        if mode == "LIVE":
            raise ServiceConfigError("MODE=LIVE is not available: nothing reaches LIVE without every evidence gate "
                                     "and explicit approval (docs/SYSTEM_LIFECYCLE.md)")
        if mode not in ("PAPER", "DEMO"):
            raise ServiceConfigError(f"MODE must be PAPER or DEMO, got {mode!r}")
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
        risk = RiskLimits(
            risk_per_trade_pct=min(_f(e, "RISK_PER_TRADE_PCT", 0.5), HARD_MAX_RISK_PCT),
            daily_loss_limit_pct=_f(e, "RISK_DAILY_LOSS_PCT", 2.0),
            max_drawdown_pct=_f(e, "RISK_MAX_DRAWDOWN_PCT", 8.0),
            max_open_positions=int(_f(e, "RISK_MAX_OPEN_POSITIONS", 3)),
            funded=funded)
        return cls(mode=mode, data_dir=e.get("DATA_DIR", "./runtime"), port=int(e.get("PORT", "8080")),
                   symbols=symbols, start_balance=_f(e, "PAPER_START_BALANCE", 20_000.0),
                   dashboard_token=e.get("DASHBOARD_TOKEN", ""), risk=risk)

    def public(self) -> dict:
        return {"mode": self.mode, "symbols": list(self.symbols), "start_balance": self.start_balance,
                "dashboard_token_configured": bool(self.dashboard_token),
                "risk": {k: v for k, v in self.risk.__dict__.items() if k != "funded"},
                "funded": (self.risk.funded.__dict__ if self.risk.funded else None)}
