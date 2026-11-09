# The discovery program: is there a real, exploitable edge, and where?

**Started 2026-11-09. RESEARCH AND PAPER ONLY.** The owner set the mission: discover, test and validate a genuinely
profitable strategy, in any market, by any scientific method. They asked for five deliverables, then for work to start
on the highest-priority experiments:

- A. an audit of everything already known;
- B. the unexplored opportunities, ranked;
- C. at least ten hypotheses from genuinely different mechanisms;
- D. a research architecture;
- E. an implementation plan.

Nothing below is a claim of profit. A hypothesis is a question, and it becomes evidence only through the registry's
rules. The rules are not changed after a result is seen.

## A. The audit

### The record

| | |
|---|---|
| Hypotheses registered (`research/registry.jsonl`) | 80 trials: 70 verdicts (58 FAILED, 9 PASSED a stage, 2 ABANDONED, 1 INCONCLUSIVE) and 10 without a verdict. The 10 are 6 records from the earlier project, 3 forward tests and 1 design trial |
| Every judged hypothesis, classified (`docs/TRADING_EDGE_REGISTRY.md`) | 142: **140 REJECTED, 1 PROMISING, 1 VALIDATED** |
| Ideas dropped before any test, on power or on prior evidence (`research/QUEUE.md`) | 39, in 17 dated checks |
| Evidence files that still match the hash recorded with their verdict | 51 of 51 (`docs/RESEARCH_REPORT.md`) |
| The one VALIDATED rule | TRND-1. It holds a stock index only above its 10-month average, long or flat, swap-free. It earned t 3.83 against a bar of 3.376 on 1929-1989. In its sealed holdout, four index CFDs over 2021-01..2026-09, it earned +0.785% a month (t 2.74), with a worst fall of 11% against holding's 22%. Since 2026-11-09 it trades on paper by itself (`docs/TREND_DESK.md`) |
| The one PROMISING | RC-EQ's turn of the month: t 2.24 against 3.0. It is being tested forward (TOM-F) |

Tests counted per market, and the bar the next test on each must clear (Bonferroni over every earlier test on the
same data; this program also keeps a floor of 3.0):

| Market data | Tests | Next bar |
|---|---|---|
| FX majors (2017 on is sealed) | 176 | 3.631 |
| Index CFDs, intraday | 32 | 3.172 |
| Multi-asset ETFs / long histories | 12 / 10 | 2.890 / 2.838 |
| Crypto (Binance USDT-M / spot / cross-venue) | 10 / 7 / 8 | 2.838 / 2.734 / 2.773 |
| US equity ETFs | 6 | 2.690 |
| Equity indices, monthly / daily | 3 / 1 | 2.498 / 2.241 |
| US Treasuries, VIX products, metals, EM FX | 2, 2, 1, 1 | 2.394, 2.394, 2.241, 2.241 |
| Energy futures curves, liquidations, attention, stablecoins and other new data | 0 | 1.960, so the 3.0 floor applies |

### The data, and where it can be read

- **Here**, in the development container, only GitHub is reachable. Checked 2026-11-09: Binance, EIA, FRED,
  CoinGecko, Wikimedia, Yahoo, Stooq and Deribit all refuse the connection.
- **On GitHub's runner**, all of these are reachable. Every new dataset is fetched there by a run workflow, with its
  sha256 recorded, as XTS-1, FOMC-1A and TRND-1 were.
- **Already held:**
  - FX M5/M15 bid/ask, 2007-2016 (2017 on sealed);
  - the Federal Reserve's H.10 rates, 1971-2026;
  - BIS policy rates, 1988 on;
  - CFTC positioning;
  - index CFD intraday bars;
  - index, ETF and metals daily bars;
  - Binance spot, perpetual and funding data;
  - Hyperliquid funding.
- **Gone:** EIA stopped publishing NYMEX futures prices after 2024-04-05. Its history from 1983 is what remains.

### What failed, and why: by mechanism, not by name

