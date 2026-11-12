"""Daily-bar analysis of each cycle's top 60: run-start timing, RS line, volume, behaviour in index pullbacks."""
import datetime as dt
import json
from concurrent.futures import ThreadPoolExecutor
from fetch import bars
from analyze import first_52w_high, drawdown_window, pct

TOP_N = 60
# symbols that belonged to another security inside a cycle's chart window
PREDECESSOR = {"META": ("FB", "2022-06-09")}
FIRST_VALID = {"SE": "2017-10-20"}  # Spectra Energy used SE before Sea's IPO


def day(ts):
    return dt.datetime.fromtimestamp(ts / 1000 + 12 * 3600, dt.timezone.utc).date().isoformat()


def raw(t, start, end, field):
    return [(day(b["t"]), b[field]) for b in bars(t, start, end) if field in b]


def series(t, start, end, field="c"):
    s = raw(t, start, end, field)
    if t in PREDECESSOR and start < PREDECESSOR[t][1]:
        old, switch = PREDECESSOR[t]
        s = [x for x in raw(old, start, end, field) if x[0] < switch] + [x for x in s if x[0] >= switch]
    if t in FIRST_VALID:
        s = [x for x in s if x[0] >= FIRST_VALID[t]]
    return s


def suspicious(s):
    """Gaps of more than a week or one-day moves past 2.5x / 0.4x: signs of a reused ticker."""
    ds = [dt.date.fromisoformat(d) for d, _ in s]
    gaps = [(s[i - 1][0], s[i][0]) for i in range(1, len(s)) if (ds[i] - ds[i - 1]).days > 6]
    jumps = [(s[i][0], round(s[i][1] / s[i - 1][1], 2)) for i in range(1, len(s))
             if s[i][1] / s[i - 1][1] > 2.5 or s[i][1] / s[i - 1][1] < 0.4]
    return gaps, jumps


def close_on(s, date):
    v = None
    for d, c in s:
        if d > date:
            break
        v = c
    return v


def drawdowns(spy, start, end):
    """Every peak-to-trough SPY closing decline of 5% or more between start and end, as (pct, peak, trough)."""
    pts = [(d, c) for d, c in spy if start <= d <= end]
    out, peak, trough = [], pts[0], pts[0]
    for d, c in pts[1:]:
        if c > peak[1]:
            if trough[1] / peak[1] - 1 <= -0.05:
                out.append((trough[1] / peak[1] - 1, peak[0], trough[0]))
            peak = trough = (d, c)
        elif c < trough[1]:
            trough = (d, c)
    if trough[1] / peak[1] - 1 <= -0.05:
        out.append((trough[1] / peak[1] - 1, peak[0], trough[0]))
    return out


def corrections(spy, low, m24):
    """The two largest ordinary pullbacks (5-20%) in SPY between the low and +24 months, oldest first."""
    ordinary = [x for x in drawdowns(spy, low, m24) if x[0] > -0.20]
    return sorted(sorted(ordinary)[:2], key=lambda x: x[1])


def months_after(date, m):
    d = dt.date.fromisoformat(date)
    y, mo = divmod(d.month - 1 + m, 12)
    return dt.date(d.year + y, mo + 1, min(d.day, 28)).isoformat()


def vol_ratio(vol, i):
    prior = [v for _, v in vol[max(0, i - 50):i] if v]
    if i is None or len(prior) < 20 or not vol[i][1]:
        return None
    return round(vol[i][1] / (sum(prior) / len(prior)), 2)


