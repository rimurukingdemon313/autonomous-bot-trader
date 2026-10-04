# Retail-CFD research program: final report (2026-10)

> **Follow-up:** `docs/TOM_INVESTIGATION_REPORT.md` investigated the surviving candidate (E1 TOM) in
> depth. **Verdict: B, a WEAK PROMISING EDGE.** The calendar excess over ordinary days has been about
> zero on developed indices since 2009 (t 0.36), so the post-2009 net is mostly equity drift.

Every number below is from a committed artifact, produced by preregistered, frozen code:

- `research/knowledge/RC-EQ.json`, `RC-FX.json`, `RC-EQ2.json` and `RC-EQ2-H.json`;
- runner logs in `research/results/rceq*.log`.

Design and diagnosis, written before any result: `docs/RETAIL_RESEARCH_PROGRAM.md`.
Preregistrations: `research/preregistrations/RC-EQ.md`, `RC-FX.md` and `RC-EQ2.md`.

**Returns are the account's.** All are monthly returns as a fraction of equity, after:

- spread, slippage and commission;
- overnight financing at the benchmark ± a broker markup;
- dividends (none credited to longs on price indices; shorts pay).

Positions are at most 1× equity (1.5× for E5).

## I. Final decision

**PROMISING BUT NOT YET PROVEN.**

**One candidate survived an independent out-of-sample replication: the turn-of-the-month rule on
index CFDs (E1 TOM).**

- **Two universes.** It is positive after full retail costs on 10 index CFDs over 1990–2020
  (t 2.24). It is also positive on 16 indices this project had never loaded, over 1990–2026
  (t 2.18). There it passed every preregistered replication gate, including 2021+, 2009+, doubled
  costs and a one-day delay.
- **Not proven.**
  - It failed its own significance gate on the first universe (t 2.24 < 3.0).
  - Its return since 2009 is small and not significant (+1.1% a year on A, t 0.58; +1.2% on B,
    t 0.81).
  - Doubled costs leave about +0.5% a year.

It deserves **controlled PAPER testing as EXPERIMENTAL**, and nothing more. No research strategy
was promoted into the live system.

## A. Current root cause: why previous systems failed

The 15-point diagnosis is in `docs/RETAIL_RESEARCH_PROGRAM.md` §A. In one paragraph:

> On FX majors, at every horizon tested (M15 to monthly), price-based rules carry essentially no
> gross directional information. Gross expectancy is ±0.03R, and losses are WRONG_DIRECTION or
> NORMAL_VARIANCE, not fixable stops or exits. Retail costs (0.09–0.21R per intraday trade) turn
> zero into a loss. The one premium found in this repository's own history, diversified trend
> following, was real before 2008 (t 4.3) and about zero after (Sharpe 0.1). Retail financing of
> the leverage it needs makes it negative.

This program adds the decisive new fact:

> **Several documented equity-index and FX premia do exist before the broker, at t ≈ 2.3–3.7. The
> retail broker's costs then remove 35% to over 100% of them.** The overnight markup on held
> notional is the single largest item for anything held more than a few days. The rest of the
> damage is post-2006 decay.

## B. Strategies tested (genuinely distinct families)

| ID | Family | Rule (frozen) | Universe, judged | Result |
|---|---|---|---|---|
| E1 TOM | calendar flow | long the last trading day of each month and the first 3 of the next | 10 index CFDs, 1990–2020 | **PROMISING → replicated on B** |
| E2 DIP | short-horizon mean reversion | long after a ≥ 1σ volatility-scaled 5-day fall; out at z ≥ 0 or 10 closes | same | REJECTED |
| E3 XSMOM | cross-asset relative strength | long top 3, short bottom 3 indices by 12-1 month return, monthly | same | REJECTED |
| E4 REGIME | regime system | long above the 10-month average, monthly | same | REJECTED |
| E5 VOLMAN | volatility management | weight min(1.5, 15% / 21-day vol), monthly | same | REJECTED |
| E6 BREAKOUT | breakout | long-only Donchian 100 in / 50 out | same | REJECTED |
| E7 ENSEMBLE | multi-strategy | mean of E1–E6 targets, one account | same | PROMISING on A → **REJECTED on B** |
| E8 HALLOWEEN | seasonal | long November–April | same | not sent to B (failed t, drawdown, region) |
| X1 COMPOSITE | FX carry + momentum + value | top/bottom 2 of 8 currencies by mean rank, monthly | 7 USD pairs, H.10, 1990–2016 | REJECTED |
| X2 COT-FILTER | COT as a low-frequency filter | monthly FX trend minus crowded positions | same, 2007–2016 | REJECTED (value added t 0.02) |

