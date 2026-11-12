# Research sources: the campaign of 2026-11-11

**Research only.** This is the source record of one search campaign, kept so that every later hypothesis can name
where it came from. The lab's own worker keeps a second, automatic record (`sources` on the `lab-data` branch: recent
arXiv and OpenAlex entries, each UNREAD until its claim is checked).

## How far each source was read: stated first

Twelve web searches were run. **No paper was opened at its source.** The environment this was written in does not
resolve the publishers' hosts (four direct fetches were tried and all four failed on DNS; that restriction was left
alone). So every statement below is what the search engine's summary of the page reports, and is marked
**summary only**. None of it is verified against the paper, no number is asserted as checked, and nothing here was
reproduced. Where a summary could not confirm an author or a figure, that is said.

A summary is enough to decide what to look for. It is not evidence that anything works. The evidence is what the lab
finds on its own data.

## The sources

| # | Source | Year | What its summary reports (not verified at the source) | Status | What it contributes here |
|---|---|---|---|---|---|
| 1 | Guo, Sang, Tu & Wang, "Cross-cryptocurrency return predictability", *J. Economic Dynamics and Control* | 2024 | On Binance data, other coins' lagged returns predict a coin's return; a long-short portfolio on them earns a sizable out-of-sample return after transaction costs | Summary only | Hypothesis H1. Covered by `leadlag` (every pair of the 55) and by `breadth` |
| 2 | Riksbank Working Paper 413, "Trading volume and liquidity provision in cryptocurrency markets" | 2022 | Short-term reversal returns are concentrated in pairs with little market activity (inventory risk, adverse selection); data to March 2022 | Summary only | H2, and a caution: the lab's 55 perpetuals are the liquid end, where the effect is reported weakest |
| 3 | "Time Series and Cross Sectional Momentum in the Cryptocurrency Market" (AUT ACFR working paper; authors not confirmed) | — | Binance-futures coins only, with actual fees, tick sizes and slippage: many momentum portfolios are liquidated, and many significant gross returns are insignificant net | Summary only | Supports the cost model, and a caution on shorting perpetuals: squeezes |
| 4 | Dobrynskaya, momentum and reversal in 2,000 large cryptocurrencies | 2023 | 2014-2020: momentum up to 2-4 weeks, a significant reversal beyond one month | Summary only | H3: long-horizon reversal. Its momentum half is this project's closed family (XSM-1 failed 2018-2024) |
| 5 | "Up or down? Short-term reversal, momentum, and liquidity effects in cryptocurrency markets", *Int. Review of Financial Analysis* | 2021 | The few largest, most tradable coins show daily momentum, not reversal | Summary only | The sign of a one-day rule is not assumed: the fit rows orient each book |
| 6 | Liu, Tsyvinski & Wu, "Common risk factors in cryptocurrency" (and Liu, Liang & Cui 2020) | 2020-22 | Three factors: market, size, momentum. Samples end around 2021; the search found no re-estimate on later data | Summary only | H5: size and liquidity are not in the lab's panel. A gap |
| 7 | MSCI, "Could factors have explained cryptocurrency risk?" | 2021 | 2017-07 to 2021-03: the characteristics with a premium were size and low liquidity | Summary only | H5 |
| 8 | Fieberg et al., "A trend factor for the cross-section of cryptocurrency returns", *JFQA* | 2024 | A machine-learned aggregate of technical signals on more than 3,000 coins; reported to survive costs and to hold in large, liquid coins | Summary only | H8. Simple momentum is closed here; an aggregate that does not behave like momentum is not |
| 9 | Cakici et al., "Machine learning and the cross-section of cryptocurrency returns", *Int. Review of Financial Analysis* | 2024 | Most machine-learning strategies stay profitable after costs, but their alphas are concentrated in hard-to-trade coins | Summary only | A caution against reading small-coin results into a liquid panel |
| 10 | Jaquart et al., LSTM and GRU long-short portfolios, *J. Finance and Data Science* | 2022 | Out-of-sample Sharpe ratios of 3.23 and 3.12 after costs; the universe was not clear from the summary | Summary only | Not used: the figure cannot be placed without its universe |
| 11 | University of Sydney, idiosyncratic risk in 4,000 coins, *J. Empirical Finance* | 2023 | 2015-2022: the riskiest coins returned -9.36% a year, the least risky +80.6%; exploiting it needs borrowing. An earlier study (2013-2019) found no low-volatility premium, and a 2025 industry note found no low-beta effect | Summary only, and conflicting | H4: low volatility in the cross-section. Open, because the evidence disagrees |
| 12 | Todorov, liquidity provision to futures-based ETFs (via a CXO Advisory summary) | — | Shorting matched long and inverse ETF pairs, 2000-2018: gross Sharpe ratios 0.81 to 2.59, **before** spreads and costs | Summary of a summary | H7: needs a panel the lab does not have, and borrow costs. Low priority |
| 13 | Zaremba & Andreu, country-selection strategies with ETFs, *Int. Review of Financial Analysis* | 2018 | 55 long-only country anomaly portfolios keep outperforming with ETFs after trading costs: 0.41% a month long-only, 0.52% long-short | Summary only | H6: the fund panel's country funds |
| 14 | de Groot, Huij & Zhou, "Another look at trading costs and short-term reversal profits", *J. Banking & Finance* | 2012 | Found as a citation only; its findings were not returned | Citation only | None yet |
| 15 | Bajgrowicz & Scaillet, "Technical trading revisited: false discoveries, persistence tests, and transaction costs", *J. Financial Economics* | 2012 | DJIA 1897-2011: even with the false-discovery rate, an investor could never have picked the future best rules in advance, and low transaction costs offset the performance even in sample | Summary only | Method: a false-discovery screen is a screen, not a proof. Persistence on unread rows is the test. This is the lab's design |
| 16 | Bailey & López de Prado, "The deflated Sharpe ratio" (*J. Portfolio Management*, 2014); Bailey, Borwein, López de Prado & Zhu, "The probability of backtest overfitting" | 2014-17 | The best of many trials must clear the expected maximum under no skill; overfitting can be estimated from the whole set of trials | Summary only | Method M1: report a deflated Sharpe ratio beside each validation. Not built |
| 17 | Allen & Karjalainen, "Using genetic algorithms to find technical trading rules", *J. Financial Economics* | 1999 | Evolved rules on the S&P 500 do not earn consistent excess returns out of sample after transaction costs | Summary only | A caution for `evolve`, and what DLAB-ENG-1 found: 21 of its rules were overfit |
| 18 | "Fundamentals of perpetual futures", arXiv 2212.06888 | 2022 | Past returns predict the gap between perpetual and spot prices; a futures-spot strategy has a large Sharpe ratio even at Binance's highest fees | Summary only | Funding and basis: a closed family here (CR-1 to CR-5), and it needs a spot leg |
| 19 | "An empirical investigation on risk factors in cryptocurrency futures" | 2023 | 2017-2021: the basis is the strongest cross-sectional signal in crypto futures; momentum is weaker | Summary only | The same closed family |
| 20 | "The quarter-hour effect: periodic algorithmic trading and return predictability in cryptocurrency futures", arXiv 2607.09426 | 2026 | Return predictability inside the hour on Binance's USDT-margined perpetuals | Summary only | Intraday periodicity: a closed family here (session and hour-of-day effects) |
| 21 | "Systematic trend-following with adaptive portfolio construction", arXiv 2602.11708 | 2026 | 2022-01 to 2024-12, with a taker fee, slippage and 8-hour funding charged on perpetual swaps | Summary only | Trend is closed; its cost model matches the lab's (fee, slippage, funding in the return) |

