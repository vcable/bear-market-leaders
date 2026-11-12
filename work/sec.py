"""SEC EDGAR client: XBRL company facts (sales, EPS) and filing history (earnings-release dates), cached locally."""
import gzip
import json
import os
import threading
import time
import urllib.request

HERE = os.path.dirname(__file__)
# SEC asks automated clients to identify themselves with a name and contact email ("Jane Doe jane@example.com").
# Set SEC_USER_AGENT, or put that line in work/sec_ua.txt (git-ignored).
UA = os.environ.get("SEC_USER_AGENT") or (open(os.path.join(HERE, "sec_ua.txt")).read().strip()
                                          if os.path.exists(os.path.join(HERE, "sec_ua.txt")) else "")
CACHE = os.path.join(HERE, "cache", "sec")
os.makedirs(CACHE, exist_ok=True)

REVENUE = [
    "Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "RevenueFromContractWithCustomerIncludingAssessedTax",
    "SalesRevenueNet", "SalesRevenueGoodsNet", "SalesRevenueServicesNet", "RevenuesNetOfInterestExpense",
    "RevenueNet", "TotalRevenuesAndOtherIncome",
]
EPS = ["EarningsPerShareDiluted", "EarningsPerShareBasicAndDiluted", "EarningsPerShareBasic"]
IFRS_REVENUE = ["Revenue", "RevenueFromContractsWithCustomers"]
IFRS_EPS = ["DilutedEarningsLossPerShare", "BasicAndDilutedEarningsLossPerShare", "BasicEarningsLossPerShare"]
KEEP = {"us-gaap": set(REVENUE + EPS + ["NetIncomeLoss"]), "ifrs-full": set(IFRS_REVENUE + IFRS_EPS + ["ProfitLoss"])}

_lock = threading.Lock()
_last = [0.0]


def get(url, tries=5):
    if not UA:
        raise SystemExit("Set SEC_USER_AGENT (name and contact email) or create work/sec_ua.txt before calling SEC EDGAR.")
    for i in range(tries):
        with _lock:  # stay well under SEC's 10 requests a second
            wait = _last[0] + 0.15 - time.time()
            if wait > 0:
                time.sleep(wait)
            _last[0] = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))


def cached(name, fn):
    p = os.path.join(CACHE, name)
    if os.path.exists(p):
        return json.load(open(p))
    d = fn()
    json.dump(d, open(p, "w"))
    return d


def facts(cik):
    """Only the sales, EPS and net-income concepts from a company's XBRL facts."""
    cik = str(cik).zfill(10)

    def fn():
        d = get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
        if not d:
            return {"facts": {}}
        out = {"name": d.get("entityName"), "facts": {}}
        for tax, concepts in d.get("facts", {}).items():
            for c, body in concepts.items():
                if c in KEEP.get(tax, ()):
                    out["facts"].setdefault(tax, {})[c] = body.get("units", {})
        return out
    return cached(f"facts_{cik}.json", fn)


def filings(cik):
    """Every filing's form, date and 8-K items, including the older pages of the history."""
    cik = str(cik).zfill(10)

    def fn():
        d = get(f"https://data.sec.gov/submissions/CIK{cik}.json")
        if not d:
            return {"rows": []}
        cols = ("form", "filingDate", "reportDate", "items", "accessionNumber")
        rows = []

        def add(block):
            n = len(block.get("form", []))
            for i in range(n):
                rows.append({k: (block.get(k) or [None] * n)[i] for k in cols})
        add(d.get("filings", {}).get("recent", {}))
        for f in d.get("filings", {}).get("files", []):
            older = get("https://data.sec.gov/submissions/" + f["name"])
            if older:
                add(older)
        return {"name": d.get("name"), "tickers": d.get("tickers"), "rows": rows}
    return cached(f"filings_{cik}.json", fn)