**Already rejected in earlier programs and not repeated:**

- FX trend, breakout, pullback and narrow-range breakout;
- carry alone; cross-sectional momentum; value and reversal alone;
- COT as a trigger;
- the Tokyo and London fixes;
- rate news and oil–CAD;
- diversified multi-asset trend.

All of them are in `docs/TRADING_EDGE_REGISTRY.md`.

**Data-limited and not tested:**

- commodity CFDs: no roll-adjusted history is reachable;
- pre-FOMC drift: decayed after publication, about 8 events a year;
- relative-value pairs: no economic anchor; a pair search is data mining.

## C. Best candidates, exact results

### E1 TOM: the only survivor

| | Universe A (10 CFDs), 1990–2020 | Universe B (16 never-loaded indices), 1990–2026 |
|---|---|---|
| Months | 372 | 441 |
| Net annual return | **+2.59%** | **+1.87%** |
| Volatility | 6.45% | 5.20% |
| Sharpe / Sortino | 0.40 / 0.59 | 0.36 / 0.52 |
| **t (net)** | **2.24** (needed 3.0: failed) | **2.18** (needed 1.96: passed) |
| Max drawdown, compounded | 21.8% | 22.1% |
| Trades a year / median hold | 111 / 6 calendar days | 148 / 6 days |
| Win rate / profit factor (trades) | 56.1% / 1.28 | 55.8% / 1.23 |
| Expectancy per trade (per unit notional) | +23.5 bps | +20.2 bps |
| Time in market / average exposure | 23% / 0.18× | 27% / 0.15× |
| Turnover (notional traded per year) | 22× | 18.5× |
| Net return per unit of turnover | 0.12% | 0.10% |
| Rolling 36-month Sharpe, min / max | −0.98 / 2.38 | −0.93 / 3.01 |

### E7 ENSEMBLE (rejected on replication)

| | Universe A | Universe B |
|---|---|---|
| Net annual return | +2.00% | +1.07% |
| t | 2.02 | 1.44 |
| Sharpe | 0.36 | 0.24 |
| Max drawdown | 17.0% | 19.0% |
| With costs ×2 | +0.73% | **−0.22%** |

### Others, for completeness (net annual, t)

| ID | Net annual | t |
|---|---|---|
| E8 Halloween | +3.68% | 2.27 (drawdown 34% summed, 37% compounded) |
| E4 Regime | +2.42% | 1.66 |
| E2 Dip | +1.76% | 1.44 |
| E6 Breakout | +1.50% | 1.30 |
| X1 FX composite | +1.44% | 1.72 |
| E5 Volman | +1.49% | 0.73 |
| E3 XSMOM | −1.11% | −1.03 |
| X2 COT filter | −1.57% | −0.91 |

## D. Cost analysis (annual, as a fraction of equity)

**How to read the columns.**

- **Price** is the price P&L.
- **Benchmark** is the cash rate paid (or, for FX, the rate differential earned).
- **Markup** is the broker's 2.5% (index) or 1.5% (FX) a year on held notional.
- **Spread + slippage** is the trading cost (FX includes commission).
- **"Before broker"** is the price P&L plus the benchmark only: what the premium earns over cash
  without the retail broker.

| ID | Price | Benchmark | Markup | Spread + slippage | Dividends | **Net** | t before broker | t net | t costs ×2 |
|---|---|---|---|---|---|---|---|---|---|
| E1 TOM (A) | +4.16% | −0.55% | −0.47% | −0.54% | 0 | **+2.59%** | 3.12 | 2.24 | 1.36 |
| E1 TOM (B) | +3.82% | −0.64% | −0.40% | −0.93% | 0 | **+1.87%** | 3.71 | 2.18 | 0.64 |
| E2 DIP | +3.40% | −0.65% | −0.52% | −0.47% | 0 | +1.76% | 2.27 | 1.44 | 0.62 |
| E3 XSMOM | +2.81% | +0.05% | −2.53% | −0.13% | −1.31% | −1.11% | 2.65 | −1.03 | −3.49 |
| E4 REGIME | +5.76% | −1.76% | −1.54% | −0.04% | 0 | +2.42% | 2.75 | 1.66 | 0.58 |
| E5 VOLMAN | +6.73% | −2.80% | −2.38% | −0.06% | 0 | +1.49% | 1.92 | 0.73 | −0.47 |
| E6 BREAKOUT | +4.02% | −1.31% | −1.15% | −0.06% | 0 | +1.50% | 2.32 | 1.30 | 0.25 |
| E7 ENSEMBLE (A) | +4.48% | −1.17% | −1.07% | −0.20% | −0.03% | +2.00% | 3.35 | 2.02 | 0.73 |
| E7 ENSEMBLE (B) | +3.76% | −1.34% | −0.93% | −0.36% | −0.06% | +1.07% | 3.27 | 1.44 | −0.30 |
| E8 HALLOWEEN | +6.26% | −1.36% | −1.17% | −0.05% | 0 | +3.68% | 3.00 | 2.27 | 1.52 |
| X1 FX COMPOSITE | +1.36% | +1.43% (carry) | −1.30% | −0.04% | 0 | +1.44% | 3.33 | 1.72 | 0.12 |
| X2 COT FILTER | −0.58% | +0.15% | −1.10% | −0.03% | 0 | −1.57% | −0.25 | −0.91 | −1.57 |

