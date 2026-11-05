# The research queue (owner, 2026-11-04 and 05: "anything that makes us a profit; never stop")

This queue is worked through one candidate at a time, by a recurring check-in. Each candidate is handled the same
way:

1. Pre-registered before its data is fetched or any outcome is computed: a frozen spec and frozen code hashes.
2. Given a threshold that counts every earlier test on its universe (`research/registry.jsonl`).
3. Split into development, validation, and a holdout opened once and only after a pass.
4. Judged once, with the result committed and reported to the owner as it is. A failure is a result, not a reason
   to stop.

The order is set by mechanism and evidence. A candidate needs a reason to exist beyond a pattern, and fresh data
where possible: the FX M5 2009-2016 data carries 166+ tests and a bar of 3.6. Only a candidate that passes and is
validated is ever proposed as a paper strategy (CLAUDE.md rule 14), never real money.

| # | Id | Question | Why it might pay | Known against it | Status |
|---|---|---|---|---|---|
| 1 | VRP-1 | Short VIX futures (VIXY) while the VIX curve is in contango | The insurance premium: buyers of crash protection overpay on average | Rare catastrophic days (Feb 2018, Mar 2020); a famous trade | FAILED (2026-11-05) |
| 2 | FOMC-1 | Long the S&P 500 into scheduled FOMC announcements | Lucca & Moench (2015): most of the equity premium 1994-2011 was earned in the 24 h before FOMC | Kurov, Wolfe & Gilbert (2021) find it faded after 2015 | FAILED (2026-11-05, as FOMC-1A) |
| 3 | XSM-1 | Crypto cross-sectional momentum: hold last week's strongest large coins | Liu, Tsyvinski & Wu (2022): momentum across coins, retail-driven | Point-in-time universe and costs; CR-1's time-series momentum failed | FAILED (2026-11-05) |
| 4 | VOLM-1 | Volatility-managed S&P 500 exposure (Moreira & Muir 2017): its alpha on the market, at the market's own risk | Volatility clusters while returns do not scale with it | Cederburg et al. (2020): weak out of sample | FAILED (2026-11-05; only t: alpha +2.6% a year at t 1.27) |
| 5 | GSR-1 | Gold/silver ratio mean reversion | Two metals with a shared driver; the ratio has historically reverted | Long regimes without reversion; costs on silver | **RUNNING** (registered 2026-11-05: z of the ratio over a year, in at 2, out at 0 or after a year; t >= 3.0) |
| 6 | SEC-1 | US sector ETF momentum, monthly (industry momentum, Moskowitz & Grinblatt 1999) | Industries trend for months | Crowded since publication | queued |
| 7 | PHD-1 | The pre-holiday effect in US equity indices | Ariel (1990) and later | Likely faded; few events a year | queued |

**Live, on fresh forward data, judged at fixed dates:** CONF-1 (do the H1 agreements the confidence floor refuses
pay?), on 2026-11-20 and 2026-11-27. It costs nothing.

**Done:**
- VOLM-1 FAILED, on t alone: volatility-managed S&P 500 exposure earned an alpha of +2.6% a year over 1995-2021 (t 1.27 against 3.113). It was positive in both halves and with costs doubled, and its drawdown was -50% against the market's -65%. A real but weak effect the bar cannot confirm.
- XSM-1 FAILED: among the 20 largest coins, the top 4 by 21-day return beat the 20 by +0.22% a week, 2018-10..2024-06, at t 0.48 against 3.144: positive to 2021, negative from 2022.
- FOMC-1A FAILED: the pre-FOMC drift earned +0.07% net per event, 2016-2021, at t 0.81 against 3.163. Ordinary weeks did better in the same window. FOMC-1 was abandoned before any outcome (its one-runner fetch could not finish).
- CONF-2 ABANDONED (2026-11-05, before any outcome was read). The senior approved none of the 52 agreements it judged in shadow, so its approved group could not fill. The reviews stopped to save the owner's money.
- VRP-1 FAILED (short VIX futures in contango: +61% a year at t 2.33 against 3.0; the filter added nothing, t 0.46; drawdown −77%).
- XTS-1 FAILED (crypto time-series momentum: t 2.87 against 3.09; timing t 1.87).
- MEH-1 FAILED (month-end hedge flows: +3.3 bps gross, +1.2 net, t 1.04 against 3.61).
- FND-1 was ABANDONED before any outcome; FND-1A FAILED (crowded funding: the timing was negative).
