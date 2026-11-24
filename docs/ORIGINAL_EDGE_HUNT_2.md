# Original edge hunt, round 2: the map, twenty hypotheses, and the three chosen

**RESEARCH ONLY · NOTHING HERE IS A PROFIT CLAIM · WRITTEN BEFORE ANY OF ITS DATA WAS READ.** The owner asked on
2026-11-16 (18:57 UTC) for a new discovery round: no published strategy copied or renamed, a map of where a net
profit could come from, twenty radically different hypotheses scored on originality, economic basis, testability,
data and net-profit potential, and the best three preregistered and tested. This file was written on 2026-11-22
from 01:55 UTC, after the record was reread and the web searches below were made. No price, return or event of the
three chosen hypotheses had been read when it was committed.

**بالعربي:**
- رجعت قريت كل السجل (94 فرضية مسجلة، و66 سطر بدفتر الاختراعات، والعوائل المسكّرة)، وطلّعت 20 فرضية جديدة من 7 مصادر ربح.
- لكل فرضية كتبت: الآلية، والمعادلة، وأقرب الأعمال السابقة، وشلون تختلف عنها، وإذا كانت معروفة أگول معروفة.
- القاعدة اللي اخترت بيها: الفرضية لازم تعبر فحص القوة الإحصائية وفحص التكاليف ببيانات مجانية ومو مختومة. ومن اللي عبروا، أخذت أعلى 3 درجات:
  - **KRP-1:** علاوة السعر الكوري لكل عملة.
  - **SCX-1:** انحراف العملات المستقرة بالويكند لمن يكون الإصدار والاسترداد مسكّر.
  - **UDL-1:** البيع الإجباري لمن Upbit يشيل عملة.
- الباقي ما انرفض بسبب نقص البيانات. كل وحدة مكتوب جنبها شنو البيانات اللي تحتاجها ومنين تنجاب.

## 1. What was excluded before starting

The record was reread so that nothing judged is retested under a new name:

- `research/registry.jsonl`: 94 registered hypotheses, 84 verdicts (72 FAILED). Families: SMC, trend, reversion, FX carry and
  rates, COT, FX fixes, multi-asset trend (DIV), index calendar and intraday effects (RC-EQ, IX-1 to IX-4, NE-1,
  FOMC-1, PHD-1, RBL-1, MEH-1, TME-1, TSY-1), crypto funding carry and cross-venue funding (CR-1 to CR-5, RADAR-1),
  crypto momentum (XTS-1, XSM-1), leverage stress (LIQ-1, EXF-1, SQZ-1, CASC-1, BAS-1, SPL-1), new listings
  (NEWL-1), VIX contango, gold/silver ratio, sectors, EM carry, low volatility, energy term structure.
- `research/inventions.jsonl`: 66 lines (the mission of 2026-11-16 and the scheduled edge hunt).
- `research/QUEUE.md`: the ideas dropped before building, among them three that came up again while this round
  was being drafted and are therefore **not** in it: stablecoin issuance and later bitcoin returns (STB-1, dropped:
  issuance follows rallies), the macro-announcement-day premium (t about 2.1 at full strength, half of it costs),
  and options-expiration pinning (the OpEx calendar and 0DTE strike pinning, both dropped). The Coinbase premium
  (CBP-1), bitcoin's weekend move and Monday's index session, CME weekend gaps and token unlocks were also already
  rejected.
- The families `docs/DISCOVERY_PROGRAM.md` closed: intraday price patterns, session and hour-of-day effects, fixes
  and month-end flows, FX carry, funding carry and extremes, positioning (COT), the calendar anomalies, crash filters
  on TRND-1, single-coin and cross-coin momentum, volatility-managed exposure, short volatility through ETPs.
