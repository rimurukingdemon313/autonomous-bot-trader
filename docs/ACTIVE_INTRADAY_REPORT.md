# Active intraday trading: the opportunity engine (ID-2), final report

## Verdict: NO EDGE

**Every configuration was rejected.** The engine is a scanner that weighs every family of market
information and trades only when its estimated net expectancy is positive.

- Of the 30 preregistered tests (18 engine configurations and 12 simple rules) and 3 random
  controls, **nothing passed the development gates.** Validation (2014–2016) was therefore never
  computed. The untouched 2017+ period stays sealed.

**What the engine did find:**

- **It ranks real information.** Its selections beat matched random entries by Welch t 3–7 at every
  scale.
- **The gross information is larger than any simple rule's** (+0.10 to +0.19R a trade against
  −0.06 to +0.02R) **and about the same size as the costs** (0.10–0.13R).
- **The five positive configurations net +0.04 to +0.09R a trade with t 0.7–1.6.** That is below the
  promotion bar (t ≥ 2.0). It is also about what the best of 18 tries would show by chance.

**Most of the ranking is cost avoidance, not direction.**

- A model given only the cost-to-stop ratio ranks better than the full model (IC 0.28 against
  0.18 at M5).
- Every directional family on its own (momentum, reversion, breakout, structure, liquidity/SMC,
  session, higher timeframes, cross-market) ranks with IC ≤ 0.07, and its best decile still loses.

**Liquidity/SMC added no information** in any form tested:

- as a rule;
- against matched random;
- as part of the model: dropping it changed nothing.

**Memory of resolved trades added no information.**

**Nothing was integrated into live trading,** because nothing survived. The live system stays as it
was: DEMO/PAPER only, the Edge Engine abstains, and the Risk Engine stays the final authority.

## Sources

| Item | Path |
|---|---|
| Preregistration, frozen and committed (`ee4a633`) before any outcome | `research/preregistrations/ID-2.md` (spec `4b3aa7ef…`, 30 tests, validation t ≥ 3.5524) |
| Results | `research/knowledge/ID-2.json`; registry verdict FAILED; `research/results/id2-run.log` |
| Code | `aitrader/research/discovery/opportunity.py` (opp-1.0.0), `scripts/id2.py` |
| Tests | `tests/unit/test_opportunity.py`: 17 behaviour tests, plus 6 mutation checks |
| Reproduce | `python scripts/id2.py run` (refuses: ID-2 has a verdict). The design is deterministic: the code and spec hashes are checked before every stage |

## A. What was tested

| | |
|---|---|
| Instruments | EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD, XAUUSD. M5 bid/ask built from Dukascopy ticks |
| Development | data 2009–2013; **judged on 2011, 2012 and 2013, each predicted out of sample** by models refitted each January on trades that had already exited |
| Candidates | Every M5 bar 07:00–19:55 UTC, both sides: **3.05M per exit scale.** The risk engine's own entry checks refuse 1.23M of them at S5, 232k at S15 and 9.9k at S60 |
| Standard trade | Next-bar entry on the correct side of the quote; stop 1.5 × ATR; target 2R; flat by 20:55 UTC; no overnight exposure |
| Exit scales | **S5** (M5 ATR, at most 4 h); **S15** (M15 ATR, 8 h); **S60** (H1 ATR, 12 h) |
| Costs | Measured spread, 0.7 pip commission per round trip, 0.1 pip slippage per market fill (provisional against TradeLocker) |
| Account | The production limits: 3 open positions, 1 per instrument, 2 per currency, and a daily stop at −4R (2% at 0.5% risk) |
| Engine | 58 inputs: 13 groups (below). Two model families, ridge and depth-3 boosted trees. Trade only if estimated net R > τ, with τ = 0, 0.05 or 0.10 |
| Rules | MOM (momentum), MR (mean reversion), BRK (breakout), SWEEP (liquidity sweep fade): the same template and portfolio |
| Controls | Random entry, one per instrument-day. A matched random for every test (same count and hours, random side), 3 seeds each |

