# SOVEREIGN on everything: the owner's three rules at every setting and on every market

**DESCRIPTIVE BACKTEST, NOT A TEST: the owner's own code on real daily bars at every setting it names and on the other markets the owner trades; it validates nothing, and the best of many rows is expected to look good by chance.** One $200,000 account from 2008-01-04 to 2026-11-20 for each row, the owner's own code (`research/external/sovereign/sovereign_top3_suite.py`, unchanged) through the red team's accounting (`scripts/sovereign_redteam.py`). Every figure is in `research/results/SOVEREIGN-everything.json`.

## Part 1: every setting the specification names, on its seven funds

| Rule | Before costs | 8 bps | 16 bps | 8 bps, a day late | t at 8 bps | Worst fall | Worst day | 2025-2026 | Regimes won | One-year windows that break a prop firm's rules | The live layer stops it |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SOVEREIGN-TITAN-MAX 12d/28d/0.0175 | +118,825 | +13,454 | +17,468 | +78,958 | 0.37 | -17.9% | -6.8% | +99,090 | 2/5 | 47% | 2008-03-24 |
| SOVEREIGN-TITAN-MAX 15d/35d/0.0175 | +267,665 | +107,081 | +46,086 | +50,808 | 1.46 | -17.1% | -7.4% | +89,947 | 3/5 | 49% | 2008-03-25 |
| SOVEREIGN-TITAN-MAX 18d/42d/0.0175 | +147,406 | +39,085 | +20,241 | +55,079 | 0.73 | -18.2% | -7.5% | +39,951 | 4/5 | 52% | 2008-04-02 |
| SOVEREIGN-TITAN-MAX 15d/35d/0.0155 | +261,368 | +101,183 | +14,589 | +56,620 | 1.40 | -16.6% | -7.2% | +86,375 | 3/5 | 46% | 2008-03-25 |
| SOVEREIGN-TITAN-MAX 15d/35d/0.0185 | +271,758 | +114,179 | +23,127 | +56,118 | 1.51 | -16.9% | -7.6% | +89,458 | 3/5 | 49% | 2008-03-25 |
| SOVEREIGN-TITAN-MAX 12d/35d/0.0175 | +217,270 | +18,175 | +1,466 | +45,324 | 0.45 | -17.6% | -7.1% | +94,746 | 3/5 | 47% | 2008-03-24 |
| SOVEREIGN-TITAN-MAX 18d/35d/0.0175 | +102,660 | +71,339 | +11,308 | +43,296 | 1.07 | -17.5% | -7.4% | +62,882 | 4/5 | 48% | 2008-03-25 |
| SOVEREIGN-TITAN-7 funded | +53,696 | +38,104 | -5,037 | +22,502 | 0.75 | -20.7% | -7.5% | -5,157 | 1/5 | 54% | 2008-03-25 |
| SOVEREIGN-TITAN-7 eval | +61,340 | +21,302 | -3,002 | +40,571 | 0.50 | -20.3% | -7.3% | -5,383 | 1/5 | 48% | 2008-03-25 |
| SEC-TSMOM-4 funded | +131,609 | +66,841 | -845 | +87,290 | 1.18 | -18.0% | -3.9% | +46,670 | 3/5 | 26% | 2008-09-22 |
| SEC-TSMOM-4 eval | +119,668 | +84,664 | -1,545 | +71,395 | 1.42 | -16.7% | -5.5% | +34,548 | 3/5 | 21% | 2008-09-22 |

Started on each of five successive days, every rule ends within a dollar or two of the same figure: the five-tranche rebalance is a five-day moving average of the daily target, whatever day it starts on (the widest gap is $2). The specification's 'weekday grid' is not what its code does when it is run every day.

### The drawdown brake

The package's two-step brake halves every position once the account is 5% below its best close and quarters it at 7.5%. A row's brake columns: the share of days it held the account there (8 bps, continuous from 2008), and the same weights with the brake held off. The second half is a diagnostic of what the brake does, not a variant: its worst falls are what the brake exists to stop, and a prop firm's account would not survive them.

