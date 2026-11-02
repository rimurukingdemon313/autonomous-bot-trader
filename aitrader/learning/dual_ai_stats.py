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
from datetime import datetime, timezone

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
#: 1.6.0: an agreement's trade on Trader 2's own levels, followed forward in shadow since dual-ai 1.10.0 (the desk
#:        trades on Trader 1's), against the trade taken: H3 stays measured after its adoption.
#: 1.7.0: the agreements below the confidence floor (dual-ai 1.12.0), followed forward in shadow as the trades they
#:        would have been, beside the trades taken: the floor stays measured. LOW_CONFIDENCE counts as a decision
#:        with both traders.
#: 1.8.0: `instrument_record`, what the desk's agreements on one instrument did (by side, by the chart's timeframe,
#:        the latest ones), for the traders' journal (dual-ai 1.13.0).
#: 1.9.0: `analysis`, the desk's record analysed (owner, 2026-11-02: "the AI should analyse the past to get better, not
#:        memorise it"): every agreement split by one condition at a time (side, session, pair, timeframe, regime,
#:        volatility, the last H1 structure break and the regime's trend against the side, the lower confidence, the
#:        reward:risk, the stop in H1 ATR), the conditions that lost or worked clearly, and what a trade must win to
#:        pay at its reward:risk after costs.
#: 1.10.0: the time machine's verdict on an agreement's levels (dual-ai 1.16.0) is one of the conditions: whether its
#:         replays leaning toward the stop or the target tell anything about what then happened.
DUAL_AI_STATS_VERSION = "dual-ai-stats-1.10.0"
FAMILY, PICK_FAMILY, LOSER_FAMILY = "DUAL_AI", "DUAL_AI_DEBATE_PICK", "DUAL_AI_DEBATE_LOSER"
T2LEVELS_FAMILY = "DUAL_AI_T2_LEVELS"
LOWCONF_FAMILY = "DUAL_AI_LOW_CONFIDENCE"
#: the desk's agreements, followed forward: as proposed (taken, or refused by the risk engine) and, since dual-ai
#: 1.12.0, under the confidence floor. A shadow exit is the same agreement closed another way: never counted again.
AGREEMENTS = (FAMILY, LOWCONF_FAMILY)
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
    shadow: dict = {PICK_FAMILY: [], LOSER_FAMILY: [], LOWCONF_FAMILY: []}
    taken: dict = {}                                   # decision id -> (net R as taken, session)
    exits: dict = {n: {} for n in EXIT_FAMILIES.values()}  # variant -> {base decision id: net R}
    t2_levels: dict = {}  # agreement decision id -> net R on Trader 2's own levels (never traded)
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
        elif fam == T2LEVELS_FAMILY:
            t2_levels[str(r["decision_id"]).rsplit(":", 1)[0]] = float(out["net_r"])

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
    both = rules["AGREE"] + rules["DISAGREE"] + rules["DEBATE"] + rules["DEBATE_UNRESOLVED"] + rules["LOW_CONFIDENCE"]
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
            "trader2_levels_in_shadow": {**against_taken(t2_levels), "every_agreement": _r(list(t2_levels.values())),
                                         "note": "since dual-ai 1.10.0 a trade is on Trader 1's levels; the same "
                                                 "agreement on Trader 2's own levels, followed forward and never "
                                                 "traded. difference_r > 0 would mean Trader 2's levels did better"},
            "low_confidence_in_shadow": {**_r(shadow[LOWCONF_FAMILY]), "note": "since dual-ai 1.12.0 an agreement "
                                         "is a trade only when both traders state 65 or more; the agreements below, "
                                         "followed forward as the trades they would have been, after costs. Doing "
                                         "better than the trades taken would mean the floor costs money"},
            "exits_in_shadow": {**{n: against_taken(v) for n, v in exits.items()},
                                "note": "each trade taken, followed again under another exit on the same entry, "
                                        "after costs; difference_r > 0 means that exit would have done better "
                                        "on these trades. Measured, never traded"},
            "taken_by_session": {s: _r([r for r, ss in taken.values() if ss == s]) for s in SESSIONS},
            "decisions_by_rule": dict(sorted(rules.items())),
            "agreement_rate": round(rules["AGREE"] / both, 3) if both else None,
            "decisions_with_both_traders": both,
            "unavailable": sum(rules[k] for k in UNAVAILABLE)}


