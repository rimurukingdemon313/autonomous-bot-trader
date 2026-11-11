# FUNDED-P — a funded-account paper track of TRND-1 · PAPER ONLY, NOT REAL MONEY

Updated 2026-11-11 01:57 UTC · funded-paper-1.1.2 · started 2026-11-09 · public daily closes · no broker

## ملخص بالعربي

- مسار نص الحجم: المرحلة الأولى (الهدف +10%)، الرصيد $199,698 (من $200,000: -302)، ماسك: US500، NAS100، GER40، UK100.
- مسار الحجم الكامل: المرحلة الأولى (الهدف +10%)، الرصيد $199,407 (من $200,000: -593)، ماسك: US500، NAS100، GER40، UK100.
- هالشهر القاعدة ماسكة: US500، NAS100، GER40، UK100. وبرّه: ولا مؤشر.
- القرار الجاي: آخر يوم تداول بالشهر (2026-11-30)، بعد الإغلاق.
- حساب ورقي للقياس، مو فلوس حقيقية، والماضي مو وعد.

## The tracks

| Track | Status | Equity | Phase P&L | Target | Trading days | Held | Last close |
|---|---|---|---|---|---|---|---|
| HALF (50% of the balance when all four are held, stop 6% a day) | **PHASE 1** | $199,698.30 | -301.70 | $220,000 | 2 | US500, NAS100, GER40, UK100 | 2026-11-10 |
| FULL (100% of the balance when all four are held, no stop) | **PHASE 1** | $199,406.61 | -593.39 | $220,000 | 2 | US500, NAS100, GER40, UK100 | 2026-11-10 |

### HALF: events

- none yet

| Date | Phase | Equity | Day P&L |
|---|---|---|---|
| 2026-11-09 | 1 | $199,945.00 | -55.00 |
| 2026-11-10 | 1 | $199,698.30 | -246.70 |

### FULL: events

- none yet

| Date | Phase | Equity | Day P&L |
|---|---|---|---|
| 2026-11-09 | 1 | $199,895.00 | -105.00 |
| 2026-11-10 | 1 | $199,406.61 | -488.39 |

## This month's decisions (November 2026)

What the rule holds now, and at the latest close what a HALF position ($25,000) is and where its one-day stop sits for the next day. GER 40 and UK 100 are priced in euros and pounds: their units use the latest EUR/USD and GBP/USD rates (shown); the contract size of a lot is the broker's.

| Index | This month | Month-end close | Mean of ten month-ends | Latest close | HALF units | HALF stop |
|---|---|---|---|---|---|---|
| US500 | **HOLD** | 7,580.07 (2026-10-30) | 7,304.23 | 7,520.93 (2026-11-10) | 3.32 | 7,069.67 |
| NAS100 | **HOLD** | 28,384.85 (2026-10-30) | 27,883.88 | 27,740.79 (2026-11-10) | 0.90 | 26,076.35 |
| GER40 | **HOLD** | 25,818.21 (2026-10-30) | 24,980.08 | 26,347.45 (2026-11-10) | 0.85 at 1.1172 | 24,766.60 |
| UK100 | **HOLD** | 10,729.80 (2026-10-30) | 10,562.40 | 10,751.60 (2026-11-10) | 1.74 at 1.3353 | 10,106.50 |

## The rules

TRND-1's rule, unchanged, on the US 500, US Tech 100, GER 40 and UK 100: an index is held for a month if the last month-end close before it is above the mean of the ten month-end closes before it; never short. 0.05% each switch; no swap; no dividends. A day losing $10,000, or equity at $180,000, fails; +10% then +5% (each with at least 4 trading days) pass the two phases. Closes only; a close counts 30 minutes after its exchange closes. `scripts/funded_paper.py`, `docs/FUNDED_PAPER.md`.
