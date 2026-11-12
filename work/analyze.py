"""Per-ticker daily-bar analysis: verified returns, run-start timing, and behaviour vs SPY/QQQ."""
import json, datetime as dt
from concurrent.futures import ThreadPoolExecutor
from fetch import bars

START, END = "2021-01-01", "2024-12-31"
TOP_N = 60


# Symbols that belonged to a different security inside the lookback window:
# stitch in the company's prior ticker, or drop the other security's bars.
PREDECESSOR = {"META": ("FB", "2022-06-09"), "COHR": ("IIVI", "2022-09-08")}
FIRST_VALID = {"SG": "2021-11-18"}


def _raw(t, field="c"):
    out = []
    for b in bars(t, START, END):
        d = dt.datetime.fromtimestamp(b["t"] / 1000 + 12 * 3600, dt.timezone.utc).date().isoformat()
        out.append((d, b[field]))
    return out


def series(t, field="c"):
    """Daily closes (or another bar field, e.g. "v" for volume) as (date, value) pairs."""
    s = _raw(t, field)
    if t in PREDECESSOR:
        old, switch = PREDECESSOR[t]
        s = [x for x in _raw(old, field) if x[0] < switch] + [x for x in s if x[0] >= switch]
    if t in FIRST_VALID:
        s = [x for x in s if x[0] >= FIRST_VALID[t]]
    return s


def close_on(s, date):
    """Last close on or before date."""
    v = None
    for d, c in s:
        if d > date:
            break
        v = c
    return v


def pct(a, b):
    return None if a is None or b is None else round((b / a - 1) * 100, 1)


def first_52w_high(s, after_idx):
    """First index after after_idx where close exceeds the max of the prior 251 closes."""
    for i in range(after_idx + 1, len(s)):
        lo = max(0, i - 251)
        if i - lo >= 120 and s[i][1] > max(c for _, c in s[lo:i]):
            return i
    return None


def drawdown_window(s, start, end):
    """Peak-to-trough window of the largest closing decline between start and end."""
    pts = [(d, c) for d, c in s if start <= d <= end]
    best, peak = (0, None, None), pts[0]
    for d, c in pts:
        if c > peak[1]:
            peak = (d, c)
        dd = c / peak[1] - 1
        if dd < best[0]:
            best = (dd, peak[0], d)
    return best


def analyze(t, spy, qqq, corrections):
    s = series(t)
    if len(s) < 200:
        return None
    sd = dict(s)
    r = {"ticker": t}
    r["ret_2023"] = pct(close_on(s, "2022-12-30"), close_on(s, "2023-12-29"))
    r["ret_2024"] = pct(close_on(s, "2023-12-29"), close_on(s, "2024-12-31"))
    r["ret_2023_24"] = pct(close_on(s, "2022-12-30"), close_on(s, "2024-12-31"))

    # run peak within 2023-24, and the cycle low that preceded it
    idx = [i for i, (d, _) in enumerate(s) if "2023-01-01" <= d <= "2024-12-31"]
    pk = max(idx, key=lambda i: s[i][1])
    lo_cands = [i for i, (d, _) in enumerate(s) if "2022-01-01" <= d and i <= pk]
    lo = min(lo_cands, key=lambda i: s[i][1])
    prior = [i for i in range(len(s)) if s[i][0] < s[lo][0]]
    hi_before = max(prior, key=lambda i: s[i][1]) if prior else None
    r["prior_high_date"] = s[hi_before][0] if hi_before is not None else None
    r["bear_drawdown_pct"] = pct(s[hi_before][1], s[lo][1]) if hi_before is not None else None
    r["cycle_low_date"], r["run_peak_date"] = s[lo][0], s[pk][0]
    r["low_to_peak_pct"] = pct(s[lo][1], s[pk][1])

    b = first_52w_high(s, lo)
    r["first_52w_high_date"] = s[b][0] if b is not None else None
    r["pct_off_low_at_52w_high"] = pct(s[lo][1], s[b][1]) if b is not None else None

    # RS line vs SPY: first new 52-week high in the ratio after the low
    rs = [(d, c / spy[d]) for d, c in s if d in spy]
    rs_lo = next(i for i, (d, _) in enumerate(rs) if d >= s[lo][0])
    rb = first_52w_high(rs, rs_lo)
    r["rs_line_52w_high_date"] = rs[rb][0] if rb is not None else None
    r["rs_led_price"] = (r["rs_line_52w_high_date"] is not None and r["first_52w_high_date"] is not None
                         and r["rs_line_52w_high_date"] < r["first_52w_high_date"])

    for name, (a, z) in corrections.items():
        r[f"{name}_pct"] = pct(close_on(s, a), close_on(s, z))

    # volume on the run-start days, against the average of the 50 sessions before each
    vol = series(t, "v")
    for key, i in (("low", lo), ("high", b)):
        r[f"{key}_volume"], r[f"{key}_vol_vs_50d"] = None, None
        if i is None:
            continue
        prior = [v for _, v in vol[max(0, i - 50):i] if v]
        if len(prior) >= 20 and vol[i][1]:
            r[f"{key}_volume"] = int(vol[i][1])
            r[f"{key}_vol_vs_50d"] = round(vol[i][1] / (sum(prior) / len(prior)), 2)
    return r


if __name__ == "__main__":
    screen = json.load(open("screen.json"))
    tick = []
    for k in ("2023", "2024", "2023-24"):
        for row in screen[k][:TOP_N]:
            if row["ticker"] not in tick:
                tick.append(row["ticker"])
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(series, tick + ["SPY", "QQQ"]))
    spy_s, qqq_s = series("SPY"), series("QQQ")
    spy, qqq = dict(spy_s), dict(qqq_s)

    # index corrections inside the uptrend, taken from SPY itself
    c23 = drawdown_window(spy_s, "2023-06-01", "2023-12-31")
    c24 = drawdown_window(spy_s, "2024-06-01", "2024-09-30")
    corrections = {"spy_corr_2023": (c23[1], c23[2]), "spy_corr_2024": (c24[1], c24[2])}

    idx_rows = [analyze(t, spy, qqq, corrections) for t in ("SPY", "QQQ")]
    with ThreadPoolExecutor(8) as ex:
        rows = [r for r in ex.map(lambda t: analyze(t, spy, qqq, corrections), tick) if r]

    # sanity-check against the market-wide screen
    by = {k: {r["ticker"]: r for r in screen[k]} for k in screen}
    for r in rows:
        for k, col in (("2023", "ret_2023"), ("2024", "ret_2024"), ("2023-24", "ret_2023_24")):
            g = by[k].get(r["ticker"])
            if g and r[col] is not None and abs(g["ret_pct"] - r[col]) > 1.5:
                print("MISMATCH", r["ticker"], k, g["ret_pct"], r[col])
    json.dump({"corrections": corrections, "index": idx_rows, "rows": rows}, open("analysis.json", "w"), indent=1)
    print("corrections", corrections)
    for r in idx_rows:
        print(r)
    print(len(rows), "names analyzed")
