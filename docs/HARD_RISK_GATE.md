# The hard risk gate (FTMO-style $200K paper evaluation)

**PAPER ONLY.** The gate decides whether a paper order may be filled. It enables nothing: there is no live path
in this build, and the gate adds none.

The purpose is to find out whether a strategy can survive FTMO-style constraints before any real capital is
considered. Every limit is enforced by deterministic Python, never by a prompt. A model's output is an
untrusted proposal; the gate has the final word.

## 1. Where it sits: there is no path around it

```
AI / strategy decision
  -> trade validation   risk engine (sizes; aitrader/risk/engine.py) + execution checks (kill switch, pause,
                        account type, model trades refused, stale decision, price drift)
  -> HARD RISK GATE     aitrader/risk/hard_gate.py: TRADE (single-use permit) or NO TRADE
  -> execution permit   bound to symbol, side, size, stop, target and client id; expires in 10 s
  -> paper broker       aitrader/broker/paper.py: fills only with a valid, unused permit
```

| Path someone could try | What happens |
|---|---|
| Build an `ExecutionEngine` without a gate | `TypeError`: `gate` is a required argument and must be a `HardRiskGate` |
| Call `PaperBroker.place_market` directly | `BrokerRejected: NO_EXECUTION_PERMIT` |
| Call it on a broker with no gate attached | `BrokerRejected: NO_RISK_GATE` |
| Forge, alter (e.g. 1 lot → 12 lots) or reuse a permit | `BrokerRejected: INVALID_EXECUTION_PERMIT` |
| Swap the gate attached to a broker | `BrokerError`: a gate is attached once |
| Two requests at once that would together exceed the open-risk limit | the gate is held from authorisation to the broker's answer, and an approval is reserved in the gate's state before the order is sent |
| The same decision sent twice, concurrently or not | one intent per decision (`DUPLICATE`); the gate also refuses a decision or client id it has authorised before |

The backtest runner uses the same engine and gate: the FTMO percentages on its own balance.

## 2. The profile (`aitrader/risk/profile.py`)

`HardRiskProfile` is a frozen, validated dataclass. An inconsistent profile cannot be constructed: risk per
trade ≤ open risk ≤ daily loss ≤ maximum loss < starting balance, a known time zone, and finite positive
numbers.

The default, `FTMO-200K`:

