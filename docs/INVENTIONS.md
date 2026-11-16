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
| EXF-1 ex-funding pass-through | FAILED | settlement microstructure, funding carry | EXF-1 |
| Liquidation-price magnets | REJECTED_BEFORE_TEST |  | No public data locates leveraged positions or their liquidation prices, and the idea is sold by data vendors as liquidation heatmaps: it can be neither tested without paid data nor called new. |
| Spot-listing demand of derivative-restricted holders | REJECTED_BEFORE_TEST |  | Its events are the new listings NEWL-1 read and spent (2021-01 to 2026-10): a test there would reuse exposed data. |
| Coin-margined hedgers' pressure on inverse perpetuals | REJECTED_BEFORE_TEST |  | A funding spread between two contracts on one index, arbitraged by the largest market makers: the carry family, which failed here five times, and small. |
| Quarterly delivery roll pressure | REJECTED_BEFORE_TEST |  | About 48 Binance expiries (BTC and ETH, 2020-2026): at the size the commodity roll literature reports, it cannot reach t 3.0. |
| Weekend gaps of CME-hedged holders | REJECTED_BEFORE_TEST |  | Folklore tested widely; the absence of hedgers predicts larger gaps, not their sign: no prediction to test. |
| The dead-zone transfer of 0.01% per eight hours | REJECTED_BEFORE_TEST |  | A known cash-and-carry yield (basis trades, synthetic dollar products): the carry family. |
| SQZ-1 crowded shorts and the spot buyer | FAILED | crowded positioning, funding carry | SQZ-1 |
| Strike pinning by 0DTE index options | REJECTED_BEFORE_TEST |  | An independent 2026 study (Elms, SSRN; seen as a search result) tested 2,294 S&P 500 days of 2016-2025 and found no pinning, and the hourly index data here would need the cash level the CFD does not quote. |
| TRND-1's rule on metals, oil and crypto funds | REJECTED_BEFORE_TEST |  | DIV-1 already judged trend rules on the same funds over 2008-2021 and failed; the test would reuse exposed data. |
| Swap-free shorting of high-yield currencies | REJECTED_BEFORE_TEST |  | It would profit from the interest differential through the broker's swap-free terms, which brokers forbid as swap abuse and which goes against the purpose of an Islamic account; FX majors are sealed besides. |
| CASC-1 liquidation-led falls and the spot buyer | FAILED | forced-deleveraging rebound | CASC-1 |
| BAS-1 high funding and the spot buyer | FAILED | crowded positioning, funding carry | BAS-1 |
| TRND-1's rule on bitcoin and ether CFDs | REJECTED_BEFORE_TEST |  | Time-series momentum already failed on these two coins (XTS-1, 2018-01 to 2024-06). The only unread window, 2024-07 to 2026-10, holds 28 monthly decisions on two assets whose path the designer knows from training data, so it is not unseen; and at bitcoin's volatility of about 20% a month, t 3.0 over 28 months needs a mean above 11% a month. The rule is Faber's (2007), not an invention; its honest form is a forward paper track, years long. |
| CALM-1 the long-only basket without leverage-stressed coins | REJECTED_BEFORE_TEST |  | Power. Planned from BAS-1's development records (exposed, used only to plan): in the weeks they occur, stressed coins are about 15% of the seasoned universe and trail it by about 1.04% a week, so leaving them out lifts the equal-weight basket by about 0.18% a week (0.15/0.85 x 1.04%) with a weekly spread of about 0.71% (0.176 x the 4.04% cohort SD), before its extra turnover. Over the about 35 active weeks of the fresh window 2025-03 to 2026-10 that expects t about 1.5 against 3.0; t 3.0 needs about 140 active weeks. |
| US-hours clientele in bitcoin | REJECTED_BEFORE_TEST |  | A session and hour-of-day effect, a family this record has closed (docs/DISCOVERY_PROGRAM.md); and at bitcoin's volatility it would need about 19 bp a day for t 3.0 over nine years. |
| Post-FOMC drift into gold | REJECTED_BEFORE_TEST |  | Power. About 143 scheduled FOMC meetings since 2009; gold's 10-day volatility is about 3.2%, so t 3.0 needs a signed drift of about 0.8% a meeting. An assumed post-announcement drift in real yields of 3-5 bp, at gold's sensitivity of about 10% per 100 bp, gives 0.3-0.5% (t about 1.1-1.9). Gold's intraday data is sealed, so the first reaction could only be read from daily closes. |
| Bitcoin's weekend move and Monday's index session | REJECTED_BEFORE_TEST |  | Power. About 350 Mondays since 2020; from the Sunday open to Monday's close an index CFD moves about 1%, so the index-intraday bar of 3.17 needs a continuation of about 0.17% a Monday in bitcoin's direction after the open has priced its share: a continuation beta of about 0.04 on bitcoin's typical 4% weekend move. No source suggests the Sunday open under-reacts by that much. |
| Passive capture of the unpriced funding fraction | REJECTED_BEFORE_TEST |  | It holds perpetuals across a funding payment: outside the Islamic condition (funding paid or received). It would also need the archive's best bid and ask and a maker's fill model, which EXF-1 did not have. |
| Buying after a token unlock | REJECTED_BEFORE_TEST |  | Contradicted before testing. Keyrock's study of more than 16,000 unlocks reports about 90% followed by price pressure, beginning about 30 days before the unlock; a Tokenomist study of 236 unlocks reports a median of -16.3% against bitcoin a month after the unlock (both seen only as search results and summaries, not read in full). Nothing points to a recovery a spot buyer could own: the information is on the short side, which the Islamic condition excludes for altcoins. The unlock schedules are a paid dataset besides (DefiLlama Pro, Tokenomist). |
| INV-1 the natural gas storage-report premium | REJECTED_BEFORE_TEST |  | Power and costs. Its unread years are 2019 on: ENG-1 read the EIA curves to 2018, and DLAB-ENG-1's 400 tests cover 1994-2011, where the bar is near 3.9. Natural gas moves about 3.5% a day, so t 3.0 over about 400 report days (2019-01 to 2026-10, and only if a front-month series can be had after the EIA stopped publishing it in 2024-04) needs about 0.53% a report day: 27% a year from report days alone. The paper's abstract (Prokopczuk, Wese Simen & Wichmann 2021, seen as a search result; its full text could not be fetched here) says more than half of the annual return is earned on report days. If a front-month position earns about 10% a year, half of it over 52 report days is about 0.1% a day, which gives t about 0.6; and a natural gas CFD's round trip, about 0.1-0.3% at retail spreads on a $3 contract, would take all of it. |
| HLQ-1 visible liquidation clusters on Hyperliquid | PROPOSED | predatory trading, visible leverage |  |
