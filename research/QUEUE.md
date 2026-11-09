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
- CONF-1 (do the H1 agreements the confidence floor refuses pay?), on 2026-11-20 and 2026-11-27. It costs
  nothing.
- TRND-F (registered 2026-11-06): TRND-1's rule, unchanged, on the four index CFDs over the months December 2026
  to November 2029, which did not exist when the rule was chosen. It is judged once, on or after 2029-12-03
  (`research/preregistrations/TRND-F.md`), and needs nothing until then. It is recorded whatever the owner
  decides about TRND-1 as a paper strategy.

**Done:**
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