| Rule | Days at half size or less | Days at a quarter | Mean exposure with the brake | Without the brake: 8 bps | t | 16 bps | Worst fall | Worst day | Mean exposure | One-year windows that break a prop firm's rules |
|---|---|---|---|---|---|---|---|---|---|---|
| SOVEREIGN-TITAN-MAX 12d/28d/0.0175 | 97% | 92% | 0.29 | +551,488 | 2.17 | +243,193 | -38.8% | -7.1% | 0.99 | 68% |
| SOVEREIGN-TITAN-MAX 15d/35d/0.0175 | 93% | 85% | 0.33 | +754,175 | 2.46 | +385,211 | -39.2% | -7.4% | 1.00 | 66% |
| SOVEREIGN-TITAN-MAX 18d/42d/0.0175 | 95% | 87% | 0.32 | +665,876 | 2.32 | +335,327 | -34.4% | -7.4% | 1.02 | 67% |
| SOVEREIGN-TITAN-MAX 15d/35d/0.0155 | 92% | 84% | 0.33 | +743,729 | 2.50 | +380,830 | -38.2% | -7.2% | 0.99 | 65% |
| SOVEREIGN-TITAN-MAX 15d/35d/0.0185 | 93% | 86% | 0.33 | +763,558 | 2.45 | +390,263 | -39.5% | -7.7% | 1.01 | 66% |
| SOVEREIGN-TITAN-MAX 12d/35d/0.0175 | 96% | 87% | 0.30 | +708,565 | 2.44 | +344,407 | -40.8% | -7.2% | 0.98 | 66% |
| SOVEREIGN-TITAN-MAX 18d/35d/0.0175 | 94% | 86% | 0.33 | +629,748 | 2.25 | +315,390 | -36.1% | -7.4% | 1.02 | 69% |
| SOVEREIGN-TITAN-7 funded | 96% | 93% | 0.33 | +274,039 | 1.48 | +64,091 | -42.5% | -7.5% | 1.14 | 74% |
| SOVEREIGN-TITAN-7 eval | 96% | 93% | 0.32 | +266,730 | 1.49 | +61,049 | -41.6% | -7.2% | 1.12 | 73% |
| SEC-TSMOM-4 funded | 94% | 89% | 0.27 | +227,434 | 1.51 | +59,959 | -39.1% | -5.9% | 0.87 | 49% |
| SEC-TSMOM-4 eval | 93% | 87% | 0.27 | +222,969 | 1.53 | +58,602 | -37.6% | -5.5% | 0.86 | 45% |

## Part 2: the same rules on the other markets the owner trades

Each step adds to the one before; every rule at the package's funded settings. Added markets and their caps: ETH (ETH-USD, crypto, cap 0.25), GER40 (^GDAXI, equity, cap 0.55), UK100 (^FTSE, equity, cap 0.55), JP225 (^N225, equity, cap 0.55), HK50 (^HSI, equity, cap 0.55), COPPER (CPER, metals, cap 0.3), NATGAS (UNG, energy, cap 0.12).

### E1: bitcoin from 2014 in IBIT's place

First bars: IBIT 2014-09-17.

| Rule | 8 bps | 16 bps | 8 bps, a day late | t at 8 bps | Worst fall | Worst day | 2025-2026 | Regimes won | One-year windows that break a prop firm's rules | The live layer stops it |
|---|---|---|---|---|---|---|---|---|---|---|
| SOVEREIGN-TITAN-MAX | +274,429 | +209,307 | +281,208 | 2.42 | -19.3% | -5.5% | +89,569 | 3/5 | 66% | 2008-03-25 |
| SOVEREIGN-TITAN-7 | +133,314 | +88,459 | +120,668 | 1.57 | -21.3% | -8.7% | +15,692 | 3/5 | 71% | 2008-03-25 |
| SEC-TSMOM-4 | +166,877 | +106,807 | +200,212 | 1.95 | -17.1% | -4.7% | +38,866 | 4/5 | 38% | 2008-09-22 |

