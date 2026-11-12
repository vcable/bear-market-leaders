"""Quarterly sales and EPS from SEC XBRL facts, with year-over-year growth and earnings-release dates.

- Each period's figures are the ones first reported for it. Year-over-year growth compares them with the
  year-earlier figures in the same filing, which is how the company presented the comparison at the time.
- EPS is put on today's share basis using the stock's split history, so it lines up with split-adjusted prices.
- Fourth quarters that are not tagged on their own are derived as the fiscal year minus its first three quarters.
- Release dates come from 8-K filings with item 2.02 (results of operations), else the 10-Q/10-K filing date.
"""
import datetime as dt
import urllib.parse
from fetch import get as massive_get, cached as massive_cached, BASE
from sec import facts, filings, REVENUE, EPS, IFRS_REVENUE, IFRS_EPS

D = dt.date.fromisoformat


def splits(ticker):
    d = massive_cached(f"splits_{ticker}.json",
                       lambda: massive_get(f"{BASE}/v3/reference/splits?ticker={urllib.parse.quote(ticker)}&limit=1000"))
    return [(r["execution_date"], r["split_from"] / r["split_to"]) for r in d.get("results", [])]


def kind(start, end):
    days = (D(end) - D(start)).days
    return "Q" if 80 <= days <= 100 else "FY" if 350 <= days <= 380 else None


def pick_unit(blocks, eps):
    count = {}
    for units in blocks:
        for u, fs in units.items():
            if (u.endswith("/shares") if eps else "/" not in u):
                count[u] = count.get(u, 0) + len(fs)
    return max(count, key=count.get) if count else None


def collect(fx, names, eps):
    """{(start, end): {accn: (val, filed)}} for quarterly and annual periods. Revenue keeps the largest concept per
    filing (the total line); EPS keeps the first concept in priority order (diluted before basic)."""
    unit = pick_unit([fx[n] for n in names if n in fx], eps)
    out = {}
    if not unit:
        return out, None
    for rank, n in enumerate(names):
        for f in fx.get(n, {}).get(unit, []):
            a, z = f.get("start"), f.get("end")
            if not a or not z or not kind(a, z):
                continue
            slot = out.setdefault((a, z), {})
            old = slot.get(f["accn"])
            if old is None or (not eps and f["val"] > old[0]) or (eps and rank < old[2]):
                slot[f["accn"]] = (f["val"], f["filed"], rank)
    return out, unit


def first(slot):
    accn, (v, filed, _) = min(slot.items(), key=lambda kv: kv[1][1])
    return v, filed, accn


def year_ago(per, k, accn):
    """The value for the period ending about a year before k, as shown in the same filing."""
    want = kind(*k)
    for k2, slot in per.items():
        if kind(*k2) == want and abs((D(k[1]) - D(k2[1])).days - 365) <= 20 and accn in slot:
            return slot[accn][0], slot[accn][1]
    return None


def series(per, adj):
    """period -> {val, filed, accn, prev} on today's share basis (adj), with Q4s derived from fiscal years."""
    rows = {}
    for k, slot in per.items():
        v, filed, accn = first(slot)
        ya = year_ago(per, k, accn)
        rows[k] = {"val": v * adj(filed), "filed": filed, "prev": ya[0] * adj(ya[1]) if ya else None, "derived": False}
    qs = {k: r for k, r in rows.items() if kind(*k) == "Q"}
    for k, r in list(rows.items()):
        if kind(*k) != "FY":
            continue
        a, z = k
        inside = sorted(q for q in qs if D(q[0]) >= D(a) - dt.timedelta(days=6) and D(q[1]) <= D(z) - dt.timedelta(days=60))
        if len(inside) != 3 or any(abs((D(q[1]) - D(z)).days) <= 6 for q in qs):
            continue
        q4 = (str(D(inside[-1][1]) + dt.timedelta(days=1)), z)
        rows[q4] = {"val": r["val"] - sum(qs[q]["val"] for q in inside), "filed": r["filed"], "prev": None, "derived": True}
    # year-ago value for derived Q4s and for anything the filing did not compare
    for k, r in rows.items():
        if r["prev"] is None and kind(*k) == "Q":
            p = next((r2 for k2, r2 in rows.items() if kind(*k2) == "Q" and abs((D(k[1]) - D(k2[1])).days - 365) <= 20), None)
            r["prev"] = p["val"] if p else None
    return rows


