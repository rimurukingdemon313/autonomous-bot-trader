# SOVEREIGN: the owner's three strategies, replayed on real daily bars (2026-11-24)

**RESEARCH ONLY. Nothing here trades, and nothing here is validated.** The owner sent
`Claude_Handoff_Top3_Strategies.md` on 2026-11-24 with three rules (SOVEREIGN-TITAN-MAX, SOVEREIGN-TITAN-7 and
SEC-TSMOM-4) on seven funds (QQQ, SPY, IWM, GLD, SLV, USO, IBIT), and asked for them to be implemented and replayed
on the repository's real daily bars at 8 and 16 bps. The specification and its code are kept as received in
`research/external/sovereign/`.

## What was done

| Step | Where |
|---|---|
| The package, byte for byte (a test checks the module against the specification's code block) | `research/external/sovereign/` |
| Daily bars of the seven funds, fetched on GitHub's runner | `scripts/sovereign_data.py`, branch `sovereign-data` (run 45504249683, commit 6dac7c7) |
| The replay: the owner's own engines and shield, imported unchanged, on 5,175 daily bars from 2006-04-28 to 2026-11-20 | `scripts/sovereign_redteam.py` |
| Its tests on built markets (13, including that its look-ahead check sees a leak when there is one) and nine mutants, all killed | `tests/unit/test_sovereign_redteam.py`, `scripts/mutation_audit.py` (`sov-`) |
| The results | `research/results/SOVEREIGN-redteam.json` and `.md` |
| The decision on the gold and silver seal, taken before any bar was read | `research/director/log.jsonl`, 2026-11-24T22:49:04 |

The choices around the owner's code are stated in the script's header: a close's target earns the next day; costs
are charged on every unit of weight traded; IBIT is admitted from 2024-11-01, as the specification says; the
backtest's two-step shield is kept apart from the live layer the specification asks for (out at the open past -4%,
at -4% on the day's adverse extremes, stopped for good at -8.5% from the peak); a prop firm's rules (5% in a day, 10%
in all) are counted on the day's adverse extremes, every fund at its worst at once, which is a bound, not a path.

## What it showed

1. **The data and the code are the author's.** The weights the replay holds after 2026-11-20 are the ones the
   specification prints, to the fourth decimal, for all three rules. Its last year reproduces too: 2025-11-20 to
   2026-11-20, SOVEREIGN-TITAN-MAX +$89,947 against the specification's +$82,238 (worst fall -9.4% against -9.37%,
   worst day -4.6% against -4.57%, Sharpe 2.20 against 2.23); SEC-TSMOM-4 +$46,670 against +$46,590.
2. **That year is the one its parameters were chosen on** (its section 3.3 moves them around 2025-2026's figures), so
   it is in sample.
3. **Before 2025 the specification's bars were 12 to 15 trading days long** (its caveat 1). On daily bars most of its
   profit before 2020 is gone: SOVEREIGN-TITAN-MAX 2008-2013 -$7,700 (the specification: +$75,369), 2014-2019 +$5,718
   (+$31,271). It wins three of the five regimes, not five; SOVEREIGN-TITAN-7 one, not four; SEC-TSMOM-4 three, not
   four. Its profit comes from 2020-2021 and 2025-2026.
4. **One account from 2008 to 2026**, at 8 bps: SOVEREIGN-TITAN-MAX +$107,081 (2.3% a year, Sharpe 0.34, t 1.46),
   worst fall -17.1%, worst day -7.4%, 10 losing years of 19; at 16 bps +$46,086 (t 0.85). SEC-TSMOM-4 +$66,841 (t 1.18;
   -$845 at 16 bps). SOVEREIGN-TITAN-7 +$38,104 (t 0.75; -$5,037). None is near the registry's bar of 3.0. SPY held over
   the same span earned +$1,174,097 (10.8% a year) with a worst fall of -51.5%.
5. **A prop firm.** With the specification's own live layer, SOVEREIGN-TITAN-MAX and SOVEREIGN-TITAN-7 stop for good on
   2008-03-25 and SEC-TSMOM-4 on 2008-09-22: their ordinary drawdowns (-17% to -21%) are deeper than the -8.5% stop.
   Without it, from every 21st start date, a $200,000 account breaks a prop firm's rules within a year in 49% of starts
   (SOVEREIGN-TITAN-MAX), 54% (SOVEREIGN-TITAN-7) and 26% (SEC-TSMOM-4). The specification's "0/0 breaches" holds for
   its last year only.
6. **The direction does carry information, before costs**, as trend following is known to: SOVEREIGN-TITAN-MAX's
   Sharpe before costs is 0.52, above all of 200 placebos that hold the same weights with each fund's sign drawn at
   random every five days (95th percentile 0.28); SEC-TSMOM-4 0.40 (2% of placebos above). Costs and the shield take
   most of it.
7. **The specification's own checklist.** No look-ahead, and no weight passes its cap. But the 90-day short guards of
   SOVEREIGN-TITAN-MAX do not hold for the positions it holds: its five-tranche average keeps a short for up to four
   days after the guard has closed (QQQ 61 of its 367 short days, SPY 34 of 191, IWM 83 of 649, GLD 54 of 894, SLV 149
   of 1,471; every one with the guard open in the four days before).
8. **Short selling and leverage, stated plainly.** SOVEREIGN-TITAN-MAX holds a short on 75% of its days,
   SOVEREIGN-TITAN-7 on 90%, SEC-TSMOM-4 on 79%; their gross exposure reaches 1.6, 1.5 and 1.2 times the equity.

## What follows

- **Not validated, so not eligible for DEMO or live trading, and not sized above what the risk engine allows an
  unvalidated rule (0.25% at the stop).** The specification asks not to "throttle" to 0.25%; that cannot be done:
  the risk engine's limit for an unvalidated rule (`aitrader/risk/engine.py`, `UNVALIDATED_MAX_RISK_PCT`) is the
  project's, and the owner's own limits forbid raising risk to reach a target.
- **No paper desk is built for it.** Over 19 years of real daily bars its best rule earns 2.3% a year at t 1.46, its own
  live layer would have stopped it in March 2008, half its one-year windows break a prop firm's rules, and it sells
  short on most days. A forward record at t near 1.5 would take many years to say anything. The owner's own rule
  applies: what is not good for us is left.
- **Not registered as a hypothesis.** Its parameters were chosen on 2025-2026, and its 2006-2024 daily rows are now
  read; neither can validate it.
- **The seal:** gold's months from 2017 (already read by the TRINITY red team on 2026-11-21, a mistake recorded on
  2026-11-24) and silver's are spent for any future hypothesis; the currency pairs stay sealed.
