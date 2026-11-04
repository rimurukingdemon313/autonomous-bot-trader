"""The dual-AI trading desk: two professional traders on two different FREE OpenRouter models (docs/DUAL_AI.md).

    MARKET DATA -> CHART IMAGE -> TRADER 1 (vision) -> TRADER 2 (independent) -> SAME SIDE: AGREEMENT
                -> BUY or SELL with entry / stop / target -> RISK ENGINE -> HARD RISK GATE -> PAPER BROKER
                                                                              -> DIFFERENT: NO TRADE
                                                                                 (one debate, in shadow only)

Selected with DECISION_MODE=dual_ai, and only with MODE=PAPER_FORWARD (the service refuses any other mode; a
context in another mode is answered NO_TRADE here as well).

THE AI DECIDES DIRECTION. Each trader must choose BUY or SELL: the side with the higher probability now, with an
entry, stop, target, risk:reward, confidence and the reasoning (structure, liquidity, momentum, trend, reversal
probability, invalidation). A mixed market is answered with the stronger side and a lower confidence, never
with a refusal.
  TRADER 1 (VisionTradingAnalyst) reads the chart image drawn from the same completed bars (charts/render.py),
  with the market data and every chart mark as numbers. (Until 1.16.0, when no free vision model gave a usable
  answer, it read the same chart from those numbers on a text model: trader1_input "numbers".)
  ONE MODEL PER SEAT (1.17.0): each trader's seat is held by one model, and when it cannot answer nobody stands in
  for it: the decision is NO_TRADE. A model whose stated confidence clears the floor on nearly every answer holds
  no trader's seat: with it, "a trade only when both are very sure" could never refuse.
  THE SENIOR TRADER (1.18.0): while the owner's funded period declares one (paid_trial), the strongest model reviews
  every trade both traders agree on at the floor, with everything the desk knows (the chart, the data, both
  analyses, the journal, the levels replayed), and answers APPROVE or VETO. It can only refuse: never a side, a
  level or a size. A veto, an unusable answer, an approval below even odds or no review at all is NO_TRADE, and the
  trade it would have been is followed forward in shadow (DUAL_AI_SENIOR_VETO). Since 1.20.0 it also judges, in
  shadow only, every agreement below the floor (`senior_shadow`): the decision stays NO_TRADE whatever it says, and
  its verdicts are followed forward so CONF-2 can tell whether its judgement picks the trades that win.
  TRADER 2 (IndependentTradingJudge) is a different model: it reads the raw data (OHLCV rows on both timeframes,
  volatility, spread, costs, structure, calendar), the chart (the image when its model can read images, its
  marks as numbers always) and Trader 1's analysis, forms its own view and picks its own side.
  SAME SIDE -> AGREEMENT: the trade candidate takes the levels of the more confident trader (Trader 1 on a tie).
  DIFFERENT SIDES -> NO TRADE (DISAGREE): two independent traders on opposite sides is an unclear market, and
  the desk stands aside. One debate still runs, IN SHADOW: a third free model (another family when one exists)
  reads both analyses, the data and the chart and must pick BUY or SELL; its pick and the side it rejected are
  followed forward as if taken and never traded, so whether standing aside was right is measured. No second round.

THE RISK ENGINE DECIDES SAFETY. The candidate goes to the SAME risk engine, hard risk gate and execution engine
as every other decision. They size it and may refuse it (stop and target sanity, spread, costs, reward:risk,
daily loss, drawdown, exposure, every hard rule). No AI sizes anything, changes a limit or reaches the broker,
and a stated confidence never changes a size.

NO_TRADE is a market opinion here in one case only: the traders disagree (DISAGREE). Otherwise it means the
decision could not be made at all:
- NOT_ASKED (MARKET_UNAVAILABLE before 1.6.0): stale or bad data, no quote, a position already open on the pair,
  trading paused, or the risk engine already refuses any trade (the calendar, a news window, full positions);
  nothing is spent asking, and the reason says which;
- AI_UNAVAILABLE: no OpenRouter key configured;
- NO_CHART, or a trader gave no usable answer (unavailable, quota spent, malformed): no decision is made on one
  trader alone, and a reply is never repaired;
- a validated lesson (confirmed out of sample) matching this exact context.

STRICT VALIDATION. A reply is one JSON object: a missing, wrongly typed, non-finite or out-of-range field, a side
other than BUY/SELL, a stop or target on the wrong side of the executable price, an entry more than 1 H1 ATR from
it (a misread price), a stop beyond 12 or a target beyond 15 H1 ATR, or a stated risk:reward that its own levels
contradict makes that reply unusable.

LEARNING is statistical only: each decision records both traders' answers, models and confidences, the rule
(AGREE / DISAGREE) and the shadow debate's choice; closed trades are scored per trader; on a disagreement the
debate's pick and the side it rejected are both followed forward as if taken, so what standing aside skipped
and whether the debate picks the better side are measured. Trader 2 and the verifier are shown these measured
records (LEARNING weeks only). No rule here moves with results.
"""

from __future__ import annotations

import dataclasses
import json
import math
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from ..charts.render import RENDER_VERSION, Chart, render_chart
from ..data.resample import resample
from ..decision.synthesis import Decision, decision_id
from ..llm.free_models import FREE_MODELS_VERSION
from ..learning.dual_ai_stats import LEVEL_KEYS, with_or_against
from ..learning.forward import session_of
from ..learning.timemachine import TIME_MACHINE_VERSION
from ..learning.timemachine import replay as replay_levels
from ..llm.openrouter import OPENROUTER_VERSION, lab_of
from ..llm.paid_trial import PAID_TRIAL, PAID_TRIAL_VERSION
from . import playbook
from .llm_trader import MAX_STOP_ATR, agent_digest, no_trade_decision, pre_model_block, trade_decision, with_ai
from .types import MarketContext

