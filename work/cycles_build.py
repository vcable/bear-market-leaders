"""Tag each cycle's top 60, pick the top 25 growth leaders, and write the CSV and cross-cycle stats."""
import csv
import datetime as dt
import json
import statistics as st

GROWTH = {"Growth", "Turnaround", "Crypto proxy"}
DROP = {"CZR"}  # symbol shared by old Caesars and Eldorado Resorts (renamed Caesars, Jul 2020)
TRIM = {"SE": "2017-10-20"}  # Spectra Energy used SE before Sea's IPO

TAGS = {
    "2018": {
        "ROKU": ("Growth", "Streaming platform"), "SE": ("Growth", "SE Asia e-commerce & games"), "SHOP": ("Growth", "E-commerce software"),
        "CVNA": ("Growth", "Online used cars"), "SNAP": ("Turnaround", "User growth returns after app redesign"),
        "LSCC": ("Turnaround", "FPGA chips, new CEO and margins"), "NVCR": ("Growth", "Cancer-treatment device"),
        "SEDG": ("Growth", "Solar inverters"), "NTRA": ("Growth", "Genetic testing"), "AMD": ("Growth", "CPUs taking share from Intel"),
        "VIPS": ("Turnaround", "China discount e-commerce profits"), "YETI": ("Growth", "Coolers & drinkware (2018 IPO)"),
        "COUP": ("Growth", "Spend-management software"), "NEO": ("Growth", "Cancer genetic testing lab"),
        "EHTH": ("Growth", "Online Medicare insurance broker"), "AVLR": ("Growth", "Sales-tax software"),
        "TTD": ("Growth", "Ad-buying software"), "GH": ("Growth", "Blood-based cancer tests (2018 IPO)"),
        "EDU": ("Growth", "China after-school education"), "OLED": ("Growth", "OLED display materials"),
        "RNG": ("Growth", "Cloud phone systems"), "PAYC": ("Growth", "Payroll software"), "GDS": ("Growth", "China data centers"),
        "PODD": ("Growth", "Insulin pumps"), "MELI": ("Growth", "Latin America e-commerce & payments"),
        "STNE": ("Growth", "Brazil payments (2018 IPO)"), "SWCH": ("Growth", "Data centers"), "THC": ("Turnaround", "Hospital operator"),
        "LPSN": ("Growth", "Messaging & chatbot software"), "TPX": ("Turnaround", "Mattress maker turnaround"),
        "GNRC": ("Growth", "Home standby generators"), "OKTA": ("Growth", "Identity security software"), "PCTY": ("Growth", "Payroll software"),
        "ARWR": ("Biotech event", "RNAi drug pipeline"), "RETA": ("Biotech event", "Drug trial data"), "ITCI": ("Biotech event", "Caplyta approval"),
        "IOVA": ("Biotech event", "Cell therapy data"), "MRTX": ("Biotech event", "KRAS drug data"), "DCPH": ("Biotech event", "Cancer drug data"),
        "ACAD": ("Biotech event", "Drug trial data"), "QURE": ("Biotech event", "Gene therapy data"), "CRSP": ("Biotech event", "Gene editing data"),
        "GLPG": ("Biotech event", "Gilead partnership"), "ASND": ("Biotech event", "Drug trial data"), "KPTI": ("Biotech event", "Drug approval"),
        "APLS": ("Biotech event", "Drug trial data"),
        "NVRO": ("Special situation", "Patent ruling, medtech rebound"), "CNNE": ("Special situation", "Holding company"),
        "CRUS": ("Cyclical", "Apple audio chips"), "LRCX": ("Cyclical", "Chip equipment"), "TER": ("Cyclical", "Chip test equipment"),
        "AMKR": ("Cyclical", "Chip packaging"), "BLDR": ("Cyclical", "Building products"), "BLD": ("Cyclical", "Insulation installer"),
        "IBP": ("Cyclical", "Insulation installer"), "SKY": ("Cyclical", "Manufactured homes"), "WGO": ("Cyclical", "RVs"),
        "INT": ("Cyclical", "Fuel distribution"), "ELP": ("Foreign macro", "Brazil utility"),
    },
    "2020": {
        "W": ("Growth", "Online furniture (stay-at-home)"), "FVRR": ("Growth", "Freelance marketplace"), "FTCH": ("Growth", "Luxury e-commerce"),
        "GTLS": ("Growth", "Hydrogen & LNG equipment"), "CVNA": ("Growth", "Online used cars"), "TSLA": ("Growth", "EVs"),
        "CRNC": ("Growth", "In-car voice AI (2019 spin-off)"), "UPWK": ("Growth", "Freelance marketplace"), "RVLV": ("Growth", "Online fashion"),
        "ETSY": ("Growth", "Online marketplace (stay-at-home)"), "MSTR": ("Crypto proxy", "Bitcoin treasury"), "RUN": ("Growth", "Home solar"),
        "CROX": ("Turnaround", "Brand comeback"), "PINS": ("Growth", "Social media (2019 IPO)"), "ENPH": ("Growth", "Solar microinverters"),
        "SE": ("Growth", "SE Asia e-commerce & games"), "SQ": ("Growth", "Payments & Cash App"), "RDFN": ("Growth", "Online real-estate broker"),
        "TWST": ("Growth", "Synthetic DNA"), "BILI": ("Growth", "China video platform"), "SPWR": ("Turnaround", "Solar panels, spin-off & restructuring"),
        "SNAP": ("Growth", "Social media"), "SWAV": ("Growth", "Heart-device medtech (2019 IPO)"), "PTON": ("Growth", "Home fitness (stay-at-home)"),
        "INSP": ("Growth", "Sleep-apnea implant"), "SPT": ("Growth", "Social-media software (2019 IPO)"),
        "SONO": ("Turnaround", "Home speakers, margins"), "ZG": ("Growth", "Online real estate (Zillow)"), "APPN": ("Growth", "Low-code software"),
        "YETI": ("Growth", "Coolers & drinkware"), "MAXR": ("Turnaround", "Satellite imagery"),
        "NVAX": ("Biotech event", "Covid vaccine"), "MRNA": ("Biotech event", "Covid vaccine"), "TGTX": ("Biotech event", "Drug trial data"),
        "NTLA": ("Biotech event", "Gene editing data"), "BEAM": ("Biotech event", "Gene editing"),
        "PENN": ("Recovery", "Casinos + Barstool sports betting"), "SGMS": ("Recovery", "Casino equipment"), "BYD": ("Recovery", "Casinos"),
        "CPRI": ("Recovery", "Luxury apparel"), "CAR": ("Recovery", "Rental cars"), "SEAS": ("Recovery", "Theme parks"),
        "CVET": ("Recovery", "Animal-health distribution"), "ACHC": ("Recovery", "Behavioral-health hospitals"),
        "DQ": ("Cyclical", "Solar polysilicon"), "FCX": ("Cyclical", "Copper"), "AA": ("Cyclical", "Aluminum"), "PDCE": ("Cyclical", "Oil & gas"),
        "TPL": ("Cyclical", "Permian land & royalties"), "DOOO": ("Cyclical", "Powersports boom"), "RH": ("Cyclical", "Luxury furniture (housing boom)"),
        "WSM": ("Cyclical", "Home furnishings (housing boom)"), "SNBR": ("Cyclical", "Beds (housing boom)"), "LAD": ("Cyclical", "Car dealers"),
        "RCII": ("Cyclical", "Rent-to-own"), "DY": ("Cyclical", "Telecom contractor"), "WCC": ("Cyclical", "Electrical distribution + merger"),
        "VIAC": ("Special situation", "Streaming hype, Archegos squeeze"), "DDD": ("Speculative", "3D printing hype"),
    },
    "2022": {
        "SMCI": ("Growth", "AI servers"), "NVDA": ("Growth", "AI chips"), "ANF": ("Turnaround", "Apparel retail turnaround"),
        "VRT": ("Growth", "AI data-center power & cooling"), "ACLS": ("Growth", "Chip equipment for power chips"), "META": ("Growth", "Ads + cost discipline"),
        "ELF": ("Growth", "Cosmetics"), "RELY": ("Growth", "Money-transfer app"), "ONTO": ("Growth", "Chip equipment (advanced packaging)"),
        "RMBS": ("Growth", "Memory-interface chips"), "FTAI": ("Growth", "Jet-engine aftermarket"), "PLTR": ("Growth", "AI software"),
        "GSHD": ("Growth", "Insurance agency franchise"), "FICO": ("Growth", "Credit scores (pricing power)"), "APP": ("Growth", "AI ad-tech"),
        "DKNG": ("Growth", "Online sports betting"), "IOT": ("Growth", "IoT software"), "AVGO": ("Growth", "AI custom chips + VMware"),
        "SHOP": ("Growth", "E-commerce software"), "EXAS": ("Growth", "Cancer screening tests"), "FSLY": ("Growth", "Edge cloud (beaten-down rebound)"),
        "MDB": ("Growth", "Database software"), "BRBR": ("Growth", "Protein shakes"), "CRS": ("Turnaround", "Aerospace alloys, earnings inflection"),
        "NVO": ("Growth", "GLP-1 obesity drugs"), "PDD": ("Growth", "E-commerce (Temu)"), "STVN": ("Growth", "Drug vials (GLP-1 demand)"),
        "IMVT": ("Biotech event", "Drug trial data"), "IMGN": ("Biotech event", "Drug approval, then buyout"), "BBIO": ("Biotech event", "Drug trial data"),
        "MDGL": ("Biotech event", "Liver drug data"), "IONQ": ("Speculative", "Quantum computing"), "AI": ("Speculative", "AI software, slow growth"),
        "TDW": ("Cyclical", "Offshore vessels"), "OII": ("Cyclical", "Offshore oil services"), "WFRD": ("Cyclical", "Oilfield services"),
        "FTI": ("Cyclical", "Offshore oil equipment"), "AROC": ("Cyclical", "Gas compression"), "LPG": ("Cyclical", "Gas shipping"),
        "PKX": ("Cyclical", "Steel + battery-materials hype"), "XPO": ("Cyclical", "LTL trucking (Yellow bankruptcy)"),
        "SAIA": ("Cyclical", "LTL trucking (Yellow bankruptcy)"), "LRCX": ("Cyclical", "Chip equipment"), "AMAT": ("Cyclical", "Chip equipment"),
        "MHO": ("Cyclical", "Homebuilder"), "ESAB": ("Cyclical", "Welding equipment (2022 spin-off)"), "PRG": ("Cyclical", "Lease-to-own"),
        "JBL": ("Mature re-rating", "Contract manufacturing (AI)"), "DELL": ("Mature re-rating", "PCs / AI servers"),
        "ADBE": ("Mature re-rating", "Software, AI hype"), "APG": ("Mature re-rating", "Fire-safety services"),
        "EDU": ("Recovery", "China education rebound"), "VIPS": ("Recovery", "China e-commerce rebound"), "SKYW": ("Recovery", "Regional airline"),
        "RCL": ("Recovery", "Cruise line"), "VIST": ("Foreign macro", "Argentina shale (Milei reforms)"), "YPF": ("Foreign macro", "Argentina energy (Milei reforms)"),
        "GE": ("Special situation", "Break-up into 3 companies"), "SPLK": ("Special situation", "Cisco buyout"), "SHC": ("Special situation", "Sterilization services"),
    },
}

