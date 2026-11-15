# EXF-1: do perpetual futures price their discrete funding payments?

Preregistered on 2026-11-15, before any bar of the study is read. The funding rates were read (they are the payments
that define the events; the probe, below); no price, premium or index bar was.

| | |
|---|---|
| Program | EXF-1, stages `dev`, `validation`, `holdout`, `replication`, `forward`, judged once each, in that order |
| Code sha256 | `fa1bcf9e49b2860193041d093c3894ed8f9532af2003db99e8a2137f4daed0c5` (`python scripts/exf1.py hash`, first value) |
| Spec sha256 | `8f338635b66666a91fe09e20d5faf3708e7a07c6e7a63b5ebb4df0c4d4637a3a` (the `SPEC` in `scripts/exf1.py`; second value) |
| Code | `aitrader/research/events/exfunding.py`, `scripts/exf1.py`, run by `.github/workflows/exf1.yml` |
| Universes | `crypto-perp-funding-settlements` (Binance USDT-M), `crypto-coinm-funding-settlements` (Binance COIN-M): new in the registry |
| Bar | max(3.0, Bonferroni over the tests on the universe and window): 3.0 for every stage |

## 1. The mechanism, from first principles

A perpetual future costs nothing to enter. At each settlement time T its holders exchange a payment: a long pays
F_T times the notional, a short receives it (the other way when F_T < 0). The payment is a lump at a known time,
and its size is known in advance to within the last minutes of the interval (it is an average of the premium over
the interval).

**The frictionless prediction.** Let P be the perpetual's price and I its index, prem = P / I - 1. A long held from
just before T to just after pays F_T P_T at T. A long opened just after T pays nothing for that settlement. A
zero-cost contract's expected gain over any interval must equal the expected value of its cash flows over it, so

    E[ P(T+) - P(T-) ] = F_T P(T)        and therefore        E[ prem(T+) - prem(T-) | F_T ] = beta F_T, beta = 1.

The index carries no such payment, so the premium alone jumps, and drifts back by the carry between settlements: a
saw-tooth whose teeth are the funding. This is the ex-dividend argument (a share falls by its dividend when it goes
ex) applied to a payment that can have either sign.

**Why beta can differ from 1, and who makes it.** The jump is enforced only by traders who time their positions
around T. Those who hold through every settlement (leveraged traders with a view, most of the open interest) pay or
receive F_T whatever the price does, and do not trade at T. Those who do time it (close before, reopen after) pay
two fills, so they act only when |F_T| exceeds their costs. Arbitrageurs who would sell the jump must hold the
paying side across T, carry the contract's risk for the window, and pay fees. If timing traders are few, the price
passes on less than the payment (beta < 1) and the side that receives it can hold only across T and keep
(1 - beta)|F_T|. If funding-avoiding orders crowd the minutes before T, the price can over-react (beta > 1) and the
paying side earns. Neither is assumed: beta is measured.

**When it should appear and disappear.** The unpriced part is (1 - beta)|F_T|, so it can pay only where |F_T| is
large: crowded positions, small contracts, squeezes. It should be absent in the dead zone of Binance's formula
(F_T = 0.01% whatever the premium), where the payment is too small to time, and it should shrink as timing bots
compete for it. An exchange that prorated funding to the time held would remove it.

**Holding period and risk.** Ten minutes, from the close of the 5-minute bar ending at T-5m to the close of the bar
ending at T+5m. The position is not hedged: it carries the contract's price for ten minutes, and the risk that the
payment settled at T has another sign or size than the previous one, which chose the side.

**The relation to expected return.** With s = -sign(F_hat) the side F_hat says receives the payment and c the cost
of a fill,

    E[net] = E[ s r_perp - s F_T ] - 2c = sign(F_hat) E[(1 - beta) F_T] - E[ sign(F_hat) r_index ] - 2c,

so the rule earns only if the price passes on less of the payment than the payment exceeds two fills.

## 2. What is known, and how this differs

- **Funding carry** (CR-1 to CR-5 and RADAR-1 in this registry; cash and carry in general) holds the receiving side
  for days to collect many payments, exposed to the premium's drift and to the round trip. EXF-1 holds across one
  payment for ten minutes, and its profit is not the payment but the part of it the price fails to take back.