**Feature groups:**

| Group | Features |
|---|---|
| momentum | 1/3/12/48-bar moves, 12-bar z |
| reversion | distance from EMA 20 and EMA 100 |
| breakout | range position, 20-bar break, failed breakout, room to the 288-bar extremes |
| structure | swing trend, BOS, CHoCH, distance to swings |
| liquidity / SMC | PDH/PDL, Asian and equal-level sweeps, BOS+FVG, order block, distance to PDH/PDL |
| volatility | ATR and Bollinger-width ranks, ATR ratio, bar range and body |
| cost | round-trip cost / stop |
| session | hour, weekday, session opens |
| mtf | H1/H4 trend of completed bars, prior day's return and range position, H1-scaled moves |
| cross-market | USD-index z, relative strength, correlation, AUDJPY risk-on/off |
| volume | tick activity |
| memory | the last 50 resolved trades on each side, the last 60 in the same hour |
| identity | side, instrument |

**Not repeated, and why** (preregistration §"Why this is not a repeat"):

- ID-1's single M5 rules, DP-001/SL-002's linear and stump models on H1/M15, and the daily TOM,
  carry, COT, flow and diversified-trend programs had all failed.
- ID-2 changes the formulation: every bar is a candidate, all families feed one estimate, there is
  a new interaction-capable model family, larger exit scales, memory features and portfolio
  limits.
- The rules were re-run only as **baselines** through the identical template.

## B–J. Results: development 2011–2013 out of sample (every test)

**How to read the table:**

- **R** is net of every cost, per trade.
- **Gross** is mid-to-mid.
- **Net return** is summed without compounding at 0.5% risk per trade: below −100% the account is
  gone.
- **"3M prof."** is the share of the 34 rolling 3-month windows that were profitable. **"Wk prof."**
  is the share of 157 weeks.
- **"vs rand"** is the Welch t against matched random entries.
- **Hold** is the median holding time.

