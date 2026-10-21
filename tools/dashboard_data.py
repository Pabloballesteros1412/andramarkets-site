#!/usr/bin/env python3
"""Fetch the figures behind the dashboard tiles, at deploy time.

Run by .github/workflows/pages.yml before tools/build_site.py. Writes one
small file, .cache/dashboards/tiles.json: for each tile, the few numbers its
preview draws, the source and the as-of date. build_site.py reads it; a tile
with no record keeps its illustrative preview and says so.

Sources:
    the agent's archive   releases archive-YYYY-MM-DD in the agent repo; only
                          the facts of the run behind a published note, on an
                          NYSE trading day, and never a series the facts mark
                          as not yet published or from another session
    FRED                  fredgraph.csv, no key
    Yahoo Finance         the public chart endpoint

When a source fails, the tile keeps its last good record (restored by the
workflow's cache) with its own date, so a FRED outage never blanks a tile or
redates it. Nothing here is published: the cache stays on the runner, holds
only the figures the tiles draw (never a facts file), and the deploy refuses
any .json in the site.

    python3 tools/dashboard_data.py

Environment:
    AGENT_ARTIFACTS_TOKEN  fine-grained token on the agent repo; reading the
                           archive releases needs Contents: read
    AGENT_REPO             default Pabloballesteros1412/andramarkets
"""
import csv
import datetime as dt
import io
import json
import math
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nyse  # noqa: E402
from import_notes import charts, number, unprinted  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
NOTES = ROOT / "data" / "notes"
CACHE = ROOT / ".cache" / "dashboards" / "tiles.json"
API = "https://api.github.com"
AGENT_REPO = os.environ.get("AGENT_REPO", "Pabloballesteros1412/andramarkets")
UA = "Mozilla/5.0 (compatible; andramarkets-site)"
MAX_JSON = 5 * 1024 * 1024
LOOKBACK = 10  # vetted sessions searched for a complete set of prints


def log(msg, level="notice"):
    print(f"::{level}::{msg}" if os.environ.get("GITHUB_ACTIONS") else msg, flush=True)


def get(url, headers=None, limit=MAX_JSON):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=40) as r:
        raw = r.read(limit + 1)
    if len(raw) > limit:
        raise ValueError(f"{url}: response too large")
    return raw


# The agent's archive --------------------------------------------------------

