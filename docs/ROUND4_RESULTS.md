# Round 4 results: is there directional information outside the FX pair? — FAILED

- **Design:** `scripts/round4.py`; preregistration `research/preregistrations/R4-directional-information.md`,
  committed before the run.
- **Verdicts:** `research/knowledge/R4.json`.
- **Information-value report:** `research/results/R4-report.json` (`scripts/r4_report.py`, descriptive).
- **Audit and data matrix:** [ROUND4_AUDIT.md](ROUND4_AUDIT.md).
- **Judgement:** judged once on 2008-07-11 → 2017-01-01 (gold from 2011-05), with fixed levels, standard
  D1 costs, the full battery, and **t ≥ 3.372**. The registry counted 62 prior tests on these outcomes.

## Sources

| Source | Status |
|---|---|
| CFTC positioning (COT) | **DATA-BLOCKED**: every source refused; not approximated |
| Consensus surprises: CPI, payrolls, GDP, retail, PMI | **DATA-BLOCKED**: historical consensus is proprietary; revised values would leak |
| Central-bank decision surprises | **DATA-BLOCKED**: needs OIS or futures expectations |
| Gold → AUD | tested (R4-XA-GOLD-A/B) |
| VIX spike → safe havens | tested (R4-XA-VIX-A) |
| US inflation acceleration → USD (unrevised CPI-U) | tested (R4-MACRO-CPI-A/B) |

## Results

All figures are in R per trade. "Control" is the price-only control: the pair's own-move condition
alone, on the same pairs, side and exit. "IV" is the information value: the hypothesis minus its
control.

| ID | n | P(dir) | Gross | Costs: spread / comm / slip / financing | **Net** | Net, low / high cost | t (req. 3.372) | Without best trade | Without best 5% | Control (n, net) | IV | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R4-XA-GOLD-A: buy AUD after gold +2% while AUD fell | 102 | 52.9% | +0.066 | .021 / .003 / .001 / .025 | **+0.015** | +0.022 / −0.010 | 0.16 | −0.002 | −0.058 | 595, −0.086 | **+0.101** | REJECTED |
| R4-XA-GOLD-B: sell AUD after gold −2% while AUD rose | 84 | 42.9% | −0.112 | .021 / .004 / .001 / .026 | **−0.163** | −0.162 / −0.193 | −1.98 | −0.185 | −0.237 | 603, −0.045 | −0.118 | REJECTED (84 < 100) |
| R4-XA-VIX-A: buy JPY/CHF after VIX +20% where the pair still rose, **registered 5 pairs** | 156 | 52.6% | −0.077 | .027 / .004 / .001 / .025 | **−0.134** | −0.122 / −0.160 | −2.07 * | −0.143 | −0.203 | 1,452, −0.050 | −0.084 | REJECTED * |
| R4-MACRO-CPI-A: US inflation +0.3pp, with the USD leg | 337 | 48.1% | +0.041 | .012 / .002 / .001 / .076 | **−0.049** | −0.042 / −0.095 | −0.80 | −0.065 | −0.173 | — | — | REJECTED |
| R4-MACRO-CPI-B: the mirror | 332 | 50.9% | +0.087 | .012 / .002 / .001 / .075 | **−0.003** | +0.003 / −0.053 | −0.05 | −0.014 | −0.131 | — | — | REJECTED |

\* **Execution defect, found and fixed.** The program (confirm-1.0.0) judged R4-XA-VIX-A on all 11
of its instruments, 361 trades, instead of its 5 registered pairs.

- Only this hypothesis was affected. Every earlier hypothesis covered all of its program's pairs,
  and the gold and CPI conditions are undefined outside their own pairs; the audit script and the
  exact trade reproductions confirm both.
- The fix is confirm-1.1.0, with a regression test.
- On its registered 5 pairs the same battery rejects it: −0.134R, t −2.07, 156 trades.
- The correction is recorded in `research/knowledge/corrections.json` and shown in the edge
  registry. The conclusion does not change.

**Best and worst regimes** (≥ 20 trades):

| ID | Best | Worst |
|---|---|---|
| GOLD-A | low volatility, +0.066 | VIX 20–30, −0.100 |
| VIX-A | range regime, −0.074 | trend regime, −0.193 |
| CPI-A | VIX ≥ 30, +0.208 | VIX < 20, −0.185 |
| CPI-B | VIX ≥ 30, +0.307 | VIX < 20, −0.162 |

**Years.** CPI-A and CPI-B were each positive in only 3 of 9 years, mostly in the crisis years 2008–2010.
GOLD-A was positive in 3 of 6 years (2012, 2013 and 2016).

## The information-value test, answered per source

| Question | Gold → AUD | VIX spike → havens | US inflation → USD |
|---|---|---|---|
| 1. Available before the trade? | yes: same close | yes: 16:45 New York | yes: from the last day of the next month |
| 2. Predicts direction? | 53% (BUY leg), 43% (SELL leg) | 53% | 48–51% |
| 3. Adds information beyond recent FX price? | BUY leg: +0.10R over its control. SELL leg: −0.12R | no: −0.08R versus its control | — (no own-price control in this form) |
| 4. Survives costs? | BUY: +0.015 normal, −0.010 high | no | no (−0.049 / −0.003) |
| 5. Survives walk-forward (judged out of sample, by year)? | no: 3 of 6 years positive | no: 1 of 9 | no: 3 of 9 years positive, mostly 2008–2010 |
| 6. Works across currencies? | only AUD tested; AUDJPY +0.001, AUDUSD +0.032 | 2 of 5 pairs positive | 2–3 of 7 positive |
| 7. Works across periods? | no | no | no |
| 8. Survives reasonable parameter changes? | **no**: −0.033 at a 1.5% gold threshold, −0.049 at 2.5% (descriptive) | — | — |
| 9. Survives removing the best trade or event? | **no**: −0.002 without the best trade | no | no: −0.065 / −0.014 |
| 10. Economic explanation? | weak: the literature finds FX leads commodities, not the reverse | contemporaneous haven moves are documented; a lagged catch-up is not | two-country Taylor rules are documented; the US side alone is not |

## Conclusion

**VALIDATED 0. PROMISING 0. REJECTED 5. DATA-BLOCKED 3 sources** (positioning, consensus surprises
and decision surprises), plus first-release macro.

The only positive information value came from the gold → AUD buy leg (+0.10R over price alone):

- its mirror leg lost;
- it is not significant (t 0.16);
- it vanishes at neighbouring thresholds and without its best trade.

That is noise, not information.
