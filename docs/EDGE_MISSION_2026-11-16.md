# Edge mission, 2026-11-16: the audit, sixteen new hypotheses, and what the evidence allows

**RESEARCH ONLY · NOTHING HERE IS A PROFIT CLAIM.** The owner's mission of 2026-11-16 asked for four things:

- an honest audit of what has been tested;
- at least ten original hypotheses from first principles, each ranked;
- the cheapest decisive experiments on the strongest of them;
- every candidate classed REJECTED, INCONCLUSIVE, PROMISING or VALIDATED, with exact numbers and reproducible steps.

**بالعربي:** راجعت كل اللي انفحص (94 تجربة مسجّلة، فشلت منها 77)، وطلّعت 16 فرضية جديدة من أساس اقتصادي.

- **ولا وحدة جديدة عبرت الفحوص الأولية،** فما شغّلت عليها اختبار نتائج. الأسباب:
  - العدد ما يكفي لنتيجة إحصائية؛
  - أو العائلة مسكّرة بالسجل لأنها فشلت قبل؛
  - أو أكو دليل منشور ضدها؛
  - أو الشرط الإسلامي يمنع الجهة اللي بيها المعلومة.
- **الشي الوحيد المثبت بعده TRND-1.**
- **الدليل يكول:** المعلومة موجودة بالسوق بس الكلفة تاكلها. فالطريق للربح هو كلفة أقل (حسابات swap-free) ورأس مال أكبر (الحسابات الممولة). وهذا اللي ربطه اليوم صار جاهز.

## 1. The audit: what the committed record says

### The registry (`research/registry.jsonl`, read with its own reader)

94 trials: **77 FAILED, 9 PASSED, 1 INCONCLUSIVE, 3 ABANDONED, 4 PENDING.** By the universe they used:

| Universe | Trials | Outcome |
|---|---|---|
| fx-majors | 38 | 35 failed, 1 passed (RV-1 stage 1), 1 inconclusive, 1 abandoned |
| index-cfd-intraday | 7 | 6 failed, 1 abandoned |
| multi-asset-etf / multi-asset-long | 9 | 5 failed, 2 passed (DIV-2, DIV-2-H), 2 pending (TOM-D, a descriptive) |
| us-equity-etf | 5 | 5 failed |
| crypto (Binance spot, USDT-M, cross-venue) | 22 | 15 failed, 3 passed (CR-1, CR-4, CR-5), 1 abandoned, 1 pending (RADAR-1), 2 others failed |
| equity-index-monthly / -b / -daily / -forward | 7 | 3 passed (TRND-1, TRND-1-H, RC-EQ2-H), 1 failed, 3 pending (TRND-F, TOM-F, TOM-D) |
| US Treasuries, energy, metals, volatility, EM FX | 8 | 8 failed |

What the nine passes are, and why only one became a tradable rule:

| Trial | What it is | Why it is not a second edge for the owner |
|---|---|---|
| TRND-1, TRND-1-H | The 10-month trend filter on index CFDs: 1929-1989 development (t 3.83, bar 3.376), 2021-2026 holdout (69 months, net t 2.737) | It **is** the edge: VALIDATED. It earns about the market's return, with about half of the market's worst fall |
| DIV-2, DIV-2-H | Time-series momentum over about 20 futures (bonds, currencies, equities, commodities), about 4x gross exposure | Bonds are interest-bearing and FX majors are sealed (the Islamic condition and research/holdout.json) |
| CR-1, CR-4, CR-5 | Funding-rate carry on Binance and Hyperliquid perpetuals | Funding paid or received is excluded (the Islamic condition). Its live forward test, RADAR-1, stands at -2.09% (perf-data, 2026-11-16) |
| RC-EQ2-H | The turn-of-the-month replication on 16 never-loaded indices | Replicated, but at net t 2.175, below the bar: PROMISING. TOM-F judges it forward |
| RV-1 (stage 1) | Cross-sectional currency information | FX is sealed from 2017 |

### The edge registry (`research/knowledge/edge_registry.json`, edges-1.12.0)

158 judged edges:

- **1 VALIDATED:** TRND-1.
- **4 PROMISING:** each a near miss on t alone.
  - DAY-1: t 2.48 against a bar of 3.39.
  - FXT-1: t 2.71 against 3.63.
  - RCEQ-E1-TOM: replicated at t 2.18.
  - TME-1: t 2.24 against 3.08.
