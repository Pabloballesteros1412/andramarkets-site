#!/usr/bin/env python3
"""Fetch the S&P 500 history behind the Trading Simulator, at deploy time.

Run by .github/workflows/pages.yml before tools/build_site.py. Writes
.cache/sim/sp500.json: one row per trading day since the end of 1927 with the
day's total return (price change plus dividends), which build_site.py packs
into assets/sim-sp500.js for the simulator page.

    - Daily closes: Yahoo Finance ^GSPC (the S&P 500, and the S&P 90 before
      March 1957), from 30 December 1927.
    - Dividends to the end of 1987: Robert Shiller's monthly S&P dividend
      (twelve-month total, in index points), as kept by the datasets/s-and-p-500
      repository on GitHub. Each month's dividend is spread evenly over that
      month's trading days as a yield on the day before's close.
    - Total return from 1988: Yahoo Finance ^SP500TR, the S&P 500 Total Return
      index (dividends reinvested), which replaces the estimate above.

The history is fetched at most once a day; a failed fetch keeps the last good
copy (restored by the workflow's cache). Nothing here is published.

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
CACHE = ROOT / ".cache" / "sim" / "sp500.json"
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


def build():
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
    return {"fetched": dt.date.today().isoformat(), "first": days[0], "rows": rows,
            "source": "Yahoo Finance ^GSPC and ^SP500TR; Robert Shiller's S&P dividends before 1988"}


def main():
    try:
        old = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        old = None
    if old and old.get("fetched") == dt.date.today().isoformat():
        log("Simulator history already fetched today")
        return 0
    try:
        data = build()
    except Exception as e:  # keep the last good copy
        log(f"Simulator history not fetched: {e}", "warning")
        return 0 if old else 1
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    log(f"Simulator history: {len(data['rows'])} sessions, {data['rows'][0][0]} to {data['rows'][-1][0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
