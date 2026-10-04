"""DECISION_MODE=experimental_ai: a model proposes, independent specialists challenge, rules decide.

EXPERIMENTAL by construction. No validated edge exists (docs/FINAL_RESEARCH_REPORT.md), so every
trade this mode produces carries edge status EXPERIMENTAL and signal class EXPERIMENTAL_AI. In
DEMO it is SHADOW (recorded, priced by the risk engine, followed forward, never sent) unless the
operator sets EXPERIMENTAL_EXECUTE=true; on the PAPER broker it executes as simulation. It can
never become live: there is no live path (execution/engine.py, service/config.py).

1. PROPOSER (the first configured provider): the language-model trader's prompt and reply schema
   (agents/llm_trader.py): BUY / SELL / NO_TRADE / UNCERTAIN with levels, confidence, evidence,
   reasons against, invalidation, regime and analogues. Malformed -> NO_TRADE.
2. SPECIALISTS (AI_SPECIALISTS, default "adversary"; each on a provider other than the proposer's
   when one is configured, so a second mind is a different model): MARKET STRUCTURE, QUANT,
   PRICE ACTION, MACRO/NEWS, ADVERSARIAL/RISK. Each reads the same packet and the proposal and
   answers AGREE / DISAGREE / UNCERTAIN with objections from the closed vocabulary. They cannot
   change a level, a size or the direction; they can only object.
3. SYNTHESIS, deterministic, not a vote:
   - a specialist that did not answer validly -> NO_TRADE (fail closed);
   - any BLOCKING objection -> NO_TRADE;
   - two or more MAJOR objections in total -> NO_TRADE;
   - at least half of the non-adversarial specialists name the opposite direction -> NO_TRADE
     (recorded as UNCERTAIN: the specialists disagree on direction);
   - otherwise the proposal, verbatim, goes to the same risk engine as everything else.
   The disagreement rate (specialists not agreeing) is recorded on every decision and measured.

The model's confidence is recorded and calibrated forward; it never sizes, prices or approves.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from ..decision.synthesis import Decision, decision_id
from .llm_trader import (
    LLM_TRADER_VERSION, SYSTEM, agent_digest, call_record, compact_packet, hold_minutes, lesson_block, level_problem,
    market_packet, model_view, no_trade_decision, pre_model_block, trade_decision, validate_trader_reply,
)
from .types import OBJECTION_CODES, SEVERITIES, MarketContext

EXPERIMENTAL_AI_VERSION = "experimental-ai-1.0.0"
FAMILY = "EXPERIMENTAL_AI"

SPECIALISTS = {
    "structure": "You are the MARKET STRUCTURE specialist: swings, BOS/CHoCH, order blocks, fair value gaps, "
                 "liquidity pools and sweeps, higher-timeframe structure.",
    "quant": "You are the QUANT specialist: base rates, the history desk, the strategy desk scoreboard, "
             "volatility, costs against the stop, and whether the expected R survives them.",
    "price_action": "You are the PRICE ACTION specialist: candles, momentum, rejection, follow-through on "
                    "the completed bars of every timeframe.",
    "macro": "You are the MACRO/NEWS specialist: the economic calendar, event risk, intermarket context "
             "(dollar, yields, gold, equities) and the trading session.",
    "adversary": "You are the ADVERSARIAL/RISK specialist: assume the proposed trade is wrong and find why: "
                 "fake breakout, liquidity trap, weak structure, overextension, event risk, costs, stale data.",
}

CHALLENGE = """{role}
A colleague proposed the trade in "proposal". The decision time is {time}; treat it as the present and do not use
any knowledge of prices or events after it. Use ONLY the data in the JSON. You cannot change the levels, the size
or the direction: judge the proposal. Reply with ONE JSON object only:
{{"verdict": "AGREE|DISAGREE|UNCERTAIN", "direction": "BUY|SELL|NONE",
  "objections": [{{"code": "<one of: {codes}>", "severity": "BLOCKING|MAJOR|MINOR", "reason": "..."}}],
  "summary": "at most 3 sentences"}}"""


def validate_challenge(d: dict) -> str | None:
    if d.get("verdict") not in ("AGREE", "DISAGREE", "UNCERTAIN"):
        return "verdict must be AGREE, DISAGREE or UNCERTAIN"
    if d.get("direction", "NONE") not in ("BUY", "SELL", "NONE"):
        return "direction must be BUY, SELL or NONE"
    objs = d.get("objections", [])
    if not isinstance(objs, list) or len(objs) > 8:
        return "objections must be a list of at most 8"
    for o in objs:
        if not isinstance(o, dict) or o.get("code") not in OBJECTION_CODES or o.get("severity") not in SEVERITIES:
            return "each objection needs a known code and severity"
    if not isinstance(d.get("summary", ""), str):
        return "summary must be text"
    return None


@dataclass(frozen=True)
class ExperimentalConfig:
    specialists: tuple[str, ...] = ("adversary",)

    def __post_init__(self) -> None:
        bad = [s for s in self.specialists if s not in SPECIALISTS]
        if bad:
            raise ValueError(f"AI_SPECIALISTS: unknown role(s) {bad}; known: {', '.join(SPECIALISTS)}. "
                             "An unknown role is refused, never ignored")

    @classmethod
    def from_env(cls, env: dict | None = None) -> "ExperimentalConfig":
        e = os.environ if env is None else env
        raw = e.get("AI_SPECIALISTS")
        roles = ("adversary",) if raw is None else tuple(r.strip().lower() for r in raw.split(",") if r.strip())
        return cls(roles)


def synthesize(proposal_action: str, answers: dict[str, dict]) -> tuple[str | None, dict]:
    """(reason to refuse or None, summary). Pure and deterministic: the specialists' answers in, a rule out."""
    blocking, major, opposite, others = [], [], [], []
    want = proposal_action
    against = "SELL" if want == "BUY" else "BUY"
    for role, a in answers.items():
        for o in a.get("objections", []):
            (blocking if o["severity"] == "BLOCKING" else major if o["severity"] == "MAJOR" else []).append(
                f"{role}: {o['code']} ({str(o.get('reason') or '')[:120]})")
        if role != "adversary":
            others.append(role)
            if a.get("direction") == against:
                opposite.append(role)
    n = len(answers)
    summary = {"blocking": blocking, "major": major, "opposite_direction": opposite,
               "disagreement": round(sum(a.get("verdict") != "AGREE" for a in answers.values()) / n, 3) if n else None,
               "verdicts": {r: a.get("verdict") for r, a in answers.items()}}
    if blocking:
        return "specialist BLOCKING objection: " + "; ".join(blocking[:3]), summary
    if len(major) >= 2:
        return f"{len(major)} MAJOR objections: " + "; ".join(major[:3]), summary
    if others and len(opposite) * 2 >= len(others) and opposite:
        return f"UNCERTAIN: specialists {', '.join(opposite)} name the opposite direction", summary
    return None, summary


