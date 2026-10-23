#!/usr/bin/env python3
"""Fetch the figures behind the dashboard tiles, at deploy time.

Run by .github/workflows/pages.yml before tools/build_site.py. Writes one
small file, .cache/dashboards/tiles.json: for each tile, the few numbers its
chart draws, the history its dashboard page draws, the source and the as-of
date. build_site.py reads it; a dashboard with no record says "Data pending".

Sources:
    the agent's archive   releases archive-YYYY-MM-DD in the agent repo; only
                          the facts of the run behind a published note, on an
                          NYSE trading day, and never a series the facts mark
                          as not yet published or from another session
    FRED                  the official API (api.stlouisfed.org), with FRED_API_KEY
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
    FRED_API_KEY           FRED API key (repository secret); never printed: any
                           error naming the request has it replaced by ***
"""
import datetime as dt
import json
import math
import os
import re
import sys
import urllib.error
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


# Ranges on the dashboard pages. A series shorter than a range is offered up
# to the first range it does not fully cover, which then shows all it has.
RANGES = [("1M", 1), ("3M", 3), ("6M", 6), ("1Y", 12)]


def months_back(d, n):
    y, m = divmod(d.month - 1 - n, 12)
    y += d.year
    m += 1
    return d.replace(year=y, month=m, day=min(d.day, [31, 29 if y % 4 == 0 and (y % 100 or y % 400 == 0) else 28,
                                                         31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]))


def at_or_before(days, d):
    """The last date in sorted days on or before d, or None."""
    best = None
    for x in days:
        if x > d:
            break
        best = x
    return best


def offered(first, last, ranges=RANGES):
    """Range labels the history from first to last can show (see RANGES)."""
    out = []
    for label, n in ranges:
        out.append(label)
        if months_back(last, n) < first:
            break
    return out


def iso(d):
    return d.isoformat()


def perf(series, names, sign=None):
    """Changes over 1D and each range, each instrument from its own latest close."""
    sign = sign or [1] * len(series)
    out = {}
    for label, n in [("1D", 0)] + RANGES:
        vals, frm, to = [], [], []
        for s, k in zip(series, sign):
            days = [d for d, _ in s]
            last_d, last = s[-1]
            base_d = days[-2] if n == 0 else at_or_before(days, months_back(last_d, n))
            if base_d is None:  # history too short for this range
                vals = None
                break
            base = dict(s)[base_d]
            vals.append(round(k * (last / base - 1) * 100, 3))
            frm.append(iso(base_d))
            to.append(iso(last_d))
        if vals is None:
            break
        out[label] = {"values": vals, "from": frm, "to": to}
    return {"kind": "perf", "names": names, "ranges": out}


def history(series, names, on=None, dec=2):
    """Every instrument's daily closes on one shared date axis (the union of
    their sessions, None where one did not trade), for the page's own ranges,
    comparison dates and views. on: shown when the page opens."""
    days = sorted(set().union(*(set(d for d, _ in s) for s in series)))
    out = []
    for i, (s, n) in enumerate(zip(series, names)):
        by = dict(s)
        out.append({"name": n, "values": [round(by[d], dec) if d in by else None for d in days],
                    "on": True if on is None else bool(on[i])})
    return {"dates": [iso(d) for d in days], "series": out}


SECTORS = [("XLK", "Technology"), ("XLF", "Financials"), ("XLV", "Health care"),
           ("XLY", "Cons. discretionary"), ("XLP", "Cons. staples"), ("XLE", "Energy"),
           ("XLI", "Industrials"), ("XLB", "Materials"), ("XLRE", "Real estate"),
           ("XLU", "Utilities"), ("XLC", "Communications")]