| What was tried | Programs | Why it failed |
|---|---|---|
| Price patterns: SMC, ICT, liquidity sweeps, order blocks, quarters, candles, classic indicator rules, intraday and daily | ID-1, QT-1/2, SL-001/2, DP-001/2, the archive's SMC, DAY-1, R2/R4 | No directional information. Net −0.04 to −0.21 R a trade. The cost of a trade was the whole result |
| Real intraday effects smaller than the spread | FXS-1 (+0.76 bp gross at t 2.88, against 1.66 bp of cost); EX-1 (≤ 2.2 bp against 2.6-3.1 bp); IX-2 and FT-1 (index close momentum); MEH-1, FLOW-1 | **The effects exist. A retail spread is larger** |
| Machine learning on the same information | ID-2, WF-001-003 | The one real finding: ID-2's picks beat random entries by Welch t 3-7. But that is +0.10 to +0.19 R gross against 0.10-0.13 R of cost, and most of it was cost avoidance |
| Published anomalies after publication | FOMC-1A, PHD-1, SEC-1, LVOL-1, VOLM-1, RBL-1, TSY-1, TME-1, VRP-1, XSM-1, XTS-1, EMC-1 | Faded, or smaller than costs. TME-1 had t 4.07 before costs and 2.24 after; TSY-1 about t 2 before and below zero after |
| Carry | RV-1, R2A, R3 (FX), EMC-1 (EM FX), CR-1/4/5 (crypto funding) | FX carry stopped paying in 2008. Crypto funding carry passed its development three times and then failed validation or the holdout each time. A swap-free account earns no carry anyway |
| Positioning and crowding | COT-1, FND-1A | No information |
| Diversified trend at futures costs | DIV-2 | 1990-2007: +19.9% a year, Sharpe 1.02 (t 4.34). 2008-2020: Sharpe 0.11. Holdout 2021-2026: +2.3% a year, Sharpe 0.11, worst fall 44%. **The trend premium of the 1990s has not been there since 2008** |
| An AI desk deciding trades | DESK-1 | −0.357 R an agreement over 109 (t −3.2): +0.06 R before costs, 0.19 R in costs |

**The common cause.** Small effects do exist. Retail costs, the fading of published effects and too few independent
observations remove them. The only thing that survived is a slow premium taken calmly: the equity premium with smaller
crashes. That is not an edge over holding.

### Leads the record itself points to

1. **Horizons and markets where the spread is small next to the move.** Daily-to-monthly holds on index, energy and
   crypto CFDs, rather than intraday FX.
2. **Large forced flows rather than small scheduled ones.** The fixes and month-ends were real but smaller than the
   spread. A forced liquidation of leveraged positions moves prices by percent, not basis points.
3. **Premia that are not interest**, so they suit a swap-free (Islamic) account:
   - the equity premium (done: TRND-1);
   - the storage and hedging premium of commodity curves (never tested here);
   - the premium for providing liquidity after forced selling (never tested here);
   - the premium for carrying scheduled announcement risk (tested only on FOMC days).
4. **ID-2's information.** It would be positive net of costs only with a broker's real, smaller spreads, so it needs
   measured costs.
5. **FXT-1.** It passed every gate except t (2.71 against 3.63): currency trend existed in 1975-1989. It cannot be
   tested forward while the FX seal is open-ended.

### Closed families: do not re-run under another name

- Intraday price patterns on any market.
- Session and hour-of-day effects.
- Fixes and month-end flows.
- FX carry.
- Funding-rate carry and extremes.
- Positioning (COT).
- Calendar anomalies already listed in `research/QUEUE.md`.
- Crash filters on top of TRND-1 (too few independent crises to have power).
- Single-coin and cross-coin momentum.
- Volatility-managed exposure.
- Short volatility through exchange-traded products.

## B. Unexplored opportunities, ranked

Ranked by scientific justification (a mechanism with independent evidence) and feasibility. Feasibility means:
- data reachable on GitHub's runner;
- tradable on a swap-free CFD account, long or flat;
- power at the bar.

"Expected t" is the source's strength over the data available, against a bar of at least 3.0.

