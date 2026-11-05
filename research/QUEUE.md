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
| 5 | GSR-1 | Gold/silver ratio mean reversion | Two metals with a shared driver; the ratio has historically reverted | Long regimes without reversion; costs on silver | FAILED (2026-11-05) |
| 6 | SEC-1 | US sector ETF momentum, monthly (industry momentum, Moskowitz & Grinblatt 1999) | Industries trend for months | Crowded since publication | FAILED (2026-11-05) |
| 7 | PHD-1 | The pre-holiday effect in US equity indices | Ariel (1990) and later | Likely faded; few events a year | FAILED (2026-11-05) |
| 8 | EMC-1 | Emerging-market currency carry: hold the higher-yielding of the emerging currencies a CFD broker quotes (MXN, ZAR, TRY, PLN, HUF, CZK) against the dollar, ranked by policy-rate differential | The carry premium: high-yield currencies pay their rate differential on average (Lustig & Verdelhan 2007; Burnside et al. 2011), as pay for crash risk | Crashes (2008, 2013, 2018 TRY); wide spreads and swap markups on exotic CFDs. Fresh data: no test here has used emerging currencies | FAILED (2026-11-05) |
| 9 | LVOL-1 | The low-volatility anomaly: the S&P 500 low-volatility ETFs (SPLV, USMV) against SPY at equal risk | Leverage-constrained investors overpay for risky stocks (Frazzini & Pedersen 2014, "Betting Against Beta") | Only since 2011; crowded since 2016; a CFD broker may not quote these ETFs. Fresh data: these ETFs are untested here | FAILED (2026-11-05) |
| 10 | TSY-1 | The Treasury auction cycle: short the 7-10 year Treasury ETF (IEF) in the days before each 10-year note auction, and long in the days after | Lou, Yan & Zhang (2013): Treasury prices fall before auctions and recover after, because dealers must absorb the new supply (1980-2008; a 10-year note strategy's Sharpe was about 0.9 after costs). Fleming, Liu & Nguyen (NY Fed) still see the pre-auction rise in yields in recent intraday data | Non-dealers now absorb more of each auction, and the price pressure has not grown. Fresh data: everything after 2008 is outside the paper's sample, and no test here has used Treasury auction dates | **RUNNING** (registered 2026-11-05: short IEF over the 5 trading days before each 10-year note auction, long over the 5 after; t >= 3.065) |
| 11 | TME-1 | The Treasury month-end effect: hold IEF over the last three trading days of each month | Hartley & Schwarz (2019): coupon Treasuries earned their excess return in the last few days of the month (1990-2018), from insurers' and index funds' month-end buying. Month-end Treasury trading has grown since 2020 (NY Fed) | A test on TLT since 2002 did not find it (CXO Advisory); a CFD's costs take a large share of about 0.25% a month. Fresh: 2019 on is after the paper's sample | **RUNNING** (registered 2026-11-05, before TSY-1's result was read: long IEF over each month's last 3 trading days, 2003-2018; t >= 3.078) |

**Live, on fresh forward data, judged at fixed dates:** CONF-1 (do the H1 agreements the confidence floor refuses
pay?), on 2026-11-20 and 2026-11-27. It costs nothing.

**Done:**
- LVOL-1 FAILED: half SPLV, half USMV earned an alpha of +0.9% a year on the S&P 500 at its 0.70 beta, 2012-2020 (t 0.44 against 3.154). Positive to 2016, not after. The runner's commit was refused by GitHub, so the verdict is recorded from its job log; the program is not run again.
- EMC-1 FAILED: the top 3 of 6 emerging currencies by policy-rate differential lost 0.63% a year over 2005-2019 (t -0.19). The +6.7% differential was eaten by -4.8% of depreciation and the CFD's costs. Positive to 2012, negative after.
- PHD-1 FAILED: the S&P 500 on a holiday's eve earned +0.053% net (236 events, 1995-2021, t 0.82), and beat ordinary days by +0.065% (t 0.98). 1999 supplied 71% of the total.
- SEC-1 FAILED: the top 3 of 9 US sectors by six-month return lost 0.53% a year to all nine over 2000-2017 (t -0.31). It was positive to 2008 (t 0.93), negative after (t -1.58).
- GSR-1 FAILED, every gate: the gold/silver pair against a two-sigma ratio lost 1.2% a year over 2002-2019 (t -0.31), in 19 trades. One trade against the 2010-11 silver run lost 40%.
- VOLM-1 FAILED, on t alone: volatility-managed S&P 500 exposure earned an alpha of +2.6% a year over 1995-2021 (t 1.27 against 3.113). It was positive in both halves and with costs doubled, and its drawdown was -50% against the market's -65%. A real but weak effect the bar cannot confirm.
- XSM-1 FAILED: among the 20 largest coins, the top 4 by 21-day return beat the 20 by +0.22% a week, 2018-10..2024-06, at t 0.48 against 3.144: positive to 2021, negative from 2022.
- FOMC-1A FAILED: the pre-FOMC drift earned +0.07% net per event, 2016-2021, at t 0.81 against 3.163. Ordinary weeks did better in the same window. FOMC-1 was abandoned before any outcome (its one-runner fetch could not finish).
- CONF-2 ABANDONED (2026-11-05, before any outcome was read). The senior approved none of the 52 agreements it judged in shadow, so its approved group could not fill. The reviews stopped to save the owner's money.
- VRP-1 FAILED (short VIX futures in contango: +61% a year at t 2.33 against 3.0; the filter added nothing, t 0.46; drawdown −77%).
- XTS-1 FAILED (crypto time-series momentum: t 2.87 against 3.09; timing t 1.87).
- MEH-1 FAILED (month-end hedge flows: +3.3 bps gross, +1.2 net, t 1.04 against 3.61).
- FND-1 was ABANDONED before any outcome; FND-1A FAILED (crowded funding: the timing was negative).