Where the profit came from, at 8 bps: SOVEREIGN-TITAN-MAX +28,697 without its crypto positions, +138,020 from them alone; SOVEREIGN-TITAN-7 +6,310 without its crypto positions, +204,420 from them alone; SEC-TSMOM-4 +53,614 without its crypto positions, +199,627 from them alone.

### E2: E1 and ether

First bars: IBIT 2014-09-17, ETH 2017-11-09.

| Rule | 8 bps | 16 bps | 8 bps, a day late | t at 8 bps | Worst fall | Worst day | 2025-2026 | Regimes won | One-year windows that break a prop firm's rules | The live layer stops it |
|---|---|---|---|---|---|---|---|---|---|---|
| SOVEREIGN-TITAN-MAX | +439,929 | +410,834 | +527,756 | 2.86 | -20.7% | -8.4% | +116,568 | 4/5 | 72% | 2008-03-25 |
| SOVEREIGN-TITAN-7 | +260,058 | +187,625 | +251,956 | 2.24 | -20.7% | -6.5% | +36,805 | 3/5 | 73% | 2008-03-25 |
| SEC-TSMOM-4 | +409,858 | +218,391 | +346,480 | 3.06 | -18.6% | -4.9% | +51,624 | 5/5 | 39% | 2008-09-22 |

Where the profit came from, at 8 bps: SOVEREIGN-TITAN-MAX +66,649 without its crypto positions, +383,815 from them alone; SOVEREIGN-TITAN-7 +5,860 without its crypto positions, +400,695 from them alone; SEC-TSMOM-4 +57,707 without its crypto positions, +346,973 from them alone.

### E3: E2 and GER40, UK100, JP225, HK50

First bars: IBIT 2014-09-17, ETH 2017-11-09, GER40 2006-04-28, UK100 2006-04-28, JP225 2006-04-28, HK50 2006-04-28.

| Rule | 8 bps | 16 bps | 8 bps, a day late | t at 8 bps | Worst fall | Worst day | 2025-2026 | Regimes won | One-year windows that break a prop firm's rules | The live layer stops it |
|---|---|---|---|---|---|---|---|---|---|---|
| SOVEREIGN-TITAN-MAX | +421,070 | +245,077 | +585,315 | 2.80 | -20.6% | -9.0% | +100,840 | 4/5 | 77% | 2008-07-17 |
| SOVEREIGN-TITAN-7 | +266,431 | +91,683 | +255,460 | 2.30 | -21.7% | -5.6% | +41,618 | 4/5 | 74% | 2008-04-14 |
| SEC-TSMOM-4 | +223,417 | +140,729 | +261,280 | 2.42 | -18.7% | -4.3% | +38,014 | 4/5 | 48% | 2008-07-23 |

Where the profit came from, at 8 bps: SOVEREIGN-TITAN-MAX +10,523 without its crypto positions, +377,206 from them alone; SOVEREIGN-TITAN-7 -14,212 without its crypto positions, +488,915 from them alone; SEC-TSMOM-4 -2,081 without its crypto positions, +396,551 from them alone.

### E4: E3 and copper and natural gas

First bars: IBIT 2014-09-17, ETH 2017-11-09, GER40 2006-04-28, UK100 2006-04-28, JP225 2006-04-28, HK50 2006-04-28, COPPER 2011-11-15, NATGAS 2007-04-18.