| Rank | Opportunity | Mechanism | Evidence | Data | Tradable | Expected t | Decision |
|---|---|---|---|---|---|---|---|
| 1 | **ENG-1**: energy futures term structure | Storage and hedging pressure | Strong theory; a term-structure factor Sharpe of about 0.41-0.49 | EIA contracts 1-4, 1983-2024 | WTI and natural gas CFDs, long or flat | 2.3-3.1 over the 32 judged years (1983-2014): passes about 25-55% of the time; 2015-2024 is the holdout | **BUILD first** |
| 2 | **LIQ-1**: buying after forced crypto deleveraging | Fire-sale liquidity provision | Strong for equities (Coval & Stafford 2007); none rigorous for crypto | Binance open interest from 2021-12 | BTC and ETH CFDs, long or flat | Unknown: a development stage measures it first | **BUILD second, in two stages** |
| 3 | **INV-1**: the inventory-announcement premium | Pay for carrying scheduled announcement risk | More than half of natural gas futures' annual return is earned on EIA report days (Prokopczuk, Wese Simen & Wichmann) | EIA report dates and the curves above | Natural gas CFD, one day a week | To be computed from the paper's figures. A natural gas CFD's spread may decide it | **Power check next** |
| 4 | **XAS-1**: bond returns as an equity signal | Slow-moving capital across asset classes | JFE 2020 (Pitkäjärvi, Suominen & Vaittinen): past bond returns predict equity returns positively | FRED yields and index data, already read | Index CFDs | Incremental over TRND-1: about 1.2 over 60 years | Dropped: no power for what it would add |
| 5 | **MAX-1**: crypto lottery demand | Overpaying for skewness | Conflicting: Grobys & Junttila 2021 find it negative, Özdamar et al. 2021 positive | Binance spot cross-section | Few coins at a CFD broker; long-only legs | Low: the direction is unknown and the large coins are few | Dropped until large-cap evidence agrees |
| 6 | **CMEG-1**: bitcoin's CME weekend gap | Anchoring and arbitrage to the CME settlement | Practitioner lore only | Binance hourly | BTC CFD | Needs about +0.9% an event over about 100 events | Dropped: no power, no study |
| 7 | **OFI-1**: order-flow imbalance | Order splitting keeps flow persistent | Strong for price impact, weak for prediction | Binance taker volume | BTC CFD, hourly | Gross about 2 bp a trade against 5-10 bp of cost | Dropped: the cost lesson of ID-2, IX-2 and FT-1 |
| 8 | **ATT-1**: retail attention | Attention-driven demand | Mixed (ElBahrawy 2019; Hoang & Vo 2024: continuation, partial reversal) | Wikimedia page views from 2015 | BTC CFD | Needs about 2.8% a week | Dropped: no power |
| 9 | **STB-1**: stablecoin issuance | Capital entering crypto | Against: no effect on subsequent returns (Economics Letters 2018); mints follow rallies | CoinGecko supply | BTC CFD | — | Dropped on prior evidence |
| 10 | **FCI-1**: financial-conditions filter | Deleveraging after tightening | Theory and macro evidence | Chicago Fed NFCI vintages | Index CFDs | 6-8 crises in any sample | Dropped: a crash filter, no power |
| 11 | **EVT-1**: drift after the storage report | Slow diffusion of information | Against: the reaction is immediate and does not revert, or partly reverses the next week | EIA | Natural gas CFD | — | Dropped on prior evidence |
| 12 | **FXC-1**: ID-2's ranking with measured costs | Cost avoidance as the edge | ID-2: real information about the size of a trade's cost | The broker's spread, recorded | FX CFDs | Unknown until the costs are measured | **Blocked**: needs a read-only spread recorder on the owner's demo account |
| 13 | **FXF-1**: Forex on data after the seal | Any FX mechanism, forward | — | FX after the seal | FX CFDs | — | **Blocked**: needs the owner's decision to close the 2017 seal at a date |

The ranking also answers the mission's question of where an edge is most likely. It is in **slow, non-interest premia
and large forced flows**: equity indices (done), energy curves, and crypto deleveraging. It is not in intraday Forex,
where 176 tests found the spread larger than every effect.

## C. The hypotheses

