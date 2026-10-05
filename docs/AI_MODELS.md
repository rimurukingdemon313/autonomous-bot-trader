# AI models: what the LLM layer is for, and which models to use

## What the LLM layer does — and does not do

The five agents each have a deterministic quantitative core that always runs.
An optional LLM layer adds reasoning on top of the same point-in-time
evidence packet, for the agents listed in `AI_AGENTS` (default:
`adversary,reviewer`, to keep calls and latency low).

- Since the takeover audit (docs/TAKEOVER_AUDIT.md) it is **advisory only**.
  Its objections (closed vocabulary) and directional opinion are recorded on
  the decision as `ai.would_veto` / `ai.opinions` and change nothing: the
  deterministic pipeline decides. Track A (deterministic) and Track B (what
  the AI veto would have kept) are compared on forward outcomes by
  `learning/metrics.ai_veto_ab`; the veto may be applied only if B beats A by
  t >= 2.0 with at least 100 outcomes each side, under 2x costs and in both
  chronological halves. Until then it is out of the decision path.
- It **cannot** size, place, modify or close anything; it never sees
  credentials; its failure costs reasoning text, never safety (unless
  `AI_REQUIRED=true`, in which case failure blocks trading).
- In **research** (`aitrader/research/hypotheses.py`, `llm_drafts`) it may
  DRAFT hypotheses, using only the declared features, models and
  templates. A draft is registered and judged like any other. The lab
  **refuses to fit or judge it on data before the model's training
  cutoff**, which the draft must declare: a model that has read about a
  period cannot be tested on it. With history ending in 2018 and current
  models trained later, an LLM hypothesis can in practice be judged only
  on forward (paper) data.
- It is **not** part of any historical backtest (MODEL_CONTRACT.md §7,
  docs/RESEARCH_LOG.md): a model trained on data after a historical date
  knows what happened next.

## Configuration (environment variables; never in code)

| Variable | Example | Notes |
|---|---|---|
| `AI_PROVIDER` | `openai_compatible` | `none` (default) = quantitative agents only |
| `AI_BASE_URL` | see table below | the provider's OpenAI-compatible base URL |
| `AI_API_KEY` | secret | empty for a local server |
| `AI_MODEL` | `qwen3.5:4b` | default for every agent |
| `AI_MODEL_ADVERSARY`, `AI_MODEL_REVIEWER`, … | | per-agent override: model diversity where it helps |
| `AI_FALLBACK_MODELS` | `m2,m3` | tried in order after a failure |
| `AI_AGENTS` | `adversary,reviewer` | which agents get an LLM layer |
| `AI_TIMEOUT_S` | `60` | per call |
| `AI_MAX_TOKENS` | `1500` | per reply; a cut-off reply is rejected |
| `AI_MODEL_TRADER` | | the model for the AI trader, if different |
| `DECISION_MODE` | `evidence` | `llm_trader` = the model proposes trades; `trading_room` = several models discuss in turn and write one joint decision (below) |
| `AI_ROOM_SIZE` / `AI_ROOM_HEAD` | `4` / first member present | trading room only |
| `AI_DAILY_CALL_BUDGET` | `500` | hard cap per UTC day |
| `AI_REQUIRED` | `false` | `true` = no LLM, no trade |

## Recommended setups (in order of cost)

1. **No LLM (default).** The system is complete without one. Start here in
   paper trading so the quantitative baseline is measured first.
2. **Local, free: Ollama on your own machine** with a small open-weight model
   (reported best CPU-only choices in 2026: Qwen3.5 4B, Phi-4 Mini 3.8B,
   Gemma 4 E4B). `AI_BASE_URL=http://<host>:11434/v1`, `AI_MODEL=qwen3.5:4b`.
   Running a model on Railway itself is possible but a 4B model needs ~3 GB
   RAM and several CPU cores for tolerable latency — usually more expensive
   than a hosted free tier.
3. **Hosted free tiers** through their OpenAI-compatible endpoints: Groq,
   Google AI Studio (Gemini), Cerebras, OpenRouter free models. Limits
   change; set `AI_DAILY_CALL_BUDGET` below the tier's daily cap.

Using a different model for the adversary than for the reviewer
(`AI_MODEL_ADVERSARY`) gives some diversity of error; whether it helps is
measured, not assumed, through the per-agent reliability the reflection
engine reports.

**Not benchmarked here.** This environment cannot download model weights
or reach model APIs, so no model was evaluated in this project. The numbers
above are from the cited 2026 sources.

## The AI trader (`DECISION_MODE=llm_trader`)

