# TRINITY DESK · TRINITY-MASTER on paper · PAPER ONLY · NOT REAL MONEY · NOT VALIDATED

**بالعربي:** حساب ورقي بـ$200,000 يتداول بيه النظام قاعدة TRINITY-MASTER اللي بعثها المالك. القاعدة تجريبية ما انعتمدت، فمحرك المخاطر يحدد حجم كل صفقة بحد 0.25% من الرصيد. الرصيد الحالي $259,204، يعني من البداية $59,204. ما ماسك شي هسه. إعادة التوازن الجاية: 2026-11-25. هذا ورق، مو فلوس حقيقية.

**What this is.** The owner's TRINITY-MASTER (research/external/trinity/), traded on paper so its record starts now. It is **EXPERIMENTAL**: its 20-year figures come from a backtest on 288 dates its author chose, and on real daily prices they did not hold as stated (research/results/TRINITY-MASTER-redteam.json, docs/TRINITY.md). The risk engine sizes every position as it sizes any unvalidated rule: at most 0.25% of the starting balance lost at its stop. No DEMO, no live account, no real money.

| | |
|---|---|
| Account | TRINITY-PAPER-200K: $200,000 paper, from 2008-01-02 |
| Equity | $259,204 (P/L $59,204); balance $259,204 |
| Risk | ACTIVE (ACTIVE) |
| Rule | TRINITY-MASTER promoted for PAPER as EXPERIMENTAL on replay |
| Last session | 2026-11-20; next rebalance about 2026-11-25 |
| Updated | 2026-11-22T01:49:33.095776+00:00 |

## Positions

| Instrument | Qty | Entry | Last close | Stop | P/L | Notional |
|---|---|---|---|---|---|---|
| none | | | | | | |

## Rebalances (the last twelve)

| Day | Weights QQQ / SPY / GLD / DBC | Held after |
|---|---|---|
| 2026-03-11 | 0.000 / 0.000 / 0.000 / 0.000 | nothing |
| 2026-04-01 | 0.000 / 0.000 / 0.112 / 0.000 | XAUUSD |
| 2026-04-23 | 0.329 / 0.287 / 0.000 / 0.000 | NAS100, US500 |
| 2026-05-14 | 0.292 / 0.318 / 0.000 / 0.000 | NAS100, US500 |
| 2026-06-05 | 0.080 / 0.171 / 0.000 / 0.000 | NAS100, US500 |
| 2026-06-29 | 0.307 / 0.452 / 0.000 / 0.000 | NAS100, US500 |
| 2026-07-21 | 0.000 / 0.000 / 0.000 / 0.000 | nothing |
| 2026-08-11 | 0.342 / 0.521 / 0.000 / 0.000 | NAS100, US500 |
| 2026-09-01 | 0.237 / 0.549 / 0.000 / 0.084 | NAS100, US500, USOIL |
| 2026-09-23 | 0.000 / 0.000 / 0.000 / 0.131 | USOIL |
| 2026-10-14 | 0.000 / 0.000 / 0.000 / 0.148 | USOIL |
| 2026-11-04 | 0.000 / 0.000 / 0.000 / 0.000 | nothing |

## The design book: the package's weights at their own size (measured, never traded)

From 2008-01-02: equity $473,762 (P/L $273,762), worst fall at the lows -$39,802. A firm's 10% maximum loss: not reached; its 5% daily loss: 2015-08-24. This is what the package claims to do, measured on the four funds it was written for. It is kept apart from the account above and never added to it.

## How it trades

- Every 15th trading day from the anchor, at the New York close: TRINITY-MASTER's weights from QQQ, SPY, GLD and DBC, the VIX, TLT and UUP read at the previous close. A weight above 1e-4 is held: NAS100, US500, XAUUSD, USOIL. The others are closed.
- Each entry is sized by the risk engine (0.25% of the starting balance at its stop for an unvalidated rule), with a stop 3.2% below the rebalance close. A stop hit leaves the instrument flat until the next rebalance.
- The hard gate checks every order and stop move and issues the only permit the paper broker accepts. Limits: $10,000 in a day (intraday lows included), $20,000 in all; a breach fails the account and closes everything.

Versions: agents agents-1.2.0, data data-1.0.0, decision decision-1.2.0, dual_ai dual-ai-1.21.0, edge_status edge-status-1.4.0, execution exec-1.9.0, experimental_ai experimental-ai-1.0.0, features feat-1.0.0, forward forward-1.3.0, forward_metrics forward-metrics-1.0.0, labels label-1.0.0, learning learning-1.2.0, llm_trader llm-trader-1.12.0, memory patterns-1.1.0, orchestrator orchestrator-1.27.0, prompt prompt-1.0.0, regime regime-1.0.0, review review-1.0.0, risk risk-1.17.0, risk_gate hard-gate-1.4.0, risk_profile hard-profile-1.3.0, taxonomy taxonomy-1.1.0, trend_desk trend-desk-1.2.0, trinity trinity-1.0.0, trinity_desk trinity-desk-1.0.0
