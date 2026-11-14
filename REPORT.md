# FUNDED-P — a funded-account paper track of TRND-1 · PAPER ONLY, NOT REAL MONEY

Updated 2026-11-14 13:50 UTC · funded-paper-1.1.2 · started 2026-11-09 · public daily closes · no broker

## ملخص بالعربي

- مسار نص الحجم: المرحلة الأولى (الهدف +10%)، الرصيد $200,747 (من $200,000: +747)، ماسك: US500، NAS100، GER40، UK100.
- مسار الحجم الكامل: المرحلة الأولى (الهدف +10%)، الرصيد $201,514 (من $200,000: +1,514)، ماسك: US500، NAS100، GER40، UK100.
- هالشهر القاعدة ماسكة: US500، NAS100، GER40، UK100. وبرّه: ولا مؤشر.
- القرار الجاي: آخر يوم تداول بالشهر (2026-11-30)، بعد الإغلاق.
- حساب ورقي للقياس، مو فلوس حقيقية، والماضي مو وعد.

## The tracks

| Track | Status | Equity | Phase P&L | Target | Trading days | Held | Last close |
|---|---|---|---|---|---|---|---|
| HALF (50% of the balance when all four are held, stop 6% a day) | **PHASE 1** | $200,747.18 | +747.18 | $220,000 | 4 | US500, NAS100, GER40, UK100 | 2026-11-13 |
| FULL (100% of the balance when all four are held, no stop) | **PHASE 1** | $201,514.36 | +1,514.36 | $220,000 | 4 | US500, NAS100, GER40, UK100 | 2026-11-13 |

### HALF: events

- none yet

| Date | Phase | Equity | Day P&L |
|---|---|---|---|
| 2026-11-09 | 1 | $199,945.00 | -55.00 |
| 2026-11-10 | 1 | $199,698.30 | -246.70 |
| 2026-11-11 | 1 | $201,085.71 | +1,387.41 |
| 2026-11-12 | 1 | $201,083.22 | -2.48 |
| 2026-11-13 | 1 | $200,747.18 | -336.05 |

### FULL: events

- none yet

| Date | Phase | Equity | Day P&L |
|---|---|---|---|
| 2026-11-09 | 1 | $199,895.00 | -105.00 |
| 2026-11-10 | 1 | $199,406.60 | -488.40 |
| 2026-11-11 | 1 | $202,186.42 | +2,779.82 |
| 2026-11-12 | 1 | $202,186.45 | +0.03 |
| 2026-11-13 | 1 | $201,514.36 | -672.09 |

## This month's decisions (November 2026)

What the rule holds now, and at the latest close what a HALF position ($25,000) is and where its one-day stop sits for the next day. GER 40 and UK 100 are priced in euros and pounds: their units use the latest EUR/USD and GBP/USD rates (shown); the contract size of a lot is the broker's.

| Index | This month | Month-end close | Mean of ten month-ends | Latest close | HALF units | HALF stop |
|---|---|---|---|---|---|---|
| US500 | **HOLD** | 7,580.07 (2026-10-30) | 7,304.23 | 7,561.67 (2026-11-13) | 3.31 | 7,107.97 |
| NAS100 | **HOLD** | 28,384.85 (2026-10-30) | 27,883.88 | 27,943.74 (2026-11-13) | 0.89 | 26,267.12 |
| GER40 | **HOLD** | 25,818.21 (2026-10-30) | 24,980.08 | 26,749.95 (2026-11-13) | 0.85 at 1.1050 | 25,144.95 |
| UK100 | **HOLD** | 10,729.80 (2026-10-30) | 10,562.40 | 10,902.60 (2026-11-13) | 1.73 at 1.3231 | 10,248.44 |

## The rules

TRND-1's rule, unchanged, on the US 500, US Tech 100, GER 40 and UK 100: an index is held for a month if the last month-end close before it is above the mean of the ten month-end closes before it; never short. 0.05% each switch; no swap; no dividends. A day losing $10,000, or equity at $180,000, fails; +10% then +5% (each with at least 4 trading days) pass the two phases. Closes only; a close counts 30 minutes after its exchange closes. `scripts/funded_paper.py`, `docs/FUNDED_PAPER.md`.
