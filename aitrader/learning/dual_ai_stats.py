"""What the dual-AI desk's own record says: measured from the journal, never estimated.

- `evaluate_trade`: one closed DUAL_AI trade scored per trader (was each trader's side right, was the target
  reached, R, MFE/MAE), and which rule produced it (AGREE; DEBATE for trades of dual-ai 1.1.0).
- `record`: closed DUAL_AI trades (win rate, expectancy in R, profit factor), split by rule and by the desk's
  confidence; each trader's hit rate on closed trades; on each disagreement (no trade since dual-ai 1.2.0), the
  side the shadow debate picked and the side it rejected, both followed forward as if taken (what did standing
  aside skip? did the debate choose the better side?); how often each rule decided. Every figure carries its
  sample size and label ("insufficient" below 30).

Trader 2 and the debate read `record(..., partition_="LEARNING")`: outcomes of LEARNING weeks only, known before
the decision, so forward evaluation is never learned from. Nothing here changes a rule, a size or a limit.
"""

from __future__ import annotations

import json
from collections import Counter

from ..learning.forward import ForwardLedger, partition
from ..learning.paper_metrics import MIN_SAMPLE

#: 1.1.0: the shadow debate's pick on a disagreement is measured beside the side it rejected; DISAGREE counts as a
#:        decision with both traders.
#: 1.2.0: each trade records how Trader 1 read the chart (image, or its numbers when no vision model answered);
#:        trades are split by it.
#: 1.3.0: the trades taken beside their shadow exits (break-even at +1R, held 24 h, twice as wide), paired on the
#:        same entries; the trades taken by session.
#: 1.4.0: NOT_ASKED (dual-ai 1.6.0's name for a decision refused before the traders were asked) counts as
#:        unavailable, as MARKET_UNAVAILABLE did before it.
#: 1.5.0: the shadow exit closed at 8 h (HOLD8H, forward 1.2.0) beside the others: the exit before dual-ai 1.7.0.
DUAL_AI_STATS_VERSION = "dual-ai-stats-1.5.0"
FAMILY, PICK_FAMILY, LOSER_FAMILY = "DUAL_AI", "DUAL_AI_DEBATE_PICK", "DUAL_AI_DEBATE_LOSER"
EXIT_FAMILIES = {f"{FAMILY}_EXIT_{n}": n for n in ("BE1R", "HOLD24H", "WIDE2X", "HOLD8H")}
SESSIONS = ("ASIA", "LONDON", "OVERLAP", "NEW_YORK", "LATE")
BANDS = ((0, 50), (50, 65), (65, 80), (80, 101))
UNAVAILABLE = ("NOT_ASKED", "MARKET_UNAVAILABLE", "AI_UNAVAILABLE", "NO_CHART", "TRADER1_UNAVAILABLE",
               "TRADER2_UNAVAILABLE", "DEBATE_UNRESOLVED", "MODE")


def _sample(n: int) -> str:
    return "none" if n == 0 else "insufficient" if n < MIN_SAMPLE else "adequate"


def _r(rs: list[float]) -> dict:
    n = len(rs)
    if not n:
        return {"n": 0, "sample": "none"}
    gain, loss = sum(x for x in rs if x > 0), -sum(x for x in rs if x <= 0)
    return {"n": n, "sample": _sample(n), "win_rate": round(sum(1 for x in rs if x > 0) / n, 3),
            "expectancy_r": round(sum(rs) / n, 3), "total_r": round(sum(rs), 2),
            "profit_factor_r": round(gain / loss, 3) if loss > 0 else None}


def _rate(flags: list) -> dict:
    xs = [f for f in flags if f is not None]
    return {"n": len(xs), "sample": _sample(len(xs)), "rate": round(sum(xs) / len(xs), 3) if xs else None}


def evaluate_trade(ai_record: dict, outcome: dict) -> dict:
    """One closed dual-AI trade, scored for each trader from what actually happened."""
    t1, t2 = ai_record.get("trader1") or {}, ai_record.get("trader2") or {}
    cons = ai_record.get("consensus") or {}
    final = cons.get("direction")
    moved = outcome.get("prediction_correct")  # the price moved the traded way, before costs

    def right(t):
        return None if moved is None or t.get("direction") not in ("BUY", "SELL") else (t["direction"] == final) == moved

    reason = outcome.get("exit_reason")
    return {"version": DUAL_AI_STATS_VERSION, "models": ai_record.get("models"), "rule": cons.get("rule"),
            "levels_from": cons.get("levels_from"), "desk_confidence": cons.get("desk_confidence"),
            "trader1_direction": t1.get("direction"), "trader1_confidence": t1.get("confidence"),
            "trader2_direction": t2.get("direction"), "trader2_confidence": t2.get("confidence"),
            "verifier_direction": (ai_record.get("verifier") or {}).get("direction"),
            "trader1_input": ai_record.get("trader1_input") or "image",
            "direction_correct": moved, "trader1_correct": right(t1), "trader2_correct": right(t2),
            "target_reached": reason == "TARGET", "stopped_out": reason == "STOP", "exit_reason": reason,
            "net_r": outcome.get("r"), "mfe_r": outcome.get("mfe_r"), "mae_r": outcome.get("mae_r"),
            "regime": ai_record.get("regime"), "vol_state": ai_record.get("vol_state"),
            "hold_minutes": ai_record.get("hold_minutes")}