| Test | Trades | /month | Win | Avg win | Avg loss | Gross | Cost | **Net R** | t | PF | Net return | Max DD | 3M prof. | Wk prof. | vs rand | Hold | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M-trees-S5-τ0.10 | 550 | 15.3 | 41.1% | +1.61 | −0.97 | +0.191 | 0.103 | **+0.087** | 1.39 | 1.15 | +24.1% | 13.5% | 62% | 40% | 4.23 | 50 min | NO EDGE (t) |
| M-ridge-S15-τ0.10 | 476 | 13.2 | 41.2% | +1.59 | −0.98 | +0.177 | 0.100 | **+0.077** | 1.13 | 1.13 | +18.3% | 9.7% | 56% | 38% | 3.09 | 35 min | NO EDGE (t, instruments) |
| M-ridge-S15-τ0.05 | 1,475 | 41.0 | 41.8% | +1.46 | −0.96 | +0.145 | 0.091 | **+0.054** | 1.56 | 1.10 | +39.6% | 10.2% | 79% | 54% | 5.37 | 85 min | NO EDGE (t, PF, instruments) |
| M-trees-S5-τ0.05 | 1,690 | 46.9 | 40.2% | +1.60 | −1.00 | +0.157 | 0.113 | **+0.044** | 1.32 | 1.07 | +37.1% | 25.8% | 74% | 50% | 5.74 | 48 min | NO EDGE (t, PF, instruments) |
| M-ridge-S5-τ0.10 | 614 | 17.1 | 40.4% | +1.56 | −0.99 | +0.153 | 0.113 | **+0.040** | 0.66 | 1.07 | +12.3% | 13.8% | 50% | 39% | 2.64 | 30 min | NO EDGE |
| M-ridge-S60-τ0.10 | 253 | 7.0 | 42.3% | +1.27 | −0.88 | +0.104 | 0.075 | **+0.029** | 0.37 | 1.06 | +3.7% | 6.2% | 59% | 31% | 1.55 | 125 min | NO EDGE |
| M-ridge-S5-τ0.05 | 1,326 | 36.8 | 38.6% | +1.60 | −1.00 | +0.120 | 0.117 | **+0.003** | 0.08 | 1.01 | +2.0% | 25.6% | 50% | 46% | 3.62 | 35 min | NO EDGE |
| M-trees-S15-τ0.05 | 2,910 | 80.8 | 39.6% | +1.49 | −0.97 | +0.103 | 0.102 | **+0.001** | 0.05 | 1.00 | +2.0% | 33.3% | 50% | 49% | 4.70 | 100 min | NO EDGE |
| M-trees-S60-τ0.05 | 2,700 | 75.0 | 41.8% | +1.23 | −0.88 | +0.077 | 0.078 | **−0.001** | −0.04 | 1.00 | −1.3% | 33.5% | 59% | 49% | 2.67 | 215 min | NO EDGE |
| M-trees-S5-τ0.00 | 4,478 | 124.4 | 38.6% | +1.61 | −1.02 | +0.122 | 0.125 | **−0.003** | −0.12 | 1.00 | −5.6% | 46.5% | 59% | 50% | 6.98 | 45 min | NO EDGE |
| M-trees-S60-τ0.10 | 1,115 | 31.0 | 42.1% | +1.21 | −0.89 | +0.072 | 0.076 | **−0.003** | −0.08 | 0.99 | −1.7% | 29.7% | 41% | 43% | 2.86 | 260 min | NO EDGE |
| M-ridge-S60-τ0.05 | 1,558 | 43.3 | 43.1% | +1.06 | −0.81 | +0.061 | 0.065 | **−0.005** | −0.15 | 0.99 | −3.6% | 24.0% | 59% | 48% | 2.74 | 155 min | NO EDGE |
| M-ridge-S15-τ0.00 | 4,534 | 125.9 | 39.2% | +1.46 | −0.97 | +0.080 | 0.094 | **−0.015** | −0.70 | 0.98 | −33.1% | 50.6% | 47% | 45% | 5.40 | 95 min | NO EDGE |
| M-trees-S15-τ0.10 | 1,007 | 28.0 | 39.2% | +1.45 | −0.97 | +0.082 | 0.102 | **−0.020** | −0.46 | 0.97 | −10.3% | 28.1% | 53% | 42% | 3.38 | 110 min | NO EDGE |
| M-ridge-S60-τ0.00 | 4,089 | 113.6 | 41.0% | +1.18 | −0.86 | +0.047 | 0.070 | **−0.023** | −1.21 | 0.95 | −47.5% | 62.1% | 44% | 50% | 4.22 | 190 min | NO EDGE |
| M-trees-S15-τ0.00 | 5,688 | 158.0 | 38.1% | +1.52 | −0.98 | +0.079 | 0.107 | **−0.028** | −1.53 | 0.95 | −80.6% | 88.1% | 29% | 40% | 5.21 | 90 min | NO EDGE |
| M-ridge-S5-τ0.00 | 3,776 | 104.9 | 37.6% | +1.62 | −1.02 | +0.098 | 0.127 | **−0.029** | −1.22 | 0.96 | −54.4% | 79.7% | 29% | 41% | 6.07 | 40 min | NO EDGE |
| M-trees-S60-τ0.00 | 4,415 | 122.6 | 39.9% | +1.22 | −0.87 | +0.042 | 0.081 | **−0.038** | −2.05 | 0.93 | −84.4% | 112.3% | 32% | 44% | 1.78 | 200 min | NO EDGE |
| R-BRK-S60 | 4,758 | 132.1 | 37.2% | +1.28 | −0.88 | +0.015 | 0.090 | **−0.075** | −4.15 | 0.86 | −179% | 182% | 9% | 38% | 1.51 | 185 min | NO EDGE |
| R-MR-S60 | 4,480 | 124.4 | 38.8% | +1.20 | −0.91 | +0.002 | 0.091 | **−0.089** | −4.82 | 0.84 | −199% | 208% | 0% | 37% | −0.00 | 195 min | NO EDGE |
| R-MOM-S60 | 4,251 | 118.1 | 36.1% | +1.33 | −0.89 | −0.004 | 0.088 | **−0.092** | −4.61 | 0.84 | −196% | 206% | 3% | 30% | −0.04 | 175 min | NO EDGE |
| R-SWEEP-S60 | 4,529 | 125.8 | 37.5% | +1.24 | −0.91 | −0.003 | 0.098 | **−0.101** | −5.72 | 0.82 | −229% | 230% | 6% | 30% | −1.31 | 190 min | NO EDGE |
| R-MOM-S15 | 5,838 | 162.1 | 34.3% | +1.54 | −0.99 | +0.004 | 0.126 | **−0.121** | −6.83 | 0.81 | −354% | 359% | 0% | 26% | 0.78 | 80 min | NO EDGE |
| R-SWEEP-S15 | 6,988 | 194.1 | 34.3% | +1.53 | −1.01 | +0.015 | 0.148 | **−0.134** | −9.00 | 0.80 | −468% | 468% | 0% | 25% | −0.04 | 75 min | NO EDGE |
| R-MR-S15 | 6,884 | 191.2 | 35.1% | +1.47 | −1.01 | +0.002 | 0.137 | **−0.135** | −8.55 | 0.79 | −465% | 480% | 0% | 24% | 0.13 | 75 min | NO EDGE |
| R-MOM-S5 | 7,216 | 200.4 | 33.6% | +1.62 | −1.04 | +0.011 | 0.155 | **−0.144** | −9.47 | 0.79 | −520% | 524% | 0% | 25% | 2.31 | 40 min | NO EDGE |
| R-BRK-S15 | 7,552 | 209.7 | 32.9% | +1.55 | −1.01 | −0.027 | 0.139 | **−0.166** | −11.19 | 0.75 | −628% | 628% | 0% | 19% | −1.46 | 70 min | NO EDGE |
| R-SWEEP-S5 | 7,456 | 207.1 | 32.9% | +1.62 | −1.05 | +0.003 | 0.174 | **−0.171** | −12.05 | 0.76 | −639% | 639% | 0% | 17% | −0.43 | 35 min | NO EDGE |
| R-MR-S5 | 8,043 | 223.4 | 32.9% | +1.62 | −1.05 | −0.004 | 0.167 | **−0.172** | −11.85 | 0.76 | −690% | 691% | 0% | 15% | 0.16 | 35 min | NO EDGE |
| R-BRK-S5 | 9,574 | 265.9 | 30.2% | +1.65 | −1.05 | −0.064 | 0.171 | **−0.235** | −22.22 | 0.68 | −1123% | 1125% | 0% | 6% | −3.42 | 35 min | NO EDGE |
| *control* RANDOM-S60 | 9,880 | 274.4 | 38.7% | +1.10 | −0.83 | +0.010 | 0.095 | **−0.084** | −7.17 | 0.84 | −416% | 419% | 0% | — | — | — | control |
| *control* RANDOM-S15 | 12,608 | 350.1 | 35.0% | +1.32 | −0.95 | −0.011 | 0.143 | **−0.154** | −14.33 | 0.75 | −969% | 969% | 0% | — | — | — | control |
| *control* RANDOM-S5 | 14,044 | 390.0 | 32.8% | +1.50 | −1.03 | −0.014 | 0.188 | **−0.202** | −19.04 | 0.71 | −1418% | 1419% | 0% | — | — | — | control |