The bar for every one is at least 3.0. Every test has:

- a development, validation and holdout split;
- costs ×1, ×1.5 and ×2 at the broker's spreads;
- a one-bar delay;
- a matched random baseline and a block bootstrap;
- no year above a quarter of the gains.

Each result reports:

- a 95% confidence interval;
- the sample size;
- the drawdown;
- exposure, turnover and trade frequency;
- every cost by kind.

### H1. ENG-1: the energy futures term-structure premium

- **Mechanism.** The theory of storage (Kaldor, Working, Brennan): when inventories are scarce, the curve is
  backwardated and the near contract earns a convenience yield. Hedging pressure (Keynes; de Roon, Nijman & Veld):
  producers hedge short and pay longs a premium. Both predict positive expected returns to holding a backwardated
  contract.
- **Why it might exist.** Hedgers pay for insurance, and arbitrage is limited by storage costs and capital. The
  term-structure factor has a Sharpe ratio of about 0.41-0.49 across commodities (sources below), and energy has
  been reported to give the strongest roll-conditional results.
- **Data.**
  - EIA daily prices of NYMEX contracts 1 to 4: WTI (1983 on), NY Harbor heating oil, gasoline (unleaded to 2006,
    then RBOB), Henry Hub natural gas (1994 on). They end 2024-04-05.
  - Contract expiry rules, so the rolls are stitched without a jump.
- **Formulation.**
  - At each month-end t, for each contract c: b_c(t) = ln(F1_c(t) / F2_c(t)) × 12 / (months between the two
    expiries).
  - Position: w_c = 1 if b_c(t) > 0, otherwise 0. Inverse-volatility weights (63-day realized volatility, known at t),
    scaled to a fixed portfolio volatility.
  - The return held from t to t+1 is that of the contract a CFD would hold, rolled at the same day each month,
    before expiry.
  - Costs: the CFD spread on every entry, exit and roll, ×1, ×1.5 and ×2. No financing.
- **Falsifiable test.**
  - The book's mean monthly net return > 0, with HAC t ≥ 3.0, over the judged period.
  - It must beat always-long at equal risk (paired t > 0), so that the signal adds value beyond holding energy.
  - Development (1983-1998) and validation (1999-2014) must each be positive. The holdout (2015-01..2024-03,
    including the 2020 negative front-month WTI price, which holding contract 2 avoids) is registered and opened
    only after a pass.
  - It must survive costs ×2 and a one-month delay.
  - A random baseline: the same number of backwardation months with shuffled signs, 10,000 times; the book must be
    above the 95th percentile.
  - No single year may give more than 25% of the gains.
- **Power.** At the sourced Sharpe ratio of 0.41-0.55 over the 32 judged years, expected t is 2.3-3.1 against 3.0:
  it passes about 25-55% of the time. TRND-1 was built at about two in three, DAY-1 at one in three.
- **Failure risks.**
  - The premium is small next to energy's volatility.
  - 2005-2014 was dominated by contango.
  - Roll mechanics: a CFD broker's roll may not pass the whole roll yield. This is checked against the broker's
    contract specification before any paper desk.
  - Only WTI and natural gas are commonly quoted as CFDs.

### H2. LIQ-1: buying after forced crypto deleveraging

- **Mechanism.** Liquidations close leveraged positions whatever the price, so they are fire sales. Forced, price-
  insensitive selling pushes prices below value, and those who provide liquidity are paid when it reverses (Coval &
  Stafford 2007; Brunnermeier & Pedersen 2009). In crypto perpetuals the forced selling is visible as a collapse in
  open interest during a fall.
- **Why it might exist.** Exchange margin engines liquidate mechanically. Leverage on perpetuals is high. The
  liquidity providers are thin in a cascade, and capital is slow to arrive.
- **Data.**
  - Binance USDT-M open interest every 5 minutes from data.binance.vision (from about 2021-12).
  - Hourly klines and funding.
  - All on GitHub's runner.
