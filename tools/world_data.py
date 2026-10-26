#!/usr/bin/env python3
"""Fetch the figures behind the World markets page, at deploy time.

Run by .github/workflows/pages.yml before tools/build_site.py. Writes
.cache/world/world.json: for each of 25 markets, eight figures, each with its
own source and date. build_site.py draws world/ from it. Nothing is guessed:
a figure no free official source gives stays empty, and the page says so.

Axes and sources:
    1M return, YTD return     Yahoo Finance, the market's main index, local currency
    3M volatility             Yahoo Finance, daily log returns of that index, annualised
    Currency against the $    Yahoo Finance, change in the dollar value of the
                              local currency since the end of last year
    10Y yield                 OECD, long-term government bond yields (monthly)
    GDP growth                World Bank, real GDP growth, latest year; IMF World
                              Economic Outlook for Taiwan (not in World Bank data)
    Inflation                 OECD consumer prices, year on year, latest month when
                              it is less than six months old; otherwise World Bank,
                              latest year; IMF for Taiwan
    Unemployment              OECD monthly unemployment rate, same rule; otherwise
                              World Bank (national estimate), latest year; IMF for Taiwan

The IMF figure is only ever a completed year (the WEO also holds projections,
which are never used). When a source fails, each figure keeps its last good
value and date (Actions cache). Nothing here is published.

    python3 tools/world_data.py
"""
import csv
import datetime as dt
import io
import json
import math
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dashboard_data import log, yahoo  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "world" / "world.json"
UA = "Mozilla/5.0 (compatible; andramarkets-site; +https://github.com/Pabloballesteros1412/andramarkets-site)"

# (ISO3, name, index symbol, index name, currency pair, how the pair is quoted).
# quote "usd": dollars per unit (EURUSD=X); "local": units per dollar (JPY=X);
# None for the United States, whose currency is the dollar itself.
MARKETS = [
    ("USA", "United States", "^GSPC", "S&P 500", None, None),
    ("CAN", "Canada", "^GSPTSE", "S&P/TSX Composite", "CAD=X", "local"),
    ("MEX", "Mexico", "^MXX", "S&P/BMV IPC", "MXN=X", "local"),
    ("BRA", "Brazil", "^BVSP", "Bovespa", "BRL=X", "local"),
    ("ARG", "Argentina", "^MERV", "S&P Merval", "ARS=X", "local"),
    ("GBR", "United Kingdom", "^FTSE", "FTSE 100", "GBPUSD=X", "usd"),
    ("DEU", "Germany", "^GDAXI", "DAX 40", "EURUSD=X", "usd"),
    ("FRA", "France", "^FCHI", "CAC 40", "EURUSD=X", "usd"),
    ("ITA", "Italy", "FTSEMIB.MI", "FTSE MIB", "EURUSD=X", "usd"),
    ("ESP", "Spain", "^IBEX", "IBEX 35", "EURUSD=X", "usd"),
    ("NLD", "Netherlands", "^AEX", "AEX", "EURUSD=X", "usd"),
    ("CHE", "Switzerland", "^SSMI", "SMI", "CHF=X", "local"),
    ("SWE", "Sweden", "^OMX", "OMX Stockholm 30", "SEK=X", "local"),
    ("TUR", "Turkey", "XU100.IS", "BIST 100", "TRY=X", "local"),
    ("ISR", "Israel", "^TA125.TA", "TA-125", "ILS=X", "local"),
    ("ZAF", "South Africa", "^J203.JO", "FTSE/JSE All Share", "ZAR=X", "local"),
    ("IND", "India", "^NSEI", "Nifty 50", "INR=X", "local"),
    ("CHN", "China", "000001.SS", "Shanghai Composite", "CNY=X", "local"),
    ("HKG", "Hong Kong", "^HSI", "Hang Seng", "HKD=X", "local"),
    ("JPN", "Japan", "^N225", "Nikkei 225", "JPY=X", "local"),
    ("KOR", "South Korea", "^KS11", "KOSPI", "KRW=X", "local"),
    ("TWN", "Taiwan", "^TWII", "TAIEX", "TWD=X", "local"),
    ("IDN", "Indonesia", "^JKSE", "IDX Composite", "IDR=X", "local"),
    ("SGP", "Singapore", "^STI", "Straits Times", "SGD=X", "local"),
    ("AUS", "Australia", "^AXJO", "S&P/ASX 200", "AUDUSD=X", "usd"),
]
AXES = ["ret1m", "ytd", "vol3m", "fx", "y10", "gdp", "cpi", "unemp"]
FRESH = 183  # days: a monthly OECD figure older than this gives way to the annual one