**Rule notes.** The rule rows use the primary parameters. SWEEP is the A1/A2/A3 liquidity sweeps
faded. The brackets name the failed promotion gates of the four best configurations. Only
M-trees-S5-τ0.10 failed on t alone. Every gate result for every test is in `ID-2.json`; the
artifact stores numpy booleans as the strings "True"/"False".

**Cost of a trade, by scale (random entries):** 0.19R at S5, 0.14R at S15, 0.09R at S60.

**Frequency** is an output, as required:

- the engine took **7 to 158 trades a month** across 8 instruments, depending on τ and scale;
- **the binding account limit was the currency rule.** All 8 instruments contain USD, and the
  production risk engine allows at most 2 open positions sharing a currency. No configuration
  ever held more than 2 positions, and the 3-position limit was never reached.
- This rule shapes the results: a third, simultaneous USD trade was always refused. A universe
  with non-USD crosses would let the engine hold up to 3.

**The three best configurations in detail** (all failed promotion on t):

| | M-trees-S5-τ0.10 | M-ridge-S15-τ0.05 | M-trees-S5-τ0.05 |
|---|---|---|---|
| Net R by year 2011 / 2012 / 2013 | +0.045 / +0.075 / +0.170 | +0.068 / +0.091 / +0.016 | +0.020 / +0.124 / +0.032 |
| BUY / SELL net R | +0.131 / +0.032 | +0.075 / +0.019 | +0.057 / +0.029 |
| Instruments net positive (≥ 30 trades) | EURUSD +0.19, XAUUSD +0.21, AUDUSD +0.03 (3 of 5) | EURUSD +0.21, XAUUSD +0.09, USDCHF +0.08 (3 of 7) | EURUSD +0.10, XAUUSD +0.13, AUDUSD +0.18 (3 of 7) |
| Instruments net negative | GBPUSD −0.07, USDCHF −0.11 (also below 30 trades: USDJPY −0.17, NZDUSD −0.35; USDCAD +0.32) | GBPUSD −0.04, USDJPY −0.06, USDCAD −0.22, AUDUSD −0.11 | GBPUSD −0.06, USDJPY −0.10, USDCAD −0.12, USDCHF −0.04 |
| Volatility regime: high / low | +0.075 (539) / +0.685 (11) | +0.054 (1,362) / +0.041 (110) | +0.033 (1,643) / +0.419 (45) |
| Trend regime: trending / ranging | +0.213 (164) / +0.034 (386) | +0.061 (474) / +0.052 (1,000) | +0.098 (407) / +0.027 (1,283) |
| Weeks profitable; worst / best week at 0.5% | 40%; −4.8% / +5.0% | 54%; −5.4% / +6.2% | 50%; −7.9% / +11.0% |
| 1-month windows: profitable, median, worst | 64%, +0.4%, −5.8% | 61%, +1.6%, −7.3% | 56%, +0.4%, −10.9% |
| 3-month windows: profitable, median, worst, best | 62%, +2.0%, −5.8%, +15.5% | 79%, +4.0%, −4.8%, +18.1% | 74%, +3.9%, −17.9%, +27.3% |
| 6-month windows: profitable, median, worst | 77%, +6.0%, −5.5% | 90%, +7.6%, −4.6% | 87%, +8.9%, −8.6% |
| Net return / max DD at 0.25% · 0.5% · 1% risk | +12 / 6.8 · +24 / 13.5 · +48 / 27.0 | +20 / 5.1 · +40 / 10.2 · +79 / 20.5 | +19 / 12.9 · +37 / 25.8 · +74 / 51.6 |
| Costs × 1.25: net R (t) | +0.055 (0.87) | +0.038 (1.08) | +0.020 (0.58) |
| Sharpe (daily, annualised) | 0.79 | 0.88 | 0.75 |
| Median / p90 hold | 50 / 240 min | 85 / 380 min | 48 / 230 min |