- **Formulation.**
  - Hourly, for BTC and ETH. An event is when both hold at the same hour:
    - Δln(OI) over the hour is below its trailing 90-day 1st percentile;
    - the hour's return is below its own trailing 1st percentile.
  - The response: long at the next hour's open, held 24 hours, one position per coin.
  - All thresholds are fixed before development.
- **Falsifiable test.** In two stages, like CR-1.
  - **Stage 1 (select)**, on development data 2021-12..2023-12. It measures the net 24-hour event return and fixes the
    rule. This counts as a test on those years.
  - **Stage 2 (judge)** is preregistered after stage 1 with the rule frozen, on 2024-01..2026-10.
  - The mean net event return must exceed 0 with a week-clustered t ≥ 3.0.
  - It must beat matched random entries: the same hours of the day and months, the same hold.
  - It must survive costs ×2, because spreads widen in cascades, and a one-hour delay.
  - Both coins must be positive.
- **Failure risks.**
  - Cascades often continue: a momentum crash.
  - The same leverage family as FND-1A.
  - Only about 4.8 years of open-interest data.
  - A CFD's spread in a cascade.
  - Weekends.

### H3. INV-1: the inventory-announcement premium

- **Mechanism.** Investors are paid for carrying risk across a scheduled release (Savor & Wilson 2013, for macro
  announcements). For natural gas, more than half the annual return of the futures is earned on the days of the
  EIA's weekly storage report.
- **Why it might exist.** The release resolves non-diversifiable uncertainty about supply, and holders of that risk
  demand a premium.
- **Data.** EIA report dates (Thursdays from 2002, earlier from the American Gas Association) and the natural gas
  curve above.
- **Formulation.** Long natural gas from the close before each report to the close of the report day, flat otherwise.
  Compared with holding on the other days.
- **Falsifiable test.**
  - The mean report-day net return > 0 with t ≥ 3.0.
  - It must exceed the mean of non-report days (a paired comparison).
  - A random baseline of other weekdays.
  - Costs ×2: a natural gas CFD's spread is the likely deciding cost.
- **Failure risks.**
  - The premium may be the announcement-day volatility rather than a mean.
  - The report's impact has shrunk over time.
  - One day's hold pays the full spread every week.

### H4. XAS-1: bond returns as a signal for equity indices

- **Mechanism.** Slow-moving capital between asset classes: after bond rallies, money flows into equity funds over
  months (Pitkäjärvi, Suominen & Vaittinen, JFE 2020).
- **Why it might exist.** Mandates rebalance slowly, and fund flows chase both markets' past returns.
- **Data.** FRED 10-year yields (US from 1962, Germany and the UK from OECD series) and the index data.
- **Formulation.** Monthly signal s = sign(12-month bond return) + sign(12-month equity return). Long when s > 0,
  otherwise flat. Bonds are only a signal and are never held.
- **Falsifiable test.** The difference between XAS-1 and TRND-1 each month: its mean > 0 with t ≥ 3.0.
- **Failure risks.** Index data already read. Few independent markets. The incremental Sharpe ratio is about
  0.1-0.2, so about t 1.2 over 60 years. **Dropped: no power for what it would add.**

### H5. MAX-1: lottery demand in crypto

- **Mechanism.** Investors overpay for lottery-like payoffs (Bali, Cakici & Whitelaw 2011), so assets with extreme
  past daily gains earn less.
- **Data.** Binance spot daily, with the point-in-time large-coin universe XSM-1 used.
- **Formulation.** Weekly, rank by the past month's maximum daily return. Low-MAX coins against BTC.
- **Falsifiable test.** The low-minus-high spread > 0 with t ≥ 3.0, then the executable long-only version.
- **Failure risks.** The published signs disagree (negative, Grobys & Junttila 2021; positive, Özdamar et al. 2021).
  The large coins a CFD broker quotes are few. **Dropped until the evidence on large coins agrees.**

### H6. CMEG-1: bitcoin's CME weekend gap

- **Mechanism.** CME bitcoin futures are shut at weekends. If traders anchor to the Friday settlement, and basis
  arbitrage pulls the price back toward it, spot would revert toward the settlement after a weekend move.
