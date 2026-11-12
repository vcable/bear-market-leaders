"""Write one data file per cycle for the Bear Market Leaders page: daily bars, leaders, new issues, index events."""
import csv
import json
import os
import statistics as st
from cycles import add_months
from cycles_analyze import series, close_on
from analyze import pct

OUT = os.path.join("..", "site", "data")
os.makedirs(OUT, exist_ok=True)

NAMES = {
    # leaders
    "ROKU": "Roku", "SE": "Sea Limited", "SHOP": "Shopify", "CVNA": "Carvana", "SNAP": "Snap", "LSCC": "Lattice Semiconductor",
    "NVCR": "NovoCure", "SEDG": "SolarEdge", "NTRA": "Natera", "AMD": "Advanced Micro Devices", "VIPS": "Vipshop",
    "YETI": "YETI Holdings", "COUP": "Coupa Software", "NEO": "NeoGenomics", "EHTH": "eHealth", "AVLR": "Avalara",
    "TTD": "The Trade Desk", "GH": "Guardant Health", "EDU": "New Oriental Education", "OLED": "Universal Display",
    "RNG": "RingCentral", "PAYC": "Paycom", "GDS": "GDS Holdings", "PODD": "Insulet", "MELI": "MercadoLibre",
    "W": "Wayfair", "FVRR": "Fiverr", "FTCH": "Farfetch", "GTLS": "Chart Industries", "TSLA": "Tesla", "CRNC": "Cerence",
    "UPWK": "Upwork", "RVLV": "Revolve", "ETSY": "Etsy", "MSTR": "MicroStrategy", "RUN": "Sunrun", "CROX": "Crocs",
    "PINS": "Pinterest", "ENPH": "Enphase Energy", "SQ": "Square (Block)", "RDFN": "Redfin", "TWST": "Twist Bioscience",
    "BILI": "Bilibili", "SPWR": "SunPower", "SWAV": "ShockWave Medical", "PTON": "Peloton", "INSP": "Inspire Medical Systems",
    "SMCI": "Super Micro Computer", "NVDA": "Nvidia", "ANF": "Abercrombie & Fitch", "VRT": "Vertiv", "ACLS": "Axcelis Technologies",
    "META": "Meta Platforms", "ELF": "e.l.f. Beauty", "RELY": "Remitly", "ONTO": "Onto Innovation", "RMBS": "Rambus",
    "FTAI": "FTAI Aviation", "PLTR": "Palantir", "GSHD": "Goosehead Insurance", "FICO": "Fair Isaac", "APP": "AppLovin",
    "DKNG": "DraftKings", "IOT": "Samsara", "AVGO": "Broadcom", "EXAS": "Exact Sciences", "FSLY": "Fastly", "MDB": "MongoDB",
    "BRBR": "BellRing Brands", "CRS": "Carpenter Technology", "NVO": "Novo Nordisk",
    # new issues
    "BILL": "Bill.com", "PLMR": "Palomar Holdings", "ZM": "Zoom Video", "TXG": "10x Genomics", "INMD": "InMode",
    "DDOG": "Datadog", "DAO": "Youdao", "OCFT": "OneConnect Financial", "NOVA": "Sunnova Energy", "NET": "Cloudflare",
    "DT": "Dynatrace", "PGNY": "Progyny", "BRP": "BRP Group", "CRWD": "CrowdStrike", "PING": "Ping Identity",
    "BYND": "Beyond Meat", "CHWY": "Chewy", "TW": "Tradeweb Markets", "PHR": "Phreesia",
    "UPST": "Upstart", "ASAN": "Asana", "LPRO": "Open Lending", "FOUR": "Shift4 Payments", "MEG": "Montrose Environmental",
    "NARI": "Inari Medical", "U": "Unity Software", "CRSR": "Corsair Gaming", "BSY": "Bentley Systems",
    "ALGM": "Allegro MicroSystems", "XPEV": "XPeng", "LI": "Li Auto", "ACCD": "Accolade", "KC": "Kingsoft Cloud",
    "NGMS": "NeoGames", "OSH": "Oak Street Health", "DADA": "Dada Nexus", "LMND": "Lemonade", "PUBM": "PubMatic",
    "ZI": "ZoomInfo", "GAN": "GAN Limited", "SNOW": "Snowflake", "ABNB": "Airbnb",
    "ARM": "Arm Holdings", "CAVA": "CAVA Group", "NXT": "Nextracker", "SN": "SharkNinja", "SKWD": "Skyward Specialty Insurance",
    "ATAT": "Atour Lifestyle", "MBLY": "Mobileye", "BIRK": "Birkenstock", "CART": "Instacart (Maplebear)", "KVYO": "Klaviyo",
}