- FX majors and gold from 2017 on are sealed (`research/holdout.json`; XAUUSD and XAGUSD are in that universe, and
  contamination is a property of market periods, so a copy of gold's price from another vendor is sealed too).

## 2. The map: where a net profit can come from

A trade earns a net profit only if someone on the other side pays for it. For an owner who trades small, daily or
slower, long or through swap-free CFDs (no interest, no funding), the payers are:

| Source (who pays) | Why it can persist | Open to the owner | Closed by the record or the rules | Round 2 |
|---|---|---|---|---|
| **A. Segmented clienteles** (participants who cannot reach the other market) | Capital controls, venue bans, listing rules: arbitrage needs access most capital does not have | Crypto spot on global venues; index CFDs | Coinbase premium (hours), country-ETF NAV effects | KRP-1, AHP-1, AIB-1 |
| **B. Forced or price-insensitive flows** (sellers or buyers with a deadline or a rule) | The flow is dated or mechanical; the trader is not paid to wait | BTC/ETH, index, energy CFDs; spot coins | Month-end and fix flows, calendar dummies, liquidation rebounds (LIQ-1) | UDL-1, TGA-1, MGN-1, HPS-1, JDR-1 |
| **C. Linked markets that drift apart** (the arbitrage is slow or blocked) | Transport, substitution or redemption limits | Stablecoin pairs, oil and metal CFDs | Funding and basis (carry) | SCX-1, BWT-1, PPS-1 |
| **D. Market makers who cannot hedge** (inventory risk when the reference market is shut) | The hedge market is closed at weekends; makers widen and let the price float | Tokenized gold and stocks (spot) | Intraday inventory effects (closed family) | PAXG-1, XST-1, AMM-1 |
| **E. Operational and protocol constraints** (queues, grids, closures) | The constraint is physical or written into a protocol | ETH, platinum, natural gas CFDs | Delivery rolls, dead zones | ESQ-1, PGL-1, NGW-1 |
| **F. Order flows that cannot clear** (rules that stop trading) | Price limits leave orders unfilled for a day | Index CFDs (HK50, China50) | Stops, sweeps, round numbers (intraday, SMC) | CHL-1 |
| **G. Structural premia** (paid for bearing risk or by arithmetic) | Compensation, not mispricing | Any long book | Volatility selling, carry | RBP-1, ANC-1 |

What the map says before any test: for this owner, categories D and F are almost all intraday (closed families, and
a speed race a small account loses), and the short side of altcoins is excluded. What is left at a daily horizon is
**segmentation (A)**, **dated forced flows (B)**, and **primary markets that close at weekends (C/D)**. The three
chosen hypotheses come from exactly those.

## 3. The twenty hypotheses

Each names its mechanism and the mathematics of the prediction, the closest known work (at most five; "search"
means a web search result of 2026-11-22, not read in full; "memory" means known from the literature but not opened
in this session; "record" means this repository), how it differs, whether it is known, its data, and what the owner
would need to trade it. Scores (1 to 5) are in section 4.

### A1 · KRP-1 — the Korean coin premium (segmented clientele) · **NEW as a test**
- **Mechanism.** Korean residents trade on KRW venues (Upbit, Bithumb) that foreigners cannot use, and capital
  controls make moving KRW out slow and capped. Korean retail concentrates on altcoins (tail assets carry 58% of
  Upbit's volume against 23% on Binance, 4Pillars). When Korean demand lifts a coin's KRW price above its global
  price by more than the premium Korea pays on bitcoin, two things follow. Korean arbitrageurs can close a
  **coin-relative** gap without moving KRW abroad: they sell the coin on Upbit, buy bitcoin there, ship the bitcoin
  out, and buy the coin on the global venue. That buying lifts the global price (**arbitrage pressure**). And if the
  demand was retail mania (noise traders), the coin later falls back everywhere (**froth**).
- **Mathematics.** Let `P^U_i` (KRW), `P^B_i` (USDT) and `X` (KRW per USDT). The premium is
  `π_i = ln P^U_i − ln X − ln P^B_i`, and the relative premium `ρ_i = π_i − π_BTC` cancels `X` and the common
  capital-control wedge. An arbitrageur earns `ρ_i − c` a round trip. With capacity `K` and global price impact
  `λ_i` (Kyle), `E[r^B_i − r^B_mkt | ρ_i] = λ_i · min(K, q(ρ_i − c)) > 0` for `ρ_i > c`, larger for small coins
  (larger `λ_i`): **H1, positive excess return over the next 24 hours.** Noise demand `D_i` mean-reverts at rate
  `κ`, so `E[r_i(t → t+20)] = −κ·D_i < 0`: **H2, negative excess return over the next 20 days.**
- **Closest known work.**
  1. Makarov & Schoar (2020, JFE), "Trading and arbitrage in cryptocurrency markets" (search): premia are much
     larger across countries, track buying pressure, and persist because capital cannot flow. *Differs:*
     country-level bitcoin premia; no coin-level prediction of the global price.
  2. Choi, Lehar & Stauffer, "Bitcoin microstructure and the Kimchi premium" (SNB seminar 2019, search): asymmetric
     capital controls keep the bitcoin premium positive. *Differs:* the level of bitcoin's premium, not a
     cross-section of coins.
  3. Finance Research Letters 2022, vol. 50 (IDEAS, search): most profit from the premium went to foreign
     arbitrageurs. *Differs:* who profits from closing it, not what it predicts.
  4. Crépellière, Pelster & Zeisberger, cross-exchange arbitrage (Paderborn WP, search): opportunities shrank after
     April 2018 and do not pay once implemented. *Differs:* profit from arbitraging the gap; here the gap is a
     signal for an outright position on the global venue, which needs no Korean account.
  5. 4Pillars, "Koreans buy the alt top, not the bitcoin top" (search): Korean flow peaks near altcoin tops.
     *Differs:* descriptive and unmeasured against a baseline; no premium, no test.
- **Known?** The kimchi premium is well known; a test of **coin-relative** premia against the global price's next
  day and next month was not found in three searches. Classed NEW as a test, not as a new phenomenon.
- **Data.** Upbit's public API (daily candles of every KRW market, no key), Binance's public archive
  (data.binance.vision, daily and hourly klines). Not in the record; not sealed.
- **To trade it.** Spot coins bought outright on a global venue (H1), held a day; no leverage, no short sale. H2's
  information is on the short side and is not tradable for altcoins under the Islamic condition: it is tested for
  what it says about the mechanism, and its only tradable use would be to leave a coin out of a long basket.

### A2 · AHP-1 — the A-H premium and the H-share index · **PARTLY KNOWN**
- **Mechanism.** Mainland investors cannot buy Hong Kong shares except through Southbound Connect quotas; the same
  company's A share then trades above its H share. When the premium is wide, Southbound buyers favour H shares.
- **Mathematics.** `π = ln(P_A · FX) − ln P_H`; Southbound flow `SB = f(π)`, `f' > 0`; `E[r_H] = λ·SB(π)`.
- **Closest known work.** Tang & Liu, arXiv 2602.14754 (search: persistence; Connect raised it 18.4%); Feng, Wu &
  Yuan, NTU working paper (search: outflow controls create it); Chan & Kwok (2016) and Fan & Wang (2017), cited by
  Tang & Liu (search snippet); Fernald & Rogers (2002), "Puzzles in the Chinese stock market" (memory). *Differs:*
  they explain the premium; none found tests what it predicts for the H-share index.
- **Data and limits.** Dual-listed prices on Yahoo (free); one index-level series a day, slow-moving: about t 1 at
  a plausible effect over 2014-2026. The cross-section of about 150 pairs would have power, but the owner would
  have to trade single H-share CFDs, which are neither on the allowed list nor screened.

### A3 · AIB-1 — aggregate insider buying · **KNOWN**
- **Mechanism and mathematics.** Insiders see aggregate earnings first: `E[r_m(t → t+12m)] = a + b·NPR_t`, `b > 0`
  for the net purchase ratio.
- **Closest known work.** Seyhun (1988) and Lakonishok & Lee (2001) (memory, cited by search results); the 2010
  replication in the Financial Analysts Journal (IDEAS, search): no forecast out of sample, 2004-2009; Huang & Lin
  (2019, HKU, search): an opportunistic-only index does forecast; a 32-country study (IJFE 2022, search): mixed.
- **Status.** Known, with an out-of-sample failure published: not tested again here.

### B1 · UDL-1 — the Korean exit at a delisting (dated forced selling) · **PARTLY KNOWN**
- **Mechanism.** When Upbit ends trading support for a coin, its Korean holders must sell or move it before a set
  date, and since 2022 the travel rule restricts which foreign venues they can withdraw to: many sell. Korean
  arbitrageurs who buy those coins cheap on Upbit can only sell them abroad, so the selling reaches the global
  price. After the cut-off date the forced seller is gone.
- **Mathematics.** A forced sale `Q` before `T` moves the global price by `−λQ`, a temporary part `θλQ` of which
  reverts once the selling stops (Almgren-Chriss temporary and permanent impact): `E[r(T → T+h)] = θλQ > 0`.
  Refuted if the excess return after `T` is not positive (the impact was permanent, or the decline continues).
- **Closest known work.**
  1. SEC staff input of 2025-02-19 (search): after regulatory events, returns fell 12% in a week and stayed down a
     month, sharper for illiquid tokens. *Differs:* SEC actions, not one venue's dated exit; it is evidence
     **against** a rebound and is the main risk to this hypothesis.
  2. An event study of exchange listing and delisting announcements (Dergipark, search): more significant negative
     abnormal returns in (−5, +10). *Differs:* the announcement; this times the end of the selling.
  3. A study of Upbit's 20-hour outage (Springer 2021, search): the reaction scales with the exchange's importance
     to the coin. *Differs:* an outage, not a delisting; it supports the channel (Korean flow moves global prices).
  4. LIQ-1 (record, FAILED): buying after forced crypto deleveraging. *Differs:* leverage liquidations found in
     price data, against a clientele exit dated by a notice; the end of the selling is known in advance.
  5. PDL-1 (record, rejected for 18 events): a perpetual's delisting. *Differs:* a spot venue with a captive
     clientele, and far more events.
- **Data.** Upbit's notices (public API, to be probed for its history), Binance's public archive. If the probe
  finds too few dated events, the hypothesis waits for data; it is not failed.
- **To trade it.** Buy the coin outright on a global venue after the Korean cut-off; no leverage, no short.

### B2 · TGA-1 — Treasury cash-balance drains · **NEW as a return test**
- **Mechanism.** Taxes and bill settlements move money into the Treasury's account at the Fed, draining bank
  reserves (BNY iFlow; the April 2026 tax day added about $145bn in a day, Bloomberg via search). Fewer reserves
  mean less balance-sheet room for leveraged buyers of risk.
- **Mathematics.** `ΔR = −ΔTGA`; `E[r(t+1 → t+5)] = −β · ΔTGA_t / σ_ΔTGA`, `β > 0`, with the Treasury's daily
  statement read a day late (it is published at 16:00 ET the next business day).
- **Closest known work.** BNY iFlow "Tax week and the funding markets"; Bloomberg 2026-04-16; JPMorgan's estimate
  via Accounting Today; a Seeking Alpha opinion piece (all search: funding mechanics, no return test); TSY-1 and
  TME-1 (record, FAILED: calendar dummies on bonds). *Differs:* the measured size of the drain, on equities and
  bitcoin.
- **Why not chosen.** Power: about 2,800 trading days since 2015 need a daily information coefficient near 0.06
  for t 3.0, implausible for a macro flow the market sees coming. It waits for a sharper design (see section 6).

### B3 · MGN-1 — margin hikes as forced deleveraging · **KNOWN, contrary**
- **Mathematics.** A trader at full margin `m` cutting to `m'` sells `E(1/m − 1/m')`: `E[r] = −λ·Spec·Δ(1/m)`.
- **Closest known work.** Hedegaard (AQR WP, search): 16 commodity futures 2000-2011, margin increases cut hedgers'
  positions but have **no price effect**, only 50% more volatility that day; Brunnermeier & Pedersen (2009, memory);
  Hardouvelis (1990, memory); Kahraman & Tookes (2017, JF, search); BIS Quarterly Review 2023-09 (search).
- **Status.** The closest test is negative; not tested again here.

### B4 · HPS-1 — miners' cash stress · **KNOWN (practitioner)**
- **Mathematics.** Miner margin `M = (hashprice − cost)·H`; with `M < 0` miners sell inventory at rate `s(M)`; when
  the hash rate turns up after capitulation the selling ends: `E[r]` positive after the 30-day hash-rate average
  crosses above the 60-day one.
- **Closest known work.** Edwards' Hash Ribbons via Nasdaq; CryptoQuant's claim that it missed once; Glassnode's
  chart; Forklog's dissent (all search, practitioner, no independent backtest found); Kristoufek (2020, memory):
  price drives the hash rate, not the reverse.
- **Why not chosen.** About ten capitulations since 2012: no power. Waits for a panel of proof-of-work coins.

### B5 · JDR-1 — Japanese index funds' dividend reinvestment · **KNOWN (practice)**
- **Mathematics.** Funds with assets `A` and dividends `d` due at the ex-date buy futures worth `A·d` the day before
  to stay invested: `E[r_eve] = λAd > 0`, reverting after.
- **Closest known work.** JPX's Nikkei 225 dividend futures, Nikkei's Dividend Point and Total Return index guides
  (search: the mechanics, no price study found); MEH-1, PHD-1 (record, calendar flows FAILED). Only these were found.
- **Why not chosen.** Two events a year (about 40 since 2006): no power.

### C1 · SCX-1 — stablecoins when their primary market is shut · **NEW as a test**
- **Mechanism.** A dollar stablecoin's secondary price is pinned near $1 by arbitrageurs who mint and redeem with
  the issuer, and the issuers move dollars only on US banking days (Circle's redemptions during the SVB weekend
  were "constrained by working hours of the U.S. banking systems", Federal Reserve note, search). At weekends the
  pin rests on market makers' inventory alone, so order-flow shocks move the price further and longer; on Monday
  the primary market reopens and the price is pulled back.
- **Mathematics.** With the primary market open, `p ∈ [1 − c_r, 1 + c_m]` and deviations decay at rate `κ_open`;
  closed, at `κ_closed < κ_open`. A deviation `δ = p_Sun − 1` measured late on Sunday decays by Monday's close to
  `δ·e^(−κ_open·Δ)`: `E[p_Mon − p_Sun] = −δ·(1 − e^(−κ_open·Δ))`. Buying the cheap side (USDC with USDT, or USDT with
  USDC or dollars) earns `|δ|·φ − c`. Refuted if weekend deviations do not revert faster once the primary market
  opens than a weekday deviation of the same size does.
- **Closest known work.**
  1. Ma, Zeng & Zhang, "Stablecoin runs and the centralization of arbitrage" (NBER/ECB conference paper, search):
     six arbitrageurs redeem USDT in an average month (the largest 66%), 521 for USDC; average deviation 41.9 bp
     against 1.7 bp. *Differs:* the structure of arbitrage, not its weekly clock.
  2. Federal Reserve FEDS Note of 2025-12-17 on SVB and stablecoins (search): the weekend redemption halt.
     *Differs:* one crisis weekend.
  3. S&P Global, stablecoin depegging report (search): leaving out weekends almost halves some stablecoins'
     volatility. *Differs:* volatility, not a trade, and not dated to the primary market's hours.
  4. Lyons & Viswanath-Natraj (2023, JIMF), "What keeps stablecoins stable?" (memory): the peg is held by
     primary-market arbitrage. *Differs:* no weekend/weekday timing.
  5. Gorton, Klee, Ross, Ross & Vardoulakis (2022), "Leverage and stablecoin pegs" (memory): deviations track
     crypto leverage demand. *Differs:* the demand side, not the closure of the supply side.
- **Data.** Binance's public archive (USDCUSDT and other stablecoin pairs, hourly, from 2018-12); Coinbase's public
  candles (USDT-USD). Not in the record; not sealed.
- **Costs.** Coinbase's stable pairs: 0 bp to make, 0.1 bp to take (Coinbase blog, 2022, search); Binance's USD
  stablecoin pairs at zero fees from November 2025 (Binance announcement, search). The test charges the spread and
  these fees, then the same doubled.
- **To trade it.** Spot stablecoin exchange, hand to hand: no leverage, no short sale, no interest received.
  **Its capacity and its size are small** (a few basis points a weekend): it can be a real edge without coming near
  $4,000 a month on a small account. That is said now, before the test.

### C2 · BWT-1 — Brent-WTI under the Cushing constraint · **KNOWN (published strategies)**
- **Mathematics.** `s = ln Brent − ln WTI = τ + ε`, `dε = −κε dt + σ dW`; trade when `|ε| > k σ/√(2κ)`.
- **Closest known work.** Büyükşahin, Lee, Moser & Robe (EIA, search); Lubnau (Bollinger bands on the spread,
  1992-2013, search); Geyer-Klingenberg & Rathgeber (J Futures Markets, search: break in December 2010); a Western
  Ontario thesis (Vasicek, search); arXiv 2309.00875 (search).
- **Status.** A published strategy: the owner excluded copies. Not tested here.

### C3 · PPS-1 — platinum-palladium substitution · **KNOWN mechanism**
- **Mathematics.** `z = ln(P_Pt/P_Pd)`, `dz = −κ(z − z*)dt`, with `κ` set by the 15% of vehicle models renewed each
  year.
- **Closest known work.** CME's "Substitution among platinum group metals", the WPIC substitution report, Reuters
  (substitution slows near parity), CME 2024 (all search); GSR-1 (record, gold/silver ratio FAILED).
- **Why not chosen.** Reversion over years: a handful of independent swings since 2000.

### D1 · PAXG-1 — tokenized gold while the gold market is shut · **KNOWN (practitioner)**
- **Mechanism and mathematics.** PAXG's minting and redemption need banks and vaults, closed at weekends, so its
  price floats on crypto flows: `P_w = G_open + b + η`; `η` reverts when gold reopens: `E[P_Mon − P_Sun] = −φη`.
- **Closest known work.** Cointelegraph and Kitco (Theo's Ioppe: "virtually 100% of weekend price discovery"),
  CoinGecko's case studies, CoinDesk 2024-04-14 (all search, practitioner); Cong et al. 2026 on tokenized stocks
  (search, by analogy); the CME weekend gaps (record, rejected).
- **Why not chosen.** Gold from 2017 on is sealed, forward months included, until the owner sets the seal's end.
  **This one needs the owner's decision, not data.**

### D2 · XST-1 — tokenized stocks at the weekend · **KNOWN (2026)**
- **Mathematics.** Cong et al.: `E[S_open − S_Fri] = 0.28·(T_w − S_Fri)`, so about 72% of a token's off-hours move
  is noise that its price should give back after the open: buy tokens that fell, sell after Monday's open.
- **Closest known work.** Cong, Landsman, Rabetti, Zhang & Zhao (Bank of Finland SRA 2026, search); DefiLlama
  research on bStocks (search: 92% of the Monday move captured over seven weekends); Kraken's market-hours page and
  Finance Magnates (search); bitcoin's weekend move and Monday's index (record, rejected for power).
- **Why not chosen.** Trading began in mid-2025 and only about ten names trade at weekends: no power yet.

### D3 · AMM-1 — concentrated-liquidity range exits · **NEW, data-heavy**
- **Mechanism and mathematics.** When ETH leaves a Uniswap v3 position's range the position holds one asset only;
  managers who re-centre it swap about half back, `F ≈ ½ L (√p_b − √p_a)`, in the direction of the move.
- **Closest known work.** arXiv 2309.08431 (LPs lose on average in ETH/USDC), 2403.09494 (repositioning raises
  concentration), 2505.15338 (reallocation costs), 2302.00610 (online learning), Dune's blog (about 30% of capital
  out of range) (all search). None measures the re-centring flow as a price predictor.
- **Why not chosen.** On-chain event extraction needs a node or a keyed indexer; the flow is small against the
  centralized venues'.

### E1 · ESQ-1 — Ethereum's validator exit queue · **NEW, few episodes**
- **Mathematics.** The queue `Q` clears at the churn limit `c`; withdrawn ETH arrives after `Q/c`; a fraction `σ` is
  sold: `E[r over the arrival window] = −λσQ`.
- **Closest known work.** The Block (July 2025: 521k ETH waiting), KuCoin's blog (October 2026: 166k to 850k after a
  staking incident), Yahoo Finance (all search; all stress that a queue is not a sale); EMIT and token unlocks
  (record, rejected).
- **Why not chosen.** A handful of large queues since 2023, and the sold fraction is unobservable.

### E2 · PGL-1 — South African load shedding and platinum · **NEW, dormant**
- **Mathematics.** South Africa mines about 70% of platinum: `Δln P = −(1/ε)·0.7·Δln Q_SA`.
- **Closest known work.** Mining Weekly 2023 and David Davis 2021; Metals Focus weekly 492 (150 koz lost in 2022;
  producers are curtailed rather than shed); S&P Global 2021; SMM August 2026 (all search).
- **Why not chosen.** The mechanism is absent: South Africa has had no load shedding for over a year (SMM, 2026).

### E3 · NGW-1 — weekend weather forecasts while NYMEX gas is shut · **KNOWN (practitioner)**
- **Mathematics.** Monday's gap `G = β·ΔHDD_weekend + u`; if traders over-extrapolate, `E[r(Mon → Tue)] = −γ(G − β*·ΔHDD)`.
- **Closest known work.** NGI and FXEmpire market reports (weekend model changes drive Monday gaps; some gaps
  reverse), CNBC 2023-03-06 (all search); EVT-1 and INV-1 (record: the storage-report reaction is immediate); Mu
  (2007), "Weather, storage, and natural gas price dynamics" (memory).
- **Why not chosen.** The weekend forecast changes need archived model runs: free archives either start in the last
  few years or are tens of gigabytes of model files.

### F1 · CHL-1 — China's price limits and the next day in Hong Kong · **PARTLY KNOWN**
- **Mathematics.** Sell orders `U` unfilled at the A-share limit carry to the next day; H shares, without limits,
  absorb them at once and overshoot: `E[r_H,t+1] = θ·(r_H,t − r_A,t)` on limit days.
- **Closest known work.** arXiv 1503.03548 (pre-hit dynamics; continuation), arXiv 1803.09422 (cooling-off, not
  magnet), an HKU thesis (magnet supported), a White Rose PhD (delayed price discovery in A and B shares), Springer
  2016 (all search). None tests the H-share side the next day.
- **Why not chosen.** Limit hits per stock need a keyed mainland data source; the owner's instrument (HK50 or
  China50 CFDs) is at index level.