- **Data.** Binance hourly bars, and the CME session calendar.
- **Formulation.** gap = ln(spot at Sunday 23:00 UTC / spot at Friday 21:00 UTC). After a negative gap beyond k%,
  long until the gap closes or H hours pass.
- **Falsifiable test.** The mean net event return > 0, t ≥ 3.0, against random weekly entries.
- **Failure risks.** No study, only lore. Long-only halves the events. **Dropped: needs about +0.9% an event over
  about 100.**

### H7. OFI-1: order-flow imbalance in bitcoin

- **Mechanism.** Large orders are split, so the sign of order flow is persistent and prices continue (Lillo & Farmer
  2004; Kyle 1985).
- **Data.** Binance hourly taker buy and sell volume.
- **Formulation.** OFI = (taker buys − taker sells) / volume. Long for the next hour when OFI is in its top decile.
- **Falsifiable test.** Gross information first. Then net of a CFD's 5-10 bp round trip, t ≥ 3.0.
- **Failure risks.** An hourly information coefficient of about 0.03 on 70 bp of hourly volatility gives about 2 bp a
  trade. **Dropped: the cost lesson of ID-2, IX-2 and FT-1.**

### H8. ATT-1: retail attention

- **Mechanism.** Attention brings retail buyers (Barber & Odean 2008). In crypto it has preceded higher returns, with
  only partial reversal (Hoang & Vo 2024).
- **Data.** Wikimedia daily page views from 2015-07, user traffic only.
- **Formulation.** Abnormal attention = ln(views) − the median of ln(views) over the previous eight weeks. Next-week
  BTC return after the top quintile of abnormal attention, against the others.
- **Falsifiable test.** The difference > 0 with t ≥ 3.0.
- **Failure risks.** Attention follows price. About 114 weeks in the top quintile, at about 9% weekly volatility,
  need a gap of about 2.8% a week. **Dropped: no power.**

### H9. STB-1: stablecoin issuance

- **Mechanism.** Fresh stablecoins are capital entering crypto, so they should buy.
- **Evidence.** Tether issuance did not predict later Bitcoin returns, only volume (Economics Letters 2018).
  Stablecoins do not inflate crypto markets (a CEPR/VoxEU column). Mints follow rallies (CrossTower).
- **Dropped on prior evidence.** No test is spent.

### H10. FCI-1: a financial-conditions filter

- **Mechanism.** Tight financial conditions lead to deleveraging and a fat left tail (Adrian, Boyarchenko & Giannone
  2019).
- **Formulation.** Hold an index only while the Chicago Fed NFCI, at its point-in-time vintage, is below its trailing
  80th percentile.
- **Failure risk.** It is a crash filter, and any sample holds six to eight crises. **Dropped: no power**, the same
  verdict as the crash filters in `research/QUEUE.md`.

### H11. EVT-1: drift after the storage report

- **Mechanism.** Slow diffusion of information (Hong & Stein 1999).
- **Evidence.** The literature finds the natural gas reaction immediate and not reverting (Halova et al. 2014,
  summarized by the EIA), or partly reversing the next week (Ederington et al.).
- **Dropped on prior evidence.** H3 keeps the same data for the premium, which is supported.

### H12. FXC-1: ID-2's information with measured costs

- **Mechanism.** In ID-2, much of the information was about when a trade is cheap. Net of a broker's real, smaller
  spread, that may be positive.
- **Data.** The owner's broker's quotes, recorded read-only for months.
- **Blocked.** It needs a spread recorder with the demo account's credentials, which the owner must add as secrets.
  They must never be pasted into a conversation.

### H13. FXF-1: Forex on data after the seal

- **Blocked.** Every month from 2017 on is sealed, open-ended, for one final test. A forward FX universe needs the owner
  to close the seal at a date: a change to the project's protection of its holdout, which only they can decide.

## D. The research architecture

The engine finds, tests, rejects and keeps hypotheses, with these stages:

