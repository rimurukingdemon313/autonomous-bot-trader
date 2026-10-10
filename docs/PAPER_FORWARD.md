# PAPER_FORWARD: the bot trades itself on paper and measures its own edge, forward

**PAPER FORWARD TEST · NOT REAL MONEY.** The historical research status is unchanged: **NO EDGE — DO NOT
TRADE.** This mode does not claim an edge. It measures, prospectively, whether the autonomous system has one.

## 1. What it changes, and what it does not

In plain `PAPER`, a deterministic proposal executes on paper, but a language model's own proposal is SHADOW:
priced, recorded and followed forward, never opened (takeover audit). `PAPER_FORWARD` is the one explicit
policy under which **every priced proposal, a model's included, becomes a real simulated paper position**, so
the system's own decisions produce real paper P&L.

Nothing else moves. The authority chain is the same code in both modes:

```
market data → features → regime → memory → agents / AI → synthesis → edge status
  → RISK ENGINE (sizes, approves or rejects; aitrader/risk/engine.py)
  → execution checks (kill switch, pause, account type, stale decision, price drift)
  → HARD RISK GATE (aitrader/risk/hard_gate.py: $500 all-in per trade, $2,000 open, $10,000 daily, $20,000 max)
  → single-use permit → PAPER BROKER (aitrader/broker/paper.py)
```

| | PAPER | PAPER_FORWARD |
|---|---|---|
| Deterministic proposal approved by the risk engine | executed on paper | executed on paper |
| Model proposal approved by the risk engine | SHADOW | **executed on paper** |
| Model proposal rejected by the risk engine or the gate | not executed | not executed |
| Broker | paper | paper **only**: the execution engine refuses any other broker for it |
| Daily loss limit reached | the run locks (FTMO rule) | no new trade until the next reset; the breach is recorded as an FTMO-rule violation |
| Maximum loss reached | the run locks permanently | the run locks permanently |
| First start | paused until an operator resumes | running: setting `MODE=PAPER_FORWARD` is the operator's decision |

A model can never execute directly. It cannot change a limit, the balance, the size or the stop, clear the
kill switch, or override a rejection:
- its numbers pass through the risk engine, which sizes from equity and the stop, never from the model's
  confidence;
- the gate reads the account from the broker itself;
- the paper broker fills only with the gate's permit.

`tests/integration/test_paper_forward.py` proves each of these.

## 2. The paper account (`PAPER-FORWARD-200K`, `aitrader/risk/profile.py`)

| | |
|---|---|
| Starting balance | $200,000 |
| Daily loss limit | $10,000. Measured on equity: realised + unrealised P&L, minus commission and financing still due on open positions, against the day's reference at 00:00 Europe/Prague |
| Maximum loss | $20,000: equity at or below $180,000 locks the run, permanently |
| Risk per trade | at most $500 all-in: stop distance from the executable price, commission $7/lot round trip, 0.5 pip slippage on each fill, 3 nights of financing. Never more after a loss, a win or a confident model |
| Total open risk | $2,000 |
| Targets | $20,000 / $10,000, reported; they never force a trade |

## 3. A position's life

1. **Open.** Each paper position is persisted in the paper account and in `positions`, and survives restarts.
   It records:
   - the trade id, decision id, time, symbol, direction, entry, stop, target, quantity and notional;
   - the planned maximum loss and the expected cost breakdown;
   - the source (`LLM_TRADER`, `EVIDENCE`, …), agent family, model and provider, edge status, and stated
     confidence;
   - the equity and balance at entry, and the quote.
2. **Managed.** Every cycle:
   - prices are read, open positions are valued, and equity is updated;
   - the monitor checks minute and H1 bars for the stop and the target (stop first when both are touched;
     a gap fills at the open);
   - holding-time exits and the model's own review (close or hold) apply;
   - the gate's heartbeat rolls the day and checks the limits.

   With missing, stale or contradictory data: no new trade. Open positions keep their stops and targets, and
   are resolved from the next real bars. No price is ever invented.
