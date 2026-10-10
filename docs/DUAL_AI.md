# DUAL AI desk: two professional traders on free OpenRouter models

`DECISION_MODE=dual_ai`, **`MODE=PAPER_FORWARD` only**. Paper money, a simulated $200,000 account, no broker,
no live path. Code: `aitrader/agents/dual_ai.py`, `aitrader/charts/`, `aitrader/llm/openrouter.py`,
`aitrader/llm/free_models.py`, `aitrader/learning/dual_ai_stats.py`.

```
MARKET DATA (completed bars, live quote)
  -> CHART IMAGE                    charts/render.py: the same bars, drawn and annotated, as a PNG
  -> TRADER 1  (vision)             reads the image + market data          -> BUY or SELL, entry, SL, TP, RR, confidence
  -> TRADER 2  (independent)        reads raw OHLC, both timeframes, costs,
                                    the chart and Trader 1's analysis      -> BUY or SELL, its own levels
  -> same side?      AGREE          the more confident trader's levels (Trader 1 on a tie)
     opposite side?  ONE DEBATE     a third model reads both analyses, the data and the chart, picks BUY or SELL
                                    and says why; the winner's levels are used. Never a second round.
  -> FINAL BUY or SELL with entry / stop / target
  -> RISK ENGINE                    sizes it, or refuses it (unchanged)
  -> HARD RISK GATE                 FTMO-style $200K limits (unchanged)
  -> PAPER BROKER                   simulated fill, costs, stop/target/time exit
```

## Who decides what

| | decides | may never |
|---|---|---|
| Traders 1 and 2, the debate | **direction**, entry, stop, target, the reasoning | size a trade, change a limit, reach the broker, bypass a check |
| Risk engine + hard gate | **capital safety**: size, and whether the trade may exist at all | — |

Each trader **must** choose BUY or SELL. When the market is mixed, it chooses the stronger side and says how
strong in its confidence (0-100). A refusal is not an answer: a reply of `NO_TRADE` (or anything other than
BUY/SELL) is malformed. Confidence never changes a size and is not a gate; it is recorded and compared with
outcomes.

The risk engine still blocks whatever it blocks: impossible stop or target, invalid price or size, a spread or
cost too large for the stop, reward:risk below its minimum (1.2), the daily loss limit, the maximum drawdown,
exposure, an open position on the pair, every hard rule. The traders do not know these limits and cannot change
them.

## NO_TRADE means "no decision could be made", never a market opinion

| rule | when | models asked |
|---|---|---|
| `MARKET_UNAVAILABLE` | stale or bad data, no quote/ATR, a position already open on the pair, trading paused or stopped, or the risk engine's account checks already refuse any trade | none |
| `AI_UNAVAILABLE` | `OPENROUTER_API_KEY` not set | none |
| `NO_CHART` | not enough completed bars to draw the chart | none |
| `TRADER1_UNAVAILABLE` / `TRADER2_UNAVAILABLE` | that trader's model gave no usable answer: unavailable, rate-limited, quota spent, malformed, impossible levels | 1 / 2 |
| `DEBATE_UNRESOLVED` | the traders disagree and the debate gave no usable answer | 3 |
| `LESSON` | a validated lesson (confirmed out of sample) matches this exact context | 2-3 |
| `MODE` | not PAPER_FORWARD (the service refuses this configuration anyway) | none |

No decision is made on one trader alone.

## Strict validation (a reply is used exactly as given, or not at all)

One JSON object. `direction` BUY or SELL; `entry`, `stop_loss`, `take_profit` finite positive prices;
`confidence` a number 0-100 (not a boolean); `risk_reward` a positive number consistent with its own levels
(within 0.25 or 20%); `reason` non-empty text; `reversal_probability` 0-100 and `invalidation` a price when
given. Rejected: NaN/Infinity, a stop or target on the wrong side of the executable price, an entry more than 1
H1 ATR from the executable price (a market order fills at the current price: a farther entry is a misread
price), a stop beyond 12 or a target beyond 15 H1 ATR. A malformed reply is never repaired.

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

- At most 3 requests per decision (2 when the traders agree). No loops, no second debate.
- Per request: timeout `OPENROUTER_TIMEOUT_S` (120); up to `OPENROUTER_MAX_RETRIES` (3) retries on timeout,
  429 or 5xx with exponential backoff and jitter; a 429 honours `Retry-After`; a wall-clock deadline per role
  (300 s) across retries and fallbacks; up to 3 free models per role.
- An account whose OpenRouter privacy setting excludes free endpoints gets `DATA_POLICY` on every free model:
  the dashboard says so and names the setting (https://openrouter.ai/settings/privacy); no model is rested for it.
- A reply cut at `max_tokens` before its JSON (a reasoning model thinking too long) is named as such.
- 401/403: `KEY_REJECTED`. 402 (credits required): OpenRouter refused it, nothing is charged, and no other model
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
probability, invalidation, reason), the debate's answer, the rule (AGREE/DEBATE/...), whose levels were used,
the desk confidence, every model used, every request's id, status, latency and tokens, the chart's hash.

After a trade closes, `outcome.dual_ai` scores it: was each trader's side right (before costs), was the target
reached, net R, MFE, MAE. The side that **lost a debate** is followed forward as if it had been taken
(`forward_proposals`, family `DUAL_AI_DEBATE_LOSER`, never executed), so whether the debate picks the better
side is measured. `learning/dual_ai_stats.record` gives: trades taken (win rate, expectancy R, profit factor),
by rule and by desk confidence, each trader's hit rate, the debate's losing side as if taken, the agreement
rate. Every figure carries its sample size; below 30 it is labelled `insufficient`.

Trader 2 and the debate are shown this record from LEARNING weeks only (every third ISO week is EVALUATION and
is never learned from). Nothing moves a rule, a size or a limit; the desk's trades are never averaged with
another mode's.

## Configuration and activation

Local (`.env` is in `.gitignore`; the environment always wins over the file):

```
cp .env.example .env          # then put your key between the quotes:
OPENROUTER_API_KEY="PASTE_MY_KEY_HERE"
MODE=PAPER_FORWARD DECISION_MODE=dual_ai DECISION_INTERVAL_MIN=75 SYMBOLS_PER_CYCLE=1 python -m aitrader
```

The continuous paper run on GitHub (`.github/workflows/paper-forward.yml`): add the repository secret
**`OPENROUTER_API_KEY`** (Settings → Secrets and variables → Actions → New repository secret). From the next
shift the run uses `dual_ai`, deciding every 75 minutes on one pair in rotation (about 2.5 requests per decision:
inside a free key's 50 a day). With credits on the key (1000 a day), set the variables
`PF_DECISION_INTERVAL_MIN` and `PF_SYMBOLS_PER_CYCLE` to decide more often. `PF_DECISION_MODE`, when set,
overrides the choice.

The dashboard's DUAL AI DESK panel (`/api/dual_ai`, `/api/dual_ai/chart.png?symbol=`) shows the OpenRouter
status, the three models, the last analysis with both traders' answers and the debate, the risk engine's
verdict, the open paper positions, AI trades, wins, losses, expectancy, profit factor and drawdown. The key is
shown only as `…` and its last four characters, and is never logged, stored or returned.

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