A language model analyses the market and trades like a discretionary
trader, on paper or demo. The rules are MODEL_CONTRACT §10.

**What it reads before every decision:**

- completed bars on H1, H4 and D1;
- the live quote and the account;
- the five quantitative analysts' findings;
- **its memory**: its record, its most relevant past trades (losses first)
  with its own review of each, and the validated lessons.

**What it decides (llm-trader 1.12.0):** BUY, SELL, NO_TRADE or **UNCERTAIN**
(mixed evidence: recorded separately, never traded), the timeframe, the stop,
the target and a maximum holding time. A trade must also state:

- a **confidence**, the probability of reaching the target before the stop, between 0 and 1;
- an **invalidation**.

It may add the expected R, the evidence, the reasons against, the regime and any analogues. Any
malformed field makes the reply rejected, which means NO_TRADE; it is never repaired.

The confidence is recorded and later calibrated against what happened (AI_OVERCONFIDENCE /
AI_UNDERCONFIDENCE in docs/FORWARD_VALIDATION.md). It never changes a size.

The prompt says explicitly that time without a trade costs nothing. It used to ask the model not to
let the account "sit idle"; that request pushed trades and is removed (llm-trader 1.12.0,
trading-room 2.9.0).

**What it cannot do:** size a trade, touch a limit, trade while paused, or
be backtested (a model may know what happened after any historical date).

**Setup with one key for many models (for example OpenRouter):**

    DECISION_MODE=llm_trader
    AI_PROVIDER=openai_compatible
    AI_BASE_URL=https://openrouter.ai/api/v1
    AI_API_KEY=<in Railway Variables only>
    AI_MODEL=<a model id from the provider>
    AI_FALLBACK_MODELS=<a second model id>

**Cost.** One call per instrument at each decision (every 4th H1 close),
plus one review per closed trade. With 12 instruments that is about 72
calls a day. `AI_DAILY_CALL_BUDGET` caps it. When the budget is reached,
decisions are NO_TRADE until the next UTC day.

**Win rate.** The status bar shows the AI trader's live record: trades,
win rate, average R, and whether the sample is still insufficient (under
30 trades). That number is the only honest measure of it.

## Experimental AI (`DECISION_MODE=experimental_ai`)

The mode for finding out, forward, whether the models have any predictive
ability at all. Every trade it makes is labelled **EXPERIMENTAL_AI** with
edge status **EXPERIMENTAL** (docs/FORWARD_VALIDATION.md).

1. **Proposer.** This is the first provider in `AI_PROVIDERS`. It uses the AI trader's prompt and
   reply schema above.
2. **Specialists.** These are set by `AI_SPECIALISTS`, by default `adversary`. The choices are
   `structure` (market structure), `quant`, `price_action`, `macro` (news and intermarket) and
   `adversary` (adversarial risk).
   - Each specialist answers on the next provider, so a second opinion comes from a different model
     when one is configured.
   - Each reads the same market packet and the proposal.
   - Each answers AGREE / DISAGREE / UNCERTAIN, with objections from the closed vocabulary.
   - None can move a level, the size or the direction.
3. **Synthesis.** A fixed rule decides; it is not a vote:
   - a specialist that did not answer validly → NO_TRADE;
   - any BLOCKING objection → NO_TRADE;
   - two or more MAJOR objections → NO_TRADE;
   - half or more of the non-adversarial specialists naming the opposite direction → NO_TRADE
     (recorded as UNCERTAIN);
   - otherwise the proposal goes, verbatim, to the risk engine.
4. **Where it goes.** Nowhere: since the takeover audit a model-proposed trade is SHADOW in every
   mode, PAPER included, and `EXPERIMENTAL_EXECUTE=true` is refused. A language model cannot be
   backtested, so it may not create a trade until forward evidence shows it adds value.

**What is recorded on every decision:**

- the proposer's and each specialist's provider, model, status, latency and tokens;
- every answer;
- the disagreement rate.

The disagreement rate is broken down by model in `/api/evidence`.

**Cost.** Per proposal: one proposer call, plus one call per specialist. A NO_TRADE or UNCERTAIN
from the proposer costs one call.

## Primary, secondary, fallback; failures; cost

- **Order.** In `AI_PROVIDERS` the first provider is primary, the second is secondary (the
  challenger in experimental_ai), and the rest are fallbacks tried in order.
- **Failures.** A timeout, an HTTP error, a rate limit (429, after one retry and then a cooldown),
  malformed JSON or a schema violation is a failed call, never an answer.
