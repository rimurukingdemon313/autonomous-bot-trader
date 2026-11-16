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
| 1 | Visible liquidation clusters on Hyperliquid (HLQ-1, being built 2026-11-15; forward only) | Hyperliquid publishes every position and its liquidation price: predators and cascades should carry the price to a large visible cluster more often than to an equally distant level with none | BTC or ETH CFD, swap-free, long or short (Hyperliquid data as information only) | a forward window of six months; Hyperliquid's mark price is anchored to other venues, so its clusters may be too small to move bitcoin |

Rejected before testing so far (with their reasons, in `research/inventions.jsonl`): on 2026-11-15, TRND-1's rule on
bitcoin and ether CFDs (time-series momentum failed on them in XTS-1, and the designer knows their unread path),
CALM-1 (power: t about 1.5), US-hours clientele in bitcoin (a closed family), the post-FOMC drift into gold (power),
bitcoin's weekend move and Monday's index session (power), passive capture of the unpriced funding (perpetuals: outside
the Islamic condition), buying after token unlocks (contradicted: the published unlock studies find the decline goes on)
and INV-1 (power and costs); before that, liquidation-price magnets,
spot-listing demand, coin-margined hedgers' pressure, quarterly delivery roll, weekend gaps of CME-hedged holders,
the dead-zone transfer, strike pinning by 0DTE options (an independent 2026 study of 2,294 S&P 500 days found
none), and the TRND-1 rule on metals, oil and crypto ETFs (DIV-1 already failed on those funds in 2008-2021).

Judged so far by the edge hunt: EXF-1, SQZ-1, CASC-1 and BAS-1, all FAILED. Their common finding: a coin under leverage stress of either sign underperforms the market for days to weeks; the information is on the short side, which the Islamic condition excludes for altcoins. A minimum counted in weeks that hold an entry must be checked against the signal's frequency, not only against calendar weeks (BAS-1's two higher thresholds could not reach theirs).
