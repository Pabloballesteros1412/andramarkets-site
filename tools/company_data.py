#!/usr/bin/env python3
"""Fetch the figures behind the company pages, at deploy time.

Run by .github/workflows/pages.yml after tools/calendar_data.py, before
tools/build_site.py. Writes one file, .cache/companies/companies.json: the
600 companies of the calendar's earnings universe (the 200 largest in the
S&P 500, in the STOXX Europe 600 and across the six Asian markets, read from
.cache/calendar/calendar.json) and, for each, the figures its page draws.
build_site.py reads it; with no file there are no company pages.

Sources:
    Calendar cache     the universe: each market's companies in rank order,
                       with the benchmark each is measured against. When it is
                       missing, the last good copy here; with neither, the US
                       list from State Street's SPY holdings
    Wikidata, Commons  official logos of US companies as SVG (property P154),
                       fetched once and kept; Financial Modeling Prep's PNG
                       where none, and for Europe and Asia
    Yahoo Finance      the fundamentals time series (annual income statement,
                       cash flow, balance sheet, quarterly diluted EPS) and the
                       chart endpoint (a year of closes and dividends, each
                       benchmark, and the dollar rate of each currency). Both
                       answer without Yahoo's session crumb. When the crumb
                       session works (it does on GitHub's runners, not always
                       elsewhere) the sector and industry are added from the
                       company profile, fetched once and kept a month.

Yahoo rate-limits a burst of requests, so each run works within a time budget
(COMPANY_BUDGET seconds, default 1200): companies with no record first, then
the oldest. Closes are refetched each run, the fundamentals and the five
years of month-end closes every FUND_DAYS days. A company not reached, or one
that fails, keeps its last good record (restored by the workflow's cache)
with its own dates. Nothing here is published: the cache stays on the runner
and the deploy refuses any .json in the site.

    python3 tools/company_data.py
"""
import datetime as dt
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from calendar_data import Yahoo, company, fetch, xlsx_rows  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "companies" / "companies.json"
CAL = ROOT / ".cache" / "calendar" / "calendar.json"
MARKETS = ("us", "europe", "asia")
PER_MARKET = 200  # the calendar's universe: 200 per market
BUDGET = float(os.environ.get("COMPANY_BUDGET", "1200"))
FUND_DAYS = 5  # the fundamentals and month-end closes are refetched after this many days
FRESH = 2 * 3600  # closes fetched less than this long ago are not fetched again
PROFILE_DAYS = 30
UA = "Mozilla/5.0"
SPY_URL = "https://www.ssga.com/us/en/intermediary/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx"

# GICS sectors of the largest S&P 500 companies. A company not listed here
# (and every European and Asian one) takes the sector from Yahoo's profile,
# named as GICS names it (YAHOO_SECTOR), else "Other".
SECTORS = {
    "Information Technology": "NVDA AAPL MSFT AVGO MU AMD PLTR INTC CSCO LRCX AMAT PANW TXN CRWD IBM ORCL MRVL KLAC "
                              "SNDK CRM ADI APH ANET QCOM NOW ACN ADBE INTU WDC STX DELL SNPS CDNS FTNT",
    "Communication Services": "GOOGL GOOG META NFLX DIS VZ T TMUS CMCSA",
    "Consumer Discretionary": "AMZN TSLA HD MCD TJX BKNG LOW SBUX NKE",
    "Health Care": "LLY JNJ ABBV UNH MRK TMO AMGN GILD ABT PFE ISRG BSX DHR SYK VRTX MDT",
    "Financials": "BRK-B JPM V MA BAC GS WFC MS C AXP BLK SCHW SPGI PGR CB COF",
    "Energy": "XOM CVX COP",
    "Consumer Staples": "WMT COST PG KO PM PEP MO",
    "Industrials": "CAT GE RTX GEV UNP DE HON BA ETN UBER LMT",
    "Materials": "LIN",
    "Utilities": "NEE SO DUK CEG",
    "Real Estate": "WELL PLD AMT",
}
SECTOR = {t: s for s, ts in SECTORS.items() for t in ts.split()}
YAHOO_SECTOR = {"Technology": "Information Technology", "Financial Services": "Financials",
                "Consumer Cyclical": "Consumer Discretionary", "Consumer Defensive": "Consumer Staples",
                "Healthcare": "Health Care", "Basic Materials": "Materials"}

