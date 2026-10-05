# ID-1: is there an intraday M5 edge after realistic retail costs? Final report

**Overall verdict: NO EDGE.**

**Intraday M5 liquidity/SMC strategies do not have a reliable edge after realistic retail CFD
costs.** Neither do the price/volatility, cross-market and hybrid alternatives tested against
them.

- All 16 preregistered hypotheses lost money on the development period (2009–2013), from −0.095R
  to −0.187R per trade after costs.
- None reached the promotion gates, so validation (2014–2016) was **never computed** for any of
  them, by design.
- The untouched test period (fx-majors 2017-01 → 2022-07) **stays sealed**. Its M5 bars were
  never built.

## Sources

| Item | Path |
|---|---|
| Preregistration, frozen before any outcome | `research/preregistrations/ID-1.md` (spec `429a0b48…`, validation t threshold 3.48) |
| Results | `research/knowledge/ID-1.json` |
| Run log | `research/results/id1-run.log` |
| Code | `aitrader/research/discovery/intraday.py` (id-1.0.0), `scripts/id1.py` |
| Data | M5 bid/ask bars built from the FX-Data mirror of Dukascopy ticks, branch `id-data` |
| Registry | `ID-1` trial with its FAILED verdict |

**One operational note.** The first run was killed by a container restart while evaluating B4. It
had recorded no verdict and written no artifact. The identical frozen code was re-run, and its
first 12 result lines match the interrupted run byte for byte. The procedure is deterministic, so
nothing was re-tuned.

## Phase 1: infrastructure and data

**Reused:**

- the tick→bar aggregator and ingester (generalised to M5, M15 behaviour unchanged);
- `BarSeries`;
- the project's bid/ask fill conventions;
- the risk engine's cost constants and entry limits;
- BIS policy rates;
- the registry and holdout seals;
- `stats.welch_t`.

**Built:**

- an M5 simulator (structure stops, limit entries, session deadlines, gap exits, financing);
- 13 rule functions, 3 hybrids, random and matched-random controls;
- rolling 1/3/6-month window statistics;
- 31 tests (fills, cost decomposition, financing, risk checks, causality of every rule, planted
  effect).

**Data.**

- **Source.** The bulk Dukascopy datafeed throttles CI runners (107 of 120 requests failed,
  `research/results/id-probe.json`). So the bars came from the FX-Data mirror of Dukascopy ticks,
  which this project already used, now known to run to 2022-07.
- **Coverage.** 8 instruments × 2009-01 → 2016-12, about 575k bars each. XAUUSD from 2011-05.
  Hour 00 UTC is missing for every pair except EURUSD (a source defect; all rules enter
  07:00–20:00).
- **Index CFDs: data-limited.** No free intraday bid/ask index history was reachable in bulk.

## Results: development period 2009-01 → 2013-12 (every hypothesis and control)

**How to read the table.**

- R is net of every cost, per trade, in units of the actual initial risk.
- "Costs R" = spread + commission + slippage + financing.
- **Net return** is summed at 0.5% risk per trade, without compounding: a figure below −100%
  means the account is gone.
- "3M windows" is the share of rolling 3-month windows that were profitable.

