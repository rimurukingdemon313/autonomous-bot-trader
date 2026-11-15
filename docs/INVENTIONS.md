# The invention ledger

**RESEARCH ONLY.** A trading mechanism proposed from first principles is written into `research/inventions.jsonl`
before any of its data is read, with its whole argument: the economic mechanism, why it should exist, who creates
it, why competition has not removed it, when it should appear and when disappear, its holding period and risk, how
the mechanism relates to expected return, predictions that can be measured, what would refute it, and the closest
known approaches with how it differs from each (`aitrader/research/inventions.py`, inventions-1.0.0).

The ledger refuses an entry without that argument, and refuses a mechanism from a family that has already failed
in this registry (funding carry, momentum across or within coins, calendar and flow effects, the new-listing drift,
the rebound after forced deleveraging) unless it says what is different this time. It is append-only: a later line
records a new status, a failed or rejected invention is never proposed again under its name, and a new idea takes a
new name. Mechanisms considered and rejected before any test are recorded with their reason, so that they are not
rediscovered as ideas.

It approves nothing. A registered invention is judged by its own preregistered test (`research/registry.jsonl`),
with the same bar, stages and seals as every other hypothesis.

## The ledger

| Invention | Status | Families | Trial or reason |
|---|---|---|---|
| EXF-1 ex-funding pass-through | REGISTERED | settlement microstructure, funding carry | EXF-1 |
| Liquidation-price magnets | REJECTED_BEFORE_TEST |  | No public data locates leveraged positions or their liquidation prices, and the idea is sold by data vendors as liquidation heatmaps: it can be neither tested without paid data nor called new. |
| Spot-listing demand of derivative-restricted holders | REJECTED_BEFORE_TEST |  | Its events are the new listings NEWL-1 read and spent (2021-01 to 2026-10): a test there would reuse exposed data. |
| Coin-margined hedgers' pressure on inverse perpetuals | REJECTED_BEFORE_TEST |  | A funding spread between two contracts on one index, arbitraged by the largest market makers: the carry family, which failed here five times, and small. |
| Quarterly delivery roll pressure | REJECTED_BEFORE_TEST |  | About 48 Binance expiries (BTC and ETH, 2020-2026): at the size the commodity roll literature reports, it cannot reach t 3.0. |
| Weekend gaps of CME-hedged holders | REJECTED_BEFORE_TEST |  | Folklore tested widely; the absence of hedgers predicts larger gaps, not their sign: no prediction to test. |
| The dead-zone transfer of 0.01% per eight hours | REJECTED_BEFORE_TEST |  | A known cash-and-carry yield (basis trades, synthetic dollar products): the carry family. |
