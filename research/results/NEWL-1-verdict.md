# NEWL-1: the verdict, and why it failed

**FAILED, as registered.** Written on 2026-11-15 by the research director, after the runner recorded the verdict.
Nothing in the frozen code, the specification or the rules was changed, and nothing was run again to judge it.
The record is `research/knowledge/NEWL-1.json` (every event); the registration is `research/preregistrations/NEWL-1.md`.

What is a fact read from the record, what is a calculation made on it afterwards, and what is an opinion are kept
apart below. Calculations after the verdict are descriptive: they explain the result, and none of them is a test.

## 1. Was the registered test the one that ran (facts)

| Check | Found |
|---|---|
| Registered before any price was read | Trial registered 2026-11-15 18:05:57 UTC (`research/registry.jsonl`, commit `0c8c0c1`). The run started at 18:15:35. The data branch `newl-data` did not exist before the run (its log: `couldn't find remote ref newl-data`), and the probe before it read file names only |
| The run | Run 3 of `newl1.yml` (id 43745730524), `workflow_dispatch`, on `0c8c0c1`; step "Run" 18:15:48 to 18:35:06 UTC. The runner committed the records itself (`9842369`) and the data to `newl-data` (`98dfd33`) |
| Code and specification | Code sha256 `93b172270747d50807d7c7ff0443e64e9b12e10aef57f9b15e328fee703b3b44`, spec sha256 `ee2fc3d6b82d0060560ffacd7c116db18861b0324edb9e2e5b6a0aaae1590930`: the same in the record, the registry and the preregistration, and recomputed from `main` afterwards. The frozen files did not change between `0c8c0c1` and `9842369`. `run()` refuses to judge when either differs |
| One look | `run()` refuses a stage that already has a verdict. This one has |
| The bar | max(3.0, Bonferroni over the tests on `crypto-perp-new-listings`): one test, so 3.0 |
| Data | Binance's public archive (`data.binance.vision`, USDT-M monthly files), fetched on GitHub's runner: 21,248 files asked for, 20,814 received, 434 not in the archive, none failed (a failure stops the run before any judgement) |
| Nothing after the stage | Last day read 2026-10-31, and the last day stored, for prices and for funding, is 2026-10-31 |
| Reproduced | All 812 event outcomes were recomputed afterwards from the stored data with the frozen functions: every one equals the record, and so does the mean (-0.001047) |

## 2. The sample (facts)

- 1,080 contracts in the archive; 915 are the first contract on their coin; **812** of them were entered between
  2021-01-01 and 2026-09-30. All 812 had an entry price and a basket of at least three seasoned contracts: none was
  dropped. They form **67 monthly cohorts** (no listing was entered in 2022-11 or 2022-12).
- 103 eligible listings fall outside the entry window (first seen in 2020, or entered after 2026-09-30).
- Of the 434 archive months that do not exist, 195 fall inside a window the test used, nearly all of them funding
  files of basket members (section 5).
- One event ended a day early: DOTECOUSDT, whose last close is 2021-02-19.
- Declared before the test and unchanged: only 40 of the 915 eligible contracts stop before 2026-10, so the archive may
  not keep every removed contract. Removed contracts are mostly ones that collapsed, which favours the short: their
  absence biases the test against the hypothesis, not for it.

## 3. The result (facts, from the record)

The statistic is the mean over monthly cohorts of each cohort's mean outcome: short the new contract at the close
of its first full day, hold 30 days, against an equal-weight long basket of contracts listed 181 to 365 days
earlier, after funding on both legs and four fills of 15 bp, per unit of short notional.

| Figure | Value |
|---|---|
| Mean, net of everything | **-0.105%** |
| Before the fills (after funding) | +0.495% |
| With the fills doubled | -0.705% |
| Newey-West t (lag 1) | **-0.011**, against a bar of 3.0 |
| Its standard error | 9.26 points |
| 95% interval (normal) | **-18.2% to +18.0%** |
| p, one-sided (mean above zero), t with 66 degrees of freedom | 0.50 (two-sided 0.99) |

| Gate (all required) | Required | Value | |
|---|---|---|---|
| t | at least 3.0 | -0.011 | FAILED |
| Costs doubled | above 0 | -0.705% | FAILED |
| Both halves | each above 0 | +10.45% (2021-01 to 2023-11), -10.34% (2023-12 to 2026-09) | FAILED |
| Five best events removed | above 0 | -0.414% (PUMP, KERNEL, PROMPT, XCN, INIT) | FAILED |
| One day late | above 0 | +1.760% | passed |
| Beats 1,000 random placebos | above their 95th percentile, 3.21% | -0.105%: 48.4% of the placebos did as well or better | FAILED |
| Best year (2026) removed | above 0 | -0.528% | FAILED |

**Six of seven gates failed.** The sample was large enough to decide (60 events and 18 months were the minimum).

## 4. Why it failed (calculations on the record, after the verdict)

**The typical new listing did fall against the seasoned basket. The average did not, because of the losses the rule
left unbounded.**

| | Mean | Median | Positive |
|---|---|---|---|
| Outcome per event (812) | -13.1% | **+15.7%** | 71.2% |
| The short alone | -17.1% | +11.5% | 66.3% |

| Entry year | Events | Mean | Median | Positive |
|---|---|---|---|---|
| 2021 | 58 | +25.0% | +29.8% | 84% |
| 2022 | 28 | -0.6% | +12.1% | 75% |
| 2023 | 94 | +0.8% | +18.2% | 77% |
| 2024 | 130 | +9.0% | +21.4% | 75% |
| 2025 | 239 | -61.9% | +19.0% | 70% |
| 2026 | 263 | +5.7% | +8.1% | 65% |

