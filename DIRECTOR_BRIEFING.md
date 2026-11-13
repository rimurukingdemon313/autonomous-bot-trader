# The research director's briefing

Written by the lab's worker (lab-cycle-1.1.0, dlab-1.2.0) at 2026-11-13 21:36 UTC, for the model that directs the research (docs/RESEARCH_INSTITUTION.md). Everything here is computed from the committed record. The director reads it, decides what is worth testing, and writes: a hypothesis as rules into `research/director/inbox/`, and each decision into `research/director/log.jsonl`. It approves nothing.

## 1. Results waiting for a review

| Run | Kind | Verdict | In short |
|---|---|---|---|
| `DLAB-CRD-D1` | directed_test | FAILED | 14 rules; 0 promising, 3 positive and not told from noise, 11 lost, 0 overfit; best check-row t 1.383 |
| `DLAB-ETF-D1` | directed_test | FAILED | 12 rules; 0 promising, 2 positive and not told from noise, 7 lost, 0 overfit; best check-row t 1.19 |

## 2. The coverage map

| Panel | Cells | With a classed rule | Set aside (closed family) | Holes |
|---|---|---|---|---|
| `crypto-daily` | 39 | 27 | 12 | 0 |
| `etf-daily` | 27 | 25 | 2 | 0 |

The map covers one declared space only: each ranking a cross-sectional book may be built on, at each holding period. A hole there is filled by the lab itself. What lies outside that space is the director's to propose.

## 3. The record in numbers

- crypto-perp-daily: 280 rules from data-driven discovery; 0 promising; 72 positive out of sample but not told from noise; 83 lost out of sample (52 of them only after costs); 60 overfit; 0 passed validation and 0 failed it
- crypto-perp-daily: combination rules overfit most often (14 of 36)
- crypto-perp-daily: 6 combination rules were positive before costs and negative after: this market's costs, not its information, stopped them
- crypto-perp-daily: 5 cross-asset lead-lag rules were positive before costs and negative after: this market's costs, not its information, stopped them
- crypto-perp-daily: 12 cross-sectional rules were positive before costs and negative after: this market's costs, not its information, stopped them
- crypto-perp-daily: 11 information (non-linear) rules were positive before costs and negative after: this market's costs, not its information, stopped them
- crypto-perp-daily: 6 ordinal pattern rules were positive before costs and negative after: this market's costs, not its information, stopped them
- crypto-perp-daily: 4 own-lag rules were positive before costs and negative after: this market's costs, not its information, stopped them
- crypto-perp-daily: 3 pooled time-series rules were positive before costs and negative after: this market's costs, not its information, stopped them
- crypto-perp-daily: the information audit found 44 of 982 feature-instrument pairs with z >= 2 about the next return (12 of them with no linear trace); chance alone gives about 22.6
- energy-futures-eia: 102 rules from data-driven discovery; 0 promising; 25 positive out of sample but not told from noise; 43 lost out of sample (10 of them only after costs); 21 overfit; 0 passed validation and 0 failed it
- energy-futures-eia: 3 evolved rule rules were positive before costs and negative after: this market's costs, not its information, stopped them
- energy-futures-eia: the information audit found 3 of 46 feature-instrument pairs with z >= 2 about the next return (1 of them with no linear trace); chance alone gives about 1.1
- us-etf-broad-daily: 278 rules from data-driven discovery; 0 promising; 51 positive out of sample but not told from noise; 109 lost out of sample (56 of them only after costs); 78 overfit; 0 passed validation and 0 failed it
- us-etf-broad-daily: own-lag rules overfit most often (7 of 8)
- us-etf-broad-daily: 9 combination rules were positive before costs and negative after: this market's costs, not its information, stopped them
- us-etf-broad-daily: 4 cross-asset lead-lag rules were positive before costs and negative after: this market's costs, not its information, stopped them
- us-etf-broad-daily: 15 cross-sectional rules were positive before costs and negative after: this market's costs, not its information, stopped them
- us-etf-broad-daily: 4 evolved rule rules were positive before costs and negative after: this market's costs, not its information, stopped them
- us-etf-broad-daily: 8 information (non-linear) rules were positive before costs and negative after: this market's costs, not its information, stopped them
- us-etf-broad-daily: 7 ordinal pattern rules were positive before costs and negative after: this market's costs, not its information, stopped them
- us-etf-broad-daily: 6 pooled time-series rules were positive before costs and negative after: this market's costs, not its information, stopped them
- us-etf-broad-daily: the information audit found 30 of 434 feature-instrument pairs with z >= 2 about the next return (9 of them with no linear trace); chance alone gives about 10.0

## 4. The strongest candidates not judged

