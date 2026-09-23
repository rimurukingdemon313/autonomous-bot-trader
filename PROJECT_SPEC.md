# Project specification

Status: **Phase 0 — specification.** Nothing described here exists yet as
code. Where this document says "the system does X", read it as "the system
must do X when it is built".

---

## 1. Objective

Build an **Autonomous AI Trading Intelligence** that can:

| Capability | Meaning |
|---|---|
| Research | examine market data for relationships that could be traded |
| Hypothesis generation | state a candidate relationship precisely enough to be tested and fail |
| Feature discovery | propose and evaluate new measurable descriptions of market state |
| Regime detection | recognise which kind of market it is in, including "a kind I have not seen" |
| Opportunity detection | evaluate candidate trades across instruments, timeframes and contexts |
| Probabilistic decision making | act on estimated probabilities and expected value, with stated uncertainty |
| BUY / SELL / NO_TRADE | choose a direction, or choose not to trade |
| Entry and exit reasoning | justify entry, stop, target and exit logic, and state what would invalidate the idea |
| Learning from outcomes | attribute results to causes and turn that into new, testable hypotheses |
| Continuous research | keep doing the above offline, without changing the live system on its own |

Every one of these is subject to:

- data integrity ([DATA_CONTRACT.md](DATA_CONTRACT.md));
- statistical validation ([VALIDATION_CONTRACT.md](VALIDATION_CONTRACT.md));
- risk controls ([RISK_CONTRACT.md](RISK_CONTRACT.md));
- execution controls ([EXECUTION_CONTRACT.md](EXECUTION_CONTRACT.md));
- no look-ahead and no data leakage (§9 below);
- versioning ([docs/VERSIONING.md](docs/VERSIONING.md)).

## 2. No fixed strategy

The project does **not** impose any trading method. Specifically, none of
the following is required, preferred or assumed:

SMC · ICT · RSI · MACD · moving averages · Bollinger Bands · VWAP ·
momentum · mean reversion · breakout · carry · any other named strategy.

The AI may use any of them once the data shows it adds value, may combine
or modify them, and may discover approaches that have no name. It may also
reject all of them.

The one requirement is that whatever it uses is:

- **TESTABLE**: stated precisely enough that data can show it is wrong;
- **VERSIONED**: identified exactly, so any result can be traced to the
  code, data and parameters that produced it;
- **VALIDATED**: it passed the validation contract on data that played no
  part in choosing it.

## 3. AI freedom

Once built, the AI may choose, without a user-supplied strategy:

- the **instrument**;
- the **timeframe**, or combination of timeframes;
- how to describe the **market regime**;
- which **features** matter;
- which **model** to use;
- **entry**, **stop**, **target** and **exit logic**;
- **NO_TRADE**.

Its freedom stops at one boundary: **the AI cannot bypass the risk
engine.** It cannot size a position, raise a limit, skip a check or reach
the broker by any other route. It proposes; the risk engine approves or
rejects ([RISK_CONTRACT.md](RISK_CONTRACT.md)).

Freedom is also bounded by honesty. An unbounded search over rules tests an
uncountable number of hypotheses, and a result from an uncountable search
cannot be corrected for chance. So every choice the AI can make is drawn
from something **declared and counted**: a declared feature set, model
family, action set or hypothesis space. The AI can widen those spaces
through the research process, and each widening is registered and counted
([RESEARCH_CONTRACT.md](RESEARCH_CONTRACT.md) §5).

## 4. NO_TRADE is a valid outcome

- **NO_TRADE is not a failure.** When the system cannot find enough
  evidence of an edge, NO_TRADE is the correct decision.
- NO_TRADE is better than a low-quality trade.
- There is **no minimum number of trades**, per day, week, month or ever.
- There is **no requirement to trade daily.**
- A system that correctly declines to trade for months has done its job
  for those months.

Every NO_TRADE is recorded with its reason, exactly as a trade is. A
NO_TRADE decision is evidence about the system just as a trade is.

## 5. Capital objective

The objective is **not**:

- maximum historical profit;
- maximum win rate;
- guaranteed income;
- a fixed monthly profit (including a $1,000 monthly target);
- doubling the account;
- aggressive growth.

