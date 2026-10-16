# DUAL AI desk: two professional traders on free OpenRouter models

`DECISION_MODE=dual_ai`, **`MODE=PAPER_FORWARD` only**. Paper money, a simulated $200,000 account, no broker,
no live path. Code: `aitrader/agents/dual_ai.py`, `aitrader/charts/`, `aitrader/llm/openrouter.py`,
`aitrader/llm/free_models.py`, `aitrader/learning/dual_ai_stats.py`.

```
MARKET DATA (completed bars, live quote)
  -> CHART IMAGE                    charts/render.py: the same bars, drawn and annotated, as a PNG
  -> TRADER 1  (vision)             reads the image + market data          -> BUY or SELL, entry, SL, TP, RR, confidence
                                    (no vision model answers: the same chart's
                                    numbers, on a text model)
  -> TRADER 2  (independent)        reads raw OHLC, both timeframes, costs,
                                    the chart and Trader 1's analysis      -> BUY or SELL, its own levels
  -> same side?      AGREE          a trade, on the more confident trader's levels (Trader 1 on a tie)
     opposite side?  DISAGREE       NO TRADE. One debate still runs IN SHADOW: a third model reads both analyses,
                                    the data and the chart and picks BUY or SELL; its pick and the side it rejected
                                    are followed forward as if taken, never traded. Never a second round.
  -> FINAL BUY or SELL with entry / stop / target (agreement only)
  -> RISK ENGINE                    sizes it, or refuses it (unchanged)
  -> HARD RISK GATE                 FTMO-style $200K limits (unchanged)
  -> PAPER BROKER                   simulated fill, costs, stop/target/time exit
```

## Who decides what

| | decides | may never |
|---|---|---|
| Traders 1 and 2 (together) | **direction**, entry, stop, target, the reasoning: a trade only when both choose the same side | size a trade, change a limit, reach the broker, bypass a check |
| The debate (shadow) | nothing that is traded: its pick on a disagreement is followed forward and measured | create a trade |
| Risk engine + hard gate | **capital safety**: size, and whether the trade may exist at all | — |

Each trader **must** choose BUY or SELL. When the market is mixed, it chooses the stronger side and says how
strong in its confidence (0-100). A refusal is not an answer: a reply of `NO_TRADE` (or anything other than
BUY/SELL) is malformed. Confidence never changes a size and is not a gate; it is recorded and compared with
outcomes.

The risk engine still blocks whatever it blocks: impossible stop or target, invalid price or size, a spread or
cost too large for the stop, reward:risk below its minimum (1.2), the daily loss limit, the maximum drawdown,
exposure, an open position on the pair, every hard rule. The traders are told the per-trade limits (minimum stop
distance at this spread, minimum reward:risk) so their levels can be executed; they cannot change them.

### Levels the risk engine can accept (dual-ai 1.4.0, 2026-10-14)

On 2026-10-14, 27 of 51 agreements were refused by the risk engine for their levels (reward:risk below 1.2, or
costs above a quarter of the stop); in 13 of them the other trader's own levels respected those limits. When both
traders choose the same side and the more confident one's levels fall inside the risk engine's published
per-trade limits (`RiskEngine.trade_limits`: minimum stop distance and minimum reward:risk, at the executable
price) while the other's respect them, the other's levels are used (`consensus.levels_reason` says so). Both
sets are the traders' own and are never edited; the risk engine still decides with the live quote.

### What the losses showed, and what is measured now (2026-10-14)

Fourteen closed trades: gross P&L +$36, costs $1,180. Before costs the desk was flat; each trade paid about 20% of
its risk in spread, commission and slippage, because the stops are about one H1 ATR. The losers went wrong at
once (their best point was at most +0.16R); the winners all reached +1.2R or more, and two gave much of it back
before their time exit (USDCAD +1.24R to +0.30R, EURCHF +1.21R to +0.74R). All three entries in the late
evening (UTC) were stopped out. Too few trades to change a rule on, so:

