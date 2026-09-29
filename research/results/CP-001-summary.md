# CP-001: result

**Verdict: FAILED.** Preregistered in `adf6d36`. Judged on 2013-07 → 2017-01 at t ≥ 3.18.

| Hypothesis | n | Mean net R | t | Profit factor | Main failures |
|---|---|---|---|---|---|
| T1: 120-day uptrend, BUY | 260 | −0.020 | −0.30 | 0.95 | significance, random baseline, years |
| T2: 120-day downtrend, SELL | 251 | **+0.187** | 1.03 | 1.53 | significance, random baseline, years, outliers |
| T3: MA-trend up, BUY | 249 | −0.003 | −0.04 | 0.99 | nearly every check |
| T4: MA-trend down, SELL | 226 | **+0.207** | 1.00 | 1.63 | significance, random baseline, years, instruments, outliers |

## Reading

- The short side of trend following made money on this period, while the long side did not.
- That profit came almost entirely from **2014**, the year of the large dollar rally: +0.86R per
  trade for T2 and +1.06R for T4. The other years were negative or flat.
- The best 5% of trades carried more than 100% of the total R.
- This is the pattern the literature describes: trend following earns in rare, large trends and
  gives back in between. Over 3.5 years it cannot be told apart from luck (t ≈ 1.0 against a
  required 3.18).
- **Not a validated edge. Nothing in production changed.**