class Archive:
    """Facts of the runs behind published notes, newest session first."""

    def __init__(self, token):
        self.token = token
        self.assets = {}  # run id -> release asset id of its facts file
        page = 1
        while True:
            rel = json.loads(self._api(f"/repos/{AGENT_REPO}/releases?per_page=100&page={page}"))
            for r in rel:
                if not str(r.get("tag_name", "")).startswith("archive-"):
                    continue
                for a in r.get("assets") or []:
                    m = re.fullmatch(r"facts_\d{8}_r(\d+)\.json", a.get("name", ""))
                    if m:
                        self.assets[int(m.group(1))] = a["id"]
            if len(rel) < 100:
                break
            page += 1
        self.runs = []
        for f in NOTES.glob("*.json"):
            rec = json.loads(f.read_text(encoding="utf-8"))
            day = dt.date.fromisoformat(rec["date"])
            run = (rec.get("source") or {}).get("run_id")
            if rec.get("published") is not False and nyse.is_trading_day(day) is True and run in self.assets:
                self.runs.append((day, run))
        self.runs.sort(reverse=True)
        self._facts = {}

    def _api(self, path, accept="application/vnd.github+json"):
        headers = {"Accept": accept, "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return get(API + path, headers)

    def facts(self, run):
        """Held in memory only: the full facts file is never written anywhere."""
        if run not in self._facts:
            raw = self._api(f"/repos/{AGENT_REPO}/releases/assets/{self.assets[run]}", "application/octet-stream")
            self._facts[run] = json.loads(raw)
        return self._facts[run]

    def sessions(self, n=LOOKBACK):
        for day, run in self.runs[:n]:
            facts = self.facts(run)
            if facts.get("date") == day.isoformat():
                yield day, facts


def prev_session(day):
    d = day - dt.timedelta(days=1)
    while nyse.is_trading_day(d) is False:
        d -= dt.timedelta(days=1)
    return d


def block_rows(facts, spec):
    """(label, last, chg) for every instrument in spec, or None if one has no print."""
    stale, rows = unprinted(facts), []
    for block, key, label in spec:
        row = next((r for r in facts.get(block) or [] if isinstance(r, dict) and r.get("key") == key), None)
        last, chg = (number(row.get("last")), number(row.get("chg"))) if row else (None, None)
        if last is None or chg is None or key in stale:
            return None
        rows.append((label or str(row.get("name"))[:28], last, chg))
    return rows


def latest_complete(archive, spec):
    """The newest vetted session in which every instrument in spec printed."""
    for day, facts in archive.sessions():
        rows = block_rows(facts, spec)
        if rows:
            return day, rows
    raise LookupError("no recent session prints every instrument")


SECTORS = [("sectors", k, None) for k in ("xlk", "xlf", "xlv", "xly", "xlp", "xle",
                                          "xli", "xlb", "xlre", "xlu", "xlc")]
# Majors against the dollar; True when the dollar is the quote currency
# (EUR/USD), so the dollar's own move is the opposite sign.
FX = [("eurusd", "Euro", True), ("usdjpy", "Japanese yen", False), ("gbpusd", "Pound", True),
      ("usdchf", "Swiss franc", False), ("usdcad", "Canadian dollar", False),
      ("audusd", "Australian dollar", True)]


def tile_sectors(archive):
    day, rows = latest_complete(archive, SECTORS)
    return day, "Yahoo Finance, sector ETFs", {"rows": sorted(([n, c] for n, _, c in rows), key=lambda r: -r[1])}


def tile_fx(archive):
    day, rows = latest_complete(archive, [("fx", k, n) for k, n, _ in FX])
    usd = [[n, -c if quote else c] for (n, _, c), (_, _, quote) in zip(rows, FX)]
    return day, "Yahoo Finance", {"rows": sorted(usd, key=lambda r: -r[1])}


def curve_at(day, facts):
    """(as-of date, {tenor key: yield}) from one session's facts, or None."""
    cv = charts(facts)["curve"]
    pts = {c["key"]: c["last"] for c in cv if c["last"] is not None}
    if len(pts) < 8 or len({c["stale"] for c in cv}) > 1:
        return None
    # FRED posts the curve after the agent runs: the facts then carry the
    # session before's curve, flagged as not yet published.
    return (prev_session(day) if cv[0]["stale"] else day), pts


def tile_curve(archive):
    curves = {}
    for day, facts in archive.sessions(40):
        c = curve_at(day, facts)
        if c:
            curves.setdefault(c[0], c[1])
    if not curves:
        raise LookupError("no curve in the archive")
    now = max(curves)
    target = now - dt.timedelta(days=30)
    then = min((d for d in curves if d < now), key=lambda d: abs((d - target).days), default=None)
    if then is None or abs((then - target).days) > 5:
        raise LookupError("no curve about a month before the latest")
    keys = [k for k in curves[now] if k in curves[then]]
    return now, "FRED, US Treasury", {"then": then.isoformat(), "tenors": keys,
                                      "now": [curves[now][k] for k in keys],
                                      "before": [curves[then][k] for k in keys]}


# FRED -----------------------------------------------------------------------

FRED_DOWN = []


def fred(series, start):
    """{series: [(date, value)]} from fredgraph.csv, skipping missing values."""
    if FRED_DOWN:
        raise FRED_DOWN[0]
    try:
        return _fred(series, start)
    except (OSError, ValueError) as e:
        FRED_DOWN.append(e)  # one outage: don't wait on every later series
        raise


def _fred(series, start):
    url = ("https://fred.stlouisfed.org/graph/fredgraph.csv?"
           + urllib.parse.urlencode({"id": ",".join(series), "cosd": start.isoformat()}))
    text = get(url).decode("utf-8-sig")
    if not text.lstrip().lower().startswith(("observation_date", "date")):
        raise ValueError("FRED did not answer with a CSV (maintenance page?)")
    out = {s: [] for s in series}
    for row in csv.DictReader(io.StringIO(text)):
        day = dt.date.fromisoformat(row.get("observation_date") or row.get("DATE"))
        for s in series:
            try:
                v = float(row.get(s, ""))
            except ValueError:
                continue
            if math.isfinite(v):
                out[s].append((day, v))
    for s in series:
        if not out[s]:
            raise ValueError(f"FRED {s}: no observations")
    return out


def tile_credit(_):
    today = dt.date.today()
    s = fred(["BAMLH0A0HYM2", "BAMLC0A0CM"], today - dt.timedelta(days=190))
    hy, ig = dict(s["BAMLH0A0HYM2"]), dict(s["BAMLC0A0CM"])
    days = sorted(set(hy) & set(ig))[-120:]
    if len(days) < 20:
        raise LookupError("too few common observations")
    return days[-1], "ICE BofA, FRED", {
        "start": days[0].isoformat(), "hy": [hy[d] for d in days], "ig": [ig[d] for d in days]}


def tile_inflation(_):
    today = dt.date.today()
    s = fred(["CPIAUCSL", "PAYEMS"], today.replace(day=1) - dt.timedelta(days=366 * 5 + 31))
    cpi, pay = dict(s["CPIAUCSL"]), s["PAYEMS"]
    yoy = [(d, (v / cpi[d.replace(year=d.year - 1)] - 1) * 100) for d, v in sorted(cpi.items())
           if d.replace(year=d.year - 1) in cpi]
    jobs = [(d, v - pv) for (pd, pv), (d, v) in zip(pay, pay[1:])
            if (d.year * 12 + d.month) - (pd.year * 12 + pd.month) == 1]
    yoy, jobs = yoy[-48:], jobs[-48:]
    if len(yoy) < 24 or len(jobs) < 24:
        raise LookupError("too few months")
    asof = max(yoy[-1][0], jobs[-1][0])
    return asof, "BLS, FRED", {"cpi_month": yoy[-1][0].isoformat(), "jobs_month": jobs[-1][0].isoformat(),
                               "cpi": [[d.isoformat(), round(v, 2)] for d, v in yoy],
                               "jobs": [[d.isoformat(), round(v)] for d, v in jobs]}


# Yahoo Finance --------------------------------------------------------------

def yahoo(symbol, rng="6mo"):
    """[(session date, close)] from Yahoo's chart endpoint, dates in the exchange's zone.

    A bar for a session still trading (or within 30 minutes of its close) is
    dropped: its "close" would be an intraday price.
    """
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?"
           + urllib.parse.urlencode({"range": rng, "interval": "1d"}))
    res = json.loads(get(url))["chart"]["result"][0]
    meta = res["meta"]
    offset = meta.get("gmtoffset") or 0
    local = lambda t: dt.datetime.fromtimestamp(t + offset, dt.timezone.utc).date()  # noqa: E731
    out = {}
    for t, c in zip(res.get("timestamp") or [], res["indicators"]["quote"][0]["close"]):
        if c is not None and math.isfinite(c):
            out[local(t)] = c
    # The newest daily bar can carry no close while the meta has it.
    price, t = meta.get("regularMarketPrice"), meta.get("regularMarketTime")
    stamps = res.get("timestamp") or []
    if isinstance(price, (int, float)) and t and stamps and local(t) == local(stamps[-1]) and local(t) not in out:
        out[local(t)] = float(price)
    end = ((meta.get("currentTradingPeriod") or {}).get("regular") or {}).get("end")
    now = dt.datetime.now(dt.timezone.utc).timestamp()
    if end and now < end + 1800:
        out.pop(local(end), None)
    if not out:
        raise ValueError(f"{symbol}: no closes")
    return sorted(out.items())


