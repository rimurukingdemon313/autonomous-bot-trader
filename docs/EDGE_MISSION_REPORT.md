# Edge mission report (2026-10, from commit 693ea9b)

The mission: find out why the system is not profitable, and find a real, defensible edge in
the data available to this repository, or prove with numbers that the data cannot support
one. No historical result was edited. The FX holdout (2017+) is still sealed.

## 1. Did we find a profitable edge?

**NO.** No candidate passed the preregistered gates, so no holdout was earned. The data in this
repository does not contain a directional signal strong enough to prove after realistic costs.
That conclusion rests on the quantified evidence in §2. The one candidate with the strongest prior
evidence in the literature, diversified trend following (DIV-1), cannot be tested here because
the network is blocked. It is now preregistered, frozen and runnable with one command wherever
the data is reachable (§3).

## 2. What was causing the previous losses (quantified)

| # | Cause | Evidence |
|---|---|---|
| 1 | **There is no gross directional information in the price data at the horizons tested.** | H1 gross expectancy of every declared entry/exit is within ±0.03R (DP-001). If trading were **free**, the best gross t across every judged hypothesis is **2.27** (FLOW1-H2), then 1.57 (CP-001-T2), 1.48 (CP-001-T4) and 1.22 (CP-001-T3), against required t of 3.18–3.43. None of the 58 rejected hypotheses would pass even with zero costs. |
| 2 | **Costs are larger than every gross edge measured.** | H1 costs 0.09–0.21R per trade, D1 about 0.10R. FLOW-1 costs 1.8–2.3 bps per round trip against gross effects of −0.17 to +2.46 bps. The London 4 p.m. fix fade has **zero** gross effect: +0.06 bps a day, t 0.3. Its net t of −11.6 is pure cost. |
| 3 | **The live risk check under-counted costs.** | The spread-to-stop check ignored commission (0.7 pip) and slippage (0.1 pip per fill). A 5-pip EURUSD stop with a 0.6-pip spread passed it at 12% while really paying 1.5 pips, **30% of R**. That needs a gross edge larger than any this project has measured. **Fixed in risk-1.1.0** (§3). |
| 4 | **Too little data to prove a normal-sized edge.** | The FX history covers about 9.75 years, with 79–85 earlier tests on the same period. The registry's Bonferroni threshold therefore needs an annual Sharpe of **1.16**. A genuine professional-grade edge (Sharpe 0.5) would pass only **2.6%** of the time; Sharpe 1.0 only 32%. |
| 5 | **The multi-agent pipeline (PR-001) filters, but has nothing to filter for.** | −0.053R (memory) and −0.072R (memory + learning) per trade, against −0.159R for random entries through the same pipeline. The filters add +0.087R over random (t 2.65): this project's only positive finding, and still below zero. Learning added −0.019R (t −0.53). |
| 6 | **How the trades lost.** | Loss forensics of 12,703 judged trades: on D1, WRONG_DIRECTION 30% and NORMAL_VARIANCE 35% of R lost; on H1, ENTRY_TIMING 34% and STOP_TOO_TIGHT 25%. Winners routinely went −0.40R first and losers +0.36R first. That is the signature of a price path with no direction, not of a fixable timing error. |
| 7 | **Data defect: hour 00 UTC is missing.** | The GitHub mirror of Dukascopy ticks has no `00h` files for 12 of 13 instruments (only EURUSD is complete). That is 4.2% of hours, and it is the Tokyo fix hour itself. H1/H4/D1 bars still exist, without that hour. A stop or target touched only inside 00:00–01:00 UTC was seen one bar late, a small bias. It cannot explain the absence of an edge. |
| 8 | **AI.** | A language model trained on text written after a date "knows" what happened next, so it cannot be backtested honestly. It has no historical evidence of value. Its value can only be measured forward, against the deterministic baseline, which the forward ledger now does (`/api/evidence`). Until then it holds no authority beyond proposing or vetoing, labelled EXPERIMENTAL. |

## 3. What changed

**Research**

