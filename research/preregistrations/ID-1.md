# ID-1: is there an intraday M5 edge after realistic retail costs? (preregistration)

**Written, frozen and committed before any strategy outcome was computed.** The only real-data
computations before writing were the data audit (bar counts, coverage, spreads) and signal
**counts and run times** for each rule on EURUSD. No return, R, win rate or P&L of any rule was
computed.

| | |
|---|---|
| Frozen spec | `research/specs/ID-1.json` |
| Spec sha256 | `429a0b48cbbd5e9101dc23d0ab140a42d8dabb20cbbbbbd3e0241f64c94c83c8` |
| Code | `aitrader/research/discovery/intraday.py` (id-1.0.0), `scripts/id1.py` (hashed in the spec) |
| Data | M5 bid/ask bars 2009–2016 built from the FX-Data mirror of Dukascopy ticks (`scripts/ingest_dukascopy.py --timeframe M5`, branch `id-data`, per-year source SHAs in `data/m5/manifest_*.json`) |
| Untouched test | The project's fx-majors holdout, 2017-01 onward (`research/holdout.json`, never opened). Its M5 bars **are not built** until a candidate earns it |

## Phase 1: what was reused, what was built

**Reused:**

- the tick→bar aggregator (`aitrader/data/ticks.py`) and ingester (generalised to M5, M15
  behaviour unchanged);
- `BarSeries`;
- the project's fill conventions (`research/labels.py`, `discovery/exits.py`: next-bar open on
  bid/ask, stop before target, gaps fill at the open);
- its cost constants (commission 0.7 pip per round trip, slippage 0.1 pip per fill: the risk
  engine's own values);
- the production risk engine's entry limits;
- BIS policy rates for financing (`data/rc/policy_rates.csv`);
- the registry and holdout mechanics;
- `stats.welch_t`.

**Built:** an intraday simulator. The existing one takes ATR-multiple stops and market entries
only, while these rules need structure-based stops, limit entries and session deadlines. Also
built: the rule library and the evaluation with rolling 1/3/6-month windows.

**Data audit, M5 2009-01 → 2016-12.**

- **Instruments and coverage.** EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF and NZDUSD, about
  575k bars each; XAUUSD from 2011-05.
- **Measured median spread, 07–20 UTC:** EURUSD 0.5, USDJPY 0.6, GBPUSD/AUDUSD/USDCAD 1.2, USDCHF
  1.3, NZDUSD 1.6 pips, XAUUSD $0.31.
- **Known source defect:** hour 00 UTC is missing for every pair except EURUSD. All rules here
  enter 07:00–20:00 UTC; the Asian range of A2 starts at 01:00 for those pairs (declared).
- **Index CFDs are not included.** The only free intraday bid/ask source probed (Dukascopy's own
  datafeed) refuses bulk access from the runners: 107 of 120 requests failed
  (`research/results/id-probe.json`).

## Costs: measured where possible, declared where not (provisional against the actual broker)

| Item | Value |
|---|---|
| Spread | **Measured** bid/ask of every bar (Dukascopy). Entries and exits trade the correct side |
| Commission | 0.7 pip per round trip (≈ $7 per standard lot; for gold $0.07 per oz) |
| Slippage | 0.1 pip per **market** fill (entries at market, stops, time exits). Targets and limit entries have none |
| Financing | Per 21:00 UTC rollover crossed (Wednesday ×3): the BIS policy-rate differential minus 1.5% a year, on the notional |
| Stress | Costs ×1.25, ×1.5, ×2 (spread, commission, slippage and markup) and slippage 0.3 pip per fill |

**These are not TradeLocker's actual spreads.** Those are unknown here (the live spread recorder
has no history), so every result is **provisional** against them. Dukascopy's 2009–2013 spreads
plus commission are at the conservative end of retail ECN pricing: EURUSD ≈ 1.3 pips all-in,
GBPUSD ≈ 2.1.

**The production risk engine's entry checks are applied to every trade**, and a failing signal is
skipped as the bot would skip it:

- stop ≥ 3 spreads;
- spread ≤ 25% of the stop;
- round trip (spread + commission + 2 slippage) ≤ 25% of the stop;
- reward:risk ≥ 1.2.

