# RC-FX: the FX factor composite and COT as a low-frequency filter (preregistration)

**Written, frozen and committed before any RC-FX return was computed.** Design and diagnosis:
`docs/RETAIL_RESEARCH_PROGRAM.md`.

| | |
|---|---|
| Frozen spec | `research/specs/RC-FX.json` |
| Spec sha256 | `ac4afb159f53a4030ebf973872af2acdf370ad13aa5731ecfb06bb8c8dce9641` |
| Code | `aitrader/research/discovery/retail.py`, `aitrader/research/discovery/rc.py`, `scripts/rc_fx.py` (hash in the spec) |
| Data | H.10 primary vintage (2018-10-17; holdout-truncated at 2017), BIS policy rates (`data/rc/policy_rates.csv`), CFTC TFF (`data/cot`) |
| Holdout | the project's fx-majors holdout (`research/holdout.json`, 2017-01 onward). Opened once, only for a passing X1 |

## What was known before writing this

- **Earlier FX results.**
  - Carry, momentum, value and one-week reversal were each tested on H.10 2000–2007 as weekly
    ICs (RV-1). Only carry passed, and it then failed with costs in 2008–2016 (RV-1-S2).
  - Cross-sectional momentum (XS-001), trend (CP-001, R2D) and COT as a one-week trigger (COT-1)
    all failed.
  - DIV-2 read H.10 currencies 1990–2018 inside a multi-asset trend portfolio, including
    2017-01 → 2018-10. That 2017–2018 read was registered under another universe name; it is
    declared here.
- **The combination of the three factors was never computed.** Neither was COT as a filter on
  monthly trend.
- **No RC-FX return.** The only real-data computation before writing was coverage counting:
  - fixings per currency;
  - the share of days with a policy rate;
  - whether a COT percentile exists at a date.

## X1 COMPOSITE (judged 1990-01 → 2016-12; development 1990–2003, validation 2004–2016, modern 2009–2016)

**At the first H.10 fixing of each month**, using fixings up to two before it (a fixing is public at
17:00 New York the next business day), score each currency with a policy rate public the previous
day. The cross-section is the seven currencies plus USD:

- **carry**: its policy rate;
- **momentum**: log change from 252 to 21 fixings ago (12-1);
- **value**: −(log level now − mean log level over fixings 4.5–5.5 years ago). Nominal (no
  price-level data), as in Asness, Moskowitz & Pedersen's proxy.

**Composite and positions.**

- The composite is the mean of the three centred cross-sectional ranks.
- Long the top 2 currencies and short the bottom 2, ±1/4 each against USD. USD in a set takes no
  position.
- At least 6 eligible currencies are required; otherwise flat.

**Grid:** momentum {126, 189, 252} × value centre {4, 5, 6 years} × k {2, 3} (18 cells).

## X2 COT-FILTER (judged 2007-04 → 2016-12; halves split at 2012)

**Base rule:** each currency long (short) against USD, 1/7, when its 252-fixing change is up
(down), monthly.

**Filter:** a position is removed when leveraged funds are already crowded in its direction. The
percentile is COT-1's definition (leveraged-money net / open interest, ranked against the 52 weeks
before it), public by 17:00 New York the day before the fill:

- remove a long when the percentile is ≥ 0.90;
- remove a short when it is ≤ 0.10.

**Grid:** lookback {126, 252} × threshold {0.80, 0.90, 0.95}.

## Costs (retail; `docs/RETAIL_RESEARCH_PROGRAM.md` §C)

- **Spread:** ECN raw spreads (EUR 0.2, AUD 0.3, JPY 0.3, others 0.5 pips).
- **Commission and slippage:** 0.7 pip per round trip, plus 0.1 pip per fill.
- **Swaps:** the policy-rate differential minus a 1.5% a year markup on notional. Not held where
  either rate is unknown (JPY in the BoJ's no-rate years).
- **Costs ×2:** doubles everything.

## Gates

1. t ≥ max(3.0, the registry's fx-majors Bonferroni value), recorded in the spec.
2. Mean net > 0 in development and in validation (X2: in both halves).
3. Mean net > 0 in 2009–2016.
4. Costs ×2 > 0.
5. One-fixing delay > 0.
6. Leave-one-currency-out > 0.
7. No year supplies more than 30% of the sum of positive years.
8. At least 75% of the grid has a mean net > 0, and the grid's median t is ≥ 2.0.
9. Maximum drawdown ≤ 30%.
10. **X2 only, value added:** the mean monthly (filtered − unfiltered) is > 0 with paired
    t ≥ 2.0; it is > 0 in both halves and in ≥ 75% of the grid.

**Classes.**

- **X1:** HOLDOUT_ELIGIBLE if every gate passes, else REJECTED.
- **X2 is never holdout-eligible.** Its base (monthly FX trend) is already rejected, and
  2007–2016 is too short to prove an absolute edge. It is PROMISING if value_added passes and its
  own mean net is > 0 (COT then deserves its own preregistered study), else REJECTED.

## Holdout (fx-majors, 2017-01 → 2026-09, once, X1 only if eligible)

- **Data:** H.10 vintage 2026-09-29. It stores EUR, GBP, AUD and NZD as inverses rounded to 4
  decimals, which is at most ≈ 0.6 bp per fixing, declared.
- **Pass:** t ≥ z(0.95) and mean net > 0 in 2017–2021 and in 2022–2026, with costs ×2 > 0.
- **Single use.** Opening it spends the project's last FX holdout.

## Power, stated in advance

Over 324 months, a t of about 3.4 needs a net Sharpe of about 0.65. The published FX
value + momentum + carry combination is of that order before costs and much weaker after 2008.
A fail is likely.
