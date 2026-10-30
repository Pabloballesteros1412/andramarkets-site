#!/usr/bin/env python3
"""Fetch the history behind the Simulators, at deploy time.

Run by .github/workflows/pages.yml before tools/build_site.py. Writes one file
per data set to .cache/sim/, which build_site.py packs into assets/simdata-*.js:

    sp500.json    every trading day since the end of 1927 with its total return
                  (price change plus dividends): Yahoo Finance ^GSPC (the S&P 90
                  before March 1957) with Robert Shiller's monthly dividends,
                  spread evenly over each month's trading days as a yield on the
                  day before's close, to the end of 1987; the S&P 500 Total
                  Return index ^SP500TR from 1988.
    nasdaq.json, stoxx50.json, nikkei.json
                  daily price returns of the Nasdaq Composite (^IXIC, from
                  1971), the Euro Stoxx 50 (^STOXX50E, from 2007 on Yahoo) and
                  the Nikkei 225 (^N225, from 1965). Prices only: no free daily
                  dividend history exists for them.
    fed.json      monthly figures for Guess the Fed, from FRED: CPI (CPIAUCSL),
                  unemployment (UNRATE), the Fed's target (DFEDTAR to 2008, then
                  the range DFEDTARL and DFEDTARU) and the 2-year Treasury yield
                  (GS2). Needs FRED_API_KEY.
    bonds.json    the monthly 10-year Treasury yield for the Portfolio Builder:
                  Shiller's long rate, replaced by FRED GS10 from 1953.

Each set is fetched at most once a day and on its own: a failed fetch keeps
its last good copy (restored by the workflow's cache). Nothing here is
published.

    python3 tools/sim_data.py
"""
import csv
import datetime as dt
import io
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "sim"
UA = "Mozilla/5.0"  # Yahoo answers 429 to a full browser string from a script
SHILLER = "https://raw.githubusercontent.com/datasets/s-and-p-500/main/data/data.csv"
TR_FROM = "1988-01-04"  # first session of ^SP500TR on Yahoo


def log(msg, level="notice"):
    print(f"::{level}::{msg}" if os.environ.get("GITHUB_ACTIONS") else msg, flush=True)


def get(url):
    for wait in (10, 30, None):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or wait is None:
                raise
            time.sleep(wait)


