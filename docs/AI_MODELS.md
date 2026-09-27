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
| `AI_TIMEOUT_S` | `20` | per call |
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