## Fill model

**Entry.**

- A signal is decided at a bar's close and entered at the **next bar's open** (ask + slippage
  for a buy, bid − slippage for a sell).
- A limit order (A4, A6) fills only when the market trades **through** its price, at the price
  or a better open. In its fill bar only the stop is checked.

**Exits.**

- **Stop:** checked before the target in every bar. A bar touching both is a stop. A gap fills
  at the open, minus slippage.
- **Target:** fills at its price, never better.
- **Time exit:** at the close of the last allowed bar.
- **Before a gap > 1 hour:** the position closes at the last bar before it (weekends,
  holidays).

**Limits:** one position or pending order per instrument; entries Monday–Friday, 07:00–20:00
UTC. Sessions are fixed UTC hours (DST ignored, declared).

**R** is net of every cost, in units of the actual initial risk (fill to stop).

## Rules (exact; `intraday.py`; ATR = mean true range of the last 14 M5 bars on mid prices)

### A. Liquidity / market structure

| ID | Rule |
|---|---|
| A1 SWEEP-PDHL | Previous trading day (22:00→22:00 UTC) high/low. A bar trading ≥ 0.10 ATR beyond it and **closing back inside** is faded. Stop: the bar's extreme ± 0.10 ATR. Target 2R. 48 bars max. First sweep of each level per day |
| A2 SWEEP-ASIA | Asian range = the UTC day's bars before 07:00. From 07:00 to 11:55, a bar trading ≥ 0.10 ATR beyond it and closing back inside is faded. Stop: the extreme ± 0.10 ATR. 2R. 36 bars. First per side per day |
| A3 SWEEP-EQUAL | Two **confirmed** fractal swing highs (3 bars each side; known 3 bars later) within the last 72 bars and within 0.10 ATR of each other form a level. A bar trading ≥ 0.10 ATR beyond it and closing back inside is faded. Stop: the bar ± 0.10 ATR. 2R. 48 bars. Mirror for lows |
| A4 BOS-FVG | A close beyond the last confirmed swing high, on a displacement bar (body ≥ 1.2 ATR), leaving a fair-value gap (low[t] > high[t−2]). Buy limit at low[t] for 12 bars. Stop low[t−2] − 0.10 ATR. 2R. 48 bars. Mirror |
| A5 CHOCH | In a confirmed downtrend (lower swing high and lower swing low), a close above the last confirmed swing high is a long. Stop: the last confirmed swing low − 0.10 ATR, kept only if 0.5–4 ATR away. 2R. 48 bars. Mirror |
| A6 ORDER-BLOCK | After A4's displacement break, the last opposite-colour bar among the previous 5 is the block. Limit at its far edge for 24 bars. Stop beyond it ± 0.10 ATR. 2R. 48 bars |

### B. Price / volatility (no SMC vocabulary)

| ID | Rule |
|---|---|
| B1 OPENING-RANGE | London range 07:00–07:25 UTC. The first close beyond it between 07:30 and 10:55 is traded in its direction. Stop: the opposite side (0.5–4 ATR). 2R. Time exit at 16:00 UTC |
| B2 SQUEEZE | Bollinger width (20, 2 sd) of the previous bar in the lowest 10% of its past 1,000 bars, then a close beyond the previous 20 bars' high/low. Stop 1.5 ATR. 2R. 36 bars |
| B3 MOMENTUM | 12-bar move ≥ 2 sd (of the past 288 one-bar moves × √12): trade with it. Stop 1.5 ATR. 2R. 24 bars. One signal per 12 bars |
| B4 MEAN-REVERSION | Close ≥ 2.5 ATR from its EMA(20): fade it. Stop 1.5 ATR. Target = the EMA at the signal. 24 bars |
| B5 FAILED-BREAKOUT | A bar trading ≥ 0.10 ATR beyond the previous 48 bars' high/low and closing back inside is faded. Stop: the bar ± 0.10 ATR. 2R. 48 bars. **The price-only twin of the sweeps** |
| B6 SESSION-OPEN | At the 07:00 UTC bar's close, trade in the direction of the move since 22:00 UTC. Stop 1.5 ATR. 2R. 48 bars. **The session / time-of-day baseline** |

