# IX-3: the overnight drift of US index CFDs at the European cash open (preregistration)

| | |
|---|---|
| Frozen spec | `research/specs/IX-3.json` |
| Spec sha256 | `86ba60500cc5e3c4e71fbad51d68257f2e7718a9f29427e62abb489a62c49ee0` |
| Code | `aitrader/research/discovery/ixdrift.py` (ixd-1.0.0), `scripts/ix3.py`; data, loader, gates and costs from `scripts/ix2.py` |
| Tests | `tests/unit/test_ixdrift.py` (7) |
| Threshold | t ≥ **3.6477** on the daily equal-weight book: Bonferroni over all 187 registered tests, plus these 2 |

## Hypothesis and mechanism

Boyarchenko, Larsen & Whelan ("The Overnight Drift", *Review of Financial Studies* 2023) find that US
equity-index futures earn a large share of their return around the opening of European cash markets.

**Mechanism.** Dealers who absorbed end-of-day customer selling hold that inventory overnight. They lay it
off when European liquidity arrives, and the price drift compensates them for the risk of holding it.
The drift is larger after sessions that ended with selling pressure.

This is a risk premium paid to liquidity providers, not a forecasting trick. It is paid as long as the
inventory problem exists.

## Rules

| | |
|---|---|
| Instruments | USA500IDXUSD, USATECHIDXUSD, USA30IDXUSD: the H1 bid/ask bars fetched for IX-2. These are three versions of nearly one market, and that is stated, not hidden |
| Judged period | 2012-01-01 → 2021-01-01, as far as each CFD reaches. The first 60 trading days build the volatility estimate. No development period: nothing is fitted |
| Trade | LONG at the open of the hour bar starting 09:00 Frankfurt (the Xetra open, DST-correct): ask + slippage. Exit at the open of the next hour bar: bid − slippage |
| Variants | ALL: every weekday. COND: only when the previous US cash session's last hour (15:00 → 16:00 New York) fell |
| Stop | 2.5 × the standard deviation of the previous 60 holding-hour returns, at least 3 spreads, checked against the held hour's range |
| Costs | Real quoted bid/ask (night-session spreads included). Slippage per fill = ¼ of the median quoted spread. No commission. No financing: no 17:00 New York rollover is crossed |

## Gates (each test must pass all; the same as IX-2)

| Gate | Requirement |
|---|---|
| min_trades | ≥ 300 |
| net_bps | > 0 at base costs |
| t_day | ≥ 3.6477 |
| costs_x1.5 | net > 0 |
| costs_x2 | net > 0. Failing it is FRAGILE, which fails |
| late_entry | net > 0 when entering at the typical price (O+H+L+C)/4 of the entry hour, plus half its opening spread |
| halves | both chronological halves net > 0 |
| instruments | ≥ 60% of instruments with ≥ 50 trades net > 0 |
| profit_factor | ≥ 1.05 on R |
| top_year_share | no calendar year > 50% of the total net |

## Holdout

2021-01-01 → 2025-01-01, fetched and judged once, for passers only.

Holdout gates:

- net > 0;
- t ≥ z(1 − 0.05/k) for k passers;
- net > 0 at costs × 1.5;
- net > 0 with late entry.

## Written before

IX-3 is registered before **any** index-CFD bar has been loaded by this project, including the IX-2
data, which arrives in the same files. A long-only rule's natural baseline is "long all the time", so
both results will be reported. Beating that baseline is not required, because the claim is about one
hour of the day.

## AI

None. Deterministic rule: Track A only.

## A pass would and would not mean

A pass on both the judged period and the holdout would make IX-3 **FORWARD_TESTING**, not VALIDATED.
Every remaining requirement still stands:

- forward demo performance;
- independent review;
- clean reproduction;
- consistency with demo execution;
- a human promotion record.

**TradeLocker's overnight index spreads are unmeasured, and this rule pays them.** Costs are provisional.

**A FAIL ends the hypothesis.** There will be no re-run with another hour, holding time or condition.