- **FLOW-1**, a new information source: scheduled order flow at the Tokyo gotobi fix and the
  London 4 p.m. fix.
  - Preregistered (commit c9eddd3) before any outcome.
  - Judged once: **REJECTED**, 4 of 4.
  - Holdout not opened.
- **DIV-1**: diversified time-series momentum on 19 multi-asset ETFs.
  - Frozen, registered, with its own sealed holdout from 2021.
  - Fetcher and judge built (`scripts/div1.py`).
  - Not runnable from this container (proxy 403 on every market-data host).
- **Edge registry** (edges-1.5.0) reads scheduled-flow programs: 58 REJECTED.
- **Loss-cause quantification, zero-cost counterfactual:** §2, cause 1.

**Live system**

- **Risk engine risk-1.1.0.** The whole round-trip cost (spread + commission + slippage on both
  fills) must be ≤ 25% of the stop distance. Before, only the spread counted.
  `RISK_MAX_COST_TO_RISK` can only lower it.
  - It removes trades that are structurally unprofitable given every gross edge measured, mostly
    the M1/M5 scalps the model traders could propose.
  - It is a hard constraint; no AI can override it.

**Not changed, deliberately**

- No historical strategy was resurrected or re-tuned. The trend shorts with positive means
  (CP-001-T2/T4, t ≈ 1) stay REJECTED: re-testing them on the same data would be curve-fitting.
- SMC is neither kept nor removed on faith. Every SMC- and structure-based rule tested so far was
  rejected, and the evidence does not support adding it to a validated strategy, because none exists.

## 4. What is the new strategy?

**There is no validated strategy, so none is promoted.**

The live system runs exactly as before, on paper or demo, labelled EXPERIMENTAL, with a stricter
cost ceiling. The best-supported **candidate** is DIV-1:

- once a month, hold every asset (stock indices, bonds, commodities, currencies) in the direction
  of its last 12 months' trend;
- size each to the same risk;
- across 19 markets at once.

It is a candidate, not a strategy, until its frozen test passes.

## 5. Historical results (FLOW-1, judged 2007-04 → 2016-12, after all costs)

Units are basis points of the entry mid per observation.

| Hypothesis | Trades | Gross | Costs | Net | t (net) | Win rate | Max drawdown |
|---|---|---|---|---|---|---|---|
| H1 Tokyo gotobi, long before the fix | 696 | +0.71 | 2.04 | −1.33 | −1.68 | 44.5% | see artifact |
| H2 Tokyo gotobi, short after the fix | 696 | **+2.46 (t 2.27)** | 1.81 | +0.65 | +0.60 | 53.0% | see artifact |
| H3 London fix fade, month-end (7 USD pairs) | 117 days | −0.17 | 2.27 | −2.44 | −3.13 | 38.5% | see artifact |
| H4 London fix fade, other days | 2,419 days | +0.06 | 2.26 | −2.20 | −11.59 | 36.3% | see artifact |

- **Breakdowns.** Long/short, per-pair, per-year and leave-one-out breakdowns are in
  `research/knowledge/FLOW-1.json`. H3 was negative on 6 of 7 pairs (only USDCHF +1.0); H4 was
  negative on all 7.
- **Profit factor.** Not computed, because these are continuous returns rather than R trades.
- **Whole project.** 58 hypotheses rejected and 0 validated (docs/TRADING_EDGE_REGISTRY.md).

## 6. Out-of-sample results (FLOW-1 development vs validation, net bps)

| Hypothesis | Development 2007-04..2011 | Validation 2012..2016 |
|---|---|---|
| H1 | −1.04 | −1.59 |
| H2 | +0.60 | +0.69 |
| H3 | −4.13 | −0.84 |
| H4 | −2.57 | −1.84 |

H2 is positive in both halves, but each half is far from significant, and it fails costs ×2 and
specificity (Welch t 0.58 against non-gotobi days).

## 7. Untouched holdout results

**None: no candidate earned the holdout.** The FX holdout (2017-01 → 2018-05) and the DIV-1
holdout (2021+) are both still sealed. Opening a holdout for a candidate that failed its gates
would spend the only untouched evidence on a known loser.

## 8. Robustness

**Costs doubled (FLOW-1, net bps):**