| | |
|---|---|
| Starting balance | $200,000 |
| Daily loss limit | $10,000 (5%) |
| Maximum total loss | $20,000 (10%): equity may never reach $180,000 |
| Challenge target | $20,000 (10%) |
| Verification target | $10,000 (5%) |
| Minimum trading days | 4 |
| Risk per trade | $500 (0.25% of the starting balance), costs included |
| Total open risk | $2,000 (1.0%) |
| Daily reset | 00:00 `Europe/Prague` (FTMO's published midnight CE(S)T). It is a profile field; nothing assumes UTC |
| Max quote age / spread / entry deviation | 30 s / 0.2% of mid / 0.2% from the executable price. The service sets the quote age to the data source's tolerance the risk engine already uses: 90 s for the public Yahoo feed, which timestamps its own price, capped at 90 s, unless `RISK_PROFILE_OVERRIDES` sets it |
| Cost model | commission $7 per lot round trip, 0.5 pip slippage per fill (the paper broker fills at 0.1), financing for 3 nights |
| Account constraints | leverage 1:30 for margin, at most 50 lots per order, at most 5 positions |

Targets are reported, never pursued. They never force a trade.

**Configuration:**
- `RISK_PROFILE` selects a profile by name. An unknown name is refused, never replaced by the default.
- `RISK_PROFILE_OVERRIDES` is a JSON object of fields. An unknown field is refused.
- `PAPER_START_BALANCE` must equal the profile's starting balance, or the service refuses to start.

The gate records the profile's sha256 when an evaluation run starts. A different profile during that run is
refused (`PROFILE_CHANGED`).

## 3. The rules: any one fails → NO TRADE

Checked in this order. The first failure is the rejection code; every rejection is logged with its calculation.

| # | Code | Rule |
|---|---|---|
| 1 | `STATE_CORRUPT` | the gate's state is missing (while a run is logged), fails its checksum or schema, or contradicts the log. **Kill switch** |
| 2 | `PROFILE_CHANGED` | the profile is not the one the run started with |
| 3 | `RISK_LOCKED` | the run is locked (daily or maximum loss breached). Permanent for the run |
| 4 | `KILL_SWITCH_ACTIVE` | the gate's kill switch, or the system kill switch, is active or **unreadable** |
| 5 | `RISK_DATA_UNVERIFIED` | account or positions unreadable, or an open position cannot be valued. **Kill switch** |
| 6 | `IMPOSSIBLE_ACCOUNT_STATE` | non-finite or non-positive balance or equity, wrong currency, equity ≠ balance with nothing open, unrealised P/L larger than the open notional, or the clock running backwards. **Kill switch** |
| 7 | `DUPLICATE_EXECUTION_STATE` / `CONFLICTING_EXECUTION_STATE` | duplicate positions or client ids, a position the gate never authorised, or one that differs from what was authorised or has no stop. **Kill switch** |
| 8 | `MAX_TOTAL_LOSS` | conservative equity ≤ $180,000. **Locks the run** |
| 9 | `DAILY_LOSS_LIMIT` | conservative equity ≤ day reference − $10,000. **Locks the run** |
| 10 | `DUPLICATE_REQUEST` | decision or client id already authorised, or already known to the broker |
| 11 | `INVALID_INSTRUMENT` | malformed symbol, or no tradable specification (contract size, conversion rate) |
| 12 | `MARKET_DATA_MISSING` / `_CONTRADICTORY` / `_STALE` / `_OUT_OF_TOLERANCE` | no or non-finite quote, ask < bid, older than the profile's quote age, spread too wide |
| 13 | `INVALID_ENTRY` / `MARKET_DATA_OUT_OF_TOLERANCE` | proposed entry not a positive finite price, or more than 0.2% from the executable price |
| 14 | `MISSING_STOP_LOSS` / `INVALID_STOP_LOSS` / `INVALID_TARGET` | no stop; a stop not on the loss side; a target not on the profit side |
| 15 | `INVALID_POSITION_SIZE` / `BROKER_CONSTRAINT` | size not finite, positive, a lot-step multiple or at least the minimum; above the maximum lots |
| 16 | `RISK_NOT_COMPUTABLE` | financing estimate not a number, or a maximum loss that is not positive and finite |
| 17 | `PER_TRADE_RISK` → `FEES_EXCEED_RISK` → `SLIPPAGE_EXCEEDS_RISK` → `FINANCING_EXCEEDS_RISK` | the loss at the stop, then plus commission, then plus slippage, then plus financing, exceeds $500. The code names the cost that tipped it |
| 18 | `OPEN_RISK_LIMIT` | open and in-flight risk plus this trade > $2,000 |
| 19 | `BROKER_CONSTRAINT` | more than 5 positions open or in flight |
| 20 | `DAILY_LOSS_LIMIT` (would breach) | equity − every open position's loss to its stop − this trade's maximum loss ≤ the daily floor. Refused, not locked |
| 21 | `MAX_TOTAL_LOSS` (would breach) | the same against $180,000 |
| 22 | `MARGIN_INVALID` / `MARGIN_UNAVAILABLE` | required margin (notional / leverage) not computable, or above free margin |
| — | `EVALUATION_REFERENCE_MISMATCH` | an evaluation run starts only from a flat account at exactly the starting balance, in the profile's currency |

An unexpected exception anywhere in the gate is `RISK_DATA_UNVERIFIED` with the kill switch. It never fails
open.

### A trade's maximum loss (`loss_per_lot`, shared with the risk engine)

```
per lot = |executable entry − stop| × contract size × value per price unit     (the spread is inside: entry is the ask for a buy)
        + commission round trip                                               ($7)
        + 2 × slippage pips × pip × contract size × value per price unit       (both fills)
        + max(0, swap per night) × 3 nights × contract size × value per unit   (a financing credit never counts)
max loss = per lot × lots
```

The risk engine sizes with this same function, within `min(equity × 0.25%, $500 × loss-streak multiplier)`. So
risk never grows after wins, only shrinks after losses, and the size it picks is the one the gate verifies. The
gate re-checks at submission against the live quote. If the spread widened in between, the trade is refused,
not resized: the gate never sizes and never changes a trade.

### Daily loss, on equity

```
conservative equity = broker equity (balance + unrealised P/L)
                      − commission still due on open positions − financing accrued on them
day reference       = at the first observation after the reset (00:00 Europe/Prague):
                      max(balance, conservative equity, the previous day's last observed equity and balance)
daily P/L           = conservative equity − day reference
daily floor         = day reference − $10,000
```

The orchestrator calls `observe()` every cycle, so the reference is taken promptly after the reset and a breach
locks the run even when nothing is proposed. Losses between the last observation and the reset are counted on
the new day, which is the conservative side. Every rejection logs these numbers.

## 4. Lock and kill switch

| | Trips on | Cleared by |
|---|---|---|
| **Risk lock** | `DAILY_LOSS_LIMIT` or `MAX_TOTAL_LOSS` actually breached (FTMO fails the account on either) | only `reset_evaluation(broker, "RESET-EVALUATION", reason)`, which needs a flat account at the starting balance. Never automatic, never by a model, never by the dashboard |
| **Kill switch** | corrupt state, impossible values, conflicting or duplicate execution state, unverifiable risk data, or a lock | `clear_kill("CLEAR-KILL-SWITCH", reason)` for the data/state causes only, never for a lock; or an evaluation reset |

A lock or kill also sets the system `kill_switch` so the whole service stops. Clearing that system switch from
the dashboard does **not** clear the gate: it refuses on its own state.

Both survive a restart. The state is one checksummed row in `risk_gate_state`. Every decision and lifecycle
event (`RUN_STARTED`, `LOCKED`, `KILL_SWITCH`, `FILLED`, `RELEASED`, `RUN_RESET`) is an append-only,
hash-chained row in `risk_gate_log`. On every call the state is re-read and cross-checked:
- deleting the state does not unlock: the log still records the run;
- editing it fails the checksum;
- re-checksumming an edited unlock contradicts the logged lock.

A broken log chain cannot be reset away. It needs a new database.

## 5. What a model cannot do

It cannot change a limit, the balance, the profile or the size. It cannot remove the stop, clear the kill
switch, unlock the run, or reach the broker without a permit.

The gate reads only the numbers of a `TradeProposal`: symbol, side, size, entry, stop, target, financing. It
reads the account from the broker itself. Anything else a decision carries (`confidence`, `override`,
`risk_pct`, instructions) is never read. The profile is frozen, and the gate exposes it read-only.

## 6. Audit log

Every decision writes a `DECISION` row (`risk_gate_log`) with:
- the timestamp, symbol, side, proposed entry, stop loss and size;
- the monetary risk and its breakdown;
- balance, equity and conservative equity;
- daily P/L, total drawdown and open risk;
- estimated fees, slippage and financing;
- the result, the rejection reason, and the final decision (`PERMIT_ISSUED` / `NO TRADE`);
- the full calculation.

It also writes one structured stdout line:

```
RISK_GATE_REJECTED reason=DAILY_LOSS_LIMIT equity_conservative=189500.00 daily_pnl=-10500.00 daily_limit=-10000.00 ...
```

## 7. Example: an AI TRADE decision rejected

The account is down $9,700 today, realised. A model proposes BUY 5 lots EURUSD at 1.10005 with a stop at
1.09925, "confidence 0.97", `override_risk=True`. The risk engine approved the size: $485 all-in, under $500.
The execution engine sends it to the gate:

```
STATUS BLOCKED
RISK_GATE_REJECTED reason=DAILY_LOSS_LIMIT equity_conservative=190300.00 daily_pnl=-9700.00
  daily_limit=-10000.00 total_pnl=-9700.00 total_limit=-20000.00 open_risk=0.00 max_loss=485.00
  detail='if every stop is hit: equity 190300.00 - open 0.00 - this trade 485.00 = 189815.00 <= daily floor
  190000.00 (reference 200000.00 - limit 10000.00)'
broker positions: []
```

The trade is within the per-trade limit, but taking it could breach the daily limit. NO TRADE; nothing
reached the broker. The model's `override_risk` and `confidence` were never read.

## 8. Operator command

`python scripts/risk_gate.py status | log [N] | clear-kill "reason" | reset-evaluation "reason"` (with
`--data-dir`). None of it is reachable from the dashboard or a model.

## 9. Tests

`tests/unit/test_hard_gate.py` has 82 cases:
- the 22 required behaviours, numbered in the test names;
- every rejection code, the bypass paths in §1, and the corruption cases;
- the daily reset in winter and summer time;
- a seeded random-sequence invariant: no approved trade ever exceeds $500, the open risk never exceeds
  $2,000, and the log chain stays intact.

`scripts/mutation_audit.py` removes each gate check in turn (`gate-*`). The tests catch every one.

## 10. Limitations

- **Single process.** The aggregate-limit lock is in-process. Two service processes on one database could
  each authorise against a stale view. The service runs one process; do not run two.
- **Equity-based daily loss is a conservative reading of FTMO's rule.** FTMO measures from the day's starting
  balance. Here the reference is the higher of balance and equity at the reset, and open costs are deducted.
  It can refuse trades FTMO would allow, never the reverse.
- **Breaches are judged at observation and authorisation times.** A paper position's stop is filled on the
  next bar. Between observations, equity can dip through a floor and back without a lock.
- **The cost model is declared, not measured.** Commission $7 per lot, 0.5 pip slippage per fill and 3 nights
  of financing are assumptions. The financing estimate comes from the decision's ATR-based swap. For a pair
  quoted against another currency, values use the paper broker's conversion rate.
- **The gate verifies, it does not size.** If a quote moves between the risk check and submission, a trade
  sized right at $500 can be refused. That is intended: refused, never resized.
- **A data outage with positions open trips the kill switch.** An open position that cannot be valued is
  unverifiable risk. Trading stays off until `scripts/risk_gate.py clear-kill "reason"`.
- **An existing paper database** whose account is not flat at $200,000 cannot start an evaluation. Use a new
  `DATA_DIR`, or reset the paper account first.
