# Edge search (final mission): what was tested and what the evidence says

**Status: EDGE NOT FOUND — RESEARCH SPACE EXHAUSTED (for what this environment can reach). Every program in this round FAILED. Nothing is promoted; every holdout is untouched.**

The machine-readable record is `research/registry.jsonl` and `research_status.json`. Each program has a
preregistration in `research/preregistrations/` that was committed **before** its outcome existed, and a
result in `research/knowledge/`.

## 1. The bottleneck, measured

The question was why ID-2's ML ranking (gross +0.19R, net +0.09R, t 1.39) never passed. The cost
decomposition of its best configurations:

| | Spread | Commission | Slippage | Total cost | Gross | Net |
|---|---|---|---|---|---|---|
| Share of cost | 57% | 35% | 8% | 0.10R | +0.19R | +0.09R |

ID-2 itself showed two things:

- **The ranking is mostly cost avoidance.** A model given only the cost-to-stop ratio ranks better than
  the full model.
- **Lengthening the holding scale reduces gross faster than cost.** Gross fell from +0.19R at S5 to
  +0.10R at S60.

The core fact is cost relative to the size of the move. Round-trip cost as a fraction of the standard
deviation of the move, FX majors 2007–2012:

| Horizon | 1 h | 4 h | 8 h |
|---|---|---|---|
| Cost / σ (EURUSD → NZDUSD) | 0.10–0.23 | 0.05–0.12 | 0.03–0.08 |

So an intraday FX rule needs more than 3 bp of predictable move per trade. Every family below fell short
of that.

## 2. What was tested in this round (every look counted in the registry)

| ID | Hypothesis and economic reason | Data | Trades | Gross | Cost | Net | t | Verdict |
|---|---|---|---|---|---|---|---|---|
| EX-1 | 21 FX session and order-flow families: Asian-session USD drift, reversal of illiquid-hours moves (Grossman–Miller), session momentum and reversal (Elaut et al.), activity-conditioned continuation (Llorente et al.) | FX majors M15, 2007–2012, real bid/ask | 457–18,327 each | ≤ +3.96 bp (best F1 24 h); every other ≤ +2.24 bp | 1.4–3.1 bp | best +1.2 bp (t 0.3) | ≤ 0.32 | FAILED: gross is below cost in every family |
| EX-2 | Intraday momentum into the futures settlement, FX and gold | FX/gold M15, 2007–2012 | 94–16,997 | FX +0.06 bp; gold +3.0 / +7.8 bp | 2.8–3.1 bp | gold +0.1 / +4.7 bp | gold 0.09 / 1.58 | FAILED (FX); gold carried to IX-1 |
| IX-1 | Intraday momentum into the COMEX settlement (Baltussen et al. 2021) | Gold, silver M5, 2013–2016 (unseen) | 1,883 / 458 | +0.72 / +3.25 bp | 11.7 bp | −10.9 / −8.4 bp | −20.4 / −7.5 | FAILED: the gold hint did not replicate; silver's spread is prohibitive |
| IX-2 | Last-hour momentum into the cash close (Gao et al. 2018; Baltussen et al. 2021): gamma and leveraged-ETF hedging | 6 index CFDs H1 (S&P 500, Nasdaq-100, Dow, Nikkei, Hang Seng, ASX), 2012–2020 | 10,511 / 2,824 (102 / 27 a month) | +1.07 / +2.61 bp | 4.3 bp | −3.24 / −1.63 bp | −7.1 / −3.1 | FAILED: the signal exists in the predicted direction but is smaller than the CFD spread |
| IX-3 | Overnight drift at the European open (Boyarchenko et al. 2023): dealer inventory compensation | US index CFDs H1, 2013–2020 | 5,431 / 2,221 | +0.003 / −0.97 bp | 3.3–3.6 bp | −3.55 / −4.23 bp | −7.8 / −5.5 | FAILED: no drift in the CFD |
| IX-4 | NASDAQ opening-candle EMA(12) signal (from a video; its +982% claim is never used) | Nasdaq-100 CFD M5 bid/ask, development 2012–2016 | 1,148 per exit (19.8 a month) | +0.20 to +1.55 bp across 10 exits (Q1 t ≤ 1.17) | 4.0–4.3 bp | −2.78 to −3.89 bp | −2.1 to −6.9 | FAILED at development: no exit promoted; validation not run |

Every program was also stressed at:

- costs × 1.5 and × 2;
- a delay or late entry;
- both chronological halves.

None reached positive net at base cost, so none survives the stresses either. The full stress numbers
are in the knowledge files.

### IX-4 in detail (the video's strategy)

**Setup:**

