# IX-4: the NASDAQ opening-candle EMA(12) signal (preregistration)

| | |
|---|---|
| Frozen spec | `research/specs/IX-4.json` |
| Spec sha256 | `c981710d50d2dd435376c9eb5d8cf29a8613cfe01e689f8fab0d84d67ec8c3be` |
| Code | `aitrader/research/discovery/ixopen.py` (ixo-1.0.0), `scripts/ix4.py` |
| Tests | `tests/unit/test_ixopen.py` (13), including **no exit may show a gross edge on a pure random walk** |
| Run | `python scripts/ix4.py develop` once → `validate` once (promoted exits only) → `holdout` once (validation passers only) |

## Source and status of the claim

The hypothesis comes from a video showing a NASDAQ intraday strategy and claiming +982%.

**That number is an unverified external claim.** It is never used as a target, a filter, a benchmark or a
reason to keep searching. Only the disclosed **entry** signal is tested. The video does not disclose its
exit, so none is reverse-engineered: a small exit family is fixed here before any data is loaded.

## Questions, reported separately

- **Q1, entry edge.** Does the 09:30 candle's close relative to EMA(12) predict the subsequent return?
  Measured as the gross, mid-to-mid, direction-signed return of every exit, with its t on the daily book,
  against the random-direction baseline.
- **Q2, tradable edge.** Does the prediction survive bid/ask, slippage and delay? Measured as net
  results, costs × 1.5 and × 2, and entry one bar later.
- **Q3, complete strategy.** Does any preregistered exit turn the signal into a statistically defensible
  positive-expectancy system? Answered by the promotion and validation gates.

A failure at Q3 does not erase a Q1 result; each is reported on its own.

## Instrument, session, EMA, entry (determined before any 5-minute data exists in this repository)

