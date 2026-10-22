#!/usr/bin/env python3
"""Fetch the figures behind the company pages, at deploy time.

Run by .github/workflows/pages.yml before tools/build_site.py. Writes one
file, .cache/companies/companies.json: the 50 largest companies in the
S&P 500 and, for each, the figures its page draws. build_site.py reads it;
with no file there are no company pages.

Sources:
    State Street       the SPY ETF's daily holdings: which companies, ranked
                       by their weight in the index (one per company, so
                       Alphabet appears once)
    Yahoo Finance      the fundamentals time series (annual income statement,
                       cash flow, balance sheet, quarterly diluted EPS) and the
                       chart endpoint (a year of closes and dividends). Both
                       answer without Yahoo's session crumb. When the crumb
                       session works (it does on GitHub's runners, not always
                       elsewhere) the industry is added from the company
                       profile; nothing depends on it.

When a company fails, it keeps its last good record (restored by the
workflow's cache) with its own dates. When the holdings file fails, the last
good list is used. Nothing here is published: the cache stays on the runner
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
TOP = 50
UA = "Mozilla/5.0"
SPY_URL = "https://www.ssga.com/us/en/intermediary/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx"

# GICS sectors of the largest S&P 500 companies. The holdings file carries no
# sector; a company not listed here takes the sector from Yahoo's profile when
# that answers, else "Other" (and the log says so, to add it here).
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

# Banks, insurers, asset managers and card networks' balance-sheet lenders:
# their cash flows are mostly customers' money, so no cash flow model.
NO_DCF = set("BRK-B JPM BAC GS WFC MS C AXP BLK SCHW PGR CB COF".split())

ANNUAL = ["TotalRevenue", "CostOfRevenue", "GrossProfit", "ResearchAndDevelopment", "SellingGeneralAndAdministration",
          "OperatingIncome", "PretaxIncome", "TaxProvision", "NetIncomeCommonStockholders", "FreeCashFlow",
          "CapitalExpenditure", "OperatingCashFlow", "StockholdersEquity", "TotalDebt"]
QUARTERLY = ["DilutedEPS", "OrdinarySharesNumber", "TotalDebt", "CashCashEquivalentsAndShortTermInvestments",
             "StockholdersEquity"]


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


def members(cache):
    """The TOP largest companies by index weight: [(Yahoo ticker, holdings name)]."""
    try:
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
            out.append([t, name])
            if len(out) == TOP:
                break
        cache["members"] = {"list": out, "ok": dt.date.today().isoformat()}
        return out
    except Exception as e:  # noqa: BLE001
        last = (cache.get("members") or {}).get("list")
        log(f"SPY holdings: {type(e).__name__}: {e}; using the last good list "
            f"({(cache.get('members') or {}).get('ok')})", "warning")
        if not last:
            raise
        return last


def series(symbol):
    """{type: [(as-of date, value)]} for the annual and quarterly fundamentals."""
    types = ",".join(["annual" + t for t in ANNUAL] + ["quarterly" + t for t in QUARTERLY])
    q = urllib.parse.urlencode({"type": types, "period1": int(dt.datetime(2019, 1, 1).timestamp()),
                                "period2": int(time.time()) + 86400})
    res = get_json(f"https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/"
                   f"{urllib.parse.quote(symbol)}?{q}")
    out = {}
    for r in res["timeseries"]["result"]:
        k = r["meta"]["type"][0]
        vals = []
        for x in r.get(k) or []:
            if x and x.get("reportedValue") and isinstance(x["reportedValue"].get("raw"), (int, float)):
                vals.append((x["asOfDate"], float(x["reportedValue"]["raw"])))
        if vals:
            out[k] = sorted(vals)
    return out


def chart(symbol):
    """A year of closes (completed sessions only), dividends and the quote meta."""
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?"
           + urllib.parse.urlencode({"range": "1y", "interval": "1d", "events": "div"}))
    res = get_json(url)["chart"]["result"][0]
    meta = res["meta"]
    offset = meta.get("gmtoffset") or 0
    day = lambda t: dt.datetime.fromtimestamp(t + offset, dt.timezone.utc).date().isoformat()  # noqa: E731
    closes = {}
    for t, c in zip(res.get("timestamp") or [], res["indicators"]["quote"][0]["close"]):
        if c is not None and math.isfinite(c):
            closes[day(t)] = round(c, 4)
    # A session still trading (or within 30 minutes of its close) is not a close yet.
    end = ((meta.get("currentTradingPeriod") or {}).get("regular") or {}).get("end")
    if end and time.time() < end + 1800:
        closes.pop(day(end), None)
    divs = sorted((day(d["date"]), d["amount"]) for d in ((res.get("events") or {}).get("dividends") or {}).values())
    return sorted(closes.items()), divs, meta


def latest(s, key):
    v = s.get(key)
    return v[-1] if v else None


def record(symbol, holdings_name, profile):
    s = series(symbol)
    closes, divs, meta = chart(symbol)
    if len(closes) < 2:
        raise ValueError("no closes")
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
    eps = s.get("quarterlyDilutedEPS") or []
    ttm_eps = sum(v for _, v in eps[-4:]) if len(eps) >= 4 else None
    eps_to = eps[-1][0] if eps else None
    cutoff = (dt.date.fromisoformat(closes[-1][0]) - dt.timedelta(days=365)).isoformat()
    div_ttm = sum(a for d, a in divs if d > cutoff)
    fcf_hist = [(d, v) for d, v in (s.get("annualFreeCashFlow") or [])]
    name = meta.get("longName") or meta.get("shortName") or holdings_name.title()
    return {
        "ticker": symbol,
        "name": name,
        "exchange": meta.get("fullExchangeName") or meta.get("exchangeName"),
        "currency": meta.get("currency") or "USD",
        "sector": SECTOR.get(symbol) or (profile or {}).get("sector") or "Other",
        "industry": (profile or {}).get("industry"),
        "closes": closes,
        "high52": meta.get("fiftyTwoWeekHigh"),
        "low52": meta.get("fiftyTwoWeekLow"),
        "fy": fy,
        "annual": annual,
        "fcf_hist": fcf_hist,
        "ttm_eps": ttm_eps,
        "eps_to": eps_to,
        "div_ttm": div_ttm,
        "shares": (latest(s, "quarterlyOrdinarySharesNumber") or latest(s, "annualDilutedAverageShares") or [None, None])[1],
        "debt": (latest(s, "quarterlyTotalDebt") or [None, None])[1],
        "cash": (latest(s, "quarterlyCashCashEquivalentsAndShortTermInvestments") or [None, None])[1],
        "equity": (latest(s, "quarterlyStockholdersEquity") or latest(s, "annualStockholdersEquity") or [None, None])[1],
        "bs_date": (latest(s, "quarterlyTotalDebt") or latest(s, "quarterlyCashCashEquivalentsAndShortTermInvestments") or [None])[0],
        "dcf": symbol not in NO_DCF,
        "fetched": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }


def profiles(symbols):
    """Sector and industry from Yahoo's profile, where the crumb session works."""
    try:
        y = Yahoo()
    except Exception as e:  # noqa: BLE001
        log(f"Yahoo profile skipped ({type(e).__name__}: {e}); sectors come from the built-in list", "notice")
        return {}
    out = {}
    for sym in symbols:
        try:
            r = y.json(f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{sym}?modules=assetProfile")
            p = r["quoteSummary"]["result"][0]["assetProfile"]
            out[sym] = {"sector": p.get("sector"), "industry": p.get("industry")}
        except Exception as e:  # noqa: BLE001
            log(f"{sym} profile: {type(e).__name__}: {e}", "notice")
    return out


def main():
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    old = cache.get("companies") or {}
    tops = members(cache)
    symbols = [t for t, _ in tops]
    prof = profiles(symbols)
    for t in symbols:
        if t not in SECTOR and not (prof.get(t) or {}).get("sector"):
            log(f"{t}: no sector; add it to SECTORS in tools/company_data.py", "warning")
    fresh, failed = {}, []
    for t, name in tops:
        try:
            fresh[t] = record(t, name, prof.get(t))
        except Exception as e:  # noqa: BLE001
            failed.append(t)
            if t in old:
                fresh[t] = old[t]
                log(f"{t}: {type(e).__name__}: {e}; keeping the record of {old[t].get('fetched')}", "warning")
            else:
                log(f"{t}: {type(e).__name__}: {e}; no record yet", "warning")
        time.sleep(0.4)
    try:
        spx, _, _ = chart("^GSPC")
        cache["spx"] = spx
    except Exception as e:  # noqa: BLE001
        log(f"^GSPC: {type(e).__name__}: {e}; keeping the last series", "warning")
    cache["order"] = symbols
    cache["companies"] = fresh
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, separators=(",", ":")))
    log(f"companies: {len(fresh) - len(failed)} fetched, {len(failed)} kept or missing {failed or ''}")
    if len(fresh) < TOP // 2:
        sys.exit("companies: fewer than half have a record")


if __name__ == "__main__":
    main()
