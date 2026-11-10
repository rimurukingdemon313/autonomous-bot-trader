# FUNDED-P — a funded-account paper track of TRND-1 · PAPER ONLY, NOT REAL MONEY

Updated 2026-11-10 08:29 UTC · funded-paper-1.1.2 · started 2026-11-09 · public daily closes · no broker

## ملخص بالعربي

- مسار نص الحجم: المرحلة الأولى (الهدف +10%)، الرصيد $199,945 (من $200,000: -55)، ماسك: US500، NAS100، GER40، UK100.
- مسار الحجم الكامل: المرحلة الأولى (الهدف +10%)، الرصيد $199,895 (من $200,000: -105)، ماسك: US500، NAS100، GER40، UK100.
- هالشهر القاعدة ماسكة: US500، NAS100، GER40، UK100. وبرّه: ولا مؤشر.
- القرار الجاي: آخر يوم تداول بالشهر (2026-11-30)، بعد الإغلاق.
- حساب ورقي للقياس، مو فلوس حقيقية، والماضي مو وعد.

## The tracks

| Track | Status | Equity | Phase P&L | Target | Trading days | Held | Last close |
|---|---|---|---|---|---|---|---|
| HALF (50% of the balance when all four are held, stop 6% a day) | **PHASE 1** | $199,945.00 | -55.00 | $220,000 | 1 | US500, NAS100, GER40, UK100 | 2026-11-09 |
| FULL (100% of the balance when all four are held, no stop) | **PHASE 1** | $199,895.00 | -105.00 | $220,000 | 1 | US500, NAS100, GER40, UK100 | 2026-11-09 |

### HALF: events

- none yet

| Date | Phase | Equity | Day P&L |
|---|---|---|---|
| 2026-11-09 | 1 | $199,945.00 | -55.00 |

### FULL: events

- none yet

| Date | Phase | Equity | Day P&L |
|---|---|---|---|
| 2026-11-09 | 1 | $199,895.00 | -105.00 |

## This month's decisions (November 2026)

What the rule holds now, and at the latest close what a HALF position ($25,000) is and where its one-day stop sits for the next day. GER 40 and UK 100 are priced in euros and pounds: their units use the latest EUR/USD and GBP/USD rates (shown); the contract size of a lot is the broker's.

| Index | This month | Month-end close | Mean of ten month-ends | Latest close | HALF units | HALF stop |
|---|---|---|---|---|---|---|
| US500 | **HOLD** | 7,580.07 (2026-10-30) | 7,304.23 | 7,549.94 (2026-11-09) | 3.31 | 7,096.94 |
| NAS100 | **HOLD** | 28,384.85 (2026-10-30) | 27,883.88 | 27,907.63 (2026-11-09) | 0.90 | 26,233.17 |
| GER40 | **HOLD** | 25,818.21 (2026-10-30) | 24,980.08 | 26,267.19 (2026-11-09) | 0.85 at 1.1246 | 24,691.16 |
| UK100 | **HOLD** | 10,729.80 (2026-10-30) | 10,562.40 | 10,782.90 (2026-11-09) | 1.72 at 1.3455 | 10,135.93 |

## The rules

TRND-1's rule, unchanged, on the US 500, US Tech 100, GER 40 and UK 100: an index is held for a month if the last month-end close before it is above the mean of the ten month-end closes before it; never short. 0.05% each switch; no swap; no dividends. A day losing $10,000, or equity at $180,000, fails; +10% then +5% (each with at least 4 trading days) pass the two phases. Closes only; a close counts 30 minutes after its exchange closes. `scripts/funded_paper.py`, `docs/FUNDED_PAPER.md`.
