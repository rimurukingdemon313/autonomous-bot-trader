# SCX-1 verdict: PASSED (development, 2026-11-22) · not validated

Judged once by run 44978745535 of `.github/workflows/scx1.yml` (head b7e1f39, the registration commit; started
03:02:07 UTC, after registration at 02:50 UTC), with the registered code sha256 `d8a58f9c...` and spec sha256
`c05a229f...`. 199 archive files, none absent, none failed; no bar after 2023-06-26 22:00 UTC was read.
Record: `research/knowledge/SCX-1.json`.

| Threshold | Swaps | Weeks | Net per swap | t | Gross | Costs doubled | Wednesdays (same rule) | Placebo p95 | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 3 bp | 603 | 184 | +2.4 bp | 1.67 | +4.4 bp | +0.4 bp | -0.5 bp (574) | +2.4 bp | FAILED (t, placebo) |
| **10 bp** | **242** | **81** | **+8.6 bp** | **3.02** | +10.6 bp | +6.6 bp | -0.1 bp (285) | +5.8 bp | **PASSED** |

At 10 bp every gate held: both halves (+11.5 bp, then +5.8 bp), the five best swaps removed (+5.6 bp), the best week
removed (+7.2 bp: it was the SVB weekend of 2023-03-12), the best pair removed (USDC; +7.6 bp), an hour later
(+7.9 bp), and none of the 1,000 placebo draws reached the rule's mean. 58% of swaps were positive, the median
+1.0 bp; the worst -46 bp, the best +357 bp. Five pairs traded: USDC, TUSD, USDP, its predecessor PAX, and BUSD.

## What it says

In 2018-2023, a stablecoin pair standing at least 10 bp from par late on Sunday came most of the way back by
Monday's US close; the same deviation on a Wednesday, with the issuers' primary market open, did not pay at all. That
is what the closure of the primary market predicts. **It is small:** 8.6 bp a swap, about three swaps a month across
the pairs, and it exists only at near-zero fees: at Binance's standard 10 bp a fill the same swaps lose 9.4 bp each.
The t of 3.02 clears the bar of 3.0 by very little.

## What follows

As registered: SCX-1-V, once, on 2023-07-02 to 2026-10-25 (174 Sundays no study here has read), at 10 bp. Only if it
passes does the forward stage follow (2026-12-06 to 2027-05-30). Nothing is traded; nothing is validated by this
stage.