```
            ┌───────────────── GENERATE ─────────────────┐
literature, │ the research loop (11:26, 23:26 UTC): web  │   research/QUEUE.md (human-readable)
the record, │ search, mechanisms, the record's own leads │──►
lessons ───►│ the engine (04:47 UTC): proposer model,    │   ideas.jsonl on research-data
            │ critic model (can only reject)             │   (append-only, fingerprinted)
            └──────────────────┬─────────────────────────┘
                               ▼
POWER GATE (arithmetic): expected t at the sourced strength against the market's bar → drop or queue
                               ▼
DATA: a dates-only probe on GitHub's runner (availability, gaps, rolls; no returns), then the data with sha256
                               ▼
PREREGISTER: frozen spec and code sha256 quoted in research/preregistrations/<ID>.md; the registry trial
                               ▼
TEST (scripts/<id>.py; run workflow): development → validation → sealed holdout, costs ×1/×1.5/×2, delay,
random baseline, block bootstrap, year concentration, regimes; tests on markets built so the answer is known
                               ▼
JUDGE once: research/knowledge/<ID>.json (its hash recorded with the verdict); classification by
aitrader/research/discovery/edges.py; REJECTED, PROMISING or VALIDATED
                               ▼
FORWARD and PAPER (VALIDATED only, and only on the owner's promotion): a forward test registered (like TRND-F);
a paper desk through the risk engine, the hard gate and the paper broker (like the trend desk)
                               ▼
LEARN: lessons into the ideas context; the closed families list; the research report
```

| Requirement | Where it is met |
|---|---|
| 1. Acquire and validate data | Run workflows on GitHub's runner. Manifests with sha256. Point-in-time rules in `aitrader/data/` (for example H.10 usable from 17:00 New York the next business day) |
| 2. Discover patterns | `aitrader/research/discovery/` screen (BH-FDR), lab walk-forward, study tools: on development data only, counted |
| 3. Generate hypotheses | The research loop and `scripts/research_engine.py` |
| 4. Turn a hypothesis into a precise rule | A frozen spec per program; the planned `scripts/harness.py` (section E) gives every program the same gates |
| 5. Many conditions and timeframes | Development, validation and holdout by era; by-year results; one result per instrument |
| 6. Costs | Spreads, commission, slippage, financing (zero swap-free) and execution delay, with ×1.5 and ×2 |
| 7. Baselines | Buy-and-hold; always-long at equal risk; matched random entries; TRND-1 for index overlays |
| 8. Walk-forward and untouched data | The registry's seal and holdout rules; forward tests |
| 9. Overfitting, look-ahead, survivorship, leakage | Signals use only data ≤ t (tests built so a leak shows); point-in-time universes; one-bar delay; Bonferroni over every test on the data; no parameter changed after a result |
| 10. Every experiment recorded | `research/registry.jsonl` (append-only, enforced); knowledge files with hashes checked daily; `ideas.jsonl`; `cycles.jsonl` |
| Scheduled cycles, checkpointing, recovery, budgets | `research-cycle.yml` (daily; checkpoints; a 20-call model budget; a visible failure on tampering or a stall); the scheduled research task twice a day; run workflows with retries |

## E. The implementation plan

| Step | Files | Tests | Status |
|---|---|---|---|
| 1. The ledger, the two reports and the engine | `scripts/desk_ledger.py`, `scripts/research_report.py`, `scripts/research_engine.py`, `scripts/research_cycle.py`, `.github/workflows/research-cycle.yml` | `test_desk_ledger.py`, `test_research_report.py`, `test_research_engine.py`, and their guards in `scripts/mutation_audit.py` | Built; pushed and deployed with the verification recorded in `docs/AUTONOMOUS_RESEARCH_SYSTEM.md` |
| 2. This program | `docs/DISCOVERY_PROGRAM.md` | — | Written |
| 3. ENG-1 probe: dates, gaps and roll calendars of the EIA contracts, no returns | `scripts/eng_probe.py`, `.github/workflows/eng-probe.yml`, `research/results/ENG-probe.json` | `tests/unit/test_eng_probe.py` | Started |
| 4. ENG-1: spec, preregistration, build, judge | `scripts/eng1.py`, `research/preregistrations/ENG-1.md`, `.github/workflows/eng1-run.yml` | `tests/unit/test_eng1.py`: built backwardated and contango curves with a known answer; a look-ahead trap; roll stitching | After the probe |
| 5. LIQ-1 probe: open interest's first date and gaps per coin | `scripts/liq_probe.py`, `.github/workflows/liq-probe.yml` | `tests/unit/test_liq_probe.py` | After ENG-1's preregistration |
| 6. LIQ-1 stage 1 (development), then stage 2 (preregistered judge) | `scripts/liq1.py`, `research/preregistrations/LIQ-1.md`, `.github/workflows/liq1-run.yml` | `tests/unit/test_liq1.py`: built cascades with a known reversal; random entries match | — |
| 7. INV-1 power check from the paper's figures | `research/QUEUE.md` | — | — |
| 8. A shared harness for the gates every program repeats | `scripts/harness.py` | `tests/unit/test_harness.py`, and each program's tests unchanged | Once ENG-1 and LIQ-1 share them |