- **The tail.** A quarter of the events lost 3.4% or more, a twentieth lost 75.7% or more, and 29 events lost more
  than the short's whole notional (together -225 notional units); 72 lost more than half of it. They are the
  squeezes on new contracts that a short is exposed to: BEAT (+407% in its 30 days), HEMI, 1000BONK, BSB, GMT
  (2022-03), GAS (2023-10) and ORDI (2023-11) among them.
- **One event outweighs the rest.** COAIUSDT, listed 2025-09-25, closed at 110 times its entry price at its peak (2025-10-16) and
  ended its window 31.7 times its entry price. Its funding was deeply negative, so the short paid it, and the
  registered rule holds a fixed quantity, so the funding was charged on a notional that grew with the price:
  -135.25 notional units of funding and +30.73 of price, an outcome of **-166.2**. Its cohort (2025-09, 30 events)
  averaged -574%. The registered rule has no stop and no liquidation, which the preregistration declared: no real
  account could have carried this position, and one would have been liquidated near a doubling.
- **Where the mean went.** Split over the cohort mean: the short's price move +3.90 points, the short's funding
  -7.51 (COAI alone -6.73), the basket after its fills +3.81, the short's fills -0.30.
- **The placebos.** A random seasoned contract shorted in place of the new one did as well as the new one in 48.4%
  of 1,000 draws: as registered, the listing added nothing a random contract did not.
- **The halves** have opposite signs: 2021-2023 positive, 2023-12 to 2026-09 negative, COAI's cohort inside the
  second.
- **The basket's own outlier.** In April 2025 one basket member, ALPACAUSDT, rose 3,181% in 30 days, with a one-day
  move of 6.2 times on 2025-04-30. It lifted the five events entered 2025-04-09 to 04-17, which the "five best
  removed" gate takes out. Whether that move is real or an error in the archive was not checked.

Excluding COAI's cohort after the fact, the other 66 cohorts average +8.6%. **This is not a result and cannot
become one.** Removing the worst outcome after seeing it is the choice the registry exists to prevent, the tail is
the risk this rule carries rather than noise in it, and 28 other events also lost more than their notional. A short
with a stop or a liquidation is a different rule: these 812 events cannot test it, because it would be designed
after seeing them.

## 5. What the audit found in the data and the design (calculations and facts)

None of these can turn the verdict: the t gate needs the mean to rise by 27.8 points, and the nearest failed gates
(five best removed, best year removed) by 0.41 and 0.53.

1. **A day without a funding record pays no funding** (`funding.get(d, 0.0)` in the frozen code). The
   preregistration does not say so. It applied to 90 of the shorts' 24,359 position-days and to 111,632 of the
   baskets' 1,921,081 (5.8%), mostly where a basket member's monthly funding file is not in the archive. Giving
   each of the 8,482 contract-days without a record that day's median funding across contracts moves the mean from
   -0.105% to -0.085%.
2. A day without a close carries the last close forward (9 short position-days, 177 in baskets).
3. **The exclusion list missed an index.** DOTECOUSDT, counted as a listing, is Binance's Polkadot-ecosystem
   composite index contract (Binance's announcement of 2021-01-20, found by a web search; the page was not opened).
   Its outcome was +51.2%; without it the mean would be -0.34%, lower.
4. **It probably excluded a coin.** ALTUSDT was refused as an index. Its archive begins in 2024-01, the month
   AltLayer (ALT) was listed at Binance, and no Binance index of that name was found: it is most likely AltLayer's
   own contract, an eligible listing left out. Its prices were never fetched. One event added to its six-event
   cohort could raise the mean by about 0.24 points at most.
5. **The event mixes two things.** "The first contract on a coin" counts new tokens and old coins getting their
   first perpetual alike (ANKR, CHZ, SAND and LUNA in 2021-01, for example). It was declared as the definition, but
   the supply-overhang mechanism concerns only new tokens, so it dilutes the test in 2021-2023.
6. **A mistake in the forward stage, moot.** NEWL-1-F, frozen in the same code, could never have passed: its entries
   span seven calendar months, and the same specification requires 18 monthly cohorts, so it would have been judged
   INCONCLUSIVE by construction. The history failed, so it was never registered. Had the history passed, it would
   have had to be found and corrected before any of its data existed. The tests covered its refusals, not whether
   its sample could reach the minimum.

## 6. What follows

- **The verdict stands as recorded.** The stage cannot be judged again (`run()` refuses), and nothing is re-run.
- **NEWL-1-F is not registered and will not be:** it was conditional on a pass.
- **These 812 events, entered 2021-01 to 2026-09 with prices to 2026-10-31, are spent** for any rule about new
  listings: they cannot validate a variant of this one.
- **No successor is registered.** A short of new listings with a liquidation or a stop would be a new hypothesis,
  formed after seeing these data. It could be judged only on listings made after its registration, and at 20 to 30
  listings a month an 18-cohort minimum would take a year and a half to reach.
- My opinion, not a measurement: I do not recommend registering one now. The median is positive in every year, but
  the squeezes are the same mechanism's other face (shorts crowd into thin new floats and are squeezed, and the
  shorts paid funding on average), and the typical gain is shrinking (median +8.1% and 65% positive in 2026,
  against +29.8% and 84% in 2021).

Nothing here is deployed, and no money was spent: the data are free and public, and the runner is GitHub's.