- **Exits in shadow** (forward 1.1.0): every trade taken is followed forward again, never traded, with the stop
  moved to the entry once +1R is reached (`DUAL_AI_EXIT_BE1R`, from the bar after the one that reached it), held
  24 h (`..._HOLD24H`), and with stop and target twice as far, held 24 h (`..._WIDE2X`: costs half the share
  of the risk). `dual_ai_stats.record()["exits_in_shadow"]` pairs each with the trade as taken on the same
  entries; the report prints the comparison.
- **By session**: `taken_by_session` splits the trades taken by UTC session.
- **Quiet hours** (risk 1.6.0, the risk engine's own limit for MODE=PAPER_FORWARD): no new position from 16:00 to 20:00 New York
  (DST-aware; 23:00-03:00 Baghdad in summer), an hour before the 17:00 rollover to the Tokyo open, when
  liquidity is thinnest and spreads widest. Split by session, the first 14 trades were: Asia +$88 (3), London
  +$716 (3), the London/New York overlap -$841 (3), New York +$162 (2), late evening -$1,270 (3, all stopped
  out). Only the last has a known market reason behind it; the others are three trades each and stay open.
  Risk 1.4.0/1.5.0 put the window in the evaluation profile; that changed the profile's hash and the hard gate
  refused every new trade with PROFILE_CHANGED from 2026-10-14 06:46 to 19:30 UTC (28 approved trades). A profile
  cannot change during an evaluation, so the window moved to the risk engine (1.6.0), the profile is back to the
  run's own (pinned by a test), and the shift report now opens with a warning whenever the gate refuses. This is a known property of the
  market, not a fit to three trades, and it can only refuse an entry. The risk engine applies it, and the
  desk is not asked inside the window.

### When no vision model answers (dual-ai 1.3.0, 2026-10-13)

Only a handful of free models read images, and at peak hours (about 11:00-14:30 UTC) all of them can be busy at
once: on 2026-10-13, 23 of 40 decisions were lost that way. When no free vision model gives a usable answer,
Trader 1 reads the **same chart from its numbers** (the packet already lists every mark at its exact price) on a
text model of the third pool, so Trader 2 keeps its own best model. It never follows a stop no other model would
fix (no key, budget or quota spent, spend on the key, a policy block), never asks a model already asked for that
decision, and its reply is validated exactly as any other. The decision records `trader1_input`: `image` or
`numbers`, and `dual_ai_stats` splits the trades by it, so whether the picture adds anything is measured. The
image prompt is unchanged.

### Why a trade needs both traders (dual-ai 1.2.0, 2026-10-13)

Until 1.1.0 the debate's pick was traded. The operator chose agreement-only after the first day: two independent
traders on opposite sides is an unclear market, and standing aside there is capital preservation (rule 8). The
first day's record does **not** prove it (4 debate trades: 3 stopped out, 1 open; 1 agreement trade, a winner):
far too few to judge either way. That is why the debate still runs in shadow: the side it would have traded
(`DUAL_AI_DEBATE_PICK`) and the side it rejected (`DUAL_AI_DEBATE_LOSER`) are both followed forward, so whether
standing aside is right is measured, not assumed. The prompts are unchanged, so these picks are comparable with
1.1.0's.

## NO_TRADE: the traders disagree, or no decision could be made

| rule | when | models asked |
|---|---|---|
| `DISAGREE` | the traders chose opposite sides: stand aside (the debate runs in shadow; if it gives no usable answer, nothing is followed) | 3 |
| `MARKET_UNAVAILABLE` | stale or bad data, no quote/ATR, a position already open on the pair, trading paused or stopped, or the risk engine's account checks already refuse any trade | none |
| `AI_UNAVAILABLE` | `OPENROUTER_API_KEY` not set | none |
| `NO_CHART` | not enough completed bars to draw the chart | none |
| `TRADER1_UNAVAILABLE` / `TRADER2_UNAVAILABLE` | that trader's model gave no usable answer: unavailable, rate-limited, quota spent, malformed, impossible levels (for Trader 1: no vision model, and then no text model reading the chart's numbers) | 1 / 2 |
| `DEBATE_UNRESOLVED` | (dual-ai 1.1.0 only) the traders disagreed and the debate gave no usable answer | 3 |
| `LESSON` | a validated lesson (confirmed out of sample) matches this exact context | 2-3 |
| `MODE` | not PAPER_FORWARD (the service refuses this configuration anyway) | none |

