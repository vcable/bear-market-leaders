"""Rank US-listed stocks by price return for 2023, 2024 and 2023-24, after liquidity and size filters."""
import json, sys
from concurrent.futures import ThreadPoolExecutor
from fetch import grouped, tickers, details

EXCHANGES = {"XNYS", "XNAS", "XASE", "ARCX", "BATS"}
MIN_PRICE = 5          # actual (unadjusted) close at period start
MIN_ADV = 10e6         # average daily dollar volume over the prior December
MIN_CAP = 1e9          # market cap at period start

PERIODS = {
    "2023": ("2022-12-30", "2023-12-29"),
    "2024": ("2023-12-29", "2024-12-31"),
    "2023-24": ("2022-12-30", "2024-12-31"),
}


def closes(date, adjusted):
    return {r["T"]: r for r in grouped(date, adjusted).get("results", [])}


def december_adv(year):
    import datetime as dt
    tot, n = {}, {}
    d = dt.date(year, 12, 1)
    while d.year == year:
        if d.weekday() < 5:
            for t, r in closes(d.isoformat(), False).items():
                tot[t] = tot.get(t, 0) + r["v"] * r.get("vw", r["c"])
                n[t] = n.get(t, 0) + 1
        d += dt.timedelta(days=1)
    return {t: tot[t] / n[t] for t in tot if n[t] >= 15}


def screen(start, end):
    ref = {t["ticker"]: t for typ in ("CS", "ADRC") for t in tickers(start, typ)
           if t.get("primary_exchange") in EXCHANGES}
    raw, a0, a1 = closes(start, False), closes(start, True), closes(end, True)
    adv = december_adv(int(start[:4]))
    pre = [t for t in ref if t in raw and t in a0 and t in a1
           and raw[t]["c"] >= MIN_PRICE and adv.get(t, 0) >= MIN_ADV]
    with ThreadPoolExecutor(8) as ex:
        det = dict(zip(pre, ex.map(lambda t: details(t, start), pre)))
    rows = []
    for t in pre:
        cap = det[t].get("market_cap") or 0
        if cap < MIN_CAP:
            continue
        rows.append({
            "ticker": t, "name": ref[t]["name"], "type": ref[t]["type"],
            "exchange": ref[t]["primary_exchange"], "sic": det[t].get("sic_description", ""),
            "start_close_actual": raw[t]["c"], "start_cap_b": round(cap / 1e9, 2),
            "adv_m": round(adv[t] / 1e6, 1),
            "ret_pct": round((a1[t]["c"] / a0[t]["c"] - 1) * 100, 1),
        })
    rows.sort(key=lambda r: -r["ret_pct"])
    return rows, len(ref), len(pre)


if __name__ == "__main__":
    out = {}
    for k, (s, e) in PERIODS.items():
        rows, nref, npre = screen(s, e)
        out[k] = rows
        print(f"\n== {k}: {nref} listed, {npre} pass price/liquidity, {len(rows)} pass $1B cap")
        for r in rows[:60]:
            print(f"{r['ticker']:6} {r['ret_pct']:8.1f}%  cap {r['start_cap_b']:7.2f}B  adv {r['adv_m']:7.1f}M  {r['name'][:38]:38} | {r['sic'][:40]}")
    json.dump(out, open("screen.json", "w"), indent=1)
