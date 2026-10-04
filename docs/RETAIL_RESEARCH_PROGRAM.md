# Retail-CFD research program (RC): diagnosis and design

Written and committed **before** any RC result was computed. It starts from commit `4818934`.
The question is no longer "does a signal predict price". It is: **does a retail CFD account make
money trading it, after spread, commission, slippage, overnight financing and dividends, without
leverage doing the work?**

## A. Why everything so far failed (from the committed records)

| # | Dimension | What the records show | Source |
|---|---|---|---|
| 1 | SMC / price action | Archive SMC grades and H2 variants failed. The full multi-agent system lost −0.07R per trade (t −2.9). Every price-only H1 rule had a gross expectancy within ±0.03R of zero. | registry `archive-smc-*`, PR-001, DP-001 |
| 2 | M15 execution with H1/H4 context | The M15 scanner architecture (boosted stumps, H1/H4 context, walked forward) failed. At M15 a round trip costs 0.1–0.2R. | WF-003 |
| 3 | Calendar / fix flow | FLOW-1 failed 4 of 4. The London 4 p.m. fade had zero gross effect (+0.06 bps). The Tokyo post-fix effect was +2.46 bps gross (t 2.27) against about 1.8 bps of retail costs. | FLOW-1 |
| 4 | Trend following | FX D1 trend (CP-001), regime-conditioned trend (R2D) and multi-asset ETF trend (DIV-1) all failed. | CP-001, R2D, DIV-1 |
| 5 | Diversified trend | Real and large in 1990–2007 (t 4.3–4.4). Since 2008, a Sharpe of about 0.1 over 226 months; the holdout t was 0.26. | DIV-2, DIV-2-H |
| 6 | Financing / leverage | DIV-1: financing the 3.5× exposure that volatility targeting needs was **86%** of all costs (7.6% a year). DIV-2 at retail CFD financing: −7.3% a year (2008–2020) and −5.7% (2021+). | DIV-1 diagnosis, DIV-2 |
| 7 | Transaction costs | 0.09–0.21R per H1 trade and about 0.10R per D1 trade, larger than every gross edge measured. The live risk check had under-counted costs (fixed in risk-1.1.0). | EDGE_MISSION_REPORT §2 |
| 8 | Turnover | Thousands of intraday trades, each paying about 0.1R. DIV-1's blend flipped 866 times. | LOSS-FORENSICS, DIV-1 |
| 9 | Stop-loss placement | A stop twice as wide would have won 24.8% of the R lost on H1. But the median winner went −0.40R first: stops sit inside noise because there is no edge. Widening them is curve-fitting. | LOSS-FORENSICS |
| 10 | Take-profit construction | Trades that reached +1R and then lost were only 6–8% of the R lost. Exits are not the problem. | LOSS-FORENSICS |
| 11 | Direction accuracy | On D1, 30% of the R lost was WRONG_DIRECTION and 35% NORMAL_VARIANCE. Gross expectancy is about zero: direction is a coin flip on FX majors at these horizons. | LOSS-FORENSICS, DP-001/002 |
| 12 | Regime dependence | Trend worked before 2008 and not after. The only positive FX legs (D1 short trend) came from one episode, the 2014–15 USD rally. | DIV-2, CP-001 |
| 13 | Asset selection | Everything until DIV-1 traded seven FX majors, the most efficient and most studied market there is. Trend's pre-2008 return came from diversification across equity, FX, bonds and commodities. | DIV-2 by-class contribution |
| 14 | Signal decay | Trend's Sharpe fell from ≈ 1.0 to ≈ 0.1. The fix effects are about the size of a retail round trip. | DIV-2, FLOW-1 |
| 15 | Implementation assumptions | The cost under-count was fixed, and the hour-00 tick gap documented. H.10 is used only after publication. No LLM forecast can be backtested honestly (its training data contains the future). | FINAL_ENGINEERING_AUDIT addendum |

## What a surviving strategy must therefore look like

1. **Its gross edge per trade must be large relative to the round trip.** That means few decisions
   on daily or slower data, not hundreds of intraday trades.
2. **It must not hold notional it is not paid for.** An index CFD charges about benchmark + 2.5% a
   year on every unit held, long or short, which is about 0.7 bp a day on the markup alone. A
   position must expect more than that per day it is held. Rules that are in the market only when
   the expected return is concentrated (the turn of the month, the days after a sharp fall) fit
   this; a permanently invested trend or beta book does not.
3. **It must not depend on leverage.** CFD leverage scales price, costs and financing together.
   It changes the drawdown, never the Sharpe.
4. **It must still work after 2008.** Every gate below includes 2009–2020 separately.
5. **Its mechanism must differ from forecasting FX-major direction**, which is exhausted
   (carry, momentum, value, reversal, breakout, pullback, COT, flows, rate news, cross-asset).
6. **It must be checked on data nobody here has used.** Every clean time period is spent or
   sealed, so RC-EQ seals a universe of 16 indices never loaded by this project (universe B).

## B. The program: two preregistered studies

### RC-EQ: equity-index CFDs (research/preregistrations/RC-EQ.md)

Seven hypotheses, judged on 10 indices (universe A) over 1990–2020. Only hypotheses that pass
every gate face universe B, once.