def release_dates(rows):
    eight = sorted(r["filingDate"] for r in rows if r["form"] in ("8-K", "8-K/A") and "2.02" in (r.get("items") or ""))
    periodic = {}
    for r in rows:
        if r["form"] in ("10-Q", "10-K", "10-KT", "20-F", "40-F") and r.get("reportDate"):
            periodic[r["reportDate"]] = min(periodic.get(r["reportDate"], "9999"), r["filingDate"])
    return eight, periodic


def report_date(end, eight, periodic, annual):
    """The last results 8-K between the quarter's end and its 10-Q/10-K (capped at 100 days), so a delivery or
    preliminary update earlier in the window gives way to the full earnings release."""
    near = [v for k, v in periodic.items() if abs((D(k) - D(end)).days) <= 6]
    pf = min(near) if near else None
    if not annual:
        cap = D(end) + dt.timedelta(days=100)
        if pf:
            cap = min(cap, D(pf))
        hits = [d for d in eight if D(end) < D(d) <= cap]
        if hits:
            return hits[-1], "8-K"
    return (pf, "annual report" if annual else "10-Q/10-K") if pf else (None, None)


def growth(cur, prev):
    if cur is None or prev is None or prev <= 0:
        return None
    return round((cur / prev - 1) * 100, 1)


def build(ticker, cik, start, end):
    f = facts(cik)
    fx = f["facts"].get("us-gaap") or {}
    rev_names, eps_names = REVENUE, EPS
    if not any(n in fx for n in REVENUE):
        fx, rev_names, eps_names = f["facts"].get("ifrs-full") or {}, IFRS_REVENUE, IFRS_EPS
    sp = splits(ticker)
    adj_eps = lambda filed: __import__("math").prod(fac for d, fac in sp if d > filed)
    rev_per, cur = collect(fx, rev_names, False)
    eps_per, _ = collect(fx, eps_names, True)
    rev = series(rev_per, lambda filed: 1.0)
    eps = series(eps_per, adj_eps)
    eight, periodic = release_dates(filings(cik)["rows"])

    def rows_for(kind_wanted):
        ks = sorted({k for k in list(rev) + list(eps) if kind(*k) == kind_wanted}, key=lambda k: k[1])
        out = []
        for k in ks:
            r, e = rev.get(k), eps.get(k)
            out.append({"start": k[0], "end": k[1], "rev": r["val"] if r else None, "rev_prev": r["prev"] if r else None,
                        "eps": e["val"] if e else None, "eps_prev": e["prev"] if e else None,
                        "derived": bool((r and r["derived"]) or (e and e["derived"]))})
        return out

    mode = "quarterly"
    rows = rows_for("Q")
    if not any(start <= r["end"] <= end for r in rows):
        mode, rows = "annual", rows_for("FY")
    rows = [r for r in rows if start <= r["end"] <= end]
    out = []
    for i, r in enumerate(rows):
        rep, src = report_date(r["end"], eight, periodic, mode == "annual")
        ry, ey = growth(r["rev"], r["rev_prev"]), growth(r["eps"], r["eps_prev"])
        p = out[-1] if out else None
        out.append({
            "end": r["end"], "reported": rep, "src": src, "derived": r["derived"],
            "rev_m": round(r["rev"] / 1e6, 1) if r["rev"] is not None else None,
            "rev_yoy": ry, "rev_accel": round(ry - p["rev_yoy"], 1) if p and ry is not None and p["rev_yoy"] is not None else None,
            "eps": round(r["eps"], 2) if r["eps"] is not None else None,
            "eps_prev": round(r["eps_prev"], 2) if r["eps_prev"] is not None else None,
            "eps_yoy": ey, "eps_accel": round(ey - p["eps_yoy"], 1) if p and ey is not None and p["eps_yoy"] is not None else None,
        })
    return {"mode": mode if out else "none", "currency": cur, "periods": out}


def last_reported(e, date):
    """The most recent period reported on or before a date."""
    if not e or not date:
        return None
    done = [p for p in e["periods"] if p["reported"] and p["reported"] <= date]
    return done[-1] if done else None


if __name__ == "__main__":
    import json
    import sys
    ciks = json.load(open("sec_ciks.json"))
    for t in sys.argv[1:] or ["SMCI", "NVDA", "ZM", "CRWD", "SE"]:
        e = build(t, ciks[t], "2018-01-01", "2025-12-31")
        print(f"\n{t} {e['mode']} {e['currency']}")
        for p in e["periods"][-12:]:
            print(f"  {p['end']} rep {p['reported']} ({p['src']}) rev {p['rev_m']}M yoy {p['rev_yoy']} acc {p['rev_accel']} | eps {p['eps']} vs {p['eps_prev']} yoy {p['eps_yoy']}{' Q4*' if p['derived'] else ''}")
