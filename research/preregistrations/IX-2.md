# IX-2: intraday momentum into the cash close, equity-index CFDs, last hour (preregistration)

| | |
|---|---|
| Frozen spec | `research/specs/IX-2.json` |
| Spec sha256 | `d171adb10e3e65f70d76014af521e0b26dbc8ea5ded7529a5fb8725aef4b4fc5` |
| Code | `aitrader/research/discovery/ixmom.py` (ix-1.0.0, unchanged since IX-1), `scripts/ix2.py` |
| Run | `python scripts/ix2.py run`, once; `holdout` only for passers |
| Threshold | t ≥ **3.645** on the daily equal-weight book: Bonferroni over all 185 tests this project has registered, plus these 2 |

## Hypothesis and mechanism

The return from the previous cash close to one hour before today's cash close predicts the return over
the last hour, in the same direction. It is the IX-1 rule on a one-hour window.

Gao, Han, Li & Zhou (2018) and Baltussen, Da, Lammers & Martens (2021) find this effect strongest in
**equity indices**. The cause is hedging demand that must trade late and in the direction of the day's
move:

- option dealers who are short gamma;
- leveraged and inverse ETFs rebalancing at the close.

Baltussen et al. report that it persisted after publication and across more than 60 futures markets.

## Relation to IX-1 (gold, silver: FAILED)

IX-1 was judged on the metals, where the literature reports the effect is weakest. It failed:

- gold's gross edge was about 0.6–1.3 bp against about 3 bp of cost;
- silver's spread is prohibitive.

IX-2 is the market class where the mechanism is reported to be strongest. **No index data has been
loaded or looked at by this project at any horizon below one day.**

The RC programs used daily closes of some of these indices (universes A and B) for unrelated calendar
and trend rules. Those tests are in the count above.

## Why hour bars, and why these six indices

The probe (`research/results/ix-probe.json`, availability only) showed the datafeed delivers about one
file a minute to CI runners. Minute candles over nine years are therefore impractical, so hour candles
are used.

With hour bars, only indices whose cash close falls on the hour can be judged without misalignment:

| CFD | Cash close |
|---|---|
| USA500IDXUSD (S&P 500) | 16:00 New York |
| USATECHIDXUSD (Nasdaq-100) | 16:00 New York |
| USA30IDXUSD (Dow) | 16:00 New York |
| JPNIDXJPY (Nikkei 225) | 15:00 Tokyo |
| HKGIDXHKD (Hang Seng) | 16:00 Hong Kong |
| AUSIDXAUD (ASX 200) | 16:00 Sydney |

The European indices close at :30 and are excluded rather than misaligned. The three US CFDs are close
to one market; the instruments gate below counts them separately, so this is stated rather than hidden.

## Rules

| | |
|---|---|
| Judged period | 2012-01-01 → 2021-01-01, as far as each CFD's history reaches (USA30 and AUS from about 2014). The first 60 trading days build the volatility estimates. There is no development period: the rule has nothing fitted to index data |
| Signal | s = mid(C − 1 h) / mid(previous day's C) − 1, using the quote at the open of the hour bar starting at C − 1 h |
| Trade | Direction of s, entered at that bar's open (ask + slippage / bid − slippage). Exit at the open of the bar starting at C |
| Variants | ALL (every day); STRONG (\|s\| > 1 × the standard deviation of the previous 60 signals) |
| Stop | 2.5 × the standard deviation of the previous 60 last-hour returns, at least 3 spreads; checked against the entry hour's range |
| Costs | Real quoted bid/ask at entry and exit. Slippage per fill = ¼ of the instrument's median quoted spread. No commission (index CFDs are spread-only). No financing: flat before the 17:00 New York rollover |

## Gates (each test must pass all)

| Gate | Requirement |
|---|---|
| min_trades | ≥ 300 |
| net_bps | > 0 at base costs |
| t_day | ≥ 3.645 |
| costs_x1.5 | net > 0 |
| costs_x2 | net > 0. Failing it is FRAGILE, which fails |
| late_entry | net > 0 when entering at the typical price (O+H+L+C)/4 of the entry hour, on the adverse side of the spread. This stands in for the delay test: a one-bar delay on hour bars would enter at the close. It approximates entering at a random moment in the hour, which is harsher than a 5-minute delay |
| halves | both chronological halves net > 0 |
| instruments | ≥ 60% of instruments with ≥ 50 trades net > 0 |
| profit_factor | ≥ 1.05 on R |
| top_year_share | no calendar year > 50% of the total net |

**Reported, not gated:**

- trades per month;
- profitable rolling 3-month windows;
- maximum drawdown in R;
- by year and by instrument.

## Holdout

2021-01-01 → 2025-01-01. Those bars are not fetched unless a test passes, and the holdout is judged
once.

Holdout gates:

- net > 0;
- t ≥ z(1 − 0.05/k) for k passers;
- net > 0 at costs × 1.5;
- net > 0 with late entry.

## AI

None. This is a deterministic rule: Track A only.

## What a pass would and would not mean

A pass here and on the holdout would make IX-2 **FORWARD_TESTING**, not VALIDATED. All of these would
still be required:

- forward demo performance;
- independent review;
- clean reproduction;
- consistency with demo execution;
- a human promotion record.

TradeLocker's index-CFD spreads are unmeasured, so every cost here is provisional.

**A FAIL ends this hypothesis for these markets.** There will be no re-run with another window,
threshold or stop.