| ID | Family (user list) | Mechanism | Turnover |
|---|---|---|---|
| E1 TOM | calendar flow (low-turnover D1) | Month-end pension and payroll flows: index returns concentrate in days −1..+3 (Ariel 1987; Lakonishok & Smidt 1988; McConnell & Xu 2008) | 12 round trips a year per index; ~20% of days held |
| E2 DIP | robust mean reversion | Liquidity provision: short-horizon index reversal after volatility-scaled falls (negative short-lag autocorrelation of index returns since the 2000s) | entries only after ≥ 1σ 5-day falls |
| E3 XSMOM | cross-asset relative strength | Country-index momentum (Asness, Moskowitz & Pedersen 2013), long-short top/bottom 3 | monthly |
| E4 REGIME | regime system | Faber (2007) 10-month moving-average timing | monthly |
| E5 VOLMAN | volatility / risk premia | Volatility-managed exposure (Moreira & Muir 2017), capped at 1.5× | monthly |
| E6 BREAKOUT | breakout | Long-only Donchian channel (100-close high in, 50-close low out) | event-driven, low |
| E7 ENSEMBLE | multi-strategy | The mean of E1–E6's targets in one account (offsetting trades net out). Defined now, not chosen after results | |

### RC-FX: the two FX questions not yet asked (research/preregistrations/RC-FX.md)

| ID | Family | Why it is new |
|---|---|---|
| X1 COMPOSITE | carry + momentum + value | Each component failed alone (RV-1, XS-001, R2A, R3). Their **combination** was never tested: value and momentum are negatively correlated, which is the documented reason the combination works when the parts are weak. Monthly; real BIS policy rates for carry and for swaps |
| X2 COT-FILTER | COT as a low-frequency filter | COT-1 tested positioning as a one-week trigger. X2 asks only whether removing trend positions that leveraged funds already crowd improves monthly trend. Measured as value added over the unfiltered rule |

### Families considered and not tested, with the reason

| Family | Why not |
|---|---|
| Carry alone | Already failed (RV-1-S2 net t −0.01; R2A; R3). It enters RC-FX only inside X1 |
| Volatility compression → expansion, Donchian on FX | Already failed on FX (SL-001-01/02/05/06) |
| FX trend, FX momentum, FX reversal, rate news, oil–CAD | Already failed (CP-001, R2D, XS-001, RV-1, R2B, R2C, R4) |
| Relative-value pairs | No economic anchor in this universe; a pair search is the data-mining the brief forbids |
| Pre-FOMC drift | Documented decay after publication (2015); about 8 events a year cannot reach significance |
| Commodity CFDs (oil, gas, softs) | No roll-adjusted futures history is reachable; Yahoo's continuous `=F` series contain roll gaps that are not returns. **Data-limited** |
| AI enhancement | Deferred until a deterministic candidate exists to enhance (priority 10). An LLM forecast cannot be backtested: its training data contains the outcome |

## C. The retail cost model (aitrader/research/discovery/retail.py, retail-1.0.0)

| Item | Index CFD | FX CFD |
|---|---|---|
| Spread | 2 bps (US500, NAS100, GER40, UK100, FRA40, JPN225, AUS200, EU50); 5 bps (HK50, CAN60, SWI20, US2000, ESP35, NETH25, SWE30, ITA40); 10 bps (others) | ECN raw: EUR 0.2, AUD 0.3, JPY 0.3, GBP/NZD/CAD/CHF 0.5 pips |
| Commission | none (spread-only) | 0.7 pip per round trip (the risk engine's value) |
| Slippage | 1 bp per fill | 0.1 pip per fill (the risk engine's value) |
| Financing | long pays benchmark + 2.5%; short receives benchmark − 2.5%; per calendar day, /360 | rate differential − 1.5% markup on notional; per calendar day, /365 |
| Dividends | long receives **nothing** on price-return indices (conservative); short pays 3% a year; total-return series (US500 = S&P 500 TR, GER40 = DAX) include them | none |
| Benchmark | BIS policy rate of the index's currency, public at the close; national rates before the euro | BIS policy rates |
| Not held | where the rate is unknown or stale (> 7 days), or above 25% (hyperinflation) | same |
| Costs ×2 | every assumption doubled: spread, slippage, commission, both markups | same |

**What is not modelled, declared.**

- **Currency translation.** Index P&L is in the index's own currency.
- **Margin calls.** Positions are at most 1× (1.5× for E5) of equity.
- **Constant-weight drift.** Positions are notional fractions of equity reset each day without
  charge; the drift trades this ignores are second order at these turnovers.
- **The Japanese policy rate.** It is absent from the BIS series in 1999-02 → 2000-08,
  2001-03 → 2006-03 and 2013-04 → 2016-09 (zero-rate and QE years). JPN225 and JPY are therefore
  not held then. Nothing is substituted.

## D. Discipline

- Every rule, parameter, neighbourhood grid, gate and threshold is frozen in the spec files
  before data is fetched (RC-EQ) or read (RC-FX).
- Universe A is never loaded after 2020-12-31. The 2021–2026 period that DIV-2-H opened is
  **not used** by RC-EQ.
- Universe B and the fx-majors 2017+ holdout open once, only for hypotheses that pass every gate.
- No result is re-run with other parameters. A rejected family is not tweaked.
