"""DECISION_MODE=edges: the edge engine's BUY / SELL / ABSTAIN as a Decision the Risk Engine can judge."""

from __future__ import annotations

from ..decision.edge_engine import EDGE_ENGINE_VERSION, evaluate
from ..decision.synthesis import Decision, decision_id
from .types import MarketContext

FAMILY = "EDGE"


def edge_decision(ctx: MarketContext, versions: dict, edges: list) -> Decision:
    v = {**versions, "edge_engine": EDGE_ENGINE_VERSION}
    did = decision_id(ctx.symbol, ctx.timeframe, ctx.t, ctx.mode, v)
    cost_atr = None  # commission/slippage are in the spread check and the edge's tested cost
    res = evaluate(edges, ctx.symbol, ctx.t, ctx.frames, ctx.bid, ctx.ask, ctx.exec_atr or ctx.atr, cost_atr,
                   open_symbols=set(ctx.open_symbols))
    evidence = {"edge_engine": res}
    if res["decision"] == "ABSTAIN":
        return Decision(did, "NO_TRADE", ctx.symbol, ctx.timeframe, ctx.t, ctx.mode, {}, ctx.regime.as_dict(),
                        res["reason"], [], [], None, None, None, None, None, FAMILY, None, None, None, None, None,
                        None, None, None, "ABSTAIN: " + res["reason"], {}, evidence, len(res["candidates"]), v)
    c = res["chosen"]
    return Decision(did, c["side"], ctx.symbol, ctx.timeframe, ctx.t, ctx.mode, {}, ctx.regime.as_dict(),
                    res["reason"], [{"edge_id": c["edge_id"], "trial": c["trial"], "oos_mean_R": c["oos_mean_R"],
                                     "oos_n": c["oos_n"], "evidence": c["evidence"]}], [],
                    c["entry"], c["stop"], c["target"], f"edge {c['edge_id']}: stop, target, time exit",
                    None, FAMILY, c["score_R"], None, c["score_R"], c["score_R"], 0.0, None, 1.0,
                    "the stop, or the time exit", None, {}, evidence, len(res["candidates"]), v,
                    max_hold_minutes=c["max_hold_minutes"])