def instrument_record(db, symbol: str, as_of: int | None = None, partition_: str | None = "LEARNING",
                      last: int = 6) -> dict:
    """What the desk's agreements on one instrument did, each followed forward after costs: by side, by the chart's
    timeframe, and the latest few. Only outcomes resolved by `as_of`; LEARNING weeks only unless told otherwise, so
    an EVALUATION week is never learned from."""
    done = [r for r in ForwardLedger(db, lambda: as_of or 0).rows(as_of=as_of, partition_=partition_)
            if r.get("symbol") == symbol and r.get("family") in AGREEMENTS
            and (r.get("outcome") or {}).get("status") == "RESOLVED" and r["outcome"].get("net_r") is not None]

    def side(r) -> str:
        return "BUY" if r.get("side") == 1 else "SELL"

    def net(rs) -> list[float]:
        return [float(r["outcome"]["net_r"]) for r in rs]
    return {"version": DUAL_AI_STATS_VERSION, "instrument": symbol, "partition": partition_ or "ALL",
            "agreements": _r(net(done)),
            "by_side": {s: _r(net([r for r in done if side(r) == s])) for s in ("BUY", "SELL")},
            "by_timeframe": {tf: _r(net([r for r in done if r.get("timeframe") == tf]))
                             for tf in sorted({str(r.get("timeframe")) for r in done})},
            "latest": [{"decided_utc": datetime.fromtimestamp(int(r["t"]), timezone.utc).strftime("%Y-%m-%d %H:%M"),
                        "side": side(r), "timeframe": r.get("timeframe"), "net_r": round(float(r["outcome"]["net_r"]), 2),
                        "exit": r["outcome"].get("reason"), "traded": bool(r.get("executed")),
                        "desk_confidence": r.get("confidence")} for r in done[-last:]],
            "note": "every agreement of the desk on this instrument, followed forward after costs whether it was "
                    "traded or not; LEARNING weeks only; below 30 a figure is an anecdote (sample)"}


#: a condition is reported as having lost or worked when its agreements number at least ANALYSIS_MIN_N and their mean
#: net R is at least ANALYSIS_T standard errors from zero; at three or more, "strong". About forty conditions are
#: read, so one or two at |t| near 2 will be chance: the traders are told so.
ANALYSIS_MIN_N, ANALYSIS_T, ANALYSIS_STRONG_T = 20, 2.0, 3.0
#: conditions that depend on the side a trader chooses, and on the levels it places
SIDE_KEYS = ("side", "last_H1_structure_break", "regime_trend")
LEVEL_KEYS = ("lower_confidence", "reward_risk", "stop_in_h1_atr", "time_machine")


def _band(x, edges: tuple, fmt: str = "{:g}") -> str | None:
    if not isinstance(x, (int, float)) or isinstance(x, bool):
        return None
    lo = None
    for e in edges:
        if x < e:
            return f"under {fmt.format(e)}" if lo is None else f"{fmt.format(lo)} to {fmt.format(e)}"
        lo = e
    return f"{fmt.format(lo)} or more"


def with_or_against(direction, side: str) -> str:
    """Whether a side goes with or against a direction: "bullish"/"bearish" or +1/-1; "none" without one."""
    if direction in ("bullish", 1) or (isinstance(direction, (int, float)) and direction > 0):
        up = True
    elif direction in ("bearish", -1) or (isinstance(direction, (int, float)) and direction < 0):
        up = False
    else:
        return "none"
    return "with" if up == (side == "BUY") else "against"


def conditions(p: dict, d: dict) -> dict:
    """The conditions of one agreement: from its forward proposal `p` and its decision record `d`."""
    side = "BUY" if p.get("side") == 1 else "SELL"
    da = ((d.get("ai") or {}).get("dual_ai") or {})
    ctx = d.get("context") or {}
    c1, c2 = (da.get("trader1") or {}).get("confidence"), (da.get("trader2") or {}).get("confidence")
    low = min(c1, c2) if all(isinstance(c, (int, float)) and not isinstance(c, bool) for c in (c1, c2)) else None
    h1 = ((((ctx.get("market_map") or {}).get("structure") or {}).get("H1") or {}).get("last_break") or {})
    return {"side": side, "session": p.get("session"), "pair": p.get("symbol"), "timeframe": p.get("timeframe"),
            "regime": p.get("regime"), "volatility": p.get("vol_state"),
            "last_H1_structure_break": with_or_against(h1.get("direction"), side),
            "regime_trend": with_or_against((ctx.get("regime") or {}).get("trend_direction"), side),
            "lower_confidence": _band(low, (55, 60, 65, 70)),
            "reward_risk": _band(p.get("reward_risk"), (1.3, 1.6, 2.0)),
            "stop_in_h1_atr": _band(p.get("stop_atr"), (0.75, 1.25, 2.0)),
            "time_machine": (da.get("time_machine") or {}).get("verdict")}