def num(v):
    return None if v in ("", None) else float(v)


def rnd(v):
    return round(v, 2) if v >= 10 else round(v, 4)


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(st.median(xs), 1) if xs else None


lists = json.load(open("cycles_lists.json"))
an = json.load(open("cycles_analysis.json"))
ipo = json.load(open("cycles_ipos_analysis.json"))
csvrows = {(r["cycle"], r["ticker"]): r for r in csv.DictReader(open("../bear_market_leaders.csv", encoding="utf-8"))}

for k in ("2018", "2020", "2022"):
    c = an[k]["cycle"]
    spy_i, qqq_i = an[k]["index"]
    arows = {r["ticker"]: r for r in an[k]["rows"]}
    irows = ipo[k]["rows"]
    end = max([c["m24"]] + [add_months(r["first_day"], 24) for r in irows])
    spy_s = series("SPY", c["chart_start"], end)
    dates = [d for d, _ in spy_s]
    end = dates[-1]
    pos = {d: i for i, d in enumerate(dates)}
    spy = dict(spy_s)

    leaders = []
    for rank, t in enumerate(lists["lists"][k], 1):
        x, a = csvrows[(k, t)], arows[t]
        leaders.append({
            "rank": rank, "ticker": t, "company": NAMES[t], "category": x["category"], "theme": x["theme"],
            "ret": num(x["ret_12m_from_index_low_pct"]), "ret24": num(x["ret_24m_from_index_low_pct"]),
            "vs_spy": num(x["vs_spy_12m_pts"]), "cap_b": num(x["mktcap_at_index_low_b"]),
            "years_listed": num(x["years_listed_at_low"]),
            "prior_high_date": a["prior_high_date"], "drop": a["bear_drawdown_pct"],
            "low_date": a["low_date"], "low_vol": a.get("low_vol_vs_50d"),
            "hi_date": a["first_52w_high_date"], "hi_pct": a["pct_off_low_at_52w_high"], "hi_vol": a.get("high_vol_vs_50d"),
            "rs_date": a["rs_new_high_date"], "rs_led": a["rs_led_price"],
            "peak_date": a["run_peak_date"], "low_to_peak": a["low_to_peak_pct"],
            "corr1": a.get("corr1_pct"), "corr2": a.get("corr2_pct"),
            "start": c["chart_start"], "end": c["m24"],
        })

    ipos = []
    for rank, r in enumerate(irows, 1):
        t, f = r["ticker"], r["first_day"]
        s12 = add_months(f, 12)
        spy12 = pct(close_on(spy_s, f), close_on(spy_s, s12))
        ipos.append({
            "rank": rank, "ticker": t, "company": NAMES[t], "category": "Growth", "theme": r["theme"], "how": r["how"],
            "ret": r["ret_first_year_pct"], "ret24": r["ret_24m_pct"],
            "vs_spy": round(r["ret_first_year_pct"] - spy12, 1) if spy12 is not None else None, "cap_b": r["cap_b"],
            "first_day": f, "first_day_chg": r["first_day_chg_pct"], "spy_at_ipo": r["spy_vs_low_at_ipo_pct"],
            "base_high_date": r["base_high_date"], "high_vs_first": r["pct_high_vs_first_close"],
            "drop": r["base_depth_pct"], "base_weeks": r["base_weeks"],
            "low_date": r["low_date"], "low_vs_first": r["pct_low_vs_first_close"], "low_vol": r.get("low_vol_vs_50d"),
            "hi_date": r["breakout_date"], "hi_pct": r["pct_off_low_at_breakout"], "hi_vol": r.get("high_vol_vs_50d"),
            "rs_date": r["rs_new_high_date"], "rs_led": r["rs_led_price"],
            "peak_date": r["run_peak_date"], "low_to_peak": r["low_to_peak_pct"],
            "corr1": r.get("corr1_pct"), "corr2": r.get("corr2_pct"),
            "start": f, "end": min(add_months(f, 24), end),
        })

    ser = {}
    for t, start, stop in ([("SPY", c["chart_start"], end), ("QQQ", c["chart_start"], end)]
                           + [(l["ticker"], c["chart_start"], c["m24"]) for l in leaders]
                           + [(r["ticker"], c["low"], add_months(c["m12"], 25)) for r in irows]):
        if t in ser:
            continue
        cl = [(d, v) for d, v in series(t, start, stop) if d in pos]
        vo = dict(series(t, start, stop, "v"))
        if not cl:
            continue
        o, last = pos[cl[0][0]], pos[cl[-1][0]]
        cmap = dict(cl)
        ser[t] = {"o": o,
                  "c": [rnd(cmap[dates[i]]) if dates[i] in cmap else None for i in range(o, last + 1)]}
        if t not in ("SPY", "QQQ"):
            ser[t]["v"] = [int(vo[dates[i]]) if vo.get(dates[i]) else None for i in range(o, last + 1)]

    events = [
        {"id": "spy_peak", "label": "SPY peak", "start": c["peak"], "end": None, "spy_pct": None},
        {"id": "spy_low", "label": "SPY low", "start": spy_i["low_date"], "end": None, "spy_pct": spy_i["bear_drawdown_pct"]},
        {"id": "qqq_low", "label": "QQQ low", "start": qqq_i["low_date"], "end": None, "spy_pct": None},
        {"id": "qqq_52w", "label": "QQQ new high", "start": qqq_i["first_52w_high_date"], "end": None, "spy_pct": None},
        {"id": "spy_52w", "label": "SPY new high", "start": spy_i["first_52w_high_date"], "end": None, "spy_pct": None},
    ]
    for n in (1, 2):
        cr = spy_i.get(f"corr{n}")
        if cr:
            events.append({"id": f"corr{n}", "label": "SPY pullback", "start": cr["start"], "end": cr["end"], "spy_pct": cr["pct"]})

    sm = lists["summary"][k]
    with_bo = [r for r in ipos if r["hi_date"]]
    summary = {
        "leaders": sm,
        "ipos": {
            "n": len(ipos), "median_first_year": med(r["ret"] for r in ipos),
            "broke_out": len(with_bo), "median_base_depth": med(r["drop"] for r in with_bo),
            "median_base_weeks": med(r["base_weeks"] for r in with_bo),
            "heavy_volume_breakout": sum(1 for r in with_bo if (r["hi_vol"] or 0) >= 1.4),
            "listed_before_spy_high": sum(1 for r in ipos if r["first_day"] < spy_i["first_52w_high_date"]),
            "breakout_before_spy_high": sum(1 for r in with_bo if r["hi_date"] < spy_i["first_52w_high_date"]),
        },
    }
    doc = {
        "key": k, "cycle": {kk: c[kk] for kk in ("peak", "low", "m12", "m24", "chart_start")},
        "index": {"spy": spy_i, "qqq": qqq_i}, "summary": summary, "events": events,
        "dates": dates, "series": ser, "leaders": leaders, "ipos": ipos,
    }
    p = os.path.join(OUT, f"{k}.json")
    json.dump(doc, open(p, "w"), separators=(",", ":"))
    print(k, "dates", len(dates), dates[0], dates[-1], "| leaders", len(leaders), "ipos", len(ipos),
          "| series", len(ser), "|", round(os.path.getsize(p) / 1e6, 2), "MB")
    print("   ipo summary", summary["ipos"])