- **4 UNCERTAIN:** too few events (BAS-1, CASC-1 and SQZ-1 thresholds).
- **149 REJECTED.**

### The discovery lab (lab-data, 2026-11-16 12:02 UTC)

**660 rules classed, 0 promising.** The lab's information audit is the most useful number in the record.

- On the crypto-perpetual panel, 44 of 982 feature-instrument pairs carry information about the next return at z ≥
  2, where chance gives about 22.6.
- Dozens of rules on every panel were positive before costs and negative after.

**The markets carry some information; the costs take it.**

### The invention ledger (before today)

- 49 lines.
- 33 ideas rejected before any data was read.
- 5 registered and judged: all five FAILED (EXF-1, SQZ-1, CASC-1, BAS-1, SPL-1).
- Their joint finding: in seasoned altcoins, large moves and leverage stress of either sign are followed by
  underperformance (SPL-1: -1.45% net a day after 8% four-hour rallies, t -5.21, 6,378 trades). **The information is
  on the short side,** which the owner's stated instruments exclude for altcoins.

### Families the record has closed (`docs/DISCOVERY_PROGRAM.md`)

These are not re-run under another name:

- intraday price patterns on any market;
- session and hour-of-day effects;
- fixes and month-end flows;
- FX carry;
- funding-rate carry and extremes;
- positioning (COT);
- the calendar anomalies in `research/QUEUE.md`;
- crash filters on top of TRND-1;
- single-coin and cross-coin momentum;
- volatility-managed exposure;
- short volatility through ETPs.

## 2. Sixteen hypotheses from first principles

Each one is answered to the mission's seven questions:

- **Mechanism:** what creates the opportunity.
- **Persists because:** why competition has not removed it.
- **Other side:** who is on the other side of the trade.
- **Data:** what observable reveals it.
- **Prediction:** the exact prediction.
- **Refuted if:** the evidence that would disprove it.
- **Differs from known work:** how it is meaningfully different.

None was in the record before today. Each is now a line in `research/inventions.jsonl`.

**H1 · PDL-1: forced closure at a perpetual's delisting**

- **Mechanism:** when an exchange delists a perpetual, every open position must be closed by a set time. Carry traders
  (long spot, short perpetual) sell their spot, and shorts hedged with borrowed spot buy theirs back.
- **Persists because:** the closure is mandatory, and the coins are thin.
- **Other side:** spot liquidity providers.
- **Data:** perpetuals' last kline files on Binance's archive, funding, spot klines.
- **Prediction:** the spot moves against the sign of the pre-delisting funding into the delisting.
- **Refuted if:** there is no sign relation.
- **Differs from known work:** no study of delisting closures was found (search results only).

**H2 · ETF-NAV: creation pressure in the benchmark hour**

- **Mechanism:** spot bitcoin ETFs strike their NAV on CF Benchmarks' 15:00-16:00 New York window. Issuers filling
  cash creations buy BTC in that hour on US trading days.
- **Persists because:** issuers minimise tracking error.
- **Other side:** market makers.
- **Data:** Binance hourly BTC; trading against non-trading days, before and after 2024-01-11.
- **Prediction:** that hour rises on trading days after the launch, against the same hour on non-trading days and
  before the launch.
- **Refuted if:** the difference-in-differences is ≤ 0.
- **Differs from known work:** a known mechanism (FX fixes) in a new market.

**H3 · Candle-boundary orders of rule-based bots**

- **Mechanism:** bots act when a daily or four-hour candle closes, so their orders cluster in the next candle's first
  minutes, signed by the candle just closed.
- **Persists because:** retail automation is common.
- **Other side:** liquidity providers.
- **Data:** Binance 1-minute klines.
- **Prediction:** continuation at boundary minutes, beyond placebo minutes.
- **Refuted if:** there is no difference from the placebo.
- **Differs from known work:** the identification by the candle clock.

**H4 · MSTR issuance and its earnings blackouts**

- **Mechanism:** Strategy buys bitcoin with at-the-market issuance, a price-insensitive bid, and pauses issuance in
  its earnings quiet periods. The pause is a natural experiment.