- **Instrument:** USATECHIDXUSD (Nasdaq-100 CFD), M5 bid/ask built from Dukascopy minute candles.
- **Session:** the signal bar opens 09:30 America/New_York (DST-correct).
- **Signal:** EMA(12) of the mid close over the full continuous M5 series. LONG if the 09:30 bar closes
  above it, SHORT if below; entry at the 09:35 open at bid/ask plus slippage (0.26 index points per fill).
- **Data:** 1,151 signal days in 2012–2016; 51% long.

**Results:**

| Question | Answer |
|---|---|
| Q1 (entry edge) | Gross +0.2 to +1.5 bp, t ≤ 1.17 for every exit. **Not distinguishable from zero** |
| Q2 (tradable edge) | Cost 4.0–4.3 bp. Net −2.8 to −3.9 bp; costs × 1.5 and × 2 and the delay are all worse |
| Q3 (complete strategy) | Best exit TCLOSE: net −2.78 bp (95% CI −5.38 to −0.17), PF 0.85, 20% wins, max DD 203R, 36% of rolling 3-month windows profitable. Nothing promoted |

**Baselines and robustness:**

| Check | Result |
|---|---|
| Baselines (T30 / TCLOSE) | Random direction gross −0.45 / −0.79 bp; random time with the EMA side +0.07 / −0.11; **first-candle direction without the EMA +1.82 / +2.00**; session long +0.60 |
| EMA period, 8 to 16 | Net −2.3 to −3.7 bp (TCLOSE); never positive |
| Regular-session EMA | Worse, −4.2 bp |
| Volatility terciles | Best cell +0.03 bp, t 0.01 |
| By year (TCLOSE) | Positive only in 2012 (+0.96 bp) |

**What this means:**

- The EMA adds nothing: the bare first-candle direction carries more gross information, and neither pays
  the CFD spread.
- The video's +982% is not reproducible from its disclosed rule under real costs. A stop-fill convention
  that fills at the stop price manufactures edge on a random walk (section 3), which is one way such
  backtests arise.
- Validation (2017–2020) was not run and the holdout (2021–2024) was never fetched.

## 3. Integrity findings in this round

- **Stop fills.** Filling a stop exactly at its level manufactured +1.5 to +3 bp of gross edge on a pure
  random walk. IX-4 fills stops through the level, and a regression test forbids any exit from showing an
  edge on a random walk. It was verified to fail against the old fill.
  - IX-1/IX-2/IX-3 used the old convention, frozen before this was found.
  - The bias is small there: 2–9% of trades stopped out.
  - It is optimistic, so it can only have flattered results that failed anyway.
- **Frozen study code.** A repository-wide lint auto-fix had silently changed frozen, registered study
  code. The frozen-design tests caught it; the edits were reverted and those files are exempted.
- **Holdouts.** None was opened.
  - fx-majors 2017+ is still sealed.
  - The index-CFD holdout (2021–2024) was never even downloaded.

## 4. What this establishes, and what it does not

**Established, for retail CFD/FX execution priced at historical Dukascopy bid/ask:**

- Intraday price-pattern edges in FX majors are smaller than the spread. That covers 160+ registered FX
  tests across this project at every horizon from 5 minutes to 1 day.
- The best-documented academic intraday effects in equity indices have the predicted **sign** but not
  the **size** to pay a CFD spread:
  - momentum into the close: +1 to +2.6 bp gross against 4.3 bp of cost;
  - the European-open drift: none.
- Those effects are measured in futures at about 0.25 bp of cost, which is roughly 15–20 times cheaper
  than a retail CFD.

**Not established:**

- That no edge exists anywhere. Execution with futures-level costs was not available here.
- TradeLocker's actual spreads are unmeasured. If they are materially tighter than Dukascopy's, IX-2's
  STRONG variant (gross +2.6 bp) is the first thing to re-measure, forward and in demo, not by re-mining
  history.

## 5. Final status

**EDGE NOT FOUND — RESEARCH SPACE EXHAUSTED** for this environment:

- retail CFD/FX execution at historical bid/ask;
- data reachable through GitHub runners;
- 2007–2020 history.

Every program was preregistered before its data was seen and judged once. All of them failed at base
cost:

- 25 exploratory looks (EX-1, EX-2);
- IX-1, IX-2, IX-3 and IX-4.

**The common cause, measured:** documented intraday effects exist in the predicted direction (IX-2:
+1 to +2.6 bp gross; IX-4's first candle: about +2 bp), but they are smaller than a retail CFD round
trip (3.5–4.3 bp). They are real in futures at about 0.25 bp of cost.

The bot stays DEMO/PAPER-only with nothing promoted. What would change this is measured broker cost, not
more mining of the same history:

- run the spread recorder against TradeLocker;
- if its index spreads are below about 1.5 bp round trip, IX-2 STRONG and the first-candle direction
  are the two candidates to re-test, **forward**, under a new preregistration.
