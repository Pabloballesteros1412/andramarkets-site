#!/usr/bin/env python3
"""Fetch the figures behind Central banks (central-banks/), at deploy time.

Run by .github/workflows/pages.yml before tools/build_site.py. Writes one
file, .cache/centralbanks/centralbanks.json: each bank's policy rate as the
days it changed (from 2015, so the chart's 2019 start and the last move are
always covered), its source and as-of date, and each bank's rate decisions
over the year ahead. tools/page_central_banks.py embeds what the page draws;
nothing here is published as a file.

Sources, each fetched on its own:
    Federal Reserve  the target range, FRED DFEDTARU and DFEDTARL (the Board's
                     own series), with FRED_API_KEY
    ECB              the deposit facility rate, from the ECB Data Portal
                     (FM.B.U2.EUR.4F.KR.DFR.LEV, the dates it changed); FRED
                     ECBDFR when the portal does not answer
    Bank of England  Bank Rate, from the Bank's database (IUDBEDR, daily); the
                     BIS series for the United Kingdom when it does not answer
    Bank of Japan    the BIS central bank policy rate series for Japan
                     (WS_CBPOL, daily), compiled from the Bank of Japan's
                     announcements
    Decision dates   each bank's own calendar, read with the parsers of
                     tools/calendar_data.py over the year ahead (the calendar
                     itself keeps five weeks, and the next meeting is often
                     further away than that)

A block whose source fails keeps its last good copy (restored by the
workflow's cache) with its own date; a failure never stops the deploy. No
figure is ever typed in by hand: a bank with no copy yet shows "Data pending".

    python3 tools/centralbanks_data.py

Environment:
    FRED_API_KEY  FRED API key (repository secret); never printed
"""
import contextlib
import csv
import datetime as dt
import io
import json
import math
import sys
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dashboard_data import fred, get, log  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "centralbanks" / "centralbanks.json"
NY = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
START = dt.date(2015, 1, 1)  # history kept; the page draws from 2019
AHEAD = 400  # days of decision dates read ahead
MAX = 40 * 1024 * 1024  # the BIS bulk file is the largest answer

ECB_URL = "https://data-api.ecb.europa.eu/service/data/FM/B.U2.EUR.4F.KR.DFR.LEV?format=csvdata"
BOE_URL = ("https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes&"
           + urllib.parse.urlencode({"Datefrom": START.strftime("%d/%b/%Y"), "Dateto": "now", "SeriesCodes": "IUDBEDR",
                                     "CSVF": "TN", "UsingCodes": "Y", "VPD": "Y", "VFD": "N"}))
# The BIS data API (SDMX), then its bulk file. The API answers SDMX-CSV or
# SDMX-ML; sdmx_series() reads either, so the request asks for CSV first.
# Areas: US, XM (euro area), GB, JP; the page uses GB (as backup) and JP.
BIS_API = ("https://stats.bis.org/api/v1/data/WS_CBPOL/D.US+XM+GB+JP/all?"
           + urllib.parse.urlencode({"startPeriod": START.isoformat(), "detail": "dataonly"}))
BIS_URLS = [BIS_API + "&format=csv", BIS_API, "https://data.bis.org/static/bulk/WS_CBPOL_csv_flat.zip"]
BIS_ACCEPT = ("application/vnd.sdmx.data+csv;version=1.0.0, text/csv;q=0.9, "
              "application/vnd.sdmx.structurespecificdata+xml;version=2.1;q=0.8, */*;q=0.5")


def iso(d):
    return d.isoformat()


def now_utc():
    return dt.datetime.now(UTC)


def today_ny():
    return dt.datetime.now(NY).date()


# Parsing -----------------------------------------------------------------------

def number(s):
    try:
        v = float(str(s).strip())
    except ValueError:
        return None
    return v if math.isfinite(v) else None


def day(s):
    """A date from 'YYYY-MM-DD' (an SDMX daily period), else None."""
    try:
        return dt.date.fromisoformat(str(s).strip()[:10])
    except ValueError:
        return None


def code(s):
    """'JP' from 'JP' or 'JP: Japan' (the bulk files add labels to codes)."""
    return str(s).split(":", 1)[0].strip()


def local(tag):
    return tag.rsplit("}", 1)[-1]


