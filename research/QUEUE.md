# The research queue (owner, 2026-11-04 and 05: "anything that makes us a profit; never stop")

This queue is worked through one candidate at a time, by a recurring check-in. Each candidate is handled the same
way:

1. Pre-registered before its data is fetched or any outcome is computed: a frozen spec and frozen code hashes.
2. Given a threshold that counts every earlier test on its universe (`research/registry.jsonl`).
3. Split into development, validation, and a holdout opened once and only after a pass.
4. Judged once, with the result committed and reported to the owner as it is. A failure is a result, not a reason
   to stop.

The order is set by mechanism and evidence. A candidate needs a reason to exist beyond a pattern, and fresh data
where possible: the FX M5 2009-2016 data carries 166+ tests and a bar of 3.6. Only a candidate that passes and is
validated is ever proposed as a paper strategy (CLAUDE.md rule 14), never real money.

| # | Id | Question | Why it might pay | Known against it | Status |
|---|---|---|---|---|---|
| 1 | VRP-1 | Short VIX futures (VIXY) while the VIX curve is in contango | The insurance premium: buyers of crash protection overpay on average | Rare catastrophic days (Feb 2018, Mar 2020); a famous trade | FAILED (2026-11-05) |
| 2 | FOMC-1 | Long the S&P 500 into scheduled FOMC announcements | Lucca & Moench (2015): most of the equity premium 1994-2011 was earned in the 24 h before FOMC | Kurov, Wolfe & Gilbert (2021) find it faded after 2015 | FAILED (2026-11-05, as FOMC-1A) |
| 3 | XSM-1 | Crypto cross-sectional momentum: hold last week's strongest large coins | Liu, Tsyvinski & Wu (2022): momentum across coins, retail-driven | Point-in-time universe and costs; CR-1's time-series momentum failed | FAILED (2026-11-05) |
| 4 | VOLM-1 | Volatility-managed S&P 500 exposure (Moreira & Muir 2017): its alpha on the market, at the market's own risk | Volatility clusters while returns do not scale with it | Cederburg et al. (2020): weak out of sample | FAILED (2026-11-05; only t: alpha +2.6% a year at t 1.27) |
| 5 | GSR-1 | Gold/silver ratio mean reversion | Two metals with a shared driver; the ratio has historically reverted | Long regimes without reversion; costs on silver | FAILED (2026-11-05) |
| 6 | SEC-1 | US sector ETF momentum, monthly (industry momentum, Moskowitz & Grinblatt 1999) | Industries trend for months | Crowded since publication | FAILED (2026-11-05) |
| 7 | PHD-1 | The pre-holiday effect in US equity indices | Ariel (1990) and later | Likely faded; few events a year | FAILED (2026-11-05) |
| 8 | EMC-1 | Emerging-market currency carry: hold the higher-yielding of the emerging currencies a CFD broker quotes (MXN, ZAR, TRY, PLN, HUF, CZK) against the dollar, ranked by policy-rate differential | The carry premium: high-yield currencies pay their rate differential on average (Lustig & Verdelhan 2007; Burnside et al. 2011), as pay for crash risk | Crashes (2008, 2013, 2018 TRY); wide spreads and swap markups on exotic CFDs. Fresh data: no test here has used emerging currencies | FAILED (2026-11-05) |
| 9 | LVOL-1 | The low-volatility anomaly: the S&P 500 low-volatility ETFs (SPLV, USMV) against SPY at equal risk | Leverage-constrained investors overpay for risky stocks (Frazzini & Pedersen 2014, "Betting Against Beta") | Only since 2011; crowded since 2016; a CFD broker may not quote these ETFs. Fresh data: these ETFs are untested here | FAILED (2026-11-05) |
| 10 | TSY-1 | The Treasury auction cycle: short the 7-10 year Treasury ETF (IEF) in the days before each 10-year note auction, and long in the days after | Lou, Yan & Zhang (2013): Treasury prices fall before auctions and recover after, because dealers must absorb the new supply (1980-2008; a 10-year note strategy's Sharpe was about 0.9 after costs). Fleming, Liu & Nguyen (NY Fed) still see the pre-auction rise in yields in recent intraday data | Non-dealers now absorb more of each auction, and the price pressure has not grown. Fresh data: everything after 2008 is outside the paper's sample, and no test here has used Treasury auction dates | FAILED (2026-11-05) |
| 11 | TME-1 | The Treasury month-end effect: hold IEF over the last three trading days of each month | Hartley & Schwarz (2019): coupon Treasuries earned their excess return in the last few days of the month (1990-2018), from insurers' and index funds' month-end buying. Month-end Treasury trading has grown since 2020 (NY Fed) | A test on TLT since 2002 did not find it (CXO Advisory); a CFD's costs take a large share of about 0.25% a month. Fresh: 2019 on is after the paper's sample | FAILED (2026-11-05; only t: +0.106% a month-end at t 2.24) |
| 12 | RBL-1 | The month-end rebalancing reversal in the S&P 500: when stocks have beaten bonds over the month, short the US 500 over the month's turn; when bonds have beaten stocks, long | Harvey, Mazzoleni & Melone (2025): pension and balanced funds rebalance to fixed weights at month-end, and when stocks are overweight their selling lowers equity returns by about 17 bp the next day. TME-1's month-ends showed the bond side of such flows | The paper's sample covers most of the data; an index CFD's costs on a short hold; US equity data carries over 30 tests here, so its bar is about 3.17. New here: no test has used the stock-bond gap as a signal | FAILED (2026-11-05) |
| 13 | FCY-1 | The FOMC cycle: hold the S&P 500 in the even weeks of FOMC cycle time, flat in the odd weeks | Cieslak, Morse & Vissing-Jorgensen (2019): over 1994-2016 the equity premium was earned in weeks 0, 2, 4 and 6 after FOMC meetings, which they trace to the Fed's information flow | Weekly returns give little power; the pre-FOMC drift faded after publication (FOMC-1A). Fresh: 2017 on is after the paper's sample | DROPPED before building (2026-11-05): even at its published strength (Sharpe 0.8 against 0.4), 2017-2026 would give t of about 2.5, below the bar of about 3.18. It cannot pass, so it is not run |
| 14 | EAP-1 | The earnings announcement premium: hold US large caps over the week of their scheduled earnings announcements, against the S&P 500 | Announcing firms earn more in announcement weeks (Frazzini & Lamont 2007; Savor & Wilson 2016; Barber et al. 2013, around the globe): attention and the systematic risk that announcements carry. Hundreds of announcements a year give a test real power | Survivorship: today's index members had good news in their past, which would inflate exactly this effect. The universe must be fixed at the start, from a point-in-time member list, before any price is read; a probe must first show that the earnings dates and that list can be had. Single-stock CFD costs | DROPPED before building (2026-11-05): the published premium is about 9.9% a year while announcing, about 0.19% a week, below a single-stock CFD's round trip and a week's markup; and a working paper reports it has disappeared in the US. It cannot pay, so it is not run |
| 15 | TRND-1 | Own a stock index only while its month-end close is above its 10-month average (Faber 2007), long or flat, in a swap-free account | Large bear markets have usually unfolded over months, below the long average. The rule's documented benefit is smaller crashes at about the market's return. RC-EQ measured it at 5.76% a year before costs on ten index CFDs (1990-2020); a CFD's financing, which a swap-free account does not charge, took most of it | Not an edge: mostly the equity premium made calmer, below the power ceiling's rule of thumb. A replication: the rule was published from data that include 1929-1989. Fresh for this registry: no test here has read the S&P 500 before 1990. Bar 3.376 (67 earlier tests on stock-index data, intraday ones included); estimated chance of passing about two in three | PASSED and VALIDATED (2026-11-06): t 3.83 against 3.376, and every holdout rule passed. Proposed to the owner as a paper strategy. Their word (2026-11-08): the trend desk trades it by itself on paper (`docs/TREND_DESK.md`) |
| 16 | DAY-1 | The 2-day RSI pullback in an uptrend on the four index CFDs: buy at the close when the 2-day RSI is below 10 above the 200-day mean, sell at the first close above the 5-day mean (Connors & Alvarez 2009), with the bot's 6% stop | The owner, 2026-11-08: "$4,000 a month; trades so the account moves; more profit than loss". Short pullbacks inside uptrends have reverted in the published record, with about 70% of trades won; about a dozen trades a year per index | Published in 2009 and widely traded; post-2007 evidence is mixed (0.25-0.69% a trade in 2007-2009, about 0.26% on the S&P 500 in 2016-2026). Index years 1990-2026 were read before (RC-EQ, TRND-1-H), so the bar counts them: 3.3879. Estimated chance of passing about one in three | FAILED (2026-11-08, on t alone: +1.81% a year, t 2.48 against 3.3879; 69.6% of 941 trades won; development t 3.02, validation 2006-2020 t 0.49) |
| 17 | CRY-1 | Bitcoin intraday time-series momentum: long BTC for the day's last half-hour when its first half-hour rose (Shen, Urquhart & Wang 2022, Financial Review), long or flat | The owner's active-trading program: one trade a day. The paper finds the first half-hour predicts the last, in and out of sample, from liquidity provision. Fresh: no test here has read crypto's intraday bars | A crypto CFD's round trip (about 0.05-0.1%) may be larger than the predictable part of a half-hour. The power check comes first, from the paper's own numbers: it is built only if the edge net of costs can reach the bar | DROPPED before building (2026-11-09): at the founding study's size it gives t between −3.4 and +1.9 against a bar of 3.1628; it would need an R² of 3.2-14.5% |
| 18 | ENG-1 | The energy futures term-structure premium: hold WTI, heating oil, RBOB and natural gas only while contract 2 is above contract 3, long or flat, swap-free (`docs/DISCOVERY_PROGRAM.md`, H1) | The theory of storage and hedging pressure: a backwardated contract rolls up toward spot. The term-structure factor's Sharpe ratio is about 0.41-0.49 | No single-energy, long-or-flat result was found; 2005-2014 was mostly contango; a CFD's roll terms; only WTI and natural gas are commonly quoted. Fresh: no test here has read energy curves. Bar 3.0; estimated chance of passing 27-58% | FAILED (2026-11-09, on t: +2.48% a year net, t 2.09 against 3.0; the slope beat 99.7% of shuffled timings, but the premium was small, halved after 2002 and gone a month late) |
| 19 | LIQ-1 | Buying after forced crypto deleveraging: long BTC or ETH for 24 h after an hour whose open-interest collapse and price fall are both beyond their trailing 1st percentile (H2) | Fire sales pay those who provide liquidity (Coval & Stafford 2007); liquidations are forced, price-insensitive sales | No rigorous crypto study; cascades can continue; the same leverage family as FND-1A. The probe found BTC open interest every 5 minutes from 2020-09 and ETH from 2021-12, both complete | **FAILED** stage 1, 2026-11-10: 83 trades, mean net −0.63% a trade (t −1.06), no better than matched random entries (74% did as well); stage 2 not registered, its data unfetched (`research/preregistrations/LIQ-1.md`) |
| 20 | DLAB | The discovery lab (`docs/DISCOVERY_LAB.md`): rules found by search on whole panels, not recalled from the literature. Each panel gets a registered discovery scan, then a preregistered validation of what the scan found promising, on rows no scan read. Panels: WTI and natural gas (done); 55 Binance perpetuals by day; 31 US-listed funds by day | A rule traded on every instrument of a broad panel at once gets a pooled test, which has power a single instrument's test has not | Crypto's history is short; costs; the bar stays at 3.0 or above. A scan validates nothing by itself | DLAB-ENG-1: the scan proposed nothing (2026-11-10). DLAB-ETF-1 and DLAB-CRD-1, run by the lab's own worker on GitHub's runner: neither scan proposed anything (2026-11-12). Next: the cross-sectional places of a scan go to each ranking before they go by strength (`docs/DISCOVERY_LAB.md` section 11) |
| 21 | NEWL-1 | New Binance USDT-M perpetuals against seasoned ones: short a new contract at the close of its first full day for 30 days, against an equal-weight long basket of contracts listed 181 to 365 days earlier, after funding and 15 bp a fill | Supply overhang at a new token's listing (unlocks, airdrops, market makers' inventory) and attention, with the short easier on a perpetual than in spot | Squeezes on thin new floats; crowded shorts pay funding; the archive may not keep removed contracts | FAILED (2026-11-15): `research/results/NEWL-1-verdict.md` |
| 22 | EXF-1 | The ex-funding pass-through: across a funding settlement, does a perpetual's price move by the payment? Take the side the previous rate says receives it, from T-5m to T+5m | A lump payment at a known time on a zero-cost contract is priced only by the traders who time it; where they are few the receiving side keeps part of it | Timing bots; the cost of two fills; the index may move with the contract | FAILED (2026-11-15): `research/results/EXF-1-verdict.md` |
| 23 | SQZ-1 | Crowded shorts and the spot buyer: buy the spot of a seasoned coin whose perpetual's funding paid its longs at least theta per 8 hours over 72 hours, hold seven days, against the seasoned market | Crowded leveraged shorts are squeezed out by liquidations and stops; a spot buyer pays no funding | Heavily shorted stocks underperform; shorts may be hedges of unlocks | FAILED (2026-11-15): `research/results/SQZ-1-verdict.md` |
| 24 | CASC-1 | Liquidation-led falls and the spot buyer: buy spot after a four-hour fall of at least 8% with the perpetual at least 0.5% below spot, hold 24 hours | Forced selling by the liquidation engine is not informed and should be bought back | Cascades continue; buying falls in crypto has lost before (LIQ-1) | FAILED (2026-11-15): `research/results/CASC-1-verdict.md` |
| 25 | BAS-1 | High funding and the spot buyer: buy the spot of a coin whose funding paid shorts at least theta per 8 hours over 72 hours, hold seven days | Carry capital buys spot to earn high funding; trend-chasing leverage | Crowded longs crash | FAILED (2026-11-15): `research/results/BAS-1-verdict.md` |
| 26 | HLQ-1 | Visible liquidation clusters on Hyperliquid: at a half-hourly snapshot where one side holds at least 75% of the leveraged notional liquidated 1-5% from the mark (and at least 1% of open interest), trade toward it, target and stop at its mean distance; on bitcoin and ether CFDs, swap-free, long or short | Predatory trading (Brunnermeier & Pedersen 2005) and cascades, on the one venue whose liquidation prices are public | Hyperliquid's mark is anchored to other venues' prices; a six-month forward window | DROPPED before registration (2026-11-16): the probe found no liquidation within 5% of the mark among the 800 largest accounts; the near ones are spread over about 47,000 accounts, and Hyperliquid's mark is a median with other venues' prices, so the effect on bitcoin and ether is not plausible at t 3.0. Its recorder was stopped; nothing was registered |
| 27 | SPL-1 | Spot-led rallies and the spot buyer: buy the spot of a seasoned coin whose spot rose at least 8% (or 15%) in four hours while its perpetual never closed more than 0.25% above spot, hold 24 hours | Unlevered demand does not have to be unwound; the leverage-led rises are the contrast | Coordinated pumps of thin coins reverse within hours; momentum families failed here | FAILED (2026-11-16): `research/results/SPL-1-verdict.md` |
| 28 | KRP-1 | The Korean coin premium: buy a coin on Binance spot, against a bitcoin CFD short, the day after its price in bitcoin on Upbit stood at least 5% (or 10%) above its price in bitcoin on Binance after a month without such a gap; hold 24 hours | Capital controls keep foreigners off Korea's venues; residents can close a coin-relative gap without moving won abroad, by buying the coin and selling bitcoin on the global venue (`docs/ORIGINAL_EDGE_HUNT_2.md`, A1) | The gap can close on the Korean side alone; arbitrage may finish within the hour; Korean spikes can mark retail tops | **FAILED** (2026-11-22): dev judged once (run 44978747723, reproduced exactly by 44982217651) on 2018-01 to 2025-02: 5% FAILED (288 entries, t -0.87, bar 3.0, every gate but one), 10% INCONCLUSIVE (138 entries, 150 required; t -0.92); +0.29% and +0.11% before the 0.6% round trip, -0.31% and -0.49% net. No later stage (`research/results/KRP-1-verdict.md`) |
| 29 | SCX-1 | Stablecoins while their primary market is shut: at 22:00 UTC on Sunday, swap a stablecoin pair at least 3 bp (or 10 bp) from par into its cheap side, from a stock of both, and back at 21:00 UTC on Monday | Issuers mint and redeem only on US banking days, so at weekends the peg rests on market makers' stock (`docs/ORIGINAL_EDGE_HUNT_2.md`, C1) | A tick of deviation is often the last trade's bounce; tiny capacity even if real | **FAILED** (2026-11-22): dev passed at 10 bp (242 swaps, +8.6 bp, t 3.02), then validation on unread 2023-07 to 2026-10 failed every gate (251 swaps, -0.2 bp, t -0.25; Wednesdays +2.0 bp). No forward stage (`research/results/SCX-1-verdict.md`) |
| 30 | UDL-1 | The Korean exit at an Upbit delisting: buy the coin on Binance spot after Upbit's cut-off, hold ten days | A captive clientele must sell by a dated deadline; the selling reaches the global price through arbitrage, and ends on a known date (`docs/ORIGINAL_EDGE_HUNT_2.md`, B1) | The SEC staff study found declines persisting a month after regulatory events | WAITING FOR DATA: Upbit's notice pages refused GitHub's runner (HTTP 403, 2026-11-22); not failed. It needs a reachable record of the notices. Checked again on 2026-11-22, 16:49 UTC (search results only): no compiled list was found; National Assembly figures put Upbit's delistings at 157 from 2017 to 2022-08 (Money Today, 2022-10-05); a third-party news feed (bloomingbit's exchange-announcement bot) republishes Upbit's notices with dates. Using a third-party copy of notices Upbit refuses to serve is the owner's decision, and it was not probed. Power if about 80 of the delistings are of coins Binance lists: at a 10-day standard deviation near 25%, t 3.0 needs about +8% a trade after the cut-off, against a published finding of further declines |

**Considered on 2026-11-05 and dropped before any code or data.** Before a candidate is built, its power at the
published strength, after a retail CFD's costs, is now checked against its bar. A test that cannot pass even if the
effect is real is not run. Each of these was checked and dropped:

| Idea | Why it was dropped |
|---|---|
| Gotobi USD/JPY flows at the Tokyo fix | Already judged: FLOW-1 (2007-2016) lost money in most years. A rerun on the same data is not allowed |
| Earnings-announcement premium in single stocks | About 0.19% a week while announcing, below a single-stock CFD's round trip. A working paper reports it has gone in the US. Survivorship would also inflate it |
| FOMC-cycle even weeks (FCY-1) | At full published strength, 2017-2026 gives t of about 2.5 against a bar of about 3.18 |
| Macro-announcement-day premium (CPI, payrolls, FOMC days) | At full strength, about t 2.1 over 2010-2026, and about half of it goes on costs |
| Variance-risk-premium timing of the S&P 500 | The timing difference reaches about t 1.5 over 2008-2026 |
| Short natural gas in contango | About t 2.5 at full strength over 2009-2026, with squeezes that wipe out a short |
| Commodity index-roll front-running | Reported to have gone after 2004 |
| S&P 500 index-inclusion effect | Reported to have gone in the 2010s |
| US overnight drift at the European open | Flat since 2021 (New York Fed, 2026) |
| RSI(2) dip-buying on index CFDs | About +0.26% a trade on the S&P 500 in 2016-2026, roughly t 1 |
| Monetary momentum: the market for 15 days after a dovish FOMC surprise (Neuhierl & Weber) | Sharpe 0.52 in 1994-2009, read from the paper. Over the fresh 2010-2026 that is about t 2 at full strength, at CFD or futures costs alike, against a bar of about 3.18 |

**Checked on 2026-11-11 and dropped again, this time for a reason that holds.** The engine's first cycle
(2026-11-10) rejected two ideas on its critic's word. Both rejections said "short selling and leverage", which break
no condition of the owner's (`docs/DISCOVERY_AUDIT.md`, weakness 2). The engine's ledger is never rewritten, so
their second look is recorded here, by the arithmetic the engine now applies to every idea (engine 1.2.0: the bar of
the idea's own window, never below 3.0, and a plan for what it would take):

| Idea | Why it was dropped |
|---|---|
| EM FX central-bank intervention follow-through (engine, 2026-11-10) | Insufficient power, not a broken condition. At its claimed net Sharpe of 0.5 over 5 fresh years it expects t 1.1 against 3.0. Its plan: about 36 years of fresh data, or the same mechanism on about 8 independent currencies tested as one book. Few central banks publish daily intervention amounts, so the book is the harder half |
| Same-day reversal after the EIA crude inventory report (engine, 2026-11-10) | Insufficient power: a net Sharpe of 0.5 over 8 fresh years expects t 1.4 against 3.0. Its plan: about 36 years, or about 5 independent instruments. It is also an intraday rule on one instrument, where a CFD's costs took the whole gross edge of every family tested here |

**What the record says about costs.** Real effects keep showing before costs and vanishing after them:

- the Treasury month-end effect: t 4.07 before costs, 2.24 after (TME-1);
- the Treasury auction cycle: about t 2 before costs, below zero after (TSY-1);
- diversified trend following (DIV-2): validated at futures-style costs, at +2.3% a year in its holdout. A retail CFD
  would have lost 5.7% a year on it.

A retail CFD's spread and its 2.5% a year financing markup are the obstacle. Cheaper execution, such as futures or
ETFs, is a question for the owner, and it would still be paper first. Until then the queue continues with candidates
that can pass at CFD costs.

**Next (from 2026-11-05 evening).** No idea checked so far can pass at CFD costs. Each check-in now looks for new
*information*, not new periods of old prices. It runs the power check first and builds only what can pass. The
first to check:

- the EIA's weekly natural-gas storage against its five-year average, for NATGAS (the theory of storage). Checked the
  same evening and dropped: natural gas moves 7-8% a week, so even a 0.5% a week edge reaches only about t 2.5 over
  25 years;
- the CFTC's positioning in gold, oil and the index futures (COT-1 tested only the currencies). Checked and dropped:
  hedging pressure needs a wide cross-section of commodities, and the broker quotes five, which gives about t 1.5.

**What the wider literature says (checked 2026-11-05, 21:30 UTC).** It agrees with this registry:

- a study of 60 published strategies found their Sharpe ratios fell by about half after publication;
- Chen & Velikov (2023, "Zeroing in on the Expected Returns of Anomalies") put the average stock anomaly's expected
  return, net of costs and of the decay after publication, at about 8 basis points a month;
- no study was found of a futures or currency anomaly with an out-of-sample Sharpe ratio above 1.5.

A test on fresh data can confirm only an effect strong enough to reach its bar. Published effects, halved by
publication and cut again by retail costs, rarely are.

With these, no idea found so far can pass at a retail CFD's costs. The queue waits for the owner's word on cheaper
execution. Each check-in keeps looking for new information, and builds a candidate only when its power check
passes.


**The owner's condition (2026-11-06): "everything is fine; the most important thing is Islamic".** Every new candidate
from now on:

- is costed as a swap-free (Islamic) CFD account: spread, slippage and commission, and no overnight financing. A
  broker's administration fee on long holds is unknown, so the costs-doubled gate stays;
- uses no interest-bearing instrument, which rules out Treasuries and other bonds whatever they earn;
- says plainly whether it needs short selling or leverage, which some readings of Islamic finance exclude.

**Checked the same morning, so that swap-free costs do not revive it by mistake: the turn of the month (TOM).** Its
recorded cost lines show a swap-free account would have kept about 3.6% a year on universe A (t about 3.1) and 2.9%
on universe B (t about 3.4) over 1990-2026. That is arithmetic on recorded results, not a test, and it changes no
verdict. TOM-D's report (docs/TOM_INVESTIGATION_REPORT.md) also shows the calendar effect gone from 2009 on the
indices the bot trades. About 85% of what a TOM trade earned gross since then is the market's own drift, and the net
since 2009 cannot be told from zero. So it is not proposed, and TOM-F keeps following it forward.

**The power ceiling (checked 2026-11-06).** Holding the broker's four index CFDs long at equal risk, swap-free, is the
market's own drift with no prediction at all. Over 1988-2020 it reaches only about t 2.5-2.9, below the bar of about
3.19 that US equity data now carries. A strategy weaker than the equity premium itself cannot be confirmed on the
data that exists. A candidate is built only when its published effect is several times stronger than that.

**Also dropped on 2026-11-06:** the Ramadan effect (Białkowski, Etebari & Wisniewski 2012: higher, calmer returns
during Ramadan in the indices of 14 Muslim-majority countries). The broker quotes none of those indices, and each
gives one event a year.

**After TRND-1 (checked on 2026-11-06, 18:30 UTC, and dropped before building).** TRND-1 waits for the owner's word.
These were checked for fresh data and for power, and none can pass:

| Idea | Why it was dropped |
|---|---|
| TRND-2: TRND-1's rule, unchanged, on other markets' pre-1990 histories | A dates-only probe (`scripts/trnd2_probe.py`, `research/results/TRND2-probe.json`) found daily pre-1990 history on Yahoo for only the Nikkei 225 (from 1965), the Nasdaq Composite (from 1971) and the TSX (from 1979). The others start between 1984 and 1987 or after 1990, and Stooq answered with a web page instead of data. Those years are dominated by Japan's bubble and hold about two independent crashes. A pass would mostly measure the bubble, and a test of the filter's advantage would have no power |
| Gold under TRND-1's rule, 1968-2001 (a daily London fixing, such as the Bundesbank's) | Fresh, but a rough estimate gives about t 2.7 at full strength. Many scholars also hold that gold must be exchanged hand to hand, which a CFD is not |
| Currency trend rules, 1974-1999 (fresh) | Moving-average profits in currencies were documented in those years and documented to have faded by the late 1990s (Olson 2004; Neely, Weller & Ulrich 2009). A pass would describe a market that no longer exists. An FX position also always sells one currency |
| Holding the index CFDs overnight only, swap-free | Two spreads a day would take most of the overnight premium even without a swap, and NE-1 already failed on it |
| Yield-curve or margin-debt crash filters on top of TRND-1 | Any fresh sample holds six to eight recessions or leverage cycles: no power for an effect added to TRND-1's |
| Currency carry | A swap-free account earns no carry by construction |

**Checked on 2026-11-07, 00:30 UTC, and dropped before building.**

| Idea | Why it was dropped |
|---|---|
| Intraday momentum on the GER 40 and UK 100 (their intraday bars are fresh: IX-2's six indices left them out) | IX-2 found the US version's gross edge smaller than a CFD's spread, and FT-1 found the same at 2025-2026 spreads. The international evidence is weaker than the US's, so it cannot reach a bar near 3 at the same costs |
| A pre-announcement drift before ECB or Bank of England decisions | Brusa, Savor & Wilson (2020, "One Central Bank to Rule Them All") find the drift before FOMC announcements only, not before other central banks' |
| The pre-holiday effect on the European indices | PHD-1 found none in the US (t 0.82). Eight or so events a year give no power at a CFD's costs |
| Calendar-month seasonality (January, September) in the four indices | One event a year per index |

**Checked on 2026-11-07, 03:30 UTC (a literature search), and dropped.** The search looked for recent out-of-sample
evidence in index futures, gold and crude oil. It found the index calendar effects gone after 1990 (an Atlanta Fed
working paper on the turn of the month in S&P 500 futures), and only mixed or academic-only evidence for oil. For
gold it found two leads:

| Idea | Why it was dropped |
|---|---|
| Gold's "autumn effect": September and November positive in 1980-2010 (Baur, "The autumn effect of gold") | Two months a year. On the 16 years since the paper's sample, even half its strength gives about t 1.3 |
| Gold rising in Asian hours and falling in Western ones (two master's theses; drops around the London fixes in the years of alleged manipulation) | Not peer-reviewed. The intraday gold data here are either already used (2009-2016) or sealed (2017 on, the global holdout), and a daily round trip's spread takes most of it |

**Checked on 2026-11-08, 21:30 UTC (the queue is empty), and dropped before building.** Each was checked for a
mechanism, fresh data and power at a swap-free CFD's costs:

| Idea | Why it was dropped |
|---|---|
| The Halloween effect ("sell in May"): the four index CFDs held only from November to April | The effect has held out of sample: about 10 points a year more in November-April than in May-October, pooled over 37 markets, 1998-2012 (Andrade, Chhaochharia & Fuerst 2013). The anomaly is the gap between the halves, and a yearly gap with a spread of about 16 points gives about t 3.0 over 2003-2025 even at that full pooled size, against a bar of about 3.39: about one chance in three of passing if the effect is still at full size, much less if it has decayed as published effects usually do. On 1929-1989 at half that size it is about t 2.3. What a winter-only hold earns beyond the gap is the equity premium on a calendar, which TRND-1 already holds with a validated rule |
| TRND-1's rule on the Dow Jones, 1896-1928, before TRND-1's own years | Fresh, but 396 months at TRND-1's own strength give about t 2.8 against a bar of about 3.39. It would repeat a validated rule, not add information |
| Holding the indices only while the VIX futures curve is in contango (a stress filter) | A filter on the market's own premium: bounded by the power ceiling (about t 2.5-2.9), and VRP-1 already read this curve from 2004 |

The queue therefore stays empty. Each check-in keeps looking for new information, and builds a candidate only when its
power check passes.

**Checked on 2026-11-09, 00:30 UTC, and dropped before building: CRY-1 (row 17).** The paper's own tables could not
be read from this workspace, because its repository's host is outside the allowed network. So the check takes the
size the founding study published for the same effect in the S&P 500: an R² of 1.6% in sample and 1.2% out of sample
(Gao, Han, Li & Zhou 2018). It then asks what size CRY-1 would need.

| | |
|---|---|
| The trade | Long BTC for the day's last half-hour when its first half-hour rose. Long or flat: one trade on about half the days |
| Fresh data | About 930 trades over 2021-09..2026-10 (the accepted manuscript is dated September 2021) |
| The bar | t ≥ 3.1628, counting the 31 earlier tests on crypto data |
| Its power | t = (0.8ρ − c/σ)·√N. A trade's gross edge is about 0.8ρσ, against a round trip c. Here ρ is the correlation of the two half-hours, σ the last half-hour's volatility, and N the number of trades |
| At the founding study's size | t between −3.4 and +1.9, over half-hour volatilities of 0.30-0.50% and round trips of 0.02-0.06% |
| To pass | An R² of 3.2% to 14.5% after publication: two to nine times the founding study's in-sample size. Trading both sides every day (excluded by long or flat) reaches about t 2.6 at best |

The paper traces the effect to liquidity provision. That suggests the predictable part pays whoever supplies
liquidity in that half-hour, while a CFD trader is the one paying the spread. CRY-1 is checked again only if the
paper's own tables show an R² above 3%.

**Checked on 2026-11-09, 03:30 UTC (a web search for rules that trade every day), and dropped before building.**

| Idea | Why it was dropped |
|---|---|
| Bitcoin's evening hours: long BTC from 21:00 to 23:00 UTC every day (Quantpedia, hourly Gemini data 2015-10..2022-02: 33% a year gross at 20.9% volatility) | No stated mechanism, and the two hours were picked as the best of 24 on the data that reports them. A study of seven exchanges found no persistent hourly pattern, and Quantpedia's own extension notes a rough 2022-2023. On the years after the finding, even its full published size gives at most about t 2.4 at a 0.02% round trip, and under 1 at half size, against 3.1628 |
| An intraday breakout of the "noise area" on GER 40 and UK 100, whose intraday bars are fresh (Zarattini, Aziz & Barbon 2024: a Sharpe ratio of 1.33 net on SPY, 2007-2024, in sample, long and short) | A CFD's spread would take about 0.35 of that Sharpe ratio at about 200 trades a year. To reach a bar of about 3.4 over 2012-2026, the rule would have to keep about 82% of its in-sample strength in other markets, after publication. At half strength it gives about t 1.1-1.8. A 2026 falsification study found that none of 14 such intraday momentum rules on Nasdaq futures survived walk-forward validation after costs, and an open implementation of this one found it much weaker than the paper |
| Gold's overnight drift: long from the US close to the next open (Blose & Gondhalekar: COMEX overnight returns positive and day returns negative, 1985-2012) | Reported to have weakened substantially since. Gold's intraday prices from 2017 on are in the sealed global holdout, and the years before are the FX desk's most-tested ones |
| Daily technical rules (moving-average and breakout) on the index CFDs | Rink (2023) tested them on the leading indices of 41 markets: strong in sample, insignificant or significantly negative out of sample against holding, and sensitive to moderate costs |

No rule found so far trades every day and can reach its bar at a CFD's costs. It is the pattern in "What the record
says about costs" above: the more often a rule trades, the smaller each trade's edge, and a spread paid on every
trade takes it.

**Checked on 2026-11-09, 05:50 UTC (a search for newer out-of-sample work), and nothing new to build.** The owner,
the same morning: "don't go quiet until we find the solution". The check-ins now run every hour and report every
cycle.

- **Crypto.** Recent out-of-sample work finds statistical predictability, but no trading profit after costs. That
  covers daily forecasts over 2021-2024 (Arain & Snudden 2025), machine-learning signals with fees (a 2025 preprint)
  and portfolio tests (Chen 2025). In the last, only volatility timing kept economic value. That is VOLM-1's family,
  which had no power on the S&P 500 (t 1.27), and crypto has fewer years.
- **Paired BTC and ETH sessions** (a 2025 study, hourly 2016-2025, holdout 2021-2025). This is the hour-of-day family
  dropped above, and only the months after its holdout would be fresh.

**Checked on 2026-11-09, 06:30 UTC, and dropped before building.**

| Idea | Why it was dropped |
|---|---|
| Price pressure around the crypto perpetuals' funding times (00:00, 08:00 and 16:00 UTC) | No study measures returns around them. Without one it is the hour-of-day family dropped above, and its gross edge would face the same 0.02-0.06% round trip |
| The European closing-auction reversal. Auctions are 40-55% of the day's volume on the FTSE, DAX and CAC, and about 14% of a stock's auction return reverses overnight | Measured on single stocks, not the index. An index CFD is quoted off the futures after the cash close, so it never carries the cash index's auction distortion |
| The end-of-day reversal across US stocks (Soebhag, Baltussen & Da; second at the 2025 Quantpedia Awards): intraday losers rebound in the last 30 minutes | 3.78-6.86 bp a day gross for the long-short quintiles, 1993-2019. Two single-stock CFD legs at 3-5 bp each leave between −6.2 and +0.9 bp a day. At the index level the same window shows momentum instead, which IX-2 and FT-1 found too small for a CFD's spread |

**Checked on 2026-11-09, 09:30 UTC (a search for 2025-2026 work on index futures, gold and crypto), and dropped.**
The FX reports had closed FX first (`docs/FX_MISSION_REPORT.md`, `docs/FX_TARGET_REPORT.md`).

| Idea | Why it was dropped |
|---|---|
| A trend-momentum regime signal in gold futures, walk-forward 2015-2025 ("Forecast-to-Fill", arXiv 2511.08571, 2025) | Its own figures cannot coexist: a Sharpe ratio of 2.88 and 43% a year, with a worst fall of 0.52% in ten years. That points to an error or a leak. It assumes 0.7 bp of cost and is not peer-reviewed. Gold's slow trend rules were checked before (about t 2.7 at full strength) |
| Intraday lead-lag across liquid ETFs from lagged cross-sectional returns (a 2025 *Management Science* paper) | Profitable at an institutional ETF's costs on minute bars of many ETFs, which this project does not have. The index-CFD intraday record (IX-2, FT-1) shows edges of this kind below a CFD's round trip |
| Exchange flows of USDT and BTC as intraday signals (arXiv 2411.06327) | No result net of fees. The flow data is sold by private providers, so it cannot be reproduced here |
| Spot-BTC ETF flows as a daily signal (since 2024) | The flows follow price and are predicted by volume (NYDIG: R² above 70%). The one backtest that beat holding starts in 2024 and charges no fees |

**Checked on 2026-11-09, 10:30 UTC, and dropped before building: the options-expiration calendar.**

| Idea | Why it was dropped |
|---|---|
| Holding the US 500 in the week of monthly options expiration (Stivers & Sun: large caps +0.45% a week in expiration weeks against +0.12% otherwise, 1996-2008; the S&P 500 only from 1983) | On the years after their sample (2009-2026, 216 expiration weeks), even the full +0.33% gap gives about t 1.9 against a bar near 3.4. Holding only those weeks, mostly the market's own drift, reaches about t 3.0 at full size. Practitioner backtests report it has weakened since. Twelve weeks a year is not frequent trading either |
| The week after expiration (a partial reversal), triple-witching weeks, the Santa Claus rally, the first trading days of a year | A short sale or a handful of events a year: weaker still in power. The holiday eves were PHD-1 (t 0.82) |

**Checked on 2026-11-09, 11:30 UTC (work published from mid-2026), and dropped before building.**

| Idea | Why it was dropped |
|---|---|
| The noise-area intraday breakout adapted to Nasdaq-100 futures (2026) | The family dropped this morning. The adaptation's own threshold was chosen on its development data |
| Calendar seasonality in commodity futures by regression and singular spectrum analysis (arXiv 2609.12227, September 2026) | By its own account the effect's strength and value differ across markets and specifications. No out-of-sample figures could be read here. A CFD account quotes only a few commodities, and one seasonal signal a month per commodity has little power |
| AI-assisted replications of nine published equity anomalies (a July 2026 roundup) | None survived out of sample, and the one apparent survivor was a construction error, as this registry keeps finding |

**Checked on 2026-11-09, 12:30 UTC, and dropped before building.**

| Idea | Why it was dropped |
|---|---|
| Retail-broker client positioning as a contrarian signal (the share of a broker's clients long the US 500 or gold, read against them) | No study has tested it: only the broker's own marketing and user-made scripts, with no performance record. No history of the data is public here. A forward record would mean scraping a broker's site daily. COT-1's institutional positioning had no information either |

**Checked on 2026-11-09, 13:30 UTC, and dropped before building (power and earlier verdicts, no new data needed).**

| Idea | Why it was dropped |
|---|---|
| The US 500 inside and outside companies' share-buyback blackout windows (the weeks before earnings, when buybacks stop) | Four windows a year: about 60 in 15 years. Even a large gap between them cannot reach a bar near 3.4 |
| Flows from volatility-targeting funds: holding or avoiding the indices after volatility spikes, when such funds cut exposure | It is the return-to-volatility relation VOLM-1 already measured (alpha t 1.27 over 1995-2021). The same data cannot carry it again |

**Checked on 2026-11-09, 17:30 UTC (the discovery program: `docs/DISCOVERY_PROGRAM.md`), and dropped before building.**

| Idea | Why it was dropped |
|---|---|
| XAS-1: past bond returns as a timing signal for the index CFDs (Pitkäjärvi, Suominen & Vaittinen, JFE 2020) | What it would add to TRND-1 is a Sharpe ratio of about 0.1-0.2: about t 1.2 over 60 years, on index data already read |
| MAX-1: lottery demand in the crypto cross-section | The published signs disagree (negative in Grobys & Junttila 2021, positive in Özdamar et al. 2021), and a CFD broker quotes few coins |
| CMEG-1: bitcoin reverting toward the CME Friday settlement after a weekend move | No study, only lore. It needs about +0.9% an event over about 100 long-only events |
| OFI-1: order-flow imbalance in bitcoin, hourly | About 2 bp a trade gross against 5-10 bp of a CFD's cost: the lesson of ID-2, IX-2 and FT-1 |
| ATT-1: Wikipedia attention and next-week bitcoin returns | About 114 high-attention weeks at about 9% weekly volatility need a gap of about 2.8% a week |
| STB-1: stablecoin issuance and later bitcoin returns | The published tests found no effect on later returns (Economics Letters 2018), and mints follow rallies |
| FCI-1: holding the indices only while financial conditions are easy (NFCI) | A crash filter: six to eight crises in any sample, no power, as with the crash filters dropped on 2026-11-06 |
| EVT-1: drift in natural gas after the weekly storage report | The reaction is immediate and does not revert (Halova et al. 2014), or partly reverses the next week (Ederington et al.). The announcement-day premium is kept as INV-1, for a power check |

**Checked on 2026-11-16, 00:00 UTC (the edge hunt's pre-checks), and dropped before building.** Each is in
`research/inventions.jsonl` with its reason in full.

| Idea | Why it was dropped |
|---|---|
| TRND-1's rule on bitcoin and ether CFDs | Time-series momentum already failed on them (XTS-1, 2018-2024); the unread 2024-07..2026-10 is 28 months whose path the designer knows; t 3.0 there needs more than 11% a month |
| CALM-1: the long-only basket without leverage-stressed coins | Power: about +0.18% a week in the weeks stress occurs, t about 1.5 over the fresh window |
| US-hours clientele in bitcoin | A session effect: a closed family |
| Post-FOMC drift into gold | About 143 meetings: t 3.0 needs 0.8% a meeting, the mechanism gives 0.3-0.5% |
| Bitcoin's weekend move and Monday's index session | About 350 Mondays: it needs a continuation of 0.17% a Monday after the Sunday open |
| Passive capture of the unpriced funding | It holds perpetuals across a payment: outside the Islamic condition |
| Buying after a token unlock | The published unlock studies (Keyrock, Tokenomist; search results only) find the decline continues after the unlock; the schedules are paid data |
| INV-1: the natural gas storage-report premium | Power and costs: about 0.1% a report day against 0.53% needed over the unread years, and a CFD's round trip would take it |

**Checked on 2026-11-16, 05:00 UTC (after SPL-1), and dropped before building.** Each is in `research/inventions.jsonl`.

| Idea | Why it was dropped |
|---|---|
| Fading large four-hour rallies in BTC and ETH (CFD short) | Rallies of the size that reversed are rare in them: about 150 entries would need 0.8% a day |
| Altcoin froth as a signal against BTC and ETH | A two-coin time series: it needs a daily predictive correlation near 0.12 |
| The rally-avoidance overlay on a spot basket | It earns only on an altcoin basket held outright (none is); at 8% it fails the cost gate |
| ETH against BTC after ether's rallies | About 70 events would need 0.9% each |
| Buying spot-led falls in large coins | +0.51% gross is 2.5 round trips at best: the cost gate |
| Shorting altcoin CFDs on the short-side findings | Not among the owner's stated instruments; ten coins have no power on the unread window |

**Checked on 2026-11-16, 07:50 UTC, and dropped before building.** Each is in `research/inventions.jsonl`.

| Idea | Why it was dropped |
|---|---|
| Shorting BTC and ETH CFDs after forced deleveraging | LIQ-1's own events: bitcoin +0.05% (t 0.07) over the next day; no continuation to sell |
| FADE-1: volatility-scaled rally fades in BTC and ETH | About -0.3% a day expected against 0.6% needed |
| OIL-1: last month's oil move and the index CFDs (Driesprong, Jacobsen & Maat 2008) | Spent in-sample by the literature; 2004-2026 gives t about 2.0 at the published strength |
| CBP-1: the Coinbase premium and the next hours | No sign fixed by the mechanism; about 0.27% per eight hours needed against a 0.1% round trip |

**Checked on 2026-11-16, 14:05 UTC (the owner's edge mission: `docs/EDGE_MISSION_2026-11-16.md`), and dropped
before building.** Sixteen hypotheses were written from first principles; none passed its pre-checks. Each is in
`research/inventions.jsonl`. PROP (the challenge fee against TRND-1's pass rate) is a business asymmetry, recorded in
the mission document only.

| Idea | Why it was dropped |
|---|---|
| PDL-1: forced closure at a perpetual's delisting | A probe of recorded file names: 18 settled delistings 2022-2026, about 10 a side once signed by funding |
| ETF-NAV: creation pressure in the ETFs' benchmark hour | A closed family (fixes; hour-of-day effects) |
| Candle-boundary orders of rule-based bots | A closed family (intraday price patterns) |
| MSTR issuance and its earnings blackouts | About 50 blackout weeks need about 3.8% a week |
| EMIT: emission-driven selling, long-only | 1.5-2% a month needed over about 70 months; literature unsettled |
| PAIR-1: new fiat and stablecoin pairs | Contrary evidence: access effects front-loaded and reverted within weeks |
| GXR-1: gold after US equity panic days | Prior art (Baur & Lucey 2010), sign not fixed, about 1.8% an event needed |
| Buyback blackout windows and the US 500 | About t 2.0 at a plausible 3-5 bp a day |
| Equity futures financing spread as leverage demand | A persistent signal with few episodes; noisy free data |
| Central-bank gold purchases | About 300 lagged months |
| On-chain fee spikes | About 100 events, two signs |
| Protocol revenue and buyback yield | 36-60 months, few tokens |
| Leveraged-ETF rebalancing at the daily horizon | No free history of their assets; the daily reversal was judged |
| NE-ON-SF: the overnight premium without financing | A forward test earns about t 0.3 a year |
| ALT-CALM: the alt basket without its post-rally coins | Its return is the alt market's; the excess needs a short |

**Checked on 2026-11-16, 16:49 UTC (the edge hunt), and dropped before building.** Each is in
`research/inventions.jsonl`.

| Idea | Why it was dropped |
|---|---|
| ETF-FLOW-1: the ETFs' creations and the next day's bitcoin | A 694-day study found a next-day correlation of 0.09 (t about 2.4 on all the history there is) |
| SGEP-1: the Shanghai premium and London gold | Prior art with a weak result (LBMA Alchemist 83, 2005-2016); about 1.1% a month needed over 2016-2026 |

**Checked on 2026-11-21, 19:56 UTC (the idea engine's first five survivors), and dropped before building.** The
engine (free models, `research-data`) queued them between 17 and 20 November: each passed its critic and its power
gate at the Sharpe ratio its proposer claimed. A claimed Sharpe ratio is not evidence, so each was
checked against the record and the owner's conditions before any rule was written. None can be written in the lab's
rule language on a panel it holds.

| Idea | Why it was dropped |
|---|---|
| Central-bank gold purchases and physical delivery | Already dropped on 2026-11-16 (14:05) for power: the figures come one to two months late and about 300 months exist. A quarterly threshold makes it worse: central banks sold through 2009 and have bought since about 2010-2011 (the World Gold Council's yearly totals, from memory, not checked here), so the rule is long gold since then, a few regime switches rather than a test |
| The inflation-risk term premium in Treasuries | Treasuries pay interest: the owner's Islamic condition excludes interest-bearing instruments |
| International sector rotation after the US sectors | The US-listed international sector funds price at the same close as the US sectors, so no lag is left at the next open; the lag the mechanism needs is in foreign stocks, which the owner cannot trade. It needs a short, and the US sector lead-lag was dropped for power |
| A volatility sort of thirty country ETFs | The lab already classed rankings on past volatility on its 31 funds, eleven of them country funds (DLAB-ETF-D1: nothing above about 1 bp a day). Long-short, so it needs a short; the long-only side is market exposure (volatility-managed exposure is a closed family) |
| ETF premium and discount reversal across fifty ETFs | Needs each fund's daily NAV history, which no feed here carries (Yahoo has none). Liquid funds' premiums are a few basis points, below the round trip (2026-11-16: ETF-NAV). Long-short |

**Checked on 2026-11-22, 02:20 UTC (the original edge hunt, round 2: `docs/ORIGINAL_EDGE_HUNT_2.md`), and dropped
before building.** The owner asked on 2026-11-16 for twenty radically different hypotheses, scored, and the best
three tested. Three were chosen (rows 28 to 30). Five are dropped with the evidence; twelve wait (below). Each is in
`research/inventions.jsonl`.

| Idea | Why it was dropped |
|---|---|
| AIB-1: aggregate insider buying and the US 500 | Published (Seyhun 1988; Lakonishok & Lee 2001) and found not to forecast out of sample, 2004-2009 (the 2010 Financial Analysts Journal replication; search result) |
| MGN-1: exchange margin hikes as forced deleveraging | The closest test is negative: no price effect of margin increases in 16 commodity futures, 2000-2011, only more volatility that day (Hedegaard, AQR working paper; search result) |
| BWT-1: Brent against WTI under the Cushing constraint | A published strategy (Bollinger bands on the spread, 1992-2013): the owner excluded copies of published strategies |
| RBP-1: the rebalancing return | Known arithmetic of portfolios (Booth & Fama 1992; Willenbrock 2011), not a market's mistake to test |
| ANC-1: the 52-week-high anchor in the index | Published (Li & Yu 2012), monthly, and sensitive to the index used: little power at that horizon |

**Round 2's twelve that wait (2026-11-22): not built, and not failed.** As the owner set it, a hypothesis is not
failed for want of data. Each waits for what is written beside it (`docs/ORIGINAL_EDGE_HUNT_2.md`, section 6).

| Hypothesis | What it waits for |
|---|---|
| TGA-1: Treasury cash-balance drains and risk assets | Power: a daily information coefficient near 0.06 would be needed over 2015-2026 |
| HPS-1: miners' cash stress and bitcoin | **Dropped on 2026-11-23** (below): the panel of proof-of-work coins does not carry the mechanism, and bitcoin alone gives about one signal a year |
| JDR-1: Japanese index funds' dividend reinvestment | Power: two events a year |
| NGW-1: weekend weather forecasts and natural gas | Data: archived weekend model runs |
| AHP-1: the A-H premium and the H-share index | Power at the index level the owner can trade |
| PPS-1: platinum against palladium | Power: a handful of independent swings since 2000 |
| PAXG-1: tokenized gold while the gold market is shut | The owner's decision: gold is sealed from 2017, forward months included, until the seal has an end date |
| XST-1: tokenized stocks at the weekend | Power: trading since mid-2025, about ten names at weekends |
| AMM-1: concentrated-liquidity range exits | Data: an indexer or a node |
| ESQ-1: Ethereum's validator exit queue | Power and data: a handful of large queues; the sold fraction unobserved |
| PGL-1: South African load shedding and platinum | Its mechanism: no load shedding for over a year |
| CHL-1: China's price limits and Hong Kong the next day | Data: daily limit hits per stock |

**Checked on 2026-11-22, 04:55 UTC (the edge hunt), and dropped before building.** No edge-hunt experiment was
running or waiting for a stage (KRP-1 and SCX-1 FAILED; UDL-1, first in the backlog, waits for data), so the cycle
invented one. It is in `research/inventions.jsonl`.

| Idea | Why it was dropped |
|---|---|
| QTG-1: buy a coin when Binance removes its Seed or Monitoring Tag | Power. A tag puts a 90-day quiz between Binance's users and the coin (search results), so a removal reopens the largest venue's buyers. But there have been about 30 removals since 2023, and at a 10-day standard deviation near 15% against bitcoin, t 3.0 needs about +8% net over 10 days after a next-day entry: far more than an access friction plausibly leaves. No study was found; the news gives falls when a tag is added (a short-side signal, excluded for altcoins) and no figure for removals |

**Checked on 2026-11-22, 07:50 UTC (the edge hunt), and dropped before building.** Still no experiment running or
waiting for a stage, so the cycle invented another. It is in `research/inventions.jsonl`.

| Idea | Why it was dropped |
|---|---|
| MSTR-1: long bitcoin in the weeks after Strategy announces a purchase | Known and contradicted: TD Cowen found its buying had minimal, statistically weak price effect; K33 found a dip after large announcements that reverses within days (search results). Power: t 3.0 needs +1.6% over three days on about 90 announcements, or a 3% difference between weeks at bitcoin's 9% weekly volatility. And bitcoin's 2020-2026 path is in the designer's training data: only a forward stage would be unseen, and none of a year or two can reach t 3.0 |

**Checked on 2026-11-22, 10:54 UTC (the edge hunt), and dropped before building.** No experiment running or waiting
for a stage. It is in `research/inventions.jsonl`.

| Idea | Why it was dropped |
|---|---|
| LPB-1: BNB around Binance's Launchpool announcements, the dated demand of users who lock BNB to farm | Contradicted and underpowered: a practitioner analysis (Odaily) finds no rise after recent announcements, often a slight fall (search result); about 100 events at a 7-day standard deviation near 6% against bitcoin need +1.8% net an event for t 3.0 after a next-day entry. The farming rewards are a yield for locking a coin, not a price edge |

**Checked on 2026-11-22, 13:48 UTC (the edge hunt), and dropped before building.** No experiment running or waiting
for a stage. It is in `research/inventions.jsonl`.

| Idea | Why it was dropped |
|---|---|
| UWD-1: record Upbit's investment-warning flags forward, buy the coin on Binance after a designation or its lifting | Power and sign: a year of recording gives some 20 to 30 designations of coins Binance lists, and at a 10-day standard deviation near 25% t 3.0 needs a +15% to +20% rebound a trade after a next-day entry. The news shows the fall at the designation itself (June 2021: 25 warned, 5 delisted, Maro down more than 70%) and nothing systematic after it (search results); many designated coins are delisted next |

**Checked on 2026-11-22, 19:49 UTC (the edge hunt), and dropped before building.** No experiment running or waiting
for a stage; UDL-1, first in the backlog, waits for the owner's word. It is in `research/inventions.jsonl`.

| Idea | Why it was dropped |
|---|---|
| SGC-1: the HK50 index CFD while Southbound Stock Connect is shut for mainland holidays (the largest net buyer absent) | Power: the net buying is about 0.01% of Hong Kong's market value a day, so even five times that a four-day closure moves the index about 0.2%, while some 35 closures since 2020 need about +1.8% each for t 3.0. The news is mixed and the flow turned to net selling in 2026 (search results) |

**Checked on 2026-11-22, 22:49 UTC (the edge hunt), and dropped before building.** No experiment running or waiting
for a stage; UDL-1 waits for the owner's word. It is in `research/inventions.jsonl`.

| Idea | Why it was dropped |
|---|---|
| TQB-1: long bitcoin into the quarter-ends when Tether books 15% of its profits into bitcoin | Not dated: Tether accumulates through the quarter and moves the coins to its reserve wallet at the end (search result), so the quarter-end is a transfer, not market buying. And about 13 quarter-ends need +4% each for t 3.0, on a path the designer has seen |

**Checked on 2026-11-23, 01:49 UTC (the edge hunt), and dropped before building.** No experiment running or waiting
for a stage; UDL-1 waits for the owner's word, so the cycle took HPS-1 from round 2's waiting list, whose note said
what was to be checked. It is in `research/inventions.jsonl`.

| Idea | Why it was dropped |
|---|---|
| HPS-1: buying bitcoin after miners' capitulation, with a panel of proof-of-work coins for power | The hash-ribbon evidence is bitcoin's alone and its promoter's own (nine signals, hypothetical); no altcoin study; the free tier's altcoin hash rates unconfirmed (search results). The panel's hash rates move with miners switching between coins of one algorithm and with merge-mining, not with cash stress, so they add events without the mechanism; bitcoin alone gives about one signal a year |

**Checked on 2026-11-23, 04:50 UTC (the edge hunt), and dropped before building.** No experiment running or waiting
for a stage; UDL-1 waits for the owner's word. It is in `research/inventions.jsonl`.

| Idea | Why it was dropped |
|---|---|
| LXR-1: a bitcoin CFD in the day's direction into the US close, when the 2x bitcoin ETFs must rebalance | Power and known: the mechanism is published for equities, BITX rebalances in CME futures where basis traders spread it (search results), and some $240 million on a 4% day plausibly moves bitcoin 5 to 15 bp against the 24 bp t 3.0 needs on about 100 days; only a forward stage would be unseen, most of a decade long |

**The cadence from 2026-11-09, 13:30 UTC.** The published ideas for these instruments are exhausted, and hourly
searches were repeating dropped families. The check-ins now run twice a day, at 11:26 and 23:26 UTC. The second
follows the trend desk's nightly session, so each report carries its real net. Each still takes one research step.

**A known gap, left as it is.** `research_status.json` feeds the dashboard's research line, and it dates from 2026-10-08.
It does not read the single-script programs. Regenerated now, its top line would still be "NO EDGE — DO NOT TRADE",
which stays true for trading, because nothing is promoted. But it would list TRND-1 as FAILED, for lack of a reader.
It waits for the owner's decision about TRND-1.

**The owner's answer (2026-11-07):** the $200K account is a funded (prop-firm) account. Everything is on paper
first: "we want to make sure". TRND-1 is therefore followed forward on paper under a funded account's rules:
FUNDED-P (`docs/FUNDED_PAPER.md`, `scripts/funded_paper.py`). It has two tracks, half and full size, and is
recomputed from 2026-11-09 after each weekday's closes. The report is on the `funded-paper-data` branch. No
broker, no bot change.

**Live, on fresh forward data, judged at fixed dates:**

- THE TREND DESK (from 2026-11-09; the owner, 2026-11-08: "النظام يتداول من وحده انتهى"). The system trades
  TRND-1 by itself on its own $200,000 paper account (`TRND1-PAPER-200K`), with FUNDED-P's HALF size and one-day
  stop. Every order and stop move goes through the risk engine, the hard gate and the paper broker
  (`docs/TREND_DESK.md`; trend-desk-1.0.0). It runs after each weekday's closes, and its report is on
  `trend-desk-data`. It is a paper record, read as it grows; TRND-F judges the rule itself. Promoted for PAPER in
  `models/artifacts/promoted_rules.json`. Its own code replayed on 2004-2026 (descriptive, on data already judged):
  +3.4% a year on average, 6 losing years in 22, no account failed. The replay found three faults before the first
  session, all fixed (trend-desk-1.1.0, hard-gate-1.4.0; `docs/TREND_DESK.md`).

- FUNDED-P (from 2026-11-09): see the owner's answer above. Not judged: a paper record, read as it grows. Its HALF
  track carries a one-day stop at 6% (funded-paper-1.1.0, added before the first day). Without it, 1987-10-19
  alone ended 547 of 732 replayed runs.
- THE TRINITY DESK (from 2026-11-23; the owner, 2026-11-21: "read CLAUDE_HANDOFF_SPEC.md and implement it in
  full"). The owner's TRINITY-MASTER on its own $200,000 paper account, EXPERIMENTAL: unvalidated, so the risk
  engine sizes it at 0.25% a position, and it never reaches DEMO or live (`docs/TRINITY.md`; trinity-desk-1.0.0;
  report on `trinity-desk-data`). Not judged: a paper record, read as it grows, with the package's own weights
  measured beside it (the design book). The package's 20-year figures were tested on real prices first and did
  not hold as stated: on the spec's own 15-day rebalance t 1.55 to 4.78 by starting day, every drawdown above
  10%, and a fixed mix of its average weights at a higher median t (`research/results/TRINITY-MASTER-redteam.json`).
- CONF-1 (do the H1 agreements the confidence floor refuses pay?): LEARNING **FAILED** (run 2026-11-21, due
  2026-11-20): 739 agreements, mean -0.044 R, t -0.90, days' t -0.53. The floor stays; EVALUATION is not judged
  (`research/preregistrations/CONF-1.md`, Result).
- TRND-F (registered 2026-11-06): TRND-1's rule, unchanged, on the four index CFDs over the months December 2026
  to November 2029, which did not exist when the rule was chosen. It is judged once, on or after 2029-12-03
  (`research/preregistrations/TRND-F.md`), and needs nothing until then. It is recorded whatever the owner
  decides about TRND-1 as a paper strategy.

- THE PERFORMANCE CYCLE (from 2026-11-15; the owner's order of 2026-11-13). Both paper systems are audited every
  three hours by `.github/workflows/perf-cycle.yml`: every figure recomputed by a second route, realized apart from
  unrealized, the radar's loss attributed, its frozen rules replayed with five declared variants on its own stored
  quotes, and the best on the earlier half judged on the later half only (`docs/PERFORMANCE_ENGINEERING.md`; report
  on `perf-data`). No challenger is registered: RADX-1 failed, and a variant is proposed only after thirty days on
  the judging part. Nothing in either system is changed by it.

**Done:**
- SPL-1 FAILED (2026-11-16): buying spot after a four-hour rise of 8% led by spot lost 1.45% net over 24 hours (6,378 trades, t -5.21), 15% lost 2.37% (t -4.65); rises the perpetual led fell as far. Large rallies reversed within a day: the short side again.

- BAS-1 FAILED, as registered (2026-11-15; dev 2021-01 to 2025-02): coins with high funding lost 1.04% a week against the seasoned market (3,372 entries, t -2.24; median -3.87%). With SQZ-1 and CASC-1: a coin under leverage stress of either sign underperforms for days to weeks; the information is on the short side, which the Islamic condition excludes for altcoins (`research/results/BAS-1-verdict.md`).
- CASC-1 FAILED, as registered (2026-11-15; dev 2023-07 to 2025-02): after a four-hour fall of at least 8% with the perpetual at least 0.5% below spot, spot lost a further 1.85% net over 24 hours (326 trades, t -2.07), while falls led by spot ended flat: the forced selling continued (`research/results/CASC-1-verdict.md`).
- SQZ-1 FAILED, as registered (2026-11-15; dev 2021-2023-06 on GitHub's runner): buying the spot of a coin whose perpetual's shorts were crowded (funding at most -0.03% per 8 hours over 72 hours) and holding seven days lost 1.52% a week against the seasoned market (1,248 entries, t -1.94); -0.33% at -0.05% (653, t -0.29); at -0.1%, 260 entries, too few. Medians -2.3% and -2.6%, 37-38% positive; the same coins did better on days their shorts were not crowded. Crowded shorts were mostly right (`research/results/SQZ-1-verdict.md`). Spot bought outright: the first candidate built to the owner's Islamic condition.
- EXF-1 FAILED, as registered (2026-11-15; dev 2021-2023 on GitHub's runner): the side the previous funding rate says receives the payment, held from five minutes before a settlement to five after, lost after two 10 bp fills at every threshold: -11.9 bp a trade at 0.05% (30,824 trades, t -7.4), -8.5 at 0.1% (t -3.1), -10.0 at 0.2% (t -1.6), -20.3 at 0.5% (t -2.5). The mechanism is measurable: the premium passes on 26% to 62% of the payment, rising with its size and almost all after the settlement, but the index moves with it and the price takes back 40% to 100% of what the trade receives; the 8 to 11 bp left before fills is less than two taker fills. No later stage is registered (`research/results/EXF-1-verdict.md`).
- NEWL-1 FAILED, as registered (2026-11-15; judged once on GitHub's runner): 812 listings entered 2021-01 to 2026-09, in 67 monthly cohorts, earned -0.105% each net of funding and four 15 bp fills (t -0.01 against 3.0; 95% interval -18% to +18%). Six of seven gates failed; only "one day late" held. The median event earned +15.7% and 71% were positive, but the rule had no stop: 29 events lost more than their notional, and one squeeze (COAIUSDT, 2025-09: -166 notional units, most of it funding) outweighed all the gains. Random seasoned contracts did as well in 48% of 1,000 placebos. NEWL-1-F is not registered (it followed only a pass, and as frozen it could not have reached its own 18-month minimum); the 812 events are spent for any rule about new listings; no successor is registered (`research/results/NEWL-1-verdict.md`).
- RADX-1 FAILED, as registered (2026-11-14; a diagnosis of RADAR-1's paper ledger, not a strategy). Stated from the
  122 positions opened before 2026-10-30 11:00 UTC and computed once on the 88 opened after. P1 held: the 41 later
  positions opened on a trailing spread under 50% a year lost 27.5 bp each (t -6.45, 21 of 22 coins negative),
  against 27.6 bp in the design part. P2 did not: the 15 later positions opened within six hours after the same
  coin's exit for a decayed spread lost 17.7 bp (t -1.36 against -3.0). Both were required. By the
  preregistration's own rule no challenger follows from it. The later positions outside both classes averaged
  -10.6 bp: the diagnosis locates most of the loss and shows a profit nowhere. RADAR-1 is read on 2026-12-06 as
  registered.
- DLAB-CRD-D1 and DLAB-ETF-D1, directed tests and not judged edges, proposed nothing for validation. The lab wrote
  both submissions from its coverage map and registered and ran them by itself on GitHub's schedule (run 7 of
  `lab-cycle.yml`, 2026-11-13 21:35 UTC). Perpetuals: 14 rankings on past returns, volatility, the volatility ratio
  and the size of the last move; 3 positive and not told from noise (the best at t 1.38), 11 lost (4 of them only
  after costs); 12 more refused before any test as cross-coin momentum. Funds: 12 rankings; 2 positive and not told
  from noise (the best at t 1.19), 3 duplicates, 7 lost; 2 refused as the funds' momentum. Both maps now have no
  hole. The aggregate of the weak positives planned for each panel was withdrawn by the director before it was
  submitted (`research/director/log.jsonl`): its expected t on unread rows is about 0.5 against a bar of 3.0.
- DLAB-ENG-1, a discovery scan and not a judged edge, proposed nothing for validation. Eight years of fit rows and eight of check rows on WTI and natural gas (1994-2011): 2,015 statistics looked at, 102 rules kept and classed. None was promising; 25 were positive on the check rows but not told from noise (the best at t 1.43), each with a written plan; 43 lost on the check rows, 21 were overfit, 11 had too few rows, 2 were duplicates. Its validation window (2012-2024) was never loaded and stays unread.
- DLAB-ETF-1, a discovery scan and not a judged edge, proposed nothing for validation. It is the first experiment the lab's worker registered and ran by itself on GitHub's runner (run 1 of `lab-cycle.yml`, 2026-11-12). Thirty-one US-listed funds by day, eight years of fit rows (2007-2014) and five of check rows (2015-2019): 15,349 statistics looked at, 266 rules kept and classed. None was promising; 49 were positive on the check rows but not told from noise (the best at t 1.70: every fund held five days while dispersion across the funds is low), each with a written plan; 102 lost on the check rows, 55 of them only after costs; 78 were overfit, 19 had too few rows, 18 were duplicates. The rules' check-row t are centred at -0.56: the average rule lost after costs. Its validation window (2020 on) was never loaded and stays unread; its bar there would have been 3.17.
- DLAB-CRD-1, a discovery scan and not a judged edge, proposed nothing for validation. The worker's second run (run 2 of `lab-cycle.yml`, 2026-11-12). Fifty-five Binance perpetuals by day with their funding, 791 fit rows (2020-05 to 2022-06) and 731 check rows (2022-07 to 2024-06): 29,218 statistics looked at, 266 rules kept and classed. None was promising, although twelve places in its batch would have cost the bar nothing; 69 were positive on the check rows but not told from noise (the best at t 2.76, one coin's reversal after a shock, which is what the best of 174 distinct behaviours looks like by chance); 72 lost on the check rows, 48 of them only after costs; 60 were overfit, 28 had too few rows, 19 were duplicates, and 18 were recognised by what they do as closed families (funding carry, single-coin momentum). A limit of the scan, found by reading its evidence: 22 of its 24 cross-sectional places went to rankings on funding, the strongest on the fit rows and a closed family; no ranking on past returns or on volatility reached the check rows. Those are not yet looked at out of sample on this panel. Its validation window (2024-07 on) was never loaded and stays unread.
- LIQ-1 FAILED at stage 1 (development, 2020-12..2023-12), on six of seven gates. Buying BTCUSDT or ETHUSDT for 24 hours after an hour whose open interest and price both fell below their trailing 90-day 1st percentile lost -0.63% a trade net over 83 trades (week-clustered t -1.06; BTC +0.05%, ETH -1.66%). By year: 2021 +2.29%, 2022 -2.95%, 2023 -0.06%. The entries did no better than matched random ones (74% of 2,000 random books did as well), and the mean was negative before costs too. Stage 2 is not registered and its 2024-2026 data stay unfetched.
- ENG-1 FAILED, on t, top year and bootstrap. Holding WTI, heating oil, RBOB and natural gas only while contract 2 was above contract 3 earned +2.48% a year net over 1985-2018 (t 2.09 against 3.0, Sharpe 0.36, worst fall 26%). Development t 1.76, validation t 1.13. The slope carried real information: it beat 99.7% of 2,000 books with the long months shuffled, and it beat holding always by +1.4% a year (t 1.08). But the premium is small, it halved after 2002, and a month's delay erased it (t 0.66). The holdout stays sealed; the family is closed on these data.
- DAY-1 FAILED, on t alone: the 2-day RSI pullback in an uptrend (Connors & Alvarez 2009) on the four index CFDs earned +1.81% a year on its basket, 1990..2020 (t 2.48 against 3.3879). 69.6% of its 941 trades won, +0.24% a trade net. Its profit was in 1990-2005 (t 3.02); after 2006 it was nearly gone (t 0.49), the decay that follows publication. The holdout stays sealed.
- TRND-1 PASSED and VALIDATED, the first in this registry. Owning the S&P 500 only above its 10-month average earned +0.509% a month net in price, 1929-1989 (t 3.83 against 3.376), with a worst fall of 51% against holding's 86%. The holdout (the four index CFDs, 2021-01..2026-09) earned +0.785% a month, with a worst fall of 11% against 22%. It is not an edge: month by month it earned slightly less than holding, and its whole lead over 1929-1989 came in the 1930s. It reached the bar the power ceiling says a plain long position cannot, with the same premium at about half the spread and over twice the years. Proposed to the owner as a paper strategy; on their word (2026-11-08) the trend desk trades it by itself on paper, from 2026-11-09.
- RBL-1 FAILED: trading the S&P 500 against the 60/40 drift from T-4 to T+1 earned +0.26% a month, 2003-2018 (t 1.57 against 3.180). The short months lost 0.29% (t -2.14) and the long months earned 1.06% (t 3.16, 2008 much of it): the market rose around month-end either way, which fits the turn-of-the-month effect better than the rebalancing reversal.
- TME-1 FAILED, on t alone: IEF over each month's last three trading days earned +0.106% net per month-end, 2003-2018 (t 2.24 against 3.078). Development, validation, costs x2 and top year all passed. Before the spread and the markup it was +0.194% (t 4.07), against +0.015% on other three-day holds: the published effect was there, and a retail CFD's costs took half of it. The holdout stays sealed.
- TSY-1 FAILED: short IEF before each 10-year auction and long after earned -0.017% net per event, 2009-2020 (t -0.16). Gross, the cycle was still there in direction, about 0.1% each side at t about 1.4, but a CFD's costs of about 0.22% per event took all of it.
- LVOL-1 FAILED: half SPLV, half USMV earned an alpha of +0.9% a year on the S&P 500 at its 0.70 beta, 2012-2020 (t 0.44 against 3.154). Positive to 2016, not after. The runner's commit was refused by GitHub, so the verdict is recorded from its job log; the program is not run again.
- EMC-1 FAILED: the top 3 of 6 emerging currencies by policy-rate differential lost 0.63% a year over 2005-2019 (t -0.19). The +6.7% differential was eaten by -4.8% of depreciation and the CFD's costs. Positive to 2012, negative after.
- PHD-1 FAILED: the S&P 500 on a holiday's eve earned +0.053% net (236 events, 1995-2021, t 0.82), and beat ordinary days by +0.065% (t 0.98). 1999 supplied 71% of the total.
- SEC-1 FAILED: the top 3 of 9 US sectors by six-month return lost 0.53% a year to all nine over 2000-2017 (t -0.31). It was positive to 2008 (t 0.93), negative after (t -1.58).
- GSR-1 FAILED, every gate: the gold/silver pair against a two-sigma ratio lost 1.2% a year over 2002-2019 (t -0.31), in 19 trades. One trade against the 2010-11 silver run lost 40%.
- VOLM-1 FAILED, on t alone: volatility-managed S&P 500 exposure earned an alpha of +2.6% a year over 1995-2021 (t 1.27 against 3.113). It was positive in both halves and with costs doubled, and its drawdown was -50% against the market's -65%. A real but weak effect the bar cannot confirm.
- XSM-1 FAILED: among the 20 largest coins, the top 4 by 21-day return beat the 20 by +0.22% a week, 2018-10..2024-06, at t 0.48 against 3.144: positive to 2021, negative from 2022.
- FOMC-1A FAILED: the pre-FOMC drift earned +0.07% net per event, 2016-2021, at t 0.81 against 3.163. Ordinary weeks did better in the same window. FOMC-1 was abandoned before any outcome (its one-runner fetch could not finish).
- CONF-2 ABANDONED (2026-11-05, before any outcome was read). The senior approved none of the 52 agreements it judged in shadow, so its approved group could not fill. The reviews stopped to save the owner's money.
- VRP-1 FAILED (short VIX futures in contango: +61% a year at t 2.33 against 3.0; the filter added nothing, t 0.46; drawdown −77%).
- XTS-1 FAILED (crypto time-series momentum: t 2.87 against 3.09; timing t 1.87).
- MEH-1 FAILED (month-end hedge flows: +3.3 bps gross, +1.2 net, t 1.04 against 3.61).
- FND-1 was ABANDONED before any outcome; FND-1A FAILED (crowded funding: the timing was negative).
