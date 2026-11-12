"""Write the three files the chart dashboard reads: daily closes, leader stats, index reference dates."""
import json, os, re
from analyze import series

os.makedirs("out", exist_ok=True)
lists = json.load(open("lists.json"))
an = json.load(open("analysis.json"))
rows = {r["ticker"]: r for r in an["rows"]}
idx = {r["ticker"]: r for r in an["index"]}
csvrows = {}
import csv
for r in csv.DictReader(open("../growth_leaders_2023_2024.csv", encoding="utf-8")):
    csvrows[r["ticker"]] = r

tickers = []
for k in ("2023", "2024"):
    for t in lists[k]:
        if t not in tickers:
            tickers.append(t)

NAMES = {
    "AFRM": "Affirm", "COIN": "Coinbase", "MSTR": "MicroStrategy", "ANF": "Abercrombie & Fitch", "APP": "AppLovin",
    "VRT": "Vertiv", "SMCI": "Super Micro Computer", "NVDA": "Nvidia", "DUOL": "Duolingo", "DKNG": "DraftKings",
    "UPST": "Upstart", "META": "Meta Platforms", "FTAI": "FTAI Aviation", "IOT": "Samsara", "PLTR": "Palantir",
    "ELF": "e.l.f. Beauty", "UBER": "Uber", "CRWD": "CrowdStrike", "SPOT": "Spotify", "AMD": "Advanced Micro Devices",
    "ROKU": "Roku", "ONTO": "Onto Innovation", "SHOP": "Shopify", "ESTC": "Elastic", "FSLY": "Fastly",
    "RKLB": "Rocket Lab", "CVNA": "Carvana", "VST": "Vistra", "CRDO": "Credo Technology", "CLS": "Celestica",
    "EAT": "Brinker International", "HOOD": "Robinhood", "SG": "Sweetgreen", "SMTC": "Semtech", "HIMS": "Hims & Hers",
    "SFM": "Sprouts Farmers Market", "CAVA": "CAVA Group", "SE": "Sea Limited", "NTRA": "Natera",
    "POWL": "Powell Industries", "CRS": "Carpenter Technology", "MMYT": "MakeMyTrip", "UI": "Ubiquiti",
    "QTWO": "Q2 Holdings", "BRBR": "BellRing Brands", "PANW": "Palo Alto Networks",
}


def clean(t, name):
    return NAMES.get(t, name)


def num(v):
    return None if v in ("", None) else float(v)


leaders = []
for t in tickers:
    c, r = csvrows[t], rows[t]
    leaders.append({
        "ticker": t, "company": clean(t, c["company"]), "category": c["category"], "theme": c["theme"],
        "rank_2023": lists["2023"].index(t) + 1 if t in lists["2023"] else None,
        "rank_2024": lists["2024"].index(t) + 1 if t in lists["2024"] else None,
        "ret_2023_pct": r["ret_2023"], "ret_2024_pct": r["ret_2024"], "ret_2023_24_pct": r["ret_2023_24"],
        "vs_spy_2023_pts": num(c["vs_spy_2023_pts"]), "vs_spy_2024_pts": num(c["vs_spy_2024_pts"]),
        "prior_high_date": r["prior_high_date"], "bear_drawdown_pct": r["bear_drawdown_pct"],
        "low_date": r["cycle_low_date"],
        "first_52w_high_date": r["first_52w_high_date"], "pct_off_low_at_52w_high": r["pct_off_low_at_52w_high"],
        "low_volume": r["low_volume"], "low_vol_vs_50d": r["low_vol_vs_50d"],
        "high_volume": r["high_volume"], "high_vol_vs_50d": r["high_vol_vs_50d"],
        "rs_new_high_date": r["rs_line_52w_high_date"], "rs_led_price": "Yes" if r["rs_led_price"] else "No",
        "run_peak_date": r["run_peak_date"], "low_to_peak_pct": r["low_to_peak_pct"],
        "corr_2023_pct": r["spy_corr_2023_pct"], "corr_2024_pct": r["spy_corr_2024_pct"],
    })

(c23a, c23b), (c24a, c24b) = an["corrections"]["spy_corr_2023"], an["corrections"]["spy_corr_2024"]
events = [
    {"id": "spy_low", "label": "SPY low", "start": idx["SPY"]["cycle_low_date"], "end": None, "spy_pct": None},
    {"id": "qqq_low", "label": "QQQ low", "start": idx["QQQ"]["cycle_low_date"], "end": None, "spy_pct": None},
    {"id": "qqq_52w", "label": "QQQ new high", "start": idx["QQQ"]["first_52w_high_date"], "end": None, "spy_pct": None},
    {"id": "spy_52w", "label": "SPY new high", "start": idx["SPY"]["first_52w_high_date"], "end": None, "spy_pct": None},
    {"id": "corr_2023", "label": "SPY correction", "start": c23a, "end": c23b, "spy_pct": idx["SPY"]["spy_corr_2023_pct"]},
    {"id": "corr_2024", "label": "SPY pullback", "start": c24a, "end": c24b, "spy_pct": idx["SPY"]["spy_corr_2024_pct"]},
]


def rnd(v):
    return round(v, 2) if v >= 10 else round(v, 3)


cols = ["SPY", "QQQ"] + tickers
data = {t: dict(series(t)) for t in cols}
prices = [{"date": d, **{t: (rnd(data[t][d]) if d in data[t] else None) for t in cols}} for d, _ in series("SPY")]
vdata = {t: dict(series(t, "v")) for t in tickers}
volumes = [{"date": d, **{t: (int(vdata[t][d]) if vdata[t].get(d) else None) for t in tickers}} for d, _ in series("SPY")]

for name, obj in (("prices", prices), ("volumes", volumes), ("leaders", leaders), ("events", events)):
    json.dump(obj, open(f"out/{name}.json", "w"), separators=(",", ":"))
    print(name, len(obj), os.path.getsize(f"out/{name}.json"), "bytes")
print(len(tickers), "tickers")
for l in leaders[:6] + leaders[-3:]:
    print(l["ticker"], "|", l["company"], "|", l["rank_2023"], l["rank_2024"])
print(sorted({l["company"] for l in leaders}))