No decision is made on one trader alone.

## Strict validation (a reply is used exactly as given, or not at all)

One JSON object. The fields that decide the trade are exact: `direction` BUY or SELL; `entry`, `stop_loss`,
`take_profit` finite positive prices; `confidence` a number 0-100 (not a boolean); `risk_reward` a positive number
consistent with its own levels (within 0.25 or 20%); `reason` non-empty text. The trader's description of the
market (`market_structure`, `liquidity`, `momentum`, `trend`, `reversal_probability`, `invalidation`) is recorded as
given, text or number, and never prices, sizes or voids a trade (the live check found a model writing its
invalidation as a sentence); a list, object or boolean there is still malformed. Rejected: NaN/Infinity, a stop or target on the wrong side of the executable price, an entry more than 1
H1 ATR from the executable price (a market order fills at the current price: a farther entry is a misread
price), a stop beyond 12 or a target beyond 15 H1 ATR. A malformed reply is never repaired, and that model is
not asked again for it: the next free model of the same role gives its own answer, inside the same deadline
(openrouter 1.6.0; the live run of 2026-10-12 lost a whole decision to one vision model answering without JSON).
Every model asked before the one that answered is recorded on the call with its status.

## The chart

`charts/render.py` draws a 1280x1000 PNG from **completed bars only** (`available_at <= decision time`); bars
after it change nothing, and the same bars always give the same bytes (both are tested).

- header: instrument, timeframes, time, bid/ask/spread, trend per panel, ATR(14), volatility and its percentile;
- upper panel, execution timeframe (M15 with at least 60 completed bars, else H1), last 100 candles: confirmed
  swings labelled HH/HL/LH/LL, BOS/CHoCH breaks, the order block (tested/broken), fair value gaps
  (open/mitigated), equal highs/lows (liquidity), sweeps, displacement candles, support/resistance clusters,
  previous day/week high/low, bid and ask lines, and the ENTRY ZONE (±1 H1 ATR around the price);
- lower panel, H4 built from completed H1: candles, swings, structure, S/R, trend;
- legend.

Every mark is computed by walking forward (`charts/annotate.py`, the same detectors as `features/market_map.py`):
a swing exists only after its two confirming bars have closed. Every mark also travels as numbers
(`chart_marks`), so no model has to read a price off pixels, and a text-only model gets the same chart.
The last chart per pair is on the dashboard and saved under `DATA_DIR/charts/` (newest 300).

## Free models only

One key, `OPENROUTER_API_KEY`, powers all three roles. A model is used only if **all** hold
(`llm/free_models.py`):

- its id ends in `:free` (OpenRouter's explicit free variant; a model that merely lists $0 without it is a
  promotion that can end, and OpenRouter's own Free filter does not list it);
- every price it lists is exactly zero;
- it writes text only (audio/image generators are billed per item; embedding/rerank models write vectors);
- no price in its description; not a router, safety/guard classifier, embedding, rerank or speech model.

At run time: a reply that reports a cost above zero, or one served by another model, is discarded and that
model is never used again; if the key's spent credit (GET /key `usage`) ever rises while the bot runs, **no
further request is made** (`PAID_USAGE_STOPPED`). Use this key for this bot only. There is never a paid
fallback: no free model, no call, NO_TRADE (`AI_UNAVAILABLE`-class).

### Selection (declared score, from catalog fields only, never from trading results)

- capability = the catalog's independent Artificial Analysis intelligence index (else from the parameter
  count, at most 12);
