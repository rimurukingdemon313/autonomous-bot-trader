"""The history desk: what happened, after costs, in the past situations most like this one.

The language-model traders read it before deciding. It answers a question a
professional asks himself: "the last times the market looked like this,
what did a buy do, what did a sell do?" It does not decide anything.

Source: the dense reference memory (models/artifacts/history.npz, one
situation per H1 bar, 2007-2016, built by scripts/build_history.py and
verified against its card) or, when that is absent, the knowledge base
memory. Only outcomes already known at the decision time are used (the
memory's own point-in-time rule), and the sealed holdout was never read.

Honesty built in:
- every number is after spread, slippage and commission;
- the count of distinct episodes (pair, day) is given next to the count of
  neighbours, because consecutive hours share the same move;
- the note says what this is not: a forecast, or evidence of an edge.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..research.labels import TEMPLATE_BY_KEY
from .patterns import PatternMemory

HISTORY_DESK_VERSION = "history-desk-1.0.0"
NOTE = ("Results after costs of fixed trade types in the most similar past situations (2007-2016); "
        "not a forecast, and no edge on its own in testing (PR-001).")


def describe(action: str) -> str:
    key, side = action.split(":")
    t = TEMPLATE_BY_KEY[key]
    return f"{side}, stop {t.stop_atr:g} ATR, target {t.target_atr:g} ATR, closed after {t.max_bars} h at most"


class HistoryDesk:
    def __init__(self, memory: PatternMemory, source: str, k: int = 300) -> None:
        self.memory, self.source, self.k = memory, source, k

    def size(self) -> dict:
        n = len(self.memory)
        return {"source": self.source, "situations": n, "trades": n * len(self.memory.action_keys)}

    def brief(self, values: dict, t: int) -> dict:
        ev = self.memory.query(values, t, k=self.k)
        if ev is None:
            return {**self.size(), "available": False,
                    "reason": "no comparable past situations (incomplete features or too little history)"}
        return {
            **self.size(), "available": True, "note": NOTE,
            "neighbours": ev.k, "distinct_episodes": ev.distinct_episodes, "similarity": round(ev.similarity, 3),
            "median_age_days": round(ev.median_age_days) if ev.median_age_days == ev.median_age_days else None,
            "top_pair_share": round(ev.top_symbol_share, 2) if ev.top_symbol_share == ev.top_symbol_share else None,
            "trades": {a: {"what": describe(a), "win_rate": round(e.win_rate, 3), "avg_R": round(e.mean_r, 3),
                           "median_R": round(e.median_r, 3),
                           # the bound treats each distinct episode, not each overlapping hour, as one observation
                           "avg_R_lower_bound": round(float(e.mean_r) - 1.28 * e.se * (ev.k / max(1, ev.distinct_episodes or ev.k)) ** 0.5, 3)}
                       for a, e in ev.actions.items()},
            "closest_examples": [{"pair": x["symbol"],
                                  "date": datetime.fromtimestamp(x["time"], timezone.utc).strftime("%Y-%m-%d %H:%M"),
                                  "results_R": x["outcomes"]} for x in ev.examples],
        }
