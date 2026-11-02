"""The desk's playbook (dual-ai 1.18.0): what this project has learned, written down for every model that sits at the
desk: both traders, the shadow debate and the senior trader.

The owner, 2026-11-02: "I want the AI not only trained by its company: it must know all the steps we have learned".
A model's own training knows trading in general; this is what THIS desk learned, trading on paper since October 2026.

Every line is one of three things, and says which:
- a rule the code enforces (the desk's rule, the risk engine's refusals, the time exit);
- a finding of the desk's own forward record, with its date and sample (docs/DUAL_AI.md);
- a result of the research behind the desk (docs/DUAL_AI.md, research/).

Nothing here refuses, sizes or places a trade: the rules it quotes are enforced by the code whatever a model makes of
them. It is static by design. The live record is in "desk_memory", and where the two differ the live figures are the
newer. Change it only by a code change that says why, and bump PLAYBOOK_VERSION.
"""

from __future__ import annotations

PLAYBOOK_VERSION = "playbook-1.0.0"


def build(min_confidence: int, hold_hours: int) -> dict:
    """The playbook, with the desk's own numbers filled in from the code that enforces them."""
    return {
        "version": PLAYBOOK_VERSION,
        "how_to_use": (
            "What this desk has learned since it began trading on paper in October 2026: its rules, the lessons of its "
            "own forward record, and the research behind it. Read it as an experienced colleague's notes. Weigh each "
            "point against the data in front of you, and say when it applies and when its cause is absent. The live "
            "record in desk_memory is newer: where the two differ, the live figures win."),
        "the_desk_rules": [
            "A paper account: never real money.",
            f"A trade needs both traders on the same side, each at a confidence of {min_confidence} or more. It is "
            "placed on Trader 1's levels. While a senior trader is declared, it also needs the senior's approval. "
            "The senior can only refuse; it cannot change a side, a level or a size.",
            "The risk engine, not a model, sizes every trade and may refuse it. Its limits for this decision are in "
            "costs.risk_engine_limits. It refuses a reward:risk or a stop below its minimum, costs too large a share "
            "of the stop, a stale quote at the opening, a news window, too many open positions, a currency already "
            "held twice, and a trade that bets against a position already open.",
            f"A trade is held up to {hold_hours} h on the H1 chart, and closed by 16:00 New York on Friday. Nothing is "
            "held over a weekend.",
            "NO TRADE is a normal answer and often the best one: standing aside loses nothing. A trader stands aside "
            "by stating a low confidence; the senior, by VETO.",
        ],
        "what_the_record_taught": [
            "Costs, not direction, were the loss on M15. Over 479 agreements followed forward, the desk earned "
            "+0.06 R a trade before costs and paid 0.19 R in them (October). That is why the desk moved to H1 "
            "(dual-ai 1.11.0): a wider stop makes the same costs a smaller share of the risk.",
            "The first fourteen closed trades (14 October): the losers went wrong at once, their best point at most "
            "+0.16 R. The winners all reached +1.2 R or more, and two gave much of it back before their time exit.",
            "Trader 2's own levels lost. Every agreement followed forward on them did -0.38 R (55, 31% won), against "
            "+0.07 R (129, 46%) on Trader 1's. The trade has been placed on Trader 1's levels since 25 October.",
            "Holding 24 h beat closing at 8 h: over 31 paired trades, +0.19 R better, 7 better and none worse "
            "(20 October).",
            "Refusing trades when the H1 structure is a range did not hold up. The refused trades did +0.03 R (34) "
            "against -0.05 R (53) for those taken, and the rule was reversed on 28 October.",
            "Over 375 agreements in the learning weeks, to 2 November: BUYs lost -0.36 R (123, t -3.4); October's "
            "falling majors may be the cause, not a rule. The London/New York overlap lost -0.43 R (54). Stops of "
            "1.25-2 H1 ATR lost -0.31 R (100). The desk won 42%, where its median reward:risk 1.38 and costs of "
            "0.19 R needed 50%.",
            f"Stated confidence has not predicted results. Over 375 agreements, both traders at {min_confidence} or "
            f"more did -0.09 R (163), against -0.05 R (212) otherwise. Each model states confidence on its own scale "
            f"(2 November).",
            "Agreements between two models of the same lab did -0.16 R (87), against -0.12 R (392) across labs. That "
            "is not significant on its own, but models of one lab share their training and their biases.",
            "The paid models of the week to 30 October did no better than the free ones: Trader 1's mimo -0.37 R "
            "(108 agreements), Trader 2's claude-haiku -0.31 R (76). A stronger model is not by itself a better "
            "trader.",
            f"On 2 November all three trades were made by a model standing in for Trader 1's, at exactly "
            f"{min_confidence}, after its own answer was cut off. Trader 1's model gave 32 usable answers that "
            "morning and none became a trade. Since dual-ai 1.17.0 a seat has one model and no stand-in.",
        ],
        "what_the_research_found": [
            "Live tests of LLM traders mostly lose, and high general benchmark scores do not mean better trading "
            "(LiveTradeBench: 21 models traded live for 50 days).",
            "A model's stated confidence is overconfident and poorly calibrated. Agreement between models of "
            "different labs is a better signal, but a weak one.",
            "Smart Money Concepts: no independent evidence of an edge. The desk's own tests found every SMC rule "
            "losing after costs (ID-1). Both Quarters/ICT programs failed on 2009-2016 data (QT-1, QT-2). The London "
            "true open earned +0.10 R a trade before costs, and costs of about 0.16 R left it at -0.05 R.",
            "An LLM's backtest on past prices is contaminated by what it memorised. This desk is therefore tested "
            "forward only.",
        ],
        "how_to_think": [
            "Costs first. The win rate a trade needs is (1 + c) / (1 + R), where c is its costs and R its "
            "reward:risk, both in R. A trade whose case cannot beat that line has no edge, however clear the chart.",
            "Put the stop where the idea is proved wrong, beyond the structure that would invalidate it, not where it "
            "is cheap. A stop inside one H1 bar's noise turns costs and noise into the loss.",
            "Say why. Name what in the data decides it and what would prove it wrong. A pattern that lost has a "
            "cause: avoid it while the cause is present, not because the past says so.",
            "Be honest about confidence: it is how sure you are, not how much you want to trade. A mixed market is "
            "the stronger side at a lower confidence.",
            "One trade is an anecdote. A sample marked insufficient proves nothing, either way.",
        ],
    }


__all__ = ["PLAYBOOK_VERSION", "build"]