- **Persists because:** the bid is set by MSTR's premium, not by BTC's value.
- **Other side:** long-term holders.
- **Data:** EDGAR 8-K purchase filings, MSTR's price.
- **Prediction:** BTC lags in blackout weeks.
- **Refuted if:** there is no difference.
- **Differs from known work:** a firm-level flow, not a market factor.

**H5 · EMIT: emission-driven selling in the spot cross-section**

- **Mechanism:** recipients of new supply (stakers, validators, vesting) sell part of it, a continuous forced sale.
- **Persists because:** shorting altcoins is costly.
- **Other side:** buyers who absorb the supply.
- **Data:** circulating supply per coin.
- **Prediction:** low-emission coins beat the equal-weight market.
- **Refuted if:** the information coefficient is ≥ 0.
- **Differs from known work:** the literature is unsettled (search results: an NBER paper relates the staking ratio
  positively to appreciation).

**H6 · PAIR-1: new fiat and stablecoin pairs as new demand**

- **Mechanism:** a new quote currency (for example a TRY pair) opens an on-ramp for a new clientele.
- **Persists because:** markets are segmented.
- **Other side:** existing holders.
- **Data:** the first day of each pair in Binance's archive.
- **Prediction:** the coin drifts up after the pair opens.
- **Refuted if:** there is no drift.
- **Differs from known work:** listing studies cover new exchanges, not new pairs.

**H7 · GXR-1: gold after US equity panic days**

- **Mechanism:** flight-to-safety demand that later reverses, or a dash for cash.
- **Persists because:** panic buyers pay for immediacy.
- **Other side:** liquidity providers.
- **Data:** COMEX gold and the S&P 500, daily.
- **Prediction:** a signed drift over the 15 days after.
- **Refuted if:** there is no drift.
- **Differs from known work:** a trading rule built on a documented property (Baur & Lucey 2010), with a cost gate and
  a fresh window.

**H8 · Buyback blackout windows and the US 500**

- **Mechanism:** buybacks stop from quarter-end until earnings, so the aggregate corporate bid falls.
- **Persists because:** the blackout is rule-bound.
- **Other side:** everyone else.
- **Data:** quarter dates, the US 500 daily.
- **Prediction:** lower returns in the peak blackout weeks.
- **Refuted if:** there is no difference.
- **Differs from known work:** a flow mechanism rather than a calendar label.

**H9 · Equity futures financing spread as leverage demand**

- **Mechanism:** index futures rich to their fair value mean leveraged longs pay up. This mirrors the record's crypto
  finding.
- **Persists because:** balance-sheet constraints.
- **Other side:** basis traders.
- **Data:** ES futures, the S&P 500, the risk-free rate, dividends.
- **Prediction:** a rich basis precedes lower returns.
- **Refuted if:** no relation.
- **Differs from known work:** the crypto finding carried to equities.

**H10 · Central-bank gold purchases as a slow bid**

- **Mechanism:** official purchases are price-insensitive and persistent.
- **Persists because:** policy, not price, drives them.
- **Other side:** private sellers.
- **Data:** monthly reserve reports.
- **Prediction:** gold rises after large reported purchases.
- **Refuted if:** no relation.
- **Differs from known work:** uses the reported flows, not narratives.

**H11 · On-chain fee spikes as capitulation or euphoria**

- **Mechanism:** urgent transfers pay high fees.
- **Persists because:** panic is costly to hide.
- **Other side:** patient holders.
- **Data:** daily fee totals.
- **Prediction:** a rebound after spikes in a fall, a decline after spikes in a rise.
- **Refuted if:** neither holds.
- **Differs from known work:** fees as a measure of urgency.

**H12 · Protocol revenue and buyback yield**

- **Mechanism:** protocols buy back or distribute their tokens from fees, a price-insensitive bid.
- **Persists because:** few investors value tokens on their cash flows.
- **Other side:** sellers.
- **Data:** fees and revenue per protocol.
- **Prediction:** a high-yield basket leads the market.
- **Refuted if:** no lead.
- **Differs from known work:** buyback yield, carried to tokens.

**H13 · Leveraged-ETF rebalancing at the daily horizon**

- **Mechanism:** leveraged ETFs trade with the day's move at the close, a temporary pressure.
- **Persists because:** the rebalancing is mechanical.
- **Other side:** overnight liquidity.
- **Data:** the ETFs' assets.
- **Prediction:** a next-day reversal scaled by those assets.
- **Refuted if:** no scaling.
- **Differs from known work:** a reversal conditioned on an identified flow.