Every step is one commit with its tests and the full suite run, and the mutation audit when a guard changes. Every
result is reported as it is, failures first.

## Sources

- Term structure in commodities (Quantpedia; EDHEC/City University working paper):
  [quantpedia.com/strategies/term-structure-effect-in-commodities](https://quantpedia.com/strategies/term-structure-effect-in-commodities),
  [openaccess.city.ac.uk/id/eprint/17296](https://openaccess.city.ac.uk/id/eprint/17296/7/IPE_EDHEC_Summer_2014_IVOl%20paper.pdf),
  [roll yields in energy futures](https://quantpedia.com/effect-of-maturity-structure-of-roll-yields-in-commodity-futures-strategies/)
- EIA's NYMEX futures prices, ending 2024-04-05: [eia.gov/dnav/pet/PET_PRI_FUT_S1_D.htm](https://www.eia.gov/dnav/pet/PET_PRI_FUT_S1_D.htm),
  [the discontinued dataset](https://preview.alphacast.io/datasets/discontinued-inflation-usa-eia-nymex-futures-prices-38629)
- Fire sales: [Coval & Stafford (NY Fed)](https://www.newyorkfed.org/medialibrary/media/research/conference/2005/liquidity/Coval_Stafford.pdf),
  [NBER w11357](https://www.nber.org/papers/w11357)
- Liquidation-cascade evidence is anecdotal: [K33/KuCoin summary](https://www.kucoin.com/news/flash/crypto-open-interest-drops-3b-triggering-308m-in-liquidations)
- Cross-asset signals: [Alpha Architect summary of Pitkäjärvi, Suominen & Vaittinen](https://alphaarchitect.com/cross-asset-signals-and-time-series-momentum/),
  [VU research record](https://research.vu.nl/en/publications/cross-asset-signals-and-time-series-momentum/)
- Crypto MAX effect: [Özdamar et al. 2021](https://link.springer.com/10.1186/s40854-021-00291-9),
  [lottery-like preferences in crypto](https://repository.bilkent.edu.tr/items/78167f5c-d3e2-4f07-b4bc-5e8a3ed0b2c0)
- Attention: [ElBahrawy et al. 2019](https://www.frontiersin.org/articles/10.3389/fbloc.2019.00012),
  [Hoang & Vo 2024](https://ideas.repec.org/a/eee/beexfi/v44y2024ics2214635024001060.html)
- Stablecoins: [Economics Letters 2018](https://ideas.repec.org/a/eee/ecolet/v171y2018icp19-22.html),
  [CEPR/VoxEU](https://cepr.org/voxeu/columns/stable-coins-dont-inflate-crypto-markets),
  [CrossTower via Blockworks](https://www.blockworks.com/news/crosstower-research-tether-mints-follow-strong-price-action)
- Natural gas storage announcements: [EIA presentation (Linn)](https://www.eia.gov/finance/markets/reports_presentations/2017/linn.pdf),
  [Ederington et al.](https://www.iaee.org/ej/ejexec/EJ40-5_Ederington_ExecSum.pdf),
  [Prokopczuk, Wese Simen & Wichmann](https://iaee.org/ej/ejexec/ej42-2-Wichmann-exsum.pdf)
