#!/usr/bin/env python3
"""Fetch the daily closes behind the Lab's risk and correlation tool, at deploy time.

Run by .github/workflows/pages.yml after tools/calendar_data.py, before
tools/build_site.py. Reads the calendar's earnings universe (every company the
calendar follows, with its benchmark) from .cache/calendar/calendar.json and
writes .cache/lab/closes.json: about three years of dividend-adjusted daily
closes for each company and each benchmark, from Yahoo Finance's chart
endpoint. build_site.py turns them into daily returns baked into
assets/lab-risk-<market>.js, which the tool page loads in the browser.

Yahoo rate-limits a burst of requests, so each run fetches only the symbols
not yet fetched today, oldest first, a fixed pause apart, and stops when its
time budget runs out (LAB_BUDGET seconds, default 300). A symbol not reached,
or one that fails, keeps its last good closes (restored by the workflow's
cache) and is fetched first next run. Nothing here is published: the cache
stays on the runner.

    python3 tools/lab_data.py
"""
import datetime as dt
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
CAL = ROOT / ".cache" / "calendar" / "calendar.json"
CACHE = ROOT / ".cache" / "lab" / "closes.json"
UA = "Mozilla/5.0"  # Yahoo answers 429 to a full browser string from a script
YEARS = 3
PAUSE = 0.35  # seconds between requests
BUDGET = float(os.environ.get("LAB_BUDGET", "300"))
# Benchmarks Yahoo keeps no history for, and the index used for beta instead.
RISK_BENCH = {"000300.SS": ("000001.SS", "Shanghai Composite")}


def bench_of(c):
    """(symbol, name) of a universe company's benchmark for the risk tool."""
    return RISK_BENCH.get(c["bench"], (c["bench"], c["bench_name"]))


def log(msg, level="notice"):
    print(f"::{level}::{msg}" if os.environ.get("GITHUB_ACTIONS") else msg, flush=True)


def get_json(url):
    """JSON at url, waiting and retrying when Yahoo rate-limits."""
    for wait in (10, 30, None):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code != 429 or wait is None:
                raise
            time.sleep(wait)


def closes(symbol, start):
    """[(session date, adjusted close)], dates in the exchange's zone, sessions
    still trading left out (their close would be an intraday price)."""
    q = urllib.parse.urlencode({"period1": int(dt.datetime.combine(start, dt.time()).timestamp()),
                                "period2": int(time.time()) + 86400, "interval": "1d", "events": "div,split"})
    res = get_json(f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?{q}")["chart"]["result"][0]
    meta = res["meta"]
    offset = meta.get("gmtoffset") or 0
    stamps = res.get("timestamp") or []
    adj = ((res["indicators"].get("adjclose") or [{}])[0].get("adjclose")) or res["indicators"]["quote"][0]["close"]
    out = {}
    for t, c in zip(stamps, adj):
        if c is not None and math.isfinite(c) and c > 0:
            out[dt.datetime.fromtimestamp(t + offset, dt.timezone.utc).date().isoformat()] = round(c, 6)
    end = ((meta.get("currentTradingPeriod") or {}).get("regular") or {}).get("end")
    if end and time.time() < end + 1800:
        out.pop(dt.datetime.fromtimestamp(end + offset, dt.timezone.utc).date().isoformat(), None)
    if len(out) < 40:
        raise ValueError(f"{symbol}: only {len(out)} closes")
    return sorted(out.items())


def main():
    try:
        universe = json.loads(CAL.read_text(encoding="utf-8")).get("universe") or {}
    except (OSError, ValueError):
        universe = {}
    try:
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    wanted = []
    for market in ("us", "europe", "asia"):
        for c in universe.get(market) or []:
            for sym in (c["symbol"], bench_of(c)[0]):
                if sym not in wanted:
                    wanted.append(sym)
    if not wanted:
        log("lab: no earnings universe in the calendar cache yet; the risk tool keeps its last closes", "warning")
        return
    today = dt.date.today()
    start = today - dt.timedelta(days=365 * YEARS + 40)
    stale = [s for s in wanted if (cache.get(s) or {}).get("fetched", "")[:10] != today.isoformat()]
    stale.sort(key=lambda s: (cache.get(s) or {}).get("fetched", ""))  # never fetched first, then oldest
    began, done, failed = time.monotonic(), 0, []
    for sym in stale:
        if time.monotonic() - began > BUDGET:
            break
        try:
            cache[sym] = {"fetched": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                          "closes": closes(sym, start)}
            done += 1
        except Exception as e:  # noqa: BLE001  one symbol failing keeps its last closes
            failed.append(f"{sym} ({type(e).__name__}: {e})"[:120])
        time.sleep(PAUSE)
    left = len(stale) - done - len(failed)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, separators=(",", ":")), encoding="utf-8")
    print(f"lab: {len(wanted)} symbols, {done} fetched in {time.monotonic() - began:.0f}s, "
          f"{len(failed)} failed, {left} left for the next run")
    for f in failed[:20]:
        log(f"lab: {f}; keeping the last closes", "warning")


if __name__ == "__main__":
    sys.exit(main())
