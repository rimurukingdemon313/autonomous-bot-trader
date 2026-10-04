"""Edge status: what kind of evidence stands behind a decision. Set once, at decision time.

    VALIDATED     a promoted edge (models/artifacts/promoted_edges.json) whose record says VALIDATED
                  and whose health is HEALTHY: it passed preregistered out-of-sample research AND an
                  untouched evaluation period, and an operator promoted it.
    PROMISING     a promoted edge whose record says PROMISING: measured, positive, short of validation.
    EXPERIMENTAL  every other trade proposal: the analogue synthesis (PR-001 failed its validation),
                  the language-model trader, the trading room, the experimental AI mode. A model's
                  stated confidence is never evidence: "95% sure" is a sentence, not a sample.
    NONE          not a trade.

The status only ever comes from the promoted-edge file, which only research and an operator write.
Forward results can make a family ELIGIBLE for review (learning/forward.py) but never relabel a
decision by themselves: promotion is a reviewed, versioned act.

Execution policy (one definition, used by the orchestrator and checked again by the execution
engine): VALIDATED may execute; anything else executes only on the PAPER broker or when the
operator has set EXPERIMENTAL_EXECUTE=true for DEMO. Otherwise it is SHADOW: recorded, priced
by the risk engine, followed forward, and never sent.
"""

from __future__ import annotations

EDGE_STATUS_VERSION = "edge-status-1.0.0"
EDGE_STATUSES = ("VALIDATED", "PROMISING", "EXPERIMENTAL", "NONE")

SIGNAL_CLASS = {"evidence": "EVIDENCE", "llm_trader": "LLM_TRADER", "trading_room": "TRADING_ROOM",
                "edges": "EDGE", "experimental_ai": "EXPERIMENTAL_AI"}


def classify(decision, decision_mode: str, promoted: list | None = None) -> str:
    """The decision's edge status. Unknown or missing evidence is EXPERIMENTAL, never VALIDATED."""
    if decision.decision not in ("BUY", "SELL"):
        return "NONE"
    if decision_mode != "edges":
        return "EXPERIMENTAL"  # no model or analogue path has validated forward evidence
    edge_id = next((s.get("edge_id") for s in decision.supporting_evidence or [] if isinstance(s, dict)
                    and s.get("edge_id")), None)
    edge = next((e for e in promoted or [] if e.edge_id == edge_id), None)
    if edge is None:
        return "EXPERIMENTAL"
    if edge.status == "VALIDATED" and edge.health == "HEALTHY":
        return "VALIDATED"
    if edge.status in ("VALIDATED", "PROMISING"):
        return "PROMISING"  # a validated edge whose health has degraded is no longer treated as validated
    return "EXPERIMENTAL"


def execution_route(edge_status: str, mode: str, experimental_execute: bool) -> str:
    """EXECUTE | SHADOW | NONE for one decision. LIVE does not exist here: config refuses it, and any
    mode this function does not know is SHADOW (fail closed). BACKTEST is a simulation, like PAPER."""
    if edge_status == "NONE":
        return "NONE"
    if mode not in ("PAPER", "BACKTEST", "DEMO"):
        return "SHADOW"
    if edge_status == "VALIDATED":
        return "EXECUTE"
    if mode in ("PAPER", "BACKTEST") or (mode == "DEMO" and experimental_execute):
        return "EXECUTE"
    return "SHADOW"