### G1 · RBP-1 — the rebalancing return · **KNOWN**
- **Mathematics.** Rebalancing to fixed weights earns about `½(Σ w_i σ_i² − σ_p²)` over buy-and-hold when relative
  prices revert (Booth & Fama 1992; Willenbrock 2011; Hallerbach 2014; all memory).
- **Closest known work.** The above; Quantpedia's crypto study and the vendor studies of Bitwise, Betashares and
  CoinShares (search).
- **Status.** Arithmetic of a portfolio, not a market's mistake; known. Not tested as an edge.

### G2 · ANC-1 — the 52-week-high anchor · **KNOWN (published)**
- **Mathematics.** `E[r_m,t+1] = a + b·(P_t/H52_t)`, `b > 0` (anchoring), Li & Yu (2012, JFE, search).
- **Closest known work.** Li & Yu (2012); George & Hwang (2004, memory); Tu et al. (CKGSB working paper, search:
  the Dow version predicts, the NYSE/AMEX version does not); George, Hwang & Li (search); TRND-1 (record).
- **Status.** Published, monthly, index-construction sensitive: not tested here.

## 4. Scores, the rule, and the three chosen

The rule was fixed before the scores were summed: **a hypothesis is eligible for preregistration only if it passes
the edge hunt's power and cost pre-checks with free data that are neither sealed nor already read**; among the
eligible, the highest totals are chosen. O originality, E economic basis, T testability (power included), D data,
P net-profit potential for this owner; each 1 to 5.