def analysis(db, as_of: int | None = None, partition_: str | None = "LEARNING") -> dict:
    """The desk's record analysed: its agreements (each once), split by one condition at a time; the conditions that
    clearly lost or worked after costs; and the win rate a trade needs at its reward:risk. Only outcomes resolved by
    `as_of`; LEARNING weeks only unless told otherwise. Statistics, never a rule: nothing here refuses a trade."""
    done = [r for r in ForwardLedger(db, lambda: as_of or 0).rows(as_of=as_of, partition_=partition_)
            if r.get("family") in AGREEMENTS
            and (r.get("outcome") or {}).get("status") == "RESOLVED" and r["outcome"].get("net_r") is not None]
    ids = sorted({str(r["decision_id"]).split(":", 1)[0] for r in done})
    decisions: dict = {}
    for i in range(0, len(ids), 500):
        chunk = ids[i:i + 500]
        for row in db.query(f"SELECT id, payload FROM decisions WHERE id IN ({','.join('?' * len(chunk))})", tuple(chunk)):
            decisions[row["id"]] = json.loads(row["payload"])
    cells: dict = {}
    for r in done:
        net = float(r["outcome"]["net_r"])
        for k, v in conditions(r, decisions.get(str(r["decision_id"]).split(":", 1)[0]) or {}).items():
            if v is not None:
                cells.setdefault((k, v), []).append(net)
    notable = []
    for (k, v), xs in cells.items():
        n = len(xs)
        if n < ANALYSIS_MIN_N:
            continue
        mean = sum(xs) / n
        sd = (sum((x - mean) ** 2 for x in xs) / (n - 1)) ** 0.5
        t = mean / (sd / n ** 0.5) if sd > 0 else 0.0
        if abs(t) >= ANALYSIS_T:
            notable.append({"key": k, "value": v, "condition": f"{k} = {v}", "n": n,
                            "win_rate": round(sum(1 for x in xs if x > 0) / n, 3), "expectancy_r": round(mean, 3),
                            "t": round(t, 2), "strength": "strong" if abs(t) >= ANALYSIS_STRONG_T else "possible"})
    nets = [float(r["outcome"]["net_r"]) for r in done]
    rr = sorted(float(r["reward_risk"]) for r in done if isinstance(r.get("reward_risk"), (int, float)))
    costs = [float(r["outcome"]["cost_r"]) for r in done if isinstance(r["outcome"].get("cost_r"), (int, float))]
    need = None
    if rr and costs:
        med, c = rr[len(rr) // 2], sum(costs) / len(costs)
        need = {"median_reward_risk": round(med, 2), "mean_cost_r": round(c, 3),
                "win_rate_needed": round((1 + c) / (1 + med), 3),
                "rule": "a trade at reward:risk R, paying costs of c R, needs to win more than (1 + c) / (1 + R) of "
                        "the time to make money"}
    return {"version": DUAL_AI_STATS_VERSION, "partition": partition_ or "ALL", "agreements": _r(nets),
            "break_even": need,
            "lost": sorted((x for x in notable if x["t"] < 0), key=lambda x: x["t"]),
            "worked": sorted((x for x in notable if x["t"] > 0), key=lambda x: -x["t"]),
            "conditions_read": len(cells),
            "how_to_read": f"every agreement of the desk, followed forward after costs whether traded or not, split by "
                           f"one condition at a time; shown when {ANALYSIS_MIN_N}+ agreements are |t| >= {ANALYSIS_T:g} "
                           f"from zero. About {len(cells)} conditions are read, so one or two near t 2 will be chance. "
                           "A condition is a pattern of the past, not a rule: ask why it lost or worked, and whether "
                           "that cause is still there now"}