- **Deterministic fallback.** When no provider answers validly, the decision is **NO_TRADE**.
- **Budget.** `AI_TIMEOUT_S` limits each call. `AI_DAILY_CALL_BUDGET` and `AI_<NAME>_DAILY_BUDGET`
  cap spend.
- **Cost tracking.** Prompt and completion tokens are counted per provider. With
  `AI_<NAME>_COST_IN_PER_MTOK` and `AI_<NAME>_COST_OUT_PER_MTOK` set, an estimated cost is
  computed. Without them the cost reads "not priced", never 0. Both appear on `/metrics` and in
  `/api/agents`.
- **Expensive providers.** No expensive provider is used unless you configure it: there is no
  built-in default model.

## The trading room (`DECISION_MODE=trading_room`)

One team with several minds, one per provider in `AI_PROVIDERS` (up to
`AI_ROOM_SIZE`). The members do not vote. They think together, in turn, and
reach ONE decision. They share the same data, rules and memory as the AI
trader. For each instrument at each decision:

1. **Discussion.** Each member has a role, like the desks of one trading
   firm. They speak in this order:

   | Role | Covers |
   |---|---|
   | **TREND** | the big picture: direction on H4 and D1, the team's bias |
   | **PRICE** | levels, the entry and the stop on M5, M15 and H1 |
   | **NEWS** | the economic calendar and the session open now: is now a good moment? |
   | **RISK** | costs, the account, the team's past mistakes and lessons |

   Each member reads everything said so far and builds on it from its role:
   it agrees and adds, corrects a mistake, or argues for a better plan to
   convince the others. Roles follow the order of `AI_PROVIDERS`: the first
   provider is TREND, the second PRICE, and so on. With fewer members, one
   holds neighbouring roles, and RISK always speaks last. With more, a role
   gets a second voice.
2. **Joint decision.** One member (`AI_ROOM_HEAD`, or the first member
   present) reads the whole discussion and writes the team's single plan:
   direction, timeframe, stop, target and holding time, or no trade.

**The calendar.** Every member reads the economic calendar for the pair:
the ForexFactory weekly feed of scheduled releases. It gives each event's
time, importance, forecast and previous value, and the session open now.
It is a schedule, not a headline feed. The feed is downloaded at most
hourly and kept on the volume. When it cannot be read, the models are told
it is unavailable, never that nothing is scheduled.

**The history desk.** Every model also reads what happened in the past
situations most like the market now. The source is
`models/artifacts/history.npz`:

- one situation per H1 bar, 12 pairs, 2007 to 2016;
- 698,265 situations and 2,793,060 trades, each with its realised result
  after spread, slippage and commission;
- four trade types: T1 (stop 1 ATR, target 1.5 ATR, 24 h) and T2 (stop
  1.5 ATR, target 3 ATR, 48 h), each as BUY and SELL;
- built by `scripts/build_history.py` from sealed data only, and loaded
  only if it matches its card.

For the 300 nearest situations, the desk gives each trade type's win rate,
average and median R, and a lower bound. It also counts the **distinct
episodes** (pair, day) among them. Consecutive hours share the same move,
so 300 neighbours may be 150 real episodes, and the lower bound treats
each episode, not each hour, as one observation. The desk reads only
outcomes known at the decision time. A search takes about 40 ms.

The knowledge base PR-001 tested (`memory.npz`) is unchanged, and the
evidence system does not use the history desk. The desk's own note says
what it is not: a forecast, or evidence of an edge.

If every member recommends no trade, the joint call is skipped. The
prompts carry the owner's wish for an active team that trades often,
including short M5/M15 trades. They steer no particular setup, and no
trade is forced. The quantitative analysts' view of the market is passed
on as information, not as a veto.

The following rules are enforced in code, not in the prompts:

- **Own voice only.** A member speaks only through its own provider. A
  member whose provider fails is skipped; no other model speaks for it.
- **No repairs.** A joint plan with a wrong-side or absurdly far stop is
  NO_TRADE, not repaired.
- **Size is not theirs.** The risk engine sizes the plan and may refuse it.
- **Lessons block.** A validated lesson against the plan's side blocks it.
- **Pause stops everything.** While paused or stopped, or when the data is
  bad, no model is called.

The whole discussion is recorded on each decision and shown on the
dashboard under TRADING ROOM, in speaking order, with the joint decision.
The status response (`trading_room.records`) keeps each member's forward
record in two parts: trades it argued for, and trades it did not.

**Cost.** Each decision costs one call per member plus one joint call, 5
with 4 members. When nobody sees a trade, it costs 4.

## Managing its own trades

- **Holding time.** The model sets how long a trade may stay open, in
  minutes (`max_hold_minutes`, from 1 minute to 14 days). It is checked
  every few seconds.
