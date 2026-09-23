# Risk contract

The risk engine is independent of the AI, and it is the final authority on
whether anything is sent to the broker.

```
AI  ──PROPOSES──►  RISK ENGINE  ──APPROVES OR REJECTS──►  EXECUTION
```

---

## 1. Independence

- The risk engine is separate code, with its own version and its own
  tests. It does not import from the AI, and the AI cannot configure it.
- It is the **only** component that computes a position size, a risk
  amount or a limit. A size computed anywhere else (in a model, a prompt,
  the dashboard or the executor) is a second source of truth, and is a
  defect.
- **The AI cannot bypass it.** There is no override flag, no trusted
  caller, no "high confidence" exemption, and no configuration that
  disables it. A higher model confidence never raises a limit.

## 2. What it protects

| Protection | Meaning |
|---|---|
| Per-trade risk | a hard ceiling on the fraction of equity at risk on one trade |
| Daily loss | trading stops for the day once the limit is reached |
| Maximum drawdown | trading halts at the limit, and resumes only with human action |
| Leverage | a ceiling on notional exposure relative to equity |
| Exposure | limits per instrument, per currency and per correlated group |
| Concurrent positions | a ceiling on the number open at once |
| Spread | no entry when the live spread is too large relative to the stop |
| Slippage | a limit on accepted slippage; persistent excess reduces activity |
| Abnormal conditions | stale data, extreme volatility, gaps, market closure or rollover: no entry |
| Duplicate orders | the same decision cannot produce two orders |
| Broker failures | unknown account state: no new orders |
| API failures | failure to read state is treated as unsafe, never as zero |
| Emergency shutdown | a kill switch that stops new orders at once |
| Funded-account constraints | a compliance layer enforcing the rules of a specific prop-firm account, supplied by the owner |

Limits are expressed in R and in fractions of equity. Where a funded
account imposes a stricter rule than these defaults, **the stricter rule
wins**.

## 3. Risk only ever decreases in response to adverse state

- Losses, drawdown, a losing streak, degraded execution or model drift may
  **reduce** risk, or stop trading.
- **Nothing may increase risk in response to a loss.** Specifically:
  - no martingale;
  - no doubling size;
  - no revenge trade;
  - no "recover the loss" logic;
  - no relaxing a limit to get back to where the account was.
- Risk returns to its normal level only through an explicit, pre-declared
  recovery rule, or by human decision. It never rises above normal.

This is guarded by a test that simulates losing sequences and asserts that
approved risk is non-increasing throughout.

## 4. Fail closed

| If this cannot be established | Then |
|---|---|
| Account equity or balance | no new orders |
| Open positions | no new orders |
| The kill switch's state | treat it as active |
| That the account is the intended type (demo or live) | no trading, kill switch trips, and the message names the fields it checked |
| The live spread | no entry |
| Persistence is available | no new orders |

## 5. Account type verification

Until LIVE is explicitly approved (Phase 12), the system operates on
**demo or paper only**. The account type is verified from **two
independent signals**, and both must agree:

1. the configured endpoint is a demo endpoint and matches no live marker;
2. the broker's own evidence says demo.

A live marker in either signal fails the check. **Missing evidence fails
the check.** Only positive evidence passes. Verification happens at
startup, at connection, before an order is created, and before it is
submitted.

## 6. Operator controls, split by direction

- Controls that can only **reduce** activity (kill switch, pause) are
  always available, from any device, without needing a credential. An
  operator must always be able to stop the system.
- Controls that **resume, widen or initiate** activity require
  authentication. With no credential configured, those controls are
  refused rather than left open.

## 7. Funded-account compliance

A separate layer, inside the risk engine's authority, enforces the rules of
a specific funded or prop-firm account: daily loss, maximum loss, trailing
drawdown, news restrictions, holding rules, consistency rules and similar.
**The rules are supplied by the owner.** They are not guessed, and until
they are supplied, no funded-account mode exists.

## 8. What the risk engine does not do

It does not look for trades, predict prices, or second-guess a model's
thesis. It answers one question: *is it safe and permitted to take this
proposal, and at what size?*