| | O | E | T | D | P | Total | Eligible | Why not, if not |
|---|---|---|---|---|---|---|---|---|
| **KRP-1** | 4 | 4 | 4 | 4 | 3 | **19** | **yes** | |
| **SCX-1** | 3 | 4 | 4 | 4 | 1 | **16** | **yes** | (small capacity, said in advance) |
| TGA-1 | 3 | 3 | 2 | 4 | 2 | 14 | no | power |
| HPS-1 | 2 | 3 | 2 | 4 | 3 | 14 | no | power (about ten episodes) |
| JDR-1 | 2 | 4 | 2 | 4 | 2 | 14 | no | power (two events a year) |
| NGW-1 | 3 | 4 | 2 | 2 | 3 | 14 | no | data (forecast archives) |
| **UDL-1** | 3 | 3 | 3 | 2 | 2 | **13** | **yes, if its probe finds the events** | |
| AHP-1 | 2 | 4 | 2 | 3 | 2 | 13 | no | power at the tradable level |
| PPS-1 | 2 | 3 | 2 | 4 | 2 | 13 | no | power |
| RBP-1 | 1 | 3 | 3 | 4 | 2 | 13 | no | known; not an inefficiency |
| PAXG-1 | 3 | 4 | 1 | 1 | 3 | 12 | no | sealed (the owner's decision) |
| XST-1 | 2 | 4 | 2 | 2 | 2 | 12 | no | power (since 2025; ten names) |
| AMM-1 | 4 | 2 | 2 | 2 | 2 | 12 | no | data |
| ESQ-1 | 4 | 2 | 2 | 2 | 2 | 12 | no | power and data |
| PGL-1 | 4 | 3 | 1 | 3 | 1 | 12 | no | the mechanism is absent now |
| ANC-1 | 1 | 3 | 2 | 4 | 2 | 12 | no | published; power |
| BWT-1 | 1 | 3 | 3 | 3 | 2 | 12 | no | a published strategy |
| AIB-1 | 1 | 3 | 2 | 3 | 2 | 11 | no | published, failed out of sample |
| CHL-1 | 2 | 3 | 2 | 2 | 2 | 11 | no | data |
| MGN-1 | 2 | 3 | 2 | 2 | 1 | 10 | no | the closest test is negative |

**Chosen: KRP-1, SCX-1 and UDL-1.** UDL-1 is chosen on the condition its data probe finds enough dated events; if it
does not, it waits for data and nothing is judged on it. Each is preregistered on the NEWL-1 pattern: a frozen spec
and code quoted by sha256, a probe that reads names and dates only, a development stage and a holdout read once,
costs at x1, x1.5 and x2, a matched random baseline, and a threshold that counts every earlier test on its data
(never below t 3.0).

### The probes (2026-11-22, names and file names only, no price read)

- **SCX-1:** hourly bars for six pair names in Binance's archive (`research/results/SCX-1-probe.json`): 237
  development Sundays with up to five pairs, 174 validation Sundays with four. It is preregistered
  (`research/preregistrations/SCX-1.md`).
- **UDL-1:** Upbit's notice pages refuse automated requests from GitHub's runner (HTTP 403 on both of the current
  announcement lists; the older list is gone, HTTP 404: `research/results/UDL-1-probe.json`). No dated exit could
  be read, so UDL-1 is **not testable now, and not failed**: it waits for a reachable record of Upbit's delisting
  notices (an archive of them, or a list the owner exports). The refusal was not worked around.
- **KRP-1:** see `research/results/KRP-1-probe.json` and its preregistration.

### The outcomes (2026-11-22)

- **SCX-1: FAILED.** Its development stage passed at 10 bp (242 swaps, +8.6 bp net, t 3.02 against a bar of 3.0, every
  gate); its validation stage, judged once on 2023-07 to 2026-10, weeks no study here had read, failed every gate
  (251 swaps, -0.2 bp net, t -0.25; the same rule on Wednesdays earned +2.0 bp). The development pass did not hold.
  No forward stage. `research/results/SCX-1-verdict.md`.
- **KRP-1: FAILED in development**, judged once by run 44978747723 of `krp1.yml` (its Run step ended at 03:17:31
  UTC): at a 5% fresh premium t -0.87 against a bar of 3.0 (288 entries; +0.29% a day before the 0.6% round trip,
  -0.31% net); at 10% INCONCLUSIVE, 138 entries where 150 are required (t -0.92). Its records were lost when its
  commit to main met SCX-1's on `research/registry.jsonl`; the rule written before the rerun was that the first
  run's verdict binds and the rerun must equal it. Run 44982217651 reproduced it exactly (the same entries, verdict
  and t values) and wrote the records. `research/results/KRP-1-verdict.md`.