| Strategy | Trades | Trades/month | Win rate | Avg win (R) | Avg loss (R) | PF | Gross R | Costs R | **Net R** | t | Net return, 0.5% risk | Max DD | 3M windows profitable | vs matched random (Welch t) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1-RANDOM | 5,897 | 98.3 | 32.6% | +1.57 | −1.03 | 0.74 | −0.008 | 0.171 | **−0.179** | −10.9 | −528.0% | 540.0% | 0% | — | control |
| E2-RANDOM-LONG | 5,817 | 97.0 | 33.6% | +1.57 | −1.03 | 0.77 | +0.013 | 0.168 | **−0.155** | −9.0 | −452.3% | 459.4% | 0% | — | control |
| E3-RANDOM-SHORT | 5,815 | 96.9 | 33.1% | +1.56 | −1.03 | 0.75 | −0.004 | 0.171 | **−0.174** | −10.2 | −506.7% | 508.6% | 0% | — | control |
| A1-SWEEP-PDHL | 3,512 | 58.5 | 33.7% | +1.61 | −1.04 | 0.79 | +0.019 | 0.164 | **−0.144** | −6.5 | −253.7% | 257.9% | 3% | 0.92 | NO EDGE |
| A2-SWEEP-ASIA | 3,058 | 51.0 | 33.3% | +1.62 | −1.05 | 0.77 | +0.014 | 0.177 | **−0.163** | −6.6 | −249.7% | 251.1% | 7% | 0.00 | NO EDGE |
| A3-SWEEP-EQUAL | 8,911 | 148.5 | 33.7% | +1.59 | −1.04 | 0.78 | +0.020 | 0.173 | **−0.153** | −10.9 | −682.5% | 687.0% | 0% | 1.49 | NO EDGE |
| A4-BOS-FVG | 1,514 | 25.2 | 33.8% | +1.75 | −1.04 | 0.85 | +0.072 | 0.175 | **−0.103** | −2.8 | −77.8% | 92.4% | 21% | 2.05 | NO EDGE |
| A5-CHOCH | 17,015 | 283.6 | 38.0% | +1.11 | −0.89 | 0.77 | +0.004 | 0.130 | **−0.126** | −13.7 | −1074.3% | 1074.3% | 0% | 1.02 | NO EDGE |
| A6-ORDER-BLOCK | 4,483 | 74.7 | 30.6% | +1.79 | −1.06 | 0.75 | −0.004 | 0.183 | **−0.187** | −9.0 | −419.1% | 427.6% | 5% | −0.02 | NO EDGE |
| B1-OPENING-RANGE | 6,930 | 115.5 | 38.4% | +1.21 | −0.92 | 0.82 | +0.020 | 0.121 | **−0.101** | −5.5 | −348.2% | 366.1% | 16% | 0.41 | NO EDGE |
| B2-SQUEEZE | 1,172 | 19.5 | 35.2% | +1.62 | −1.05 | 0.84 | +0.092 | 0.203 | **−0.111** | −2.8 | −65.0% | 71.2% | 22% | 2.37 | NO EDGE |
| B3-MOMENTUM | 17,394 | 289.9 | 34.7% | +1.38 | −0.98 | 0.75 | −0.011 | 0.151 | **−0.162** | −14.3 | −1412.5% | 1416.8% | 0% | 0.20 | NO EDGE |
| B4-MEAN-REVERSION | 14,799 | 246.7 | 36.3% | +1.39 | −1.02 | 0.78 | +0.025 | 0.168 | **−0.143** | −12.7 | −1062.0% | 1065.1% | 0% | 2.63 | NO EDGE |
| B5-FAILED-BREAKOUT | 17,787 | 296.5 | 32.5% | +1.61 | −1.05 | 0.74 | −0.007 | 0.179 | **−0.186** | −16.6 | −1650.4% | 1650.5% | 0% | −0.15 | NO EDGE |
| B6-SESSION-OPEN | 4,565 | 76.1 | 32.2% | +1.72 | −1.06 | 0.77 | +0.007 | 0.173 | **−0.165** | −6.5 | −377.4% | 387.1% | 2% | −0.50 | NO EDGE |
| C1-USD-LAG | 3,029 | 50.5 | 37.7% | +1.30 | −0.98 | 0.80 | +0.043 | 0.166 | **−0.123** | −5.5 | −186.0% | 193.4% | 7% | 2.87 | NO EDGE |
| D1-BEST-SWEEP+HIGH-VOL (A4 + vol) | 1,319 | 22.0 | 33.8% | +1.74 | −1.05 | 0.85 | +0.064 | 0.170 | **−0.106** | −2.7 | −69.6% | 81.1% | 21% | 1.73 | NO EDGE |
| D2-MOMENTUM+OVERLAP | 8,512 | 141.9 | 35.6% | +1.40 | −0.98 | 0.79 | +0.014 | 0.146 | **−0.132** | −8.1 | −563.1% | 567.4% | 2% | 2.42 | NO EDGE |
| D3-SQUEEZE+H1-TREND | 627 | 10.5 | 36.0% | +1.60 | −1.05 | 0.86 | +0.106 | 0.201 | **−0.095** | −1.8 | −29.7% | 37.2% | 33% | 2.19 | NO EDGE |