# Banks, insurers, asset managers and card networks' balance-sheet lenders:
# their cash flows are mostly customers' money, so no cash flow model. Beyond
# this list, any financial company whose Yahoo industry is one of LENDERS (or
# that has no industry yet), except the payment networks in DCF_OK.
NO_DCF = set("BRK-B JPM BAC GS WFC MS C AXP BLK SCHW PGR CB COF".split())
LENDERS = re.compile(r"Banks|Insurance|Asset Management|Capital Markets|Credit Services|Mortgage|Conglomerates", re.I)
DCF_OK = set("V MA PYPL SPGI MCO ICE CME".split())
# Yahoo quotes some markets in a minor unit: pence for London, cents for Johannesburg.
MINOR = {"GBp": ("GBP", 100), "GBX": ("GBP", 100), "ZAc": ("ZAR", 100), "ILA": ("ILS", 100)}

ANNUAL = ["TotalRevenue", "CostOfRevenue", "GrossProfit", "ResearchAndDevelopment", "SellingGeneralAndAdministration",
          "OperatingIncome", "PretaxIncome", "TaxProvision", "NetIncomeCommonStockholders", "FreeCashFlow",
          "CapitalExpenditure", "OperatingCashFlow", "StockholdersEquity", "TotalDebt",
          "CashCashEquivalentsAndShortTermInvestments", "CashDividendsPaid", "RepurchaseOfCapitalStock", "DilutedEPS",
          "OrdinarySharesNumber", "DilutedAverageShares"]
QUARTERLY = ["DilutedEPS", "OrdinarySharesNumber", "TotalDebt", "CashCashEquivalentsAndShortTermInvestments",
             "StockholdersEquity", "TotalRevenue", "NetIncomeCommonStockholders"]
# Annual and quarterly series the page charts over time.
HISTORY_ANNUAL = ["TotalRevenue", "NetIncomeCommonStockholders", "OperatingCashFlow", "CapitalExpenditure",
                  "FreeCashFlow", "CashCashEquivalentsAndShortTermInvestments", "TotalDebt", "StockholdersEquity",
                  "CashDividendsPaid", "RepurchaseOfCapitalStock", "DilutedEPS"]
HISTORY_QUARTERLY = ["TotalRevenue", "DilutedEPS", "NetIncomeCommonStockholders"]
LOGOS = CACHE.parent / "logos"
LOGO_URL = "https://financialmodelingprep.com/image-stock/{}.png"
WIKIDATA = "https://query.wikidata.org/sparql"
# Where Wikidata lists several logos for a company, the one to use (a word in
# its file name); where its only file is wrong or not vector, None (PNG then).
LOGO_PICK = {"GOOGL": "Alphabet", "GOOG": "Alphabet", "AAPL": "black", "AMAT": "Applied", "WMT": "2025", "LIN": None}


def log(msg, level="notice"):
    print(f"::{level}::{msg}" if os.environ.get("GITHUB_ACTIONS") else msg, flush=True)


def get_json(url):
    """JSON at url without a crumb, waiting and retrying when Yahoo rate-limits."""
    for wait in (5, 20, 45, None):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code != 429 or wait is None:
                raise
            time.sleep(wait)