def sdmx_series(raw):
    """{REF_AREA: [(date, value)]} from an SDMX answer: SDMX-CSV (also the bulk
    file's flat CSV, whose headers and codes may carry labels) or SDMX-ML,
    structure-specific or generic. Only observations dated to the day are kept
    (daily and business-day series; a monthly period reads "2024-03")."""
    text = raw.decode("utf-8-sig", "replace").lstrip()
    out = {}

    def add(area, t, v):
        d, x = day(t or ""), number(v if v is not None else "")
        if area and d and x is not None and len(str(t).strip()) == 10:
            out.setdefault(code(area), {})[d] = x

    if text.startswith("<"):
        if "<!ENTITY" in text[:4096]:
            raise ValueError("SDMX: refusing a document that declares entities")
        root = ET.fromstring(text)
        for series in root.iter():
            if local(series.tag) != "Series":
                continue
            area = series.attrib.get("REF_AREA")
            for v in series.iter():
                if area is None and local(v.tag) == "Value" and v.attrib.get("id") == "REF_AREA":
                    area = v.attrib.get("value")
            for obs in series:
                if local(obs.tag) != "Obs":
                    continue
                t, val = obs.attrib.get("TIME_PERIOD"), obs.attrib.get("OBS_VALUE")
                if t is None or val is None:
                    for c in obs.iter():
                        if local(c.tag) == "ObsDimension":
                            t = c.attrib.get("value")
                        elif local(c.tag) == "ObsValue":
                            val = c.attrib.get("value")
                add(area, t, val)
    else:
        rows = csv.reader(io.StringIO(text))
        head = [code(h).upper() for h in next(rows, [])]
        if "TIME_PERIOD" not in head or "OBS_VALUE" not in head:
            raise ValueError("SDMX: no TIME_PERIOD and OBS_VALUE columns")
        ti, vi = head.index("TIME_PERIOD"), head.index("OBS_VALUE")
        ai = head.index("REF_AREA") if "REF_AREA" in head else None
        for r in rows:
            if len(r) <= max(ti, vi):
                continue
            add(r[ai] if ai is not None and ai < len(r) else "_", r[ti], r[vi])
    if not out:
        raise ValueError("SDMX: no daily observations")
    return {a: sorted(v.items()) for a, v in out.items()}


def boe_rows(raw):
    """[(date, value)] from the Bank of England database's CSV ("02 Jan 2015,0.5")."""
    text = raw.decode("utf-8-sig", "replace")
    if text.lstrip().startswith("<"):
        raise ValueError("Bank of England: an HTML page, not the CSV")
    out = {}
    for r in csv.reader(io.StringIO(text)):
        if len(r) < 2:
            continue
        for fmt in ("%d %b %Y", "%d/%m/%Y", "%Y-%m-%d"):
            try:
                d = dt.datetime.strptime(r[0].strip(), fmt).date()
                break
            except ValueError:
                d = None
        v = number(r[1])
        if d and v is not None:
            out[d] = v
    if not out:
        raise ValueError("Bank of England: no Bank Rate in the CSV")
    return sorted(out.items())


# The record ---------------------------------------------------------------------

def check(rows, name, lo=-2.0, hi=25.0):
    if len(rows) < 2:
        raise ValueError(f"{name}: too few observations")
    bad = [v for _, v in rows if not lo <= v <= hi]
    if bad:
        raise ValueError(f"{name}: a value out of range ({bad[0]})")
    return rows


def steps(rows, start=START):
    """[(date, value)] (daily, or the days it changed) -> [[ISO date, value]]: the
    level in force on start, then every change after it."""
    out, prev = [], None
    for d, v in rows:
        v = round(v, 4)
        if d <= start:
            prev = v
            continue
        if not out:
            out.append([iso(start), prev] if prev is not None else [iso(d), v])
            if prev is None:
                prev = v
                continue
        if v != prev:
            out.append([iso(d), v])
            prev = v
    if not out and prev is not None:
        out.append([iso(start), prev])
    return out


def last_move(rows):
    """The latest change: {"date", "bp"} (bp to one decimal), or None."""
    for i in range(len(rows) - 1, 0, -1):
        a, b = round(rows[i - 1][1], 4), round(rows[i][1], 4)
        if a != b:
            return {"date": iso(rows[i][0]), "bp": round((b - a) * 100, 1)}
    return None


def record(rows, source, asof, extra=None):
    rec = {"level": round(rows[-1][1], 4), "steps": steps(rows), "last_move": last_move(rows), "asof": iso(asof),
           "source": source, "fetched": now_utc().isoformat(timespec="seconds")}
    rec.update(extra or {})
    return rec


# Banks ----------------------------------------------------------------------------

def r_fed():
    s = fred(["DFEDTARU", "DFEDTARL"], START - dt.timedelta(days=60))
    up, lo = check(s["DFEDTARU"], "Fed"), check(s["DFEDTARL"], "Fed")
    lower = dict(lo)
    if up[-1][0] not in lower:
        raise ValueError("Fed: the bounds end on different days")
    return record(up, "Federal Reserve via FRED (DFEDTARU, DFEDTARL)", up[-1][0],
                  {"lower": round(lower[up[-1][0]], 4), "lower_steps": steps(lo)})


def r_ecb():
    try:
        series = sdmx_series(cd().fetch(ECB_URL, headers={"Accept": "text/csv,*/*"}))
        rows = check(next(iter(series.values())), "ECB")
        # The portal lists the days the rate changed, so the level holds on the day it is read.
        return record(rows, "ECB Data Portal (FM.B.U2.EUR.4F.KR.DFR.LEV)", today_ny(), {"changes_only": True})
    except (OSError, ValueError, StopIteration) as e:
        log(f"centralbanks ecb: ECB Data Portal: {type(e).__name__}: {e}; trying FRED", "warning")
    rows = check(fred(["ECBDFR"], START - dt.timedelta(days=60))["ECBDFR"], "ECB")
    return record(rows, "ECB via FRED (ECBDFR)", rows[-1][0])


