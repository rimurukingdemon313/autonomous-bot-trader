# DIV-2-H: declaration before the holdout is opened

Written and committed **before** `python scripts/div2.py holdout` runs. Nothing below changes the
frozen DIV-2 spec (sha256 `cb440fbd…`); it states, in advance, what the frozen code will and will
not see in 2021-01 onward, so the result cannot be reinterpreted afterwards.

- **Why it may be opened.** DIV-2 PASSED every preregistered gate on 1990–2007 for both hypotheses
  (`research/knowledge/DIV-2.json`): H1 net t 4.34, H2 net t 4.38. DIV-2.md: "Opened once, only for
  DIV-2 passers."
- **What decides it (frozen, DIV-2.md):** per hypothesis, mean monthly net > 0 **and** mean net with
  costs ×2 > 0 over 2021-01 onward. A hypothesis meeting both is VALIDATED; otherwise REJECTED.
- **Known reduced universe, declared now.** The currency class comes from the pinned H.10 vintage of
  2018-10-17 (frozen in `aitrader/data/h10.py`), so **no currency is held in the holdout**. The holdout
  therefore tests 16 assets: 10 equity indices, 2 US bond yields, 4 commodities. In 1990–2007 the
  portfolio without currencies still earned +1.05% (H1) / +0.95% (H2) a month (leave-one-class-out),
  so the reduced universe is a weaker test, not a different strategy. Adding a newer FX source would
  change frozen code and is not done.
- **Already-seen warning, declared now.** 2008–2020 (descriptive, never a gate) was weak: H1 net
  Sharpe 0.11, H2 0.37. Trend following's published 2010s were also weak; 2022 was a strong year
  that is public knowledge. A holdout pass is therefore one honest, small sample (≈ 69 months), not
  proof of a durable edge, and it will be reported that way.
- **Retail-CFD line** is reported, not gating, as preregistered.
- **Single use.** The workflow refuses to run if `DIV-2-H` has a verdict, and `open_final_test`
  allows one opening.
