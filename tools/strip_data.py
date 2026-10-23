#!/usr/bin/env python3
"""Fetch the homepage market strip (the tape), at deploy time.

Run by .github/workflows/pages.yml before tools/build_site.py, on every
deploy and on the market strip schedule (.github/workflows/market-strip.yml):
every 15 minutes while the NYSE is open, and once after the Euro Stoxx 50
and Nikkei 225 close. Writes .cache/strip/strip.json: for each of the ten
tape instruments its last price, its change on the previous session's close,
the time of that price and whether its market was open. build_site.py shows
it in place of the latest note's closes when it is newer than that note.

Sources:
    Yahoo Finance   the public chart endpoint. The price is the metadata's
                    regularMarketPrice at regularMarketTime, which is the
                    session's close once the market has shut, so the Euro
                    Stoxx 50 and the Nikkei 225 show their close after their
                    session ends (the daily bar's close is often still empty
                    then). The change is on the last daily close before that
                    session.
    FRED            US 10Y yield (DGS10) through the official API, with
                    FRED_API_KEY; the CBOE 10-year yield index (^TNX) on
                    Yahoo when FRED is unavailable.

An instrument that fails keeps its last good figure (restored by the
workflow's cache) with its own time. Nothing here is published: the cache
stays on the runner and the deploy refuses any .json in the site.

    python3 tools/strip_data.py            fetch and write the cache
    python3 tools/strip_data.py --due us   print due=true or due=false: is a
                                           refresh due now (us, europe, asia)

Environment:
    FRED_API_KEY  FRED API key (repository secret); never printed
"""
import datetime as dt
import json
import math
import sys
import urllib.parse
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nyse  # noqa: E402
from dashboard_data import fred, get, log  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "strip" / "strip.json"
NY = ZoneInfo("America/New_York")
BERLIN = ZoneInfo("Europe/Berlin")
TOKYO = ZoneInfo("Asia/Tokyo")

# Tape instrument key (as in tools/build_site.py TAPE) -> Yahoo symbol.
YAHOO = {
    "spx": "^GSPC", "ndx": "^NDX", "rut": "^RUT", "sx5e": "^STOXX50E", "nky": "^N225",
    "vix": "^VIX", "eurusd": "EURUSD=X", "wti": "CL=F", "gold": "GC=F",
}


def finite(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def quote(symbol, now):
    """Last price, change on the previous close (%), its time and market state."""
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?"
           + urllib.parse.urlencode({"range": "5d", "interval": "1d"}))
    res = json.loads(get(url))["chart"]["result"][0]
    meta = res["meta"]
    price, t = meta.get("regularMarketPrice"), meta.get("regularMarketTime")
    if not finite(price) or not t or price <= 0:
        raise ValueError(f"{symbol}: no price in the metadata")
    zone = ZoneInfo(meta.get("exchangeTimezoneName") or "UTC")
    when = dt.datetime.fromtimestamp(t, dt.timezone.utc)
    session = when.astimezone(zone).date()
    bars = {}
    for ts, c in zip(res.get("timestamp") or [], res["indicators"]["quote"][0]["close"]):
        if finite(c) and c > 0:
            bars[dt.datetime.fromtimestamp(ts, dt.timezone.utc).astimezone(zone).date()] = c
    before = [d for d in bars if d < session]
    if not before:
        raise ValueError(f"{symbol}: no close before {session}")
    prev = bars[max(before)]
    reg = (meta.get("currentTradingPeriod") or {}).get("regular") or {}
    is_open = bool(reg.get("start") and reg.get("end")
                   and reg["start"] <= now.timestamp() < reg["end"]
                   and when.timestamp() >= reg["start"])
    return {"last": float(price), "chg": round((price / prev - 1) * 100, 4), "unit": "%",
            "time": when.isoformat(timespec="seconds"), "day": session.isoformat(),
            "state": "open" if is_open else "close", "src": "Yahoo Finance"}


def ten_year(now):
    """US 10Y yield: FRED's DGS10, else the CBOE index ^TNX on Yahoo."""
    try:
        rows = fred(["DGS10"], (now - dt.timedelta(days=21)).date())["DGS10"]
        (_, v0), (d1, v1) = rows[-2], rows[-1]
        return {"last": v1, "chg": round((v1 - v0) * 100, 2), "unit": "bp", "time": None,
                "day": d1.isoformat(), "state": "close", "src": "FRED"}
    except Exception as e:  # noqa: BLE001  the error text never carries the key
        log(f"ust10y: FRED unavailable ({type(e).__name__}: {e}); trying Yahoo ^TNX", "warning")
    q = quote("^TNX", now)
    # ^TNX quotes the yield in percent (4.25); older data had it times ten.
    scale = 10 if q["last"] > 20 else 1
    last = q["last"] / scale
    prev = last / (1 + q["chg"] / 100)
    return {**q, "last": round(last, 4), "chg": round((last - prev) * 100, 2), "unit": "bp",
            "src": "Yahoo Finance, CBOE 10-year yield index"}


def due(market, now):
    """Is a refresh due now? us: the NYSE is open, or closed less than 45
    minutes ago (the closing prints); europe and asia: a weekday there (the
    schedule fires once, after the close)."""
    if market == "us":
        local = now.astimezone(NY)
        if nyse.is_trading_day(local.date()) is not True:
            return False
        close = 13 if nyse.close_time(local.date()) == "1:00 pm" else 16
        start = local.replace(hour=9, minute=30, second=0, microsecond=0)
        end = local.replace(hour=close, minute=45, second=0, microsecond=0)
        return start <= local < end
    zone = {"europe": BERLIN, "asia": TOKYO}[market]
    return now.astimezone(zone).weekday() < 5


def main():
    now = dt.datetime.now(dt.timezone.utc)
    if len(sys.argv) == 3 and sys.argv[1] == "--due":
        print(f"due={'true' if due(sys.argv[2], now) else 'false'}")
        return
    try:
        strip = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        strip = {}
    items = strip.get("items") or {}
    fresh = 0
    jobs = [(key, lambda s=sym: quote(s, now)) for key, sym in YAHOO.items()] + [("ust10y", lambda: ten_year(now))]
    for key, fn in jobs:
        try:
            items[key] = fn()
            fresh += 1
            print(f"{key}: {items[key]['last']:.4f} {items[key]['chg']:+.2f}{items[key]['unit']}, "
                  f"{items[key]['time'] or items[key]['day']} ({items[key]['state']})")
        except Exception as e:  # noqa: BLE001  one instrument failing never stops the deploy
            kept = (items.get(key) or {}).get("time") or (items.get(key) or {}).get("day") or "none"
            log(f"{key}: {type(e).__name__}: {e}; keeping the last figure ({kept})", "warning")
    if not fresh:
        log("Market strip: every source failed; the tape keeps its last figures.", "warning")
        return
    strip = {"updated": now.isoformat(timespec="seconds"), "items": items}
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(strip, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