#: 1.1.0 (live check): the traders are told the risk engine's per-trade limits (minimum stop distance, minimum
#:        reward:risk) so their levels can be executed; the analysis fields are recorded as given (text or number) and
#:        never void a trade; the trade fields stay exact.
#: 1.2.0 (operator's choice, 2026-10-13): a trade only when both traders choose the same side. Opposite sides are
#:        NO_TRADE (DISAGREE); the debate runs in shadow and its pick and the side it rejected are followed forward,
#:        never traded. (1.1.0 traded the debate's pick: 4 debate trades so far, too few to judge either way.)
#: 1.3.0 (live, 2026-10-13: 23 of 40 decisions lost when every free vision model was busy at peak hours): when no
#:        vision model gives a usable answer, Trader 1 reads the same chart from its numbers (every mark at its exact
#:        price) on a text model of the third pool, never one already asked for the decision; recorded as
#:        trader1_input "numbers" (else "image"). The image prompt is unchanged.
#: 1.4.0 (live, 2026-10-14: 27 of 51 agreements refused by the risk engine for their levels; in 13 the other
#:        trader's own levels respected its limits): when both choose the same side and the more confident trader's
#:        levels fall inside the risk engine's published per-trade limits (RiskEngine.trade_limits: minimum stop
#:        distance, minimum reward:risk, at the executable price) while the other's respect them, the other's are
#:        used. Both are the traders' own, never edited; the risk engine still decides.
#: 1.5.0 (live, 2026-10-16: two agreements refused as stale, 933 s and 1103 s old, after the other pair's shadow
#:        debate waited 420 s on a busy model): every call has a time budget. A trader is asked only while the
#:        decision can still execute in time (MarketContext.decide_within_s), and never for longer than is left;
#:        the shadow debate, measurement only, waits at most SHADOW_DEBATE_DEADLINE_S. Prompts are unchanged.
#: 1.6.0 (operator, 2026-10-19): a decision refused before the traders are asked is NOT_ASKED, with the refusal
#:        as its reason ("risk engine: trading_calendar (...)"); it read "market unavailable for a decision", 88
#:        times that day, when the market was there and a rule had refused. Record only: nothing decides by it.
#: 1.7.0 (operator, 2026-10-20: "find the fix for the losses"): an M15 trade stays open up to 24 h (TIME_EXIT_MINUTES),
#:        not 8 h, and always closes an hour before the Friday close. Registered hypothesis H4: of 31 trades followed
#:        again in shadow with the same levels, holding 24 h did better in 7 and worse in none (+0.19 R a trade): the
#:        8 h exit closed trades still running toward their targets, and 6 of the 7 reached them. The traders still
#:        plan their levels for HOLD_MINUTES, as in those trades; the old 8 h exit is followed in shadow (HOLD8H).
#: 1.8.0 (operator, 2026-10-22: "a bigger timeframe, keep it free"): the desk trades the H1 chart (EXECUTION_TF), H4
#:        above it, not M15. All 79 agreement trades so far were M15: their round-trip costs took a median 16% of
#:        each trade's risk, about what the desk lost per trade (-0.05 R), and in shadow the same trades with stop
#:        and target twice as far did +0.07 R better (60 pairs). On H1 the traders set wider levels from the larger
#:        structure, so the same costs are a far smaller share. A trade is planned and held up to 48 h, closed by
#:        16:00 New York on Friday; the traders are told the time it really has.
#: 1.9.0 (operator, 2026-10-22, before 1.8.0 traded live): back to the M15 chart, keeping the 24 h time exit.
#:        On the same 60 trades followed in shadow, the levels as taken held 24 h did +$4,360 better than the
#:        trades did; stop and target twice as far (the closest measure of H1 levels) +$2,289. The H1 path
#:        stays, named by EXECUTION_TF; the Friday cut of every time exit and hold_minutes stay.
#: 1.10.0 (owner, 2026-10-25: "look at every trade, why it loses, and fix it"): a trade is always on Trader 1's
#:         levels (LEVELS_FROM). Registered hypothesis H3 (2026-10-17, from 7 trades): Trader 2's levels lose when
#:         used. Judged as registered, on the trades opened from 2026-10-19: on Trader 2's levels 21 trades at -0.57 R
#:         against 37 on Trader 1's at +0.06 R (threshold: 15+ trades, 0.3 R below). Every agreement since, followed
#:         forward: 55 at -0.38 R (31% won) against 129 at +0.07 R (46%). It held whichever model sat as Trader 2.
#:         Both traders still decide together whether there is a trade (the same side). Trader 2's own levels are
#:         followed forward in shadow (DUAL_AI_T2_LEVELS), never traded. Trader 1's levels outside the risk engine's
#:         limits are refused by it, and no longer replaced by Trader 2's (1.4.0).
#: 1.11.0 (owner, 2026-10-31: "a longer timeframe, H1 for example"): the desk trades the H1 chart again, H4 above it
#:         (EXECUTION_TF, the 1.8.0 path), planned and held up to 48 h and closed by 16:00 New York on Friday. What
#:         1.9.0 weighed is now settled by more trades: the 24 h hold it kept is in place, and on top of it the same
#:         agreements with stop and target twice as far (the closest measure of H1 levels, WIDE2X) did +0.10 R a
#:         trade better on 118 pairs (-0.03 R against -0.13 R), because costs fall from 0.18 R to 0.09 R of the risk.
#:         Over 479 agreements followed forward the desk earned +0.06 R before costs and paid 0.19 R in them: on M15
#:         the costs, not the direction, were the loss. The M15 path stays, named by EXECUTION_TF.
#: 1.12.0 (owner, 2026-10-31: "the AI enters only when it is very confident"): an agreement is a trade only when
#:         BOTH traders state a confidence of MIN_CONFIDENCE or more; below it, the agreement is NO_TRADE
#:         (LOW_CONFIDENCE), and the trade it would have been (Trader 1's levels, held as a trade) is followed forward
#:         in shadow (DUAL_AI_LOW_CONFIDENCE), never traded, so the floor stays measured. It only ever removes a
#:         trade. In the forward record (479 agreements on M15) the lower of the two confidences under 60 lost
#:         -0.25 R a trade (182) against -0.05 R at 60 or more (297), Welch t 1.8; and with stop and target twice as
#:         far, the H1-like levels of 1.11.0, the agreements at 65 or more did +0.33 R (34) against -0.18 R below
#:         (84). Small samples and one model pair's calibration among several: a floor the owner asked for, kept
#:         honest by its shadow. The traders are not told it, so it cannot move what they state.
#: 1.13.0 (owner, 2026-10-31: "make it learn everything"): BOTH traders read the desk's own journal (desk_memory):
#:         its record on the pair by side and timeframe, every agreement followed forward after costs; the most
#:         relevant past trades with how and why they ended; its record overall; the lessons confirmed out of sample.
#:         Trader 1, the one that reads the chart, saw none of it before; Trader 2 and the debate saw only the
#:         record overall. LEARNING weeks only, outcomes resolved before the decision: an EVALUATION week is never
#:         learned from, and nothing from after the decision time can be read.
#: 1.14.0 (owner, 2026-11-01: "learn from the internet"): Trader 2 is asked on another lab's model than Trader 1's
#:         first (openrouter 1.10.0, other_lab_than), and the shadow debate on a third lab's when there is one.
#:         Published audits find that agreement between models is weak evidence when they share training and
#:         biases, and that a panel of decorrelated models does better than one lab's models agreeing. The desk's
#:         own record leans the same way: agreements of two models of one lab did -0.16 R (87) against -0.12 R
#:         (392) across labs; at both confidences 65 or more, -0.24 R (32) against -0.02 R (130). Not significant on
#:         its own; it changes which free model answers first, never a rule, a level or a size. Each decision
#:         records the two traders' labs.
#: 1.15.0 (owner, 2026-11-02: "I want the AI to analyse the past to get better, not memorise it like a monkey"): the
#:         journal carries the desk's record ANALYSED (dual_ai_stats.analysis): every agreement split by one condition
#:         at a time, the conditions that clearly lost or worked after costs, the win rate a trade needs at its
#:         reward:risk, and which of those conditions apply to this decision, for either side, if BUY, if SELL, and
#:         against the trader's own levels. Both traders are asked to reason about each one as an analyst: why it
#:         lost or worked, and whether that cause is present now. On 2 November the record said: BUYs lost (-0.36 R,
#:         123, t -3.4), the London/New York overlap lost (-0.43 R, 54), stops 1.25-2 H1 ATR lost (-0.31 R, 100), and
#:         the desk won 42% where its median reward:risk 1.38 and costs 0.19 R needed 50%. An agreement under the
#:         confidence floor now records its desk confidence too.
#: 1.16.0 (owner, 2026-11-02, the day-trader-skill's /trader-timemachine): every agreement's levels (Trader 1's, the
#:         ones a trade is placed on) are replayed 10,000 times on the pair's own H1 hours of the last sixty days
#:         (learning/timemachine.py) before the risk engine decides: how often the target comes first, the stop first,
#:         or neither within the time exit, against the win rate the levels need after costs, and one verdict. It is
#:         recorded on the decision (`time_machine`), shown in the report, and read by the analysis as a condition, so
#:         the desk learns whether its verdict predicts outcomes. Measurement only: it refuses and sizes nothing.
#: 1.17.0 (owner, 2026-11-02: "nano is always high; every time the AI changes it is like a child; I want a trained
#:         AI that knows trading"): one model per trader's seat, no stand-ins (openrouter 1.11.0 `seat`). That morning
#:         Trader 1's model gave 32 usable answers and none became a trade; 5 times its answer was cut at max_tokens
#:         while it was still thinking, another vision model stood in at 65 or more, and 3 of those 5 were the day's
#:         three trades. So: (1) a seat's model that cannot answer means NO_TRADE, and Trader 1's numbers fallback on
#:         a text model is gone; (2) the traders' answers get 16,000 tokens (12,000 before; its usable answers used up
#:         to ~24,000 with the ~15,000 of the prompt); (3) a model that stated the floor or more in ALWAYS_SURE_SHARE
#:         of at least ALWAYS_SURE_MIN answers as a trader (dual_ai_stats.confidence_habits) holds no trader's seat:
#:         nemotron-3-nano-omni stated 65 or more in all of its 46. Which model answers changes, never a rule, a
#:         level or a size; the debate (shadow only) keeps its fallbacks.
#: 1.18.0 (owner, 2026-11-02: "use stronger models if you want, but please make them know"): the SENIOR TRADER. The
#:         strongest model on the catalog (paid_trial.SENIOR_2026_11: anthropic/claude-opus-5.5) reviews each trade the
#:         two traders agree on at the floor, after the deterministic lesson check, with the market packet both
#:         traders read (its journal included), both analyses, the trade's exact levels and costs, and the time
#:         machine's replay of them. APPROVE (at even odds or more) lets the trade go to the risk engine as before;
#:         anything else is NO_TRADE (SENIOR_VETO, SENIOR_UNAVAILABLE), followed forward in shadow. Asked only on a
#:         trade candidate: a handful of times a day, where a trader's seat would ask it ~150 times. Required only
#:         while the funded period covers the decision's time; outside it the desk decides as in 1.17.0.
#:         And THE DESK'S PLAYBOOK (agents/playbook.py; the owner: "not only what the company trained it on: it must
#:         know all the steps we learned"): the desk's rules, the lessons of its forward record with their samples
#:         and dates, and the research behind it, in every packet (both traders, the debate, the senior).
#: 1.19.0 (live, 2026-11-04): Trader 1's answer may use 20,000 tokens (16,000 before). On H1 its usable answers ran
#:         to ~15,200 tokens after the ~15,000 of the prompt, and 6 of its 267 answers since 1 November were cut at
#:         16,000 while it was still thinking, 4 of them among the 50 of the morning of 4 November: each one a decision
#:         lost (TRADER1_UNAVAILABLE). A cut answer had taken 83-152 s, and no decision has run out of time (both
#:         traders together: 261 s at the 90th percentile). Trader 2's seat keeps 16,000: 2 of its 202 answers were
#:         cut, and its long answers already take 160-180 s. How long a trader may think changes; no rule, level,
#:         limit or size does.
#: 1.20.0 (owner, 2026-11-04: "change everything if you must; the most important thing is a profit; the budget can
#:         be $100"): the senior trader also judges, IN SHADOW ONLY, every agreement below the confidence floor: the
#:         trade it would have been, exactly as it would be placed, with everything the desk knows, under a system
#:         prompt that says the desk will not take it whatever it answers (SENIOR_SHADOW_SYSTEM). Its verdict is
#:         recorded (`senior_shadow`) and the decision stays NO_TRADE (LOW_CONFIDENCE): it can never cause, change or
#:         size a trade. On H1 the traders' stated confidence is each model's habit (CONF-1), so the floor refuses
#:         nearly every agreement; CONF-2 (research/preregistrations/CONF-2.md) asks whether the strongest model's
#:         judgement picks the ones that win. Paid (paid-trial 1.4.0), and only while today's spend leaves room for
#:         REAL_REVIEWS_KEPT reviews of real trade candidates after it.
DUAL_AI_VERSION = "dual-ai-1.20.0"
#: whose stop and target a trade is placed on (1.10.0): Trader 1's, the trader that reads the chart
LEVELS_FROM = "trader1"
FAMILY = "DUAL_AI"
#: The two sides of a disagreement, followed forward under their own names (never traded): the side the shadow
#: debate picked, and the side it rejected. Never mixed with the trades taken, in any statistic or lesson scope.
PICK_FAMILY, PICK_SUFFIX = "DUAL_AI_DEBATE_PICK", ":debate-pick"
LOSER_FAMILY, LOSER_SUFFIX = "DUAL_AI_DEBATE_LOSER", ":debate-loser"
#: an agreement's trade on Trader 2's own levels (1.10.0): followed forward beside the trade on Trader 1's, never traded
T2LEVELS_FAMILY, T2LEVELS_SUFFIX = "DUAL_AI_T2_LEVELS", ":t2-levels"
#: an agreement below the confidence floor (1.12.0): the trade it would have been, followed forward, never traded
LOWCONF_FAMILY, LOWCONF_SUFFIX = "DUAL_AI_LOW_CONFIDENCE", ":low-confidence"
#: an agreement at the floor the senior trader did not approve (1.18.0): the trade it would have been, never traded
SENIOR_FAMILY, SENIOR_SUFFIX = "DUAL_AI_SENIOR_VETO", ":senior-veto"
SHADOW = {PICK_FAMILY: (PICK_SUFFIX, "DEBATE_PICK_NOT_TRADED"), LOSER_FAMILY: (LOSER_SUFFIX, "LOST_THE_DEBATE"),
          T2LEVELS_FAMILY: (T2LEVELS_SUFFIX, "TRADER2_LEVELS_NOT_TRADED"),
          LOWCONF_FAMILY: (LOWCONF_SUFFIX, "BELOW_THE_CONFIDENCE_FLOOR"),
          SENIOR_FAMILY: (SENIOR_SUFFIX, "NOT_APPROVED_BY_THE_SENIOR")}
