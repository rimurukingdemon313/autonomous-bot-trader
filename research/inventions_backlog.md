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
| 1 | KRP-1 the Korean coin premium (round 2, A1) | Residents close a coin-relative Korean gap by buying the coin and selling bitcoin abroad | Coin spot bought outright on Binance, short bitcoin through a swap-free CFD (one short, stated) | Arbitrage may finish within the hour; 0.6% a round trip |
| 2 | SCX-1 stablecoins while their primary market is shut (round 2, C1) | Issuers move dollars only on US banking days; weekend deviations wait for Monday | A spot swap between stablecoins from a stock of both; no short, no borrowing | A tick is often the last trade's bounce; small capacity |
| 3 | UDL-1 the Korean exit at an Upbit delisting (round 2, B1) | A captive clientele sells by a dated deadline; the selling ends on a known date | Coin spot bought outright on Binance | WAITING FOR DATA: Upbit's notice pages refuse GitHub's runner (403); not failed |

Round 2 (`docs/ORIGINAL_EDGE_HUNT_2.md`, 2026-11-22) chose these three by a rule fixed before scoring; its twelve
others wait for data or power (`research/QUEUE.md`), and five were rejected with the evidence.

Rejected before testing so far (with their reasons, in `research/inventions.jsonl`): on 2026-11-15, TRND-1's rule on
bitcoin and ether CFDs (time-series momentum failed on them in XTS-1, and the designer knows their unread path),
CALM-1 (power: t about 1.5), US-hours clientele in bitcoin (a closed family), the post-FOMC drift into gold (power),
bitcoin's weekend move and Monday's index session (power), passive capture of the unpriced funding (perpetuals: outside
the Islamic condition), buying after token unlocks (contradicted: the published unlock studies find the decline goes on)
INV-1 (power and costs), OPT-1 (option flow: the index-option evidence is a quarter of the size needed), REC-1 (recovery after stress: power), VCR-1 (vol-control flows are smooth), OSH-1 (Japanese margin calls: no study, few events), maker-only bitcoin at zero fees (no honest fill model) and, after its probe, HLQ-1 (visible liquidation clusters on Hyperliquid: none near the price among the largest accounts, and a mark anchored to other venues); before that, liquidation-price magnets,
spot-listing demand, coin-margined hedgers' pressure, quarterly delivery roll, weekend gaps of CME-hedged holders,
the dead-zone transfer, strike pinning by 0DTE options (an independent 2026 study of 2,294 S&P 500 days found
none), and the TRND-1 rule on metals, oil and crypto ETFs (DIV-1 already failed on those funds in 2008-2021).

Judged so far by the edge hunt: EXF-1, SQZ-1, CASC-1, BAS-1 and SPL-1, all FAILED (SPL-1: large four-hour rallies reversed within a day, whoever led them). Their common finding: a coin under leverage stress of either sign underperforms the market for days to weeks; the information is on the short side, which the Islamic condition excludes for altcoins. A minimum counted in weeks that hold an entry must be checked against the signal's frequency, not only against calendar weeks (BAS-1's two higher thresholds could not reach theirs).