**H14 · NE-ON-SF: the overnight premium without financing**

- **Mechanism:** a swap-free account pays no financing, which was the only reason NE-ON failed.
- **Persists because:** an institutional cost asymmetry.
- **Other side:** the broker.
- **Data:** the future (history is forbidden).
- **Prediction:** a positive net per night.
- **Refuted if:** the net is ≤ 0.
- **Differs from known work:** the cost regime, not the premium.

**H15 · PROP: the challenge fee against a validated rule's pass rate**

- **Mechanism:** firms price challenges for the typical trader's failure rate, so a rule with a materially higher pass
  rate buys a cheap option.
- **Persists because:** the firms' pricing is averaged over all traders.
- **Other side:** the firm and its failing traders' fees.
- **Data:** FUNDED-P's lifecycle replay.
- **Prediction:** positive expected payout per fee.
- **Refuted if:** the expected payout is ≤ the fee.
- **Differs from known work:** an asymmetry in a business, not in a price.

**H16 · ALT-CALM: the alt basket without its post-rally coins**

- **Mechanism:** SPL-1's reversal, used as an exclusion.
- **Persists because:** shorting is costly.
- **Other side:** late buyers.
- **Data:** the CASC-1 hourly panel.
- **Prediction:** the basket beats the equal-weight market.
- **Refuted if:** no excess.
- **Differs from known work:** an exclusion rule, not a short.

## 3. Ranking and the cheapest decisive check for each

Scores run from 1 (poor) to 5 on the mission's seven criteria. The column headings are short:

- **Plaus.** economic plausibility;
- **Orig.** originality;
- **Data** data availability;
- **Speed** the cost and speed of testing;
- **Profit** potential net profitability;
- **Exec.** ease of execution on the owner's instruments;
- **Test.** statistical testability, i.e. power at t 3.0.

| # | Hypothesis | Plaus. | Orig. | Data | Speed | Profit | Exec. | Test. | Decisive check run today | Result |
|---|---|---|---|---|---|---|---|---|---|---|
| H2 | ETF-NAV | 4 | 2 | 5 | 5 | 3 | 5 | 3 | Closed-family check | **Closed family** (fixes; hour-of-day) |
| H1 | PDL-1 | 3 | 5 | 4 | 5 | 2 | 1 | 1 | Event-count probe | **18 settled delistings**, no power |
| H15 | PROP | 4 | 3 | 4 | 5 | 4 | 4 | 2 | Read FUNDED-P | Structural, descriptive only |
| H7 | GXR-1 | 3 | 2 | 5 | 5 | 2 | 5 | 2 | Prior-art and power arithmetic | Needs about 1.8% an event; sign not fixed |
| H5 | EMIT | 3 | 3 | 2 | 3 | 2 | 2 | 2 | Prior-art and power arithmetic | Needs 1.5-2% a month, long-only |
| H4 | MSTR | 3 | 4 | 3 | 3 | 2 | 5 | 1 | Power arithmetic | Needs about 3.8% a week |
| H3 | Candle bots | 3 | 3 | 5 | 4 | 2 | 4 | 4 | Closed-family check | **Closed family** (intraday) |
| H6 | PAIR-1 | 2 | 4 | 5 | 5 | 2 | 3 | 3 | Prior-art search | **Contrary evidence**: front-loaded, reverts |
| H14 | NE-ON-SF | 4 | 2 | 1 | 1 | 3 | 5 | 1 | Power arithmetic | About t 0.3 a year forward |
| H16 | ALT-CALM | 3 | 3 | 5 | 5 | 1 | 2 | 4 | Tradability check | Beta-dominated; no short |
| H9 | Equity basis | 3 | 3 | 2 | 3 | 2 | 4 | 1 | Power and data check | Persistent signal, few episodes |
| H12 | Revenue yield | 3 | 2 | 3 | 3 | 2 | 2 | 1 | Power arithmetic | 36-60 months, few tokens |
| H8 | Buybacks | 3 | 2 | 3 | 4 | 2 | 5 | 1 | Power arithmetic | About t 2.0 at 3-5 bp a day |
| H11 | Fee spikes | 2 | 3 | 4 | 4 | 2 | 5 | 1 | Power arithmetic | About 100 events, two signs |
| H10 | CB gold | 3 | 2 | 2 | 3 | 1 | 5 | 1 | Power arithmetic | About 300 lagged months |
| H13 | LETF daily | 3 | 2 | 1 | 2 | 2 | 5 | 2 | Data check | No free AUM history; reversal judged |