# Majors against the dollar; -1 where the dollar is the quote currency
# (EUR/USD), so the dollar's own move is the opposite sign.
FX = [("EURUSD=X", "Euro", -1), ("JPY=X", "Japanese yen", 1), ("GBPUSD=X", "Pound", -1),
      ("CHF=X", "Swiss franc", 1), ("CAD=X", "Canadian dollar", 1), ("AUDUSD=X", "Australian dollar", -1)]


def perf_tile(spec, source, sign=None, dated=False, extra=(), dec=2):
    """Changes over each range for the tile's instruments (spec), and a page
    history that adds the extra ones (off when the page opens)."""
    series = [yahoo(sym, "2y") for sym, *_ in spec]
    names = [x[1] for x in spec]
    detail = perf(series, names, sign)
    day = detail["ranges"]["1D"]
    rows = [[n, v] + ([t] if dated else []) for n, v, t in zip(names, day["values"], day["to"])]
    asof = max(dt.date.fromisoformat(t) for t in day["to"])
    more = []
    for x in extra:
        try:
            more.append((x, yahoo(x[0], "2y")))
        except Exception as e:  # noqa: BLE001  a missing extra never loses the tile
            log(f"{x[0]}: {type(e).__name__}: {e}; left off the page", "warning")
    allspec, allseries = list(spec) + [x for x, _ in more], series + [sr for _, sr in more]
    detail["hist"] = history(allseries, [x[1] for x in allspec], [True] * len(spec) + [False] * len(more), dec)
    if sign:
        detail["hist"]["sign"] = list(sign) + [x[2] for x, _ in more]
    return asof, source, {"rows": sorted(rows, key=lambda r: -r[1])}, detail


def tile_sectors(_):
    return perf_tile(SECTORS, "Yahoo Finance, sector ETFs", extra=[("SPY", "S&P 500 (SPY)")])


# Further currencies on the page (off when it opens): the other G10 and the
# main emerging-market currencies, each as the dollar's move.
FX_MORE = [("NZDUSD=X", "New Zealand dollar", -1), ("SEK=X", "Swedish krona", 1), ("NOK=X", "Norwegian krone", 1),
           ("CNY=X", "Chinese yuan", 1), ("MXN=X", "Mexican peso", 1), ("INR=X", "Indian rupee", 1),
           ("BRL=X", "Brazilian real", 1), ("KRW=X", "Korean won", 1), ("ZAR=X", "South African rand", 1),
           ("DX-Y.NYB", "Dollar index (DXY)", 1)]


def tile_fx(_):
    return perf_tile(FX, "Yahoo Finance", [k for *_, k in FX], extra=FX_MORE, dec=4)


def tile_breadth(archive):
    """Advancers and decliners across the agent's watchlist, session by session."""
    rows = []
    for day, facts in archive.sessions(len(archive.runs)):
        b = facts.get("breadth") if isinstance(facts.get("breadth"), dict) else {}
        adv, dec, unch = (b.get(k) for k in ("advancers", "decliners", "unchanged"))
        if all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in (adv, dec, unch)) and adv + dec:
            rows.append([day.isoformat(), adv, dec, unch])
    rows = rows[::-1]
    if len(rows) < 10:
        raise LookupError("too few sessions with breadth")
    first, last = dt.date.fromisoformat(rows[0][0]), dt.date.fromisoformat(rows[-1][0])
    return last, "Andra Markets watchlist, Yahoo Finance", {"sessions": rows[-30:], "size": sum(rows[-1][1:])}, {
        "kind": "breadth", "sessions": rows, "ranges": offered(first, last)}


def curve_at(day, facts):
    """(as-of date, {tenor key: yield}) from one session's facts, or None."""
    cv = charts(facts)["curve"]
    pts = {c["key"]: c["last"] for c in cv if c["last"] is not None}
    if len(pts) < 8 or len({c["stale"] for c in cv}) > 1:
        return None
    # FRED posts the curve after the agent runs: the facts then carry the
    # session before's curve, flagged as not yet published.
    return (prev_session(day) if cv[0]["stale"] else day), pts