**Readings.**

1. **The markup on held notional is the killer for anything held long.**
   - It cost XSMOM 2.5% a year (it is always 1× invested), VOLMAN 2.4% and REGIME 1.5%.
   - For FX, the 1.5% swap markup took the carry/value/momentum composite from t 3.33 to 1.72.
2. **TOM survives because it holds notional only 23–27% of the time.**
   - Its broker costs are about 1.0–1.3% a year against a 3.3–3.6% excess return.
   - Spread and slippage are about half of that: 111–148 round trips a year at 4 bps per
     round trip plus 1–6 days of markup.
3. **Leverage changes nothing about the ratio**: a CFD scales price, costs and financing together.

   | E1 TOM (A) | Net annual | Compounded max drawdown |
   |---|---|---|
   | 1× | +2.6% | 21.8% |
   | 2× | +5.2% | 40.4% |
   | 3× | +7.8% | 55.8% |

   Sharpe is unchanged by construction. **Any useful return requires leverage whose drawdown is
   not retail-compatible.**

## E. Out-of-sample results, separated

| | Development | Validation | Modern 2009+ | Independent universe B | B from 2021 |
|---|---|---|---|---|---|
| E1 TOM | 1990–2005: +4.49%, t 2.75 | 2006–2020: +0.57%, t 0.35 | A 2009–20: +1.06%, t 0.58; B 2009–26: +1.17%, t 0.81 | +1.87%, t 2.18 (B before 2021: +2.02%, t 2.17) | +1.02%, t 0.46 (69 months) |
| E7 ENSEMBLE | +2.47%, t 1.71 | +1.50%, t 1.11 | +2.01%, t 1.33 | +1.07%, t 1.44 (failed) | +1.89%, t 0.94 |
| E8 HALLOWEEN | t 1.77 | t 1.45 | t 1.82 | not run (failed A) | — |
| X1 FX | 1990–2003: +2.23%, t 2.12 | 2004–2016: +0.59%, t 0.45 | +1.64%, t 0.90 | FX holdout **still sealed** | — |

**What stays sealed or unused.**

- **Universe A after 2020** (the period DIV-2-H opened) was never loaded.
- **The fx-majors 2017+ holdout is still sealed.** No FX candidate earned it.

## F. Robustness (E1 TOM)

- **Neighbourhood.** All 9 grid cells are positive on A (k_pre {1,2,3} × k_post {2,3,4}). t runs
  from 1.86 to 2.72, median 2.44. It is a region, not a magic number.
  - Windows starting earlier (k_pre 3) are slightly stronger: t 2.44–2.72.
  - Extending to day +4 is weaker: t 1.86–2.44.
- **Costs ×2.** A: +1.58% (t 1.36). B: +0.55% (t 0.64). Positive, barely.
- **One-day execution delay.** A: +1.84% (t 1.51). B: +1.30% (t 1.37).
- **Leave one index out.** Positive for every omission on A and on B.
- **Per index, A.** Nine of ten are positive. The exception is JPN225 (t −0.04), which is also
  excluded about 32% of the time because the BoJ published no policy rate.
- **Per index, B.** 13 of 16 are positive. The negatives are EU50, SWE30 and MYS30.
- **Regimes (A, annualised mean daily net).**
  - US500 above its 200-day average: +2.97%; below: +0.93%.
  - High volatility: +5.19%; medium: +2.01%; low: +0.34%.
  - The effect is larger in turbulent markets.
- **By year.**
  - B: 25 of 37 years positive. The worst year is 2016 (−9.9% at the 1/16 sizing). The best year
    supplies 12% of the positive total.
  - A: 19 of 31 years positive. The best year supplies 13%.

## G. Economic explanation (why TOM should exist)

- **Ariel (1987), Lakonishok & Smidt (1988), McConnell & Xu (2008):** most of the equity premium
  accrues around the turn of the month.