def spy_list():
    """The PER_MARKET largest S&P 500 companies by index weight, as universe
    entries: the fallback when the calendar has no universe yet."""
    table = xlsx_rows(fetch(SPY_URL))
    head = next(i for i, r in enumerate(table) if "Ticker" in r)
    cols = table[head]
    ti, ni, wi = cols.index("Ticker"), cols.index("Name"), cols.index("Weight")
    rows = []
    for r in table[head + 1:]:
        if len(r) <= max(ti, ni, wi):
            continue
        t = r[ti].strip()
        if not re.fullmatch(r"[A-Z]{1,5}(?:\.[A-Z])?", t):
            continue
        try:
            rows.append((float(r[wi]), t.replace(".", "-"), r[ni].strip()))
        except ValueError:
            continue
    if len(rows) < 400:
        raise ValueError(f"SPY holdings: only {len(rows)} rows")
    rows.sort(reverse=True)
    out, seen = [], set()
    for _, t, name in rows:
        key = company(name)
        if key in seen:
            continue
        seen.add(key)
        out.append({"symbol": t, "name": name, "country": "US", "bench": "^GSPC", "bench_name": "S&P 500"})
        if len(out) == PER_MARKET:
            break
    return out


def series(symbol):
    """({type: [(as-of date, value)]}, reporting currency) for the annual and
    quarterly fundamentals."""
    types = ",".join(["annual" + t for t in ANNUAL] + ["quarterly" + t for t in QUARTERLY])
    q = urllib.parse.urlencode({"type": types, "period1": int(dt.datetime(2019, 1, 1).timestamp()),
                                "period2": int(time.time()) + 86400})
    res = get_json(f"https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/"
                   f"{urllib.parse.quote(symbol)}?{q}")
    out, curs = {}, {}
    for r in res["timeseries"]["result"]:
        k = r["meta"]["type"][0]
        vals = []
        for x in r.get(k) or []:
            if x and x.get("reportedValue") and isinstance(x["reportedValue"].get("raw"), (int, float)):
                vals.append((x["asOfDate"], float(x["reportedValue"]["raw"])))
                if x.get("currencyCode") and k == "annualTotalRevenue":
                    curs[x["currencyCode"]] = curs.get(x["currencyCode"], 0) + 1
        if vals:
            out[k] = sorted(vals)
    return out, (max(curs, key=curs.get) if curs else None)


def chart(symbol, rng="1y", interval="1d"):
    """Closes (completed sessions only), dividends and the quote meta."""
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?"
           + urllib.parse.urlencode({"range": rng, "interval": interval, "events": "div"}))
    res = get_json(url)["chart"]["result"][0]
    meta = res["meta"]
    # Pence and other minor units become the major unit: GBp 3,927.5 is GBP 39.275.
    major, div = MINOR.get(meta.get("currency"), (meta.get("currency"), 1))
    meta["currency"] = major
    for k in ("fiftyTwoWeekHigh", "fiftyTwoWeekLow", "regularMarketPrice"):
        if isinstance(meta.get(k), (int, float)):
            meta[k] = meta[k] / div
    offset = meta.get("gmtoffset") or 0
    day = lambda t: dt.datetime.fromtimestamp(t + offset, dt.timezone.utc).date().isoformat()  # noqa: E731
    closes = {}
    for t, c in zip(res.get("timestamp") or [], res["indicators"]["quote"][0]["close"]):
        if c is not None and math.isfinite(c):
            closes[day(t)] = round(c / div, 4 if div == 1 else 6)
    # A session still trading (or within 30 minutes of its close) is not a close yet.
    end = ((meta.get("currentTradingPeriod") or {}).get("regular") or {}).get("end")
    if interval == "1d" and end and time.time() < end + 1800:
        closes.pop(day(end), None)
    divs = sorted((day(d["date"]), d["amount"] / div) for d in ((res.get("events") or {}).get("dividends") or {}).values())
    return sorted(closes.items()), divs, meta


def latest(s, key):
    v = s.get(key)
    return v[-1] if v else None


def ttm(eps, annual_eps):
    """(diluted EPS over the last 12 months, the date it runs to): the last four
    quarters when they are consecutive; else the last fiscal year's (a company
    that reports half-yearly, or a quarter Yahoo lacks)."""
    if len(eps) >= 4 and (dt.date.fromisoformat(eps[-1][0]) - dt.date.fromisoformat(eps[-4][0])).days <= 300:
        return sum(v for _, v in eps[-4:]), eps[-1][0]
    if annual_eps:
        return annual_eps[-1][1], annual_eps[-1][0]
    return None, None