# Cboe volatility indices by days to expiry.
# (Yahoo keeps no history for the one-year index, ^VIX1Y.)
VOL = [("^VIX9D", 9, "9D"), ("^VIX", 30, "1M"), ("^VIX3M", 93, "3M"), ("^VIX6M", 184, "6M")]


def tile_vol(_):
    series = {s: dict((yahoo(s, "3mo"))) for s, _, _ in VOL}
    days = sorted(set.intersection(*(set(v) for v in series.values())))
    if len(days) < 6:
        raise LookupError("too few common sessions")
    now, then = days[-1], days[-6]
    return now, "Cboe, Yahoo Finance", {"then": then.isoformat(), "days": [n for _, n, _ in VOL],
                                         "labels": [lb for _, _, lb in VOL],
                                         "now": [series[s][now] for s, _, _ in VOL],
                                         "before": [series[s][then] for s, _, _ in VOL]}


def tile_commodities(_):
    oil, gold = dict((yahoo("CL=F", "6mo"))), dict((yahoo("GC=F", "6mo")))
    days = sorted(set(oil) & set(gold))[-90:]
    if len(days) < 30:
        raise LookupError("too few common sessions")
    return days[-1], "Futures, Yahoo Finance", {
        "start": days[0].isoformat(),
        "oil": [round(oil[d] / oil[days[0]] * 100, 2) for d in days],
        "gold": [round(gold[d] / gold[days[0]] * 100, 2) for d in days]}