#: an agreement is a trade only when both traders state at least this confidence (1.12.0)
MIN_CONFIDENCE = 65
SIDES = ("BUY", "SELL")
ENTRY_TOL_ATR = 1.0       # a market order: a stated entry further than this from the executable price is a misread
MAX_TARGET_ATR = 15.0
RR_ABS_TOL, RR_REL_TOL = 0.25, 0.20
HOLD_MINUTES = {"M15": 8 * 60, "H1": 48 * 60}  # the holding time the traders plan their levels for
#: how long a position may stay open before its time exit (1.7.0); never past an hour before the Friday close
TIME_EXIT_MINUTES = {"M15": 24 * 60, "H1": 48 * 60}
#: what this desk has learned, with its own numbers filled in from the code that enforces them (1.18.0)
PLAYBOOK = playbook.build(MIN_CONFIDENCE, TIME_EXIT_MINUTES["H1"] // 60)
NEW_YORK = ZoneInfo("America/New_York")
FRIDAY_LAST_EXIT_NY = 16 * 60  # 16:00 New York, an hour before the 17:00 close
MIN_EXEC_BARS = {"M15": 60}  # fewer completed M15 bars than this: the chart executes on H1
#: the chart the desk trades on: "H1" always H1 (1.8.0, again since 1.11.0); "M15" (1.9.0) when it has MIN_EXEC_BARS,
#: else H1
EXECUTION_TF = "H1"
EXEC_ROWS, HTF_ROWS = 60, 30
#: reasoning models think before they answer; the traders' seats have room to finish (1.17.0: 12,000 cut Trader 1's
#: model off 7 times in a day, and a stand-in took the decision; 1.19.0: 16,000 cut it off 4 times in a morning)
MAX_TOKENS = {"vision": 20000, "judge": 16000, "verifier": 12000, "senior": 10000}
#: the senior's approval must be at least even odds by its own account: an approval it is less sure of than not
#: contradicts itself, and a contradictory answer is NO_TRADE (1.18.0)
SENIOR_EVEN_ODDS = 50
#: the senior's shadow review of an agreement below the floor (1.20.0): measurement only, so it never holds up the
#: next decision long, and it is paid for only while today's budget still has room for this many real reviews after it
SHADOW_SENIOR_DEADLINE_S = 180.0
REAL_REVIEWS_KEPT = 2
CALL_DEADLINE_S = 420.0          # a trader's call, across its retries and fallbacks
SHADOW_DEBATE_DEADLINE_S = 120.0  # the shadow debate is measurement only: it never holds up the next decision long
MIN_CALL_S = 30.0                # less time left than this: the trader is not asked (its answer would come too late)
#: a model holds no trader's seat once it has stated the floor or more in this share of at least this many answers as
#: a trader (1.17.0): its "very sure" is its every answer, so the floor could never refuse it
ALWAYS_SURE_SHARE, ALWAYS_SURE_MIN = 0.9, 30
CHART_KEEP = 300  # chart files kept on disk

_SCHEMA = """{{"direction": "BUY|SELL", "entry": <price>, "stop_loss": <price>, "take_profit": <price>,
  "confidence": <0-100>, "risk_reward": <reward/risk from your own levels>,
  "market_structure": "...", "liquidity": "...", "momentum": "...", "trend": "...",
  "reversal_probability": <0-100>, "invalidation": <the price that proves this side wrong>,
  "reason": "at most 4 sentences"}}"""

#: what each trader is told of the desk's own journal (1.13.0)
_JOURNAL = """"desk_memory" is this desk's own trading journal, after costs, from completed outcomes only: its record on
this instrument by side and timeframe (every agreement followed forward, traded or not), the most relevant past
trades with how and why they ended, its record overall, and lessons confirmed out of sample. Read it as a
professional reviews a journal before a trade: when the same kind of trade here has kept losing, say what makes
this one different or lower your confidence; a run of wins is no reason on its own to be surer. A figure marked
"insufficient" is an anecdote, not proof, and the journal never replaces reading the market now.

"desk_memory.analysis" is that record ANALYSED: every agreement split by one condition at a time, the conditions
that clearly lost or worked after costs (each with its sample and t), and the win rate a trade needs at its
reward:risk to pay its costs. "analysis.now" lists the conditions that apply to THIS decision: for either side, if
you BUY, if you SELL, and the ones to check against your own levels. Be an analyst, not a parrot: for each one that
applies, ask WHY it lost or worked (a trend that has since turned, a session's thin liquidity, stops inside the
noise, targets too close for the win rate) and whether that cause is present now. Avoid repeating a losing pattern
whose cause is still there, and say so in your reason; never avoid a trade only because the past says so when its
cause is gone.

"desk_playbook" is what this desk has learned since it began: its rules, the lessons of its forward record (each with
its date and sample) and the research behind it. Read it as an experienced colleague's notes, not as orders: weigh
each point against the data now, and where it and desk_memory differ, desk_memory is newer."""

_T1_IMAGE = """You are TRADER 1 on a professional trading desk: an experienced discretionary trader reading ONE
chart image of one instrument, now. The time is {time} UTC; treat it as the present and use nothing you may know
about prices or events after it.

The image: a header (instrument, bid/ask/spread, trend, ATR, volatility), the execution timeframe above and the
higher timeframe below. Marks: confirmed swings (HH/HL/LH/LL), BOS/CHoCH structure breaks, the order block, fair
value gaps, equal highs/lows (liquidity), sweeps, displacement candles, support/resistance, previous day/week
levels, the price and the ENTRY ZONE. Only completed bars are drawn. The JSON lists every mark with its exact
price and the market data: use those numbers, not pixel estimates.

"""
#: Trader 1 when no free vision model gives a usable answer: the same chart, read from its numbers
_T1_TASK = """Your job is to FIND THE SIDE WITH THE HIGHER PROBABILITY. You MUST choose BUY or SELL. When the picture is mixed,
choose the stronger side and let your confidence say how strong it is: a low confidence is a valid answer, a
refusal is not. Read the structure, the liquidity, the momentum, the trend on both timeframes and the chance of
a reversal, and place the trade as a professional would:
- the order is a market order: BUY fills at the ask, SELL at the bid; your entry is the current price, inside
  the ENTRY ZONE;
- the stop goes beyond the level that proves your side wrong; the target at a level price can reach within
  {hold} minutes given the volatility;
- the risk engine refuses a stop closer to the entry than costs.risk_engine_limits.min_stop_distance and a
  reward:risk below min_reward_risk: place levels that respect them, or the trade will not be executed;
- you do not size the trade and you do not decide whether it may be taken: a second, independent trader gives
  his own view and a risk engine sizes the trade and may refuse it.

""" + _JOURNAL + """

Reply with ONE JSON object only, no other text:
""" + _SCHEMA
TRADER1_SYSTEM = _T1_IMAGE + _T1_TASK

TRADER2_SYSTEM = """You are TRADER 2 on a professional trading desk: an independent, experienced trader. You analyse
the same instrument, now, from the raw market data: completed OHLC bars on both timeframes (tick counts, not
traded volume: spot FX has none), volatility, spread and costs, market structure, the economic calendar, the
chart (the image if you can see it; its marks as numbers in "chart_marks" either way) and the desk's own journal
("desk_memory"). The time is {time} UTC; treat it as the present and use nothing you may know about later prices or
events.

Trader 1 has given his read in "trader1_analysis". Form YOUR OWN view first from the data, then compare: you may
agree or disagree, but agreeing because Trader 1 said so is not analysis. Say what in the data decides it.

Your job is to find the side with the higher probability. You MUST choose BUY or SELL. When the picture is
mixed, choose the stronger side and let your confidence say how strong it is: a refusal is not an answer. The
order is a market order (BUY at the ask, SELL at the bid); the stop goes beyond your invalidation, and no closer to
the entry than costs.risk_engine_limits.min_stop_distance; the target at a level reachable within {hold} minutes,
with reward:risk at least min_reward_risk. A risk engine sizes the trade and may refuse it.

""" + _JOURNAL + """

Reply with ONE JSON object only, no other text:
""" + _SCHEMA

VERIFY_SYSTEM = """You are the DESK HEAD settling a disagreement: two professional traders analysed the same instrument
and chose opposite sides ("trader1_analysis", "trader2_analysis"). You have the market data, the chart (the
image if you can see it; its marks as numbers in "chart_marks" either way) and both arguments. The time is
{time} UTC; treat it as the present.

Decide which side is stronger and why. You MUST choose BUY or SELL: one of the two traders' sides. Judge the
arguments against the data, not the confidence each trader claimed.
Reply with ONE JSON object only, no other text:
{{"direction": "BUY|SELL", "confidence": <0-100>, "reason": "why this side's argument wins, at most 4 sentences"}}"""


SENIOR_SYSTEM = """You are the SENIOR TRADER on a professional trading desk: its most experienced trader. The time is {time}
UTC; treat it as the present and use nothing you may know about later prices or events.

Two traders of the desk, each on a different model, have both chosen the same side of this instrument, each with a
confidence of {floor} or more. On such an agreement the desk takes a trade, on Trader 1's levels, held up to
{hold_h} hours and closed by 16:00 New York on Friday; the risk engine then sizes it and may still refuse it.
"the_trade" is that trade, exactly: its side, the price it would fill at, its stop and target, its reward:risk, its
costs as a share of the risk, and the win rate it needs to pay them. "time_machine", when present, is the trade's own
levels replayed 10,000 times on the pair's own recent hours: a simulation of the recent past, not a forecast.

You have everything the desk knows: the chart (the image if you can see it; every mark as numbers in "chart_marks"),
the raw bars on both timeframes, volatility, spread and costs, market structure, the economic calendar, both traders'
full analyses ("trader1_analysis", "trader2_analysis"), the desk's own journal ("desk_memory": its record after
costs, how its trades did under each condition, and the lessons confirmed out of sample), and the desk's playbook
("desk_playbook": its rules, the lessons of its record with their dates and samples, and the research behind it).

You decide ONE thing: whether this exact trade is taken. Answer APPROVE or VETO. You cannot change the side, the
entry, the stop, the target or the size, and a better trade elsewhere is not your question. APPROVE only a trade you
would take with your own money at these levels, after costs. VETO when the evidence for it is weak or mixed, when the
traders' reasoning does not hold against the data, when the costs and the reward:risk leave no edge, or when the
journal shows this kind of trade losing. A veto is a normal answer: the desk stands aside and loses nothing. Say what
in the data decides it.

Reply with ONE JSON object only, no other text:
{{"verdict": "APPROVE|VETO", "confidence": <0-100: how sure you are that your verdict is right>,
  "reason": "what in the data decides it, at most 5 sentences",
  "main_risk": "the one thing most likely to make this trade lose"}}"""

SENIOR_SHADOW_SYSTEM = """You are the SENIOR TRADER on a professional trading desk: its most experienced trader. The time is {time}
UTC; treat it as the present and use nothing you may know about later prices or events.

Two traders of the desk, each on a different model, have both chosen the same side of this instrument, but not both
with a confidence of {floor} or more, so the desk will NOT take this trade, whatever you answer. Your answer is
recorded and the trade is followed forward to its outcome, to learn whether your judgement picks the trades that win.
So judge it exactly as if it would be taken: on Trader 1's levels, held up to {hold_h} hours and closed by 16:00 New
York on Friday. "the_trade" is that trade, exactly: its side, the price it would fill at, its stop and target, its
reward:risk, its costs as a share of the risk, and the win rate it needs to pay them. "time_machine", when present, is
the trade's own levels replayed 10,000 times on the pair's own recent hours: a simulation of the recent past, not a
forecast. The confidence each trader states is how its model habitually answers; it is not evidence about this trade.

You have everything the desk knows: the chart (the image if you can see it; every mark as numbers in "chart_marks"),
the raw bars on both timeframes, volatility, spread and costs, market structure, the economic calendar, both traders'
full analyses ("trader1_analysis", "trader2_analysis"), the desk's own journal ("desk_memory": its record after
costs, how its trades did under each condition, and the lessons confirmed out of sample), and the desk's playbook
("desk_playbook": its rules, the lessons of its record with their dates and samples, and the research behind it).

You decide ONE thing: whether you would take this exact trade. Answer APPROVE or VETO. You cannot change the side, the
entry, the stop, the target or the size. APPROVE only a trade you would take with your own money at these levels,
after costs. VETO when the evidence for it is weak or mixed, when the traders' reasoning does not hold against the
data, when the costs and the reward:risk leave no edge, or when the journal shows this kind of trade losing. A veto
is a normal answer. Say what in the data decides it.

Reply with ONE JSON object only, no other text:
{{"verdict": "APPROVE|VETO", "confidence": <0-100: how sure you are that your verdict is right>,
  "reason": "what in the data decides it, at most 5 sentences",
  "main_risk": "the one thing most likely to make this trade lose"}}"""


# ── validation: a reply is used exactly as given, or not at all ─────────

def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _text(x) -> bool:
    return isinstance(x, str) and bool(x.strip())


def _pct(x) -> bool:
    return _num(x) and 0 <= x <= 100


def check_levels(direction: str, d: dict, px: dict) -> str | None:
    """The entry, stop, target and stated risk:reward of one answer, against the executable price, or why not."""
    for k in ("entry", "stop_loss", "take_profit"):
        if not _num(d.get(k)) or d[k] <= 0:
            return f"{k} must be a positive finite price"
    side = 1 if direction == "BUY" else -1
    entry, stop, target = float(d["entry"]), float(d["stop_loss"]), float(d["take_profit"])
    fill = px["ask"] if side > 0 else px["bid"]
    atr = px["atr"]
    if abs(entry - fill) > ENTRY_TOL_ATR * atr:
        return (f"entry {entry} is {abs(entry - fill) / atr:.2f} H1 ATR from the executable price {fill}: a market "
                f"order fills at the current price (at most {ENTRY_TOL_ATR} ATR away is accepted)")
    if (entry - stop) * side <= 0 or (fill - stop) * side <= 0:
        return f"stop_loss {stop} is on the wrong side for {direction} (entry {entry}, executable {fill})"
    if (target - entry) * side <= 0 or (target - fill) * side <= 0:
        return f"take_profit {target} is on the wrong side for {direction} (entry {entry}, executable {fill})"
    if abs(fill - stop) / atr > MAX_STOP_ATR:
        return f"stop {abs(fill - stop) / atr:.1f} H1 ATR away is beyond {MAX_STOP_ATR}: a typo, not a stop"
    if abs(target - fill) / atr > MAX_TARGET_ATR:
        return f"target {abs(target - fill) / atr:.1f} H1 ATR away is beyond {MAX_TARGET_ATR}"
    rr = abs(target - entry) / abs(entry - stop)
    stated = d.get("risk_reward")
    if not _num(stated) or stated <= 0:
        return "risk_reward must be a positive number"
    if abs(stated - rr) > max(RR_ABS_TOL, RR_REL_TOL * rr):
        return f"stated risk_reward {stated} contradicts its own levels ({rr:.2f})"
    return None


#: The fields that decide the trade: each must be exactly right, or the answer is unusable.
TRADE_FIELDS = ("direction", "entry", "stop_loss", "take_profit", "confidence", "risk_reward", "reason")
#: The trader's description of the market: recorded as given (text or number), never used to price, size or route
#: a trade, so a model writing "below the 1.0850 low" where a bare price was asked does not void its trade
#: (found by the live check). A list, an object or a boolean there is still a malformed answer.
ANALYSIS_FIELDS = ("market_structure", "liquidity", "momentum", "trend", "reversal_probability", "invalidation")


def validate_trader(d: dict, px: dict) -> str | None:
    """One trader's answer: a side, levels, confidence and reasoning exactly; the analysis fields as text or number."""
    if d.get("direction") not in SIDES:
        return "direction must be BUY or SELL: the desk always chooses a side"
    if not _pct(d.get("confidence")):
        return "confidence must be a number from 0 to 100"
    if not _text(d.get("reason")):
        return "reason must be text"
    for k in ANALYSIS_FIELDS:
        v = d.get(k)
        if v is not None and not isinstance(v, str) and not _num(v):
            return f"{k} must be text or a number"
    return check_levels(d["direction"], d, px)


def validate_verifier(d: dict) -> str | None:
    if d.get("direction") not in SIDES:
        return "direction must be BUY or SELL: the debate must choose a side"
    if not _pct(d.get("confidence")):
        return "confidence must be a number from 0 to 100"
    return None if _text(d.get("reason")) else "reason must be text"


def validate_senior(d: dict) -> str | None:
    """The senior's answer: a verdict, a confidence and a reason exactly; nothing else is read (1.18.0)."""
    if d.get("verdict") not in ("APPROVE", "VETO"):
        return "verdict must be APPROVE or VETO"
    if not _pct(d.get("confidence")):
        return "confidence must be a number from 0 to 100"
    return None if _text(d.get("reason")) else "reason must be text"


def _clean(d: dict | None, keys: tuple) -> dict | None:
    """The fields the record keeps of an answer: the schema's own, text cut short."""
    if not isinstance(d, dict):
        return None
    return {k: (str(d[k])[:600] if isinstance(d.get(k), str) else d.get(k)) for k in keys}


TRADER_KEYS = ("direction", "entry", "stop_loss", "take_profit", "confidence", "risk_reward", "market_structure",
               "liquidity", "momentum", "trend", "reversal_probability", "invalidation", "reason")
VERIFY_KEYS = ("direction", "confidence", "reason")
SENIOR_KEYS = ("verdict", "confidence", "reason", "main_risk")


def time_exit_minutes(timeframe: str, t: int) -> int:
    """How long a trade opened at `t` may stay open: TIME_EXIT_MINUTES for its execution timeframe, cut so it closes
    by 16:00 New York on Friday, an hour before the weekend close, so the weekend-carry rule never refuses a trade
    for its time exit alone (new positions stop at 12:00 UTC on Friday, so the cut never leaves an M15 trade less
    than its 8 h). The traders are told the shorter of this and HOLD_MINUTES (hold_minutes)."""
    full = TIME_EXIT_MINUTES.get(timeframe, TIME_EXIT_MINUTES["H1"])
    ny = datetime.fromtimestamp(t, NEW_YORK)
    friday = (ny + timedelta(days=(4 - ny.weekday()) % 7)).replace(
        hour=FRIDAY_LAST_EXIT_NY // 60, minute=FRIDAY_LAST_EXIT_NY % 60, second=0, microsecond=0)
    left = int((friday.timestamp() - t) // 60)
    return min(full, left) if left > 0 else full


def hold_minutes(timeframe: str, t: int) -> int:
    """The holding time the traders plan their levels for: HOLD_MINUTES, never longer than the trade can stay open."""
    return min(HOLD_MINUTES.get(timeframe, HOLD_MINUTES["H1"]), time_exit_minutes(timeframe, t))


def resolve(t1: dict, t2: dict, verdict: dict | None = None) -> dict:
    """The desk's rule, pure: whose side and whose levels. Same side, both at MIN_CONFIDENCE or more: a trade, on
    Trader 1's levels (1.10.0; the more confident trader is named for the record). Same side below it: no trade
    (1.12.0), the side they agreed on named for the shadow record. Opposite sides: no trade, whatever the debate
    says; the debate's pick (when it answered) and the side it rejected are named for the shadow record only."""
    if t1["direction"] == t2["direction"]:
        lead = "trader1" if t1["confidence"] >= t2["confidence"] else "trader2"
        if min(t1["confidence"], t2["confidence"]) < MIN_CONFIDENCE:
            return {"outcome": "NO_TRADE", "rule": "LOW_CONFIDENCE", "direction": None, "agreed": t1["direction"],
                    "levels_from": None, "more_confident": lead, "floor": MIN_CONFIDENCE}
        return {"outcome": "TRADE", "rule": "AGREE", "direction": t1["direction"], "levels_from": LEVELS_FROM,
                "more_confident": lead}
    pick = None if verdict is None else "trader1" if verdict["direction"] == t1["direction"] else "trader2"
    return {"outcome": "NO_TRADE", "rule": "DISAGREE", "direction": None, "levels_from": None,
            "debate_pick": None if verdict is None else verdict["direction"], "pick_from": pick,
            "loser": None if pick is None else "trader2" if pick == "trader1" else "trader1"}


def fits_limits(t: dict, px: dict, lim: dict | None) -> bool:
    """Whether a trader's own levels respect the risk engine's published per-trade limits at the executable price.
    Used only to choose between the two traders' levels when both chose the same side: the risk engine still
    decides, with the live quote at the time. Unknown limits give no preference."""
    if not lim:
        return True
    side = 1 if t["direction"] == "BUY" else -1
    e = px["ask"] if side > 0 else px["bid"]
    stop = abs(e - float(t["stop_loss"]))
    return stop > 0 and stop >= float(lim["min_stop_distance"]) and (
        abs(float(t["take_profit"]) - e) / stop >= float(lim["min_reward_risk"]))


def _shadow_side(t: dict, who: str, family: str, hold: int) -> dict:
    return {"family": family, "trader": who, "direction": t["direction"], "stop_loss": float(t["stop_loss"]),
            "take_profit": float(t["take_profit"]), "hold_minutes": hold}


# ── the data each trader reads ──────────────────────────────────────────

def chart_frames(ctx: MarketContext):
    """(execution bars, higher-timeframe bars) from the context's completed bars: M15 when EXECUTION_TF names it and
    there is enough of it, else H1; H4 resampled from H1 as the higher timeframe."""
    bars = ctx.bars or {}
    h1 = bars.get("H1")
    m15 = bars.get("M15")
    ex = (m15 if EXECUTION_TF == "M15" and m15 is not None and len(m15.as_of(ctx.t)) >= MIN_EXEC_BARS["M15"]
          else h1)
    htf = None
    if h1 is not None and len(h1):
        try:
            htf = resample(h1, "H4", as_of=ctx.t)
        except ValueError:
            htf = None
    return ex, htf


def build_chart(ctx: MarketContext) -> Chart:
    ex, htf = chart_frames(ctx)
    if ex is None:
        raise ValueError("no completed bars for this instrument")
    levels = (ctx.market_map or {}).get("levels") if isinstance(ctx.market_map, dict) else None
    return render_chart(ctx.symbol, ex, htf, as_of=ctx.t, bid=float(ctx.bid), ask=float(ctx.ask), h1_atr=ctx.atr,
                        levels=levels, entry_atr=ENTRY_TOL_ATR)


def _rows(bars, as_of: int, n: int) -> list:
    if bars is None:
        return []
    b = bars.as_of(as_of)
    b = b.take(slice(max(0, len(b) - n), len(b)))
    return [[datetime.fromtimestamp(int(b.open_time[i]), timezone.utc).strftime("%d %H:%M"),
             round(float(b.mid_open[i]), 5), round(float(b.mid_high[i]), 5), round(float(b.mid_low[i]), 5),
             round(float(b.mid_close[i]), 5), int(b.ticks[i])] for i in range(len(b))]


def _iso(t: int) -> str:
    return datetime.fromtimestamp(int(t), timezone.utc).strftime("%Y-%m-%d %H:%M")


def _with_image(packet: dict, chart: Chart) -> list:
    return [{"type": "text", "text": json.dumps(packet, default=str)},
            {"type": "image_url", "image_url": {"url": chart.data_url()}}]


#: the parts of the desk's overall record a trader reads in its journal (1.13.0); the rest stays on the dashboard
JOURNAL_RECORD = ("trades_taken", "by_desk_confidence", "taken_by_session", "exits_in_shadow",
                  "low_confidence_in_shadow", "senior_vetoes_in_shadow", "trader1_hit_rate", "trader2_hit_rate",
                  "agreement_rate")


def analysis_now(analysis: dict, ctx: MarketContext, timeframe: str | None) -> dict:
    """Which of the analysis' clear conditions apply to this decision (1.15.0): those either side meets now, those
    each side would meet, and those that depend on the levels a trader places."""
    regime = ctx.regime
    h1 = ((((ctx.market_map or {}).get("structure") or {}).get("H1") or {}).get("last_break") or {}).get("direction")
    now = {"session": session_of(ctx.t), "pair": ctx.symbol, "timeframe": timeframe,
           "regime": getattr(regime, "label", None), "volatility": getattr(regime, "vol_state", None)}
    cells = [*(analysis.get("lost") or []), *(analysis.get("worked") or [])]

    def brief(x: dict) -> dict:
        return {k: x[k] for k in ("condition", "n", "win_rate", "expectancy_r", "t", "strength")}

    def side(s: str) -> list:
        val = {"side": s, "last_H1_structure_break": with_or_against(h1, s),
               "regime_trend": with_or_against(getattr(regime, "trend_direction", None), s)}
        return [brief(x) for x in cells if x["key"] in val and val[x["key"]] == x["value"]]
    return {"for_either_side": [brief(x) for x in cells if x["key"] in now and now[x["key"]] == x["value"]],
            "if_BUY": side("BUY"), "if_SELL": side("SELL"),
            "check_your_levels": [brief(x) for x in cells if x["key"] in LEVEL_KEYS]}


def always_sure(ctx: MarketContext) -> dict:
    """The models that hold no trader's seat for this decision (1.17.0): those whose recorded answers as a trader,
    made before it (the orchestrator's `dual_ai_confidence`), stated MIN_CONFIDENCE or more in ALWAYS_SURE_SHARE of
    ALWAYS_SURE_MIN or more. A model with fewer answers keeps its seat until its habit is known."""
    habits = (ctx.memory_brief or {}).get("dual_ai_confidence") or {}
    return {m: h for m, h in habits.items() if isinstance(h, dict) and (h.get("answers") or 0) >= ALWAYS_SURE_MIN
            and (h.get("share") or 0) >= ALWAYS_SURE_SHARE}


def desk_memory(ctx: MarketContext, timeframe: str | None = None) -> dict:
    """The desk's own journal as both traders read it (1.13.0), from the orchestrator's memory brief: LEARNING weeks
    only, outcomes resolved before the decision; since 1.15.0 with the record analysed and matched to this decision.
    Never sized, never a rule: what happened and what it suggests, for the traders to weigh."""
    m = ctx.memory_brief or {}
    rec = m.get("dual_ai") or {}
    a = m.get("dual_ai_analysis")
    return {
        "analysis": ({**{k: v for k, v in a.items() if k != "version"}, "now": analysis_now(a, ctx, timeframe)}
                     if isinstance(a, dict) else None),
        "this_instrument": m.get("dual_ai_instrument"),
        "past_trades": [{**{k: v for k, v in t.items() if k != "opened"},
                         "opened_utc": _iso(t["opened"]) if _num(t.get("opened")) else None}
                        for t in (m.get("relevant_past_trades") or [])],
        "record_overall": {k: rec[k] for k in JOURNAL_RECORD if k in rec} or None,
        "trades_record": m.get("my_record"),
        "validated_lessons": m.get("validated_lessons") or [],
        "lessons_confirmed_out_of_sample": m.get("forward_lessons") or [],
    }


def trader1_packet(ctx: MarketContext, chart: Chart, hold: int) -> dict:
    return {"instrument": ctx.symbol, "decision_time_utc": _iso(ctx.t), "quote": {"bid": ctx.bid, "ask": ctx.ask},
            "holding_time_minutes": hold, "costs": ctx.costs, "chart_marks": chart.facts,
            "timeframe_summaries": ctx.mtf,
            "regime": {k: v for k, v in ctx.regime.as_dict().items() if k != "reasons"},
            "desk_memory": desk_memory(ctx, chart.meta.get("execution_timeframe")), "desk_playbook": PLAYBOOK}


def market_packet(ctx: MarketContext, reports: dict, chart: Chart, hold: int) -> dict:
    ex, htf = chart_frames(ctx)
    return {
        "instrument": ctx.symbol, "decision_time_utc": _iso(ctx.t), "quote": {"bid": ctx.bid, "ask": ctx.ask},
        "holding_time_minutes": hold, "costs": ctx.costs,
        "volatility": {"atr_h1": ctx.atr, "atr_execution": chart.facts.get("atr14_execution"),
                       "state": chart.facts.get("volatility"), "atr_percentile": chart.facts.get("atr_percentile")},
        "bar_fields": ["open_utc", "open", "high", "low", "close", "tick_count (not traded volume)"],
        "execution_bars": {"timeframe": ex.timeframe if ex is not None else None, "rows": _rows(ex, ctx.t, EXEC_ROWS)},
        "higher_timeframe_bars": {"timeframe": htf.timeframe if htf is not None else None,
                                  "rows": _rows(htf, ctx.t, HTF_ROWS)},
        "timeframe_summaries": ctx.mtf, "market_structure": ctx.market_map, "chart_marks": chart.facts,
        "regime": {k: v for k, v in ctx.regime.as_dict().items() if k != "reasons"},
        "calendar": ctx.news if ctx.news is not None else {"feed": {"status": "NOT_CONFIGURED"}, "events": None},
        "quant_agents": {k: {"summary": r.summary, "objections": [f"{o.severity} {o.code}: {o.message}"
                                                                   for o in r.objections][:5]}
                         for k, r in reports.items()},
        "desk_memory": desk_memory(ctx, chart.meta.get("execution_timeframe")),
        "desk_playbook": PLAYBOOK,
    }


def trader1_messages(ctx, chart, hold) -> list[dict]:
    return [{"role": "system", "content": TRADER1_SYSTEM.format(time=_iso(ctx.t), hold=hold)},
            {"role": "user", "content": _with_image(trader1_packet(ctx, chart, hold), chart)}]


def trader2_messages(ctx, reports, chart, t1, hold) -> list[dict]:
    packet = {**market_packet(ctx, reports, chart, hold), "trader1_analysis": _clean(t1, TRADER_KEYS)}
    return [{"role": "system", "content": TRADER2_SYSTEM.format(time=_iso(ctx.t), hold=hold)},
            {"role": "user", "content": _with_image(packet, chart)}]


def senior_messages(ctx, reports, chart, t1, t2, trade, tm, hold, system: str | None = None) -> list[dict]:
    """The senior's review (1.18.0): the market packet both traders read (the journal included), both analyses, the
    trade exactly as it would be placed and the time machine's replay of its levels. `system` is SENIOR_SHADOW_SYSTEM
    for a review in shadow (1.20.0); the packet is the same."""
    packet = {**market_packet(ctx, reports, chart, hold), "trader1_analysis": _clean(t1, TRADER_KEYS),
              "trader2_analysis": _clean(t2, TRADER_KEYS), "the_trade": trade,
              "time_machine": None if not tm else {k: tm.get(k) for k in (
                  "target_first", "stop_first", "neither", "target_share_of_decided", "win_rate_needed",
                  "mean_r_after_costs", "verdict", "hours", "replays", "based_on")}}
    return [{"role": "system", "content": (system or SENIOR_SYSTEM).format(time=_iso(ctx.t), floor=MIN_CONFIDENCE,
                                                                         hold_h=round(hold / 60))},
            {"role": "user", "content": _with_image(packet, chart)}]


def the_trade(ctx, px, side: str, lead: dict, exit_after: int, levels_from: str) -> dict:
    """The trade exactly as it would be placed (1.18.0): the price it fills at, its levels, its reward:risk, its costs
    as a share of the risk, and the win rate it needs to pay them."""
    fill = px["ask"] if side == "BUY" else px["bid"]
    sl, tp = float(lead["stop_loss"]), float(lead["take_profit"])
    risk = abs(fill - sl)
    cost_r = float((ctx.costs or {}).get("total") or 0.0) / risk if risk > 0 else None
    rr = abs(tp - fill) / risk if risk > 0 else None
    return {"side": side, "fills_at": fill, "stop_loss": sl, "take_profit": tp,
            "reward_risk": None if rr is None else round(rr, 2),
            "costs_as_share_of_risk": None if cost_r is None else round(cost_r, 3),
            "win_rate_needed_after_costs": None if rr is None or cost_r is None else round((1 + cost_r) / (1 + rr), 3),
            "held_up_to_hours": round(exit_after / 60, 1), "levels_from": levels_from}


def room_for_shadow_review(client) -> bool:
    """Whether a review in shadow may be paid for now (1.20.0): only while the funded period is open and today's spend,
    read from the key, still leaves room for REAL_REVIEWS_KEPT reviews of real trade candidates after this one. An
    unread spend is no room: measurement never takes a real trade's review."""
    status = getattr(client, "trial_status", None)
    st = status() if callable(status) else None
    if not isinstance(st, dict) or not st.get("active"):
        return False
    today, daily, per_call = st.get("spent_today"), st.get("daily_usd"), st.get("max_call_usd")
    if not all(_num(x) for x in (today, daily, per_call)):
        return False
    return today + (1 + REAL_REVIEWS_KEPT) * per_call <= daily


def _funded(client, role: str, t: int) -> bool:
    """Whether the owner's funded period declares `role` for the time `t` (1.18.0): the decision's own time, so a
    replay or a test decides as its clock says."""
    trial = getattr(client, "trial", None)
    return trial is not None and role in getattr(trial, "models", {}) and bool(trial.active(t))


def verify_messages(ctx, reports, chart, t1, t2, hold) -> list[dict]:
    packet = {**market_packet(ctx, reports, chart, hold), "trader1_analysis": _clean(t1, TRADER_KEYS),
              "trader2_analysis": _clean(t2, TRADER_KEYS)}
    return [{"role": "system", "content": VERIFY_SYSTEM.format(time=_iso(ctx.t))},
            {"role": "user", "content": _with_image(packet, chart)}]


class _Configured:
    """What `pre_model_block` asks of a provider: is one configured."""

    def __init__(self, ok: bool) -> None:
        self.config = type("C", (), {"enabled": ok})()


# ── the desk ────────────────────────────────────────────────────────────

class DualAITrader:
    def __init__(self, client=None, chart_dir: str | Path | None = None) -> None:
        self.client = client
        self.chart_dir = Path(chart_dir) if chart_dir else None
        self.charts: dict[str, dict] = {}   # symbol -> the last chart (PNG bytes and what it showed)
        self.last: dict | None = None        # the last analysis, for the dashboard
        self._lock = threading.Lock()

    def _keep_chart(self, ctx: MarketContext, chart: Chart, did: str) -> None:
        with self._lock:
            self.charts[ctx.symbol] = {"png": chart.png, "meta": chart.meta, "t": ctx.t, "decision_id": did}
        if self.chart_dir is None:
            return
        try:
            self.chart_dir.mkdir(parents=True, exist_ok=True)
            (self.chart_dir / f"{ctx.symbol}_{ctx.t}.png").write_bytes(chart.png)
            files = sorted(self.chart_dir.glob("*.png"), key=lambda p: p.stat().st_mtime)
            for old in files[:-CHART_KEEP]:
                old.unlink(missing_ok=True)
        except OSError:
            pass  # the chart's hash is on the decision record; a lost file loses only the picture

    def decide(self, ctx: MarketContext, reports: dict, versions: dict, llm_opinions=None) -> Decision:
        if ctx.mode == "BACKTEST":
            raise ValueError("the dual-AI desk cannot be backtested honestly: the models may know what happened "
                             "after the decision time")
        v = {**versions, "dual_ai": DUAL_AI_VERSION, "chart": RENDER_VERSION, "openrouter": OPENROUTER_VERSION,
             "free_models": FREE_MODELS_VERSION, "paid_trial": f"{PAID_TRIAL.name}:{PAID_TRIAL_VERSION}",
             "time_machine": TIME_MACHINE_VERSION, "playbook": playbook.PLAYBOOK_VERSION}
        did = decision_id(ctx.symbol, ctx.timeframe, ctx.t, ctx.mode, v)
        agents = agent_digest(reports)
        rec: dict = {"version": DUAL_AI_VERSION, "symbol": ctx.symbol, "t": ctx.t, "calls": [], "models": {},
                     "chart": None, "trader1": None, "trader2": None, "verifier": None, "consensus": None,
                     "regime": ctx.regime.label, "vol_state": ctx.regime.vol_state}

        def done(d: Decision, verdict: str | None) -> Decision:
            view = {"action": d.decision, "confidence": (rec.get("consensus") or {}).get("desk_confidence"),
                    "method": "dual_ai " + str((rec.get("consensus") or {}).get("rule") or ""),
                    "timeframe": (rec.get("chart") or {}).get("execution_timeframe")}
            m = rec["models"]
            ai = {"provider": "openrouter", "dual_ai": rec, "view": view,
                  "model": "+".join(x for x in (m.get("trader1"), m.get("trader2"), m.get("verifier")) if x) or None}
            d.family, d.template = FAMILY, FAMILY
            with self._lock:
                self.last = {"decision_id": d.id, "symbol": ctx.symbol, "t": ctx.t, "decision": d.decision,
                             "reason": d.no_trade_reason or d.thesis, **rec}
            return with_ai(d, ai, verdict)

        def stop(reason: str, rule: str, contra=None) -> Decision:
            rec["consensus"] = {**(rec.get("consensus") or {}), "outcome": "NO_TRADE", "rule": rule, "reason": reason}
            return done(no_trade_decision(ctx, did, v, agents, reason, contra), rule)

        if ctx.mode != "PAPER_FORWARD":
            return stop(f"DECISION_MODE=dual_ai runs in MODE=PAPER_FORWARD only (this context is {ctx.mode})", "MODE")
        client = self.client
        if client is None or not client.config.configured:
            return stop("OPENROUTER_API_KEY is not set: the traders cannot be asked", "AI_UNAVAILABLE")
        blocked = pre_model_block(ctx, reports, _Configured(True))
        if blocked:
            return stop(blocked[0], "NOT_ASKED", blocked[1])
        try:
            chart = build_chart(ctx)
        except (ValueError, TypeError) as exc:
            return stop(f"no chart could be drawn ({exc}): the traders were not consulted", "NO_CHART")
        rec["chart"] = chart.meta
        self._keep_chart(ctx, chart, did)
        px = {"bid": float(ctx.bid), "ask": float(ctx.ask), "atr": float(ctx.atr)}
        hold = hold_minutes(chart.meta["execution_timeframe"], ctx.t)
        rec["hold_minutes"] = hold
        rec["time_exit_minutes"] = exit_after = time_exit_minutes(chart.meta["execution_timeframe"], ctx.t)
        key = f"{ctx.symbol}|{ctx.t}|{chart.meta['sha256'][:16]}"
        started = time.monotonic()

        def why(r) -> str:
            return f"{r.status}{': ' + r.error if r.error else ''}"

        def budget(cap: float) -> float | None:
            """Seconds a call may take: its cap, or what is left before the decision would be too old to execute;
            None when too little is left to ask at all."""
            if ctx.decide_within_s is None:
                return cap
            rest = ctx.decide_within_s - (time.monotonic() - started)
            return min(cap, rest) if rest >= MIN_CALL_S else None

        def late(who: str) -> str:
            return (f"{who} was not asked: too little time left before the decision would be too old to execute "
                    f"({ctx.decide_within_s:.0f} s at the start)")

        # one model per seat (1.17.0): the seat's holder answers or nobody does; an always-sure model holds no seat
        sure = always_sure(ctx)
        rec["seats"] = {"no_stand_in": True, "always_sure": sure}
        if hasattr(client, "exclude_from_seats"):  # the client's status then names each seat's true holder
            client.exclude_from_seats({m: f"stated {MIN_CONFIDENCE} or more in {h['at_or_above_floor']} of its "
                                          f"{h['answers']} answers as a trader" for m, h in sure.items()})

        # Trader 1: the chart image
        dl = budget(CALL_DEADLINE_S)
        if dl is None:
            return stop(late("Trader 1") + ": no decision", "TRADER1_UNAVAILABLE")
        r1 = client.chat_json("vision", trader1_messages(ctx, chart, hold), lambda d: validate_trader(d, px),
                              dedupe_key=key + "|trader1", max_tokens=MAX_TOKENS["vision"], deadline_s=dl,
                              avoid=tuple(sorted(sure)), seat=True)
        rec["calls"].append(r1.record())
        rec["models"]["trader1"] = r1.model
        rec["trader1_input"] = "image"
        if r1.data is not None:
            rec["trader1"] = _clean(r1.data, TRADER_KEYS)
        if not r1.ok:
            return stop(f"Trader 1's model gave no usable answer ({why(r1)}): nobody stands in for it, and there is "
                        "no decision on one trader alone", "TRADER1_UNAVAILABLE")
        t1 = r1.data

        # Trader 2: independent, on a different model
        dl = budget(CALL_DEADLINE_S)
        if dl is None:
            return stop(late("Trader 2") + ": no decision on one trader alone", "TRADER2_UNAVAILABLE")
        r2 = client.chat_json("judge", trader2_messages(ctx, reports, chart, t1, hold),
                              lambda d: validate_trader(d, px), dedupe_key=key + "|trader2",
                              max_tokens=MAX_TOKENS["judge"], avoid=(r1.model, *sorted(sure)), deadline_s=dl,
                              other_lab_than=(lab_of(r1.model),), seat=True)
        rec["calls"].append(r2.record())
        rec["models"]["trader2"] = r2.model
        rec["labs"] = {"trader1": lab_of(r1.model), "trader2": lab_of(r2.model) if r2.model else None}
        if r2.data is not None:
            rec["trader2"] = _clean(r2.data, TRADER_KEYS)
        if not r2.ok:
            return stop(f"Trader 2's model gave no usable answer ({why(r2)}): nobody stands in for it, and there is "
                        "no decision on one trader alone", "TRADER2_UNAVAILABLE")
        t2 = r2.data

        if t1["direction"] != t2["direction"]:
            # opposite sides: no trade. One debate (a third model when one exists, never a second round) runs in
            # shadow: its pick and the side it rejected are followed forward as if taken, never traded.
            dl = budget(SHADOW_DEBATE_DEADLINE_S)
            r3 = None if dl is None else client.chat_json(
                "verifier", verify_messages(ctx, reports, chart, t1, t2, hold), validate_verifier,
                dedupe_key=key + "|verifier", max_tokens=MAX_TOKENS["verifier"],
                avoid=tuple(m for m in (r1.model, r2.model) if m), avoid_soft=True, deadline_s=dl,
                other_lab_than=tuple(sorted({lab_of(m) for m in (r1.model, r2.model) if m})))
            if r3 is not None:
                rec["calls"].append(r3.record())
                rec["models"]["verifier"] = r3.model
                if r3.data is not None:
                    rec["verifier"] = _clean(r3.data, VERIFY_KEYS)
            res = resolve(t1, t2, r3.data if r3 is not None and r3.ok else None)
            rec["consensus"] = res
            if res["pick_from"]:
                sides = {"trader1": t1, "trader2": t2}
                rec["shadow"] = [_shadow_side(sides[res["pick_from"]], res["pick_from"], PICK_FAMILY, hold),
                                 _shadow_side(sides[res["loser"]], res["loser"], LOSER_FAMILY, hold)]
            seen = (f"the debate ({r3.model}) would have chosen {res['debate_pick']}: followed forward in shadow, "
                    "not traded" if res["pick_from"] else late("the shadow debate") if r3 is None else
                    f"the shadow debate gave no usable answer ({why(r3)})")
            return stop(f"the traders disagree (Trader 1 {t1['direction']} {t1['confidence']}, Trader 2 "
                        f"{t2['direction']} {t2['confidence']}): no trade unless both choose the same side; {seen}",
                        "DISAGREE")
        res = resolve(t1, t2)
        # the time machine (1.16.0): the agreed trade's levels, Trader 1's, replayed on the pair's own recent hours
        rec["time_machine"] = time_machine(ctx, did, t1, px, exit_after)
        if res["rule"] == "LOW_CONFIDENCE":
            # the same side, but not both surely enough: no trade. The trade it would have been, on Trader 1's
            # levels and held as a trade, is followed forward in shadow, so the floor stays measured
            rec["consensus"] = {**res, "desk_confidence": round(min(t1["confidence"], t2["confidence"]) / 100, 3)}
            rec["shadow"] = [_shadow_side(t1, "trader1", LOWCONF_FAMILY, exit_after)]
            if _funded(client, "senior", ctx.t):
                # the senior's judgement, measured (1.20.0): it judges the trade this would have been as if it could
                # be taken; the decision stays NO_TRADE whatever it answers, and CONF-2 follows its verdict forward
                dl = budget(SHADOW_SENIOR_DEADLINE_S)
                if dl is None:
                    rec["senior_shadow"] = {"asked": False, "why": late("the senior trader")}
                elif not room_for_shadow_review(client):
                    rec["senior_shadow"] = {"asked": False, "why": "today's paid budget is kept for the reviews of "
                                                                   "real trade candidates"}
                else:
                    trade = the_trade(ctx, px, res["agreed"], t1, exit_after, "trader1")
                    r5 = client.chat_json(
                        "senior", senior_messages(ctx, reports, chart, t1, t2, trade, rec.get("time_machine"), hold,
                                                  SENIOR_SHADOW_SYSTEM),
                        validate_senior, dedupe_key=key + "|senior-shadow", max_tokens=MAX_TOKENS["senior"],
                        deadline_s=dl, seat=True)
                    rec["calls"].append(r5.record())
                    rec["senior_shadow"] = {"asked": True, "model": r5.model, "status": r5.status,
                                            **((_clean(r5.data, SENIOR_KEYS) or {}) if r5.ok else {})}
            return stop(f"both traders chose {res['agreed']}, but not both at {MIN_CONFIDENCE} or more (Trader 1 "
                        f"{t1['confidence']}, Trader 2 {t2['confidence']}): no trade unless both are that sure; "
                        "followed forward in shadow, not traded", "LOW_CONFIDENCE")
        if res["outcome"] != "TRADE":
            return stop(f"the desk's rule gave no trade ({res['rule']})", res["rule"])
        traders = {"trader1": t1, "trader2": t2}
        lead = traders[res["levels_from"]]
        if (float(t2["stop_loss"]), float(t2["take_profit"])) != (float(t1["stop_loss"]), float(t1["take_profit"])):
            # Trader 2's own levels, followed forward beside the trade and never traded: H3 stays measured
            rec["shadow"] = [_shadow_side(t2, "trader2", T2LEVELS_FAMILY, exit_after)]
        rec["consensus"] = {**res, "desk_confidence": round(min(t1["confidence"], t2["confidence"]) / 100, 3),
                            "stop_loss": float(lead["stop_loss"]), "take_profit": float(lead["take_profit"])}
        hit = _lesson(ctx, 1 if res["direction"] == "BUY" else -1)
        if hit:
            return stop(f"validated lesson {hit['lesson_id']}: {hit['statement']}", "LESSON",
                        [{"code": "LESSON_MATCH", "severity": "BLOCKING", "message": hit["statement"]}])
        story = (f"{res['rule']}: Trader 1 ({r1.model}) {t1['direction']} {t1['confidence']}: {t1['reason']} | "
                 f"Trader 2 ({r2.model}) {t2['direction']} {t2['confidence']}: {t2['reason']}")
        # the senior trader (1.18.0): while the owner's funded period declares one, no trade is taken without its
        # approval. It reads everything the desk knows and can only refuse: never a side, a level or a size
        if _funded(client, "senior", ctx.t):
            trade = the_trade(ctx, px, res["direction"], lead, exit_after, res["levels_from"])
            dl = budget(CALL_DEADLINE_S)
            r4 = None if dl is None else client.chat_json(
                "senior", senior_messages(ctx, reports, chart, t1, t2, trade, rec.get("time_machine"), hold),
                validate_senior, dedupe_key=key + "|senior", max_tokens=MAX_TOKENS["senior"], deadline_s=dl,
                seat=True)
            if r4 is not None:
                rec["calls"].append(r4.record())
                rec["models"]["senior"] = r4.model
                if r4.data is not None:
                    rec["senior"] = _clean(r4.data, SENIOR_KEYS)
            if not (r4 is not None and r4.ok and r4.data["verdict"] == "APPROVE"
                    and float(r4.data["confidence"]) >= SENIOR_EVEN_ODDS):
                said = (late("the senior trader") if r4 is None else
                        f"the senior trader gave no usable answer ({why(r4)})" if not r4.ok else
                        f"the senior trader vetoed it ({r4.data['confidence']}): {r4.data['reason']}"
                        if r4.data["verdict"] == "VETO" else
                        f"the senior trader approved it below even odds ({r4.data['confidence']}), which is no "
                        "approval")
                rec["shadow"] = [_shadow_side(lead, res["levels_from"], SENIOR_FAMILY, exit_after)]
                return stop(f"both traders chose {res['direction']} at {MIN_CONFIDENCE} or more, but {said}: no trade "
                            "without the senior's approval; followed forward in shadow, not traded",
                            "SENIOR_VETO" if r4 is not None and r4.ok else "SENIOR_UNAVAILABLE")
            story += f" | Senior ({r4.model}) APPROVE {r4.data['confidence']}: {r4.data['reason']}"
        p = {"action": res["direction"], "timeframe": chart.meta["execution_timeframe"],
             "stop": float(lead["stop_loss"]), "target": float(lead["take_profit"]), "max_hold_minutes": exit_after,
             "thesis": story[:500],
             "invalidation": (f"price trades through {lead['invalidation']}" if _num(lead.get("invalidation"))
                              else str(lead["invalidation"])[:200] if _text(lead.get("invalidation"))
                              else f"price trades through the stop {float(lead['stop_loss'])}")}
        d = trade_decision(ctx, did, v, agents, reports, p,
                           [{"agent": "dual_ai", "claim": f"{res['rule']}: levels from {res['levels_from']}",
                             "models": rec["models"]}], evidence={"consensus": res["rule"]})
        return done(d, res["rule"])

    def chart_png(self, symbol: str) -> bytes | None:
        with self._lock:
            c = self.charts.get(symbol)
            return c["png"] if c else None


def time_machine(ctx: MarketContext, did: str, t: dict, px: dict, exit_after: int) -> dict | None:
    """A trader's levels replayed on the pair's own completed H1 hours (learning/timemachine.py), from the price the
    order would fill at, for the time the trade may stay open, with its costs; None when it cannot be replayed."""
    h1 = (ctx.bars or {}).get("H1")
    if h1 is None:
        return None
    entry = px["ask"] if t["direction"] == "BUY" else px["bid"]
    try:
        seed = int(did[:8], 16)
    except ValueError:
        seed = 19
    try:
        return replay_levels(h1, as_of=int(ctx.t), entry=float(entry), stop=float(t["stop_loss"]),
                             target=float(t["take_profit"]), hold_minutes=int(exit_after),
                             cost=float((ctx.costs or {}).get("total") or 0.0), seed=seed)
    except (ValueError, TypeError, KeyError):
        return None


def _lesson(ctx: MarketContext, side: int) -> dict | None:
    kv = ctx.knowledge
    if kv is not None and hasattr(kv, "lessons_matching"):
        hits = kv.lessons_matching(FAMILY, ctx.regime.label, ctx.regime.vol_state, side, ctx.t)
        if hits:
            return hits[0]
    return None


def counterfactual_decisions(d: Decision) -> list[Decision]:
    """The two sides of a disagreement (the shadow debate's pick and the side it rejected), as decision records for
    the forward ledger only: each followed forward as if it had been taken, so what standing aside skipped and
    whether the debate chose the better side are measured. Never sent anywhere."""
    out = []
    for s in ((d.ai or {}).get("dual_ai") or {}).get("shadow") or []:
        suffix, verdict = SHADOW[s["family"]]
        out.append(dataclasses.replace(d, id=d.id + suffix, decision=s["direction"], stop_loss=s["stop_loss"],
                                       take_profit=s["take_profit"], max_hold_minutes=s["hold_minutes"],
                                       family=s["family"], template=s["family"], signal_class=s["family"],
                                       edge_status="EXPERIMENTAL", ai_verdict=verdict))
    return out


__all__ = ["ALWAYS_SURE_MIN", "ALWAYS_SURE_SHARE", "REAL_REVIEWS_KEPT", "SENIOR_SHADOW_SYSTEM", "DUAL_AI_VERSION", "DualAITrader", "FAMILY", "JOURNAL_RECORD",
           "LEVELS_FROM", "LOSER_FAMILY", "LOSER_SUFFIX", "LOWCONF_FAMILY", "LOWCONF_SUFFIX", "MIN_CONFIDENCE",
           "PICK_FAMILY", "PICK_SUFFIX", "PLAYBOOK", "SENIOR_EVEN_ODDS", "SENIOR_FAMILY", "SENIOR_SUFFIX", "SENIOR_SYSTEM",
           "T2LEVELS_FAMILY", "T2LEVELS_SUFFIX", "always_sure", "analysis_now", "build_chart", "check_levels",
           "counterfactual_decisions", "desk_memory", "resolve", "senior_messages", "time_machine", "validate_senior",
           "validate_trader", "validate_verifier"]
