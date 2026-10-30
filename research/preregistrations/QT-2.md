# QT-2: the London true open, with a stop wide enough to pay its costs? (preregistration)

**Written, frozen and committed before any QT-2 outcome was computed.** Its only input is QT-1's
recorded development result for T3 (`research/knowledge/QT-1.json`). No QT-2 configuration was
filled or measured before freezing.

| | |
|---|---|
| Frozen spec | `research/specs/QT-2.json` |
| Spec sha256 | `8908a06cab8dec38552f7df4142d7220bdce9f93d7f7f35c5c5327ba42af6e36` |
| Code | `aitrader/research/discovery/quarters_wide.py` (qt-2.0.0), with `quarters.py` (qt-1.0.0), ID-1's `intraday.py` and `scripts/id1.py`, and `scripts/qt2.py` (all hashed in the spec) |
| Data | ID-1's M5 bid/ask bars 2009–2016, all eight instruments |
| Untouched test | The fx-majors holdout, 2017-01 on, stays sealed |

## Why

QT-1's T3, the London true open, was the only rule in the program that showed an effect before
costs. On 2009–2013 it earned +0.10R a trade before costs and beat its matched random (Welch
t 2.97). Costs, however, take about 0.16R a trade, which left it at −0.05R net, so it was not
promoted. A trade's costs are fixed in pips, so their share of R falls as the stop widens. QT-2
asks whether the same signal, with a wider stop and a longer hold, keeps enough of its edge to pay
them.

## The rule

The signal is T3's, unchanged (see `QT-1.md`), and only three things move:

- **The stop** is `stop_mult` times T3's distance from the signal close.
- **The target** is `r` times the new stop distance.
- **The time exit** is at `until`: 06:00 New York (London's end, as in T3) or 12:00 New York (the
  end of New York AM).

**Every configuration looked at, all charged (12).** The grid is `stop_mult` {1, 1.5, 2} ×
`r` {1.5, 2} × `until` {06:00, 12:00 New York}. The cell (1, 2, 06:00) is T3 itself.

**Selection, on development 2009–2013, frozen.**

- **What is chosen.** Of the configurations that pass every ID-1 promotion gate, the one with the
  highest net R. The gates:
  - at least 300 trades;
  - net R > 0;
  - t ≥ 2.0;
  - profit factor ≥ 1.10;
  - beats matched random by t ≥ 2.0;
  - 60% of symbols positive.
- **If none passes,** QT-2 is FAILED and validation is not run.

**Judgement, on validation 2014–2016, the selected configuration only.** These are ID-1's gates,
all required:

- t (daily) ≥ **3.568**, the registry's Bonferroni over every test touching 2014–2016 plus this
  one;
- net R > 0;
- profit factor ≥ 1.20;
- net R > 0 at costs × 1.5;
- 60% of symbols positive;
- 60% of three-month windows profitable;
- beats its matched random by t ≥ 2.0;
- 75% of the 12-cell grid positive on validation.

**After the result.**

- **Nothing passes.** The Quarters line ends here and nothing in the bot changes.
- **A configuration passes.** It is still not traded until the sealed holdout confirms it,
  through its own preregistration, and a paper-forward run follows that.