**Best strategy (the least bad):** D3 SQUEEZE + H1 TREND. Net −0.095R per trade, 627 trades,
33% of 3-month windows profitable. It has the highest gross expectancy (+0.106R) and the fewest
trades. It is still a loss of −29.7% over five years at 0.5% risk.

**3-month windows of the four highest-gross rules.**

| Rule | Profitable | Median 3M | Worst 3M | Best 3M |
|---|---|---|---|---|
| D3 | 33% | −1.6% | −10.2% | +6.3% |
| B2 | 22% | −3.4% | −11.3% | +2.9% |
| A4 | 21% | −4.2% | −15.6% | +6.9% |
| C1 | 7% | −9.9% | −21.4% | +13.6% |

**For most rules no 3-month window was profitable at all.** Starting at any point in 2009–2013,
the next three months would have lost money 67–100% of the time.

**Win rate versus expectancy.** Every rule wins 31–38% of the time with average wins of +1.1 to
+1.8R. That structure would be excellent if the average loss were not −0.9 to −1.06R and costs
did not take 0.12–0.20R from every trade. The rules with the highest win rates (B1 38.4%, A5
38.0%) are not the least bad; D3 is, at 36.0%.

## The liquidity / SMC question, answered with numbers (development, net R per trade)

| | Gross R | Net R | vs matched random* |
|---|---|---|---|
| Liquidity sweep, previous-day high/low (A1) | +0.019 | −0.144 | Welch t 0.92 (no information) |
| Liquidity sweep, Asian range (A2) | +0.014 | −0.163 | t 0.00 |
| Equal highs/lows sweep (A3) | +0.020 | −0.153 | t 1.49 |
| BOS + fair-value-gap retest (A4) | **+0.072** | −0.103 | t 2.05 |
| CHoCH (A5) | +0.004 | −0.126 | t 1.02 |
| Order block (A6) | −0.004 | −0.187 | t −0.02 |
| **Liquidity + volatility regime** (D1 = A4 in high volatility) | +0.064 | −0.106 | t 1.73: the regime filter **removed** value (A4 alone +0.072) |
| Generic failed breakout, no SMC labels (B5) | −0.007 | −0.186 | t −0.15 |
| Simple momentum (B3) | −0.011 | −0.162 | t 0.20 |
| Simple mean reversion (B4) | +0.025 | −0.143 | t 2.63 |
| Session / time-of-day baseline (B6) | +0.007 | −0.165 | t −0.50 |
| Random entries (E1) | −0.008 | −0.179 | — |

\* Matched random: the same number of trades, at random bars in the rule's own hours, with the
same stop distance in ATR, reward:risk and holding (3 seeds).

**What the numbers say.**

1. **Sweeps of named liquidity carry no information that random entries with the same stops and
   hours do not.**
   - The three sweep rules (A1–A3) gross +0.014 to +0.020R, against −0.007R for the same
     mechanism on an unnamed 48-bar range (B5).
   - That difference of about 0.02–0.03R per trade is real in sign and **one-eighth of the cost
     of a trade**.
2. **Structure-break continuation (A4 BOS-FVG) is the only SMC concept with measurable
   information.**
   - It grosses +0.072R and beats its matched random at t 2.05. That is still only 41% of its
     0.175R cost.
   - A volatility filter on top (D1) did not help.
3. **The non-SMC rules with similar measurable information** are the squeeze breakout (B2,
   +0.092R), squeeze in the H1 trend's direction (D3, +0.106R) and the USD catch-up (C1,
   +0.043R). Every one of them is far below its cost.