**Reading these honestly:**

1. **Profit is narrow.** It comes from the cheapest instruments relative to their volatility,
   EURUSD and XAUUSD. GBPUSD and USDJPY lose in every one of the three. The preregistered gate
   that ≥ 60% of instruments (those with ≥ 30 trades) be positive failed for M-ridge-S15-τ0.05 and
   M-trees-S5-τ0.05 (3 of 7). M-trees-S5-τ0.10 passed it at exactly 3 of 5, because two losing
   instruments had fewer than 30 trades.
2. **The low-volatility cells are too small to mean anything** (11 and 45 trades).
3. **The best of 18 configurations shows t ≤ 1.6, which is what chance alone often produces.**
   The registry's Bonferroni threshold for this family is t ≥ 3.55. The preregistered promotion
   bar is t ≥ 2.0.

## K. Rolling 3-month results

Every row of the table has its 3-month share profitable; the three best are detailed above.

- The engine at τ ≥ 0.05 had **50–79% of 3-month windows profitable**, with medians up to +4% at
  0.5% risk.
- Simple rules and random entries had **0–9%.**

That is the clearest sign that the engine's selection is not random. It is also a 3-year sample
with 34 overlapping windows, which is too few to separate a weak edge from luck.

## L. Robustness

The full battery was preregistered for promoted tests only, and nothing was promoted. What was
computed for every test:

