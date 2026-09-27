"""The shared vocabulary of the agents: evidence, objections, reports, context.

Everything an agent says is structured. Free text exists only as an
explanation attached to structured fields; nothing downstream parses prose
to decide anything (an unparseable answer is NO_TRADE, never a guess).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ..features.store import FeatureVector
from ..memory.patterns import AnalogEvidence
from ..regime.model import RegimeState

#: 1.1.0: an independent Reviewer runs before synthesis (evidence-quality checks moved
#: from the Adversary, same codes and severities; four new MINOR quality checks).
AGENT_VERSION = "agents-1.1.0"

SEVERITIES = ("BLOCKING", "MAJOR", "MINOR")

#: The enumerated objection vocabulary. An LLM may only raise codes from this
#: list (an "indexed action space"): anything else is discarded as unparseable.
OBJECTION_CODES = {
    # risk analyst
    "SPREAD_COST": "spread and costs are a large share of the stop",
    "ABNORMAL_MARKET": "volatility or spread beyond anything seen in training",
    "UNFAMILIAR_STATE": "the market state is unlike the training data",
    "STALE_DATA": "the latest data is too old to act on",
    "DATA_QUALITY": "the data failed a quality check",
    "EXPOSURE": "the account already holds this currency exposure",
    "CORRELATED_POSITION": "an open position is strongly correlated with this one",
    "DRAWDOWN_STATE": "the account is in drawdown",
    "ROLLOVER_WINDOW": "spreads widen around the daily rollover",
    "WEEKEND_GAP": "the trade would be held into the weekend",
    "EVENT_RISK_UNKNOWN": "no economic-calendar data is available",
    # adversarial analyst
    "COUNTER_TREND_HTF": "the setup opposes the higher-timeframe trend",
    "OVEREXTENDED": "price is stretched far from its mean in the trade direction",
    "FAKE_BREAKOUT_RISK": "the breakout lacks follow-through",
    "SWEEP_AGAINST": "a liquidity sweep points the other way",
    # reviewer (moved from the adversary in agents-1.1.0; same severities)
    "WEAK_ANALOG_EVIDENCE": "historical analogues are few, dissimilar or dispersed",
    "ANALOG_CONTRADICTION": "historical analogues lost money in this direction",
    "LESSON_MATCH": "a validated lesson says this setup fails in this context",
    "REGIME_MISMATCH": "this setup family has underperformed in this regime",
    "LATE_ENTRY": "most of the expected move has already happened",
    # reviewer (evidence quality; MINOR until their predictive value is measured)
    "ANALOG_NOISE": "the analogue expectancy is smaller than its own standard error",
    "ANALOG_STALE": "most analogues are years old: evidence from a different era",
    "ANALOG_CONCENTRATED": "most analogues come from a single instrument",
    "TEMPLATE_DISAGREEMENT": "the other action template in the same direction disagrees in sign",
    "LLM_OBJECTION": "the language-model reviewer objected",
    "OTHER": "other (explained in text)",
}

FAMILIES = ("TREND_PULLBACK", "BREAKOUT", "MEAN_REVERSION", "SWEEP_REVERSAL", "ANALOG_DISCOVERY")


@dataclass(frozen=True)
class Evidence:
    agent: str
    claim: str
    direction: int  # +1 bullish, -1 bearish, 0 neutral
    strength: float  # 0..1, from the measured quantity, never a model's self-report
    sources: tuple[str, ...]  # feature names or memory ids it rests on (independence accounting)
    data: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        d = asdict(self)
        d["sources"] = list(self.sources)
        return d


@dataclass(frozen=True)
class Objection:
    code: str
    severity: str
    agent: str
    message: str
    data: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.code not in OBJECTION_CODES:
            raise ValueError(f"unknown objection code {self.code!r}")
        if self.severity not in SEVERITIES:
            raise ValueError(f"unknown severity {self.severity!r}")

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SetupCandidate:
    family: str
    direction: int  # +1 BUY, -1 SELL
    template: str
    entry: float  # reference price at decision: ask for BUY, bid for SELL
    stop: float
    target: float
    reward_risk: float
    max_bars: int
    invalidation: str
    analog: dict | None  # AnalogEvidence for this action, point-in-time
    expected_r: float | None
    lower_r: float | None
    win_rate: float | None
    n_analogs: int

    @property
    def action(self) -> str:
        return f"{self.template}:{'BUY' if self.direction > 0 else 'SELL'}"

    def as_dict(self) -> dict:
        d = asdict(self)
        d["action"] = self.action
        return d


@dataclass
class AgentReport:
    agent: str
    version: str
    status: str  # OK | ERROR | TIMEOUT | UNAVAILABLE
    stance: str  # SUPPORT | OPPOSE | NEUTRAL | DESCRIBE
    started: float
    finished: float
    evidence: list[Evidence] = field(default_factory=list)
    objections: list[Objection] = field(default_factory=list)
    candidates: list[SetupCandidate] = field(default_factory=list)
    summary: str = ""
    llm: dict | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.status == "OK"

    @property
    def latency_ms(self) -> float:
        return round((self.finished - self.started) * 1000, 2)

    def as_dict(self) -> dict:
        return {
            "agent": self.agent, "version": self.version, "status": self.status, "stance": self.stance,
            "latency_ms": self.latency_ms, "summary": self.summary, "error": self.error,
            "evidence": [e.as_dict() for e in self.evidence],
            "objections": [o.as_dict() for o in self.objections],
            "candidates": [c.as_dict() for c in self.candidates],
            "llm": self.llm,
        }


@dataclass
class AccountView:
    """What the agents may know about the account. Never credentials, never a size."""

    equity: float | None
    balance: float | None
    drawdown_pct: float | None
    open_positions: list[dict] = field(default_factory=list)  # symbol, side
    daily_pnl_pct: float | None = None


@dataclass
class MarketContext:
    """Everything known at decision time `t`, and nothing else."""

    symbol: str
    timeframe: str
    t: int
    features: FeatureVector
    regime: RegimeState
    atr: float | None
    bid: float | None
    ask: float | None
    quote_time: int | None
    levels: dict[str, float | None]
    account: AccountView
    data_flags: list[str] = field(default_factory=list)
    analogs: dict[str, AnalogEvidence] = field(default_factory=dict)  # action -> evidence
    analog_meta: dict = field(default_factory=dict)
    knowledge: Any = None  # ExperienceView (point-in-time lessons and statistics)
    mode: str = "BACKTEST"
    # Filled only when the language-model trader decides (it costs a wider data read):
    mtf: dict = field(default_factory=dict)  # timeframe -> compact summary of COMPLETED bars
    memory_brief: dict = field(default_factory=dict)  # its own past trades, reflections, lessons
    trading_allowed: bool = True  # False when paused / stopped / halted: the model is not consulted

    def as_dict(self) -> dict:
        return {
            "symbol": self.symbol, "timeframe": self.timeframe, "t": self.t,
            "features": self.features.as_dict(), "regime": self.regime.as_dict(),
            "atr": self.atr, "bid": self.bid, "ask": self.ask, "quote_time": self.quote_time,
            "levels": self.levels, "data_flags": self.data_flags, "mode": self.mode,
            "account": asdict(self.account), "analog_meta": self.analog_meta,
        }