### C. Cross-market

| ID | Rule |
|---|---|
| C1 USD-LAG | A USD index (mean USD-signed log price of the USD pairs, each forward-filled from its own past). When its 12-bar move is ≥ 2 sd and a pair's own USD-signed move is ≤ 0.5 sd (it has not followed), trade the pair in the USD's direction. Stop 1.5 ATR. 2R. 24 bars |

### D. Hybrids: defined now, each judged against its own component

| ID | Rule |
|---|---|
| D1 | The liquidity rule (A1–A6) with the best **development** net R (≥ 300 trades), kept only when ATR is in the top half of its past week (a volatility regime) |
| D2 | B3 MOMENTUM, entries 12:00–16:00 UTC only (the London/New York overlap) |
| D3 | B2 SQUEEZE, only in the direction of the slope of an EMA(50) of **completed** H1 closes over 3 hours |

### E. Controls (not hypotheses)

| Control | What it does |
|---|---|
| E1 RANDOM | One random bar per day per instrument in 07:00–20:00, random side, stop 1.5 ATR, 2R, 48 bars |
| E2 / E3 | The same, long only / short only (the drift baselines) |
| Matched random, for every hypothesis | The same number of signals, at random bars **in the rule's own hours**, random side, the **same stop distance in ATR**, the same reward:risk and holding as a random signal of the rule (3 seeds) |

B3 and B4 are the simple momentum and mean-reversion baselines; B6 is the session baseline.

## Periods and gates

| Stage | Period | Role |
|---|---|---|
| Development | 2009-01 → 2013-12 | `select`: every hypothesis and control |
| Validation | 2014-01 → 2016-12 | `judge`: **promoted hypotheses only**, never computed for the others |
| Untouched test | 2017-01 → 2022-07 | fx-majors holdout: validation passers only, once |

**Promotion (development, all required):**

1. ≥ 300 trades;
2. net R > 0;
3. t ≥ 2.0 on daily net R (every weekday counted);
4. profit factor ≥ 1.10;
5. beats its matched random by Welch t ≥ 2.0;
6. net R > 0 on ≥ 60% of the instruments with ≥ 30 trades.

**Validation (all required):**

1. t ≥ max(3.0, the registry's Bonferroni value for fx-majors 2014–2016), recorded in the spec;
2. net R > 0;
3. profit factor ≥ 1.20;
4. costs ×1.5 net R > 0;
5. ≥ 60% of instruments positive;
6. ≥ 60% of rolling 3-month windows profitable;
7. beats matched random (Welch t ≥ 2.0);
8. ≥ 75% of its preregistered parameter grid positive;
9. hybrids only: validation net R above its component's.

**Holdout:** t ≥ z(1 − 0.05/k), net R > 0, profit factor ≥ 1.1, costs ×1.5 > 0, and ≥ 55% of
3-month windows profitable.

## Reported for every hypothesis

- **Trades:** count, trades a month, win rate, average win and loss R, profit factor.
- **Expectancy:** gross R and its spread, commission, slippage and financing parts, net R, t.
- **Account at 0.5% risk per trade, without compounding:** net return, annual return, Sharpe and
  maximum drawdown, plus the 0.25% / 0.5% / 1% risk table.
- **Rolling windows (1, 3 and 6 months):** share profitable, median, worst, best, deciles and
  drawdown inside.
- **Breakdowns:** by instrument, year, session and regime (volatility; trend vs range by
  efficiency ratio).
- **Concentration:** the share of profit from the best 10% of trades.
- **Executability:** the maximum number of simultaneous positions, and the time spent above the
  bot's limit of 3.

## What would and would not follow

- **A candidate passing the holdout** would be a candidate for PAPER/DEMO only, after the
  executability checks. Nothing would be promoted automatically.
- **A failure of everything is the expected outcome** given the project's record at H1 and M15
  (gross expectancy ±0.03R). It will be reported as NO EDGE, with the cost decomposition that
  explains it.
