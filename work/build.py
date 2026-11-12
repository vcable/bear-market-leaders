"""Tag each name, build the growth-leader lists, and write the CSV + summary stats."""
import csv, json, statistics as st

# category, theme.  "Growth" and "Turnaround" make the growth lists; the rest are kept in the CSV.
TAGS = {
    "NVDA": ("Growth", "AI chips"), "AMD": ("Growth", "AI chips / CPUs"), "AVGO": ("Growth", "AI custom chips + VMware"),
    "MRVL": ("Growth", "AI custom chips / optics"), "CRDO": ("Growth", "AI connectivity chips"),
    "SMCI": ("Growth", "AI servers"), "VRT": ("Growth", "AI data-center power & cooling"),
    "ANET": ("Growth", "AI networking"), "CLS": ("Growth", "AI hardware manufacturing"),
    "COHR": ("Growth", "AI optical components"), "ONTO": ("Growth", "Semi equipment (advanced packaging)"),
    "POWL": ("Growth", "Electrical gear (data centers, LNG)"), "FIX": ("Growth", "Mechanical contractor (data centers)"),
    "EME": ("Growth", "Electrical contractor (data centers)"), "PRIM": ("Growth", "Power & infrastructure contractor"),
    "ROAD": ("Growth", "Road construction"), "VST": ("Growth", "AI power demand (power producer)"),
    "NRG": ("Growth", "AI power demand (power producer)"),
    "APP": ("Growth", "AI ad-tech"), "PLTR": ("Growth", "AI software"), "META": ("Growth", "Ads + cost discipline"),
    "NFLX": ("Growth", "Streaming (ads, password sharing)"), "SPOT": ("Growth", "Music streaming (margin inflection)"),
    "UBER": ("Growth", "Ride-hailing / delivery (first profits)"), "DASH": ("Growth", "Delivery platform"),
    "SHOP": ("Growth", "E-commerce software"), "CRWD": ("Growth", "Cybersecurity"), "PANW": ("Growth", "Cybersecurity"),
    "ZS": ("Growth", "Cybersecurity"), "IOT": ("Growth", "IoT software"), "MDB": ("Growth", "Database software"),
    "HUBS": ("Growth", "Marketing software"), "ESTC": ("Growth", "Search / observability software"),
    "PATH": ("Growth", "Automation software"), "QTWO": ("Growth", "Banking software"), "ZETA": ("Growth", "Marketing software"),
    "FSLY": ("Growth", "Edge cloud (beaten-down rebound)"), "ROKU": ("Growth", "Streaming platform (beaten-down rebound)"),
    "UI": ("Growth", "Networking hardware"), "FICO": ("Growth", "Credit scores (pricing power)"),
    "DUOL": ("Growth", "Language-learning app"), "DKNG": ("Growth", "Online sports betting"),
    "AFRM": ("Growth", "Buy-now-pay-later fintech"), "HOOD": ("Growth", "Retail brokerage (crypto-levered)"),
    "IBKR": ("Growth", "Online brokerage"), "TSLA": ("Growth", "EVs / autonomy"),
    "RKLB": ("Growth", "Space launch & systems"), "AXON": ("Growth", "Tasers, body cams + software"),
    "FTAI": ("Growth", "Jet-engine aftermarket"), "HWM": ("Growth", "Aerospace engine parts"),
    "ELF": ("Growth", "Cosmetics"), "ONON": ("Growth", "Running shoes"), "DECK": ("Growth", "HOKA / UGG footwear"),
    "BRBR": ("Growth", "Protein shakes"), "FRPT": ("Growth", "Pet food"), "SFM": ("Growth", "Natural-foods grocer"),
    "CAVA": ("Growth", "Fast-casual restaurant (2023 IPO)"), "SG": ("Growth", "Fast-casual restaurant"),
    "SHAK": ("Growth", "Fast-casual restaurant"), "RVLV": ("Growth", "Online fashion retail"),
    "LRN": ("Growth", "Online K-12 education"), "MMYT": ("Growth", "India online travel"),
    "NTRA": ("Growth", "Genetic testing"), "GKOS": ("Growth", "Eye-care medtech"), "RDNT": ("Growth", "Imaging centers"),
    "HIMS": ("Growth", "Telehealth (GLP-1s)"),
    "ANF": ("Turnaround", "Apparel retail turnaround"), "CVNA": ("Turnaround", "Online used cars, from near-bankruptcy"),
    "EAT": ("Turnaround", "Chili's comeback"), "CRS": ("Turnaround", "Aerospace alloys, earnings inflection"),
    "SMTC": ("Turnaround", "AI copper interconnect after debt scare"), "SE": ("Turnaround", "SE Asia e-commerce rebound"),
    "ERJ": ("Turnaround", "Brazilian aircraft maker"), "KD": ("Turnaround", "IT services (IBM spin-off)"),
    "TEVA": ("Turnaround", "Generic-drug maker turnaround"), "UPST": ("Turnaround", "AI lending, high short interest"),
    "COIN": ("Crypto proxy", "Crypto exchange"), "MSTR": ("Crypto proxy", "Bitcoin treasury"),
    "BTDR": ("Crypto proxy", "Bitcoin miner"),
    "AI": ("Speculative", "AI software, slow growth"), "IONQ": ("Speculative", "Quantum computing"),
    "LMND": ("Speculative", "Insurtech"),
    "RCL": ("Recovery", "Cruise line"), "CCL": ("Recovery", "Cruise line"), "CUK": ("Recovery", "Cruise line"),
    "UAL": ("Recovery", "Airline"), "CNK": ("Recovery", "Movie theaters"), "EDU": ("Recovery", "China education rebound"),
    "BLDR": ("Cyclical", "Building products"), "BLD": ("Cyclical", "Insulation installer"),
    "IBP": ("Cyclical", "Insulation installer"), "SSD": ("Cyclical", "Building products"), "TREX": ("Cyclical", "Decking"),
    "PHM": ("Cyclical", "Homebuilder"), "TOL": ("Cyclical", "Homebuilder"), "KBH": ("Cyclical", "Homebuilder"),
    "CNM": ("Cyclical", "Water/sewer distribution"), "XPO": ("Cyclical", "LTL trucking (Yellow bankruptcy)"),
    "SAIA": ("Cyclical", "LTL trucking (Yellow bankruptcy)"), "AMR": ("Cyclical", "Met coal"),
    "CRK": ("Cyclical", "Natural gas"), "TRGP": ("Cyclical", "Midstream energy"), "TDW": ("Cyclical", "Offshore vessels"),
    "TPL": ("Cyclical", "Permian land & royalties"), "ZIM": ("Cyclical", "Container shipping (Red Sea)"),
    "BVN": ("Cyclical", "Peru precious-metals miner"),
    "WSM": ("Mature re-rating", "Home furnishings (margins)"), "DELL": ("Mature re-rating", "PCs / AI servers"),
    "CRM": ("Mature re-rating", "Software margin expansion"), "KKR": ("Mature re-rating", "Alt asset manager"),
    "GGAL": ("Foreign macro", "Argentina bank (Milei reforms)"), "BMA": ("Foreign macro", "Argentina bank (Milei reforms)"),
    "YPF": ("Foreign macro", "Argentina energy (Milei reforms)"), "QFIN": ("Foreign macro", "China consumer lending"),
    "GDS": ("Foreign macro", "China data centers"),
    "IMVT": ("Biotech event", "Drug data readout"), "SRRK": ("Biotech event", "SMA drug Phase 3 (Oct 2024)"),
    "VKTX": ("Biotech event", "Obesity drug data"), "VRNA": ("Biotech event", "COPD drug approval"),
    "ACAD": ("Biotech event", "Rett syndrome drug approval"), "INSM": ("Biotech event", "Lung drug Phase 3 (May 2024)"),
    "NVCR": ("Biotech event", "Cancer device data"), "BPMC": ("Biotech event", "Rare-disease drug launch"),
    "GE": ("Special situation", "Break-up into 3 companies (spin-offs)"), "TDS": ("Special situation", "UScellular asset sale"),
    "IDCC": ("Special situation", "Patent licensing settlements"), "GEO": ("Special situation", "Private prisons (election trade)"),
    "SHC": ("Special situation", "Sterilization services"),
}
GROWTH = {"Growth", "Turnaround", "Crypto proxy"}