def compare(curves, keys, labels, x):
    """Latest curve against the curve on or before each range's start."""
    days = sorted(curves)
    now = days[-1]
    cmp = {}
    for label, n in RANGES:
        then = at_or_before(days, months_back(now, n))
        if then is None or (months_back(now, n) - then).days > 7:
            break
        cmp[label] = {"date": iso(then), "values": [curves[then][k] for k in keys]}
    if not cmp:
        raise LookupError("no curve a month before the latest")
    return now, {"kind": "curve", "labels": labels, "x": x, "date": iso(now),
                 "values": [curves[now][k] for k in keys], "compare": cmp}


TENORS = [("ust1m", "DGS1MO", "1M", 1 / 12), ("ust3m", "DGS3MO", "3M", 0.25), ("ust6m", "DGS6MO", "6M", 0.5),
          ("ust1y", "DGS1", "1Y", 1), ("ust2y", "DGS2", "2Y", 2), ("ust3y", "DGS3", "3Y", 3),
          ("ust5y", "DGS5", "5Y", 5), ("ust7y", "DGS7", "7Y", 7), ("ust10y", "DGS10", "10Y", 10),
          ("ust20y", "DGS20", "20Y", 20), ("ust30y", "DGS30", "30Y", 30)]


def tile_curve(archive):
    """FRED's Treasury yields; while FRED is down, the curves in the agent's archive."""
    try:
        s = fred([f for _, f, _, _ in TENORS], months_back(dt.date.today(), 25))
        by = {}
        for key, f, _, _ in TENORS:
            for d, v in s[f]:
                by.setdefault(d, {})[key] = v
        curves = {d: c for d, c in by.items() if len(c) == len(TENORS)}
        source = "FRED, US Treasury"
    except (OSError, ValueError):
        if archive is None:
            raise
        curves = {}
        for day, facts in archive.sessions(len(archive.runs)):
            c = curve_at(day, facts)
            if c and all(k in c[1] for k, *_ in TENORS):
                curves.setdefault(c[0], c[1])
        source = "FRED, US Treasury, via the Andra Markets archive"
    keys = [k for k, *_ in TENORS]
    now, detail = compare(curves, keys, [lb for *_, lb, _ in TENORS], [math.sqrt(t) for *_, t in TENORS])
    detail["unit"], detail["dec"] = "%", 2
    lbs = [lb for *_, lb, _ in TENORS]
    detail["hist"] = curve_history(curves, keys, lbs, ["3M", "2Y", "10Y", "30Y"], 3)
    # Spreads over time, in basis points: the page's second view.
    days = sorted(curves)
    detail["spreads"] = {"dates": detail["hist"]["dates"], "unit": "bp", "series": [
        {"name": name, "values": [round((curves[d][keys[lbs.index(a)]] - curves[d][keys[lbs.index(b)]]) * 100, 1) for d in days],
         "on": on} for name, a, b, on in (("10Y less 2Y", "10Y", "2Y", True), ("10Y less 3M", "10Y", "3M", True),
                                          ("30Y less 5Y", "30Y", "5Y", False), ("2Y less 3M", "2Y", "3M", False))]}
    month = detail["compare"]["1M"]
    return now, source, {"then": month["date"], "tenors": keys, "now": detail["values"],
                         "before": month["values"]}, detail


def curve_history(curves, keys, labels, on, dec):
    """Every day's curve, one series per point on it: the page's comparison
    dates and its over-time view."""
    days = sorted(curves)
    return {"dates": [iso(d) for d in days],
            "series": [{"name": lb, "values": [round(curves[d][k], dec) for d in days], "on": lb in on}
                       for k, lb in zip(keys, labels)]}


# FRED -----------------------------------------------------------------------

FRED_DOWN = []