def r_boe():
    try:
        rows = check(boe_rows(cd().fetch(BOE_URL)), "BoE")
        return record(rows, "Bank of England database (IUDBEDR)", rows[-1][0])
    except (OSError, ValueError) as e:
        log(f"centralbanks boe: Bank of England database: {type(e).__name__}: {e}; trying the BIS", "warning")
    rows = check(bis()["GB"], "BoE")
    return record(rows, "BIS central bank policy rates (WS_CBPOL), United Kingdom", rows[-1][0])


def r_boj():
    rows = check(bis()["JP"], "BoJ")
    return record(rows, "BIS central bank policy rates (WS_CBPOL), Japan", rows[-1][0])


BIS_CACHE = {}


def bis():
    """{area: [(date, value)]} for the four areas, read once per run."""
    if "data" in BIS_CACHE:
        return BIS_CACHE["data"]
    if "error" in BIS_CACHE:
        raise BIS_CACHE["error"]
    errors = []
    for url in BIS_URLS:
        try:
            raw = get(url, headers={"Accept": BIS_ACCEPT}, limit=MAX)
            if url.endswith(".zip"):
                with zipfile.ZipFile(io.BytesIO(raw)) as z:
                    name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
                    raw = z.read(name)
            data = sdmx_series(raw)
            data = {a: [(d, v) for d, v in rows if d >= START - dt.timedelta(days=60)] for a, rows in data.items()}
            missing = [a for a in ("GB", "JP") if not data.get(a)]
            if missing:
                raise ValueError(f"no series for {', '.join(missing)}")
            BIS_CACHE["data"] = data
            return data
        except (OSError, ValueError, KeyError, StopIteration, ET.ParseError, zipfile.BadZipFile) as e:
            why = f"HTTP {e.code}" if isinstance(e, urllib.error.HTTPError) else f"{type(e).__name__}: {e}"
            errors.append(f"{url.split('?')[0]}: {why}")
    BIS_CACHE["error"] = LookupError("BIS: " + "; ".join(errors))
    raise BIS_CACHE["error"]


# Decision dates -------------------------------------------------------------------

def cd():
    import calendar_data
    return calendar_data


@contextlib.contextmanager
def year_ahead():
    """calendar_data's publishers keep the calendar's five weeks; read the year ahead."""
    mod = cd()
    keep = mod.window

    def wide():
        today = today_ny()
        return today, today - dt.timedelta(days=today.weekday()), today + dt.timedelta(days=AHEAD)
    mod.window = wide
    try:
        yield mod
    finally:
        mod.window = keep


def decisions(events, title):
    rows = sorted({(e["date"], e.get("utc")) for e in events if e.get("title") == title})
    if not rows:
        raise ValueError(f"no '{title}' on the calendar page")
    return [{"day": d, "utc": u} for d, u in rows]


def m_fed():
    meetings = sorted({b for _, b, _ in cd().fomc_meetings()})  # the Fed's page lists whole years
    today = today_ny()
    return [{"day": iso(b), "utc": dt.datetime(b.year, b.month, b.day, 14, 0, tzinfo=NY).astimezone(UTC).isoformat()}
            for b in meetings if today - dt.timedelta(days=7) <= b <= today + dt.timedelta(days=AHEAD)]


def m_ecb():
    with year_ahead() as mod:
        return decisions(mod.ecb(), "ECB rate decision")


def m_boe():
    with year_ahead() as mod:
        return decisions(mod.boe(), "Bank of England rate decision and minutes")


def m_boj():
    with year_ahead() as mod:
        return decisions(mod.boj(), "Bank of Japan rate decision")


# Main ---------------------------------------------------------------------------------

def main():
    try:
        data = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    rates, meetings = data.setdefault("rates", {}), data.setdefault("meetings", {})

    def run(store, what, key, fn):
        try:
            store[key] = fn()
            return True
        except Exception as e:  # noqa: BLE001  one source failing never stops the deploy
            kept = (store.get(key) or {}).get("asof") or (store.get(key) or {}).get("fetched") or "none"
            log(f"centralbanks {what} {key}: {type(e).__name__}: {e}; keeping the last copy ({kept})", "warning")
            return False

    for key, fn in (("fed", r_fed), ("ecb", r_ecb), ("boe", r_boe), ("boj", r_boj)):
        if run(rates, "rate", key, fn):
            r = rates[key]
            print(f"rate {key}: {r['level']} as of {r['asof']} ({r['source']})")
    for key, fn in (("fed", m_fed), ("ecb", m_ecb), ("boe", m_boe), ("boj", m_boj)):
        def block(fn=fn, key=key):
            src = cd().SOURCES[key]  # the calendar's own name and page for each bank
            return {"dates": fn(), "source": src["name"], "url": src["url"], "fetched": now_utc().isoformat(timespec="seconds")}
        if run(meetings, "meetings", key, block):
            print(f"meetings {key}: {len(meetings[key]['dates'])} from {meetings[key]['source']}")
    data["updated"] = now_utc().isoformat(timespec="seconds")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")


if __name__ == "__main__":
    main()
