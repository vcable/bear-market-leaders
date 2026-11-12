"""Multi-cycle leader study: rank stocks by their gain in the 12 months after each bear-market low."""
import datetime as dt
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from fetch import grouped, tickers, details, bars

EXCHANGES = {"XNYS", "XNAS", "XASE", "ARCX", "BATS"}
MIN_PRICE = 5        # actual close on the index-low day
MIN_ADV = 5e6        # average daily dollar volume over the 20 sessions before the low
MIN_CAP = 5e8        # market cap on the index-low day
TOP_N = 60

# index peak before the bear market, index low, and the chart window for each cycle
CYCLES = {
    "2018": {"peak": "2018-09-20", "low": "2018-12-24", "chart_start": "2016-11-14"},
    "2020": {"peak": "2020-02-19", "low": "2020-03-23", "chart_start": "2018-06-01"},
    "2022": {"peak": "2022-01-03", "low": "2022-10-12", "chart_start": "2021-01-04"},
}
SPY_START, SPY_END = "2016-11-14", "2024-12-31"


def day(ts):
    return dt.datetime.fromtimestamp(ts / 1000 + 12 * 3600, dt.timezone.utc).date().isoformat()


def spy_days():
    return [day(b["t"]) for b in bars("SPY", SPY_START, SPY_END)]


def on_or_before(days, date):
    return max(d for d in days if d <= date)


def add_months(date, m):
    d = dt.date.fromisoformat(date)
    y, mo = divmod(d.month - 1 + m, 12)
    return dt.date(d.year + y, mo + 1, min(d.day, 28)).isoformat()


def windows(c, days):
    low = c["low"]
    c = dict(c)
    c["m12"] = on_or_before(days, add_months(low, 12))
    c["m24"] = on_or_before(days, add_months(low, 24))
    c["adv_days"] = [d for d in days if d < low][-20:]
    return c


def closes(date, adjusted):
    return {r["T"]: r for r in grouped(date, adjusted).get("results", [])}


def screen(c):
    low = c["low"]
    ref = {t["ticker"]: t for typ in ("CS", "ADRC") for t in tickers(low, typ)
           if t.get("primary_exchange") in EXCHANGES}
    raw, a0, a12, a24 = closes(low, False), closes(low, True), closes(c["m12"], True), closes(c["m24"], True)
    tot, n = {}, {}
    for d in c["adv_days"]:
        for t, r in closes(d, False).items():
            tot[t] = tot.get(t, 0) + r["v"] * r.get("vw", r["c"])
            n[t] = n.get(t, 0) + 1
    adv = {t: tot[t] / n[t] for t in tot if n[t] >= 15}
    pre = [t for t in ref if t in raw and t in a0 and t in a12
           and raw[t]["c"] >= MIN_PRICE and adv.get(t, 0) >= MIN_ADV]
    with ThreadPoolExecutor(8) as ex:
        det = dict(zip(pre, ex.map(lambda t: details(t, low), pre)))
    rows = []
    for t in pre:
        cap = det[t].get("market_cap") or 0
        if cap < MIN_CAP:
            continue
        rows.append({
            "ticker": t, "name": ref[t]["name"], "type": ref[t]["type"], "sic": det[t].get("sic_description", ""),
            "list_date": det[t].get("list_date"), "low_close_actual": raw[t]["c"],
            "cap_at_low_b": round(cap / 1e9, 2), "adv_m": round(adv[t] / 1e6, 1),
            "ret_12m": round((a12[t]["c"] / a0[t]["c"] - 1) * 100, 1),
            "ret_24m": round((a24[t]["c"] / a0[t]["c"] - 1) * 100, 1) if t in a24 else None,
        })
    rows.sort(key=lambda r: -r["ret_12m"])
    return rows, len(ref), len(pre)


if __name__ == "__main__":
    days = spy_days()
    out = {}
    for k, c in CYCLES.items():
        c = windows(c, days)
        rows, nref, npre = screen(c)
        out[k] = {"cycle": c, "rows": rows}
        print(f"\n== {k} cycle: low {c['low']}, +12m {c['m12']}, +24m {c['m24']} | {nref} listed, {npre} pass price/liquidity, {len(rows)} pass cap")
        for r in rows[:TOP_N]:
            print(f"{r['ticker']:6} 12m {r['ret_12m']:7.1f}%  24m {str(r['ret_24m']):>7}%  cap {r['cap_at_low_b']:6.2f}B  listed {r['list_date']}  {r['name'][:34]:34} | {r['sic'][:34]}")
    json.dump(out, open("cycles_screen.json", "w"), indent=1)