| Check | Result |
|---|---|
| Costs × 1.25 | The positive engine configurations keep +0.02 to +0.06R at t ≤ 1.1. Every one at τ = 0 turns more negative |
| Instruments | 3 of 7, 3 of 7 and 3 of 5 instruments positive for the best three (needs ≥ 60%); the gate failed for every positive configuration except M-trees-S5-τ0.10 |
| Direction | Both sides are positive in all three, with BUY ahead (+0.06 to +0.13R against +0.02 to +0.03R) |
| Concentration | Profits are spread, but the totals are near zero. The "top 10% of trades" share is 2–4× the total, which is what a near-zero total produces |
| Neighbours | The ridge S5 and S15 results rise with τ, as a working ranking should. Trees S15 do not (τ0.10 < τ0.05), and neither do trees S60: the trees' top estimates are noisy |

The parameter-perturbation, ×1.5 / ×2 cost, slippage-stress and independent-period tests were
**not run**, by the frozen design: they apply only after promotion. Running them now would
judge a non-candidate on data reserved for a candidate.

## M. Out-of-sample results

**All development figures are already out of sample:** each year 2011–2013 was predicted by a model
fitted only on trades that had exited before that year.

**The independent out-of-sample stages were not reached:**

- **Validation 2014–2016:** never computed (no promotion).
- **Holdout 2017-01 → 2022-07:** sealed; its M5 bars were never built.

Both remain unspent for a future, better-founded candidate.

## N. Which market concepts added predictive value

**Ablations (descriptive, development out of sample).** IC is the Spearman rank correlation between
the estimate and realised net R over every tradable candidate. "Top" is the realised net R of the
estimate's top decile.

