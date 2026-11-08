# FUNDED-P — a funded-account paper track of TRND-1 · PAPER ONLY, NOT REAL MONEY

Updated 2026-11-08 07:56 UTC · funded-paper-1.1.1 · started 2026-11-09 · public daily closes · no broker

## ملخص بالعربي

- مسار نص الحجم: يبدي بإغلاق 2026-11-09.
- مسار الحجم الكامل: يبدي بإغلاق 2026-11-09.
- هالشهر القاعدة ماسكة: US500، NAS100، GER40، UK100. وبرّه: ولا مؤشر.
- القرار الجاي: آخر يوم تداول بالشهر (2026-11-30)، بعد الإغلاق.
- حساب ورقي للقياس، مو فلوس حقيقية، والماضي مو وعد.

## The tracks

| Track | Status | Equity | Phase P&L | Target | Trading days | Held | Last close |
|---|---|---|---|---|---|---|---|
| HALF | not started: the record starts at the close of 2026-11-09 | | | | | | |
| FULL | not started: the record starts at the close of 2026-11-09 | | | | | | |

### HALF: events

- none yet

| Date | Phase | Equity | Day P&L |
|---|---|---|---|

### FULL: events

- none yet

| Date | Phase | Equity | Day P&L |
|---|---|---|---|

## This month's decisions (November 2026)

What the rule holds now, and at the latest close what a HALF position ($25,000) is and where its one-day stop sits for the next day.

| Index | This month | Month-end close | Mean of ten month-ends | Latest close | HALF units | HALF stop |
|---|---|---|---|---|---|---|
| US500 | **HOLD** | 7,580.07 (2026-10-30) | 7,304.23 | 7,376.86 (2026-11-06) | 3.39 | 6,934.25 |
| NAS100 | **HOLD** | 28,384.85 (2026-10-30) | 27,883.88 | 26,989.99 (2026-11-06) | 0.93 | 25,370.59 |
| GER40 | **HOLD** | 25,818.21 (2026-10-30) | 24,980.08 | 25,820.36 (2026-11-06) | 0.97 | 24,271.14 |
| UK100 | **HOLD** | 10,729.80 (2026-10-30) | 10,562.40 | 10,673.90 (2026-11-06) | 2.34 | 10,033.47 |

## The rules

TRND-1's rule, unchanged, on the US 500, US Tech 100, GER 40 and UK 100: an index is held for a month if the last month-end close before it is above the mean of the ten month-end closes before it; never short. 0.05% each switch; no swap; no dividends. A day losing $10,000, or equity at $180,000, fails; +10% then +5% (each with at least 4 trading days) pass the two phases. Closes only; a close counts 30 minutes after its exchange closes. `scripts/funded_paper.py`, `docs/FUNDED_PAPER.md`.