OECD = "https://sdmx.oecd.org/public/rest/data/"
OECD_Q = {
    "y10": "OECD.SDD.STES,DSD_STES@DF_FINMARK,/.M.IRLT.PA.....",
    "cpi": "OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,/.M..CPI.PA._T.N.GY",
    "unemp": "OECD.SDD.TPS,DSD_LFS@DF_IALFS_UNE_M,/.UNE_LF_M.PT_LF_SUB._Z.Y._T.Y_GE15._Z.M",
}
OECD_NAME = {"y10": "OECD, long-term interest rates", "cpi": "OECD, consumer prices",
             "unemp": "OECD, monthly unemployment rate"}
WB = {"gdp": ("NY.GDP.MKTP.KD.ZG", "World Bank, real GDP growth"),
      "cpi": ("FP.CPI.TOTL.ZG", "World Bank, consumer price inflation"),
      "unemp": ("SL.UEM.TOTL.NE.ZS", "World Bank, unemployment (national estimate)")}
IMF = {"gdp": "NGDP_RPCH", "cpi": "PCPIPCH", "unemp": "LUR"}


def get(url, headers=None, tries=3):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except Exception:  # noqa: BLE001
            if k == tries - 1:
                raise
            time.sleep(5 * (k + 1))


def month_label(period):
    """'2026-09' -> a date at the month's start, kept as 'YYYY-MM'."""
    return period


def oecd(axis):
    """{ISO3: (period, value)}, the latest observation of each country. For
    prices, the national CPI where both it and the HICP exist."""
    raw = get(OECD + OECD_Q[axis] + "?" + urllib.parse.urlencode(
        {"startPeriod": f"{dt.date.today().year - 1}-01", "dimensionAtObservation": "AllDimensions"}),
        {"Accept": "application/vnd.sdmx.data+csv; charset=utf-8"}).decode("utf-8")
    best = {}
    for r in csv.DictReader(io.StringIO(raw)):
        try:
            v = float(r["OBS_VALUE"])
        except (KeyError, ValueError):
            continue
        key = (r["TIME_PERIOD"], 1 if r.get("METHODOLOGY", "N") == "N" else 0)
        if r["REF_AREA"] not in best or key > best[r["REF_AREA"]][0]:
            best[r["REF_AREA"]] = (key, (r["TIME_PERIOD"], round(v, 2)))
    if len(best) < 10:
        raise ValueError(f"OECD {axis}: only {len(best)} countries")
    return {k: v for k, (_, v) in best.items()}


def worldbank(axis):
    ind, _ = WB[axis]
    codes = ";".join(m[0] for m in MARKETS if m[0] != "TWN")
    res = json.loads(get(f"https://api.worldbank.org/v2/country/{codes}/indicator/{ind}?format=json&mrv=1&per_page=100"))
    out = {}
    for x in res[1] or []:
        if x.get("value") is not None:
            out[x["countryiso3code"]] = (x["date"], round(x["value"], 2))
    return out


def imf(axis, iso):
    """The last completed year's figure from the IMF World Economic Outlook."""
    ind = IMF[axis]
    res = json.loads(get(f"https://www.imf.org/external/datamapper/api/v1/{ind}/{iso}"))
    vals = res["values"][ind][iso]
    year = str(dt.date.today().year - 1)
    return (year, round(vals[year], 2)) if year in vals else None