3. **Closed.** The paper broker records the net P&L and its exact cost decomposition:
   `gross − commission − financing − slippage − spread = net`.

   The orchestrator writes the outcome:
   - win or loss; gross and net P&L, fees, slippage, spread, financing;
   - R, MFE R, MAE R, holding time;
   - entry and exit reasoning, source, agent and edge status;
   - the regime at entry and exit, and the partition;
   - whether the direction was right (gross > 0);
   - whether the risk estimate held (the loss stayed within the planned maximum).

## 4. Learning: bounded, partitioned, auditable (unchanged architecture)

- Every proposal is in the forward ledger (`forward_proposals`), executed ones with `route EXECUTE`, at
  decision time. Its partition (LEARNING / EVALUATION, by ISO week) is fixed then, never by the result.
- Closed trades become `trades` and `episodes` rows with post-mortems. The model reviews its own closed trade
  (`reflections`), and the experience view records the result.
- Lessons (`learning/taxonomy.py`) are proposed from LEARNING outcomes only and confirmed only on EVALUATION
  outcomes that resolved later. The models' memory of their own trades holds LEARNING-week trades only.
  EVALUATION trades never reach learning.
- No single trade changes anything. Nothing here tunes a parameter or a threshold.

## 5. What is measured

Exposed by `/api/paper_forward` and the dashboard panel, from every closed trade with nothing filtered:
- totals: trades, wins, losses, win rate, gross profit and loss, net P&L, costs;
- per trade: average R, expectancy in R and in $, profit factor;
- risk and timing: maximum drawdown, worst day, average holding time, longest win and loss streaks;
- how often the direction and the risk estimate were right;
- breakdowns by symbol, direction, agent, regime and partition.

Every figure carries its sample label (`insufficient` below 30 trades).

The dashboard shows **PAPER FORWARD TEST** and **NOT REAL MONEY** with:
- account, equity, P&L today, total P&L, drawdown;
- open positions, trades, win rate, expectancy, profit factor;
- risk status (ACTIVE / DAILY_LOCK / MAX_LOSS_LOCK), bot status (RUNNING / PAUSED / RISK LOCK / STARTING),
  and mode;
- the last decisions as `AI DECISION → RISK APPROVED → PAPER EXECUTED`, or `AI DECISION → RISK REJECTED`
  with the exact reason.

## 6. How to run it

Railway or any host: `MODE=PAPER_FORWARD`. That is the only variable needed. Defaults:
- `RISK_PROFILE` = PAPER-FORWARD-200K;
- `PAPER_START_BALANCE` = 200000, and it must match the profile;
- `DATA_SOURCE=yahoo`;
- `DECISION_MODE=evidence`. Set `llm_trader`, `trading_room` or `experimental_ai` for the model traders, with
  `AI_PROVIDER`, `AI_BASE_URL`, `AI_MODEL` and `AI_API_KEY` configured in the host's own secret settings.

GitHub: `.github/workflows/paper-forward.yml` runs the same service in 6-hour shifts. The paper account is
carried between shifts, and the panel is published every 15 min to `REPORT.md` and `paper_forward.json` on the
`paper-forward-data` branch. The repository variable `PF_DECISION_MODE` and the secret `AI_API_KEY`, added by
the owner in the repository settings, switch it to a model trader.

`MODE=LIVE`, `LIVE_TRADING=true`, `MODE=DEMO` and `EXPERIMENTAL_EXECUTE=true` are all refused at startup. No
broker other than the paper broker exists.

## 7. Reading the result honestly

- Fewer than 30 closed trades is anecdote.
- The forward-eligibility definition (`learning/metrics.py`) needs 100 EVALUATION outcomes, t ≥ 2.5, positive
  at doubled costs and in both halves. It is the bar for even asking an operator to review.
- The deterministic system's history is already known. PR-001 C, 2010–2016, ran bar by bar with real bid/ask
  and costs: −0.072 R per trade over 2,928 trades, t −2.9, negative in 5 of 7 years.
- A model trader can only be judged here, forward. It cannot be judged on history it may have memorised.

## Decision systems

Any decision mode runs here through the same risk engine, hard gate and paper broker. `DECISION_MODE=dual_ai` (docs/DUAL_AI.md) is the two-trader desk on free OpenRouter models; the GitHub run selects it automatically once the `OPENROUTER_API_KEY` secret exists.