# Each at its own latest local close: the agent's facts flag Asian closes as
# another session, so this tile reads Yahoo directly.
INDICES = [("^GSPC", "S&P 500"), ("^STOXX50E", "Euro Stoxx 50"), ("^GDAXI", "DAX 40"),
           ("^FTSE", "FTSE 100"), ("^N225", "Nikkei 225"), ("^HSI", "Hang Seng"),
           ("^BVSP", "Bovespa"), ("^GSPTSE", "S&P/TSX")]


def tile_indices(_):
    rows, asof = [], None
    for sym, name in INDICES:
        (_, a), (d1, b) = yahoo(sym, "1mo")[-2:]
        rows.append([name, round((b / a - 1) * 100, 3), d1.isoformat()])
        asof = max(asof or d1, d1)
    return asof, "Yahoo Finance, local closes", {"rows": sorted(rows, key=lambda r: -r[1])}


CORR = [("^GSPC", "S&P 500"), ("TLT", "Long Treasuries"), ("DX-Y.NYB", "Dollar index"),
        ("CL=F", "WTI crude"), ("GC=F", "Gold")]


def tile_correlation(_):
    series = [dict((yahoo(s, "6mo"))) for s, _ in CORR]
    days = sorted(set.intersection(*(set(v) for v in series)))[-61:]
    if len(days) < 41:
        raise LookupError("too few common sessions")
    rets = [[math.log(s[b] / s[a]) for a, b in zip(days, days[1:])] for s in series]

    def corr(x, y):
        mx, my = sum(x) / len(x), sum(y) / len(y)
        sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
        sxx, syy = sum((a - mx) ** 2 for a in x), sum((b - my) ** 2 for b in y)
        return sxy / math.sqrt(sxx * syy)

    m = [[round(corr(a, b), 2) for b in rets] for a in rets]
    return days[-1], "Yahoo Finance, daily returns", {"names": [n for _, n in CORR], "matrix": m,
                                                      "sessions": len(days) - 1}


MONTH_CODES = "FGHJKMNQUVXZ"


def tile_fed(_):
    """30-day fed funds futures: 100 minus the price is the month's expected average rate."""
    today = dt.date.today()
    months, asof = [], None
    for i in range(12):
        y, m = divmod(today.month - 1 + i, 12)
        y += today.year
        sym = f"ZQ{MONTH_CODES[m]}{y % 100:02d}.CBT"
        try:
            day, price = (yahoo(sym, "1mo"))[-1]
        except Exception:  # noqa: BLE001  a contract Yahoo does not list ends the path
            break
        months.append([f"{y}-{m + 1:02d}", round(100 - price, 3)])
        asof = max(asof or day, day)
    if len(months) < 6:
        raise LookupError("too few fed funds futures")
    effr = fred(["EFFR"], today - dt.timedelta(days=20))["EFFR"][-1]
    return asof, "CME futures, Yahoo Finance; FRED", {
        "months": months, "effr": effr[1], "effr_date": effr[0].isoformat()}


TILES = {
    "yield_curve": ("archive", tile_curve),
    "fed_path": (None, tile_fed),
    "sector_heatmap": ("archive", tile_sectors),
    "vol_term": (None, tile_vol),
    "global_indices": ("archive", tile_indices),
    "fx_majors": ("archive", tile_fx),
    "commodities": (None, tile_commodities),
    "credit_spreads": (None, tile_credit),
    "inflation_labour": (None, tile_inflation),
    "correlation": (None, tile_correlation),
}


def main():
    try:
        tiles = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        tiles = {}
    archive = None
    try:
        archive = Archive(os.environ.get("AGENT_ARTIFACTS_TOKEN"))
    except Exception as e:  # noqa: BLE001
        log(f"Agent archive unavailable ({type(e).__name__}: {e}); archive tiles keep their last record. "
            "The token needs Contents: read on the agent repo.", "warning")
    for key, (needs, fn) in TILES.items():
        if needs == "archive" and archive is None:
            continue
        try:
            asof, source, data = fn(archive)
        except Exception as e:  # noqa: BLE001  one source failing never stops the deploy
            kept = tiles.get(key, {}).get("asof", "none")
            log(f"{key}: {type(e).__name__}: {e}; keeping the last record ({kept})", "warning")
            continue
        tiles[key] = {"asof": asof.isoformat(), "source": source, "data": data,
                      "fetched": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
        print(f"{key}: {source}, {asof}")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(tiles, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