def fundamentals(symbol):
    """The figures from the reports: refetched every FUND_DAYS days."""
    s, fin = series(symbol)
    rev = s.get("annualTotalRevenue")
    if not rev:
        raise ValueError("no annual revenue")
    fy = rev[-1][0]
    annual = {}
    for t in ANNUAL:
        vals = dict(s.get("annual" + t) or [])
        annual[t] = {"fy": vals.get(fy), "prev": None}
        prior = [d for d in vals if d < fy]
        if prior:
            annual[t]["prev"] = vals[max(prior)]
    ttm_eps, eps_to = ttm(s.get("quarterlyDilutedEPS") or [], s.get("annualDilutedEPS") or [])
    try:
        monthly, _, _ = chart(symbol, "5y", "1mo")
    except Exception as e:  # noqa: BLE001
        log(f"{symbol} 5y monthly: {type(e).__name__}: {e}", "notice")
        monthly = []
    return {
        "fin_currency": fin,
        "fy": fy,
        "annual": annual,
        "fcf_hist": [(d, v) for d, v in (s.get("annualFreeCashFlow") or [])],
        "ttm_eps": ttm_eps,
        "eps_to": eps_to,
        "shares": (latest(s, "quarterlyOrdinarySharesNumber") or latest(s, "annualOrdinarySharesNumber")
                   or latest(s, "annualDilutedAverageShares") or [None, None])[1],
        "debt": (latest(s, "quarterlyTotalDebt") or latest(s, "annualTotalDebt") or [None, None])[1],
        "cash": (latest(s, "quarterlyCashCashEquivalentsAndShortTermInvestments")
                 or latest(s, "annualCashCashEquivalentsAndShortTermInvestments") or [None, None])[1],
        "equity": (latest(s, "quarterlyStockholdersEquity") or latest(s, "annualStockholdersEquity") or [None, None])[1],
        "bs_date": (latest(s, "quarterlyTotalDebt") or latest(s, "quarterlyCashCashEquivalentsAndShortTermInvestments")
                    or latest(s, "annualTotalDebt") or [None])[0],
        "hist_a": {t: [[d, v] for d, v in (s.get("annual" + t) or [])][-5:] for t in HISTORY_ANNUAL},
        "hist_q": {t: [[d, v] for d, v in (s.get("quarterly" + t) or [])][-8:] for t in HISTORY_QUARTERLY},
        "monthly": monthly,
        "fund_fetched": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }


FUND_KEYS = ("fin_currency", "fy", "annual", "fcf_hist", "ttm_eps", "eps_to", "shares", "debt", "cash", "equity",
             "bs_date", "hist_a", "hist_q", "monthly", "fund_fetched")


def age(stamp):
    """Seconds since an ISO time stamp; very large when there is none."""
    try:
        return (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(stamp)).total_seconds()
    except (TypeError, ValueError):
        return 1e12


def sector_of(symbol, profile):
    raw = (profile or {}).get("sector")
    return SECTOR.get(symbol) or YAHOO_SECTOR.get(raw, raw) or "Other"


def models_cash(symbol, sector, industry):
    """Whether a cash flow model fits: not for lenders, insurers and asset managers."""
    if symbol in NO_DCF:
        return False
    if sector == "Financials" and symbol not in DCF_OK:
        return bool(industry) and not LENDERS.search(industry)
    return True