4. **No regime, session, instrument or year rescues the liquidity rules.**
   - A1 by session: London −0.148, London/NY overlap −0.112, New York −0.231.
   - A1 by regime: high volatility −0.138, low −0.211, trending −0.126, ranging −0.147.
   - A1 by year: 2009–2013, every year negative.
   - Per instrument: every instrument negative for A1, A2, A3, A6 and B5.

## Why M5 fails: the cost arithmetic

**The cost per trade is about 0.17R, against a gross information of at most 0.1R.**

| Item | Per trade | Note |
|---|---|---|
| Average stop | ≈ 13 pips | Commission 0.054R ≙ 0.7 pip |
| Spread | ≈ 0.10R | Measured Dukascopy bid/ask, both fills |
| Commission | ≈ 0.055R | |
| Slippage | ≈ 0.013R | |
| Financing | ≈ 0 | Intraday positions rarely cross 21:00 UTC |
| **Total** | **≈ 0.17R** | |

- **A rule therefore needs a gross expectancy of about +0.17R just to break even.** The best
  measured was +0.106R. Random entries gross about zero, as they must.
- **Larger stops reduce cost per R,** but they also lengthen the holding period towards the H1
  horizons where this project already measured gross expectancies within ±0.03R (DP-001, SL-002,
  WF-003).
- **The production risk engine already rejects the most cost-burdened trades** (cost > 25% of
  the stop). Of the failed-breakout signals on EURUSD alone, 4,846 of 15,658 were skipped that
  way. The trades that remain still pay about 0.17R.

**A cheaper broker would not change the verdict.** This is arithmetic from the decomposition
above, not a test:

| Rule | Net at half of every cost |
|---|---|
| D3 | ≈ +0.005R |
| B2 | ≈ −0.01R |
| A4 | ≈ −0.016R |
| Every other rule | below zero |

Dukascopy's 2009–2013 spreads plus a 0.7-pip commission sit at the conservative end of retail ECN
pricing, which is why every result here is labelled **provisional** against TradeLocker's real
spreads. There is no realistic broker whose costs are low enough.

## Robustness, cost stress, walk-forward and the untouched period

**Not run, by the preregistered design.** The parameter grids, cost ×1.25/×1.5/×2, slippage
stress, symbol, session, regime and walk-forward checks apply only to **promoted** candidates,
and there were none. Stress tests can only make negative expectancies more negative.

**The untouched period stays sealed.** The fx-majors holdout (2017-01 → 2022-07) remains unspent
for a future candidate with a new mechanism. Its M5 data was not built.

## Executability through the bot (for the record)

**These rule shapes fit the existing architecture far better than TOM did:**

- every trade has a stop and a target, with reward:risk 1.5–2.5;
- FX symbols resolve;
- the risk engine's cost checks were applied in the simulation.

**Simultaneous positions** across the 8 instruments peaked at 4–7, and exceeded the bot's limit
of 3 for at most 4% of the exposed time (B5). **Executability is not the problem; the edge is.**

## AI

No LLM was added. With no deterministic edge, there is nothing for a classifier or veto to
improve. An LLM cannot be backtested honestly: its training data contains the outcomes.

## Final verdicts

| Family | Verdict |
|---|---|
| Liquidity / SMC (A1–A6, D1) | **NO EDGE** |
| Price / volatility (B1–B6) | **NO EDGE** |
| Cross-market (C1) | **NO EDGE** |
| Hybrids (D2, D3) | **NO EDGE** |

**Strongest evidence (against an edge):**

- 16 of 16 rules are net negative, each across 5 years and 8 instruments;
- random entries lose almost exactly their cost (−0.179R against 0.171R of cost);
- the best rules carry at most 0.1R of information against 0.17R of cost.

**Weakest assumptions:**

- the spreads are Dukascopy 2009–2013, not TradeLocker today;
- commission and slippage are declared constants;
- sessions use fixed UTC hours;
- hour 00 UTC is missing for seven pairs.

None of these is large enough to turn a −0.1R rule positive. Even halving every cost leaves the
best rule at about zero.