## The hypotheses this campaign adds, and where each stands

Each names its parents (the source numbers above). None is a claim that anything works.

| Id | Hypothesis | Parents | Can the lab test it now? |
|---|---|---|---|
| H1 | Among liquid perpetuals, some coins' moves lead others' by a day or more, and a book of those links pays after costs | 1 | Looked at by DLAB-CRD-1 (2026-11-12): 15,125 lead-lag statistics, 24 rules kept; 8 positive on the check rows and not told from noise (the best at t 1.62), 11 lost. Nothing promising |
| H2 | A cross-sectional reversal over one to five days exists among liquid perpetuals and survives 7 to 13 basis points | 2, 5 | **Not yet out of sample.** DLAB-CRD-1 ranked on it on the fit rows, where rankings on funding were stronger and took the places: no ranking on past returns reached the check rows. Waits for the next version of `breadth` |
| H3 | Coins that fell most over two months outperform over the following weeks | 4 | **Not yet out of sample**, for the same reason as H2 |
| H4 | Low-volatility perpetuals outperform high-volatility ones | 11 | **Not yet out of sample.** Only the ratio of short to long volatility reached the check rows, and lost there (t -0.69 and -0.75); the ranking on volatility itself did not reach them |
| H5 | Size or liquidity carries a premium in the cross-section of perpetuals | 6, 7 | **No.** The panel has no volume. Plan: add each day's quote volume to the crypto feed, and a dollar-volume and an illiquidity state series to the panel, in the lab's next version |
| H6 | Rankings of country funds on recent returns or volatility pay after costs | 13 | Looked at by DLAB-ETF-1 (2026-11-12) on 31 funds, country funds among them: every ranking on past returns of one day to a month, and on the volatility ratio, reached the check rows. 18 of 24 books lost there, none was told from noise (the best at t 1.37). Nothing promising |
| H7 | Providing liquidity to leveraged and inverse funds' daily rebalancing pays | 12 | **No.** It needs a panel of leveraged pairs and a borrow-cost model. Low priority |
| H8 | A rule that joins several price features of one coin, applied to every coin, pays where no single feature does | 8 | Partly: the pooled evolutionary search joins two conditions. A richer aggregate is a method not yet built |
| M1 | Report a deflated Sharpe ratio for every judged rule | 16 | Not built |

