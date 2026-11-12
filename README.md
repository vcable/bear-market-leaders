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
- Stocks that went public after a low are on that cycle's separate new-issues list.

Per stock: bear-market drawdown, the stock's own low, its first new 52-week high (a close above every close of the prior 251 sessions), the RS line's first new high (stock divided by SPY), volume on those days against the prior 50-session average, and its moves during the index's two largest ordinary pullbacks (5-20%) in the 24 months after the low.

## New issues

- Companies that started trading in the 12 months after each index low: IPOs, direct listings, SPAC mergers and spin-offs. Renamed or relisted companies are left out.
- Worth $1B or more 12 months after the low, at least $5M average daily dollar volume over the first 20 sessions, and a full year of trading.
- Growth companies with a positive first year, ranked by gain from the first close over the first year (up to 25 per cycle). Trial-data biotechs, cyclicals, financials that are not growth stories, and spin-offs of mature industrial businesses are left out.
- First base and breakout: the breakout is the first close above every earlier close that comes at least 15 sessions (three weeks) after the previous closing high; the base runs from that high to the breakout, and its low is the lowest close in between. Breakout volume is compared with up to 50 prior sessions, leaving out the two IPO days.

## Earnings

Quarterly sales and diluted EPS come from SEC EDGAR structured filings (XBRL company facts):

- Each quarter's figures are the ones first reported for it. Year-over-year growth uses the year-earlier figures shown in the same filing, the comparison the company presented at the time.
- EPS is adjusted for later stock splits (split history from Massive), so it lines up with the split-adjusted prices.
- Fourth quarters that are not tagged on their own are the fiscal year minus the first three quarters (marked * on the page).
- Release dates are the last 8-K with item 2.02 (results of operations) between the quarter's end and its 10-Q/10-K, capped at 100 days; otherwise the 10-Q/10-K filing date.
- Foreign companies that file 20-F annual reports (Sea, Novo Nordisk, the Chinese ADRs and others) have only annual figures in SEC data.
- Figures are GAAP. Companies often headline adjusted (non-GAAP) numbers, which can differ.

## What fueled each run

`work/stories/part_*.json` holds a short write-up for every stock on both lists: what started the run and what kept it going, with dated catalysts and source links. They were researched from news, company and SEC sources by Claude with web search, given each stock's chart dates and SEC figures. Treat specifics as a starting point and check the sources; some catalysts are marked as unclear where no single trigger was found.

## Files

| Path | What it is |
|---|---|
| `bear_market_leaders.csv` | All 180 screened names across the three cycles, with tags and timing stats |
| `growth_leaders_2023_2024.csv` | Earlier study: top growth stocks by calendar year 2023 and 2024 |
| `work/cycles.py` | Multi-cycle screen (12-month gain from each index low) |
| `work/cycles_analyze.py` | Daily-bar analysis of each cycle's top 60 |
| `work/cycles_build.py` | Category tags, top-25 lists, cross-cycle stats, CSV |
| `work/cycles_ipos.py` | New-issues screen: new listings in the 12 months after each low |
| `work/cycles_ipos_analyze.py` | New-issue tags, first base and breakout, RS line, volume |
| `work/sec.py` | SEC EDGAR client (company facts, filing history), cached in `work/cache/sec/` |
| `work/earnings.py` | Quarterly sales/EPS, year-over-year growth, acceleration and release dates |
| `work/sec_ciks.json` | Ticker to SEC company ID for every stock studied |
| `work/stories/` | Research briefs and the "what fueled the run" write-ups |
| `work/cycles_export.py` | Writes `site/data/<cycle>.json` (prices, lists, earnings, write-ups) for the Bear Market Leaders page |
| `site/` | Page source (`index.html`) and per-cycle data for the Bear Market Leaders page |
| `work/screen.py`, `analyze.py`, `build.py`, `export.py` | The calendar-year 2023/2024 study and its dashboard data |
| `work/fetch.py` | Massive API client with a local cache |
| `work/out/` | Data files and page source for the Growth Leaders 2023-24 dashboard |

## Running it

Python 3.10 or later, standard library only.

```bash
export MASSIVE_API_KEY=your_key   # or put the key in work/key.txt (git-ignored)
cd work
python cycles.py && python cycles_analyze.py && python cycles_build.py
python cycles_ipos.py && python cycles_ipos_analyze.py && python cycles_export.py
```

API responses are cached in `work/cache/` (git-ignored), so reruns are fast. A fresh computer re-downloads them on the first run.

## Data sources

- Prices and volume: [Massive](https://massive.com) (formerly Polygon.io), split-adjusted daily bars. Stocks Developer plan: 10 years of history.
- Earnings: SEC EDGAR structured filings (GAAP quarterly sales and EPS, 8-K release dates). The SEC requires a contact name and email in each request's User-Agent: set `SEC_USER_AGENT="Your Name you@example.com"` or put that line in `work/sec_ua.txt` (git-ignored). Responses are cached in `work/cache/sec/`.
- Stock splits: Massive reference data.

## Dashboards

- [Bear Market Leaders](https://claude.ai/artifact/S9Pvyh4yJLf25rGzVBUp3w): the 2018, 2020 and 2022 cycles. Leaders and new issues, each charted against SPY and QQQ with RS line, volume, run-start markers, SPY pullbacks, earnings-report and catalyst markers, a "what fueled the run" write-up and a quarterly results table from SEC filings. The Ask Claude panel answers questions about the selected stock, the cycle and any date pinned on the chart, and saves answers and notes privately per viewer. It searches the web only when the page is open in the Claude desktop app; elsewhere it answers without search.
- [Growth Leaders 2023-24](https://claude.ai/artifact/L1RM2pYDKMrcrUBFDHKtU7): daily charts of the 2023 and 2024 leaders against SPY and QQQ, with RS line, volume and run-start markers.