class ExperimentalAI:
    def __init__(self, llm, config: ExperimentalConfig | None = None) -> None:
        self.llm = llm
        self.config = config or ExperimentalConfig()

    def _second(self, first_provider: str | None) -> str | None:
        """A provider other than the proposer's, when one is configured: a second model, not an echo."""
        names = [ep.name for ep in self.llm.config.endpoints()] if self.llm is not None else []
        other = [n for n in names if n != first_provider]
        return other[0] if other else None

    def decide(self, ctx: MarketContext, reports: dict, versions: dict, llm_opinions=None) -> Decision:
        if ctx.mode == "BACKTEST":
            raise ValueError("the experimental AI cannot be backtested honestly: the models may know what "
                             "happened after the decision time")
        v = {**versions, "llm_trader": LLM_TRADER_VERSION, "experimental_ai": EXPERIMENTAL_AI_VERSION}
        did = decision_id(ctx.symbol, ctx.timeframe, ctx.t, ctx.mode, v)
        agents = agent_digest(reports)

        def no_trade(reason: str, ai: dict, verdict: str | None, contra=None, evidence=None) -> Decision:
            d = no_trade_decision(ctx, did, v, agents, reason, contra, evidence=evidence)
            d.family, d.ai, d.ai_verdict = FAMILY, ai, verdict
            return d

        blocked = pre_model_block(ctx, reports, self.llm)
        if blocked:
            return no_trade(blocked[0], {}, None, contra=blocked[1])
        packet = market_packet(ctx, reports)
        system = SYSTEM.format(time=packet["decision_time"]) + (
            "\nThis is an EXPERIMENTAL forward test of your judgement: no edge has been validated, and every "
            "proposal you make is measured after costs against what the market then did.")
        res = self.llm.complete_json("experimental:proposer", system, packet, validate_trader_reply,
                                     cache_key=f"{ctx.symbol}|{ctx.t}|xai", shrink=compact_packet)
        ai: dict = {"proposer": call_record(res), "specialists": {}}
        ai.update({k: ai["proposer"][k] for k in ("provider", "model", "status", "latency_ms", "tokens")})
        if not res.ok:
            return no_trade(f"proposer unavailable or reply rejected ({res.status}): failing closed", ai, None)
        p = res.data
        ai["view"] = model_view(p)
        if p["action"] in ("NO_TRADE", "UNCERTAIN"):
            return no_trade(f"proposer {p['action']}: {str(p.get('thesis') or '')[:400]}", ai, p["action"])
        problem = level_problem(ctx, p)
        if problem:
            return no_trade(problem, ai, "TRADE")
        hit = lesson_block(ctx, 1 if p["action"] == "BUY" else -1)
        if hit:
            return no_trade(f"validated lesson {hit['lesson_id']}: {hit['statement']}", ai, "TRADE",
                            contra=[{"code": "LESSON_MATCH", "severity": "BLOCKING", "message": hit["statement"]}])

        proposal = {k: p.get(k) for k in ("action", "timeframe", "stop", "target", "max_hold_minutes", "thesis",
                                          "invalidation", "confidence", "expected_r", "evidence", "reasons_against",
                                          "method")}
        second = self._second(ai["proposer"]["provider"])
        answers: dict[str, dict] = {}
        for role in self.config.specialists:
            sys_ = CHALLENGE.format(role=SPECIALISTS[role], time=packet["decision_time"], codes=", ".join(OBJECTION_CODES))
            r = self.llm.complete_json(f"specialist:{role}", sys_, {**packet, "proposal": proposal}, validate_challenge,
                                       cache_key=f"{ctx.symbol}|{ctx.t}|xai|{role}", only=second, shrink=compact_packet)
            if not r.ok and second is not None:  # that provider failed: any configured model may answer
                r = self.llm.complete_json(f"specialist:{role}", sys_, {**packet, "proposal": proposal},
                                           validate_challenge, cache_key=f"{ctx.symbol}|{ctx.t}|xai|{role}|any",
                                           shrink=compact_packet)
            ai["specialists"][role] = {**call_record(r), "answer": r.data if r.ok else None}
            if not r.ok:
                return no_trade(f"specialist '{role}' unavailable or reply rejected ({r.status}): failing closed",
                                ai, "TRADE")
            answers[role] = r.data
        refuse, summary = synthesize(p["action"], answers)
        ai["synthesis"] = summary
        ai["disagreement"] = summary["disagreement"]
        if refuse:
            verdict = "UNCERTAIN" if refuse.startswith("UNCERTAIN") else "TRADE"
            contra = [{"agent": f"specialist:{role}", "code": o["code"], "severity": o["severity"],
                       "message": str(o.get("reason") or "")[:200]} for role, a in answers.items()
                      for o in a.get("objections", [])][:12]
            return no_trade(refuse, ai, verdict, contra=contra)
        support = [{"agent": "experimental:proposer", "claim": str(p.get("thesis") or "")[:300], "model": res.model}]
        support += [{"agent": f"specialist:{role}", "claim": f"{a['verdict']}: {str(a.get('summary') or '')[:200]}"}
                    for role, a in answers.items()]
        d = trade_decision(ctx, did, v, agents, reports, p, support,
                           evidence={"specialists": {r: a.get("verdict") for r, a in answers.items()},
                                     "max_hold_minutes": hold_minutes(p)})
        d.family, d.ai, d.ai_verdict = FAMILY, ai, "TRADE"
        return d