- Trader 1 needs image input: 40 + capability + context + 3 reasoning + 2 recent;
- Trader 2: capability + context + 6 reasoning + 3 image input + 10 if another family than Trader 1;
- debate: capability + context + 6 reasoning + 4 image input + 10 if a family neither trader uses;
- minus 10 for single-domain specialists (code, health) and for models expiring within 30 days (within 7:
  excluded), minus 30 x failure rate.

With only two suitable models, the stronger reasoner of the two is reused for the debate.

**Picks on the live catalog, 2026-10-10 19:14 UTC** (458 models, 14 qualifying free, 6 with image input;
`research/results/openrouter-free-models.json`):

| role | model | why |
|---|---|---|
| Trader 1 (vision) | `thinkingmachines/inkling-small:free` | highest intelligence index of the free image models (25.7), 1M context, reasoning; fallback `thinkingmachines/inkling:free` (25.0) |
| Trader 2 (independent) | `nvidia/nemotron-3-ultra-550b-a55b:free` | the strongest free reasoner of another family (22.9; 550B, 1M context); text only, so it reads the chart's marks as numbers |
| Debate | `google/gemma-4-26b-a4b-it:free` | a third family, sees the chart image (16.7) |

The catalog changes; the selection is recomputed hourly and on failures. Optional pins
(`OPENROUTER_VISION_MODEL`, `OPENROUTER_JUDGE_MODEL`) are honoured only while the catalog lists them as free.

## Limits, retries, duplicates

- At most 3 roles asked per decision (2 when the traders agree). No loops, no second debate.
- Per request: timeout `OPENROUTER_TIMEOUT_S` (180; free models took 30-170 s in the live check); up to
  `OPENROUTER_MAX_RETRIES` (3) retries on a timeout or 5xx with exponential backoff and jitter. A busy model (a 429
  without a short `Retry-After`, or a 200 carrying an upstream error such as "ResourceExhausted") rests and the
  next free model answers at once. A model busy again before giving a usable reply rests twice as long each time
  (5 minutes doubling to 60; a failing one 15 doubling to 60), and its first usable reply resets it: a model busy
  all day is not asked every cycle only to say so (openrouter 1.7.0). A wall-clock deadline per role (420 s) across retries and fallbacks; up to 8
  free models per role. Reasoning models are asked for medium reasoning effort and may write 12,000 tokens, so
  the answer fits after the thinking.
- The traders are told the risk engine's own per-trade limits (`RiskEngine.trade_limits`: minimum stop distance
  at this spread, minimum reward:risk), so their levels can be executed; the risk engine still decides.
- An account whose OpenRouter privacy setting excludes free endpoints gets `DATA_POLICY` on every free model:
  the dashboard says so and names the setting (https://openrouter.ai/settings/privacy); no model is rested for it.
- A reply cut at `max_tokens` before its JSON (a reasoning model thinking too long) is named as such.
- 401, or a 403 about the key itself: `KEY_REJECTED`. A 403 about one model (OpenRouter: "only available on
  agentic harnesses") excludes that model for the process and the next free one answers. 402 (credits required): OpenRouter refused it, nothing is charged, and no other model
  is tried. 404 or "no endpoints": that model rests 6 hours and the next free one answers. A spent free daily
  quota: no call until the next UTC day.
- Daily budget: `OPENROUTER_DAILY_CALL_BUDGET` (900), never above the key's own free quota read from GET /key
  (50 a day on a key that never bought credits, 1000 after $10), less a margin of 2.
- Every request has its own `X-Request-Id`, recorded with the decision. An identical request (same role, model,
  prompt, chart) is answered from the cache, never sent twice. Trader 2 is never the model that answered as
  Trader 1; the debate avoids both when a third free model exists.
- The image is sent only to a model the catalog lists with image input.

## Learning (statistical only)

Recorded on every decision (`decisions.payload.ai.dual_ai`): symbol, time, timeframes, regime and volatility,
both traders' full answers (direction, levels, confidence, structure, liquidity, momentum, trend, reversal
probability, invalidation, reason), the shadow debate's answer, the rule (AGREE/DISAGREE/...; DEBATE for
dual-ai 1.1.0), whose levels were used,
the desk confidence, every model used, every request's id, status, latency and tokens, the chart's hash.

