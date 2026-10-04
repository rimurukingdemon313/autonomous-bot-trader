"""Component versions (docs/VERSIONING.md).

Every behaviour change bumps the matching component. Every decision and
every experiment records `stamp()`, and results are analysed per version.
"""

from __future__ import annotations

from .agents.experimental_ai import EXPERIMENTAL_AI_VERSION
from .agents.llm_trader import LLM_TRADER_VERSION
from .agents.types import AGENT_VERSION
from .decision.edge_status import EDGE_STATUS_VERSION
from .decision.synthesis import DECISION_VERSION
from .execution.engine import EXECUTION_VERSION
from .features.store import FEATURE_VERSION
from .learning.experience import LEARNING_VERSION
from .learning.forward import FORWARD_VERSION
from .learning.metrics import METRICS_VERSION
from .learning.taxonomy import TAXONOMY_VERSION
from .learning.review import REVIEW_VERSION
from .llm.provider import PROMPT_VERSION
from .memory.patterns import MEMORY_VERSION
from .orchestrator.core import ORCHESTRATOR_VERSION
from .regime.model import REGIME_VERSION
from .research.labels import LABEL_VERSION
from .risk.engine import RISK_VERSION

DATA_VERSION = "data-1.0.0"


def stamp() -> dict[str, str]:
    """Every component whose behaviour can change a decision or its outcome."""
    return {"data": DATA_VERSION, "features": FEATURE_VERSION, "labels": LABEL_VERSION,
            "regime": REGIME_VERSION, "memory": MEMORY_VERSION, "agents": AGENT_VERSION,
            "prompt": PROMPT_VERSION, "decision": DECISION_VERSION, "risk": RISK_VERSION,
            "execution": EXECUTION_VERSION, "orchestrator": ORCHESTRATOR_VERSION,
            "learning": LEARNING_VERSION, "review": REVIEW_VERSION, "llm_trader": LLM_TRADER_VERSION,
            "experimental_ai": EXPERIMENTAL_AI_VERSION, "edge_status": EDGE_STATUS_VERSION,
            "forward": FORWARD_VERSION, "forward_metrics": METRICS_VERSION, "taxonomy": TAXONOMY_VERSION}