- **Reviews.** On its pair's turn in the rotation, each open trade is put
  back to the model with its current R, the latest M1 to H1 bars and the calendar. It
  answers HOLD or CLOSE. A close is executed at the market and shows as
  `MODEL_EXIT`. It can only close: never open, resize, or move the stop or
  target.
- **When nothing answers.** An unanswered review holds, and the stop and
  target stay on the broker.
- **Cost.** One model call per review. A pair with an open trade is not
  put to the team for a new one (the risk engine allows one per pair), so
  its turn costs 1 call instead of 5.

## How often it decides (`DECISION_INTERVAL_MIN`, `SYMBOLS_PER_CYCLE`)

**An active setup (the owner's choice).** Three liquid pairs, one decision
a minute, one pair per cycle, so each pair gets a turn every 3 minutes:

    SYMBOLS=EURUSD,GBPUSD,USDJPY
    DECISION_INTERVAL_MIN=1
    SYMBOLS_PER_CYCLE=1

This costs at most 5 calls a minute, and 1 when the pair of that minute
already has an open trade: roughly 1,500 to 7,200 calls a day.

By default the model traders decide at every 4th H1 close, the cadence the
system was tested at. With `DECISION_INTERVAL_MIN=N` (1 to 240) the
`llm_trader` and `trading_room` modes decide every N minutes instead. The
evidence system refuses this setting: it runs at the cadence it was tested
at, and startup fails with the reason shown.

When the interval is set:

- **More timeframes.** The models also read completed M5 and M15 bars from
  the broker, and may propose trades on those timeframes.
- **Faster exits.** Open paper positions are checked on every completed M1
  bar, so a stop or target is hit within the minute, not at the next H1
  close. A bar from before a position opened never closes it.
- **Pair rotation.** `SYMBOLS_PER_CYCLE=k` analyses k pairs per cycle, in
  rotation, so every pair gets its turn. 0 means all pairs every cycle.
- **Unchanged.** Every rule stays the same: the risk engine sizes every
  trade and may refuse it (maximum open positions, daily loss limit,
  minimum reward:risk), and NO_TRADE is always allowed. Nothing forces a
  trade.

**Cost is the real limit.** The number of calls per cycle is:

- **Single trader:** one call per pair analysed.
- **Trading room:** up to 5 calls per pair (4 minds in turn, 1 joint decision).

For example, `DECISION_INTERVAL_MIN=1` with `SYMBOLS_PER_CYCLE=1` in the
trading room is up to 300 calls an hour. Free tiers run out. When a
provider's budget is spent, its member is absent. When every member is
absent, the decision is NO_TRADE until the next UTC day.

## Several providers at once

Set `AI_PROVIDERS` to a comma-separated list. The order is the fallback
order. When a provider fails (HTTP error, timeout, rate limit after one
retry), gives an invalid reply, or has spent its own daily quota, the next
one answers. Each provider has its own key, and every `*_API_KEY` variable
is redacted from logs. Base URLs of the known names come from each
provider's official documentation:

| Name | Base URL | Notes |
|---|---|---|
| `openrouter` | `https://openrouter.ai/api/v1` | one key, many models |
| `groq` | `https://api.groq.com/openai/v1` | fast; free tier with limits |
| `xai` (or `grok`) | `https://api.x.ai/v1` | Grok models |
| `gemini` | `https://generativelanguage.googleapis.com/v1beta/openai` | Google AI Studio key; free tier with limits |
| `bytez` | `https://api.bytez.com/models/v2/openai/v1` | many open and closed models |

Per provider: `AI_<NAME>_API_KEY`, `AI_<NAME>_MODEL`, and optionally
`AI_<NAME>_FALLBACK_MODELS`, `AI_<NAME>_DAILY_BUDGET` (set it just under the
free tier's daily cap) and `AI_<NAME>_BASE_URL` (for any other
OpenAI-compatible provider). `AI_DAILY_CALL_BUDGET` still caps the total.
If a provider rejects the JSON response mode, the request is repeated once
without it. The reply is validated here either way. The dashboard's AI chip
shows which provider answered each decision, and `/api/agents` shows the
calls per provider today.

Sources: [OpenRouter](https://openrouter.ai/docs), [Groq OpenAI compatibility](https://console.groq.com/docs/openai),
[xAI docs](https://docs.x.ai/overview), [Gemini OpenAI compatibility](https://ai.google.dev/gemini-api/docs/openai),
[Bytez chat completions](https://docs.bytez.com/http-reference/examples/openai-compliant/chatCompletionsExample).
