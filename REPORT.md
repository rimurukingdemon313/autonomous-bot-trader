# TREND DESK · TRND-1 traded by the system itself · PAPER ONLY · NOT REAL MONEY

**بالعربي:** هذا حساب ورقي بـ$200,000 يتداول بيه النظام قاعدة TRND-1 وحده، من غير ما أحد يدخل صفقة بإيده. الرصيد الحالي (مع الصفقات المفتوحة) $200,783، يعني الربح أو الخسارة من البداية $783. الحساب شغّال. الماسكهم هسه: GER40، UK100، US500، NAS100. كل مؤشر ماسكه عليه وقف تحت آخر إغلاق بـ6%، ويتحرك كل مساء. هذا ورق، مو فلوس حقيقية، والماضي ما يضمن المستقبل.

| | |
|---|---|
| Account | TRND1-PAPER-200K: $200,000 paper, from 2026-11-09 |
| Equity | $200,783 (P/L $783); balance $200,000 |
| Today | reference $201,079 on 2026-11-13; the day may lose $10,000 at most |
| Risk | ACTIVE (ACTIVE) |
| Rule | TRND-1: VALIDATED/HEALTHY (1 promoted rule(s)) |
| Last session | 2026-11-13T21:00:00+00:00 |
| Updated | 2026-11-14T13:46:31.246670+00:00 |

## Positions

| Index | Units | Entry | Last close | Stop | P/L | Notional |
|---|---|---|---|---|---|---|
| GER40 | 0.84 | 26,268.04 | 26,749.20 | 25,144.95 | $448 | $24,930 |
| UK100 | 1.7 | 10,783.50 | 10,902.10 | 10,248.44 | $268 | $24,606 |
| US500 | 3.25 | 7,550.29 | 7,561.42 | 7,107.97 | $36 | $24,575 |
| NAS100 | 0.89 | 27,908.47 | 27,942.99 | 26,267.11 | $31 | $24,869 |

## The rule now

| Index | For | Decision | Month-end close | Ten-month mean | Latest close | Its stop if held |
|---|---|---|---|---|---|---|
| US500 | 2026-11 | **HOLD** | 7,580.07 (2026-10-30) | 7,304.23 | 7,561.67 (2026-11-13) | 7,107.97 |
| NAS100 | 2026-11 | **HOLD** | 28,384.85 (2026-10-30) | 27,883.88 | 27,943.74 (2026-11-13) | 26,267.12 |
| GER40 | 2026-11 | **HOLD** | 25,818.21 (2026-10-30) | 24,980.08 | 26,749.95 (2026-11-13) | 25,144.95 |
| UK100 | 2026-11 | **HOLD** | 10,729.80 (2026-10-30) | 10,562.40 | 10,902.60 (2026-11-13) | 10,248.44 |

## Closed trades

| Index | Opened | Closed | Entry | Exit | Why | P/L | R |
|---|---|---|---|---|---|---|---|
| none yet | | | | | | | |

Stops moved: 16. Refused or unknown: 0.

## How it trades

- TRND-1: an index is held for a month if its month-end close is above the mean of its ten month-end closes; otherwise nothing is held. Long or flat, never short.
- The switch is at the close of the month's last weekday (the next close, if that day is a holiday).
- Each entry is sized by the risk engine: at most $1,500 lost at its stop, all costs included. The hard gate checks every order and every stop move and issues the only permit the paper broker accepts.
- The stop is 6% below each close and moves after every close. After it is hit, the index stays flat until the next month-end decision.
- Limits: $10,000 in a day (each session's intraday low included), $20,000 in all. A breach fails the account and closes every position, as a firm would.

Versions: agents agents-1.2.0, data data-1.0.0, decision decision-1.2.0, dual_ai dual-ai-1.21.0, edge_status edge-status-1.4.0, execution exec-1.9.0, experimental_ai experimental-ai-1.0.0, features feat-1.0.0, forward forward-1.3.0, forward_metrics forward-metrics-1.0.0, labels label-1.0.0, learning learning-1.2.0, llm_trader llm-trader-1.12.0, memory patterns-1.1.0, orchestrator orchestrator-1.27.0, prompt prompt-1.0.0, regime regime-1.0.0, review review-1.0.0, risk risk-1.16.0, risk_gate hard-gate-1.4.0, risk_profile hard-profile-1.2.0, taxonomy taxonomy-1.1.0, trend_desk trend-desk-1.1.0