def record(entry, market, old, profile):
    """One company's record: fresh closes, and fundamentals unless the old
    record's are less than FUND_DAYS old."""
    symbol = entry["symbol"]
    if old and old.get("fund_fetched") and age(old["fund_fetched"]) < FUND_DAYS * 86400 and old.get("annual"):
        fund = {k: old.get(k) for k in FUND_KEYS}
    else:
        fund = fundamentals(symbol)
    closes, divs, meta = chart(symbol)
    if len(closes) < 2:
        raise ValueError("no closes")
    cutoff = (dt.date.fromisoformat(closes[-1][0]) - dt.timedelta(days=365)).isoformat()
    sector = sector_of(symbol, profile)
    industry = (profile or {}).get("industry")
    return {
        **fund,
        "ticker": symbol,
        "name": meta.get("longName") or meta.get("shortName") or entry.get("name") or symbol,
        "market": market,
        "country": entry.get("country") or "",
        "bench": entry.get("bench"),
        "bench_name": entry.get("bench_name"),
        "exchange": meta.get("fullExchangeName") or meta.get("exchangeName"),
        "currency": meta.get("currency") or "USD",
        "fin_currency": fund.get("fin_currency") or meta.get("currency") or "USD",
        "sector": sector,
        "industry": industry,
        "closes": closes,
        "high52": meta.get("fiftyTwoWeekHigh"),
        "low52": meta.get("fiftyTwoWeekLow"),
        "div_ttm": sum(a for d, a in divs if d > cutoff),
        "dcf": models_cash(symbol, sector, industry),
        "fetched": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }


