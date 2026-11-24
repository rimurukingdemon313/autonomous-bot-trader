# The edge hunt's backlog

Candidates waiting for their pre-checks, ranked. A candidate leaves this list when it is registered (then it is in
`research/inventions.jsonl` and `research/registry.jsonl`) or rejected before any test (then it is in the ledger
with its reason). Each cycle of the scheduled edge hunt takes the first one whose pre-checks it can run.

Every candidate must be tradable by the owner (swap-free CFDs on indices, metals, energy, BTC or ETH, or spot crypto
bought outright: no funding paid or received, no interest), must say whether it needs short selling or leverage,
and passes four checks before any code: the closest known work and its contradictions (a web search, cited); power
(the effect t 3.0 needs is no larger than the mechanism's plausible size); costs (a plausible gross of at least
three times the round trip); unread data, or a forward design.

| Rank | Candidate | Mechanism, in one line | Instrument | First worry |
|---|---|---|---|---|
| 1 | UDL-1 the Korean exit at an Upbit delisting (round 2, B1) | A captive clientele sells by a dated deadline; the selling ends on a known date | Coin spot bought outright on Binance | WAITING FOR DATA: Upbit's notice pages refuse GitHub's runner (403); not failed. A third-party feed republishes the notices with dates: using it waits for the owner's word (`research/QUEUE.md`, row 30) |

Round 2 (`docs/ORIGINAL_EDGE_HUNT_2.md`, 2026-11-22) chose three by a rule fixed before scoring: KRP-1 and SCX-1
were registered and judged (below), UDL-1 waits here for data; its twelve others wait for data or power
(`research/QUEUE.md`), and five were rejected with the evidence.

Rejected before testing so far (with their reasons, in `research/inventions.jsonl`): on 2026-11-24, PED-1 (the pre-ECB drift: published, a failed family, eight meetings a year), GSZ-1 (seized and estate bitcoin sales: few, small, and the US no longer sells), BWS-1 (the Brent-WTI spread: slow reversion, traded by exporters at futures' costs), GRL-1 (energy CFDs in the commodity-index roll window: a spread effect that reverses within minutes, and costs), DAT-1 (crypto treasury companies below their coins' value: small sales disclosed after the fact, a regime months old), CHL-1 (China's price limits and Hong Kong: few events at the index's level, a weakened mechanism, read data), AMM-1 (Uniswap re-centring flows: a fraction of a percent of ether's volume, power and costs), NGW-1 (weekend weather and natural gas: priced at the open, paid data); on 2026-11-23, AHP-1 (the A-H premium: no predictability found, a handful of swings), PPS-1 (platinum against palladium: a moving mean, four or five swings), JDR-1 (Japanese dividend reinvestment: known, anticipated, two events a year), TGA-1 (the Treasury's cash balance: ten years of forward data), XST-1 (tokenized stocks at the weekend: costs, capacity), ESQ-1 (ether after a large exit queue: four or five episodes), LXR-1 (bitcoin into the close of the leveraged ETFs' rebalancing: power) and HPS-1 (miners' capitulation: the coin panel does not carry the mechanism); on 2026-11-22, TQB-1 (Tether's quarter-end bitcoin: accumulated through the quarter, power), SGC-1 (the Hong Kong index while Southbound Stock Connect is shut: power), UWD-1 (Upbit's investment warnings recorded forward: power, and no sign of a rebound), LPB-1 (BNB around Launchpool announcements: faded by a practitioner's count, power), MSTR-1 (Strategy's weekly bitcoin purchases: a minimal and reversing price effect, power, and a path the designer has seen) and QTG-1 (buying when Binance removes a coin's quiz-gated Seed or Monitoring Tag: about 30 removals, power); on 2026-11-15, TRND-1's rule on
bitcoin and ether CFDs (time-series momentum failed on them in XTS-1, and the designer knows their unread path),
CALM-1 (power: t about 1.5), US-hours clientele in bitcoin (a closed family), the post-FOMC drift into gold (power),
bitcoin's weekend move and Monday's index session (power), passive capture of the unpriced funding (perpetuals: outside
the Islamic condition), buying after token unlocks (contradicted: the published unlock studies find the decline goes on)
INV-1 (power and costs), OPT-1 (option flow: the index-option evidence is a quarter of the size needed), REC-1 (recovery after stress: power), VCR-1 (vol-control flows are smooth), OSH-1 (Japanese margin calls: no study, few events), maker-only bitcoin at zero fees (no honest fill model) and, after its probe, HLQ-1 (visible liquidation clusters on Hyperliquid: none near the price among the largest accounts, and a mark anchored to other venues); before that, liquidation-price magnets,
spot-listing demand, coin-margined hedgers' pressure, quarterly delivery roll, weekend gaps of CME-hedged holders,
the dead-zone transfer, strike pinning by 0DTE options (an independent 2026 study of 2,294 S&P 500 days found
none), and the TRND-1 rule on metals, oil and crypto ETFs (DIV-1 already failed on those funds in 2008-2021).

Judged so far by the edge hunt: EXF-1, SQZ-1, CASC-1, BAS-1 and SPL-1, all FAILED (SPL-1: large four-hour rallies reversed within a day, whoever led them); then round 2's KRP-1, FAILED in development (a coin with a fresh Korean premium beat bitcoin by less than the 0.6% round trip), and SCX-1, which passed its development stage at 10 bp and FAILED on the unread validation weeks (the Wednesdays did better than the Sundays). Their common finding: a coin under leverage stress of either sign underperforms the market for days to weeks; the information is on the short side, which the Islamic condition excludes for altcoins. A minimum counted in weeks that hold an entry must be checked against the signal's frequency, not only against calendar weeks (BAS-1's two higher thresholds could not reach theirs).