| Rule | 8 bps | 16 bps | 8 bps, a day late | t at 8 bps | Worst fall | Worst day | 2025-2026 | Regimes won | One-year windows that break a prop firm's rules | The live layer stops it |
|---|---|---|---|---|---|---|---|---|---|---|
| SOVEREIGN-TITAN-MAX | +453,658 | +76,899 | +287,427 | 2.96 | -17.1% | -5.8% | +82,352 | 4/5 | 74% | 2008-04-14 |
| SOVEREIGN-TITAN-7 | +138,577 | +16,716 | +112,530 | 1.55 | -20.3% | -9.0% | +13,017 | 3/5 | 74% | 2008-04-10 |
| SEC-TSMOM-4 | +130,762 | +15,101 | +155,483 | 1.74 | -16.6% | -4.3% | +7,539 | 4/5 | 44% | 2008-07-18 |

Where the profit came from, at 8 bps: SOVEREIGN-TITAN-MAX -5,081 without its crypto positions, +378,613 from them alone; SOVEREIGN-TITAN-7 -25,139 without its crypto positions, +409,914 from them alone; SEC-TSMOM-4 -19,964 without its crypto positions, +346,316 from them alone.

### The drawdown brake on the other markets

The package's two-step brake halves every position once the account is 5% below its best close and quarters it at 7.5%. A row's brake columns: the share of days it held the account there (8 bps, continuous from 2008), and the same weights with the brake held off. The second half is a diagnostic of what the brake does, not a variant: its worst falls are what the brake exists to stop, and a prop firm's account would not survive them.

| Rule | Days at half size or less | Days at a quarter | Mean exposure with the brake | Without the brake: 8 bps | t | 16 bps | Worst fall | Worst day | Mean exposure | One-year windows that break a prop firm's rules |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 SOVEREIGN-TITAN-MAX | 92% | 82% | 0.37 | +2,501,927 | 3.45 | +1,393,262 | -42.6% | -8.6% | 1.08 | 82% |
| E1 SOVEREIGN-TITAN-7 | 94% | 89% | 0.37 | +1,211,555 | 2.62 | +558,342 | -42.1% | -8.6% | 1.21 | 84% |
| E1 SEC-TSMOM-4 | 91% | 81% | 0.33 | +901,298 | 2.73 | +448,009 | -36.4% | -6.5% | 0.94 | 59% |
| E2 SOVEREIGN-TITAN-MAX | 90% | 80% | 0.39 | +5,005,009 | 4.08 | +2,816,805 | -43.1% | -9.0% | 1.09 | 82% |
| E2 SOVEREIGN-TITAN-7 | 93% | 85% | 0.40 | +2,420,388 | 3.23 | +1,184,888 | -48.1% | -9.0% | 1.22 | 84% |
| E2 SEC-TSMOM-4 | 87% | 77% | 0.35 | +1,626,128 | 3.34 | +862,762 | -41.6% | -6.6% | 0.95 | 58% |
| E3 SOVEREIGN-TITAN-MAX | 91% | 84% | 0.41 | +2,268,203 | 3.22 | +984,946 | -48.6% | -8.9% | 1.21 | 90% |
| E3 SOVEREIGN-TITAN-7 | 92% | 87% | 0.42 | +1,007,980 | 2.42 | +332,492 | -50.8% | -8.9% | 1.31 | 92% |
| E3 SEC-TSMOM-4 | 92% | 83% | 0.33 | +856,266 | 2.64 | +348,310 | -41.3% | -6.6% | 0.97 | 70% |
| E4 SOVEREIGN-TITAN-MAX | 91% | 85% | 0.42 | +1,420,956 | 2.73 | +526,307 | -39.2% | -15.8% | 1.24 | 92% |
| E4 SOVEREIGN-TITAN-7 | 94% | 88% | 0.41 | +589,582 | 1.94 | +126,747 | -50.2% | -15.8% | 1.32 | 93% |
| E4 SEC-TSMOM-4 | 93% | 86% | 0.32 | +537,098 | 2.12 | +162,023 | -38.1% | -11.8% | 0.99 | 71% |

## How to read it

- A row is a description of the past, not a test. Among this many rows the best is expected to look good by chance; no row was registered, and none can be validated on these days, which are now read.
- The bar a registered test must clear here is t 3.0. Read the t column against it.