- **UDL-1: not tested.** It waits for a readable record of Upbit's delisting notices.

**Round 2 found no edge.** Of the three chosen, two failed on data they had not seen and one could not be tested.

### Every possible trade (a descriptive backtest, 2026-11-22)

The owner asked to see both strategies applied to every trade they could have made, without flattery.
`scripts/r2_backtest.py` (run 45010822465; `research/results/ROUND2-full-backtest.md` and `.json`) ran the frozen
study code on all of 2018 to October 2026: every threshold, every cost level, holds from 6 hours to a week. It
reproduces every entry the judged runs recorded (KRP-1's 288, SCX-1's 242 and SCX-1-V's 251, identical). It is not a
test and changes no verdict. It spent KRP-1's unread validation months, and with them the hourly window
2025-03-08 to 2026-10-29 that the decision of 2026-11-16 kept unread for a possible altcoin short-side test: by the
rule that contamination is a property of market periods, a future altcoin test needs months after 2026-10
(`research/director/log.jsonl`, 2026-11-22 11:30).

- **SCX-1:** the reversion from a deviation is real before costs (+4.9 bp a swap at 10 bp, t 4.14, 493 swaps), but
  it is on every weekday (Monday +4.2 bp, Wednesday +3.1 bp), and it is small: $10,000 became $10,695 in 7.9 years
  at 1 bp a fill (+0.86% a year), and $7,068 at Binance's standard 10 bp (-29%). At 2 bp a fill nothing is left
  (+0.9 bp, t 0.77).
- **KRP-1:** no threshold or hold makes money at 0.6% a round trip with any significance (the best row: 20% for a
  day, +0.85%, t 0.75, 76 trades). The registered rule: 429 trades, 47% beat bitcoin, $10,000 became $9,664. The
  one strong figure is negative: coins with a fresh 2% premium lose to bitcoin over the next week (-2.58% net, t
  -3.26, 521 trades), a short-side signal the Islamic condition excludes for altcoins.

## 5. What would count as success

As the owner set it: a result out of sample, significant after the multiple-test correction, net of every cost,
with its capacity estimated, then an independent test, then paper forward testing. A development-stage pass is
none of those: it only earns the holdout its single look.

## 6. What the others need

- **PAXG-1:** the owner closes the gold seal at a date; tokenized-gold weekends after it are then fresh data.
- **TGA-1, HPS-1, JDR-1, PPS-1, AHP-1, XST-1:** power. HPS-1 can gain it from a panel of proof-of-work coins (hash
  rates for several coins are in Coin Metrics' free tier, to be checked); XST-1 from time (about 50 weekends a year
  with ten names); the others need decades and are kept as written, not failed.
  (2026-11-23: HPS-1 was checked and dropped: the coin panel's hash rates move with miners switching between coins and with merge-mining, not with cash stress; `research/QUEUE.md`.) (2026-11-23: XST-1 was checked and dropped: weekend token prices already carry most of Monday's move, and the rest cannot pay a thin token's round trip.) (2026-11-23: TGA-1 was checked and dropped: commentary on both sides, no study, and a forward stage of about ten years.) (2026-11-23: JDR-1 was checked and dropped: a trade brokers sell, which dividend futures let anyone pre-position.) (2026-11-23: PPS-1 was checked and dropped: the ratio's mean moves, and the swings are four or five.) (2026-11-23: AHP-1 was checked and dropped: no study finds the premium predicts returns, and the dollar moves it.)
- **NGW-1, AMM-1, ESQ-1, CHL-1:** data. NGW-1 needs archived weekend weather forecasts; AMM-1 and ESQ-1 an indexer or
  a node; CHL-1 a mainland source of daily limit hits.
  (2026-11-23: ESQ-1 was checked and dropped: four or five large queues, whatever the data; `research/QUEUE.md`.) (2026-11-24: NGW-1 was checked and dropped: the Monday gap prices the weekend's model changes, and the degree-day forecasts traded on are sold.) (2026-11-24: AMM-1 was checked and dropped: the re-centring flow is a fraction of a percent of ether's daily volume, too small for t 3.0 or the costs.)
- **PGL-1:** the mechanism has to come back (load shedding of stage 4 or more).

## 7. Sources

Every source above that is marked "search" came from a web search made on 2026-11-22. **Search results only: no
paper was read in full**, and a claim taken from a result is reported as the result stated it. The full list, by
hypothesis, with every URL, is in `research/results/ROUND2-sources.md`.