def yahoo(symbol, start):
    """{session date: close} for a Yahoo index, sessions still trading left out."""
    q = urllib.parse.urlencode({"period1": int(dt.datetime(start.year, start.month, start.day, tzinfo=dt.timezone.utc).timestamp()),
                                "period2": int(time.time()) + 86400, "interval": "1d"})
    res = json.loads(get(f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?{q}"))["chart"]["result"][0]
    meta = res["meta"]
    offset = meta.get("gmtoffset") or 0
    out = {}
    for t, c in zip(res.get("timestamp") or [], res["indicators"]["quote"][0]["close"]):
        if c is not None and math.isfinite(c) and c > 0:
            out[dt.datetime.fromtimestamp(t + offset, dt.timezone.utc).date().isoformat()] = c
    end = ((meta.get("currentTradingPeriod") or {}).get("regular") or {}).get("end")
    if end and time.time() < end + 1800 and out:
        out.pop(max(out))  # today's session is not closed yet
    return out


def shiller_dividends():
    """{'YYYY-MM': twelve-month dividend in index points}."""
    rows = csv.DictReader(io.StringIO(get(SHILLER).decode("utf-8")))
    return {r["Date"][:7]: float(r["Dividend"]) for r in rows if float(r["Dividend"] or 0) > 0}


def build_sp500():
    price = yahoo("^GSPC", dt.date(1927, 12, 1))
    tr = yahoo("^SP500TR", dt.date(1987, 12, 1))
    divs = shiller_dividends()
    days = sorted(price)
    if len(days) < 20000 or days[0] > "1928-01-31":
        raise ValueError(f"^GSPC history too short: {len(days)} sessions from {days[0] if days else None}")
    per_month = {}
    for d in days:
        per_month[d[:7]] = per_month.get(d[:7], 0) + 1
    rows = []
    for prev, d in zip(days, days[1:]):
        if d >= TR_FROM:
            if d not in tr or prev not in tr:
                continue  # rare gap between the two Yahoo series: the day is left out
            r = tr[d] / tr[prev] - 1
        else:
            div = divs.get(d[:7])
            if div is None:
                raise ValueError(f"no Shiller dividend for {d[:7]}")
            r = price[d] / price[prev] - 1 + div / 12 / per_month[d[:7]] / price[prev]
        rows.append([d, round(r, 6)])
    return {"first": days[0], "rows": rows}


def price_returns(symbol, start, min_days):
    def build():
        price = yahoo(symbol, start)
        days = sorted(price)
        if len(days) < min_days:
            raise ValueError(f"{symbol} history too short: {len(days)} sessions")
        rows = [[d, round(price[d] / price[p] - 1, 6)] for p, d in zip(days, days[1:])]
        return {"first": days[0], "rows": rows}
    return build


def month_end(points):
    """{'YYYY-MM': last value in the month} from [(date, value)]."""
    out = {}
    for d, v in points:
        out[d.isoformat()[:7] if hasattr(d, "isoformat") else str(d)[:7]] = v
    return out


def build_fed():
    from dashboard_data import fred
    s = fred(["CPIAUCSL", "UNRATE", "GS2", "DFEDTAR", "DFEDTARL", "DFEDTARU"], dt.date(1975, 1, 1))
    cpi, unrate, gs2 = (month_end(s[k]) for k in ("CPIAUCSL", "UNRATE", "GS2"))
    single, lo, hi = (month_end(s[k]) for k in ("DFEDTAR", "DFEDTARL", "DFEDTARU"))
    rows = []
    for m in sorted(set(single) | set(lo)):
        y, mo = int(m[:4]), int(m[5:])
        prev = f"{y - 1}-{mo:02d}"
        if m not in cpi or prev not in cpi or m not in unrate:
            continue
        t_lo, t_hi = (lo[m], hi[m]) if m in lo else (single[m], single[m])
        rows.append([m, round((cpi[m] / cpi[prev] - 1) * 100, 2), unrate[m], t_lo, t_hi, gs2.get(m)])
    if len(rows) < 300:
        raise ValueError(f"FRED history too short: {len(rows)} months")
    return {"rows": rows}


def build_bonds():
    rows = csv.DictReader(io.StringIO(get(SHILLER).decode("utf-8")))
    yields = {r["Date"][:7]: float(r["Long Interest Rate"]) for r in rows if float(r["Long Interest Rate"] or 0) > 0}
    try:
        from dashboard_data import fred
        yields.update(month_end(fred(["GS10"], dt.date(1953, 1, 1))["GS10"]))
    except Exception as e:  # Shiller alone still covers all but the latest months
        log(f"FRED GS10 not fetched, Shiller's long rate only: {e}", "warning")
    return {"rows": [[m, yields[m]] for m in sorted(yields) if m >= "1927-12"]}


SETS = {
    "sp500": build_sp500,
    "nasdaq": price_returns("^IXIC", dt.date(1971, 1, 1), 10000),
    "stoxx50": price_returns("^STOXX50E", dt.date(1986, 1, 1), 2500),
    "nikkei": price_returns("^N225", dt.date(1965, 1, 1), 10000),
    "fed": build_fed,
    "bonds": build_bonds,
}


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    missing = 0
    for name, build in SETS.items():
        path = CACHE / f"{name}.json"
        try:
            old = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            old = None
        if old and old.get("fetched") == today:
            continue
        try:
            data = build()
        except Exception as e:  # keep the last good copy
            log(f"Simulator data {name} not fetched: {e}", "warning")
            missing += old is None
            continue
        data["fetched"] = today
        path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
        log(f"Simulator data {name}: {len(data['rows'])} rows, {data['rows'][0][0]} to {data['rows'][-1][0]}")
        time.sleep(0.5)
    return 1 if missing == len(SETS) else 0


if __name__ == "__main__":
    sys.exit(main())