| Group | M5 ridge: drop it (IC / top) | M5 ridge: it alone (IC / top) | M5 trees: drop it (IC / top) | M15 ridge: it alone (IC / top) | H1 ridge: it alone (IC / top) |
|---|---|---|---|---|---|
| **full model** | 0.178 / −0.056 | — | 0.177 / −0.045 | full 0.179 / −0.053 | full 0.108 / −0.044 |
| **cost** (round trip / stop) | **0.118 / −0.068** | **0.281 / −0.091** | **0.111 / −0.056** | **0.265 / −0.072** | **0.192 / −0.041** |
| volatility | 0.177 / −0.056 | 0.145 / −0.130 | 0.175 / −0.043 | 0.061 / −0.106 | 0.067 / −0.069 |
| volume (ticks) | 0.178 / −0.059 | 0.098 / −0.138 | 0.177 / −0.039 | 0.019 / −0.120 | 0.010 / −0.078 |
| breakout | 0.185 / −0.061 | 0.068 / −0.141 | 0.183 / −0.049 | 0.027 / −0.112 | 0.007 / −0.097 |
| identity (side, instrument) | 0.181 / −0.059 | 0.069 / −0.143 | 0.179 / −0.043 | 0.124 / −0.086 | 0.040 / −0.043 |
| memory (resolved trades) | 0.178 / −0.062 | 0.062 / −0.139 | 0.174 / −0.045 | 0.061 / −0.126 | 0.026 / −0.075 |
| liquidity / SMC | 0.181 / −0.061 | 0.046 / −0.153 | 0.179 / −0.047 | 0.022 / −0.129 | 0.007 / −0.096 |
| structure (BOS, CHoCH, swings) | 0.184 / −0.064 | 0.019 / −0.127 | 0.177 / −0.050 | 0.023 / −0.114 | 0.021 / −0.071 |
| momentum | 0.189 / −0.060 | 0.018 / −0.131 | 0.179 / −0.048 | 0.020 / −0.117 | 0.019 / −0.074 |
| reversion | 0.178 / −0.054 | 0.010 / −0.162 | 0.178 / −0.046 | 0.015 / −0.123 | 0.015 / −0.073 |
| mtf (H1/H4, prior day) | 0.184 / −0.062 | 0.005 / −0.171 | 0.177 / −0.048 | 0.009 / −0.132 | 0.010 / −0.069 |
| session | 0.181 / −0.057 | −0.004 / −0.198 | 0.177 / −0.050 | −0.044 / −0.143 | 0.082 / −0.093 |
| cross-market | 0.184 / −0.052 | −0.013 / −0.155 | 0.174 / −0.048 | 0.021 / −0.143 | 0.018 / −0.093 |

**What these numbers say:**

1. **The only input whose removal hurts is cost.** Removing it cuts the M5 IC by about 40%. On its
   own it ranks better than everything together.
   - Much of the engine's "intelligence" is the arithmetic that a trade with a wide stop relative
     to its spread loses less.
   - At H1, the cost-only model's best decile (−0.041R) is as good as the full model's (−0.044R).
2. **No directional family carries information on its own:** IC ≤ 0.07 at every scale, and every
   one's best decile loses 0.07–0.20R a trade. The few cases that rank at all are volatility
   (0.145) and tick activity (0.098) at M5; they partly measure cost too.
3. **Together, the non-cost inputs add about +0.035R to the M5 top decile:** the full model's
   −0.056R against cost-only −0.091R. That is the real, directional part of what the engine
   found. It is a quarter of a trade's cost.
4. **Decile shape.** Realised net R rises monotonically with the estimate at every scale. In the
   M5 trees model it climbs from −0.282R in the lowest decile to −0.045R in the highest.
   - The estimate is well ordered.
   - Even its best tenth of all candidates loses money.
   - The positive selections come from the top 1–10%, where the samples are smallest.

## O. Did liquidity/SMC help, hurt, or add nothing?

**It added nothing measurable, in every form tested:**

- **As a rule.** The sweep fade nets −0.171R at S5, −0.134R at S15 and −0.101R at S60, with gross
  −0.003 to +0.015R. It is no better than matched random at any scale (Welch t −0.43, −0.04,
  −1.31).
- **As model inputs.** Dropping the liquidity/SMC group leaves the ranking unchanged (M5 trees IC
  0.177 → 0.179). On its own it ranks at IC 0.046 at M5 and 0.007 at H1.
- **Structure** (BOS, CHoCH, swings) is the same: drop 0.177 → 0.177; alone 0.019.

This repeats ID-1 under a different formulation (larger stops, combined with context, portfolio
limits). Sweeps, BOS, CHoCH, FVG and order blocks carry no short-term directional information in
these 8 instruments, 2011–2013, that random entries with the same stops and hours lack.

## P. Did "AI" improve decisions compared with deterministic signals?

**Language model: not tested, and it cannot be tested historically.** Its training data contains
what happened next (as in DP/RC). The engine instead emits a structured `Opportunity` record that
a future AI layer can read and **veto**, but never change:

