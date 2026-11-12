"""Daily-bar analysis of each cycle's new issues: the post-IPO base, the breakout from it, RS line, volume, market context."""
import datetime as dt
import json
from cycles import add_months, day
from cycles_analyze import series, close_on, vol_ratio
from analyze import pct

TOP_N = 25
MIN_BASE = 15  # sessions without a new closing high before a breakout counts (three weeks)
# Growth-company new listings that passed the screen (cap, liquidity, a full year of trading) with a positive first year.
# Left out: renamed or relisted companies, biotechs trading on trial data, cyclicals, banks/insurers/REITs that are not
# growth stories, share-class and holding-company listings, and spin-offs of mature industrial businesses.
# ticker: (theme, how it listed)
NEW_ISSUES = {
    "2018": {
        "BILL": ("Payments software for small businesses", "IPO"), "PTON": ("Connected fitness", "IPO"),
        "PLMR": ("Earthquake & specialty insurance", "IPO"), "ZM": ("Video meetings", "IPO"),
        "TXG": ("Single-cell genomics tools", "IPO"), "INMD": ("Aesthetic medical devices", "IPO"),
        "DDOG": ("Cloud monitoring software", "IPO"), "DAO": ("China online education", "IPO"),
        "OCFT": ("China bank-tech software", "IPO"), "NOVA": ("Home solar service", "IPO"),
        "NET": ("Edge network & security", "IPO"), "DT": ("Software monitoring", "IPO"),
        "PGNY": ("Fertility benefits", "IPO"), "FSLY": ("Edge cloud", "IPO"),
        "BRP": ("Insurance distribution", "IPO"), "CRWD": ("Endpoint security software", "IPO"),
        "PING": ("Identity security software", "IPO"), "BYND": ("Plant-based meat", "IPO"),
        "CHWY": ("Online pet supplies", "IPO"), "SWAV": ("Heart-device medtech", "IPO"),
        "TW": ("Electronic bond trading", "IPO"), "PHR": ("Patient-intake software", "IPO"),
    },
    "2020": {
        "UPST": ("AI lending platform", "IPO"), "ASAN": ("Work-management software", "Direct listing"),
        "DKNG": ("Online sports betting", "SPAC merger"), "LPRO": ("Auto-loan underwriting software", "SPAC merger"),
        "FOUR": ("Payment processing", "IPO"), "PLTR": ("Data-analytics software", "Direct listing"),
        "MEG": ("Environmental testing", "IPO"), "NARI": ("Clot-removal devices", "IPO"),
        "U": ("Game-engine software", "IPO"), "CRSR": ("Gaming PC gear", "IPO"),
        "BSY": ("Infrastructure design software", "IPO"), "ALGM": ("Auto & industrial sensor chips", "IPO"),
        "XPEV": ("China EVs", "IPO"), "LI": ("China EVs", "IPO"), "ACCD": ("Healthcare navigation", "IPO"),
        "KC": ("China cloud", "IPO"), "NGMS": ("Online lottery software", "IPO"),
        "OSH": ("Primary-care clinics for seniors", "IPO"), "DADA": ("China on-demand delivery", "IPO"),
        "LMND": ("Insurance app", "IPO"), "PUBM": ("Ad-tech for publishers", "IPO"),
        "ZI": ("Sales-intelligence software", "IPO"), "GAN": ("Online casino software", "IPO"),
        "SNOW": ("Cloud data warehouse", "IPO"), "ABNB": ("Home-sharing marketplace", "IPO"),
    },
    "2022": {
        "ARM": ("Chip designs (AI, phones)", "IPO"), "CAVA": ("Mediterranean fast-casual", "IPO"),
        "NXT": ("Solar trackers", "IPO"), "SN": ("Home appliances", "Spin-off"),
        "SKWD": ("Specialty insurance", "IPO"), "ATAT": ("China midscale hotels", "IPO"),
        "MBLY": ("Driver-assist chips", "IPO"), "BIRK": ("Footwear brand", "IPO"),
        "CART": ("Grocery delivery", "IPO"), "KVYO": ("Marketing software", "IPO"),
    },
}


def ipo_vol_ratio(vol, i):
    """Volume against the average of up to 50 prior sessions, leaving out the two IPO days; needs 10."""
    if i is None:
        return None
    prior = [v for _, v in vol[max(2, i - 50):i] if v]
    if len(prior) < 10 or not vol[i][1]:
        return None
    return round(vol[i][1] / (sum(prior) / len(prior)), 2)