Two of the nine have now been looked at out of sample by the worker's scans, and three more wait for one change to
the scan (`docs/DISCOVERY_LAB.md` section 11). A data-driven scan does not need the hypothesis named in advance; but
it looks out of sample only at what its places allow, and reading its evidence is how that was found.

## What the campaign changed in the design

- Costs first. Sources 3, 9, 15 and 17 all report gross effects that vanish net. The lab's books therefore include
  slow ones (held 5 or 20 rows), and every validation doubles the costs.
- The sign is never assumed. Sources 2, 4 and 5 disagree on whether liquid coins reverse or continue day to day. Each
  book is oriented by its fit rows and judged on rows it did not see.
- Small-coin results are not read into a liquid panel (sources 2 and 9).
- A gap was found: nothing in this project has ever used volume. It is the next panel feature (H5).

## Sources

- [Cross-cryptocurrency return predictability (Bristol research portal)](https://research-information.bris.ac.uk/en/publications/cross-cryptocurrency-return-predictability/)
- [Cross-cryptocurrency Return Predictability (AMiner)](https://aminer.org/pub/622847295aee126c0f09164a/cross-cryptocurrency-return-predictability)
- [Riksbank Working Paper 413](https://www.riksbank.se/globalassets/media/rapporter/working-papers/2022/no.-413-trading-volume-and-liquidity-provision-in-cryptocurreny-markets.pdf)
- [Time Series and Cross Sectional Momentum in the Cryptocurrency Market (AUT ACFR)](https://acfr.aut.ac.nz/__data/assets/pdf_file/0009/918729/Time_Series_and_Cross_Sectional_Momentum_in_the_Cryptocurrency_Market_with_IA.pdf)
- [Dobrynskaya, HSE publications](https://publications.hse.ru/en/articles/811744977)
- [Up or down? Short-term reversal, momentum, and liquidity effects in cryptocurrency markets (IDEAS)](https://ideas.repec.org/a/eee/finana/v78y2021ics1057521921002349.html)
- [Common risk factors in the returns on cryptocurrencies (IDEAS)](https://ideas.repec.org/a/eee/ecmode/v86y2020icp299-305.html)
- [Common Risk Factors in Cryptocurrency (Alpha Architect summary)](https://alphaarchitect.com/2022/06/factors-investing-in-cryptocurrency)
- [MSCI: Could factors have explained cryptocurrency risk?](https://www.msci.com/research-and-insights/blog-post/could-factors-have-explained-cryptocurrency-risk)
- [A trend factor for the cross-section of cryptocurrency returns (JFQA, Cambridge)](https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/trend-factor-for-the-cross-section-of-cryptocurrency-returns/4C1509ACBA33D5DCAF0AC24379148178)
- [Machine learning and the cross-section of cryptocurrency returns](https://open.icm.edu.pl/items/7566337e-2e7e-40e7-86da-413d57c313b0)
- [Journal of Finance and Data Science, November 2022 (DOAJ)](https://doaj.org/article/cfc09801314441198e3e1c92a3914e54)
- [University of Sydney: huge crypto study finds high risk doesn't equal reward](https://sydney.edu.au/news-opinion/news/2023/11/01/huge-crypto-study-finds-high-risk-doesnt-equal-reward.html)
- [Low volatility in cryptocurrencies (IDEAS, 2020)](https://ideas.repec.org/a/eee/riibaf/v54y2020ics0275531920301926.html)
- [Bitwise: Does the low beta anomaly apply to crypto?](https://bitwiseinvestments.eu/blog/crypto-research/does-the-low-beta-anomaly-apply-to-crypto)
- [CXO Advisory: exploiting liquidity needs of futures-based ETFs](https://www.cxoadvisory.com/volatility-effects/exploiting-liquidity-needs-of-futures-based-etfs)
- [Zaremba & Andreu (IDEAS)](https://ideas.repec.org/a/eee/finana/v56y2018icp181-192.html)
- [Quantpedia: reversal effect in international equity ETFs](https://quantpedia.com/Screener/Details/16)
- [Technical trading revisited (EconPapers)](https://econpapers.repec.org/RePEc:eee:jfinec:v:106:y:2012:i:3:p:473-491)
- [The deflated Sharpe ratio (SSRN)](https://papers.ssrn.com/abstract=2460551)
- [The probability of backtest overfitting (SSRN)](https://papers.ssrn.com/abstract=2326253)
- [Using genetic algorithms to find technical trading rules (JFE 1999)](https://www.cs.montana.edu/courses/spring2007/536/materials/Lopez/genetic.pdf)
- [Fundamentals of perpetual futures (arXiv 2212.06888)](https://arxiv.org/pdf/2212.06888)
- [An empirical investigation on risk factors in cryptocurrency futures](https://katalog.lib.cas.cz/KNAV/EdsRecord/edsair,edsair.doi.dedup.....63ceef0168b9a0081406939244ac95a7)
- [The quarter-hour effect (arXiv 2607.09426)](https://arxiv.org/pdf/2607.09426)
- [Systematic trend-following with adaptive portfolio construction (arXiv 2602.11708)](https://arxiv.org/pdf/2602.11708)