After a trade closes, `outcome.dual_ai` scores it: was each trader's side right (before costs), was the target
reached, net R, MFE, MAE. On a disagreement both sides are followed forward as if they had been taken
(`forward_proposals`, route `COUNTERFACTUAL`, never executed, not checked by the risk engine): the side the
shadow debate picked (family `DUAL_AI_DEBATE_PICK`: what standing aside skipped) and the side it rejected
(family `DUAL_AI_DEBATE_LOSER`: did the debate choose the better side?). `learning/dual_ai_stats.record`
gives: trades taken (win rate, expectancy R, profit factor), by rule and by desk confidence, each trader's hit
rate, the debate's pick and its rejected side as if taken, the agreement rate. Every figure carries its sample size; below 30 it is labelled `insufficient`.

Trader 2 and the debate are shown this record from LEARNING weeks only (every third ISO week is EVALUATION and
is never learned from). Nothing moves a rule, a size or a limit; the desk's trades are never averaged with
another mode's.

## Configuration and activation

Local (`.env` is in `.gitignore`; the environment always wins over the file):

```
cp .env.example .env          # then put your key between the quotes:
OPENROUTER_API_KEY="PASTE_MY_KEY_HERE"
MODE=PAPER_FORWARD DECISION_MODE=dual_ai DECISION_INTERVAL_MIN=15 SYMBOLS_PER_CYCLE=2 python -m aitrader
```

The continuous paper run on GitHub (`.github/workflows/paper-forward.yml`): add the repository secret
**`OPENROUTER_API_KEY`** (Settings → Secrets and variables → Actions → New repository secret). From the next
shift the run uses `dual_ai`, deciding at every M15 close on two pairs in rotation, so each of the 12 pairs is
looked at every 90 minutes (since 2026-10-13; 75 minutes and one pair before, sized for a key without credits). That
is at most 192 decisions a day, about 2.5 requests each when both traders are asked and none when a pair is
blocked first (open position, currency exposure, stale data): inside the 1000 a day of a key with credits. The
client stops at its daily budget (900, never above the key's own quota read from GET /key), and a decision
without a model is NO_TRADE, never a guess. A decision that runs past the next M15 close delays the next one;
requests never pile up. On a key without credits (50 a day) set `PF_DECISION_INTERVAL_MIN=75` and
`PF_SYMBOLS_PER_CYCLE=1`. `PF_DECISION_MODE`, when set, overrides the choice.

The dashboard's DUAL AI DESK panel (`/api/dual_ai`, `/api/dual_ai/chart.png?symbol=`) shows the OpenRouter
status, the three models, the last analysis with both traders' answers and the debate, the risk engine's
verdict, the open paper positions, and the desk's trades: wins, losses, net P&L, expectancy, profit factor and
drawdown. The key is shown only as `…` and its last four characters, and is never logged, stored or returned.

**One figure per rule.** Two rules are never averaged into one number ([VERSIONING.md](VERSIONING.md)). The
desk's figures (`performance`, `recent_trades`, and the head of `REPORT.md`) are those of the rule it trades:
AGREE. The trades of the debate rule, which traded on a disagreement until dual-ai 1.2.0 stopped it, are shown
apart under `retired_rules` with their own figures; `performance_by_rule` has every rule, and
`performance_all_rules` every desk trade, nothing left out. Every closed trade carries its `rule`
(`paper_metrics.rule_of`, from `outcome.dual_ai.rule`); a desk trade whose rule cannot be read is `UNKNOWN`,
never counted as agreement.

**The retired rule's trades removed from the account (operator's request, 2026-10-15).** The journal is
append-only: no trade is ever deleted from it. The 4 debate-rule trades were taken out of the paper account by a
declared adjustment (`aitrader/broker/adjustments.py`): their net P/L as the broker booked it (−$1,416.51) is
put back once, journaled (`PAPER_ADJUSTMENT`), and every report shows it beside the equity, with the equity it
replaced. They are listed apart (`removed_trades`, `retired_rules.DEBATE.removed_from_account`) and are in none
of the account's figures. The desk's own learning record still holds them: what the debate did is a fact the
traders are shown.

