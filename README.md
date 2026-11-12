# Bear Market Leaders

A model-book study of the top growth stocks coming out of bear markets: what they looked like early on, how they behaved against the S&P 500 and Nasdaq-100, and the earnings, catalysts and themes behind their runs.

## Cycles covered

| Cycle | S&P 500 low | SPY first new 52-week high |
|---|---|---|
| 2018 | Dec 24, 2018 | Apr 29, 2019 |
| 2020 | Mar 23, 2020 | Aug 18, 2020 |
| 2022 | Oct 12, 2022 | Jun 9, 2023 |

Earlier cycles (2016, 2009, the dot-com low) are outside the 10-year history of the current Massive plan.

## How leaders are picked

- Universe: US-listed common stocks and ADRs, including ones later delisted.
- On the day of the index low: price at least $5, market cap at least $500M, at least $5M average daily dollar volume over the prior 20 sessions.
- Ranked by price gain in the 12 months after the index low; the top 60 are analyzed and tagged, and the top 25 growth stocks, turnarounds and crypto proxies make each cycle's list.
- Stocks that went public after a low are not in that cycle's list.

Per stock: bear-market drawdown, the stock's own low, its first new 52-week high (a close above every close of the prior 251 sessions), the RS line's first new high (stock divided by SPY), volume on those days against the prior 50-session average, and its moves during the index's two largest ordinary pullbacks (5-20%) in the 24 months after the low.

## Files

| Path | What it is |
|---|---|
| `bear_market_leaders.csv` | All 180 screened names across the three cycles, with tags and timing stats |
| `growth_leaders_2023_2024.csv` | Earlier study: top growth stocks by calendar year 2023 and 2024 |
| `work/cycles.py` | Multi-cycle screen (12-month gain from each index low) |
| `work/cycles_analyze.py` | Daily-bar analysis of each cycle's top 60 |
| `work/cycles_build.py` | Category tags, top-25 lists, cross-cycle stats, CSV |
| `work/screen.py`, `analyze.py`, `build.py`, `export.py` | The calendar-year 2023/2024 study and its dashboard data |
| `work/fetch.py` | Massive API client with a local cache |
| `work/out/` | Data files and page source for the Growth Leaders 2023-24 dashboard |

## Running it

Python 3.10 or later, standard library only.

```bash
export MASSIVE_API_KEY=your_key   # or put the key in work/key.txt (git-ignored)
cd work
python cycles.py && python cycles_analyze.py && python cycles_build.py
```

API responses are cached in `work/cache/` (git-ignored), so reruns are fast. A fresh computer re-downloads them on the first run.

## Data sources

- Prices and volume: [Massive](https://massive.com) (formerly Polygon.io), split-adjusted daily bars. Stocks Developer plan: 10 years of history.
- Earnings (planned): SEC EDGAR structured filings, which give reported (GAAP) quarterly EPS and revenue from 2009 on, and earnings-release dates from 8-K filings.

## Dashboards

- [Growth Leaders 2023-24](https://claude.ai/artifact/L1RM2pYDKMrcrUBFDHKtU7): daily charts of the 2023 and 2024 leaders against SPY and QQQ, with RS line, volume and run-start markers.