def wikidata_logos(symbols):
    """{ticker: Commons file URL} for the official logos on Wikidata (property
    P154), found through each company's NYSE or Nasdaq ticker."""
    tickers = " ".join(f'"{t.replace("-", ".")}"' for t in symbols)
    q = ("SELECT ?ticker ?logo WHERE { VALUES ?ticker { %s } ?item p:P414 ?st . ?st pq:P249 ?ticker ; ps:P414 ?ex . "
         "VALUES ?ex { wd:Q82059 wd:Q13677 } ?item wdt:P154 ?logo . }" % tickers)
    req = urllib.request.Request(f"{WIKIDATA}?{urllib.parse.urlencode({'query': q, 'format': 'json'})}",
                                 headers={"User-Agent": "andramarkets-site/1.0 (https://github.com/Pabloballesteros1412/andramarkets-site)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        rows = json.loads(r.read())["results"]["bindings"]
    found = {}
    for b in rows:
        found.setdefault(b["ticker"]["value"].replace(".", "-"), []).append(b["logo"]["value"])
    out = {}
    for t, urls in found.items():
        svgs = sorted(u for u in urls if u.lower().endswith(".svg"))
        if t in LOGO_PICK:
            word = LOGO_PICK[t]
            svgs = [u for u in svgs if word and word.lower() in urllib.parse.unquote(u).lower()]
        if svgs:
            out[t] = svgs[0]
    return out


def commons_file(url):
    """The file's direct address on upload.wikimedia.org, instead of the
    Special:FilePath redirect, which Commons rate-limits more tightly."""
    import hashlib
    name = urllib.parse.unquote(url.rsplit("/", 1)[-1]).replace(" ", "_")
    h = hashlib.md5(name.encode("utf-8")).hexdigest()
    return f"https://upload.wikimedia.org/wikipedia/commons/{h[0]}/{h[:2]}/{urllib.parse.quote(name)}"


def logo(symbol, svg_url=None):
    """The company's logo, kept once fetched: the official SVG from Wikimedia
    Commons where Wikidata has one, else a PNG from Financial Modeling Prep."""
    LOGOS.mkdir(parents=True, exist_ok=True)
    svg, png = LOGOS / f"{symbol}.svg", LOGOS / f"{symbol}.png"
    if svg_url:
        if svg.exists() and svg.stat().st_size > 100:
            return
        url = commons_file(svg_url)
        req = urllib.request.Request(url, headers={"User-Agent": "andramarkets-site/1.0 (https://github.com/Pabloballesteros1412/andramarkets-site)"})
        # Commons asks scripts to go slowly: wait between files, and longer on a 429.
        for wait in (20, 60, None):
            time.sleep(2)
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    raw = r.read(3 * 1024 * 1024 + 1)
                break
            except urllib.error.HTTPError as e:
                if e.code != 429 or wait is None:
                    raise
                time.sleep(wait)
        head = raw[:600].lower()
        if len(raw) > 3 * 1024 * 1024 or (b"<svg" not in head and b"<?xml" not in head):
            raise ValueError("not an SVG")
        # Served only through <img>, where scripts never run; dropped anyway.
        if b"<script" in raw.lower():
            raise ValueError("SVG with a script")
        svg.write_bytes(raw)
        return
    if png.exists() and png.stat().st_size > 200:
        return
    req = urllib.request.Request(LOGO_URL.format(urllib.parse.quote(symbol)), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read(2 * 1024 * 1024 + 1)
    if not raw.startswith(b"\x89PNG") or len(raw) > 2 * 1024 * 1024:
        raise ValueError("not a PNG")
    png.write_bytes(raw)


class Profiles:
    """Sector and industry from Yahoo's company profile, where the crumb session
    works; each kept PROFILE_DAYS days in the cache."""

    def __init__(self, cache):
        self.kept = cache.setdefault("profiles", {})
        self.yahoo = None
        self.down = False

    def get(self, sym):
        p = self.kept.get(sym)
        if p and age(p.get("ok")) < PROFILE_DAYS * 86400:
            return p
        if self.down:
            return p
        try:
            if self.yahoo is None:
                self.yahoo = Yahoo()
            r = self.yahoo.json(f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{urllib.parse.quote(sym)}"
                                "?modules=assetProfile")
            a = r["quoteSummary"]["result"][0]["assetProfile"]
            p = {"sector": a.get("sector"), "industry": a.get("industry"),
                 "ok": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
            self.kept[sym] = p
        except Exception as e:  # noqa: BLE001
            if self.yahoo is None:
                self.down = True
                log(f"Yahoo profile skipped ({type(e).__name__}: {e}); sectors come from the built-in list", "notice")
            else:
                log(f"{sym} profile: {type(e).__name__}: {e}", "notice")
        return p


def universe(cache):
    """[(market, entry)] in rank order: the calendar's earnings universe, else
    the last good copy, else the US alone from the SPY holdings."""
    kept = cache.get("universe") or {}
    try:
        got = json.loads(CAL.read_text()).get("universe") or {}
    except (OSError, ValueError):
        got = {}
    lists = {}
    for m in MARKETS:
        rows = [r for r in got.get(m) or [] if r.get("symbol")][:PER_MARKET]
        if len(rows) >= PER_MARKET // 2:
            lists[m] = rows
        elif kept.get(m):
            log(f"universe {m}: the calendar has {len(rows)}; using the last good list", "warning")
            lists[m] = kept[m]
    if "us" not in lists:
        try:
            lists["us"] = spy_list()
        except Exception as e:  # noqa: BLE001
            log(f"SPY holdings: {type(e).__name__}: {e}", "warning")
    if not lists:
        raise SystemExit("companies: no universe (run tools/calendar_data.py first)")
    cache["universe"] = {**kept, **lists}
    out, seen = [], set()
    for m in MARKETS:
        for r in lists.get(m) or []:
            if r["symbol"] not in seen:
                seen.add(r["symbol"])
                out.append((m, r))
    return out


def usd_rates(currencies, kept):
    """US dollars per unit of each currency, from Yahoo's FX chart; a currency
    that fails keeps its last rate."""
    out = {"USD": 1.0}
    for c in sorted(set(currencies) - {"USD", None, ""}):
        try:
            # Quoted as units per dollar and inverted: Yahoo rounds KRWUSD to 0.0008.
            _, _, meta = chart(f"USD{c}=X", "5d")
            if meta.get("regularMarketPrice"):
                out[c] = 1 / meta["regularMarketPrice"]
                continue
        except Exception as e:  # noqa: BLE001
            log(f"{c}USD: {type(e).__name__}: {e}; keeping the last rate", "warning")
        if kept.get(c):
            out[c] = kept[c]
    return out


def main():
    start = time.monotonic()
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    old = cache.get("companies") or {}
    uni = universe(cache)
    symbols = [e["symbol"] for _, e in uni]
    prof = Profiles(cache)
    # Wikidata lists NYSE and Nasdaq tickers: the US companies still without a logo.
    need = [e["symbol"] for m, e in uni if m == "us" and not any((LOGOS / f"{e['symbol']}{x}").exists() for x in (".svg", ".png"))]
    svgs = {}
    if need:
        try:
            svgs = wikidata_logos(need)
        except Exception as e:  # noqa: BLE001
            log(f"Wikidata logos: {type(e).__name__}: {e}; PNG logos only", "notice")
    # Companies with no record first, then the oldest closes; fresh ones are skipped.
    todo = sorted((x for x in uni if age((old.get(x[1]["symbol"]) or {}).get("fetched")) > FRESH),
                  key=lambda x: (x[1]["symbol"] in old, (old.get(x[1]["symbol"]) or {}).get("fetched") or ""))
    fresh, failed, left = {}, [], 0
    misses = cache.setdefault("logo_miss", {})
    for i, (market, entry) in enumerate(todo):
        t = entry["symbol"]
        if time.monotonic() - start > BUDGET:
            left = len(todo) - i
            break
        try:
            fresh[t] = record(entry, market, old.get(t), prof.get(t))
        except Exception as e:  # noqa: BLE001
            failed.append(t)
            log(f"{t}: {type(e).__name__}: {e}; " + (f"keeping the record of {old[t].get('fetched')}" if t in old else "no record yet"),
                "warning")
        # A logo not found is tried again after a week, not on every run.
        if age(misses.get(t)) > 7 * 86400:
            try:
                logo(t, svgs.get(t))
                misses.pop(t, None)
            except Exception as e:  # noqa: BLE001
                log(f"{t} logo: {type(e).__name__}: {e}", "notice")
                try:
                    if not svgs.get(t):
                        raise
                    logo(t)
                    misses.pop(t, None)
                except Exception as e2:  # noqa: BLE001
                    if svgs.get(t):
                        log(f"{t} PNG logo: {type(e2).__name__}: {e2}", "notice")
                    misses[t] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        time.sleep(0.3)
    # Members kept from earlier runs where not refetched; companies that left the universe drop out.
    companies = {t: fresh.get(t) or old[t] for t in symbols if t in fresh or t in old}
    for t, rec in companies.items():
        # The universe's own fields follow today's list even on a kept record.
        m, e = next((m, e) for m, e in uni if e["symbol"] == t)
        rec.update(market=m, country=e.get("country") or rec.get("country"), bench=e.get("bench"), bench_name=e.get("bench_name"),
                   cap=e.get("cap"))
    bench = cache.get("bench") or {}
    for b in sorted({c.get("bench") for c in companies.values() if c.get("bench")}):
        try:
            bench[b] = chart(b)[0]
        except Exception as e:  # noqa: BLE001
            log(f"{b}: {type(e).__name__}: {e}; keeping the last series", "warning")
    cache["bench"] = bench
    cache.pop("spx", None)  # now bench["^GSPC"]
    cache.pop("members", None)  # the old SPY list, now cache["universe"]
    cache["usd"] = usd_rates([c.get("currency") for c in companies.values()]
                             + [c.get("fin_currency") for c in companies.values()], cache.get("usd") or {})
    cache["order"] = [t for t in symbols if t in companies]
    cache["companies"] = companies
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, separators=(",", ":")))
    log(f"companies: {len(fresh)} fetched, {len(failed)} failed {failed or ''}, {left} left for the next run "
        f"(time budget), {len(companies)} of {len(symbols)} with a record")
    for t, c in companies.items():
        if c["sector"] == "Other":
            log(f"{t}: no sector yet (Yahoo profile); add US ones to SECTORS in tools/company_data.py", "notice")


if __name__ == "__main__":
    main()
