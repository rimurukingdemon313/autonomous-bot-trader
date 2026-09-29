# DP-001 — Bounded state x trigger discovery on H1 FX with a three-way chronological split

**Generated from the design and committed before any run on real data.** The registry entry
stores this document's hash, the design hash and the hash of the code that will run; `run()`
refuses if any of them differs. Results are written to `research/knowledge/DP-001.json` and
judged by the rules below, unchanged.

## Question

Does any cell of a declared state x trigger grid (19 features in terciles, both sides), or a boosted-stumps model of 35 features, have positive net expectancy that survives a validation period it never saw and then a frozen battery on a confirmation period — across instruments, years, regimes, costs, delays and bin perturbations?

## Data

- Instruments (12): EURUSD GBPUSD USDJPY AUDUSD USDCAD USDCHF NZDUSD EURGBP EURJPY GBPJPY EURCHF AUDJPY — H1 bid/ask bars built from complete M15 bars.
- The sealed holdout (from 2017-01-01) is not read: the loader truncates there and every
  outcome must resolve inside its segment.

| Segment | Decision dates | Registry role |
|---|---|---|
| discovery | 2007-06-01 → 2011-01-01 | fit |
| validation | 2011-01-11 → 2013-07-01 | select |
| confirmation | 2013-07-11 → 2017-01-01 | judge |

Outcomes never straddle segments (rows whose longest possible outcome would cross the segment end
are purged); consecutive segments are separated by at least 10 days.

## Stage 1 — discovery (fit): a bounded screen

- States (9): er120, vol_ratio, ma_slope, range_pos120, d1_trend, usd_basket, atr_pctile, usd_corr, session
- Triggers (10): r1, r6, r24, bar_body, range_pos24, smc_sweep, bar_range, range_contraction, up_persistence, smc_structure
- Bins: per-instrument terciles fitted on discovery rows only and frozen; declared groups for
  categorical features (session: low=[0.0], mid=[1.0, 2.0], high=[3.0, 4.0]; smc_sweep: low=[-1.0], mid=[0.0], high=[1.0]; smc_structure: low=[-2.0, -1.0], mid=[0.0], high=[1.0, 2.0]).
- Cells: every single feature bin, and every state bin x trigger bin, each for BUY and SELL:
  **1734 tests**, all counted (cells with fewer than 100 trades get p = 1).
- Baseline exit E1; one position per instrument; clustered (weekly) t; one-sided p;
  Benjamini-Hochberg at q = 0.1. The best 20 discoveries by (mean - 2 se)
  become DRAFT hypotheses.

## Stage 2 — validation (select)

- Each draft is evaluated with every declared exit (E1, E2, E3, E4, E5, E6, E7, E8): 160
  configurations at most. It passes with n >= 100, mean R > 0 and t >= 2.0
  for its best exit; the best 5 passing drafts (by t) are the finalists, each with its
  best exit frozen.
- Model family: `stumps` on 35 features, trained on every 4th discovery row per side (target: E1 net R); thresholds at validation-prediction quantiles [0.8, 0.9, 0.95] x exits ['E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8'] x both sides = 48 configurations; the best passing one is judged.

## Stage 3 — confirmation (judge)

At most **6 judged tests**. The significance threshold is frozen now from the
registry (every earlier test on the judged period, plus these): **t >= 3.0781**.
A finalist is VALIDATED only if every check passes:

- **min_trades** — n >= 100
- **significance** — clustered (by week) t >= 3.078
- **beats_random** — Welch t vs random entries >= 2.0 (20 draws)
- **permutation** — circular-shift p < 0.05 (200 shifts)
- **costs_stress** — mean R > 0 with spread x1.5, slippage x2, commission and swap x1.5
- **delay_stress** — mean R > 0 with entry one bar late
- **perturbation** — mean R > 0 with tercile edges moved by -0.05 and +0.05 quantile
- **years** — >= 60% of years with >= 20 trades positive (>= 2 years)
- **instruments** — >= 60% of instruments with >= 20 trades positive (>= 2 instruments)
- **leave_one_out** — mean R > 0 with any one instrument removed
- **regimes** — no regime cell (er120 x vol_ratio, discovery medians) with t <= -2.0; >= 2 cells with >= 20 trades positive
- **outliers** — top 5% of trades carry < 50% of total R

Then the research board (market, opportunity, risk, adversarial, independent reviewer) reads the
result. There is no vote: any blocking objection turns VALIDATED into REJECTED; nothing turns
REJECTED into VALIDATED. The objections that block are declared now:

- risk: any single trade worse than -3R (a gap carried it past its stop; no per-trade
  limit bounds that loss);
- adversarial: one instrument or one year carries more than 60% of the total R while the
  remaining trades earn less than a third as much per trade;
- reviewer: its independent recomputation of n or the clustered t disagrees with the battery; a trade
  lies outside the judged segment or reaches the holdout; two trades overlap on one instrument; the
  exit, the threshold or the design hash is not the one frozen here.

Market and opportunity analysts record concerns only. The deflated Sharpe ratio over all
1948 configurations is reported for information.

## What the outcome means

- PASSED (at least one VALIDATED hypothesis): research knowledge, not a trading rule. The next
  step is a prospective paper test; production is not changed by this program.
- FAILED: a valid negative result. It is recorded, searchable, and counted in every later threshold.

Costs: {"slippage_pips": 0.1, "commission_pips_rt": 0.7, "swap_atr_per_night": 0.05, "spread_multiple": 1.0}. Design sha256 `2761915fe8f4183d0cbd90f324d949555b040c5cb549850e776a73d2317b7340`; code sha256 `0dbca65d79053dcffbddc40a0bb0554460d8b2d7a7eeb5990fa09cc9a6c16e47`.
