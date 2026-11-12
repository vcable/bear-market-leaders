"""New issues: stocks that started trading in the 12 months after each bear-market low, ranked by their first-year gain."""
import json
from concurrent.futures import ThreadPoolExecutor
from fetch import tickers, details, bars
from cycles import CYCLES, EXCHANGES, windows, spy_days, add_months, on_or_before, day

MIN_CAP = 1e9        # market cap 12 months after the index low
MIN_ADV = 5e6        # average daily dollar volume over the first 20 sessions
BLANK_CHECK = "BLANK CHECKS"


def listed(date):
    return {t["ticker"]: t for typ in ("CS", "ADRC") for t in tickers(date, typ)
            if t.get("primary_exchange") in EXCHANGES}


def history(t, c):
    """Daily bars from the index low to two years after the end of the IPO window."""
    return bars(t, c["low"], add_months(c["m12"], 25))


def screen(k, c):
    before, after = listed(c["low"]), listed(c["m12"])
    new = [t for t in after if t not in before]
    with ThreadPoolExecutor(8) as ex:
        det = dict(zip(new, ex.map(lambda t: details(t, c["m12"]), new)))
        hist = dict(zip(new, ex.map(lambda t: history(t, c), new)))
    rows = []
    for t in new:
        d, b = det[t], hist[t]
        if not b or BLANK_CHECK in (d.get("sic_description") or "").upper():
            continue
        first = day(b[0]["t"])
        if not (c["low"] < first <= c["m12"]):
            continue  # traded under this symbol before the low
        dv = [x["v"] * x.get("vw", x["c"]) for x in b[:20]]
        adv = sum(dv) / len(dv)
        cap = d.get("market_cap") or 0
        if cap < MIN_CAP or adv < MIN_ADV:
            continue
        end = add_months(first, 12)
        closes = [(day(x["t"]), x["c"]) for x in b]
        if closes[-1][0] < end:
            continue  # did not trade for a full year
        c12 = [v for dd, v in closes if dd <= end][-1]
        rows.append({
            "ticker": t, "name": after[t]["name"], "type": after[t]["type"], "sic": d.get("sic_description", ""),
            "list_date": d.get("list_date"), "first_day": first, "first_close": b[0]["c"], "first_open": b[0]["o"],
            "cap_b": round(cap / 1e9, 2), "adv_m": round(adv / 1e6, 1),
            "ret_12m_from_first_close": round((c12 / b[0]["c"] - 1) * 100, 1),
        })
    rows.sort(key=lambda r: -r["ret_12m_from_first_close"])
    print(f"\n== {k}: {len(new)} new symbols, {len(rows)} pass cap/liquidity/full year")
    for r in rows[:45]:
        print(f"{r['ticker']:6} {r['ret_12m_from_first_close']:7.1f}%  first {r['first_day']}  listed {r['list_date']}  cap {r['cap_b']:6.2f}B adv {r['adv_m']:6.1f}M  {r['name'][:34]:34} | {r['sic'][:30]}")
    return rows


if __name__ == "__main__":
    days = spy_days()
    out = {}
    for k, c in CYCLES.items():
        c = windows(c, days)
        out[k] = {"cycle": c, "rows": screen(k, c)}
    json.dump(out, open("cycles_ipos_screen.json", "w"), indent=1)
