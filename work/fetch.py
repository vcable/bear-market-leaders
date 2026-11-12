"""Pull market-wide daily snapshots and reference data from Massive for the 2023/2024 screen."""
import json, os, sys, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

KEY = os.environ.get("MASSIVE_API_KEY") or open(os.path.join(os.path.dirname(__file__), "key.txt")).read().strip()
BASE = "https://api.massive.com"
CACHE = os.path.join(os.path.dirname(__file__), "cache")
os.makedirs(CACHE, exist_ok=True)


def get(url, tries=5):
    sep = "&" if "?" in url else "?"
    for i in range(tries):
        try:
            with urllib.request.urlopen(f"{url}{sep}apiKey={KEY}", timeout=60) as r:
                return json.load(r)
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))


def cached(name, fn):
    p = os.path.join(CACHE, name)
    if os.path.exists(p):
        return json.load(open(p))
    d = fn()
    json.dump(d, open(p, "w"))
    return d


def grouped(date, adjusted):
    return cached(f"grouped_{date}_{'adj' if adjusted else 'raw'}.json",
                  lambda: get(f"{BASE}/v2/aggs/grouped/locale/us/market/stocks/{date}?adjusted={str(adjusted).lower()}"))


def tickers(date, typ):
    def fn():
        out, url = [], f"{BASE}/v3/reference/tickers?market=stocks&type={typ}&date={date}&limit=1000"
        while url:
            d = get(url)
            out += d.get("results", [])
            url = d.get("next_url")
        return out
    return cached(f"tickers_{date}_{typ}.json", fn)


def details(ticker, date):
    return cached(f"details_{ticker}_{date}.json",
                  lambda: get(f"{BASE}/v3/reference/tickers/{urllib.parse.quote(ticker)}?date={date}").get("results", {}))


def bars(ticker, start, end):
    return cached(f"bars_{ticker}_{start}_{end}.json",
                  lambda: get(f"{BASE}/v2/aggs/ticker/{urllib.parse.quote(ticker)}/range/1/day/{start}/{end}?adjusted=true&sort=asc&limit=50000").get("results", []))


if __name__ == "__main__":
    # December trading days before each period start, for liquidity + actual price at the time
    import datetime as dt
    days = []
    for y in (2022, 2023):
        d = dt.date(y, 12, 1)
        while d.year == y:
            if d.weekday() < 5:
                days.append(d.isoformat())
            d += dt.timedelta(days=1)
    jobs = [(d, False) for d in days] + [(d, True) for d in ("2022-12-30", "2023-12-29", "2024-12-31")]
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(lambda a: grouped(*a), jobs))
    for date in ("2022-12-30", "2023-12-29"):
        for typ in ("CS", "ADRC"):
            print(date, typ, len(tickers(date, typ)))