| Run | Rule | Family | Check-row t | Class |
|---|---|---|---|---|
| DLAB-CRD-1 | ONTUSDT: rev for 5 rows after a multivariate shock of mkt(1), disp(1), ret(ONTUSDT,1) beyond 11.9 | anomaly | 2.756 | INSUFFICIENT_POWER |
| DLAB-CRD-1 | XMRUSDT: against the sign of z250[ret(XMRUSDT,1)] beyond 0.5 | own-lag | 2.148 | INSUFFICIENT_POWER |
| DLAB-CRD-1 | BNBUSDT: by 2 regimes of 1 state features, map [1.0, 0.0] | regime | 2.025 | INSUFFICIENT_POWER |
| DLAB-CRD-1 | XMRUSDT: rev for 5 rows after a multivariate shock of mkt(1), disp(1), ret(XMRUSDT,1) beyond 13.2 | anomaly | 1.889 | INSUFFICIENT_POWER |
| DLAB-CRD-1 | BCHUSDT: by the rank bins of ret(BCHUSDT,1) x aux(BCHUSDT.fund7), map [0.0, 1.0, 1.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0] | information (non-linear) | 1.822 | INSUFFICIENT_POWER |
| DLAB-ETF-1 | book of 31: long SPY for 5 rows while rank250[disp(20)] < 0.2; long QQQ for 5 rows while rank250[disp(20)] < 0.2; long IWM for 5 rows while  | pooled time-series | 1.701 | INSUFFICIENT_POWER |
| DLAB-CRD-1 | IOTAUSDT: and of IOTAUSDT: by the ordering of IOTAUSDT's last 3 1-row returns, map [0.0, 0.0, -1.0, 0.0, 1.0, 1.0] | IOTAUSDT: with the sign | combination | 1.652 | INSUFFICIENT_POWER |
| DLAB-CRD-1 | AVAXUSDT: with the sign of z250[ret(EGLDUSDT,5)] beyond 0.5 | cross-asset lead-lag | 1.617 | INSUFFICIENT_POWER |
| DLAB-CRD-1 | BCHUSDT: by the rank bins of ret(BCHUSDT,1) x volr(BCHUSDT,5,60), map [-1.0, 1.0, 1.0, -1.0, -1.0, -1.0, 0.0, 1.0, -1.0] | information (non-linear) | 1.613 | INSUFFICIENT_POWER |
| DLAB-ETF-1 | EWY: and of EWY: by the rank bins of rel(EWY,20) x disp(20), map [1.0, -1.0, 1.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0] | EWY: against the sign of  | combination | 1.597 | INSUFFICIENT_POWER |

## 5. The queue and the inbox

- The queue is empty.
- `crypto-daily`: scanned once under dlab-1.1.0; of its 39 ranking-and-holding-period cells, 27 have a classed rule, 12 are set aside as closed families, and 0 are holes
- `etf-daily`: scanned once under dlab-1.1.0; of its 27 ranking-and-holding-period cells, 25 have a classed rule, 2 are set aside as closed families, and 0 are holes
- no submission is waiting in `research/director/inbox`
- the next experiment starts with a submission (the research director's, or the idea engine's), a new panel or method (a new version of the lab), or a new month of data

## 6. Sources

85 on file; 85 are UNREAD (a title and an abstract are not a finding). The newest:

- 2026-11-10 · Point-in-Time Encoders for Earnings Calls (http://arxiv.org/abs/2611.14325v1)
- 2026-11-10 · Deep Learning for Operator Maps in Optimal Liquidation (http://arxiv.org/abs/2611.14245v1)
- 2026-11-10 · Fine-Tuning an Order-Flow Foundation Model for Sub-Second Forecasting (http://arxiv.org/abs/2611.14117v1)
- 2026-11-10 · Deceleration without identification: testing a power-law trend in Bitcoin prices under persistent noise (http://arxiv.org/abs/2611.13962v1)
- 2026-11-10 · Optimal Trading Speed on Blockchain (http://arxiv.org/abs/2611.13616v1)
- 2026-11-10 · Tabular Foundation Models in Financial Predictions (http://arxiv.org/abs/2611.13550v1)
- 2026-11-09 · Making sense of rule 605 (http://arxiv.org/abs/2611.13365v1)
- 2026-11-09 · Diversification Across Predictors: Heterogeneous Ensemble Learning for Cross-Sectional Return Prediction (http://arxiv.org/abs/2611.12389v1)
- 2026-11-08 · Adjoint Kernel Sensitivity of the Rough Heston Characteristic Exponent (http://arxiv.org/abs/2611.11652v1)
- 2026-11-08 · Retrospective Analysis of Team-Following Trading Profitability in Pumpfun Meme Coins Using Funding Networks (http://arxiv.org/abs/2611.11436v1)
- 2026-11-08 · Optimal execution in a fractional setting with reinforcement learning (http://arxiv.org/abs/2611.11373v1)
- 2026-11-07 · Risk-Sensitive Reinforcement Learning for an Options Market Maker: An Empirical Study with Real S&P 500 Options (http://arxiv.org/abs/2611.10956v1)

## 7. How a hypothesis is submitted

One file, `research/director/inbox/<id>.json`, committed to main. It is taken as written or refused: nothing is repaired. Fields: `id` (the file's name), `author` (`role`: director, engine or lab; `model`; `interface`), `dataset` (crypto-daily, etf-daily), `title`, `hypothesis`, `mechanism`, `why_now`, `refuted_by`, `parents`, and `rules`: 1 to 48, each with a `family`, a `why`, a `spec` in the lab's rule language (aitrader/research/dlab/signals.py) and, if the fit rows are to choose its side, `orient: fit`. A rule that reads the future, names an unknown instrument, repeats a classed rule or behaves as a closed family is refused before any test is charged. `in_sample_on_check_rows: true` says the rules were chosen on the check rows (an aggregate of classed rules): their check-row figures then show nothing, and only a validation can judge them.