- **Practitioners' "funding sniping"** opens just before the timestamp to collect a payment. EXF-1 measures how much
  of the payment the price takes back, against the frictionless prediction, and requires the effect to be absent at
  the same distance from no settlement.
- **A public research log** (github.com/jienotas/funding-rate-event-study, unreviewed; seen only as a search
  result, not read) reports, for BTC and ETH, more volume and range after a settlement than three hours later, no
  change in absolute returns, and a price-pressure design that did not identify an effect. EXF-1 measures the
  SIGNED premium move against the SIZE of the payment across every USDT-M contract, where |F| ranges over three
  orders of magnitude: a dead-zone payment of 1 bp is invisible in BTC's returns, a payment of 50 bp is not.
- **Theory** (He, Manela, Ross & von Wachter 2022; Ackerer, Hugonnier & Jermann 2024; seen as search results, not
  read in full) prices perpetuals with continuously accruing funding, where no jump exists. The saw-tooth is the
  discrete-settlement case those models smooth away.
- **Ex-dividend studies** (Elton & Gruber 1970 and the work after it): the analogy. Here there are no taxes, the
  payment's sign varies, and its size is known in advance.

What would refute the mechanism as a source of profit: beta indistinguishable from 1 where |F| is large, or a
"profit" that the placebo windows earn too.

## 3. Declared prior

I have not measured beta anywhere. I expect it to be well above 0 for the largest contracts and lower for small
ones, and I give a tradable edge after 10 bp a fill about one chance in five. The rule's parameters were fixed from
the cost arithmetic, not from data: the threshold grid starts at 0.05%, where two 10 bp fills need beta below 0.6.

## 4. The probe (file names, and the funding rates only)