screen = json.load(open("screen.json"))
an = json.load(open("analysis.json"))
rows = {r["ticker"]: r for r in an["rows"]}
idx = {r["ticker"]: r for r in an["index"]}
missing = [t for t in rows if t not in TAGS]
assert not missing, missing

info, ranks = {}, {}
for k in ("2023", "2024", "2023-24"):
    for i, r in enumerate(screen[k], 1):
        info.setdefault(r["ticker"], {}).update(name=r["name"])
        info[r["ticker"]][f"cap_{k}"] = r["start_cap_b"]
        ranks.setdefault(r["ticker"], {})[k] = i


def rel(a, b):
    return None if a is None or b is None else round(a - b, 1)


out = []
for t, r in rows.items():
    cat, theme = TAGS[t]
    rk = ranks.get(t, {})
    out.append({
        "ticker": t, "company": info[t]["name"], "category": cat, "theme": theme,
        "growth_list": "Y" if cat in GROWTH else "N",
        "screen_rank_2023": rk.get("2023") if rk.get("2023", 999) <= 60 else "",
        "screen_rank_2024": rk.get("2024") if rk.get("2024", 999) <= 60 else "",
        "screen_rank_2023_24": rk.get("2023-24") if rk.get("2023-24", 999) <= 60 else "",
        "ret_2023_pct": r["ret_2023"], "vs_spy_2023_pts": rel(r["ret_2023"], idx["SPY"]["ret_2023"]),
        "vs_qqq_2023_pts": rel(r["ret_2023"], idx["QQQ"]["ret_2023"]),
        "ret_2024_pct": r["ret_2024"], "vs_spy_2024_pts": rel(r["ret_2024"], idx["SPY"]["ret_2024"]),
        "vs_qqq_2024_pts": rel(r["ret_2024"], idx["QQQ"]["ret_2024"]),
        "ret_2023_24_pct": r["ret_2023_24"],
        "mktcap_end2022_b": info[t].get("cap_2023", ""), "mktcap_end2023_b": info[t].get("cap_2024", ""),
        "prior_high_date": r["prior_high_date"], "bear_drawdown_pct": r["bear_drawdown_pct"],
        "cycle_low_date": r["cycle_low_date"], "first_52w_high_after_low": r["first_52w_high_date"],
        "pct_off_low_at_first_52w_high": r["pct_off_low_at_52w_high"],
        "vol_on_low_x_50d_avg": r["low_vol_vs_50d"], "vol_on_first_52w_high_x_50d_avg": r["high_vol_vs_50d"],
        "rs_line_first_52w_high": r["rs_line_52w_high_date"], "rs_line_led_price": "Y" if r["rs_led_price"] else "N",
        "run_peak_date_2023_24": r["run_peak_date"], "low_to_peak_pct": r["low_to_peak_pct"],
        "chg_spy_corr_jul31_oct27_2023_pct": r["spy_corr_2023_pct"],
        "chg_spy_corr_jul16_aug5_2024_pct": r["spy_corr_2024_pct"],
    })
