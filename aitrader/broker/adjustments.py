"""Declared operator adjustments of the PAPER account.

The journal is append-only: a trade is never deleted from it. When the operator removes trades from the paper
account, they stay in the journal, labelled, and the balance is moved back by exactly their net P/L as the broker
booked it, once. Every report shows the adjustment next to the equity, with the equity it replaced.

An adjustment is declared here, in reviewed code: no request, dashboard control or model can make one. It applies
only when every trade it names is in this account's journal, closed, with a booked P/L and the rule it names;
otherwise nothing moves and the reason is reported. A deployment whose journal holds none of them (another account)
reads NOT_APPLICABLE.
"""

from __future__ import annotations

import json

from ..learning.paper_metrics import rule_of

ADJUSTMENTS_VERSION = "paper-adjustments-1.0.0"

#: The operator's request (2026-10-15): the 4 trades of the debate rule, which traded a disagreement until dual-ai
#: 1.2.0 stopped it, are removed from the paper account, which now measures the agreement rule. Their money returns.
DECLARED: tuple[dict, ...] = (
    {"id": "remove-retired-debate-rule-trades-2026-10-15", "rule": "DEBATE", "requested": "2026-10-15",
     "reason": "operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed "
               "from the paper account; they stay in the journal",
     "decision_ids": ("ea3d671b2daab0f128af67bc", "e5274d880fc3d2b5a155b156", "84ff17d2520ad60b7a8f52b8",
                      "61b50d48c7fd17eff3124309")},
)


def apply(broker, db, declared=None) -> list[dict]:
    """Apply each declared adjustment this account has not had yet; report every one."""
    declared = DECLARED if declared is None else declared
    out = []
    for adj in declared:
        if any(a["id"] == adj["id"] for a in broker.adjustments()):
            out.append({"id": adj["id"], "status": "ALREADY_APPLIED"})
            continue
        ids = tuple(adj["decision_ids"])
        rows: dict[str, list[dict]] = {}
        for i in ids:
            rows[i] = db.query("SELECT pnl, payload FROM trades WHERE decision_id=?", (i,))
        if not any(rows.values()):
            out.append({"id": adj["id"], "status": "NOT_APPLICABLE", "why": "none of its trades is in this journal"})
            continue
        why = []
        for i, rs in rows.items():
            if len(rs) != 1:
                why.append(f"{i}: {len(rs)} trades in the journal, expected 1")
                continue
            outcome = (json.loads(rs[0]["payload"]) or {}).get("outcome") or {}
            if rs[0]["pnl"] is None:
                why.append(f"{i}: no booked P/L")
            elif rule_of(outcome) != adj["rule"]:
                why.append(f"{i}: rule {rule_of(outcome)}, not {adj['rule']}")
        if why:
            out.append({"id": adj["id"], "status": "NOT_APPLIED", "why": "; ".join(why)})
            continue
        removed = sum(float(rs[0]["pnl"]) for rs in rows.values())
        applied = broker.adjust(adj["id"], -removed, adj["reason"],
                                {"rule": adj["rule"], "decision_ids": list(ids), "removed_pnl": removed,
                                 "requested": adj.get("requested"), "version": ADJUSTMENTS_VERSION})
        out.append({"id": adj["id"], "status": "APPLIED" if applied else "ALREADY_APPLIED", "amount": -removed})
    return out


__all__ = ["ADJUSTMENTS_VERSION", "DECLARED", "apply"]
