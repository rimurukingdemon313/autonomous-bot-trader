# IX-1: intraday momentum into the COMEX settlement, gold and silver (preregistration)

| | |
|---|---|
| Frozen spec | `research/specs/IX-1.json` |
| Spec sha256 | `089e4b7353d5bc1d52f5eafe0e7ab3761c893fea5f6aaaa2797fb6444c8c8bfc` |
| Code | `aitrader/research/discovery/ixmom.py` (ix-1.0.0), `scripts/ix1.py` (hash in the spec) |
| Tests | `tests/unit/test_ixmom.py`: 10 behaviour tests on constructed scenarios |
| Run | `python scripts/ix1.py run`, once; `holdout` only for passers |
| Threshold | t ≥ **3.6422** on the daily book: Bonferroni over all 183 tests this project has ever registered, plus these 2 |

## The hypothesis and why it should exist

The return from the previous settlement to 30 minutes before today's settlement predicts the return over
the last 30 minutes, in the same direction.

**Economic mechanism.** Gao, Han, Li & Zhou (2018, JFE) and Baltussen, Da, Lammers & Martens (2021, JFE)
document intraday momentum in more than 60 futures markets, commodities included. The cause is hedging
demand that must trade late and in the direction of the day's move:

- option dealers who are short gamma;
- leveraged and inverse products that rebalance into the close.

That flow is mechanical and carries no information. Better-informed traders could absorb it but have no
reason to remove it, so it can persist after publication. Baltussen et al. report that it did.

## What was seen before this was written

All of it is registered as tests and counted in the threshold:

- **EX-1** (21 looks) and **EX-2** (4 looks) on fx-majors 2007–2012.
- **EX-2 included gold into the COMEX close on 2011-05 to 2012-12:**
  - every day: gross +3.0 bp, net +0.1 bp, t 0.09 (351 trades);
  - on days with |signal| > 1 sd: gross +7.8 bp, net +4.7 bp, t 1.58 (94 trades).
- **The same gold data was used to smoke-test this runner.** At M5 with a 5-minute delay, the strong
  variant was net +2.3 bp.
- FX into the CME settlement showed no gross edge.
- **Silver** has never been looked at.
- **2013–2016** has never been used for this hypothesis, for either metal.

The development evidence is short and weak. This preregistration exists to judge the hypothesis on data
that played no part in choosing it, not to confirm what 1.6 years of gold appeared to show.

## Rules (`ixmom.trades`)

| | |
|---|---|
| Instruments | XAUUSD (settlement 13:30 New York), XAGUSD (13:25 New York), Dukascopy bid/ask M5 bars built from the FX-Data tick mirror |
| Validation | 2013-01-01 → 2017-01-01; the first 60 trading days of the period build the volatility estimates |
| Signal | s = mid(C − 30 min) / mid(previous day's C) − 1, using the quote at the open of the bar starting at C − 30 min |
| Trade | Direction of s, entered at that bar's open (ask + slippage for a buy, bid − slippage for a sell). Exit at the open of the bar starting at C |
| Variants | ALL: every day with s ≠ 0. STRONG: \|s\| > 1 × the standard deviation of the previous 60 signals |
| Protective stop | 2.5 × the standard deviation of the previous 60 last-30-minute returns (never closer than 3 spreads). Checked bar by bar on the closing side, gaps filled at the open |
| Costs (base) | Real quoted spread at entry and exit. Slippage per fill: 0.1 pip (gold $0.01, silver $0.0001). Commission per round trip: 0.7 pip (gold $0.07, silver $0.0007) |
| Financing | None: flat before the 17:00 New York rollover |
| Book | Equal weight per day across the metals that traded. t is computed on daily book returns |

## Gates (validation; each test must pass all)

| Gate | Requirement |
|---|---|
| min_trades | ≥ 200 |
| net_bps | > 0 at base costs |
| t_day | ≥ 3.6422 |
| costs_x1.5 | net > 0 with every cost × 1.5 |
| costs_x2 | net > 0 with every cost × 2. Failing it is FRAGILE, which fails |
| delay | net > 0 when entering one bar (5 minutes) later |
| halves | both chronological halves net > 0 |
| instruments | ≥ 60% of instruments with ≥ 50 trades net > 0, and at least 2 such instruments: **both metals must be positive** |
| profit_factor | ≥ 1.05 on R |
| top_year_share | no calendar year > 50% of the total net |

**Reported, not gated:**

- trades per month;
- profitable rolling 3-month windows;
- maximum drawdown in R;
- by year and by instrument.

## Holdout

The holdout is fx-majors from 2017-01-01: XAUUSD and XAGUSD through 2018-06. It is opened only for
validation passers, and only once.

This is the first post-seal use of that universe's holdout. Opening it **spends it for every future FX
and metals program**, and that consequence is accepted only for a validation passer.

The M5 bars for 2017–2018 are built only after a passer exists.

Holdout gates:

- net > 0;
- t ≥ z(1 − 0.05/k) for k passers;
- net > 0 at costs × 1.5;
- net > 0 with the one-bar delay.

## AI

None. This is a deterministic rule. Track A is the only track, and nothing here is model-ranked.

## What a pass would and would not mean

**A validation and holdout pass would make this FORWARD_TESTING under `aitrader/research/promotion.py`,
not VALIDATED.** Every one of these is still required before promotion:

- forward performance;
- independent review;
- clean reproduction;
- demo consistency;
- a human promotion record.

**A pass says nothing about TradeLocker's actual metal spreads.** They are unmeasured, so every cost
here is provisional.

**A FAIL ends this hypothesis for metals.** There will be no re-run with a different offset, threshold
or stop.
