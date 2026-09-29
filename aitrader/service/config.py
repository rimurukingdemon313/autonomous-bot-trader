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
    #: Model-trader modes only: decide every N minutes instead of every 4th H1 close.
    #: 0 = the tested cadence. The evidence system refuses anything else (runtime).
    decision_interval_min: int = 0
    #: Pairs analysed per decision cycle, in rotation; 0 = all. Keeps a frequent
    #: cadence inside the language-model providers' rate limits.
    symbols_per_cycle: int = 0
    #: SCAN_TIMEFRAME: "H1" = decide on H1 closes at the tested cadence; "M15" = the opportunity
    #: scanner: every M15 close, with H1 and H4 as context (edges / model modes only, see runtime).
    scan_timeframe: str = "H1"
    #: Where prices come from: "auto" (TradeLocker when its credentials are set, else none),
    #: "tradelocker", or "yahoo" (PAPER only: no broker, no account, estimated spreads).
    data_source: str = "auto"
    spreads_pips: dict = field(default_factory=dict)  # PAPER_SPREAD_PIPS_<PAIR> overrides (yahoo)
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
            # A public feed timestamps its price itself and may lag a broker's by up to a minute.
            max_quote_age_s=int(_f(e, "RISK_MAX_QUOTE_AGE_S",
                                   90 if e.get("DATA_SOURCE", "").strip().lower() == "yahoo" else 30)),
            funded=funded)
        source = e.get("DATA_SOURCE", "auto").strip().lower() or "auto"
        if source not in ("auto", "tradelocker", "yahoo"):
            raise ServiceConfigError(f"DATA_SOURCE must be auto, tradelocker or yahoo, got {source!r}; "
                                     "an unknown source is refused, never replaced")
        if source == "yahoo" and mode != "PAPER":
            raise ServiceConfigError("DATA_SOURCE=yahoo is for MODE=PAPER only: it has no broker to place orders")
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
        return cls(mode=mode, data_dir=e.get("DATA_DIR", "./runtime"), port=int(e.get("PORT", "8080")),
                   symbols=symbols, start_balance=_f(e, "PAPER_START_BALANCE", 20_000.0),
                   dashboard_token=e.get("DASHBOARD_TOKEN", ""), risk=risk,
                   decision_interval_min=interval, symbols_per_cycle=per_cycle, scan_timeframe=scan,
                   data_source=source, spreads_pips=spreads)

    def public(self) -> dict:
        return {"mode": self.mode, "symbols": list(self.symbols), "start_balance": self.start_balance,
                "decision_interval_min": self.decision_interval_min, "symbols_per_cycle": self.symbols_per_cycle,
                "scan_timeframe": self.scan_timeframe,
                "data_source": self.data_source,
                "dashboard_token_configured": bool(self.dashboard_token),
                "risk": {k: v for k, v in self.risk.__dict__.items() if k != "funded"},
                "funded": (self.risk.funded.__dict__ if self.risk.funded else None)}