The objective is:

> **Robust positive expectancy + capital preservation + generalization +
> controlled drawdown.**

Any future financial goal is a **scenario**: arithmetic about what an edge
of a given size would produce at a given risk. It is never a trading
constraint. No component may take a trade, raise risk or lower a
threshold to meet one.

For scale: monthly return ≈ risk per trade × trades per month × average R
per trade. At 0.5% risk and 20 trades a month, a genuinely strong edge of
+0.10R gives about 1% a month, so $1,000 a month needs about $100,000 of
equity. Even that edge would lose money in roughly one month in three.

## 6. Learning philosophy

Required:

```
Observation → Hypothesis → Experiment → Validation → Out-of-sample test
  → Robustness test → Version → Deployment candidate
```

Forbidden:

```
Loss → change random parameters → backtest again → repeat until profitable
```

The forbidden loop is not a weaker form of research. It is a procedure
that is guaranteed to find something that looks profitable on past data
and has no reason to work on future data.

The system learns **from** losses. It does not react **to** them. A loss
may lead to a new hypothesis, tested like any other. It never leads
directly to a larger position, a revenge trade, a doubled size or a relaxed
limit.

## 7. Production lifecycle

```
RESEARCH → BACKTEST → OUT-OF-SAMPLE → ROBUSTNESS → FINAL HOLDOUT
  → PAPER → DEMO → LIVE
```

- Each transition has an evidence gate ([docs/SYSTEM_LIFECYCLE.md](docs/SYSTEM_LIFECYCLE.md)).
- Each transition from PAPER onwards requires **explicit human approval**.
- **There is no automatic transition to LIVE, under any condition.**
- A failure at any stage sends the candidate back, and it is recorded as
  FAILED ([docs/FAILURE_POLICY.md](docs/FAILURE_POLICY.md)).

## 8. Decision record

Every decision, including NO_TRADE, is recorded **before** anything is sent
to the risk engine. The record will contain at least:

decision (BUY / SELL / NO_TRADE) · instrument · timeframe · decision
timestamp · market state · regime · familiarity (how similar this state is
to the training data) · thesis · supporting evidence · contradicting
evidence · proposed entry · stop · target · exit logic · invalidation ·
estimated probability · expected R after costs, with its uncertainty ·
the reason for NO_TRADE when that is the decision · model version · feature
version · data version · research version · code version.

The record is proposal and evidence only. Size and risk amount are added
by the risk engine and are never produced by the AI.

## 9. The future-information rule (non-negotiable)

> **A decision at time T may only use information that was genuinely
> available at or before time T.**

This covers, without exception:

prices · indicators · labels · normalization statistics · model selection ·
feature selection · hyperparameters · news · sentiment · correlations ·
market state · regime definitions · thresholds · anything a language model
"knows".

"Available at T" means available **in the form the live system would have
had it**. A bar that closes after T is not available at T. A statistic
computed over a period ending after T is not available at T. A revised data
point was not available in its revised form at T.

Enforcement is by test, not by review: [docs/TESTING_PHILOSOPHY.md](docs/TESTING_PHILOSOPHY.md).

## 10. Out of scope, until approved

- Real-money trading of any kind.
- High-frequency or latency-sensitive strategies. The infrastructure is not
  built for them, and a backtest cannot represent their costs honestly.
- Any data source this project does not actually have.
- Notifications (for example Telegram) before the core system works.
  Priority order: core > data > AI > risk > execution > persistence >
  dashboard > notifications.

## 11. What "success" means

Success is not a profitable backtest. A profitable backtest is the easiest
thing in quantitative finance to produce and the least informative.

The system has succeeded when it can answer these with evidence:

1. Does it generalise to data that played no part in building it?
2. Does it survive realistic and pessimistic costs?
3. Does it hold across regimes, instruments and periods?
4. Does it reject bad trades?
5. Is it free of leakage, as demonstrated by adversarial tests?
6. Can it be operated safely, and recover from failure?

A clear, evidenced "no edge was found" also counts as a successful result
of the research. It is recorded and reported as exactly that.