def record(db, as_of: int | None = None, partition_: str | None = None) -> dict:
    trades = []
    for row in db.query("SELECT payload FROM trades ORDER BY seq"):
        p = json.loads(row["payload"])
        o = p.get("outcome") or {}
        if (p.get("decision") or {}).get("family") != FAMILY or o.get("r") is None:
            continue
        if as_of is not None and (o.get("closed") or 0) > as_of:
            continue
        if partition_ and partition(int(o.get("opened") or 0)) != partition_:
            continue
        trades.append(o)
    ev = [o.get("dual_ai") or {} for o in trades]
    bands = {}
    for lo, hi in BANDS:
        sel = [o["r"] for o, e in zip(trades, ev) if isinstance(e.get("desk_confidence"), (int, float))
               and lo <= 100 * e["desk_confidence"] < hi]
        bands[f"{lo}-{min(hi, 100)}"] = _r(sel)
    shadow: dict = {PICK_FAMILY: [], LOSER_FAMILY: []}
    taken: dict = {}                                   # decision id -> (net R as taken, session)
    exits: dict = {n: {} for n in EXIT_FAMILIES.values()}  # variant -> {base decision id: net R}
    for r in ForwardLedger(db, lambda: as_of or 0).rows(as_of=as_of, partition_=partition_):
        out = r.get("outcome") or {}
        if out.get("status") != "RESOLVED" or out.get("net_r") is None:
            continue
        fam = r.get("family")
        if fam in shadow:
            shadow[fam].append(float(out["net_r"]))
        elif fam == FAMILY and r.get("route") == "EXECUTE" and r.get("executed"):
            taken[r["decision_id"]] = (float(out["net_r"]), r.get("session"))
        elif fam in EXIT_FAMILIES and r.get("base_decision_id"):
            exits[EXIT_FAMILIES[fam]][r["base_decision_id"]] = float(out["net_r"])

    def against_taken(variant: dict) -> dict:
        pairs = [(taken[k][0], v) for k, v in variant.items() if k in taken]
        st = _r([v for _, v in pairs])
        if pairs:
            st["as_taken_expectancy_r"] = round(sum(a for a, _ in pairs) / len(pairs), 3)
            st["difference_r"] = round(sum(v - a for a, v in pairs) / len(pairs), 3)
        return st
    rules: Counter = Counter()
    for row in db.query("SELECT payload FROM decisions ORDER BY seq"):
        p = json.loads(row["payload"])
        if p.get("family") != FAMILY or (as_of is not None and (p.get("timestamp") or 0) > as_of):
            continue
        if partition_ and partition(int(p.get("timestamp") or 0)) != partition_:
            continue
        rules[(((p.get("ai") or {}).get("dual_ai") or {}).get("consensus") or {}).get("rule") or "?"] += 1
    both = rules["AGREE"] + rules["DISAGREE"] + rules["DEBATE"] + rules["DEBATE_UNRESOLVED"]
    return {"version": DUAL_AI_STATS_VERSION, "partition": partition_ or "ALL",
            "trades_taken": _r([o["r"] for o in trades]),
            "by_rule": {k: _r([o["r"] for o, e in zip(trades, ev) if e.get("rule") == k]) for k in ("AGREE", "DEBATE")},
            "by_desk_confidence": bands,
            "by_trader1_input": {k: _r([o["r"] for o, e in zip(trades, ev) if (e.get("trader1_input") or "image") == k])
                                 for k in ("image", "numbers")},
            "trader1_hit_rate": _rate([e.get("trader1_correct") for e in ev]),
            "trader2_hit_rate": _rate([e.get("trader2_correct") for e in ev]),
            "debate_pick_if_taken": {**_r(shadow[PICK_FAMILY]), "note": "on a disagreement (not traded), the side "
                                     "the shadow debate picked, followed forward as if taken, after costs: what "
                                     "standing aside skipped"},
            "debate_losing_side_if_taken": {**_r(shadow[LOSER_FAMILY]), "note": "the side the debate rejected, "
                                            "followed forward as if taken, after costs: if it does better than the "
                                            "side picked, the debate is choosing the wrong side"},
            "exits_in_shadow": {**{n: against_taken(v) for n, v in exits.items()},
                                "note": "each trade taken, followed again under another exit on the same entry, "
                                        "after costs; difference_r > 0 means that exit would have done better "
                                        "on these trades. Measured, never traded"},
            "taken_by_session": {s: _r([r for r, ss in taken.values() if ss == s]) for s in SESSIONS},
            "decisions_by_rule": dict(sorted(rules.items())),
            "agreement_rate": round(rules["AGREE"] / both, 3) if both else None,
            "decisions_with_both_traders": both,
            "unavailable": sum(rules[k] for k in UNAVAILABLE)}