**How the arithmetic was done.** For n independent events with a per-event deviation σ, t 3.0 needs a mean of 3σ/√n.
The record's pre-check rule (`research/QUEUE.md`) requires that mean to be no larger than the mechanism's plausible
size. A test that cannot pass even if the effect is real is not run.

## 4. The experiments run today

1. **E1 · PDL-1 event count.** This was the decisive experiment for the most original candidate. It read file names
   only, no price, from `research/results/NEWL-1-probe.json` (an S3 listing of Binance's USDT-M monthly klines,
   retrieved 2026-11-15T17:54 UTC).
   - 923 USDT contracts are listed. 31 stopped before 2026-10, mostly renames: MATIC, RNDR, EOS, LUNA, GAL, TOMO, HNT.
   - 18 contracts were settled at delisting, by year of their last month: 2022 1, 2023 3, 2025 8, 2026 6.
   - The mechanism signs the move by funding, which halves the events: about 10 a side. At an alt's multi-day
     deviation of about 15%, t 3.0 needs about 9% an event.
   - **REJECTED: no power.**

   Reproduce:

   ```bash
   python3 -c "import json; c=json.load(open('research/results/NEWL-1-probe.json'))['contracts']; \
   print(len([k for k in c if 'SETTLED' in k]), len([k for k,v in c.items() if v['last']<'2026-10' \
   and k.endswith('USDT') and '_' not in k]))"   # 18 31
   ```

2. **E2 · Prior-art searches.** Run on 2026-11-16, for H1, H5, H6 and H7; every source is listed in section 7.
   - **H6:** the studies found contradict it. Access effects are front-loaded and revert within weeks.
   - **H7:** the property was already documented (Baur & Lucey 2010), with a horizon of about 15 trading days.
   - **H5:** the literature is unsettled.
   - **H1:** no study was found.

3. **E3 · Closed-family check.** Against `docs/DISCOVERY_PROGRAM.md`: H2 and H3 fall in closed families and are not
   re-run under new names.

4. **E4 · Power and cost arithmetic.** For every remaining candidate (section 3).

**Why no outcome test was run.** Every candidate failed a gate that decides its result before the data is read.

- A test with no power cannot reach the bar.
- A closed family would be a failed hypothesis under a new name.
- Contrary published evidence makes the prediction implausible.

Running one anyway would spend fresh data, and a slot of the threshold, on a foregone answer. The owner's standing
rule forbids that: "never invents an experiment to keep a queue busy".

## 5. Classification (the mission's final standard)

| Candidate | Class | Evidence |
|---|---|---|
| TRND-1 (existing) | **VALIDATED** | 1929-1989 t 3.83 against a bar of 3.376. 2021-2026 holdout: 69 months, net t 2.737, +0.785% a month, worst fall 10.6% against the indices' 22.2%. About the market's return at about half its worst fall |
| H15 PROP (challenge economics with TRND-1) | **PROMISING** (structural, not a market inefficiency) | FUNDED-P lifecycle replay, descriptive. 8 FULL accounts: median about $154,000 over three years (about $4,300 a month). Year one median -$8,800 in fees. 10% of starts lose. All accounts fail together on a crash day |
| DAY-1, FXT-1, RCEQ-E1-TOM, TME-1 (existing) | **PROMISING** (near misses) | t 2.48 / 2.71 / 2.18 / 2.24 against bars of 3.08-3.63. TOM is judged forward by TOM-F. FXT-1 and TME-1 are not tradable (FX sealed; Treasuries interest-bearing) |
| H14 NE-ON-SF | **INCONCLUSIVE** (by design) | Gross +2.7 bp a night (NE-ON); financing was the only obstacle. A forward test earns about t 0.3 a year |
| H1 PDL-1 | **REJECTED** before test | 18 settled delistings 2022-2026; about 10 a side |
| H2 ETF-NAV, H3 candle bots | **REJECTED** before test | Closed families |
| H4, H5, H8, H9, H10, H11, H12 | **REJECTED** before test | Power (section 3) |
| H6 PAIR-1 | **REJECTED** before test | Contrary evidence |
| H7 GXR-1 | **REJECTED** before test | Prior art, an unfixed sign, power |
| H13 LETF daily | **REJECTED** before test | No free data; the daily reversal was already judged |
| H16 ALT-CALM | **REJECTED** before test | Not separable from alt beta without a short |

