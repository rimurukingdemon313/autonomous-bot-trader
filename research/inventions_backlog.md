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
| 1 | SQZ-1 (registered 2026-11-15) | Crowded shorts are squeezed: spot beats the market after deeply negative funding | spot, long only | heavily shorted stocks underperform; survivorship favours it |
| 2 | Cascade rebound on spot | A leveraged long cascade in a coin's perpetual drags its spot below value; spot-only buyers are paid for absorbing it | spot, long only | LIQ-1 (BTC and ETH) failed: must say what differs (the cross-section, the size of the cascade relative to spot volume) |
| 3 | US-hours clientele in BTC, with the US-holiday control | US institutions buy in US hours; on US exchange holidays and weekends the same clock hours should show nothing | BTC CFD or spot, long only | power: BTC's volatility needs about 19 bp a day for t 3 over nine years |
| 4 | Post-FOMC drift into gold | Treasury yields drift for days after FOMC surprises (slow-moving capital); gold, priced off real yields, should follow its own first reaction | gold CFD, long and short | about 140 meetings since 2009: power is the problem |
| 5 | BTC's weekend move and Monday's index session | News of the weekend is priced first in crypto; equities reopen thin on Sunday night and may under-react | index CFDs, long and short | the Sunday open may price it fully; power |
| 6 | Passive capture of the unpriced funding fraction (from EXF-1) | 8-11 bp of a moderate payment is left unpriced; a maker's fill instead of two taker fills might keep it | perpetuals: outside the Islamic condition unless the owner says otherwise | needs the archive's best bid and ask and a fill model; adverse selection |

Rejected before testing so far (with their reasons, in `research/inventions.jsonl`): liquidation-price magnets,
spot-listing demand, coin-margined hedgers' pressure, quarterly delivery roll, weekend gaps of CME-hedged holders,
the dead-zone transfer, strike pinning by 0DTE options (an independent 2026 study of 2,294 S&P 500 days found
none), and the TRND-1 rule on metals, oil and crypto ETFs (DIV-1 already failed on those funds in 2008-2021).