The probe (run 1 of `exf1.yml`, id 43753985512, 2026-11-15 19:56 UTC; `research/results/EXF-1-probe.json`) listed
923 USDT-M perpetuals with funding files (922 with 5-minute klines and 918 with their index's, from 2020-01) and 49
COIN-M perpetuals (all 49 with their index's). It read 14,961 USDT-M funding files of 2020-12 to 2025-12, none
failed, and counted the settlements whose previous rate reaches each threshold:

| Year | Settlements | at least 0.05% | 0.1% | 0.2% | 0.5% |
|---|---|---|---|---|---|
| 2021 | 124,223 | 30,464 | 14,241 | 5,014 | 395 |
| 2022 | 156,451 | 6,789 | 2,564 | 1,066 | 391 |
| 2023 | 226,476 | 7,561 | 2,602 | 1,384 | 574 |
| 2024 | 438,760 | 21,107 | 4,103 | 1,243 | 440 |
| 2025 | 881,479 | 45,095 | 20,131 | 9,187 | 3,184 |

Before the volume floor and any missing bar, dev holds **44,814, 19,407, 7,464 and 1,360** candidate trades at the
four thresholds (2021 carries most of them), and will fetch the bars of 3,236 contract-months on 263 contracts, all
with both files. Validation would fetch 4,708 contract-months on 611 contracts. No bar, price or premium was read:
the funding rates are the payments that define the events, and they say nothing of how the price moves across a
settlement. The 2026 rates (the holdout) and every COIN-M rate (the replication) were not read.

## 5. Definitions (frozen in the code)

- **Contracts.** USDT-M: every perpetual with funding files whose name ends in USDT, except dollar bases. COIN-M:
  every `*_PERP` contract, against its pair's index.
- **Settlement.** Each row of the monthly funding files: its time (to the minute) and its rate F_T. Its prediction
  F_hat is the previous settlement's rate on the same contract, if that is at most 9 hours earlier; otherwise the
  settlement has no prediction and is counted, not traded.
- **Bars.** 5-minute klines of the contract and of its index. The price at time x is the close of the bar that
  ends at x. A settlement with any bar missing is incomplete: counted, never filled.
- **Measured** on every complete settlement: the premium move across T (T-5m to T+5m), split into before and after
  T, against F_T, by size of |F_T|: the pass-through ratio E[sign(F) dprem] / E[|F|]. Reported, not gated.
- **The rule.** At T-5m, if |F_hat| >= theta and the 5-minute bar before entry traded at least 100,000 in quote
  currency, take side s = -sign(F_hat) at the close of the bar ending at T-5m; at T pay or receive the ACTUAL F_T;
  exit at the close of the bar ending at T+5m. Net = s r_perp - s F_T - 2 x 10 bp (5 bp taker fee, 5 bp spread and
  slippage).
- **Statistic.** The mean over ISO weeks of each week's mean net; its t with a Newey-West error (lag 2).
- **Placebos.** The same trade, the same side and costs, without any payment, at a quarter, a half and three
  quarters of the interval before T.

## 6. Stages

| Stage | Trial | Settlements | Contracts | Thresholds | Minimum | Runs only after |
|---|---|---|---|---|---|---|
| dev | EXF-1 | 2021-01-01 to 2023-12-31 | USDT-M | 0.05%, 0.1%, 0.2%, 0.5% (4 tests) | 300 trades, 52 weeks | registration |
| validation | EXF-1-V | 2024-01-01 to 2025-12-31 | USDT-M | the one dev chose | 300 trades, 52 weeks | EXF-1 PASSED |
| holdout | EXF-1-H | 2026-01-01 to 2026-10-31 (sealed) | USDT-M | the same | 100 trades, 20 weeks | EXF-1-V PASSED |
| replication | EXF-1-R | 2021-01-01 to 2025-12-31 | COIN-M (other contracts, other holders) | the same | 100 trades, 26 weeks | EXF-1-H PASSED |
| forward | EXF-1-F | 2026-11-23 to 2027-03-28 (did not exist when registered) | USDT-M | the same | 100 trades, 10 weeks | EXF-1-R PASSED, on or after 2027-04-10 |

Dev chooses the threshold: among those that pass every gate, the one with the highest t. Each later stage is
registered only after the one before it passed, with this same code, and reads only its own months. Every window
can reach its own minimum (a test asserts it; NEWL-1-F could not have).

## 7. Gates (every one required)

1. t >= 3.0.
2. Costs doubled (20 bp a fill): the mean stays above zero.
3. Both halves of the weeks above zero.
4. The five best trades removed: above zero.
5. Entering one bar earlier (T-10m): above zero.
6. Above the 95th percentile of 1,000 placebo draws (one placebo window per trade, no payment).
7. The best year removed: above zero.
8. The best contract removed: above zero.

Too few trades or weeks is INCONCLUSIVE, never a pass.

## 8. Power

The trade's noise is the contract's price over ten minutes. For contracts with this much funding I assume a
ten-minute standard deviation of about 0.7% (an assumption: no bar has been read). At 0.2% (7,464 candidates in 156
weeks, most of them in 2021) the error of a week's mean is then about 0.1% and that of the statistic about 0.01%:
t 3.0 needs about 3 bp a trade net. At 0.5% (1,360 candidates) it needs about 8 bp. If the pass-through were 0.5
where |F| is near 0.5%, the unpriced part (about 25 bp) less 20 bp of fills leaves about 5 bp, at the edge of what
can be seen; at a pass-through of 0.9 or more no threshold can pass. The stage tells these apart, and the measured
pass-through is reported whatever the rule's verdict.

## 9. What follows

- dev FAILED or INCONCLUSIVE: recorded; no later stage is registered; the measured pass-through is reported as what
  it is, a description, and no variant is judged on 2021-2023.
- dev PASSED: EXF-1-V is registered with this code and judged once on 2024-2025; then the holdout, the COIN-M
  replication and the forward stage, each only after the one before it passed. Only a rule that passes all five is
  proposed to the owner, for a paper desk through the risk engine, never real money.

## 10. Limits, declared

- Costs are assumed, not measured: 10 bp a fill, taker. The spread in the minutes around a settlement of a
  squeezed contract can be wider; the doubled-cost gate is there for that, and the volume floor keeps out the
  thinnest bars. Market impact beyond that is not modelled: the capacity of the rule is reported (the volume of the
  bar before entry), not assumed.
- The previous rate predicts the next one's sign and size; Binance's live estimate would predict better. The rule
  uses the weaker, fully known one.
- Five-minute bars: the jump is measured over ten minutes, which adds ten minutes of the premium's own movement
  around it.
- The archive may not keep every contract that was removed. That changes which contracts are present, not what
  happens across their settlements.
- The funding cap and the shortening of a contract's interval (to 4 or 1 hours) are part of the data, not modelled.