| Hypothesis | Net, costs ×2 |
|---|---|
| H1 | −3.37 |
| H2 | −1.16 |
| H3 | −4.71 |
| H4 | −4.46 |

Nothing survives realistic costs doubled. The by-year and by-pair breakdowns show no regime in
which the fix effects are reliably positive.

## 9. Why should an edge exist (and why none was found here)?

- **The fix effects (FLOW-1).** Scheduled benchmark orders are real, and the literature documents
  them. Our data shows no exploitable London effect in either half of 2007–2016, before and after
  the 2015 widening of the fix window. Net means of −2.57 and −1.84 bps against about 2.3 bps of
  costs put the gross fade near zero in both halves. The documented pre-fix pressure is either too
  small to capture with M15 bars and a fixed 16:15–17:15 exit, or already competed away. The Tokyo
  post-fix effect survives gross (t 2.27) but is about the size of a retail round trip. That is
  what an efficient market leaves to someone paying 1.8 bps.
- **The trend premium (DIV-1).** It exists because of under-reaction to information,
  hedging-driven flows, and investors paying for the crash-protection trend portfolios provide. It
  is earned through diversification across asset classes. **That is exactly what an FX-only,
  10-year dataset cannot provide, and the most likely reason everything here failed.**

## 10. Missing data that would unlock the research

| Data | Why | Obtainable? |
|---|---|---|
| Daily multi-asset prices (equity indices, bonds, commodities, FX), 2000+ | DIV-1; diversification is where the documented edge lives | **Yes**, free (Yahoo/Stooq), from any normal internet connection. Blocked only in this container. `python scripts/div1.py fetch && python scripts/div1.py judge` |
| Hour 00 UTC ticks | The Tokyo fix hour; complete bars | Yes, from Dukascopy directly, also blocked here. Re-ingest with `scripts/ingest_dukascopy.py` pointed at the original feed |
| A longer FX history (1990s+) with bid/ask | Power: 25+ years would let a Sharpe 0.5 edge be proven | Partly (daily only); paid intraday sources |
| Economic-release consensus vs actual | News-surprise drift strategies | Paid (Bloomberg/Refinitiv) or careful scraping |
| Order flow / positioning beyond weekly COT | The flow information banks trade on | Mostly paid (CLS, broker data) |

## 11. Files changed

- **Research code:**
  - `aitrader/research/discovery/flow.py` (FLOW-1 study)
  - `scripts/flow1.py` (FLOW-1 runner)
  - `aitrader/research/discovery/trend.py` (DIV-1 study)
  - `scripts/div1.py` (DIV-1 fetch, judge and holdout)
  - `aitrader/research/discovery/edges.py` (edges-1.5.0)
- **Preregistrations and specs:**
  - `research/preregistrations/FLOW-1.md`, `research/specs/FLOW-1.json`
  - `research/preregistrations/DIV-1.md`, `research/specs/DIV-1.json`
  - `research/holdout-div.json`
- **Results:**
  - `research/registry.jsonl`: FLOW-1 trial and verdict; DIV-1 trial, pending
  - `research/knowledge/FLOW-1.json`, `research/results/FLOW-1-summary.md`
  - `research/knowledge/edge_registry.json`, `docs/TRADING_EDGE_REGISTRY.md`
- **Live system:**
  - `aitrader/risk/engine.py` (risk-1.1.0, full round-trip cost ceiling)
  - `aitrader/service/config.py` (`RISK_MAX_COST_TO_RISK`, which can only be lowered)
  - `.env.example`
- **Tests:**
  - `tests/unit/test_flow.py`, `tests/unit/test_trend.py`, `tests/unit/test_risk.py`
  - `scripts/mutation_audit.py` (7 new mutants)
- **Docs:** this report, `docs/MUTATION_AUDIT.md` and `README.md`.

## 12. Tests and commit

- Full suite: **678 passed, 0 failed** (`bash scripts/check.sh`; 661 before this mission).
- Mutation audit: **142 of 142 killed** (7 new mutants for the cost ceiling, the fix-flow study and the trend study).
- Commit: see the repository log. This report is part of the final commit of the mission.
