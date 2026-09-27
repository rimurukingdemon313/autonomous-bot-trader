# AI models: what the LLM layer is for, and which models to use

## What the LLM layer does — and does not do

The five agents each have a deterministic quantitative core that always runs.
An optional LLM layer adds reasoning on top of the same point-in-time
evidence packet, for the agents listed in `AI_AGENTS` (default:
`adversary,reviewer`, to keep calls and latency low).

- It **can** raise objections from a closed vocabulary (it can block a trade:
  AI can only subtract).
- It **can** state a directional opinion. That opinion enters the decision
  with a weight equal to its **measured forward reliability**, which starts at
  **zero** and rises only after its oppositions have been shown to predict
  worse outcomes on at least 50 resolved cases each side. Agreement never
  lowers the bar.
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
| `DECISION_MODE` | `evidence` | `llm_trader` = the model proposes trades; `trading_room` = several models hunt, debate and a head picks (below) |
| `AI_ROOM_SIZE` / `AI_ROOM_QUORUM` / `AI_ROOM_HEAD` | `4` / `2` / first member | trading room only |
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

**What it decides:** BUY, SELL or NO_TRADE, the timeframe, the stop, the
target and a maximum holding time.

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

## The trading room (`DECISION_MODE=trading_room`)

Several models trade together, one per provider in `AI_PROVIDERS` (up to
`AI_ROOM_SIZE`). They share the same data, rules and memory as the AI
trader. For each instrument at each decision:

1. **Own view.** Each member reads the market its own way and decides
   freely, without seeing the others: a trade of its own choosing, or
   none. If no member wants a trade, the room stops here.
2. **Debate.** Each member reads every view and gives a final position:
   keep it, change it, take another member's trade, or stand aside.
3. **Head.** The head trader (`AI_ROOM_HEAD`, or the first member present)
   reads the final positions, the critiques and each member's record, and
   takes ONE member's trade exactly as proposed, or none. Members may
   disagree, even on direction; weighing that is the head's job.

The prompts steer no style, setup or timeframe. The quantitative analysts'
view of the market is passed on as information, not as a veto.

The following rules are enforced in code, not in the prompts:

- **Own voice only.** A member speaks only through its own provider. A
  member whose provider fails is absent; no other model speaks for it.
- **Quorum (optional).** With `AI_ROOM_QUORUM=k`, a direction needs k
  members holding it to be eligible. The default is 1, so any member's
  trade may be taken. The quorum is capped by how many members are present.
- **No repairs.** A final trade with a wrong-side or absurd stop is
  dropped, not repaired.
- **The head only chooses.** It picks one supporter's trade verbatim. It
  cannot change a level, invent a trade, or size one.
- **Lessons block.** A validated lesson against the chosen side blocks the
  trade.
- **Pause stops everything.** While paused or stopped, no model is called.

The whole discussion is recorded on each decision and shown on the
dashboard under TRADING ROOM. The status response (`trading_room.records`)
keeps each member's forward record in two parts: trades it backed and
trades it did not.

**Cost.** Each decision costs one call per member. Only if someone finds a
trade does it add one debate call per member and one head call. With 4
members and 12 instruments this is roughly 290 to 650 calls a day. Free
tiers run out; set `AI_<NAME>_DAILY_BUDGET` for each provider. A member
whose budget is spent is simply absent.

## How often it decides (`DECISION_INTERVAL_MIN`, `SYMBOLS_PER_CYCLE`)

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
- **Trading room:** up to 9 calls per pair (4 hunt, 4 debate, 1 head).

For example, `DECISION_INTERVAL_MIN=1` with `SYMBOLS_PER_CYCLE=1` in the
trading room is up to 540 calls an hour. Free tiers run out. When a
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
