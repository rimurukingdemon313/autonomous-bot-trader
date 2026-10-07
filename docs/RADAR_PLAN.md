# The funding radar: how it would make money, and the plan

**Status: PAPER ONLY.** The rules and the single verdict are in `research/preregistrations/RADAR-1.md`.

Nothing here is proven yet. This document explains the mechanism, what has to be true for it to pay, and the
stages before any real money.

## 1. How it makes money

A perpetual future has no expiry. To keep its price near the coin's price, longs and shorts exchange
**funding**, every hour or every eight hours depending on the venue. When the perpetual trades above the coin,
longs pay shorts. Each venue sets its own rate from its own traders, so **the same coin can pay different
funding on different venues.**

The radar holds positions like this:

```
venue A pays  +40%/yr on coin X   →  SHORT X on A   (receives 40%/yr)
venue B pays   +5%/yr on coin X   →  LONG  X on B   (pays 5%/yr)
                                      ────────────
price exposure: none (short and long cancel)   net funding: +35%/yr on the notional
```

If coin X doubles or halves, one leg gains what the other loses. What remains is the **difference in
funding**. The costs are the four trades needed to open and close (≈ 30–40 bp of notional) and the small
drift between the two venues' prices.

Worked example, at 1× margin:

| | |
|---|---|
| Notional | $1,000 short on A + $1,000 long on B; capital $2,000 |
| Spread | 35%/yr for 10 days → $1,000 × 35% × 10/365 ≈ **$9.6** funding |
| Costs | 4 fills × ≈ 10 bp × $1,000 ≈ **$3.9** |
| Net | ≈ **$5.7** on $2,000 in 10 days ≈ 10%/yr on the capital, before the cash rate |

With up to 10 such positions the book diversifies across coins and venues. Higher margin (2–3×, usual for a
hedged position) multiplies the return on capital, and multiplies the liquidation risk on each leg with it.

## 2. Why it might still be there, and why it might not

**For:** each venue's funding comes from its own users. Closing the gap needs capital parked on two venues,
two margin accounts to manage, and acceptance of venue risk. New listings and narrative spikes open gaps
faster than that capital moves. On 2026-10-07 the live check found 6 liquid coins with a current gap of
25%/yr or more (`research/results/radar-check.json`).

**Against:** every historical test in this repository (CR-1 … CR-5) found that a crypto funding premium is
competed down to about the cost of capital within one or two years. Gaps also close fast. A gap that lasts
hours pays less than the 30–40 bp it costs to cross. The radar's entry rule (72 h of a ≥ 25% spread) exists to
skip those. Whether enough gaps last long enough is exactly what the forward test measures.

## 3. The plan

| Stage | What | Money | Pass condition | Time |
|---|---|---|---|---|
| **0. Built** (done) | radar, venue parsers verified live, tests, preregistration, hourly runs | none | the parsers agree with live prices (0 mismatches) | done |
| **1. Paper forward test** (running) | hourly paper ledger on 4 venues, public report on `radar-data` | none | the single look at day 60: excess over cash ≥ 10%/yr on the capital used, t ≥ 2, still > 0 at 1.5× costs and without the best coin, drawdown ≤ 10% | 60 days (120 if too few trades) |
| **2. Real fills, small** | only if stage 1 passes. You run it on your own accounts; the radar's report tells you what to open and close. Keys never leave your machine and are never sent in chat | a size you can lose entirely, e.g. $500–$1,000 per venue | the same gates on the fees and fills actually paid | 60 days |
| **3. Scale** | only if stage 2 passes: more capital, more venues, maker orders to cut fees | grow step by step | the gates keep holding; capacity measured, not assumed | ongoing |

At any stage a failed gate means stop. The rules are not tuned and retried.

## 4. What can lose money even when the idea is right

| Risk | Effect | Guard |
|---|---|---|
| A venue fails, freezes withdrawals or is hacked | the margin on that venue can be lost entirely | never more on one venue than you can lose; the hurdle is cash + 10%, not cash |
| One leg liquidated in a fast move | the hedge breaks at the worst moment | 1× margin; rebalance at a 25% move |
| Funding flips | the position pays instead of earning | exits on a decayed or reversed spread |
| Fees and slippage above the declared ones | the edge shrinks | the gate at 1.5× costs |
| Venue rule changes (caps, intervals) | the spread is redefined | live data only; nothing is assumed to persist |

## 5. Where to look

| | |
|---|---|
| Hourly report | branch `radar-data`, `REPORT.md` |
| Positions and marks | branch `radar-data`, `ledger.json` |
| The verdict, when due | branch `radar-data`, `RADAR-1-look1.json` (frozen once, at day 60) |
| Rules | `research/preregistrations/RADAR-1.md` |