| | |
|---|---|
| Instrument | **USATECHIDXUSD**, Dukascopy's Nasdaq-100 CFD (the "NAS100 / US100" class of instrument), M5 bid/ask built from its minute bid and ask candles (`scripts/ingest_dukascopy_candles.py`). Index-CFD history starts in 2012 (`research/results/ix-probe.json`). No other instrument is substituted |
| Session | New York cash session. The signal bar is the 5-minute bar **opening at 09:30 America/New_York** (14:30 UTC in winter, 13:30 UTC in summer: `zoneinfo`, DST-correct). It closes at 09:35. The session close is 16:00 New York. Weekdays only; a day whose 09:30 bar is missing (holidays) is skipped. Half-days are not treated specially; the CFD keeps trading after a 13:00 cash close |
| EMA | EMA(12) of the **mid close**, α = 2/13, recursive, seeded with the first loaded close. **Primary: the full continuous 5-minute series** (the CFD trades nearly 24 hours, as a trader sees it on a chart). Reported, never selected: EMA over regular-session bars only, and EMA 8 / 10 / 14 / 16 |
| Signal | LONG if the 09:30 bar's mid close > EMA(12) at that bar; SHORT if <; no trade if equal |
| Entry | The open of the next bar (09:35) on the correct side of the quote (ask for a buy, bid for a sell) plus slippage. Nothing of the signal bar is used before it closes. The delay stress enters at 09:40 |
| Risk unit | ATR(14) of the mid bars up to and including the signal bar. Every initial stop is at least 3 spreads from the entry (the risk engine's own entry rule). R = net P&L / initial stop distance |

## The exit family: 10 exits, fixed now, all reported

Every exit is flat at the open of the 16:00 New York bar at the latest, so no financing is ever charged.

| Exit | Rule |
|---|---|
| T30, T60, T120, T240 | Exit at the open of the bar starting 30 / 60 / 120 / 240 minutes after entry; catastrophic stop at 2 ATR |
| TCLOSE | Exit at the 16:00 bar's open; catastrophic stop at 2 ATR |
| S1.0, S1.5, S2.0 | Stop k ATR, target 2k ATR (reward:risk 2); otherwise TCLOSE |
| TRATR | Initial stop 1.5 ATR, trailed 1.5 ATR behind the best mid close of completed bars |
| TRBAR | Initial stop 1.5 ATR, then trailed to the previous completed bar's low (long) or high (short), only ever tightening |

**Fills:**

- A stop is a market order once triggered. It fills half a spread **through** the stop, or at a gapping
  bar's open, less slippage. Filling exactly at the stop manufactured +1.5 to +3 bp of gross edge on a
  pure random walk; the regression test now forbids that.
- A target fills at its price, never better.
- A bar touching both the stop and the target counts as a stop.

## Costs

| Cost | Treatment |
|---|---|
| Spread | The bar's real bid/ask at entry and exit |
| Slippage | Per fill, a quarter of the median quoted spread of the development bars at 09:35 |
| Commission | 0 (index CFDs are spread-only) |
| Financing | None |
| Stress | Costs × 1.5 and × 2 scale every cost, spread included. Entry one bar later |

## Baselines (computed for every exit)

1. Random direction at the same entry times (3 seeds). The promotion and validation gates require
   **Welch t ≥ 2 against it**.
2. A random 09:35–15:00 entry bar with the EMA(12) side at that bar: EMA without the opening timing
   (3 seeds).
3. A random bar with a random side (3 seeds).
4. First-candle direction without the EMA (close vs open of the 09:30 bar).
5. Session long, 09:35 → 16:00: the NASDAQ intraday drift benchmark.

## Data split

| Period | Role |
|---|---|
| **Development 2012-01-01 → 2017-01-01** | Registered as "select". All 10 exits are run once; the full statistics are reported |
| **Validation 2017-01-01 → 2021-01-01** | Only promoted exits, once |
| **Holdout 2021-01-01 → 2025-01-01** | Sealed. Not fetched unless an exit passes validation. Never opened to investigate a disappointing result |

## Promotion from development (each exit; all required)

- ≥ 300 trades;
- net > 0;
- t ≥ 2.0 on the daily book;
- net > 0 at costs × 1.5;
- Welch t ≥ 2.0 against random direction (net per trade).

## Validation gates (promoted exits; all required)

| Gate | Requirement |
|---|---|
| net | > 0 |
| t | ≥ Bonferroni over every test ever registered (189 before IX-4, plus IX-4's 10, plus the k promoted: about **3.66–3.67**) |
| costs × 1.5 | net > 0 |
| costs × 2 | net > 0. Failing it is FRAGILE, which fails |
| delay | net > 0 with entry one bar later |
| halves | both chronological halves > 0 |
| profit factor | ≥ 1.05 |
| top year | no calendar year > 50% of the total net |
| vs random direction | Welch t ≥ 2.0 |

## Reported, not gated

- trades and trades per month;
- gross, cost and net expectancy in bp and R, with a 95% confidence interval;
- win rate, average win and average loss;
- profit factor and maximum drawdown in R;
- t, profitable rolling 3-month windows, by year, by half;
- by ATR-volatility tercile (cuts fixed on development and reused on validation);
- the EMA 8 / 10 / 14 / 16 and regular-session-EMA robustness;
- every baseline.

## Forbidden, by this document

- tuning anything to reproduce +982%;
- choosing an exit after seeing validation;
- changing the EMA or the session times;
- dropping years or days;
- opening the holdout to explore.

**A FAIL is final for this signal:** "FAILED — NO AFTER-COST EDGE". There will be no resurrection with
variations.

## A pass would mean

"EDGE FOUND — NASDAQ OPENING-CANDLE EMA SIGNAL" can be claimed only after **all** of these:

- validation passes;
- the holdout passes;
- robustness holds;
- a promotion review.

Even then the status is FORWARD_TESTING (forward demo first), never live. TradeLocker's NAS100 spread
at the open is unmeasured, so costs are provisional.
