# R3 — Genuine interest-rate information and FX carry

Does point-in-time interest-rate information (the level, change, acceleration of the policy-rate differential, and policy moves) improve directional prediction on the FX pairs, and does carry (spot + RATE-DIFFERENTIAL CARRY PROXY - financing - costs) have positive net expectancy?

Hypotheses (one judged test each), bins fitted on 2007-04-02 → 2008-07-01, judged on 2008-07-11 → 2017-01-01 with t >= 3.3506 and every battery check:

- **R3-A** (opportunity, human): buying a pair whose base out-yields its quote by >= 1pp (carry long) has positive net expectancy — `rate_level=high` BUY, exit D4
- **R3-B** (opportunity, human): selling a pair whose quote out-yields its base by >= 1pp (carry long via the quote) has positive net expectancy — `rate_level=low` SELL, exit D4
- **R3-C** (opportunity, human): after the differential widened >= 0.25pp in the base's favour over 91 days, buying has positive net expectancy — `rate_change=high` BUY, exit D4
- **R3-D** (opportunity, human): after the differential narrowed >= 0.25pp over 91 days, selling has positive net expectancy — `rate_change=low` SELL, exit D4
- **R3-E** (opportunity, human): when the widening of the differential accelerates (>= 0.25pp), buying has positive net expectancy — `rate_accel=high` BUY, exit D4
- **R3-F** (opportunity, human): after a policy move in the base's favour within 30 days (base hike or quote cut, >= 0.10pp), buying has positive net expectancy — `policy_move=high` BUY, exit D4
- **R3-G** (opportunity, human): carry long (>= 1pp) only while VIX < 20 has positive net expectancy — `rate_level=high&vix_state=low` BUY, exit D4
- **R3-H** (opportunity, human): carry long (>= 1pp) only when neither central bank moved in the last 30 days has positive net expectancy — `rate_level=high&policy_move=mid` BUY, exit D4

- min_trades: n >= 100
- significance: clustered (by week) t >= 3.351
- beats_random: Welch t vs random entries >= 2.0 (20 draws)
- permutation: circular-shift p < 0.05 (200 shifts)
- costs_stress: mean R > 0 with spread x1.5, slippage x2, commission and swap x1.5
- delay_stress: mean R > 0 with entry one bar late
- perturbation: mean R > 0 with tercile edges moved by -0.05 and +0.05 quantile
- years: >= 60% of years with >= 20 trades positive (>= 2 years)
- instruments: >= 60% of instruments with >= 20 trades positive (>= 2 instruments)
- leave_one_out: mean R > 0 with any one instrument removed
- regimes: no regime cell (er120 x vol_ratio, discovery medians) with t <= -2.0; >= 2 cells with >= 20 trades positive
- outliers: top 5% of trades carry < 50% of total R

Design sha256 `c85979b216fe7dea77eed63fd13b7c1a4dbd88ca16b545328232b16bdeb607f7`; code sha256 `e718bbec4e743e3dd7a14f05d40bc3718906eacbd08cf2fa7a28989bfc369681`.

## Stated before the run (feature values only; no outcome read)

- Data: BIS WS_CBPOL daily policy rates (official bulk file supplied by the user; CSV sha256
  4f7e117017ce7fda7775c9a4f63753115a30b24a2a3bb18270ead31791708e5a), validated against published values.
- Qualifying pairs (frozen universe rule: both currencies covered over the whole period): EURUSD, GBPUSD,
  AUDUSD, USDCAD, USDCHF, NZDUSD, EURGBP, EURCHF. JPY is NOT covered: BIS publishes no Japanese policy rate
  from 2013-04-04 to 2016-09 (the BoJ targeted the monetary base under QQE); under the declared staleness
  rule (a daily rate older than 7 days is not carried forward) that gap stays a gap, so the four JPY pairs
  are excluded. Nothing is substituted.
- Share of judged days each condition holds, per pair: R3-A is concentrated in AUDUSD and NZDUSD (99-100%)
  and rare elsewhere; R3-B holds on 0-6% of days (it may fail min_trades); R3-F on 1-7% (it may fail
  min_trades); R3-G and R3-H are dominated by AUDUSD and NZDUSD. The frozen design is run as registered.