scr = json.load(open("cycles_screen.json"))
an = json.load(open("cycles_analysis.json"))
all_rows, lists, summary = [], {}, {}
for k in ("2018", "2020", "2022"):
    c = an[k]["cycle"]
    spy, qqq = an[k]["index"]
    srow = {r["ticker"]: r for r in scr[k]["rows"]}
    rows = [r for r in an[k]["rows"] if r["ticker"] not in DROP]
    missing = [r["ticker"] for r in rows if r["ticker"] not in TAGS[k]]
    assert not missing, (k, missing)
    rows.sort(key=lambda r: -srow[r["ticker"]]["ret_12m"])
    top = [r for r in rows if TAGS[k][r["ticker"]][0] in GROWTH][:25]
    lists[k] = [r["ticker"] for r in top]
    low = dt.date.fromisoformat(c["low"])
    for r in rows:
        s, (cat, theme) = srow[r["ticker"]], TAGS[k][r["ticker"]]
        ld = s.get("list_date")
        all_rows.append({
            "cycle": k, "index_low": c["low"], "ticker": r["ticker"], "company": s["name"], "category": cat, "theme": theme,
            "growth_rank": lists[k].index(r["ticker"]) + 1 if r["ticker"] in lists[k] else "",
            "ret_12m_from_index_low_pct": s["ret_12m"], "ret_24m_from_index_low_pct": s["ret_24m"],
            "vs_spy_12m_pts": round(s["ret_12m"] - spy["ret_12m"], 1),
            "mktcap_at_index_low_b": s["cap_at_low_b"],
            "years_listed_at_low": round((low - dt.date.fromisoformat(ld)).days / 365.25, 1) if ld else "",
            "prior_high_date": r["prior_high_date"], "bear_drawdown_pct": r["bear_drawdown_pct"],
            "stock_low_date": r["low_date"], "first_52w_high_after_low": r["first_52w_high_date"],
            "pct_off_low_at_first_52w_high": r["pct_off_low_at_52w_high"],
            "vol_on_low_x_50d_avg": r.get("low_vol_vs_50d"), "vol_on_first_52w_high_x_50d_avg": r.get("high_vol_vs_50d"),
            "rs_line_first_52w_high": r["rs_new_high_date"], "rs_line_led_price": r["rs_led_price"],
            "run_peak_date": r["run_peak_date"], "low_to_peak_pct": r["low_to_peak_pct"],
            "pullback1": f"{spy['corr1']['start']} to {spy['corr1']['end']} (SPY {spy['corr1']['pct']}%)", "chg_in_pullback1_pct": r.get("corr1_pct"),
            "pullback2": f"{spy['corr2']['start']} to {spy['corr2']['end']} (SPY {spy['corr2']['pct']}%)" if "corr2" in spy else "",
            "chg_in_pullback2_pct": r.get("corr2_pct"),
        })

    g = [x for x in all_rows if x["cycle"] == k and x["growth_rank"]]
    n = len(g)
    off = [(dt.date.fromisoformat(x["stock_low_date"]) - low).days for x in g]
    summary[k] = {
        "index_low": c["low"], "spy_first_new_high": spy["first_52w_high_date"], "qqq_first_new_high": qqq["first_52w_high_date"],
        "spy_12m": spy["ret_12m"], "qqq_12m": qqq["ret_12m"],
        "median_bear_drawdown": st.median(x["bear_drawdown_pct"] for x in g if x["bear_drawdown_pct"] is not None),
        "low_2wk_plus_before_index": sum(o < -14 for o in off), "low_within_2wk": sum(-14 <= o <= 14 for o in off),
        "low_2wk_plus_after": sum(o > 14 for o in off),
        "new_high_before_spy": sum(1 for x in g if x["first_52w_high_after_low"] and x["first_52w_high_after_low"] < spy["first_52w_high_date"]),
        "rs_led_price": sum(1 for x in g if x["rs_line_led_price"] == "Yes"),
        "median_pct_off_low_at_new_high": st.median(x["pct_off_low_at_first_52w_high"] for x in g if x["pct_off_low_at_first_52w_high"] is not None),
        "heavy_volume_at_new_high": sum(1 for x in g if (x["vol_on_first_52w_high_x_50d_avg"] or 0) >= 1.4),
        "listed_under_5y": sum(1 for x in g if x["years_listed_at_low"] != "" and x["years_listed_at_low"] < 5),
        "median_cap_b": st.median(x["mktcap_at_index_low_b"] for x in g),
        "pullback1": an[k]["index"][0]["corr1"], "median_in_pullback1": st.median(x["chg_in_pullback1_pct"] for x in g if x["chg_in_pullback1_pct"] is not None),
        "n": n,
    }

with open("../bear_market_leaders.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(all_rows[0]))
    w.writeheader()
    w.writerows(all_rows)
json.dump({"lists": lists, "summary": summary}, open("cycles_lists.json", "w"), indent=1)

by = {(x["cycle"], x["ticker"]): x for x in all_rows}
for k in lists:
    print(f"\n=== {k} cycle (index low {summary[k]['index_low']}; SPY 12m {summary[k]['spy_12m']}%, QQQ {summary[k]['qqq_12m']}%)")
    for i, t in enumerate(lists[k], 1):
        x = by[(k, t)]
        print(f"{i:2} {t:5} {x['ret_12m_from_index_low_pct']:7}% 24m {str(x['ret_24m_from_index_low_pct']):>7}% | {x['category'][:4]} {x['theme'][:36]:36} | low {x['stock_low_date']} | 52wH {x['first_52w_high_after_low']} (+{x['pct_off_low_at_first_52w_high']}) vol {x['vol_on_first_52w_high_x_50d_avg']} | RS {x['rs_line_led_price']} | yrs {x['years_listed_at_low']} cap {x['mktcap_at_index_low_b']}")
    print({kk: vv for kk, vv in summary[k].items()})