def fred(series, start):
    """{series: [(date, value)]} from the FRED API, skipping missing values."""
    if FRED_DOWN:
        raise FRED_DOWN[0]
    try:
        return _fred(series, start)
    except FredError as e:
        if e.outage:
            FRED_DOWN.append(e)  # one outage: don't wait on every later series
        raise


FRED_API = "https://api.stlouisfed.org/fred/series/observations"


class FredError(ValueError):
    """A FRED failure whose message never carries the API key. outage is False
    when FRED answered but refused one series, so the others are still tried."""

    def __init__(self, message, outage=True):
        super().__init__(message)
        self.outage = outage


def _fred(series, start):
    key = os.environ.get("FRED_API_KEY", "").strip()
    if not key:
        raise FredError("FRED_API_KEY is not set")

    def hide(text):
        return str(text).replace(key, "***")

    out = {}
    for sid in series:
        q = urllib.parse.urlencode({"series_id": sid, "observation_start": start.isoformat(),
                                    "file_type": "json", "api_key": key})
        req = urllib.request.Request(f"{FRED_API}?{q}", headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                raw = r.read(MAX_JSON + 1)
        except urllib.error.HTTPError as e:
            try:  # FRED says why, e.g. "Bad Request. The series does not exist."
                why = json.loads(e.read(4096)).get("error_message", "")
            except Exception:  # noqa: BLE001
                why = ""
            raise FredError(hide(f"FRED {sid}: HTTP {e.code} {why}".strip()), outage=e.code >= 500) from None
        except (OSError, ValueError) as e:
            raise FredError(hide(f"FRED {sid}: {type(e).__name__}: {e}")) from None
        if len(raw) > MAX_JSON:
            raise FredError(f"FRED {sid}: response too large")
        rows = []
        for o in json.loads(raw).get("observations", []):
            try:
                v = float(o["value"])  # "." marks a missing observation
            except (KeyError, ValueError):
                continue
            if math.isfinite(v):
                rows.append((dt.date.fromisoformat(o["date"]), v))
        if not rows:
            raise FredError(f"FRED {sid}: no observations", outage=False)
        out[sid] = rows
    return out


# Further ICE BofA option-adjusted spreads on the page, off when it opens.
CREDIT_MORE = [("BAMLC0A4CBBB", "BBB corporate"), ("BAMLH0A1HYBB", "BB high yield"),
               ("BAMLH0A3HYC", "CCC and lower"), ("BAMLHE00EHYIOAS", "Euro high yield"),
               ("BAMLEMCBPIOAS", "Emerging markets corporate")]


def tile_credit(_):
    today = dt.date.today()
    s = fred(["BAMLH0A0HYM2", "BAMLC0A0CM"], months_back(today, 25))
    hy, ig = dict(s["BAMLH0A0HYM2"]), dict(s["BAMLC0A0CM"])
    days = sorted(set(hy) & set(ig))
    if len(days) < 20:
        raise LookupError("too few common observations")
    tile = days[-120:]
    return days[-1], "ICE BofA, FRED", {
        "start": iso(tile[0]), "hy": [hy[d] for d in tile], "ig": [ig[d] for d in tile]}, {
        "kind": "lines", "dates": [iso(d) for d in days], "ranges": offered(days[0], days[-1], RANGES_2Y),
        "series": [{"name": "High yield", "style": "line", "values": [hy[d] for d in days], "on": True},
                   {"name": "Investment grade", "style": "dash", "values": [ig[d] for d in days], "area": True, "on": True}]
        + credit_more(days, today), "unit": "%", "dec": 2}


def credit_more(days, today):
    out = []
    for sid, name in CREDIT_MORE:
        try:
            vals = carried(dict(fred([sid], months_back(today, 25))[sid]), days)
        except (OSError, ValueError) as e:
            log(f"{sid}: {e}; left off the page", "warning")
            continue
        if vals[0] is not None:
            out.append({"name": name, "values": vals, "on": False})
    return out


def tile_inflation(_):
    today = dt.date.today()
    s = fred(["CPIAUCSL", "PAYEMS"], months_back(today.replace(day=1), 12 * 6 + 2))
    cpi, pay = dict(s["CPIAUCSL"]), s["PAYEMS"]
    yoy = [(d, (v / cpi[d.replace(year=d.year - 1)] - 1) * 100) for d, v in sorted(cpi.items())
           if d.replace(year=d.year - 1) in cpi]
    jobs = dict((d, v - pv) for (pd, pv), (d, v) in zip(pay, pay[1:])
                if (d.year * 12 + d.month) - (pd.year * 12 + pd.month) == 1)
    yoy = yoy[-60:]
    if len(yoy) < 24 or len(jobs) < 24:
        raise LookupError("too few months")
    months = sorted(set(d for d, _ in yoy) | set(d for d in jobs if d >= yoy[0][0]))
    cpi_y = dict(yoy)
    last_job = max(jobs)
    asof = max(yoy[-1][0], last_job)
    tile_jobs = sorted(jobs.items())[-48:]
    return asof, "BLS, FRED", {"cpi_month": iso(yoy[-1][0]), "jobs_month": iso(last_job),
                               "cpi": [[iso(d), round(v, 2)] for d, v in yoy[-48:]],
                               "jobs": [[iso(d), round(v)] for d, v in tile_jobs]}, {
        "kind": "macro", "dates": [iso(d) for d in months],
        "cpi": [round(cpi_y[d], 2) if d in cpi_y else None for d in months],
        "jobs": [round(jobs[d]) if d in jobs else None for d in months],
        "ranges": [lb for lb, n in (("1Y", 12), ("2Y", 24), ("5Y", 60)) if len(months) >= n - 1]}


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
    series = {s: dict(yahoo(s, "2y")) for s, _, _ in VOL}
    days = sorted(set.intersection(*(set(v) for v in series.values())))
    if len(days) < 6:
        raise LookupError("too few common sessions")
    curves = {d: {s: series[s][d] for s, _, _ in VOL} for d in days}
    now, detail = compare(curves, [s for s, _, _ in VOL], [lb for *_, lb in VOL],
                          [math.sqrt(n) for _, n, _ in VOL])
    detail["unit"], detail["dec"] = "", 2
    then = days[-6]
    detail["compare"] = {"1W": {"date": iso(then), "values": [series[s][then] for s, _, _ in VOL]}, **detail["compare"]}
    detail["hist"] = curve_history(curves, [s for s, _, _ in VOL], [lb for *_, lb in VOL], ["1M", "3M"], 2)
    # Over time, besides the four expiries: the one-day index, the volatility
    # of the VIX itself, and the slope from one month to three.
    for sym, name in (("^VIX1D", "VIX 1-day"), ("^VVIX", "VVIX")):
        try:
            h = dict(yahoo(sym, "2y"))
            detail["hist"]["series"].append({"name": name, "on": False,
                                             "values": [round(h[d], 2) if d in h else None for d in days]})
        except Exception as e:  # noqa: BLE001
            log(f"{sym}: {type(e).__name__}: {e}; left off the page", "warning")
    detail["hist"]["series"].append({"name": "VIX less VIX 3-month", "on": False,
                                     "values": [round(series["^VIX"][d] - series["^VIX3M"][d], 2) for d in days]})
    return now, "Cboe, Yahoo Finance", {"then": iso(then), "days": [n for _, n, _ in VOL],
                                         "labels": [lb for _, _, lb in VOL],
                                         "now": [series[s][now] for s, _, _ in VOL],
                                         "before": [series[s][then] for s, _, _ in VOL]}, detail


# Further front-month futures on the page, off when it opens: (symbol, name, decimals).
COMMODITIES_MORE = [("BZ=F", "Brent crude", 2), ("NG=F", "Natural gas", 3), ("SI=F", "Silver", 2),
                    ("HG=F", "Copper", 3), ("PL=F", "Platinum", 1), ("ZC=F", "Corn", 2), ("ZW=F", "Wheat", 2)]
RANGES_2Y = RANGES + [("2Y", 24)]


def carried(h, days):
    """A series' value on each day; its last value before a day it skipped."""
    out, last = [], None
    for d in days:
        last = h.get(d, last)
        out.append(last)
    return out


def tile_commodities(_):
    oil, gold = dict(yahoo("CL=F", "2y")), dict(yahoo("GC=F", "2y"))
    days = sorted(set(oil) & set(gold))
    days = [d for d in days if d >= months_back(days[-1], 25)]
    if len(days) < 30:
        raise LookupError("too few common sessions")
    tile = days[-90:]
    series = [{"name": "WTI crude", "style": "line", "values": [round(oil[d], 2) for d in days], "dec": 2, "on": True},
              {"name": "Gold", "style": "dash", "values": [round(gold[d], 1) for d in days], "dec": 1, "on": True}]
    for sym, name, dec in COMMODITIES_MORE:
        try:
            vals = carried(dict(yahoo(sym, "2y")), days)
        except Exception as e:  # noqa: BLE001
            log(f"{sym}: {type(e).__name__}: {e}; left off the page", "warning")
            continue
        if vals[0] is not None:
            series.append({"name": name, "values": [round(v, dec) for v in vals], "dec": dec, "on": False})
    return days[-1], "Futures, Yahoo Finance", {
        "start": iso(tile[0]),
        "oil": [round(oil[d] / oil[tile[0]] * 100, 2) for d in tile],
        "gold": [round(gold[d] / gold[tile[0]] * 100, 2) for d in tile]}, {
        "kind": "lines", "rebase": True, "dates": [iso(d) for d in days], "ranges": offered(days[0], days[-1], RANGES_2Y),
        "series": series}


# Each at its own latest local close: the agent's facts flag Asian closes as
# another session, so this tile reads Yahoo directly.
INDICES = [("^GSPC", "S&P 500"), ("^STOXX50E", "Euro Stoxx 50"), ("^GDAXI", "DAX 40"),
           ("^FTSE", "FTSE 100"), ("^N225", "Nikkei 225"), ("^HSI", "Hang Seng"),
           ("^BVSP", "Bovespa"), ("^GSPTSE", "S&P/TSX")]


INDICES_MORE = [("^NDX", "Nasdaq 100"), ("^RUT", "Russell 2000"), ("^FCHI", "CAC 40"), ("^IBEX", "IBEX 35"),
                ("FTSEMIB.MI", "FTSE MIB"), ("^SSMI", "SMI"), ("^KS11", "KOSPI"), ("^TWII", "TAIEX"),
                ("^NSEI", "Nifty 50"), ("^AXJO", "S&P/ASX 200"), ("000001.SS", "Shanghai Composite"), ("^MXX", "IPC Mexico")]


def tile_indices(_):
    return perf_tile(INDICES, "Yahoo Finance, local closes", dated=True, extra=INDICES_MORE)


CORR = [("^GSPC", "S&P 500"), ("TLT", "Long Treasuries"), ("DX-Y.NYB", "Dollar index"),
        ("CL=F", "WTI crude"), ("GC=F", "Gold")]
WINDOWS = [("1M", 21), ("3M", 63), ("6M", 126), ("1Y", 250)]


def corr_matrix(rets):
    def corr(x, y):
        mx, my = sum(x) / len(x), sum(y) / len(y)
        sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
        sxx, syy = sum((a - mx) ** 2 for a in x), sum((b - my) ** 2 for b in y)
        return sxy / math.sqrt(sxx * syy)
    return [[round(corr(a, b), 2) for b in rets] for a in rets]


def tile_correlation(_):
    series = [dict(yahoo(s, "2y")) for s, _ in CORR]
    days = sorted(set.intersection(*(set(v) for v in series)))
    if len(days) < 41:
        raise LookupError("too few common sessions")
    rets = [[math.log(s[b] / s[a]) for a, b in zip(days, days[1:])] for s in series]
    windows = {}
    for label, n in WINDOWS:
        if len(rets[0]) < n:
            break
        windows[label] = {"sessions": n, "from": iso(days[-n - 1]), "matrix": corr_matrix([r[-n:] for r in rets])}
    tile = corr_matrix([r[-60:] for r in rets])
    names = [n for _, n in CORR]
    return days[-1], "Yahoo Finance, daily returns", {"names": names, "matrix": tile, "sessions": 60}, {
        "kind": "matrix", "names": names, "windows": windows}


MONTH_CODES = "FGHJKMNQUVXZ"


def tile_fed(_):
    """30-day fed funds futures: 100 minus the price is the month's expected average rate."""
    today = dt.date.today()
    months, hist = [], []
    for i in range(12):
        y, m = divmod(today.month - 1 + i, 12)
        y += today.year
        sym = f"ZQ{MONTH_CODES[m]}{y % 100:02d}.CBT"
        try:
            h = dict(yahoo(sym, "2y"))
        except Exception:  # noqa: BLE001  a contract Yahoo does not list ends the path
            break
        months.append(f"{y}-{m + 1:02d}")
        hist.append(h)
    if len(months) < 6:
        raise LookupError("too few fed funds futures")
    # A date counts when every contract on the path settled that day.
    days = sorted(set.intersection(*(set(h) for h in hist)))
    curves = {d: {mo: round(100 - h[d], 3) for mo, h in zip(months, hist)} for d in days}
    now, detail = compare(curves, months, [f"{dt.date.fromisoformat(mo + '-01'):%b %y}" for mo in months],
                          list(range(len(months))))
    detail["unit"], detail["dec"] = "%", 3
    try:
        effr = fred(["EFFR"], today - dt.timedelta(days=20))["EFFR"][-1]
        detail["ref"] = {"name": "Effective rate", "value": effr[1], "date": iso(effr[0])}
        source = "CME futures, Yahoo Finance; FRED"
    except (OSError, ValueError):
        effr, source = None, "CME futures, Yahoo Finance"
    tile = {"months": [[mo, v] for mo, v in zip(months, detail["values"])]}
    if effr:
        tile.update(effr=effr[1], effr_date=iso(effr[0]))
    return now, source, tile, detail


TILES = {
    "yield_curve": (None, tile_curve),
    "fed_path": (None, tile_fed),
    "sector_heatmap": (None, tile_sectors),
    "breadth": ("archive", tile_breadth),
    "vol_term": (None, tile_vol),
    "global_indices": (None, tile_indices),
    "fx_majors": (None, tile_fx),
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
        why = f"{type(e).__name__}: {e}"
        if isinstance(e, urllib.error.HTTPError):
            try:  # GitHub says why, e.g. "Resource not accessible by personal access token"
                why += f" ({json.loads(e.read(4096)).get('message')})"
            except Exception:  # noqa: BLE001
                pass
        log(f"Agent archive unavailable, {why}; archive tiles keep their last record or show as pending. "
            "Reading releases needs Contents: read on the agent repo for AGENT_ARTIFACTS_TOKEN.", "warning")
    for key, (needs, fn) in TILES.items():
        if needs == "archive" and archive is None:
            continue
        try:
            asof, source, data, detail = fn(archive)
        except Exception as e:  # noqa: BLE001  one source failing never stops the deploy
            kept = tiles.get(key, {}).get("asof", "none")
            log(f"{key}: {type(e).__name__}: {e}; keeping the last record ({kept})", "warning")
            continue
        tiles[key] = {"asof": asof.isoformat(), "source": source, "data": data, "detail": detail,
                      "fetched": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
        print(f"{key}: {source}, {asof}")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(tiles, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
