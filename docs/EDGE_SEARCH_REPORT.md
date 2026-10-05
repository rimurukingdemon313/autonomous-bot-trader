# Edge search (final mission): what was tested and what the evidence says

**Status: IX-4 PENDING. Every other program in this round FAILED. Nothing is promoted.**

The machine-readable record is `research/registry.jsonl` and `research_status.json`. Each program has a
preregistration in `research/preregistrations/` that was committed **before** its outcome existed, and a
result in `research/knowledge/`.

## 1. The bottleneck, measured

The question was why ID-2's ML ranking (gross +0.19R, net +0.09R, t 1.39) never passed. The cost
decomposition of its best configurations:

| | Spread | Commission | Slippage | Total cost | Gross | Net |
|---|---|---|---|---|---|---|
| Share of cost | 57% | 35% | 8% | 0.10R | +0.19R | +0.09R |

ID-2 itself showed two things:

- **The ranking is mostly cost avoidance.** A model given only the cost-to-stop ratio ranks better than
  the full model.
- **Lengthening the holding scale reduces gross faster than cost.** Gross fell from +0.19R at S5 to
  +0.10R at S60.

The core fact is cost relative to the size of the move. Round-trip cost as a fraction of the standard
deviation of the move, FX majors 2007–2012:

| Horizon | 1 h | 4 h | 8 h |
|---|---|---|---|
| Cost / σ (EURUSD → NZDUSD) | 0.10–0.23 | 0.05–0.12 | 0.03–0.08 |

So an intraday FX rule needs more than 3 bp of predictable move per trade. Every family below fell short
of that.

## 2. What was tested in this round (every look counted in the registry)

| ID | Hypothesis and economic reason | Data | Trades | Gross | Cost | Net | t | Verdict |
|---|---|---|---|---|---|---|---|---|
| EX-1 | 21 FX session and order-flow families: Asian-session USD drift, reversal of illiquid-hours moves (Grossman–Miller), session momentum and reversal (Elaut et al.), activity-conditioned continuation (Llorente et al.) | FX majors M15, 2007–2012, real bid/ask | 457–18,327 each | ≤ +3.96 bp (best F1 24 h); every other ≤ +2.24 bp | 1.4–3.1 bp | best +1.2 bp (t 0.3) | ≤ 0.32 | FAILED: gross is below cost in every family |
| EX-2 | Intraday momentum into the futures settlement, FX and gold | FX/gold M15, 2007–2012 | 94–16,997 | FX +0.06 bp; gold +3.0 / +7.8 bp | 2.8–3.1 bp | gold +0.1 / +4.7 bp | gold 0.09 / 1.58 | FAILED (FX); gold carried to IX-1 |
| IX-1 | Intraday momentum into the COMEX settlement (Baltussen et al. 2021) | Gold, silver M5, 2013–2016 (unseen) | 1,883 / 458 | +0.72 / +3.25 bp | 11.7 bp | −10.9 / −8.4 bp | −20.4 / −7.5 | FAILED: the gold hint did not replicate; silver's spread is prohibitive |
| IX-2 | Last-hour momentum into the cash close (Gao et al. 2018; Baltussen et al. 2021): gamma and leveraged-ETF hedging | 6 index CFDs H1 (S&P 500, Nasdaq-100, Dow, Nikkei, Hang Seng, ASX), 2012–2020 | 10,511 / 2,824 (102 / 27 a month) | +1.07 / +2.61 bp | 4.3 bp | −3.24 / −1.63 bp | −7.1 / −3.1 | FAILED: the signal exists in the predicted direction but is smaller than the CFD spread |
| IX-3 | Overnight drift at the European open (Boyarchenko et al. 2023): dealer inventory compensation | US index CFDs H1, 2013–2020 | 5,431 / 2,221 | +0.003 / −0.97 bp | 3.3–3.6 bp | −3.55 / −4.23 bp | −7.8 / −5.5 | FAILED: no drift in the CFD |
| IX-4 | NASDAQ opening-candle EMA(12) signal (from a video; its +982% claim is never used) | Nasdaq-100 CFD M5, dev 2012–2016, val 2017–2020 | — | — | — | — | — | PENDING (data downloading) |

Every program was also stressed at:

- costs × 1.5 and × 2;
- a delay or late entry;
- both chronological halves.

None reached positive net at base cost, so none survives the stresses either. The full stress numbers
are in the knowledge files.

## 3. Integrity findings in this round

- **Stop fills.** Filling a stop exactly at its level manufactured +1.5 to +3 bp of gross edge on a pure
  random walk. IX-4 fills stops through the level, and a regression test forbids any exit from showing an
  edge on a random walk. It was verified to fail against the old fill.
  - IX-1/IX-2/IX-3 used the old convention, frozen before this was found.
  - The bias is small there: 2–9% of trades stopped out.
  - It is optimistic, so it can only have flattered results that failed anyway.
- **Frozen study code.** A repository-wide lint auto-fix had silently changed frozen, registered study
  code. The frozen-design tests caught it; the edits were reverted and those files are exempted.
- **Holdouts.** None was opened.
  - fx-majors 2017+ is still sealed.
  - The index-CFD holdout (2021–2024) was never even downloaded.

## 4. What this establishes, and what it does not

**Established, for retail CFD/FX execution priced at historical Dukascopy bid/ask:**

- Intraday price-pattern edges in FX majors are smaller than the spread. That covers 160+ registered FX
  tests across this project at every horizon from 5 minutes to 1 day.
- The best-documented academic intraday effects in equity indices have the predicted **sign** but not
  the **size** to pay a CFD spread:
  - momentum into the close: +1 to +2.6 bp gross against 4.3 bp of cost;
  - the European-open drift: none.
- Those effects are measured in futures at about 0.25 bp of cost, which is roughly 15–20 times cheaper
  than a retail CFD.

**Not established:**

- That no edge exists anywhere. Execution with futures-level costs was not available here.
- TradeLocker's actual spreads are unmeasured. If they are materially tighter than Dukascopy's, IX-2's
  STRONG variant (gross +2.6 bp) is the first thing to re-measure, forward and in demo, not by re-mining
  history.

## 5. Final status

Pending IX-4. If IX-4 fails: **EDGE NOT FOUND — NO AFTER-COST EDGE IN THE ACCESSIBLE RESEARCH SPACE.**