def market_figures(m):
    """1M and YTD return, 3M volatility of the index; the currency's YTD move."""
    iso, _, sym, _, pair, quote = m
    out = {}
    closes = yahoo(sym, "2y")
    days = [d for d, _ in closes]
    last_d, last = closes[-1]
    by = dict(closes)

    def on_or_before(d):
        best = None
        for x in days:
            if x > d:
                break
            best = x
        return best
    m1 = on_or_before(last_d - dt.timedelta(days=30))
    ye = on_or_before(dt.date(last_d.year - 1, 12, 31))
    if m1:
        out["ret1m"] = {"v": round((last / by[m1] - 1) * 100, 2), "date": last_d.isoformat(), "from": m1.isoformat()}
    if ye:
        out["ytd"] = {"v": round((last / by[ye] - 1) * 100, 2), "date": last_d.isoformat(), "from": ye.isoformat()}
    start = on_or_before(last_d - dt.timedelta(days=91))
    window = [c for d, c in closes if start and d >= start]
    rets = [math.log(b / a) for a, b in zip(window, window[1:])]
    if len(rets) > 40:
        mean = sum(rets) / len(rets)
        sd = math.sqrt(sum((r - mean) ** 2 for r in rets) / (len(rets) - 1))
        out["vol3m"] = {"v": round(sd * math.sqrt(252) * 100, 2), "date": last_d.isoformat(), "from": start.isoformat()}
    if pair:
        fx = yahoo(pair, "2y")
        fdays = [d for d, _ in fx]
        fby = dict(fx)
        fl_d, fl = fx[-1]
        fye = None
        for x in fdays:
            if x > dt.date(fl_d.year - 1, 12, 31):
                break
            fye = x
        if fye:
            ratio = fl / fby[fye]
            move = (ratio if quote == "usd" else 1 / ratio) - 1
            out["fx"] = {"v": round(move * 100, 2), "date": fl_d.isoformat(), "from": fye.isoformat()}
    return out


SOURCE = {"ret1m": "Yahoo Finance", "ytd": "Yahoo Finance", "vol3m": "Yahoo Finance", "fx": "Yahoo Finance"}


def main():
    try:
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    fig = cache.setdefault("figures", {})
    status = cache.setdefault("sources", {})
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    today = dt.date.today()

    def put(iso, axis, rec):
        fig.setdefault(iso, {})[axis] = rec

    # Markets: index and currency from Yahoo, one market at a time.
    bad = []
    for m in MARKETS:
        try:
            for axis, rec in market_figures(m).items():
                rec["src"] = SOURCE[axis]
                put(m[0], axis, rec)
        except Exception as e:  # noqa: BLE001  a market keeps its last figures
            bad.append(f"{m[0]} ({type(e).__name__}: {e})"[:100])
        time.sleep(0.3)
    status["yahoo"] = {"ok": now, "error": "; ".join(bad) or None}

    # Official figures.
    got = {}
    for axis in OECD_Q:
        try:
            got[("oecd", axis)] = oecd(axis)
            status[f"oecd_{axis}"] = {"ok": now, "error": None}
        except Exception as e:  # noqa: BLE001
            status.setdefault(f"oecd_{axis}", {})["error"] = f"{type(e).__name__}: {e}"[:200]
            log(f"world: OECD {axis}: {e}; keeping the last figures", "warning")
        time.sleep(3)  # OECD limits bursts of requests
    for axis in WB:
        try:
            got[("wb", axis)] = worldbank(axis)
            status[f"wb_{axis}"] = {"ok": now, "error": None}
        except Exception as e:  # noqa: BLE001
            status.setdefault(f"wb_{axis}", {})["error"] = f"{type(e).__name__}: {e}"[:200]
            log(f"world: World Bank {axis}: {e}; keeping the last figures", "warning")
    for m in MARKETS:
        iso = m[0]
        y = (got.get(("oecd", "y10")) or {}).get(iso)
        if y:
            put(iso, "y10", {"v": y[1], "date": y[0], "src": OECD_NAME["y10"]})
        for axis in ("gdp", "cpi", "unemp"):
            rec = None
            o = (got.get(("oecd", axis)) or {}).get(iso) if axis in OECD_Q else None
            if o and (today - dt.date.fromisoformat(o[0] + "-01")).days <= FRESH:
                rec = {"v": o[1], "date": o[0], "src": OECD_NAME[axis]}
            elif (got.get(("wb", axis)) or {}).get(iso):
                w = got[("wb", axis)][iso]
                rec = {"v": w[1], "date": w[0], "src": WB[axis][1]}
            elif iso == "TWN":
                try:
                    i = imf(axis, iso)
                    if i:
                        rec = {"v": i[1], "date": i[0], "src": "IMF, World Economic Outlook"}
                except Exception as e:  # noqa: BLE001
                    log(f"world: IMF {axis} {iso}: {e}; keeping the last figure", "warning")
            if rec:
                put(iso, axis, rec)
    cache["updated"] = now
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=1), encoding="utf-8")
    filled = sum(1 for m in MARKETS for a in AXES if a in fig.get(m[0], {}))
    print(f"world: {filled} of {len(MARKETS) * len(AXES)} figures; Yahoo failures: {len(bad)}")
    for b in bad:
        log(f"world: {b}", "warning")


if __name__ == "__main__":
    main()