out.sort(key=lambda r: -(r["ret_2023_24_pct"] if r["ret_2023_24_pct"] is not None else -1e9))

with open("../growth_leaders_2023_2024.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader()
    for t, name in (("SPY", "S&P 500 ETF (benchmark)"), ("QQQ", "Nasdaq-100 ETF (benchmark)")):
        r = idx[t]
        w.writerow({"ticker": t, "company": name, "category": "Benchmark", "growth_list": "N",
                    "ret_2023_pct": r["ret_2023"], "ret_2024_pct": r["ret_2024"], "ret_2023_24_pct": r["ret_2023_24"],
                    "prior_high_date": r["prior_high_date"], "bear_drawdown_pct": r["bear_drawdown_pct"],
                    "cycle_low_date": r["cycle_low_date"], "first_52w_high_after_low": r["first_52w_high_date"],
                    "pct_off_low_at_first_52w_high": r["pct_off_low_at_52w_high"],
                    "run_peak_date_2023_24": r["run_peak_date"], "low_to_peak_pct": r["low_to_peak_pct"],
                    "chg_spy_corr_jul31_oct27_2023_pct": r["spy_corr_2023_pct"],
                    "chg_spy_corr_jul16_aug5_2024_pct": r["spy_corr_2024_pct"]})
    w.writerows(out)

by = {r["ticker"]: r for r in out}
lists = {}
for k, col in (("2023", "ret_2023_pct"), ("2024", "ret_2024_pct"), ("2023-24", "ret_2023_24_pct")):
    top = [r["ticker"] for r in screen[k] if r["ticker"] in by and by[r["ticker"]]["growth_list"] == "Y"][:25]
    skipped = [(r["ticker"], TAGS[r["ticker"]][0]) for r in screen[k][:25] if TAGS.get(r["ticker"], ("?",))[0] not in GROWTH]
    lists[k] = top
    print(f"\n=== {k}  (SPY {idx['SPY']['ret_' + k.replace('-', '_')]}%, QQQ {idx['QQQ']['ret_' + k.replace('-', '_')]}%)")
    for i, t in enumerate(top, 1):
        r = by[t]
        print(f"{i:2} {t:5} {r[col]:7}% | {r['company'][:30]:30} | {r['category'][:4]} {r['theme'][:34]:34} | low {r['cycle_low_date']} dd {r['bear_drawdown_pct']} | 52wH {r['first_52w_high_after_low']} (+{r['pct_off_low_at_first_52w_high']}) | RS {r['rs_line_first_52w_high']} {r['rs_line_led_price']} | c23 {r['chg_spy_corr_jul31_oct27_2023_pct']} c24 {r['chg_spy_corr_jul16_aug5_2024_pct']}")
    print("non-growth names in overall top 25:", skipped)

# pattern stats for the 2023 growth leaders (the names coming straight out of the bear market)
g = [by[t] for t in lists["2023"]]
spy_52, qqq_52 = idx["SPY"]["first_52w_high_date"], idx["QQQ"]["first_52w_high_date"]
before_spy = [r["ticker"] for r in g if r["first_52w_high_after_low"] and r["first_52w_high_after_low"] < spy_52]
before_qqq = [r["ticker"] for r in g if r["first_52w_high_after_low"] and r["first_52w_high_after_low"] < qqq_52]
led_2022 = [r["ticker"] for r in g if r["first_52w_high_after_low"] and r["first_52w_high_after_low"] < "2022-10-12"]
rs_led = [r["ticker"] for r in g if r["rs_line_led_price"] == "Y"]
print("\n2023 top-25 growth stats")
print("median bear drawdown", st.median(r["bear_drawdown_pct"] for r in g))
print("lows: by month", sorted(r["cycle_low_date"][:7] for r in g))
print("first 52w high before SPY's (", spy_52, "):", len(before_spy), before_spy)
print("first 52w high before QQQ's (", qqq_52, "):", len(before_qqq))
print("already at 52w highs before SPY's 10/12/22 low:", led_2022)
print("RS line led price:", len(rs_led), rs_led)
print("median % off low at first 52w high", st.median(r["pct_off_low_at_first_52w_high"] for r in g if r["pct_off_low_at_first_52w_high"] is not None))
print("Aug-Oct 2023 correction: SPY", idx["SPY"]["spy_corr_2023_pct"], "median leader", st.median(r["chg_spy_corr_jul31_oct27_2023_pct"] for r in g),
      "held better than SPY:", [r["ticker"] for r in g if r["chg_spy_corr_jul31_oct27_2023_pct"] > idx["SPY"]["spy_corr_2023_pct"]])
g24 = [by[t] for t in lists["2024"]]
print("Jul-Aug 2024 correction: SPY", idx["SPY"]["spy_corr_2024_pct"], "QQQ", idx["QQQ"]["spy_corr_2024_pct"], "median 2024 leader", st.median(r["chg_spy_corr_jul16_aug5_2024_pct"] for r in g24))
print("2024 leaders' lows by year-month", sorted(r["cycle_low_date"][:7] for r in g24))
print("2024 first 52w highs", sorted((r["first_52w_high_after_low"] or "none")[:7] for r in g24))
json.dump(lists, open("lists.json", "w"))