- symbol, side or NO TRADE;
- expected R;
- entry, stop, target;
- maximum hold and the exit by 20:55;
- reasons;
- invalidation.

That layer can only be judged on forward (demo) data.

**Statistical model vs deterministic rules: yes, the model is better, but not good enough.**

| Scale | Best rule (gross / net) | Engine at τ = 0.05 (gross / net) | Difference |
|---|---|---|---|
| S5 | MOM +0.011 / −0.144 | trees +0.157 / +0.044 | **+0.15R gross**: real and significant against random (t 5.7) |
| S15 | MOM +0.004 / −0.121 | ridge +0.145 / +0.054 | **+0.14R** |
| S60 | BRK +0.015 / −0.075 | trees +0.077 / −0.001 | +0.06R |

**Learning from errors (memory):**

- Removing memory changes the M5 trees IC from 0.177 to 0.174. On its own, memory ranks at IC
  0.06.
- Recent outcomes of the same setup add no usable out-of-sample information beyond the current
  market state.
- The memory architecture is preserved and causal; the evidence does not justify giving it weight.

## Q. Exact production-readiness gaps

1. **No validated edge.** This is the blocking gap. Nothing passed development, so nothing may
   trade. The Edge Engine correctly abstains (the edge registry: 115 REJECTED, 2 PROMISING, 1
   VALIDATED long-horizon DIV-2, which retail financing makes unprofitable).
2. **The broker's real costs are unknown, and they decide everything here.**
   - Cost is the engine's strongest input, and its gross information (0.10–0.19R) is the size of
     the assumed costs (0.10–0.13R).
   - Every number above rests on Dukascopy 2009–2013 spreads plus 0.7 pip commission, not
     TradeLocker's.
   - The production spread recorder exists but has no history. **Months of recorded demo spreads
     by instrument and hour are the prerequisite for any further intraday research.** A
     cost-aware estimate is only as good as the cost it is given.
3. **Feature parity.** The engine's 58 inputs are computed offline from 8 synchronised M5 bid/ask
   series, including tick counts. Production would need the same feed and the same code path,
   with a parity test (live vs offline on the same bars).
4. **Model artifact.** The trees and ridge models are not serialised, hashed or versioned the way
   `research/knowledge` artifacts are. A validated model would need that, plus a model card, before
   any paper run.
5. **Exits.** Only the fixed template was tested (1.5 ATR stop, 2R, flat by 20:55). Break-even,
   trailing, partials and model-driven exits are untested for this engine.
6. **Wiring.** By design, nothing connects
   `Scanner → Opportunity → AI veto → Risk Engine → Execution → TradeLocker` for this engine. The
   risk engine's account limits are mirrored in the simulation, not called. A candidate would be
   wired as a `Strategy` returning a priced setup, so that the risk engine still sizes and
   approves.
7. **Data limits.** Hour 00 UTC is missing for 7 pairs; XAUUSD starts in 2011-05. There is no index
   CFD intraday bid/ask history, and no data after 2016 has been built (by design).

## What the evidence supports next (no promise of profitability)

- **Do not trade any of this.**
- The only lever with evidence behind it is **cost**: the engine finds real selection information
  of about the same size as the assumed costs.
- Whether TradeLocker's actual spreads are lower or higher than Dukascopy's 2009–2013 spreads is
  unknown. It decides whether this information could ever be tradable.
- The honest next step is to **record demo spreads for several months**, then preregister a
  successor that uses the measured costs. That successor would be judged once on the still-unspent
  2014–2016 validation period, and then on the sealed 2017+ holdout.
- More features, more model families or lower thresholds on the same data would be curve-fitting:
  the 18 configurations already show where the information is.

**Bottom line:**

- The system can be **active**: the scanner and the engine propose and select 7–158 trades a
  month.
- It is **selective in the right direction**: realised R rises with the estimate.
- But on the evidence, **there is not yet a positive expected value after realistic costs to be
  active about.** Its correct output today is NO TRADE.
