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
| A late public price | Yahoo stamps its own prices and is sometimes a minute or two late; the hard gate refuses a quote older than 90 s. On a live feed the execution engine waits, bounded (up to 6 x 15 s), for the next price before the gate decides: a read retried, nothing sent (exec 1.8.0) |
| Weekend | no new position whose maximum holding time could run past the Friday close (17:00 New York): the market shuts for two days and reopens where it likes (risk 1.7.0) |
| Quiet hours | no new position from 16:00 to 20:00 New York (DST-aware), an hour before the 17:00 rollover to the Tokyo open: liquidity is thinnest and spreads widest then. Open positions are kept and managed. The risk engine's own limit for MODE=PAPER_FORWARD, not a field of the evaluation profile (a profile cannot change during an evaluation) |
| Closed days and hours | no new position in the London/New York overlap, 12:00-16:00 UTC (the session the desk did worst in: 8 trades, -0.38 R), on Friday from 12:00 UTC to the weekend, nor on Saturday or Sunday. Friday before 12:00 UTC trades (the one Friday so far, all entered then: 9 trades, +2.88 R). The operator's choice, 2026-10-17; the risk engine's own calendar for MODE=PAPER_FORWARD (risk 1.9.0), not a field of the evaluation profile. Open positions are kept and managed |
| Against itself | no new position on the opposite side of a currency an open position holds (long EUR while short EUR): 11 such trades won 36%, -0.21 R each, the others +0.23 R (risk 1.9.0) |
| Chop | no new position unless the pair's H1 market structure is a clear trend, up (HH+HL) or down (LH+LL); a range or an unreadable structure refuses it. Of the first 50 agreement trades, the 23 in an H1 range won 30%, -0.24 R each; the 27 in a clear trend +0.23 R (risk 1.12.0, the operator's choice, 2026-10-19). Checked after the traders answer: refused agreements are followed forward |
| News | no new position from 30 min before to 30 min after a High- or Medium-impact scheduled release (ForexFactory economic calendar) for either currency of the pair; Low impact never closes the window; with no readable calendar (none for 3 days) event risk is unknown and no new position is opened (risk 1.10.0; Medium since 1.11.0, the operator's choice, 2026-10-19). The traders are not asked then |
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
- Each rule is judged on its own trades. With the dual-AI desk, `REPORT.md` opens with the rule that trades
  (both AIs agree) and says, under it, how many trades of a retired rule the account also holds and what they
  made; every closed trade carries its `rule`, and `performance.by_rule` has each rule's figures.
- The account moves only by closed trades and by operator adjustments declared in code
  (`aitrader/broker/adjustments.py`), never by a request or a model. An adjustment applies once, at startup, only
  when every trade it names is in the journal with the rule it names; it is journaled and shown next to the
  equity (`adjustments_total`, `equity_before_adjustments`), and P&L today excludes it. The trades it removes
  stay in the journal and are listed apart (`removed_trades`). One exists: the 4 trades of the retired debate
  rule (2026-10-15, +$1,416.51). Made after the day's reference was taken, it gives that one day's loss limit the
  same headroom; the gate's floors are otherwise unchanged.
- The new account (`aitrader/broker/periods.py`, owner 2026-10-27: "I don't want it negative"; chosen over
  carrying on). The paper account had lost $3,454 under the setups replaced on 23-26 October. A period is a new
  paper account for the setup trading now: $200,000 from 2026-10-26 16:22 UTC, the first shift with both
  traders paid and every trade on Trader 1's levels.
  - Only the trades opened from then move it: by their booked net P/L once closed, by their open P/L while
    open.
  - `REPORT.md` shows it first. Under it are the trades before it, kept and apart, and the whole paper journal.
  - Nothing is moved, removed or reset. The broker's balance, the hard gate and the risk engine keep
    guarding the whole account, and the risk engine's size after the losing streak is unchanged.
  - An unreadable value makes its equity None.
  - The Friday decision on the setup is read from this account.
- Who lost it, the market or us (`aitrader/learning/blame.py`, owner 2026-10-25: "if we lose, let it be the
  market"). Every closed trade is checked against what the system controls, from its own journal, and
  `REPORT.md` shows the result under the account, with a column on each closed trade. The checks:
  - the rules and the hard gate approved it, with every check passed;
  - its data was not flagged, and the fill's quote was within the gate's age;
  - it was sized within the per-trade risk;
  - both traders chose its side;
  - it closed by its time exit, and was not open over a weekend;
  - its costs were as planned (1.5 times, plus $5).

  A trade that fails one is **ours**, a defect, named with the check it failed. A check that cannot be read
  counts as ours too. A trade that passes them all is the market's: at its stop within the plan, by its time
  exit, or stopped beyond the plan (a gap or the spread at the stop, named, with the rollover marked).
  - On the first 99 agreement trades, to 2026-10-23, all 56 losses ($-18,545.89) were the market's: 50 at the
    stop within the plan, 5 by the time exit, and 1 beyond it (GBPJPY, $-644.82 against $498.95, in the
    rollover).
  - The 4 trades of the retired debate rule are ours (not both traders' choice), and were already taken out of
    the account.
  - A loss being the market's says the system did what it is built to do. It does not say the trade had an
    edge: that is what the expectancy, over enough trades, measures.
- Risk 1.14.0 and orchestrator 1.23.0 (found while building that check): the risk engine measured the quote's age
  from the decision time. On a quote read after a 5-minute answer it read "age -297s", so it could never find a
  stale price; only the hard gate, on its own clock, could. The quote is now asked for, and its age judged, at
  the moment the position would open. A quote stamped more than 5 s after that is refused, as the gate refuses
  it.

## Decision systems

Any decision mode runs here through the same risk engine, hard gate and paper broker. `DECISION_MODE=dual_ai` (docs/DUAL_AI.md) is the two-trader desk on free OpenRouter models; the GitHub run selects it automatically once the `OPENROUTER_API_KEY` secret exists.
