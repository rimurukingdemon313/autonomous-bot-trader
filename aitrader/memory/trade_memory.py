"""The language-model trader's memory of its own trades, as it reads it before every decision.

It is built from the immutable journal, never from free-floating notes:

- its closed trades (trades table): thesis, levels, exit, realised R, the
  deterministic post-mortem cause;
- its own reflection on each of them (reflections table, kind "trade"),
  written after the trade closed;
- the validated lessons the evidence-gated lifecycle has confirmed;
- its record so far: trades, win rate, average R, reported as "insufficient"
  below 30 trades, because a win rate over a handful of trades says nothing.

Retrieval favours what is relevant now: trades on this instrument, trades in
this regime, and its most recent losses. The brief stays short, a dozen
trades at most, so the model reads its mistakes rather than a log.
Everything here happened before the decision it informs: memory is journal
history, and the journal only grows forward.
"""

from __future__ import annotations

import json

LLM_FAMILY = "LLM_TRADER"
MAX_TRADES = 12


def _trade_view(row: dict, reflections: dict[str, dict]) -> dict:
    p = json.loads(row["payload"])
    dec, pos, ex = p.get("decision") or {}, p.get("position") or {}, p.get("exit") or {}
    refl = reflections.get(dec.get("id") or "")
    return {
        "symbol": row["symbol"], "side": pos.get("side"), "opened": pos.get("opened"),
        "entry": pos.get("entry"), "stop": pos.get("stop"), "target": pos.get("target"),
        "exit_reason": ex.get("reason"), "R": round(row["r"], 3) if row["r"] is not None else None,
        "regime_at_entry": ((dec.get("regime") or {}).get("label")),
        "thesis": (dec.get("thesis") or "")[:300],
        "post_mortem_cause": (p.get("postmortem") or {}).get("cause"),
        "my_reflection": (refl or {}).get("text"),
        "my_lesson": (refl or {}).get("lesson"),
    }


class TradeMemory:
    def __init__(self, db, knowledge=None) -> None:
        self.db, self.knowledge = db, knowledge

    def _rows(self) -> list[dict]:
        rows = self.db.query("SELECT symbol, r, payload FROM trades ORDER BY seq")
        return [r for r in rows if (json.loads(r["payload"]).get("decision") or {}).get("family") == LLM_FAMILY]

    def _reflections(self) -> dict[str, dict]:
        out = {}
        for r in self.db.query("SELECT payload FROM reflections ORDER BY seq"):
            p = json.loads(r["payload"])
            if p.get("kind") == "trade" and p.get("decision_id"):
                out[p["decision_id"]] = p
        return out

    def record(self) -> dict:
        rs = [r["r"] for r in self._rows() if r["r"] is not None]
        n = len(rs)
        if not n:
            return {"trades": 0, "sample": "none"}
        return {"trades": n, "win_rate": round(sum(1 for x in rs if x > 0) / n, 3),
                "avg_R": round(sum(rs) / n, 3), "total_R": round(sum(rs), 2),
                "sample": "insufficient" if n < 30 else "adequate"}

    def brief(self, symbol: str, regime: str, t: int) -> dict:
        rows = self._rows()
        refl = self._reflections()
        views = [_trade_view(r, refl) for r in rows]
        picked: list[dict] = []
        seen: set = set()

        def take(items, k):
            for v in items[-k:]:
                key = (v["symbol"], v["opened"])
                if key not in seen and len(picked) < MAX_TRADES:
                    seen.add(key)
                    picked.append(v)

        take([v for v in views if v["R"] is not None and v["R"] < 0], 4)          # recent mistakes first
        take([v for v in views if v["symbol"] == symbol], 4)                       # this instrument
        take([v for v in views if v["regime_at_entry"] == regime], 4)             # this kind of market
        lessons = []
        if self.knowledge is not None and hasattr(self.knowledge, "lessons"):
            for versions in self.knowledge.lessons.values():
                cur = versions[-1] if versions else None
                if cur and cur.get("status") == "VALIDATED" and cur.get("effective", 0) <= t:
                    lessons.append(cur.get("statement"))
        return {"my_record": self.record(), "relevant_past_trades": picked, "validated_lessons": lessons[:10]}