def analyze(t, first, c, spy, corr):
    end = add_months(first, 24)
    s = [x for x in series(t, c["low"], add_months(c["m12"], 25)) if x[0] <= end]
    vol = [x for x in series(t, c["low"], add_months(c["m12"], 25), "v") if x[0] <= end]
    if len(vol) != len(s):
        vol = None
    r = {"ticker": t, "first_day": first, "first_close": s[0][1]}
    m12 = add_months(first, 12)
    r["ret_first_year_pct"] = pct(s[0][1], close_on(s, m12))
    r["ret_24m_pct"] = pct(s[0][1], s[-1][1]) if s[-1][0] >= add_months(first, 23) else None
    # First base breakout: the first close above every earlier close that comes at least MIN_BASE sessions
    # after the previous closing high. The base runs from that high to the breakout; its low is the lowest close in between.
    bo, bh, top = None, 0, s[0][1]
    for i in range(1, len(s)):
        if s[i][1] > top:
            if i - bh >= MIN_BASE:
                bo = i
                break
            bh, top = i, s[i][1]
    if bo is not None:
        lo = min(range(bh, bo), key=lambda i: s[i][1])
    else:
        bh = max(range(min(len(s), 127)), key=lambda i: s[i][1])
        lo = min(range(bh, min(len(s), 253)), key=lambda i: s[i][1])
    r["base_high_date"], r["low_date"] = s[bh][0], s[lo][0]
    r["base_depth_pct"] = pct(s[bh][1], s[lo][1])
    r["pct_low_vs_first_close"] = pct(s[0][1], s[lo][1])
    r["pct_high_vs_first_close"] = pct(s[0][1], s[bh][1])
    r["breakout_date"] = s[bo][0] if bo is not None else None
    r["pct_off_low_at_breakout"] = pct(s[lo][1], s[bo][1]) if bo is not None else None
    r["base_weeks"] = round((bo - bh) / 5, 1) if bo is not None else None
    r["sessions_to_breakout"] = bo
    rs = [(d, v / spy[d]) for d, v in s if d in spy]
    rlo = next(i for i, (d, _) in enumerate(rs) if d >= s[lo][0])
    rb = next((i for i in range(rlo + 1, len(rs)) if rs[i][1] > max(v for _, v in rs[:i])), None)
    r["rs_new_high_date"] = rs[rb][0] if rb is not None else None
    r["rs_led_price"] = "Yes" if (r["rs_new_high_date"] and r["breakout_date"] and r["rs_new_high_date"] < r["breakout_date"]) else "No"
    if vol:
        r["low_vol_vs_50d"] = ipo_vol_ratio(vol, lo) if lo >= 12 else None
        r["high_vol_vs_50d"] = ipo_vol_ratio(vol, bo)
        r["first_day_volume"] = int(vol[0][1])
    r["first_day_chg_pct"] = None  # filled from the opening print in cycles_export
    peak = max(range(len(s)), key=lambda i: s[i][1])
    r["run_peak_date"], r["low_to_peak_pct"] = s[peak][0], pct(s[lo][1], s[peak][1])
    sl = close_on(list(spy.items()), c["low"])
    r["spy_vs_low_at_ipo_pct"] = pct(sl, close_on(list(spy.items()), first))
    for k, (_, a, z) in enumerate(corr, 1):
        r[f"corr{k}_pct"] = pct(close_on(s, a), close_on(s, z)) if s[0][0] <= a and s[-1][0] >= z else None
    return r


if __name__ == "__main__":
    from cycles_analyze import corrections
    scr = json.load(open("cycles_ipos_screen.json"))
    out = {}
    for k, v in scr.items():
        c = v["cycle"]
        spy_s = series("SPY", c["chart_start"], add_months(c["m12"], 25))
        spy = dict(spy_s)
        corr = corrections(spy_s, c["low"], c["m24"])
        rows = []
        pick = [x for x in v["rows"] if x["ticker"] in NEW_ISSUES[k]][:TOP_N]
        missing = set(NEW_ISSUES[k]) - {x["ticker"] for x in v["rows"]}
        assert not missing, (k, missing)
        for x in pick:
            r = analyze(x["ticker"], x["first_day"], c, spy, corr)
            r["first_day_chg_pct"] = pct(x["first_open"], x["first_close"])
            r["theme"], r["how"] = NEW_ISSUES[k][x["ticker"]]
            r["cap_b"], r["sic"] = x["cap_b"], x["sic"]
            rows.append(r)
        out[k] = {"cycle": c, "rows": rows}
        print(f"\n== {k}")
        for r in rows:
            print(f"{r['ticker']:6} first {r['first_day']} yr {r['ret_first_year_pct']:7} | base hi {r['base_high_date']} low {r['low_date']} depth {r['base_depth_pct']} | BO {r['breakout_date']} ({r['base_weeks']} wk, vol {r.get('high_vol_vs_50d')}) | RS {r['rs_new_high_date']} led {r['rs_led_price']} | SPY +{r['spy_vs_low_at_ipo_pct']}% at IPO")
    json.dump(out, open("cycles_ipos_analysis.json", "w"), indent=1)