## Live check (the real services, on demand)

`.github/workflows/dual-ai-check.yml` runs `scripts/dual_ai_check.py` on a GitHub runner with the
`OPENROUTER_API_KEY` secret: Actions tab → "Dual-AI live check" → Run workflow (or push to the branch
`dual-ai-check`). The report is committed to the branch `dual-ai-check-results` (`dai-check/REPORT.md`, the
charts; never the key). It checks, in order: the live catalog and the three picks; the key (accepted, free
tier, daily quota); one small JSON request to each model, and the vision model reading the chart; the chart
from live Yahoo bars; a dry run of the whole desk on real prices with scripted traders (no request sent); and
one complete decision per pair with the real models through the production runtime, on a temporary paper
account that is discarded. On a closed-market day it replays the last full trading hour and says so. It uses
about 10 of the key's free daily requests.

Run 2026-10-12 06:21 UTC with the key (Sunday: replay of Friday's last full hour): key accepted (credits on the
account: daily quota 998, spend 0.00); all three pairs decided by the real models and approved by the risk engine:
USDJPY AGREE → BUY (Trader 1 `dots-3-note-preview` 65, Trader 2 `nemotron-3-ultra` 60), GBPUSD AGREE → SELL (68,
65), EURUSD DEBATE → SELL (Trader 1 `nemotron-3-nano-omni` BUY 75, Trader 2 SELL 65, debate `dots-3-note-preview`
SELL). In practice `inkling-small`/`inkling` are closed to API keys (403 "agentic harnesses") and `gemma-4-26b`
was rate-limited upstream, so Trader 1 was served by the next free vision models; each request took 30-130 s.
Earlier runs that day found and fixed: the 403 stopping all calls, busy models retried instead of replaced,
replies cut at the token limit, an analysis field voiding a trade, a 2.6B model chosen for the debate, stops
placed inside the risk engine's cost limit.

Run 2026-10-10 (Saturday, no key yet): catalog OK (14 free of 458; the three picks above), charts OK on live
M15/H4 bars for EURUSD, GBPUSD, USDJPY, and the dry run OK on Friday's last full hour: EURUSD AGREE → BUY, risk
APPROVED; GBPUSD DEBATE → BUY, risk APPROVED; USDJPY refused by the risk engine's currency-exposure limit (two
open positions already shared USD). Sections needing the key were skipped.

## Mocked end-to-end run

`python scripts/dual_ai_simulation.py --days 7 --out research/results/dual-ai-mock-simulation.json` runs the
production runtime in PAPER_FORWARD for 7 simulated days on a synthetic replay, with OpenRouter MOCKED by fixed
rules (Trader 1: the chart's trend; Trader 2: 20-bar momentum in the raw rows; debate: the higher timeframe).
Last run: 135 decision points, of which 96 `MARKET_UNAVAILABLE` (a position already open on the pair, the risk
engine's currency-exposure limit, the weekend's stale data) and 39 decided: 25 AGREE, 14 DEBATE; 92 requests
(2.4 per decided point); all 39 approved by the risk engine and executed on paper; 37 closed. The forward ledger
followed the 14 sides that lost a debate (8 resolved so far). No key left the client; live trading false.
The P&L is that of fixed rules on synthetic prices and means nothing about any model.

## What this is not

Not evidence of profitability. The historical research status is unchanged (no validated edge). The desk is
measured forward, after costs, on paper; until its record has an adequate sample and survives the evaluation
weeks, any number it shows is a measurement in progress, not a result.