def analyze(t, c, spy, corr, end):
    s = series(t, c["chart_start"], end)
    if len(s) < 150:
        return None
    vol = series(t, c["chart_start"], end, "v")
    r = {"ticker": t}
    r["ret_12m"] = pct(close_on(s, c["low"]), close_on(s, c["m12"]))
    r["ret_24m"] = pct(close_on(s, c["low"]), close_on(s, c["m24"])) if s[-1][0] >= c["m24"] else None
    idx = [i for i, (d, _) in enumerate(s) if c["low"] <= d <= c["m24"]]
    pk = max(idx, key=lambda i: s[i][1])
    # the stock's own low: between the index peak and six months after the index low
    lo_end = months_after(c["low"], 6)
    lo_c = [i for i, (d, _) in enumerate(s) if c["peak"] <= d <= lo_end and i <= pk]
    lo = min(lo_c, key=lambda i: s[i][1])
    prior = [i for i in range(lo)]
    hi = max(prior, key=lambda i: s[i][1]) if prior else None
    r["prior_high_date"] = s[hi][0] if hi is not None else None
    r["bear_drawdown_pct"] = pct(s[hi][1], s[lo][1]) if hi is not None else None
    r["low_date"], r["run_peak_date"] = s[lo][0], s[pk][0]
    r["low_to_peak_pct"] = pct(s[lo][1], s[pk][1])
    b = first_52w_high(s, lo)
    r["first_52w_high_date"] = s[b][0] if b is not None else None
    r["pct_off_low_at_52w_high"] = pct(s[lo][1], s[b][1]) if b is not None else None
    rs = [(d, v / spy[d]) for d, v in s if d in spy]
    rs_lo = next(i for i, (d, _) in enumerate(rs) if d >= s[lo][0])
    rb = first_52w_high(rs, rs_lo)
    r["rs_new_high_date"] = rs[rb][0] if rb is not None else None
    r["rs_led_price"] = "Yes" if (r["rs_new_high_date"] and r["first_52w_high_date"]
                                  and r["rs_new_high_date"] < r["first_52w_high_date"]) else "No"
    if len(vol) == len(s):
        r["low_vol_vs_50d"] = vol_ratio(vol, lo)
        r["high_vol_vs_50d"] = vol_ratio(vol, b) if b is not None else None
    for k, (_, a, z) in enumerate(corr, 1):
        r[f"corr{k}_pct"] = pct(close_on(s, a), close_on(s, z))
    r["gaps"], r["jumps"] = suspicious(s)
    return r


def index_row(t, c, spy_corr, end):
    s = series(t, c["chart_start"], end)
    lo = min((i for i, (d, _) in enumerate(s) if c["peak"] <= d <= c["m12"]), key=lambda i: s[i][1])
    b = first_52w_high(s, lo)
    return {"ticker": t, "low_date": s[lo][0], "first_52w_high_date": s[b][0] if b is not None else None,
            "bear_drawdown_pct": pct(max(v for d, v in s if d <= s[lo][0]), s[lo][1]),
            "ret_12m": pct(close_on(s, c["low"]), close_on(s, c["m12"])),
            "ret_24m": pct(close_on(s, c["low"]), close_on(s, c["m24"]))}


if __name__ == "__main__":
    scr = json.load(open("cycles_screen.json"))
    out = {}
    for k, v in scr.items():
        c = v["cycle"]
        end = c["m24"]
        tick = [r["ticker"] for r in v["rows"][:TOP_N]]
        with ThreadPoolExecutor(8) as ex:
            list(ex.map(lambda t: (series(t, c["chart_start"], end), series(t, c["chart_start"], end, "v")), tick + ["SPY", "QQQ"]))
        spy_s = series("SPY", c["chart_start"], end)
        spy = dict(spy_s)
        corr = corrections(spy_s, c["low"], c["m24"])
        idx = [index_row(t, c, corr, end) for t in ("SPY", "QQQ")]
        for i, (dd, a, z) in enumerate(corr, 1):
            idx[0][f"corr{i}"] = {"start": a, "end": z, "pct": round(dd * 100, 1)}
        with ThreadPoolExecutor(8) as ex:
            rows = [r for r in ex.map(lambda t: analyze(t, c, spy, corr, end), tick) if r]
        out[k] = {"cycle": c, "index": idx, "rows": rows}
        print(f"\n== {k}: SPY low {idx[0]['low_date']} first new high {idx[0]['first_52w_high_date']} | QQQ low {idx[1]['low_date']} new high {idx[1]['first_52w_high_date']}")
        print("   pullbacks:", [(x[1], x[2], round(x[0] * 100, 1)) for x in corr])
        for r in rows:
            if r["gaps"] or r["jumps"]:
                print("   CHECK", r["ticker"], "gaps", r["gaps"][:2], "jumps", r["jumps"][:3])
        print("   analyzed", len(rows), "of", len(tick))
    json.dump(out, open("cycles_analysis.json", "w"), indent=1)