**No new candidate is VALIDATED or PROMISING as a market inefficiency.** That is the honest result of this round.

## 6. What the evidence says about where a profit can come from

1. **Costs, not information.** The lab finds information at about twice chance on crypto perpetuals, and dozens of
   rules that were positive before costs and negative after. A cheaper execution venue changes which rules survive.
   - The owner's swap-free CFD costs are the next measured input: the cTrader probe (`docs/CTRADER.md`) records them
     once the owner's demo secrets exist.
   - A test re-judged on read rows under new costs is not allowed. A new cost regime earns a new, forward test.
2. **Capital, not a new edge.** TRND-1 earns about the market's return, so the target is reached by capital: funded
   accounts at FULL size.
   - The demo desk (`docs/CTRADER.md`) now runs it on a cTrader demo account by itself, once the owner sets the
     secrets and gives the word.
   - Challenges are bought only on the owner's explicit word.
3. **The record's strongest information is on the short side of altcoins.** SPL-1, SQZ-1, BAS-1 and CASC-1 point the
   same way. It becomes a trading question only if two things are true:
   - the owner adds swap-free altcoin CFDs (short) to the allowed instruments;
   - a broker quotes them.

   The hourly window 2025-03-08 to 2026-10-29 is still unread and would be its validation. With only the ten or so
   coins a broker quotes, its power must first be checked on that subset.
4. **FX** stays sealed until the owner sets a date (`research/holdout.json`).

## 7. Sources (web searches of 2026-11-16; search results only, no paper read in full)

- [Binance listing effect (CoinDesk/Yahoo)](https://malaysia.news.yahoo.com/binance-effect-means-41-price-173526978.html)
- [The TIE: what a Binance listing delivers for already-listed tokens](https://www.thetie.io/insights/what-a-binance-listing-delivers-for-already-listed-tokens)
- [The TIE: what an exchange listing delivers in 2026](https://www.thetie.io/insights/what-does-an-exchange-listing-actually-deliver-in-2026)
- [RockawayX: what happens when tokens list on a CEX](https://rockawayx.com/insights/bullish-or-bearish-what-really-happens-when-tokens-list-on-a-cex)
- [Baur & Lucey (2010), RePEc entry](https://econpapers.repec.org/RePEc:bla:finrev:v:45:y:2010:i:2:p:217-229)
- [Baur & Lucey, IIIS discussion paper 198](https://www.tcd.ie/triss/assets/PDFs/iiis/iiisdp198.pdf)
- [CXO Advisory: gold as hedge and safe haven](https://www.cxoadvisory.com/gold/gold-as-hedge-and-safe-haven/)
- [NBER w33640 (staking)](https://www.nber.org/system/files/working_papers/w33640/w33640.pdf)
- [Cross-sectional return predictors of utility tokens (ECGI)](https://ecgi.global/sites/default/files/Paper%3A%20Cross-Sectional%20Return%20Predictors%20of%20Utility%20Tokens.pdf)
- [Hyperliquid JELLY delisting (Cointelegraph)](https://cointelegraph.com/news/hyperliquid-delists-jelly-perps-citing-suspicious-activity)
- [KuCoin futures delisting notice](https://www.kucoin.com/announcement/en-kucoin-futures-will-delist-the-xcnusdt-flmusdt-and-perpusdt-perpetual-contracts-11-21)

## 8. Reproduce

- The audit's numbers:

  ```bash
  python3 -c "import sys; sys.path.insert(0,'.'); from aitrader.research.registry import Registry; \
  r=Registry.load('research/registry.jsonl'); import collections; \
  print(collections.Counter(r.status_of(t.id) for t in r.trials))"
  ```

- The ledger lines: `research/inventions.jsonl`, at 2026-11-16T14:05:00Z; rendered in `docs/INVENTIONS.md`.
- The lab's numbers: `git show origin/lab-data:DIRECTOR_BRIEFING.md`.
- The paper desk's numbers: `git show origin/perf-data:PERF_REPORT.md`.
