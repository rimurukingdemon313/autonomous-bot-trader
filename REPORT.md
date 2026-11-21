# FUNDED-P — a funded-account paper track of TRND-1 · PAPER ONLY, NOT REAL MONEY

Updated 2026-11-21 03:15 UTC · funded-paper-1.1.2 · started 2026-11-09 · public daily closes · no broker

## ملخص بالعربي

- مسار نص الحجم: المرحلة الأولى (الهدف +10%)، الرصيد $192,655 (من $200,000: -7,345)، ماسك: US500، NAS100، GER40، UK100.
- مسار الحجم الكامل: المرحلة الأولى (الهدف +10%)، الرصيد $185,330 (من $200,000: -14,670)، ماسك: US500، NAS100، GER40، UK100.
- هالشهر القاعدة ماسكة: US500، NAS100، GER40، UK100. وبرّه: ولا مؤشر.
- القرار الجاي: آخر يوم تداول بالشهر (2026-11-30)، بعد الإغلاق.
- حساب ورقي للقياس، مو فلوس حقيقية، والماضي مو وعد.

## The tracks

| Track | Status | Equity | Phase P&L | Target | Trading days | Held | Last close |
|---|---|---|---|---|---|---|---|
| HALF (50% of the balance when all four are held, stop 6% a day) | **PHASE 1** | $192,654.77 | -7,345.23 | $220,000 | 4 | US500, NAS100, GER40, UK100 | 2026-11-20 |
| FULL (100% of the balance when all four are held, no stop) | **PHASE 1** | $185,329.55 | -14,670.45 | $220,000 | 4 | US500, NAS100, GER40, UK100 | 2026-11-20 |

### HALF: events

- none yet

| Date | Phase | Equity | Day P&L |
|---|---|---|---|
| 2026-11-09 | 1 | $199,945.00 | -55.00 |
| 2026-11-10 | 1 | $199,698.30 | -246.70 |
| 2026-11-11 | 1 | $201,085.71 | +1,387.41 |
| 2026-11-12 | 1 | $201,083.22 | -2.48 |
| 2026-11-13 | 1 | $200,747.18 | -336.05 |
| 2026-11-16 | 1 | $199,410.02 | -1,337.16 |
| 2026-11-17 | 1 | $198,013.61 | -1,396.41 |
| 2026-11-18 | 1 | $197,440.95 | -572.66 |
| 2026-11-19 | 1 | $195,885.95 | -1,555.00 |
| 2026-11-20 | 1 | $192,654.77 | -3,231.18 |

### FULL: events

- none yet

| Date | Phase | Equity | Day P&L |
|---|---|---|---|
| 2026-11-09 | 1 | $199,895.00 | -105.00 |
| 2026-11-10 | 1 | $199,406.60 | -488.40 |
| 2026-11-11 | 1 | $202,186.42 | +2,779.82 |
| 2026-11-12 | 1 | $202,186.45 | +0.03 |
| 2026-11-13 | 1 | $201,514.36 | -672.09 |
| 2026-11-16 | 1 | $198,840.04 | -2,674.32 |
| 2026-11-17 | 1 | $196,047.21 | -2,792.82 |
| 2026-11-18 | 1 | $194,901.90 | -1,145.31 |
| 2026-11-19 | 1 | $191,791.91 | -3,109.99 |
| 2026-11-20 | 1 | $185,329.55 | -6,462.36 |

## This month's decisions (November 2026)

What the rule holds now, and at the latest close what a HALF position ($25,000) is and where its one-day stop sits for the next day. GER 40 and UK 100 are priced in euros and pounds: their units use the latest EUR/USD and GBP/USD rates (shown); the contract size of a lot is the broker's.

| Index | This month | Month-end close | Mean of ten month-ends | Latest close | HALF units | HALF stop |
|---|---|---|---|---|---|---|
| US500 | **HOLD** | 7,580.07 (2026-10-30) | 7,304.23 | 6,910.39 (2026-11-20) | 3.62 | 6,495.77 |
| NAS100 | **HOLD** | 28,384.85 (2026-10-30) | 27,883.88 | 25,028.98 (2026-11-20) | 1.00 | 23,527.24 |
| GER40 | **HOLD** | 25,818.21 (2026-10-30) | 24,980.08 | 24,802.78 (2026-11-20) | 0.92 at 1.0970 | 23,314.61 |
| UK100 | **HOLD** | 10,729.80 (2026-10-30) | 10,562.40 | 10,346.30 (2026-11-20) | 1.85 at 1.3086 | 9,725.52 |

## The rules

TRND-1's rule, unchanged, on the US 500, US Tech 100, GER 40 and UK 100: an index is held for a month if the last month-end close before it is above the mean of the ten month-end closes before it; never short. 0.05% each switch; no swap; no dividends. A day losing $10,000, or equity at $180,000, fails; +10% then +5% (each with at least 4 trading days) pass the two phases. Closes only; a close counts 30 minutes after its exchange closes. `scripts/funded_paper.py`, `docs/FUNDED_PAPER.md`.