- **The mechanism is scheduled cash flow.** Salaries, pension contributions, dividend reinvestment
  and fund subscriptions arrive and are invested at month end, while window dressing and
  liquidity needs are concentrated just before it.
- **What earlier tests here did not have.** The flow is predictable in time, it is in equities
  (where the cash goes, not FX majors), and it needs no forecast of direction. That is why it
  survives the retail broker better than everything else here: the position is held only on the
  days the flow is expected.
- **Why it decays.** It is well known, and index futures and ETFs make it cheap to front-run. The
  grid's earlier-starting windows do best. Both are consistent with anticipation pulling the effect
  earlier and thinner.

## H. AI contribution

**None was measured, deliberately.**

- **No baseline yet.** The program's priority order puts AI after a deterministic edge exists.
  The only candidate (TOM) is calendar-only, with nothing to classify or score that a model could
  improve without being fitted on the same data.
- **No honest backtest.** A language model cannot be backtested: its training text contains the
  outcomes.
- **Where the live system stands.** It keeps AI as a veto only, labelled EXPERIMENTAL, and
  measures it forward against the deterministic baseline (`/api/evidence`). If a TOM paper test
  runs, an AI veto's value would be measured there the same way, and kept only if it beats the
  plain calendar rule.

## The candidate, exactly as tested (for a controlled PAPER test only)

| Item | Specification |
|---|---|
| Strategy | E1 TOM, `rc.tom(k_pre=1, k_post=3)`, frozen in `research/specs/RC-EQ.json` |
| Instruments | index CFDs: US500, NAS100, GER40, UK100, FRA40, JPN225, AUS200, HK50, CAN60, SWI20 (B confirms on 16 more) |
| Timeframe | daily closes; exchange calendar |
| Entry | at the close of the second-to-last trading day of each month (holds the last day) |
| Exit | at the close of the 3rd trading day of the next month |
| Sizing | 1/N of equity notional per index (N = 10), at most 1× in total; no leverage |
| Turnover | about 12 round trips a year per index, 111–148 trades a year in total |
| Costs used | 2–10 bps spread, 1 bp slippage per fill, benchmark + 2.5% financing, no dividend credit |
| Expected | **about +1–2.6% a year, Sharpe 0.2–0.4, drawdowns above 20%, and many losing years.** Since 2009 the net mean is not distinguishable from zero |
| Evidence | A t 2.24 (failed 3.0), B t 2.18 (passed 1.96), every robustness gate passed. Before the broker, t 3.1 / 3.7 |

**What promotion to PAPER would need (not built).**

- TradeLocker index instruments and their real spread and financing tables.
- A calendar-driven decision path that passes the unchanged risk engine. The engine's stop-based
  sizing and cost-to-risk check are FX/pip-oriented and have no notion of a time exit; adapting
  them is engineering that must not weaken them.

**What a paper test can and cannot show.** At Sharpe ≈ 0.3, a forward test needs decades to reach
significance. **A paper test measures execution realism (real spreads, real financing), not the
edge.** It must not be read as proof either way within a year.

## Exhausted, and what prevents further credible research

- **Equity indices:** universe A (1990–2020) is judged; universe B is spent on the replication.
  No clean equity-index data remains.
- **FX majors:** every documented family has been judged on 1990–2016. One holdout remains,
  fx-majors 2017+, **sealed and unspent**. It should be kept for a candidate with a mechanism not
  yet tested.
- **Commodities:** blocked by the lack of roll-adjusted futures history.
- **What could add credible evidence:**
  1. **forward data** (the live forward ledger, and a TOM paper test);
  2. **instruments with lower holding costs** (dated/forward index CFDs or futures carry no 2.5%
     markup; every "before broker" t above is what such instruments would see before their own,
     smaller, costs);
  3. **point-in-time single-stock data** without survivorship bias (paid), for the large
     cross-sectional equity literature that cannot be tested honestly from free data.

## Tests and commit

- Full suite: **715 passed, 0 failed** (`bash scripts/check.sh`; 687 before this program).
- Mutation audit: **149 of 149 killed**, including 6 new guards: index markup charged, no
  position without a known rate, the TOM window, the FX publication lag, cross-sectional fills
  after the decision, and a replication never turning PROMISING into VALIDATED.
- Edge registry (edges-1.7.0): 69 REJECTED, 2 PROMISING (E1 TOM replicated; E8 Halloween by
  RC-EQ's definition, never tested on B), 1 VALIDATED (DIV2-H1 by its sign rule, explained in
  `research/results/DIV-2-summary.md`).

